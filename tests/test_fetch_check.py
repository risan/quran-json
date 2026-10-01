"""`quran-json fetch --check`: compare upstream with the committed snapshots, write nothing."""

from __future__ import annotations

from pathlib import Path

import orjson
import pytest
from typer.testing import CliRunner

from quranjson import config, sources
from quranjson.__main__ import app

SNAPSHOT = b'{"1": [{"verse": 1, "text": "a"}]}'


def _task(path: Path, url: str) -> sources.FetchTask:
    return sources.FetchTask(
        path=path,
        url=url,
        source="fixture",
        license=config.QURANENC,
        parse=orjson.loads,
    )


class _BodyFetcher:
    """Serves one fixed body per URL; any other URL is unreachable."""

    def __init__(self, bodies: dict[str, bytes]) -> None:
        self.bodies = bodies

    def get_bytes(self, url: str, *, headers: dict[str, str] | None = None) -> bytes:
        if url not in self.bodies:
            raise OSError(f"no route to {url}")

        return self.bodies[url]

    def close(self) -> None:
        pass


@pytest.fixture
def data_dir(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setattr(config, "ROOT", tmp_path)
    directory = tmp_path / "data"
    directory.mkdir()

    return directory


def test_nothing_is_reported_when_upstream_matches(
    monkeypatch: pytest.MonkeyPatch, data_dir: Path
) -> None:
    target = data_dir / "a.json"
    target.write_bytes(SNAPSHOT)
    monkeypatch.setattr(sources, "tasks", lambda: [_task(target, "https://example.test/a.json")])

    findings = sources.check_all(fetcher=_BodyFetcher({"https://example.test/a.json": SNAPSHOT}))

    assert findings == []


def test_the_changed_snapshot_is_named_and_nothing_is_written(
    monkeypatch: pytest.MonkeyPatch, data_dir: Path
) -> None:
    changed = data_dir / "changed.json"
    unchanged = data_dir / "unchanged.json"
    changed.write_bytes(SNAPSHOT)
    unchanged.write_bytes(SNAPSHOT)
    monkeypatch.setattr(
        sources,
        "tasks",
        lambda: [
            _task(changed, "https://example.test/changed.json"),
            _task(unchanged, "https://example.test/unchanged.json"),
        ],
    )
    fetcher = _BodyFetcher(
        {
            "https://example.test/changed.json": b'{"1": [{"verse": 1, "text": "A"}]}',
            "https://example.test/unchanged.json": SNAPSHOT,
        }
    )

    findings = sources.check_all(fetcher=fetcher)

    assert len(findings) == 1
    assert findings[0].startswith("CHANGED data/changed.json")
    assert changed.read_bytes() == SNAPSHOT


def test_a_missing_snapshot_and_an_unreachable_upstream_are_reported(
    monkeypatch: pytest.MonkeyPatch, data_dir: Path
) -> None:
    present = data_dir / "present.json"
    present.write_bytes(b"{}")
    monkeypatch.setattr(
        sources,
        "tasks",
        lambda: [
            _task(data_dir / "absent.json", "https://example.test/absent.json"),
            _task(present, "https://example.test/down.json"),
        ],
    )

    findings = sources.check_all(fetcher=_BodyFetcher({}))

    assert [line.split(":")[0] for line in findings] == [
        "MISSING data/absent.json",
        "ERROR   data/present.json",
    ]


def test_the_command_exits_one_on_any_finding(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sources, "check_all", lambda: ["CHANGED data/x.json: content differs"])
    result = CliRunner().invoke(app, ["fetch", "--check"])

    assert result.exit_code == 1
    assert "CHANGED data/x.json" in result.output

    monkeypatch.setattr(sources, "check_all", lambda: [])
    result = CliRunner().invoke(app, ["fetch", "--check"])

    assert result.exit_code == 0
