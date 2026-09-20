# transliteration-reader behavior contract

Status: ready
Scout: ../../../quran-modernization/scout-quran-json.md; targeted current source decisions at ../../source-decisions.md and ../../transliteration-decisions.md

## Goal

Support the named transliteration resources and make the reader safe for new Arabic editions.

## Requirements

- R1 — Each transliteration candidate is supported, reused/deduplicated or explicitly withheld with a concrete source blocker.
- R2 — Granularity, markup, audience/scheme and rights are preserved rather than fabricated.
- R3 — New scripts pass font, alignment and audio-safety checks; existing reader behavior remains covered.

## Acceptance criteria

- [ ] AC1 [R1] — Each transliteration candidate is supported, reused/deduplicated or explicitly withheld with a concrete source blocker.
- [ ] AC2 [R2] — Granularity, markup, audience/scheme and rights are preserved rather than fabricated.
- [ ] AC3 [R3] — New scripts pass font, alignment and audio-safety checks; existing reader behavior remains covered.

## Edge cases and failures

- An incomplete, misidentified or malformed corpus fails import/validation rather than publishing partial content.
- Explicit restricted/unknown corpus rights remain recorded; unresolved candidates are distinguishable from published editions.
- A missing verse mapping or unsupported font prevents a misleading reading view; no alignment is guessed.

## Must not change

- Existing immutable payloads, frozen npm dist, prior modernization edits, and previously supported reader links/preferences.
