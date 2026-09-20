# Quran dataset, documentation, and reader modernization

Status: ready
Type: feature
Route: initiative — corpus expansion, data architecture, and the public reading experience are distinct workstreams.
Next: decompose, then implement and verify locally

## Request

Find widely adopted Quran scripts and translations missing from this repository; explain and identify language-specific transliterations. Propose code efficiency, JSON and directory structure improvements, simpler documentation, and an elegant, readable, fast homepage and reader. Evaluate Astro with Vue or React and Tailwind. Use Astra only for orchestration/planning, Sol High for deep reasoning/research, and Luna Max for exploration/implementation.

## Goal

Produce a repository-grounded and source-linked audit, then implement the justified data-contract, documentation, and reader improvements locally. Distinguish verified facts, recommendations, and unresolved source or redistribution questions.

## Target

- Repository datasets, generators, validation, package outputs, and public JSON contracts.
- `README.md` and the documentation at <https://quran-json.risanb.com/>.
- The Quran reader at <https://quran-json.risanb.com/app/>.

## Acceptance criteria

- [ ] Inventory existing Arabic editions, translations, and transliterations with repository evidence.
- [ ] Identify worthwhile missing Arabic editions and translations with primary sources, availability, and reuse status.
- [ ] Explain whether transliteration is defined per language and assess actual candidate corpora separately from abstract schemes.
- [ ] Propose concrete code, data schema, and directory improvements while accounting for existing consumers.
- [ ] Audit the live homepage and reader, distinguishing observed behavior from source-based inference.
- [ ] Recommend a frontend architecture and visual/interaction direction with testable performance and accessibility criteria.
- [ ] Provide a prioritized sequence and document questions that must be resolved before corpus ingestion or migration.
- [ ] Implement and verify an elegant, accessible static documentation site and reader with preserved data and reader contracts.
- [ ] Implement justified data-contract and efficiency improvements with meaningful regression coverage; ingest new editions only where provenance, redistribution, and verse alignment can be verified.

## Out of scope for this pass

- Publishing, deployment, contacting corpus owners, or changing remote resources.
- Unverified additions or transformations of Quran text.

## Assumptions

- Existing dataset paths and consumer behavior should remain compatible unless a versioned migration is explicitly chosen.

## Questions

- Q: Audit and proposal only, or also implement locally? — A: User explicitly selected “Audit, then implement locally.”
