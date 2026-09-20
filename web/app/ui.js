/*
 * Rendering. Every function here returns HTML for `innerHTML`; every value that comes from
 * the dataset goes through `esc()`, because an author name or a footnote is data from a
 * third party and must never be interpreted as markup.
 *
 * The Arabic font is not a styling detail. Which font can render a script is measured at
 * build time and published at /app/fonts.json, so a script/font pair that would render
 * missing-glyph boxes is never offered.
 */

import {
  editionKey,
  nativeChapterCount,
  recitersForScript,
  scriptReadingIdentity,
} from "./reader-core.js";

export function esc(value) {
  return String(value ?? "").replace(
    /[&<>"']/g,
    (character) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character],
  );
}

export function byId(chapters, id) {
  return chapters.find((chapter) => chapter.id === Number(id));
}

export function fontOf(state, coverage, script) {
  const entry = coverage?.scripts?.[script] ?? Object.values(coverage?.scripts ?? {})[0] ?? {
    usable: [],
    default: "amiri",
  };
  return state.font !== "auto" && entry.usable?.includes(state.font) ? state.font : entry.default;
}

export function familyOf(coverage, fontId) {
  return coverage.fonts.find((font) => font.id === fontId)?.name ?? "Amiri";
}

export function arabicStyle(state, coverage, script) {
  return `--arabic-family:'${familyOf(coverage, fontOf(state, coverage, script))}'`;
}

const PAD = (value) => String(value).padStart(3, "0");

/* ------------------------------------------------------------- chapter grid --- */

export function surahGridHTML({ chapters, query, script = null }) {
  const needle = query.trim().toLowerCase();
  const cards = chapters
    .filter((chapter) => {
      if (!needle) return true;
      return (
        String(chapter.id) === needle ||
        String(chapter.id).padStart(3, "0") === needle ||
        chapter.name.includes(query.trim()) ||
        chapter.transliteration.toLowerCase().includes(needle) ||
        chapter.translation.toLowerCase().includes(needle)
      );
    })
    .map(
      (chapter) => `
      <a class="surah-card" href="#/${chapter.id}" data-chapter="${chapter.id}">
        <span class="surah-no">${chapter.id}</span>
        <span class="surah-names">
          <span class="surah-latin">${esc(chapter.transliteration)}</span>
          <span class="surah-arabic arabic" lang="ar" dir="rtl">${esc(chapter.name)}</span>
        </span>
        <span class="surah-meta">
          <span>${esc(chapter.translation)}</span>
          <span class="dot">·</span>
          <span>${nativeChapterCount(script, chapter.id, chapter.total_verses)} verses</span>
          <span class="tag ${chapter.type}">${esc(chapter.type)}</span>
        </span>
      </a>`,
    )
    .join("");

  return cards || '<p class="empty">No chapter matches that.</p>';
}

export function chapterGrid({ chapters, state, coverage, query, resume, scriptName, script = null }) {
  const scriptId = state.script;
  const font = fontOf(state, coverage, scriptId);

  const resumeCard = resume
    ? `<a class="button" href="#/${esc(resume.chapter)}:${esc(resume.verse)}">Continue at ${esc(
        resume.chapter,
      )}:${esc(resume.verse)}</a>`
    : "";

  return `
    <section class="grid-view" style="${arabicStyle(state, coverage, scriptId)}">
      <header class="view-head">
        <div>
          <h1>Read the Quran</h1>
          <p class="muted">
            ${chapters.length} chapters · ${esc(scriptName ?? scriptId)} · ${esc(
              familyOf(coverage, font),
            )}, chosen for this script
          </p>
        </div>
        ${resumeCard}
      </header>
      <label class="search">
        <span class="visually-hidden">Find a chapter</span>
        <input type="search" data-role="chapter-search" value="${esc(query)}"
          placeholder="Find a chapter by number, name or meaning…">
      </label>
      <div class="surah-grid">${surahGridHTML({ chapters, query, script })}</div>
    </section>`;
}

/* ----------------------------------------------------------------- toolbar --- */

