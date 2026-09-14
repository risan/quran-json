"""Transcription-defect restoration: the correction table must not silently rot."""

from __future__ import annotations

import pytest

from quranjson import qa


def test_recorded_correction_restores_the_duplicated_fragment() -> None:
    """The Yusuf Ali defect is repaired exactly once, leaving the rest untouched."""
    defective = "a game well within reach of game well within reach of your hands"
    grouped = {"5": [{"verse": 94, "text": defective}]}

    result = qa.apply_corrections("english_yusuf_ali", grouped)

    assert result["5"][0]["text"] == "a game well within reach of your hands"


def test_sibling_verses_and_other_editions_are_left_alone() -> None:
    """Corrections are scoped: no carry-over to a sibling verse or another edition."""
    grouped = {
        "5": [
            {"verse": 93, "text": "sibling untouched"},
            {"verse": 94, "text": "x game well within reach of game well within reach of y"},
        ]
    }
    result = qa.apply_corrections("english_yusuf_ali", grouped)

    assert result["5"][0]["text"] == "sibling untouched"
    assert result["5"][1]["text"] == "x game well within reach of y"

    duplicated = "x game well within reach of game well within reach of y"
    other = {"5": [{"verse": 94, "text": duplicated}]}
    assert qa.apply_corrections("english_pickthall", other)["5"][0]["text"] == duplicated


def test_upstream_change_fails_loudly_instead_of_double_correcting() -> None:
    """If upstream repairs the text, the stale patch must not be applied blindly."""
    grouped = {"5": [{"verse": 94, "text": "already clean text"}]}

    with pytest.raises(ValueError, match="defective fragment absent"):
        qa.apply_corrections("english_yusuf_ali", grouped)


def test_missing_target_raises() -> None:
    """A correction pointing at a vanished verse or chapter is an error, not a no-op."""
    with pytest.raises(KeyError):
        qa.apply_corrections("english_yusuf_ali", {"5": [{"verse": 1, "text": "x"}]})
    with pytest.raises(KeyError):
        qa.apply_corrections("english_yusuf_ali", {})


def test_manifest_cites_evidence_for_every_correction() -> None:
    """Each published correction carries a witness URL, so the claim is auditable."""
    manifest = qa.manifest()

    assert manifest["corrections"], "the correction table must not be empty"
    for entry in manifest["corrections"]:
        assert entry["evidence"].startswith("http")
