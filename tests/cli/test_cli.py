import os
import traceback
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from shutil import copyfile

import pytest
from typer.testing import CliRunner, Result

from changelog import __version__, load_from_file
from changelog.__main__ import app
from changelog.model import Entry, ReleaseTag


runner = CliRunner()


def assert_exit_code(result: Result, exit_code: int = 0) -> None:
    exception_message = None
    if result.exception:
        exception_message = "\n".join(
            traceback.format_exception(type(result.exception), result.exception, result.exception.__traceback__)
        )
    assert (
        result.exit_code == exit_code
    ), f"""Expected exit code {exit_code}, got {result.exit_code}

{result.output or exception_message}

"""


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
def changelog_path() -> Iterator[str]:
    target = "tests/cli/outputs/CHANGELOG.md"
    copyfile("tests/changelogs/initial_changelog.md", target)
    try:
        yield target
    finally:
        os.remove(target)


def test_it_displays_version():
    result = runner.invoke(app, ["--version"])
    assert_exit_code(result)
    assert result.stdout == f"changelog version {__version__}\n"


def test_it_validates_a_valid_changelog(changelog_path: str):
    result = runner.invoke(app, ["--path", changelog_path, "validate"])
    assert_exit_code(result)


def test_it_fails_to_validate_empty_changelog(changelog_path: str):
    with open(changelog_path, "w") as file:
        file.write("")
    result = runner.invoke(app, ["--path", changelog_path, "validate"])
    assert_exit_code(result, 1)
    assert "Changelog contains no releases" in result.output


def test_it_fails_to_validate_changelog_with_missing_releases(changelog_path: str):
    with open(changelog_path, "r") as file:
        content = "\n".join([line for line in file if not line.startswith("[Unreleased]")])
    with open(changelog_path, "w") as file:
        file.write(content)
    result = runner.invoke(app, ["--path", changelog_path, "validate"])
    assert_exit_code(result, 1)
    assert "The following releases are missing links: {'Unreleased'}" in result.output


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
    assert_exit_code(result)
    with open(changelog_path, "r") as file:
        output = file.read()
    assert output == content


@pytest.mark.parametrize("path_mode", ["option", "environment"])
def test_it_adds_an_entry_to_the_specified_changelog(changelog_path: str, path_mode: str):
    if path_mode == "option":
        result = runner.invoke(
            app, ["--path", changelog_path, "entry", "added", "-m", "A new feature", "-m", "More details"]
        )
    else:
        with override_env("CHANGELOG_PATH", changelog_path):
            result = runner.invoke(app, ["entry", "added", "-m", "A new feature", "-m", "More details"])
    assert_exit_code(result)
    changelog = load_from_file(changelog_path)
    assert changelog.releases[ReleaseTag("Unreleased")].entries["Added"][-1] == Entry(
        "A new feature", children=[Entry("More details")]
    )


def test_it_adds_a_breaking_change(changelog_path: str):
    result = runner.invoke(app, ["--path", changelog_path, "entry", "changed", "-m", "Changed something", "--breaking"])
    assert_exit_code(result)
    changelog = load_from_file(changelog_path)
    entry = changelog.releases[ReleaseTag("Unreleased")].entries["Changed"][-1]
    assert entry.text == "BREAKING Changed something"


def test_it_can_configure_breaking_change_token(changelog_path: str):
    # GIVEN the breaking change token is changed
    new_token = "**BREAKING CHANGE**"
    assert_exit_code(
        runner.invoke(
            app, ["--path", changelog_path, "config", "set", "--field", "breaking_change_token", "--value", new_token]
        )
    )
    # WHEN I retrieve the breaking change token
    result = runner.invoke(app, ["--path", changelog_path, "config", "get", "--field", "breaking_change_token"])
    assert_exit_code(result)
    # THEN the new token is retrieved
    assert result.output.strip() == new_token
    # AND WHEN I add a breaking change
    assert_exit_code(
        runner.invoke(app, ["--path", changelog_path, "entry", "added", "-m", "A new feature", "--breaking"])
    )
    # THEN the new token is used
    changelog = load_from_file(changelog_path)
    assert changelog.releases[ReleaseTag("Unreleased")].entries["Added"][-1].text.startswith(new_token)


def test_it_cuts_first_release_with_default_options(changelog_path: str):
    result = runner.invoke(app, ["--path", changelog_path, "release"])
    assert_exit_code(result)
    changelog = load_from_file(changelog_path)
    assert list(changelog.releases) == ["Unreleased", "0.1.0"]
    assert {"Unreleased", "0.1.0"} <= set(changelog.links)
    assert not changelog.releases[ReleaseTag("Unreleased")].entries
    assert changelog.releases[ReleaseTag("0.1.0")].entries["Added"] == [Entry("Project started :)")]
    assert changelog.releases[ReleaseTag("0.1.0")].timestamp == date.today().isoformat()


def test_it_cuts_a_release_with_a_specific_tag(changelog_path: str):
    result = runner.invoke(app, ["--path", changelog_path, "release", "--tag", "1.0.0"])
    assert_exit_code(result)
    changelog = load_from_file(changelog_path)
    assert list(changelog.releases) == ["Unreleased", "1.0.0"]
    assert {"Unreleased", "1.0.0"} <= set(changelog.links)
    assert not changelog.releases[ReleaseTag("Unreleased")].entries
    assert changelog.releases[ReleaseTag("1.0.0")].entries["Added"] == [Entry("Project started :)")]
    assert changelog.releases[ReleaseTag("1.0.0")].timestamp == date.today().isoformat()


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
    assert_exit_code(runner.invoke(app, ["--path", changelog_path, "release", "--tag", initial_version]), 0)
    # AND the unreleased section contains an entry
    assert_exit_code(
        runner.invoke(
            app,
            ["--path", changelog_path, "entry", change_type, "--message", "Some stuff"]
            + (["--breaking"] if breaking_change else []),
        ),
        0,
    )
    # WHEN the release command is run
    result = runner.invoke(app, ["--path", changelog_path, "release"])
    # THEN the command exits successfully
    assert_exit_code(result, 0)
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
    assert changelog.latest_tag == expected


def test_it_cuts_a_release_with_specific_bump(
    changelog_path: str,
):
    # GIVEN the previous release is 0.1.0
    assert_exit_code(runner.invoke(app, ["--path", changelog_path, "release", "--tag", "0.1.0"]), 0)
    # AND the unreleased section contains a new feature
    assert_exit_code(runner.invoke(app, ["--path", changelog_path, "entry", "added", "--message", "Some stuff"]), 0)
    # WHEN the release command is run specifying a major version bump
    result = runner.invoke(app, ["--path", changelog_path, "release", "--bump", "major"])
    # THEN the command exits successfully
    assert_exit_code(result, 0)
    # AND the changelog has the correct latest version
    changelog = load_from_file(changelog_path)
    assert changelog.latest_tag == "1.0.0"


def test_it_fails_to_cut_release_without_link(changelog_path: str):
    # GIVEN the changelog is missing a release link format:
    with open(changelog_path, "r") as file:
        content = "\n".join([line for line in file if not line.startswith("[_release_link_format]:")])
    with open(changelog_path, "w") as file:
        file.write(content)
    # WHEN I try to cut a release:
    result = runner.invoke(app, ["--path", changelog_path, "release"])
    # THEN the command fails
    assert_exit_code(result, 1)
    # AND the output explains how to resolve
    assert (
        result.output.strip()
        == f"""ERROR: Could not create release due to missing config: 'release_link_format'.

Run the following before cutting a release:
    changelog --path {changelog_path} config set --field release_link_format --value VALUE"""
    )
