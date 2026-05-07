"""Single facade between coach_run and the CS RAG subsystem.

coach_run imports this module **lazily** (inside the pipeline step that
needs it) so missing ML dependencies degrade to cs_readiness.state="missing"
instead of crashing the whole coach-run call. See the "Lazy import
contract" section in ``docs/cs-rag-internals.md``.

Public contract
---------------
``augment(...)`` is the only function coach_run calls. It takes:

- ``prompt``: raw learner question
- ``learning_points``: peer-derived learning-point ids (may be empty)
- ``topic_hints``: extra query hints (focus topic, primary_topic)
- ``cs_search_mode``: "skip" | "cheap" | "full" from intent_router.pre_decide
- ``index_root``: override for tests
- ``top_k``: optional override
- ``readiness``: pre-computed ReadinessReport from indexer.is_ready() — avoids
  re-hashing the corpus twice per turn.

It returns a compact dict::

    {
        "by_learning_point": {lp: [hit, ...]},
        "by_fallback_key":  {"<category>:<signal_tag>": [hit, ...]},
        "fallback_reason":  str | None,
        "cs_categories_hit": [...],
        "sidecar": {...} | None,           # full-body payload for sidecar file
        "meta": {
            "latency_ms": int,
            "rag_ready": bool,
            "reason": str | None,           # 'ready'|'skip_mode'|'not_ready'|'deps_missing'|...
            "mode_used": "skip"|"cheap"|"full",
        },
    }

Degrade rules
-------------
- ``cs_search_mode == "skip"`` → return empty augment, mode_used="skip".
- readiness.state != "ready" → return empty augment, reason=readiness.reason.
- ImportError / ModuleNotFoundError on lazy searcher import → reason="deps_missing".
- Any other exception from searcher → reason="search_error", empty augment.

drill offers / drill results
----------------------------
``augment`` does **not** build drill offers. That lives in
``scripts.learning.drill.build_offer_if_due``, called **after**
``profile_merge.unify()`` by coach_run (Phase 4). This separation is
enforced in the plan's Phase 2.1 "책임 경계" clause and verified by
``tests/unit/test_cs_block_is_view_of_augmentation.py``.
"""

from __future__ import annotations

import json
import math
import os
import re
import time
from pathlib import Path, PurePosixPath
from typing import Any

from .rag import category_mapping, signal_rules
from .rag import indexer as rag_indexer

RAG_RUNTIME_BACKEND_ENV = "WOOWA_RAG_RUNTIME_BACKEND"
VALID_SEARCH_BACKENDS = {"auto", "legacy", "lance", "r3"}
R3_LEXICAL_SIDECAR_NAME = "r3_lexical_sidecar.json"
_KNOWN_CITATION_CATEGORIES = {
    "algorithm",
    "data-structure",
    "database",
    "design-pattern",
    "language",
    "network",
    "operating-system",
    "security",
    "software-engineering",
    "spring",
    "system-design",
}
_CITATION_BUCKET_SEGMENT_RE = re.compile(r"^[a-z0-9][a-z0-9/_-]*$")
_CITATION_BUCKET_ALIAS_SEGMENT_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def _empty_response_hints() -> dict[str, Any]:
    """Default response_hints used by every augment() return path.

    Carrier for paste-verbatim contract fields (Phase 9.4 citation,
    Phase 9.3 refusal tier-downgrade). Always present so the AI session
    contract can read the same shape regardless of whether RAG was
    skipped, ready, or failed.
    """
    return {
        "citation_markdown": None,
        "citation_paths": [],
        "citation_trace": [],
        "tier_downgrade": None,
        "fallback_disclaimer": None,
    }


def _response_hints_with(**overrides: Any) -> dict[str, Any]:
    """Return a normalized response_hints payload with stable keys."""
    payload = _empty_response_hints()
    payload.update(overrides)
    return payload


# Phase 9.3 — tier-downgrade discriminator and Korean fallback line.
TIER_DOWNGRADE_REASON = "corpus_gap_no_confident_match"
TIER_DOWNGRADE_DISCLAIMER = (
    "코퍼스에 이 주제의 신뢰할 만한 자료가 없어 일반 지식 기반으로 답한다."
)


