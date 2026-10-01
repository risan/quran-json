"""The generated site's headers, which are the only part a static host must interpret.

`_headers` cannot be exercised by reading a JSON file, so it is pinned here. Its inheritance
and detach semantics follow Cloudflare Workers Static Assets and are checked with the local
Wrangler Workers dev path when available.
"""

from __future__ import annotations

from collections import defaultdict

from quranjson.cdn import _HEADERS


def _effective_headers(path: str) -> dict[str, str]:
    """Model the Static Assets `_headers` inheritance used by Cloudflare.

    A wildcard and an exact rule both apply. Cloudflare joins duplicate header values, and
    the documented ``! Header`` form detaches an inherited value before the replacement is
    applied. Keeping that small model here catches a cache policy that merely *looks* more
    specific in the file but still leaves the catalogue immutable.
    """
    effective: dict[str, list[str]] = defaultdict(list)

    for raw_block in _HEADERS.strip().split("\n\n"):
        lines = [line.strip() for line in raw_block.splitlines() if line.strip()]
        if not lines:
            continue

        pattern, *header_lines = lines
        matches = path == pattern or (pattern.endswith("/*") and path.startswith(pattern[:-1]))
        if not matches:
            continue

        for line in header_lines:
            if line.startswith("!"):
                effective.pop(line[1:].strip(), None)
                continue
            name, value = line.split(":", 1)
            effective[name.strip()].append(value.strip())

    return {name: ", ".join(values) for name, values in effective.items()}


def test_every_path_is_cors_readable() -> None:
    """A blanket rule must grant cross-origin reads, or no browser client can use it."""
    assert _HEADERS.startswith("/*")
    assert "Access-Control-Allow-Origin: *" in _HEADERS


DATA_CACHE = "public, max-age=86400, stale-while-revalidate=604800"
IMMUTABLE_CACHE = "public, max-age=31536000, immutable"


def test_data_paths_are_cached_for_a_day_and_revalidated_in_the_background() -> None:
    """Data keeps its path but may receive upstream corrections, so it is not immutable.

    A stale copy may be served for a week while the CDN revalidates, so a correction reaches
    consumers within a day for fresh requests without a hard failure for the rest.
    """
    for family in ("text", "translations", "transliteration"):
        assert _effective_headers(f"/{family}/x/quran.json")["Cache-Control"] == DATA_CACHE


def test_only_hashed_build_output_and_fonts_are_immutable() -> None:
    for path in ("/_astro/index.abc123.js", "/fonts/amiri-regular.woff2"):
        assert _effective_headers(path)["Cache-Control"] == IMMUTABLE_CACHE, path

    for path in ("/text/uthmani/quran.json", "/translations/en-pickthall/quran.json"):
        assert "immutable" not in _effective_headers(path)["Cache-Control"], path


def test_catalogue_indexes_revalidate_sooner_than_edition_payloads() -> None:
    """Exact catalogue rules detach the inherited wildcard cache.

    An updated edition list must not stay hidden behind a day-old copy, so the two indexes
    revalidate after a minute while the payloads under them keep the one-day policy.
    """
    for family in ("translations", "transliteration"):
        assert _effective_headers(f"/{family}/quran.json")["Cache-Control"] == DATA_CACHE
        assert _effective_headers(f"/{family}/index.json")["Cache-Control"] == (
            "public, max-age=60, must-revalidate"
        )


def test_the_landing_page_is_not_cached_for_a_year() -> None:
    """The blanket CORS rule must not accidentally make the HTML immutable too."""
    root = _HEADERS.split("/*", 1)[1].split("\n\n", 1)[0]

    assert "immutable" not in root


def test_no_redirect_file_is_generated() -> None:
    """Unversioned paths need no `/latest` indirection."""
    import quranjson.cdn as cdn

    assert not hasattr(cdn, "_REDIRECTS")
