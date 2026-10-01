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
    (the HTML pages, /_astro/* and /fonts/* are added by `npm run site`)
    /_headers

Three deliberate choices, each reversing an earlier one:

*   **Unversioned.** The Quran text is immutable and translations are only ever added, so
    versioning guarded against a change we have committed never to make -- at the cost of
    a ``/latest/`` redirect and a version segment in every URL.
*   **No per-verse files.** They were 6,236 of 15,987 files (39%) to save a consumer from
    reading one chapter file first, and they silently carried an arbitrary subset of
    editions.
*   **Translations carry no Arabic.** Embedding the text in every edition duplicated one
    1.7 MB corpus 83 times -- 105 MB, a fifth of the deployment.

Because paths are unversioned, a published path is never renamed or removed. Its content may
receive upstream corrections (Quranpedia's licence requires keeping copies current); they are
logged in `/meta/qa.json` and, for a new upstream release, in the source version recorded in
`/meta/sources.json`. So ``_headers`` caches data for a day and lets a stale copy be served
for a week while it revalidates, rather than caching it immutably. Only the hashed
`/_astro/*` build output and the font files are immutable.

Only editions with a verified redistribution grant are published; see
`quranjson.licensing`.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any, cast

from . import config, licensing, qa
from .jsonio import read_json, write_json

__all__ = [
    "build_site",
    "edition_url_key",
    "published_editions",
]

#: Chapters in the Quran, asserted against the snapshots before anything is written.
CHAPTER_COUNT = 114

#: Per-verse source fields published beside `id` and `text`, when a snapshot carries them.
#: `number_in_hafs` is the Nafiʿ riwayat' mapping onto the Hafs ayah numbers: those two
#: scripts number 6,214 ayahs and 50 surahs differ in length, so a consumer needs the
#: mapping to join them to the Hafs scripts at all.
PUBLISHED_VERSE_FIELDS = ("number_in_hafs",)

#: The Kufi count every translation, transliteration and Hafs script is keyed to.
HAFS_VERSES = 6236

_HEADERS = """\
/*
  Access-Control-Allow-Origin: *
  Access-Control-Allow-Methods: GET, HEAD, OPTIONS
  Access-Control-Expose-Headers: ETag, Content-Length
  X-Content-Type-Options: nosniff

/text/*
  Cache-Control: public, max-age=86400, stale-while-revalidate=604800

/translations/*
  Cache-Control: public, max-age=86400, stale-while-revalidate=604800

/translations/index.json
  ! Cache-Control
  Cache-Control: public, max-age=60, must-revalidate

/transliteration/*
  Cache-Control: public, max-age=86400, stale-while-revalidate=604800

/transliteration/index.json
  ! Cache-Control
  Cache-Control: public, max-age=60, must-revalidate

/audio/*
  Cache-Control: public, max-age=3600

/fonts/*
  Cache-Control: public, max-age=31536000, immutable

/_astro/*
  Cache-Control: public, max-age=31536000, immutable
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


def _script_snapshot_path(script: str) -> Path:
    """Where a script's committed snapshot lives, by source."""
    if script == config.DIGITALKHATT_SCRIPT:
        return config.digitalkhatt_path()

    if script in config.QURANPEDIA_SCRIPTS:
        return config.quranpedia_path(script)

    return config.tanzil_text_path(script)


def _script_chapters(script: str) -> list[dict[str, Any]]:
    """One script's text as 114 chapter objects, verses only."""
    if script == config.KEMENAG_SCRIPT:
        return _kemenag_chapters()

    snapshot: dict[str, list[dict[str, Any]]] = read_json(_script_snapshot_path(script))

    notice = {"notice": config.TANZIL_NOTICE} if script in config.TANZIL_VARIANTS else {}

    return [
        {
            "id": int(chapter),
            **notice,
            "verses": [
                {
                    "id": int(verse["verse"]),
                    "text": verse["text"],
                    **{field: verse[field] for field in PUBLISHED_VERSE_FIELDS if field in verse},
                }
                for verse in sorted(snapshot[chapter], key=lambda item: int(item["verse"]))
            ],
        }
        for chapter in sorted(snapshot, key=int)
    ]


def _kemenag_chapters() -> list[dict[str, Any]]:
    """Qur'an Kemenag's snapshot as 114 chapter objects carrying the Arabic text only.

    The snapshot also holds the ministry's translation and transliteration, which are
    protected and never published; only the text is covered by a grant.
    """
    # The committed snapshot stays exactly as the upstream served it; its recorded spacing slips
    # are restored here, and the build fails if upstream has already fixed one of them.
    snapshot = qa.apply_corrections(config.KEMENAG_SCRIPT, read_json(config.kemenag_path()))

    return [
        {
            "id": int(chapter),
            "verses": [
                {"id": int(verse["verse"]), "text": verse["text"]}
                for verse in sorted(verses, key=lambda item: int(item["verse"]))
            ],
        }
        for chapter, verses in sorted(snapshot.items(), key=lambda item: int(item[0]))
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


def _check_mapping(label: str, chapters: list[dict[str, Any]], script: str) -> None:
    """Validate a source-provided Hafs map without erasing legitimate overlaps."""
    chapter_counts = {chapter["id"]: chapter["total_verses"] for chapter in chapter_metadata()}
    for chapter in chapters:
        flattened: list[int] = []
        for verse in chapter["verses"]:
            numbers = verse.get("number_in_hafs")
            if not isinstance(numbers, list) or not numbers or numbers != sorted(set(numbers)):
                raise ValueError(
                    f"{label}: invalid number_in_hafs at {chapter['id']}:{verse['id']}"
                )
            if script in config.NATIVE_HAFS_QURANPEDIA_SCRIPTS and numbers != [verse["id"]]:
                raise ValueError(
                    f"{label}: {script} map is not native at {chapter['id']}:{verse['id']}"
                )
            limit = chapter_counts[chapter["id"]]
            if not all(isinstance(number, int) and 1 <= number <= limit for number in numbers):
                raise ValueError(
                    f"{label}: out-of-range number_in_hafs at {chapter['id']}:{verse['id']}"
                )
            flattened.extend(numbers)

        if flattened != sorted(flattened):
            raise ValueError(f"{label}: non-monotonic number_in_hafs in chapter {chapter['id']}")
        exception = next(
            (
                item
                for item in config.SCRIPT_MAPPING_COVERAGE_EXCEPTIONS.get(script, ())
                if item["chapter"] == chapter["id"]
            ),
            None,
        )
        expected = set(range(1, chapter_counts[chapter["id"]] + 1))
        if exception is None:
            if set(flattened) != expected:
                raise ValueError(f"{label}: incomplete Hafs mapping in chapter {chapter['id']}")
            continue

        missing = set(cast(tuple[int, ...], exception["missing_hafs"]))
        repeated = set(cast(tuple[int, ...], exception["repeated_hafs"]))
        if set(flattened) != expected - missing:
            raise ValueError(f"{label}: unexpected missing Hafs ids in chapter {chapter['id']}")
        counts = Counter(flattened)
        if any(counts[number] != 2 for number in repeated) or any(
            counts[number] != 1 for number in expected - missing - repeated
        ):
            raise ValueError(f"{label}: unexpected Hafs overlap in chapter {chapter['id']}")


def _native_chapter_counts(chapters: list[dict[str, Any]]) -> dict[str, int]:
    """Return only source chapter counts that differ from shared Hafs metadata."""
    canonical = {chapter["id"]: chapter["total_verses"] for chapter in chapter_metadata()}
    return {
        str(chapter["id"]): len(chapter["verses"])
        for chapter in chapters
        if len(chapter["verses"]) != canonical[chapter["id"]]
    }


def _chapter_furniture(script: str) -> list[dict[str, Any]]:
    """Expose source furniture whose position is pinned by the source dump.

    Quranpedia's al-Duri and al-Susi dumps carry the basmala outside its numbered ayah rows.  It is
    deliberately a manifest annotation: adding it as verse 1 would shift every source map
    and invent a Hafs join.  The dump exposes no similarly bounded furniture contract for
    the other chapters or scripts.
    """
    if script not in (config.DURI_SCRIPT, config.SUSI_SCRIPT):
        return []

    from .quranpedia import DUMP_METADATA

    return [
        {
            "chapter": 1,
            "position": "before-verses",
            "kind": "bismillah",
            "text": DUMP_METADATA[script]["bismillah"],
            "numbered": False,
        }
    ]


def _check_shape(
    label: str,
    chapters: list[dict[str, Any]],
    expected_verses: int,
    *,
    script: str | None = None,
) -> int:
    """Assert a rendered scripture is complete before it is written.

    The verse total is per script rather than a constant: the Hafs-count scripts run to
    6,236, while Warsh and Qalun number 6,214 ayahs to Nafiʿ's count, and padding either to
    6,236 would mean merging or splitting ayahs the riwayah holds apart.
    """
    if len(chapters) != CHAPTER_COUNT:
        raise ValueError(f"{label}: expected {CHAPTER_COUNT} chapters, got {len(chapters)}")

    verses = sum(len(chapter["verses"]) for chapter in chapters)
    if verses != expected_verses:
        raise ValueError(f"{label}: expected {expected_verses} verses, got {verses}")

    for chapter in chapters:
        ids = [verse["id"] for verse in chapter["verses"]]
        if ids != list(range(1, len(ids) + 1)):
            raise ValueError(f"{label}: chapter {chapter['id']} is not numbered 1..n")

    if script is not None and (
        config.SCRIPT_VERSE_IDS[script] == "mapped"
        or script in config.NATIVE_HAFS_QURANPEDIA_SCRIPTS
    ):
        _check_mapping(label, chapters, script)

    return verses


def _chapter(chapters: list[dict[str, Any]], chapter_id: int) -> dict[str, Any]:
    """One chapter of an already-rendered scripture, by its id."""
    return next(chapter for chapter in chapters if chapter["id"] == chapter_id)


def _write_jsonl_dir(directory: Path, chapters: list[dict[str, Any]], *, pretty: bool) -> None:
    """Write one file per chapter plus the whole collection, for one scripture."""
    write_json(directory / "quran.json", chapters, pretty=pretty)
    for chapter in chapters:
        write_json(directory / "chapters" / f"{chapter['id']}.json", chapter, pretty=pretty)


def published_editions() -> list[config.Edition]:
    """Every translation we publish: the QuranEnc catalogue plus our extra editions."""
    editions: list[config.Edition] = []

    if config.quranenc_catalogue_path().exists():
        from .quranenc import catalogue_editions, load_catalogues, merged_catalogue

        editions.extend(
            catalogue_editions(merged_catalogue(load_catalogues()), include_withheld=False)
        )

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
    audio: bool = True,
) -> None:
    """Render the site into ``out_dir``, replacing whatever is there.

    Args:
        out_dir: directory to write into; emptied first.
        pretty: indent the JSON by two spaces instead of emitting it compactly.
        audio: also write the reciter index.

    Raises:
        licensing.LicenseError: a published edition has no verified grant.
        ValueError: a snapshot is incomplete, or two editions collide on one URL.
    """
    editions = published_editions()

    if not editions:
        raise licensing.LicenseError("no translations are committed; run `quran-json fetch` first")

    licensing.require_publishable(editions)

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

    # A script's bytes are published on the strength of its own licence, not because it
    # arrived with the others: Kemenag's text is covered by its publishing regulation,
    # Tanzil's by CC-BY 3.0, and anything else has to earn its place here first.
    scripts = [
        script for script in config.SCRIPT_IDS if config.SCRIPT_LICENSES[script].allows_publication
    ]

    counts: dict[str, int] = {}
    native_counts: dict[str, dict[str, int]] = {}
    furniture_by_script: dict[str, list[dict[str, Any]]] = {}

    for script in scripts:
        text = _script_chapters(script)
        counts[script] = _check_shape(
            f"text/{script}", text, config.SCRIPT_VERSES[script], script=script
        )
        if differing := _native_chapter_counts(text):
            native_counts[script] = differing
        _write_jsonl_dir(out_dir / "text" / script, text, pretty=pretty)

        furniture = _chapter_furniture(script)
        if furniture:
            furniture_by_script[script] = furniture

    # What was actually published, so nothing published is also listed as withheld.
    published_langs = {edition.lang for edition in editions}

    index: list[dict[str, Any]] = []
    catalogue = _catalogue_metadata()

    for edition in editions:
        key = edition_url_key(edition)
        translated = _edition_chapters(edition)
        _check_shape(f"translations/{key}", translated, HAFS_VERSES)
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

    translations_manifest: dict[str, Any] = {
        "count": len(index),
        "editions": index,
        "withheld": _catalogue_withheld_entries(published_langs),
    }
    write_json(out_dir / "translations" / "index.json", translations_manifest, pretty=pretty)

    # The transliteration catalogue is always written, even when it publishes nothing: a
    # consumer asking whether a romanisation exists deserves an answer, not a 404.
    transliteration_manifest: dict[str, Any] = {"count": 0, "editions": [], "withheld": []}
    write_json(out_dir / "transliteration" / "index.json", transliteration_manifest, pretty=pretty)

    manifest: dict[str, Any] = {
        "chapters": {"count": CHAPTER_COUNT, "path": "/chapters.json"},
        "scripts": [
            {
                "id": script,
                "name": config.SCRIPT_LABELS[script][0],
                "description": config.SCRIPT_LABELS[script][1],
                "verses": counts.get(script, 0),
                "verse_ids": config.SCRIPT_VERSE_IDS[script],
                "license": _script_license(script),
                "path": f"/text/{script}/quran.json",
                "chapters": f"/text/{script}/chapters/{{1-{CHAPTER_COUNT}}}.json",
                **({"note": config.SCRIPT_NOTES[script]} if script in config.SCRIPT_NOTES else {}),
                **(
                    {"verse_ids_differ_in": list(config.SCRIPT_VERSE_ID_DIVERGENCE[script])}
                    if script in config.SCRIPT_VERSE_ID_DIVERGENCE
                    else {}
                ),
                **(
                    {"native_chapter_counts": native_counts[script]}
                    if script in native_counts
                    else {}
                ),
                **(
                    {
                        "mapping_coverage_exceptions": list(
                            config.SCRIPT_MAPPING_COVERAGE_EXCEPTIONS[script]
                        )
                    }
                    if script in config.SCRIPT_MAPPING_COVERAGE_EXCEPTIONS
                    else {}
                ),
                **(config.SCRIPT_READING_IDENTITIES.get(script, {})),
                **(
                    {"group": "specialist", "group_note": config.SPECIALIST_GROUP_NOTE}
                    if script in config.SPECIALIST_SCRIPTS
                    else {}
                ),
                **(
                    {"chapter_furniture": furniture_by_script[script]}
                    if script in furniture_by_script
                    else {}
                ),
            }
            for script in scripts
        ],
        "translations": {
            "count": len(index),
            "languages": len({entry["code"] for entry in index}),
            "index": "/translations/index.json",
        },
        "transliteration": {
            "count": transliteration_manifest["count"],
            "index": "/transliteration/index.json",
        },
        "audio": "/audio/reciters.json" if audio else None,
        "license": {
            "project": "CC BY-SA 4.0",
            "text": {
                "source": (
                    "tanzil.net, quran.kemenag.go.id, DigitalKhatt (MIT) and "
                    "quranpedia.net -- see /meta/sources.json for the verdict on each"
                ),
                "status": config.TANZIL_TEXT.status,
                "url": config.TANZIL_TEXT.url,
            },
        },
        "attribution": (
            "Quran text and chapter metadata: Tanzil.net (CC-BY 3.0, verbatim); the "
            "Mushaf Standar Indonesia script, LPMQ / Kementerian Agama RI; the Indo-Pak "
            "script, DigitalKhatt (MIT); and the Warsh, Qalun, al-Duri and Hafs Nastaliq "
            "texts, Qur'anpedia.net (https://quranpedia.net). Exact dump versions, mushaf "
            "identities and archive checksums are recorded per snapshot in /meta/sources.json. "
            "Translations: each "
            "edition's publisher, credited in /translations/index.json. Audio: linked "
            "from EveryAyah, Islamic Network and MP3Quran; no audio is hosted here."
        ),
    }
    write_json(out_dir / "manifest.json", manifest, pretty=pretty)

    write_json(
        out_dir / "meta" / "sources.json",
        sources_manifest(scripts=scripts, editions=editions),
        pretty=pretty,
    )
    write_json(out_dir / "meta" / "qa.json", qa.manifest(), pretty=pretty)

    if audio:
        from .audio import build_audio_index

        build_audio_index(out_dir / "audio", pretty=pretty)

    (out_dir / "_headers").write_text(_HEADERS, encoding="utf-8")


def _script_license(script: str) -> dict[str, str]:
    """The licence object published beside a script, with Tanzil's notice where required."""
    license_ = config.SCRIPT_LICENSES[script]

    return {
        "status": license_.status,
        "url": license_.url,
        "attribution": config.SCRIPT_ATTRIBUTIONS[script],
        **({"notice": config.TANZIL_NOTICE} if script in config.TANZIL_VARIANTS else {}),
    }


def _catalogue_metadata() -> dict[str, dict[str, Any]]:
    """Per-edition catalogue fields: direction, version, and the source description."""
    if not config.quranenc_catalogue_path().exists():
        return {}
    from .quranenc import load_catalogues, merged_catalogue

    return {entry["key"]: entry for entry in merged_catalogue(load_catalogues())["translations"]}


def _withheld_entry(edition: config.Edition) -> dict[str, Any]:
    """One withheld edition as a catalogue entry."""
    entry = {
        "edition": edition.lang,
        "author": edition.author,
        "status": edition.license.status,
        "license_url": edition.license.url,
    }
    if edition.availability != "published":
        entry["availability"] = edition.availability
        entry["reason"] = edition.availability_reason
    return entry


def _catalogue_withheld_entries(published_langs: set[str]) -> list[dict[str, Any]]:
    """Report technically incomplete supplemental editions without publishing their bytes."""
    if not config.quranenc_catalogue_path().exists():
        return []
    from .quranenc import catalogue_editions, load_catalogues, merged_catalogue

    return [
        _withheld_entry(edition)
        for edition in catalogue_editions(merged_catalogue(load_catalogues()))
        if not edition.available and edition.lang not in published_langs
    ]


def sources_manifest(
    *,
    scripts: list[str],
    editions: list[config.Edition],
) -> dict[str, Any]:
    """Provenance and licence status for the sources behind the published site.

    Takes what the build actually published instead of recomputing it, so the manifest
    describes the tree it is written into.
    """
    versions = {key: entry.get("version", "n/a") for key, entry in _catalogue_metadata().items()}
    published_langs = {edition.lang for edition in editions}

    return {
        "text": {
            "source": (
                "https://tanzil.net/pub/download/, https://quran.kemenag.go.id/, "
                "https://github.com/DigitalKhatt/digitalkhatt-js and "
                "https://api.quranpedia.net/dumps"
            ),
            "status": config.TANZIL_TEXT.status,
            "license": config.TANZIL_TEXT.text,
            "license_url": config.TANZIL_TEXT.url,
            "scripts": scripts,
            "script_licenses": [
                {
                    "script": script,
                    "status": config.SCRIPT_LICENSES[script].status,
                    "license_url": config.SCRIPT_LICENSES[script].url,
                    "verses": config.SCRIPT_VERSES[script],
                }
                for script in config.SCRIPT_IDS
            ],
            "withheld_scripts": [script for script in config.SCRIPT_IDS if script not in scripts],
            "note": (
                "Every script is published on the strength of its own grant, and the "
                "grants differ in kind. Six Tanzil variants: one licence, CC-BY 3.0 "
                "verbatim, because the grant is per text rather than per variant. Qur'an "
                "Kemenag's Mushaf Standar Indonesia: the ministry's own publishing "
                "regulation (PMA 44/2016 Pasal 8(1)) holds the mushaf text to be "
                "uncopyrightable, and only its plain UTF-8 text is taken -- no fonts, no "
                "mushaf layout, no ornaments, which Pasal 8(2) reserves to the publisher. "
                "The Indo-Pak script is DigitalKhatt's own typesetting under its "
                "repository's MIT licence. Warsh and Qalun are Qur'anpedia.net's dumps "
                "under their data licence, which requires crediting them and stating the "
                "dump version; they are riwayat rather than orthographies and number 6,214 "
                "ayahs, so their per-surah counts differ from /chapters.json, which is "
                "Hafs metadata."
            ),
        },
        "chapters": {
            "source": "https://tanzil.net/res/text/metadata/quran-data.xml",
            "status": config.TANZIL_TEXT.status,
            "license_url": config.TANZIL_TEXT.url,
        },
        "transliteration": {
            "status": "withheld",
            "reason": "No transliteration with a redistribution grant is published yet.",
            "index": "/transliteration/index.json",
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
        "withheld": _catalogue_withheld_entries(published_langs),
    }
