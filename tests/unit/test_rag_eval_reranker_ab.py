"""Unit tests for scripts.learning.rag.eval.reranker_ab.

Coverage targets:
- aggregate_to_candidate_score pulls fields off RunReport blob
- run_one_reranker requires factory + non-empty queries
- run_reranker_ab_sweep iterates candidates, returns RerankerABReport
- run_reranker_ab_sweep selected_candidate_id is None when nobody passes
- reranker_ab_report_to_dict round-trips through json.dumps
- progress callback fired on candidate lifecycle
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.learning.rag.eval import reranker_ab as RA
from scripts.learning.rag.eval.dataset import (
    Bucket,
    GradedQuery,
    Qrel,
    RankBudget,
)
from scripts.learning.rag.eval.gate import BaselineScore, GateThresholds
from scripts.learning.rag.eval.reranker_candidates import RerankerCandidate


def _candidate(cid="rcand", size=120.0, is_control=False, high_risk=False):
    return RerankerCandidate(
        candidate_id=cid,
        hf_model_id=f"fake/{cid}",
        approx_size_mb=size,
        is_control=is_control,
        high_memory_risk=high_risk,
        notes="test fake",
    )


def _query(qid="q1"):
    return GradedQuery(
        query_id=qid,
        prompt="test prompt",
        mode="full",
        experience_level=None,
        learning_points=(),
        bucket=Bucket("spring", "beginner", "ko", "definition"),
        qrels=(Qrel("a.md", 3, "primary"),),
        forbidden_paths=(),
        rank_budget=RankBudget(10, 10),
        bucket_source="auto",
    )


def _baseline():
    return BaselineScore(
        primary_ndcg_macro=0.95,
        primary_ndcg_by_category={"spring": 0.95},
        primary_ndcg_category_counts={"spring": 50},
        forbidden_rate_overall=0.0,
        hard_regression_failures=5,
    )


def _runreport_blob():
    return {
        "manifest": {
            "corpus_hash": "x",
            "index_version": 2,
            "embedding_model": "fake-embed",
            "model_revision": None,
            "embedding_dim": 384,
            "device": "cpu",
            "reranker_model": "fake-reranker",
            "fusion_weights": {"k": 60, "w_bm25": 1.0, "w_dense": 1.0},
            "top_k": 10,
            "mode": "full",
            "latency_p50_warm": 80.0,
            "latency_p95_warm": 200.0,
            "cold_start_ms": 1000.0,
        },
        "macro_reports": {
            "primary_ndcg": {
                "category": {
                    "axis": "category", "macro_mean": 0.97,
                    "micro_mean": 0.97,
                    "per_bucket_mean": {"spring": 0.97},
                    "per_bucket_count": {"spring": 50},
                    "included_buckets": ["spring"], "excluded_buckets": [],
                }
            }
        },
        "overall_means": {
            "primary_ndcg": 0.97, "graded_ndcg": 0.97, "mrr": 0.97,
            "hit": 1.0, "recall": 1.0,
            "companion_coverage": 0.5, "forbidden_rate": 0.0,
        },
        "regression_summary": {
            "total": 50, "passed_count": 48, "failed_count": 2,
            "all_passed": False, "violations_by_kind": {},
            "warnings_by_kind": {}, "failed_query_ids": [],
        },
    }


# ---------------------------------------------------------------------------
# aggregate_to_candidate_score
# ---------------------------------------------------------------------------

def test_aggregate_pulls_macro_fields():
    cand = _candidate(cid="bge-reranker-v2-m3", size=2270.0)
    score = RA.aggregate_to_candidate_score(
        cand, _runreport_blob(), rss_mb=4500.0
    )
    assert score.candidate_id == "bge-reranker-v2-m3"
    assert score.primary_ndcg_macro == 0.97
    assert score.primary_ndcg_by_category == {"spring": 0.97}
    assert score.forbidden_rate_overall == 0.0
    assert score.hard_regression_failures == 2
    assert score.warm_p95_ms == 200.0
    assert score.rss_mb == 4500.0
    assert score.model_size_mb == 2270.0


# ---------------------------------------------------------------------------
# run_one_reranker — input validation only (heavy ML import skipped)
# ---------------------------------------------------------------------------

def test_run_one_reranker_requires_factory():
    cand = _candidate()
    with pytest.raises(ValueError, match="model_factory"):
        RA.run_one_reranker(cand, [_query()])


def test_run_one_reranker_rejects_empty_queries():
    cand = _candidate()
    with pytest.raises(ValueError, match="queries is empty"):
        RA.run_one_reranker(
            cand, [], model_factory=lambda _id: object()
        )


# ---------------------------------------------------------------------------
# run_reranker_ab_sweep — fully mocked to avoid loading searcher / torch
# ---------------------------------------------------------------------------

def test_run_reranker_ab_sweep_returns_report_with_passers(monkeypatch):
    """Stub run_one_reranker so we test orchestration without ML deps."""
    candidates = [_candidate(cid="a"), _candidate(cid="b")]

    def stub_run_one(candidate, queries, **kwargs):
        return _runreport_blob(), 4500.0

    monkeypatch.setattr(RA, "run_one_reranker", stub_run_one)

    report = RA.run_reranker_ab_sweep(
        candidates, [_query()], _baseline(),
        thresholds=GateThresholds(
            min_primary_uplift=-1.0,  # any uplift accepted
            max_p95_warm_ms=1e9,
            max_rss_mb=1e9,
        ),
        model_factory=lambda _id: object(),
    )

    assert len(report.candidates) == 2
    ids = {c.candidate.candidate_id for c in report.candidates}
    assert ids == {"a", "b"}
    assert report.embedding_index_root  # non-empty


def test_run_reranker_ab_sweep_no_passers_yields_no_selection(monkeypatch):
    monkeypatch.setattr(
        RA,
        "run_one_reranker",
        lambda c, q, **kw: (_runreport_blob(), 4500.0),
    )

    # Strict thresholds so nobody passes
    report = RA.run_reranker_ab_sweep(
        [_candidate(cid="z")], [_query()], _baseline(),
        thresholds=GateThresholds(min_primary_uplift=10.0),
        model_factory=lambda _id: object(),
    )
    assert report.selected_candidate_id is None
    assert report.pareto_order == ()
    assert "stay on baseline" in report.selection_rationale


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------

def test_reranker_ab_report_to_dict_round_trips_json(monkeypatch):
    monkeypatch.setattr(
        RA,
        "run_one_reranker",
        lambda c, q, **kw: (_runreport_blob(), 4500.0),
    )

    report = RA.run_reranker_ab_sweep(
        [_candidate(cid="x", size=120)], [_query()], _baseline(),
        thresholds=GateThresholds(min_primary_uplift=-1.0,
                                   max_p95_warm_ms=1e9, max_rss_mb=1e9),
        model_factory=lambda _id: object(),
    )
    blob = RA.reranker_ab_report_to_dict(report)
    serialised = json.dumps(blob)
    assert json.loads(serialised) == blob

    # Top-level structure
    assert "baseline" in blob
    assert "thresholds" in blob
    assert "embedding_index_root" in blob
    assert "candidates" in blob
    assert "pareto_order" in blob
    assert "selected_candidate_id" in blob
    assert "selection_rationale" in blob

    # Per-candidate carries reranker-specific fields
    cand_blob = blob["candidates"][0]
    assert cand_blob["candidate_id"] == "x"
    assert "high_memory_risk" in cand_blob
    assert "hf_model_id" in cand_blob
    assert "score" in cand_blob
    assert "gate" in cand_blob


def test_progress_callback_fires_on_candidate_lifecycle(monkeypatch):
    monkeypatch.setattr(
        RA,
        "run_one_reranker",
        lambda c, q, **kw: (_runreport_blob(), 4500.0),
    )

    events: list[tuple[str, dict]] = []

    def progress(stage, info):
        events.append((stage, info))

    RA.run_reranker_ab_sweep(
        [_candidate(cid="p")], [_query()], _baseline(),
        thresholds=GateThresholds(min_primary_uplift=-1.0,
                                   max_p95_warm_ms=1e9, max_rss_mb=1e9),
        model_factory=lambda _id: object(),
        progress=progress,
    )

    stages = [e[0] for e in events]
    assert "candidate_start" in stages
    assert "candidate_done" in stages
