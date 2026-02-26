"""Unit tests for markdown_validator.infrastructure.reporter."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from markdown_validator.domain.models import ScanReport, ValidationResult
from markdown_validator.infrastructure.reporter import write_csv_report, write_json_report


@pytest.fixture
def sample_report() -> ScanReport:
    return ScanReport(
        filepath="/tmp/test.md",
        score=2,
        total_rules=3,
        passed=False,
        results=[
            ValidationResult(rule_id=1, rule_name="rule-a", passed=True,
                             level="Required", expected_value="tutorial", mitigation=""),
            ValidationResult(rule_id=2, rule_name="rule-b", passed=True,
                             level="Suggested", expected_value="azure", mitigation=""),
            ValidationResult(rule_id=3, rule_name="rule-c", passed=False,
                             level="Required", expected_value="yes", mitigation="Fix this."),
        ],
    )


class TestWriteJsonReport:
    def test_creates_file(self, tmp_path: Path, sample_report: ScanReport) -> None:
        dest = tmp_path / "report.json"
        result = write_json_report(sample_report, dest)
        assert dest.exists()
        assert result == dest.resolve()

    def test_valid_json(self, tmp_path: Path, sample_report: ScanReport) -> None:
        dest = tmp_path / "report.json"
        write_json_report(sample_report, dest)
        data = json.loads(dest.read_text())
        assert data["score"] == 2
        assert data["total_rules"] == 3
        assert len(data["results"]) == 3

    def test_creates_parent_directories(self, tmp_path: Path, sample_report: ScanReport) -> None:
        dest = tmp_path / "nested" / "deep" / "report.json"
        write_json_report(sample_report, dest)
        assert dest.exists()

    def test_passed_flag_in_output(self, tmp_path: Path, sample_report: ScanReport) -> None:
        dest = tmp_path / "r.json"
        write_json_report(sample_report, dest)
        data = json.loads(dest.read_text())
        assert data["passed"] is False


class TestWriteCsvReport:
    def test_creates_file(self, tmp_path: Path, sample_report: ScanReport) -> None:
        dest = tmp_path / "report.csv"
        result = write_csv_report(sample_report, dest)
        assert dest.exists()
        assert result == dest.resolve()

    def test_row_count(self, tmp_path: Path, sample_report: ScanReport) -> None:
        dest = tmp_path / "report.csv"
        write_csv_report(sample_report, dest)
        with dest.open(newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 3  # one row per ValidationResult

    def test_columns_present(self, tmp_path: Path, sample_report: ScanReport) -> None:
        dest = tmp_path / "report.csv"
        write_csv_report(sample_report, dest)
        with dest.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
        assert fieldnames is not None
        assert "rule_id" in fieldnames
        assert "passed" in fieldnames
        assert "mitigation" in fieldnames

    def test_creates_parent_directories(self, tmp_path: Path, sample_report: ScanReport) -> None:
        dest = tmp_path / "out" / "report.csv"
        write_csv_report(sample_report, dest)
        assert dest.exists()
