"""Workflow execution engine.

A *workflow* is an ordered sequence of steps that combines the results of
individual validation rules into a higher-level pass/fail decision.  Steps
are encoded in a mini-language::

    S-1,1-D,T-2,F-3,M-E

Each token is ``<source>-<target>`` where source/target are either a rule ID
(integer) or a control symbol (``S``, ``D``, ``T``, ``F``, ``M``, ``E``,
``R``).  Twelve step patterns are supported; see :meth:`WorkflowEngine.run`.

Design pattern: **Chain of Responsibility** — each step pattern is dispatched
to its own handler method, making the state machine readable and individually
testable.
"""

from __future__ import annotations

import dataclasses
import logging

from markdown_validator.domain.models import (
    RuleSetModel,
    ScanReport,
    WorkflowModel,
    WorkflowResult,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal state container
# ---------------------------------------------------------------------------


@dataclasses.dataclass
class _WorkflowState:
    """Mutable execution state for a single workflow run.

    :param workflow_state: Current overall pass/fail state.
    :param decision: State captured at a decision point (``N-D`` step).
    :param merge_active: Whether a merge operation is in progress.
    """

    workflow_state: bool | None = None
    decision: bool | None = None
    merge_active: bool = False


# ---------------------------------------------------------------------------
# Workflow engine
# ---------------------------------------------------------------------------


class WorkflowEngine:
    """Executes workflow step sequences against a set of rule results.

    :param rule_results: Mapping from rule ID to the boolean pass/fail result
        for that rule, as produced by the scanner.
    """

    def __init__(self, rule_results: dict[int, bool]) -> None:
        self._results = rule_results

    def run(self, workflow: WorkflowModel) -> WorkflowResult:
        """Execute a single workflow and return its result.

        :param workflow: The workflow definition (already normalised).
        :return: A :class:`~markdown_validator.domain.models.WorkflowResult`.
        """
        steps = _parse_steps(workflow.steps)
        state = _WorkflowState()

        for step_num, (source, target) in enumerate(steps, start=1):
            logger.debug(
                "WorkflowEngine.run: step %d — %r-%r | wf=%s dec=%s",
                step_num,
                source,
                target,
                state.workflow_state,
                state.decision,
            )
            self._dispatch(source, target, state, step_num, workflow.name)

        passed = bool(state.workflow_state)
        logger.debug(
            "WorkflowEngine.run: workflow %r finished — passed=%s",
            workflow.name,
            passed,
        )
        return WorkflowResult(
            workflow_name=workflow.name,
            passed=passed,
            fix=workflow.fix if not passed else "",
        )

    def _dispatch(
        self,
        source: str | int,
        target: str | int,
        state: _WorkflowState,
        step_num: int,
        workflow_name: str,
    ) -> None:
        """Dispatch a single step to the appropriate handler.

        Implements all 12 workflow step patterns.

        :param source: Left-hand token of the step.
        :param target: Right-hand token of the step.
        :param state: Mutable workflow execution state (modified in place).
        :param step_num: 1-based step counter (for logging).
        :param workflow_name: Name of the enclosing workflow (for logging).
        """
        s_is_num = isinstance(source, int)
        t_is_num = isinstance(target, int)

        # Pattern 1: S-N  →  start, load rule N
        if source == "s" and t_is_num:
            state.workflow_state = self._rule_passed(target)  # type: ignore[arg-type]

        # Pattern 2: N-D  →  rule N becomes the decision
        elif s_is_num and target == "d":
            state.decision = self._rule_passed(source)  # type: ignore[arg-type]
            state.merge_active = True

        # Pattern 3: M-D  →  merge state becomes decision
        elif source == "m" and target == "d":
            state.workflow_state = state.decision
            state.merge_active = True
            state.decision = None

        # Pattern 4: T-N  →  if decision was True, load rule N
        elif source == "t" and t_is_num and state.decision is True:
            state.workflow_state = self._rule_passed(target)  # type: ignore[arg-type]

        # Pattern 5: F-N  →  if decision was False, load rule N
        elif source == "f" and t_is_num and state.decision is False:
            state.workflow_state = self._rule_passed(target)  # type: ignore[arg-type]

        # Pattern 6: T-R  →  if decision True, reverse (negate) it
        elif source == "t" and target == "r" and state.decision is True:
            state.decision = False

        # Pattern 7: F-R  →  if decision False, reverse (negate) it
        elif source == "f" and target == "r" and state.decision is False:
            state.decision = True

        # Pattern 8: N-M  →  rule N merges into merge state
        elif s_is_num and target == "m" and state.merge_active:
            state.workflow_state = state.decision
            state.merge_active = False  # type: ignore[assignment]

        # Pattern 9: M-N  →  exit merge, load rule N
        elif source == "m" and t_is_num and not state.merge_active:
            state.workflow_state = state.decision
            state.merge_active = False
            state.decision = None

        # Pattern 10: M-E  →  merge ends workflow
        elif source == "m" and target == "e":
            state.workflow_state = state.decision

        # Pattern 11: N-E  →  rule N ends workflow
        elif s_is_num and target == "e":
            state.workflow_state = self._rule_passed(source)  # type: ignore[arg-type]

        # Pattern 12: N-N  →  both rules must pass
        elif s_is_num and t_is_num:
            if not self._rule_passed(source):  # type: ignore[arg-type]
                state.workflow_state = False
            if not self._rule_passed(target):  # type: ignore[arg-type]
                state.workflow_state = False

        else:
            logger.warning(
                "WorkflowEngine: unrecognised step %r-%r in workflow %r (step %d)",
                source,
                target,
                workflow_name,
                step_num,
            )

    def _rule_passed(self, rule_id: int) -> bool:
        """Look up the pass/fail state of *rule_id*.

        :param rule_id: ID of the rule to look up.
        :return: ``True`` if the rule passed, ``False`` if it failed or is
            not present in the results.
        """
        result = self._results.get(rule_id)
        if result is None:
            logger.warning("WorkflowEngine: rule id=%d not found in results", rule_id)
            return False
        return result


# ---------------------------------------------------------------------------
# Workflow runner — runs all workflows in a rule set
# ---------------------------------------------------------------------------


def run_all_workflows(
    rule_set: RuleSetModel,
    scan_report: ScanReport,
) -> list[WorkflowResult]:
    """Run every workflow defined in *rule_set* against *scan_report* results.

    :param rule_set: The rule set containing workflow definitions.
    :param scan_report: The scan report produced by the scanner for the same
        document and rule set.
    :return: List of :class:`~markdown_validator.domain.models.WorkflowResult`
        objects, one per workflow.
    """
    rule_results: dict[int, bool] = {r.rule_id: r.passed for r in scan_report.results}
    engine = WorkflowEngine(rule_results)

    results: list[WorkflowResult] = []
    for workflow in rule_set.workflows:
        wf_result = engine.run(workflow)
        results.append(wf_result)
        logger.info(
            "run_all_workflows: workflow=%r passed=%s",
            workflow.name,
            wf_result.passed,
        )
    return results


# ---------------------------------------------------------------------------
# Step string parser
# ---------------------------------------------------------------------------


def _parse_steps(steps_str: str) -> list[tuple[str | int, str | int]]:
    """Parse a step string into a list of (source, target) tuples.

    Accepts the normalised dash-separated format ``"S-1,1-D,T-2,M-E"``.
    Symbols are lowercased; numeric tokens are converted to ``int``.

    :param steps_str: Normalised workflow step string.
    :return: List of ``(source, target)`` pairs.
    :raises ValueError: If a step token cannot be parsed.
    """
    tuples: list[tuple[str | int, str | int]] = []
    for token in steps_str.split(","):
        token = token.strip()
        if not token:
            continue
        parts = token.split("-", maxsplit=1)
        if len(parts) != 2:
            raise ValueError(f"Invalid workflow step token: {token!r}")
        src, tgt = parts
        tuples.append((_to_token(src), _to_token(tgt)))
    return tuples


def _to_token(raw: str) -> str | int:
    """Convert a raw step part to either a lowercase symbol or an integer.

    :param raw: Raw token string from the step language.
    :return: Integer if numeric, otherwise lowercase string.
    """
    try:
        return int(raw)
    except ValueError:
        return raw.lower()
