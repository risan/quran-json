/*
 * Data access. Every artifact this app reads is published as an immutable JSON file on the
 * same origin, so the cache here is only a memo for the current page view: the browser's
 * own HTTP cache does the durable work (the data paths are served `immutable` for a year).
 */

const cache = new Map();

async function getJSON(path) {
  let pending = cache.get(path);
  if (pending) return pending;

  pending = fetch(path, { headers: { accept: "application/json" } }).then((response) => {
    if (!response.ok) throw new Error(`${path} → HTTP ${response.status}`);
    return response.json();
  });

  // A failed read must not be remembered as the answer.
  pending.catch(() => cache.delete(path));
  cache.set(path, pending);
  return pending;
}

export const api = {
  manifest: () => getJSON("/manifest.json"),
  chapters: () => getJSON("/chapters.json"),
  translations: () => getJSON("/translations/index.json"),
  transliterations: () => getJSON("/transliteration/index.json"),
  reciters: () => getJSON("/audio/reciters.json"),
  fonts: () => getJSON("/app/fonts.json"),
  text: (script, chapter) => getJSON(`/text/${script}/chapters/${chapter}.json`),
  translation: (edition, chapter) => getJSON(`/translations/${edition}/chapters/${chapter}.json`),
  transliteration: (edition, chapter) =>
    getJSON(`/transliteration/${edition}/chapters/${chapter}.json`),
};

/** Ayahs before each chapter, so a surah-relative verse can be turned into a global one. */
export function globalOffsets(chapters) {
  const offsets = [];
  let total = 0;
  for (const chapter of chapters) {
    offsets[chapter.id] = total;
    total += chapter.total_verses;
  }
  return offsets;
}

export function globalAyah(offsets, chapter, verse) {
  return (offsets[chapter] ?? 0) + verse;
}

/*
 * Audio URLs are templates, and the three hosts do not agree on how they address an ayah:
 * everyayah wants the surah-relative ayah zero-padded to three digits, cdn.islamic.network
 * wants the global ayah (1..6236) unpadded, mp3quran wants a whole-surah file. The host
 * record publishes `indexing_mode`, `surah_pad` and `ayah_pad` precisely so this function
 * never has to parse the prose.
 */
export function fillTemplate(template, host, { surah, ayah, global }) {
  const pad = (value, width) => (width ? String(value).padStart(width, "0") : String(value));
  const ayahValue = host.indexing_mode === "global-ayah" ? global : ayah;

  // The padded placeholders are replaced first: `{surah}` is a substring of `{surah:03d}`.
  return template
    .replaceAll("{surah:03d}", pad(surah, host.surah_pad ?? 3))
    .replaceAll("{ayah:03d}", pad(ayahValue, host.ayah_pad ?? 3))
    .replaceAll("{surah}", pad(surah, host.surah_pad ?? 0))
    .replaceAll("{ayah}", pad(ayahValue, host.ayah_pad ?? 0));
}

/** Return a reciter's declared reading identity when a source provides one. */
export function riwayahOf(reciter) {
  return reciter?.reading?.riwayah ?? reciter?.riwayah ?? null;
}
