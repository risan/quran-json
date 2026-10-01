# Research: per-ayah audio sources (2026-10-01)

Labels: **[V]** verified live today by curl or a fetched page. **[R]** reported by a page or API I read, not independently proven. **[G]** my guess or inference. Raw outputs are in the scratchpad `audio/` folder.

## Summary

- **Per-ayah audio exists and is easy.** EveryAyah has 79 listed recitations, about 47 distinct Arabic recitations if you drop duplicate bitrates and the non-Arabic translation folders [V]. Three are Warsh [V].
- **Nobody grants an open licence for the recordings.** The strongest wording found is Islamic Network's: "Recitations are licensed to us by the reciters or their estates for free, non-commercial redistribution at the bitrates we publish" [V, alquran.cloud terms]. EveryAyah has no terms at all [V]. MP3Quran's "redistribution with attribution" claim in our README I could **not** find on its public pages [V: not found].
- **A third-party review says the same.** The QuranLab dataset ran a licence review and concluded "no surveyed source grants an open, sublicensable license to redistribute the recordings" [V, quoted below]. It therefore links to audio and never hosts it. That is exactly our posture.
- **Timing data with a clean licence exists.** `cpfair/quran-align` gives word-level timing for 12 EveryAyah recitations, CC-BY-4.0 (the repo LICENSE says MIT for code; the data README says CC-BY-4.0) [V]. QuranLab adds CC-BY-4.0 timing for more recitations, but as Parquet [R].
- **Per-surah files with ayah timing** exist at MP3Quran (115 recitations with `ayat_timing`, includes Warsh/Qalun) [V] and Quran.com (14 chapter recitations with segments) [V]. Their timing licence is not stated [V: none found].
- **Recommendation:** keep EveryAyah as the main per-ayah host. Keep Islamic Network as the second one. Keep MP3Quran for per-surah breadth. Add a `timing` link to the CC-BY cpfair data. Do not add Quran.com audio, QUL, or QuranicAudio as hosts (no licence, and they are mostly mirrors).

## Host table

