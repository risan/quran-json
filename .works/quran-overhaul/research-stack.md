# Frontend stack research (2026-10-01)

Versions checked with `npm view` on 2026-10-01. Repo facts: `site/package.json` already pins astro 7.3.3, tailwindcss and @tailwindcss/vite 4.3.3, typescript ^6.0.3. Node 24.21.0 is installed. `wrangler.jsonc` serves `./cdn` as static assets.

## 1. Versions

| Package | Latest | Node / notes |
|---|---|---|
| astro | 7.3.5 | >=22.12.0. Depends on vite ^8.0.13 (Vite 8.3.1 latest) |
| @astrojs/react | 7.0.0 | >=22.12.0. Peers react/react-dom 17-19. Uses @vitejs/plugin-react ^6.1.1 |
| @astrojs/check | 0.9.10 | |
| @astrojs/cloudflare | 14.3.3 | Peers astro ^7.2.0, wrangler ^4.125.0. NOT needed for pure static output |
| react / react-dom | 19.3.0 | |
| tailwindcss, @tailwindcss/vite | 4.3.3 | |
| vite | 8.3.1 | ^20.19 or >=22.12. Do not install separately; Astro brings it. Pin via `overrides` only if needed |
| oxlint | 1.86.0 | ^20.19 or >=22.12. Released weekly |
| oxfmt | 0.71.0 | 0.x, weekly releases. Docs call it production-ready (100% Prettier JS/TS conformance). No explicit "stable" label |
| typescript | 7.0.2 (site pins ^6.0.3) | TS 7 is the Go-native compiler. `@astrojs/check` 0.9.10 may not support it; keep ^6.0.3 until verified |
| shadcn (CLI) | 4.21.0 | >=20.18.1 |
| tw-animate-css | 1.4.0 | shadcn's Tailwind v4 replacement for tailwindcss-animate |
| lucide-react | 1.49.0 | |
| @base-ui/react | 1.8.0 | |
| radix-ui | 1.6.7 | |
| cmdk | 1.1.1 | last push 2025-10-29 (13k stars). Stable but quiet |
| @tanstack/react-virtual | 3.14.13 | 7.1k stars, active |
| wrangler | 4.145.0 | |
| prettier / prettier-plugin-astro | 3.9.9 / 1.1.0 | |

Astro repo: 63k stars, pushed today. shadcn-ui/ui: 125k stars, pushed today. oxc: 23k stars, pushed today.

## 2. Oxlint and Oxfmt

Oxlint:
- `npm i -D oxlint`, run `oxlint`. Config: `.oxlintrc.json` (also `oxlint.config.ts` in newer versions). Plugins: `"plugins": ["typescript","react","jsx-a11y","import"]`. Init: `npx oxlint --init`.
- `.astro`: Oxlint parses only the frontmatter script of Astro files (partial support). Open bug: it reports unused imports and vars wrongly in `.astro` (oxc issue 18878). Lint `.ts`, `.tsx`, `.mjs` and treat `.astro` as best-effort. `astro check` covers `.astro` types.

Oxfmt:
- `npm i -D oxfmt`. Run `oxfmt` to write, `oxfmt --check` in CI.
- Config search order: `.oxfmtrc.json`, `.oxfmtrc.jsonc`, `oxfmt.config.ts`, `oxfmt.config.mts`. `-c` accepts more extensions.
- Defaults: printWidth 100 (not 80), semi true, double quotes, trailingComma "all", tabWidth 2, insertFinalNewline true.
- Options: `ignorePatterns`, `overrides` (globs), `sortTailwindcss` (off by default).
- Migrate from Prettier: `npx oxfmt --migrate=prettier` (documented in the Oxfmt migration guide; I did not run it).
- Languages: JS, JSX, TS, TSX, JSON(C/5), YAML, TOML, HTML, Vue, Svelte, CSS, SCSS, Less, Markdown, MDX, GraphQL. **No `.astro` support in 0.71.0**: the CLI skips `.astro`. Plan is to bundle prettier-plugin-astro (oxc issue 19715, targeted Q2 2026, still open). `withastro/oxc` PR 5 adds Astro formatting but is not released.
- Recommendation for `.astro`: keep a small `prettier` + `prettier-plugin-astro` run only for `**/*.astro` (`prettier --write "site/src/**/*.astro"`), and use Oxfmt for everything else. Or skip `.astro` formatting and keep the files small; do not block the redesign on it. Remove Prettier once Oxfmt ships Astro support.
- Contributors format with one script, for example: `"fmt": "oxfmt && prettier --write \"site/src/**/*.astro\""`.

