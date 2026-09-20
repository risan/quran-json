"""Qur'an Kemenag as a source: the crawl, the three payloads, and the licence gate.

The gate is the point of these tests. Qur'an Kemenag serves a text, a translation and a
transliteration from one API, and only the text is publishable: the translation is a
protected work and the romanisation has no grant at all. So the published tree has to gain
a script and *not* gain a translation or a romanisation, while the manifests still describe
what was held back, and why.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import orjson
import pytest

from quranjson import config, kemenag
from quranjson.cdn import build_site
from quranjson.jsonio import read_json

CHAPTERS = 114
VERSES = 6236

#: Alef wasla. Every Tanzil variant marks it thousands of times; the Indonesian standard
#: writes the same words with a plain alef, which is the clearest sign the two texts are
#: different orthographies rather than one text under two labels.
ALEF_WASLA = "\u0671"

#: One ayah exactly as `web-api.qurankemenag.net` returns it, field for field.
AYAH: dict[str, Any] = {
    "id": 8,
    "surah_id": 2,
    "ayah": 1,
    "page": 2,
    "quarter_hizb": 1,
    "juz": 1,
    "manzil": 1,
    "arabic": "\u0627\u0644\u06e4\u0645\u0651\u06e4 \u06da ",
    "kitabah": "\u0627\u0644\u06e1\u0645\u0651\u06e1 \u06da",
    "latin": "Alif l\u0101m m\u012bm. ",
    "arabic_words": None,
    "translation": "Alif L\u0101m M\u012bm. 4)",
    "footnotes": "4) Dalam Al-Qur\u2019an terdapat 29 surah",
    "updated_at": None,
    "surah": {"id": 2, "arabic": " \u0627\u0644\u0628\u0642\u0631\u0629", "latin": "Al-Baqarah "},
}


@pytest.fixture(scope="module")
def unverified_tree(cdn_override_tree: Path) -> Path:
    """The site as published under `--include-unverified-licenses`."""
    return cdn_override_tree


def _payload(*ayahs: dict[str, Any]) -> bytes:
    return orjson.dumps({"data": list(ayahs)})


class _FakeFetcher:
    """Stands in for `Fetcher`: serves a synthetic surah per request, recording the call."""

    def __init__(self, counts: dict[int, int]) -> None:
        self.counts = counts
        self.calls: list[tuple[str, dict[str, str]]] = []

    def get_bytes(self, url: str, *, headers: dict[str, str] | None = None) -> bytes:
        self.calls.append((url, headers or {}))
        surah = int(re.search(r"surah=(\d+)", url).group(1))
        ayahs = [
            {
                **AYAH,
                "surah_id": surah,
                "ayah": number,
                "arabic": f"arabic {surah}:{number}",
                "latin": f"latin {number}",
                "translation": f"translation {number}",
                "footnotes": None,
            }
            for number in range(1, self.counts[surah] + 1)
        ]

        return _payload(*ayahs)


#: Verses where the two orthographies happen to coincide, by global verse number. Pinning
#: them keeps the claim honest: the two texts agree on a handful of verses that hold none
#: of the distinguishing marks (56:3 against Uthmani; 47:6, 55:4 and 56:3 against Imlaei),
#: and disagree everywhere else. If a refresh moves these, the script's separate label --
#: and the licence behind it -- needs re-checking rather than silently re-asserting.
COINCIDENT_VERSES: dict[str, tuple[int, ...]] = {
    "uthmani": (4982,),
    "uthmani-min": (),
    "simple": (4551, 4905, 4982),
    "simple-plain": (4551, 4905),
    "simple-min": (),
    "simple-clean": (),
}


def _chapter_counts() -> dict[int, int]:
    chapters = read_json(config.tanzil_chapters_path())["chapters"]
    return {chapter["id"]: chapter["total_verses"] for chapter in chapters}


def _verse_texts(snapshot: dict[str, list[dict[str, Any]]]) -> list[str]:
    """Every verse's text, in canonical order."""
    return [
        verse["text"]
        for chapter in sorted(snapshot, key=int)
        for verse in sorted(snapshot[chapter], key=lambda item: int(item["verse"]))
    ]


# --- the crawl -----------------------------------------------------------------


def test_parse_surah_keeps_the_three_payloads_and_drops_the_app_metadata() -> None:
    """Only what we publish survives, and the API's trailing space goes with the rest."""
    assert kemenag.parse_surah(_payload(AYAH)) == [
        {
            "chapter": 2,
            "verse": 1,
            "text": "\u0627\u0644\u06e4\u0645\u0651\u06e4 \u06da",
            "transliteration": "Alif l\u0101m m\u012bm.",
            "translation": "Alif L\u0101m M\u012bm. 4)",
            "footnotes": "4) Dalam Al-Qur\u2019an terdapat 29 surah",
        }
    ]


