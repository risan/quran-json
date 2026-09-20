# Repository scout: quran-json

Date: 2026-09-20
Scope: read-only repository audit for the Quran corpus, Python publication pipeline, JSON contract, documentation, and reader.
Status: complete; no product, source data, generated CDN output, or tests were changed.

## State and local instructions

- Checkout: `/home/risan/projects/code/quran-json`, `main` at `5497c1be` (`origin/main` and `origin/HEAD` point to the same commit).
- No project or ancestor `AGENTS.md` was found. The repository's effective engineering constraints are in `pyproject.toml`: Python `>=3.12`, uv lockfile, strict mypy, Ruff lint/format (`pyproject.toml:1-57`).
- Before this report, the product tree was clean. The shared audit directory already contained `brief.md` and `research-architecture.md`; this file is the only file owned by this scout. `cdn/`, `.venv/`, and caches are ignored (`.gitignore:5-20`).
- The root package and the Python package intentionally have different versions: npm remains `3.1.2` with `main` at the frozen `dist/` tree, while the Python build metadata is `4.0.0` (`package.json:1-40`, `pyproject.toml:1-29`).

## Corpus inventory

### Arabic text and script identity

The current pipeline defines ten publishable script IDs (`src/quranjson/config.py:202-240,362-384`):

| IDs | Shape and source | Verse identity |
|---|---|---|
| `uthmani`, `uthmani-min`, `simple`, `simple-plain`, `simple-min`, `simple-clean` | Six Tanzil snapshots, CC-BY 3.0 verbatim; Uthmani/Imlaei orthography and mark variants | Hafs/Kufi numbering, 6,236 verses each |
| `kemenag` | Qur'an Kemenag/LPMQ Mushaf Standar Indonesia UTF-8 text; its publishing regulation is recorded as the text grant (`config.py:266-290`) | Hafs numbering, 6,236; Indonesian waqf signs |
| `indopak` | DigitalKhatt's MIT-licensed Indo-Pak typesetting (`config.py:324-339`); parser removes page/marker controls and preserves text marks | `own`; 6,236 verses, but Al-Fatiha labels diverge because the basmala is unnumbered (`config.py:259-263,389-400`) |
| `warsh`, `qalun` | Qur'anpedia.net dumps under a dated data licence requiring source credit and dump version (`config.py:341-360`) | `mapped`; Nafiʿ count, 6,214 verses each, with `number_in_hafs` mappings |

The six Tanzil files and metadata are committed under `data/tanzil/`; Kemenag, DigitalKhatt, and Qur'anpedia snapshots are under `data/kemenag/`, `data/digitalkhatt/`, and `data/quranpedia/`. The output keeps the axes separate in prose and manifest data: riwayah, rasm/orthography, and print layout are not interchangeable (`README.md:115-150`). Page geometry is absent by design; no 13/15/16-line, ayet-berkenar, page, or line-break resource can be represented by the current verse arrays (`README.md:130-140`).

The reader must use `number_in_hafs` for Warsh/Qalun and cannot align translations by a constant offset. The implementation joins mapped verses through the manifest identity and disables translation beside Indo-Pak Al-Fatiha, whose verse labels do not share the Hafs keys (`web/app/app.js:122-166,258-301`; `tests/test_riwayat.py:73-115`; `tests/test_web.py:148-181`).

### Translation editions, languages, and provenance

