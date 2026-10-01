# Cross-check results

Output of `uv run quran-json crosscheck` (module `quranjson.crosscheck`, decision D14),
run on 2026-10-01 against the committed snapshots. Witnesses are downloaded into
`.cache/crosscheck/`; residual vocalised differences are in `.cache/crosscheck/<script>.tsv`
(not committed). Reproduce with the same command (network needed; not part of CI).

## How to read the table

- **raw**: NFC text, leading and trailing whitespace ignored, otherwise byte for byte.
- **vocalised**: letters and vowel marks after the reviewed encoding-equivalence table (listed
  below). Word spacing is ignored at this level and counted separately in the **spacing**
  column (verses that agree vocalised but split words differently).
- **skeleton**: consonant letters only (marks, signs, alef dropped; hamza seats folded:
  ؤ to و, ئ to ي, bare hamza dropped). Strictest test that is blind to encoding conventions.
- **chapters = skeleton**: chapters whose whole text (verse boundaries ignored, leading
  basmala ignored) agrees at skeleton level.
- Percentages are floored to one decimal, so 100.0% always means every unit agrees.
- Warsh, Qalun and Duri use their own verse numbers; the fawazahmed0 copies were renumbered to
  Hafs, so those rows compare per chapter (`unit = chapter`), as the research did. For
  `indopak`, chapter 1 (basmala unnumbered, so every verse is shifted by one against Hafs) is
  left out of the verse counts (6,229 of 6,236) and covered by the chapter column only.
- Verse 1 of chapters 2-114 is compared with the basmala prefix removed from both sides.

## Encoding-equivalence table (vocalised level)

Each row is a pure encoding choice that the unit tests prove is treated as equal. Deliberately
not folded: alef wasla vs plain alef, dagger alef vs full alef, hamza seats, and different
vowels in the same position (all are reported).

- tatweel, zero-width, bidi and word-joiner controls, no-break and hair spaces: layout, not text.
- pause, rub el hizb and sajdah signs (U+06D6-06DC, U+06DE, U+06E9): editions place and encode
  them differently.
- KFGQPC sukun U+06E1 vs round silent sign U+0652 (Tanzil: U+0652 sukun, U+06DF circle).
- space after an open tanween before a lone alef or alef maksura (KFGQPC writes the tanween
  on the preceding letter).
- open tanween U+08F0-08F2, U+0656, U+0657, U+065E vs the standard tanween code points.
- alef maksura, Farsi yeh, yeh barree, keheh, heh goal vs the Arabic letters.
- hamza and madda order on alef; Tanzil's fatha before a hamza-alef pair.
- tanween vs the matching single haraka, only in a word that carries an iqlab small meem
  (U+06E2 or U+06ED): Tanzil writes أَلِيمٌۢ, KFGQPC أَلِيمُۢ. Revised 2026-10-01: the first
  version folded every tanween to its haraka everywhere, which would have hidden a lost tanween
  (`كِتَابٌ هُوَ` vs `كِتَابُ هُوَ`). Measured against the real witnesses the blanket fold was
  hiding exactly 338 words (Tanzil Uthmani vs KFGQPC and DigitalKhatt), every one an iqlab
  word before baa, so the restricted fold leaves every count in this file unchanged; mutation
  tests now require a tanween lost elsewhere to be reported.
- word spacing (ignored below raw, counted in the spacing column).

## Interpretation

Nothing in these runs points at a wrong word in any script.

