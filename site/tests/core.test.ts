import { describe, expect, it } from "vitest";

import {
  alignsWithHafs,
  applyLinkParams,
  canJoinWithHafs,
  defaultTranslation,
  mergeChapter,
  nativeChapterCount,
  normalizePrefs,
  parseReaderHash,
  readerHash,
  readingSlug,
  resolveFont,
  scriptIdentity,
  scriptReading,
  suggestedTransliteration,
  transliterationApplies,
  validateOptionalChapter,
  type BootCatalogue,
} from "../src/reader/core";
import type { Edition, FontCoverage, Script, TextChapter } from "../src/lib/types";

function script(partial: Partial<Script> & Pick<Script, "id" | "verse_ids">): Script {
  return {
    name: partial.id,
    description: "",
    verses: 6236,
    path: `/text/${partial.id}/quran.json`,
    chapters: `/text/${partial.id}/chapters/{1-114}.json`,
    ...partial,
  };
}

const uthmani = script({ id: "uthmani", verse_ids: "hafs" });
const indopak = script({ id: "indopak", verse_ids: "own", verse_ids_differ_in: [1] });
const warsh = script({ id: "warsh", verse_ids: "mapped" });
const duri = script({
  id: "duri",
  name: "al-Duri",
  verse_ids: "mapped",
  verse_ids_differ_in: [2, 4],
  verse_ids_unjoinable_in: [],
  native_chapter_counts: { "2": 285, "9": 130 },
  reading: { qiraah: "Abu Amr", riwayah: "Duri" },
});
const hafsNastaliq = script({
  id: "hafs-nastaliq",
  name: "Hafs Nastaliq",
  verse_ids: "hafs",
  reading: { qiraah: "Asim", riwayah: "Hafs" },
});

const coverage: FontCoverage = {
  fonts: [],
  scripts: {
    uthmani: { default: "amiri", usable: ["amiri", "scheherazade-new", "noto-naskh-arabic"] },
    indopak: { default: "scheherazade-new", usable: ["scheherazade-new", "noto-naskh-arabic"] },
  },
};

function edition(path: string, extra: Partial<Edition> = {}): Edition {
  return { path, edition: path, author: "A", code: "en", ...extra };
}

const translationEdition = edition("/translations/en-rwwad/");
const hafsTransliteration = edition("/transliteration/en/", { reading: "hafs" });

const catalogue: BootCatalogue = {
  scripts: [uthmani, indopak, warsh, duri, hafsNastaliq],
  chapters: [{ id: 1, total_verses: 7 } as never],
  translations: [translationEdition],
  transliterations: [hafsTransliteration],
  coverage,
};

function chapter(verses: object[]): TextChapter {
  return { id: 1, verses } as TextChapter;
}

