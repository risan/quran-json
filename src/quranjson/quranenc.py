"""QuranEnc.com as the translation source.

QuranEnc is the only translation source found whose terms grant re-publication (verbatim,
with attribution and the version number recorded). Its bulk endpoint is a zip containing
a SQLite database per translation, so the whole catalogue is 75 requests rather than one
request per surah.

Each translation record also carries the `version` string that condition 3 of the licence
requires us to republish, so it is kept in the snapshot and surfaced in the published
provenance.
"""

from __future__ import annotations

from typing import Any

from . import config

__all__ = ["CATALOGUE_URL", "catalogue_editions", "parse_catalogue", "parse_translation"]

CATALOGUE_URL = "https://quranenc.com/api/v1/translations/list"

#: The dataset generation these editions belong to.
EDITION_PREFIX = "quranenc"


def parse_catalogue(raw: bytes) -> dict[str, Any]:
    """Keep the fields needed to fetch, attribute, and version each translation."""
    import orjson

    payload = orjson.loads(raw)

    return {
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


def parse_translation(raw: bytes) -> dict[str, list[dict[str, Any]]]:
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
        member = next((name for name in archive.namelist() if name.endswith(".sqlite")), None)
        if member is None:
            raise ValueError("translation archive contains no .sqlite member")
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
        for sura, aya, text, footnotes in connection.execute(query):
            entry: dict[str, Any] = {
                "chapter": int(sura),
                "verse": int(aya),
                "text": text,
            }
            if footnotes:
                entry["footnotes"] = footnotes
            verses.setdefault(str(int(sura)), []).append(entry)

        return verses
    finally:
        connection.close()


def catalogue_editions(catalogue: dict[str, Any]) -> list[config.Edition]:
    """Build Edition records for every translation QuranEnc grants us."""
    return [
        config.Edition(
            lang=entry["key"],
            slug=entry["key"],
            author=entry["title"],
            source=f"https://quranenc.com/en/browse/{entry['key']}/",
            license=config.QURANENC,
        )
        for entry in catalogue["translations"]
    ]


def featured_keys(catalogue: dict[str, Any]) -> tuple[str, ...]:
    """One representative translation per major language, for the per-verse index.

    `verses/{n}.json` embeds every translation it covers, so covering all 75 would
    duplicate the whole corpus once more (~141 MB). The full set stays reachable through
    `chapters/{key}/{n}.json`.
    """
    chosen: dict[str, str] = {}

    for entry in catalogue["translations"]:
        chosen.setdefault(entry["lang"], entry["key"])

    return tuple(chosen[lang] for lang in config.FEATURED_LANGS if lang in chosen)
