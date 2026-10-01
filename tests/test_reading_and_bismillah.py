"""Reading ids and basmala placement in the manifest, checked against the published text."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from quranjson import config
from quranjson.jsonio import read_json

SHADDA = "ّ"
EXPECTED_READING_IDS = {
    **dict.fromkeys(
        (
            *config.TANZIL_VARIANTS,
            config.KEMENAG_SCRIPT,
            config.DIGITALKHATT_SCRIPT,
            config.HAFS_NASTALIQ_SCRIPT,
            config.QPC_HAFS_SCRIPT,
        ),
        "hafs",
    ),
    config.WARSH_SCRIPT: "warsh",
    config.QALUN_SCRIPT: "qalun",
    config.DURI_SCRIPT: "duri-abu-amr",
    config.SUSI_SCRIPT: "susi",
    config.SHUBAH_SCRIPT: "shubah",
}

#: The scripts whose first verse of chapters 2 to 114 (except 9) begins with the basmala.
EMBEDDED = {*config.TANZIL_VARIANTS}


def _scripts(tree: Path) -> dict[str, dict[str, Any]]:
    return {script["id"]: script for script in read_json(tree / "manifest.json")["scripts"]}


def test_every_script_has_a_stable_reading_id(cdn_tree: Path) -> None:
    scripts = _scripts(cdn_tree)

    assert set(scripts) == set(EXPECTED_READING_IDS)
    assert {script: entry["reading"]["id"] for script, entry in scripts.items()} == (
        EXPECTED_READING_IDS
    )


def test_manifest_reading_ids_are_the_ids_the_audio_index_uses(cdn_tree: Path) -> None:
    reciters = read_json(cdn_tree / "audio" / "reciters.json")["reciters"]
    audio_readings = {entry["reading"] for entry in reciters}

    for reading_id in set(EXPECTED_READING_IDS.values()):
        assert reading_id in audio_readings, reading_id


def test_al_duris_two_readings_cannot_be_confused(cdn_tree: Path) -> None:
    """Al-Duri from Abu Amr and al-Duri from al-Kisai are different readings."""
    reciters = read_json(cdn_tree / "audio" / "reciters.json")["reciters"]
    readings = {entry["reading"] for entry in reciters}
    kisai = [entry for entry in reciters if entry["reading"] == "duri-kisai"]

    assert "duri" not in readings
    assert kisai
    assert all("Kisa" in entry["recitation"] for entry in kisai)
    assert _scripts(cdn_tree)[config.DURI_SCRIPT]["reading"]["id"] == "duri-abu-amr"


def _first_verses(tree: Path, script: str) -> dict[int, str]:
    chapters = read_json(tree / "text" / script / "quran.json")

    return {chapter["id"]: chapter["verses"][0]["text"] for chapter in chapters}


@pytest.mark.parametrize("script", config.SCRIPT_IDS)
def test_bismillah_placement_matches_the_script_text(cdn_tree: Path, script: str) -> None:
    bismillah = _scripts(cdn_tree)[script]["bismillah"]
    first = _first_verses(cdn_tree, script)
    wanted = bismillah["text"].replace(SHADDA, "")
    openers = {
        chapter: text.replace(SHADDA, "").startswith(wanted)
        for chapter, text in first.items()
        if chapter not in (1, 9)
    }

    assert bismillah["text"] == bismillah["text"].strip()
    assert bismillah["in_verse_one"] is (script in EMBEDDED)

    if bismillah["in_verse_one"]:
        assert all(openers.values()), [chapter for chapter, ok in openers.items() if not ok]
    else:
        assert not any(openers.values()), [chapter for chapter, ok in openers.items() if ok]

    assert (first[1] == bismillah["text"]) is bismillah["numbered_in_fatiha"]
    assert bismillah["numbered_in_fatiha"] is (script in config.BISMILLAH_NUMBERED_SCRIPTS)


def test_embedded_basmala_differs_from_the_text_only_by_a_shadda_in_two_chapters(
    cdn_tree: Path,
) -> None:
    first = _first_verses(cdn_tree, "uthmani")
    text = _scripts(cdn_tree)["uthmani"]["bismillah"]["text"]
    exact = {
        chapter
        for chapter, verse in first.items()
        if chapter not in (1, 9) and not verse.startswith(text)
    }

    assert exact == {95, 97}


def test_unnumbered_basmalas_say_where_their_text_comes_from(cdn_tree: Path) -> None:
    for script, entry in _scripts(cdn_tree).items():
        bismillah = entry["bismillah"]

        assert ("source" in bismillah) is (not bismillah["numbered_in_fatiha"]), script


def test_indopak_basmala_is_the_one_its_source_prints(cdn_tree: Path) -> None:
    from quranjson import digitalkhatt

    assert _scripts(cdn_tree)[config.DIGITALKHATT_SCRIPT]["bismillah"]["text"] == (
        digitalkhatt.BISMILLAH
    )
