/*
 * Documentation page behaviour: colour theme, code tabs and copy buttons, and the edition
 * filter. All of it is enhancement -- the page renders the catalogue server-side, so with
 * JavaScript disabled every table is still complete and every code sample still readable.
 */

const THEME_KEY = "quran-json:theme";

function applyTheme(theme) {
  const root = document.documentElement;
  if (theme) {
    root.dataset.theme = theme;
  } else {
    delete root.dataset.theme;
  }
}

function initTheme() {
  for (const button of document.querySelectorAll("[data-theme-toggle]")) {
    button.addEventListener("click", () => {
      const current =
        document.documentElement.dataset.theme ||
        (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
      const next = current === "dark" ? "light" : "dark";
      applyTheme(next);
      try {
        localStorage.setItem(THEME_KEY, next);
      } catch {
        /* private mode: the toggle still works for this page view */
      }
    });
  }
}

/* Language tabs: the first tab is selected, and every panel stays in the DOM so that
   `Ctrl+F` still finds a sample and a copy button still copies one. */
function initTabs() {
  for (const group of document.querySelectorAll("[data-tabs]")) {
    const tabs = [...group.querySelectorAll("[role=tab]")];
    const panels = [...group.querySelectorAll("pre[data-lang]")];
    if (!tabs.length || !panels.length) continue;

    const select = (lang) => {
      for (const tab of tabs) {
        const active = tab.dataset.lang === lang;
        tab.setAttribute("aria-selected", String(active));
        tab.tabIndex = active ? 0 : -1;
      }
      for (const panel of panels) {
        panel.hidden = panel.dataset.lang !== lang;
      }
    };

    for (const tab of tabs) {
      tab.addEventListener("click", () => select(tab.dataset.lang));
      tab.addEventListener("keydown", (event) => {
        const index = tabs.indexOf(tab);
        if (event.key === "ArrowRight") tabs[(index + 1) % tabs.length].focus();
        if (event.key === "ArrowLeft") tabs[(index - 1 + tabs.length) % tabs.length].focus();
      });
    }

    select(tabs[0].dataset.lang);
  }
}

function initCopyButtons() {
  for (const block of document.querySelectorAll("pre")) {
    const source = block.querySelector("code");
    if (!source) continue;

    const button = document.createElement("button");
    button.type = "button";
    button.className = "copy";
    button.textContent = "copy";
    button.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(source.textContent);
        button.textContent = "copied";
      } catch {
        button.textContent = "press ⌘C";
      }
      setTimeout(() => {
        button.textContent = "copy";
      }, 1500);
    });
    block.append(button);
  }
}

/* Filters a table's rows on their visible text, and reports how many survived. */
function initFilters() {
  for (const input of document.querySelectorAll("[data-filter]")) {
    const name = input.dataset.filter;
    const table = document.querySelector(`[data-filterable=${name}]`);
    const counter = document.querySelector(`[data-filter-count=${name}]`);
    if (!table) continue;

    const rows = [...table.querySelectorAll("tbody tr")];
    const total = rows.length;

    input.addEventListener("input", () => {
      const needle = input.value.trim().toLowerCase();
      let shown = 0;
      for (const row of rows) {
        const match = !needle || row.textContent.toLowerCase().includes(needle);
        row.hidden = !match;
        if (match) shown += 1;
      }
      if (counter) {
        counter.textContent =
          shown === total ? `${total} editions` : `${shown} of ${total} editions`;
      }
    });
  }
}

initTheme();
initTabs();
initCopyButtons();
initFilters();
