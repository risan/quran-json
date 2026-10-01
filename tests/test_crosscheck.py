"""Offline tests for the cross-check tool: mutated verses must be reported at the right level."""

from __future__ import annotations

import gzip
from pathlib import Path

import httpx
import orjson
import pytest

from quranjson import config, crosscheck
from quranjson.crosscheck import (
    EQUIVALENCES,
    SCRIPTS,
    WITNESSES,
    CrosscheckError,
    Script,
    Witness,
    compare,
    raw_key,
    skeleton_key,
    strip_basmala,
    vocalised_key,
)

#: Al-Fatiha 1:2 in Tanzil's Uthmani encoding.
VERSE = "ٱلْحَمْدُ لِلَّهِ رَبِّ ٱلْعَٰلَمِينَ"
BASMALA = "بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ"


def levels(ours: str, theirs: str) -> tuple[bool, bool, bool]:
    """Whether the two texts agree at the raw, vocalised and skeleton levels."""
    return (
        raw_key(ours) == raw_key(theirs),
        vocalised_key(ours) == vocalised_key(theirs),
        skeleton_key(ours) == skeleton_key(theirs),
    )


def test_identical_text_agrees_everywhere() -> None:
    assert levels(VERSE, VERSE) == (True, True, True)


def test_changed_vowel_is_vocalised_only() -> None:
    mutated = VERSE.replace("ُ", "ِ", 1)

    assert mutated != VERSE
    assert levels(VERSE, mutated) == (False, False, True)


def test_changed_hamza_seat_is_vocalised_but_folds_in_the_skeleton() -> None:
    ours = "أَنْعَمْتَ عَلَيْهِمْ"
    bare_hamza = "ءَنْعَمْتَ عَلَيْهِمْ"

    assert levels(ours, bare_hamza) == (False, False, True)


def test_hamza_on_waw_folds_to_waw_in_the_skeleton() -> None:
    assert levels("مُؤْمِنِينَ", "مُومِنِينَ") == (
        False,
        False,
        True,
    )


def test_dropped_letter_is_reported_at_every_level_but_raw_is_also_different() -> None:
    mutated = VERSE.replace("ح", "", 1)

    assert levels(VERSE, mutated) == (False, False, False)


def test_dropped_word_is_reported_in_the_skeleton() -> None:
    mutated = VERSE.rsplit(" ", 1)[0]

    assert levels(VERSE, mutated) == (False, False, False)


def test_dropped_alef_is_invisible_in_the_skeleton_but_not_vocalised() -> None:
    ours = "قَالُوا"
    mutated = "قَالُو"

    assert levels(ours, mutated) == (False, False, True)


@pytest.mark.parametrize("row", EQUIVALENCES, ids=lambda row: row.name[:40])
def test_listed_encoding_differences_are_not_reported_as_vocalised(
    row: crosscheck.Equivalence,
) -> None:
    ours, theirs = row.example
    raw_same, vocalised_same, skeleton_same = levels(ours, theirs)

    assert not raw_same
    assert vocalised_same
    assert skeleton_same


def test_tanween_marks_stay_distinct_from_each_other() -> None:
    assert vocalised_key("مً") != vocalised_key("مٌ")


@pytest.mark.parametrize(
    ("ours", "lost"),
    [
        ("كِتَابٌ هُوَ", "كِتَابُ هُوَ"),
        ("غَفُورٌ رَّحِيمٌ", "غَفُورُ رَّحِيمٌ"),
        ("يَوْمًا عَظِيمًا", "يَوْمَا عَظِيمًا"),
        ("مَاءٍ دَافِقٍ", "مَاءِ دَافِقٍ"),
    ],
)
def test_a_lost_tanween_is_reported_at_the_vocalised_level(ours: str, lost: str) -> None:
    assert levels(ours, lost) == (False, False, True)


def test_tanween_is_folded_only_where_the_word_carries_an_iqlab_meem() -> None:
    tanzil = "عَذَابٌ أَلِيمٌۢ بِمَا"
    kfgqpc = "عَذَابٌ أَلِيمُۢ بِمَا"
    lost_elsewhere = "عَذَابُ أَلِيمُۢ بِمَا"

    assert levels(tanzil, kfgqpc) == (False, True, True)
    assert levels(tanzil, lost_elsewhere) == (False, False, True)


