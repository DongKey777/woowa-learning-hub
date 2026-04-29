"""Unit tests for scripts.learning.rag.eval.hard_regression.

Coverage targets — hard gates (must fail PR):
- primary at rank 1 within budget=1: passes
- primary at rank 2 with budget=1: fails (primary_over_budget)
- primary at rank 3 with budget=3: passes (boundary)
- primary missing entirely: fails (primary_not_present)
- forbidden in top-k window: fails (forbidden_in_topk)
- forbidden outside window: passes
- multiple violations on one query: all reported
- multiple primary paths: each checked independently
- forbidden_window override

Soft warnings (do NOT fail):
- companion before primary: warning emitted, passed stays True
- companion after primary: no warning

Aggregation:
- summarise counts pass/fail correctly
- summarise buckets violations by kind
- summarise.all_passed true when failed_count=0
- failed_query_ids preserves order
"""

from __future__ import annotations

import pytest

from scripts.learning.rag.eval.dataset import (
    Bucket,
    GradedQuery,
    Qrel,
    RankBudget,
)
from scripts.learning.rag.eval import hard_regression as HR


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _query(
    *,
    primary: str = "primary.md",
    acceptable: tuple[str, ...] = (),
    companion: tuple[str, ...] = (),
    forbidden: tuple[str, ...] = (),
    primary_max_rank: int = 1,
    companion_max_rank: int = 4,
    qid: str = "q",
) -> GradedQuery:
    qrels = [Qrel(primary, 3, "primary")]
    qrels.extend(Qrel(p, 2, "acceptable") for p in acceptable)
    qrels.extend(Qrel(p, 1, "companion") for p in companion)
    return GradedQuery(
        query_id=qid,
        prompt="p",
        mode="full",
        experience_level=None,
        learning_points=(),
        bucket=Bucket("c", "d", "l", "i"),
        qrels=tuple(qrels),
        forbidden_paths=forbidden,
        rank_budget=RankBudget(primary_max_rank, companion_max_rank),
        bucket_source="auto",
    )


# ---------------------------------------------------------------------------
# Hard gate 1: primary in budget
# ---------------------------------------------------------------------------

def test_primary_at_rank_one_within_budget_one_passes():
    q = _query(primary_max_rank=1)
    r = HR.check_query(q, ["primary.md", "x.md", "y.md"])
    assert r.passed is True
    assert r.violations == ()


def test_primary_at_rank_two_with_budget_one_fails():
    q = _query(primary_max_rank=1)
    r = HR.check_query(q, ["x.md", "primary.md", "y.md"])
    assert r.passed is False
    assert any("primary_over_budget" in v for v in r.violations)
    # Error message names the actual rank and the budget
    assert any("rank 2" in v and "budget=1" in v for v in r.violations)


def test_primary_at_budget_boundary_passes():
    q = _query(primary_max_rank=3)
    r = HR.check_query(q, ["x.md", "y.md", "primary.md"])
    assert r.passed is True


def test_primary_missing_from_ranking_fails():
    q = _query(primary_max_rank=1)
    r = HR.check_query(q, ["x.md", "y.md"])
    assert r.passed is False
    assert any("primary_not_present" in v for v in r.violations)


def test_multiple_primaries_each_checked_independently():
    """If two primaries are listed, both must satisfy the budget — one
    passing isn't enough."""
    q = GradedQuery(
        query_id="multi",
        prompt="p",
        mode="full",
        experience_level=None,
        learning_points=(),
        bucket=Bucket("c", "d", "l", "i"),
        qrels=(
            Qrel("p1.md", 3, "primary"),
            Qrel("p2.md", 3, "primary"),
        ),
        forbidden_paths=(),
        rank_budget=RankBudget(1, 4),
        bucket_source="auto",
    )
    r = HR.check_query(q, ["p1.md", "x.md", "p2.md"])
    assert r.passed is False
    assert any("p2.md" in v for v in r.violations)


# ---------------------------------------------------------------------------
# Hard gate 2: forbidden in top-k
# ---------------------------------------------------------------------------

