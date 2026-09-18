"""DigitalKhatt's Indo-Pak text -- the only Indo-Pak rasm found under a redistribution grant.

Every other Indo-Pak text in circulation is either unlicensed or expressly restricted. The
QuranWBW/Quran.com Indopak text (QUL resources 55/59) carries "Sadaqa-e-Jaria purposes
only ... DO NOT SELL, MANIPULATE, DISTRIBUTE WITHOUT CREDITS", and Quran Foundation's
developer terms forbid redistributing QF Content; KFGQPC's Indopak/Nastaleeq reach us
only through mirrors whose own licence covers the packaging. Verified 2026-09-18 against
each rights holder's own page -- see `quranjson.review`.

This file is different in kind. It is DigitalKhatt's own typesetting, published in
`DigitalKhatt/digitalkhatt-js` under the repository's MIT licence
(https://github.com/DigitalKhatt/digitalkhatt-js/blob/main/LICENSE, "Permission is hereby
granted, free of charge ... without restriction"). The project is sponsored by Tarteel,
but the licence is the repository's own, and the text is not a copy of anyone else's
Indopak data: measured against the QuranWBW text and the KFGQPC text, it shares **0 of
6,236** verses with either.

**The source is a printed page, not a verse array.** The file is `quran_text_indopak_15`:
610 page groups of 15 lines (the first two are 8, the classic Indo-Pak opening spread),
with surah headers as their own lines and `۝` + Arabic-Indic digits as the ayah-end
markers. So this module reconstructs verses from lines, and three decisions in that
reconstruction are worth stating:

* **Lines join with a single space.** Verified: no line break falls inside a word. Aligning
  all 6,236 reconstructed verses against the Kemenag snapshot leaves 156 verses whose word
  count differs, and every one of them is an orthographic difference between the two
  traditions ('لَّا شِيَةَ' vs 'لَّاشِيَةَ', MSI joining the proclitic) rather than a broken
  token; no fragment is out of vocabulary once marks are stripped.
* **The marker's trailing marks belong to the verse it closes.** `۝١ۙ` means "ayah 1 ends
  here", printed with its waqf sign after the number. Attaching that run to the closed
  verse reproduces the Kemenag text's own mark placement on the same verses, which is the
  independent check that this reading of the source is right.
* **Rendering controls are stripped and the text is NFC-normalised.** The file carries
  U+034F COMBINING GRAPHEME JOINER (which blocks composition), one U+202E RIGHT-TO-LEFT
  OVERRIDE used as a bidi hack on 1:6, and hamza written as a combining mark over its seat
  rather than precomposed. Removing the controls and composing to NFC is canonical, not
  editorial: U+0648 U+0654 and U+0624 are the same character.

Three properties of the published text a consumer should know:

* **Al-Fatiha is segmented the Indo-Pak way.** The basmala is unnumbered (the source
  prints it with a bare `۝`), so verse 1 is 'اَلْحَمْدُ لِلّٰهِ رَبِّ الْعٰلَمِيْنَ' and the
  last two verses are the source's own, where the Hafs scripts make the basmala verse 1 and
  hold the final two as one. All 114 chapters have the canonical count; only chapter 1's
  verse *labels* differ from the other scripts.
* **No basmala is embedded in any verse.** The source prints it as an unnumbered line, so
  it is chapter furniture here, as upstream. Tanzil's texts embed it at the head of verse 1.
* **It uses Arabic Extended-B marks** (U+089C ARABIC MADDA WAAJIB, 2,098 of them) and needs
  a font with Extended-B coverage. They are the source's own encoding of the madda and are
  published verbatim rather than rewritten to another mark.
"""

from __future__ import annotations

import ast
import re
import unicodedata
from typing import Any, Final

__all__ = ["RAW_URL", "SNAPSHOT_URL", "VERSE_COUNT", "parse_text"]

#: The text, as published in DigitalKhatt's app source. `HEAD` rather than a pinned SHA:
#: the snapshot is what the build reads, and `quran-json fetch --force` records drift.
RAW_URL: Final = (
    "https://raw.githubusercontent.com/DigitalKhatt/digitalkhatt-js/HEAD/"
    "apps/site-angular/src/app/services/quran_text_indopak_15.ts"
)

#: Documents the request pattern a snapshot was taken with, for provenance.
SNAPSHOT_URL: Final = RAW_URL

LICENSE_URL: Final = "https://raw.githubusercontent.com/DigitalKhatt/digitalkhatt-js/HEAD/LICENSE"

