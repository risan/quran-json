# Arabic and translation expansion review

Status: **GO — no unresolved data blocker**

Scope inspected: `data/quranenc/{catalogue,supplemental}.json` and the active changes in `src/quranjson/{config,quranenc,quranpedia,sources,cdn,build}.py`. Product files were not edited and source-rights decisions were treated as settled.

## Verified so far

- The canonical QuranEnc catalogue remains a separate, unmodified 75-entry file. Its current SHA-256 is `74fc274893dbf2eec954eddf733c47248d4636c1a06b463b725606921d4123e4`.
- `data/quranenc/supplemental.json` contains exactly the eight approved keys, with unique keys and no overlap with the canonical catalogue. All are `ltr`; their language codes and versions match the source decision record.
- Each supplemental record carries the official browse URL, bulk ZIP URL, terms URL, manual-registration marker, checked date, raw archive byte count, and raw archive SHA-256.
- `quranenc.merged_catalogue()` now rejects duplicate keys across catalogue files and preserves the deterministic canonical-then-supplement order.
- ZIP/SQLite imports remain inside `parse_translation()`; importing the catalogue helpers on the render path does not import `sqlite3`.
- Raw archive byte and SHA pins are checked before parsing, while parsed snapshot hashes and source metadata are recorded separately in provenance.
- The publication and licensed-build consumers now use the merged catalogue, and Hafs Nastaliq now resolves through the Quranpedia snapshot path.
- The eight locally retained official ZIPs match every registered archive SHA-256 and byte count. A direct SQLite-to-snapshot comparison covered 49,888 rows and found zero chapter/verse identity, translation-text, or footnote differences.
- Seven supplemental translations contain exactly 114 chapters and 6,236 contiguous Hafs-keyed, nonblank rows. Their retained footnote counts are: Bengali Zakaria 3,608; Bengali Rowwad 1,640; Russian Rowwad 73; Italian Rowwad 87; Ukrainian Yakubovych 472; Malay and Korean Hamid contain none upstream.
- Korean Rowwad v1.0.11 is structurally 114 chapters / 6,236 rows but contains 1,955 blank upstream translation rows across chapters 14–35. The snapshot is retained for provenance and explicitly withheld from both default and licence-override publication. The override does not bypass technical incompleteness.
- The two Quranpedia snapshots match their pinned raw dump SHA-256 and size. Independent raw-to-snapshot review recorded zero text, mapping, or identity differences. Hafs Nastaliq is 114 / 6,236 with an exact singleton identity map. Duri is 114 / 6,218, has 44 native-count differences, and retains its source mappings including the explicit Al-Fatiha missing-Hafs-1/repeated-Hafs-7 shape.
- No pre-existing tracked corpus snapshot changed. The only tracked file under `data/` changed is the provenance registry; all ten corpus files and the supplemental catalogue are additive.
- A fresh baseline-to-assembled comparison checked 10,697 pre-existing immutable chapter, audio, text, translation, and transliteration payloads. None was missing and none changed.

## Resolved review findings

### [High] Prove the Hafs Nastaliq map is an identity map

`config.SCRIPT_VERSE_IDS` declares `hafs-nastaliq` to have Hafs-native verse IDs, so translations and reader joins use each published native verse ID directly. The first candidate validator accepted any monotonic, full-coverage map, including multi-ID and overlapping rows.

Resolved: both the importer and a negative unit test now require every Hafs Nastaliq row to have `number_in_hafs == [verse]`. The actual 6,236-row source satisfies the invariant.

### [High] Do not treat legitimate mapped overlaps as corruption

The first whole-corpus contract required every mapped Hafs ID outside the Duri Al-Fatiha exception to occur once. Quranpedia's legitimate split/merge model allows adjacent source rows to reference the same Hafs verse; Duri and the established Warsh/Qalun corpora contain such overlaps.

Resolved: the global contract now requires monotonic coverage and the declared missing-ID exception without imposing global uniqueness. The exact Al-Fatiha exception remains strict.

### [High] Never let the rights override publish an incomplete translation

The first metadata implementation selected permissive empty-row parsing independently of publication availability.

Resolved: catalogue validation now rejects `allow_empty: true` unless the edition is explicitly `withheld`, publication filters withheld entries for both build profiles, and generated catalogues explain the Korean Rowwad blocker.

## Final verification evidence

The strict translation validator covers every supplemental snapshot; catalogue tests cover collision and availability failures; a disposable failure-path test proves a raw SHA mismatch aborts before replacing an existing snapshot; and default plus override builds both prove Korean Rowwad stays withheld. The README now distinguishes the canonical 75 from the seven published supplements, records the corrected 90/91 profile totals, and removes Bengali and Malay from the remaining gaps.

The builder's final receipt records `uv run pytest -q` at 151 passed, Ruff check and format check passed, mypy passed, `npm run site` passed, the targeted site/contract/corpus expansion tests passed, `.build/assembled` and `cdn` matched, and `git diff --check` passed. I did not rerun that suite; this independent pass verified the imported source bytes, publication semantics, mappings, provenance, documentation correction, and the 10,697-file immutable baseline comparison described above.

Korean Rowwad's withheld status is a transparent upstream completeness limit, not a release blocker. No other material data issue remains in the inspected scope.
