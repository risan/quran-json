#!/usr/bin/env node

import { cp, mkdir, readFile, readdir, rm, stat } from "node:fs/promises";
import { join, resolve, sep } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL("..", import.meta.url)));
const site = join(root, "site");
const staging = join(root, ".build");
const data = join(staging, "data");
const siteOutput = join(staging, "site");
const assembled = join(staging, "assembled");
const fontCoverage = join(staging, "fonts.json");
const writeCdn = !process.argv.includes("--no-cdn");

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd ?? root,
    env: { ...process.env, ...options.env },
    stdio: "inherit",
  });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    throw new Error(`${command} ${args.join(" ")} failed with status ${result.status}`);
  }
}

async function filesUnder(directory, prefix = "") {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = [];
  for (const entry of entries) {
    const relativePath = join(prefix, entry.name);
    const absolutePath = join(directory, entry.name);
    if (entry.isDirectory()) {
      files.push(...(await filesUnder(absolutePath, relativePath)));
    } else if (entry.isFile()) {
      files.push(relativePath);
    }
  }
  return files;
}

/**
 * Astro may add only its own pages, hashed assets, fonts and favicon, and never a path the
 * data tree already publishes: a page that shadowed `/manifest.json` would silently break
 * every consumer.
 */
function isAllowed(relativePath) {
  const parts = relativePath.split(sep);
  return (
    relativePath === "index.html" ||
    relativePath === join("app", "index.html") ||
    relativePath === "favicon.svg" ||
    ((parts[0] === "_astro" || parts[0] === "fonts") && parts.length > 1)
  );
}

async function overlayAstro() {
  const outputFiles = await filesUnder(siteOutput);

  for (const relativePath of outputFiles) {
    if (!isAllowed(relativePath)) {
      throw new Error(`Astro emitted an unallowlisted file: ${relativePath}`);
    }
  }

  for (const relativePath of outputFiles) {
    const source = join(siteOutput, relativePath);
    const target = join(assembled, relativePath);
    try {
      await stat(target);
      throw new Error(`Astro output collides with an existing data path: ${relativePath}`);
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
    }
    await mkdir(resolve(target, ".."), { recursive: true });
    await cp(source, target);
  }
}

await rm(staging, { recursive: true, force: true });
await mkdir(staging, { recursive: true });

const uvEnv = { UV_CACHE_DIR: process.env.UV_CACHE_DIR ?? join(root, ".cache", "uv") };
run("uv", ["run", "quran-json", "cdn", "--out", data], { env: uvEnv });

// Outside the data tree on purpose: the report feeds the site build and is never published.
run("uv", ["run", "quran-json", "fonts", "--data", data, "--out", fontCoverage], { env: uvEnv });

run("npm", ["run", "build"], {
  cwd: site,
  env: {
    ASTRO_TELEMETRY_DISABLED: "1",
    QURAN_JSON_SITE_DATA: data,
    QURAN_JSON_FONTS: fontCoverage,
    XDG_CONFIG_HOME: process.env.XDG_CONFIG_HOME ?? join(root, ".cache", "config"),
  },
});

await cp(data, assembled, { recursive: true });
await overlayAstro();

if (writeCdn) {
  await rm(join(root, "cdn"), { recursive: true, force: true });
  await cp(assembled, join(root, "cdn"), { recursive: true });
}

const manifest = JSON.parse(await readFile(join(assembled, "manifest.json"), "utf8"));
const output = writeCdn ? "cdn/" : ".build/assembled/";
console.log(
  `built ${output} with ${manifest.scripts.length} scripts, ` +
    `${manifest.translations.count} translations, ` +
    `${manifest.transliteration.count} transliterations`,
);
