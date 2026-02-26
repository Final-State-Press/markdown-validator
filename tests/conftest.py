"""Shared pytest fixtures for all test modules.

Fixtures are organised by scope:
- ``session`` scope: expensive objects created once per test run (parsed doc).
- ``function`` scope (default): cheap objects recreated per test.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from markdown_validator.domain.models import (
    ParsedDocument,
    RuleModel,
    RuleSetModel,
    RulesSection,
)
from markdown_validator.infrastructure.parser import parse_document

# ---------------------------------------------------------------------------
# Fixture paths (cross-platform)
# ---------------------------------------------------------------------------

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="session")
def azure_md_path() -> Path:
    """Path to the azure-stack-overview.md test fixture."""
    return FIXTURES / "azure-stack-overview.md"


@pytest.fixture(scope="session")
def checkworkflow_json_path() -> Path:
    """Path to the checkworkflow.json test fixture."""
    return FIXTURES / "checkworkflow.json"


@pytest.fixture(scope="session")
def concept_json_path() -> Path:
    """Path to the concept.json test fixture."""
    return FIXTURES / "concept.json"


@pytest.fixture(scope="session")
def tutorial_md_path() -> Path:
    """Path to the tutorial.md valid template fixture."""
    return FIXTURES / "validtemplates" / "tutorial.md"


@pytest.fixture(scope="session")
def concept_md_path() -> Path:
    """Path to the concept.md valid template fixture."""
    return FIXTURES / "validtemplates" / "concept.md"


# ---------------------------------------------------------------------------
# Parsed document fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def azure_doc(azure_md_path: Path) -> ParsedDocument:
    """Pre-parsed ParsedDocument for azure-stack-overview.md."""
    return parse_document(azure_md_path)


# ---------------------------------------------------------------------------
# Minimal in-memory rule set fixture (no file I/O needed in unit tests)
# ---------------------------------------------------------------------------


@pytest.fixture
def minimal_header_rule() -> RuleModel:
    """A minimal header rule: checks ms.topic == 'overview'."""
    return RuleModel(
        id=1,
        name="ms-topic-check",
        type="header",
        query="ms.topic",
        flag="value",
        operation="==",
        value="overview",
    )


@pytest.fixture
def minimal_body_rule() -> RuleModel:
    """A minimal body rule: checks that an H1 exists (count == 1)."""
    return RuleModel(
        id=2,
        name="h1-count",
        type="body",
        query="/html/body/h1",
        flag="count",
        operation="==",
        value="1",
    )


@pytest.fixture
def minimal_rule_set(
    minimal_header_rule: RuleModel, minimal_body_rule: RuleModel
) -> RuleSetModel:
    """A minimal RuleSetModel with one header and one body rule."""
    return RuleSetModel(
        rules=RulesSection(header=[minimal_header_rule], body=[minimal_body_rule])
    )
