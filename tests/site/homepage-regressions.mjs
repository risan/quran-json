/*
 * Run against an assembled local site:
 *
 *   SITE_BASE_URL=http://127.0.0.1:8789 npm run homepage:browser --prefix site
 *
 * Build and serve the assembled site before running this script. The checks cover
 * the homepage interaction contract; reader behavior remains in tests/reader.
 */

import assert from "node:assert/strict";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

const requestedModule = process.env.SITE_PLAYWRIGHT_MODULE;
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

const base = process.env.SITE_BASE_URL;
if (!base) throw new Error("Set SITE_BASE_URL to an assembled local homepage before running browser regressions.");

const browser = await chromium.launch({ headless: true });

async function open(path, options = {}) {
  const context = await browser.newContext({
    locale: "en-US",
    permissions: ["clipboard-read", "clipboard-write"],
    ...options,
  });
  const page = await context.newPage();
  const errors = [];
  const failed = [];
  page.on("pageerror", (error) => errors.push(String(error)));
  page.on("requestfailed", (request) => failed.push(`${request.method()} ${request.url()}`));
  await page.goto(base + path, { waitUntil: "networkidle", timeout: 45000 });
  return { context, page, errors, failed };
}

try {
  {
    const { context, page, errors, failed } = await open("/", {
      viewport: { width: 1440, height: 1000 },
      colorScheme: "light",
    });
    assert.equal(await page.title(), "quran-json — Quran data, clearly published");
    assert.equal(await page.locator("h1").innerText(), "Al-Quran");
    assert.equal(await page.locator("pre.astro-code .line").count() > 0, true);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    assert.equal(await page.evaluate(() => /generated catalog|build profile|python publisher|withheld edition/i.test(document.body.innerText)), false);
    const copyButton = page.locator("[data-copy]").first();
    const expected = await copyButton.getAttribute("data-copy");
    await copyButton.click();
    await page.waitForFunction(() => document.querySelector("[data-copy]")?.textContent === "Copied");
    assert.equal(await page.evaluate(() => navigator.clipboard.readText()), expected);
    assert.deepEqual({ errors, failed }, { errors: [], failed: [] });
    await context.close();
  }

  {
    const context = await browser.newContext({
      viewport: { width: 1100, height: 900 },
      locale: "en-US",
      permissions: [],
    });
    await context.addInitScript(() => {
      Object.defineProperty(navigator, "clipboard", {
        configurable: true,
        value: { writeText: async () => { throw new DOMException("denied", "NotAllowedError"); } },
      });
    });
    const page = await context.newPage();
    await page.goto(base + "/", { waitUntil: "networkidle", timeout: 45000 });
    const copyButton = page.locator("[data-copy]").first();
    const expected = await copyButton.getAttribute("data-copy");
    await copyButton.click();
    const selection = page.locator(".copy-fallback").first();
    await selection.waitFor({ state: "visible" });
    assert.equal(await selection.inputValue(), expected);
    assert.deepEqual(await selection.evaluate((node) => ({ start: node.selectionStart, end: node.selectionEnd })), {
      start: 0,
      end: expected.length,
    });
    assert.match(await page.locator("[data-copy-status]").first().innerText(), /Ctrl\+C.*⌘C/);
    await context.close();
  }

  {
    const { context, page, errors, failed } = await open("/", {
      viewport: { width: 390, height: 844 },
      colorScheme: "dark",
    });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), true);
    assert.equal(await page.locator(".mobile-nav").count(), 1);
    assert.deepEqual({ errors, failed }, { errors: [], failed: [] });
    await context.close();
  }

  {
    const { context, page, errors, failed } = await open("/#catalogues", {
      viewport: { width: 1100, height: 900 },
    });
    assert.equal(await page.locator("[data-translation-row]:not([hidden])").count(), 12);
    assert.equal(await page.locator("[data-translation-count]").innerText(), "Showing 1–12 of 90 translations");
    assert.equal(await page.locator("[data-translation-page]").innerText(), "Page 1 of 8");

    await page.locator("#translation-search").fill("en-rwwad");
    assert.equal(await page.locator("[data-translation-row]:not([hidden])").count(), 1);
    assert.equal(await page.locator("[data-translation-count]").innerText(), "Showing 1–1 of 1 translations");

    await page.locator("#translation-search").fill("no-such-edition-xyz");
    assert.equal(await page.locator("[data-translation-empty]").isVisible(), true);
    assert.equal(await page.locator("[data-translation-count]").innerText(), "0 translations");

    await page.locator("[data-translation-reset]").click();
    assert.equal(await page.locator("#translation-search").inputValue(), "");
    assert.equal(await page.locator("[data-translation-page]").innerText(), "Page 1 of 8");
    await page.locator("[data-translation-next]").click();
    assert.equal(await page.locator("[data-translation-page]").innerText(), "Page 2 of 8");
    assert.deepEqual({ errors, failed }, { errors: [], failed: [] });
    await context.close();
  }

  {
    const { context, page, errors, failed } = await open("/#catalogues", {
      viewport: { width: 390, height: 844 },
    });
    const firstRow = page.locator("[data-translation-row]:not([hidden])").first();
    const mobileRow = await firstRow.evaluate((row) => {
      const name = row.querySelector(".name-cell");
      const data = row.querySelector(".file-cell a");
      return {
        name: name?.textContent?.trim(),
        data: data?.textContent?.trim(),
        nameVisible: Boolean(name && name.getBoundingClientRect().width),
        dataVisible: Boolean(data && data.getBoundingClientRect().width),
        dataRight: data?.getBoundingClientRect().right,
        viewport: window.innerWidth,
        documentWidth: document.documentElement.scrollWidth,
      };
    });
    assert.equal(mobileRow.nameVisible, true);
    assert.equal(mobileRow.dataVisible, true);
    assert.ok(mobileRow.name);
    assert.ok(mobileRow.data);
    assert.ok(mobileRow.dataRight <= mobileRow.viewport);
    assert.equal(mobileRow.documentWidth, mobileRow.viewport);
    assert.deepEqual({ errors, failed }, { errors: [], failed: [] });
    await context.close();
  }

  {
    const { context, page, errors, failed } = await open("/", {
      viewport: { width: 1100, height: 900 },
      javaScriptEnabled: false,
    });
    assert.equal(await page.locator("#translation-table tbody tr").count(), 90);
    assert.equal(await page.locator("#translation-table tbody tr:not([hidden])").count(), 90);
    assert.equal(await page.locator("#translation-search").count(), 1);
    assert.deepEqual({ errors, failed }, { errors: [], failed: [] });
    await context.close();
  }

  console.log("homepage browser regressions passed");
} finally {
  await browser.close();
}
