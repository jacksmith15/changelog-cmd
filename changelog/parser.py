from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from changelog.exceptions import ChangelogParseError, ChangelogValidationError
from changelog.model import Changelog, Entry, Version, VersionSection


@dataclass
class ParserState:
    changelog: Changelog = field(default_factory=Changelog)
    version: Optional[tuple[Version, Optional[str]]] = None
    change_type: Optional[str] = None
    entry: Optional[Entry] = None

    def flush(self):
        if self.version and self.change_type and self.entry:
            version, timestamp = self.version
            self.changelog.versions.setdefault(
                version, VersionSection(entries={}, timestamp=timestamp)
            ).entries.setdefault(self.change_type, []).append(self.entry)
            self.entry = None


def loads(text: str, indent: int = 2) -> Changelog:
    parser_state = ParserState()
    for index, line in enumerate(text.splitlines()):
        if (version_match := re.match(r"^## \[(?P<version>.+)\]( +- +(?P<date>\d+\-\d+\-\d+))?", line)) :
            # New versions are level-two headings, and must be linked.
            # They optionally include a timestamp.
            parser_state.flush()
            match_dict = version_match.groupdict()
            version = Version(match_dict["version"])
            timestamp = match_dict.get("date")
            parser_state.version = version, timestamp
            parser_state.changelog.versions.setdefault(version, VersionSection(entries={}, timestamp=timestamp))
            continue
        if not parser_state.version:
            # If version is not set, assume we are parsing header text
            parser_state.changelog.header += f"\n{line}"
            continue
        if (
            change_type_match := re.match(
                r"^### (?P<change_type>Security|Deprecated|Added|Changed|Removed|Fixed)$", line
            )
        ) :
            # Change types are grouped under level 3 headings.
            parser_state.flush()
            parser_state.change_type = change_type_match.groupdict()["change_type"]
            continue
        if (entry_start_match := re.match(r"^(\*|\+|-) (?P<entry_start>.+)", line)) :
            # New top-level entry
            parser_state.flush()
            parser_state.entry = Entry(text=entry_start_match.groupdict()["entry_start"])
            continue
        if parser_state.entry and (sub_entry_start_match := re.match(r"^ +(\*|\+|-) (?P<sub_entry_start>.+)", line)):
            # Sub-entry, grouped under a parent entry.
            parent_entry = _get_parent_entry(index, line, parser_state.entry, indent)
            parent_entry.sub_entries.append(Entry(text=sub_entry_start_match.groupdict()["sub_entry_start"]))
            continue
        if parser_state.entry and (entry_continued_match := re.match(r"^ +(?P<entry_continued>.+)", line)):
            # Multi-line continuation of entry text.
            parent_entry = _get_parent_entry(index, line, parser_state.entry, indent)
            parent_entry.text += " " + entry_continued_match.groupdict()["entry_continued"].lstrip()
            continue
        if (link_match := re.match(r"^\[(?P<link_name>.+)\]: (?P<link_target>.+)$", line)) :
            # Links follow the format [{link_name}]: http://example.com/link/target
            parser_state.flush()
            match_dict = link_match.groupdict()
            parser_state.changelog.links[match_dict["link_name"]] = match_dict["link_target"]
            continue
        if not line.strip() or "nothing here" in line.lower():
            # Blank lines terminate the previous entry, but are otherwise ignored.
            parser_state.flush()
            continue
        raise ChangelogParseError(f"Invalid changelog at line {index}: {line!r}")
    parser_state.flush()
    parser_state.changelog.header = parser_state.changelog.header.lstrip()
    try:
        parser_state.changelog.validate()
    except ChangelogValidationError as exc:
        raise ChangelogParseError("Changelog failed validation") from exc
    return parser_state.changelog


def _get_parent_entry(index: int, line: str, parent_entry: Entry, indent_size: int = 2) -> Entry:
    indentation_depth = _get_indentation_depth(index, line, indent_size)
    if not indentation_depth:
        raise ValueError("Cannot get parent entry for root-level entry.")
    try:
        for _ in range(indentation_depth - 1):
            parent_entry = parent_entry.sub_entries[-1]
    except IndexError:
        raise ChangelogParseError(f"Bad indentation (too large) at line {index}: {line!r}")
    return parent_entry


def _get_indentation_depth(index: int, line: str, indent_size: int = 2) -> int:
    line = line.replace("\t", " " * indent_size)
    chars = len(line) - len(line.lstrip())
    if chars % indent_size:
        raise ChangelogParseError(f"Bad indentation at line {index}, must be a multiple of {indent_size}: {line!r}")
    return chars // indent_size


def load_from_file(path: str = "CHANGELOG.md") -> Changelog:
    with open(path, "r") as file:
        contents = file.read()
    return loads(contents)
