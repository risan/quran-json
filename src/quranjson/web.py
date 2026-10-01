"""Font coverage: which bundled Arabic font can render which published script.

The site ships three Arabic fonts (`site/public/fonts/`). This module measures them with
fontTools against every codepoint a script's verses, chapter names and unnumbered furniture
use, and fails when a script has no font that covers it. That gate matters because the
alternative is a reader that renders missing-glyph boxes for a mushaf tradition and calls it
published.

The fonts are the site's, never the dataset's: the dataset publishes UTF-8 text and names no
font. Preference order is the order of `sources.json` -- the first font complete for a script
becomes that script's default. Amiri leads as the traditional naskh of the printed mushaf;
Noto Naskh Arabic trails as the deliberate last resort, since it covers everything and so makes
the gaps in the others visible instead of fatal.

The measured result is written to a path the caller chooses (`quran-json fonts --out`), outside
the published data tree: the site build reads it, and it is never deployed.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from dataclasses import fields as dataclass_fields
from pathlib import Path
from typing import Any, Final

from fontTools.ttLib import TTFont

from . import config
from .jsonio import read_json, write_json

__all__ = ["FONTS", "Font", "coverage_from_data", "font_coverage", "fonts", "write_coverage"]

#: The bundled fonts, their licence texts and `sources.json`; served at `/fonts/`.
FONTS: Final = config.ROOT / "site" / "public" / "fonts"

#: The public URL prefix of `FONTS`.
FONT_URL: Final = "/fonts"


@dataclass(frozen=True, slots=True)
class Font:
    """One bundled Arabic font, with the provenance and licence that travel with it."""

    id: str
    family: str
    file: str
    version: str
    copyright: str
    source: str
    license: str
    license_url: str
    license_file: str

    def payload(self, coverage: Mapping[str, Any]) -> dict[str, str]:
        """This font as the site receives it, with the scripts it is complete for."""
        return {
            "id": self.id,
            "name": self.family,
            "file": f"{FONT_URL}/{self.file}",
            "version": self.version,
            "copyright": self.copyright,
            "source": self.source,
            "license": self.license,
            "license_url": self.license_url,
            "license_file": f"{FONT_URL}/{self.license_file}",
            "covers": ",".join(
                script
                for script, entry in coverage["scripts"].items()
                if self.id not in entry["missing"]
            ),
        }


def fonts() -> list[Font]:
    """Every bundled font, in preference order (see the module docstring)."""
    fields = {field.name for field in dataclass_fields(Font)}
    records: list[dict[str, Any]] = read_json(FONTS / "sources.json")

    # The manifest carries provenance the build does not need (path, hash, byte count), so
    # the record is filtered rather than the dataclass widened.
    return [Font(**{key: record[key] for key in fields}) for record in records]


def _codepoints(path: Path) -> set[int]:
    """Every codepoint a font can render, across all of its cmap subtables."""
    font = TTFont(str(path), lazy=True)
    try:
        covered: set[int] = set()
        for table in font["cmap"].tables:
            covered |= set(table.cmap)
    finally:
        font.close()

    return covered


def _used(texts: Iterable[str]) -> Counter[int]:
    """How often each codepoint appears in the text being checked."""
    counts: Counter[int] = Counter()
    for text in texts:
        counts.update(ord(character) for character in text)

    return counts


def font_coverage(
    scripts: Mapping[str, Sequence[str]],
    *,
    names: Sequence[str] = (),
    furniture: Mapping[str, Sequence[str]] | None = None,
) -> dict[str, Any]:
    """Measure every bundled font against every published script.

    Args:
        scripts: script id -> the text of its verses.
        names: chapter names, rendered in the same font as the scripture and so part of
            what a script's font has to cover.
        furniture: optional script id -> unnumbered source furniture rendered with a script,
            such as a source-provided bismillah before Duri chapter 1.

    Returns:
        The coverage report: per script, the font that covers it and, for each font that does
        not, the codepoints it is missing and how often they occur.

    Raises:
        ValueError: a script no bundled font covers. Publishing it would render missing
            glyphs for a mushaf tradition, which is worse than failing the build.
    """
    bundled = fonts()
    cmaps = {font.id: _codepoints(FONTS / font.file) for font in bundled}
    name_counts = _used(names)
    furniture = furniture or {}

    report: dict[str, Any] = {}

    for script, texts in scripts.items():
        counts = _used(texts) + _used(furniture.get(script, ())) + name_counts
        missing: dict[str, dict[str, int]] = {}

        for font in bundled:
            gaps = {
                f"U+{codepoint:04X}": count
                for codepoint, count in sorted(counts.items())
                if codepoint not in cmaps[font.id]
            }
            if gaps:
                missing[font.id] = gaps

        usable = [font.id for font in bundled if font.id not in missing]
        if not usable:
            detail = ", ".join(f"{font_id} misses {len(gaps)}" for font_id, gaps in missing.items())
            raise ValueError(f"text/{script}: no bundled font covers it ({detail})")

        report[script] = {
            "codepoints": len(counts),
            "default": usable[0],
            "usable": usable,
            "missing": missing,
        }

    return {
        "note": (
            "Coverage measured at build time from the bundled fonts against every codepoint "
            "each script's verses and the chapter names use. `default` is the first font in "
            "preference order that is complete for the script; `missing` counts the "
            "codepoints a font cannot render. Coverage is not shaping: a font that has the "
            "glyph still positions these marks by its own rules."
        ),
        "fonts": [font.payload({"scripts": report}) for font in bundled],
        "scripts": report,
        "uncovered": [],
    }


def coverage_from_data(data_dir: Path) -> dict[str, Any]:
    """Measure the fonts against the scripts of an already generated data tree."""
    manifest = read_json(data_dir / "manifest.json")
    names = [chapter["name"] for chapter in read_json(data_dir / "chapters.json")]
    corpora: dict[str, list[str]] = {}
    furniture: dict[str, list[str]] = {}

    for script in manifest["scripts"]:
        script_id = script["id"]
        quran = read_json(data_dir / "text" / script_id / "quran.json")
        corpora[script_id] = [verse["text"] for chapter in quran for verse in chapter["verses"]]
        furniture[script_id] = [item["text"] for item in script.get("chapter_furniture", [])]

    return font_coverage(corpora, names=names, furniture=furniture)


def write_coverage(data_dir: Path, out: Path) -> dict[str, Any]:
    """Measure the fonts against `data_dir` and write the report to `out`."""
    coverage = coverage_from_data(data_dir)
    write_json(out, coverage, pretty=True)

    return coverage
