"""Unit tests for scripts.learning.rag.eval.runner.

Coverage targets:
- compute_metrics returns all seven values for one (query, ranking)
- evaluate_queries calls retrieve_fn once per query and times each
- evaluate_queries propagates retrieve_fn exceptions
- build_run_report aggregates macro reports for headline metrics
- build_run_report length-mismatch raises
- Empty queries → empty report (no division-by-zero)
- run_report_to_dict produces JSON-serialisable output
- Round-trip: report dict round-trips through json.dumps without loss
"""

from __future__ import annotations

import json
import math

import pytest

from scripts.learning.rag.eval.dataset import (
    Bucket,
    GradedQuery,
    Qrel,
    RankBudget,
)
from scripts.learning.rag.eval.manifest import FusionWeights, RunManifest
from scripts.learning.rag.eval import runner as R


def _query(
    *,
    qid: str = "q",
    primary: str = "primary.md",
    companion: tuple[str, ...] = (),
    forbidden: tuple[str, ...] = (),
    bucket: Bucket | None = None,
    primary_max_rank: int = 1,
) -> GradedQuery:
    if bucket is None:
        bucket = Bucket("spring", "beginner", "ko", "definition")
    qrels = [Qrel(primary, 3, "primary")]
    qrels.extend(Qrel(p, 1, "companion") for p in companion)
    return GradedQuery(
        query_id=qid,
        prompt="p",
        mode="full",
        experience_level=None,
        learning_points=(),
        bucket=bucket,
        qrels=tuple(qrels),
        forbidden_paths=forbidden,
        rank_budget=RankBudget(primary_max_rank, 4),
        bucket_source="auto",
    )


def _good_manifest() -> RunManifest:
    return RunManifest(
        corpus_hash="abc",
        index_version=2,
        embedding_model="m",
        model_revision=None,
        embedding_dim=384,
        device="cpu",
        reranker_model=None,
        fusion_weights=FusionWeights.default(),
        top_k=10,
        mode="full",
        latency_p50_warm=10.0,
        latency_p95_warm=20.0,
        cold_start_ms=100.0,
    )


# ---------------------------------------------------------------------------
# compute_metrics
# ---------------------------------------------------------------------------

def test_compute_metrics_perfect_ranking():
    q = _query()
    pq = R.compute_metrics(q, ["primary.md", "x.md"], top_k=10)
    assert pq.query_id == "q"
    assert pq.bucket_category == "spring"
    assert math.isclose(pq.primary_ndcg, 1.0)
    assert math.isclose(pq.graded_ndcg, 1.0)
    assert math.isclose(pq.mrr, 1.0)
    assert pq.hit == 1.0
    assert math.isclose(pq.recall, 1.0)


def test_compute_metrics_companion_signal_separated_from_primary():
    q = _query(companion=("c1.md",))
    pq = R.compute_metrics(q, ["primary.md", "c1.md"], top_k=10)
    assert pq.primary_ndcg == 1.0  # primary at rank 1
    assert pq.companion_coverage == 1.0  # c1 in top-10
    # companion shouldn't count as relevant (grade 1 < 2 threshold)
    # so MRR is from primary only
    assert pq.mrr == 1.0


def test_compute_metrics_forbidden_rate_uses_window_not_top_k():
    """forbidden_rate respects forbidden_window even when top_k is larger."""
    q = _query(forbidden=("bad.md",))
    pq = R.compute_metrics(
        q, ["primary.md", "x.md", "y.md", "z.md", "w.md", "bad.md"],
        top_k=10, forbidden_window=5,
    )
    # bad.md at rank 6 → outside window=5 → forbidden_rate = 0
    assert pq.forbidden_rate == 0.0


# ---------------------------------------------------------------------------
# evaluate_queries
# ---------------------------------------------------------------------------

def test_evaluate_queries_calls_retrieve_once_per_query():
    queries = [_query(qid=f"q{i}") for i in range(3)]
    calls: list[str] = []

    def fake_retrieve(q: GradedQuery) -> list[str]:
        calls.append(q.query_id)
        return ["primary.md"]

    pq, reg, timings = R.evaluate_queries(queries, fake_retrieve, top_k=10)
    assert calls == ["q0", "q1", "q2"]
    assert len(pq) == 3
    assert len(reg) == 3
    assert len(timings) == 3
    assert all(t >= 0 for t in timings)


