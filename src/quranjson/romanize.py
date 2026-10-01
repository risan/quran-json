"""A Latin-script transliteration of the Qur'an, generated from the Kemenag Arabic text.

The input is the Indonesian standard mushaf text (`data/kemenag/quran.json`, field `text`),
whose text carries no copyright (Minister of Religious Affairs Regulation 44/2016, Pasal
8(1)). The Kemenag Latin field is never read here: it is only a comparison reference in
`romanize_validation`.

The pipeline has four layers, each a plain function over the previous one:

1. **Tokenise** -- a verse becomes words; waqf marks are lifted to word-level flags. A mark may
   sit at the start of the *next* token in Kemenag text, but it belongs to the previous word.
2. **Phoneme layer** -- each word is read in connected Hafs recitation into a list of phone
   strings (see "Phones" below). Cross-word rules (hamzat al-wasl joining, idgham, iqlab)
   run over the whole verse.
3. **Pause layer** -- at the verse end and at a pausal waqf mark the word is read as if
   stopped on: final short vowel dropped, tanwin dropped (fatha tanwin becomes a long a),
   ta marbuta becomes h.
4. **Renderers** -- table-driven. Every renderer reads the same phones.

Phones
------
A phone is one of: a consonant key (`b t th j H kh d dh r z s sh S D T Z ` gh f q k l m n h w
y '`, where capitals are the emphatics and `` ` `` is ayn), a short vowel `a i u`, a long
vowel `A I U`, the imala vowel `E`, the article boundary `-`, or `TA_MARBUTA`.

Hafs exceptions
---------------
The Kemenag text writes each of them as a dedicated mark, so each is a mark rule rather than a
verse list. `HAFS_EXCEPTIONS` names every one of them with its verse, and the golden tests
pin each verse.

* imala (11:41 `majreh\u0101`): a dagger alif carrying U+06EA is read as the vowel `E`.
* ishmam (12:11 `ta'mann\u0101`): U+06EB is lip rounding, which has no Latin letter; ignored.
* tashil (41:44 `a'a'jamiyyun`): U+06EC is a softened hamza, which has no Latin letter; ignored.
* sakta (18:1, 36:52, 75:27, 83:14): U+06DC is a silence without breath. It breaks the flow
  (no joining, no idgham) but keeps every vowel, and is drawn as an ellipsis.
* small sin (2:245, 7:69, 52:37): a sad carrying U+06E3 is read as sin.
* complete idgham `nakhlukkum` (77:20) and `bi'sa lismu` (49:11) follow from the written
  shadda and the written lam vowel; they are pinned by tests only.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

from . import config
from .jsonio import read_json

__all__ = [
    "EDITIONS",
    "HAFS_EXCEPTIONS",
    "RENDERERS",
    "build_editions",
    "romanize_chapters",
    "romanize_verse",
    "write_report",
]

RENDERERS: Final = ("id-skb", "en", "en-simple")

# ---------------------------------------------------------------------------------------
# Arabic characters
# ---------------------------------------------------------------------------------------

FATHA: Final = "\u064e"
DAMMA: Final = "\u064f"
KASRA: Final = "\u0650"
FATHATAN: Final = "\u064b"
DAMMATAN: Final = "\u064c"
KASRATAN: Final = "\u064d"
SUKUN: Final = "\u0652"
SHADDA: Final = "\u0651"
DAGGER_ALEF: Final = "\u0670"
SUBSCRIPT_ALEF: Final = "\u0656"
INVERTED_DAMMA: Final = "\u0657"
MADDAH_ABOVE: Final = "\u0653"
SMALL_HIGH_MADDA: Final = "\u06e4"
HAMZA_ABOVE: Final = "\u0654"
HAMZA_BELOW: Final = "\u0655"
SMALL_HIGH_MEEM: Final = "\u06e2"
SMALL_LOW_MEEM: Final = "\u06ed"
ROUNDED_ZERO: Final = "\u06df"
RECTANGULAR_ZERO: Final = "\u06e0"
SMALL_HIGH_NOON: Final = "\u06e8"
SMALL_HIGH_YEH: Final = "\u06e7"
TATWEEL: Final = "\u0640"

SAKTA_MARK: Final = "\u06dc"  # small high seen, written between words
SMALL_LOW_SEEN: Final = "\u06e3"
IMALA_MARK: Final = "\u06ea"  # empty centre low stop
ISHMAM_MARK: Final = "\u06eb"  # empty centre high stop
TASHIL_MARK: Final = "\u06ec"  # rounded high stop with filled centre

WAQF_MUANAQA: Final = "\u06db"
PAUSE_MARKS: Final = frozenset("\u06d6\u06d7\u06d8\u06da")  # sli, qli, meem, jeem
# The signs a reader may stop at: the pausal ones, the "do not stop" lam-alef, mu'anaqa.
STOP_CANDIDATES: Final = PAUSE_MARKS | {"\u06d9", "\u06db"}
WAQF_MARKS: Final = frozenset("\u06d6\u06d7\u06d8\u06d9\u06da\u06db\u08d6\u06d5\u06d4\u06de\u06e9")
SMALL_MEEMS: Final = frozenset({SMALL_HIGH_MEEM, SMALL_LOW_MEEM})
SILENT_MARKS: Final = frozenset({ROUNDED_ZERO, RECTANGULAR_ZERO})
MADDAHS: Final = frozenset({MADDAH_ABOVE, SMALL_HIGH_MADDA})
HAMZA_MARKS: Final = frozenset({HAMZA_ABOVE, HAMZA_BELOW})
SHORT_VOWEL_MARKS: Final = (FATHA, KASRA, DAMMA)
TANWIN_MARKS: Final = (FATHATAN, KASRATAN, DAMMATAN)
VOWELLING: Final = frozenset(
    {FATHA, KASRA, DAMMA, SUKUN, SHADDA, *TANWIN_MARKS, DAGGER_ALEF, *HAMZA_MARKS}
)
# Marks that never start a letter cluster: they decorate the letter before them.
DIACRITICS: Final = frozenset(
    {
        *VOWELLING,
        SUBSCRIPT_ALEF,
        INVERTED_DAMMA,
        *MADDAHS,
        *SMALL_MEEMS,
        *SILENT_MARKS,
        SMALL_HIGH_NOON,
        SMALL_HIGH_YEH,
        SAKTA_MARK,
        SMALL_LOW_SEEN,
        IMALA_MARK,
        ISHMAM_MARK,
        TASHIL_MARK,
    }
)

# Marks that, at the start of a token, belong to the word before it.
LEADING_MARKS: Final = WAQF_MARKS | SMALL_MEEMS | {SAKTA_MARK, SMALL_HIGH_NOON}

ALEF: Final = "\u0627"
ALEF_MADDA: Final = "\u0622"
ALEF_MAKSURA: Final = "\u0649"
YEH: Final = "\u064a"
WAW: Final = "\u0648"
LAM: Final = "\u0644"
TEH_MARBUTA: Final = "\u0629"
SAD: Final = "\u0635"

# ---------------------------------------------------------------------------------------
# Phones
# ---------------------------------------------------------------------------------------

HAMZA: Final = "'"
AYN: Final = "`"
ARTICLE_BOUNDARY: Final = "-"
TA_MARBUTA: Final = "ta*"
# The waw that ends a plural verb (`tawallaw`), written with a silent alef after it. Unlike the
# waw of `lau` or of an assimilated tanwin, Kemenag spells it `au` even before another waw.
PLURAL_WAW: Final = "W"

CONSONANTS: Final[Mapping[str, str]] = {
    "\u0628": "b",
    "\u062a": "t",
    "\u062b": "th",
    "\u062c": "j",
    "\u062d": "H",
    "\u062e": "kh",
    "\u062f": "d",
    "\u0630": "dh",
    "\u0631": "r",
    "\u0632": "z",
    "\u0633": "s",
    "\u0634": "sh",
    SAD: "S",
    "\u0636": "D",
    "\u0637": "T",
    "\u0638": "Z",
    "\u0639": AYN,
    "\u063a": "gh",
    "\u0641": "f",
    "\u0642": "q",
    "\u0643": "k",
    LAM: "l",
    "\u0645": "m",
    "\u0646": "n",
    "\u0647": "h",
    WAW: "w",
    YEH: "y",
    "\u0621": HAMZA,
    "\u0623": HAMZA,
    "\u0625": HAMZA,
    "\u0624": HAMZA,
    "\u0626": HAMZA,
}
SHORT_VOWELS: Final = frozenset("aiu")
LONG_VOWELS: Final = frozenset("AIUE")
VOWELS: Final = SHORT_VOWELS | LONG_VOWELS
SHORTENED: Final = {"A": "a", "I": "i", "U": "u"}
LENGTHENED: Final = {"a": "A", "i": "I", "u": "U"}
CONSONANT_PHONES: Final = frozenset(CONSONANTS.values())
# Consonants whose final sound an initial shadda of the next word can absorb.
ASSIMILABLE_FINALS: Final = frozenset(
    {"n", "l", "t", "d", "dh", "th", "b", "q", "k", "m", "T", "Z", "D", "S", "r"}
)

# The nouns that begin with a hamzat al-wasl: ibn, ism, imru', ithnan.
WASL_NOUN_STEMS: Final = frozenset(
    {("\u0628", "\u0646"), ("\u0633", "\u0645"), ("\u0645", "\u0631"), ("\u062b", "\u0646")}
)

# The name of each letter that opens a chapter, as the phones of its spoken name.
LETTER_NAMES: Final[Mapping[str, tuple[str, ...]]] = {
    ALEF: (HAMZA, "a", "l", "i", "f"),
    LAM: ("l", "A", "m"),
    "\u0645": ("m", "I", "m"),
    "\u0631": ("r", "A"),
    SAD: ("S", "A", "d"),
    "\u0643": ("k", "A", "f"),
    "\u0647": ("h", "A"),
    YEH: ("y", "A"),
    "\u0639": (AYN, "a", "y", "n"),
    "\u0637": ("T", "A"),
    "\u0633": ("s", "I", "n"),
    "\u062d": ("H", "A"),
    "\u0642": ("q", "A", "f"),
    "\u0646": ("n", "U", "n"),
}

#: Every Hafs exception the generator hand-codes, with the verse that shows it.
HAFS_EXCEPTIONS: Final[Mapping[str, tuple[tuple[int, int], ...]]] = {
    "imala (majrehaa)": ((11, 41),),
    "ishmam (ta'mannaa)": ((12, 11),),
    "sakta": ((18, 1), (36, 52), (75, 27), (83, 14)),
    "tashil (a'a'jamiyyun)": ((41, 44),),
    "bi'sa lismu": ((49, 11),),
    "complete idgham (nakhlukkum)": ((77, 20),),
    "small sin over sad": ((2, 245), (7, 69), (52, 37)),
}

# ---------------------------------------------------------------------------------------
# Layer 1: tokenising
# ---------------------------------------------------------------------------------------


@dataclass
class Cluster:
    """One letter with the marks written on it."""

    base: str
    marks: set[str] = field(default_factory=set)

    def short_vowel(self) -> str | None:
        for mark, phone in zip(SHORT_VOWEL_MARKS, "aiu", strict=True):
            if mark in self.marks:
                return phone

        return None

    def tanwin(self) -> str | None:
        for mark, phone in zip(TANWIN_MARKS, "aiu", strict=True):
            if mark in self.marks:
                return phone

        return None

    def has_no_vowelling(self) -> bool:
        return not self.marks & VOWELLING


@dataclass
class Word:
    """One word after the phoneme layer, before the cross-word rules."""

    phones: list[str]
    wasl: bool = False
    ends_in_tanwin: bool = False
    iqlab: bool = False
    pause_after: bool = False
    sakta_after: bool = False
    starts_with_shadda: bool = False
    mark_ordinal: int | None = None

    @property
    def breaks_flow(self) -> bool:
        return self.pause_after or self.sakta_after


def split_clusters(token: str) -> list[Cluster]:
    clusters: list[Cluster] = []

    for character in token:
        if character in DIACRITICS:
            if clusters:
                clusters[-1].marks.add(character)

            continue

        clusters.append(Cluster(character))

    return clusters


def is_chapter_opening_letters(clusters: Sequence[Cluster]) -> bool:
    """True for letters read by name (alif lam mim), not as a word."""
    if not clusters:
        return False

    return all(
        cluster.base in LETTER_NAMES and not cluster.marks & (set(SHORT_VOWEL_MARKS) | {SUKUN})
        for cluster in clusters
    )


# ---------------------------------------------------------------------------------------
# Layer 2: the phoneme layer, one word at a time
# ---------------------------------------------------------------------------------------


class WordReader:
    """Reads one word in connected recitation.

    `initial` is true when the word begins the verse or follows a pause, where a hamzat
    al-wasl is pronounced instead of dropped.
    """

    def __init__(self, clusters: Sequence[Cluster], *, initial: bool) -> None:
        self.clusters = clusters
        self.initial = initial
        self.phones: list[str] = []
        self.wasl = False
        self.ends_in_tanwin = False
        self.iqlab = False
        self.article_lam_assimilated = False

    def read(self) -> Word:
        for index in range(len(self.clusters)):
            self._read_cluster(index)

        if self._small_meem_on_last_two_letters() and self._last_phone() == "n":
            self.iqlab = True

        return Word(
            self.phones,
            wasl=self.wasl,
            ends_in_tanwin=self.ends_in_tanwin,
            iqlab=self.iqlab,
        )

    # -- helpers --

    def _last_phone(self) -> str | None:
        return self.phones[-1] if self.phones else None

    def _previous_vowel(self) -> str | None:
        """The last phone, if it is a vowel; the article boundary is looked through."""
        for phone in reversed(self.phones):
            if phone in VOWELS:
                return phone

            if phone != ARTICLE_BOUNDARY:
                return None

        return None

    def _cluster_after(self, index: int) -> Cluster | None:
        if index + 1 < len(self.clusters):
            return self.clusters[index + 1]

        return None

    def _small_meem_on_last_two_letters(self) -> bool:
        return any(cluster.marks & SMALL_MEEMS for cluster in self.clusters[-2:])

    def _add_tanwin(self, vowel: str) -> None:
        self.phones += [vowel, "n"]
        self.ends_in_tanwin = True

    # -- dispatch --

    def _read_cluster(self, index: int) -> None:
        cluster = self.clusters[index]
        base = cluster.base

        if base == TATWEEL:
            self._read_tatweel(cluster)
        elif base == ALEF_MADDA:
            self._read_madda_alef(index)
        elif base == ALEF and cluster.marks & HAMZA_MARKS:
            self._read_consonant(index, "\u0621")
        elif base in (ALEF_MAKSURA, YEH) and cluster.marks & HAMZA_MARKS:
            self._read_consonant(index, "\u0626")
        elif base == ALEF:
            self._read_alef(index)
        elif base == ALEF_MAKSURA:
            self._read_alef_maksura(index)
        else:
            self._read_consonant(index, base)

    def _read_tatweel(self, cluster: Cluster) -> None:
        vowel = cluster.short_vowel()
        tanwin = cluster.tanwin()

        if cluster.marks & HAMZA_MARKS:
            self.phones.append(HAMZA)

            if DAGGER_ALEF in cluster.marks:
                self.phones.append("A")
            elif vowel:
                self.phones.append(vowel)

            if tanwin:
                self._add_tanwin(tanwin)
        elif vowel:
            self.phones.append(vowel)

    # -- alef --

    def _read_alef(self, index: int) -> None:
        cluster = self.clusters[index]
        vowel = cluster.short_vowel()
        tanwin = cluster.tanwin()

        if cluster.marks & SILENT_MARKS:
            return

        if DAGGER_ALEF in cluster.marks:
            self.phones += [HAMZA, "A"]
        elif cluster.marks & MADDAHS and not vowel:
            self._read_madda_alef(index)
        elif vowel:
            self.phones += [HAMZA, vowel]
        elif tanwin:
            self.phones.append(HAMZA)
            self._add_tanwin(tanwin)
        elif index == 0:
            self._read_initial_bare_alef()
        elif not self._is_silent_alef_before_article(index):
            self._lengthen_preceding_fatha()

    def _read_madda_alef(self, index: int) -> None:
        if index == 0 or self._previous_vowel() != "a":
            self.phones += [HAMZA, "A"]
        else:
            self.phones[-1] = "A"

    def _read_initial_bare_alef(self) -> None:
        """A hamzat al-wasl: dropped when the word is joined, pronounced after a pause."""
        self.wasl = True

        if not self.initial:
            return

        self.phones += [HAMZA, self._initial_wasl_vowel()]

    def _initial_wasl_vowel(self) -> str:
        """`al-` takes a, an imperative like `uqtul` takes u, everything else takes i."""
        following = self._cluster_after(0)

        if following is not None and following.base == LAM:
            return "a"

        stem_vowel = self.clusters[2].short_vowel() if len(self.clusters) > 3 else None
        is_noun = tuple(cluster.base for cluster in self.clusters[1:3]) in WASL_NOUN_STEMS

        return "u" if stem_vowel == "u" and not is_noun else "i"

    def _is_silent_alef_before_article(self, index: int) -> bool:
        """The alef of `al-` after a one-letter prefix (`wal-`, `bil-`), or of a joined wasl."""
        following = self._cluster_after(index)

        if following is None:
            return False

        prefixes = self.clusters[:index]
        prefix_letters_only = all(
            cluster.base in "\u0648\u0641\u0628\u0644\u0643\u0633\u062a" for cluster in prefixes
        )
        lam_of_article = following.base == LAM and (
            following.has_no_vowelling()
            or SUKUN in following.marks
            or (SHADDA in following.marks and DAGGER_ALEF not in following.marks)
        )
        wasl_after_conjunction = (
            index == 1
            and self.clusters[0].base in "\u0648\u0641\u0644"
            and bool(following.marks & {SUKUN, SHADDA})
        )

        return (index <= 2 and lam_of_article and prefix_letters_only) or wasl_after_conjunction

    def _lengthen_preceding_fatha(self) -> None:
        if self._last_phone() == "a" and not self.ends_in_tanwin:
            self.phones[-1] = "A"

    def _read_alef_maksura(self, index: int) -> None:
        cluster = self.clusters[index]
        vowel = cluster.short_vowel()

        if DAGGER_ALEF in cluster.marks:
            if self._last_phone() == "a":
                self.phones[-1] = "A"
            else:
                self.phones.append("A")
        elif SUBSCRIPT_ALEF in cluster.marks:
            self.phones[-1:] = ["I"]
        elif vowel and self._vowel_shifted_onto_alef_maksura(index):
            self.phones.append(LENGTHENED[vowel])
        elif vowel:
            self.phones += ["y", vowel]
        elif self.ends_in_tanwin:
            return
        elif self._last_phone() == "a":
            self.phones[-1] = "A"
        elif self._last_phone() == "i":
            self.phones[-1] = "I"

    def _vowel_shifted_onto_alef_maksura(self, index: int) -> bool:
        """`\u0641\u0649\u0650`: the kasra is written on the ya, but it is the vowel of the letter before.

        The result is a long vowel, not a consonant ya plus a short vowel.
        """
        before = self.clusters[index - 1] if index > 0 else None

        return before is not None and before.has_no_vowelling() and self._last_phone() not in VOWELS

    # -- consonants and semivowels --

    def _read_consonant(self, index: int, base: str) -> None:
        cluster = self.clusters[index]

        consonant = self._consonant_phone(index, base)

        if consonant is None:
            return

        if self._is_article_lam_before_sun_letter(index, base):
            self.article_lam_assimilated = True

            return

        if self._is_lam_of_allah_first_lam(index, base):
            return

        if SUKUN in cluster.marks and self._is_assimilated_into_next(index, base):
            return

        self._add_consonant(index, base, consonant)
        self._add_vowel_of(cluster)
        self._add_small_marks(index, cluster)

    def _consonant_phone(self, index: int, base: str) -> str | None:
        """The phone of a letter, or None when the letter is written but not pronounced."""
        cluster = self.clusters[index]
        is_semivowel = base in (WAW, YEH)

        if base == TEH_MARBUTA:
            return TA_MARBUTA

        if is_semivowel and SUKUN in cluster.marks and self._lengthen_previous_vowel(base):
            return None

        if (
            is_semivowel
            and cluster.has_no_vowelling()
            and not cluster.marks & {SUBSCRIPT_ALEF, INVERTED_DAMMA}
        ):
            return self._semivowel_without_vowelling(index, base)

        if base == SAD and SMALL_LOW_SEEN in cluster.marks:
            return "s"

        if base == WAW and SUKUN in cluster.marks and self._is_plural_waw(index):
            return PLURAL_WAW

        return CONSONANTS.get(base)

    def _lengthen_previous_vowel(self, semivowel: str) -> bool:
        """A waw after u, or a yeh after i, with sukun, only lengthens that vowel."""
        matching = "u" if semivowel == WAW else "i"
        last = self._last_phone()

        if last != matching:
            return False

        self.phones[-1] = LENGTHENED[last]

        return True

    def _is_plural_waw(self, index: int) -> bool:
        following = self._cluster_after(index)

        return (
            following is not None
            and following.base == ALEF
            and following.has_no_vowelling()
            and index + 2 == len(self.clusters)
        )

    def _semivowel_without_vowelling(self, index: int, base: str) -> str | None:
        """A bare waw or yeh is a long vowel's carrier (silent) or a real semivowel."""
        last = self._last_phone()

        if last == "A":
            return None

        if last == ("u" if base == WAW else "i"):
            if base == YEH:
                self.phones[-1] = "I"

            return None

        if last == "a" and base == WAW and index == len(self.clusters) - 1:
            return None

        return CONSONANTS[base]

    def _is_article_lam_before_sun_letter(self, index: int, base: str) -> bool:
        cluster = self.clusters[index]
        following = self._cluster_after(index)

        if base != LAM or not cluster.has_no_vowelling() or following is None:
            return False

        if SHADDA not in following.marks:
            return False

        return not (DAGGER_ALEF in following.marks and following.base == LAM)

    def _is_lam_of_allah_first_lam(self, index: int, base: str) -> bool:
        cluster = self.clusters[index]
        following = self._cluster_after(index)

        return (
            base == LAM
            and cluster.has_no_vowelling()
            and following is not None
            and following.base == LAM
            and SHADDA in following.marks
        )

    def _is_assimilated_into_next(self, index: int, base: str) -> bool:
        """A consonant with sukun before a shadda letter is spoken as that letter."""
        following = self._cluster_after(index)

        return (
            following is not None
            and SHADDA in following.marks
            and base not in (WAW, YEH, "\u0646", "\u0645")
        )

    def _add_consonant(self, index: int, base: str, consonant: str) -> None:
        cluster = self.clusters[index]

        if self.article_lam_assimilated:
            self.article_lam_assimilated = False
            self.phones += [consonant, ARTICLE_BOUNDARY, consonant]
        elif SHADDA in cluster.marks:
            if self._is_article_lam_with_shadda(index, base):
                self.phones += [consonant, ARTICLE_BOUNDARY, consonant]
            else:
                self.phones += [consonant, consonant]
        else:
            self.phones.append(consonant)

        if consonant == "l" and SUKUN in cluster.marks and self._ends_article(index):
            self.phones.append(ARTICLE_BOUNDARY)

    def _is_article_lam_with_shadda(self, index: int, base: str) -> bool:
        """`al-ladhi`: the lam of the article doubled with a following lam."""
        if base != LAM or DAGGER_ALEF in self.clusters[index].marks:
            return False

        if not 1 <= index <= 3:
            return False

        before = self.clusters[index - 1]

        return before.base == ALEF and before.has_no_vowelling()

    def _ends_article(self, index: int) -> bool:
        """The lam-with-sukun that closes `al` (or `lil`) when more of the word follows."""
        if self._cluster_after(index) is None:
            return False

        if index >= 1:
            before = self.clusters[index - 1]
            after_alef = (
                before.base == ALEF
                and index - 1 <= 2
                and (before.has_no_vowelling() or (index == 1 and self.initial))
            )

            if after_alef:
                return True

        return index == 1 and self.clusters[0].base == LAM

    def _add_vowel_of(self, cluster: Cluster) -> None:
        vowel = cluster.short_vowel()
        tanwin = cluster.tanwin()

        if INVERTED_DAMMA in cluster.marks:
            self.phones.append("U")
        elif SUBSCRIPT_ALEF in cluster.marks:
            self.phones.append("I")
        elif DAGGER_ALEF in cluster.marks:
            self.phones.append("E" if IMALA_MARK in cluster.marks else "A")
        elif vowel:
            long_form = SMALL_HIGH_YEH in cluster.marks
            self.phones.append(LENGTHENED[vowel] if long_form else vowel)
        elif tanwin:
            self._add_tanwin(tanwin)

    def _add_small_marks(self, index: int, cluster: Cluster) -> None:
        if cluster.marks & SMALL_MEEMS:
            if index < len(self.clusters) - 1 and self._last_phone() == "n":
                self.phones[-1] = "m"
            else:
                self.iqlab = True

        if SMALL_HIGH_NOON in cluster.marks:
            self.phones.append("n")