- `data/quranenc/catalogue.json` contains 75 QuranEnc editions, each with `key`, ISO-like `lang`, direction, version, title, description, and database URL (`data/quranenc/catalogue.json:1-28`; `src/quranjson/quranenc.py:1-10`). The committed `data/quranenc/` directory has the catalogue plus 75 snapshots.
- `config.EXTRA_EDITIONS` adds eight granted editions: Talal Itani's two ClearQuran archives, four public-domain English editions (Pickthall, Yusuf Ali, Palmer, Sale), and two public-domain Russian editions (Sablukov and Krachkovsky) (`src/quranjson/config.py:688-758`).
- The gated current build therefore publishes 83 granted translations (75 + 8). The explicit `--include-unverified-licenses` build adds Kemenag's Indonesian translation, producing the published-site count of 84 (`src/quranjson/cdn.py:314-343,401-508`; `src/quranjson/config.py:761-787`). The Kemenag translation remains `restricted`, and the Kemenag Latin field remains `unknown`; the override does not relabel either (`tests/test_kemenag.py:171-183,238-334`).
- The 57 language codes in the current override catalogue are: `aa, ak, am, as, az, bs, ceb, de, en, es, fa, ff, fr, gu, ha, hi, hr, id, ja, km, kn, ku, ky, ln, lt, mdh, mk, ml, mos, nl, nqo, om, pa, ps, pt, rn, ro, rw, si, so, sq, sr, sv, sw, ta, te, tg, th, tl, tr, ug, ur, uz, vi, yo, zh`. English has nine editions in the generated catalogue; Russian has two; the remaining languages are represented by one or more QuranEnc editions. Language and direction are taken from the QuranEnc catalogue rather than invented by the reader (`src/quranjson/cdn.py:464-497,550-578`).
- The frozen legacy inputs under `data/editions/` are only ten language keys plus the old `transliteration` snapshot (`bn`, `en`, `es`, `fr`, `id`, `ru`, `sv`, `tr`, `ur`, `zh`, transliteration). Most are restricted by Tanzil terms and stay in `dist/` for URL compatibility; the licence registry deliberately prevents them from entering the current build (`src/quranjson/config.py:530-610`; `src/quranjson/licensing.py:1-95`).
- `data/meta/sources.json` has 121 snapshot records with URL, source, licence text/status, SHA-256, byte count, and revision; current records are 100 granted, 19 restricted, and 2 unknown. `data/meta/licensing-review.json` has 36 reviewed source records, including 11 transliteration candidates. `sources.verify_snapshots()` checks hashes and byte counts (`src/quranjson/sources.py:1-60`; `tests/test_provenance.py:20-63`).
- Translation chapter payloads deliberately contain only `id`, `translation`, and optional `footnotes`; Arabic is fetched from `/text/` once and is not copied into every edition (`src/quranjson/cdn.py:244-277`; `tests/test_dataset.py:112-124`).

### Transliteration

- The legacy `dist/` generation carries Tanzil's `quran_transliteration.json`, but Tanzil's translation terms are restricted. Current `config.PENDING_EDITIONS` records Kemenag's authored Latin field separately from the granted mushaf text (`src/quranjson/config.py:292-322,761-787`).
- The default gated site publishes no transliteration but always writes `/transliteration/index.json` with withheld candidates. The override site publishes one Kemenag edition and reports its real `unknown` status (`src/quranjson/cdn.py:356-374,510-548`; `tests/test_kemenag.py:249-334`).
- The repository review records no broadly licensed, ready-to-publish transliteration. It lists Tanzil, Islamic Bulletin, Pickthall's bundled text, QUL/Tarteel, QuranPhoneticSearch, fawazahmed0 transliteration slugs, Quran.com, Kemenag, and self-generated Wikisource as separate candidates and blockers (`README.md:454-498`; `data/meta/licensing-review.json`).
- “Language-specific transliteration” is not represented as a generic Arabic script property today: a published transliteration is a separate Hafs-keyed edition with its own author, source, status, and chapter files. A future model must retain this distinction and should not infer an Indonesian, Urdu, or Turkish transliteration merely from a translation language.

### Fonts and audio

- Three bundled OFL 1.1 Arabic fonts are measured at build time: Amiri, Scheherazade New, and Noto Naskh Arabic (`web/assets/fonts/sources.json:1-55`; `src/quranjson/web.py:110-195`). The generated coverage report records default/usable fonts and missing codepoints per script; Amiri lacks `U+08D6` in Kemenag and ten codepoints including `U+089C` in Indo-Pak. The site fails if no bundled font covers a script (`tests/test_web.py:101-137`).
- Audio is URL-template metadata, never audio bytes. The three hosts are EveryAyah (surah-relative ayah), MP3Quran (whole surah), and Islamic Network (global ayah and surah); host indexing and padding are machine-readable (`src/quranjson/audio.py:1-76,175-205`). The current generated index has 595 recitations, and tests pin host counts, URL schemes, completeness, ayah totals, and licence-status recording (`tests/test_audio.py:23-80`).

