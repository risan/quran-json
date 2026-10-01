import { realpath, stat } from "node:fs/promises";
import { isAbsolute, relative, resolve } from "node:path";

/**
 * Resolve a request path to a regular file inside `root`, or null.
 *
 * Decodes once, so `%252e` stays a literal `%2e` file name, and checks containment on real
 * paths: a string prefix would let `data-private` pass for root `data`, and a symlink could
 * point out of the tree.
 */
export async function resolveDataFile(root, requestPath) {
  let decoded;

  try {
    decoded = decodeURIComponent(requestPath);
  } catch {
    return null;
  }

  if (decoded.includes("\0") || decoded.includes("\\")) {
    return null;
  }

  try {
    const realRoot = await realpath(resolve(root));
    const target = await realpath(
      resolve(realRoot, `.${decoded.startsWith("/") ? "" : "/"}${decoded}`),
    );
    const inside = relative(realRoot, target);

    if (inside === "" || inside.startsWith("..") || isAbsolute(inside)) {
      return null;
    }

    return (await stat(target)).isFile() ? target : null;
  } catch {
    return null;
  }
}
