/*
 * The reader: one page, one hash route, and the dataset as its only data source.
 *
 * Route: `#/{chapter}[:{verse}]?s={script}&t={edition,edition}&tl={transliteration}&r={reciter}`
 *
 * The route carries everything needed to reproduce a view, so a link to 2:255 in a Warsh
 * script with two translations and a recitation works when pasted into a fresh tab; the
 * preferences in localStorage only supply defaults for a visit that has no route yet.
 *
 * Rendering is deliberately whole-view: a route change re-renders the view container and the
 * toolbar, and one delegated listener handles every interaction. Diffing a DOM this simple
 * would be more code and more bugs. The two things that must *not* be re-rendered wholesale
 * are the audio element (playback would stop) and the seek slider (it would fight the
 * listener's thumb), so both are updated in place.
 */

import { api, globalOffsets } from "./api.js";
import { Player } from "./audio.js";
import { currentTheme, loadPrefs, savePrefs, setTheme } from "./store.js";
import {
  byId,
  chapterGrid,
  editionKey,
  playerView,
  readerView,
  reciterPanel,
  surahGridHTML,
  toolbar,
  translationPanel,
} from "./ui.js";

const MAX_TRANSLATIONS = 3;
const ARABIC_SIZES = [1.35, 1.6, 1.9, 2.2, 2.5, 2.9];

const dom = {
  view: document.getElementById("view"),
  toolbar: document.getElementById("toolbar"),
  player: document.getElementById("player"),
  popover: document.getElementById("popover"),
  audio: document.getElementById("audio"),
  status: document.getElementById("status"),
};

const player = new Player(dom.audio);

let data = null; // manifest, chapters, catalogues, coverage, offsets
let state = loadPrefs();
let route = { chapter: null, verse: null };
let ui = { query: "", highlight: null };
let reciters = null; // loaded on first use: 136 KB is not worth a first paint
let loadToken = 0;
let pendingVerse = null; // a verse the reader asked for before choosing a reciter
let continuation = false; // the player rolled past the end of a chapter

/* ------------------------------------------------------------------- route --- */

