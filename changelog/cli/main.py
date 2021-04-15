from enum import Enum
from pathlib import Path
from typing import Optional, cast

import typer

from changelog import __version__
from changelog.cli.constants import default_changelog
from changelog.cli.state import get_changelog, global_options, save_changelog
from changelog.exceptions import ChangelogMissingConfigError
from changelog.model import Bump, ChangeType

app = typer.Typer()


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
    ),
):
    """A tool for managing a changelog in the style of 'Keep a Changelog'.

    http://keepachangelog.com/en/1.0.0/
    """
    if path:
        global_options()["path"] = path


_RELEASE_LINK_DESCRIPTION = """For example:

"https://github.com/user/repo/compare/{previous_tag}..{tag}"

Optionally may contain the following vars for substitution:

{tag},{previous_tag}

"""


@app.command()
def init(
    force: bool = typer.Option(False, help="If set, override any existing file at target location."),
    release_link_format: str = typer.Option(
        ...,
        prompt=f"Please specify the format for release links. {_RELEASE_LINK_DESCRIPTION}",
        help=f"Format string for release links. {_RELEASE_LINK_DESCRIPTION}",
    ),
    breaking_change_token: str = typer.Option("BREAKING", help="Token used to indicate breaking changes."),
):
    path = Path(global_options()["path"])
    if not force and path.exists():
        typer.secho(
            f"Path {path.absolute()} already exists. Aborting.",
            fg="red",
        )
        raise typer.Exit(1)

    save_changelog(
        default_changelog(release_link_format=release_link_format, breaking_change_token=breaking_change_token)
    )
    typer.secho(f"Changelog initialised at '{path.absolute()}'", fg="green")


@app.command()
def validate():
    """Parse and validate the changelog."""
    get_changelog()


@app.command()
def format():
    """Parse, validate and format the changelog."""
    save_changelog(get_changelog())


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
    changelog = get_changelog()
    force = {
        ReleaseTypeOption.major: Bump.MAJOR,
        ReleaseTypeOption.minor: Bump.MINOR,
        ReleaseTypeOption.patch: Bump.PATCH,
        ReleaseTypeOption.auto: None,
    }[bump]
    try:
        changelog.cut_release(force=force, tag=tag)
    except ChangelogMissingConfigError as exc:
        typer.secho(
            f"""
ERROR: Could not create release due to missing config: {exc.field!r}.

Run the following before cutting a release:
    changelog --path {global_options()['path']} config set --field {exc.field} --value VALUE
""",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)
    save_changelog(changelog)


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
    changelog = get_changelog()
    changelog.add_entry(cast(ChangeType, change_type.title()), *message, breaking=breaking, tag=tag)
    save_changelog(changelog)
