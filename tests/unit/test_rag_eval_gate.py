"""Unit tests for scripts.learning.rag.eval.gate.

Coverage targets:
- All six gate checks individually fail and pass
- Multiple failures reported together (not short-circuited)
- Bucket regression respects min_bucket_size noise floor
- Bucket regression treats missing bucket as full regression
- Pareto prefers smaller model when within tolerance
- Pareto prefers larger model when gap >= force_larger_above
- Pareto raw quality wins in the middle band
- Pareto deterministic on exact ties
- Single-candidate input returns same list
"""

from __future__ import annotations

import pytest

from scripts.learning.rag.eval import gate as G


def _baseline(
    *, primary=0.97, by_cat=None, counts=None, forbidden=0.0, hard=13
) -> G.BaselineScore:
    return G.BaselineScore(
        primary_ndcg_macro=primary,
        primary_ndcg_by_category=by_cat or {"spring": 0.98, "database": 0.89},
        primary_ndcg_category_counts=counts or {"spring": 72, "database": 48},
        forbidden_rate_overall=forbidden,
        hard_regression_failures=hard,
    )


def _candidate(
    *,
    cid="cand",
    primary=1.00,
    by_cat=None,
    counts=None,
    forbidden=0.0,
    hard=13,
    p95=150.0,
    rss=2000.0,
    size=1200.0,
) -> G.CandidateScore:
    return G.CandidateScore(
        candidate_id=cid,
        primary_ndcg_macro=primary,
        primary_ndcg_by_category=by_cat or {"spring": 0.99, "database": 0.95},
        primary_ndcg_category_counts=counts or {"spring": 72, "database": 48},
        forbidden_rate_overall=forbidden,
        hard_regression_failures=hard,
        warm_p95_ms=p95,
        rss_mb=rss,
        model_size_mb=size,
    )


# ---------------------------------------------------------------------------
# Individual gate failures
# ---------------------------------------------------------------------------

def test_passes_when_all_gates_satisfied():
    r = G.evaluate_candidate(_candidate(), _baseline())
    assert r.passed is True
    assert r.failed_checks == ()
    assert "primary_uplift" in r.passed_checks
    assert "hard_regression" in r.passed_checks


def test_fails_on_insufficient_primary_uplift():
    # +1% uplift, threshold +3%
    r = G.evaluate_candidate(
        _candidate(primary=0.98), _baseline(primary=0.97)
    )
    assert r.passed is False
    assert any("primary_uplift" in c for c in r.failed_checks)


def test_fails_on_new_hard_regression():
    r = G.evaluate_candidate(
        _candidate(hard=20), _baseline(hard=13)
    )
    assert r.passed is False
    assert any("hard_regression" in c for c in r.failed_checks)


def test_fails_on_increased_forbidden_rate():
    r = G.evaluate_candidate(
        _candidate(forbidden=0.02), _baseline(forbidden=0.0)
    )
    assert r.passed is False
    assert any("forbidden_rate" in c for c in r.failed_checks)


def test_fails_on_p95_over_budget():
    r = G.evaluate_candidate(
        _candidate(p95=300.0), _baseline()
    )
    assert r.passed is False
    assert any("warm_p95" in c for c in r.failed_checks)


def test_fails_on_rss_over_budget():
    r = G.evaluate_candidate(
        _candidate(rss=8000.0), _baseline()
    )
    assert r.passed is False
    assert any("rss" in c for c in r.failed_checks)


# ---------------------------------------------------------------------------
# Bucket regression
# ---------------------------------------------------------------------------

def test_fails_on_major_bucket_regression():
    # database drops 10% (>5% threshold)
    r = G.evaluate_candidate(
        _candidate(by_cat={"spring": 0.99, "database": 0.79}),
        _baseline(by_cat={"spring": 0.98, "database": 0.89}),
    )
    assert r.passed is False
    assert any("bucket_regression" in c for c in r.failed_checks)


def test_skips_regression_check_for_tiny_buckets():
    # 'rare' bucket has only 2 queries → below noise floor → skip
    baseline = _baseline(
        by_cat={"spring": 0.98, "rare": 0.99},
        counts={"spring": 72, "rare": 2},
    )
    candidate = _candidate(
        by_cat={"spring": 0.99, "rare": 0.10},  # 'rare' tanked
        counts={"spring": 72, "rare": 2},
    )
    r = G.evaluate_candidate(candidate, baseline)
    # 'rare' regression is ignored (n=2 < 5); other gates pass → overall pass
    assert r.passed is True
    assert "bucket_regression" in r.passed_checks


