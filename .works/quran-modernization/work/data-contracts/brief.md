# Reliable data discovery and contracts

Status: ready
Type: feature
Route: bounded-change — one independently verifiable local outcome
Next: draft-spec

## Request

Implement this slice of the user-authorized local modernization; source: ../../brief.md.

## Goal

Make current data easier to discover and validate without changing Quran payloads or the legacy npm tree.

## Target

- src/quranjson/cdn.py, new schemas/, dataset/cache tests; research-backed corpus shortlist.
- Pattern to follow: ../../scout-quran-json.md and ../../audit-site.md.

## Acceptance criteria

- [ ] Mutable edition catalogues have a tested revalidation policy; immutable edition payload caching remains.
- [ ] Machine-readable schemas describe the current manifest, catalogs, and chapter layers; generated examples validate and malformed fixtures fail.
- [ ] All existing Quran payloads and frozen dist bytes remain unchanged; no unverified corpus is newly published.

## Out of scope

- Frontend redesign and source ingestion.

## Assumptions

- Existing wire paths and license gating remain compatible.
- Shared build integration follows ../../roadmap.md.
