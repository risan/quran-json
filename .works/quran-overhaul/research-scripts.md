# Arabic scripts audit: validity, gaps, cross-checks, licences

Researched 2026-10-01. Every number below was measured that day with the scripts in
`/home/risan/.cache/claude-tmp/claude-1000/-home-risan-projects-code-quran-json/19c2ddb2-a9d1-4fd5-9952-ac000374a71b/scratchpad/scripts/`
(`run_all.sh` reproduces them; raw output in `run_all.out`). Downloads are in `../dl`.
"Verified" means I fetched or measured it today. "Inference" or "unverified" marks a guess.

## Summary

1. **All 12 texts are sound Qur'an texts.** No verse in any script has a wrong or missing
   word. Every difference found against an independent copy is spelling convention
   (full vs dagger alef, hamza seat, word spacing), never a different word.
2. **`uthmani` is the Madinah mushaf, letter for letter.** Against KFGQPC's own Uthmanic
   Hafs text, all 114 chapters have identical letters. With vowel marks, 98.0% of verses
   are identical after mapping encoding conventions. It is also a byte-exact copy of
   today's tanzil.net file, so Tanzil's "verbatim only" rule is met. KEEP.
3. **`hafs-nastaliq` is KFGQPC's Indo-Pak (Nastaleeq) text, and its label is wrong.** Its
   letters match KFGQPC's Hafs Nastaleeq v10 file in all 114 chapters. The manifest says
   it is "not matching the printed edition". That misreads Quranpedia's flag, which only
   means "no page-image layout is attached" (the flag lines up exactly with the mushafs
   that have no SVG page pack). KEEP, and fix the name and description to
   "Indo-Pak (KFGQPC Nastaleeq)".
4. **`indopak` (DigitalKhatt) is a real Indo-Pak text.** It follows the 13-line Taj
   "Quraan Al Majeed" mushaf. At letter level it differs from KFGQPC Nastaleeq in only 49
   verses, all spelling choices. The README's "shares 0 of 6,236 verses" is a byte
   comparison; it hides that the letters agree in 99.2% of verses. KEEP, as the
   secondary Indo-Pak script.
5. **`warsh`, `qalun`, `duri` are KFGQPC's printed riwayah editions.** Letters match
   KFGQPC's own Warsh v8, Qalun v8 and Duri v8 files in 114/114 chapters. Today's
   Quranpedia dumps are byte-identical to the committed snapshots. KEEP all three.
6. **`kemenag` is the Indonesian standard text, with about 15 typing slips.** Words are
   run together, e.g. 8:67 `عَزِيْزٌحَكِيْمٌ` and 38:19 `وَالطَّيْرَمَحْشُوْرَةً`. No word
   is wrong. KEEP; document the slips and report them to LPMQ.
7. **The six Tanzil texts are not redundant, but three are niche.** `uthmani`, `simple`
   and `simple-clean` are the ones apps use. `uthmani-min`, `simple-min` and
   `simple-plain` are rarely used (alquran.cloud does not even offer `simple-plain`).
   The compatibility contract forbids removing paths, so KEEP all six and list the three
   niche ones last in the docs.
8. **The biggest missing script is KFGQPC's Uthmanic Hafs text ("QPC Hafs")**, the text
   Quran.com, QUL and KFGQPC's apps use. Quranpedia ships it as mushaf 2 under the same
   licence the repo already accepts for Warsh and Qalun. ADD it. Shu'bah, al-Susi,
   al-Bazzi and Qunbul are also there, but KFGQPC itself calls them specialist readings.
   Add them only if specialist users matter. No digital text exists for Hisham, Ibn
   Dhakwan, Khalaf or the other remaining narrators in any source checked.
9. **Licence risks to decide on.** (a) Quranpedia's licence says "keep any copy current"
   and "don't freeze a copy". That clashes with this project's immutable paths. (b) The
   four Quranpedia texts are KFGQPC's digitisation. The README marks the same KFGQPC
   texts "restricted" when they come from KFGQPC, but "granted" when they come through
   Quranpedia. (c) The repo is CC BY-SA 4.0, but Tanzil text may not be changed, and its
   notice "shall be included in all verbatim copies". The per-chapter files carry no
   notice. (d) DigitalKhatt's MIT label is not proof of ownership: the same repository's
   Madina text is Tanzil's text re-encoded.
