"""Command line interface for the dataset build pipeline."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from . import audio, config, sources
from .cdn import build_site

app = typer.Typer(add_completion=False, help="Build and verify the quran-json dataset.")


@app.callback()
def _group() -> None:
    """Build and verify the quran-json dataset."""


@app.command()
def cdn(
    out: Annotated[Path, typer.Option("--out", "-o", help="Site output directory.")] = config.CDN,
    pretty: Annotated[bool, typer.Option("--pretty", help="Indent output by two spaces.")] = False,
    audio_enabled: Annotated[
        bool, typer.Option("--audio/--no-audio", help="Include the audio reciter index.")
    ] = True,
) -> None:
    """Render the site deployed to Cloudflare Workers."""
    build_site(out, pretty=pretty, audio=audio_enabled)
    typer.echo(f"built site {out}")


@app.command()
def fetch(
    force: Annotated[
        bool, typer.Option("--force", help="Re-download snapshots that already exist.")
    ] = False,
    check: Annotated[
        bool,
        typer.Option(
            "--check",
            help="Compare upstream with the committed snapshots without writing; "
            "exit 1 if any differ.",
        ),
    ] = False,
) -> None:
    """Refresh the committed upstream snapshots and the provenance manifest."""
    if check:
        findings = sources.check_all()

        for finding in findings:
            typer.echo(finding)

        if findings:
            raise typer.Exit(code=1)

        typer.echo("upstream matches the committed snapshots")
        return

    records = sources.fetch_all(force=force)
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
