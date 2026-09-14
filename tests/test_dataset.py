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


def test_translation_files_carry_no_arabic(cdn_tree: Path) -> None:
    """Translations ship without the text, which is identical for every edition.

    Embedding it duplicated one 1.7 MB corpus 83 times: 105 MB, a fifth of the old
    deployment. The Arabic is published once under /text/ instead.
    """
    chapter = read_json(cdn_tree / "translations" / "en-pickthall" / "chapters" / "1.json")

    assert set(chapter["verses"][0]) == {"id", "translation"}
    assert chapter["verses"][0]["translation"] == (
        "In the name of Allah, the Beneficent, the Merciful"
    )


def test_every_script_is_published_complete(cdn_tree: Path) -> None:
    """All six Tanzil variants are whole: 114 chapters, 6,236 verses, plus chapter files."""
    for variant in config.TANZIL_VARIANTS:
        chapters = read_json(cdn_tree / "text" / variant / "quran.json")

        assert len(chapters) == CHAPTERS, variant
        assert sum(len(chapter["verses"]) for chapter in chapters) == VERSES, variant
        assert (cdn_tree / "text" / variant / "chapters" / f"{CHAPTERS}.json").exists()


def test_the_unvocalised_script_carries_no_vowel_marks(cdn_tree: Path) -> None:
    """`simple-clean` is the variant to reach for when no harakat is wanted.

    `simple` is an easy trap: it is a different orthography, not a different level of
    vocalisation, and it carries the full set of marks.
    """
    clean = read_json(cdn_tree / "text" / "simple-clean" / "chapters" / "1.json")
    text = clean["verses"][0]["text"]

    expected = (
        "\u0628\u0633\u0645 \u0627\u0644\u0644\u0647 "
        "\u0627\u0644\u0631\u062d\u0645\u0646 \u0627\u0644\u0631\u062d\u064a\u0645"
    )
    assert text == expected
    assert not [char for char in text if 0x064B <= ord(char) <= 0x0652]

    marked = read_json(cdn_tree / "text" / "simple" / "chapters" / "1.json")
    assert [char for char in marked["verses"][0]["text"] if 0x064B <= ord(char) <= 0x0652]


def test_paths_are_unversioned(cdn_tree: Path) -> None:
    """A published path never gains a version segment, and never needs a redirect."""
    assert not (cdn_tree / config.DATASET_VERSION).exists()
    assert not (cdn_tree / "versions.json").exists()
    assert not (cdn_tree / "_redirects").exists()


def test_gated_tree_omits_restricted_editions_entirely(cdn_tree: Path) -> None:
    """A restricted edition must leave no trace in the published tree."""
    catalogue = read_json(cdn_tree / "translations" / "index.json")
    published = {entry["edition"] for entry in catalogue["editions"]}

    withheld = {entry["edition"] for entry in catalogue["withheld"]}
    assert withheld, "the catalogue must report what it withheld"
    assert not withheld & published

    directories = {path.name for path in (cdn_tree / "translations").iterdir() if path.is_dir()}
    assert directories == {
        entry["path"].rstrip("/").rsplit("/", 1)[-1] for entry in catalogue["editions"]
    }


def test_catalogue_entries_are_self_describing(cdn_tree: Path) -> None:
    """Every entry states where it lives, what it is, and the terms it is published under."""
    catalogue = read_json(cdn_tree / "translations" / "index.json")

    assert catalogue["count"] == len(catalogue["editions"]) > 0

    for entry in catalogue["editions"]:
        assert entry["path"].startswith(f"/translations/{entry['code']}-"), entry["path"]
        assert (cdn_tree / entry["path"].lstrip("/")).is_dir(), entry["path"]
        assert entry["direction"] in {"ltr", "rtl"}, entry["path"]
        assert entry["license"]["status"] == "granted", entry["path"]

        # QuranEnc condition 3 requires stating the version of a republished translation.
        if entry["source"].startswith("https://quranenc.com"):
            assert entry["version"] != "n/a", entry["path"]


def test_manifest_agrees_with_the_tree_it_describes(cdn_tree: Path) -> None:
    manifest = read_json(cdn_tree / "manifest.json")
    catalogue = read_json(cdn_tree / "translations" / "index.json")

    assert manifest["chapters"]["count"] == CHAPTERS
    assert [script["id"] for script in manifest["scripts"]] == list(config.TANZIL_VARIANTS)
    assert manifest["translations"]["count"] == catalogue["count"]
    assert (cdn_tree / "chapters.json").exists()

    for script in manifest["scripts"]:
        assert script["verses"] == VERSES, script["id"]


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
