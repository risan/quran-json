"""Checks for the assembled site after `npm run site -- --no-cdn` has run."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPOSITORY = Path(__file__).parents[1]
ASSEMBLED = REPOSITORY / ".build" / "assembled"

#: Local targets a page or stylesheet points at: href/src attributes and CSS url().
LOCAL_URL = re.compile(r"""(?:href|src)="(/[^"#?]*)"|url\(["']?(/[^"')?#]*)["']?\)""")
FRAGMENT = re.compile(r'''href="#([^"]+)"''')


def _tree() -> Path:
    if not ASSEMBLED.is_dir():
        pytest.skip("run `npm run site -- --no-cdn` before assembled-site checks")

    return ASSEMBLED


def _targets(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")

    return {match.group(1) or match.group(2) for match in LOCAL_URL.finditer(text)}


def _resolves(tree: Path, url: str) -> bool:
    target = tree / url.lstrip("/")

    return target.is_file() or (target / "index.html").is_file()


def test_astro_adds_only_its_own_files() -> None:
    tree = _tree()

    assert (tree / "index.html").is_file()
    assert (tree / "app" / "index.html").is_file()
    assert (tree / "favicon.svg").is_file()
    assert list((tree / "_astro").glob("*.js"))
    assert list((tree / "_astro").glob("*.css"))
    assert (tree / "fonts" / "amiri-regular.woff2").is_file()
    assert (tree / "fonts" / "sources.json").is_file()


def test_old_site_paths_are_gone() -> None:
    tree = _tree()

    for old in ("assets", "app/fonts.json", "app/app.js", "app/app.css", "_site"):
        assert not (tree / old).exists(), old


def test_the_coverage_report_is_never_published() -> None:
    tree = _tree()

    assert not list(tree.rglob("fonts.json"))
    assert not (tree.parent / "data" / "fonts.json").exists()
    assert (tree.parent / "fonts.json").is_file()


def test_the_romanisation_report_is_built_but_never_published() -> None:
    tree = _tree()
    report = tree.parent / "romanize-report.md"

    assert report.is_file()
    assert "## Every non-matching verse" in report.read_text(encoding="utf-8")
    assert not list(tree.rglob("romanize-report*"))


def test_every_local_link_and_asset_resolves() -> None:
    tree = _tree()
    sources = [tree / "index.html", tree / "app" / "index.html"]
    sources.extend((tree / "_astro").glob("*.css"))

    for source in sources:
        for url in _targets(source):
            assert _resolves(tree, url), f"{source.relative_to(tree)} points at missing {url}"


def test_in_page_links_point_at_ids_that_exist() -> None:
    page = (_tree() / "index.html").read_text(encoding="utf-8")
    ids = set(re.findall(r'id="([^"]+)"', page))

    assert {match.group(1) for match in FRAGMENT.finditer(page)} <= ids


def test_the_docs_page_is_rendered_from_the_published_catalogue() -> None:
    tree = _tree()
    manifest = json.loads((tree / "manifest.json").read_text(encoding="utf-8"))
    translations = json.loads((tree / "translations" / "index.json").read_text(encoding="utf-8"))
    page = (tree / "index.html").read_text(encoding="utf-8")

    assert "{{" not in page
    for script in manifest["scripts"]:
        assert f"<code>{script['id']}</code>" in page, script["id"]
        assert _resolves(tree, script["path"])
    for edition in translations["editions"]:
        assert edition["path"] in page, edition["path"]
        assert _resolves(tree, edition["files"]["quran"])
    for anchor in (
        "quick-start",
        "endpoints",
        "scripts",
        "translations",
        "transliteration",
        "audio",
        "sources",
        "changes",
    ):
        assert f'id="{anchor}"' in page, anchor


def test_the_reader_island_receives_the_measured_fonts() -> None:
    """The reader limits font choices per script from coverage embedded at build time."""
    tree = _tree()
    page = (tree / "app" / "index.html").read_text(encoding="utf-8")

    assert "client:only" in page or "astro-island" in page
    assert "&quot;usable&quot;" in page or '"usable"' in page
