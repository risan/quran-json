"""The transliteration generator: golden rules, the Kemenag agreement gate, and the editions.

The Kemenag Latin field is a comparison reference only. Nothing here asserts that a
generated string *is* that field, and nothing copies it into an output.
"""

from __future__ import annotations

import json
import random
import time
import unicodedata
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator, FormatChecker

from quranjson import romanize
from quranjson import romanize_validation as validation

DATA = Path(__file__).parent / "data"
CATALOGUE_SCHEMA = Path(__file__).parents[1] / "schemas" / "transliteration-catalogue.schema.json"

# Measured on the committed snapshot; raised to just below the achieved numbers so that a
# regression fails (the plan's floor is 85% exact and 0.35% CER).
MIN_EXACT_RATE = 0.871
MAX_CHARACTER_ERROR_RATE = 0.0030

VERSE_COUNT = 6236
CHAPTER_COUNT = 114

# One entry per phone-layer rule: (rule, Arabic, id-skb, en, en-simple). Short snippets keep
# each rule isolated; the verse-level goldens below cover the rules in running text.
RULE_CASES: list[tuple[str, str, str, str, str]] = [
    ("moon letter keeps the lam", "اَلْقَمَرُ", "Al-qamar.", "Al-qamar", "Al-qamar"),
    ("sun letter assimilates the lam", "اَلشَّمْسُ", "Asy-syams.", "Ash-shams", "Ash-shams"),
    (
        "hamzat wasl joins and shortens the long vowel before it",
        "فِى السَّمَاۤءِ",
        "Fis-samā'.",
        "Fis-samāʾ",
        "Fis-samaa'",
    ),
    ("pause: tanwin fatha becomes a long a", "كِتَابًا", "Kitābā.", "Kitābā", "Kitaabaa"),
    ("pause: tanwin damma is dropped", "كِتَابٌ", "Kitāb.", "Kitāb", "Kitaab"),
    ("pause: tanwin kasra is dropped", "كِتَابٍ", "Kitāb.", "Kitāb", "Kitaab"),
    ("pause: ta marbuta becomes h", "رَحْمَةٌ", "Raḥmah.", "Raḥmah", "Rahmah"),
    ("pause: tanwin fatha on a ta marbuta", "رَحْمَةً", "Raḥmah.", "Raḥmah", "Rahmah"),
    (
        "connected: ta marbuta stays t, lam of Allah",
        "رَحْمَةُ اللّٰهِ",
        "Raḥmatullāh.",
        "Raḥmatullāh",
        "Rahmatullaah",
    ),
    ("diphthongs aw and ay", "لَوْ بَيْنَ", "Lau bain.", "Law bayn", "Law bayn"),
    ("dagger alef", "ذٰلِكَ", "Żālik.", "Dhālik", "Dhaalik"),
    ("small waw (sila)", "لَهٗ", "Lah.", "Lah", "Lah"),
    ("subscript alef (sila)", "بِهٖ", "Bih.", "Bih", "Bih"),
    ("waw of the plural with silent alef", "قَالُوْا", "Qālū.", "Qālū", "Qaaloo"),
    ("silent waw in ula'ika", "اُولٰۤىِٕكَ", "Ulā'ik.", "Ulāʾik", "Ulaa'ik"),
    ("idgham without ghunna", "مِنْ رَّبِّهِمْ", "Mir rabbihim.", "Mir rabbihim", "Mir rabbihim"),
    ("idgham with ghunna", "مَنْ يَّقُوْلُ", "May yaqūl.", "May yaqūl", "May yaqool"),
    ("iqlab from the small mim", "مِنْۢ بَعْدِ", "Mim ba‘d.", "Mim baʿd", "Mim ba`d"),
    ("lam of Allah", "بِاللّٰهِ", "Billāh.", "Billāh", "Billaah"),
    ("alef maksura, ayn is not capitalised away", "عَلٰى", "‘Alā.", "ʿAlā", "`Alaa"),
    ("idgham of nun into mim", "مِنْ مَّاۤءٍ", "Mim mā'.", "Mim māʾ", "Mim maa'"),
    ("mid-verse stop at a waqf mark", "وَقَالَ ۗ اِنَّ", "Waqāl, inn.", "Waqāl, inn", "Waqaal, inn"),
]


