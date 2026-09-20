"""Registry and fail-closed importers for transliteration candidate sources.

The registry describes what a transliteration represents without treating a language,
source host, or software licence as a corpus grant.  Existing Kemenag and Tanzil English
snapshots are read in place.  Restricted Tanzil files and unknown QUL exports may be
validated from a user-supplied local file, but this module never downloads authenticated
QUL previews or turns an unreviewed word layer into an ayah string.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Final, Literal

import orjson

from . import config

__all__ = [
    "CANDIDATES",
    "REGISTRY_PATH",
    "Candidate",
    "ImportedTransliteration",
    "TransliterationImportError",
    "candidate",
    "import_file",
    "parse_qul_ayah_json",
    "parse_qul_word_json",
    "parse_tanzil_pipe",
    "published_candidates",
    "validate_ayah_records",
    "validate_markup",
    "validate_word_records",
]

Granularity = Literal["ayah", "word", "unknown"]
RightsStatus = Literal["granted", "restricted", "unknown"]
CandidateMode = Literal["existing_snapshot", "private_local_file", "manual_export", "alias"]

CHAPTER_COUNT: Final = 114
VERSE_COUNT: Final = 6236
_AYAH_KEY = re.compile(r"^(\d+):(\d+)$")
_WORD_KEY = re.compile(r"^(\d+):(\d+):(\d+)$")

REGISTRY_PATH: Final = config.DATA / "transliteration-candidates" / "registry.json"


class TransliterationImportError(ValueError):
    """Raised when a candidate file cannot be proven complete and correctly keyed."""


@dataclass(frozen=True, slots=True)
class Candidate:
    """A source descriptor; ``rights_status`` is the corpus status, not software status."""

    id: str
    name: str
    source_url: str
    source_kind: str
    snapshot_ref: str | None
    import_mode: CandidateMode
    author: str | None
    rights_status: RightsStatus
    rights_url: str
    rights_note: str
    audience_language: str | None
    purpose: str
    granularity: Granularity
    markup: str
    preserve_whitespace: bool
    scheme: Mapping[str, Any] | None
    reading: Mapping[str, Any]
    expected_chapters: int
    expected_verses: int
    markup_tags: tuple[str, ...] = ()
    alias_of: str | None = None
    dedupe_candidate_of: str | None = None

    @property
    def snapshot_path(self) -> Path | None:
        """Resolve a committed snapshot reference, if this candidate reuses one."""
        return config.ROOT / self.snapshot_ref if self.snapshot_ref else None

    @property
    def can_publish(self) -> bool:
        """Whether the adapter may offer the candidate to the default publisher."""
        return self.rights_status == "granted" and self.snapshot_path is not None


@dataclass(frozen=True, slots=True)
class ImportedTransliteration:
    """A validated local import and its source checksum.

    ``records`` is a tuple of ayah records for ayah candidates or word records for word
    candidates.  The shape stays explicit so a caller cannot accidentally concatenate words
    and present them as a reviewed ayah transcription.
    """

    candidate: Candidate
    records: tuple[dict[str, Any], ...]
    sha256: str

    @property
    def granularity(self) -> Granularity:
        return self.candidate.granularity


def _load_registry() -> tuple[Candidate, ...]:
    payload = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    if payload.get("schema_version") != 1 or not isinstance(payload.get("candidates"), list):
        raise TransliterationImportError("transliteration registry has an unsupported shape")

    records: list[Candidate] = []
    seen: set[str] = set()
    for raw in payload["candidates"]:
        if not isinstance(raw, dict):
            raise TransliterationImportError("transliteration registry has a non-object entry")
        item = dict(raw)
        item["markup_tags"] = tuple(item.get("markup_tags", ()))
        item.setdefault("alias_of", None)
        item.setdefault("dedupe_candidate_of", None)
        value = Candidate(**item)
        if value.id in seen:
            raise TransliterationImportError(f"duplicate transliteration candidate: {value.id}")
        if value.expected_chapters != CHAPTER_COUNT or value.expected_verses != VERSE_COUNT:
            raise TransliterationImportError(f"{value.id}: unexpected canonical coverage")
        if value.alias_of and value.alias_of == value.id:
            raise TransliterationImportError(f"{value.id}: candidate aliases itself")
        if value.dedupe_candidate_of and value.dedupe_candidate_of == value.id:
            raise TransliterationImportError(f"{value.id}: dedupe target is itself")
        seen.add(value.id)
        records.append(value)

    known = seen
    for value in records:
        if value.alias_of and value.alias_of not in known:
            raise TransliterationImportError(f"{value.id}: unknown alias target {value.alias_of}")
        if value.dedupe_candidate_of and value.dedupe_candidate_of not in known:
            raise TransliterationImportError(
                f"{value.id}: unknown dedupe target {value.dedupe_candidate_of}"
            )
    return tuple(records)


CANDIDATES: Final[tuple[Candidate, ...]] = _load_registry()


def candidate(candidate_id: str) -> Candidate:
    """Return one candidate by stable id, rejecting unknown source identities."""
    for item in CANDIDATES:
        if item.id == candidate_id:
            return item
    raise KeyError(f"unknown transliteration candidate: {candidate_id}")


def published_candidates() -> tuple[Candidate, ...]:
    """Return only rights-cleared candidates with a committed validated snapshot.

    This is deliberately separate from :data:`CANDIDATES`: a registry entry records a
    research/import path, while the default CDN must publish only a candidate whose source
    owner and snapshot have both been cleared.
    """
    return tuple(item for item in CANDIDATES if item.can_publish)


def _canonical_counts() -> dict[int, int]:
    path = config.tanzil_chapters_path()
    if not path.is_file():
        raise TransliterationImportError(f"missing canonical chapter metadata: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    chapters = payload.get("chapters")
    if not isinstance(chapters, list):
        raise TransliterationImportError("canonical chapter metadata has no chapters list")
    counts = {int(item["id"]): int(item["total_verses"]) for item in chapters}
    if len(counts) != CHAPTER_COUNT or sum(counts.values()) != VERSE_COUNT:
        raise TransliterationImportError("canonical chapter metadata is incomplete")
    return counts


def _require_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise TransliterationImportError(f"{label}: transliteration text is empty or not text")
    return value


def validate_ayah_records(
    records: Sequence[Mapping[str, Any]],
    *,
    chapter_counts: Mapping[int, int] | None = None,
) -> tuple[dict[str, Any], ...]:
    """Validate ordered ``chapter, verse, text`` records without changing their text.

    The input must already be in source order.  Reordering a malformed source would hide an
    upstream defect, so duplicate, missing, out-of-order, and wrong-chapter rows fail.
    """
    counts = dict(chapter_counts) if chapter_counts is not None else _canonical_counts()
    if not counts or set(counts) != set(range(1, max(counts) + 1)):
        raise TransliterationImportError("ayah import has incomplete chapter metadata")

    normalized: list[dict[str, Any]] = []
    index = 0
    for chapter_id in range(1, max(counts) + 1):
        expected = counts[chapter_id]
        for verse_id in range(1, expected + 1):
            if index >= len(records):
                raise TransliterationImportError(
                    f"ayah import is truncated at {chapter_id}:{verse_id}"
                )
            record = records[index]
            try:
                actual_chapter = int(record["chapter"])
                actual_verse = int(record["verse"])
            except (KeyError, TypeError, ValueError) as error:
                raise TransliterationImportError(
                    f"ayah row {index + 1} has no numeric identity"
                ) from error
            if (actual_chapter, actual_verse) != (chapter_id, verse_id):
                raise TransliterationImportError(
                    f"ayah import expected {chapter_id}:{verse_id}, "
                    f"got {actual_chapter}:{actual_verse}"
                )
            normalized.append(
                {
                    "chapter": chapter_id,
                    "verse": verse_id,
                    "text": _require_text(record.get("text"), f"{chapter_id}:{verse_id}"),
                }
            )
            index += 1

    if index != len(records):
        raise TransliterationImportError(f"ayah import has {len(records) - index} extra rows")
    return tuple(normalized)


def validate_word_records(
    records: Sequence[Mapping[str, Any]],
    *,
    chapter_counts: Mapping[int, int] | None = None,
) -> tuple[dict[str, Any], ...]:
    """Validate word identity and coverage while preserving each word as a separate row."""
    counts = dict(chapter_counts) if chapter_counts is not None else _canonical_counts()
    if not counts or set(counts) != set(range(1, max(counts) + 1)):
        raise TransliterationImportError("word import has incomplete chapter metadata")
    expected_ayahs = {
        (chapter, verse) for chapter, total in counts.items() for verse in range(1, total + 1)
    }
    seen_ayahs: set[tuple[int, int]] = set()
    expected_key: tuple[int, int, int] | None = None
    normalized: list[dict[str, Any]] = []

    for index, record in enumerate(records, start=1):
        try:
            key = (int(record["chapter"]), int(record["verse"]), int(record["word"]))
        except (KeyError, TypeError, ValueError) as error:
            raise TransliterationImportError(f"word row {index} has no numeric identity") from error
        chapter_id, verse_id, word_id = key
        if (chapter_id, verse_id) not in expected_ayahs or word_id < 1:
            raise TransliterationImportError(f"word row {index} has an invalid identity {key}")
        if expected_key is None:
            if word_id != 1:
                raise TransliterationImportError(f"word positions must start at 1 at {key}")
        else:
            previous_chapter, previous_verse, previous_word = expected_key
            if key < expected_key:
                raise TransliterationImportError(f"word rows are out of order at {key}")
            if key[:2] == (previous_chapter, previous_verse):
                if word_id != previous_word + 1:
                    raise TransliterationImportError(f"word positions are not sequential at {key}")
            else:
                if word_id != 1:
                    raise TransliterationImportError(f"word positions must restart at 1 at {key}")
                seen_ayahs.add((previous_chapter, previous_verse))
        normalized.append(
            {
                "chapter": chapter_id,
                "verse": verse_id,
                "word": word_id,
                "text": _require_text(record.get("text"), f"{chapter_id}:{verse_id}:{word_id}"),
            }
        )
        expected_key = key

    if expected_key is not None:
        seen_ayahs.add(expected_key[:2])
    missing = expected_ayahs - seen_ayahs
    if missing:
        first = min(missing)
        raise TransliterationImportError(f"word import has no rows for ayah {first[0]}:{first[1]}")
    return tuple(normalized)


def validate_markup(
    records: Sequence[Mapping[str, Any]],
    *,
    allowed_tags: Sequence[str],
) -> tuple[dict[str, Any], ...]:
    """Check rich-text tags while retaining every source string byte-for-byte.

    This deliberately does not strip or rewrite HTML.  A renderer can apply a separate
    allowlist sanitizer after import; the importer only rejects tags outside the candidate's
    declared semantics.
    """
    allowed = {tag.lower() for tag in allowed_tags}

    class MarkupValidator(HTMLParser):
        def __init__(self) -> None:
            super().__init__(convert_charrefs=False)
            self.open_tags: list[str] = []

        def _check_tag(self, tag: str, attrs: list[tuple[str, str | None]]) -> str:
            normalized = tag.lower()
            if normalized not in allowed:
                raise TransliterationImportError(
                    f"markup tag <{tag}> is outside the declared allowlist"
                )
            if attrs:
                raise TransliterationImportError(
                    f"markup tag <{tag}> has attributes; only plain allowlisted tags are accepted"
                )
            return normalized

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            self.open_tags.append(self._check_tag(tag, attrs))

        def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            raise TransliterationImportError(f"self-closing markup tag <{tag}/> is not accepted")

        def handle_endtag(self, tag: str) -> None:
            normalized = tag.lower()
            if normalized not in allowed:
                raise TransliterationImportError(
                    f"markup tag </{tag}> is outside the declared allowlist"
                )
            if not self.open_tags or self.open_tags[-1] != normalized:
                raise TransliterationImportError(f"markup tag </{tag}> is not balanced")
            self.open_tags.pop()

        def handle_comment(self, data: str) -> None:
            raise TransliterationImportError("markup comments are not accepted")

        def handle_decl(self, decl: str) -> None:
            raise TransliterationImportError("markup declarations are not accepted")

        def handle_pi(self, data: str) -> None:
            raise TransliterationImportError("markup processing instructions are not accepted")

        def unknown_decl(self, data: str) -> None:
            raise TransliterationImportError("unknown markup is not accepted")

    checked: list[dict[str, Any]] = []
    for index, record in enumerate(records, start=1):
        text = _require_text(record.get("text"), f"row {index}")
        if "<" in text and any(
            text.find(">", position) < 0
            for position, character in enumerate(text)
            if character == "<"
        ):
            raise TransliterationImportError(f"row {index}: markup is not closed")
        parser = MarkupValidator()
        try:
            parser.feed(text)
            parser.close()
        except TransliterationImportError as error:
            raise TransliterationImportError(f"row {index}: {error}") from error
        if parser.open_tags:
            raise TransliterationImportError(f"row {index}: markup tags are not balanced")
        checked.append(dict(record))
    return tuple(checked)


def _records_from_keyed_json(payload: Mapping[str, Any], *, word: bool) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    pattern = _WORD_KEY if word else _AYAH_KEY
    for key, text in payload.items():
        if not isinstance(key, str):
            raise TransliterationImportError("keyed transliteration JSON contains a non-string key")
        match = pattern.fullmatch(key)
        if match is None:
            raise TransliterationImportError(f"invalid keyed transliteration identity: {key!r}")
        numbers = tuple(int(value) for value in match.groups())
        record: dict[str, Any] = {"chapter": numbers[0], "verse": numbers[1], "text": text}
        if word:
            record["word"] = numbers[2]
        records.append(record)
    records.sort(key=lambda item: (item["chapter"], item["verse"], item.get("word", 0)))
    return records


def parse_qul_ayah_json(
    payload: Any,
    *,
    chapter_counts: Mapping[int, int] | None = None,
) -> tuple[dict[str, Any], ...]:
    """Parse QUL's documented ``{"surah:ayah": "text"}`` JSON without stripping markup."""
    if not isinstance(payload, dict):
        raise TransliterationImportError("QUL ayah export must be an object keyed by ayah_key")
    return validate_ayah_records(
        _records_from_keyed_json(payload, word=False), chapter_counts=chapter_counts
    )


