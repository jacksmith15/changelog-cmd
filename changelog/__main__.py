import os
from enum import Enum
from functools import cached_property
from typing import Optional, cast

import typer

from changelog import __version__
from changelog.model import Bump, ChangeType
from changelog.parser import load_from_file
from changelog.renderer import dump_to_file


class App(typer.Typer):
    @cached_property
    def state(self):
        return {"path": os.getenv("CHANGELOG_PATH", "CHANGELOG.md")}


app = App()


def version_callback(value: bool):
    if value:
        typer.echo(f"changelog version {__version__}")
        raise typer.Exit(0)


@app.callback()
def main(
    path: str = typer.Option(
        None,
        "--path",
        "-p",
        help="Path to changelog. Defaults to the CHANGELOG_PATH env var if present, otherwise 'CHANGELOG.md'",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Display CLI version and exit.",
        callback=version_callback,
        is_eager=True,
    )
):
    """A tool for managing a changelog in the style of 'Keep a Changelog'.

    http://keepachangelog.com/en/1.0.0/
    """
    if path:
        app.state["path"] = path


@app.command()
def validate():
    """Parse and validate the changelog."""
    load_from_file(path=app.state["path"])


@app.command()
def format():
    """Parse, validate and format the changelog."""
    dump_to_file(load_from_file(path=app.state["path"]), path=app.state["path"])


class ReleaseTypeOption(Enum):
    major = "major"
    minor = "minor"
    patch = "patch"
    auto = "auto"


@app.command()
def release(
    bump: ReleaseTypeOption = typer.Option(
        "auto",
        "--bump",
        "-b",
        help=(
            "Type of release bump. Infers from changelog entries by default. Requires that semantic "
            "versioning is being used."
        ),
    ),
    tag: Optional[str] = typer.Option(
        None,
        "--tag",
        "-t",
        help=(
            "Manually provide the new release tag. Necessary if semantic versioning is not being used, "
            "but otherwise not recommended."
        ),
    ),
):
    """Move the unreleased entries in the changelog to a new release tag."""
    changelog = load_from_file(path=app.state["path"])
    force = {
        ReleaseTypeOption.major: Bump.MAJOR,
        ReleaseTypeOption.minor: Bump.MINOR,
        ReleaseTypeOption.patch: Bump.PATCH,
        ReleaseTypeOption.auto: None,
    }[bump]
    changelog.cut_release(force=force, tag=tag)
    dump_to_file(changelog, path=app.state["path"])


@app.command()
def entry(
    change_type: str = typer.Argument(...),
    message: list[str] = typer.Option(..., "--message", "-m", help="Message describing changelog entry."),
    breaking: bool = typer.Option(False, "--breaking", "-b", help="Mark this change as a breaking change."),
    tag: Optional[str] = typer.Option(
        None, "--tag", "-t", help="Specify the release tag for this entry. Will add to unreleased tag by default."
    ),
):
    """Add a new entry to the changelog."""
    changelog = load_from_file(path=app.state["path"])
    changelog.add_entry(cast(ChangeType, change_type.title()), *message, breaking=breaking, tag=tag)
    dump_to_file(changelog, path=app.state["path"])


if __name__ == "__main__":
    app()