function parseRoute() {
  const raw = location.hash.replace(/^#/, "");
  const [path, query] = raw.split("?");
  const params = new URLSearchParams(query ?? "");
  const [chapter, verse] = path.replace(/^\//, "").split(":");

  if (params.has("s")) state.script = params.get("s");
  if (params.has("t")) state.translations = params.get("t").split(",").filter(Boolean);
  if (params.has("tl")) state.transliteration = params.get("tl") || null;
  if (params.has("r")) state.reciter = params.get("r") || null;
  if (params.has("f")) state.font = params.get("f") || "auto";

  return {
    chapter: chapter ? Number(chapter) : null,
    verse: verse ? Number(verse) : null,
  };
}

function routeHash({ chapter = route.chapter, verse = null } = {}) {
  const params = new URLSearchParams();
  if (state.script) params.set("s", state.script);
  if (state.translations.length) params.set("t", state.translations.join(","));
  if (state.transliteration) params.set("tl", state.transliteration);
  if (state.reciter) params.set("r", state.reciter);
  if (state.font !== "auto") params.set("f", state.font);

  const path = chapter ? `/${chapter}${verse ? `:${verse}` : ""}` : "/";
  const query = params.toString();
  return `#${path}${query ? `?${query}` : ""}`;
}

function navigate({ chapter = route.chapter, verse = null, replace = false } = {}) {
  const hash = routeHash({ chapter, verse });
  const sameRoute = location.hash === hash;

  if (replace || sameRoute) {
    history.replaceState(null, "", hash);
    route = parseRoute();
    ui.highlight = route.verse;
    render();
    return;
  }

  location.hash = hash;
}

/** Persist what the reader chose, without the route: the defaults for the next visit. */
function remember(patch) {
  Object.assign(state, patch);
  savePrefs(state);
}

/* -------------------------------------------------------------------- data --- */

async function ensureReciters() {
  if (!reciters) reciters = await api.reciters();
  return reciters;
}

function translationsFor(catalogue) {
  return state.translations
    .map((key) => catalogue.editions.find((edition) => editionKey(edition) === key))
    .filter(Boolean);
}

/**
 * Which Hafs ayah numbers one verse of the selected script stands for.
 *
 * Translations are keyed to the Hafs count, and the scripts are not all keyed that way, so
 * the manifest says how: `hafs` ids are Hafs numbers, `mapped` verses carry the Hafs ayah
 * or ayahs they cover, and `own` labels are not Hafs numbers at all in the chapters the
 * manifest names. Nothing here guesses.
 */
export function hafsNumbers(script, verse) {
  if (script.verse_ids === "mapped") {
    const mapped = verse.number_in_hafs;
    return Array.isArray(mapped) ? mapped : [mapped ?? verse.id];
  }
  return [verse.id];
}

/** Merge the Arabic, the romanisation and every selected translation into verse records. */
function mergeChapter({ arabic, romanisation, translated, script }) {
  return arabic.verses.map((verse, index) => {
    const merged = { ...verse };

    if (romanisation?.verses[index]) {
      merged.transliteration = romanisation.verses[index].transliteration;
    }

    const numbers = hafsNumbers(script, verse);
    const translations = {};
    let footnote = null;

    for (const { key, chapter } of translated) {
      // A riwayah verse can cover two Hafs verses; both translations belong to it.
      const parts = numbers.map((number) => chapter.verses[number - 1]).filter(Boolean);
      if (!parts.length) continue;

      translations[key] = parts.map((entry) => entry.translation).join(" ");
      const notes = parts.map((entry) => entry.footnotes).filter(Boolean);
      if (notes.length) footnote = footnote ? `${footnote}\n\n${notes.join("\n\n")}` : notes.join("\n\n");
    }

    if (Object.keys(translations).length) merged.translations = translations;
    if (footnote) merged.footnote = footnote;

    return merged;
  });
}

function currentChapter() {
  return route.chapter ? byId(data.chapters, route.chapter) : null;
}

function currentScript() {
  return data.manifest.scripts.find((entry) => entry.id === state.script) ?? data.manifest.scripts[0];
}

/** `warsh` and `qalun` are riwayat, and the published per-ayah audio is all Hafs. */
function scriptRiwayah() {
  return ["warsh", "qalun"].includes(state.script) ? state.script : "hafs";
}

function configurePlayer(chapter = currentChapter()) {
  player.configure({
    reciters: reciters ?? undefined,
    chapter,
    offsets: data.offsets,
    riwayah: scriptRiwayah(),
  });
}

/* ------------------------------------------------------------------ render --- */

function setStatus(message, kind = "info") {
  dom.status.textContent = message ?? "";
  dom.status.dataset.kind = kind;
  dom.status.hidden = !message;
}

function renderToolbar() {
  dom.toolbar.innerHTML = toolbar({
    state,
    chapters: data.chapters,
    manifest: data.manifest,
    translations: data.translations,
    transliterations: data.transliterations,
    coverage: data.coverage,
    reciter: player.reciter,
  });
}

function renderPlayer() {
  if (!player.reciter || !player.open) {
    dom.player.hidden = true;
    dom.player.innerHTML = "";
    return;
  }

  dom.player.hidden = false;
  dom.player.innerHTML = playerView({
    host: player.host ?? { name: player.reciter.host, home: "" },
    reciter: player.reciter,
    state,
    playing: player.playing,
    progress: player.progress(),
    error: player.error,
    mismatch: player.conflicted,
  });
}

/** The slider is dragged by the reader too, so only move it when they are not holding it. */
function updateProgress() {
  const slider = dom.player.querySelector("[data-role=seek]");
  if (!slider || document.activeElement === slider) return;
  slider.value = String(Math.round(player.progress() * 1000));
}

function render() {
  const chapter = currentChapter();

  renderToolbar();
  renderPlayer();

  if (!chapter) {
    document.title = "quran-json — read the Quran";
    dom.view.innerHTML = chapterGrid({
      chapters: data.chapters,
      state,
      coverage: data.coverage,
      query: ui.query,
      resume: state.resume ?? null,
      scriptName: currentScript().name,
    });
    return;
  }

  loadChapter(chapter);
}

async function loadChapter(chapter) {
  const script = currentScript();
  const romanisationKey = state.transliteration;
  const token = ++loadToken;

  // Where a script's verse labels are not Hafs numbers, no translation can be joined to
  // them without inventing an alignment, so the reader shows the Arabic and says why.
  const diverges = (script.verse_ids_differ_in ?? []).includes(chapter.id);
  const selected = diverges ? [] : translationsFor(data.translations);

  setStatus("Loading…");
  try {
    const [arabic, romanisation, ...translated] = await Promise.all([
      api.text(state.script, chapter.id),
      romanisationKey ? api.transliteration(romanisationKey, chapter.id) : null,
      ...selected.map(async (edition) => ({
        key: editionKey(edition),
        chapter: await api.translation(editionKey(edition), chapter.id),
      })),
    ]);

    if (token !== loadToken) return; // a newer navigation won

    const verses = mergeChapter({ arabic, romanisation, translated, script });
    document.title = `${chapter.id}. ${chapter.transliteration} — quran-json`;

    dom.view.innerHTML = readerView({
      chapters: data.chapters,
      chapter,
      text: { verses },
      translations: selected,
      transliteration: romanisationKey ? { key: romanisationKey } : null,
      coverage: data.coverage,
      state,
      manifest: data.manifest,
      highlight: ui.highlight,
      perAyahDisabled: player.conflicted,
      reciter: player.reciter,
      translationNote: diverges
        ? `${script.name} does not number ${chapter.transliteration} the way the Hafs count ` +
          `that every translation is keyed to does (its verse 1 is Hafs 2, and its last two ` +
          `verses split Hafs 7), so no translation is shown beside it here. Read this ` +
          `chapter in another script to see translations.`
        : null,
    });

    setStatus(null);
    remember({ resume: { chapter: chapter.id, verse: route.verse ?? 1 } });
    configurePlayer(chapter);

    if (route.verse) {
      dom.view.querySelector(`#v${route.verse}`)?.scrollIntoView({ block: "center" });
    } else {
      window.scrollTo({ top: 0 });
    }

    if (continuation && player.reciter) {
      continuation = false;
      await player.start(1);
    }
  } catch (error) {
    if (token !== loadToken) return;
    setStatus(`Could not load this chapter: ${error.message}`, "error");
  }
}

/* ----------------------------------------------------------------- popovers --- */

function openPopover(html, focusSelector) {
  dom.popover.innerHTML = html;
  dom.popover.hidden = false;
  if (focusSelector) dom.popover.querySelector(focusSelector)?.focus();
}

function closePopover() {
  dom.popover.hidden = true;
  dom.popover.innerHTML = "";
}

function pickReciter(id) {
  const chosen = player.setReciter(id);
  remember({ reciter: id });
  closePopover();

  if (chosen && pendingVerse !== null) {
    const verse = pendingVerse;
    pendingVerse = null;
    configurePlayer();
    player.start(verse).then(renderPlayer);
    return;
  }

  renderPlayer();
  navigate({ verse: route.verse, replace: true });
}

/* ------------------------------------------------------------------- events --- */

document.addEventListener("click", async (event) => {
  const target = event.target.closest("[data-role]");
  if (!target) {
    if (!event.target.closest("#popover")) closePopover();
    return;
  }

  switch (target.dataset.role) {
    case "translation-picker":
      openPopover(
        translationPanel({ translations: data.translations, state }),
        "[data-role=translation-search]",
      );
      break;

    case "translation-clear":
      state = { ...state, translations: [] };
      remember({ translations: [] });
      closePopover();
      navigate({ replace: true });
      break;

    case "transliteration": {
      const first = data.transliterations.editions[0];
      if (!first) break;
      const chosen = state.transliteration ? null : editionKey(first);
      state = { ...state, transliteration: chosen };
      remember({ transliteration: chosen });
      navigate({ replace: true });
      break;
    }

    case "reciter-picker": {
      const index = await ensureReciters();
      openPopover(
        reciterPanel({ reciters: index, host: index.hosts.everyayah, state }),
        "[data-role=reciter-search]",
      );
      break;
    }

    case "size-down":
    case "size-up": {
      const delta = target.dataset.role === "size-up" ? 1 : -1;
      const size = Math.min(ARABIC_SIZES.length, Math.max(1, state.size + delta));
      remember({ size });
      document.documentElement.style.setProperty("--arabic-size", `${ARABIC_SIZES[size - 1]}rem`);
      break;
    }

    case "play-verse":
    case "play-surah": {
      await ensureReciters();
      const verse = target.dataset.role === "play-verse" ? Number(target.dataset.verse) : null;
      configurePlayer();

      if (!player.reciter) {
        pendingVerse = verse;
        openPopover(
          reciterPanel({ reciters, host: reciters.hosts.everyayah, state }),
          "[data-role=reciter-search]",
        );
        break;
      }

      await player.start(verse);
      renderPlayer();
      break;
    }

    case "toggle-play":
      player.toggle();
      break;

    case "prev-verse":
      await player.step(-1);
      break;

    case "next-verse":
      await player.step(1);
      break;

    case "toggle-repeat":
      remember({ repeat: !state.repeat });
      player.repeat = state.repeat;
      renderPlayer();
      break;

    case "toggle-autoplay":
      remember({ autoplay: !state.autoplay });
      player.autoplay = state.autoplay;
      renderPlayer();
      break;

    case "close-player":
      player.close();
      renderPlayer();
      break;

    case "copy-verse": {
      const verse = dom.view.querySelector(`#v${target.dataset.verse}`);
      await navigator.clipboard.writeText(verse?.innerText.trim() ?? "");
      target.textContent = "Copied";
      setTimeout(() => (target.textContent = "Copy"), 1200);
      break;
    }

    case "link-verse":
      await navigator.clipboard.writeText(
        `${location.origin}/app/${routeHash({ verse: Number(target.dataset.verse) })}`,
      );
      target.textContent = "Linked";
      setTimeout(() => (target.textContent = "Link"), 1200);
      break;

    case "theme":
      setTheme(currentTheme() === "dark" ? "light" : "dark");
      break;

    default:
      break;
  }
});

document.addEventListener("change", (event) => {
  const target = event.target.closest("[data-role]");
  if (!target) return;

  switch (target.dataset.role) {
    case "script":
      state = { ...state, script: target.value };
      remember({ script: state.script });
      navigate({ verse: null, replace: true });
      break;

    case "font":
      state = { ...state, font: target.value };
      remember({ font: state.font });
      navigate({ verse: route.verse, replace: true });
      break;

    case "translation": {
      const chosen = [...dom.popover.querySelectorAll("[data-role=translation]:checked")].map(
        (input) => input.value,
      );
      if (chosen.length > MAX_TRANSLATIONS) {
        target.checked = false;
        setStatus(`Up to ${MAX_TRANSLATIONS} translations at once.`, "error");
        return;
      }
      remember({ translations: chosen });
      navigate({ verse: route.verse, replace: true });
      break;
    }

    case "reciter":
      pickReciter(target.value);
      break;

    default:
      break;
  }
});

document.addEventListener("input", (event) => {
  const target = event.target.closest("[data-role]");
  if (!target) return;

  switch (target.dataset.role) {
    case "chapter-search": {
      ui.query = target.value;
      const grid = dom.view.querySelector(".surah-grid");
      if (grid) grid.innerHTML = surahGridHTML({ chapters: data.chapters, query: ui.query });
      break;
    }

    case "translation-search":
    case "reciter-search": {
      const needle = target.value.trim().toLowerCase();
      for (const item of dom.popover.querySelectorAll("[data-search]")) {
        item.hidden = Boolean(needle) && !item.dataset.search.includes(needle);
      }
      break;
    }

    case "seek":
      player.seek(Number(target.value) / 1000);
      break;

    default:
      break;
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") {
    closePopover();
    return;
  }

  const typing = ["INPUT", "SELECT", "TEXTAREA"].includes(event.target.tagName);
  if (typing || !player.reciter) return;

  if (event.key === " ") {
    event.preventDefault();
    player.toggle();
  }
});

player.onVerse = (verse) => {
  for (const node of dom.view.querySelectorAll(".verse.playing")) node.classList.remove("playing");
  if (!verse) return;

  const node = dom.view.querySelector(`#v${verse}`);
  node?.classList.add("playing");
  node?.scrollIntoView({ block: "center", behavior: "smooth" });
};

player.onProgress = updateProgress;
player.onState = renderPlayer;
player.onChapterEnd = (delta = 1) => {
  const next = byId(data.chapters, route.chapter + delta);
  if (!next) return;
  continuation = delta > 0;
  navigate({ chapter: next.id, verse: 1 });
};

/* --------------------------------------------------------------- start up --- */

async function main() {
  const [manifest, chapters, translations, transliterations, coverage] = await Promise.all([
    api.manifest(),
    api.chapters(),
    api.translations(),
    api.transliterations(),
    api.fonts(),
  ]);

  data = { manifest, chapters, translations, transliterations, coverage, offsets: globalOffsets(chapters) };

  // A fresh visit starts on a published script and on a language the browser asks for, when
  // the catalogue has one: the dataset's 57 languages are worth using rather than ignoring.
  if (!state.script || !manifest.scripts.some((entry) => entry.id === state.script)) {
    state.script = manifest.scripts[0].id;
  }
  if (!state.translations.length) {
    const wanted = (navigator.languages ?? [navigator.language ?? "en"]).map((tag) =>
      tag.split("-")[0].toLowerCase(),
    );
    const edition =
      translations.editions.find((entry) => wanted.includes(entry.code)) ??
      translations.editions.find((entry) => entry.code === "en") ??
      translations.editions[0];
    if (edition) state.translations = [editionKey(edition)];
  }
  if (state.transliteration && !transliterations.editions.length) state.transliteration = null;

  player.autoplay = state.autoplay;
  player.repeat = state.repeat;
  document.documentElement.style.setProperty(
    "--arabic-size",
    `${ARABIC_SIZES[(state.size ?? 3) - 1]}rem`,
  );

  route = parseRoute();
  ui.highlight = route.verse;

  if (state.reciter) {
    await ensureReciters();
    configurePlayer();
    player.setReciter(state.reciter);
  }

  window.addEventListener("hashchange", () => {
    route = parseRoute();
    ui.highlight = route.verse;
    render();
  });

  render();
}

main().catch((error) => {
  setStatus(`Could not start the reader: ${error.message}`, "error");
});
