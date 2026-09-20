# Live site and reader audit

Date: 2026-09-20
Scope: `https://quran-json.risanb.com/`, `https://quran-json.risanb.com/app/`, and the
checked-out `web/` implementation.  This is an audit only; no product files were changed.

## Confidence and method

The two live URLs and representative JSON, CSS, JavaScript, and font paths were fetched with
`curl` on 2026-09-20. Both pages returned HTTP 200 from Cloudflare. The deployed bytes match
the generated checkout artifact for the key page and app files:

| Live path | Local generated file | SHA-256 prefix |
| --- | --- | --- |
| `/` | `cdn/index.html` | `8e6b79c136e5…` |
| `/app/` | `cdn/app/index.html` | `48c94e7e5f56…` |
| `/assets/base.css` | `cdn/assets/base.css` | `83e66108c198…` |
| `/assets/docs.css` | `cdn/assets/docs.css` | `d1d8591f9b7b…` |
| `/app/app.js` | `cdn/app/app.js` | `d71922f62cc4…` |
| `/app/ui.js` | `cdn/app/ui.js` | `45c9c18eacd4…` |
| `/app/app.css` | `cdn/app/app.css` | `8b43a592a372…` |

The root HTML is the generated version of `web/index.html`; its placeholders are substituted at
build time. The deployed page currently reports 10 scripts, 84 translations in 57 languages,
one transliteration, 114 chapters, 6,236 verses, and 595 recitations. This means the source
and deployed behavior are sufficiently aligned for this audit. The checkout has no applicable
`AGENTS.md` (the only matches are under an unrelated `oauth1/vendor` tree).

There is no browser binary, Playwright package, or Puppeteer package available in this
environment. I therefore did not claim pixel-level visual results, computed layout boxes, or
manually observed focus order. CSS and JavaScript findings below are source-backed inferences;
HTTP status, response size, headers, content, and deployed hash comparisons are direct live
observations.

## What is live today

The docs page is server-rendered static HTML. It includes the full endpoint reference, ten-script
table, font coverage table, 84-row translation catalogue, licensing/withheld material, audio
host table, compatibility contract, and attribution in one document. The uncompressed response
was 51,600 bytes; Cloudflare served it with `content-encoding: zstd`, transferring about 11.3 KB
in the sampled request. The app entry response is only 1,900 bytes and contains a loading message,
the shell, and a `noscript` explanation. It does not contain the chapter list or verse content.

The reader waits for five metadata requests before it renders the chapter grid:

```text
/manifest.json              4,613 bytes
/chapters.json             14,161 bytes
/translations/index.json   65,235 bytes
/transliteration/index.json 1,066 bytes
/app/fonts.json             3,420 bytes
```

Those requests are started in parallel by `Promise.all` at `web/app/app.js:585-592`. The
reciter index is correctly deferred until audio is requested (`web/app/app.js:46-50` and
`:388-393`); it is about 140 KB uncompressed. The app's first-party source bodies are about
48.4 KB JavaScript across its five modules and 17.8 KB CSS across its two stylesheets. Opening
Surah 2 then requests only chapter files: the sampled Uthmani chapter was 110,717 bytes and
the selected English translation chapter was 93,006 bytes. No whole-corpus file is needed for
the interactive reader.

Static data and font responses have useful caching behavior, with one catalogue caveat. Text,
translation, and transliteration paths—including their `index.json` discovery files—return
`Cache-Control: public, max-age=31536000, immutable` through the wildcard rules; `/manifest.json`,
`/chapters.json`, and `/app/fonts.json` currently revalidate with `max-age=0, must-revalidate`;
and `/audio/reciters.json` is cached for one hour. The headers provide
`Access-Control-Allow-Origin: *` and `X-Content-Type-Options: nosniff` (`cdn/_headers:1-21`).
The immutable edition indexes mean a catalogue update at the same URL can remain stranded in
browser/CDN caches for a year, so any modernization that adds editions must preserve paths or
introduce a separately revalidated discovery document. The three bundled WOFF2 fonts are served
from the project origin and total about 342,640 bytes locally. This is a good baseline to
preserve in a redesign.

## Findings, ordered by user impact

### 1. The first useful reader view is gated on all catalogue metadata

**Observed:** `/app/` returns only a loading shell. The controller does not call `render()` until
manifest, chapter metadata, translations, transliteration metadata, and font coverage all resolve
(`web/app/index.html:26-31`, `web/app/app.js:585-635`). A slow or failed translation catalogue
therefore delays or prevents even the chapter directory, although the directory only needs
chapter metadata and the chosen script/font.

