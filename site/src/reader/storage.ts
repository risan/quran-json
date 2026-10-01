/** Reader preferences in localStorage. Every access is guarded: storage can be blocked or full. */

const PREFS_KEY = "quran-json:reader:v2";

export function loadStoredPrefs(): unknown {
  try {
    return JSON.parse(localStorage.getItem(PREFS_KEY) ?? "null");
  } catch {
    return null;
  }
}

export function saveStoredPrefs(prefs: unknown): void {
  try {
    localStorage.setItem(PREFS_KEY, JSON.stringify(prefs));
  } catch {
    // Private mode or a full quota: preferences just do not survive the page view.
  }
}