@pytest.fixture(scope="module")
def snapshot() -> Mapping[str, Sequence[Mapping[str, Any]]]:
    return validation.load_snapshot()


@pytest.fixture(scope="module")
def editions(
    snapshot: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, list[dict[str, Any]]]:
    return romanize.build_editions(snapshot)


@pytest.fixture(scope="module")
def found(snapshot: Mapping[str, Sequence[Mapping[str, Any]]]) -> list[validation.Mismatch]:
    return list(validation.mismatches(snapshot))


def load_golden() -> list[dict[str, Any]]:
    golden: list[dict[str, Any]] = json.loads(
        (DATA / "romanize_golden.json").read_text(encoding="utf-8")
    )

    return golden


GOLDEN_VERSES = [
    pytest.param(entry["rule"], verse, id=f"{entry['rule']} {verse['chapter']}:{verse['verse']}")
    for entry in load_golden()
    for verse in entry["verses"]
]


def verse_text(
    snapshot: Mapping[str, Sequence[Mapping[str, Any]]], chapter: int, verse: int
) -> str:
    text: str = snapshot[str(chapter)][verse - 1]["text"]

    return text


# -- public API ---------------------------------------------------------------------------


def test_renderers_are_the_three_published_editions() -> None:
    assert romanize.RENDERERS == ("id-skb", "en", "en-simple")
    assert [edition["key"] for edition in romanize.EDITIONS] == list(romanize.RENDERERS)


def test_unknown_renderer_and_invalid_verse_are_refused() -> None:
    with pytest.raises(ValueError, match="unknown renderer"):
        romanize.romanize_verse("اَلْقَمَرُ", "tr", chapter=1, verse=1)

    with pytest.raises(ValueError, match="invalid verse id"):
        romanize.romanize_verse("اَلْقَمَرُ", "en", chapter=0, verse=1)


def test_generating_every_verse_in_all_renderers_is_fast(
    snapshot: Mapping[str, Sequence[Mapping[str, Any]]],
) -> None:
    started = time.perf_counter()
    romanize.build_editions(snapshot)

    assert time.perf_counter() - started < 8


# -- golden: one test per rule --------------------------------------------------------------


@pytest.mark.parametrize(
    ("rule", "arabic", "id_skb", "english", "simple"),
    RULE_CASES,
    ids=[case[0] for case in RULE_CASES],
)
def test_rule(rule: str, arabic: str, id_skb: str, english: str, simple: str) -> None:
    assert romanize.romanize_verse(arabic, "id-skb", chapter=1, verse=1) == id_skb
    assert romanize.romanize_verse(arabic, "en", chapter=1, verse=1) == english
    assert romanize.romanize_verse(arabic, "en-simple", chapter=1, verse=1) == simple


@pytest.mark.parametrize(("rule", "golden"), GOLDEN_VERSES)
def test_golden_verse(
    snapshot: Mapping[str, Sequence[Mapping[str, Any]]], rule: str, golden: Mapping[str, Any]
) -> None:
    text = verse_text(snapshot, golden["chapter"], golden["verse"])

    for renderer in romanize.RENDERERS:
        actual = romanize.romanize_verse(
            text, renderer, chapter=golden["chapter"], verse=golden["verse"]
        )

        assert actual == golden[renderer], f"{rule}: {renderer}"


def test_the_fatiha_in_all_three_renderers(
    editions: Mapping[str, list[dict[str, Any]]],
) -> None:
    fatiha = {
        renderer: [verse["transliteration"] for verse in editions[renderer][0]["verses"]]
        for renderer in romanize.RENDERERS
    }

    assert fatiha["id-skb"][0] == "Bismillāhir-raḥmānir-raḥīm."
    assert fatiha["en"][0] == "Bismillāhir-raḥmānir-raḥīm"
    assert fatiha["en-simple"][0] == "Bismillaahir-rahmaanir-raheem"
    assert fatiha["id-skb"][3] == "Māliki yaumid-dīn."
    assert fatiha["en-simple"][6].endswith("walad-daalleen")


