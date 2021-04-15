from __future__ import annotations

import re
from collections import OrderedDict
from dataclasses import Field, dataclass, field
from datetime import date
from enum import Enum
from typing import Literal, Optional, cast
from urllib.parse import quote_plus, unquote_plus

from changelog.exceptions import ChangelogError, ChangelogMissingConfigError, ChangelogValidationError
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
class ChangelogConfig:
    release_link_format: Optional[str] = None
    breaking_change_token: str = field(default="BREAKING", metadata={"parse": unquote_plus, "render": quote_plus})

    @property
    def fields(self) -> dict[str, Field]:
        return self.__dataclass_fields__  # type: ignore[attr-defined]

    def get(self, key: str, default: str = None) -> str:
        if key not in self.fields:
            raise ChangelogError(f"{key} is not a valid config option.")
        value = getattr(self, key)
        if not value:
            if default:
                return default
            raise ChangelogMissingConfigError(f"No config option for {key!r}", field=key)
        return value

    def set(self, key: str, value: str) -> None:
        if key not in self.fields:
            raise ChangelogError(f"{key} is not a valid config option.")
        setattr(self, key, value)


@dataclass
class Changelog:
    header: str = ""
    config: ChangelogConfig = field(default_factory=ChangelogConfig)
    releases: OrderedDict[ReleaseTag, ReleaseSection] = field(default_factory=OrderedDict)
    links: OrderedDict[str, str] = field(default_factory=OrderedDict)

    def validate(self):
        """Validate the changelog."""
        if not self.releases:
            raise ChangelogValidationError("Changelog contains no releases!")
        missing_tag_links = set(self.releases) - set(self.links)
        if missing_tag_links:
            raise ChangelogValidationError(f"The following releases are missing links: {missing_tag_links}")

    def add_entry(self, change_type: ChangeType, *items: str, breaking: bool = False, tag: str = None) -> None:
        """Add an entry to the changelog, under unreleased."""
        tag = ReleaseTag(tag) if tag else _UNRELEASED
        assert change_type in ChangeType.__args__  # type: ignore
        prefix = f"{self.config.get('breaking_change_token')} " if breaking else ""
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
        if self.config.get("breaking_change_token", "BREAKING") in str(unreleased) and self.latest_tag.semver[0] > 0:
            return self.latest_tag.bump_semver(Bump.MAJOR)
        if set(unreleased) - {"Fixed"}:
            return self.latest_tag.bump_semver(Bump.MINOR)
        return self.latest_tag.bump_semver(Bump.PATCH)

    def cut_release(self, force: Bump = None, tag: str = None) -> tuple[ReleaseTag, ReleaseSection]:
        previous_tag = self.latest_tag
        release_tag = ReleaseTag(tag) if tag else self.next_tag(force=force)
        # Move entries from unreleased to the new tag:
        self.releases[release_tag] = self.releases[_UNRELEASED]
        self.releases[release_tag].timestamp = date.today().isoformat()
        self.releases[_UNRELEASED] = ReleaseSection(entries={}, timestamp=None)
        # Reorder releases:
        self.releases.move_to_end(release_tag, last=False)
        self.releases.move_to_end(_UNRELEASED, last=False)
        # Update tag links
        link_spec = self.config.get("release_link_format")
        self.links[release_tag] = link_spec.format(previous_tag=previous_tag or "initial", tag=release_tag)
        self.links[_UNRELEASED] = link_spec.format(
            previous_tag=release_tag,
            tag=reverse_format(self.links[_UNRELEASED], link_spec, cast(dict[str, str], {})).get("tag", "HEAD"),
        )
        # Reorder links
        self.links.move_to_end(release_tag, last=False)
        self.links.move_to_end(_UNRELEASED, last=False)
        return release_tag, self.releases[release_tag]


@dataclass
class ReleaseSection:
    entries: dict[str, list[Entry]]
    timestamp: Optional[str]


@dataclass
class Entry:
    text: str
    children: list[Entry] = field(default_factory=list)
