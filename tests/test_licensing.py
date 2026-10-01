"""The licence gate.

Any change that silently publishes an edition without a verified grant fails here.
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from quranjson import audio, cdn, config, licensing
from quranjson.jsonio import read_json


def test_every_published_edition_is_granted_and_documented() -> None:
    editions = cdn.published_editions()

    assert editions

    for edition in editions:
        assert edition.redistributable, edition.lang
        assert edition.license.url.startswith("https://"), edition.lang
        assert edition.license.text.strip(), edition.lang


def test_require_publishable_refuses_an_edition_without_a_grant() -> None:
    granted = config.EXTRA_EDITIONS[0]
    restricted = dataclasses.replace(
        granted,
        lang="english_unlicensed",
        license=dataclasses.replace(granted.license, status="restricted"),
    )

    with pytest.raises(licensing.LicenseError) as error:
        licensing.require_publishable([granted, restricted])

    assert "english_unlicensed" in str(error.value)
    assert granted.lang not in str(error.value)


def test_require_publishable_allows_granted_editions() -> None:
    licensing.require_publishable(cdn.published_editions())


def test_tanzil_text_is_granted_and_no_script_is_published_without_a_grant() -> None:
    assert config.TANZIL_TEXT.status == "granted"

    for script in config.SCRIPT_IDS:
        assert config.SCRIPT_LICENSES[script].allows_publication, script


def test_tanzil_notice_is_in_every_tanzil_chapter_object_and_nowhere_else(
    cdn_tree: Path,
) -> None:
    for script in config.SCRIPT_IDS:
        expected = config.TANZIL_NOTICE if script in config.TANZIL_VARIANTS else None
        whole = read_json(cdn_tree / "text" / script / "quran.json")

        assert isinstance(whole, list), script
        assert [chapter.get("notice") for chapter in whole] == [expected] * 114, script

        for chapter in (1, 9, 114):
            single = read_json(cdn_tree / "text" / script / "chapters" / f"{chapter}.json")

            assert single.get("notice") == expected, f"{script} {chapter}"


def test_every_manifest_script_declares_its_licence_and_reading(cdn_tree: Path) -> None:
    manifest = read_json(cdn_tree / "manifest.json")

    assert [script["id"] for script in manifest["scripts"]] == list(config.SCRIPT_IDS)

    for script in manifest["scripts"]:
        license_ = script["license"]

        assert license_["status"] == "granted", script["id"]
        assert license_["url"].startswith("https://"), script["id"]
        assert license_["attribution"].strip(), script["id"]
        assert ("notice" in license_) == (script["id"] in config.TANZIL_VARIANTS), script["id"]
        assert set(script["reading"]) == {"riwayah", "qiraah", "verse_numbering"}, script["id"]
        assert script["reading"]["verse_numbering"] == script["verse_ids"], script["id"]

    hafs = {script["id"]: script["reading"] for script in manifest["scripts"]}["uthmani"]

    assert hafs["riwayah"] == "Hafs"
    assert hafs["qiraah"] == "ʿAsim"


def test_the_indo_pak_scripts_are_named_by_their_source(cdn_tree: Path) -> None:
    scripts = {script["id"]: script for script in read_json(cdn_tree / "manifest.json")["scripts"]}

    assert scripts["hafs-nastaliq"]["name"] == "Indo-Pak (KFGQPC Nastaleeq)"
    assert scripts["indopak"]["name"] == "Indo-Pak (DigitalKhatt)"
    assert "printed edition" not in scripts["hafs-nastaliq"]["description"]
    assert "0 of 6,236" not in config.DIGITALKHATT.text
    assert config.DIGITALKHATT.status == "granted"


def test_audio_hosts_state_what_is_known_about_their_terms() -> None:
    assert audio.AUDIO_HOSTS[audio.MP3QURAN]["license"].status == "unknown"
    assert audio.AUDIO_HOSTS[audio.ISLAMIC_NETWORK]["license"].url == (
        "https://alquran.cloud/terms-and-conditions"
    )
    assert audio.AUDIO_HOSTS[audio.ISLAMIC_NETWORK]["cors"] is False
