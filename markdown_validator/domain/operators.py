"""Pure comparison operator functions.

Every public function in this module is a *strategy* — a ``Callable[[str, str], bool]``
that takes a *result* string and an *expected* value string, and returns
``True`` if the assertion is satisfied.

Design pattern: **Strategy** — operators are independent functions with a
uniform signature. Adding a new operator requires no changes to the caller;
it is simply registered in :data:`OPERATOR_REGISTRY`.

None of these functions perform I/O, logging, or raise exceptions on normal
evaluation. Invalid inputs return ``False``.
"""

from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# String comparison operators
# ---------------------------------------------------------------------------


def op_equal(result: str, value: str) -> bool:
    """Return ``True`` if *result* and *value* are equal (stripped).

    :param result: Actual string extracted from the document.
    :param value: Expected value to compare against.
    :return: ``True`` when both strings are equal after stripping whitespace.
    """
    return result.strip() == value.strip()


def op_not_equal(result: str, value: str) -> bool:
    """Return ``True`` if *result* and *value* are **not** equal (stripped).

    :param result: Actual string extracted from the document.
    :param value: Expected value to compare against.
    :return: ``True`` when strings differ after stripping whitespace.
    """
    return result.strip() != value.strip()


def op_greater(result: str, value: str) -> bool:
    """Return ``True`` if numeric *result* is greater than numeric *value*.

    :param result: Actual value (will be cast to ``int``).
    :param value: Expected threshold (will be cast to ``int``).
    :return: ``True`` when ``int(result) > int(value)``.
    """
    try:
        return int(result) > int(value)
    except (ValueError, TypeError):
        logger.warning("op_greater: non-numeric operand result=%r value=%r", result, value)
        return False


def op_less(result: str, value: str) -> bool:
    """Return ``True`` if numeric *result* is less than numeric *value*.

    :param result: Actual value (will be cast to ``int``).
    :param value: Expected threshold (will be cast to ``int``).
    :return: ``True`` when ``int(result) < int(value)``.
    """
    try:
        return int(result) < int(value)
    except (ValueError, TypeError):
        logger.warning("op_less: non-numeric operand result=%r value=%r", result, value)
        return False


def op_contains(result: str, value: str) -> bool:
    """Return ``True`` if *value* appears inside *result* (case-insensitive).

    :param result: Actual string extracted from the document.
    :param value: Substring to search for.
    :return: ``True`` when *value* is found within *result*.
    """
    return value.lower().strip() in result.lower()


def op_starts_with(result: str, value: str) -> bool:
    """Return ``True`` if *result* starts with *value*.

    :param result: Actual string extracted from the document.
    :param value: Expected prefix.
    :return: ``True`` when *result* begins with *value* (stripped).
    """
    return result.startswith(value.strip())


def op_ends_with(result: str, value: str) -> bool:
    """Return ``True`` if *result* ends with *value*.

    :param result: Actual string extracted from the document.
    :param value: Expected suffix.
    :return: ``True`` when *result* ends with *value* (stripped).
    """
    return result.endswith(value.strip())


def op_regex(result: str, value: str) -> bool:
    """Return ``True`` if *result* matches the regex pattern in *value*.

    Uses Python :mod:`re` with ``re.DOTALL``.

    :param result: String to search within.
    :param value: Regular expression pattern (Python syntax).
    :return: ``True`` when the pattern matches.
    """
    try:
        return bool(re.search(value, result, re.DOTALL))
    except re.error as exc:
        logger.warning("op_regex: invalid pattern %r — %s", value, exc)
        return False


def op_length(result: str, value: str) -> bool:
    """Return ``True`` if ``len(result)`` is **less than** *value*.

    :param result: String whose length is measured.
    :param value: Maximum allowed length (exclusive), as a string integer.
    :return: ``True`` when ``len(result) < int(value)``.
    """
    try:
        return len(result) < int(value)
    except (ValueError, TypeError):
        logger.warning("op_length: non-numeric value %r", value)
        return False


# ---------------------------------------------------------------------------
# Date comparison operator
# ---------------------------------------------------------------------------


def _parse_date(raw: str) -> date:
    """Parse a date string in ``m/d/yyyy`` or ``m-d-yy`` formats.

    :param raw: Date string to parse.
    :return: A :class:`datetime.date` object.
    :raises ValueError: If the string cannot be parsed.
    """
    normalised = raw.strip().replace("/", "-")
    parts = normalised.split("-")
    if len(parts) != 3:
        raise ValueError(f"Cannot parse date: {raw!r}")
    month, day, year_str = parts
    year = int(year_str)
    # Handle 2-digit years stored as YY after the year 2000
    if len(year_str) == 2:
        year += 2000
    return date(month=int(month), day=int(day), year=year)


def op_date(result: str, operator: str, value: str) -> bool:
    """Compare a date string against another date or an offset.

    :param result: Date string from the document metadata.
    :param operator: One of ``"=="``, ``"!="``, ``"<"``, ``">"``.
    :param value: Either ``"now"`` (current date), an integer number of days
        (interpreted as *today minus N days*), or another date string.
    :return: Boolean result of the date comparison.
    """
    try:
        date1 = _parse_date(result)
    except ValueError:
        logger.warning("op_date: cannot parse document date %r", result)
        return False

    try:
        if value.lower() == "now":
            date2: date = datetime.now().date()
        else:
            days = int(value)
            date2 = (datetime.now() - timedelta(days=days)).date()
    except ValueError:
        try:
            date2 = _parse_date(value)
        except ValueError:
            logger.warning("op_date: cannot parse comparison date %r", value)
            return False

    if operator == "==":
        return date1 == date2
    if operator == "!=":
        return date1 != date2
    if operator == "<":
        return date1 < date2
    if operator == ">":
        return date1 > date2
    logger.warning("op_date: unknown operator %r", operator)
    return False


# ---------------------------------------------------------------------------
# Operator registry
# ---------------------------------------------------------------------------


#: Maps operator token strings to their handler functions.
#: Functions must accept ``(result: str, value: str) -> bool``.
#: The ``date`` and ``pos``/``s`` operators are handled separately in
#: :mod:`markdown_validator.domain.evaluator` because they require extra
#: context (operator string or index).
OPERATOR_REGISTRY: dict[str, object] = {
    "==": op_equal,
    "!=": op_not_equal,
    ">": op_greater,
    "<": op_less,
    "[]": op_contains,
    "[:": op_starts_with,
    ":]": op_ends_with,
    "r": op_regex,
    "l": op_length,
}
