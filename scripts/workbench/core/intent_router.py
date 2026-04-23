"""Two-stage intent routing.

Stage 1 — ``pre_decide``
    Fast rule-based classification run **before** CS augmentation. Decides
    whether the turn is mission-only, cs-only, mixed, or a drill answer,
    and picks a ``cs_search_mode`` ("skip" | "cheap" | "full") so the
    searcher pipeline can skip expensive work on pure mission turns.

Stage 2 — ``finalize``
    Run **after** augment + drill offer + profile merge. Uses the actual
    augmentation result + drill offer to lock down the final
    ``block_plan`` for the AI session (which blocks are primary /
    supporting / omit).

The separation exists so (a) pure mission turns can ``skip`` CS search
entirely (no numpy / sentence-transformers loaded, no latency), and (b)
the block plan reflects real augment results instead of being a guess.
See Phase 2.3 / 5차 Finding 2 in the plan.

``block_plan`` is advisory guidance, not a hard enforcement. The AI
session copies ``primary`` and ``supporting`` blocks into its reply and
may omit ``omit`` blocks — but runtime validators do not punish
divergence. This matches the existing snapshot_block copy rule
inherited from the coach pipeline (the "verbatim" guidance is not
enforced at validation time).
"""

from __future__ import annotations

from typing import Any

from .answer_classifier import classify_drill_answer as _looks_like_drill_answer
from .intent_tokens import CS_TOKENS as _CS_TOKENS
from .intent_tokens import MISSION_TOKENS as _MISSION_TOKENS

# Intent labels (also used inside coach-run.json.intent_decision).
MISSION_ONLY = "mission_only"
CS_ONLY = "cs_only"
MIXED = "mixed"
DRILL_ANSWER = "drill_answer"
MIXED_WITH_DRILL_ANSWER = "mixed_with_drill_answer"
UNKNOWN = "unknown"

VALID_INTENTS = {
    MISSION_ONLY,
    CS_ONLY,
    MIXED,
    DRILL_ANSWER,
    MIXED_WITH_DRILL_ANSWER,
    UNKNOWN,
}


def _haystack(prompt: str) -> str:
    return (prompt or "").lower()


def _count_substr_hits(haystack: str, tokens: frozenset[str]) -> int:
    return sum(1 for t in tokens if t in haystack)


# ---------------------------------------------------------------------------
# Stage 1: pre_decide
# ---------------------------------------------------------------------------

def pre_decide(
    prompt: str,
    *,
    history: list[dict] | None = None,
    pending_drill: dict | None = None,
    learner_state: dict | None = None,
) -> dict[str, Any]:
    """Classify a turn before CS augment.

    Returns ``{"pre_intent", "cs_search_mode", "signals"}``.
    ``cs_search_mode`` ∈ {"skip", "cheap", "full"}.
    """
    haystack = _haystack(prompt)

    mission_score = _count_substr_hits(haystack, _MISSION_TOKENS)
    cs_score = _count_substr_hits(haystack, _CS_TOKENS)

    # Learner state hints: an unresolved thread count > 0 nudges the
    # mission axis, even when the prompt is short.
    ls_unresolved = 0
    if learner_state:
        threads = ((learner_state.get("target_pr_detail") or {}).get("threads") or [])
        ls_unresolved = sum(
            1 for t in threads if t.get("classification") in {"still-applies", "ambiguous", "unread"}
        )

    drill_is_answer, drill_signals = _looks_like_drill_answer(prompt, pending_drill)

    signals = {
        "mission_score": mission_score,
        "cs_score": cs_score,
        "unresolved_thread_count": ls_unresolved,
        "drill_signals": drill_signals,
    }

    # Drill-answer path
    if drill_is_answer:
        if mission_score > 0:
            pre_intent = MIXED_WITH_DRILL_ANSWER
        else:
            pre_intent = DRILL_ANSWER
        return {"pre_intent": pre_intent, "cs_search_mode": "cheap", "signals": signals}

    if mission_score == 0 and cs_score == 0:
        # No strong signal. Lean mission-only if there are unresolved
        # threads; otherwise unknown/mixed.
        if ls_unresolved > 0:
            return {"pre_intent": MISSION_ONLY, "cs_search_mode": "skip", "signals": signals}
        return {"pre_intent": UNKNOWN, "cs_search_mode": "cheap", "signals": signals}

    if mission_score > 0 and cs_score == 0:
        return {"pre_intent": MISSION_ONLY, "cs_search_mode": "skip", "signals": signals}

    if cs_score > 0 and mission_score == 0:
        return {"pre_intent": CS_ONLY, "cs_search_mode": "full", "signals": signals}

    return {"pre_intent": MIXED, "cs_search_mode": "full", "signals": signals}


