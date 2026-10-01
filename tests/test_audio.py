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

    # everyayah 79 listed + 2 unlisted, mp3quran 288 moshaf, islamic.network 69 + 159 editions.
    assert counts["everyayah"] == 81
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


def test_every_recording_declares_its_reading_and_content(index: dict) -> None:
    for entry in index["reciters"]:
        assert isinstance(entry["reading"], str) and entry["reading"], entry["id"]
        assert entry["content"] in {"recitation", "translation"}, entry["id"]


def test_every_ayah_recording_declares_verse_ids_or_null(index: dict) -> None:
    for entry in index["reciters"]:
        if entry["scope"] == "ayah":
            assert "verse_ids" in entry, entry["id"]
            assert entry["verse_ids"] in {"hafs", None}, entry["id"]
        else:
            assert "verse_ids" not in entry, entry["id"]


def test_hafs_numbering_is_only_claimed_for_hafs_recitations(index: dict) -> None:
    for entry in index["reciters"]:
        if entry.get("verse_ids") == "hafs":
            assert entry["reading"] == "hafs", entry["id"]
            assert entry["content"] == "recitation", entry["id"]


def test_warsh_folders_are_listed_but_never_claim_hafs_numbering(index: dict) -> None:
    warsh = [
        entry
        for entry in index["reciters"]
        if entry["host"] == "everyayah" and entry["id"].startswith("everyayah/warsh/")
    ]

    assert len(warsh) == 3
    for entry in warsh:
        assert entry["reading"] == "warsh", entry["id"]
        assert entry["verse_ids"] is None, entry["id"]


def test_every_everyayah_recitation_folder_is_hafs_unless_marked_otherwise(index: dict) -> None:
    hafs = [
        entry
        for entry in index["reciters"]
        if entry["host"] == "everyayah" and entry["reading"] == "hafs"
    ]

    assert len(hafs) == 70
    assert all(entry["verse_ids"] == "hafs" for entry in hafs)


def test_translation_audio_is_never_a_reading(index: dict) -> None:
    translations = [entry for entry in index["reciters"] if entry["content"] == "translation"]

    assert translations
    for entry in translations:
        assert entry["reading"] == "unknown", entry["id"]
        assert entry.get("verse_ids") is None, entry["id"]


def test_mp3quran_reading_comes_from_the_riwayah_in_the_moshaf_name() -> None:
    assert audio.mp3quran_reading("Rewayat Hafs A'n Assem - Murattal") == "hafs"
    assert audio.mp3quran_reading("Rewayat Warsh A'n Nafi' - Murattal") == "warsh"
    assert audio.mp3quran_reading("Rewayat Qalon A'n Nafi' Men Tariq Abi Nasheet - Murattal") == (
        "qalun"
    )
    assert audio.mp3quran_reading("Rewayat Aldori A'n Abi Amr - Murattal") == "duri-abu-amr"
    assert audio.mp3quran_reading("Rewayat Assosi A'n Abi Amr - Murattal") == "susi"
    assert audio.mp3quran_reading("Sho'bah A'n Asim - Murattal") == "shubah"
    assert audio.mp3quran_reading("Almusshaf Al Mojawwad - Almusshaf Al Mojawwad") == "unknown"


def test_every_mp3quran_riwayah_is_recognised_except_the_mushaf_styles(index: dict) -> None:
    unknown = {
        entry["recitation"]
        for entry in index["reciters"]
        if entry["host"] == "mp3quran" and entry["reading"] == "unknown"
    }

    assert unknown == {
        "Almusshaf Al Mojawwad - Almusshaf Al Mojawwad",
        "Almusshaf Al Mo'lim - Almusshaf Al Mo'lim",
    }


def test_islamic_network_reading_is_read_from_the_edition_identifier(index: dict) -> None:
    readings = {
        entry["id"]: entry["reading"]
        for entry in index["reciters"]
        if entry["host"] == "islamic_network"
    }

    assert readings["islamic_network/surah/128/ar.aliabdurrahmanalhuthaifyqaloon"] == "qalun"
    assert readings["islamic_network/surah/128/ar.abdurrasheedsufishubahanasim"] == "shubah"
    assert readings["islamic_network/surah/128/ar.abdurrasheedsufisoosi"] == "susi"
    assert (
        readings["islamic_network/surah/128/ar.abdurrasheedsufiaddoorianabiamr"] == "duri-abu-amr"
    )
    # Unmarked per-surah editions include Maghribi reciters; the host does not say Hafs.
    assert readings["islamic_network/surah/128/ar.benkirane"] == "unknown"
    assert readings["islamic_network/128/ar.alafasy"] == "hafs"
    assert readings["islamic_network/128/fr.leclerc"] == "unknown"


def test_everyayah_folders_missing_from_its_own_manifest_are_listed(index: dict) -> None:
    ids = {entry["id"] for entry in index["reciters"]}
    unlisted = read_json(config.DATA / "audio" / "everyayah_unlisted.json")

    assert unlisted["recitations"]
    for recitation in unlisted["recitations"]:
        assert f"everyayah/{recitation['id']}" in ids
        assert all(status == 200 for status, _ in recitation["checks"].values())

    for skipped in unlisted["not_added"]:
        assert f"everyayah/{skipped['folder']}" not in ids