def parse_qul_word_json(
    payload: Any,
    *,
    chapter_counts: Mapping[int, int] | None = None,
) -> tuple[dict[str, Any], ...]:
    """Parse QUL word JSON and keep word positions; no word concatenation is performed."""
    if not isinstance(payload, dict):
        raise TransliterationImportError("QUL word export must be keyed JSON")
    records = _records_from_keyed_json(payload, word=True)
    return validate_word_records(records, chapter_counts=chapter_counts)


def parse_tanzil_pipe(
    raw: bytes,
    *,
    chapter_counts: Mapping[int, int] | None = None,
) -> tuple[dict[str, Any], ...]:
    """Parse Tanzil's ``surah|ayah|text`` export, retaining Unicode and whitespace."""
    records: list[dict[str, Any]] = []
    for line_number, line in enumerate(raw.decode("utf-8").splitlines(), start=1):
        if not line or line.startswith("#"):
            continue
        parts = line.split("|", 2)
        if len(parts) != 3:
            raise TransliterationImportError(f"Tanzil row {line_number} is not surah|ayah|text")
        try:
            chapter_id, verse_id = int(parts[0]), int(parts[1])
        except ValueError as error:
            raise TransliterationImportError(
                f"Tanzil row {line_number} has invalid identity"
            ) from error
        records.append({"chapter": chapter_id, "verse": verse_id, "text": parts[2]})
    return validate_ayah_records(records, chapter_counts=chapter_counts)


