"""Known transcription defects in upstream snapshots, and their restoration.

The public-domain editions are digitised by volunteers and occasionally carry
transcription damage. This module records each defect we have confirmed against an
independent witness, together with the restored reading, and applies the fix on every
snapshot load so a re-fetch cannot silently reintroduce it.

Corrections are deliberately additive and narrow: they restore a translator's text, they
never modernise, retitle, or otherwise edit it. Each entry is verified against the
defective fragment before being applied, so if upstream later fixes the text the build
fails loudly instead of double-correcting.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Final, Literal

from . import config, jsonio

#: Project Gutenberg #16955 carries Yusuf Ali, Pickthall and Shakir side by side,
#: "re-proofed and corrected for Project Gutenberg against paper copies of the
#: translations by Irfan Ali". It is our independent witness for English editions.
GUTENBERG: Final = "https://www.gutenberg.org/ebooks/16955"


@dataclass(frozen=True)
class Correction:
    """One restored reading: `defective` must be present for `restored` to apply.

    `lang` names the translation edition, or for ``kind="script"`` the script id.
    """

    lang: str
    chapter: int
    verse: int
    defective: str
    restored: str
    evidence: str
    kind: Literal["translation", "script"] = "translation"
    #: The defect is the start of the verse, so a repaired verse cannot match it again.
    at_start: bool = False

    def key(self) -> str:
        return f"{self.lang} {self.chapter}:{self.verse}"


#: Qur'an Kemenag's text is typed, and in 33 places the typist dropped or added a space. Each
#: row is (chapter, verse, upstream fragment, restored fragment); only the space differs.
#: Tanzil Uthmani 1.1, KFGQPC's Hafs (Quranpedia mushaf 2) and KFGQPC's Nastaleeq (mushaf 3)
#: all agree on the boundary for every row, and the letter at the break is a non-connecting
#: one (alef, dal, dhal, ra, zay, waw), so the fix can never change a rasm.
#: 31:27 `اَنَّ مَا` is deliberately absent: the break follows a connecting letter, so it can be
#: a genuine Indonesian-standard spelling and no witness settles it.
KEMENAG_SPACING: Final[tuple[tuple[int, int, str, str], ...]] = (
    (2, 71, "لَّاشِيَةَ", "لَّا شِيَةَ"),
    (2, 102, "مَاشَرَوْا", "مَا شَرَوْا"),
    (2, 145, "مَاجَاۤءَكَ", "مَا جَاۤءَكَ"),
    (2, 163, "لَآاِلٰهَ", "لَآ اِلٰهَ"),
    (2, 177, "الْبِرَّاَنْ", "الْبِرَّ اَنْ"),
    (2, 181, "بَعْدَمَا", "بَعْدَ مَا"),
    (2, 205, "وَ اللّٰهُ", "وَاللّٰهُ"),
    (2, 246, "وَقَدْاُخْرِجْنَا", "وَقَدْ اُخْرِجْنَا"),
    (3, 21, "بِغَيْرِحَقٍّۖ", "بِغَيْرِ حَقٍّۖ"),
    (3, 67, "مَاكَانَ", "مَا كَانَ"),
    (3, 106, "اَ كَفَرْتُمْ", "اَكَفَرْتُمْ"),
    (5, 58, "بِاَ نَّهُمْ", "بِاَنَّهُمْ"),
    (8, 6, "بَعْدَمَا", "بَعْدَ مَا"),
    (8, 47, "بِمَايَعْمَلُوْنَ", "بِمَا يَعْمَلُوْنَ"),
    (8, 63, "لَوْاَنْفَقْتَ", "لَوْ اَنْفَقْتَ"),
    (8, 67, "مَاكَانَ", "مَا كَانَ"),
    (8, 67, "عَزِيْزٌحَكِيْمٌ", "عَزِيْزٌ حَكِيْمٌ"),
    (8, 68, "لَوْلَاكِتٰبٌ", "لَوْلَا كِتٰبٌ"),
    (8, 69, "مِمَّاغَنِمْتُمْ", "مِمَّا غَنِمْتُمْ"),
    (9, 9, "مَاكَانُوْا", "مَا كَانُوْا"),
    (9, 17, "وَ فِى", "وَفِى"),
    (11, 22, "لَاجَرَمَ", "لَا جَرَمَ"),
    (11, 32, "فَاَ كْثَرْتَ", "فَاَكْثَرْتَ"),
    (11, 53, "مَاجِئْتَنَا", "مَا جِئْتَنَا"),
    (13, 37, "بَعْدَمَا", "بَعْدَ مَا"),
    (36, 43, "وَلَاهُمْ", "وَلَا هُمْ"),
    (38, 19, "وَالطَّيْرَمَحْشُوْرَةً", "وَالطَّيْرَ مَحْشُوْرَةً"),
    (40, 53, "وَلَقَدْاٰتَيْنَا", "وَلَقَدْ اٰتَيْنَا"),
    (42, 15, "لَاحُجَّةَ", "لَا حُجَّةَ"),
    (43, 68, "لَاخَوْفٌ", "لَا خَوْفٌ"),
    (43, 84, "وَّ فِى", "وَّفِى"),
    (45, 26, "لَارَيْبَ", "لَا رَيْبَ"),
    (56, 51, "الضَّاۤ لُّوْنَ", "الضَّاۤلُّوْنَ"),
)

KEMENAG_SPACING_WITNESS: Final = "https://api.quranpedia.net/dumps/mushafs-2.json.gz"


def _kemenag_spacing_corrections() -> tuple[Correction, ...]:
    return tuple(
        Correction(
            lang=config.KEMENAG_SCRIPT,
            chapter=chapter,
            verse=verse,
            defective=defective,
            restored=restored,
            kind="script",
            evidence=(
                f"{KEMENAG_SPACING_WITNESS} (KFGQPC Hafs), Tanzil Uthmani 1.1 and KFGQPC "
                f"Nastaleeq all {'separate' if ' ' in restored else 'join'} these letters; "
                "only the space is "
                f"{'inserted' if ' ' in restored else 'removed'}, the letters are untouched."
            ),
        )
        for chapter, verse, defective, restored in KEMENAG_SPACING
    )


#: Project Gutenberg #19786 prints Salomo Keyzer's Dutch Koran. The upstream snapshot (Tanzil's
#: `nl.keyzer`) lost the leading letters of the mystic-letter verses, leaving "M" for
#: "A. L. M." at 2:1. Gutenberg gives the full opening for each one.
GUTENBERG_DUTCH: Final = "https://www.gutenberg.org/ebooks/19786"

_KEYZER_OPENINGS: Final = (
    (2, "M", "A. L. M."),
    (3, "M", "A. L. M."),
    (7, "M. S", "A. L. M. S."),
    (12, "R. Dit zijn teekens", "E. L. R. Dit zijn teekens"),
    (13, "M. R. Ziehier", "A. L. M. R. Ziehier"),
    (14, "R. Dit boek", "E. L. R. Dit boek"),
    (15, "R. Dit zijn de teekens", "E. L. R. Dit zijn de teekens"),
    (19, "Y. A. S", "C. H. Y. A. S."),
    (20, "H", "T. H."),
    (26, "M", "T. S. M."),
    (27, "Dit zijn de teekenen van den Koran", "T. S. Dit zijn de teekenen van den Koran"),
    (28, "M", "T. S. M."),
    (29, "M", "A. L. M."),
    (30, "M", "A. L. M."),
    (31, "M", "A. L. M."),
    (32, "M", "A. L. M."),
)

KEYZER_CORRECTIONS: Final[tuple[Correction, ...]] = tuple(
    Correction(
        lang="dutch_keyzer",
        chapter=chapter,
        verse=1,
        defective=defective,
        restored=restored,
        evidence=(
            f"{GUTENBERG_DUTCH} opens chapter {chapter} with '{restored}'; the upstream "
            f"snapshot begins '{defective}', the leading letters lost."
        ),
        at_start=True,
    )
    for chapter, defective, restored in _KEYZER_OPENINGS
)

CORRECTIONS: Final[tuple[Correction, ...]] = (
    Correction(
        lang="english_yusuf_ali",
        chapter=5,
        verse=94,
        defective="game well within reach of game well within reach of",
        restored="game well within reach of",
        evidence=(
            f"{GUTENBERG} reads 'a little matter of game well within reach of your hands "
            "and your lances'; the upstream snapshot repeats the fragment 'game well "
            "within reach of', a duplication artefact."
        ),
    ),
    *_kemenag_spacing_corrections(),
    *KEYZER_CORRECTIONS,
)


def known() -> tuple[Correction, ...]:
    """Every recorded correction, for reporting."""
    return CORRECTIONS


def apply_corrections(
    lang: str, grouped: dict[str, list[dict[str, Any]]]
) -> dict[str, list[dict[str, Any]]]:
    """Restore every recorded defect for `lang`, in place.

    Raises:
        KeyError: the verse a correction targets is absent from the snapshot.
        ValueError: the verse no longer contains the defective fragment, which means
            upstream changed and the correction must be re-derived rather than applied.
    """
    for correction in CORRECTIONS:
        if correction.lang != lang:
            continue

        verses = grouped.get(str(correction.chapter))
        if verses is None:
            raise KeyError(f"{correction.key()}: chapter missing from snapshot")

        for item in verses:
            if item["verse"] != correction.verse:
                continue
            text = item["text"]
            present = (
                text.startswith(correction.defective)
                if correction.at_start
                else correction.defective in text
            )
            if not present:
                raise ValueError(
                    f"{correction.key()}: defective fragment absent, upstream may have "
                    f"changed -- re-derive the correction. Got: {text[:120]!r}"
                )
            item["text"] = text.replace(correction.defective, correction.restored, 1)
            break
        else:
            raise KeyError(f"{correction.key()}: verse missing from snapshot")

    return grouped


def manifest() -> dict[str, Any]:
    """Machine-readable record of every applied correction."""
    return {
        "note": (
            "Upstream transcription defects restored on load. Additive fixes only: the "
            "translator's wording is never edited, only repair of damaged text. Script "
            "corrections (`kind: script`) change only a space the upstream typist dropped or "
            "added; the letters are never touched."
        ),
        "witness": GUTENBERG,
        "corrections": [
            {
                "kind": c.kind,
                "lang": c.lang,
                "chapter": c.chapter,
                "verse": c.verse,
                "defective": c.defective,
                "restored": c.restored,
                "evidence": c.evidence,
            }
            for c in CORRECTIONS
        ],
    }


def write_manifest() -> None:
    """Persist the correction record next to the other build metadata."""
    jsonio.write_json(config.QA_PATH, manifest(), pretty=True)
