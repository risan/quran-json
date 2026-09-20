# transliteration-reader

Status: ready
Type: feature
Route: bounded-change — a defined corpus/import outcome
Next: draft-spec

## Request

Add the shortlisted editions; source: ../../brief.md.

## Goal

Support the named transliteration resources and make the reader safe for new Arabic editions.

## Target

- Owned transliteration modules/snapshots/tests; reader/font integration; shared config changes delegated to the data owner.
- Pattern to follow: existing source-specific snapshots, license gates, semantic QA and reader identity metadata, documented in ../../../quran-modernization/scout-quran-json.md. Builders perform targeted fresh checks before editing.

## Acceptance criteria

- [ ] Each transliteration candidate is supported, reused/deduplicated or explicitly withheld with a concrete source blocker.
- [ ] Granularity, markup, audience/scheme and rights are preserved rather than fabricated.
- [ ] New scripts pass font, alignment and audio-safety checks; existing reader behavior remains covered.

## Out of scope

- Remote publication, rights-holder contact and unrelated later-priority editions.

## Assumptions

- Shared-file ownership and integration order follow ../../implementation-plan.md.
