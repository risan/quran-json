# arabic-translations

Status: ready
Type: feature
Route: bounded-change — a defined corpus/import outcome
Next: draft-spec

## Request

Add the shortlisted editions; source: ../../brief.md.

## Goal

Add the two named Arabic editions and eight named QuranEnc translations, with complete source validation and unchanged existing payloads.

## Target

- Shared config/CDN/provenance, Quranpedia and QuranEnc importers, snapshots and data/schema tests.
- Pattern to follow: existing source-specific snapshots, license gates, semantic QA and reader identity metadata, documented in ../../../quran-modernization/scout-quran-json.md. Builders perform targeted fresh checks before editing.

## Acceptance criteria

- [ ] Every target has a tested source and import outcome with exact edition/version/rights metadata.
- [ ] Publishable snapshots cover every chapter with valid verse identity and provenance.
- [ ] Old immutable payloads and frozen dist remain byte-identical; default and override profiles stay truthful.

## Out of scope

- Remote publication, rights-holder contact and unrelated later-priority editions.

## Assumptions

- Shared-file ownership and integration order follow ../../implementation-plan.md.
