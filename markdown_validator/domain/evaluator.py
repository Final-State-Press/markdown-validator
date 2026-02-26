"""Rule evaluation engine.

:func:`evaluate_rule` is the single entry point for applying a
:class:`~markdown_validator.domain.models.RuleModel` to a
:class:`~markdown_validator.domain.models.ParsedDocument`.

It dispatches to:

* :mod:`markdown_validator.domain.operators` for string/numeric/regex
  comparisons.
* :mod:`markdown_validator.domain.pos` for part-of-speech and sentence-count
  checks.

The function is **pure** with respect to I/O — it never reads files or logs
at the INFO level; it emits DEBUG messages only.

:raises ValueError: If the rule's flag or operation is unrecognised.
"""

from __future__ import annotations

import logging

import html2text
from lxml import etree

from markdown_validator.domain import pos as pos_module
from markdown_validator.domain.models import ParsedDocument, RuleModel, ValidationResult
from markdown_validator.domain.operators import (
    OPERATOR_REGISTRY,
    op_date,
    op_regex,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def evaluate_rule(rule: RuleModel, doc: ParsedDocument) -> ValidationResult:
    """Apply *rule* to *doc* and return a :class:`ValidationResult`.

    :param rule: The rule to evaluate.
    :param doc: The parsed document to evaluate the rule against.
    :return: A frozen :class:`ValidationResult` with ``passed`` set
        accordingly.
    """
    logger.debug(
        "evaluate_rule: id=%d name=%r type=%s flag=%s op=%s",
        rule.id,
        rule.name,
        rule.type,
        rule.flag,
        rule.operation,
    )

    try:
        if rule.type == "header":
            passed = _evaluate_header_rule(rule, doc)
        else:
            passed = _evaluate_body_rule(rule, doc)
    except Exception:
        logger.exception(
            "evaluate_rule: unexpected error for rule id=%d, returning False",
            rule.id,
        )
        passed = False

    return ValidationResult(
        rule_id=rule.id,
        rule_name=rule.name,
        passed=passed,
        level=rule.level,
        expected_value=rule.value,
        mitigation=rule.mitigation,
        filepath=str(doc.filepath),
    )


# ---------------------------------------------------------------------------
# Header (metadata) evaluation
# ---------------------------------------------------------------------------


def _evaluate_header_rule(rule: RuleModel, doc: ParsedDocument) -> bool:
    """Evaluate a ``type="header"`` rule against document metadata.

    :param rule: Header rule to evaluate.
    :param doc: Parsed document whose ``metadata`` dict is inspected.
    :return: Boolean result.
    """
    flag = rule.flag.lower()
    keyword = rule.query

    if flag in ("", "value"):
        raw = doc.metadata.get(keyword)
        if raw is None:
            logger.debug("_evaluate_header_rule: key %r not found in metadata", keyword)
            return False
        return _apply_string_operator(rule.operation, str(raw), rule.value)

    if flag == "check":
        present = keyword in doc.metadata
        logger.debug("_evaluate_header_rule: check key=%r present=%s", keyword, present)
        return present

    if flag == "date":
        raw = doc.metadata.get(keyword)
        if raw is None:
            return False
        return op_date(str(raw), rule.operation, rule.value)

    if flag == "pattern":
        raw = doc.metadata.get(keyword)
        if raw is None:
            return False
        return op_regex(str(raw), rule.value)

    logger.warning("_evaluate_header_rule: unknown flag %r for rule id=%d", flag, rule.id)
    return False


# ---------------------------------------------------------------------------
# Body (XPath / HTML) evaluation
# ---------------------------------------------------------------------------


def _evaluate_body_rule(rule: RuleModel, doc: ParsedDocument) -> bool:
    """Evaluate a ``type="body"`` rule against the HTML document body.

    Comma-separated *values* cause each value to be checked independently;
    all must pass (logical AND).

    :param rule: Body rule to evaluate.
    :param doc: Parsed document whose ``html`` string is queried.
    :return: Boolean result.
    """
    # Support comma-separated expected values (all must match)
    values = [v.strip() for v in rule.value.split(",")]
    return all(
        _evaluate_body_single(rule, doc.html, expected)
        for expected in values
    )


def _evaluate_body_single(rule: RuleModel, html: str, expected_value: str) -> bool:
    """Evaluate the body rule for a single expected value.

    :param rule: Body rule to evaluate.
    :param html: HTML string to query.
    :param expected_value: Single expected value (already split from CSV list).
    :return: Boolean result.
    """
    flag = rule.flag.lower()

    # "all" flag: return the full plain-text content of the page
    if flag == "all":
        full_text = html2text.html2text(html)
        return _apply_string_operator(rule.operation, full_text, expected_value)

    results = _xpath_query(html, rule.query, flag)
    if results is None:
        logger.debug(
            "_evaluate_body_single: xpath returned None for rule id=%d query=%r",
            rule.id,
            rule.query,
        )
        return False

    # "count" flag: compare count as integer
    if flag == "count":
        count_str = str(results[0]) if results else "0"
        return _apply_string_operator(rule.operation, count_str, expected_value)

    # For text/dom flags, evaluate each node result; all must satisfy the assertion
    truth: list[bool] = []
    for item in results:
        item_str = str(item) if item is not None else ""
        # Part-of-speech operator: "p<N>"
        if rule.operation.startswith("p") and len(rule.operation) > 1:
            try:
                idx = int(rule.operation[1:])
                tag = pos_module.word_pos_at(item_str, idx)
                truth.append(tag == expected_value)
            except ValueError:
                truth.append(False)
        # Sentence count operator
        elif rule.operation == "s":
            count = pos_module.sentence_count(item_str)
            try:
                truth.append(count <= int(expected_value))
            except ValueError:
                truth.append(False)
        else:
            truth.append(_apply_string_operator(rule.operation, item_str, expected_value))

    if not truth:
        return False
    return all(truth)


# ---------------------------------------------------------------------------
# XPath helpers
# ---------------------------------------------------------------------------


def _xpath_query(html: str, query: str, flag: str) -> list[str] | list[int] | None:
    """Run an XPath query against an HTML string.

    :param html: HTML string to query (produced by markdown-to-HTML conversion).
    :param query: XPath expression.
    :param flag: One of ``"text"``, ``"count"``, ``"dom"``, or ``""`` (text default).
    :return: List of extracted values, or ``None`` on error.
    """
    try:
        parser = etree.HTMLParser()
        tree = etree.fromstring(html.encode("utf-8"), parser)
        raw = tree.xpath(query)

        if flag == "count":
            return [len(raw)]

        if flag == "dom":
            return [node.tag for node in raw if hasattr(node, "tag")]

        # Default: "text" — extract .text from each element
        values: list[str] = []
        for node in raw:
            text = node.text if hasattr(node, "text") else str(node)
            values.append(text or "")
        return values if values else None

    except etree.XPathError as exc:
        logger.warning("_xpath_query: XPath error for query %r — %s", query, exc)
        return None
    except Exception:
        logger.exception("_xpath_query: unexpected error for query %r", query)
        return None


# ---------------------------------------------------------------------------
# Operator dispatcher
# ---------------------------------------------------------------------------


def _apply_string_operator(operation: str, result: str, value: str) -> bool:
    """Look up the operator function from the registry and apply it.

    :param operation: Operator token (e.g. ``"=="``, ``"r"``, ``"l"``).
    :param result: Actual string extracted from the document.
    :param value: Expected value to compare against.
    :return: Boolean result, or ``False`` if the operator is unknown.
    """
    fn = OPERATOR_REGISTRY.get(operation)
    if fn is None:
        logger.warning("_apply_string_operator: unknown operation %r", operation)
        return False
    return fn(result, value)  # type: ignore[operator]


# ---------------------------------------------------------------------------
# Convenience: evaluate a list of values (metadata multi-value support)
# ---------------------------------------------------------------------------


def evaluate_header_value_list(
    rule: RuleModel, doc: ParsedDocument
) -> bool:
    """Evaluate a header rule where the expected value may be a CSV list.

    Each value in the comma-separated *rule.value* must independently pass
    the assertion.

    :param rule: Header rule with potentially comma-separated ``value``.
    :param doc: Parsed document to check.
    :return: ``True`` only if all values in the CSV list pass.
    """
    values = [v.strip() for v in rule.value.split(",")]
    return all(
        _evaluate_header_rule(
            rule.model_copy(update={"value": v}),
            doc,
        )
        for v in values
    )
