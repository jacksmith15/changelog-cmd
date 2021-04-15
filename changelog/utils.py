import re
from string import Formatter
from typing import TypeVar, Union, overload

_NOT_PASSED = object()


DefaultT = TypeVar("DefaultT")


@overload
def reverse_format(string: str, format_spec: str) -> dict[str, str]:
    ...  # pragma: no cover


@overload
def reverse_format(string: str, format_spec: str, default: DefaultT) -> Union[dict[str, str], DefaultT]:
    ...  # pragma: no cover


def reverse_format(string, format_spec, default=_NOT_PASSED, multiline: bool = False):
    """Inverse of `format`.

    Returns a mapping of the format_spec field names to their values in `string`.

    :param string: The string to extract values from.
    :param format_spec: The format spec which describes the string fields. Field names must
        be valid Python identifiers.
    :param default: Optional value to return if string does not match the format spec.
    :param multiline: If true, allow parameters values to include newlines.
    :raises ValueError: if format spec is invalid, or does not match the string and no
        default is provided.
    """
    pattern = format_spec_to_regex(format_spec, multiline=multiline)
    if not (match := pattern.match(string)):
        if default is _NOT_PASSED:
            raise ValueError(f"String {string!r} does not match format {format_spec!r}")
        return default
    return match.groupdict()


def format_spec_to_regex(format_spec: str, multiline: bool = False) -> re.Pattern:
    """Convert a Python format spec string to a regex pattern with named groups.

    :param format_spec: The format spec to convert.
    :param multiline: If true, allow parameters to include newlines. Adds the re.DOTALL flag
        under-the-hood.
    """
    output = re.escape(format_spec)
    group_name_pattern = re.compile(r"\\{([a-zA-Z_][a-zA-Z0-9_]*)\\}")
    group_names = set(group_name_pattern.findall(output))
    if (invalid_names := _format_spec_field_names(format_spec) - group_names) :
        raise ValueError(
            f"Unsupported field names in format string, only valid Python identifiers are supported: {invalid_names}"
        )
    for group_name in group_names:
        # Set the occurence to declare the group
        output = re.sub(r"\\{(" + group_name + r")\\}", r"(?P<\1>.*)", output, count=1)
        # Set remaining occurences to backreference the group
        output = re.sub(r"\\{(" + group_name + r")\\}", r"(?P=\1)", output)
    flags = [re.DOTALL] if multiline else []
    return re.compile(output, *flags)


def _format_spec_field_names(format_spec: str) -> set[str]:
    """Extract field names from a format spec."""
    return {name for _, name, __, ___ in Formatter().parse(format_spec) if name is not None}
