import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { fileURLToPath } from "node:url";

export type Direction = "ltr" | "rtl";

export interface License {
  status: "granted" | "restricted" | "unknown";
  text: string;
  url: string;
}

export interface Script {
  id: string;
  name: string;
  description: string;
  verses: number;
  verse_ids: "hafs" | "mapped" | "own";
  path: string;
  chapters: string;
  note?: string;
  verse_ids_differ_in?: number[];
}

export interface Edition {
  path: string;
  edition: string;
  author: string;
  source: string;
  license: License;
  chapters: number;
  files: {
    quran: string;
    chapters: string;
  };
  language?: string;
  code?: string;
  direction?: Direction;
  version?: string;
}

export interface Withheld {
  edition: string;
  author: string;
  status: License["status"];
  license_url: string;
}

export interface Catalogue {
  count: number;
  editions: Edition[];
  withheld: Withheld[];
}

export interface Manifest {
  chapters: { count: number; path: string };
  scripts: Script[];
  translations: { count: number; languages: number; index: string };
  transliteration: { count: number; index: string };
  audio: string | null;
  license: {
    project: string;
    text: { source: string; status: License["status"]; url: string };
  };
  attribution: string;
}

export interface Chapter {
  id: number;
  name: string;
  transliteration: string;
  translation: string;
  type: "meccan" | "medinan";
  total_verses: number;
}

export interface ReciterIndex {
  reciters: Record<string, unknown>[];
  hosts: Record<string, { name: string; template: string; indexing: string; license_status: string }>;
}

export interface FontCoverage {
  scripts: Record<string, { default: string; usable: string[] }>;
}

export interface SiteCatalog {
  manifest: Manifest;
  chapters: Chapter[];
  translations: Catalogue;
  transliterations: Catalogue;
  reciters: ReciterIndex | null;
  coverage: FontCoverage;
}

const dataRoot = process.env.QURAN_JSON_SITE_DATA
  ? resolve(process.env.QURAN_JSON_SITE_DATA)
  : resolve(fileURLToPath(new URL("../../../.build/data", import.meta.url)));

function readJson<T>(relativePath: string): T {
  return JSON.parse(readFileSync(resolve(dataRoot, relativePath), "utf8")) as T;
}

export function loadCatalog(): SiteCatalog {
  const manifest = readJson<Manifest>("manifest.json");
  return {
    manifest,
    chapters: readJson<Chapter[]>("chapters.json"),
    translations: readJson<Catalogue>("translations/index.json"),
    transliterations: readJson<Catalogue>("transliteration/index.json"),
    reciters: manifest.audio ? readJson<ReciterIndex>("audio/reciters.json") : null,
    coverage: readJson<FontCoverage>("app/fonts.json"),
  };
}

export function chapterUrl(chapter: Chapter): string {
  return `/app/#/${chapter.id}`;
}

export function editionKey(edition: Edition): string {
  return edition.path.split("/").filter(Boolean).at(-1) ?? edition.edition;
}

export function chapterPath(edition: Edition, chapter: number): string {
  return `${edition.path}chapters/${chapter}.json`;
}
