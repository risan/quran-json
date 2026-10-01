/**
 * Screenshots of the assembled site, for design review. Not part of CI.
 *
 *   npm run site -- --no-cdn
 *   node site/tests/e2e/screenshots.mjs   (run from the repository root; OUT_DIR optional)
 */
import { mkdir } from "node:fs/promises";
import { chromium } from "playwright";
import { serve } from "./serve.mjs";

const { server, url: base } = await serve(".build/assembled");
const out = process.env.OUT_DIR ?? ".works/quran-overhaul/site-evidence";

await mkdir(out, { recursive: true });

const browser = await chromium.launch();
const sizes = {
  desktop: { width: 1440, height: 900 },
  mobile: { width: 390, height: 844 },
};

async function theme(page, mode) {
  await page.addInitScript((value) => localStorage.setItem("quran-json:theme", value), mode);
}

for (const [device, viewport] of Object.entries(sizes)) {
  for (const mode of ["light", "dark"]) {
    const context = await browser.newContext({ viewport, deviceScaleFactor: 1 });
    const page = await context.newPage();

    await theme(page, mode);

    await page.goto(`${base}/`, { waitUntil: "networkidle" });
    await page.screenshot({ path: `${out}/docs-${device}-${mode}.png` });
    await page.screenshot({ path: `${out}/docs-${device}-${mode}-full.png`, fullPage: true });

    await page.goto(`${base}/app/#/2:255`, { waitUntil: "networkidle" });
    await page.waitForSelector("#v255");
    await page.waitForTimeout(400);
    await page.screenshot({ path: `${out}/reader-${device}-${mode}.png` });

    if (mode === "light" || device === "desktop") {
      await page.getByRole("button", { name: "Settings" }).click();
      await page.waitForTimeout(400);
      await page.screenshot({ path: `${out}/reader-${device}-${mode}-settings.png` });
      await page.keyboard.press("Escape");
      await page.waitForTimeout(300);

      await page.keyboard.press("Control+k");
      await page.keyboard.type("baq");
      await page.waitForTimeout(300);
      await page.screenshot({ path: `${out}/reader-${device}-${mode}-palette.png` });
      await page.keyboard.press("Escape");
    }

    if (device === "mobile" && mode === "light") {
      await page.getByRole("button", { name: "Open the surah list" }).click();
      await page.waitForTimeout(400);
      await page.screenshot({ path: `${out}/reader-mobile-light-surahs.png` });
    }

    const overflow = await page.evaluate(
      () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
    );

    console.log(`${device} ${mode}: horizontal overflow ${overflow}px`);
    await context.close();
  }
}

await browser.close();
server.close();
