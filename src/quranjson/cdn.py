"""Generate the Cloudflare Pages site.

Layout produced under the output directory::

    _headers            CORS + immutable caching for version-pinned paths
    _redirects          /latest/* -> /<version>/*
    index.html          human-readable endpoint reference
    versions.json       machine-readable version catalogue
    <version>/...       the dataset tree (via build.render_tree)

Paths are version-pinned so they can be cached immutably forever, which is the whole
point of putting this behind a CDN. New data means a new version directory, never a
mutation of an existing one.

Only editions with a verified redistribution grant are published; see
`quranjson.licensing`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import config, licensing, qa
from .build import RenderOptions, render_tree
from .jsonio import write_json

__all__ = ["DEFAULT_BASE_URL", "build_site"]

DEFAULT_BASE_URL = "https://quran-json.pages.dev/"

_HEADERS = """\
/*
  Access-Control-Allow-Origin: *
  Access-Control-Allow-Methods: GET, HEAD, OPTIONS
  Access-Control-Expose-Headers: ETag, Content-Length
  X-Content-Type-Options: nosniff

/{version}/*
  Cache-Control: public, max-age=31536000, immutable
"""

_REDIRECTS = """/latest/* /{version}/:splat 302
/latest /{version}/ 302
"""

_INDEX = """\
<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>quran-json</title>
<style>
  body {{ font: 16px/1.6 system-ui, sans-serif; max-width: 46rem; margin: 4rem auto; padding: 0 1rem; }}
  code, pre {{ font-family: ui-monospace, monospace; background: #f4f4f5; }}
  code {{ padding: .1rem .3rem; border-radius: 3px; }}
  pre {{ padding: 1rem; overflow-x: auto; border-radius: 6px; }}
  th, td {{ text-align: left; padding: .25rem .75rem .25rem 0; }}
</style>
<h1>quran-json</h1>
<p>Quran text, transliteration, and translations in JSON. Version
<code>{version}</code>. CORS enabled, no authentication, no rate limit.</p>

<h2>Endpoints</h2>
<table>
  <tr><th>Path</th><th>Contents</th></tr>
  <tr><td><code>/{version}/quran.json</code></td><td>All 114 chapters with Uthmani text</td></tr>
  <tr><td><code>/{version}/quran_{{lang}}.json</code></td><td>Text plus a translation</td></tr>
  <tr><td><code>/{version}/chapters/index.json</code></td><td>Chapter index</td></tr>
  <tr><td><code>/{version}/chapters/{{1-114}}.json</code></td><td>One chapter</td></tr>
  <tr><td><code>/{version}/chapters/{{lang}}/{{1-114}}.json</code></td><td>One chapter with a translation</td></tr>
  <tr><td><code>/{version}/verses/{{1-6236}}.json</code></td><td>One verse with every translation</td></tr>
{extra}
  <tr><td><code>/{version}/meta/sources.json</code></td><td>Provenance and license per dataset</td></tr>
</table>

<p>Translations published: {langs}.</p>
<p><code>/latest/</code> redirects to the newest version. Pin a version in production:
only version-pinned paths are cached immutably.</p>
<p><a href="versions.json">versions.json</a></p>
"""


def build_site(
    out_dir: Path,
    *,
    version: str,
    base_url: str = DEFAULT_BASE_URL,
    pretty: bool = False,
    include_unverified_licenses: bool = False,
    audio: bool = True,
) -> list[licensing.Violation]:
    """Render the versioned dataset tree plus the Pages site files.

    Returns the editions that were withheld for lack of a redistribution grant.
    """
    options, withheld = _render_options(
        version=version,
        base_url=base_url,
        pretty=pretty,
        include_unverified_licenses=include_unverified_licenses,
    )
    render_tree(out_dir / version, options)

    if audio:
        from .audio import build_audio_index

        build_audio_index(out_dir / version / "audio", pretty=pretty)

    write_json(
        out_dir / version / "meta" / "sources.json",
        sources_manifest(include_withheld=withheld),
        pretty=pretty,
    )
    write_json(out_dir / version / "meta" / "qa.json", qa.manifest(), pretty=pretty)

    (out_dir / "_headers").write_text(_HEADERS.format(version=version), encoding="utf-8")
    (out_dir / "_redirects").write_text(_REDIRECTS.format(version=version), encoding="utf-8")
    (out_dir / "index.html").write_text(
        _INDEX.format(
            version=version,
            langs=", ".join(lang for lang in options.langs if lang is not None) or "none",
            extra=(
                f"  <tr><td><code>/{version}/audio/reciters.json</code></td>"
                "<td>Reciters and audio URL templates</td></tr>\n"
                if audio
                else ""
            ),
        ),
        encoding="utf-8",
    )

    _write_versions(out_dir, version, base_url)
    return withheld


def _render_options(
    *,
    version: str,
    base_url: str,
    pretty: bool,
    include_unverified_licenses: bool,
) -> tuple[RenderOptions, list[licensing.Violation]]:
    """Decide what may be published, enforcing the licence gate.

    The licensed generation is the default: Tanzil text, Tanzil chapter metadata, and
    every QuranEnc translation. ``include_unverified_licenses`` falls back to the legacy
    sources instead, which is only appropriate for reproducing `dist/`.
    """
    if include_unverified_licenses:
        permitted = set(licensing.publishable_languages())
        langs: tuple[str | None, ...] = tuple(
            lang for lang in config.LANG_CODES if lang is None or lang in permitted
        )
        return (
            RenderOptions(
                link_base=f"{base_url.rstrip('/')}/{version}/chapters/",
                pretty=pretty,
                content="legacy",
                langs=langs,
                verse_langs=tuple(lang for lang in langs if lang is not None),
                transliteration=False,
            ),
            [violation for violation in licensing.blocked() if violation.lang not in permitted],
        )

    keys = tuple(edition.lang for edition in published_editions())

    if not keys:
        raise licensing.LicenseError(
            "no QuranEnc translations are committed; run `quran-json fetch` first"
        )

    from .jsonio import read_json as _read
    from .quranenc import featured_keys

    featured = featured_keys(_read(config.quranenc_catalogue_path()))

    return (
        RenderOptions(
            link_base=f"{base_url.rstrip('/')}/{version}/chapters/",
            pretty=pretty,
            content="licensed",
            langs=(None, *keys),
            verse_langs=featured,
            transliteration=False,
        ),
        _withheld_legacy(),
    )


def published_editions() -> list[config.Edition]:
    """Every translation we publish: the QuranEnc catalogue plus our extra editions."""
    catalogue = config.quranenc_catalogue_path()
    editions: list[config.Edition] = []

    if catalogue.exists():
        from .jsonio import read_json
        from .quranenc import catalogue_editions

        editions.extend(catalogue_editions(read_json(catalogue)))

    editions.extend(
        edition
        for edition in config.EXTRA_EDITIONS
        if config.extra_edition_path(edition.lang).exists()
    )
    return editions


def _withheld_legacy() -> list[licensing.Violation]:
    """Everything in the legacy registry that the licensed generation does not use."""
    return [
        licensing.Violation(
            lang=edition.lang,
            author=edition.author,
            status=edition.license.status,
            license_url=edition.license.url,
        )
        for edition in config.EDITIONS
        if not edition.redistributable
    ]


def sources_manifest(
    *, include_withheld: list[licensing.Violation] | None = None
) -> dict[str, Any]:
    """Provenance and licence status for exactly what the site publishes.

    QuranEnc condition 3 requires stating the version of a republished translation, so the
    catalogue version travels with each edition.
    """
    from .jsonio import read_json

    catalogue = config.quranenc_catalogue_path()
    versions: dict[str, str] = {}

    if catalogue.exists():
        versions = {
            entry["key"]: entry["version"] for entry in read_json(catalogue)["translations"]
        }

    editions = [
        {
            "lang": edition.lang,
            "author": edition.author,
            "source": edition.source,
            "status": edition.license.status,
            "license": edition.license.text,
            "license_url": edition.license.url,
            "version": versions.get(edition.lang, "n/a"),
        }
        for edition in published_editions()
    ]

    return {
        "text": {
            "edition": "tanzil-uthmani",
            "status": config.TANZIL_TEXT.status,
            "license": config.TANZIL_TEXT.text,
            "license_url": config.TANZIL_TEXT.url,
            "source": "https://tanzil.net/pub/download/",
        },
        "chapters": {
            "source": "https://tanzil.net/res/text/metadata/quran-data.xml",
            "status": config.TANZIL_TEXT.status,
            "license_url": config.TANZIL_TEXT.url,
        },
        "transliteration": {
            "status": "withheld",
            "reason": "No transliteration source with a redistribution grant was found.",
            "review": "data/meta/licensing-review.json",
        },
        "editions": editions,
        "withheld": [
            {
                "lang": violation.lang,
                "author": violation.author,
                "status": violation.status,
                "license_url": violation.license_url,
            }
            for violation in (include_withheld or [])
        ],
        "attribution": (
            "Quran text and chapter metadata: Tanzil.net (CC-BY 3.0, verbatim). "
            "Translations: each edition's publisher, credited per entry above. "
            "Audio: linked from EveryAyah, Islamic Network and MP3Quran; we host no audio."
        ),
    }


def _write_versions(out_dir: Path, version: str, base_url: str) -> None:
    """Catalogue every version directory present in the output."""
    versions: list[dict[str, Any]] = []

    for child in sorted(out_dir.iterdir()):
        if not child.is_dir() or child.name.startswith(("_", ".")):
            continue
        versions.append(
            {
                "version": child.name,
                "base": f"{base_url.rstrip('/')}/{child.name}/",
                "files": sum(1 for path in child.rglob("*") if path.is_file()),
            }
        )

    write_json(
        out_dir / "versions.json",
        {"latest": version, "versions": versions},
        pretty=True,
    )
