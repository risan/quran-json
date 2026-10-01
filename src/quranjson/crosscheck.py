"""Repeatable text cross-check: our committed snapshots against independent witnesses.

A development tool, not part of the build and not run in CI (it needs the network). For each
script it downloads one or more witnesses into ``.cache/crosscheck/``, compares them verse by
verse (or chapter by chapter when the verse numbering differs) and prints, per witness, how
many units agree at three levels:

``raw``
    NFC-normalised text, byte for byte.
``vocalised``
    Letters and vowel marks, after the reviewed encoding-equivalence table
    (:data:`EQUIVALENCES`). Anything left over is a real difference in the text or a
    convention that is not yet in the table.
``skeleton``
    Consonant letters only: marks, signs, spaces and alef dropped, hamza seats folded.

Every witness lists its ancestry. Agreement between two copies of the same origin proves that
nobody corrupted the copy; it says nothing about an error in the origin.

Run it with ``uv run quran-json crosscheck [--script uthmani ...]``.
"""

from __future__ import annotations

import difflib
import gzip
import re
import unicodedata
from collections import Counter, defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final, Literal

import httpx
import orjson

from . import config, digitalkhatt, tanzil
from .http import USER_AGENT, Fetcher, RetryableStatus
from .jsonio import read_json

__all__ = [
    "EQUIVALENCES",
    "SCRIPTS",
    "WITNESSES",
    "Report",
    "compare",
    "raw_key",
    "skeleton_key",
    "strip_basmala",
    "vocalised_form",
    "vocalised_key",
]

#: ``{(chapter, verse): text}``.
Verses = dict[tuple[int, int], str]

CACHE_DIR: Final = config.ROOT / ".cache" / "crosscheck"

CHAPTER_COUNT: Final = 114

#: Most common code-point edits listed per witness in the report.
EDITS_SHOWN: Final = 6


class CrosscheckError(Exception):
    """A witness could not be fetched or parsed."""


# ---------------------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------------------

_WHITESPACE: Final = re.compile(r"\s+")

_TATWEEL_AND_CONTROLS: Final = re.compile("[\u0640\u00a0\u2009\u200a\u200b-\u200f\u2060\ufeff]")

#: Pause (waqf) signs, the rub el hizb sign and the sajdah sign: annotations that editions
#: place and encode differently.
_ANNOTATION_SIGNS: Final = re.compile("[\u06d6-\u06dc\u06de\u06e9]")

#: Open (stacked-side-by-side) tanween as KFGQPC and Quranpedia encode it.
_OPEN_TANWEEN: Final = {
    "\u08f0": "\u064b",
    "\u0657": "\u064b",
    "\u08f1": "\u064c",
    "\u065e": "\u064c",
    "\u08f2": "\u064d",
    "\u0656": "\u064d",
}

_OPEN_TANWEEN_GAP: Final = re.compile(
    "([\u08f0-\u08f2\u0656\u0657\u065e][\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed]*)"
    " +([\u0627\u0649])(?= |$)"
)

#: A tanween that carries an iqlab small meem (U+06E2 or U+06ED) later in the same word.
#: Tanzil keeps the doubled vowel and adds the meem; KFGQPC writes the single vowel with the
#: meem. Matching on the meem keeps the fold out of every other word, so a tanween lost
#: elsewhere (before an izhar letter, say) is still reported.
_IQLAB_TANWEEN: Final = re.compile("([ً-ٍ])(?=[ؐ-ًؚ-ٰٟۖ-ۣۡ-۬]*[ۭۢ])")

_TANWEEN_AS_HARAKA: Final = {"ً": "َ", "ٌ": "ُ", "ٍ": "ِ"}

#: Letters that mean one Arabic letter in a script-specific form.
_LETTER_VARIANTS: Final = {
    "ی": "ي",  # Farsi yeh
    "ے": "ي",  # yeh barree
    "ۓ": "ي",  # yeh barree with hamza above
    "ى": "ي",  # alef maksura
    "ک": "ك",  # keheh
    "ہ": "ه",  # heh goal
    "ھ": "ه",  # heh doachashmee
    "ۃ": "ة",  # teh marbuta goal
}


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def _drop_tatweel_and_controls(text: str) -> str:
    return _TATWEEL_AND_CONTROLS.sub("", text)


def _drop_annotation_signs(text: str) -> str:
    return _ANNOTATION_SIGNS.sub("", text)


def _kfgqpc_sukun(text: str) -> str:
    if "\u06e1" not in text:
        return text

    return text.replace("\u0652", "\u06df").replace("\u06e1", "\u0652")


def _tanween_gap(text: str) -> str:
    return _OPEN_TANWEEN_GAP.sub(r"\1\2", text)


def _open_tanween(text: str) -> str:
    return "".join(_OPEN_TANWEEN.get(char, char) for char in text)


def _letter_variants(text: str) -> str:
    return "".join(_LETTER_VARIANTS.get(char, char) for char in text)


