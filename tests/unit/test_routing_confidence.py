"""Tests for the heuristic confidence scorer (plan §P4.4)."""

from __future__ import annotations

import pytest

from scripts.workbench.core import routing_confidence as RC


def _matched(**kwargs) -> dict:
    """Build a matched_tokens snapshot with explicit overrides."""
    base = {
        "definition": [], "depth": [], "cs_domain": [], "learning_concept": [],
        "coach_request": [], "tool": [], "override": None,
    }
    base.update(kwargs)
    return base


def _decision(**kwargs) -> dict:
    base = {
        "tier": 1, "mode": "cheap", "reason": "...",
        "experience_level": None, "override_active": False,
        "blocked": False, "promoted_by_profile": False,
    }
    base.update(kwargs)
    return base


# ---------------------------------------------------------------------------
# Override always wins
# ---------------------------------------------------------------------------

def test_override_active_returns_max_confidence():
    res = RC.score_decision(
        decision=_decision(override_active=True),
        matched_tokens=_matched(),
    )
    assert res.score == 1.0
    assert res.should_fallback is False


# ---------------------------------------------------------------------------
# Tier 3
# ---------------------------------------------------------------------------

def test_tier3_with_coach_token_high_confidence():
    res = RC.score_decision(
        decision=_decision(tier=3, mode="coach-run"),
        matched_tokens=_matched(coach_request=["내 pr"]),
    )
    assert res.score >= 0.9
    assert res.should_fallback is False


def test_tier3_blocked_moderate_confidence_no_fallback():
    """Blocked = we know the intent but can't help. AI can't fix
    repo state, so don't fall back."""
    res = RC.score_decision(
        decision=_decision(tier=3, mode=None, blocked=True),
        matched_tokens=_matched(coach_request=["내 pr"]),
    )
    assert 0.5 <= res.score <= 0.7
    assert res.should_fallback is False  # 0.6 > default 0.55


def test_tier3_without_coach_token_low_confidence_falls_back():
    res = RC.score_decision(
        decision=_decision(tier=3, mode="coach-run"),
        matched_tokens=_matched(),
    )
    assert res.should_fallback is True


# ---------------------------------------------------------------------------
# Tier 2
# ---------------------------------------------------------------------------

def test_tier2_depth_and_domain_high_confidence():
    res = RC.score_decision(
        decision=_decision(tier=2, mode="full"),
        matched_tokens=_matched(depth=["vs"], cs_domain=["트랜잭션"]),
    )
    assert res.score >= 0.8
    assert res.should_fallback is False


def test_tier2_promoted_by_profile_softer_score():
    res = RC.score_decision(
        decision=_decision(tier=2, mode="full", promoted_by_profile=True),
        matched_tokens=_matched(definition=["뭐야"], cs_domain=["트랜잭션"]),
    )
    assert 0.6 <= res.score <= 0.8


def test_tier2_with_extra_buckets_takes_ambiguity_penalty():
    """Domain + depth + tool all firing → ambiguous prompt; score
    drops slightly to encourage AI fallback consideration."""
    plain = RC.score_decision(
        decision=_decision(tier=2, mode="full"),
        matched_tokens=_matched(depth=["vs"], cs_domain=["트랜잭션"]),
    )
    busy = RC.score_decision(
        decision=_decision(tier=2, mode="full"),
        matched_tokens=_matched(
            depth=["vs"], cs_domain=["트랜잭션"],
            tool=["gradle"], definition=["뭐야"],
        ),
    )
    assert busy.score < plain.score


# ---------------------------------------------------------------------------
# Tier 1
# ---------------------------------------------------------------------------

def test_tier1_definition_and_domain():
    res = RC.score_decision(
        decision=_decision(tier=1, mode="cheap"),
        matched_tokens=_matched(definition=["뭐야"], cs_domain=["스레드"]),
    )
    assert 0.7 <= res.score <= 0.8


def test_tier1_weak_signal_falls_back():
    res = RC.score_decision(
        decision=_decision(tier=1, mode="cheap"),
        matched_tokens=_matched(),
    )
    assert res.should_fallback is True


# ---------------------------------------------------------------------------
# Tier 0
# ---------------------------------------------------------------------------

def test_tier0_tool_only_high_confidence():
    res = RC.score_decision(
        decision=_decision(tier=0, mode=None),
        matched_tokens=_matched(tool=["gradle"]),
    )
    assert res.score >= 0.8


def test_tier0_no_signals_at_all_acceptable():
    """Off-topic chatter — Tier 0 is right, score is moderate."""
    res = RC.score_decision(
        decision=_decision(tier=0, mode=None),
        matched_tokens=_matched(),
    )
    assert 0.5 <= res.score <= 0.7
    # Above default threshold, so no fallback
    assert res.should_fallback is False


def test_tier0_with_signal_tokens_falls_back():
    """Tier 0 *despite* domain matched is the suspicious case — AI
    fallback might recover."""
    res = RC.score_decision(
        decision=_decision(tier=0, mode=None),
        matched_tokens=_matched(cs_domain=["트랜잭션"]),
    )
    assert res.score < 0.55
    assert res.should_fallback is True


# ---------------------------------------------------------------------------
# Threshold parameter
# ---------------------------------------------------------------------------

def test_custom_threshold_changes_fallback_decision():
    res_low = RC.score_decision(
        decision=_decision(tier=1, mode="cheap"),
        matched_tokens=_matched(definition=["뭐야"], cs_domain=["스레드"]),
        threshold=0.9,  # very strict — even good Tier 1 would fall back
    )
    res_high = RC.score_decision(
        decision=_decision(tier=1, mode="cheap"),
        matched_tokens=_matched(definition=["뭐야"], cs_domain=["스레드"]),
        threshold=0.3,  # lax — almost nothing falls back
    )
    assert res_low.should_fallback is True
    assert res_high.should_fallback is False


def test_invalid_threshold_raises():
    with pytest.raises(ValueError):
        RC.score_decision(
            decision=_decision(tier=0),
            matched_tokens=_matched(),
            threshold=1.5,
        )


# ---------------------------------------------------------------------------
# Score is always clamped
# ---------------------------------------------------------------------------

def test_score_always_in_unit_interval():
    """Synthetic stress check across many shapes — score stays in [0, 1]."""
    cases = [
        (_decision(tier=t), _matched()) for t in (0, 1, 2, 3)
    ] + [
        (_decision(tier=99), _matched()),  # bogus tier
    ]
    for d, m in cases:
        res = RC.score_decision(decision=d, matched_tokens=m)
        assert 0.0 <= res.score <= 1.0


def test_result_carries_rationale():
    res = RC.score_decision(
        decision=_decision(override_active=True),
        matched_tokens=_matched(),
    )
    assert "override" in res.rationale.lower()
