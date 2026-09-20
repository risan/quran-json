/* Pure reader rules shared by the controller and executable reader regressions. */

export const DEFAULT_READER_STATE = Object.freeze({
  script: null,
  translations: [],
  transliteration: null,
  reciter: null,
  font: "auto",
  size: 3,
  autoplay: true,
  repeat: false,
});

export function editionKey(edition) {
  return edition.path.replace(/\/$/, "").split("/").pop();
}

/** Parse a reader hash without trusting any value supplied by a link. */
export function parseReaderHash(rawHash) {
  const raw = String(rawHash ?? "").replace(/^#/, "");
  const [path = "", query = ""] = raw.split("?");
  const parts = path.replace(/^\//, "").split(":");
  const positive = (value) => {
    const number = Number(value);
    return Number.isInteger(number) && number > 0 ? number : null;
  };
  const params = new URLSearchParams(query);
  return {
    chapter: positive(parts[0]),
    verse: positive(parts[1]),
    invalidChapter: Boolean(parts[0] && positive(parts[0]) === null),
    invalidVerse: Boolean(parts[1] && positive(parts[1]) === null),
    params,
  };
}

export function hafsNumbers(script, verse) {
  if (script.verse_ids === "mapped") {
    const mapped = verse.number_in_hafs;
    if (Array.isArray(mapped)) return mapped;
    if (Number.isInteger(mapped)) return [mapped];
    return [];
  }
  return [verse.id];
}

function objectOrEmpty(value) {
  return value && typeof value === "object" && !Array.isArray(value) ? value : {};
}

function normalized(value) {
  return String(value ?? "").trim().toLowerCase();
}

/**
 * Read the identity a manifest declares for a script and its audio.
 *
 * Older manifests only have `verse_ids`; those still get a conservative fallback. New
 * riwayat must declare their reading identity so a name such as Duri cannot accidentally be
 * treated as Hafs merely because one chapter happens to map to the Hafs count.
 */
export function scriptReadingIdentity(script) {
  const descriptor = objectOrEmpty(script);
  const reading = objectOrEmpty(descriptor.reading);
  const audio = objectOrEmpty(descriptor.audio);
  const riwayah = reading.riwayah ?? descriptor.riwayah ?? null;
  const verseNumbering = reading.verse_numbering ?? descriptor.verse_ids ?? null;
  const audioVerseNumbering =
    audio.verse_numbering ?? audio.verse_ids ?? descriptor.audio_verse_ids ?? null;
  const explicitPerAyah =
    typeof audio.per_ayah === "boolean"
      ? audio.per_ayah
      : typeof descriptor.per_ayah_audio === "boolean"
        ? descriptor.per_ayah_audio
        : null;
  const isHafsReading = !riwayah || normalized(riwayah) === "hafs";
  const numberingMatches =
    audioVerseNumbering === null ||
    verseNumbering === null ||
    normalized(audioVerseNumbering) === normalized(verseNumbering);

  return {
    id: descriptor.id ?? null,
    name: descriptor.name ?? riwayah ?? descriptor.id ?? "selected script",
    qiraah: reading.qiraah ?? descriptor.qiraah ?? null,
    riwayah,
    verseNumbering,
    audioVerseNumbering,
    perAyah: explicitPerAyah ?? (isHafsReading && verseNumbering === "hafs" && numberingMatches),
  };
}

/** Whether the manifest says an ayah-scoped audio URL can follow this script. */
export function scriptAllowsAyahAudio(script) {
  return scriptReadingIdentity(script).perAyah;
}

/** Return a script's native chapter count when a newer manifest publishes one. */
export function nativeChapterCount(script, chapterId, fallback = null) {
  const rawCounts = script?.native_chapter_counts;
  const counts = objectOrEmpty(rawCounts);
  const value = Array.isArray(rawCounts)
    ? rawCounts[Number(chapterId) - 1]
    : counts[String(chapterId)] ?? counts[chapterId];
  return Number.isInteger(value) && value > 0 ? value : fallback;
}

/** Whether a chapter can be joined to Hafs-keyed optional layers. */
export function alignsWithHafs(script, chapterId) {
  const explicit = script.verse_ids_unjoinable_in ?? script.alignment_exceptions;
  // A mapped reading may have a different native count and still join through
  // `number_in_hafs`. Count differences alone are therefore not an alignment failure.
  const unjoinable =
    explicit ?? (script.verse_ids === "mapped" ? [] : script.verse_ids_differ_in ?? []);
  return !unjoinable.includes(Number(chapterId));
}

/** A mapped reading must carry an explicit Hafs map for every native verse. */
export function canJoinWithHafs(script, verses) {
  return (
    script.verse_ids !== "mapped" ||
    verses.every(
      (verse) => {
        const numbers = verse.number_in_hafs;
        return (
          Array.isArray(numbers) &&
          numbers.length > 0 &&
          numbers.every((number) => Number.isInteger(number) && number > 0) &&
          numbers.every((number, index) => index === 0 || number > numbers[index - 1])
        );
      },
    )
  );
}

/** Reject a fulfilled optional payload before any positional join can occur. */
export function validateOptionalChapter(payload, { chapterId, key, type, expectedVerseCount }) {
  const field = type === "transliteration" ? "transliteration" : "translation";
  if (
    !payload ||
    payload.id !== Number(chapterId) ||
    !Array.isArray(payload.verses) ||
    !Number.isInteger(expectedVerseCount) ||
    expectedVerseCount < 1 ||
    payload.verses.length !== expectedVerseCount
  ) {
    throw new Error(key + " returned an invalid chapter payload or verse count");
  }
  for (let index = 0; index < payload.verses.length; index += 1) {
    const verse = payload.verses[index];
    if (
      !verse ||
      verse.id !== index + 1 ||
      typeof verse[field] !== "string"
    ) {
      throw new Error(key + " returned mismatched or incomplete verse data");
    }
  }
  return payload;
}

/** Merge only optional layers whose verse identity can be joined safely. */
export function mergeChapter({ arabic, romanisation, translated, script, chapterId = arabic.id }) {
  const aligned = alignsWithHafs(script, chapterId) && canJoinWithHafs(script, arabic.verses);

  return arabic.verses.map((verse) => {
    const merged = { ...verse };

    if (aligned && romanisation) {
      const parts = hafsNumbers(script, verse)
        .map((number) => romanisation.verses[number - 1])
        .filter(Boolean);
      if (parts.length) merged.transliteration = parts.map((entry) => entry.transliteration).join(" ");
    }

    const numbers = hafsNumbers(script, verse);
    const translations = {};
    const footnotes = {};

    for (const { key, chapter } of aligned ? translated : []) {
      const parts = numbers.map((number) => chapter.verses[number - 1]).filter(Boolean);
      if (!parts.length) continue;

      translations[key] = parts.map((entry) => entry.translation).join(" ");
      const notes = parts.map((entry) => entry.footnotes).filter(Boolean);
      if (notes.length) footnotes[key] = notes.join("\n\n");
    }

    if (Object.keys(translations).length) merged.translations = translations;
    if (Object.keys(footnotes).length) merged.footnotes = footnotes;

    return merged;
  });
}

export function recitersForScript(reciters, script) {
  const allowsAyah = scriptAllowsAyahAudio(script);
  return reciters.filter(
    (reciter) => reciter.scope === "surah" || allowsAyah,
  );
}

export function normalizeReaderState(
  raw,
  { manifest, chapters = [], translations, transliterations, coverage, reciters = null },
) {
  const state = { ...DEFAULT_READER_STATE, ...(raw && typeof raw === "object" ? raw : {}) };
  const scripts = manifest?.scripts ?? [];
  const script = scripts.find((entry) => entry.id === state.script) ?? scripts[0] ?? null;
  const coverageEntry = script ? coverage?.scripts?.[script.id] : null;
  const editionKeys = new Set((translations?.editions ?? []).map(editionKey));
  const transliterationKeys = new Set((transliterations?.editions ?? []).map(editionKey));
  const resumeChapter = Number.isInteger(state.resume?.chapter)
    ? chapters.find((chapter) => chapter.id === state.resume.chapter)
    : null;
  const resumeLimit = resumeChapter
    ? nativeChapterCount(script, resumeChapter.id, resumeChapter.total_verses)
    : null;
  const resumeVerse =
    Number.isInteger(state.resume?.verse) &&
    state.resume.verse > 0 &&
    resumeChapter &&
    state.resume.verse <= resumeLimit
      ? state.resume.verse
      : null;

  return {
    ...state,
    script: script?.id ?? null,
    translations: Array.isArray(state.translations)
      ? [...new Set(state.translations.filter((key) => editionKeys.has(key)))].slice(0, 3)
      : [],
    transliteration:
      typeof state.transliteration === "string" && transliterationKeys.has(state.transliteration)
        ? state.transliteration
        : null,
    reciter:
      reciters?.reciters?.some((entry) => entry.id === state.reciter) ? state.reciter :
        reciters ? null : state.reciter,
    font:
      state.font === "auto" || coverageEntry?.usable?.includes(state.font)
        ? state.font
        : "auto",
    size: Number.isInteger(state.size) ? Math.min(6, Math.max(1, state.size)) : 3,
    autoplay: typeof state.autoplay === "boolean" ? state.autoplay : true,
    repeat: typeof state.repeat === "boolean" ? state.repeat : false,
    resume: resumeChapter && resumeVerse ? { chapter: resumeChapter.id, verse: resumeVerse } : null,
  };
}
