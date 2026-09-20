# Data contracts implementation

Status: implemented locally; no commit or push.

The data slice keeps the current CDN paths, payload bytes, license gate, and frozen `dist/`
tree intact. It adds machine-readable descriptions of the generated wire contract and a
tested cache policy for mutable discovery catalogues.

## Changes

- `src/quranjson/cdn.py:81-93` keeps `/text/*`, edition payloads, and fonts year-long and
  immutable, but adds exact `/translations/index.json` and
  `/transliteration/index.json` exceptions. Each exception detaches the inherited
  `Cache-Control` value and sets `public, max-age=60, must-revalidate`.
- `tests/test_cdn_site.py:14-77` models Cloudflare Static Assets inheritance, including
  wildcard plus exact matching and the `! Cache-Control` detach syntax. It proves that
  catalogue indexes revalidate while `/quran.json` payloads remain immutable. The previous
  wildcard-only policy would fail this test because the index would resolve to the immutable
  year-long value.
- `schemas/` contains Draft 2020-12 schemas for `manifest.json`, `chapters.json`, complete
  or per-chapter Arabic script layers, translation layers and catalogues, and transliteration
  layers and catalogues. `schemas/README.md` maps each schema to its public path.
- `tests/test_contracts.py:22-239` validates every schema with `Draft202012Validator`, checks
  generated default and explicit override trees once per session, and checks semantic
  chapter/verse identity, mapped riwayah joins, catalogue file pointers, direction, and
  manifest counts. Mapped IDs are checked against each chapter's Hafs-local range; the
  offset-adjusted full sequence must be monotonic and cover exactly `1..6236`, while
  legitimate split mappings may repeat an ID across adjacent verses. Malformed direction,
  duplicate or out-of-range mapped IDs, a missing mapping, duplicate chapter IDs, and
  missing verse text fixtures fail validation.
- `tests/conftest.py:29-34` shares one audio-free explicit override render between the
  Kemenag gate tests and contract tests. The default and override renders stay in pytest
  temporary directories; the ignored repository `cdn/` and tracked `dist/` are not targets.
- `pyproject.toml:14-20` and `uv.lock` add `jsonschema` to the development group only; data
  generation has no new runtime dependency.

## Verification

Passed:

- `UV_CACHE_DIR=/tmp/quran-json-uv-cache uv run pytest tests/test_cdn_site.py tests/test_contracts.py -q` — 10 passed.
- `UV_CACHE_DIR=/tmp/quran-json-uv-cache uv run pytest tests/test_kemenag.py -q` — 15 passed.
- `UV_CACHE_DIR=/tmp/quran-json-uv-cache uv run ruff check src tests/test_cdn_site.py tests/test_contracts.py tests/conftest.py tests/test_kemenag.py` — all checks passed.
- `UV_CACHE_DIR=/tmp/quran-json-uv-cache uv run ruff format --check src tests/test_cdn_site.py tests/test_contracts.py tests/conftest.py tests/test_kemenag.py` — 23 files already formatted.
- `UV_CACHE_DIR=/tmp/quran-json-uv-cache uv run mypy` — no issues in 19 source files.
- `git diff --check` — clean.

The contract tests read generated output from temporary directories and exercise both the
default rights-gated tree and the explicit `--include-unverified-licenses` tree. The latter
still publishes the existing Kemenag translation/transliteration only when explicitly
requested; no new corpus was ingested.

Cloudflare rule semantics were checked against the official Static Assets `_headers`
documentation: matching rules inherit headers, duplicate values are joined, and `! Header`
detaches an inherited header before replacement:
<https://developers.cloudflare.com/workers/static-assets/headers/>.

## Handoff

The static-site builder can consume the schemas directly from `schemas/` and should retain
the generated catalogue paths `/translations/index.json` and `/transliteration/index.json`.
The documented local preview should serve the assembled temporary `cdn/` output after a
data build; no site integration was made in this slice.
