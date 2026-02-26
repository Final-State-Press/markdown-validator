"""Unit tests for markdown_validator.domain.operators."""

from __future__ import annotations

import pytest

from markdown_validator.domain.operators import (
    OPERATOR_REGISTRY,
    op_contains,
    op_date,
    op_ends_with,
    op_equal,
    op_greater,
    op_length,
    op_less,
    op_not_equal,
    op_regex,
    op_starts_with,
)


class TestOpEqual:
    def test_equal_strings(self) -> None:
        assert op_equal("hello", "hello") is True

    def test_unequal_strings(self) -> None:
        assert op_equal("hello", "world") is False

    def test_strips_whitespace(self) -> None:
        assert op_equal("  hello  ", "hello") is True

    def test_empty_strings(self) -> None:
        assert op_equal("", "") is True


class TestOpNotEqual:
    def test_unequal(self) -> None:
        assert op_not_equal("a", "b") is True

    def test_equal_returns_false(self) -> None:
        assert op_not_equal("x", "x") is False


class TestOpGreater:
    def test_greater(self) -> None:
        assert op_greater("5", "3") is True

    def test_not_greater(self) -> None:
        assert op_greater("3", "5") is False

    def test_equal_is_not_greater(self) -> None:
        assert op_greater("5", "5") is False

    def test_non_numeric_returns_false(self) -> None:
        assert op_greater("abc", "3") is False


class TestOpLess:
    def test_less(self) -> None:
        assert op_less("2", "5") is True

    def test_not_less(self) -> None:
        assert op_less("5", "2") is False

    def test_non_numeric_returns_false(self) -> None:
        assert op_less("x", "5") is False


class TestOpContains:
    def test_found(self) -> None:
        assert op_contains("Hello World", "world") is True

    def test_not_found(self) -> None:
        assert op_contains("Hello World", "python") is False

    def test_case_insensitive(self) -> None:
        assert op_contains("AZURE STACK HUB", "azure") is True


class TestOpStartsWith:
    def test_starts(self) -> None:
        assert op_starts_with("Tutorial: Getting started", "Tutorial:") is True

    def test_not_starts(self) -> None:
        assert op_starts_with("Getting started", "Tutorial:") is False


class TestOpEndsWith:
    def test_ends(self) -> None:
        assert op_ends_with("Hello World", "World") is True

    def test_not_ends(self) -> None:
        assert op_ends_with("Hello World", "Hello") is False


class TestOpRegex:
    def test_match(self) -> None:
        assert op_regex("Tutorial: My guide", r"^Tutorial") is True

    def test_no_match(self) -> None:
        assert op_regex("How to guide", r"^Tutorial") is False

    def test_invalid_pattern_returns_false(self) -> None:
        assert op_regex("text", "[invalid(") is False

    def test_dotall(self) -> None:
        assert op_regex("line1\nline2", r"line1.*line2") is True


class TestOpLength:
    def test_within_limit(self) -> None:
        assert op_length("short", "10") is True

    def test_exceeds_limit(self) -> None:
        assert op_length("a" * 200, "100") is False

    def test_non_numeric_value_returns_false(self) -> None:
        assert op_length("text", "abc") is False


class TestOpDate:
    def test_less_than_today(self) -> None:
        # A date from 2020 should be less than today
        assert op_date("1-1-2020", "<", "now") is True

    def test_greater_than_old_date(self) -> None:
        assert op_date("1-1-2025", ">", "1-1-2020") is True

    def test_invalid_date_returns_false(self) -> None:
        assert op_date("not-a-date", "<", "now") is False

    def test_day_offset(self) -> None:
        # A date from 2020 should be older than 100 days ago
        assert op_date("1-1-2020", "<", "100") is True

    def test_unknown_operator_returns_false(self) -> None:
        assert op_date("1-1-2020", "??", "now") is False


class TestOperatorRegistry:
    def test_all_expected_keys_present(self) -> None:
        expected = {"==", "!=", ">", "<", "[]", "[:", ":]", "r", "l"}
        assert expected.issubset(OPERATOR_REGISTRY.keys())

    def test_registry_values_are_callable(self) -> None:
        for key, fn in OPERATOR_REGISTRY.items():
            assert callable(fn), f"Registry entry {key!r} is not callable"
