import assert from "node:assert/strict";
import test from "node:test";

import {
  alignsWithHafs,
  canJoinWithHafs,
  mergeChapter,
  nativeChapterCount,
  normalizeReaderState,
  parseReaderHash,
  recitersForScript,
  scriptReadingIdentity,
  validateOptionalChapter,
} from "../../web/app/reader-core.js";

const manifest = {
  scripts: [
    { id: "uthmani", verse_ids: "hafs" },
    { id: "indopak", verse_ids: "own", verse_ids_differ_in: [1] },
    { id: "warsh", verse_ids: "mapped" },
    {
      id: "duri",
      name: "al-Duri",
      verse_ids: "mapped",
      verse_ids_differ_in: [2, 4],
      verse_ids_unjoinable_in: [],
      native_chapter_counts: { "2": 285, "9": 130 },
      reading: { qiraah: "Abu Amr", riwayah: "Duri" },
    },
    {
      id: "hafs-nastaliq",
      name: "Hafs Nastaliq",
      verse_ids: "hafs",
      reading: { qiraah: "Asim", riwayah: "Hafs" },
    },
  ],
};
const coverage = { scripts: { uthmani: { usable: ["amiri"] }, indopak: { usable: ["naskh"] } } };
const translations = { editions: [{ path: "/translations/en-rwwad/", code: "en" }] };
const transliterations = { editions: [{ path: "/transliteration/kemenag/", code: "id" }] };
const chapters = [{ id: 1, total_verses: 7 }];

function chapter(verses) {
  return { id: 1, verses };
}

test("Indo-Pak divergent chapters suppress every Hafs-keyed optional layer", () => {
  const script = manifest.scripts[1];
  const arabic = chapter([
    { id: 1, text: "al-hamdu" },
    { id: 2, text: "rabb" },
  ]);
  const romanisation = chapter([
    { id: 1, transliteration: "basmala" },
    { id: 2, transliteration: "al-hamdu" },
  ]);
  const translated = [{
    key: "en-rwwad",
    chapter: chapter([
      { id: 1, translation: "basmala translation" },
      { id: 2, translation: "al-hamdu translation" },
    ]),
  }];

  assert.equal(alignsWithHafs(script, 1), false);
  const merged = mergeChapter({ arabic, romanisation, translated, script, chapterId: 1 });
  assert.equal(merged[0].transliteration, undefined);
  assert.equal(merged[0].translations, undefined);
  assert.equal(merged[1].transliteration, undefined);
  assert.equal(merged[1].translations, undefined);
});

test("mapped Warsh verses join each Hafs translation exactly once", () => {
  const script = manifest.scripts[2];
  const arabic = chapter([{ id: 1, text: "warsh", number_in_hafs: [1, 2] }]);
  const translated = [{
    key: "en-rwwad",
    chapter: chapter([
      { id: 1, translation: "first", footnotes: "first note" },
      { id: 2, translation: "second", footnotes: "second note" },
    ]),
  }];

  const merged = mergeChapter({ arabic, romanisation: null, translated, script, chapterId: 1 });
  assert.deepEqual(merged[0].translations, { "en-rwwad": "first second" });
  assert.deepEqual(merged[0].footnotes, { "en-rwwad": "first note\n\nsecond note" });
});

test("mapped Duri Fatiha joins its explicit source mapping", () => {
  const script = { ...manifest.scripts[3], verse_ids_differ_in: [] };
  const arabic = chapter([
    { id: 1, text: "bismillah", number_in_hafs: [2] },
    { id: 2, text: "one", number_in_hafs: [3] },
    { id: 3, text: "two", number_in_hafs: [4] },
    { id: 4, text: "three", number_in_hafs: [5] },
    { id: 5, text: "four", number_in_hafs: [6] },
    { id: 6, text: "five", number_in_hafs: [7] },
    { id: 7, text: "six", number_in_hafs: [7] },
  ]);
  const translated = [{
    key: "en-rwwad",
    chapter: chapter([
      { id: 1, translation: "basmala" },
      { id: 2, translation: "one" },
      { id: 3, translation: "two" },
      { id: 4, translation: "three" },
      { id: 5, translation: "four" },
      { id: 6, translation: "five" },
      { id: 7, translation: "six" },
    ]),
  }];

  assert.equal(alignsWithHafs(script, 1), true);
  const merged = mergeChapter({ arabic, romanisation: null, translated, script, chapterId: 1 });
  assert.equal(merged[0].translations["en-rwwad"], "one");
  assert.equal(merged.at(-2).translations["en-rwwad"], "six");
  assert.equal(merged.at(-1).translations["en-rwwad"], "six");
});

