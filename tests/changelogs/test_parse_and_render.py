from collections import OrderedDict

import pytest

from changelog.model import Changelog, ReleaseTag, ReleaseSection, Entry
from changelog import dumps, loads, load_from_file
from tests.constants import DEFAULT_HEADER, DEFAULT_LINKS


EXPECTATIONS = {
    "initial_changelog.md": Changelog(
        header=DEFAULT_HEADER,
        releases=OrderedDict(
            {ReleaseTag("Unreleased"): ReleaseSection(timestamp=None, entries={"Added": [Entry("Project started :)")]})}
        ),
        links=OrderedDict(
            {
                "Unreleased": "https://github.com/jacksmith15/changelog/compare/initial..HEAD",
                **DEFAULT_LINKS,
            }
        ),
    ),
    "populated_changelog.md": Changelog(
        header=DEFAULT_HEADER,
        releases=OrderedDict(
            {
                ReleaseTag("Unreleased"): ReleaseSection(
                    timestamp=None,
                    entries={
                        "Added": [Entry("A third feature", children=[Entry("Some notes"), Entry("Even more notes")])]
                    },
                ),
                ReleaseTag("0.2.0"): ReleaseSection(
                    timestamp="2021-04-12",
                    entries={
                        "Added": [
                            Entry(
                                "A second feature",
                                children=[
                                    Entry("Some notes"),
                                    Entry("Even more notes", children=[Entry("Nested notes")]),
                                ],
                            )
                        ],
                        "Fixed": [Entry("Corrected behaviour")],
                    },
                ),
                ReleaseTag("0.1.0"): ReleaseSection(
                    timestamp="2021-04-12",
                    entries={
                        "Added": [
                            Entry("Project started :)"),
                            Entry(
                                "The first feature",
                                children=[
                                    Entry("Some notes"),
                                    Entry("Some more notes"),
                                ],
                            ),
                        ],
                    },
                ),
            },
        ),
        links=OrderedDict(
            {
                "Unreleased": "https://github.com/jacksmith15/changelog/compare/0.2.0..HEAD",
                "0.2.0": "https://github.com/jacksmith15/changelog/compare/0.1.0..0.2.0",
                "0.1.0": "https://github.com/jacksmith15/changelog/compare/initial..0.1.0",
                **DEFAULT_LINKS,
            }
        ),
    ),
}


@pytest.mark.parametrize("path,expectation", EXPECTATIONS.items())
def test_parses_example_changelog_correctly(path: str, expectation: Changelog):
    changelog = load_from_file(f"tests/changelogs/{path}")
    assert changelog == expectation


@pytest.mark.parametrize("path", EXPECTATIONS.keys())
def test_rendered_matches_parsed(path: str):
    with open(f"tests/changelogs/{path}", "r") as file:
        contents = file.read()
    changelog = loads(contents)
    assert dumps(changelog) == contents
