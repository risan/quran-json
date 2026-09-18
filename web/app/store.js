/*
 * Reader preferences, kept in localStorage. The URL is the source of truth for what is on
 * screen (so a link reproduces it); these are the defaults a fresh visit starts from.
 */

const KEY = "quran-json:reader";
const THEME_KEY = "quran-json:theme";

export const defaults = {
  script: null,
  translations: [],
  transliteration: null,
  reciter: null,
  font: "auto",
  size: 3,
  autoplay: true,
  repeat: false,
};

export function loadPrefs() {
  let stored = {};
  try {
    stored = JSON.parse(localStorage.getItem(KEY) ?? "{}") ?? {};
  } catch {
    stored = {};
  }

  const prefs = { ...defaults, ...stored };
  if (!Array.isArray(prefs.translations)) prefs.translations = [];
  if (typeof prefs.size !== "number") prefs.size = defaults.size;
  return prefs;
}

/** Write the reader's choices. The stored object mirrors the live state, not a merge of
 * stale defaults with a patch -- a patch merged over *stored* values would resurrect the
 * defaults the reader has since changed. */
export function savePrefs(values) {
  const next = { ...defaults, ...values };
  try {
    localStorage.setItem(KEY, JSON.stringify(next));
  } catch {
    /* private mode: preferences simply do not survive the page view */
  }
  return next;
}

export function theme() {
  try {
    return localStorage.getItem(THEME_KEY);
  } catch {
    return null;
  }
}

export function setTheme(value) {
  const root = document.documentElement;
  if (value) root.dataset.theme = value;
  else delete root.dataset.theme;
  try {
    if (value) localStorage.setItem(THEME_KEY, value);
    else localStorage.removeItem(THEME_KEY);
  } catch {
    /* private mode */
  }
}

export function currentTheme() {
  return (
    document.documentElement.dataset.theme ||
    (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")
  );
}
