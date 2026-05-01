"""R3 stage-level metrics."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class RerankerComparison:
    query_id: str
    language: str
    level: str
    category: str
    primary_paths: tuple[str, ...]
    before_paths: tuple[str, ...]
    after_paths: tuple[str, ...]


def _best_rank(paths: tuple[str, ...], targets: set[str]) -> int | None:
    for rank, path in enumerate(paths, start=1):
        if path in targets:
            return rank
    return None


def _empty_bucket() -> dict:
    return {"total": 0, "demoted": 0, "missing_after": 0, "rate": 0.0}


def _add(bucket: dict, *, demoted: bool, missing_after: bool) -> None:
    bucket["total"] += 1
    if demoted:
        bucket["demoted"] += 1
    if missing_after:
        bucket["missing_after"] += 1
    bucket["rate"] = bucket["demoted"] / bucket["total"] if bucket["total"] else 0.0


def reranker_demotion_summary(
    comparisons: Iterable[RerankerComparison],
) -> dict:
    """Summarize primary-document demotions by language/level/category."""

    out = {
        "overall": _empty_bucket(),
        "by_language": {},
        "by_level": {},
        "by_category": {},
        "demoted_query_ids": [],
    }
    for item in comparisons:
        targets = set(item.primary_paths)
        before_rank = _best_rank(item.before_paths, targets)
        after_rank = _best_rank(item.after_paths, targets)
        missing_after = after_rank is None
        demoted = (
            before_rank is not None
            and (after_rank is None or after_rank > before_rank)
        )
        _add(out["overall"], demoted=demoted, missing_after=missing_after)
        for key, value in (
            ("by_language", item.language),
            ("by_level", item.level),
            ("by_category", item.category),
        ):
            bucket = out[key].setdefault(value or "unknown", _empty_bucket())
            _add(bucket, demoted=demoted, missing_after=missing_after)
        if demoted:
            out["demoted_query_ids"].append(item.query_id)
    return out
