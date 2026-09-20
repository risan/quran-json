# Readable and resilient Quran reader

Status: ready
Scout: ../../scout-quran-json.md, ../../audit-site.md, ../../research-architecture.md

## Goal

Improve the existing reader's correctness, accessibility, mobile controls and reading presentation while preserving its tested data-loading behavior.

## Requirements

- R1 — Render only correctly aligned text layers and identify each translation's edition near its verse text.
- R2 — Unsupported route or stored selections must resolve to supported choices with useful feedback; optional data failures must leave available Arabic readable.
- R3 — Reading/settings/navigation must work by touch and keyboard on narrow and wide screens; dialogs must provide a complete accessible interaction.
- R4 — Preserve existing deep links, saved preferences, chapter-only data loading, stale-response protection, font coverage and recitation safety.

## Acceptance criteria

- [ ] AC1 [R1] — IndoPak divergent chapter suppresses every unsupported Hafs-keyed optional layer; mapped Warsh/Qalun behavior remains correct.
- [ ] AC2 [R2] — URL and saved preferences are validated; malformed selections recover; optional catalog/layer failures do not prevent Arabic reading.
- [ ] AC3 [R3] — Each translation identifies its edition; settings have accessible names, close/Escape/focus-return behavior and usable mobile controls.
- [ ] AC4 [R4] — Hash routes, preferences, chapter-only loading, promise caching, race handling, font eligibility, audio numbering and selected-layer behavior retain tests.
- [ ] AC5 [R4] — Browser tests cover 320px/desktop, mixed RTL/LTR, keyboard settings, network failure, deep links and alignment; capture screenshots and payload measurements.

## Must not change

- Quran corpus content, source license status, frozen npm dist bytes, current JSON paths, and reader identity/audio contracts — ../../scout-quran-json.md.

## Edge cases and failures

- Invalid optional selections recover to supported defaults; no mismatched text is rendered.
- Missing optional corpora remain explicitly unavailable, without false availability claims.
- Build or validation failure is reported and does not count as successful verification.

## Out of scope

- Framework rewrite, source ingestion, offline/PWA and remote deployment.
