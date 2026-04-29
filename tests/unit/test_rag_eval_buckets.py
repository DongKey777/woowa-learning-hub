"""Unit tests for scripts.learning.rag.eval.buckets.

Coverage targets:
- group_indexes_by_axis preserves insertion order
- macro vs micro mean: divergence under unbalanced bucket sizes
- 'unknown' bucket exclusion default + include_unknown override
- empty queries/scores edge cases
- length mismatch error
- bad axis error
- multi-axis projection helper
- determinism (same input → same output for buckets and means)
- serialisation round-trip
"""

from __future__ import annotations

import math

import pytest

from scripts.learning.rag.eval import buckets as B
from scripts.learning.rag.eval.dataset import GradedQuery, Qrel, Bucket, RankBudget


def _q(query_id: str, bucket: Bucket) -> GradedQuery:
    """Build a minimal GradedQuery with the given bucket."""
    return GradedQuery(
        query_id=query_id,
        prompt="p",
        mode="full",
        experience_level=None,
        learning_points=(),
        bucket=bucket,
        qrels=(Qrel("a.md", 3, "primary"),),
        forbidden_paths=(),
        rank_budget=RankBudget(1, 4),
        bucket_source="auto",
    )


def _close(a: float, b: float, tol: float = 1e-9) -> bool:
    return math.isclose(a, b, rel_tol=tol, abs_tol=tol)


# ---------------------------------------------------------------------------
# group_indexes_by_axis
# ---------------------------------------------------------------------------

def test_group_indexes_preserves_insertion_order():
    queries = [
        _q("q1", Bucket("spring", "beginner", "ko", "definition")),
        _q("q2", Bucket("database", "advanced", "en", "deep-dive")),
        _q("q3", Bucket("spring", "advanced", "ko", "comparison")),
    ]
    grouped = B.group_indexes_by_axis(queries, "category")
    # 'spring' should come first because q1 is at index 0
    assert list(grouped.keys()) == ["spring", "database"]
    assert grouped["spring"] == [0, 2]
    assert grouped["database"] == [1]


def test_group_indexes_rejects_unknown_axis():
    queries = [_q("q", Bucket("c", "d", "l", "i"))]
    with pytest.raises(ValueError, match="unknown bucket axis"):
        B.group_indexes_by_axis(queries, "bogus")


# ---------------------------------------------------------------------------
# macro vs micro mean — the central correctness story
# ---------------------------------------------------------------------------

def test_macro_equals_micro_when_buckets_are_balanced():
    # Two buckets, equal size, equal mean → macro == micro
    queries = [
        _q("a", Bucket("spring", "x", "x", "x")),
        _q("b", Bucket("spring", "x", "x", "x")),
        _q("c", Bucket("database", "x", "x", "x")),
        _q("d", Bucket("database", "x", "x", "x")),
    ]
    scores = [0.8, 0.6, 0.8, 0.6]  # both buckets mean to 0.7
    report = B.macro_average_by_axis(queries, scores, "category")
    assert _close(report.macro_mean, 0.7)
    assert _close(report.micro_mean, 0.7)


def test_macro_differs_from_micro_under_imbalance():
    # 'spring' has 4 queries averaging 0.9, 'network' has 1 query at 0.1
    # micro = (0.9*4 + 0.1)/5 = 0.74
    # macro = (0.9 + 0.1) / 2 = 0.50  ← much more pessimistic, fairer
    queries = [
        _q(f"s{i}", Bucket("spring", "x", "x", "x")) for i in range(4)
    ] + [
        _q("n1", Bucket("network", "x", "x", "x")),
    ]
    scores = [0.9, 0.9, 0.9, 0.9, 0.1]
    report = B.macro_average_by_axis(queries, scores, "category")
    assert _close(report.macro_mean, 0.5)
    assert _close(report.micro_mean, 0.74)


def test_per_bucket_count_recorded():
    queries = [
        _q("a", Bucket("spring", "x", "x", "x")),
        _q("b", Bucket("spring", "x", "x", "x")),
        _q("c", Bucket("database", "x", "x", "x")),
    ]
    report = B.macro_average_by_axis(queries, [1.0, 0.5, 0.0], "category")
    assert report.per_bucket_count == {"spring": 2, "database": 1}