export function toolbar({
  state,
  chapters,
  manifest,
  translations,
  transliterations,
  coverage,
  reciter,
}) {
  const script = manifest.scripts.find((entry) => entry.id === state.script);
  const entry = coverage.scripts[state.script] ?? Object.values(coverage.scripts)[0] ?? { usable: [], missing: {}, default: "amiri" };
  const chosen = state.translations.length;

  const fontOptions = coverage.fonts
    .map((font) => {
      const gaps = entry.missing?.[font.id];
      const label = font.name + (gaps ? ` — ${Object.keys(gaps).length} codepoints missing` : "");
      const disabled = gaps ? " disabled" : "";
      const selected = state.font === "auto" ? "" : font.id === state.font ? " selected" : "";
      return `<option value="${font.id}"${disabled}${selected}>${esc(label)}</option>`;
    })
    .join("");

  const transliterationKey = state.transliteration;

  return `
    <div class="toolbar-inner" role="region" aria-label="Reader controls">
      <div class="toolbar-primary">
      <label class="field">
        <span class="field-label">Script</span>
        <select id="reader-script" data-role="script" aria-label="Text script">
          ${manifest.scripts
            .map(
              (item) =>
                `<option value="${esc(item.id)}"${item.id === state.script ? " selected" : ""}>${esc(
                  item.name,
                )}</option>`,
            )
            .join("")}
        </select>
      </label>
      <button class="button settings-trigger" type="button" data-role="settings" aria-label="Open reader settings" aria-haspopup="dialog" aria-controls="popover" aria-expanded="false">Settings</button>
      </div>
      <div class="toolbar-controls">

      <label class="field">
        <span class="field-label">Font</span>
        <select id="reader-font" data-role="font" aria-label="Arabic font">
          <option value="auto"${state.font === "auto" ? " selected" : ""}>Auto (${
            coverage.fonts.find((font) => font.id === entry.default)?.name ?? entry.default
          })</option>
          ${fontOptions}
        </select>
      </label>

      <div class="field">
        <span class="field-label">Translation${chosen > 1 ? "s" : ""}</span>
        <button class="button" type="button" data-role="translation-picker" aria-controls="popover" aria-haspopup="dialog" aria-expanded="false">
          ${
            chosen
              ? `${chosen} selected<span class="chev">▾</span>`
              : `Choose…<span class="chev">▾</span>`
          }
        </button>
      </div>

      <div class="field">
        <span class="field-label">Transliteration</span>
        ${
          transliterations.editions.length
            ? `<button class="button" type="button" data-role="transliteration" aria-pressed="${
                transliterationKey ? "true" : "false"
              }">${transliterationKey ? "On" : "Off"}</button>`
            : `<button class="button" type="button" disabled
                 title="No romanisation with a redistribution grant is published.">None published</button>`
        }
      </div>

      <div class="field">
        <span class="field-label">Recitation</span>
        <button class="button" type="button" data-role="reciter-picker" aria-controls="popover" aria-haspopup="dialog" aria-expanded="false">
          ${reciter ? esc(reciter.name) : "Choose…"}<span class="chev">▾</span>
        </button>
      </div>

      <div class="field">
        <span class="field-label">Arabic size</span>
        <div class="stepper">
          <button class="button icon" type="button" data-role="size-down" aria-label="Smaller Arabic">A−</button>
          <button class="button icon" type="button" data-role="size-up" aria-label="Larger Arabic">A+</button>
        </div>
      </div>
      </div>
    </div>
    ${
      script?.note
        ? `<details class="script-note"><summary>About <code>${esc(state.script)}</code></summary><p>${esc(
            script.note,
          )}</p></details>`
        : ""
    }`;
}

export function settingsPanel({ state, manifest, transliterations, coverage, reciter }) {
  const scriptOptions = manifest.scripts
    .map((item) => `<option value="${esc(item.id)}"${item.id === state.script ? " selected" : ""}>${esc(item.name)}</option>`)
    .join("");
  const entry = coverage.scripts[state.script] ?? Object.values(coverage.scripts)[0] ?? { usable: [], missing: {}, default: "amiri" };
  const fonts = coverage.fonts
    .map((font) => {
      const disabled = entry.missing?.[font.id] ? " disabled" : "";
      return `<option value="${esc(font.id)}"${disabled}${state.font === font.id ? " selected" : ""}>${esc(font.name)}</option>`;
    })
    .join("");
  return `
    <section class="settings-sheet" aria-labelledby="settings-title">
      <div class="popover-head">
        <div>
          <h2 id="settings-title">Reader settings</h2>
          <p class="popover-hint">Choose the text, language and reading comfort for this visit.</p>
        </div>
        <button class="button ghost" type="button" data-role="close-popover" aria-label="Close reader settings">Close</button>
      </div>
      <div class="settings-grid">
        <label class="field"><span class="field-label">Script</span><select data-role="script" aria-label="Text script">${scriptOptions}</select></label>
        <label class="field"><span class="field-label">Font</span><select data-role="font" aria-label="Arabic font"><option value="auto"${state.font === "auto" ? " selected" : ""}>Auto</option>${fonts}</select></label>
        <div class="field"><span class="field-label">Translations</span><button class="button" type="button" data-role="translation-picker" aria-haspopup="dialog" aria-controls="popover">${state.translations.length ? `${state.translations.length} selected` : "Choose…"}</button></div>
        <div class="field"><span class="field-label">Transliteration</span>${transliterations.editions.length ? `<button class="button" type="button" data-role="transliteration" aria-pressed="${state.transliteration ? "true" : "false"}">${state.transliteration ? "On" : "Off"}</button>` : `<span class="muted">None published</span>`}</div>
        <div class="field"><span class="field-label">Recitation</span><button class="button" type="button" data-role="reciter-picker" aria-haspopup="dialog" aria-controls="popover">${reciter ? esc(reciter.name) : "Choose…"}</button></div>
        <div class="field"><span class="field-label">Arabic size</span><div class="stepper"><button class="button icon" type="button" data-role="size-down" aria-label="Smaller Arabic">A−</button><button class="button icon" type="button" data-role="size-up" aria-label="Larger Arabic">A+</button></div></div>
      </div>
    </section>`;
}

export function translationPanel({ translations, state }) {

  const rows = translations.editions
    .map((edition) => {
      const key = editionKey(edition);
      const checked = state.translations.includes(key) ? " checked" : "";
      return `
        <label class="pick" data-search="${esc(
          `${edition.code} ${edition.author} ${key} ${edition.direction}`.toLowerCase(),
        )}">
          <input type="checkbox" data-role="translation" value="${esc(key)}"${checked}>
          <span class="pick-body">
            <span class="pick-author">${esc(edition.author)}</span>
            <span class="pick-meta">
              <code>${esc(key)}</code>
              <span class="dot">·</span>${esc(edition.code)}
              ${edition.direction === "rtl" ? '<span class="dot">·</span>rtl' : ""}
            </span>
          </span>
        </label>`;
    })
    .join("");

  return `
   <div class="popover-head">
      <div class="popover-title">
        <h2 id="translation-title">Translations</h2>
        <p class="popover-hint">Up to three editions can sit beside each verse.</p>
      </div>
      <label class="popover-search"><span class="visually-hidden">Filter translations</span><input type="search" data-role="translation-search" aria-label="Filter translations" placeholder="Filter by language, translator or path…"></label>
      <button class="button ghost" type="button" data-role="translation-clear">Clear</button>
      <button class="button ghost" type="button" data-role="close-popover" aria-label="Close translations">Close</button>
   </div>
   <div class="popover-list">${rows}</div>`;
}

/* ------------------------------------------------------------------ reader --- */

export function readerView({
  chapters,
  chapter,
  text,
  translations,
  transliteration,
  coverage,
  state,
  manifest,
  highlight,
  perAyahDisabled = false,
  reciter = null,
  translationNote = null,
  layerNote = null,
}) {
  const previous = byId(chapters, chapter.id - 1);
  const next = byId(chapters, chapter.id + 1);
  const transliterationKey = transliteration?.key ?? null;
  const furniture = (manifest?.scripts?.find((script) => script.id === state.script)?.chapter_furniture ?? [])
    .filter((item) => item.chapter === chapter.id && item.position === "before-verses" && item.numbered === false);
  const furnitureHTML = furniture
    .map(
      (item) =>
        `<div class="chapter-furniture arabic" lang="ar" dir="rtl" data-furniture="${esc(item.kind)}">${esc(item.text)}</div>`,
    )
    .join("");

  const verses = text.verses
    .map((verse) => {
      const blocks = translations
        .map((edition) => {
          const key = editionKey(edition);
          const label = `${edition.author ?? key} · ${edition.code ?? ""}`;
          const editionNote = verse.footnotes?.[key]
            ? `<details class="footnotes"><summary>${esc(label)} note</summary><p>${esc(
                verse.footnotes[key],
              )}</p></details>`
            : "";
          return `<div class="translation-block">
            <p class="translation-label">${esc(label)}</p>
            <p class="translation" dir="${edition.direction ?? "ltr"}" lang="${esc(edition.code ?? "und")}">${esc(
              verse.translations?.[key] ?? "",
            )}</p>
            ${editionNote}
          </div>`;
        })
        .join("");

      const footnote = verse.footnote
        ? `<details class="footnotes"><summary>Translator's note</summary><p>${esc(
            verse.footnote,
          )}</p></details>`
        : "";

      const romanised = transliterationKey
        ? `<p class="transliteration" lang="${esc(transliteration?.edition?.code ?? "und-Latn")}">${esc(verse.transliteration ?? "")}</p>`
        : "";

      return `
      <li class="verse${highlight === verse.id ? " highlight" : ""}" id="v${verse.id}" data-verse="${
        verse.id
      }">
        <div class="verse-gutter">
          <button class="verse-no" type="button" data-role="play-verse" data-verse="${verse.id}"
            ${perAyahDisabled ? 'disabled title="Per-ayah audio is not declared compatible with this script; choose a surah recitation to listen."' : ""}
            aria-label="Play verse ${chapter.id}:${verse.id}">${verse.id}</button>
        </div>
        <div class="verse-body">
          <p class="arabic" lang="ar" dir="rtl">${esc(verse.text)}</p>
          ${romanised}
          ${blocks}
          ${footnote}
          <div class="verse-tools">
            <button type="button" data-role="copy-verse" data-verse="${verse.id}">Copy</button>
            <button type="button" data-role="link-verse" data-verse="${verse.id}">Link</button>
            ${
              verse.number_in_hafs
                ? `<span class="tag" title="This riwayah verse covers Hafs ayah ${
                    Array.isArray(verse.number_in_hafs)
                      ? verse.number_in_hafs.join(", ")
                      : verse.number_in_hafs
                  }">Hafs ${Array.isArray(verse.number_in_hafs) ? verse.number_in_hafs.join("–") : verse.number_in_hafs}</span>`
                : ""
            }
          </div>
        </div>
      </li>`;
    })
    .join("");

  const editionNames = translationNote
    ? "translation not alignable in this script"
    : translations.length
      ? translations.map((edition) => esc(edition.author)).join(" · ")
      : "no translation selected";

  return `
   <article class="reader" aria-labelledby="chapter-title" style="${arabicStyle(state, coverage, state.script)}">
      <header class="chapter-head">
        <div class="chapter-title">
          <p class="muted">Surah ${chapter.id} of ${chapters.length} · ${esc(chapter.type)}</p>
          <h1 id="chapter-title">
            <span class="latin">${esc(chapter.transliteration)}</span>
            <span class="arabic" lang="ar" dir="rtl">${esc(chapter.name)}</span>
          </h1>
          <p class="muted">
            ${esc(chapter.translation)} · ${chapter.total_verses} verses · ${editionNames}
          </p>
        </div>
        <nav class="chapter-nav" aria-label="Chapter navigation">
          ${
            previous
              ? `<a class="button" href="#/${previous.id}">← ${previous.id}</a>`
              : '<span class="button" aria-disabled="true">←</span>'
          }
          <a class="button" href="#/">All chapters</a>
          <button class="button" type="button" data-role="play-surah">
            ▶ ${reciter?.scope === "surah" ? "Listen to this surah" : "Listen"}
          </button>
          ${
            next
              ? `<a class="button" href="#/${next.id}">${next.id} →</a>`
              : '<span class="button" aria-disabled="true">→</span>'
          }
        </nav>
      </header>
      ${[translationNote, layerNote]
        .filter(Boolean)
        .map((note) => `<p class="note warn" role="note">${esc(note)}</p>`)
        .join("")}
      ${furnitureHTML}
      <ol class="verses">${verses}</ol>
      <details class="data-paths">
        <summary>Data behind this page</summary>
        <ul>
          <li><a href="/text/${esc(state.script)}/chapters/${chapter.id}.json"><code>/text/${esc(
            state.script,
          )}/chapters/${chapter.id}.json</code></a> — the Arabic in <code>${esc(state.script)}</code></li>
          ${translations
            .map(
              (edition) =>
                `<li><a href="/translations/${esc(editionKey(edition))}/chapters/${
                  chapter.id
                }.json"><code>/translations/${esc(editionKey(edition))}/chapters/${
                  chapter.id
                }.json</code></a> — ${esc(edition.author)}</li>`,
            )
            .join("")}
          ${
            transliterationKey
              ? `<li><a href="/transliteration/${esc(transliterationKey)}/chapters/${chapter.id}.json"><code>/transliteration/${esc(
                  transliterationKey,
                )}/chapters/${chapter.id}.json</code></a></li>`
              : ""
          }
          <li><a href="/chapters.json"><code>/chapters.json</code></a> — chapter metadata</li>
        </ul>
      </details>
      <footer class="chapter-foot">
        <nav class="chapter-nav" aria-label="Adjacent chapters">
          ${
            previous
              ? `<a class="button" href="#/${previous.id}">← ${esc(previous.transliteration)}</a>`
              : ""
          }
          ${
            next
              ? `<a class="button" href="#/${next.id}">${esc(next.transliteration)} →</a>`
              : ""
          }
        </nav>
      </footer>
    </article>`;
}

/* ------------------------------------------------------------------ player --- */

export function playerView({ reciter, host, state, playing, progress, error, mismatch }) {
  const label = reciter.scope === "ayah" ? "Ayah" : "Surah";

  return `
    <div class="player-inner">
      <button class="button icon" type="button" data-role="toggle-play" aria-label="${
        playing ? "Pause" : "Play"
      }">${playing ? "❚❚" : "▶"}</button>
      <button class="button icon" type="button" data-role="prev-verse" aria-label="Previous verse">⏮</button>
      <button class="button icon" type="button" data-role="next-verse" aria-label="Next verse">⏭</button>
      <div class="player-now">
        <span class="player-title">${esc(reciter.name)}<span class="dot">·</span>${esc(
          label,
        )}<span class="dot">·</span>${esc(host.name)}</span>
        <span class="player-sub${error || mismatch ? " warn" : ""}">${esc(
          error ??
            (mismatch
              ? "Per-ayah audio is not declared compatible with this script"
              : reciter.recitation ??
                  `${reciter.bitrate_kbps ? `${reciter.bitrate_kbps} kbps · ` : ""}${host.name}`),
        )}</span>
      </div>
      <div class="player-progress">
        <input type="range" min="0" max="1000" value="${Math.round(progress * 1000)}"
          data-role="seek" aria-label="Seek">
      </div>
      <button class="button icon" type="button" data-role="toggle-repeat" aria-pressed="${
        state.repeat ? "true" : "false"
      }" aria-label="Repeat this verse">↻</button>
      <button class="button icon" type="button" data-role="toggle-autoplay" aria-pressed="${
        state.autoplay ? "true" : "false"
      }" aria-label="Play the next verse automatically">⇥</button>
      <button class="button icon" type="button" data-role="close-player" aria-label="Close the player">✕</button>
    </div>`;
}

export function reciterPanel({ reciters, host, state, script = null }) {
  script ??= { id: state.script };
  const identity = scriptReadingIdentity(script);
  const usable = recitersForScript(reciters.reciters, script);
  const sorted = [...usable].sort((a, b) => {
    const desired = [identity.riwayah, identity.name, identity.id]
      .filter(Boolean)
      .map((value) => String(value).toLowerCase());
    const score = (reciter) => {
      const text = `${reciter.recitation ?? ""} ${reciter.name} ${reciter.id}`.toLowerCase();
      return desired.some((value) => text.includes(value)) ? 0 : 1;
    };
    return score(a) - score(b) || a.name.localeCompare(b.name);
  });

  const rows = sorted
    .map(
      (reciter) => `
      <label class="pick" data-search="${esc(
        `${reciter.name} ${reciter.recitation ?? ""} ${reciter.id} ${reciter.scope}`.toLowerCase(),
      )}">
        <input type="radio" name="reciter" data-role="reciter" value="${esc(reciter.id)}"${
          reciter.id === state.reciter ? " checked" : ""
        }>
        <span class="pick-body">
          <span class="pick-author">${esc(reciter.name)}</span>
          <span class="pick-meta">
            ${esc(reciter.scope)}<span class="dot">·</span>${esc(
              reciter.host,
            )}${reciter.bitrate_kbps ? `<span class="dot">·</span>${reciter.bitrate_kbps} kbps` : ""}${
              reciter.recitation ? `<span class="dot">·</span>${esc(reciter.recitation)}` : ""
            }
          </span>
        </span>
      </label>`,
    )
    .join("");

  return `
   <div class="popover-head">
      <div class="popover-title"><h2 id="reciter-title">Recitation</h2></div>
      <label class="popover-search"><span class="visually-hidden">Filter reciters</span><input type="search" data-role="reciter-search" aria-label="Filter reciters" placeholder="Filter by reciter or recitation…" value=""></label>
      <button class="button ghost" type="button" data-role="close-popover" aria-label="Close recitation choices">Close</button>
   </div>
    <p class="popover-hint">
      Recitations are hosted by ${esc(host.name)} and others; this site publishes URL templates and
      hosts no audio. ${
        !identity.perAyah
          ? "Per-ayah recitations are hidden because their Hafs reading and numbering are not declared compatible with this script."
          : ""
      }
    </p>
    <div class="popover-list">${rows}</div>`;
}
