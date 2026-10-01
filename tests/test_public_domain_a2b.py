"""Rodwell, Kanzul Iman, Mahmud ul Hasan and Keyzer: complete, aligned, repaired and licensed."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from quranjson import cdn, config, qa, sources
from quranjson.jsonio import read_json

NEW_KEYS = ("english_rodwell", "urdu_kanzuliman", "urdu_mahmudulhasan", "dutch_keyzer")
DEATH_YEARS = {
    "english_rodwell": "1900",
    "urdu_kanzuliman": "1921",
    "urdu_mahmudulhasan": "1920",
    "dutch_keyzer": "1868",
}
FOOTNOTE_MARKER = re.compile(r"\[\d+(?:/\d+)?[\]\[]")


def _snapshot(key: str) -> dict[str, list[dict]]:
    return read_json(config.extra_edition_path(key))


def _verse(key: str, chapter: int, verse: int) -> str:
    return _snapshot(key)[str(chapter)][verse - 1]["text"]


@pytest.mark.parametrize("key", NEW_KEYS)
def test_edition_is_complete_aligned_and_non_empty(key: str) -> None:
    snapshot = _snapshot(key)
    chapters = read_json(config.tanzil_chapters_path())["chapters"]

    assert len(snapshot) == 114
    total = 0
    for chapter in chapters:
        entries = snapshot[str(chapter["id"])]

        assert [entry["verse"] for entry in entries] == list(range(1, chapter["total_verses"] + 1))
        assert all(entry["chapter"] == chapter["id"] for entry in entries)
        assert all(entry["text"].strip() for entry in entries), (key, chapter["id"])
        assert all(entry["text"] == entry["text"].strip() for entry in entries)
        total += len(entries)

    assert total == 6236


@pytest.mark.parametrize("key", NEW_KEYS)
def test_licence_is_a_public_domain_grant_citing_the_death_year_and_its_source(key: str) -> None:
    edition = next(item for item in config.EXTRA_EDITIONS if item.lang == key)

    assert edition.license.status == "granted"
    assert edition.license.text.startswith("Public domain.")
    assert f"Translator died {DEATH_YEARS[key]} (https://" in edition.license.text
    assert edition.license.url.startswith("https://")


def test_urls_are_unique_and_follow_the_code_slug_convention() -> None:
    keys = {
        config_edition.lang: cdn.edition_url_key(config_edition)
        for config_edition in cdn.published_editions()
    }

    assert keys["english_rodwell"] == "en-rodwell"
    assert keys["urdu_kanzuliman"] == "ur-kanzuliman"
    assert keys["urdu_mahmudulhasan"] == "ur-mahmudulhasan"
    assert keys["dutch_keyzer"] == "nl-keyzer"
    assert len(set(keys.values())) == len(keys)


def test_openings_read_as_the_translators() -> None:
    assert _verse("english_rodwell", 1, 1) == "In the Name of God, the Compassionate, the Merciful"
    assert _verse("urdu_kanzuliman", 1, 1) == "اللہ کے نام سے شروع جو بہت مہربان رحمت والا"
    assert (
        _verse("urdu_mahmudulhasan", 1, 1) == "شروع اللہ کے نام سے جو بڑا مہربان نہایت رحم والا ہے"
    )
    assert _verse("dutch_keyzer", 1, 1) == "In naam van den lankmoedigen en albarmhartigen God"
    for key in NEW_KEYS:
        assert len(_snapshot(key)["1"]) == 7
        assert len(_snapshot(key)["112"]) == 4


def test_mahmud_ul_hasan_footnote_markers_are_gone_but_glosses_stay() -> None:
    snapshot = _snapshot("urdu_mahmudulhasan")
    texts = [entry["text"] for entries in snapshot.values() for entry in entries]

    assert not [text for text in texts if FOOTNOTE_MARKER.search(text)]
    assert not [text for text in texts if any(char.isdigit() for char in text)]
    assert _verse("urdu_mahmudulhasan", 112, 1) == "تو کہہ وہ اللہ ایک ہے"
    assert any("[یعنی انکے اعتراضوں سے]" in text for text in texts)


def test_strip_footnote_markers_handles_every_marker_shape() -> None:
    one, two, three, four = "\u06f1", "\u06f2", "\u06f3", "\u06f4"
    alif = "\u0627"
    grouped = {
        "1": [
            {"text": f"x [{one}] y [{two}{three}] z [{one}{two}{three}/{four}]"},
            {"text": "x [12] y [66["},
            {"text": "x [gloss] z"},
            {"text": f"[{alif}] x y ]{two}{three}{two}] z [{one}{alif}]"},
            {"text": f"la{four}e"},
            {"text": f"[{alif}x y ]{two}{three}{two}] z [{two}{three}{three}]"},
        ]
    }

    result = sources.strip_footnote_markers(grouped)

    assert [entry["text"] for entry in result["1"]] == [
        "x y z",
        "x y",
        "x [gloss] z",
        "x y z",
        "lae",
        f"{alif}x y z",
    ]


def test_keyzer_chapter_opening_letters_are_restored() -> None:
    expected = {
        (2, 1): "A. L. M.",
        (3, 1): "A. L. M.",
        (20, 1): "T. H.",
        (26, 1): "T. S. M.",
        (28, 1): "T. S. M.",
        (29, 1): "A. L. M.",
        (32, 1): "A. L. M.",
    }

    for (chapter, verse), text in expected.items():
        assert _verse("dutch_keyzer", chapter, verse) == text

    assert _verse("dutch_keyzer", 27, 1).startswith("T. S. Dit zijn de teekenen")
    assert _verse("dutch_keyzer", 12, 1).startswith("E. L. R. Dit zijn teekens")


def test_every_keyzer_correction_cites_gutenberg_and_anchors_at_the_verse_start() -> None:
    corrections = [item for item in qa.known() if item.lang == "dutch_keyzer"]

    assert {item.chapter for item in corrections} >= {2, 3, 20, 26, 28, 29, 30, 31, 32}
    for item in corrections:
        assert item.at_start
        assert item.evidence.startswith("https://www.gutenberg.org/ebooks/19786")


def test_a_repaired_keyzer_verse_is_not_corrected_twice() -> None:
    repaired = {"2": [{"verse": 1, "text": "A. L. M."}]}

    with pytest.raises(ValueError, match="defective fragment absent"):
        qa.apply_corrections("dutch_keyzer", repaired)


def test_the_three_pd_sources_are_pinned_or_fetched_without_a_transform_surprise() -> None:
    tasks = {task.path.stem: task for task in sources.licensed_tasks()}

    assert tasks["urdu_kanzuliman"].source_sha256 == sources.PINNED_EXTRA_SOURCES["urdu_kanzuliman"]
    assert tasks["urdu_kanzuliman"].parse is not None
    assert tasks["urdu_mahmudulhasan"].transform is not None
    assert tasks["english_rodwell"].source_sha256 is None


def test_published_directions_and_listing(cdn_tree: Path) -> None:
    index = read_json(cdn_tree / "translations" / "index.json")
    by_edition = {entry["edition"]: entry for entry in index["editions"]}

    assert by_edition["urdu_kanzuliman"]["direction"] == "rtl"
    assert by_edition["urdu_mahmudulhasan"]["direction"] == "rtl"
    assert by_edition["english_rodwell"]["direction"] == "ltr"
    assert by_edition["dutch_keyzer"]["code"] == "nl"
    for key in NEW_KEYS:
        assert by_edition[key]["license"]["status"] == "granted"
