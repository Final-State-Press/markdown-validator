"""Unit tests for markdown_validator.services.workflow."""

from __future__ import annotations

import pytest

from markdown_validator.domain.models import (
    RuleSetModel,
    RulesSection,
    ScanReport,
    ValidationResult,
    WorkflowModel,
    WorkflowResult,
)
from markdown_validator.services.workflow import (
    WorkflowEngine,
    _parse_steps,
    _to_token,
    run_all_workflows,
)


# ---------------------------------------------------------------------------
# _parse_steps
# ---------------------------------------------------------------------------

class TestParseSteps:
    def test_simple_steps(self) -> None:
        steps = _parse_steps("S-1,1-E")
        assert steps == [("s", 1), (1, "e")]

    def test_complex_steps(self) -> None:
        steps = _parse_steps("S-1,1-D,T-2,F-3,M-E")
        assert steps[0] == ("s", 1)
        assert steps[1] == (1, "d")
        assert steps[2] == ("t", 2)
        assert steps[3] == ("f", 3)
        assert steps[4] == ("m", "e")

    def test_symbols_lowercased(self) -> None:
        steps = _parse_steps("S-1,1-E")
        assert steps[0][0] == "s"
        assert steps[1][1] == "e"

    def test_invalid_token_raises(self) -> None:
        with pytest.raises(ValueError):
            _parse_steps("S1invalid")  # no dash separator at all


class TestToToken:
    def test_numeric_string(self) -> None:
        assert _to_token("5") == 5

    def test_symbol_lowercased(self) -> None:
        assert _to_token("S") == "s"

    def test_already_lowercase(self) -> None:
        assert _to_token("d") == "d"


# ---------------------------------------------------------------------------
# WorkflowEngine — individual step patterns
# ---------------------------------------------------------------------------

class TestWorkflowEnginePatterns:
    """Test each of the 12 step patterns independently."""

    def _make_engine(self, results: dict[int, bool]) -> WorkflowEngine:
        return WorkflowEngine(results)

    # Pattern 1: S-N
    def test_pattern1_start_loads_rule(self) -> None:
        wf = WorkflowModel(name="p1", steps="S-1,1-E")
        result = self._make_engine({1: True}).run(wf)
        assert result.passed is True

    def test_pattern1_failing_rule(self) -> None:
        wf = WorkflowModel(name="p1f", steps="S-1,1-E")
        result = self._make_engine({1: False}).run(wf)
        assert result.passed is False

    # Pattern 11: N-E
    def test_pattern11_rule_to_end(self) -> None:
        wf = WorkflowModel(name="p11", steps="S-1,1-E")
        result = self._make_engine({1: True}).run(wf)
        assert result.passed is True

    # Pattern 12: N-N (both must pass)
    def test_pattern12_both_pass(self) -> None:
        wf = WorkflowModel(name="p12", steps="S-1,1-2,2-E")
        result = self._make_engine({1: True, 2: True}).run(wf)
        assert result.passed is True

    def test_pattern12_one_fails(self) -> None:
        wf = WorkflowModel(name="p12f", steps="S-1,1-2,2-E")
        result = self._make_engine({1: True, 2: False}).run(wf)
        assert result.passed is False

    # Pattern 2+4+3: N-D, T-N, M-D (decision branch true)
    def test_pattern_decision_true_branch(self) -> None:
        # S-1 → rule 1 is True; 1-D sets decision=True; T-2 follows; 2-E ends
        wf = WorkflowModel(name="dec-t", steps="S-1,1-D,T-2,2-E")
        result = self._make_engine({1: True, 2: True}).run(wf)
        assert result.passed is True

    # Pattern 5: F-N (false branch)
    def test_pattern_decision_false_branch(self) -> None:
        # 1-D sets decision=False; F-2 applies rule 2; 2-E ends
        wf = WorkflowModel(name="dec-f", steps="S-1,1-D,F-2,2-E")
        result = self._make_engine({1: False, 2: True}).run(wf)
        assert result.passed is True

    # Pattern 6: T-R (reverse on true)
    def test_pattern6_true_reverse(self) -> None:
        # Rule 1 is True → decision=True → T-R reverses → decision=False → M-E
        wf = WorkflowModel(name="tr", steps="S-1,1-D,T-R,M-E")
        result = self._make_engine({1: True}).run(wf)
        assert result.passed is False

    # Pattern 7: F-R (reverse on false)
    def test_pattern7_false_reverse(self) -> None:
        # Rule 1 is False → decision=False → F-R reverses → decision=True → M-E
        wf = WorkflowModel(name="fr", steps="S-1,1-D,F-R,M-E")
        result = self._make_engine({1: False}).run(wf)
        assert result.passed is True

    # Missing rule returns False
    def test_missing_rule_id_returns_false(self) -> None:
        wf = WorkflowModel(name="missing", steps="S-99,99-E")
        result = self._make_engine({}).run(wf)
        assert result.passed is False


# ---------------------------------------------------------------------------
# WorkflowResult
# ---------------------------------------------------------------------------

class TestWorkflowResult:
    def test_fix_included_on_failure(self) -> None:
        wf = WorkflowModel(name="wf", steps="S-1,1-E", fix="Please fix this.")
        result = WorkflowEngine({1: False}).run(wf)
        assert result.passed is False
        assert result.fix == "Please fix this."

    def test_fix_empty_on_pass(self) -> None:
        wf = WorkflowModel(name="wf", steps="S-1,1-E", fix="Please fix this.")
        result = WorkflowEngine({1: True}).run(wf)
        assert result.passed is True
        assert result.fix == ""


# ---------------------------------------------------------------------------
# run_all_workflows
# ---------------------------------------------------------------------------

class TestRunAllWorkflows:
    def _make_report(self, results: dict[int, bool]) -> ScanReport:
        vr = [
            ValidationResult(rule_id=k, rule_name=f"r{k}", passed=v)
            for k, v in results.items()
        ]
        passed = all(v for v in results.values())
        return ScanReport(
            filepath="/tmp/test.md",
            score=sum(results.values()),
            total_rules=len(results),
            passed=passed,
            results=vr,
        )

    def test_returns_list_of_results(self) -> None:
        rule_set = RuleSetModel(
            rules=RulesSection(),
            workflows=[
                WorkflowModel(name="wf1", steps="S-1,1-E"),
                WorkflowModel(name="wf2", steps="S-2,2-E"),
            ],
        )
        report = self._make_report({1: True, 2: False})
        results = run_all_workflows(rule_set, report)
        assert len(results) == 2
        assert results[0].passed is True
        assert results[1].passed is False

    def test_empty_workflows_returns_empty_list(self) -> None:
        rule_set = RuleSetModel(rules=RulesSection(), workflows=[])
        report = self._make_report({1: True})
        results = run_all_workflows(rule_set, report)
        assert results == []

    def test_checkworkflow_integration(
        self, checkworkflow_json_path, azure_md_path
    ) -> None:
        from markdown_validator.infrastructure.loader import RuleSetRepository
        from markdown_validator.services.scanner import Scanner
        rule_set = RuleSetRepository().load(checkworkflow_json_path)
        report = Scanner().validate_with_ruleset(azure_md_path, rule_set)
        wf_results = run_all_workflows(rule_set, report)
        assert len(wf_results) == 22
        assert all(isinstance(r, WorkflowResult) for r in wf_results)
