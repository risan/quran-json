/**
 * Data access. Files are fetched relative to the site origin, unless
 * `PUBLIC_QURAN_JSON_DATA_BASE` points somewhere else (a local data server, say). A successful
 * response is remembered for the page view; a failed one is not, so Retry really retries.
 */

import type {
  ReciterIndex,
  TextChapter,
  TranslationChapter,
  TransliterationChapter,
} from "@/lib/types";

const BASE = String(import.meta.env.PUBLIC_QURAN_JSON_DATA_BASE ?? "").replace(/\/$/, "");

const cache = new Map<string, Promise<unknown>>();

export function getJson<T>(path: string): Promise<T> {
  const cached = cache.get(path);

  if (cached) {
    return cached as Promise<T>;
  }

  const pending = fetch(`${BASE}${path}`, { headers: { accept: "application/json" } }).then(
    (response) => {
      if (!response.ok) {
        throw new Error(`${path} returned HTTP ${response.status}`);
      }

      return response.json() as Promise<T>;
    },
  );

  pending.catch(() => cache.delete(path));
  cache.set(path, pending);

  return pending;
}

export const api = {
  text: (script: string, chapter: number) =>
    getJson<TextChapter>(`/text/${script}/chapters/${chapter}.json`),
  translation: (edition: string, chapter: number) =>
    getJson<TranslationChapter>(`/translations/${edition}/chapters/${chapter}.json`),
  transliteration: (edition: string, chapter: number) =>
    getJson<TransliterationChapter>(`/transliteration/${edition}/chapters/${chapter}.json`),
  reciters: () => getJson<ReciterIndex>("/audio/reciters.json"),
};
