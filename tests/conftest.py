"""Shared fixtures: build the trees once per session."""

from __future__ import annotations

from pathlib import Path

import pytest

from quranjson.cdn import build_site


@pytest.fixture(scope="session")
def cdn_tree(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The published site tree, rendered exactly as deployed."""
    out = tmp_path_factory.mktemp("cdn")
    build_site(out)
    return out