# ---------------------------------------------------------------------------------------
# Tokenising a verse into words
# ---------------------------------------------------------------------------------------


class _StopMarks:
    """Lifts the waqf marks of a verse to pause flags on the words that carry them.

    A word that carries a mark a reader may stop at (any of the six waqf signs) gets an
    ordinal. `flipped` lists ordinals whose stop decision is inverted; the validation report
    uses it to ask whether a verse could match Kemenag's romanisation with other pause choices.
    """

    def __init__(self, flipped: frozenset[int]) -> None:
        self.flipped = flipped
        self.muanaqa_seen = 0
        self.next_ordinal = 0
        self.default_stop: dict[int, bool] = {}

    def apply(self, word: Word, marks: Sequence[str]) -> None:
        for mark in marks:
            if mark in STOP_CANDIDATES:
                self._apply_stop_candidate(word, mark)
            elif mark == SAKTA_MARK:
                word.sakta_after = True
            elif mark in SMALL_MEEMS:
                word.iqlab = True
            elif mark == SMALL_HIGH_NOON:
                _add_written_noon(word)

    def _apply_stop_candidate(self, word: Word, mark: str) -> None:
        if word.mark_ordinal is None:
            word.mark_ordinal = self.next_ordinal
            self.default_stop[word.mark_ordinal] = False
            self.next_ordinal += 1

        if mark in PAUSE_MARKS:
            self.default_stop[word.mark_ordinal] = True
        elif mark == WAQF_MUANAQA:
            self.muanaqa_seen += 1

            if self.muanaqa_seen % 2 == 0:
                self.default_stop[word.mark_ordinal] = True

        flipped = word.mark_ordinal in self.flipped
        word.pause_after = self.default_stop[word.mark_ordinal] != flipped


