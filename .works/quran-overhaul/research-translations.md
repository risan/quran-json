# Research: more translations and transliterations

Date: 2026-10-01. Read-only research; no repository file was changed except this report.
Scratchpad with every download, script and log:
`/home/risan/.cache/claude-tmp/claude-1000/-home-risan-projects-code-quran-json/19c2ddb2-a9d1-4fd5-9952-ac000374a71b/scratchpad/translit/`
(called `$SP` below).

Marking: **VERIFIED** = fetched/downloaded and counted in this session. **SEARCHED** = from search
snippets or a secondary page only. **GUESS** = my inference, not checked.

## Summary

- **QuranEnc has 36 complete editions we do not ship** (19 of them in languages we have none of),
  plus 2 incomplete ones and 41 tafsir editions. They are on the website but not in the
  `/api/v1/translations/list` endpoint (which returns the same 75 keys as our
  `catalogue.json`). This is the same situation as the 8 editions already in
  `data/quranenc/supplemental.json`, so the existing supplemental route covers them.
  Three shipped editions have newer versions upstream.
- **Public domain: 4 editions are ready with little work** — Rodwell (English, 1861),
  Ahmed Raza Khan *Kanzul Iman* (Urdu, 1911), Mahmud ul Hasan (Urdu, c.1909) and Keyzer (Dutch,
  1860). All four are complete at 6,236 verses in Kufi numbering. Five more PD works exist but
  need Flügel→Kufi re-alignment or OCR clean-up (Goldschmidt DE, Savary FR, Kazimirski FR,
  Muhammad Ali 1917 EN, Zetterstéen SV).
- **Transliteration: still no ready-made text with a grant**, in any script. A fresh search
  (GitHub, Hugging Face, PyPI, Wikisource, Leeds corpus) found only unlicensed copies,
  a no-ads/no-paywall licence (Quran-Lab), and MIT *code*.
- **Generating our own is feasible and is the recommended route.** A 600-line prototype that
  reads the Kemenag Arabic text (no copyright by Indonesian regulation; already `granted` in
  `licensing-review.json`) reproduces Kemenag's own Latin field exactly for **85.2% of all 6,236
  verses, character error rate 0.33%**. Most remaining differences are inconsistencies or typos
  in Kemenag's reference, not generator errors. Its phoneme layer agrees with an independent MIT
  tajweed phonemizer at **0.35% phoneme error** (1,000 random verses).
- Expected additions: **+36 QuranEnc** (90 → 126), **+4 PD now** (+5 later), and
  **3 generated transliterations first** (Indonesian SKB-1987, English with diacritics,
  English ASCII), then Turkish, Bengali, Devanagari and Cyrillic after native-reader review.

## QuranEnc gap table

**Method (VERIFIED).** Fetched `https://quranenc.com/api/v1/translations/list` (75 entries) and
`https://quranenc.com/en/home` (162 `browse/<key>` links with a `DD/MM/YYYY - Vx.y.z` card).
Downloaded every missing translation's SQLite archive (`https://quranenc.com/downloads/sqlite/<key>.zip`),
or, where the zip is 404, all 114 surahs from `https://quranenc.com/api/v1/translation/sura/<key>/<n>`
(the API serves these keys even though the list omits them; it answers 403 to Python's default
User-Agent). Counted rows, empty rows, and adjacent identical rows (verse groups translated together).
Scripts: `$SP/qe_gap.py`, `qe_cards.py`, `qe_check.py`, `qe_api_full.py`, `qe_table.py`.

**Terms.** Every browse page carries the same terms as the API page:
> "Contents of the translations can be downloaded and re-published, with the following terms and
> conditions: 1. No modification, addition, or deletion of the content. 2. Clearly referring to the
> publisher and the source (QuranEnc.com). 3. Mentioning the version number when re-publishing the
> translation. 4. Keeping the transcript information inside the document. 5. Notifying the source
> (QuranEnc.com) of any note on the translation. 6. Updating the translation according to the latest
> version issued from the source (QuranEnc.com). 7. Inappropriate advertisements must not be included
> when displaying translations of the meanings of the Noble Quran."
> — e.g. https://quranenc.com/en/browse/bosnian_korkut (VERIFIED)

Versions come from the homepage cards because these keys are not in the API list.

### A. Complete translations to add (36)

