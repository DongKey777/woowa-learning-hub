"""Compare retrieval top-K candidates across two runtime indexes.

This diagnostic is intentionally narrower than the full metric harness:
it explains *why* a quality delta happened by preserving the actual top-K
documents, primary ranks, and category drift for each query.
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from scripts.learning.cli_rag_eval import (
    _resolve_device,
    _summarize_runtime_debug,
    load_queries,
)
from scripts.learning.rag.eval.dataset import GradedQuery, infer_category
from scripts.learning.rag.eval.runtime_index import resolve_runtime_index_info


REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_FIXTURE = REPO_ROOT / "tests" / "fixtures" / "cs_rag_cutover_failure_queries.json"
DEFAULT_LEGACY_INDEX = REPO_ROOT / "state" / "cs_rag_archive" / "v2_20260501T063445Z"
DEFAULT_LANCE_INDEX = REPO_ROOT / "state" / "cs_rag"
DEFAULT_OUT = REPO_ROOT / "reports" / "rag_eval" / "retrieval_top10_diagnosis.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="diagnose-retrieval",
        description=(
            "Run the same query fixture against a legacy index and a Lance index, "
            "then emit top-K candidate/category drift diagnostics."
        ),
    )
    parser.add_argument("--fixture", type=Path, default=DEFAULT_FIXTURE)
    parser.add_argument("--legacy-index-root", type=Path, default=DEFAULT_LEGACY_INDEX)
    parser.add_argument("--lance-index-root", type=Path, default=DEFAULT_LANCE_INDEX)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--top-k", type=int, default=10)
    parser.add_argument(
        "--device",
        choices=("auto", "cpu", "mps", "cuda"),
        default="auto",
        help="Embedder device. Defaults to the same resolver used by rag-eval.",
    )
    return parser


def _rank_of(paths: Sequence[str], primary_paths: set[str]) -> int | None:
    for idx, path in enumerate(paths, start=1):
        if path in primary_paths:
            return idx
    return None


def _path_category(path: str | None, fallback: str | None = None) -> str:
    if path:
        category = infer_category(path)
        if category != "unknown":
            return category
    return fallback or "unknown"


def _format_hits(hits: Sequence[dict[str, Any]], *, top_k: int) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for idx, hit in enumerate(hits[:top_k], start=1):
        path = str(hit.get("path") or "")
        out.append(
            {
                "rank": idx,
                "path": path,
                "category": _path_category(path, hit.get("category")),
                "title": hit.get("title"),
                "section_title": hit.get("section_title"),
                "score": hit.get("score"),
            }
        )
    return out


def _runtime_manifest(index_root: Path, *, backend: str) -> dict[str, Any]:
    info = resolve_runtime_index_info(index_root, backend=backend)
    return {
        "index_root": str(info.index_root),
        "backend": info.backend,
        "corpus_hash": info.corpus_hash,
        "index_version": info.index_version,
        "embedding_model": info.embedding_model,
        "model_revision": info.model_revision,
        "embedding_dim": info.embedding_dim,
        "modalities": list(info.modalities),
    }


def _search_backend(
    query: GradedQuery,
    *,
    backend: str,
    index_root: Path,
    top_k: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    from scripts.learning.rag import searcher

    debug: dict[str, Any] = {}
    hits = searcher.search(
        query.prompt,
        learning_points=list(query.learning_points),
        top_k=top_k,
        mode=query.mode,
        experience_level=query.experience_level,
        backend=backend,
        index_root=index_root,
        debug=debug,
    )
    primary_paths = query.primary_paths()
    ranked_paths = [str(hit.get("path") or "") for hit in hits]
    primary_rank = _rank_of(ranked_paths, primary_paths)
    formatted_hits = _format_hits(hits, top_k=top_k)
    top1 = formatted_hits[0] if formatted_hits else None
    expected_category = query.bucket.category
    top1_category = top1.get("category") if top1 else None
    cross_category = (
        bool(top1_category)
        and expected_category != "unknown"
        and top1_category != expected_category
    )
    record = {
        "primary_rank": primary_rank,
        "primary_in_top_k": primary_rank is not None,
        "primary_at_1": primary_rank == 1,
        "top1": top1,
        "top1_cross_category": cross_category,
        "top_k": formatted_hits,
        "debug": debug,
    }
    debug_record = {
        "query_id": query.query_id,
        "backend": backend,
        "mode": query.mode,
        **debug,
        "hit_count": len(hits),
    }
    return record, debug_record


def _rank_value(rank: int | None, *, missing_rank: int) -> int:
    return rank if rank is not None else missing_rank


def _classify_lance(record: dict[str, Any]) -> str:
    lance = record["lance"]
    if lance["primary_at_1"]:
        return "pass_rank1"
    if lance["top1_cross_category"]:
        return "top1_cross_category"
    if lance["primary_rank"] is None:
        return "primary_missing_top_k"
    return "same_category_wrong_rank"


def _summarize(records: Sequence[dict[str, Any]], *, top_k: int) -> dict[str, Any]:
    total = len(records)
    legacy_better = 0
    lance_better = 0
    tie = 0
    confusion: Counter[str] = Counter()
    failure_classes: Counter[str] = Counter()
    by_query: dict[str, list[str]] = {
        "legacy_only_primary_at_1": [],
        "lance_only_primary_at_1": [],
        "both_primary_at_1": [],
        "neither_primary_at_1": [],
        "lance_top1_cross_category": [],
    }

    for record in records:
        query_id = record["query_id"]
        legacy_rank = _rank_value(record["legacy"]["primary_rank"], missing_rank=top_k + 1)
        lance_rank = _rank_value(record["lance"]["primary_rank"], missing_rank=top_k + 1)
        if legacy_rank < lance_rank:
            legacy_better += 1
        elif lance_rank < legacy_rank:
            lance_better += 1
        else:
            tie += 1

        legacy_at1 = record["legacy"]["primary_at_1"]
        lance_at1 = record["lance"]["primary_at_1"]
        if legacy_at1 and lance_at1:
            by_query["both_primary_at_1"].append(query_id)
        elif legacy_at1:
            by_query["legacy_only_primary_at_1"].append(query_id)
        elif lance_at1:
            by_query["lance_only_primary_at_1"].append(query_id)
        else:
            by_query["neither_primary_at_1"].append(query_id)

        if record["lance"]["top1_cross_category"]:
            by_query["lance_top1_cross_category"].append(query_id)
            expected = record["expected"]["category"]
            actual = record["lance"]["top1"]["category"] if record["lance"]["top1"] else "missing"
            confusion[f"{expected}->{actual}"] += 1

        failure_classes[_classify_lance(record)] += 1

    return {
        "total_queries": total,
        "top_k": top_k,
        "primary_at_1": {
            "legacy": sum(1 for r in records if r["legacy"]["primary_at_1"]),
            "lance": sum(1 for r in records if r["lance"]["primary_at_1"]),
        },
        "primary_in_top_k": {
            "legacy": sum(1 for r in records if r["legacy"]["primary_in_top_k"]),
            "lance": sum(1 for r in records if r["lance"]["primary_in_top_k"]),
        },
        "primary_missing_top_k": {
            "legacy": sum(1 for r in records if r["legacy"]["primary_rank"] is None),
            "lance": sum(1 for r in records if r["lance"]["primary_rank"] is None),
        },
        "top1_cross_category": {
            "legacy": sum(1 for r in records if r["legacy"]["top1_cross_category"]),
            "lance": sum(1 for r in records if r["lance"]["top1_cross_category"]),
        },
        "rank_comparison": {
            "legacy_better": legacy_better,
            "lance_better": lance_better,
            "tie": tie,
        },
        "lance_failure_classes": dict(sorted(failure_classes.items())),
        "lance_top1_confusion": dict(sorted(confusion.items())),
        "query_sets": {key: sorted(values) for key, values in by_query.items()},
    }


def build_diagnosis(
    queries: Sequence[GradedQuery],
    *,
    legacy_index_root: Path,
    lance_index_root: Path,
    top_k: int,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    legacy_debug: list[dict[str, Any]] = []
    lance_debug: list[dict[str, Any]] = []

    for query in queries:
        legacy, legacy_dbg = _search_backend(
            query,
            backend="legacy",
            index_root=legacy_index_root,
            top_k=top_k,
        )
        lance, lance_dbg = _search_backend(
            query,
            backend="lance",
            index_root=lance_index_root,
            top_k=top_k,
        )
        legacy_debug.append(legacy_dbg)
        lance_debug.append(lance_dbg)
        legacy_rank = _rank_value(legacy["primary_rank"], missing_rank=top_k + 1)
        lance_rank = _rank_value(lance["primary_rank"], missing_rank=top_k + 1)
        records.append(
            {
                "query_id": query.query_id,
                "prompt": query.prompt,
                "mode": query.mode,
                "experience_level": query.experience_level,
                "expected": {
                    "category": query.bucket.category,
                    "difficulty": query.bucket.difficulty,
                    "language": query.bucket.language,
                    "intent": query.bucket.intent,
                    "primary_paths": sorted(query.primary_paths()),
                    "acceptable_paths": sorted(query.acceptable_paths()),
                    "companion_paths": sorted(query.companion_paths()),
                },
                "legacy": legacy,
                "lance": lance,
                "comparison": {
                    "rank_delta_lance_minus_legacy": lance_rank - legacy_rank,
                    "legacy_better_rank": legacy_rank < lance_rank,
                    "lance_better_rank": lance_rank < legacy_rank,
                    "same_rank": legacy_rank == lance_rank,
                },
            }
        )

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fixture_query_count": len(queries),
        "summary": _summarize(records, top_k=top_k),
        "runtime_summary": {
            "legacy": _summarize_runtime_debug(legacy_debug),
            "lance": _summarize_runtime_debug(lance_debug),
        },
        "records": records,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    device = _resolve_device(args.device)
    os.environ["WOOWA_RAG_DEVICE"] = device

    queries = load_queries(args.fixture)
    diagnosis = build_diagnosis(
        queries,
        legacy_index_root=args.legacy_index_root,
        lance_index_root=args.lance_index_root,
        top_k=args.top_k,
    )
    diagnosis["input"] = {
        "fixture": str(args.fixture),
        "top_k": args.top_k,
        "device": device,
        "legacy": _runtime_manifest(args.legacy_index_root, backend="legacy"),
        "lance": _runtime_manifest(args.lance_index_root, backend="lance"),
    }

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(diagnosis, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote: {args.out}")
    print(json.dumps(diagnosis["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
