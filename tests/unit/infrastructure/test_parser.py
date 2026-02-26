"""Unit tests for markdown_validator.infrastructure.parser."""

from __future__ import annotations

from pathlib import Path

import pytest

from markdown_validator.domain.models import ParsedDocument
from markdown_validator.infrastructure.parser import (
    _split_front_matter,
    find_markdown_files,
    parse_document,
)


class TestParseDocument:
    def test_returns_parsed_document(self, azure_md_path: Path) -> None:
        doc = parse_document(azure_md_path)
        assert isinstance(doc, ParsedDocument)

    def test_metadata_extracted(self, azure_doc: ParsedDocument) -> None:
        assert "title" in azure_doc.metadata
        assert "ms.topic" in azure_doc.metadata

    def test_html_contains_h1(self, azure_doc: ParsedDocument) -> None:
        assert "<h1>" in azure_doc.html

    def test_filepath_is_resolved(self, azure_md_path: Path) -> None:
        doc = parse_document(azure_md_path)
        assert doc.filepath.is_absolute()

    def test_file_not_found_raises(self) -> None:
        with pytest.raises(FileNotFoundError):
            parse_document("/no/such/file.md")

    def test_missing_front_matter_raises(self, tmp_path: Path) -> None:
        md = tmp_path / "no_frontmatter.md"
        md.write_text("# Just a heading\n\nNo front matter.", encoding="utf-8")
        with pytest.raises(ValueError, match="front-matter"):
            parse_document(md)

    def test_malformed_yaml_raises(self, tmp_path: Path) -> None:
        md = tmp_path / "bad_yaml.md"
        md.write_text("---\ntitle: [unclosed\n---\n# Body", encoding="utf-8")
        with pytest.raises(ValueError, match="malformed"):
            parse_document(md)

    def test_metadata_with_colon_in_value(self, tmp_path: Path) -> None:
        """PyYAML correctly handles colons in values (unlike the old naive splitter)."""
        md = tmp_path / "colon_value.md"
        md.write_text(
            "---\nurl: https://example.com/page\ntitle: My Article\n---\n# Body",
            encoding="utf-8",
        )
        doc = parse_document(md)
        assert doc.metadata["url"] == "https://example.com/page"
        assert doc.metadata["title"] == "My Article"


class TestFindMarkdownFiles:
    def test_finds_md_files(self, tmp_path: Path) -> None:
        (tmp_path / "a.md").write_text("---\ntitle: A\n---\n# A", encoding="utf-8")
        (tmp_path / "b.md").write_text("---\ntitle: B\n---\n# B", encoding="utf-8")
        (tmp_path / "c.txt").write_text("not markdown", encoding="utf-8")
        files = find_markdown_files(tmp_path)
        assert len(files) == 2
        assert all(f.suffix == ".md" for f in files)

    def test_recursive_search(self, tmp_path: Path) -> None:
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "nested.md").write_text("---\ntitle: N\n---\n# N", encoding="utf-8")
        files = find_markdown_files(tmp_path)
        assert any(f.name == "nested.md" for f in files)

    def test_not_a_directory_raises(self, tmp_path: Path) -> None:
        f = tmp_path / "file.md"
        f.write_text("---\ntitle: x\n---\n# x", encoding="utf-8")
        with pytest.raises(NotADirectoryError):
            find_markdown_files(f)


class TestSplitFrontMatter:
    def test_basic_split(self) -> None:
        raw = "---\ntitle: Hello\n---\n# Body"
        meta, body = _split_front_matter(raw, Path("test.md"))
        assert meta == {"title": "Hello"}
        assert "# Body" in body

    def test_unclosed_block_raises(self) -> None:
        raw = "---\ntitle: Hello\n"
        with pytest.raises(ValueError, match="unclosed"):
            _split_front_matter(raw, Path("test.md"))

    def test_no_front_matter_raises(self) -> None:
        raw = "# Just a heading"
        with pytest.raises(ValueError, match="front-matter"):
            _split_front_matter(raw, Path("test.md"))