| Key | Title (QuranEnc) | Version | Upstream date | Source | Rows | Empty | Adjacent dup. | New language? |
|---|---|---|---|---|---|---|---|---|
| `ankobambara_foudi` | N'ko Translation - Sulaiman Kante | 1.0.0 | 28/11/2021 | zip | 6236 | 0 | 0 | no (N'ko; have `ankobambara_dayyan`) |
| `belarusian_krivtsov` | Belarusian Translation - Krivtsov | 1.0.0 | 31/12/2025 | API only | 6236 | 0 | 0 | **yes** |
| `bosnian_korkut` | Bosnian Translation - Besim Korkut | 1.0.0 | 10/04/2017 | zip | 6236 | 0 | 0 | no |
| `bulgarian_translation` | Bulgarian Translation | 1.0.0 | 07/06/2021 | zip | 6236 | 0 | 0 | **yes** |
| `chichewa_betala` | Chichewa Translation - Khalid Ibrahim Batyala | 1.0.0 | 04/04/2022 | zip | 6236 | 0 | 0 | **yes** |
| `chinese_mayolong` | Chinese Translation - Basair (Ma Yulong) | 1.0.0 | 31/05/2022 | zip | 6236 | 0 | 1 | no |
| `chinese_suliman_modern` | Chinese - Muhammad Suliman - modern Chinese | 1.0.0 | 16/09/2026 | API only | 6236 | 0 | 0 | no |
| `dagbani_ghatubo` | Dagbani Translation - Muhammad Baba Ghutubo | 1.0.0 | 29/10/2020 | zip | 6236 | 0 | 0 | **yes** |
| `dari_badkhashani` | Dari Translation - Muhammad Anwar Badakhshani | 1.0.0 | 16/02/2021 | zip | 6236 | 0 | 0 | **yes** |
| `french_hameedullah` | French Translation - Muhammad Hamidullah | 1.0.2 | 02/07/2025 | zip | 6236 | 0 | 0 | no (see note 2) |
| `georgian_rwwad` | Georgian Translation (Rowwad) | 1.0.7 | 28/07/2026 | zip | 6236 | 0 | 0 | **yes** |
| `german_aburida` | German Translation - Abu Rida | 1.0.0 | 27/11/2016 | zip | 6236 | 0 | 0 | no |
| `greek_rwwad` | Greek Translation - Rowwad Translation Center | 1.0.2 | 02/09/2024 | zip | 6236 | 0 | 0 | **yes** |
| `hebrew_darussalam` | Hebrew Translation - Darussalam Association | 1.0.3 | 22/08/2023 | zip | 6236 | 0 | 0 | **yes** |
| `iranun_sarro` | Filipino Translation (Iranun) | 1.0.1 | 29/06/2025 | zip | 6236 | 0 | 0 | **yes** |
| `kannada_bashir` | Kannada - Shaykh Bashir Misuri | 1.0.1 | 26/06/2025 | zip | 6236 | 0 | 54 | no |
| `kazakh_altai` | Kazakh Translation - Khalifa Altai | 1.0.0 | 30/03/2017 | zip | 6236 | 0 | 4 | **yes** |
| `kurdish_salahuddin` | Kurdish Translation - Salahuddin | 1.0.0 | 28/03/2021 | zip | 6236 | 0 | 4 | no |
| `kurmanji_ismail` | Kurdish (Kurmanji) - Ismail Sageri | 1.0.0 | 13/01/2022 | zip | 6236 | 0 | 0 | **yes** (Kurmanji) |
| `luganda_foundation` | Luganda - African Development Foundation | 1.0.1 | 21/02/2026 | zip | 6236 | 0 | 0 | **yes** |
| `luhya_center` | Luhya - Intl. Association for Science and Culture | 1.0.3 | 13/10/2024 | zip | 6236 | 0 | 1 | **yes** |
| `malagasy_rwwad` | Malagasy Translation - Rowwad | 1.0.1 | 15/10/2024 | zip | 6236 | 0 | 0 | **yes** |
| `marathi_ansari` | Marathi Translation - Muhammad Shafee' Ansari | 1.0.0 | 03/10/2018 | zip | 6236 | 0 | 0 | **yes** |
| `nepali_central` | Nepali - Ahlul-Hadith Association | 1.0.3 | 07/06/2024 | zip | 6236 | 0 | 0 | **yes** |
| `oromo_rwwad` | Oromo Translation - Rowwad | 1.0.0 | 16/07/2026 | API only | 6236 | 0 | 0 | no |
| `pashto_sarfaraz` | Pashto - Maulawi Janbaz Sarfaraz | 1.0.0 | 28/11/2024 | zip | 6236 | 0 | 0 | no |
| `pashto_zakaria` | Pashto - Abu Zakaria | 1.0.1 | 15/06/2020 | zip | 6236 | 0 | 0 | no (every row is prefixed `n-m`, see note 3) |
| `russian_aboadel` | Russian Translation - Abu Adel | 1.0.0 | 14/02/2026 | zip | 6236 | 0 | 21 | no |
| `shona_institute` | Shona - Dar al-Ilm Institute | 1.0.0 | 20/07/2026 | zip | 6236 | 0 | 1 | **yes** |
| `swahili_abubakr` | Swahili - Abdullah Muhammad & Nasser Khamis | 1.0.1 | 12/03/2026 | zip | 6236 | 0 | 0 | no |
| `tajik_khawaja` | Tajik - Khoja Mirov Khoja Mir | 1.0.2 | 24/01/2022 | zip | 6236 | 0 | 0 | no |
| `thai_complex` | Thai - A group of seekers of knowledge | 1.0.1 | 25/06/2025 | zip | 6236 | 0 | 0 | no |
| `uzbek_sadiq` | Uzbek - Muhammad Sadiq | 1.0.1 | 25/06/2025 | zip | 6236 | 0 | 1 | no |
| `vietnamese_hassan` | Vietnamese - Hasan Abdulkarim | 1.0.1 | 25/06/2025 | zip | 6236 | 0 | 0 | no |
| `yaw_silika` | Yao Translation - Muhammad ibn Abdulhamid Silika | 1.0.3 | 15/07/2025 | zip | 6236 | 0 | 0 | **yes** |
| `zulu_adel` | Zulu - Adel Jaafar Moltsho | 1.0.0 | 23/07/2026 | API only | 6236 | 0 | 0 | **yes** |

