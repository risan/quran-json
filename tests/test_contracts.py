"""Machine-readable CDN contracts and the semantic joins they cannot express."""

from __future__ import annotations

import copy
import json
from collections import Counter
from functools import cache
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from quranjson import config
from quranjson.jsonio import read_json

SCHEMA_DIR = Path(__file__).parents[1] / "schemas"
CHAPTER_COUNT = 114
HAFS_VERSE_COUNT = 6236


@cache
def _validator(schema_name: str) -> Draft202012Validator:
    schema = json.loads((SCHEMA_DIR / schema_name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def _assert_schema(document: Any, schema_name: str) -> None:
    errors = sorted(
        _validator(schema_name).iter_errors(document), key=lambda error: list(error.path)
    )
    assert not errors, "\n".join(error.message for error in errors[:5])


def _assert_layer(
    document: Any,
    schema_name: str,
    *,
    mapped: bool = False,
    chapter_counts: dict[int, int] | None = None,
    mapping_exceptions: list[dict[str, Any]] | None = None,
) -> None:
    """Validate shape plus chapter/verse identity and optional riwayah joins."""
    _assert_schema(document, schema_name)
    chapters = document if isinstance(document, list) else [document]
    exceptions = {int(exception["chapter"]): exception for exception in (mapping_exceptions or [])}

    if isinstance(document, list):
        assert len(document) == CHAPTER_COUNT
        assert [chapter["id"] for chapter in chapters] == list(range(1, CHAPTER_COUNT + 1))

    for chapter in chapters:
        verses = chapter["verses"]
        assert [verse["id"] for verse in verses] == list(range(1, len(verses) + 1))
        if mapped:
            for verse in verses:
                numbers = verse.get("number_in_hafs")
                assert isinstance(numbers, list) and numbers
                assert numbers == sorted(set(numbers))
                limit = (
                    chapter_counts.get(chapter["id"], HAFS_VERSE_COUNT)
                    if chapter_counts
                    else HAFS_VERSE_COUNT
                )
                assert all(1 <= number <= limit for number in numbers)

            if chapter_counts:
                limit = chapter_counts[chapter["id"]]
                chapter_numbers = [number for verse in verses for number in verse["number_in_hafs"]]
                assert chapter_numbers == sorted(chapter_numbers)
                exception = exceptions.get(chapter["id"])
                if exception is None:
                    assert set(chapter_numbers) == set(range(1, limit + 1))
                else:
                    missing = set(exception["missing_hafs"])
                    repeated = set(exception["repeated_hafs"])
                    expected = set(range(1, limit + 1))
                    assert set(chapter_numbers) == expected - missing
                    counts = Counter(chapter_numbers)
                    assert all(counts[number] == 2 for number in repeated)
                    assert all(counts[number] == 1 for number in expected - missing - repeated)

    if mapped and isinstance(document, list):
        assert chapter_counts is not None
        flattened = []
        offset = 0
        missing_global: set[int] = set()
        for chapter in chapters:
            flattened.extend(
                offset + number for verse in chapter["verses"] for number in verse["number_in_hafs"]
            )
            exception = exceptions.get(chapter["id"])
            if exception is not None:
                missing_global.update(offset + number for number in exception["missing_hafs"])
            offset += chapter_counts[chapter["id"]]
        assert offset == HAFS_VERSE_COUNT
        assert flattened == sorted(flattened)
        expected = set(range(1, HAFS_VERSE_COUNT + 1))
        assert set(flattened) == expected - missing_global


def _assert_chapters(document: Any) -> None:
    _assert_schema(document, "chapters.schema.json")
    assert [chapter["id"] for chapter in document] == list(range(1, CHAPTER_COUNT + 1))


def _assert_catalogue(document: dict[str, Any], schema_name: str, *, transliteration: bool) -> None:
    _assert_schema(document, schema_name)
    editions = document["editions"]
    assert document["count"] == len(editions)

    for edition in editions:
        path = edition["path"].rstrip("/")
        assert edition["files"]["quran"] == f"{path}/quran.json"
        assert edition["files"]["chapters"] == f"{path}/chapters/{{1-114}}.json"
        if transliteration:
            assert edition["edition"].startswith("transliteration_")
        else:
            assert edition["files"]["quran"].startswith("/translations/")
            assert edition["direction"] in {"ltr", "rtl"}


def test_all_contract_documents_are_valid_json_schema() -> None:
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        schema = json.loads(path.read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)


def test_default_generated_tree_validates_manifest_catalogues_and_layers(cdn_tree: Path) -> None:
    manifest = read_json(cdn_tree / "manifest.json")
    _assert_schema(manifest, "manifest.schema.json")
    chapters = read_json(cdn_tree / "chapters.json")
    _assert_chapters(chapters)
    chapter_counts = {chapter["id"]: chapter["total_verses"] for chapter in chapters}

    for script in manifest["scripts"]:
        _assert_layer(
            read_json(cdn_tree / script["path"].lstrip("/")),
            "script.schema.json",
            mapped=script["verse_ids"] == "mapped",
            chapter_counts=chapter_counts if script["verse_ids"] == "mapped" else None,
            mapping_exceptions=script.get("mapping_coverage_exceptions"),
        )

    translations = read_json(cdn_tree / "translations" / "index.json")
    _assert_catalogue(translations, "translation-catalogue.schema.json", transliteration=False)
    for edition in translations["editions"]:
        translation_key = edition["path"].split("/")[2]
        _assert_layer(
            read_json(cdn_tree / "translations" / translation_key / "chapters" / "1.json"),
            "translation.schema.json",
        )

    transliterations = read_json(cdn_tree / "transliteration" / "index.json")
    _assert_catalogue(
        transliterations,
        "transliteration-catalogue.schema.json",
        transliteration=True,
    )
    assert transliterations["count"] == 0
    assert manifest["transliteration"]["count"] == 0


def test_explicit_override_generated_transliteration_validates(cdn_override_tree: Path) -> None:
    """The override remains available for an explicit rights decision.

    This fixture is session-scoped with the existing gate tests, so schema checks do not
    trigger a full CDN render for every assertion.
    """
    catalogue = read_json(cdn_override_tree / "transliteration" / "index.json")
    _assert_catalogue(catalogue, "transliteration-catalogue.schema.json", transliteration=True)
    assert catalogue["count"] == 1

    key = catalogue["editions"][0]["path"].split("/")[2]
    _assert_layer(
        read_json(cdn_override_tree / "transliteration" / key / "quran.json"),
        "transliteration.schema.json",
    )
    _assert_layer(
        read_json(cdn_override_tree / "transliteration" / key / "chapters" / "1.json"),
        "transliteration.schema.json",
    )


def test_malformed_catalogue_and_alignment_fixtures_fail_contract_checks(cdn_tree: Path) -> None:
    translations = read_json(cdn_tree / "translations" / "index.json")
    malformed_catalogue = copy.deepcopy(translations)
    malformed_catalogue["editions"][0]["direction"] = "diagonal"
    with pytest.raises(AssertionError):
        _assert_catalogue(
            malformed_catalogue, "translation-catalogue.schema.json", transliteration=False
        )

    script = read_json(cdn_tree / "text" / "warsh" / "chapters" / "1.json")
    malformed_alignment = copy.deepcopy(script)
    malformed_alignment["verses"][0]["number_in_hafs"] = [1, 1]
    with pytest.raises(AssertionError):
        _assert_layer(
            malformed_alignment,
            "script.schema.json",
            mapped=True,
            chapter_counts={1: 7},
        )

    malformed_mapping_range = copy.deepcopy(script)
    malformed_mapping_range["verses"][0]["number_in_hafs"] = [0, 1]
    with pytest.raises(AssertionError):
        _assert_layer(
            malformed_mapping_range,
            "script.schema.json",
            mapped=True,
            chapter_counts={1: 7},
        )

    malformed_mapping_gap = read_json(cdn_tree / "text" / "warsh" / "quran.json")
    malformed_mapping_gap[0]["verses"][0]["number_in_hafs"] = [1]
    chapter_counts = {
        chapter["id"]: chapter["total_verses"] for chapter in read_json(cdn_tree / "chapters.json")
    }
    with pytest.raises(AssertionError):
        _assert_layer(
            malformed_mapping_gap,
            "script.schema.json",
            mapped=True,
            chapter_counts=chapter_counts,
        )

    duri = read_json(cdn_tree / "text" / "duri" / "chapters" / "1.json")
    malformed_duri_exception = copy.deepcopy(duri)
    malformed_duri_exception["verses"][-1]["number_in_hafs"] = [6]
    with pytest.raises(AssertionError):
        _assert_layer(
            malformed_duri_exception,
            "script.schema.json",
            mapped=True,
            chapter_counts={1: 7},
            mapping_exceptions=[
                {
                    "chapter": 1,
                    "missing_hafs": [1],
                    "repeated_hafs": [7],
                    "reason": "fixture",
                }
            ],
        )

    malformed_script = read_json(cdn_tree / "text" / "uthmani" / "quran.json")
    malformed_script[1]["id"] = 1
    with pytest.raises(AssertionError):
        _assert_layer(malformed_script, "script.schema.json")

    malformed_chapters = read_json(cdn_tree / "chapters.json")
    malformed_chapters[1]["id"] = 1
    with pytest.raises(AssertionError):
        _assert_chapters(malformed_chapters)

    malformed_translation = copy.deepcopy(
        read_json(cdn_tree / "translations" / "en-pickthall" / "chapters" / "1.json")
    )
    malformed_translation["verses"][0].pop("translation")
    with pytest.raises(AssertionError):
        _assert_layer(malformed_translation, "translation.schema.json")


def test_manifest_points_to_the_same_catalogues_that_were_validated(cdn_tree: Path) -> None:
    manifest = read_json(cdn_tree / "manifest.json")
    translations = read_json(cdn_tree / "translations" / "index.json")
    transliterations = read_json(cdn_tree / "transliteration" / "index.json")

    assert manifest["chapters"] == {"count": CHAPTER_COUNT, "path": "/chapters.json"}
    assert manifest["translations"]["count"] == translations["count"]
    assert manifest["translations"]["index"] == "/translations/index.json"
    assert manifest["transliteration"]["count"] == transliterations["count"]
    assert manifest["transliteration"]["index"] == "/transliteration/index.json"
    assert config.SCRIPT_IDS[0] == manifest["scripts"][0]["id"]

    scripts = {script["id"]: script for script in manifest["scripts"]}
    assert scripts[config.DURI_SCRIPT]["reading"] == {
        "riwayah": "al-Duri",
        "qiraah": "Abu ʿAmr",
        "verse_numbering": "mapped",
    }
    assert scripts[config.DURI_SCRIPT]["audio"] == {
        "verse_numbering": "mapped",
        "per_ayah": False,
    }
    assert "verse_ids_differ_in" not in scripts[config.DURI_SCRIPT]
    assert scripts[config.DURI_SCRIPT]["chapter_furniture"] == [
        {
            "chapter": 1,
            "position": "before-verses",
            "kind": "bismillah",
            "text": "بِسۡمِ اِ۬للَّهِ اِ۬لرَّحۡمَٰنِ اِ۬لرَّحِيمِ ",
            "numbered": False,
        }
    ]
    assert scripts[config.HAFS_NASTALIQ_SCRIPT]["reading"] == {
        "riwayah": "Hafs",
        "qiraah": "ʿAsim",
        "verse_numbering": "hafs",
    }
    assert scripts[config.HAFS_NASTALIQ_SCRIPT]["audio"] == {
        "verse_numbering": "hafs",
        "per_ayah": True,
    }