def _add_written_noon(word: Word) -> None:
    """A small noon at the start of the next word is the tanwin written as vowel plus noon."""
    word.phones.append("n")
    word.ends_in_tanwin = True


def verse_words(text: str, *, flipped_stops: frozenset[int] = frozenset()) -> list[Word]:
    """Split a verse into words, apply the waqf marks, and read each word."""
    words: list[Word] = []
    stop_marks = _StopMarks(flipped_stops)

    for token in text.split():
        leading, token = _split_leading_marks(token)
        marks = [
            character for character in token if character in WAQF_MARKS or character == SAKTA_MARK
        ]
        core = "".join(
            character
            for character in token
            if character not in WAQF_MARKS and character != SAKTA_MARK
        )

        if words:
            stop_marks.apply(words[-1], leading)

        clusters = split_clusters(core)

        if not clusters:
            if words:
                stop_marks.apply(words[-1], marks)

                if any(character in SMALL_MEEMS for character in core):
                    words[-1].iqlab = True

            continue

        words.extend(_read_token(clusters, words))
        stop_marks.apply(words[-1], marks)

    return words


def _split_leading_marks(token: str) -> tuple[str, str]:
    """Marks at the start of a token belong to the word before it."""
    length = 0

    while length < len(token) and token[length] in LEADING_MARKS:
        length += 1

    return token[:length], token[length:]