def _hamza_madda_order(text: str) -> str:
    return text.replace("أ\u0653", "\u0654ا").replace("\u064e\u0654ا", "\u0654ا")


def _iqlab_tanween_as_haraka(text: str) -> str:
    return _IQLAB_TANWEEN.sub(lambda match: _TANWEEN_AS_HARAKA[match.group(1)], text)


def _remove_spaces(text: str) -> str:
    return _WHITESPACE.sub("", text)


@dataclass(frozen=True)
class Equivalence:
    """One reviewed encoding convention that the vocalised level treats as equal.

    ``example`` is a pair of strings that differ only by this convention: the unit tests
    assert that each pair is different raw and identical vocalised.
    """

    name: str
    why: str
    apply: Callable[[str], str]
    example: tuple[str, str]
    #: Spacing rows are skipped when a readable (space-preserving) form is wanted.
    spacing: bool = False


#: The reviewed table, applied in order. Keep it short: every row hides a class of
#: difference, so it must be a pure encoding choice, never a different reading.
#: Deliberately NOT folded: alef wasla vs plain alef, dagger alef vs full alef, hamza seats and
#: tanween vs a different haraka in the same position, except for the iqlab convention above;
#: those differences are reported.
EQUIVALENCES: Final[tuple[Equivalence, ...]] = (
    Equivalence(
        "tatweel, zero-width, bidi and word-joiner controls, no-break and hair spaces",
        "Layout characters: a tatweel stretches a letter, controls steer rendering, and "
        "KFGQPC-style hair spaces and word joiners kern around a dagger alef. None is part "
        "of the text.",
        _drop_tatweel_and_controls,
        ("ب\u0650س\u0652م\u0650\u200f", "ب\u0650\u0640س\u0652م\u0650"),
    ),
    Equivalence(
        "pause, rub el hizb and sajdah signs (U+06D6-06DC, U+06DE, U+06E9)",
        "Annotations rather than letters or vowels; editions place and encode them "
        "differently (Tanzil and KFGQPC disagree on which verses carry one).",
        _drop_annotation_signs,
        ("ق\u064eال\u064e \u06d6", "ق\u064eال\u064e"),
    ),
    Equivalence(
        "KFGQPC sukun (U+06E1) and round silent sign (U+0652)",
        "KFGQPC draws the round 'silent letter' circle with U+0652 and its sukun with "
        "U+06E1; Tanzil uses U+06DF for the circle and U+0652 for the sukun. Applied only to a "
        "text that contains U+06E1, so a Tanzil verse is never rewritten.",
        _kfgqpc_sukun,
        ("م\u0650ن\u0652", "م\u0650ن\u06e1"),
    ),
    Equivalence(
        "space after an open tanween",
        "KFGQPC writes an open tanween on the letter before the alef or alef maksura that "
        "carries its sound, with a space in between that is not a word boundary (marks such as "
        "a shadda may sit between). Only a lone "
        "alef or alef maksura after the space counts.",
        _tanween_gap,
        ("م\u08f0 \u0649", "م\u08f0\u0649"),
    ),
    Equivalence(
        "open tanween (U+08F0-08F2, U+0656, U+0657, U+065E)",
        "The same three signs, encoded as KFGQPC/Quranpedia's open (side-by-side) forms.",
        _open_tanween,
        ("م\u08f0", "م\u064b"),
    ),
    Equivalence(
        "alef maksura vs dotless yeh, Farsi yeh, keheh, heh goal",
        "Indo-Pak and Persian-keyboard code points for the Arabic letter the other copy "
        "writes in the Arabic form; same letter, different code point.",
        _letter_variants,
        ("ع\u064eل\u064eى\u0670", "ع\u064eل\u064eي\u0670"),
    ),
    Equivalence(
        "hamza-and-madda order, fatha before a hamza-alef pair",
        "Hamza above and madda on an alef are written in either order; Tanzil's fatha on "
        "the hamza-alef pair is KFGQPC's alef plus hamza with no separate fatha.",
        _hamza_madda_order,
        ("أ\u0653", "\u0654ا"),
    ),
    Equivalence(
        "tanween vs the matching haraka, only where the word carries an iqlab small meem",
        "Before a baa, Tanzil writes the doubled vowel plus the small meem (أَلِيمٌۢ) and "
        "KFGQPC the single vowel plus the meem (أَلِيمُۢ): 338 words in the Uthmani text, all "
        "of this one shape. The fold is tied to the meem, so a tanween lost anywhere else is "
        "reported.",
        _iqlab_tanween_as_haraka,
        ("أَلِيمٌۢ", "أَلِيمُۢ"),
    ),
    Equivalence(
        "word spacing",
        "Spaces are ignored below the raw level. Word boundaries are a typesetting choice "
        "in several copies (Tanzil's 'ما لي', Kemenag's run-together words) and are "
        "counted separately as 'spacing-only' differences.",
        _remove_spaces,
        ("ما لي", "مالي"),
        spacing=True,
    ),
)

