/**
 * Build-time loader for the generated data. Only Astro pages (the server side of the build)
 * may import this: it reads files. The reader island receives what it needs as props.
 */

import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

import type {
  Catalogue,
  Chapter,
  Edition,
  FontCoverage,
  Manifest,
  ReaderBoot,
  ReciterIndex,
  Script,
} from "./types";

export interface SourcesMeta {
  text: {
    source: string;
    status: string;
    license: string;
    license_url: string;
    scripts?: string[];
  };
  editions: { edition: string; path: string; author: string; status: string; license: string }[];
  withheld: {
    edition: string;
    author: string;
    status: string;
    license_url?: string;
    reason?: string;
  }[];
}

export interface SiteCatalog {
  manifest: Manifest;
  chapters: Chapter[];
  translations: Catalogue;
  transliterations: Catalogue;
  reciters: ReciterIndex | null;
  coverage: FontCoverage;
  sources: SourcesMeta;
}

const repositoryRoot = fileURLToPath(new URL("../../../", import.meta.url));

const dataRoot = resolve(
  process.env.QURAN_JSON_SITE_DATA ?? resolve(repositoryRoot, ".build/data"),
);

// The coverage report is written outside the data tree (it is never published), so its path
// is handed over explicitly by `scripts/build-site.mjs`.
const fontsPath = resolve(
  process.env.QURAN_JSON_FONTS ?? resolve(repositoryRoot, ".build/fonts.json"),
);

function readJson<T>(path: string): T {
  return JSON.parse(readFileSync(path, "utf8")) as T;
}

let cached: SiteCatalog | null = null;

export function loadCatalog(): SiteCatalog {
  if (cached) {
    return cached;
  }

  const manifest = readJson<Manifest>(resolve(dataRoot, "manifest.json"));

  cached = {
    manifest,
    chapters: readJson<Chapter[]>(resolve(dataRoot, "chapters.json")),
    translations: readJson<Catalogue>(resolve(dataRoot, "translations/index.json")),
    transliterations: readJson<Catalogue>(resolve(dataRoot, "transliteration/index.json")),
    reciters: manifest.audio
      ? readJson<ReciterIndex>(resolve(dataRoot, "audio/reciters.json"))
      : null,
    coverage: readJson<FontCoverage>(fontsPath),
    sources: readJson<SourcesMeta>(resolve(dataRoot, "meta/sources.json")),
  };

  return cached;
}

/** What the reader island is built with: the catalogue, trimmed to what the reader uses. */
export function readerBoot(catalog: SiteCatalog): ReaderBoot {
  const slim = (edition: Edition): Edition => ({
    path: edition.path,
    edition: edition.edition,
    author: edition.author,
    language: edition.language,
    code: edition.code,
    direction: edition.direction,
    version: edition.version,
    reading: edition.reading,
    verse_ids: edition.verse_ids,
    review: edition.review,
    name: edition.name,
    style: edition.style,
  });

  return {
    scripts: catalog.manifest.scripts,
    chapters: catalog.chapters,
    translations: catalog.translations.editions.map(slim),
    transliterations: catalog.transliterations.editions.map(slim),
    coverage: catalog.coverage,
    audio: catalog.reciters !== null,
  };
}

export function editionKey(edition: Pick<Edition, "path">): string {
  return edition.path.replace(/\/$/, "").split("/").pop() ?? "";
}

export function sortEditions(editions: Edition[]): Edition[] {
  return [...editions].sort((a, b) =>
    `${a.language}\u0000${a.author}\u0000${a.path}`.localeCompare(
      `${b.language}\u0000${b.author}\u0000${b.path}`,
      "en",
      { sensitivity: "base", numeric: true },
    ),
  );
}

/** Script order for the docs: the widely used ones first, the specialist ones last. */
const SCRIPT_ORDER = [
  "uthmani",
  "qpc-hafs",
  "simple",
  "simple-clean",
  "kemenag",
  "hafs-nastaliq",
  "indopak",
  "warsh",
  "qalun",
  "duri",
];

export function orderedScripts(scripts: Script[]): Script[] {
  const rank = (id: string) => {
    const index = SCRIPT_ORDER.indexOf(id);

    return index === -1 ? SCRIPT_ORDER.length : index;
  };

  return [...scripts].sort((a, b) => rank(a.id) - rank(b.id));
}

export function readingLabel(script: Script): string {
  const reading = script.reading;

  if (typeof reading === "string") {
    return reading;
  }

  if (reading?.riwayah) {
    return reading.riwayah;
  }

  return script.verse_ids === "mapped" ? script.id : "Hafs";
}

export function verseIdsLabel(script: Script): string {
  if (script.verse_ids === "hafs") {
    return "Hafs numbering";
  }

  if (script.verse_ids === "mapped") {
    return "own numbering, `number_in_hafs` maps to Hafs";
  }

  return "own numbering";
}

/** A fixed-locale integer, so the build does not depend on the machine's locale. */
export function count(value: number): string {
  return value.toLocaleString("en-US");
}
