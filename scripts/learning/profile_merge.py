"""Unify the coach profile and the CS (drill) view into one projection.

**Source-of-truth rule** (Phase 3.2 in the plan):

- ``state/repos/<repo>/memory/profile.json`` is the persisted truth.
- ``coach-run.json.unified_profile`` is a per-turn compact projection
  derived here. It can always be rebuilt from profile.json + a
  drill-history window, so treat it as a cache, not a store.

The reconciled section cross-cuts the two views to surface learning
points that need attention *from both angles* at once.

Pure stdlib.
"""

from __future__ import annotations

from typing import Any

DIMENSION_TO_TAG = {
    "accuracy": "정확도",
    "depth": "깊이",
    "practicality": "실전성",
    "completeness": "완결성",
}

# Drill-history window for computing cs_view. Tune later; Phase 3 default
# matches the plan's "recent N" guidance.
DEFAULT_DRILL_WINDOW = 5


def _drill_window(drill_history: list[dict], window: int) -> list[dict]:
    if not drill_history:
        return []
    return list(drill_history[-window:])


def compute_cs_view(
    drill_history: list[dict] | None,
    *,
    window: int = DEFAULT_DRILL_WINDOW,
) -> dict[str, Any] | None:
    """Aggregate recent drill results into a cs_view. None when empty.

    Not a persistence step — the caller decides whether to write this
    back to profile.json.
    """
    history = _drill_window(drill_history or [], window)
    if not history:
        return None

    totals = [entry.get("total_score") for entry in history if isinstance(entry.get("total_score"), (int, float))]
    if not totals:
        return None
    avg = round(sum(totals) / len(totals), 2)

    dim_sums: dict[str, float] = {}
    dim_counts: dict[str, int] = {}
    for entry in history:
        dims = entry.get("dimensions") or {}
        for k, v in dims.items():
            if isinstance(v, (int, float)):
                dim_sums[k] = dim_sums.get(k, 0.0) + float(v)
                dim_counts[k] = dim_counts.get(k, 0) + 1

    weak_dims: list[str] = []
    for dim in ("accuracy", "depth", "practicality", "completeness"):
        count = dim_counts.get(dim, 0)
        if count == 0:
            continue
        avg_dim = dim_sums[dim] / count
        # Below 60% of dimension ceiling (accuracy=4/depth=3/prac=2/comp=1).
        ceiling = {"accuracy": 4, "depth": 3, "practicality": 2, "completeness": 1}[dim]
        if avg_dim < ceiling * 0.6:
            weak_dims.append(dim)

    weak_tags: list[str] = []
    for entry in history:
        for tag in entry.get("weak_tags") or []:
            if tag not in weak_tags:
                weak_tags.append(tag)

    low_categories: list[str] = []
    seen_cat: set[str] = set()
    for entry in history:
        total = entry.get("total_score")
        cat = (entry.get("source_doc") or {}).get("category")
        if cat and cat not in seen_cat and isinstance(total, (int, float)) and total < 6:
            seen_cat.add(cat)
            low_categories.append(cat)

    return {
        "avg_score": avg,
        "level": _level_for(avg),
        "weak_dimensions": weak_dims,
        "weak_tags": weak_tags,
        "low_categories": low_categories,
        "recent_drills": [
            {
                "scored_at": entry.get("scored_at"),
                "total_score": entry.get("total_score"),
                "level": entry.get("level"),
                "weak_tags": entry.get("weak_tags") or [],
                "linked_learning_point": entry.get("linked_learning_point"),
            }
            for entry in history
        ],
    }


def _level_for(avg: float) -> str:
    if avg >= 9:
        return "L5"
    if avg >= 7:
        return "L4"
    if avg >= 5:
        return "L3"
    if avg >= 3:
        return "L2"
    return "L1"


def _coach_view(coach_profile: dict[str, Any]) -> dict[str, Any]:
    recency_by_point: dict[str, str] = {}

    def _names(entries: list[dict]) -> list[str]:
        out: list[str] = []
        for e in entries or []:
            if isinstance(e, dict):
                label = e.get("label") or e.get("learning_point")
                if label:
                    out.append(label)
                    status = e.get("recency_status")
                    if status and label not in recency_by_point:
                        recency_by_point[label] = status
            elif isinstance(e, str):
                out.append(e)
        return out

    dominant = _names(coach_profile.get("dominant_learning_points") or [])
    repeated = _names(coach_profile.get("repeated_learning_points") or [])
    underexplored = _names(coach_profile.get("underexplored_learning_points") or [])

    return {
        "dominant_points": dominant,
        "repeated_points": repeated,
        "underexplored_points": underexplored,
        "confidence": coach_profile.get("confidence"),
        "recency_by_point": recency_by_point,
    }


def _reconcile(coach_view: dict[str, Any], cs_view: dict[str, Any] | None) -> dict[str, Any]:
    dominant = set(coach_view.get("dominant_points") or [])
    repeated = set(coach_view.get("repeated_points") or [])
    underexplored = set(coach_view.get("underexplored_points") or [])

    cs_weak_tags = set((cs_view or {}).get("weak_tags") or [])
    cs_low_categories = set((cs_view or {}).get("low_categories") or [])

    # Priority focus: coach 반복 약점과 CS 쪽에서도 약한 축이 겹치는 지점.
    # coach 쪽은 learning-point 이름, CS 쪽은 dimension tag이므로 단순
    # 교집합 대신 "양쪽에 공통된 주제 카테고리 키워드" 기준으로 정리.
    priority_focus = sorted(repeated & dominant)

    empirical_only = sorted(repeated - set(cs_low_categories))
    theoretical_only = sorted(cs_weak_tags - (repeated | dominant))

    return {
        "priority_focus": priority_focus,
        "empirical_only_gaps": empirical_only[:5],
        "theoretical_only_gaps": theoretical_only[:5],
    }


def unify(
    coach_profile: dict[str, Any] | None,
    *,
    drill_history: list[dict] | None = None,
    cs_view: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Produce the per-turn unified_profile projection.

    Either ``cs_view`` is supplied directly (when caller already has one
    on hand) or it is computed from ``drill_history``. Empty drill
    history → cs_view is None.
    """
    coach_profile = coach_profile or {}
    coach_view = _coach_view(coach_profile)
    if cs_view is None:
        cs_view = compute_cs_view(drill_history)
    reconciled = _reconcile(coach_view, cs_view)
    return {
        "coach_view": coach_view,
        "cs_view": cs_view,
        "reconciled": reconciled,
    }
