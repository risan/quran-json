/**
 * Which recording may play for which script, and how its URL is built.
 *
 * A recording has a reading (whose words it recites) and, when it is split per ayah, a verse
 * numbering. A script has the same two properties. An ayah-scoped URL is built from a Hafs
 * verse number, so it is only valid when the script is Hafs, numbered like Hafs, and the
 * recording is Hafs recited in Hafs numbering. A whole-surah file has no verse number, so it
 * only needs the readings to match.
 */

import type { AudioHost, Chapter, Reciter, Script } from "@/lib/types";
import { readingSlug, scriptIdentity } from "./core";

/**
 * The reading a recording recites. Newer indexes declare `reading`; older ones do not, so it is
 * inferred from what the entry names: an EveryAyah Warsh folder, or an MP3Quran `recitation`
 * text that names a riwayah. Anything else is Hafs, which is what the rest of the index is.
 */
export function recordingReading(reciter: Reciter): string {
  const declared =
    typeof reciter.reading === "string" ? reciter.reading : (reciter.reading?.riwayah ?? null);
  const slug = readingSlug(declared);

  if (slug) {
    return slug;
  }

  if (/warsh/i.test(reciter.id)) {
    return "warsh";
  }

  return readingSlug(reciter.recitation) ?? "hafs";
}

/**
 * The verse numbering of an ayah-scoped recording. Undeclared Hafs recordings follow Hafs
 * numbering; an undeclared recording of another reading is `unknown`, since its numbering has
 * not been checked against the files.
 */
export function recordingVerseIds(reciter: Reciter): string | null {
  if (reciter.scope !== "ayah") {
    return null;
  }

  if (reciter.verse_ids) {
    return reciter.verse_ids;
  }

  return recordingReading(reciter) === "hafs" ? "hafs" : "unknown";
}

export type AudioAvailability =
  | { ok: true; mode: "ayah" | "surah" }
  | { ok: false; reason: string };

export function audioAvailability(script: Script, reciter: Reciter): AudioAvailability {
  const identity = scriptIdentity(script);
  const reading = recordingReading(reciter);

  if (reading !== identity.reading) {
    return {
      ok: false,
      reason: `This recording is ${reading}; ${script.name} is ${identity.reading}.`,
    };
  }

  if (reciter.scope === "surah") {
    return { ok: true, mode: "surah" };
  }

  if (!identity.perAyah) {
    return {
      ok: false,
      reason: `Per-ayah audio follows Hafs numbering, which ${script.name} does not declare.`,
    };
  }

  if (recordingVerseIds(reciter) !== "hafs") {
    return { ok: false, reason: "This recording's verse numbering is not confirmed as Hafs." };
  }

  return { ok: true, mode: "ayah" };
}

/** The recordings that can play for this script. */
export function recitersForScript(reciters: Reciter[], script: Script): Reciter[] {
  return reciters.filter((reciter) => audioAvailability(script, reciter).ok);
}

/** Ayahs before each chapter, so a surah-relative verse can be turned into a global one. */
export function globalOffsets(chapters: Pick<Chapter, "id" | "total_verses">[]): number[] {
  const offsets: number[] = [];
  let total = 0;

  for (const chapter of chapters) {
    offsets[chapter.id] = total;
    total += chapter.total_verses;
  }

  return offsets;
}

export function globalAyah(offsets: number[], chapter: number, verse: number): number {
  return (offsets[chapter] ?? 0) + verse;
}

function pad(value: number, width: number): string {
  return width ? String(value).padStart(width, "0") : String(value);
}

/**
 * Fill a URL template. The three hosts disagree about how an ayah is addressed: EveryAyah wants
 * the surah-relative ayah zero-padded, Islamic Network wants the global ayah, MP3Quran a whole
 * surah file. The host record publishes `indexing_mode` and the pad widths for exactly this.
 */
export function fillTemplate(
  template: string,
  host: Pick<AudioHost, "indexing_mode" | "surah_pad" | "ayah_pad">,
  position: { surah: number; ayah: number; global: number },
): string {
  const ayah = host.indexing_mode === "global-ayah" ? position.global : position.ayah;

  // The padded placeholders go first: `{surah}` is a substring of `{surah:03d}`.
  return template
    .replaceAll("{surah:03d}", pad(position.surah, host.surah_pad ?? 3))
    .replaceAll("{ayah:03d}", pad(ayah, host.ayah_pad ?? 3))
    .replaceAll("{surah}", pad(position.surah, host.surah_pad ?? 0))
    .replaceAll("{ayah}", pad(ayah, host.ayah_pad ?? 0));
}

/** The URL to play for a recording, or null when this script may not use it. */
export function audioUrl(options: {
  script: Script;
  reciter: Reciter;
  host: AudioHost;
  offsets: number[];
  chapter: number;
  verse: number;
}): string | null {
  const { script, reciter, host, offsets, chapter, verse } = options;
  const availability = audioAvailability(script, reciter);

  if (!availability.ok) {
    return null;
  }

  return fillTemplate(reciter.url, host, {
    surah: chapter,
    ayah: availability.mode === "surah" ? 1 : verse,
    global: globalAyah(offsets, chapter, verse),
  });
}
