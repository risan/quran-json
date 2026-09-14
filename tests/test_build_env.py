"""The render path must not depend on the SQLite extension.

Cloudflare's build image ships a CPython 3.13 compiled without `_sqlite3`, and the deploy
failed there with `ModuleNotFoundError: No module named '_sqlite3'`. Rendering only reads
the already-parsed JSON snapshots, so SQLite is a fetch-time concern and must stay out of
the import graph. These tests run a poisoned `sqlite3` in a subprocess to prove it.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

#: Mimics the interpreter Cloudflare builds with: the stdlib module exists but the C
#: extension behind it does not.
POISON = "raise ModuleNotFoundError(\"No module named '_sqlite3'\")\n"


def _run(code: str, poisoned: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONPATH": str(poisoned)},
        check=False,
    )


@pytest.fixture
def poisoned_interpreter(tmp_path: Path) -> Path:
    """A directory that shadows `sqlite3` with an import that always fails."""
    (tmp_path / "sqlite3.py").write_text(POISON, encoding="utf-8")
    return tmp_path


def test_the_poison_actually_bites(poisoned_interpreter: Path) -> None:
    """Guard the guard: without this, the real test could pass vacuously."""
    result = _run("import sqlite3", poisoned_interpreter)

    assert result.returncode != 0
    assert "_sqlite3" in result.stderr


def test_rendering_works_without_sqlite3(poisoned_interpreter: Path) -> None:
    """The whole publishable dataset must resolve on an interpreter lacking SQLite."""
    result = _run(
        "from quranjson import cdn\n"
        "editions = cdn.published_editions()\n"
        "assert len(editions) >= 80, len(editions)\n"
        "import sys\n"
        "assert 'sqlite3' not in sys.modules, 'render path imported sqlite3'\n",
        poisoned_interpreter,
    )

    assert result.returncode == 0, result.stderr