def _is_refusal_sentinel(hits: list[dict[str, Any]] | None) -> bool:
    """True when ``r3.search.search`` emitted a confidence-threshold
    refusal sentinel (Phase 9.3 Step B).

    The sentinel is the AI session's signal to abandon corpus-grounded
    answering and fall back to training knowledge with the
    ``TIER_DOWNGRADE_DISCLAIMER`` first line. We never let a sentinel
    leak into the bucket population — once detected, the per-query
    bucket is treated as if no hits were returned.
    """
    if not hits:
        return False
    head = hits[0]
    return isinstance(head, dict) and head.get("sentinel") == "no_confident_match"


def _iter_hit_dicts(hits: list[Any] | None) -> list[dict[str, Any]]:
    """Drop malformed search rows instead of collapsing the whole turn."""
    if not hits:
        return []
    return [hit for hit in hits if isinstance(hit, dict)]


def _coerce_citation_score(value: Any) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return float("-inf")
    if not math.isfinite(score):
        return float("-inf")
    return score


def _normalize_citation_path(value: Any) -> str | None:
    """Accept only CS content doc paths for learner citations."""
    path = str(value or "").strip()
    if not path:
        return None
    if any(char.isspace() for char in path):
        return None
    if "\\" in path or "#" in path or "?" in path:
        return None
    normalized = PurePosixPath(path)
    # Keep the learner-facing citation block and operator trace on one
    # canonical repo-relative spelling. Reject dot-segments or duplicate
    # separators instead of silently rewriting them.
    if normalized.as_posix() != path:
        return None
    if normalized.suffix != ".md":
        return None
    parts = normalized.parts
    is_repo_relative = len(parts) >= 5 and parts[:3] == ("knowledge", "cs", "contents")
    is_corpus_relative = len(parts) >= 3 and parts[0] == "contents"
    if not (is_repo_relative or is_corpus_relative):
        return None
    if any(part in {"", ".", ".."} for part in parts):
        return None
    return path


def _normalize_citation_field(value: Any) -> str | None:
    """Keep trace metadata JSON-safe and free of accidental whitespace payloads."""
    text = str(value or "").strip()
    if not text or any(char.isspace() for char in text):
        return None
    return text


def _sanitize_citation_bucket_segment(value: Any) -> str:
    """Slug unsafe bucket fragments so trace provenance keeps a stable shape."""
    raw = str(value or "").strip().lower()
    if not raw:
        return "unknown"
    sanitized = re.sub(r"[^a-z0-9/_-]+", "-", raw)
    sanitized = re.sub(r"-{2,}", "-", sanitized).strip("-")
    sanitized = re.sub(r"/{2,}", "/", sanitized).strip("/")
    return sanitized or "unknown"


def _format_citation_bucket(prefix: str, *segments: Any) -> str:
    """Construct a normalized trace bucket instead of leaking raw query text."""
    if prefix == "learning_point":
        return f"{prefix}:{_sanitize_citation_bucket_segment(segments[0])}"
    if prefix == "fallback":
        return (
            f"{prefix}:{_sanitize_citation_bucket_segment(segments[0])}:"
            f"{_sanitize_citation_bucket_segment(segments[1])}"
        )
    raise ValueError(f"unknown citation bucket prefix: {prefix}")


def _normalize_citation_bucket(value: Any) -> str | None:
    """Allow only known trace bucket prefixes in operator-facing payloads."""
    bucket = _normalize_citation_field(value)
    if not bucket:
        return None
    for prefix in ("learning_point:", "fallback:"):
        if not bucket.startswith(prefix):
            continue
        suffix = bucket[len(prefix):]
        if not suffix:
            return None
        # Trace buckets should expose exactly one routing provenance,
        # not nested alias prefixes from accidental reformatting.
        if suffix.startswith("learning_point:") or suffix.startswith("fallback:"):
            return None
        if prefix == "learning_point:":
            if ":" in suffix:
                return None
            if not _is_valid_citation_bucket_alias(suffix):
                return None
        elif suffix.count(":") != 1:
            return None
        else:
            category, alias = suffix.split(":", 1)
            if not (
                _is_valid_citation_bucket_category(category)
                and _is_valid_citation_bucket_alias(alias)
            ):
                return None
        return bucket
    return None


