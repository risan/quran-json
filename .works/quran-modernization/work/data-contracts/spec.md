# Reliable data discovery and contracts

Status: ready
Scout: ../../scout-quran-json.md, ../../audit-site.md, ../../research-architecture.md

## Goal

Make current data easier to discover and validate without changing Quran payloads or the legacy npm tree.

## Requirements

- R1 — Discovery catalogs must become refreshable while existing public URLs remain valid.
- R2 — Published schema documents must describe current data shapes and semantic regression checks must reject invalid identity/direction/alignment fields.
- R3 — Existing corpus bytes, source statuses, license gate, frozen package output and all existing dataset routes remain compatible.

## Acceptance criteria

- [ ] AC1 [R1] — Mutable edition catalogues have a tested revalidation policy; immutable edition payload caching remains.
- [ ] AC2 [R2] — Machine-readable schemas describe the current manifest, catalogs, and chapter layers; generated examples validate and malformed fixtures fail.
- [ ] AC3 [R3] — All existing Quran payloads and frozen dist bytes remain unchanged; no unverified corpus is newly published.

## Must not change

- Quran corpus content, source license status, frozen npm dist bytes, current JSON paths, and reader identity/audio contracts — ../../scout-quran-json.md.

## Edge cases and failures

- Invalid optional selections recover to supported defaults; no mismatched text is rendered.
- Missing optional corpora remain explicitly unavailable, without false availability claims.
- Build or validation failure is reported and does not count as successful verification.

## Out of scope

- Frontend redesign and source ingestion.
