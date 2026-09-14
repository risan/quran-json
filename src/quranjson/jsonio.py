"""Deterministic JSON I/O.

The published artifacts were produced by Node's ``JSON.stringify`` through
``fs-extra.outputJson(..., { spaces: pretty ? 2 : 0 })``. Reproducing those bytes
exactly is a hard requirement (git-diff parity gate), so this module mirrors that
formatting precisely:

* compact output when ``pretty`` is false -- ``{"a":1,"b":2}``
* two-space indentation when true
* non-ASCII (Arabic, CJK, Cyrillic) left raw as UTF-8 -- never ``\\uXXXX``
* a single trailing newline (jsonfile's default EOL)
* key order = insertion order
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import orjson

__all__ = ["dumps", "write_json"]


def dumps(obj: Any, *, pretty: bool = False) -> bytes:
    """Serialize ``obj`` to the exact byte form published by this project."""
    if pretty:
        text = json.dumps(obj, ensure_ascii=False, indent=2, separators=(",", ": "))
        return text.encode("utf-8") + b"\n"

    return orjson.dumps(obj) + b"\n"


def write_json(path: Path, obj: Any, *, pretty: bool = False) -> None:
    """Write ``obj`` to ``path``, creating parent directories as needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(dumps(obj, pretty=pretty))


def read_json(path: Path) -> Any:
    """Read JSON from ``path`` preserving key order."""
    return orjson.loads(path.read_bytes())