# ---------------------------------------------------------------------------
# 'unknown' bucket handling
# ---------------------------------------------------------------------------

def test_unknown_bucket_excluded_from_macro_by_default():
    queries = [
        _q("a", Bucket("spring", "x", "x", "x")),
        _q("b", Bucket("unknown", "x", "x", "x")),
    ]
    scores = [1.0, 0.0]
    report = B.macro_average_by_axis(queries, scores, "category")
    # macro should only include 'spring' → 1.0
    assert _close(report.macro_mean, 1.0)
    assert "unknown" in report.excluded_buckets
    assert "spring" in report.included_buckets
    # unknown still gets a per-bucket mean reported for transparency
    assert report.per_bucket_mean["unknown"] == 0.0


def test_unknown_bucket_included_when_flag_set():
    queries = [
        _q("a", Bucket("spring", "x", "x", "x")),
        _q("b", Bucket("unknown", "x", "x", "x")),
    ]
    scores = [1.0, 0.0]
    report = B.macro_average_by_axis(
        queries, scores, "category", include_unknown=True
    )
    # macro = (1.0 + 0.0) / 2 = 0.5
    assert _close(report.macro_mean, 0.5)
    assert "unknown" in report.included_buckets


def test_macro_zero_when_only_unknown_bucket_and_excluded():
    # All queries fall into 'unknown' → no included buckets → macro=0.0
    queries = [_q("a", Bucket("unknown", "x", "x", "x"))]
    report = B.macro_average_by_axis(queries, [0.9], "category")
    assert report.macro_mean == 0.0
    assert _close(report.micro_mean, 0.9)
    assert report.included_buckets == ()


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

def test_empty_queries_yield_zero_means():
    report = B.macro_average_by_axis([], [], "category")
    assert report.macro_mean == 0.0
    assert report.micro_mean == 0.0
    assert report.per_bucket_mean == {}


def test_length_mismatch_raises():
    queries = [_q("a", Bucket("spring", "x", "x", "x"))]
    with pytest.raises(ValueError, match="length mismatch"):
        B.macro_average_by_axis(queries, [], "category")


def test_bad_axis_raises():
    queries = [_q("a", Bucket("spring", "x", "x", "x"))]
    with pytest.raises(ValueError, match="unknown bucket axis"):
        B.macro_average_by_axis(queries, [0.5], "bogus_axis")


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

def test_macro_average_is_deterministic():
    queries = [
        _q(f"q{i}", Bucket("spring" if i % 2 == 0 else "database", "x", "x", "x"))
        for i in range(10)
    ]
    scores = [i / 10.0 for i in range(10)]
    r1 = B.macro_average_by_axis(queries, scores, "category")
    r2 = B.macro_average_by_axis(queries, scores, "category")
    assert r1 == r2


# ---------------------------------------------------------------------------
# Multi-axis projection
# ---------------------------------------------------------------------------

def test_macro_report_all_axes_returns_one_per_axis():
    queries = [
        _q("a", Bucket("spring", "beginner", "ko", "definition")),
        _q("b", Bucket("spring", "advanced", "en", "deep-dive")),
    ]
    reports = B.macro_report_all_axes(queries, [0.9, 0.5])
    assert set(reports.keys()) == set(B.BUCKET_AXES)
    for axis, report in reports.items():
        assert report.axis == axis


# ---------------------------------------------------------------------------
# Serialisation
# ---------------------------------------------------------------------------

def test_to_serialisable_returns_json_friendly_dict():
    queries = [
        _q("a", Bucket("spring", "x", "x", "x")),
        _q("b", Bucket("database", "x", "x", "x")),
    ]
    report = B.macro_average_by_axis(queries, [0.8, 0.4], "category")
    blob = B.to_serialisable(report)

    # All values JSON-serialisable
    import json

    json.dumps(blob)  # would raise if not

    assert blob["axis"] == "category"
    assert blob["per_bucket_count"] == {"spring": 1, "database": 1}
    assert isinstance(blob["per_bucket_mean"], dict)
    assert isinstance(blob["macro_mean"], float)
    assert isinstance(blob["micro_mean"], float)
    assert isinstance(blob["included_buckets"], list)
    assert isinstance(blob["excluded_buckets"], list)
