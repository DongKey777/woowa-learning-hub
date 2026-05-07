"""Cohort-aware R3 retrieval evaluation harness (Phase 6 measurement gate).

Given a CohortQrelSuite and a search callable, this module runs every
query, classifies its outcome, and emits:

* Per-query result records (for diff / triage)
* Per-cohort metric summaries (recall@5, recall@10, MRR, forbidden hit
  rate, refusal correctness for corpus_gap_probe)
* Failure taxonomy classification — uses the failure_focus tags from the
  qrel record + the trace metadata to assign a primary failure_class
  per missing-primary query

The harness is *evaluation-only* — it never mutates state. It accepts a
``search_fn`` so tests / smoke runs can inject a fake search and the
production path can wire ``scripts.learning.rag.r3.search.search``
directly.

CLI: ``python -m scripts.learning.rag.r3.eval.cohort_eval --qrels ...
--out ... [--index-root ...] [--catalog-root ...]``
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Sequence

from .cohort_qrels import CohortQrelSuite, CohortQuery, VALID_COHORTS, load_cohort_qrels


SearchFn = Callable[..., list[dict]]


def _is_refusal_clean_outcome(actual_outcome: str) -> bool:
    """True when a corpus-gap query ended in an acceptable refusal path."""
    return actual_outcome in {"refusal_clean", "tier_downgraded"}


def _qrel_sha256(qrel_path: str) -> str | None:
    if not qrel_path:
        return None
    path = Path(qrel_path)
    if not path.exists() or not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class CohortQueryResult:
    query_id: str
    cohort_tag: str
    language: str
    level: str
    primary_paths: tuple[str, ...]
    acceptable_paths: tuple[str, ...]
    forbidden_paths: tuple[str, ...]
    final_paths: tuple[str, ...]
    primary_rank: int | None
    acceptable_rank: int | None
    forbidden_hit_rank: int | None
    expected_outcome: str        # "primary_in_top_k" | "refusal_clean"
    actual_outcome: str          # "primary_hit" | "acceptable_hit" |
                                 # "forbidden_hit" | "miss" | "refusal_clean"
    pass_status: bool
    failure_class: str | None
    failure_focus: tuple[str, ...]
    debug: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        blob = asdict(self)
        blob["primary_paths"] = list(self.primary_paths)
        blob["acceptable_paths"] = list(self.acceptable_paths)
        blob["forbidden_paths"] = list(self.forbidden_paths)
        blob["final_paths"] = list(self.final_paths)
        blob["failure_focus"] = list(self.failure_focus)
        return blob


@dataclass
class CohortMetrics:
    cohort_tag: str
    total: int = 0
    pass_count: int = 0
    primary_hit_top_k: int = 0
    forbidden_hit_top_k: int = 0
    sum_reciprocal_rank: float = 0.0
    refusal_clean: int = 0    # corpus_gap_probe: top-k missed both primary AND forbidden

    def add(self, result: CohortQueryResult, *, top_k: int) -> None:
        self.total += 1
        if result.pass_status:
            self.pass_count += 1
        if result.primary_rank and result.primary_rank <= top_k:
            self.primary_hit_top_k += 1
            self.sum_reciprocal_rank += 1.0 / result.primary_rank
        if result.forbidden_hit_rank and result.forbidden_hit_rank <= top_k:
            self.forbidden_hit_top_k += 1
        if _is_refusal_clean_outcome(result.actual_outcome):
            self.refusal_clean += 1

    def to_dict(self, *, top_k: int) -> dict[str, Any]:
        recall = self.primary_hit_top_k / self.total if self.total else 0.0
        forbidden_rate = self.forbidden_hit_top_k / self.total if self.total else 0.0
        mrr = self.sum_reciprocal_rank / self.total if self.total else 0.0
        pass_rate = self.pass_count / self.total if self.total else 0.0
        return {
            "cohort_tag": self.cohort_tag,
            "total": self.total,
            "pass_count": self.pass_count,
            "pass_rate": round(pass_rate, 4),
            f"recall_at_{top_k}": round(recall, 4),
            f"forbidden_hit_rate_at_{top_k}": round(forbidden_rate, 4),
            "mrr": round(mrr, 4),
            "refusal_clean": self.refusal_clean,
        }


@dataclass
class CohortEvalReport:
    qrel_path: str
    top_k: int
    query_count: int
    overall_pass_rate: float
    per_query: list[CohortQueryResult]
    per_cohort: dict[str, CohortMetrics]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "qrel_path": self.qrel_path,
            "top_k": self.top_k,
            "query_count": self.query_count,
            "overall_pass_rate": round(self.overall_pass_rate, 4),
            "per_cohort": {
                tag: metrics.to_dict(top_k=self.top_k)
                for tag, metrics in self.per_cohort.items()
            },
            "per_query": [q.to_dict() for q in self.per_query],
            "metadata": dict(self.metadata),
        }


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------

def _first_matching_rank(
    final_paths: Sequence[str], targets: set[str], top_k: int,
) -> int | None:
    for rank, path in enumerate(final_paths[:top_k], start=1):
        if path in targets:
            return rank
    return None


def _hits_contain_refusal_sentinel(hits) -> bool:
    """True when the search response carries the Phase 9.3 sentinel.

    ``hits`` may be a list/tuple of dicts (real R3 output), an empty
    sequence, or ``None`` (legacy callers that don't know about the
    sentinel — fall through to the pre-9.3 grading).
    """
    if not hits:
        return False
    head = hits[0]
    return isinstance(head, dict) and head.get("sentinel") == "no_confident_match"


def _classify_outcome(
    *,
    cohort_tag: str,
    final_paths: tuple[str, ...],
    primary_paths: tuple[str, ...],
    acceptable_paths: tuple[str, ...],
    forbidden_paths: tuple[str, ...],
    top_k: int,
    hits: tuple | list | None = None,
) -> tuple[str, str, bool, int | None, int | None, int | None]:
    """Returns (expected_outcome, actual_outcome, pass_status,
    primary_rank, acceptable_rank, forbidden_hit_rank).

    ``hits`` is the raw search response. When provided, Phase 9.3
    refusal-sentinel detection runs for ``corpus_gap_probe`` queries
    so that real refusals get a ``tier_downgraded`` outcome (pass) and
    irrelevant top-K returns get ``silent_failure`` (fail). Legacy
    callers passing ``None`` see the pre-9.3 grading.
    """
    primary_rank = _first_matching_rank(
        final_paths, set(primary_paths), top_k,
    ) if primary_paths else None
    acceptable_rank = _first_matching_rank(
        final_paths, set(acceptable_paths), top_k,
    ) if acceptable_paths else None
    forbidden_rank = _first_matching_rank(
        final_paths, set(forbidden_paths), top_k,
    ) if forbidden_paths else None

    # Refusal cohorts: primary may be empty by design.
    if cohort_tag == "corpus_gap_probe":
        # Phase 9.3 — explicit refusal sentinel is the *real*
        # tier_downgraded pass. Honest "no confident match" answer.
        if hits is not None and _hits_contain_refusal_sentinel(hits):
            return ("refusal_clean", "tier_downgraded", True,
                    primary_rank, acceptable_rank, forbidden_rank)
        if forbidden_rank is not None:
            return ("refusal_clean", "forbidden_hit", False,
                    primary_rank, acceptable_rank, forbidden_rank)
        # If primary is set, primary_hit is also fine; otherwise refusal_clean
        if primary_rank is not None:
            return ("refusal_clean", "primary_hit", True,
                    primary_rank, acceptable_rank, forbidden_rank)
        if acceptable_rank is not None:
            return ("refusal_clean", "acceptable_hit", True,
                    primary_rank, acceptable_rank, forbidden_rank)
        # Phase 9.3 — when hits info is supplied (i.e. caller is on
        # the v9.3 contract) and no sentinel was emitted but no
        # primary/acceptable matched either, this is silent_failure:
        # R3 returned top-K garbage that the pre-9.3 metric scored as
        # refusal_clean=true. We now mark it as a regression.
        if hits is not None:
            return ("refusal_clean", "silent_failure", False,
                    primary_rank, acceptable_rank, forbidden_rank)
        # Legacy callers without hits info — preserve prior behavior.
        return ("refusal_clean", "refusal_clean", True,
                primary_rank, acceptable_rank, forbidden_rank)

    if cohort_tag == "forbidden_neighbor":
        # Pass if NO forbidden in top_k, regardless of primary.
        if forbidden_rank is not None:
            return ("forbidden_avoidance", "forbidden_hit", False,
                    primary_rank, acceptable_rank, forbidden_rank)
        if primary_rank is not None:
            return ("forbidden_avoidance", "primary_hit", True,
                    primary_rank, acceptable_rank, forbidden_rank)
        if acceptable_rank is not None:
            return ("forbidden_avoidance", "acceptable_hit", True,
                    primary_rank, acceptable_rank, forbidden_rank)
        # No forbidden hit AND no primary/acceptable — pass (clean)
        return ("forbidden_avoidance", "miss_clean", True,
                primary_rank, acceptable_rank, forbidden_rank)

    # Standard cohorts: pass requires primary in top_k AND no forbidden hit.
    if forbidden_rank is not None:
        return ("primary_in_top_k", "forbidden_hit", False,
                primary_rank, acceptable_rank, forbidden_rank)
    if primary_rank is not None:
        return ("primary_in_top_k", "primary_hit", True,
                primary_rank, acceptable_rank, forbidden_rank)
    if acceptable_rank is not None:
        # Acceptable hit is partial credit — counted as miss for strict
        # primary recall but flagged separately so analysts can audit
        # whether the canonical primary is mis-ranked.
        return ("primary_in_top_k", "acceptable_hit", False,
                primary_rank, acceptable_rank, forbidden_rank)
    return ("primary_in_top_k", "miss", False,
            primary_rank, acceptable_rank, forbidden_rank)


def _classify_failure(
    *,
    actual_outcome: str,
    pass_status: bool,
    failure_focus: Sequence[str],
    debug: dict,
) -> str | None:
    """Map an outcome + qrel-author failure_focus tags to a primary
    failure class. Returns None for passing queries.

    Classes (per system spec §4.4):
      - candidate_absent       — primary doc never reached fusion
      - retriever_absent       — primary in fusion but no retriever owned it
      - fusion_under_ranked    — primary in fusion but ranked below top_k
      - reranker_demoted       — primary in fusion top_k pre-rerank, dropped after
      - dedupe_lost            — primary chunk lost to doc-diversity dedupe
      - metadata_blocked       — primary filtered by doc_role/level/source_priority
      - qrel_incomplete        — answer was correct but primary was wrong
      - corpus_gap             — primary doesn't exist in corpus
      - query_understood_badly — query plan misclassified language/intent
      - forbidden_polluted     — forbidden surfaced in top_k

    Without a per-stage trace this classifier defers to ``failure_focus``
    when the trace is sparse. The classifier becomes more precise once
    the eval harness threads the per-stage trace metadata through.
    """
    if pass_status:
        return None
    if actual_outcome == "forbidden_hit":
        return "forbidden_polluted"
    if actual_outcome == "acceptable_hit":
        return "qrel_incomplete"
    # Use failure_focus tags as the primary signal when present
    focus = {f.lower() for f in failure_focus}
    if "corpus_gap" in focus:
        return "corpus_gap"
    if "paraphrase_robustness" in focus or "korean_no_alias_match" in focus:
        return "query_understood_badly"
    if "alias_overuse" in focus:
        return "fusion_under_ranked"
    if "reranker_demotion" in focus:
        return "reranker_demoted"
    # Default — primary missing without a clear signal
    return "candidate_absent"


# ---------------------------------------------------------------------------
# Harness
# ---------------------------------------------------------------------------

def evaluate_cohort_query(
    query: CohortQuery,
    search_fn: SearchFn,
    *,
    top_k: int,
    search_kwargs: dict[str, Any] | None = None,
    use_reformulated_query: bool = False,
) -> CohortQueryResult:
    debug: dict[str, Any] = {}
    started = time.perf_counter()
    search_call_kwargs = dict(search_kwargs or {})
    search_call_kwargs.setdefault("top_k", max(top_k, 5))
    if use_reformulated_query and query.reformulated_query:
        search_call_kwargs["reformulated_query"] = query.reformulated_query
    hits = search_fn(query.prompt, debug=debug, **search_call_kwargs)
    duration_ms = (time.perf_counter() - started) * 1000.0
    final_paths = tuple(h.get("path", "") for h in hits if h.get("path"))

    expected, actual, pass_status, prim_rank, acc_rank, forb_rank = _classify_outcome(
        cohort_tag=query.cohort_tag,
        final_paths=final_paths,
        primary_paths=query.primary_paths,
        acceptable_paths=query.acceptable_paths,
        forbidden_paths=query.forbidden_paths,
        top_k=top_k,
        hits=hits,
    )
    failure_class = _classify_failure(
        actual_outcome=actual,
        pass_status=pass_status,
        failure_focus=query.failure_focus,
        debug=debug,
    )
    return CohortQueryResult(
        query_id=query.query_id,
        cohort_tag=query.cohort_tag,
        language=query.language,
        level=query.level,
        primary_paths=query.primary_paths,
        acceptable_paths=query.acceptable_paths,
        forbidden_paths=query.forbidden_paths,
        final_paths=final_paths,
        primary_rank=prim_rank,
        acceptable_rank=acc_rank,
        forbidden_hit_rank=forb_rank,
        expected_outcome=expected,
        actual_outcome=actual,
        pass_status=pass_status,
        failure_class=failure_class,
        failure_focus=query.failure_focus,
        debug={
            "catalog_channels_used": debug.get("r3_catalog_channels_used", []),
            "fused_paths": debug.get("r3_final_paths", []),
            "reranker_model": debug.get("r3_reranker_model"),
        },
        duration_ms=round(duration_ms, 3),
    )


def evaluate_suite(
    suite: CohortQrelSuite,
    search_fn: SearchFn,
    *,
    top_k: int = 5,
    qrel_path: str = "",
    search_kwargs: dict[str, Any] | None = None,
    use_reformulated_query: bool = False,
) -> CohortEvalReport:
    per_query: list[CohortQueryResult] = []
    per_cohort: dict[str, CohortMetrics] = {
        tag: CohortMetrics(cohort_tag=tag) for tag in VALID_COHORTS
    }
    for query in suite.queries:
        result = evaluate_cohort_query(
            query, search_fn,
            top_k=top_k,
            search_kwargs=search_kwargs,
            use_reformulated_query=use_reformulated_query,
        )
        per_query.append(result)
        per_cohort[result.cohort_tag].add(result, top_k=top_k)

    pass_total = sum(1 for r in per_query if r.pass_status)
    overall = pass_total / len(per_query) if per_query else 0.0
    metadata = dict(suite.metadata)
    qrel_sha = _qrel_sha256(qrel_path)
    if qrel_sha is not None:
        metadata["qrel_sha256"] = qrel_sha
    return CohortEvalReport(
        qrel_path=qrel_path,
        top_k=top_k,
        query_count=len(per_query),
        overall_pass_rate=overall,
        per_query=per_query,
        per_cohort=per_cohort,
        metadata=metadata,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_default_search_fn(
    *, index_root: Path | None, catalog_root: Path | None,
) -> SearchFn:
    from scripts.learning.rag.r3.search import search

    def _fn(prompt: str, **kwargs: Any) -> list[dict]:
        return search(
            prompt,
            index_root=index_root,
            catalog_root=catalog_root,
            **kwargs,
        )
    return _fn


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qrels", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--index-root", type=Path, default=None)
    parser.add_argument("--catalog-root", type=Path, default=None)
    parser.add_argument(
        "--mode",
        choices=("cheap", "full"),
        default="full",
        help="R3 search mode (default: full).",
    )
    parser.add_argument(
        "--use-reformulated-query",
        action="store_true",
        help="Use the qrel's reformulated_query field for the semantic "
             "channels (dense + reranker). Lexical FTS still uses the raw "
             "prompt. Default: off (raw query for everything).",
    )
    args = parser.parse_args(argv)

    suite = load_cohort_qrels(args.qrels)
    search_fn = _build_default_search_fn(
        index_root=args.index_root,
        catalog_root=args.catalog_root,
    )
    report = evaluate_suite(
        suite,
        search_fn,
        top_k=args.top_k,
        qrel_path=str(args.qrels),
        search_kwargs={"mode": args.mode},
        use_reformulated_query=args.use_reformulated_query,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(
        f"[cohort-eval] {report.query_count} queries → "
        f"overall pass {report.overall_pass_rate:.2%} (top_k={report.top_k})"
    )
    for tag, metrics in report.per_cohort.items():
        if metrics.total == 0:
            continue
        d = metrics.to_dict(top_k=report.top_k)
        print(
            f"  {tag}: pass {d['pass_rate']:.2%} | "
            f"recall@{report.top_k}={d[f'recall_at_{report.top_k}']:.2%} | "
            f"forbidden@{report.top_k}={d[f'forbidden_hit_rate_at_{report.top_k}']:.2%}"
            f" | mrr={d['mrr']:.3f} | n={d['total']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
