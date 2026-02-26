"""Scanner service — top-level validation orchestrator.

:class:`Scanner` is the **Facade** for the entire validation pipeline.
Callers (CLI, tests, external code) only need to interact with this class;
they do not need to know about parsers, loaders, or evaluators.

Design pattern: **Facade** — :class:`Scanner` presents a single, simple
interface over the multi-step parse → load → evaluate pipeline.

Usage::

    from markdown_validator.services.scanner import Scanner

    scanner = Scanner()
    report = scanner.validate(
        markdown_file="docs/article.md",
        rules_file="rules/tutorial.json",
    )
    print(report.passed, report.score, report.total_rules)
"""

from __future__ import annotations

import logging
from pathlib import Path

from markdown_validator.domain.evaluator import evaluate_rule
from markdown_validator.domain.models import RuleSetModel, ScanReport, ValidationResult
from markdown_validator.infrastructure.loader import RuleSetRepository
from markdown_validator.infrastructure.parser import parse_document

logger = logging.getLogger(__name__)


class Scanner:
    """Orchestrates the end-to-end markdown validation pipeline.

    :param repository: Optional custom :class:`~markdown_validator.infrastructure.loader.RuleSetRepository`.
        If omitted, a default instance is created.  Inject a custom
        repository in tests to avoid filesystem access.
    """

    def __init__(self, repository: RuleSetRepository | None = None) -> None:
        self._repo = repository or RuleSetRepository()

    def validate(
        self,
        markdown_file: str | Path,
        rules_file: str | Path,
    ) -> ScanReport:
        """Validate a single Markdown file against a rule-set.

        :param markdown_file: Path to the ``.md`` file to validate.
        :param rules_file: Path to the rule-set JSON file.
        :return: A frozen :class:`~markdown_validator.domain.models.ScanReport`
            with per-rule results and an aggregate ``passed`` flag.
        :raises FileNotFoundError: If either file does not exist.
        :raises ValueError: If the rule-set JSON is invalid.
        """
        md_path = Path(markdown_file)
        logger.info("Scanner.validate: file=%s rules=%s", md_path, rules_file)

        rule_set = self._repo.load(rules_file)
        return self.validate_with_ruleset(md_path, rule_set)

    def validate_with_ruleset(
        self,
        markdown_file: str | Path,
        rule_set: RuleSetModel,
    ) -> ScanReport:
        """Validate a Markdown file against an already-loaded rule set.

        This method is useful when the rule set has already been loaded (e.g.,
        to validate multiple files against the same rules without re-reading
        the JSON on each call).

        :param markdown_file: Path to the ``.md`` file to validate.
        :param rule_set: Pre-loaded, validated rule set.
        :return: A frozen :class:`~markdown_validator.domain.models.ScanReport`.
        :raises FileNotFoundError: If *markdown_file* does not exist.
        """
        md_path = Path(markdown_file)
        doc = parse_document(md_path)

        results: list[ValidationResult] = []
        for rule in rule_set.all_rules:
            result = evaluate_rule(rule, doc)
            results.append(result)
            logger.debug(
                "Scanner: rule id=%d %r → %s",
                rule.id,
                rule.name,
                "PASS" if result.passed else "FAIL",
            )

        score = sum(1 for r in results if r.passed)
        # A scan passes only when all Required rules pass
        passed = all(
            r.passed for r in results if r.level == "Required"
        )

        report = ScanReport(
            filepath=str(md_path.resolve()),
            score=score,
            total_rules=len(results),
            passed=passed,
            results=results,
        )
        logger.info(
            "Scanner.validate: score=%d/%d passed=%s file=%s",
            score,
            len(results),
            passed,
            md_path,
        )
        return report

    def validate_directory(
        self,
        directory: str | Path,
        rules_file: str | Path,
    ) -> list[ScanReport]:
        """Validate all ``.md`` files under *directory*.

        The rule set is loaded once and reused for every file.

        :param directory: Root directory to scan recursively.
        :param rules_file: Path to the rule-set JSON file.
        :return: List of :class:`~markdown_validator.domain.models.ScanReport`
            objects, one per file.
        :raises FileNotFoundError: If the rule-set file does not exist.
        :raises NotADirectoryError: If *directory* is not a directory.
        """
        from markdown_validator.infrastructure.parser import find_markdown_files

        rule_set = self._repo.load(rules_file)
        files = find_markdown_files(directory)
        logger.info(
            "Scanner.validate_directory: %d files in %s", len(files), directory
        )

        reports: list[ScanReport] = []
        for md_path in files:
            try:
                report = self.validate_with_ruleset(md_path, rule_set)
                reports.append(report)
            except (FileNotFoundError, ValueError) as exc:
                logger.error("Scanner.validate_directory: skipping %s — %s", md_path, exc)

        return reports
