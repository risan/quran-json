import assert from "node:assert/strict";
import fs from "node:fs";

const { chromium } = await import(
  process.env.READER_PLAYWRIGHT_MODULE ?? "playwright",
);

const base = process.env.SITE_BASE ?? "http://127.0.0.1:8776";
const evidenceDir = new URL(".", import.meta.url).pathname;
const browser = await chromium.launch({ headless: true });
const captures = [];

async function capture(name, path, viewport, ready, colorScheme = "light") {
  const context = await browser.newContext({ viewport, locale: "en-US", colorScheme });
  const page = await context.newPage();
  await page.goto(base + path, { waitUntil: "networkidle", timeout: 45000 });
  await page.locator(ready).first().waitFor({ state: "visible", timeout: 30000 });
  const screenshot = `${evidenceDir}/${name}.png`;
  await page.screenshot({ path: screenshot, fullPage: true });
  captures.push({
    name,
    path,
    viewport,
    screenshot,
    title: await page.title(),
    h1: await page.locator("h1").allTextContents(),
    bodyScrollWidth: await page.evaluate(() => document.body.scrollWidth),
    innerWidth: await page.evaluate(() => window.innerWidth),
  });
  await context.close();
}

await capture("assembled-docs-desktop", "/", { width: 1440, height: 1000 }, "h1");
await capture("assembled-docs-mobile", "/", { width: 375, height: 812 }, "h1");
await capture("assembled-reader-home-desktop", "/app/", { width: 1440, height: 1000 }, ".surah-grid");
await capture("assembled-reader-home-mobile", "/app/", { width: 375, height: 812 }, ".surah-grid");
await capture("assembled-reader-dark", "/app/#/2?t=en-rwwad", { width: 1440, height: 1000 }, ".verses", "dark");
await capture("assembled-reader-rtl", "/app/#/2?t=nqo-dayyan", { width: 1440, height: 1000 }, ".verses");

const navigationContext = await browser.newContext({ viewport: { width: 375, height: 812 }, locale: "en-US" });
const navigationPage = await navigationContext.newPage();
await navigationPage.goto(base + "/", { waitUntil: "networkidle", timeout: 45000 });
const mobileMenu = navigationPage.locator(".mobile-nav");
await mobileMenu.locator("summary").click();
await mobileMenu.locator('a[href="#quickstart"]').click();
assert.equal(await navigationPage.evaluate(() => location.hash), "#quickstart");
assert.equal(await navigationPage.locator("#quickstart").isVisible(), true);
assert.equal(await mobileMenu.evaluate((node) => node.open), true);
const navigation = await navigationPage.locator(".mobile-nav nav a").evaluateAll((links) =>
  links.map((link) => ({ text: link.textContent.trim(), href: link.getAttribute("href") })),
);
assert.ok(navigation.some((link) => link.href === "#endpoints"));
await navigationContext.close();

const noJsContext = await browser.newContext({
  viewport: { width: 375, height: 812 },
  locale: "en-US",
  javaScriptEnabled: false,
});
const noJsPage = await noJsContext.newPage();
await noJsPage.goto(base + "/", { waitUntil: "domcontentloaded", timeout: 45000 });
assert.equal(await noJsPage.locator("h1").isVisible(), true);
assert.equal(await noJsPage.locator('a[href="/app/"]').count() > 0, true);
assert.equal(await noJsPage.locator(".desktop-nav a").count() > 0, true);
const noJs = {
  h1: await noJsPage.locator("h1").first().innerText(),
  readerLinks: await noJsPage.locator('a[href="/app/"]').count(),
  primaryNavLinks: await noJsPage.locator(".desktop-nav a").count(),
};
await noJsContext.close();

fs.writeFileSync(
  `${evidenceDir}/assembled-smoke.json`,
  JSON.stringify(
    {
      capturedAt: new Date().toISOString(),
      base,
      browser: "Playwright 1.63.0 / Chromium 153.0.8010.12",
      captures,
      navigation,
      noJs,
      readerRegressionCommand:
        "READER_BASE_URL=http://127.0.0.1:8776 node tests/reader/browser-regressions.mjs",
    },
    null,
    2,
  ),
);

await browser.close();
console.log("assembled site screenshots and no-JS/navigation smoke passed");