def _parse_grouped_json(payload: Any, *, field: str) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        raise TransliterationImportError("grouped transliteration snapshot must be an object")
    records: list[dict[str, Any]] = []
    for chapter_key, verses in payload.items():
        try:
            chapter_id = int(chapter_key)
        except (TypeError, ValueError) as error:
            raise TransliterationImportError(f"invalid chapter key: {chapter_key!r}") from error
        if not isinstance(verses, list):
            raise TransliterationImportError(f"chapter {chapter_id} is not a row list")
        for row in verses:
            if not isinstance(row, dict):
                raise TransliterationImportError(f"chapter {chapter_id} contains a non-object row")
            records.append(
                {"chapter": chapter_id, "verse": row.get("verse"), "text": row.get(field)}
            )
    return records


def _parse_sqlite(raw: bytes, *, word: bool) -> list[dict[str, Any]]:
    # QUL's official export can be SQLite, but the publish/render interpreter may not ship
    # `_sqlite3`. Keep this acquisition-only dependency out of the module import graph.
    import sqlite3

    connection = sqlite3.connect(":memory:")
    try:
        connection.deserialize(raw)
        table = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name LIMIT 1"
        ).fetchone()
        if table is None:
            raise TransliterationImportError("QUL SQLite export has no data table")
        table_name = str(table[0]).replace('"', '""')
        columns = [row[1] for row in connection.execute(f'PRAGMA table_info("{table_name}")')]
        aliases = {
            "chapter": ("chapter", "surah", "sura", "surah_id", "surah_number"),
            "verse": ("verse", "ayah", "ayah_number"),
            "word": ("word", "position", "word_position", "word_number"),
            "text": ("text", "transliteration"),
        }
        selected: dict[str, str] = {}
        for output, names in aliases.items():
            if output == "word" and not word:
                continue
            source = next((name for name in names if name in columns), None)
            if source is None:
                raise TransliterationImportError(f"QUL SQLite export has no {output} column")
            selected[output] = source
        quoted = ", ".join(f'"{name.replace(chr(34), chr(34) * 2)}"' for name in selected.values())
        rows = connection.execute(f'SELECT {quoted} FROM "{table_name}"').fetchall()
        records = []
        for row in rows:
            records.append(dict(zip(selected, row, strict=True)))
        return records
    finally:
        connection.close()