describe("joining optional layers", () => {
  it("Indo-Pak divergent chapters suppress every Hafs-keyed optional layer", () => {
    const arabic = chapter([
      { id: 1, text: "al-hamdu" },
      { id: 2, text: "rabb" },
    ]);
    const merged = mergeChapter({
      arabic,
      script: indopak,
      chapterId: 1,
      romanisation: {
        edition: hafsTransliteration,
        chapter: {
          id: 1,
          verses: [
            { id: 1, transliteration: "basmala" },
            { id: 2, transliteration: "al-hamdu" },
          ],
        },
      },
      translated: [
        {
          key: "en-rwwad",
          chapter: {
            id: 1,
            verses: [
              { id: 1, translation: "basmala translation" },
              { id: 2, translation: "al-hamdu translation" },
            ],
          },
        },
      ],
    });

    expect(alignsWithHafs(indopak, 1)).toBe(false);
    expect(merged[0].transliteration).toBeUndefined();
    expect(merged[0].translations).toBeUndefined();
    expect(merged[1].transliteration).toBeUndefined();
    expect(merged[1].translations).toBeUndefined();
  });

  it("mapped Warsh verses join each Hafs translation exactly once", () => {
    const arabic = chapter([{ id: 1, text: "warsh", number_in_hafs: [1, 2] }]);
    const merged = mergeChapter({
      arabic,
      script: warsh,
      chapterId: 1,
      translated: [
        {
          key: "en-rwwad",
          chapter: {
            id: 1,
            verses: [
              { id: 1, translation: "first", footnotes: "first note" },
              { id: 2, translation: "second", footnotes: "second note" },
            ],
          },
        },
      ],
    });

    expect(merged[0].translations).toEqual({ "en-rwwad": "first second" });
    expect(merged[0].footnotes).toEqual({ "en-rwwad": "first note\n\nsecond note" });
  });

  it("mapped Duri Fatiha joins its explicit source mapping", () => {
    const fatiha = { ...duri, verse_ids_differ_in: [] };
    const arabic = chapter([
      { id: 1, text: "bismillah", number_in_hafs: [2] },
      { id: 2, text: "one", number_in_hafs: [3] },
      { id: 3, text: "two", number_in_hafs: [4] },
      { id: 4, text: "three", number_in_hafs: [5] },
      { id: 5, text: "four", number_in_hafs: [6] },
      { id: 6, text: "five", number_in_hafs: [7] },
      { id: 7, text: "six", number_in_hafs: [7] },
    ]);
    const translated = [
      {
        key: "en-rwwad",
        chapter: {
          id: 1,
          verses: ["basmala", "one", "two", "three", "four", "five", "six"].map(
            (translation, index) => ({ id: index + 1, translation }),
          ),
        },
      },
    ];

    expect(alignsWithHafs(fatiha, 1)).toBe(true);
    const merged = mergeChapter({ arabic, script: fatiha, chapterId: 1, translated });
    expect(merged[0].translations?.["en-rwwad"]).toBe("one");
    expect(merged.at(-2)?.translations?.["en-rwwad"]).toBe("six");
    expect(merged.at(-1)?.translations?.["en-rwwad"]).toBe("six");
  });

  it("explicit unjoinable chapters override broad count-difference metadata", () => {
    const explicit = script({
      id: "duri",
      verse_ids: "mapped",
      verse_ids_differ_in: [1, 2, 4],
      verse_ids_unjoinable_in: [1],
    });

    expect(alignsWithHafs(explicit, 1)).toBe(false);
    expect(alignsWithHafs(explicit, 2)).toBe(true);
  });

  it("mapped count differences remain joinable without an explicit exception", () => {
    const broad = script({ id: "duri", verse_ids: "mapped", verse_ids_differ_in: [1, 2, 4] });

    expect(alignsWithHafs(broad, 1)).toBe(true);
    expect(alignsWithHafs(broad, 2)).toBe(true);
  });

  it("mapped readings without an explicit map do not guess optional joins", () => {
    const unmapped = script({ id: "duri", verse_ids: "mapped" });
    const arabic = chapter([{ id: 1, text: "unmapped" }]);

    expect(canJoinWithHafs(unmapped, arabic.verses)).toBe(false);

    const merged = mergeChapter({
      arabic,
      script: unmapped,
      chapterId: 1,
      romanisation: {
        edition: hafsTransliteration,
        chapter: { id: 1, verses: [{ id: 1, transliteration: "wrong" }] },
      },
      translated: [{ key: "en", chapter: { id: 1, verses: [{ id: 1, translation: "wrong" }] } }],
    });

    expect(merged[0].transliteration).toBeUndefined();
    expect(merged[0].translations).toBeUndefined();
  });
});

describe("transliteration reading identity", () => {
  const warshFatiha = chapter([
    { id: 1, text: "al-hamdu", number_in_hafs: [1, 2] },
    { id: 2, text: "ar-rahman", number_in_hafs: [3] },
    { id: 3, text: "malik", number_in_hafs: [4] },
  ]);
  const hafsFatiha = {
    id: 1,
    verses: [
      { id: 1, transliteration: "Bismillahi" },
      { id: 2, transliteration: "Alhamdu" },
      { id: 3, transliteration: "Arrahmani" },
      { id: 4, transliteration: "Maaliki" },
    ],
  };

  it("Warsh chapter 1 never shows a Hafs transliteration (Warsh 1:3 is malik, Hafs 1:4 is Maaliki)", () => {
    const merged = mergeChapter({
      arabic: warshFatiha,
      script: warsh,
      chapterId: 1,
      romanisation: { edition: hafsTransliteration, chapter: hafsFatiha },
      translated: [],
    });

    expect(transliterationApplies(warsh, hafsTransliteration, 1)).toBe(false);
    expect(merged.every((verse) => verse.transliteration === undefined)).toBe(true);
  });

  it("a Hafs script shows it, joined by verse id", () => {
    const merged = mergeChapter({
      arabic: chapter([
        { id: 1, text: "b" },
        { id: 2, text: "h" },
      ]),
      script: uthmani,
      chapterId: 1,
      romanisation: { edition: hafsTransliteration, chapter: hafsFatiha },
      translated: [],
    });

    expect(merged.map((verse) => verse.transliteration)).toEqual(["Bismillahi", "Alhamdu"]);
  });

  it("a mapped script is never joined, even when it declares the Hafs riwayah", () => {
    const odd = script({ id: "odd", verse_ids: "mapped", reading: { riwayah: "Hafs" } });

    expect(transliterationApplies(odd, hafsTransliteration, 1)).toBe(false);
  });

  it("an undeclared reading counts as Hafs only for hafs or own verse ids", () => {
    expect(scriptReading(uthmani)).toBe("hafs");
    expect(scriptReading(indopak)).toBe("hafs");
    expect(scriptReading(warsh)).toBe("warsh");
    expect(scriptReading(script({ id: "mystery", verse_ids: "mapped" }))).toBe("mystery");
    expect(scriptReading(duri)).toBe("duri-abu-amr");
    expect(scriptReading(hafsNastaliq)).toBe("hafs");
  });

  it("a non-Hafs transliteration is hidden even for a Hafs script", () => {
    const warshRendering = edition("/transliteration/en-warsh/", { reading: "warsh" });

    expect(transliterationApplies(uthmani, warshRendering, 1)).toBe(false);
    expect(transliterationApplies(uthmani, edition("/transliteration/x/"), 1)).toBe(true);
    expect(transliterationApplies(uthmani, undefined, 1)).toBe(false);
  });

  it("a divergent chapter hides it", () => {
    expect(transliterationApplies(indopak, hafsTransliteration, 1)).toBe(false);
    expect(transliterationApplies(indopak, hafsTransliteration, 2)).toBe(true);
  });
});

