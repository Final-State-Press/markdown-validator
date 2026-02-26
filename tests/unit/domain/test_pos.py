"""Unit tests for markdown_validator.domain.pos."""

from __future__ import annotations

import pytest

from markdown_validator.domain.pos import PENN_TAGS, sentence_count, word_pos_at


class TestSentenceCount:
    def test_single_sentence(self) -> None:
        assert sentence_count("Hello world.") == 1

    def test_two_sentences(self) -> None:
        assert sentence_count("Hello world. How are you?") == 2

    def test_empty_string(self) -> None:
        # NLTK returns 1 for empty string (empty sentence)
        result = sentence_count("")
        assert isinstance(result, int)

    def test_paragraph(self) -> None:
        text = "First sentence. Second sentence. Third sentence."
        assert sentence_count(text) == 3


class TestWordPosAt:
    def test_noun(self) -> None:
        # "Azure" as a proper noun
        tag = word_pos_at("Azure Stack Hub overview", 1)
        assert tag in ("NNP", "NN")  # may vary with NLTK model

    def test_verb_base_form(self) -> None:
        # "Run" at position 1
        tag = word_pos_at("Run the command now", 1)
        assert tag in ("VB", "VBP", "NN")

    def test_out_of_range_returns_empty(self) -> None:
        result = word_pos_at("One word", 99)
        assert result == ""

    def test_zero_index_returns_empty(self) -> None:
        result = word_pos_at("Hello world", 0)
        assert result == ""

    def test_returns_string(self) -> None:
        result = word_pos_at("The quick brown fox", 1)
        assert isinstance(result, str)


class TestPennTags:
    def test_known_tags_present(self) -> None:
        for tag in ("NN", "VB", "JJ", "NNP", "CC"):
            assert tag in PENN_TAGS

    def test_total_count(self) -> None:
        assert len(PENN_TAGS) >= 30
