# Architecture research: data package, documentation, and reader

Date: 2026-09-20

## Recommendation

The proportionate default is **keep the Python-generated static HTML/CSS/JavaScript site, improve it in place, add browser evidence, and keep the Python pipeline as the sole authority for Quran data**. The present site is already small and static: the generated docs HTML is 51,600 bytes (about 10.9 KB local gzip), and the reader's five JavaScript modules total 48,444 source bytes (about 14.7 KB local gzip). There is no measured performance or maintenance failure that currently justifies a second Node build, a framework runtime, or an output overlay.

If the approved information architecture later splits documentation into reusable pages, or repeated UI work demonstrates that the templates are the bottleneck, use **Astro static output** as the upgrade path. [Astro builds on Vite](https://docs.astro.build/en/recipes/add-yaml-support/), so that would be one Astro project rather than an Astro site beside a separate Vite SPA. Keep the existing reader as vanilla modules first; Vue is the preferred framework only if a comparison proves it solves a specific reader problem.

**Selected local implementation:** the parent work has chosen the bounded Astro option now as a maintainability and product-design choice: componentized static documentation and app shell, Tailwind 4 tokens/utilities, and the existing modular JavaScript reader unchanged. This choice explores the requested technology without claiming a measured speed necessity. It explicitly excludes a TypeScript or Vue/React reader migration and any public data URL rewrite.

This is a proportionate split:

- Documentation is content-first and already arrives as semantic static HTML with no framework runtime. First simplify its information hierarchy, fix observed examples, and improve navigation in the existing template. If componentization becomes valuable, Astro components render to HTML without client JavaScript by default, while an explicitly hydrated component becomes a client island ([Astro islands](https://docs.astro.build/en/concepts/islands/)).
- The reader's five JavaScript modules already separate API access, state, audio, controller, and rendering. It has deliberate chapter-level fetching, memoization, stale-response protection, and lazy reciter loading. Preserve those strengths, add browser tests, and split or type modules only when the changes themselves require a build step.
- If a later UI rewrite earns that cost, Vue is the better fit of the two proposed framework choices because the current reader is template- and DOM-oriented. Vue single-file component templates can preserve the existing semantic HTML and event flow with less translation than JSX. This is an architectural fit judgment, not a speed claim. Both choices are officially supported: Astro's [Vue integration](https://docs.astro.build/en/guides/integrations-guide/vue/) and [React integration](https://docs.astro.build/en/guides/integrations-guide/react/) provide rendering and client hydration.
- The current CSS is only about 3.9 KB local gzip across the shared and docs styles, plus 2.3 KB for the app. Start with CSS custom-property tokens and the existing stylesheets. If Astro is adopted and utility classes demonstrably improve repeated UI work, use Tailwind 4 through its Vite plugin while retaining Arabic typography, bidi, print, font-face, and prose rules in ordinary CSS. The older `@astrojs/tailwind` integration is deprecated ([Astro styling guide](https://docs.astro.build/en/guides/styling/), [deprecated integration notice](https://docs.astro.build/en/guides/integrations-guide/tailwind/)).
- Keep deployment static. Astro's default output is `static`, which prerenders pages ([configuration reference](https://docs.astro.build/en/reference/configuration-reference/#output)); Cloudflare's Astro deployment guide shows the same static asset-directory deployment already used here ([Cloudflare deployment](https://docs.astro.build/en/guides/deploy/cloudflare/)). No SSR adapter, database, or server endpoint is needed.

Do not treat the site migration as a data redesign. The public package is the product, and changing its URLs or bytes is much riskier than replacing the website renderer.

## Repository evidence that shapes the decision

- The repository ships two public generations. npm exposes the frozen `dist/` tree and still points `main` at `dist/chapters/en/index.json` ([package.json](../../package.json#L24)); Cloudflare serves the generated `cdn/` tree ([wrangler.jsonc](../../wrangler.jsonc#L12)). Astro's default output directory is also named `dist`, so building Astro at repository root with defaults could overwrite or mix with the legacy npm payload. The site needs its own root and output directory.
- One Worker currently serves docs, `/app/`, and all JSON ([README](../../README.md#L48)). The Python renderer substitutes catalog data into `web/index.html`, copies the app and assets, and measures font coverage ([web.py](../../src/quranjson/web.py#L1), [web.py](../../src/quranjson/web.py#L198)). That single-source behavior is valuable and must survive: Astro should consume generated catalog data; it must not gain a second handwritten list of editions.
- The current reader is already economical. Its five JavaScript files are 48,444 bytes uncompressed and approximately 14,702 bytes when each source file is gzipped locally. It memoizes same-page JSON requests, relies on the HTTP cache, and loads chapter-level Arabic, transliteration, and chosen translations in parallel ([api.js](../../web/app/api.js#L7), [app.js](../../web/app/app.js#L258)). It also defers the 136 KB reciter catalog until needed ([app.js](../../web/app/app.js#L46)). A framework rewrite should preserve these decisions and prove its payload cost.
- Reader URLs are a compatibility surface too: `#/{chapter}[:{verse}]` plus script, translation, transliteration, reciter, and font parameters reproduces a view ([app.js](../../web/app/app.js#L1)). The retained reader must continue to parse and emit this exact form.
- Arabic editions cannot be modeled as interchangeable strings. Warsh and Qalun use mapped Nafiʿ verse numbering; Indo-Pak differs in Al-Fatiha; translations are keyed to Hafs ([README](../../README.md#L176), [README](../../README.md#L200)). Font coverage is also a build gate, not presentation trivia ([web.py](../../src/quranjson/web.py#L155)). Those distinctions belong in typed catalog records and invariant tests.
- A clean gated build measured **10,723 files**; the ignored local `cdn/` generated with `--include-unverified-licenses` measured **10,953 files** on 2026-09-20 ([repository scout](scout-quran-json.md#L104)). The README's older 10,359 count is stale, and the documented free-plan limit is 20,000 ([README](../../README.md#L25)). Duplicating the whole tree under a new versioned prefix would exceed the remaining allowance before future editions are added. CI proves the gated build while the documented production command uses the override, so that rights-sensitive input must remain explicit.
- Current wildcard headers mark `/translations/*` and `/transliteration/*` immutable for a year, which also catches each mutable-looking `index.json` ([cdn/_headers](../../cdn/_headers#L7)). New catalog discovery should live outside those immutable wildcards or receive a proven exact-path cache rule; previously cached catalog bytes cannot be recalled merely by changing a future header.

## Lower-risk option and selected Astro boundary

### Lower-risk option

The first local implementation should not split the Python publisher, replace its output flow, or add a production frontend build. Keep `quran-json cdn` generating `cdn/` from `web/`. Improve `web/index.html`, `web/assets/**`, and `web/app/**` directly; fix the catalog cache contract in Python; add schemas or boundary validation; and add browser tests around the existing reader. Record gated and override builds separately because they publish different catalogues and file counts.

This keeps one build and makes the visual/accessibility work reviewable without changing packaging. JavaScript modules can gain `// @ts-check` and JSDoc types without a runtime or bundler. A full TypeScript conversion can wait for an accepted build-tool boundary.

### Selected local Astro boundary

The selected local implementation uses the following isolated shape:

```text
quran-json/
├── site/                         # Node boundary; no frontend deps in Python package
│   ├── astro.config.mjs          # output: static, outDir: ../.build/site
│   ├── package.json
│   ├── src/
│   │   ├── layouts/Base.astro
│   │   ├── pages/index.astro
│   │   ├── pages/app/index.astro
│   │   ├── components/docs/*.astro
│   │   ├── lib/catalog.ts
│   │   └── styles/{tokens,global,arabic,prose}.css
│   └── public/                   # only site-owned static assets
├── web/app/                      # existing reader modules retained unchanged
├── schemas/                      # public JSON Schema plus fixtures
│   └── v1/{manifest,chapter,translation,transliteration,audio}.schema.json
├── src/quranjson/                # acquisition, normalization, QA, publication
├── data/                         # canonical inputs
├── .build/site/                  # disposable Astro output, never deployed directly
├── cdn/                          # assembled Worker artifact
└── dist/                         # frozen npm v3 artifact; never an Astro output
```

Build the selected Astro slice in three explicit steps:

1. The existing Python command creates a clean `cdn/` exactly as it does now.
2. Astro reads `cdn/manifest.json`, the two edition indexes, chapter metadata, and the font report at build time, then writes only site output to `.build/site`. This retains the current guarantee that documentation tables and counts come from the same published records.
3. A small overlay step replaces only the allowlisted site paths, preserves the existing reader modules, removes only explicitly superseded shell assets, and fails on any dataset collision. Existing JSON/schema checks, internal-link checks, and public-path/byte compatibility checks run before Wrangler may deploy.

Keep the root npm package metadata and legacy `dist/` behavior intact. The frontend can use npm, pnpm, or another locked Node package manager inside `site/`; it should not change what `npm pack` includes until a separately reviewed package-contract change.

Set Astro's canonical `site` URL, keep `base: '/'`, and choose `build.format: 'directory'` with `trailingSlash: 'always'` so `/app/` remains a real static directory. Astro documents `base`, `site`, and trailing-slash/build-format behavior in its [configuration reference](https://docs.astro.build/en/reference/configuration-reference/). Absolute dataset URLs beginning with `/text/`, `/translations/`, and so on remain valid on both published origins.

## Data model and public URL compatibility

Keep the current public payloads and paths first. Improve the internal model and machine-readable contracts around them. A useful internal discriminated model is:

```ts
type LicenseStatus = "granted" | "restricted" | "unknown";
type VerseIdentity = "hafs" | "mapped" | "own";

interface EditionBase {
  id: string;
  kind: "arabic" | "translation" | "transliteration";
  name: string;
  sourceId: string;
  sourceVersion: string | null;
  license: { status: LicenseStatus; url: string; attribution: string };
  files: {
    quran: string;
    chapters: string; // existing template ending in /{1-114}.json
  };
}

interface ArabicEdition extends EditionBase {
  kind: "arabic";
  reading: "hafs" | "warsh" | "qalun";
  orthography: "uthmani" | "imlaei" | "indopak" | "kemenag";
  verseIdentity: VerseIdentity;
  verseIdsDifferIn: number[];
  basmala: "embedded-as-ayah" | "chapter-furniture";
  requiredCodepoints: string[];
}

interface TranslationEdition extends EditionBase {
  kind: "translation";
  language: { code: string; name: string; direction: "ltr" | "rtl" };
  joinsTo: "hafs";
}

interface TransliterationEdition extends EditionBase {
  kind: "transliteration";
  sourceScript: "Arab";
  targetScript: "Latn";
  audienceLanguage: { code: string; name: string } | null;
  scheme: { id: string; version: string | null };
  purpose:
    | "orthographic_transliteration"
    | "reading_aid"
    | "pronunciation_transcription"
    | "phonetic_encoding";
  alignmentId: "hafs-kufi";
}
```

The exact enum values should be derived from the source inventory during implementation; the important point is to separate reading, orthography, verse identity, and display direction instead of hiding all of them behind `script` or `edition`. Transliteration is not inherently a language: a scheme can be language-neutral, while a pronunciation aid can target a particular audience language. `audienceLanguage` therefore stays nullable, direction follows the target script, and `alignmentId` describes this corpus's verse alignment rather than pretending every future transliteration must join to Hafs.

Publish JSON Schemas for the existing shapes and run them over every generated file. Static types alone would not make network JSON trustworthy. Keep a small reader boundary parser that checks the required keys, chapter id, ordered verse ids, expected verse count, and mapped-Hafs arrays before rendering. A full generic schema validator in the browser is unnecessary unless measurement shows the small parser is insufficient.

Compatibility rules:

- Preserve every existing `/text/...`, `/translations/...`, `/transliteration/...`, `/audio/...`, `manifest.json`, `chapters.json`, and npm `dist/...` URL. Preserve bytes for artifacts promised immutable. Keep CORS behavior.
- Do not rename `id`, `text`, `translation`, `transliteration`, `number_in_hafs`, or existing catalog fields. New internal names map back to the current wire format.
- Add new editions at new paths. Corrections to immutable content get a new edition/revision id; the old file stays available.
- If a better discovery layer is needed, add a small `/catalog/v2.json` outside immutable collection wildcards. Give it a short cache lifetime with revalidation and let it point to existing immutable payloads. Do not clone the 10,953-file corpus under `/v2/` merely to make paths look uniform.
- If a future payload format truly warrants v2, introduce it per edition and measure file-count headroom first. The chapter/full-corpus dual form is currently useful: the reader avoids multi-megabyte downloads while bulk consumers retain one-file access. There is no evidence yet that regrouping chapters would improve the product.

## Reader loading, caching, and failure behavior

Retain the current chapter-first strategy in `web/app/api.js`:

1. On app start, request the manifest, chapter metadata, edition catalogs, and font coverage in parallel. Keep reciters lazy.
2. On chapter selection, request only the selected Arabic chapter, optional transliteration chapter, and up to the supported translation chapters in parallel. Never download a full `quran.json` for the interactive reader.
3. Key an in-memory promise cache by full URL and evict rejected requests, as the current implementation does. Let immutable HTTP responses provide cross-session caching.
4. Associate every navigation with an `AbortController` or monotonically increasing request token. A late response must never replace the chapter chosen more recently. The current token behavior is the compatibility baseline.
5. Validate each payload before merge. Render a specific retryable error for a failed layer; Arabic failure blocks the chapter, while an optional translation failure can leave the Arabic readable and name the failed edition.

Adjacent-chapter prefetching is a later experiment, not part of the migration baseline. Add it only if navigation measurements show a problem, cap it to one Arabic chapter while idle, and respect `navigator.connection?.saveData` where available.

Do not add a service worker in the first migration. The browser already receives year-long immutable caching for data, and service-worker lifecycle bugs could leave scripture or catalogs stale. If offline reading becomes an explicit requirement, add it as a later feature with a visible download action, versioned cache names, a storage budget, and eviction for chapter payloads. The maintained Vite PWA project does offer an [Astro integration](https://vite-pwa-org.netlify.app/frameworks/astro), but installing it is not itself an offline-content policy.

## Documentation and search

Split the current long page into a concise landing page plus task-based reference pages only if user testing shows the one-page form is hard to navigate. Astro pages should be semantic HTML and usable with scripts disabled. Keep generated catalog tables driven by the Python snapshot, with source/license status visible rather than copied into Markdown.

Do not add site search while documentation remains one or a few pages; headings, a table of contents, and browser find are cheaper and clearer. If the reference grows to many generated pages, Pagefind is a suitable later candidate because it indexes built static HTML and emits a static search bundle ([Pagefind build model](https://pagefind.app/docs/running-pagefind/)). It should index documentation, not silently become Quran full-text search: Arabic normalization, diacritics, readings, and translation search semantics need their own product specification.

## Staged migration

1. **Freeze evidence.** Record the complete current public path list, hashes for promised-immutable JSON, npm-pack contents, current hash-route behavior, compressed JS/CSS sizes, representative chapter request waterfalls, and accessibility/performance baselines.
2. **Build the selected static site boundary.** Add isolated `site/`, Astro static config, Tailwind 4, `.build/site` staging, and the site-path-only overlay. Componentize and simplify the documentation and app shell while reading the freshly generated `cdn` catalogs. Keep the reader's existing JavaScript files, hash routes, and local-storage keys unchanged.
3. **Prove the assembled behavior.** Add browser, accessibility, mobile-layout, and request-waterfall tests. Verify docs remain useful without JavaScript and the reader retains its startup, chapter-loading, race, alignment, font, and audio behavior. Compare built payloads with the recorded baseline.
4. **Harden data contracts.** Separate mutable catalog caching from immutable edition payloads. Add JSON Schemas or equivalent generated-tree validation, typed catalog records, boundary validation, and cross-file invariants without changing public URLs.
5. **Stop at the selected scope.** Do not migrate the reader to TypeScript, Vue, or React in this implementation. Consider those only after the shipped modular reader demonstrates a specific problem and a separately reviewed comparison earns the cost.
6. **Consider catalog v2, search, prefetching, or PWA separately.** Each needs measured demand and its own compatibility/cache acceptance criteria.

The evidence-first recommendation would keep the current production toolchain. The selected implementation deliberately limits the additional Astro/Tailwind toolchain to static documentation and shell generation, while retaining the vanilla reader. A React/Vue rewrite is not required for elegance, accessibility, or speed.

## Acceptance criteria for the architecture

### Compatibility and data integrity

- A clean build preserves the recorded URL set and SHA-256 for all existing immutable JSON and frozen npm `dist/` files; any intentional content correction appears at a new path.
- `npm pack --dry-run` retains the expected legacy files and entry point. Astro never writes to root `dist/`.
- Both published hostnames serve the same assembled bytes, CORS headers remain present, and cache rules distinguish revalidated catalogs from immutable content.
- Every output JSON validates against its schema. Referential checks prove catalog paths exist, chapters are 1 through 114, verse ids/order/counts are correct for the declared identity scheme, `number_in_hafs` is valid where required, language direction is declared, and source/license records resolve.
- All generated documentation links resolve inside the assembled tree.

### Reader behavior

- Existing deep links, including chapter/verse and all current query parameters, open the same selection. Existing local-storage preferences remain readable.
- Initial app load does not request any full-corpus `quran.json` or reciter catalog. Opening a chapter requests only the selected chapter layers; changing only a translation reuses cached Arabic.
- Rapid chapter changes cannot render a stale response. Network and validation failures produce a named, retryable state without a blank page.
- Warsh/Qalun mapping, Indo-Pak Al-Fatiha behavior, translation joins, audio-host indexing, font eligibility, autoplay/repeat, and chapter continuation retain fixture-backed tests.

### Performance

- The docs pages ship no hydrated Vue/React runtime. Any small Astro client script is justified and measured.
- The current unbundled reader baseline is approximately **14.7 KB gzip JavaScript** and **2.3 KB gzip app CSS** by summing local gzip output for the served source files. Record production-built gzip and Brotli sizes. Because the selected implementation retains those reader modules, their behavior and payload should remain unchanged. Report Astro/Tailwind shell CSS separately; use a provisional 25% CSS regression ceiling unless a measured user benefit and explicit exception justify more. Fonts and fetched chapter JSON are reported separately.
- On representative mobile throttling, the landing page and reader shell meet LCP at or below 2.5 s and CLS at or below 0.1; interaction tests keep the main thread responsive. Once real-user data exists, target the official Core Web Vitals thresholds at the 75th percentile: LCP <= 2.5 s, INP <= 200 ms, CLS <= 0.1 ([web.dev](https://web.dev/articles/vitals)).
- Fonts use `font-display` deliberately, no external runtime/font request is introduced, and the existing build-time codepoint coverage gate remains mandatory.

### Accessibility and resilience

- Meet WCAG 2.2 AA for the docs and reader. All functionality, including edition selectors, chapter navigation, popovers, and audio controls, works by keyboard with no trap; focus is visible and is not hidden by sticky UI. These requirements map directly to WCAG's [keyboard criteria](https://www.w3.org/TR/WCAG22/#keyboard-accessible) and [focus-not-obscured criterion](https://www.w3.org/TR/WCAG22/#focus-not-obscured-minimum).
- Each page has one clear `h1`, landmarks, a skip link, descriptive titles, labelled controls, programmatic loading/error status, and sensible focus placement after client-side navigation.
- Arabic spans use `lang="ar" dir="rtl"`; translation containers use catalog direction; mixed verse numbers and controls remain readable in RTL and LTR editions. Text can zoom to 200% and the reader works at 320 CSS px without horizontal page scrolling.
- `prefers-reduced-motion` disables nonessential smooth scrolling/animation. Color contrast meets AA in light and dark themes. Automated accessibility checks report no serious/critical violations, and manual keyboard plus screen-reader smoke tests cover the reader's main flow.
- Documentation content and endpoint examples remain available without JavaScript. The reader shows a useful shell and explanation while its existing modules load or if they fail.

## Decision summary

The evidence-only recommendation is the current Python-generated static site with focused HTML/CSS/JavaScript improvements and stronger browser/data validation. The selected implementation uses Astro static documentation and shell components plus Tailwind 4 as an explicit maintainability and product-design choice, while preserving that same Python data authority and the existing JavaScript reader. Static Cloudflare hosting, public dataset paths, the npm legacy tree, font verification, and chapter-level fetching remain. TypeScript, Vue, and React reader migrations are outside this implementation.
