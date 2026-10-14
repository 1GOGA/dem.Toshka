"""Serialisation helpers — convert ParsedDemo to/from JSON-safe dicts.

Schema version is embedded in every output so the storage layer can detect
stale cached data and trigger a re-parse.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path
from typing import Any

from backend.parser.models import ParsedDemo


def to_dict(result: ParsedDemo) -> dict[str, Any]:
    """Convert a ParsedDemo to a plain JSON-serialisable dict."""
    d = dataclasses.asdict(result)
    # Remove private raw header — not for external consumers
    d.pop("_raw_header", None)
    return d


def to_json(result: ParsedDemo, indent: int = 2) -> str:
    """Return a formatted JSON string of the ParsedDemo."""
    return json.dumps(to_dict(result), indent=indent, ensure_ascii=False)


def save_json(result: ParsedDemo, output_path: Path) -> None:
    """Write the ParsedDemo to a JSON file.

    Args:
        result:      The parsed demo result.
        output_path: Destination file path.  Parent directory must exist.
    """
    output_path.write_text(to_json(result), encoding="utf-8")
