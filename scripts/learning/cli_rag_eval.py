"""CLI entry point for the RAG evaluation harness.

Modes (plan §P1.1, §8 PR-1 scope):

- ``--fast``: schema/fixture/manifest validation only. Loads the
  legacy or graded fixture, converts it to GradedQuery, and asserts
  that all 338 entries pass the dataclass + JSON Schema gates. No
  live retrieval, no ML deps required at runtime. CI fast contract.

- ``--baseline-only``: live retrieval against the current production
  searcher (MiniLM-L12 + existing reranker + RRF k=60). Emits two
  artifacts (plan §P0.1):
    * reports/rag_eval/baseline_quality.json — graded nDCG, primary
      nDCG, MRR, hit/recall, bucket macro, run manifest. Repo-committed.
    * state/cs_rag/baseline_machine.json — latency P50/P95, cold start,
      RSS. Gitignored (machine-dependent).

Higher modes (--regression, --full) land in PR-2+; --baseline-only is
sufficient for the PR-1 baseline gate.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "cs_rag_golden_queries.json"
DEFAULT_QUALITY_OUT = REPO_ROOT / "reports" / "rag_eval" / "baseline_quality.json"
DEFAULT_MACHINE_OUT = REPO_ROOT / "state" / "cs_rag" / "baseline_machine.json"


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rag-eval",
        description=(
            "Evaluate the CS RAG pipeline. --fast for CI contract checks, "
            "--baseline-only to measure the current production stack."
        ),
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--fast",
        action="store_true",
        help="Schema / fixture / manifest validation only (no retrieval).",
    )
    mode.add_argument(
        "--baseline-only",
        action="store_true",
        help="Measure current production stack and emit baseline_quality.json.",
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        default=DEFAULT_FIXTURE,
        help=f"Path to legacy or graded fixture (default: {DEFAULT_FIXTURE}).",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="top-K window for nDCG/hit/recall (default: 10).",
    )
    parser.add_argument(
        "--forbidden-window",
        type=int,
        default=5,
        help="top-K slots to scan for forbidden_paths (default: 5).",
    )
    parser.add_argument(
        "--out-quality",
        type=Path,
        default=DEFAULT_QUALITY_OUT,
        help=f"Quality report path (default: {DEFAULT_QUALITY_OUT}).",
    )
    parser.add_argument(
        "--out-machine",
        type=Path,
        default=DEFAULT_MACHINE_OUT,
        help=f"Machine-dependent report path (default: {DEFAULT_MACHINE_OUT}).",
    )
    parser.add_argument(
        "--device",
        default="auto",
        choices=("auto", "cpu", "mps", "cuda"),
        help="Embedder device (default: auto).",
    )
    return parser


# ---------------------------------------------------------------------------
# Fixture loading (legacy or graded)
# ---------------------------------------------------------------------------

def load_queries(fixture_path: Path) -> list:
    """Load and convert a fixture into GradedQuery list.

    Detects legacy vs graded format by inspecting the first query's
    keys. Legacy uses ``id`` + ``expected_path``; graded uses
    ``query_id`` + ``qrels``.
    """
    from scripts.learning.rag.eval.dataset import (
        load_graded_fixture,
        convert_legacy_payload,
    )

    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    queries_node = payload.get("queries") if isinstance(payload, dict) else payload
    if not queries_node:
        raise ValueError(f"fixture has no queries: {fixture_path}")

    sample = queries_node[0]
    if "qrels" in sample:
        return load_graded_fixture(fixture_path)
    if "expected_path" in sample:
        if isinstance(payload, dict):
            return convert_legacy_payload(payload)
        return convert_legacy_payload({"queries": payload})

    raise ValueError(
        f"unrecognised fixture format (missing qrels/expected_path): "
        f"{sorted(sample.keys())}"
    )


# ---------------------------------------------------------------------------
# Mode: --fast
# ---------------------------------------------------------------------------

def run_fast(args: argparse.Namespace) -> int:
    """Schema / fixture / manifest validation only.

    Loads the fixture, converts it (legacy → graded if needed),
    confirms every query has a primary qrel, confirms unique ids,
    and walks the bucket inference output to ensure ``unknown``
    category rate stays below the 10% threshold the dataset tests
    enforce. Exits 0 on PASS, 1 on FAIL.
    """
    print(f"[rag-eval --fast] fixture={args.fixture}", file=sys.stderr)

    queries = load_queries(args.fixture)
    total = len(queries)
    if total == 0:
        print("FAIL: fixture has no queries", file=sys.stderr)
        return 1

    failures: list[str] = []

    seen_ids: set[str] = set()
    for q in queries:
        if q.query_id in seen_ids:
            failures.append(f"duplicate id: {q.query_id}")
        seen_ids.add(q.query_id)
        if not q.primary_paths():
            failures.append(f"{q.query_id}: no primary qrel")

    unknown_categories = sum(1 for q in queries if q.bucket.category == "unknown")
    unknown_ratio = unknown_categories / total
    print(
        f"  total queries: {total}",
        f"  unknown categories: {unknown_categories} ({unknown_ratio:.1%})",
        sep="\n",
        file=sys.stderr,
    )
    if unknown_ratio >= 0.10:
        failures.append(
            f"unknown category rate {unknown_ratio:.1%} ≥ 10% threshold"
        )

    if failures:
        print("FAIL:", file=sys.stderr)
        for msg in failures:
            print(f"  - {msg}", file=sys.stderr)
        return 1

    print("PASS", file=sys.stderr)
    return 0


# ---------------------------------------------------------------------------
# Mode: --baseline-only (live retrieval)
# ---------------------------------------------------------------------------

def _resolve_device(arg: str) -> str:
    """Resolve 'auto' to 'mps' on Apple Silicon (when MPS available)
    or 'cpu' otherwise. Other arg values pass through."""
    if arg != "auto":
        return arg
    try:
        import platform

        import torch  # type: ignore

        if (
            platform.system() == "Darwin"
            and torch.backends.mps.is_available()
        ):
            return "mps"
    except Exception:
        pass
    return "cpu"


def _live_retrieve_factory(
    *, top_k: int, device: str
) -> Callable[[Any], Sequence[str]]:
    """Build a retrieve_fn that calls scripts.learning.rag.searcher.search.

    Note: searcher.search itself decides how to embed. This factory
    sets WOOWA_RAG_DEVICE for downstream code that honours it (added
    in P2.1) but does not currently force device — searcher's existing
    cache controls that. Recorded in the manifest for traceability.
    """
    import os

    os.environ["WOOWA_RAG_DEVICE"] = device

    from scripts.learning.rag import searcher  # late import: heavy ML deps

    def retrieve(query) -> list[str]:
        hits = searcher.search(
            query.prompt,
            learning_points=list(query.learning_points),
            top_k=top_k,
            mode=query.mode,
            experience_level=query.experience_level,
        )
        return [h["path"] for h in hits]

    return retrieve


def run_baseline_only(args: argparse.Namespace) -> int:
    """Run live retrieval against the current stack and emit two
    artifacts. Returns 0 on success, 1 on hard regression failure
    (caller can flip to a non-blocking exit if desired)."""
    from scripts.learning.rag import indexer
    from scripts.learning.rag.eval import runner as R
    from scripts.learning.rag.eval.manifest import (
        FusionWeights,
        RunManifest,
        manifest_to_dict,
    )

    print(
        f"[rag-eval --baseline-only] fixture={args.fixture}",
        f"  top_k={args.top_k}  forbidden_window={args.forbidden_window}",
        sep="\n",
        file=sys.stderr,
    )

    queries = load_queries(args.fixture)
    print(f"  loaded {len(queries)} queries", file=sys.stderr)

    # Index manifest → corpus_hash, embed_model identity
    readiness = indexer.is_ready()
    if readiness.state != "ready":
        print(
            f"FAIL: index not ready (state={readiness.state}, "
            f"reason={readiness.reason}). Run bin/cs-index-build.",
            file=sys.stderr,
        )
        return 2

    # Pull manifest fields off disk (don't hardcode)
    manifest_path = indexer.DEFAULT_INDEX_ROOT / indexer.MANIFEST_NAME
    raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    device = _resolve_device(args.device)

    # Cold start: time the first retrieval so we can record cold_start_ms
    cold_started_at = time.perf_counter()
    retrieve = _live_retrieve_factory(top_k=args.top_k, device=device)
    # The factory itself is light; the heavy import happens here.
    # We still wait until the first retrieve_fn call inside evaluate_queries
    # to capture model load time.

    if queries:
        warmup_query = queries[0]
        retrieve(warmup_query)
        cold_start_ms = (time.perf_counter() - cold_started_at) * 1000.0
    else:
        cold_start_ms = 0.0

    per_query, regressions, timings_warm = R.evaluate_queries(
        queries, retrieve,
        top_k=args.top_k, forbidden_window=args.forbidden_window,
    )

    p50 = statistics.quantiles(timings_warm, n=2)[0] if len(timings_warm) >= 2 else (
        timings_warm[0] if timings_warm else 0.0
    )
    p95 = (
        statistics.quantiles(timings_warm, n=20)[18]
        if len(timings_warm) >= 20
        else max(timings_warm) if timings_warm else 0.0
    )

    from scripts.learning.rag.reranker import RERANK_MODEL

    manifest = RunManifest(
        corpus_hash=raw_manifest["corpus_hash"],
        index_version=int(raw_manifest["index_version"]),
        embedding_model=raw_manifest["embed_model"],
        model_revision=None,
        embedding_dim=int(raw_manifest["embed_dim"]),
        device=device,
        reranker_model=RERANK_MODEL,
        fusion_weights=FusionWeights.default(),
        top_k=args.top_k,
        mode="full",
        latency_p50_warm=p50,
        latency_p95_warm=p95,
        cold_start_ms=cold_start_ms,
    )

    report = R.build_run_report(
        queries, per_query, regressions,
        manifest=manifest, top_k=args.top_k,
        forbidden_window=args.forbidden_window,
        timings_warm_ms=timings_warm,
    )
    blob = R.run_report_to_dict(report)

    # Split artifacts: quality (committed) vs machine (gitignored)
    quality_view = {
        "manifest": {
            k: v
            for k, v in blob["manifest"].items()
            if k not in ("device", "latency_p50_warm", "latency_p95_warm", "cold_start_ms")
        },
        "top_k": blob["top_k"],
        "forbidden_window": blob["forbidden_window"],
        "overall_means": blob["overall_means"],
        "macro_reports": blob["macro_reports"],
        "regression_summary": blob["regression_summary"],
        "regressions": blob["regressions"],
        "per_query": blob["per_query"],
    }
    machine_view = {
        "manifest_machine_subset": {
            "device": blob["manifest"]["device"],
            "latency_p50_warm": blob["manifest"]["latency_p50_warm"],
            "latency_p95_warm": blob["manifest"]["latency_p95_warm"],
            "cold_start_ms": blob["manifest"]["cold_start_ms"],
        },
        "timing_warm_per_query_ms": blob["timing_warm_per_query_ms"],
    }

    args.out_quality.parent.mkdir(parents=True, exist_ok=True)
    args.out_machine.parent.mkdir(parents=True, exist_ok=True)
    args.out_quality.write_text(
        json.dumps(quality_view, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    args.out_machine.write_text(
        json.dumps(machine_view, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(
        f"  wrote: {args.out_quality.relative_to(REPO_ROOT)}",
        f"  wrote: {args.out_machine.relative_to(REPO_ROOT)}",
        sep="\n",
        file=sys.stderr,
    )

    summary = blob["regression_summary"]
    print(
        f"  primary_nDCG@{args.top_k}: {blob['overall_means']['primary_ndcg']:.4f}",
        f"  graded_nDCG@{args.top_k}:  {blob['overall_means']['graded_ndcg']:.4f}",
        f"  MRR:  {blob['overall_means']['mrr']:.4f}",
        f"  hit:  {blob['overall_means']['hit']:.4f}",
        f"  recall: {blob['overall_means']['recall']:.4f}",
        f"  hard regression: {summary['passed_count']}/{summary['total']} passed",
        sep="\n",
        file=sys.stderr,
    )

    return 0 if summary["all_passed"] else 1


# ---------------------------------------------------------------------------
# Entry
# ---------------------------------------------------------------------------

def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.fast:
        return run_fast(args)
    if args.baseline_only:
        return run_baseline_only(args)
    parser.error("no mode selected")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
