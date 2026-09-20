# Reader implementation review

Verdict: **changes requested**. The Arabic-first loading, route normalization, Hafs alignment rules, per-edition attribution and footnotes, stale-response guard, and core modal mechanics are materially improved. Three defects remain before this reader candidate meets the approved correctness and accessibility contract.

## Candidate reviewed

- Repository HEAD: `5497c1be67a8f544014bec5dd6a0d2e7c2abbd36`
- Dirty reader snapshot reviewed on 2026-09-20:
  - `web/app/app.js` — `968cc3f7aeb927fb53f4db7c319af89acae16788eb35e284205d70a3e7d6dd81`
  - `web/app/ui.js` — `3f98fbd7137ebb57b4e11edab1592cce8008662c5d4a59d6a57ef6d60ff26d40`
  - `web/app/app.css` — `8d4bbaf8de4d19e420d6c4d5ca7070cb53d257a88ac452d81ceff816858c42c4`
  - `web/app/index.html` — `0b9e0a3fbfd11221325ec4cf37f73af7db2e8c2ecbcbb0ebc6af6a74ae75674f`
  - `web/app/reader-core.js` — `ac6fab4463dee7a6b84a8a604ffd434da46355d1bfe3a9aeb888011a250e574c`
  - `tests/reader/reader-regressions.mjs` — `1915df872b4d6b5368abdf56383660a938226c5bb44bccee6111201513e4f2d0`
- Evidence inspected: `work/reader/implementation.md`, `site-evidence/reader-local-checks.json`, and the desktop, 320 px reader, and 320 x 568 settings screenshots. Per assignment, this review did not rerun tests or browser automation.

## Material findings

### 1. Blocker — the settings dialog cannot expose all controls in a short mobile viewport

**Evidence:** `reader-modernized-settings-mobile-viewport.png` is 320 x 568 and visibly ends halfway through the **Arabic size** label; its buttons are below the viewport. `web/app/app.css:730-741` caps the fixed popover to the viewport height, but neither `.popover` nor `.settings-sheet` has vertical scrolling. Only `.popover-list` scrolls (`web/app/app.css:464-467`), which does not help the settings sheet. The rest of the page is correctly made inert while the dialog is open (`web/app/app.js:383-387`), so scrolling the background cannot reveal these controls.

**Reproduction:** at a 320 x 568 viewport, open **Settings**. The last setting is clipped below the screen and the dialog has no scroll container.

**Required fix:** make the settings content scroll inside the dialog's capped height, for example by giving the sheet a bounded flex size with `min-height: 0` and `overflow-y: auto`, or by making the dialog itself scroll while retaining the existing `.popover-list` behavior. Re-capture 320 x 568 with the Arabic-size buttons reachable by touch and keyboard.

### 2. Blocker — a structurally wrong optional chapter can be attached to the wrong Arabic verses

**Evidence:** `optionalChapterPayload()` accepts every fulfilled object whose `verses` value is an array (`web/app/app.js:159-163`). `mergeChapter()` then indexes that array with `number - 1` and does not verify the returned verse's `id` (`web/app/reader-core.js:58-75`). The recorded malformed-payload check proves that a non-array is isolated, but it does not protect verse identity.

**Reproduction:** fulfill a selected translation request for chapter 2 with `{ "id": 2, "verses": [{ "id": 999, "translation": "wrong verse" }] }`. It passes the current validator, and `wrong verse` is rendered beside Arabic verse 1.

**Required fix:** validate the optional payload before merge: matching chapter id, expected verse count, sequential and unique verse ids, and the layer's required string field (`translation` or `transliteration`). Treat a validation failure like the existing optional-layer rejection so Arabic remains available and the named layer warning appears. Add a failure-capable regression using a valid array with wrong ids/order, since the current `verses: null` case cannot catch this defect.

### 3. Major — mutating dialog actions lose focus, and the settings transliteration state becomes stale

**Evidence:** `closePopover()` can resolve a replacement trigger after a toolbar rerender (`web/app/app.js:389-425`), but several callers close first and rerender second. Translation clear does this at `web/app/app.js:477-481`; normal reciter selection does it through `pickReciter()` at `web/app/app.js:428-443`. Script and font changes explicitly close without restoration before rerendering (`web/app/app.js:596-608`). In all four cases the focused trigger is then removed with the toolbar, leaving keyboard focus on the document body. The tested Escape path avoids this and is correct.

