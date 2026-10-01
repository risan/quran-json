import { describe, expect, it } from "vitest";

import {
  audioAvailability,
  audioUrl,
  fillTemplate,
  globalAyah,
  globalOffsets,
  recitersForScript,
  recordingReading,
  recordingVerseIds,
} from "../src/reader/audio";
import type { AudioHost, Reciter, Script } from "../src/lib/types";

function script(partial: Partial<Script> & Pick<Script, "id" | "verse_ids">): Script {
  return {
    name: partial.id,
    description: "",
    verses: 6236,
    path: "",
    chapters: "",
    ...partial,
  };
}

const uthmani = script({ id: "uthmani", verse_ids: "hafs" });
const indopak = script({ id: "indopak", verse_ids: "own", verse_ids_differ_in: [1] });
const warsh = script({ id: "warsh", verse_ids: "mapped" });
const duri = script({ id: "duri", verse_ids: "mapped", reading: { riwayah: "Duri" } });
const hafsNastaliq = script({
  id: "hafs-nastaliq",
  verse_ids: "hafs",
  reading: { qiraah: "Asim", riwayah: "Hafs" },
});

const hafsAyah: Reciter = {
  id: "everyayah/Abdul_Basit_Murattal_64kbps",
  host: "everyayah",
  name: "Abdul Basit",
  scope: "ayah",
  url: "https://everyayah.com/data/Abdul_Basit_Murattal_64kbps/{surah:03d}{ayah:03d}.mp3",
};
const warshAyah: Reciter = {
  id: "everyayah/warsh/warsh_ibrahim_aldosary_128kbps",
  host: "everyayah",
  name: "(Warsh) Ibrahim Al-Dosary",
  scope: "ayah",
  url: "https://everyayah.com/data/warsh/warsh_ibrahim_aldosary_128kbps/{surah:03d}{ayah:03d}.mp3",
};
const hafsSurah: Reciter = {
  id: "mp3quran/1-1",
  host: "mp3quran",
  name: "Ibrahim Al-Akdar",
  recitation: "Rewayat Hafs A'n Assem - Murattal",
  scope: "surah",
  url: "https://server6.mp3quran.net/akdr/{surah:03d}.mp3",
};
const warshSurah: Reciter = {
  id: "mp3quran/54-3",
  host: "mp3quran",
  name: "Someone",
  recitation: "Rewayat Warsh A'n Nafi'",
  scope: "surah",
  url: "https://server.mp3quran.net/w/{surah:03d}.mp3",
};

const everyayah: AudioHost = {
  name: "EveryAyah",
  template: "",
  indexing: "",
  indexing_mode: "surah-relative",
  surah_pad: 3,
  ayah_pad: 3,
  license_status: "unknown",
};
const islamic: AudioHost = {
  name: "Islamic Network",
  template: "",
  indexing: "",
  indexing_mode: "global-ayah",
  surah_pad: 0,
  ayah_pad: 0,
  license_status: "granted",
};

describe("recording identity", () => {
  it("infers the reading from entries that do not declare one", () => {
    expect(recordingReading(hafsAyah)).toBe("hafs");
    expect(recordingReading(warshAyah)).toBe("warsh");
    expect(recordingReading(hafsSurah)).toBe("hafs");
    expect(recordingReading(warshSurah)).toBe("warsh");
    expect(recordingReading({ ...hafsSurah, recitation: undefined })).toBe("hafs");
  });

  it("believes a declared reading and verse numbering", () => {
    const declared = { ...warshAyah, reading: "warsh", verse_ids: "hafs" };

    expect(recordingReading({ ...hafsAyah, reading: { riwayah: "Qalun" } })).toBe("qalun");
    expect(recordingVerseIds(declared)).toBe("hafs");
  });

  it("does not trust the numbering of an undeclared non-Hafs folder", () => {
    expect(recordingVerseIds(hafsAyah)).toBe("hafs");
    expect(recordingVerseIds(warshAyah)).toBe("unknown");
    expect(recordingVerseIds(hafsSurah)).toBeNull();
  });
});

