"""Top-level coach-run.json size budget enforcement.

Plan §"Artifact Size Budget": top-level compact payload must stay under
~182KB (current ~140KB × 1.3). When it exceeds the cap, shrink in this
fixed order:

1. cs_augmentation bucket snippet previews → truncated to 150 chars.
2. memory.drill_history details → keep only last 3 entries (total_score,
   level, weak_tags only).
3. cs_augmentation.by_fallback_key top-K 5 → 3.
4. unified_profile.reconciled.{priority_focus, empirical_only_gaps,
   theoretical_only_gaps} → top 5.

Never shrink: response_contract.cs_block.markdown, snapshot_block.markdown,
drill_block.markdown, intent_decision, cs_readiness, execution_status.
These are load-bearing for rendering and shrinking them forces sidecar
re-reads that cost more tokens than they save.
"""

from __future__ import annotations

import copy
import json
from typing import Any

DEFAULT_MAX_BYTES = 182_000


def measure_bytes(payload: dict) -> int:
    return len(json.dumps(payload, ensure_ascii=False).encode("utf-8"))


def _shrink_snippets(payload: dict) -> bool:
    aug = payload.get("cs_augmentation") or {}
    changed = False
    for key in ("by_learning_point", "by_fallback_key"):
        bucket = aug.get(key) or {}
        for hits in bucket.values():
            if not isinstance(hits, list):
                continue
            for hit in hits:
                preview = hit.get("snippet_preview")
                if isinstance(preview, str) and len(preview) > 150:
                    hit["snippet_preview"] = preview[:150]
                    changed = True
    return changed


def _shrink_drill_history(payload: dict) -> bool:
    memory = payload.get("memory") or {}
    profile = memory.get("profile") or {}
    history = profile.get("drill_history")
    if not isinstance(history, list) or len(history) <= 3:
        return False
    profile["drill_history"] = [
        {
            "total_score": entry.get("total_score"),
            "level": entry.get("level"),
            "weak_tags": entry.get("weak_tags") or [],
        }
        for entry in history[-3:]
    ]
    return True


def _shrink_fallback_topk(payload: dict, new_k: int = 3) -> bool:
    aug = payload.get("cs_augmentation") or {}
    fallback = aug.get("by_fallback_key") or {}
    changed = False
    for key, hits in fallback.items():
        if isinstance(hits, list) and len(hits) > new_k:
            fallback[key] = hits[:new_k]
            changed = True
    return changed


def _shrink_reconciled_lists(payload: dict, top_n: int = 5) -> bool:
    unified = payload.get("unified_profile") or {}
    reconciled = unified.get("reconciled") or {}
    changed = False
    for key in ("priority_focus", "empirical_only_gaps", "theoretical_only_gaps"):
        lst = reconciled.get(key)
        if isinstance(lst, list) and len(lst) > top_n:
            reconciled[key] = lst[:top_n]
            changed = True
    return changed


SHRINK_LADDER = (
    _shrink_snippets,
    _shrink_drill_history,
    _shrink_fallback_topk,
    _shrink_reconciled_lists,
)


def enforce_budget(payload: dict, max_bytes: int = DEFAULT_MAX_BYTES) -> dict:
    """Return a copy of ``payload`` shrunk until it fits ``max_bytes``.

    Mutates a deep copy — the caller's payload is untouched. If every
    ladder step runs and the payload still exceeds ``max_bytes``, the
    last-shrunk copy is returned anyway (upstream logs the overflow;
    never silently drop load-bearing fields).
    """
    out = copy.deepcopy(payload)
    if measure_bytes(out) <= max_bytes:
        return out
    for step in SHRINK_LADDER:
        step(out)
        if measure_bytes(out) <= max_bytes:
            return out
    return out