def test_parse_surah_omits_an_absent_footnote() -> None:
    """A footnote key on every verse would claim every ayah has one."""
    for empty in (None, "", "   "):
        verse = kemenag.parse_surah(_payload({**AYAH, "footnotes": empty}))[0]

        assert "footnotes" not in verse


def test_parse_surah_rejects_a_payload_without_verses() -> None:
    with pytest.raises(ValueError, match="no verses"):
        kemenag.parse_surah(b'{"data":[]}')


def test_gather_crawls_every_surah_under_the_sites_own_origin() -> None:
    """The API is the app's backend: without the Origin header it answers 403."""
    fetcher = _FakeFetcher(_chapter_counts())

    snapshot = kemenag.gather(fetcher)

    expected_urls = [kemenag.ayah_url(number) for number in range(1, CHAPTERS + 1)]
    assert [url for url, _ in fetcher.calls] == expected_urls
    assert {headers.get("Origin") for _, headers in fetcher.calls} == {kemenag.ORIGIN}
    assert list(snapshot) == [str(number) for number in range(1, CHAPTERS + 1)]
    assert sum(len(verses) for verses in snapshot.values()) == VERSES
    assert snapshot["2"][254]["verse"] == 255


def test_gather_refuses_a_truncated_crawl() -> None:
    """A short crawl must fail rather than publish a partial Quran."""
    with pytest.raises(ValueError, match=f"expected {VERSES} verses"):
        kemenag.gather(_FakeFetcher(dict.fromkeys(range(1, CHAPTERS + 1), 1)))


# --- the verdicts --------------------------------------------------------------


def test_kemenag_editions_carry_the_audited_verdicts() -> None:
    """A restricted item must not silently regain a permissive label."""
    assert {edition.lang: edition.license.status for edition in config.PENDING_EDITIONS} == {
        "indonesian_kemenag": "restricted",
        "transliteration_kemenag": "unknown",
    }


def test_the_mushaf_text_verdict_names_its_statutory_basis() -> None:
    assert config.KEMENAG_TEXT.status == "granted"
    assert "Pasal 8(1)" in config.KEMENAG_TEXT.text
    assert config.KEMENAG_TEXT.url.startswith("https://")


# --- the published site --------------------------------------------------------


def test_the_mushaf_text_is_published_as_a_distinct_script(cdn_tree: Path) -> None:
    """A seventh orthography, published whole, with its own licence on record."""
    chapters = read_json(cdn_tree / "text" / config.KEMENAG_SCRIPT / "quran.json")
    snapshot = read_json(config.kemenag_path())

    assert len(chapters) == CHAPTERS
    assert sum(len(chapter["verses"]) for chapter in chapters) == VERSES
    assert chapters[0]["verses"][0]["text"] == snapshot["1"][0]["text"]

    text = read_json(cdn_tree / "meta" / "sources.json")["text"]
    licenses = {entry["script"]: entry for entry in text["script_licenses"]}

    assert licenses[config.KEMENAG_SCRIPT]["status"] == "granted"
    assert licenses[config.KEMENAG_SCRIPT]["license_url"] == config.PMA_MUSHAF_URL
    assert text["withheld_scripts"] == []


def test_the_mushaf_text_is_its_own_orthography() -> None:
    """It is a new script, not a relabelled Tanzil variant.

    The marker is decisive: the Indonesian standard writes the words Tanzil's Uthmani text
    spells with an alef wasla (13,819 of them) using a plain alef, so the two texts part
    company on nearly every verse. That is what makes the separate label -- and the
    separate licence behind it -- mean something.
    """
    kemenag_text = _verse_texts(read_json(config.kemenag_path()))

    assert len(kemenag_text) == VERSES
    assert ALEF_WASLA not in "".join(kemenag_text)
    # Tanzil's Uthmani variant is where the marker is unambiguous; `simple-clean` is
    # unvocalised and drops it too, so the comparison is against the marked variant.
    uthmani = _verse_texts(read_json(config.tanzil_text_path("uthmani")))

    assert ALEF_WASLA in "".join(uthmani)

    for variant in config.TANZIL_VARIANTS:
        tanzil_text = _verse_texts(read_json(config.tanzil_text_path(variant)))

        assert len(tanzil_text) == VERSES, variant

        identical = tuple(
            global_id
            for global_id, (left, right) in enumerate(
                zip(kemenag_text, tanzil_text, strict=True), start=1
            )
            if left == right
        )
        assert identical == COINCIDENT_VERSES[variant], variant


