"""Rule-set loader — Repository pattern.

Loads a :class:`~markdown_validator.domain.models.RuleSetModel` from a JSON
file. This is the only place in the codebase that reads rule-set files from
disk.

Design pattern: **Repository** — the :class:`RuleSetRepository` class
separates the service layer from the filesystem. Tests can substitute
an in-memory rule set without touching the loader.

:raises FileNotFoundError: If the JSON file does not exist.
:raises ValueError: If the JSON does not conform to the rule-set schema.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from pydantic import ValidationError

from markdown_validator.domain.models import RuleSetModel

logger = logging.getLogger(__name__)


class RuleSetRepository:
    """Loads and validates rule-set JSON files.

    Usage::

        repo = RuleSetRepository()
        rule_set = repo.load("path/to/rules.json")

    Design pattern: **Repository** — decouples the scanner service from
    direct file I/O, making the scanner independently testable.
    """

    def load(self, filepath: str | Path) -> RuleSetModel:
        """Load and validate a rule-set from a JSON file.

        :param filepath: Path to the ``.json`` rule-set file.
        :return: A validated, immutable :class:`~markdown_validator.domain.models.RuleSetModel`.
        :raises FileNotFoundError: If *filepath* does not exist.
        :raises ValueError: If the JSON is invalid or fails schema validation.
        """
        path = Path(filepath)
        logger.info("RuleSetRepository.load: reading %s", path)

        if not path.exists():
            raise FileNotFoundError(f"Rule-set file not found: {path}")

        raw = path.read_text(encoding="utf-8")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Rule-set file {path} is not valid JSON: {exc}") from exc

        try:
            rule_set = RuleSetModel.model_validate(data)
        except ValidationError as exc:
            raise ValueError(
                f"Rule-set file {path} failed schema validation:\n{exc}"
            ) from exc

        n_rules = len(rule_set.rules.header) + len(rule_set.rules.body)
        n_workflows = len(rule_set.workflows)
        logger.info(
            "RuleSetRepository.load: loaded %d rules (%d header, %d body), %d workflows",
            n_rules,
            len(rule_set.rules.header),
            len(rule_set.rules.body),
            n_workflows,
        )
        return rule_set

    def load_from_dict(self, data: dict) -> RuleSetModel:  # type: ignore[type-arg]
        """Load and validate a rule-set from an already-parsed dictionary.

        Useful in tests to construct rule sets without filesystem access.

        :param data: Dictionary conforming to the rule-set schema.
        :return: A validated, immutable :class:`~markdown_validator.domain.models.RuleSetModel`.
        :raises ValueError: If *data* fails schema validation.
        """
        try:
            return RuleSetModel.model_validate(data)
        except ValidationError as exc:
            raise ValueError(f"Rule-set dict failed schema validation:\n{exc}") from exc
