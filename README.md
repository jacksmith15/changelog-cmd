# Changelog

Tool for managing a changelog in the style of [Keep a Changelog](http://keepachangelog.com/en/1.0.0/).

### Features:

- Write new changelog entries in a consistent manner
- Validate and format your changelog
- Suggest semantic version of releases based on their contents
- Write scripts which make automated changes and updates to changelogs, whilst keeping the changelog in a human-readable format

## Installation

TODO

## Usage

### Starting a changelog

Create a changelog named `CHANGELOG.md` in the current directory by running

```shell
changelog init --release-link-format=RELEASE_LINK_FORMAT
```

Where the `--release-link-format` option specifies how to generate links to a given release, and is given using a Python string format specifier. For example, if you want to link to source on GitHub, this format specifier might be:

- `https://github.com/user/repo/tree/{tag}` - the source code at this release
- `https://github.com/user/repo/compare/{previous_tag}...{tag}` - a comparison of this release with the one before

Or if you want to link to PyPi, the format might be:

- `https://pypi.org/project/package/{tag}/`

Above you see the two variables available for substitution:
- `tag` is the tag of the release
- `previous_tag` is the tag of the previous release


### Finding the changelog

By default, `changelog` looks for a changelog called `CHANGELOG.md` in the current directory. You can override this by passing a command-line option:

```shell
changelog --path path/to/changelog.md ...
```

Or you can set an environment variable:

```shell
CHANGELOG_PATH=path/to/changelog.md ...
```

The command-line option takes precedence.

### Adding entries to a changelog

Add an entry to the unreleased section of a changelog:

```shell
changelog entry added --message "Description of my change"
```

You can replace `added` in the above with any of the following types of entry:

- `added`
- `changed`
- `deprecated`
- `fixed`
- `removed`
- `security`

To specify a change as breaking, simply include the `--breaking` flag:

```shell
changelog entry changed --message "Description of a breaking change" --breaking
```

If you need to add a missing entry to a past release, you can specify the release tag explicitly:

```shell
changelog entry fixed --message "Description of a fix" --tag "0.1.1"
```

### Cutting a release

When you are ready to cut a release, run the following:

```shell
changelog release
```

This will identify the correct semantic version. Alternatively, you can specify the semantic version bump yourself:

```shell
changelog release --bump "major"
```

Or, if you don't use semantic versioning at all, simply specify the tag of the release:

```shell
changelog release --tag "2021.r3"
```

## Development

Install dependencies:

```shell
pyenv shell 3.9.4  # Or other 3.9.x
pre-commit install  # Configure commit hooks
poetry install  # Install Python dependencies
```

Run tests:

```shell
poetry run inv verify
```
