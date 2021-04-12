from enum import Enum
from typing import Optional

import typer

from changelog.model import Bump, ChangeType
from changelog.parser import load_from_file
from changelog.renderer import dump_to_file

app = typer.Typer()


@app.command()
def validate(path: str = typer.Option("CHANGELOG.md", "--path", "-p", help="Path to changelog.")):
    """Parse and validate the changelog."""
    load_from_file(path=path)


@app.command()
def format(path: str = typer.Option("CHANGELOG.md", "--path", "-p", help="Path to changelog.")):
    """Parse, validate and format the changelog."""
    dump_to_file(load_from_file(path=path), path=path)


class ReleaseTypeOption(Enum):
    major = "major"
    minor = "minor"
    patch = "patch"
    auto = "auto"


@app.command()
def release(
    path: str = typer.Option("CHANGELOG.md", "--path", "-p", help="Path to changelog."),
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
    changelog = load_from_file(path=path)
    force = {
        ReleaseTypeOption.major: Bump.MAJOR,
        ReleaseTypeOption.minor: Bump.MINOR,
        ReleaseTypeOption.patch: Bump.PATCH,
        ReleaseTypeOption.auto: None,
    }[bump]
    changelog.cut_release(force=force, tag=tag)
    dump_to_file(changelog, path=path)


@app.command()
def entry(
    change_type: str = typer.Argument(...),
    message: list[str] = typer.Option(..., "--message", "-m", help="Message describing changelog entry."),
    path: str = typer.Option("CHANGELOG.md", "--path", "-p", help="Path to changelog."),
    breaking: bool = typer.Option(False, "--breaking", "-b", help="Mark this change as a breaking change."),
    tag: str = typer.Option("auto", "--tag", "-t", help="Specify the release tag for this entry. Will add to unreleased tag by default.")
):
    """Add a new entry to the changelog."""
    changelog = load_from_file(path=path)
    changelog.add_entry(change_type.title(), *message, breaking=breaking)
    dump_to_file(changelog, path=path)


if __name__ == "__main__":
    app()
