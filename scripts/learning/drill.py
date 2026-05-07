"""Drill-question engine: offer, route, score, persist.

Lifecycle (one pending at a time):
1. ``build_offer_if_due(unified_profile, ...)`` decides whether this turn
   should propose a new drill question.
2. If yes, coach_run persists the offer via ``save_pending()``. The file
   lives at ``state/repos/<repo>/memory/drill-pending.json`` and is
   **absent** whenever there is no open drill.
3. On the next turn, coach_run calls ``load_pending()`` + ``decrement_ttl()``
   and passes the result into the learning pipeline. ``route_answer()``
   decides whether the learner's prompt is an answer or a fresh question.
4. If it is an answer, ``score_pending_answer()`` calls
   ``learning.scoring.score_answer`` and returns a drill_result dict;
   coach_run appends it to ``memory/drill-history.jsonl`` and calls
   ``clear_pending()``.
5. A fresh turn that is **not** an answer leaves the pending file alone
   until TTL hits zero.

All file I/O is local to this module so coach_run only has to call the
top-level helpers — no direct path math. Pure stdlib.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from scripts.workbench.core.answer_classifier import classify_drill_answer
from scripts.workbench.core.paths import repo_memory_dir

from . import scoring

# --- state ------------------------------------------------------------------

DEFAULT_TTL_TURNS = 3
# The plan originally proposed a 3-turn cooldown between offers. Coach_run
# does not track turn indices, so the effective rule is: one drill pending
# at a time — a new offer cannot be generated while drill-pending.json is
# live (either unanswered or still inside TTL). This is enforced in
# build_offer_if_due via the ``pending`` argument.

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _pending_path(repo_name: str) -> Path:
    return repo_memory_dir(repo_name) / "drill-pending.json"


def _history_path(repo_name: str) -> Path:
    return repo_memory_dir(repo_name) / "drill-history.jsonl"


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        text = str(value)
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _spaced_repetition_bands() -> list[int]:
    raw = os.environ.get("WOOWA_SPACED_REPETITION_BANDS", "3,7,14")
    bands: list[int] = []
    for chunk in raw.split(","):
        try:
            days = int(chunk.strip())
        except ValueError:
            return [3, 7, 14]
        if days <= 0:
            return [3, 7, 14]
        bands.append(days)
    return bands or [3, 7, 14]


def _compute_due_at(scored_at: str | None = None, *, review_count: int = 0) -> str:
    bands = _spaced_repetition_bands()
    band_index = max(0, min(review_count, len(bands) - 1))
    base = _parse_timestamp(scored_at) or datetime.now(timezone.utc)
    return (base + timedelta(days=bands[band_index])).isoformat()


# ---------------------------------------------------------------------------
# Pending persistence
# ---------------------------------------------------------------------------

def load_pending(repo_name: str) -> dict | None:
    path = _pending_path(repo_name)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def save_pending(repo_name: str, offer: dict) -> Path:
    path = _pending_path(repo_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(offer, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def clear_pending(repo_name: str) -> None:
    path = _pending_path(repo_name)
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def decrement_ttl(pending: dict | None) -> dict | None:
    """Return pending with ttl_turns-1 applied. None if TTL would expire."""
    if not pending:
        return None
    ttl = int(pending.get("ttl_turns", 0)) - 1
    if ttl < 0:
        return None
    out = dict(pending)
    out["ttl_turns"] = ttl
    return out


# ---------------------------------------------------------------------------
# Answer routing (4-condition) — delegates to answer_classifier so the rule
# stays single-source. Kept as a thin wrapper because external callers
# (coach_run, tests, docs) reference ``drill.route_answer``.
# ---------------------------------------------------------------------------

def route_answer(prompt: str, pending: dict | None) -> tuple[bool, dict]:
    return classify_drill_answer(prompt, pending)


# ---------------------------------------------------------------------------
# Scoring a pending answer
# ---------------------------------------------------------------------------

def score_pending_answer(prompt: str, pending: dict) -> dict:
    """Score ``prompt`` as an answer to ``pending``. Returns drill_result dict."""
    expected_terms = pending.get("expected_terms") or []
    source_doc = pending.get("source_doc")
    category = (source_doc or {}).get("category") if source_doc else None
    scored = scoring.score_answer(
        question=pending.get("question") or "",
        answer=prompt or "",
        category=category,
        expected_terms=list(expected_terms),
    )
    scored_at = _timestamp()
    try:
        review_count = max(0, int(pending.get("review_count") or 0))
    except (TypeError, ValueError):
        review_count = 0
    review_of_session_id = pending.get("review_of_session_id") or pending.get("drill_session_id")
    return {
        "drill_session_id": pending.get("drill_session_id"),
        "scored_at": scored_at,
        "linked_learning_point": pending.get("linked_learning_point"),
        "question": pending.get("question"),
        "answer": prompt,
        "total_score": scored["total_score"],
        "level": scored["level"],
        "dimensions": scored["dimensions"],
        "weak_tags": scored["weak_tags"],
        "improvement_notes": scored["improvement_notes"],
        "source_doc": source_doc,
        "due_at": _compute_due_at(scored_at, review_count=review_count),
        "review_of_session_id": review_of_session_id,
        "review_count": review_count,
        "last_outcome": scored["level"],
    }


def append_history(repo_name: str, drill_result: dict) -> Path:
    path = _history_path(repo_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(drill_result, ensure_ascii=False) + "\n")
    # Learner stream hook (v3): single sink for drill answers, so this
    # function carries the cross-repo `drill_answer` event too. Failure
    # is swallowed — the per-repo drill history already holds the truth.
    try:
        from scripts.workbench.core.learner_memory import (  # type: ignore
            _resolve_learner_id,
            append_learner_event,
            build_drill_answer_event,
        )
        from scripts.workbench.core.concept_catalog import load_catalog  # type: ignore
        event = build_drill_answer_event(
            drill_record=drill_result,
            learner_id=_resolve_learner_id(),
            repo=repo_name,
            catalog=load_catalog(),
        )
        append_learner_event(event)
    except Exception:
        pass
    return path


def load_history(repo_name: str, *, limit: int | None = None) -> list[dict]:
    path = _history_path(repo_name)
    if not path.exists():
        return []
    out: list[dict] = []
    try:
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    if limit is not None and limit > 0:
        return out[-limit:]
    return out


# ---------------------------------------------------------------------------
# Offer generation
# ---------------------------------------------------------------------------

_DRILL_TEMPLATES_BY_CATEGORY = {
    "database": "데이터베이스 관점에서 {focus}의 경계와 트랜잭션 책임이 왜 그렇게 나뉘는지 설명해 보세요.",
    "network": "네트워크 관점에서 {focus}가 장애·지연·재시도에 어떻게 반응해야 하는지 설명해 보세요.",
    "security": "보안 관점에서 {focus}가 인증/무결성을 어떻게 보장하는지 설명해 보세요.",
    "design-pattern": "설계 관점에서 {focus} 경계를 긋는 이유와 trade-off를 설명해 보세요.",
    "software-engineering": "{focus} 관점에서 책임 분리와 테스트 전략이 왜 그렇게 되어야 하는지 설명해 보세요.",
}

_DEFAULT_TEMPLATE = "{focus}의 핵심 원리와 실제 적용 상황을 한 번 설명해 보세요."


_RECENCY_RANK = {"active": 0, "cooling": 1, "dormant": 2}


def _pick_by_recency(items: list[str], recency_by_point: dict[str, str]) -> str:
    """Stable tiebreak: active > cooling > dormant, else first item.

    List order is preserved when recency info is absent so callers without a
    unified_profile still see the same deterministic first element.
    """
    if not recency_by_point:
        return items[0]
    ranked = sorted(
        enumerate(items),
        key=lambda pair: (
            _RECENCY_RANK.get(recency_by_point.get(pair[1], ""), 3),
            pair[0],
        ),
    )
    return ranked[0][1]


def _pick_focus(unified_profile: dict | None) -> str | None:
    if not unified_profile:
        return None
    coach_view = unified_profile.get("coach_view") or {}
    recency_by_point = coach_view.get("recency_by_point") or {}
    reconciled = unified_profile.get("reconciled") or {}
    for key in ("priority_focus", "empirical_only_gaps", "theoretical_only_gaps"):
        items = reconciled.get(key) or []
        if items:
            return _pick_by_recency(items, recency_by_point)
    for key in ("repeated_points", "dominant_points", "underexplored_points"):
        items = coach_view.get(key) or []
        if items:
            return _pick_by_recency(items, recency_by_point)
    return None


def _pick_category_for_focus(focus: str) -> str | None:
    try:
        from .rag.category_mapping import categories_for  # noqa: WPS433
    except Exception:
        return None
    cats = categories_for(focus)
    return cats[0] if cats else None


def build_offer_if_due(
    unified_profile: dict | None,
    *,
    pre_intent: str | None,
    pending: dict | None,
    drill_history: list[dict] | None = None,
    session_payload: dict | None = None,
) -> dict | None:
    """Return a new drill offer or None.

    Refuses to offer when:
    - a pending drill is still open (one at a time)
    - the current turn is a drill-answer turn (to avoid stale profile
      feedback loops — see plan 4차 리뷰 Finding 2)
    - there is no priority_focus to anchor on
    """
    if pending is not None:
        return None
    if pre_intent in {"drill_answer", "mixed_with_drill_answer"}:
        return None

    focus = _pick_focus(unified_profile)
    if not focus:
        return None

    category = _pick_category_for_focus(focus)
    template = _DRILL_TEMPLATES_BY_CATEGORY.get(category or "", _DEFAULT_TEMPLATE)
    question = template.format(focus=focus)

    expected_terms: list[str] = []
    if (session_payload or {}).get("primary_topic"):
        expected_terms.append(session_payload["primary_topic"])

    # Pull the learner's active weak_tags from cs_view so the next scoring
    # pass can actually measure whether the recent gap was closed. Without
    # this, expected_terms only echoes primary_topic and the feedback loop
    # from drill scoring → next drill is blind to the previous weak axes.
    cs_view = (unified_profile or {}).get("cs_view") or {}
    for tag in cs_view.get("weak_tags") or []:
        if tag and tag not in expected_terms:
            expected_terms.append(tag)

    return {
        "drill_session_id": f"drill-{uuid.uuid4().hex[:12]}",
        "question": question,
        "linked_learning_point": focus,
        "source_doc": {"category": category} if category else None,
        "expected_terms": expected_terms,
        "created_at": _timestamp(),
        "ttl_turns": DEFAULT_TTL_TURNS,
    }


def build_review_offer_if_due(
    drill_history: list[dict] | None,
    *,
    pending: dict | None = None,
    now: datetime | None = None,
) -> dict | None:
    """Return a spaced-repetition review offer when a prior drill is due."""
    if pending is not None:
        return None
    reference = now or datetime.now(timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)

    due_items: list[tuple[datetime, int, dict]] = []
    for index, entry in enumerate(drill_history or []):
        if not isinstance(entry, dict):
            continue
        question = (entry.get("question") or "").strip()
        due_at = _parse_timestamp(entry.get("due_at"))
        if not question or due_at is None or due_at > reference:
            continue
        due_items.append((due_at, index, entry))
    if not due_items:
        return None

    _, _, entry = sorted(due_items, key=lambda item: (item[0], item[1]))[0]
    try:
        previous_review_count = max(0, int(entry.get("review_count") or 0))
    except (TypeError, ValueError):
        previous_review_count = 0
    review_of_session_id = entry.get("review_of_session_id") or entry.get("drill_session_id")
    return {
        "drill_session_id": f"drill-{uuid.uuid4().hex[:12]}",
        "question": entry.get("question"),
        "linked_learning_point": entry.get("linked_learning_point"),
        "source_doc": entry.get("source_doc"),
        "expected_terms": list(entry.get("weak_tags") or []),
        "created_at": _timestamp(),
        "ttl_turns": DEFAULT_TTL_TURNS,
        "review_of_session_id": review_of_session_id,
        "review_count": previous_review_count + 1,
        "review_due_at": entry.get("due_at"),
    }
