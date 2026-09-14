"""Provenance: every published byte traces back to a licensed, hashed upstream snapshot."""

from __future__ import annotations

from hashlib import sha256

from quranjson import config, sources
from quranjson.jsonio import read_json

#: The Uthmani text the frozen `dist/` tree was generated from. Pinned so that a
#: refresh which silently re-encodes the text (see drift.json) can never slip through.
FROZEN_TEXT_SHA256 = "bd74e2cefe800e2600baa4a6056d1e83a83c771f6ff525064cb08bdccbf128bf"
FROZEN_TEXT_BYTES = 1_766_131


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


def test_frozen_text_snapshot_is_pinned() -> None:
    body = config.text_path().read_bytes()

    assert sha256(body).hexdigest() == FROZEN_TEXT_SHA256
    assert len(body) == FROZEN_TEXT_BYTES


def test_manifest_records_the_drift_that_was_not_applied() -> None:
    """The text snapshot was deliberately frozen; the refused refresh stays documented."""
    drift = {record["path"]: record for record in read_json(config.DATA / "meta" / "drift.json")}

    assert "data/quran.json" in drift

    text = drift["data/quran.json"]
    assert text["changed"] > 0
    assert text["previous_sha256"] == FROZEN_TEXT_SHA256
    assert text["sha256"] != text["previous_sha256"]

    added = " ".join(text["codepoint_delta"]["added"])
    removed = " ".join(text["codepoint_delta"]["removed"])

    assert "U+06CC" in added, "upstream switched to Farsi Yeh"
    assert "U+064A" in removed, "the standard Arabic Yeh disappeared"
    assert "U+00A0" in added, "non-breaking spaces were introduced"
