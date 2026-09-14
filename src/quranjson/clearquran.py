"""Talal Itani's ClearQuran as a first-party English translation source.

We fetch from the translator's own site rather than from a packager, because the grant is
his: CC BY-ND 4.0, commercial use included, no permission required, unmodified with credit
("Translation by Talal Itani, ClearQuran.com").

His distribution is one plain-text file per verse inside a zip, named `SSS-AAA.txt`, so the
alignment is already exact and no PDF or docx extraction is needed. Two wordings are
published: one uses "Allah", the other "God".

Note the numbering: 112 chapters include an `SSS-000.txt` holding the basmala as a
standalone pseudo-verse (every chapter except Al-Fatiha, where it is ayah 1, and At-Tawbah,
which has none). Those are skipped -- the Tanzil text we publish already carries the
basmala inside ayah 1, and keeping them would break the one-verse-per-ayah invariant.
"""

from __future__ import annotations

import io
import re
import zipfile
from typing import Any

from . import config

__all__ = ["EXPECTED_CHAPTERS", "EXPECTED_VERSES", "VARIANTS", "parse_verse_files", "variant_url"]

EXPECTED_CHAPTERS = 114
EXPECTED_VERSES = 6236

#: Edition key -> archive filename on clearquran.com.
VARIANTS: dict[str, str] = {
    "english_itani": "quran-verse-by-verse-text.zip",
    "english_itani_allah": "quran-in-english-clearquran-verse-by-verse-txt-edition-allah.zip",
}

_VERSE_FILE = re.compile(r"(\d{3})-(\d{3})\.txt\Z")


def variant_url(key: str) -> str:
    """Download URL for one edition of the translation."""
    return config.clearquran_url(VARIANTS[key])


def parse_verse_files(raw: bytes) -> dict[str, list[dict[str, Any]]]:
    """Turn the per-verse zip into `{chapter: [{chapter, verse, text}]}`."""
    verses: dict[int, list[dict[str, Any]]] = {}

    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        for name in archive.namelist():
            match = _VERSE_FILE.search(name)

            if match is None:
                continue

            chapter, verse = int(match.group(1)), int(match.group(2))

            if verse == 0:
                continue  # standalone basmala; see the module docstring

            # Verse files are single lines; collapse breaks so each stays one JSON string.
            text = " ".join(archive.read(name).decode("utf-8").split())

            if not text:
                raise ValueError(f"empty verse in archive: {name}")

            verses.setdefault(chapter, []).append(
                {"chapter": chapter, "verse": verse, "text": text}
            )

    ordered = {
        str(chapter): sorted(items, key=lambda item: item["verse"])
        for chapter, items in verses.items()
    }

    # Fail loudly rather than committing a partial translation.
    if len(ordered) != EXPECTED_CHAPTERS:
        raise ValueError(f"expected {EXPECTED_CHAPTERS} chapters, found {len(ordered)}")

    total = sum(len(items) for items in ordered.values())
    if total != EXPECTED_VERSES:
        raise ValueError(f"expected {EXPECTED_VERSES} verses, found {total}")

    for key, items in ordered.items():
        numbers = [item["verse"] for item in items]
        if numbers != list(range(1, len(numbers) + 1)):
            raise ValueError(f"chapter {key} has non-contiguous verses")

    return ordered
