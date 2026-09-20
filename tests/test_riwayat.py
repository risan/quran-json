"""The two Nafiʿ riwayat: Warsh and Qalun from Qur'anpedia.net's dumps.

A riwayah is not an orthography. Warsh and Qalun read the text differently, and they number
6,214 ayahs to Nafiʿ's count where the Kufi count -- Hafs, and every other script here --
runs to 6,236. These tests defend the three consequences a consumer meets: the verse count,
the genuinely-different reading, and the `number_in_hafs` map that makes the two counts
joinable instead of merely inconsistent.
"""

from __future__ import annotations

import collections
from pathlib import Path

from quranjson import config, jsonio

CHAPTERS = 114
MAGHRIBI_SCRIPTS = (config.WARSH_SCRIPT, config.QALUN_SCRIPT)
VERSES = 6214

#: Surahs where Nafiʿ's count differs from the Kufi count. Pinned because 50 is the figure
#: the manifest note states: if upstream ever renumbers, that note must be revised with it.
DIFFERING_SURAHS = 50


def _script(cdn_tree: Path, script: str) -> list[dict[str, object]]:
    return jsonio.read_json(cdn_tree / "text" / script / "quran.json")


def test_both_riwayat_are_published_whole(cdn_tree: Path) -> None:
    for script in MAGHRIBI_SCRIPTS:
        chapters = _script(cdn_tree, script)

        assert len(chapters) == CHAPTERS, script
        assert sum(len(chapter["verses"]) for chapter in chapters) == VERSES, script
        assert all(
            [verse["id"] for verse in chapter["verses"]]
            == list(range(1, len(chapter["verses"]) + 1))
            for chapter in chapters
        ), script


def test_the_riwayat_are_different_readings_not_relabelled_hafs(cdn_tree: Path) -> None:
    """The trap this guards against: repos that ship Hafs twice, once under `warsh`.

    One such repo's Warsh file is byte-identical to its Hafs file in 6,236 of 6,236 verses.
    A Maghribi text is separable mechanically -- no alef wasla (U+0671), and instead the
    Maghribi dabt layer (U+06EC, U+06D2) -- and Warsh and Qalun must differ from each other.
    """
    fingerprints: dict[str, collections.Counter[int]] = {}

    for script in MAGHRIBI_SCRIPTS:
        counter: collections.Counter[int] = collections.Counter()
        for chapter in _script(cdn_tree, script):
            for verse in chapter["verses"]:
                counter.update(ord(char) for char in str(verse["text"]))
        fingerprints[script] = counter

        assert counter[0x0671] == 0, f"{script} marks alef wasla, so it is Hafs rasm"
        assert counter[0x06D2] > 1000, f"{script} carries no yeh barree"
        assert counter[0x06EC] > 1000, f"{script} carries no Maghribi rounded high stop"

    warsh = _verses(_script(cdn_tree, config.WARSH_SCRIPT))
    qalun = _verses(_script(cdn_tree, config.QALUN_SCRIPT))
    differing = sum(1 for left, right in zip(warsh, qalun, strict=True) if left != right)

    assert differing > 1000, "the two riwayat are the same text"


def _verses(chapters: list[dict[str, object]]) -> list[str]:
    return [str(verse["text"]) for chapter in chapters for verse in chapter["verses"]]


def test_the_mapping_covers_the_hafs_count_surah_by_surah(cdn_tree: Path) -> None:
    """`number_in_hafs` is the whole reason these scripts are usable next to the others.

    Per surah, the highest Hafs ayah the riwayah maps onto must be that surah's last Hafs
    ayah -- if it stopped short, the two counts could not be joined at all.
    """
    hafs = jsonio.read_json(config.kemenag_path())

    for script in config.RIWAYAH_SCRIPTS:
        for chapter in _script(cdn_tree, script):
            mapped = [number for verse in chapter["verses"] for number in verse["number_in_hafs"]]

            assert mapped, f"{script} {chapter['id']}: a verse maps to no Hafs ayah"
            assert max(mapped) == len(hafs[str(chapter["id"])]), f"{script} {chapter['id']}"


def test_the_verse_counts_differ_from_the_hafs_metadata(cdn_tree: Path) -> None:
    """`/chapters.json` is Hafs metadata, so the riwayat counts against it are documented.

    The manifest carries a per-script `note` saying so; this pins the scale of the
    divergence rather than leaving it to the note alone.
    """
    hafs = jsonio.read_json(config.kemenag_path())

    expected_differences = {
        config.WARSH_SCRIPT: 50,
        config.QALUN_SCRIPT: 50,
        config.DURI_SCRIPT: 44,
    }
    for script in config.RIWAYAH_SCRIPTS:
        chapters = _script(cdn_tree, script)
        differing = [
            chapter["id"]
            for chapter in chapters
            if len(chapter["verses"]) != len(hafs[str(chapter["id"])])
        ]

        assert len(differing) == expected_differences[script], script
        assert 2 in differing and 9 in differing

        note = next(
            entry["note"]
            for entry in jsonio.read_json(cdn_tree / "manifest.json")["scripts"]
            if entry["id"] == script
        )
        assert f"{config.SCRIPT_VERSES[script]:,}" in note
        assert "number_in_hafs" in note


def test_duri_fatiha_preserves_the_non_surjective_source_map(cdn_tree: Path) -> None:
    chapter = _script(cdn_tree, config.DURI_SCRIPT)[0]
    assert [verse["number_in_hafs"] for verse in chapter["verses"]] == [
        [2],
        [3],
        [4],
        [5],
        [6],
        [7],
        [7],
    ]

    descriptor = next(
        entry
        for entry in jsonio.read_json(cdn_tree / "manifest.json")["scripts"]
        if entry["id"] == config.DURI_SCRIPT
    )
    assert descriptor["mapping_coverage_exceptions"] == [
        {
            "chapter": 1,
            "missing_hafs": [1],
            "repeated_hafs": [7],
            "reason": "source bismillah is unnumbered; retain source map without inventing Hafs 1",
        }
    ]
