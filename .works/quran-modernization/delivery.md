# Local delivery

Date: 2026-09-20
Status: implemented and verified locally

## Delivered

- Astro/Tailwind static documentation and reader shell, with generated catalog data, a task-first quickstart, identity-based joining examples, preserved anchors, mobile navigation, and useful documentation without JavaScript.
- A refined modular JavaScript reader: labelled translation passages and notes, mobile settings with keyboard/focus/scroll behavior, validated links and saved state, correct optional-layer alignment, isolated optional failures, and protection against late chapter responses.
- JSON schemas and semantic contract tests, including legitimate Warsh/Qalun split/merge mappings; corrected discovery-cache headers without changing immutable Quran payloads.
- An isolated, reproducible site build, explicit safe versus unverified profiles, CI coverage for the assembled output, and source-linked corpus/transliteration research.

Astro supplies Vite. The reader remains in JavaScript; no Vue or React runtime was added. Python remains the data authority, and the frozen npm `dist/` contract remains intact.

## Research answer

The strongest Arabic addition to investigate is al-Duri as a distinct riwayah. The repo already has IndoPak; Quranpedia Hafs Nastaliq is an exact-edition comparison candidate, not proof that an entire writing tradition is absent.

Bengali and Malay lead the current-catalog translation clarification queue, followed by Korean, Italian and Ukrainian. Modern Russian is an additional-edition gap. Bengali also exists in the restricted legacy tree. All 75 translations returned by QuranEnc's canonical list are already imported; the newly identified endpoints are unlisted and conditional.

There is no automatic one-transliteration-per-language rule. Store a named scheme, source and target scripts, intended audience, purpose, alignment, provenance and corpus rights. Kemenag Latin and Tanzil English/Turkish are useful permission targets; QUL needs resource-specific provenance and terms.

No new corpus was ingested: none of the newly identified candidates had sufficiently verified source-specific rights, completeness and alignment. See the [proposal](proposal.md), [corpus research](research-corpus.md), and [transliteration research](research-transliteration.md).

## Verification

| Check | Result |
|---|---|
| Python suite | 128 passed |
| Reader Node regressions | 7 passed |
| Assembled reader browser scenarios | 7 passed |
| Astro check, Ruff, formatting, mypy | Passed |
| Assembled local links, anchors and module imports | Passed |
| Desktop/mobile docs and reader, dark/RTL, mobile navigation, no-JS docs | Smoke checks passed |
| Reader accessibility sample | No axe violations on sampled chapter views; keyboard/settings checks passed |
| Data compatibility | Review compared 10,703 generated JSON files byte-for-byte with baseline |
| Frozen legacy package | `dist/` unchanged; npm pack contract checked |
| Independent source reviews | Data, site and reader follow-ups have no open blocker |
| Final local output | Canonical safe build populated `cdn/`; all 10,725 files match `.build/assembled` |

Playwright is a locked, site-only development dependency. The repository browser harness resolves it from `site/node_modules`; it no longer requires a temporary module path. The README documents installation and the `reader:browser:install` / `reader:browser` scripts.

The measured safe homepage is 49,050 bytes (9,364 gzip); its generated stylesheet is 13,365 bytes (3,843 gzip). These are local compressed sizes, not field Core Web Vitals. The safe profile contains 10 Arabic editions, 83 translations and no transliteration; the explicit unverified profile was also built and checked, with 84 translations and one transliteration retaining its status metadata.

The checks do not constitute a complete screen-reader, cross-browser or real-user performance certification. Audio host availability remains external. Already cached live catalog responses cannot be recalled by a local header change.

## Preview

From the repository root:

```sh
npm ci --prefix site
npm run site -- --no-cdn
python3 -m http.server 8777 --bind 127.0.0.1 --directory .build/assembled
```

Open <http://127.0.0.1:8777/> and <http://127.0.0.1:8777/app/>. The default is the rights-gated profile. `npm run site` also writes the assembled output to the ignored local `cdn/` directory.

## Evidence

- [Data implementation](work/data-contracts/implementation.md) and [review](work/data-contracts/review.md)
- [Site implementation](work/static-site/implementation.md) and [review](work/static-site/review.md)
- [Reader implementation](work/reader/implementation.md) and [review](work/reader/review.md)
- [Homepage desktop](site-evidence/assembled-docs-desktop.png) and [mobile](site-evidence/assembled-docs-mobile.png)
- [Reader desktop](site-evidence/assembled-reader-home-desktop.png), [mobile](site-evidence/assembled-reader-home-mobile.png), [dark](site-evidence/assembled-reader-dark.png), and [RTL](site-evidence/assembled-reader-rtl.png)
- [Assembled smoke results](site-evidence/assembled-smoke.json)

No commit, push, deployment, or contact with rights holders was performed.
