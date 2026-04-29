"""Unit tests for scripts.learning.rag.eval.split.

Coverage targets:
- Determinism: same input + seed → identical splits across calls
- Iteration-order independence: shuffled input yields the same split
- Different seeds yield different splits on a non-trivial fixture
- holdout_ratio ≈ 30% on a representative size
- holdout_ratio extremes: 0.0 → no holdout, 1.0 → no tune
- Disjoint + covering invariant: tune ∩ holdout = ∅ and union covers all
- Empty input → ([], [])
- Single query honors holdout_ratio rounding
- Duplicate query_ids rejected
- holdout_ratio out of range rejected
"""

from __future__ import annotations

import pytest

from scripts.learning.rag.eval.split import (
    DEFAULT_HOLDOUT_RATIO,
    split_tune_holdout,
)
from scripts.learning.rag.eval.dataset import (
    Bucket,
    GradedQuery,
    Qrel,
    RankBudget,
)


def _q(qid: str) -> GradedQuery:
    return GradedQuery(
        query_id=qid,
        prompt="p",
        mode="full",
        experience_level=None,
        learning_points=(),
        bucket=Bucket("c", "d", "l", "i"),
        qrels=(Qrel("a.md", 3, "primary"),),
        forbidden_paths=(),
        rank_budget=RankBudget(1, 4),
        bucket_source="auto",
    )


def _bulk(n: int) -> list[GradedQuery]:
    return [_q(f"q{i:04d}") for i in range(n)]


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_same_input_and_seed_yield_identical_splits():
    queries = _bulk(100)
    a_tune, a_hold = split_tune_holdout(queries, seed=42)
    b_tune, b_hold = split_tune_holdout(queries, seed=42)
    assert [q.query_id for q in a_tune] == [q.query_id for q in b_tune]
    assert [q.query_id for q in a_hold] == [q.query_id for q in b_hold]


def test_iteration_order_independence():
    """Shuffling the input must not change the resulting partition —
    the function normalises by query_id before splitting."""
    queries = _bulk(50)
    forward_tune, forward_hold = split_tune_holdout(queries, seed=7)
    reversed_tune, reversed_hold = split_tune_holdout(list(reversed(queries)), seed=7)
    assert {q.query_id for q in forward_tune} == {q.query_id for q in reversed_tune}
    assert {q.query_id for q in forward_hold} == {q.query_id for q in reversed_hold}


def test_different_seed_changes_partition():
    queries = _bulk(50)
    _, hold_a = split_tune_holdout(queries, seed=1)
    _, hold_b = split_tune_holdout(queries, seed=2)
    # Holdout sets should differ for any reasonable size (here 15 elems
    # out of 50, the chance of identical sets across seeds is ~1e-12).
    assert {q.query_id for q in hold_a} != {q.query_id for q in hold_b}


# ---------------------------------------------------------------------------
# Ratio
# ---------------------------------------------------------------------------

def test_default_ratio_is_70_30():
    queries = _bulk(100)
    tune, holdout = split_tune_holdout(queries)
    # round(100 * 0.30) = 30 → 70/30
    assert len(tune) == 70
    assert len(holdout) == 30
    assert DEFAULT_HOLDOUT_RATIO == 0.30


def test_holdout_ratio_zero_yields_no_holdout():
    queries = _bulk(10)
    tune, holdout = split_tune_holdout(queries, holdout_ratio=0.0)
    assert len(tune) == 10
    assert len(holdout) == 0


def test_holdout_ratio_one_yields_no_tune():
    queries = _bulk(10)
    tune, holdout = split_tune_holdout(queries, holdout_ratio=1.0)
    assert len(tune) == 0
    assert len(holdout) == 10


def test_holdout_ratio_rounds_to_nearest_integer():
    """7 * 0.30 = 2.1 → round → 2 holdout / 5 tune."""
    queries = _bulk(7)
    tune, holdout = split_tune_holdout(queries, holdout_ratio=0.30)
    assert len(holdout) == 2
    assert len(tune) == 5


def test_holdout_ratio_out_of_range_raises():
    queries = _bulk(5)
    with pytest.raises(ValueError, match="holdout_ratio"):
        split_tune_holdout(queries, holdout_ratio=-0.1)
    with pytest.raises(ValueError, match="holdout_ratio"):
        split_tune_holdout(queries, holdout_ratio=1.1)


# ---------------------------------------------------------------------------
# Disjoint + covering invariant
# ---------------------------------------------------------------------------

def test_tune_and_holdout_are_disjoint_and_cover_all():
    queries = _bulk(338)  # match real fixture size for realism
    tune, holdout = split_tune_holdout(queries)
    tune_ids = {q.query_id for q in tune}
    holdout_ids = {q.query_id for q in holdout}
    assert tune_ids.isdisjoint(holdout_ids)
    assert tune_ids | holdout_ids == {q.query_id for q in queries}
    assert len(tune) + len(holdout) == len(queries)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_input_returns_two_empty_lists():
    assert split_tune_holdout([]) == ([], [])


def test_single_query_default_ratio_lands_in_tune():
    """round(1 * 0.30) = 0 → all 1 query goes to tune."""
    one = [_q("solo")]
    tune, holdout = split_tune_holdout(one)
    assert len(tune) == 1
    assert len(holdout) == 0


def test_two_queries_default_ratio_one_in_each():
    """round(2 * 0.30) = 1 → 1 tune / 1 holdout."""
    two = _bulk(2)
    tune, holdout = split_tune_holdout(two, seed=0)
    assert len(tune) == 1
    assert len(holdout) == 1


def test_duplicate_query_ids_rejected():
    queries = [_q("dup"), _q("dup"), _q("ok")]
    with pytest.raises(ValueError, match="duplicate query_ids"):
        split_tune_holdout(queries)
