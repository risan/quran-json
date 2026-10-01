# Track A1 report (D7, D8, D9, D5, D4)

Merged into `overhaul/quran-json-v5` at a852939b, plus 9a6f4399 (Tanzil notice quoted verbatim
from https://tanzil.net/docs/text_license, checked 2026-10-01).

- D9: removed `transliterations.py`, `review.py`, `data/transliteration-candidates/`,
  `tests/test_transliterations.py`, `data/meta/licensing-review.json`, the `licenses` command.
  `/transliteration/index.json` still written.
- D7/D8: removed `dist/`, `build.py`, the `build` command, `fetch --lang`, legacy config, the
  legacy snapshots (`data/quran.json`, `data/chapters/`, `data/editions/`, `drift.json`) and
  their 22 provenance records, the parity CI steps, the `--include-unverified-licenses`
  profile and Kemenag translation/latin publishing. Root `package.json` is private tooling.
  `test_dataset.py` ported to `cdn_tree`.
- D5: every manifest script has `license` and `reading`; Tanzil `notice` on every Tanzil
  chapter object; schemas updated; MP3Quran audio `unknown`; Islamic Network terms URL fixed;
  "0 shared verses" claim removed; Indo-Pak names fixed.
- D4: data paths cached one day + stale-while-revalidate; `/_astro/*` immutable;
  `quran-json fetch --check` + weekly `.github/workflows/upstream.yml`.

Open: `fetch --check` is only covered by mocked tests (a live run is ~110 requests); a network
error makes the weekly job fail, which is intended (it needs a look either way).
Tests: 124 passed, 2 skipped (site build tests need `.build/assembled`); ruff, mypy, verify pass.
