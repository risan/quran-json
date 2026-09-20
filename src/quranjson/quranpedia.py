"""Qur'anpedia.net's text dumps.

The repository carries four distinct Quranpedia texts: the two Maghribi riwayat Warsh and
Qalun, Hafs Nastaliq (mushaf 3), and al-Duri (mushaf 6). A different reading changes the
consonants and vowels of the text and, in places, where one ayah ends and the next begins.
The Nastaliq text is a distinct digital edition even though its reading is Hafs; it must not
replace the existing Indo-Pak text or imply byte compatibility with a printed edition.

The dumps are gzipped JSON files at ``https://api.quranpedia.net/dumps``. Republishing a
downloadable dataset requires crediting Quranpedia.net and stating the exact dump version.
The fonts and per-page SVG packs named by a mushaf are separate assets and are not included
here. Every parser gate below is deliberately source-driven: a changed count, identity,
mapping, or archive hash fails a refresh rather than silently relabelling another edition.
"""

from __future__ import annotations

import gzip
from collections import Counter
from collections.abc import Callable
from typing import Any, Final, cast

import orjson

from . import config

__all__ = [
    "DUMPS_URL",
    "DUMP_METADATA",
    "LICENSE_URL",
    "MOUNT",
    "VERSE_COUNT",
    "dump_url",
    "parse_dump",
    "parse_dump_for",
]

DUMPS_URL: Final = "https://api.quranpedia.net/dumps"
LICENSE_URL: Final = f"{DUMPS_URL}/LICENSE.md"

#: Quranpedia serves one dump per mushaf, numbered, with the catalogue at
#: ``/dumps/mushafs-index.json.gz``.
MOUNT: Final[dict[str, int]] = {
    "warsh": 4,
    "qalun": 7,
    "hafs-nastaliq": 3,
    "duri": 6,
}

#: Pinned counts after parsing each dump. The al-Duri count is intentionally not copied from
#: the public catalogue, whose count metadata conflicts with the text dump.
VERSE_COUNT: Final[dict[str, int]] = {
    "warsh": 6214,
    "qalun": 6214,
    "hafs-nastaliq": 6236,
    "duri": 6218,
}

#: Source-faithful exceptions to a complete Hafs join. Al-Duri's first chapter carries the
#: source's seven rows but maps to Hafs 2..7 with the final row covering Hafs 7 again; adding
#: Hafs 1 would fabricate a join. The verse map remains published for auditability.
MAPPING_DIVERGENCE: Final[dict[str, tuple[int, ...]]] = {"duri": (1,)}

#: Raw archive identity from the Quranpedia manifest fetched with the committed snapshots.
#: A refresh must update this table deliberately rather than silently replacing a text.
DUMP_METADATA: Final[dict[str, dict[str, Any]]] = {
    "warsh": {
        "mushaf_id": 4,
        "name": "Warsh",
        "dump_version": "2026-09-18",
    },
    "qalun": {
        "mushaf_id": 7,
        "name": "Qalun",
        "dump_version": "2026-09-18",
    },
    "hafs-nastaliq": {
        "mushaf_id": 3,
        "name": "مصحف حفص نستعليق",
        "dump_version": "2026-09-20",
        "built_at": "2026-09-20T03:46:39+00:00",
        "archive_sha256": "fbec857dd613946604fd4c004d7322778ecf1c058c46080e30702e9bf9959b02",
        "archive_bytes": 395980,
        "description": "مصحف حفص نستعليق — not matching the printed edition",
        "bismillah": "بِسْمِ اللّٰهِ الرَّحْمٰنِ الرَّحِيْمِ \u0600",
    },
    "duri": {
        "mushaf_id": 6,
        "name": "مصحف الدوري",
        "dump_version": "2026-09-20",
        "built_at": "2026-09-20T03:46:42+00:00",
        "archive_sha256": "f6024036b0040afea6af7973abd78b883ab2a0837ae72f6360b69e597c53999a",
        "archive_bytes": 421957,
        "description": "مصحف الدوري — al-Duri from Abu Amr, own source numbering",
        "bismillah": "بِسۡمِ اِ۬للَّهِ اِ۬لرَّحۡمَٰنِ اِ۬لرَّحِيمِ ",
    },
}

CHAPTER_COUNT: Final = 114


def dump_url(script: str) -> str:
    """Download URL for one Quranpedia dump."""
    return f"{DUMPS_URL}/mushafs-{MOUNT[script]}.json.gz"


def _hafs_chapter_counts() -> dict[int, int]:
    """Read canonical Hafs chapter lengths without making a network request."""
    from .jsonio import read_json

    return {
        int(chapter["id"]): int(chapter["total_verses"])
        for chapter in read_json(config.tanzil_chapters_path())["chapters"]
    }