def test_every_hafs_exception_has_a_golden_verse() -> None:
    golden = {(v["chapter"], v["verse"]) for entry in load_golden() for v in entry["verses"]}

    for name, verses in romanize.HAFS_EXCEPTIONS.items():
        for chapter_and_verse in verses:
            assert chapter_and_verse in golden, name


def test_imala_and_the_small_sin_follow_the_written_marks(
    snapshot: Mapping[str, Sequence[Mapping[str, Any]]],
) -> None:
    def render(chapter: int, verse: int, renderer: str) -> str:
        text = verse_text(snapshot, chapter, verse)

        return romanize.romanize_verse(text, renderer, chapter=chapter, verse=verse)

    assert "majrêhā" in render(11, 41, "id-skb")
    assert "majrēhā" in render(11, 41, "en")
    assert "majrayhaa" in render(11, 41, "en-simple")
    assert "yabsuṭ" in render(2, 245, "id-skb")
    assert "basṭah" in render(7, 69, "id-skb")
    assert "musaiṭirūn" in render(52, 37, "id-skb")
    assert "nakhlukkum" in render(77, 20, "en")


def test_a_sakta_keeps_the_vowels_and_breaks_the_flow(
    snapshot: Mapping[str, Sequence[Mapping[str, Any]]],
) -> None:
    with_sakta = romanize.romanize_verse(verse_text(snapshot, 75, 27), "en", chapter=75, verse=27)
    without_sakta = romanize.romanize_verse("وَقِيْلَ مَنْ رَاقٍ", "en", chapter=75, verse=27)

    assert with_sakta == "Waqīla man… rāq"
    assert without_sakta == "Waqīla man rāq"


# -- build_editions --------------------------------------------------------------------------


def test_editions_carry_every_hafs_verse_once(
    snapshot: Mapping[str, Sequence[Mapping[str, Any]]],
    editions: Mapping[str, list[dict[str, Any]]],
) -> None:
    assert list(editions) == list(romanize.RENDERERS)

    for chapters in editions.values():
        assert [chapter["id"] for chapter in chapters] == list(range(1, CHAPTER_COUNT + 1))
        assert sum(len(chapter["verses"]) for chapter in chapters) == VERSE_COUNT

        for chapter in chapters:
            ids = [verse["id"] for verse in chapter["verses"]]

            assert ids == list(range(1, len(snapshot[str(chapter["id"])]) + 1))
            assert all(set(verse) == {"id", "transliteration"} for verse in chapter["verses"])
            assert all(verse["transliteration"] for verse in chapter["verses"])


def first_letter(text: str) -> str:
    """The first letter of a transliteration; the ayn and hamza marks are not letters."""
    return next(
        character
        for character in text
        if character.isalpha() and unicodedata.category(character) != "Lm"
    )


def test_every_verse_starts_with_a_capital(
    editions: Mapping[str, list[dict[str, Any]]],
) -> None:
    for chapters in editions.values():
        for chapter in chapters:
            for verse in chapter["verses"]:
                assert first_letter(verse["transliteration"]).isupper(), (
                    chapter["id"],
                    verse["id"],
                )


def test_the_transliteration_follows_hafs_numbering_not_warsh(
    editions: Mapping[str, list[dict[str, Any]]],
) -> None:
    """Hafs 1:4 is Maliki yawm ad-din; Warsh reads Maliki at 1:3, so ids are never remapped."""
    fatiha = editions["id-skb"][0]["verses"]

    assert fatiha[3]["id"] == 4
    assert fatiha[3]["transliteration"].startswith("Māliki")
    assert fatiha[2]["transliteration"].startswith("Ar-raḥmān")
    assert {edition["reading"] for edition in romanize.EDITIONS} == {"hafs"}
    assert {edition["verse_ids"] for edition in romanize.EDITIONS} == {"hafs"}


