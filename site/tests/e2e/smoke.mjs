/**
 * Browser smoke test of the assembled site. Not part of CI.
 *
 *   npm run site -- --no-cdn
 *   node site/tests/e2e/smoke.mjs        (run from the repository root)
 */
import assert from "node:assert/strict";
import { chromium } from "playwright";
import { serve } from "./serve.mjs";

const { server, url } = await serve(".build/assembled");
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
const errors = [];

page.on("pageerror", (error) => errors.push(error.message));

// Docs
await page.goto(`${url}/`);
assert.equal(await page.locator("h1").innerText(), "Quran JSON");
await page.getByRole("tab", { name: "Python" }).click();
assert.ok(await page.getByRole("tabpanel", { name: "Python" }).isVisible());
await page.locator("#translation-search").fill("indonesian");
assert.ok((await page.locator("[data-translation-row]:not([hidden])").count()) >= 1);

// Reader: deep link
await page.goto(`${url}/app/#/2:255`);
await page.waitForSelector("#v255");
assert.match(await page.locator("h1").innerText(), /Al-Baqara/);
assert.ok((await page.locator("#v255").getAttribute("class")).includes("border-l-brand"));

// Command palette jumps to a verse
await page.keyboard.press("Control+k");
await page.keyboard.type("36:1");
await page.keyboard.press("Enter");
await page.waitForSelector("#v1");
assert.match(page.url(), /#\/36:1$/);

// Switch script from the toolbar to Warsh
await page.getByRole("combobox", { name: "Script" }).click();
await page.getByRole("option", { name: "Warsh", exact: true }).click();
await page.waitForFunction(() => document.querySelector("#v1 .arabic")?.textContent?.length > 0);

// Per-ayah audio: a Hafs script requests an EveryAyah file
await page.getByRole("combobox", { name: "Script" }).click();
await page.getByRole("option", { name: "Uthmani", exact: true }).click();
const request = page.waitForRequest((req) => req.url().includes("everyayah.com"), {
  timeout: 15000,
});

await page.getByRole("button", { name: "Play 36:1", exact: true }).click();
const audioRequest = await request;

assert.match(audioRequest.url(), /\/036001\.mp3$/);
await page.getByRole("region", { name: "Audio player" }).waitFor();

assert.deepEqual(errors, []);
await browser.close();
server.close();
console.log("smoke ok");
