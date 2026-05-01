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


@dataclass(frozen=True)
class RetrievalEvaluationQuery:
    """One qrel-backed retrieval result for stage-level gate metrics."""

    query_id: str
    language: str
    level: str
    category: str
    primary_paths: tuple[str, ...]
    acceptable_paths: tuple[str, ...]
    forbidden_paths: tuple[str, ...]
    candidate_paths: tuple[str, ...]
    final_paths: tuple[str, ...]


def _best_rank(paths: tuple[str, ...], targets: set[str]) -> int | None:
    for rank, path in enumerate(paths, start=1):
        if path in targets:
            return rank
    return None


def _empty_bucket() -> dict:
    return {
        "total": 0,
        "demoted": 0,
        "missing_after": 0,
        "lost_top5": 0,
        "lost_top20": 0,
        "rate": 0.0,
        "lost_top5_rate": 0.0,
        "lost_top20_rate": 0.0,
    }


def _add(
    bucket: dict,
    *,
    demoted: bool,
    missing_after: bool,
    lost_top5: bool,
    lost_top20: bool,
) -> None:
    bucket["total"] += 1
    if demoted:
        bucket["demoted"] += 1
    if missing_after:
        bucket["missing_after"] += 1
    if lost_top5:
        bucket["lost_top5"] += 1
    if lost_top20:
        bucket["lost_top20"] += 1
    bucket["rate"] = bucket["demoted"] / bucket["total"] if bucket["total"] else 0.0
    bucket["lost_top5_rate"] = (
        bucket["lost_top5"] / bucket["total"] if bucket["total"] else 0.0
    )
    bucket["lost_top20_rate"] = (
        bucket["lost_top20"] / bucket["total"] if bucket["total"] else 0.0
    )


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
        "lost_top5_query_ids": [],
        "lost_top20_query_ids": [],
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
        lost_top5 = (
            before_rank is not None
            and before_rank <= 5
            and (after_rank is None or after_rank > 5)
        )
        lost_top20 = (
            before_rank is not None
            and before_rank <= 20
            and (after_rank is None or after_rank > 20)
        )
        _add(
            out["overall"],
            demoted=demoted,
            missing_after=missing_after,
            lost_top5=lost_top5,
            lost_top20=lost_top20,
        )
        for key, value in (
            ("by_language", item.language),
            ("by_level", item.level),
            ("by_category", item.category),
        ):
            bucket = out[key].setdefault(value or "unknown", _empty_bucket())
            _add(
                bucket,
                demoted=demoted,
                missing_after=missing_after,
                lost_top5=lost_top5,
                lost_top20=lost_top20,
            )
        if demoted:
            out["demoted_query_ids"].append(item.query_id)
        if lost_top5:
            out["lost_top5_query_ids"].append(item.query_id)
        if lost_top20:
            out["lost_top20_query_ids"].append(item.query_id)
    return out


def _hit(paths: tuple[str, ...], targets: set[str], window: int) -> bool:
    if window <= 0:
        return False
    return any(path in targets for path in paths[:window])


def _rate(count: int, total: int) -> float:
    return count / total if total else 0.0


def _retrieval_empty_bucket(windows: tuple[int, ...], forbidden_window: int) -> dict:
    return {
        "total": 0,
        "candidate_primary_hits": {str(window): 0 for window in windows},
        "candidate_relevant_hits": {str(window): 0 for window in windows},
        "final_primary_hits": {str(window): 0 for window in windows},
        "final_relevant_hits": {str(window): 0 for window in windows},
        "forbidden_hits": 0,
        "forbidden_window": forbidden_window,
    }


