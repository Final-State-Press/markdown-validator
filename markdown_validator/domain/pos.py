"""Part-of-speech analysis utilities.

Wraps NLTK tokenisation and POS tagging behind a narrow, pure interface.
All functions accept plain text strings and return plain text strings or
integers; no I/O or side-effects.

NLTK data (``punkt_tab``, ``averaged_perceptron_tagger_eng``) must be
downloaded before first use::

    import nltk
    nltk.download("punkt_tab")
    nltk.download("averaged_perceptron_tagger_eng")
"""

from __future__ import annotations

import logging

import nltk

logger = logging.getLogger(__name__)

#: Penn Treebank POS tag descriptions, provided for documentation and
#: error messages.
PENN_TAGS: dict[str, str] = {
    "CC": "Coordinating conjunction",
    "CD": "Cardinal number",
    "DT": "Determiner",
    "EX": "Existential there",
    "FW": "Foreign word",
    "IN": "Preposition or subordinating conjunction",
    "JJ": "Adjective",
    "JJR": "Adjective, comparative",
    "JJS": "Adjective, superlative",
    "LS": "List item marker",
    "MD": "Modal",
    "NN": "Noun, singular or mass",
    "NNS": "Noun, plural",
    "NNP": "Proper noun, singular",
    "NNPS": "Proper noun, plural",
    "PDT": "Predeterminer",
    "POS": "Possessive ending",
    "PRP": "Personal pronoun",
    "PRP$": "Possessive pronoun",
    "RB": "Adverb",
    "RBR": "Adverb, comparative",
    "RBS": "Adverb, superlative",
    "RP": "Particle",
    "SYM": "Symbol",
    "TO": "to",
    "UH": "Interjection",
    "VB": "Verb, base form",
    "VBD": "Verb, past tense",
    "VBG": "Verb, gerund or present participle",
    "VBN": "Verb, past participle",
    "VBP": "Verb, non-3rd person singular present",
    "VBZ": "Verb, 3rd person singular present",
    "WDT": "Wh-determiner",
    "WP": "Wh-pronoun",
    "WP$": "Possessive wh-pronoun",
    "WRB": "Wh-adverb",
}


def sentence_count(text: str) -> int:
    """Return the number of sentences in *text*.

    :param text: Plain text to analyse.
    :return: Number of sentences detected by NLTK's sentence tokeniser.
    """
    sentences = nltk.sent_tokenize(text)
    return len(sentences)


def word_pos_at(text: str, index: int) -> str:
    """Return the Penn Treebank POS tag for the word at *index* (1-based).

    The entire *text* is tokenised as a single corpus before indexing, so
    *index* counts across all tokens in order.

    :param text: Plain text to analyse.
    :param index: 1-based position of the word whose POS tag is requested.
    :return: POS tag string, e.g. ``"NN"`` or ``"VB"``.  Returns ``""`` if
        the index is out of range.
    """
    try:
        tokens = nltk.word_tokenize(text)
        tagged: list[tuple[str, str]] = nltk.pos_tag(tokens)
        # Convert to 1-based indexing
        if index < 1 or index > len(tagged):
            logger.warning(
                "word_pos_at: index %d out of range for %d tokens",
                index,
                len(tagged),
            )
            return ""
        return tagged[index - 1][1]
    except Exception:
        logger.exception("word_pos_at: failed to tag text %r at index %d", text[:50], index)
        return ""
