"""Unit tests for the snapshot reshape, parsing, and drift-detection logic."""

from __future__ import annotations

import io
import sqlite3
import zipfile

import pytest

from quranjson import config, quranenc, tanzil
from quranjson.clearquran import parse_verse_files
from quranjson.jsonio import read_json
from quranjson.sources import _chapter_list, _group_by_chapter, _summarise_change


def test_chapter_list_reshape_drops_unused_api_fields() -> None:
    payload = {
        "chapters": [
            {
                "id": 1,
                "name_arabic": "\u0627\u0644\u0641\u0627\u062a\u062d\u0629",
                "name_simple": "Al-Fatihah",
                "translated_name": {"name": "The Opener", "language_name": "english"},
                "revelation_place": "makkah",
                "verses_count": 7,
                "bismillah_pre": False,
                "pages": [1, 1],
            }
        ]
    }

    assert _chapter_list(payload) == [
        {
            "id": 1,
            "name": "\u0627\u0644\u0641\u0627\u062a\u062d\u0629",
            "transliteration": "Al-Fatihah",
            "translation": "The Opener",
            "type": "meccan",
            "total_verses": 7,
        }
    ]


def test_verse_grouping_preserves_chapter_and_verse_order() -> None:
    payload = {
        "quran": [
            {"chapter": 1, "verse": 1, "text": "a"},
            {"chapter": 1, "verse": 2, "text": "b"},
            {"chapter": 2, "verse": 1, "text": "c"},
        ]
    }

    assert _group_by_chapter(payload) == {
        "1": [
            {"chapter": 1, "verse": 1, "text": "a"},
            {"chapter": 1, "verse": 2, "text": "b"},
        ],
        "2": [{"chapter": 2, "verse": 1, "text": "c"}],
    }


def test_identical_snapshot_reports_no_drift() -> None:
    snapshot = {"1": [{"chapter": 1, "verse": 1, "text": "x"}]}

    summary = _summarise_change(snapshot, snapshot)

    assert summary["changed"] == 0
    assert summary["records"] == 1
    assert "codepoint_delta" not in summary


def test_changed_verse_is_counted_with_its_codepoint_delta() -> None:
    """Mirrors the real drift: upstream swapped Yeh for Farsi Yeh."""
    before = {"1": [{"chapter": 1, "verse": 1, "text": "\u064a\u064e"}]}
    after = {"1": [{"chapter": 1, "verse": 1, "text": "\u06cc\u064e"}]}

    summary = _summarise_change(before, after)

    assert summary["changed"] == 1
    assert summary["records"] == 1
    assert any("U+06CC" in entry for entry in summary["codepoint_delta"]["added"])
    assert any("U+064A" in entry for entry in summary["codepoint_delta"]["removed"])


def test_codepoint_delta_only_reports_characters_that_appeared_or_vanished() -> None:
    """A character that merely occurs fewer times is not a re-encoding."""
    before = {"1": [{"verse": 1, "text": "\u0628\u064e\u0644\u064e\u0645"}]}
    after = {"1": [{"verse": 1, "text": "\u0628\u064e\u0644\u0645"}]}

    summary = _summarise_change(before, after)

    assert summary["changed"] == 1
    assert summary["codepoint_delta"]["added"] == []
    assert summary["codepoint_delta"]["removed"] == []


def test_shrinking_snapshot_is_reported_as_drift() -> None:
    before = {"1": [{"verse": 1}, {"verse": 2}, {"verse": 3}]}
    after = {"1": [{"verse": 1}, {"verse": 2}]}

    summary = _summarise_change(before, after)

    assert summary["changed"] == 1
    assert summary["records"] == 3


def test_added_chapter_is_reported_as_drift() -> None:
    before = {"1": [{"verse": 1}]}
    after = {"1": [{"verse": 1}], "2": [{"verse": 1}, {"verse": 2}]}

    assert _summarise_change(before, after)["changed"] == 2


