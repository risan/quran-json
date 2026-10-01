"""QuranEnc.com as the translation source.

QuranEnc is the only translation source found whose terms grant re-publication (verbatim,
with attribution and the version number recorded). Its bulk endpoint is a zip containing
a SQLite database per translation, so the whole catalogue is 75 requests rather than one
request per surah.

Each translation record also carries the `version` string that condition 3 of the licence
requires us to republish, so it is kept in the snapshot and surfaced in the published
provenance.  The provider's discovery endpoint is not a complete catalogue, so a small
manually reviewed catalogue is kept alongside it for editions whose official bulk archives
are present but omitted from that endpoint.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Any, Final

from . import config

if TYPE_CHECKING:
    from .http import Fetcher

__all__ = [
    "CATALOGUE_URL",
    "SURA_URL",
    "TERMS_URL",
    "api_gatherer",
    "catalogue_editions",
    "load_catalogues",
    "merged_catalogue",
    "parse_catalogue",
    "parse_complete_translation",
    "parse_complete_translation_allow_empty",
    "parse_sura",
    "parse_translation",
    "validate_catalogue",
    "validate_translation",
]

CATALOGUE_URL = "https://quranenc.com/api/v1/translations/list"
TERMS_URL: Final = "https://quranenc.com/en/home/api"

#: One surah of one translation. Some editions are listed on the website and served here,
#: yet have no SQLite archive, so their 114 surahs are fetched one by one.
SURA_URL: Final = "https://quranenc.com/api/v1/translation/sura/{key}/{sura}"

#: How a catalogue entry's text is obtained: its SQLite archive, or surah by surah.
INGEST_MODES: Final = ("archive", "api")

#: The dataset generation these editions belong to.
EDITION_PREFIX = "quranenc"


def parse_catalogue(raw: bytes) -> dict[str, Any]:
    """Keep the fields needed to fetch, attribute, and version each translation."""
    import orjson

    payload = orjson.loads(raw)

    catalogue = {
        "translations": [
            {
                "key": entry["key"],
                "lang": entry["language_iso_code"],
                "direction": entry["direction"],
                "version": entry["version"],
                "title": entry["title"],
                "description": entry["description"],
                "database_url": entry["database_url"],
            }
            for entry in payload["translations"]
        ]
    }
    validate_catalogue(catalogue)
    return catalogue


def validate_catalogue(catalogue: dict[str, Any], *, expected_keys: set[str] | None = None) -> None:
    """Fail closed on an incomplete or colliding QuranEnc catalogue.

    The canonical endpoint and the supplemental snapshot use the same normalized shape.  A
    catalogue is metadata, but a duplicate key would make the source selected by a build
    depend on list order, so it is treated as an import error.
    """
    entries = catalogue.get("translations")
    if not isinstance(entries, list) or not entries:
        raise ValueError("quranenc catalogue has no translations")

    keys: set[str] = set()
    required = {"key", "lang", "direction", "version", "title", "description", "database_url"}
    for entry in entries:
        if not isinstance(entry, dict) or not required <= entry.keys():
            raise ValueError("quranenc catalogue entry is missing required metadata")
        key = entry["key"]
        if not isinstance(key, str) or not key or key in keys:
            raise ValueError(f"quranenc catalogue duplicate/invalid key: {key!r}")
        keys.add(key)
        if entry["direction"] not in {"ltr", "rtl"}:
            raise ValueError(f"quranenc catalogue invalid direction for {key!r}")
        if not all(isinstance(entry[field], str) and entry[field] for field in required - {"key"}):
            raise ValueError(f"quranenc catalogue has empty metadata for {key!r}")
        ingest = entry.get("ingest", "archive")
        if ingest not in INGEST_MODES:
            raise ValueError(f"quranenc catalogue invalid ingest mode for {key!r}")
        if ingest == "api":
            if "{sura}" not in entry["database_url"]:
                raise ValueError(f"quranenc API entry has no surah URL pattern for {key!r}")
            if "archive_sha256" in entry or "archive_bytes" in entry:
                raise ValueError(f"quranenc API entry cannot pin an archive for {key!r}")
        availability = entry.get("availability", "published")
        if availability not in {"published", "withheld"}:
            raise ValueError(f"quranenc catalogue invalid availability for {key!r}")
        if availability == "withheld" and not entry.get("availability_reason"):
            raise ValueError(f"quranenc withheld entry has no reason for {key!r}")
        if entry.get("allow_empty", False) and availability != "withheld":
            raise ValueError(
                f"quranenc entry allowing empty rows must be explicitly withheld: {key!r}"
            )

    if expected_keys is not None and keys != expected_keys:
        raise ValueError(f"quranenc catalogue keys differ: expected {sorted(expected_keys)}")


def merged_catalogue(catalogues: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Merge canonical and manually registered catalogues with a collision gate."""
    entries: list[dict[str, Any]] = []
    seen: set[str] = set()
    for catalogue in catalogues:
        validate_catalogue(catalogue)
        for entry in catalogue["translations"]:
            if entry["key"] in seen:
                raise ValueError(f"quranenc catalogue key appears more than once: {entry['key']}")
            seen.add(entry["key"])
            entries.append(entry)
    if not entries:
        raise ValueError("quranenc has no translation catalogues")
    return {"translations": entries}


