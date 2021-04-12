from __future__ import annotations

import re
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Literal, Optional, cast

from changelog.constants import _BREAKING_CHANGE_INDICATOR
from changelog.exceptions import ChangelogError, ChangelogValidationError

ChangeType = Literal["Security", "Deprecated", "Added", "Changed", "Removed", "Fixed"]


class Bump(Enum):
    MAJOR = 0
    MINOR = 1
    PATCH = 2


class Version(str):
    @classmethod
    def from_semver(cls, semver: tuple[int, int, int]) -> Version:
        return cls(".".join(map(str, semver)))

    @property
    def is_semver(self):
        return re.match(r"^\d+\.\d+\.\d+$", self)

    @property
    def semver(self) -> tuple[int, int, int]:
        if not self.is_semver:
            raise TypeError(f"Version {self!r} is not a semantic version")
        return cast(tuple[int, int, int], tuple(map(int, self.split("."))))

    def bump_semver(self, bump: Bump) -> Version:
        semver = list(self.semver)
        semver[bump.value] = semver[bump.value] + 1
        for idx in range(bump.value + 1, 3):
            semver[idx] = 0
        return type(self)(".".join(map(str, semver)))


_UNRELEASED = Version("Unreleased")


@dataclass
class Changelog:
    header: str = ""
    versions: OrderedDict[Version, VersionSection] = field(default_factory=OrderedDict)
    links: OrderedDict[str, str] = field(default_factory=OrderedDict)

    def validate(self):
        """Validate the changelog."""
        missing_version_links = set(self.versions) - set(self.links)
        if missing_version_links:
            raise ChangelogValidationError(f"The following versions are missing links: {missing_version_links}")

    def add_entry(self, change_type: ChangeType, *items: str, breaking: bool = False, tag: str = None) -> None:
        """Add an entry to the changelog, under unreleased."""
        tag = Version(tag) if tag else _UNRELEASED
        assert change_type in ChangeType.__args__  # type: ignore
        prefix = f"{_BREAKING_CHANGE_INDICATOR} " if breaking else ""
        self.versions.setdefault(tag, VersionSection(entries={}, timestamp=None)).entries.setdefault(
            change_type, []
        ).append(Entry(text=prefix + items[0], sub_entries=[Entry(text=item) for item in items[1:]]))

    @property
    def latest_version(self) -> Optional[Version]:
        return next((version for version in self.versions if not version == _UNRELEASED), None)

    def next_version(self, force: Bump = None) -> Version:
        if not self.latest_version:
            return Version.from_semver((0, 1, 0))
        if not self.latest_version.is_semver:
            raise ChangelogError(f"Previous version {self.latest_version} is not semantic")
        if force:
            return self.latest_version.bump_semver(force)
        unreleased = self.versions[_UNRELEASED].entries
        if _BREAKING_CHANGE_INDICATOR in str(unreleased) and self.latest_version.semver[0] > 0:
            return self.latest_version.bump_semver(Bump.MAJOR)
        if set(unreleased) - {"Fixed"}:
            return self.latest_version.bump_semver(Bump.MINOR)
        return self.latest_version.bump_semver(Bump.PATCH)

    def cut_release(self, force: Bump = None, tag: str = None) -> tuple[Version, VersionSection]:
        latest_version = self.latest_version
        next_version = Version(tag) if tag else self.next_version(force=force)
        # Move entries from unreleased to the new version:
        self.versions[next_version] = self.versions[_UNRELEASED]
        self.versions[next_version].timestamp = date.today().isoformat()
        self.versions[_UNRELEASED] = VersionSection(entries={}, timestamp=None)
        # Reorder versions:
        self.versions.move_to_end(next_version, last=False)
        self.versions.move_to_end(_UNRELEASED, last=False)
        # Update version links
        self.links[next_version] = self.links[_UNRELEASED].replace("HEAD", next_version)
        self.links[_UNRELEASED] = self.links[_UNRELEASED].replace(latest_version or "initial", next_version)
        # Reorder links
        self.links.move_to_end(next_version, last=False)
        self.links.move_to_end(_UNRELEASED, last=False)
        return next_version, self.versions[next_version]


@dataclass
class VersionSection:
    entries: dict[ChangeType, list[Entry]]
    timestamp: Optional[str]


@dataclass
class Entry:
    text: str
    sub_entries: list[Entry] = field(default_factory=list)
