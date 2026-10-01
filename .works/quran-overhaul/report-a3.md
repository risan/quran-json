# Track A3 report: transliteration generator (D12)

Branch `worktree-agent-ac967fca18185257e` (worktree
`.claude/worktrees/agent-ac967fca18185257e`), on top of `overhaul/quran-json-v5` including the
A1 merge. Nothing is wired into `cdn.py`; the integrator calls `romanize.build_editions()` and
reads `romanize.EDITIONS`.

## What was built

| File | Role |
|---|---|
| `src/quranjson/romanize.py` | The generator: tokenise, phoneme layer, cross-word rules, pause layer, three table-driven renderers, `build_editions`, `EDITIONS`, `HAFS_EXCEPTIONS`. |
| `src/quranjson/romanize_validation.py` | Metric A, the disagreement classifier, the report writer, the English skeleton helpers, a bit-parallel edit distance (no new dependency). |
| `scripts/romanize_crosscheck.py` | Dev only, needs the network: `english` (Tanzil skeleton check), `phonemes` (QUD engine), `baselines` (rewrites the two committed lists). |
| `tests/test_romanize.py` | 90 tests, about 14 s. |
| `tests/data/romanize_golden.json` | Golden strings (all three renderers) for each rule and each hand-coded exception. |
| `tests/data/romanize_generator_gaps.txt` | The 13 verses currently in the generator-gap class. |
| `tests/data/romanize_reference_witness.txt` | 334 verses where the Kemenag Latin differs and an independent engine agrees with our phones, each with a digest of our phones. |
| `schemas/transliteration-catalogue.schema.json` | Added optional `language`, `name`, `reading`, `verse_ids`, `method`, `review` (still `additionalProperties: false`). |
| `pyproject.toml` | Only `per-file-ignores` (RUF001 for the IPA script and the romanisation test). No dependency added. |

Public API:

* `romanize_verse(text, renderer, *, chapter, verse) -> str`, `RENDERERS = ("id-skb", "en", "en-simple")`.
* `build_editions(snapshot=None) -> {renderer: [{"id": n, "verses": [{"id", "transliteration"}]}]}`,
  114 chapters, 6,236 Hafs ids, read from `config.kemenag_path()` when no snapshot is passed.
  A verse is read once and rendered three times: 2.3 s for everything.
* `EDITIONS`: one dict per renderer with `key`, `edition` (`transliteration_<key>`),
  `language`, `name`, `reading: "hafs"`, `verse_ids: "hafs"`, `author`, `source` (Kemenag URL),
  `method`, `license` (`{status: "granted", text, url}`, CC BY-SA 4.0 with the Kemenag source
  credit), `review: "machine-generated; not yet reviewed by a qualified reader"`.
* `write_report(path)`: the markdown disagreement report (counts per class, up to 50 examples
  per class, shown as the differing fragment with context rather than whole lines).

## Approach

The prototype's pipeline was kept and rewritten as typed, small functions (`WordReader` with one
method per rule, `_StopMarks` for waqf marks, `speak` for the cross-word and pause layers,
`Scheme` tables for rendering). The Kemenag `transliteration` field (upstream `latin`) is read
only in `romanize_validation.py` and in tests, as a reference.