def load_catalogues() -> list[dict[str, Any]]:
    """Load the endpoint snapshot and optional reviewed supplemental snapshot."""
    from .jsonio import read_json

    paths = (config.quranenc_catalogue_path(), config.quranenc_supplemental_catalogue_path())
    return [read_json(path) for path in paths if path.exists()]


def validate_translation(
    verses: dict[str, list[dict[str, Any]]],
    *,
    chapter_counts: dict[int, int],
    expected_total: int = 6236,
    allow_empty: bool = False,
) -> None:
    """Validate a complete 114-surah translation against the Hafs reference.

    The SQLite archive is the source of truth for wording and footnotes.  This check only
    validates identity and completeness, so it cannot accidentally rewrite a translation
    while making it fit an assumed array length.
    """
    expected_chapters = set(range(1, 115))
    actual_chapters = {int(key) for key in verses}
    if actual_chapters != expected_chapters:
        raise ValueError("quranenc translation must contain exactly chapters 1..114")

    total = 0
    for chapter in range(1, 115):
        entries = verses.get(str(chapter), [])
        expected_count = chapter_counts[chapter]
        if len(entries) != expected_count:
            raise ValueError(
                f"quranenc translation chapter {chapter}: expected {expected_count} verses, "
                f"got {len(entries)}"
            )
        for verse, entry in enumerate(entries, start=1):
            if entry.get("chapter") != chapter or entry.get("verse") != verse:
                raise ValueError(f"quranenc translation has invalid id at {chapter}:{verse}")
            if not isinstance(entry.get("text"), str) or (
                not allow_empty and not entry["text"].strip()
            ):
                raise ValueError(f"quranenc translation has empty text at {chapter}:{verse}")
            if "footnotes" in entry and not isinstance(entry["footnotes"], str):
                raise ValueError(f"quranenc translation has invalid footnotes at {chapter}:{verse}")
        total += len(entries)

    if total != expected_total:
        raise ValueError(f"quranenc translation expected {expected_total} verses, got {total}")


def _reference_chapter_counts() -> dict[int, int]:
    from .jsonio import read_json

    return {
        int(chapter["id"]): int(chapter["total_verses"])
        for chapter in read_json(config.tanzil_chapters_path())["chapters"]
    }


def parse_translation(
    raw: bytes,
    *,
    chapter_counts: dict[int, int] | None = None,
    expected_total: int = 6236,
    allow_empty: bool = False,
) -> dict[str, list[dict[str, Any]]]:
    """Extract one translation's verses from its zipped SQLite database.

    `io`, `zipfile` and `sqlite3` are imported here rather than at module scope because
    this is the only function that needs them, and `catalogue_editions` is imported on the
    render path. Importing `sqlite3` there would hard-fail on any interpreter built without
    the SQLite extension -- notably Cloudflare's build image, whose CPython 3.13 has no
    `_sqlite3` -- even though rendering only reads the already-parsed JSON snapshots.
    """
    import io
    import sqlite3
    import zipfile

    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        members = [name for name in archive.namelist() if name.endswith(".sqlite")]
        if not members:
            raise ValueError("translation archive contains no .sqlite member")
        if len(members) != 1:
            raise ValueError("translation archive must contain exactly one .sqlite member")
        member = members[0]
        database = archive.read(member)

    connection = sqlite3.connect(":memory:")
    try:
        connection.deserialize(database)
        columns = {row[1] for row in connection.execute("PRAGMA table_info(translations)")}
        missing = {"sura", "aya", "translation"} - columns
        if missing:
            raise ValueError(f"translations table is missing columns: {sorted(missing)}")

        has_footnotes = "footnotes" in columns
        query = (
            "SELECT sura, aya, translation, footnotes FROM translations ORDER BY sura, aya"
            if has_footnotes
            else "SELECT sura, aya, translation, '' FROM translations ORDER BY sura, aya"
        )

        verses: dict[str, list[dict[str, Any]]] = {}
        seen: set[tuple[int, int]] = set()
        for sura, aya, text, footnotes in connection.execute(query):
            chapter = int(sura)
            verse = int(aya)
            if (chapter, verse) in seen:
                raise ValueError(f"translation archive has duplicate verse {chapter}:{verse}")
            seen.add((chapter, verse))
            entry: dict[str, Any] = {
                "chapter": chapter,
                "verse": verse,
                "text": text,
            }
            if footnotes:
                entry["footnotes"] = footnotes
            verses.setdefault(str(chapter), []).append(entry)

        if chapter_counts is not None:
            validate_translation(
                verses,
                chapter_counts=chapter_counts,
                expected_total=expected_total,
                allow_empty=allow_empty,
            )
        return verses
    finally:
        connection.close()