Notes:
1. **Provenance class.** Seven of these (Korkut, Hamidullah, Altai, Khawaja, Sadiq, Hassan,
   Thai) say *"developed under the supervision of the Rowwad Translation Center. The original
   translation is available for the purpose of expressing opinion, evaluation, and continuous
   development."* That is the same wording as `ukrainian_yakubovych` and `korean_hamid`, which are
   already published from `supplemental.json`. The QuranEnc grant therefore covers them to the
   same degree. If the owner wants to be stricter for translators who are well known outside
   QuranEnc (Besim Korkut d.1975, Muhammad Hamidullah d.2002), that would be a new policy and
   would also apply to the two already shipped. My view: keep the current policy.
2. **`french_hameedullah` re-opens a withheld edition.** The live site withholds Tanzil's `fr`
   (Hamidullah) as `restricted`. QuranEnc's v1.0.2 is a separate, granted source of the same
   translation (QuranEnc's edited text, not Tanzil's bytes).
3. **`pashto_zakaria`:** all 6,236 rows start with a `n-m` style prefix (regex
   `^\(?\d+\s*[-–]\s*\d+`). Probably a verse-number label; check before publishing, but "no
   modification" means we publish it as served.
4. **Adjacent duplicates** are verse groups translated as one block and repeated per verse
   (Kannada 54, Abu Adel 21). Shipped editions already have this pattern; not a blocker.
5. Four editions have no SQLite zip (404) — `belarusian_krivtsov`, `chinese_suliman_modern`,
   `oromo_rwwad`, `zulu_adel`. Their full text came from the per-surah API (114 calls each,
   VERIFIED complete). The ingest needs an API-fetch path, or we wait for the zips.

### B. Do not add yet (incomplete)

| Key | Version | Rows | Empty | Reason |
|---|---|---|---|---|
| `circassian_rwwad` | 1.0.1 (06/08/2025) | 6236 | **1,000** | incomplete |
| `english_waleed` | 1.0.2 (16/09/2025) | 6236 | **3,753** | title says "(in progress)" |
| `korean_rwwad` (already withheld) | 1.0.11 | 6236 | **1,955** | re-checked today: unchanged, still incomplete |

### C. Version drift in shipped editions (update on next fetch)

| Key | Ours | Upstream |
|---|---|---|
| `vietnamese_rwwad` | 1.0.8 | **1.0.9** (API) |
| `moore_rwwad` | 1.0.1 | **1.0.2** (API) |
| `korean_hamid` (supplemental) | 1.0.3 | **1.0.4**, card dated 01/10/2026 (today) |

Term 6 ("Updating the translation according to the latest version") requires these updates.

### D. Out of scope: 41 tafsir editions

`arabic_{mokhtasar,moyassar,nafahat,saadi,seraj,yaseer}`, 29 `*_mokhtasar` translations of
*Al-Mukhtasar fi Tafsir*, 6 `*_saadi`/`uzbek_moyassar` tafsir translations. They are commentary,
not translations of the text. They could become a separate `tafsir` category later under the same
grant; not counted in the numbers above.

## Public-domain candidates table

Policy reminder: a work is PD when the translator died more than 70 years ago (before 1956 for
2026), unless the home-country term is shorter and we choose to rely on it. A later revision by a
newer editor is not PD. "Judge the work, not the host": a PD text may come from any mirror.

### Ready now (complete, verse-aligned to Kufi 6,236)