## Public data and build architecture

The repository has two intentionally different trees:

1. `quran-json build` renders the frozen npm/jsDelivr-compatible `dist/` tree from legacy snapshots. `build.render_tree` preserves old per-language and per-verse shapes and `tests/test_parity.py` requires byte identity (`src/quranjson/build.py:1-18,155-271`; `tests/test_parity.py:19-31`). Tracked `dist/` currently has 7,513 JSON files and 81.8 MB.
2. `quran-json cdn` renders the ignored `cdn/` tree from the licensed/current snapshots. It writes shared `chapters.json`, `/text/{script}/quran.json` plus 114 chapter files, translation/transliteration catalogues plus whole/chapter files, `manifest.json`, provenance/QA metadata, audio, fonts, docs, app assets, and `_headers` (`src/quranjson/cdn.py:1-22,435-635`).

The current wire contract is unversioned and add-only: `/manifest.json`, `/chapters.json`, `/text/{script}/...`, `/translations/{code}-{slug}/...`, `/transliteration/{key}/...`, `/audio/reciters.json`, and `/meta/{sources,qa}.json` (`README.md:94-113`). Existing paths are cached immutable for one year, so rewriting or renaming an existing path is a compatibility break; adding a new script/edition/chapter is allowed (`README.md:245-255`; `src/quranjson/cdn.py:71-92`).

Important generated counts measured locally:

| Output | Files | Bytes | Conditions |
|---|---:|---:|---|
| Tracked `dist/` | 7,513 | 81,807,518 | Frozen 3.1.2 parity tree |
| Default gated `cdn/` render | 10,723 | 321,244,187 | 10 scripts, 83 granted translations, no transliteration; 11 registered editions withheld |
| Existing ignored local `cdn/` | 10,953 | 325,884,653 | Last generated with `--include-unverified-licenses`; 84 translations + 1 Kemenag transliteration |

The README’s 10,359-file/10,704-file figures and 330 MB current-site figure are historical relative to the measured artifacts (`README.md:25-39,264-274`). The ignored `cdn/` is not a trustworthy committed baseline; CI and Cloudflare regenerate it. Before any migration, record a clean default and production-override manifest/file list separately.

The Python build holds complete chapter lists and writes each edition serially. `build.render_tree` builds `quran_files`, then a second merged structure for transliteration and verse output (`src/quranjson/build.py:155-250`); `cdn.build_site` materializes each script and edition as a whole file plus 114 chapter files (`src/quranjson/cdn.py:307-311,418-471`). This is clear and reproducible, but the duplicated in-memory structures and thousands of individual writes are the primary backend efficiency seam if larger corpus growth becomes material. Any optimization must retain exact `dist/` bytes and current chapter/whole-file paths.

Provenance is strong: fetchers commit normalized snapshots and record drift rather than silently overwriting changes (`src/quranjson/sources.py:287-340`; `data/meta/drift.json`). Rendering does not import SQLite, which is required by the Cloudflare build image and is protected by a poisoned-interpreter test (`tests/test_build_env.py:1-59`).

## Documentation, deployment, and reader

