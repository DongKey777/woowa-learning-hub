"""Recent conversational context helpers for RAG query rewriting."""

from __future__ import annotations

from typing import Any, Iterable


def _compact_event(event: dict[str, Any]) -> str | None:
    concept_ids = [str(item) for item in event.get("concept_ids") or [] if item]
    if concept_ids:
        return "concepts=" + ",".join(concept_ids[:3])
    top_paths = [str(item) for item in event.get("top_paths") or [] if item]
    if top_paths:
        return "paths=" + ",".join(top_paths[:2])
    categories = [str(item) for item in event.get("category_hits") or [] if item]
    if categories:
        return "categories=" + ",".join(categories[:3])
    prompt = str(event.get("prompt") or "").strip()
    return prompt[:80] if prompt else None


def recent_rag_ask_context(
    *,
    limit: int = 2,
    history: Iterable[dict[str, Any]] | None = None,
) -> list[str]:
    """Return compact context strings for the latest rag_ask events.

    Tests can pass ``history`` directly. Runtime callers may omit it, in which
    case the learner-memory history reader is imported lazily to avoid adding a
    hard dependency to the RAG module import path.
    """
    if limit <= 0:
        return []
    if history is None:
        try:
            from scripts.workbench.core.learner_memory import _load_history  # noqa: WPS433

            events = _load_history(limit=limit * 6)
        except Exception:
            return []
    else:
        events = list(history)

    out: list[str] = []
    for event in reversed(events):
        if event.get("event_type") != "rag_ask":
            continue
        compact = _compact_event(event)
        if compact is None:
            continue
        out.append(compact)
        if len(out) >= limit:
            break
    return out