**Opportunity:** render the chapter directory as soon as the manifest, chapters, and font
coverage are usable; load the edition catalogues in parallel for the settings UI and default
language, or render a small catalogue loading state. On a chapter route, keep the current
chapter-level parallel fetch and promise cache. Show Arabic when an optional translation fails,
with a named retry for that edition, instead of treating every metadata layer as an all-or-
nothing startup dependency.

This is a practical speed and resilience improvement. It does not require downloading a full
Quran file or introducing a service worker.

### 2. Multiple translations have no per-verse identity

**Observed:** the selector allows up to three translations (`web/app/app.js:497-507`), and the
chapter header lists selected author names together (`web/app/ui.js:312-316`). Each verse then
renders only consecutive `<p class="translation">` blocks with direction and language
attributes; it emits no edition name, short label, or association to the selected catalogue
entry (`web/app/ui.js:259-267`). A reader who sees three paragraphs cannot reliably tell which
translator wrote each one.

**Opportunity:** render a visible, compact label for each translation block, derived from the
catalogue, and retain `lang`/`dir`. On wide screens, a labelled comparison layout can use
columns only when there is room; on narrow screens, stack the same labelled blocks. Keep one
translation as the calm default and make comparison mode an explicit choice.

### 3. Settings popovers are not a complete keyboard or screen-reader interaction

**Observed:** the app has a fixed `role="dialog"` with the generic accessible name “Choices”
(`web/app/index.html:34`). `openPopover()` injects content and focuses the search field, but there
is no close button, `aria-modal`, labelled relationship, focus return, or focus containment
(`web/app/app.js:326-335`). The translation trigger hard-codes `aria-expanded="false"` and the
reciter trigger has no expanded state (`web/app/ui.js:161-189`). Escape closes the popover, but
does not restore focus or announce what changed (`web/app/app.js:550-554`).

**Opportunity:** treat each picker as an actual disclosure/dialog: give it a specific name,
toggle `aria-expanded`, provide a close button, return focus to the trigger, close on Escape and
outside click, and ensure the fixed panel remains usable at 320 CSS px. A native `<dialog>` or a
small tested disclosure primitive is suitable; the important requirement is the interaction
contract, not the framework.

### 4. Mobile navigation and the reader toolbar lose discoverability

**Observed:** the docs top navigation is hidden entirely at widths up to 720 px
(`web/assets/base.css:410-417`). There is no replacement menu, table of contents, or “back to
sections” control. The app toolbar remains a single horizontally scrolling row with its
scrollbar hidden (`web/app/app.css:46-64`); it contains Script, Font, Translations,
Transliteration, Recitation, and Arabic size controls (`web/app/ui.js:135-198`). This is a
source-based layout inference because no browser was available, but the CSS guarantees that
the controls are wider than many phone viewports and that their overflow affordance is hidden.

**Opportunity:** give the docs a compact menu or sticky contents control on small screens. In the
reader, group common controls into a concise top bar and put less frequent choices in a labelled
settings sheet. Keep chapter navigation, search, and reading controls reachable without a
horizontal gesture. Test at 320, 375, and 412 CSS px with long Arabic names and RTL editions.

### 5. The docs are trustworthy but make the first task hard to find

**Observed:** the top of the page presents prose, seven statistics, and three links, then flows
through quickstart, endpoints, script semantics, font coverage, riwayah alignment, the full
translation catalogue, transliteration, audio, compatibility, and licensing
(`web/index.html:37-72`, `:145-172`, `:174-265`, `:267-378`). The visible “Compatibility contract”
section is absent from the nav (`web/index.html:20-28` vs `:351-361`). The page is static and
browser-findable, but an API consumer must scan a long document to reach the endpoint details.

**Opportunity:** keep the generated facts and deep explanations, but establish a task-first
information architecture:

1. A short landing section with “read”, “fetch one chapter”, and “browse the data” paths.
2. A compact endpoint and data-shape reference with copyable examples.
3. Separate or collapsible advanced material for riwayah alignment, fonts, licensing, and
   compatibility.
4. A generated catalogue view or section that remains searchable and links directly to JSON.

The current single-page URL and anchors should keep working during any split. Do not maintain
catalogue rows by hand: they are generated from the same structures as the JSON
(`src/quranjson/web.py:245-379`).

### 6. One quickstart example contradicts its own joining rule

**Observed:** the note says “Join on `id`, not on position” (`web/index.html:118-123`), but the
JavaScript sample indexes `translated.verses[i]` and the Python sample uses `zip` by array order
(`web/index.html:100-116`). The reader implementation correctly resolves mapped riwayah verses
through `number_in_hafs` (`web/app/app.js:122-165`).

