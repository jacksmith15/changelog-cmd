# Changelog

Tool for managing a changelog in the style of [Keep a Changelog](http://keepachangelog.com/en/1.0.0/).

## Installation

TODO

## Usage

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

## TODOs:

- Initialise a new changelog
