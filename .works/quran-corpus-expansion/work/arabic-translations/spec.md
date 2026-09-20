# arabic-translations behavior contract

Status: ready
Scout: ../../../quran-modernization/scout-quran-json.md; targeted current source decisions at ../../source-decisions.md and ../../transliteration-decisions.md

## Goal

Add the two named Arabic editions and eight named QuranEnc translations, with complete source validation and unchanged existing payloads.

## Requirements

- R1 — Every target has a tested source and import outcome with exact edition/version/rights metadata.
- R2 — Publishable snapshots cover every chapter with valid verse identity and provenance.
- R3 — Old immutable payloads and frozen dist remain byte-identical; default and override profiles stay truthful.

## Acceptance criteria

- [ ] AC1 [R1] — Every target has a tested source and import outcome with exact edition/version/rights metadata.
- [ ] AC2 [R2] — Publishable snapshots cover every chapter with valid verse identity and provenance.
- [ ] AC3 [R3] — Old immutable payloads and frozen dist remain byte-identical; default and override profiles stay truthful.

## Edge cases and failures

- An incomplete, misidentified or malformed corpus fails import/validation rather than publishing partial content.
- Explicit restricted/unknown corpus rights remain recorded; unresolved candidates are distinguishable from published editions.
- A missing verse mapping or unsupported font prevents a misleading reading view; no alignment is guessed.

## Must not change

- Existing immutable payloads, frozen npm dist, prior modernization edits, and previously supported reader links/preferences.
