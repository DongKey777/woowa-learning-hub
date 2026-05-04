"""Reranker A/B sweep orchestrator — fixed embedding index, swap reranker.

Plan §P3.1 — reranker A/B's structure mirrors P2's embedding A/B but
inverts the fixture: the embedding index is *fixed* (typically
production state/cs_rag/) and only the reranker swaps. That isolates
the reranker contribution to the metric.

Pipeline per candidate:
1. RerankerSwap(model_id, factory) binds reranker._model + RERANK_MODEL.
2. searcher.search() runs FTS + dense + RRF + reranker (the swapped
   one) on the fixed embedding index.
3. runner.evaluate_queries computes per-query metrics.
4. Aggregate → CandidateScore (reused from gate.py).
5. Gate evaluation against the embedding-baseline.

Heavy ML imports (CrossEncoder) lazy-load through the factory so this
module is import-cheap and unit-testable with fakes.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import runner as R
from .dataset import GradedQuery
from .gate import (
    BaselineScore,
    CandidateScore,
    GateResult,
    GateThresholds,
    evaluate_candidate,
    pareto_select,
)
from .manifest import FusionWeights, RunManifest
from .precheck import get_process_rss_mb
from .reranker_candidates import RerankerCandidate
from .reranker_swap import RerankerSwap
from .runtime_index import resolve_runtime_index_info


DEFAULT_EMBEDDING_INDEX_ROOT = Path("state/cs_rag")
"""Default fixed embedding index path (= production root). Reranker
A/B sweep uses this so reranker scores are isolated from embedding
variance."""


# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class RerankerRunResult:
    """One reranker candidate's full output."""

    candidate: RerankerCandidate
    candidate_score: CandidateScore
    gate_result: GateResult
    run_report_blob: dict[str, Any]
    rss_after_run_mb: float


@dataclass(frozen=True)
class RerankerABReport:
    """Top-level reranker_ab_report.json structure."""

    baseline: BaselineScore
    thresholds: GateThresholds
    embedding_index_root: str  # provenance — which embedding was used
    candidates: tuple[RerankerRunResult, ...]
    pareto_order: tuple[str, ...]
    selected_candidate_id: str | None
    selection_rationale: str


# ---------------------------------------------------------------------------
# Aggregate RunReport → CandidateScore
# ---------------------------------------------------------------------------

def aggregate_to_candidate_score(
    candidate: RerankerCandidate,
    run_report_blob: dict[str, Any],
    *,
    rss_mb: float,
    bucket_axis: str = "category",
) -> CandidateScore:
    """Same projection as ab_sweep.aggregate_to_candidate_score, but
    reuses the reranker candidate's metadata for the score."""
    macro = run_report_blob["macro_reports"]["primary_ndcg"][bucket_axis]
    overall = run_report_blob["overall_means"]
    summary = run_report_blob["regression_summary"]
    manifest = run_report_blob["manifest"]

    return CandidateScore(
        candidate_id=candidate.candidate_id,
        primary_ndcg_macro=float(macro["macro_mean"]),
        primary_ndcg_by_category=dict(macro["per_bucket_mean"]),
        primary_ndcg_category_counts=dict(macro["per_bucket_count"]),
        forbidden_rate_overall=float(overall.get("forbidden_rate", 0.0)),
        hard_regression_failures=int(summary["failed_count"]),
        warm_p95_ms=float(manifest["latency_p95_warm"]),
        rss_mb=rss_mb,
        model_size_mb=candidate.approx_size_mb,
    )


# ---------------------------------------------------------------------------
# Per-candidate run
# ---------------------------------------------------------------------------

