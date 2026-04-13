"""Pre-rendered Response Contract fragments embedded in coach-run.json.

This module produces the machine-computed pieces of the Response Contract —
snapshot counts and verification (git-show-required) thread lists — so the AI
session can copy them verbatim instead of re-deriving from learner-state.json.

See `docs/agent-operating-contract.md` Response Contract section, and
`/Users/idonghun/.claude/plans/declarative-imagining-ullman.md` Part 2.
"""

from __future__ import annotations

from typing import Any


CLASSIFICATION_BUCKETS = (
    "still-applies",
    "likely-fixed",
    "already-fixed",
    "ambiguous",
    "unread",
)
REPLY_BUCKETS = ("text", "emoji", "none", "unknown")
VERIFICATION_CLASSES = ("likely-fixed", "ambiguous")
# Deterministic sort priority inside verification.thread_refs.
_VERIFICATION_SORT = {"ambiguous": 0, "likely-fixed": 1}

REPLY_LABELS = {
    "text": "텍스트 답글",
    "emoji": "이모지",
    "none": "없음",
    "unknown": "불명",
}


def _classify_reply(thread: dict[str, Any]) -> str:
    for participant in thread.get("participants") or []:
        if participant.get("role") != "self":
            continue
        body = (participant.get("body_excerpt") or "").strip()
        if body:
            return "text"
    if thread.get("learner_reactions"):
        return "emoji"
    if thread.get("learner_acknowledged") == "unknown":
        return "unknown"
    return "none"


def _empty_counts() -> dict[str, Any]:
    return {
        "total": 0,
        "classification": {bucket: 0 for bucket in CLASSIFICATION_BUCKETS},
        "reply_axis": {bucket: 0 for bucket in REPLY_BUCKETS},
    }


def _tally(threads: list[dict[str, Any]]) -> dict[str, Any]:
    counts = _empty_counts()
    for thread in threads:
        classification = thread.get("classification")
        if classification not in counts["classification"]:
            raise ValueError(
                f"unexpected classification {classification!r}; "
                f"expected one of {CLASSIFICATION_BUCKETS}"
            )
        counts["classification"][classification] += 1
        counts["reply_axis"][_classify_reply(thread)] += 1
        counts["total"] += 1

    total = counts["total"]
    if sum(counts["classification"].values()) != total:
        raise ValueError("classification counts do not sum to total")
    if sum(counts["reply_axis"].values()) != total:
        raise ValueError("reply_axis counts do not sum to total")
    return counts


def _render_markdown(
    *,
    head_branch: str,
    target_pr_number: int,
    selection_reason: str,
    computed_at: str,
    counts: dict[str, Any],
) -> str:
    lines = [
        f"## 상태 요약 (snapshot, computed_at={computed_at})",
        f"- 타깃: {head_branch} / PR #{target_pr_number}  ({selection_reason})",
        f"- 스레드 {counts['total']}개:",
    ]
    for bucket in CLASSIFICATION_BUCKETS:
        lines.append(f"  - {bucket}: {counts['classification'][bucket]}")
    lines.append("- 답변 유형:")
    for bucket in REPLY_BUCKETS:
        label = REPLY_LABELS[bucket]
        lines.append(f"  - {label}: {counts['reply_axis'][bucket]}")
    return "\n".join(lines)


def _empty_snapshot_block(snapshot: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "markdown": None,
        "counts": None,
        "computed_at": snapshot.get("computed_at") or "",
        "target_pr_number": snapshot.get("target_pr_number"),
        "target_pr_selection_reason": snapshot.get("target_pr_selection_reason") or "",
        "reason": reason,
    }


def build_snapshot_block(
    snapshot: dict[str, Any],
    execution_status: str,
) -> dict[str, Any]:
    """Produce the ``## 상태 요약`` block from a learner-state snapshot.

    Always returns a dict of the same shape. ``markdown`` and ``counts`` are
    nullable when the snapshot cannot support a real block.
    """
    if execution_status != "ready":
        return _empty_snapshot_block(snapshot, execution_status)

    target_pr_number = snapshot.get("target_pr_number")
    detail = snapshot.get("target_pr_detail") or None
    if target_pr_number is None or detail is None:
        return _empty_snapshot_block(snapshot, "no_target_pr")

    threads = detail.get("threads") or []
    counts = _tally(threads)
    markdown = _render_markdown(
        head_branch=snapshot.get("head_branch") or "",
        target_pr_number=target_pr_number,
        selection_reason=snapshot.get("target_pr_selection_reason") or "",
        computed_at=snapshot.get("computed_at") or "",
        counts=counts,
    )
    return {
        "markdown": markdown,
        "counts": counts,
        "computed_at": snapshot.get("computed_at") or "",
        "target_pr_number": target_pr_number,
        "target_pr_selection_reason": snapshot.get("target_pr_selection_reason") or "",
        "reason": "ready",
    }


def _empty_verification_block() -> dict[str, Any]:
    return {"required_count": 0, "thread_refs": [], "stub_markdown": None}


def _render_stub(thread_refs: list[dict[str, Any]]) -> str:
    lines = ["## 수동 확인 필요"]
    for ref in thread_refs:
        path = ref.get("path") or ""
        line = ref.get("line")
        loc = f"{path}:{line}" if line is not None else path
        classification = ref.get("classification") or ""
        reason = ref.get("classification_reason") or "no_reason"
        lines.append(f"- [{loc}] ({classification}, reason={reason})")
    return "\n".join(lines)


def build_verification_block(
    snapshot: dict[str, Any],
    execution_status: str,
) -> dict[str, Any]:
    """Produce the pre-rendered git-show-required list for the current turn."""
    if execution_status != "ready":
        return _empty_verification_block()

    detail = snapshot.get("target_pr_detail") or None
    if detail is None:
        return _empty_verification_block()

    threads = detail.get("threads") or []
    refs: list[dict[str, Any]] = []
    for thread in threads:
        classification = thread.get("classification")
        if classification not in VERIFICATION_CLASSES:
            continue
        refs.append({
            "thread_id": thread.get("id"),
            "path": thread.get("path") or "",
            "line": thread.get("line"),
            "classification": classification,
            "classification_reason": thread.get("classification_reason"),
        })

    refs.sort(key=lambda r: (
        _VERIFICATION_SORT.get(r["classification"], 99),
        r.get("path") or "",
        r.get("line") if r.get("line") is not None else -1,
    ))

    stub = _render_stub(refs) if refs else None
    return {
        "required_count": len(refs),
        "thread_refs": refs,
        "stub_markdown": stub,
    }


def build_response_contract(
    snapshot: dict[str, Any] | None,
    execution_status: str,
) -> dict[str, Any]:
    """Top-level entry — returns the full ``response_contract`` payload dict.

    ``snapshot`` may be ``None`` when the pipeline failed before learner-state
    was produced; in that case an empty always-present contract is returned so
    downstream schema validation and AI consumers see a uniform shape.
    """
    effective_snapshot = snapshot or {}
    return {
        "snapshot_block": build_snapshot_block(effective_snapshot, execution_status),
        "verification": build_verification_block(effective_snapshot, execution_status),
    }
