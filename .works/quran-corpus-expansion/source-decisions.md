# Source decisions for the corpus expansion

Evidence checked: **2026-09-20**

This is a source and terms decision for the ten requested additions. It does
not replace the builder's byte-level, schema, and completeness checks. It does
not cover fonts, SVG pages, audio, or other assets adjacent to the text dumps.
Where this targeted re-check differs from the earlier modernization research,
this file supersedes that report's provisional rights status for these ten
records.

## Decision

| Candidate | Stable source identity | Rights disposition | Implementation disposition |
|---|---|---|---|
| Hafs Nastaliq | Quranpedia mushaf **3**, `mushafs-3.json.gz` | **Granted under the existing `QURANPEDIA` record.** No mushaf-specific exception appears in the current license. | Add as a distinct text-only script/edition. Preserve the source name and qualification that it does not match the printed edition. Do not present it as a generic or canonical Indo-Pak byte stream. |
| al-Duri | Quranpedia mushaf **6**, `mushafs-6.json.gz` | **Granted under the existing `QURANPEDIA` record.** No mushaf-specific exception appears in the current license. | Add as a distinct riwayah, not as an orthographic variant. Derive its source verse count and Hafs mappings from the downloaded dump because the public metadata currently conflicts. |
| Bengali — Abu Bakr Zakaria | QuranEnc `bengali_zakaria`, v1.1.1 | **Granted under the existing `QURANENC` record.** | Manually register the edition because the catalogue API omits it; use the official bulk ZIP and preserve the exact translation content. |
| Bengali — Rowwad Translation Center | QuranEnc `bengali_rwwad`, v1.1.2 | **Granted under the existing `QURANENC` record.** | Same. This is an additional Bengali edition, not additional language coverage after Zakaria is added. |
| Malay — Abdullah Basumayyah | QuranEnc `malay_basumayyah`, v1.0.0 | **Granted under the existing `QURANENC` record.** | Manually register and ingest from the official bulk ZIP. The upstream key spells the name `basumayyah`; retain that key. |
| Russian — Rowwad Translation Center | QuranEnc `russian_rwwad`, v1.0.1 | **Granted under the existing `QURANENC` record.** | Add as a modern additional Russian edition; Russian already exists in the project. |
| Korean — Hamid Choi | QuranEnc `korean_hamid`, v1.0.3 | **Granted under the existing `QURANENC` record.** | Manually register and ingest from the official bulk ZIP. |
| Korean — Rowwad Translation Center | QuranEnc `korean_rwwad`, v1.0.11 | **Granted under the existing `QURANENC` record.** | **Withhold.** The official source has 1,955 empty translations in surahs 14–35 and identifies this edition as in progress. Keep the candidate identity; do not replace it with Hamid Choi. |
| Italian — Rowwad Translation Center | QuranEnc `italian_rwwad`, v1.0.2 | **Granted under the existing `QURANENC` record.** | Manually register and ingest from the official bulk ZIP. |
| Ukrainian — Mikhailo Yakubovych | QuranEnc `ukrainian_yakubovych`, v1.0.2 | **Granted under the existing `QURANENC` record.** | Manually register and ingest from the official bulk ZIP. Use the current upstream title spelling `Mikhailo`; do not silently normalize the credited name. |

These decisions deliberately apply the same provider-level grants the project
already accepted for Quranpedia Warsh/Qalun and the 75 QuranEnc catalogue
editions. No primary source states a narrower rule for these records.

## Quranpedia: scope of the grant

