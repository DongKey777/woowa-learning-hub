"""Phase 9.3 Step A — calibrate the R3 refusal threshold.

Companion to ``WOOWA_RAG_REFUSAL_THRESHOLD`` (config.py:_optional_float_from_env)
and the ``R3Config.refusal_threshold`` knob. Runs the live R3 pipeline
across two cohorts and reports the threshold that best separates them:

  * ``corpus_gap_probe`` (negatives) — queries the qrel marks as
    intentionally outside the corpus. Top-1 cross-encoder scores
    here represent "no confident match" — what we want to refuse.
  * ``paraphrase_human`` (positives) — high-quality paraphrase
    queries with primary_paths populated. Top-1 cross-encoder scores
    here represent "should be answered with citation".

Output (JSON, written to ``--out``):

  {
    "schema_version": 1,
    "computed_at": "<isoformat utc>",
    "qrel_path": "<input>",
    "top_k": 5,
    "negative_cohort": "corpus_gap_probe",
    "positive_cohort": "paraphrase_human",
    "negative_scores": [..., ...],          # top-1 ce_score per query
    "positive_scores": [..., ...],
    "negative_summary": {"n", "min", "p50", "p90", "p95", "max"},
    "positive_summary": {"n", "min", "p5", "p10", "p50", "max"},
    "f1_optimal_threshold": <float>,         # max-F1 separator
    "recommended_threshold": <float>,        # f1_optimal rounded down to nice boundary
    "report": "Set WOOWA_RAG_REFUSAL_THRESHOLD=<recommended>"
  }

The script does not write to ``R3Config`` or any env file — operators
read the report and decide whether to set the env. This keeps the
calibration auditable.

Usage::

    .venv/bin/python -m scripts.learning.rag.r3.eval.calibrate_refusal_threshold \\
        --qrels tests/fixtures/r3_qrels_real_v1.json \\
        --out reports/rag_eval/refusal_threshold_calibration.json \\
        --index-root state/cs_rag \\
        --catalog-root knowledge/cs/catalog
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from scripts.learning.rag.r3.eval.cohort_qrels import load_cohort_qrels


NEGATIVE_COHORT = "corpus_gap_probe"
POSITIVE_COHORT = "paraphrase_human"


def _percentile(values: Sequence[float], pct: float) -> float:
    if not values:
        return 0.0
    sorted_values = sorted(values)
    n = len(sorted_values)
    idx = max(0, min(n - 1, int(round((pct / 100.0) * (n - 1)))))
    return float(sorted_values[idx])


def _summary(values: Sequence[float]) -> dict[str, Any]:
    if not values:
        return {"n": 0}
    return {
        "n": len(values),
        "min": float(min(values)),
        "p5": _percentile(values, 5),
        "p10": _percentile(values, 10),
        "p50": _percentile(values, 50),
        "p90": _percentile(values, 90),
        "p95": _percentile(values, 95),
        "max": float(max(values)),
    }


def _f1_at_threshold(
    *, threshold: float,
    negatives: Sequence[float],
    positives: Sequence[float],
) -> float:
    """F1 of "negative class = score < threshold" classification.

    Treat the *negative* class (corpus_gap_probe) as the target — we
    want to maximize correct refusal detection. False negatives =
    corpus_gap_probe queries that scored above threshold (would
    silently fail). False positives = paraphrase queries that scored
    below threshold (would spuriously refuse).
    """
    tp = sum(1 for s in negatives if s < threshold)
    fn = sum(1 for s in negatives if s >= threshold)
    fp = sum(1 for s in positives if s < threshold)
    if tp + fp == 0 or tp + fn == 0:
        return 0.0
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def _f1_optimal_threshold(
    *,
    negatives: Sequence[float],
    positives: Sequence[float],
) -> float:
    """Sweep candidate thresholds (every observed score boundary) and
    return the one with the highest F1.

    Tie-break: prefer the *lower* threshold (more conservative refusal
    — fewer spurious refusals on positives)."""
    candidates = sorted(set(list(negatives) + list(positives)))
    if not candidates:
        return 0.0
    best_threshold = candidates[0]
    best_f1 = -1.0
    for boundary in candidates:
        score = _f1_at_threshold(threshold=boundary, negatives=negatives, positives=positives)
        if score > best_f1:
            best_f1 = score
            best_threshold = boundary
    return float(best_threshold)


def _round_recommendation(threshold: float) -> float:
    """Round *down* to the nearest 0.05 so the recommended config
    value stays slightly more conservative than the F1-optimal point.

    This biases toward fewer spurious refusals on positives at the
    cost of letting a few negatives slip through (preferable for the
    learner UX — silent_failure is recoverable via Phase 8 corpus
    growth, but an unwarranted refusal feels broken to the learner)."""
    return float(int(threshold * 20) / 20.0)


def _collect_top1_scores(
    queries: list[Any],
    *,
    search_fn,
    top_k: int,
    use_reformulated_query: bool,
) -> list[float]:
    """Run R3 on each query and collect top-1 cross_encoder_score.

    Skips queries where the reranker did not run (no ce_score in
    metadata) since calibration requires the reranker stage active.
    """
    out: list[float] = []
    for query in queries:
        debug: dict = {}
        kwargs: dict[str, Any] = {"top_k": max(top_k, 5), "debug": debug}
        if use_reformulated_query and getattr(query, "reformulated_query", None):
            kwargs["reformulated_query"] = query.reformulated_query
        hits = search_fn(query.prompt, **kwargs)
        if not hits:
            continue
        top = hits[0]
        # Sentinel hits carry the rejected raw cross-encoder score
        # in `rejected_score` (the gate's threshold check uses the
        # raw ce_score, not the hybrid RRF). Normal hits expose it
        # via `cross_encoder_score` (Phase 9.3 hit shape extension).
        if top.get("sentinel") == "no_confident_match":
            score = top.get("rejected_score")
        else:
            score = top.get("cross_encoder_score")
        try:
            score_float = float(score) if score is not None else None
        except (TypeError, ValueError):
            score_float = None
        if score_float is None:
            # Reranker did not run for this query (e.g. mode != full
            # or sidecar gating). Skip — calibration only meaningful
            # over reranked queries.
            continue
        out.append(score_float)
    return out


def calibrate(
    *,
    qrels_path: Path,
    search_fn,
    top_k: int = 5,
    use_reformulated_query: bool = True,
) -> dict[str, Any]:
    suite = load_cohort_qrels(qrels_path)
    negatives_q = [q for q in suite.queries if q.cohort_tag == NEGATIVE_COHORT]
    positives_q = [q for q in suite.queries if q.cohort_tag == POSITIVE_COHORT]
    if not negatives_q:
        raise RuntimeError(
            f"qrels has no {NEGATIVE_COHORT!r} queries — "
            "calibration requires both cohorts populated"
        )
    if not positives_q:
        raise RuntimeError(
            f"qrels has no {POSITIVE_COHORT!r} queries — "
            "calibration requires both cohorts populated"
        )

    # Force the threshold OFF for the calibration run so R3 returns
    # real top-1 reranks (not sentinels) on negative queries — we
    # need the raw distribution to set the threshold.
    saved = os.environ.get("WOOWA_RAG_REFUSAL_THRESHOLD")
    os.environ["WOOWA_RAG_REFUSAL_THRESHOLD"] = "off"
    try:
        negatives = _collect_top1_scores(
            negatives_q, search_fn=search_fn, top_k=top_k,
            use_reformulated_query=use_reformulated_query,
        )
        positives = _collect_top1_scores(
            positives_q, search_fn=search_fn, top_k=top_k,
            use_reformulated_query=use_reformulated_query,
        )
    finally:
        if saved is None:
            os.environ.pop("WOOWA_RAG_REFUSAL_THRESHOLD", None)
        else:
            os.environ["WOOWA_RAG_REFUSAL_THRESHOLD"] = saved

    f1_optimal = _f1_optimal_threshold(negatives=negatives, positives=positives)
    recommended = _round_recommendation(f1_optimal)

    return {
        "schema_version": 1,
        "computed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "qrel_path": str(qrels_path),
        "top_k": top_k,
        "use_reformulated_query": use_reformulated_query,
        "negative_cohort": NEGATIVE_COHORT,
        "positive_cohort": POSITIVE_COHORT,
        "negative_scores": negatives,
        "positive_scores": positives,
        "negative_summary": _summary(negatives),
        "positive_summary": _summary(positives),
        "f1_optimal_threshold": float(f1_optimal),
        "f1_at_optimal": _f1_at_threshold(
            threshold=f1_optimal, negatives=negatives, positives=positives,
        ),
        "recommended_threshold": recommended,
        "report": (
            f"Set WOOWA_RAG_REFUSAL_THRESHOLD={recommended} to enable Phase 9.3 "
            f"refusal sentinel. F1-optimal raw value was {f1_optimal:.4f}; "
            f"recommendation rounds down to nearest 0.05 for safety margin."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="calibrate_refusal_threshold",
        description=__doc__,
    )
    parser.add_argument("--qrels", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--index-root", type=Path, default=None)
    parser.add_argument("--catalog-root", type=Path, default=None)
    parser.add_argument(
        "--no-reformulated-query",
        action="store_true",
        help="Disable reformulated_query usage (default uses the qrel "
             "reformulation when present — matches production cohort_eval).",
    )
    args = parser.parse_args(argv)

    from scripts.learning.rag.r3.search import search

    def search_fn(prompt: str, **kwargs: Any) -> list[dict]:
        return search(
            prompt,
            index_root=args.index_root,
            catalog_root=args.catalog_root,
            **kwargs,
        )

    report = calibrate(
        qrels_path=args.qrels,
        search_fn=search_fn,
        top_k=args.top_k,
        use_reformulated_query=not args.no_reformulated_query,
    )
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[calibrate] negatives n={report['negative_summary']['n']} "
          f"positives n={report['positive_summary']['n']}")
    print(f"[calibrate] F1-optimal threshold = {report['f1_optimal_threshold']:.4f}")
    print(f"[calibrate] recommended threshold = {report['recommended_threshold']}")
    print(f"[calibrate] report → {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
