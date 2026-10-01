/**
 * Pure reader rules: how a script's verse ids relate to the Hafs numbering that translations
 * use, which optional layers may be joined to which script, and how a saved or linked state is
 * made safe. No DOM, no React, no network: everything here is tested by vitest.
 *
 * Reading identity is the rule that matters. Translations are keyed to the Hafs verse
 * numbering, so they may join to a mapped riwayah (Warsh, Qalun, al-Duri) through each verse's
 * `number_in_hafs`. A transliteration is a rendering of one reading's *words*: it is shown only
 * for a Hafs script and a Hafs transliteration, and never joined through `number_in_hafs`
 * (Warsh 1:3 is "malik", where Hafs 1:4 is "maaliki").
 */

import type {
  Chapter,
  Edition,
  FontCoverage,
  ReadingDeclaration,
  Script,
  TextChapter,
  TranslationChapter,
  TransliterationChapter,
  VerseText,
} from "@/lib/types";

export const MAX_TRANSLATIONS = 3;
export const ARABIC_SIZE_MIN = 20;
export const ARABIC_SIZE_MAX = 44;
export const ARABIC_SIZE_DEFAULT = 28;

export interface ReaderPrefs {
  script: string | null;
  translations: string[];
  transliteration: string | null;
  reciter: string | null;
  font: string;
  size: number;
  showArabic: boolean;
  showTransliteration: boolean;
  showTranslations: boolean;
  continuous: boolean;
  repeat: boolean;
  resume: { chapter: number; verse: number } | null;
}

export const DEFAULT_PREFS: Readonly<ReaderPrefs> = Object.freeze({
  script: null,
  translations: [],
  transliteration: null,
  reciter: null,
  font: "auto",
  size: ARABIC_SIZE_DEFAULT,
  showArabic: true,
  showTransliteration: true,
  showTranslations: true,
  continuous: true,
  repeat: false,
  resume: null,
});

export function editionKey(edition: Pick<Edition, "path">): string {
  return edition.path.replace(/\/$/, "").split("/").pop() ?? "";
}

export interface ParsedHash {
  chapter: number | null;
  verse: number | null;
  invalidChapter: boolean;
  invalidVerse: boolean;
  params: URLSearchParams;
}

function positiveInteger(value: string | undefined): number | null {
  const number = Number(value);

  return Number.isInteger(number) && number > 0 ? number : null;
}

/**
 * Parse a reader hash without trusting any value supplied by a link.
 *
 * Accepts `#/2`, `#/2:255` and the old `#/1?s=warsh&t=...` form.
 */
