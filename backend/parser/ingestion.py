"""Ingestion layer — validates path before handing off to the adapter.

Responsibilities:
  1. Check the file exists.
  2. Check the extension is .dem.
  3. Check the file is non-empty.
  4. Compute a simple fingerprint for cache/storage use.
  5. Delegate actual parsing to adapter.parse_demo().

This module NEVER modifies or deletes the source file.
"""

from __future__ import annotations

import hashlib
import logging
from pathlib import Path

from backend.parser.errors import InvalidDemoPathError
from backend.parser.models import ParsedDemo

logger = logging.getLogger(__name__)

_ALLOWED_EXTENSIONS = {".dem"}
_MIN_DEMO_SIZE_BYTES = 1024  # anything smaller is certainly invalid


def fingerprint(path: Path) -> str:
    """Compute a SHA-256 hex digest of the first 4 MB of the file.

    Reading only the beginning is fast enough and unique enough for our cache
    key.  We do NOT read the full file to avoid stalling on large demos.
    """
    sha = hashlib.sha256()
    chunk_size = 4 * 1024 * 1024
    with path.open("rb") as fh:
        sha.update(fh.read(chunk_size))
    return sha.hexdigest()


def validate_demo_path(path: Path) -> None:
    """Raise InvalidDemoPathError with a user-readable message on any problem.

    Checks performed (in order):
      1. Path refers to a file (not a directory).
      2. File exists.
      3. Extension is .dem (case-insensitive).
      4. File size > minimum threshold.

    Args:
        path: Path object to validate.

    Raises:
        InvalidDemoPathError: with a descriptive message.
    """
    if not path.exists():
        raise InvalidDemoPathError(f"File not found: {path}")
    if not path.is_file():
        raise InvalidDemoPathError(f"Path is not a file: {path}")
    if path.suffix.lower() not in _ALLOWED_EXTENSIONS:
        raise InvalidDemoPathError(
            f"Unsupported file type '{path.suffix}'. "
            f"Only {_ALLOWED_EXTENSIONS} are accepted."
        )
    size = path.stat().st_size
    if size < _MIN_DEMO_SIZE_BYTES:
        raise InvalidDemoPathError(
            f"File is too small ({size} bytes) to be a valid CS2 demo."
        )


def ingest(demo_path: str | Path) -> ParsedDemo:
    """Validate and parse a CS2 .dem file.

    This is the single public entry point used by the CLI and future FastAPI
    endpoints.  It validates the path, then calls the Awpy adapter.

    Args:
        demo_path: Path to the .dem file (string or Path).

    Returns:
        ParsedDemo with schema_version, map_name, rounds, players, kills.

    Raises:
        InvalidDemoPathError: if the path fails validation.
        DemoParseError: if Awpy fails to parse the demo.
    """
    path = Path(demo_path).resolve()
    logger.info("Ingesting demo: %s", path)

    validate_demo_path(path)

    fp = fingerprint(path)
    logger.info("Demo fingerprint (SHA-256 first 4 MB): %s", fp)

    # Import adapter here — keeps the ingestion layer testable without awpy
    from backend.parser.adapter import parse_demo

    result = parse_demo(path)
    # Attach fingerprint to raw header so storage can use it later
    result._raw_header["_fingerprint"] = fp
    logger.info(
        "Ingestion complete: map=%s rounds=%d players=%d kills=%d",
        result.map_name,
        len(result.rounds),
        len(result.players),
        len(result.kills),
    )
    return result
