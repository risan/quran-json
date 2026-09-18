/*
 * The recitation player.
 *
 * Two shapes of audio exist in the index and they behave differently, so the player has two
 * modes rather than one:
 *
 * * **Ayah scope** (everyayah, cdn.islamic.network): one file per verse, played in sequence
 *   with the "play the next verse" toggle. This is the mode a reader wants, because the
 *   playing verse can be followed in the text.
 * * **Surah scope** (mp3quran, cdn.islamic.network): one file per chapter. It cannot be
 *   followed verse by verse, since no host here publishes timings.
 *
 * Riwayah safety: every per-ayah recitation in the index is Hafs, and a Hafs ayah number
 * means nothing in Warsh or Qalun, which number 6,214 ayahs. So per-ayah playback is
 * refused for those scripts rather than playing the wrong verse, and the caller only offers
 * surah-scope recitations there.
 */

import { fillTemplate, globalAyah } from "./api.js";

export class Player {
  constructor(audio) {
    this.audio = audio;
    this.reciter = null;
    this.host = null;
    this.chapter = null;
    this.verse = null;
    this.offsets = null;
    this.autoplay = true;
    this.repeat = false;
    this.riwayah = "hafs";
    this.error = null;
    this.open = false; // the bar is shown from the first play until it is closed

    this.onVerse = () => {};
    this.onProgress = () => {};
    this.onState = () => {};
    this.onChapterEnd = () => {};

    audio.addEventListener("play", () => this.onState());
    audio.addEventListener("pause", () => this.onState());
    audio.addEventListener("timeupdate", () => this.onProgress(this.progress()));
    audio.addEventListener("loadedmetadata", () => this.onProgress(this.progress()));
    audio.addEventListener("ended", () => this.ended());
    audio.addEventListener("error", () => {
      this.error = this.audio.currentTime > 0 ? null : "This recitation has no audio for that verse.";
      this.onState();
    });
  }

  /** Point the player at a chapter, and at the riwayah the reader is looking at. */
  configure({ reciters, chapter, offsets, riwayah = "hafs" }) {
    this.reciters = reciters;
    this.chapter = chapter;
    this.offsets = offsets;
    this.riwayah = riwayah;
  }

  /** Every per-ayah recitation published here is Hafs; a Nafiʿ script numbers differently. */
  get conflicted() {
    return this.riwayah !== "hafs" && this.reciter?.scope === "ayah";
  }

  get playing() {
    return !this.audio.paused && !this.audio.ended;
  }

  progress() {
    const duration = this.audio.duration;
    return Number.isFinite(duration) && duration > 0 ? this.audio.currentTime / duration : 0;
  }

  setReciter(id) {
    this.reciter = this.reciters?.reciters.find((entry) => entry.id === id) ?? null;
    this.host = this.reciter ? this.reciters.hosts[this.reciter.host] : null;
    this.error = null;
    return this.reciter;
  }

  url({ chapter, verse }) {
    return fillTemplate(this.reciter.url, this.host, {
      surah: chapter,
      ayah: verse,
      global: globalAyah(this.offsets, chapter, verse),
    });
  }

  /** Play one verse of the current chapter, or the whole chapter for a surah-scope reciter. */
  async start(verse = null) {
    if (!this.reciter) return;

    // Open the bar first: a refusal is explained in the bar, so it has to be visible.
    this.open = true;

    if (this.conflicted) {
      this.error = `This recitation follows the Hafs ayah numbering, and ${this.riwayah} does not share it. Pick a ${this.riwayah} surah recitation instead.`;
      this.onState();
      return;
    }

    this.error = null;
    this.verse = this.reciter.scope === "surah" ? null : verse ?? this.verse ?? 1;

    const source =
      this.reciter.scope === "surah"
        ? this.url({ chapter: this.chapter.id, verse: 1 })
        : this.url({ chapter: this.chapter.id, verse: this.verse });

    if (this.audio.src !== source) {
      this.audio.src = source;
      this.audio.load();
    }

    this.onVerse(this.verse);
    try {
      await this.audio.play();
    } catch {
      // Autoplay policies refuse a programmatic play before the first user gesture. The
      // controls stay usable, so the reader can press play themselves.
      this.error = "Press play to start listening.";
    }
    this.onState();
  }

  toggle() {
    if (!this.audio.src) return this.start(this.verse);
    if (this.playing) this.audio.pause();
    else this.audio.play().catch(() => {});
    return undefined;
  }

  async ended() {
    if (this.repeat) {
      this.audio.currentTime = 0;
      await this.audio.play().catch(() => {});
      return;
    }

    if (this.reciter.scope === "surah" || !this.autoplay) {
      this.onState();
      return;
    }

    const nextVerse = (this.verse ?? 0) + 1;
    if (nextVerse <= this.chapter.total_verses) {
      await this.start(nextVerse);
      return;
    }

    this.onChapterEnd();
  }

  async step(delta) {
    if (this.reciter?.scope === "surah") {
      this.onChapterEnd(delta);
      return;
    }

    const target = (this.verse ?? 1) + delta;
    if (target < 1) return;
    if (target > this.chapter.total_verses) {
      this.onChapterEnd();
      return;
    }
    await this.start(target);
  }

  seek(fraction) {
    if (Number.isFinite(this.audio.duration)) {
      this.audio.currentTime = fraction * this.audio.duration;
    }
  }

  /** Dismiss the bar without forgetting the recitation: the next play reopens it. */
  close() {
    this.audio.pause();
    this.audio.removeAttribute("src");
    this.error = null;
    this.verse = null;
    this.open = false;
    this.onState();
  }
}
