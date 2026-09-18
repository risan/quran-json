"""The licensing review record.

Every source investigated for redistribution rights, with the verdict and the evidence
behind it, so the research does not have to be repeated and a decision to publish
something new starts from facts rather than a fresh web search.

`quran-json licenses --write` regenerates `data/meta/licensing-review.json`; the test
suite asserts every entry carries an evidence URL. Adding a source to the dataset means
changing a verdict here, deliberately.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from . import config

__all__ = ["REVIEWED", "SourceReview", "review_manifest"]

#: When the review below was last carried out.
REVIEWED = "2026-09-18"


@dataclass(frozen=True, slots=True)
class SourceReview:
    """One investigated source."""

    name: str
    kind: str
    status: config.Status
    license_url: str
    evidence: str
    #: What would have to happen to move this to `granted`.
    blocker: str = ""


CANDIDATES: tuple[SourceReview, ...] = (
    SourceReview(
        name="Tanzil.net Quran text (uthmani, simple) and chapter metadata",
        kind="text",
        status="granted",
        license_url="https://tanzil.net/docs/text_license",
        evidence=(
            "CC-BY 3.0: 'Permission is granted to copy and distribute verbatim copies of "
            "this text, but CHANGING IT IS NOT ALLOWED.'"
        ),
    ),
    SourceReview(
        name="QuranEnc.com translations",
        kind="translation",
        status="granted",
        license_url="https://quranenc.com/en/home/api",
        evidence=(
            "'Contents of the translations can be downloaded and re-published' under 7 "
            "conditions: verbatim, credit publisher + QuranEnc.com, state the version, "
            "keep transcripts, report notes, keep current, no inappropriate advertising."
        ),
    ),
    SourceReview(
        name="QuranEnc.com bulk download (zipped SQLite per translation)",
        kind="translation",
        status="granted",
        license_url="https://quranenc.com/en/home/api",
        evidence="database_url field per catalogue entry; 75 translations, 56 languages.",
    ),
    SourceReview(
        name="Tanzil.net en.transliteration",
        kind="transliteration",
        status="restricted",
        license_url="https://tanzil.net/trans/",
        evidence=(
            "'The translations provided at this page are for non-commercial purposes only. "
            "If used otherwise, you need to obtain necessary permission from the "
            "translator or the publisher.' and 'Redistributing the following list in "
            "another website is not allowed, unless direct permission is granted by the "
            "Tanzil Project.' Tanzil's CC-BY-3.0 notice covers its Arabic text only."
        ),
        blocker=(
            "Written permission from the Tanzil Project (admin@tanzil.net). Their terms "
            "explicitly contemplate granting it and the file is machine-readable, so this "
            "is the cheapest route to a high-quality transliteration."
        ),
    ),
    SourceReview(
        name="Talal Itani, ClearQuran (english_itani, english_itani_allah)",
        kind="translation",
        status="granted",
        license_url="https://blog.clearquran.com/download",
        evidence=(
            "'free to use, share, and distribute - including in commercial projects - with "
            "no permission or authorization required. When sharing, please keep the files "
            "unmodified and credit the source as shown below. They are released under the "
            "Creative Commons Attribution-NoDerivatives 4.0 International License.' "
            "Fetched from the translator's own verse-by-verse archive (6,236 files), not a "
            "packager."
        ),
    ),
    SourceReview(
        name="Public-domain English translations: Sale 1734, Palmer 1880, Pickthall 1930, "
        "Yusuf Ali 1934",
        kind="translation",
        status="granted",
        license_url="https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions.json",
        evidence=(
            "Public domain by the death of the author: Sale d.1736, Palmer d.1882, "
            "Pickthall d.1936, Yusuf Ali d.1953 -- all out of copyright in life+70 "
            "jurisdictions, and pre-1929 US publication for Sale/Palmer/Rodwell. "
            "VERIFIED 2026-09-14: each edition returns 200 with 6,236 verses across 114 "
            "chapters and the expected opening wording. For a PD work the distribution "
            "channel is irrelevant, so the packager's lack of a per-edition licence "
            "field does not apply."
        ),
        blocker="",
    ),
    SourceReview(
        name="Rodwell 1861 (public domain, but unavailable)",
        kind="translation",
        status="unknown",
        license_url="https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions.json",
        evidence=(
            "The work is public domain (J. M. Rodwell d.1900), and the catalogue lists "
            "eng-johnmedowsrodwe, but that file returns HTTP 403. Project Gutenberg's "
            "Rodwell (#2800/#3434) is continuous prose with NO per-ayah numbering."
        ),
        blocker="Needs a verse-numbered digitisation; the prose Gutenberg text would "
        "require ayah alignment.",
    ),
    SourceReview(
        name="Shakir (do not ship)",
        kind="translation",
        status="unknown",
        license_url="https://www.gutenberg.org/cache/epub/16955/pg16955.txt",
        evidence=(
            "Project Gutenberg #16955 bundles Yusuf Ali, Pickthall and Shakir side by side "
            "with clean NNN.NNN verse numbering, but its own header says the text "
            "'originates from a file whose origins we don't know'. Shakir's death year is "
            "contradictory across sources (1959 vs a 1866-1939 record), so his copyright "
            "status cannot be established."
        ),
        blocker="Establish Shakir's copyright status, or use the Yusuf Ali/Pickthall "
        "selections from the same file with a proper provenance chain.",
    ),
    SourceReview(
        name="Islamic Bulletin 'Quran Transliteration' PDF (also on archive.org)",
        kind="transliteration",
        status="restricted",
        license_url="https://islamicbulletin.org/en/ebooks/quran/quran_transliteration.pdf",
        evidence=(
            "The document carries a reuse line -- 'This work is free for use to everyone as "
            "long as no changes that might distort it are done to it' -- but it credits 'The "
            "Calgary Islamic Homepage', whose own archived footer reads 'Copyright 1997 - "
            "2004 The Calgary Islamic Homepage, All Rights Reserved.' A downstream "
            "compiler's grant cannot override the credited author's reservation, so the "
            "only apparent grant on this text is contradicted."
        ),
        blocker=(
            "Written permission from the Calgary Islamic Homepage (or whoever holds the "
            "rights to the transliteration text they published)."
        ),
    ),
    SourceReview(
        name="Roman transliteration bundled with Pickthall (M. A. Haleem Eliasii)",
        kind="transliteration",
        status="restricted",
        license_url="https://archive.org/details/TheNobleQuran",
        evidence=(
            "First published 1983, so still in copyright; not a public-domain work despite "
            "accompanying Pickthall's 1930 translation."
        ),
        blocker="Permission from the author or publisher.",
    ),
    SourceReview(
        name="Pre-1929 public-domain Arabic transliteration",
        kind="transliteration",
        status="unknown",
        license_url="https://archive.org/",
        evidence=(
            "Searched for and found NONE. The only pre-1929 'Roman' Qur'an located is the "
            "1844 Allahabad / 1876 Ludhiana Roman-URDU Qur'an, which is an Urdu translation "
            "in Latin letters, not a transliteration of the Arabic."
        ),
        blocker="No such work exists; this route is closed.",
    ),
    SourceReview(
        name="MostafaOsmanFathi/QuranPhoneticSearch (claimed MIT transliteration data)",
        kind="transliteration",
        status="restricted",
        license_url="https://github.com/MostafaOsmanFathi/QuranPhoneticSearch",
        evidence=(
            "MIT covers the code, but the data derives from the Islamic Bulletin/Calgary "
            "text (see above), ships no verse identifiers, and is INCOMPLETE: the CSV ends "
            "inside al-A'raf 7:135, i.e. surahs 1-7 of 114."
        ),
        blocker="Upstream text rights plus an incomplete, unaligned dataset.",
    ),
    SourceReview(
        name="Self-generated transliteration from a CC BY-SA Arabic text (Wikisource)",
        kind="transliteration",
        status="unknown",
        license_url="https://ar.wikisource.org/wiki/%D8%A7%D9%84%D9%82%D8%B1%D8%A2%D9%86_%D8%A7%D9%84%D9%83%D8%B1%D9%8A%D9%85_(%D8%AD%D9%81%D8%B5%D8%8C_%D8%A7%D9%84%D9%85%D8%AF%D9%8A%D9%86%D8%A9_%D8%A7%D9%84%D9%86%D8%A8%D9%88%D9%8A%D8%A9)",
        evidence=(
            "This is the most promising route: generate the transliteration ourselves from "
            "an Arabic text that permits adaptation, sidestepping Tanzil's verbatim-only "
            "term. VERIFIED 2026-09-14: ar.wikisource.org hosts the Hafs/Madinah and imlaei "
            "script texts organised by surah, and Wikisource content is CC BY-SA -- the "
            "same licence this repository ships under, so no permission email is needed. "
            "Caveat: the surah pages only transclude a Lua table ({{#invoke:Quran|...}}), so "
            "the text must be extracted from Module:Quran. Also VERIFIED 2026-09-14: the two "
            "MIT phonemizer projects previously credited for this work do NOT exist "
            "(obadx/quran-transcript and Hetchy/Quranic-Phonemizer both 404), so the "
            "grapheme-to-phoneme step would have to be written, and the result reviewed."
        ),
        blocker=(
            "Build and validate the transliteration engine. Tanzil's en.transliteration "
            "remains the one-email fallback and would be the reference for spot-checking "
            "our output."
        ),
    ),
    SourceReview(
        name="QUL / Tarteel Quranic Universal Library transliterations (8 resources)",
        kind="transliteration",
        status="unknown",
        license_url="https://qul.tarteel.ai/resources/transliteration",
        evidence=(
            "VERIFIED 2026-09-14 by sweeping EVERY resource id 1-1760 at "
            "/resources/{id}/copyright: of about 591 published resources, only 2 carry any "
            "licence statement and both are restrictive (permission required / exclusive "
            "licence held by a third party). The other ~589, including all 8 "
            "transliterations (477, 468, 475, 476, 469, 71, 72, 478), render 'We don't have "
            "copyright information for this resource.' QUL renders only the free-text "
            "copyright_notice; the permission_to_host / permission_to_share enums are "
            "login-only. Bulk download requires authentication."
        ),
        blocker=(
            "QUL publishes no grant for any transliteration, and nothing in its catalogue "
            "is cleared by its own records."
        ),
    ),
    SourceReview(
        name="fawazahmed0/quran-api transliteration editions (-la / -lad slugs)",
        kind="transliteration",
        status="unknown",
        license_url="https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions.json",
        evidence=(
            "Repo is Unlicense, but the catalogue carries NO per-edition licence field, "
            "and most `-la` entries are romanised translations rather than "
            "transliterations. Only a handful of ara-* entries are true transliterations, "
            "and those declare tanzil.net as their source."
        ),
        blocker="Per-edition grants do not exist; the upstream rights holders must be asked.",
    ),
    SourceReview(
        name="Quran.com API v4 (transliteration id 57, chapter metadata, tafsirs)",
        kind="transliteration",
        status="restricted",
        license_url="https://quran.com/terms-and-conditions",
        evidence=(
            "'FOR YOUR PERSONAL, NON-COMMERCIAL USE ONLY' and no 'compiling a collection "
            "of listings or data for any purpose'."
        ),
        blocker="Contradicts the open-redistribution goal entirely.",
    ),
    SourceReview(
        name="Self-generated transliteration from the Arabic text",
        kind="transliteration",
        status="unknown",
        license_url="https://tanzil.net/docs/text_license",
        evidence=(
            "Technically solved: obadx/quran-transcript and Hetchy/Quranic-Phonemizer are "
            "MIT-licensed phonemizers covering our exact Uthmani codepoints; the remaining "
            "work is a phoneme-to-Latin table. Legally ambiguous: Tanzil's notice forbids "
            "non-verbatim renderings, while the same notice grants CC-BY 3.0 (which permits "
            "adaptations), and Tanzil files its own transliteration under its Translations "
            "repository rather than under the text licence. US Copyright Office Compendium "
            "709.1 says a mechanical transliteration cannot be registered."
        ),
        blocker=(
            "Either a written adaptation grant from Tanzil, or generate from a non-Tanzil "
            "Arabic text. Would also need a 6,236-verse review pass."
        ),
    ),
    SourceReview(
        name="EveryAyah per-ayah audio",
        kind="audio",
        status="unknown",
        license_url="https://everyayah.com/data/",
        evidence=(
            "No licence published anywhere: license, terms and readme paths all 404. "
            "Verified serving: HTTP/2 200/206, accept-ranges, access-control-allow-origin "
            "'*', filename {SSS}{AAA}.mp3 with surah-relative ayah numbers."
        ),
        blocker="We link to these files rather than redistribute them, so this gates nothing.",
    ),
    SourceReview(
        name="MP3Quran API v3 (whole-surah audio)",
        kind="audio",
        status="granted",
        license_url="https://mp3quran.net/eng/",
        evidence=(
            "Permits copying and redistribution with attribution to the site; reciter "
            "rights retained. 242 reciters / 288 moshaf; verified 206 with CORS."
        ),
    ),
    SourceReview(
        name="Islamic Network CDN (per-ayah and per-surah audio)",
        kind="audio",
        status="granted",
        license_url="https://islamic.network/",
        evidence=(
            "Free non-commercial redistribution, reciter copyrights retained. 69 per-ayah "
            "and 159 per-surah editions; global ayah numbering (6236.mp3); verified NO "
            "CORS header."
        ),
    ),
    SourceReview(
        name="Qur'an Kemenag (LPMQ) Arabic text -- Mushaf Standar Indonesia",
        kind="text",
        status="granted",
        license_url=config.PMA_MUSHAF_URL,
        evidence=(
            "Minister of Religious Affairs Regulation 44/2016 Pasal 8(1): 'Teks Mushaf "
            "Al-Qur'an tidak memiliki hak cipta.' Copyright Law 28/2014 Pasal 42(e): "
            "'Tidak ada Hak Cipta atas hasil karya berupa: ... e. kitab suci atau simbol "
            "keagamaan.' Pasal 8(2) keeps the publisher's rights in the khat, the "
            "tanda baca/tajwid/qira'at apparatus and the ornaments, so only the plain "
            "UTF-8 text is taken. VERIFIED 2026-09-18: both instruments downloaded (HTTP "
            "200) and read as text, not summarised. The text is a seventh orthography: it "
            "carries no alef wasla (U+0671) where Tanzil's Uthmani marks 13,819, and only "
            "6 of the 37,416 verse comparisons against the six Tanzil variants coincide."
        ),
    ),
    SourceReview(
        name="Qur'an Kemenag (LPMQ) Indonesian translation, 2019 revision",
        kind="translation",
        status="restricted",
        license_url=config.UU_COPYRIGHT_URL,
        evidence=(
            "A translation is a protected work: Copyright Law 28/2014 Pasal 59(g) covers "
            "'terjemahan, tafsir, saduran, ...' for 50 years from first publication, and "
            "nothing in the Act exempts the ministry. No grant found: the serving API "
            "(web-api.qurankemenag.net) publishes no terms and answers HTTP 403 without "
            "the site's Origin header; the ministry's own site was unreachable on "
            "2026-09-18 (lajnah.kemenag.go.id redirects to a maintenance page) and the "
            "Wayback Machine holds no snapshot of the relevant pages. The 2019 revision is "
            "a re-edit of the ministry translation already published as `id-affairs` under "
            "the QuranEnc grant, but only 116 of 6,236 verses are byte-identical, so that "
            "grant does not cover these bytes."
        ),
        blocker=(
            "Written permission from LPMQ (lajnah@kemenag.go.id; the tashih service at "
            "tashih.kemenag.go.id is the live channel). Ingested and withheld meanwhile: "
            "publish with --include-unverified-licenses once cleared. NOTE ON THE "
            "NON-COMMERCIAL CARVE-OUT: Copyright Law 28/2014 Pasal 43(d) excuses "
            "'pembuatan dan penyebarluasan konten Hak Cipta melalui media teknologi "
            "informasi dan komunikasi yang bersifat tidak komersial', and this project is "
            "non-commercial. It does not lift the verdict: 43(d) is a limitation on "
            "infringement, not a grant, so it confers nothing on a consumer; it is "
            "conditioned on use being non-commercial, while this dataset is offered under "
            "CC BY-SA with no such limit on downstream use; and this repository already "
            "records a non-commercial-only term as `restricted`, which is exactly how "
            "Tanzil's translations are treated. It also requires that the author state no "
            "objection, and LPMQ has stated none reachable to us."
        ),
    ),
    SourceReview(
        name="Qur'an Kemenag (LPMQ) Latin transliteration (the API's `latin` field)",
        kind="transliteration",
        status="unknown",
        license_url=f"{config.KEMENAG_API}?start=0&limit=3&surah=2",
        evidence=(
            "A romanisation carrying authored vocalisation choices, so it is not the "
            "uncopyrightable 'teks Mushaf Al-Qur'an' of Regulation 44/2016 Pasal 8(1): "
            "Copyright Law 28/2014 Pasal 59(g) protects 'karya lain dari hasil "
            "transformasi'. No grant published either -- the API carries no terms and is "
            "the app's private backend (403 without Origin). Complete for all 6,236 "
            "verses, one romanised ayah per verse, with parenthetical case endings."
        ),
        blocker=(
            "Written permission from LPMQ, or generate the transliteration mechanically "
            "from the uncopyrightable Arabic text -- the route recorded above and the one "
            "with no rights holder at all."
        ),
    ),
    SourceReview(
        name="DigitalKhatt digitalkhatt-js -- Indo-Pak (15-line) text",
        kind="text",
        status="granted",
        license_url="https://github.com/DigitalKhatt/digitalkhatt-js/blob/main/LICENSE",
        evidence=(
            "MIT at the repository root: 'Permission is hereby granted, free of charge, to "
            "any person obtaining a copy of this software and associated documentation "
            "files ... to deal in the Software without restriction, including without "
            "limitation the rights to use, copy, modify, merge, publish, distribute, "
            "sublicense, and/or sell copies of the Software.' VERIFIED 2026-09-18: the "
            "text lives at apps/site-angular/src/app/services/quran_text_indopak_15.ts, "
            "1,503,148 bytes, 610 page groups of 15 lines, and parses to 6,236 verses. It "
            "is DigitalKhatt's own typesetting, not a copy of another producer's Indopak "
            "data: 0 of 6,236 verses match the QuranWBW text or the KFGQPC text. The "
            "sibling `indopakfont` is OFL -- a font grant, which never reaches the text. "
            "Published as the `indopak` script."
        ),
    ),
    SourceReview(
        name="Qur'anpedia.net dumps -- Warsh and Qalun (mushafs 4 and 7)",
        kind="text",
        status="granted",
        license_url="https://api.quranpedia.net/dumps/LICENSE.md",
        evidence=(
            "'Free to use inside apps, websites, bots, and research tools -- no attribution "
            "required ... Republishing this data -- in full or in part -- as a downloadable "
            "database or dataset requires: (1) crediting Qur'anpedia.net as the source with "
            "a link, and (2) stating this dump's version.' Both conditions are met: the "
            "attribution is in manifest.json, meta/sources.json and the README, and the "
            "dump version (2026-09-18) travels in the provenance record. VERIFIED "
            "2026-09-18: mushafs-4 (Warsh, 422,507 bytes) and mushafs-7 (Qalun, 418,528 "
            "bytes) each parse to 114 surahs / 6,214 ayahs, Nafiʿ's count rather than the "
            "Kufi 6,236, with per-verse `number_in_hafs` covering all 6,214. Both texts are "
            "genuinely the riwayah and not relabelled Hafs: Warsh carries U+06D2 yeh barree "
            "2,996x and U+06EC 10,055x with no U+0671 alef wasla, and Warsh and Qalun differ "
            "in 4,566 of 6,214 ayahs. The licence's currency clause ('distributing outdated "
            "Quranic text is the distributor's responsibility') is handled as QuranEnc's "
            "equivalent is: the version is recorded and `fetch --force` re-checks upstream. "
            "Fonts and per-page SVG packs are separate KFGQPC assets, not covered."
        ),
    ),
    SourceReview(
        name="KFGQPC (King Fahd Complex) developer text -- Madinah Hafs / QPC",
        kind="text",
        status="restricted",
        license_url="https://web.archive.org/web/20240518045023/https://dm.qurancomplex.gov.sa/copyright/",
        evidence=(
            "The Complex does publish real per-ayah data (Excel/CSV/SQL/XML/JSON/PDF/Word "
            "with page, jozz and line_start/line_end), and its own IT department built it, "
            "so its terms do reach the text rather than a third party's transcription. But "
            "the only grant it publishes is scoped to output formats: 'يتشـرَّف المجمع "
            "بإتاحة نسخة رقمية كاملة ... رسم المتجهات Illustrator ... ويمكن استخدام النسخة "
            "المذكورة مجاناً في المجالات الشخصية والأعمال الفردية كافة ... ومواقع الإنترنت "
            "والبرامج الحاسوبية' -- Illustrator/PDF/images/TrueType files, not a verse "
            "array. Elsewhere the Complex states 'جميع الحقوق محفوظة لمجمع الملك فهد لطباعة "
            "المصحف الشريف © 2025' and its policy page: 'All the contents ... including the "
            "texts ... and compiled information are owned by the Complex'. The whole domain "
            "timed out from this network (HTTP 000 on qurancomplex.gov.sa, dm., fonts., "
            "download., policy.), so these are archive snapshots of the rights holder's own "
            "pages, not third-party summaries."
        ),
        blocker=(
            "Written permission from KFGQPC for the verse text itself, or a granted "
            "redistribution route from a party that holds the text. The Arabic rasm this "
            "tradition prints (Hafs, Uthmani) is already covered by Tanzil's `uthmani`; "
            "what is missing is the Complex's own transcription and its calligraphy, which "
            "no grant reaches."
        ),
    ),
    SourceReview(
        name="KFGQPC developer text -- Warsh narration",
        kind="text",
        status="restricted",
        license_url="https://web.archive.org/web/20250907020432/https://qurancomplex.gov.sa/en/techquran/dev/",
        evidence=(
            "A versioned, complete-looking Warsh package exists: 'It contains files for "
            "developers (Excel, CSV, HTML5, SQL, XML, JSON, TXT and PDF)' with fields jozz, "
            "page, sura_no, line_start, line_end, aya_no, aya_text; 8.62 MB, MD5 "
            "4701e8bbf053098220cf2cf4cda206a1, version 6.0. It carries no licence text, and "
            "the site footer reads 'جميع الحقوق محفوظة ... © 2025'. The same text reaches the "
            "world only through mirrors whose licences cover packaging (fawazahmed0/quran-api "
            "Unlicense; QUL account-gated, no per-resource licence). Two independent mirrors "
            "are byte-identical after one documented mapping (U+08F0 -> U+0657), which "
            "confirms the provenance, not a grant. Published instead from Qur'anpedia.net's "
            "granted dump."
        ),
        blocker="A redistribution grant from KFGQPC for the text package.",
    ),
    SourceReview(
        name="Diyanet (Türkiye) Turkish mushaf text",
        kind="text",
        status="restricted",
        license_url="https://acikkaynakkuran-dev.diyanet.gov.tr/",
        evidence=(
            "The Presidency publishes a complete per-ayah text (kuran.diyanet.gov.tr/Yayinlar, "
            "kuran.docx: 114 surahs, 6,236 verses), but its API page refuses redistribution: "
            "'...metin, ses dosyası, veri seti, kaynak dosya... firma, vatandaş, bireysel "
            "yazılım geliştiricisi veya diğer üçüncü kişilerle paylaşılmamaktadır' and bulk "
            "transfer/republish/source-file requests are 'karşılanamamaktadır'; the API key "
            "itself is capped (30 pages, 9 ayat per surah, juz 1). The download carries no "
            "licence, only a meta copyright '(c) 2016 Bilgi Yönetimi ve İletişim Daire "
            "Başkanlığı'. Measured, it is also not an Uthmani text: 0x U+0671, 10,012x "
            "U+06EA (Turkish isaret) and an embedded 'Shaikh Hamdullah Mushaf' font. "
            "SEPARATELY, 'ayet-berkenar' is a page-layout convention, not a reading or an "
            "orthography: Diyanet's own Hafızlık Eğitimi Rehberi defines it as 'her sayfada "
            "on beş satırdan müteşekkil' (fifteen lines per page). A verse array carries no "
            "page geometry, so ayet-berkenar cannot be delivered by a text script at all."
        ),
        blocker=(
            "Written permission from Diyanet for the text dataset. Note that even with it, "
            "the Turkish mushaf's isaret layer and the ayet-berkenar pagination are "
            "editorial/apparatus material outside a plain text grant."
        ),
    ),
    SourceReview(
        name="QuranWBW / Quran.com IndoPak text (QUL resources 55/59, QF text_indopak)",
        kind="text",
        status="restricted",
        license_url="https://github.com/marwan/indopak-quran-text",
        evidence=(
            "The most widely redistributed IndoPak text, and the one an `indopak` label "
            "usually means. Its authors' own notice: 'Made by Ayman Siddiqui and R. Siddiqua "
            "for www.QuranWBW.com and www.Quran.com for Sadaqa-e-Jaria purposes only. DO NOT "
            "SELL, MANIPULATE, DISTRIBUTE WITHOUT CREDITS OR TAMPER IN ANY FORM OR MANNER.' "
            "Sadaqa-e-Jaria is a religious-benefit framing, not a redistribution grant, and "
            "the notice forbids distribution outright, so no credit condition can satisfy "
            "it. Quran Foundation's developer terms add: QF Content 'is not sold, "
            "sublicensed, or redistributed', with a dataset or content package requiring a "
            "separate written commercial licence, and a one-week cache limit. QUL publishes "
            "no licence field for the resource, its downloads are account-gated (HTTP 401), "
            "and its own credits page says the majority of its resources 'were created or "
            "curated by the community, not Tarteel'. Independent corroboration: "
            "UmmahLibrary removed the bundled Indopak text and fetches it live from "
            "quran.com display-only, tracking an unanswered permission request."
        ),
        blocker=(
            "Written permission from the text's authors (Ayman Siddiqui / QuranWBW) or a "
            "commercial licence from Quran Foundation. Neither has granted one publicly."
        ),
    ),
    SourceReview(
        name="KFGQPC Indopak / Nastaleeq text via fawazahmed0/quran-api",
        kind="text",
        status="unknown",
        license_url="https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions.json",
        evidence=(
            "CORRECTS an earlier audit: an IndoPak edition DOES exist here -- "
            "ara-quranindopak (1,967,814 bytes) and ara-qurannastaleeqn (1,992,827 bytes), "
            "6,236 verses each, per-ayah, self-declaring KFGQPC as their upstream "
            "('This is a copy of Quran Nastaleeq from https://fonts.qurancomplex.gov.sa/'). "
            "Both are genuine Indopak rasm (U+06E1 ~62,300x, U+0656 ~990x, 0x U+0671) and "
            "distinct from the QuranWBW text (58 of 6,236 verses shared). But the repo's "
            "Unlicense covers its packaging only, and KFGQPC's own terms could not be "
            "reached (every qurancomplex host returned HTTP 000), so no grant can be quoted."
        ),
        blocker=(
            "KFGQPC's own terms, or a grant from the mirror. What is reachable is "
            "DigitalKhatt's MIT text, which is published instead."
        ),
    ),
    SourceReview(
        name="alquran.cloud `quran-indopak` (Islamic Network)",
        kind="text",
        status="unknown",
        license_url="https://api.alquran.cloud/v1/quran/quran-indopak",
        evidence=(
            "The endpoint serves 6,236 verses, but the edition is undocumented: its own "
            "metadata endpoint 404s, it is absent from the 331-edition catalogue and from "
            "the OpenAPI spec, and no provenance, author or licence is stated anywhere "
            "reachable (alquran.cloud/terms 404s). Measured, it is also not the QuranWBW "
            "Indopak text but a hybrid: U+06E1 x37,372, U+0671 alef wasla x13,819, U+06CC "
            "Farsi yeh x22,024 -- a Persianised transcription layer no other Indopak text "
            "has. 0 of 6,236 verses match quran.com's text_indopak."
        ),
        blocker="A stated provenance and grant from Islamic Network for this edition.",
    ),
    SourceReview(
        name="QUL mushaf-layout resources (Taj 13/16-line, Qudratullah 13/15-line, Gaba 9-line)",
        kind="text",
        status="restricted",
        license_url="https://qul.tarteel.ai/resources/mushaf-layout",
        evidence=(
            "Where the 13/15/16-line Indo-Pak print traditions actually live online, as "
            "page/line grids rather than texts: 12 layouts, tagged Indopak 5 / QPC 4 / "
            "Madani 3 / Digital khatt 1, offering sqlite, docx, images or zip -- never a "
            "per-ayah rasm. The pages state no licence; Tarteel's terms call the Service "
            "Content 'the proprietary property of Tarteel or its licensors' and forbid "
            "copying or distributing it. QUL re-hosts exist without any licence (e.g. a "
            "`quran-indopak` repo mirroring exactly these archives). CONCLUSION ON THE "
            "AXIS: Taj Company 13-line/16-line and Qudratullah 13-line/15-line are layouts, "
            "not separate texts, so a verse array of an Indopak text does not imply any of "
            "them. DigitalKhatt's MIT file is the one Indopak artefact that carries a "
            "15-line page structure as data."
        ),
        blocker=(
            "A grant from each layout's originator. Not needed for the text we publish: a "
            "per-ayah scripture carries no page geometry."
        ),
    ),
    SourceReview(
        name="King Saud University e-Mushaf (`quran.ksu.edu.sa`) -- Warsh mode",
        kind="text",
        status="unknown",
        license_url="https://quran.ksu.edu.sa/index.php?l=en",
        evidence=(
            "VERIFIED 2026-09-18: the site offers Hafs, Hafs-Mujawwad and Warsh, and says of "
            "Qalun 'وقريباً رواية قالون' (soon) -- announced, not shipped. Warsh is served as "
            "*page images*, not text: engine.js holds `'warsh': {url:'warsh/', ext:'png', "
            "page_key:'Page_warsh'}` and the site's only text panel is Hafs Imlaei "
            "('نص القرآن الكريم (إملائي)'). Its Page_warsh index differs from the Hafs "
            "pagination in 28 of 604 page-starts, so it is genuine Maghribi pagination "
            "(axis 3). There is no API (/api/ 404s) and no terms page: support/index.php, "
            "support/terms.php and about.php all 404."
        ),
        blocker=(
            "No text to take and no rights statement to rely on. Warsh is published "
            "instead from Qur'anpedia.net's granted dump."
        ),
    ),
    SourceReview(
        name="Morocco -- Ministry of Habous and the Mohammed VI Foundation",
        kind="text",
        status="restricted",
        license_url="https://www.habous.gov.ma/",
        evidence=(
            "The origin and rights holder of the Maghribi mushaf, by dahir 1.09.198 "
            "(23 Feb 2010): the Mohammed VI Foundation for the Publication of the Holy "
            "Quran is 'هيئة وطنية مرجعية عليا في مجال الإعداد العلمي والمادي والفني لنسخ "
            "المصحف الشريف ونشره', mandated to re-copy the Quran 'برواية ورش عن نافع' and "
            "among other things to license reproduction. It publishes no machine-readable "
            "text: almoshaf-almohammadi.ma is a reader whose API refuses unauthenticated "
            "calls (403 'The used authentication method is not allowed on this route.'), and "
            "habous.gov.ma offers no bulk text. quran.ma was unreachable (HTTP 000)."
        ),
        blocker="A licence from the Foundation, which explicitly runs a permission regime.",
    ),
    SourceReview(
        name="Malaysia -- KDN licensing under Akta 326, and Brunei's per-item vetting",
        kind="text",
        status="restricted",
        license_url="https://www.mygp.gov.my/garis-panduan-permohonan-lesen-mencetak-teks-al-quran",
        evidence=(
            "Malaysia has no published Malaysian-standard text, and its regime is stricter "
            "than Indonesia's: a licence is required to print or publish Quran text under "
            "the Printing of Quranic Texts Act 1986 (Akta 326), failing which a fine to "
            "RM10,000 and/or three years, administered by Kementerian Dalam Negeri (KDN, not "
            "JAKIM) through the LPPPQ. Brunei vets each item: the Religious Affairs Ministry "
            "publishes a list of approved Quran editions (LULUS/PEMBETULAN) vetted by the "
            "Da'wah Islamiah Centre, with a footer reading 'Hak Cipta Terpelihara', and no "
            "machine-readable Brunei text exists. Neither country's standard is a separate "
            "rassm: both work from rasm Uthmani, which Tanzil's texts already cover."
        ),
        blocker=(
            "A Malaysian printing licence does not grant redistribution, and no Malaysian "
            "or Bruneian text dataset has been published for licensing."
        ),
    ),
    SourceReview(
        name="Bombay mushaf (the print tradition)",
        kind="text",
        status="unknown",
        license_url="https://web.lpmqkemenag.id/berita-dan-artikel/artikel/mushaf-al-qur-an-standar-usmani.html",
        evidence=(
            "Not a text edition, so there is nothing to license: the Bombay mushaf is a "
            "print family (Mumbai), Hafs with a rasm-Usmani-family text and its own waqf "
            "conventions, reprinted across Southeast Asia by Menara Kudus, Toha Putra and "
            "Sulaiman Marʿī, in 13, 17 or 18 lines as the printer chose. LPMQ records that "
            "the 1960 Bombay mushaf was the model for Indonesia's standard rasm and tanda "
            "baca, and still certifies 'Mushaf Al-Qur'an Bombay 18 Baris Ayat Pojok'. No "
            "digital text self-identifies as Bombay; the modern digitised descendants are "
            "layout grids (Taj 16-line, Qudratullah 15-line) tracked above."
        ),
        blocker=(
            "Nothing to unblock as a text: the tradition is print layout plus a waqf "
            "convention on an Uthmani-family Hafs text, which is already published."
        ),
    ),
)


def review_manifest() -> dict[str, Any]:
    """The committed record of every source reviewed and its verdict."""
    return {
        "reviewed": REVIEWED,
        "note": (
            "Verdicts are derived from the rights holders' own terms, not from aggregator "
            "or packager licences. `unknown` is not permission. Only `granted` sources may "
            "be published; see quranjson.licensing."
        ),
        "sources": [asdict(review) for review in CANDIDATES],
        "published": {
            "quranenc": "all 75 catalogue editions (see data/quranenc/catalogue.json)",
            "extra": [
                {
                    "lang": edition.lang,
                    "author": edition.author,
                    "status": edition.license.status,
                }
                for edition in config.EXTRA_EDITIONS
            ],
            "text": (
                "tanzil variants (CC-BY 3.0, verbatim), kemenag (the Indonesian mushaf "
                "text, which its publishing regulation holds to be uncopyrightable), "
                "indopak (DigitalKhatt, MIT), and warsh and qalun (Qur'anpedia.net, whose "
                "licence requires crediting them and stating the dump version)"
            ),
        },
    }
