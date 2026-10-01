"""The publication licence gate.

An edition may only be published when its redistribution status is verified as
``granted``. This module is the single chokepoint that enforces that, so a future
"just add another language" change cannot quietly vendor a copyrighted translation.
See `data/meta/sources.json` for the per-edition evidence.
"""

from __future__ import annotations

from collections.abc import Iterable

from . import config

__all__ = ["LicenseError", "require_publishable"]


class LicenseError(RuntimeError):
    """Raised when a build would publish an edition without a redistribution grant."""


def require_publishable(editions: Iterable[config.Edition]) -> None:
    """Raise if any edition has no verified redistribution grant."""
    offending = [edition for edition in editions if not edition.redistributable]

    if offending:
        listed = "\n  ".join(
            f"{edition.lang}: {edition.author} ({edition.license.status}) -- {edition.license.url}"
            for edition in offending
        )
        raise LicenseError(f"{len(offending)} edition(s) have no redistribution grant:\n  {listed}")
