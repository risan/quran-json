"""The licensed dataset generation: Tanzil text and metadata, QuranEnc translations.

These pin the properties that make this generation different from the frozen `dist/`
tree, including the basmala convention, which is the one change most likely to surprise
a consumer migrating from the old text.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from quranjson import config, quranenc
from quranjson.build import Sources
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
        chapter = read_json(cdn_tree / "chapters" / key / "1.json")

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
        chapter = read_json(cdn_tree / "chapters" / key / "1.json")

        assert (cdn_tree / f"quran_{key}.json").exists()
        assert chapter["verses"][0]["translation"].startswith("In the name of")
        # Verse 0 of the source archive must not leak in as an extra ayah.
        assert [v["id"] for v in chapter["verses"]] == list(range(1, 8))


def test_published_manifest_declares_every_edition_as_granted(cdn_tree: Path) -> None:
    manifest = read_json(cdn_tree / "meta" / "sources.json")

    assert manifest["text"]["status"] == "granted"
    assert manifest["text"]["edition"] == "tanzil-uthmani"
    assert manifest["transliteration"]["status"] == "withheld"

    editions = manifest["editions"]
    assert len(editions) == 83
    assert {entry["status"] for entry in editions} == {"granted"}

    # QuranEnc condition 3: state the version of a republished translation.
    quranenc_entries = []
    for entry in editions:
        if entry["lang"].startswith("english_rwwad") or entry["lang"].startswith("indonesian"):
            quranenc_entries.append(entry)

    assert quranenc_entries
    for entry in quranenc_entries:
        assert entry["version"] != "n/a", entry["lang"]

    for entry in editions:
        assert entry["license_url"].startswith("https://"), entry["lang"]
        assert entry["author"].strip(), entry["lang"]


def test_catalogue_records_language_and_version(catalogue: dict) -> None:
    translations = catalogue["translations"]

    assert len(translations) == 75
    assert len({entry["lang"] for entry in translations}) == 56

    for entry in translations:
        # Condition 3 of the QuranEnc grant: state the version when republishing.
        assert entry["version"], entry["key"]
        assert entry["database_url"].startswith("https://"), entry["key"]


def test_featured_keys_pick_one_translation_per_language(catalogue: dict) -> None:
    featured = quranenc.featured_keys(catalogue)

    assert len(featured) == len(set(featured))
    assert len(featured) == 11
    assert "english_rwwad" in featured

    langs = [entry["lang"] for entry in catalogue["translations"] if entry["key"] in featured]
    assert len(langs) == len(set(langs))


def test_footnotes_travel_with_the_verse(licensed: Sources, cdn_tree: Path) -> None:
    """QuranEnc grants republication on condition of no deletion."""
    with_notes = [
        verse for verse in licensed.editions["english_rwwad"]["1"] if verse.get("footnotes")
    ]

    assert with_notes, "expected at least one footnoted verse in Al-Fatiha"

    published = read_json(cdn_tree / "chapters" / "english_rwwad" / "1.json")
    assert any("footnotes" in verse for verse in published["verses"])


def test_published_verse_index_covers_the_featured_translations(
    cdn_tree: Path, catalogue: dict
) -> None:
    published = read_json(cdn_tree / "verses" / "1.json")

    assert sorted(published["translations"]) == sorted(quranenc.featured_keys(catalogue))
    assert "transliteration" not in published


def test_licensed_tree_publishes_every_translation_per_chapter(cdn_tree: Path) -> None:
    for key in ("english_rwwad", "urdu_junagarhi", "chinese_suliman"):
        assert (cdn_tree / "chapters" / key / "1.json").exists()
        assert (cdn_tree / f"quran_{key}.json").exists()

    # The legacy registry's codes are not edition keys in this generation.
    assert not (cdn_tree / "chapters" / "en").exists()
    assert not (cdn_tree / "quran_transliteration.json").exists()
