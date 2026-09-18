"""Generate the published site.

Layout, all unversioned::

    /manifest.json                                  scripts, counts, pointers
    /chapters.json                                  the 114 chapters' shared metadata
    /text/{script}/quran.json
    /text/{script}/chapters/{1-114}.json
    /translations/index.json                        the edition catalogue
    /translations/{code}-{slug}/quran.json
    /translations/{code}-{slug}/chapters/{1-114}.json
    /transliteration/index.json                     the transliteration catalogue
    /transliteration/{key}/quran.json
    /transliteration/{key}/chapters/{1-114}.json
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

__all__ = [
    "build_site",
    "edition_url_key",
    "published_editions",
    "published_transliterations",
    "transliteration_url_key",
]

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

/transliteration/*
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


def _is_transliteration(edition: config.Edition) -> bool:
    """A transliteration is language-shaped but is not a translation: it gets its own path."""
    return edition.lang.startswith(config.TRANSLITERATION)


def transliteration_url_key(edition: config.Edition) -> str:
    """The path segment for a transliteration: ``transliteration_kemenag`` -> ``kemenag``.

    Raises:
        ValueError: the edition is not a transliteration.
    """
    if not _is_transliteration(edition):
        raise ValueError(f"edition {edition.lang!r} is not a transliteration")

    return edition.lang.partition("_")[2] or edition.lang


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


def _script_chapters(script: str) -> list[dict[str, Any]]:
    """One script's text as 114 chapter objects, verses only."""
    if script == config.KEMENAG_SCRIPT:
        return _kemenag_chapters("text")

    snapshot: dict[str, list[dict[str, Any]]] = read_json(config.tanzil_text_path(script))

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


def _kemenag_chapters(field: str) -> list[dict[str, Any]]:
    """Qur'an Kemenag's snapshot as 114 chapter objects carrying one field per verse.

    The snapshot keeps the text, the translation and the transliteration as three fields of
    one ayah record -- they are one API response -- so each published artifact slices the
    field it needs.
    """
    snapshot: dict[str, list[dict[str, Any]]] = read_json(config.kemenag_path())

    return [
        {
            "id": int(chapter),
            "verses": [
                {"id": int(verse["verse"]), field: verse[field]}
                for verse in sorted(verses, key=lambda item: int(item["verse"]))
            ],
        }
        for chapter, verses in sorted(snapshot.items(), key=lambda item: int(item[0]))
    ]


def _kemenag_translation_chapters() -> list[dict[str, Any]]:
    """Qur'an Kemenag's 2019 Indonesian translation, carrying the translator's footnotes."""
    snapshot: dict[str, list[dict[str, Any]]] = read_json(config.kemenag_path())

    chapters: list[dict[str, Any]] = []

    for chapter in sorted(snapshot, key=int):
        verses: list[dict[str, Any]] = []

        for verse in sorted(snapshot[chapter], key=lambda item: int(item["verse"])):
            entry: dict[str, Any] = {
                "id": int(verse["verse"]),
                "translation": verse["translation"],
            }

            # The ministry's footnotes are part of its translation, as QuranEnc's are.
            if verse.get("footnotes"):
                entry["footnotes"] = verse["footnotes"]

            verses.append(entry)

        chapters.append({"id": int(chapter), "verses": verses})

    return chapters


def _transliteration_chapters(edition: config.Edition) -> list[dict[str, Any]]:
    """One transliteration as 114 chapter objects, romanisation text only.

    Every transliteration registered so far is Qur'an Kemenag's, where the romanisation is
    one field of the same ayah record as the text. A transliteration delivered as a
    language-shaped snapshot would read `text` instead, as the editions do -- so an unknown
    kind is refused rather than silently read from the wrong file.
    """
    if edition.kind != "kemenag":
        raise ValueError(f"no reader for a {edition.kind!r} transliteration")

    return _kemenag_chapters("transliteration")


def _edition_chapters(edition: config.Edition) -> list[dict[str, Any]]:
    """One edition's translation as 114 chapter objects, translation text only.

    The Arabic verse text is deliberately absent: it is identical for every edition and
    lives under `/text/`, so including it here duplicated the corpus 83 times.
    """
    if edition.kind == "kemenag":
        return _kemenag_translation_chapters()

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


def published_editions(*, include_unverified: bool = False) -> list[config.Edition]:
    """Every translation we publish: the QuranEnc catalogue plus our extra editions.

    With ``include_unverified`` the ingested-but-uncleared editions join the list, which is
    what `--include-unverified-licenses` means: publish these too, now that the rights have
    been cleared out of band.
    """
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

    if include_unverified:
        editions.extend(
            edition
            for edition in config.PENDING_EDITIONS
            if not _is_transliteration(edition) and _edition_snapshot(edition).exists()
        )

    return editions


