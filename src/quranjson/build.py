"""Assemble the published JSON artifacts.

`render_tree` is the general renderer; `build_tree` is the frozen-`dist/` entry point.
Output bytes are load-bearing: the frozen tree is a public contract served through
jsDelivr, so `build_tree` must reproduce it exactly (see `tests/test_parity.py`).
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import config
from .jsonio import read_json, write_json

__all__ = ["RenderOptions", "Sources", "build_tree", "render_tree"]


@dataclass(frozen=True, slots=True)
class RenderOptions:
    """What goes into a rendered tree.

    ``langs`` and ``verse_langs`` are separate because a language can appear as a
    whole-chapter translation while being excluded from the per-verse index.
    ``transliteration`` is a switch because the transliteration edition is licensed
    separately from the translations and is embedded into chapter and verse files.
    """

    link_base: str
    pretty: bool = False
    content: str = "legacy"
    langs: tuple[str | None, ...] = field(default=config.LANG_CODES)
    verse_langs: tuple[str, ...] = field(default=config.VERSE_LANGS)
    transliteration: bool = True

    def __post_init__(self) -> None:
        available = {lang for lang in self.langs if lang is not None}
        unknown = sorted(set(self.verse_langs) - available)

        if unknown:
            raise ValueError(f"verse_langs not among rendered langs: {unknown}")

        if config.TRANSLITERATION in self.verse_langs:
            raise ValueError("transliteration is not a verse-level translation language")

        if config.TRANSLITERATION in available and not self.transliteration:
            raise ValueError("transliteration cannot be rendered without its edition")


class Sources:
    """The committed snapshots the build reads from.

    ``content`` selects the generation: ``legacy`` reproduces the frozen `dist/` tree from
    the original snapshots, ``licensed`` uses the Tanzil text and QuranEnc translations
    whose grants actually cover redistribution.
    """

    def __init__(self, content: str = "legacy") -> None:
        self.content = content
        self.text: dict[str, list[dict[str, Any]]] = {}
        self.chapters: dict[str | None, list[dict[str, Any]]] = {}
        self.editions: dict[str, dict[str, list[dict[str, Any]]]] = {}

        if content == "licensed":
            self._load_licensed()
        elif content == "legacy":
            self._load_legacy()
        else:
            raise ValueError(f"unknown content generation: {content}")

    def _load_legacy(self) -> None:
        self.text = read_json(config.text_path())

        for lang in (*config.LANG_CODES, config.TRANSLITERATION):
            if lang is None:
                continue
            self.chapters[lang] = read_json(config.chapter_list_path(lang))
            self.editions[lang] = read_json(config.edition_path(lang))

        self.chapters[None] = self.chapters["en"]

    def _load_licensed(self) -> None:
        """Tanzil text and chapter metadata; QuranEnc translations keyed by catalogue key."""
        self.text = read_json(config.tanzil_text_path("uthmani"))

        chapters = read_json(config.tanzil_chapters_path())["chapters"]
        catalogue = read_json(config.quranenc_catalogue_path())["translations"]

        self.chapters = {None: chapters}

        for key in (entry["key"] for entry in catalogue):
            # Chapter names come from Tanzil and are identical across editions, so each
            # edition reuses the same list.
            self.chapters[key] = chapters
            self.editions[key] = read_json(config.quranenc_path(key))

        # Editions sourced outside QuranEnc (their own grant, own distribution).
        for edition in config.EXTRA_EDITIONS:
            self.chapters[edition.lang] = chapters
            self.editions[edition.lang] = read_json(config.extra_edition_path(edition.lang))

    def verses(self, chapter_id: int) -> list[dict[str, Any]]:
        return self.text[str(chapter_id)]


def _chapter(src: Sources, lang: str | None, item: dict[str, Any]) -> dict[str, Any]:
    """Build one chapter exactly as `generateQuran` did."""
    verses: list[dict[str, Any]] = []

    for idx, verse in enumerate(src.verses(item["id"])):
        entry: dict[str, Any] = {"id": verse["verse"], "text": verse["text"]}

        if lang is not None:
            key = "transliteration" if lang == config.TRANSLITERATION else "translation"
            edition = src.editions[lang][str(item["id"])][idx]
            entry[key] = edition["text"]

            # QuranEnc grants republication on condition of no deletion, so translator
            # footnotes travel with the verse when the source supplies them.
            if edition.get("footnotes"):
                entry["footnotes"] = edition["footnotes"]

        verses.append(entry)

    chapter: dict[str, Any] = {
        "id": item["id"],
        "name": item["name"],
        "transliteration": item["transliteration"],
    }

    if lang is not None:
        chapter["translation"] = item["translation"]

    chapter["type"] = item["type"]
    chapter["total_verses"] = item["total_verses"]
    chapter["verses"] = verses
    return chapter


def _merge_transliteration(
    chapter: dict[str, Any],
    transliteration_chapter: dict[str, Any],
) -> dict[str, Any]:
    """`qurans[].chapters[].verses[].transliteration` merge step."""
    merged = dict(chapter)
    merged["verses"] = [
        {**verse, "transliteration": transliteration_chapter["verses"][idx]["transliteration"]}
        for idx, verse in enumerate(chapter["verses"])
    ]
    return merged


def render_tree(out_dir: Path, options: RenderOptions) -> None:
    """Render every artifact into ``out_dir``, replacing whatever is there."""
    src = Sources(options.content)

    if out_dir.exists():
        shutil.rmtree(out_dir)

    quran_files: dict[str | None, list[dict[str, Any]]] = {
        lang: [_chapter(src, lang, item) for item in src.chapters[lang]] for lang in options.langs
    }

    if options.transliteration:
        transliteration = [
            _chapter(src, config.TRANSLITERATION, item)
            for item in src.chapters[config.TRANSLITERATION]
        ]
        write_json(out_dir / "quran_transliteration.json", transliteration, pretty=options.pretty)

        merged = {
            lang: [
                _merge_transliteration(chapter, transliteration[idx])
                for idx, chapter in enumerate(chapters)
            ]
            for lang, chapters in quran_files.items()
        }
    else:
        merged = quran_files

    for lang, chapters in quran_files.items():
        filename = "quran.json" if lang is None else f"quran_{lang}.json"
        write_json(out_dir / filename, chapters, pretty=options.pretty)

    _write_chapters(out_dir, merged, options)
    _write_verses(out_dir, merged, options)


def _write_chapters(
    out_dir: Path,
    merged: dict[str | None, list[dict[str, Any]]],
    options: RenderOptions,
) -> None:
    """`generateByChapter`: per-chapter files plus per-language indexes."""
    for lang, chapters in merged.items():
        prefix = "" if lang is None else f"{lang}/"

        for chapter in chapters:
            target = out_dir / "chapters" / f"{prefix}{chapter['id']}.json"
            write_json(target, chapter, pretty=options.pretty)

        index = []
        for chapter in chapters:
            entry = {key: value for key, value in chapter.items() if key != "verses"}
            entry["link"] = f"{options.link_base}{prefix}{chapter['id']}.json"
            index.append(entry)

        write_json(out_dir / "chapters" / f"{prefix}index.json", index, pretty=options.pretty)


def _write_verses(
    out_dir: Path,
    merged: dict[str | None, list[dict[str, Any]]],
    options: RenderOptions,
) -> None:
    """`generateByVerses`: the global 1..6236 verse files carrying every translation."""
    base = merged[None]
    translations = [(lang, merged[lang]) for lang in options.verse_langs]

    verse_id = 1

    for chapter_idx, chapter in enumerate(base):
        for chapter_verse_idx, verse in enumerate(chapter["verses"]):
            entry: dict[str, Any] = {
                "id": verse_id,
                "number": verse["id"],
                "text": verse["text"],
                "translations": {
                    lang: chapters[chapter_idx]["verses"][chapter_verse_idx]["translation"]
                    for lang, chapters in translations
                },
            }

            if "transliteration" in verse:
                entry["transliteration"] = verse["transliteration"]

            entry["chapter"] = {
                "id": chapter["id"],
                "name": chapter["name"],
                "transliteration": chapter["transliteration"],
                "translations": {
                    lang: chapters[chapter_idx]["translation"] for lang, chapters in translations
                },
                "type": chapter["type"],
            }

            write_json(out_dir / "verses" / f"{verse_id}.json", entry, pretty=options.pretty)
            verse_id += 1


def build_tree(
    out_dir: Path,
    *,
    link_base: str = config.DEFAULT_LINK_BASE,
    version: str = config.LEGACY_VERSION,
    pretty: bool = False,
    legacy_verse_langs: bool = True,
) -> None:
    """Render the frozen `dist/` tree, reproducing the upstream build byte-for-byte."""
    render_tree(
        out_dir,
        RenderOptions(
            link_base=link_base.format(version=version),
            pretty=pretty,
            langs=config.LANG_CODES,
            verse_langs=config.LEGACY_VERSE_LANGS if legacy_verse_langs else config.VERSE_LANGS,
            transliteration=True,
        ),
    )