def _is_valid_citation_bucket_category(value: str) -> bool:
    """Restrict fallback categories to the known retrieval namespace."""
    return value == "general" or value in _KNOWN_CITATION_CATEGORIES


def _is_valid_citation_bucket_alias(value: str) -> bool:
    """Accept path-like aliases without overlap or traversal ambiguity."""
    if not _CITATION_BUCKET_SEGMENT_RE.fullmatch(value):
        return False
    if value.startswith("/") or value.endswith("/") or "//" in value:
        return False
    parts = value.split("/")
    return all(
        part not in {"", ".", ".."}
        and _CITATION_BUCKET_ALIAS_SEGMENT_RE.fullmatch(part)
        for part in parts
    )


def _citation_bucket_priority(bucket: str | None) -> int:
    """Prefer learner-specific trace sources when score ties.

    A path can surface through both a learning-point query and a broader
    fallback query with the same score. In that case keep the more
    specific learning-point bucket in `citation_trace` so operators do
    not lose the stronger provenance.
    """
    if not bucket:
        return 0
    if bucket.startswith("learning_point:"):
        return 2
    if bucket.startswith("fallback:"):
        return 1
    return 0


def _derive_citation_category(path: str, raw_category: Any) -> str:
    """Keep clean retrieval categories, fall back to the corpus path otherwise."""
    category = _normalize_citation_field(raw_category)
    if category in _KNOWN_CITATION_CATEGORIES:
        return category
    parts = PurePosixPath(path).parts
    if len(parts) >= 5 and parts[:3] == ("knowledge", "cs", "contents"):
        return parts[3]
    if len(parts) >= 3 and parts[0] == "contents":
        return parts[1]
    return ""


def _normalize_compact_hit(hit: dict[str, Any]) -> dict[str, Any] | None:
    """Keep augment payload rows structurally safe before sidecar/meta assembly."""
    path = _normalize_citation_path(hit.get("path"))
    if not path:
        return None
    title = _normalize_citation_field(hit.get("title"))
    section_title = _normalize_citation_field(hit.get("section_title"))
    snippet_preview = hit.get("snippet_preview")
    if not isinstance(snippet_preview, str):
        snippet_preview = ""
    section_path = hit.get("section_path")
    if not isinstance(section_path, list):
        section_path = []
    return {
        **hit,
        "path": path,
        "title": title or Path(path).stem,
        "category": _derive_citation_category(path, hit.get("category")),
        "section_title": section_title or "",
        "section_path": [str(part) for part in section_path if str(part).strip()],
        "score": hit.get("score"),
        "snippet_preview": snippet_preview,
    }


def _citation_trace_completeness(hit: dict[str, Any]) -> tuple[int, int]:
    """Prefer ties with cleaner trace metadata for operator debugging."""
    category = hit.get("category")
    bucket = hit.get("bucket")
    return (
        1 if category else 0,
        _citation_bucket_priority(bucket),
        1 if bucket else 0,
    )