describe("reading slugs", () => {
  it("normalise the spellings sources use", () => {
    expect(readingSlug("Rewayat Hafs A'n Assem - Murattal")).toBe("hafs");
    expect(readingSlug("Rewayat Warsh A'n Nafi'")).toBe("warsh");
    expect(readingSlug("Rewayat Qalon A'n Nafi'")).toBe("qalun");
    expect(readingSlug("al-Duri")).toBe("duri-abu-amr");
    expect(readingSlug("Douri")).toBe("duri-abu-amr");
    expect(readingSlug("duri-abu-amr")).toBe("duri-abu-amr");
    expect(readingSlug("duri-kisai")).toBe("duri-kisai");
    expect(readingSlug("Rewayat Aldori A'n Al-Kisa'i")).toBe("duri-kisai");
    expect(readingSlug("")).toBeNull();
    expect(readingSlug(undefined)).toBeNull();
  });

  it("a script's audio identity needs Hafs reading and Hafs numbering for per-ayah", () => {
    expect(scriptIdentity(uthmani).perAyah).toBe(true);
    expect(scriptIdentity(indopak).perAyah).toBe(false);
    expect(scriptIdentity(warsh).perAyah).toBe(false);
    expect(scriptIdentity(duri).perAyah).toBe(false);
    expect(scriptIdentity(hafsNastaliq).perAyah).toBe(true);
    expect(
      scriptIdentity(script({ id: "x", verse_ids: "hafs", audio: { per_ayah: false } })).perAyah,
    ).toBe(false);
  });
});

describe("state recovery", () => {
  it("malformed stored selections recover to published reader defaults", () => {
    const state = normalizePrefs(
      {
        script: "not-published",
        translations: ["missing", "en-rwwad", "en-rwwad", "too-many"],
        transliteration: "missing",
        font: "missing",
        size: 99,
        continuous: "yes",
        repeat: null,
      },
      catalogue,
    );

    expect(state.script).toBe("uthmani");
    expect(state.translations).toEqual(["en-rwwad"]);
    expect(state.transliteration).toBeNull();
    expect(state.font).toBe("auto");
    expect(state.size).toBe(44);
    expect(state.continuous).toBe(true);
    expect(state.repeat).toBe(false);
  });

  it("invalid saved resume positions are discarded", () => {
    const state = normalizePrefs({ resume: { chapter: 999, verse: 999 } }, catalogue);

    expect(state.resume).toBeNull();
  });

  it("native script chapter counts keep mapped resume links usable", () => {
    expect(nativeChapterCount(duri, 2, 286)).toBe(285);
    expect(nativeChapterCount(duri, 9, 129)).toBe(130);

    const state = normalizePrefs(
      { script: "duri", resume: { chapter: 9, verse: 130 } },
      { ...catalogue, chapters: [{ id: 9, total_verses: 129 } as never] },
    );

    expect(state.resume).toEqual({ chapter: 9, verse: 130 });
  });

  it("a persisted font that does not cover the script falls back to a covering font", () => {
    const state = normalizePrefs({ script: "indopak", font: "amiri" }, catalogue);

    expect(state.font).toBe("auto");

    const resolved = resolveFont(coverage, "indopak", state.font);
    expect(resolved).not.toBe("amiri");
    expect(coverage.scripts.indopak.usable).toContain(resolved);
  });

  it("a persisted font that does cover the script is kept", () => {
    expect(normalizePrefs({ script: "uthmani", font: "noto-naskh-arabic" }, catalogue).font).toBe(
      "noto-naskh-arabic",
    );
    expect(resolveFont(coverage, "uthmani", "noto-naskh-arabic")).toBe("noto-naskh-arabic");
    expect(resolveFont(coverage, "uthmani", "auto")).toBe("amiri");
  });

  it("old links keep applying their options", () => {
    const parsed = parseReaderHash("#/1?s=indopak&t=en-rwwad&f=amiri");
    const state = applyLinkParams(normalizePrefs({}, catalogue), parsed.params, catalogue);

    expect(state.script).toBe("indopak");
    expect(state.translations).toEqual(["en-rwwad"]);
    expect(state.font).toBe("auto");
  });
});

