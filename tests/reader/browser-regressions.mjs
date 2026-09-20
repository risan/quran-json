/*
 * Run against an assembled local site:
 *
 *   npm ci --prefix site
 *   npm run reader:browser:install --prefix site
 *   READER_BASE_URL=http://127.0.0.1:8765 npm run reader:browser --prefix site
 *
 * The site must serve the generated data paths and the working /app/ files.
 */

import assert from "node:assert/strict";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

const requestedModule = process.env.READER_PLAYWRIGHT_MODULE;
const importTarget = requestedModule
  ? pathToFileURL(resolve(process.cwd(), requestedModule)).href
  : "playwright";
let playwright;
try {
  playwright = await import(importTarget);
} catch (error) {
  if (requestedModule) throw error;
  playwright = await import(new URL("../../site/node_modules/playwright/index.mjs", import.meta.url));
}
const { chromium } = playwright;

const base = process.env.READER_BASE_URL;
if (!base) {
  throw new Error("Set READER_BASE_URL to an assembled local reader before running browser regressions.");
}

const browser = await chromium.launch({ headless: true });

async function pageAt(path, viewport, options = {}) {
  const context = await browser.newContext({ viewport, locale: "en-US", ...options });
  const page = await context.newPage();
  await page.goto(base + path, { waitUntil: "networkidle", timeout: 45000 });
  return { context, page };
}

