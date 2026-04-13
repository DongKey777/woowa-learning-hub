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


APPLICABILITY_HINTS = ("primary", "supporting", "omit")


def _hint_from_plan(block_plan: dict[str, Any] | None, key: str, default: str) -> str:
    if not block_plan:
        return default
    value = block_plan.get(key)
    if value in APPLICABILITY_HINTS:
        return value
    return default


def _iter_cs_hits(augment_result: dict[str, Any]):
    """Yield (bucket_key, hit) pairs for cs_block rendering.

    by_fallback_key is preferred when ``fallback_reason`` is set; by_learning_point
    is preferred otherwise. Both may appear when ``fallback_reason='partial_coverage'``.
    """
    fallback_reason = augment_result.get("fallback_reason")
    by_lp = augment_result.get("by_learning_point") or {}
    by_fb = augment_result.get("by_fallback_key") or {}

    if fallback_reason and by_fb:
        for key, hits in by_fb.items():
            for hit in hits:
                yield key, hit
        if fallback_reason == "partial_coverage":
            for key, hits in by_lp.items():
                for hit in hits:
                    yield key, hit
        return

    for key, hits in by_lp.items():
        for hit in hits:
            yield key, hit
    for key, hits in by_fb.items():
        for hit in hits:
            yield key, hit


def build_cs_block(
    augment_result: dict[str, Any] | None,
    *,
    applicability_hint: str = "omit",
) -> dict[str, Any]:
    """Render a cs_block as a **view** of cs_augmentation.

    cs_augmentation is the source of truth; this block is rebuildable from it.
    ``reason`` tracks whether we have hits, no hits, or a degrade.
    """
    if not augment_result:
        return {
            "markdown": None,
            "sources": [],
            "reason": "no_augmentation",
            "applicability_hint": applicability_hint,
        }

    meta = augment_result.get("meta") or {}
    mode_used = meta.get("mode_used")
    if mode_used == "skip":
        return {
            "markdown": None,
            "sources": [],
            "reason": "rag_skip",
            "applicability_hint": applicability_hint,
        }
    if not meta.get("rag_ready", False):
        return {
            "markdown": None,
            "sources": [],
            "reason": meta.get("reason") or "rag_not_ready",
            "applicability_hint": applicability_hint,
        }

    pairs = list(_iter_cs_hits(augment_result))
    if not pairs:
        return {
            "markdown": None,
            "sources": [],
            "reason": "no_hits",
            "applicability_hint": applicability_hint,
        }

    lines = ["## 이번 질문의 CS 근거"]
    sources: list[dict[str, Any]] = []
    for bucket_key, hit in pairs:
        category = hit.get("category") or "general"
        path = hit.get("path") or ""
        section = hit.get("section_title") or ""
        snippet = (hit.get("snippet_preview") or "").strip()
        header = f"- [{category}] {path}"
        if section:
            header += f" — {section}"
        lines.append(header)
        if snippet:
            lines.append(f"  {snippet}")
        sources.append({
            "bucket": bucket_key,
            "path": path,
            "category": category,
            "section_title": section or None,
            "score": hit.get("score"),
        })

    return {
        "markdown": "\n".join(lines),
        "sources": sources,
        "reason": "ready",
        "applicability_hint": applicability_hint,
    }


def build_drill_block(
    drill_offer: dict[str, Any] | None,
    drill_result: dict[str, Any] | None,
    *,
    applicability_hint: str = "omit",
) -> dict[str, Any]:
    """Drill offer block. Phase 4 replaces the body; Phase 2 ships a stub."""
    if drill_offer:
        question = drill_offer.get("question") or ""
        markdown = (
            "## 확인 질문 (선택)\n"
            f"{question}\n\n"
            "(원한다면 다음 턴에 답변해 줘. 약점 축을 다듬을 수 있어.)"
        )
        return {
            "markdown": markdown,
            "reason": "new_offer",
            "applicability_hint": applicability_hint,
        }
    if drill_result is not None:
        return {
            "markdown": None,
            "reason": "result_from_previous",
            "applicability_hint": applicability_hint,
        }
    return {
        "markdown": None,
        "reason": "none",
        "applicability_hint": applicability_hint,
    }


def build_drill_result_block(
    drill_result: dict[str, Any] | None,
    *,
    applicability_hint: str = "omit",
) -> dict[str, Any]:
    """Drill answer scoring block. Phase 4 fills in real scoring."""
    if not drill_result:
        return {
            "markdown": None,
            "reason": "none",
            "applicability_hint": applicability_hint,
        }
    total = drill_result.get("total_score")
    level = drill_result.get("level")
    weak = ", ".join(drill_result.get("weak_tags") or []) or "-"
    markdown = (
        "## 지난 확인 질문 채점\n"
        f"- 점수: {total}/10 ({level})\n"
        f"- 약점: {weak}"
    )
    return {
        "markdown": markdown,
        "reason": "scored",
        "applicability_hint": applicability_hint,
    }


def build_response_contract(
    snapshot: dict[str, Any] | None,
    execution_status: str,
    *,
    augment_result: dict[str, Any] | None = None,
    intent_decision: dict[str, Any] | None = None,
    drill_offer: dict[str, Any] | None = None,
    drill_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Top-level entry — returns the full ``response_contract`` payload dict.

    ``snapshot`` may be ``None`` when the pipeline failed before learner-state
    was produced; in that case an empty always-present contract is returned so
    downstream schema validation and AI consumers see a uniform shape.

    ``augment_result`` + ``intent_decision`` feed the CS/drill blocks. Both are
    optional for backward compatibility with peer-only code paths.
    """
    effective_snapshot = snapshot or {}
    block_plan = (intent_decision or {}).get("block_plan") or {}

    snapshot_block = build_snapshot_block(effective_snapshot, execution_status)
    verification = build_verification_block(effective_snapshot, execution_status)

    cs_block = build_cs_block(
        augment_result,
        applicability_hint=_hint_from_plan(block_plan, "cs_block", "omit"),
    )
    drill_block = build_drill_block(
        drill_offer,
        drill_result,
        applicability_hint=_hint_from_plan(block_plan, "drill_block", "omit"),
    )
    drill_result_block = build_drill_result_block(
        drill_result,
        applicability_hint=_hint_from_plan(block_plan, "drill_block", "omit"),
    )

    return {
        "snapshot_block": snapshot_block,
        "verification": verification,
        "cs_block": cs_block,
        "drill_block": drill_block,
        "drill_result_block": drill_result_block,
    }
