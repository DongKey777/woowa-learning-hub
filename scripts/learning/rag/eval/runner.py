"""Run report assembly — wires metrics + hard_regression + buckets +
manifest into a single artifact.

Design:
- The runner does NOT know how to retrieve. The caller injects a
  ``retrieve_fn(GradedQuery) -> list[str]`` callback. This keeps the
  runner test-friendly (mock retriever in unit tests) and lets callers
  swap between live searcher.search(), pre-computed results, or
  custom A/B harnesses without changing this module.
- Per-query metrics are computed in the order specified by plan
  §P1.1 step 2: graded_ndcg, primary_ndcg, MRR, hit, recall,
  companion_coverage, forbidden_rate. The full per-query record is
  preserved so downstream tools (CI delta comments, A/B reports) can
  drill in.
- Macro reports are emitted for all four bucket axes (category,
  difficulty, language, intent) on the four headline metrics.
- The RunReport is JSON-serialisable through ``run_report_to_dict``.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

from . import metrics as M
from .buckets import macro_report_all_axes, to_serialisable, BUCKET_AXES
from .dataset import GradedQuery
from .hard_regression import (
    RegressionResult,
    RegressionSummary,
    check_query,
    summarise,
    DEFAULT_FORBIDDEN_WINDOW,
)
from .manifest import RunManifest, manifest_to_dict

DEFAULT_TOP_K = 10

# Headline metrics that get macro-bucketed (plan §P1.1 step 2 / step 3).
HEADLINE_METRICS = (
    "primary_ndcg",
    "graded_ndcg",
    "mrr",
    "recall",
)


# ---------------------------------------------------------------------------
# Per-query record
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PerQueryMetrics:
    """All headline + side-signal metrics for one query at one top_k."""

    query_id: str
    bucket_category: str
    bucket_difficulty: str
    bucket_language: str
    bucket_intent: str
    primary_ndcg: float
    graded_ndcg: float
    mrr: float
    hit: float
    recall: float
    companion_coverage: float
    forbidden_rate: float


def compute_metrics(
    query: GradedQuery,
    ranked_paths: Sequence[str],
    *,
    top_k: int,
    forbidden_window: int = DEFAULT_FORBIDDEN_WINDOW,
) -> PerQueryMetrics:
    """Compute the seven metrics for one (query, ranking) pair.

    forbidden_rate uses ``forbidden_window`` not ``top_k`` — forbidden
    is a "near the top" check, not a "full retrieval" check.
    """
    qrels = query.qrels_dict()
    relevant = M.relevant_paths_from_qrels(qrels)
    ranked_list = list(ranked_paths)

    return PerQueryMetrics(
        query_id=query.query_id,
        bucket_category=query.bucket.category,
        bucket_difficulty=query.bucket.difficulty,
        bucket_language=query.bucket.language,
        bucket_intent=query.bucket.intent,
        primary_ndcg=M.primary_ndcg_at_k(ranked_list, qrels, top_k),
        graded_ndcg=M.graded_ndcg_at_k(ranked_list, qrels, top_k),
        mrr=M.mrr(ranked_list, relevant),
        hit=M.hit_at_k(ranked_list, relevant, top_k),
        recall=M.recall_at_k(ranked_list, relevant, top_k),
        companion_coverage=M.companion_coverage_at_k(
            ranked_list, query.companion_paths(), top_k
        ),
        forbidden_rate=M.forbidden_rate_at_k(
            ranked_list, query.forbidden_paths, forbidden_window
        ),
    )


# ---------------------------------------------------------------------------
# Run report
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RunReport:
    """Top-level evaluation artifact for one (model, fixture, top_k) run.

    Plan §P0.1 / §P1.1 — what gets serialised into
    reports/rag_eval/baseline_quality.json and similar.
    """

    manifest: RunManifest
    top_k: int
    forbidden_window: int
    per_query: tuple[PerQueryMetrics, ...]
    regression_summary: RegressionSummary
    regression_results: tuple[RegressionResult, ...]
    macro_reports: dict[str, dict[str, Any]]  # {metric: {axis: BucketReport}}
    overall_means: dict[str, float]  # {metric: micro mean}
    timing_warm_per_query_ms: tuple[float, ...] = field(default_factory=tuple)


# ---------------------------------------------------------------------------
# Evaluation loop
# ---------------------------------------------------------------------------

def evaluate_queries(
    queries: Sequence[GradedQuery],
    retrieve_fn: Callable[[GradedQuery], Sequence[str]],
    *,
    top_k: int = DEFAULT_TOP_K,
    forbidden_window: int = DEFAULT_FORBIDDEN_WINDOW,
) -> tuple[list[PerQueryMetrics], list[RegressionResult], list[float]]:
    """Run the retriever against every query and compute metrics + gates.

    Args:
        queries: fixture entries.
        retrieve_fn: callable that returns the ranked path list for one
            GradedQuery. Caller decides whether this hits the live
            searcher or a fake.
        top_k: number of ranks considered for nDCG/hit/recall/coverage.
        forbidden_window: separate window for forbidden_rate +
            hard_regression forbidden check.

    Returns:
        (per_query_metrics, regression_results, warm_per_query_ms)
        — three parallel lists in input order. Latency is measured
        around the retrieve_fn call only, so caller can choose what
        counts as "the retrieval".
    """
    per_query: list[PerQueryMetrics] = []
    regressions: list[RegressionResult] = []
    timings_ms: list[float] = []

    for query in queries:
        t0 = time.perf_counter()
        ranked_paths = retrieve_fn(query)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        timings_ms.append(elapsed_ms)

        per_query.append(
            compute_metrics(
                query,
                ranked_paths,
                top_k=top_k,
                forbidden_window=forbidden_window,
            )
        )
        regressions.append(
            check_query(query, ranked_paths, forbidden_window=forbidden_window)
        )

    return per_query, regressions, timings_ms


# ---------------------------------------------------------------------------
# Aggregate into RunReport
# ---------------------------------------------------------------------------

def build_run_report(
    queries: Sequence[GradedQuery],
    per_query: Sequence[PerQueryMetrics],
    regressions: Sequence[RegressionResult],
    *,
    manifest: RunManifest,
    top_k: int,
    forbidden_window: int,
    timings_warm_ms: Sequence[float] = (),
) -> RunReport:
    """Bundle per-query data into a RunReport with bucket macro views.

    Args:
        queries: same length as per_query / regressions; the bucket
            axes are read off these.
        per_query: PerQueryMetrics list parallel to queries.
        regressions: RegressionResult list parallel to queries.
        manifest: identity metadata (model, device, corpus_hash, ...)
            already constructed by the caller.
        top_k / forbidden_window: echoed into the report so consumers
            can interpret the metrics correctly.
        timings_warm_ms: optional per-query warm latencies (ms).
    """
    if len(queries) != len(per_query):
        raise ValueError(
            f"length mismatch: queries={len(queries)} per_query={len(per_query)}"
        )
    if len(queries) != len(regressions):
        raise ValueError(
            f"length mismatch: queries={len(queries)} regressions={len(regressions)}"
        )

    queries_list = list(queries)

    # Macro reports per metric per axis
    macro: dict[str, dict[str, Any]] = {}
    overall: dict[str, float] = {}
    for metric_name in HEADLINE_METRICS:
        scores = [getattr(pq, metric_name) for pq in per_query]
        # Per-axis macro (only when we have data)
        if queries_list:
            reports = macro_report_all_axes(queries_list, scores)
            macro[metric_name] = {
                axis: to_serialisable(reports[axis]) for axis in BUCKET_AXES
            }
            overall[metric_name] = (
                sum(scores) / len(scores) if scores else 0.0
            )
        else:
            macro[metric_name] = {}
            overall[metric_name] = 0.0

    # Side signals reported only as overall means (no macro needed —
    # they're tie-breakers, not selection drivers).
    side_signals = ("companion_coverage", "forbidden_rate", "hit")
    for metric_name in side_signals:
        scores = [getattr(pq, metric_name) for pq in per_query]
        overall[metric_name] = sum(scores) / len(scores) if scores else 0.0

    return RunReport(
        manifest=manifest,
        top_k=top_k,
        forbidden_window=forbidden_window,
        per_query=tuple(per_query),
        regression_summary=summarise(regressions),
        regression_results=tuple(regressions),
        macro_reports=macro,
        overall_means=overall,
        timing_warm_per_query_ms=tuple(timings_warm_ms),
    )


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------

def run_report_to_dict(report: RunReport) -> dict[str, Any]:
    """Render a RunReport into a JSON-friendly dict.

    Latency aggregates (P50/P95) are included from
    timing_warm_per_query_ms; manifest fields already carry the
    canonical p50/p95 values, but per-query ms are echoed here for
    debugging / drill-in.
    """
    per_query_blob = [
        {
            "query_id": pq.query_id,
            "bucket": {
                "category": pq.bucket_category,
                "difficulty": pq.bucket_difficulty,
                "language": pq.bucket_language,
                "intent": pq.bucket_intent,
            },
            "metrics": {
                "primary_ndcg": pq.primary_ndcg,
                "graded_ndcg": pq.graded_ndcg,
                "mrr": pq.mrr,
                "hit": pq.hit,
                "recall": pq.recall,
                "companion_coverage": pq.companion_coverage,
                "forbidden_rate": pq.forbidden_rate,
            },
        }
        for pq in report.per_query
    ]

    regressions_blob = [
        {
            "query_id": r.query_id,
            "passed": r.passed,
            "violations": list(r.violations),
            "warnings": list(r.warnings),
        }
        for r in report.regression_results
    ]

    summary = report.regression_summary
    return {
        "manifest": manifest_to_dict(report.manifest),
        "top_k": report.top_k,
        "forbidden_window": report.forbidden_window,
        "overall_means": dict(report.overall_means),
        "macro_reports": report.macro_reports,
        "regression_summary": {
            "total": summary.total,
            "passed_count": summary.passed_count,
            "failed_count": summary.failed_count,
            "all_passed": summary.all_passed,
            "violations_by_kind": dict(summary.violations_by_kind),
            "warnings_by_kind": dict(summary.warnings_by_kind),
            "failed_query_ids": list(summary.failed_query_ids),
        },
        "regressions": regressions_blob,
        "per_query": per_query_blob,
        "timing_warm_per_query_ms": list(report.timing_warm_per_query_ms),
    }
