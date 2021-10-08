# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog] and this project adheres to
[Semantic Versioning].

Types of changes are:
* **Security** in case of vulnerabilities.
* **Deprecated** for soon-to-be removed features.
* **Added** for new features.
* **Changed** for changes in existing functionality.
* **Removed** for now removed features.
* **Fixed** for any bug fixes.

## [Unreleased]
### Added
* Added support for Python 3.8

## [0.1.3] - 2021-10-08
### Fixed
* Unrestrict dependency on typer

## [0.1.2] - 2021-04-16
### Fixed
* Fixed missing typer dependency in package

## [0.1.1] - 2021-04-16
### Fixed
* Missing package metadata added

## [0.1.0] - 2021-04-16
### Added
* Project started :)
* CLI for managing changelogs
  - `changelog init` to create new changelog
  - `changelog validate` to validate changelog
  - `changelog format` to format the changelog
  - `changelog entry` to add entries to changelog
  - `changelog release` to create a new release in changelog
  - `changelog config` to manage changelog configuration

[Unreleased]: https://github.com/jacksmith15/changelog/compare/0.1.3..HEAD
[0.1.3]: https://github.com/jacksmith15/changelog/compare/0.1.2..0.1.3
[0.1.2]: https://github.com/jacksmith15/changelog/compare/0.1.1..0.1.2
[0.1.1]: https://github.com/jacksmith15/changelog/compare/0.1.0..0.1.1
[0.1.0]: https://github.com/jacksmith15/changelog/compare/initial..0.1.0

[Keep a Changelog]: http://keepachangelog.com/en/1.0.0/
[Semantic Versioning]: http://semver.org/spec/v2.0.0.html

[_release_link_format]: https://github.com/jacksmith15/changelog/compare/{previous_tag}..{tag}
[_breaking_change_token]: BREAKING
