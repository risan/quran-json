# Quran JSON

[![Latest Version](https://badgen.net/npm/v/quran-json)](https://www.npmjs.com/package/quran-json)

Quran text and translations in JSON format. Both Quran text and the translations are provided by [Al Quran Cloud](https://alquran.cloud/).

## CDN

Check the [surahs directory](https://github.com/risan/quran-json/tree/master/surahs) to see all available JSON files. The JSON files are also available through [UNPKG](https://unpkg.com/) CDN.

### List of Surahs

* List of surahs: [unpkg.com/quran-json@latest/surahs/index.json](https://unpkg.com/quran-json@latest/surahs/index.json)

### Quran Text

You can get the Quran text based on the surah number. Where the `surahNumber` is an integer from `1` (Al-Faatiha) all the way to `144` (An-Naas).

```
https://unpkg.com/quran-json@latest/surahs/{surahNumber}.json
```

For example:

* Al-Faatiha: [unpkg.com/quran-json@latest/surahs/1.json](https://unpkg.com/quran-json@latest/surahs/1.json)
* Ar-Rahmaan: [unpkg.com/quran-json@latest/surahs/55.json](https://unpkg.com/quran-json@latest/surahs/55.json)
* Al-Ikhlaas: [unpkg.com/quran-json@latest/surahs/112.json](https://unpkg.com/quran-json@latest/surahs/112.json)

### Translation

There are several translations available:

1. Chinese: [unpkg.com/quran-json@latest/surahs/112.zh.json](https://unpkg.com/quran-json@latest/surahs/112.zh.json)
2. English: [unpkg.com/quran-json@latest/surahs/112.en.json](https://unpkg.com/quran-json@latest/surahs/112.en.json)
3. Indonesian: [unpkg.com/quran-json@latest/surahs/112.id.json](https://unpkg.com/quran-json@latest/surahs/112.id.json)
4. Spanish: [unpkg.com/quran-json@latest/surahs/112.es.json](https://unpkg.com/quran-json@latest/surahs/112.es.json)

## Generate the JSON

If you want to generate the JSON by yourself:

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

## License

[CC-BY-SA 4.0](https://github.com/risan/quran-json/blob/master/LICENSE.txt) · [Risan Bagja Pradana](https://risanb.com)

## Legal

This repository is in no way affiliated with, authorized, maintained, sponsored or endorsed by [Al Quran Cloud](https://alquran.cloud/) or any of its affiliates or subsidiaries. This is an independent and unofficial library.

By using this library you agree to Al Quran Cloud's [terms and conditions](https://alquran.cloud/terms-and-conditions).
