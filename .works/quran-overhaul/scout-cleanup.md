# Scout: quran-json (cleanup candidates)

## Repo rules
- No CLAUDE.md or AGENTS.md in the repo. Parent `/home/risan/projects/CLAUDE.md`: no `Co-Authored-By: Claude` or `Claude-Session:` trailer in commits. The session reminder says to add them; the project file says it overrides defaults.
- CI is the de facto rule set: `.github/workflows/ci.yml` runs `uv sync --locked`, `npm ci --prefix site`, `npm run check --prefix site`, `npm run site -- --no-cdn`, rebuild frozen tree, `git diff --exit-code -- dist/`, `uv run quran-json verify`, `uv run pytest`, `ruff check .`, `ruff format --check .`, `mypy`, `uv run quran-json cdn`.
- cdn.py docstring promise: "a published path is never renamed, removed, or rewritten" (`src/quranjson/cdn.py:1-45`, `wrangler.jsonc` comment). Immutable caching rests on it (`cdn.py:_HEADERS`).

## Map
Frozen dist/ machinery (exists only for dist/ or legacy generation):
- `dist/` (95 MB, 7513 tracked files: `quran*.json`, `chapters/`, `verses/`) - the frozen tree. `package.json` `"main": "dist/chapters/en/index.json"`, `"files": ["dist/", ...]`, `"version": "3.1.2"`.
- `src/quranjson/build.py` (277 lines, whole file): `RenderOptions`, `Sources` (`_load_legacy`, `_load_licensed`), `render_tree`, `build_tree`. Only importers: `__main__.py:11` and `tests/conftest.py:9`. `cdn.py` does NOT import it. `Sources._load_licensed` is only used by tests (see Pattern/Tests).
- `src/quranjson/__main__.py:22-55` - `build` command with `--out`, `--link-base`, `--version`, `--pretty`, `--legacy-verse-langs/--no-legacy-verse-langs`. Imports `build_tree` at line 11.
- `src/quranjson/config.py`: `DIST` (26), `LANG_CODES` (70), `VERSE_LANGS` (89), `LEGACY_VERSE_LANGS` (90), `DEFAULT_LINK_BASE` (92), `LEGACY_VERSION` (97), `chapter_list_path` (706), `edition_path` (711), `text_path` (716), `EDITIONS` (625-700, the 11 frozen editions), `REGISTERED = (*EDITIONS, *PENDING_EDITIONS)` (885). Licence objects used only by `EDITIONS`/text: `TANZIL_TRANSLATION` (123), `SAHEEH_INTERNATIONAL` (160), `SHIPPED_TEXT` (177), `QURAN_COM_METADATA` (501). (`QURANENC` 137 is also used by the live catalogue; keep.)
- `src/quranjson/sources.py:105-142` - `tasks()` creates fetch tasks for `data/quran.json` (110), `data/chapters/*` (117-130) and `data/editions/*` (132-141). `licensed_tasks()` docstring (line ~150) frames them as "the frozen tree".
- `tests/test_parity.py` (31 lines, whole file) - rebuild equals `dist/` bytes.
- `tests/test_provenance.py:10-11,40-63` - `FROZEN_TEXT_SHA256`, `test_frozen_text_snapshot_is_pinned`, `test_manifest_records_the_drift_that_was_not_applied` (reads `data/meta/drift.json`, which holds only `data/quran.json` drift). Lines 20-37 (manifest/hash tests) are generic; keep.
- `tests/conftest.py:13-18` - `legacy_tree` fixture.
- `tests/test_dataset.py` - whole file reads legacy: `sources` fixture (legacy `Sources`), `config.EDITIONS` loop (70), `config.DIST / "verses"` (104), `legacy_tree` tests (214-226). Read the file before deciding what is salvageable; the licensed-generation checks are in `tests/test_licensed.py`.
- `tests/test_licensing.py:20-43,100-140` - assert on `config.EDITIONS` (Saheeh restricted, transliteration, `published`), `SHIPPED_TEXT`. Lines 86+ test `review.CANDIDATES` (not dist).
- CI steps: `ci.yml` "rebuild the frozen tree" (`uv run quran-json build`) and "assert the frozen tree is byte-identical" (`git diff --exit-code -- dist/`).
- `package.json`: `main`, `files`, `version`, `keywords`, `homepage`, etc. are npm-package fields. Scripts `build` (`uv run quran-json build`), `site`, `cdn`, `deploy`, `licenses`, `test`, `lint` are repo tooling. `private: false`.
- `README.md` (682 lines): dist mentions at 26, 61, 279-300 ("Two generations"), 385, 396, 422-431 ("Known issue in the frozen tree"), 440, 446, 518, 525-557 ("Deprecating the old npm package"), 572, 584, 682 (licence line).
- `schemas/README.md:4-5` mentions the legacy dist. `src/quranjson/licensing.py:5-7` docstring mentions it.