_MARKS: Final = re.compile(
    "[\u0610-\u061a\u064b-\u065f\u0670\u06d6-\u06ed\u0890-\u089f\u08d3-\u08ff]"
)

#: Quranic signs, digits (Arabic-Indic, Persian, ASCII), brackets, dashes and private-use
#: glyph codes: everything that is neither a letter nor a mark nor a space.
_SIGNS: Final = re.compile(
    "[\u06dd\u06de\u06e9\u0600-\u0605\u06d4ە\u06fd\u06fe\u061e٠-٩۰-۹\\d()﴾﴿—\\-\ue000-\uf8ff]"
)

_ALEF_FORMS: Final = re.compile("[ٱآأإٲٳٵ]")

_BASMALA_LETTERS: Final = "بسمللهلرحمنلرحيم"
_SKIPPED_IN_BASMALA: Final = re.compile("[اٱآأإ\u0640\\s]")


def strip_basmala(text: str) -> str:
    """Remove a leading basmala, whatever its marks, spacing or alef spelling.

    Returns ``text`` unchanged when it does not begin with the basmala letters.
    """
    text = _letter_variants(_drop_tatweel_and_controls(_nfc(text)))
    expected = iter(_BASMALA_LETTERS)
    wanted = next(expected, None)
    position = 0

    while wanted is not None and position < len(text):
        char = text[position]

        if _MARKS.match(char) or _SKIPPED_IN_BASMALA.match(char):
            position += 1
        elif char == wanted:
            position += 1
            wanted = next(expected, None)
        else:
            return text

    if wanted is not None:
        return text

    while position < len(text) and (_MARKS.match(text[position]) or text[position].isspace()):
        position += 1

    return text[position:]


def raw_key(text: str) -> str:
    """The raw level: NFC bytes, ignoring leading and trailing whitespace."""
    return _nfc(text).strip()


def vocalised_form(text: str) -> str:
    """The text after the equivalence table, with single spaces kept for readability."""
    text = _nfc(text)

    for row in EQUIVALENCES:
        if not row.spacing:
            text = row.apply(text)

    return _WHITESPACE.sub(" ", _nfc(text)).strip()


def vocalised_key(text: str) -> str:
    """The vocalised level: the comparison key, spaces ignored."""
    return _remove_spaces(vocalised_form(text))


def skeleton_key(text: str) -> str:
    """The skeleton level: consonant letters only.

    Marks, signs, digits, spaces and every alef are dropped; alef forms, yeh/heh/kaf
    variants are unified first; hamza seats fold (ؤ to waw, ئ to yeh, bare hamza dropped).
    """
    text = _drop_tatweel_and_controls(_nfc(text))
    text = _letter_variants(text)
    text = _ALEF_FORMS.sub("ا", text)
    text = _MARKS.sub("", text)
    text = _SIGNS.sub("", text)
    text = text.replace("ؤ", "و").replace("ئ", "ي").replace("ء", "")

    return _remove_spaces(text).replace("ا", "")


# ---------------------------------------------------------------------------------------
# Registry: our scripts and their witnesses
# ---------------------------------------------------------------------------------------

Numbering = Literal["hafs", "own"]

JSDELIVR_QURAN_API: Final = "https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions"


@dataclass(frozen=True)
class Witness:
    """An independent (or deliberately not independent) copy of a text."""

    id: str
    label: str
    urls: tuple[str, ...]
    parse: Callable[[Sequence[bytes]], Verses]
    ancestry: str
    #: ``own`` when verse numbers follow a riwayah's own count, ``hafs`` for Hafs numbering.
    numbering: Numbering = "hafs"
    #: Tanzil's certificate expired on 2026-09-30 and was still expired at the time of
    #: writing; a read-only comparison leaks nothing, so verification is waived per witness.
    tls_verify: bool = True


@dataclass(frozen=True)
class Script:
    """One of our scripts and the witnesses it is checked against."""

    id: str
    path: Callable[[], Path]
    witnesses: tuple[str, ...]
    numbering: Numbering = "hafs"
    #: ``False`` for a script that carries no vowel marks: the vocalised level is skipped.
    vocalised: bool = True
    #: Chapters whose verse numbering differs from Hafs although the script is Hafs-numbered
    #: elsewhere. Compared per chapter only.
    shifted_chapters: frozenset[int] = frozenset()


def _flatten(chapters: dict[str, list[dict[str, Any]]]) -> Verses:
    return {
        (int(verse["chapter"]), int(verse["verse"])): str(verse["text"])
        for verses in chapters.values()
        for verse in verses
    }


def _parse_faw(raws: Sequence[bytes]) -> Verses:
    rows = orjson.loads(raws[0])["quran"]

    return {(int(row["chapter"]), int(row["verse"])): str(row["text"]) for row in rows}


def _parse_alquran_cloud(raws: Sequence[bytes]) -> Verses:
    surahs = orjson.loads(raws[0])["data"]["surahs"]

    return {
        (int(surah["number"]), int(ayah["numberInSurah"])): str(ayah["text"])
        for surah in surahs
        for ayah in surah["ayahs"]
    }


