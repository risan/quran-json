import {
  ListEndIcon,
  PauseIcon,
  PlayIcon,
  Repeat1Icon,
  SkipBackIcon,
  SkipForwardIcon,
  XIcon,
} from "lucide-react";

import { Button } from "@/components/ui/button";
import type { Reciter } from "@/lib/types";
import { cn } from "@/lib/utils";
import type { Playing } from "@/reader/useAudio";

interface Props {
  reciter: Reciter | null;
  playing: Playing;
  isPlaying: boolean;
  error: string | null;
  continuous: boolean;
  repeat: boolean;
  onToggle: () => void;
  onStep: (direction: 1 | -1) => void;
  onContinuous: () => void;
  onRepeat: () => void;
  onClose: () => void;
  onShow: () => void;
}

export function AudioBar({
  reciter,
  playing,
  isPlaying,
  error,
  continuous,
  repeat,
  onToggle,
  onStep,
  onContinuous,
  onRepeat,
  onClose,
  onShow,
}: Props) {
  const where =
    playing.verse === null ? `Surah ${playing.chapter}` : `${playing.chapter}:${playing.verse}`;

  return (
    <section
      aria-label="Audio player"
      className="bg-background sticky bottom-0 z-30 flex min-h-12 items-center gap-1 border-t px-3"
    >
      <Button variant="ghost" size="icon-sm" aria-label="Previous" onClick={() => onStep(-1)}>
        <SkipBackIcon aria-hidden="true" />
      </Button>
      <Button
        variant="ghost"
        size="icon-sm"
        aria-label={isPlaying ? "Pause" : "Play"}
        onClick={onToggle}
      >
        {isPlaying ? <PauseIcon aria-hidden="true" /> : <PlayIcon aria-hidden="true" />}
      </Button>
      <Button variant="ghost" size="icon-sm" aria-label="Next" onClick={() => onStep(1)}>
        <SkipForwardIcon aria-hidden="true" />
      </Button>
      <button
        type="button"
        onClick={onShow}
        className="hover:bg-muted ml-2 min-w-0 flex-1 rounded-md px-2 py-1 text-left text-[13px]"
      >
        <span className="block truncate font-medium tabular-nums">{where}</span>
        <span
          className={cn(
            "block truncate text-xs",
            error ? "text-destructive" : "text-muted-foreground",
          )}
          role={error ? "alert" : undefined}
        >
          {error ?? reciter?.name ?? "No reciter"}
        </span>
      </button>
      <Button
        variant="ghost"
        size="icon-sm"
        aria-label="Continue to the next verse"
        aria-pressed={continuous}
        onClick={onContinuous}
        className={cn(continuous && "text-brand")}
      >
        <ListEndIcon aria-hidden="true" />
      </Button>
      <Button
        variant="ghost"
        size="icon-sm"
        aria-label="Repeat this verse"
        aria-pressed={repeat}
        onClick={onRepeat}
        className={cn(repeat && "text-brand")}
      >
        <Repeat1Icon aria-hidden="true" />
      </Button>
      <Button variant="ghost" size="icon-sm" aria-label="Close player" onClick={onClose}>
        <XIcon aria-hidden="true" />
      </Button>
    </section>
  );
}
