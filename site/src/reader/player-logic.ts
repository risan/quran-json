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