def _parse_quranpedia(raws: Sequence[bytes]) -> Verses:
    surahs = orjson.loads(gzip.decompress(raws[0]))["data"]["surahs"]

    return {
        (int(surah["id"]), int(ayah["number"])): str(ayah["text"])
        for surah in surahs
        for ayah in surah["ayahs"]
    }


def _parse_tanzil(raws: Sequence[bytes]) -> Verses:
    return _flatten(tanzil.parse_text(raws[0]))


def _parse_madina(raws: Sequence[bytes]) -> Verses:
    return _flatten(digitalkhatt.parse_text(raws[0]))


def _parse_kemenag_scrape(raws: Sequence[bytes]) -> Verses:
    verses: Verses = {}

    for chapter, raw in enumerate(raws, start=1):
        for row in orjson.loads(raw):
            verses[(chapter, int(row["ayah"]))] = str(row["arabic"])

    return verses


def _faw(edition: str, label: str, ancestry: str) -> Witness:
    return Witness(
        id=f"faw-{edition}",
        label=label,
        urls=(f"{JSDELIVR_QURAN_API}/ara-{edition}.json",),
        parse=_parse_faw,
        ancestry=ancestry,
    )


def _quranpedia(mushaf: int, label: str, ancestry: str, *, numbering: Numbering) -> Witness:
    return Witness(
        id=f"qp-{mushaf}",
        label=label,
        urls=(f"https://api.quranpedia.net/dumps/mushafs-{mushaf}.json.gz",),
        parse=_parse_quranpedia,
        ancestry=ancestry,
        numbering=numbering,
    )


_KFGQPC_VIA_FAW = "KFGQPC {what} via the fawazahmed0 mirror on jsDelivr"
_KFGQPC_VIA_QP = "KFGQPC {what} via Quranpedia; same origin as the fawazahmed0 copy"