def _select_citation_hits(
    all_hits: list[dict[str, Any]],
    *,
    max_n: int = 3,
) -> list[dict[str, Any]]:
    """Pick the exact hit set that backs learner-visible citations.

    Both `citation_markdown` and `citation_trace` must derive from the
    same capped, deduplicated ordering so operators can trust that each
    trace entry corresponds to one pasted `참고:` line.
    """
    best_hit_by_path: dict[str, dict[str, Any]] = {}
    first_seen_by_path: dict[str, int] = {}
    for index, hit in enumerate(_iter_hit_dicts(all_hits)):
        path = _normalize_citation_path(hit.get("path"))
        if not path:
            continue
        score = _coerce_citation_score(hit.get("score"))
        first_seen_by_path.setdefault(path, index)
        current = best_hit_by_path.get(path)
        current_score = (
            _coerce_citation_score(current.get("score"))
            if current is not None
            else float("-inf")
        )
        candidate = {
            "path": path,
            "score": None if not math.isfinite(score) else score,
            "category": _derive_citation_category(path, hit.get("category")),
            "bucket": _normalize_citation_bucket(hit.get("_citation_bucket")),
        }
        should_replace = current is None or score > current_score
        if (
            not should_replace
            and current is not None
            and score == current_score
            and _citation_trace_completeness(candidate)
            > _citation_trace_completeness(current)
        ):
            should_replace = True
        if should_replace:
            best_hit_by_path[path] = {
                **candidate,
            }
    return [
        best_hit_by_path[path]
        for path in sorted(
            best_hit_by_path,
            key=lambda value: (
                # Keep equal-score ties aligned with the earliest
                # retrieval order so `citation_markdown` and
                # `citation_trace` stay stable across identical-score
                # reruns and operator diffs remain readable.
                -_coerce_citation_score(best_hit_by_path[value]["score"]),
                first_seen_by_path[value],
                value,
            ),
        )[:max_n]
    ]


def _build_citation_payload(
    all_hits: list[dict[str, Any]],
    *,
    max_n: int = 3,
) -> tuple[str | None, list[str], list[dict[str, Any]]]:
    """Build learner-facing citation fields from one shared selection pass.

    `citation_markdown`, `citation_paths`, and `citation_trace` are a
    single contract surface. Deriving them from the same selected hit
    list avoids drift when selection logic changes or is instrumented in
    tests.
    """
    selected_hits = _select_citation_hits(all_hits, max_n=max_n)
    normalized_hits: list[dict[str, Any]] = []
    seen_paths: set[str] = set()
    for hit in selected_hits:
        path = _normalize_citation_path(hit.get("path"))
        if not path or path in seen_paths:
            continue
        seen_paths.add(path)
        score = _coerce_citation_score(hit.get("score"))
        normalized_hits.append(
            {
                "path": path,
                "score": None if not math.isfinite(score) else score,
                "category": _derive_citation_category(path, hit.get("category")),
                "bucket": _normalize_citation_bucket(hit.get("bucket")),
            }
        )
        if len(normalized_hits) >= max_n:
            break
    paths = [hit["path"] for hit in normalized_hits]
    if not paths:
        return None, [], []
    body = "\n".join(f"- {p}" for p in paths)
    return f"참고:\n{body}", paths, normalized_hits


def _empty_result(reason: str, mode_used: str) -> dict[str, Any]:
    return {
        "by_learning_point": {},
        "by_fallback_key": {},
        "fallback_reason": None,
        "cs_categories_hit": [],
        "sidecar": None,
        "meta": {
            "latency_ms": 0,
            "rag_ready": False,
            "reason": reason,
            "mode_used": mode_used,
            "category_filter_fallback": False,
        },
        "response_hints": _empty_response_hints(),
    }


