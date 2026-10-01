import { describe, expect, it } from "vitest";

import {
  bismillahHeader,
  chapterFurniture,
  isBismillah,
  showsOpeningBismillah,
} from "../src/reader/core";
import { neighbour } from "../src/reader/player-logic";
import { filterChapters, parseVerseTarget } from "../src/reader/search";
import type { Chapter, Script } from "../src/lib/types";

const chapters = [
  {
    id: 1,
    name: "الفاتحة",
    transliteration: "Al-Faatiha",
    translation: "The Opening",
    total_verses: 7,
  },
  {
    id: 2,
    name: "البقرة",
    transliteration: "Al-Baqara",
    translation: "The Cow",
    total_verses: 286,
  },
] as Chapter[];

describe("chapter search", () => {
  it("matches number, name, meaning and Arabic", () => {
    expect(filterChapters(chapters, "2").map((c) => c.id)).toEqual([2]);
    expect(filterChapters(chapters, "fatiha").map((c) => c.id)).toEqual([1]);
    expect(filterChapters(chapters, "al baqarah").length).toBe(0);
    expect(filterChapters(chapters, "cow").map((c) => c.id)).toEqual([2]);
    expect(filterChapters(chapters, "البقرة").map((c) => c.id)).toEqual([2]);
  });

  it("parses verse targets that exist", () => {
    expect(parseVerseTarget("2:255", chapters)).toEqual({ chapter: 2, verse: 255 });
    expect(parseVerseTarget("2:287", chapters)).toBeNull();
    expect(parseVerseTarget("3:1", chapters)).toBeNull();
  });

  it("uses the selected script's own chapter counts", () => {
    const mulk = [{ id: 67, name: "الملك", total_verses: 30 }] as Chapter[];
    const duri = { id: "duri", native_chapter_counts: { "67": 31 } } as unknown as Script;
    const warsh = { id: "warsh", native_chapter_counts: { "2": 285 } } as unknown as Script;

    expect(parseVerseTarget("67:31", mulk, duri)).toEqual({ chapter: 67, verse: 31 });
    expect(parseVerseTarget("67:31", mulk)).toBeNull();
    expect(parseVerseTarget("2:286", chapters, warsh)).toBeNull();
    expect(parseVerseTarget("2:285", chapters, warsh)).toEqual({ chapter: 2, verse: 285 });
  });
});

describe("opening bismillah", () => {
  const hafs = { id: "uthmani", verse_ids: "hafs" } as Script;
  const duri = {
    id: "duri",
    verse_ids: "mapped",
    chapter_furniture: [
      { chapter: 1, position: "before-verses", kind: "bismillah", text: "x", numbered: false },
    ],
  } as Script;

  it("is drawn for Hafs-numbered scripts except chapters 1 and 9", () => {
    expect(showsOpeningBismillah(hafs, 2)).toBe(true);
    expect(showsOpeningBismillah(hafs, 1)).toBe(false);
    expect(showsOpeningBismillah(hafs, 9)).toBe(false);
    expect(showsOpeningBismillah(duri, 2)).toBe(false);
  });

  it("source furniture is used as given", () => {
    expect(chapterFurniture(duri, 1)).toEqual(["x"]);
    expect(chapterFurniture(duri, 2)).toEqual([]);
  });

  it("recognises the bismillah across orthographies", () => {
    expect(isBismillah("بِسۡمِ ٱللَّهِ")).toBe(true);
    expect(isBismillah("ٱلۡحَمۡدُ")).toBe(false);
  });
});

describe("bismillah header from the manifest field", () => {
  const text = "بِسۡمِ";
  const withRule = (in_verse_one: boolean, numbered_in_fatiha: boolean) =>
    ({ id: "x", bismillah: { text, in_verse_one, numbered_in_fatiha } }) as Script;
  const tanzil = withRule(true, true);
  const warsh = withRule(false, false);
  const qpc = withRule(false, true);

  it("is never drawn for chapter 9", () => {
    expect(bismillahHeader(warsh, 9)).toBeNull();
  });

  it("is drawn for chapter 1 only when the source does not number it", () => {
    expect(bismillahHeader(warsh, 1)).toBe(text);
    expect(bismillahHeader(qpc, 1)).toBeNull();
    expect(bismillahHeader(tanzil, 1)).toBeNull();
  });

  it("is drawn for chapters 2 to 114 only when verse one does not carry it", () => {
    expect(bismillahHeader(warsh, 2)).toBe(text);
    expect(bismillahHeader(warsh, 114)).toBe(text);
    expect(bismillahHeader(qpc, 2)).toBe(text);
    expect(bismillahHeader(tanzil, 2)).toBeNull();
  });

  it("is undefined without the field, so the old behaviour applies", () => {
    expect(bismillahHeader({ id: "x" } as Script, 2)).toBeUndefined();
  });
});

describe("playback neighbours", () => {
  const counts = (chapter: number) => (chapter === 1 ? 7 : 286);

  it("steps within and across chapters and stops at the ends", () => {
    expect(neighbour({ chapter: 1, verse: 3 }, 1, counts, 114)).toEqual({ chapter: 1, verse: 4 });
    expect(neighbour({ chapter: 1, verse: 7 }, 1, counts, 114)).toEqual({ chapter: 2, verse: 1 });
    expect(neighbour({ chapter: 2, verse: 1 }, -1, counts, 114)).toEqual({ chapter: 1, verse: 7 });
    expect(neighbour({ chapter: 1, verse: 1 }, -1, counts, 114)).toBeNull();
    expect(neighbour({ chapter: 114, verse: 286 }, 1, counts, 114)).toBeNull();
  });
});