def _witnesses() -> dict[str, Witness]:
    witnesses = [
        Witness(
            id="tanzil-uthmani",
            label="tanzil.net uthmani, today",
            urls=(config.TANZIL_DOWNLOAD.format(variant="uthmani"),),
            parse=_parse_tanzil,
            ancestry="Tanzil itself. A refresh check: shows our snapshot is verbatim, not a "
            "second opinion on the text.",
            tls_verify=False,
        ),
        Witness(
            id="tanzil-simple-clean",
            label="tanzil.net simple-clean, today",
            urls=(config.TANZIL_DOWNLOAD.format(variant="simple-clean"),),
            parse=_parse_tanzil,
            ancestry="Tanzil itself. A refresh check, not a second opinion.",
            tls_verify=False,
        ),
        Witness(
            id="tanzil-uthmani-min",
            label="tanzil.net uthmani-min, today",
            urls=(config.TANZIL_DOWNLOAD.format(variant="uthmani-min"),),
            parse=_parse_tanzil,
            ancestry="Tanzil itself. A refresh check, not a second opinion.",
            tls_verify=False,
        ),
        Witness(
            id="tanzil-simple-min",
            label="tanzil.net simple-min, today",
            urls=(config.TANZIL_DOWNLOAD.format(variant="simple-min"),),
            parse=_parse_tanzil,
            ancestry="Tanzil itself. A refresh check, not a second opinion.",
            tls_verify=False,
        ),
        Witness(
            id="tanzil-simple-plain",
            label="tanzil.net simple-plain, today",
            urls=(config.TANZIL_DOWNLOAD.format(variant="simple-plain"),),
            parse=_parse_tanzil,
            ancestry="Tanzil itself. A refresh check, not a second opinion.",
            tls_verify=False,
        ),
        Witness(
            id="alquran-uthmani",
            label="alquran.cloud quran-uthmani",
            urls=("https://api.alquran.cloud/v1/quran/quran-uthmani",),
            parse=_parse_alquran_cloud,
            ancestry="Tanzil 1.0.x, before the 2021-02-12 Tanzil 1.1 fix at 12:39 and 12:41. "
            "Same origin as Tanzil: tests the mirror, not the text.",
        ),
        Witness(
            id="alquran-simple",
            label="alquran.cloud quran-simple",
            urls=("https://api.alquran.cloud/v1/quran/quran-simple",),
            parse=_parse_alquran_cloud,
            ancestry="Tanzil 1.0.x (Imlaei). Same origin as Tanzil.",
        ),
        Witness(
            id="alquran-uthmani-min",
            label="alquran.cloud quran-uthmani-min",
            urls=("https://api.alquran.cloud/v1/quran/quran-uthmani-min",),
            parse=_parse_alquran_cloud,
            ancestry="Tanzil 1.0.x, minimal-marks Uthmani. Same origin as Tanzil: tests the "
            "mirror, not the text.",
        ),
        Witness(
            id="alquran-simple-min",
            label="alquran.cloud quran-simple-min",
            urls=("https://api.alquran.cloud/v1/quran/quran-simple-min",),
            parse=_parse_alquran_cloud,
            ancestry="Tanzil 1.0.x, minimal-marks Imlaei. Same origin as Tanzil.",
        ),
        Witness(
            id="digitalkhatt-madina",
            label="DigitalKhatt quran_text_madina.ts",
            urls=(
                "https://raw.githubusercontent.com/DigitalKhatt/digitalkhatt-js/HEAD/"
                "apps/site-angular/src/app/services/quran_text_madina.ts",
            ),
            parse=_parse_madina,
            ancestry="Tanzil's Uthmani text re-encoded for DigitalKhatt's font (it even keeps "
            "Tanzil's three word-spacing choices). Not independent of Tanzil.",
        ),
        _faw(
            "quranuthmanihaf",
            "KFGQPC Hafs Uthmanic (fawazahmed0 ara-quranuthmanihaf)",
            _KFGQPC_VIA_FAW.format(what="Hafs v13, Uthmanic script"),
        ),
        _faw(
            "qurankhaledhosn",
            "Khaled Hosny quran-data (fawazahmed0 ara-qurankhaledhosn)",
            "Khaled Hosny's quran-data, itself taken from Tanzil. Not independent of Tanzil.",
        ),
        _faw(
            "quranspelled",
            "Wikisource Imlaei (fawazahmed0 ara-quranspelled)",
            "Wikisource's Imlaei transcription: an independently typed text, so the only "
            "witness here that does not descend from Tanzil or KFGQPC.",
        ),
        _faw(
            "quranindopak",
            "KFGQPC Hafs Nastaleeq (fawazahmed0 ara-quranindopak)",
            _KFGQPC_VIA_FAW.format(what="Hafs Nastaleeq v10"),
        ),
        _faw(
            "quranwarsh",
            "KFGQPC Warsh (fawazahmed0 ara-quranwarsh)",
            _KFGQPC_VIA_FAW.format(what="Warsh v8")
            + "; verse numbers renumbered to Hafs, so chapter level only.",
        ),
        _faw(
            "quranqaloon",
            "KFGQPC Qaloon (fawazahmed0 ara-quranqaloon)",
            _KFGQPC_VIA_FAW.format(what="Qaloon v8")
            + "; verse numbers renumbered to Hafs, so chapter level only.",
        ),
        _faw(
            "quranshouba",
            "KFGQPC Shu'bah (fawazahmed0 ara-quranshouba)",
            _KFGQPC_VIA_FAW.format(what="Shu'bah") + "; renumbered to Hafs, so chapter level only.",
        ),
        _faw(
            "quransoosi",
            "KFGQPC Soosi (fawazahmed0 ara-quransoosi)",
            _KFGQPC_VIA_FAW.format(what="Soosi") + "; renumbered to Hafs, so chapter level only.",
        ),
        _faw(
            "qurandoori",
            "KFGQPC Doori (fawazahmed0 ara-qurandoori)",
            _KFGQPC_VIA_FAW.format(what="Doori v8")
            + "; verse numbers renumbered to Hafs, so chapter level only.",
        ),
        _quranpedia(
            1,
            "Quranpedia mushaf 1 (Imlaei)",
            "Quranpedia's Imlaei text, corrected by its team. Compare with Tanzil Imlaei.",
            numbering="hafs",
        ),
        _quranpedia(
            2,
            "Quranpedia mushaf 2 (KFGQPC Hafs)",
            _KFGQPC_VIA_QP.format(what="Hafs v13")
            + " (vocalised 6,234/6,236 identical to it in the research).",
            numbering="hafs",
        ),
        _quranpedia(
            3,
            "Quranpedia mushaf 3 (KFGQPC Hafs Nastaleeq)",
            _KFGQPC_VIA_QP.format(what="Hafs Nastaleeq v10")
            + ". Our hafs-nastaliq snapshot is this dump: a refresh check.",
            numbering="hafs",
        ),
        _quranpedia(
            4,
            "Quranpedia mushaf 4 (Warsh)",
            _KFGQPC_VIA_QP.format(what="Warsh v8")
            + ". Our warsh snapshot is this dump: a refresh check.",
            numbering="own",
        ),
        _quranpedia(
            6,
            "Quranpedia mushaf 6 (al-Duri)",
            _KFGQPC_VIA_QP.format(what="Doori v8")
            + ". Our duri snapshot is this dump: a refresh check.",
            numbering="own",
        ),
        _quranpedia(
            7,
            "Quranpedia mushaf 7 (Qalun)",
            _KFGQPC_VIA_QP.format(what="Qaloon v8")
            + ". Our qalun snapshot is this dump: a refresh check.",
            numbering="own",
        ),
        _quranpedia(
            9,
            "Quranpedia mushaf 9 (Shu'bah)",
            _KFGQPC_VIA_QP.format(what="Shu'bah")
            + ". Our shubah snapshot is this dump: a refresh check.",
            numbering="own",
        ),
        _quranpedia(
            10,
            "Quranpedia mushaf 10 (al-Susi)",
            _KFGQPC_VIA_QP.format(what="Soosi")
            + ". Our susi snapshot is this dump: a refresh check.",
            numbering="own",
        ),
        _quranpedia(
            12,
            "Quranpedia mushaf 12 (Libyan Awqaf Qalun)",
            "Byte-identical to mushaf 7 when last checked: not a second witness.",
            numbering="own",
        ),
        Witness(
            id="kemenag-2025-scrape",
            label="dyazincahya/quran-json-kemenag (2025 scrape)",
            urls=tuple(
                "https://raw.githubusercontent.com/dyazincahya/quran-json-kemenag/main/"
                f"surah/{chapter}.json"
                for chapter in range(1, CHAPTER_COUNT + 1)
            ),
            parse=_parse_kemenag_scrape,
            ancestry="A 2025 scrape of the same Kemenag (LPMQ) API: shows upstream drift, "
            "not an independent text.",
        ),
    ]

    return {witness.id: witness for witness in witnesses}


