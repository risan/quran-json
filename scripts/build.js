const fs = require('fs-extra');
const _ = require('lodash');
const meta = require('../package.json');

const generateQuran = async (lang = null) => {
  const filename = lang ? `quran_${lang}.json` : 'quran.json';

  console.log(`+ Generating ${filename}...`);

  const [chapters, quran, trans] = await Promise.all([
    fs.readJson(`data/chapters/${lang ? lang : 'en'}.json`),
    fs.readJson('data/quran.json'),
    lang ? fs.readJson(`data/translations/${lang}.json`) : null,
  ]);

  const data = chapters.map(item => {
    const chapter = {
      id: item.id,
      name: item.name,
      transliteration: item.transliteration,
      translation: item.translation,
      type: item.type,
      total_verses: item.total_verses,
      verses: quran[item.id].map((i, idx) => {
        const verse = {
          id: i.verse,
          text: i.text,
        };

        if (trans) {
          verse.translation = trans[item.id][idx].text;
        }

        return verse;
      }),
    };

    if (lang === null) {
      delete chapter.translation;
    }

    return chapter;
  });

  await fs.outputJson(`dist/${filename}`, data);

  return data;
};

const generateByChapter = async (chapters, lang = null) => {
  await Promise.all(chapters.map(chapter => {
    const filename = lang ? `${lang}/${chapter.id}.json` : `${chapter.id}.json`;

    console.log(`+ Generating chapter: ${filename}...`);

    return fs.outputJson(`dist/chapters/${filename}`, chapter);
  }));

  const indexFilename = lang ? `${lang}/index.json` : 'index.json';

  const index = chapters.map(({ verses, ...chapter }) => {
    const filename = lang ? `${lang}/${chapter.id}.json` : `${chapter.id}.json`;

    return {
      ...chapter,
      link: `https://cdn.jsdelivr.net/npm/quran-json@${meta.version}/dist/chapters/${filename}`,
    };
  });

  await fs.outputJson(`dist/chapters/${indexFilename}`, index);
};

const generateByVerses = async (enChapters, idChapters) => {
  let id = 1;

  const verses = _.flatten(enChapters.map((enChapter, chapterIdx) => {
    const idChapter = idChapters[chapterIdx];

    return enChapter.verses.map((enVerse, verseIdx) => {
      return {
        id: id++,
        number: enVerse.id,
        text: enVerse.text,
        translation: {
          en: enVerse.translation,
          id: idChapter.verses[verseIdx].translation,
        },
        chapter: {
          id: enChapter.id,
          name: enChapter.name,
          transliteration: enChapter.transliteration,
          translation: {
            en: enChapter.translation,
            id: idChapter.translation,
          },
          type: enChapter.type,
        },
      };
    });
  }));

  const chunkVerses = _.chunk(verses, 100);

  for (let i = 0; i < chunkVerses.length; i++) {
    await Promise.all(chunkVerses[i].map(verse => {
      const filename = `${verse.id}.json`;

      console.log(`+ Generating verse: ${filename}...`);

      return fs.outputJson(`dist/verses/${filename}`, verse);
    }));
  }
};

(async () => {
  await fs.emptyDir('dist');

  const langCodes = [null, 'en', 'id'];

  const results = await Promise.all(langCodes.map(lang => generateQuran(lang)));

  await Promise.all(results.map((chapters, idx) => generateByChapter(chapters, langCodes[idx])));

  await generateByVerses(results[1], results[2]);

  console.log('✓ Done');
})();
