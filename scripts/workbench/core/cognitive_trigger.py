"""Central cognitive trigger selection for learning turns.

The selector is intentionally side-effect free. It decides which single
learner-facing cognitive prompt should be surfaced for this turn; callers own
any persistence such as pending trigger files.
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Literal

from .paths import ensure_learner_layout

TriggerType = Literal["self_assessment", "review_drill", "follow_up", "none"]


def _empty_trigger(*, competed_against: list[str] | None = None) -> dict[str, Any]:
    return {
        "trigger_type": "none",
        "trigger_session_id": None,
        "markdown": None,
        "payload": {},
        "applicability_hint": "omit",
        "reason": "none",
        "evidence": {},
        "competed_against": competed_against or [],
    }


def _pending_triggers_path() -> Path:
    return ensure_learner_layout() / "pending_triggers.json"


def load_pending_triggers() -> dict[str, Any]:
    """Read state/learner/pending_triggers.json, returning {} on cold start."""
    path = _pending_triggers_path()
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def write_pending_triggers_atomic(triggers: dict[str, Any]) -> None:
    """Atomically persist pending cognitive triggers."""
    path = _pending_triggers_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    closed = False
    try:
        os.write(fd, (json.dumps(triggers, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        os.fsync(fd)
        os.close(fd)
        closed = True
        os.replace(tmp, path)
    except BaseException:
        if not closed:
            os.close(fd)
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def _parse_iso(value: Any) -> datetime | None:
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


def expire_stale_triggers(
    pending: dict[str, Any],
    now: datetime,
    *,
    ttl_hours: int = 24,
) -> dict[str, Any]:
    """Return pending triggers with stale entries removed."""
    out: dict[str, Any] = {}
    for trigger_type, payload in (pending or {}).items():
        if not isinstance(payload, dict):
            continue
        expires_at = _parse_iso(payload.get("expires_at"))
        issued_at = _parse_iso(payload.get("issued_at"))
        if expires_at is not None:
            if expires_at > now:
                out[trigger_type] = payload
            continue
        if issued_at is not None and issued_at + timedelta(hours=ttl_hours) > now:
            out[trigger_type] = payload
    return out


def match_pending_trigger(
    pending: dict[str, Any],
    trigger_type: str,
    response_payload: dict[str, Any] | None,
) -> str | None:
    """Return the matching trigger_session_id for a response payload."""
    candidate = (pending or {}).get(trigger_type)
    if not isinstance(candidate, dict):
        return None
    trigger_session_id = candidate.get("trigger_session_id")
    if not trigger_session_id:
        return None
    response_id = (response_payload or {}).get("trigger_session_id")
    if response_id and response_id != trigger_session_id:
        return None
    return str(trigger_session_id)


def _follow_up_candidate(
    *,
    profile: dict[str, Any] | None,
    **_: Any,
) -> dict[str, Any] | None:
    queue = (profile or {}).get("open_follow_up_queue") or []
    items = [item for item in queue if isinstance(item, dict) and (item.get("question") or "").strip()]
    if not items:
        return None
    first = items[0]
    question = str(first.get("question") or "").strip()
    markdown = "## 이어서 보면 좋은 질문\n" f"- {question}"
    learning_points = list(first.get("learning_points") or [])
    if learning_points:
        markdown += "\n" f"  - 관련 학습 포인트: {', '.join(str(p) for p in learning_points)}"
    return {
        "trigger_type": "follow_up",
        "trigger_session_id": None,
        "markdown": markdown,
        "payload": {"item": first},
        "applicability_hint": "supporting",
        "reason": "open_follow_up",
        "evidence": {
            "source": "learning_profile.open_follow_up_queue",
            "queue_size": len(items),
        },
        "competed_against": [],
    }


def _disabled_candidate(**_: Any) -> dict[str, Any] | None:
    return None


def _self_assessment_due_candidate(
    *,
    profile: dict[str, Any] | None,
    pending_triggers: dict[str, Any] | None,
    **_: Any,
) -> dict[str, Any] | None:
    if (pending_triggers or {}).get("self_assessment"):
        return None
    recent_changes = list((profile or {}).get("recent_code_changes_24h") or [])
    if not recent_changes:
        return None
    assessed_concepts = {
        concept_id
        for item in ((profile or {}).get("calibration_status") or {}).get(
            "recent_self_assessments",
            [],
        )
        for concept_id in (item.get("concept_ids") or [])
    }
    for change in reversed(recent_changes):
        concept_ids = [
            concept_id
            for concept_id in (change.get("concept_ids") or [])
            if concept_id not in assessed_concepts
        ]
        if concept_ids:
            file_path = change.get("file_path") or "최근 변경"
            return {
                "trigger_type": "self_assessment",
                "trigger_session_id": str(uuid.uuid4()),
                "markdown": (
                    "## 자기 점검\n"
                    f"- 방금 다룬 `{file_path}` 변경 기준으로 이해도를 1-10점으로 적어줘."
                ),
                "payload": {
                    "concept_ids": concept_ids,
                    "source_event_id": change.get("event_id"),
                    "file_path": file_path,
                },
                "applicability_hint": "supporting",
                "reason": "recent_code_attempt_without_self_assessment",
                "evidence": {
                    "source": "learner_profile.recent_code_changes_24h",
                    "code_attempt_ts": change.get("ts"),
                },
                "competed_against": [],
            }
    return None


_CANDIDATE_REGISTRY: dict[str, dict[str, Any]] = {
    "self_assessment_due": {"enabled": True, "fn": _self_assessment_due_candidate},
    "review_due": {"enabled": False, "fn": _disabled_candidate},
    "follow_up": {"enabled": True, "fn": _follow_up_candidate},
}


def select_cognitive_trigger(
    *,
    history: list[dict[str, Any]] | None = None,
    profile: dict[str, Any] | None = None,
    drill_pending: dict[str, Any] | None = None,
    drill_history: list[dict[str, Any]] | None = None,
    intent: dict[str, Any] | None = None,
    learner_context: dict[str, Any] | None = None,
    pending_triggers: dict[str, Any] | None = None,
    input_signals: dict[str, Any] | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Select at most one cognitive trigger for the current turn."""
    del now  # Reserved for due-date candidates enabled in later commits.
    competed_against: list[str] = []
    pre_intent = (intent or {}).get("pre_intent") or (intent or {}).get("detected_intent")
    if drill_pending is not None or pre_intent in {"drill_answer", "mixed_with_drill_answer"}:
        return _empty_trigger(competed_against=competed_against)

    context = {
        "history": history or [],
        "profile": profile,
        "drill_pending": drill_pending,
        "drill_history": drill_history or [],
        "intent": intent or {},
        "learner_context": learner_context,
        "pending_triggers": pending_triggers or {},
        "input_signals": input_signals or {},
    }
    for name in ("self_assessment_due", "review_due", "follow_up"):
        spec = _CANDIDATE_REGISTRY.get(name) or {}
        if not spec.get("enabled"):
            continue
        competed_against.append(name)
        fn: Callable[..., dict[str, Any] | None] = spec["fn"]
        candidate = fn(**context)
        if candidate:
            candidate["competed_against"] = list(competed_against)
            if not candidate.get("trigger_session_id") and candidate.get("trigger_type") in {
                "self_assessment",
                "review_drill",
            }:
                candidate["trigger_session_id"] = str(uuid.uuid4())
            return candidate
    return _empty_trigger(competed_against=competed_against)
