"""Integration tests: validate concept.md against concept.json.

Tests the full pipeline with the concept rule set, including the
parenthesis-format workflow steps in concept.json.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from markdown_validator.domain.models import ScanReport
from markdown_validator.infrastructure.loader import RuleSetRepository
from markdown_validator.infrastructure.reporter import write_csv_report, write_json_report
from markdown_validator.services.scanner import Scanner
from markdown_validator.services.workflow import run_all_workflows

FIXTURES = Path(__file__).parent.parent / "fixtures"


class TestConceptValidation:
    def test_concept_ruleset_loads(self) -> None:
        rule_set = RuleSetRepository().load(FIXTURES / "concept.json")
        assert len(rule_set.all_rules) > 0

    def test_concept_workflows_normalised(self) -> None:
        """Parenthesis-format steps in concept.json are normalised to dash format."""
        rule_set = RuleSetRepository().load(FIXTURES / "concept.json")
        for wf in rule_set.workflows:
            assert "(" not in wf.steps, f"Steps not normalised: {wf.steps!r}"

    def test_concept_md_scan_returns_report(self) -> None:
        scanner = Scanner()
        report = scanner.validate(
            FIXTURES / "validtemplates" / "concept.md",
            FIXTURES / "concept.json",
        )
        assert isinstance(report, ScanReport)
        assert report.total_rules > 0

    def test_concept_workflows_run(self) -> None:
        rule_set = RuleSetRepository().load(FIXTURES / "concept.json")
        scanner = Scanner()
        report = scanner.validate_with_ruleset(
            FIXTURES / "validtemplates" / "concept.md",
            rule_set,
        )
        wf_results = run_all_workflows(rule_set, report)
        assert len(wf_results) == len(rule_set.workflows)

    def test_reports_written_to_disk(self, tmp_path: Path) -> None:
        scanner = Scanner()
        report = scanner.validate(
            FIXTURES / "validtemplates" / "concept.md",
            FIXTURES / "concept.json",
        )
        json_path = write_json_report(report, tmp_path / "concept_report.json")
        csv_path = write_csv_report(report, tmp_path / "concept_report.csv")
        assert json_path.exists()
        assert csv_path.exists()

    def test_public_api_surface(self) -> None:
        """Verify the public markdown_validator API can be used end-to-end."""
        from markdown_validator import Scanner as PublicScanner
        from markdown_validator import ScanReport as PublicReport

        scanner = PublicScanner()
        report = scanner.validate(
            FIXTURES / "validtemplates" / "concept.md",
            FIXTURES / "concept.json",
        )
        assert isinstance(report, PublicReport)
