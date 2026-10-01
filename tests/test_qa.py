"""Transcription-defect restoration: the correction table must not silently rot."""

from __future__ import annotations

from pathlib import Path

import pytest

from quranjson import config, jsonio, qa


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


def _kemenag_corrections() -> list[qa.Correction]:
    return [item for item in qa.known() if item.lang == config.KEMENAG_SCRIPT]


def test_kemenag_spacing_corrections_change_only_spaces() -> None:
    corrections = _kemenag_corrections()

    assert len(corrections) == len(qa.KEMENAG_SPACING) == 33
    assert {(item.chapter, item.verse) for item in corrections} >= {(8, 67), (38, 19), (40, 53)}
    for item in corrections:
        assert item.kind == "script"
        assert item.defective.replace(" ", "") == item.restored.replace(" ", ""), item.key()
        assert item.defective != item.restored


def test_kemenag_spacing_never_touches_a_joining_letter() -> None:
    """The invariant that makes these safe: no rasm can change at a non-connecting letter."""
    non_joining = set("اأإآٱدذرزو")

    for item in _kemenag_corrections():
        shorter, longer = sorted((item.defective, item.restored), key=len)
        position = next(
            index
            for index, (left, right) in enumerate(zip(shorter, longer, strict=False))
            if left != right
        )
        letters = [char for char in longer[:position] if "ء" <= char <= "ي"]

        assert letters[-1] in non_joining, item.key()


def test_the_committed_kemenag_snapshot_still_has_every_defect() -> None:
    """If LPMQ fixes a slip upstream the correction must be retired, not silently kept."""
    snapshot = jsonio.read_json(config.kemenag_path())

    for item in _kemenag_corrections():
        text = next(v["text"] for v in snapshot[str(item.chapter)] if v["verse"] == item.verse)

        assert text.count(item.defective) == 1, item.key()


def test_kemenag_corrections_are_applied_to_the_published_text(cdn_tree: Path) -> None:
    for item in _kemenag_corrections():
        chapter = jsonio.read_json(
            cdn_tree / "text" / "kemenag" / "chapters" / f"{item.chapter}.json"
        )
        text = next(v["text"] for v in chapter["verses"] if v["id"] == item.verse)

        assert item.restored in text, item.key()
        assert item.defective not in text, item.key()


def test_kemenag_defect_already_fixed_upstream_fails_the_build() -> None:
    snapshot = jsonio.read_json(config.kemenag_path())
    item = _kemenag_corrections()[0]
    verse = next(v for v in snapshot[str(item.chapter)] if v["verse"] == item.verse)
    verse["text"] = verse["text"].replace(item.defective, item.restored)

    with pytest.raises(ValueError, match="defective fragment absent"):
        qa.apply_corrections(config.KEMENAG_SCRIPT, snapshot)


def test_qa_manifest_marks_script_corrections() -> None:
    entries = qa.manifest()["corrections"]

    assert {entry["kind"] for entry in entries} == {"translation", "script"}