- Root `web/index.html` is a long generated documentation page with quickstart, endpoint table, ten-script/font tables, 84-edition catalogue, withheld/licensing section, transliteration, audio, compatibility, and attribution sections (`web/index.html:37-382`). `web.py` substitutes values from the generated manifest/catalogues and copies `web/assets` and `web/app`; placeholder and link tests enforce this coupling (`src/quranjson/web.py:198-220,245-379`; `tests/test_web.py:59-100`).
- The reader is a no-build vanilla ES-module app. `web/app/index.html` has a shell, toolbar, status region, view, popover, audio element/player, footer, and noscript docs link (`web/app/index.html:1-56`). `api.js` memoizes in-flight JSON promises and exposes metadata/chapter routes (`web/app/api.js:1-35`); `store.js` persists theme/preferences in localStorage (`web/app/store.js:1-72`).
- Reader startup fetches manifest, chapters, translation/transliteration catalogues, and font coverage in parallel; reciters are lazy. Chapter selection fetches only the chosen Arabic, transliteration, and up to three translation chapter files in parallel, with a monotonic token preventing late responses from replacing newer navigation (`web/app/app.js:258-321,585-640`). Hash URLs preserve chapter/verse, script, translation, transliteration, reciter, and font state (`web/app/app.js:1-107`).
- Audio safety is explicit: per-ayah reciters are hidden/refused for Warsh/Qalun because those hosts use Hafs numbering; whole-surah reciters remain available (`web/app/audio.js:1-17,51-123`; `web/app/ui.js:431-480`).
- There are no Astro, Vue, React, Tailwind, TypeScript, or browser-test dependencies in the tracked project. The root npm package is the legacy dataset package, not a frontend workspace (`package.json:24-40`; `rg --files` inventory). A future Astro site must use an isolated output/staging directory so its default `dist/` cannot overwrite npm’s frozen `dist/`.
- `wrangler.jsonc` serves `./cdn` as Workers static assets with `workers_dev: true` and preview URLs disabled (`wrangler.jsonc:1-19`). CI runs the gated build without the override (`.github/workflows/ci.yml:20-42`), while README’s production Cloudflare command includes `--include-unverified-licenses` (`README.md:28-39,563-580`). That rights-sensitive difference is currently external to tracked configuration and should be made explicit before implementation or deployment automation changes.

## Tests and baseline

The suite has 120 tests and passed in 25.39 seconds with a writable cache:

```text
UV_CACHE_DIR=/tmp/quran-json-uv-cache uv run pytest
120 passed in 25.39s
UV_CACHE_DIR=/tmp/quran-json-uv-cache uv run ruff check .
UV_CACHE_DIR=/tmp/quran-json-uv-cache uv run ruff format --check .
UV_CACHE_DIR=/tmp/quran-json-uv-cache uv run mypy
All checks passed; 36 files formatted; Success: no issues found in 19 source files
```

The first pytest attempt without `UV_CACHE_DIR` was not a test failure: uv could not write its shared `/home/risan/.cache/uv` on the managed read-only filesystem. The suite covers source reshaping/drift, legacy parity, current shapes/counts, licences/provenance/QA, riwayah/Kemenag/Indo-Pak fingerprints, audio templates, font coverage, docs links/placeholders, and SQLite-free rendering (`tests/conftest.py:1-26`; test files). It does not currently run a browser, accessibility, mobile-layout, or audio-playback test; `tests/test_web.py:91-100` only verifies that imported JavaScript modules exist.

## Evidence-backed gaps and improvement seams

These are audit findings, not an authorization to ingest or publish new content.

