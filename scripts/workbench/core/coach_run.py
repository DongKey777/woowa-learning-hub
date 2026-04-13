from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .archive import compute_archive_status, ensure_repo_archive, write_archive_status
from .artifact_budget import enforce_budget
from .learner_state import (
    _section_b_working_copy,
    is_stale,
    load_learner_state,
    write_learner_state,
)
from .memory import (
    commit_history_entry,
    commit_memory_snapshot,
    compute_memory_update,
    load_learning_memory,
    needs_recompute,
    recompute_from_history,
)
from .intent_router import finalize as intent_finalize, pre_decide as intent_pre_decide
from .paths import repo_action_dir, repo_context_dir
from .repo_intake import resolve_repo_input
from .response_contract import build_response_contract, build_verification_block
from .schema_validation import validate_payload
from .session import start_session


def _current_target_pr_head_sha(repo: dict, target_pr_number: int | None) -> str | None:
    """Fetch the live head SHA of the target PR from upstream.

    Returns None on any failure — is_stale() treats None as 'no target PR SHA
    to compare' and skips that branch of the staleness check.
    """
    if not target_pr_number:
        return None
    upstream = repo.get("upstream") or repo.get("upstream_slug")
    if not upstream:
        return None
    import subprocess
    try:
        result = subprocess.run(
            [
                "gh", "pr", "view", str(target_pr_number),
                "--repo", upstream,
                "--json", "headRefOid",
                "-q", ".headRefOid",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    sha = result.stdout.strip()
    return sha or None


def _learner_state_snapshot(
    repo: dict, prompt: str | None
) -> tuple[dict | None, dict | None]:
    """Ensure learner-state.json is fresh, return (pointer, full_snapshot).

    Applies the 4-way staleness contract from agent-operating-contract.md
    step 6: rebuild if head_sha, working_copy.fingerprint, target PR head
    SHA, or TTL has changed/expired.

    Returns a tuple ``(pointer, full_snapshot)``. The pointer is the compact
    embedded view used by downstream schema (``learner_state`` field); the
    full snapshot is passed to ``build_response_contract`` so counts and
    verification lists are computed off the same in-memory object without
    re-reading disk.
    """
    repo_name = repo["name"]
    path = repo_context_dir(repo_name) / "learner-state.json"
    repo_path_raw = repo.get("path")
    repo_path = Path(repo_path_raw).expanduser() if repo_path_raw else None
    upstream = repo.get("upstream") or repo.get("upstream_slug")

    snapshot = load_learner_state(repo_name)
    needs_rebuild = snapshot is None

    if snapshot is not None and repo_path is not None:
        # Cheap part of the 4-way check: local head SHA + working copy
        # fingerprint. These are two git calls (~few ms).
        try:
            working_copy, _, current_head_sha = _section_b_working_copy(repo_path)
            current_fingerprint = working_copy.get("fingerprint", "")
        except Exception:
            current_head_sha = ""
            current_fingerprint = ""

        # Target PR head SHA — one gh call. Skip if local check already says
        # rebuild (no point burning the gh call on a doomed cache).
        current_target_head_sha: str | None = None
        snapshot_target_head = ((snapshot.get("target_pr_detail") or {}).get("head_sha"))
        if (
            snapshot.get("head_sha") == current_head_sha
            and (snapshot.get("working_copy") or {}).get("fingerprint") == current_fingerprint
            and snapshot_target_head  # no point checking if snapshot had no target
        ):
            current_target_head_sha = _current_target_pr_head_sha(
                repo, snapshot.get("target_pr_number")
            )

        needs_rebuild = is_stale(
            snapshot,
            current_head_sha=current_head_sha,
            current_fingerprint=current_fingerprint,
            current_target_head_sha=current_target_head_sha,
        )

    if needs_rebuild:
        if repo_path is None:
            return None, None
        try:
            snapshot = write_learner_state(
                repo_name=repo_name,
                repo_path=repo_path,
                prompt=prompt,
                upstream_owner_repo=upstream,
            )
        except Exception:
            return None, None
    if snapshot is None:
        return None, None
    pointer = {
        "path": str(path),
        "computed_at": snapshot.get("computed_at"),
        "target_pr_number": snapshot.get("target_pr_number"),
        "target_pr_selection_reason": snapshot.get("target_pr_selection_reason"),
        "coverage": snapshot.get("coverage"),
        "head_branch": snapshot.get("head_branch"),
        "head_sha": snapshot.get("head_sha"),
        "cycle_hint": snapshot.get("cycle_hint"),
    }
    return pointer, snapshot


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _memory_notes(summary: dict) -> list[str]:
    notes = []
    total_sessions = summary.get("total_sessions", 0)
    if total_sessions:
        notes.append(f"이 repo 기준 누적 학습 세션은 {total_sessions}회다.")
    top_topics = summary.get("top_topics", [])
    if top_topics:
        topic = top_topics[0]
        notes.append(f"가장 자주 다룬 주제는 {topic.get('topic')} ({topic.get('count')}회)다.")
    top_intents = summary.get("top_intents", [])
    if top_intents:
        intent = top_intents[0]
        notes.append(f"가장 자주 나온 질문 의도는 {intent.get('intent')} ({intent.get('count')}회)다.")
    top_learning_points = summary.get("top_learning_points", [])
    if top_learning_points:
        point = top_learning_points[0]
        if point.get("count", 0) >= 2 and point.get("confidence") in {"medium", "high"}:
            notes.append(f"반복 학습 중인 포인트는 {point.get('learning_point')} ({point.get('count')}회, confidence={point.get('confidence')})다.")
    recurring_paths = summary.get("recurring_paths", [])
    if recurring_paths:
        path = recurring_paths[0]
        notes.append(f"반복해서 걸리는 경로는 {path.get('path')} ({path.get('count')}회)다.")
    return notes


def _profile_notes(profile: dict) -> list[str]:
    notes = []
    if profile.get("confidence"):
        notes.append(f"현재 장기 학습 profile confidence는 {profile.get('confidence')} 이다.")
    streak = profile.get("recent_learning_streak")
    if streak and (streak.get("count") or 0) >= 2:
        notes.append(f"최근 학습 streak는 {streak.get('learning_point')} {streak.get('count')}회다.")
    underexplored = profile.get("underexplored_learning_points", [])
    if underexplored:
        first = underexplored[0]
        notes.append(f"상대적으로 덜 다룬 포인트는 {first.get('label')} 이다.")
    return notes


def _data_confidence_banner(archive_status: dict) -> list[str]:
    state = archive_status.get("bootstrap_state")
    if state == "ready":
        return []
    signals = archive_status.get("signals", {})
    total_prs = signals.get("total_prs", 0)
    covered = signals.get("prs_with_review_activity", 0)
    if state == "bootstrapping":
        return [
            f"⚠️ 아직 학습 자료가 충분히 모이지 않았습니다. 지금 답변은 일부 PR만 보고 만든 초안입니다 (현재 PR {total_prs}개, 리뷰 활동 있는 PR {covered}개).",
            "지금도 학습은 계속할 수 있지만, 다른 크루 사례와 리뷰 근거를 더 풍부하게 보려면 초기 자료 수집을 한 번 해두는 편이 좋습니다.",
        ]
    return [
        "⚠️ 아직 이 미션에 대한 학습 자료가 없습니다.",
        "다른 크루 PR와 리뷰를 근거로 같이 보려면 초기 자료 수집을 먼저 해야 합니다.",
    ]


def _render_coach_reply(
    session_payload: dict,
    memory_summary: dict,
    memory_profile: dict,
    archive_status: dict | None = None,
) -> str:
    response = session_payload["response"]
    lines = [
        "참고용 응답 초안:",
        "- 아래 내용은 최종 답변이 아니라, 현재 질문과 근거를 바탕으로 다시 합성하기 위한 reference다.",
    ]

    if archive_status:
        banner = _data_confidence_banner(archive_status)
        if banner:
            lines.append("")
            for item in banner:
                lines.append(item)
            lines.append("")

    for item in response.get("summary", []):
        lines.append(f"- {item}")

    memory_notes = _memory_notes(memory_summary)
    if memory_notes:
        lines.append("")
        lines.append("누적 학습 맥락:")
        for item in memory_notes:
            lines.append(f"- {item}")

    profile_notes = _profile_notes(memory_profile)
    if profile_notes:
        if "누적 학습 맥락:" not in lines:
            lines.append("")
            lines.append("누적 학습 맥락:")
        for item in profile_notes:
            lines.append(f"- {item}")

    if response.get("answer"):
        lines.append("")
        lines.append("이번 질문에 대한 해석:")
        for item in response["answer"]:
            lines.append(f"- {item}")

    for section in response.get("sections", [])[:3]:
        lines.append("")
        lines.append(f"{section['title']}:")
        for item in section.get("items", [])[:4]:
            lines.append(f"- {item}")

    if response.get("next_actions"):
        lines.append("")
        lines.append("지금 바로 할 일:")
        for item in response["next_actions"][:3]:
            lines.append(f"- [{item['priority']}] {item['title']}")

    follow_up = response.get("follow_up_question")
    if follow_up:
        lines.append("")
        lines.append("다음 질문:")
        lines.append(f"- {follow_up}")

    return "\n".join(lines).strip() + "\n"


def _blocked_coach_reply(repo_name: str, archive_status: dict, memory_summary: dict, memory_profile: dict) -> dict:
    lines = []
    for item in _data_confidence_banner(archive_status):
        lines.append(item)
    lines.append("")
    lines.append(f"- repo: {repo_name}")
    lines.append(f"- archive bootstrap_state: {archive_status.get('bootstrap_state')}")
    lines.append(f"- data_confidence: {archive_status.get('data_confidence')}")
    for reason in archive_status.get("reasons", []):
        lines.append(f"- reason: {reason}")

    memory_notes = _memory_notes(memory_summary)
    profile_notes = _profile_notes(memory_profile)
    if memory_notes or profile_notes:
        lines.append("")
        lines.append("누적 학습 맥락:")
        for item in memory_notes + profile_notes:
            lines.append(f"- {item}")

    return {
        "memory_notes": memory_notes + profile_notes,
        "response": {
            "status": "blocked",
            "reason": "학습 자료가 아직 없어 초기 자료 수집이 먼저 필요합니다.",
        },
        "markdown": "\n".join(lines).strip() + "\n",
    }


def _empty_cs_readiness(reason: str = "not_checked") -> dict:
    return {
        "state": "missing",
        "reason": reason,
        "corpus_hash": None,
        "index_manifest_hash": None,
        "next_command": "bin/cs-index-build",
    }


def _probe_missing_ml_deps() -> list[str]:
    """Return the subset of CS RAG ML deps that are not importable.

    Uses ``importlib.util.find_spec`` so the check stays lightweight and
    does not pull ~1 GB of torch/sentence-transformers into memory just to
    report readiness. Reused by both the ready path in
    ``_pre_augment_phase`` and the archive-blocked payload builder so the
    ``cs_readiness.reason == "deps_missing"`` contract is uniform across
    execution_status.
    """
    from importlib.util import find_spec  # noqa: WPS433

    return [
        name
        for name in ("sentence_transformers", "numpy", "sklearn")
        if find_spec(name) is None
    ]


def _check_cs_readiness() -> dict:
    """Probe CS RAG index readiness without importing ML deps.

    Lazy: only imports scripts.learning.rag.indexer, which is pure stdlib.
    Falls back to a degraded report if even that import fails. The ML
    dependency probe runs first — if deps are missing, we report
    ``reason=deps_missing`` regardless of whether the index files exist,
    because ``pip install -e .`` must land before an index rebuild can
    even be attempted.
    """
    missing_deps = _probe_missing_ml_deps()
    if missing_deps:
        return {
            "state": "missing",
            "reason": "deps_missing",
            "corpus_hash": None,
            "index_manifest_hash": None,
            "next_command": "pip install -e .",
        }
    try:
        from scripts.learning.rag import indexer as rag_indexer  # noqa: WPS433
    except Exception:
        return _empty_cs_readiness("indexer_import_failed")
    try:
        report = rag_indexer.is_ready()
    except Exception:
        return _empty_cs_readiness("readiness_error")
    return {
        "state": report.state,
        "reason": report.reason,
        "corpus_hash": report.corpus_hash,
        "index_manifest_hash": report.index_manifest_hash,
        "next_command": report.next_command,
    }


def _build_learning_projection(
    *,
    repo_name: str,
    drill_result: dict | None,
) -> dict | None:
    """Assemble cs_view / drill_history / reconciled for profile.json.

    Loads the append-only drill-history jsonl (including the this-turn
    drill_result that Phase 2 will persist), derives a compact summary,
    and runs profile_merge.compute_cs_view for the cs_view projection.
    Returns None if profile_merge is unavailable.
    """
    try:
        from scripts.learning import drill as _drill_mod  # noqa: WPS433
        from scripts.learning.profile_merge import compute_cs_view  # noqa: WPS433
    except Exception:
        return None

    history = _drill_mod.load_history(repo_name, limit=50)
    if drill_result is not None:
        history = history + [drill_result]

    cs_view = compute_cs_view(history)
    compact_history = [
        {
            "drill_session_id": h.get("drill_session_id"),
            "scored_at": h.get("scored_at"),
            "total_score": h.get("total_score"),
            "level": h.get("level"),
            "weak_tags": h.get("weak_tags") or [],
        }
        for h in history[-5:]
    ]
    return {
        "cs_view": cs_view,
        "drill_history": compact_history,
        "reconciled": None,  # filled in after unify()
    }


def _build_unified_profile(memory_profile: dict | None) -> dict | None:
    """Derive the per-turn unified_profile projection.

    Persisted truth stays in memory/profile.json; this is a compact view.
    Reuse the already-persisted ``cs_view`` directly — recomputing from
    ``drill_history`` here would only see the compact tail (missing
    ``dimensions`` and ``source_doc.category``), silently weakening
    ``weak_dimensions`` / ``low_categories`` vs persisted truth.
    Returns None if profile_merge is unavailable (never happens in practice
    because it's pure stdlib, but defensive to keep the payload valid).
    """
    try:
        from scripts.learning.profile_merge import unify as _unify  # noqa: WPS433
    except Exception:
        return None
    persisted_cs_view = (memory_profile or {}).get("cs_view")
    return _unify(memory_profile or {}, cs_view=persisted_cs_view)


def _pre_augment_phase(
    *,
    prompt: str | None,
    learner_state_full: dict | None,
    session_payload: dict,
    pending_drill: dict | None,
) -> dict:
    """Steps 3–6 of the learning pipeline: route drill → pre_decide → readiness → augment.

    Returns a dict bundle consumed by ``run_coach`` — keeps the ordering
    explicit so drill offer generation (step 8) can run after
    ``profile_merge.unify`` without duplicating the earlier steps.
    """
    # Lazy drill import — stdlib-only but deferred to keep coach_run alive
    # if anything in scripts.learning blows up.
    try:
        from scripts.learning import drill  # noqa: WPS433
    except Exception:
        drill = None  # type: ignore[assignment]

    drill_result: dict | None = None
    consumed_pending_id: str | None = None
    route_signals: dict = {}
    if drill is not None and pending_drill is not None:
        is_answer, route_signals = drill.route_answer(prompt or "", pending_drill)
        if is_answer:
            drill_result = drill.score_pending_answer(prompt or "", pending_drill)
            consumed_pending_id = pending_drill.get("drill_session_id")

    learning_points = [
        rec.get("learning_point")
        for rec in (session_payload.get("learning_point_recommendations") or [])
        if rec.get("learning_point")
    ]
    topic_hints = [t for t in (session_payload.get("primary_topic"),) if t]

    pre_result = intent_pre_decide(
        prompt or "",
        history=None,
        pending_drill=pending_drill if drill_result is None else None,
        learner_state=learner_state_full,
    )

    cs_readiness = _check_cs_readiness()
    cs_search_mode = pre_result.get("cs_search_mode", "skip")

    # ``_check_cs_readiness`` already folded the ML deps probe: a missing
    # stack yields state="missing"/reason="deps_missing", so the
    # state=="ready" guard below is sufficient — no second probe needed.
    augment_result: dict | None = None
    if cs_search_mode != "skip" and cs_readiness.get("state") == "ready":
        try:
            from scripts.learning.integration import augment as cs_augment  # noqa: WPS433
            augment_result = cs_augment(
                prompt=prompt or "",
                learning_points=learning_points,
                topic_hints=topic_hints,
                cs_search_mode=cs_search_mode,
            )
        except (ImportError, ModuleNotFoundError):
            # Defensive — find_spec said deps are present but an internal
            # import still broke. Degrade the same way so the AI can act.
            cs_readiness = {
                **cs_readiness,
                "state": "missing",
                "reason": "deps_missing",
                "next_command": "pip install -e .",
            }
            augment_result = None
        except Exception:
            augment_result = None

    sidecar = None
    cs_augmentation_compact: dict | None = None
    if augment_result is not None:
        sidecar = augment_result.get("sidecar")
        cs_augmentation_compact = {
            "by_learning_point": augment_result.get("by_learning_point") or {},
            "by_fallback_key": augment_result.get("by_fallback_key") or {},
            "fallback_reason": augment_result.get("fallback_reason"),
            "cs_categories_hit": augment_result.get("cs_categories_hit") or [],
            "sidecar_path": (
                "contexts/cs-augmentation.json" if sidecar else None
            ),
            "meta": augment_result.get("meta") or {},
        }

    return {
        "pre_result": pre_result,
        "cs_readiness": cs_readiness,
        "cs_augmentation_compact": cs_augmentation_compact,
        "sidecar": sidecar,
        "drill_result": drill_result,
        "consumed_pending_id": consumed_pending_id,
        "route_signals": route_signals,
    }


def _assert_response_contract(payload: dict) -> None:
    """Producer-side guard for response_contract shape.

    Why: the schema validator only enforces ``required`` inside dict values,
    so a root-level omission would slip through. This assertion runs before
    ``validate_payload`` and crashes loud on producer mistakes (missing
    contract, ready-state with null counts, thread_refs/stub_markdown
    mismatch).
    """
    assert "response_contract" in payload, "response_contract must be injected unconditionally"
    rc = payload["response_contract"]
    assert isinstance(rc, dict), "response_contract must be a dict"
    assert "snapshot_block" in rc and isinstance(rc["snapshot_block"], dict)
    assert "verification" in rc and isinstance(rc["verification"], dict)
    v = rc["verification"]
    assert "thread_refs" in v and isinstance(v["thread_refs"], list)

    if payload.get("execution_status") != "ready":
        return

    sb = rc["snapshot_block"]
    if sb.get("reason") == "ready":
        assert sb["markdown"] is not None, "ready payload: snapshot_block.markdown must be non-null"
        assert isinstance(sb["counts"], dict), "ready payload: snapshot_block.counts must be a dict"
        for bucket in ("still-applies", "likely-fixed", "already-fixed", "ambiguous", "unread"):
            assert bucket in sb["counts"]["classification"], f"missing classification bucket {bucket}"
        for bucket in ("text", "emoji", "none", "unknown"):
            assert bucket in sb["counts"]["reply_axis"], f"missing reply_axis bucket {bucket}"
    assert v["required_count"] == len(v["thread_refs"])
    if v["required_count"] > 0:
        assert v["stub_markdown"] is not None
    else:
        assert v["stub_markdown"] is None


def run_coach(
    repo_name: str | None = None,
    repo_path: str | None = None,
    prompt: str | None = None,
    pr_number: int | None = None,
    reviewer: str | None = None,
    context: str = "coach",
    freshness_hours: int = 6,
    force_sync: bool = False,
    sync_limit: int | None = None,
) -> dict:
    repo, resolution = resolve_repo_input(repo_name=repo_name, repo_path=repo_path, auto_register=True)

    if needs_recompute(repo["name"]):
        recompute_from_history(repo["name"])

    previous_memory = load_learning_memory(repo["name"])
    learner_state_pointer, learner_state_full = _learner_state_snapshot(repo, prompt)

    pre_status = compute_archive_status(repo["name"], freshness_hours=freshness_hours)
    if pre_status["bootstrap_state"] == "uninitialized":
        write_archive_status(repo["name"], freshness_hours=freshness_hours)
        blocked_payload = {
            "run_type": "coach_run",
            "execution_status": "blocked",
            "generated_at": _timestamp(),
            "repo": repo["name"],
            "repo_resolution": {
                "source": resolution.get("source"),
                "path": repo.get("path"),
                "upstream": repo.get("upstream"),
                "origin_full_name": repo.get("origin_full_name"),
                "track": repo.get("track"),
                "mission": repo.get("mission"),
                "title_contains": repo.get("title_contains"),
                "branch_hint": repo.get("branch_hint"),
                "current_pr_title": repo.get("current_pr_title"),
            },
            "archive_sync": {
                "skipped": True,
                "blocked": True,
                "reason": "학습 자료가 아직 없어 초기 자료 수집이 필요합니다.",
                "next_command": {
                    "cli": f"bin/bootstrap-repo --repo {repo['name']}",
                    "why": "한 번만 전체 수집을 해두면 이후 세션에서는 이 자료를 계속 재사용할 수 있습니다.",
                },
            },
            "archive_status": pre_status,
            "session": {
                "mode": context,
                "prompt": prompt,
                "json_path": None,
                "context_path": None,
                "action_path": None,
                "response_json_path": None,
                "response_markdown_path": None,
                "primary_intent": None,
                "primary_topic": None,
                "reviewer": reviewer,
                "current_pr": {"number": pr_number} if pr_number is not None else None,
                "focus_ranking_path": None,
                "focus_candidates": [],
                "candidate_interpretation_path": None,
                "learning_point_recommendations": [],
            },
            "memory": {
                "history_path": previous_memory.get("history_path"),
                "summary_path": previous_memory.get("summary_path"),
                "profile_path": previous_memory.get("profile_path"),
                "summary": previous_memory.get("summary"),
                "profile": previous_memory.get("profile"),
            },
            "learner_state": learner_state_pointer,
            "coach_reply": _blocked_coach_reply(
                repo["name"],
                pre_status,
                previous_memory.get("summary", {}),
                previous_memory.get("profile", {}),
            ),
            # Keep the top-level shape uniform with ready payloads so AI
            # consumers don't need a special branch for blocked. Learning
            # fields are null/omit because archive bootstrap must complete
            # first; CS readiness is still reported honestly.
            "cs_readiness": _check_cs_readiness(),
            "cs_augmentation": None,
            "intent_decision": {
                "detected_intent": "unknown",
                "pre_intent": "unknown",
                "cs_search_mode": "skip",
                "signals": {"reason": "archive_blocked"},
                "block_plan": {
                    "snapshot_block": "omit",
                    "cs_block": "omit",
                    "verification": "omit",
                    "drill_block": "omit",
                },
            },
            "unified_profile": None,
            "response_contract": build_response_contract(learner_state_full, "blocked"),
        }
        _assert_response_contract(blocked_payload)
        validate_payload("coach-run-result", blocked_payload)
        action_dir = repo_action_dir(repo["name"])
        path = action_dir / "coach-run.json"
        path.write_text(json.dumps(blocked_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        blocked_payload["json_path"] = str(path)
        return blocked_payload

    sync_result = ensure_repo_archive(
        repo,
        freshness_hours=freshness_hours,
        force=force_sync,
        limit=sync_limit,
        allow_full=False,
    )
    archive_status = compute_archive_status(repo["name"], freshness_hours=freshness_hours)
    session_payload = start_session(
        repo,
        mode=context,
        prompt=prompt,
        pr_number=pr_number,
        reviewer=reviewer,
        memory_context=previous_memory,
        archive_status=archive_status,
    )

    # Learning pipeline phase A — route drill → pre_decide → readiness → augment.
    # verification_required_count is derived from the same learner-state full
    # snapshot that build_response_contract will use, so block_plan stays in
    # sync with the rendered verification block.
    try:
        from scripts.learning import drill as _drill  # noqa: WPS433
        pending_drill_raw = _drill.load_pending(repo["name"])
        pending_drill = _drill.decrement_ttl(pending_drill_raw)
    except Exception:
        _drill = None  # type: ignore[assignment]
        pending_drill_raw = None
        pending_drill = None

    pre_verification = build_verification_block(learner_state_full or {}, "ready")
    phase_a = _pre_augment_phase(
        prompt=prompt,
        learner_state_full=learner_state_full,
        session_payload=session_payload,
        pending_drill=pending_drill,
    )
    pre_result = phase_a["pre_result"]
    cs_readiness = phase_a["cs_readiness"]
    cs_augmentation_compact = phase_a["cs_augmentation_compact"]
    cs_sidecar = phase_a["sidecar"]
    drill_result = phase_a["drill_result"]
    consumed_pending_id = phase_a["consumed_pending_id"]

    # Phase 1: compute everything in memory (no file writes).
    # Build learning_projection first so the persisted profile matches the
    # per-turn unified_profile view (cs_view / drill_history / reconciled
    # are the source-of-truth fields in profile.json, not coach-run.json).
    learning_projection = _build_learning_projection(
        repo_name=repo["name"],
        drill_result=drill_result,
    )
    memory_update = compute_memory_update(
        repo["name"],
        session_payload,
        learning_projection=learning_projection,
    )
    memory_summary = memory_update["summary"]
    memory_profile = memory_update["profile"]
    unified_profile = _build_unified_profile(memory_profile)

    # Persist reconciled onto profile.json so the next session can read it
    # directly instead of rerunning profile_merge.unify on the jsonl tail.
    if unified_profile is not None and isinstance(memory_profile, dict):
        memory_profile["reconciled"] = unified_profile.get("reconciled")
        memory_update["profile"] = memory_profile

    # Learning pipeline phase B — drill offer (after unified_profile) + finalize.
    drill_offer: dict | None = None
    if _drill is not None:
        # Skip the cooldown check when the same turn just consumed a pending
        # drill: the plan forbids chaining drill_answer → new offer in one turn.
        _pending_for_offer = pending_drill_raw if drill_result is None else {"just_consumed": True}
        try:
            drill_offer = _drill.build_offer_if_due(
                unified_profile,
                pre_intent=pre_result.get("pre_intent"),
                pending=_pending_for_offer,
                drill_history=_drill.load_history(repo["name"], limit=10),
                session_payload=session_payload,
            )
        except Exception:
            drill_offer = None

    intent_decision = intent_finalize(
        pre_result,
        augment_result=cs_augmentation_compact,
        drill_offer=drill_offer,
        drill_result=drill_result,
        verification_required_count=pre_verification.get("required_count", 0),
    )

    coach_reply_markdown = _render_coach_reply(
        session_payload,
        memory_summary,
        memory_profile,
        archive_status=archive_status,
    )

    payload = {
        "run_type": "coach_run",
        "execution_status": "ready",
        "generated_at": _timestamp(),
        "repo": repo["name"],
        "repo_resolution": {
            "source": resolution.get("source"),
            "path": repo.get("path"),
            "upstream": repo.get("upstream"),
            "origin_full_name": repo.get("origin_full_name"),
            "track": repo.get("track"),
            "mission": repo.get("mission"),
            "title_contains": repo.get("title_contains"),
            "branch_hint": repo.get("branch_hint"),
            "current_pr_title": repo.get("current_pr_title"),
        },
        "archive_sync": sync_result,
        "archive_status": archive_status,
        "session": {
            "mode": session_payload.get("mode"),
            "prompt": session_payload.get("prompt"),
            "json_path": session_payload.get("json_path"),
            "context_path": session_payload.get("context_path"),
            "action_path": session_payload.get("action_path"),
            "response_json_path": session_payload.get("response_json_path"),
            "response_markdown_path": session_payload.get("response_markdown_path"),
            "mission_map_path": session_payload.get("mission_map_path"),
            "mission_map_summary": session_payload.get("mission_map_summary", []),
            "primary_intent": session_payload.get("primary_intent"),
            "primary_topic": session_payload.get("primary_topic"),
            "reviewer": session_payload.get("reviewer"),
            "current_pr": session_payload.get("current_pr"),
            "focus_ranking_path": session_payload.get("focus_ranking_path"),
            "focus_candidates": session_payload.get("focus_candidates", []),
            "candidate_interpretation_path": session_payload.get("candidate_interpretation_path"),
            "learning_point_recommendations": session_payload.get("learning_point_recommendations", []),
        },
        "memory": {
            "history_path": memory_update.get("history_path"),
            "summary_path": memory_update.get("summary_path"),
            "profile_path": memory_update.get("profile_path"),
            "summary": memory_summary,
            "profile": memory_profile,
        },
        "learner_state": learner_state_pointer,
        "coach_reply": {
            "memory_notes": _memory_notes(memory_summary),
            "response": session_payload["response"],
            "markdown": coach_reply_markdown,
        },
        "cs_readiness": cs_readiness,
        "cs_augmentation": cs_augmentation_compact,
        "intent_decision": intent_decision,
        "unified_profile": unified_profile,
        "response_contract": build_response_contract(
            learner_state_full,
            "ready",
            augment_result=cs_augmentation_compact,
            intent_decision=intent_decision,
            drill_offer=drill_offer,
            drill_result=drill_result,
        ),
    }
    _assert_response_contract(payload)
    # Size budget: shrink heavy optional fields before schema validation so
    # the canonical artifact stays within the top-level budget (see
    # artifact_budget.SHRINK_LADDER). Load-bearing fields are untouched.
    payload = enforce_budget(payload)
    validate_payload("coach-run-result", payload)

    # Phase 2: sequential file writes — docs/learning-flow.md write-order:
    #   history.jsonl → coach-run.json → cs-augmentation sidecar →
    #   summary.json → profile.json → drill persistence
    # Rationale: history is append-only truth, then the canonical top-level
    # artifact, then advisory sidecars, then derived snapshots, then drill
    # state. Drill persistence runs last so a partial failure leaves an
    # unambiguous "pending still valid" state on disk.
    action_dir = repo_action_dir(repo["name"])
    path = action_dir / "coach-run.json"
    error_phase: str | None = None
    error_message: str | None = None

    try:
        commit_history_entry(repo["name"], memory_update)
    except Exception as exc:
        error_phase = "history_append"
        error_message = str(exc)

    if error_phase is None:
        try:
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        except Exception as exc:
            error_phase = "coach_run_write"
            error_message = str(exc)

    if error_phase is None and cs_sidecar is not None:
        try:
            sidecar_path = repo_context_dir(repo["name"]) / "cs-augmentation.json"
            sidecar_path.parent.mkdir(parents=True, exist_ok=True)
            sidecar_path.write_text(
                json.dumps(cs_sidecar, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        except Exception:
            # Sidecar write is advisory; do not block coach-run on failure.
            pass

    if error_phase is None:
        try:
            commit_memory_snapshot(repo["name"], memory_update)
        except Exception as exc:
            error_phase = "memory_snapshot"
            error_message = str(exc)

    if error_phase is None and _drill is not None:
        try:
            if drill_result is not None:
                _drill.append_history(repo["name"], drill_result)
            if consumed_pending_id is not None:
                _drill.clear_pending(repo["name"])
            if drill_offer is not None:
                _drill.save_pending(repo["name"], drill_offer)
            elif pending_drill is not None and consumed_pending_id is None:
                # TTL was decremented in memory — persist the new counter.
                _drill.save_pending(repo["name"], pending_drill)
        except Exception:
            pass

    if error_phase is not None:
        payload["execution_status"] = "error"
        payload["error_detail"] = {
            "phase": error_phase,
            "message": error_message,
            "timestamp": _timestamp(),
        }
        # Best-effort error marker. Try canonical path first, then sidecar.
        # Sidecar ensures error state is visible even if the original write failed.
        error_body = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
        written_path = path
        canonical_ok = False
        try:
            path.write_text(error_body, encoding="utf-8")
            canonical_ok = True
        except Exception:
            pass
        if not canonical_ok:
            sidecar = action_dir / "coach-run.error.json"
            try:
                sidecar.parent.mkdir(parents=True, exist_ok=True)
                sidecar.write_text(error_body, encoding="utf-8")
                written_path = sidecar
                payload["canonical_write_failed"] = True
                payload["error_detail"]["sidecar_path"] = str(sidecar)
            except Exception:
                pass
        payload["json_path"] = str(written_path)
        return payload

    payload["json_path"] = str(path)
    return payload