def test_forbidden_in_topk_fails():
    q = _query(forbidden=("bad.md",))
    r = HR.check_query(q, ["primary.md", "bad.md", "x.md"], forbidden_window=5)
    assert r.passed is False
    assert any("forbidden_in_topk" in v for v in r.violations)
    assert any("bad.md" in v for v in r.violations)


def test_forbidden_outside_window_passes():
    """If the forbidden path appears outside the configured window, no
    violation."""
    q = _query(forbidden=("bad.md",))
    ranked = ["primary.md", "x.md", "y.md", "z.md", "w.md", "bad.md"]
    r = HR.check_query(q, ranked, forbidden_window=5)
    assert r.passed is True


def test_forbidden_window_override():
    q = _query(forbidden=("bad.md",))
    ranked = ["primary.md", "x.md", "bad.md"]
    # window=2 → bad.md at rank 3 is outside; passes
    assert HR.check_query(q, ranked, forbidden_window=2).passed is True
    # window=3 → bad.md at rank 3 is inside; fails
    assert HR.check_query(q, ranked, forbidden_window=3).passed is False


def test_no_forbidden_paths_means_no_check():
    q = _query(forbidden=())
    r = HR.check_query(q, ["primary.md", "anything.md"])
    assert r.passed is True
    assert not any("forbidden" in v for v in r.violations)


# ---------------------------------------------------------------------------
# Combined violations
# ---------------------------------------------------------------------------

def test_multiple_violations_all_reported():
    q = _query(primary_max_rank=1, forbidden=("bad.md",))
    # primary at rank 3 (over budget) + bad.md in top-k → both violations
    r = HR.check_query(q, ["x.md", "bad.md", "primary.md"])
    assert r.passed is False
    kinds = {v.split(":")[0] for v in r.violations}
    assert "primary_over_budget" in kinds
    assert "forbidden_in_topk" in kinds


# ---------------------------------------------------------------------------
# Soft warning: companion before primary
# ---------------------------------------------------------------------------

def test_companion_before_primary_is_warning_not_violation():
    q = _query(primary_max_rank=3, companion=("comp.md",))
    r = HR.check_query(q, ["comp.md", "x.md", "primary.md"])
    # Hard gate: primary at rank 3, budget=3 → passes
    assert r.passed is True
    # Soft warning: companion at rank 1 < primary at rank 3
    assert any("companion_before_primary" in w for w in r.warnings)


def test_companion_after_primary_no_warning():
    q = _query(primary_max_rank=1, companion=("comp.md",))
    r = HR.check_query(q, ["primary.md", "comp.md", "x.md"])
    assert r.passed is True
    assert r.warnings == ()


def test_no_companion_means_no_warning():
    q = _query(primary_max_rank=1)
    r = HR.check_query(q, ["primary.md"])
    assert r.warnings == ()


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def test_summarise_counts_pass_fail():
    results = [
        HR.RegressionResult("a", True, ()),
        HR.RegressionResult("b", False, ("primary_over_budget: ...",)),
        HR.RegressionResult("c", False, ("forbidden_in_topk: ...",)),
        HR.RegressionResult("d", True, ()),
    ]
    s = HR.summarise(results)
    assert s.total == 4
    assert s.passed_count == 2
    assert s.failed_count == 2
    assert s.all_passed is False
    assert s.failed_query_ids == ("b", "c")


def test_summarise_buckets_violations_by_kind():
    results = [
        HR.RegressionResult("a", False, ("primary_over_budget: x", "forbidden_in_topk: y")),
        HR.RegressionResult("b", False, ("primary_over_budget: z",)),
        HR.RegressionResult("c", True, ()),
    ]
    s = HR.summarise(results)
    assert s.violations_by_kind == {"primary_over_budget": 2, "forbidden_in_topk": 1}


def test_summarise_all_passed_true_when_zero_failures():
    results = [HR.RegressionResult("a", True, ()), HR.RegressionResult("b", True, ())]
    assert HR.summarise(results).all_passed is True


def test_summarise_buckets_warnings_by_kind():
    results = [
        HR.RegressionResult(
            "a",
            True,
            (),
            warnings=("companion_before_primary: ...",),
        ),
    ]
    s = HR.summarise(results)
    assert s.warnings_by_kind == {"companion_before_primary": 1}