def _read_token(clusters: list[Cluster], words: Sequence[Word]) -> list[Word]:
    if not words:
        clusters[0].marks.discard(SHADDA)

        if is_chapter_opening_letters(clusters):
            return [Word(list(LETTER_NAMES[cluster.base])) for cluster in clusters]

    initial = not words or words[-1].breaks_flow
    word = WordReader(clusters, initial=initial).read()
    first = clusters[0]
    word.starts_with_shadda = SHADDA in first.marks and first.base != ALEF

    return [word]


# ---------------------------------------------------------------------------------------
# Cross-word rules and the pause layer
# ---------------------------------------------------------------------------------------


@dataclass
class SpokenWord:
    """A word after the cross-word rules and the pause layer, ready to render."""

    phones: list[str]
    joined_to_previous: bool = False
    pause: bool = False
    sakta: bool = False


def pause_form(phones: Sequence[str], *, ends_in_tanwin: bool) -> list[str]:
    """The word as spoken when stopping on it."""
    result = list(phones)

    if ends_in_tanwin and len(result) >= 2 and result[-1] == "n":
        vowel = result[-2]
        del result[-2:]

        if result and result[-1] == TA_MARBUTA:
            result[-1] = "h"
        elif vowel == "a":
            result.append("A")

        return result

    if _ends_in_droppable_vowel(result):
        result.pop()

    if result and result[-1] == TA_MARBUTA:
        result[-1] = "h"

    return result


