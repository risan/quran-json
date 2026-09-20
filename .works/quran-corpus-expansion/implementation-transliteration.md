# Transliteration and reader implementation

Status: candidate support and reader integration complete; public transliteration publication
remains rights-gated. The shared Arabic manifest integration is landed in the assembled build.

## Transliteration candidates

`data/transliteration-candidates/registry.json` records the requested source identities and
`src/quranjson/transliterations.py` provides a no-network, fail-closed local importer.
`published_candidates()` exposes only entries with a committed snapshot and a `granted` corpus
status. The default registry currently returns no publishable new candidate.

| Candidate | Local outcome | Granularity | Publication state |
| --- | --- | --- | --- |
| Kemenag Latin | Reuses `data/kemenag/quran.json` | ayah | existing snapshot; rights remain `unknown` |
| Tanzil English | Reuses `data/editions/transliteration.json`; no duplicate bytes | ayah | existing restricted corpus |
| Tanzil Turkish / Muhammet Abay | Private local fetch validated: 114 chapters / 6,236 rows; SHA-256 `a4130441fb6c2e8c38510461cbb1588170f593d046680691c99cdb5fb474bb19` | ayah | withheld; restricted |
| QUL 71 | Evidence-backed keyed JSON `surah:ayah:word` and SQLite import support | word | withheld; manual export and unknown rights/reading identity |
| QUL 469 | Keyed JSON/SQLite ayah import support | ayah | withheld; manual export and unknown rights/reading identity |
| QUL 475 | Keyed JSON/SQLite ayah import support with source whitespace retained | ayah | withheld; manual export and unknown rights/reading identity |
| QUL 478 | Keyed JSON/SQLite ayah import plus strict `b/u/i` validation | ayah rich text | withheld; manual export and unknown rights/reading identity |
| QUL 72, 468 | Keyed ayah-import descriptors pending a complete canonical comparison; no alias until proven | ayah | withheld; manual export and unknown rights |

The importer checks the canonical 114 chapter / 6,236 ayah coverage, source order, duplicate and
missing identities, nonempty text, and word positions (each ayah must restart at word 1). It
retains word rows as rows and never concatenates them into an unreviewed ayah transcription.
SQLite is imported lazily so the
publish/render path remains usable on interpreters without `_sqlite3`. No authenticated QUL
download, preview scrape, or other restricted bytes were copied into the repository. QUL
reading identity stays unknown until an official export or source record establishes it.

Rich-text validation uses a parser and accepts only balanced, attribute-free allowlisted tags;
comments, declarations, processing instructions, malformed nesting, and unclosed tags fail.
Raw source text is retained for a future separately sanitized renderer. Candidates whose markup
is `unknown` remain opaque and are not treated as render-safe.

The private Turkish input used for validation stayed outside the repository and is not a
generated site asset. Its local receipt identifies Muhammet Abay, `tr.transliteration`, and the
2010-09-15 update; that receipt is intentionally excluded from the public tree. The restricted
status remains withheld even though the local import is complete.

## Reader and Arabic identity integration

The reader now consumes declared script identity rather than matching script names:

- `reading.riwayah`, `reading.qiraah`, `reading.verse_numbering`, and optional
  `audio.per_ayah` / `audio.verse_numbering` determine whether Hafs-indexed ayah audio is
  compatible. Duri therefore remains audio-safe even when an individual chapter’s count maps to
  Hafs; Hafs Nastaliq is eligible when it declares Hafs-compatible identity.
- `verse_ids_unjoinable_in` is preferred over broad count-difference metadata. Mapped Duri
  chapters join translations and transliterations through `number_in_hafs`, including the
  explicit Al-Fatiha map `[2,3,4,5,6,7,7]`; mapped count differences remain joinable unless a
  future manifest explicitly marks a chapter unjoinable. Missing or malformed maps fail closed
  rather than guessing by position.
- `native_chapter_counts` is used for chapter-grid labels and saved-resume validation when
  supplied. The fetched Arabic chapter remains the final deep-link bound, so native Duri counts
  do not inherit Hafs-only limits. Optional translation/transliteration payload validation still
  uses canonical Hafs chapter counts.
- Per-ayah reciter choices and player refusal are driven by the manifest identity. The old
  Warsh/Qalun name checks were removed from the app.
- Duri’s declared `chapter_furniture` bismillah renders before chapter 1’s numbered rows as
  Arabic text without a verse id, anchor, optional layer, audio control, or count. No furniture
  is inferred for other chapters.

`src/quranjson/web.py` measures arbitrary script IDs from their actual verse strings and chapter
names; no script-name branch was added. The shared CDN build includes the Duri chapter furniture
text in the coverage corpus, so the generated `fonts.json` covers both new Arabic IDs and the
declared source furniture. Coverage proves glyph presence only, not the visual quality of the
Nastaliq shaping.

## Verification

Focused evidence from this checkout:

- `node --test tests/reader/reader-regressions.mjs`: 11 passed, covering Indo-Pak, Warsh,
  mapped Duri Fatiha, count-different native chapters, malformed maps, declared audio identity,
  malformed preferences, native resume counts, and optional payload validation.
- `pytest -q tests/test_transliterations.py tests/test_build_env.py tests/test_corpus_expansion.py`:
  18 passed, including the poisoned-`sqlite3` render-import check, the complete supplemental
  translation gates, and the QUL 72/468 keyed-ayah import path.
- `ruff check src/quranjson/transliterations.py tests/test_transliterations.py`: passed.
- `mypy src/quranjson/transliterations.py`: passed.
- `node --check` passed for the changed reader modules.
- Full Python suite: `pytest -q` completed with 151 passed.

The browser scenarios in `tests/reader/browser-regressions.mjs` include Duri chapter 1/2 mapped
optional layers, native Duri 9:130 versus invalid 2:286 bounds, Duri furniture and per-ayah audio
filtering. Against the fresh safe assembled build at `http://127.0.0.1:8778`, the full harness
passes. The safe catalogue has zero transliterations because the existing Kemenag and Tanzil
resources remain rights-gated; the harness only asserts a transliteration block when a profile
actually publishes one.

## Shared integration receipt

The assembled manifest now publishes the identity fields named above, `native_chapter_counts`,
Duri's explicit chapter-1 mapping exception, and its declared chapter furniture. Duri's broad
count-difference list is retained as native metadata and is not treated as an unjoinable list:
its source maps remain valid for translation joins. The existing transliteration catalogue
continues to publish only rights-cleared editions; this registry is an import/readiness layer,
not a rights override.