The settings-sheet transliteration button has a related state defect: it changes state and rerenders the toolbar and reader, but leaves the open dialog's old **On/Off** text and `aria-pressed` value in place (`web/app/app.js:484-491`; `web/app/ui.js:239-242`). A second activation performs the opposite action from the state announced on screen.

**Reproduction:** open Settings with the keyboard, change Script or Font, then inspect `document.activeElement`; the trigger is not restored. Separately, toggle Transliteration in Settings; the visible label and `aria-pressed` do not change although the reader state does.

**Required fix:** perform the external rerender before resolving/restoring the recorded trigger, or defer role-based focus restoration until after the new toolbar exists. Update or rerender the settings sheet after the transliteration toggle (or close it and restore focus) so its visible and programmatic state match. Cover selection/clear/change closure in addition to Escape.

## Confirmed improvements

The reviewed source and receipts support these outcomes: navigating from a pending chapter request back to the grid invalidates the old response; an HTTP failure or the tested non-array optional payload preserves Arabic; Indo-Pak chapter 1 suppresses Hafs-keyed translation and transliteration; mapped Warsh joins remain covered; per-edition translation labels and footnotes remain associated; invalid saved resume data is discarded; a missing saved reciter is reported after the intentionally lazy reciter fetch; and the dialog has a specific accessible name, Escape close, connected-trigger recovery, visible-item focus wrapping, and inert background content.

The reader screenshot is otherwise calm and readable at 320 px: the chapter heading, mixed Latin/Arabic title, navigation, and right-aligned Arabic remain legible without horizontal overflow. The desktop full-page capture and mobile capture do not show a bidirectional-text collision. Those visual strengths do not offset the clipped settings controls above.

## Follow-up review — 2026-09-20 14:33 evidence

Verdict: **changes requested — one correctness blocker remains**. Findings 1 and 3 above are fixed in the revised source. Finding 2 is fixed for wrong chapter ids, wrong verse ids/order, and absent text fields, but the requested expected-count condition is still missing.

### Revised candidate snapshot

- Repository HEAD remains `5497c1be67a8f544014bec5dd6a0d2e7c2abbd36`.
- `web/app/app.js` — `fc50496fed1334517c78076c6d91ed41afe599af99920d18690b688b1a30c211`
- `web/app/ui.js` — `3f98fbd7137ebb57b4e11edab1592cce8008662c5d4a59d6a57ef6d60ff26d40`
- `web/app/app.css` — `82e45453d3c61d501cd6e517219040d9590b43cdc40c3aa1e5dd05c32880cb65`
- `web/app/index.html` — `0b9e0a3fbfd11221325ec4cf37f73af7db2e8c2ecbcbb0ebc6af6a74ae75674f`
- `web/app/reader-core.js` — `faf7ec761124cca1a35838645a07af6d5160901f962cc531c72d2c55753ed541`
- `tests/reader/reader-regressions.mjs` — `843a4e8aa686b479df3b793ad53a790bcbbe07852947cb5ffd1dacce10fad708`
- `tests/reader/browser-regressions.mjs` — `15dd89a3b0f036ac6f059d280e0ea8e66b3953bbadc83a245a3062d3d1a9183c`

This follow-up inspected source, the updated implementation receipt and JSON evidence, the reproducible browser harness, and both mobile PNGs. It did not execute tests or browser automation.

### Corrections verified

1. **Short-viewport settings access is fixed in source and executable evidence.** `.settings-sheet` now has `min-height: 0` and `overflow-y: auto` (`web/app/app.css:670-673`). The browser regression scrolls this element at 320 x 568 and asserts that the Arabic-size button is within the dialog (`tests/reader/browser-regressions.mjs:32-47`); the updated JSON records `arabicSizeReachableAfterScroll: true`. The settings PNG itself was not recaptured: it still has the 14:15 timestamp and shows the initial, unscrolled position. This is an evidence presentation limitation rather than a source blocker because the scroll assertion is reproducible.

