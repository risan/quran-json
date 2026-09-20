# Independent review: data contracts and catalogue caching

Date: 2026-09-20
Candidate: current shared worktree data slice
Verdict: **changes requested**

## Material finding

### The semantic contract accepts corrupt chapter and mapped-verse identities

`chapters.schema.json` constrains the array length and each `id` range, but it does not
require the IDs to be the ordered sequence 1 through 114. `test_contracts.py` applies only
the schema to `chapters.json`, so duplicate or missing chapter identities pass.

The mapped-layer helper requires `number_in_hafs` to be nonempty and sorted, but it does
not reject a duplicate inside one verse, an out-of-range value, a missing Hafs ayah, or a
non-monotonic mapping across verses. The malformed test changes `[1, 2]` to `[2, 1]`, which
proves ordering only.

Fresh counterexamples accepted by the current checks:

```text
Warsh verse number_in_hafs = [1, 1]
chapters[0].id = 1; chapters[1].id = 1
```

Real Warsh and Qalun data establish the correct boundary. A Hafs ID may intentionally
appear in adjacent output verses where one Hafs verse is split, so flattened global
uniqueness would be wrong. Across all 114 chapters of both current mapped scripts:

- every individual mapping array is nonempty, sorted, and unique;
- the flattened sequence is monotonic nondecreasing; and
- the set of mapped IDs is exactly `1..Hafs chapter verse count`, with no gaps or
  out-of-range values.

Add those semantic checks and failure-capable fixtures. Keep cross-verse duplicates
allowed. Require `chapters.json` IDs to be exactly 1 through 114 in order.

The current test also samples only Uthmani whole text, Warsh chapter 1, the first
translation whole file, and the override Kemenag transliteration. This is representative
validation, not validation of every generated layer. Either walk every generated
script/edition whole file and chapter file, or narrow the implementation report so it
does not claim the generated trees are validated comprehensively.

## Confirmed behavior

The cache fix is correct. Cloudflare's official Workers Static Assets documentation says
that every matching `_headers` rule contributes, duplicate header values are joined, and
`! Header` detaches a value inherited from a broader rule. The exact rules therefore need
the detach before the replacement. See
<https://developers.cloudflare.com/workers/static-assets/headers/>.

A fresh local Workers Static Assets probe over the generated tree confirmed:

```text
/translations/index.json       public, max-age=60, must-revalidate
/transliteration/index.json    public, max-age=60, must-revalidate
/translations/en-rwwad/quran.json  public, max-age=31536000, immutable
/manifest.json                 public, max-age=0, must-revalidate
```

The in-test `_effective_headers` model agrees with both the official rule semantics and
the local runtime result; it is not merely encoding an assumed specificity rule. Update
the module comment that still names `wrangler pages dev` to describe the Workers Static
Assets check actually used by this project.

No payload or licensing drift was found:

- a baseline build from `git archive HEAD` and a current build produced byte-identical
  JSON trees (10,703 JSON files compared; `_headers` is the intended output change);
- no tracked `dist/` or `data/` file changed;
- the default tree still publishes 83 granted translations and no transliteration;
- the explicit override still publishes Kemenag while retaining `restricted` and
  `unknown` status; and
- `jsonschema` is a development dependency only.

## Verification run

```text
UV_CACHE_DIR=/tmp/quran-json-uv-cache uv run pytest \
  tests/test_cdn_site.py tests/test_contracts.py tests/test_kemenag.py \
  tests/test_parity.py -q
26 passed

Wrangler local static-assets probe: passed after using a writable XDG config directory
and lowering the local compatibility date to the installed workerd maximum.

Baseline/current generated JSON byte comparison: identical.
git diff --check: passed at review time.
```

The first Wrangler attempt was not a product failure: its logger targeted the managed
read-only user config directory, and the installed workerd supported compatibility dates
only through 2026-09-10. The second run used `/tmp` for configuration and an explicit
2026-09-10 local date.

## Follow-up source review: mapping fixes present

Date: 2026-09-20
Follow-up verdict: **the original mapping findings are resolved in current source; final
execution remains pending**

This follow-up preserves the original changes-requested evidence above. It inspected the
current `tests/test_contracts.py`, schema files, data-contract implementation report, and
tracked-path status. No new test command was run; the earlier 26-test result remains historical
evidence for its earlier candidate, and the builder must run full verification over the final
shared-worktree candidate.

Current relevant hashes:

```text
3a7b4000248adf677e61696ec13aea80d067366eb8a7462fbbcd300f8668ff48  tests/test_contracts.py
d0b7e2bdf8bd74adedf0f2afc4c48d0fb67edfd0947a5ce2f3d685942eca083b  schemas/chapters.schema.json
00826a99ff4f5a81ffd53ef9b8952a4897a6931ce1dd1b7ed261219951bb402c  schemas/script.schema.json
```

The corrected semantic checks now enforce the measured split/merge model without imposing
invalid flattened uniqueness:

- a whole layer must contain the ordered chapter IDs 1 through 114
  (`tests/test_contracts.py:47-49`);
- verse IDs must be the ordered local sequence (`tests/test_contracts.py:51-53`);
- each mapped verse must have a nonempty, sorted, unique `number_in_hafs` array and every value
  must fall inside that chapter's Hafs range (`tests/test_contracts.py:54-64`);
- the flattened mapping within a chapter is monotonic nondecreasing and its set covers exactly
  `1..chapter Hafs verse count`, so a Hafs ID may still legitimately repeat across adjacent
  output verses (`tests/test_contracts.py:66-70`);
- the offset-adjusted whole-corpus mapping is monotonic and covers exactly `1..6236`
  (`tests/test_contracts.py:72-83`); and
- shared chapter metadata IDs must also be exactly 1 through 114
  (`tests/test_contracts.py:86-88`).

Failure-capable fixtures now reject a duplicate within one mapping array, an out-of-range
mapping, a missing Hafs mapping, a duplicate script chapter ID, and duplicate shared chapter
metadata (`tests/test_contracts.py:168-219`). The generated-tree check walks every whole-script
file, including both mapped riwayat, and validates chapter 1 for every published translation
(`tests/test_contracts.py:113-135`). The report now describes that actual scope rather than
claiming that every translation chapter is traversed.

The original byte and licensing evidence remains applicable to the reviewed data slice:
10,703 baseline/current JSON files were identical, no tracked `dist/` or `data/` path changed,
and the default versus explicit-override licensing behavior did not drift. The current source
review also found no tracked change under `dist/`, `data/`, or `config/`. Those statements must
still be reconfirmed by the builder's final exact-candidate verification because the shared
worktree continued changing after the original run.