def parse_sura(raw: bytes, *, sura: int) -> list[dict[str, Any]]:
    """Parse one surah from the per-surah API into verse records, footnotes kept.

    The response is checked row by row, because a truncated or reshaped answer must stop
    the import rather than leave a translation with silently missing verses.
    """
    import orjson

    payload = orjson.loads(raw)
    rows = payload.get("result") if isinstance(payload, dict) else None
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"quranenc surah {sura} response has no result rows")

    verses: list[dict[str, Any]] = []
    seen: set[int] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError(f"quranenc surah {sura} response has a malformed row")

        try:
            chapter = int(row["sura"])
            verse = int(row["aya"])
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(f"quranenc surah {sura} row has no valid sura/aya") from error

        if chapter != sura:
            raise ValueError(f"quranenc surah {sura} response contains verse {chapter}:{verse}")
        if verse in seen:
            raise ValueError(f"quranenc surah {sura} response repeats verse {verse}")
        seen.add(verse)

        text = row.get("translation")
        footnotes = row.get("footnotes")
        if not isinstance(text, str):
            raise ValueError(f"quranenc translation has no text at {chapter}:{verse}")
        if footnotes is not None and not isinstance(footnotes, str):
            raise ValueError(f"quranenc translation has invalid footnotes at {chapter}:{verse}")

        entry: dict[str, Any] = {"chapter": chapter, "verse": verse, "text": text}
        if footnotes:
            entry["footnotes"] = footnotes
        verses.append(entry)

    return sorted(verses, key=lambda entry: entry["verse"])


def api_gatherer(
    key: str, *, allow_empty: bool = False
) -> Callable[[Fetcher], dict[str, list[dict[str, Any]]]]:
    """A `FetchTask.gather` that crawls the 114 surahs of one translation.

    The result has the same shape as `parse_translation`, so the snapshot is
    indistinguishable from one imported from an archive.
    """

    def gather(client: Fetcher) -> dict[str, list[dict[str, Any]]]:
        verses: dict[str, list[dict[str, Any]]] = {}
        for sura in range(1, 115):
            raw = client.get_bytes(SURA_URL.format(key=key, sura=sura))
            verses[str(sura)] = parse_sura(raw, sura=sura)

        validate_translation(
            verses,
            chapter_counts=_reference_chapter_counts(),
            allow_empty=allow_empty,
        )
        return verses

    return gather


def parse_complete_translation(
    raw: bytes, *, allow_empty: bool = False
) -> dict[str, list[dict[str, Any]]]:
    """Parse an official archive and require all 6,236 Hafs-keyed ayahs."""
    return parse_translation(
        raw,
        chapter_counts=_reference_chapter_counts(),
        expected_total=6236,
        allow_empty=allow_empty,
    )


def parse_complete_translation_allow_empty(raw: bytes) -> dict[str, list[dict[str, Any]]]:
    """Structural complete import for a reviewed candidate that contains blank rows."""
    return parse_complete_translation(raw, allow_empty=True)


def catalogue_editions(
    catalogue: dict[str, Any], *, include_withheld: bool = True
) -> list[config.Edition]:
    """Build Edition records for every translation QuranEnc grants us."""
    validate_catalogue(catalogue)
    return [
        config.Edition(
            lang=entry["key"],
            slug=entry["key"],
            code=entry["lang"],
            author=entry["title"],
            source=entry.get("browse_url", f"https://quranenc.com/en/browse/{entry['key']}/"),
            license=config.QURANENC,
            kind="quranenc",
            availability=entry.get("availability", "published"),
            availability_reason=entry.get("availability_reason", ""),
        )
        for entry in catalogue["translations"]
        if include_withheld or entry.get("availability", "published") == "published"
    ]
