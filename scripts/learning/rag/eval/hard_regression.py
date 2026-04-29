"""Hard regression gate — the merge-blocking primary/forbidden checks.

Plan §P1.1 step 2 — two contracts that PR-1 promises NEVER to break:

1. **Primary in budget**: every fixture's primary path (grade 3) must
   appear within ``rank_budget.primary_max_rank``. If we drop a model
   that pushes a primary out of its budget, the regression test fails
   the PR.

2. **No forbidden in top-k**: any path listed under
   ``forbidden_paths`` must NOT appear in the top-k window. Forbidden
   paths are wrong-but-tempting siblings (e.g. an advanced doc when
   the prompt asks for a beginner primer).

Soft / advisory check (NOT a merge gate, plan §P1.1 step 2 second
half): primary should appear before any companion path. Reported as a
warning so callers can surface drift without failing the PR — primary
ordering inside the rank budget already guards the correctness path.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from .dataset import GradedQuery

# Default top-k slice for forbidden checks when fixture doesn't specify one.
DEFAULT_FORBIDDEN_WINDOW = 5


@dataclass(frozen=True)
class RegressionResult:
    """Outcome of one fixture query against one retrieval ranking."""

    query_id: str
    passed: bool
    violations: tuple[str, ...]
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class RegressionSummary:
    """Aggregate over a list of RegressionResult — used by the runner
    to gate PRs and by the CI workflow to set exit codes."""

    total: int
    passed_count: int
    failed_count: int
    violations_by_kind: dict[str, int]
    warnings_by_kind: dict[str, int] = field(default_factory=dict)
    failed_query_ids: tuple[str, ...] = ()

    @property
    def all_passed(self) -> bool:
        return self.failed_count == 0


# ---------------------------------------------------------------------------
# Per-query check
# ---------------------------------------------------------------------------

def check_query(
    query: GradedQuery,
    ranked_paths: Sequence[str],
    *,
    forbidden_window: int = DEFAULT_FORBIDDEN_WINDOW,
) -> RegressionResult:
    """Run hard + soft checks for one query against its retrieval ranking.

    Hard (gate, contributes to RegressionResult.passed=False):
    - Each primary (grade 3) path must appear within the
      ``primary_max_rank`` budget. ``primary_not_present`` (rank
      missing entirely) is also a hard fail.
    - No path from ``forbidden_paths`` may appear in
      ``ranked_paths[:forbidden_window]``.

    Soft (warning, never fails the gate):
    - Primary should be ranked before any companion (grade 1) path.
      If a companion outranks the primary, surface as a warning.

    Args:
        query: the fixture entry (carries qrels + rank_budget +
            forbidden_paths).
        ranked_paths: retriever output for ``query.prompt``, rank 1
            first.
        forbidden_window: how many top-k slots to check for
            forbidden_paths. Defaults to DEFAULT_FORBIDDEN_WINDOW.

    Returns:
        RegressionResult with ``passed=False`` if any HARD check
        fails. Soft warnings appear in ``warnings`` but do not flip
        ``passed``.
    """
    violations: list[str] = []
    warnings: list[str] = []

    primary_paths = query.primary_paths()
    companion_paths = query.companion_paths()
    forbidden = set(query.forbidden_paths)

    # rank lookup map: path → 1-indexed rank, first occurrence wins
    rank_of: dict[str, int] = {}
    for i, path in enumerate(ranked_paths, start=1):
        if path not in rank_of:
            rank_of[path] = i

    # ── Hard gate 1: primary in budget ────────────────────────────────
    budget = query.rank_budget.primary_max_rank
    for primary in primary_paths:
        actual = rank_of.get(primary)
        if actual is None:
            violations.append(
                f"primary_not_present: {primary!r} missing from ranking "
                f"(budget={budget})"
            )
        elif actual > budget:
            violations.append(
                f"primary_over_budget: {primary!r} at rank {actual}, "
                f"budget={budget}"
            )

    # ── Hard gate 2: forbidden in top-k ───────────────────────────────
    if forbidden:
        topk = ranked_paths[:forbidden_window]
        for i, path in enumerate(topk, start=1):
            if path in forbidden:
                violations.append(
                    f"forbidden_in_topk: {path!r} at rank {i} "
                    f"(window={forbidden_window})"
                )

    # ── Soft warning: primary before companion ────────────────────────
    if companion_paths:
        first_primary_rank = min(
            (rank_of[p] for p in primary_paths if p in rank_of),
            default=None,
        )
        if first_primary_rank is not None:
            for companion in companion_paths:
                comp_rank = rank_of.get(companion)
                if comp_rank is not None and comp_rank < first_primary_rank:
                    warnings.append(
                        f"companion_before_primary: companion {companion!r} "
                        f"at rank {comp_rank} ahead of primary at rank "
                        f"{first_primary_rank}"
                    )

    return RegressionResult(
        query_id=query.query_id,
        passed=not violations,
        violations=tuple(violations),
        warnings=tuple(warnings),
    )


# ---------------------------------------------------------------------------
# Aggregate
# ---------------------------------------------------------------------------

def summarise(results: Sequence[RegressionResult]) -> RegressionSummary:
    """Aggregate per-query results into a RegressionSummary.

    Violations are bucketed by kind (the prefix before ":") so the
    summary tells you whether failures concentrate around primary
    budget or forbidden surfaces.
    """
    total = len(results)
    passed_count = sum(1 for r in results if r.passed)
    failed_count = total - passed_count

    by_kind: dict[str, int] = {}
    warn_kind: dict[str, int] = {}
    failed_ids: list[str] = []

    for r in results:
        if not r.passed:
            failed_ids.append(r.query_id)
        for v in r.violations:
            kind = v.split(":", 1)[0]
            by_kind[kind] = by_kind.get(kind, 0) + 1
        for w in r.warnings:
            kind = w.split(":", 1)[0]
            warn_kind[kind] = warn_kind.get(kind, 0) + 1

    return RegressionSummary(
        total=total,
        passed_count=passed_count,
        failed_count=failed_count,
        violations_by_kind=by_kind,
        warnings_by_kind=warn_kind,
        failed_query_ids=tuple(failed_ids),
    )
