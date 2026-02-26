"""Domain value objects and Pydantic contract models.

All objects in this module are immutable. They define the contracts between
layers and are safe to pass across layer boundaries without defensive copying.

Design pattern: **Value Object** — each model is frozen after construction;
mutation always creates a new instance.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, field_validator, model_validator

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Input contracts — validated at load time (fail fast)
# ---------------------------------------------------------------------------


class RuleModel(BaseModel):
    """A single validation rule loaded from a JSON rule-set file.

    :param id: Unique positive integer identifier for this rule.
    :param name: Human-readable rule description.
    :param type: Whether this rule targets ``"header"`` (YAML metadata) or
        ``"body"`` (HTML-rendered document body).
    :param query: For ``header`` rules, the metadata key to look up.
        For ``body`` rules, an XPath expression against the HTML body.
    :param flag: Processing mode — controls what ``query`` extracts.
        Values: ``"value"``, ``"check"``, ``"count"``, ``"text"``,
        ``"date"``, ``"dom"``, ``"all"``.
    :param operation: Comparison operator token. See
        :mod:`markdown_validator.domain.operators`.
    :param value: Expected value used in the comparison assertion.
    :param level: Severity — ``"Required"`` failures fail the entire scan;
        ``"Suggested"`` failures are informational only.
    :param mitigation: Human-readable remediation hint shown on failure.
    """

    id: int
    name: str
    type: Literal["header", "body"]
    query: str
    flag: str
    operation: str
    value: str
    level: Literal["Required", "Suggested"] = "Required"
    mitigation: str = ""

    model_config = {"frozen": True}

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id(cls, v: object) -> int:
        """Accept string IDs from older JSON files and coerce to ``int``."""
        try:
            return int(v)  # type: ignore[arg-type]
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Rule 'id' must be numeric, got {v!r}") from exc

    @field_validator("id")
    @classmethod
    def id_must_be_positive(cls, v: int) -> int:
        """Enforce that rule IDs are positive integers."""
        if v <= 0:
            raise ValueError(f"Rule id must be a positive integer, got {v}")
        return v

    @field_validator("type", mode="before")
    @classmethod
    def normalise_type(cls, v: object) -> str:
        """Normalise rule type to lowercase."""
        if isinstance(v, str):
            return v.lower()
        return v  # type: ignore[return-value]


class RulesSection(BaseModel):
    """The ``"rules"`` section of a rule-set JSON file.

    :param header: Rules that operate on YAML front-matter metadata.
    :param body: Rules that operate on the HTML-rendered document body.
    """

    header: list[RuleModel] = []
    body: list[RuleModel] = []

    model_config = {"frozen": True}

    @model_validator(mode="before")
    @classmethod
    def inject_type_from_section(cls, data: object) -> object:
        """Inject ``type`` from the section name when absent.

        Older rule JSON files (e.g. ``concept.json``) omit the ``type``
        field on each rule because the section name already encodes it.
        This validator adds ``"type": "header"`` or ``"type": "body"``
        to any rule dict that lacks the field.
        """
        if isinstance(data, dict):
            for rule in data.get("header", []):
                if isinstance(rule, dict) and "type" not in rule:
                    rule["type"] = "header"
            for rule in data.get("body", []):
                if isinstance(rule, dict) and "type" not in rule:
                    rule["type"] = "body"
        return data

    @model_validator(mode="after")
    def no_duplicate_ids(self) -> RulesSection:
        """Fail fast if any two rules share the same ID."""
        all_ids = [r.id for r in self.header] + [r.id for r in self.body]
        seen: set[int] = set()
        for rule_id in all_ids:
            if rule_id in seen:
                raise ValueError(f"Duplicate rule id {rule_id} in rule set")
            seen.add(rule_id)
        return self


class WorkflowModel(BaseModel):
    """A single workflow definition from a rule-set JSON file.

    :param name: Descriptive name for the workflow.
    :param steps: Step string in the workflow step language, e.g.
        ``"S-1,1-D,T-2,M-E"``. Both dash-separated (``S-1``) and
        parenthesis-separated (``(S,1)``) formats are accepted; the latter
        is normalised on load.
    :param level: Whether this workflow is ``"Required"`` or ``"Suggested"``.
    :param fix: Human-readable remediation text shown when the workflow fails.
    """

    name: str
    steps: str
    level: Literal["Required", "Suggested"] = "Required"
    fix: str = ""

    model_config = {"frozen": True}

    @field_validator("steps", mode="before")
    @classmethod
    def normalise_steps(cls, v: object) -> str:
        """Normalise ``(S,1)(1,E)`` format to ``S-1,1-E`` format."""
        if not isinstance(v, str):
            raise ValueError(f"steps must be a string, got {type(v)}")
        s = v.strip()
        if s.startswith("("):
            # Convert "(S,1)(1,D)(T,2)(M,E)" → "S-1,1-D,T-2,M-E"
            parts = s.replace(")(", ",").strip("()").split(",")
            pairs: list[str] = []
            for i in range(0, len(parts) - 1, 2):
                pairs.append(f"{parts[i]}-{parts[i + 1]}")
            return ",".join(pairs)
        return s


class RuleSetModel(BaseModel):
    """The top-level schema for a rule-set JSON file.

    :param rules: Header and body rule definitions.
    :param workflows: Optional list of multi-step workflow definitions.
    """

    rules: RulesSection
    workflows: list[WorkflowModel] = []

    model_config = {"frozen": True}

    @property
    def all_rules(self) -> list[RuleModel]:
        """Return all rules (header + body) in definition order."""
        return list(self.rules.header) + list(self.rules.body)

    @property
    def rules_by_id(self) -> dict[int, RuleModel]:
        """Return a mapping from rule ID to :class:`RuleModel`."""
        return {r.id: r for r in self.all_rules}


# ---------------------------------------------------------------------------
# Infrastructure value object — produced by the parser
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParsedDocument:
    """An immutable representation of a parsed Markdown file.

    :param filepath: Absolute path to the source ``.md`` file.
    :param metadata: Key-value pairs extracted from the YAML front matter.
    :param html: HTML string produced by rendering the document body.
    """

    filepath: Path
    metadata: dict[str, str]
    html: str


# ---------------------------------------------------------------------------
# Output contracts — produced by the scanner service
# ---------------------------------------------------------------------------


class ValidationResult(BaseModel):
    """The outcome of evaluating a single rule against a document.

    :param rule_id: ID of the rule that was evaluated.
    :param rule_name: Human-readable name of the rule.
    :param passed: ``True`` if the rule assertion succeeded.
    :param level: Severity of this rule (``"Required"`` or ``"Suggested"``).
    :param expected_value: The value the rule expected to find.
    :param actual_value: The value actually found (or ``""`` if unavailable).
    :param mitigation: Remediation hint shown when the rule fails.
    :param filepath: Path to the document that was validated.
    """

    rule_id: int
    rule_name: str
    passed: bool
    level: Literal["Required", "Suggested"] = "Required"
    expected_value: str = ""
    actual_value: str = ""
    mitigation: str = ""
    filepath: str = ""

    model_config = {"frozen": True}


class ScanReport(BaseModel):
    """Aggregated results of running all rules in a rule set against one file.

    :param filepath: Path to the validated document.
    :param score: Number of rules that passed.
    :param total_rules: Total number of rules evaluated.
    :param passed: ``True`` only when every ``Required`` rule passed.
    :param results: Per-rule validation outcomes.
    """

    filepath: str
    score: int
    total_rules: int
    passed: bool
    results: list[ValidationResult]

    model_config = {"frozen": True}


class WorkflowResult(BaseModel):
    """Outcome of running a single workflow step sequence.

    :param workflow_name: Name of the workflow.
    :param passed: Final boolean state after all steps.
    :param fix: Remediation text if the workflow failed.
    """

    workflow_name: str
    passed: bool
    fix: str = ""

    model_config = {"frozen": True}
