from collections import OrderedDict

from changelog.model import Changelog, ChangelogConfig, ReleaseSection, ReleaseTag


def default_changelog(release_link_format: str, breaking_change_token: str = "BREAKING"):
    """Generate an initial changelog with default header and links."""
    return Changelog(
        header="""# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog] and this project adheres to
[Semantic Versioning].

Types of changes are:
* **Security** in case of vulnerabilities.
* **Deprecated** for soon-to-be removed features.
* **Added** for new features.
* **Changed** for changes in existing functionality.
* **Removed** for now removed features.
* **Fixed** for any bug fixes.""",
        config=ChangelogConfig(
            release_link_format=release_link_format,
            breaking_change_token=breaking_change_token,
        ),
        releases=OrderedDict(
            {
                ReleaseTag("Unreleased"): ReleaseSection(entries={}, timestamp=None),
            }
        ),
        links=OrderedDict(
            {
                "Unreleased": release_link_format.format(previous_tag="initial", tag="HEAD"),
                "Keep a Changelog": "http://keepachangelog.com/en/1.0.0/",
                "Semantic Versioning": "http://semver.org/spec/v2.0.0.html",
            },
        ),
    )
