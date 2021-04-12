import pytest
import toml

import changelog


def test_version_matches_pyproject():
    with open("pyproject.toml", "r") as file:
        pyproject = toml.loads(file.read())
    assert pyproject["tool"]["poetry"]["version"] == changelog.__version__


@pytest.mark.xfail(strict=True, reason="No release has yet been made")
def test_version_matches_changelog():
    log = changelog.load_from_file("CHANGELOG.md")
    assert log.latest_version == changelog.__version__
