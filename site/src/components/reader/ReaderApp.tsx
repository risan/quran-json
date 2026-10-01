import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from "react";

import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetDescription, SheetTitle } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { TooltipProvider } from "@/components/ui/tooltip";
import type { ReaderBoot, Reciter, ReciterIndex } from "@/lib/types";
import { recitersForScript } from "@/reader/audio";
import {
  MAX_TRANSLATIONS,
  applyLinkParams,
  editionKey,
  normalizePrefs,
  parseReaderHash,
  readerHash,
  resolveFont,
  type MergedVerse,
  type ReaderPrefs,
} from "@/reader/core";
import { api } from "@/reader/data";
import { loadStoredPrefs, saveStoredPrefs } from "@/reader/storage";
import { useAudio } from "@/reader/useAudio";
import { useChapter } from "@/reader/useChapter";
import { AudioBar } from "./AudioBar";
import { CommandPalette } from "./CommandPalette";
import { SettingsSheet } from "./SettingsSheet";
import { SurahNav } from "./SurahNav";
import { Toolbar } from "./Toolbar";
import { VerseRow, type VerseAction } from "./VerseRow";

interface Route {
  chapter: number;
  verse: number | null;
}

function initialState(boot: ReaderBoot): {
  prefs: ReaderPrefs;
  route: Route;
  warning: string | null;
} {
  const parsed = parseReaderHash(location.hash);
  const saved = loadStoredPrefs();
  // A first visit reads with an English translation rather than bare Arabic.
  const english = boot.translations.find((edition) => edition.code === "en");
  const stored = normalizePrefs(
    saved ?? { translations: english ? [editionKey(english)] : [] },
    boot,
  );
  const prefs = applyLinkParams(stored, parsed.params, boot);
  const known = boot.chapters.some((chapter) => chapter.id === parsed.chapter);
  const chapter = known ? (parsed.chapter as number) : (prefs.resume?.chapter ?? 1);
  const warning =
    parsed.invalidChapter || (parsed.chapter && !known)
      ? "That link names a surah that does not exist."
      : null;

  return { prefs, route: { chapter, verse: known ? parsed.verse : null }, warning };
}

/** Jump (not glide) to a linked verse, or to the top of the chapter. */
function scrollToVerse(verse: number | null) {
  const target = verse ? document.getElementById(`v${verse}`) : null;

  if (target) {
    target.scrollIntoView({ block: "center", behavior: "instant" });
  } else {
    window.scrollTo({ top: 0, behavior: "instant" });
  }
}

function pickDefaultReciter(playable: Reciter[]): Reciter | null {
  return (
    playable.find((reciter) => reciter.scope === "ayah" && /alafasy.*128/i.test(reciter.id)) ??
    playable.find((reciter) => reciter.scope === "ayah") ??
    playable[0] ??
    null
  );
}

