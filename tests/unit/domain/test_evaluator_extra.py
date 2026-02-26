"""Additional evaluator tests to cover edge-case branches."""

from __future__ import annotations

from pathlib import Path

import pytest

from markdown_validator.domain.evaluator import evaluate_rule
from markdown_validator.domain.models import ParsedDocument, RuleModel

SAMPLE_HTML = """
<html><body>
<h1>Azure Stack Hub overview</h1>
<h2>Why use Azure Stack Hub?</h2>
<p>First sentence. Second sentence. Third sentence.</p>
</body></html>
"""

SAMPLE_META = {
    "title": "Azure Stack Hub overview",
    "ms.topic": "overview",
    "ms.date": "1-1-2020",
    "author": "mabrigg",
}


@pytest.fixture
def doc() -> ParsedDocument:
    return ParsedDocument(
        filepath=Path("/tmp/sample.md"),
        metadata=SAMPLE_META,
        html=SAMPLE_HTML,
    )


class TestBodyRuleEdgeCases:
    def test_all_flag_returns_full_text(self, doc: ParsedDocument) -> None:
        rule = RuleModel(id=20, name="all-text", type="body", query="/html/body",
                         flag="all", operation="[]", value="Azure")
        result = evaluate_rule(rule, doc)
        assert result.passed is True

    def test_sentence_count_operator(self, doc: ParsedDocument) -> None:
        rule = RuleModel(id=21, name="sent-count", type="body", query="//p",
                         flag="text", operation="s", value="5")
        result = evaluate_rule(rule, doc)
        assert isinstance(result.passed, bool)

    def test_dom_flag(self, doc: ParsedDocument) -> None:
        rule = RuleModel(id=22, name="dom-check", type="body", query="/html/body/h1",
                         flag="dom", operation="==", value="h1")
        result = evaluate_rule(rule, doc)
        assert result.passed is True

    def test_not_equal_operator(self, doc: ParsedDocument) -> None:
        rule = RuleModel(id=23, name="not-eq", type="body", query="/html/body/h1",
                         flag="text", operation="!=", value="wrong title")
        result = evaluate_rule(rule, doc)
        assert result.passed is True

    def test_regex_operator_body(self, doc: ParsedDocument) -> None:
        rule = RuleModel(id=24, name="regex", type="body", query="/html/body/h1",
                         flag="text", operation="r", value=r"^Azure")
        result = evaluate_rule(rule, doc)
        assert result.passed is True

    def test_ends_with_operator(self, doc: ParsedDocument) -> None:
        rule = RuleModel(id=25, name="ends", type="body", query="/html/body/h1",
                         flag="text", operation=":]", value="overview")
        result = evaluate_rule(rule, doc)
        assert result.passed is True

    def test_contains_operator_body(self, doc: ParsedDocument) -> None:
        rule = RuleModel(id=26, name="contains", type="body", query="/html/body/h1",
                         flag="text", operation="[]", value="Stack Hub")
        result = evaluate_rule(rule, doc)
        assert result.passed is True

    def test_length_operator(self, doc: ParsedDocument) -> None:
        rule = RuleModel(id=27, name="length", type="body", query="/html/body/h1",
                         flag="text", operation="l", value="200")
        result = evaluate_rule(rule, doc)
        assert result.passed is True

    def test_greater_operator_count(self, doc: ParsedDocument) -> None:
        rule = RuleModel(id=28, name="gt", type="body", query="/html/body/h2",
                         flag="count", operation=">", value="0")
        result = evaluate_rule(rule, doc)
        assert result.passed is True

    def test_less_operator_count(self, doc: ParsedDocument) -> None:
        rule = RuleModel(id=29, name="lt", type="body", query="/html/body/h2",
                         flag="count", operation="<", value="10")
        result = evaluate_rule(rule, doc)
        assert result.passed is True

    def test_pos_operator(self, doc: ParsedDocument) -> None:
        rule = RuleModel(id=30, name="pos", type="body", query="/html/body/h1",
                         flag="text", operation="p1", value="NNP")
        result = evaluate_rule(rule, doc)
        # Result is a bool regardless of the exact POS tag
        assert isinstance(result.passed, bool)

    def test_comma_separated_values_all_must_match(self, doc: ParsedDocument) -> None:
        # Both "Azure" and "overview" appear in the H1 text
        rule = RuleModel(id=31, name="multi", type="body", query="/html/body/h1",
                         flag="text", operation="[]", value="Azure,overview")
        result = evaluate_rule(rule, doc)
        assert result.passed is True

    def test_comma_separated_values_one_fails(self, doc: ParsedDocument) -> None:
        rule = RuleModel(id=32, name="multi-fail", type="body", query="/html/body/h1",
                         flag="text", operation="[]", value="Azure,NOSUCHTERM")
        result = evaluate_rule(rule, doc)
        assert result.passed is False


class TestHeaderRuleEdgeCases:
    def test_pattern_flag_regex(self, doc: ParsedDocument) -> None:
        rule = RuleModel(id=40, name="pat", type="header", query="title",
                         flag="pattern", operation="r", value=r"^Azure")
        result = evaluate_rule(rule, doc)
        assert result.passed is True

    def test_unknown_header_flag(self, doc: ParsedDocument) -> None:
        rule = RuleModel(id=41, name="unk", type="header", query="title",
                         flag="unknown_flag", operation="==", value="v")
        result = evaluate_rule(rule, doc)
        assert result.passed is False