Suggested `.oxfmtrc.json`:
```json
{
  "printWidth": 100,
  "ignorePatterns": [".build/**", "cdn/**", "**/*.astro", "site/src/components/ui/**"]
}
```
(Ignoring generated shadcn files avoids churn when re-running `shadcn add`. Optional.)

## 3. shadcn/ui on Astro

Source: https://ui.shadcn.com/docs/installation/astro
- New project: `npx shadcn@latest init -t astro` (preset: `--preset <code> --template astro`).
- Existing project (our case):
  1. Install React integration: `npx astro add react` (adds `@astrojs/react`, react, react-dom, types, and `integrations: [react()]`).
  2. Tailwind v4 is already set via `@tailwindcss/vite` in `astro.config.mjs` (`vite.plugins`). Keep it.
  3. Path alias in `site/tsconfig.json`: `"compilerOptions": { "baseUrl": ".", "paths": { "@/*": ["./src/*"] } }`.
  4. From `site/`: `npx shadcn@latest init`. It writes `components.json`, `src/lib/utils.ts` (`cn()` using clsx and tailwind-merge), adds `tw-animate-css`, and rewrites the CSS file with `@import "tailwindcss"; @import "tw-animate-css"; @custom-variant dark (...); @theme inline {...}` plus `:root` and `.dark` OKLCH tokens.
  5. Add parts: `npx shadcn@latest add button sheet command dialog tabs scroll-area input select slider switch toggle-group sonner`.