**Opportunity:** make the example build a map keyed by `id` for Hafs-keyed files and show a
separate, explicit alignment example for Warsh/Qalun. Documentation should never teach a safe
rule and then demonstrate a different operation, even if today’s arrays happen to be ordered.

### 7. The app has two alignment edge cases that need explicit tests and UI treatment

**Observed:** the reader suppresses translations for the divergent Indo-Pak Al-Fatiha chapter,
which is the correct safety behavior (`web/app/app.js:263-301`). However, transliteration is
still fetched and merged by array index before that divergence check is applied
(`web/app/app.js:140-145`, `:270-277`). If a transliteration is enabled while reading that
chapter, its Hafs-keyed rows can be paired with the Indo-Pak rows by position. The current UI
also uses the generic “translation not alignable in this script” label in the chapter header
(`web/app/ui.js:312-316`), while the warning explains the specific issue later.

**Opportunity:** either suppress transliteration for a chapter whose verse identity diverges or
join it through an explicit mapping. Make the warning appear before the reader controls and
state exactly which layers are unavailable. Add fixture-backed tests for Indo-Pak 1, Warsh/Qalun
split/merge cases, and every selected optional layer.

### 8. Deep links are valuable but malformed URL state can strand the reader

**Observed:** the hash URL intentionally carries chapter, verse, script, translation,
transliteration, reciter, and font state (`web/app/app.js:1-8`, `:54-82`). That is an excellent
shareability baseline. `parseRoute()` accepts any `s` value, while `toolbar()` immediately reads
`coverage.scripts[state.script]` (`web/app/app.js:54-67`, `web/app/ui.js:119-129`). A link such as
`/app/#/?s=unknown` can therefore leave the app in its startup/error state instead of falling
back to a published script. Similar validation is not visible for every URL enum.

**Opportunity:** validate every route parameter against the published manifest/catalogue before
rendering, preserve a useful fallback, and surface a small “link had an unsupported option”
message. Keep the existing hash shape and local-storage keys for compatibility.

### 9. Arabic typography and bidi handling are a product requirement

**Observed:** the project bundles Amiri, Scheherazade New, and Noto Naskh Arabic, measures
codepoint coverage at build time, and selects a usable font per script (`web/assets/base.css:16-35`,
`web/app/ui.js:23-34`; build gate `src/quranjson/web.py:132-195`). Verse Arabic and chapter names
carry `lang="ar" dir="rtl"`; translation paragraphs carry catalogue `lang` and `dir`
(`web/app/ui.js:259-267`, `:290`, `:319-326`). The reader uses a user-adjustable Arabic size
and defaults to a generous line-height (`web/assets/base.css:45-64`, `web/app/app.css:319-325`).

**Opportunity:** retain these as explicit contracts in any visual refresh. Test mixed Arabic,
Latin, verse numbers, footnotes, and RTL translations together. Keep the measured font
eligibility gate and avoid treating “has a glyph” as proof of correct mark shaping. A visual
direction can become more distinctive through a restrained mushaf/editorial typographic system,
but it should not replace the current font selection or bidi metadata.

### 10. A few small accessibility details are missing from the static docs

The docs have no skip link, no explicit focus-visible treatment for the shared buttons, and no
mobile navigation fallback (`web/index.html:16-33`, `web/assets/base.css:208-263`, `:410-417`).
The code tabs set `aria-selected` and roving `tabIndex`, but have no `aria-controls` or panel IDs;
arrow keys move focus without selecting the next tab, and Home/End are not handled
(`web/assets/site.js:35-64`). These are straightforward improvements with high value for
keyboard and screen-reader users.

## Constraints a redesign must preserve

- Existing JSON paths, response shapes, CORS, and the frozen npm `dist/` contract. The web layer
  must not become a second source of truth for catalogue rows or counts.
- The static Worker deployment and same-origin fonts. No runtime font or analytics dependency is
  needed for the reading experience.
- Chapter-first data loading and lazy reciter loading. Do not make the reader fetch a whole
  `quran.json` simply to render a chapter.
- The hash route and local-storage preferences, including direct chapter/verse links and selected
  script/translation/font/reciter state. A friendlier route can be added only as a compatibility
  layer.
- Arabic coverage, `lang`/`dir`, reading/orthography distinctions, Warsh/Qalun mapped verse
  identity, and Indo-Pak’s chapter-one divergence. These are reader correctness rules.