def _validate_mapping(
    chapters: dict[str, list[dict[str, Any]]],
    chapter_counts: dict[int, int],
    *,
    script: str | None = None,
) -> None:
    """Validate a source-provided per-chapter Hafs map, retaining legitimate overlaps."""
    for chapter_key, verses in chapters.items():
        chapter = int(chapter_key)
        flattened: list[int] = []
        for verse in verses:
            numbers = verse["number_in_hafs"]
            if not numbers or numbers != sorted(set(numbers)):
                raise ValueError(
                    f"quranpedia: invalid number_in_hafs at {chapter}:{verse['verse']}"
                )
            if script == "hafs-nastaliq" and numbers != [verse["verse"]]:
                raise ValueError(
                    f"quranpedia: Hafs Nastaliq map is not native at {chapter}:{verse['verse']}"
                )
            if not all(isinstance(number, int) for number in numbers):
                raise ValueError(
                    f"quranpedia: non-integer number_in_hafs at {chapter}:{verse['verse']}"
                )
            if not all(1 <= number <= chapter_counts[chapter] for number in numbers):
                raise ValueError(
                    f"quranpedia: out-of-range number_in_hafs at {chapter}:{verse['verse']}"
                )
            flattened.extend(numbers)

        # Adjacent source rows may intentionally overlap a Hafs id at a split/merge boundary.
        if flattened != sorted(flattened):
            raise ValueError(f"quranpedia: non-monotonic number_in_hafs in chapter {chapter}")
        exception = next(
            (
                item
                for item in config.SCRIPT_MAPPING_COVERAGE_EXCEPTIONS.get(script or "", ())
                if item["chapter"] == chapter
            ),
            None,
        )
        expected = set(range(1, chapter_counts[chapter] + 1))
        if exception is None:
            if set(flattened) != expected:
                raise ValueError(f"quranpedia: incomplete Hafs mapping in chapter {chapter}")
            continue

        missing = set(cast(tuple[int, ...], exception["missing_hafs"]))
        repeated = set(cast(tuple[int, ...], exception["repeated_hafs"]))
        if set(flattened) != expected - missing:
            raise ValueError(f"quranpedia: unexpected missing Hafs ids in chapter {chapter}")
        counts = Counter(flattened)
        if any(counts[number] != 2 for number in repeated) or any(
            counts[number] != 1 for number in expected - missing - repeated
        ):
            raise ValueError(f"quranpedia: unexpected Hafs overlap in chapter {chapter}")


def parse_dump(raw: bytes, *, script: str | None = None) -> dict[str, list[dict[str, Any]]]:
    """Parse a gzipped dump into ``{chapter: verses}``.

    ``script`` activates identity and pinned-count checks. The optional form keeps this
    parser convenient for small unit fixtures while every production fetch task uses the
    named form through :func:`parse_dump_for`.
    """
    payload = orjson.loads(gzip.decompress(raw))
    surahs = payload["data"]["surahs"]

    if script is not None:
        if script not in MOUNT:
            raise ValueError(f"quranpedia: unknown script {script!r}")
        metadata = DUMP_METADATA.get(script)
        if metadata is not None:
            if "mushaf_id" in metadata and int(payload["data"]["id"]) != metadata["mushaf_id"]:
                raise ValueError(f"quranpedia: dump is not mushaf {metadata['mushaf_id']}")
            if (
                metadata.get("dump_version")
                and payload["license"].get("version") != metadata["dump_version"]
            ):
                raise ValueError(f"quranpedia: unexpected dump version for {script}")
            if metadata.get("name") and payload["data"].get("name") != metadata["name"]:
                raise ValueError(f"quranpedia: unexpected mushaf name for {script}")
            if (
                metadata.get("bismillah")
                and payload["data"].get("bismillah") != metadata["bismillah"]
            ):
                raise ValueError(f"quranpedia: unexpected bismillah for {script}")

    if len(surahs) != CHAPTER_COUNT:
        raise ValueError(f"quranpedia: expected {CHAPTER_COUNT} surahs, got {len(surahs)}")

    chapters: dict[str, list[dict[str, Any]]] = {}

    for surah in surahs:
        chapter = int(surah["id"])
        if chapter < 1 or chapter > CHAPTER_COUNT or str(chapter) in chapters:
            raise ValueError(f"quranpedia: duplicate/out-of-range chapter {chapter}")
        verses: list[dict[str, Any]] = []

        for ayah in surah["ayahs"]:
            text = ayah["text"].strip()
            if not text:
                raise ValueError(f"quranpedia: empty verse at {chapter}:{ayah['number']}")

            mapping = ayah.get("number_in_hafs")
            if not isinstance(mapping, list) or not mapping:
                raise ValueError(
                    f"quranpedia: missing number_in_hafs at {chapter}:{ayah['number']}"
                )

            verses.append(
                {
                    "chapter": chapter,
                    "verse": int(ayah["number"]),
                    "text": text,
                    "number_in_hafs": list(mapping),
                }
            )

        if [verse["verse"] for verse in verses] != list(range(1, len(verses) + 1)):
            raise ValueError(f"quranpedia: chapter {chapter} is not numbered 1..n")

        chapters[str(chapter)] = verses

    if set(map(int, chapters)) != set(range(1, CHAPTER_COUNT + 1)):
        raise ValueError("quranpedia: chapters are not exactly 1..114")

    total = sum(len(verses) for verses in chapters.values())
    expected = VERSE_COUNT[script] if script is not None else 6214
    if total != expected:
        raise ValueError(f"quranpedia: expected {expected} verses, got {total}")

    _validate_mapping(chapters, _hafs_chapter_counts(), script=script)
    return chapters


def parse_dump_for(script: str) -> Callable[[bytes], dict[str, list[dict[str, Any]]]]:
    """Return a parser callable for a named Quranpedia script."""

    def parse(raw: bytes) -> dict[str, list[dict[str, Any]]]:
        return parse_dump(raw, script=script)

    return parse