def _edition_snapshot(edition: config.Edition) -> Path:
    """Where an edition's committed snapshot lives, by the shape its source delivers."""
    if edition.kind == "kemenag":
        return config.kemenag_path()
    if edition.kind == "quranenc":
        return config.quranenc_path(edition.lang)
    if edition in config.EXTRA_EDITIONS:
        return config.extra_edition_path(edition.lang)
    return config.edition_path(edition.lang)


def published_transliterations(*, include_unverified: bool = False) -> list[config.Edition]:
    """Every transliteration we publish, in registry order.

    Today that is none, and the site publishes no romanisation: Qur'an Kemenag's has no
    grant, so a tree here would be a tree of unchecked romanisations. The catalogue at
    `/transliteration/index.json` says so rather than 404ing, and each candidate is
    published only once its rights are cleared.

    Like the translations, this covers the editions ingested for this generation rather
    than the frozen `dist/` registry, so `--include-unverified-licenses` republishes what
    we just ingested and not every romanisation the frozen tree once referenced.
    """
    return [
        edition
        for edition in config.PENDING_EDITIONS
        if _is_transliteration(edition)
        and (edition.redistributable or include_unverified)
        and _edition_snapshot(edition).exists()
    ]


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
    editions = published_editions(include_unverified=include_unverified_licenses)
    transliterations = published_transliterations(include_unverified=include_unverified_licenses)

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

    for edition in transliterations:
        key = transliteration_url_key(edition)
        if key in written:
            raise ValueError(f"URL collision on {key!r}: {written[key]} and {edition.lang}")
        written[key] = edition.lang

    write_json(out_dir / "chapters.json", chapters, pretty=pretty)

    # A script's bytes are published on the strength of its own licence, not because it
    # arrived with the others: Kemenag's text is covered by its publishing regulation,
    # Tanzil's by CC-BY 3.0, and anything else has to earn its place here first.
    scripts = [
        script
        for script in config.SCRIPT_IDS
        if config.SCRIPT_LICENSES[script].allows_publication or include_unverified_licenses
    ]

    counts: dict[str, int] = {}

    for script in scripts:
        text = _script_chapters(script)
        counts[script] = _check_shape(f"text/{script}", text)
        _write_jsonl_dir(out_dir / "text" / script, text, pretty=pretty)

    # What was actually published, so nothing published is also listed as withheld.
    published_langs = {edition.lang for edition in (*editions, *transliterations)}

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
                _withheld_entry(edition)
                for edition in _withheld_editions(published_langs)
                if not _is_transliteration(edition)
            ],
        },
        pretty=pretty,
    )

    # The transliteration catalogue is always written, even when it publishes nothing: a
    # consumer asking whether a romanisation exists deserves an answer, not a 404.
    transliteration_index: list[dict[str, Any]] = []

    for edition in transliterations:
        key = transliteration_url_key(edition)
        romanised = _transliteration_chapters(edition)
        _check_shape(f"transliteration/{key}", romanised)
        _write_jsonl_dir(out_dir / "transliteration" / key, romanised, pretty=pretty)

        transliteration_index.append(
            {
                "path": f"/transliteration/{key}/",
                "edition": edition.lang,
                "author": edition.author,
                "source": edition.source,
                "license": {
                    "status": edition.license.status,
                    "text": edition.license.text,
                    "url": edition.license.url,
                },
                "chapters": CHAPTER_COUNT,
                "files": {
                    "quran": f"/transliteration/{key}/quran.json",
                    "chapters": f"/transliteration/{key}/chapters/{{1-{CHAPTER_COUNT}}}.json",
                },
            }
        )

    write_json(
        out_dir / "transliteration" / "index.json",
        {
            "count": len(transliteration_index),
            "editions": transliteration_index,
            "withheld": [
                _withheld_entry(edition)
                for edition in _withheld_editions(published_langs)
                if _is_transliteration(edition)
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
                    "id": script,
                    "name": config.SCRIPT_LABELS[script][0],
                    "description": config.SCRIPT_LABELS[script][1],
                    "verses": counts.get(script, 0),
                    "path": f"/text/{script}/quran.json",
                    "chapters": f"/text/{script}/chapters/{{1-{CHAPTER_COUNT}}}.json",
                }
                for script in scripts
            ],
            "translations": {
                "count": len(index),
                "languages": len({entry["code"] for entry in index}),
                "index": "/translations/index.json",
            },
            "transliteration": {
                "count": len(transliteration_index),
                "index": "/transliteration/index.json",
            },
            "audio": "/audio/reciters.json" if audio else None,
            "license": {
                "project": "CC BY-SA 4.0",
                "text": {
                    "source": "tanzil.net and quran.kemenag.go.id",
                    "status": config.TANZIL_TEXT.status,
                    "url": config.TANZIL_TEXT.url,
                },
            },
            "attribution": (
                "Quran text and chapter metadata: Tanzil.net (CC-BY 3.0, verbatim) and, for "
                "the Mushaf Standar Indonesia script, LPMQ / Kementerian Agama RI. "
                "Translations: each edition's publisher, credited in "
                "/translations/index.json. Audio: linked from EveryAyah, Islamic Network "
                "and MP3Quran; no audio is hosted here."
            ),
        },
        pretty=pretty,
    )

    write_json(
        out_dir / "meta" / "sources.json",
        sources_manifest(scripts=scripts, editions=editions, transliterations=transliterations),
        pretty=pretty,
    )
    write_json(out_dir / "meta" / "qa.json", qa.manifest(), pretty=pretty)

    if audio:
        from .audio import build_audio_index

        build_audio_index(out_dir / "audio", pretty=pretty)

    (out_dir / "_headers").write_text(_HEADERS, encoding="utf-8")
    (out_dir / "index.html").write_text(
        _INDEX.format(
            scripts=", ".join(f"<code>{script}</code>" for script in scripts),
            translations=len(index),
            languages=len({entry["code"] for entry in index}),
            extra=(
                (
                    "  <tr><td><code>/transliteration/index.json</code></td>"
                    "<td>The romanisation catalogue</td></tr>\n"
                )
                if transliteration_index
                else ""
            )
            + (
                "  <tr><td><code>/audio/reciters.json</code></td>"
                "<td>Reciters and audio URL templates</td></tr>\n"
                if audio
                else ""
            ),
        ),
        encoding="utf-8",
    )

    return [licensing.violation(edition) for edition in _withheld_editions(published_langs)]


