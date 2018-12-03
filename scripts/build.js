#!/usr/bin/env node
/* eslint no-console: "off" */
const cleanJsonDir = require("./clean-json-dir");
const processSurahList = require("./process-surah-list");
const processQuranText = require("./process-quran-text");
const processTranslations = require("./process-translations");
const combineQuranTextAndTranslations = require("./combine-quran-text-and-translations");
const groupBySurah = require("./group-by-surah");

(async () => {
  try {
    console.log("Cleaning JSON dir...");
    await cleanJsonDir();

    console.log("Processing surah list...");
    const surahs = await processSurahList();

    console.log("Processing quran text...");
    const quranText = await processQuranText();

    console.log("Processing translations...");
    const { en, id } = await processTranslations();

    console.log("Combining quran text and translations...");
    const [, , quranEnId] = await Promise.all([
      combineQuranTextAndTranslations(quranText, { en }),
      combineQuranTextAndTranslations(quranText, { id }),
      combineQuranTextAndTranslations(quranText, { en, id })
    ]);

    console.log("Grouping by surah...");
    await groupBySurah(quranEnId, surahs);
  } catch (error) {
    console.error(error.message);
  }
})();