def test_the_simple_edition_is_plain_ascii(
    editions: Mapping[str, list[dict[str, Any]]],
) -> None:
    for chapter in editions["en-simple"]:
        for verse in chapter["verses"]:
            assert verse["transliteration"].isascii(), (chapter["id"], verse["id"])


# -- EDITIONS metadata against the published schema ---------------------------------------------


def published_catalogue() -> dict[str, Any]:
    """The catalogue as the publisher writes it: path and files added, `key` dropped."""
    entries = []

    for edition in romanize.EDITIONS:
        entry = {name: value for name, value in edition.items() if name != "key"}
        path = f"/transliteration/{edition['key']}/"
        entry["path"] = path
        entry["chapters"] = CHAPTER_COUNT
        entry["files"] = {
            "quran": f"{path}quran.json",
            "chapters": f"{path}chapters/{{1-114}}.json",
        }
        entries.append(entry)

    return {"count": len(entries), "editions": entries, "withheld": []}


@pytest.fixture(scope="module")
def catalogue_validator() -> Draft202012Validator:
    schema = json.loads(CATALOGUE_SCHEMA.read_text(encoding="utf-8"))

    return Draft202012Validator(schema, format_checker=FormatChecker())


def test_editions_metadata_is_valid_against_the_catalogue_schema(
    catalogue_validator: Draft202012Validator,
) -> None:
    errors = sorted(catalogue_validator.iter_errors(published_catalogue()), key=str)

    assert errors == []


def test_editions_declare_licence_review_and_method() -> None:
    for edition in romanize.EDITIONS:
        assert edition["license"]["status"] == "granted"
        assert "CC BY-SA 4.0" in edition["license"]["text"]
        assert "Kemenag" in edition["license"]["text"]
        assert edition["review"] == "machine-generated; not yet reviewed by a qualified reader"
        assert edition["method"]
        assert edition["language"] in {"id", "en"}


@pytest.mark.parametrize(
    ("field", "value"),
    [("reading", "kisai"), ("verse_ids", "madani"), ("review", ""), ("reading", 3)],
)
def test_the_schema_rejects_an_invalid_reading_identity(
    catalogue_validator: Draft202012Validator, field: str, value: Any
) -> None:
    catalogue = published_catalogue()
    catalogue["editions"][0][field] = value

    assert list(catalogue_validator.iter_errors(catalogue))


def test_the_schema_stays_strict_about_unknown_properties(
    catalogue_validator: Draft202012Validator,
) -> None:
    catalogue = published_catalogue()
    catalogue["editions"][0]["key"] = "id-skb"

    assert list(catalogue_validator.iter_errors(catalogue))


# -- Metric A: agreement with the Kemenag Latin field ---------------------------------------------


def test_normalisation_is_fixed() -> None:
    assert validation.normalise("Bismillāhir-raḥmānir-raḥīm(i).") == "bismillāhirraḥmānirraḥīm"
    assert validation.normalise("An‘amta wa ’iżā  ʾa") == "an‘amtawa'iżā'a"


def test_agreement_with_kemenag_latin(
    snapshot: Mapping[str, Sequence[Mapping[str, Any]]],
) -> None:
    agreement = validation.measure_agreement(snapshot)

    assert agreement.verses == VERSE_COUNT
    assert agreement.exact_rate >= MIN_EXACT_RATE, agreement
    assert agreement.character_error_rate <= MAX_CHARACTER_ERROR_RATE, agreement


def test_every_disagreeing_verse_has_a_class(
    found: list[validation.Mismatch],
) -> None:
    classes = Counter(item.category for item in found)

    assert set(classes) <= set(validation.Class.ALL)
    assert classes[validation.Class.HAMZA_SPACING] > 0
    assert classes[validation.Class.PAUSE_CHOICE] > 0
    assert classes[validation.Class.REFERENCE_TYPO] > 0


def test_no_new_verse_enters_the_generator_gap_class(
    found: list[validation.Mismatch],
) -> None:
    allowed = set(validation.load_lines(validation.GAPS_PATH))
    gaps = {item.key for item in found if item.category == validation.Class.GENERATOR_GAP}

    assert gaps - allowed == set(), "new generator gap; fix the generator or investigate"
    assert allowed - gaps == set(), (
        "fixed or reclassified; rerun scripts/romanize_crosscheck.py baselines"
    )