def test_evaluate_queries_propagates_retriever_exceptions():
    queries = [_query()]

    def boom(q):
        raise RuntimeError("retriever down")

    with pytest.raises(RuntimeError, match="retriever down"):
        R.evaluate_queries(queries, boom, top_k=10)


def test_evaluate_queries_per_query_metrics_match_compute_metrics():
    """The runner should call the same compute_metrics path that callers
    can use directly. Sanity check: matched output."""
    q = _query()
    pq, _, _ = R.evaluate_queries([q], lambda _: ["primary.md"], top_k=10)
    direct = R.compute_metrics(q, ["primary.md"], top_k=10)
    assert pq[0] == direct


# ---------------------------------------------------------------------------
# build_run_report
# ---------------------------------------------------------------------------

def test_build_run_report_includes_all_headline_macros():
    queries = [_query(qid=f"q{i}") for i in range(2)]
    pq = [R.compute_metrics(q, ["primary.md"], top_k=10) for q in queries]
    reg = [
        R.check_query(q, ["primary.md"]) if False else  # noqa: E712 placeholder
        __import__(
            "scripts.learning.rag.eval.hard_regression",
            fromlist=["check_query"],
        ).check_query(q, ["primary.md"])
        for q in queries
    ]
    report = R.build_run_report(
        queries, pq, reg,
        manifest=_good_manifest(), top_k=10, forbidden_window=5,
    )
    # Headline macros present
    for m in R.HEADLINE_METRICS:
        assert m in report.macro_reports
        for axis in ("category", "difficulty", "language", "intent"):
            assert axis in report.macro_reports[m]


def test_build_run_report_length_mismatch_raises():
    queries = [_query(qid="q1")]
    pq = []
    with pytest.raises(ValueError, match="length mismatch"):
        R.build_run_report(
            queries, pq, [],
            manifest=_good_manifest(), top_k=10, forbidden_window=5,
        )


def test_build_run_report_empty_queries_produce_zero_overall():
    report = R.build_run_report(
        [], [], [],
        manifest=_good_manifest(), top_k=10, forbidden_window=5,
    )
    for m in R.HEADLINE_METRICS:
        assert report.overall_means[m] == 0.0
    assert report.regression_summary.total == 0
    assert report.regression_summary.all_passed  # no failures, vacuously


# ---------------------------------------------------------------------------
# run_report_to_dict — JSON serialisation
# ---------------------------------------------------------------------------

def test_run_report_to_dict_is_json_serialisable():
    queries = [_query()]
    pq, reg, timings = R.evaluate_queries(queries, lambda _: ["primary.md"], top_k=10)
    report = R.build_run_report(
        queries, pq, reg,
        manifest=_good_manifest(), top_k=10, forbidden_window=5,
        timings_warm_ms=timings,
    )
    blob = R.run_report_to_dict(report)
    serialised = json.dumps(blob)
    # Round trip
    assert json.loads(serialised) == blob


def test_run_report_to_dict_carries_per_query_and_regressions():
    queries = [_query(qid="qa"), _query(qid="qb")]
    pq, reg, _ = R.evaluate_queries(queries, lambda _: ["primary.md"], top_k=10)
    report = R.build_run_report(
        queries, pq, reg,
        manifest=_good_manifest(), top_k=10, forbidden_window=5,
    )
    blob = R.run_report_to_dict(report)
    assert len(blob["per_query"]) == 2
    assert blob["per_query"][0]["query_id"] == "qa"
    assert "metrics" in blob["per_query"][0]
    assert "primary_ndcg" in blob["per_query"][0]["metrics"]

    assert len(blob["regressions"]) == 2
    assert blob["regression_summary"]["total"] == 2
    assert blob["regression_summary"]["all_passed"] is True


def test_run_report_to_dict_manifest_validates():
    """The manifest section MUST round-trip through schema validation
    (manifest_to_dict already does this; this test just confirms the
    runner doesn't bypass it)."""
    queries = [_query()]
    pq, reg, _ = R.evaluate_queries(queries, lambda _: ["primary.md"], top_k=10)
    report = R.build_run_report(
        queries, pq, reg,
        manifest=_good_manifest(), top_k=10, forbidden_window=5,
    )
    blob = R.run_report_to_dict(report)
    # manifest_to_dict is called inside; if it didn't validate, an
    # invalid blob could leak. Spot-check required keys.
    required = {
        "corpus_hash", "embedding_model", "embedding_dim",
        "device", "mode", "top_k", "fusion_weights",
    }
    assert required <= set(blob["manifest"])
