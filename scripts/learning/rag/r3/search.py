"""Experimental R3 search entrypoint.

This module is deliberately a skeleton until independent retrievers are added.
It proves routing, query planning, and trace shape without changing the
production legacy/Lance search behavior.
"""

from __future__ import annotations

from pathlib import Path

from .config import R3Config
from .eval.trace import R3Trace
from .fusion import fuse_candidates
from .index.runtime_loader import load_runtime_documents
from .index.lexical_store import LexicalStore
from .query_plan import build_query_plan
from .retrievers import LexicalRetriever, SignalRetriever, SparseRetriever
from .rerankers import CrossEncoderReranker


def _hit_from_candidate(candidate) -> dict:
    document_metadata = candidate.metadata.get("document") or {}
    return {
        "row_id": None,
        "doc_id": None,
        "chunk_id": candidate.chunk_id,
        "path": candidate.path,
        "title": candidate.title or "",
        "category": document_metadata.get("category", "unknown"),
        "section_title": candidate.section_title or "",
        "section_path": [candidate.title or "", candidate.section_title or ""],
        "score": candidate.score,
        "snippet_preview": "",
        "anchors": [],
        "r3_sources": candidate.metadata.get("sources", []),
    }


def search(
    prompt: str,
    *,
    learning_points: list[str] | None = None,
    topic_hints: list[str] | None = None,
    top_k: int = 5,
    mode: str = "full",
    index_root: Path | str | None = None,
    use_reranker: bool | None = None,
    experience_level: str | None = None,
    learner_context: dict | None = None,
    debug: dict | None = None,
) -> list[dict]:
    """Run the R3 skeleton and return no results until retrievers land."""

    config = R3Config.from_env()
    query_plan = build_query_plan(prompt)
    candidates = []
    fused = []
    try:
        documents = (
            load_runtime_documents(
                index_root,
                query=query_plan.raw_query,
                limit=config.runtime_lance_prefetch_limit,
            )
            if index_root is not None
            else []
        )
    except FileNotFoundError:
        documents = []

    if documents:
        lexical = LexicalRetriever(LexicalStore.from_documents(documents))
        sparse = SparseRetriever(documents)
        signal = SignalRetriever(documents)
        fusion_limit = max(
            top_k,
            config.rerank_input_window(offline=False) if use_reranker is True else top_k,
            1,
        )
        candidates = [
            *lexical.retrieve(query_plan),
            *sparse.retrieve(query_plan),
            *signal.retrieve([*query_plan.route_tags, *(topic_hints or [])]),
        ]
        fused = fuse_candidates(candidates, limit=fusion_limit)

    reranker_model = None
    fused_paths = tuple(candidate.path for candidate in fused)
    rerank_input_paths: tuple[str, ...] = ()
    if use_reranker is True and fused:
        reranker = CrossEncoderReranker.for_language(query_plan.language)
        reranker_model = reranker.model_id
        rerank_window = min(len(fused), config.rerank_input_window(offline=False))
        rerank_input_paths = tuple(candidate.path for candidate in fused[:rerank_window])
        fused = reranker.rerank(
            query_plan.raw_query,
            fused,
            top_n=rerank_window,
        )

    trace = R3Trace(
        trace_id=query_plan.normalized_query,
        query_plan=query_plan,
        candidates=tuple(candidates),
        final_paths=tuple(candidate.path for candidate in fused[:top_k]),
        metadata={
            "backend": "r3",
            "source_index": documents[0].metadata.get("index_backend") if documents else None,
            "reranker_model": reranker_model,
            "fused_paths": list(fused_paths),
            "rerank_input_paths": list(rerank_input_paths),
        },
    )

    if debug is not None:
        debug["backend"] = "r3"
        debug["r3_enabled"] = config.enabled
        debug["r3_skeleton"] = True
        debug["r3_query_plan"] = query_plan.to_dict()
        debug["r3_trace"] = trace.to_dict()
        debug["r3_candidate_count"] = len(candidates)
        debug["r3_final_paths"] = list(trace.final_paths)
        debug["r3_reranker_model"] = reranker_model
        debug["rerank_input_window"] = config.rerank_input_window(offline=False)
        debug["top_k"] = top_k
        debug["mode"] = mode
        debug["learning_points"] = list(learning_points or [])
        debug["topic_hints"] = list(topic_hints or [])
        debug["index_root"] = str(index_root) if index_root is not None else None
        debug["use_reranker"] = use_reranker
        debug["experience_level"] = experience_level
        debug["learner_context_present"] = learner_context is not None

    return [_hit_from_candidate(candidate) for candidate in fused[:top_k]]
