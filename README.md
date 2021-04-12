# Changelog

Tool for managing a changelog in the style of [Keep a Changelog](http://keepachangelog.com/en/1.0.0/).

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
- Support parsing config from changelog:
    + SemVer flag
    + Breaking change token
    + Change types (and their semver meaning)
    + Tag link format string
