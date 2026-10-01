"""Provenance: every published byte traces back to a licensed, hashed upstream snapshot."""

from __future__ import annotations

from pathlib import Path

from quranjson import config, quranpedia, sources
from quranjson.jsonio import read_json


def _manifest() -> list[dict[str, object]]:
    return read_json(config.DATA / "meta" / "sources.json")


def test_every_snapshot_has_a_manifest_record() -> None:
    expected = {task.rel for task in sources.tasks()}
    recorded = {record["path"] for record in _manifest()}

    assert recorded == expected


def test_manifest_hashes_match_the_committed_snapshots() -> None:
    assert sources.verify_snapshots() == []


def test_every_snapshot_declares_a_license_and_source() -> None:
    for record in _manifest():
        assert record["license"], record["path"]
        assert record["source"], record["path"]
        assert str(record["url"]).startswith("https://"), record["path"]
        assert record["bytes"] == (config.ROOT / str(record["path"])).stat().st_size
        assert len(str(record["sha256"])) == 64


def test_published_provenance_states_dump_versions_and_hashes(cdn_tree: Path) -> None:
    """Quranpedia's licence requires the dump version wherever its text is republished."""
    sources_doc = read_json(cdn_tree / "meta" / "sources.json")
    manifest = read_json(cdn_tree / "manifest.json")
    by_script = {entry["script"]: entry for entry in sources_doc["text"]["script_licenses"]}
    manifest_by_script = {entry["id"]: entry for entry in manifest["scripts"]}

    for script in config.QURANPEDIA_SCRIPTS:
        expected = quranpedia.DUMP_METADATA[script]["dump_version"]

        assert by_script[script]["version"] == expected
        assert manifest_by_script[script]["license"]["version"] == expected

    for script in config.SCRIPT_IDS:
        assert len(by_script[script]["sha256"]) == 64
        assert by_script[script]["snapshot"].startswith("data/")
        assert by_script[script]["upstream_url"].startswith("https://")

    for edition in sources_doc["editions"]:
        assert len(edition["sha256"]) == 64
        assert edition["snapshot"].startswith("data/")

    assert len(sources_doc["transliteration"]["source_text_provenance"]["sha256"]) == 64
