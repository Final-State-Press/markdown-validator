"""Unit tests for markdown_validator.services.scanner."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from markdown_validator.domain.models import RuleModel, RuleSetModel, RulesSection, ScanReport
from markdown_validator.infrastructure.loader import RuleSetRepository
from markdown_validator.services.scanner import Scanner


# ---------------------------------------------------------------------------
# Helper: build minimal in-memory rule set without touching disk
# ---------------------------------------------------------------------------

def _make_rule_set(*rules: RuleModel) -> RuleSetModel:
    headers = [r for r in rules if r.type == "header"]
    bodies = [r for r in rules if r.type == "body"]
    return RuleSetModel(rules=RulesSection(header=headers, body=bodies))


class TestScannerValidate:
    def test_validate_returns_scan_report(
        self, azure_md_path: Path, checkworkflow_json_path: Path
    ) -> None:
        scanner = Scanner()
        report = scanner.validate(azure_md_path, checkworkflow_json_path)
        assert isinstance(report, ScanReport)

    def test_report_has_results(
        self, azure_md_path: Path, checkworkflow_json_path: Path
    ) -> None:
        scanner = Scanner()
        report = scanner.validate(azure_md_path, checkworkflow_json_path)
        assert report.total_rules > 0
        assert len(report.results) == report.total_rules

    def test_score_consistent(
        self, azure_md_path: Path, checkworkflow_json_path: Path
    ) -> None:
        scanner = Scanner()
        report = scanner.validate(azure_md_path, checkworkflow_json_path)
        manual_score = sum(1 for r in report.results if r.passed)
        assert report.score == manual_score

    def test_file_not_found_raises(self, checkworkflow_json_path: Path) -> None:
        scanner = Scanner()
        with pytest.raises(FileNotFoundError):
            scanner.validate("/no/such/file.md", checkworkflow_json_path)

    def test_bad_rules_file_raises(self, azure_md_path: Path, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text("{}", encoding="utf-8")
        scanner = Scanner()
        with pytest.raises((FileNotFoundError, ValueError)):
            scanner.validate(azure_md_path, bad)


class TestScannerValidateWithRuleset:
    def test_all_required_pass_sets_passed_true(self, azure_md_path: Path) -> None:
        # Rule that is always true: check h1 count > 0
        rule = RuleModel(
            id=1, name="h1-exists", type="body", query="/html/body/h1",
            flag="count", operation=">", value="0", level="Required"
        )
        rule_set = _make_rule_set(rule)
        scanner = Scanner()
        report = scanner.validate_with_ruleset(azure_md_path, rule_set)
        assert report.passed is True

    def test_required_fail_sets_passed_false(self, azure_md_path: Path) -> None:
        rule = RuleModel(
            id=1, name="impossible", type="body", query="/html/body/h1",
            flag="text", operation="==", value="This title will never exist xyz",
            level="Required"
        )
        rule_set = _make_rule_set(rule)
        scanner = Scanner()
        report = scanner.validate_with_ruleset(azure_md_path, rule_set)
        assert report.passed is False

    def test_suggested_fail_does_not_fail_scan(self, azure_md_path: Path) -> None:
        rule = RuleModel(
            id=1, name="suggested-fail", type="body", query="/html/body/h1",
            flag="text", operation="==", value="impossible text xyz",
            level="Suggested"
        )
        rule_set = _make_rule_set(rule)
        scanner = Scanner()
        report = scanner.validate_with_ruleset(azure_md_path, rule_set)
        assert report.passed is True  # no Required rules at all → passes

    def test_report_filepath_is_absolute(self, azure_md_path: Path) -> None:
        rule = RuleModel(id=1, name="x", type="body", query="/html/body/h1",
                         flag="count", operation=">", value="0")
        rule_set = _make_rule_set(rule)
        scanner = Scanner()
        report = scanner.validate_with_ruleset(azure_md_path, rule_set)
        assert Path(report.filepath).is_absolute()


class TestScannerValidateDirectory:
    def test_returns_list_of_reports(self, tmp_path: Path, checkworkflow_json_path: Path) -> None:
        fixtures = Path(__file__).parent.parent.parent / "fixtures" / "validtemplates"
        scanner = Scanner()
        reports = scanner.validate_directory(fixtures, checkworkflow_json_path)
        assert isinstance(reports, list)
        assert len(reports) >= 1

    def test_not_a_directory_raises(
        self, azure_md_path: Path, checkworkflow_json_path: Path
    ) -> None:
        scanner = Scanner()
        with pytest.raises(NotADirectoryError):
            scanner.validate_directory(azure_md_path, checkworkflow_json_path)


class TestScannerCustomRepository:
    def test_custom_repository_is_used(self, azure_md_path: Path) -> None:
        mock_repo = MagicMock(spec=RuleSetRepository)
        rule = RuleModel(id=1, name="x", type="body", query="/html/body/h1",
                         flag="count", operation=">", value="0")
        rule_set = _make_rule_set(rule)
        mock_repo.load.return_value = rule_set

        scanner = Scanner(repository=mock_repo)
        report = scanner.validate(azure_md_path, "any_path.json")

        mock_repo.load.assert_called_once_with("any_path.json")
        assert isinstance(report, ScanReport)
