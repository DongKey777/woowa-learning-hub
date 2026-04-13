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

import re
from typing import Any

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

_MISSION_TOKENS = {
    # Korean
    "pr", "리뷰", "리뷰어", "스레드", "코멘트", "브랜치", "커밋", "해결",
    "답변", "답글", "내 pr", "내꺼", "내 코드", "내 미션", "미션",
    # English
    "pull request", "review", "reviewer", "thread", "unresolved",
    "branch", "commit", "feedback", "comment",
}

_CS_TOKENS = {
    # Korean
    "개념", "이론", "원리", "차이", "왜", "무엇", "정의", "설명해",
    "알려줘", "격리", "트랜잭션", "정규화", "인덱스", "캐시", "락",
    "쓰레드", "동기화", "재시도", "타임아웃", "아키텍처", "패턴",
    # English
    "concept", "theory", "definition", "difference between", "explain",
    "what is", "why does", "how does",
}

_DRILL_ANSWER_NEGATIVE_KEYWORDS = {
    # presence of these words → prompt is asking, not answering
    "뭐야", "어떻게", "왜", "알려줘", "설명해", "차이", "무엇", "what", "why", "how", "explain",
}

_TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣]+")


def _haystack(prompt: str) -> str:
    return (prompt or "").lower()


def _count_substr_hits(haystack: str, tokens: set[str]) -> int:
    return sum(1 for t in tokens if t in haystack)


def _tokenize(prompt: str) -> list[str]:
    return [m.lower() for m in _TOKEN_RE.findall(prompt or "")]


# ---------------------------------------------------------------------------
# Drill-answer heuristic
# ---------------------------------------------------------------------------

def _looks_like_drill_answer(
    prompt: str,
    pending_drill: dict | None,
) -> tuple[bool, dict]:
    """Return (is_answer, signals) based on the 4-condition rule in the plan.

    Conditions (3 of 4 required):
      a. length ≥ 20 chars
      b. no trailing question mark
      c. lacks question-word keywords
      d. token overlap with pending question ≥ threshold
    """
    signals: dict = {
        "length_ok": False,
        "not_question": False,
        "no_question_word": False,
        "token_overlap": 0.0,
        "has_pending": pending_drill is not None,
    }

    if not pending_drill:
        return False, signals

    body = (prompt or "").strip()
    if len(body) >= 20:
        signals["length_ok"] = True
    if not body.endswith("?") and not body.endswith("？"):
        signals["not_question"] = True

    haystack = _haystack(body)
    if not any(kw in haystack for kw in _DRILL_ANSWER_NEGATIVE_KEYWORDS):
        signals["no_question_word"] = True

    pending_question = (pending_drill.get("question") or "") if pending_drill else ""
    prompt_tokens = set(_tokenize(body))
    question_tokens = set(_tokenize(pending_question))
    if question_tokens:
        overlap = len(prompt_tokens & question_tokens) / max(len(question_tokens), 1)
        signals["token_overlap"] = round(overlap, 3)

    satisfied = sum(
        1
        for k in ("length_ok", "not_question", "no_question_word")
        if signals[k]
    )
    if signals["token_overlap"] >= 0.2:
        satisfied += 1

    return satisfied >= 3, signals


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
) -> dict[str, Any]:
    """Lock the final intent_decision + block_plan for this turn."""
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

    return {
        "detected_intent": detected_intent,
        "pre_intent": pre_intent,
        "cs_search_mode": pre_result.get("cs_search_mode"),
        "signals": pre_result.get("signals", {}),
        "block_plan": block_plan,
        "drill_in_turn": {
            "has_offer": drill_offer is not None,
            "has_result": drill_result is not None,
        },
    }
