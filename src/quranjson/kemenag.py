"""Qur'an Kemenag (LPMQ) as a source: the Indonesian standard mushaf, its 2019
Indonesian translation, and its Latin transliteration.

`quran.kemenag.go.id` is a client-side app over a private JSON API that returns three
fields per ayah -- `arabic`, `translation`, `latin` -- one surah window at a time
(`?surah=N&start=&limit=`), so the whole corpus is 114 requests. That API is the app's
backend rather than a documented public service: it publishes no terms, and it answers
**403 unless the request carries the site's own `Origin` header**, which is why that
header is spelled out here instead of hidden in a config knob. Availability is not a
licence; the verdicts live in `config` and are reported by `quranjson.review`.

Licensing, all three items verified first-hand on 2026-09-18 (see `config`):

* **Text** -- granted. Minister of Religious Affairs Regulation 44/2016 Pasal 8(1): "Teks
  Mushaf Al-Qur'an tidak memiliki hak cipta", and Copyright Law 28/2014 Pasal 42(e)
  removes copyright from a kitab suci. Pasal 8(2) keeps the publisher's rights in the
  khat, the tanda baca/tajwid/qira'at apparatus and the ornaments, so only the plain text
  is taken: no fonts, no mushaf layout.
* **Translation** -- restricted. A protected work (Pasal 59(g), 50 years from first
  publication) with no redistribution grant published anywhere.
* **Transliteration** -- unknown. An authored romanisation, so nothing in Pasal 8(1)
  covers it, and no grant exists either.

The text is a seventh orthography, not a Tanzil variant. Measured against the snapshots in
`data/tanzil/` on 2026-09-18: it carries **no alef wasla (U+0671)** at all, where Tanzil's
Uthmani text marks it 13,819 times, and only **6 of the 37,416 verse comparisons** across
the six variants coincide -- 56:3 against Uthmani, and 47:6, 55:4 and 56:3 against the
Imlaei (`simple`/`simple-plain`) texts. Those are verses where the two orthographies happen
to agree completely, not evidence of a shared text. It follows the Mushaf Standar Indonesia
(Imlaei rasm carrying Uthmani-style marks and waqf signs) rather than Tanzil's Uthmani or
Imlaei.

Two upstream traits are preserved rather than corrected, because they are the text as
published: the API leaves a trailing space on many fields (stripped, being invisible and
outside the verse) and puts a double space after a waqf sign (kept -- it is inside the
verse, and "correcting" it would make the published bytes not the source's).
"""

from __future__ import annotations

from typing import Any, Final

import orjson

from .http import Fetcher

__all__ = ["AYAH_API", "ORIGIN", "SNAPSHOT_URL", "Fetcher", "ayah_url", "gather", "parse_surah"]

AYAH_API: Final = "https://web-api.qurankemenag.net/quran-ayah"

#: The API refuses anything that does not look like a request from the app itself.
ORIGIN: Final = "https://quran.kemenag.go.id"

#: `limit` is a window *within* a surah, so this one value covers the longest surah.
PAGE_LIMIT: Final = 286

CHAPTER_COUNT: Final = 114
VERSE_COUNT: Final = 6236

#: Documents the request pattern a gathered snapshot was crawled with, for provenance.
SNAPSHOT_URL: Final = f"{AYAH_API}?start=0&limit={PAGE_LIMIT}&surah={{1-{CHAPTER_COUNT}}}"

HEADERS: Final = {"Origin": ORIGIN}


def ayah_url(surah: int, *, start: int = 0, limit: int = PAGE_LIMIT) -> str:
    """The verse window URL for one surah."""
    return f"{AYAH_API}?start={start}&limit={limit}&surah={surah}"


def _verse(ayah: dict[str, Any]) -> dict[str, Any]:
    """Keep the three publishable payloads of one ayah, dropping the app's own metadata."""
    verse = {
        "chapter": int(ayah["surah_id"]),
        "verse": int(ayah["ayah"]),
        "text": str(ayah["arabic"]).strip(),
        "transliteration": str(ayah["latin"]).strip(),
        "translation": str(ayah["translation"]).strip(),
    }

    # The translator's footnotes are part of the translation, as they are for QuranEnc.
    notes = str(ayah.get("footnotes") or "").strip()
    if notes:
        verse["footnotes"] = notes

    return verse


def parse_surah(raw: bytes) -> list[dict[str, Any]]:
    """One surah's payload as verse records, in the order the API returned them."""
    payload = orjson.loads(raw)
    ayahs = payload.get("data")

    if not isinstance(ayahs, list) or not ayahs:
        raise ValueError("Qur'an Kemenag returned no verses for a surah")

    return [_verse(ayah) for ayah in ayahs]


def gather(fetcher: Fetcher) -> dict[str, list[dict[str, Any]]]:
    """Crawl all 114 surahs into `{chapter: [verses]}`.

    The three payloads come from the same ayah record, so they share one snapshot: one
    crawl, one file, and a re-encode in any of them surfaces as per-verse drift.
    """
    chapters: dict[str, list[dict[str, Any]]] = {}

    for surah in range(1, CHAPTER_COUNT + 1):
        chapters[str(surah)] = parse_surah(fetcher.get_bytes(ayah_url(surah), headers=HEADERS))

    total = sum(len(verses) for verses in chapters.values())
    if total != VERSE_COUNT:
        raise ValueError(f"Qur'an Kemenag: expected {VERSE_COUNT} verses, got {total}")

    return chapters
