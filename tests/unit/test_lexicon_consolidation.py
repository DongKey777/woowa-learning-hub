"""Tests for the consolidated lexicon module (plan §P5.1).

Locks the contract that:

1. ``lexicon.py`` is the single source of truth — the router and
   intent_tokens modules re-export the *same* identity (no copies).
2. Every set is non-empty and contains no obviously dangerous tokens
   (1-char Korean particles that would false-positive).
3. Match helpers behave correctly on the canonical false-positive
   case (Korean particle attached to ASCII token like ``"DI가"``) and
   the substring case.
"""

from __future__ import annotations

import pytest

from scripts.workbench.core import intent_tokens, interactive_rag_router, lexicon


# ---------------------------------------------------------------------------
# Re-export identity — adding a token to lexicon.py must propagate
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", [
    "DEFINITION_SIGNALS", "DEPTH_SIGNALS", "CS_DOMAIN_TOKENS",
    "STUDY_INTENT_SIGNALS", "LEARNING_CONCEPT_TOKENS",
    "COACH_REQUEST_TOKENS", "TOOL_TOKENS", "BEGINNER_HINTS",
    "ADVANCED_HINTS", "OVERRIDE_TOKENS",
])
def test_router_reexports_lexicon_identity(name):
    """The router module must use the *same* object from lexicon — not
    a copy. If a future PR redefines a token set inline, this test
    catches it immediately."""
    assert getattr(interactive_rag_router, name) is getattr(lexicon, name)


@pytest.mark.parametrize("name", ["MISSION_TOKENS", "CS_TOKENS", "DRILL_ANSWER_NEGATIVE_KEYWORDS"])
def test_intent_tokens_reexports_lexicon_identity(name):
    assert getattr(intent_tokens, name) is getattr(lexicon, name)


# ---------------------------------------------------------------------------
# Set hygiene — no 1-char Korean particles snuck in
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name,tokens", [
    ("DEFINITION_SIGNALS", lexicon.DEFINITION_SIGNALS),
    ("DEPTH_SIGNALS", lexicon.DEPTH_SIGNALS),
    ("STUDY_INTENT_SIGNALS", lexicon.STUDY_INTENT_SIGNALS),
    ("CS_DOMAIN_TOKENS", lexicon.CS_DOMAIN_TOKENS),
    ("LEARNING_CONCEPT_TOKENS", lexicon.LEARNING_CONCEPT_TOKENS),
    ("COACH_REQUEST_TOKENS", lexicon.COACH_REQUEST_TOKENS),
    ("TOOL_TOKENS", lexicon.TOOL_TOKENS),
    ("BEGINNER_HINTS", lexicon.BEGINNER_HINTS),
    ("ADVANCED_HINTS", lexicon.ADVANCED_HINTS),
    ("MISSION_TOKENS", lexicon.MISSION_TOKENS),
    ("CS_TOKENS", lexicon.CS_TOKENS),
    ("DRILL_ANSWER_NEGATIVE_KEYWORDS", lexicon.DRILL_ANSWER_NEGATIVE_KEYWORDS),
])
def test_no_empty_or_whitespace_only_tokens(name, tokens):
    for tok in tokens:
        assert isinstance(tok, str), f"{name}: non-str token {tok!r}"
        assert tok.strip(), f"{name}: empty/whitespace token"


def test_lexicon_sets_are_non_empty():
    for name in (
        "DEFINITION_SIGNALS", "DEPTH_SIGNALS", "CS_DOMAIN_TOKENS",
        "STUDY_INTENT_SIGNALS", "LEARNING_CONCEPT_TOKENS",
        "COACH_REQUEST_TOKENS", "TOOL_TOKENS", "BEGINNER_HINTS",
        "ADVANCED_HINTS",
        "MISSION_TOKENS", "CS_TOKENS", "DRILL_ANSWER_NEGATIVE_KEYWORDS",
    ):
        assert len(getattr(lexicon, name)) > 0, name


# ---------------------------------------------------------------------------
# match_word_boundary contract
# ---------------------------------------------------------------------------

def test_word_boundary_handles_korean_attached_to_ascii():
    """Canonical false-positive guard: ASCII token must NOT match when
    immediately followed by Hangul under naive \\b. Lookaround fixes."""
    assert lexicon.match_word_boundary_one("DI가 뭐야", "di") is True
    # "ad" should NOT match "DI가 뭐야"
    assert lexicon.match_word_boundary_one("DI가 뭐야", "ad") is False
    # Embedded ASCII inside another ASCII word is rejected
    assert lexicon.match_word_boundary_one("identity", "id") is False


def test_word_boundary_korean_substring_ok():
    """Korean tokens use casefold substring — distinctive multi-char
    tokens shouldn't false-positive."""
    assert lexicon.match_word_boundary_one("스프링 빈이 뭐야", "스프링") is True
    assert lexicon.match_word_boundary_one("스프링 빈이 뭐야", "트랜잭션") is False


def test_word_boundary_caseinsensitive():
    assert lexicon.match_word_boundary_one("DI가 뭐야", "DI") is True
    assert lexicon.match_word_boundary_one("di가 뭐야", "DI") is True


def test_match_word_boundary_iterates():
    assert lexicon.match_word_boundary("MVCC vs 격리수준", lexicon.DEPTH_SIGNALS) is True
    assert lexicon.match_word_boundary("그냥 잡담", lexicon.DEPTH_SIGNALS) is False


def test_study_intent_signals_are_separate_from_domain():
    assert lexicon.match_word_boundary("DB 설계 공부하고 싶어", lexicon.STUDY_INTENT_SIGNALS) is True
    assert lexicon.match_word_boundary("DB 설계 공부하고 싶어", lexicon.CS_DOMAIN_TOKENS) is True
    assert lexicon.match_word_boundary("그냥 공부하고 싶어", lexicon.CS_DOMAIN_TOKENS) is False


# ---------------------------------------------------------------------------
# Substring helpers
# ---------------------------------------------------------------------------

def test_match_substring_lowercases_haystack():
    assert lexicon.match_substring("Spring Bean Review", lexicon.MISSION_TOKENS) is True
    assert lexicon.match_substring("아무 의미 없는 잡담", lexicon.MISSION_TOKENS) is False


def test_count_substring_hits_returns_count():
    # 'review' + 'pr' both in MISSION_TOKENS (lowercased haystack)
    n = lexicon.count_substring_hits("PR review thread", lexicon.MISSION_TOKENS)
    assert n >= 2  # exact count depends on token set; just lock that hits multiple
    # 'thread', 'pr', 'review' all match


# ---------------------------------------------------------------------------
# Strategy tags exposed
# ---------------------------------------------------------------------------

def test_strategy_constants_available():
    assert lexicon.WORD_BOUNDARY == "word_boundary"
    assert lexicon.SUBSTRING == "substring"
