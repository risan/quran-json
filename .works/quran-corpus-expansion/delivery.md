# Quran corpus expansion — local delivery

Status: completed locally. Independent data, Arabic/reader and transliteration-import reviews all passed with no open findings. Source-access and completeness limits are recorded below.

## Candidate outcomes

| Candidate | Outcome |
| --- | --- |
| Quranpedia Hafs Nastaliq, mushaf 3 | Added as a distinct Arabic edition; 114 chapters / 6,236 verses; direct Hafs identity |
| Quranpedia al-Duri an Abi Amr, mushaf 6 | Added as a distinct Arabic edition; 114 chapters / 6,218 native verses; explicit Hafs joins |
| Bengali Zakaria | Complete official translation added |
| Bengali Rowwad | Complete official translation added |
| Malay Basumayyah | Complete official translation added |
| Russian Rowwad | Complete official translation added |
| Korean Hamid | Complete official translation added |
| Italian Rowwad | Complete official translation added |
| Ukrainian Yakubovych | Complete official translation added |
| Korean Rowwad | Official snapshot acquired and retained with provenance; withheld from both publication profiles because 1,955 upstream translations are blank, covering chapters 14–35 |
| Tanzil Turkish / Muhammet Abay | Private local input acquired and validated: 114 chapters / 6,236 verses; restricted and excluded from repository/public corpora |
| Tanzil English | Existing snapshot reused; no duplicate corpus |
| Kemenag Latin | Existing snapshot reused; existing unknown-rights gate retained |
| QUL 71, 469, 475, 478 | Source descriptors and manual-export import support added; official exports still required; unknown rights, no public activation |

Korean Rowwad's supported API, website and uncompressed SQLite agree with the blank rows. The official catalogue labels the edition in progress. No complete same-edition official alternative was established. Korean Hamid is a separate edition, not a substitute under the Rowwad identity.

## Reader and data behavior

- Native Arabic counts govern navigation, saved resume and headings; optional layers remain validated against canonical Hafs counts.
- Duri Al-Fatiha keeps the exact source mapping `[2,3,4,5,6,7,7]`. Its source basmala is explicit unnumbered chapter-1 furniture, with no invented verse ID, optional join or audio position.
- Declared reading identity controls per-ayah audio compatibility. Duri does not use Hafs-indexed per-ayah playback.
- Supplemental QuranEnc registrations are separate from the canonical 75-entry catalogue. Pinned archive identities and normalized snapshot identities are recorded separately.
- Publication excludes incomplete editions even under the unverified-licence override. New private transliteration candidates cannot be activated by that override.

## Evidence

- [Source decisions](source-decisions.md)
- [Transliteration source decisions](transliteration-decisions.md)
- [Data implementation](implementation-data.md)
- [Reader and transliteration implementation](implementation-transliteration.md)
- [Data review](review-data.md)
- [Arabic and reader review](review-arabic-reader.md)
- [Transliteration review](review-transliteration.md)

The final default build contains **12 Arabic editions, 90 translations across 62 languages, and 0 transliterations**, in 11,760 files. The explicit unverified-licence profile contains 12 Arabic editions, 91 translations and 1 existing transliteration; it still excludes incomplete Korean Rowwad and all new restricted/unknown transliteration candidates.

Verification receipts record 151 passing Python tests after the final candidate-import correction, Ruff lint/format, mypy, the canonical Astro site build, targeted data/site contracts and a clean diff check. The reader's 12 Node regressions and full browser harness pass. Independent review confirmed all 10,697 existing immutable data payloads remain present and byte-identical. The frozen npm `dist/` remains unchanged, and the final safe `cdn/` matches `.build/assembled` byte-for-byte.

Work remains local; no commit, push or deployment was performed. See the implementation and review reports above for commands, hashes and the final manual-import review.
