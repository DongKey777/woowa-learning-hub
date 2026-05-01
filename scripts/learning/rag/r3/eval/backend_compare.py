"""Run qrel-backed R3 backend comparisons with trace-compatible output."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from scripts.learning.rag import indexer, searcher

from ..eval.metrics import (
    RerankerComparison,
    RetrievalEvaluationQuery,
    reranker_demotion_summary,
    retrieval_summary,
)
from ..eval.qrels import R3QueryJudgement, load_qrels
from ..eval.trace import R3Trace, write_jsonl
from ..query_plan import build_query_plan


SearchCallable = Callable[..., list[dict[str, Any]]]


@dataclass(frozen=True)
class BackendSpec:
    name: str
    backend: str
    index_root: Path | None = None
    use_reranker: bool | None = None
    modalities: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        blob = asdict(self)
        blob["index_root"] = str(self.index_root) if self.index_root is not None else None
        blob["modalities"] = list(self.modalities)
        return blob


def _hit_paths(hits: Iterable[dict[str, Any]]) -> tuple[str, ...]:
    paths: list[str] = []
    for hit in hits:
        path = hit.get("path")
        if isinstance(path, str) and path:
            paths.append(path)
    return tuple(paths)


def _trace_from_debug_or_hits(
    *,
    query: R3QueryJudgement,
    spec: BackendSpec,
    debug: dict[str, Any],
    hits: list[dict[str, Any]],
) -> R3Trace:
    if isinstance(debug.get("r3_trace"), dict):
        trace = R3Trace.from_dict(debug["r3_trace"])
        return R3Trace(
            trace_id=query.query_id,
            query_plan=trace.query_plan,
            candidates=trace.candidates,
            final_paths=trace.final_paths,
            stage_ms=trace.stage_ms,
            metadata={
                **trace.metadata,
                "backend_spec": spec.to_dict(),
                "qrels": [qrel.to_dict() for qrel in query.qrels],
                "forbidden_paths": list(query.forbidden_paths),
                "tags": list(query.tags),
            },
        )

    final_paths = _hit_paths(hits)
    return R3Trace(
        trace_id=query.query_id,
        query_plan=build_query_plan(query.prompt),
        final_paths=final_paths,
        metadata={
            "backend": spec.backend,
            "backend_spec": spec.to_dict(),
            "fused_paths": list(final_paths),
            "qrels": [qrel.to_dict() for qrel in query.qrels],
            "forbidden_paths": list(query.forbidden_paths),
            "tags": list(query.tags),
        },
    )


def _tag_value(tags: tuple[str, ...], prefix: str, default: str = "unknown") -> str:
    needle = f"{prefix}:"
    for tag in tags:
        if tag.startswith(needle):
            return tag[len(needle) :] or default
    return default


def _evaluation_query_from_trace(
    query: R3QueryJudgement,
    trace: R3Trace,
) -> RetrievalEvaluationQuery:
    fused_paths = trace.metadata.get("fused_paths")
    candidate_paths = (
        tuple(str(path) for path in fused_paths)
        if isinstance(fused_paths, list)
        else trace.final_paths
    )
    return RetrievalEvaluationQuery(
        query_id=query.query_id,
        language=trace.query_plan.language,
        level=_tag_value(query.tags, "level"),
        category=_tag_value(query.tags, "category"),
        primary_paths=tuple(sorted(query.primary_paths())),
        acceptable_paths=tuple(sorted(query.acceptable_paths())),
        forbidden_paths=query.forbidden_paths,
        candidate_paths=candidate_paths,
        final_paths=trace.final_paths,
    )


def run_backend(
    spec: BackendSpec,
    qrels: list[R3QueryJudgement],
    *,
    top_k: int = 100,
    windows: tuple[int, ...] = (20, 50, 100),
    forbidden_window: int = 5,
    search_fn: SearchCallable = searcher.search,
) -> dict[str, Any]:
    traces: list[R3Trace] = []
    evaluation_queries: list[RetrievalEvaluationQuery] = []
    reranker_comparisons: list[RerankerComparison] = []

    for query in qrels:
        debug: dict[str, Any] = {}
        kwargs: dict[str, Any] = {
            "backend": spec.backend,
            "top_k": top_k,
            "debug": debug,
            "use_reranker": spec.use_reranker,
        }
        if spec.index_root is not None:
            kwargs["index_root"] = spec.index_root
        if spec.modalities:
            kwargs["modalities"] = spec.modalities
        hits = search_fn(query.prompt, **kwargs)
        trace = _trace_from_debug_or_hits(
            query=query,
            spec=spec,
            debug=debug,
            hits=hits,
        )
        traces.append(trace)
        evaluation_query = _evaluation_query_from_trace(query, trace)
        evaluation_queries.append(evaluation_query)
        fused_paths = trace.metadata.get("fused_paths")
        if spec.use_reranker and isinstance(fused_paths, list):
            reranker_comparisons.append(
                RerankerComparison(
                    query_id=query.query_id,
                    language=evaluation_query.language,
                    level=evaluation_query.level,
                    category=evaluation_query.category,
                    primary_paths=evaluation_query.primary_paths,
                    before_paths=tuple(str(path) for path in fused_paths),
                    after_paths=trace.final_paths,
                )
            )

    result = {
        "backend": spec.name,
        "spec": spec.to_dict(),
        "query_count": len(qrels),
        "summary": retrieval_summary(
            evaluation_queries,
            windows=windows,
            forbidden_window=forbidden_window,
        ),
        "traces": [trace.to_dict() for trace in traces],
    }
    if spec.use_reranker:
        result["reranker_demotion"] = reranker_demotion_summary(reranker_comparisons)
    return result


def run_backend_comparison(
    specs: list[BackendSpec],
    qrels: list[R3QueryJudgement],
    *,
    top_k: int = 100,
    windows: tuple[int, ...] = (20, 50, 100),
    forbidden_window: int = 5,
    search_fn: SearchCallable = searcher.search,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "top_k": top_k,
        "windows": list(windows),
        "forbidden_window": forbidden_window,
        "backends": [
            run_backend(
                spec,
                qrels,
                top_k=top_k,
                windows=windows,
                forbidden_window=forbidden_window,
                search_fn=search_fn,
            )
            for spec in specs
        ],
    }


def write_backend_traces(report: dict[str, Any], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for backend in report.get("backends", []):
        name = str(backend.get("backend") or "backend")
        trace_path = output_dir / f"{name}.jsonl"
        traces = [R3Trace.from_dict(blob) for blob in backend.get("traces", [])]
        write_jsonl(traces, trace_path)
        paths.append(trace_path)
    return paths


def _parse_backend(value: str, default_index_root: Path) -> BackendSpec:
    parts = value.split(":")
    name = parts[0]
    backend = parts[1] if len(parts) > 1 else name
    if backend not in {"auto", "legacy", "lance", "r3"}:
        raise argparse.ArgumentTypeError(f"unknown backend in {value!r}: {backend}")
    return BackendSpec(name=name, backend=backend, index_root=default_index_root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qrels", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--trace-dir", type=Path, default=None)
    parser.add_argument("--index-root", type=Path, default=indexer.DEFAULT_INDEX_ROOT)
    parser.add_argument(
        "--backend",
        action="append",
        default=None,
        help="Backend spec as name or name:backend. Repeatable. Default: r3.",
    )
    parser.add_argument("--top-k", type=int, default=100)
    parser.add_argument("--window", type=int, action="append", default=None)
    parser.add_argument("--forbidden-window", type=int, default=5)
    parser.add_argument("--use-reranker", action="store_true")
    args = parser.parse_args(argv)

    windows = tuple(args.window or [20, 50, 100])
    specs = [
        _parse_backend(value, args.index_root)
        for value in (args.backend or ["r3"])
    ]
    if args.use_reranker:
        specs = [
            BackendSpec(
                name=spec.name,
                backend=spec.backend,
                index_root=spec.index_root,
                use_reranker=True,
                modalities=spec.modalities,
            )
            for spec in specs
        ]
    report = run_backend_comparison(
        specs,
        load_qrels(args.qrels),
        top_k=args.top_k,
        windows=windows,
        forbidden_window=args.forbidden_window,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    if args.trace_dir is not None:
        write_backend_traces(report, args.trace_dir)
    print(f"wrote R3 backend comparison report to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
