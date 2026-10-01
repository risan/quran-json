import { mkdirSync, mkdtempSync, realpathSync, rmSync, symlinkSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { afterAll, beforeAll, describe, expect, it } from "vitest";

import { resolveDataFile } from "../src/dev-data.mjs";

let work: string;
let root: string;

beforeAll(() => {
  work = realpathSync(mkdtempSync(join(tmpdir(), "dev-data-")));
  root = join(work, "data");
  mkdirSync(join(root, "text"), { recursive: true });
  mkdirSync(join(work, "data-private"));
  writeFileSync(join(root, "text", "quran.json"), "{}");
  writeFileSync(join(root, "%2e%2e"), "literal name");
  writeFileSync(join(work, "data-private", ".env"), "SECRET=1");
  writeFileSync(join(work, "outside.json"), "{}");
  symlinkSync(join(work, "outside.json"), join(root, "text", "link.json"));
  symlinkSync(join(work, "data-private"), join(root, "text", "dir-link"));
});

afterAll(() => rmSync(work, { recursive: true, force: true }));

describe("dev data guard", () => {
  it("serves a regular file inside the root", async () => {
    expect(await resolveDataFile(root, "/text/quran.json")).toBe(join(root, "text", "quran.json"));
  });

  it("rejects plain traversal", async () => {
    expect(await resolveDataFile(root, "/text/../../data-private/.env")).toBeNull();
  });

  it("rejects encoded traversal into a sibling whose name starts with the root", async () => {
    expect(await resolveDataFile(root, "/text/%2e%2e/%2e%2e/data-private/.env")).toBeNull();
  });

  it("decodes only once", async () => {
    expect(await resolveDataFile(root, "/text/%252e%252e/%252e%252e/data-private/.env")).toBeNull();
    expect(await resolveDataFile(root, "/%252e%252e")).toBe(join(root, "%2e%2e"));
  });

  it("rejects backslashes and NUL", async () => {
    expect(await resolveDataFile(root, "/text/..\\..\\data-private\\.env")).toBeNull();
    expect(await resolveDataFile(root, "/text/quran.json%00")).toBeNull();
  });

  it("rejects a symlink that leaves the root", async () => {
    expect(await resolveDataFile(root, "/text/link.json")).toBeNull();
    expect(await resolveDataFile(root, "/text/dir-link/.env")).toBeNull();
  });

  it("rejects directories, missing files and malformed escapes", async () => {
    expect(await resolveDataFile(root, "/text")).toBeNull();
    expect(await resolveDataFile(root, "/text/none.json")).toBeNull();
    expect(await resolveDataFile(root, "/%E0%A4%A")).toBeNull();
  });
});