1. **Resolve current-site truth before migration.** Regenerate and record separate gated and override manifests. Update the stale README counts, and make the production build flag a tracked, reviewed input. CI currently proves the gated site, whereas production documentation says the override site is deployed (`.github/workflows/ci.yml:39-42`; `README.md:28-39`).
2. **Separate immutable payloads from mutable catalogues.** `_headers` currently applies one-year immutable caching to `/translations/*` and `/transliteration/*`, including `index.json` (`src/quranjson/cdn.py:71-92`; `tests/test_cdn_site.py:18-29`). Edition additions can leave consumers with a stale catalogue for a year. Preserve immutable edition paths but give catalogue indexes an explicit revalidation policy or publish a short-lived discovery document outside those wildcards; test the chosen rule against Cloudflare behavior.
3. **Add explicit JSON schemas and generated-tree validation.** The current tests are strong semantic checks but are handwritten and selective; there is no tracked `schemas/` directory. Add schemas or a boundary validator for manifests, catalogues, chapters, verses, footnotes, mapped-Hafs arrays, language direction, and source records, then walk every generated JSON artifact. Keep current wire keys and old paths unchanged.
4. **Add browser-level reader evidence before a framework port.** Preserve hash routes/localStorage keys, chapter-first loading, three-translation cap, stale-response token, Arabic `dir/lang`, font eligibility, copy/link actions, keyboard behavior, and audio/riwayah safety. Exercise these in a real browser at narrow mobile width and with failed/malformed responses before replacing the vanilla app; static import/link checks cannot prove those behaviors.
5. **Measure build growth before optimizing or changing directories.** The current site is already 10,723 gated files and ~321 MB, close enough to the 20,000-file Worker limit that duplicating a versioned tree would be expensive. First profile JSON serialization and repeated structures; then consider streaming/atomic writes or staging, while preserving exact legacy output and collision checks (`src/quranjson/build.py:155-250`; `src/quranjson/cdn.py:418-471`).
6. **Treat corpus additions as typed, rights-gated editions.** The main missing Arabic families are additional riwayat/qira'at beyond Hafs, Warsh, and Qalun, plus any genuine text editions for Turkish/Ottoman and mainstream Indo-Pak traditions. The repository evidence says many apparent “scripts” are print layouts and that common KFGQPC/QuranWBW/Diyanet sources are restricted or unknown (`README.md:130-150,431-452`). Do not add a relabelled Hafs or a page layout as a text script.
7. **Prioritize translation gaps by adoption and rights evidence.** The current 57-language/84-edition override already covers many languages. The clearest repo-recorded gaps are verse-numbered Bengali (Girish Chandra Sen) and Malay (Tarjuman al-Mustafid) public-domain editions, which still need extraction and quality review (`README.md:288-301`). Any other “widely adopted” shortlist requires the separate source/research evidence and an explicit redistribution grant; availability in an API is not enough.
8. **Transliteration needs a source decision, not a language flag.** The default build intentionally publishes none. The cheapest reviewed path is permission for Tanzil’s machine-readable romanisation; the independent path is a new grapheme-to-phoneme generator from a compatible Arabic source plus a 6,236-verse review. Kemenag Latin remains an unverified authored transformation (`README.md:454-498`; `data/meta/licensing-review.json`).
9. **Astro/Vue/React/Tailwind is a site boundary choice.** The existing data pipeline should remain authoritative. If the requested frontend modernization proceeds, isolate a static Astro site output from npm `dist/`, keep docs server-rendered/static, and migrate the reader as one client island only after browser parity. Vue is the lower-translation-cost fit for the current template/DOM reader; retaining the vanilla reader with TypeScript is a viable lower-risk baseline. This is consistent with the architecture research artifact, not a current repository capability.

## Proposed implementation ownership seams

| Workstream | Primary paths | Contract to preserve |
|---|---|---|
| Corpus/data and backend | `data/**`; `src/quranjson/{config,build,cdn,sources,licensing,qa,tanzil,quranenc,kemenag,digitalkhatt,quranpedia,audio}.py`; dataset/provenance/licensing/riwayah/audio tests | Snapshot hashes/licences; ten scripts and identity metadata; current catalogues; all existing `/text`, `/translations`, `/transliteration`, `/audio`, `/meta` paths; frozen `dist/` bytes |
| Documentation and static site | `web/index.html`; `web/assets/**`; `src/quranjson/web.py`; `wrangler.jsonc`; CI/deploy docs | Generated counts and rows come from Python-published structures; fonts/licences and internal links resolve; deployment flag is explicit; output does not touch npm `dist/` |
| Reader | `web/app/{index.html,app.js,api.js,store.js,ui.js,audio.js,app.css}` plus browser tests | Existing hash URLs/localStorage keys; chapter-first requests; mapped identities; translation direction/footnotes; font coverage; audio host semantics and Nafi safety |
| Documentation/compatibility handoff | `README.md`, `.works/quran-modernization/*.md`, release/CI checks | Distinguish frozen legacy from current site; record measured file/byte counts; state gated vs override rights; preserve consumer migration examples |

Recommended order: freeze current public path/hash/byte and request baselines; settle the rights-backed corpus shortlist; fix catalog cache/deployment truth; add schemas and browser tests; then build an isolated Astro site or a measured vanilla/TypeScript refresh behind a comparison path. Do not combine corpus ingestion, public URL migration, and framework replacement into one unverified change.
