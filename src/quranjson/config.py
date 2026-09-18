"""Paths, edition registry, licensing, and provenance for everything this project publishes.

The registry is the single source of truth for *where* each edition comes from and
*under which licence* it may be redistributed. Nothing is published without an entry
here -- this is what stops an unlicensed translation from being vendored by accident.

Licence status is recorded per edition as ``granted`` / ``restricted`` / ``unknown``.
Only ``granted`` editions may be published; ``restricted`` and ``unknown`` are blocked
by `quranjson.licensing`. See `data/meta/sources.json` and the README for the evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal

ROOT: Final = Path(__file__).resolve().parents[2]

#: Committed upstream snapshots -- the build inputs. Tracked in git so that builds
#: are offline and reproducible even if an upstream API disappears.
DATA: Final = ROOT / "data"

#: Frozen v3 artifacts, published to npm and served by jsDelivr. Byte-identical
#: reference tree; regenerating it must produce a clean `git diff`.
DIST: Final = ROOT / "dist"

#: New artifact tree, deployed to Cloudflare Pages.
CDN: Final = ROOT / "cdn"

#: The verse text used by the frozen tree.
TEXT_EDITION: Final = "ara-quranuthmanienc"

#: `transliteration` is generated like a language but has no chapter directory.
TRANSLITERATION: Final = "transliteration"

#: The Indonesian standard mushaf served by the Qur'an Kemenag app. Not a Tanzil variant:
#: it is the Mushaf Standar Indonesia, whose own definition (PMA 44/2016 Pasal 1(2), and
#: Pasal 17's variant list of Usmani/Bahriyyah/Braille) makes it a *standard*, and whose
#: serving API describes its text as "Rasm Usmani". Measured, it marks no alef wasla
#: (U+0671) where Tanzil's Uthmani text marks 13,819 of them, and only 6 of the 37,416
#: verse comparisons against the six Tanzil variants coincide. "Imlaei" is a producer
#: orthography name, not an MSI variant, so it is not used for this script.
KEMENAG_SCRIPT: Final = "kemenag"

#: DigitalKhatt's Indo-Pak text. The only Indo-Pak rasm under a redistribution grant:
#: every other one is either all-rights-reserved or an unlicensed mirror, and the
#: QuranWBW/Quran.com text is expressly "DO NOT SELL, MANIPULATE, DISTRIBUTE WITHOUT
#: CREDITS". See `quranjson.digitalkhatt` for the three reconstruction decisions and the
#: three properties a consumer should know (Fatiha segmentation, no embedded basmala,
#: Arabic Extended-B marks).
DIGITALKHATT_SCRIPT: Final = "indopak"

#: Qur'anpedia.net's two Nafiʿ riwayat -- Warsh (the Maghrib: Morocco, Algeria, West
#: Africa) and Qalun (Libya, Tunisia). Riwayat, not orthographies: their ayah numbering is
#: Nafiʿ's, 6,214, so they are not interchangeable with the Hafs scripts and are not
#: forced into a 6,236-slot array. See `quranjson.quranpedia`.
WARSH_SCRIPT: Final = "warsh"
QALUN_SCRIPT: Final = "qalun"
RIWAYAH_SCRIPTS: Final = (WARSH_SCRIPT, QALUN_SCRIPT)

#: Order matters: it determines key order in `verses/*.json`.
LANG_CODES: Final = (
    None,
    "bn",
    "en",
    "es",
    "fr",
    "id",
    "ru",
    "sv",
    "tr",
    "ur",
    "zh",
)

#: Languages that get a verse-level translation in `verses/*.json`.
#: NOTE: upstream `scripts/build.js` passed `qurans.slice(2)`, which silently skipped
#: `bn` -- Bengali is absent from every one of the 6,236 verse files it produced.
#: `LEGACY_VERSE_LANGS` reproduces that bug so the frozen `dist/` tree can be proven
#: byte-identical; published trees use `VERSE_LANGS` and include Bengali.
VERSE_LANGS: Final = tuple(lang for lang in LANG_CODES if lang is not None)
LEGACY_VERSE_LANGS: Final = tuple(LANG_CODES[2:])

DEFAULT_LINK_BASE: Final = "https://cdn.jsdelivr.net/npm/quran-json@{version}/dist/chapters/"

#: Version baked into the frozen `dist/` tree's chapter links. It is the npm package
#: version that was current when those files were generated; it is NOT a free variable.
#: Changing it would rewrite every `link` field and break the byte-parity gate.
LEGACY_VERSION: Final = "3.1.2"

#: Version of the new, corrected dataset generation served from the CDN. It differs from
#: the frozen tree because it fixes the dropped Bengali translation in every verse file.
DATASET_VERSION: Final = "4.0.0"

Status = Literal["granted", "restricted", "unknown"]


@dataclass(frozen=True, slots=True)
class License:
    """A redistribution verdict with the evidence behind it."""

    status: Status
    text: str
    url: str

    @property
    def allows_publication(self) -> bool:
        return self.status == "granted"


#: Tanzil hosts translations but grants nothing for them. Its CC-BY-3.0 notice covers
#: the Arabic *text* only; the Terms of Use on the translations page restrict them to
#: non-commercial use and forbid redistribution of the list.
#: https://tanzil.net/trans/  (verified 2026-09-14)
TANZIL_TRANSLATION = License(
    status="restricted",
    text=(
        "Tanzil translations: 'for non-commercial purposes only. If used otherwise, you "
        "need to obtain necessary permission from the translator or the publisher.' and "
        "'Redistributing the following list in another website is not allowed, unless "
        "direct permission is granted by the Tanzil Project.' The CC-BY-3.0 Tanzil Quran "
        "text licence covers Tanzil's Arabic text, NOT its translations."
    ),
    url="https://tanzil.net/trans/",
)

#: The one source whose terms grant re-publication on their face.
#: https://quranenc.com/en/home/api  ("Terms and Policies")
QURANENC = License(
    status="granted",
    text=(
        "QuranEnc.com permits download and re-publication of translation contents on 7 "
        "conditions: no modification/addition/deletion; credit the publisher and "
        "QuranEnc.com; state the version number; keep the transcript information; report "
        "notes back; keep up to date with the latest version; no inappropriate advertising."
    ),
    url="https://quranenc.com/en/home/api",
)

#: Talal Itani's ClearQuran -- an explicit open grant, including commercial use.
ITANI = License(
    status="granted",
    text=(
        "CC BY-ND 4.0. Free to use, share and distribute including in commercial projects, "
        "no permission required. Keep the files unmodified and credit the work as "
        "'Translation by Talal Itani, ClearQuran.com'."
    ),
    url="https://blog.clearquran.com/download",
)

#: Saheeh International. No grant exists and the publisher's domain is gone.
SAHEEH_INTERNATIONAL = License(
    status="restricted",
    text=(
        "Saheeh International (Umm Muhammad, Dar Abul-Qasim): all rights reserved, no "
        "redistribution grant found. Both Tanzil (non-commercial, permission required) and "
        "Quran.com (personal, non-commercial, no compilation) restrict the copies in "
        "circulation. Written permission from the publisher is required."
    ),
    url="https://tanzil.net/trans/",
)

#: The Arabic text currently shipped. VERIFIED 2026-09-14: the `ara-quranuthmanienc`
#: edition is itself a copy of `ara-quranacademy`, whose upstream repo states it is
#: "derived from Tanzil's Uthmani text" with systematic re-encoding (Farsi yeh U+06CC,
#: U+06E1 sukun, open tanween, tatweel). That upstream carries NO licence, and Tanzil's
#: licence forbids modification. So this is a modified derivative with no grant -- the
#: README's "text from The Noble Qur'an Encyclopedia" attribution is not accurate.
SHIPPED_TEXT = License(
    status="unknown",
    text=(
        "Modified derivative with no grant. The ara-quranuthmanienc edition is a copy of "
        "ara-quranacademy, which states it is derived from Tanzil's Uthmani text with "
        "systematic re-encoding; that upstream has no LICENSE file. Tanzil's text licence "
        "permits verbatim copies only: 'CHANGING IT IS NOT ALLOWED'."
    ),
    url="https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions/ara-quranuthmanienc.json",
)

#: Tanzil's own text -- the recommended replacement for the shipped derivative. Explicit
#: CC-BY 3.0 verbatim-redistribution grant. Note: its first ayah of every surah except
#: At-Tawbah carries the basmala, unlike the text shipped today.
TANZIL_TEXT = License(
    status="granted",
    text=(
        "Tanzil Quran Text / Copyright (C) 2007-2021 Tanzil Project / Creative Commons "
        "Attribution 3.0. Permission is granted to copy and distribute verbatim copies of "
        "this text, but CHANGING IT IS NOT ALLOWED."
    ),
    url="https://tanzil.net/docs/text_license",
)

TANZIL_DOWNLOAD = (
    "https://tanzil.net/pub/download/index.php?quranType={variant}&outType=txt-2&agree=true"
)

#: Tanzil text variants offered by the download endpoint.
TANZIL_VARIANTS: Final = (
    "uthmani",
    "uthmani-min",
    "simple",
    "simple-plain",
    "simple-min",
    "simple-clean",
)

#: Human-readable name and description for each text variant, published in the
#: manifest so consumers can choose without guessing what a Tanzil identifier means.
SCRIPT_LABELS: Final[dict[str, tuple[str, str]]] = {
    "uthmani": ("Uthmani", "Uthmanic orthography, full vocalisation"),
    "uthmani-min": ("Uthmani minimal", "Uthmanic orthography, reduced marks"),
    "simple": ("Imlaei", "Modern orthography, full vocalisation, assimilated letters"),
    "simple-plain": ("Imlaei plain", "Modern orthography, unassimilated letters"),
    "simple-min": ("Imlaei minimal", "Modern orthography, reduced marks"),
    "simple-clean": ("Imlaei unvocalised", "Modern orthography, no vowel marks at all"),
    KEMENAG_SCRIPT: (
        "Mushaf Standar Indonesia",
        "Kemenag (LPMQ) Mushaf Standar Indonesia, the rasm Usmani text the ministry's API "
        "serves, carrying the Indonesian standard's waqf signs",
    ),
    DIGITALKHATT_SCRIPT: (
        "Indo-Pak",
        "DigitalKhatt's Indo-Pak typesetting: subscript alef (U+0656), no alef wasla, "
        "Arabic Extended-B marks",
    ),
    WARSH_SCRIPT: (
        "Warsh",
        "Warsh ʿan Nafiʿ (the Maghrib: Morocco, Algeria, West Africa), 6,214 ayahs to "
        "Nafiʿ's count",
    ),
    QALUN_SCRIPT: (
        "Qalun",
        "Qalun ʿan Nafiʿ (Libya, Tunisia), 6,214 ayahs to Nafiʿ's count",
    ),
}


#: Qur'an Kemenag -- the LPMQ (Ministry of Religious Affairs) mushaf text, its 2019
#: Indonesian translation, and its Latin transliteration, all served by the app's own
#: JSON API. `data/kemenag/quran.json` snapshots all three from one crawl.
KEMENAG_SOURCE: Final = "https://quran.kemenag.go.id/"
KEMENAG_API: Final = "https://web-api.qurankemenag.net/quran-ayah"
PMA_MUSHAF_URL: Final = (
    "https://jdih.kemenag.go.id/regulation-download/"
    "penerbitan-pentashihan-dan-peredaran-mushaf-al-qur%27an"
)
UU_COPYRIGHT_URL: Final = "https://peraturan.bpk.go.id/Details/38690/uu-no-28-tahun-2014"

#: The text: the state's own instrument says the mushaf text carries no copyright.
#: Verified 2026-09-18 by extracting the text of both instruments, not from a summary.
KEMENAG_TEXT = License(
    status="granted",
    text=(
        "Minister of Religious Affairs Regulation 44/2016, Pasal 8(1): 'Teks Mushaf "
        "Al-Qur'an tidak memiliki hak cipta.' Copyright Law 28/2014, Pasal 42(e): 'Tidak "
        "ada Hak Cipta atas hasil karya berupa: ... e. kitab suci atau simbol keagamaan.' "
        "Pasal 8(2) reserves the publisher's rights in khat, tanda baca/tajwid/qira'at and "
        "ornamentation, so only the plain UTF-8 text is published: no fonts, no mushaf "
        "layout, no ornaments."
    ),
    url=PMA_MUSHAF_URL,
)

#: The 2019 Indonesian translation: a protected work with no grant found.
KEMENAG_TRANSLATION = License(
    status="restricted",
    text=(
        "No grant. A translation is a protected work: Copyright Law 28/2014 Pasal 59(g) "
        "covers 'terjemahan, tafsir, saduran, ...' for 50 years from first publication, and "
        "nothing exempts the ministry. The serving API publishes no terms and the ministry's "
        "own site (lajnah.kemenag.go.id) was unreachable on 2026-09-18, with no Wayback "
        "snapshot to fall back on. This 2019 revision is a re-edit of the ministry "
        "translation already published as `id-affairs` under the QuranEnc grant, but only "
        "116 of 6,236 verses are byte-identical, so that grant does not cover these bytes. "
        "Pasal 43(d) excuses non-commercial distribution but is a limitation on "
        "infringement rather than a grant, and this dataset carries no non-commercial "
        "limit downstream."
    ),
    url=UU_COPYRIGHT_URL,
)

#: The Latin transliteration: no grant, and no statutory basis either.
KEMENAG_TRANSLITERATION = License(
    status="unknown",
    text=(
        "No grant, and no statutory basis: the API's `latin` field is a romanisation with "
        "authored vocalisation, not the uncopyrightable 'teks Mushaf Al-Qur'an' of "
        "Regulation 44/2016 Pasal 8(1). Copyright Law 28/2014 Pasal 59(g) protects 'karya "
        "lain dari hasil transformasi'. Complete for all 6,236 verses. Pasal 43(d) excuses "
        "non-commercial distribution, but it is a limitation on infringement rather than a "
        "grant, and the dataset imposes no non-commercial limit downstream."
    ),
    url=f"{KEMENAG_API}?start=0&limit=3&surah=2",
)

#: DigitalKhatt's own typesetting, MIT-licensed at the repository root. A font licence
#: would not do: OFL on DigitalKhatt's `indopakfont` covers the glyphs, never the text.
DIGITALKHATT = License(
    status="granted",
    text=(
        "MIT (DigitalKhatt/digitalkhatt-js): 'Permission is hereby granted, free of charge, "
        "to any person obtaining a copy of this software and associated documentation "
        "files ... to deal in the Software without restriction, including without limitation "
        "the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or "
        "sell copies of the Software.' The repository's root LICENSE covers the text file "
        "this dataset parses; there is no separate data licence and no NOTICE file. The "
        "Indo-Pak rasm itself is DigitalKhatt's own typesetting, not a copy of another "
        "producer's Indopak data (0 of 6,236 verses shared with the QuranWBW or KFGQPC text)."
    ),
    url="https://raw.githubusercontent.com/DigitalKhatt/digitalkhatt-js/HEAD/LICENSE",
)

#: The first source found whose grant reaches the Maghribi riwayat at all. It is granted
#: with two conditions a dataset must meet (credit + dump version) and one duty (stay
#: current), which is why the version travels in the provenance record.
QURANPEDIA = License(
    status="granted",
    text=(
        "Qur'anpedia.net Data License (version 2026-09-18): 'Free to use inside apps, "
        "websites, bots, and research tools -- no attribution required ... Republishing "
        "this data -- in full or in part -- as a downloadable database or dataset "
        "requires: (1) crediting Qur'anpedia.net as the source with a link, and (2) stating "
        "this dump's version.' The same licence requires keeping a copy current via "
        "/api/v1/changes and holds the distributor responsible for outdated text; the "
        "snapshot records the dump version it was taken from. The underlying riwayah text "
        "is KFGQPC's printed mushaf per the dump's own description; the licence's own "
        "ownership clause treats the qira'at text as the ummah's shared heritage and claims "
        "only the digitisation, dabt and metadata. Fonts and per-page SVG packs are separate "
        "KFGQPC assets and are not published here."
    ),
    url="https://api.quranpedia.net/dumps/LICENSE.md",
)

#: Every script published under `/text/`, in manifest order, with its covering licence.
SCRIPT_IDS: Final = (
    *TANZIL_VARIANTS,
    KEMENAG_SCRIPT,
    DIGITALKHATT_SCRIPT,
    *RIWAYAH_SCRIPTS,
)
SCRIPT_LICENSES: Final[dict[str, License]] = {
    **dict.fromkeys(TANZIL_VARIANTS, TANZIL_TEXT),
    KEMENAG_SCRIPT: KEMENAG_TEXT,
    DIGITALKHATT_SCRIPT: DIGITALKHATT,
    **dict.fromkeys(RIWAYAH_SCRIPTS, QURANPEDIA),
}

#: Verses a script is expected to hold. The Hafs-count scripts all run to 6,236; Nafiʿ's
#: two riwayat do not, and flattening them to 6,236 would mean merging or splitting ayahs.
#: The per-script total is published in `manifest.json`, so the divergence is visible to a
#: consumer rather than implied.
SCRIPT_VERSES: Final[dict[str, int]] = {
    **dict.fromkeys(SCRIPT_IDS, 6236),
    WARSH_SCRIPT: 6214,
    QALUN_SCRIPT: 6214,
}

#: What a consumer must know before reading a script's bytes, published per script in
#: `manifest.json`. Only scripts whose shape or segmentation departs from the dataset's
#: Hafs-based chapter metadata carry one.
SCRIPT_NOTES: Final[dict[str, str]] = {
    DIGITALKHATT_SCRIPT: (
        "Al-Fatiha follows the Indo-Pak segmentation: the basmala is unnumbered, so verse 1 "
        "is 'al-hamdu lillahi rabbi al-'alamin' and the last two verses are held separately, "
        "where the Hafs scripts make the basmala verse 1 and hold the final two together. "
        "Every chapter has the canonical count; only chapter 1's verse labels differ. No "
        "basmala is embedded in any verse. The text uses Arabic Extended-B marks (U+089C, "
        "2,098 of them), which not every font covers: Noto Naskh Arabic and DigitalKhatt's "
        "own fonts cover every codepoint here, while Amiri renders U+089C as a missing "
        "glyph. Coverage is not shaping: a font that has the glyph still positions these "
        "marks by its own rules."
    ),
    WARSH_SCRIPT: (
        "Warsh ʿan Nafiʿ, a different riwayah, not an orthography: 6,214 ayahs to Nafiʿ's "
        "count, of which 50 surahs differ in length from the Hafs count in /chapters.json "
        "(al-Baqarah 285 where Hafs has 286, At-Tawbah 130 where Hafs has 129). Each verse's "
        "`number_in_hafs` gives the Hafs ayah number or numbers it covers."
    ),
    QALUN_SCRIPT: (
        "Qalun ʿan Nafiʿ, a different riwayah, not an orthography: 6,214 ayahs to Nafiʿ's "
        "count, of which 50 surahs differ in length from the Hafs count in /chapters.json. "
        "Each verse's `number_in_hafs` gives the Hafs ayah number or numbers it covers."
    ),
}


#: Chapter metadata snapshotted from the Quran.com API.
QURAN_COM_METADATA = License(
    status="restricted",
    text=(
        "Quran.com terms: content is 'FOR YOUR PERSONAL, NON-COMMERCIAL USE ONLY' and "
        "users 'shall not ... use the Service for data mining, scraping, crawling, "
        "redirecting, or compiling a collection of listings or data for any purpose'. The "
        "chapter metadata in data/chapters/ is snapshotted for the existing published "
        "build and is not cleared for re-publication."
    ),
    url="https://quran.com/terms-and-conditions",
)


def public_domain(work: str, basis: str, url: str) -> License:
    """A public-domain verdict, with the basis that makes it one."""
    return License(status="granted", text=f"Public domain. {work}. {basis}", url=url)


#: Public-domain English translations, all verified verse-numbered and complete
#: (6,236 verses / 114 chapters) from the sources recorded below. For a public-domain
#: work the distribution channel is irrelevant -- what matters is that the work is free.
SALE = public_domain(
    "George Sale, first published 1734",
    "Author died 1736, so out of copyright in life+70 jurisdictions and in the US.",
    "https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions/eng-georgesale.json",
)

PALMER = public_domain(
    "E. H. Palmer, Sacred Books of the East, 1880",
    "Author died 1882, so out of copyright in life+70 jurisdictions and in the US.",
    "https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions/eng-edwardhenrypalm.json",
)

PICKTHALL = public_domain(
    "Marmaduke Pickthall, The Meaning of the Glorious Koran, 1930",
    "Author died 1936, so out of copyright in life+70 jurisdictions since 2007 and in "
    "the US since 1 January 2026.",
    "https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions/eng-mohammedmarmadu.json",
)

YUSUF_ALI = public_domain(
    "Abdullah Yusuf Ali, The Holy Qur'an, 1934",
    "Author died 1953, so out of copyright in life+70 jurisdictions since 2024.",
    "https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions/eng-abdullahyusufal.json",
)


SABLUKOV = public_domain(
    "Gordy Semyonovich Sablukov, 1878 -- the first Russian translation of the Quran",
    "Author died 1880, so out of copyright in life+70 jurisdictions and in the US.",
    "https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions/rus-gordysemyonovic.json",
)

KRACHKOVSKY = public_domain(
    "Ignaty Yulianovich Krachkovsky, 1963 (posthumous)",
    "Author died 1951, so out of copyright in life+70 jurisdictions since 2022.",
    "https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions/rus-ignatyyulianovi.json",
)


#: Audio hosts. We publish URL templates and never mirror audio bytes, so these record
#: the host's own terms for the consumer rather than gating our output.
MP3QURAN_AUDIO = License(
    status="granted",
    text=(
        "mp3quran.net permits copying, publishing and redistribution of its recitations "
        "with attribution to the site; the reciter's rights are retained."
    ),
    url="https://mp3quran.net/eng/",
)

ISLAMIC_NETWORK_AUDIO = License(
    status="granted",
    text=(
        "islamic.network audio is free to redistribute for non-commercial use; each "
        "recitation's copyright remains with its reciter."
    ),
    url="https://islamic.network/",
)

EVERYAYAH_AUDIO = License(
    status="unknown",
    text=(
        "everyayah.com states no licence: its license, terms and readme paths all return "
        "404 and the homepage carries no matching terms. Treated as unknown -- we link to "
        "the files rather than redistribute them."
    ),
    url="https://everyayah.com/data/",
)


@dataclass(frozen=True, slots=True)
class Edition:
    """A translation the dataset ships, with its verified licence status."""

    lang: str
    slug: str
    author: str
    source: str
    license: License
    #: How the snapshot is parsed: "quran-api" (JSON, grouped by chapter),
    #: "clearquran" (zip of per-verse text files), "quranenc" (zip of SQLite), or
    #: "kemenag" (the Qur'an Kemenag snapshot, one field per edition).
    kind: str = "quran-api"
    #: ISO 639 language code used in published URLs, e.g. the `en` in
    #: `/translations/en-pickthall/`. QuranEnc supplies this authoritatively in its
    #: catalogue; the extra editions declare it here.
    code: str = ""

    @property
    def redistributable(self) -> bool:
        return self.license.allows_publication


#: The editions the frozen `dist/` tree was built from. Slugs are frozen too: changing one
#: changes the published bytes, so the parity gate pins this list.
EDITIONS: Final[tuple[Edition, ...]] = (
    Edition(
        lang=TRANSLITERATION,
        slug="ara-quran-la",
        author="Tanzil.net",
        source="https://tanzil.net/trans/en.transliteration",
        license=TANZIL_TRANSLATION,
    ),
    Edition(
        lang="bn",
        slug="ben-muhiuddinkhan",
        author="Muhiuddin Khan",
        source="https://tanzil.net/trans/bn.bengali",
        license=TANZIL_TRANSLATION,
    ),
    Edition(
        lang="en",
        slug="eng-ummmuhammad",
        author="Umm Muhammad (Saheeh International)",
        source="https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions/eng-ummmuhammad.json",
        license=SAHEEH_INTERNATIONAL,
    ),
    Edition(
        lang="es",
        slug="spa-muhammadisagarc",
        author="Muhammad Isa Garcia",
        source="https://tanzil.net/trans/es.garcia",
        license=TANZIL_TRANSLATION,
    ),
    Edition(
        lang="fr",
        slug="fra-muhammadhamidul",
        author="Muhammad Hamidullah",
        source="https://tanzil.net/trans/fr.hamidullah",
        license=TANZIL_TRANSLATION,
    ),
    Edition(
        lang="id",
        slug="ind-indonesianislam",
        author="Indonesian Islamic Affairs Ministry",
        source="https://quranenc.com/en/browse/indonesian_affairs/",
        license=QURANENC,
    ),
    Edition(
        lang="ru",
        slug="rus-elmirkuliev",
        author="Elmir Kuliev",
        source="https://tanzil.net/trans/ru.kuliev",
        license=TANZIL_TRANSLATION,
    ),
    Edition(
        lang="sv",
        slug="swe-knutbernstrom",
        author="Knut Bernstrom",
        source="https://tanzil.net/trans/sv.bernstrom",
        license=TANZIL_TRANSLATION,
    ),
    Edition(
        lang="tr",
        slug="tur-diyanetisleri",
        author="Turkish Directorate of Religious Affairs",
        source="https://tanzil.net/trans/tr.diyanet",
        license=TANZIL_TRANSLATION,
    ),
    Edition(
        lang="ur",
        slug="urd-abulaalamaududi",
        author="Abul A'la Maududi",
        source="https://tanzil.net/trans/ur.maududi",
        license=TANZIL_TRANSLATION,
    ),
    Edition(
        lang="zh",
        slug="zho-muhammadmakin",
        author="Muhammad Makin",
        source="https://quranenc.com/en/browse/chinese_makin/",
        license=QURANENC,
    ),
)


def chapter_list_path(lang: str | None) -> Path:
    """Path to the committed chapter-list snapshot for ``lang``."""
    return DATA / "chapters" / f"{'en' if lang in (None, TRANSLITERATION) else lang}.json"


def edition_path(lang: str) -> Path:
    """Path to the committed translation snapshot for ``lang``."""
    return DATA / "editions" / f"{lang}.json"


def text_path() -> Path:
    """Path to the committed Uthmani text snapshot."""
    return DATA / "quran.json"


def tanzil_text_path(variant: str) -> Path:
    """Path to a committed Tanzil text snapshot (licence: CC-BY 3.0, verbatim)."""
    return DATA / "tanzil" / f"{variant}.json"


def tanzil_chapters_path() -> Path:
    """Path to the committed Tanzil chapter metadata snapshot."""
    return DATA / "tanzil" / "chapters.json"


def quranenc_catalogue_path() -> Path:
    """Path to the committed QuranEnc translation catalogue."""
    return DATA / "quranenc" / "catalogue.json"


def quranenc_path(key: str) -> Path:
    """Path to a committed QuranEnc translation snapshot."""
    return DATA / "quranenc" / f"{key}.json"


def kemenag_path() -> Path:
    """Path to the committed Qur'an Kemenag snapshot.

    One file for one upstream: the Arabic text, the 2019 Indonesian translation and the
    Latin transliteration are three fields of the same ayah record, so they come from one
    crawl and drift in any of them is detected verse by verse.
    """
    return DATA / "kemenag" / "quran.json"


def digitalkhatt_path() -> Path:
    """Path to the committed DigitalKhatt Indo-Pak snapshot (licence: MIT)."""
    return DATA / "digitalkhatt" / "quran.json"


def quranpedia_path(script: str) -> Path:
    """Path to a committed Qur'anpedia snapshot, one per Nafiʿ riwayah."""
    return DATA / "quranpedia" / f"{script}.json"


