"""The generated site's headers, which are the only part a static host must interpret.

`_headers` cannot be exercised by reading a JSON file, so it is pinned here. Verified
against `wrangler pages dev`.
"""

from __future__ import annotations

from quranjson.cdn import _HEADERS


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


def test_the_landing_page_is_not_cached_for_a_year() -> None:
    """The blanket CORS rule must not accidentally make the HTML immutable too."""
    root = _HEADERS.split("/*", 1)[1].split("\n\n", 1)[0]

    assert "immutable" not in root


def test_no_redirect_file_is_generated() -> None:
    """Unversioned paths need no `/latest` indirection."""
    import quranjson.cdn as cdn

    assert not hasattr(cdn, "_REDIRECTS")