def test_the_named_reference_typos_are_classified_as_typos(
    found: list[validation.Mismatch],
) -> None:
    classes = {item.key: item.category for item in found}

    for key in ("7:96", "2:282", "8:65", "3:49"):
        assert classes[key] == validation.Class.REFERENCE_TYPO, key


def test_known_pause_choice_and_hamza_spacing_verses(
    found: list[validation.Mismatch],
) -> None:
    classes = {item.key: item.category for item in found}

    assert classes["3:11"] == validation.Class.PAUSE_CHOICE
    assert classes["2:24"] == validation.Class.HAMZA_SPACING


def test_a_stale_witness_digest_voids_the_reference_typo_class() -> None:
    witness = validation.load_witness()
    key = "7:96"
    chapter, verse = (int(part) for part in key.split(":"))
    snapshot = validation.load_snapshot()
    record = snapshot[str(chapter)][verse - 1]
    reference = validation.normalise(record["transliteration"])

    assert witness[key] == validation.phone_digest(record["text"])
    assert (
        validation.classify(chapter, verse, record["text"], reference, {key: "000000000000"})
        == validation.Class.GENERATOR_GAP
    )


def test_the_report_lists_counts_and_at_most_fifty_examples_per_class(
    snapshot: Mapping[str, Sequence[Mapping[str, Any]]],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    # Three chapters are enough to exercise every class and the cap, and keep the test quick.
    monkeypatch.setattr(
        validation, "load_snapshot", lambda: {key: snapshot[key] for key in ("2", "3", "4")}
    )
    report = tmp_path / "report.md"
    romanize.write_report(report)
    text = report.read_text(encoding="utf-8")

    for name in validation.Class.ALL:
        assert f"## {name} (" in text

    sections = text.split("\n## ")[1:]

    for section in sections:
        assert section.count("\n* ") <= validation.EXAMPLES_PER_CLASS


# -- comparison helpers -------------------------------------------------------------------------


def test_edit_distance_matches_the_textbook_algorithm() -> None:
    def textbook(left: str, right: str) -> int:
        previous = list(range(len(right) + 1))

        for index, a in enumerate(left, 1):
            current = [index]

            for jndex, b in enumerate(right, 1):
                current.append(
                    min(previous[jndex] + 1, current[-1] + 1, previous[jndex - 1] + (a != b))
                )

            previous = current

        return previous[-1]

    generator = random.Random(7)
    alphabet = "abcdeā‘'"

    for _ in range(300):
        left = "".join(generator.choices(alphabet, k=generator.randint(0, 40)))
        right = "".join(generator.choices(alphabet, k=generator.randint(0, 40)))

        assert validation.edit_distance(left, right) == textbook(left, right)

    assert validation.edit_distance(["a", "b"], ["a", "c", "b"]) == 1


def test_skeleton_ignores_spelling_but_keeps_consonants_and_vowel_length() -> None:
    assert validation.skeleton("Bismillāhir-raḥmānir-raḥīm") == validation.skeleton(
        "Bismillaahir Rahmaanir Raheem"
    )
    assert validation.skeleton("Qul huwallāhu aḥad") == validation.skeleton("Qul huwal laahu ahad")
    assert validation.skeleton("kitāb") != validation.skeleton("kitab")
    assert validation.skeleton("kitāb") != validation.skeleton("kitāt")


def test_skeleton_error_rate_of_english_output_against_another_spelling() -> None:
    pairs = [
        ("Alhamdu lillaahi Rabbil 'aalameen", "Al-ḥamdu lillāhi rabbil-ʿālamīn"),
        ("Qul huwal laahu ahad", "Qul huwallāhu aḥad"),
    ]

    assert validation.skeleton_error_rate(pairs) == 0.0
    assert validation.skeleton_error_rate([("kitaab", "kitab")]) > 0.0
