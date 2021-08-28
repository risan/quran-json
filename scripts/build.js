const fs = require('fs-extra');

const generateSurahs = async (sourceFile, {
  prefix = '',
  formatter = surah => surah,
} = {}) => {
  const { data } = await fs.readJson(sourceFile);

  await Promise.all(data.surahs.map(surah => {
    return fs.outputJson(`surahs/${surah.number}${prefix ? `.${prefix}` : ''}.json`, formatter({
      number: surah.number,
      name: surah.name.substr(8),
      transliteration: surah.englishName,
      translation: surah.englishNameTranslation,
      revelation_type: surah.revelationType,
      total_verses: surah.ayahs.length,
      verses: surah.ayahs.map(verse => ({
        number: verse.numberInSurah,
        text: verse.text,
      })),
    }));
  }));
};

(async () => {
  try {
    await fs.emptyDir('surahs');

    const { data: surahsId } = await fs.readJson('data/surahs.id.kemenag.json');

    await Promise.all([
      generateSurahs('data/quran-simple.json'),
      generateSurahs('data/en.sahih.json', { prefix: 'en' }),
      generateSurahs('data/es.asad.json', { prefix: 'es' }),
      generateSurahs('data/zh.mazhonggang.json', { prefix: 'zh' }),
      generateSurahs('data/id.indonesian.json', {
        prefix: 'id',
        formatter: surah => {
          surah.transliteration = surahsId[surah.number - 1].surat_name;
          surah.translation = surahsId[surah.number - 1].surat_terjemahan;
          surah.revelation_type = surah.revelation_type === 'Meccan' ? 'Makkiyah' : 'Madaniyah';

          return surah;
        },
      }),
    ]);

    const { data } = await fs.readJson('data/quran-simple.json');

    await fs.outputJson('surahs/index.json', data.surahs.map(surah => ({
      number: surah.number,
      name: surah.name.substr(8),
      transliteration: surah.englishName,
      translation: surah.englishNameTranslation,
      revelation_type: surah.revelationType,
      total_verses: surah.ayahs.length,
    })));
  } catch (error) {
    console.error(error.message);
  }
})();
