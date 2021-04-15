from enum import Enum

import typer

from changelog.cli.state import get_changelog, save_changelog

app = typer.Typer()


@app.callback()
def config():
    """Manage config encoded in changelog."""


class ConfigField(Enum):
    release_link_format = "release_link_format"
    breaking_change_token = "breaking_change_token"


@app.command()
def get(
    field: ConfigField = typer.Option(..., help="Config field to retrieve."),
):
    """Retrieve a config value from the changelog."""
    changelog = get_changelog()
    typer.echo(changelog.config.get(field.name, "not set"))


@app.command()
def set(
    field: ConfigField = typer.Option(..., help="Config field to set."),
    value: str = typer.Option(..., help="Value to set field to."),
):
    """Set a config value in the changelog."""
    changelog = get_changelog()
    changelog.config.set(field.name, value)
    save_changelog(changelog)
