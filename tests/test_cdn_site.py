"""The generated Cloudflare Pages site: routing rules the CDN depends on.

`_headers` and `_redirects` are the only parts of the site that cannot be exercised by
reading a JSON file, so they are pinned here. Verified against `wrangler pages dev`.
"""

from __future__ import annotations

from quranjson.cdn import _HEADERS, _REDIRECTS


def test_every_dataset_path_is_cors_readable() -> None:
    """A blanket rule must grant cross-origin reads, or no browser client can use it."""
    assert _HEADERS.startswith("/*")
    assert "Access-Control-Allow-Origin: *" in _HEADERS


def test_dataset_paths_are_immutable_cached() -> None:
    """Version-pinned files never change, so they should cache for a year."""
    assert "max-age=31536000" in _HEADERS
    assert "immutable" in _HEADERS


def test_latest_prefix_redirects_to_the_pinned_version() -> None:
    """`/latest/...` must land on the version it names, preserving the tail."""
    rule = _REDIRECTS.format(version="4.0.0")

    assert "/latest/* /4.0.0/:splat 302" in rule


def test_bare_latest_also_redirects() -> None:
    """`/latest` without a trailing path must not silently serve the landing page."""
    rule = _REDIRECTS.format(version="4.0.0")

    assert "\n/latest /4.0.0/ 302" in rule