#: Record of upstream transcription defects restored on load (see `quranjson.qa`).
QA_PATH: Final = DATA / "meta" / "qa.json"


CLEARQURAN_DOWNLOADS: Final = "https://www.clearquran.com/downloads/{file}"

#: Base for a single Quran.com-API-shaped edition JSON, as mirrored by quran-api.
QURAN_API_EDITION: Final = "https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions"


def clearquran_url(filename: str) -> str:
    """Download URL for one of Talal Itani's verse-by-verse archives."""
    return CLEARQURAN_DOWNLOADS.format(file=filename)


def extra_edition_path(key: str) -> Path:
    """Path to a committed snapshot for an edition sourced outside QuranEnc."""
    return DATA / "extra" / f"{key}.json"


#: Editions sourced outside QuranEnc, each carrying its own grant from the rights holder.
#: Fetching from the translator's own site is preferred over an aggregator, because the
#: grant then travels with the distribution.
EXTRA_EDITIONS: Final[tuple[Edition, ...]] = (
    Edition(
        lang="english_itani",
        code="en",
        slug="clearquran-verse-by-verse",
        author="Talal Itani",
        source="https://www.clearquran.com/downloads/quran-verse-by-verse-text.zip",
        license=ITANI,
        kind="clearquran",
    ),
    Edition(
        lang="english_itani_allah",
        code="en",
        slug="clearquran-verse-by-verse-allah",
        author="Talal Itani",
        source=clearquran_url("quran-in-english-clearquran-verse-by-verse-txt-edition-allah.zip"),
        license=ITANI,
        kind="clearquran",
    ),
    Edition(
        lang="english_pickthall",
        code="en",
        slug="eng-mohammedmarmadu",
        author="Marmaduke Pickthall (1930)",
        source=f"{QURAN_API_EDITION}/eng-mohammedmarmadu.json",
        license=PICKTHALL,
    ),
    Edition(
        lang="english_yusuf_ali",
        code="en",
        slug="eng-abdullahyusufal",
        author="Abdullah Yusuf Ali (1934)",
        source=f"{QURAN_API_EDITION}/eng-abdullahyusufal.json",
        license=YUSUF_ALI,
    ),
    Edition(
        lang="english_palmer",
        code="en",
        slug="eng-edwardhenrypalm",
        author="E. H. Palmer (1880)",
        source=f"{QURAN_API_EDITION}/eng-edwardhenrypalm.json",
        license=PALMER,
    ),
    Edition(
        lang="english_sale",
        code="en",
        slug="eng-georgesale",
        author="George Sale (1734)",
        source=f"{QURAN_API_EDITION}/eng-georgesale.json",
        license=SALE,
    ),
    Edition(
        lang="russian_sablukov",
        code="ru",
        slug="rus-gordysemyonovic",
        author="Gordy Semyonovich Sablukov (1878)",
        source=f"{QURAN_API_EDITION}/rus-gordysemyonovic.json",
        license=SABLUKOV,
    ),
    Edition(
        lang="russian_krachkovsky",
        code="ru",
        slug="rus-ignatyyulianovi",
        author="Ignaty Yulianovich Krachkovsky (1963)",
        source=f"{QURAN_API_EDITION}/rus-ignatyyulianovi.json",
        license=KRACHKOVSKY,
    ),
)


#: Editions that are ingested but not publishable: their licence is not `granted`, so the
#: gate keeps them out of `cdn/` and reports them, with the reason, in the withheld lists.
#: They are published only under `--include-unverified-licenses`, once the rights have
#: been cleared out of band. Fetching them anyway is deliberate: the snapshot is what
#: makes the withheld bytes auditable, exactly as the frozen tree's 9 editions are.
PENDING_EDITIONS: Final[tuple[Edition, ...]] = (
    Edition(
        lang="indonesian_kemenag",
        code="id",
        slug="ind-kemenag-2019",
        author="Kementerian Agama RI (Lajnah Pentashihan Mushaf Al-Qur'an)",
        source=KEMENAG_API,
        license=KEMENAG_TRANSLATION,
        kind="kemenag",
    ),
    Edition(
        lang="transliteration_kemenag",
        slug="ara-kemenag-latin",
        author="Kementerian Agama RI (Lajnah Pentashihan Mushaf Al-Qur'an)",
        source=KEMENAG_API,
        license=KEMENAG_TRANSLITERATION,
        kind="kemenag",
    ),
)

#: Every registered edition, publishable or not -- what the licence report accounts for.
REGISTERED: Final = (*EDITIONS, *PENDING_EDITIONS)