def _add_retrieval_item(
    bucket: dict,
    item: RetrievalEvaluationQuery,
    *,
    windows: tuple[int, ...],
    forbidden_window: int,
) -> None:
    primary = set(item.primary_paths)
    relevant = primary | set(item.acceptable_paths)
    forbidden = set(item.forbidden_paths)
    bucket["total"] += 1
    for window in windows:
        key = str(window)
        if _hit(item.candidate_paths, primary, window):
            bucket["candidate_primary_hits"][key] += 1
        if _hit(item.candidate_paths, relevant, window):
            bucket["candidate_relevant_hits"][key] += 1
        if _hit(item.final_paths, primary, window):
            bucket["final_primary_hits"][key] += 1
        if _hit(item.final_paths, relevant, window):
            bucket["final_relevant_hits"][key] += 1
    if forbidden and _hit(item.final_paths, forbidden, forbidden_window):
        bucket["forbidden_hits"] += 1


def _finalize_retrieval_bucket(bucket: dict) -> dict:
    total = int(bucket["total"])
    out = {
        "total": total,
        "candidate_recall_primary": {},
        "candidate_recall_relevant": {},
        "final_hit_primary": {},
        "final_hit_relevant": {},
        "forbidden_hits": bucket["forbidden_hits"],
        "forbidden_window": bucket["forbidden_window"],
        "forbidden_rate": _rate(bucket["forbidden_hits"], total),
    }
    for key, count in bucket["candidate_primary_hits"].items():
        out["candidate_recall_primary"][key] = _rate(count, total)
    for key, count in bucket["candidate_relevant_hits"].items():
        out["candidate_recall_relevant"][key] = _rate(count, total)
    for key, count in bucket["final_primary_hits"].items():
        out["final_hit_primary"][key] = _rate(count, total)
    for key, count in bucket["final_relevant_hits"].items():
        out["final_hit_relevant"][key] = _rate(count, total)
    return out


def retrieval_summary(
    queries: Iterable[RetrievalEvaluationQuery],
    *,
    windows: Iterable[int] = (20, 50, 100),
    forbidden_window: int = 5,
) -> dict:
    """Summarize qrel-backed candidate/final recall and forbidden leakage."""

    normalized_windows = tuple(sorted({int(window) for window in windows if window > 0}))
    overall = _retrieval_empty_bucket(normalized_windows, forbidden_window)
    by_language: dict[str, dict] = {}
    by_level: dict[str, dict] = {}
    by_category: dict[str, dict] = {}
    missing_candidate_primary: list[str] = []
    missing_final_primary: list[str] = []
    forbidden_query_ids: list[str] = []

    for item in queries:
        _add_retrieval_item(
            overall,
            item,
            windows=normalized_windows,
            forbidden_window=forbidden_window,
        )
        for group, value in (
            (by_language, item.language),
            (by_level, item.level),
            (by_category, item.category),
        ):
            bucket = group.setdefault(
                value or "unknown",
                _retrieval_empty_bucket(normalized_windows, forbidden_window),
            )
            _add_retrieval_item(
                bucket,
                item,
                windows=normalized_windows,
                forbidden_window=forbidden_window,
            )

        primary = set(item.primary_paths)
        max_window = max(normalized_windows, default=0)
        if primary and not _hit(item.candidate_paths, primary, max_window):
            missing_candidate_primary.append(item.query_id)
        if primary and not _hit(item.final_paths, primary, max_window):
            missing_final_primary.append(item.query_id)
        if item.forbidden_paths and _hit(
            item.final_paths,
            set(item.forbidden_paths),
            forbidden_window,
        ):
            forbidden_query_ids.append(item.query_id)

    return {
        "windows": list(normalized_windows),
        "overall": _finalize_retrieval_bucket(overall),
        "by_language": {
            key: _finalize_retrieval_bucket(value)
            for key, value in sorted(by_language.items())
        },
        "by_level": {
            key: _finalize_retrieval_bucket(value)
            for key, value in sorted(by_level.items())
        },
        "by_category": {
            key: _finalize_retrieval_bucket(value)
            for key, value in sorted(by_category.items())
        },
        "missing_candidate_primary_query_ids": missing_candidate_primary,
        "missing_final_primary_query_ids": missing_final_primary,
        "forbidden_query_ids": forbidden_query_ids,
    }
