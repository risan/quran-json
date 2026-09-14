"""The published-bytes contract.

`dist/` is served through jsDelivr to pinned consumer installations. Regenerating it
must reproduce the tracked files exactly; any drift here is a breaking change for
everyone already depending on those URLs.
"""

from __future__ import annotations

from pathlib import Path

from quranjson import config


def _relative_files(root: Path) -> set[str]:
    return {str(path.relative_to(root)) for path in root.rglob("*") if path.is_file()}


def test_build_reproduces_committed_dist(legacy_tree: Path) -> None:
    committed = config.DIST
    rendered = _relative_files(legacy_tree)

    assert rendered == _relative_files(committed)

    mismatched = [
        name
        for name in sorted(rendered)
        if (legacy_tree / name).read_bytes() != (committed / name).read_bytes()
    ]

    assert mismatched == [], f"{len(mismatched)} artifact(s) changed, e.g. {mismatched[:5]}"
