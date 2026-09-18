# Quran JSON

Quran text, translations, and audio references in JSON format — built by a Python
pipeline, published to a CDN, and generated only from sources that license
redistribution.

## Hosting

| | URL | Served by | Cost |
|---|---|---|---|
| **Dataset (current)** | `https://quran-json.risan.workers.dev/…` | Cloudflare Workers static assets | Free, unlimited bandwidth |
| Dataset (legacy) | `https://cdn.jsdelivr.net/npm/quran-json@3.1.2/dist/…` | npm + jsDelivr | Free |

Cloudflare Workers static assets was chosen over R2 because this dataset is read-heavy:
static requests carry **no quota and no egress charge**, whereas R2 bills Class B read
operations (10M/month free) and only returns CORS headers for pre-configured origins.
`Access-Control-Allow-Origin: *` comes from the generated `_headers` file, which Workers
parses natively.

Two limits matter. **Files: 20,000 per Worker version** on the free plan, 100,000 on paid;
the tree uses 10,359. **Size: 25 MiB per file**; the largest is 5.8 MiB.

**cdnjs was evaluated and rejected.** It is a curated CDN for *"established libraries
published through npm or versioned Git repositories"*: its guide explicitly excludes
*"general-purpose dataset hosting"*, requires ~800 npm downloads/month or ~200 GitHub
stars, discourages broad file globs, and retains only the **10 most recent versions**. It
would also add nothing, because jsDelivr already mirrors this npm package. Use jsDelivr for
the frozen legacy tree and Cloudflare Workers for the current one.

## Endpoints

All paths are relative to `https://quran-json.risan.workers.dev/`, and none of them carry a
version.

| Path | Contents |
|---|---|
| `manifest.json` | Scripts, counts, and pointers |
| `chapters.json` | Metadata for all 114 chapters |
| `text/{script}/quran.json` | The whole Quran in one script |
| `text/{script}/chapters/{1-114}.json` | One chapter in one script |
| `translations/index.json` | The edition catalogue, with licence and version per entry |
| `translations/{code}-{slug}/quran.json` | The whole Quran in one translation |
| `translations/{code}-{slug}/chapters/{1-114}.json` | One chapter in one translation, with footnotes |
| `transliteration/index.json` | The romanisation catalogue — empty while nothing is licensed |
| `transliteration/{key}/quran.json` | The whole Quran in one romanisation |
| `transliteration/{key}/chapters/{1-114}.json` | One chapter in one romanisation |
| `audio/reciters.json` | 595 recitations across 3 hosts, as URL templates |
| `meta/sources.json` | Provenance and license for everything published |
| `meta/qa.json` | Transcription corrections applied to upstream sources |

**Seven text scripts**, all complete at 6,236 verses — six Tanzil orthographies, plus the
Indonesian standard mushaf from Qur'an Kemenag:

| `{script}` | Name | Notes |
|---|---|---|
| `uthmani` | Uthmani | Uthmanic orthography, full vocalisation |
| `uthmani-min` | Uthmani minimal | Uthmanic orthography, reduced marks |
| `simple` | Imlaei | Modern orthography, full vocalisation, assimilated letters |
| `simple-plain` | Imlaei plain | Modern orthography, unassimilated letters |
| `simple-min` | Imlaei minimal | Modern orthography, reduced marks |
| `simple-clean` | Imlaei unvocalised | Modern orthography, **no vowel marks at all** |
| `kemenag` | Mushaf Standar Indonesia | Kemenag (LPMQ) Indonesian standard, Imlaei rasm with waqf marks |

`simple` is an easy trap: it is a different *orthography*, not a lower level of
vocalisation, and it carries the full set of harakat. Reach for `simple-clean` if you want
the text without them.

