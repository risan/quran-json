# Track A2b report: more translations (decision D11)

Branch `worktree-agent-ad36859f28b66925f`, based on `overhaul/quran-json-v5` (fast-forwarded).
All fetches were made on 2026-10-01.

## Result

| | Before | After |
|---|---|---|
| Published translations | 90 | **130** |
| Languages (distinct `code` in `translations/index.json`) | 62 | **81** |
| Withheld (public `withheld` arrays) | 1 | **3** (`korean_rwwad`, `circassian_rwwad`, `english_waleed`) |
| QuranEnc published | 82 | 118 (75 list + 43 supplemental) |
| Public-domain / author-granted extras | 8 | 12 |
| Site files / largest file | 11,988 (README figure) | 16,359 / 13.1 MB (`bn-zakaria`; limits 20,000 files, 25 MiB) |

## Editions added (QuranEnc, 36)

All 36: 6,236 rows, 0 empty, verse ids 1..n in every chapter. Checked by
`quranenc.validate_translation` at fetch time and again by a separate script. The URL key is
`{code}-{translator}`; there is no collision (the build raises on one).

32 from the SQLite ZIP (supplemental route; archive sha256 and byte count pinned):
`ankobambara_foudi` (nqo), `bosnian_korkut` (bs), `bulgarian_translation` (bg),
`chichewa_betala` (ny), `chinese_mayolong` (zh), `dagbani_ghatubo` (dag),
`dari_badkhashani` (prs), `french_hameedullah` (fr), `georgian_rwwad` (ka),
`german_aburida` (de), `greek_rwwad` (el), `hebrew_darussalam` (he), `iranun_sarro` (ilp),
`kannada_bashir` (kn), `kazakh_altai` (kk), `kurdish_salahuddin` (ku),
`kurmanji_ismail` (kmr), `luganda_foundation` (lg), `luhya_center` (luy),
`malagasy_rwwad` (mg), `marathi_ansari` (mr), `nepali_central` (ne), `pashto_sarfaraz` (ps),
`pashto_zakaria` (ps), `russian_aboadel` (ru), `shona_institute` (sn),
`swahili_abubakr` (sw), `tajik_khawaja` (tg), `thai_complex` (th), `uzbek_sadiq` (uz),
`vietnamese_hassan` (vi), `yaw_silika` (yao).

4 through the new API ingest: `belarusian_krivtsov` (be), `chinese_suliman_modern` (zh),
`oromo_rwwad` (om), `zulu_adel` (zu). Footnotes are kept (oromo: 1,122 verses carry them,
zulu: 159). All 6,236 rows of each (text and footnotes) are identical to the researcher's
independent crawl of the same endpoint.

New language codes (19; ISO 639-1 where one exists, else 639-3): be, bg, ny, dag, prs, ka,
el, he, ilp, kk, kmr, lg, luy, mg, mr, ne, sn, yao, zu. QuranEnc gives no language code for
keys outside its list endpoint, so `ilp` (Iranun, Philippines), `prs` (Dari) and `kmr`
(Kurmanji) are my choices from the titles. Directions come from the script of the text:
Dari, both Pashto, Sorani Kurdish, Kurmanji (it is written in Arabic script), Hebrew and
N'ko are rtl.

