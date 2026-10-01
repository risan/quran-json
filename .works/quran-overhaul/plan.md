# Plan: quran-json overhaul (data audit, cleanup, transliteration, new site)

Worktree: `.claude/worktrees/quran-overhaul`, branch `overhaul/quran-json-v5`, base `origin/main` b197d1ba.
Research behind every decision: `research-scripts.md`, `research-translations.md`,
`research-audio.md`, `research-stack.md`, `scout-cleanup.md` (all in this folder).

## Goals (owner's request, condensed)

1. Every published Arabic script is a valid, accepted text; fill the widely used gaps.
2. Cross-check the texts against independent sources and keep that check repeatable.
3. Remove unnecessary or confusing things (repo, README, docs).
4. Fix licence problems: nothing published under a restricted or unsourced claim.
5. More translations, and real transliterations.
6. Audio, per-ayah where possible.
7. A new site (docs + reader) with one design language: latest Astro, Vite, Tailwind,
   shadcn/ui, Oxlint, Oxfmt. Compact, easy to navigate.
8. A short README and short docs.

## Decisions

- **D1 Keep all 12 scripts.** Research found no wrong word in any of them; every difference
  against KFGQPC/independent copies is spelling convention. Paths stay. Display names change:
  `hafs-nastaliq` → "Indo-Pak (KFGQPC Nastaleeq)", `indopak` → "Indo-Pak (DigitalKhatt)".
  Fix the wrong descriptions ("not matching the printed edition", "shares 0 verses").
  Order in docs: uthmani, simple, simple-clean, kemenag, hafs-nastaliq, indopak, warsh, qalun,
  duri, then the niche uthmani-min, simple-min, simple-plain.
- **D2 Add `qpc-hafs`** (KFGQPC Uthmanic Hafs, Quranpedia mushaf 2) — the text Quran.com and
  KFGQPC apps use. Add the four specialist riwayat from Quranpedia (`shubah` mushaf 9, `bazzi` 5,
  `qunbul` 8, `susi` 10) only if their dumps carry a Hafs map like warsh/qalun/duri and pass
  the same tests; they are labelled "specialist readings". All must pass the font-coverage gate.
- **D3 One licence position for KFGQPC-derived text:** we rely on Quranpedia's published grant
  (it claims rights in the digitisation and dabt and grants republication with credit +
  version). KFGQPC's reachable terms cover its fonts and vector page copies, not a verse array.
  Written once in the docs; no contradictory "KFGQPC restricted" rows.
