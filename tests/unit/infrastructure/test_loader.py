"""Unit tests for markdown_validator.infrastructure.loader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from markdown_validator.domain.models import RuleSetModel
from markdown_validator.infrastructure.loader import RuleSetRepository


MINIMAL_RULESET = {
    "rules": {
        "header": [
            {"id": "1", "name": "topic-check", "type": "header",
             "query": "ms.topic", "flag": "value", "operation": "==", "value": "tutorial"}
        ],
        "body": []
    },
    "workflows": []
}


class TestRuleSetRepository:
    def test_load_valid_file(self, checkworkflow_json_path: Path) -> None:
        repo = RuleSetRepository()
        rule_set = repo.load(checkworkflow_json_path)
        assert isinstance(rule_set, RuleSetModel)
        assert len(rule_set.all_rules) > 0

    def test_load_concept_file(self, concept_json_path: Path) -> None:
        repo = RuleSetRepository()
        rule_set = repo.load(concept_json_path)
        assert isinstance(rule_set, RuleSetModel)

    def test_file_not_found_raises(self) -> None:
        repo = RuleSetRepository()
        with pytest.raises(FileNotFoundError):
            repo.load("/no/such/rules.json")

    def test_invalid_json_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad.json"
        bad.write_text("{invalid json}", encoding="utf-8")
        repo = RuleSetRepository()
        with pytest.raises(ValueError, match="valid JSON"):
            repo.load(bad)

    def test_schema_violation_raises(self, tmp_path: Path) -> None:
        bad = tmp_path / "bad_schema.json"
        bad.write_text(json.dumps({"rules": {"header": [{"id": "abc"}]}}), encoding="utf-8")
        repo = RuleSetRepository()
        with pytest.raises(ValueError, match="schema validation"):
            repo.load(bad)

    def test_load_from_dict(self) -> None:
        repo = RuleSetRepository()
        rule_set = repo.load_from_dict(MINIMAL_RULESET)
        assert len(rule_set.rules.header) == 1
        assert rule_set.rules.header[0].id == 1

    def test_load_from_dict_invalid_raises(self) -> None:
        repo = RuleSetRepository()
        with pytest.raises(ValueError, match="schema validation"):
            repo.load_from_dict({"rules": {"header": [{"id": "x"}]}})

    def test_workflow_steps_normalised(self, tmp_path: Path) -> None:
        """Parenthesis-format steps are normalised at load time."""
        data = {
            "rules": {"header": [], "body": []},
            "workflows": [
                {"name": "wf1", "steps": "(S,1)(1,E)"}
            ]
        }
        f = tmp_path / "rules.json"
        f.write_text(json.dumps(data), encoding="utf-8")
        rule_set = RuleSetRepository().load(f)
        assert rule_set.workflows[0].steps == "S-1,1-E"

    def test_checkworkflow_rule_count(self, checkworkflow_json_path: Path) -> None:
        repo = RuleSetRepository()
        rule_set = repo.load(checkworkflow_json_path)
        # 5 header + 21 body rules in checkworkflow.json
        assert len(rule_set.rules.header) == 5
        assert len(rule_set.rules.body) == 21
        assert len(rule_set.workflows) == 22
