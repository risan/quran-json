"""Structural and textual invariants of the dataset.

These defend the properties a consumer actually relies on: chapter and verse counts,
the 1..n verse numbering of every Hafs script, and translation coverage.
"""

from __future__ import annotations

from pathlib import Path

from quranjson import config
from quranjson.jsonio import read_json

CHAPTERS = 114
VERSES = 6236


def _hafs_scripts(cdn_tree: Path) -> list[str]:
    manifest = read_json(cdn_tree / "manifest.json")

    return [script["id"] for script in manifest["scripts"] if script["verse_ids"] == "hafs"]


def test_chapter_table_is_complete(cdn_tree: Path) -> None:
    chapters = read_json(cdn_tree / "chapters.json")

    assert len(chapters) == CHAPTERS
    assert [chapter["id"] for chapter in chapters] == list(range(1, CHAPTERS + 1))
    assert sum(chapter["total_verses"] for chapter in chapters) == VERSES


def test_declared_verse_counts_match_every_hafs_script(cdn_tree: Path) -> None:
    declared = {
        chapter["id"]: chapter["total_verses"] for chapter in read_json(cdn_tree / "chapters.json")
    }
    scripts = _hafs_scripts(cdn_tree)

    assert "uthmani" in scripts

    for script in scripts:
        for chapter in read_json(cdn_tree / "text" / script / "quran.json"):
            verses = chapter["verses"]

            assert len(verses) == declared[chapter["id"]], f"{script} {chapter['id']}"
            assert [verse["id"] for verse in verses] == list(range(1, len(verses) + 1))


def test_every_script_has_text_for_every_verse(cdn_tree: Path) -> None:
    for script in config.SCRIPT_IDS:
        for chapter in read_json(cdn_tree / "text" / script / "quran.json"):
            for verse in chapter["verses"]:
                assert verse["text"].strip(), f"{script} {chapter['id']}:{verse['id']}"


def test_translations_align_with_the_chapter_table_verse_for_verse(cdn_tree: Path) -> None:
    declared = {
        chapter["id"]: chapter["total_verses"] for chapter in read_json(cdn_tree / "chapters.json")
    }
    catalogue = read_json(cdn_tree / "translations" / "index.json")

    assert catalogue["editions"]

    for edition in catalogue["editions"]:
        chapters = read_json(cdn_tree / edition["path"].lstrip("/") / "quran.json")

        assert [chapter["id"] for chapter in chapters] == list(range(1, CHAPTERS + 1)), edition
        assert sum(len(chapter["verses"]) for chapter in chapters) == VERSES, edition["edition"]

        for chapter in chapters:
            ids = [verse["id"] for verse in chapter["verses"]]

            assert ids == list(range(1, declared[chapter["id"]] + 1)), edition["edition"]


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
    """Every published script is whole: 114 chapters, its own verse count, chapter files.

    The count is per script rather than a constant: the Hafs-count scripts run to 6,236,
    while Warsh and Qalun carry Nafiʿ's 6,214 ayahs.
    """
    for script in config.SCRIPT_IDS:
        chapters = read_json(cdn_tree / "text" / script / "quran.json")

        assert len(chapters) == CHAPTERS, script
        assert (
            sum(len(chapter["verses"]) for chapter in chapters) == config.SCRIPT_VERSES[script]
        ), script
        assert (cdn_tree / "text" / script / "chapters" / f"{CHAPTERS}.json").exists()


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
    assert [script["id"] for script in manifest["scripts"]] == list(config.SCRIPT_IDS)
    assert manifest["translations"]["count"] == catalogue["count"]
    assert (cdn_tree / "chapters.json").exists()

    for script in manifest["scripts"]:
        assert script["verses"] == config.SCRIPT_VERSES[script["id"]], script["id"]
