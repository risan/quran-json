# Reader implementation

Status: locally verified

This slice keeps the existing dependency free reader controller and adds a small pure rules
module. The deployed site was not changed. Browser checks ran first against a temporary `cdn/`
copy, then against the fresh safe-profile `.build/assembled/` output on
`127.0.0.1:8777`; the assembled app hashes match `web/app/`.

## Behavior delivered

- `web/app/reader-core.js` parses hash routes, validates saved and URL selections
  against the published manifest/catalogues/font coverage, validates resume positions, joins
  mapped Warsh/Qalun verses to Hafs keyed optional layers, suppresses all optional layers for
  divergent IndoPak chapters, validates optional chapter identity, required fields, sequential
  IDs, and the canonical verse count before joining, and filters per-ayah audio for riwayat where
  Hafs numbering cannot be trusted.
- `web/app/app.js` loads required manifest/chapter/font metadata first. Translation
  and transliteration catalogues use `Promise.allSettled`, and each optional chapter
  layer is isolated with a failure result and payload-shape validation. Arabic remains renderable
  when an optional request fails; stale chapter responses still use the existing load token and
  `api.js` memo cache.
- `web/app/ui.js` gives every loaded translation an author/code label beside its
  text, attributes translator notes to the matching edition, labels both chapter navigation
  landmarks, adds an explicitly named `Open reader settings` control, and provides
  a mobile settings dialog with close, Escape, focus return, Tab wrapping, an inert background,
  and an internal scroll region that reaches Arabic-size controls at 320px.
- `web/app/app.css` keeps the shared paper/ink token interface, narrows the reading
  column, improves translation hierarchy and focus visibility, groups the toolbar on narrow
  screens, and removes page overflow at 320px in the local browser check.

## Executable checks

`node --check web/app/app.js`, `node --check web/app/ui.js`, and
`node --check web/app/reader-core.js` pass.

`node --test tests/reader/reader-regressions.mjs` passes 7 tests:

- IndoPak chapter 1 has Arabic only when its verse IDs diverge from Hafs.
- A mapped Warsh verse joins its two Hafs translations once and in order.
- Warsh and Qalun expose only surah audio records to the reader.
- Malformed stored script, edition, font, size, boolean, and resume values recover to supported
  defaults.
- Fulfilled optional chapter payloads with the wrong chapter, duplicate/gapped IDs, missing
  required text, truncated/extra verse rows, or a mismatched canonical count are rejected before
  a positional join.
- Malformed hash chapter/selection values remain parseable for controller validation.

The Node run emits the existing `MODULE_TYPELESS_PACKAGE_JSON` warning because this
repository's root package does not declare `"type": "module"`; no package/config file
was changed for this reader-owned slice.

## Browser evidence

The isolated browser toolchain is Playwright 1.63.0 with Chromium 153.0.8010.12 under
`/tmp/quran-modernization-browser`. A compact summary is in
`.works/quran-modernization/site-evidence/reader-local-checks.json`.
The repository harness is `tests/reader/browser-regressions.mjs`; run it against an assembled
site after installing the site's Playwright dependency (the isolated run supplied
`READER_PLAYWRIGHT_MODULE=/tmp/quran-modernization-browser/node_modules/playwright/index.mjs`).

- At 320×568, both the chapter grid and chapter 2 report
  `document.documentElement.scrollWidth === innerWidth` (320), and the toolbar
  exposes `aria-label="Open reader settings"`.
- At 375×812, the settings dialog opens with label `Reader settings`, focuses the
  script select, and Escape closes it with focus returned to the Settings trigger. Tab from the
  close button wraps to the script select; scrolling the settings sheet reaches Arabic-size
  controls. The local axe run reported no violations for mobile and desktop chapter pages.
- The local IndoPak deep link
  `#/1?s=indopak&t=en-rwwad&tl=kemenag` rendered 8 Arabic nodes, zero translation
  blocks, zero transliteration nodes, and the explicit divergence explanation.
- Local 503 and malformed-JSON/wrong-ID responses for
  `/translations/*/chapters/**` rendered 287 Arabic nodes, zero translation blocks,
  and the status `Arabic is ready; 1 optional layer could not be loaded.`.
- A valid-looking truncated optional chapter (matching chapter ID and verse 1 but missing the
  canonical verse count) is rejected with the same Arabic-only result.
- Delaying the chapter request and navigating to `#/` left the chapter grid visible
  after the delayed response completed, proving the grid invalidates the pending load.

Viewport captures are in
`.works/quran-modernization/site-evidence/reader-modernized-desktop.png`,
`reader-modernized-mobile-viewport.png`, and
`reader-modernized-settings-mobile-viewport.png`. The earlier live baseline remains
in `baseline.json` and `reader-home-*`/`reader-chapter-2-*`;
those files describe the deployed pre-change page and must not be read as evidence that the
deployment includes this implementation.

Fresh assembled captures are named `assembled-docs-desktop.png`,
`assembled-docs-mobile.png`, `assembled-reader-home-desktop.png`,
`assembled-reader-home-mobile.png`, `assembled-reader-dark.png`, and
`assembled-reader-rtl.png` in the same evidence directory.

The final assembled Astro smoke is recorded in
`.works/quran-modernization/site-evidence/assembled-smoke.json`, with fresh screenshots for
documentation and reader desktop/mobile, a dark reader chapter, and an RTL translation chapter.
It also verifies the mobile navigation hash, all four primary mobile navigation links, and the
documentation homepage plus reader link with JavaScript disabled. The final assembled reader run
passed all seven browser scenarios with:

```sh
READER_PLAYWRIGHT_MODULE=/tmp/quran-modernization-browser/node_modules/playwright/index.mjs \
PLAYWRIGHT_BROWSERS_PATH=/tmp/quran-modernization-browser/browsers \
READER_BASE_URL=http://127.0.0.1:8777 node tests/reader/browser-regressions.mjs
```

## Integration notes

The site shell should copy all files in `web/app/`, including
`reader-core.js`, and retain the existing `/app/` route and shared token
names. No JSON corpus, data source, audio template, cache header, or generated `cdn/`
artifact was edited by this slice.