| Host | Granularity | Template | Numbering | Reciters / riwayat | Bitrate | CORS | HTTPS | Timing |
|---|---|---|---|---|---|---|---|---|
| **EveryAyah** | per-ayah | `https://everyayah.com/data/{folder}/{SSS}{AAA}.mp3` | surah-relative, both 3-digit zero-padded | 79 folders [V]; ~47 distinct Arabic recitations (~44 Hafs + 3 Warsh) [G-count from list]. Index: `https://everyayah.com/data/recitations.js` [V] | 16-192 kbps, per folder | `access-control-allow-origin: *` [V] | yes | No timing on EveryAyah itself (`/files.html` 404 [V]). Third-party: cpfair, QuranLab |
| **Islamic Network CDN** | per-ayah and per-surah | `https://cdn.islamic.network/quran/audio/{bitrate}/{edition}/{N}.mp3` and `.../audio-surah/{bitrate}/{edition}/{S}.mp3` | per-ayah: global 1-6236, no padding; per-surah: 1-114 | 190 audio editions via `api.alquran.cloud/v1/edition?format=audio` [V]: 176 Arabic, rest translations. Hafs; Qaloon appears as a per-surah edition [R] | 32/40/48/64/128/192 per page [R] | **No** `access-control-allow-origin` on `cdn.islamic.network` files [V]. `api.alquran.cloud` JSON does send `*` [V]. Plain `<audio>` playback does not need CORS [G] | yes | none found |
| **MP3Quran** | per-surah | `{server}{SSS}.mp3` | surah, 3-digit | 242 reciters, 288 moshaf, 19 riwayat incl. Warsh (3 variants), Qalon, Doori, Soosi, Shu'bah, Khalaf [V, API v3] | mostly 64-128 kbps [G] | `*` [V] | yes | `GET https://mp3quran.net/api/v3/ayat_timing?surah={n}&read={id}` returns `start_time`/`end_time` in ms per ayah (+ SVG polygons) [V]. 115 recitations covered [V]. Licence: none found |
| **Quran.com** (`verses.quran.com`, `audio.qurancdn.com`) | per-ayah | `https://verses.quran.com/{path}/{SSS}{AAA}.mp3`, path from `api.quran.com/api/v4/recitations/{id}/by_chapter/{n}` | surah-relative, 3+3 pad | 12 recitations [V]. 3 of them (Husary, Tablawi, Husary Muallim) are `mirrors.quranicaudio.com/everyayah/...`, i.e. EveryAyah copies [V]. Hafs only | n/a | `*` [V] | yes | Chapter files with `segments` (word level) via `chapter_recitations/{id}/{n}?segments=true`: 14 reciters, all Hafs [V]. Licence: none found |
| **QuranicAudio** (`download.quranicaudio.com`) | per-surah | `https://download.quranicaudio.com/quran/{reciter}/{SSS}.mp3`, also `/qdc/{reciter}/murattal/{n}.mp3` | surah | many (not counted) | n/a | `*` [V] | yes | via Quran.com chapter segments only |
| **Tarteel QUL** | both | JSON/SQLite download, needs account [G] | n/a | 133 recitations: ~20 ayah-by-ayah, ~113 surah-by-surah, 59 with segments [R] | n/a | n/a | n/a | segments `[word, start_ms, end_ms]`. Audio source not disclosed [R] |
| **QuranLab / HF** `quranlab/quran-audio` | metadata only, no audio | Parquet manifests with `audio_url` | `verse_key` | 245-reciter taxonomy; 47 per-ayah (EveryAyah) + 285 per-surah (MP3Quran), 15 riwayat [R] | n/a | n/a | n/a | CC-BY-4.0 word timing for 44 recordings [R] |
| **cpfair/quran-align** | timing only | GitHub release zip, 12 JSON files, ~2.3 MB each [V] | surah, ayah | EveryAyah folders | n/a | n/a | n/a | CC-BY-4.0, 2016, repo inactive since 2017 [V] |
| archive.org, KSU e-mushaf, Quranpedia | not examined in depth | | | | | | | I found no per-ayah open collection with a stated licence. Quranpedia is named by QuranLab only as "consulted, never quoted" [R]. Treat as **not investigated** |

### Licence text, verbatim

