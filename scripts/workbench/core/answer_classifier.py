"""Drill-answer routing heuristic, single-source.

Pre-PR#4, this 4-condition rule lived in two places:

- ``scripts.learning.drill.route_answer`` (live)
- ``scripts.workbench.core.intent_router._looks_like_drill_answer`` (dead)

This module owns the live implementation. ``drill.route_answer`` becomes a
thin wrapper for backward compatibility with external callers.
"""

from __future__ import annotations

import re

from .intent_tokens import DRILL_ANSWER_NEGATIVE_KEYWORDS

_TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣_]+")


def tokenize(text: str) -> list[str]:
    return [m.lower() for m in _TOKEN_RE.findall(text or "")]


def is_question_like(text: str) -> bool:
    """Return True when ``text`` reads as a fresh question, not an answer."""
    body = (text or "").strip()
    if body.endswith("?") or body.endswith("？"):
        return True
    lower = body.lower()
    return any(kw in lower for kw in DRILL_ANSWER_NEGATIVE_KEYWORDS)


def classify_drill_answer(
    prompt: str,
    pending: dict | None,
) -> tuple[bool, dict]:
    """Decide whether ``prompt`` is an answer to ``pending``.

    Returns ``(is_answer, signals)``. 3 of 4 conditions required:

    a. length ≥ 20 chars
    b. no trailing ? / ？
    c. lacks question-word keywords
    d. token overlap with pending question ≥ 0.2
    """
    signals: dict = {
        "length_ok": False,
        "not_question": False,
        "no_question_word": False,
        "token_overlap": 0.0,
        "has_pending": pending is not None,
    }
    if not pending:
        return False, signals

    body = (prompt or "").strip()
    if len(body) >= 20:
        signals["length_ok"] = True
    if not body.endswith("?") and not body.endswith("？"):
        signals["not_question"] = True
    lower = body.lower()
    if not any(kw in lower for kw in DRILL_ANSWER_NEGATIVE_KEYWORDS):
        signals["no_question_word"] = True

    question_tokens = set(tokenize(pending.get("question") or ""))
    prompt_tokens = set(tokenize(body))
    if question_tokens:
        overlap = len(prompt_tokens & question_tokens) / max(len(question_tokens), 1)
        signals["token_overlap"] = round(overlap, 3)

    satisfied = sum(
        1 for k in ("length_ok", "not_question", "no_question_word") if signals[k]
    )
    if signals["token_overlap"] >= 0.2:
        satisfied += 1
    return satisfied >= 3, signals


def classify_self_assessment_response(
    prompt: str,
    pending_trigger: dict | None,
) -> tuple[bool, dict]:
    """Detect a self-assessment score response for a pending trigger."""
    try:
        from scripts.learning.self_assessment import parse_response  # noqa: WPS433
    except Exception:
        return False, {"has_pending": pending_trigger is not None, "parse_error": True}
    parsed = parse_response(prompt, pending_trigger)
    if parsed is None:
        return False, {"has_pending": pending_trigger is not None, "score": None}
    return True, {
        "has_pending": True,
        "score": parsed.get("score"),
        "concept_ids": parsed.get("concept_ids") or [],
        "trigger_session_id": parsed.get("trigger_session_id"),
        "free_text": parsed.get("free_text"),
    }
