"""The upstream snapshot registry: what we fetch, from where, and under what license.

This replaces `scripts/download.js`. Snapshot files are committed under `data/`, so a
build needs no network; `fetch` exists to refresh or extend them. Every snapshot records
provenance (URL, sha256, fetch time, license) in `data/meta/sources.json`.
"""

from __future__ import annotations

import json
import unicodedata
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Final

import orjson

from . import config, qa
from .http import Fetcher
from .jsonio import read_json, write_json

__all__ = ["FetchTask", "fetch_all", "tasks", "verify_snapshots"]

CHAPTERS_SOURCE: Final = "api.quran.com v4"
CHAPTERS_BASE: Final = "https://api.quran.com/api/v4/chapters"

EDITION_BASE: Final = "https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions"


@dataclass(frozen=True, slots=True)
class FetchTask:
    """One upstream snapshot."""

    path: Path
    url: str
    source: str
    license: config.License
    #: Reshape applied to the decoded JSON body before it is written.
    transform: Callable[[Any], Any] | None = None
    #: For non-JSON upstreams: takes the raw body, returns the snapshot payload.
    parse: Callable[[bytes], Any] | None = None
    #: Bulk snapshots (75 translations) are stored compactly; the difference is ~40%.
    compact: bool = False
    #: For upstreams whose corpus spans many requests: crawls through the client and
    #: returns the payload directly. `url` then documents the request pattern rather than
    #: a single endpoint.
    gather: Callable[[Fetcher], Any] | None = None
    #: Extra verdicts for a snapshot carrying more than one payload. `license` stays the
    #: primary -- it is what `verify_snapshots` checks -- and these record the rest, so a
    #: reader of the provenance file sees every verdict the file's bytes are held under.
    extra_licenses: tuple[config.License, ...] = ()
    #: A manually reviewed metadata snapshot is recorded and verified but never overwritten
    #: by `fetch --force`; its source URL is the review evidence, not a replacement payload.
    refresh: bool = True
    #: SHA-256 of the raw upstream archive before parsing. This catches a changed bulk file
    #: even when its parsed JSON happens to retain the same shape.
    source_sha256: str | None = None
    #: Source archive byte count, when the upstream manifest or review pins it.
    source_bytes: int | None = None
    #: Source-specific identity and freshness fields retained in provenance.
    source_metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def rel(self) -> str:
        return str(self.path.relative_to(config.ROOT))


