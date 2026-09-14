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
from typing import Any, Final

from . import jsonio

#: Project Gutenberg #16955 carries Yusuf Ali, Pickthall and Shakir side by side,
#: "re-proofed and corrected for Project Gutenberg against paper copies of the
#: translations by Irfan Ali". It is our independent witness for English editions.
GUTENBERG: Final = "https://www.gutenberg.org/ebooks/16955"


@dataclass(frozen=True)
class Correction:
    """One restored reading: `defective` must be present for `restored` to apply."""

    lang: str
    chapter: int
    verse: int
    defective: str
    restored: str
    evidence: str

    def key(self) -> str:
        return f"{self.lang} {self.chapter}:{self.verse}"


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
            if correction.defective not in text:
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
            "translator's wording is never edited, only repair of damaged text."
        ),
        "witness": GUTENBERG,
        "corrections": [
            {
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
    from . import config

    jsonio.write_json(config.QA_PATH, manifest(), pretty=True)
