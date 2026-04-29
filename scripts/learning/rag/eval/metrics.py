"""IR metric functions for graded relevance fixtures.

All inputs are pure Python primitives (no numpy in the public API) so unit
tests can assert exact rational values without floating-point fudge factors
beyond `math.isclose` tolerances.

Conventions:
- `ranked_paths`: ordered list[str] returned by the retriever (rank 1 first)
- `qrels`: dict[path -> grade in {1, 2, 3}] from the fixture's qrels list
- `relevant_paths`: set[str] of paths considered relevant for binary metrics
  (default rule: grade >= 2 — see plan §P1.1 step 2)
- `forbidden_paths`: set[str] from the fixture
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping

# ---------------------------------------------------------------------------
# Relevance threshold
# ---------------------------------------------------------------------------

DEFAULT_RELEVANT_GRADE = 2
"""Plan §P1.1 step 2 — grade >= 2 counts as relevant for hit/MRR/recall.

Companion paths (grade 1) get their own metric: companion_coverage_at_k.
"""


def relevant_paths_from_qrels(
    qrels: Mapping[str, int],
    min_grade: int = DEFAULT_RELEVANT_GRADE,
) -> set[str]:
    """Project qrels into a binary-relevant set using the grade threshold."""
    return {path for path, grade in qrels.items() if grade >= min_grade}


# ---------------------------------------------------------------------------
# Graded nDCG (Burges-style: gain = 2^grade - 1)
# ---------------------------------------------------------------------------

def _gain(grade: int) -> float:
    """Burges-style gain — 2^grade - 1.

    Grade 0 → 0, grade 1 → 1, grade 2 → 3, grade 3 → 7.
    Higher grades are weighted exponentially more, which is the standard
    formulation for graded nDCG in IR literature.
    """
    return float((1 << grade) - 1)


def _discount(rank: int) -> float:
    """Logarithmic position discount — 1 / log2(rank + 1).

    rank is 1-indexed (rank 1 → log2(2) = 1.0 → discount 1.0).
    """
    return 1.0 / math.log2(rank + 1)


def graded_dcg_at_k(
    ranked_paths: list[str],
    qrels: Mapping[str, int],
    k: int,
) -> float:
    """DCG@k under Burges-style graded gain.

    Paths not present in qrels contribute 0 (irrelevant).
    """
    if k <= 0:
        return 0.0
    total = 0.0
    for rank, path in enumerate(ranked_paths[:k], start=1):
        grade = qrels.get(path, 0)
        if grade <= 0:
            continue
        total += _gain(grade) * _discount(rank)
    return total


def graded_idcg_at_k(qrels: Mapping[str, int], k: int) -> float:
    """Ideal DCG@k — sort qrels by grade descending, take top-k."""
    if k <= 0:
        return 0.0
    sorted_grades = sorted(qrels.values(), reverse=True)
    total = 0.0
    for rank, grade in enumerate(sorted_grades[:k], start=1):
        if grade <= 0:
            continue
        total += _gain(grade) * _discount(rank)
    return total


def graded_ndcg_at_k(
    ranked_paths: list[str],
    qrels: Mapping[str, int],
    k: int,
) -> float:
    """nDCG@k = DCG@k / IDCG@k. Returns 0.0 when IDCG is 0."""
    idcg = graded_idcg_at_k(qrels, k)
    if idcg == 0.0:
        return 0.0
    return graded_dcg_at_k(ranked_paths, qrels, k) / idcg


# ---------------------------------------------------------------------------
# primary_nDCG — only grade-3 (primary) paths count as relevant
# ---------------------------------------------------------------------------

PRIMARY_GRADE = 3


def primary_ndcg_at_k(
    ranked_paths: list[str],
    qrels: Mapping[str, int],
    k: int,
) -> float:
    """nDCG@k using only primary (grade==3) paths as relevant.

    Plan §P1.1 step 2 — `primary_nDCG@k` is the most conservative quality
    signal because it ignores companion-fluff that can inflate full graded
    nDCG when a topic family has many adjacent docs.
    """
    primary_only = {p: 1 for p, g in qrels.items() if g == PRIMARY_GRADE}
    return graded_ndcg_at_k(ranked_paths, primary_only, k)


# ---------------------------------------------------------------------------
# MRR / hit@k / recall@k — binary relevance (grade >= threshold)
# ---------------------------------------------------------------------------

def mrr(
    ranked_paths: list[str],
    relevant_paths: Iterable[str],
) -> float:
    """Mean Reciprocal Rank for a single query.

    Returns 1/rank of the first relevant hit, or 0.0 if none in the ranking.
    Caller averages MRR across queries to get the mean.
    """
    relevant_set = set(relevant_paths)
    if not relevant_set:
        return 0.0
    for rank, path in enumerate(ranked_paths, start=1):
        if path in relevant_set:
            return 1.0 / rank
    return 0.0


def hit_at_k(
    ranked_paths: list[str],
    relevant_paths: Iterable[str],
    k: int,
) -> float:
    """1.0 if any relevant path appears in top-k, else 0.0.

    Use as: hit@k for a single query is binary; mean across queries is the
    hit-rate.
    """
    if k <= 0:
        return 0.0
    relevant_set = set(relevant_paths)
    if not relevant_set:
        return 0.0
    return 1.0 if any(p in relevant_set for p in ranked_paths[:k]) else 0.0


def recall_at_k(
    ranked_paths: list[str],
    relevant_paths: Iterable[str],
    k: int,
) -> float:
    """Fraction of relevant paths recovered in top-k. Returns 0.0 when no
    relevant paths exist (avoids division by zero)."""
    if k <= 0:
        return 0.0
    relevant_set = set(relevant_paths)
    if not relevant_set:
        return 0.0
    hits = sum(1 for p in ranked_paths[:k] if p in relevant_set)
    return hits / len(relevant_set)


# ---------------------------------------------------------------------------
# Companion coverage & forbidden rate (plan §P1.1 step 2 — separate signals)
# ---------------------------------------------------------------------------

def companion_coverage_at_k(
    ranked_paths: list[str],
    companion_paths: Iterable[str],
    k: int,
) -> float:
    """Fraction of companion paths (grade==1) appearing in top-k.

    Reported as a side signal — should not be the primary selection criterion
    because adjacent-family docs can inflate it.
    """
    if k <= 0:
        return 0.0
    companion_set = set(companion_paths)
    if not companion_set:
        return 0.0
    seen = sum(1 for p in ranked_paths[:k] if p in companion_set)
    return seen / len(companion_set)


def forbidden_rate_at_k(
    ranked_paths: list[str],
    forbidden_paths: Iterable[str],
    k: int,
) -> float:
    """Fraction of top-k slots occupied by forbidden paths.

    Lower is better. Tie-breaker in selection rule (plan §P8.1).
    Returns 0.0 when there are no forbidden paths defined for the query.
    """
    if k <= 0:
        return 0.0
    forbidden_set = set(forbidden_paths)
    if not forbidden_set:
        return 0.0
    hits = sum(1 for p in ranked_paths[:k] if p in forbidden_set)
    return hits / k
