# Static site implementation

Status: implemented locally; no commit, push, or deployment.

This slice keeps Python as the data authority and adds an isolated Astro/Tailwind build for the
documentation page and reader shell. The build stages generated data and Astro output under
`.build/`, then overlays only the two HTML pages and `_astro/` assets into the assembled tree.
It does not write the frozen `dist/` tree.

## Changes

- `site/package.json:1-25` and `site/package-lock.json` pin Astro 7.3.3, Tailwind 4.3.3,
  the Tailwind Vite plugin, the Astro checker, and Playwright 1.63.0 as a development-only
  browser QA dependency. The `reader:browser:install` and `reader:browser` scripts keep browser
  setup out of the published runtime. `site/astro.config.mjs:1-16` emits static
  pages to `.build/site/`; `site/src/lib/catalog.ts:1-125` reads manifest, catalogues, coverage, and
  chapter metadata from `QURAN_JSON_SITE_DATA`, so the page has no hand-maintained edition list.
- `site/src/pages/index.astro:1-321` renders profile-derived counts, rights status, script
  inventory, generated translation/transliteration catalogues, source links, endpoint examples,
  font coverage, audio references, compatibility notes, and preserved anchors (`quickstart`,
  `endpoints`, `scripts`, `translations`, `transliteration`, `audio`, `fonts`, `compatibility`,
  `licensing`, and `attribution`). The read/fetch/browse tasks are static HTML. The examples join
  translation rows by verse `id`; mapped readings use `number_in_hafs`.
- `site/src/layouts/Base.astro:12-96` provides semantic navigation, a no-JavaScript `<details>`
  mobile menu, skip link, theme control, reader link, and same-origin bundled font faces.
  `site/src/styles/global.css:1-663` supplies the responsive paper/ink design, readable widths,
  dark theme, visible focus, reduced-motion handling, code/table styles, and keyboard-safe links.
  `site/src/pages/app/index.astro` preserves the vanilla reader's existing route, IDs, module
  path, and asset contract; reader behavior remains in `web/app/`.
- `scripts/build-site.mjs:44-105` is the build seam. It runs `uv run quran-json cdn --out
  .build/data` with the safe default unless `--include-unverified-licenses` is explicit, runs
  `npm run build` against that generated tree, rejects unallowlisted Astro output and collisions
  with data paths, assembles the result, and copies to `cdn/` only when `--no-cdn` is absent.
  The explicit override retains restricted/unknown catalogue status; it never changes the data
  publisher's gate.
- `tests/test_site_build.py:1-90` runs after an assembled build and checks generated counts,
  all legacy anchors, chapter-derived reader routing, safe transliteration absence, manifest and
  catalogue JSON pointers, HTML/CSS local links, bundled font presence, and every reader module's
  relative imports. It skips when no assembled build exists, while CI builds first and therefore
  executes these checks.
- `tests/reader/browser-regressions.mjs:1-33` resolves the site-local Playwright module after
  `npm ci --prefix site`, while retaining an explicit module override for external harnesses;
  its documented browser cache uses Playwright's normal user location rather than a temporary
  repository path.
- `.github/workflows/ci.yml:20-57` installs Node 22.12.0 and the locked site dependencies,
  runs `astro check`, builds the assembled safe profile before Python tests, and retains the
  frozen `dist/` byte check. `README.md:7-18,73-79,572-600` documents the short onboarding,
  split Python/Astro build,
  safe and explicit profiles, assembled preview, and the post-build test command.

## Verification

Passed locally:

- `NPM_CONFIG_CACHE=/tmp/quran-json-npm-cache npm ci --prefix site` — 291 packages, no audit findings.
- `ASTRO_TELEMETRY_DISABLED=1 XDG_CONFIG_HOME=/tmp/quran-json-astro-config NPM_CONFIG_CACHE=/tmp/quran-json-npm-cache npm run check --prefix site` — 0 errors, warnings, or hints.
- `NPM_CONFIG_CACHE=/tmp/quran-json-npm-cache npm run site -- --no-cdn` — Astro built 2 pages and assembled the safe profile: 10 scripts, 83 translations, 0 transliterations.
- `NPM_CONFIG_CACHE=/tmp/quran-json-npm-cache npm run site -- --include-unverified-licenses --no-cdn` — assembled the explicit profile: 10 scripts, 84 translations, 1 transliteration, including the Kemenag transliteration layer. The post-change safe build was rerun after the final routing, font, and allowlist changes.
- `UV_CACHE_DIR=/tmp/quran-json-uv-cache uv run pytest tests/test_site_build.py -q` — 2 passed against `.build/assembled`.
- `node --test tests/reader/reader-regressions.mjs` — 7/7 unit cases; site_audit additionally reported 7/7 browser scenarios plus desktop/mobile/dark/RTL/no-JavaScript smoke checks against `.build/assembled`.
- `UV_CACHE_DIR=/tmp/quran-json-uv-cache NPM_CONFIG_CACHE=/tmp/quran-json-npm-cache npm run site` — populated local `cdn/` with the safe profile (10,725 files). `diff -rq .build/assembled cdn` is clean, and manifest, reader app, and homepage hashes match.
- `UV_CACHE_DIR=/tmp/quran-json-uv-cache uv run pytest tests/test_cdn_site.py tests/test_contracts.py -q` — 10 passed.
- `UV_CACHE_DIR=/tmp/quran-json-uv-cache uv run pytest -q` — 128 passed across the full repository suite.
- `UV_CACHE_DIR=/tmp/quran-json-uv-cache uv run ruff check .`, `uv run ruff format --check .`,
  and `uv run mypy` — all passed (60 files formatted; 19 source files type-checked).
- `NPM_CONFIG_CACHE=/tmp/quran-json-npm-cache npm pack --dry-run --json` — 7,516 files,
  23,006,390-byte tarball, 81,875,299-byte unpacked legacy package; the new site and schemas
  are excluded by the unchanged root `files` list.
- `git diff --check` passed. `git diff --name-only -- dist/` is empty.

The final safe assembled homepage is 49,050 bytes (9,364 gzip) and its generated Astro CSS is
13,365 bytes (3,843 gzip), keeping the measured documentation stylesheet near the previous
3.9 KB gzip baseline. With the current reader modules, `web/app/*.js` is 65,816 bytes (17,039
gzip) and `web/app/*.css` is 12,666 bytes (2,907 gzip). The local-link check found no missing
target among the page, reader shell, stylesheets, fonts, JSON pointers, or reader module imports.

## Handoff

Run `npm ci --prefix site` once, then `npm run site -- --no-cdn` and serve
`.build/assembled` for a safe local preview. Install Chromium with
`npm run reader:browser:install --prefix site` and run the seven-scenario browser harness with
`READER_BASE_URL=http://127.0.0.1:8765 npm run reader:browser --prefix site`. Use `npm run site`
when the generated `cdn/` output is intended, and pass `--include-unverified-licenses` only for
the explicitly authorized profile.
The reader builder's `web/app/**` changes are consumed by the shell but remain outside this
slice's ownership. The local `cdn/` was generated after the current reader QA; future root
regenerations should remain serialized after reader changes settle.