def test_chapter_list_drift_is_counted() -> None:
    before = [{"id": 1, "translation": "a"}, {"id": 2, "translation": "b"}]
    after = [{"id": 1, "translation": "a"}, {"id": 2, "translation": "c"}]

    assert _summarise_change(before, after) == {
        "kind": "records",
        "records": 2,
        "changed": 1,
    }


# --- Tanzil -------------------------------------------------------------------


def test_tanzil_text_parser_skips_the_licence_banner() -> None:
    raw = (
        b"# Quran text\n"
        b"#  Please check updates at: http://tanzil.net/updates/\n"
        b"1|1|\xd8\xa8\xd8\xb3\xd9\x85\n"
        b"1|2|\xd8\xa7\xd9\x84\xd8\xad\xd9\x85\xd8\xaf\n"
        b"2|1|\xd8\xa7\xd9\x84\xd9\x85\n"
    )

    assert tanzil.parse_text(raw) == {
        "1": [
            {"chapter": 1, "verse": 1, "text": "\u0628\u0633\u0645"},
            {"chapter": 1, "verse": 2, "text": "\u0627\u0644\u062d\u0645\u062f"},
        ],
        "2": [{"chapter": 2, "verse": 1, "text": "\u0627\u0644\u0645"}],
    }


def test_tanzil_text_parser_rejects_a_malformed_line() -> None:
    with pytest.raises(ValueError):
        tanzil.parse_text(b"1|1|ok\nnot a verse line\n")


def test_tanzil_metadata_parser_normalises_the_revelation_place() -> None:
    raw = (
        b'<?xml version="1.0" encoding="utf-8" ?>\n'
        b'<quran type="metadata">'
        b"<suras>"
        b'<sura index="1" ayas="7" start="0" name="x" tname="Al-Faatiha" '
        b'ename="The Opening" type="Meccan" order="5" rukus="1" />'
        b'<sura index="2" ayas="286" start="7" name="y" tname="Al-Baqara" '
        b'ename="The Cow" type="Medinan" order="87" rukus="40" />'
        b"</suras>"
        b'<sajdas><sajda index="1" sura="7" aya="206" type="recommended" /></sajdas>'
        b"</quran>"
    )

    parsed = tanzil.parse_metadata(raw)

    assert parsed["chapters"][0] == {
        "id": 1,
        "name": "x",
        "transliteration": "Al-Faatiha",
        "translation": "The Opening",
        "type": "meccan",
        "total_verses": 7,
    }
    assert parsed["chapters"][1]["type"] == "medinan"
    assert parsed["indexes"]["sajdas"] == [
        {"index": 1, "sura": 7, "aya": 206, "type": "recommended"}
    ]


def test_tanzil_rejects_an_unknown_variant() -> None:
    with pytest.raises(ValueError):
        tanzil.text_url("not-a-variant")


# --- QuranEnc -----------------------------------------------------------------


def _sqlite_archive(rows: list[tuple[int, int, str, str]]) -> bytes:
    """Build the same zip-of-sqlite shape QuranEnc serves."""
    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE translations (id INTEGER PRIMARY KEY, sura INTEGER, aya INTEGER, "
        "translation TEXT, footnotes TEXT)"
    )
    connection.executemany(
        "INSERT INTO translations (sura, aya, translation, footnotes) VALUES (?, ?, ?, ?)",
        rows,
    )
    connection.commit()
    payload = connection.serialize()
    connection.close()

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("translation.sqlite", payload)
    return buffer.getvalue()


def test_quranenc_catalogue_reshape_keeps_version_and_database_url() -> None:
    raw = (
        b'{"translations":[{"key":"english_rwwad","language_iso_code":"en",'
        b'"direction":"ltr","version":"1.0.19","title":"Rowwad",'
        b'"description":"d","database_url":"https://quranenc.com/x.zip",'
        b'"pdf_url":"https://quranenc.com/x.pdf","pdf_size":1}]}'
    )

    assert quranenc.parse_catalogue(raw) == {
        "translations": [
            {
                "key": "english_rwwad",
                "lang": "en",
                "direction": "ltr",
                "version": "1.0.19",
                "title": "Rowwad",
                "description": "d",
                "database_url": "https://quranenc.com/x.zip",
            }
        ]
    }