- **D4 Content may be corrected; paths never move.** Quranpedia's licence requires keeping
  copies current. New rule: a published path is never renamed or removed; its content may
  receive corrections from upstream, recorded in `/meta/qa.json` or the source version in
  `/meta/sources.json`. `_headers`: data paths get `public, max-age=86400,
  stale-while-revalidate=604800` instead of a one-year `immutable`; `_astro/*` stays immutable.
  Add `quran-json fetch --check` (no writes, exit 1 on upstream change) and a weekly CI job
  running it.
  *Migration (review r1 #5):* clients that cached a path under the old one-year `immutable`
  header may keep the old bytes until that entry expires. The site has been public since
  2026-09-20 (11 days), and every same-URL change in this release is benign for a stale
  reader: added `notice`/`license` fields, the Kemenag spacing fixes, three minor QuranEnc
  version bumps. We accept that staleness instead of adding revision URLs; the docs' changes
  policy says so. Text corrections after this release are logged in `/meta/qa.json` with the
  date, so a consumer can detect them.
- **D5 Licence fixes.** Manifest entries for every script get a `license` object (`id`, `url`,
  `attribution`, optional `notice`). Tanzil's notice goes into the manifest and into every
  chapter object of the six Tanzil scripts — both `text/{script}/chapters/{n}.json` and each
  element of the `text/{script}/quran.json` array (which stays an array) — as a `notice`
  string. `schemas/script.schema.json` and `schemas/manifest.schema.json` declare the new
  optional properties (they use `additionalProperties: false`); a test asserts the notice is
  present in every Tanzil chapter object and absent elsewhere. MP3Quran audio → `unknown` (no source for
  the "permits redistribution" claim). Islamic Network → licence URL on alquran.cloud terms, and
  `cors: false`. DigitalKhatt: the "shares 0 verses" justification is removed from code, provenance and docs
  (research shows letters agree with KFGQPC Nastaleeq in 99.2% of verses). The verdict stays
  `granted` on the repository's MIT licence, which its owner placed at the root of the repo
  that holds the file; research found no evidence the Indo-Pak file was copied from a
  restricted source (unlike the separate Madina file). `hafs-nastaliq` is presented as the
  primary Indo-Pak text and `indopak` as the alternative. Asking DigitalKhatt to confirm the
  file's provenance is an owner action, listed in the final report.
- **D6 Kemenag spacing slips** (~15 run-together words, e.g. 8:67 `عَزِيْزٌحَكِيْمٌ`): fix as
  `qa.py` corrections (insert the missing space only where the KFGQPC/Tanzil letters show a
  word boundary). Each correction fails the build if upstream fixes it. The text has no
  copyright (PMA 44/2016 Pasal 8(1)), so fixing it is allowed.
- **D7 Remove the frozen `dist/` tree and everything that exists only for it**: `dist/`,
  `build.py`, the `build` CLI command and its legacy options, legacy config
  (`EDITIONS`, `LANG_CODES`, `VERSE_LANGS`, `DEFAULT_LINK_BASE`, `LEGACY_VERSION`, path helpers,
  licence objects only they use), `data/quran.json`, `data/chapters/`, `data/editions/`,
  `data/meta/drift.json` content about them, `tests/test_parity.py`, legacy parts of
  `test_dataset.py`/`test_provenance.py`/`test_licensing.py`, the CI parity steps. npm 3.1.2
  and git tag `v3.1.2` keep serving the old files (jsDelivr npm and gh URLs resolve to them).
  Root `package.json` becomes a private tooling file (no `main`/`files`/`version`).
- **D8 Remove the `--include-unverified-licenses` profile** and the Kemenag translation and
  `latin` publishing paths (`PENDING_EDITIONS`, override fixtures/tests, build-site flag).
  `data/kemenag/quran.json` stays (it backs the `kemenag` script; its `latin` field becomes the
  comparison reference for the transliteration gate, never published).
- **D9 Remove dead research machinery**: `transliterations.py` (candidate importer, no
  publishing caller), `data/transliteration-candidates/`, `review.py`, the `licenses` command,
  `data/meta/licensing-review.json`. The rejected-source list survives as one short table in
  the docs ("Sources we checked and do not use") and in git history. `withheld` arrays stay in
  the public JSON (contract) and list only real withheld items (incomplete QuranEnc editions).
- **D10 Python stops writing HTML.** `web.py` keeps only the font-coverage gate (fontTools);
  it reads fonts from `site/public/fonts/` and writes the measured result to a path the caller
  gives, which `scripts/build-site.mjs` sets to `.build/fonts.json` — outside the data tree, so
  it is never assembled or published (test asserts its absence from `.build/assembled`).
  `web/` is deleted. All of D10 belongs to Track B (see Work split).
- **D11 Translations: 90 → 130.** Add the 36 complete QuranEnc editions that are on the website
  but not the API list (the `supplemental.json` route of the existing 8 for the 32 with a
  SQLite ZIP; the 4 API-only editions — `belarusian_krivtsov`, `chinese_suliman_modern`,
  `oromo_rwwad`, `zulu_adel` — need a new per-surah API ingest mode in `quranenc.py` using
  `FetchTask.gather`, keeping footnotes and version, with tests for partial and malformed
  responses; if that path cannot be made reliable, skip those 4 and say so), update
  `vietnamese_rwwad` 1.0.9, `moore_rwwad` 1.0.2, `korean_hamid` 1.0.4. Keep incomplete ones
  withheld (`circassian_rwwad`, `english_waleed`, `korean_rwwad`). Add four public-domain
  editions: Rodwell (en, d.1900), Kanzul Iman by Ahmed Raza Khan (ur, d.1921), Mahmud ul Hasan
  (ur, d.1920, footnote markers `[n]` stripped), Keyzer (nl, d.1868, stray mystic-letter
  characters fixed via `qa.py`). Each verified 6,236 non-empty verses.
- **D12 Transliteration: generate our own** from the Kemenag Arabic text (no copyright, so no
  third-party rights in the output). Module `quranjson/romanize.py`: tokenise → phoneme layer
  with Hafs reading rules (wasl, sun/moon letters, idgham, iqlab, madd, tanwin, ta marbuta,
  silent Uthmani letters, muqattaat, pause at verse end and at jim/qala/sala/mim waqf marks) →
  table-driven renderers. Publish three editions: `id-skb` (Indonesian SKB 1987 / Kemenag style),
  `en` (English with diacritics), `en-simple` (plain ASCII). Hand-code the Hafs exceptions
  (11:41 majreha, 12:11 ishmam, the four saktas 18:1 36:52 75:27 83:14, 41:44 tashil, 49:11,
  77:20, small sin/sad 2:245 7:69 52:37). Gates in tests: agreement with Kemenag `latin` ≥ 85%
  exact verses and CER ≤ 0.35%; golden tests per rule; snapshot of 50 sample verses per renderer.
  Licence of output: CC BY-SA 4.0 (the repo's), source credited to Kemenag. Starting point: the
  research prototype `scratchpad/translit/translit.py` + `evaluate.py`.
  Turkish, Bengali, Devanagari, Cyrillic renderers: not in this change (need a native reviewer).
  *Reading identity (review r1 #1):* each transliteration catalogue entry declares
  `reading: "hafs"` and `verse_ids: "hafs"`. The reader offers a transliteration only when the
  selected script's reading is Hafs and the chapter is joinable; it is never joined through
  `number_in_hafs` to Warsh/Qalun/Duri or other readings (translations still are). Regression
  test with Warsh 1:3 (مَلِكِ) vs Hafs 1:4 (Māliki).
  *Validation (review r1 #7):* (a) normalisation for the Kemenag gate is fixed in code and
  documented: NFC, drop `(…)` pause hints, lower-case, keep letters plus `'` and `‘`; (b) a
  disagreement report (`.build/romanize-report.md`, not published) classifies every
  non-matching verse by rule (reference typo, hamza-spacing style, mid-verse pause choice,
  generator gap), and the gate fails on any new verse in the "generator gap" class; (c) the
  phoneme layer is compared with the independent MIT `quranic-phonemizer` in the dev-only
  `crosscheck` tool (network, not CI), target phoneme error ≤ 0.5%; (d) English renderers
  are compared at consonant + vowel-length skeleton level with Tanzil `en.transliteration`
  (comparison only, fetched to `.cache/`, never committed); (e) golden tests for every rule and
  every hand-coded exception. No qualified human reviewer is available in this change, so each
  transliteration entry carries `review: "machine-generated; not yet reviewed by a qualified
  reader"` and the reader shows that note. Owner action: arrange a review.
- **D13 Audio.** Keep EveryAyah (per-ayah, CORS) as the default per-ayah host and Islamic
  Network as second per-ayah host; MP3Quran per-surah. Make sure every EveryAyah folder that
  answers 200 is listed. No timing import in this change.
  *Recording identity (review r1 #2):* every reciter entry in `/audio/reciters.json` gets
  `reading` (`hafs`, `warsh`, `qalun`, … or `unknown`) and, for `scope: "ayah"`, `verse_ids`
  (`hafs` for EveryAyah/Islamic Network Hafs folders). The reader builds a per-ayah URL only
  when the recording's reading and verse_ids equal the selected script's; the three EveryAyah
  Warsh folders stay unavailable for per-ayah playback (numbering unverified) but are listed.
  Per-surah files require only the same reading. Tests cover both mismatch directions.
- **D14 Cross-check is repeatable.** Add `quran-json crosscheck` (dev tool, not part of the
  build) that downloads independent witnesses into `.cache/` (KFGQPC files via fawazahmed0,
  Quranpedia, Tanzil) and prints, per script, three levels: raw bytes, vocalised (with the
  reviewed encoding-equivalence table), and letter skeleton. Each witness is listed with its
  ancestry (e.g. Quranpedia and the fawazahmed0 KFGQPC copies share KFGQPC as origin). Residual
  vocalised differences are written to `.cache/crosscheck/<script>.tsv`. Offline unit tests
  feed mutated verses (changed vowel, changed hamza seat, dropped letter, dropped word) and
  assert each is reported. Port from `scratchpad/scripts/run_all.sh`. Not in CI (network).
- **D15 New site.** `site/` = Astro 7.3.x (Vite 8) + `@astrojs/react` + React 19 + Tailwind 4 +
  shadcn/ui (Base UI default) + lucide. One `global.css` with shadcn tokens is shared by docs and
  reader. Fonts self-hosted from `site/public/fonts/` (Amiri, Scheherazade New, Noto Naskh Arabic,
  OFL texts beside them) + a variable UI font (Inter or Geist via Fontsource). Tooling in
  `site/`: `oxlint`, `oxfmt`, `prettier` + `prettier-plugin-astro` for `.astro` only,
  `astro check`, `vitest` for reader logic.
  - `/` docs: one compact page, sticky table of contents on desktop, sections: Quick start,
    Endpoints, Scripts ("Which script should I use?" list + table), Translations (searchable
    table, server-rendered), Transliteration, Audio, Sources & licences, Changes policy.
  - `/app/` reader: one React island (`client:only="react"`). Header shared with docs.
    Surah picker (Command palette, Ctrl/Cmd+K, search by number/name/meaning), verse list
    (Arabic + optional transliteration + one or more translations), settings Sheet (script, font,
    Arabic size, translations, transliteration, reciter), sticky audio bar (play verse, play from
    here, continuous, repeat, highlight + auto-scroll), deep links (`/app/#/2:255`, and the old
    `/app/#/1?s=...` form still parses), settings in localStorage, light/dark, correct RTL.
    Port the riwayah logic in `web/app/reader-core.js` (mapped verse ids, unjoinable chapters,
    per-ayah audio only for Hafs-numbered scripts) with its tests.
  - Compact: base spacing small, max content width ~1100px docs / ~800px reading column, no
    hero banner, no oversized headings.
  - Build: `scripts/build-site.mjs` keeps its interface (`npm run site`, `--no-cdn`) and its
    allowlist overlay (Astro may only add `index.html`, `app/index.html`, `_astro/*`,
    `fonts/*`, `favicon.svg`), reads data from `.build/data`.
- **D16 README ≤ ~150 lines**: what it is, quick start, endpoints, which script, translations /
  transliteration / audio in a few lines, licences table (short), changes policy, development.
  Everything else is deleted or lives on the docs page.
- **D17 Out of scope:** deploying (owner deploys by merging), npm publishing, `.works/` history,
  second-wave PD translations needing Flügel→Kufi maps or OCR, tafsir, audio timing, non-Latin
  transliterations.

## Public contract after the change

Unchanged paths: `/manifest.json`, `/chapters.json`, `/text/{script}/…`, `/translations/…`,
`/transliteration/…`, `/audio/reciters.json`, `/meta/sources.json`, `/meta/qa.json`.
Additive: new scripts, editions, transliterations, `license` objects, `notice` fields.
Removed (internal, undocumented): `/assets/*.css|js`, `/app/*.js|css`, `/app/fonts.json`,
`/assets/fonts/*` (moved to `/fonts/*`).

## Work split (revised after review r1 #9)

- **Track A — data (Python), in order:**
  - A1 cleanup: D7, D8, D9, D5, D4. Does not touch `web.py`, `web/`, fonts, the `web.*` calls
    in `cdn.py`, `scripts/build-site.mjs` or site tests. Tests green, ruff, mypy, and
    `npm run site -- --no-cdn` still builds.
  - A2 corpus: D1 names, D2, D6, D11, D13. 
  - A3 transliteration: D12 (new module + tests), wired into `cdn.py`.
  - A4 cross-check tool: D14.
- **Track B — site:** D15 and all of D10: owns `web.py`, the `web.*` calls in `cdn.py`,
  `web/` (deleted), fonts (moved to `site/public/fonts/`), `scripts/build-site.mjs`,
  `tests/test_web.py`, `tests/test_site_build.py`, tests in `site/`, and the CI site steps
  (`npm run lint`, `npm run check`, `npm test`, build). Before merge: the assembled build passes.
- **Track C — docs:** D16 README and the docs-page copy, after A and B merge.

Track B depends on A only through the JSON contract above and the `fonts.json` location.

## Verification

- `uv run pytest`, `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`,
  `uv run quran-json verify`.
- `npm ci --prefix site && npm run lint --prefix site && npm run check --prefix site &&
  npm test --prefix site && npm run site -- --no-cdn`, then `uv run pytest tests/test_site_build.py`.
- Browser check of the assembled site (desktop + 390px, light + dark): docs navigation, reader
  surah switch, settings, translation + transliteration display, per-ayah audio playing a real
  EveryAyah file, Warsh script disables per-ayah audio, deep link `#/2:255`.
- Codex (`sol`) reviews this plan, then the final diff.

## Review round 1 — 2026-10-01

Accepted: #1 transliteration reading identity (D12); #2 recording reading/verse_ids (D13);
#3 API ingest for 4 QuranEnc editions (D11); #4 Tanzil notice per chapter object + schemas
(D5); #7 validation gates, disagreement classes, machine-generated label (D12); #8 crosscheck
three levels, ancestry, mutation tests (D14); #9 ownership of fonts/web/build in Track B
(Work split); #10 fonts.json outside the data tree (D10).
Partly accepted: #5 cache migration — header change staged now; same-URL rewrites in this
release are benign and the site is 11 days old, so no revision URLs (D4 Migration).
Pushed back: #6 DigitalKhatt — MIT at the repo root is a clear grant by its owner; the
Tanzil-derived file is a different file; no evidence the Indo-Pak file is copied. The
disproven "0 shared verses" justification is removed; provenance confirmation is an owner
action (D5).
status: revised; session: fresh