CHAPTER_COUNT: Final = 114
VERSE_COUNT: Final = 6236

#: A line that names the surah rather than carrying text.
HEADER: Final = "سُورَةُ"

#: `۝` + Arabic-Indic digits closes a verse; a bare `۝` marks the unnumbered basmala. The
#: one U+202E in the file is the same marker written with a bidi override instead of `۝`
#: (surah 1, ayah 6) -- a quirk of the source, not a different convention.
DELIMITER: Final = re.compile(
    "(\u06dd|\u202e)([\u0660-\u0669]*)([\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u08d3-\u08ff]*)"
)

#: Rendering controls: the grapheme joiner, zero-width and bidi marks, and the BOM.
CONTROLS: Final = re.compile("[\u034f\u200b-\u200f\u202a-\u202e\ufeff]")

DIGITS: Final = {chr(0x660 + digit): str(digit) for digit in range(10)}


def _number(digits: str) -> int:
    """The ayah number a marker carries, from its Arabic-Indic digits."""
    return int("".join(DIGITS[digit] for digit in digits))


def _clean(text: str) -> str:
    """Strip rendering controls, collapse whitespace, and compose to NFC."""
    return unicodedata.normalize("NFC", re.sub(r"\s+", " ", CONTROLS.sub("", text)).strip())


def _pages(raw: bytes) -> list[list[str]]:
    """The TypeScript array literal, decoded: one list of lines per page group."""
    source = raw.decode("utf-8")
    start = source.find("quranText = ")

    if start < 0:
        raise ValueError("digitalkhatt: the text array is no longer named `quranText`")

    literal = source[start + len("quranText = ") : source.rfind("]") + 1]

    try:
        pages = ast.literal_eval(literal)
    except (SyntaxError, ValueError) as error:  # pragma: no cover - upstream shape change
        raise ValueError(
            f"digitalkhatt: the text array no longer parses as a literal: {error}"
        ) from error

    if not isinstance(pages, list) or not all(isinstance(page, list) for page in pages):
        raise ValueError("digitalkhatt: expected a list of page groups")

    return pages


def _surahs(pages: list[list[str]]) -> list[list[str]]:
    """Group the page lines by surah, dropping the header lines."""
    surahs: list[list[str]] = []

    for line in (line for page in pages for line in page):
        if line.startswith(HEADER):
            surahs.append([])
        elif surahs:
            surahs[-1].append(line)
        else:
            raise ValueError(f"digitalkhatt: text before the first surah header: {line[:40]!r}")

    if len(surahs) != CHAPTER_COUNT:
        raise ValueError(f"digitalkhatt: expected {CHAPTER_COUNT} surahs, got {len(surahs)}")

    return surahs


def parse_text(raw: bytes) -> dict[str, list[dict[str, Any]]]:
    """Parse the 15-line Indo-Pak text into `{chapter: [{chapter, verse, text}]}`.

    Raises:
        ValueError: the upstream file no longer has the shape this parser assumes. The
            checks are deliberately loud -- a silent mis-split would corrupt the text.
    """
    chapters: dict[str, list[dict[str, Any]]] = {}

    for index, lines in enumerate(_surahs(_pages(raw)), start=1):
        page = " ".join(lines)
        verses: dict[int, str] = {}
        position = 0

        for marker in DELIMITER.finditer(page):
            body = page[position : marker.start()]
            digits = marker.group(2)

            if marker.group(1) == "\u202e" and not digits:  # pragma: no cover - shape change
                raise ValueError("digitalkhatt: a bidi override with no ayah number")

            if digits:
                verses[_number(digits)] = _clean(body) + _clean(marker.group(3))

            # Everything up to the next space after the marker's trailing marks belongs to
            # the marker. Anything else means the reading below is wrong.
            after = page[marker.end() : marker.end() + 1]
            if after and not after.isspace():  # pragma: no cover - shape change
                raise ValueError(
                    f"digitalkhatt: unexpected {after!r} after the marker at "
                    f"{index}:{marker.group(2) or 'basmala'}"
                )

            position = marker.end()

        if sorted(verses) != list(range(1, len(verses) + 1)):
            raise ValueError(f"digitalkhatt: chapter {index} is not numbered 1..n")

        chapters[str(index)] = [
            {"chapter": index, "verse": number, "text": verses[number]} for number in sorted(verses)
        ]

    total = sum(len(verses) for verses in chapters.values())
    if total != VERSE_COUNT:
        raise ValueError(f"digitalkhatt: expected {VERSE_COUNT} verses, got {total}")

    return chapters
