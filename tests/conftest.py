"""Shared fixtures: build the trees once per session."""

from __future__ import annotations

from pathlib import Path

import pytest

from quranjson import config
from quranjson.build import build_tree
from quranjson.cdn import build_site


@pytest.fixture(scope="session")
def legacy_tree(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The frozen `dist/` tree as rendered by the Python port (upstream bug included)."""
    out = tmp_path_factory.mktemp("legacy")
    build_tree(out, version="3.1.2", legacy_verse_langs=True)
    return out


@pytest.fixture(scope="session")
def cdn_tree(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """The version-pinned site tree published to the CDN."""
    out = tmp_path_factory.mktemp("cdn")
    build_site(out, version=config.DATASET_VERSION, base_url="https://quran.example/")
    return out / config.DATASET_VERSION
