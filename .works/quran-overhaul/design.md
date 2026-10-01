# Site design brief (Track B)

One product, two views: **Docs** (`/`) and **Reader** (`/app/`). Same header, same tokens,
same type scale, same components. A visitor must not feel they changed sites.

## What to avoid (the "AI slop" look the owner dislikes)

- Big hero with a giant headline, eyebrow labels ("QURAN TEXT + STATIC JSON"), taglines.
- Gradients, glows, glassmorphism, coloured shadows, emoji, decorative Arabic art.
- Cards inside cards, `rounded-2xl`+ everywhere, pill badges on everything.
- Large vertical padding between sections (no `py-24`), wide empty gutters.
- Marketing copy ("clearly published", "Paths that stay legible"). Write plain labels.
- Different accent colours on the two pages.

## Tokens

- shadcn tokens in `site/src/styles/global.css` (`:root` / `.dark`), base colour **neutral**
  or **zinc**. One accent: a muted green, e.g. `oklch(0.52 0.09 160)` light /
  `oklch(0.72 0.1 160)` dark, used for links, active nav item, the playing verse marker,
  focus ring. Nothing else is coloured.
- Radius `0.375rem`. Borders 1px `border`. No shadows except popovers/sheets.
- UI font: Inter variable (or Geist). Mono: system mono stack (`ui-monospace, …`).
- Arabic fonts self-hosted from `/fonts/`: Amiri, Scheherazade New, Noto Naskh Arabic; the
  per-script default and the allowed fonts come from the measured `fonts.json`.
- Type scale (UI): 13px meta, 14px body/UI, 16px reading translation, 20px page title, 15px
  section headings (semibold). Arabic reading size default 28px, adjustable 20–44px.
- Spacing: section gap `space-y-8` max in docs; table rows `py-1.5`; buttons `h-8`.

## Shared header (both views)

`h-12`, sticky, bottom border. Left: wordmark `quran-json` (text, mono or semibold) → `/`.
Then nav: `Docs`, `Reader`. Right: GitHub link icon, theme toggle (light/dark/system).
In the reader the header also shows the current surah selector button on mobile.

## Docs (`/`)

- Desktop: left sidebar (w-52, sticky, section links with active state from scroll), main
  column max ~860px. Mobile: sidebar becomes a Sheet opened from a header button.
- Opening: one line title "Quran JSON" + one sentence + a row of 4 stats (scripts,
  translations, languages, transliterations) in small text + two buttons (Open reader,
  GitHub). No hero.
- Sections: Quick start (tabs: curl / JavaScript / Python; copy button), Endpoints (table),
  Scripts (the "Which script should I use?" list, then a compact table: id, name, reading,
  verses, link), Translations (search input + language filter + table: language, name,
  translator, link; server-rendered full list, client search enhances), Transliteration,
  Audio (hosts table + note on per-ayah), Sources & licences (short table + "sources we
  checked and do not use"), Changes policy.
- Code blocks: Shiki (Astro built-in), theme pair github-light/github-dark, small (13px).

## Reader (`/app/`)

- Desktop ≥1024px: left panel (w-64) surah list with filter input, scrollable; centre reading
  column (max ~760px). Mobile: surah list in a Sheet; Ctrl/Cmd+K command palette everywhere.
- Toolbar under the header (sticky, h-10): surah name (Arabic + transliterated), verse count,
  quick selects for Script and Translation, Settings button (Sheet: font, Arabic size,
  translations multi-select, transliteration select, reciter select, show/hide toggles).
- Verse row: left gutter with verse key `2:255` and a small play button + a menu (copy text,
  copy link, play from here). Arabic right-aligned `dir="rtl" lang="ar"`, then transliteration
  (muted, italic off), then each translation with a tiny edition label. Rows separated by a
  border, `py-3`. The playing verse gets an accent left border and auto-scrolls into view.
- Bismillah line above chapters (not for 9, nor where the script embeds it in verse 1 — follow
  the data's own rules from `reader-core.js`).
- Audio bar: sticky bottom, h-12: reciter name, prev/play/next, continuous toggle, repeat
  verse toggle, speed? (no), close. Only when audio is active.
- Empty/error states: loading skeleton rows; a failed fetch shows a one-line message with Retry.
- URL: `/app/#/2` (surah), `/app/#/2:255` (verse), old `/app/#/1?s=...` still parsed.
- Accessibility: keyboard reachable everything, visible focus, `aria-current` on active surah,
  audio buttons labelled, prefers-reduced-motion disables smooth scrolling.

## Quality bar

- Lighthouse-style basics: no layout shift on load, fonts `font-display: swap`, JS only on the
  reader page (docs works fully without JS except search/copy/theme).
- No horizontal scroll at 360px. Tables scroll inside their own container on mobile.
- Light and dark both checked.
