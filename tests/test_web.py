"""The bundled Arabic fonts and the coverage gate.

The fonts live in `site/public/fonts/` and are served at `/fonts/`. These tests pin their bytes
and licences, and the coverage measurement that decides whether a script renders or shows
missing-glyph boxes. The measurement is pinned because a font swap is exactly the kind of
change that would otherwise silently degrade one mushaf tradition.

The site's HTML is tested against the assembled tree in `test_site_build.py`.
"""

from __future__ import annotations

import json
import re
from hashlib import sha256
from pathlib import Path

import pytest
from typer.testing import CliRunner

from quranjson import web
from quranjson.__main__ import app
from quranjson.jsonio import read_json


def test_bundled_fonts_match_their_manifest_hashes() -> None:
    """A font is a binary published with the site; its bytes are pinned like any snapshot."""
    for record in read_json(web.FONTS / "sources.json"):
        path = web.FONTS / record["file"]
        assert record["path"] == f"site/public/fonts/{record['file']}", record["id"]
        assert path.is_file(), record["path"]
        assert sha256(path.read_bytes()).hexdigest() == record["sha256"], record["id"]
        assert path.stat().st_size == record["bytes"], record["id"]
        assert str(record["url"]).startswith("https://"), record["id"]


def test_every_font_ships_the_licence_that_grants_it() -> None:
    """OFL requires the licence and copyright notice to travel with the font."""
    for record in read_json(web.FONTS / "sources.json"):
        licence = web.FONTS / record["license_file"]
        assert licence.is_file(), record["license_file"]
        assert "SIL Open Font License" in licence.read_text(encoding="utf-8"), record["id"]
        assert record["license_status"] == "granted", record["id"]


def test_coverage_is_measured_for_every_script_and_font(cdn_tree: Path) -> None:
    """The reader chooses a font per script from this report, so it has to be complete."""
    manifest = read_json(cdn_tree / "manifest.json")
    coverage = web.coverage_from_data(cdn_tree)

    assert set(coverage["scripts"]) == {script["id"] for script in manifest["scripts"]}
    assert coverage["uncovered"] == []
    assert len(coverage["fonts"]) >= 2

    for script, entry in coverage["scripts"].items():
        assert entry["default"] in entry["usable"], script
        assert entry["default"] not in entry["missing"], script
        assert entry["usable"] == [
            font["id"] for font in coverage["fonts"] if font["id"] not in entry["missing"]
        ], script

    for font in coverage["fonts"]:
        assert font["license_url"].startswith("https://"), font["id"]
        assert font["file"].startswith("/fonts/"), font["id"]
        assert font["license_file"].startswith("/fonts/"), font["id"]


def test_the_measured_gaps_are_the_ones_published(cdn_tree: Path) -> None:
    """Amiri is the traditional naskh and also the one with holes: U+089C in `indopak`,
    U+08D6 in `kemenag`. If a font is swapped, this is the record of what the previous choice
    could not render."""
    scripts = web.coverage_from_data(cdn_tree)["scripts"]

    assert scripts["indopak"]["missing"]["amiri"]["U+089C"] > 0
    assert scripts["kemenag"]["missing"]["amiri"]["U+08D6"] > 0
    assert "amiri" not in scripts["indopak"]["usable"]
    assert scripts["uthmani"]["missing"] == {}


def test_a_script_no_font_covers_fails_the_build() -> None:
    """The gate, not just the report: an uncovered codepoint stops the site being built."""
    with pytest.raises(ValueError, match="no bundled font covers"):
        web.font_coverage({"uthmani": ["\U0001f600"]})


def test_the_fonts_command_writes_the_report_where_asked(cdn_tree: Path, tmp_path: Path) -> None:
    """The report goes outside the data tree, so it is never published."""
    out = tmp_path / "fonts.json"
    result = CliRunner().invoke(app, ["fonts", "--data", str(cdn_tree), "--out", str(out)])

    assert result.exit_code == 0, result.output
    assert set(json.loads(out.read_text(encoding="utf-8"))["scripts"]) >= {"uthmani", "warsh"}
    assert not list(cdn_tree.rglob("fonts.json"))


def test_verse_ids_are_published_per_script(cdn_tree: Path) -> None:
    """Translations are keyed to the Hafs count and the scripts are not all keyed that way.

    The reader joins them through this field, so it has to say which of the three cases each
    script is in rather than leaving a consumer to infer it from prose.
    """
    scripts = {entry["id"]: entry for entry in read_json(cdn_tree / "manifest.json")["scripts"]}

    assert scripts["uthmani"]["verse_ids"] == "hafs"
    assert scripts["kemenag"]["verse_ids"] == "hafs"
    assert scripts["warsh"]["verse_ids"] == "mapped"
    assert scripts["qalun"]["verse_ids"] == "mapped"
    assert scripts["indopak"]["verse_ids"] == "own"
    assert scripts["indopak"]["verse_ids_differ_in"] == [1]

    divergent = {entry["id"] for entry in scripts.values() if "verse_ids_differ_in" in entry}
    assert divergent == {"indopak"}


def test_the_divergent_chapter_is_the_one_with_an_unnumbered_basmala(cdn_tree: Path) -> None:
    """`verse_ids_differ_in` is a claim about the text, so the text has to bear it out."""
    indopak = read_json(cdn_tree / "text" / "indopak" / "chapters" / "1.json")["verses"]
    uthmani = read_json(cdn_tree / "text" / "uthmani" / "chapters" / "1.json")["verses"]

    # The counts agree, so it is the labels that differ, not the number of verses.
    assert len(indopak) == len(uthmani) == 7
    assert uthmani[0]["text"].startswith("ب")  # the basmala, numbered 1:1
    assert not indopak[0]["text"].startswith("ب")  # al-hamdu: basmala left unnumbered
    assert "number_in_hafs" not in indopak[0]

    # Which verse is which, read off the letters across the two orthographies.
    assert "الحمد" in _letters(indopak[0]["text"])
    assert "الحمد" in _letters(uthmani[1]["text"])
    assert "الحمد" not in _letters(uthmani[0]["text"])


#: Diacritics, superscript alef, tatweel and the waqf signs: what one rasm spells and
#: another writes differently, so that letters can be looked for across orthographies.
_MARKS = re.compile(r"[ـً-ٰٟۖ-ۭ࣢ࣰ-ࣿ\s]")


def _letters(text: str) -> str:
    """The bare letters of a verse, with alef wasla read as a plain alef."""
    return _MARKS.sub("", text).replace("ٱ", "ا")
