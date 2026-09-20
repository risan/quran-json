# Corpus expansion roadmap

Status: implemented and verified locally. No merge or deployment.

| # | Child | Route | After | Conflicts | Covers | Status |
|---|---|---|---|---|---|---|
| 1 | work/arabic-translations/ — Arabic/translation editions and shared integration | bounded-change | — | 2: config/CDN/provenance edits are applied by owner 1; builds serialized | 1, 2, 3, 6, 7 | planned |
| 2 | work/transliteration-reader/ — transliteration support and new-script reader behavior | bounded-change | — | 1: same shared integration boundary | 1, 3, 4, 5, 6, 7 | planned |

Source decisions are dependencies of publishing each edition, not reasons to stop independent adapter, validation or reader work. The user already authorized implementation. No merge or deployment is included; local completion evidence will be recorded separately.

## Local outcome

Child 1 is implemented and reviewed GO: two Arabic editions and seven complete translations added; the eighth translation is acquired, provenance-recorded and withheld because its official source is incomplete. Child 2 is implemented with passing reader/browser checks and final transliteration review GO. See [delivery.md](delivery.md) for actual candidate dispositions and validation evidence. The roadmap rows retain their unmerged status because this task authorizes local work only.
