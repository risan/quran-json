const readTanzilText = require("./read-tanzil-text");
const writeJson = require("./write-json");

const processQuranText = async () => {
  const quranText = await readTanzilText("quran-text/uthmani.txt");

  await writeJson(quranText, "quran/text.json");

  return quranText;
};

module.exports = processQuranText;
