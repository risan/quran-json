# Transliteration source decisions for local expansion

Checked 2026-09-20 against the live primary pages, direct files, and the current QUL
application source. This is an implementation note for the requested candidates only:
Kemenag Latin, Tanzil English and Turkish, and QUL resources 71, 469, 475, and 478.

## Decision matrix

| Edition/source | Corpus and fetch locator | Verified format and coverage | Deduplication | Rights and implementation status |
|---|---|---|---|---|
| Kemenag Latin | Existing `data/kemenag/quran.json`; refresh from `https://web-api.qurankemenag.net/quran-ayah?start=0&limit=286&surah=N`, `N=1..114`, with `Origin: https://quran.kemenag.go.id` | API JSON `data[]`; one authored plain-text `latin` field per ayah. Local snapshot has 114 surahs and 6,236 ayahs. | Distinct from Tanzil English and Turkish. | Keep existing `unknown` corpus status. It is already registered as `ara-kemenag-latin`; the repository currently emits it only through its explicit unverified-rights override. That is an operational state, not corpus-rights clearance. |
| Tanzil English | <https://tanzil.net/trans/en.transliteration> | UTF-8 `surah|ayah|text`, 6,236 rows. Almost every row contains presentation tags (`u`, `b`, sometimes `i`/`strong`, case-insensitive). Footer identifies `en.transliteration`, English Transliteration, last update 2010-09-06. | After stripping those tags, all 6,236 rows exactly equal existing `data/editions/transliteration.json`. Do not create a second corpus or copy new public data. Add provenance/alias metadata to the existing legacy edition. | `restricted` under the terms on Tanzil's translation page. Reuse the legacy bytes already present; do not describe them as covered by Tanzil's Arabic-text CC notice. This work does not expand their public distribution. |
| Tanzil Turkish | <https://tanzil.net/trans/tr.transliteration> | UTF-8 `surah|ayah|text`, plain Unicode without HTML tags, 6,236 rows. Footer identifies `tr.transliteration`, *Çeviriyazı*, Muhammet Abay, last update 2010-09-15. | New versus the existing English corpus. QUL 468 is a mirror/family duplicate and is outside this requested set; do not create a second Turkish copy. | Add a tested importer and truthful withheld record with `restricted` status. Fetch only into a private, ignored local snapshot for validation. Do not activate a public CDN edition through the generic unverified-rights override; Tanzil permission is still required for public redistribution. |
| QUL 71 | <https://qul.tarteel.ai/resources/transliteration/71> | English word-by-word; advertised JSON and SQLite. Public samples use Latin diacritics such as `ʿ` and macrons. Official exporter shapes are JSON `{ "surah:ayah:word": "text" }` and SQLite `(surah_number, ayah_number, word_number, text)`. Bound previews exist for 1:1 and 114:6, but a full export was unavailable for a gap count. | Its word granularity makes it distinct from existing ayah English. | Register as an `unknown`, word-level import source. The official download requires normal sign-in and a generated token; do not scrape 6,236 preview pages or guess tokens. Ingest only a user-supplied official JSON/SQLite export, then validate coverage. |
| QUL 469 | <https://qul.tarteel.ai/resources/transliteration/469> | “English Transliteration(Tajweed)”, ayah-by-ayah. Page advertises `simple.json`, `simple.sqlite`, `json`, and `sqlite`; public sample is plain text. A downloaded export is needed to establish whether and how tajweed markup is encoded. Bound previews exist for 1:1 and 114:6; full gap count unverified. | Public 73:4 sample differs from the legacy/Tanzil English text. Run whole-corpus canonical comparison after import. | Register as an `unknown`, ayah-level import source. Same authenticated-export requirement as 71. |
| QUL 475 | <https://qul.tarteel.ai/resources/transliteration/475> | “Syllables Transliteration 2”, English, ayah-by-ayah; JSON and SQLite. Public sample is plain lowercase text and the source HTML indicates spacing may carry syllable grouping, so preserve whitespace until the export is characterized. Bound previews exist for 1:1 and 114:6; full gap count unverified. | Public 73:4 sample differs from the legacy/Tanzil English text. Run whole-corpus comparison after import. | Register as an `unknown`, ayah-level import source. Same authenticated-export requirement as 71. |
| QUL 478 | <https://qul.tarteel.ai/resources/transliteration/478> | “English Transliteration(RTF Updated)”, ayah-by-ayah; JSON and SQLite. QUL explicitly documents HTML `b`, `u`, and `i`; `b` marks silent letters and the others support readability/emphasis. Bound previews exist for 1:1 and 114:6; full gap count unverified. | It shares the Tanzil-style `AA` family but the public 73:4 sample differs (`alqur-ana` versus legacy `alqurana`). Preserve it as a candidate until a whole-export comparison proves whether it is only markup/normalization. | Register as an `unknown`, ayah-level rich-text import source. Same authenticated-export requirement as 71. Preserve source HTML separately from any sanitized/plain rendering. |

