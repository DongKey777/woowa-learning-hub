"""Experimental R3 search entrypoint.

This module is deliberately a skeleton until independent retrievers are added.
It proves routing, query planning, and trace shape without changing the
production legacy/Lance search behavior.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from .config import R3Config
from .eval.trace import R3Trace
from .fusion import fuse_candidates
from .index.lexical_sidecar import load_lexical_sidecar
from .index.runtime_loader import (
    encode_runtime_query,
    load_runtime_dense_candidates,
    load_runtime_documents,
    load_runtime_sparse_documents,
)
from .index.lexical_store import LexicalStore
from .query_plan import build_query_plan
from .retrievers import LexicalRetriever, SignalRetriever, SparseRetriever
from .rerankers import CrossEncoderReranker

_SPARSE_RETRIEVER_CACHE: dict[tuple[int, int, int], SparseRetriever] = {}
_MAX_SPARSE_RETRIEVER_CACHE_ENTRIES = 4
_LEXICAL_SIDECAR_FIELDS = ("title", "section", "aliases")
_QUERY_PREFETCH_BODY_FIELDS = ("body",)


def _record_stage(stage_ms: dict[str, float], name: str, started_at: float) -> None:
    elapsed_ms = (time.perf_counter() - started_at) * 1000.0
    stage_ms[name] = round(stage_ms.get(name, 0.0) + elapsed_ms, 3)


def _cached_sparse_retriever(
    documents,
    *,
    limit: int = 100,
) -> tuple[SparseRetriever, bool]:
    key = (id(documents), len(documents), limit)
    cached = _SPARSE_RETRIEVER_CACHE.get(key)
    if cached is not None:
        return cached, True
    retriever = SparseRetriever(documents, limit=limit)
    _SPARSE_RETRIEVER_CACHE[key] = retriever
    while len(_SPARSE_RETRIEVER_CACHE) > _MAX_SPARSE_RETRIEVER_CACHE_ENTRIES:
        oldest = next(iter(_SPARSE_RETRIEVER_CACHE))
        _SPARSE_RETRIEVER_CACHE.pop(oldest, None)
    return retriever, False


def _reranker_enabled(mode: str, use_reranker: bool | None) -> bool:
    if use_reranker is False:
        return False
    if mode != "full":
        return False
    if os.environ.get("WOOWA_RAG_NO_RERANK") == "1":
        return False
    return use_reranker is True or use_reranker is None


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

    stage_ms: dict[str, float] = {}
    started = time.perf_counter()
    config = R3Config.from_env()
    query_plan = build_query_plan(prompt)
    _record_stage(stage_ms, "query_plan", started)
    candidates = []
    fused = []
    sparse_documents = []
    query_sparse_terms: dict[str, float] = {}
    dense_candidates = []
    sparse_source = "lexical_terms"
    sparse_retriever_cache_hit = False
    lexical_sidecar = None
    lexical_sidecar_used = False
    lexical_sidecar_error = None
    reranker_active = _reranker_enabled(mode, use_reranker)
    try:
        started = time.perf_counter()
        documents = (
            load_runtime_documents(
                index_root,
                query=query_plan.raw_query,
                limit=config.runtime_lance_prefetch_limit,
            )
            if index_root is not None
            else []
        )
        _record_stage(stage_ms, "load_runtime_documents", started)
    except FileNotFoundError:
        documents = []
        _record_stage(stage_ms, "load_runtime_documents", started)

    if index_root is not None and config.lexical_sidecar_enabled:
        started = time.perf_counter()
        try:
            lexical_sidecar = load_lexical_sidecar(index_root)
            lexical_sidecar_used = lexical_sidecar is not None
        except Exception as exc:
            lexical_sidecar = None
            lexical_sidecar_error = f"{type(exc).__name__}: {exc}"
        _record_stage(stage_ms, "load_lexical_sidecar", started)

    sparse_encoder_allowed = mode == "full" or config.sparse_encoder_in_cheap_mode
    if index_root is not None and sparse_encoder_allowed:
        try:
            started = time.perf_counter()
            query_encoding = encode_runtime_query(index_root, query_plan.raw_query)
            _record_stage(stage_ms, "encode_runtime_query", started)
        except Exception:
            query_encoding = {}
            _record_stage(stage_ms, "encode_runtime_query", started)
        query_sparse_terms = dict(query_encoding.get("sparse_terms") or {})
        started = time.perf_counter()
        dense_candidates = load_runtime_dense_candidates(
            index_root,
            query_encoding.get("dense"),
            limit=config.runtime_lance_prefetch_limit,
        )
        _record_stage(stage_ms, "load_runtime_dense_candidates", started)
        if query_sparse_terms:
            try:
                started = time.perf_counter()
                sparse_documents = load_runtime_sparse_documents(index_root)
                _record_stage(stage_ms, "load_runtime_sparse_documents", started)
                sparse_source = "bge_m3_sparse_vec_sidecar"
            except FileNotFoundError:
                sparse_documents = []
                _record_stage(stage_ms, "load_runtime_sparse_documents", started)
    if not sparse_documents:
        sparse_documents = documents
        query_sparse_terms = {}
        sparse_source = "lexical_terms"

    if documents or sparse_documents or lexical_sidecar is not None:
        started = time.perf_counter()
        signal_documents = (
            lexical_sidecar.store.documents
            if lexical_sidecar is not None
            else documents
        )
        lexical_retrievers = []
        if lexical_sidecar is not None:
            lexical_retrievers.append(
                LexicalRetriever(
                    lexical_sidecar.store,
                    fields=_LEXICAL_SIDECAR_FIELDS,
                    retriever_namespace="lexical_sidecar",
                )
            )
            if documents:
                lexical_retrievers.append(
                    LexicalRetriever(
                        LexicalStore.from_documents(documents),
                        fields=_QUERY_PREFETCH_BODY_FIELDS,
                    )
                )
        else:
            lexical_retrievers.append(
                LexicalRetriever(LexicalStore.from_documents(documents))
            )
        signal = SignalRetriever(signal_documents)
        sparse, sparse_retriever_cache_hit = _cached_sparse_retriever(
            sparse_documents,
        )
        _record_stage(stage_ms, "construct_retrievers", started)
        fusion_limit = max(
            top_k,
            config.rerank_input_window(offline=False) if reranker_active else top_k,
            1,
        )
        started = time.perf_counter()
        candidates = [
            *[
                candidate
                for lexical in lexical_retrievers
                for candidate in lexical.retrieve(query_plan)
            ],
            *dense_candidates,
            *sparse.retrieve(query_plan, query_terms=query_sparse_terms or None),
            *signal.retrieve([*query_plan.route_tags, *(topic_hints or [])]),
        ]
        _record_stage(stage_ms, "retrieve_candidates", started)
        started = time.perf_counter()
        fused = fuse_candidates(candidates, limit=fusion_limit)
        _record_stage(stage_ms, "fuse_candidates", started)

    reranker_model = None
    fused_paths = tuple(candidate.path for candidate in fused)
    rerank_input_paths: tuple[str, ...] = ()
    if reranker_active and fused:
        started = time.perf_counter()
        reranker = CrossEncoderReranker.for_language(query_plan.language)
        reranker_model = reranker.model_id
        rerank_window = min(len(fused), config.rerank_input_window(offline=False))
        rerank_input_paths = tuple(candidate.path for candidate in fused[:rerank_window])
        fused = reranker.rerank(
            query_plan.raw_query,
            fused,
            top_n=rerank_window,
        )
        _record_stage(stage_ms, "rerank", started)

    trace = R3Trace(
        trace_id=query_plan.normalized_query,
        query_plan=query_plan,
        candidates=tuple(candidates),
        final_paths=tuple(candidate.path for candidate in fused[:top_k]),
        stage_ms=stage_ms,
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
            "dense_candidate_count": len(dense_candidates),
            "sparse_retriever_cache_hit": sparse_retriever_cache_hit,
            "lexical_sidecar_used": lexical_sidecar_used,
            "lexical_sidecar": lexical_sidecar.metadata if lexical_sidecar is not None else None,
            "lexical_sidecar_error": lexical_sidecar_error,
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
        debug["r3_reranker_enabled"] = reranker_active
        debug["r3_sparse_source"] = sparse_source
        debug["r3_sparse_sidecar_document_count"] = len(sparse_documents)
        debug["r3_sparse_query_terms_count"] = len(query_sparse_terms)
        debug["r3_sparse_encoder_allowed"] = sparse_encoder_allowed
        debug["r3_sparse_retriever_cache_hit"] = sparse_retriever_cache_hit
        debug["r3_dense_candidate_count"] = len(dense_candidates)
        debug["r3_lexical_sidecar_used"] = lexical_sidecar_used
        debug["r3_lexical_sidecar"] = (
            lexical_sidecar.metadata if lexical_sidecar is not None else None
        )
        debug["r3_lexical_sidecar_error"] = lexical_sidecar_error
        debug["r3_stage_ms"] = dict(stage_ms)
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
