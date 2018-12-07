/* eslint import/no-extraneous-dependencies: "off" */
const groupBy = require("lodash.groupby");
const writeJson = require("./write-json");

const groupBySurah = async (quran, surahs) => {
  const groups = groupBy(quran, "surah_number");

  Promise.all(
    surahs.map(surah => {
      const data = {
        ...surah,
        verses: groups[surah.number].map(
          ({ surah_number, verse_number, ...rest }) => ({ // eslint-disable-line
            number: verse_number,
            ...rest
          })
        )
      };

      return writeJson(data, `surahs/${surah.number}.json`);
    })
  );
};

module.exports = groupBySurah;
