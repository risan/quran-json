import { useEffect, useRef, useState } from "react";

import type { Chapter } from "@/lib/types";
import { cn } from "@/lib/utils";
import { readerHash } from "@/reader/core";
import { filterChapters } from "@/reader/search";

interface Props {
  chapters: Chapter[];
  current: number;
  /** Called after a chapter is chosen, e.g. to close the sheet that holds the list. */
  onSelect?: () => void;
  className?: string;
}

export function SurahNav({ chapters, current, onSelect, className }: Props) {
  const [query, setQuery] = useState("");
  const activeRef = useRef<HTMLAnchorElement>(null);
  const shown = filterChapters(chapters, query);

  useEffect(() => {
    activeRef.current?.scrollIntoView({ block: "nearest" });
  }, [current]);

  return (
    <nav aria-label="Surahs" className={cn("flex min-h-0 flex-col", className)}>
      <div className="p-2">
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Filter surahs"
          aria-label="Filter surahs"
          className="border-input bg-background placeholder:text-muted-foreground focus-visible:ring-ring h-8 w-full rounded-md border px-2.5 text-sm outline-none focus-visible:ring-2"
        />
      </div>
      <ul className="min-h-0 flex-1 overflow-y-auto px-2 pb-2">
        {shown.map((chapter) => {
          const isCurrent = chapter.id === current;

          return (
            <li key={chapter.id}>
              <a
                ref={isCurrent ? activeRef : undefined}
                href={readerHash(chapter.id)}
                aria-current={isCurrent ? "page" : undefined}
                title={`${chapter.translation}, ${chapter.total_verses} verses`}
                onClick={onSelect}
                className={cn(
                  "text-foreground hover:bg-muted flex h-8 items-center gap-2 rounded-md px-2 text-[13px] no-underline",
                  isCurrent && "bg-muted text-brand font-medium",
                )}
              >
                <span className="text-muted-foreground w-6 shrink-0 text-right text-xs tabular-nums">
                  {chapter.id}
                </span>
                <span className="min-w-0 flex-1 truncate">{chapter.transliteration}</span>
                <span lang="ar" dir="rtl" className="text-muted-foreground font-arabic text-sm">
                  {chapter.name}
                </span>
              </a>
            </li>
          );
        })}
        {shown.length === 0 ? (
          <li className="text-muted-foreground px-2 py-3 text-[13px]">No surah matches.</li>
        ) : null}
      </ul>
    </nav>
  );
}
