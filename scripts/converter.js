const fs = require('fs');
const path = require('path');
const util = require('util');
const rimraf = require('rimraf');
const Reader = require('./reader');

const writeFile = util.promisify(fs.writeFile);
const dataDir = path.resolve(`${__dirname}/../tanzil`);
const jsonDir = path.resolve(`${__dirname}/../json`);
const reader = new Reader({ dataDir });

const cleanJsonDir = async () => new Promise((resolve, reject) => (
  rimraf(`${jsonDir}/*`, err => {
    if (err) {
      return reject(err);
    }

    resolve(true);
  })
));

const writeJsonFile = async (path, data, pretty = true) => writeFile(
  path, JSON.stringify(data, null, pretty ? 2 : null), 'utf8'
);

const writeToJson = async (name, data) => Promise.all([
  writeJsonFile(path.join(jsonDir, `${name}-pretty.json`), data),
  writeJsonFile(path.join(jsonDir, `${name}.json`), data, false),
]);

const combineQuranWithTranslation = async (name, quran, trans) => writeToJson(
  name,
  quran.map((verse, idx) => ({
    ...verse,
    translation: trans[idx].content
  }))
);

const convert = async () => {
  const [surahs, quran, transEn, transId] = await Promise.all([
    reader.readSurahs(),
    reader.readQuranFile('uthmani'),
    reader.readTranslationFile('en.sahih'),
    reader.readTranslationFile('id.indonesian'),
    cleanJsonDir()
  ]);

  fs.mkdirSync(path.join(jsonDir, 'translations'));
  fs.mkdirSync(path.join(jsonDir, 'surahs'));
  fs.mkdirSync(path.join(jsonDir, 'surahs-pretty'));

  Promise.all([
    writeToJson('surahs', surahs),
    writeToJson('quran', quran),
    writeToJson('translations/en', transEn),
    writeToJson('translations/id', transId),
    combineQuranWithTranslation('quran-en', quran, transEn),
    combineQuranWithTranslation('quran-id', quran, transId)
  ]);

  const quranEnId = quran.map((verse, idx) => ({
    ...verse,
    translation_en: transEn[idx].content,
    translation_id: transId[idx].content
  }));

  await writeToJson('quran-en-id', quranEnId);

  const groupedBySurah = quranEnId.reduce((grouped, { surah_number, verse_number, content, translation_en, translation_id }) => {
    const surahIdx = surah_number - 1;

    if (grouped[surahIdx] === undefined) {
      grouped[surahIdx] = {
        ...surahs[surahIdx],
        verses: []
      };
    }

    grouped[surahIdx].verses[verse_number - 1] = {
      number: verse_number,
      content,
      translation_en,
      translation_id
    };

    return grouped;
  }, []);

  const writeSurahs = groupedBySurah.map(surah => writeJsonFile(
    path.join(jsonDir, `surahs/${surah.number}.json`), surah, false
  ));

  const writeSurahsPretty = groupedBySurah.map(surah => writeJsonFile(
    path.join(jsonDir, `surahs-pretty/${surah.number}.json`), surah
  ));

  await Promise.all([
    ...writeSurahs,
    ...writeSurahsPretty
  ]);

  console.log('✅ Done...');
}

convert();
