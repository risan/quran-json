"""The published audio index.

We ship URL templates rather than audio, so the properties that matter are: the padding
scheme per host is right, no per-ayah file explosion, and the host terms are recorded.
"""

from __future__ import annotations

import pytest

from quranjson import audio, config
from quranjson.jsonio import read_json

VERSES = 6236


@pytest.fixture(scope="module")
def index(tmp_path_factory: pytest.TempPathFactory) -> dict:
    out = tmp_path_factory.mktemp("audio")
    return audio.build_audio_index(out)


def test_index_covers_every_host(index: dict) -> None:
    assert set(index["hosts"]) == set(audio.AUDIO_HOSTS)
    assert {entry["host"] for entry in index["reciters"]} == set(audio.AUDIO_HOSTS)


def test_each_host_has_at_least_one_recitation(index: dict) -> None:
    counts: dict[str, int] = {}
    for entry in index["reciters"]:
        counts[entry["host"]] = counts.get(entry["host"], 0) + 1

    # everyayah 79, mp3quran 288 moshaf, islamic.network 69 + 159 editions.
    assert counts["everyayah"] == 79
    assert counts["mp3quran"] == 288
    assert counts["islamic_network"] == 228


def test_templates_use_the_scheme_each_host_actually_serves(index: dict) -> None:
    urls = {entry["id"]: entry["url"] for entry in index["reciters"]}

    # everyayah: {SSS}{AAA}.mp3 -- both three digits, ayah is surah-relative.
    assert urls["everyayah/Alafasy_128kbps"] == (
        "https://everyayah.com/data/Alafasy_128kbps/{surah:03d}{ayah:03d}.mp3"
    )
    # mp3quran: whole-surah, three-digit surah.
    assert urls["mp3quran/1-1"].endswith("/{surah:03d}.mp3")
    # islamic.network per-ayah uses the GLOBAL ayah number, unpadded.
    assert urls["islamic_network/128/ar.alafasy"].endswith("/{ayah}.mp3")


def test_no_reciter_placeholder_survives_into_a_url(index: dict) -> None:
    for entry in index["reciters"]:
        assert "{reciter}" not in entry["url"], entry["id"]


def test_islamic_network_per_surah_editions_are_complete(index: dict) -> None:
    surahs = [
        entry
        for entry in index["reciters"]
        if entry["host"] == "islamic_network" and entry["scope"] == "surah"
    ]

    assert surahs
    for entry in surahs:
        assert entry["surah_files"] == 114, entry["id"]


def test_ayah_counts_sum_to_the_quran(index: dict) -> None:
    manifest = read_json(config.DATA / "audio" / "everyayah.json")

    assert sum(manifest["ayah_count"]) == VERSES
    assert len(manifest["ayah_count"]) == 114


def test_publishing_urls_not_audio_is_recorded(index: dict) -> None:
    for host, spec in index["hosts"].items():
        assert spec["license_status"] in {"granted", "restricted", "unknown"}
        assert spec["license_url"].startswith("https://"), host
        assert "does not host audio" in index["note"]
