"""Qur'anpedia.net's Maghribi riwayat: Warsh ʿan Nafiʿ and Qalun ʿan Nafiʿ.

These are the two readings of the Maghrib, and they are **riwayat, not orthographies**: a
different reading changes the consonants and vowels of the text and, in places, where one
ayah ends and the next begins. Neither is interchangeable with the Hafs scripts.

Provenance and licence, verified 2026-09-18 from the rights holder's own pages:

* The dumps are Qur'anpedia.net's, at `https://api.quranpedia.net/dumps`, one gzipped JSON
  per mushaf, versioned and checksummed on the page. Their text for both riwayat is the
  King Fahd Complex (KFGQPC) printed mushaf, as the dump's own `description` states
  ("نسخة موافقة للمطبوع").
* Their licence (https://api.quranpedia.net/dumps/LICENSE.md, version 2026-09-18): "Free to
  use inside apps, websites, bots, and research tools -- no attribution required.
  **Republishing this data -- in full or in part -- as a downloadable database or dataset
  requires**: (1) crediting **Quranpedia.net** as the source with a link, and (2) stating
  this dump's version." This dataset is a downloadable dataset, so both conditions apply:
  the attribution is rendered in `manifest.json`, `meta/sources.json` and the README, and
  the dump version travels in the snapshot's own provenance record.
* The same licence adds a currency condition -- "The content is continuously corrected ...
  distributing outdated Quranic text is the distributor's responsibility", pointing at
  `https://quranpedia.net/api/v1/changes?since=<version>`. A frozen snapshot cannot honour
  that by itself, so the version is recorded and `quran-json fetch --force` re-checks the
  upstream, exactly as QuranEnc's "keep up to date" condition is handled.
* What the licence does **not** cover: the fonts (`UthmanicQaloun_V21.ttf` and siblings) and
  the per-page SVG packs are separate assets of KFGQPC's. We publish neither, only text.

**These texts number 6,214 ayahs, not 6,236.** That is the riwayah, not a defect: Nafiʿ's
count differs from the Kufi count that Hafs carries, and 50 surahs differ in length
(al-Baqarah 285 where Hafs has 286, At-Tawbah 130 where Hafs has 129, and so on). Each
verse therefore carries the source's own `number_in_hafs` -- the Hafs ayah number or
numbers that this ayah covers, since Hafs sometimes splits one Nafiʿ ayah in two (81 such
positions). That field is what lets a consumer join a riwayah verse to the Hafs numbering
without this dataset merging or splitting any verse to fake a 6,236-slot array.
"""

from __future__ import annotations

import gzip
from typing import Any, Final

import orjson

__all__ = ["DUMPS_URL", "LICENSE_URL", "MOUNT", "VERSE_COUNT", "dump_url", "parse_dump"]

DUMPS_URL: Final = "https://api.quranpedia.net/dumps"
LICENSE_URL: Final = f"{DUMPS_URL}/LICENSE.md"

#: Qur'anpedia serves one dump per mushaf, numbered, with the catalogue at
#: `/dumps/mushafs-index.json.gz`. These ids are the Nafiʿ riwayat; the catalogue also holds
#: Hafs, Shu'bah, al-Duri, al-Susi, al-Bazzi and Qunbul, which this dataset does not carry.
MOUNT: Final[dict[str, int]] = {"warsh": 4, "qalun": 7}

#: Nafiʿ's count of the ayahs, for both riwayat. NOT the Kufi 6,236.
VERSE_COUNT: Final = 6214

CHAPTER_COUNT: Final = 114


def dump_url(script: str) -> str:
    """Download URL for one riwayah's dump."""
    return f"{DUMPS_URL}/mushafs-{MOUNT[script]}.json.gz"


def parse_dump(raw: bytes) -> dict[str, list[dict[str, Any]]]:
    """Parse a gzipped dump into `{chapter: [{chapter, verse, text, number_in_hafs}]}`.

    Raises:
        ValueError: the dump no longer has the shape this parser assumes, or its verse
            count moved. Both are worth failing a build over: a riwayah text published
            under the wrong count is worse than no text.
    """
    payload = orjson.loads(gzip.decompress(raw))
    surahs = payload["data"]["surahs"]

    if len(surahs) != CHAPTER_COUNT:
        raise ValueError(f"quranpedia: expected {CHAPTER_COUNT} surahs, got {len(surahs)}")

    chapters: dict[str, list[dict[str, Any]]] = {}

    for surah in surahs:
        chapter = int(surah["id"])
        verses: list[dict[str, Any]] = []

        for ayah in surah["ayahs"]:
            text = ayah["text"].strip()
            if not text:
                raise ValueError(f"quranpedia: empty verse at {chapter}:{ayah['number']}")

            verses.append(
                {
                    "chapter": chapter,
                    "verse": int(ayah["number"]),
                    "text": text,
                    "number_in_hafs": list(ayah.get("number_in_hafs") or []),
                }
            )

        if [verse["verse"] for verse in verses] != list(range(1, len(verses) + 1)):
            raise ValueError(f"quranpedia: chapter {chapter} is not numbered 1..n")

        chapters[str(chapter)] = verses

    total = sum(len(verses) for verses in chapters.values())
    if total != VERSE_COUNT:
        raise ValueError(f"quranpedia: expected {VERSE_COUNT} verses, got {total}")

    return chapters
