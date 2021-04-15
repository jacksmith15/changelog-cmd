from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from changelog.exceptions import ChangelogParseError
from changelog.model import Changelog, Entry, ReleaseSection, ReleaseTag


@dataclass
class ParserState:
    changelog: Changelog = field(default_factory=Changelog)
    release_tag: Optional[tuple[ReleaseTag, Optional[str]]] = None
    change_type: Optional[str] = None
    entry_stack: list[tuple[Entry, int]] = field(default_factory=list)

    @property
    def root_entry(self) -> Optional[Entry]:
        if not self.entry_stack:
            return None
        return self.entry_stack[0][0]

    def parent_entry(self, indentation_chars: int) -> Optional[Entry]:
        if not self.entry_stack or indentation_chars == self.entry_stack[0][1]:
            # Top level entry
            return None
        if indentation_chars > self.entry_stack[-1][1]:
            # If its more indented than the previous entry, its a child of that entry
            return self.entry_stack[-1][0]
        # Remove more nested items from the stack
        while indentation_chars < self.entry_stack[-1][1]:
            self.entry_stack.pop(-1)
        if indentation_chars != self.entry_stack[-1][1]:
            raise ChangelogParseError("Bad indentation")
        self.entry_stack.pop(-1)
        return self.entry_stack[-1][0]

    def flush(self) -> None:
        if self.release_tag and self.change_type and self.root_entry:
            tag, timestamp = self.release_tag
            self.changelog.releases.setdefault(tag, ReleaseSection(entries={}, timestamp=timestamp)).entries.setdefault(
                self.change_type, []
            ).append(self.root_entry)
            self.entry_stack = []


def loads(text: str, tab_indent: int = 2) -> Changelog:
    parser_state = ParserState()
    text = text.replace("\t", tab_indent * " ")
    for index, line in enumerate(text.splitlines()):
        if (release_header_match := re.match(r"^## \[(?P<tag>.+)\]( +- +(?P<date>\d+\-\d+\-\d+))?", line)) :
            # New tags are level-two headings, and must be linked.
            # They optionally include a timestamp.
            parser_state.flush()
            match_dict = release_header_match.groupdict()
            tag = ReleaseTag(match_dict["tag"])
            timestamp = match_dict.get("date")
            parser_state.release_tag = tag, timestamp
            parser_state.changelog.releases.setdefault(tag, ReleaseSection(entries={}, timestamp=timestamp))
            continue
        if not parser_state.release_tag:
            # If release_tag is not set, assume we are parsing header text
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
        if (entry_start_match := re.match(r"^ *(\*|\+|-) (?P<sub_entry_start>.+)", line)) :
            # New entry start
            indentation_chars = len(line) - len(line.lstrip())
            entry = Entry(text=entry_start_match.groupdict()["sub_entry_start"])
            try:
                parent_entry = parser_state.parent_entry(indentation_chars)
            except ChangelogParseError:
                raise ChangelogParseError(f"Bad indentation at line {index}: {line!r}")
            if not parent_entry:
                # Must be top-level
                parser_state.flush()
            else:
                # New sub entry
                parent_entry.children.append(entry)
            parser_state.entry_stack.append((entry, indentation_chars))
            continue
        if parser_state.entry_stack and (entry_continued_match := re.match(r"^ *(?P<entry_continued>.+)", line)):
            # Multi-line continuation of entry text.
            indentation_chars = len(line) - len(line.lstrip())
            if indentation_chars < parser_state.entry_stack[-1][1] + 2:
                raise ChangelogParseError(f"Line {index} is not indented enough to be a continuation: {line!r}")
            parser_state.entry_stack[-1][0].text += " " + entry_continued_match.groupdict()["entry_continued"].lstrip()
            continue
        if (link_match := re.match(r"^\[(?P<link_name>.+)\]: (?P<link_target>.+)$", line)) :
            # Links follow the format [{link_name}]: http://example.com/link/target
            parser_state.flush()
            match_dict = link_match.groupdict()
            link_name = match_dict["link_name"]
            link_target = match_dict["link_target"]
            if link_name.startswith("_") and link_name[1:] in parser_state.changelog.config.fields:
                # Check if the link is actually a config field in disguise
                field_name = link_name[1:]
                config = parser_state.changelog.config
                field_parser = config.fields[field_name].metadata.get("parse", lambda _: _)
                setattr(config, link_name[1:], field_parser(link_target))
                continue
            parser_state.changelog.links[link_name] = link_target
            continue
        if not line.strip() or "nothing here" in line.lower():
            # Blank lines terminate the previous entry, but are otherwise ignored.
            parser_state.flush()
            continue
        raise ChangelogParseError(f"Invalid changelog at line {index}: {line!r}")
    parser_state.flush()
    parser_state.changelog.header = parser_state.changelog.header.lstrip()
    parser_state.changelog.validate()
    return parser_state.changelog


def load_from_file(path: str = "CHANGELOG.md") -> Changelog:
    with open(path, "r") as file:
        contents = file.read()
    return loads(contents)