export function parseReaderHash(rawHash: string | null | undefined): ParsedHash {
  const raw = String(rawHash ?? "").replace(/^#/, "");
  const [path = "", query = ""] = raw.split("?");
  const parts = path.replace(/^\//, "").split(":");
  const chapter = positiveInteger(parts[0]);
  const verse = positiveInteger(parts[1]);

  return {
    chapter,
    verse,
    invalidChapter: Boolean(parts[0] && chapter === null),
    invalidVerse: Boolean(parts[1] && verse === null),
    params: new URLSearchParams(query),
  };
}

export function readerHash(chapter: number, verse?: number | null): string {
  return `#/${chapter}${verse ? `:${verse}` : ""}`;
}

/** The Hafs verse numbers a native verse of this script covers. */
export function hafsNumbers(script: Script, verse: VerseText): number[] {
  if (script.verse_ids === "mapped") {
    const mapped = verse.number_in_hafs;

    if (Array.isArray(mapped)) {
      return mapped;
    }

    if (Number.isInteger(mapped)) {
      return [mapped as number];
    }

    return [];
  }

  return [verse.id];
}

function declaredRiwayah(reading: ReadingDeclaration | undefined): string | null {
  if (typeof reading === "string") {
    return reading || null;
  }

  return reading?.riwayah ?? null;
}

/**
 * A reading as a short comparable slug: `hafs`, `warsh`, `qalun`, `duri`, ... Declarations
 * spell the same riwayah several ways ("al-Duri", "Douri", "Rewayat Hafs A'n Assem").
 */
export function readingSlug(text: string | null | undefined): string | null {
  const value = String(text ?? "")
    .toLowerCase()
    .replace(/[ʿʻ'’`]/g, "");

  if (!value.trim()) {
    return null;
  }

  const known: [RegExp, string][] = [
    [/hafs/, "hafs"],
    [/warsh/, "warsh"],
    [/qal+o+n|qalun/, "qalun"],
    [/d[ou]+ri|doori/, "duri"],
    [/shu?bah|shuba/, "shubah"],
    [/bazz?i/, "bazzi"],
    [/qunbul/, "qunbul"],
    [/s[ou]+si|soosi/, "susi"],
  ];

  for (const [pattern, slug] of known) {
    if (pattern.test(value)) {
      return slug;
    }
  }

  return value.trim();
}

/**
 * The reading a script is written in. A manifest that declares `reading.riwayah` is believed;
 * an older one is read conservatively: only `verse_ids` of `hafs` or `own` implies Hafs, and a
 * mapped script is named by its id (so a name like "Duri" can never pass for Hafs).
 */
export function scriptReading(script: Script): string {
  const declared = readingSlug(declaredRiwayah(script.reading));

  if (declared) {
    return declared;
  }

  if (script.verse_ids === "hafs" || script.verse_ids === "own") {
    return "hafs";
  }

  return readingSlug(script.id) ?? script.id;
}

export interface ScriptIdentity {
  reading: string;
  verseNumbering: string | null;
  /** Whether the manifest allows an ayah-scoped (Hafs-numbered) audio URL for this script. */
  perAyah: boolean;
}

export function scriptIdentity(script: Script): ScriptIdentity {
  const reading = scriptReading(script);
  const verseNumbering = script.verse_ids ?? null;
  const audioNumbering = script.audio?.verse_numbering ?? script.audio?.verse_ids ?? null;
  const numberingMatches =
    audioNumbering === null || verseNumbering === null || audioNumbering === verseNumbering;
  const perAyah =
    typeof script.audio?.per_ayah === "boolean"
      ? script.audio.per_ayah
      : reading === "hafs" && verseNumbering === "hafs" && numberingMatches;

  return { reading, verseNumbering, perAyah };
}

/** Return a script's native chapter count when the manifest publishes one. */
export function nativeChapterCount(
  script: Script | null | undefined,
  chapterId: number,
  fallback: number | null = null,
): number | null {
  const value = script?.native_chapter_counts?.[String(chapterId)];

  return Number.isInteger(value) && (value as number) > 0 ? (value as number) : fallback;
}

/** Whether a chapter can be joined to Hafs-keyed optional layers. */
export function alignsWithHafs(script: Script, chapterId: number): boolean {
  // A mapped reading may have a different native count and still join through
  // `number_in_hafs`, so a count difference alone is not an alignment failure.
  const unjoinable =
    script.verse_ids_unjoinable_in ??
    (script.verse_ids === "mapped" ? [] : (script.verse_ids_differ_in ?? []));

  return !unjoinable.includes(Number(chapterId));
}

/** A mapped reading must carry an explicit, increasing Hafs map for every native verse. */
export function canJoinWithHafs(script: Script, verses: VerseText[]): boolean {
  if (script.verse_ids !== "mapped") {
    return true;
  }

  return verses.every((verse) => {
    const numbers = verse.number_in_hafs;

    return (
      Array.isArray(numbers) &&
      numbers.length > 0 &&
      numbers.every((number) => Number.isInteger(number) && number > 0) &&
      numbers.every((number, index) => index === 0 || number > numbers[index - 1])
    );
  });
}

/** The reading a transliteration edition was generated from; an undeclared one is Hafs. */
export function transliterationReading(edition: Edition | undefined): string {
  return readingSlug(declaredRiwayah(edition?.reading)) ?? "hafs";
}

/**
 * Whether this transliteration edition may be shown beside this script's chapter.
 *
 * All of: the script is a Hafs reading with verse ids a transliteration can be joined on
 * directly (not a mapped one), the edition is a Hafs transliteration, and the chapter is joinable.
 */
export function transliterationApplies(
  script: Script,
  edition: Edition | undefined,
  chapterId: number,
): boolean {
  return (
    edition !== undefined &&
    scriptReading(script) === "hafs" &&
    script.verse_ids !== "mapped" &&
    transliterationReading(edition) === "hafs" &&
    alignsWithHafs(script, chapterId)
  );
}

/** Why a selected transliteration is not shown, for a one-line note; null when it is. */
export function transliterationNote(
  script: Script,
  edition: Edition | undefined,
  chapterId: number,
): string | null {
  if (!edition || transliterationApplies(script, edition, chapterId)) {
    return null;
  }

  if (scriptReading(script) !== "hafs" || script.verse_ids === "mapped") {
    return `Transliteration is generated from the Hafs reading, so it is hidden for ${script.name}.`;
  }

  if (transliterationReading(edition) !== "hafs") {
    return "This transliteration is not for the Hafs reading, so it is hidden here.";
  }

  return `${script.name} numbers this chapter differently, so transliteration is hidden here.`;
}

/** Reject a fulfilled optional payload before any positional join can occur. */
export function validateOptionalChapter<T extends TranslationChapter | TransliterationChapter>(
  payload: T | null | undefined,
  options: {
    chapterId: number;
    key: string;
    type: "translation" | "transliteration";
    expectedVerseCount: number;
  },
): T {
  const { chapterId, key, type, expectedVerseCount } = options;
  const field = type === "transliteration" ? "transliteration" : "translation";

  if (
    !payload ||
    payload.id !== Number(chapterId) ||
    !Array.isArray(payload.verses) ||
    !Number.isInteger(expectedVerseCount) ||
    expectedVerseCount < 1 ||
    payload.verses.length !== expectedVerseCount
  ) {
    throw new Error(`${key} returned an invalid chapter payload or verse count`);
  }

  for (let index = 0; index < payload.verses.length; index += 1) {
    const verse = payload.verses[index] as unknown as Record<string, unknown> | undefined;

    if (!verse || verse.id !== index + 1 || typeof verse[field] !== "string") {
      throw new Error(`${key} returned mismatched or incomplete verse data`);
    }
  }

  return payload;
}

export interface MergedVerse extends VerseText {
  transliteration?: string;
  translations?: Record<string, string>;
  footnotes?: Record<string, string>;
}

export interface MergeInput {
  arabic: TextChapter;
  script: Script;
  chapterId?: number;
  /** A transliteration chapter and its edition (so its reading can be checked), or null. */
  romanisation?: { edition: Edition; chapter: TransliterationChapter } | null;
  translated: { key: string; chapter: TranslationChapter }[];
}

/** Merge only optional layers whose verse identity can be joined safely. */
export function mergeChapter({
  arabic,
  script,
  chapterId = arabic.id,
  romanisation = null,
  translated,
}: MergeInput): MergedVerse[] {
  const aligned = alignsWithHafs(script, chapterId) && canJoinWithHafs(script, arabic.verses);
  const showRomanisation =
    aligned &&
    romanisation !== null &&
    transliterationApplies(script, romanisation.edition, chapterId);

  return arabic.verses.map((verse) => {
    const merged: MergedVerse = { ...verse };

    if (showRomanisation && romanisation) {
      // Verse id, not number_in_hafs: the words differ between readings.
      const entry = romanisation.chapter.verses[verse.id - 1];

      if (entry) {
        merged.transliteration = entry.transliteration;
      }
    }

    if (!aligned) {
      return merged;
    }

    const numbers = hafsNumbers(script, verse);
    const translations: Record<string, string> = {};
    const footnotes: Record<string, string> = {};

    for (const { key, chapter } of translated) {
      const parts = numbers.map((number) => chapter.verses[number - 1]).filter(Boolean);

      if (!parts.length) {
        continue;
      }

      translations[key] = parts.map((entry) => entry.translation).join(" ");
      const notes = parts.map((entry) => entry.footnotes).filter(Boolean);

      if (notes.length) {
        footnotes[key] = notes.join("\n\n");
      }
    }

    if (Object.keys(translations).length) {
      merged.translations = translations;
    }

    if (Object.keys(footnotes).length) {
      merged.footnotes = footnotes;
    }

    return merged;
  });
}

/** The font ids that cover every codepoint of this script; empty when none is measured. */
export function usableFonts(coverage: FontCoverage, scriptId: string | null): string[] {
  return (scriptId && coverage.scripts[scriptId]?.usable) || [];
}

/**
 * The font to render a script with: the saved one if it covers every codepoint of the script,
 * else the script's measured default. The build gate only proves that one font covers a script,
 * so a font chosen for another script (or restored from storage) must not be trusted.
 */
export function resolveFont(
  coverage: FontCoverage,
  scriptId: string | null,
  saved: string,
): string | null {
  const entry = scriptId ? coverage.scripts[scriptId] : undefined;

  if (!entry) {
    return null;
  }

  return entry.usable.includes(saved) ? saved : entry.default;
}

export interface BootCatalogue {
  scripts: Script[];
  chapters: Chapter[];
  translations: Edition[];
  transliterations: Edition[];
  coverage: FontCoverage;
}

function booleanOr(value: unknown, fallback: boolean): boolean {
  return typeof value === "boolean" ? value : fallback;
}

/**
 * Make a stored or linked state safe: unknown scripts, editions and fonts fall back to the
 * published defaults, so a stale link or an old localStorage entry can never break the reader.
 */
export function normalizePrefs(raw: unknown, catalogue: BootCatalogue): ReaderPrefs {
  const input = (raw && typeof raw === "object" ? raw : {}) as Record<string, unknown>;
  const state = { ...DEFAULT_PREFS, ...input } as Record<string, unknown>;
  const scripts = catalogue.scripts;
  const script = scripts.find((entry) => entry.id === state.script) ?? scripts[0] ?? null;
  const editionKeys = new Set(catalogue.translations.map(editionKey));
  const transliterationKeys = new Set(catalogue.transliterations.map(editionKey));
  const resume = state.resume as { chapter?: unknown; verse?: unknown } | null | undefined;
  const resumeChapter = Number.isInteger(resume?.chapter)
    ? catalogue.chapters.find((chapter) => chapter.id === resume?.chapter)
    : undefined;
  const resumeLimit = resumeChapter
    ? nativeChapterCount(script, resumeChapter.id, resumeChapter.total_verses)
    : null;
  const resumeVerse =
    resumeChapter &&
    Number.isInteger(resume?.verse) &&
    (resume?.verse as number) > 0 &&
    (resume?.verse as number) <= (resumeLimit ?? 0)
      ? (resume?.verse as number)
      : null;
  const size = Number(state.size);

  return {
    script: script?.id ?? null,
    translations: Array.isArray(state.translations)
      ? [
          ...new Set(
            state.translations.filter(
              (key): key is string => typeof key === "string" && editionKeys.has(key),
            ),
          ),
        ].slice(0, MAX_TRANSLATIONS)
      : [],
    transliteration:
      typeof state.transliteration === "string" && transliterationKeys.has(state.transliteration)
        ? state.transliteration
        : null,
    reciter: typeof state.reciter === "string" ? state.reciter : null,
    font:
      typeof state.font === "string" &&
      usableFonts(catalogue.coverage, script?.id ?? null).includes(state.font)
        ? state.font
        : "auto",
    size: Number.isFinite(size)
      ? Math.min(ARABIC_SIZE_MAX, Math.max(ARABIC_SIZE_MIN, Math.round(size)))
      : ARABIC_SIZE_DEFAULT,
    showArabic: booleanOr(state.showArabic, true),
    showTransliteration: booleanOr(state.showTransliteration, true),
    showTranslations: booleanOr(state.showTranslations, true),
    continuous: booleanOr(state.continuous, true),
    repeat: booleanOr(state.repeat, false),
    resume: resumeChapter && resumeVerse ? { chapter: resumeChapter.id, verse: resumeVerse } : null,
  };
}

/** Prefs overridden by an old-style `?s=&t=&tl=&r=&f=` link. */
export function applyLinkParams(
  prefs: ReaderPrefs,
  params: URLSearchParams,
  catalogue: BootCatalogue,
): ReaderPrefs {
  const raw: Record<string, unknown> = { ...prefs };

  if (params.has("s")) {
    raw.script = params.get("s");
  }

  if (params.has("t")) {
    raw.translations = (params.get("t") ?? "").split(",").filter(Boolean);
  }

  if (params.has("tl")) {
    raw.transliteration = params.get("tl") || null;
  }

  if (params.has("r")) {
    raw.reciter = params.get("r") || null;
  }

  if (params.has("f")) {
    raw.font = params.get("f") || "auto";
  }

  return normalizePrefs(raw, catalogue);
}

/** Unnumbered text a script's source puts before a chapter's verses (Duri's bismillah). */
export function chapterFurniture(script: Script, chapterId: number): string[] {
  return (script.chapter_furniture ?? [])
    .filter(
      (item) =>
        item.chapter === chapterId && item.position === "before-verses" && item.numbered === false,
    )
    .map((item) => item.text);
}

const COMBINING_MARKS = /[ـً-ٰٟۖ-ۭ࣓-ࣿ\s]/g;

/** Whether verse text is the bismillah, read off its letters across the orthographies. */
export function isBismillah(text: string): boolean {
  return text.replace(COMBINING_MARKS, "").startsWith("بسم");
}

/**
 * Whether a chapter opens with the bismillah drawn from the script's own 1:1. Only Hafs-numbered
 * scripts, where 1:1 is the bismillah itself; chapter 1 carries it as verse 1 and chapter 9 has
 * none. Scripts that number differently, or carry it as furniture, are left to their data.
 */
export function showsOpeningBismillah(script: Script, chapterId: number): boolean {
  return (
    script.verse_ids === "hafs" &&
    scriptReading(script) === "hafs" &&
    chapterId !== 1 &&
    chapterId !== 9 &&
    chapterFurniture(script, chapterId).length === 0
  );
}
