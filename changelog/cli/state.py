import os
from functools import cache

import typer

from changelog import dump_to_file, load_from_file
from changelog.exceptions import ChangelogParseError, ChangelogValidationError
from changelog.model import Changelog


@cache
def global_options():
    return {"path": os.getenv("CHANGELOG_PATH", "CHANGELOG.md")}


def get_changelog() -> Changelog:
    path = global_options()["path"]
    try:
        changelog = load_from_file(path=path)
    except (ChangelogParseError, ChangelogValidationError) as exc:
        typer.secho(
            f"""
ERROR: Could not parse changelog: {str(exc)}""",
            fg="red",
        )
        raise typer.Exit(1)
    return changelog


def save_changelog(changelog: Changelog):
    path = global_options()["path"]
    dump_to_file(changelog, path=path)
