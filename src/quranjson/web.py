"""The site's own assets: the documentation page, the reader app, and the Arabic fonts.

`cdn/` is generated from `data/`; the page and the app are generated from `web/` the same
way. They live there as real HTML, CSS and JavaScript -- editable, lintable, and readable as
what they are -- and this module substitutes the catalogue into the page and copies both
trees into the output.

Two things are *measured* rather than written down:

*   **The catalogue rows on the page** are rendered from the same structures the JSON
    artifacts are written from, so the documentation cannot disagree with the data.
*   **The font coverage table** is measured from the committed font files against the bytes
    of every published script. A script no bundled font covers fails the build, because the
    alternative is a page that renders missing-glyph boxes for a mushaf tradition and calls
    it published.

The fonts are the site's, never the dataset's: the dataset publishes UTF-8 text and names no
font, so a consumer is free to render it their own way. Preference order is the manifest's
order -- the first font complete for a script becomes that script's default. Amiri leads as
the traditional naskh of the printed mushaf; Noto Naskh Arabic trails as the deliberate last
resort, since it covers everything and so makes the gaps in the others visible instead of
fatal.
"""

from __future__ import annotations

import html
import re
import shutil
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from dataclasses import fields as dataclass_fields
from pathlib import Path
from typing import Any, Final

from fontTools.ttLib import TTFont

from . import config
from .jsonio import read_json, write_json

__all__ = [
    "APP",
    "ASSETS",
    "DOCS",
    "Font",
    "docs_context",
    "font_coverage",
    "fonts",
    "write_docs",
    "write_site_assets",
]

#: Hand-written assets, copied verbatim into the output tree.
ASSETS: Final = config.WEB / "assets"
APP: Final = config.WEB / "app"
DOCS: Final = config.WEB / "index.html"

#: Where the coverage report is published, for the app to consume.
FONTS_JSON: Final = "app/fonts.json"

#: `{{placeholder}}` in the page template; substituted, never left behind.
_PLACEHOLDER: Final = re.compile(r"\{\{([a-z_0-9]+)\}\}")


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
        """This font as the app receives it, with the scripts it is complete for."""
        return {
            "id": self.id,
            "name": self.family,
            "file": f"/assets/fonts/{self.file}",
            "version": self.version,
            "copyright": self.copyright,
            "source": self.source,
            "license": self.license,
            "license_url": self.license_url,
            "license_file": f"/assets/fonts/{self.license_file}",
            "covers": ",".join(
                script
                for script, entry in coverage["scripts"].items()
                if self.id not in entry["missing"]
            ),
        }


def fonts() -> list[Font]:
    """Every bundled font, in preference order (see the module docstring)."""
    fields = {field.name for field in dataclass_fields(Font)}
    records: list[dict[str, Any]] = read_json(ASSETS / "fonts" / "sources.json")

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
) -> dict[str, Any]:
    """Measure every bundled font against every published script.

    Args:
        scripts: script id -> the text of its verses.
        names: chapter names, rendered in the same font as the scripture and so part of
            what a script's font has to cover.

    Returns:
        The coverage report published as `/app/fonts.json`: per script, the font that
        covers it and, for each font that does not, the codepoints it is missing and how
        often they occur.

    Raises:
        ValueError: a script no bundled font covers. Publishing it would render missing
            glyphs for a mushaf tradition, which is worse than failing the build.
    """
    bundled = fonts()
    cmaps = {font.id: _codepoints(ASSETS / "fonts" / font.file) for font in bundled}
    name_counts = _used(names)

    report: dict[str, Any] = {}

    for script, texts in scripts.items():
        counts = _used(texts) + name_counts
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


def write_site_assets(out_dir: Path, coverage: Mapping[str, Any]) -> None:
    """Copy the hand-written assets into the site and publish the coverage report."""
    for source in (ASSETS, APP):
        shutil.copytree(source, out_dir / source.name)

    write_json(out_dir / FONTS_JSON, coverage)


