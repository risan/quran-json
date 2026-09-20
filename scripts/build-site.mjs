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
const includeUnverified = process.argv.includes("--include-unverified-licenses");
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

async function overlayAstro() {
  const intentional = new Set(["index.html", join("app", "index.html")]);
  const astroPrefix = `${join("_astro", "")}${sep}`;
  const allowed = (relativePath) =>
    intentional.has(relativePath) || relativePath.startsWith(astroPrefix);
  const outputFiles = await filesUnder(siteOutput);

  for (const relativePath of outputFiles) {
    if (!allowed(relativePath)) {
      throw new Error(`Astro emitted an unallowlisted file: ${relativePath}`);
    }
  }

  for (const relativePath of outputFiles) {
    const source = join(siteOutput, relativePath);
    const target = join(assembled, relativePath);
    try {
      await stat(target);
      if (!intentional.has(relativePath)) {
        throw new Error(`Astro output collides with an existing data path: ${relativePath}`);
      }
    } catch (error) {
      if (error.code !== "ENOENT") throw error;
    }
    await mkdir(resolve(target, ".."), { recursive: true });
    await cp(source, target);
  }
}

await rm(staging, { recursive: true, force: true });
await mkdir(staging, { recursive: true });

const dataArgs = ["run", "quran-json", "cdn", "--out", data];
if (includeUnverified) dataArgs.push("--include-unverified-licenses");
run("uv", dataArgs, {
  env: { UV_CACHE_DIR: process.env.UV_CACHE_DIR ?? join(root, ".cache", "uv") },
});

run("npm", ["run", "build"], {
  cwd: site,
  env: {
    ASTRO_TELEMETRY_DISABLED: "1",
    QURAN_JSON_SITE_DATA: data,
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
    `${manifest.transliteration.count} transliterations` +
    (includeUnverified ? " (explicit unverified override)" : " (safe default)"),
);
