"""Modal ablation runner for the LanceDB/bge-m3 retrieval stack.

H7 evaluates retrieval quality by enabling subsets of the four LanceDB
modalities: FTS, dense, sparse rescore, and ColBERT MaxSim rescore.
The runner intentionally reuses ``runner.evaluate_queries`` and
``ABRetriever`` so every modality combination gets the same graded qrels,
bucket macro reporting, hard-regression checks, and scoped encoder binding.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path
from typing import Any

from scripts.learning.rag import indexer

from . import runner as R
from .ab_retriever import ABRetriever
from .dataset import GradedQuery
from .manifest import FusionWeights, RunManifest

CANONICAL_MODALITIES = ("fts", "dense", "sparse", "colbert")


@dataclass(frozen=True)
class AblationRunResult:
    modalities: tuple[str, ...]
    run_report_blob: dict[str, Any]
    primary_ndcg_macro: float
    latency_p95_warm: float
    hard_regression_failures: int


@dataclass(frozen=True)
class AblationReport:
    index_root: str
    split: str
    query_count: int
    top_k: int
    forbidden_window: int
    mode: str
    runs: tuple[AblationRunResult, ...]
    best_modalities: tuple[str, ...] | None
    selection_rationale: str


def default_modality_sets() -> tuple[tuple[str, ...], ...]:
    """Return H7's singleton + pairwise + full modality schedule.

    Sparse and ColBERT are currently rescore-only in ``searcher.py``;
    their singleton rows are still measured because a zero-hit row is a
    useful proof that the modality does not provide discovery by itself yet.
    """
    out: list[tuple[str, ...]] = []
    out.extend((m,) for m in CANONICAL_MODALITIES)
    out.extend(tuple(combo) for combo in combinations(CANONICAL_MODALITIES, 2))
    out.append(CANONICAL_MODALITIES)
    return tuple(out)


def normalize_modality_set(value: Sequence[str]) -> tuple[str, ...]:
    """Validate and canonicalise one modality subset."""
    if not value:
        raise ValueError("modality set must be non-empty")
    unknown = [m for m in value if m not in CANONICAL_MODALITIES]
    if unknown:
        raise ValueError(f"unknown modalities: {unknown!r}")
    seen: set[str] = set()
    ordered: list[str] = []
    for modality in CANONICAL_MODALITIES:
        if modality in value and modality not in seen:
            ordered.append(modality)
            seen.add(modality)
    return tuple(ordered)


def parse_modality_sets(values: Sequence[str] | None) -> tuple[tuple[str, ...], ...]:
    """Parse CLI values like ``fts,dense`` into canonical modality tuples."""
    if not values:
        return default_modality_sets()
    parsed: list[tuple[str, ...]] = []
    for raw in values:
        parts = [part.strip() for part in raw.split(",") if part.strip()]
        parsed.append(normalize_modality_set(parts))
    return tuple(dict.fromkeys(parsed))


def _p50_p95(values: Sequence[float]) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    sorted_values = sorted(values)
    p50 = sorted_values[len(sorted_values) // 2]
    p95_idx = max(
        0,
        min(len(sorted_values) - 1, int(round(0.95 * (len(sorted_values) - 1)))),
    )
    return p50, sorted_values[p95_idx]


def _macro_primary(blob: dict[str, Any]) -> float:
    macro = blob["macro_reports"]["primary_ndcg"]["category"]
    return float(macro["macro_mean"])


def _best_run(runs: Sequence[AblationRunResult]) -> AblationRunResult | None:
    if not runs:
        return None
    return sorted(
        runs,
        key=lambda run: (
            -run.primary_ndcg_macro,
            run.hard_regression_failures,
            run.latency_p95_warm,
            len(run.modalities),
            run.modalities,
        ),
    )[0]


def run_modality_ablation(
    queries: Sequence[GradedQuery],
    *,
    index_root: Path | str,
    encoder: Any,
    modality_sets: Sequence[Sequence[str]] | None = None,
    top_k: int = 10,
    forbidden_window: int = 5,
    device: str = "cpu",
    mode: str = "full",
    split: str = "full",
    embedding_dim: int = 1024,
    progress=None,
) -> AblationReport:
    """Evaluate every requested modality subset against one LanceDB index."""
    query_list = list(queries)
    if not query_list:
        raise ValueError("run_modality_ablation: queries is empty")

    root = Path(index_root)
    manifest = indexer.read_manifest_v3(root)
    encoder_info = dict(manifest.get("encoder") or {})
    lancedb_info = dict(manifest.get("lancedb") or {})
    model_id = str(encoder_info.get("model_id") or getattr(encoder, "model_id", ""))
    model_version = str(encoder_info.get("model_version") or "")
    if not model_id:
        raise ValueError("run_modality_ablation: index manifest missing encoder.model_id")

    def _tick(stage: str, info: dict | None = None) -> None:
        if progress is not None:
            progress(stage, info or {})

    runs: list[AblationRunResult] = []
    for modalities in modality_sets or default_modality_sets():
        mods = normalize_modality_set(modalities)
        _tick("ablation_start", {"modalities": list(mods)})
        with ABRetriever(
            index_root=root,
            model=encoder,
            model_id=model_id,
            embed_dim=embedding_dim,
            top_k=top_k,
            mode=mode,
            backend="lance",
            modalities=mods,
        ) as retrieve:
            per_query, regressions, timings = R.evaluate_queries(
                query_list,
                retrieve,
                top_k=top_k,
                forbidden_window=forbidden_window,
            )

        p50, p95 = _p50_p95(timings)
        run_manifest = RunManifest(
            corpus_hash=str(manifest["corpus_hash"]),
            index_version=int(manifest["index_version"]),
            embedding_model=model_id,
            model_revision=model_version or None,
            embedding_dim=embedding_dim,
            device=device,
            reranker_model=None,
            fusion_weights=FusionWeights.default(),
            top_k=top_k,
            mode=mode,
            latency_p50_warm=p50,
            latency_p95_warm=p95,
            cold_start_ms=0.0,
            backend="lance",
            modalities=mods,
            encoder=encoder_info,
            lancedb=lancedb_info,
        )
        run_report = R.build_run_report(
            query_list,
            per_query,
            regressions,
            manifest=run_manifest,
            top_k=top_k,
            forbidden_window=forbidden_window,
            timings_warm_ms=timings,
        )
        blob = R.run_report_to_dict(run_report)
        result = AblationRunResult(
            modalities=mods,
            run_report_blob=blob,
            primary_ndcg_macro=_macro_primary(blob),
            latency_p95_warm=p95,
            hard_regression_failures=int(blob["regression_summary"]["failed_count"]),
        )
        runs.append(result)
        _tick(
            "ablation_done",
            {
                "modalities": list(mods),
                "primary_ndcg_macro": result.primary_ndcg_macro,
                "p95_ms": p95,
            },
        )

    best = _best_run(runs)
    if best is None:
        rationale = "no modality run was evaluated"
    else:
        rationale = (
            "selected by primary_nDCG_macro, then hard-regression count, "
            f"latency, and smaller modality set: {','.join(best.modalities)}"
        )
    return AblationReport(
        index_root=str(root),
        split=split,
        query_count=len(query_list),
        top_k=top_k,
        forbidden_window=forbidden_window,
        mode=mode,
        runs=tuple(runs),
        best_modalities=best.modalities if best else None,
        selection_rationale=rationale,
    )


def ablation_report_to_dict(report: AblationReport) -> dict[str, Any]:
    return {
        "index_root": report.index_root,
        "split": report.split,
        "query_count": report.query_count,
        "top_k": report.top_k,
        "forbidden_window": report.forbidden_window,
        "mode": report.mode,
        "runs": [
            {
                "modalities": list(run.modalities),
                "primary_ndcg_macro": run.primary_ndcg_macro,
                "latency_p95_warm": run.latency_p95_warm,
                "hard_regression_failures": run.hard_regression_failures,
                "run_report": run.run_report_blob,
            }
            for run in report.runs
        ],
        "best_modalities": list(report.best_modalities)
        if report.best_modalities
        else None,
        "selection_rationale": report.selection_rationale,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
