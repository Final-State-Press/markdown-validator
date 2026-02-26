"""Unit tests for markdown_validator.domain.models."""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from markdown_validator.domain.models import (
    ParsedDocument,
    RuleModel,
    RuleSetModel,
    RulesSection,
    ScanReport,
    ValidationResult,
    WorkflowModel,
    WorkflowResult,
)


class TestRuleModel:
    def test_valid_header_rule(self) -> None:
        rule = RuleModel(
            id=1, name="test", type="header", query="ms.topic",
            flag="value", operation="==", value="tutorial"
        )
        assert rule.id == 1
        assert rule.type == "header"
        assert rule.level == "Required"
        assert rule.mitigation == ""

    def test_string_id_is_coerced_to_int(self) -> None:
        rule = RuleModel(
            id="5", name="t", type="body", query="/html/body/h1",  # type: ignore[arg-type]
            flag="count", operation="==", value="1"
        )
        assert rule.id == 5

    def test_non_numeric_id_raises(self) -> None:
        with pytest.raises(ValidationError, match="numeric"):
            RuleModel(
                id="abc", name="t", type="body", query="x",  # type: ignore[arg-type]
                flag="", operation="==", value="1"
            )

    def test_zero_id_raises(self) -> None:
        with pytest.raises(ValidationError):
            RuleModel(id=0, name="t", type="body", query="x", flag="", operation="==", value="1")

    def test_invalid_type_raises(self) -> None:
        with pytest.raises(ValidationError):
            RuleModel(
                id=1, name="t", type="invalid",  # type: ignore[arg-type]
                query="x", flag="", operation="==", value="1"
            )

    def test_type_normalised_to_lowercase(self) -> None:
        rule = RuleModel(
            id=1, name="t", type="HEADER",  # type: ignore[arg-type]
            query="k", flag="value", operation="==", value="v"
        )
        assert rule.type == "header"

    def test_rule_is_frozen(self) -> None:
        rule = RuleModel(
            id=1, name="t", type="header", query="k",
            flag="value", operation="==", value="v"
        )
        with pytest.raises(Exception):
            rule.id = 99  # type: ignore[misc]

    def test_suggested_level(self) -> None:
        rule = RuleModel(
            id=1, name="t", type="body", query="x",
            flag="count", operation="==", value="1", level="Suggested"
        )
        assert rule.level == "Suggested"


class TestRulesSection:
    def test_duplicate_ids_raise(self) -> None:
        r1 = RuleModel(id=1, name="a", type="header", query="k", flag="value", operation="==", value="v")
        r2 = RuleModel(id=1, name="b", type="body", query="x", flag="count", operation="==", value="1")
        with pytest.raises(ValidationError, match="Duplicate rule id"):
            RulesSection(header=[r1], body=[r2])

    def test_empty_sections_allowed(self) -> None:
        section = RulesSection()
        assert section.header == []
        assert section.body == []


class TestRuleSetModel:
    def test_all_rules_order(self) -> None:
        r1 = RuleModel(id=1, name="h", type="header", query="k", flag="value", operation="==", value="v")
        r2 = RuleModel(id=2, name="b", type="body", query="x", flag="count", operation="==", value="1")
        rs = RuleSetModel(rules=RulesSection(header=[r1], body=[r2]))
        assert rs.all_rules == [r1, r2]

    def test_rules_by_id(self) -> None:
        r1 = RuleModel(id=10, name="h", type="header", query="k", flag="value", operation="==", value="v")
        rs = RuleSetModel(rules=RulesSection(header=[r1]))
        assert rs.rules_by_id[10] == r1


class TestWorkflowModel:
    def test_normalises_parenthesis_format(self) -> None:
        wf = WorkflowModel(name="test", steps="(S,1)(1,E)")
        assert wf.steps == "S-1,1-E"

    def test_preserves_dash_format(self) -> None:
        wf = WorkflowModel(name="test", steps="S-1,1-D,T-2,M-E")
        assert wf.steps == "S-1,1-D,T-2,M-E"

    def test_frozen(self) -> None:
        wf = WorkflowModel(name="test", steps="S-1,1-E")
        with pytest.raises(Exception):
            wf.name = "other"  # type: ignore[misc]


class TestParsedDocument:
    def test_frozen_dataclass(self) -> None:
        doc = ParsedDocument(
            filepath=Path("/tmp/test.md"),
            metadata={"title": "Hello"},
            html="<h1>Hello</h1>",
        )
        with pytest.raises(Exception):
            doc.html = "other"  # type: ignore[misc]


class TestValidationResult:
    def test_defaults(self) -> None:
        r = ValidationResult(rule_id=1, rule_name="test", passed=True)
        assert r.level == "Required"
        assert r.expected_value == ""
        assert r.mitigation == ""

    def test_frozen(self) -> None:
        r = ValidationResult(rule_id=1, rule_name="test", passed=True)
        with pytest.raises(Exception):
            r.passed = False  # type: ignore[misc]


class TestScanReport:
    def test_passed_flag(self) -> None:
        results = [
            ValidationResult(rule_id=1, rule_name="a", passed=True),
            ValidationResult(rule_id=2, rule_name="b", passed=False, level="Suggested"),
        ]
        report = ScanReport(
            filepath="/f.md", score=1, total_rules=2, passed=True, results=results
        )
        assert report.passed is True
        assert report.score == 1