10. **Replace the "Mushaf traditions" table with a five-line "Which script should I use?"
    list** (text below). Move the layout/rasm/riwayah explanation to a single sentence.

## Per-script verdicts

| Script | What it is | Who uses it | Recognised? | Concerns | Verdict |
|---|---|---|---|---|---|
| `uthmani` | Tanzil Uthmani 1.1 (2021). Unicode text of the Madinah mushaf, Hafs. | The most copied web text: Tanzil, alquran.cloud (older 1.0.x copy), Quranic Arabic Corpus base, countless apps. | Tanzil's own claim: "carefully produced, highly verified and continuously monitored by a group of specialists". Letters match KFGQPC Hafs 114/114 chapters (measured). Not certified by KFGQPC itself. | None in the text. tanzil.net's TLS certificate expired 2026-09-30 (fetching needs a workaround). | **KEEP** (primary) |
| `uthmani-min` | Same text, fewer marks. | Offered by alquran.cloud (`quran-uthmani-min`). Rare elsewhere. | Tanzil product. | Niche. | **KEEP**, list last |
| `simple` | Tanzil Imlaei (modern spelling), full vowels. | alquran.cloud `quran-simple`, fawazahmed0 `ara-quransimple`. | Tanzil product. Letters match Quranpedia's Imlaei text in 6,233/6,236 verses. | People confuse it with "less marks". README already warns. | **KEEP** |
| `simple-plain` | Imlaei without special idgham/ikhfa marking. | Not offered by alquran.cloud (verified edition list). | Tanzil product. | Least used of the six. | **KEEP**, list last |
| `simple-min` | Imlaei, minimal marks. | alquran.cloud `quran-simple-min`. | Tanzil product. | Niche. | **KEEP**, list last |
| `simple-clean` | Imlaei, no marks. Tanzil: "Suitable for easy search." | Search features in many apps; alquran.cloud `quran-simple-clean`. | Tanzil product. | None. | **KEEP** |
| `kemenag` | Mushaf Standar Indonesia (LPMQ), rasm Usmani, as served by quran.kemenag.go.id. | Indonesia: the legal standard; every mushaf printed or circulated there needs LPMQ tashih (PMA 44/2016). | Yes: the Indonesian ministry's own text. | ~15 run-together words and ~5 split words in the API text (list below). One upstream fix seen since 2025 (11:19), so LPMQ maintains it. | **KEEP**; document the slips, report to LPMQ |
| `indopak` | DigitalKhatt's Indo-Pak text (15-line file), based on the 13-line Taj "Quraan Al Majeed" mushaf. | QUL lists it (resources 565/566) beside KFGQPC and QuranWBW Indopak; Tarteel sponsors DigitalKhatt. | Follows a widely printed South Asian mushaf. No authority certifies the digital text. | Al-Fatiha numbered the Indo-Pak way (basmala unnumbered). Needs Extended-B font. MIT ownership unproven (see Licence issues). | **KEEP** as secondary Indo-Pak; rename display to "Indo-Pak (DigitalKhatt)" |
| `warsh` | KFGQPC Warsh ʿan Nafiʿ, via Quranpedia mushaf 4 ("نسخة موافقة للمطبوع"). | KFGQPC: "the reading of the people of the Arab Maghreb, West and Central Africa, and Western Europe (France and Spain)". | Yes: KFGQPC printed mushaf. Letters match KFGQPC Warsh v8 in 114/114 chapters. | It is the Saudi (KFGQPC) Warsh edition, not Morocco's national Mohammed VI mushaf, whose marks and spelling conventions differ (inference; that text is not available to compare). | **KEEP** |
| `qalun` | KFGQPC Qalun ʿan Nafiʿ, via Quranpedia mushaf 7. | KFGQPC: "the people of Libya, Tunisia and some regions of Mauritania". | Yes: KFGQPC printed mushaf. Letters match KFGQPC Qalun v8 in 114/114 chapters. | Quranpedia's "Libyan Awqaf Qalun" (mushaf 12) is byte-identical text, so it is not a second witness. | **KEEP** |
| `hafs-nastaliq` | KFGQPC Hafs Nastaleeq v10, KFGQPC's Indo-Pak-script edition, via Quranpedia mushaf 3. | Quranpedia: "the one adopted in a number of Asian countries such as India and Pakistan". QuranWBW verified its own Madinah Indopak text against this KFGQPC text. Quran.com/QUL offer "QPC Nastaleeq". | Yes: KFGQPC lists "حفص خط نستعليق" among its official fonts; QuranWBW cites the official KFGQPC Nastaleeq mushaf. | Mislabelled as "not matching the printed edition". Name hides that it is the mainstream KFGQPC Indo-Pak text. | **KEEP**; rename display to "Indo-Pak (KFGQPC Nastaleeq)", fix description |
| `duri` | KFGQPC al-Duri ʿan Abi ʿAmr, via Quranpedia mushaf 6 ("موافقة للمطبوع"). | KFGQPC (as relayed by a mirror of its developer page): "the people of Sudan and East Africa". | Yes: KFGQPC printed mushaf. Letters match KFGQPC Duri v8 in 114/114 chapters. | Numbering: Duri has 31 ayahs in al-Mulk (67:9 split after `نَذِيرٞ`), al-Susi (same reading) has 30, giving 6,218 vs 6,217. Unverified which matches the KFGQPC print. | **KEEP**; verify the al-Mulk split before documenting "6,218" as canonical |

