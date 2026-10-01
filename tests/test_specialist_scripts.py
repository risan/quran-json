"""KFGQPC Hafs and the specialist riwayat added from Quranpedia (Track A2a)."""

from __future__ import annotations

from pathlib import Path

import pytest

from quranjson import config, jsonio, quranpedia

BISMILLAH_PREFIX = "بِسۡمِ"


def _manifest_scripts(cdn_tree: Path) -> dict[str, dict[str, object]]:
    manifest = jsonio.read_json(cdn_tree / "manifest.json")

    return {script["id"]: script for script in manifest["scripts"]}


def _snapshot(script: str) -> dict[str, list[dict[str, object]]]:
    return jsonio.read_json(config.quranpedia_path(script))


@pytest.mark.parametrize("script", config.NATIVE_HAFS_QURANPEDIA_SCRIPTS)
def test_native_hafs_scripts_number_every_verse_as_hafs(script: str) -> None:
    snapshot = _snapshot(script)

    assert sum(map(len, snapshot.values())) == 6236
    assert all(
        verse["number_in_hafs"] == [verse["verse"]]
        for verses in snapshot.values()
        for verse in verses
    )


def test_qpc_hafs_carries_the_basmala_only_as_fatiha_verse_one() -> None:
    snapshot = _snapshot(config.QPC_HAFS_SCRIPT)

    assert len(snapshot["1"]) == 7
    assert str(snapshot["1"][0]["text"]).startswith(BISMILLAH_PREFIX)

    prefixed = [
        chapter
        for chapter, verses in snapshot.items()
        if chapter != "1" and str(verses[0]["text"]).startswith(BISMILLAH_PREFIX)
    ]
    assert prefixed == []


def test_susi_keeps_the_unnumbered_fatiha_basmala_exception() -> None:
    snapshot = _snapshot(config.SUSI_SCRIPT)

    assert sum(map(len, snapshot.values())) == quranpedia.VERSE_COUNT[config.SUSI_SCRIPT] == 6217
    assert [verse["number_in_hafs"] for verse in snapshot["1"]] == [
        [2],
        [3],
        [4],
        [5],
        [6],
        [7],
        [7],
    ]
    assert config.SCRIPT_MAPPING_COVERAGE_EXCEPTIONS[config.SUSI_SCRIPT][0]["missing_hafs"] == (1,)


def test_al_mulk_is_split_in_duri_but_not_in_susi() -> None:
    """Both are Abu ʿAmr's riwayat; the source splits Hafs 67:9 for al-Duri only.

    Recorded rather than corrected: nothing independent says which numbering the printed
    mushafs follow, so the dumps are published as the source states them.
    """
    duri = _snapshot(config.DURI_SCRIPT)["67"]
    susi = _snapshot(config.SUSI_SCRIPT)["67"]

    assert (len(duri), len(susi)) == (31, 30)
    assert [verse["number_in_hafs"] for verse in duri[8:10]] == [[9], [9]]
    assert [verse["number_in_hafs"] for verse in susi[8:10]] == [[9], [10]]


def test_specialist_group_is_declared_only_for_the_specialist_readings(cdn_tree: Path) -> None:
    scripts = _manifest_scripts(cdn_tree)

    grouped = {script for script, entry in scripts.items() if "group" in entry}

    assert grouped == set(config.SPECIALIST_SCRIPTS) == {"shubah", "susi"}
    assert all(scripts[script]["group"] == "specialist" for script in grouped)
    assert all(scripts[script]["group_note"] for script in grouped)
    assert "specialists" in str(scripts["shubah"]["description"])


def test_shubah_never_offers_hafs_per_ayah_audio(cdn_tree: Path) -> None:
    entry = _manifest_scripts(cdn_tree)["shubah"]

    assert entry["verse_ids"] == "hafs"
    assert entry["audio"] == {"verse_numbering": "hafs", "per_ayah": False}


def test_susi_publishes_its_bismillah_as_unnumbered_furniture(cdn_tree: Path) -> None:
    entry = _manifest_scripts(cdn_tree)["susi"]

    assert entry["chapter_furniture"] == [
        {
            "chapter": 1,
            "position": "before-verses",
            "kind": "bismillah",
            "text": quranpedia.DUMP_METADATA[config.SUSI_SCRIPT]["bismillah"],
            "numbered": False,
        }
    ]


def test_bazzi_and_qunbul_are_skipped_with_a_reason(cdn_tree: Path) -> None:
    scripts = _manifest_scripts(cdn_tree)

    assert set(quranpedia.SKIPPED) == {"bazzi", "qunbul"}
    assert not set(quranpedia.SKIPPED) & set(scripts)


def test_a_malformed_jinn_style_map_fails_the_mapping_gate() -> None:
    """The defect that keeps Bazzi and Qunbul out: a last ayah that maps back to Hafs 2."""
    chapter = [{"verse": 1, "number_in_hafs": [1]}, {"verse": 2, "number_in_hafs": [2]}]
    chapter.append({"verse": 3, "number_in_hafs": [3]})
    chapter.append({"verse": 4, "number_in_hafs": [2]})

    with pytest.raises(ValueError, match="non-monotonic"):
        quranpedia._validate_mapping({"1": chapter}, {1: 4}, script=config.SUSI_SCRIPT)
