/**
 * The shapes of the published JSON the site reads. Fields that other parts of the pipeline
 * are still adding (`reading`, `license`, `audio`, `review`) are optional: the reader has to
 * work on today's data and on tomorrow's.
 */

export type Direction = "ltr" | "rtl";
export type LicenseStatus = "granted" | "restricted" | "unknown";
export type VerseIds = "hafs" | "mapped" | "own";

export interface License {
  status: LicenseStatus;
  text?: string;
  url?: string;
  id?: string;
  attribution?: string;
  notice?: string;
}

/** `reading` as a manifest or catalogue declares it: a bare riwayah or an object. */
export type ReadingDeclaration = string | { qiraah?: string; riwayah?: string };

export interface ChapterFurniture {
  chapter: number;
  position: string;
  kind: string;
  text: string;
  numbered: boolean;
}

export interface Script {
  id: string;
  name: string;
  description: string;
  verses: number;
  verse_ids: VerseIds;
  path: string;
  chapters: string;
  note?: string;
  license?: License;
  reading?: ReadingDeclaration;
  audio?: { per_ayah?: boolean; verse_ids?: string; verse_numbering?: string };
  verse_ids_differ_in?: number[];
  verse_ids_unjoinable_in?: number[];
  native_chapter_counts?: Record<string, number>;
  chapter_furniture?: ChapterFurniture[];
}

export interface Edition {
  path: string;
  edition: string;
  author: string;
  source?: string;
  license?: License;
  chapters?: number;
  files?: { quran: string; chapters: string };
  language?: string;
  code?: string;
  direction?: Direction;
  version?: string;
  /** Transliteration editions: the reading the romanisation was generated from. */
  reading?: ReadingDeclaration;
  verse_ids?: string;
  /** Transliteration editions: a review note the reader must show. */
  review?: string;
  name?: string;
  style?: string;
}

export interface Withheld {
  edition: string;
  author: string;
  status: LicenseStatus;
  license_url?: string;
  availability?: string;
  reason?: string;
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
    text: { source: string; status: LicenseStatus; url: string };
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

export interface AudioHost {
  name: string;
  home?: string;
  template: string;
  surah_template?: string;
  indexing: string;
  indexing_mode?: "surah-relative" | "global-ayah" | "whole-surah";
  surah_pad?: number;
  ayah_pad?: number;
  cors?: boolean;
  license_status: LicenseStatus;
  license?: string;
  license_url?: string;
}

export interface Reciter {
  id: string;
  host: string;
  name: string;
  scope: "ayah" | "surah";
  url: string;
  bitrate_kbps?: number;
  recitation?: string;
  reading?: ReadingDeclaration;
  verse_ids?: string;
}

export interface ReciterIndex {
  note?: string;
  hosts: Record<string, AudioHost>;
  reciters: Reciter[];
}

export interface FontInfo {
  id: string;
  name: string;
  file: string;
  license: string;
  license_url: string;
  license_file: string;
  source: string;
  covers: string;
}

export interface FontCoverage {
  fonts: FontInfo[];
  scripts: Record<string, { default: string; usable: string[] }>;
}

export interface VerseText {
  id: number;
  text: string;
  number_in_hafs?: number | number[];
  notice?: string;
}

export interface TextChapter {
  id: number;
  verses: VerseText[];
}

export interface TranslationVerse {
  id: number;
  translation: string;
  footnotes?: string;
}

export interface TranslationChapter {
  id: number;
  verses: TranslationVerse[];
}

export interface TransliterationVerse {
  id: number;
  transliteration: string;
}

export interface TransliterationChapter {
  id: number;
  verses: TransliterationVerse[];
}

/** What the page hands the reader island: everything that does not change per chapter. */
export interface ReaderBoot {
  scripts: Script[];
  chapters: Chapter[];
  translations: Edition[];
  transliterations: Edition[];
  coverage: FontCoverage;
  audio: boolean;
}