def test_alef_wasla_is_not_folded_into_plain_alef_at_the_vocalised_level() -> None:
    assert levels("ٱلْحَمْدُ", "الْحَمْدُ") == (
        False,
        False,
        True,
    )


def test_tatweel_hair_space_and_word_joiner_are_ignored_below_raw() -> None:
    kerned = VERSE.replace("ٰ", "\u200aٰ\u2060")

    assert levels(VERSE, kerned) == (False, True, True)


def test_strip_basmala_ignores_marks_spacing_and_alef_spelling() -> None:
    assert strip_basmala(BASMALA + " الٓمٓ") == "الٓمٓ"
    assert strip_basmala("بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيْمِ ذٰلِكَ") == "ذٰلِكَ"
    assert strip_basmala(VERSE) == VERSE


# --- compare() ------------------------------------------------------------------------


def _script(**changes: object) -> Script:
    values: dict[str, object] = {
        "id": "t",
        "path": lambda: Path("unused"),
        "witnesses": ("w",),
    }
    values.update(changes)

    return Script(**values)  # type: ignore[arg-type]


def _witness(**changes: object) -> Witness:
    values: dict[str, object] = {
        "id": "w",
        "label": "test witness",
        "urls": (),
        "parse": lambda raws: {},
        "ancestry": "test",
    }
    values.update(changes)

    return Witness(**values)  # type: ignore[arg-type]


def test_compare_counts_each_mutation_at_the_right_level() -> None:
    ours = {
        (1, 2): VERSE,
        (2, 5): "قَالَ رَبُّهُ",
        (2, 6): "مُؤْمِنِينَ",
        (2, 7): "ٱلْحَمْدُ لِلَّهِ رَبِّ",
        (2, 8): "ٱلْحَمْدُ لِلَّهِ رَبِّ",
    }
    theirs = {
        (1, 2): VERSE,
        (2, 5): "قَالَ رَبِّهُ",  # vowel
        (2, 6): "مُومِنِينَ",  # hamza seat
        (2, 7): "ٱلْحَمْدُ لِلَّهِ",  # dropped word
        (2, 8): "ٱلْحَمْدُ لِلَّهِ رَبِّ",
    }

    report = compare(_script(), ours, theirs, _witness())

    assert report.unit == "verse"
    assert report.total == 5
    assert report.raw_same == 2
    assert report.vocalised_same == 2
    assert report.skeleton_same == 4
    assert {residual.key for residual in report.residuals} == {"2:5", "2:6", "2:7"}


def test_compare_ignores_the_basmala_prefix_of_verse_one_after_the_first_chapter() -> None:
    ours = {(1, 1): BASMALA, (2, 1): BASMALA + " الٓمٓ"}
    theirs = {(1, 1): BASMALA, (2, 1): "الٓمٓ"}

    report = compare(_script(), ours, theirs, _witness())

    assert report.vocalised_same == 2
    assert report.skeleton_same == 2


def test_compare_reports_a_basmala_that_is_missing_from_the_first_chapter() -> None:
    report = compare(_script(), {(1, 1): BASMALA}, {(1, 1): "ٱلْحَمْدُ"}, _witness())

    assert report.skeleton_same == 0


def test_compare_skips_the_vocalised_level_for_an_unvocalised_script() -> None:
    ours = {(1, 2): "الحمد لله رب العالمين"}
    theirs = {(1, 2): VERSE}

    report = compare(_script(vocalised=False), ours, theirs, _witness())

    assert report.vocalised_same is None
    assert report.skeleton_same == 1
    assert report.residuals == []


def test_compare_counts_a_word_boundary_difference_as_spacing_only() -> None:
    ours = {(15, 7): "لَوْ مَا تَأْتِينَا"}
    theirs = {(15, 7): "لَوْمَا تَأْتِينَا"}

    report = compare(_script(), ours, theirs, _witness())

    assert report.vocalised_same == 1
    assert report.spacing_only == 1


