"""The licence gate.

Regression guard for the defect this gate was built for: the shipped `dist/` tree carries
Saheeh International under a licence label that belongs to Tanzil's Arabic *text*. Any
change that silently re-permits a restricted edition fails here.
"""

from __future__ import annotations

import pytest

from quranjson import config, licensing, review


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


# --- the licensing review record ----------------------------------------------


def test_every_reviewed_source_carries_evidence() -> None:
    for entry in review.CANDIDATES:
        assert entry.license_url.startswith("https://"), entry.name
        assert entry.evidence.strip(), entry.name
        assert entry.status in {"granted", "restricted", "unknown"}, entry.name
        assert entry.kind in {"text", "translation", "transliteration", "audio"}, entry.name


def test_no_transliteration_source_is_publishable() -> None:
    """The exhaustive search found no transliteration with a rights-holder grant.

    If this ever fails, a grant was obtained: update config.EDITIONS and the gate
    together, and say so in the README.
    """
    candidates = [entry for entry in review.CANDIDATES if entry.kind == "transliteration"]

    assert candidates, "the transliteration review went missing"
    assert {entry.status for entry in candidates} == {"restricted", "unknown"}
    assert len(candidates) >= 5, "the transliteration review must stay exhaustive"

    transliteration = next(
        edition for edition in config.EDITIONS if edition.lang == config.TRANSLITERATION
    )
    assert transliteration.redistributable is False

    for entry in candidates:
        if entry.status != "granted":
            assert entry.blocker, f"{entry.name} must say what would unblock it"


def test_review_manifest_lists_what_is_published() -> None:
    manifest = review.review_manifest()

    assert manifest["sources"]
    assert "75" in manifest["published"]["quranenc"]
    assert {entry["lang"] for entry in manifest["published"]["extra"]} == {
        "english_itani",
        "english_itani_allah",
        "english_pickthall",
        "english_yusuf_ali",
        "english_palmer",
        "english_sale",
        "russian_sablukov",
        "russian_krachkovsky",
    }
    assert "unknown` is not permission" in manifest["note"]


def test_granted_reviews_match_the_publishable_editions() -> None:
    """A `granted` verdict must correspond to something we actually publish."""
    published = {edition.lang for edition in config.EDITIONS if edition.redistributable}
    granted_translations = {
        entry.name
        for entry in review.CANDIDATES
        if entry.status == "granted" and entry.kind == "translation"
    }

    assert published == {"id", "zh"}
    assert granted_translations, "QuranEnc should be recorded as granted"