def augment(
    *,
    prompt: str,
    reformulated_query: str | None = None,
    learning_points: list[str] | None = None,
    topic_hints: list[str] | None = None,
    cs_search_mode: str = "full",
    index_root: Path | str = rag_indexer.DEFAULT_INDEX_ROOT,
    top_k: int = 5,
    readiness: rag_indexer.ReadinessReport | None = None,
    experience_level: str | None = None,
    learner_context: dict[str, Any] | None = None,
    backend: str | None = None,
) -> dict[str, Any]:
    """Run CS RAG search and shape results for coach_run payload assembly."""
    if cs_search_mode not in ("skip", "cheap", "full"):
        raise ValueError(f"unknown cs_search_mode: {cs_search_mode}")

    if cs_search_mode == "skip":
        return _empty_result("skip_mode", "skip")

    # Readiness check. Caller may pass a pre-computed report from the
    # coach-run turn to avoid re-hashing the corpus twice.
    if readiness is None:
        try:
            readiness = rag_indexer.is_ready(index_root)
        except Exception:
            return _empty_result("readiness_error", cs_search_mode)
    if readiness.state != "ready":
        return _empty_result(readiness.reason or "not_ready", cs_search_mode)

    # Lazy import of the searcher — keeps cs_readiness degrade path alive
    # on environments without sentence-transformers.
    try:
        from .rag import searcher  # noqa: WPS433
    except (ImportError, ModuleNotFoundError):
        return _empty_result("deps_missing", cs_search_mode)
    except Exception:
        return _empty_result("import_error", cs_search_mode)

    start = time.time()
    backend = resolve_search_backend(index_root, override=backend)

    by_lp: dict[str, list[dict]] = {}
    by_fallback: dict[str, list[dict]] = {}
    fallback_reason: str | None = None
    all_hits: list[dict] = []
    citation_hits: list[dict] = []
    seen_paths: set[str] = set()
    category_filter_fallback = False
    query_candidate_kinds: list[str] = []
    query_plans: list[dict[str, Any]] = []
    runtime_debug: dict[str, Any] = {}
    refusal_sentinel_detected = False  # Phase 9.3 — set when any
    # downstream search call returns the no_confident_match sentinel.

    def record_query_debug(bucket: str, search_debug: dict) -> None:
        raw_kinds = search_debug.get("query_candidate_kinds")
        if not isinstance(raw_kinds, list):
            return
        kinds = [str(kind) for kind in raw_kinds if str(kind)]
        if not kinds:
            return
        query_plans.append(
            {
                "bucket": bucket,
                "query_candidate_kinds": kinds,
            }
        )
        for kind in kinds:
            if kind not in query_candidate_kinds:
                query_candidate_kinds.append(kind)

    def record_runtime_debug(search_debug: dict) -> None:
        if runtime_debug:
            return
        fields = (
            "backend",
            "mode",
            "r3_reranker_enabled",
            "r3_reranker_model",
            "r3_rerank_policy",
            "r3_reranker_skip_reason",
            "rerank_input_window",
            "r3_sparse_source",
            "r3_sparse_sidecar_document_count",
            "r3_sparse_query_terms_count",
            "r3_sparse_retriever_cache_hit",
            "r3_dense_candidate_count",
            "r3_lexical_sidecar_used",
            "r3_lexical_sidecar",
            "r3_lexical_sidecar_error",
            "r3_stage_ms",
        )
        captured = {
            field: search_debug[field]
            for field in fields
            if field in search_debug
        }
        if captured:
            runtime_debug.update(captured)

    def extend_citation_hits(bucket: str, hits: list[dict[str, Any]]) -> None:
        for hit in _iter_hit_dicts(hits):
            citation_hits.append({**hit, "_citation_bucket": bucket})

    def extend_payload_hits(hits: list[dict[str, Any]]) -> None:
        for hit in _iter_hit_dicts(hits):
            normalized = _normalize_compact_hit(hit)
            if not normalized:
                continue
            path = normalized["path"]
            if path in seen_paths:
                continue
            seen_paths.add(path)
            all_hits.append(normalized)

    try:
        if learning_points:
            # Peer-derived path: search once per learning point so each
            # bucket reflects its own category boost.
            for lp in learning_points:
                lp_debug: dict = {}
                hits = searcher.search(
                    prompt,
                    reformulated_query=reformulated_query,
                    learning_points=[lp],
                    topic_hints=topic_hints,
                    mode=cs_search_mode,
                    backend=backend,
                    index_root=index_root,
                    top_k=top_k,
                    experience_level=experience_level,
                    learner_context=learner_context,
                    debug=lp_debug,
                )
                if lp_debug.get("category_filter_fallback"):
                    category_filter_fallback = True
                record_query_debug(f"learning_point:{lp}", lp_debug)
                record_runtime_debug(lp_debug)
                if _is_refusal_sentinel(hits):
                    refusal_sentinel_detected = True
                    # Sentinel for one bucket means corpus has no
                    # confident match for this query — every other
                    # bucket would emit the same sentinel. Stop the
                    # per-LP loop and let the function fall through to
                    # the post-loop tier-downgrade override.
                    break
                if hits:
                    by_lp[lp] = hits
                    extend_citation_hits(_format_citation_bucket("learning_point", lp), hits)
                    extend_payload_hits(hits)

        # If no peer learning point matched (cs_only turn) or all buckets
        # came back empty, fall back to signal-tag bucketing.
        if not by_lp and not refusal_sentinel_detected:
            signals = signal_rules.detect_signals(prompt, topic_hints)
            fallback_reason = (
                "cs_only_no_peer_learning_point"
                if not learning_points
                else "no_learning_point_hits"
            )
            if signals:
                # Use the top 2 signal tags as bucket keys.
                for sig in signals[:2]:
                    key = f"{sig['category']}:{sig['tag']}"
                    fallback_debug: dict = {}
                    hits = searcher.search(
                        prompt,
                        reformulated_query=reformulated_query,
                        learning_points=None,
                        topic_hints=topic_hints,
                        mode=cs_search_mode,
                        backend=backend,
                        index_root=index_root,
                        top_k=top_k,
                        experience_level=experience_level,
                        learner_context=learner_context,
                        debug=fallback_debug,
                    )
                    if fallback_debug.get("category_filter_fallback"):
                        category_filter_fallback = True
                    record_query_debug(f"fallback:{key}", fallback_debug)
                    record_runtime_debug(fallback_debug)
                    if _is_refusal_sentinel(hits):
                        refusal_sentinel_detected = True
                        break
                    if hits:
                        by_fallback[key] = hits
                        extend_citation_hits(
                            _format_citation_bucket(
                                "fallback",
                                sig["category"],
                                sig["tag"],
                            ),
                            hits,
                        )
                        extend_payload_hits(hits)
                        # One search is enough — signal tags share the
                        # same query, only the bucket key differs. Keep
                        # the rest of the signals as bucket aliases.
                        break
            else:
                key = f"general:{_top_token(prompt)}"
                fallback_debug = {}
                hits = searcher.search(
                    prompt,
                    reformulated_query=reformulated_query,
                    learning_points=None,
                    topic_hints=topic_hints,
                    mode=cs_search_mode,
                    backend=backend,
                    index_root=index_root,
                    top_k=top_k,
                    experience_level=experience_level,
                    learner_context=learner_context,
                    debug=fallback_debug,
                )
                if fallback_debug.get("category_filter_fallback"):
                    category_filter_fallback = True
                record_query_debug(f"fallback:{key}", fallback_debug)
                record_runtime_debug(fallback_debug)
                if _is_refusal_sentinel(hits):
                    refusal_sentinel_detected = True
                elif hits:
                    by_fallback[key] = hits
                    extend_citation_hits(
                        _format_citation_bucket("fallback", "general", _top_token(prompt)),
                        hits,
                    )
                    extend_payload_hits(hits)
    except Exception:
        return _empty_result("search_error", cs_search_mode)

    latency_ms = int((time.time() - start) * 1000)

    if refusal_sentinel_detected:
        # Phase 9.3 sentinel means "no confident corpus answer for this
        # turn", not "one bucket failed". Drop any earlier provisional
        # hits so downstream payloads cannot mix tier-0 fallback with
        # stale citation/sidecar context from a previous bucket.
        by_lp = {}
        by_fallback = {}
        fallback_reason = TIER_DOWNGRADE_REASON
        all_hits = []
        citation_hits = []

    categories_hit = sorted(
        {category for h in all_hits if (category := h.get("category"))}
    )

    # Compact body fields are kept inside by_learning_point / by_fallback_key
    # directly (snippet_preview is already 250-char capped by searcher).
    # The sidecar mirrors each hit with the same compact shape today; a
    # future enhancement can attach full document bodies here.
    sidecar = None
    if all_hits:
        sidecar = {
            "generated_by": "scripts.learning.integration.augment",
            "mode_used": cs_search_mode,
            "backend": backend,
            "hits": [_sidecar_hit(h) for h in all_hits],
        }
        if query_candidate_kinds:
            sidecar["query_candidate_kinds"] = query_candidate_kinds
            sidecar["query_plans"] = query_plans

    meta = {
        "latency_ms": latency_ms,
        "rag_ready": True,
        "reason": "ready",
        "mode_used": cs_search_mode,
        "backend": backend,
        "category_filter_fallback": category_filter_fallback,
    }
    if query_candidate_kinds:
        meta["query_candidate_kinds"] = query_candidate_kinds
        meta["query_plans"] = query_plans
    if runtime_debug:
        meta["runtime_debug"] = runtime_debug

    citation_markdown, citation_paths, citation_trace = _build_citation_payload(
        citation_hits
    )
    response_hints = _response_hints_with(
        citation_markdown=citation_markdown,
        citation_paths=citation_paths,
        citation_trace=citation_trace,
    )

    # Phase 9.3 — when R3 emitted a refusal sentinel for any of the
    # search buckets, flip this turn into a tier-0 fallback. Citation
    # is suppressed (no corpus hit to anchor on); the AI session reads
    # `tier_downgrade` + `fallback_disclaimer` and responds from
    # training knowledge with the disclaimer as the first line.
    if refusal_sentinel_detected:
        response_hints = _response_hints_with(
            tier_downgrade=TIER_DOWNGRADE_REASON,
            fallback_disclaimer=TIER_DOWNGRADE_DISCLAIMER,
        )
        meta["fallback_reason"] = TIER_DOWNGRADE_REASON

    return {
        "by_learning_point": by_lp,
        "by_fallback_key": by_fallback,
        "fallback_reason": fallback_reason,
        "cs_categories_hit": categories_hit,
        "sidecar": sidecar,
        "meta": meta,
        "response_hints": response_hints,
    }


