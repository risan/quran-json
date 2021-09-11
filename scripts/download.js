const fs = require('fs-extra');
const axios = require('axios');
const _ = require('lodash');

const downloadChapterList = async (langCode) => {
  const file = `data/chapters/${langCode}.json`;
  const exists = await fs.pathExists(file);

  if (exists) {
    return;
  }

  console.log(`+ Downloading chapter list in [${langCode}]...`);

  const res = await axios.get('https://api.quran.com/api/v4/chapters', {
    params: {
      language: langCode,
    },
  });

  const chapters = res.data.chapters.map(chapter => {
    return {
      id: chapter.id,
      name: chapter.name_arabic,
      transliteration: chapter.name_simple,
      translation: chapter.translated_name.name,
      type: chapter.revelation_place === 'makkah' ? 'meccan' : 'medinan',
      total_verses: chapter.verses_count,
    };
  });

  await fs.outputJson(file, chapters, { spaces: 2 });
};

const downloadEdition = async (edition, file) => {
  const exists = await fs.pathExists(file);

  if (exists) {
    return;
  }

  console.log(`+ Downloading Quran edition [${edition}]...`);

  const res = await axios.get(`https://cdn.jsdelivr.net/gh/fawazahmed0/quran-api@1/editions/${edition}.json`);

  const verses = _.groupBy(res.data.quran, 'chapter');

  await fs.outputJson(file, verses, { spaces: 2 });
};

(async () => {
  const args = process.argv.slice(2);

  if (args.length > 0 && args[0] === '--clean') {
    await fs.emptyDir('data');
  }

  const langCodes = ['bn', 'en', 'es', 'fr', 'id', 'ru', 'sv', 'tr', 'ur', 'zh'];

  await Promise.all(langCodes.map(langCode => downloadChapterList(langCode)));

  await Promise.all([
    // Bengali, Author: Muhiuddin Khan, Source: https://tanzil.net
    downloadEdition('ben-muhiuddinkhan', 'data/translations/bn.json'),
    // Quran Uthmani, Source: https://quranenc.com
    downloadEdition('ara-quranuthmanienc', 'data/quran.json'),
    // English, Author: Umm Muhammad (Saheeh International), Source: https://tanzil.net
    downloadEdition('eng-ummmuhammad', 'data/translations/en.json'),
    // Spanish, Author: Muhammad Isa García, Source: https://tanzil.net
    downloadEdition('spa-muhammadisagarc', 'data/translations/es.json'),
    // French, Author: Muhammad Hamidullah, Source: https://tanzil.net
    downloadEdition('fra-muhammadhamidul', 'data/translations/fr.json'),
    // Indonesian, Author: Indonesian Islamic Affairs Ministry, Source: https://quranenc.com/en/browse/indonesian_affairs/
    downloadEdition('ind-indonesianislam', 'data/translations/id.json'),
    // Russian, Author: Elmir Kuliev, Source: https://tanzil.net
    downloadEdition('rus-elmirkuliev', 'data/translations/ru.json'),
    // Swedish, Author: Knut Bernstrom, Source: https://tanzil.net
    downloadEdition('swe-knutbernstrom', 'data/translations/sv.json'),
    // Turkish, Author: Directorate of Religious Affairs, Source: https://tanzil.net
    downloadEdition('tur-diyanetisleri', 'data/translations/tr.json'),
    // Urdu, Author: Abul A'la Maududi, Source: https://tanzil.net
    downloadEdition('urd-abulaalamaududi', 'data/translations/ur.json'),
    // Chinese (simplified), Author: Muhammad Makin, Source: https://quranenc.com/en/browse/chinese_makin
    downloadEdition('zho-muhammadmakin', 'data/translations/zh.json'),
  ]);

  await downloadEdition('ara-quranuthmanienc', 'data/quran.json');

  console.log('✓ Done');
})();