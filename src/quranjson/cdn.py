"""Generate the published site.

Layout, all unversioned::

    /manifest.json                                  scripts, counts, pointers
    /chapters.json                                  the 114 chapters' shared metadata
    /text/{script}/quran.json
    /text/{script}/chapters/{1-114}.json
    /translations/index.json                        the edition catalogue
    /translations/{code}-{slug}/quran.json
    /translations/{code}-{slug}/chapters/{1-114}.json
    /audio/reciters.json
    /_headers
    /index.html

Three deliberate choices, each reversing an earlier one:

*   **Unversioned.** The Quran text is immutable and translations are only ever added, so
    versioning guarded against a change we have committed never to make -- at the cost of
    a ``/latest/`` redirect and a version segment in every URL.
*   **No per-verse files.** They were 6,236 of 15,987 files (39%) to save a consumer from
    reading one chapter file first, and they silently carried an arbitrary subset of
    editions.
*   **Translations carry no Arabic.** Embedding the text in every edition duplicated one
    1.7 MB corpus 83 times -- 105 MB, a fifth of the deployment.

Because paths are unversioned, ``_headers`` caches the data immutably on the strength of a
promise: a published path is never renamed, removed, or rewritten. Adding a script, an
edition, or a chapter is fine; changing one is not.

Only editions with a verified redistribution grant are published; see
`quranjson.licensing`.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import config, licensing, qa
from .jsonio import read_json, write_json

__all__ = ["build_site", "edition_url_key", "published_editions"]

#: Chapters in the Quran, asserted against the snapshots before anything is written.
CHAPTER_COUNT = 114

_HEADERS = """\
/*
  Access-Control-Allow-Origin: *
  Access-Control-Allow-Methods: GET, HEAD, OPTIONS
  Access-Control-Expose-Headers: ETag, Content-Length
  X-Content-Type-Options: nosniff

/text/*
  Cache-Control: public, max-age=31536000, immutable

/translations/*
  Cache-Control: public, max-age=31536000, immutable

/audio/*
  Cache-Control: public, max-age=3600
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
<p>Quran text and translations in JSON. CORS enabled, no authentication, no rate limit.</p>

<h2>Text</h2>
<table>
  <tr><th>Path</th><th>Contents</th></tr>
  <tr><td><code>/manifest.json</code></td><td>Scripts, counts, and pointers</td></tr>
  <tr><td><code>/chapters.json</code></td><td>Metadata for all 114 chapters</td></tr>
  <tr><td><code>/text/{{script}}/quran.json</code></td><td>The whole Quran in one script</td></tr>
  <tr><td><code>/text/{{script}}/chapters/{{1-114}}.json</code></td><td>One chapter in one script</td></tr>
</table>
<p>Scripts: {scripts}.</p>

<h2>Translations</h2>
<table>
  <tr><th>Path</th><th>Contents</th></tr>
  <tr><td><code>/translations/index.json</code></td><td>The edition catalogue</td></tr>
  <tr><td><code>/translations/{{code}}-{{slug}}/quran.json</code></td><td>The whole Quran in one translation</td></tr>
  <tr><td><code>/translations/{{code}}-{{slug}}/chapters/{{1-114}}.json</code></td><td>One chapter in one translation</td></tr>
</table>
<p>{translations} translations are published, across {languages} languages. Translation
files carry the translation only; fetch a <code>/text/</code> file for the Arabic.</p>

<h2>Other</h2>
<table>
  <tr><th>Path</th><th>Contents</th></tr>
{extra}
  <tr><td><code>/meta/sources.json</code></td><td>Provenance and license per dataset</td></tr>
  <tr><td><code>/meta/qa.json</code></td><td>Transcription corrections applied upstream</td></tr>
</table>

<p>Paths carry no version. The text is immutable and editions are only ever added, so a
path published today keeps working; see the README for the compatibility contract.</p>
"""


def edition_url_key(edition: config.Edition) -> str:
    """The path segment for an edition: ``english_pickthall`` becomes ``en-pickthall``.

    Raises:
        ValueError: the edition has no language code, or its key is not
            ``<language>_<translator>``.
    """
    if not edition.code:
        raise ValueError(f"edition {edition.lang!r} has no language code for its URL")

    _, _, translator = edition.lang.partition("_")
    if not translator:
        raise ValueError(f"edition {edition.lang!r} is not `<language>_<translator>`")

    return f"{edition.code}-{translator.replace('_', '-')}"


def chapter_metadata() -> list[dict[str, Any]]:
    """Metadata for all 114 chapters, published once rather than per edition.

    The Arabic name and Tanzil's English rendering do not vary by edition or script, so
    copying them into every chapter file would repeat the same 89 KB across ~10,000 files
    -- and would present an English chapter name as though it belonged to a French edition.
    """
    return [
        {
            "id": chapter["id"],
            "name": chapter["name"],
            "transliteration": chapter["transliteration"],
            "translation": chapter["translation"],
            "type": chapter["type"],
            "total_verses": chapter["total_verses"],
        }
        for chapter in read_json(config.tanzil_chapters_path())["chapters"]
    ]


def _script_chapters(variant: str) -> list[dict[str, Any]]:
    """One script's text as 114 chapter objects, verses only."""
    snapshot: dict[str, list[dict[str, Any]]] = read_json(config.tanzil_text_path(variant))

    return [
        {
            "id": int(chapter),
            "verses": [
                {"id": int(verse["verse"]), "text": verse["text"]}
                for verse in sorted(snapshot[chapter], key=lambda item: int(item["verse"]))
            ],
        }
        for chapter in sorted(snapshot, key=int)
    ]


def _edition_chapters(edition: config.Edition) -> list[dict[str, Any]]:
    """One edition's translation as 114 chapter objects, translation text only.

    The Arabic verse text is deliberately absent: it is identical for every edition and
    lives under `/text/`, so including it here duplicated the corpus 83 times.
    """
    path = (
        config.quranenc_path(edition.lang)
        if edition.kind == "quranenc"
        else config.extra_edition_path(edition.lang)
    )
    snapshot: dict[str, list[dict[str, Any]]] = read_json(path)

    chapters: list[dict[str, Any]] = []

    for key in sorted(snapshot, key=int):
        verses: list[dict[str, Any]] = []

        for verse in sorted(snapshot[key], key=lambda item: int(item["verse"])):
            entry: dict[str, Any] = {"id": int(verse["verse"]), "translation": verse["text"]}

            # QuranEnc grants republication on condition that nothing is deleted, so
            # translator footnotes travel with the verse when the source supplies them.
            if verse.get("footnotes"):
                entry["footnotes"] = verse["footnotes"]

            verses.append(entry)

        chapters.append({"id": int(key), "verses": verses})

    return chapters


def _check_shape(label: str, chapters: list[dict[str, Any]]) -> int:
    """Assert a rendered scripture is complete before it is written."""
    if len(chapters) != CHAPTER_COUNT:
        raise ValueError(f"{label}: expected {CHAPTER_COUNT} chapters, got {len(chapters)}")

    verses = sum(len(chapter["verses"]) for chapter in chapters)
    if verses != 6236:
        raise ValueError(f"{label}: expected 6236 verses, got {verses}")

    return verses


def _write_jsonl_dir(directory: Path, chapters: list[dict[str, Any]], *, pretty: bool) -> None:
    """Write one file per chapter plus the whole collection, for one scripture."""
    write_json(directory / "quran.json", chapters, pretty=pretty)
    for chapter in chapters:
        write_json(directory / "chapters" / f"{chapter['id']}.json", chapter, pretty=pretty)


def published_editions() -> list[config.Edition]:
    """Every translation we publish: the QuranEnc catalogue plus our extra editions."""
    catalogue = config.quranenc_catalogue_path()
    editions: list[config.Edition] = []

    if catalogue.exists():
        from .quranenc import catalogue_editions

        editions.extend(catalogue_editions(read_json(catalogue)))

    editions.extend(
        edition
        for edition in config.EXTRA_EDITIONS
        if config.extra_edition_path(edition.lang).exists()
    )
    return editions


def build_site(
    out_dir: Path,
    *,
    pretty: bool = False,
    include_unverified_licenses: bool = False,
    audio: bool = True,
) -> list[licensing.Violation]:
    """Render the site into ``out_dir``, replacing whatever is there.

    Args:
        out_dir: directory to write into; emptied first.
        pretty: indent the JSON by two spaces instead of emitting it compactly.
        include_unverified_licenses: publish editions whose redistribution status is not
            verified as granted. Only use once you have cleared the rights yourself.
        audio: also write the reciter index.

    Returns:
        The editions withheld for lack of a redistribution grant.

    Raises:
        licensing.LicenseError: a published edition has no verified grant and
            ``include_unverified_licenses`` was not set.
        ValueError: a snapshot is incomplete, or two editions collide on one URL.
    """
    editions = published_editions()

    if not editions:
        raise licensing.LicenseError("no translations are committed; run `quran-json fetch` first")

    if not include_unverified_licenses:
        licensing.require_publishable(
            (edition.lang for edition in editions),
            editions=editions,
        )

    if out_dir.exists():
        import shutil

        shutil.rmtree(out_dir)

    chapters = chapter_metadata()
    if len(chapters) != CHAPTER_COUNT:
        raise ValueError(f"chapter metadata: expected {CHAPTER_COUNT}, got {len(chapters)}")

    written: dict[str, str] = {}
    for edition in editions:
        key = edition_url_key(edition)
        if key in written:
            raise ValueError(f"URL collision on {key!r}: {written[key]} and {edition.lang}")
        written[key] = edition.lang

    write_json(out_dir / "chapters.json", chapters, pretty=pretty)

    counts: dict[str, int] = {}

    for variant in config.TANZIL_VARIANTS:
        script = _script_chapters(variant)
        counts[variant] = _check_shape(f"text/{variant}", script)
        _write_jsonl_dir(out_dir / "text" / variant, script, pretty=pretty)

    index: list[dict[str, Any]] = []
    catalogue = _catalogue_metadata()

    for edition in editions:
        key = edition_url_key(edition)
        translated = _edition_chapters(edition)
        _check_shape(f"translations/{key}", translated)
        _write_jsonl_dir(out_dir / "translations" / key, translated, pretty=pretty)

        meta = catalogue.get(edition.lang, {})
        index.append(
            {
                "path": f"/translations/{key}/",
                "edition": edition.lang,
                "language": edition.lang.partition("_")[0],
                "code": edition.code,
                "direction": meta.get("direction", "ltr"),
                "author": edition.author,
                "source": edition.source,
                "license": {
                    "status": edition.license.status,
                    "text": edition.license.text,
                    "url": edition.license.url,
                },
                # QuranEnc condition 3 requires stating the version of a republished
                # translation, so it travels with the catalogue entry.
                "version": meta.get("version", "n/a"),
                "chapters": CHAPTER_COUNT,
                "files": {
                    "quran": f"/translations/{key}/quran.json",
                    "chapters": f"/translations/{key}/chapters/{{1-{CHAPTER_COUNT}}}.json",
                },
            }
        )

    write_json(
        out_dir / "translations" / "index.json",
        {
            "count": len(index),
            "editions": index,
            "withheld": [
                {
                    "edition": violation.lang,
                    "author": violation.author,
                    "status": violation.status,
                    "license_url": violation.license_url,
                }
                for violation in _withheld()
            ],
        },
        pretty=pretty,
    )

    write_json(
        out_dir / "manifest.json",
        {
            "chapters": {"count": CHAPTER_COUNT, "path": "/chapters.json"},
            "scripts": [
                {
                    "id": variant,
                    "name": config.SCRIPT_LABELS[variant][0],
                    "description": config.SCRIPT_LABELS[variant][1],
                    "verses": counts.get(variant, 0),
                    "path": f"/text/{variant}/quran.json",
                    "chapters": f"/text/{variant}/chapters/{{1-{CHAPTER_COUNT}}}.json",
                }
                for variant in config.TANZIL_VARIANTS
            ],
            "translations": {
                "count": len(index),
                "languages": len({entry["code"] for entry in index}),
                "index": "/translations/index.json",
            },
            "audio": "/audio/reciters.json" if audio else None,
            "license": {
                "project": "CC BY-SA 4.0",
                "text": {
                    "source": "tanzil.net",
                    "status": config.TANZIL_TEXT.status,
                    "url": config.TANZIL_TEXT.url,
                },
            },
            "attribution": (
                "Quran text and chapter metadata: Tanzil.net (CC-BY 3.0, verbatim). "
                "Translations: each edition's publisher, credited in "
                "/translations/index.json. Audio: linked from EveryAyah, Islamic Network "
                "and MP3Quran; no audio is hosted here."
            ),
        },
        pretty=pretty,
    )

    write_json(out_dir / "meta" / "sources.json", sources_manifest(), pretty=pretty)
    write_json(out_dir / "meta" / "qa.json", qa.manifest(), pretty=pretty)

    if audio:
        from .audio import build_audio_index

        build_audio_index(out_dir / "audio", pretty=pretty)

    (out_dir / "_headers").write_text(_HEADERS, encoding="utf-8")
    (out_dir / "index.html").write_text(
        _INDEX.format(
            scripts=", ".join(f"<code>{variant}</code>" for variant in config.TANZIL_VARIANTS),
            translations=len(index),
            languages=len({entry["code"] for entry in index}),
            extra=(
                "  <tr><td><code>/audio/reciters.json</code></td>"
                "<td>Reciters and audio URL templates</td></tr>\n"
                if audio
                else ""
            ),
        ),
        encoding="utf-8",
    )

    return _withheld()


def _catalogue_metadata() -> dict[str, dict[str, Any]]:
    """Per-edition catalogue fields: direction, version, and the source description."""
    catalogue = config.quranenc_catalogue_path()
    if not catalogue.exists():
        return {}
    return {entry["key"]: entry for entry in read_json(catalogue)["translations"]}


def _withheld() -> list[licensing.Violation]:
    """Every registered edition we do not publish, and why."""
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


def sources_manifest() -> dict[str, Any]:
    """Provenance and licence status for the sources behind the published site."""
    versions = {key: entry.get("version", "n/a") for key, entry in _catalogue_metadata().items()}
    scripts = list(config.TANZIL_VARIANTS)

    return {
        "text": {
            "source": "https://tanzil.net/pub/download/",
            "status": config.TANZIL_TEXT.status,
            "license": config.TANZIL_TEXT.text,
            "license_url": config.TANZIL_TEXT.url,
            "scripts": scripts,
            "note": (
                "Six Tanzil text variants are published. They are the same licence as the "
                "single variant published before; the grant is per text, not per variant."
            ),
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
        "editions": [
            {
                "edition": edition.lang,
                "path": f"/translations/{edition_url_key(edition)}/",
                "author": edition.author,
                "source": edition.source,
                "status": edition.license.status,
                "license": edition.license.text,
                "license_url": edition.license.url,
                "version": versions.get(edition.lang, "n/a"),
            }
            for edition in published_editions()
        ],
        "withheld": [
            {
                "edition": violation.lang,
                "author": violation.author,
                "status": violation.status,
                "license_url": violation.license_url,
            }
            for violation in _withheld()
        ],
    }
