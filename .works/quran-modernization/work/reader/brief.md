# Readable and resilient Quran reader

Status: ready
Type: feature
Route: bounded-change — one independently verifiable local outcome
Next: draft-spec

## Request

Implement this slice of the user-authorized local modernization; source: ../../brief.md.

## Goal

Improve the existing reader's correctness, accessibility, mobile controls and reading presentation while preserving its tested data-loading behavior.

## Target

- web/app/** plus reader-focused browser/unit tests. Shared site tokens coordinated with static-site owner.
- Pattern to follow: ../../scout-quran-json.md and ../../audit-site.md.

## Acceptance criteria

- [ ] IndoPak divergent chapter suppresses every unsupported Hafs-keyed optional layer; mapped Warsh/Qalun behavior remains correct.
- [ ] URL and saved preferences are validated; malformed selections recover; optional catalog/layer failures do not prevent Arabic reading.
- [ ] Each translation identifies its edition; settings have accessible names, close/Escape/focus-return behavior and usable mobile controls.
- [ ] Hash routes, preferences, chapter-only loading, promise caching, race handling, font eligibility, audio numbering and selected-layer behavior retain tests.
- [ ] Browser tests cover 320px/desktop, mixed RTL/LTR, keyboard settings, network failure, deep links and alignment; capture screenshots and payload measurements.

## Out of scope

- Framework rewrite, source ingestion, offline/PWA and remote deployment.

## Assumptions

- Existing wire paths and license gating remain compatible.
- Shared build integration follows ../../roadmap.md.