- **EveryAyah:** none. `license.txt`, `terms.html`, `readme.txt`, `LICENSE` all return 404; the home page has no terms [V]. Hotlinking: not addressed. It serves `access-control-allow-origin: *` and range requests, which suggests tolerance [G]. The CDN is BunnyCDN [V].
- **Islamic Network / alquran.cloud** (https://alquran.cloud/terms-and-conditions) [V, curl]:
  - "Recitations are licensed to us by the reciters or their estates for free, non-commercial redistribution at the bitrates we publish. You may stream, embed and download them for personal and educational use. You may bundle them into a commercial product, but please note that copyrights lie with the reciters and they may ask you to remove the conent." (typo is upstream)
  - The CDN docs page (https://alquran.cloud/cdn) states no limits or hotlinking rule [R].
  - `islamic.network/terms` returned 404 [V]. I assume alquran.cloud and Islamic Network are one operator; the site footers point to each other [G].
- **MP3Quran:** I fetched `/eng`, `/eng/about`, `/eng/api`. None states a licence, copyright grant, or redistribution rule [V: not found]. `/eng/terms` and `/eng/copyright` return 404 [V]. **Our README's "copying and redistribution permitted with attribution" is unsupported by what I could reach.** It may live on a page I did not find (Arabic site, torrent page). Needs a source URL or a downgrade to "unknown".
- **Quran.com** (https://quran.com/terms-and-conditions) [R, via fetch summary]: content "for individual, noncommercial, informational purposes only"; no copying or distribution "without the prior written consent of Quran.com"; no scraping. This is restrictive. Do not use as a host.
- **QUL FAQ** [R]: "Yes, you can use QUL data in commercial projects. However, please review the licensing terms for each resource." and "Some are in the public domain, while others may be subject to specific licenses." Audio resource pages state no licence [R].
- **cpfair/quran-align data README** [V]: "These data files are licensed under a Creative Commons Attribution 4.0 International License."
- **QuranLab LICENSES.md** [V]: "A determined license review (6 of 6 redistribution claims refuted) found that no surveyed source grants an open, sublicensable license to redistribute the recordings ... We therefore reference audio by URL and never host it." Timing is "all CC-BY-4.0".

## Reciter coverage (per-ayah unless noted)

All EveryAyah rows [V]: HTTP 200 for `001001`, `002255`, `114006` on each folder listed. One transient connect failure on first try for the Yassin Warsh folder, then 200 [V].

| Reciter | EveryAyah folder (best bitrate) | Islamic Network edition | Quran.com | MP3Quran (per-surah) | Word timing (CC-BY) |
|---|---|---|---|---|---|
| Alafasy | `Alafasy_128kbps` | `ar.alafasy` (128) | rec 7 | read 123 | cpfair |
| Abdul Basit Murattal | `Abdul_Basit_Murattal_192kbps` | `ar.abdulbasitmurattal` (192) | rec 2 | n/a | cpfair (64k folder) |
| Abdul Basit Mujawwad | `Abdul_Basit_Mujawwad_128kbps` | `ar.abdulbasitmujawwad` | rec 1 | n/a | cpfair |
| Husary | `Husary_128kbps` | `ar.husary` | rec 6 | read 118 | cpfair (64k folder) |
| Husary Mujawwad / Muallim | `Husary_128kbps_Mujawwad`, `Husary_Muallim_128kbps` | `ar.husarymujawwad` | rec 12 (Muallim) | read 119 (Mujawwad) | cpfair (Muallim) |
| Minshawi | `Minshawy_Murattal_128kbps`, `Minshawy_Mujawwad_192kbps` | `ar.minshawi` | rec 9, 8 | read 112 | cpfair |
| Sudais | `Abdurrahmaan_As-Sudais_192kbps` | `ar.abdurrahmaansudais` | rec 3 | read 54 | cpfair |
| Shuraim | `Saood_ash-Shuraym_128kbps` | `ar.saoodshuraym` | rec 10 | read 31 | cpfair |
| Ghamdi | `Ghamadi_40kbps` (low quality) | not seen in list [R] | no | read 30 | none |
| Maher Al Muaiqly | `MaherAlMuaiqly128kbps` | `ar.mahermuaiqly` | no | Mojawwad read 133 | none |
| Yasser Al-Dosari | `Yasser_Ad-Dussary_128kbps` | not seen [R] | chapter only (reciter 97) | read 92 | none |
| Ahmed Al-Ajmi | `ahmed_ibn_ali_al_ajamy_128kbps` | `ar.ahmedajamy`, `ar.ahmedalajmi` (per-surah) | no | read 5 | none |
| Ali Al-Hudhaify | `Hudhaify_128kbps` | `ar.hudhaify` | no | read 74 | none |
| Abdullah Basfar | `Abdullah_Basfar_192kbps` | `ar.abdullahbasfar` | no | read 60 | none |
| Ayman Suwaid | `Ayman_Sowaid_64kbps` | `ar.aymanswoaid` | no | n/a | none |
| Hani Rifai | `Hani_Rifai_192kbps` | `ar.hanirifai` | rec 5 | n/a | cpfair |
| Abu Bakr Shatri | `Abu_Bakr_Ash-Shaatree_128kbps` | `ar.shaatree` | rec 4 | read 4 | cpfair |
| **Warsh** | `warsh/warsh_ibrahim_aldosary_128kbps`, `warsh/warsh_yassin_al_jazaery_64kbps`, `warsh/warsh_Abdul_Basit_128kbps` | none per-ayah | none | Warsh per-surah: Yassin (14), Koshi (16), Qazabri (80), Husary (120), M. Sayed (134) with timing | none |

Per-ayah Warsh note: Warsh uses a different verse division in places [R, QuranLab]. A Warsh per-ayah URL must use the Warsh verse numbering, not Hafs. Check this before shipping Warsh per-ayah.

Islamic Network bitrate and count check [V]: its `bitrates` data in our repo lists `ar.alafasy` etc. with 6236 ayahs at 128; `ar.husary` and `ar.minshawi` have 6235 (one missing ayah each) [V, from `data/audio/islamic_network_by_ayah.json`].

Same-file signal [V]: `Alafasy_128kbps/001001.mp3` is 146830 bytes on EveryAyah, on Islamic Network, on Quran.com. Same bytes strongly suggests one source recording copied to three CDNs [G].

## Live checks (Origin: https://example.com, 2026-10-01)

| URL | Status | CORS `*` | Notes |
|---|---|---|---|
| everyayah.com/data/Alafasy_128kbps/001001.mp3 | 200 | yes | audio/mpeg, accept-ranges, BunnyCDN |
| everyayah.com/data/Abdul_Basit_Murattal_192kbps/002255.mp3 | 200 | yes | 1.3 MB |
| everyayah.com/data/Husary_128kbps/114006.mp3 | 200 | yes | |
| cdn.islamic.network/quran/audio/128/ar.alafasy/1.mp3 | 200 | **no** | nginx, accept-ranges |
| cdn.islamic.network/quran/audio/64/ar.alafasy/6236.mp3 | 200 | **no** | |
| cdn.islamic.network/quran/audio-surah/128/ar.alafasy/1.mp3 | 200 | **no** | |
| server8.mp3quran.net/afs/001.mp3 | 200 | yes | Cloudflare |
| verses.quran.com/Alafasy/mp3/001001.mp3, /114006.mp3 | 200 | yes | BunnyCDN |
| download.quranicaudio.com/quran/mishaari_raashid_al_3afaasee/001.mp3 | 200 | yes | |
| download.quranicaudio.com/qdc/mishari_al_afasy/murattal/1.mp3 | 200 | yes | |
| mp3quran.net/api/v3/reciters, /ayat_timing | 200 / 301 | yes | the `ayat_timing` call 301-redirects to `www.` |
| api.quran.com/api/v4/resources/recitations | 200 | yes | `chapter_reciters` returned a 503 Varnish page once [V] |
| everyayah Warsh folders, 11 other reciter folders (table above) | 200 | n/a | 3 files each |

All hosts use HTTPS. Reliability: I only sampled once. EveryAyah and the Quran.com CDNs run on BunnyCDN. I have no uptime history [G: nothing to report].

## Recommendation

1. **Keep EveryAyah** as the per-ayah host. It is the only host with 40+ per-ayah reciters, Warsh, a stable URL, and permissive CORS. Its risk is that it states no licence. Keep the README row as "no terms; linked, not copied". The QuranLab project took the same stance.
2. **Keep Islamic Network** as the second per-ayah host, because it is the only one with explicit words ("free, non-commercial redistribution"). Fix the doc: the terms live on alquran.cloud, and the CDN has no CORS header. Fine for `<audio>`, not for `fetch`.
3. **Keep MP3Quran** only for per-surah breadth and Warsh/Qalun. Its licence claim in the README needs a source or a downgrade to "unknown" (see above). If we cannot source it, MP3Quran is no better than EveryAyah.
4. **Do not add** Quran.com audio hosts (restrictive terms, and 3 of 12 are EveryAyah mirrors), QuranicAudio (no licence found), or QUL (no audio licence, account needed, source undisclosed).
5. **Add timing as optional links**, not copies: cpfair CC-BY-4.0 covers 12 recitations. Importing JSON of ~2.3 MB each into the build is feasible, but 12 x 2.3 MB is large for the 20,000-file budget only if split per ayah; as 12 files it is fine [G]. Attribution to Collin Fair is required. QuranLab's timing for 44 recordings is a second source, but it is Parquet and I did not verify its per-row coverage (its own CSV flags only some recordings as having timing) [R], so treat it as a later option.
6. **How many good per-ayah reciters can we offer?** About 47 EveryAyah recitations (44 Hafs, 3 Warsh), of which roughly 25 at 128 kbps or better [G]. Islamic Network adds about 22 Arabic per-ayah editions at 64-192 kbps, mostly overlapping EveryAyah [R]. Every famous reciter on your list has a per-ayah folder on EveryAyah. The weak one is Ghamdi (40 kbps only). Maher Al Muaiqly's Mojawwad is per-surah only.

### Minimal JSON shape for per-ayah audio

Keep the current host template idea. Add one `timing` object only where a CC-BY file exists.

```json
{
  "hosts": {
    "everyayah": {
      "granularity": "ayah",
      "template": "https://everyayah.com/data/{folder}/{surah:03d}{ayah:03d}.mp3",
      "indexing_mode": "surah-relative",
      "license": { "status": "unknown", "url": "https://everyayah.com/" }
    }
  },
  "recitations": [
    {
      "id": "everyayah:Alafasy_128kbps",
      "host": "everyayah",
      "folder": "Alafasy_128kbps",
      "reciter": "Mishari Alafasy",
      "riwayah": "hafs",
      "style": "murattal",
      "bitrate_kbps": 128,
      "timing": {
        "url": "https://quran-json.risanb.com/audio/timing/Alafasy_128kbps.json",
        "unit": "word",
        "ms_from": "ayah-start",
        "license": "CC-BY-4.0",
        "attribution": "Collin Fair, cpfair/quran-align"
      }
    }
  ]
}
```

`timing` is optional and absent for most reciters. cpfair segments are `[word_start_index, word_end_index_exclusive, start_msec, end_msec]` within each ayah file [V], which fits "per-ayah file, word highlighting" and is not useful for whole-surah files. For per-surah timing, MP3Quran's `ayat_timing` is a live API without a stated licence, so link to it as `timing_api` only, and do not copy it.

### Open questions for the owner

- Is the README's MP3Quran "redistribution permitted with attribution" claim from an email or a page? If there is no source, the claim must go.
- Should Warsh per-ayah be shipped before its verse numbering is checked against the Hafs scheme?

## Sources

- https://everyayah.com/data/recitations.js (79 folders)
- https://alquran.cloud/terms-and-conditions (audio clause, verified by curl)
- https://alquran.cloud/cdn (templates, bitrates)
- https://api.alquran.cloud/v1/edition?format=audio (190 audio editions)
- https://mp3quran.net/api/v3/reciters, /riwayat, /ayat_timing/reads, /ayat_timing?surah=&read= (all fetched)
- https://api.quran.com/api/v4/resources/recitations, /recitations/{id}/by_chapter/{n}, /chapter_recitations/{id}/{n}?segments=true
- https://api.qurancdn.com/api/qdc/audio/reciters (14 chapter reciters)
- https://quran.com/terms-and-conditions (via fetch summary)
- https://qul.tarteel.ai/resources/recitation and /faq; https://qul.tarteel.ai/resources/recitation/108
- https://github.com/cpfair/quran-align and release `release-2016-11-24` zip (README and LICENSE inside)
- https://huggingface.co/datasets/quranlab/quran-audio (README, LICENSES.md, SOURCES.md, metadata/recitations.csv)
- https://huggingface.co/datasets/hetchyy/quranic-universal-ayahs and tarteel-ai/everyayah (seen in search only; not examined)
- https://github.com/quran/audio.quran.com (repo exists; no licence file in API metadata)
