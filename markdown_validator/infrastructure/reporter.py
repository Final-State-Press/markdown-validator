"""Scan result reporter.

Writes :class:`~markdown_validator.domain.models.ScanReport` objects to disk
in JSON or CSV format. This is the only place in the codebase that writes
output files.

:raises OSError: If the destination directory cannot be created or the file
    cannot be written.
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path

from markdown_validator.domain.models import ScanReport

logger = logging.getLogger(__name__)


def write_json_report(report: ScanReport, output_path: str | Path) -> Path:
    """Serialise a :class:`ScanReport` to a JSON file.

    The parent directory is created if it does not already exist.

    :param report: Validated scan report to serialise.
    :param output_path: Destination ``.json`` file path.
    :return: Resolved path of the written file.
    :raises OSError: On filesystem errors.
    """
    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    payload = report.model_dump()
    dest.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    logger.info("write_json_report: wrote %s", dest)
    return dest.resolve()


def write_csv_report(report: ScanReport, output_path: str | Path) -> Path:
    """Write a :class:`ScanReport` as a flat CSV file.

    Each row represents one :class:`~markdown_validator.domain.models.ValidationResult`.
    The parent directory is created if it does not already exist.

    :param report: Validated scan report to serialise.
    :param output_path: Destination ``.csv`` file path.
    :return: Resolved path of the written file.
    :raises OSError: On filesystem errors.
    """
    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "filepath",
        "rule_id",
        "rule_name",
        "passed",
        "level",
        "expected_value",
        "actual_value",
        "mitigation",
    ]

    with dest.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for result in report.results:
            writer.writerow(
                {
                    "filepath": report.filepath,
                    "rule_id": result.rule_id,
                    "rule_name": result.rule_name,
                    "passed": result.passed,
                    "level": result.level,
                    "expected_value": result.expected_value,
                    "actual_value": result.actual_value,
                    "mitigation": result.mitigation,
                }
            )

    logger.info("write_csv_report: wrote %d rows to %s", len(report.results), dest)
    return dest.resolve()
