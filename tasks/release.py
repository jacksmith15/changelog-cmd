from __future__ import annotations

import re
from collections.abc import Callable

from invoke import task
from invoke.exceptions import Exit, UnexpectedExit
from termcolor import colored

import changelog
from changelog.renderer import render_changelog_release
from tasks.helpers import package, print_header
from tasks.verify import verify

RELEASE_BRANCH = "main"


@task(pre=[verify])
def build(ctx):
    """Build wheel and sdist."""
    print_header("Building package")
    ctx.run("poetry build")


@task()
def _validate_branch(ctx):
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


@task(pre=[_validate_branch, build])
def release(ctx, dry_run=False):
    """Perform a release, by updating metadata, tagging commit, and publishing."""
    print_header("Starting release")
    print_header("Determining release type", level=2)
    update_release_tags()
    if not verify_diff(ctx):
        raise Exit(code=1, message="Aborted.")
    print_header("Committing, tagging and pushing", level=2)
    if not dry_run:
        tag_release(ctx)
    if not dry_run:
        ctx.run("poetry publish")
    else:
        ctx.run("poetry publish --dry-run")
    return


def bool_input(message, default=True):
    return input(message + (" [Y/n] " if default else " [y/N] ")).lower().startswith("n" if default else "y") ^ default


def update_file(path: str, processor: Callable[[str], str]):
    with open(path, "r") as file:
        content = processor(file.read())
    with open(path, "w") as file:
        file.write(content)


def update_release_tags():
    log = changelog.load_from_file("CHANGELOG.md")
    previous_release_tag: str = log.latest_tag or "unknown"
    release_tag, release_content = log.cut_release()
    if not verify_release(previous_release_tag, release_tag, render_changelog_release(release_tag, release_content)):
        raise Exit(code=1, message="Aborted.")

    print_header("Updating changelog", level=2)
    changelog.write_to_file(log, "CHANGELOG.md")

    print_header(f"Updating {package.__file__}", level=2)
    update_file(
        package.__file__,
        lambda content: re.sub(
            r'__version__ *= *".*"',
            f'__version__ = "{release_tag}"',
            content,
        ),
    )

    print_header("Updating pyproject.toml", level=2)
    update_file(
        package.__file__,
        lambda content: re.sub(
            r'version *= *".*"',
            f'version = "{release_tag}"',
            content,
        ),
    )


def verify_release(previous_release_tag: str, target_release_tag: str, content: str) -> bool:
    return bool_input(
        f"""
This release would update from {previous_release_tag!r} to {target_release_tag!r} due to
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


def tag_release(ctx, release_tag: str):
    ctx.run(f"git commit -i CHANGELOG.md {package.__file__}.py pyproject.toml -m release/{release_tag}")
    ctx.run(f"git push origin {RELEASE_BRANCH}")
    ctx.run(f"git tag -a {release_tag} -m {release_tag}")
    ctx.run(f"git push origin {release_tag}")
