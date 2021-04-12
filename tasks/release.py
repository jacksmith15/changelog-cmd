from __future__ import annotations

import re
from itertools import takewhile

from invoke import task
from invoke.exceptions import Exit, UnexpectedExit
from termcolor import colored

import changelog
from changelog.renderer import render_changelog_version
from tasks.helpers import package, print_header

RELEASE_BRANCH = "main"


@task()
def release(ctx):
    print_header("Starting release")
    validate_branch(ctx)
    print_header("Determining release type", level=2)
    update_versions()
    if not verify_diff(ctx):
        raise Exit(code=1, message="Aborted.")
    print_header("Committing, tagging and pushing", level=2)
    tag_release(ctx)
    return


def validate_branch(ctx):
    print_header("Validating local branch", level=2)
    branch = ctx.run("git branch --show-current", hide=True).stdout.strip()
    if branch != RELEASE_BRANCH:
        raise Exit(code=1, message=f"You are not on the release branch: {branch!r}")
    try:
        ctx.run("git diff-index --quiet HEAD --")
    except UnexpectedExit:
        raise Exit(code=1, message="You have uncommitted changes, cannot release.")
    ctx.run("git remote update")
    status = ctx.run("git status --untracked-files=no", hide=True).stdout
    if f"Your branch is up-to-date with 'origin/{RELEASE_BRANCH}'." not in status:
        raise Exit(code=1, message="Local branch is not up-to-date with remote.")


def bool_input(message, default=True):
    return input(message + (" [Y/n] " if default else " [y/N] ")).lower().startswith("n" if default else "y") ^ default


def update_versions():
    current_version: str = package.__version__
    log = changelog.load_from_file("CHANGELOG.md")
    next_version, version_content = log.cut_release()
    if not verify_release(current_version, next_version, render_changelog_version(next_version, version_content)):
        raise Exit(code=1, message="Aborted.")

    print_header("Updating changelog", level=2)
    changelog.write_to_file(log, "CHANGELOG.md")

    print_header(f"Updating {package.__file__}", level=2)
    with open(package.__file__, "r", encoding="utf8") as file:
        new_init = [
            *takewhile(lambda l: not re.match(r"^__version__ = .*", l), file),
            f'__version__ = "{next_version}"\n',
            *file,
        ]
    with open(package.__file__, "w", encoding="utf8") as file:
        file.writelines(new_init)

    print_header("Updating pyproject.toml", level=2)
    with open("pyproject.toml", "r", encoding="utf8") as file:
        new_pyproject = [
            *takewhile(lambda l: not re.match(r"^version = .*", l), file),
            'version = "{new_version}"\n',
            *file,
        ]

    with open("pyproject.toml", "w", encoding="utf8") as file:
        file.writelines(new_pyproject)


def verify_release(current_version: str, next_version: str, content: str) -> bool:
    return bool_input(
        f"""
This release would update to {next_version} from {current_version} due to
the following changes:

{content}

Proceed?
"""
    )


def verify_diff(ctx):
    diff = ctx.run("git diff", hide=True).stdout
    color_lines = "\n".join([color_line(line) for line in diff.split("\n")])
    return bool_input(
        f"""
Please review release before tag:

{color_lines}

Proceed?
"""
    )


def color_line(line: str) -> str:
    if line.startswith("+"):
        return colored(line, "green")
    if line.startswith("-"):
        return colored(line, "red")
    if line.startswith("^"):
        return colored(line, "blue")
    return line


def tag_release(ctx, next_version: str):
    ctx.run(f"git commit -i CHANGELOG.md {package.__file__}.py pyproject.toml -m release/{next_version}")
    ctx.run(f"git push origin {RELEASE_BRANCH}")
    ctx.run(f"git tag -a {next_version} -m {next_version}")
    ctx.run(f"git push origin {next_version}")