describe("optional chapter validation", () => {
  it("fulfilled payloads must match chapter and sequential text ids", () => {
    expect(() =>
      validateOptionalChapter(
        { id: 2, verses: [{ id: 999, translation: "wrong verse" }] },
        { chapterId: 2, key: "en-rwwad", type: "translation", expectedVerseCount: 1 },
      ),
    ).toThrow(/mismatched/);

    expect(() =>
      validateOptionalChapter(
        { id: 3, verses: [{ id: 1, transliteration: "wrong chapter" }] },
        { chapterId: 2, key: "kemenag", type: "transliteration", expectedVerseCount: 1 },
      ),
    ).toThrow(/invalid chapter/);

    expect(() =>
      validateOptionalChapter(
        { id: 2, verses: [{ id: 1, translation: "truncated" }] },
        { chapterId: 2, key: "en-rwwad", type: "translation", expectedVerseCount: 2 },
      ),
    ).toThrow(/verse count/);

    expect(() =>
      validateOptionalChapter(
        {
          id: 2,
          verses: [
            { id: 1, translation: "one" },
            { id: 2, translation: "two" },
            { id: 3, translation: "extra" },
          ],
        },
        { chapterId: 2, key: "en-rwwad", type: "translation", expectedVerseCount: 2 },
      ),
    ).toThrow(/verse count/);
  });
});

describe("hash routes", () => {
  it("malformed hash values stay parseable for normalisation", () => {
    const parsed = parseReaderHash("#/999:bad?s=missing&t=en-rwwad,missing&tl=missing&f=bad");

    expect(parsed.chapter).toBe(999);
    expect(parsed.verse).toBeNull();
    expect(parsed.invalidVerse).toBe(true);
    expect(parsed.params.get("s")).toBe("missing");
    expect(parsed.params.get("t")).toBe("en-rwwad,missing");
  });

  it("parses surah, verse and the old query form", () => {
    expect(parseReaderHash("#/2")).toMatchObject({ chapter: 2, verse: null });
    expect(parseReaderHash("#/2:255")).toMatchObject({ chapter: 2, verse: 255 });
    expect(parseReaderHash("#/1?s=warsh")).toMatchObject({ chapter: 1, verse: null });
    expect(parseReaderHash("")).toMatchObject({ chapter: null, verse: null });
    expect(parseReaderHash("#/0")).toMatchObject({ chapter: null, invalidChapter: true });
    expect(readerHash(2, 255)).toBe("#/2:255");
    expect(readerHash(2)).toBe("#/2");
  });
});

describe("reading id", () => {
  it("prefers the machine id and matches the audio index spelling", () => {
    const declared = script({
      id: "duri",
      verse_ids: "mapped",
      reading: { id: "duri-abu-amr", riwayah: "al-Duri" },
    });

    expect(scriptReading(declared)).toBe("duri-abu-amr");
    expect(scriptReading(script({ id: "x", verse_ids: "mapped", reading: { id: "warsh" } }))).toBe(
      "warsh",
    );
  });
});

describe("first-visit defaults", () => {
  const editions = [
    edition("/translations/en-other/"),
    edition("/translations/en-saheeh/"),
    edition("/translations/id-kemenag/", { code: "id" }),
    edition("/translations/id-other/", { code: "id" }),
  ];

  it("prefers the visitor's language, then Saheeh, then English", () => {
    expect(defaultTranslation(editions, "id-ID")).toBe(editions[2]);
    expect(defaultTranslation(editions, "fr-FR")).toBe(editions[1]);
    expect(defaultTranslation(editions.slice(0, 1), "fr")).toBe(editions[0]);
    expect(defaultTranslation([], "en")).toBeUndefined();
  });

  it("suggests Indonesian transliteration for Indonesian locales, else English", () => {
    const list = [
      edition("/transliteration/en-simple/"),
      edition("/transliteration/en/"),
      edition("/transliteration/id-skb/"),
    ];

    expect(suggestedTransliteration(list, "id")).toBe(list[2]);
    expect(suggestedTransliteration(list, "de-DE")).toBe(list[1]);
    expect(suggestedTransliteration([], "id")).toBeUndefined();
  });
});
