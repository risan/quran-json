# Local implementation plan

Status: ready
Planning: Astra; research/review: Sol High; implementation and execution: Luna Max.

## Decisions

- Build static docs and the reader shell with Astro and Tailwind 4, isolated in site/. Astro already supplies Vite.
- Retain and improve the modular vanilla reader. Its existing small dependency-free design, caching and identity-aware behavior make a Vue port unnecessary for the requested UX. Do not add an unused framework dependency.
- Python remains the only catalog/data authority. The site consumes generated records. Keep the Python data-only build usable without Node; document and test a canonical full-site build using locked Node dependencies.
- Stage frontend output outside root dist and integrate it into cdn with explicit copy boundaries. Preserve /app/, hash routes, old anchors, data paths, license gates and fonts.
- Use paper/ink colors, quiet borders, typographic hierarchy and generous reading space; avoid decorative card grids/gradients. Compact controls with visible labels, accessible settings sheet and per-translation attribution.
- Preserve gated and override modes; do not remove or silently enable existing unverified corpus options. No new corpus ingestion until the research's open provenance/permission/alignment questions are resolved.

## Ownership and execution

1. Data builder owns schemas/, src/quranjson/cdn.py and relevant data/cache tests. Add failing checks for catalog caching and schema rejection first. Implement minimal cache/schema fixes; preserve old data bytes and license status. Coordinate new output assets with site builder.
2. Site builder owns site/, excluding any separately assigned reader tests; web/index.html; web/assets CSS/site.js; README and build/CI integration; src/quranjson/web.py only if required. First capture frozen dist/data hashes and package file list. Build Astro docs from actual Python catalogs, retain useful no-JS content and old anchors, correct join examples, and render a compatible app shell that loads the owned web/app modules. Introduce locked dependencies and a safe canonical build command. Avoid rewriting corpus or root package entry/files fields.
3. Reader builder owns web/app/** and tests/reader/** (or site/tests/reader/** agreed with site builder). First reproduce unsafe optional-layer alignment and invalid route behavior in executable JS/browser tests, then fix. Improve translation labels, settings interaction, mobile toolbar, startup independence and per-layer failure handling. Preserve memoization/race/audio contracts.
4. Build integration is serialized by site builder after the two other builders finish. Run Python suite/lint/typing, Node tests, frontend production build, package/data parity, internal link checks and browser scenarios. Record which checks ran and actual output sizes; no unsupported accessibility/performance claims.
5. Sol independently reviews final diff/contracts; Luna fixes material findings and reruns affected checks. Capture rendered mobile/desktop examples and update local delivery evidence.

## Required verification

- Existing Python regression suite (baseline 120 passed), Ruff lint/format, mypy, legacy parity and licensed/default + explicit override metadata behavior.
- Schemas accept generated representative/current corpus outputs and reject malformed layers; catalog rules ensure mutable discovery isn't trapped by immutable wildcard caching.
- Full-site build succeeds from documented commands; npm packaging and frozen dist remain unchanged; current immutable Quran payloads retain hashes; output file count remains within current hosting capacity.
- Node/browser tests reproduce and fix invalid URL state and IndoPak transliteration alignment; preserve mapped riwayah joins and audio restrictions.
- Browser tests on mobile and desktop: navigation/search/chapter, labelled translations, settings keyboard/Escape/focus return, optional failures, deep links, no horizontal page overflow, no startup whole-corpus or reciter fetch, and stale response handling.
- Docs have no framework hydration and remain useful without JavaScript; record compressed first-party JS/CSS and font sizes, screenshots, external-request behavior and any tool limitations.

## Rollback

Existing Python snapshots and frozen dist remain intact. The prior template/data-only renderer remains available during migration. A frontend build failure fails the full-site command; it must not be mistaken for a newly completed site. No deployment occurs.
