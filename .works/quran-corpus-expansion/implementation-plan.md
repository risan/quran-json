# Corpus expansion implementation plan

Status: implemented and verified locally; see delivery.md for actual candidate dispositions and external limits.

## Approach

1. Reassess exact current primary terms for the named source editions, using the same evidence standard as equivalent already accepted editions. Do not infer a legal exclusion solely from absence in an availability list. Distinguish source permission from technical completeness and update support.
2. Preserve the complete existing worktree and snapshot public payload identities before extension. Keep frozen dist and existing immutable edition paths byte-identical.
3. Add the two exact Quranpedia Arabic editions through the existing downloader/parser/provenance pipeline, with edition-specific verse identity and accurate mappings. Do not replace indopak or reuse a font/layout label as corpus identity.
4. Add explicitly named supplemental QuranEnc editions when source terms support them. Record metadata/version separately from the canonical upstream list, import and validate all 114 chapters, and make refreshes deterministic and drift-aware.
5. Add transliteration registry/acquisition support using exact provenance, scheme/audience/purpose/granularity and rights. Reuse existing English/Kemenag snapshots. Distinguish original QUL resources from Tanzil mirrors. Publish only when the source-specific terms and representation support it; represent blocked resources as tested withheld candidates rather than invented content.
6. Extend identity-based reader alignment/audio behavior, schemas, source QA and font checks for new scripts. A missing mapping must result in an explicit unavailable optional layer, never guessed verse pairing.
7. Run data and reader regressions, both gate profiles, immutable-byte comparison, legacy parity and the generated Astro site checks. Independently review the source decisions and final diff; fix material findings and rerun affected checks.

## Ownership

- **repo_audit (Luna Max):** Arabic/translation pipeline and snapshots, shared config/CDN/provenance/licensing/schema integration and final build. Owns shared metadata files.
- **site_audit (Luna Max):** new transliteration adapter/registry modules and owned snapshots/tests, reader behavior and font checks. Sends shared-file changes as integration specifications to repo_audit.
- **quran_sources (Sol High):** targeted primary-source decisions for Arabic and translation additions.
- **transliteration_research (Sol High):** exact transliteration source/format/rights decisions.
- **recommendation_review / architecture_research (Sol High):** bounded independent source/correctness review when candidates are ready.
- **root (Astra):** scope, plan, coordination and delivery synthesis only.

## Regression requirements

- Missing/duplicate/out-of-order chapter or verse IDs, incomplete corpora, wrong chapter joins and invalid source revisions must fail import/validation.
- Mapped readings may repeat a Hafs ID across adjacent split verses; each individual mapping remains unique and ordered, with valid coverage.
- Unknown/restricted rights remain visible; default publication does not silently promote them to granted.
- New recitation identities must not enable incompatible Hafs-indexed ayah audio.
- New Arabic code points must be supported by a bundled, appropriately licensed font before the generated reader advertises that edition.
- Generated counts, links and edition selectors derive from the actual build profile.

## Completion

Deliver a per-candidate matrix identifying actual snapshots, published IDs, source grants, validation evidence, duplicate handling and any remaining external blocker. A registered withheld candidate must never be described as a published corpus addition.

## Evidence-driven scope refinements

- The pinned Korean Rowwad SQLite archive contains 1,955 blank translations. Preserve the acquired source and its provenance, but withhold this edition from every public build unless a complete official replacement is verified. A rights override cannot bypass completeness.
- Duri Al-Fatiha maps its seven native verses to Hafs `[2,3,4,5,6,7,7]`. Preserve this exact declared exception. Display the source's separate basmala as explicit unnumbered chapter-1 furniture, without creating a verse, translation join or audio position. Do not infer furniture applicability for other chapters.
- Native Arabic chapter counts govern navigation and resume; canonical Hafs counts continue to validate optional layers. Test Duri 9:130 and reject Duri 2:286.
- Turkish transliteration may be acquired and validated privately; it remains excluded from committed/public corpora. QUL registrations and manual import support do not count as acquired corpora without official exports.