- `components.json` fields (https://ui.shadcn.com/docs/components-json): `style` (format `{library}-{style}`, e.g. `base-vega` or `radix-vega`/`new-york`), `tailwind.css` (path to global CSS), `tailwind.config` blank for v4, `tailwind.baseColor` (neutral, stone, zinc, mauve, olive, mist, taupe), `tailwind.cssVariables` true (cannot change later), `rsc` false for Astro, `tsx` true, `iconLibrary` lucide, `aliases` (`components`, `ui`, `lib`, `hooks`, `utils`).
- **Base UI vs Radix**: since 2026-07-03 Base UI is the default for new projects (https://ui.shadcn.com/docs/changelog/2026-07-base-ui-default). Radix is not deprecated: `shadcn init -b radix`. Both receive updates. Pick Base UI (new default, smaller surface, maintained by MUI/Radix/Floating UI authors) unless a needed component is missing. Radix has the larger install base and more third-party blocks. Either works; choose once at init (switching later means re-adding components).
- Rendering: shadcn parts are React. In `.astro` they render to static HTML on the server, but interactive parts (Sheet, Dialog, Command, Select, Tabs) need a client directive: `<ReaderApp client:load />` or `client:only="react"`. Static-only parts (Card, Badge, Button as a link, Separator, Table) cost no JS inside `.astro` with no directive. Components with Portals (Sheet, Dialog) must live inside one island; do not scatter them across multiple islands.
- Do not mix: a shadcn component imported into a `.astro` file with no directive ships zero JS, which is fine for docs.

## 4. Alternatives for Astro-native components

| Option | Signals | Notes |
|---|---|---|
| starwind-ui (`starwind` 3.3.2) | 738 stars, pushed 2026-09-28 | Astro-native, no React, Tailwind v4, copy-in CLI (`npx starwind@latest init`). Small, young |
| fulldev/ui (`fulldev-ui` 0.14.2) | 608 stars, pushed 2026-09-30 | Astro-native blocks and sections. Pre-1.0 |
| shadcn/ui | 125k stars, daily commits | Official Astro guide, largest ecosystem, React |

Neither Astro-native library has the maturity or accessibility depth of shadcn for an interactive reader (sheet, command palette, slider). Not recommended as the base.

**Recommendation**: Astro 7 static site, Tailwind 4 tokens defined once in one CSS file, shadcn/ui (Base UI) for the interactive reader as one React island at `/app/` (`client:only="react"`, since the reader reads URL hash and localStorage). Docs pages stay `.astro` using the same Tailwind tokens (`bg-background`, `text-muted-foreground`, `rounded-lg`, same font vars), and may use zero-JS shadcn pieces (Card, Badge, Button, Table) for visual parity. One `global.css` imported by both layouts gives one design language. Port the 2,800 lines of `web/app/*` into React hooks and components rather than wrapping the vanilla code.

## 5. Command palette and virtualization

- shadcn `Command` wraps `cmdk` 1.1.1 (`npx shadcn@latest add command`), usually shown inside `CommandDialog` with Ctrl/Cmd+K. Works with React 19. Quiet repo (last push Oct 2025) but widely used and stable. cmdk filters in memory; for 114 surahs this is instant. For verse search across 6,236 verses, build a prebuilt index and filter with `shouldFilter={false}` plus own matching (for example MiniSearch or Fuse.js) in a worker. Unverified: bundle sizes.
- Virtualization: not needed for one surah. Longest, Al-Baqarah, has 286 verses; rendering 286 simple rows is fine. If each verse shows Arabic, translation and transliteration (about 3 text blocks), the DOM is about 1,000 nodes, still fine with `content-visibility: auto` on rows. Use `@tanstack/react-virtual` only for a whole-Quran continuous view (6,236 verses) or a verse-search results list. Cost: variable row heights need `measureElement`, and in-page find (Ctrl+F) and scroll-to-verse need care. Recommendation: skip it for v1.

## 6. Fonts (Astro Fonts API)

Source: https://docs.astro.build/en/guides/fonts/ and https://docs.astro.build/en/reference/font-provider-reference/. The Fonts API is stable (added in Astro 6.0.0), self-hosts and preloads, and generates fallback metrics. Config goes in `astro.config.mjs`; the `<Font />` component goes in `<head>`.

```js
import { defineConfig, fontProviders } from "astro/config";

export default defineConfig({
  fonts: [
    {
      provider: fontProviders.fontsource(),
      name: "Inter",            // or "Geist"
      cssVariable: "--font-sans",
      weights: ["100 900"],
      subsets: ["latin"],
    },
    {
      provider: fontProviders.fontsource(),
      name: "Amiri",
      cssVariable: "--font-amiri",
      weights: [400, 700],
      subsets: ["arabic"],
      fallbacks: ["serif"],
    },
    {
      provider: fontProviders.fontsource(),
      name: "Scheherazade New",
      cssVariable: "--font-scheherazade",
      weights: [400, 700],
      subsets: ["arabic"],
    },
    {
      provider: fontProviders.fontsource(),
      name: "Noto Naskh Arabic",
      cssVariable: "--font-noto-naskh",
      weights: ["400 700"],
      subsets: ["arabic"],
    },
  ],
});
```
```astro
---
import { Font } from "astro:assets";
---
<head>
  <Font cssVariable="--font-sans" preload />
  <Font cssVariable="--font-amiri" />
</head>
```
Tailwind v4 hookup in `global.css`: `@theme inline { --font-sans: var(--font-sans); --font-arabic: var(--font-amiri); }`. Caution: a variable cannot refer to itself in `@theme inline`; use distinct names (for example `--font-astro-sans` for Astro, `--font-sans` in theme).
- Only preload the default Arabic font. Others load on demand when the user selects them (the CSS `@font-face` is emitted but files are fetched only when used).
- Fontsource packages exist (version 5.3.0): `@fontsource/amiri`, `@fontsource/scheherazade-new`, `@fontsource/noto-naskh-arabic`, `@fontsource-variable/noto-naskh-arabic`, `@fontsource-variable/inter`, `@fontsource-variable/geist`. Fallback if the Fonts API misbehaves: install these as npm packages and use the `local`/`npm` provider or plain `import "@fontsource-variable/inter"`.
- Unverified: the exact subset name list Fontsource exposes for Amiri (`arabic` and `latin` expected), and whether Arabic Quranic marks (tashkeel, small high marks) render fully in each font. Test with a verse containing waqf marks (for example 2:282). Scheherazade New and Amiri are the best-known for full Quranic diacritics; Noto Naskh Arabic is weaker on Quranic marks. UI font suggestion: Geist or Inter variable.

## 7. Astro 7 changes relevant to a static site

Source: https://docs.astro.build/en/guides/upgrade-to/v7/. We are already on 7.3.x.
- Vite 8 (Rolldown/Oxc based) is the bundler. Plugins written for Vite 7 may need updates. `@tailwindcss/vite` 4.3.3 works (the site builds today).
- New Rust compiler is the default and stricter: unclosed tags and invalid nesting are errors, no auto-fix. Close every non-void element.
- `compressHTML` default changed from `true` to `'jsx'`: whitespace between inline elements is stripped by JSX rules. Check spacing between `<span>` and `<em>`; use `{" "}` where needed.
- Markdown pipeline is Satteri, not remark/rehype. Install `@astrojs/markdown-remark` to keep unified plugins.
- `src/fetch.ts` is reserved for routing; do not use that filename.
- `@astrojs/db` removed. Unrelated.
- `output: "static"` and `build.format: "directory"` stay valid (current config uses both). Static output needs no adapter; `@astrojs/cloudflare` is only for SSR. Keep `wrangler.jsonc` `assets.directory` pointed at the built output. Note `astro.config.mjs` writes to `.build/site/`, while `wrangler.jsonc` serves `./cdn`; the build script must merge the site into `cdn` (existing behavior, not verified here).
- Assets and fonts: images go through `astro:assets`; fonts through the Fonts API; the `_astro/` hashed folder is emitted. Workers static assets reads `_headers` for cache rules, so give `_astro/*` immutable caching.
- Node >=22.12 required (installed: 24.21.0).

## 8. Suggested install set for `site/`

```bash
cd site
npx astro add react
npm i react-dom@19 class-variance-authority clsx tailwind-merge lucide-react tw-animate-css
npm i -D oxlint oxfmt prettier prettier-plugin-astro
npx shadcn@latest init            # accept Base UI default; or: init -b radix
npx shadcn@latest add button sheet command dialog tabs scroll-area slider switch toggle-group select input
```
Keep typescript at ^6.0.3 and `@astrojs/check` ^0.9.10 until TS 7 support is confirmed.

## Sources
- https://ui.shadcn.com/docs/installation/astro
- https://ui.shadcn.com/docs/components-json
- https://ui.shadcn.com/docs/changelog/2026-07-base-ui-default
- https://docs.astro.build/en/guides/upgrade-to/v7/
- https://docs.astro.build/en/guides/fonts/
- https://docs.astro.build/en/reference/font-provider-reference/
- https://oxc.rs/docs/guide/usage/formatter.html
- https://oxc.rs/docs/guide/usage/formatter/config.html
- https://github.com/oxc-project/oxc/issues/19715 (Astro in oxfmt)
- https://github.com/oxc-project/oxc/issues/18878 (oxlint Astro unused vars)
- https://github.com/withastro/oxc/pull/5
- npm registry (`npm view`) and GitHub API for star and push dates, 2026-10-01