The direct Tanzil files fetched during this check each contained exactly 6,236 valid
three-field rows. Their SHA-256 values at the check time were:

```text
en.transliteration  8c20d95e484534e921cd2e0d2546aab7f5300090c0bd76697095b3ca1db1e01d
tr.transliteration  a4130441fb6c2e8c38510461cbb1588170f593d046680691c99cdb5fb474bb19
```

These hashes are provenance receipts, not upstream version guarantees; retain the footer
metadata and retrieval timestamp too.

## Primary terms and their scope

### Tanzil

The current [Tanzil translations page](https://tanzil.net/trans/) includes both “English
Transliteration” and Muhammet Abay's Turkish “Çeviriyazı” in its resource list. Its terms
say the resources on that page are for non-commercial purposes, commercial use requires
the translator's or publisher's permission, and redistribution of the list on another
website requires direct permission from Tanzil. Those are the terms applicable to these
two transliteration resources. Tanzil's separate CC notice for its Arabic Qur'an text
does not establish a licence for them.

Accordingly, keep `license.status = restricted`. The user’s instruction to implement the
sources locally authorizes the repository work; it does not change the upstream corpus
terms. For Turkish, implementation means a fetch/import path, tests against a private
ignored snapshot, and a withheld source record. It does not mean committing the corpus or
turning it on in the public CDN through a generic override. Tanzil permission is still
needed before public activation. For English, reuse the legacy bytes already in the tree
and add provenance without making another public copy. Do not report either corpus as
generally redistributable under the repository licence.

### Kemenag

The live endpoint succeeds only when the official site's Origin header is supplied. A
three-row request was rechecked successfully and returned the expected `latin` field.
The API itself publishes no corpus-specific licence terms. The official LPMQ guide
identifies the Indonesian transliteration convention, but a scheme description is not a
reuse grant for the authored API corpus. Keep the existing `unknown` classification;
do not broaden the legal status of the Arabic mushaf text to cover this Latin field.

Primary locators:

* Presentation/source: <https://quran.kemenag.go.id/>
* Machine endpoint: <https://web-api.qurankemenag.net/quran-ayah>
* Official transliteration explanation:
  <https://tashih.kemenag.go.id/uploads/1/2019-12/buku_tanya_jawab_tentang_mushaf_fth.pdf>

### QUL/Tarteel

Each requested resource's public copyright endpoint currently says only that QUL does
not have copyright information:

* <https://qul.tarteel.ai/resources/71/copyright>
* <https://qul.tarteel.ai/resources/469/copyright>
* <https://qul.tarteel.ai/resources/475/copyright>
* <https://qul.tarteel.ai/resources/478/copyright>

This is absence of corpus-specific information, not a prohibition and not a grant. QUL's
[FAQ](https://qul.tarteel.ai/faq) says commercial projects must review the terms for each
resource. Its [credits](https://qul.tarteel.ai/credits) say most resources were created or
curated by the community rather than Tarteel; those general credits do not identify the
original author of any of these four resources. Record the original author/source as
`unknown`, with QUL as the source host/curator, until an official export supplies more
metadata. Do not infer a corpus licence from the QUL software repository's licence or
Tarteel's site terms.

The live detail pages show download buttons, but an unauthenticated request opens the
normal sign-in dialog. The current official application source confirms that file
downloads use opaque tokens and the controller authenticates the user before the
download action:

* [download UI](https://github.com/TarteelAI/quranic-universal-library/blob/5331a0a8b4f20e21dc5d8a056d4ad950be3f7c15/app/views/card/_download_dropdown.html.erb)
* [authenticated controller](https://github.com/TarteelAI/quranic-universal-library/blob/5331a0a8b4f20e21dc5d8a056d4ad950be3f7c15/app/controllers/resources_controller.rb)
* [ayah exporter](https://github.com/TarteelAI/quranic-universal-library/blob/5331a0a8b4f20e21dc5d8a056d4ad950be3f7c15/lib/exporter/export_transliteration.rb)
* [word exporter](https://github.com/TarteelAI/quranic-universal-library/blob/5331a0a8b4f20e21dc5d8a056d4ad950be3f7c15/lib/exporter/export_word_transliteration.rb)

QUL also states that it currently has no API. There is therefore no stable anonymous
machine-download URL to put in an automated fetcher today. The implementable path is a
source descriptor plus a validated import command for a file downloaded through the
official account flow. The checkout has no QUL credentials or downloaded export, so the
four corpora themselves cannot truthfully be added from the public pages in this run.

## Required import and QA behavior

1. **Do not duplicate Tanzil English.** Keep the frozen `ara-quran-la` bytes and attach
   the direct Tanzil identity, footer version, retrieval date, and source hash. If the
   modern catalogue needs a clearer id, expose an alias rather than writing a second
   6,236-ayah payload.
2. **Add Tanzil Turkish as a separate reader edition.** Preserve all Unicode diacritics,
   apostrophe/backtick distinctions, punctuation, and case. Validate exactly 114 surahs,
   6,236 unique Kufi keys, ordered within each surah, and no gaps or duplicates.
3. **Keep Kemenag on its existing source path.** Reuse its verified 114-window fetcher
   and current 6,236 snapshot. This request does not justify another edition id for the
   same bytes.
4. **Represent all four QUL resources now as distinct import sources.** Each descriptor
   should include QUL id, canonical detail URL, granularity, advertised formats, markup
   policy, `author = unknown`, `license.status = unknown`, and `fetch.mode = manual_export`.
   Resolve each configured input from a documented ignored local path. The absence of a
   local export should be reported as unavailable input, not silently replaced with
   preview scraping. Registration does not activate a public edition.
5. **Validate QUL after an official export is supplied.** For 469/475/478 require exactly
   the 6,236 Kufi ayah keys before enabling the edition. QUL's FAQ explicitly calls its
   translations, Quran scripts, and recitations Hafs-based, but does not make that same
   statement explicit for transliteration, so verify alignment from the file. For 71 validate
   `surah:ayah:word` key syntax, unique ordered word positions, both corpus bounds, and
   coverage of every ayah; do not invent a universal word count because tokenization can
   vary by source.
6. **Treat rich text as data.** Preserve the original 478 HTML string. For rendered or
   plain output, parse and allowlist only `b`, `u`, and `i`; never run regex-only HTML
   cleanup in the browser. Store the normalization policy so a plain derivative is not
   mistaken for source bytes. Apply the same inspection to 469 before calling its
   “Tajweed” label structured markup.
7. **Run canonical deduplication before publication.** Compare exact source strings,
   Unicode-normalized strings, approved-markup-stripped strings, and whitespace-preserved
   strings. Keep 469/475/478 separate when the underlying text or semantic markup differs;
   alias them when only packaging differs. Do not infer distinct authorship from distinct
   QUL ids.
8. **Keep publication state explicit.** Private/local acquisition and validation are
   separate from public CDN publication. New `unknown` and `restricted` sources remain
   withheld even when an ignored local input is available; do not route them through the
   existing generic public override. Public activation requires corpus-specific evidence
   that supports redistribution. A later grant can change that field without changing
   corpus identity or source provenance. Existing Kemenag override behavior is recorded
   as current repository state, not broadened by this decision.

## Suggested source identities

These are implementation labels, not claims that QUL authored the data:

```text
ara-quran-la                         existing Tanzil English corpus; attach alias/provenance
ara-tanzil-tr-muhammet-abay          Tanzil Turkish, ayah, restricted
ara-kemenag-latin                    existing Kemenag Latin, ayah, unknown
ara-qul-en-wbw-71                    QUL-hosted, word, unknown/manual export
ara-qul-en-tajweed-469               QUL-hosted, ayah, unknown/manual export
ara-qul-en-syllables-475             QUL-hosted, ayah, unknown/manual export
ara-qul-en-rtf-updated-478           QUL-hosted, ayah/rich HTML, unknown/manual export
```

For every entry keep `source_host` separate from `author`, and keep
`audience_language = en|tr|id` separate from `target_script = Latn`.
