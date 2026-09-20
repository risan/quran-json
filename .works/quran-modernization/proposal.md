# Quran modernization: decisions and research shortlist

Date: 2026-09-20

## What the audit established

The current gated build already includes ten Arabic text editions and 83 granted translations. The existing production-style override adds a Kemenag translation and Latin transliteration with their restricted/unknown statuses retained. The default build has no granted transliteration. The legacy npm corpus remains a separate compatibility artifact. See [repository evidence](scout-quran-json.md).

The audit did not verify any newly identified corpus as ready for ingestion. This is a shortlist of useful source and permission investigations, not a list of approved additions.

| Priority | Candidate | Precise gap | What must be settled |
|---|---|---|---|
| First | al-Duri an Abi Amr | Additional riwayah, with documented use in Sudan/East Africa | KFGQPC/Quranpedia rights chain, source revision, verse identity and alignment |
| First | Quranpedia Hafs Nastaliq | Additional exact text edition to compare with existing DigitalKhatt IndoPak | Rights chain and byte/mark comparison; mainstream interoperability is not established |
| First | Bengali and Malay QuranEnc editions | Current-catalog language coverage; Bengali also exists in the restricted legacy tree | Why editions are absent from canonical API list, edition-specific grant, stable versions and full validation |
| Next | Modern Russian, Korean, Italian, Ukrainian | Modern Russian is an edition gap; other candidates add language coverage | Same source/rights/completeness checks |
| Later | Kazakh, Nepali, Marathi and further readings | Additional coverage worth evaluating | Demand, supported source, permission and validation |

The repo already imports all 75 editions returned by QuranEnc's canonical list. Fetchable but unlisted endpoints are conditional candidates. Popular translations such as Mustafa Khattab's *The Clear Quran* and Abdel Haleem need their own grants; the existing Talal Itani ClearQuran is a different work. See [corpus research](research-corpus.md) and [independent review](review-recommendations.md).

## Transliteration answer

Languages do not automatically have one Quran transliteration. A transliteration maps Arabic writing into a target script under a named scheme. Some schemes are language-neutral; others use conventions familiar to a particular audience. Pronunciation transcriptions are a related but different product. A Romanized translation is still a translation of meaning.

Prioritize corpus-specific permission for Kemenag Latin and Tanzil English/Turkish; investigate original provenance and terms for distinct QUL resources. Do not treat an API, downloadable file, software license, or romanization standard as permission to redistribute an authored Quran corpus. No complete newly publishable reader corpus was verified. See [transliteration research](research-transliteration.md).

Future edition metadata should distinguish source script, target script, audience language, named scheme, purpose, verse alignment, source revision, and the corpus's own license. Extended Buckwalter is a reversible orthographic encoding, not pronunciation transcription.

## Local implementation decision

Use Astro for componentized static documentation and the page shell, Tailwind for the shared styling system, and the existing modular JavaScript reader for interaction. Astro includes Vite. A Vue/React conversion is unnecessary for the evidenced UX fixes and is not part of this implementation.

This is a maintainability and design choice, not a claim that adding a framework makes the existing small site faster. The independent reviewer recommends current-stack fixes first; those fixes remain mandatory, and the new site must retain static HTML documentation, generated catalogs, small payloads and chapter-only fetching.

| Work | Result |
|---|---|
| Data contracts | Refreshable discovery catalogs, explicit current JSON schemas, meaningful validation and unchanged Quran payloads |
| Documentation | Obvious read/fetch/catalog entry points, correct ID-based joins, accessible mobile navigation and generated reference data |
| Reader | Correct optional-layer alignment, labeled translations, usable settings, safe deep links and resilient optional-data loading |
| Design | Restrained paper/ink palette, strong type hierarchy, generous reading measure, clear focus and mixed-direction text |
| Build | Isolated frontend output; Python retains data authority; frozen npm dist and existing public paths remain compatible |

Full requirements and ownership are in the [implementation plan](implementation-plan.md) and [roadmap](roadmap.md). Verification evidence is recorded with each child implementation and the integrated delivery report.

## JSON and directory direction

Keep the current chapter/whole-corpus split and edition-specific public URLs. Do not copy the entire corpus into a parallel versioned tree or repeat Arabic in each translation. Add schemas around the existing wire shapes, and put the frontend project in `site/` with staging outside the npm `dist/` directory.

A later richer catalog can distinguish riwayah, orthography, verse identity and font/layout metadata without renaming existing data fields. New text revisions need new paths where current paths promise immutability. Corpus expansion should follow source-specific permission and validation, not a blanket language checkbox.

## Operational boundary

This work is local only. No deployment, commit, push, or contact with rights holders is authorized or required. Existing gated and explicit unverified build modes remain distinguishable. Local cache-rule changes cannot retroactively recall responses already cached by browsers from the live site.
