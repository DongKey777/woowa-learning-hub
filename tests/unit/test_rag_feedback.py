"""Tests for the rag-feedback channel (plan §P7.1 + §P7.2)."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from scripts.learning.rag import feedback as F


# ---------------------------------------------------------------------------
# prompt_hash
# ---------------------------------------------------------------------------

def test_compute_prompt_hash_strips_whitespace():
    assert F.compute_prompt_hash("  spring  ") == F.compute_prompt_hash("spring")


def test_compute_prompt_hash_distinct():
    assert F.compute_prompt_hash("a") != F.compute_prompt_hash("b")


# ---------------------------------------------------------------------------
# build_feedback_row
# ---------------------------------------------------------------------------

def test_build_feedback_row_minimal():
    row = F.build_feedback_row(
        prompt="스프링 빈?",
        signal="helpful",
        hits=[{"path": "knowledge/cs/contents/spring/bean.md"}],
        now=datetime(2026, 4, 30, 12, 0, 0, tzinfo=timezone.utc),
    )
    assert row["schema_id"] == "rag-feedback-v1"
    assert row["signal"] == "helpful"
    assert row["prompt"] == "스프링 빈?"
    assert len(row["prompt_hash"]) == 40
    assert row["repo"] == ""
    assert row["note"] == ""
    assert row["hits"] == [{"path": "knowledge/cs/contents/spring/bean.md"}]


def test_build_feedback_row_accepts_strings_and_dataclass():
    row = F.build_feedback_row(
        prompt="x",
        signal="helpful",
        hits=[
            "knowledge/cs/contents/spring/bean.md",
            F.FeedbackHit(path="knowledge/cs/contents/spring/component-scan.md", section="핵심 개념"),
            {"path": "knowledge/cs/contents/spring/aop.md", "section": "프록시"},
        ],
    )
    assert row["hits"] == [
        {"path": "knowledge/cs/contents/spring/bean.md"},
        {"path": "knowledge/cs/contents/spring/component-scan.md", "section": "핵심 개념"},
        {"path": "knowledge/cs/contents/spring/aop.md", "section": "프록시"},
    ]


def test_build_feedback_row_rejects_invalid_signal():
    with pytest.raises(ValueError):
        F.build_feedback_row(prompt="x", signal="great", hits=[])


def test_build_feedback_row_rejects_empty_prompt():
    with pytest.raises(ValueError):
        F.build_feedback_row(prompt="   ", signal="helpful", hits=[])


def test_build_feedback_row_rejects_unsupported_hit_shape():
    with pytest.raises(ValueError):
        F.build_feedback_row(prompt="x", signal="helpful", hits=[123])  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# resolve_log_paths
# ---------------------------------------------------------------------------

def test_resolve_log_paths_global_only_when_no_repo(tmp_path):
    paths = F.resolve_log_paths(repo=None, repo_root=tmp_path)
    assert len(paths) == 1
    assert paths[0] == tmp_path / "state" / "cs_rag" / "feedback.jsonl"


def test_resolve_log_paths_includes_per_repo_when_repo_set(tmp_path):
    paths = F.resolve_log_paths(repo="my-repo", repo_root=tmp_path)
    assert len(paths) == 2
    assert paths[0] == tmp_path / "state" / "cs_rag" / "feedback.jsonl"
    assert paths[1] == tmp_path / "state" / "repos" / "my-repo" / "logs" / "rag_feedback.jsonl"


# ---------------------------------------------------------------------------
# append_feedback
# ---------------------------------------------------------------------------

def test_append_feedback_writes_to_global_only(tmp_path):
    paths = F.append_feedback(
        prompt="x",
        signal="helpful",
        hits=["a.md"],
        repo=None,
        repo_root=tmp_path,
    )
    assert len(paths) == 1
    assert paths[0].exists()


def test_append_feedback_mirrors_to_per_repo(tmp_path):
    paths = F.append_feedback(
        prompt="x",
        signal="helpful",
        hits=["a.md"],
        repo="r1",
        repo_root=tmp_path,
    )
    assert len(paths) == 2
    for p in paths:
        assert p.exists()


def test_append_feedback_appends_multiple_rows(tmp_path):
    for i in range(3):
        F.append_feedback(
            prompt=f"q{i}", signal="helpful", hits=[f"d{i}.md"],
            repo=None, repo_root=tmp_path,
        )
    log = tmp_path / "state" / "cs_rag" / "feedback.jsonl"
    lines = log.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    rows = [json.loads(ln) for ln in lines]
    assert [r["prompt"] for r in rows] == ["q0", "q1", "q2"]


# ---------------------------------------------------------------------------
# iter_feedback_rows: corruption-resistant
# ---------------------------------------------------------------------------

def test_iter_feedback_rows_skips_invalid(tmp_path):
    p = tmp_path / "log.jsonl"
    p.write_text(
        "\n".join([
            json.dumps({"schema_id": "rag-feedback-v1", "signal": "helpful", "prompt": "a"}),
            "garbage",
            json.dumps({"schema_id": "different", "signal": "helpful"}),
            json.dumps({"schema_id": "rag-feedback-v1", "signal": "bogus"}),  # bad enum
            json.dumps({"schema_id": "rag-feedback-v1", "signal": "not_helpful", "prompt": "b"}),
        ]) + "\n",
        encoding="utf-8",
    )
    rows = list(F.iter_feedback_rows(p))
    assert len(rows) == 2
    assert {r["signal"] for r in rows} == {"helpful", "not_helpful"}


def test_iter_feedback_rows_missing_file(tmp_path):
    assert list(F.iter_feedback_rows(tmp_path / "missing.jsonl")) == []


# ---------------------------------------------------------------------------
# Summary helpers
# ---------------------------------------------------------------------------

def test_summarize_signals_counts():
    rows = [
        {"signal": "helpful"}, {"signal": "helpful"},
        {"signal": "not_helpful"},
        {"signal": "unclear"},
    ]
    assert F.summarize_signals(rows) == {"helpful": 2, "not_helpful": 1, "unclear": 1}


def test_aggregate_pair_counts_sorts_desc_then_alpha():
    rows = [
        {"signal": "not_helpful", "prompt": "Q1", "hits": [{"path": "doc-A.md"}]},
        {"signal": "not_helpful", "prompt": "Q1", "hits": [{"path": "doc-A.md"}]},
        {"signal": "not_helpful", "prompt": "Q2", "hits": [{"path": "doc-B.md"}]},
        {"signal": "helpful",     "prompt": "Q1", "hits": [{"path": "doc-A.md"}]},
    ]
    pairs = F.aggregate_pair_counts(rows, signal="not_helpful")
    assert pairs[0] == ("Q1", "doc-A.md", 2)
    assert pairs[1] == ("Q2", "doc-B.md", 1)


def test_aggregate_pair_counts_rejects_invalid_signal():
    with pytest.raises(ValueError):
        F.aggregate_pair_counts([], signal="bogus")


def test_golden_promotion_candidates_excludes_negatives():
    rows = [
        {"signal": "helpful", "prompt": "Q", "hits": [{"path": "good.md"}]},
        {"signal": "helpful", "prompt": "Q", "hits": [{"path": "good.md"}]},
        {"signal": "helpful", "prompt": "R", "hits": [{"path": "mixed.md"}]},
        {"signal": "helpful", "prompt": "R", "hits": [{"path": "mixed.md"}]},
        {"signal": "not_helpful", "prompt": "R", "hits": [{"path": "mixed.md"}]},
    ]
    candidates = F.golden_promotion_candidates(rows, min_helpful=2)
    assert candidates == [("Q", "good.md", 2)]


def test_golden_promotion_candidates_respects_min_helpful_threshold():
    rows = [
        {"signal": "helpful", "prompt": "Q", "hits": [{"path": "single.md"}]},
    ]
    assert F.golden_promotion_candidates(rows, min_helpful=2) == []


def test_cleanup_candidates_threshold():
    rows = [
        {"signal": "not_helpful", "prompt": "Q", "hits": [{"path": "bad.md"}]},
        {"signal": "not_helpful", "prompt": "Q", "hits": [{"path": "bad.md"}]},
        {"signal": "not_helpful", "prompt": "R", "hits": [{"path": "single.md"}]},
    ]
    candidates = F.cleanup_candidates(rows, min_not_helpful=2)
    assert candidates == [("Q", "bad.md", 2)]
