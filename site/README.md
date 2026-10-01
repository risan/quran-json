# quran-json site

Astro + React + shadcn. Docs at `/`, reader at `/app/`.

Dev: build the data once from the repo root with `npm run site -- --no-cdn`, then run
`npm run dev --prefix site`. A dev middleware serves
`.build/data` (or `QURAN_JSON_SITE_DATA`) at `/manifest.json`, `/text/`, `/translations/` and the
other data paths, so the reader works on the dev origin.
Checks: `npm run lint|fmt:check|check|test --prefix site`. The e2e smoke test needs the assembled tree.