def _ends_in_droppable_vowel(phones: Sequence[str]) -> bool:
    """A final short vowel, or the long vowel of a pronoun suffix (`lahu`, `bihi`)."""
    if not phones:
        return False

    if phones[-1] in SHORT_VOWELS:
        return True

    return len(phones) >= 2 and phones[-1] in ("U", "I") and phones[-2] == "h"


def speak(words: Sequence[Word]) -> list[SpokenWord]:
    """Apply wasl, idgham and iqlab across word boundaries, then the pause layer."""
    spoken: list[SpokenWord] = []

    for index, word in enumerate(words):
        phones = list(word.phones)
        previous_word = words[index - 1] if index else None
        previous = spoken[-1] if spoken else None
        joined = False

        if previous_word is not None and previous is not None and not previous_word.breaks_flow:
            if word.wasl:
                joined = True
                _join_wasl(previous, previous_word)

            if word.starts_with_shadda:
                phones = _absorb_initial_shadda(previous, phones)

            if previous_word.iqlab and previous.phones and previous.phones[-1] == "n":
                previous.phones[-1] = "m"
        elif word.starts_with_shadda and _is_doubled(phones):
            phones = phones[1:]

        spoken.append(
            SpokenWord(
                phones,
                joined_to_previous=joined,
                sakta=word.sakta_after and not word.pause_after,
            )
        )

    for index, word in enumerate(words):
        is_last = index == len(words) - 1

        if is_last or word.pause_after:
            spoken[index].phones = pause_form(
                spoken[index].phones, ends_in_tanwin=word.ends_in_tanwin
            )
            spoken[index].pause = True

    return spoken