WITNESSES: Final[dict[str, Witness]] = _witnesses()


def _tanzil_path(variant: str) -> Callable[[], Path]:
    return lambda: config.tanzil_text_path(variant)


def _quranpedia_path(script: str) -> Callable[[], Path]:
    return lambda: config.quranpedia_path(script)


#: Scripts in the order they are reported. ``qpc-hafs`` is checked only once its snapshot
#: exists.
SCRIPTS: Final[dict[str, Script]] = {
    script.id: script
    for script in (
        Script(
            "uthmani",
            _tanzil_path("uthmani"),
            (
                "tanzil-uthmani",
                "qp-2",
                "faw-quranuthmanihaf",
                "alquran-uthmani",
                "digitalkhatt-madina",
                "faw-qurankhaledhosn",
            ),
        ),
        Script(
            "simple",
            _tanzil_path("simple"),
            ("qp-1", "faw-quranspelled", "alquran-simple"),
        ),
        Script(
            "uthmani-min",
            _tanzil_path("uthmani-min"),
            ("tanzil-uthmani-min", "alquran-uthmani-min"),
        ),
        Script(
            "simple-plain",
            _tanzil_path("simple-plain"),
            ("tanzil-simple-plain",),
        ),
        Script(
            "simple-min",
            _tanzil_path("simple-min"),
            ("tanzil-simple-min", "alquran-simple-min"),
        ),
        Script(
            "simple-clean",
            _tanzil_path("simple-clean"),
            ("tanzil-simple-clean", "qp-1", "alquran-simple"),
            vocalised=False,
        ),
        Script(
            "kemenag",
            config.kemenag_path,
            ("kemenag-2025-scrape", "qp-2"),
        ),
        Script(
            "indopak",
            config.digitalkhatt_path,
            ("faw-quranindopak",),
            shifted_chapters=frozenset({1}),
        ),
        Script(
            "hafs-nastaliq",
            _quranpedia_path("hafs-nastaliq"),
            ("qp-3", "faw-quranindopak"),
        ),
        Script("warsh", _quranpedia_path("warsh"), ("qp-4", "faw-quranwarsh"), numbering="own"),
        Script(
            "qalun",
            _quranpedia_path("qalun"),
            ("qp-7", "qp-12", "faw-quranqaloon"),
            numbering="own",
        ),
        Script("duri", _quranpedia_path("duri"), ("qp-6", "faw-qurandoori"), numbering="own"),
        Script(
            "shubah",
            _quranpedia_path("shubah"),
            ("qp-9", "faw-quranshouba"),
            numbering="own",
        ),
        Script(
            "susi",
            _quranpedia_path("susi"),
            ("qp-10", "faw-quransoosi"),
            numbering="own",
        ),
        Script(
            "qpc-hafs",
            _quranpedia_path("qpc-hafs"),
            ("qp-2", "faw-quranuthmanihaf"),
        ),
    )
}


# ---------------------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------------------


def load_ours(script: Script) -> Verses:
    """Read a committed snapshot the way the build does."""
    return _flatten(read_json(script.path()))


def _download(url: str, *, verify: bool) -> bytes:
    client = httpx.Client(
        timeout=120.0,
        follow_redirects=True,
        verify=verify,
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "gzip, deflate"},
    )

    try:
        with Fetcher(delay=0.2, client=client) as fetcher:
            return fetcher.get_bytes(url)
    finally:
        client.close()


