import {
  ChevronLeftIcon,
  ChevronRightIcon,
  ListIcon,
  PlayIcon,
  SearchIcon,
  SlidersHorizontalIcon,
} from "lucide-react";

import { Button, buttonVariants } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { Chapter, ReaderBoot, Script } from "@/lib/types";
import { editionKey, readerHash } from "@/reader/core";
import { Combobox, type ComboboxItem } from "./Combobox";

interface Props {
  boot: ReaderBoot;
  chapter: Chapter;
  nativeVerseCount: number | null;
  script: Script;
  primaryTranslation: string | null;
  onScript: (id: string) => void;
  onPrimaryTranslation: (key: string | null) => void;
  onOpenSurahs: () => void;
  onOpenSearch: () => void;
  onOpenSettings: () => void;
  onPlay: () => void;
}

const isApple = typeof navigator !== "undefined" && /Mac|iPhone|iPad/.test(navigator.platform);

export function Toolbar({
  boot,
  chapter,
  nativeVerseCount,
  script,
  primaryTranslation,
  onScript,
  onPrimaryTranslation,
  onOpenSurahs,
  onOpenSearch,
  onOpenSettings,
  onPlay,
}: Props) {
  const previous = boot.chapters.find((entry) => entry.id === chapter.id - 1);
  const next = boot.chapters.find((entry) => entry.id === chapter.id + 1);
  const primary = boot.translations.find((edition) => editionKey(edition) === primaryTranslation);
  const translationItems: ComboboxItem[] = [
    { value: "", label: "No translation" },
    ...[...boot.translations]
      .sort((a, b) => `${a.language}${a.author}`.localeCompare(`${b.language}${b.author}`))
      .map((edition) => ({
        value: editionKey(edition),
        label: edition.author,
        group: (edition.language ?? "").replace(/^./, (letter) => letter.toUpperCase()),
        keywords: `${edition.language} ${edition.code} ${editionKey(edition)}`,
      })),
  ];

  return (
    <div className="bg-background sticky top-12 z-30 flex h-10 items-center gap-1 border-b px-3">
      <Button
        variant="ghost"
        size="icon-sm"
        className="lg:hidden"
        aria-label="Open the surah list"
        onClick={onOpenSurahs}
      >
        <ListIcon aria-hidden="true" />
      </Button>
      {previous ? (
        <a
          href={readerHash(previous.id)}
          aria-label="Previous surah"
          className={buttonVariants({ variant: "ghost", size: "icon-sm" })}
        >
          <ChevronLeftIcon aria-hidden="true" />
        </a>
      ) : (
        <Button variant="ghost" size="icon-sm" aria-label="Previous surah" disabled>
          <ChevronLeftIcon aria-hidden="true" />
        </Button>
      )}
      <h1 className="flex min-w-0 items-baseline gap-2 text-sm font-semibold">
        <span className="truncate">
          {chapter.id}. {chapter.transliteration}
        </span>
        <span lang="ar" dir="rtl" className="font-arabic text-base font-normal">
          {chapter.name}
        </span>
        <span className="text-muted-foreground hidden text-[13px] font-normal md:inline">
          {nativeVerseCount ?? chapter.total_verses} verses
        </span>
      </h1>
      {next ? (
        <a
          href={readerHash(next.id)}
          aria-label="Next surah"
          className={buttonVariants({ variant: "ghost", size: "icon-sm" })}
        >
          <ChevronRightIcon aria-hidden="true" />
        </a>
      ) : (
        <Button variant="ghost" size="icon-sm" aria-label="Next surah" disabled>
          <ChevronRightIcon aria-hidden="true" />
        </Button>
      )}

      <div className="ml-auto flex items-center gap-1.5">
        <div className="hidden items-center gap-1.5 sm:flex">
          <Select
            value={script.id}
            onValueChange={(value) => value && onScript(value)}
            items={boot.scripts.map((entry) => ({ value: entry.id, label: entry.name }))}
          >
            <SelectTrigger size="sm" aria-label="Script" className="max-w-44">
              <SelectValue />
            </SelectTrigger>
            <SelectContent alignItemWithTrigger={false}>
              {boot.scripts.map((entry) => (
                <SelectItem key={entry.id} value={entry.id}>
                  {entry.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Combobox
            items={translationItems}
            selected={[primaryTranslation ?? ""]}
            onToggle={(value) => onPrimaryTranslation(value || null)}
            label="Translation"
            searchPlaceholder="Search language or translator"
            className="h-7 w-44 px-2.5 text-sm"
          >
            {primary ? primary.author.replace(/^.*? Translation - /, "") : "No translation"}
          </Combobox>
        </div>
        <Button variant="ghost" size="icon-sm" aria-label="Play this surah" onClick={onPlay}>
          <PlayIcon aria-hidden="true" />
        </Button>
        <Button
          variant="outline"
          size="sm"
          aria-label="Search surahs and verses"
          onClick={onOpenSearch}
          className="text-muted-foreground font-normal"
        >
          <SearchIcon aria-hidden="true" />
          <kbd className="hidden font-sans text-xs sm:inline">{isApple ? "⌘K" : "Ctrl K"}</kbd>
        </Button>
        <Button variant="ghost" size="icon-sm" aria-label="Settings" onClick={onOpenSettings}>
          <SlidersHorizontalIcon aria-hidden="true" />
        </Button>
      </div>
    </div>
  );
}
