# Add the shortlisted Quran editions

Status: ready
Type: feature
Route: initiative — Arabic editions, translations and transliteration resources have distinct acquisition and alignment contracts
Next: implement the bounded workstreams in implementation-plan.md

## Request

“So? Let's add all those best next candidates then!” — following the modernization audit and implementation.

## Goal

Add the shortlisted editions to the repository's data pipeline and generated catalog where verified source terms and complete validated data allow it. Provide concrete, tested candidate/import support with truthful status for any resource whose acquisition or publication remains unresolved.

## Target

- Arabic: Quranpedia al-Duri and Hafs Nastaliq, with distinct identities from current editions.
- Translations: QuranEnc Bengali Zakaria and Rowwad, Malay Basmeih, modern Russian Rowwad, Korean Hamid Choi and Rowwad, Italian Rowwad and Ukrainian Yakubovych.
- Transliteration: existing Kemenag Latin, Tanzil English and Turkish, and distinct QUL resources 71, 469, 475 and 478; deduplicate mirrored editions.
- Existing provenance/licensing gates, schemas, generated documentation, reader alignment, fonts and audio behavior.

## Acceptance criteria

- [ ] Every named candidate has an explicit implemented outcome: published addition, existing supported edition, deduplicated alias, or a concrete withheld candidate with its blocker recorded.
- [ ] New publishable Arabic and translation snapshots are complete, attributed, versioned, checksum-recorded and covered by semantic validation.
- [ ] Source terms are evaluated consistently with equivalent existing editions; speculative concerns are distinguished from explicit restrictions.
- [ ] Transliteration metadata preserves scheme/audience/purpose/granularity and actual corpus rights without fabricating a grant or pronunciation authority.
- [ ] The reader handles new Arabic numbering, optional-layer alignment, font eligibility and audio restrictions correctly.
- [ ] Existing immutable payloads and frozen npm dist remain unchanged, default gates remain truthful, and both build profiles are tested.
- [ ] Final generated site/catalog, tests and a per-candidate delivery matrix demonstrate what was actually added.

## Out of scope

- Remote publication, deployment, or contacting rights holders.
- Additional later-priority languages, other riwayat, CLDR generation or new phonetic products beyond the shortlist.

## Assumptions

- The user authorizes local source acquisition and implementation; explicit third-party restrictions are preserved rather than represented as permission.
- Existing override behavior remains available, with its actual unknown/restricted statuses. The request does not establish new third-party grants.
