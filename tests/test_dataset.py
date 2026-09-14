"""Structural and textual invariants of the dataset.

These defend the properties a consumer actually relies on: chapter and verse counts,
the global 1..6236 numbering, how the basmala is encoded, and translation coverage.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from quranjson import config
from quranjson.build import Sources
from quranjson.jsonio import read_json

BASMALA = "\u0628\u0650\u0633\u06e1\u0645\u0650 \u0671\u0644\u0644\u0651\u064e\u0647\u0650"

CHAPTERS = 114
VERSES = 6236


@pytest.fixture(scope="module")
def sources() -> Sources:
    return Sources()


def test_chapter_table_is_complete(sources: Sources) -> None:
    chapters = sources.chapters["en"]

    assert len(chapters) == CHAPTERS
    assert [chapter["id"] for chapter in chapters] == list(range(1, CHAPTERS + 1))
    assert sum(chapter["total_verses"] for chapter in chapters) == VERSES


def test_declared_verse_counts_match_the_text(sources: Sources) -> None:
    for chapter in sources.chapters["en"]:
        verses = sources.verses(chapter["id"])

        assert len(verses) == chapter["total_verses"], chapter["id"]
        assert [verse["verse"] for verse in verses] == list(range(1, len(verses) + 1))


def test_uthmani_text_is_present_for_every_verse(sources: Sources) -> None:
    for chapter in sources.chapters["en"]:
        for verse in sources.verses(chapter["id"]):
            assert verse["text"].strip(), f"{chapter['id']}:{verse['verse']}"


def test_basmala_is_only_inside_the_first_verse_of_al_fatiha(sources: Sources) -> None:
    """Surahs 2-114 must not carry the basmala inside ayah 1; 1:1 *is* the basmala."""
    prefixed = [
        chapter["id"]
        for chapter in sources.chapters["en"]
        if sources.verses(chapter["id"])[0]["text"].startswith(BASMALA)
    ]

    assert prefixed == [1]

    embedded = [
        chapter["id"]
        for chapter in sources.chapters["en"]
        if chapter["id"] != 1 and BASMALA in sources.verses(chapter["id"])[0]["text"]
    ]

    assert embedded == [], "basmala must not be prefixed to the first ayah of other surahs"


def test_editions_align_with_the_text_verse_for_verse(sources: Sources) -> None:
    for edition in config.EDITIONS:
        chapters = sources.editions[edition.lang]

        assert len(chapters) == CHAPTERS, edition.lang

        total = 0
        for chapter in sources.chapters["en"]:
            entries = chapters[str(chapter["id"])]

            assert len(entries) == chapter["total_verses"], f"{edition.lang} {chapter['id']}"

            for index, (entry, verse) in enumerate(
                zip(entries, sources.verses(chapter["id"]), strict=True), 1
            ):
                assert entry["chapter"] == chapter["id"]
                assert entry["verse"] == index == verse["verse"]
                assert entry["text"].strip(), f"{edition.lang} {chapter['id']}:{index}"

            total += len(entries)

        assert total == VERSES, edition.lang


def test_global_verse_files_match_the_source_text(sources: Sources) -> None:
    """The 6,236 verse files are the global index; each must mirror its source verse."""
    expected = [
        (chapter["id"], verse["verse"], verse["text"])
        for chapter in sources.chapters["en"]
        for verse in sources.verses(chapter["id"])
    ]

    assert len(expected) == VERSES

    for index, (chapter_id, number, text) in enumerate(expected, start=1):
        entry = read_json(config.DIST / "verses" / f"{index}.json")

        assert entry["id"] == index
        assert entry["number"] == number
        assert entry["text"] == text
        assert entry["chapter"]["id"] == chapter_id


def test_verse_files_carry_only_publishable_translations(legacy_tree: Path, cdn_tree: Path) -> None:
    legacy = read_json(legacy_tree / "verses" / "1.json")
    published = read_json(cdn_tree / "verses" / "1.json")

    # Upstream `qurans.slice(2)` dropped Bengali from the frozen tree. The published tree
    # carries one QuranEnc translation per major language instead (see test_licensed.py).
    assert "bn" not in legacy["translations"]
    assert "bn" not in published["translations"]
    assert "en" not in published["translations"]
    assert len(published["translations"]) == 11
    assert published["chapter"]["translations"].keys() == published["translations"].keys()


def test_gated_tree_omits_restricted_editions_entirely(cdn_tree: Path) -> None:
    """A restricted edition must leave no trace: no file, and no transliteration key."""
    assert not (cdn_tree / "quran_en.json").exists()
    assert not (cdn_tree / "quran_bn.json").exists()
    assert not (cdn_tree / "quran_transliteration.json").exists()
    assert not (cdn_tree / "chapters" / "en").exists()

    assert "transliteration" not in read_json(cdn_tree / "verses" / "1.json")
    assert "transliteration" not in read_json(cdn_tree / "chapters" / "1.json")["verses"][0]


def test_gated_tree_still_publishes_the_full_quran(cdn_tree: Path) -> None:
    """Withholding translations must not reduce the text: 114 chapters, 6,236 verses."""
    chapters = read_json(cdn_tree / "quran.json")

    assert len(chapters) == CHAPTERS
    assert sum(chapter["total_verses"] for chapter in chapters) == VERSES
    assert (cdn_tree / "verses" / f"{VERSES}.json").exists()
    assert "translation" not in chapters[0]


def test_chapter_index_links_point_at_the_configured_base(cdn_tree: Path) -> None:
    index = read_json(cdn_tree / "chapters" / "index.json")
    translated = read_json(cdn_tree / "chapters" / "english_rwwad" / "index.json")

    assert len(index) == CHAPTERS
    assert index[0]["link"] == "https://quran.example/4.0.0/chapters/1.json"
    assert translated[0]["link"] == "https://quran.example/4.0.0/chapters/english_rwwad/1.json"
    assert "verses" not in index[0]


def test_chapter_files_embed_transliteration_but_quran_json_does_not(legacy_tree: Path) -> None:
    chapter = read_json(legacy_tree / "chapters" / "1.json")
    whole = read_json(legacy_tree / "quran.json")

    assert "transliteration" in chapter["verses"][0]
    assert "transliteration" not in whole[0]["verses"][0]
    assert "translation" not in whole[0]


def test_no_chapter_directory_exists_for_transliteration(legacy_tree: Path) -> None:
    """`transliteration` is language-shaped but has no chapter directory upstream."""
    assert (legacy_tree / "quran_transliteration.json").exists()
    assert not (legacy_tree / "chapters" / config.TRANSLITERATION).exists()
