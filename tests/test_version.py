import toml

import changelog


def test_version_matches_pyproject() -> None:
    with open("pyproject.toml", "r") as file:
        pyproject = toml.loads(file.read())
    assert pyproject["tool"]["poetry"]["version"] == changelog.__version__


def test_version_matches_changelog() -> None:
    log = changelog.load_from_file("CHANGELOG.md")
    assert log.latest_tag == changelog.__version__
