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
  editionKey,
  alignsWithHafs,
  canJoinWithHafs,
  mergeChapter as mergeReaderChapter,
  normalizeReaderState,
  parseReaderHash,
  validateOptionalChapter,
} from "./reader-core.js";
import {
  byId,
  chapterGrid,
  playerView,
  readerView,
  reciterPanel,
  surahGridHTML,
  settingsPanel,
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
let popoverTrigger = null;
let catalogueWarnings = [];
let deferredOptionalPrefs = { translations: [], transliteration: null };

/* ------------------------------------------------------------------- route --- */

function parseRoute() {
  const parsed = parseReaderHash(location.hash);
  const params = parsed.params;
  catalogueWarnings = [];
  const raw = { ...state };
  if (params.has("s")) raw.script = params.get("s");
  if (params.has("t")) raw.translations = params.get("t").split(",").filter(Boolean);
  if (params.has("tl")) raw.transliteration = params.get("tl") || null;
  if (params.has("r")) raw.reciter = params.get("r") || null;
  if (params.has("f")) raw.font = params.get("f") || "auto";

  state = normalizeReaderState(raw, data);
  const chapter = byId(data.chapters, parsed.chapter);
  // The catalogue's chapter counts are Hafs counts. A selected mapped script can have a
  // different native count, so the Arabic chapter fetch is the authority for verse bounds.
  const verse = chapter && parsed.verse ? parsed.verse : null;

  const invalid = [];
  if (params.has("s") && raw.script !== state.script) invalid.push("script");
  if (params.has("t") && state.translations.length !== raw.translations.length) invalid.push("translation");
  if (params.has("tl") && raw.transliteration && !state.transliteration) invalid.push("transliteration");
  if (params.has("f") && raw.font !== state.font) invalid.push("font");
  if (
    parsed.invalidChapter ||
    parsed.invalidVerse ||
    (parsed.chapter && !chapter)
  ) {
    invalid.push("chapter link");
  }
  if (invalid.length) {
    catalogueWarnings = [
      "Some link options were unavailable (" + invalid.join(", ") + "); showing the published defaults.",
    ];
  }

  return { chapter: chapter?.id ?? null, verse };
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
  if (!reciters) {
    const requested = state.reciter;
    reciters = await api.reciters();
    state = normalizeReaderState(state, { ...data, reciters });
    if (requested && !state.reciter) {
      setStatus("That reciter is unavailable; choose one from the published list.", "error");
    }
    if (state.reciter) player.setReciter(state.reciter);
    renderToolbar();
  }
  return reciters;
}

function translationsFor(catalogue) {
  return state.translations
    .map((key) => catalogue.editions.find((edition) => editionKey(edition) === key))
    .filter(Boolean);
}

function cataloguePayload(value) {
  return value && Array.isArray(value.editions) ? value : { editions: [] };
}

function currentChapter() {
  return route.chapter ? byId(data.chapters, route.chapter) : null;
}

function currentScript() {
  return data.manifest.scripts.find((entry) => entry.id === state.script) ?? data.manifest.scripts[0];
}

function configurePlayer(chapter = currentChapter()) {
  player.configure({
    reciters: reciters ?? undefined,
    chapter,
    offsets: data.offsets,
    script: currentScript(),
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
    loadToken += 1;
    document.title = "quran-json — read the Quran";
    setStatus(catalogueWarnings.shift() ?? null, "error");
    dom.view.innerHTML = chapterGrid({
      chapters: data.chapters,
      state,
      coverage: data.coverage,
      query: ui.query,
      resume: state.resume ?? null,
      scriptName: currentScript().name,
      script: currentScript(),
    });
    return;
  }

  loadChapter(chapter);
}

async function loadChapter(chapter) {
  const script = currentScript();
  const romanisationKey = state.transliteration;
  const token = ++loadToken;

  // Only chapters explicitly marked as unjoinable suppress Hafs-keyed optional layers. Mapped
  // readings can have different counts and still join through each verse's source map.
  const diverges = !alignsWithHafs(script, chapter.id);
  const selected = diverges ? [] : translationsFor(data.translations);
  const optionalRequests = [];
  if (!diverges && romanisationKey) {
    optionalRequests.push({
      type: "transliteration",
      key: romanisationKey,
      promise: api.transliteration(romanisationKey, chapter.id),
    });
  }
  for (const edition of selected) {
    const key = editionKey(edition);
    optionalRequests.push({
      type: "translation",
      key,
      promise: api.translation(key, chapter.id),
    });
  }

  setStatus("Loading…");
  try {
    const [arabic, ...optionalResults] = await Promise.all([
      api.text(state.script, chapter.id),
      ...optionalRequests.map(({ type, key, promise }) =>
        promise
          .then((chapterData) => ({
            ok: true,
            type,
            key,
            chapter: validateOptionalChapter(chapterData, {
              chapterId: chapter.id,
              key,
              type,
              expectedVerseCount: chapter.total_verses,
            }),
          }))
          .catch((error) => ({ ok: false, type, key, error })),
      ),
    ]);

    if (token !== loadToken) return; // a newer navigation won

    // Validate a deep-linked native verse after loading the selected script. Optional layers
    // remain Hafs-keyed and continue to use `chapter.total_verses` above.
    const nativeVerseCount = arabic.verses.length;
    const requestedVerse = route.verse;
    if (requestedVerse && requestedVerse > nativeVerseCount) {
      route = { ...route, verse: null };
      ui.highlight = null;
      history.replaceState(null, "", routeHash({ verse: null }));
      catalogueWarnings.push(
        `Verse ${requestedVerse} is not present in ${script.name}; showing the chapter instead.`,
      );
    }
    const nativeChapter = { ...chapter, total_verses: nativeVerseCount };
    const mappingValid = canJoinWithHafs(script, arabic.verses);

    const romanResult = optionalResults.find(
      (result) => result.type === "transliteration" && result.key === romanisationKey,
    );
    const romanisation = romanResult?.ok && mappingValid ? romanResult.chapter : null;
    const translated = optionalResults.filter(
      (result) => result.ok && result.type === "translation",
    );
    const loadedTranslations = mappingValid
      ? selected.filter((edition) => translated.some((result) => result.key === editionKey(edition)))
      : [];
    const failedLayers = optionalResults.filter((result) => !result.ok);
    const mappingNote = mappingValid || (!selected.length && !romanisationKey)
      ? null
      : "Optional layers are unavailable because this script chapter has an invalid verse mapping.";
    const unavailableLayers = failedLayers.length + (mappingNote ? 1 : 0);
    const verses = mergeReaderChapter({
      arabic,
      romanisation,
      translated,
      script,
      chapterId: chapter.id,
    });
    document.title = `${chapter.id}. ${chapter.transliteration} — quran-json`;

    dom.view.innerHTML = readerView({
      chapters: data.chapters,
      chapter: nativeChapter,
      text: { verses },
     translations: loadedTranslations,
      transliteration: romanisation
        ? {
            key: romanisationKey,
            edition: data.transliterations.editions.find((edition) => editionKey(edition) === romanisationKey),
          }
        : null,
      coverage: data.coverage,
      state,
      manifest: data.manifest,
      highlight: ui.highlight,
      perAyahDisabled: player.conflicted,
      reciter: player.reciter,
      translationNote: diverges
        ? `${script.name} does not publish a safe verse mapping for this chapter, so Hafs-keyed ` +
          `translations and transliterations are hidden here. Read this chapter in another ` +
          `script to see those optional layers.`
        : null,
      layerNote: [
        mappingNote,
        failedLayers.length
          ? `Some optional layers could not be loaded: ${failedLayers
                .map((result) => result.key)
                .join(", ")}. Arabic remains available.`
          : null,
      ]
        .filter(Boolean)
        .join(" ") || null,
    });

    setStatus(
      unavailableLayers
        ? `Arabic is ready; ${unavailableLayers} optional layer${unavailableLayers > 1 ? "s" : ""} could not be loaded.`
        : catalogueWarnings.shift() ?? null,
      failedLayers.length ? "error" : "info",
    );
    remember({ resume: { chapter: chapter.id, verse: route.verse ?? 1 } });
    configurePlayer(nativeChapter);

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

function setModalInert(value) {
  for (const child of document.body.children) {
    if (child !== dom.popover) child.inert = value;
  }
}

function resolvedPopoverTrigger(record) {
  if (!record) return null;
  if (record.element?.isConnected) return record.element;
  if (!record.role) return null;
  return [...document.querySelectorAll('[data-role="' + record.role + '"]')].find(
    (element) => element !== dom.popover && element.getClientRects().length,
  ) ?? null;
}

function focusTrigger(role) {
  resolvedPopoverTrigger({ role })?.focus();
}

function openPopover(
  html,
  focusSelector,
  { label = "Reader choices", trigger = document.activeElement } = {},
) {
  const previous = popoverTrigger?.element ?? null;
  const parentTrigger = dom.popover.hidden || !dom.popover.contains(trigger) ? trigger : previous;
  if (previous && previous !== parentTrigger) previous.setAttribute("aria-expanded", "false");
  popoverTrigger = parentTrigger
    ? { element: parentTrigger, role: parentTrigger.dataset.role ?? null }
    : null;
  dom.popover.innerHTML = html;
  dom.popover.hidden = false;
  dom.popover.setAttribute("aria-label", label);
  setModalInert(true);
  if (parentTrigger) parentTrigger.setAttribute("aria-expanded", "true");
  if (focusSelector) dom.popover.querySelector(focusSelector)?.focus();
}

function closePopover({ restore = true } = {}) {
  const record = popoverTrigger;
  const trigger = resolvedPopoverTrigger(record);
  if (trigger) trigger.setAttribute("aria-expanded", "false");
  setModalInert(false);
  dom.popover.hidden = true;
  dom.popover.innerHTML = "";
  popoverTrigger = null;
  if (restore) trigger?.focus();
}

function pickReciter(id) {
  const chosen = player.setReciter(id);
  closePopover({ restore: false });
  remember({ reciter: id });

  if (chosen && pendingVerse !== null) {
    const verse = pendingVerse;
    pendingVerse = null;
    configurePlayer();
    renderToolbar();
    focusTrigger("reciter-picker");
    player.start(verse).then(renderPlayer);
    return;
  }

  renderPlayer();
  navigate({ verse: route.verse, replace: true });
  focusTrigger("reciter-picker");
}

/* ------------------------------------------------------------------- events --- */

document.addEventListener("click", async (event) => {
  const target = event.target.closest("[data-role]");
  if (!target) {
    if (!event.target.closest("#popover")) closePopover();
    return;
  }

  switch (target.dataset.role) {
    case "settings":
      openPopover(
        settingsPanel({
          state,
          manifest: data.manifest,
          transliterations: data.transliterations,
          coverage: data.coverage,
          reciter: player.reciter,
        }),
        "[data-role=script]",
        { label: "Reader settings", trigger: target },
      );
      break;

    case "translation-picker":
      openPopover(
        translationPanel({ translations: data.translations, state }),
        "[data-role=translation-search]",
        { label: "Translations", trigger: target },
      );
      break;

    case "translation-clear":
      state = { ...state, translations: [] };
      remember({ translations: [] });
      closePopover({ restore: false });
      navigate({ replace: true });
      focusTrigger("translation-picker");
      break;

    case "transliteration": {
      const first = data.transliterations.editions[0];
      if (!first) break;
      const fromPopover = dom.popover.contains(target);
      const chosen = state.transliteration ? null : editionKey(first);
      state = { ...state, transliteration: chosen };
      remember({ transliteration: chosen });
      if (fromPopover) closePopover({ restore: false });
      navigate({ replace: true });
      if (fromPopover) focusTrigger("settings");
      break;
    }

    case "reciter-picker": {
      const index = await ensureReciters();
      openPopover(
        reciterPanel({ reciters: index, host: index.hosts.everyayah, state, script: currentScript() }),
        "[data-role=reciter-search]",
        { label: "Recitation", trigger: target },
      );
      break;
    }

    case "close-popover":
      closePopover();
      break;

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
          reciterPanel({ reciters, host: reciters.hosts.everyayah, state, script: currentScript() }),
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
      {
        const fromPopover = dom.popover.contains(target);
        if (fromPopover) closePopover({ restore: false });
        state = { ...state, script: target.value };
        remember({ script: state.script });
        navigate({ verse: null, replace: true });
        if (fromPopover) focusTrigger("settings");
      }
      break;

    case "font":
      {
        const fromPopover = dom.popover.contains(target);
        if (fromPopover) closePopover({ restore: false });
        state = { ...state, font: target.value };
        remember({ font: state.font });
        navigate({ verse: route.verse, replace: true });
        if (fromPopover) focusTrigger("settings");
      }
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
      if (grid) {
        grid.innerHTML = surahGridHTML({
          chapters: data.chapters,
          query: ui.query,
          script: currentScript(),
        });
      }
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
    if (!dom.popover.hidden) closePopover();
    return;
  }
  if (!dom.popover.hidden && event.key === "Tab") {
    const focusable = [...dom.popover.querySelectorAll(
      "button:not([disabled]), input:not([disabled]), select:not([disabled]), [href], [tabindex]:not([tabindex=\"-1\"])",
    )].filter((item) => !item.hidden && item.getClientRects().length);
    if (focusable.length) {
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
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
function defaultTranslation(catalogue) {
  const wanted = (navigator.languages ?? [navigator.language ?? "en"]).map((tag) =>
    tag.split("-")[0].toLowerCase(),
  );
  return (
    catalogue.editions.find((entry) => wanted.includes(entry.code)) ??
    catalogue.editions.find((entry) => entry.code === "en") ??
    catalogue.editions[0] ??
    null
  );
}

async function loadCatalogues() {
  const [translationResult, transliterationResult] = await Promise.allSettled([
    api.translations(),
    api.transliterations(),
  ]);
  data.translations = translationResult.status === "fulfilled"
    ? cataloguePayload(translationResult.value)
    : { editions: [] };
  data.transliterations = transliterationResult.status === "fulfilled"
    ? cataloguePayload(transliterationResult.value)
    : { editions: [] };
  const failures = [];
  if (translationResult.status === "rejected") failures.push("translations");
  if (transliterationResult.status === "rejected") failures.push("transliteration");
  if (
    translationResult.status === "fulfilled" &&
    !Array.isArray(translationResult.value?.editions)
  ) {
    failures.push("translations");
  }
  if (
    transliterationResult.status === "fulfilled" &&
    !Array.isArray(transliterationResult.value?.editions)
  ) {
    failures.push("transliteration");
  }

 state = normalizeReaderState(state, data);
 route = parseRoute();
 const params = parseReaderHash(location.hash).params;
  if (!params.has("t") && deferredOptionalPrefs.translations.length) {
    state = { ...state, translations: deferredOptionalPrefs.translations };
  }
  if (!params.has("tl") && deferredOptionalPrefs.transliteration) {
    state = { ...state, transliteration: deferredOptionalPrefs.transliteration };
  }
  if (!params.has("t") && !state.translations.length && data.translations.editions.length) {
    const edition = defaultTranslation(data.translations);
    if (edition) state = { ...state, translations: [editionKey(edition)] };
  }
  state = normalizeReaderState(state, data);
 route = parseRoute();
 if (failures.length) {
    catalogueWarnings = [];
   catalogueWarnings.push("Optional " + failures.join(" and ") + " catalogue unavailable; Arabic remains readable.");
  }
  render();
}


async function main() {
  const [manifest, chapters, coverage] = await Promise.all([
    api.manifest(),
    api.chapters(),
    api.fonts(),
  ]);

  data = {
    manifest,
    chapters,
    translations: { editions: [] },
    transliterations: { editions: [] },
    coverage,
    offsets: globalOffsets(chapters),
  };

// A fresh visit starts on a published script and on a language the browser asks for, when
// the catalogue has one: the dataset's 57 languages are worth using rather than ignoring.
  deferredOptionalPrefs = {
    translations: Array.isArray(state.translations) ? [...state.translations] : [],
    transliteration: state.transliteration,
  };
 state = normalizeReaderState(
    { ...state, translations: [], transliteration: null },
    data,
  );

  player.autoplay = state.autoplay;
  player.repeat = state.repeat;
  document.documentElement.style.setProperty(
    "--arabic-size",
    `${ARABIC_SIZES[(state.size ?? 3) - 1]}rem`,
  );

  route = parseRoute();
  ui.highlight = route.verse;


 window.addEventListener("hashchange", () => {
    route = parseRoute();
    ui.highlight = route.verse;
    render();
  });

 render();
  loadCatalogues().catch((error) => {
    data.translations = { editions: [] };
    data.transliterations = { editions: [] };
    catalogueWarnings = ["Optional catalogues unavailable: " + error.message];
    render();
  });
}

main().catch((error) => {
  setStatus(`Could not start the reader: ${error.message}`, "error");
});
