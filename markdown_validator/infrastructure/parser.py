"""Markdown document parser.

Reads a ``.md`` file from disk and returns a :class:`~markdown_validator.domain.models.ParsedDocument`.
This module is the only place in the codebase that touches the filesystem for
reading source documents.

Pipeline
--------
1. Read the raw file bytes (UTF-8).
2. Split the YAML front-matter block from the body using PyYAML.
3. Convert the body Markdown to HTML using the ``markdown`` library.
4. Return an immutable :class:`~markdown_validator.domain.models.ParsedDocument`.

:raises FileNotFoundError: If the given path does not exist.
:raises ValueError: If the YAML front-matter block is missing or malformed.
"""

from __future__ import annotations

import logging
from pathlib import Path

import markdown
import yaml

from markdown_validator.domain.models import ParsedDocument

logger = logging.getLogger(__name__)

_FRONT_MATTER_DELIMITER = "---"


def parse_document(filepath: str | Path) -> ParsedDocument:
    """Parse a Markdown file and return an immutable :class:`ParsedDocument`.

    The file must begin with a YAML front-matter block delimited by ``---``
    lines, for example::

        ---
        title: My Article
        ms.topic: tutorial
        ---
        # Body starts here

    :param filepath: Path to the ``.md`` file to parse.
    :return: Parsed and validated document representation.
    :raises FileNotFoundError: If *filepath* does not exist.
    :raises ValueError: If front-matter is absent or cannot be parsed as YAML.
    """
    path = Path(filepath)
    logger.info("parse_document: loading %s", path)

    if not path.exists():
        raise FileNotFoundError(f"Markdown file not found: {path}")

    raw = path.read_text(encoding="utf-8")
    metadata, body = _split_front_matter(raw, path)
    html = markdown.markdown(body)

    logger.debug("parse_document: %d metadata keys, %d chars html", len(metadata), len(html))
    return ParsedDocument(filepath=path.resolve(), metadata=metadata, html=html)


def find_markdown_files(directory: str | Path) -> list[Path]:
    """Recursively discover all ``.md`` files under *directory*.

    :param directory: Root directory to search.
    :return: Sorted list of :class:`pathlib.Path` objects.
    :raises NotADirectoryError: If *directory* is not a directory.
    """
    root = Path(directory)
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")
    files = sorted(root.rglob("*.md"))
    logger.info("find_markdown_files: found %d files under %s", len(files), root)
    return files


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _split_front_matter(raw: str, path: Path) -> tuple[dict[str, str], str]:
    """Split raw file text into a metadata dict and a body string.

    Expects the file to begin with ``---``, followed by YAML, followed by
    another ``---``.

    :param raw: Full raw file content.
    :param path: Source path (used in error messages only).
    :return: ``(metadata_dict, body_markdown_string)``
    :raises ValueError: If the front-matter structure is invalid.
    """
    stripped = raw.lstrip()
    if not stripped.startswith(_FRONT_MATTER_DELIMITER):
        raise ValueError(
            f"File {path} has no YAML front-matter block (expected '---' at start)"
        )

    # Split on the '---' delimiter; first occurrence opens the block, second closes it.
    parts = stripped.split(_FRONT_MATTER_DELIMITER, maxsplit=2)
    if len(parts) < 3:
        raise ValueError(
            f"File {path} has an unclosed YAML front-matter block"
        )

    yaml_block = parts[1]
    body = parts[2]

    try:
        raw_meta = yaml.safe_load(yaml_block)
    except yaml.YAMLError as exc:
        raise ValueError(f"YAML front-matter in {path} is malformed: {exc}") from exc

    if not isinstance(raw_meta, dict):
        raise ValueError(
            f"YAML front-matter in {path} must be a mapping, got {type(raw_meta).__name__}"
        )

    # Coerce all values to strings for uniform downstream handling
    metadata: dict[str, str] = {str(k): str(v) for k, v in raw_meta.items()}
    return metadata, body
