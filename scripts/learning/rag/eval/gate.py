"""Automated acceptance gate + Pareto preference rule.

Plan §P2.1 — replaces "ask the learner" with explicit, testable
thresholds so candidate selection is reproducible across runs and
machines. Reuses the same shape for P3.1 (reranker A/B) by accepting
configurable thresholds.

Two layers:

1. ``GateThresholds.evaluate(candidate, baseline)`` — boolean gate per
   plan §P2.1 rules:
   - hard regression count must not exceed baseline (0 new failures)
   - primary_nDCG@k macro must improve by ``min_primary_uplift`` over
     baseline (default +3%)
   - no major bucket may drop more than ``max_bucket_regression``
     (default 5%)
   - forbidden_rate must not increase
   - warm P95 latency must be ≤ ``max_p95_warm_ms`` (default 200)
   - RSS must be ≤ ``max_rss_mb`` (default 6144 = 6GB)

2. ``pareto_select(candidates, ...)`` — final ranking among gate
   passers. When two candidates' primary_nDCG_macro differ by less
   than ``pareto_tolerance`` (default 0.02 = 2%), prefer the smaller
   / faster model; if the difference exceeds 3%, prefer the larger
   one. Plan §P2.1 step 7.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any


# ---------------------------------------------------------------------------
# Defaults (plan §P2.1 + §P3.1 thresholds)
# ---------------------------------------------------------------------------

DEFAULT_MIN_PRIMARY_UPLIFT = 0.03
"""+3% on primary_nDCG@k macro vs baseline (plan §P2.1)."""

DEFAULT_MAX_BUCKET_REGRESSION = 0.05
"""No major bucket may regress more than -5% vs baseline (plan §P2.1)."""

DEFAULT_MAX_P95_WARM_MS = 200.0
"""Warm-query P95 latency budget on M4 MPS (plan §P2.1)."""

DEFAULT_MAX_RSS_MB = 6144.0
"""Total memory budget = 6 GB; safe margin on a 16 GB M4 Air after
account for OS / IDE / browser baseline."""

DEFAULT_PARETO_TOLERANCE = 0.02
"""Primary_nDCG difference within this tolerance triggers Pareto
preference for the smaller candidate (plan §P2.1 step 7)."""

DEFAULT_PARETO_FORCE_LARGER_ABOVE = 0.03
"""Primary_nDCG difference at or above this overrides Pareto: prefer
the larger candidate (the gain justifies the cost)."""

MIN_BUCKET_SIZE_FOR_REGRESSION = 5
"""A bucket with fewer queries than this is treated as too-noisy for
regression checks. Otherwise a single query in a tiny bucket can flip
its mean by 100% and falsely tank the gate."""


# ---------------------------------------------------------------------------
# Inputs / outputs
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CandidateScore:
    """Headline numbers for one candidate, fed into the gate.

    All percent-style fields are 0..1 floats (NOT 0..100). RSS is
    in MB. P95 latency is ms. Bucket means are
    {bucket_value: macro_mean} per category-axis (the headline axis
    plan §P2.1 macro reports use).
    """

    candidate_id: str
    primary_ndcg_macro: float
    primary_ndcg_by_category: dict[str, float]
    primary_ndcg_category_counts: dict[str, int]
    forbidden_rate_overall: float
    hard_regression_failures: int
    warm_p95_ms: float
    rss_mb: float
    model_size_mb: float = 0.0


@dataclass(frozen=True)
class BaselineScore:
    """Same shape as CandidateScore minus the model_size field
    (baseline model size isn't a selection input)."""

    primary_ndcg_macro: float
    primary_ndcg_by_category: dict[str, float]
    primary_ndcg_category_counts: dict[str, int]
    forbidden_rate_overall: float
    hard_regression_failures: int


@dataclass(frozen=True)
class GateThresholds:
    """All thresholds in one place — override per phase if needed."""

    min_primary_uplift: float = DEFAULT_MIN_PRIMARY_UPLIFT
    max_bucket_regression: float = DEFAULT_MAX_BUCKET_REGRESSION
    max_p95_warm_ms: float = DEFAULT_MAX_P95_WARM_MS
    max_rss_mb: float = DEFAULT_MAX_RSS_MB
    pareto_tolerance: float = DEFAULT_PARETO_TOLERANCE
    pareto_force_larger_above: float = DEFAULT_PARETO_FORCE_LARGER_ABOVE
    min_bucket_size_for_regression: int = MIN_BUCKET_SIZE_FOR_REGRESSION


@dataclass(frozen=True)
class GateResult:
    """Outcome of running one candidate through the gate.

    ``passed`` is True iff every reason in ``failed_checks`` is empty.
    ``passed_checks`` records which gates were OK so reports can show
    the full picture.
    """

    candidate_id: str
    passed: bool
    failed_checks: tuple[str, ...]
    passed_checks: tuple[str, ...]
    diagnostics: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Gate evaluation
# ---------------------------------------------------------------------------

def evaluate_candidate(
    candidate: CandidateScore,
    baseline: BaselineScore,
    thresholds: GateThresholds = GateThresholds(),
) -> GateResult:
    """Run all six gates for one candidate. Returns a GateResult.

    Failed checks are NOT short-circuited — every gate is evaluated so
    the operator sees the full set of issues (parallel to
    assert_index_compat reporting all mismatches at once).
    """
    failed: list[str] = []
    passed: list[str] = []
    diag: dict[str, Any] = {}

    # 1. Hard regression — no NEW failures vs baseline
    new_failures = candidate.hard_regression_failures - baseline.hard_regression_failures
    diag["new_hard_regression_failures"] = new_failures
    if new_failures > 0:
        failed.append(
            f"hard_regression: {new_failures} new failures over baseline "
            f"({candidate.hard_regression_failures} vs {baseline.hard_regression_failures})"
        )
    else:
        passed.append("hard_regression")

    # 2. primary_nDCG macro uplift
    uplift = candidate.primary_ndcg_macro - baseline.primary_ndcg_macro
    diag["primary_uplift"] = uplift
    if uplift < thresholds.min_primary_uplift:
        failed.append(
            f"primary_uplift: {uplift:+.4f} < required "
            f"+{thresholds.min_primary_uplift:.4f}"
        )
    else:
        passed.append("primary_uplift")

    # 3. No major bucket regression
    bucket_regressions: list[tuple[str, float]] = []
    for bucket_value, baseline_mean in baseline.primary_ndcg_by_category.items():
        n = baseline.primary_ndcg_category_counts.get(bucket_value, 0)
        if n < thresholds.min_bucket_size_for_regression:
            continue  # noise floor — skip
        cand_mean = candidate.primary_ndcg_by_category.get(bucket_value)
        if cand_mean is None:
            # Candidate didn't cover this bucket → treat as full regression
            bucket_regressions.append((bucket_value, -baseline_mean))
            continue
        delta = cand_mean - baseline_mean
        if delta < -thresholds.max_bucket_regression:
            bucket_regressions.append((bucket_value, delta))
    diag["bucket_regressions"] = bucket_regressions
    if bucket_regressions:
        formatted = ", ".join(
            f"{name}({delta:+.4f})" for name, delta in bucket_regressions
        )
        failed.append(
            f"bucket_regression: {len(bucket_regressions)} categories "
            f"dropped > {thresholds.max_bucket_regression}: {formatted}"
        )
    else:
        passed.append("bucket_regression")

    # 4. forbidden_rate must not increase
    forbidden_delta = candidate.forbidden_rate_overall - baseline.forbidden_rate_overall
    diag["forbidden_rate_delta"] = forbidden_delta
    if forbidden_delta > 0:
        failed.append(
            f"forbidden_rate: increased by {forbidden_delta:+.4f}"
        )
    else:
        passed.append("forbidden_rate")

    # 5. P95 latency
    diag["warm_p95_ms"] = candidate.warm_p95_ms
    if candidate.warm_p95_ms > thresholds.max_p95_warm_ms:
        failed.append(
            f"warm_p95: {candidate.warm_p95_ms:.1f}ms > budget "
            f"{thresholds.max_p95_warm_ms:.1f}ms"
        )
    else:
        passed.append("warm_p95")

    # 6. RSS
    diag["rss_mb"] = candidate.rss_mb
    if candidate.rss_mb > thresholds.max_rss_mb:
        failed.append(
            f"rss: {candidate.rss_mb:.0f}MB > budget {thresholds.max_rss_mb:.0f}MB"
        )
    else:
        passed.append("rss")

    return GateResult(
        candidate_id=candidate.candidate_id,
        passed=not failed,
        failed_checks=tuple(failed),
        passed_checks=tuple(passed),
        diagnostics=diag,
    )


# ---------------------------------------------------------------------------
# Pareto selection
# ---------------------------------------------------------------------------

def pareto_select(
    candidates: Sequence[CandidateScore],
    thresholds: GateThresholds = GateThresholds(),
) -> list[CandidateScore]:
    """Sort gate-passing candidates by Pareto preference.

    Returns the input list re-ordered: best (= preferred) first.

    Rule (plan §P2.1 step 7):
    - When two candidates' primary_nDCG_macro differ by less than
      ``pareto_tolerance``, prefer the smaller / faster one
      (model_size_mb breaks ties; warm_p95_ms breaks further).
    - When the difference is at or above ``pareto_force_larger_above``,
      prefer the larger model (the gain justifies the cost).
    - Otherwise (between tolerance and force_larger), the larger
      uplift wins on raw primary_nDCG_macro.

    Determinism contract: candidate_id is the final tiebreaker so the
    output is reproducible across runs.
    """
    sorted_ = list(candidates)
    if len(sorted_) <= 1:
        return sorted_

    def _comparator(a: CandidateScore, b: CandidateScore) -> int:
        diff = a.primary_ndcg_macro - b.primary_ndcg_macro
        abs_diff = abs(diff)

        if abs_diff < thresholds.pareto_tolerance:
            # Within tolerance — prefer smaller/faster
            if a.model_size_mb != b.model_size_mb:
                return -1 if a.model_size_mb < b.model_size_mb else 1
            if a.warm_p95_ms != b.warm_p95_ms:
                return -1 if a.warm_p95_ms < b.warm_p95_ms else 1
            # Tie → use raw primary score
            if diff != 0:
                return -1 if diff > 0 else 1
            return -1 if a.candidate_id < b.candidate_id else 1

        if abs_diff >= thresholds.pareto_force_larger_above:
            # Big gap — quality wins regardless of size
            return -1 if diff > 0 else 1

        # Middle band — straight quality preference
        return -1 if diff > 0 else 1

    import functools

    return sorted(sorted_, key=functools.cmp_to_key(_comparator))
