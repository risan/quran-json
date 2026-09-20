"""Transliteration candidate registry and fail-closed import tests."""

from __future__ import annotations

import hashlib

import pytest

from quranjson import config, transliterations

SMALL_COUNTS = {1: 2, 2: 1}


def test_registry_covers_requested_candidates_without_duplicate_mirrors() -> None:
    ids = {item.id for item in transliterations.CANDIDATES}
    assert {
        "ara-kemenag-latin",
        "ara-quran-la",
        "ara-tanzil-tr-muhammet-abay",
        "ara-qul-en-wbw-71",
        "ara-qul-en-tajweed-469",
        "ara-qul-en-syllables-475",
        "ara-qul-en-rtf-updated-478",
        "ara-qul-en-72",
        "ara-qul-tr-468",
    } <= ids

    dedupe_candidates = {
        item.id: item.dedupe_candidate_of
        for item in transliterations.CANDIDATES
        if item.dedupe_candidate_of
    }
    assert dedupe_candidates == {
        "ara-qul-en-72": "ara-quran-la",
        "ara-qul-tr-468": "ara-tanzil-tr-muhammet-abay",
    }
    assert all(item.alias_of is None for item in transliterations.CANDIDATES)
    assert all(
        item.reading["riwayah"] == "unknown"
        for item in transliterations.CANDIDATES
        if item.id.startswith("ara-qul-")
    )
    assert all(not item.can_publish for item in transliterations.CANDIDATES)
    assert transliterations.published_candidates() == ()


def test_existing_kemenag_snapshot_is_reused_and_complete() -> None:
    imported = transliterations.import_file("ara-kemenag-latin")

    assert imported.candidate.snapshot_path == config.kemenag_path()
    assert imported.granularity == "ayah"
    assert len(imported.records) == 6236
    assert imported.records[0] == {
        "chapter": 1,
        "verse": 1,
        "text": "Bismillāhir-raḥmānir-raḥīm(i).",
    }
    assert imported.sha256 == hashlib.sha256(config.kemenag_path().read_bytes()).hexdigest()


def test_existing_tanzil_english_snapshot_is_not_copied() -> None:
    imported = transliterations.import_file("ara-quran-la")

    assert imported.candidate.snapshot_path == config.edition_path(config.TRANSLITERATION)
    assert len(imported.records) == 6236
    assert imported.records[0]["text"] == "Bismi Allahi alrrahmani alrraheemi"


def test_tanzil_pipe_preserves_unicode_and_whitespace() -> None:
    raw = "# footer\n1|1|  Çeviriyaz\u0131  \n1|2|düz\n2|1|son\n".encode()

    records = transliterations.parse_tanzil_pipe(raw, chapter_counts=SMALL_COUNTS)

    assert records[0]["text"] == "  Çeviriyaz\u0131  "
    assert records[-1] == {"chapter": 2, "verse": 1, "text": "son"}


def test_ayah_validation_rejects_missing_duplicate_or_out_of_order_rows() -> None:
    good = [
        {"chapter": 1, "verse": 1, "text": "one"},
        {"chapter": 1, "verse": 2, "text": "two"},
        {"chapter": 2, "verse": 1, "text": "three"},
    ]
    assert transliterations.validate_ayah_records(good, chapter_counts=SMALL_COUNTS) == tuple(good)

    for bad in (
        good[:-1],
        [good[0], good[0], good[2]],
        [good[1], good[0], good[2]],
    ):
        with pytest.raises(transliterations.TransliterationImportError):
            transliterations.validate_ayah_records(bad, chapter_counts=SMALL_COUNTS)


def test_qul_ayah_json_preserves_markup_and_does_not_normalize_text() -> None:
    payload = {"1:1": "Bismi <b>a</b>l<u>lā</u>hi", "1:2": "Praise", "2:1": "Three"}

    records = transliterations.parse_qul_ayah_json(payload, chapter_counts=SMALL_COUNTS)

    assert records[0]["text"] == "Bismi <b>a</b>l<u>lā</u>hi"


