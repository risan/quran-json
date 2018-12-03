const readFile = require("./read-file");

const readTanzilText = async path => {
  const text = await readFile(path);

  return text
    .split("\n")
    .filter(line => /^\d{1,3}\|\d{1,3}/.test(line))
    .map(line => {
      const [surahNumber, verseNumber, content] = line.split("|");

      return {
        surah_number: parseInt(surahNumber, 10),
        verse_number: parseInt(verseNumber, 10),
        content: content.trim()
      };
    });
};

module.exports = readTanzilText;
