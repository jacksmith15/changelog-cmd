import os
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from shutil import copyfile

import pytest
from typer.testing import CliRunner

from changelog import __version__, load_from_file
from changelog.__main__ import app
from changelog.model import Entry, Version


runner = CliRunner()


@contextmanager
def override_env(key: str, value: str) -> Iterator[None]:
    original = os.getenv(key, None)
    os.environ[key] = value
    try:
        yield
    finally:
        if original:
            os.environ[key] = original
            return
        del os.environ[key]


@pytest.fixture()
def changelog_path() -> str:
    target = "tests/cli/outputs/CHANGELOG.md"
    copyfile("tests/changelogs/initial_changelog.md", target)
    try:
        yield target
    finally:
        os.remove(target)


def test_it_displays_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout == f"changelog version {__version__}\n"


def test_it_validates_a_valid_changelog(changelog_path: str):
    result = runner.invoke(app, ["--path", changelog_path, "validate"])
    assert result.exit_code == 0


def test_it_validates_an_invalid_changelog(changelog_path: str):
    with open(changelog_path, "a") as file:
        file.write("Under-indented text")
    result = runner.invoke(app, ["--path", changelog_path, "validate"])
    assert result.exit_code == 1


def test_it_formats_a_changelog(changelog_path: str):
    with open(changelog_path, "r") as file:
        content = file.read()
    # Add lots more whitespace
    with open(changelog_path, "w") as file:
        file.write(content + "\n" * 100)
    result = runner.invoke(app, ["--path", changelog_path, "format"])
    assert result.exit_code == 0
    with open(changelog_path, "r") as file:
        output = file.read()
    assert output == content


@pytest.mark.parametrize("path_mode", ["option", "environment"])
def test_it_adds_an_entry(changelog_path: str, path_mode: str):
    if path_mode == "option":
        result = runner.invoke(
            app, ["--path", changelog_path, "entry", "added", "-m", "A new feature", "-m", "More details"]
        )
    else:
        with override_env("CHANGELOG_PATH", changelog_path):
            result = runner.invoke(app, ["entry", "added", "-m", "A new feature", "-m", "More details"])
    assert result.exit_code == 0
    changelog = load_from_file(changelog_path)
    assert changelog.versions[Version("Unreleased")].entries["Added"][-1] == Entry(
        "A new feature", sub_entries=[Entry("More details")]
    )


def test_it_cuts_first_release_with_default_options(changelog_path: str):
    result = runner.invoke(app, ["--path", changelog_path, "release"])
    assert result.exit_code == 0
    changelog = load_from_file(changelog_path)
    assert list(changelog.versions) == ["Unreleased", "0.1.0"]
    assert {"Unreleased", "0.1.0"} <= set(changelog.links)
    assert not changelog.versions[Version("Unreleased")].entries
    assert changelog.versions[Version("0.1.0")].entries["Added"] == [Entry("Project started :)")]
    assert changelog.versions[Version("0.1.0")].timestamp == date.today().isoformat()


def test_it_cuts_a_release_with_a_specific_tag(changelog_path: str):
    result = runner.invoke(app, ["--path", changelog_path, "release", "--tag", "1.0.0"])
    assert result.exit_code == 0
    changelog = load_from_file(changelog_path)
    assert list(changelog.versions) == ["Unreleased", "1.0.0"]
    assert {"Unreleased", "1.0.0"} <= set(changelog.links)
    assert not changelog.versions[Version("Unreleased")].entries
    assert changelog.versions[Version("1.0.0")].entries["Added"] == [Entry("Project started :)")]
    assert changelog.versions[Version("1.0.0")].timestamp == date.today().isoformat()


@pytest.mark.parametrize(
    "change_type",
    [
        "added",
        "removed",
        "fixed",
    ],
)
@pytest.mark.parametrize(
    "breaking_change",
    [
        True,
        False,
    ],
)
@pytest.mark.parametrize(
    "initial_version",
    [
        "0.1.0",
        "1.0.0",
    ],
)
def test_it_cuts_a_release_with_auto_version(
    changelog_path: str, change_type: str, breaking_change: bool, initial_version: str
):
    # GIVEN the previous release is `initial_version`
    assert not runner.invoke(app, ["--path", changelog_path, "release", "--tag", initial_version]).exit_code
    # AND the unreleased section contains an entry
    assert not runner.invoke(
        app, ["--path", changelog_path, "entry", change_type, "--message", "Some stuff"] + (["--breaking"] if breaking_change else [])
    ).exit_code
    # WHEN the release command is run
    result = runner.invoke(app, ["--path", changelog_path, "release"])
    # THEN the command exits successfully
    assert not result.exit_code
    # AND the changelog has the correct latest version
    changelog = load_from_file(changelog_path)
    if breaking_change and initial_version == "1.0.0":
        expected = "2.0.0"
    else:
        if change_type == "fixed":
            expected = {
                "0.1.0": "0.1.1",
                "1.0.0": "1.0.1",
            }[initial_version]
        else:
            expected = {
                "0.1.0": "0.2.0",
                "1.0.0": "1.1.0",
            }[initial_version]
    assert changelog.latest_version == expected


def test_it_cuts_a_release_with_specific_bump(
    changelog_path: str,
):
    # GIVEN the previous release is 0.1.0
    assert not runner.invoke(app, ["--path", changelog_path, "release", "--tag", "0.1.0"]).exit_code
    # AND the unreleased section contains a new feature
    assert not runner.invoke(
        app, ["--path", changelog_path, "entry", "added", "--message", "Some stuff"]
    ).exit_code
    # WHEN the release command is run specifying a major version bump
    result = runner.invoke(app, ["--path", changelog_path, "release", "--bump", "major"])
    # THEN the command exits successfully
    assert not result.exit_code
    # AND the changelog has the correct latest version
    changelog = load_from_file(changelog_path)
    assert changelog.latest_version == "1.0.0"
