# Clear Astro documentation and reproducible site build

Status: ready
Type: migration
Route: bounded-change — one independently verifiable local outcome
Next: draft-spec

## Request

Implement this slice of the user-authorized local modernization; source: ../../brief.md.

## Goal

Deliver elegant static documentation and shared styles with a reproducible Astro/Tailwind build isolated from the data package.

## Target

- site/ except reader-owned files; web/index.html, web/assets styling, src/quranjson/web.py only if needed; README, build documentation and CI.
- Pattern to follow: ../../scout-quran-json.md and ../../audit-site.md.

## Acceptance criteria

- [ ] An isolated Astro/Tailwind build produces homepage and reader shell in cdn without writing frozen dist.
- [ ] Homepage gives direct read/fetch/catalog tasks, corrected ID-based join examples, generated catalogs, licenses and preserved anchors; useful with JavaScript disabled.
- [ ] Shared visual design is restrained, responsive and keyboard accessible; mobile navigation replaces hidden navigation.
- [ ] Canonical full-site command and safe default/explicit unverified build option are documented; data remain Python-owned.

## Out of scope

- Reader business logic, corpus ingestion and remote deployment.

## Assumptions

- Existing wire paths and license gating remain compatible.
- Shared build integration follows ../../roadmap.md.
