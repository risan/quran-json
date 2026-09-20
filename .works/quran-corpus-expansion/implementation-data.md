# Arabic and translation data implementation

Status: complete locally; no remote publication or deployment performed.

## Baseline

The pre-extension snapshot is recorded in [baseline.json](baseline.json), captured
2026-09-20. The safe CDN tree had 10,725 files, 10 scripts, 83 translations across
57 languages, and no published transliterations. Existing payload hashes were captured
for the whole tree; representative contracts were:

- cdn/manifest.json: 4,613 bytes,
  0afcd3467274663cbe4683ab38db523c0e54c9aaa6151ee6841119bf1ba80b53
- cdn/text/uthmani/quran.json:
  fb862d48e8ff27c56fc9fea859bca1c96b93d18d46b442e5611b001344164ca4
- cdn/translations/en-pickthall/quran.json:
  4860928bde0e064838774b382f1cdbce92918c960a83136f6369e5b3cd675e76
- cdn/translations/index.json:
  a2fb3cb20f98503bd4d4c426fd16f28e8299785ad47e0d3e2406a23d5b3a54cd

The frozen dist/ tree was rendered to a disposable directory and compared with
diff -rq; it is byte-identical and remains untouched.

## Imported sources

The source registry now covers 132 snapshots. The canonical QuranEnc catalogue remains
75 entries. data/quranenc/supplemental.json manually registers the eight requested
official bulk editions, with browse URL, terms URL, version, archive size and SHA-256:

| ID | Snapshot | Source archive SHA-256 | Result |
|---|---|---|---|
| bengali_zakaria | data/quranenc/bengali_zakaria.json | 3fa5450da0fd89de6988763035eecc86b9bb3f38216539f2517d9f089fe5bd8e | published |
| bengali_rwwad | data/quranenc/bengali_rwwad.json | 0e5ad67ff327c50a0014351436fff85e344247d38c4b447a3a2ae9f7c235ae5b | published |
| malay_basumayyah | data/quranenc/malay_basumayyah.json | b35aacd919a5a21ac96059d587ee47edb8e18afc79334d3fb97dc8e197c4ff63 | published |
| russian_rwwad | data/quranenc/russian_rwwad.json | 210c2049df6fb20c44fc980c3ae0b52856794722d050b5e9cdbcf9b8cf4d9123 | published |
| korean_hamid | data/quranenc/korean_hamid.json | 138e9899d4e03aeebe7d1943682babb0ed9ecf425b9c24f669b6a40627990752 | published |
| korean_rwwad | data/quranenc/korean_rwwad.json | 7f4447a96e36903e0b02b8ec15915ca8238c8ce871cc9ef6acbe83fded5d15ab | withheld |
| italian_rwwad | data/quranenc/italian_rwwad.json | 80defdf474dba341957f563e217ef60b1fa1b529213f263c02c2224792b9cc26 | published |
| ukrainian_yakubovych | data/quranenc/ukrainian_yakubovych.json | 7f5dc69ca86a80761ccf9123be47334bd67dad7c13e3fd0fb38c10dc8ae35b54 | published |

Every archive was compared against its SQLite rows and validated as 114 chapters and
6,236 sequential Hafs IDs, retaining source footnotes. Korean Rowwad v1.0.11 has
1,955 empty rows in surahs 14–35, confirmed by the official API and SQLite archive.
It therefore remains a granted but technically incomplete candidate. The explicit
unverified-rights override cannot publish it, and its reason is present in both
catalogue profiles.

The two Quranpedia additions are added locally as independent text snapshots:

- data/quranpedia/duri.json: mushaf 6, 6,218 native rows,
  snapshot SHA-256 d4734c7176dd666530c066e638d602669be6ac016b3da699fff599cb746a89ac;
  source archive SHA-256
  f6024036b0040afea6af7973abd78b883ab2a0837ae72f6360b69e597c53999a.
- data/quranpedia/hafs-nastaliq.json: mushaf 3, 6,236 native rows,
  snapshot SHA-256 7276ed5158d314d4f323545e24ff2912d411a3ac4e3c6bdc6ae3ffcf2c3a3c67;
  source archive SHA-256
  fbec857dd613946604fd4c004d7322778ecf1c058c46080e30702e9bf9959b02.

The Nastaliq parser requires every number_in_hafs value to be exactly its native
verse ID. It is a distinct Quranpedia digital edition and does not replace indopak
or claim printed-edition compatibility. Duri validates every per-verse map, allows
legitimate repeated Hafs IDs, and records its exact chapter-1 exception
[2,3,4,5,6,7,7]: Hafs 1 is absent because the source bismillah is unnumbered,
and Hafs 7 occurs twice. The generated Duri descriptor carries reading identity,
mapped audio with per_ayah false, and an unnumbered chapter-1 bismillah furniture
entry. The exact source bismillah text is retained in that entry and in
meta/sources.json.

Native per-chapter counts are included in the manifest for mapped readings; readers
can therefore accept Duri 9:130 and reject an incorrect 2:286 bound without fetching
the whole corpus.

## Publication result

The canonical npm run site build (safe profile, with audio) produced 11,760 files:
12 scripts, 90 translations across 62 languages, and 0 transliterations. Its manifest
SHA-256 is c1cd7b0dd8f2d864e6135de53a2c88357c288260fe22ed2377aac4dcb99f3d50.
The explicit local no-audio override render produced 11,988 files, 12 scripts, 91
translations, and 1 transliteration. It still withheld korean_rwwad; the override
only changes rights gates. The same raw CDN render with the optional audio index is
11,989 files.

All 1,150 existing text payloads and 9,545 existing translation payloads matched their
baseline hashes. New output was additive: the old paths were not rewritten. The
assembled Astro tree and root cdn/ are byte-identical after npm run site.

## Validation

The import/build gates are:

- quranenc.validate_translation: exact 1..114 chapters, canonical per-chapter counts,
  sequential IDs, nonempty text for publishable editions, and preserved footnotes.
- quranenc.validate_catalogue and merged_catalogue: supplemental metadata, explicit
  availability reasons, allow_empty only for withheld entries, and cross-catalogue
  duplicate rejection.
- quranpedia.parse_dump: source mushaf identity/version, 114 chapters, source-derived
  count, nonempty text, mapping order/range/coverage, exact Duri exception, and exact
  Nastaliq native IDs.
- sources.fetch_all: raw archive hash and byte-size checks before parsing or replacing
  a snapshot; provenance records both parsed snapshot and raw source identities.
- JSON schemas cover script reading/audio identity, native chapter counts, mapping
  exceptions, chapter furniture, and withheld translation reasons.

Validation completed locally:

- uv run pytest -q: 151 passed.
- uv run ruff check src tests: passed.
- uv run ruff format --check src tests: passed.
- uv run mypy src: passed.
- npm run site: passed; Astro generated static pages and assembled them with the
  safe Python data tree.
- pytest -q tests/test_site_build.py tests/test_contracts.py tests/test_corpus_expansion.py:
  passed; diff -rq .build/assembled cdn is clean.
- git diff --check: passed.

No remote source was contacted during the final render, no deployment was run, and no
commit or push was made.