def test_compare_uses_chapters_when_a_riwayah_has_its_own_verse_numbers() -> None:
    ours = {
        (2, 1): "وَقَالَ رَبُّكَ",
        (2, 2): "ٱلْحَمْدُ لِلَّهِ",
    }
    theirs = {
        (2, 1): "وَقَالَ رَبُّكَ ٱلْحَمْدُ",
        (2, 2): "لِلَّهِ",
    }

    report = compare(_script(numbering="own"), ours, theirs, _witness())

    assert report.unit == "chapter"
    assert (report.total, report.vocalised_same, report.skeleton_same) == (1, 1, 1)
    assert report.chapters_skeleton_same == report.chapters_total == 1


def test_compare_reports_a_dropped_word_in_a_chapter_compared_as_a_whole() -> None:
    ours = {
        (2, 1): "وَقَالَ رَبُّكَ",
        (2, 2): "ٱلْحَمْدُ لِلَّهِ",
    }
    theirs = {(2, 1): "وَقَالَ رَبُّكَ ٱلْحَمْدُ"}

    report = compare(_script(numbering="own"), ours, theirs, _witness())

    assert report.skeleton_same == 0
    assert report.chapters_skeleton_same == 0
    assert [(r.key, r.ours, r.theirs) for r in report.residuals] == [("chapter 2", "لِلَّهِ", "")]


def test_compare_leaves_shifted_chapters_to_the_chapter_level() -> None:
    ours = {
        (1, 1): "ٱلْحَمْدُ لِلَّهِ",
        (1, 2): "ٱلرَّحْمَٰنِ",
        (2, 1): "الٓمٓ",
    }
    theirs = {
        (1, 1): BASMALA,
        (1, 2): "ٱلْحَمْدُ لِلَّهِ",
        (1, 3): "ٱلرَّحْمَٰنِ",
        (2, 1): "الٓمٓ",
    }

    report = compare(_script(shifted_chapters=frozenset({1})), ours, theirs, _witness())

    assert report.total == 1
    assert report.chapters_skeleton_same == report.chapters_total == 2


# --- registry ---------------------------------------------------------------------------


def test_every_script_witness_exists_and_states_its_ancestry() -> None:
    for script in SCRIPTS.values():
        assert script.witnesses
        for witness_id in script.witnesses:
            assert WITNESSES[witness_id].ancestry


def test_every_published_script_is_registered_for_crosscheck() -> None:
    assert set(config.SCRIPT_IDS) <= set(SCRIPTS)


def test_riwayat_scripts_use_their_own_numbering() -> None:
    assert {SCRIPTS[name].numbering for name in ("warsh", "qalun", "duri")} == {"own"}
    assert {SCRIPTS[name].numbering for name in ("uthmani", "kemenag", "hafs-nastaliq")} == {"hafs"}


def test_every_committed_script_resolves_to_a_snapshot() -> None:
    present = [script for script in SCRIPTS.values() if script.path().exists()]

    assert {script.id for script in present} >= {"uthmani", "kemenag", "warsh", "indopak"}
    for script in present:
        assert crosscheck.load_ours(script)


# --- parsing and fetching ---------------------------------------------------------------


def test_witness_parsers_read_their_formats() -> None:
    faw = orjson.dumps({"quran": [{"chapter": 1, "verse": 2, "text": "a"}]})
    cloud = orjson.dumps(
        {"data": {"surahs": [{"number": 3, "ayahs": [{"numberInSurah": 4, "text": "b"}]}]}}
    )
    pedia = gzip.compress(
        orjson.dumps({"data": {"surahs": [{"id": 5, "ayahs": [{"number": 6, "text": "c"}]}]}})
    )
    scrape = [
        orjson.dumps([{"ayah": 7, "arabic": "d"}]),
        orjson.dumps([{"ayah": 1, "arabic": "e"}]),
    ]

    assert WITNESSES["faw-quranwarsh"].parse([faw]) == {(1, 2): "a"}
    assert WITNESSES["alquran-simple"].parse([cloud]) == {(3, 4): "b"}
    assert WITNESSES["qp-1"].parse([pedia]) == {(5, 6): "c"}
    assert WITNESSES["kemenag-2025-scrape"].parse(scrape) == {(1, 7): "d", (2, 1): "e"}


