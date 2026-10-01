"""Validation of the generated romanisation against comparison references.

Nothing here ships. The Kemenag Latin field (the `transliteration` field of
`data/kemenag/quran.json`) is a reference to compare against, never an output.

Metric A: agreement of the `id-skb` renderer with the Kemenag Latin field
---------------------------------------------------------------------------
Both sides are normalised by `normalise`: Unicode NFC, parenthesised pause hints such as
`(i)` dropped, lower-cased, typographic apostrophes folded to `'`, and everything except
letters, `'` (hamza) and the left single quote U+2018 (ayn) removed. Spaces, hyphens, commas
and full stops therefore never count. The report gives the share of verses whose normalised
forms are identical and the character error rate (edit distance over reference length).

Disagreement classes
--------------------
Every verse that does not match is given exactly one class by `classify`:

* `pause-choice`: the verse matches once individual mid-verse pause decisions are flipped
  (Kemenag stops at some waqf signs and runs through others, and the signs do not decide).
* `hamza-spacing`: the only difference is an apostrophe (Kemenag writes `fa'in` and `fa in`
  about equally often).
* `reference-typo`: the reference deviates from the Arabic where the generator's phones are
  confirmed by an independent engine (QUD `quranic-phonemizer`, MIT). Typical cases are a
  missing macron (`'azizun`), a wrong letter (`rijaliukum` in 2:282, `wal ardhi` in 7:96,
  `sabirun` in 8:65, `ubarri'u` in 3:49) and words dropped from the Latin line. The
  confirmation is `tests/data/romanize_reference_witness.txt`: one line per verse, with a
  digest of our phones at the time `scripts/romanize_crosscheck.py` compared them. A changed
  digest voids the confirmation, so a later generator change cannot hide behind it.
* `generator-gap`: anything else. `tests/data/romanize_generator_gaps.txt` lists the verses
  currently in this class; a verse that enters it fails the tests.

A verse that needs more than one excuse takes the first of the order above.
"""

from __future__ import annotations

import difflib
import hashlib
import re
import unicodedata
from collections import Counter
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from . import qa
from .romanize import (
    ARTICLE_BOUNDARY,
    SCHEMES,
    iter_verses,
    render,
    romanize_verse,
    speak,
    verse_words,
)

__all__ = [
    "Agreement",
    "Class",
    "Mismatch",
    "classify",
    "connected_phones",
    "edit_distance",
    "load_lines",
    "load_witness",
    "measure_agreement",
    "mismatches",
    "normalise",
    "phone_digest",
    "skeleton",
    "skeleton_error_rate",
    "write_report",
]

AYN_QUOTE: Final = "\u2018"
KEPT_PUNCTUATION: Final = frozenset({"'", AYN_QUOTE})
EXAMPLES_PER_CLASS: Final = 50
RENDERER: Final = "id-skb"


class Class:
    REFERENCE_TYPO: Final = "reference-typo"
    HAMZA_SPACING: Final = "hamza-spacing"
    PAUSE_CHOICE: Final = "pause-choice"
    GENERATOR_GAP: Final = "generator-gap"

    ALL: Final = (REFERENCE_TYPO, PAUSE_CHOICE, HAMZA_SPACING, GENERATOR_GAP)


TESTS_DATA: Final = Path(__file__).resolve().parents[2] / "tests" / "data"
WITNESS_PATH: Final = TESTS_DATA / "romanize_reference_witness.txt"
GAPS_PATH: Final = TESTS_DATA / "romanize_generator_gaps.txt"


def normalise(text: str) -> str:
    """The Metric A normalisation; see the module docstring."""
    text = unicodedata.normalize("NFC", text)
    text = _drop_parenthesised(text).lower().replace("\u2019", "'").replace("\u02be", "'")

    return "".join(ch for ch in text if ch.isalpha() or ch in KEPT_PUNCTUATION)


def _drop_parenthesised(text: str) -> str:
    result: list[str] = []
    depth = 0

    for character in text:
        if character == "(":
            depth += 1
        elif character == ")":
            depth = max(0, depth - 1)
        elif depth == 0:
            result.append(character)

    return "".join(result)


def edit_distance[Item](left: Sequence[Item], right: Sequence[Item]) -> int:
    """Levenshtein distance, by the bit-parallel algorithm of Myers (1999) and Hyyro (2003).

    Works on strings and on any other sequence of hashable items (phones, for example).
    """
    if not left:
        return len(right)

    if not right:
        return len(left)

    size = len(left)
    all_ones = (1 << size) - 1
    last_bit = 1 << (size - 1)
    positions: dict[Item, int] = {}

    for index, character in enumerate(left):
        positions[character] = positions.get(character, 0) | (1 << index)

    plus = all_ones
    minus = 0
    score = size

    for character in right:
        match = positions.get(character, 0)
        carry = match | minus
        horizontal = (((match & plus) + plus) ^ plus) | match
        plus_h = minus | (~(horizontal | plus) & all_ones)
        minus_h = plus & horizontal

        if plus_h & last_bit:
            score += 1
        elif minus_h & last_bit:
            score -= 1

        plus_h = ((plus_h << 1) | 1) & all_ones
        minus_h = (minus_h << 1) & all_ones
        plus = minus_h | (~(carry | plus_h) & all_ones)
        minus = plus_h & carry

    return score


