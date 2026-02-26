"""markdown_validator — rule-based Markdown document validation.

Public API surface::

    from markdown_validator import Scanner, ScanReport

The full layer structure is documented in :mod:`markdown_validator.domain`,
:mod:`markdown_validator.infrastructure`, :mod:`markdown_validator.services`,
and :mod:`markdown_validator.cli`.
"""

from markdown_validator.domain.models import (
    ParsedDocument,
    RuleModel,
    RuleSetModel,
    ScanReport,
    ValidationResult,
    WorkflowResult,
)
from markdown_validator.services.scanner import Scanner

__all__ = [
    "Scanner",
    "ScanReport",
    "ValidationResult",
    "RuleModel",
    "RuleSetModel",
    "ParsedDocument",
    "WorkflowResult",
]

__version__ = "0.2.0"
