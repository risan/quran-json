"""Command line interface for the dataset build pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from . import audio, config, licensing, review, sources
from .build import build_tree
from .cdn import build_site

app = typer.Typer(add_completion=False, help="Build and verify the quran-json dataset.")


@app.callback()
def _group() -> None:
    """Build and verify the quran-json dataset."""


@app.command()
def build(
    out: Annotated[Path, typer.Option("--out", "-o", help="Output directory.")] = config.DIST,
    link_base: Annotated[
        str,
        typer.Option(
            "--link-base",
            help="Prefix for the `link` field in chapter indexes ({version} is substituted).",
        ),
    ] = config.DEFAULT_LINK_BASE,
    version: Annotated[
        str, typer.Option("--version", help="Version used in generated links.")
    ] = config.LEGACY_VERSION,
    pretty: Annotated[bool, typer.Option("--pretty", help="Indent output by two spaces.")] = False,
    legacy_verse_langs: Annotated[
        bool,
        typer.Option(
            "--legacy-verse-langs/--no-legacy-verse-langs",
            help="Reproduce the upstream bug that omits `bn` from verse files. On by default: "
            "the default output IS the published dist/ tree.",
        ),
    ] = True,
) -> None:
    """Render the frozen dist/ tree. Defaults reproduce the published bytes exactly."""
    build_tree(
        out,
        link_base=link_base,
        version=version,
        pretty=pretty,
        legacy_verse_langs=legacy_verse_langs,
    )
    typer.echo(f"built {out}")


@app.command()
def cdn(
    out: Annotated[Path, typer.Option("--out", "-o", help="Site output directory.")] = config.CDN,
    pretty: Annotated[bool, typer.Option("--pretty", help="Indent output by two spaces.")] = False,
    include_unverified_licenses: Annotated[
        bool,
        typer.Option(
            "--include-unverified-licenses",
            help="Publish editions whose redistribution status is not verified as granted. "
            "Only use this once you have cleared the rights yourself.",
        ),
    ] = False,
    audio_enabled: Annotated[
        bool, typer.Option("--audio/--no-audio", help="Include the audio reciter index.")
    ] = True,
) -> None:
    """Render the site deployed to Cloudflare Workers."""
    withheld = build_site(
        out,
        pretty=pretty,
        include_unverified_licenses=include_unverified_licenses,
        audio=audio_enabled,
    )

    for violation in withheld:
        typer.echo(f"withheld (no redistribution grant): {violation}")

    typer.echo(f"built site {out}")


@app.command()
def licenses(
    write: Annotated[
        bool,
        typer.Option("--write", help="Also refresh data/meta/licensing-review.json."),
    ] = False,
) -> None:
    """Print the redistribution status of every edition and audio host."""
    typer.echo(licensing.report())
    typer.echo("")
    typer.echo("audio hosts:")
    for host, spec in audio.AUDIO_HOSTS.items():
        license_ = spec["license"]
        typer.echo(f"{license_.status:<11} {host:<17} {license_.url}")

    typer.echo("")
    typer.echo("transliteration candidates (none publishable yet):")
    for entry in review.CANDIDATES:
        if entry.kind == "transliteration":
            typer.echo(f"{entry.status:<11} {entry.name}")
            if entry.blocker:
                typer.echo(f"            blocker: {entry.blocker}")

    if write:
        from .jsonio import write_json

        target = config.DATA / "meta" / "licensing-review.json"
        write_json(target, review.review_manifest(), pretty=True)
        typer.echo(f"wrote {target.relative_to(config.ROOT)}")


@app.command()
def fetch(
    force: Annotated[
        bool, typer.Option("--force", help="Re-download snapshots that already exist.")
    ] = False,
    lang: Annotated[
        list[str] | None, typer.Option("--lang", help="Limit to these languages.")
    ] = None,
) -> None:
    """Refresh the committed upstream snapshots and the provenance manifest."""
    records = sources.fetch_all(force=force, langs=tuple(lang) if lang else None)
    typer.echo(f"manifest covers {len(records)} snapshots")


@app.command()
def verify() -> None:
    """Check snapshot provenance and hashes."""
    problems = sources.verify_snapshots()

    for problem in problems:
        typer.echo(f"FAIL {problem}", err=True)

    if problems:
        raise typer.Exit(code=1)

    typer.echo("provenance ok")


@app.command()
def probe() -> None:
    """Check a fixed sample of constructed audio URLs against the live hosts."""
    for result in audio.probe():
        typer.echo(
            f"{result['status']} {result['reciter']:<42} "
            f"{result['content_length'] or '-':>10}  cors={result['cors']}  {result['url']}"
        )


def main() -> None:
    app()


if __name__ == "__main__":
    main()
