"""The licence gate.

Regression guard for the defect this gate was built for: the shipped `dist/` tree carries
Saheeh International under a licence label that belongs to Tanzil's Arabic *text*. Any
change that silently re-permits a restricted edition fails here.
"""

from __future__ import annotations

import pytest

from quranjson import config, licensing


def test_publishable_languages_are_only_the_granted_ones() -> None:
    assert licensing.publishable_languages() == ("id", "zh")


def test_every_edition_declares_a_status_and_a_licence_url() -> None:
    for edition in config.EDITIONS:
        assert edition.license.status in {"granted", "restricted", "unknown"}
        assert edition.license.url.startswith("https://"), edition.lang
        assert edition.license.text.strip(), edition.lang


def test_saheeh_international_is_flagged_as_not_redistributable() -> None:
    """It is copyrighted, the publisher is gone, and neither upstream grants reuse."""
    english = next(edition for edition in config.EDITIONS if edition.lang == "en")

    assert english.author.startswith("Umm Muhammad")
    assert english.license is config.SAHEEH_INTERNATIONAL
    assert english.license.status == "restricted"
    assert english.redistributable is False


def test_tanzil_translations_are_not_treated_as_covered_by_the_text_licence() -> None:
    for edition in config.EDITIONS:
        if edition.license is config.TANZIL_TRANSLATION:
            assert edition.redistributable is False, edition.lang

    assert config.TANZIL_TEXT.status == "granted"
    assert config.TANZIL_TRANSLATION.status == "restricted"
    assert config.SHIPPED_TEXT.status == "unknown"


def test_blocked_lists_every_withheld_edition() -> None:
    blocked = {violation.lang for violation in licensing.blocked()}

    assert blocked == {
        config.TRANSLITERATION,
        "bn",
        "en",
        "es",
        "fr",
        "ru",
        "sv",
        "tr",
        "ur",
        # Ingested from Qur'an Kemenag but not cleared: a protected translation and a
        # romanisation nobody has granted rights to.
        "indonesian_kemenag",
        "transliteration_kemenag",
    }


def test_require_publishable_refuses_a_restricted_language() -> None:
    with pytest.raises(licensing.LicenseError) as error:
        licensing.require_publishable(["en"])

    assert "en" in str(error.value)


def test_require_publishable_allows_granted_languages() -> None:
    licensing.require_publishable(["id", "zh"])


def test_report_marks_each_edition() -> None:
    report = licensing.report()
    lines = {line.split()[1]: line.split()[0] for line in report.splitlines()}

    assert lines["en"] == "BLOCKED"
    assert lines["id"] == "OK"
    assert lines["zh"] == "OK"
