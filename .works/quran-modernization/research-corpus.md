# Corpus and translation expansion research

Research date: **2026-09-20**

Scope: recommendation only. This report does not ingest data, contact rights
holders, or authorize publication. It distinguishes a usable endpoint from a
right to redistribute its contents.

## Executive recommendation

The repository already covers the main Arabic text families unusually well:
Hafs in Uthmani and Imlaei forms, an Indonesian Uthmani standard, a
DigitalKhatt Indo-Pak form, and the Warsh and Qalun riwayat. There is no
permission-ready, widely adopted Hafs "script" that should simply be added by
name.

The strongest missing Arabic corpus is **al-Dūrī ʿan Abī ʿAmr**. It is a
different riwayah, not a font or orthographic skin. The King Fahd Complex says
it is read in Sudan and East Africa, and both the Complex and Quranpedia expose
machine-readable text. Regional-use and technical-source evidence are strong; the
redistribution chain is not yet clear enough for this repository because the
Quranpedia edition identifies KFGQPC as its source, while no KFGQPC dataset
redistribution grant was found.

The strongest orthographic audit hypothesis is a Hafs **Indo-Pak/Nastaliq**
edition that interoperates with a widely used digital text. The current
`indopak` is a legitimate DigitalKhatt edition, but it does not stand in for
every text labelled Indo-Pak. Quranpedia now publishes a Hafs Nastaliq dump,
but describes it as KFGQPC-derived and not matching the printed edition. Only
a byte-level comparison can show whether it matches QuranWBW, Quran
Foundation, or any common 15-line product. It is a promising audit target, not
a cleared addition or a proven interoperability match.

For translations, the live QuranEnc canonical API list contains the same 75
editions already represented in the repository. QuranEnc's website also has
important browse editions omitted from that list. Direct surah endpoints work
for them, but their omission from the endpoint documented as "Available
translations" may be deliberate. Treat the general QuranEnc republication
terms as favorable evidence, not proof that every omitted edition is cleared
for bulk republication.

The practical translation queue is:

1. Bengali: Abu Bakr Zakaria and/or the newer Rowwad edition.
2. Malay: Abdullah Muhammad Basmeih.
3. Modern Russian: Rowwad, while retaining the existing historical editions.
4. Korean: Hamid Choi or Rowwad.
5. Italian: Rowwad.
6. Ukrainian: Mykhaylo Yakubovych.
7. Kazakh, Nepali, and Marathi after the first group.

None of those browse-only QuranEnc candidates is marked permission-ready in
this report. The exact edition must first be brought into the official API
catalogue or otherwise shown to fall within QuranEnc's republication grant.

## Current baseline

The generated catalogue inspected on 2026-09-20 contains **84 current
translations in 57 language codes**. Of those, 75 are from the live QuranEnc
machine-readable catalogue, eight are public-domain or directly licensed
extras, and one current Kemenag edition is published under the repository's
unverified-rights override.

This matters when describing a "gap":

- Russian is present, but only through the historical Sablukov (1878) and
  Krachkovsky (1963) editions. This is a **modern-edition gap**, not a language
  absence.
- Bengali is absent from the current catalogue, but the frozen legacy tree has
  Muhiuddin Khan. That legacy edition is withheld from the current build under
  Tanzil's restrictive translation terms.
- Urdu is present through Muhammad Junagarhi. Maududi is a missing additional
  edition, not missing Urdu coverage.
- French is present through Rachid Maach and Noor International. Hamidullah is
  a missing additional edition, not missing French coverage.
- English already has nine current editions. Mustafa Khattab and Abdel Haleem
  are edition-diversity requests, not reach gaps.

Repository facts above come from the generated
`cdn/translations/index.json`; legal conclusions below come from the linked
primary sources.

## Keep the axes separate

