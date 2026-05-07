"""Self-assessment response parser.

MVP rule: a score-like learner message is treated as self-assessment only
when there is an outstanding self_assessment pending trigger. Random "8점"
messages outside that flow are ignored.
"""

from __future__ import annotations

import re
from typing import Any

_SCORE_RE = re.compile(r"(?<!\d)(10|[1-9])\s*(?:점|/10|out\s+of\s+10)?(?!\d)", re.IGNORECASE)


def _concept_ids_from_pending(pending_trigger: dict[str, Any]) -> list[str]:
    payload = pending_trigger.get("payload") if isinstance(pending_trigger, dict) else {}
    raw = (
        pending_trigger.get("concept_ids")
        or (payload or {}).get("concept_ids")
        or (payload or {}).get("concept_id")
        or []
    )
    if isinstance(raw, str):
        return [raw]
    return [str(item) for item in raw if item]


def parse_response(
    prompt: str,
    pending_trigger: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """Parse a score response only when a pending trigger exists."""
    if not pending_trigger:
        return None
    match = _SCORE_RE.search(prompt or "")
    if not match:
        return None
    score = int(match.group(1))
    trigger_session_id = pending_trigger.get("trigger_session_id")
    if not trigger_session_id:
        return None
    return {
        "score": score,
        "free_text": (prompt or "").strip(),
        "concept_ids": _concept_ids_from_pending(pending_trigger),
        "trigger_session_id": str(trigger_session_id),
    }


def route_response(
    prompt: str,
    learner_context: dict[str, Any] | None,
    pending_triggers: dict[str, Any] | None,
) -> bool:
    """Return True when prompt is a pending self-assessment response."""
    del learner_context  # Reserved for later personalization-sensitive routing.
    pending = (pending_triggers or {}).get("self_assessment")
    return parse_response(prompt, pending) is not None

