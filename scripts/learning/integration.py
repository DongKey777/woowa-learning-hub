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

import time
from pathlib import Path
from typing import Any

from .rag import category_mapping, signal_rules
from .rag import indexer as rag_indexer


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
    }


def augment(
    *,
    prompt: str,
    learning_points: list[str] | None = None,
    topic_hints: list[str] | None = None,
    cs_search_mode: str = "full",
    index_root: Path | str = rag_indexer.DEFAULT_INDEX_ROOT,
    top_k: int = 5,
    readiness: rag_indexer.ReadinessReport | None = None,
    experience_level: str | None = None,
    learner_context: dict[str, Any] | None = None,
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
    backend = _detect_backend(index_root)

    by_lp: dict[str, list[dict]] = {}
    by_fallback: dict[str, list[dict]] = {}
    fallback_reason: str | None = None
    all_hits: list[dict] = []
    seen_paths: set[str] = set()
    category_filter_fallback = False

    try:
        if learning_points:
            # Peer-derived path: search once per learning point so each
            # bucket reflects its own category boost.
            for lp in learning_points:
                lp_debug: dict = {}
                hits = searcher.search(
                    prompt,
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
                if hits:
                    by_lp[lp] = hits
                    for h in hits:
                        if h["path"] not in seen_paths:
                            seen_paths.add(h["path"])
                            all_hits.append(h)

        # If no peer learning point matched (cs_only turn) or all buckets
        # came back empty, fall back to signal-tag bucketing.
        if not by_lp:
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
                    hits = searcher.search(
                        prompt,
                        learning_points=None,
                        topic_hints=topic_hints,
                        mode=cs_search_mode,
                        backend=backend,
                        index_root=index_root,
                        top_k=top_k,
                        experience_level=experience_level,
                        learner_context=learner_context,
                    )
                    if hits:
                        by_fallback[key] = hits
                        for h in hits:
                            if h["path"] not in seen_paths:
                                seen_paths.add(h["path"])
                                all_hits.append(h)
                        # One search is enough — signal tags share the
                        # same query, only the bucket key differs. Keep
                        # the rest of the signals as bucket aliases.
                        break
            else:
                key = f"general:{_top_token(prompt)}"
                hits = searcher.search(
                    prompt,
                    learning_points=None,
                    topic_hints=topic_hints,
                    mode=cs_search_mode,
                    backend=backend,
                    index_root=index_root,
                    top_k=top_k,
                    experience_level=experience_level,
                    learner_context=learner_context,
                )
                if hits:
                    by_fallback[key] = hits
                    for h in hits:
                        if h["path"] not in seen_paths:
                            seen_paths.add(h["path"])
                            all_hits.append(h)
    except Exception:
        return _empty_result("search_error", cs_search_mode)

    latency_ms = int((time.time() - start) * 1000)

    categories_hit = sorted({h["category"] for h in all_hits})

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

    return {
        "by_learning_point": by_lp,
        "by_fallback_key": by_fallback,
        "fallback_reason": fallback_reason,
        "cs_categories_hit": categories_hit,
        "sidecar": sidecar,
        "meta": {
            "latency_ms": latency_ms,
            "rag_ready": True,
            "reason": "ready",
            "mode_used": cs_search_mode,
            "backend": backend,
            "category_filter_fallback": category_filter_fallback,
        },
    }


def _top_token(prompt: str) -> str:
    tokens = signal_rules._tokenize(prompt)  # internal tokenizer is fine here
    return tokens[0] if tokens else "unknown"


def _detect_backend(index_root: Path | str) -> str:
    """Infer the search backend from the index manifest version."""
    try:
        manifest = rag_indexer.load_manifest(index_root)
    except Exception:
        return "legacy"
    try:
        version = int(manifest.get("index_version", rag_indexer.INDEX_VERSION))
    except (TypeError, ValueError):
        return "legacy"
    return "lance" if version >= rag_indexer.LANCE_INDEX_VERSION else "legacy"


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