export default function ReaderApp({ boot }: { boot: ReaderBoot }) {
  const initial = useMemo(() => initialState(boot), [boot]);
  const [prefs, setPrefs] = useState<ReaderPrefs>(initial.prefs);
  const [route, setRoute] = useState<Route>(initial.route);
  const [notice, setNotice] = useState<string | null>(initial.warning);
  const [attempt, setAttempt] = useState(0);
  const [surahsOpen, setSurahsOpen] = useState(false);
  const [searchOpen, setSearchOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [reciterIndex, setReciterIndex] = useState<ReciterIndex | null>(null);
  const [reciterError, setReciterError] = useState<string | null>(null);
  const noticeTimer = useRef<number | undefined>(undefined);

  const script = boot.scripts.find((entry) => entry.id === prefs.script) ?? boot.scripts[0];
  const chapter = boot.chapters.find((entry) => entry.id === route.chapter) ?? boot.chapters[0];
  const playable = useMemo(
    () => (reciterIndex ? recitersForScript(reciterIndex.reciters, script) : []),
    [reciterIndex, script],
  );
  const reciter = reciterIndex?.reciters.find((entry) => entry.id === prefs.reciter) ?? null;

  const notify = useCallback((message: string) => {
    setNotice(message);
    window.clearTimeout(noticeTimer.current);
    noticeTimer.current = window.setTimeout(() => setNotice(null), 2600);
  }, []);

  const patch = useCallback(
    (change: Partial<ReaderPrefs>) =>
      setPrefs((previous) => normalizePrefs({ ...previous, ...change }, boot)),
    [boot],
  );

  const go = useCallback((target: number, verse?: number) => {
    window.location.hash = readerHash(target, verse);
  }, []);

  // Routing: the hash is the source of truth for what is on screen.
  useEffect(() => {
    if (!location.hash || parseReaderHash(location.hash).params.size > 0) {
      history.replaceState(null, "", readerHash(route.chapter, route.verse));
    }

    function onHashChange() {
      const parsed = parseReaderHash(location.hash);
      const known = boot.chapters.some((entry) => entry.id === parsed.chapter);

      if (!known) {
        notify("That link names a surah that does not exist.");

        return;
      }

      if (parsed.params.size > 0) {
        setPrefs((previous) => applyLinkParams(previous, parsed.params, boot));
      }

      setRoute({ chapter: parsed.chapter as number, verse: parsed.verse });
    }

    window.addEventListener("hashchange", onHashChange);

    return () => window.removeEventListener("hashchange", onHashChange);
    // The initial route is only used to normalise the first URL.
    // oxlint-disable-next-line react-hooks/exhaustive-deps
  }, [boot, notify]);

  useEffect(() => saveStoredPrefs(prefs), [prefs]);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        setSearchOpen((open) => !open);
      }
    }

    window.addEventListener("keydown", onKey);

    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const state = useChapter({
    boot,
    script,
    chapterId: chapter.id,
    translationKeys: prefs.translations,
    transliterationKey: prefs.transliteration,
    attempt,
  });
  const view = state.view && state.view.chapterId === chapter.id ? state.view : null;

  useEffect(() => {
    document.title = `${chapter.transliteration} · quran-json reader`;
  }, [chapter]);

  // Once a chapter is on screen: remember it, validate a linked verse, and scroll to it.
  const readyKey = view ? view.chapterId : null;

  useEffect(() => {
    if (readyKey === null || !view) {
      return;
    }

    let verse = route.verse;

    if (verse && verse > view.verses.length) {
      notify(`Verse ${verse} is not in ${script.name}'s ${chapter.transliteration}.`);
      history.replaceState(null, "", readerHash(chapter.id));
      verse = null;
    }

    setPrefs((previous) => ({ ...previous, resume: { chapter: chapter.id, verse: verse ?? 1 } }));

    scrollToVerse(verse);

    // Arabic fonts arrive after the first layout and change row heights: settle again.
    let current = true;

    void document.fonts?.ready.then(() => {
      if (current) {
        scrollToVerse(verse);
      }
    });

    return () => {
      current = false;
    };
    // Runs when a chapter finishes loading or the linked verse changes, not on every render.
    // oxlint-disable-next-line react-hooks/exhaustive-deps
  }, [readyKey, route.verse]);

  const loadReciters = useCallback(async (): Promise<ReciterIndex | null> => {
    if (reciterIndex) {
      return reciterIndex;
    }

    try {
      const index = await api.reciters();

      setReciterIndex(index);
      setReciterError(null);

      return index;
    } catch (error) {
      setReciterError(
        error instanceof Error
          ? `Could not load reciters: ${error.message}`
          : "Could not load reciters.",
      );

      return null;
    }
  }, [reciterIndex]);

  const audio = useAudio({
    script,
    chapters: boot.chapters,
    index: reciterIndex,
    reciter,
    continuous: prefs.continuous,
    repeat: prefs.repeat,
    onChapterChange: go,
  });

  // A recording belongs to one reading: stop when the script (and so the reading) changes.
  const scriptId = script.id;
  const closeAudio = audio.close;

  useEffect(() => {
    closeAudio();
  }, [scriptId, closeAudio]);

  const startPlayback = useCallback(
    async (chapterId: number, verse: number | null) => {
      const index = await loadReciters();

      if (!index) {
        notify("Could not load the reciter list. Try again.");

        return;
      }

      const usable = recitersForScript(index.reciters, script);
      const chosen =
        usable.find((entry) => entry.id === prefs.reciter) ?? pickDefaultReciter(usable);

      if (!chosen) {
        notify(`No recording matches the reading of ${script.name}.`);

        return;
      }

      if (chosen.id !== prefs.reciter) {
        patch({ reciter: chosen.id });
      }

      audio.play(chapterId, verse, { reciter: chosen, index });
    },
    [audio, loadReciters, notify, patch, prefs.reciter, script],
  );

  // Follow the verse being played.
  const playing = audio.playing;
  const followKey = playing && playing.chapter === chapter.id ? playing.verse : null;

  useEffect(() => {
    if (followKey === null) {
      return;
    }

    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    document
      .getElementById(`v${followKey}`)
      ?.scrollIntoView({ block: "center", behavior: reduce ? "auto" : "smooth" });
  }, [followKey]);

  async function copy(text: string) {
    try {
      await navigator.clipboard.writeText(text);
      notify("Copied");
    } catch {
      notify("Copy failed. Select the text and copy it.");
    }
  }

  function linkFor(verse: number): string {
    const params = new URLSearchParams();

    if (script.id !== boot.scripts[0].id) {
      params.set("s", script.id);
    }

    if (prefs.translations.length > 0) {
      params.set("t", prefs.translations.join(","));
    }

    const query = params.toString();

    return `${location.origin}${location.pathname}${readerHash(chapter.id, verse)}${query ? `?${query}` : ""}`;
  }

  function onVerseAction(action: VerseAction, verse: MergedVerse) {
    const key = `${chapter.id}:${verse.id}`;

    if (action === "copy-arabic") {
      void copy(`${verse.text}\n${chapter.transliteration} ${key}`);
    } else if (action === "copy-link") {
      void copy(linkFor(verse.id));
    } else if (action === "play-from-here") {
      void startPlayback(chapter.id, verse.id);
    } else if (action === "copy-translation") {
      const parts = (view?.translations ?? []).flatMap((edition) => {
        const text = verse.translations?.[editionKey(edition)];

        return text ? [`${text}\n${edition.author}, ${key}`] : [];
      });

      if (parts.length === 0) {
        notify("No translation is shown for this verse.");
      } else {
        void copy(parts.join("\n\n"));
      }
    }
  }

  function toggleTranslation(key: string) {
    if (prefs.translations.includes(key)) {
      patch({ translations: prefs.translations.filter((entry) => entry !== key) });
    } else if (prefs.translations.length >= MAX_TRANSLATIONS) {
      notify(`Up to ${MAX_TRANSLATIONS} translations at a time.`);
    } else {
      patch({ translations: [...prefs.translations, key] });
    }
  }

  function setPrimaryTranslation(key: string | null) {
    patch({
      translations: key
        ? [key, ...prefs.translations.filter((entry) => entry !== key)].slice(0, MAX_TRANSLATIONS)
        : [],
    });
  }

  const fontId = resolveFont(boot.coverage, script.id, prefs.font);
  const fontName = boot.coverage.fonts.find((font) => font.id === fontId)?.name ?? "Amiri";
  const readingStyle = {
    "--arabic-size": `${prefs.size}px`,
    "--arabic-font": `"${fontName}"`,
  } as CSSProperties;
  const romanisation = view?.romanisation ?? null;
  const showReview = Boolean(romanisation?.review) && prefs.showTransliteration;

  return (
    <TooltipProvider>
      <div className="flex min-h-[calc(100dvh-3rem)] flex-col">
        <Toolbar
          boot={boot}
          chapter={chapter}
          nativeVerseCount={view?.verses.length ?? null}
          script={script}
          primaryTranslation={prefs.translations[0] ?? null}
          onScript={(id) => patch({ script: id })}
          onPrimaryTranslation={setPrimaryTranslation}
          onOpenSurahs={() => setSurahsOpen(true)}
          onOpenSearch={() => setSearchOpen(true)}
          onOpenSettings={() => {
            setSettingsOpen(true);
            void loadReciters();
          }}
          onPlay={() => void startPlayback(chapter.id, route.verse ?? 1)}
        />

        <div className="flex flex-1">
          <aside className="sticky top-[5.5rem] hidden h-[calc(100dvh-5.5rem)] w-64 shrink-0 border-r lg:flex lg:flex-col">
            <SurahNav chapters={boot.chapters} current={chapter.id} className="h-full" />
          </aside>

          <main className="min-w-0 flex-1 px-4 pb-8" style={readingStyle}>
            <div className="mx-auto max-w-[760px]">
              {view?.notes.map((note) => (
                <p
                  key={note}
                  role="note"
                  className="text-muted-foreground border-b py-2 text-[13px]"
                >
                  {note}
                </p>
              ))}
              {showReview ? (
                <p role="note" className="text-muted-foreground border-b py-2 text-[13px]">
                  Transliteration: {romanisation?.review}
                </p>
              ) : null}

              {state.status === "error" ? (
                <div role="alert" className="space-y-3 py-10 text-center">
                  <p className="text-sm">Could not load this surah. {state.message}</p>
                  <Button variant="outline" onClick={() => setAttempt((count) => count + 1)}>
                    Retry
                  </Button>
                </div>
              ) : view ? (
                <div
                  className={
                    state.status === "loading" ? "opacity-60 transition-opacity" : undefined
                  }
                >
                  {view.opening.map((line) => (
                    <p
                      key={line}
                      lang="ar"
                      dir="rtl"
                      className="arabic border-b py-3 text-center"
                      aria-label="Bismillah"
                    >
                      {line}
                    </p>
                  ))}
                  <ol aria-label={`Verses of ${chapter.transliteration}`}>
                    {view.verses.map((verse) => (
                      <VerseRow
                        key={verse.id}
                        chapterId={chapter.id}
                        verse={verse}
                        translations={view.translations}
                        romanisation={romanisation}
                        showArabic={prefs.showArabic}
                        showTransliteration={prefs.showTransliteration}
                        showTranslations={prefs.showTranslations}
                        playing={playing?.chapter === chapter.id && playing.verse === verse.id}
                        linked={route.verse === verse.id}
                        onAction={onVerseAction}
                      />
                    ))}
                  </ol>
                </div>
              ) : (
                <div aria-busy="true" aria-label="Loading" className="space-y-1">
                  {Array.from({ length: 6 }, (_, index) => (
                    <div key={index} className="space-y-2 border-b py-4">
                      <Skeleton className="ml-auto h-8 w-4/5" />
                      <Skeleton className="h-4 w-full" />
                      <Skeleton className="h-4 w-2/3" />
                    </div>
                  ))}
                </div>
              )}
            </div>
          </main>
        </div>

        {playing ? (
          <AudioBar
            reciter={reciter}
            playing={playing}
            isPlaying={audio.isPlaying}
            error={audio.error}
            continuous={prefs.continuous}
            repeat={prefs.repeat}
            onToggle={audio.toggle}
            onStep={audio.step}
            onContinuous={() => patch({ continuous: !prefs.continuous })}
            onRepeat={() => patch({ repeat: !prefs.repeat })}
            onClose={audio.close}
            onShow={() => go(playing.chapter, playing.verse ?? undefined)}
          />
        ) : null}
      </div>

      <Sheet open={surahsOpen} onOpenChange={setSurahsOpen}>
        <SheetContent side="left" className="w-72 gap-0 p-0">
          <div className="border-b px-4 py-3">
            <SheetTitle>Surahs</SheetTitle>
            <SheetDescription className="sr-only">Choose a surah to read.</SheetDescription>
          </div>
          <SurahNav
            chapters={boot.chapters}
            current={chapter.id}
            onSelect={() => setSurahsOpen(false)}
            className="min-h-0 flex-1"
          />
        </SheetContent>
      </Sheet>

      <CommandPalette
        open={searchOpen}
        onOpenChange={setSearchOpen}
        chapters={boot.chapters}
        onGo={go}
      />

      <SettingsSheet
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
        boot={boot}
        prefs={prefs}
        script={script}
        onChange={patch}
        onToggleTranslation={toggleTranslation}
        reciterIndex={reciterIndex}
        reciters={playable}
        reciterError={reciterError}
        onNeedReciters={() => void loadReciters()}
      />

      <output className="pointer-events-none fixed inset-x-0 bottom-16 z-50 flex justify-center px-4">
        {notice ? (
          <p className="bg-popover text-popover-foreground rounded-md border px-3 py-1.5 text-[13px] shadow-md">
            {notice}
          </p>
        ) : null}
      </output>
    </TooltipProvider>
  );
}