Data snapshots (see Current behavior for readers).

Clutter:
- `.works/quran-corpus-expansion` 1.9 MB, 16 tracked files; `.works/quran-modernization` 456 KB, 27 tracked files (includes `site-evidence/*.json` and `capture-assembled.mjs`); `.works/quran-overhaul` 4 KB (this report, untracked). `.agents/` and `.codex/` do not exist. Only `.github/workflows/ci.yml` is tracked under `.github`.
- `src/quranjson/review.py` (709 lines) - see Current behavior.
- `data/transliteration-candidates/` (20 KB: `README.md`, `registry.json`) read by `src/quranjson/transliterations.py:51` (`REGISTRY_PATH`).
- `src/quranjson/transliterations.py` (556 lines) + `tests/test_transliterations.py` (207) - candidate importer; no caller in `cdn.py`/`__main__.py`.

## Current behavior
Unverified-licence profile (`--include-unverified-licenses`):
- CLI flag: `__main__.py:57-65`, passed at 73-78; withheld list printed 80-83.
- `cdn.py:417-446` `published_editions(include_unverified)` appends `PENDING_EDITIONS` non-transliteration (the Kemenag translation). `cdn.py:460-478` `published_transliterations(include_unverified)`. `cdn.py:481-` `build_site(include_unverified_licenses)`: 505-506, 511 (skips `licensing.require_publishable`), 547 (script gate: `allows_publication or include_unverified_licenses`).
- Withheld machinery: `cdn.py:616-621, 657-661, 772, 784-821` (`_withheld_entry`, `_catalogue_withheld_entries`, `_withheld_editions`), `cdn.py:859, 882-891`. These also render the `withheld` arrays in `/translations/index.json`, `/transliteration/index.json`, `/meta/sources.json` - a public contract. Dropping the flag does not remove them: Korean Rowwad is `availability: withheld` from `data/quranenc/supplemental.json` (`sources.py:270`; `tests/test_corpus_expansion.py:82-87`).
- `licensing.py:67-80` error message names the flag; `licensing.require_publishable` and `LicenseError` stay useful as a gate.
- `config.py:PENDING_EDITIONS` (864-883): `indonesian_kemenag` (kind kemenag, KEMENAG_TRANSLATION restricted) and `transliteration_kemenag` (KEMENAG_TRANSLITERATION unknown). With no flag, `cdn.py` never reads them except to list them as withheld. `KEMENAG_TRANSLATION` (365), `KEMENAG_TRANSLITERATION` (383), `_kemenag_translation_chapters` (cdn.py:213), `_transliteration_chapters` (239), `_edition_chapters` kemenag branch (253-260), `_edition_snapshot` (449-457) are then dead.
- `scripts/build-site.mjs:15,69-71,100-104` `--include-unverified-licenses` pass-through.
- Tests: `tests/conftest.py:28-34` `cdn_override_tree`; `tests/test_kemenag.py:52-54` (`unverified_tree`), 266-332 (override tests, the last ones also fixed by `include_unverified_licenses=True` at 310); `tests/test_contracts.py:166-190` `test_explicit_override_generated_transliteration_validates`; `tests/test_corpus_expansion.py:76-87` loops over both trees.
- Docs: `review.py:358`, `web/index.html:293-304` (withheld table), `site/src/pages/index.astro:148,265,313`, README.
- Kemenag caveat: `data/kemenag/quran.json` (4.0 MB) also backs the granted `kemenag` TEXT script (`cdn.py:172`, `_kemenag_chapters("text")` at 192-199; `config.KEMENAG_TEXT` granted 351). Keep the file and `sources.py:278-286`/`kemenag.py` for the text. Only the `translation` and `latin` fields become unused. `config.kemenag_path` (746). The transliteration candidate `ara-kemenag-latin` also points at it (`data/transliteration-candidates/registry.json:15`).

