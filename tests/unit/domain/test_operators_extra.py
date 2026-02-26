"""Additional operator tests for op_date edge cases."""

from __future__ import annotations

from markdown_validator.domain.operators import op_date, _parse_date
import pytest
from datetime import date


class TestParseDateHelper:
    def test_slash_format(self) -> None:
        d = _parse_date("1/15/2023")
        assert d == date(2023, 1, 15)

    def test_dash_format(self) -> None:
        d = _parse_date("3-20-2021")
        assert d == date(2021, 3, 20)

    def test_two_digit_year(self) -> None:
        d = _parse_date("6-1-24")
        assert d == date(2024, 6, 1)

    def test_invalid_raises(self) -> None:
        with pytest.raises(ValueError):
            _parse_date("not-a-date-at-all")


class TestOpDateEdgeCases:
    def test_equal_operator(self) -> None:
        assert op_date("1-1-2020", "==", "1-1-2020") is True

    def test_not_equal_operator(self) -> None:
        assert op_date("1-1-2020", "!=", "1-1-2021") is True

    def test_invalid_comparison_date(self) -> None:
        assert op_date("1-1-2020", "<", "not-a-date") is False

    def test_invalid_document_date(self) -> None:
        assert op_date("not-a-date", "<", "now") is False
