from __future__ import annotations

from dataclasses import asdict

from changelog.model import Changelog, ChangelogConfig, Entry, ReleaseSection, ReleaseTag


def dumps(changelog: Changelog, indent: int = 2) -> str:
    changelog.validate()
    return (
        "\n\n".join(
            [
                changelog.header.strip(),
                _render_changelog_releases(changelog.releases, indent=indent),
                _render_changelog_links(changelog.links, set(changelog.releases)),
                _render_changelog_config(changelog.config),
            ]
        )
        + "\n"
    )


def _render_changelog_releases(releases: dict[ReleaseTag, ReleaseSection], indent: int = 2) -> str:
    return "\n\n".join([render_changelog_release(release_tag, section) for release_tag, section in releases.items()])


def render_changelog_release(release_tag: ReleaseTag, section: ReleaseSection, indent: int = 2) -> str:
    header = f"## [{release_tag}]"
    if section.timestamp:
        header += f" - {section.timestamp}"
    return "\n".join([header, _render_changelog_change_types(section.entries, indent=indent)])


def _render_changelog_change_types(change_types: dict[str, list[Entry]], indent: int = 2) -> str:
    return "\n\n".join(
        [
            _render_changelog_change_type(change_type, entries, indent=indent)
            for change_type, entries in sorted(change_types.items())
        ]
    )


def _render_changelog_change_type(change_type: str, entries: list[Entry], indent: int = 2) -> str:
    return "\n".join(
        [f"### {change_type}", "\n".join([_render_changelog_entry(entry, indent=indent) for entry in entries])]
    )


def _render_changelog_entry(entry: Entry, indent: int = 2, _indent_level: int = 0) -> str:
    bullet = ("*", "-", "+")[_indent_level % 3]
    return "\n".join(
        [
            " " * indent * _indent_level + f"{bullet} {entry.text}",
            *[
                _render_changelog_entry(sub_entry, indent=indent, _indent_level=_indent_level + 1)
                for sub_entry in entry.children
            ],
        ]
    )


def _render_changelog_links(links: dict[str, str], release_tags: set[ReleaseTag]) -> str:
    return "\n\n".join(
        [
            "\n".join(
                [
                    f"[{link_name}]: {link_target}"
                    for link_name, link_target in links.items()
                    if link_name in release_tags
                ]
            ),
            "\n".join(
                [
                    f"[{link_name}]: {link_target}"
                    for link_name, link_target in links.items()
                    if link_name not in release_tags
                ]
            ),
        ]
    )


def _render_changelog_config(config: ChangelogConfig) -> str:
    return "\n".join([_render_config_field(config, field, value) for field, value in asdict(config).items() if value])


def _render_config_field(config: ChangelogConfig, field: str, value: str) -> str:
    render_value = config.fields[field].metadata.get("render", lambda _: _)
    return f"[_{field}]: {render_value(value)}"


def dump_to_file(changelog: Changelog, path: str = "CHANGELOG.md") -> None:
    with open(path, "w") as file:
        file.write(dumps(changelog))