def test_fetch_caches_downloads_and_names_the_witness_on_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    witness = _witness(
        urls=("https://example.invalid/a.json",),
        parse=lambda raws: {(1, 1): raws[0].decode()},
    )
    calls: list[str] = []

    def download(url: str, *, verify: bool) -> bytes:
        calls.append(url)

        return b"text"

    monkeypatch.setattr(crosscheck, "_download", download)

    assert crosscheck.fetch(witness, tmp_path) == {(1, 1): "text"}
    assert crosscheck.fetch(witness, tmp_path) == {(1, 1): "text"}
    assert len(calls) == 1

    crosscheck.fetch(witness, tmp_path, refresh=True)
    assert len(calls) == 2


def test_fetch_reports_a_network_failure_with_the_witness_and_url(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def download(url: str, *, verify: bool) -> bytes:
        raise httpx.ConnectError("no route")

    monkeypatch.setattr(crosscheck, "_download", download)
    witness = _witness(urls=("https://example.invalid/a.json",))

    with pytest.raises(CrosscheckError, match=r"w: cannot download https://example.invalid/a.json"):
        crosscheck.fetch(witness, tmp_path)


def test_fetch_reports_an_unparseable_download(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(crosscheck, "_download", lambda url, *, verify: b"not json")
    witness = _witness(urls=("https://example.invalid/a.json",), parse=lambda raws: {})

    with pytest.raises(CrosscheckError, match="holds no verses"):
        crosscheck.fetch(witness, tmp_path)


# --- run() ------------------------------------------------------------------------------


def test_run_prints_the_table_and_writes_the_residual_tsv(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = _script(path=lambda: tmp_path / "ours.json")
    (tmp_path / "ours.json").write_bytes(
        orjson.dumps(
            {
                "2": [
                    {
                        "chapter": 2,
                        "verse": 5,
                        "text": "قَالَ رَبُّهُ",
                    }
                ]
            },
        )
    )
    witness = _witness(urls=("https://example.invalid/a.json",))
    monkeypatch.setitem(SCRIPTS, "t", script)
    monkeypatch.setitem(WITNESSES, "w", witness)
    monkeypatch.setattr(
        crosscheck,
        "fetch",
        lambda w, cache_dir, refresh=False: {(2, 5): "قَالَ رَبِّهُ"},
    )
    lines: list[str] = []

    status = crosscheck.run(["t"], cache_dir=tmp_path / "cache", out=lines.append)

    assert status == 0
    assert "## t" in lines[0]
    assert "test witness" in lines[0]
    tsv = (tmp_path / "cache" / "t.tsv").read_text(encoding="utf-8").splitlines()
    assert tsv[0].startswith("key\twitness")
    assert tsv[1] == "2:5\tw\tقَالَ رَبُّهُ\tقَالَ رَبِّهُ"


def test_run_exits_nonzero_when_a_witness_is_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    script = _script(path=lambda: tmp_path / "ours.json")
    (tmp_path / "ours.json").write_bytes(
        orjson.dumps({"2": [{"chapter": 2, "verse": 5, "text": "قَالَ"}]})
    )
    monkeypatch.setitem(SCRIPTS, "t", script)
    monkeypatch.setitem(WITNESSES, "w", _witness())

    def unavailable(
        w: Witness, cache_dir: Path, refresh: bool = False
    ) -> dict[tuple[int, int], str]:
        raise CrosscheckError("w: cannot download x: down")

    monkeypatch.setattr(crosscheck, "fetch", unavailable)
    lines: list[str] = []

    assert crosscheck.run(["t"], cache_dir=tmp_path / "cache", out=lines.append) == 1
    assert any("witness unavailable" in line for line in lines)


def test_run_skips_a_script_without_a_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setitem(SCRIPTS, "t", _script(path=lambda: tmp_path / "missing.json"))
    lines: list[str] = []

    assert crosscheck.run(["t"], cache_dir=tmp_path, out=lines.append) == 0
    assert "skipped" in lines[0]
