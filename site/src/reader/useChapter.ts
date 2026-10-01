import { useEffect, useState } from "react";

import type {
  Edition,
  ReaderBoot,
  Script,
  TranslationChapter,
  TransliterationChapter,
} from "@/lib/types";
import { api } from "./data";
import {
  alignsWithHafs,
  canJoinWithHafs,
  chapterFurniture,
  editionKey,
  isBismillah,
  mergeChapter,
  showsOpeningBismillah,
  transliterationApplies,
  transliterationNote,
  validateOptionalChapter,
  type MergedVerse,
} from "./core";

export interface ChapterView {
  chapterId: number;
  scriptId: string;
  verses: MergedVerse[];
  /** Unnumbered text before the verses: source furniture, or the script's own bismillah. */
  opening: string[];
  notes: string[];
  translations: Edition[];
  romanisation: Edition | null;
}

export type ChapterState =
  | { status: "loading"; view: ChapterView | null }
  | { status: "ready"; view: ChapterView }
  | { status: "error"; view: null; message: string };

interface Request {
  boot: ReaderBoot;
  script: Script;
  chapterId: number;
  translationKeys: string[];
  transliterationKey: string | null;
  /** Bumped by Retry. */
  attempt: number;
}

type OptionalResult =
  | {
      ok: true;
      type: "translation" | "transliteration";
      edition: Edition;
      payload: TranslationChapter | TransliterationChapter;
    }
  | { ok: false; edition: Edition; error: unknown };

async function loadChapter({
  boot,
  script,
  chapterId,
  translationKeys,
  transliterationKey,
}: Request): Promise<ChapterView> {
  const chapter = boot.chapters.find((entry) => entry.id === chapterId);

  if (!chapter) {
    throw new Error(`There is no chapter ${chapterId}.`);
  }

  // Only a chapter marked unjoinable hides the Hafs-keyed layers. A mapped reading can have a
  // different native count and still join through each verse's `number_in_hafs`.
  const joinable = alignsWithHafs(script, chapterId);
  const wanted = joinable
    ? translationKeys
        .map((key) => boot.translations.find((edition) => editionKey(edition) === key))
        .filter((edition): edition is Edition => edition !== undefined)
    : [];
  const romanisationEdition = boot.transliterations.find(
    (edition) => editionKey(edition) === transliterationKey,
  );
  const romanisationWanted = transliterationApplies(script, romanisationEdition, chapterId);
  const opensWithBismillah = showsOpeningBismillah(script, chapterId);

  const optionalRequests: Promise<OptionalResult>[] = wanted.map((edition) =>
    api
      .translation(editionKey(edition), chapterId)
      .then((payload): OptionalResult => ({
        ok: true,
        type: "translation",
        edition,
        payload: validateOptionalChapter(payload, {
          chapterId,
          key: editionKey(edition),
          type: "translation",
          expectedVerseCount: chapter.total_verses,
        }),
      }))
      .catch((error: unknown): OptionalResult => ({ ok: false, edition, error })),
  );

  if (romanisationWanted && romanisationEdition && transliterationKey) {
    optionalRequests.push(
      api
        .transliteration(transliterationKey, chapterId)
        .then((payload): OptionalResult => ({
          ok: true,
          type: "transliteration",
          edition: romanisationEdition,
          payload: validateOptionalChapter(payload, {
            chapterId,
            key: transliterationKey,
            type: "transliteration",
            expectedVerseCount: chapter.total_verses,
          }),
        }))
        .catch((error: unknown): OptionalResult => ({
          ok: false,
          edition: romanisationEdition,
          error,
        })),
    );
  }

  const [arabic, bismillahSource, optional] = await Promise.all([
    api.text(script.id, chapterId),
    opensWithBismillah ? api.text(script.id, 1).catch(() => null) : Promise.resolve(null),
    Promise.all(optionalRequests),
  ]);

  const notes: string[] = [];
  const mappingValid = canJoinWithHafs(script, arabic.verses);
  const failed = optional.filter((result) => !result.ok);
  const loadedTranslations = optional.flatMap((result) =>
    result.ok && result.type === "translation" ? [result] : [],
  );
  const loadedRomanisation = optional.find(
    (result) => result.ok && result.type === "transliteration",
  );
  const romanisationChapter = loadedRomanisation?.ok
    ? (loadedRomanisation.payload as TransliterationChapter)
    : null;

  if (!joinable && translationKeys.length > 0) {
    notes.push(
      `${script.name} numbers this chapter differently, so translations are hidden here. Read it in another script to see them.`,
    );
  }

  if (joinable && !mappingValid && (translationKeys.length > 0 || transliterationKey)) {
    notes.push("Translations are unavailable: this script chapter has an invalid verse mapping.");
  }

  const readingNote = transliterationNote(script, romanisationEdition, chapterId);

  if (readingNote) {
    notes.push(readingNote);
  }

  if (failed.length > 0) {
    notes.push(
      `Could not load ${failed.map((result) => editionKey(result.edition)).join(", ")}. The Arabic is unaffected.`,
    );
  }

  const verses = mergeChapter({
    arabic,
    script,
    chapterId,
    romanisation:
      loadedRomanisation && romanisationChapter
        ? { edition: loadedRomanisation.edition, chapter: romanisationChapter }
        : null,
    translated: loadedTranslations.map((result) => ({
      key: editionKey(result.edition),
      chapter: result.payload as TranslationChapter,
    })),
  });

  const opening = chapterFurniture(script, chapterId);
  const bismillah = bismillahSource?.verses[0]?.text;

  if (opensWithBismillah && bismillah && isBismillah(bismillah)) {
    opening.push(bismillah);
  }

  return {
    chapterId,
    scriptId: script.id,
    verses,
    opening,
    notes,
    translations: mappingValid ? loadedTranslations.map((result) => result.edition) : [],
    romanisation: mappingValid && loadedRomanisation?.ok ? loadedRomanisation.edition : null,
  };
}

export function useChapter(request: Request): ChapterState {
  const [state, setState] = useState<ChapterState>({ status: "loading", view: null });
  const key = [
    request.script.id,
    request.chapterId,
    request.translationKeys.join(","),
    request.transliterationKey,
    request.attempt,
  ].join("|");

  useEffect(() => {
    let current = true;

    setState((previous) => ({ status: "loading", view: previous.view }));
    loadChapter(request)
      .then((view) => {
        if (current) {
          setState({ status: "ready", view });
        }
      })
      .catch((error: unknown) => {
        if (current) {
          setState({
            status: "error",
            view: null,
            message: error instanceof Error ? error.message : String(error),
          });
        }
      });

    return () => {
      current = false;
    };
    // `key` captures every field of the request that changes what is loaded.
    // oxlint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  return state;
}