def _join_wasl(previous: SpokenWord, previous_word: Word) -> None:
    last = previous.phones[-1] if previous.phones else None

    if last in SHORTENED:
        previous.phones[-1] = SHORTENED[last]
    elif last == "n" and previous_word.ends_in_tanwin:
        previous.phones.append("i")


def _absorb_initial_shadda(previous: SpokenWord, phones: list[str]) -> list[str]:
    """Idgham across words: the shadda on this word's first letter doubles the last of the previous.

    The written text already carries the assimilation, so the previous word's final
    consonant is replaced by this word's first, and one of the doubled pair is dropped.
    """
    first = phones[0]

    if first == HAMZA or first not in CONSONANT_PHONES:
        return phones

    last = previous.phones[-1] if previous.phones else None

    if last == PLURAL_WAW:
        last = "w"

    if last == first and _is_doubled(phones):
        return phones[1:]

    if last in ASSIMILABLE_FINALS:
        previous.phones[-1] = first

        if _is_doubled(phones):
            phones = phones[1:]

        if _is_doubled(phones):
            phones = phones[1:]

    return phones


def _is_doubled(phones: Sequence[str]) -> bool:
    return len(phones) > 1 and phones[0] == phones[1]


# ---------------------------------------------------------------------------------------
# Layer 4: renderers
# ---------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Scheme:
    """A romanisation: how each phone is spelled."""

    consonants: Mapping[str, str]
    vowels: Mapping[str, str]
    diphthongs: Mapping[str, str]
    sakta: str
    space_before_prefixed_hamza: bool = False
    final_stop: str = ""


