import { useCallback, useEffect, useRef, useState } from "react";

import type { Chapter, Reciter, ReciterIndex, Script } from "@/lib/types";
import { audioAvailability, audioUrl, globalOffsets } from "./audio";
import { neighbour } from "./player-logic";

/** What is loaded in the player. `verse` is null for a whole-surah file. */
export interface Playing {
  chapter: number;
  verse: number | null;
}

export interface AudioOptions {
  script: Script;
  chapters: Chapter[];
  index: ReciterIndex | null;
  reciter: Reciter | null;
  continuous: boolean;
  repeat: boolean;
  /** Called when playback moves on to another chapter, so the page can follow. */
  onChapterChange: (chapter: number) => void;
}

export interface AudioControls {
  playing: Playing | null;
  isPlaying: boolean;
  error: string | null;
  /** `use` supplies a reciter chosen a moment ago, before the options have re-rendered. */
  play: (
    chapter: number,
    verse: number | null,
    use?: { reciter: Reciter; index: ReciterIndex },
  ) => void;
  toggle: () => void;
  step: (direction: 1 | -1) => void;
  close: () => void;
}

export function useAudio(options: AudioOptions): AudioControls {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const latest = useRef(options);
  const playingRef = useRef<Playing | null>(null);
  const [playing, setPlayingState] = useState<Playing | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    latest.current = options;
  });

  const setPlaying = useCallback((value: Playing | null) => {
    playingRef.current = value;
    setPlayingState(value);
  }, []);

  const start = useCallback(
    async (
      chapter: number,
      verse: number | null,
      use?: { reciter: Reciter; index: ReciterIndex },
    ) => {
      const { script, chapters } = latest.current;
      const reciter = use?.reciter ?? latest.current.reciter;
      const index = use?.index ?? latest.current.index;
      const audio = audioRef.current;

      if (!audio) {
        return;
      }

      if (!reciter || !index) {
        setPlaying({ chapter, verse });
        setError("Choose a reciter in Settings.");

        return;
      }

      const availability = audioAvailability(script, reciter);

      if (!availability.ok) {
        setPlaying({ chapter, verse });
        setError(availability.reason);
        audio.pause();

        return;
      }

      const position = availability.mode === "surah" ? null : (verse ?? 1);
      const url = audioUrl({
        script,
        reciter,
        host: index.hosts[reciter.host],
        offsets: globalOffsets(chapters),
        chapter,
        verse: position ?? 1,
      });

      if (!url) {
        return;
      }

      setPlaying({ chapter, verse: position });
      setError(null);

      if (audio.getAttribute("src") !== url) {
        audio.src = url;
      }

      try {
        await audio.play();
      } catch (failure) {
        // A newer load interrupts this one; that is not an error.
        if (failure instanceof DOMException && failure.name === "NotAllowedError") {
          setError("Press play to start listening.");
        }
      }
    },
    [setPlaying],
  );

  const verseCount = useCallback(
    (chapter: number) => latest.current.chapters[chapter - 1]?.total_verses ?? 0,
    [],
  );

  const advance = useCallback(
    (direction: 1 | -1) => {
      const current = playingRef.current;
      const chapterCount = latest.current.chapters.length;

      if (!current) {
        return;
      }

      const target =
        current.verse === null
          ? current.chapter + direction >= 1 && current.chapter + direction <= chapterCount
            ? { chapter: current.chapter + direction, verse: null }
            : null
          : neighbour(
              { chapter: current.chapter, verse: current.verse },
              direction,
              verseCount,
              chapterCount,
            );

      if (!target) {
        return;
      }

      if (target.chapter !== current.chapter) {
        latest.current.onChapterChange(target.chapter);
      }

      void start(target.chapter, target.verse);
    },
    [start, verseCount],
  );

  useEffect(() => {
    const audio = new Audio();

    audio.preload = "none";
    audioRef.current = audio;

    const sync = () => setIsPlaying(!audio.paused && !audio.ended);
    const ended = () => {
      sync();

      if (latest.current.repeat) {
        audio.currentTime = 0;
        void audio.play();

        return;
      }

      if (latest.current.continuous) {
        advance(1);
      }
    };
    const failed = () => {
      sync();
      setError(audio.currentTime > 0 ? null : "This recording could not be loaded for that verse.");
    };

    audio.addEventListener("play", sync);
    audio.addEventListener("pause", sync);
    audio.addEventListener("ended", ended);
    audio.addEventListener("error", failed);

    return () => {
      audio.pause();
      audio.removeAttribute("src");
      audio.removeEventListener("play", sync);
      audio.removeEventListener("pause", sync);
      audio.removeEventListener("ended", ended);
      audio.removeEventListener("error", failed);
      audioRef.current = null;
    };
  }, [advance]);

  const toggle = useCallback(() => {
    const audio = audioRef.current;
    const current = playingRef.current;

    if (!audio || !current) {
      return;
    }

    if (!audio.getAttribute("src")) {
      void start(current.chapter, current.verse);
    } else if (audio.paused) {
      void audio.play().catch(() => undefined);
    } else {
      audio.pause();
    }
  }, [start]);

  const close = useCallback(() => {
    const audio = audioRef.current;

    audio?.pause();
    audio?.removeAttribute("src");
    setPlaying(null);
    setError(null);
    setIsPlaying(false);
  }, [setPlaying]);

  return {
    playing,
    isPlaying,
    error,
    play: (chapter, verse, use) => void start(chapter, verse, use),
    toggle,
    step: advance,
    close,
  };
}
