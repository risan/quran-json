/** Where playback goes next. Pure, so the edges (end of a chapter, first verse) are tested. */

export interface Position {
  chapter: number;
  verse: number;
}

export function neighbour(
  position: Position,
  direction: 1 | -1,
  verseCounts: (chapter: number) => number,
  chapterCount: number,
): Position | null {
  const verse = position.verse + direction;

  if (verse >= 1 && verse <= verseCounts(position.chapter)) {
    return { chapter: position.chapter, verse };
  }

  const chapter = position.chapter + direction;

  if (chapter < 1 || chapter > chapterCount) {
    return null;
  }

  return { chapter, verse: direction === 1 ? 1 : verseCounts(chapter) };
}

/** The recording a player holds: one script (so one reading) and one reciter. */
export interface RecordingIdentity {
  scriptId: string;
  reciter: { id: string; url: string } | null;
}

export function recordingKey({ scriptId, reciter }: RecordingIdentity): string {
  return [scriptId, reciter?.id ?? "", reciter?.url ?? ""].join("|");
}

/**
 * Whether what is loaded no longer matches what is selected. The loaded audio belongs to the
 * old recording, so the player stops instead of labelling it with the new reciter.
 */
export function recordingChanged(
  loaded: RecordingIdentity | null,
  selected: RecordingIdentity,
): boolean {
  return loaded !== null && recordingKey(loaded) !== recordingKey(selected);
}
