"""Bucket grouping + macro average over GradedQuery metric scores.

Why macro instead of micro:
The legacy golden fixture is dominated by a few topic families
(projection / failover / spring-beginner). A simple mean across all 338
queries is biased toward those over-represented buckets — a model that
is great on projection but mediocre everywhere else can look "better"
than a model that is balanced.

Macro averaging fixes this: per-bucket mean → mean of means. Each
bucket counts equally regardless of how many queries it has.

Plan §P1.1 step 3 — bucket macro average is the final-judgement signal;
micro is reported as a secondary check.
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass

from .dataset import GradedQuery, Bucket

# Names of the four bucket axes (matches Bucket dataclass fields)
BUCKET_AXES = ("category", "difficulty", "language", "intent")
"""Public list of valid axis names — used by callers and validators."""


def _bucket_value(bucket: Bucket, axis: str) -> str:
    """Pick one axis value off a Bucket. Raises ValueError on bad axis."""
    if axis not in BUCKET_AXES:
        raise ValueError(f"unknown bucket axis: {axis!r} (allowed: {BUCKET_AXES})")
    return getattr(bucket, axis)


# ---------------------------------------------------------------------------
# Grouping
# ---------------------------------------------------------------------------

def group_indexes_by_axis(
    queries: Sequence[GradedQuery],
    axis: str,
) -> dict[str, list[int]]:
    """Group ``queries`` by one bucket axis. Returns ``{bucket_value: [indexes]}``
    where indexes refer back into the original sequence — this lets callers
    project per-query metric arrays without re-iterating queries.

    Insertion order is preserved (first-seen bucket value first).
    """
    out: dict[str, list[int]] = {}
    for idx, q in enumerate(queries):
        key = _bucket_value(q.bucket, axis)
        out.setdefault(key, []).append(idx)
    return out


# ---------------------------------------------------------------------------
# Macro / micro means
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BucketReport:
    """One axis's per-bucket means + the macro average across buckets.

    Attributes:
        axis: bucket axis name
        per_bucket_mean: ordered dict-like ``{bucket_value: mean_score}``
        per_bucket_count: ``{bucket_value: query_count}``
        macro_mean: unweighted mean of per_bucket_mean values (skipping empty
            and 'unknown' buckets unless ``include_unknown`` was True)
        micro_mean: weighted mean across all query scores (sanity check)
        included_buckets: list of bucket values that contributed to macro_mean
        excluded_buckets: list excluded (empty, or 'unknown' when
            include_unknown=False)
    """

    axis: str
    per_bucket_mean: dict[str, float]
    per_bucket_count: dict[str, int]
    macro_mean: float
    micro_mean: float
    included_buckets: tuple[str, ...]
    excluded_buckets: tuple[str, ...]


def macro_average_by_axis(
    queries: Sequence[GradedQuery],
    scores: Sequence[float],
    axis: str,
    *,
    include_unknown: bool = False,
) -> BucketReport:
    """Group ``scores`` by one bucket axis and compute per-bucket + macro means.

    Args:
        queries: same length as ``scores`` — query at position i maps to
            scores[i].
        scores: per-query metric values (any float — graded nDCG, MRR, etc.)
        axis: one of BUCKET_AXES.
        include_unknown: when False (default), the 'unknown' bucket is
            reported per-bucket but excluded from the macro mean to avoid
            inflating with unclassifiable queries. When True, 'unknown' is
            treated like any other bucket.

    Raises:
        ValueError on length mismatch or bad axis.
    """
    if len(queries) != len(scores):
        raise ValueError(
            f"queries/scores length mismatch: {len(queries)} vs {len(scores)}"
        )
    if axis not in BUCKET_AXES:
        raise ValueError(f"unknown bucket axis: {axis!r}")

    grouped = group_indexes_by_axis(queries, axis)
    per_bucket_mean: dict[str, float] = {}
    per_bucket_count: dict[str, int] = {}
    included: list[str] = []
    excluded: list[str] = []

    for bucket_value, idxs in grouped.items():
        if not idxs:  # impossible given grouping, but defensive
            excluded.append(bucket_value)
            continue
        bucket_scores = [scores[i] for i in idxs]
        per_bucket_mean[bucket_value] = statistics.fmean(bucket_scores)
        per_bucket_count[bucket_value] = len(bucket_scores)

        if bucket_value == "unknown" and not include_unknown:
            excluded.append(bucket_value)
        else:
            included.append(bucket_value)

    macro_mean = (
        statistics.fmean(per_bucket_mean[b] for b in included)
        if included
        else 0.0
    )
    micro_mean = statistics.fmean(scores) if scores else 0.0

    return BucketReport(
        axis=axis,
        per_bucket_mean=per_bucket_mean,
        per_bucket_count=per_bucket_count,
        macro_mean=macro_mean,
        micro_mean=micro_mean,
        included_buckets=tuple(included),
        excluded_buckets=tuple(excluded),
    )


# ---------------------------------------------------------------------------
# Multi-axis projection (helper for runner reports)
# ---------------------------------------------------------------------------

def macro_report_all_axes(
    queries: Sequence[GradedQuery],
    scores: Sequence[float],
    *,
    include_unknown: bool = False,
) -> dict[str, BucketReport]:
    """Compute one BucketReport per axis. Convenience for run manifests."""
    return {
        axis: macro_average_by_axis(
            queries, scores, axis, include_unknown=include_unknown
        )
        for axis in BUCKET_AXES
    }


def to_serialisable(report: BucketReport) -> dict[str, object]:
    """Render a BucketReport into JSON-friendly primitives."""
    return {
        "axis": report.axis,
        "per_bucket_mean": dict(report.per_bucket_mean),
        "per_bucket_count": dict(report.per_bucket_count),
        "macro_mean": report.macro_mean,
        "micro_mean": report.micro_mean,
        "included_buckets": list(report.included_buckets),
        "excluded_buckets": list(report.excluded_buckets),
    }