def test_treats_missing_bucket_as_full_regression():
    # Candidate covers spring but not database
    baseline = _baseline(
        by_cat={"spring": 0.98, "database": 0.89},
        counts={"spring": 72, "database": 48},
    )
    candidate = _candidate(
        by_cat={"spring": 0.99},  # database missing
        counts={"spring": 72},
    )
    r = G.evaluate_candidate(candidate, baseline)
    assert r.passed is False
    assert any("database" in c for c in r.failed_checks)


# ---------------------------------------------------------------------------
# Multiple failures reported together
# ---------------------------------------------------------------------------

def test_multiple_failures_all_reported():
    r = G.evaluate_candidate(
        _candidate(p95=400.0, rss=8000.0, primary=0.97),
        _baseline(primary=0.97),
    )
    assert r.passed is False
    # Three independent gates fail
    kinds = {c.split(":", 1)[0] for c in r.failed_checks}
    assert "primary_uplift" in kinds
    assert "warm_p95" in kinds
    assert "rss" in kinds


def test_diagnostics_carry_numeric_signals():
    r = G.evaluate_candidate(_candidate(), _baseline())
    diag = r.diagnostics
    assert "primary_uplift" in diag
    assert "warm_p95_ms" in diag
    assert "rss_mb" in diag
    assert "new_hard_regression_failures" in diag


# ---------------------------------------------------------------------------
# Pareto selection
# ---------------------------------------------------------------------------

def test_pareto_single_candidate_returns_same():
    only = [_candidate(cid="solo")]
    assert G.pareto_select(only) == only


def test_pareto_prefers_smaller_when_within_tolerance():
    big = _candidate(cid="big", primary=0.99, size=2300.0)
    small = _candidate(cid="small", primary=0.985, size=300.0)  # 0.5% gap
    sorted_ = G.pareto_select([big, small])
    assert sorted_[0].candidate_id == "small"


def test_pareto_prefers_larger_when_gap_exceeds_force():
    big = _candidate(cid="big", primary=0.99, size=2300.0)
    small = _candidate(cid="small", primary=0.94, size=300.0)  # 5% gap
    sorted_ = G.pareto_select([big, small])
    assert sorted_[0].candidate_id == "big"


def test_pareto_quality_wins_in_middle_band():
    # 2.5% gap — between tolerance (2%) and force_larger (3%)
    a = _candidate(cid="a", primary=0.99, size=2300.0)
    b = _candidate(cid="b", primary=0.965, size=300.0)
    sorted_ = G.pareto_select([a, b])
    assert sorted_[0].candidate_id == "a"


def test_pareto_uses_p95_as_secondary_within_tolerance():
    same_size_a = _candidate(
        cid="a", primary=0.985, size=300.0, p95=150.0
    )
    same_size_b = _candidate(
        cid="b", primary=0.985, size=300.0, p95=80.0  # faster
    )
    sorted_ = G.pareto_select([same_size_a, same_size_b])
    assert sorted_[0].candidate_id == "b"


def test_pareto_deterministic_on_exact_ties():
    a = _candidate(cid="a", primary=0.98, size=300.0, p95=100.0)
    b = _candidate(cid="b", primary=0.98, size=300.0, p95=100.0)
    # Either ordering is acceptable as long as it's stable
    s1 = G.pareto_select([a, b])
    s2 = G.pareto_select([b, a])
    assert [c.candidate_id for c in s1] == [c.candidate_id for c in s2]


# ---------------------------------------------------------------------------
# Threshold overrides
# ---------------------------------------------------------------------------

def test_thresholds_can_be_overridden():
    # Force +5% uplift requirement → +3% candidate now fails
    strict = G.GateThresholds(min_primary_uplift=0.05)
    r = G.evaluate_candidate(
        _candidate(primary=1.00), _baseline(primary=0.97), strict
    )
    assert r.passed is False
    assert any("primary_uplift" in c for c in r.failed_checks)