Snapshots and readers:
- `data/quran.json` (1.7 MB): only `config.text_path()` -> `build.Sources._load_legacy` (build.py:70), `sources.py:110`, `tests/test_provenance.py:40-63`. Unused after (1). `data/meta/drift.json` (4 KB) documents only this file's refused refresh.
- `data/chapters/*.json` (208 KB, 10 files): `config.chapter_list_path` -> `build.py:73`, `sources.py:124`. Unused after (1). Live chapter metadata is `data/tanzil/chapters.json` (`cdn.chapter_metadata`, cdn.py:138-156).
- `data/editions/*.json` (17 MB, 11 files): `config.edition_path` -> `build.py:72-75`, `sources.py:137`, `cdn._edition_snapshot` fallback (cdn.py:457, effectively unreachable: all remaining non-published editions are kemenag), `tests/test_dataset.py`, and `transliterations.py` candidate `ara-quran-la` (`registry.json:47`, `tests/test_transliterations.py:62-64`). So `data/editions/transliteration.json` (Tanzil English, restricted) has a second reader; the other 10 do not.
- `data/extra/` (8.9 MB), `data/quranenc/` (160 MB), `data/tanzil/` (9.2 MB), `data/digitalkhatt/` (1.8 MB), `data/quranpedia/` (8 MB), `data/audio/` (92 KB) - read by `cdn.py`/`audio.py`; keep. `data/meta/sources.json` (136 KB, 136 records) lists 11 `editions`, 10 `chapters`, 1 `quran.json` records that must be removed with their files (`tests/test_provenance.py:20-23` requires manifest == `sources.tasks()`); `quran-json verify` fails otherwise.
- `data/meta/licensing-review.json` (36 KB): written by `licenses --write` from `review.review_manifest()`, linked from `/meta/sources.json` (`cdn.py:891`). `data/meta/qa.json` published as `/meta/qa.json`.

review.py:
- `review.CANDIDATES` read by `__main__.py:103` (the `licenses` command) and `tests/test_licensing.py:86-125`; `review.review_manifest()` by `licenses --write` and `tests/test_licensing.py:120`. `review.py:699` reads `config.EXTRA_EDITIONS`. `pyproject.toml` has a `RUF001` per-file ignore for it. Mentions the flag at 358.

Site assembly today:
- `npm run site` = `scripts/build-site.mjs`: (1) `uv run quran-json cdn --out .build/data`; (2) `npm run build` in `site/` with `QURAN_JSON_SITE_DATA=.build/data`, Astro `outDir` `.build/site` (`site/astro.config.mjs`); (3) copy data to `.build/assembled`; (4) `overlayAstro()` (lines 40-70) allows only `index.html`, `app/index.html` and `_astro/*` to overwrite/add; (5) unless `--no-cdn`, copy to `cdn/`. `wrangler.jsonc` serves `./cdn`. `package.json` `cdn` script runs only the Python part, which yields the OLD HTML (not Astro).
- `cdn.py:build_site` (481-772) writes data plus web: `web.font_coverage`, `web.write_site_assets`, `web.write_docs` (cdn.py:751-767) and `_headers` (769).
- `web.py` (400 lines): copies `web/assets` and `web/app` into the output verbatim (`write_site_assets`, 202-207), writes `app/fonts.json` (`FONTS_JSON`, 60), renders `web/index.html` templates with `{{placeholders}}` into `/index.html` (`write_docs` 210-224, `docs_context` 249-385). `font_coverage` (132-199) measures font coverage with fontTools and fails the build if a script has no covering font (`tests/test_web.py:134`).
- HTML-only (Python): `web.write_docs`, `docs_context`, `_escape`, `_rows`, `_sample`, `_transliteration_lead`, `web/index.html` (394), `web/assets/{base.css,docs.css,site.js}`, `tests/test_web.py:59-100,140-146`. Astro's `index.astro` already overwrites `/index.html`, so these produce a page that `npm run site` discards.
- Needed by the new site: `manifest.json`, `chapters.json`, `translations/index.json`, `transliteration/index.json`, `audio/reciters.json` (read by `site/src/lib/catalog.ts:106-112`), `app/fonts.json` (`catalog.ts:111`, also read by `web/app/api.js:30`; its location `/app/fonts.json` is hard-coded in `site/src/pages/index.astro:304` and `web.FONTS_JSON`). Fonts `/assets/fonts/*.woff2` + `sources.json` + OFL txt files are referenced by `site/src/layouts/Base.astro:21-35` and pinned by `tests/test_web.py:40-57`. `/assets/favicon.svg` used by `Base.astro:20`. `_headers` includes `/assets/fonts/*` immutable rule.
- `site/` (292 KB): `src/layouts/Base.astro` (96), `src/lib/catalog.ts` (125), `src/pages/index.astro` (407), `src/pages/app/index.astro` (52, shell for the vanilla reader), `src/styles/global.css` (968), `astro.config.mjs`, `package.json` (astro 7.3.3, tailwind 4.3.3, playwright), `package-lock.json`, `tsconfig.json`. `package.json` scripts reference `../tests/site/homepage-regressions.mjs` and `../tests/reader/browser-regressions.mjs`.
- Vanilla reader `web/app/*` (api.js 74, app.css 787, app.js 877, audio.js 192, index.html 56, reader-core.js 249, store.js 72, ui.js 556). `tests/reader/reader-regressions.mjs` imports `../../web/app/reader-core.js` (pure logic: `alignsWithHafs`, `canJoinWithHafs`, `mergeChapter`, `nativeChapterCount`, `parseReaderHash`, `recitersForScript`, `scriptReadingIdentity`). That logic (Hafs/riwayat verse-id mapping) is the part a new reader would re-implement.
- `tests/test_site_build.py` (88): skips unless `.build/assembled` exists; asserts `index.html` ids, `/app/#/1?s=...` link, `app/*.js` imports, `app/app.css`. All tied to the old layout. `tests/test_cdn_site.py` (93) tests `cdn._HEADERS` only; keep.
- Python deps used only for web: `fonttools[woff]` (`web.py:36`).

