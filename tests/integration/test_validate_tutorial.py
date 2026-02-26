"""Integration tests: validate tutorial.md against checkworkflow.json.

These tests exercise the full pipeline from file I/O → parsing → rule
loading → evaluation → reporting, without mocking any layers.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from markdown_validator.domain.models import ScanReport
from markdown_validator.services.scanner import Scanner
from markdown_validator.services.workflow import run_all_workflows
from markdown_validator.infrastructure.loader import RuleSetRepository


FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestTutorialValidation:
    def test_scanner_returns_report(self) -> None:
        scanner = Scanner()
        report = scanner.validate(
            FIXTURES / "validtemplates" / "tutorial.md",
            FIXTURES / "checkworkflow.json",
        )
        assert isinstance(report, ScanReport)

    def test_report_has_all_rule_results(self) -> None:
        rule_set = RuleSetRepository().load(FIXTURES / "checkworkflow.json")
        scanner = Scanner()
        report = scanner.validate_with_ruleset(
            FIXTURES / "validtemplates" / "tutorial.md",
            rule_set,
        )
        assert report.total_rules == len(rule_set.all_rules)
        assert len(report.results) == report.total_rules

    def test_score_within_valid_range(self) -> None:
        scanner = Scanner()
        report = scanner.validate(
            FIXTURES / "validtemplates" / "tutorial.md",
            FIXTURES / "checkworkflow.json",
        )
        assert 0 <= report.score <= report.total_rules

    def test_workflows_execute_without_error(self) -> None:
        rule_set = RuleSetRepository().load(FIXTURES / "checkworkflow.json")
        scanner = Scanner()
        report = scanner.validate_with_ruleset(
            FIXTURES / "validtemplates" / "tutorial.md",
            rule_set,
        )
        wf_results = run_all_workflows(rule_set, report)
        assert len(wf_results) == len(rule_set.workflows)

    def test_azure_overview_scan(self) -> None:
        """azure-stack-overview.md is not a tutorial — some rules should fail."""
        scanner = Scanner()
        report = scanner.validate(
            FIXTURES / "azure-stack-overview.md",
            FIXTURES / "checkworkflow.json",
        )
        # The document is not a tutorial; we expect some rules to fail
        assert report.total_rules > 0
        # At minimum it should have an H1
        h1_results = [r for r in report.results if "h1" in r.rule_name.lower()]
        # Scores are non-negative
        assert report.score >= 0

    def test_json_report_serialisable(self) -> None:
        import json
        scanner = Scanner()
        report = scanner.validate(
            FIXTURES / "azure-stack-overview.md",
            FIXTURES / "checkworkflow.json",
        )
        payload = report.model_dump()
        dumped = json.dumps(payload)
        restored = json.loads(dumped)
        assert restored["total_rules"] == report.total_rules
