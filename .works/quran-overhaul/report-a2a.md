# Track A2a report (D2, D6, D13)

Merged into `overhaul/quran-json-v5` from `worktree-agent-ae7a36cba123b13d8`.

## Scripts

| Script | Source | Verses | Verse ids | Result |
|---|---|---|---|---|
| `qpc-hafs` | Quranpedia mushaf 2, dump 2026-09-30 | 6,236 | hafs | added |
| `shubah` | mushaf 9, dump 2026-09-30 | 6,236 | hafs | added, `group: specialist` |
| `susi` | mushaf 10, dump 2026-10-01 | 6,217 | mapped | added, `group: specialist` |
| `bazzi` | mushaf 5 | 6,221 | — | skipped: Al-Jinn (72) Hafs map is non-monotonic |
| `qunbul` | mushaf 8 | 6,221 | — | skipped: same defect |

- `qpc-hafs` carries the basmala only as 1:1 (like `hafs-nastaliq`); noted in the manifest.
- Amiri covers all three new scripts. `shubah` has `audio.per_ayah: false`.
- Duri has 31 ayahs in al-Mulk (splits Hafs 67:9), Susi 30. Unresolved which matches print.
- The live Duri dump hash differs from the pin (`f6024036…` → `c9432307…`) with identical
  verses; refresh the pin so `fetch --check` stays green.

## Kemenag spacing (33 corrections in `qa.KEMENAG_SPACING`)

A boundary is corrected only when Tanzil Uthmani 1.1, QPC Hafs and KFGQPC Nastaleeq agree and
the letter at the break is non-connecting, so no rasm changes. Applied at build time; the
snapshot stays as served. 26 insertions, 7 removals; each fails the build if LPMQ fixes it.

## Audio (`/audio/reciters.json`, 597 entries)

Every entry has `reading` and `content` (`recitation` | `translation`); ayah-scope entries have
`verse_ids` (`hafs` | null). EveryAyah: 70 Hafs, 3 Warsh (verse_ids null), 8 translation
folders; added `Minshawy_Teacher_128kbps` and `Nabil_Rifa3i_48kbps` after HEAD checks.
MP3Quran readings come from the moshaf name (matches `rewaya_id`).

## Open

- Bazzi/Qunbul need Quranpedia to fix the Al-Jinn map (owner may email quranpedia.help@gmail.com).
- Report the Kemenag slips to LPMQ.
