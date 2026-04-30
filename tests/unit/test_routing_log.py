"""Tests for the routing decision logger (plan §P5.2)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts.workbench.core import routing_log
from scripts.workbench.core.interactive_rag_router import RouterDecision


# ---------------------------------------------------------------------------
# Token matching
# ---------------------------------------------------------------------------

def test_collect_matched_tokens_for_definition_query():
    """`Spring Bean 뭐야?` matches definition + learning_concept buckets.
    (Korean phrase "스프링 빈" lives in CS_DOMAIN/LEARNING vocab as English
    tokens — this mirrors the heuristic's existing behavior.)"""
    snap = routing_log.collect_matched_tokens("Spring Bean 뭐야?")
    assert "뭐야" in snap["definition"]
    assert "bean" in snap["learning_concept"] or "spring" in snap["learning_concept"]
    assert snap["override"] is None


def test_collect_matched_tokens_detects_override():
    snap = routing_log.collect_matched_tokens("RAG로 깊게 답해줘 spring")
    assert snap["override"] == "force_full"


def test_collect_matched_tokens_for_compose_question():
    snap = routing_log.collect_matched_tokens("DI vs IoC 차이가 뭐고 언제 써야 해?")
    assert "vs" in snap["depth"] or "차이" in snap["depth"]
    assert "di" in snap["learning_concept"] or "ioc" in snap["learning_concept"]


def test_collect_matched_tokens_returns_sorted_lists():
    """Determinism — same prompt always produces the same snapshot."""
    s1 = routing_log.collect_matched_tokens("transaction isolation 격리수준 캐시 vs index")
    s2 = routing_log.collect_matched_tokens("transaction isolation 격리수준 캐시 vs index")
    assert s1 == s2
    for bucket in ("definition", "depth", "cs_domain", "learning_concept", "coach_request", "tool"):
        assert s1[bucket] == sorted(s1[bucket])


# ---------------------------------------------------------------------------
# build_log_row
# ---------------------------------------------------------------------------

def _decision(**overrides) -> RouterDecision:
    base = dict(
        tier=1, mode="cheap", reason="domain + definition signal",
        experience_level=None, override_active=False,
        blocked=False, promoted_by_profile=False,
    )
    base.update(overrides)
    return RouterDecision(**base)


def test_build_log_row_includes_required_fields():
    row = routing_log.build_log_row(
        prompt="스프링 빈 뭐야?",
        decision=_decision(),
        repo="tobys-mission-1",
        now=datetime(2026, 4, 30, 12, 0, 0, tzinfo=timezone.utc),
    )
    assert row["schema_id"] == "routing-log-v1"
    assert row["repo"] == "tobys-mission-1"
    assert row["prompt"] == "스프링 빈 뭐야?"
    assert row["tier"] == 1
    assert row["mode"] == "cheap"
    assert row["logged_at"] == "2026-04-30T12:00:00+00:00"
    assert row["override_active"] is False
    assert row["blocked"] is False
    assert "matched_tokens" in row
    assert isinstance(row["matched_tokens"], dict)
    assert row["ai_unavailable"] is False


def test_build_log_row_carries_blocked_and_promoted_flags():
    row = routing_log.build_log_row(
        prompt="내 PR 어때?",
        decision=_decision(tier=3, mode=None, blocked=True),
        repo="tobys-mission-1",
    )
    assert row["tier"] == 3
    assert row["blocked"] is True


def test_build_log_row_records_ai_unavailable():
    row = routing_log.build_log_row(
        prompt="모호한 질문",
        decision=_decision(tier=0, mode=None, reason="no learning-domain signal"),
        repo="tobys-mission-1",
        ai_unavailable=True,
    )
    assert row["ai_unavailable"] is True


def test_build_log_row_includes_confidence_score():
    """The post-hoc heuristic confidence ride along on every row so
    analysis can correlate certainty with AI fallback usage (P4.4)."""
    row = routing_log.build_log_row(
        prompt="DI vs IoC 차이가 뭐야?",
        decision=_decision(tier=2, mode="full", reason="domain + depth signal"),
        repo="tobys-mission-1",
    )
    assert "confidence" in row
    assert 0.0 <= row["confidence"] <= 1.0
    assert isinstance(row["confidence_rationale"], str)
    assert isinstance(row["should_fallback"], bool)


def test_build_log_row_confidence_high_for_clear_tier2():
    row = routing_log.build_log_row(
        prompt="MVCC vs 트랜잭션 격리수준 차이",
        decision=_decision(tier=2, mode="full"),
        repo=None,
    )
    assert row["confidence"] >= 0.8
    assert row["should_fallback"] is False


def test_build_log_row_accepts_dict_decision():
    """Caller can pass a plain dict (e.g. asdict result) — useful when
    rag-ask carries the decision through a JSON stop."""
    row = routing_log.build_log_row(
        prompt="x",
        decision={
            "tier": 2, "mode": "full", "reason": "depth",
            "experience_level": "advanced", "override_active": False,
            "blocked": False, "promoted_by_profile": False,
        },
        repo=None,
    )
    assert row["tier"] == 2
    assert row["repo"] == ""


# ---------------------------------------------------------------------------
# resolve_log_path
# ---------------------------------------------------------------------------

def test_resolve_log_path_with_repo(tmp_path):
    p = routing_log.resolve_log_path(repo="my-repo", repo_root=tmp_path)
    assert p == tmp_path / "state" / "repos" / "my-repo" / "logs" / "routing.jsonl"


def test_resolve_log_path_without_repo_falls_back(tmp_path):
    p = routing_log.resolve_log_path(repo=None, repo_root=tmp_path)
    assert p == tmp_path / "state" / "cs_rag" / "logs" / "routing.jsonl"


def test_resolve_log_path_empty_string_repo_falls_back(tmp_path):
    p = routing_log.resolve_log_path(repo="", repo_root=tmp_path)
    assert p == tmp_path / "state" / "cs_rag" / "logs" / "routing.jsonl"


# ---------------------------------------------------------------------------
# record_routing_decision: append + parent dir
# ---------------------------------------------------------------------------

def test_record_routing_decision_appends_jsonl(tmp_path):
    path = routing_log.record_routing_decision(
        prompt="MVCC vs 격리수준 차이?",
        decision=_decision(tier=2, mode="full", reason="domain + depth signal"),
        repo="tobys-mission-1",
        repo_root=tmp_path,
        now=datetime(2026, 4, 30, 12, 0, 0, tzinfo=timezone.utc),
    )
    assert path.exists()
    rows = [json.loads(ln) for ln in path.read_text(encoding="utf-8").splitlines() if ln]
    assert len(rows) == 1
    assert rows[0]["tier"] == 2


def test_record_routing_decision_creates_parent_dirs(tmp_path):
    routing_log.record_routing_decision(
        prompt="x",
        decision=_decision(),
        repo="never-before-seen-repo",
        repo_root=tmp_path,
    )
    expected_dir = tmp_path / "state" / "repos" / "never-before-seen-repo" / "logs"
    assert expected_dir.exists()


def test_record_routing_decision_appends_multiple_rows(tmp_path):
    for i in range(3):
        routing_log.record_routing_decision(
            prompt=f"prompt-{i}",
            decision=_decision(reason=f"reason-{i}"),
            repo="repo-1",
            repo_root=tmp_path,
        )
    path = routing_log.resolve_log_path(repo="repo-1", repo_root=tmp_path)
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    reasons = [json.loads(ln)["reason"] for ln in lines]
    assert reasons == ["reason-0", "reason-1", "reason-2"]


# ---------------------------------------------------------------------------
# iter_log_rows: corruption-resistant
# ---------------------------------------------------------------------------

def test_iter_log_rows_skips_corrupt_and_unknown_schema(tmp_path):
    path = tmp_path / "log.jsonl"
    rows = [
        json.dumps({"schema_id": "routing-log-v1", "tier": 1}),
        "this is not json",
        json.dumps({"schema_id": "different-schema", "tier": 99}),  # filtered
        json.dumps({"schema_id": "routing-log-v1", "tier": 2}),
    ]
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
    parsed = list(routing_log.iter_log_rows(path))
    assert len(parsed) == 2
    assert parsed[0]["tier"] == 1
    assert parsed[1]["tier"] == 2


def test_iter_log_rows_missing_file_yields_nothing(tmp_path):
    assert list(routing_log.iter_log_rows(tmp_path / "missing.jsonl")) == []


# ---------------------------------------------------------------------------
# Summary helpers
# ---------------------------------------------------------------------------

def test_summarize_tier_distribution():
    rows = [
        {"tier": 0, "blocked": False},
        {"tier": 0, "blocked": False},
        {"tier": 1, "blocked": False},
        {"tier": 2, "blocked": False},
        {"tier": 3, "blocked": True},
        {"tier": 3, "blocked": False},
    ]
    counts = routing_log.summarize_tier_distribution(rows)
    assert counts == {"tier0": 2, "tier1": 1, "tier2": 1, "tier3_blocked": 1, "tier3": 1}


def test_summarize_token_match_frequency():
    rows = [
        {"matched_tokens": {"definition": ["뭐야"], "depth": []}},
        {"matched_tokens": {"definition": ["뭐야", "설명해"], "depth": ["vs"]}},
        {"matched_tokens": {"definition": ["뭐야"], "depth": ["vs", "차이"]}},
    ]
    top_def = routing_log.summarize_token_match_frequency(rows, bucket="definition", top_n=10)
    assert top_def[0] == ("뭐야", 3)
    assert ("설명해", 1) in top_def
    top_depth = routing_log.summarize_token_match_frequency(rows, bucket="depth", top_n=10)
    assert top_depth[0] == ("vs", 2)


def test_summarize_token_match_frequency_deterministic_on_ties():
    rows = [
        {"matched_tokens": {"definition": ["a", "b", "c"]}},
    ]
    out = routing_log.summarize_token_match_frequency(rows, bucket="definition")
    assert out == [("a", 1), ("b", 1), ("c", 1)]
