# Clear Astro documentation and reproducible site build

Status: ready
Scout: ../../scout-quran-json.md, ../../audit-site.md, ../../research-architecture.md

## Goal

Deliver elegant static documentation and shared styles with a reproducible Astro/Tailwind build isolated from the data package.

## Requirements

- R1 — Documentation must offer obvious routes to reading, fetching one chapter and browsing generated editions, without requiring client hydration.
- R2 — All existing documented anchors and data links must remain valid; code examples must join by verse identity.
- R3 — The full-site build must preserve dataset outputs, frozen dist and data license gating; a frontend failure must be reported as a failed build.
- R4 — The site must provide semantic navigation, visible keyboard focus, responsive reading widths, dark theme, same-origin fonts and useful no-JavaScript documentation.

## Acceptance criteria

- [ ] AC1 [R1] — An isolated Astro/Tailwind build produces homepage and reader shell in cdn without writing frozen dist.
- [ ] AC2 [R2] — Homepage gives direct read/fetch/catalog tasks, corrected ID-based join examples, generated catalogs, licenses and preserved anchors; useful with JavaScript disabled.
- [ ] AC3 [R3] — Shared visual design is restrained, responsive and keyboard accessible; mobile navigation replaces hidden navigation.
- [ ] AC4 [R4] — Canonical full-site command and safe default/explicit unverified build option are documented; data remain Python-owned.

## Must not change

- Quran corpus content, source license status, frozen npm dist bytes, current JSON paths, and reader identity/audio contracts — ../../scout-quran-json.md.

## Edge cases and failures

- Invalid optional selections recover to supported defaults; no mismatched text is rendered.
- Missing optional corpora remain explicitly unavailable, without false availability claims.
- Build or validation failure is reported and does not count as successful verification.

## Out of scope

- Reader business logic, corpus ingestion and remote deployment.