2. **After-rerender focus and transliteration state are fixed.** Script and font changes close without focusing the soon-to-be-removed node, synchronously rerender, and then focus the new Settings trigger (`web/app/app.js:605-624`). Settings transliteration follows the same sequence and closes before rerender, so reopening derives its visible label and `aria-pressed` from the new state (`web/app/app.js:490-500`). Translation clear and both normal and pending-audio reciter selection likewise call `focusTrigger()` only after the replacement toolbar exists (`web/app/app.js:430-448`, `:482-488`). The browser harness directly covers script, transliteration, translation-clear, and Escape focus (`tests/reader/browser-regressions.mjs:48-71`); font and reciter use the same synchronous replacement-and-focus mechanism.

3. **Wrong-identity optional data is now isolated.** `validateOptionalChapter()` rejects a mismatched chapter, non-array/empty verses, non-sequential ids, and missing type-specific text before the positional merge (`web/app/reader-core.js:50-71`). The controller converts the thrown error into the existing optional-layer failure result (`web/app/app.js:286-299`). Node and browser regressions include the formerly unsafe `{id: 999}` shape.

### Remaining blocker — truncated sequential chapters still pass validation

`validateOptionalChapter()` has no expected verse-count input. The controller passes only `chapterId`, `key`, and `type` (`web/app/app.js:292-296`). Consequently, chapter 2 payload `{ "id": 2, "verses": [{ "id": 1, "translation": "only one" }] }` is nonempty, sequential, and has the expected field, so it passes. The first translation is rendered and the other 285 missing translations produce no layer warning. An overlong sequential array also passes, with the excess silently unused.

Pass the chapter's expected Hafs verse count into the validator and require exact equality before checking ids and fields. Add a regression using a truncated but otherwise valid sequential array. Once that condition is enforced, the three original findings are clean in source and focused evidence; final assembled-site browser integration remains the broader delivery gate.

## Final focused follow-up — expected verse count

Verdict: **clean for the reader source and visual scope reviewed; pending the final assembled-site browser integration run.** The last correctness blocker is fixed.

`validateOptionalChapter()` now requires a positive integer `expectedVerseCount` and exact array length before inspecting sequential ids and the required layer field (`web/app/reader-core.js:51-73`). The controller supplies `chapter.total_verses` for every optional request (`web/app/app.js:292-297`). The focused regression rejects both a truncated sequential chapter and an overlong sequential chapter (`tests/reader/reader-regressions.mjs:129-150`). Those conditions close the silent partial-layer and ignored-excess cases described above while retaining the existing Arabic-only failure path.

Snapshot reviewed without executing tests:

- Repository HEAD: `5497c1be67a8f544014bec5dd6a0d2e7c2abbd36`
- `web/app/app.js` — `54d6a0f1c25422161d3198ffa103650d355270aa3dee3613cc9bd14e0e2b0cb5`
- `web/app/ui.js` — `3f98fbd7137ebb57b4e11edab1592cce8008662c5d4a59d6a57ef6d60ff26d40`
- `web/app/app.css` — `82e45453d3c61d501cd6e517219040d9590b43cdc40c3aa1e5dd05c32880cb65`
- `web/app/index.html` — `0b9e0a3fbfd11221325ec4cf37f73af7db2e8c2ecbcbb0ebc6af6a74ae75674f`
- `web/app/reader-core.js` — `4b566bcb68376ba2caff80c8424454aedb80b19da6b4c18887dc8f4985f1d08b`
- `tests/reader/reader-regressions.mjs` — `2bb389a5ee9a2decd2ca89b8539e5fba3f6c1286626f34c33a479edd422d1dd7`
- `tests/reader/browser-regressions.mjs` — `e0377da529265083f2e75b0167f4b0d176d43c409e8c9779f90a1c670b7140f3`

No material reader defect remains from the three requested corrections. The retained narrow limitation is evidence presentation: the settings PNG shows the initial unscrolled position; reachability is established by the reproducible 320 x 568 browser assertion rather than a scrolled screenshot. Final judgment on the assembled Astro/Python output still belongs to the integration run because this review inspected the reader-owned source snapshot only.
