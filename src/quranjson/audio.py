"""Audio: upstream manifests, and the published reciter/URL-template index.

We publish **URL templates, not audio bytes**. That keeps the repository small, keeps the
20,000-file Cloudflare Pages budget intact (one file per ayah per reciter would blow it
immediately), and means we are linking to these hosts rather than redistributing their
recordings -- which matters because only some of them grant redistribution.

There is deliberately no per-ayah audio file. Consumers construct the URL from the verse
they already fetched: `/text/{script}/chapters/{n}.json` carries the chapter id as the file
name and each verse's surah-relative `id`, which is what a `surah-relative` host wants; a
`global-ayah` host wants the verse's number across the whole Quran, which `/chapters.json`
sums from `total_verses`. Both are published per host as `indexing_mode`, `surah_pad` and
`ayah_pad`, so a client never has to parse the prose.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from . import config
from .http import Fetcher
from .jsonio import read_json, write_json
from .sources import FetchTask

__all__ = ["AUDIO_HOSTS", "PROBE_URLS", "audio_tasks", "build_audio_index", "probe"]

EVERYAYAH = "everyayah"
MP3QURAN = "mp3quran"
ISLAMIC_NETWORK = "islamic_network"

AUDIO_HOSTS: dict[str, dict[str, Any]] = {
    EVERYAYAH: {
        "name": "EveryAyah",
        "home": "https://everyayah.com/",
        "template": "https://everyayah.com/data/{reciter}/{surah:03d}{ayah:03d}.mp3",
        "indexing": "surah-relative ayah, both zero-padded to 3 digits",
        "indexing_mode": "surah-relative",
        "surah_pad": 3,
        "ayah_pad": 3,
        "cors": True,
        "accept_ranges": True,
        "license": config.EVERYAYAH_AUDIO,
    },
    MP3QURAN: {
        "name": "MP3Quran",
        "home": "https://mp3quran.net/eng/",
        "template": "{reciter}{surah:03d}.mp3",
        "indexing": "whole-surah files, surah zero-padded to 3 digits",
        "indexing_mode": "whole-surah",
        "surah_pad": 3,
        "ayah_pad": 0,
        "cors": True,
        "accept_ranges": True,
        "license": config.MP3QURAN_AUDIO,
    },
    ISLAMIC_NETWORK: {
        "name": "Islamic Network CDN",
        "home": "https://islamic.network/",
        "template": "https://cdn.islamic.network/quran/audio/{bitrate}/{reciter}/{ayah}.mp3",
        "surah_template": "https://cdn.islamic.network/quran/audio-surah/{bitrate}/{reciter}/{surah}.mp3",
        "indexing": "per-ayah files use the GLOBAL ayah number 1-6236 (not zero-padded)",
        "indexing_mode": "global-ayah",
        "surah_pad": 0,
        "ayah_pad": 0,
        "cors": False,
        "accept_ranges": True,
        "license": config.ISLAMIC_NETWORK_AUDIO,
    },
}

EVERYAYAH_MANIFEST = "https://everyayah.com/data/recitations.js"
MP3QURAN_MANIFEST = "https://mp3quran.net/api/v3/reciters?language=eng"
ISLAMIC_NETWORK_BY_AYAH = "https://cdn.islamic.network/quran/info/by-ayah/info.json"
ISLAMIC_NETWORK_BY_SURAH = "https://cdn.islamic.network/quran/info/by-surah/info.json"

_BITRATE = re.compile(r"(\d+)")


def _recitations(payload: Any) -> dict[str, Any]:
    """Keep the everyayah manifest as-is minus its per-chapter noise."""
    entries = sorted(
        ((key, value) for key, value in payload.items() if key != "ayahCount"),
        key=lambda item: int(item[0]),
    )

    recitations = [
        {
            "id": entry["subfolder"],
            "name": entry["name"],
            "bitrate_kbps": int(_BITRATE.search(entry["bitrate"]).group(1)),  # type: ignore[union-attr]
        }
        for _, entry in entries
    ]

    return {"ayah_count": payload["ayahCount"], "recitations": recitations}


def _mp3quran(payload: Any) -> dict[str, Any]:
    """Flatten reciters to the fields that build a URL, dropping churn-prone dates."""
    reciters = []

    for reciter in payload["reciters"]:
        for moshaf in reciter["moshaf"]:
            reciters.append(
                {
                    "id": f"{reciter['id']}-{moshaf['id']}",
                    "name": reciter["name"],
                    "recitation": moshaf["name"],
                    "server": moshaf["server"],
                    "surah_total": moshaf["surah_total"],
                }
            )

    return {"reciters": reciters}


def _directory_inventory(payload: Any) -> dict[str, Any]:
    """Reduce an islamic.network directory dump to `bitrate -> {edition: file count}`.

    The dump is a JSON array whose first element is the directory tree; the rest is null.
    """
    tree = next((node for node in payload if node), None) if isinstance(payload, list) else payload

    if not isinstance(tree, dict):
        raise ValueError("unexpected islamic.network info.json shape")

    bitrates: dict[str, dict[str, int]] = {}

    for node in tree.get("contents", []):
        editions = {
            child["name"]: sum(1 for f in child.get("contents", []) if f.get("type") == "file")
            for child in node.get("contents", [])
        }
        bitrates[node["name"]] = editions

    return {"bitrates": bitrates}


def audio_tasks() -> list[FetchTask]:
    """The audio manifests, fetched into committed snapshots."""
    return [
        FetchTask(
            path=config.DATA / "audio" / "everyayah.json",
            url=EVERYAYAH_MANIFEST,
            source=AUDIO_HOSTS[EVERYAYAH]["name"],
            license=config.EVERYAYAH_AUDIO,
            transform=_recitations,
        ),
        FetchTask(
            path=config.DATA / "audio" / "mp3quran.json",
            url=MP3QURAN_MANIFEST,
            source=AUDIO_HOSTS[MP3QURAN]["name"],
            license=config.MP3QURAN_AUDIO,
            transform=_mp3quran,
        ),
        FetchTask(
            path=config.DATA / "audio" / "islamic_network_by_ayah.json",
            url=ISLAMIC_NETWORK_BY_AYAH,
            source=AUDIO_HOSTS[ISLAMIC_NETWORK]["name"],
            license=config.ISLAMIC_NETWORK_AUDIO,
            transform=_directory_inventory,
        ),
        FetchTask(
            path=config.DATA / "audio" / "islamic_network_by_surah.json",
            url=ISLAMIC_NETWORK_BY_SURAH,
            source=AUDIO_HOSTS[ISLAMIC_NETWORK]["name"],
            license=config.ISLAMIC_NETWORK_AUDIO,
            transform=_directory_inventory,
        ),
    ]


def _host_entry(host: str) -> dict[str, Any]:
    spec = AUDIO_HOSTS[host]
    entry = {
        "name": spec["name"],
        "home": spec["home"],
        "template": spec["template"],
        "indexing": spec["indexing"],
        # Prose above for a reader, fields here for a client: which ayah number a template
        # wants, and how wide each placeholder must be padded, without parsing English.
        "indexing_mode": spec["indexing_mode"],
        "surah_pad": spec["surah_pad"],
        "ayah_pad": spec["ayah_pad"],
        "cors": spec["cors"],
        "accept_ranges": spec["accept_ranges"],
        "license_status": spec["license"].status,
        "license": spec["license"].text,
        "license_url": spec["license"].url,
    }

    if "surah_template" in spec:
        entry["surah_template"] = spec["surah_template"]

    return entry


def build_audio_index(out_dir: Path, *, pretty: bool = False) -> dict[str, Any]:
    """Write `reciters.json` describing every audio edition we can point consumers at."""
    everyayah = read_json(config.DATA / "audio" / "everyayah.json")
    mp3quran = read_json(config.DATA / "audio" / "mp3quran.json")
    by_ayah = read_json(config.DATA / "audio" / "islamic_network_by_ayah.json")
    by_surah = read_json(config.DATA / "audio" / "islamic_network_by_surah.json")

    reciters: list[dict[str, Any]] = []

    for entry in everyayah["recitations"]:
        reciters.append(
            {
                "id": f"{EVERYAYAH}/{entry['id']}",
                "host": EVERYAYAH,
                "name": entry["name"],
                "bitrate_kbps": entry["bitrate_kbps"],
                "scope": "ayah",
                "url": AUDIO_HOSTS[EVERYAYAH]["template"].replace("{reciter}", entry["id"]),
            }
        )

    for entry in mp3quran["reciters"]:
        reciters.append(
            {
                "id": f"{MP3QURAN}/{entry['id']}",
                "host": MP3QURAN,
                "name": entry["name"],
                "recitation": entry["recitation"],
                "surah_total": entry["surah_total"],
                "scope": "surah",
                "url": AUDIO_HOSTS[MP3QURAN]["template"].replace("{reciter}", entry["server"]),
            }
        )

    for bitrate, editions in by_ayah["bitrates"].items():
        for edition, count in editions.items():
            reciters.append(
                {
                    "id": f"{ISLAMIC_NETWORK}/{bitrate}/{edition}",
                    "host": ISLAMIC_NETWORK,
                    "name": edition,
                    "bitrate_kbps": int(bitrate),
                    "scope": "ayah",
                    "ayah_files": count,
                    "url": AUDIO_HOSTS[ISLAMIC_NETWORK]["template"]
                    .replace("{bitrate}", bitrate)
                    .replace("{reciter}", edition),
                }
            )

    for bitrate, editions in by_surah["bitrates"].items():
        for edition, count in editions.items():
            reciters.append(
                {
                    "id": f"{ISLAMIC_NETWORK}/surah/{bitrate}/{edition}",
                    "host": ISLAMIC_NETWORK,
                    "name": edition,
                    "bitrate_kbps": int(bitrate),
                    "scope": "surah",
                    "surah_files": count,
                    "url": AUDIO_HOSTS[ISLAMIC_NETWORK]["surah_template"]
                    .replace("{bitrate}", bitrate)
                    .replace("{reciter}", edition),
                }
            )

    index = {
        "note": (
            "URL templates only; this project does not host audio. Substitute {surah} with "
            "the chapter id and {ayah} with a verse id from "
            "/text/{script}/chapters/{n}.json -- or, where the host's `indexing_mode` is "
            "`global-ayah`, with the verse's number across the whole Quran (1-6236), which "
            "`total_verses` in /chapters.json sums to. `surah_pad` and `ayah_pad` give each "
            "placeholder's zero-padded width, so no client has to read this sentence."
        ),
        "hosts": {host: _host_entry(host) for host in AUDIO_HOSTS},
        "reciters": reciters,
    }

    write_json(out_dir / "reciters.json", index, pretty=pretty)
    return index


#: A fixed spread covering both padding schemes and every host: 1:1 (first), 2:255
#: (mid), 114:6 (last ayah, 6th), plus whole-surah files.
PROBE_URLS: tuple[tuple[str, str], ...] = (
    (
        f"{EVERYAYAH}/Alafasy_128kbps",
        "https://everyayah.com/data/Alafasy_128kbps/001001.mp3",
    ),
    (
        f"{EVERYAYAH}/Alafasy_128kbps",
        "https://everyayah.com/data/Alafasy_128kbps/002255.mp3",
    ),
    (
        f"{EVERYAYAH}/Abdul_Basit_Murattal_64kbps",
        "https://everyayah.com/data/Abdul_Basit_Murattal_64kbps/114006.mp3",
    ),
    (
        f"{ISLAMIC_NETWORK}/128/ar.alafasy",
        "https://cdn.islamic.network/quran/audio/128/ar.alafasy/6236.mp3",
    ),
    (
        f"{ISLAMIC_NETWORK}/surah/128/ar.alafasy",
        "https://cdn.islamic.network/quran/audio-surah/128/ar.alafasy/114.mp3",
    ),
    (f"{MP3QURAN}/1-1", "https://server6.mp3quran.net/akdr/001.mp3"),
    (f"{MP3QURAN}/1-1", "https://server6.mp3quran.net/akdr/114.mp3"),
)


def probe(fetcher: Fetcher | None = None) -> list[dict[str, Any]]:
    """HEAD a fixed sample of constructed audio URLs and report what the hosts answer."""
    owned = fetcher is None
    client = fetcher or Fetcher(delay=0.5)

    try:
        results = []
        for reciter, url in PROBE_URLS:
            response = client.head(url)
            results.append(
                {
                    "reciter": reciter,
                    "url": url,
                    "status": response.status_code,
                    "content_type": response.headers.get("content-type"),
                    "content_length": response.headers.get("content-length"),
                    "cors": response.headers.get("access-control-allow-origin"),
                }
            )
        return results
    finally:
        if owned:
            client.close()
