"""Provenance: every published byte traces back to a licensed, hashed upstream snapshot."""

from __future__ import annotations

from quranjson import config, sources
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