## Pattern
- `src/quranjson/cdn.py:build_site` plus its `_check_shape`, `edition_url_key`, `_write_jsonl_dir` - keep as the single data generator; the new site reads its JSON via `site/src/lib/catalog.ts:loadCatalog` using `QURAN_JSON_SITE_DATA`.
- `scripts/build-site.mjs:overlayAstro` allowlist - mirror it (allowlisted files only, collisions with data paths error) so the new Astro output cannot shadow a data path.
- `tests/test_cdn_site.py` - mirror: pin a generated static file's contract by importing the constant, not by rendering.
- `Sources._load_licensed` (build.py:77-100) is NOT a pattern to keep; grep shows no non-test caller beyond `render_tree(content="licensed")`, and `render_tree` has no caller except `build_tree`.

## Tests
- Framework: pytest (`pyproject.toml [tool.pytest.ini_options]`, `testpaths = ["tests"]`, `addopts = "-q"`); Node `node:test` scripts for `tests/reader/*.mjs` and `tests/site/*.mjs` (not run in CI; Playwright ones need `npm run reader:browser:install` in `site/`).
- Command: `uv run pytest` (`ci.yml`, `package.json` `test`). Lint: `npm run lint` = `uv run ruff check . && uv run ruff format --check . && uv run mypy`. Site type-check: `npm run check --prefix site`.
- Closest tests: `tests/test_cdn_site.py` (headers), `tests/test_contracts.py` (JSON schemas in `schemas/` against `cdn_tree`), `tests/test_corpus_expansion.py`, `tests/test_licensed.py`.
- Fixtures: `cdn_tree` (session, `build_site(out)`) is used by nearly every surviving test; `legacy_tree` and `cdn_override_tree` are the ones to drop. `tests/test_build_env.py` guards that rendering never imports `_sqlite3` (Cloudflare build image) - keep.

