# Qur'an transliteration research

Research date: 2026-09-20. This note separates a **scheme** (rules for mapping one
script to another) from a **corpus** (the rules already applied to every ayah), and
separates both from a translation.

## Answer to “does every language have its own transliteration?”

No. A translation changes language. Transliteration changes script, and its identity
is determined by the source orthography, target script, and mapping scheme. A generic
Arabic-to-Latin scheme can be useful regardless of the reader's language. A reading or
pronunciation transcription may instead be tailored to Indonesian, Turkish, English,
or another audience. There can be several competing schemes for one audience, while
many languages have no reviewed, complete Qur'an transcription at all.

Unicode CLDR makes the same distinction: generic script transforms and
language-specific transforms serve different purposes, and reversible scholarly
transliteration trades readability for a closer character mapping. It also warns that a
standard transliteration need not reproduce target-language pronunciation
([CLDR transliteration guidelines](https://cldr.unicode.org/index/cldr-spec/transliteration-guidelines)).

The Indonesian Ministry's own guide is especially precise. It defines transliteration
as changing script, says Indonesian Qur'an transliteration follows the joint ministerial
decree SKB 158/1987, notes that other countries use different systems, and distinguishes
letter-based transliteration from sound-based transcription. For example, emphatic
Arabic vowels are still written with the mapped Latin vowel rather than respelled to
imitate the sound ([LPMQ, *Tanya Jawab Tentang Mushaf Al-Qur'an Standar Indonesia*,
pp. 89–91](https://tashih.kemenag.go.id/uploads/1/2019-12/buku_tanya_jawab_tentang_mushaf_fth.pdf)).

This yields four materially different data products:

| Product | What it represents | Example | Suitable label |
|---|---|---|---|
| Orthographic transliteration | A letter/script mapping, which may be reversible and language-neutral or may follow an audience's writing conventions | ISO 233, ALA-LC, CLDR Arabic-Latin; Kemenag SKB Latin; extended Buckwalter as a machine-oriented subtype | `orthographic_transliteration` or `computational_orthographic_encoding` |
| Reader transliteration | An authored, readable romanization convention whose phonetic precision is not established merely by its name | Muhammet Abay's Turkish text; English-facing Tanzil text | `reading_aid` |
| Pronunciation transcription | An explicit approximation of sound, syllables, or recitation for a named audience | QUL resources advertised as pronunciation, syllable, or tajweed help | `pronunciation_transcription` |
| Phonetic/phonological encoding | Sounds, recitation features, or phonological units for computation; not ordinary reader prose | Quran Transcript phonological script; a corpus's separately documented phoneme field | `phonetic_encoding` |

None is a translation. A romanized Urdu translation is still an Urdu translation in
Latin script, not a transliteration of the Arabic Qur'an.

## What the repository already has

The repository has two complete verse-aligned snapshots:

* The legacy `data/editions/transliteration.json` is Tanzil's
  `en.transliteration` family.
* `data/kemenag/quran.json` contains all 6,236 Kufi-numbered verses and the API's
  `latin` field. The configured edition is `ara-kemenag-latin`, attributed to
  **Kementerian Agama RI (Lajnah Pentashihan Mushaf Al-Qur'an)**, sourced from
  `https://web-api.qurankemenag.net/quran-ayah` and presented by
  <https://quran.kemenag.go.id/>.

The second attribution is established by this repository's source configuration and
snapshot provenance. The official LPMQ guide establishes the national SKB 158/1987
scheme. It does **not** by itself grant reuse of the authored `latin` corpus returned by
the API. The statutory rule cited for the Arabic mushaf text is therefore not a safe
basis for relicensing the Latin rendition. The current `unknown` corpus-rights status is
accurate; distribution can only remain an explicitly separate, unverified-rights choice
until LPMQ supplies terms or permission.

## Verified machine-readable candidates

### 1. Tanzil English-facing and Turkish corpora — best permission request

Tanzil has two distinct, complete 6,236-ayah resources:

* [`en.transliteration`](https://tanzil.net/trans/en.transliteration), an
  English-facing Latin reading aid. Its update log is
  <https://tanzil.net/trans/log/en.transliteration>.
* [`tr.transliteration`](https://tanzil.net/trans/tr.transliteration), credited to
  Muhammet Abay and using Turkish scholarly conventions such as `â`, `ḳ`, and `ẕ`.
  Its log records the complete 1–6236 range:
  <https://tanzil.net/trans/log/tr.transliteration>.

Tanzil's current translations page says redistribution of items on that list on another
website is not allowed without direct permission
([exact terms and catalogue](https://tanzil.net/trans/)). This restriction applies to
the translation/transliteration resources, while Tanzil's separate Creative Commons
notice applies to its Qur'anic Arabic text. These files cannot be represented as covered
by this repository's default licence. They could be distributed as separately licensed
editions if Tanzil grants permission and the resulting notice preserves its conditions.
One request to `admin@tanzil.net` should ask explicitly for both keys, modification
rights, API/CDN redistribution, commercial downstream reuse, and required attribution.

### 2. Qur'an Kemenag `latin` — highest Indonesian value, permission required

The local snapshot is already complete and machine-readable, so there is no acquisition
or alignment risk. It is an Indonesian conventional transliteration based on SKB
158/1987 and 0543b/U/1987, not a generic language-neutral romanization and, by LPMQ's
own explanation, not a sound transcription. Its value is high for this project's likely Indonesian
audience and its institutional attribution is stronger than an anonymous mirror.

No reuse grant for the API's authored Latin corpus was found. Ask LPMQ through its live
Tashih channel at <https://tashih.kemenag.go.id/> (the repository review also records
`lajnah@kemenag.go.id`). The request should distinguish the Latin rendition from the
Arabic mushaf text and ask whether the complete corpus may be redistributed, modified,
and served commercially, plus the exact attribution and version/revision name. Until
then it should remain `license.status = unknown`, not be silently relicensed under the
repository default.

### 3. QUL/Tarteel resources — useful packaging, provenance first

[QUL's transliteration catalogue](https://qul.tarteel.ai/resources/transliteration)
offers downloadable JSON/SQLite, including ayah-level and word-level resources. The
most relevant records are:

| ID | Advertised content | Assessment |
|---:|---|---|
| [71](https://qul.tarteel.ai/resources/transliteration/71) | English word-by-word Latin with diacritics | Potentially useful at word granularity |
| [72](https://qul.tarteel.ai/resources/transliteration/72) | Ayah transliteration | Same textual family as Tanzil English; do not treat the mirror as a new grant |
| [468](https://qul.tarteel.ai/resources/transliteration/468) | Turkish ayah transliteration | Sample matches Muhammet Abay/Tanzil; Tanzil provenance and permission still matter |
| [469](https://qul.tarteel.ai/resources/transliteration/469) | English transliteration with tajweed markup | Distinct display value; markup must be retained or normalized explicitly |
| [475](https://qul.tarteel.ai/resources/transliteration/475) | Syllable-oriented transliteration | Distinct pedagogical value; needs author and method verification |
| [478](https://qul.tarteel.ai/resources/transliteration/478) | Updated rich-text English transliteration | Rich-text ingestion, provenance, and rights need verification |

QUL describes the feature as pronunciation help and documents multiple languages and
levels ([documentation](https://qul.tarteel.ai/docs/transliteration)). Its FAQ tells
users to inspect each dataset's licence before commercial use
([FAQ](https://qul.tarteel.ai/docs/faq)); its credits say the library combines
community-curated and third-party sources ([credits](https://qul.tarteel.ai/credits)).
Availability for download is not a reuse grant. The inspected transliteration records
do not publish a usable per-resource grant. Ask QUL for the original author/source and
terms for 71, 469, 475, and 478; avoid adding 72 and 468 as separate editions when they
only duplicate Tanzil.

### 4. CLDR Arabic-Latin — the strongest ruleset for a derived orthographic layer

Unicode publishes machine-readable
[`Arabic-Latin.xml`](https://github.com/unicode-org/cldr/blob/main/common/transforms/Arabic-Latin.xml)
under the [Unicode License v3](https://github.com/unicode-org/cldr/blob/main/LICENSE).
This is a versionable rule set, not a ready-made 6,236-ayah Qur'an corpus. It is the best
candidate for generating an explicitly **orthographic** Latin layer from an Arabic source
that permits adaptations.

The implementation would need complete Uthmani/imla'i code-point coverage, NFC
normalization, round-trip tests where applicable, verse-count and identifier checks, and
expert review of Qur'anic marks. Its output must say `algorithmic` and
`orthographic_transliteration`; it must not be advertised as authoritative recitation or
pronunciation. Wikisource's fully vocalized imla'i module is a possible adaptable input
([module](https://ar.wikisource.org/wiki/%D9%88%D8%AD%D8%AF%D8%A9:Quran/data_text),
[documentation](https://ar.wikisource.org/wiki/%D9%88%D8%AD%D8%AF%D8%A9:Quran/%D8%B4%D8%B1%D8%AD)),
but its source-specific provenance must be checked rather than relying only on the site's
general [CC BY-SA 4.0/PD policy](https://wikisource.org/wiki/Help:Copyright).

### 5. Quranic Arabic Corpus extended Buckwalter — complete computational orthographic encoding, restricted terms

The Quranic Arabic Corpus defines a reversible, one-to-one ASCII encoding extended with
fourteen Qur'anic symbols
([scheme](https://corpus.quran.com/java/buckwalter.jsp)) and provides a complete
word/morphology download, currently labelled version 0.4
([download](https://corpus.quran.com/download/)). It represents graphemes/code points,
not sounds, so it belongs under computational orthographic transliteration rather than
phonetic encoding. It is valuable as a validation reference, not as readable verse-level
pronunciation prose.

The download page permits verbatim distribution with attribution and prohibits changes;
the [FAQ](https://corpus.quran.com/faq.jsp) additionally describes use as research and
non-commercial. Those terms are not a basis for relicensing the corpus under this
repository's default licence. A separately distributed, unmodified edition might be
possible only after clarifying the apparent terms mismatch and preserving all
restrictions. Converting its word/segment representation into normalized verse strings
would itself be a modification, so permission is needed for that route.

## Candidates to withhold pending evidence

* **Açık Kuran API.** Its API documentation exposes verse `transcription` and
  `transcription_en`, plus Turkish and English word transcription
  ([repository/API examples](https://github.com/acik-kuran/acikkuran-api)). The project
  README says the *project* is CC BY-NC-SA 4.0, but the repository does not contain the
  transcription corpus and the API database has external inputs. That statement cannot
  safely be assumed to cover every returned text. The API hostname also failed DNS in
  this review, so completeness could not be recounted. Confirm corpus authorship,
  provenance, scope of the CC statement, and service availability first. If granted,
  it would require a separately non-commercial/share-alike edition rather than default
  relicensing.
* **Quran-MD audio/text datasets.** The ayah dataset advertises 6,236 unique ayahs and
  romanized Arabic, and the word dataset advertises 77,429 words
  ([ayah dataset](https://huggingface.co/datasets/Buraaq/quran-audio-text-dataset),
  [word dataset](https://huggingface.co/datasets/Buraaq/quran-md-words)). No clear corpus
  licence is displayed, and the described source includes QuranWBW. Treat it as a
  research lead, not a publishable source.
* **QuranWBW language options.** The legacy interface advertises English, Urdu, Hindi,
  Indonesian, Bangla, Turkish, Russian, German, and Ingush word-by-word views, but also
  states that data belongs to its respective owners and copying is not allowed
  ([example page](https://legacy.quranwbw.com/33)). These are interface language options,
  not evidence of nine independently reviewed, complete verse-transliteration schemes.
  The current [MIT code repository](https://github.com/marwan/quranwbw) does not make its
  private CDN corpus MIT-licensed.
* **Quran Transcript.** [`obadx/quran-transcript`](https://github.com/obadx/quran-transcript)
  generates an Arabic-script phonological notation with tajweed attributes. It is a
  useful QA/reference tool but is neither a Latin transliteration nor an
  audience-language edition. Its licence separates MIT software from bundled Tanzil
  text restrictions
  ([licence](https://raw.githubusercontent.com/obadx/quran-transcript/main/LICENSE)).
* **Wrappers and mirrors.** [`Kristories/quran`](https://github.com/Kristories/quran)
  packages the Muhammet Abay/Tanzil Turkish text under an MIT software repository;
  [`nazimali/quranic-transliteration`](https://huggingface.co/datasets/nazimali/quranic-transliteration)
  mirrors English and Turkish rows. A wrapper's repository licence does not replace the
  upstream corpus terms. Neither is an independent permission source.
* **Cyrillic and other scripts.** This review found no complete, versioned,
  machine-readable, clearly reusable Cyrillic Qur'an pronunciation corpus. The same
  evidentiary bar should apply to Bengali, Devanagari, and other target scripts. Their
  absence is a discovery gap, not a reason to synthesize and label an automatic result
  as an authoritative recitation guide.

## Standards are not datasets

ISO 233 is a stringent Arabic-to-Latin character-conversion standard for information
exchange ([ISO 233:1984](https://www.iso.org/standard/4117.html)); its successor is under
development ([ISO/DIS 233-1](https://www.iso.org/obp/ui?_escaped_fragment_=iso%3Astd%3Aiso%3A233%3A-1%3Adis%3Aed-1%3Av1%3Aen)). ALA-LC publishes an Arabic romanization table
for bibliographic work ([Library of Congress tables](https://www.loc.gov/catdir/cpso/roman)).
They do not supply a Qur'an verse corpus. Implementing a named standard requires rights
to use/reproduce the rules, a declared edition of the standard, and validation against
Qur'anic combining marks. Merely naming one does not create an authoritative reading
aid.

## Prioritized additions

1. **Run two permission tracks in parallel:** obtain a corpus-specific grant from LPMQ
   for the already-ingested Kemenag Latin data, and one from Tanzil for both complete
   `en.transliteration` and `tr.transliteration`. These have the highest value and lowest
   technical risk. Store their actual terms per edition rather than describing them as
   covered by the repository default.
2. **Ask QUL about the genuinely distinct resources** 71, 469, 475, and 478. Add one
   only when its original source, author, complete coverage, format semantics, and reuse
   terms are explicit. Deduplicate Tanzil mirrors.
3. **Prototype CLDR-derived orthographic tooling privately** against an Arabic source
   whose adaptation rights have been verified exactly. Do not publish its output unless
   those rights, complete code-point coverage, and expert review of Qur'anic marks are
   all proven. Any eventual edition needs a visible algorithmic/non-pronunciation label
   and pinned rule/source revisions.
4. **Keep QAC Buckwalter as a research/validation source** unless its terms are clarified
   and the product can preserve its word-level, unmodified representation.
5. **Do not promise one edition per language or script.** Add a Cyrillic, Bengali,
   Devanagari, or other reader-facing edition only when a complete reviewed corpus and a
   corpus-specific reuse grant are both verified.

## Suggested metadata contract

Language alone is insufficient. A transliteration catalogue entry should record at
least:

```json
{
  "id": "hafs-kufi-kemenag-latn-skb158-1987",
  "kind": "transliteration",
  "purpose": "orthographic_transliteration",
  "source_language": "ar",
  "source_script": "Arab",
  "target_script": "Latn",
  "audience_language": "id",
  "scheme": {
    "id": "kemenag-skb-158-1987-0543b-u-1987",
    "name": "SKB Menteri Agama 158/1987 dan Menteri Pendidikan dan Kebudayaan 0543b/U/1987",
    "version": "1987",
    "authority": "Government of Indonesia",
    "reversible": false,
    "uri": "https://tashih.kemenag.go.id/uploads/1/2019-12/buku_tanya_jawab_tentang_mushaf_fth.pdf"
  },
  "reading": {
    "qiraah": "Asim",
    "riwayah": "Hafs",
    "verse_numbering": "kufi"
  },
  "granularity": "ayah",
  "coverage": { "surahs": 114, "verses": 6236 },
  "representation": { "normalization": "NFC", "markup": "none" },
  "generation": "authored",
  "review_status": "official_source_unlicensed",
  "source": {
    "url": "https://web-api.qurankemenag.net/quran-ayah",
    "retrieved_at": "<date>",
    "version": null,
    "checksum": "<sha256>"
  },
  "license": {
    "status": "unknown",
    "spdx": null,
    "scope": "corpus",
    "url": null,
    "attribution": "Kementerian Agama RI (Lajnah Pentashihan Mushaf Al-Qur'an)",
    "modification_allowed": null,
    "commercial_use_allowed": null
  },
  "derived_from": null,
  "notes": []
}
```

Use `audience_language: null` for a language-neutral scholarly mapping. Use
`purpose: computational_orthographic_encoding` for extended Buckwalter or an equivalent
grapheme/code-point representation; do not classify it as phonetic. For generated
editions also record `generator_version`, `rule_set_version`, exact Arabic source
revision/checksum, and human review status. For QUL-style resources record `markup`
(`html_tajweed`, `rtf`, or `none`) and word/ayah granularity. Keep licence `scope`
explicit (`corpus`, `software`, or `site`) so a permissive code licence is never inferred
to cover imported text.