describe("which audio may play", () => {
  it("a Hafs script plays Hafs per-ayah and per-surah audio", () => {
    expect(audioAvailability(uthmani, hafsAyah)).toEqual({ ok: true, mode: "ayah" });
    expect(audioAvailability(hafsNastaliq, hafsAyah)).toEqual({ ok: true, mode: "ayah" });
    expect(audioAvailability(uthmani, hafsSurah)).toEqual({ ok: true, mode: "surah" });
  });

  it("a Hafs script with a Warsh recording gets no per-ayah URL", () => {
    const result = audioAvailability(uthmani, warshAyah);

    expect(result.ok).toBe(false);
    expect(
      audioUrl({
        script: uthmani,
        reciter: warshAyah,
        host: everyayah,
        offsets: [],
        chapter: 1,
        verse: 1,
      }),
    ).toBeNull();
    expect(audioAvailability(uthmani, warshSurah).ok).toBe(false);
  });

  it("a Warsh script with a Hafs recording gets no per-ayah URL", () => {
    expect(audioAvailability(warsh, hafsAyah).ok).toBe(false);
    expect(
      audioUrl({
        script: warsh,
        reciter: hafsAyah,
        host: everyayah,
        offsets: [],
        chapter: 1,
        verse: 1,
      }),
    ).toBeNull();
    expect(audioAvailability(warsh, hafsSurah).ok).toBe(false);
  });

  it("a Warsh script never plays per-ayah audio, even for a Warsh recording", () => {
    expect(audioAvailability(warsh, warshAyah).ok).toBe(false);
    expect(
      audioAvailability(warsh, { ...warshAyah, reading: "warsh", verse_ids: "warsh" }).ok,
    ).toBe(false);
    expect(audioAvailability(warsh, { ...warshAyah, verse_ids: "hafs" }).ok).toBe(false);
  });

  it("a Warsh script plays a Warsh per-surah file", () => {
    expect(audioAvailability(warsh, warshSurah)).toEqual({ ok: true, mode: "surah" });
  });

  it("an own-numbered Hafs script only gets per-surah audio", () => {
    expect(audioAvailability(indopak, hafsAyah).ok).toBe(false);
    expect(audioAvailability(indopak, hafsSurah).ok).toBe(true);
  });

  it("declared readings control per-ayah audio without name special cases", () => {
    const all = [hafsAyah, warshAyah, hafsSurah, warshSurah];
    const ids = (target: Script) => recitersForScript(all, target).map((item) => item.id);

    expect(ids(uthmani)).toEqual([hafsAyah.id, hafsSurah.id]);
    expect(ids(warsh)).toEqual([warshSurah.id]);
    expect(ids(duri)).toEqual([]);
    expect(ids(hafsNastaliq)).toEqual([hafsAyah.id, hafsSurah.id]);
  });
});

describe("audio URLs", () => {
  it("builds each host's addressing", () => {
    const offsets = globalOffsets([
      { id: 1, total_verses: 7 },
      { id: 2, total_verses: 286 },
    ]);

    expect(globalAyah(offsets, 2, 255)).toBe(262);
    expect(
      audioUrl({
        script: uthmani,
        reciter: hafsAyah,
        host: everyayah,
        offsets,
        chapter: 2,
        verse: 255,
      }),
    ).toBe("https://everyayah.com/data/Abdul_Basit_Murattal_64kbps/002255.mp3");
    expect(
      fillTemplate("https://cdn.islamic.network/quran/audio/128/ar.alafasy/{ayah}.mp3", islamic, {
        surah: 2,
        ayah: 255,
        global: 262,
      }),
    ).toBe("https://cdn.islamic.network/quran/audio/128/ar.alafasy/262.mp3");
    expect(
      audioUrl({
        script: uthmani,
        reciter: hafsSurah,
        host: { ...everyayah, indexing_mode: "whole-surah" },
        offsets,
        chapter: 2,
        verse: 255,
      }),
    ).toBe("https://server6.mp3quran.net/akdr/002.mp3");
  });
});
