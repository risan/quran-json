const writeJson = require("./write-json");

const combineQuranTextAndTranslations = async (quranText, translations) => {
  const languages = Object.keys(translations);
  const multipleLanguages = languages.length > 1;

  const quran = quranText.map(({ content, ...rest }, idx) => {
    let trans = {};

    if (multipleLanguages) {
      languages.forEach(language => {
        trans[`translation_${language}`] = translations[language][idx].content;
      });
    } else {
      trans = {
        translation: translations[languages[0]][idx].content
      };
    }

    return {
      ...rest,
      text: content,
      ...trans
    };
  });

  await writeJson(quran, `quran/${languages.join("-")}.json`);

  return quran;
};

module.exports = combineQuranTextAndTranslations;
