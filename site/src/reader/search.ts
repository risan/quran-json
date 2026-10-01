/** Chapter search for the surah list and the command palette. */

import type { Chapter, Script } from "@/lib/types";
import { nativeChapterCount } from "./core";

/** Arabic diacritics, tatweel, Quranic marks and extended marks: stripped before matching. */
const ARABIC_MARKS = /[ـً-ٰٟۖ-ۭ࣓-ࣿ]/g;

/**
 * Lowercase, drop accents and Arabic marks, and collapse the spellings Latin names vary in
 * (hyphens, apostrophes, doubled long vowels), so "al baqara" finds "Al-Baqarah" and "fatiha"
 * finds "Al-Faatiha".
 */
export function normalizeForSearch(text: string): string {
  return text
    .normalize("NFD")
    .replace(/\p{M}/gu, "")
    .replace(ARABIC_MARKS, "")
    .toLowerCase()
    .replace(/[-_'’`ʿʻ]/g, " ")
    .replace(/([aiu])\1+/g, "$1")
    .replace(/\s+/g, " ")
    .trim();
}

export function chapterMatches(chapter: Chapter, query: string): boolean {
  const needle = normalizeForSearch(query);

  if (!needle) {
    return true;
  }

  if (/^\d+$/.test(needle)) {
    return String(chapter.id).startsWith(needle);
  }

  const haystack = [chapter.transliteration, chapter.translation, chapter.name]
    .map(normalizeForSearch)
    .join(" | ");

  return haystack.includes(needle);
}

export function filterChapters(chapters: Chapter[], query: string): Chapter[] {
  return chapters.filter((chapter) => chapterMatches(chapter, query));
}

export interface VerseTarget {
  chapter: number;
  verse: number;
}

/**
 * `2:255`, `2.255` or `2 255` as a verse that exists in the selected script, else null. Warsh,
 * Qalun, al-Duri and al-Susi number some chapters differently, so their own counts decide.
 */
export function parseVerseTarget(
  query: string,
  chapters: Chapter[],
  script?: Script | null,
): VerseTarget | null {
  const match = /^\s*(\d{1,3})\s*[:.\s]\s*(\d{1,3})\s*$/.exec(query);

  if (!match) {
    return null;
  }

  const chapter = chapters.find((entry) => entry.id === Number(match[1]));
  const verse = Number(match[2]);

  if (!chapter) {
    return null;
  }

  const count =
    nativeChapterCount(script, chapter.id, chapter.total_verses) ?? chapter.total_verses;

  if (verse < 1 || verse > count) {
    return null;
  }

  return { chapter: chapter.id, verse };
}
