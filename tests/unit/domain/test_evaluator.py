"""Unit tests for markdown_validator.domain.evaluator."""

from __future__ import annotations

from pathlib import Path

import pytest

from markdown_validator.domain.evaluator import (
    _apply_string_operator,
    _xpath_query,
    evaluate_rule,
)
from markdown_validator.domain.models import ParsedDocument, RuleModel, ValidationResult


# ---------------------------------------------------------------------------
# Test document
# ---------------------------------------------------------------------------

SAMPLE_HTML = """
<html><body>
<h1>Azure Stack Hub overview</h1>
<h2>Why use Azure Stack Hub?</h2>
<p>This is a paragraph with some content.</p>
<h2>Architecture</h2>
<p>Second paragraph.</p>
</body></html>
"""

SAMPLE_META = {
    "title": "Azure Stack Hub overview",
    "ms.topic": "overview",
    "ms.date": "1-1-2020",
    "author": "mabrigg",
}


@pytest.fixture
def sample_doc() -> ParsedDocument:
    return ParsedDocument(
        filepath=Path("/tmp/sample.md"),
        metadata=SAMPLE_META,
        html=SAMPLE_HTML,
    )


# ---------------------------------------------------------------------------
# Header rule evaluation
# ---------------------------------------------------------------------------

class TestHeaderRuleEvaluation:
    def test_equal_match(self, sample_doc: ParsedDocument) -> None:
        rule = RuleModel(id=1, name="topic", type="header", query="ms.topic",
                         flag="value", operation="==", value="overview")
        result = evaluate_rule(rule, sample_doc)
        assert result.passed is True

    def test_equal_no_match(self, sample_doc: ParsedDocument) -> None:
        rule = RuleModel(id=1, name="topic", type="header", query="ms.topic",
                         flag="value", operation="==", value="tutorial")
        result = evaluate_rule(rule, sample_doc)
        assert result.passed is False

    def test_check_flag_key_exists(self, sample_doc: ParsedDocument) -> None:
        rule = RuleModel(id=2, name="author-check", type="header", query="author",
                         flag="check", operation="==", value="")
        result = evaluate_rule(rule, sample_doc)
        assert result.passed is True

    def test_check_flag_key_missing(self, sample_doc: ParsedDocument) -> None:
        rule = RuleModel(id=3, name="missing", type="header", query="no.such.key",
                         flag="check", operation="==", value="")
        result = evaluate_rule(rule, sample_doc)
        assert result.passed is False

    def test_date_flag_less_than_now(self, sample_doc: ParsedDocument) -> None:
        rule = RuleModel(id=4, name="date-check", type="header", query="ms.date",
                         flag="date", operation="<", value="now")
        result = evaluate_rule(rule, sample_doc)
        assert result.passed is True

    def test_missing_key_returns_false(self, sample_doc: ParsedDocument) -> None:
        rule = RuleModel(id=5, name="x", type="header", query="nonexistent",
                         flag="value", operation="==", value="v")
        result = evaluate_rule(rule, sample_doc)
        assert result.passed is False

    def test_contains_operator(self, sample_doc: ParsedDocument) -> None:
        rule = RuleModel(id=6, name="x", type="header", query="title",
                         flag="value", operation="[]", value="Azure")
        result = evaluate_rule(rule, sample_doc)
        assert result.passed is True


# ---------------------------------------------------------------------------
# Body rule evaluation
# ---------------------------------------------------------------------------

class TestBodyRuleEvaluation:
    def test_h1_count_equals_one(self, sample_doc: ParsedDocument) -> None:
        rule = RuleModel(id=10, name="h1-count", type="body", query="/html/body/h1",
                         flag="count", operation="==", value="1")
        result = evaluate_rule(rule, sample_doc)
        assert result.passed is True

    def test_h2_count_equals_two(self, sample_doc: ParsedDocument) -> None:
        rule = RuleModel(id=11, name="h2-count", type="body", query="/html/body/h2",
                         flag="count", operation="==", value="2")
        result = evaluate_rule(rule, sample_doc)
        assert result.passed is True

    def test_h1_text_match(self, sample_doc: ParsedDocument) -> None:
        rule = RuleModel(id=12, name="h1-text", type="body", query="/html/body/h1",
                         flag="text", operation="==", value="Azure Stack Hub overview")
        result = evaluate_rule(rule, sample_doc)
        assert result.passed is True

    def test_h1_starts_with(self, sample_doc: ParsedDocument) -> None:
        rule = RuleModel(id=13, name="h1-starts", type="body", query="/html/body/h1",
                         flag="text", operation="[:", value="Azure")
        result = evaluate_rule(rule, sample_doc)
        assert result.passed is True

    def test_xpath_no_results_returns_false(self, sample_doc: ParsedDocument) -> None:
        rule = RuleModel(id=14, name="h3-check", type="body", query="/html/body/h3",
                         flag="count", operation="==", value="1")
        result = evaluate_rule(rule, sample_doc)
        assert result.passed is False

    def test_result_has_correct_fields(self, sample_doc: ParsedDocument) -> None:
        rule = RuleModel(id=15, name="test-rule", type="body", query="/html/body/h1",
                         flag="count", operation="==", value="1",
                         level="Suggested", mitigation="Fix this")
        result = evaluate_rule(rule, sample_doc)
        assert result.rule_id == 15
        assert result.rule_name == "test-rule"
        assert result.level == "Suggested"
        assert result.mitigation == "Fix this"
        assert isinstance(result, ValidationResult)


# ---------------------------------------------------------------------------
# XPath helper tests
# ---------------------------------------------------------------------------

class TestXpathQuery:
    def test_text_flag(self) -> None:
        results = _xpath_query(SAMPLE_HTML, "/html/body/h1", "text")
        assert results is not None
        assert "Azure Stack Hub overview" in results

    def test_count_flag(self) -> None:
        results = _xpath_query(SAMPLE_HTML, "/html/body/h2", "count")
        assert results == [2]

    def test_no_results_returns_none(self) -> None:
        results = _xpath_query(SAMPLE_HTML, "/html/body/h3", "text")
        assert results is None

    def test_dom_flag(self) -> None:
        results = _xpath_query(SAMPLE_HTML, "/html/body/h1", "dom")
        assert results is not None
        assert "h1" in results

    def test_invalid_xpath_returns_none(self) -> None:
        results = _xpath_query(SAMPLE_HTML, "//[@invalid", "text")
        assert results is None


# ---------------------------------------------------------------------------
# Operator dispatcher tests
# ---------------------------------------------------------------------------

class TestApplyStringOperator:
    def test_known_operator(self) -> None:
        assert _apply_string_operator("==", "hello", "hello") is True

    def test_unknown_operator_returns_false(self) -> None:
        assert _apply_string_operator("??", "hello", "hello") is False