def fetch(witness: Witness, cache_dir: Path, *, refresh: bool = False) -> Verses:
    """Download (or reuse) a witness and parse it.

    Raises:
        CrosscheckError: the download failed or the file does not parse.
    """
    directory = cache_dir / "downloads" / witness.id
    directory.mkdir(parents=True, exist_ok=True)
    raws: list[bytes] = []

    for index, url in enumerate(witness.urls):
        cached = directory / f"{index:03d}"

        if refresh or not cached.exists():
            try:
                body = _download(url, verify=witness.tls_verify)
            except (httpx.HTTPError, RetryableStatus) as error:
                raise CrosscheckError(f"{witness.id}: cannot download {url}: {error}") from error

            cached.write_bytes(body)

        raws.append(cached.read_bytes())

    try:
        verses = witness.parse(raws)
    except (ValueError, KeyError, TypeError, OSError) as error:
        raise CrosscheckError(f"{witness.id}: cannot parse the download: {error!r}") from error

    if not verses:
        raise CrosscheckError(f"{witness.id}: the download holds no verses")

    return verses


# ---------------------------------------------------------------------------------------
# Comparison
# ---------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Residual:
    """One difference that survived the level used for the residual report."""

    key: str
    ours: str
    theirs: str


@dataclass
class Report:
    """Outcome of one script against one witness."""

    script: str
    witness: str
    unit: Literal["verse", "chapter"]
    total: int = 0
    raw_same: int = 0
    vocalised_same: int | None = None
    skeleton_same: int = 0
    spacing_only: int = 0
    chapters_total: int = 0
    chapters_skeleton_same: int = 0
    missing_ours: int = 0
    missing_theirs: int = 0
    residuals: list[Residual] = field(default_factory=list)
    #: Code-point edits behind the verse-level residuals, most common first when printed.
    edits: Counter[tuple[str, str]] = field(default_factory=Counter)


def _comparable(text: str, chapter: int, verse: int) -> str:
    """Drop the basmala that Tanzil-style texts prefix to verse 1 of every chapter but the first."""
    return strip_basmala(text) if verse == 1 and chapter != 1 else text


def _chapter_texts(verses: Verses) -> dict[int, str]:
    by_chapter: dict[int, list[str]] = defaultdict(list)

    for chapter, verse in sorted(verses):
        by_chapter[chapter].append(verses[(chapter, verse)])

    return {chapter: strip_basmala(" ".join(parts)) for chapter, parts in by_chapter.items()}


def _word_spans(ours: str, theirs: str) -> list[tuple[str, str]]:
    ours_words, theirs_words = ours.split(" "), theirs.split(" ")
    matcher = difflib.SequenceMatcher(None, ours_words, theirs_words, autojunk=False)

    return [
        (" ".join(ours_words[i1:i2]), " ".join(theirs_words[j1:j2]))
        for tag, i1, i2, j1, j2 in matcher.get_opcodes()
        if tag != "equal"
    ]


def _code_point_edits(ours: str, theirs: str) -> list[tuple[str, str]]:
    matcher = difflib.SequenceMatcher(None, ours, theirs, autojunk=False)

    return [
        (
            " ".join(f"{ord(char):04X}" for char in ours[i1:i2]),
            " ".join(f"{ord(char):04X}" for char in theirs[j1:j2]),
        )
        for tag, i1, i2, j1, j2 in matcher.get_opcodes()
        if tag != "equal"
    ]


def compare(script: Script, ours: Verses, theirs: Verses, witness: Witness) -> Report:
    """Compare ``ours`` with one witness at the raw, vocalised and skeleton levels.

    Verse by verse when both sides number verses alike; chapter by chapter otherwise
    (a Hafs-numbered witness for a riwayah with its own count). Chapters listed in
    ``script.shifted_chapters`` are left out of the verse counts and covered by the
    chapter-level skeleton figure.
    """
    verse_mode = script.numbering == witness.numbering
    report = Report(script.id, witness.id, "verse" if verse_mode else "chapter")
    report.vocalised_same = 0 if script.vocalised else None
    residual_level = vocalised_key if script.vocalised else skeleton_key

    if verse_mode:
        keys = sorted(
            key for key in set(ours) & set(theirs) if key[0] not in script.shifted_chapters
        )
        report.missing_ours = len(set(theirs) - set(ours))
        report.missing_theirs = len(set(ours) - set(theirs))
        units = [
            (f"{chapter}:{verse}", ours[(chapter, verse)], theirs[(chapter, verse)], chapter, verse)
            for chapter, verse in keys
        ]
    else:
        our_chapters, their_chapters = _chapter_texts(ours), _chapter_texts(theirs)
        units = [
            (str(chapter), our_chapters[chapter], their_chapters[chapter], 0, 0)
            for chapter in sorted(set(our_chapters) & set(their_chapters))
        ]

    for key, ours_text, theirs_text, chapter, verse in units:
        report.total += 1

        if raw_key(ours_text) == raw_key(theirs_text):
            report.raw_same += 1

        if verse_mode:
            ours_text = _comparable(ours_text, chapter, verse)
            theirs_text = _comparable(theirs_text, chapter, verse)

        if skeleton_key(ours_text) == skeleton_key(theirs_text):
            report.skeleton_same += 1

        if report.vocalised_same is not None and vocalised_key(ours_text) == vocalised_key(
            theirs_text
        ):
            report.vocalised_same += 1

        if residual_level(ours_text) == residual_level(theirs_text):
            if len(vocalised_form(ours_text).split()) != len(vocalised_form(theirs_text).split()):
                report.spacing_only += 1

            continue

        if verse_mode:
            report.residuals.append(
                Residual(key, vocalised_form(ours_text), vocalised_form(theirs_text))
            )
            report.edits.update(
                _code_point_edits(residual_level(ours_text), residual_level(theirs_text))
            )
        else:
            for ours_span, theirs_span in _word_spans(
                vocalised_form(ours_text), vocalised_form(theirs_text)
            ):
                report.residuals.append(Residual(f"chapter {key}", ours_span, theirs_span))
                report.edits.update(
                    _code_point_edits(_remove_spaces(ours_span), _remove_spaces(theirs_span))
                )

    our_chapters, their_chapters = _chapter_texts(ours), _chapter_texts(theirs)
    shared = sorted(set(our_chapters) & set(their_chapters))
    report.chapters_total = len(shared)
    report.chapters_skeleton_same = sum(
        skeleton_key(our_chapters[chapter]) == skeleton_key(their_chapters[chapter])
        for chapter in shared
    )

    return report