The current [Quranpedia Data License](https://api.quranpedia.net/dumps/LICENSE.md)
is version **2026-09-20**. Its ownership section expressly includes the Quran
text in its canonical qira'at and describes the digitization, structuring,
verification, dabt, linking, and metadata as Quranpedia's work. It permits
republication as a downloadable dataset with two requirements: credit
Quranpedia.net with a link and state the dump version. It also requires a
publisher to keep a copy current and says verification remains the user's
duty. A short operative excerpt is: “crediting Quranpedia.net as the source
with a link.”

The license's explicit third-party exceptions are Quranic Arabic Corpus
morphology under GPL and Quranic Treebank syntax under MIT. It does **not**
name the KFGQPC-derived mushaf texts as an exception. KFGQPC provenance in a
mushaf description therefore does not create a new source-specific prohibition
on the evidence available. Treating mushafs 3 and 6 as blocked while accepting
mushafs 4 and 7 under the same license would be inconsistent.

The grant does not extend to the font and per-page SVG assets shown in mushaf
metadata. This expansion should publish text data only.

Primary endpoints:

- [Data-license text](https://api.quranpedia.net/dumps/LICENSE.md)
- [Bulk-download policy and files](https://api.quranpedia.net/dumps?lang=en)
- [Machine-readable manifest](https://api.quranpedia.net/dumps/manifest.json)
- [Mushaf catalogue API](https://api.quranpedia.net/v1/mushafs)
- [Compact mushaf index](https://api.quranpedia.net/dumps/mushafs-index.json.gz)

### Quranpedia records

| Field | Hafs Nastaliq | al-Duri |
|---|---|---|
| Mushaf ID | `3` | `6` |
| Current source name | `مصحف حفص نستعليق` | `مصحف الدوري` |
| Reading metadata | Hafs from Asim | al-Duri from Abu Amr |
| Count metadata | Kufi (`الكوفي`) | al-Madani al-Awwal (`المدني الأول`) |
| Official download | [`mushafs-3.json.gz`](https://api.quranpedia.net/dumps/mushafs-3.json.gz) | [`mushafs-6.json.gz`](https://api.quranpedia.net/dumps/mushafs-6.json.gz) |
| Manifest `built_at` | `2026-09-20T03:46:39+00:00` | `2026-09-20T03:46:42+00:00` |
| Manifest SHA-256 | `fbec857dd613946604fd4c004d7322778ecf1c058c46080e30702e9bf9959b02` | `f6024036b0040afea6af7973abd78b883ab2a0837ae72f6360b69e597c53999a` |

The mushaf-3 description says this is a Hafs text in Nastaliq used in parts of
Asia such as India and Pakistan, issued by the King Fahd Complex, and **not
matching the printed edition**. Its safe product identity is therefore “Hafs
Nastaliq — Quranpedia mushaf 3,” with the provenance visible. It is not yet
evidence of byte compatibility with QuranWBW, Quran Foundation, or a common
15-line print product.

The mushaf-6 description identifies an Uthmani-script al-Duri edition from the
King Fahd Complex and says it corresponds to the printed edition. The index
labels its count al-Madani al-Awwal. At the same time, Quranpedia's public
mushaf page displays standard Kufi-style per-surah counts totalling 6,236.
That is a source self-inconsistency. It is not a reason to alter, merge, or
split verses. The downloaded dump must decide the published total and mapping.

The current [manifest](https://api.quranpedia.net/dumps/manifest.json) reported
version `2026-09-20` during this check, while the human downloads page was
cached with current version `2026-09-19`, and an earlier compact index carried
`2026-09-18`. Record the license/version embedded in the exact downloaded
payload alongside the manifest version, `built_at`, source URL, and verified
SHA-256. Do not infer that these changing labels are interchangeable.

### Expected Quranpedia shape and builder gates

The downloads page describes each mushaf file as full text plus per-ayah
options using the `/v1/mushafs/{id}` schema. The existing adapter expects a
gzipped JSON object with `data.surahs`; each surah contains `ayahs`, and each
ayah supplies `text`, `number`, and optional `number_in_hafs`.

Before generation, the builder should fail closed unless each new dump:

1. matches the manifest SHA-256 for the fetched version;
2. contains exactly 114 unique, sequential surahs;
3. has non-empty text and sequential source ayah numbers in every surah;
4. has a stable, dump-derived total recorded separately for each script;
5. preserves `number_in_hafs` exactly and validates its type/range;
6. retains source bytes rather than deriving one edition through Unicode or
   orthographic transformation of another; and
7. records source URL, mushaf ID, embedded dump-license version, manifest
   version, `built_at`, and SHA-256 in provenance.

Completeness and exact counts remain builder evidence. This research did not
download either full mushaf payload.

## QuranEnc: scope of the grant

The current [QuranEnc developer page](https://quranenc.com/en/home/api) lists
all eight requested editions in its translation selector and places one
general “Terms and Policies” statement on translation contents. It says those
contents “can be downloaded and re-published” subject to seven conditions:

1. no modification, addition, or deletion;
2. identify the publisher and QuranEnc.com as source;
3. state the version;
4. retain transcript information;
5. notify QuranEnc if a note on a translation is found;
6. update to the latest QuranEnc version; and
7. do not display the translations with inappropriate advertisements.

Nothing in that statement restricts the grant to records returned by
`/api/v1/translations/list`. Nothing on the candidate pages says that an
omitted edition cannot be downloaded or republished. Each edition also has an
official QuranEnc browse page, a working direct QuranEnc translation API, and
a working official bulk SQLite URL. The list omission is therefore an
**operational discovery and freshness limitation**, not an identified rights
prohibition.

The current list endpoint still omits these records, so the normal automatic
catalogue path cannot supply their metadata or alert on their versions. Manual
registration should preserve the same `QURANENC` grant and add explicit
version/freshness checks. API access alone is not the rights basis; the general
republication statement on the same provider's developer page is.

### QuranEnc records

| Key | Language | Exact current title | Version | Page metadata date | Browse page | Official bulk ZIP |
|---|---|---|---|---|---|---|
| `bengali_zakaria` | `bn` | Bengali Translation - Abu Bakr Zakaria | `1.1.1` | `22/05/2021` | [browse](https://quranenc.com/en/browse/bengali_zakaria) | [SQLite ZIP](https://quranenc.com/downloads/sqlite/bengali_zakaria.zip) |
| `bengali_rwwad` | `bn` | Bengali Translation - Rowwad Translation Center | `1.1.2` | `27/08/2026` | [browse](https://quranenc.com/en/browse/bengali_rwwad) | [SQLite ZIP](https://quranenc.com/downloads/sqlite/bengali_rwwad.zip) |
| `malay_basumayyah` | `ms` | Malay Translation - Abdullah Basumayyah | `1.0.0` | `27/01/2021` | [browse](https://quranenc.com/en/browse/malay_basumayyah) | [SQLite ZIP](https://quranenc.com/downloads/sqlite/malay_basumayyah.zip) |
| `russian_rwwad` | `ru` | Russian Translation - Rowwad Translation Center | `1.0.1` | `29/03/2026` | [browse](https://quranenc.com/en/browse/russian_rwwad) | [SQLite ZIP](https://quranenc.com/downloads/sqlite/russian_rwwad.zip) |
| `korean_hamid` | `ko` | Korean Translation - Hamid Choi | `1.0.3` | `03/03/2022` | [browse](https://quranenc.com/en/browse/korean_hamid) | [SQLite ZIP](https://quranenc.com/downloads/sqlite/korean_hamid.zip) |
| `korean_rwwad` | `ko` | Korean Translation - Rowwad Translation Center | `1.0.11` | `07/09/2026` | [browse](https://quranenc.com/en/browse/korean_rwwad) | [SQLite ZIP](https://quranenc.com/downloads/sqlite/korean_rwwad.zip) |
| `italian_rwwad` | `it` | Italian Translation - Rowwad Translation Center | `1.0.2` | `29/08/2022` | [browse](https://quranenc.com/en/browse/italian_rwwad) | [SQLite ZIP](https://quranenc.com/downloads/sqlite/italian_rwwad.zip) |
| `ukrainian_yakubovych` | `uk` | Ukrainian Translation - Mikhailo Yakubovych | `1.0.2` | `26/06/2025` | [browse](https://quranenc.com/en/browse/ukrainian_yakubovych) | [SQLite ZIP](https://quranenc.com/downloads/sqlite/ukrainian_yakubovych.zip) |

All eight bulk URLs returned HTTP 200 with `application/zip` during the source
probe. The complete archives were not retained or audited here. The future
fetch should use these static bulk URLs, not the empty `/en/home/d/sqlite/...`
UI route.

The documented per-surah endpoint is
`/api/v1/translation/sura/{translation_key}/{sura_number}` and returns entries
with `sura`, `aya`, `translation`, and `footnotes`. The existing bulk adapter
expects one `.sqlite` member containing a `translations` table with `sura`,
`aya`, and `translation`, plus optional `footnotes`. That is the expected
schema, not yet a completeness finding for these eight archives.

### Required QuranEnc source identity and builder gates

For every manually registered edition, provenance should include at least:

- provider `quranenc`, exact key, language code, direction, current title,
  current description/transcript metadata, and version;
- the exact browse URL, bulk ZIP URL, and developer-terms URL;
- a locally calculated archive hash for reproducibility; and
- the fetch/check date because the canonical catalogue cannot monitor it.

The builder should fail closed unless each archive contains one usable SQLite
database, the expected table/columns, exactly 114 surahs and 6,236 unique
`(sura, aya)` records, sequential verse numbers matching the repository's
Hafs reference, non-empty translation text, and no unexpected duplicate rows.
Footnotes must remain attached to the correct verse. Preserve translation and
footnote content; restructuring the transport into repository JSON must not
rewrite the contents.

Freshness checking must read the candidate's current browse metadata or an
equivalent official endpoint rather than treating continued HTTP 200 as proof
that the pinned version is current. If an upstream title, version, transcript,
or archive changes, require a reviewed snapshot update. The QuranEnc terms
also require source/publisher credit, version display, retained transcript
information, and reporting any discovered translation note back to QuranEnc;
the last duty is conditional on finding such a note and does not require
contact as part of this ingestion work.

## Remaining unknowns that do not change the present grant decision

- Quranpedia's exact al-Duri verse total and mapping cannot be trusted from the
  public page/index combination; only the pinned dump can settle them.
- Quranpedia's Hafs Nastaliq byte relationship to other Indo-Pak datasets is
  untested. No interoperability claim should be made from the shared label.
- QuranEnc does not explain why these eight records are absent from the
  catalogue API. That affects discovery and updates. No primary text was found
  that turns the omission into a redistribution restriction.
- QuranEnc supplies no observed checksum in the browsed metadata for these
  ZIPs. The project should calculate and record its own archive hash while
  continuing to identify the upstream edition by key and version.

## Post-download completeness finding: `korean_rwwad`

Checked **2026-09-20** after the builder correctly rejected the official ZIP.
This finding changes the ingestion disposition, not the affirmative QuranEnc
rights disposition.

The same-edition primary sources agree that version `1.0.11` is incomplete:

- The [old official catalogue](https://old.quranenc.com/en) identifies the
  exact key as “Korean Translation - Rowwad Translation Center (in progress),”
  dated `2026-09-07`, version `1.0.11`.
- The supported [surah 14 API](https://quranenc.com/api/v1/translation/sura/korean_rwwad/14)
  returns all 52 expected rows, but all 52 `translation` fields are empty.
  Surah 35 similarly has 45 empty rows. Boundary probes show all 43 rows in
  surah 13 and all 83 rows in surah 36 are nonempty.
- The official [surah 14 browse page](https://quranenc.com/en/browse/korean_rwwad/14-1)
  renders the Arabic text but an empty translation span. The gap is therefore
  present in the public browse corpus as well as the export.
- The official uncompressed
  [SQLite export](https://quranenc.com/downloads/sqlite/korean_rwwad.sqlite)
  contains 6,236 verse rows and exactly 1,955 empty translations, comprising
  every verse in surahs 14 through 35. Its locally verified SHA-256 is
  `4427431635203c7418be52eea94a94c1ecc24ac6a87808d85cd161cafa8dd973`.

The old official catalogue exposes same-key XML, CSV, and Excel links:

- `https://old.quranenc.com/en/home/download/xml/korean_rwwad`
- `https://old.quranenc.com/en/home/download/csv/korean_rwwad`
- `https://old.quranenc.com/en/home/download/excel/korean_rwwad`

All three returned HTTP 503 during this check on both the old and current
hosts, so none supplied an auditable alternative. More decisively, the
supported API and browse view are themselves blank for the missing range.
There is no evidence that another current official export contains the absent
text.

**Disposition:** withhold `korean_rwwad` until QuranEnc publishes a complete
same-edition version that passes the nonempty 6,236-row gate. Do not scrape
individual verses to assemble a substitute and do not silently use
`korean_hamid`; it is a different named edition and remains independently
eligible. A future source update should be accepted only after a full official
bulk export validates with zero empty translations.

The independent review below assessed provider rights before this downstream
completeness failure was discovered. Its grant conclusion remains applicable;
its all-ten operational go does not override this source-quality blocker.

## Independent source-decision review

Reviewer: recommendation_review (independent of the evidence author)
Review date: **2026-09-20**
Verdict: **go for all ten text candidates under the existing provider grants**

I independently checked the current primary terms and the exact provider
records named above. The evidence supports the report's decision. No material
correction is required, and no candidate-specific redistribution restriction
was found.

### Rights decision

- Quranpedia's [2026-09-20 data license](https://api.quranpedia.net/dumps/LICENSE.md)
  expressly covers Quran text in canonical qira'at plus Quranpedia's
  digitization, structuring, verification, dabt, linking, and metadata. Its
  downloadable-dataset grant requires Quranpedia attribution with a link and
  the dump version. The only separately licensed data fields it identifies are
  Quranic Arabic Corpus morphology (GPL) and Quranic Treebank syntax (MIT).
  Mushaf 3 and mushaf 6 are listed in the same licensed
  [manifest](https://api.quranpedia.net/dumps/manifest.json) as the already
  accepted Warsh and Qalun dumps; neither requested text uses the morphology or
  syntax exception. KFGQPC provenance in the catalogue is not an expressed
  exception to Quranpedia's grant.
- QuranEnc's [developer terms](https://quranenc.com/en/home/api) state generally
  that translation contents may be downloaded and republished under seven
  listed conditions. The same official page's translation selector includes
  all eight requested editions, and each exact key has an official browse page
  and an official bulk ZIP. The terms do not restrict republication to keys
  returned by `/api/v1/translations/list` and contain no candidate-specific
  exclusion. The canonical-list omission is therefore an operational catalogue
  limitation, not evidence of a narrower grant.

The earlier `conditional/unknown` rights labels should not be carried into the
implementation. For these exact provider records, use `granted` while recording
and enforcing the provider conditions.

### Conditions that must travel with publication

- Quranpedia text must credit Quranpedia.net with a link, state the exact dump
  version, retain exact source identity, and participate in the provider's
  freshness/update process. The distributor remains responsible for verifying
  the text it republishes.
- QuranEnc content must remain unmodified and complete; credit both publisher
  and QuranEnc.com; state the edition version; retain transcript information;
  keep the snapshot current; preserve the conditional feedback duty; and obey
  the advertising condition. Footnotes and provider metadata must not be
  silently discarded.

These are publication obligations under an affirmative grant. They are not
reasons to withhold an otherwise valid candidate.

### Operational uncertainty, separate from rights

Implementation still must fail closed on technical evidence:

- verify downloaded bytes against Quranpedia's manifest hashes and record the
  exact `2026-09-20` dump identity used;
- derive al-Duri's verse total and Hafs mapping from the pinned dump because the
  public count metadata is inconsistent;
- retain Quranpedia mushaf 3 as the exact “Hafs Nastaliq” digital edition and
  preserve its “not matching the printed edition” qualification; do not claim
  byte compatibility with other Indo-Pak datasets or replace `indopak`;
- validate 114 sequential chapters, verse identity, nonempty text, mapping
  coverage, and existing-payload immutability for both Arabic additions;
- register the eight QuranEnc keys explicitly, validate each official ZIP as a
  complete 114-surah/6,236-verse snapshot, preserve translation and footnote
  bytes, calculate a reproducibility hash, and monitor versions outside the
  incomplete catalogue endpoint; and
- treat fonts, SVG pages, and other adjacent assets as separate source records
  if the product later bundles them. Their status does not block ingestion of
  the text datasets reviewed here.

The full Arabic dumps and translation archives were not downloaded in this
review. Availability was checked from the provider records and response
headers; completeness, parsing, alignment, and checksum verification remain
builder acceptance evidence.