Fixes made while porting, each found by diffing against the Kemenag Latin or the independent
engine (they moved Metric A from the prototype's 85.2% / 0.33% to 87.2% / 0.294%):

* The alif carrying a maddah (U+0622) after a fatha only lengthens it (`yurīdā`, not `yurīda'ā`).
* A tatweel that carries a dagger alef lengthens the vowel (`ambā'u`, `al'āna`).
* Hamza spacing: a vowelled hamza after `wa`/`fa`/`ya` is spaced (the majority, `fa in`), a hamza
  with sukun is not (`fa'tū`): all 11 sites seen agree with Kemenag.
* Idgham across a stop: a word starting with a shadda after a pause keeps one consonant.
* A small noon at the start of the next word is the tanwin written as vowel plus noon
  (`yauma'iżinil-ḥaqq`), about 54 places.
* A yeh-maksura carrying the kasra is a long ī (`fī`); a bare one after a kasra mid-word is not
  lengthened.
* The silent alif of a plural waw gets its own phone, so `latawallau wa hum` and the tanwin
  assimilation `kaṡīraw wa` are spelled differently, as Kemenag does.
* A pausal alif (U+06E0, `ẓunūnā`, `salāsilā`) is pronounced only when the word is stopped on.
* A hamzat al-wasl takes `u` for an imperative (`uqtulū`), `a` for the article, `i` otherwise.
* `ṭ` before a shadda `t` stays audible (`basaṭta`); alif with subscript alef is `ʾī`;
  silent alif after a prefix chain (`afattakhażtum`, `lattaba‘nākum`, `tallāhi`).

Hafs exceptions: the Kemenag text writes each one as a mark, so each is a mark rule (module
docstring and `HAFS_EXCEPTIONS`): imala U+06EA (`majrêhā`), ishmam U+06EB and tashil U+06EC
(no Latin letter, ignored on purpose), sakta U+06DC (breaks the flow, keeps vowels, drawn as an
ellipsis), small sin U+06E3 (`yabsuṭ`, `basṭah`, `musaiṭirūn`). Complete idgham `nakhlukkum` and
`bi'salismul-fusūqu` follow from the written shadda and lam vowel. Every one is pinned by a
golden verse, and a test fails if a listed exception has none.

## Numbers (all 6,236 verses of the committed snapshot)

**Metric A**, `id-skb` against the Kemenag Latin, normalised as documented in
`romanize_validation.py` (NFC, `(…)` hints dropped, lower case, letters plus `'` and `‘`):

* exact verses: 5,435 (87.16%); character error rate: 0.294% (1,418 edits / 482,454 characters).
* test gate: exact >= 87.1% and CER <= 0.30% (plan floor was 85% and 0.35%).

**Disagreement classes** (801 non-matching verses):

| Class | Verses | Meaning |
|---|---|---|
| reference-typo | 334 | Kemenag Latin deviates from the Arabic; our phones agree with the independent engine |
| pause-choice | 286 | matches once individual mid-verse stop decisions are flipped |
| hamza-spacing | 168 | only an apostrophe differs (`fa'in` / `fa in`) |
| generator-gap | 13 | everything else; listed in `tests/data/romanize_generator_gaps.txt` |

The "reference-typo" label is evidence-based but broad: the reference deviates from two
independent derivations of the Arabic. Spot checks show missing macrons (`‘azizun`), wrong
letters (`rijāliūkum` 2:282, `wal ardḍi` 7:96, `ṣabirūna` 8:65, `ubarri'u` 3:49, all four
classified), `a`/`ā` drift, and words dropped from the Latin line (9:10, 23:78). A few may be
conventions rather than typos (tanwin written `ā(n)` mid-verse in 2:29). The witness file
stores a digest of our phones per verse, so a later generator change voids the confirmation and
the verse falls into generator-gap (tested).

**The 13 remaining generator-gap verses**: 7:196, 25:49, 27:36, 46:33, 75:40 are text-versus-
reading cases (the Kemenag Arabic lacks the final yā of `nuḥyiya`, `waliyyiya`, `ātāniya` that
both the Latin and the engine have; not fixable from the text). 2:61, 4:171, 5:8, 6:93, 7:148,
21:71, 38:74, 60:10 differ from the engine only where a word after a stop mark carries an
explicit alif vowel that connected reading would drop (an artefact of how the comparison removes
stops), and also have a reference deviation of their own. So these 13 are "not confirmed", not
"known wrong"; none is a known generator bug.

**Metric B**, phone stream against QUD `quranic-phonemizer` (MIT, `uv run --with`, not a project
dependency), connected reading, gemination ignored:

* with nasals compared: 5,035 identical verses (80.7%), phone error rate 0.332%;
* nasals dropped from both sides: 6,191 identical verses (99.3%), phone error rate 0.022%.
  The engine marks ikhfa and iqlab with symbols of its own that do not map one to one onto n
  and m, which is why the strict number is worse. Plan target was <= 0.5%.

**English skeleton check** (`en` against Tanzil `en.transliteration`): consonant plus
vowel-length skeleton error rate **1.68%**, 44.2% of verses identical. tanzil.net's certificate
has expired, so the script fell back to the same transliteration from
`https://api.alquran.cloud/v1/quran/en.transliteration` (cached in `.cache/`, git-ignored).
Residuals are style: Tanzil writes `n wa` where we write the assimilated `w wa`, and its vowel
lengths are inconsistent (`Allahu`, `laaa`).

**Performance**: all three renderers over 6,236 verses: 2.3 s.

**Checks**: `uv run pytest` 275 passed, 7 skipped (the skips predate this work);
`ruff check`, `ruff format --check`, `mypy` clean.

## Samples (generated; 2:255 is cut to its first lines here, the golden test pins all of it)

### id-skb

```
1:1   Bismillāhir-raḥmānir-raḥīm.
1:2   Al-ḥamdu lillāhi rabbil-‘ālamīn.
1:3   Ar-raḥmānir-raḥīm.
1:4   Māliki yaumid-dīn.
1:5   Iyyāka na‘budu wa iyyāka nasta‘īn.
1:6   Ihdinaṣ-ṣirāṭal-mustaqīm.
1:7   Ṣirāṭal-lażīna an‘amta ‘alaihim gairil-magḍūbi ‘alaihim walaḍ-ḍāllīn.
2:255 Allāhu lā ilāha illā huw, al-ḥayyul-qayyūm, lā ta'khużuhū sinatuw walā naum, lahū mā fis-samāwāti wamā fil-arḍ, man żal-lażī yasyfa‘u ‘indahū illā bi'iżnih, ya‘lamu mā baina aidīhim wamā khalfahum, walā yuḥīṭūna bisyai'im min ‘ilmihī illā bimā syā', wasi‘a kursiyyuhus-samāwāti wal-arḍ, walā ya'ūduhū ḥifẓuhumā, wahuwal-‘aliyyul-‘aẓīm.
112:1   Qul huwallāhu aḥad.
112:2   Allāhuṣ-ṣamad.
112:3   Lam yalid walam yūlad.
112:4   Walam yakul lahū kufuwan aḥad.
```

### en

```
1:1   Bismillāhir-raḥmānir-raḥīm
1:2   Al-ḥamdu lillāhi rabbil-ʿālamīn
1:3   Ar-raḥmānir-raḥīm
1:4   Māliki yawmid-dīn
1:5   Iyyāka naʿbudu waʾiyyāka nastaʿīn
1:6   Ihdinaṣ-ṣirāṭal-mustaqīm
1:7   Ṣirāṭal-ladhīna anʿamta ʿalayhim ghayril-maghḍūbi ʿalayhim walaḍ-ḍāllīn
2:255 Allāhu lā ilāha illā huw, al-ḥayyul-qayyūm, lā taʾkhudhuhū sinatuw walā nawm, lahū mā fis-samāwāti wamā fil-arḍ, man dhal-ladhī yashfaʿu ʿindahū illā biʾidhnih, yaʿlamu mā bayna aydīhim wamā khalfahum, walā yuḥīṭūna bishayʾim min ʿilmihī illā bimā shāʾ, wasiʿa kursiyyuhus-samāwāti wal-arḍ, walā yaʾūduhū ḥifẓuhumā, wahuwal-ʿaliyyul-ʿaẓīm
112:1   Qul huwallāhu aḥad
112:2   Allāhuṣ-ṣamad
112:3   Lam yalid walam yūlad
112:4   Walam yakul lahū kufuwan aḥad
```

### en-simple

```
1:1   Bismillaahir-rahmaanir-raheem
1:2   Al-hamdu lillaahi rabbil-`aalameen
1:3   Ar-rahmaanir-raheem
1:4   Maaliki yawmid-deen
1:5   Iyyaaka na`budu wa'iyyaaka nasta`een
1:6   Ihdinas-siraatal-mustaqeem
1:7   Siraatal-ladheena an`amta `alayhim ghayril-maghdoobi `alayhim walad-daalleen
2:255 Allaahu laa ilaaha illaa huw, al-hayyul-qayyoom, laa ta'khudhuhoo sinatuw walaa nawm, lahoo maa fis-samaawaati wamaa fil-ard, man dhal-ladhee yashfa`u `indahoo illaa bi'idhnih, ya`lamu maa bayna aydeehim wamaa khalfahum, walaa yuheetoona bishay'im min `ilmihee illaa bimaa shaa', wasi`a kursiyyuhus-samaawaati wal-ard, walaa ya'ooduhoo hifzuhumaa, wahuwal-`aliyyul-`azeem
112:1   Qul huwallaahu ahad
112:2   Allaahus-samad
112:3   Lam yalid walam yoolad
112:4   Walam yakul lahoo kufuwan ahad
```


## Known limitations and findings

* **Not reviewed.** Every edition carries `review: "machine-generated; not yet reviewed by a
  qualified reader"`. Owner action: arrange a review.
* **Stops at the lam-alef sign.** The generator does not stop at the "la" sign, following
  tajwid. Kemenag's Latin does stop there often: stopping there as well raises exact agreement
  from 5,435 to 5,645 verses (90.5%). That is a policy choice for the integrator or reviewer,
  one constant (`PAUSE_MARKS`) away.
* `wa` is joined to the next word (`walā`); Kemenag writes `wa lā` always. Spaces are not part
  of Metric A, and separating `wa` needs a lexicon (many roots begin with `wa`).
* The reference is inconsistent about `au`/`aw` before a following `wa` and about hamza spacing;
  we pick the majority (`au`, spaced vowelled hamza).
* Not modelled: ikhfa, madd lengths beyond the written alef/maddah, qalqala, tafkhim.
* 52:37: the engine reads the ṣād, Kemenag's Latin and the written small sin say sīn; we follow
  the text. All three small-sin verses are read as `s`.
* Kemenag text differs from the Madani mushaf in a few places (the five `ya` verses above);
  the generator follows the text it is given.
* `romanize_verse` takes `chapter` and `verse` but only validates them: every exception is
  driven by a mark in the text, so no verse list exists to apply to the wrong reading.
* The `reference-typo` class is defined at phone level with nasals dropped (see above); an n/m
  mistake would be caught by Metric A, not by the engine.

## For the integrator

* Catalogue entry per edition: take `EDITIONS[i]` minus `key`, add `path`
  (`/transliteration/<key>/`), `chapters: 114`, `files`. `tests/test_romanize.py` builds exactly
  that and validates it against the schema (and rejects an invalid `reading`).
* The new schema properties are optional so the current Kemenag entry still validates; once the
  generated editions replace it, `reading`, `verse_ids` and `review` can be made required.
* The reader must offer a transliteration only when the selected script's reading is Hafs; the
  entries declare `reading` and `verse_ids` as `hafs` and the ids are Hafs ids (a test pins
  Hafs 1:4 = `Māliki`).
* `scripts/romanize_crosscheck.py baselines` regenerates the witness and gap lists after a
  generator change; review the diff before committing. Needs `uv run --with quranic-phonemizer`.
