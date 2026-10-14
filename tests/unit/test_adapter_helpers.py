"""Unit tests for backend.parser.adapter helper functions.

Tests the private normalisation helpers (_safe_str, _safe_bool, _safe_int)
and the _row_get utility WITHOUT invoking Awpy or the filesystem.

parse_demo() itself requires a real .dem — that lives in tests/integration/.
"""

from __future__ import annotations

import pytest

# Import the helpers directly (they are module-level functions, not truly private)
from backend.parser.adapter import _safe_bool, _safe_int, _safe_str, _row_get


class TestSafeStr:
    def test_normal_string(self):
        assert _safe_str("hello") == "hello"

    def test_none_returns_none(self):
        assert _safe_str(None) is None

    def test_empty_string_returns_none(self):
        assert _safe_str("") is None

    def test_whitespace_only_returns_none(self):
        assert _safe_str("   ") is None

    def test_nan_string_returns_none(self):
        assert _safe_str("nan") is None

    def test_none_string_returns_none(self):
        assert _safe_str("none") is None

    def test_None_string_returns_none(self):
        assert _safe_str("None") is None

    def test_integer_converts(self):
        assert _safe_str(42) == "42"

    def test_strips_whitespace(self):
        assert _safe_str("  ak47  ") == "ak47"


class TestSafeBool:
    def test_true_bool(self):
        assert _safe_bool(True) is True

    def test_false_bool(self):
        assert _safe_bool(False) is False

    def test_none_returns_none(self):
        assert _safe_bool(None) is None

    def test_int_1_is_true(self):
        assert _safe_bool(1) is True

    def test_int_0_is_false(self):
        assert _safe_bool(0) is False

    def test_float_1_is_true(self):
        assert _safe_bool(1.0) is True


class TestSafeInt:
    def test_normal_int(self):
        assert _safe_int(42) == 42

    def test_string_int(self):
        assert _safe_int("128") == 128

    def test_none_returns_none(self):
        assert _safe_int(None) is None

    def test_invalid_string_returns_none(self):
        assert _safe_int("abc") is None

    def test_float_truncates(self):
        assert _safe_int(3.9) == 3


class TestRowGet:
    def test_first_key_found(self):
        row = {"a": 1, "b": 2}
        assert _row_get(row, "a", "b") == 1

    def test_fallback_to_second_key(self):
        row = {"b": 2}
        assert _row_get(row, "a", "b") == 2

    def test_all_missing_returns_none(self):
        row = {"c": 3}
        assert _row_get(row, "a", "b") is None

    def test_none_value_skipped(self):
        row = {"a": None, "b": 5}
        assert _row_get(row, "a", "b") == 5
