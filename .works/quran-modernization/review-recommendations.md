# Independent review of modernization recommendations

Date: 2026-09-20

## Verdict

The audit is a sound basis for deciding what to investigate next, after the
qualifications below. It does **not** support ingesting or publishing a new corpus now,
and it does not yet support a framework migration as the first implementation step.

The strongest findings are narrower:

- the canonical QuranEnc list has 75 editions and the repository already has all 75;
- several omitted QuranEnc keys return data, but their catalogue omission leaves exact
  grant scope, support status, and whole-corpus completeness unresolved;
- Quranpedia makes al-Duri and a Hafs Nastaliq text technically easy to inspect, but its
  republisher policy does not by itself settle the rights of KFGQPC-sourced material;
- the current site has specific correctness and accessibility problems that can be fixed
  without replacing its architecture; and
- the current data pipeline, immutable paths, frozen npm payload, reader state contract,
  font checks, and chapter-level loading are strengths to preserve.

Claims about edition adoption, user demand, Core Web Vitals, visual behavior, or
framework maintainability remain hypotheses unless the report names direct measurement.

## Corpus claims that must stay conditional

### QuranEnc translations

The live canonical endpoint returned 75 editions on the review date, matching the 75
QuranEnc snapshots in the repository. Bengali, Malay, modern Russian, Korean, Italian,
Ukrainian, Kazakh, Nepali, and Marathi candidates are therefore not ordinary omissions
from a source the importer failed to consume.

Direct endpoints for sampled omitted keys returned HTTP 200 for surahs 1 and 114, but
the API documentation calls the canonical list the available translations. A successful
URL proves technical access only. It does not prove that:

- the omission is accidental;
- the general republication grant applies to that exact omitted edition;
- all 114 surahs, verse counts, footnotes, and versions are complete; or
- QuranEnc intends the endpoint to be a supported bulk source.

The translation queue in `research-corpus.md` is best read as a **product-value and
rights-clarification queue**, not an ingestion queue. Cross-listing on QuranEnc and
Quran.com is distribution evidence, not readership or adoption evidence. Language
population is not edition demand. Bengali and Malay are good first clarification targets
because they add language coverage and have named sources; they are not permission-ready.

The repository already has Russian, Urdu, French, and nine English editions. Modern
Russian is an edition-modernity gap, while Maududi, Hamidullah, Khattab, and Abdel Haleem
are additional-edition requests. Talal Itani's `ClearQuran` must not be conflated with
Mustafa Khattab's *The Clear Quran*.

