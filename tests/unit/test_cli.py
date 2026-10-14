"""Unit tests for the CLI entry point (backend.parser_cli).

Tests path-validation errors and help output WITHOUT a real demo or Awpy.
Integration tests with a real demo live in tests/integration/.
"""

from __future__ import annotations

import pytest

from backend.parser_cli import main


class TestCLIHelp:
    def test_help_exits_zero(self):
        with pytest.raises(SystemExit) as exc_info:
            main(["--help"])
        assert exc_info.value.code == 0

    def test_version_exits_zero(self):
        with pytest.raises(SystemExit) as exc_info:
            main(["--version"])
        assert exc_info.value.code == 0


class TestCLIErrorHandling:
    def test_no_args_returns_exit_1(self):
        """No demo path provided — should exit with code 1."""
        code = main([])
        assert code == 1

    def test_missing_file_returns_exit_1(self, tmp_path):
        missing = str(tmp_path / "nonexistent.dem")
        code = main([missing])
        assert code == 1

    def test_wrong_extension_returns_exit_1(self, tmp_path):
        f = tmp_path / "clip.mp4"
        f.write_bytes(b"\x00" * 2048)
        code = main([str(f)])
        assert code == 1

    def test_empty_file_returns_exit_1(self, tmp_path):
        f = tmp_path / "empty.dem"
        f.write_bytes(b"")
        code = main([str(f)])
        assert code == 1

    def test_directory_as_path_returns_exit_1(self, tmp_path):
        d = tmp_path / "fake.dem"
        d.mkdir()
        code = main([str(d)])
        assert code == 1
