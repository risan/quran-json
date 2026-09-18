"""The site's own assets: the documentation page, the reader app, and the Arabic fonts.

`cdn/` is a contract for consumers, and the HTML and JavaScript in it are a contract for
readers. These tests pin the parts of that a mistake would otherwise be invisible in: a link
that 404s, a placeholder left unsubstituted in the page, a font path that does not resolve,
and the coverage measurement that decides whether a script renders or shows missing-glyph
boxes. They also pin the measurement itself, because a font swap is exactly the kind of
change that would otherwise silently degrade one mushaf tradition.
"""

from __future__ import annotations

import re
from hashlib import sha256
from pathlib import Path

import pytest

from quranjson import web
from quranjson.jsonio import read_json

#: Every local target a page or a stylesheet can point at.
_LOCAL_URL = re.compile(r"""(?:href|src)="(/[^"#?]*)"|url\(["']?(/[^"')?#]*)["']?\)""")


def _targets(path: Path) -> set[str]:
    """Local paths referenced by one HTML or CSS file."""
    found: set[str] = set()
    for match in _LOCAL_URL.finditer(path.read_text(encoding="utf-8")):
        found.add(match.group(1) or match.group(2))
    return found


def _resolve(tree: Path, url: str) -> bool:
    """A URL resolves when its exact file exists, or a directory serves an index page."""
    target = tree / url.lstrip("/")
    return target.is_file() or (target / "index.html").is_file()


def test_bundled_fonts_match_their_manifest_hashes() -> None:
    """A font is a binary published in the page; its bytes are pinned like any snapshot."""
    for record in read_json(web.ASSETS / "fonts" / "sources.json"):
        path = Path(record["path"])
        assert path.is_file(), record["path"]
        assert sha256(path.read_bytes()).hexdigest() == record["sha256"], record["id"]
        assert path.stat().st_size == record["bytes"], record["id"]
        assert str(record["url"]).startswith("https://"), record["id"]


def test_every_font_ships_the_licence_that_grants_it() -> None:
    """OFL requires the licence and copyright notice to travel with the font."""
    for record in read_json(web.ASSETS / "fonts" / "sources.json"):
        licence = web.ASSETS / "fonts" / record["license_file"]
        assert licence.is_file(), record["license_file"]
        assert "SIL Open Font License" in licence.read_text(encoding="utf-8"), record["id"]
        assert record["license_status"] == "granted", record["id"]


def test_the_page_leaves_no_placeholder_behind(cdn_tree: Path) -> None:
    """An unsubstituted `{{...}}` would ship a template artefact to a reader."""
    page = (cdn_tree / "index.html").read_text(encoding="utf-8")
    assert "{{" not in page
    assert "}}" not in page


def test_the_page_is_rendered_from_the_published_catalogue(cdn_tree: Path) -> None:
    """The documentation cannot disagree with the data, because it is rendered from it."""
    manifest = read_json(cdn_tree / "manifest.json")
    translations = read_json(cdn_tree / "translations" / "index.json")
    page = (cdn_tree / "index.html").read_text(encoding="utf-8")

    assert f"{manifest['translations']['languages']:,}" in page
    assert f"{translations['count']:,}" in page

    for script in manifest["scripts"]:
        assert f"<code>{script['id']}</code>" in page, script["id"]
    for edition in translations["editions"]:
        assert edition["path"] in page, edition["path"]


def test_every_local_link_and_asset_resolves(cdn_tree: Path) -> None:
    """A broken internal link is invisible in review and obvious to a reader."""
    sources = [cdn_tree / "index.html", *(cdn_tree / "app").glob("*.html")]
    sources += [cdn_tree / "assets" / "base.css", cdn_tree / "app" / "app.css"]

    for source in sources:
        for url in _targets(source):
            assert _resolve(cdn_tree, url), f"{source.name} points at {url}, which is missing"


def test_the_app_ships_every_module_it_imports(cdn_tree: Path) -> None:
    """`app.js` is an ES module; every `import "./x.js"` has to exist beside it."""
    app = cdn_tree / "app"
    for module in app.glob("*.js"):
        for imported in re.findall(r'from "(\./[^"]+)"', module.read_text(encoding="utf-8")):
            assert (app / imported.removeprefix("./")).is_file(), (
                f"{module.name} imports {imported}"
            )


def test_coverage_is_published_for_every_script_and_font(cdn_tree: Path) -> None:
    """The app chooses a font per script from this file, so it has to be complete."""
    manifest = read_json(cdn_tree / "manifest.json")
    coverage = read_json(cdn_tree / "app" / "fonts.json")

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
        assert font["file"].startswith("/assets/fonts/"), font["id"]


def test_the_measured_gaps_are_the_ones_published(cdn_tree: Path) -> None:
    """Amiri is the traditional naskh and also the one with holes: U+089C in `indopak`,
    U+08D6 in `kemenag`. If a font is swapped, this is the record of what the previous choice
    could not render."""
    scripts = read_json(cdn_tree / "app" / "fonts.json")["scripts"]

    assert scripts["indopak"]["missing"]["amiri"]["U+089C"] > 0
    assert scripts["kemenag"]["missing"]["amiri"]["U+08D6"] > 0
    assert "amiri" not in scripts["indopak"]["usable"]
    assert scripts["uthmani"]["missing"] == {}


def test_a_script_no_font_covers_fails_the_build() -> None:
    """The gate, not just the report: an uncovered codepoint stops the site being built."""
    with pytest.raises(ValueError, match="no bundled font covers"):
        web.font_coverage({"uthmani": ["\U0001f600"]})


def test_the_docs_template_names_only_values_the_build_sets(tmp_path: Path) -> None:
    """`write_docs` raises on a placeholder the build does not set, so a typo cannot ship."""
    with pytest.raises(KeyError, match=r"web/index\.html asks for"):
        web.write_docs(tmp_path, {})

    assert not list(tmp_path.iterdir())


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
    assert uthmani[0]["text"].startswith("\u0628")  # the basmala, numbered 1:1
    assert not indopak[0]["text"].startswith("\u0628")  # al-hamdu: basmala left unnumbered
    assert "number_in_hafs" not in indopak[0]

    # Which verse is which, read off the letters across the two orthographies.
    assert "\u0627\u0644\u062d\u0645\u062f" in _letters(indopak[0]["text"])
    assert "\u0627\u0644\u062d\u0645\u062f" in _letters(uthmani[1]["text"])
    assert "\u0627\u0644\u062d\u0645\u062f" not in _letters(uthmani[0]["text"])


#: Diacritics, superscript alef, tatweel and the waqf signs: what one rasm spells and
#: another writes differently, so that letters can be looked for across orthographies.
_MARKS = re.compile(r"[\u0640\u064b-\u065f\u0670\u06d6-\u06ed\u08e2\u08f0-\u08ff\s]")


def _letters(text: str) -> str:
    """The bare letters of a verse, with alef wasla read as a plain alef."""
    return _MARKS.sub("", text).replace("\u0671", "\u0627")
