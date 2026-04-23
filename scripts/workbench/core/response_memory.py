"""Memory and context preprocessing helpers extracted from response.py."""

from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str | None) -> dict | None:
    if not path:
        return None
    json_path = Path(path)
    if not json_path.exists():
        return None
    try:
        return json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _packet_payloads(context: dict) -> dict:
    packets = {}
    for key in ["pr_report", "reviewer_packet", "topic_packet", "focus_ranking", "candidate_interpretation"]:
        payload = _load_json(context.get(f"{key}_json_path"))
        if payload is None and context.get(f"{key}_evidence") is not None:
            payload = {"evidence": context.get(f"{key}_evidence")}
        if payload is None and context.get(key) is not None:
            payload = context.get(key)
        packets[key] = payload or {}
    return packets


def _learning_memory_profile(context: dict) -> dict:
    return context.get("learning_memory_profile") or {}


def _learning_memory_summary(context: dict) -> dict:
    return context.get("learning_memory_summary") or {}


def _infer_question_focus(context: dict) -> dict:
    prompt = (context.get("prompt") or "").lower()
    intent = context.get("primary_intent") or ""

    focus_rules = [
        ("response", ["답변", "reply", "response", "뭐라고", "어떻게 답"]),
        ("application", ["내 코드", "어디", "어떻게 적용", "어떻게 바꿔", "어디부터", "수정", "반영"]),
        ("reviewer", ["리뷰어", "리뷰", "코멘트", "왜 달렸", "관점"]),
        ("example", ["다른 크루", "사례", "예시", "비교", "패턴", "어떻게 했"]),
        ("lesson", ["왜", "무슨 뜻", "설명", "개념", "차이", "원리", "관점"]),
    ]

    for focus, keywords in focus_rules:
        if any(keyword in prompt for keyword in keywords):
            return {"focus": focus, "reason": f"prompt:{focus}"}

    fallback = {
        "concept_explanation": "lesson",
        "peer_comparison": "example",
        "reviewer_lens": "reviewer",
        "implementation_planning": "application",
        "testing_strategy": "application",
        "review_triage": "reviewer",
        "pr_response": "response",
    }
    return {"focus": fallback.get(intent, "lesson"), "reason": f"intent:{intent}"}


def _memory_policy(context: dict, packets: dict) -> dict:
    profile = _learning_memory_profile(context)
    confidence = profile.get("confidence", "low")
    if confidence == "low":
        return {
            "mode": "neutral",
            "reason": "memory confidence is low, so current question and current evidence should dominate",
        }

    streak = profile.get("recent_learning_streak") or {}
    if (streak.get("count") or 0) >= 3:
        return {
            "mode": "broaden",
            "reason": f"recent learning streak on {streak.get('learning_point')} suggests broadening into a less explored point",
        }

    dormant_points = {
        item.get("learning_point")
        for item in profile.get("dominant_learning_points", [])
        if item.get("recency_status") == "dormant" and item.get("confidence") in {"medium", "high"}
    }
    if dormant_points:
        return {
            "mode": "broaden",
            "reason": f"dominant points {', '.join(sorted(dormant_points))} are dormant — broadening to refresh or explore new areas",
        }

    active_repeated = {
        item.get("learning_point")
        for item in profile.get("repeated_learning_points", [])
        if item.get("confidence") in {"medium", "high"} and item.get("recency_status") in {"active", "cooling"}
    }
    interpretation = packets.get("candidate_interpretation", {})
    if any(item.get("learning_point") in active_repeated for item in interpretation.get("learning_point_recommendations", [])):
        return {
            "mode": "deepen",
            "reason": "current recommendations overlap with actively repeated learning points",
        }

    return {
        "mode": "neutral",
        "reason": "no strong memory signal suggests explicit deepen or broaden policy",
    }


def _join_states(states: dict) -> str:
    if not states:
        return "state 없음"
    ordered = sorted(states.items(), key=lambda item: item[0])
    return ", ".join(f"{name}={count}" for name, count in ordered)