def _chapter_list(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Reshape the quran.com chapter list into the snapshot format."""
    return [
        {
            "id": chapter["id"],
            "name": chapter["name_arabic"],
            "transliteration": chapter["name_simple"],
            "translation": chapter["translated_name"]["name"],
            "type": "meccan" if chapter["revelation_place"] == "makkah" else "medinan",
            "total_verses": chapter["verses_count"],
        }
        for chapter in payload["chapters"]
    ]


def _group_by_chapter(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    """Reshape a flat verse list into `{chapter: [verses]}` -- `_.groupBy` equivalent."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for verse in payload["quran"]:
        grouped.setdefault(str(verse["chapter"]), []).append(verse)
    return grouped


def _qa_transform(lang: str) -> Callable[[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    """Group a flat edition into chapters, then restore known upstream defects."""

    def transform(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
        return qa.apply_corrections(lang, _group_by_chapter(payload))

    return transform


def tasks(*, langs: tuple[str, ...] | None = None) -> list[FetchTask]:
    """Every snapshot the build depends on, optionally restricted to ``langs``."""
    selected = set(langs) if langs is not None else None

    out: list[FetchTask] = [
        FetchTask(
            path=config.text_path(),
            url=f"{EDITION_BASE}/{config.TEXT_EDITION}.json",
            source="quranenc.com via fawazahmed0/quran-api",
            license=config.SHIPPED_TEXT,
        )
    ]

    for lang in config.LANG_CODES:
        if lang is None:
            continue
        if selected is not None and lang not in selected:
            continue
        out.append(
            FetchTask(
                path=config.chapter_list_path(lang),
                url=f"{CHAPTERS_BASE}?language={lang}",
                source=CHAPTERS_SOURCE,
                license=config.QURAN_COM_METADATA,
                transform=_chapter_list,
            )
        )

    for edition in config.EDITIONS:
        if selected is not None and edition.lang not in selected:
            continue
        out.append(
            FetchTask(
                path=config.edition_path(edition.lang),
                url=f"{EDITION_BASE}/{edition.slug}.json",
                source=edition.source,
                license=edition.license,
                transform=_group_by_chapter,
            )
        )

    from .audio import audio_tasks

    out.extend(audio_tasks())
    out.extend(licensed_tasks())
    return out


def licensed_tasks() -> list[FetchTask]:
    """Snapshots for the licensed dataset generation: Tanzil, QuranEnc, Qur'an Kemenag.

    These are the sources whose grants actually cover redistribution, as opposed to the
    re-encoded derivative the frozen `dist/` tree was built from. Qur'an Kemenag is the
    exception in kind rather than in treatment: only its text is publishable, so the
    snapshot is fetched and its three verdicts travel with it into the provenance file.
    """
    from . import quranenc, tanzil

    tasks = [
        FetchTask(
            path=config.tanzil_text_path(variant),
            url=tanzil.text_url(variant),
            source="tanzil.net",
            license=config.TANZIL_TEXT,
            parse=tanzil.parse_text,
        )
        for variant in config.TANZIL_VARIANTS
    ]

    tasks.append(
        FetchTask(
            path=config.tanzil_chapters_path(),
            url=tanzil.METADATA_URL,
            source="tanzil.net",
            license=config.TANZIL_TEXT,
            parse=tanzil.parse_metadata,
        )
    )

    tasks.append(
        FetchTask(
            path=config.quranenc_catalogue_path(),
            url=quranenc.CATALOGUE_URL,
            source="quranenc.com",
            license=config.QURANENC,
            parse=quranenc.parse_catalogue,
        )
    )

    # The list endpoint is not complete. This reviewed catalogue is deliberately a
    # committed input: it is checked against the official browse/terms page and its
    # versioned bulk URLs, but `--force` must not replace it with the incomplete list.
    if config.quranenc_supplemental_catalogue_path().exists():
        tasks.append(
            FetchTask(
                path=config.quranenc_supplemental_catalogue_path(),
                url=quranenc.TERMS_URL,
                source="quranenc.com manually reviewed supplemental catalogue",
                license=config.QURANENC,
                refresh=False,
                source_metadata={
                    "manual_registration": True,
                    "catalogue_endpoint": quranenc.CATALOGUE_URL,
                },
            )
        )

    catalogues = quranenc.load_catalogues()
    if catalogues:
        quranenc.merged_catalogue(catalogues)

    from . import clearquran

    parsers = {
        "clearquran": clearquran.parse_verse_files,
        "quranenc": None,  # handled by the QuranEnc catalogue pass above
    }

    for edition in config.EXTRA_EDITIONS:
        kind = edition.kind
        tasks.append(
            FetchTask(
                path=config.extra_edition_path(edition.lang),
                url=edition.source,
                source=edition.source,
                license=edition.license,
                parse=parsers.get(kind),
                transform=None if kind != "quran-api" else _qa_transform(edition.lang),
                compact=True,
            )
        )

    for catalogue in catalogues:
        quranenc.validate_catalogue(catalogue)
        tasks.extend(
            FetchTask(
                path=config.quranenc_path(entry["key"]),
                url=entry["database_url"],
                source=f"quranenc.com/{entry['key']} v{entry['version']}",
                license=config.QURANENC,
                parse=(
                    quranenc.parse_complete_translation_allow_empty
                    if entry.get("allow_empty")
                    else quranenc.parse_complete_translation
                ),
                compact=True,
                source_sha256=entry.get("archive_sha256"),
                source_bytes=entry.get("archive_bytes"),
                source_metadata={
                    "provider": "quranenc",
                    "key": entry["key"],
                    "language": entry["lang"],
                    "direction": entry["direction"],
                    "title": entry["title"],
                    "version": entry["version"],
                    "browse_url": entry.get(
                        "browse_url", f"https://quranenc.com/en/browse/{entry['key']}/"
                    ),
                    "terms_url": quranenc.TERMS_URL,
                    **({"manual_registration": True} if entry.get("manual_registration") else {}),
                    **(
                        {
                            "availability": entry["availability"],
                            "availability_reason": entry["availability_reason"],
                            "allow_empty": True,
                        }
                        if entry.get("availability") == "withheld"
                        else {}
                    ),
                },
            )
            for entry in catalogue["translations"]
        )

    from . import kemenag

    tasks.append(
        FetchTask(
            path=config.kemenag_path(),
            url=kemenag.SNAPSHOT_URL,
            source="quran.kemenag.go.id (Lajnah Pentashihan Mushaf Al-Qur'an)",
            license=config.KEMENAG_TEXT,
            gather=kemenag.gather,
            # The one snapshot holds all three payloads, under three different verdicts.
            extra_licenses=(config.KEMENAG_TRANSLATION, config.KEMENAG_TRANSLITERATION),
        )
    )

    from . import digitalkhatt

    tasks.append(
        FetchTask(
            path=config.digitalkhatt_path(),
            url=digitalkhatt.SNAPSHOT_URL,
            source="DigitalKhatt/digitalkhatt-js (Indo-Pak, 15-line)",
            license=config.DIGITALKHATT,
            parse=digitalkhatt.parse_text,
        )
    )

    from . import quranpedia

    tasks.extend(
        FetchTask(
            path=config.quranpedia_path(script),
            url=quranpedia.dump_url(script),
            source=(
                f"quranpedia.net dumps/mushafs-{quranpedia.MOUNT[script]} "
                f"({script}, {config.SCRIPT_LABELS[script][0]})"
            ),
            license=config.QURANPEDIA,
            parse=quranpedia.parse_dump_for(script),
            source_sha256=quranpedia.DUMP_METADATA.get(script, {}).get("archive_sha256"),
            source_bytes=quranpedia.DUMP_METADATA.get(script, {}).get("archive_bytes"),
            source_metadata=(
                {
                    "provider": "quranpedia",
                    "mushaf_id": quranpedia.MOUNT[script],
                    "name": quranpedia.DUMP_METADATA.get(script, {}).get(
                        "name", config.SCRIPT_LABELS[script][0]
                    ),
                    "dump_version": quranpedia.DUMP_METADATA.get(script, {}).get(
                        "dump_version", "unknown"
                    ),
                    "built_at": quranpedia.DUMP_METADATA.get(script, {}).get("built_at"),
                    "license_url": quranpedia.LICENSE_URL,
                    "description": quranpedia.DUMP_METADATA.get(script, {}).get("description"),
                    "bismillah": quranpedia.DUMP_METADATA.get(script, {}).get("bismillah"),
                }
            ),
        )
        for script in config.QURANPEDIA_SCRIPTS
    )

    return tasks


def _normalise(
    raw: bytes,
    transform: Callable[[Any], Any] | None = None,
    parse: Callable[[bytes], Any] | None = None,
) -> Any:
    """Reshape an upstream body into snapshot form."""
    if parse is not None:
        return parse(raw)

    payload = orjson.loads(raw)

    if transform is not None:
        return transform(payload)

    if "chapters" in payload:
        return _chapter_list(payload)
    return _group_by_chapter(payload)


def _summarise_change(old: Any, new: Any) -> dict[str, Any]:
    """Describe how a refreshed snapshot differs from the committed one.

    Upstream editions are mutable and have silently changed orthographic standard
    before (see `data/meta/drift.json`), so a refresh must never be invisible. For
    text-bearing snapshots the character-level delta is recorded too, because a
    re-encoded orthography is the failure mode that actually bites.
    """
    if isinstance(old, dict) and isinstance(new, dict):
        changed = total = 0
        before_text: Counter[str] = Counter()
        after_text: Counter[str] = Counter()

        for key, verses in old.items():
            new_verses = new.get(key, [])
            total += len(verses)
            # A different record count is itself drift, not something to skip over.
            changed += abs(len(verses) - len(new_verses))

            for before, after in zip(verses, new_verses, strict=False):
                if before != after:
                    changed += 1
                    before_text.update(json.dumps(before, ensure_ascii=False))
                    after_text.update(json.dumps(after, ensure_ascii=False))

        changed += sum(len(verses) for key, verses in new.items() if key not in old)

        summary: dict[str, Any] = {"kind": "records", "records": total, "changed": changed}

        if changed:
            summary["codepoint_delta"] = {
                "added": _rare_codepoints(before_text, after_text),
                "removed": _rare_codepoints(after_text, before_text),
            }

        return summary

    if isinstance(old, list) and isinstance(new, list):
        changed = sum(1 for before, after in zip(old, new, strict=False) if before != after)
        return {
            "kind": "records",
            "records": max(len(old), len(new)),
            "changed": changed + abs(len(old) - len(new)),
        }

    return {"kind": "opaque", "changed": int(old != new)}


def _rare_codepoints(reference: Counter[str], subject: Counter[str]) -> list[str]:
    """Codepoints present in ``subject`` but absent from ``reference``, most frequent first."""
    extra = [(char, count) for char, count in subject.items() if char not in reference]
    extra.sort(key=lambda item: -item[1])

    return [
        f"U+{ord(char):04X} {unicodedata.name(char, '?')} x{count}" for char, count in extra[:12]
    ]


def _validate_source_payload(task: FetchTask, raw: bytes) -> None:
    """Check a pinned bulk artifact before parsing or replacing its snapshot."""
    if task.source_sha256 is not None:
        actual_sha256 = sha256(raw).hexdigest()
        if actual_sha256 != task.source_sha256:
            raise ValueError(
                f"source archive hash mismatch for {task.rel}: "
                f"expected {task.source_sha256[:12]}, got {actual_sha256[:12]}"
            )
    if task.source_bytes is not None and len(raw) != task.source_bytes:
        raise ValueError(
            f"source archive size mismatch for {task.rel}: "
            f"expected {task.source_bytes}, got {len(raw)}"
        )


def fetch_all(
    *,
    force: bool = False,
    langs: tuple[str, ...] | None = None,
    fetcher: Fetcher | None = None,
) -> list[dict[str, Any]]:
    """Download every missing snapshot and refresh the provenance manifest.

    Existing files are kept unless ``force`` is set, so the build stays reproducible.
    With ``force``, any snapshot whose content changed is recorded in
    ``data/meta/drift.json`` before it is replaced.
    """
    drift: list[dict[str, Any]] = []
    owned = fetcher is None
    client = fetcher or Fetcher()

    try:
        # Two passes: the QuranEnc catalogue is itself a snapshot, and the per-translation
        # tasks only exist once it has been fetched. The second pass picks those up.
        for _ in range(2):
            selected = tasks(langs=langs)
            pending = [
                task for task in selected if task.refresh and (force or not task.path.exists())
            ]

            if not pending:
                break

            for task in pending:
                previous = read_json(task.path) if task.path.exists() else None
                previous_sha = (
                    sha256(task.path.read_bytes()).hexdigest() if previous is not None else None
                )
                if task.gather is not None:
                    payload = task.gather(client)
                else:
                    raw = client.get_bytes(task.url)
                    _validate_source_payload(task, raw)
                    payload = _normalise(raw, task.transform, task.parse)
                summary = _summarise_change(previous, payload) if previous is not None else None

                write_json(task.path, payload, pretty=not task.compact)

                if summary is not None and summary["changed"]:
                    drift.append(
                        {
                            "path": task.rel,
                            "url": task.url,
                            "detected_at": fetched_at(),
                            **summary,
                            "previous_sha256": previous_sha,
                            "sha256": sha256(task.path.read_bytes()).hexdigest(),
                        }
                    )
    finally:
        if owned:
            client.close()

    if drift:
        write_json(config.DATA / "meta" / "drift.json", drift, pretty=True)

    records = [_record(task) for task in tasks(langs=langs)]
    write_json(config.DATA / "meta" / "sources.json", records, pretty=True)
    qa.write_manifest()
    return records


def _record(task: FetchTask) -> dict[str, Any]:
    body = task.path.read_bytes()
    record: dict[str, Any] = {
        "path": task.rel,
        "url": task.url,
        "source": task.source,
        "license": task.license.text,
        "license_status": task.license.status,
        "license_url": task.license.url,
        "sha256": sha256(body).hexdigest(),
        "bytes": len(body),
        "revision": _revision(task.path),
    }

    if task.source_sha256 is not None:
        record["source_sha256"] = task.source_sha256
    if task.source_bytes is not None:
        record["source_bytes"] = task.source_bytes
    if task.source_metadata:
        record["source_metadata"] = task.source_metadata

    # A multipart snapshot carries bytes held under more than one verdict; record them all
    # so the provenance file never implies the primary licence covers the whole file.
    if task.extra_licenses:
        record["extra_licenses"] = [
            {"status": license_.status, "text": license_.text, "url": license_.url}
            for license_ in task.extra_licenses
        ]

    return record


def _revision(path: Path) -> str:
    """Git blob revision of a snapshot, when the file is tracked."""
    import subprocess

    result = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", str(path)],
        cwd=config.ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def verify_snapshots(records: list[dict[str, Any]] | None = None) -> list[str]:
    """Return a list of provenance problems (empty when everything checks out)."""
    manifest_path = config.DATA / "meta" / "sources.json"
    if records is None:
        if not manifest_path.exists():
            return ["data/meta/sources.json is missing; run `quran-json fetch`"]
        records = read_json(manifest_path)

    problems: list[str] = []

    for record in records:
        path = config.ROOT / record["path"]

        if not path.exists():
            problems.append(f"missing snapshot: {record['path']}")
            continue

        digest = sha256(path.read_bytes()).hexdigest()
        if digest != record["sha256"]:
            problems.append(
                f"hash mismatch for {record['path']}: manifest={record['sha256'][:12]} "
                f"actual={digest[:12]}"
            )

        if not record.get("license"):
            problems.append(f"no license recorded for {record['path']}")

        if not record.get("license_url"):
            problems.append(f"no license URL recorded for {record['path']}")

    return problems


def fetched_at() -> str:
    """ISO-8601 UTC timestamp for manifest stamping."""
    return datetime.now(UTC).replace(microsecond=0).isoformat()