test("explicit unjoinable chapters override broad count-difference metadata", () => {
  const script = {
    id: "duri",
    verse_ids: "mapped",
    verse_ids_differ_in: [1, 2, 4],
    verse_ids_unjoinable_in: [1],
  };
  assert.equal(alignsWithHafs(script, 1), false);
  assert.equal(alignsWithHafs(script, 2), true);
});

test("mapped count differences remain joinable without an explicit exception", () => {
  const script = { id: "duri", verse_ids: "mapped", verse_ids_differ_in: [1, 2, 4] };
  assert.equal(alignsWithHafs(script, 1), true);
  assert.equal(alignsWithHafs(script, 2), true);
});

test("mapped readings without an explicit map do not guess optional joins", () => {
  const script = { id: "duri", verse_ids: "mapped" };
  const arabic = chapter([{ id: 1, text: "unmapped" }]);
  assert.equal(canJoinWithHafs(script, arabic.verses), false);
  const merged = mergeChapter({
    arabic,
    romanisation: { id: 1, verses: [{ id: 1, transliteration: "wrong" }] },
    translated: [{ key: "en", chapter: { id: 1, verses: [{ id: 1, translation: "wrong" }] } }],
    script,
    chapterId: 1,
  });
  assert.equal(merged[0].transliteration, undefined);
  assert.equal(merged[0].translations, undefined);
});

test("declared readings control Hafs per-ayah audio without name special cases", () => {
  const reciters = [
    { id: "ayah", scope: "ayah" },
    { id: "surah", scope: "surah" },
  ];
  assert.deepEqual(recitersForScript(reciters, manifest.scripts[2]).map((item) => item.id), ["surah"]);
  assert.deepEqual(recitersForScript(reciters, manifest.scripts[3]).map((item) => item.id), ["surah"]);
  assert.deepEqual(recitersForScript(reciters, manifest.scripts[4]).map((item) => item.id), ["ayah", "surah"]);
  assert.equal(scriptReadingIdentity(manifest.scripts[3]).riwayah, "Duri");
});

test("malformed stored selections recover to published reader defaults", () => {
  const state = normalizeReaderState(
    {
      script: "not-published",
      translations: ["missing", "en-rwwad", "en-rwwad", "too-many"],
      transliteration: "missing",
      font: "missing",
      size: 99,
      autoplay: "yes",
      repeat: null,
    },
    { manifest, translations, transliterations, coverage },
  );

  assert.equal(state.script, "uthmani");
  assert.deepEqual(state.translations, ["en-rwwad"]);
  assert.equal(state.transliteration, null);
  assert.equal(state.font, "auto");
  assert.equal(state.size, 6);
  assert.equal(state.autoplay, true);
  assert.equal(state.repeat, false);
});

test("invalid saved resume positions are discarded", () => {
  const state = normalizeReaderState(
    { resume: { chapter: 999, verse: 999 } },
    { manifest, chapters, translations, transliterations, coverage },
  );
  assert.equal(state.resume, null);
});

test("native script chapter counts keep mapped resume links usable", () => {
  const script = manifest.scripts[3];
  assert.equal(nativeChapterCount(script, 2, 286), 285);
  assert.equal(nativeChapterCount(script, 9, 129), 130);
  const state = normalizeReaderState(
    { script: "duri", resume: { chapter: 9, verse: 130 } },
    {
      manifest,
      chapters: [{ id: 9, total_verses: 129 }],
      translations,
      transliterations,
      coverage,
    },
  );
  assert.deepEqual(state.resume, { chapter: 9, verse: 130 });
});

test("fulfilled optional payloads must match chapter and sequential text IDs", () => {
  assert.throws(
    () =>
      validateOptionalChapter(
        { id: 2, verses: [{ id: 999, translation: "wrong verse" }] },
        { chapterId: 2, key: "en-rwwad", type: "translation", expectedVerseCount: 1 },
      ),
    /mismatched/,
  );
  assert.throws(
    () =>
      validateOptionalChapter(
        { id: 3, verses: [{ id: 1, transliteration: "wrong chapter" }] },
        { chapterId: 2, key: "kemenag", type: "transliteration", expectedVerseCount: 1 },
      ),
    /invalid chapter/,
  );
  assert.throws(
    () =>
      validateOptionalChapter(
        { id: 2, verses: [{ id: 1, translation: "truncated" }] },
        { chapterId: 2, key: "en-rwwad", type: "translation", expectedVerseCount: 2 },
      ),
    /verse count/,
  );
  assert.throws(
    () =>
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
    /verse count/,
  );
});

test("malformed hash values stay parseable for controller normalization", () => {
  const parsed = parseReaderHash("#/999:bad?s=missing&t=en-rwwad,missing&tl=missing&f=bad");
  assert.equal(parsed.chapter, 999);
  assert.equal(parsed.verse, null);
  assert.equal(parsed.params.get("s"), "missing");
  assert.equal(parsed.params.get("t"), "en-rwwad,missing");
});
