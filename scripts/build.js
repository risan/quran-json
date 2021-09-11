const fs = require('fs-extra');
const _ = require('lodash');
const meta = require('../package.json');

const generateQuran = async (lang = null, pretty = false) => {
  const filename = lang ? `quran_${lang}.json` : 'quran.json';

  console.log(`+ Generating ${filename}...`);

  const [chapters, quran, trans] = await Promise.all([
    fs.readJson(`data/chapters/${lang === null || lang === 'transliteration' ? 'en' : lang}.json`),
    fs.readJson('data/quran.json'),
    lang ? fs.readJson(`data/editions/${lang}.json`) : null,
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
          verse[lang === 'transliteration' ? 'transliteration' : 'translation'] = trans[item.id][idx].text;
        }

        return verse;
      }),
    };

    if (lang === null) {
      delete chapter.translation;
    }

    return chapter;
  });

  await fs.outputJson(`dist/${filename}`, data, { spaces: pretty ? 2 : 0 });

  return data;
};

const generateByChapter = async (chapters, lang = null, pretty = false) => {
  await Promise.all(chapters.map(chapter => {
    const filename = lang ? `${lang}/${chapter.id}.json` : `${chapter.id}.json`;

    console.log(`+ Generating chapter: ${filename}...`);

    return fs.outputJson(`dist/chapters/${filename}`, chapter, { spaces: pretty ? 2 : 0 });
  }));

  const indexFilename = lang ? `${lang}/index.json` : 'index.json';

  const index = chapters.map(({ verses, ...chapter }) => {
    const filename = lang ? `${lang}/${chapter.id}.json` : `${chapter.id}.json`;

    return {
      ...chapter,
      link: `https://cdn.jsdelivr.net/npm/quran-json@${meta.version}/dist/chapters/${filename}`,
    };
  });

  await fs.outputJson(`dist/chapters/${indexFilename}`, index, { spaces: pretty ? 2 : 0 });
};

const generateByVerses = async (quran, transQurans, pretty = false) => {
  let id = 1;

  const verses = _.flatten(quran.chapters.map((chapter, chapterIdx) => {
    return chapter.verses.map((verse, verseIdx) => {
      return {
        id: id++,
        number: verse.id,
        text: verse.text,
        translations: _.zipObject(
          transQurans.map(transQuran => transQuran.lang),
          transQurans.map(transQuran => transQuran.chapters[chapterIdx].verses[verseIdx].translation)
        ),
        transliteration: verse.transliteration,
        chapter: {
          id: chapter.id,
          name: chapter.name,
          transliteration: chapter.transliteration,
          translations: _.zipObject(
            transQurans.map(transQuran => transQuran.lang),
            transQurans.map(transQuran => transQuran.chapters[chapterIdx].translation)
          ),
          type: chapter.type,
        },
      };
    });
  }));

  const chunkVerses = _.chunk(verses, 100);

  for (let i = 0; i < chunkVerses.length; i++) {
    await Promise.all(chunkVerses[i].map(verse => {
      const filename = `${verse.id}.json`;

      console.log(`+ Generating verse: ${filename}...`);

      return fs.outputJson(`dist/verses/${filename}`, verse, { spaces: pretty ? 2 : 0 });
    }));
  }
};

(async () => {
  const args = process.argv.slice(2);

  const pretty = args.length > 0 && args[0] === '--pretty';

  await fs.emptyDir('dist');

  const langCodes = [null, 'bn', 'en', 'es', 'fr', 'id', 'ru', 'sv', 'tr', 'ur', 'zh'];

  const [transliterationChapters, ...chaptersList] = await Promise.all(
    ['transliteration', ...langCodes].map(lang => generateQuran(lang, pretty))
  );

  const qurans = chaptersList.map((chapters, idx) => {
    return {
      lang: langCodes[idx],
      chapters: chapters.map((chapter, chapterIdx) => {
        return {
          ...chapter,
          verses: chapter.verses.map((verse, verseIdx) => {
            return {
              ...verse,
              transliteration: transliterationChapters[chapterIdx].verses[verseIdx].transliteration,
            };
          }),
        };
      }),
    };
  });

  await Promise.all(qurans.map(quran => generateByChapter(quran.chapters, quran.lang, pretty)));

  await generateByVerses(qurans[0], qurans.slice(2), pretty);

  console.log('✓ Done');
})();