| Script | Result | What the residue is |
|---|---|---|
| `uthmani` | skeleton 100% against Tanzil today, KFGQPC Hafs (two copies), DigitalKhatt Madina and Khaled Hosny; 99.9% (6,234/6,236) against alquran.cloud | alquran.cloud is Tanzil 1.0.x and lacks the 12:39 and 12:41 fix from Tanzil 1.1. Vocalised against KFGQPC 98.0% (6,113/6,236): dabt conventions only (fatha on a hamza-alef pair 62, round silent sign vs sukun 33, small high madda 26, hamza below 14, ئ vs ي 13) |
| `simple` | skeleton 6,233/6,236 against Quranpedia Imlaei and alquran.cloud; 6,230/6,236 against Wikisource | the three Tanzil 1.1 spellings (5:31, 17:32, 39:56) plus three spacing or spelling choices in Wikisource. Vocalised differs everywhere because Imlaei marks assimilation differently (shadda vs sukun), which the table deliberately does not hide |
| `uthmani-min` | byte-identical to Tanzil today; skeleton 6,234/6,236 and vocalised 5,931/6,236 against alquran.cloud | alquran.cloud is Tanzil 1.0.x (same origin): hamza on alef written as separate hamza (215+62) and small-vowel encodings (U+06E7 vs U+06E6, 34). Registered 2026-10-01; no independent witness exists for the minimal variant |
| `simple-plain` | byte-identical to Tanzil today | registered 2026-10-01; no mirror carries this variant, so Tanzil itself is the only witness |
| `simple-min` | byte-identical to Tanzil today; skeleton and vocalised 6,233/6,236 against alquran.cloud | the same three Tanzil 1.1 spellings. Registered 2026-10-01 |
| `simple-clean` | byte-identical to Tanzil today; skeleton 6,233/6,236 against Quranpedia Imlaei | the same three verses |
| `kemenag` | 6,235/6,236 identical to the 2025 scrape of the same API; skeleton 6,226/6,236 against KFGQPC Hafs | the 10 rasm conventions of the Indonesian standard recorded in the research; vocalised against KFGQPC is not meaningful (different tradition and dabt) |
| `indopak` | skeleton 6,219/6,229 verses against KFGQPC Nastaleeq | alef spelling (full vs dagger alef) and hamza seats; 10 verses (the research's L4 count for the same pair was 6,219/6,236, which includes the 7 Al-Fatiha verses left out here) |
| `hafs-nastaliq` | byte-identical to a fresh Quranpedia dump; skeleton 100% against KFGQPC via fawazahmed0 | encoding of Nastaleeq marks only |
| `warsh`, `qalun`, `duri` | byte-identical to fresh Quranpedia dumps; skeleton 114/114 chapters against KFGQPC via fawazahmed0 | vocalised 76%, 84%, 39% of chapters against the mirror: yeh in place of hamza-on-yeh (ئ vs ي, 20 in Warsh) and other mark encodings in the mirror, not letter differences |
| `shubah`, `susi` | byte-identical to fresh Quranpedia dumps; skeleton 114/114 chapters against KFGQPC via fawazahmed0 | vocalised 97% and 42% of chapters: the mirror's encoding of small high marks (592 U+06ED vs U+065C in Susi) |
| `qpc-hafs` | byte-identical to Quranpedia mushaf 2; skeleton 100% and vocalised 6,234/6,236 against KFGQPC Hafs v13 via fawazahmed0 | two dabt encodings (2:72 hamza with sukun vs U+0654; 11:41 small high mark U+06EA vs U+065C), see `qpc-hafs.tsv`; reproduces the research's 6,234/6,236 |

Independence: every witness other than Wikisource descends from Tanzil or KFGQPC (the table
printed under each script says which). Agreement proves nobody corrupted a copy; it cannot
detect an error made by KFGQPC or Tanzil themselves.

## Deviations from the research numbers (`run_all.out`)

- **Same as research**: Tanzil snapshots byte-identical (6,236/6,236); `uthmani` vs KFGQPC
  letters 114/114 and skeleton 6,236; alquran.cloud 6,234; Khaled Hosny 114/114; Quranpedia
  Imlaei 6,233 and 111/114 chapters; Wikisource 108/114 chapters; Kemenag scrape 6,235 and
  Kemenag vs KFGQPC 6,226; Nastaleeq 114/114; Quranpedia riwayat dumps byte-identical; riwayat
  vs KFGQPC 114/114; three word-spacing differences between Tanzil and KFGQPC.
- `uthmani` vs Quranpedia mushaf 2 vocalised: 6,113 here, 6,112 in the research. The table
  here has two additions (Farsi yeh and related letters, and the space after an open tanween);
  one verse moved.
- The research's 6,234/6,236 for Quranpedia mushaf 2 vs the fawazahmed0 KFGQPC copy compared
  the two witnesses with each other. This tool compares witnesses with our snapshots, but
  `qpc-hafs` is that same Quranpedia text, so its fawazahmed0 row reproduces 6,234/6,236.
- Raw counts differ by one in places (alquran.cloud 1,876 vs 1,877) because the research's L0
  also removed zero-width characters and tatweel; raw here does not.
- Not ported: the published-site check (`tanzil_verbatim.py` also fetched chapters from
  quran-json.risanb.com), the QuranWBW Indopak comparison (its licence forbids redistribution
  and its data lives in git history), the Bazzi and Qunbul riwayat (not shipped yet), the Quranpedia
  changes feed, and the Kemenag word-segmentation and `updated_at` analysis.
- tanzil.net's certificate was expired when this was run (as in the research), so its two
  witnesses are fetched without certificate verification; they only feed a read-only comparison.

## Full output

```text
## uthmani
witness                unit     compared     raw  vocalised  skeleton  spacing  chapters = skeleton
---------------------------------------------------------------------------------------------------
tanzil-uthmani         verse        6236  100.0%     100.0%    100.0%        0        114/114      
qp-2                   verse        6236    0.8%      98.0%    100.0%        3        114/114      
faw-quranuthmanihaf    verse        6236    0.8%      98.0%    100.0%        4        114/114      
alquran-uthmani        verse        6236   30.0%      42.0%     99.9%        1        113/114      
digitalkhatt-madina    verse        6236   23.3%      99.9%    100.0%        0        114/114      
faw-qurankhaledhosn    verse        6236    0.4%      49.5%    100.0%        0        114/114      
  tanzil-uthmani: tanzil.net uthmani, today. Ancestry: Tanzil itself. A refresh check: shows our snapshot is verbatim, not a second opinion on the text.
    identical units raw/skeleton/vocalised of 6236: 6236/6236/6236
  qp-2: Quranpedia mushaf 2 (KFGQPC Hafs). Ancestry: KFGQPC Hafs v13 via Quranpedia; same origin as the fawazahmed0 copy (vocalised 6,234/6,236 identical to it in the research).
    identical units raw/skeleton/vocalised of 6236: 54/6236/6113
         62  [064E] -> []
         33  [06DF] -> [0652]
         26  [] -> [06E4]
         14  [] -> [0655]
         13  [0626] -> [064A]
          1  [] -> [0670 0621]
  faw-quranuthmanihaf: KFGQPC Hafs Uthmanic (fawazahmed0 ara-quranuthmanihaf). Ancestry: KFGQPC Hafs v13, Uthmanic script via the fawazahmed0 mirror on jsDelivr
    identical units raw/skeleton/vocalised of 6236: 54/6236/6112
         62  [064E] -> []
         33  [06DF] -> [0652]
         26  [] -> [06E4]
         14  [] -> [0655]
         13  [0626] -> [064A]
          1  [0652] -> []
  alquran-uthmani: alquran.cloud quran-uthmani. Ancestry: Tanzil 1.0.x, before the 2021-02-12 Tanzil 1.1 fix at 12:39 and 12:41. Same origin as Tanzil: tests the mirror, not the text.
    identical units raw/skeleton/vocalised of 6236: 1876/6234/2621
       2617  [064B] -> [064E 06ED]
       1863  [064D] -> [0650 06E2]
       1708  [064C] -> [064F 06ED]
        380  [] -> [06ED]
        281  [064B] -> [064E]
        276  [0654] -> [0621 064E]
  digitalkhatt-madina: DigitalKhatt quran_text_madina.ts. Ancestry: Tanzil's Uthmani text re-encoded for DigitalKhatt's font (it even keeps Tanzil's three word-spacing choices). Not independent of Tanzil.
    identical units raw/skeleton/vocalised of 6236: 1454/6236/6233
          1  [06EA] -> [065C]
          1  [06EB] -> [06EC]
          1  [06E5] -> []
          1  [] -> [08F3]
  faw-qurankhaledhosn: Khaled Hosny quran-data (fawazahmed0 ara-qurankhaledhosn). Ancestry: Khaled Hosny's quran-data, itself taken from Tanzil. Not independent of Tanzil.
    identical units raw/skeleton/vocalised of 6236: 28/6236/3089
       2741  [0622] -> [0627 06E4]
       2122  [0653] -> [06E4]
        686  [] -> [0655]
        308  [0653 0626] -> [06E4 064A]
        204  [0622 0626] -> [0627 06E4 064A]
        173  [0626] -> [064A]
  residual differences: <repo>/.cache/crosscheck/uthmani.tsv

## simple
witness                unit     compared     raw  vocalised  skeleton  spacing  chapters = skeleton
---------------------------------------------------------------------------------------------------
qp-1                   verse        6236    0.0%      36.8%     99.9%        0        111/114      
faw-quranspelled       verse        6236   24.5%      25.6%     99.9%        0        108/114      
alquran-simple         verse        6236   27.8%      36.8%     99.9%        0        111/114      
  qp-1: Quranpedia mushaf 1 (Imlaei). Ancestry: Quranpedia's Imlaei text, corrected by its team. Compare with Tanzil Imlaei.
    identical units raw/skeleton/vocalised of 6236: 0/6233/2301
       6968  [] -> [0652]
       3766  [0651] -> []
          3  [064A 0670] -> [0627]
  faw-quranspelled: Wikisource Imlaei (fawazahmed0 ara-quranspelled). Ancestry: Wikisource's Imlaei transcription: an independently typed text, so the only witness here that does not descend from Tanzil or KFGQPC.
    identical units raw/skeleton/vocalised of 6236: 1528/6230/1601
       6966  [] -> [0652]
       3760  [0651] -> []
       3211  [0670] -> []
          4  [0651 0670] -> []
          3  [064A 0670] -> [0627]
          1  [0627 0627] -> []
  alquran-simple: alquran.cloud quran-simple. Ancestry: Tanzil 1.0.x (Imlaei). Same origin as Tanzil.
    identical units raw/skeleton/vocalised of 6236: 1737/6233/2301
       6968  [] -> [0652]
       3766  [0651] -> []
          3  [064A 0670] -> [0627]
  residual differences: <repo>/.cache/crosscheck/simple.tsv

## uthmani-min
witness                unit     compared     raw  vocalised  skeleton  spacing  chapters = skeleton
---------------------------------------------------------------------------------------------------
tanzil-uthmani-min     verse        6236  100.0%     100.0%    100.0%        0        114/114      
alquran-uthmani-min    verse        6236   54.0%      95.1%     99.9%        3        113/114      
  tanzil-uthmani-min: tanzil.net uthmani-min, today. Ancestry: Tanzil itself. A refresh check, not a second opinion.
    identical units raw/skeleton/vocalised of 6236: 6236/6236/6236
  alquran-uthmani-min: alquran.cloud quran-uthmani-min. Ancestry: Tanzil 1.0.x, minimal-marks Uthmani. Same origin as Tanzil: tests the mirror, not the text.
    identical units raw/skeleton/vocalised of 6236: 3368/6234/5931
        215  [0654] -> [0621]
         62  [0654] -> [064E 0621]
         34  [06E7] -> [06E6]
          4  [] -> [06E6]
          4  [06E7] -> []
          2  [] -> [064A]
  residual differences: <repo>/.cache/crosscheck/uthmani-min.tsv

## simple-plain
witness                unit     compared     raw  vocalised  skeleton  spacing  chapters = skeleton
---------------------------------------------------------------------------------------------------
tanzil-simple-plain    verse        6236  100.0%     100.0%    100.0%        0        114/114      
  tanzil-simple-plain: tanzil.net simple-plain, today. Ancestry: Tanzil itself. A refresh check, not a second opinion.
    identical units raw/skeleton/vocalised of 6236: 6236/6236/6236
  residual differences: <repo>/.cache/crosscheck/simple-plain.tsv

## simple-min
witness                unit     compared     raw  vocalised  skeleton  spacing  chapters = skeleton
---------------------------------------------------------------------------------------------------
tanzil-simple-min      verse        6236  100.0%     100.0%    100.0%        0        114/114      
alquran-simple-min     verse        6236   56.3%      99.9%     99.9%        3        111/114      
  tanzil-simple-min: tanzil.net simple-min, today. Ancestry: Tanzil itself. A refresh check, not a second opinion.
    identical units raw/skeleton/vocalised of 6236: 6236/6236/6236
  alquran-simple-min: alquran.cloud quran-simple-min. Ancestry: Tanzil 1.0.x, minimal-marks Imlaei. Same origin as Tanzil.
    identical units raw/skeleton/vocalised of 6236: 3514/6233/6233
          3  [064A 0670] -> [0627]
  residual differences: <repo>/.cache/crosscheck/simple-min.tsv

## simple-clean
witness                unit     compared     raw  vocalised  skeleton  spacing  chapters = skeleton
---------------------------------------------------------------------------------------------------
tanzil-simple-clean    verse        6236  100.0%        n/a    100.0%        0        114/114      
qp-1                   verse        6236    0.0%        n/a     99.9%        3        111/114      
alquran-simple         verse        6236    0.0%        n/a     99.9%        3        111/114      
  tanzil-simple-clean: tanzil.net simple-clean, today. Ancestry: Tanzil itself. A refresh check, not a second opinion.
    identical units raw/skeleton/vocalised of 6236: 6236/6236/-
  qp-1: Quranpedia mushaf 1 (Imlaei). Ancestry: Quranpedia's Imlaei text, corrected by its team. Compare with Tanzil Imlaei.
    identical units raw/skeleton/vocalised of 6236: 0/6233/-
          3  [064A] -> []
  alquran-simple: alquran.cloud quran-simple. Ancestry: Tanzil 1.0.x (Imlaei). Same origin as Tanzil.
    identical units raw/skeleton/vocalised of 6236: 1/6233/-
          3  [064A] -> []
  residual differences: <repo>/.cache/crosscheck/simple-clean.tsv

## kemenag
witness                unit     compared     raw  vocalised  skeleton  spacing  chapters = skeleton
---------------------------------------------------------------------------------------------------
kemenag-2025-scrape    verse        6236   99.9%      99.9%    100.0%        0        114/114      
qp-2                   verse        6236    0.0%       0.3%     99.8%        0        104/114      
  kemenag-2025-scrape: dyazincahya/quran-json-kemenag (2025 scrape). Ancestry: A 2025 scrape of the same Kemenag (LPMQ) API: shows upstream drift, not an independent text.
    identical units raw/skeleton/vocalised of 6236: 6235/6236/6235
          1  [0670] -> []
          1  [] -> [0670]
  qp-2: Quranpedia mushaf 2 (KFGQPC Hafs). Ancestry: KFGQPC Hafs v13 via Quranpedia; same origin as the fawazahmed0 copy (vocalised 6,234/6,236 identical to it in the research).
    identical units raw/skeleton/vocalised of 6236: 0/6226/23
      25060  [0652] -> []
      12593  [0627] -> [0671]
       8617  [] -> [064E]
       7733  [0627] -> [0623]
       4589  [0627] -> [0625]
       4183  [0670] -> []
  residual differences: <repo>/.cache/crosscheck/kemenag.tsv

## indopak
witness                unit     compared     raw  vocalised  skeleton  spacing  chapters = skeleton
---------------------------------------------------------------------------------------------------
faw-quranindopak       verse        6229    0.0%      47.0%     99.8%       37        105/114      
  faw-quranindopak: KFGQPC Hafs Nastaleeq (fawazahmed0 ara-quranindopak). Ancestry: KFGQPC Hafs Nastaleeq v10 via the fawazahmed0 mirror on jsDelivr
    identical units raw/skeleton/vocalised of 6229: 0/6219/2929
       1735  [0653] -> [0658]
       1420  [0627 089C] -> [0622]
       1288  [0622] -> [0627 0658]
        684  [0655] -> []
        490  [06E2] -> [06ED]
        295  [089C 064A] -> [0653 0626]
  residual differences: <repo>/.cache/crosscheck/indopak.tsv

## hafs-nastaliq
witness                unit     compared     raw  vocalised  skeleton  spacing  chapters = skeleton
---------------------------------------------------------------------------------------------------
qp-3                   verse        6236  100.0%     100.0%    100.0%        0        114/114      
faw-quranindopak       verse        6236    0.4%      46.9%    100.0%        0        114/114      
  qp-3: Quranpedia mushaf 3 (KFGQPC Hafs Nastaleeq). Ancestry: KFGQPC Hafs Nastaleeq v10 via Quranpedia; same origin as the fawazahmed0 copy. Our hafs-nastaliq snapshot is this dump: a refresh check.
    identical units raw/skeleton/vocalised of 6236: 6236/6236/6236
  faw-quranindopak: KFGQPC Hafs Nastaleeq (fawazahmed0 ara-quranindopak). Ancestry: KFGQPC Hafs Nastaleeq v10 via the fawazahmed0 mirror on jsDelivr
    identical units raw/skeleton/vocalised of 6236: 30/6236/2925
       3467  [] -> [0615]
        542  [] -> [08D6]
        342  [06E3] -> [06ED]
        230  [] -> [0617]
        147  [] -> [08D5]
        122  [] -> [08DE]
  residual differences: <repo>/.cache/crosscheck/hafs-nastaliq.tsv

## warsh
witness                unit     compared     raw  vocalised  skeleton  spacing  chapters = skeleton
---------------------------------------------------------------------------------------------------
qp-4                   verse        6214  100.0%     100.0%    100.0%        0        114/114      
faw-quranwarsh         chapter       114    5.2%      76.3%    100.0%        4        114/114      
  qp-4: Quranpedia mushaf 4 (Warsh). Ancestry: KFGQPC Warsh v8 via Quranpedia; same origin as the fawazahmed0 copy. Our warsh snapshot is this dump: a refresh check.
    identical units raw/skeleton/vocalised of 6214: 6214/6214/6214
  faw-quranwarsh: KFGQPC Warsh (fawazahmed0 ara-quranwarsh). Ancestry: KFGQPC Warsh v8 via the fawazahmed0 mirror on jsDelivr; verse numbers renumbered to Hafs, so chapter level only.
    identical units raw/skeleton/vocalised of 114: 6/114/87
         20  [0626] -> [064A]
          5  [064E] -> []
          3  [0652] -> []
          3  [064F] -> [064E]
          3  [] -> [0652]
          3  [0651] -> []
  residual differences: <repo>/.cache/crosscheck/warsh.tsv

## qalun
witness                unit     compared     raw  vocalised  skeleton  spacing  chapters = skeleton
---------------------------------------------------------------------------------------------------
qp-7                   verse        6214  100.0%     100.0%    100.0%        0        114/114      
qp-12                  verse        6214  100.0%     100.0%    100.0%        0        114/114      
faw-quranqaloon        chapter       114    6.1%      84.2%    100.0%        5        114/114      
  qp-7: Quranpedia mushaf 7 (Qalun). Ancestry: KFGQPC Qaloon v8 via Quranpedia; same origin as the fawazahmed0 copy. Our qalun snapshot is this dump: a refresh check.
    identical units raw/skeleton/vocalised of 6214: 6214/6214/6214
  qp-12: Quranpedia mushaf 12 (Libyan Awqaf Qalun). Ancestry: Byte-identical to mushaf 7 when last checked: not a second witness.
    identical units raw/skeleton/vocalised of 6214: 6214/6214/6214
  faw-quranqaloon: KFGQPC Qaloon (fawazahmed0 ara-quranqaloon). Ancestry: KFGQPC Qaloon v8 via the fawazahmed0 mirror on jsDelivr; verse numbers renumbered to Hafs, so chapter level only.
    identical units raw/skeleton/vocalised of 114: 7/114/96
         20  [0626] -> [064A]
          1  [0621 0652] -> [0654]
          1  [] -> [064E 06EC]
          1  [0651] -> []
          1  [064E] -> []
  residual differences: <repo>/.cache/crosscheck/qalun.tsv

## duri
witness                unit     compared     raw  vocalised  skeleton  spacing  chapters = skeleton
---------------------------------------------------------------------------------------------------
qp-6                   verse        6218  100.0%     100.0%    100.0%        0        114/114      
faw-qurandoori         chapter       114    6.1%      39.4%    100.0%        1        114/114      
  qp-6: Quranpedia mushaf 6 (al-Duri). Ancestry: KFGQPC Doori v8 via Quranpedia; same origin as the fawazahmed0 copy. Our duri snapshot is this dump: a refresh check.
    identical units raw/skeleton/vocalised of 6218: 6218/6218/6218
  faw-qurandoori: KFGQPC Doori (fawazahmed0 ara-qurandoori). Ancestry: KFGQPC Doori v8 via the fawazahmed0 mirror on jsDelivr; verse numbers renumbered to Hafs, so chapter level only.
    identical units raw/skeleton/vocalised of 114: 7/114/45
        626  [06ED] -> [065C]
          3  [064E] -> []
          1  [0621 0652] -> [0654]
  residual differences: <repo>/.cache/crosscheck/duri.tsv

## shubah
witness                unit     compared     raw  vocalised  skeleton  spacing  chapters = skeleton
---------------------------------------------------------------------------------------------------
qp-9                   verse        6236  100.0%     100.0%    100.0%        0        114/114      
faw-quranshouba        chapter       114    6.1%      97.3%    100.0%       35        114/114      
  qp-9: Quranpedia mushaf 9 (Shu'bah). Ancestry: KFGQPC Shu'bah via Quranpedia; same origin as the fawazahmed0 copy. Our shubah snapshot is this dump: a refresh check.
    identical units raw/skeleton/vocalised of 6236: 6236/6236/6236
  faw-quranshouba: KFGQPC Shu'bah (fawazahmed0 ara-quranshouba). Ancestry: KFGQPC Shu'bah via the fawazahmed0 mirror on jsDelivr; renumbered to Hafs, so chapter level only.
    identical units raw/skeleton/vocalised of 114: 7/114/111
          3  [064E] -> []
          1  [0621 0652] -> [0654]
  residual differences: <repo>/.cache/crosscheck/shubah.tsv

## susi
witness                unit     compared     raw  vocalised  skeleton  spacing  chapters = skeleton
---------------------------------------------------------------------------------------------------
qp-10                  verse        6217  100.0%     100.0%    100.0%        0        114/114      
faw-quransoosi         chapter       114    6.1%      42.1%    100.0%        2        114/114      
  qp-10: Quranpedia mushaf 10 (al-Susi). Ancestry: KFGQPC Soosi via Quranpedia; same origin as the fawazahmed0 copy. Our susi snapshot is this dump: a refresh check.
    identical units raw/skeleton/vocalised of 6217: 6217/6217/6217
  faw-quransoosi: KFGQPC Soosi (fawazahmed0 ara-quransoosi). Ancestry: KFGQPC Soosi via the fawazahmed0 mirror on jsDelivr; renumbered to Hafs, so chapter level only.
    identical units raw/skeleton/vocalised of 114: 7/114/48
        592  [06ED] -> [065C]
          3  [064E] -> []
          1  [06ED] -> [06EA]
          1  [] -> [0651]
  residual differences: <repo>/.cache/crosscheck/susi.tsv

## qpc-hafs
witness                unit     compared     raw  vocalised  skeleton  spacing  chapters = skeleton
---------------------------------------------------------------------------------------------------
qp-2                   verse        6236  100.0%     100.0%    100.0%        0        114/114      
faw-quranuthmanihaf    verse        6236   40.1%      99.9%    100.0%        5        114/114      
  qp-2: Quranpedia mushaf 2 (KFGQPC Hafs). Ancestry: KFGQPC Hafs v13 via Quranpedia; same origin as the fawazahmed0 copy (vocalised 6,234/6,236 identical to it in the research).
    identical units raw/skeleton/vocalised of 6236: 6236/6236/6236
  faw-quranuthmanihaf: KFGQPC Hafs Uthmanic (fawazahmed0 ara-quranuthmanihaf). Ancestry: KFGQPC Hafs v13, Uthmanic script via the fawazahmed0 mirror on jsDelivr
    identical units raw/skeleton/vocalised of 6236: 2506/6236/6234
          1  [0621 0652] -> [0654]
          1  [06EA] -> [065C]
  residual differences: <repo>/.cache/crosscheck/qpc-hafs.tsv
```
