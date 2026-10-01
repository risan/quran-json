/** Progressive enhancement for the docs page: it is complete without any of this. */

function setupTabs() {
  document.querySelectorAll<HTMLElement>("[data-tabs]").forEach((root) => {
    const tabs = [...root.querySelectorAll<HTMLButtonElement>("[data-tab]")];
    const panels = [...root.querySelectorAll<HTMLElement>("[data-panel]")];
    const copy = root.querySelector<HTMLButtonElement>("[data-copy]");
    let selected = 0;

    root.querySelector<HTMLElement>("[data-tablist]")?.removeAttribute("hidden");
    root.querySelector<HTMLElement>("[data-tabs-static]")?.setAttribute("hidden", "");
    root.querySelectorAll<HTMLElement>("[data-panel-caption]").forEach((caption) => {
      caption.hidden = true;
    });
    copy?.removeAttribute("hidden");

    function select(index: number) {
      selected = index;
      tabs.forEach((tab, tabIndex) => {
        tab.setAttribute("aria-selected", String(tabIndex === index));
        tab.tabIndex = tabIndex === index ? 0 : -1;
      });
      panels.forEach((panel, panelIndex) => {
        panel.hidden = panelIndex !== index;
      });
    }

    tabs.forEach((tab, index) => {
      tab.addEventListener("click", () => select(index));
      tab.addEventListener("keydown", (event) => {
        const step = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;

        if (step === 0) {
          return;
        }

        const next = (index + step + tabs.length) % tabs.length;

        select(next);
        tabs[next].focus();
        event.preventDefault();
      });
    });

    copy?.addEventListener("click", async () => {
      const code = panels[selected]?.dataset.code ?? "";
      const status = root.querySelector<HTMLElement>("[data-copy-status]");

      try {
        await navigator.clipboard.writeText(code);
      } catch {
        if (status) {
          status.textContent = "Copy failed. Select the code and copy it.";
        }

        return;
      }

      copy.querySelector("[data-copy-icon]")?.classList.add("hidden");
      copy.querySelector("[data-copied-icon]")?.classList.remove("hidden");
      copy.querySelector("[data-copy-label]")!.textContent = "Copied";

      if (status) {
        status.textContent = "Copied to the clipboard.";
      }

      setTimeout(() => {
        copy.querySelector("[data-copy-icon]")?.classList.remove("hidden");
        copy.querySelector("[data-copied-icon]")?.classList.add("hidden");
        copy.querySelector("[data-copy-label]")!.textContent = "Copy";
      }, 1500);
    });

    select(0);
  });
}

function setupScrollSpy() {
  const links = [...document.querySelectorAll<HTMLAnchorElement>("[data-toc-link]")];
  const ids = [...new Set(links.map((link) => link.dataset.tocLink ?? ""))];
  const sections = ids
    .map((id) => document.getElementById(id))
    .filter((section): section is HTMLElement => section !== null);
  const label = document.querySelector<HTMLElement>("[data-toc-current]");

  if (!sections.length) {
    return;
  }

  function mark(id: string) {
    links.forEach((link) => {
      if (link.dataset.tocLink === id) {
        link.setAttribute("aria-current", "true");
      } else {
        link.removeAttribute("aria-current");
      }
    });

    const active = links.find((link) => link.dataset.tocLink === id);

    if (label && active) {
      label.textContent = active.textContent?.trim() ?? "";
    }
  }

  function update() {
    // The last section whose top has passed the sticky header is the one being read.
    let current = sections[0].id;

    for (const section of sections) {
      if (section.getBoundingClientRect().top <= 96) {
        current = section.id;
      }
    }

    if (window.innerHeight + window.scrollY >= document.body.scrollHeight - 4) {
      current = sections[sections.length - 1].id;
    }

    mark(current);
  }

  addEventListener("scroll", update, { passive: true });
  addEventListener("resize", update);
  update();
}

function setupTocSheet() {
  const dialog = document.querySelector<HTMLDialogElement>("[data-toc-dialog]");

  if (!dialog) {
    return;
  }

  document.querySelectorAll("[data-toc-open]").forEach((button) => {
    button.addEventListener("click", () => dialog.showModal());
  });
  dialog.querySelector("[data-toc-close]")?.addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (event) => {
    // A click on the backdrop lands on the dialog element itself.
    if (event.target === dialog || (event.target as HTMLElement).closest("a")) {
      dialog.close();
    }
  });
}

function setupTranslationFilter() {
  const root = document.querySelector<HTMLElement>("[data-translations]");

  if (!root) {
    return;
  }

  const search = root.querySelector<HTMLInputElement>("[data-translation-search]");
  const language = root.querySelector<HTMLSelectElement>("[data-translation-language]");
  const rows = [...root.querySelectorAll<HTMLTableRowElement>("[data-translation-row]")];
  const status = root.querySelector<HTMLElement>("[data-translation-count]");
  const empty = root.querySelector<HTMLElement>("[data-translation-empty]");
  const controls = root.querySelector<HTMLElement>("[data-translation-controls]");

  controls?.removeAttribute("hidden");

  function apply() {
    const query = (search?.value ?? "").trim().toLowerCase();
    const selected = language?.value ?? "";
    let shown = 0;

    for (const row of rows) {
      const matches =
        (!selected || row.dataset.language === selected) &&
        (!query || (row.dataset.search ?? "").includes(query));

      row.hidden = !matches;
      shown += matches ? 1 : 0;
    }

    if (status) {
      status.textContent = `Showing ${shown} of ${rows.length}`;
    }

    if (empty) {
      empty.hidden = shown > 0;
    }
  }

  search?.addEventListener("input", apply);
  language?.addEventListener("change", apply);
  apply();
}

setupTabs();
setupScrollSpy();
setupTocSheet();
setupTranslationFilter();
