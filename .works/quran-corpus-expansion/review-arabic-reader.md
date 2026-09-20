# Arabic corpus and reader semantic review

Status: **go — no material corpus/reader finding remains in the reviewed candidate**

Reviewed scope: the two new Quranpedia snapshots and their importer/validation/provenance
contracts, plus the reader's script identity, native verse-count, optional-layer, per-ayah audio,
and font-coverage behavior. Source grants were treated as settled. No product files or tests were
changed or run by this review.

## Verified source and snapshot identity

The pinned raw downloads inspected locally were:

| Script | Raw dump | Raw SHA-256 | Raw bytes | Committed snapshot SHA-256 |
| --- | --- | --- | ---: | --- |
| Hafs Nastaliq | `/tmp/quran-corpus-expansion/mushafs-3.json.gz` | `fbec857dd613946604fd4c004d7322778ecf1c058c46080e30702e9bf9959b02` | 395,980 | `7276ed5158d314d4f323545e24ff2912d411a3ac4e3c6bdc6ae3ffcf2c3a3c67` |
| al-Duri | `/tmp/quran-corpus-expansion/mushafs-6.json.gz` | `f6024036b0040afea6af7973abd78b883ab2a0837ae72f6360b69e597c53999a` | 421,957 | `d4734c7176dd666530c066e638d602669be6ac016b3da699fff599cb746a89ac` |

A direct raw-to-snapshot comparison found zero text differences, zero mapping differences, and
zero chapter/verse identity differences across all 6,236 Hafs Nastaliq rows and all 6,218 Duri
rows. Both have exactly 114 unique chapters numbered 1 through 114, and each chapter's native
verse IDs are contiguous from 1. Every source verse was already trimmed, so the parser's existing
`strip()` call did not alter these source strings.

`quranpedia.py` now pins mushaf ID, Arabic name, embedded license version, source bismillah, raw
archive byte count, and raw archive SHA-256 before accepting a refresh. `sources.py` records both
the raw archive identity and the parsed snapshot identity. The build validator independently checks
the rendered corpus shape and mapping.

## Verse identity and joins

Hafs Nastaliq has 6,236 rows and every source `number_in_hafs` is exactly the singleton native
verse ID. Both importer and build validation now reject a row whose map is not `[verse]`, which
supports the manifest's `verse_ids: "hafs"` contract without claiming byte compatibility with
another Hafs or print product.

Duri has 6,218 rows. Every native verse has a nonempty, integer, ordered, per-verse unique,
in-range `number_in_hafs` list. The maps are monotonic within every chapter. Forty-four chapters
have a native count different from canonical Hafs metadata; this does not make them unjoinable,
because the source maps cover the Hafs-keyed optional layers.

Duri Al-Fatiha is a declared coverage exception, not an unmapped chapter. Its seven numbered
source rows map to `[2, 3, 4, 5, 6, 7, 7]`; the source carries the basmala separately as unnumbered
chapter furniture. Thus every native row remains safely joinable, Hafs 1 has no numbered Duri row,
and Hafs 7 is intentionally used twice across the split ending. The validator now requires exactly
that missing/repeated shape and full Hafs coverage in every other chapter. The reader correctly
keeps translations and transliteration available for Duri chapter 1 and simply has no native row
on which to display the unused Hafs-1 optional text.

## Reader counts, audio, and fonts

The reader defers deep-link upper-bound validation until the selected Arabic chapter loads and
then uses the actual native row count. It also consumes `native_chapter_counts` when validating
saved resume links and presenting chapter counts. Translation and transliteration payloads remain
Hafs keyed, so their payload validation correctly continues to use canonical Hafs chapter counts.
This allows Duri 9:130, rejects Duri 2:286, and does not weaken optional-payload validation.

The player and reciter picker consume reading identity rather than script-name branches. Their
intended manifest contract makes Duri/Warsh/Qalun ineligible for the available Hafs per-ayah audio
and keeps Hafs Nastaliq eligible. Surah-scope audio remains available because it does not claim a
verse-following join.

The existing font report measures actual codepoint presence for every generated script. Direct
inspection found that all three bundled fonts contain every codepoint used by both new snapshots
(Duri includes U+200D). This proves glyph coverage only. The documentation and generated coverage
note correctly avoid claiming Nastaliq shaping fidelity or printed-layout compatibility.

### Bounded Duri basmala evidence and contract