def _top_token(prompt: str) -> str:
    tokens = signal_rules._tokenize(prompt)  # internal tokenizer is fine here
    return tokens[0] if tokens else "unknown"


def _has_valid_r3_sidecar(index_root: Path | str, manifest: dict[str, Any]) -> bool:
    sidecar_path = Path(index_root) / R3_LEXICAL_SIDECAR_NAME
    if not sidecar_path.exists():
        return False
    try:
        sidecar = json.loads(sidecar_path.read_text(encoding="utf-8"))
    except Exception:
        return False
    return (
        sidecar.get("corpus_hash") == manifest.get("corpus_hash")
        and sidecar.get("row_count") == manifest.get("row_count")
        and sidecar.get("document_count") == manifest.get("row_count")
    )


def _detect_backend(index_root: Path | str) -> str:
    """Infer the runtime backend from the manifest and R3 sidecar contract."""
    try:
        manifest = rag_indexer.load_manifest(index_root)
    except Exception:
        return "legacy"
    try:
        version = int(manifest.get("index_version", rag_indexer.INDEX_VERSION))
    except (TypeError, ValueError):
        return "legacy"
    if version < rag_indexer.LANCE_INDEX_VERSION:
        return "legacy"
    return "r3" if _has_valid_r3_sidecar(index_root, manifest) else "lance"


def resolve_search_backend(
    index_root: Path | str,
    *,
    override: str | None = None,
) -> str:
    """Resolve the runtime search backend.

    Explicit overrides still win.  Without an override, a Lance v3 index is
    promoted to R3 only when the remote-built lexical sidecar is present and
    matches the index manifest, so stale or partial R3 artifacts fail back to
    the plain Lance runtime.
    """

    candidate = override or os.environ.get(RAG_RUNTIME_BACKEND_ENV)
    if candidate and candidate not in VALID_SEARCH_BACKENDS:
        raise ValueError(f"unknown RAG runtime backend: {candidate}")
    if candidate and candidate != "auto":
        return candidate
    return _detect_backend(index_root)


def _sidecar_hit(hit: dict) -> dict:
    # Sidecar shape intentionally mirrors the top-level compact view today.
    # Phase 2.x can extend this to carry full document bodies when the
    # artifact size budget is comfortable with it.
    return {
        "path": hit["path"],
        "title": hit["title"],
        "category": hit["category"],
        "section_title": hit["section_title"],
        "section_path": list(hit.get("section_path") or []),
        "score": hit["score"],
        "snippet_preview": hit["snippet_preview"],
    }
