"""Hybrid CS RAG searcher.

Pipeline
--------
1. Expand query via signal_rules.expand_query (original + rule expansions).
2. FTS5 MATCH to get top-N candidates (score = bm25, lower is better).
3. Dense cosine similarity top-N (skipped in ``cheap`` mode).
4. Reciprocal Rank Fusion (RRF, k=60) to merge the two rankings.
5. Category boost for learning-point ↔ CS category pairs.
6. Category filter — when learning_points are set, restrict the pool to the
   mapped categories so the reranker never sees off-topic noise (e.g. an
   auth doc winning a persistence query on surface-token overlap). If the
   filter would leave fewer than top_k items, fall back to unfiltered.
7. Optional cross-encoder rerank (skipped in ``cheap`` mode, env-disabled
   in tests via WOOWA_RAG_NO_RERANK=1).
8. Document-level dedupe — keep the best-scoring chunk per source path so
   a single document's sibling sections cannot monopolize top-K.
9. Return top-K dicts ready for cs_block rendering.

Modes
-----
- ``cheap``: FTS only + category boost. No ML deps loaded. Used by
  intent_router when pre_intent == "drill_answer" or for tests.
- ``full``: FTS + dense + RRF + (optional) rerank.

Contracts
---------
- ``search()`` returns a list of dicts with deterministic ordering.
- Lazy-imports numpy / sentence-transformers only when needed.
- Never raises on empty corpus — returns [].
"""

from __future__ import annotations

import math
import os
import re
import sqlite3
from pathlib import Path
from typing import Iterable

from . import category_mapping, indexer, signal_rules

RRF_K = 60
DEFAULT_TOP_K = 5
FTS_POOL_SIZE = 40
DENSE_POOL_SIZE = 40
CATEGORY_BOOST = 0.15  # added to final score when category matches a learning point

# Difficulty boost ladder — applied as a tie-breaker inside the top pool only,
# so it never promotes an unrelated doc into the candidate set. Experience
# levels other than beginner/intermediate keep the legacy zero-boost behavior
# to guarantee zero diff against existing golden fixtures.
#
# Magnitudes are intentionally an order of magnitude smaller than CATEGORY_BOOST
# (0.15) so a clearly-more-relevant advanced doc still beats a marginally
# relevant beginner doc, while ties are broken in favor of the learner level.
DIFFICULTY_BOOST_LADDER: dict[str | None, dict[str | None, float]] = {
    "beginner": {
        "beginner": 0.04,
        "intermediate": 0.02,
        "advanced": 0.0,
        "expert": -0.01,
        None: 0.0,
    },
    "intermediate": {
        "beginner": 0.01,
        "intermediate": 0.03,
        "advanced": 0.01,
        "expert": 0.0,
        None: 0.0,
    },
}


# ---------------------------------------------------------------------------
# FTS query sanitization
# ---------------------------------------------------------------------------

_FTS_TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣]+")


def _to_fts_query(tokens: Iterable[str]) -> str:
    """Build a defensive FTS5 MATCH string from free tokens.

    Each token is quoted so punctuation cannot break the parser, and the
    tokens are OR-joined.
    """
    quoted: list[str] = []
    seen: set[str] = set()
    for tok in tokens:
        # extract only matchable segments; drop stray chars
        for piece in _FTS_TOKEN_RE.findall(tok):
            key = piece.lower()
            if len(key) < 2 or key in seen:
                continue
            seen.add(key)
            quoted.append(f'"{piece}"')
    return " OR ".join(quoted)


# ---------------------------------------------------------------------------
# FTS search
# ---------------------------------------------------------------------------

def _fts_search(
    conn: sqlite3.Connection,
    fts_query: str,
    limit: int,
) -> list[tuple[int, float]]:
    """Return ``[(row_id, bm25_score)]``. Lower score = better match."""
    if not fts_query:
        return []
    try:
        cur = conn.execute(
            """
            SELECT chunks_fts.rowid, bm25(chunks_fts)
            FROM chunks_fts
            WHERE chunks_fts MATCH ?
            ORDER BY bm25(chunks_fts)
            LIMIT ?
            """,
            (fts_query, limit),
        )
    except sqlite3.OperationalError:
        return []
    return [(row[0], row[1]) for row in cur.fetchall()]


