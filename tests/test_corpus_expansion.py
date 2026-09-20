"""Regression contracts for the supplemental Arabic and translation corpus."""

from __future__ import annotations

from pathlib import Path

from quranjson import config, jsonio, quranenc, quranpedia

NEW_TRANSLATIONS = {
    "bengali_zakaria",
    "bengali_rwwad",
    "malay_basumayyah",
    "russian_rwwad",
    "korean_hamid",
    "korean_rwwad",
    "italian_rwwad",
    "ukrainian_yakubovych",
}
PUBLISHABLE_NEW_TRANSLATIONS = NEW_TRANSLATIONS - {"korean_rwwad"}


def test_new_source_snapshots_have_pinned_complete_shapes() -> None:
    duri = jsonio.read_json(config.quranpedia_path(config.DURI_SCRIPT))
    nastaliq = jsonio.read_json(config.quranpedia_path(config.HAFS_NASTALIQ_SCRIPT))

    assert len(duri) == len(nastaliq) == 114
    assert sum(map(len, duri.values())) == quranpedia.VERSE_COUNT[config.DURI_SCRIPT] == 6218
    assert (
        sum(map(len, nastaliq.values()))
        == quranpedia.VERSE_COUNT[config.HAFS_NASTALIQ_SCRIPT]
        == 6236
    )
    assert nastaliq["1"][0]["number_in_hafs"] == [1]
    assert all(
        verse["number_in_hafs"] == [verse["verse"]]
        for chapter in nastaliq.values()
        for verse in chapter
    )
    assert [verse["number_in_hafs"] for verse in duri["1"]] == [
        [2],
        [3],
        [4],
        [5],
        [6],
        [7],
        [7],
    ]


def test_supplemental_translations_are_complete_except_explicit_korean_candidate() -> None:
    chapters = {
        int(chapter["id"]): int(chapter["total_verses"])
        for chapter in jsonio.read_json(config.tanzil_chapters_path())["chapters"]
    }

    for key in NEW_TRANSLATIONS:
        snapshot = jsonio.read_json(config.quranenc_path(key))
        assert set(map(int, snapshot)) == set(range(1, 115))
        assert sum(map(len, snapshot.values())) == 6236
        assert all(len(snapshot[str(chapter)]) == count for chapter, count in chapters.items())
        quranenc.validate_translation(
            snapshot,
            chapter_counts=chapters,
            allow_empty=key == "korean_rwwad",
        )

    korean = jsonio.read_json(config.quranenc_path("korean_rwwad"))
    assert (
        sum(not verse["text"].strip() for entries in korean.values() for verse in entries) == 1955
    )
    assert all(
        not verse["text"].strip() for chapter in range(14, 36) for verse in korean[str(chapter)]
    )


def test_default_and_explicit_override_keep_incomplete_korean_out_of_public_bytes(
    cdn_tree: Path, cdn_override_tree: Path
) -> None:
    for tree in (cdn_tree, cdn_override_tree):
        catalogue = jsonio.read_json(tree / "translations" / "index.json")
        published = {entry["edition"] for entry in catalogue["editions"]}
        withheld = {entry["edition"]: entry for entry in catalogue["withheld"]}

        assert published >= PUBLISHABLE_NEW_TRANSLATIONS
        assert "korean_rwwad" not in published
        assert withheld["korean_rwwad"]["availability"] == "withheld"
        assert "1,955 empty" in withheld["korean_rwwad"]["reason"]
        assert not (tree / "translations" / "ko-rwwad").exists()


def test_manifest_declares_new_reading_identities_and_native_counts(cdn_tree: Path) -> None:
    manifest = jsonio.read_json(cdn_tree / "manifest.json")
    scripts = {script["id"]: script for script in manifest["scripts"]}

    assert scripts[config.DURI_SCRIPT]["verses"] == 6218
    assert scripts[config.DURI_SCRIPT]["native_chapter_counts"] == {
        str(chapter): len(entries)
        for chapter, entries in jsonio.read_json(config.quranpedia_path(config.DURI_SCRIPT)).items()
        if len(entries)
        != next(
            item["total_verses"]
            for item in jsonio.read_json(config.tanzil_chapters_path())["chapters"]
            if item["id"] == int(chapter)
        )
    }
    assert scripts[config.DURI_SCRIPT]["audio"]["per_ayah"] is False
    assert scripts[config.HAFS_NASTALIQ_SCRIPT]["audio"]["per_ayah"] is True
