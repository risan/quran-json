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
    monkeypatch.setattr(sources, "check_all", lambda **_: ["CHANGED data/x.json: content differs"])
    result = CliRunner().invoke(app, ["fetch", "--check"])

    assert result.exit_code == 1
    assert "CHANGED data/x.json" in result.output

    monkeypatch.setattr(sources, "check_all", lambda **_: [])
    result = CliRunner().invoke(app, ["fetch", "--check"])

    assert result.exit_code == 0


def test_only_limits_the_check_and_the_refresh_to_matching_paths(
    monkeypatch: pytest.MonkeyPatch, data_dir: Path
) -> None:
    kept = data_dir / "kept.json"
    other = data_dir / "other.json"
    kept.write_bytes(SNAPSHOT)
    other.write_bytes(SNAPSHOT)
    new = b'{"1": [{"verse": 1, "text": "b"}]}'
    bodies = {"https://example.test/kept.json": new, "https://example.test/other.json": new}
    monkeypatch.setattr(
        sources,
        "tasks",
        lambda: [
            _task(kept, "https://example.test/kept.json"),
            _task(other, "https://example.test/other.json"),
        ],
    )
    monkeypatch.setattr(sources, "_record", lambda task: {"path": task.rel})
    monkeypatch.setattr(sources.qa, "write_manifest", lambda: None)
    monkeypatch.setattr(config, "DATA", data_dir)
    (data_dir / "meta").mkdir()

    findings = sources.check_all(fetcher=_BodyFetcher(bodies), only=["data/kept"])

    assert [line.split(":")[0] for line in findings] == ["CHANGED data/kept.json"]

    sources.fetch_all(force=True, fetcher=_BodyFetcher(bodies), only=["data/kept"])

    assert orjson.loads(kept.read_bytes()) == orjson.loads(new)
    assert other.read_bytes() == SNAPSHOT


def test_a_refresh_appends_to_the_drift_history(
    monkeypatch: pytest.MonkeyPatch, data_dir: Path
) -> None:
    target = data_dir / "a.json"
    target.write_bytes(SNAPSHOT)
    meta = data_dir / "meta"
    meta.mkdir()
    monkeypatch.setattr(config, "DATA", data_dir)
    (meta / "drift.json").write_bytes(b'[{"path": "data/earlier.json", "changed": 1}]')
    monkeypatch.setattr(sources, "tasks", lambda: [_task(target, "https://example.test/a.json")])
    monkeypatch.setattr(sources, "_record", lambda task: {"path": task.rel})
    monkeypatch.setattr(sources.qa, "write_manifest", lambda: None)
    body = b'{"1": [{"verse": 1, "text": "b"}]}'

    sources.fetch_all(force=True, fetcher=_BodyFetcher({"https://example.test/a.json": body}))

    history = orjson.loads((meta / "drift.json").read_bytes())

    assert [entry["path"] for entry in history] == ["data/earlier.json", "data/a.json"]
    assert history[1]["changed_verses"] == ["1:1"]
