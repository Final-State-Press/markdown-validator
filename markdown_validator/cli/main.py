"""Command-line interface for markdown-validator.

Entry point: ``md-validate`` (defined in ``pyproject.toml``).

Usage examples::

    # Validate a single file
    md-validate validate article.md --rules rules/tutorial.json

    # Validate all .md files in a directory
    md-validate validate docs/ --rules rules/tutorial.json --output results/

    # Output JSON report
    md-validate validate article.md --rules rules/tutorial.json --format json

    # Verbose logging
    md-validate --verbose validate article.md --rules rules/tutorial.json
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import click

from markdown_validator.domain.models import ScanReport
from markdown_validator.infrastructure.reporter import write_csv_report, write_json_report
from markdown_validator.services.scanner import Scanner
from markdown_validator.services.workflow import run_all_workflows

_DEFAULT_LOG_FORMAT = "%(levelname)s [%(name)s] %(message)s"


def _configure_logging(verbose: bool, quiet: bool) -> None:
    """Configure root logger based on CLI verbosity flags.

    :param verbose: Enable DEBUG-level output.
    :param quiet: Suppress all output below ERROR level.
    """
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logging.basicConfig(format=_DEFAULT_LOG_FORMAT, level=level)


@click.group()
@click.option("--verbose", "-v", is_flag=True, default=False, help="Enable debug logging.")
@click.option("--quiet", "-q", is_flag=True, default=False, help="Suppress all non-error output.")
@click.pass_context
def cli(ctx: click.Context, verbose: bool, quiet: bool) -> None:
    """Markdown Validator — rule-based document validation.

    :param ctx: Click context object.
    :param verbose: Enable DEBUG-level output when True.
    :param quiet: Suppress INFO/DEBUG output when True.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["quiet"] = quiet
    _configure_logging(verbose, quiet)


@cli.command()
@click.argument("target", type=click.Path(exists=True))
@click.option(
    "--rules",
    "-r",
    required=True,
    type=click.Path(exists=True),
    help="Path to the rule-set JSON file.",
)
@click.option(
    "--output",
    "-o",
    default=None,
    type=click.Path(),
    help="Output directory for reports (optional).",
)
@click.option(
    "--format",
    "-f",
    "output_format",
    default="text",
    type=click.Choice(["text", "json", "csv"], case_sensitive=False),
    help="Output format (default: text).",
)
@click.option(
    "--workflows/--no-workflows",
    default=True,
    help="Run workflow chains defined in the rule set (default: enabled).",
)
@click.pass_context
def validate(
    ctx: click.Context,
    target: str,
    rules: str,
    output: str | None,
    output_format: str,
    workflows: bool,
) -> None:
    """Validate TARGET (file or directory) against RULES.

    TARGET may be a single ``.md`` file or a directory; when a directory is
    given, all ``.md`` files within it are validated recursively.

    :param ctx: Click context object.
    :param target: Path to the markdown file or directory.
    :param rules: Path to the rule-set JSON file.
    :param output: Optional output directory for persisting reports.
    :param output_format: Format for report output (``text``, ``json``, ``csv``).
    :param workflows: Whether to execute workflow chains after rule evaluation.
    """
    scanner = Scanner()
    target_path = Path(target)

    try:
        if target_path.is_dir():
            reports = scanner.validate_directory(target_path, rules)
        else:
            reports = [scanner.validate(target_path, rules)]
    except (FileNotFoundError, ValueError) as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)

    overall_passed = all(r.passed for r in reports)

    for report in reports:
        _render_report(report, output_format, output, rules, workflows)

    if not overall_passed:
        sys.exit(1)


def _render_report(
    report: ScanReport,
    output_format: str,
    output_dir: str | None,
    rules_file: str,
    run_workflows: bool,
) -> None:
    """Render and optionally persist a single :class:`ScanReport`.

    :param report: The scan report to render.
    :param output_format: One of ``"text"``, ``"json"``, ``"csv"``.
    :param output_dir: Optional directory to write the report file.
    :param rules_file: Path to the rule-set file (for workflow execution).
    :param run_workflows: Whether to also run and display workflow results.
    """
    if output_format == "json":
        payload = report.model_dump()
        output_str = json.dumps(payload, indent=2)
        click.echo(output_str)
        if output_dir:
            stem = Path(report.filepath).stem
            dest = Path(output_dir) / f"{stem}_report.json"
            write_json_report(report, dest)
            click.echo(f"Report written to {dest}", err=True)

    elif output_format == "csv":
        if output_dir:
            stem = Path(report.filepath).stem
            dest = Path(output_dir) / f"{stem}_report.csv"
            write_csv_report(report, dest)
            click.echo(f"Report written to {dest}", err=True)
        else:
            import csv
            import io
            buf = io.StringIO()
            writer = csv.writer(buf)
            writer.writerow(["rule_id", "rule_name", "passed", "level", "expected_value", "mitigation"])
            for r in report.results:
                writer.writerow([r.rule_id, r.rule_name, r.passed, r.level, r.expected_value, r.mitigation])
            click.echo(buf.getvalue())

    else:
        # Text format
        status = click.style("PASS", fg="green") if report.passed else click.style("FAIL", fg="red")
        click.echo(f"\n{status}  {report.filepath}")
        click.echo(f"     Score: {report.score}/{report.total_rules} rules passed")
        for result in report.results:
            icon = "✓" if result.passed else "✗"
            colour = "green" if result.passed else "red"
            line = f"  {click.style(icon, fg=colour)} [{result.rule_id:>3}] {result.rule_name}"
            if not result.passed and result.mitigation:
                line += f"\n         → {result.mitigation}"
            click.echo(line)

        if run_workflows:
            _render_workflows(report, rules_file)


def _render_workflows(report: ScanReport, rules_file: str) -> None:
    """Load the rule set and run workflows, printing results.

    :param report: Scan report containing rule results.
    :param rules_file: Path to the rule-set JSON for loading workflows.
    """
    from markdown_validator.infrastructure.loader import RuleSetRepository

    try:
        rule_set = RuleSetRepository().load(rules_file)
        if not rule_set.workflows:
            return
        wf_results = run_all_workflows(rule_set, report)
        click.echo("\n  Workflows:")
        for wf in wf_results:
            icon = "✓" if wf.passed else "✗"
            colour = "green" if wf.passed else "red"
            click.echo(f"    {click.style(icon, fg=colour)} {wf.workflow_name}")
            if not wf.passed and wf.fix:
                click.echo(f"       → {wf.fix}")
    except (FileNotFoundError, ValueError) as exc:
        click.echo(f"  Warning: could not run workflows — {exc}", err=True)


if __name__ == "__main__":
    cli()
