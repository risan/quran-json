/* global expect:false, test:false */
const fs = require("fs");
const path = require("path");
const range = require("lodash.range");
const util = require("util");

const access = util.promisify(fs.access);

const jsonPath = p => path.resolve(__dirname, `../json`, p);

const isJsonExists = async p => {
  await access(jsonPath(p), fs.constants.F_OK);

  return true;
};

const allJsonPairExists = async files => {
  const pairs = [
    ...files,
    ...files.map(file => file.replace(/\.json$/i, ".pretty.json"))
  ];

  const res = await Promise.all(pairs.map(file => isJsonExists(file)));

  return !res.includes(false);
};

test("it generate surah json files", async () => {
  const res = await allJsonPairExists(["surahs.json"]);
  expect(res).toBe(true);
});

test("it generate quran json files", async () => {
  const res = await allJsonPairExists([
    "quran/en-id.json",
    "quran/en.json",
    "quran/id.json",
    "quran/text.json"
  ]);

  expect(res).toBe(true);
});

test("it generate surah json files", async () => {
  const res = await allJsonPairExists(
    range(1, 115).map(num => `surahs/${num}.json`)
  );

  expect(res).toBe(true);
});

test("it generate translations json files", async () => {
  const res = await allJsonPairExists([
    "translations/en.json",
    "translations/id.json"
  ]);

  expect(res).toBe(true);
});