@dataclass(frozen=True)
class Agreement:
    verses: int
    exact: int
    edits: int
    reference_length: int

    @property
    def exact_rate(self) -> float:
        return self.exact / self.verses

    @property
    def character_error_rate(self) -> float:
        return self.edits / self.reference_length


@dataclass(frozen=True)
class Mismatch:
    chapter: int
    verse: int
    reference: str
    generated: str
    category: str

    @property
    def key(self) -> str:
        return f"{self.chapter}:{self.verse}"

    def differences(self, *, context: int = 8, limit: int = 3) -> list[tuple[str, str]]:
        """The first few places the two normalised strings differ, as (reference, generated).

        Each side shows the differing characters between `context` characters of what they
        share, so a report line is readable without printing the whole verse.
        """
        matcher = difflib.SequenceMatcher(None, self.reference, self.generated, autojunk=False)
        found: list[tuple[str, str]] = []

        for tag, start_a, end_a, start_b, end_b in matcher.get_opcodes():
            if tag == "equal":
                continue

            before = self.reference[max(0, start_a - context) : start_a]
            after = self.reference[end_a : end_a + context]
            found.append(
                (
                    f"{before}[{self.reference[start_a:end_a]}]{after}",
                    f"{before}[{self.generated[start_b:end_b]}]{after}",
                )
            )

        return found[:limit]


def load_snapshot() -> Mapping[str, Sequence[Mapping[str, Any]]]:
    return qa.corrected_kemenag()


def _generated(record: Mapping[str, Any], chapter: int, verse: int) -> str:
    return normalise(romanize_verse(record["text"], RENDERER, chapter=chapter, verse=verse))


def measure_agreement(snapshot: Mapping[str, Sequence[Mapping[str, Any]]]) -> Agreement:
    exact = edits = length = verses = 0

    for chapter, verse, record in iter_verses(snapshot):
        reference = normalise(record["transliteration"])
        distance = edit_distance(reference, _generated(record, chapter, verse))
        verses += 1
        exact += distance == 0
        edits += distance
        length += len(reference)

    return Agreement(verses, exact, edits, length)


# ---------------------------------------------------------------------------------------
# Classifying disagreements
# ---------------------------------------------------------------------------------------


def _without_hamza(text: str) -> str:
    return text.replace("'", "")


def connected_phones(text: str) -> list[str]:
    """The phones of a verse read straight through: no stop except at the verse end.

    This is the sequence the independent engine is compared with.
    """
    words = verse_words(text)
    every_stop = frozenset(
        word.mark_ordinal for word in words if word.pause_after and word.mark_ordinal is not None
    )
    spoken = speak(verse_words(text, flipped_stops=every_stop))

    return [phone for word in spoken for phone in word.phones if phone != ARTICLE_BOUNDARY]


def phone_digest(text: str) -> str:
    """A short stable digest of `connected_phones`, to detect a generator change."""
    joined = " ".join(connected_phones(text))

    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:12]


def load_lines(path: Path) -> list[str]:
    """The non-blank, non-comment lines of a committed data file; missing means empty."""
    if not path.exists():
        return []

    lines = path.read_text(encoding="utf-8").splitlines()

    return [line.strip() for line in lines if line.strip() and not line.startswith("#")]


def load_witness(path: Path = WITNESS_PATH) -> dict[str, str]:
    """Verse key to the phone digest confirmed by the independent engine."""
    witness: dict[str, str] = {}

    for line in load_lines(path):
        key, digest = line.split()
        witness[key] = digest

    return witness


def _render_with_flips(text: str, flipped: frozenset[int]) -> str:
    words = verse_words(text, flipped_stops=flipped)

    return normalise(render(speak(words), SCHEMES[RENDERER]))


def _best_pause_variant(text: str, reference: str) -> frozenset[int]:
    """Greedily flip single pause decisions while that brings the verse closer to `reference`."""
    candidates = [word.mark_ordinal for word in verse_words(text) if word.mark_ordinal is not None]
    target = _without_hamza(reference)
    flipped: frozenset[int] = frozenset()
    best = edit_distance(target, _without_hamza(_render_with_flips(text, flipped)))

    while best:
        improvement: tuple[int, frozenset[int]] | None = None

        for ordinal in candidates:
            trial = flipped ^ {ordinal}
            distance = edit_distance(target, _without_hamza(_render_with_flips(text, trial)))

            if distance < best and (improvement is None or distance < improvement[0]):
                improvement = (distance, trial)

        if improvement is None:
            break

        best, flipped = improvement

    return flipped


