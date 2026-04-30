"""A/B sweep orchestrator — build index, retrieve, evaluate, gate.

Plan §P2.1 — for each candidate:

1. Build a separate eval index at ``state/cs_rag_eval/<candidate_id>/``
   via index_builder.build_eval_index. Skip if already present and
   ``force_rebuild=False`` (lets repeat runs resume cheaply).
2. Bind ABRetriever (scoped query-embedder swap) and call
   runner.evaluate_queries with the production runner.
3. Aggregate the per-query metrics into a CandidateScore for the gate.
4. (Caller) compute BaselineScore from the previously committed
   baseline_quality.json and run gate.evaluate_candidate per
   candidate, then pareto_select among passers.

Heavy ML deps (sentence_transformers, torch) are imported lazily
inside the model_factory callsite — this module itself stays
import-cheap so unit tests can exercise the orchestration logic with
fakes.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import runner as R
from .ab_retriever import ABRetriever
from .candidates import EmbeddingCandidate
from .cleanup import CleanupReport, cleanup_candidate_artifacts
from .dataset import GradedQuery
from .gate import (
    BaselineScore,
    CandidateScore,
    GateResult,
    GateThresholds,
    evaluate_candidate,
    pareto_select,
)
from .index_builder import build_eval_index, eval_index_root_for
from .manifest import FusionWeights, RunManifest
from .precheck import get_process_rss_mb


DEFAULT_AB_BASE_DIR = Path("state/cs_rag_eval")
"""Where each candidate's index lives. Configurable per call."""


# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CandidateRunResult:
    """Everything one candidate produced — used to assemble the
    AB report and the gate decision."""

    candidate: EmbeddingCandidate
    candidate_score: CandidateScore
    gate_result: GateResult
    run_report_blob: dict[str, Any]  # full RunReport JSON
    rss_after_run_mb: float


@dataclass(frozen=True)
class ABReport:
    """Top-level structure for embedding_ab_report.json."""

    baseline: BaselineScore
    thresholds: GateThresholds
    candidates: tuple[CandidateRunResult, ...]
    pareto_order: tuple[str, ...]  # candidate_ids in preferred order
    selected_candidate_id: str | None
    selection_rationale: str


# ---------------------------------------------------------------------------
# Aggregate RunReport → CandidateScore
# ---------------------------------------------------------------------------

def aggregate_to_candidate_score(
    candidate: EmbeddingCandidate,
    run_report_blob: dict[str, Any],
    *,
    rss_mb: float,
    bucket_axis: str = "category",
) -> CandidateScore:
    """Project a RunReport blob into the gate's CandidateScore shape.

    ``bucket_axis`` defaults to "category" because plan §P2.1 uses
    category-macro as the headline. Other axes are still in the run
    report under macro_reports["primary_ndcg"]["difficulty"|...].

    Raises KeyError if the run report shape is missing fields — the
    runner contract guarantees them, so a missing field is a bug
    upstream not a recoverable case.
    """
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


def baseline_from_quality_blob(
    blob: dict[str, Any],
    *,
    bucket_axis: str = "category",
) -> BaselineScore:
    """Project the committed baseline_quality.json into BaselineScore.

    blob is the parsed reports/rag_eval/baseline_quality.json.
    """
    macro = blob["macro_reports"]["primary_ndcg"][bucket_axis]
    overall = blob["overall_means"]
    summary = blob["regression_summary"]
    return BaselineScore(
        primary_ndcg_macro=float(macro["macro_mean"]),
        primary_ndcg_by_category=dict(macro["per_bucket_mean"]),
        primary_ndcg_category_counts=dict(macro["per_bucket_count"]),
        forbidden_rate_overall=float(overall.get("forbidden_rate", 0.0)),
        hard_regression_failures=int(summary["failed_count"]),
    )


# ---------------------------------------------------------------------------
# Per-candidate run
# ---------------------------------------------------------------------------

@dataclass
class _Timing:
    cold_ms: float
    warm_ms: list[float] = field(default_factory=list)


