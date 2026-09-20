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


def test_data_paths_are_cached_immutably() -> None:
    """Data paths carry no version, so immutable caching rests on the no-rewrite promise.

    Text and translations are each cached for a year; if that promise is broken, a
    consumer keeps the old bytes for as long as their browser holds them. The font files of
    the bundled Arabic faces are cached the same way and on the same terms: a font file that
    changes content would have to arrive under a new name.
    """
    for rule in ("/text/*", "/translations/*", "/transliteration/*", "/assets/fonts/*"):
        block = _HEADERS.split(rule, 1)[1].split("\n\n", 1)[0]
        assert "max-age=31536000" in block, rule
        assert "immutable" in block, rule


def test_catalogue_indexes_revalidate_while_edition_payloads_remain_immutable() -> None:
    """Exact catalogue rules detach the inherited immutable wildcard cache.

    Before the exception existed, both index paths inherited the wildcard year-long cache;
    an updated edition list could therefore remain hidden behind a stale browser/CDN copy.
    The payloads retain the immutable policy because their unversioned paths are promised
    never to be rewritten.
    """
    for family in ("translations", "transliteration"):
        assert _effective_headers(f"/{family}/quran.json")["Cache-Control"] == (
            "public, max-age=31536000, immutable"
        )
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
