"""Experimental R3 search entrypoint.

This module is deliberately a skeleton until independent retrievers are added.
It proves routing, query planning, and trace shape without changing the
production legacy/Lance search behavior.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from .anaphora import detect_follow_up
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
from .retrievers import (
    LexicalRetriever,
    MissionBridgeRetriever,
    SignalRetriever,
    SparseRetriever,
    SymptomRouterRetriever,
)
from .rerankers import CrossEncoderReranker

_SPARSE_RETRIEVER_CACHE: dict[tuple[int, int, int], SparseRetriever] = {}
_MAX_SPARSE_RETRIEVER_CACHE_ENTRIES = 4
_LEXICAL_SIDECAR_FIELDS = ("title", "section", "aliases")
_QUERY_PREFETCH_BODY_FIELDS = ("body",)
_CATALOG_REQUIRED_FILES = (
    "concepts.v3.json",
    "mission_ids_to_concepts.json",
    "symptom_to_concepts.json",
)


def _resolve_catalog_root(catalog_root: Path | str | None) -> Path | None:
    """Find a v3 catalog directory by explicit override or repo-default.

    Resolution order:
      1. ``catalog_root`` argument when provided
      2. ``WOOWA_RAG_CATALOG_ROOT`` env var
      3. Repo default ``knowledge/cs/catalog`` (resolved relative to this
         module's location)

    Returns None when no candidate has the required catalog files —
    callers must handle absence gracefully so search keeps working on
    indexes built before Phase 4.5.
    """
    candidates: list[Path] = []
    if catalog_root is not None:
        candidates.append(Path(catalog_root))
    env_override = os.environ.get("WOOWA_RAG_CATALOG_ROOT")
    if env_override:
        candidates.append(Path(env_override))
    here = Path(__file__).resolve()
    for parent in [here, *here.parents]:
        candidate = parent / "knowledge" / "cs" / "catalog"
        if candidate.exists():
            candidates.append(candidate)
            break
    for cand in candidates:
        if all((cand / name).exists() for name in _CATALOG_REQUIRED_FILES):
            return cand
    return None


def _record_stage(stage_ms: dict[str, float], name: str, started_at: float) -> None:
    elapsed_ms = (time.perf_counter() - started_at) * 1000.0
    stage_ms[name] = round(stage_ms.get(name, 0.0) + elapsed_ms, 3)


_FORBIDDEN_FILTER_DEFAULT_ON = "1"


def _forbidden_filter_enabled() -> bool:
    return os.environ.get(
        "WOOWA_RAG_R3_FORBIDDEN_FILTER",
        _FORBIDDEN_FILTER_DEFAULT_ON,
    ) == "1"


# ---------------------------------------------------------------------------
# Phase 9.3 — refusal sentinel
# ---------------------------------------------------------------------------

_SENTINEL_PATH = "<sentinel:no_confident_match>"


def _evaluate_refusal_sentinel(
    *,
    fused: list,
    reranker_active: bool,
    config: "R3Config",
) -> tuple[bool, dict | None]:
    """Decide whether to short-circuit retrieval with a refusal sentinel.

    Returns ``(should_emit, info)``. ``info`` carries the diagnostic
    payload used for trace metadata when ``should_emit`` is True; None
    otherwise.

    Conservative — never emits when:
      * threshold is None (disabled — production default)
      * reranker did not run (no cross-encoder score to threshold)
      * fused is empty
      * top-1 candidate has no ``cross_encoder_score`` in metadata
        (upstream contract change must not silently start refusing)
    """
    threshold = config.refusal_threshold
    if threshold is None:
        return False, None
    if not reranker_active:
        return False, None
    if not fused:
        return False, None
    top = fused[0]
    metadata = getattr(top, "metadata", None) or {}
    raw = metadata.get("cross_encoder_score")
    if raw is None:
        return False, None
    try:
        ce_score = float(raw)
    except (TypeError, ValueError):
        return False, None
    if ce_score >= threshold:
        return False, None
    return True, {
        "applied": True,
        "reason": "no_confident_match",
        "rejected_top_path": top.path,
        "rejected_top_score": ce_score,
        "threshold": float(threshold),
    }


def _make_refusal_sentinel(
    *,
    top_path: str,
    top_score: float,
    threshold: float,
) -> dict:
    """Build the single sentinel hit returned by ``r3.search.search``
    when ``_evaluate_refusal_sentinel`` returns True.

    Shape mirrors a normal hit (so downstream code reading required
    keys still finds them) plus three discriminator fields:

      * ``sentinel`` — the ID consumer code keys off of
      * ``rejected_top`` / ``rejected_score`` — what would have
        been returned, kept for telemetry / debugging
      * ``threshold`` — config value at decision time, so trace
        archives carry their own context
    """
    return {
        "row_id": None,
        "doc_id": None,
        "chunk_id": None,
        "path": _SENTINEL_PATH,
        "title": "",
        "category": "",
        "section_title": "",
        "section_path": [],
        "score": float(top_score),
        "snippet_preview": "",
        "anchors": [],
        "r3_sources": [],
        "sentinel": "no_confident_match",
        "rejected_top": top_path,
        "rejected_score": float(top_score),
        "threshold": float(threshold),
    }


def _load_path_to_forbidden(catalog_dir: Path | None) -> dict[str, frozenset[str]]:
    """Build a path -> forbidden_neighbors mapping from concepts.v3.json.

    Catalog stores doc_path with no ``contents/`` prefix and
    forbidden_neighbors with the prefix. We normalize both to the
    full prefixed form so the lookup matches the candidate.path the
    fusion stage emits.
    """
    if catalog_dir is None:
        return {}
    catalog_path = catalog_dir / "concepts.v3.json"
    if not catalog_path.exists():
        return {}
    import json
    try:
        blob = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    out: dict[str, frozenset[str]] = {}
    for entry in blob.get("concepts", {}).values():
        doc_path = entry.get("doc_path")
        forbidden = entry.get("forbidden_neighbors") or []
        if not doc_path or not forbidden:
            continue
        full_path = doc_path if doc_path.startswith("contents/") else f"contents/{doc_path}"
        out[full_path] = frozenset(forbidden)
    return out


def _apply_forbidden_filter(
    fused: list,
    path_to_forbidden: dict[str, frozenset[str]],
) -> tuple[list, dict[str, str | int]]:
    """Drop fused candidates whose path matches a forbidden_neighbor of
    the current top-1.

    The intent comes from the v3 corpus contract: each canonical doc
    declares the docs that should *not* be primary for queries about
    it. When the retrieval system surfaces such a doc inside top_k of
    a query whose top-1 is the canonical, the forbidden doc is wrong-
    bucket noise and should be demoted out of top_k.

    This implementation removes the forbidden candidates entirely
    rather than re-ranking them down. That matches how the cohort_eval
    forbidden_neighbor cohort scores: forbidden_hit_rate is computed on
    top_k membership, so removal == demotion past the boundary. We do
    not touch top-1 itself.

    Returns ``(filtered_fused, info)`` where info records the filter
    decision for the trace metadata.
    """
    info: dict[str, str | int] = {
        "applied": False,
        "removed_count": 0,
        "removed_paths": [],
    }
    if not fused or not path_to_forbidden:
        return fused, info
    top1_path = fused[0].path
    forbidden_set = path_to_forbidden.get(top1_path)
    if not forbidden_set:
        return fused, info
    info["applied"] = True
    kept = [fused[0]]
    removed: list[str] = []
    for cand in fused[1:]:
        if cand.path in forbidden_set:
            removed.append(cand.path)
            continue
        kept.append(cand)
    info["removed_count"] = len(removed)
    info["removed_paths"] = removed
    return kept, info


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


def _reranker_decision(
    mode: str,
    use_reranker: bool | None,
    *,
    config: R3Config,
    lexical_sidecar_used: bool,
) -> tuple[bool, str | None]:
    if use_reranker is False:
        return False, "caller_disabled"
    if mode != "full":
        return False, "mode_not_full"
    if os.environ.get("WOOWA_RAG_NO_RERANK") == "1":
        return False, "legacy_no_rerank_env"
    if use_reranker is True:
        return True, None
    if config.local_rerank_policy == "off":
        return False, "policy_off"
    if config.local_rerank_policy == "always":
        return True, None
    if lexical_sidecar_used:
        return False, "policy_auto_sidecar_first_stage_gate"
    return True, None


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
    reformulated_query: str | None = None,
    learning_points: list[str] | None = None,
    topic_hints: list[str] | None = None,
    top_k: int = 5,
    mode: str = "full",
    index_root: Path | str | None = None,
    catalog_root: Path | str | None = None,
    use_reranker: bool | None = None,
    experience_level: str | None = None,
    learner_context: dict | None = None,
    debug: dict | None = None,
) -> list[dict]:
    """Run the R3 skeleton and return no results until retrievers land.

    ``prompt`` is the learner's raw natural-language query. When
    ``reformulated_query`` is supplied (e.g. by the AI session that maps
    the learner's paraphrase to corpus-friendly vocabulary), it is used
    for the semantic channels — dense BGE-M3 encoding and cross-encoder
    rerank — while the lexical retriever keeps the raw token form. This
    is the corpus-agnostic equivalent of contextual_chunk_prefix on the
    corpus side: the corpus stays as the author wrote it, the learner's
    natural language stays as they typed it, and the AI session bridges
    the two at retrieval time.
    """

    # Phase 9.1 — multi-turn anaphora. detect_follow_up consults the
    # AI-session reformulation first (verbatim use, regex suppressed)
    # and falls back to regex + learner_context fold-in for short
    # follow-up prompts. Lexical retriever still uses the raw prompt.
    follow_up = detect_follow_up(
        prompt=prompt,
        reformulated_query=reformulated_query,
        learner_context=learner_context,
    )
    semantic_query = follow_up.augmented_semantic_query
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
    reranker_active = False
    reranker_skip_reason = None
    catalog_channels_used: list[str] = []
    catalog_error: str | None = None
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

    reranker_active, reranker_skip_reason = _reranker_decision(
        mode,
        use_reranker,
        config=config,
        lexical_sidecar_used=lexical_sidecar_used,
    )

    sparse_encoder_allowed = mode == "full" or config.sparse_encoder_in_cheap_mode
    if index_root is not None and sparse_encoder_allowed:
        try:
            started = time.perf_counter()
            query_encoding = encode_runtime_query(
                index_root,
                semantic_query,
                query_plan_version=query_plan.version,
            )
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
        catalog_dir = _resolve_catalog_root(catalog_root)
        catalog_candidates: list = []
        if catalog_dir is not None:
            try:
                mission_retriever = MissionBridgeRetriever.from_catalog_dir(
                    catalog_dir, signal_documents,
                )
                catalog_candidates.extend(mission_retriever.retrieve(query_plan))
                catalog_channels_used.append("mission_bridge")
                symptom_retriever = SymptomRouterRetriever.from_catalog_dir(
                    catalog_dir, signal_documents,
                )
                catalog_candidates.extend(symptom_retriever.retrieve(query_plan))
                catalog_channels_used.append("symptom_router")
            except Exception as exc:
                # Graceful degradation — never let catalog channel issues
                # break the existing dense / lexical / sparse path.
                catalog_error = f"{type(exc).__name__}: {exc}"
                catalog_candidates = []

        candidates = [
            *[
                candidate
                for lexical in lexical_retrievers
                for candidate in lexical.retrieve(query_plan)
            ],
            *dense_candidates,
            *sparse.retrieve(query_plan, query_terms=query_sparse_terms or None),
            *signal.retrieve([*query_plan.route_tags, *(topic_hints or [])]),
            *catalog_candidates,
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
            semantic_query,
            fused,
            top_n=rerank_window,
        )
        _record_stage(stage_ms, "rerank", started)

    # Phase 9.3 — refusal sentinel. Evaluate before forbidden_filter so
    # the threshold gate sees the *reranked* top-1, not a forbidden-
    # filtered remainder. When triggered, fused is cleared so the
    # downstream forbidden_filter / trace path becomes a no-op for
    # candidates while still recording the decision in trace metadata.
    sentinel_emitted, refusal_info = _evaluate_refusal_sentinel(
        fused=fused,
        reranker_active=reranker_active,
        config=config,
    )
    sentinel_hit_payload: dict | None = None
    if sentinel_emitted and refusal_info is not None:
        sentinel_hit_payload = _make_refusal_sentinel(
            top_path=str(refusal_info["rejected_top_path"]),
            top_score=float(refusal_info["rejected_top_score"]),
            threshold=float(refusal_info["threshold"]),
        )
        fused = []

    forbidden_filter_info: dict[str, str | int] = {"applied": False, "removed_count": 0, "removed_paths": []}
    if fused and _forbidden_filter_enabled():
        started = time.perf_counter()
        catalog_dir_for_filter = _resolve_catalog_root(catalog_root)
        path_to_forbidden = _load_path_to_forbidden(catalog_dir_for_filter)
        fused, forbidden_filter_info = _apply_forbidden_filter(fused, path_to_forbidden)
        _record_stage(stage_ms, "forbidden_filter", started)

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
            "reformulated_query": reformulated_query,
            "semantic_query": semantic_query,
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
            "rerank_policy": config.local_rerank_policy,
            "reranker_skip_reason": reranker_skip_reason,
            "forbidden_filter": forbidden_filter_info,
            "refusal_sentinel": refusal_info if sentinel_emitted else None,
            "anaphora": {
                "detected_via": follow_up.detected_via,
                "is_follow_up": follow_up.is_follow_up,
                "prior_topics": list(follow_up.prior_topics),
            },
            "catalog_channels_used": list(catalog_channels_used),
            "catalog_error": catalog_error,
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
        debug["r3_rerank_policy"] = config.local_rerank_policy
        debug["r3_reranker_skip_reason"] = reranker_skip_reason
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
        debug["r3_catalog_channels_used"] = list(catalog_channels_used)
        debug["r3_catalog_error"] = catalog_error
        debug["r3_forbidden_filter"] = dict(forbidden_filter_info)
        debug["r3_refusal_sentinel"] = (
            dict(refusal_info) if sentinel_emitted and refusal_info else None
        )
        debug["r3_anaphora"] = {
            "detected_via": follow_up.detected_via,
            "is_follow_up": follow_up.is_follow_up,
            "prior_topics": list(follow_up.prior_topics),
        }
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

    if sentinel_hit_payload is not None:
        return [sentinel_hit_payload]
    return [_hit_from_candidate(candidate) for candidate in fused[:top_k]]
