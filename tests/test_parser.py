import re
from typing import Union

import pytest

from changelog import loads
from changelog.exceptions import ChangelogParseError
from changelog.model import Entry, ReleaseTag, ReleaseSection
from tests.constants import DEFAULT_HEADER

SECTION_PARAMS = [
    pytest.param(
        """## [0.1.0] - 2021-04-12
### Added
* A single entry
""",
        ReleaseSection(
            timestamp="2021-04-12",
            entries={"Added": [Entry("A single entry")]}
        ),
        id="single-entry",
    ),
    pytest.param(
        """## [0.1.0] - 2021-04-12
### Added
* A single entry split over
  multiple lines
""",
        ReleaseSection(
            timestamp="2021-04-12",
            entries={"Added": [Entry("A single entry split over multiple lines")]}
        ),
        id="single-multiline-entry",
    ),
    pytest.param(
        """## [0.1.0] - 2021-04-12

### Added

* A single entry
""",
        ReleaseSection(
            timestamp="2021-04-12",
            entries={"Added": [Entry("A single entry")]}
        ),
        id="single-entry-with-blank-lines",
    ),
    pytest.param(
        """## [0.1.0] - 2021-04-12
### Added
* Entry one
* Entry two
""",
        ReleaseSection(
            timestamp="2021-04-12",
            entries={"Added": [Entry("Entry one"), Entry("Entry two")]}
        ),
        id="multiple-entries",
    ),
    pytest.param(
        """## [0.1.0] - 2021-04-12
### Added
* A new feature

### Fixed
* A fix
""",
        ReleaseSection(
            timestamp="2021-04-12",
            entries={"Added": [Entry("A new feature")], "Fixed": [Entry("A fix")]}
        ),
        id="multiple-types",
    ),
    pytest.param(
        """## [0.1.0] - 2021-04-12
### Added
* A parent entry
  - A child entry
  - A parent and child entry
    + A nested child entry
  - Another child entry
* Another entry
""",
        ReleaseSection(
            timestamp="2021-04-12",
            entries={
                "Added": [
                    Entry(
                        "A parent entry",
                        children=[
                            Entry("A child entry"),
                            Entry("A parent and child entry", children=[Entry("A nested child entry")]),
                            Entry("Another child entry"),
                        ],
                    ),
                    Entry("Another entry")
                ]
            }
        ),
        id="nested-entries",
    ),
    pytest.param(
        """## [0.1.0] - 2021-04-12
### Added
* A parent entry
  * A child entry
  * A parent and child entry
    * A nested child entry
  * Another child entry
* Another entry
""",
        ReleaseSection(
            timestamp="2021-04-12",
            entries={
                "Added": [
                    Entry(
                        "A parent entry",
                        children=[
                            Entry("A child entry"),
                            Entry("A parent and child entry", children=[Entry("A nested child entry")]),
                            Entry("Another child entry"),
                        ],
                    ),
                    Entry("Another entry")
                ]
            }
        ),
        id="nested-entries-with-one-bullet-type",
    ),
    pytest.param(
        """## [0.1.0] - 2021-04-12
### Added
* A parent entry
    - A more indented child entry
""",
        ReleaseSection(
            timestamp="2021-04-12",
            entries={
                "Added": [
                    Entry(
                        "A parent entry",
                        children=[
                            Entry("A more indented child entry"),
                        ],
                    ),
                ]
            }
        ),
        id="nested-more-indented-entries",
    ),
    pytest.param(
        """## [0.1.0] - 2021-04-12
### Added
* A single entry
Some random root level text
""",
        ChangelogParseError(r"Line \d+ is not indented enough to be a continuation: 'Some random root level text'"),
        id="bad-continuation",
    ),
    pytest.param(
        """## [0.1.0] - 2021-04-12
### Added
* A single entry
  - A nested entry
    + A double nested entry
  Poorly indented continuation
""",
        ChangelogParseError(r"Line \d+ is not indented enough to be a continuation: '  Poorly indented continuation'"),
        id="bad-nested-continuation",
    ),
    pytest.param(
        """## [0.1.0] - 2021-04-12
### Added
* A single entry
  - A nested entry
 * Unclear indentation
""",
        ChangelogParseError(r"Bad indentation at line \d+: ' \* Unclear indentation'"),
        id="bad-indentation",
    ),
]

@pytest.mark.parametrize(
    "section,expectation",
    SECTION_PARAMS,
)
def test_parse_version_section(section: str, expectation: Union[ReleaseSection, Exception]):
    if isinstance(expectation, Exception):
        with pytest.raises(type(expectation)) as exc_info:
            _ = parse_section(section)
        assert re.search(str(expectation), str(exc_info.value)), (
            f"Expected error message matching {str(expectation)!r}, got {str(exc_info.value)!r}"
        )
        return
    section = parse_section(section)
    assert section == expectation


def parse_section(section: str):
    parts = [
        DEFAULT_HEADER,
        section,
    ]
    match = re.match(r"## \[(.+)\]", section)
    if not match:
        raise ValueError(f"No version tag info in test section: {section}")
    version = match.groups()[0]
    parts = [
        DEFAULT_HEADER,
        section,
        f"[{version}]: http://example.com",
    ]
    changelog_text = "\n".join(parts)
    changelog = loads(changelog_text)
    return changelog.releases[ReleaseTag(version)]
