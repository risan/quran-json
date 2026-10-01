"""The generated transliterations as published under `/transliteration/`."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from quranjson import romanize
from quranjson.jsonio import read_json

KEYS = ("id-skb", "en", "en-simple")


def _catalogue(tree: Path) -> dict[str, Any]:
    catalogue: dict[str, Any] = read_json(tree / "transliteration" / "index.json")

    return catalogue


def test_the_three_generated_editions_are_listed(cdn_tree: Path) -> None:
    catalogue = _catalogue(cdn_tree)

    assert [entry["path"] for entry in catalogue["editions"]] == [
        f"/transliteration/{key}/" for key in KEYS
    ]
    assert catalogue["count"] == 3
    assert catalogue["withheld"] == []
    assert read_json(cdn_tree / "manifest.json")["transliteration"]["count"] == 3


def test_every_entry_declares_its_reading_licence_and_review_status(cdn_tree: Path) -> None:
    for entry in _catalogue(cdn_tree)["editions"]:
        assert entry["reading"] == "hafs"
        assert entry["verse_ids"] == "hafs"
        assert entry["license"]["status"] == "granted"
        assert "CC BY-SA 4.0" in entry["license"]["text"]
        assert "Kemenag" in entry["license"]["text"]
        assert "machine-generated" in entry["review"]
        assert entry["method"]
        assert entry["source"] == "https://quran.kemenag.go.id/"


@pytest.mark.parametrize("key", KEYS)
def test_each_edition_covers_every_chapter_and_verse_of_the_hafs_count(
    cdn_tree: Path, key: str
) -> None:
    chapters = read_json(cdn_tree / "chapters.json")
    whole = read_json(cdn_tree / "transliteration" / key / "quran.json")

    assert [chapter["id"] for chapter in whole] == list(range(1, 115))

    for chapter, expected in zip(whole, chapters, strict=True):
        assert len(chapter["verses"]) == expected["total_verses"]
        assert chapter == read_json(
            cdn_tree / "transliteration" / key / "chapters" / f"{chapter['id']}.json"
        )


def test_the_published_editions_are_generated_from_the_spacing_corrected_text(
    cdn_tree: Path,
) -> None:
    """3:106 is one of the recorded spacing fixes: the question particle joins its verb."""
    chapter = read_json(cdn_tree / "transliteration" / "en" / "chapters" / "3.json")

    assert "akafartum" in chapter["verses"][105]["transliteration"]


def test_the_published_bytes_equal_the_generator_output(cdn_tree: Path) -> None:
    generated = romanize.build_editions()

    for key in KEYS:
        assert read_json(cdn_tree / "transliteration" / key / "quran.json") == generated[key]


def test_sources_manifest_explains_the_generated_transliterations(cdn_tree: Path) -> None:
    sources = read_json(cdn_tree / "meta" / "sources.json")["transliteration"]

    assert sources["status"] == "published"
    assert sources["generated"] is True
    assert "/text/kemenag/" in sources["source_text"]
    assert "Hafs" in sources["method"]
    assert "CC BY-SA 4.0" in sources["license"]
    assert sources["license_url"] == "https://creativecommons.org/licenses/by-sa/4.0/"
    assert [entry["path"] for entry in sources["editions"]] == [
        f"/transliteration/{key}/" for key in KEYS
    ]