def classify(
    chapter: int, verse: int, text: str, reference: str, witness: Mapping[str, str]
) -> str | None:
    """The disagreement class of one verse, or None when the generator agrees."""
    generated = normalise(romanize_verse(text, RENDERER, chapter=chapter, verse=verse))

    if generated == reference:
        return None

    flipped = _best_pause_variant(text, reference)
    variant = _render_with_flips(text, flipped)

    if _without_hamza(variant) == _without_hamza(reference):
        return Class.PAUSE_CHOICE if flipped else Class.HAMZA_SPACING

    if witness.get(f"{chapter}:{verse}") == phone_digest(text):
        return Class.REFERENCE_TYPO

    return Class.GENERATOR_GAP


def mismatches(
    snapshot: Mapping[str, Sequence[Mapping[str, Any]]], witness: Mapping[str, str] | None = None
) -> Iterator[Mismatch]:
    """Every verse the generator does not reproduce, with its class."""
    witness = load_witness() if witness is None else witness

    for chapter, verse, record in iter_verses(snapshot):
        reference = normalise(record["transliteration"])
        category = classify(chapter, verse, record["text"], reference, witness)

        if category is not None:
            generated = _generated(record, chapter, verse)
            yield Mismatch(chapter, verse, reference, generated, category)


# ---------------------------------------------------------------------------------------
# Comparison of English renderers at skeleton level
# ---------------------------------------------------------------------------------------

_SKELETON_FOLDS: Final = {
    "\u0101": "aa",
    "\u012b": "ii",
    "\u016b": "uu",
    "\u1e25": "h",
    "\u1e63": "s",
    "\u1e0d": "d",
    "\u1e6d": "t",
    "\u1e93": "z",
}
_SKELETON_SPELLINGS: Final = (
    ("ee", "ii"),
    ("oo", "uu"),
    ("ay", "ai"),
    ("aw", "au"),
    ("dh", "z"),
    ("th", "s"),
)


def skeleton(text: str) -> str:
    """A consonant and vowel-length skeleton, for comparing two English transliterations.

    Emphatics fold to their plain letters, `dh` and `th` fold to `z` and `s`, and the long
    vowel spellings (macrons, `ee`, `oo`) and diphthong spellings (`ay`, `aw`) fold to one
    form. Hamza, ayn, hyphens, spaces and punctuation are dropped. A run of the same vowel is
    one long vowel whatever its length (Tanzil writes `laaa`), and a run of the same consonant
    is one consonant (spelling of gemination and of assimilated `l` differs between sources).
    """
    text = unicodedata.normalize("NFC", text).lower()
    text = "".join(_SKELETON_FOLDS.get(character, character) for character in text)
    text = "".join(character for character in text if "a" <= character <= "z")

    for spelling, folded in _SKELETON_SPELLINGS:
        text = text.replace(spelling, folded)

    text = re.sub(r"([aiu])\1+", r"\1\1", text)

    return re.sub(r"([^aiu])\1+", r"\1", text)


def skeleton_error_rate(pairs: Sequence[tuple[str, str]]) -> float:
    """Edit distance over reference length between skeletons of (reference, candidate) pairs."""
    edits = length = 0

    for reference, candidate in pairs:
        skeleton_reference = skeleton(reference)
        edits += edit_distance(skeleton_reference, skeleton(candidate))
        length += len(skeleton_reference)

    return edits / length


# ---------------------------------------------------------------------------------------
# The report
# ---------------------------------------------------------------------------------------


def write_report(path: Path) -> None:
    """Write the Metric A numbers, every disagreement class with examples, and the full verse table.

    The per-class sections are capped for readability; the closing table is not.
    """
    snapshot = load_snapshot()
    agreement = measure_agreement(snapshot)
    found = list(mismatches(snapshot))
    counts = Counter(item.category for item in found)
    lines = [
        "# Romanisation report (id-skb against the Kemenag Latin field)",
        "",
        f"* verses compared: {agreement.verses}",
        f"* exact: {agreement.exact} ({agreement.exact_rate:.2%})",
        f"* character error rate: {agreement.character_error_rate:.3%}",
        "",
        "| class | verses |",
        "|---|---|",
        *(f"| {name} | {counts[name]} |" for name in Class.ALL),
        "",
    ]

    for name in Class.ALL:
        lines += [f"## {name} ({counts[name]})", ""]

        for item in [entry for entry in found if entry.category == name][:EXAMPLES_PER_CLASS]:
            lines.append(f"* {item.key}")

            for reference, generated in item.differences():
                lines.append(f"  * reference `{reference}`, generated `{generated}`")

        lines.append("")

    lines += [
        f"## Every non-matching verse ({len(found)})",
        "",
        "| verse | class |",
        "|---|---|",
        *(f"| {item.key} | {item.category} |" for item in found),
        "",
    ]

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
