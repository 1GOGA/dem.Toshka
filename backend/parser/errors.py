"""Custom exceptions for the parser layer."""

from __future__ import annotations


class DemoParseError(RuntimeError):
    """Raised when Awpy or demoparser2 fails to parse a demo.

    The message is safe to display in the UI / CLI output.
    """


class UnsupportedDemoError(ValueError):
    """Raised when the file is structurally wrong (bad magic, truncated, etc.)."""


class InvalidDemoPathError(ValueError):
    """Raised when path validation fails before the parser is invoked."""
