# Quran modernization — roadmap

Status: ready

| # | Child | Route | After | Conflicts | Covers | Status |
|---|---|---|---|---|---|---|
| 1 | work/data-contracts/ — data discovery/contracts and research shortlist | bounded-change | — | 2: generated output during integrated build; serialize builds | 1, 2, 3, 4, 7, 9 | planned |
| 2 | work/static-site/ — Astro/Tailwind documentation and build | bounded-change | — | 3: shared CSS contract; owner 2 owns web/assets, owner 3 web/app | 4, 5, 6, 7, 8 | planned |
| 3 | work/reader/ — correct, accessible reader | bounded-change | — | 2: shared style/build integration; no overlapping source ownership | 5, 6, 8, 9 | planned |

## Local delivery

Implementation is authorized locally. No commit, push, PR or deployment is required. Rows stay planned until merged under the skill's status convention; local completion evidence is recorded below rather than claiming a merge.

All three slices are implemented and verified locally. See [delivery.md](delivery.md) for the final checks, preview instructions and evidence. No merge was performed.

## Research decision

No newly researched corpus has sufficient verified source-specific rights and validation to ingest in this pass. Record the shortlist, keep existing publication gates, and implement the independently justified site and contract improvements.