def run_one_reranker(
    candidate: RerankerCandidate,
    queries: Sequence[GradedQuery],
    *,
    embedding_index_root: Path | str = DEFAULT_EMBEDDING_INDEX_ROOT,
    top_k: int = 10,
    forbidden_window: int = 5,
    device: str = "cpu",
    mode: str = "full",
    model_factory: Callable[[str], Any] | None = None,
    progress: Callable[[str, dict], None] | None = None,
) -> tuple[dict[str, Any], float]:
    """Bind candidate reranker, evaluate against fixed embedding index.

    Returns (run_report_blob, rss_after_run_mb).

    The embedding index at ``embedding_index_root`` is NOT touched —
    we only swap the reranker. This isolates the reranker
    contribution to the score.

    Args:
        candidate: which reranker to bind
        queries: shared fixture
        embedding_index_root: path to the fixed embedding index
            (state/cs_rag/ in production; could be a P2 candidate's
            eval index if doing combined embedding+reranker testing)
        top_k / forbidden_window: forwarded to evaluate_queries
        device: forwarded to model_factory
        mode: searcher mode for this run
        model_factory: callable(hf_model_id) -> CrossEncoder. Tests
            pass a fake; production uses
            reranker_swap.default_cross_encoder_factory(device).
        progress: optional ``(stage, info)`` callback.
    """
    if not queries:
        raise ValueError("run_one_reranker: queries is empty")
    if model_factory is None:
        raise ValueError(
            "run_one_reranker: model_factory must be provided "
            "(production: reranker_swap.default_cross_encoder_factory(device))"
        )

    def _tick(stage: str, info: dict | None = None) -> None:
        if progress is not None:
            progress(stage, info or {})

    # Late import to keep this module unit-testable without searcher
    # (which pulls torch at import time)
    from scripts.learning.rag import searcher

    index_info = resolve_runtime_index_info(embedding_index_root, backend="auto")

    _tick("load_reranker", {"candidate": candidate.candidate_id})
    t0 = time.perf_counter()

    # Bind reranker for the duration of evaluation
    with RerankerSwap(
        model_id=candidate.hf_model_id,
        model_factory=model_factory,
    ):
        cold_load_ms = (time.perf_counter() - t0) * 1000.0
        _tick("evaluate", {"top_k": top_k})

        def retrieve(query):
            hits = searcher.search(
                query.prompt,
                learning_points=list(query.learning_points),
                top_k=top_k,
                mode=mode,
                experience_level=query.experience_level,
                index_root=embedding_index_root,
                backend=index_info.backend,
            )
            return [h["path"] for h in hits]

        per_query, regressions, timings_warm = R.evaluate_queries(
            queries, retrieve,
            top_k=top_k, forbidden_window=forbidden_window,
        )

    # Compute warm percentiles
    if timings_warm:
        sorted_t = sorted(timings_warm)
        p50 = sorted_t[len(sorted_t) // 2]
        p95_idx = max(0, min(len(sorted_t) - 1,
                              int(round(0.95 * (len(sorted_t) - 1)))))
        p95 = sorted_t[p95_idx]
    else:
        p50 = 0.0
        p95 = 0.0

    manifest = RunManifest(
        corpus_hash=index_info.corpus_hash,
        index_version=index_info.index_version,
        embedding_model=index_info.embedding_model,
        model_revision=index_info.model_revision,
        embedding_dim=index_info.embedding_dim,
        device=device,
        reranker_model=candidate.hf_model_id,
        fusion_weights=FusionWeights.default(),
        top_k=top_k,
        mode=mode,
        latency_p50_warm=p50,
        latency_p95_warm=p95,
        cold_start_ms=cold_load_ms,
        backend=index_info.backend,
        modalities=index_info.modalities,
        encoder=index_info.encoder,
        lancedb=index_info.lancedb,
    )
    report = R.build_run_report(
        queries, per_query, regressions,
        manifest=manifest, top_k=top_k,
        forbidden_window=forbidden_window,
        timings_warm_ms=timings_warm,
    )
    blob = R.run_report_to_dict(report)

    rss_mb = get_process_rss_mb()
    _tick("done", {"rss_mb": rss_mb, "p95_ms": p95})

    return blob, rss_mb


# ---------------------------------------------------------------------------
# Whole sweep
# ---------------------------------------------------------------------------

def run_reranker_ab_sweep(
    candidates: Sequence[RerankerCandidate],
    queries: Sequence[GradedQuery],
    baseline: BaselineScore,
    *,
    embedding_index_root: Path | str = DEFAULT_EMBEDDING_INDEX_ROOT,
    top_k: int = 10,
    forbidden_window: int = 5,
    device: str = "cpu",
    mode: str = "full",
    thresholds: GateThresholds = GateThresholds(),
    model_factory: Callable[[str], Any] | None = None,
    progress: Callable[[str, dict], None] | None = None,
) -> RerankerABReport:
    """Run every reranker candidate against the fixed embedding index,
    gate them, return RerankerABReport with Pareto-selected winner."""
    results: list[RerankerRunResult] = []

    for candidate in candidates:
        if progress:
            progress("candidate_start", {"candidate_id": candidate.candidate_id})
        blob, rss = run_one_reranker(
            candidate, queries,
            embedding_index_root=embedding_index_root,
            top_k=top_k, forbidden_window=forbidden_window,
            device=device, mode=mode, model_factory=model_factory,
            progress=progress,
        )
        score = aggregate_to_candidate_score(candidate, blob, rss_mb=rss)
        gate = evaluate_candidate(score, baseline, thresholds)
        results.append(RerankerRunResult(
            candidate=candidate,
            candidate_score=score,
            gate_result=gate,
            run_report_blob=blob,
            rss_after_run_mb=rss,
        ))
        if progress:
            progress(
                "candidate_done",
                {
                    "candidate_id": candidate.candidate_id,
                    "passed": gate.passed,
                    "primary_ndcg_macro": score.primary_ndcg_macro,
                },
            )

    # Pareto select among passers
    passers = [r for r in results if r.gate_result.passed]
    if passers:
        ordered = pareto_select(
            [r.candidate_score for r in passers], thresholds
        )
        pareto_ids = tuple(s.candidate_id for s in ordered)
        selected = pareto_ids[0]
        rationale = (
            f"{len(passers)}/{len(results)} reranker candidates passed the gate; "
            f"Pareto preference selected {selected!r}."
        )
    else:
        pareto_ids = ()
        selected = None
        rationale = (
            f"0/{len(results)} reranker candidates passed the gate; "
            "stay on baseline reranker (no upgrade)."
        )

    return RerankerABReport(
        baseline=baseline,
        thresholds=thresholds,
        embedding_index_root=str(embedding_index_root),
        candidates=tuple(results),
        pareto_order=pareto_ids,
        selected_candidate_id=selected,
        selection_rationale=rationale,
    )


def reranker_ab_report_to_dict(report: RerankerABReport) -> dict[str, Any]:
    """JSON-serialisable form for reranker_ab_report.json."""
    return {
        "baseline": {
            "primary_ndcg_macro": report.baseline.primary_ndcg_macro,
            "primary_ndcg_by_category": dict(report.baseline.primary_ndcg_by_category),
            "primary_ndcg_category_counts": dict(report.baseline.primary_ndcg_category_counts),
            "forbidden_rate_overall": report.baseline.forbidden_rate_overall,
            "hard_regression_failures": report.baseline.hard_regression_failures,
        },
        "thresholds": {
            "min_primary_uplift": report.thresholds.min_primary_uplift,
            "max_bucket_regression": report.thresholds.max_bucket_regression,
            "max_p95_warm_ms": report.thresholds.max_p95_warm_ms,
            "max_rss_mb": report.thresholds.max_rss_mb,
            "pareto_tolerance": report.thresholds.pareto_tolerance,
            "pareto_force_larger_above": report.thresholds.pareto_force_larger_above,
            "min_bucket_size_for_regression": report.thresholds.min_bucket_size_for_regression,
        },
        "embedding_index_root": report.embedding_index_root,
        "candidates": [
            {
                "candidate_id": r.candidate.candidate_id,
                "hf_model_id": r.candidate.hf_model_id,
                "approx_size_mb": r.candidate.approx_size_mb,
                "is_control": r.candidate.is_control,
                "high_memory_risk": r.candidate.high_memory_risk,
                "score": {
                    "primary_ndcg_macro": r.candidate_score.primary_ndcg_macro,
                    "primary_ndcg_by_category": dict(r.candidate_score.primary_ndcg_by_category),
                    "forbidden_rate_overall": r.candidate_score.forbidden_rate_overall,
                    "hard_regression_failures": r.candidate_score.hard_regression_failures,
                    "warm_p95_ms": r.candidate_score.warm_p95_ms,
                    "rss_mb": r.candidate_score.rss_mb,
                    "model_size_mb": r.candidate_score.model_size_mb,
                },
                "gate": {
                    "passed": r.gate_result.passed,
                    "failed_checks": list(r.gate_result.failed_checks),
                    "passed_checks": list(r.gate_result.passed_checks),
                    "diagnostics": r.gate_result.diagnostics,
                },
                "rss_after_run_mb": r.rss_after_run_mb,
                "run_report": r.run_report_blob,
            }
            for r in report.candidates
        ],
        "pareto_order": list(report.pareto_order),
        "selected_candidate_id": report.selected_candidate_id,
        "selection_rationale": report.selection_rationale,
    }
