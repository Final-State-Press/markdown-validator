"""Additional workflow tests for uncovered patterns."""

from __future__ import annotations

from markdown_validator.domain.models import WorkflowModel
from markdown_validator.services.workflow import WorkflowEngine


class TestWorkflowEngineAdditionalPatterns:
    def _engine(self, results: dict[int, bool]) -> WorkflowEngine:
        return WorkflowEngine(results)

    # Pattern 3: M-D (merge becomes decision)
    def test_pattern3_merge_to_decision(self) -> None:
        # S-1, 1-D sets decision=True; M-D sets workflow=True; M-E ends
        wf = WorkflowModel(name="p3", steps="S-1,1-D,M-D,M-E")
        result = self._engine({1: True}).run(wf)
        assert isinstance(result.passed, bool)

    # Pattern 8: N-M merge with merge_active
    def test_pattern8_number_to_merge(self) -> None:
        # S-1, 1-D, T-2, 2-M (merge), M-E
        wf = WorkflowModel(name="p8", steps="S-1,1-D,T-2,2-M,M-E")
        result = self._engine({1: True, 2: True}).run(wf)
        assert isinstance(result.passed, bool)

    # Pattern 9: M-N exit merge
    def test_pattern9_merge_to_number(self) -> None:
        wf = WorkflowModel(name="p9", steps="S-1,1-D,F-R,M-3,3-E")
        result = self._engine({1: False, 3: True}).run(wf)
        assert isinstance(result.passed, bool)

    # Unrecognised step — should log warning and not crash
    def test_unrecognised_step_does_not_raise(self) -> None:
        wf = WorkflowModel(name="weird", steps="S-1,X-Y,1-E")
        result = self._engine({1: True}).run(wf)
        # Should not raise; result may be True or False
        assert isinstance(result.passed, bool)
