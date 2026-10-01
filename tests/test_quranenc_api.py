"""The per-surah QuranEnc API ingest: complete, partial and malformed responses (no network)."""

from __future__ import annotations

from typing import Any

import orjson
import pytest

from quranjson import config, quranenc, sources
from quranjson.jsonio import read_json

API_ONLY_KEYS = {"belarusian_krivtsov", "chinese_suliman_modern", "oromo_rwwad", "zulu_adel"}


def _counts() -> dict[int, int]:
    return {
        int(chapter["id"]): int(chapter["total_verses"])
        for chapter in read_json(config.tanzil_chapters_path())["chapters"]
    }


def _row(sura: int, aya: int, **fields: Any) -> dict[str, Any]:
    return {
        "id": str(sura * 1000 + aya),
        "sura": str(sura),
        "aya": str(aya),
        "arabic_text": "x",
        "translation": f"text {sura}:{aya}",
        "footnotes": "",
        **fields,
    }


def _body(sura: int, count: int | None = None, **fields: Any) -> bytes:
    count = _counts()[sura] if count is None else count
    return orjson.dumps({"result": [_row(sura, aya, **fields) for aya in range(1, count + 1)]})


class StubFetcher:
    """Answers each surah URL from a table, recording what was asked for."""

    def __init__(self, overrides: dict[int, bytes] | None = None) -> None:
        self.overrides = overrides or {}
        self.requested: list[str] = []

    def get_bytes(self, url: str) -> bytes:
        self.requested.append(url)
        sura = int(url.rsplit("/", 1)[1])

        return self.overrides.get(sura, _body(sura))


def test_parse_sura_keeps_text_and_footnotes_and_orders_by_verse() -> None:
    raw = orjson.dumps(
        {
            "result": [
                _row(1, 2, translation="second"),
                _row(1, 1, translation="first", footnotes="[1] note"),
            ]
        }
    )

    assert quranenc.parse_sura(raw, sura=1) == [
        {"chapter": 1, "verse": 1, "text": "first", "footnotes": "[1] note"},
        {"chapter": 1, "verse": 2, "text": "second"},
    ]


def test_parse_sura_accepts_a_missing_footnotes_field() -> None:
    row = _row(1, 1)
    del row["footnotes"]

    assert quranenc.parse_sura(orjson.dumps({"result": [row]}), sura=1) == [
        {"chapter": 1, "verse": 1, "text": "text 1:1"}
    ]


@pytest.mark.parametrize(
    ("raw", "message"),
    [
        (b"<html>403</html>", ""),
        (b"", ""),
        (orjson.dumps([]), "no result rows"),
        (orjson.dumps({"error": "x"}), "no result rows"),
        (orjson.dumps({"result": []}), "no result rows"),
        (orjson.dumps({"result": "oops"}), "no result rows"),
        (orjson.dumps({"result": ["row"]}), "malformed row"),
        (orjson.dumps({"result": [{"sura": "1"}]}), "no valid sura/aya"),
        (orjson.dumps({"result": [{**_row(1, 1), "aya": "one"}]}), "no valid sura/aya"),
        (orjson.dumps({"result": [_row(2, 1)]}), "contains verse 2:1"),
        (orjson.dumps({"result": [_row(1, 1), _row(1, 1)]}), "repeats verse 1"),
        (orjson.dumps({"result": [_row(1, 1, translation=None)]}), "no text at 1:1"),
        (orjson.dumps({"result": [_row(1, 1, footnotes=["x"])]}), "invalid footnotes at 1:1"),
    ],
)
def test_parse_sura_rejects_malformed_responses(raw: bytes, message: str) -> None:
    with pytest.raises(ValueError, match=message or None):
        quranenc.parse_sura(raw, sura=1)


