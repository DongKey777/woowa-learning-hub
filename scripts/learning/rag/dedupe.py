"""Embedding-based dedupe candidate finder (plan §P5.4).

Surfaces document pairs whose embeddings are suspiciously similar
(cosine ≥ 0.92 by default). Output drives the P5.5 manual dedupe
pass — humans decide which doc supersedes which, the script only
identifies *candidates*.

Pure algorithmic core: takes pre-computed embeddings and returns
``DedupePair`` triples. The corpus_lint integration layer
(``corpus_dedupe_runner``) loads either the production LanceDB v3 table or an
archived legacy SQLite/NPZ index and calls this. Keeping the algorithm
embedding-source-agnostic lets tests use synthetic vectors.

## Granularity

The CS index has multiple chunks per doc (H2 splits). Two docs
covering the same concept usually have many similar chunks but
different framing. We aggregate to **doc-level** by averaging the
chunk embeddings per doc path, then run pairwise cosine on
unit-normalized averages. Loses some precision vs. max-chunk
similarity but is fast (O(D²·dim) instead of O(C²·dim)) and
matches the use case (triage, not exhaustive ground-truth).

## Scope

By default, all docs are compared pairwise. ``scope_fn`` lets the
caller restrict comparison — typically by category prefix so
comparing ``database/transactions.md`` to ``algorithm/dfs.md`` is
skipped (waste of compute, no signal).

## Determinism

Same embeddings + same paths + same threshold → identical pair list,
sorted by descending cosine then ``(path_a, path_b)`` ascending.

Tested in ``tests/unit/test_corpus_dedupe.py``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Iterable


DEFAULT_COSINE_THRESHOLD = 0.92


@dataclass(frozen=True)
class DedupePair:
    path_a: str
    path_b: str
    cosine: float

    def to_dict(self) -> dict:
        return {
            "path_a": self.path_a,
            "path_b": self.path_b,
            "cosine": self.cosine,
        }


# ---------------------------------------------------------------------------
# Core math
# ---------------------------------------------------------------------------

def aggregate_by_path(
    embeddings,  # shape (N, D), dtype float32
    paths: list[str],
):
    """Mean-aggregate chunk embeddings per doc path. Returns
    ``(unique_paths, mean_embeddings)`` with shape ``(M, D)`` where
    ``M`` is the number of distinct paths.

    Order of ``unique_paths`` is the *first occurrence* in ``paths``,
    so two runs over the same input produce identical aggregates.
    """
    try:
        import numpy as np  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("numpy not installed.") from exc

    if len(paths) != embeddings.shape[0]:
        raise ValueError(
            f"paths length ({len(paths)}) != embeddings rows ({embeddings.shape[0]})"
        )
    seen_index: dict[str, int] = {}
    sums: list = []
    counts: list[int] = []
    for i, p in enumerate(paths):
        if p not in seen_index:
            seen_index[p] = len(sums)
            sums.append(np.zeros(embeddings.shape[1], dtype="float64"))
            counts.append(0)
        idx = seen_index[p]
        sums[idx] += embeddings[i].astype("float64", copy=False)
        counts[idx] += 1
    means = np.zeros((len(sums), embeddings.shape[1]), dtype="float32")
    for j, (s, c) in enumerate(zip(sums, counts)):
        means[j] = (s / max(c, 1)).astype("float32")
    return list(seen_index.keys()), means


def _normalize_rows(matrix):
    """Return ``matrix`` with each row L2-normalised. Zero rows stay
    zero (no division-by-zero)."""
    import numpy as np  # type: ignore
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return matrix / norms


def find_near_duplicate_pairs(
    embeddings,
    paths: list[str],
    *,
    threshold: float = DEFAULT_COSINE_THRESHOLD,
    scope_fn: Callable[[str, str], bool] | None = None,
) -> list[DedupePair]:
    """Find doc pairs with cosine ≥ ``threshold``.

    Args:
      embeddings: numpy array shape (N, D), float32.
      paths: list of N doc paths (one per chunk).
      threshold: cosine similarity threshold (0.0 to 1.0).
      scope_fn: optional callable ``(path_a, path_b) -> bool`` that
        returns True when the pair should be evaluated. False skips.
        Default: compare every pair (None).

    Returns:
      Sorted list of ``DedupePair``. Sort key: ``(-cosine, path_a, path_b)``
      so the most similar pair comes first and ties break alphabetically.
    """
    if not (0.0 <= threshold <= 1.0):
        raise ValueError("threshold must be in [0, 1]")
    try:
        import numpy as np  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("numpy not installed.") from exc

    unique_paths, doc_means = aggregate_by_path(embeddings, paths)
    if len(unique_paths) < 2:
        return []

    # Normalize once so cosine = dot product.
    normed = _normalize_rows(doc_means)

    # Pairwise cosine via single matmul. For 2K docs at 1024-dim this
    # is a 2K×2K matrix = ~16MB — fine even on M4 16GB. For 100K+ docs
    # we'd switch to a streaming approach, but P5.4 corpus is small.
    sims = normed @ normed.T  # shape (M, M)
    M = len(unique_paths)

    pairs: list[DedupePair] = []
    for i in range(M):
        for j in range(i + 1, M):
            if scope_fn is not None and not scope_fn(unique_paths[i], unique_paths[j]):
                continue
            cos = float(sims[i, j])
            if cos >= threshold:
                # Order pair alphabetically for stable output
                a, b = unique_paths[i], unique_paths[j]
                if a > b:
                    a, b = b, a
                pairs.append(DedupePair(path_a=a, path_b=b, cosine=cos))

    pairs.sort(key=lambda p: (-p.cosine, p.path_a, p.path_b))
    return pairs


# ---------------------------------------------------------------------------
# Scope helpers
# ---------------------------------------------------------------------------

def same_category_scope(path_a: str, path_b: str) -> bool:
    """Compare only docs whose first path segment matches.

    ``knowledge/cs/contents/spring/bean.md`` vs.
    ``knowledge/cs/contents/spring/component.md`` → True
    ``knowledge/cs/contents/spring/bean.md`` vs.
    ``knowledge/cs/contents/algorithm/dfs.md`` → False

    Cuts pair count by ~10× for the cs corpus, so dedupe scan finishes
    in seconds even on the full chunk set.
    """
    return _category_of(path_a) == _category_of(path_b)


def _category_of(path: str) -> str:
    """Return the first path segment after ``contents/`` (or the first
    segment if ``contents/`` is absent)."""
    parts = path.replace("\\", "/").split("/")
    try:
        idx = parts.index("contents")
        return parts[idx + 1] if idx + 1 < len(parts) else ""
    except ValueError:
        return parts[0] if parts else ""