def test_the_uncleared_editions_are_withheld_by_default(cdn_tree: Path) -> None:
    """No bytes, and no empty directory pretending to be an edition."""
    assert not (cdn_tree / "translations" / "id-kemenag").exists()
    assert not (cdn_tree / "transliteration" / "kemenag").exists()

    catalogue = read_json(cdn_tree / "translations" / "index.json")
    withheld = {entry["edition"] for entry in catalogue["withheld"]}

    assert "indonesian_kemenag" in withheld


def test_the_transliteration_catalogue_answers_even_with_nothing_published(
    cdn_tree: Path,
) -> None:
    """A consumer asking whether a romanisation exists gets a catalogue, not a 404."""
    catalogue = read_json(cdn_tree / "transliteration" / "index.json")

    assert catalogue["count"] == 0
    assert catalogue["editions"] == []
    assert {entry["edition"] for entry in catalogue["withheld"]} == {
        config.TRANSLITERATION,
        "transliteration_kemenag",
    }

    manifest = read_json(cdn_tree / "manifest.json")

    assert manifest["transliteration"]["count"] == 0
    assert read_json(cdn_tree / "meta" / "sources.json")["transliteration"]["status"] == "withheld"


def test_the_override_publishes_what_the_gate_withheld(unverified_tree: Path) -> None:
    """`--include-unverified-licenses` is the documented way to publish cleared rights."""
    translation = read_json(unverified_tree / "translations" / "id-kemenag" / "quran.json")

    assert len(translation) == CHAPTERS
    assert sum(len(chapter["verses"]) for chapter in translation) == VERSES
    assert translation[0]["verses"][0]["translation"] == (
        "Dengan nama Allah Yang Maha Pengasih lagi Maha Penyayang."
    )
    assert any("footnotes" in verse for verse in translation[1]["verses"])

    romanised = read_json(unverified_tree / "transliteration" / "kemenag" / "quran.json")

    assert len(romanised) == CHAPTERS
    assert sum(len(chapter["verses"]) for chapter in romanised) == VERSES
    assert romanised[0]["verses"][0]["transliteration"].startswith("Bismill\u0101hir-")

    assert read_json(unverified_tree / "manifest.json")["transliteration"]["count"] == 1


def test_the_override_still_reports_the_real_status(unverified_tree: Path) -> None:
    """Publishing on an override must not relabel an edition as granted."""
    sources = read_json(unverified_tree / "meta" / "sources.json")
    statuses = {entry["edition"]: entry["status"] for entry in sources["editions"]}

    assert statuses["indonesian_kemenag"] == "restricted"
    assert sources["transliteration"]["status"] == "published"

    published = {
        entry["edition"]
        for entry in read_json(unverified_tree / "translations" / "index.json")["editions"]
    }
    withheld = {entry["edition"] for entry in sources["withheld"]}

    assert "indonesian_kemenag" in published
    assert "indonesian_kemenag" not in withheld


def test_the_build_reports_only_what_it_withheld(tmp_path: Path) -> None:
    """`quran-json cdn` prints this list, so an override must not call published withheld."""
    gated = {violation.lang for violation in build_site(tmp_path / "gated", audio=False)}
    overridden = {
        violation.lang
        for violation in build_site(
            tmp_path / "override", include_unverified_licenses=True, audio=False
        )
    }

    assert {"indonesian_kemenag", "transliteration_kemenag"} <= gated
    assert {"indonesian_kemenag", "transliteration_kemenag"}.isdisjoint(overridden)

    # The editions nobody has cleared stay withheld under either build.
    assert {"en", "bn", "ur"} <= overridden


def test_the_override_keeps_the_frozen_editions_withheld(unverified_tree: Path) -> None:
    """The flag clears what we ingested, not the editions whose rights nobody holds."""
    catalogue = read_json(unverified_tree / "translations" / "index.json")
    withheld = {entry["edition"] for entry in catalogue["withheld"]}
    published = {entry["edition"] for entry in catalogue["editions"]}

    assert {"en", "bn", "ur"} <= withheld
    assert {"en", "bn", "ur"}.isdisjoint(published)

    # Nor does it resurrect the frozen transliteration, which has its own rights holder.
    romanisations = read_json(unverified_tree / "transliteration" / "index.json")
    assert {entry["edition"] for entry in romanisations["withheld"]} == {config.TRANSLITERATION}