# ---------------------------------------------------------------------------
# Stage 2: finalize
# ---------------------------------------------------------------------------

def _empty_block_plan() -> dict[str, str]:
    return {
        "snapshot_block": "omit",
        "cs_block": "omit",
        "verification": "omit",
        "drill_block": "omit",
    }


def finalize(
    pre_result: dict[str, Any],
    *,
    augment_result: dict | None = None,
    drill_offer: dict | None = None,
    drill_result: dict | None = None,
    verification_required_count: int = 0,
    learner_state_coverage: str | None = None,
) -> dict[str, Any]:
    """Lock the final intent_decision + block_plan for this turn.

    ``learner_state_coverage`` reflects ``learner_state.coverage`` at scan
    time: ``"full"`` means every thread was processed within the budget,
    ``"partial"`` means the scan hit caps and some threads were skipped.
    When partial, any ``snapshot_block == "primary"`` is downgraded to
    ``"supporting"`` so the AI session stops promoting an incomplete
    snapshot as the canonical answer.
    """
    pre_intent = pre_result.get("pre_intent", UNKNOWN)
    detected_intent = pre_intent  # finalize may refine below

    has_cs_hits = bool(
        augment_result
        and (augment_result.get("by_learning_point") or augment_result.get("by_fallback_key"))
    )

    block_plan = _empty_block_plan()

    if pre_intent == MISSION_ONLY:
        block_plan["snapshot_block"] = "primary"
        block_plan["cs_block"] = "omit"
        block_plan["verification"] = "primary" if verification_required_count > 0 else "omit"
    elif pre_intent == CS_ONLY:
        block_plan["cs_block"] = "primary" if has_cs_hits else "omit"
        block_plan["snapshot_block"] = "omit"
        block_plan["verification"] = "omit"
        if not has_cs_hits:
            # Fall back to mission-only surfacing so the learner still
            # gets *something* on a degraded CS turn.
            block_plan["snapshot_block"] = "supporting"
    elif pre_intent in (MIXED, UNKNOWN):
        block_plan["snapshot_block"] = "primary"
        block_plan["cs_block"] = "supporting" if has_cs_hits else "omit"
        block_plan["verification"] = "supporting" if verification_required_count > 0 else "omit"
    elif pre_intent == DRILL_ANSWER:
        block_plan["drill_block"] = "primary"
        block_plan["cs_block"] = "supporting" if has_cs_hits else "omit"
        block_plan["snapshot_block"] = "supporting"
        block_plan["verification"] = "supporting" if verification_required_count > 0 else "omit"
    elif pre_intent == MIXED_WITH_DRILL_ANSWER:
        block_plan["snapshot_block"] = "primary"
        block_plan["drill_block"] = "supporting"
        block_plan["cs_block"] = "supporting" if has_cs_hits else "omit"
        block_plan["verification"] = "supporting" if verification_required_count > 0 else "omit"

    # drill_block elevation when a *new* offer exists and intent isn't
    # already drill-driven.
    if drill_offer and block_plan["drill_block"] == "omit":
        block_plan["drill_block"] = "supporting"

    # Partial-coverage downgrade: a snapshot built from a truncated scan
    # should never be narrated as the primary answer.
    coverage_downgraded = False
    if learner_state_coverage == "partial" and block_plan["snapshot_block"] == "primary":
        block_plan["snapshot_block"] = "supporting"
        coverage_downgraded = True

    return {
        "detected_intent": detected_intent,
        "pre_intent": pre_intent,
        "cs_search_mode": pre_result.get("cs_search_mode"),
        "signals": pre_result.get("signals", {}),
        "block_plan": block_plan,
        "coverage": learner_state_coverage,
        "coverage_downgraded_snapshot": coverage_downgraded,
        "drill_in_turn": {
            "has_offer": drill_offer is not None,
            "has_result": drill_result is not None,
        },
    }