_ID_SKB_CONSONANTS: Final = {
    "th": "\u1e61",
    "H": "\u1e25",
    "dh": "\u017c",
    "sh": "sy",
    "S": "\u1e63",
    "D": "\u1e0d",
    "T": "\u1e6d",
    "Z": "\u1e93",
    AYN: "\u2018",
    "gh": "g",
}
_ENGLISH_CONSONANTS: Final = {
    "H": "\u1e25",
    "S": "\u1e63",
    "D": "\u1e0d",
    "T": "\u1e6d",
    "Z": "\u1e93",
    AYN: "\u02bf",
    HAMZA: "\u02be",
}
# ASCII keeps the hamza as ' and the ayn as `, so the two stay distinguishable.
_ASCII_CONSONANTS: Final = {"H": "h", "S": "s", "D": "d", "T": "t", "Z": "z"}

SCHEMES: Final[Mapping[str, Scheme]] = {
    "id-skb": Scheme(
        consonants=_ID_SKB_CONSONANTS,
        vowels={
            "a": "a",
            "i": "i",
            "u": "u",
            "A": "\u0101",
            "I": "\u012b",
            "U": "\u016b",
            "E": "\u00ea",
        },
        diphthongs={"w": "au", "y": "ai"},
        sakta="\u2026",
        space_before_prefixed_hamza=True,
        final_stop=".",
    ),
    "en": Scheme(
        consonants=_ENGLISH_CONSONANTS,
        vowels={
            "a": "a",
            "i": "i",
            "u": "u",
            "A": "\u0101",
            "I": "\u012b",
            "U": "\u016b",
            "E": "\u0113",
        },
        diphthongs={"w": "aw", "y": "ay"},
        sakta="\u2026",
    ),
    "en-simple": Scheme(
        consonants=_ASCII_CONSONANTS,
        vowels={"a": "a", "i": "i", "u": "u", "A": "aa", "I": "ee", "U": "oo", "E": "ay"},
        diphthongs={"w": "aw", "y": "ay"},
        sakta="...",
    ),
}


def render(spoken: Sequence[SpokenWord], scheme: Scheme) -> str:
    pieces: list[str] = []

    for index, word in enumerate(spoken):
        following = spoken[index + 1] if index + 1 < len(spoken) else None
        text = _render_word(word, following, scheme)

        if word.joined_to_previous and pieces:
            pieces[-1] += text
        else:
            pieces.append(text)

        if word.pause and following is not None:
            pieces[-1] += ","
        elif word.sakta and following is not None:
            pieces[-1] += scheme.sakta

    result = " ".join(pieces).replace("--", "-")

    return _capitalise(result) + scheme.final_stop if result else result


def _render_word(word: SpokenWord, following: SpokenWord | None, scheme: Scheme) -> str:
    phones = [("t" if phone == TA_MARBUTA else phone) for phone in word.phones]
    next_first = following.phones[0] if following and following.phones else None
    parts: list[str] = []

    for index, phone in enumerate(phones):
        if phone == ARTICLE_BOUNDARY:
            parts.append("-")
        elif phone == HAMZA and _hamza_is_not_written(index, phones, word):
            continue
        elif phone == HAMZA and _hamza_follows_prefix(index, phones, scheme):
            parts.append(" ")
        elif phone == PLURAL_WAW:
            _append_plural_waw(parts, index, phones, scheme)
        elif _is_diphthong_end(index, phones, next_first):
            parts[-1] = scheme.diphthongs[phone]
        elif phone in VOWELS:
            parts.append(scheme.vowels[phone])
        else:
            parts.append(scheme.consonants.get(phone, phone))

    return "".join(parts)


def _append_plural_waw(parts: list[str], index: int, phones: Sequence[str], scheme: Scheme) -> None:
    if index > 0 and phones[index - 1] == "a":
        parts[-1] = scheme.diphthongs["w"]
    else:
        parts.append(scheme.consonants.get("w", "w"))


def _hamza_is_not_written(index: int, phones: Sequence[str], word: SpokenWord) -> bool:
    """A hamza that opens a word is not written; neither is one after the article."""
    starts_word = index == 0 and not word.joined_to_previous

    return starts_word or (index > 0 and phones[index - 1] == ARTICLE_BOUNDARY)


def _hamza_follows_prefix(index: int, phones: Sequence[str], scheme: Scheme) -> bool:
    """Kemenag spaces off a vowelled hamza after the prefix `wa`, `fa` or `ya`.

    It writes `fa'tu` for a hamza with sukun, and spaces or apostrophes the rest about
    equally (`fa in` against `fa'in`); the spaced form is the majority.
    """
    if not scheme.space_before_prefixed_hamza or index != 2:
        return False

    if len(phones) < 4 or phones[3] not in VOWELS:
        return False

    return (phones[0] in ("w", "f") and phones[1] == "a") or (phones[0] == "y" and phones[1] == "A")


