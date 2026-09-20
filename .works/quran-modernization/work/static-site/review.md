# Independent source review: static site integration

Date: 2026-09-20
Candidate: current shared worktree static-site slice
Verdict: **source review clean; full execution pending**

## Scope inspected

This pass inspected the current source in:

- `scripts/build-site.mjs`;
- `site/astro.config.mjs`, `site/package.json`, `site/package-lock.json`, and `site/src/**`;
- `tests/test_site_build.py` and `.github/workflows/ci.yml`;
- the static-site changes in `README.md`, root `package.json`, and `.gitignore`; and
- the legacy anchor set in `web/index.html` and tracked-path status for `dist/`, `data/`,
  and `config/`.

Reader behavior and reader-owned files were outside this pass. No test command was run in
this follow-up; the builder's full verification remains required before final delivery.

Key source hashes at review time:

```text
06e1e3413ae4b62510a1e2283435575d2f7c337bf71d141bba1f9b3ecf46bd9b  scripts/build-site.mjs
3d1ba9d370ae93d059a64e258f91a5f533f8f1679d88c287038fd7c3e4748838  site/src/lib/catalog.ts
b01aaa3f4099ee6e3e4e004d1257b96022257c0156924be810c5377e54f27fb3  site/src/pages/index.astro
89fc1cae743d8e9f43c27349ecb686d217b868f6ab16112ccf192a673e30a360  site/src/pages/app/index.astro
0581888b86ea82db6824e4326e7ccacb4d431e2639c646cf0c58c88863fff931  tests/test_site_build.py
c4f35e4ca3a333687809a5dd1618e0cf29935dadec02f98d876d3d3df027045e  .github/workflows/ci.yml
```

## Confirmed source behavior

- Astro writes to `.build/site`, while the Python data build writes to `.build/data` and
  assembly occurs in `.build/assembled`. The root frozen `dist/` tree is never a target.
- The overlay accepts only `index.html`, `app/index.html`, and files below `_astro/`.
  Existing non-shell targets cause a collision failure. The `_astro` prefix is separator-bound,
  so similarly named root files such as `_astroevil.json` are rejected
  (`scripts/build-site.mjs:44-70`).
- Data are copied before the shell overlay, and the live `cdn/` directory is replaced only
  after the Python and Astro builds and assembly succeed (`scripts/build-site.mjs:73-97`).
  This preserves corpus files and `_headers`; only the two intentional HTML shells and new
  hashed Astro assets may be introduced by the frontend step.
- The safe build is the default. The unverified corpus flag is passed to the Python publisher
  only when the operator supplies `--include-unverified-licenses`
  (`scripts/build-site.mjs:14-15,76-80`).
- Astro reads `manifest.json`, chapter metadata, both edition catalogues, the optional reciter
  index, and font coverage from the generated Python tree at build time
  (`site/src/lib/catalog.ts:95-112`). The documentation does not maintain a parallel handwritten
  edition list.
- The homepage is statically rendered and contains no framework hydration directive. Its
  JavaScript and Python examples join translations by verse `id`; mapped readings use
  `number_in_hafs` explicitly (`site/src/pages/index.astro:26-47`).
- Every legacy documentation anchor remains present. The new page adds `catalogues`, `fonts`,
  and `attribution` without removing the old `quickstart`, `endpoints`, `scripts`,
  `translations`, `transliteration`, `audio`, `compatibility`, or `licensing` anchors.
- The sample reader link now derives chapter 2 from the same generated chapter record used for
  its Al-Baqara label (`site/src/pages/index.astro:15-17,96`). The assembled-site regression
  pins that route (`tests/test_site_build.py:69-72`).
- The assembled-site checks resolve generated data paths, legacy fragments, same-origin assets,
  and reader module imports (`tests/test_site_build.py:33-90`). CI installs locked frontend
  dependencies, type-checks Astro, builds `.build/assembled`, and then includes these checks in
  the full Python test run (`.github/workflows/ci.yml:20-46`).
- The current worktree has no tracked change under `dist/`, `data/`, or `config/`.

## Findings resolved during review

Three concrete defects or evidence gaps were found while the builder was still working and are
fixed in the source hashes above:

1. the Al-Baqara task originally linked to reader chapter 1;
2. the Astro allowlist originally accepted any root filename beginning with `_astro`; and
3. CI originally built Astro without checking the assembled page, while the README overstated
   the coverage of `tests/test_web.py`.

The link now uses the generated chapter ID, the prefix is directory-bound, and
`tests/test_site_build.py` plus the CI ordering cover the assembled output. No material static
site source defect remains from this pass.

## Pending execution

This is a source verdict over a moving shared worktree, not final implementation sign-off. The
builder still needs to record the complete locked Astro build, assembled-site tests, Python
suite, lint/type checks, frozen `dist/` parity, generated payload preservation, and final output
measurements against the exact delivery candidate.