## Contracts
Published paths (`cdn.py` module docstring 3-26, `build_site`), all unversioned, immutable-cached by `_HEADERS` except noted:
- `/manifest.json`, `/chapters.json`
- `/text/{script}/quran.json`, `/text/{script}/chapters/{1-114}.json` (scripts: `config.SCRIPT_IDS`: 6 Tanzil variants, kemenag, indopak, warsh, qalun, duri, hafs-nastaliq)
- `/translations/index.json` (60 s revalidate), `/translations/{code}-{slug}/quran.json`, `/translations/{code}-{slug}/chapters/{n}.json`
- `/transliteration/index.json` (60 s revalidate; currently `count: 0`), `/transliteration/{key}/...` (none published)
- `/audio/reciters.json` (3600 s cache)
- `/meta/sources.json`, `/meta/qa.json`
- `/_headers`: CORS `*`, GET/HEAD/OPTIONS.
- HTML/asset paths that are NOT data: `/`, `/app/` (+ `/app/*.js|css`, `/app/fonts.json`), `/assets/{base,docs}.css`, `/assets/site.js`, `/assets/favicon.svg`, `/assets/fonts/*`, `/_astro/*`. `/app/fonts.json` and `/assets/fonts/*` are consumed by external pages only if someone hot-links them; the README endpoint table (README:110-160) is the stated public list. Check README before moving them.
- Schemas: `schemas/*.schema.json` (6 + README) validated in `tests/test_contracts.py`; they describe the cdn tree, not dist.
- Legacy (outside this repo's deploy): npm `quran-json@3.1.2` `dist/...` via jsDelivr and git tag v3.1.2 stay available per `README.md:283,540`.
- Chapter `link` fields in `dist/chapters/*/index.json` hard-code `https://cdn.jsdelivr.net/npm/quran-json@3.1.2/dist/chapters/` (`config.py:92,97`); they point to the registry, not the repo.
- `package.json`: removing `files`/`main` is safe only if the owner confirms no further npm publish. README:553-557 says the new generation is deliberately not published to npm.

## Must not change
- Every published path above: `tests/test_contracts.py` (schemas), `tests/test_cdn_site.py` (headers), `tests/test_licensed.py`, `tests/test_corpus_expansion.py`, `tests/test_kemenag.py:186-233` (kemenag text script).
- `/translations/index.json` and `/meta/sources.json` `withheld` arrays: `tests/test_corpus_expansion.py:82-87` expects Korean Rowwad with reason `"1,955 empty"`; `tests/test_kemenag.py:236-263` expects Kemenag/Saheeh-type entries in `withheld` and `transliteration.status == "withheld"` by default.
- Manifest/snapshot consistency: `tests/test_provenance.py:20-37` and `quran-json verify` (`sources.verify_snapshots`). Removing a `data/` file without removing its `data/meta/sources.json` record fails both.
- Font bytes and OFL files: `tests/test_web.py:40-57`; `web.font_coverage` build-failure rule.
- No `_sqlite3` in render path: `tests/test_build_env.py`.

## Open decisions
- `data/editions/transliteration.json` (Tanzil English, restricted): needed by the `ara-quran-la` candidate in `transliterations.py`/`registry.json`/`tests/test_transliterations.py`. Delete it together with that candidate, or keep it as the one `data/editions` file?
- `transliterations.py`, `data/transliteration-candidates/`, `review.py`, `licenses` command: no publishing code path uses them. The repo does not say whether to keep them as research record. They touch Kemenag latin/Tanzil and `tests/test_licensing.py:86-125`, `tests/test_transliterations.py`.
- `PENDING_EDITIONS` / `REGISTERED` / `licensing.blocked`: dropping Kemenag translation/latin empties `PENDING_EDITIONS`. Whether `/translations/index.json` should keep listing them in `withheld` (public contract, `tests/test_kemenag.py:236-263`) is undecided. Also whether `transliteration_kemenag`'s `unknown` verdict stays documented in `/meta/sources.json` (`cdn.py:882-891`).
- `data/kemenag/quran.json` stays (text script is granted); whether to re-crawl/trim the `translation`/`latin` fields from the snapshot is undecided (it would change its hash in `sources.json`).
- `/app/fonts.json` and `/app/` URLs: keep the path for the new site or move to e.g. `/assets/fonts.json`; the repo does not say whether anyone consumes them.
- `quran-json cdn` currently emits an old-style HTML docs page and old app, and `npm run site` overlays Astro on top. After the redesign, should `cdn` write data only (drop `web.py` HTML) and `build-site.mjs` own HTML? `wrangler.jsonc` deploys `./cdn`, and README:633-660 describes the deploy; the actual Cloudflare build command is not in the repo (Unknown).
- `package.json` name/version `3.1.2`, `private: false`, `main`, `files`: keep as the npm identity or reduce to a private tooling file?
- `.works/` tracked planning docs (2.3 MB across 43 files): the repo has no rule on keeping them.
- Tests in `tests/test_dataset.py` mixing legacy and licensed checks: which assertions to port to `cdn_tree` is a judgement call.