try {
  {
    const { context, page } = await pageAt("/app/#/2", { width: 320, height: 568 });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth), 320);
    assert.equal(await page.locator('[data-role="settings"]').getAttribute("aria-label"), "Open reader settings");
    await page.locator('[data-role="settings"]').click();
    assert.equal(await page.locator("#popover").getAttribute("aria-label"), "Reader settings");
    assert.equal(await page.locator("#popover [data-role=\"script\"]:focus").count(), 1);
    await page.locator(".settings-sheet").evaluate((sheet) => {
      sheet.scrollTop = sheet.scrollHeight;
    });
    assert.equal(
      await page.locator('[data-role="size-up"]:visible').evaluate((button) => {
        const popover = document.getElementById("popover").getBoundingClientRect();
        return button.getBoundingClientRect().bottom <= popover.bottom;
      }),
      true,
    );
    const script = page.locator('#popover [data-role="script"]:visible');
    const scriptValues = await script.locator("option").evaluateAll((options) => options.map((option) => option.value));
    if (scriptValues.length > 1) {
      await script.selectOption(scriptValues.at(-1));
      assert.equal(await page.locator('[data-role="settings"]:focus').count(), 1);
      await page.locator('[data-role="settings"]').click();
    }
    const transliteration = page.locator('[data-role="transliteration"]:visible');
    if (await transliteration.count()) {
      await transliteration.click();
      assert.equal(await page.locator('[data-role="settings"]:focus').count(), 1);
      await page.locator('[data-role="settings"]').click();
      assert.equal(await page.locator('[data-role="transliteration"]:visible').getAttribute("aria-pressed"), "true");
    }
    await page.keyboard.press("Escape");
    assert.equal(await page.locator('[data-role="settings"]:focus').count(), 1);
    await context.close();
  }

  {
    const { context, page } = await pageAt("/app/#/2?t=en-rwwad", { width: 1440, height: 1000 });
    await page.locator('[data-role="translation-picker"]:visible').click();
    await page.locator('[data-role="translation-clear"]').click();
    assert.equal(await page.locator('[data-role="translation-picker"]:focus').count(), 1);
    await context.close();
  }

  {
    const { context, page } = await pageAt(
      "/app/#/1?s=indopak&t=en-rwwad&tl=kemenag",
      { width: 1440, height: 1000 },
    );
    assert.equal(await page.locator(".translation-block").count(), 0);
    assert.equal(await page.locator(".transliteration").count(), 0);
    assert.match(await page.locator(".note").innerText(), /safe verse mapping/i);
    await context.close();
  }

  {
    const { context, page } = await pageAt("/app/#/1", { width: 1440, height: 1000 });
    const scripts = await page.locator('[data-role="script"] option').evaluateAll((options) =>
      options.map((option) => option.value),
    );
    assert.equal(scripts.includes("duri"), true, "assembled reader must expose the Duri script");
    await page.goto(base + "/app/#/1?s=duri&t=en-rwwad&tl=kemenag", {
      waitUntil: "networkidle",
      timeout: 45000,
    });
    await page.locator(".translation-block").first().waitFor({ state: "visible" });
    assert.equal(await page.locator(".translation-block").count() > 0, true);
    assert.equal(await page.locator('[data-furniture="bismillah"]').count(), 1);
    assert.equal(await page.locator('[data-furniture="bismillah"]').getAttribute("data-verse"), null);
    const transliterations = await page.evaluate(() =>
      fetch("/transliteration/index.json").then((response) => response.json()),
    );
    if (transliterations.editions.length) {
      assert.equal(await page.locator(".transliteration").count() > 0, true);
    }
    await page.goto(base + "/app/#/2?s=duri&t=en-rwwad&tl=kemenag", {
      waitUntil: "networkidle",
      timeout: 45000,
    });
    await page.locator(".translation-block").first().waitFor({ state: "visible" });
    assert.equal(await page.locator(".translation-block").count() > 0, true);
    await page.goto(base + "/app/#/9:130?s=duri&t=en-rwwad", {
      waitUntil: "networkidle",
      timeout: 45000,
    });
    await page.waitForFunction(() => document.querySelector(".chapter-head")?.innerText.includes("Surah 9"));
    assert.match(await page.locator(".chapter-head").innerText(), /130 verses/);
    assert.equal(await page.locator("#v130").count(), 1);
    assert.equal(await page.locator('[data-furniture="bismillah"]').count(), 0);
    await page.goto(base + "/app/#/2:286?s=duri&t=en-rwwad", {
      waitUntil: "networkidle",
      timeout: 45000,
    });
    await page.waitForFunction(() => document.querySelector(".chapter-head")?.innerText.includes("Surah 2"));
    assert.equal(await page.locator("#v286").count(), 0);
    assert.match(await page.locator("#status").innerText(), /not present/i);
    await page.locator('[data-role="reciter-picker"]').click();
    const scopes = await page.locator('[data-role="reciter"]:visible').evaluateAll((inputs) =>
      inputs.map((input) => input.closest(".pick")?.querySelector(".pick-meta")?.textContent?.trim().split("·")[0]),
    );
    assert.equal(scopes.includes("ayah"), false, "Duri must hide Hafs-indexed per-ayah audio");
    await context.close();
  }

  {
    const { context, page } = await pageAt("/app/#/2?t=en-rwwad", { width: 375, height: 812 });
    assert.equal(await page.locator(".translation-label").count() > 0, true);
    assert.equal(await page.locator(".arabic[dir=\"rtl\"]").count() > 0, true);
    assert.equal(await page.locator(".translation[dir=\"ltr\"]").count() > 0, true);
    await context.close();
  }

  {
    const context = await browser.newContext({ viewport: { width: 375, height: 812 }, locale: "en-US" });
    const page = await context.newPage();
    await page.route("**/translations/*/chapters/**", (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ id: 2, verses: [{ id: 1, translation: "truncated" }] }),
      }),
    );
    await page.goto(base + "/app/#/2?t=en-rwwad", { waitUntil: "networkidle", timeout: 45000 });
    assert.equal(await page.locator(".translation-block").count(), 0);
    assert.equal(await page.locator(".arabic").count() > 0, true);
    assert.match(await page.locator("#status").innerText(), /Arabic is ready/i);
    await context.close();
  }

  {
    let release;
    const delayed = new Promise((resolve) => {
      release = resolve;
    });
    const context = await browser.newContext({ viewport: { width: 375, height: 812 }, locale: "en-US" });
    const page = await context.newPage();
    await page.route("**/text/uthmani/chapters/2.json", async (route) => {
      await delayed;
      await route.continue();
    });
    await page.goto(base + "/app/#/2", { waitUntil: "domcontentloaded", timeout: 45000 });
    await page.waitForTimeout(200);
    await page.evaluate(() => {
      location.hash = "#/";
    });
    await page.locator(".surah-grid").waitFor({ state: "visible", timeout: 30000 });
    release();
    await page.waitForTimeout(1200);
    assert.equal(await page.locator(".surah-grid").count(), 1);
    assert.equal(await page.locator(".verses").count(), 0);
    await context.close();
  }

  {
    const context = await browser.newContext({
      viewport: { width: 1440, height: 1000 },
      locale: "en-US",
      colorScheme: "dark",
    });
    const page = await context.newPage();
    const requests = [];
    page.on("request", (request) => requests.push(request.url()));
    await page.goto(base + "/app/", { waitUntil: "networkidle", timeout: 45000 });
    assert.equal(requests.some((url) => url.includes("/audio/reciters.json")), false);
    assert.equal(requests.some((url) => /\/text\/[^/]+\/quran\.json/.test(url)), false);
    await context.close();
  }

  console.log("reader browser regressions passed");
} finally {
  await browser.close();
}
