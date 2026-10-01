import { memo } from "react";
import { EllipsisIcon, PlayIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { Edition } from "@/lib/types";
import { cn } from "@/lib/utils";
import { editionKey, type MergedVerse } from "@/reader/core";

export type VerseAction = "copy-arabic" | "copy-translation" | "copy-link" | "play-from-here";

interface Props {
  chapterId: number;
  verse: MergedVerse;
  translations: Edition[];
  romanisation: Edition | null;
  showArabic: boolean;
  showTransliteration: boolean;
  showTranslations: boolean;
  /** The verse the audio is on. */
  playing: boolean;
  /** The verse a link points at. */
  linked: boolean;
  onAction: (action: VerseAction, verse: MergedVerse) => void;
}

function editionLabel(edition: Edition): string {
  return edition.author.replace(/^.*? Translation - /, "");
}

export const VerseRow = memo(function VerseRow({
  chapterId,
  verse,
  translations,
  romanisation,
  showArabic,
  showTransliteration,
  showTranslations,
  playing,
  linked,
  onAction,
}: Props) {
  const key = `${chapterId}:${verse.id}`;
  const hafs = Array.isArray(verse.number_in_hafs)
    ? verse.number_in_hafs
    : verse.number_in_hafs
      ? [verse.number_in_hafs]
      : [];
  const hasTranslation = translations.some((edition) => verse.translations?.[editionKey(edition)]);

  return (
    <li
      id={`v${verse.id}`}
      data-verse={verse.id}
      aria-current={playing ? "true" : undefined}
      className={cn(
        "scroll-mt-28 border-b border-l-2 border-l-transparent py-3 pl-3 sm:grid sm:grid-cols-[4.5rem_minmax(0,1fr)] sm:gap-3",
        (playing || linked) && "border-l-brand bg-muted/40",
      )}
    >
      <div className="mb-1 flex items-center gap-1 sm:mb-0 sm:flex-col sm:items-start sm:gap-0.5">
        <a
          href={`#/${chapterId}:${verse.id}`}
          className="text-muted-foreground text-xs tabular-nums no-underline hover:underline"
          aria-label={`Verse ${key}`}
        >
          {key}
        </a>
        {hafs.length > 0 ? (
          <span
            className="text-muted-foreground hidden text-[11px] sm:block"
            title="The Hafs verse number this verse covers"
          >
            Hafs {hafs.length > 1 ? `${hafs[0]}–${hafs[hafs.length - 1]}` : hafs[0]}
          </span>
        ) : null}
        <div className="flex items-center sm:-ml-1.5 sm:mt-1">
          <Button
            variant="ghost"
            size="icon-sm"
            aria-label={`Play ${key}`}
            aria-pressed={playing}
            onClick={() => onAction("play-from-here", verse)}
            className={cn(playing && "text-brand")}
          >
            <PlayIcon className="size-3.5" aria-hidden="true" />
          </Button>
          <DropdownMenu>
            <DropdownMenuTrigger
              render={
                <Button variant="ghost" size="icon-sm" aria-label={`More actions for ${key}`} />
              }
            >
              <EllipsisIcon className="size-3.5" aria-hidden="true" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="w-44">
              <DropdownMenuItem onClick={() => onAction("copy-arabic", verse)}>
                Copy Arabic
              </DropdownMenuItem>
              <DropdownMenuItem
                disabled={!hasTranslation}
                onClick={() => onAction("copy-translation", verse)}
              >
                Copy translation
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onAction("copy-link", verse)}>
                Copy link
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onAction("play-from-here", verse)}>
                Play from here
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
      <div className="min-w-0 space-y-2">
        {showArabic ? (
          <p lang="ar" dir="rtl" className="arabic">
            {verse.text}
          </p>
        ) : null}
        {showTransliteration && romanisation && verse.transliteration ? (
          <p lang={`${romanisation.code ?? "und"}-Latn`} className="text-muted-foreground text-sm">
            {verse.transliteration}
          </p>
        ) : null}
        {showTranslations
          ? translations.map((edition) => {
              const editionId = editionKey(edition);
              const text = verse.translations?.[editionId];
              const note = verse.footnotes?.[editionId];

              if (!text) {
                return null;
              }

              return (
                <div key={editionId}>
                  <p
                    lang={edition.code ?? "und"}
                    dir={edition.direction ?? "ltr"}
                    className="text-base leading-7"
                  >
                    {text}
                  </p>
                  <p className="text-muted-foreground mt-0.5 text-xs">{editionLabel(edition)}</p>
                  {note ? (
                    <details className="text-muted-foreground mt-1 text-[13px]">
                      <summary className="cursor-pointer">Notes</summary>
                      <p className="mt-1 whitespace-pre-line">{note}</p>
                    </details>
                  ) : null}
                </div>
              );
            })
          : null}
      </div>
    </li>
  );
});
