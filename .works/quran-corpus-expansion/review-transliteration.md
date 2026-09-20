# Review: transliteration candidate registry and importers

Final verdict: **GO**. The publication and acquisition boundary remains fail closed, and
all findings from the initial review are resolved in the final candidate.

Reviewed:

* `src/quranjson/transliterations.py`
* `data/transliteration-candidates/registry.json`
* `data/transliteration-candidates/README.md`
* `tests/test_transliterations.py`
* public-builder reachability in `src/quranjson/`

Reference contract: `.works/quran-corpus-expansion/transliteration-decisions.md`.

## Closed findings

### Word completeness

Word imports require word 1 on the first row and every ayah transition, then require
sequential positions within each ayah. Regression tests cover a first ayah and a later
ayah starting at word 2.

### HTML preservation and safety

Rich markup validation uses `HTMLParser`, preserves the source string, and permits only
balanced, attribute-free `b`, `u`, and `i` elements. It rejects active attributes,
malformed nesting, comments, declarations, processing instructions, and unclosed tags.
`markup = none` uses an empty allowlist. `markup = unknown` stays opaque and is not wired
to any renderer.

### Evidence-honest QUL metadata

The four requested QUL resources keep their reading metadata unknown rather than inferring
Asim/Hafs from their 6,236-key alignment expectation.

QUL 72 and 468 are ayah-level `dedupe_candidate_of` records, not aliases. Both use the
`qul_ayah_json` source kind, so an explicit private keyed export reaches complete ayah
validation. Empty exports fail as truncated at 1:1, which proves these descriptors are
importable and fail closed before any whole-corpus identity claim is made.

QUL 71 accepts only the evidenced keyed JSON form or official-shape SQLite. The
unevidenced generic row-list parser was removed.

## Rights and publication boundary

* `quranjson.transliterations` is not imported by the CDN, config, CLI, or renderer.
  `published_candidates()` is empty and every candidate has `can_publish == false`.
* The new Turkish and QUL records are absent from `config.PENDING_EDITIONS`; the existing
  generic override cannot discover or publish them.
* No private corpus is committed. Tanzil Turkish has no snapshot reference and QUL sources
  have no snapshots.
* Turkish and QUL imports require an explicit local path. There is no downloader, token
  guessing, preview-page acquisition, or authenticated-site bypass.
* Kemenag and Tanzil English reuse existing snapshots; no duplicate English corpus was
  added.
* Kemenag and QUL rights remain `unknown`; Tanzil English and Turkish remain `restricted`;
  original QUL authors remain null. QUL copyright locators are resource-specific.
* SQLite is imported lazily. Official-shape ayah and word SQLite fixtures parse only when
  that import path is invoked.

## Private Turkish receipt

The private Tanzil Turkish file matches its durable receipt:

```text
path       /tmp/quran-corpus-expansion-private/tr.transliteration
bytes      730458
sha256     a4130441fb6c2e8c38510461cbb1588170f593d046680691c99cdb5fb474bb19
chapters   114
ayahs      6236
first      1:1  bismi-llâhi-rraḥmâni-rraḥîm.
last       114:6 mine-lcinneti vennâs.
```

The footer names Muhammet Abay, `tr.transliteration`, Tanzil.net, and the 2010-09-15
update. The file remains outside the repository; its receipt marks it `restricted` and
`withheld`.

## Verification

Fresh bounded reviewer checks:

```text
pytest tests/test_transliterations.py -q    12 passed
QUL 72 explicit empty export               ayah import is truncated at 1:1
QUL 468 explicit empty export              ayah import is truncated at 1:1
```

The builder's final receipt records 151 passing tests for the full Python suite and clean
mypy and Ruff checks. This reviewer reran only the bounded 12-test transliteration suite.

No open finding remains from this review. The candidate registry and local import layer
are ready to hand off with their current rights gate and publication isolation.