# ---------------------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------------------


def _percent(same: int | None, total: int) -> str:
    if same is None or total == 0:
        return "n/a"

    return f"{int(1000 * same / total) / 10:.1f}%"


def format_table(script: Script, reports: list[Report]) -> str:
    """The per-script table printed to the terminal and saved in the results file."""
    header = (
        f"{'witness':<22} {'unit':<8} {'compared':>8} {'raw':>7} {'vocalised':>10} "
        f"{'skeleton':>9} {'spacing':>8} {'chapters = skeleton':>20}"
    )
    lines = [f"## {script.id}", header, "-" * len(header)]

    for report in reports:
        lines.append(
            f"{report.witness:<22} {report.unit:<8} {report.total:>8} "
            f"{_percent(report.raw_same, report.total):>7} "
            f"{_percent(report.vocalised_same, report.total):>10} "
            f"{_percent(report.skeleton_same, report.total):>9} "
            f"{report.spacing_only:>8} "
            f"{report.chapters_skeleton_same:>10}/{report.chapters_total:<9}"
        )

    for report in reports:
        witness = WITNESSES[report.witness]
        counts = (
            f"{report.raw_same}/{report.skeleton_same}/"
            f"{'-' if report.vocalised_same is None else report.vocalised_same}"
        )
        lines.append(f"  {witness.id}: {witness.label}. Ancestry: {witness.ancestry}")
        lines.append(f"    identical units raw/skeleton/vocalised of {report.total}: {counts}")

        for (ours_points, theirs_points), count in report.edits.most_common(EDITS_SHOWN):
            lines.append(f"      {count:5}  [{ours_points}] -> [{theirs_points}]")

        if report.missing_ours or report.missing_theirs:
            lines.append(
                f"    verses only in the witness: {report.missing_ours}, "
                f"only in ours: {report.missing_theirs}"
            )

    return "\n".join(lines)


def write_residuals(script: Script, reports: list[Report], cache_dir: Path) -> Path:
    """Write the residual differences of every witness to ``<cache>/<script>.tsv``."""
    path = cache_dir / f"{script.id}.tsv"
    path.parent.mkdir(parents=True, exist_ok=True)
    level = "vocalised" if script.vocalised else "skeleton"
    lines = [f"key\twitness\tours ({level})\twitness text"]

    for report in reports:
        lines.extend(
            f"{residual.key}\t{report.witness}\t{residual.ours}\t{residual.theirs}"
            for residual in report.residuals
        )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return path


def format_equivalences() -> str:
    """The encoding-equivalence table, for the results file."""
    return "\n".join(f"- {row.name}: {row.why}" for row in EQUIVALENCES)


def run(
    script_ids: Sequence[str],
    *,
    cache_dir: Path = CACHE_DIR,
    refresh: bool = False,
    out: Callable[[str], None] = print,
) -> int:
    """Check each script; return a process exit status (1 when a witness was unavailable)."""
    unavailable = 0
    downloaded: dict[str, Verses] = {}

    for script_id in script_ids:
        script = SCRIPTS[script_id]

        try:
            ours = load_ours(script)
        except FileNotFoundError:
            out(f"## {script.id}\n  skipped: no snapshot at {script.path()}\n")
            continue

        reports: list[Report] = []

        for witness_id in script.witnesses:
            witness = WITNESSES[witness_id]

            try:
                if witness_id not in downloaded:
                    downloaded[witness_id] = fetch(witness, cache_dir, refresh=refresh)
            except CrosscheckError as error:
                unavailable += 1
                out(f"  witness unavailable: {error}")
                continue

            reports.append(compare(script, ours, downloaded[witness_id], witness))

        out(format_table(script, reports))
        out(f"  residual differences: {write_residuals(script, reports, cache_dir)}\n")

    return 1 if unavailable else 0
