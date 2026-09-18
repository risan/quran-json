"""The licensed dataset generation: Tanzil text and metadata, QuranEnc translations.

These pin the properties that make this generation different from the frozen `dist/`
tree, including the basmala convention, which is the one change most likely to surprise
a consumer migrating from the old text.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from quranjson import config
from quranjson.build import Sources
from quranjson.cdn import edition_url_key, published_editions
from quranjson.jsonio import read_json

CHAPTERS = 114
VERSES = 6236

#: Tanzil embeds the basmala at the head of ayah 1 rather than storing it as chapter
#: metadata. Two surahs spell it with a shadda on the beh (idgham with the preceding
#: surah's final letter), so there are two forms.
BASMALA = "\u0628\u0650\u0633\u0652\u0645\u0650 \u0671\u0644\u0644\u0651\u064e\u0647\u0650"
BASMALA_ASSIMILATED = (
    "\u0628\u0651\u0650\u0633\u0652\u0645\u0650 \u0671\u0644\u0644\u0651\u064e\u0647\u0650"
)


@pytest.fixture(scope="module")
def licensed() -> Sources:
    return Sources("licensed")


def url_of(edition_lang: str) -> str:
    """The published path segment for an edition, derived rather than hardcoded."""
    for edition in published_editions():
        if edition.lang == edition_lang:
            return edition_url_key(edition)
    raise AssertionError(f"{edition_lang} is not published")


def published_chapter(cdn_tree: Path, edition_lang: str, chapter: int = 1) -> dict:
    """One published chapter of one translation."""
    path = cdn_tree / "translations" / url_of(edition_lang) / "chapters" / f"{chapter}.json"
    return read_json(path)


@pytest.fixture(scope="module")
def catalogue() -> dict:
    return read_json(config.quranenc_catalogue_path())


def test_tanzil_text_covers_the_whole_quran(licensed: Sources) -> None:
    chapters = licensed.chapters[None]
    total = sum(len(licensed.verses(chapter["id"])) for chapter in chapters)

    assert len(chapters) == CHAPTERS
    assert total == VERSES


def test_tanzil_embeds_the_basmala_in_the_first_ayah_of_every_surah_but_at_tawbah(
    licensed: Sources,
) -> None:
    """The deliberate difference from the shipped text, which omitted it entirely."""
    plain, assimilated, absent = [], [], []

    for chapter in licensed.chapters[None]:
        first = licensed.verses(chapter["id"])[0]["text"]

        if first.startswith(BASMALA):
            plain.append(chapter["id"])
        elif first.startswith(BASMALA_ASSIMILATED):
            assimilated.append(chapter["id"])
        else:
            absent.append(chapter["id"])

    assert absent == [9]
    assert assimilated == [95, 97]
    assert plain == [n for n in range(1, CHAPTERS + 1) if n not in {9, 95, 97}]
    assert first_ayah(licensed, 9).startswith("\u0628\u064e\u0631\u064e\u0627"), "9:1"


def first_ayah(sources: Sources, chapter_id: int) -> str:
    """The opening ayah of a chapter."""
    return sources.verses(chapter_id)[0]["text"]


def test_tanzil_chapter_metadata_is_consistent(licensed: Sources) -> None:
    chapters = licensed.chapters[None]

    assert [chapter["id"] for chapter in chapters] == list(range(1, CHAPTERS + 1))
    assert sum(chapter["total_verses"] for chapter in chapters) == VERSES
    assert {chapter["type"] for chapter in chapters} == {"meccan", "medinan"}
    assert len([c for c in chapters if c["type"] == "meccan"]) == 86
    assert len([c for c in chapters if c["type"] == "medinan"]) == 28

    for chapter in chapters:
        assert len(licensed.verses(chapter["id"])) == chapter["total_verses"], chapter["id"]


def test_tanzil_structural_indexes_have_the_canonical_counts() -> None:
    indexes = read_json(config.tanzil_chapters_path())["indexes"]

    assert len(indexes["juzs"]) == 30
    assert len(indexes["hizbs"]) == 240
    assert len(indexes["pages"]) == 604
    assert len(indexes["sajdas"]) == 15


def test_every_published_translation_is_complete(licensed: Sources) -> None:
    """75 QuranEnc editions, 2 ClearQuran, and 4 public-domain English translations."""
    expected = {
        "english_itani",
        "english_itani_allah",
        "english_pickthall",
        "english_yusuf_ali",
        "english_palmer",
        "english_sale",
        "russian_sablukov",
        "russian_krachkovsky",
    }

    assert len(licensed.editions) == 83
    assert expected <= set(licensed.editions)

    for key, chapters in licensed.editions.items():
        assert len(chapters) == CHAPTERS, key

        total = 0
        for chapter in licensed.chapters[None]:
            entries = chapters[str(chapter["id"])]

            assert len(entries) == chapter["total_verses"], f"{key} {chapter['id']}"
            for index, entry in enumerate(entries, start=1):
                assert entry["chapter"] == chapter["id"]
                assert entry["verse"] == index
                assert entry["text"].strip(), f"{key} {chapter['id']}:{index}"

            total += len(entries)

        assert total == VERSES, key


def test_public_domain_translations_are_published(cdn_tree: Path) -> None:
    """The classics: their authors died long ago, so the works are free regardless of host."""
    for key, opening in (
        ("english_sale", "In the name of the most merciful God"),
        ("english_palmer", "IN the name of the merciful and compassionate God"),
        ("english_pickthall", "In the name of Allah, the Beneficent, the Merciful"),
        ("english_yusuf_ali", "In the name of Allah, Most Gracious, Most Merciful"),
    ):
        chapter = published_chapter(cdn_tree, key)

        assert chapter["verses"][0]["translation"] == opening, key
        assert len(chapter["verses"]) == 7, key


def test_public_domain_verdicts_state_their_basis() -> None:
    """A public-domain claim must name the work and why it is free."""
    for edition in config.EXTRA_EDITIONS:
        if edition.license.status != "granted":
            continue
        if edition.kind != "quran-api":
            continue

        assert edition.license.text.startswith("Public domain."), edition.lang
        assert "died" in edition.license.text, edition.lang
        assert edition.license.url.startswith("https://"), edition.lang


def test_clearquran_editions_are_published_from_the_translators_own_distribution(
    cdn_tree: Path,
) -> None:
    """The grant is the translator's (CC BY-ND 4.0), so it travels with his own files."""
    for key in ("english_itani", "english_itani_allah"):
        base = cdn_tree / "translations" / url_of(key)
        chapter = read_json(base / "chapters" / "1.json")

        assert (base / "quran.json").exists()
        assert chapter["verses"][0]["translation"].startswith("In the name of")
        # Verse 0 of the source archive must not leak in as an extra ayah.
        assert [v["id"] for v in chapter["verses"]] == list(range(1, 8))


