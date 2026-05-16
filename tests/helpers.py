import pathlib
import unittest


def normalize_path(path: str | pathlib.Path) -> pathlib.Path:
    """Return a canonical path for cross-platform test comparisons."""
    return pathlib.Path(path).expanduser().resolve(strict=False)


def assert_same_path(
    testcase: unittest.TestCase,
    actual: str | pathlib.Path,
    expected: str | pathlib.Path,
    msg: str | None = None,
) -> None:
    """Assert that two path strings identify the same filesystem location."""
    testcase.assertEqual(normalize_path(expected), normalize_path(actual), msg=msg)


def parse_cli_fields(output: str) -> dict[str, str]:
    """Parse simple Taurworks CLI diagnostic `key: value` lines.

    Taurworks diagnostics are intentionally human-readable, with top-level lines
    commonly rendered as either `key: value` or `- key: value`. Tests should use
    this helper for path-bearing fields so they can compare values semantically
    instead of matching raw path substrings.
    """
    fields: dict[str, str] = {}
    for raw_line in output.splitlines():
        line = raw_line.strip()
        if line.startswith("- "):
            line = line[2:]
        if ": " not in line:
            continue
        key, value = line.split(": ", 1)
        if key and key not in fields:
            fields[key] = value
    return fields