`kemenag` is not a seventh *label* for a Tanzil text but a different orthography: it writes
no alef wasla (`U+0671`) where Tanzil's Uthmani text writes 13,819 of them, and only 6 of
the 37,416 verse comparisons against the six Tanzil variants coincide (47:6, 55:4 and 56:3
against the Imlaei texts, 56:3 against Uthmani) — verses that hold none of the
distinguishing marks. It is the text served by <https://quran.kemenag.go.id/>, and the
ministry's own publishing regulation holds the mushaf text to be uncopyrightable; see
[Licensing](#licensing). Trailing whitespace is stripped, and the API's double space after
a waqf sign is preserved as published.

**Translations carry the translation only.** The Arabic is identical across editions, so
embedding it would have duplicated one 1.7 MB corpus 83 times — 105 MB, a fifth of the old
deployment. Pair a text file with a translation file instead:

```js
const [arabic, indonesian] = await Promise.all([
  fetch("https://quran-json.risan.workers.dev/text/simple-clean/chapters/2.json").then(r => r.json()),
  fetch("https://quran-json.risan.workers.dev/translations/id-affairs/chapters/2.json").then(r => r.json()),
]);
// arabic.verses[254].text === "الله لا إله إلا هو الحي القيوم" (2:255, Ayat al-Kursi)
// indonesian.verses[254].translation
```

Every chapter file numbers its verses `1..total_verses` with the key `id`, which is what the
audio templates need:

```js
const audio = `https://everyayah.com/data/Alafasy_128kbps/${String(chapterId).padStart(3, "0")}${String(verseId).padStart(3, "0")}.mp3`;
```

### Compatibility contract

Unversioned paths only work because they are stable. The rules:

- A published path is **never renamed, removed, or rewritten**. Data paths are cached
  `immutable` for a year, so a rewrite would strand consumers on stale bytes.
- **Adding is always fine** — new scripts, editions, and chapters.
- Correcting the Quran text would be a break, and would require publishing new paths
  rather than editing existing ones.

`dist/` is the exception: it is frozen and never regenerated.

## Two generations

`dist/` is the original published tree, frozen. It is still served through jsDelivr and is
reproduced byte-for-byte by `quran-json build` (enforced by `tests/test_parity.py`), because
consumers pin those URLs. It is **not** regenerated: it contains editions whose licenses
do not permit redistribution.

| | `dist/` (frozen, 3.1.2) | Published (current) |
|---|---|---|
| Arabic text | Re-encoded derivative, no upstream license | **Seven scripts**: six Tanzil, CC-BY 3.0 verbatim, plus the Indonesian standard mushaf from Qur'an Kemenag |
| Chapter metadata | Quran.com API (personal, non-commercial) | **Tanzil `quran-data.xml`**, CC-BY 3.0 |
| Translations | 11, mostly Tanzil (redistribution not permitted) | **83, all with grants**: 75 QuranEnc + 8 public-domain / author-granted. Two more are ingested from Qur'an Kemenag and withheld |
| Transliteration | Yes (Tanzil) | Withheld — no romanisation is licensed, including Qur'an Kemenag's (see below) |
| Per-surah audio | none | 159 editions (Islamic Network), 288 (MP3Quran) |
| Basmala | Only in 1:1 | Embedded in ayah 1 of every surah except 9 |
| Verse files | Bengali missing (upstream bug) | No per-verse files: a chapter file answers the same question |
| Files | 7,513 | 10,359 |
| Size | 82 MB | 312 MB |

The basmala change is the one most likely to surprise a consumer migrating. Tanzil embeds
it in the opening ayah rather than storing it as chapter metadata, so `2:1` is
`بِسْمِ ٱللَّهِ ٱلرَّحْمَٰنِ ٱلرَّحِيمِ الٓمٓ`. Surahs 95 and 97 spell it `بِّسْمِ` with a shadda
on the beh (idgham with the preceding surah), and At-Tawbah has no basmala at all.

## Licensing

Everything published comes from a source that grants redistribution. **The grant must come
from the rights holder; the distribution channel is irrelevant** — which is why public-domain
and author-granted works qualify even when they were fetched from an aggregator that states no
licence. Judge the work, not the host.

**English** is covered nine times over: three QuranEnc editions (Rowwad, Noor/Saheeh
International, Hilali-Khan), two ClearQuran editions fetched from the translator's own
archive, and four public-domain classics (Sale 1734, Palmer 1880, Pickthall 1930, Yusuf
Ali 1934).

**Russian** is covered twice via public domain — Sablukov (1878, d.1880) and Krachkovsky
(d.1951) — which matters because QuranEnc publishes no Russian edition at all.

Known gaps: **Bengali** (Girish Chandra Sen, d.1910) and **Malay** (Tarjuman al-Mustafid,
d.1693) have public-domain translations but no verse-numbered digitisation exists; both
would need an extraction pass.

`quran-json licenses` prints the current verdicts; `data/meta/licensing-review.json` records
the evidence behind each.

### What "public domain" means here

A **public-domain (PD)** work has no copyright owner left — the term expired, so anyone may
copy, modify, and redistribute it with no permission and no conditions. The four English
classics qualify because their authors died long enough ago, under the life-plus-70-years
rule used across most jurisdictions: Sale (d.1736), Palmer (d.1882), Pickthall (d.1936) and
Yusuf Ali (d.1953).

**They are supplements, not replacements.** The *modern* reputable English translations
this project can legally ship already do ship — Rowwad, Noor/Saheeh International and
Hilali-Khan under QuranEnc's grant, plus Talal Itani's own CC BY-ND archive. What cannot
ship is every translation still in copyright with no grant: Abdel Haleem (OUP), Khattab's
*The Clear Quran*, Asad's *Message*, *The Study Quran*. None offers a free-licence route,
so the PD classics are the only legitimate way to widen English coverage further.

### Text quality is checked against an independent witness

Volunteer digitisation can carry transcription damage, so the public-domain editions were
verified against **Project Gutenberg #16955** — Yusuf Ali, Pickthall and Shakir side by
side, *"re-proofed and corrected for Project Gutenberg against paper copies of the
translations"*:

| Edition | Identical after normalisation | Edition variants | True defects |
|---|---|---|---|
| Pickthall | 6,157 / 6,232 (98.8%) | ~14 (`God` → `Allah` renderings) | 0 |
| Yusuf Ali | 6,173 / 6,232 (99.1%) | ~14 (revised-printing wording) | **1** |

Gutenberg's own file is missing four verses (17:33, 39:46, 45:32, 56:26), so it is a witness
rather than a source. Flagged phrase repetitions were checked individually: most are genuine
Quranic rhetoric that Gutenberg confirms exactly (*"a wave, above which is a wave"* 24:40),
not corruption. The single true defect — a duplicated fragment in Yusuf Ali 5:94 — is
restored by `quranjson.qa`, which also **fails the build if upstream ever repairs the text
itself**, so the patch cannot rot into a double-correction. The record is published at
`/meta/qa.json`.

| Source | Status | Evidence |
|---|---|---|
| **Tanzil text & metadata** | ✅ Granted | CC-BY 3.0: *"Permission is granted to copy and distribute verbatim copies of this text, but CHANGING IT IS NOT ALLOWED."* — <https://tanzil.net/docs/text_license> |
| **Public-domain English translations** — Sale 1734, Palmer 1880, Pickthall 1930, Yusuf Ali 1934 | ✅ Granted | Out of copyright by the death of the author (Sale d.1736, Palmer d.1882, Pickthall d.1936, Yusuf Ali d.1953). Each verified verse-numbered and complete |
| **ClearQuran (Talal Itani)** | ✅ Granted | *"free to use, share, and distribute — including in commercial projects — with no permission or authorization required"* under CC BY-ND 4.0 — <https://blog.clearquran.com/download>. Fetched from the translator's own verse-by-verse archive, not a packager |
| **QuranEnc translations** (75) | ✅ Granted | *"Contents of the translations can be downloaded and re-published"* under 7 conditions: verbatim, credit publisher + QuranEnc.com, state the version, keep transcripts, no inappropriate advertising — <https://quranenc.com/en/home/api> |
| **Qur'an Kemenag text** (`kemenag`) | ✅ Granted | Minister of Religious Affairs Regulation 44/2016, Pasal 8(1): *"Teks Mushaf Al-Qur'an tidak memiliki hak cipta"*, and Copyright Law 28/2014, Pasal 42(e), which removes copyright from a *kitab suci*. Pasal 8(2) keeps the publisher's rights in the calligraphy, the tanda baca/tajwid/qira'at apparatus and the ornaments, so this project takes only the plain UTF-8 text — no fonts, no mushaf layout, no ornaments — <https://jdih.kemenag.go.id/regulation-download/penerbitan-pentashihan-dan-peredaran-mushaf-al-qur%27an> |
| Qur'an Kemenag translation (Indonesian, 2019) | ⛔ Restricted | A translation is a protected work: Copyright Law 28/2014, Pasal 59(g) covers *"terjemahan, tafsir, …"* for 50 years from first publication, and nothing exempts the ministry. No grant is published — the serving API states no terms and the ministry's own site was unreachable (2026-09-18). Ingested and withheld; the same ministry's earlier edition is already published as `id-affairs` under the QuranEnc grant — <https://peraturan.bpk.go.id/Details/38690/uu-no-28-tahun-2014> |
| Qur'an Kemenag translation romanisation | ⚠️ Unknown | A romanisation carrying authored vocalisation, so the uncopyrightable-mushaf-text rule does not reach it, and no grant exists either. Ingested and withheld |
| Tanzil translations | ⛔ Restricted | *"for non-commercial purposes only… you need to obtain necessary permission from the translator or the publisher"* and *"Redistributing the following list in another website is not allowed"* — <https://tanzil.net/trans/> |
| Saheeh International (`en`) | ⛔ Restricted | All rights reserved; the publisher's domain is gone. Ships in the frozen `dist/` tree — see below |
| fawazahmed0/quran-api | ⚠️ Unknown per edition | Repo is Unlicense, but no per-edition license field exists and it republishes all-rights-reserved works |
| Quran.com API v4 | ⛔ Restricted | *"FOR YOUR PERSONAL, NON-COMMERCIAL USE ONLY"*, no *"compiling a collection of listings or data"* — <https://quran.com/terms-and-conditions> |
| MP3Quran audio | ✅ Granted | Copying and redistribution permitted with attribution |
| Islamic Network audio | ✅ Granted | Free non-commercial redistribution; reciter copyrights retained |
| EveryAyah audio | ⚠️ Unknown | No license page exists (license/terms/readme all 404) |

The gate is enforced in code, not documentation: `quranjson.licensing` refuses to publish
an edition whose status is not `granted`, `cdn` prints what it withheld, and
`tests/test_licensing.py` fails if a restricted edition silently regains a permissive
label. `--include-unverified-licenses` overrides it deliberately — it republishes the
editions ingested for this generation, not the frozen tree's restricted ones.

**On Indonesia's non-commercial carve-out.** Copyright Law 28/2014, Pasal 43(d) does not
treat *"pembuatan dan penyebarluasan konten Hak Cipta melalui media teknologi informasi dan
komunikasi yang bersifat tidak komersial"* as infringement, and this project is
non-commercial. That does not change the verdicts above. Pasal 43(d) limits liability
rather than granting rights, so it passes nothing on to a consumer; it is conditioned on the
use being non-commercial, whereas this dataset is offered under CC BY-SA with no such limit
downstream; and this repository already records a non-commercial-only term as `restricted`
— which is exactly how Tanzil's translations are treated. It also requires the author to
state no objection, and LPMQ has stated none reachable to us.

**Copyright is not the only duty.** Indonesia's Minister of Religious Affairs Regulation
44/2016, Pasal 2 requires every *mushaf* published, printed or circulated in Indonesia —
and Pasal 1 defines a mushaf as any medium holding Quranic verses, *"baik cetak maupun
digital"* — to hold a Surat Tanda Tashih or Surat Izin Edar from LPMQ. A dataset of the
whole text is squarely within that definition, so anyone circulating this data *in
Indonesia* should treat tashih as a separate registration step. It is not a condition of
this project's redistribution grant, it applies to the Tanzil scripts just as much as to
the `kemenag` one, and it is stated here because a consumer should meet it knowingly.

**Audio ships as URL templates, never as audio files.** That keeps the repository small,
keeps the 20,000-file budget intact (one file per ayah per reciter would exhaust it
immediately), and means this project links to those hosts rather than redistributing
their recordings — which matters for the two hosts whose terms are unstated or partial.

### Known issue in the frozen tree

`dist/` (and the npm package up to 3.1.2) ships **Saheeh International** as
`data/editions/en.json`, labelled in the original source with *Tanzil's Arabic-text
licence* — which does not cover translations. Eight further editions are Tanzil-hosted
and Tanzil forbids their redistribution. The frozen tree is retained for URL stability;
the published generation does not use any of them. If you control that npm package, the
clean fix is to deprecate 3.1.2 in favour of the CDN.

## What the research found

- **Upstream drift.** The `ara-quranuthmanienc` edition changed underneath the project:
  6,031 of 6,236 verses now differ from the committed 2019 snapshot. It switched to
  **Farsi Yeh U+06CC** (21,912×), replaced sukun U+0652 with small-high-rounded-zero
  U+06DF, and introduced **non-breaking spaces U+00A0** (1,631×). `fetch --force` does not
  apply this silently: it records counts and a codepoint delta in `data/meta/drift.json`,
  and the frozen hash in `tests/test_provenance.py` pins the text that was actually
  shipped. A one-record chapter-name change in `data/chapters/ur.json` is recorded too.
- **That text is a derivative with no grant.** It came from `ara-quranacademy`, which
  states it is derived from Tanzil's Uthmani text with systematic re-encoding, and carries
  no LICENSE file — while Tanzil permits verbatim copies only.
- **A latent bug in the original build.** `qurans.slice(2)` silently omitted Bengali from
  all 6,236 verse files. Reproduced deliberately by `--legacy-verse-langs` so the frozen
  tree stays provable, and fixed in the published generation.
- **Basmala handling** is not uniform: 111 surahs use `بِسْمِ`, surahs 95 and 97 use the
  assimilated `بِّسْمِ`, and At-Tawbah has none.
- **Audio URL schemes differ and were verified live**: EveryAyah uses surah-relative ayah
  numbers with both parts zero-padded (`114006.mp3`), Islamic Network uses the global ayah
  number unpadded (`6236.mp3`), MP3Quran uses whole-surah files (`114.mp3`).

## Transliteration

**Not published: no transliteration was found whose redistribution is granted.** This was
researched exhaustively, and the whole readable Latin transliteration space collapses to
essentially one text (the `Bismi Allahi alrrahmani alrraheemi` family), republished under
contradictory licence labels. `quran-json licenses` lists every candidate with its blocker;
`data/meta/licensing-review.json` is the durable record.

Qur'an Kemenag does serve a romanisation beside its text, so one is now **ingested** — all
6,236 verses, one romanised ayah per verse, `latin` in the API and
`data/kemenag/quran.json` in this repository. It stays withheld: a romanisation is an
authored transformation, so the rule that frees the mushaf text does not reach it, and no
grant is published. Publishing it is `--include-unverified-licenses` away, once the rights
are cleared.

| Candidate | Status | Blocker |
|---|---|---|
| **Pre-1929 public-domain transliteration** | ⛔ None exists | The only pre-1929 "Roman" Qur'an is the 1844/1876 Roman-**Urdu** translation — an Urdu text in Latin letters, not a transliteration of the Arabic |
| Tanzil `en.transliteration` | ⛔ Restricted | Terms forbid redistribution; their CC-BY notice covers the Arabic text only |
| **Qur'an Kemenag (LPMQ) `latin` field** | ⚠️ Unknown | An authored romanisation, not the uncopyrightable mushaf text, and no grant is published. Complete at 6,236 verses; ingested, reviewed, and withheld |
| Islamic Bulletin PDF | ⛔ Restricted | It offers *"free for use to everyone…"* but credits **"The Calgary Islamic Homepage"**, whose archived footer reads **"Copyright 1997 - 2004 … All Rights Reserved"** — the only grant on that text is contradicted by the credited author |
| Pickthall's bundled transliteration | ⛔ Restricted | By M. A. Haleem Eliasii, first published **1983** — in copyright |
| QUL / Tarteel | ⚠️ None | Swept **every** resource id: of ~591 resources, 2 have any licence statement and both are restrictive; the rest say *"We don't have copyright information"* |
| QuranPhoneticSearch (MIT) | ⛔ Unusable | Data derives from the Calgary text, has no verse ids, and stops inside al-A'raf 7:135 — surahs 1–7 of 114 |
| fawazahmed0 `-la` editions | ⚠️ Unknown | No per-edition licence; most `-la` slugs are romanised *translations*, not transliterations |
| Quran.com id 57 | ⛔ Restricted | Personal, non-commercial, no compilation |
| **Self-generated from a CC BY-SA Arabic text** | 🟡 Viable, needs building | Generate from Wikisource's Hafs/imlaei text — **CC BY-SA**, the same licence this repo ships under, so no permission email is needed. See below |

**The viable route is to generate one.** Wikisource hosts the Hafs/Madinah and imlaei
Arabic texts organised by surah under CC BY-SA 4.0 — compatible with this repository's own
licence — so a transliteration derived from it needs nobody's permission. Two caveats
verified first-hand: the surah pages only *transclude* a Lua table, so the text has to come
out of `Module:Quran`; and the MIT phonemizer projects a research pass credited for this
work **do not exist** (both 404), so the grapheme-to-phoneme step must be written and
reviewed. Tanzil's `en.transliteration` remains the one-email fallback
(`admin@tanzil.net`) and would be the reference for spot-checking our output.

The pipeline is transliteration-capable end to end: `build.RenderOptions.transliteration`
and `quran_transliteration.json` in the frozen tree, and a `/transliteration/` category on
the site. The site writes `/transliteration/index.json` even when it publishes nothing, so
a consumer asking whether a romanisation exists gets an answer — and the candidates it lists
with their verdicts — rather than a 404. Publishing one is a matter of moving a verdict to
`granted`, or running the build with `--include-unverified-licenses`; `tests/test_licensing.py`
deliberately fails while no transliteration is licensed.

## Deprecating the old npm package

`dist/` is unchanged and stays on npm + jsDelivr — do not remove or regenerate it.
Deprecating it is **non-breaking**: `npm deprecate` only edits registry metadata. It does
not delete files, touch `node_modules`, invalidate lockfiles, or change
`require()`/`import` behaviour. Only *new* installs see a warning, and jsDelivr keeps
serving every pinned URL (it retains fetched files permanently). Do **not**
`npm unpublish` — that is the destructive action.

```bash
npm deprecate "quran-json@<=3.1.2" \
  "Ships translations without redistribution rights and is unmaintained. Use the licensed dataset at https://quran-json.risan.workers.dev/ instead."
```

Nothing here publishes to npm on its own, and `package.json` still reads `3.1.2`, so the
frozen tree's generated `link` fields stay valid.

## Development

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12+.

```bash
uv sync                       # install
uv run pytest                 # 84 tests: parity, integrity, licensing, layout
uv run mypy && uv run ruff check .

uv run quran-json licenses    # what may be published, why, and what blocks the rest
uv run quran-json licenses --write   # refresh data/meta/licensing-review.json
uv run quran-json fetch       # refresh the committed upstream snapshots
uv run quran-json verify      # snapshot hashes and licence completeness
uv run quran-json build       # regenerate the frozen dist/ tree (byte-identical)
uv run quran-json cdn         # render the deployable site into cdn/
uv run quran-json probe       # check a sample of live audio URLs
```

`fetch` never overwrites an existing snapshot unless `--force` is passed, and `--force`
records whatever changed in `data/meta/drift.json` first. Builds read only the committed
snapshots under `data/`, so they work offline.

## Deploying

```bash
uv run quran-json cdn        # render the site into cdn/
npx wrangler deploy          # reads assets.directory from wrangler.jsonc
```

On Cloudflare, connect the repository to the Worker instead and let it build. The build
command must be:

```
curl -LsSf https://astral.sh/uv/install.sh | sh && export PATH="$HOME/.local/bin:$PATH" && uv sync --locked && uv run quran-json cdn
```

and the deploy command `npx wrangler deploy`. `cdn/` is gitignored, so it has to be
generated in the same run — there is nothing committed for a static-only deploy to serve.
Cloudflare's build image ships Python 3.13, which satisfies `requires-python`; `uv` is not
in the image, hence the installer. `workers_dev` is enabled and `preview_urls` disabled in
`wrangler.jsonc`, so each deployment does not publish a second copy of the dataset at an
unpredictable hostname.

`.github/workflows/deploy.yml` can do the same from GitHub on a `v*` tag or manual
dispatch; set `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` as repository secrets. Do
not run both paths at once — they target the same Worker, and the workflow derives the URL
version from the tag while the Cloudflare build uses the constant.

## Attribution

Quran text and chapter metadata: [Tanzil.net](https://tanzil.net) (CC-BY 3.0, six text
variants published verbatim) and, for the `kemenag` script, LPMQ / Kementerian Agama RI
(the Indonesian standard mushaf, whose text its publishing regulation holds to be
uncopyrightable). Translations: the publishers credited per edition in
`translations/index.json` and `meta/sources.json` via [QuranEnc.com](https://quranenc.com). Audio: linked from EveryAyah, Islamic Network, and
MP3Quran; each recitation's rights remain with its reciter.

Project code and the frozen `dist/` tree: [CC BY-SA 4.0](LICENSE.txt).