def write_docs(out_dir: Path, values: Mapping[str, str]) -> None:
    """Render the documentation page from its template.

    Raises:
        KeyError: the template asks for a value the build does not supply.
    """

    def substitute(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in values:
            raise KeyError(f"web/index.html asks for {{{{{key}}}}}, which the build does not set")
        return values[key]

    page = _PLACEHOLDER.sub(substitute, DOCS.read_text(encoding="utf-8"))
    (out_dir / "index.html").write_text(page, encoding="utf-8")


def _escape(value: Any) -> str:
    return html.escape(str(value), quote=True)


def _rows(rows: Iterable[Sequence[str]]) -> str:
    """One `<tr>` per row; cells are escaped by the caller."""
    return "\n".join(
        "      <tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>" for row in rows
    )


def _sample(
    script: str, text: str, coverage: Mapping[str, Any], bundled: Mapping[str, Font]
) -> str:
    """A verse of the script, rendered in the font the app will use for it."""
    font = bundled[coverage["scripts"][script]["default"]]
    return (
        '<span class="sample" lang="ar" dir="rtl" '
        f'style="font-family:{_escape(font.family)}">{_escape(text)}</span>'
    )


def docs_context(
    *,
    manifest: Mapping[str, Any],
    translations: Mapping[str, Any],
    transliterations: Mapping[str, Any],
    reciters: Mapping[str, Any] | None,
    coverage: Mapping[str, Any],
    chapters: Sequence[Mapping[str, Any]],
    samples: Mapping[str, str],
) -> dict[str, str]:
    """Every value the documentation page's template asks for.

    Args:
        manifest: the manifest the site publishes, so the page cannot disagree with it.
        translations: the published translation catalogue, as published.
        transliterations: the published transliteration catalogue.
        reciters: the reciter index, or None when the build skipped audio.
        coverage: the measured font coverage report.
        chapters: the 114 chapter metadata records.
        samples: script id -> a verse from that script, for the scripts table.
    """
    bundled = {font.id: font for font in fonts()}
    scripts = manifest["scripts"]
    editions = translations["editions"]
    published_transliterations = transliterations["editions"]

    # The quickstart examples name a real script and a real edition, so a reader can paste
    # them. Chapter 2 is the one every consumer ends up fetching; its 255th verse is the
    # 262nd ayah of the Quran, which is what the global-ayah audio template needs.
    global_ayah_2_255 = (
        sum(int(chapter["total_verses"]) for chapter in chapters if int(chapter["id"]) < 2) + 255
    )

    script_rows = [
        (
            f"<code>{_escape(script['id'])}</code>",
            _escape(script["name"]),
            f"{script['verses']:,}",
            _escape(script["description"]),
            _sample(script["id"], samples[script["id"]], coverage, bundled),
        )
        for script in scripts
    ]

    font_rows = []
    for script in scripts:
        entry = coverage["scripts"][script["id"]]
        marks = []
        for font in bundled.values():
            gaps = entry["missing"].get(font.id)
            if not gaps:
                marks.append('<span class="yes" title="every codepoint covered">yes</span>')
                continue

            title = ", ".join(f"{cp} x{count}" for cp, count in list(gaps.items())[:4])
            marks.append(f'<span class="no" title="{_escape(title)}">{len(gaps)}</span>')

        font_rows.append(
            (
                f"<code>{_escape(script['id'])}</code>",
                str(entry["codepoints"]),
                f"<code>{_escape(entry['default'])}</code>",
                *marks,
            )
        )

    translation_rows = [
        (
            f"<code>{_escape(edition['code'])}</code>",
            _escape(edition["author"]),
            _escape(edition["direction"]),
            _escape(edition["version"]),
            f'<a href="{_escape(edition["license"]["url"])}">'
            f"{_escape(edition['license']['status'])}</a>",
            # A directory has no index page on a static host: link the file it contains.
            f'<a href="{_escape(edition["path"])}quran.json">'
            f"<code>{_escape(edition['path'])}quran.json</code></a>",
        )
        for edition in editions
    ]

    return {
        "chapter_count": str(len(chapters)),
        "script_count": str(len(scripts)),
        "translation_count": f"{translations['count']:,}",
        "language_count": f"{manifest['translations']['languages']:,}",
        "transliteration_count": f"{transliterations['count']:,}",
        "verse_count": f"{int(manifest['scripts'][0]['verses']):,}",
        "reciter_count": f"{len(reciters['reciters']):,}" if reciters else "0",
        "host_count": str(len(reciters["hosts"])) if reciters else "0",
        "scripts_rows": _rows(script_rows),
        "font_rows": _rows(font_rows),
        "font_columns": "".join(f"<th>{_escape(font.family)}</th>" for font in bundled.values()),
        "translations_rows": _rows(translation_rows),
        "withheld_rows": _rows(
            (
                _escape(entry["edition"]),
                _escape(entry["author"]),
                _escape(entry["status"]),
                f'<a href="{_escape(entry["license_url"])}">terms</a>',
            )
            for entry in [*translations["withheld"], *transliterations["withheld"]]
        ),
        "withheld_count": str(len(translations["withheld"]) + len(transliterations["withheld"])),
        "transliterations_rows": _rows(
            (
                f"<code>{_escape(edition['edition'])}</code>",
                _escape(edition["author"]),
                f'<a href="{_escape(edition["license"]["url"])}">'
                f"{_escape(edition['license']['status'])}</a>",
                f'<a href="{_escape(edition["path"])}quran.json">'
                f"<code>{_escape(edition['path'])}quran.json</code></a>",
            )
            for edition in published_transliterations
        ),
        "transliteration_lead": _transliteration_lead(published_transliterations),
        "audio_rows": _rows(
            (
                _escape(host["name"]),
                f"<code>{_escape(host['template'])}</code>",
                _escape(host["indexing"]),
                _escape(host["license_status"]),
            )
            for host in (reciters or {}).get("hosts", {}).values()
        ),
        "default_script": scripts[0]["id"],
        "default_translation": editions[0]["path"].strip("/").split("/")[-1],
        "default_transliteration": (
            published_transliterations[0]["path"].strip("/").split("/")[-1]
            if published_transliterations
            else ""
        ),
        "global_ayah_2_255": str(global_ayah_2_255),
        "attribution": _escape(manifest["attribution"]),
    }


def _transliteration_lead(published: Sequence[Mapping[str, Any]]) -> str:
    """One sentence saying whether a romanisation is published, and why not if none is."""
    if not published:
        return (
            "No romanisation is published: Qur'an Kemenag's carries no grant and Tanzil's "
            "is restricted to non-commercial use. The catalogue is written anyway, so a "
            "client asking whether one exists gets an answer rather than a 404."
        )

    names = ", ".join(f"<code>{_escape(entry['edition'])}</code>" for entry in published)
    return (
        f"Published: {names}. The grant is not verified — the origin serves it under "
        "<code>--include-unverified-licenses</code>, and the catalogue entry says so "
        "instead of claiming rights the project does not hold."
    )
