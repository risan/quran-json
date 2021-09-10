# Quran JSON

[![Latest Version](https://badgen.net/npm/v/quran-json)](https://www.npmjs.com/package/quran-json)

Quran text and translations in JSON format.

## CDN

Check out the [`/dist`](https://github.com/risan/quran-json/tree/master/dist) to see all available JSON files. The JSON files are also available through [JSDELIVR](https://www.jsdelivr.com/package/npm/quran-json?path=surahs) CDN.

### Get The Entire Quran Text & Translation

This project is using the Uthmani Quran text from the [The Noble Qur'an Encyclopedia](https://quranenc.com/en/home). The translations are available in two languages: English & Indonesia. The English translation is authored by Umm Muhammad (Saheeh International). While the Indonesian translation is made by Indonesian Islamic Affairs Ministry.

- Quran text only: [cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/quran.json](https://cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/quran.json)
- With English translation: [cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/quran_en.json](https://cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/quran_en.json)
- With Indonesian translation: [cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/quran_id.json](https://cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/quran_id.json)

### Get the List of Chapters

* Arabic only: [cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/chapters/index.json](https://cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/chapters/index.json)
* With English translation: [cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/chapters/en/index.json](https://cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/chapters/en/index.json)
* With Indonesian translation: [cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/chapters/id/index.json](https://cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/chapters/id/index.json)

### Get a Chapter

You can get a single chapter (surah) by providing its `chapterNumber` (`1-114`).

```
https://cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/chapters/{chapterNumber}.json
https://cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/chapters/en/{chapterNumber}.json
https://cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/chapters/id/{chapterNumber}.json
```

For example:

* *Al-Fatihah* Quran text only: [cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/chapters/1.json](https://cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/chapters/1.json)
* *Al-Rahman* with English translation: [cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/chapters/en/55.json](https://cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/chapters/en/55.json)
* *Al-Ikhlas* with Indonesian translation: [cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/chapters/en/112.json](https://cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/chapters/en/112.json)

### Get a Verse

You can get a single verse (ayah) by providing its `verseNumber` (`1-6236`).

```
https://cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/verses/{verseNumber}.json
```

Unlike the rest of the JSON files, a single verse JSON file contains both English & Indonesian translations.

For example:

* *Al-Fatihah* verse #1: [cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/verses/1.json](https://cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/verses/1.json)
* *An-Nas* verse #6: [cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/verses/6236.json](https://cdn.jsdelivr.net/npm/quran-json@3.0.0/dist/verses/6236.json)

## Generate the JSON

If you want to generate the JSON files by yourself:

### 1. Clone the Repository

Clone this repository to your local computer:

```bash
$ git clone git@github.com:risan/quran-json.git
```

### 2. Install the Dependencies

`CD` into the project directory and install the dependencies:

```bash
# Go to the project directory
$ cd quran-json

# Install the dependencies
$ npm install
```

### 3. Generate the JSON Files

Run the following command to generate the JSON files:

```bash
$ npm run build
```

## Data Source

* The Uthmani Quran text is from [The Noble Qur'an Encyclopedia](https://quranenc.com/en/home).
* The English translation is authored by Umm Muhammad (Saheeh International) and it's sourced from [tanzil.net](https://tanzil.net/trans/).
* The Indonesian translation is authored by Indonesian Islamic Affairs Ministry and it's sourced from [The Noble Qur'an Encyclopedia](https://quranenc.com/en/browse/indonesian_affairs).

## License

[CC-BY-SA 4.0](https://github.com/risan/quran-json/blob/master/LICENSE.txt) · [Risan Bagja Pradana](https://risanb.com)