def _catalogue_metadata() -> dict[str, dict[str, Any]]:
    """Per-edition catalogue fields: direction, version, and the source description."""
    catalogue = config.quranenc_catalogue_path()
    if not catalogue.exists():
        return {}
    return {entry["key"]: entry for entry in read_json(catalogue)["translations"]}


def _withheld_entry(edition: config.Edition) -> dict[str, Any]:
    """One withheld edition as a catalogue entry."""
    return {
        "edition": edition.lang,
        "author": edition.author,
        "status": edition.license.status,
        "license_url": edition.license.url,
    }


def _withheld_editions(published_langs: set[str]) -> list[config.Edition]:
    """Registered editions a build left out because their licence is not granted.

    Not `licensing.blocked()`: under `--include-unverified-licenses` an uncleared edition is
    published, so it is not withheld, and reporting it as such would misdescribe the tree.
    """
    return [
        edition
        for edition in config.REGISTERED
        if not edition.redistributable and edition.lang not in published_langs
    ]


def sources_manifest(
    *,
    scripts: list[str],
    editions: list[config.Edition],
    transliterations: list[config.Edition],
) -> dict[str, Any]:
    """Provenance and licence status for the sources behind the published site.

    Takes what the build actually published instead of recomputing it, so the manifest
    describes the tree it is written into -- under `--include-unverified-licenses` a
    granted-only view would be a lie.
    """
    versions = {key: entry.get("version", "n/a") for key, entry in _catalogue_metadata().items()}
    published_langs = {edition.lang for edition in (*editions, *transliterations)}

    return {
        "text": {
            "source": "https://tanzil.net/pub/download/ and https://quran.kemenag.go.id/",
            "status": config.TANZIL_TEXT.status,
            "license": config.TANZIL_TEXT.text,
            "license_url": config.TANZIL_TEXT.url,
            "scripts": scripts,
            "script_licenses": [
                {
                    "script": script,
                    "status": config.SCRIPT_LICENSES[script].status,
                    "license_url": config.SCRIPT_LICENSES[script].url,
                }
                for script in config.SCRIPT_IDS
            ],
            "withheld_scripts": [script for script in config.SCRIPT_IDS if script not in scripts],
            "note": (
                "Seven scripts are published: the six Tanzil variants (one licence -- the "
                "grant is per text, not per variant) and Qur'an Kemenag's Mushaf Standar "
                "Indonesia, a distinct orthography whose text the ministry's own publishing "
                "regulation (PMA 44/2016 Pasal 8(1)) holds to be uncopyrightable. Only "
                "UTF-8 text is taken from Kemenag: no fonts, no mushaf layout, no "
                "ornaments, which Pasal 8(2) reserves to the publisher."
            ),
        },
        "chapters": {
            "source": "https://tanzil.net/res/text/metadata/quran-data.xml",
            "status": config.TANZIL_TEXT.status,
            "license_url": config.TANZIL_TEXT.url,
        },
        "transliteration": {
            "status": "published" if transliterations else "withheld",
            "reason": (
                "Published under the verdicts recorded in the review record."
                if transliterations
                else "No transliteration with a redistribution grant: Qur'an Kemenag's is of "
                "unknown status and Tanzil's is restricted. The review record states what "
                "would unblock each."
            ),
            "index": "/transliteration/index.json",
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
            for edition in editions
        ],
        "withheld": [_withheld_entry(edition) for edition in _withheld_editions(published_langs)],
    }
