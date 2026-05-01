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
from .index.runtime_loader import (
    encode_runtime_sparse_query,
    load_runtime_documents,
    load_runtime_sparse_documents,
)
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
    sparse_documents = []
    query_sparse_terms: dict[str, float] = {}
    sparse_source = "lexical_terms"
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

    sparse_encoder_allowed = mode == "full" or config.sparse_encoder_in_cheap_mode
    if index_root is not None and sparse_encoder_allowed:
        try:
            query_sparse_terms = encode_runtime_sparse_query(index_root, query_plan.raw_query)
        except Exception:
            query_sparse_terms = {}
        if query_sparse_terms:
            try:
                sparse_documents = load_runtime_sparse_documents(index_root)
                sparse_source = "bge_m3_sparse_vec_sidecar"
            except FileNotFoundError:
                sparse_documents = []
    if not sparse_documents:
        sparse_documents = documents
        query_sparse_terms = {}
        sparse_source = "lexical_terms"

    if documents or sparse_documents:
        lexical = LexicalRetriever(LexicalStore.from_documents(documents))
        sparse = SparseRetriever(sparse_documents)
        signal = SignalRetriever(documents)
        fusion_limit = max(
            top_k,
            config.rerank_input_window(offline=False) if use_reranker is True else top_k,
            1,
        )
        candidates = [
            *lexical.retrieve(query_plan),
            *sparse.retrieve(query_plan, query_terms=query_sparse_terms or None),
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
            "sparse_source": sparse_source,
            "sparse_sidecar_document_count": len(sparse_documents),
            "sparse_query_terms_count": len(query_sparse_terms),
            "sparse_encoder_allowed": sparse_encoder_allowed,
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
        debug["r3_sparse_source"] = sparse_source
        debug["r3_sparse_sidecar_document_count"] = len(sparse_documents)
        debug["r3_sparse_query_terms_count"] = len(query_sparse_terms)
        debug["r3_sparse_encoder_allowed"] = sparse_encoder_allowed
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
