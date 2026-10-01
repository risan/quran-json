import { useState } from "react";
import { CornerDownLeftIcon } from "lucide-react";

import {
  Command,
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/components/ui/command";
import type { Chapter, Script } from "@/lib/types";
import { filterChapters, parseVerseTarget } from "@/reader/search";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  chapters: Chapter[];
  script: Script;
  onGo: (chapter: number, verse?: number) => void;
}

export function CommandPalette({ open, onOpenChange, chapters, script, onGo }: Props) {
  const [query, setQuery] = useState("");
  const verse = parseVerseTarget(query, chapters, script);
  const matches = filterChapters(chapters, query);

  function go(chapter: number, target?: number) {
    onOpenChange(false);
    setQuery("");
    onGo(chapter, target);
  }

  return (
    <CommandDialog
      open={open}
      onOpenChange={(next) => {
        onOpenChange(next);

        if (!next) {
          setQuery("");
        }
      }}
      title="Go to a surah or verse"
      description="Search by number, name or meaning, or type a verse such as 2:255."
    >
      <Command shouldFilter={false} loop>
        <CommandInput
          value={query}
          onValueChange={setQuery}
          placeholder="Surah number, name, meaning, or 2:255"
        />
        <CommandList className="max-h-80">
          <CommandEmpty>No surah matches.</CommandEmpty>
          {verse ? (
            <CommandGroup heading="Verse">
              <CommandItem
                value={`verse ${verse.chapter}:${verse.verse}`}
                onSelect={() => go(verse.chapter, verse.verse)}
              >
                <span>
                  Go to {verse.chapter}:{verse.verse}
                </span>
                <CornerDownLeftIcon className="text-muted-foreground ml-auto" />
              </CommandItem>
            </CommandGroup>
          ) : null}
          {matches.length > 0 ? (
            <CommandGroup heading="Surahs">
              {matches.map((chapter) => (
                <CommandItem
                  key={chapter.id}
                  value={`surah ${chapter.id}`}
                  onSelect={() => go(chapter.id)}
                >
                  <span className="text-muted-foreground w-7 shrink-0 text-right text-xs tabular-nums">
                    {chapter.id}
                  </span>
                  <span className="min-w-0 flex-1 truncate">
                    {chapter.transliteration}
                    <span className="text-muted-foreground"> · {chapter.translation}</span>
                  </span>
                  <span lang="ar" dir="rtl" className="font-arabic text-base">
                    {chapter.name}
                  </span>
                </CommandItem>
              ))}
            </CommandGroup>
          ) : null}
        </CommandList>
      </Command>
    </CommandDialog>
  );
}
