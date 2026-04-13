"""Cross-encoder reranker (lazy-loaded).

Used by searcher._rerank() after RRF fusion to polish the top pool. The
model is loaded on first call and cached in a module-level slot so repeat
calls within a single coach-run turn reuse it.

Environment knobs
-----------------
- ``WOOWA_RAG_NO_RERANK=1`` — disable reranking entirely (tests, fast runs).
  Checked by searcher._rerank_enabled(); this module also honors it as a
  second line of defense.

Contract
--------
- ``rerank(query, items)`` takes ``items = [(row_id, chunk_dict), ...]`` and
  returns ``[(row_id, rerank_score), ...]`` sorted best-first.
- Never raises for the caller — wraps import and inference errors and
  returns the input list unchanged so the searcher degrades gracefully.
"""

from __future__ import annotations

import os

RERANK_MODEL = "cross-encoder/mmarco-mMiniLMv2-L12-H384-v1"

_model = None  # lazy slot


def _get_model():
    global _model
    if _model is not None:
        return _model
    from sentence_transformers import CrossEncoder  # type: ignore

    _model = CrossEncoder(RERANK_MODEL)
    return _model


def rerank(
    query: str,
    items: list[tuple[int, dict]],
    *,
    max_pair_len: int = 512,
) -> list[tuple[int, float]]:
    """Score (query, chunk) pairs with the cross-encoder.

    Safe no-op on missing deps or empty input.
    """
    if not items:
        return []
    if os.environ.get("WOOWA_RAG_NO_RERANK") == "1":
        # Preserve input order as-is; scores are synthetic descending.
        return [(rid, float(len(items) - i)) for i, (rid, _) in enumerate(items)]

    try:
        model = _get_model()
    except Exception:
        return [(rid, float(len(items) - i)) for i, (rid, _) in enumerate(items)]

    pairs = [[query, _compose_passage(chunk)[:max_pair_len]] for _, chunk in items]
    try:
        scores = model.predict(pairs, show_progress_bar=False)
    except Exception:
        return [(rid, float(len(items) - i)) for i, (rid, _) in enumerate(items)]

    scored = [
        (items[i][0], float(scores[i])) for i in range(len(items))
    ]
    scored.sort(key=lambda t: (-t[1], t[0]))
    return scored


def _compose_passage(chunk: dict) -> str:
    """Same shape as indexer._embed_text — keeps reranker input consistent."""
    section_path = chunk.get("section_path") or []
    head = " > ".join(section_path) if section_path else chunk.get("title", "")
    body = chunk.get("body", "")
    return f"{head}\n\n{body}"
