"""The Indo-Pak script: DigitalKhatt's MIT text, reconstructed from a 15-line page.

The upstream artefact is a page layout -- 610 page groups of 15 lines with `۝` + digits as
ayah markers -- so the published verses are a derivation, not the source's own bytes.
These tests defend the three things that derivation could get wrong: where a verse ends,
what the text is left carrying, and the Al-Fatiha segmentation a consumer has to know
about before joining this script to the others.
"""

from __future__ import annotations

import unicodedata
from pathlib import Path
from typing import Any

import pytest

from quranjson import config, digitalkhatt, jsonio

CHAPTERS = 114
VERSES = 6236


def _verses(chapters: list[dict[str, Any]]) -> list[str]:
    return [verse["text"] for chapter in chapters for verse in chapter["verses"]]


def test_the_script_is_whole(cdn_tree: Path) -> None:
    chapters = jsonio.read_json(cdn_tree / "text" / config.DIGITALKHATT_SCRIPT / "quran.json")

    assert len(chapters) == CHAPTERS
    assert sum(len(chapter["verses"]) for chapter in chapters) == VERSES
    assert all(
        [verse["id"] for verse in chapter["verses"]] == list(range(1, len(chapter["verses"]) + 1))
        for chapter in chapters
    )


def test_verses_are_stripped_of_markers_and_rendering_controls(cdn_tree: Path) -> None:
    """The published text is verse text: no ayah cartouche, no bidi hack, NFC-composed.

    The source writes its ayah marker as `۝` + digits, one bidi override (1:6) instead of
    that marker, U+034F between a hamza and its seat, and hamza as a combining mark. Every
    one of those is the source's typesetting, and none of it is the Quran text. The
    mushaf's own *annotation* marks are kept, deliberately: U+08E2 marks a verse end the
    tradition holds disputed, and the waqf signs are the same kind of notation the Mushaf
    Standar Indonesia text publishes.
    """
    chapters = jsonio.read_json(cdn_tree / "text" / config.DIGITALKHATT_SCRIPT / "quran.json")
    rendering_controls = {"\u034f"} | {chr(cp) for cp in range(0x200B, 0x2010)}
    rendering_controls |= {chr(cp) for cp in range(0x202A, 0x202F)} | {"\ufeff"}
    annotated = 0

    for text in _verses(chapters):
        assert text, "an empty verse means a mis-split"
        assert "\u06dd" not in text, "the ayah marker leaked into the text"
        assert not rendering_controls & set(text)
        assert unicodedata.normalize("NFC", text) == text
        annotated += "\u08e2" in text

    assert annotated, "the disputed-verse-end annotation was stripped along with the controls"


def test_al_fatiha_keeps_the_indo_pak_segmentation(cdn_tree: Path) -> None:
    """The source does not number Al-Fatiha's basmala, and splits the last two verses.

    That is the Indo-Pak convention, and it is why this script's chapter 1 carries a
    `note` in the manifest: the verse *labels* differ from every other script here, while
    the count does not. Every other chapter matches the shared chapter metadata exactly.
    """
    chapters = jsonio.read_json(cdn_tree / "text" / config.DIGITALKHATT_SCRIPT / "quran.json")
    metadata = jsonio.read_json(cdn_tree / "chapters.json")
    fatiha = chapters[0]["verses"]

    assert len(fatiha) == 7
    assert fatiha[0]["text"].startswith("اَلْحَمْدُ لِلّٰهِ")
    assert fatiha[6]["text"].startswith("غَيْرِ الْمَغْضُوْبِ")
    assert "بِسْمِ" not in fatiha[0]["text"]

    for chapter, meta in zip(chapters, metadata, strict=True):
        assert len(chapter["verses"]) == meta["total_verses"], chapter["id"]


def test_the_rasm_is_indo_pak_not_hafs(cdn_tree: Path) -> None:
    """The fingerprint that separates the two families: no alef wasla, and a subscript alef.

    Uthmani rasm marks alef wasla (U+0671); this text marks none, and carries the Indo-Pak
    subscript alef (U+0656) that no Tanzil variant has. A file that fails this is a
    relabelled Hafs text, which is what most repos labelled `indopak` turn out to be.
    """
    chapters = jsonio.read_json(cdn_tree / "text" / config.DIGITALKHATT_SCRIPT / "quran.json")
    counts: dict[int, int] = {}

    for char in "".join(_verses(chapters)):
        counts[ord(char)] = counts.get(ord(char), 0) + 1

    assert counts.get(0x0671, 0) == 0
    assert counts.get(0x0656, 0) > 900
    assert counts.get(0x06E1, 0) == 0, "U+06E1 marks the other producer's Indopak encoding"
    # The manifest note tells consumers to pick an Extended-B font; that is only true while
    # this text uses U+089C. If upstream re-encodes, revise the note with this number.
    assert counts.get(0x089C, 0) > 2000


def test_the_parser_refuses_a_source_that_changed_shape() -> None:
    """Every guard fails loudly: a quiet mis-split would corrupt the text.

    Checked against synthetic bodies rather than the 1.5 MB upstream file, so the guards
    keep being exercised even if a fetch is unavailable.
    """

    def page(line: str) -> str:
        header = (
            "\u0633\u064f\u0648\u0631\u064e\u0629\u064f "
            "\u0627\u0644\u0641\u064e\u0627\u062a\u0650\u062d\u064e\u0629\u0650"
        )
        return f"  [\n    '{header}',\n    '{line}',\n  ],\n"

    with pytest.raises(ValueError, match="no longer named"):
        digitalkhatt.parse_text(b"const other = [];")

    # 114 headers is not enough on its own: the verse count must add up too.
    body = (
        "let quranText = [\n"
        + page("\u0627\u064e\u0644\u0652\u062d\u064e\u0645\u0652\u062f\u064f \u06dd\u0661") * 114
        + "]\nexport { quranText };\n"
    ).encode()

    with pytest.raises(ValueError, match="expected 6236 verses"):
        digitalkhatt.parse_text(body)

    # A marker followed by a letter means the trailing-marks rule no longer holds.
    broken_verse = "\u0627\u064e\u0644\u0652\u062d\u064e\u0645\u0652\u062f\u064f \u06dd\u0661\u063a"
    broken = (
        "let quranText = [\n"
        + page(broken_verse)
        + page("\u0627\u064e\u0644\u0652\u062d\u064e\u0645\u0652\u062f\u064f \u06dd\u0661") * 113
        + "]\nexport { quranText };\n"
    ).encode()

    with pytest.raises(ValueError, match="unexpected"):
        digitalkhatt.parse_text(broken)