def run_one_candidate(
    candidate: EmbeddingCandidate,
    queries: Sequence[GradedQuery],
    *,
    base_dir: Path | str = DEFAULT_AB_BASE_DIR,
    corpus_root: Path | str | None = None,
    top_k: int = 10,
    forbidden_window: int = 5,
    device: str = "cpu",
    mode: str = "full",
    backend: str = "legacy",
    modalities: list[str] | tuple[str, ...] | None = None,
    batch_size: int = 32,
    model_factory: Callable[[str, int], Any] | None = None,
    force_rebuild: bool = False,
    progress: Callable[[str, dict], None] | None = None,
) -> tuple[dict[str, Any], float]:
    """Build/refresh the candidate's index, retrieve, evaluate.

    Returns ``(run_report_blob, rss_after_run_mb)``. Caller decides
    how to compose this with baseline / thresholds.

    Args:
        candidate: which model + dim to evaluate
        queries: shared fixture
        base_dir: parent dir for state/cs_rag_eval/<id>/
        top_k / forbidden_window: forwarded to evaluate_queries
        device: forwarded to model_factory + manifest
        mode: searcher mode for this run
        backend / modalities: forwarded to ABRetriever and captured in
            the run manifest. Defaults preserve the legacy v2 SQLite/NPZ
            embedding A/B path.
        model_factory: callable(hf_model_id, embed_dim) -> encoder.
            Tests pass a fake; production uses
            cli_rag_eval._default_st_factory(device).
        force_rebuild: rebuild index even when the directory already
            has a manifest. Default False so repeat runs are cheap.
        progress: optional ``(stage, info)`` callback.

    Manifest semantics: `latency_p95_warm` is computed from
    per-query warm timings; `cold_start_ms` covers model load only
    (the first encode call sits outside the timed loop because
    runner.evaluate_queries times retrieve_fn calls including the
    first one — that's "warm" by our convention here since the model
    is already loaded).
    """
    if not queries:
        raise ValueError("run_one_candidate: queries is empty")
    if model_factory is None:
        raise ValueError(
            "run_one_candidate: model_factory must be provided "
            "(production: cli_rag_eval._default_st_factory(device))"
        )

    base = Path(base_dir)
    index_root = base / candidate.index_dir_name()

    def _tick(stage: str, info: dict | None = None) -> None:
        if progress is not None:
            progress(stage, info or {})

    # 1. Load (or build) index
    manifest_path = index_root / "manifest.json"
    if force_rebuild or not manifest_path.exists():
        _tick("model_load_for_build", {"candidate": candidate.candidate_id})
        t0 = time.perf_counter()
        builder_model = model_factory(candidate.hf_model_id, candidate.embed_dim)
        cold_load_ms = (time.perf_counter() - t0) * 1000.0
        _tick("model_loaded", {"cold_ms": cold_load_ms})

        _tick("build_index", {"index_root": str(index_root), "batch_size": batch_size})
        build_eval_index(
            model=builder_model,
            model_id=candidate.hf_model_id,
            embed_dim=candidate.embed_dim,
            index_root=index_root,
            corpus_root=corpus_root,
            batch_size=batch_size,
            progress=progress,
        )
        # The builder model is also used as the query embedder below.
        query_model = builder_model
    else:
        _tick("reuse_index", {"index_root": str(index_root)})
        t0 = time.perf_counter()
        query_model = model_factory(candidate.hf_model_id, candidate.embed_dim)
        cold_load_ms = (time.perf_counter() - t0) * 1000.0

    # 2. Bind retriever and run evaluate_queries
    _tick("retrieve_evaluate", {"top_k": top_k})
    with ABRetriever(
        index_root=index_root,
        model=query_model,
        model_id=candidate.hf_model_id,
        embed_dim=candidate.embed_dim,
        top_k=top_k,
        mode=mode,
        backend=backend,
        modalities=modalities,
    ) as retrieve:
        per_query, regressions, timings_warm = R.evaluate_queries(
            queries, retrieve,
            top_k=top_k, forbidden_window=forbidden_window,
        )

    # 3. Compute warm percentiles for the manifest
    if timings_warm:
        sorted_t = sorted(timings_warm)
        p50 = sorted_t[len(sorted_t) // 2]
        p95_idx = max(0, min(len(sorted_t) - 1,
                              int(round(0.95 * (len(sorted_t) - 1)))))
        p95 = sorted_t[p95_idx]
    else:
        p50 = 0.0
        p95 = 0.0

    # 4. Build manifest + run report
    raw_index_manifest = json.loads(manifest_path.read_text())
    manifest = RunManifest(
        corpus_hash=raw_index_manifest["corpus_hash"],
        index_version=int(raw_index_manifest["index_version"]),
        embedding_model=candidate.hf_model_id,
        model_revision=None,
        embedding_dim=candidate.embed_dim,
        device=device,
        reranker_model=None,  # P3.1 will fill this; P2.1 sweep is dense+FTS only
        fusion_weights=FusionWeights.default(),
        top_k=top_k,
        mode=mode,
        latency_p50_warm=p50,
        latency_p95_warm=p95,
        cold_start_ms=cold_load_ms,
        backend=backend,
        modalities=tuple(modalities or ()),
        encoder=dict(raw_index_manifest.get("encoder") or {}),
        lancedb=dict(raw_index_manifest.get("lancedb") or {}),
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

def run_ab_sweep(
    candidates: Sequence[EmbeddingCandidate],
    queries: Sequence[GradedQuery],
    baseline: BaselineScore,
    *,
    base_dir: Path | str = DEFAULT_AB_BASE_DIR,
    corpus_root: Path | str | None = None,
    top_k: int = 10,
    forbidden_window: int = 5,
    device: str = "cpu",
    mode: str = "full",
    backend: str = "legacy",
    modalities: list[str] | tuple[str, ...] | None = None,
    batch_size: int = 32,
    thresholds: GateThresholds = GateThresholds(),
    model_factory: Callable[[str, int], Any] | None = None,
    force_rebuild: bool = False,
    cleanup_after: bool = False,
    progress: Callable[[str, dict], None] | None = None,
) -> ABReport:
    """Run every candidate, gate them, return an ABReport.

    The report carries the full per-candidate run report blobs so the
    caller can serialise to embedding_ab_report.json without losing
    detail.
    """
    results: list[CandidateRunResult] = []

    for candidate in candidates:
        if progress:
            progress("candidate_start", {"candidate_id": candidate.candidate_id})
        blob, rss = run_one_candidate(
            candidate, queries,
            base_dir=base_dir, corpus_root=corpus_root,
            top_k=top_k, forbidden_window=forbidden_window,
            device=device, mode=mode, backend=backend, modalities=modalities,
            batch_size=batch_size,
            model_factory=model_factory,
            force_rebuild=force_rebuild, progress=progress,
        )
        score = aggregate_to_candidate_score(candidate, blob, rss_mb=rss)
        gate = evaluate_candidate(score, baseline, thresholds)
        results.append(CandidateRunResult(
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

        # Per-candidate cleanup (disk pressure mitigation). Run AFTER
        # the run report has been computed and aggregated, so the
        # report's run_report_blob is already in memory and the on-disk
        # index is no longer needed.
        if cleanup_after:
            cl = cleanup_candidate_artifacts(
                candidate, base_dir=base_dir, drop_hf_cache=True
            )
            if progress:
                progress("candidate_cleanup", {
                    "candidate_id": candidate.candidate_id,
                    "freed_mb": cl.total_freed_mb,
                    "skipped_hf_cache": cl.skipped_hf_cache_due_to_control,
                })

    # Pareto select among passers
    passers = [r for r in results if r.gate_result.passed]
    if passers:
        ordered = pareto_select(
            [r.candidate_score for r in passers], thresholds
        )
        pareto_ids = tuple(s.candidate_id for s in ordered)
        selected = pareto_ids[0]
        rationale = (
            f"{len(passers)}/{len(results)} candidates passed the gate; "
            f"Pareto preference selected {selected!r}."
        )
    else:
        pareto_ids = ()
        selected = None
        rationale = (
            f"0/{len(results)} candidates passed the gate; "
            "stay on baseline (no upgrade)."
        )

    return ABReport(
        baseline=baseline,
        thresholds=thresholds,
        candidates=tuple(results),
        pareto_order=pareto_ids,
        selected_candidate_id=selected,
        selection_rationale=rationale,
    )


def ab_report_to_dict(report: ABReport) -> dict[str, Any]:
    """JSON-serialisable form of an ABReport for embedding_ab_report.json."""
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
        "candidates": [
            {
                "candidate_id": r.candidate.candidate_id,
                "hf_model_id": r.candidate.hf_model_id,
                "embed_dim": r.candidate.embed_dim,
                "approx_size_mb": r.candidate.approx_size_mb,
                "is_control": r.candidate.is_control,
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