Versions come from the QuranEnc homepage cards (re-read today, identical to the
researcher's). The per-surah API response carries no version, so an API-only edition's
version is its catalogue entry's.

### API ingest

`quranenc.py`: `SURA_URL`, `parse_sura` (row-level validation) and `api_gatherer(key)` for
`FetchTask.gather`. Catalogue entries get `"ingest": "api"` (validated: a `{sura}` URL
pattern is required and no archive hash may be pinned). `validate_translation` runs over the
assembled 114 surahs, so a partial surah, a gap, a renumbered surah, an empty result, a
non-JSON or 403 body, a wrong-surah row, a duplicate verse, or a non-string text or
footnote fails the whole import before anything is written. Covered by
`tests/test_quranenc_api.py` (no network). `fetch --check` re-crawls them like any other
snapshot, and the live check below found no difference. The path is reliable enough to ship.

## Updates

| Edition | Version | Rows changed |
|---|---|---|
| `vietnamese_rwwad` | 1.0.8 -> 1.0.9 | 122 |
| `moore_rwwad` | 1.0.1 -> 1.0.2 | 2,616 |
| `korean_hamid` | 1.0.3 -> 1.0.4 | 9 |

`catalogue.json` differed from the live list only in those two versions. The changes are
recorded in `data/meta/drift.json` (a new file). I replaced the three snapshots rather than
running `fetch --force`, which would have refetched all ~150 snapshots.

## Kept withheld

`circassian_rwwad` (1,000 empty, v1.0.1), `english_waleed` (3,753 empty, v1.0.2),
`korean_rwwad` (1,955 empty). Registered in `supplemental.json` with `availability:
"withheld"`, a reason and `allow_empty`. They appear in the `withheld` arrays of
`translations/index.json` and `meta/sources.json`, and in no public directory.
`circassian_rwwad` is coded `ady` (Adyghe), a guess; the code is not published for withheld
editions.

## Public-domain editions

| Key | Source | Translator d. | Evidence cited in the licence text |
|---|---|---|---|
| `english_rodwell` (en-rodwell) | fawazahmed0 `eng-johnmedowsrodwe` | 1900 | en.wikipedia John_Medows_Rodwell |
| `urdu_kanzuliman` (ur-kanzuliman) | Tanzil `ur.kanzuliman` (2011-03-17) | 1921 | en.wikipedia Ahmed_Raza_Khan_Barelvi |
| `urdu_mahmudulhasan` (ur-mahmudulhasan) | fawazahmed0 `urd-mahmoodulhassan` (dailyayat.com) | 1920 | en.wikipedia Mahmud_Hasan_Deobandi |
| `dutch_keyzer` (nl-keyzer) | fawazahmed0 `nld-salomokeyzer` (Tanzil `nl.keyzer`) | 1868 | nl.wikipedia Salomo_Keyzer |

Status `granted`; text "Public domain. ... Translator died YYYY (URL), so out of copyright
...". Death years come from Wikipedia only (Rodwell 1808-1900; Ahmed Raza Khan 28 Oct 1921;
Mahmud Hasan 1851-1920; Keyzer 25 Feb 1868), not from a primary record. Each edition has
6,236 non-empty verse-aligned rows, and 1:1-1:7, 2:255 and 112:1-4 were read for each
(Rodwell 1:1 "In the Name of God, the Compassionate, the Merciful"; Keyzer 112:1 "Zeg: God
is een eenig God").

- **Rodwell:** the "returns 403" claim lived in `licensing-review.json`, which an earlier
  cleanup deleted, so there is nothing left to correct. The file fetches fine.
- **Kanzul Iman:** tanzil.net's TLS certificate has expired, so the verified client cannot
  fetch it (curl exit 60). I seeded the snapshot from the researcher's file, which is
  byte-identical (sha256 `b946a407...af801`) to what `curl -k` returns today, and pinned that
  hash as `source_sha256` (`PINNED_EXTRA_SOURCES`). Added `kind="tanzil"` (parser
  `tanzil.parse_text`).
- **Mahmud ul Hasan:** the markers are `[n]` with Persian digits (`[۱]`, `[۱۲]`, `[۱۲۳]`,
  rarely `[n/m]`); 5,097 verses carried them. They are stripped at import
  (`sources.strip_footnote_markers`, edition list `FOOTNOTE_MARKER_EDITIONS`). The source also
  has mangled markers, stripped too: `]۲۳۲]` (4:171), `[ا]` (60:1), `[۰ا]` (91:11), a bare
  `۴` inside a word (72:2) and a lone `[` left at the start of 4:171. The translator's
  bracketed glosses (`[قصاص]`, `[ناحق]`, `[فریب]`) stay. The source's old spellings
  (2:255 "نہں") and an upstream bracket typo (`[کھلے)`, 13:22) are left alone.
- **Keyzer:** research listed 2:1, 3:1, 20:1, 26:1 and 28:1-32:1. Project Gutenberg #19786,
  checked chapter by chapter, shows the same lost-leading-letters defect also at 7:1, 12:1,
  13:1, 14:1, 15:1, 19:1 and 27:1, so 16 verses are restored (`qa.KEYZER_CORRECTIONS`, with
  an evidence URL on each, published in `data/meta/qa.json`). The restored text is
  Gutenberg's reading (`A. L. M.`, `T. S. M.`, `E. L. R.`, `C. H. Y. A. S.`). New
  `Correction.at_start` makes a correction match only at the start of a verse, so a repaired
  verse fails the build instead of being corrected twice (a bare `M` would otherwise match
  any text containing an M). Caveat: Gutenberg's edition and Tanzil's wording differ in
  places (1:1 "barmhartigen" vs "albarmhartigen"), so Gutenberg is a witness for the opening
  letters, not proof that the two texts are one printing.

Other code change: `config.Edition.direction` (Urdu is rtl; the catalogue only describes
QuranEnc editions), used by `cdn.py`.

## Live upstream check

`uv run quran-json fetch --check` was run after the final data commit. It reported no
difference for any of the 36 new editions (including the four API crawls), the three updated
editions, or the Rodwell, Mahmud ul Hasan and Keyzer sources. It did report, none of them from
this track:
- every Tanzil snapshot, plus `urdu_kanzuliman`: ERROR, expired certificate;
- `data/kemenag/quran.json`: 1 of 6,236 records differs;
- `quranpedia` warsh, qalun, hafs-nastaliq, duri: dump version or hash mismatch (scripts track).

## Open issues

- Tanzil's expired certificate blocks refetching the six Arabic variants, the chapter
  metadata and Kanzul Iman until it is renewed.
- Language codes `ilp`, `prs`, `kmr`, `ady` are inferred; confirm with a native reader.
- Death years rest on Wikipedia.
- README: I updated only the numbers I touched (130/118/43/12 editions, 16,359 files,
  largest file 13 MiB). Its "explicit unverified-licence profile" wording is stale since A1.
- `tests/site/homepage-regressions.mjs` hard-codes the translation count; updated to 130, not
  run (needs a browser).
- 16,359 of 20,000 files; the scripts and audio track will add more.

## Test results (final commit)

- `uv run pytest`: pass (2 skipped, the assembled-site tests that need `npm run site`)
- `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`: pass
- `uv run quran-json verify`: provenance ok (152 snapshots)
- `uv run quran-json cdn --out /tmp/qj-a2b`: built; `manifest.json` reports 130 translations,
  81 languages; three withheld.