- JavaScript-disabled docs. The current page renders its catalogue and examples in HTML and only
  enhances them with tabs, copy buttons, theme, and filtering (`web/assets/site.js:1-121`). A new
  docs shell should preserve useful endpoint content without requiring hydration.

## Recommended experience direction

Use the current public dataset as the product’s stable foundation and make the website feel like
a calm reading instrument rather than a generic dashboard. The visual language should have a
warm ink/paper or similarly restrained palette, a distinctive Arabic display face paired with a
quiet text face, a narrow prose measure, and clear typographic hierarchy. Avoid gradients,
decorative “bento” panels, excess pills, and card grids that make the Quran compete with the
controls. Keep borders and surfaces quiet; reserve accent color for active reading state,
links, and actions.

The reader should have one obvious first task: choose a chapter and read. Make the chapter
directory searchable and scannable, then give the verse view a stable reading column with Arabic,
optional transliteration, and clearly labelled translation blocks. Put script/font/language/audio
choices into a settings surface that works equally well with pointer, touch, and keyboard. Keep
audio controls visible once playing, but let the reader close or minimize the player without
losing the selected reciter.

The docs should answer “how do I fetch one chapter?” within the first screenful, then let a
consumer choose endpoint reference, catalogue, alignment semantics, or licensing detail. Preserve
the generated tables for authority, but move them out of the main reading path or make them
collapsible. A direct link to the reader should remain the primary product action.

## Validation needed before implementation is accepted

The implementation should add browser-level checks around the existing repository tests. At
minimum, exercise these at 320/375/768/1440 CSS px in light and dark themes:

- Keyboard-only docs navigation, skip link, tab activation, copy feedback, filter input, and
  focus visibility with sticky headers.
- Keyboard-only reader flow: chapter search, chapter navigation, each picker, Escape/outside
  close, focus return, audio controls, copy/link actions, and no trapped focus.
- 200% zoom and 320 px width with no page-level horizontal scrolling; horizontal overflow should
  be limited to intentionally scrollable data tables or code blocks.
- Arabic rendering for all published scripts, including measured font fallback; mixed RTL/LTR
  translation blocks; long translator names; footnotes; and verse numbers.
- Deep links with valid chapter/verse and every query option, malformed options, stale catalogue
  values, Indo-Pak chapter 1, and Warsh/Qalun mapped verses.
- Startup and chapter waterfalls on a throttled mobile profile. Record first usable chapter-grid
  time, first usable verse time, transferred first-party JS/CSS/font bytes, and failed optional
  layer behavior. The redesign should beat or clearly justify any regression against the live
  baseline above.
- `prefers-reduced-motion`, offline/failed metadata, failed optional translation, and a reader
  error with a retry path. No external request should be required for docs or Arabic fonts.

The current Python tests cover generated links, placeholders, module existence, and font coverage
(`tests/test_web.py:59-121`), but do not exercise viewport layout, keyboard behavior, screen-reader
semantics, or the reader’s asynchronous UI. Those checks are the main evidence gap for a frontend
modernization.

## Suggested sequence

1. Fix content and semantics first: translation labels, the contradictory join example, docs
   compatibility link, picker ARIA/focus behavior, route validation, and the Indo-Pak
   transliteration alignment rule.
2. Establish browser baselines at the viewports above, including the current live waterfall and
   accessibility checks. Keep a vanilla-reader comparison path while changing the docs shell or
   styling.
3. Simplify the docs information architecture and visual system while retaining generated data,
   no-JavaScript endpoint content, and all old anchors.
4. Rework the reader layout around the chapter/read/settings hierarchy, then measure whether a
   framework migration provides a maintenance or interaction benefit. The user-facing gains do
   not depend on a framework choice.
5. Only after behavior and performance parity, consider switching the static build tooling or
   moving the reader into a client framework. Keep the existing URLs and data contracts as the
   acceptance boundary.

## Open product questions

- Is the reader’s primary audience single-language reading, or should side-by-side translation
  comparison be a first-class mode? This determines whether labels are always shown or only in a
  comparison layout.
- Should the docs remain one page with a compact contents drawer, or may advanced catalogue and
  licensing sections become separate pages while preserving current anchors?
- Is transliteration intended as a user-selectable edition with known alignment guarantees, or
  should it be hidden for scripts/chapters whose verse identity is not Hafs?
- Does “fast” prioritize first chapter-directory paint, first verse paint, or low bandwidth on
  repeat visits? The current cache makes repeat visits cheap, while first paint is gated by the
  metadata catalogue.
- Is offline reading a real requirement? Nothing in the current contract requires a service
  worker; adding one would need an explicit stale-content and storage policy.
