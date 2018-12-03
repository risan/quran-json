const readTanzilText = require("./read-tanzil-text");
const writeJson = require("./write-json");

const processTranslations = async () => {
  const [en, id] = await Promise.all([
    readTanzilText("translations/en.sahih.txt"),
    readTanzilText("translations/id.indonesian.txt")
  ]);

  await Promise.all([
    writeJson(en, "translations/en.json"),
    writeJson(id, "translations/id.json")
  ]);

  return { en, id };
};

module.exports = processTranslations;
