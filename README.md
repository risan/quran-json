# Quran JSON

Quran text and translations in JSON format. Both Quran text and the translations are provided by [tanzil.net](http://tanzil.net).

## Quran JSON CDN

Check the [json directory](https://github.com/risan/quran-json/tree/master/json) to see all available JSON files. The JSON files are also available through [UNPKG](https://unpkg.com/) CDN.

### List of Surah

* List of surah: [unpkg.com/quran-json@latest/json/surahs.json](https://unpkg.com/quran-json@latest/json/surahs.json)

### Quran Text

* Quran Text: [unpkg.com/quran-json@latest/json/quran/text.json](https://unpkg.com/quran-json@latest/json/quran/text.json)

### Translations

* English translation (Saheeh International): [unpkg.com/quran-json@latest/json/translations/en.json](https://unpkg.com/quran-json@latest/json/translations/en.json)
* Indonesian translation (Indonesian Ministry of Religious Affairs): [unpkg.com/quran-json@latest/json/translations/id.json](https://unpkg.com/quran-json@latest/json/translations/id.json)

### Quran Text with Translations

* Quran text with English translation (Saheeh International): [unpkg.com/quran-json@latest/json/quran/en.json](https://unpkg.com/quran-json@latest/json/quran/en.json)
* Quran text with Indonesian translation (Indonesian Ministry of Religious Affairs): [unpkg.com/quran-json@latest/json/quran/id.json](https://unpkg.com/quran-json@latest/json/quran/id.json)
* Quran text with English and Indonesian translations: [unpkg.com/quran-json@latest/json/quran/en-id.json](https://unpkg.com/quran-json@latest/json/quran/en-id.json)

### Quran Text with Translations per Surah

Each Surah is available under the following URL format:

```
https://unpkg.com/quran-json@latest/json/surahs/{surahNumber}.json
```

`surahNumber` is an integer from `1` (Al-Faatiha) to `144` (An-Naas). For example:

* Al-Faatiha: [unpkg.com/quran-json@latest/json/surahs/1.json](https://unpkg.com/quran-json@latest/json/surahs/1.json)
* Ar-Rahmaan: [unpkg.com/quran-json@latest/json/surahs/55.json](https://unpkg.com/quran-json@latest/json/surahs/55.json)
* Al-Aadiyaat: [unpkg.com/quran-json@latest/json/surahs/100.json](https://unpkg.com/quran-json@latest/json/surahs/100.json)

### Pretty JSON Version

All of the JSON files above are the minified version. Each one of them also has the pretty version with spacing. For example:

* List of surah: [unpkg.com/quran-json@latest/json/surahs.pretty.json](https://unpkg.com/quran-json@latest/json/surahs.pretty.json)
* Quran Text: [unpkg.com/quran-json@latest/json/quran/text.pretty.json](https://unpkg.com/quran-json@latest/json/quran/text.pretty.json)
* Quran text with English and Indonesian translations: [unpkg.com/quran-json@latest/json/quran/en-id.pretty.json](https://unpkg.com/quran-json@latest/json/quran/en-id.pretty.json)
* Al-Faatiha: [unpkg.com/quran-json@latest/json/surahs/1.pretty.json](https://unpkg.com/quran-json@latest/json/surahs/1.pretty.json)

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

# Or if you use Yarn
$ yarn
```

### 3. Generate the JSON Files

Run the following command to generate the JSON files:

```bash
$ npm run build

# Or if you use Yarn
$ yarn build
```

## Related

* [tanzil-downloader](https://github.com/risan/tanzil-downloader)

## License

CC-BY-SA 4.0 · [Risan Bagja Pradana](https://bagja.net)

## Legal

This repository is in no way affiliated with, authorized, maintained, sponsored or endorsed by [Tanzil.net](http://tanzil.net) or any of its affiliates or subsidiaries. This is an independent and unofficial library.

By using this Quran text from [Tanzil.net](http://tanzil.net) you agree to Tanzil's terms of use:

```
#  - This quran text is distributed under the terms of a
#    Creative Commons Attribution 3.0 License.
#
#  - Permission is granted to copy and distribute verbatim copies
#    of this text, but CHANGING IT IS NOT ALLOWED.
#
#  - This quran text can be used in any website or application,
#    provided its source (Tanzil.net) is clearly indicated, and
#    a link is made to http://tanzil.net to enable users to keep
#    track of changes.
#
#  - This copyright notice shall be included in all verbatim copies
#    of the text, and shall be reproduced appropriately in all files
#    derived from or containing substantial portion of this text.
```