def test_published_manifest_declares_every_edition_as_granted(cdn_tree: Path) -> None:
    manifest = read_json(cdn_tree / "meta" / "sources.json")

    assert manifest["text"]["status"] == "granted"
    assert manifest["text"]["scripts"] == list(config.SCRIPT_IDS)
    assert manifest["transliteration"]["status"] == "withheld"

    editions = manifest["editions"]
    assert len(editions) == 83
    assert {entry["status"] for entry in editions} == {"granted"}

    # QuranEnc condition 3: state the version of a republished translation.
    quranenc_entries = [
        entry for entry in editions if entry["source"].startswith("https://quranenc.com")
    ]

    assert quranenc_entries
    for entry in quranenc_entries:
        assert entry["version"] != "n/a", entry["edition"]

    for entry in editions:
        assert entry["license_url"].startswith("https://"), entry["edition"]
        assert entry["author"].strip(), entry["edition"]


def test_catalogue_records_language_and_version(catalogue: dict) -> None:
    translations = catalogue["translations"]

    assert len(translations) == 75
    assert len({entry["lang"] for entry in translations}) == 56

    for entry in translations:
        # Condition 3 of the QuranEnc grant: state the version when republishing.
        assert entry["version"], entry["key"]
        assert entry["database_url"].startswith("https://"), entry["key"]


def test_footnotes_travel_with_the_verse(licensed: Sources, cdn_tree: Path) -> None:
    """QuranEnc grants republication on condition of no deletion."""
    with_notes = [
        verse for verse in licensed.editions["english_rwwad"]["1"] if verse.get("footnotes")
    ]

    assert with_notes, "expected at least one footnoted verse in Al-Fatiha"

    published = published_chapter(cdn_tree, "english_rwwad")
    assert any("footnotes" in verse for verse in published["verses"])


def test_every_published_edition_has_a_whole_and_a_per_chapter_file(cdn_tree: Path) -> None:
    """One edition is reachable whole or chapter by chapter, for all 83."""
    for edition in published_editions():
        base = cdn_tree / "translations" / edition_url_key(edition)

        assert (base / "quran.json").exists(), edition.lang
        assert len(read_json(base / "quran.json")) == CHAPTERS, edition.lang
        assert (base / "chapters" / "1.json").exists(), edition.lang
        assert (base / "chapters" / f"{CHAPTERS}.json").exists(), edition.lang


def test_no_edition_is_reachable_only_through_the_chapter_tree(cdn_tree: Path) -> None:
    """The old tree had 75 editions but only 11 of them in the per-verse index."""
    catalogue = read_json(cdn_tree / "translations" / "index.json")

    assert len(catalogue["editions"]) == len(published_editions()) > 75
