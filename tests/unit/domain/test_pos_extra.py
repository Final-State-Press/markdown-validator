"""Additional POS tests for edge cases."""

from __future__ import annotations

from unittest.mock import patch

from markdown_validator.domain.pos import word_pos_at


class TestWordPosAtErrors:
    def test_exception_returns_empty_string(self) -> None:
        """Simulate NLTK failure — should return empty string, not raise."""
        with patch("markdown_validator.domain.pos.nltk.word_tokenize",
                   side_effect=RuntimeError("NLTK error")):
            result = word_pos_at("Hello world", 1)
        assert result == ""
