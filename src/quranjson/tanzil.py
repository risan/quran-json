"""Tanzil.net as the Arabic text and chapter-metadata source.

Tanzil is the only source found whose grant covers verbatim redistribution explicitly
(CC-BY 3.0), which is why the licensed dataset generation uses it rather than the
re-encoded derivative the frozen `dist/` tree was built from.

Two notes that matter to consumers:

* Tanzil embeds the basmala at the head of the **first ayah of every surah except
  At-Tawbah**, rather than treating it as chapter metadata. The shipped text did not.
* The text is standard Uthmani orthography (Arabic Yeh U+064A, sukun U+0652), unlike the
  Farsi Yeh (U+06CC) / U+06E1 style of the frozen tree.
"""

from __future__ import annotations

import re
from typing import Any
from xml.etree import ElementTree

from . import config

__all__ = ["TEXT_VARIANTS", "parse_metadata", "parse_text", "text_url"]

#: Tanzil's download endpoint accepts these `quranType` values.
TEXT_VARIANTS = (
    "uthmani",
    "uthmani-min",
    "simple",
    "simple-plain",
    "simple-min",
    "simple-clean",
)

METADATA_URL = "https://tanzil.net/res/text/metadata/quran-data.xml"

_LINE = re.compile(r"^(\d+)\|(\d+)\|(.+)$")

#: Tanzil spells the revelation place in title case; the dataset uses lower case.
_PLACE = {"meccan": "meccan", "medinan": "medinan"}


def text_url(variant: str) -> str:
    """Download URL for one Tanzil text variant."""
    if variant not in TEXT_VARIANTS:
        raise ValueError(f"unknown Tanzil text variant: {variant}")
    return config.TANZIL_DOWNLOAD.format(variant=variant)


def parse_text(raw: bytes) -> dict[str, list[dict[str, Any]]]:
    """Parse Tanzil's `sura|aya|text` export into `{chapter: [{chapter, verse, text}]}`.

    Comment lines (leading `#`) carry the licence banner and are skipped.
    """
    chapters: dict[str, list[dict[str, Any]]] = {}

    for line in raw.decode("utf-8").splitlines():
        if not line or line.startswith("#"):
            continue

        match = _LINE.match(line)
        if match is None:
            raise ValueError(f"unexpected Tanzil line: {line[:60]!r}")

        sura, aya, text = match.groups()
        chapters.setdefault(sura, []).append(
            {"chapter": int(sura), "verse": int(aya), "text": text}
        )

    return chapters


def parse_metadata(raw: bytes) -> dict[str, Any]:
    """Parse Tanzil's `quran-data.xml` into chapter metadata plus structural indexes."""
    root = ElementTree.fromstring(raw)

    sura_node = root.find("suras")
    if sura_node is None:
        raise ValueError("quran-data.xml has no <suras> section")

    chapters = [
        {
            "id": int(sura.attrib["index"]),
            "name": sura.attrib["name"],
            "transliteration": sura.attrib["tname"],
            "translation": sura.attrib["ename"],
            "type": _PLACE[sura.attrib["type"].lower()],
            "total_verses": int(sura.attrib["ayas"]),
        }
        for sura in sura_node.findall("sura")
    ]

    indexes: dict[str, list[dict[str, Any]]] = {}

    for group in ("juzs", "hizbs", "pages", "sajdas"):
        node = root.find(group)
        indexes[group] = [
            {key: (int(value) if value.isdigit() else value) for key, value in child.attrib.items()}
            for child in (node if node is not None else [])
        ]

    return {"chapters": chapters, "indexes": indexes}
