"""Checks for the assembled Astro site after the site build has run."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPOSITORY = Path(__file__).parents[1]
ASSEMBLED = REPOSITORY / ".build" / "assembled"
LOCAL_URL = re.compile(r"""(?:href|src)="(/[^"#?]*)"|url\(["']?(/[^"')?#]*)["']?\)""")
FRAGMENT = re.compile(r'''href="#([^"]+)"''')
MODULE_IMPORT = re.compile(r"""(?:from|import)\s+["'](\./[^"']+)["']""")


def _assembled_tree() -> Path:
    if not ASSEMBLED.is_dir():
        pytest.skip("run `npm run site -- --no-cdn` before assembled-site checks")
    return ASSEMBLED


def _local_targets(path: Path) -> set[str]:
    return {match.group(1) or match.group(2) for match in LOCAL_URL.finditer(path.read_text())}


def _resolves(tree: Path, url: str) -> bool:
    target = tree / url.lstrip("/")
    return target.is_file() or (target / "index.html").is_file()


def test_assembled_astro_pages_keep_profile_and_catalogue_contract() -> None:
    tree = _assembled_tree()
    manifest = json.loads((tree / "manifest.json").read_text(encoding="utf-8"))
    chapters = json.loads((tree / "chapters.json").read_text(encoding="utf-8"))
    translations = json.loads((tree / "translations" / "index.json").read_text(encoding="utf-8"))
    page = (tree / "index.html").read_text(encoding="utf-8")

    assert "{{" not in page and "}}" not in page
    assert f">{len(manifest['scripts'])}<" in page
    assert f">{translations['count']}<" in page
    for anchor in (
        "quickstart",
        "endpoints",
        "scripts",
        "translations",
        "transliteration",
        "audio",
        "fonts",
        "sources",
    ):
        assert f'id="{anchor}"' in page
    page_ids = set(re.findall(r'id="([^"]+)"', page))
    assert {match.group(1) for match in FRAGMENT.finditer(page)} <= page_ids

    for script in manifest["scripts"]:
        assert _resolves(tree, script["path"])
        assert _resolves(tree, script["chapters"].replace("{1-114}", "1"))
    assert _resolves(tree, manifest["chapters"]["path"])
    assert _resolves(tree, manifest["translations"]["index"])
    assert _resolves(tree, manifest["transliteration"]["index"])
    for edition in translations["editions"]:
        assert _resolves(tree, edition["files"]["quran"])
        assert _resolves(tree, edition["files"]["chapters"].replace("{1-114}", "1"))

    # The quickstart uses the first chapter, so its reader route must use id 1.
    assert f"/app/#/{chapters[0]['id']}?s={manifest['scripts'][0]['id']}" in page
    assert manifest["transliteration"]["count"] == 0
    assert not (tree / "transliteration" / "kemenag").exists()


def test_assembled_pages_and_styles_reference_existing_same_origin_files() -> None:
    tree = _assembled_tree()
    sources = [tree / "index.html", tree / "app" / "index.html"]
    sources.extend((tree / "_astro").glob("*.css"))
    sources.extend([tree / "assets" / "base.css", tree / "app" / "app.css"])

    assert (tree / "assets" / "fonts" / "amiri-regular.woff2").is_file()
    for source in sources:
        for url in _local_targets(source):
            assert _resolves(tree, url), f"{source.relative_to(tree)} points at missing {url}"

    for module in (tree / "app").glob("*.js"):
        for imported in MODULE_IMPORT.findall(module.read_text(encoding="utf-8")):
            assert (module.parent / imported.removeprefix("./")).is_file(), (
                f"{module.name} imports missing {imported}"
            )