Primary evidence: [QuranEnc API and republication conditions](https://quranenc.com/en/home/api).

### Quranpedia and KFGQPC Arabic corpora

Al-Duri is the best new Arabic text to investigate because the KFGQPC developer page
identifies it as a riwayah read in Sudan and East Africa and supplies developer formats.
Quranpedia also provides a versioned dump. That establishes relevance and source
readiness, not a complete rights chain.

Quranpedia's licence grants use of its digitization, structure, verification, and
metadata, and sets conditions for republishing dumps. Its mushaf descriptions identify
the relevant editions as issued by KFGQPC. The Quranpedia policy cannot be assumed to
override upstream rights or provenance. No explicit KFGQPC verse-dataset redistribution
grant was verified. Al-Duri must remain `conditional/unknown` until that point is resolved.

The Quranpedia Hafs Nastaliq mushaf is likewise an **audit candidate**. Its metadata says
it is a KFGQPC issue used in India and Pakistan and does not match the printed edition.
Whether its bytes match Quran Foundation, QuranWBW, or common 15-line products is an
unperformed comparison, so interoperability is a hypothesis. It must be named as its
exact source edition and must not silently replace the existing MIT-licensed
DigitalKhatt `indopak` text.

Shu'bah, al-Susi, al-Bazzi, and Qunbul are technically available but no broad general-user
adoption was established. Fonts, Nastaliq rendering, 13/15/16-line layouts, QCF glyph
streams, tajweed colouring, and Braille are different product/data axes and must not be
presented as missing verse-text scripts.

Primary evidence:
[KFGQPC developer platform](https://qurancomplex.gov.sa/en/techquran/dev/),
[Quranpedia usage policy](https://quranpedia.net/api-docs#usage-policy),
[Quranpedia dumps](https://api.quranpedia.net/dumps?lang=en), and
[Quranpedia data licence](https://api.quranpedia.net/dumps/LICENSE.md).

### Source access is not a general redistribution grant

Rights findings must remain source- and work-specific:

- Tanzil's CC BY notice covers its Arabic Quran text and requires verbatim copying,
  attribution, a link, and retention of its notice. Tanzil translations have separate
  non-commercial and no-redistribution terms.
- Quran Foundation permits display in an application but prohibits redistributing QF
  Content or raw API data as a dataset without a separate written licence.
- Quranpedia explicitly leaves translations and contemporary works with their authors
  and publishers. Its dump policy cannot cure missing translation permission.
- A wrapper repository's software licence, an API response, a downloadable file, or a
  site's general terms cannot be transferred automatically to an imported corpus.

Primary evidence:
[Tanzil text licence](https://tanzil.net/docs/Text_License),
[Tanzil translation terms](https://tanzil.net/trans/), and
[Quran Foundation developer terms](https://api-docs.quran.com/legal/developer-terms/).

## Transliteration corrections

The audit should use four distinct concepts:

1. **Orthographic transliteration** maps writing systems under named rules. It may be
   language-neutral or use an audience's writing conventions. Kemenag SKB Latin belongs
   here; LPMQ explicitly distinguishes its letter mapping from sound transcription.
2. **Reader transliteration** is an authored readable romanization whose phonetic
   precision is not established by the label alone, such as the Tanzil English and
   Turkish corpora.
3. **Pronunciation transcription** explicitly approximates sound, syllables, or recitation
   for a named audience.
4. **Phonetic encoding** represents segments or recitation features for computation and
   is not ordinary reader prose.

Extended Buckwalter is a reversible one-to-one grapheme/codepoint mapping. It belongs
under machine-oriented orthographic transliteration or a computational orthographic
subtype, not under phonetic encoding. Actual phoneme or phonological representations
belong in the fourth category.

A language therefore does not automatically have one transliteration, and a
transliteration is not necessarily language-specific. Romanized Urdu remains an Urdu
translation in Latin script if the content translates meaning rather than maps the Arabic.

No complete, ready-to-publish transliteration corpus with an unambiguous redistribution
grant was verified. Kemenag Latin is complete but has unknown corpus rights. Tanzil
English and Turkish are complete but need direct permission. QUL resources need original
provenance and per-resource terms. CLDR provides licensed transformation rules, not a
Quran corpus or an authoritative pronunciation aid. Any CLDR-derived experiment needs
an adaptation-permitted Arabic source, exact rule/source versions, complete Quranic-mark
coverage, and expert review before publication.

## Repository and live-behavior corrections

The current system is not an empty legacy shell. It already has:

- ten Arabic text editions with explicit Hafs, mapped, or own verse identity;
- 83 granted translations in the gated build, and 84 plus one unknown-rights
  transliteration in the current override artifact;
- frozen npm `dist/` byte parity and add-only current CDN paths;
- generated docs and catalogue counts from the same Python data structures;
- build-time font coverage checks and local OFL fonts;
- chapter-only parallel fetching, promise caching, late-response protection, reproducible
  hash routes, persisted preferences, and lazy reciter loading; and
- 120 passing repository tests plus Ruff, formatting, and strict mypy checks.

The measured local override artifact has 10,953 files. README counts of 10,359 and 10,704
are stale. A clean gated build has 10,723 files. Any capacity statement must name which
build profile it measured.

The live cache behavior resolves an apparent report contradiction. On 2026-09-20,
`/translations/index.json` and `/transliteration/index.json` returned one-year immutable
cache headers through their wildcard rules; `/manifest.json`, `/chapters.json`, and
`/app/fonts.json` revalidated. Edition discovery can therefore remain stale for a year
even when a new edition is added. Fix the exact catalogue caching policy or introduce a
separately revalidated discovery URL before corpus expansion.

The live audit measured response bytes and inspected deployed source, but no browser was
available. Mobile overflow, visual hierarchy, focus behavior, Core Web Vitals, and the
ranking of UX impact are source-based or heuristic findings, not observed browser/user
results. Preserve that distinction in the final proposal.

## Recommendations in evidence order

### P0 — correctness, rights, and release truth

1. Fix the quickstart samples that say to join by verse `id` but demonstrate positional
   array joins.
2. Prevent Hafs-keyed transliteration from being merged by array position into the
   divergent Indo-Pak Al-Fatiha. Use an explicit mapping or suppress that optional layer.
3. Validate every hash-route enum and numeric bound before rendering; fall back safely on
   stale or malformed links.
4. Separate mutable edition discovery from immutable edition payload caching and verify
   the deployed headers.
5. Make the gated versus `--include-unverified-licenses` production profile an explicit,
   reviewed build input. CI currently proves a different rights profile from the
   documented production command.

### P1 — measured reader and documentation improvements

1. Add browser tests for existing deep links, local-storage migration, mapped verse
   identities, audio restrictions, rapid navigation, malformed data, keyboard behavior,
   narrow layouts, RTL/LTR content, and failed optional layers.
2. Render the chapter directory after its essential metadata is ready instead of blocking
   on every edition catalogue; measure the resulting first-useful-view change.
3. Label each displayed translation by edition, repair picker dialog semantics and focus
   return, replace hidden mobile navigation, and make reader settings discoverable without
   a hidden horizontal scroll gesture.
4. Preserve generated catalogue truth, static/no-script documentation, same-origin fonts,
   chapter-level requests, lazy reciters, hash URLs, and local-storage keys.

These changes are all feasible in the existing HTML/CSS/ES-module implementation.

### P2 — source and permission clarification

1. Ask QuranEnc whether its republication conditions cover the exact omitted Bengali and
   Malay editions, why they are absent from the canonical list, and whether a supported
   versioned bulk source exists. Then validate all 114 surahs and attribution/version data.
2. Resolve the KFGQPC/Quranpedia rights chain for al-Duri before ingestion; independently
   validate numbering, Hafs mapping, source bytes, and print samples.
3. Compare the Quranpedia Hafs Nastaliq bytes with the existing DigitalKhatt edition and
   claimed interoperability targets only after rights are clear.
4. Seek corpus-specific grants for Kemenag Latin and Tanzil English/Turkish reader
   transliterations. Store the resulting terms per edition.

Contacting rights holders remains outside this audit; these are blocking questions, not
assumed permissions.

### P3 — architecture after evidence

Add machine-readable schemas and generated-tree validation without changing existing wire
keys or immutable paths. Record the public path/hash set, npm pack contents, deployed
response headers, reader request waterfall, compressed assets, accessibility behavior,
and narrow-screen behavior before changing the web build.

The current evidence does not establish Astro, Tailwind, Vue, or React as a speed or
correctness fix. The docs transfer is already small, the Python renderer preserves
single-source catalogue truth, the reader modules are about 48.4 KB uncompressed, and the
app CSS is about 2.3 KB gzip. First fix the evidenced issues in the current stack.

If an approved multi-page/componentized information architecture later creates repeated
page-shell work, evaluate isolated Astro static output and Tailwind against the preserved
Python build, frozen root `dist/`, current URLs, and measured asset baseline. Retain the
typed vanilla reader by default. Vue is a later comparison only if a concrete interaction
or maintenance problem remains and parity plus payload measurements justify the runtime.
React has no repository-specific advantage established by this audit.

## Unresolved caveats

- No direct usage telemetry or user research ranks translation languages, editions, or
  documentation tasks.
- No omitted QuranEnc candidate received a full 114-surah validation in this audit.
- No reviewed legal opinion resolves KFGQPC ownership versus Quranpedia's digitization
  grant; the reports correctly stop at a rights uncertainty.
- No real-browser, screen-reader, audio-playback, mobile-layout, or throttled performance
  run was available. Source inspection found real risks but cannot prove their visual or
  timing impact.
- Quranpedia and QuranEnc data are continuously corrected. Any future ingestion needs a
  versioned update policy that is compatible with this repository's immutable public URLs.
- The current live site intentionally includes restricted/unknown Kemenag derivatives via
  an override. Modernization must not hide or silently normalize that unresolved choice.