| Axis | Meaning | Examples | Dataset consequence |
|---|---|---|---|
| Riwayah / qira'ah | Which transmitted reading is represented | Hafs, Warsh, Qalun, al-Dūrī | Words, vocalization, and verse numbering may differ; it needs its own corpus and mappings. |
| Rasm / orthography / dabt | How a reading is written and marked | Uthmani, Imlaei, Indo-Pak, Maghribi signs | May change characters and combining marks without changing the reading. Preserve exact source bytes. |
| Font | Glyph design and shaping rules | Amiri, Scheherazade, QPC fonts, Nastaliq faces | A font is not a text edition. Coverage and shaping are tested separately. |
| Page layout | Page, line, word, or glyph placement | 13/15/16-line, ayet-berkenar, QCF V1/V2 glyph streams | This is layout metadata or a font-coupled encoding, not a verse-text `script`. |
| Annotation | Meaning layered onto text | tajweed colours, pause explanations, morphology | Publish as spans/ranges or structured annotations; do not turn it into another supposed reading. |

## Arabic corpus candidates

### Ranked shortlist

| Priority | Candidate | What it actually is | Use/distribution evidence | Machine availability | Redistribution evidence | Recommendation |
|---|---|---|---|---|---|---|
| P0 | al-Dūrī ʿan Abī ʿAmr | Riwayah, generally in Uthmani rasm | **High for a bounded region.** KFGQPC explicitly says it is read in Sudan and East Africa. | **High.** KFGQPC lists Unicode text plus Word, Excel, CSV, JSON, SQL, XML and TXT data; Quranpedia publishes a versioned `mushafs-6.json.gz`. | **Conditional.** Quranpedia expressly permits republished dumps with source link and version, but its metadata calls this a KFGQPC edition. KFGQPC publishes downloads but no explicit dataset redistribution grant was found; its site reserves rights. | First corpus to audit. Do not publish until the upstream-rights chain is resolved and verse numbering/mapping is independently validated. |
| P1 | Quranpedia Hafs Nastaliq audit candidate | Orthography and mark encoding for Hafs, plus a Nastaliq rendering convention | **High tradition-level use; exact digital-edition distribution unproven.** Quranpedia describes Nastaliq as used in India and Pakistan, but explicitly says this source does not match print. | **High technically.** Quranpedia lists mushaf 3 and a versioned `mushafs-3.json.gz`. Quran Foundation also serves other IndoPak data to applications. | **Conditional to blocked.** Quranpedia describes its data as KFGQPC-derived; Quran Foundation forbids redistribution of QF Content/raw API data. | Compare Quranpedia mushaf 3 byte-for-byte against DigitalKhatt, QuranWBW, and QF samples before making any interoperability claim. If later added, use its exact source name and never silently replace `indopak`. |
| P2 | KFGQPC exact Hafs Uthmani | Exact official encoding of a reading/rasm already represented by `uthmani` | **High publisher visibility; low incremental semantic reach.** | **High.** KFGQPC publishes developer packages, and Quranpedia publishes corresponding dumps. | **Conditional** for the same KFGQPC chain. | Defer behind al-Dūrī and the Nastaliq audit. Its potential value is byte interoperability and exact signs, not a new reading. |
| P3 | Shuʿbah ʿan ʿĀṣim | Riwayah | **Low-to-medium general-use evidence.** KFGQPC describes it as useful to specialists and students rather than tying it to a broad reading region. | **High.** KFGQPC developer data and Quranpedia `mushafs-9.json.gz`. | **Conditional** for the same KFGQPC chain. | Scholarly expansion after al-Dūrī, not a general-user priority. |
| P3 | al-Susi, al-Bazzi, Qunbul | Other riwayat | **Low general-use confidence.** The available official descriptions emphasize specialist study; no broad current user region was established in this research. | **High.** Quranpedia publishes versioned dumps for each. | **Conditional** for source provenance; availability is not permission. | Defer unless the product explicitly expands into qira'at study. |

Primary sources:

