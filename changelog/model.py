from __future__ import annotations

import re
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Literal, Optional, cast

from changelog.exceptions import ChangelogError, ChangelogValidationError
from changelog.utils import reverse_format

ChangeType = Literal["Security", "Deprecated", "Added", "Changed", "Removed", "Fixed"]


class Bump(Enum):
    MAJOR = 0
    MINOR = 1
    PATCH = 2


class ReleaseTag(str):
    @classmethod
    def from_semver(cls, semver: tuple[int, int, int]) -> ReleaseTag:
        return cls(".".join(map(str, semver)))

    @property
    def is_semver(self):
        return re.match(r"^\d+\.\d+\.\d+$", self)

    @property
    def semver(self) -> tuple[int, int, int]:
        if not self.is_semver:
            raise TypeError(f"ReleaseTag {self!r} is not a semantic version")
        return cast(tuple[int, int, int], tuple(map(int, self.split("."))))

    def bump_semver(self, bump: Bump) -> ReleaseTag:
        semver = list(self.semver)
        semver[bump.value] = semver[bump.value] + 1
        for idx in range(bump.value + 1, 3):
            semver[idx] = 0
        return type(self)(".".join(map(str, semver)))


_UNRELEASED = ReleaseTag("Unreleased")


@dataclass
class Changelog:
    header: str = ""
    releases: OrderedDict[ReleaseTag, ReleaseSection] = field(default_factory=OrderedDict)
    links: OrderedDict[str, str] = field(default_factory=OrderedDict)

    @property
    def release_link_format(self) -> str:
        if "_release_link_format" not in self.links:
            raise ChangelogError("No release link format specified.")
        return self.links["_release_link_format"]

    @property
    def breaking_change_tag(self) -> str:
        return self.links.get("_breaking_change_tag", "BREAKING")

    def validate(self):
        """Validate the changelog."""
        missing_tag_links = set(self.releases) - set(self.links)
        if missing_tag_links:
            raise ChangelogValidationError(f"The following releases are missing links: {missing_tag_links}")

    def add_entry(self, change_type: ChangeType, *items: str, breaking: bool = False, tag: str = None) -> None:
        """Add an entry to the changelog, under unreleased."""
        tag = ReleaseTag(tag) if tag else _UNRELEASED
        assert change_type in ChangeType.__args__  # type: ignore
        prefix = f"{self.breaking_change_tag} " if breaking else ""
        self.releases.setdefault(tag, ReleaseSection(entries={}, timestamp=None)).entries.setdefault(
            change_type, []
        ).append(Entry(text=prefix + items[0], children=[Entry(text=item) for item in items[1:]]))

    @property
    def latest_tag(self) -> Optional[ReleaseTag]:
        return next((tag for tag in self.releases if not tag == _UNRELEASED), None)

    def next_tag(self, force: Bump = None) -> ReleaseTag:
        if not self.latest_tag:
            return ReleaseTag.from_semver((0, 1, 0))
        if not self.latest_tag.is_semver:
            raise ChangelogError(f"Previous tag {self.latest_tag} is not semantic")
        if force:
            return self.latest_tag.bump_semver(force)
        unreleased = self.releases[_UNRELEASED].entries
        if self.breaking_change_tag in str(unreleased) and self.latest_tag.semver[0] > 0:
            return self.latest_tag.bump_semver(Bump.MAJOR)
        if set(unreleased) - {"Fixed"}:
            return self.latest_tag.bump_semver(Bump.MINOR)
        return self.latest_tag.bump_semver(Bump.PATCH)

    def cut_release(self, force: Bump = None, tag: str = None) -> tuple[ReleaseTag, ReleaseSection]:
        previous_tag = self.latest_tag
        next_tag = ReleaseTag(tag) if tag else self.next_tag(force=force)
        # Move entries from unreleased to the new tag:
        self.releases[next_tag] = self.releases[_UNRELEASED]
        self.releases[next_tag].timestamp = date.today().isoformat()
        self.releases[_UNRELEASED] = ReleaseSection(entries={}, timestamp=None)
        # Reorder releases:
        self.releases.move_to_end(next_tag, last=False)
        self.releases.move_to_end(_UNRELEASED, last=False)
        # Update tag links
        self.links[next_tag] = self.release_link_format.format(previous_tag=previous_tag or "initial", next_tag=next_tag)
        self.links[_UNRELEASED] = self.release_link_format.format(previous_tag=next_tag, next_tag=self._unreleased_link_tag)
        # Reorder links
        self.links.move_to_end(next_tag, last=False)
        self.links.move_to_end(_UNRELEASED, last=False)
        return next_tag, self.releases[next_tag]

    @property
    def _unreleased_link_tag(self) -> str:
        unreleased_link_tags: dict[str, str] = reverse_format(self.links[_UNRELEASED], self.release_link_format, {})
        return unreleased_link_tags.get("next_tag", "HEAD")


@dataclass
class ReleaseSection:
    entries: dict[str, list[Entry]]
    timestamp: Optional[str]


@dataclass
class Entry:
    text: str
    children: list[Entry] = field(default_factory=list)
