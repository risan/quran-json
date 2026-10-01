# Published data schemas

These Draft 2020-12 JSON Schemas describe the CDN wire contract: the generated site under
`cdn/`.

| Schema | Published path or payload |
| --- | --- |
| `manifest.schema.json` | `/manifest.json` |
| `chapters.schema.json` | `/chapters.json` |
| `script.schema.json` | `/text/{script}/quran.json` and chapter objects |
| `translation-catalogue.schema.json` | `/translations/index.json` |
| `translation.schema.json` | `/translations/{edition}/quran.json` and chapter objects |
| `transliteration-catalogue.schema.json` | `/transliteration/index.json` |
| `transliteration.schema.json` | `/transliteration/{edition}/quran.json` and chapter objects |

The generated examples are checked in the Python test suite with a standard JSON Schema
validator. The tests also check semantic catalogue counts and verse identity alignment,
because those relationships cannot be expressed by a small portable schema alone.
