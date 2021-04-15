import pytest

from changelog.utils import reverse_format


def test_it_can_reverse_on_no_fields():
    assert reverse_format("Hello, world", "Hello, world") == {}


def test_it_can_reverse_single_field():
    assert reverse_format("Hello, world", "Hello, {name}") == {"name": "world"}


def test_it_can_reverse_multi_fields():
    assert reverse_format("Hello, world", "{greeting}, {name}") == {"name": "world", "greeting": "Hello"}


def test_it_can_reverse_repeated_fields():
    assert reverse_format("foo foo", "{word} {word}") == {"word": "foo"}


def test_raises_on_no_match():
    with pytest.raises(ValueError):
        reverse_format("Greetings, world", "Hello, {name}")


def test_it_returns_default_on_no_match():
    assert reverse_format("Greetings, world", "Hello, {name}", 123) == 123


@pytest.mark.parametrize("invalid_name", ["", "0", "foo-bar", "123foo"])
def test_it_raises_on_invalid_names(invalid_name: str):
    with pytest.raises(ValueError):
        reverse_format("x", "{" + invalid_name + "}")


def test_it_works_on_multiline_string():
    format_spec = """Hello, {name}

Some other stuff
"""
    string = """Hello, world

Some other stuff
"""
    result = reverse_format(string, format_spec)
    assert result["name"] == "world"


def test_it_works_on_multiline_parameter():
    format_spec = """Hello, {name}

Some other stuff
"""
    string = """Hello, world
et al

Some other stuff
"""
    result = reverse_format(string, format_spec, multiline=True)
    assert result["name"] == "world\net al"
