"""Dev-only cross-checks of the generated romanisation. Needs the network; never run in CI.

    uv run python scripts/romanize_crosscheck.py english
    uv run --with quranic-phonemizer python scripts/romanize_crosscheck.py phonemes
    uv run --with quranic-phonemizer python scripts/romanize_crosscheck.py baselines

english
    Downloads Tanzil's `en.transliteration` to `.cache/` (git-ignored, never committed) and
    prints the skeleton error rate of the `en` renderer against it. A skeleton keeps the
    consonants and the vowel lengths and drops everything the two spellings disagree on.

phonemes
    Compares the phone stream with the independent QUD `quranic-phonemizer` (MIT), per verse,
    with nasals dropped from both sides (their tajweed nasal symbols are not ours) and
    gemination ignored. Prints the verse agreement and the phone error rate. The package is
    not a project dependency: `uv run --with` fetches it for the one run.

baselines
    Rewrites the two committed lists the tests read: the verses the Kemenag Latin disagrees
    on while our phones agree with the engine (`romanize_reference_witness.txt`), and the
    generator gaps (`romanize_generator_gaps.txt`). Review the diff before committing.
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from quranjson import romanize
from quranjson import romanize_validation as validation

CACHE = Path(__file__).resolve().parents[1] / ".cache"
TANZIL_URL = "https://tanzil.net/trans/?transID=en.transliteration&type=txt-2"
ALQURAN_CLOUD_URL = "https://api.alquran.cloud/v1/quran/en.transliteration"

OUR_PHONES = {
    "A": "a:",
    "I": "i:",
    "U": "u:",
    "E": "i:",
    "th": "θ",
    "j": "ʒ",
    "H": "ħ",
    "kh": "x",
    "dh": "ð",
    "sh": "ʃ",
    "S": "sˤ",
    "D": "dˤ",
    "T": "tˤ",
    "Z": "ðˤ",
    "`": "ʕ",
    "gh": "ɣ",
    "y": "j",
    "'": "ʔ",
    romanize.TA_MARBUTA: "t",
    romanize.PLURAL_WAW: "w",
}
ENGINE_PHONES = {
    "ŋ": "n",
    "ñ": "n",
    "m̃": "m",
    "j̃": "j",
    "w̃": "w",
    "aˤ": "a",
    "aˤ:": "a:",
    "lˤ": "l",
    "rˤ": "r",
    "ŋˤ": "n",
}
NASALS = frozenset({"n", "m"})


# -- English: Tanzil ----------------------------------------------------------------------


def fetch_tanzil() -> dict[tuple[int, int], str]:
    CACHE.mkdir(exist_ok=True)
    cached = CACHE / "tanzil-en-transliteration.txt"

    if not cached.exists():
        try:
            cached.write_text(httpx.get(TANZIL_URL, timeout=60).text, encoding="utf-8")
        except httpx.HTTPError as error:
            print(f"tanzil.net failed ({error!r}); trying alquran.cloud", file=sys.stderr)

            return fetch_alquran_cloud()

    verses: dict[tuple[int, int], str] = {}

    for line in cached.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^(\d+)\|(\d+)\|(.*)$", line)

        if match:
            verses[(int(match[1]), int(match[2]))] = match[3]

    return verses


def fetch_alquran_cloud() -> dict[tuple[int, int], str]:
    CACHE.mkdir(exist_ok=True)
    cached = CACHE / "alquran-cloud-en-transliteration.json"

    if not cached.exists():
        cached.write_text(httpx.get(ALQURAN_CLOUD_URL, timeout=120).text, encoding="utf-8")

    payload = json.loads(cached.read_text(encoding="utf-8"))
    verses: dict[tuple[int, int], str] = {}

    for surah in payload["data"]["surahs"]:
        for ayah in surah["ayahs"]:
            verses[(surah["number"], ayah["numberInSurah"])] = ayah["text"]

    return verses


def run_english() -> None:
    reference = fetch_tanzil()
    snapshot = validation.load_snapshot()
    pairs: list[tuple[str, str]] = []
    identical = 0

    for chapter, verse, record in romanize.iter_verses(snapshot):
        theirs = reference.get((chapter, verse))

        if theirs is None:
            continue

        ours = romanize.romanize_verse(record["text"], "en", chapter=chapter, verse=verse)
        pairs.append((theirs, ours))
        identical += validation.skeleton(theirs) == validation.skeleton(ours)

    rate = validation.skeleton_error_rate(pairs)
    print(f"verses compared: {len(pairs)}")
    print(f"identical skeletons: {identical} ({identical / len(pairs):.1%})")
    print(f"skeleton error rate: {rate:.2%}")


# -- Phonemes: QUD quranic-phonemizer -----------------------------------------------------


def our_sequence(text: str) -> list[str]:
    return [OUR_PHONES.get(phone, phone) for phone in validation.connected_phones(text)]


def engine_sequence(result: Any) -> list[str]:
    sequence: list[str] = []

    for phone in result.phonemes():
        if phone == "Q":
            continue

        light = phone.replace("lˤ", "l").replace("rˤ", "r")
        phone = ENGINE_PHONES.get(light, light)
        phone = re.sub(r":+", ":", phone)
        half = len(phone) // 2

        if half and phone[:half] == phone[half:] and not phone.endswith(":"):
            sequence += [phone[:half]] * 2
        else:
            sequence.append(phone)

    return sequence


def comparable(sequence: Sequence[str], *, drop_nasals: bool) -> list[str]:
    """Doubled consonants collapsed, and nasals dropped if asked.

    The two engines mark gemination differently, and the engine writes tajweed nasalisation
    (ikhfa, iqlab) with symbols of its own that cannot be mapped one to one onto n and m.
    """
    result: list[str] = []

    for phone in sequence:
        if drop_nasals and phone in NASALS:
            continue

        if result and phone == result[-1] and not phone.endswith(":") and phone not in "aiu":
            continue

        result.append(phone)

    return result


def compare_with_engine() -> dict[str, bool]:
    from quranic_phonemizer import Phonemizer  # type: ignore[import-not-found]

    engine = Phonemizer()
    snapshot = validation.load_snapshot()
    agreement: dict[str, bool] = {}
    strict_edits = strict_exact = edits = length = strict_length = 0

    for chapter, verse, record in romanize.iter_verses(snapshot):
        ours = our_sequence(record["text"])
        theirs = engine_sequence(engine.analyse(f"{chapter}:{verse}"))
        strict_ours = comparable(ours, drop_nasals=False)
        strict_theirs = comparable(theirs, drop_nasals=False)
        distance = validation.edit_distance(strict_theirs, strict_ours)
        strict_edits += distance
        strict_exact += distance == 0
        strict_length += len(strict_theirs)

        blind_ours = comparable(ours, drop_nasals=True)
        blind_theirs = comparable(theirs, drop_nasals=True)
        distance = validation.edit_distance(blind_theirs, blind_ours)
        edits += distance
        length += len(blind_theirs)
        agreement[f"{chapter}:{verse}"] = distance == 0

    verses = len(agreement)
    agreeing = sum(agreement.values())
    print(f"verses: {verses}")
    print(
        f"with nasals:    {strict_exact} identical ({strict_exact / verses:.1%}), "
        f"phone error rate {strict_edits / strict_length:.3%}"
    )
    print(
        f"without nasals: {agreeing} identical ({agreeing / verses:.1%}), "
        f"phone error rate {edits / length:.3%}"
    )

    return agreement


def run_baselines(agreement: Mapping[str, bool]) -> None:
    snapshot = validation.load_snapshot()
    witness: dict[str, str] = {}
    gaps: list[str] = []

    for mismatch in validation.mismatches(snapshot, witness={}):
        if mismatch.category != validation.Class.GENERATOR_GAP:
            continue

        if agreement[mismatch.key]:
            record = snapshot[str(mismatch.chapter)][mismatch.verse - 1]
            witness[mismatch.key] = validation.phone_digest(record["text"])
        else:
            gaps.append(mismatch.key)

    witness_lines = [f"{key} {digest}" for key, digest in witness.items()]
    validation.WITNESS_PATH.write_text(
        "# Verses where the Kemenag Latin differs and the QUD engine agrees with our phones.\n"
        "# Regenerate with scripts/romanize_crosscheck.py baselines.\n"
        + "\n".join(witness_lines)
        + "\n",
        encoding="utf-8",
    )
    validation.GAPS_PATH.write_text(
        "# Verses in the generator-gap class. A verse not listed here must not enter it.\n"
        + "\n".join(gaps)
        + "\n",
        encoding="utf-8",
    )
    print(f"witness: {len(witness)} verses; generator gaps: {len(gaps)}")


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else "english"

    if command == "english":
        run_english()
    elif command == "phonemes":
        compare_with_engine()
    elif command == "baselines":
        run_baselines(compare_with_engine())
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