No script is controversial among Muslims. All four riwayat (Hafs, Warsh, Qalun, al-Duri)
are mutawatir readings that are recited publicly today.

**DROP is not available.** README "Compatibility contract": "A published path is never
renamed, removed, or rewritten." So "rename" above means the manifest `name`/`description`
and README wording, not the path. An alias path (e.g. `indopak-kfgqpc` →
same bytes as `hafs-nastaliq`) is allowed, because "Adding is always fine".

## Missing scripts

| Candidate | Where | Licence wording (quoted) | Verdict | How widely used |
|---|---|---|---|---|
| **KFGQPC Uthmanic Hafs ("QPC Hafs")** | Quranpedia mushaf 2, <https://api.quranpedia.net/dumps/mushafs-2.json.gz> (font `UthmanicHafs_V22.ttf`) | "Republishing this data — in full or in part — as a downloadable database or dataset requires: (1) crediting Quranpedia.net as the source with a link, and (2) stating this dump's version." | **Granted by Quranpedia**, with the same KFGQPC chain-of-title caveat as `warsh` | Very wide: KFGQPC apps; QUL resource 86 "QPC Hafs script" (says "published by the King Fahd Complex"); Quran.com. Measured: vocalised text identical to KFGQPC Hafs v13 in 6,234/6,236 verses |
| same, via QUL | <https://qul.tarteel.ai/resources/quran-script/86> | No licence on the page. FAQ: "The resources available on QUL vary in their copyright status… We recommend reviewing the licensing information provided by each resource's author." Issue #773 asking exactly this is open and unanswered. | **Unknown** | as above |
| same, from KFGQPC | qurancomplex.gov.sa/techquran/dev (unreachable today: connection timeout; read via Wayback 2025-09-01) | Footer: "جميع الحقوق محفوظة ل مجمع الملك فهد لطباعة المصحف الشريف © 2025". The one grant (dm.qurancomplex.gov.sa/copyright, Wayback 2024-05-18) covers only "رسم المتجهات Illustrator". Font licence: "This Font is the property of King Fahd Glorious Quran Printing Complex, and may not be reproduced, modified without the express written approval". | **Restricted** | — |
| **Shu'bah ʿan ʿAsim** | Quranpedia mushaf 9 ("موافقة للمطبوع", page SVGs available) | Quranpedia licence (above) | **Granted by Quranpedia** (KFGQPC caveat) | KFGQPC: "من الروايات التي يستفيد منها المتخصصون في القراءات" (specialists). Letters match KFGQPC Shouba v7 114/114 |
| **al-Susi ʿan Abi ʿAmr** | Quranpedia mushaf 10 (6,217 ayahs; "غير موافق للمطبوع" = no page pack) | Quranpedia licence | **Granted by Quranpedia** (KFGQPC caveat) | Specialists (KFGQPC wording, via mirror). Letters match KFGQPC Soosi v8 114/114 |
| **al-Bazzi / Qunbul ʿan Ibn Kathir** | Quranpedia mushafs 5 and 8 (6,221 ayahs each) | Quranpedia licence | **Granted by Quranpedia** (KFGQPC caveat) | Specialists. Letters match KFGQPC Bazzi v7 / Qumbul v7 114/114 |
| Mainstream Indopak (QuranWBW / Quran.com, QUL 59/89) | <https://github.com/marwan/indopak-quran-text> | "for Sadaqa-e-Jaria purposes only. DO NOT SELL, MANIPULATE, DISTRIBUTE WITHOUT CREDITS OR TAMPER IN ANY FORM OR MANNER." Its own text is not fully Unicode (private-use glyph codes). | **Restricted** | Very wide in South Asia via Quran.com/QuranWBW. The KFGQPC Nastaleeq text it was checked against is already shipped as `hafs-nastaliq` |
| Hisham, Ibn Dhakwan, Khalaf, Khallad, al-Kisa'i's narrators, Abu Jaʿfar, Yaʿqub | — | — | **Not available** | None of Quranpedia (12 mushafs), KFGQPC's developer page, fawazahmed0, Wikisource `Module:Quran/*`, or QUL's script list offers them |
| fawazahmed0 KFGQPC copies (`ara-quranuthmanihaf`, `-warsh`, `-qaloon`, `-doori`, `-soosi`, `-shouba`, `-bazzi`, `-qumbul`, `-indopak`) | <https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions.json> | Repo is Unlicense; editions only say "source: https://qurancomplex.gov.sa/". Its Hafs v13 copy also inserts a space before tanween alef (`شَيۡـࣰٔ ا`). | **Unknown**; good as a comparison witness only | — |
| Wikisource `وحدة:Quran/data KFGQPC`, `…Warsh.json`, `…DKhatt.json` etc. | ar.wikisource.org | Module header: "Data from https://fonts.qurancomplex.gov.sa/wp02/حفص v2.0". Wikisource's CC BY-SA cannot cover KFGQPC's own work. | **Unknown** (not a clean grant) | — |
| Khaled Hosny `quran-data` | <https://github.com/khaledhosny/quran-data> | No LICENSE file. README: "The text have not been formally reviewed, so it may contain some unintentional errors." | **Unknown** | Letters equal Tanzil Uthmani (114/114), so it adds nothing |
| Quranic Arabic Corpus | corpus.quran.com | GPL; "Any use must clearly indicate the Quranic Arabic Corpus as the source" (as quoted in Quranpedia's licence) | Granted (GPL) but it is morphology on a Tanzil-based text (unverified today), not a new script | — |
| alquran.cloud | api.alquran.cloud | No text licence found; texts are Tanzil's | Not a new source | Serves pre-2021 Tanzil 1.0.x Uthmani (measured: lacks the 1.1 fixes at 12:39 and 12:41) |

**Recommended additions, in order:** (1) `qpc-hafs` from Quranpedia mushaf 2 — widely used,
and it gives users KFGQPC's exact encoding for KFGQPC fonts; (2) `shubah` (the only other
riwayah with a KFGQPC page-matched edition on Quranpedia); (3) `susi`, `bazzi`, `qunbul`
only if you want completeness for specialists.

