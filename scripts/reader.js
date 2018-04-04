const fs = require('fs');
const path = require('path');
const util = require('util');

const readFile = util.promisify(fs.readFile);

class Reader {
  constructor({ dataDir }) {
    this.dataDir = dataDir;
  }

  getDataPath(...paths) {
    return path.join(this.dataDir, ...paths);
  }

  async readSurahs() {
    const surahs = await readFile(this.getDataPath('/surahs.json'), 'utf8');

    return JSON.parse(surahs).data.map(surah => ({
      number: surah.number,
      name: surah.name,
      transliteration_en: surah.englishName,
      translation_en: surah.englishNameTranslation,
      total_verses: surah.numberOfAyahs,
      revelation_type: surah.revelationType
    }));
  }

  async readQuranFile(name) {
    return await this.readTanzilFile(
      this.getDataPath(`quran-texts/${name}.txt`)
    );
  }

  async readTranslationFile(name) {
    return await this.readTanzilFile(
      this.getDataPath(`translations/${name}.txt`)
    );
  }

  async readTanzilFile(path) {
    const data = await readFile(path, 'utf8');

    return data.split('\n').filter(line =>
      Boolean(line.trim()) && line[0] !== '#'
    ).map(line => {
      const [surahNumber, verseNumber, content] = line.split('|');

      return {
        surah_number: parseInt(surahNumber, 10),
        verse_number: parseInt(verseNumber),
        content: content.trim()
      };
    });
  }
}

module.exports = Reader;
