"""Deterministic tune/holdout split of GradedQuery sequences.

Plan §P1.1 step 6 — fusion grid search and other hyperparameter tuning
must run on the *tune* split only; the final acceptance decision uses
the *holdout* split. Without this discipline a model picked for its
tune-set score over-fits the very fixture that's supposed to certify
it.

Determinism contract:
- Same input list + same seed → identical (tune, holdout) tuples.
- Order of the input list is normalised by query_id before shuffling
  so callers don't have to care about iteration stability.
- ``holdout_ratio`` is preserved within ±1 query (rounding).
- Edge cases (0/1/2 queries) handled without raising.
"""

from __future__ import annotations

import random
from collections.abc import Sequence

from .dataset import GradedQuery

DEFAULT_HOLDOUT_RATIO = 0.30
"""Plan §P1.1 step 6 — 70/30 tune/holdout. Configurable but the default
is the canonical contract."""


def split_tune_holdout(
    queries: Sequence[GradedQuery],
    *,
    seed: int = 0,
    holdout_ratio: float = DEFAULT_HOLDOUT_RATIO,
) -> tuple[list[GradedQuery], list[GradedQuery]]:
    """Split ``queries`` into (tune, holdout) deterministically.

    Args:
        queries: source queries; iteration order does NOT affect the result.
        seed: RNG seed (default 0). Different seeds produce different
            shuffles but each (queries, seed) pair always yields the
            same partition.
        holdout_ratio: fraction reserved for holdout, in [0.0, 1.0].

    Returns:
        ``(tune_list, holdout_list)`` — disjoint, union covers all
        unique-by-id input queries.

    Raises:
        ValueError if holdout_ratio is outside [0.0, 1.0].
        ValueError if input contains duplicate query_ids — duplicates
            would let the same query appear in both splits, defeating
            the point.
    """
    if not 0.0 <= holdout_ratio <= 1.0:
        raise ValueError(
            f"holdout_ratio must be in [0.0, 1.0], got {holdout_ratio!r}"
        )

    materialised = list(queries)
    if not materialised:
        return [], []

    seen_ids: set[str] = set()
    duplicates: list[str] = []
    for q in materialised:
        if q.query_id in seen_ids:
            duplicates.append(q.query_id)
        seen_ids.add(q.query_id)
    if duplicates:
        raise ValueError(
            f"duplicate query_ids in split input: {sorted(set(duplicates))!r}"
        )

    # Normalise iteration order BEFORE shuffling so callers can't
    # influence the partition by reordering the input.
    sorted_queries = sorted(materialised, key=lambda q: q.query_id)

    rng = random.Random(seed)
    indexes = list(range(len(sorted_queries)))
    rng.shuffle(indexes)

    holdout_size = round(len(sorted_queries) * holdout_ratio)
    holdout_indexes = set(indexes[:holdout_size])

    tune: list[GradedQuery] = []
    holdout: list[GradedQuery] = []
    for i, q in enumerate(sorted_queries):
        if i in holdout_indexes:
            holdout.append(q)
        else:
            tune.append(q)
    return tune, holdout