def _parse_existing(candidate_item: Candidate, path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if candidate_item.source_kind == "kemenag_snapshot":
        return _parse_grouped_json(payload, field="transliteration")
    if candidate_item.source_kind == "grouped_json":
        return _parse_grouped_json(payload, field="text")
    raise TransliterationImportError(f"{candidate_item.id}: no committed snapshot parser")


def import_file(candidate_id: str, path: str | Path | None = None) -> ImportedTransliteration:
    """Import one existing or user-supplied file, after complete identity validation.

    A candidate with a committed snapshot may omit ``path``.  A restricted or unknown
    candidate without a committed snapshot must be supplied explicitly; no network access is
    performed by this function.
    """
    candidate_item = candidate(candidate_id)
    if candidate_item.alias_of:
        raise TransliterationImportError(f"{candidate_id}: aliases are not importable editions")
    source_path = Path(path) if path is not None else candidate_item.snapshot_path
    if source_path is None:
        raise TransliterationImportError(
            f"{candidate_id}: provide an official local export; no downloader is configured"
        )
    if not source_path.is_file():
        raise TransliterationImportError(
            f"{candidate_id}: input file does not exist: {source_path}"
        )
    raw = source_path.read_bytes()

    if candidate_item.source_kind == "tanzil_pipe":
        records = parse_tanzil_pipe(raw)
    elif candidate_item.source_kind == "qul_ayah_json":
        if source_path.suffix.lower() in {".sqlite", ".db"}:
            records = validate_ayah_records(_parse_sqlite(raw, word=False))
        else:
            records = parse_qul_ayah_json(orjson.loads(raw))
    elif candidate_item.source_kind == "qul_word_json":
        if source_path.suffix.lower() in {".sqlite", ".db"}:
            records = validate_word_records(_parse_sqlite(raw, word=True))
        else:
            records = parse_qul_word_json(orjson.loads(raw))
    elif candidate_item.source_kind in {"kemenag_snapshot", "grouped_json"}:
        records = validate_ayah_records(_parse_existing(candidate_item, source_path))
    else:
        raise TransliterationImportError(f"{candidate_id}: unsupported source kind")

    if candidate_item.markup == "html_rich_text":
        records = validate_markup(records, allowed_tags=candidate_item.markup_tags)
    elif candidate_item.markup == "none":
        records = validate_markup(records, allowed_tags=())

    return ImportedTransliteration(candidate_item, tuple(records), sha256(raw).hexdigest())