def _is_diphthong_end(index: int, phones: Sequence[str], next_first: str | None) -> bool:
    """A w or y after a, with no vowel after it and no doubling: `au`, `ai`."""
    phone = phones[index]

    if phone not in ("w", "y") or index == 0 or phones[index - 1] != "a":
        return False

    is_last = index + 1 == len(phones)

    if not is_last and phones[index + 1] in VOWELS:
        return False

    if not is_last and phones[index + 1] == phone:
        return False

    return not (is_last and next_first == phone)


def _capitalise(text: str) -> str:
    for index, character in enumerate(text):
        if character.isalpha():
            return text[:index] + character.upper() + text[index + 1 :]

    return text


# ---------------------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------------------


def romanize_verse(text: str, renderer: str, *, chapter: int, verse: int) -> str:
    """Romanise one verse of Hafs text.

    `chapter` and `verse` identify the verse in Hafs numbering. They are required so that a
    verse-specific rule can never be applied to the wrong reading.
    """
    if renderer not in SCHEMES:
        raise ValueError(f"unknown renderer {renderer!r}; expected one of {RENDERERS}")

    if chapter < 1 or verse < 1:
        raise ValueError(f"invalid verse id {chapter}:{verse}")

    return render(speak(verse_words(text)), SCHEMES[renderer])


def romanize_chapters(
    snapshot: Mapping[str, Sequence[Mapping[str, Any]]], renderer: str
) -> list[dict[str, Any]]:
    """114 chapter objects, each with its verses' `id` and `transliteration`."""
    return [
        {
            "id": int(chapter),
            "verses": [
                {
                    "id": int(verse["verse"]),
                    "transliteration": romanize_verse(
                        verse["text"],
                        renderer,
                        chapter=int(chapter),
                        verse=int(verse["verse"]),
                    ),
                }
                for verse in sorted(verses, key=lambda item: int(item["verse"]))
            ],
        }
        for chapter, verses in sorted(snapshot.items(), key=lambda item: int(item[0]))
    ]


def build_editions(
    snapshot: Mapping[str, Sequence[Mapping[str, Any]]] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Every renderer's chapters, generated from the Kemenag snapshot."""
    if snapshot is None:
        snapshot = read_json(config.kemenag_path())

    return {renderer: romanize_chapters(snapshot, renderer) for renderer in RENDERERS}


_REVIEW_NOTE: Final = "machine-generated; not yet reviewed by a qualified reader"
_SOURCE_URL: Final = "https://quran.kemenag.go.id/"
_LICENSE: Final = {
    "status": "granted",
    "text": (
        "CC BY-SA 4.0, the licence of this repository. Generated from the Arabic text of the "
        "Mushaf Standar Indonesia (Indonesian Ministry of Religious Affairs, Kemenag), which "
        "carries no copyright (PMA 44/2016, Pasal 8(1)); the romanisation is machine-generated."
    ),
    "url": "https://creativecommons.org/licenses/by-sa/4.0/",
}
_AUTHOR: Final = "quran-json (generated from the Kemenag Arabic text)"


def _edition(key: str, language: str, name: str, method: str) -> dict[str, Any]:
    """One catalogue entry, minus the `path` and `files` the publisher adds."""
    return {
        "key": key,
        "edition": f"transliteration_{key}",
        "language": language,
        "name": name,
        "reading": "hafs",
        "verse_ids": "hafs",
        "author": _AUTHOR,
        "source": _SOURCE_URL,
        "method": method,
        "license": dict(_LICENSE),
        "review": _REVIEW_NOTE,
    }


EDITIONS: Final[tuple[dict[str, Any], ...]] = (
    _edition(
        "id-skb",
        "id",
        "Indonesian transliteration (SKB 1987)",
        "Rule-based: Hafs connected-reading rules and pausal forms applied to the Arabic text, "
        "spelled in the Indonesian SKB 1987 Latin convention that Kemenag uses.",
    ),
    _edition(
        "en",
        "en",
        "English transliteration (with diacritics)",
        "Rule-based: Hafs connected-reading rules and pausal forms applied to the Arabic text, "
        "spelled with macrons, dots below, and the modifier letters \u02bf (ayn) and \u02be "
        "(hamza).",
    ),
    _edition(
        "en-simple",
        "en",
        "English transliteration (plain ASCII)",
        "Rule-based: Hafs connected-reading rules and pausal forms applied to the Arabic text, "
        "spelled in ASCII: long vowels aa ee oo, emphatics as plain letters, hamza as ' and "
        "ayn as a backtick.",
    ),
)


def iter_verses(
    snapshot: Mapping[str, Sequence[Mapping[str, Any]]],
) -> Iterator[tuple[int, int, Mapping[str, Any]]]:
    """(chapter, verse, record) for every verse, in reading order."""
    for chapter, verses in sorted(snapshot.items(), key=lambda item: int(item[0])):
        for record in sorted(verses, key=lambda item: int(item["verse"])):
            yield int(chapter), int(record["verse"]), record


def write_report(path: Path) -> None:
    """Write the disagreement report; see `romanize_validation.write_report`."""
    from .romanize_validation import write_report as write

    write(path)
