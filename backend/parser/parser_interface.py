"""Abstract interface for CS2 demo parsers.

Enables swappable parsing backends (Awpy, demoparser2, demoinfocs-golang).
"""

from __future__ import annotations

import abc
from pathlib import Path

from backend.parser.models import ParsedDemo


class DemoParserInterface(abc.ABC):
    """Abstract interface that all demo parser adapters must satisfy."""

    @abc.abstractmethod
    def parse_demo(self, path: Path) -> ParsedDemo:
        """Parse a .dem file and return a standardized ParsedDemo domain model."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_backend_name(self) -> str:
        """Return the unique backend identifier (e.g. 'awpy', 'demoparser2')."""
        raise NotImplementedError