def test_quranenc_translation_is_extracted_and_grouped_by_chapter() -> None:
    archive = _sqlite_archive(
        [
            (1, 1, "In the name of Allah", "fn"),
            (1, 2, "Praise be to Allah", ""),
            (2, 1, "Alif Lam Meem", ""),
        ]
    )

    verses = quranenc.parse_translation(archive)

    assert verses["1"][0] == {
        "chapter": 1,
        "verse": 1,
        "text": "In the name of Allah",
        "footnotes": "fn",
    }
    # An empty footnotes column must not add a key.
    assert "footnotes" not in verses["1"][1]
    assert verses["2"] == [{"chapter": 2, "verse": 1, "text": "Alif Lam Meem"}]


def test_quranenc_translation_rejects_a_non_sqlite_archive() -> None:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("readme.txt", "not a database")

    with pytest.raises(ValueError, match=r"no \.sqlite member"):
        quranenc.parse_translation(buffer.getvalue())


# --- ClearQuran (Talal Itani) -------------------------------------------------


def _clearquran_archive(verses: dict[tuple[int, int], str], *, with_basmala: bool = True) -> bytes:
    """Build the per-verse zip clearquran.com serves: one SSS-AAA.txt per verse."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("_readme.txt", "Translated by Talal Itani")
        for (chapter, verse), text in verses.items():
            archive.writestr(f"{chapter:03d}-{verse:03d}.txt", text)
        if with_basmala:
            for chapter in range(2, 115):
                if chapter != 9:  # At-Tawbah has no basmala
                    archive.writestr(f"{chapter:03d}-000.txt", "In the name of God")
    return buffer.getvalue()


def _complete_verses() -> dict[tuple[int, int], str]:
    """Every ayah of the Quran, with a distinctive marker text."""
    chapters = read_json(config.tanzil_chapters_path())["chapters"]
    return {
        (chapter["id"], verse): f"verse {chapter['id']}:{verse}"
        for chapter in chapters
        for verse in range(1, chapter["total_verses"] + 1)
    }


def test_clearquran_parser_skips_the_basmala_pseudo_verse() -> None:
    """112 chapters ship an SSS-000.txt holding the basmala; it is not an ayah."""
    verses = _complete_verses()
    verses[(1, 1)] = "In the name of God, the Gracious, the Merciful."

    parsed = parse_verse_files(_clearquran_archive(verses))

    assert len(parsed) == 114
    assert sum(len(items) for items in parsed.values()) == 6236
    assert parsed["1"][0] == {
        "chapter": 1,
        "verse": 1,
        "text": "In the name of God, the Gracious, the Merciful.",
    }


def test_clearquran_parser_collapses_wrapped_lines() -> None:
    verses = _complete_verses()
    verses[(1, 1)] = "In the name of God,\nthe Gracious,\n   the Merciful."

    parsed = parse_verse_files(_clearquran_archive(verses))

    assert parsed["1"][0]["text"] == "In the name of God, the Gracious, the Merciful."


def test_clearquran_parser_rejects_a_truncated_archive() -> None:
    """A partial translation must never be committed silently."""
    verses = _complete_verses()
    del verses[(114, 6)]

    with pytest.raises(ValueError, match="verses"):
        parse_verse_files(_clearquran_archive(verses))


def test_clearquran_parser_rejects_a_missing_chapter() -> None:
    verses = {k: v for k, v in _complete_verses().items() if k[0] != 114}

    with pytest.raises(ValueError, match="chapters"):
        parse_verse_files(_clearquran_archive(verses))


def test_clearquran_parser_rejects_empty_verse_text() -> None:
    verses = _complete_verses()
    verses[(1, 1)] = "   "

    with pytest.raises(ValueError, match="empty verse"):
        parse_verse_files(_clearquran_archive(verses))
