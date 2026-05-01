"""Probe Qdrant local mode against the current R3 qrel suite.

This is an optional backend spike, not a production dependency.  It reads the
current LanceDB v3 artifact, mirrors dense and BGE-M3 sparse vectors into an
in-memory Qdrant collection, and evaluates first-stage candidate recall with
the same qrel model used by the R3 backend comparison runner.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import resource
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from scripts.learning.rag import indexer
from scripts.learning.rag.r3.eval.metrics import (
    RetrievalEvaluationQuery,
    retrieval_summary,
)
from scripts.learning.rag.r3.eval.qrels import R3QueryJudgement, load_qrels
from scripts.learning.rag.r3.index.runtime_loader import encode_runtime_query
from scripts.learning.rag.r3.query_plan import build_query_plan


COLLECTION_NAME = "woowa_r3_probe"
DENSE_VECTOR = "dense"
SPARSE_VECTOR = "sparse"


@dataclass(frozen=True)
class QdrantProbePoint:
    point_id: int
    path: str
    chunk_id: str
    title: str
    category: str
    dense: list[float]
    sparse_indices: list[int]
    sparse_values: list[float]


def _rss_peak_mb() -> float:
    value = float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if sys.platform == "darwin":
        return value / (1024.0 * 1024.0)
    return value / 1024.0


def _plain_list(value: Any) -> list:
    if value is None:
        return []
    if hasattr(value, "tolist"):
        return list(value.tolist())
    return list(value)


def _dense_list(value: Any) -> list[float]:
    return [float(item) for item in _plain_list(value)]


def _sparse_lists(value: Any) -> tuple[list[int], list[float]]:
    if not isinstance(value, dict):
        return [], []
    raw_indices = _plain_list(value.get("indices"))
    raw_values = _plain_list(value.get("values"))
    indices: list[int] = []
    values: list[float] = []
    for token_id, weight in zip(raw_indices, raw_values):
        try:
            normalized_id = int(token_id)
            normalized_weight = float(weight)
        except (TypeError, ValueError):
            continue
        if normalized_weight > 0:
            indices.append(normalized_id)
            values.append(normalized_weight)
    return indices, values


def load_lance_points(
    index_root: Path,
    *,
    limit_docs: int | None = None,
) -> tuple[list[QdrantProbePoint], dict[str, Any]]:
    manifest = indexer.read_manifest_v3(index_root)
    table = indexer.open_lance_table(index_root)
    columns = [
        "chunk_id",
        "path",
        "title",
        "category",
        "dense_vec",
        "sparse_vec",
    ]
    try:
        frame = table.to_pandas(columns=columns)
    except TypeError:
        frame = table.to_pandas()
    rows = frame.to_dict("records")
    if limit_docs is not None:
        rows = rows[: max(limit_docs, 0)]

    points: list[QdrantProbePoint] = []
    for idx, row in enumerate(rows, start=1):
        dense = _dense_list(row.get("dense_vec"))
        if not dense:
            continue
        sparse_indices, sparse_values = _sparse_lists(row.get("sparse_vec"))
        points.append(
            QdrantProbePoint(
                point_id=idx,
                path=str(row.get("path") or ""),
                chunk_id=str(row.get("chunk_id") or ""),
                title=str(row.get("title") or ""),
                category=str(row.get("category") or "unknown"),
                dense=dense,
                sparse_indices=sparse_indices,
                sparse_values=sparse_values,
            )
        )
    metadata = {
        "source_index": "lance",
        "source_table_version": getattr(table, "version", None),
        "corpus_hash": manifest.get("corpus_hash"),
        "manifest_row_count": manifest.get("row_count"),
        "loaded_points": len(points),
        "dense_dim": len(points[0].dense) if points else 0,
    }
    return points, metadata


def _batches(items: list[QdrantProbePoint], batch_size: int) -> Iterable[list[QdrantProbePoint]]:
    for start in range(0, len(items), batch_size):
        yield items[start : start + batch_size]


def build_local_collection(
    points: list[QdrantProbePoint],
    *,
    batch_size: int,
):
    try:
        from qdrant_client import QdrantClient, models
    except ImportError as exc:
        raise SystemExit(
            "qdrant-client is required for this optional probe. "
            "Install with `pip install -e '.[qdrant]'`."
        ) from exc

    if not points:
        raise ValueError("cannot build Qdrant probe collection with no points")

    client = QdrantClient(":memory:")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config={
            DENSE_VECTOR: models.VectorParams(
                size=len(points[0].dense),
                distance=models.Distance.COSINE,
            )
        },
        sparse_vectors_config={
            SPARSE_VECTOR: models.SparseVectorParams(),
        },
    )

    for batch in _batches(points, batch_size):
        payloads = []
        for point in batch:
            vector: dict[str, Any] = {DENSE_VECTOR: point.dense}
            if point.sparse_indices:
                vector[SPARSE_VECTOR] = models.SparseVector(
                    indices=point.sparse_indices,
                    values=point.sparse_values,
                )
            payloads.append(
                models.PointStruct(
                    id=point.point_id,
                    vector=vector,
                    payload={
                        "path": point.path,
                        "chunk_id": point.chunk_id,
                        "title": point.title,
                        "category": point.category,
                    },
                )
            )
        client.upsert(collection_name=COLLECTION_NAME, points=payloads)
    return client


def _paths_from_qdrant(points) -> tuple[str, ...]:
    paths: list[str] = []
    for point in points:
        payload = point.payload or {}
        path = payload.get("path")
        if isinstance(path, str) and path:
            paths.append(path)
    return tuple(paths)


def _rrf_fuse(
    ranked_lists: Iterable[tuple[float, tuple[str, ...]]],
    *,
    limit: int,
    k: int = 60,
) -> tuple[str, ...]:
    scores: dict[str, float] = {}
    first_seen: dict[str, int] = {}
    order = 0
    for weight, paths in ranked_lists:
        for rank, path in enumerate(paths, start=1):
            order += 1
            first_seen.setdefault(path, order)
            scores[path] = scores.get(path, 0.0) + weight / (k + rank)
    return tuple(
        path
        for path, _score in sorted(
            scores.items(),
            key=lambda item: (-item[1], first_seen[item[0]], item[0]),
        )[:limit]
    )


def _tag_value(tags: tuple[str, ...], prefix: str, default: str = "unknown") -> str:
    needle = f"{prefix}:"
    for tag in tags:
        if tag.startswith(needle):
            return tag[len(needle) :] or default
    return default


def evaluate_qdrant(
    client,
    qrels: list[R3QueryJudgement],
    *,
    index_root: Path,
    top_k: int,
    windows: tuple[int, ...],
    forbidden_window: int,
) -> dict[str, Any]:
    from qdrant_client import models

    eval_queries: list[RetrievalEvaluationQuery] = []
    query_profiles: list[dict[str, Any]] = []
    for query in qrels:
        started = time.perf_counter()
        encoding = encode_runtime_query(index_root, query.prompt)
        encode_ms = (time.perf_counter() - started) * 1000.0

        dense_paths: tuple[str, ...] = ()
        dense_ms = 0.0
        if encoding.get("dense") is not None:
            started = time.perf_counter()
            dense_paths = _paths_from_qdrant(
                client.query_points(
                    collection_name=COLLECTION_NAME,
                    query=encoding["dense"],
                    using=DENSE_VECTOR,
                    limit=top_k,
                    with_payload=["path"],
                    with_vectors=False,
                ).points
            )
            dense_ms = (time.perf_counter() - started) * 1000.0

        sparse_terms = dict(encoding.get("sparse_terms") or {})
        sparse_paths: tuple[str, ...] = ()
        sparse_ms = 0.0
        if sparse_terms:
            started = time.perf_counter()
            sparse_paths = _paths_from_qdrant(
                client.query_points(
                    collection_name=COLLECTION_NAME,
                    query=models.SparseVector(
                        indices=[int(token_id) for token_id in sparse_terms],
                        values=[float(weight) for weight in sparse_terms.values()],
                    ),
                    using=SPARSE_VECTOR,
                    limit=top_k,
                    with_payload=["path"],
                    with_vectors=False,
                ).points
            )
            sparse_ms = (time.perf_counter() - started) * 1000.0

        fused_paths = _rrf_fuse(
            ((1.0, dense_paths), (1.0, sparse_paths)),
            limit=top_k,
        )
        plan = build_query_plan(query.prompt)
        eval_queries.append(
            RetrievalEvaluationQuery(
                query_id=query.query_id,
                language=plan.language,
                level=_tag_value(query.tags, "level"),
                category=_tag_value(query.tags, "category"),
                primary_paths=tuple(sorted(query.primary_paths())),
                acceptable_paths=tuple(sorted(query.acceptable_paths())),
                forbidden_paths=query.forbidden_paths,
                candidate_paths=fused_paths,
                final_paths=fused_paths,
            )
        )
        query_profiles.append(
            {
                "query_id": query.query_id,
                "language": plan.language,
                "encode_ms": round(encode_ms, 3),
                "dense_ms": round(dense_ms, 3),
                "sparse_ms": round(sparse_ms, 3),
                "dense_count": len(dense_paths),
                "sparse_count": len(sparse_paths),
                "fused_count": len(fused_paths),
                "primary_rank": (
                    min(
                        (fused_paths.index(path) + 1 for path in query.primary_paths() if path in fused_paths),
                        default=None,
                    )
                ),
            }
        )

    return {
        "query_count": len(qrels),
        "summary": retrieval_summary(
            eval_queries,
            windows=windows,
            forbidden_window=forbidden_window,
        ),
        "query_profiles": query_profiles,
    }


def _latency_summary(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"min": None, "p50": None, "p95": None, "max": None, "avg": None}
    ordered = sorted(values)

    def percentile(p: float) -> float:
        index = min(len(ordered) - 1, max(0, int(round((len(ordered) - 1) * p))))
        return round(ordered[index], 3)

    return {
        "min": round(ordered[0], 3),
        "p50": percentile(0.50),
        "p95": percentile(0.95),
        "max": round(ordered[-1], 3),
        "avg": round(sum(ordered) / len(ordered), 3),
    }


def run_probe(
    *,
    index_root: Path,
    qrels_path: Path,
    limit_docs: int | None,
    top_k: int,
    windows: tuple[int, ...],
    forbidden_window: int,
    batch_size: int,
) -> dict[str, Any]:
    started = time.perf_counter()
    rss_before = _rss_peak_mb()
    points, source_metadata = load_lance_points(index_root, limit_docs=limit_docs)
    load_ms = (time.perf_counter() - started) * 1000.0

    started = time.perf_counter()
    client = build_local_collection(points, batch_size=batch_size)
    build_ms = (time.perf_counter() - started) * 1000.0
    rss_after_build = _rss_peak_mb()

    started = time.perf_counter()
    evaluation = evaluate_qdrant(
        client,
        load_qrels(qrels_path),
        index_root=index_root,
        top_k=top_k,
        windows=windows,
        forbidden_window=forbidden_window,
    )
    eval_ms = (time.perf_counter() - started) * 1000.0
    profiles = evaluation["query_profiles"]
    return {
        "schema_version": 1,
        "artifact_kind": "r3_qdrant_local_probe",
        "backend": "qdrant_local_memory",
        "qdrant_client_version": importlib.metadata.version("qdrant-client"),
        "spec": {
            "index_root": str(index_root),
            "qrels": str(qrels_path),
            "limit_docs": limit_docs,
            "top_k": top_k,
            "windows": list(windows),
            "forbidden_window": forbidden_window,
            "batch_size": batch_size,
        },
        "source": source_metadata,
        "timing_ms": {
            "load_lance_points": round(load_ms, 3),
            "build_qdrant_collection": round(build_ms, 3),
            "evaluate_queries": round(eval_ms, 3),
        },
        "rss_peak_mb": {
            "before": round(rss_before, 3),
            "after_build": round(rss_after_build, 3),
            "delta_build": round(max(rss_after_build - rss_before, 0.0), 3),
            "after_eval": round(_rss_peak_mb(), 3),
        },
        "latency_ms": {
            "encode": _latency_summary([float(row["encode_ms"]) for row in profiles]),
            "dense_query": _latency_summary([float(row["dense_ms"]) for row in profiles]),
            "sparse_query": _latency_summary([float(row["sparse_ms"]) for row in profiles]),
        },
        "summary": evaluation["summary"],
        "query_profiles": profiles,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index-root", type=Path, default=indexer.DEFAULT_INDEX_ROOT)
    parser.add_argument("--qrels", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--limit-docs", type=int, default=None)
    parser.add_argument("--top-k", type=int, default=100)
    parser.add_argument("--window", type=int, action="append", default=None)
    parser.add_argument("--forbidden-window", type=int, default=5)
    parser.add_argument("--batch-size", type=int, default=512)
    args = parser.parse_args(argv)

    report = run_probe(
        index_root=args.index_root,
        qrels_path=args.qrels,
        limit_docs=args.limit_docs,
        top_k=args.top_k,
        windows=tuple(args.window or [5, 20, 100]),
        forbidden_window=args.forbidden_window,
        batch_size=args.batch_size,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(f"wrote Qdrant local probe report to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