## Cross-check results

### Method

Each pair is compared verse by verse (or chapter by chapter when verse numbering differs)
after five normalisation levels:

| Level | What is removed or unified |
|---|---|
| L0 | NFC, tatweel, zero-width and bidi controls |
| L1 | + letter variants unified (Farsi yeh, alef maksura, keheh, heh goal, alef forms incl. alef wasla) |
| L2 | + all vowel marks, Quranic annotation signs, waqf marks, digits, private-use glyphs |
| L3 | + hamza seats collapsed (ؤ→و, ئ→ي, ء dropped); alef kept |
| L4 | + alef dropped, spaces dropped, basmala prefix of verse 1 dropped (consonant skeleton) |

"Letters identical" below means L3 with spaces ignored, compared per chapter: the strongest
test that is still blind to encoding conventions. A real word difference (a different
reading or a typo) survives every level.

### Hafs (Tanzil `uthmani`, `simple`, `simple-clean`)

| Comparison | Result | Nature of differences |
|---|---|---|
| Our snapshot vs tanzil.net today (uthmani, simple-clean) | 6,236/6,236 byte-identical | none. Published site chapters 1, 2, 9, 95, 112, 114 also byte-identical (440/440) |
| `uthmani` vs KFGQPC Hafs (Quranpedia mushaf 2) | letters identical 114/114 chapters; L4 6,236/6,236 verses | 3 word-spacing choices (15:7 `لو ما`, 27:20 `ما لي`, 36:22 `وما لي`) |
| same, fully vocalised, after mapping 5 encoding conventions (KFGQPC sukun U+06E1 vs U+0652, open tanween, hamza+madda order, dotless yeh) | 6,112/6,236 (98.0%) | dabt conventions only: fatha on `لَٔا`-type hamza, small high madda U+06E4, hamza below U+0655 |
| `uthmani` vs KFGQPC Hafs v13 (fawazahmed0 copy) | letters identical 114/114 | none |
| Quranpedia mushaf 2 vs KFGQPC Hafs v13 | vocalised 6,234/6,236 identical | so Quranpedia mushaf 2 **is** KFGQPC's Hafs text |
| `uthmani` vs alquran.cloud `quran-uthmani` | L4 6,234/6,236; L0 only 1,877/6,236 | alquran.cloud is Tanzil 1.0.x: lacks the Tanzil 1.1 (2021-02-12) fix at 12:39 and 12:41 and uses older mark encoding |
| `uthmani` vs DigitalKhatt `quran_text_madina.ts` | L2 6,236/6,236 | DigitalKhatt's Madina file is Tanzil's text re-encoded (it even copies Tanzil's three spacing choices above) |
| `uthmani` vs Khaled Hosny quran-data | letters identical 114/114 | not independent |
| `simple` vs Quranpedia mushaf 1 (Imlaei) | L4 6,233/6,236 | Tanzil 1.1 spellings at 5:31, 17:32, 39:56 (`يا ويلتىٰ`, `الزنىٰ`, `يا حسرتىٰ`) |
| `simple` vs Wikisource Imlaei (fawazahmed0 `quranspelled`) | 108/114 chapters identical | the same 3 Tanzil 1.1 spellings + 3 spacing/spelling choices (20:94 `يا ابن أم`, 68:6 `بأييكم`, 72:16 `وأن لو`) |

**Conclusion:** the Tanzil Hafs texts carry no textual error detectable against KFGQPC.

### `kemenag`

| Comparison | Result | Nature of differences |
|---|---|---|
| vs Tanzil `uthmani` | L4 6,226/6,236 | 10 verses, all rasm conventions of the Indonesian standard: 10:96 `كلمة` (Madinah writes open `كلمت`), 72:16 `أن لو` written separated, 55:54 `وَجَنَا` (Tanzil `وَجَنَى`), 3:102 `تُقٰىتِهٖ` (Tanzil `تُقَاتِهِۦ`), 20:122 and 68:50 `اجْتَبٰىهُ` (Tanzil `ٱجْتَبَٰهُ`), 38:8, 22:11, 28:20, 40:58 hamza/yeh seats |
| vs KFGQPC Hafs (word boundaries) | 34 boundary differences; Kemenag has fewer spaces in 25 | Most are **typing slips in the Kemenag API**: `عَزِيْزٌحَكِيْمٌ` (8:67), `بِغَيْرِحَقٍّ` (3:21), `وَالطَّيْرَمَحْشُوْرَةً` (38:19), `وَقَدْاُخْرِجْنَا` (2:246), `وَلَقَدْاٰتَيْنَا` (40:53), `بِمَايَعْمَلُوْنَ` (8:47), `لَوْاَنْفَقْتَ` (8:63), `لَوْلَاكِتٰبٌ` (8:68), `مِمَّاغَنِمْتُمْ` (8:69), `لَاخَوْفٌ` (43:68), `لَارَيْبَ` (45:26); split words: `بِاَ نَّهُمْ` (5:58), `وَ اللّٰهُ` (2:205). A few joins may be MSI convention (`بَعْدَمَا`, `لَاجَرَمَ`): unverified |
| vs a 2025 scrape of the same API (dyazincahya/quran-json-kemenag) | 6,235/6,236 byte-identical | 1 upstream correction: 11:19 `كفِٰرُوْنَ` → `كٰفِرُوْنَ` (misplaced dagger alef fixed). Not an independent witness, but shows LPMQ maintains the text |
| vs Indo-Pak texts | L2 6,036/6,236 with DigitalKhatt `indopak`, vs 3,734 with Tanzil | Kemenag's spelling is far closer to the Indo-Pak (Bombay) tradition than to Madinah, as LPMQ's history says |

No independent LPMQ copy (e.g. its Word download) could be fetched today; lajnah.kemenag.go.id
was already recorded as unreachable on 2026-09-18.

### Indo-Pak (`hafs-nastaliq`, `indopak`)

| Comparison | Result | Nature of differences |
|---|---|---|
| `hafs-nastaliq` vs KFGQPC Hafs Nastaleeq v10 (fawazahmed0 `ara-quranindopak`) | letters identical 114/114; L4 6,236/6,236 | spacing only → it **is** KFGQPC's Nastaleeq text |
| `indopak` vs `hafs-nastaliq` | 49 verses with letter differences (51 word spans) | all full vs dagger alef (`قاتلهم/قٰتلهم`, `جادلتم`, `بناتي`), hamza seat (`اولياؤهم`), spacing; plus Al-Fatiha segmentation |
| `indopak` vs QuranWBW Indopak v9.6 Madinah (git history, 2023) | L2 6,123/6,236 | WBW private-use glyphs and the same alef choices. DigitalKhatt differs from **both** WBW and KFGQPC on the same ~50 alef words, which suggests an independent transcription (inference) |
| fresh Quranpedia mushaf 3 vs committed `hafs-nastaliq` | 6,236/6,236 byte-identical | — |

### Riwayat (`warsh`, `qalun`, `duri`)

Verse numbers differ (fawazahmed0 renumbered its copies to Hafs), so these are chapter-level.

| Comparison | Result |
|---|---|
| `warsh` vs KFGQPC Warsh v8 | letters identical 114/114 chapters |
| `qalun` vs KFGQPC Qaloon v8 | letters identical 114/114 chapters |
| `duri` vs KFGQPC Doori v8 | letters identical 114/114 chapters |
| fresh Quranpedia dumps (version 2026-09-30) vs committed snapshots | warsh 6,214/6,214, qalun 6,214/6,214, duri 6,218/6,218 byte-identical |
| Quranpedia changes feed since 2026-09-18 | 0 ayah changes |
| Quranpedia Shu'bah / Susi / Bazzi / Qunbul vs KFGQPC copies | letters identical 114/114 each |
| Quranpedia Libyan Awqaf Qalun (mushaf 12) vs mushaf 7 | byte-identical: not a second witness |

Caveat on independence: the fawazahmed0 copies and Quranpedia both come from KFGQPC
files. The check proves Quranpedia did not corrupt KFGQPC's letters. It cannot detect an
error KFGQPC itself made. No non-KFGQPC Warsh/Qalun/Duri text was found to compare
(Morocco's is not published; KSU's e-Mushaf serves Warsh as images only, per the README).

### Encoding notes for the docs

At L0 (raw bytes) almost no two sources agree: Tanzil vs KFGQPC 54/6,236, indopak vs
KFGQPC Nastaleeq 719/6,236. Byte-level "0 shared verses" therefore says nothing about
whether two texts are the same edition. The README's DigitalKhatt claim should say
"letters agree in 6,187/6,236 verses; bytes differ because the encoding differs".

## Licence issues

| Source | Issue | Severity | Proposal |
|---|---|---|---|
| **Tanzil** (6 scripts) | Notice (fetched today, tanzil.net/docs/text_license): "Permission is granted to copy and distribute verbatim copies of this text, but CHANGING IT IS NOT ALLOWED." and "This copyright notice shall be included in all verbatim copies of the text, and shall be reproduced appropriately in all files derived from or containing substantial portion of this text." Published chapter files (e.g. `/text/uthmani/chapters/112.json`) carry only `id` and `verses`. The manifest's `license.project` says "CC BY-SA 4.0" and per-script entries have no licence field. | Medium: the notice term is not met per file, and a reader may think CC BY-SA lets them change the text. | Add a `license`/`notice` field per script in the manifest, and the Tanzil notice to `text/{tanzil-script}/quran.json`. Because paths are immutable, do this in new files or the next generation. State plainly: "Tanzil texts are under Tanzil's terms, not CC BY-SA". |
| Tanzil (ops) | tanzil.net's TLS certificate expired 2026-09-30 (curl: "certificate has expired"). | Low | Fetch with pinned checksums; do not disable verification silently. |
| **Quranpedia** (`warsh`, `qalun`, `duri`, `hafs-nastaliq`) | LICENSE.md (now "Version 2026-10-01"; terms unchanged in substance): "The content is continuously corrected. Keep any copy current via https://quranpedia.net/api/v1/changes?since=<version> — distributing outdated Quranic text is the distributor's responsibility." Usage policy: "build on the API live and credit Quranpedia — don't freeze a copy of a text that is still being corrected." This project caches data paths `immutable` for a year and says "Correcting the Quran text would be a break". | **High (conflict of principle).** | Decide one rule: publish corrected text at new versioned paths and mark old ones superseded in the manifest, and run the changes feed in CI. Or ask Quranpedia (quranpedia.help@gmail.com) to confirm that pinned, dated snapshots with a changes check satisfy the licence. |
| Quranpedia → KFGQPC chain of title | Quranpedia's index labels mushafs 2–10 "من إصدار مجمع الملك فهد", and the letters match KFGQPC's own files. Quranpedia's licence claims only "the digitization, structuring, verification, diacritical correction (dabt)…". KFGQPC: "جميع الحقوق محفوظة" and a font licence that forbids reproduction without written approval. The README marks "KFGQPC developer text — Madinah Hafs/QPC and the Warsh package" **restricted**, yet ships the same KFGQPC letters via Quranpedia as **granted**. | **High (inconsistency).** | Pick one position and write it down. Either: accept Quranpedia's grant (and say why: KFGQPC's terms reachable to us cover only fonts and the vector copy, not text), or write to KFGQPC for a text grant. Do not add `qpc-hafs` until this is settled. |
| **DigitalKhatt** (`indopak`) | MIT at the repo root. But `quran_text_madina.ts` in the same repo is Tanzil's Uthmani re-encoded (L2 6,236/6,236), and Tanzil forbids changes. So the MIT label alone does not show DigitalKhatt owns its texts. For `indopak` the evidence points to an independent transcription, but provenance is not documented. QUL issue #758 ("Licensing clarification: commercial use of DigitalKhatt resources 21, 48 and 247") is open and unanswered. | Medium | Ask DigitalKhatt (Amine Anane) to confirm the source of `quran_text_indopak_15.ts` and that MIT covers it. Until then keep, with the risk recorded. |
| **Kemenag** | Statutory, not a licence: Regulation 44/2016 Pasal 8(1) "Teks Mushaf Al-Qur'an tidak memiliki hak cipta". Outside Indonesia this rests on the general public-domain status of the Qur'an. Distribution in Indonesia needs LPMQ tashih (already documented). | Low | Keep as is. |
| `dist/` frozen tree | `ara-quranuthmanienc` is a modified Tanzil text with no grant (already documented). | Known | No change. |

**Clearer alternatives.** For Hafs Uthmani there is no cleaner source than Tanzil:
KFGQPC reserves all rights, QUL publishes no licence, and Wikisource's copy is KFGQPC's
text. Quranpedia mushaf 2 is the only option whose licence does not forbid changes (useful
for derived work such as a generated transliteration), but it carries the KFGQPC
chain-of-title question. For Warsh, Qalun and al-Duri, Quranpedia is the only granted
route found. For Indo-Pak, `hafs-nastaliq` (KFGQPC via Quranpedia) and `indopak`
(DigitalKhatt) are both already shipped; QuranWBW's text remains restricted.

## "Mushaf traditions, and what is covered" section

**Drop the table.** It mixes three things (print traditions, gaps, licence verdicts) and
repeats the licensing table. Replace it with this:

> ### Which script should I use?
>
> - **Most apps (Madinah mushaf, Hafs):** `uthmani`. For search, `simple-clean`.
> - **South Asia (Indo-Pak script):** `hafs-nastaliq` (KFGQPC Nastaleeq) or `indopak` (DigitalKhatt).
> - **Indonesia:** `kemenag` (Mushaf Standar Indonesia).
> - **North and West Africa:** `warsh` (Morocco, Algeria, West Africa), `qalun` (Libya, Tunisia), `duri` (Sudan).
>
> Page layouts such as 13-, 15- or 16-line mushafs are not texts, so they are not here.

The three-axes explanation (riwayah / rasm / layout) can stay as one sentence in the
script table's intro. The per-tradition gaps already live in the Licensing table.

## Sources

All accessed 2026-10-01 unless stated.

- Quranpedia licence: <https://api.quranpedia.net/dumps/LICENSE.md> ("Version 2026-10-01")
- Quranpedia dumps index and mushaf index: <https://api.quranpedia.net/dumps/>, <https://api.quranpedia.net/dumps/mushafs-index.json.gz> (licence version 2026-09-30); mushaf dumps 1–12
- Quranpedia usage policy: <https://quranpedia.net/api-docs#usage-policy>; changes feed <https://quranpedia.net/api/v1/changes?since=2026-09-18>
- Tanzil licence: <https://tanzil.net/docs/text_license>; text types <https://tanzil.net/docs/quran_text_types>; updates <https://tanzil.net/docs/text_updates>; download `https://tanzil.net/pub/download/index.php?quranType=uthmani&outType=txt-2&agree=true` (certificate expired; fetched with verification off, read-only)
- KFGQPC developer page (live site unreachable: connection timeout): Wayback snapshot 2025-09-01 of <https://qurancomplex.gov.sa/techquran/dev/>; usage rights: Wayback 2024-05-18 of <https://dm.qurancomplex.gov.sa/copyright/>
- KFGQPC font licence text: <https://scancode-licensedb.aboutcode.org/kfgqpc-uthmanic-script-hafs.html>
- KFGQPC data mirror (English riwayah descriptions): <https://github.com/thetruetruth/quran-data-kfgqpc>
- fawazahmed0 editions: <https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions.json> and `editions/ara-*.json`
- QUL: <https://qul.tarteel.ai/faq>, <https://qul.tarteel.ai/resources/quran-script>, <https://qul.tarteel.ai/resources/quran-script/86>; issues <https://github.com/TarteelAI/quranic-universal-library/issues/773>, `/758`
- QuranWBW Indopak: <https://github.com/marwan/indopak-quran-text> (README; v9.6 data and `(Important) Readme.txt` at commit `1e2042e415`)
- DigitalKhatt: <https://github.com/DigitalKhatt/digitalkhatt-js> (MIT; `quran_text_madina.ts`), <https://github.com/DigitalKhatt/indopakfont> (OFL; "Font based on Quraan Al Majeed 13 lines IndoPak Mushaf")
- alquran.cloud: <https://api.alquran.cloud/v1/edition?format=text&language=ar>, `/v1/quran/quran-uthmani`, `/v1/quran/quran-simple`
- Kemenag 2025 scrape: <https://github.com/dyazincahya/quran-json-kemenag>
- Wikisource modules: <https://ar.wikisource.org/wiki/وحدة:Quran/data_KFGQPC> (raw header line quoted above)
- Khaled Hosny: <https://github.com/khaledhosny/quran-data>
- Published site: <https://quran-json.risanb.com/manifest.json>, `/text/{uthmani,simple-clean}/chapters/{1,2,9,95,112,114}.json`
- Repo: `README.md` (Compatibility contract, Licensing, Mushaf traditions), `data/meta/sources.json`, `data/meta/licensing-review.json`, `src/quranjson/digitalkhatt.py`
- Not reachable today: qurancomplex.gov.sa and fonts.qurancomplex.gov.sa (timeout); Wayback CDX API ("Temporarily Offline") for later lookups.