The raw mushaf 3 and 6 payloads each carry one mushaf-level `data.bismillah` field; no surah has
an applicability flag. Quranpedia's [API documentation](https://quranpedia.net/api-docs) likewise
defines `bismillah` on a mushaf, separately from its surahs and ayahs. Quranpedia's own textual
[Duri Fatiha page](https://quranpedia.net/surah/6/1) prints the seven numbered rows beginning with
al-Hamdu, and its [Duri Baqarah page](https://quranpedia.net/surah/6/2) also starts at numbered
verse 1 without rendering the mushaf-level field. The source therefore does not establish a safe
general client rule such as "show before every chapter except 9."

Duri chapter 1 is narrower: its explicit map omits Hafs 1, the source supplies the Duri-specific
bismillah separately, and the declared coverage exception is limited to that chapter. The
implemented closed script descriptor is
`chapter_furniture: [{chapter: 1, position: "before-verses", kind: "bismillah", text: <exact source
string>, numbered: false}]`. The reader renders it before the verse cards with no verse ID, anchor, mapping,
translation/transliteration join, count, or audio control. Include the string in font coverage and
asserts that Duri has exactly this chapter-1 record and no chapter-9 record. This preserves source
furniture without inventing a verse or pretending that the dump declares a universal display
rule.

## Resolved material integration findings

1. **Generated manifest omitted the declared reading/audio identity.** Resolved: the generated
   descriptors and closed schema now separate `qiraah`, `riwayah`, and verse numbering. The fresh
   assembled manifest declares Duri as Abu ʿAmr / al-Duri / mapped with `per_ayah: false`, and
   Hafs Nastaliq as ʿAsim / Hafs / Hafs numbering with `per_ayah: true`.

2. **The shared contract helper assumed surjective coverage for every mapped corpus.** Resolved:
   it now consumes the manifest exception, requires exactly the Duri chapter-1 missing/repeated
   shape, retains full set coverage elsewhere, and allows legitimate adjacent split overlaps.

3. **Generated top-level attribution was stale.** Resolved: it now names all four Quranpedia texts
   and directs consumers to the exact per-snapshot version, mushaf identity, and archive checksum
   records without relabelling older Warsh/Qalun snapshots.

4. **The unnumbered Duri basmala was retained only as provenance.** Resolved with the bounded
   furniture contract above. The fresh assembled manifest carries the exact source string only for
   Duri chapter 1; the reader renders it before numbered rows, chapter 9 has none, and the font
   report includes the furniture text.

## Fresh assembled evidence and candidate identity

The assembled tree was regenerated at 2026-09-20 15:54:53 +07:00. Its inspected artifacts are:

- `manifest.json`: `c1cd7b0dd8f2d864e6135de53a2c88357c288260fe22ed2377aac4dcb99f3d50`
- `app/fonts.json`: `e97746f98cf931d73de95b3d4848e332c73cd3bdc3e5560f11442198cd625b6d`
- `text/hafs-nastaliq/quran.json`: `c8747ad1f05d8e721fb879b0c72589b426454cd4bb436483963bf366b0892914`
- `text/duri/quran.json`: `8d66e02d484c3c59985d7c00b78bceb871a883d11df0361890b5e717e30e4f8b`

Inspection of those generated outputs confirms 114 / 6,236 Hafs Nastaliq rows, 114 / 6,218
Duri rows, the 44 Duri native chapter-count overrides, the exact chapter-1 coverage exception and
furniture record, and no furniture record on another script or chapter. `fonts.json` reports Amiri,
Scheherazade New, and Noto Naskh Arabic usable for both new scripts with no missing codepoint.

The assembled reader bytes equal the reviewed source bytes for `app.js`, `reader-core.js`,
`audio.js`, `ui.js`, and `app.css`. The builder's implementation receipt (SHA-256
`992016c587b560a7864cd0f902dd7c60b7c069d4466d0b98411f06e5ebb0e53d`) records a passing full
browser harness against this fresh safe assembled build. Its expansion cases cover Duri chapter 1
and 2 optional joins, native Duri 9:130, rejection of Duri 2:286, chapter-1 furniture with none on
chapter 9, and removal of Hafs per-ayah reciters for Duri.

This review did not rerun the builders' tests. It independently inspected the source, pinned raw
dumps, normalized snapshots, final generated metadata/text/font artifacts, source-to-assembled
hash equality, and the browser receipt. No material corpus identity, alignment, count, audio, or
font defect remains in that scope.
