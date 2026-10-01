"""The licence gate.

Any change that silently publishes an edition without a verified grant fails here.
"""

from __future__ import annotations

import dataclasses

import pytest

from quranjson import cdn, config, licensing


def test_every_published_edition_is_granted_and_documented() -> None:
    editions = cdn.published_editions()

    assert editions

    for edition in editions:
        assert edition.redistributable, edition.lang
        assert edition.license.url.startswith("https://"), edition.lang
        assert edition.license.text.strip(), edition.lang


def test_require_publishable_refuses_an_edition_without_a_grant() -> None:
    granted = config.EXTRA_EDITIONS[0]
    restricted = dataclasses.replace(
        granted,
        lang="english_unlicensed",
        license=dataclasses.replace(granted.license, status="restricted"),
    )

    with pytest.raises(licensing.LicenseError) as error:
        licensing.require_publishable([granted, restricted])

    assert "english_unlicensed" in str(error.value)
    assert granted.lang not in str(error.value)


def test_require_publishable_allows_granted_editions() -> None:
    licensing.require_publishable(cdn.published_editions())


def test_tanzil_text_is_granted_and_no_script_is_published_without_a_grant() -> None:
    assert config.TANZIL_TEXT.status == "granted"

    for script in config.SCRIPT_IDS:
        assert config.SCRIPT_LICENSES[script].allows_publication, script