| Language | Translator (died), first published | PD reasoning | Best source | Completeness (VERIFIED by me) | Sample, fidelity |
|---|---|---|---|---|---|
| English | **J. M. Rodwell** (d.1900, SEARCHED), 1861 | life+70 and pre-1931 US | fawazahmed0 `https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions/eng-johnmedowsrodwe.json` | 6,236 verses, 114 surahs, 0 empty | 1:1 "In the Name of God, the Compassionate, the Merciful"; 2:1 "ELIF. LAM. MIM". Rodwell wording. **This corrects `licensing-review.json`**, which records the file as HTTP 403; it downloaded today. Rodwell's own book orders surahs chronologically; this file is in Mushaf order (someone re-ordered it, which adds no copyright). |
| Urdu | **Ahmed Raza Khan**, *Kanzul Iman* (d.28 Oct 1921, [Wikipedia](https://en.wikipedia.org/wiki/Ahmed_Raza_Khan_Barelvi)), 1911 | life+70 since 1992; India life+60 and Pakistan life+50 also passed | Tanzil `ur.kanzuliman` (file header: "Last Update: March 17, 2011") | 6,236 verses, 0 empty | 1:1 "اللہ کے نام سے شروع جو بہت مہربان رحمت والا". Reads as the original. Plain translation, no commentary. |
| Urdu | **Mahmud ul Hasan** (d.30 Nov 1920, [Wikipedia](https://en.wikipedia.org/wiki/Mahmud_Hasan_Deobandi)), c.1909 (GUESS) | life+70 since 1991 | fawazahmed0 `urd-mahmoodulhassan` (packager says source dailyayat.com) | 6,236 verses, 0 empty | 1:1 "شروع اللہ کے نام سے جو بڑا مہربان نہایت رحم والا ہے [۱]". Old spelling ("نہں" in 2:255) suggests original wording. **5,095 verses carry footnote markers like `[۱]`** that point to Usmani's notes (not included); strip them. |
| Dutch | **Salomo Keyzer** (d.1868, SEARCHED), 1860 | life+70 | fawazahmed0 `nld-salomokeyzer` (= Tanzil `nl.keyzer`); cross-check Project Gutenberg #19786 | 6,236 verses, 0 empty | 1:1 "In naam van den lankmoedigen en albarmhartigen God". Research agent found 2:2 and 112:1–4 identical to Gutenberg's printing, so original wording. **Defect:** mystic-letter verses hold a stray "M" (2:1 = "M"; also 3:1, 26:1, 28:1–32:1; 20:1 "H"). Fix by hand, documented. |

### Needs re-alignment or OCR work (PD, but not ready)

| Language | Translator (died), year | Source | State | Work needed |
|---|---|---|---|---|
| German | Lazarus Goldschmidt (d.1950, SEARCHED), 1916 | GitHub `Chajmke/goldschmidt_koran` (README says Public Domain; some footnotes missing) | 114 surahs, clean text, Flügel numbering (headers sum to 6,239) | Flügel→Kufi verse map |
| French | Claude-Étienne Savary (d.1788), 1783 (Wikisource has 1821 reprint) | fr.wikisource `Le_Coran_(Traduction_de_Savary)/N` | 109/114 fetched; numbered; Flügel | refetch 5 surahs; Flügel→Kufi map |
| French | Albin de Biberstein Kazimirski (d.1887, GUESS), 1840/1869 | fr.wikisource `Le_Koran_(Traduction_de_Kazimirski)/N` | all 114 fetched; **verse boundaries not marked** (line splits match counts in only 13/114 surahs) | manual verse segmentation — large |
| English | Maulana Muhammad Ali (d.1951, SEARCHED), 1917 | archive.org `Translation_And_Commentary_Of_The_Holy_Quran_By-Muhammad_Ali_Jauhar_1917` | OCR with verse numbers inside commentary | parse and proofread; use only the 1917 text (the 1951/1973 revisions are not PD). The withheld "Shakir" text is widely reported to derive from this one (SEARCHED). |
| Swedish | K. V. Zetterstéen (d.1953, SEARCHED), 1917 | runeberg.org/zetkoran (proofread OCR per page) | verse-numbered, Flügel | scrape + Flügel→Kufi |
| Italian | Luigi Bonelli (d.1947, SEARCHED), 1929 | archive.org `corano-bonelli` (1948 reprint) | OCR, numbered, Flügel | clean OCR + map |
| Latin | Ludovico Marracci (d.1700), 1698 | archive.org `Alcoranus` | OCR with long-s errors; numbering Kufi-like | heavy clean-up; low audience |
| Turkish | Elmalılı Hamdi Yazır (d.1942, SEARCHED), 1935–38 | fawazahmed0 `tur-elmalilihamdiya` (= Tanzil `tr.yazir`) | 6,236 verses, 0 empty (VERIFIED) | **Probably a modern simplified edition, not PD.** 2:255 reads "O daima diridir (hayydır), bütün varlığın idaresini yürüten (kayyum)dir" — modern Turkish (GUESS that it is the later *sadeleştirilmiş* text). Compare with a 1935 scan before any use. |
| Bengali | Girish Chandra Sen (d.1910), 1881–86 | bn.wikisource hub (রচনা:কুর’আন) | transcription state unverified; Wikisource copy is a 1936 posthumous edition | scrape, verse-split, confirm it is not revised |

### Rejected or no usable source

| Candidate | Reason |
|---|---|
| Max Henning (DE, d.1927) | Only digital text (projekt-gutenberg.org) is the 1970 Reclam edition by Kurt Rudolph with his numbering and notes; archive.org 1901 OCR is unusable Fraktur. Not the Hofmann 1999 revision, but still not a clean PD text. |
| Ludwig Ullmann (DE, d.1842) | archive.org Fraktur OCR only (GUESS: poor). |
| Fateh Muhammad Jalandhari (UR) | ur.wikipedia gives 1916–1982 → not PD until 2053. Exclude. |
| Shah Abdul Qadir / Shah Rafiuddin / Ashraf Ali Thanwi (UR), Shah Waliullah (FA) | PD authors, but only scans or unaligned HTML; no verse-aligned text. |
| Ömer Rıza Doğrul (TR, d.1952) | PD, scans only. |
| Hasan Basri Çantay (TR, d.1964) | Not PD. |
| Wang Jingzhai (ZH, d.1949) | PD in China; zh.wikisource has only chapters 1–2. |
| Okawa Shumei (JA, d.1957) | Not PD under life+70 until 2028. Sakamoto 1920: scans only. |
| Mirza Abul Fazl (EN, d.1956) | PD from 2027. |
| Arberry (EN, d.1969), Ignác Veselý (CS, d.1964), Ivan Hrbek (CS) | Not PD. |
| García Bravo (ES, 1907) | Translator death year unknown; OCR noisy (sura 2 parses to 205/286). |
| Indonesian, Malay, Hindi, Tamil, Malayalam, Gujarati, Swahili, Hungarian, Portuguese, Polish | No PD translation with a usable digital text found. |

### Other open-licensed modern translations

None new. The research agents found translation texts on Wikisource (tr, bs, es; CC BY-SA by site
policy) but did not confirm complete verse-aligned modern works; Hugging Face
`anisafifi/multilingual-quran` is CC BY 4.0 but repackages existing translations whose rights are
not the packager's. Nothing here beats the QuranEnc additions.

## Transliteration sources table

All data candidates below were fetched by the research agent unless marked. None is grantable.

| Candidate | Licence (verbatim) | Provenance | Verdict, blocker |
|---|---|---|---|
| github.com/maqsats/Quran-Transliteration- (EN/RU/KK) | none (no LICENSE) | author unstated; EN likely the Calgary text (GUESS) | unknown — no grant |
| github.com/eyaqubali/Quran-Transliteration (bn/en/id) | none, no README | unstated | unknown |
| hf.co/datasets/Buraaq/quran-md-ayahs (`ayah_tr`) | none in card | unstated | unknown |
| hf.co/datasets/ReySajju742/Quran | card `license: cc` (no variant) | scraped CSVs | unknown |
| github.com/TheAbubakrAbu/Quran-Tajweed-Engine | MIT | CREDITS.md credits its transliteration to risan/quran-json | circular — it is our own old data |
| hf.co/datasets/Quran-Lab/quran-tajweed-phonetics | "Quran-Lab No-Profit License Version 1.2 … You may not Charge for the Work or for any Derivative … neither the Work nor any feature it powers may be placed behind a payment, a subscription, a paywall, or advertising." | Quran-Lab; 6,236 ayat of phones, not Latin | **restricted** (field-of-use limit is incompatible with CC BY-SA) |
| Leeds Quranic Arabic Corpus, corpus.quran.com/download/ | "operates under the GNU General Public License"; "Permission is granted to copy and distribute verbatim copies of this file, but CHANGING IT IS NOT ALLOWED." | word morphology with Buckwalter | Buckwalter (`bisomi`) is a reversible ASCII code, not a reading aid. Not useful. |
| Wikisource tr/bs/es | CC BY-SA (site policy) | translations only | no transliteration found |
| github.com/alperenugus/Kuran | CC BY 4.0 | Arabic text in Diyanet orthography | not a transliteration |
| medinaschool.org Russian transcription | none seen | unknown | unknown |
| Indonesian, Bengali, Hindi, Urdu, Bosnian, Russian, Tamil open-licensed transliterations | — | — | **none found** |
| Already rejected (unchanged): Tanzil `en.transliteration`, Calgary/Islamic Bulletin, Eliasii (Pickthall), QUL/Tarteel, QuranPhoneticSearch, fawazahmed0 `-la`, Quran.com id 57, Kemenag `latin`, Tanzil Turkish | see `data/meta/licensing-review.json` | | |

Not fetched in this pass: the Kemenag, JAKIM, Bangladesh Islamic Foundation and Diyanet terms
pages. tanzil.net itself did not answer from this machine today (curl exit 60 / no response), so
Tanzil wording below is quoted from a verbatim copy.

### Generator code found

| Tool | Licence | Last commit | Notes |
|---|---|---|---|
| **QUD-Technologies/quranic-phonemizer** (moved from Hetchy/Quranic-Phonemizer; PyPI `quranic-phonemizer`) | MIT, "Copyright (c) 2025 Ahmed Ibrahim" (VERIFIED) | 2026-09-30 | IPA phonemes with tajweed (ikhfa, iqlab, idgham, qalqala, waqf). **Bundles QUL's Quran script** ("The project makes use of the Quranic Universal Library's (QUL) Quran script", README Credits) — QUL text is `unknown` in our records. Use only as a comparison oracle, never as output. |
| **obadx/quran-transcript** (PyPI 0.6.4) | LICENSE: "MIT License. Copyright (c) [2024] [The Holy Quran Technoligies team]", preceded by the full Tanzil Uthmani copyright block (VERIFIED) | 2026-10-01 | Arabic-letter phonetic script, not Latin (1:1 → `بِسمِ للَااهِ ررَحمَاانِ ررَحِۦۦۦۦم`); ran over all 6,236 ayat without error (agent). Works from bundled Tanzil text. |
| Quran-Lab/quran-g2p | GitHub "other"; LICENSE not opened (GUESS: same No-Profit licence) | 2026-09-26 | restricted (GUESS) |
| camel-tools | MIT | — | Buckwalter/HSB maps only, no tajweed |
| mishkal, pyarabic | GPL | — | no Quran phonology |

Note: `licensing-review.json` has two contradictory records about these phonemizers
("MIT-licensed phonemizers covering our exact Uthmani codepoints" vs "both 404"). Today both
repositories exist (one under a new owner). The record should be corrected either way.

## Generator design + prototype results

### Input text: use Kemenag, not Tanzil

- **Kemenag Arabic text** (`data/kemenag/quran.json`, field `text`) is already `granted`:
  Minister of Religious Affairs Regulation 44/2016, Pasal 8(1): *"Teks Mushaf Al-Qur'an tidak
  memiliki hak cipta."* A transliteration generated from it has no third-party rights holder.
- It is also the **better G2P input**. Its Indonesian orthography is explicit where Uthmani is
  implicit: long ū/ī carry a sukun (`يُوْصِيْكُمْ`), silent letters are left bare
  (`كَفَرُوْا`), elided long vowels lose their sukun before a wasl (`لَقُوا الَّذِيْنَ`), verse-initial
  wasl alifs carry their vowel (`اَلْحَمْدُ`, `اِهْدِنَا`), helping vowels are written (`قُلِ`),
  idgham is written as shadda on the next word (`مِنْ رَّبِّهِمْ`), and iqlab has the small mīm.
- **Tanzil Uthmani — is a generated transliteration a "change"?** Tanzil's terms say
  "Permission is granted to copy and distribute verbatim copies of this text, but CHANGING IT IS
  NOT ALLOWED", and also "This copyright notice shall be included in all verbatim copies of the
  text, and shall be reproduced appropriately in all files derived from or containing substantial
  portion of this text." My view: a romanisation is not a copy of the text at all, so the
  no-change clause (which protects the integrity of the Arabic as scripture) does not naturally
  apply; the third clause even contemplates "files derived from" the text, asking only for the
  notice. So Tanzil is *defensible* with attribution plus the notice. But it is arguable, and the
  repo already records it as "legally ambiguous". Kemenag removes the question at no cost, so use
  Kemenag as the source and keep Tanzil (and Qur'anpedia, Wikisource) for cross-checks only.
- Caveat (GUESS): Pasal 8(2) keeps the publisher's rights in the *tanda baca/tajwid* apparatus.
  The repository already publishes this text with its marks; the generator only reads waqf marks to
  decide where to pause. A verse-end-only pause policy avoids even that, at the cost of not pausing
  mid-verse.

### Pipeline

1. **Tokenise** each verse into words; each word into clusters (base letter + marks). Waqf marks
   (ۖ ۗ ۘ ۙ ۚ ۛ ࣖ ە) are lifted to word-level "pause after" flags. Marks can sit at the start
   of the next token in the Kemenag text (`ۗوَاِنَّ`); they belong to the previous word.
2. **Phoneme layer (per word, connected reading):** consonant inventory (b t th j ḥ kh d dh r z s
   sh ṣ ḍ ṭ ẓ ʿ gh f q k l m n h w y ʾ), short a/i/u, long ā/ī/ū, gemination, article boundary.
   Rules implemented:
   - sun letters (bare lām before a shadda letter → assimilation, `ar-raḥmān`); moon letters
     (`al-ḥamdu`); the lām of *Allāh*; `al-ladhī` (lām-shadda after wasl);
   - hamzat al-wasl: a bare word-initial alif is dropped and the word joins the previous one; a
     preceding long vowel is shortened (`fī s-samāwāti` → `fis-samāwāti`); after tanwin a helping
     *i* is added;
   - long vowels from alif / sukun-wāw / sukun-yā / alif maqṣūra / dagger alif / subscript alif /
     inverted ḍamma (ṣila `lahū`, `bihī`); diphthongs aw/ay;
   - Uthmani silent letters: alif after wāw al-jamāʿa, after tanwin fatḥ, rectangular/round zero,
     wāw after dagger alif (`ṣalāh`), silent wāw in `ulāʾika`;
   - idgham (with and without ghunna, mithlayn, mutajānisayn, within and across words) driven by
     the shadda the text writes; iqlab from the small mīm (`mim baʿdi`, `ṭayram bi`);
   - ikhfa: not marked in output (optional; a renderer may add `ŋ`);
   - verse-initial shadda (continuation of the previous verse's idgham) is dropped;
   - muqaṭṭaʿāt read as letter names (`Alif lām mīm`, `Kāf hā yā ʿain ṣād`).
3. **Pause (waqf) layer:** at verse end and at jīm/qalā/ṣalā/mīm marks (and the second of a
   muʿānaqa pair): drop final short vowel; tanwin ḍamm/kasr dropped; tanwin fatḥ → ā;
   tā marbūṭa → h; ṣila ū/ī dropped (`ʿaddadah`). Measured: this policy matches Kemenag best
   (verse-end-only drops exact verses from 85% to 58%).
4. **Renderers** (table-driven, all from the same phoneme stream):

| Renderer | 1:1 | 112:1 |
|---|---|---|
| Indonesian SKB 1987 (Kemenag style) | Bismillāhir-raḥmānir-raḥīm. | Qul huwallāhu aḥad. |
| English, diacritics | Bismillāhir-raḥmānir-raḥīm | Qul huwallāhu aḥad |
| English, plain ASCII | Bismillaahir-rahmaanir-raheem | Qul huwallaahu ahad |
| Turkish okunuş (approximate vowel harmony) | Bismillâhirrahmânirrahîm | Kul huvellâhu ahad |
| Cyrillic | Бисмильляхиррахманиррахим | Куль хувальляху ахад |
| Devanagari | बिस्मिल्लाहिर्रह़्मानिर्रह़ीम | क़ुल हुवल्लाहु अह़द |
| Bengali | বিস্মিল্লাহির্রহ্মানির্রহীম | কুল হুওল্লাহু আহদ |

Al-Fātiḥa 1:7, Kemenag-style output vs Kemenag's own field:
- ours: `Ṣirāṭal-lażīna an‘amta ‘alaihim gairil-magḍūbi ‘alaihim walaḍ-ḍāllīn.`
- Kemenag: `Ṣirāṭal-lażīna an‘amta ‘alaihim, gairil-magḍūbi ‘alaihim wa laḍ-ḍāllīn(a).`

2:255, English with diacritics (ours): `Allāhu lā ilāha illā huw, al-ḥayyul-qayyūm, lā taʾkhudhuhū
sinatuw walā nawm, lahū mā fis-samāwāti wamā fil-arḍ, man dhal-ladhī yashfaʿu ʿindahū illā
biʾidhnih, …, wahuwal-ʿaliyyul-ʿaẓīm`

### Validation and results (all 6,236 verses unless stated)

**Metric A — agreement with Kemenag's `latin` field (comparison only, never redistributed).**
Normalise both sides: NFC, drop Kemenag's parenthesised pause hints `(…)`, lower-case, keep only
letters plus `'` (hamza) and `‘` (ʿain). Then report exact-verse rate and character error rate
(CER = Levenshtein edits / reference length). Script: `$SP/evaluate.py`.

| Iteration | Exact verses | CER |
|---|---|---|
| first draft | 32.3% | 2.26% |
| + prefix/article/wasl fixes | 69.1% | 0.68% |
| + dagger-alif hamza, ṣila, iqlab carriers | 80.6% | 0.41% |
| **final prototype** | **85.2% (5,316)** | **0.33%** |
| final, ignoring hamza apostrophe | 88.2% (5,503) | 0.28% |

What is left is mostly the reference, not the generator:
- Kemenag writes the conjunction before a hamza both ways, about equally often (~175 diff
  sites each way: `fa'in` vs `fa in`). We must pick one; either choice "loses" the other half.
- Kemenag pauses at ۙ in some verses and not in others (`ma‘akum, innamā` vs `mir rabbihim wa`).
- Typos in the reference: `wal ardḍi` (7:96), `rijāliūkum` (2:282), `ṣabirūna` for صٰبِرُوْنَ
  (8:65), `ubarri'u` for اُبْرِئُ (3:49), `fihi` for فِيْهِ (3:49).
- Genuine generator gaps seen so far are small: some hyphen positions, ṣila before a pause at ۙ.

**Metric B — phoneme agreement with an independent engine (comparison only).**
QUD-Technologies `quranic-phonemizer` (MIT code, QUL text) on 1,000 random verses, after mapping
both to IPA, ignoring gemination and collapsing its nasal tajweed symbols (ŋ, ñ, m̃) to n/m:
**80.1% verses identical, phoneme error rate 0.35%.** Residuals: its `ŋ` for iqlab vs our `m`
(representation), and its different default stop policy at mid-verse marks (it stopped where we
ran without mid-verse pauses). Script: `$SP/oracle.py`.

**Recommended validation for production:**
1. Metric A on every build for the Indonesian renderer (gate: no regression in exact-verse count).
2. Metric B on all 6,236 verses for the phoneme layer.
3. English renderers: compare against Tanzil `en.transliteration` and Quran.com id 57 **for
   comparison only**, after mapping both to a consonant+vowel-length skeleton (their spelling style
   differs: `alrrahmani`). Report skeleton CER.
4. A stratified human review: ~300 verses chosen to cover each rule (wasl, sun letters, idgham
   types, iqlab, ta marbūṭa, muqaṭṭaʿāt, the Hafs special cases), read by one native reader per
   script.
5. A fixed list of Hafs exceptions to hand-code: imāla `majrēhā` (11:41), ishmām `taʾmannā`
   (12:11), the four saktas (18:1, 36:52, 75:27, 83:14), tashīl `aʾaʿjamiyyun` (41:44),
   `bi'sa l-ismu` (49:11), complete idgham `nakhlukkum` (77:20), plus the small-sīn/ṣād words
   (2:245, 7:69, 52:37). Not yet handled in the prototype.

**Feasibility verdict:** feasible. The prototype took about two hours and 600 lines. Production
quality (tests, the exception list, clean renderer tables, native review for non-Latin scripts) is
a medium-sized task. The Latin renderers are close to done; the abugida renderers need native
conventions (e.g. Bengali's inherent vowel is /ɔ/, so fatḥa is usually written with ā-kar; the
prototype is naive there).

### Which conventions to ship first (audience)

| Order | Convention | Why | Validation available |
|---|---|---|---|
| 1 | **Indonesian SKB 1987** (Kemenag style) | Largest Muslim population (Indonesia ~240M; readable in Malaysia/Brunei); measurable today | Kemenag `latin` (Metric A) |
| 2 | **English with diacritics** (ā ḥ ṣ ʿ ʾ) | global default for learners and apps | Tanzil / Quran.com skeleton (comparison only) |
| 3 | **English plain ASCII** (aa/ee/oo, no diacritics) | the style most English-speaking readers expect; search-friendly | same as 2 |
| 4 | Turkish okunuş | ~85M readers; Diyanet style is well defined | Diyanet okunuş (comparison only; terms not checked) |
| 5 | Bengali script | ~150M+ Bengali-speaking Muslims; high demand for "উচ্চারণ" | needs a native reviewer; no licensed reference |
| 6 | Devanagari, Cyrillic | smaller or Arabic-literate audiences (Urdu readers read Arabic script, so no Urdu renderer is needed) | native reviewer |

## Recommendations

In priority order, with expected counts:

1. **Add the 36 complete QuranEnc editions** through `supplemental.json` (same manual-registration
   path as the existing 8): 90 → **126 published translations**, +19 languages. Add an API-fetch
   path for the 4 keys without a zip. Keep `circassian_rwwad`, `english_waleed` and `korean_rwwad`
   withheld (incomplete). Update `vietnamese_rwwad` 1.0.9, `moore_rwwad` 1.0.2,
   `korean_hamid` 1.0.4.
2. **Add 4 public-domain editions now:** Rodwell (EN), Kanzul Iman (UR), Mahmud ul Hasan (UR,
   strip `[n]` markers), Keyzer (NL, fix the stray mystic-letter verses) → **130**. Record each
   as PD by author death year, with the transformation noted. Fix the Rodwell record in
   `licensing-review.json` (the file now answers 200).
3. **Build the transliteration generator from the Kemenag text** and publish 3 editions
   (Indonesian SKB-1987, English diacritics, English ASCII), 6,236 verses each, licensed like the
   rest of the repo. This finally gives `/transliteration/` granted content and lets the
   Kemenag `latin` override be dropped. Gate with Metric A + B and the human sample.
4. **Second wave of PD work** (needs a Flügel→Kufi map, written once and reused): Goldschmidt
   (DE), Savary (FR), Zetterstéen (SV), Bonelli (IT); then OCR projects Muhammad Ali 1917 (EN)
   and Kazimirski (FR, manual verse split) → up to **+6**.
5. **Second wave of transliterations:** Turkish okunuş, then Bengali, Devanagari and Cyrillic
   after a native reader signs off → **+4**.
6. Optional: a `tafsir` category from QuranEnc's 41 tafsir editions (same grant).
7. Do not ship: Elmalılı via Tanzil/fawazahmed0 (likely a modern simplified edition), Henning
   (only the 1970 Rudolph edition is digitised), Jalandhari (d.1982), any data candidate in the
   transliteration table.

## Sources

QuranEnc
- API list: https://quranenc.com/api/v1/translations/list ; per language: https://quranenc.com/api/v1/translations/list/bs
- Homepage catalogue: https://quranenc.com/en/home ; terms on every browse page, e.g. https://quranenc.com/en/browse/bosnian_korkut and https://quranenc.com/en/home/api
- Archives: https://quranenc.com/downloads/sqlite/<key>.zip ; per-surah API: https://quranenc.com/api/v1/translation/sura/<key>/<n>

Public domain
- fawazahmed0 index: https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions.json ; files `eng-johnmedowsrodwe`, `urd-mahmoodulhassan`, `nld-salomokeyzer`, `tur-elmalilihamdiya`, `urd-fatehmuhammadja`, `tur-hasanbasricanta`
- Tanzil translations: https://tanzil.net/trans/ (`ur.kanzuliman`, `nl.keyzer`, `tr.yazir`)
- Ahmed Raza Khan: https://en.wikipedia.org/wiki/Ahmed_Raza_Khan_Barelvi ; Kanzul Iman: https://en.wikipedia.org/wiki/Kanzul_Iman
- Mahmud Hasan Deobandi: https://en.wikipedia.org/wiki/Mahmud_Hasan_Deobandi
- Elmalılı: https://islamansiklopedisi.org.tr/hak-dini-kuran-dili
- Wang Jingzhai: https://en.wikipedia.org/wiki/Wang_Jingzhai
- Keyzer: https://www.gutenberg.org/ebooks/19786
- Goldschmidt: https://github.com/Chajmke/goldschmidt_koran
- Kazimirski / Savary: https://fr.wikisource.org/wiki/Le_Koran_(Traduction_de_Kazimirski) , https://fr.wikisource.org/wiki/Le_Coran_(Traduction_de_Savary)
- Zetterstéen: https://runeberg.org/zetkoran/
- Muhammad Ali 1917: https://archive.org/details/Translation_And_Commentary_Of_The_Holy_Quran_By-Muhammad_Ali_Jauhar_1917
- Bonelli: https://archive.org/details/corano-bonelli ; Marracci: https://archive.org/details/Alcoranus

Transliteration and tools
- QUD-Technologies/quranic-phonemizer: https://github.com/QUD-Technologies/quranic-phonemizer (MIT) ; https://pypi.org/project/quranic-phonemizer/
- obadx/quran-transcript: https://github.com/obadx/quran-transcript ; https://pypi.org/project/quran-transcript/
- Quran-Lab phonetics dataset: https://huggingface.co/datasets/Quran-Lab/quran-tajweed-phonetics
- Leeds corpus: https://corpus.quran.com/download/
- Tanzil text licence: https://tanzil.net/docs/text_license (quoted from the verbatim copy in https://github.com/obadx/quran-transcript/blob/main/LICENSE ; tanzil.net unreachable from here on 2026-10-01)
- Kemenag text status: Regulation 44/2016, https://jdih.kemenag.go.id/regulation-download/penerbitan-pentashihan-dan-peredaran-mushaf-al-qur%27an ; Copyright Law 28/2014, https://peraturan.bpk.go.id/Details/38690/uu-no-28-tahun-2014
- Kemenag transliteration scheme (SKB 158/1987 & 0543b/U/1987), as recorded in `data/transliteration-candidates/registry.json`

Scratchpad files (`$SP`)
- QuranEnc: `qe_list.json`, `qe_home.html`, `qe_cards.json`, `qe/*.zip|*.sqlite`, `qe_api/*.json`
- PD: `pd-asia/` (Kanzul Iman, Mahmud ul Hasan, Elmalılı, Jalandhari), `pd-europe/` (Rodwell, Keyzer, Goldschmidt, Savary, Kazimirski, Bonelli, Marracci, Muhammad Ali 1917, Henning partial)
- Generator: `translit.py` (prototype), `evaluate.py` (Metric A), `oracle.py` (Metric B), `find.py`, `ops.py` (error triage), `verify_pd.py`