- [KFGQPC developer platform](https://qurancomplex.gov.sa/en/techquran/dev/)
  lists whole-Quran Unicode data and developer formats for Hafs, Warsh,
  Shuʿbah, Qalun, al-Dūrī, and al-Sūsī. It identifies al-Dūrī with Sudan and
  East Africa and describes Shuʿbah/al-Sūsī as specialist-use readings.
- [KFGQPC al-Duri page](https://qurancomplex.gov.sa/riwaiah-dori/) repeats the
  regional-use statement and describes Unicode-conformant text.
- [Quranpedia API policy](https://quranpedia.net/api-docs#usage-policy)
  requires official dumps instead of bulk scraping and requires source credit
  for republished datasets.
- [Quranpedia mushaf catalogue](https://api.quranpedia.net/v1/mushafs) supplies
  the exact provenance descriptions used here, including the KFGQPC source and
  the "not matching the printed edition" qualification for mushaf 3.
- [Quranpedia versioned downloads](https://api.quranpedia.net/dumps?lang=en)
  list the dated mushaf files, SHA-256 support, and per-file version metadata.
- [Quranpedia `LICENSE.md`](https://api.quranpedia.net/dumps/LICENSE.md) says
  canonical Quran readings are shared heritage and licenses Quranpedia's
  digitization/structure, but provides the data as-is and places verification
  on the user. It also says translations and contemporary works remain their
  owners' property.
- [Quran Foundation developer terms](https://api-docs.quran.com/legal/developer-terms/)
  permit display inside an application but say QF Content and raw API data may
  not be sold, sublicensed, or redistributed as a dataset without a separate
  written licence.

### Items not to add as text scripts

| Label seen in products | Correct treatment |
|---|---|
| 13-line, 15-line, 16-line, hifz, or ayet-berkenar | Page/line layout metadata. The line count does not create a new Arabic text. |
| QCF/QPC V1, V2, V4 | Font-coupled glyph identifiers. They are unsuitable as interoperable Unicode verse text. |
| "Madinah font" or "Uthman Taha" | Typeface/calligraphy or a named print edition. A font does not establish new text bytes or redistribution rights. |
| Colour tajweed | An annotation layer tied to character or word spans. Quranpedia's coloured-tajweed mushaf is technically available, but it should not become a plain text `script`. |
| Braille | An accessibility encoding and layout with its own cell/reading rules. It should be a separate accessible representation, not another Arabic Unicode orthography. |

No additional Ottoman/Turkish, Malaysian, Bruneian, or official Maghribi byte
stream was found with both a clear machine source and a clear redistribution
grant. Their printed distribution does not by itself make them dataset candidates.

## Translation expansion

### What QuranEnc currently proves

The [QuranEnc API documentation](https://quranenc.com/en/home/api) describes
`/api/v1/translations/list` as the list of "Available translations" and says
translation contents may be downloaded and republished under seven conditions:
no modification; credit publisher and QuranEnc; state the version; retain
transcript information; report notes; keep current; and do not display the
translation with inappropriate advertising.

On 2026-09-20:

- `https://quranenc.com/api/v1/translations/list?localization=en` returned 75
  editions, exactly the 75 QuranEnc editions already represented here.
- The website catalogue showed additional editions absent from that list.
- Direct endpoints in the documented URL shape returned HTTP 200 for surahs 1
  and 114 for the shortlisted keys below.
- This was a two-surah availability probe only. All 114 surahs, verse counts,
  footnotes, and version consistency were **not** validated.
- The browse-only cards do not offer the same download controls as listed
  editions. A working direct endpoint does not establish that omission as an
  accident.

Therefore the browse-only editions are **technically discoverable, legally
conditional, and corpus-completeness unverified**. The umbrella terms need to
be tied to each exact omitted edition before republication.

### Language reach queue

This table ranks the value of adding a language or a modern edition. "Audience
reach" is a directional product judgment from the language's general reach and
the project's current coverage, not repository telemetry, a Quran readership
estimate, or a measured demand claim. No exact speaker counts are used.
"Distribution evidence" is deliberately separate and means only visible
availability through QuranEnc, Quran.com, or another named publisher; it is
not a readership count. The P0/P1 order is product judgment that
combines language reach, distribution evidence, modernity, and the narrowness
of the source/right uncertainty.

| Priority | Language and exact candidate | Current-project gap | Audience-reach judgment | Distribution evidence | Machine/source readiness | Rights readiness | Recommendation |
|---|---|---|---|---|---|---|---|
| P0 | Bengali — Abu Bakr Muhammad Zakaria (`bengali_zakaria`, v1.1.1) | Current language absent; legacy Muhiuddin Khan exists but is withheld | **Very high** | **Medium-high:** carried by both QuranEnc and Quran.com | Direct QuranEnc surah endpoints respond; full corpus not audited; omitted from canonical list | **Conditional** | Best first Bengali edition because cross-portal distribution is visible. Resolve exact grant/list status before ingest. |
| P0 | Bengali — Rowwad Translation Center (`bengali_rwwad`, v1.1.2) | Same language absence; offers a newer alternative edition | **Very high** | **Medium:** named institutional publisher and newly updated in 2026; independent distribution not measured | Same conditional endpoint status | **Conditional** | Consider alongside Zakaria, but treat "one language added" separately from "two editions added." |
| P0 | Malay — Abdullah Muhammad Basmeih (`malay_basumayyah`, v1.0.0) | Language absent | **High** | **High relative confidence:** QuranEnc and Quran.com both distribute this named edition | Direct QuranEnc surah endpoints respond; omitted from canonical list | **Conditional** | Highest-value single missing Southeast Asian language edition. |
| P1 | Russian — Rowwad Translation Center (`russian_rwwad`, v1.0.1) | Language exists only in two historical editions; legacy Kuliev remains withheld | **High** | **Low-to-medium:** authoritative publisher entry, but broad uptake was not established | Direct endpoints respond; omitted from canonical list | **Conditional** | Add as a modern complement, not a replacement for or relabeling of the historical editions. |
| P1 | Korean — Hamid Choi (`korean_hamid`, v1.0.3) and/or Rowwad (`korean_rwwad`, v1.0.11) | Language absent | **High** | **Medium for Hamid Choi; low/unknown for the new Rowwad edition** | Direct endpoints respond for both; omitted from canonical list; only sample surahs tested | **Conditional** | Choose one only after editorial comparison; two editions do not double language reach. |
| P1 | Italian — Rowwad Translation Center (`italian_rwwad`, v1.0.2) | Language absent | **Medium-high** | **Low-to-medium:** official QuranEnc presence, no independent distribution measure established | Direct endpoints respond; omitted from canonical list | **Conditional** | Good European coverage addition after Bengali/Malay. |
| P1 | Ukrainian — Mykhaylo Yakubovych (`ukrainian_yakubovych`, v1.0.2) | Language absent | **Medium-high** | **Medium:** a named translator and visible on QuranEnc; also mirrored elsewhere, but mirrors do not prove rights | Direct endpoints respond; omitted from canonical list | **Conditional** | Strong named-edition candidate once grant scope is clear. |
| P2 | Kazakh — Khalifa Altai (`kazakh_altai`, v1.0.0) | Language absent | **Medium** | **Medium:** named established edition on QuranEnc; no measured usage | Direct endpoints respond; omitted from canonical list | **Conditional** | Add after the P0/P1 gaps. |
| P2 | Nepali — Ahlul-Hadith Association (`nepali_central`, v1.0.3) | Language absent | **Medium** | **Low/unknown** | Direct endpoints respond; omitted from canonical list | **Conditional** | Worth a later coverage pass. |
| P2 | Marathi — Muhammad Shafee Ansari (`marathi_ansari`, v1.0.0) | Language absent | **High general-language reach, unknown Quran-reader demand** | **Low/unknown** | Direct endpoints respond; omitted from canonical list | **Conditional** | Do not rank solely from total language population; validate audience demand and edition status. |

Edition pages and sample machine endpoints:

- Bengali:
  [Zakaria browse](https://quranenc.com/en/browse/bengali_zakaria),
  [Rowwad browse](https://quranenc.com/en/browse/bengali_rwwad), and
  [Rowwad API sample](https://quranenc.com/api/v1/translation/sura/bengali_rwwad/1).
  [Quran.com also identifies Zakaria](https://quran.com/bn/hud/translation/213),
  which supports cross-portal distribution evidence but not redistribution rights.
- Malay:
  [Basmeih browse](https://quranenc.com/en/browse/malay_basumayyah),
  [API sample](https://quranenc.com/api/v1/translation/sura/malay_basumayyah/1),
  and [Quran.com edition page](https://quran.com/tr/tur/translation/ms-abdullah).
- Russian:
  [Rowwad browse](https://quranenc.com/en/browse/russian_rwwad) and
  [API sample](https://quranenc.com/api/v1/translation/sura/russian_rwwad/1).
- Korean:
  [Hamid Choi browse](https://quranenc.com/en/browse/korean_hamid),
  [Rowwad browse](https://quranenc.com/en/browse/korean_rwwad), and
  [Hamid API sample](https://quranenc.com/api/v1/translation/sura/korean_hamid/1).
- Italian:
  [Rowwad browse](https://quranenc.com/en/browse/italian_rwwad) and
  [API sample](https://quranenc.com/api/v1/translation/sura/italian_rwwad/1).
- Ukrainian:
  [Yakubovych browse](https://quranenc.com/en/browse/ukrainian_yakubovych)
  and
  [API sample](https://quranenc.com/api/v1/translation/sura/ukrainian_yakubovych/1).
- Later queue:
  [Kazakh](https://quranenc.com/en/browse/kazakh_altai),
  [Nepali](https://quranenc.com/en/browse/nepali_central), and
  [Marathi](https://quranenc.com/en/browse/marathi_ansari).

### Famous named editions that are not permission-ready

| Edition | Why users may expect it | Machine availability | Reuse finding |
|---|---|---|---|
| Dr Mustafa Khattab, *The Clear Quran* | Modern English edition, distributed by its publisher and Quran.com | Quran Foundation API and Quranpedia mirror | **Blocked/unknown for this dataset.** Quran Foundation forbids raw-content redistribution. Quranpedia's licence says translations remain the property of their authors/publishers, so its dump cannot supply missing upstream permission. No direct redistribution grant was found. |
| M. A. S. Abdel Haleem | Major modern English named edition on Quran.com | Quran Foundation API and Quranpedia mirror | **Blocked/unknown** for the same reason. |
| Elmir Kuliev (Russian) | Modern Russian edition in Tanzil and other portals | Tanzil and mirrors | **Restricted.** Tanzil translations are non-commercial and the translation list may not be redistributed without permission. Mirror availability does not change that. |
| Muhammad Hamidullah (French) | Long-established French edition in Tanzil; also visible on QuranEnc's website | Several portals | **Conditional/restricted.** The Tanzil copy is restricted; the QuranEnc browse edition is omitted from the canonical machine list. Do not transfer rights from one host to another. |
| Fateh Muhammad Jalandhari or Abul A'la Maududi (Urdu); Maududi English | Common named editions in large portals | Tanzil, Quran.com/Quranpedia mirrors | **Restricted/unknown.** No direct grant was found; Tanzil and Quran Foundation terms do not permit this dataset redistribution. |

Primary rights sources:

- [Tanzil translation terms](https://tanzil.net/trans/) limit translations to
  non-commercial use and forbid redistributing the list on another website
  without direct permission.
- [Tanzil Arabic text licence](https://tanzil.net/docs/text_license) is a
  separate CC BY 3.0 verbatim-copy grant. It must not be applied to Tanzil's
  translations.
- [Quran Foundation developer terms](https://api-docs.quran.com/legal/developer-terms/)
  allow API-backed display, impose storage limits, and prohibit redistribution
  as a dataset or data feed without a separate written licence.
- [Quranpedia's licence](https://api.quranpedia.net/dumps/LICENSE.md) explicitly
  preserves translations and contemporary works as the property of their
  authors and publishers. Its general dump attribution rule is therefore not
  a substitute for translation permission.

Name the English works carefully: the current `english_itani` editions from
Talal Itani's **ClearQuran.com** are not Dr Mustafa Khattab's trademarked
***The Clear Quran***. Similar names do not make the texts or permissions
interchangeable.

## Validation and scholarly-risk controls

Arabic text transformation is the highest-risk place to manufacture a corpus
that no authority actually published. A source may be authentic while a
normalizer, verse splitter, or diacritic filter silently creates a new edition.

Any future corpus addition should require all of the following evidence:

1. **Immutable source identity:** source URL, publisher, edition/riwayah,
   source version, retrieval date, and SHA-256 of the downloaded official
   dump. Use Quranpedia's dump, manifest, and version; do not bulk-scrape its
   API.
2. **Verbatim raw snapshot:** preserve upstream code points before parsing.
   Do not normalize Unicode, replace presentation forms, reorder combining
   marks, strip pause signs, or insert basmalas in the source layer.
3. **Independent structural checks:** 114 surahs; per-surah and total verse
   counts from the edition's own numbering; no duplicate/missing verse keys;
   basmala policy recorded explicitly.
4. **Riwayah-aware mapping:** for any non-Hafs edition, carry a reviewed
   `number_in_hafs` many-to-many mapping. Never infer a constant offset and
   never join a Hafs translation/audio track by array position.
5. **Textual diff classification:** compare base letters, hamza/alef forms,
   vowels, pause signs, verse markers, and whitespace separately. A large
   difference in marks may be expected; a base-letter difference needs
   edition-specific review.
6. **Print/source spot checks:** compare a stratified sample against the named
   authoritative edition, including al-Fatiha, basmala boundaries, long
   surahs, known qira'ah differences, and surahs whose verse counts differ.
7. **Font and shaping checks:** inventory every code point and test coverage
   and shaping in the intended font. Font coverage is not proof that marks are
   positioned correctly.
8. **No silent derived labels:** if the product removes diacritics or markers,
   expose it as a documented derivative with a reproducible transform. Never
   call a generated simplification an official KFGQPC, Indo-Pak, or national
   standard text.
9. **Versioned update policy:** Quranpedia and QuranEnc both require or expect
   consumers to follow corrections. Record upstream versions in the public
   catalogue and make byte changes reviewable; do not update in place without
   a provenance diff.

For translations, also validate exactly 6,236 Hafs verse positions (unless the
edition itself declares another alignment), preserve footnotes without unsafe
HTML, retain translator/publisher/version attribution, and distinguish a
language addition from an additional edition in an already covered language.

## Decision matrix

| Bucket | Candidates | Meaning |
|---|---|---|
| Permission-ready now | **None newly identified** | No candidate combines an exact edition, credible use/distribution evidence, complete validated source, and an unambiguous redistribution chain today. |
| Best rights/source clarification targets | al-Dūrī; Quranpedia Hafs Nastaliq; QuranEnc Bengali and Malay browse editions | High user value and usable machine sources, with a narrow, identifiable uncertainty. |
| Next coverage targets after clarification | Modern Russian, Korean, Italian, Ukrainian | Strong language/modernity gaps; direct source availability exists but exact grant/list status remains conditional. |
| Later coverage | Kazakh, Nepali, Marathi | Real language gaps with weaker distribution evidence or lower demonstrated Quran-specific demand. |
| Do not ingest from current mirrors | Khattab, Abdel Haleem, Kuliev, Hamidullah, Jalandhari/Maududi; Quran Foundation/Quran.com raw content | Popularity and API access do not grant redistribution. |
| Model separately, not as `script` | line/page layouts, QCF glyph streams, fonts, tajweed colours, Braille | They require layout, rendering, accessibility, or annotation models rather than another verse-text key. |
