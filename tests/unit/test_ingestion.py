"""Unit tests for backend.parser.ingestion (path validation layer).

These tests exercise validate_demo_path and fingerprint WITHOUT calling Awpy.
All filesystem interactions use pytest's tmp_path fixture — no real demo needed.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from backend.parser.errors import InvalidDemoPathError
from backend.parser.ingestion import fingerprint, validate_demo_path


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _make_demo(tmp_path: Path, name: str = "test.dem", size: int = 2048) -> Path:
    """Write a fake .dem file of `size` bytes so validation passes."""
    p = tmp_path / name
    p.write_bytes(b"\x00" * size)
    return p


# ─── validate_demo_path ──────────────────────────────────────────────────────

class TestValidateDemoPath:
    def test_valid_dem_file_passes(self, tmp_path):
        p = _make_demo(tmp_path)
        # Should not raise
        validate_demo_path(p)

    def test_missing_file_raises(self, tmp_path):
        p = tmp_path / "missing.dem"
        with pytest.raises(InvalidDemoPathError, match="not found"):
            validate_demo_path(p)

    def test_wrong_extension_txt_raises(self, tmp_path):
        p = tmp_path / "demo.txt"
        p.write_bytes(b"\x00" * 2048)
        with pytest.raises(InvalidDemoPathError, match="Unsupported file type"):
            validate_demo_path(p)

    def test_wrong_extension_mp4_raises(self, tmp_path):
        p = tmp_path / "clip.mp4"
        p.write_bytes(b"\x00" * 2048)
        with pytest.raises(InvalidDemoPathError, match="Unsupported file type"):
            validate_demo_path(p)

    def test_no_extension_raises(self, tmp_path):
        p = tmp_path / "nodemoextension"
        p.write_bytes(b"\x00" * 2048)
        with pytest.raises(InvalidDemoPathError, match="Unsupported file type"):
            validate_demo_path(p)

    def test_extension_case_insensitive(self, tmp_path):
        """Windows often stores with .DEM uppercase — must be accepted."""
        p = tmp_path / "MATCH.DEM"
        p.write_bytes(b"\x00" * 2048)
        validate_demo_path(p)  # Should not raise

    def test_empty_file_raises(self, tmp_path):
        p = tmp_path / "empty.dem"
        p.write_bytes(b"")
        with pytest.raises(InvalidDemoPathError, match="too small"):
            validate_demo_path(p)

    def test_tiny_file_raises(self, tmp_path):
        p = tmp_path / "tiny.dem"
        p.write_bytes(b"\x00" * 10)
        with pytest.raises(InvalidDemoPathError, match="too small"):
            validate_demo_path(p)

    def test_directory_raises(self, tmp_path):
        d = tmp_path / "some.dem"
        d.mkdir()
        with pytest.raises(InvalidDemoPathError, match="not a file"):
            validate_demo_path(d)


# ─── fingerprint ─────────────────────────────────────────────────────────────

class TestFingerprint:
    def test_fingerprint_is_hex_string(self, tmp_path):
        p = _make_demo(tmp_path)
        fp = fingerprint(p)
        assert isinstance(fp, str)
        assert len(fp) == 64  # SHA-256 hex = 64 chars
        assert all(c in "0123456789abcdef" for c in fp)

    def test_same_file_same_fingerprint(self, tmp_path):
        p = _make_demo(tmp_path)
        assert fingerprint(p) == fingerprint(p)

    def test_different_content_different_fingerprint(self, tmp_path):
        p1 = tmp_path / "a.dem"
        p2 = tmp_path / "b.dem"
        p1.write_bytes(b"\x00" * 2048)
        p2.write_bytes(b"\xFF" * 2048)
        assert fingerprint(p1) != fingerprint(p2)

    def test_large_file_only_reads_first_chunk(self, tmp_path):
        """Fingerprint must complete quickly even for huge files.
        We simulate by writing 5 MB and checking it returns a valid hash.
        """
        p = tmp_path / "large.dem"
        p.write_bytes(b"\xAB" * (5 * 1024 * 1024))
        fp = fingerprint(p)
        assert len(fp) == 64