def test_rich_markup_allowlist_rejects_unreviewed_tags_without_rewriting() -> None:
    records = ({"chapter": 1, "verse": 1, "text": "a<i>b</i>"},)
    assert transliterations.validate_markup(records, allowed_tags=("b", "u", "i")) == records

    with pytest.raises(transliterations.TransliterationImportError, match="allowlist"):
        transliterations.validate_markup(
            ({"chapter": 1, "verse": 1, "text": "a<script>b</script>"},),
            allowed_tags=("b", "u", "i"),
        )

    for text in ("a<b class='unsafe'>b</b>", "a<b>b", "a<b>one</i>", "a<!--comment-->"):
        with pytest.raises(transliterations.TransliterationImportError):
            transliterations.validate_markup(
                ({"chapter": 1, "verse": 1, "text": text},),
                allowed_tags=("b", "u", "i"),
            )


def test_qul_word_json_preserves_word_identity_without_ayah_concatenation() -> None:
    payload = {
        "1:1:1": "one",
        "1:1:2": "two",
        "1:2:1": "three",
        "2:1:1": "four",
    }

    records = transliterations.parse_qul_word_json(payload, chapter_counts=SMALL_COUNTS)

    assert records == (
        {"chapter": 1, "verse": 1, "word": 1, "text": "one"},
        {"chapter": 1, "verse": 1, "word": 2, "text": "two"},
        {"chapter": 1, "verse": 2, "word": 1, "text": "three"},
        {"chapter": 2, "verse": 1, "word": 1, "text": "four"},
    )


def test_word_validation_rejects_gaps_and_missing_ayahs() -> None:
    with pytest.raises(transliterations.TransliterationImportError, match="sequential"):
        transliterations.validate_word_records(
            [
                {"chapter": 1, "verse": 1, "word": 1, "text": "one"},
                {"chapter": 1, "verse": 1, "word": 3, "text": "three"},
                {"chapter": 1, "verse": 2, "word": 1, "text": "two"},
                {"chapter": 2, "verse": 1, "word": 1, "text": "four"},
            ],
            chapter_counts=SMALL_COUNTS,
        )

    with pytest.raises(transliterations.TransliterationImportError, match="no rows for ayah"):
        transliterations.validate_word_records(
            [{"chapter": 1, "verse": 1, "word": 1, "text": "one"}],
            chapter_counts=SMALL_COUNTS,
        )

    with pytest.raises(transliterations.TransliterationImportError, match="start at 1"):
        transliterations.validate_word_records(
            [
                {"chapter": 1, "verse": 1, "word": 2, "text": "two"},
                {"chapter": 1, "verse": 2, "word": 1, "text": "three"},
                {"chapter": 2, "verse": 1, "word": 1, "text": "four"},
            ],
            chapter_counts=SMALL_COUNTS,
        )

    with pytest.raises(transliterations.TransliterationImportError, match="restart at 1"):
        transliterations.validate_word_records(
            [
                {"chapter": 1, "verse": 1, "word": 1, "text": "one"},
                {"chapter": 1, "verse": 1, "word": 2, "text": "two"},
                {"chapter": 1, "verse": 2, "word": 2, "text": "bad"},
                {"chapter": 2, "verse": 1, "word": 1, "text": "four"},
            ],
            chapter_counts=SMALL_COUNTS,
        )

    with pytest.raises(transliterations.TransliterationImportError, match="keyed JSON"):
        transliterations.parse_qul_word_json(
            [{"chapter": 1, "verse": 1, "word": 1, "text": "one"}],
            chapter_counts=SMALL_COUNTS,
        )


def test_manual_candidates_fail_closed_without_a_user_supplied_export() -> None:
    with pytest.raises(transliterations.TransliterationImportError, match="official local export"):
        transliterations.import_file("ara-qul-en-tajweed-469")

    with pytest.raises(transliterations.TransliterationImportError, match="official local export"):
        transliterations.import_file("ara-tanzil-tr-muhammet-abay")


def test_dedupe_candidates_wait_for_a_complete_official_export() -> None:
    with pytest.raises(transliterations.TransliterationImportError, match="official local export"):
        transliterations.import_file("ara-qul-en-72")


def test_dedupe_candidates_use_keyed_ayah_validation_for_local_exports(tmp_path) -> None:
    source = tmp_path / "candidate.json"
    source.write_text("{}", encoding="utf-8")

    for candidate_id in ("ara-qul-en-72", "ara-qul-tr-468"):
        with pytest.raises(
            transliterations.TransliterationImportError,
            match="ayah import is truncated at 1:1",
        ):
            transliterations.import_file(candidate_id, source)
