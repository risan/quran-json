"""The publication licence gate.

An edition may only be published when its redistribution status is verified as
``granted``. This module is the single chokepoint that enforces that, so a future
"just add another language" change cannot quietly vendor a copyrighted translation.

Background: the frozen `dist/` tree ships Saheeh International under a licence label
that actually belongs to Tanzil's Arabic text. That is exactly the class of mistake this
gate exists to prevent -- see `data/meta/sources.json` for the per-edition evidence.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from . import config

__all__ = [
    "LicenseError",
    "blocked",
    "publishable_languages",
    "report",
    "require_publishable",
    "violation",
]


class LicenseError(RuntimeError):
    """Raised when a build would publish an edition without a redistribution grant."""


@dataclass(frozen=True, slots=True)
class Violation:
    """An edition withheld from publication, and why."""

    lang: str
    author: str
    status: config.Status
    license_url: str

    def __str__(self) -> str:
        return f"{self.lang}: {self.author} ({self.status}) -- {self.license_url}"


def violation(edition: config.Edition) -> Violation:
    """The record of one edition withheld for lack of a redistribution grant."""
    return Violation(
        lang=edition.lang,
        author=edition.author,
        status=edition.license.status,
        license_url=edition.license.url,
    )


def blocked(editions: Iterable[config.Edition] = config.REGISTERED) -> list[Violation]:
    """Editions whose licence is not verified as ``granted``.

    This is the registry view: an edition listed here is one a build refuses to publish
    *unless* it was published on an explicit override. `quranjson.cdn.build_site` reports
    what a given build actually held back, which differs once the override is in play.
    """
    return [violation(edition) for edition in editions if not edition.redistributable]


def require_publishable(
    languages: Iterable[str],
    editions: Iterable[config.Edition] = config.REGISTERED,
) -> None:
    """Raise if any requested language has no verified redistribution grant."""
    wanted = set(languages)
    offending = [violation for violation in blocked(editions) if violation.lang in wanted]

    if offending:
        listed = "\n  ".join(str(violation) for violation in offending)
        raise LicenseError(
            f"{len(offending)} edition(s) have no redistribution grant:\n  {listed}\n"
            "Pass --include-unverified-licenses only if you have cleared the rights yourself."
        )


def publishable_languages(
    editions: Iterable[config.Edition] = config.REGISTERED,
) -> tuple[str, ...]:
    """Languages safe to publish, in registry order."""
    return tuple(edition.lang for edition in editions if edition.redistributable)


def report(editions: Iterable[config.Edition] = config.REGISTERED) -> str:
    """A human-readable licence summary for the CLI."""
    lines = []
    for edition in editions:
        mark = "OK  " if edition.redistributable else "BLOCKED"
        lines.append(f"{mark} {edition.lang:<15} {edition.author:<42} {edition.license.url}")
    return "\n".join(lines)