# ---------------------------------------------------------------------------
# Dense search (lazy)
# ---------------------------------------------------------------------------

_QUERY_EMBEDDER = None  # module-level cache to avoid reloading per query


def _get_query_embedder():
    global _QUERY_EMBEDDER
    if _QUERY_EMBEDDER is not None:
        return _QUERY_EMBEDDER
    from sentence_transformers import SentenceTransformer  # type: ignore

    _QUERY_EMBEDDER = SentenceTransformer(indexer.EMBED_MODEL)
    return _QUERY_EMBEDDER


def _load_query_vector(prompt: str, topic_hints: list[str] | None):
    import numpy as np  # type: ignore

    model = _get_query_embedder()
    text = prompt
    if topic_hints:
        text = f"{prompt}\n\n" + "\n".join(topic_hints)
    vec = model.encode(
        [text],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return np.asarray(vec[0], dtype="float32")


def _dense_search(
    index_root: Path | str,
    prompt: str,
    topic_hints: list[str] | None,
    limit: int,
) -> list[tuple[int, float]]:
    """Return ``[(row_id, similarity)]`` where similarity is in [-1, 1]."""
    try:
        import numpy as np  # type: ignore
    except ImportError:
        return []
    try:
        embeddings, row_ids = indexer.load_dense(index_root)
    except (FileNotFoundError, OSError):
        return []
    try:
        qvec = _load_query_vector(prompt, topic_hints)
    except Exception:
        return []
    if embeddings.shape[0] == 0:
        return []
    sims = embeddings @ qvec  # (N,)
    top = np.argsort(-sims)[:limit]
    return [(int(row_ids[i]), float(sims[i])) for i in top]


# ---------------------------------------------------------------------------
# Reciprocal Rank Fusion
# ---------------------------------------------------------------------------

def _rrf_merge(
    rankings: list[list[tuple[int, float]]],
    k: int = RRF_K,
) -> list[tuple[int, float]]:
    """Merge multiple (row_id, score) rankings into a single fused ranking.

    RRF formula: score_rrf(d) = Σ 1 / (k + rank(d in list_i))
    """
    fused: dict[int, float] = {}
    for ranking in rankings:
        for rank, (row_id, _) in enumerate(ranking, start=1):
            fused[row_id] = fused.get(row_id, 0.0) + 1.0 / (k + rank)
    return sorted(fused.items(), key=lambda t: (-t[1], t[0]))


# ---------------------------------------------------------------------------
# Category boost
# ---------------------------------------------------------------------------

def _apply_category_boost(
    scored: list[tuple[int, float]],
    chunks: dict[int, dict],
    allowed_categories: set[str],
) -> list[tuple[int, float]]:
    if not allowed_categories:
        return scored
    boosted: list[tuple[int, float]] = []
    for row_id, score in scored:
        chunk = chunks.get(row_id)
        if chunk and chunk["category"] in allowed_categories:
            score = score + CATEGORY_BOOST
        boosted.append((row_id, score))
    boosted.sort(key=lambda t: (-t[1], t[0]))
    return boosted


def _apply_difficulty_boost(
    scored: list[tuple[int, float]],
    chunks: dict[int, dict],
    experience_level: str | None,
) -> list[tuple[int, float]]:
    """Re-rank the existing pool toward the learner's level.

    No-op when ``experience_level`` is None or not in the ladder (advanced /
    expert learners keep legacy ranking exactly). Applied after category
    boost so the discovery set is unchanged — purely a tie-breaker on the
    candidates that already passed FTS+dense+category filtering.
    """
    if not experience_level:
        return scored
    ladder = DIFFICULTY_BOOST_LADDER.get(experience_level)
    if ladder is None:
        return scored
    boosted: list[tuple[int, float]] = []
    for row_id, score in scored:
        chunk = chunks.get(row_id)
        delta = ladder.get((chunk or {}).get("difficulty"), 0.0) if chunk else 0.0
        boosted.append((row_id, score + delta))
    boosted.sort(key=lambda t: (-t[1], t[0]))
    return boosted


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def search(
    prompt: str,
    *,
    learning_points: list[str] | None = None,
    topic_hints: list[str] | None = None,
    top_k: int = DEFAULT_TOP_K,
    mode: str = "full",
    index_root: Path | str = indexer.DEFAULT_INDEX_ROOT,
    use_reranker: bool | None = None,
    experience_level: str | None = None,
    debug: dict | None = None,
) -> list[dict]:
    """Run a hybrid CS RAG search and return top-K chunk dicts.

    Each output item::

        {
            "row_id", "doc_id", "chunk_id", "path", "title",
            "category", "section_title", "section_path",
            "score", "snippet_preview", "anchors"
        }
    """
    if mode not in ("cheap", "full"):
        raise ValueError(f"unknown mode: {mode}")

    try:
        conn = indexer.open_readonly(index_root)
    except FileNotFoundError:
        return []

    try:
        # 1. Query expansion
        tokens = signal_rules.expand_query(prompt, topic_hints)
        fts_query = _to_fts_query(tokens or _fallback_tokens(prompt))

        # 2. FTS ranking
        fts_hits = _fts_search(conn, fts_query, FTS_POOL_SIZE)

        rankings: list[list[tuple[int, float]]] = []
        if fts_hits:
            rankings.append(fts_hits)

        # 3. Dense ranking (full mode only)
        if mode == "full":
            dense_hits = _dense_search(index_root, prompt, topic_hints, DENSE_POOL_SIZE)
            if dense_hits:
                rankings.append(dense_hits)

        if not rankings:
            return []

        # 4. RRF fusion
        fused = _rrf_merge(rankings)

        # Resolve chunk rows for boost + output
        top_pool_ids = [rid for rid, _ in fused[: max(top_k * 4, 20)]]
        chunks = indexer.fetch_chunks_by_rowid(conn, top_pool_ids)

        # 5. Category boost
        allowed_categories = _collect_categories(learning_points)
        boosted = _apply_category_boost(
            [(rid, sc) for rid, sc in fused if rid in chunks],
            chunks,
            allowed_categories,
        )

        # 5b. Difficulty boost — re-rank the existing top pool toward the
        #     learner's experience level. No-op for advanced/expert learners
        #     and when experience_level is None, so legacy goldens are
        #     untouched. Applied to the same `boosted` pool so the discovery
        #     set is never widened by difficulty alone.
        boosted = _apply_difficulty_boost(boosted, chunks, experience_level)

        # 6. Category filter — keep only chunks whose category matches the
        #    learning points, if any. Falls back to unfiltered when the
        #    filter would leave fewer than top_k candidates.
        filtered, filter_fallback_used = _filter_allowed_categories(
            boosted, chunks, allowed_categories, top_k
        )
        if debug is not None:
            debug["category_filter_fallback"] = filter_fallback_used
            debug["allowed_categories"] = sorted(allowed_categories)

        # 7. Optional rerank (full mode only). Decorate the prompt with
        #    learning-point anchor phrases so the reranker sees canonical
        #    domain terms (fixes e.g. "책임 분리" collapsing onto
        #    "Chain of Responsibility" on raw token overlap).
        if mode == "full" and _rerank_enabled(use_reranker):
            anchor = category_mapping.anchor_phrase_for(learning_points)
            rerank_prompt = f"{anchor}\n\n{prompt}" if anchor else prompt
            filtered = _rerank(rerank_prompt, filtered, chunks, top_n=top_k * 2)

        # 8. Document-level dedupe — one chunk per source path
        deduped = _dedupe_by_path(filtered, chunks)

        # 9. Compose output
        return [_format_hit(chunks[rid], score) for rid, score in deduped[:top_k]]
    finally:
        conn.close()


def _fallback_tokens(prompt: str) -> list[str]:
    """When signal_rules.expand_query returns empty (short prompt)."""
    return [tok for tok in _FTS_TOKEN_RE.findall(prompt) if len(tok) >= 2]


def _collect_categories(learning_points: list[str] | None) -> set[str]:
    if not learning_points:
        return set()
    allowed: set[str] = set()
    for lp in learning_points:
        allowed.update(category_mapping.categories_for(lp))
    return allowed


def _rerank_enabled(use_reranker: bool | None) -> bool:
    if use_reranker is False:
        return False
    if os.environ.get("WOOWA_RAG_NO_RERANK") == "1":
        return False
    return use_reranker is True or use_reranker is None  # default on


def _filter_allowed_categories(
    scored: list[tuple[int, float]],
    chunks: dict[int, dict],
    allowed_categories: set[str],
    min_keep: int,
) -> tuple[list[tuple[int, float]], bool]:
    """Filter the pool to chunks whose category is in ``allowed_categories``.

    When ``allowed_categories`` is empty (no learning points supplied) the
    pool is returned untouched. If strict filtering would leave fewer than
    ``min_keep`` items (too narrow — e.g. a learning point mapped to a
    single category with thin coverage), the original unfiltered pool is
    returned so retrieval still produces an answer.

    Returns ``(pool, fallback_used)``. ``fallback_used`` is True when the
    strict filter would have starved the pool and the unfiltered result
    was returned instead — callers surface this as observability so AI
    sessions can footnote "results from outside the expected category".
    """
    if not allowed_categories:
        return scored, False
    kept: list[tuple[int, float]] = []
    for row_id, score in scored:
        chunk = chunks.get(row_id)
        if chunk is None:
            continue
        if chunk["category"] in allowed_categories:
            kept.append((row_id, score))
    if len(kept) < min_keep:
        return scored, True
    return kept, False


def _dedupe_by_path(
    scored: list[tuple[int, float]],
    chunks: dict[int, dict],
) -> list[tuple[int, float]]:
    """Keep only the first (highest-ranked) chunk per source path.

    Preserves input order, so whatever upstream ranking determined the
    winner wins. Chunks whose row_id is missing from the chunk map are
    dropped silently.
    """
    seen: set[str] = set()
    out: list[tuple[int, float]] = []
    for row_id, score in scored:
        chunk = chunks.get(row_id)
        if chunk is None:
            continue
        path = chunk["path"]
        if path in seen:
            continue
        seen.add(path)
        out.append((row_id, score))
    return out


def _rerank(
    prompt: str,
    scored: list[tuple[int, float]],
    chunks: dict[int, dict],
    top_n: int,
) -> list[tuple[int, float]]:
    try:
        from .reranker import rerank  # type: ignore
    except ImportError:
        return scored
    pool = scored[:top_n]
    try:
        reranked = rerank(prompt, [(rid, chunks[rid]) for rid, _ in pool if rid in chunks])
    except Exception:
        return scored
    reranked_ids = {rid for rid, _ in reranked}
    tail = [item for item in scored if item[0] not in reranked_ids]
    return reranked + tail


def _format_hit(chunk: dict, score: float) -> dict:
    body = chunk["body"]
    snippet = body[:250].replace("\n", " ").strip()
    if len(body) > 250:
        snippet += "…"
    return {
        "row_id": chunk["row_id"],
        "doc_id": chunk["doc_id"],
        "chunk_id": chunk["chunk_id"],
        "path": chunk["path"],
        "title": chunk["title"],
        "category": chunk["category"],
        "section_title": chunk["section_title"],
        "section_path": chunk["section_path"],
        "score": round(score, 6),
        "snippet_preview": snippet,
        "anchors": chunk["anchors"],
    }
