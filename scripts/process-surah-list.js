const readFile = require("./read-file");
const writeJson = require("./write-json");

const processSurahList = async () => {
  const surahsJson = await readFile("surahs.json");

  const surahs = JSON.parse(surahsJson).data.map(surah => ({
    number: surah.number,
    name: surah.name,
    transliteration_en: surah.englishName,
    translation_en: surah.englishNameTranslation,
    total_verses: surah.numberOfAyahs,
    revelation_type: surah.revelationType
  }));

  await writeJson(surahs, "surahs.json");

  return surahs;
};

module.exports = processSurahList;