def test_gatherer_crawls_every_surah_into_the_archive_shape() -> None:
    client = StubFetcher({1: _body(1, footnotes="[1] note")})

    verses = quranenc.api_gatherer("zulu_adel")(client)  # type: ignore[arg-type]

    assert len(client.requested) == len(set(client.requested)) == 114
    assert client.requested[0] == "https://quranenc.com/api/v1/translation/sura/zulu_adel/1"
    assert sum(len(entries) for entries in verses.values()) == 6236
    assert verses["1"][0] == {
        "chapter": 1,
        "verse": 1,
        "text": "text 1:1",
        "footnotes": "[1] note",
    }
    assert "footnotes" not in verses["2"][0]


def test_gatherer_fails_on_a_partial_surah() -> None:
    client = StubFetcher({2: _body(2, count=285)})

    with pytest.raises(ValueError, match="chapter 2: expected 286 verses, got 285"):
        quranenc.api_gatherer("zulu_adel")(client)  # type: ignore[arg-type]


def test_gatherer_fails_on_a_gap_inside_a_surah() -> None:
    rows = [_row(3, aya) for aya in range(1, 201) if aya != 7]
    client = StubFetcher({3: orjson.dumps({"result": rows})})

    with pytest.raises(ValueError, match="chapter 3: expected 200 verses, got 199"):
        quranenc.api_gatherer("zulu_adel")(client)  # type: ignore[arg-type]


def test_gatherer_fails_on_a_renumbered_surah() -> None:
    rows = [_row(3, aya) for aya in range(2, 202)]
    client = StubFetcher({3: orjson.dumps({"result": rows})})

    with pytest.raises(ValueError, match="invalid id at 3:1"):
        quranenc.api_gatherer("zulu_adel")(client)  # type: ignore[arg-type]


def test_gatherer_stops_on_one_malformed_surah() -> None:
    client = StubFetcher({50: b"not json"})

    with pytest.raises(ValueError):
        quranenc.api_gatherer("zulu_adel")(client)  # type: ignore[arg-type]

    assert len(client.requested) == 50


def test_gatherer_rejects_empty_rows_unless_the_edition_is_withheld() -> None:
    client = StubFetcher({114: _body(114, translation="  ")})

    with pytest.raises(ValueError, match="empty text at 114:1"):
        quranenc.api_gatherer("zulu_adel")(client)  # type: ignore[arg-type]

    verses = quranenc.api_gatherer("zulu_adel", allow_empty=True)(client)  # type: ignore[arg-type]
    assert verses["114"][0]["text"].strip() == ""


def test_catalogue_rejects_an_api_entry_without_a_surah_pattern_or_with_a_pinned_archive() -> None:
    entry = {
        "key": "zulu_adel",
        "lang": "zu",
        "direction": "ltr",
        "version": "1.0.0",
        "title": "Zulu",
        "description": "Zulu",
        "database_url": quranenc.SURA_URL,
        "ingest": "api",
    }
    quranenc.validate_catalogue({"translations": [entry]})

    with pytest.raises(ValueError, match="surah URL pattern"):
        quranenc.validate_catalogue(
            {"translations": [dict(entry, database_url="https://quranenc.com/x.zip")]}
        )
    with pytest.raises(ValueError, match="cannot pin an archive"):
        quranenc.validate_catalogue({"translations": [dict(entry, archive_sha256="ab")]})
    with pytest.raises(ValueError, match="invalid ingest mode"):
        quranenc.validate_catalogue({"translations": [dict(entry, ingest="scrape")]})


def test_the_four_api_only_editions_are_registered_as_api_ingests() -> None:
    catalogue = read_json(config.quranenc_supplemental_catalogue_path())
    entries = {entry["key"]: entry for entry in catalogue["translations"]}

    for key in API_ONLY_KEYS:
        assert entries[key]["ingest"] == "api", key
        assert entries[key]["version"], key

    tasks = {task.path.stem: task for task in sources.licensed_tasks()}
    for key in API_ONLY_KEYS:
        assert tasks[key].gather is not None, key
        assert tasks[key].parse is None, key
        assert tasks[key].source_metadata["ingest"] == "api", key
    assert tasks["bengali_rwwad"].gather is None
