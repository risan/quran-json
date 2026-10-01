# Track B report: new site

Branch: worktree-agent-ade5a69346f6cd0ee (A1 merged in).

## Built
- `web/` deleted. Fonts + OFL texts + sources.json moved to `site/public/fonts/` (served `/fonts/`), favicon to `site/public/favicon.svg`.
- `src/quranjson/web.py` is now only the fontTools coverage gate (`FONTS`, `font_coverage`, `coverage_from_data`, `write_coverage`). New CLI `quran-json fonts --data DIR --out PATH`. `cdn.py` lost only the `web.*` calls (plus the `corpora`/`samples` locals that fed them); `config.WEB` removed. `cdn._chapter` is now unused (left in place to keep the diff small).
- `scripts/build-site.mjs`: runs `fonts` into `.build/fonts.json` (outside the data tree) before Astro, passes it via `QURAN_JSON_FONTS`; allowlist `index.html`, `app/index.html`, `favicon.svg`, `_astro/*`, `fonts/*`; any collision with a data path errors.
- Coverage is embedded in the reader island props at build time; the reader restricts fonts per script to `usable` and falls back to the script default when a stored font does not cover it (vitest: indopak + amiri).
- site/src: `layouts/Base.astro`, `components/Header.astro`, `components/docs/*` (Section, CodeTabs, Toc), `pages/index.astro` (docs), `pages/app/index.astro`, `components/reader/*` (ReaderApp, Toolbar, SurahNav, CommandPalette, SettingsSheet, VerseRow, AudioBar, Combobox), `reader/*` (core.ts riwayah logic, audio.ts, search.ts, data.ts, storage.ts, useChapter.ts, useAudio.ts, player-logic.ts), `lib/catalog.ts` (build-time loader), `lib/types.ts`, `scripts/docs.ts`, `styles/global.css`, `components/ui/*` (shadcn, Base UI, edited: no shadows, h-8 controls, radius .375rem).
- Reading identity: all reader-core regressions ported to vitest, plus Warsh 1:3 vs Hafs 1:4 transliteration, both audio mismatch directions, font fallback.
- CI: lint, fmt:check, check, test, `npm run site -- --no-cdn`, `pytest tests/test_site_build.py`. `tests/reader`, `tests/site` removed. `tests/test_web.py`, `tests/test_site_build.py` rewritten.
- Docs Changes section states `/app/fonts.json`, `/assets/*`, `/app/*.js|css` were removed.

## Run
- `npm ci --prefix site`; `npm run site -- --no-cdn` builds `.build/assembled`.
- Dev: `QURAN_JSON_SITE_DATA=.build/data QURAN_JSON_FONTS=.build/fonts.json npm run dev --prefix site` needs `.build/data` to exist (run `npm run site -- --no-cdn` once) and the reader fetches data from the same origin; see Known gaps.
- E2E (not in CI, run from repo root): `node site/tests/e2e/smoke.mjs`, `node site/tests/e2e/screenshots.mjs`.

## Results
lint, fmt:check, check, vitest (40 tests), site build, `uv run pytest` (127), ruff check/format, mypy: all pass. Smoke test passes (docs tabs/search, deep link `#/2:255`, palette `36:1`, switch to Warsh and back, Play requests `everyayah.com/.../036001.mp3` and shows the audio bar).

## Screenshots
`.works/quran-overhaul/site-evidence/`: docs and reader at 1440 and 390, light and dark; reader settings sheet, command palette, mobile surah sheet. No horizontal overflow at 390.

## Known gaps
- `npm run dev`: no dev data middleware was written; reader data fetches are same-origin or `PUBLIC_QURAN_JSON_DATA_BASE` (needs a CORS-enabled data server). Use the assembled build for local testing.
- Audio playback itself (sound) was not verified; only that the correct URL is requested.
- Transliteration UI is untested against real data (the index has 0 entries); covered by unit tests only.
- Docs mobile contents is a native `<dialog>` sheet, not a React Sheet (keeps docs JS-free). The reader's mobile surah button lives in the toolbar, not the header.
- Opening bismillah is drawn only for Hafs-numbered scripts (from the script's own 1:1), chapters other than 1 and 9; Duri uses manifest furniture.
- `components/ui/scroll-area.tsx` produces an astro-check hint (generated file).
