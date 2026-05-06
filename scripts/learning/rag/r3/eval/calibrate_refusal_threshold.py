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
    "schema_version": 4,
    "computed_at": "<isoformat utc>",
    "qrel_path": "<input>",
    "top_k": 5,
    "use_reformulated_query": true,
    "negative_cohort": "corpus_gap_probe",
    "positive_cohort": "paraphrase_human",
    "negative_query_count": 20,
    "positive_query_count": 50,
    "negative_score_count": 20,
    "positive_score_count": 50,
    "negative_score_coverage_rate": 1.0,
    "positive_score_coverage_rate": 1.0,
    "negative_scores": [..., ...],          # top-1 ce_score per query
    "positive_scores": [..., ...],
    "negative_summary": {"n", "min", "p50", "p90", "p95", "max"},
    "positive_summary": {"n", "min", "p5", "p10", "p50", "max"},
    "refusal_rule": "top1_cross_encoder_score < threshold",
    "threshold_semantics": "strict_less_than_preserves_equal_scores",
    "score_source": "top hit cross_encoder_score (sentinel fallback uses rejected_score)",
    "coverage_requirement": "full_reranked_scores_per_cohort",
    "recommended_rounding_policy": "floor_to_nearest_0.05",
    "separation_diagnostics": {
      "strict_gap_exists": true,
      "max_negative_score": <float>,
      "min_positive_score": <float>,
      "strict_gap_width": <float>,
      "negative_overlap_count_at_or_above_min_positive": <int>,
      "positive_overlap_count_at_or_below_max_negative": <int>,
      "zero_spurious_margin_below_min_positive": <float>,
      "zero_spurious_coverage_over_max_negative": <float>,
      "f1_optimal_margin_below_min_positive": <float>,
      "f1_optimal_coverage_over_max_negative": <float>
    },
    "boundary_diagnostics": {
      "zero_spurious_negative_equal_count": <int>,
      "zero_spurious_positive_equal_count": <int>,
      "f1_optimal_negative_equal_count": <int>,
      "f1_optimal_positive_equal_count": <int>
    },
    "calibration_env_defaults": {...},
    "calibration_env_applied": {..., "WOOWA_RAG_REFUSAL_THRESHOLD": "off"},
    "f1_optimal_threshold": <float>,         # max-F1 separator
    "f1_optimal_outcomes": {...},            # refusal tradeoff counts at raw optimum
    "recommendation_policy": "prefer_zero_spurious_floor_0.05_else_off",
    "recommendation_mode": "zero_spurious_numeric" | "disabled_overlap",
    "numeric_recommendation_min_negative_recall": 0.50,
    "zero_spurious_numeric_candidate_threshold": <float>,
    "zero_spurious_numeric_candidate_env_value": "0.10",
    "zero_spurious_numeric_candidate_outcomes": {...},
    "recommended_threshold": <float> | null,
    "recommended_env_value": "0.10" | "off",
    "runtime_default_env_file": "bin/_rag_env.sh",
    "runtime_default_env_value": "0.10",     # parsed from wrapper default
    "runtime_default_parse_status": "ok",
    "runtime_default_parse_contract": "accepts export_or_assignment plus literal_or_${...} values, with quoted_or_unquoted fallbacks and inner-quoted defaults",
    "runtime_default_matches_recommendation": true,
    "runtime_default_numeric_delta_from_recommendation": 0.0,
    "runtime_default_drift_severity": "aligned",
    "runtime_default_comparison_basis": "numeric_if_parseable_else_string",
    "f1_at_recommended": <float> | null,
    "recommended_outcomes": {...} | null,    # null when the safe recommendation is "off"
    "report": "Keep WOOWA_RAG_REFUSAL_THRESHOLD=<recommended>"
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
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence

from scripts.learning.rag.r3.eval.cohort_qrels import load_cohort_qrels


NEGATIVE_COHORT = "corpus_gap_probe"
POSITIVE_COHORT = "paraphrase_human"
CALIBRATION_ENV_DEFAULTS = {
    "WOOWA_RAG_R3_ENABLED": "1",
    "WOOWA_RAG_R3_RERANK_POLICY": "always",
    "WOOWA_RAG_R3_FORBIDDEN_FILTER": "1",
    "HF_HUB_OFFLINE": "1",
}
RECOMMENDATION_POLICY = "prefer_zero_spurious_floor_0.05_else_off"
NUMERIC_RECOMMENDATION_MIN_NEGATIVE_RECALL = 0.50
REPO_ROOT = Path(__file__).resolve().parents[5]
RUNTIME_ENV_RELATIVE_PATH = Path("bin/_rag_env.sh")
RUNTIME_ENV_FILE = REPO_ROOT / RUNTIME_ENV_RELATIVE_PATH
RUNTIME_THRESHOLD_ASSIGNMENT_RE = re.compile(
    r"^\s*(?:export\s+)?WOOWA_RAG_REFUSAL_THRESHOLD\s*=\s*(?P<rhs>.+?)\s*$"
)
RUNTIME_THRESHOLD_FALLBACK_RE = re.compile(
    r"""^(?P<quote>["']?)\$\{WOOWA_RAG_REFUSAL_THRESHOLD:-(?P<value>[^}]*)\}(?P=quote)$"""
)
RUNTIME_THRESHOLD_LITERAL_RE = re.compile(
    r"""^(?P<quote>["']?)(?P<value>[^"']+?)(?P=quote)$"""
)
RUNTIME_DEFAULT_PARSE_CONTRACT = (
    "accepts export_or_assignment plus literal_or_${...} values, with quoted_or_unquoted "
    "fallbacks and inner-quoted defaults"
)


def _strip_matching_quotes(value: str) -> str:
    text = value.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        return text[1:-1]
    return text


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


def _threshold_outcomes(
    *,
    threshold: float,
    negatives: Sequence[float],
    positives: Sequence[float],
) -> dict[str, Any]:
    """Summarize refusal-vs-answer outcomes at one threshold.

    The negative class (`corpus_gap_probe`) is the refusal target.
    Counts are reported explicitly so operators can see the tradeoff:
    how many corpus-gap queries still slip through as silent failures,
    and how many paraphrase queries would be spuriously refused.
    """
    correct_refusals = sum(1 for s in negatives if s < threshold)
    silent_failures = sum(1 for s in negatives if s >= threshold)
    spurious_refusals = sum(1 for s in positives if s < threshold)
    preserved_answers = sum(1 for s in positives if s >= threshold)
    precision = (
        correct_refusals / (correct_refusals + spurious_refusals)
        if (correct_refusals + spurious_refusals) > 0 else 0.0
    )
    recall = (
        correct_refusals / (correct_refusals + silent_failures)
        if (correct_refusals + silent_failures) > 0 else 0.0
    )
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0 else 0.0
    )
    negative_total = len(negatives)
    positive_total = len(positives)
    return {
        "threshold": float(threshold),
        "correct_refusals": correct_refusals,
        "silent_failures": silent_failures,
        "spurious_refusals": spurious_refusals,
        "preserved_answers": preserved_answers,
        "negative_recall": recall,
        "positive_preservation_rate": (
            preserved_answers / positive_total if positive_total > 0 else 0.0
        ),
        "negative_silent_failure_rate": (
            silent_failures / negative_total if negative_total > 0 else 0.0
        ),
        "precision": precision,
        "f1": f1,
    }


def _f1_optimal_threshold(
    *,
    negatives: Sequence[float],
    positives: Sequence[float],
) -> float:
    """Sweep candidate thresholds (every observed score boundary) and
    return the one with the highest F1.

    Tie-break: prefer the *lower* threshold (more conservative refusal
    — fewer spurious refusals on positives).

    The candidate sweep also includes one open interval just above the
    maximum observed score so a max-score negative can still become a
    correct refusal during calibration."""
    candidates = sorted(set(list(negatives) + list(positives)))
    if not candidates:
        return 0.0
    # The refusal rule is strict (`score < threshold`), so the
    # candidate sweep must include one value *above* the max observed
    # score. Otherwise a max-score negative can never be classified as
    # refused during calibration even though any threshold just above
    # it would do so in production.
    upper_open_candidate = math.nextafter(candidates[-1], math.inf)
    if upper_open_candidate > candidates[-1]:
        candidates.append(upper_open_candidate)
    best_threshold = candidates[0]
    best_f1 = -1.0
    for boundary in candidates:
        score = _f1_at_threshold(threshold=boundary, negatives=negatives, positives=positives)
        if score > best_f1 or (
            score == best_f1 and boundary < best_threshold
        ):
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
    return float(math.floor(threshold * 20) / 20.0)


def _format_threshold(threshold: float) -> str:
    """Render a threshold the same way operators paste it into env files."""
    return f"{threshold:.2f}"


def _zero_spurious_numeric_candidate(
    *,
    positives: Sequence[float],
) -> float:
    """Return the highest 0.05-grid threshold that preserves all positives."""
    if not positives:
        return 0.0
    return _round_recommendation(float(min(positives)))


def _recommend_threshold(
    *,
    negatives: Sequence[float],
    positives: Sequence[float],
) -> tuple[float | None, str, str, dict[str, Any]]:
    """Choose a learner-safe default from the observed score overlap.

    Phase 9.3 defaults should not ship a numeric threshold unless the
    rounded 0.05-grid candidate preserves every positive query while
    still catching a meaningful share of corpus-gap negatives. When
    the cohorts overlap too heavily, recommend ``off`` and surface the
    zero-spurious numeric candidate only as a diagnostic.
    """
    candidate_threshold = _zero_spurious_numeric_candidate(positives=positives)
    candidate_outcomes = _threshold_outcomes(
        threshold=candidate_threshold,
        negatives=negatives,
        positives=positives,
    )
    if (
        candidate_threshold > 0.0
        and candidate_outcomes["spurious_refusals"] == 0
        and candidate_outcomes["negative_recall"] >= NUMERIC_RECOMMENDATION_MIN_NEGATIVE_RECALL
    ):
        return (
            candidate_threshold,
            _format_threshold(candidate_threshold),
            "zero_spurious_numeric",
            candidate_outcomes,
        )
    return (
        None,
        "off",
        "disabled_overlap",
        candidate_outcomes,
    )


def _separation_diagnostics(
    *,
    negatives: Sequence[float],
    positives: Sequence[float],
    recommended_threshold: float,
    f1_optimal_threshold: float,
) -> dict[str, Any]:
    if not negatives or not positives:
        return {
            "strict_gap_exists": False,
            "max_negative_score": None,
            "min_positive_score": None,
            "strict_gap_width": None,
            "negative_overlap_count_at_or_above_min_positive": None,
            "positive_overlap_count_at_or_below_max_negative": None,
            "zero_spurious_margin_below_min_positive": None,
            "zero_spurious_coverage_over_max_negative": None,
            "f1_optimal_margin_below_min_positive": None,
            "f1_optimal_coverage_over_max_negative": None,
        }

    max_negative = float(max(negatives))
    min_positive = float(min(positives))
    return {
        "strict_gap_exists": max_negative < min_positive,
        "max_negative_score": max_negative,
        "min_positive_score": min_positive,
        "strict_gap_width": float(min_positive - max_negative),
        "negative_overlap_count_at_or_above_min_positive": sum(
            1 for score in negatives if score >= min_positive
        ),
        "positive_overlap_count_at_or_below_max_negative": sum(
            1 for score in positives if score <= max_negative
        ),
        "zero_spurious_margin_below_min_positive": float(
            min_positive - recommended_threshold
        ),
        "zero_spurious_coverage_over_max_negative": float(
            recommended_threshold - max_negative
        ),
        "f1_optimal_margin_below_min_positive": float(
            min_positive - f1_optimal_threshold
        ),
        "f1_optimal_coverage_over_max_negative": float(
            f1_optimal_threshold - max_negative
        ),
    }


def _boundary_diagnostics(
    *,
    negatives: Sequence[float],
    positives: Sequence[float],
    recommended_threshold: float,
    f1_optimal_threshold: float,
) -> dict[str, int]:
    return {
        "zero_spurious_negative_equal_count": sum(
            1 for score in negatives if score == recommended_threshold
        ),
        "zero_spurious_positive_equal_count": sum(
            1 for score in positives if score == recommended_threshold
        ),
        "f1_optimal_negative_equal_count": sum(
            1 for score in negatives if score == f1_optimal_threshold
        ),
        "f1_optimal_positive_equal_count": sum(
            1 for score in positives if score == f1_optimal_threshold
        ),
    }


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


def _require_full_score_coverage(
    *,
    queries: Sequence[Any],
    scores: Sequence[float],
    cohort_name: str,
) -> None:
    if len(scores) != len(queries):
        raise RuntimeError(
            f"calibration collected {len(scores)}/{len(queries)} reranked scores for "
            f"{cohort_name!r}. Calibration requires full cohort coverage so the "
            "recommended threshold is not biased by skipped queries. Ensure the "
            "R3 reranker weights/index are available and that sidecar-only gating "
            "did not bypass cross-encoder scoring."
        )


def _env_snapshot(keys: Sequence[str]) -> dict[str, str | None]:
    return {key: os.environ.get(key) for key in keys}


def _restore_env(snapshot: dict[str, str | None]) -> None:
    for key, value in snapshot.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def _read_runtime_default_threshold(
    env_file: Path = RUNTIME_ENV_FILE,
) -> tuple[str | None, str]:
    try:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if "WOOWA_RAG_REFUSAL_THRESHOLD" not in stripped:
                continue
            if "#" in stripped:
                stripped = stripped.split("#", 1)[0].rstrip()
            match = RUNTIME_THRESHOLD_ASSIGNMENT_RE.match(stripped)
            if match is None:
                return None, "unparseable"
            rhs = match.group("rhs").strip()
            fallback_match = RUNTIME_THRESHOLD_FALLBACK_RE.match(rhs)
            if fallback_match is not None:
                return _strip_matching_quotes(fallback_match.group("value")), "ok"
            literal_match = RUNTIME_THRESHOLD_LITERAL_RE.match(rhs)
            if literal_match is not None:
                return _strip_matching_quotes(literal_match.group("value")), "ok"
            return None, "unparseable"
    except FileNotFoundError:
        return None, "missing"
    return None, "not_found"


def _parse_threshold_value(raw: str | None) -> float | None:
    if raw is None:
        return None
    text = raw.strip()
    if not text or text.lower() == "off":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _runtime_default_matches_recommendation(
    runtime_default_raw: str | None,
    recommended_raw: str,
) -> bool:
    runtime_numeric = _parse_threshold_value(runtime_default_raw)
    recommended_numeric = _parse_threshold_value(recommended_raw)
    if runtime_numeric is not None and recommended_numeric is not None:
        return math.isclose(runtime_numeric, recommended_numeric, rel_tol=0.0, abs_tol=1e-12)
    return runtime_default_raw == recommended_raw


def _runtime_default_delta_from_recommendation(
    runtime_default_raw: str | None,
    recommended_raw: str,
) -> float | None:
    runtime_numeric = _parse_threshold_value(runtime_default_raw)
    recommended_numeric = _parse_threshold_value(recommended_raw)
    if runtime_numeric is None or recommended_numeric is None:
        return None
    return float(runtime_numeric - recommended_numeric)


def _runtime_default_drift_severity(
    *,
    runtime_default_raw: str | None,
    recommended_raw: str,
    parse_status: str,
    matches_recommendation: bool,
) -> str:
    if parse_status != "ok":
        return "parse_error"
    if matches_recommendation:
        return "aligned"
    if (
        _parse_threshold_value(runtime_default_raw) is not None
        and _parse_threshold_value(recommended_raw) is not None
    ):
        return "numeric_drift"
    return "string_mismatch"


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
    env_keys = tuple(CALIBRATION_ENV_DEFAULTS) + ("WOOWA_RAG_REFUSAL_THRESHOLD",)
    saved = _env_snapshot(env_keys)
    os.environ.update(CALIBRATION_ENV_DEFAULTS)
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
        _restore_env(saved)

    _require_full_score_coverage(
        queries=negatives_q,
        scores=negatives,
        cohort_name=NEGATIVE_COHORT,
    )
    _require_full_score_coverage(
        queries=positives_q,
        scores=positives,
        cohort_name=POSITIVE_COHORT,
    )

    f1_optimal = _f1_optimal_threshold(negatives=negatives, positives=positives)
    recommended, recommended_env_value, recommendation_mode, zero_spurious_candidate_outcomes = (
        _recommend_threshold(
            negatives=negatives,
            positives=positives,
        )
    )
    recommended_threshold_for_diagnostics = (
        recommended if recommended is not None else 0.0
    )
    runtime_default_env_value, runtime_default_parse_status = _read_runtime_default_threshold()
    runtime_default_matches_recommendation = _runtime_default_matches_recommendation(
        runtime_default_env_value,
        recommended_env_value,
    )
    runtime_default_delta = _runtime_default_delta_from_recommendation(
        runtime_default_env_value,
        recommended_env_value,
    )
    runtime_default_drift_severity = _runtime_default_drift_severity(
        runtime_default_raw=runtime_default_env_value,
        recommended_raw=recommended_env_value,
        parse_status=runtime_default_parse_status,
        matches_recommendation=runtime_default_matches_recommendation,
    )
    f1_optimal_outcomes = _threshold_outcomes(
        threshold=f1_optimal, negatives=negatives, positives=positives,
    )
    recommended_outcomes = (
        _threshold_outcomes(threshold=recommended, negatives=negatives, positives=positives)
        if recommended is not None else None
    )
    separation_diagnostics = _separation_diagnostics(
        negatives=negatives,
        positives=positives,
        recommended_threshold=recommended_threshold_for_diagnostics,
        f1_optimal_threshold=f1_optimal,
    )
    boundary_diagnostics = _boundary_diagnostics(
        negatives=negatives,
        positives=positives,
        recommended_threshold=recommended_threshold_for_diagnostics,
        f1_optimal_threshold=f1_optimal,
    )

    return {
        "schema_version": 4,
        "computed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "qrel_path": str(qrels_path),
        "top_k": top_k,
        "use_reformulated_query": use_reformulated_query,
        "calibration_env_defaults": dict(CALIBRATION_ENV_DEFAULTS),
        "calibration_env_applied": {
            **CALIBRATION_ENV_DEFAULTS,
            "WOOWA_RAG_REFUSAL_THRESHOLD": "off",
        },
        "negative_cohort": NEGATIVE_COHORT,
        "positive_cohort": POSITIVE_COHORT,
        "negative_query_count": len(negatives_q),
        "positive_query_count": len(positives_q),
        "negative_score_count": len(negatives),
        "positive_score_count": len(positives),
        "negative_score_coverage_rate": (
            len(negatives) / len(negatives_q) if negatives_q else 0.0
        ),
        "positive_score_coverage_rate": (
            len(positives) / len(positives_q) if positives_q else 0.0
        ),
        "negative_scores": negatives,
        "positive_scores": positives,
        "negative_summary": _summary(negatives),
        "positive_summary": _summary(positives),
        "refusal_rule": "top1_cross_encoder_score < threshold",
        "threshold_semantics": "strict_less_than_preserves_equal_scores",
        "score_source": (
            "top hit cross_encoder_score "
            "(sentinel fallback uses rejected_score)"
        ),
        "coverage_requirement": "full_reranked_scores_per_cohort",
        "recommended_rounding_policy": "floor_to_nearest_0.05",
        "separation_diagnostics": separation_diagnostics,
        "boundary_diagnostics": boundary_diagnostics,
        "f1_optimal_threshold": float(f1_optimal),
        "f1_at_optimal": f1_optimal_outcomes["f1"],
        "f1_optimal_outcomes": f1_optimal_outcomes,
        "recommendation_policy": RECOMMENDATION_POLICY,
        "recommendation_mode": recommendation_mode,
        "numeric_recommendation_min_negative_recall": (
            NUMERIC_RECOMMENDATION_MIN_NEGATIVE_RECALL
        ),
        "zero_spurious_numeric_candidate_threshold": (
            zero_spurious_candidate_outcomes["threshold"]
        ),
        "zero_spurious_numeric_candidate_env_value": _format_threshold(
            zero_spurious_candidate_outcomes["threshold"]
        ),
        "zero_spurious_numeric_candidate_outcomes": zero_spurious_candidate_outcomes,
        "recommended_threshold": recommended,
        "recommended_env_value": recommended_env_value,
        "runtime_default_env_file": str(RUNTIME_ENV_RELATIVE_PATH),
        "runtime_default_env_value": runtime_default_env_value,
        "runtime_default_parse_status": runtime_default_parse_status,
        "runtime_default_parse_contract": (
            RUNTIME_DEFAULT_PARSE_CONTRACT
        ),
        "runtime_default_matches_recommendation": runtime_default_matches_recommendation,
        "runtime_default_numeric_delta_from_recommendation": runtime_default_delta,
        "runtime_default_drift_severity": runtime_default_drift_severity,
        "runtime_default_comparison_basis": "numeric_if_parseable_else_string",
        "f1_at_recommended": (
            recommended_outcomes["f1"] if recommended_outcomes is not None else None
        ),
        "recommended_outcomes": recommended_outcomes,
        "report": (
            f"{'Set' if recommended_outcomes is not None else 'Keep'} "
            f"WOOWA_RAG_REFUSAL_THRESHOLD={recommended_env_value} "
            f"{'to enable Phase 9.3 refusal sentinel' if recommended_outcomes is not None else 'until Phase 9.3 overlap improves enough for a learner-safe numeric sentinel'}" 
            f". F1-optimal raw value was {f1_optimal:.4f}; "
            f"recommendation policy is {RECOMMENDATION_POLICY}. "
            f"Wrapper default in {RUNTIME_ENV_RELATIVE_PATH} is "
            f"{runtime_default_env_value or 'unavailable'} "
            f"({'aligned' if runtime_default_matches_recommendation else 'drifted'}, "
            f"parse_status={runtime_default_parse_status}, "
            f"drift_severity={runtime_default_drift_severity}, "
            f"numeric_delta={runtime_default_delta if runtime_default_delta is not None else 'n/a'}). "
            f"Negative/positive top-1 scores "
            f"{'do not overlap' if separation_diagnostics['strict_gap_exists'] else 'overlap'} "
            f"({separation_diagnostics['negative_overlap_count_at_or_above_min_positive']} "
            f"negatives at/above the weakest positive, "
            f"{separation_diagnostics['positive_overlap_count_at_or_below_max_negative']} "
            f"positives at/below the strongest negative). "
            f"Zero-spurious numeric candidate leaves a "
            f"{separation_diagnostics['zero_spurious_margin_below_min_positive']:.4f} "
            f"margin below the weakest positive and has a "
            f"{separation_diagnostics['zero_spurious_coverage_over_max_negative']:.4f} "
            f"delta versus the strongest negative. "
            f"Exact-boundary scores remain answerable because runtime uses "
            f"`score < threshold`: "
            f"{boundary_diagnostics['zero_spurious_positive_equal_count']} positives/"
            f"{boundary_diagnostics['zero_spurious_negative_equal_count']} negatives sit exactly "
            f"on the shipped threshold, and "
            f"{boundary_diagnostics['f1_optimal_positive_equal_count']} positives/"
            f"{boundary_diagnostics['f1_optimal_negative_equal_count']} negatives sit exactly "
            f"on the raw F1-optimal threshold. "
            f"Zero-spurious numeric candidate = "
            f"{zero_spurious_candidate_outcomes['threshold']:.4f}: "
            f"{zero_spurious_candidate_outcomes['correct_refusals']}/{len(negatives)} "
            f"corpus-gap queries downgrade cleanly, "
            f"{zero_spurious_candidate_outcomes['silent_failures']}/{len(negatives)} "
            f"still slip through as silent failures, "
            f"{zero_spurious_candidate_outcomes['spurious_refusals']}/{len(positives)} "
            f"paraphrase queries are spuriously refused. "
            f"{'Recommendation stays numeric.' if recommended_outcomes is not None else 'Observed overlap is too high for a learner-safe numeric default, so the shipped recommendation stays off.'} "
            f"Cross-encoder coverage during calibration was "
            f"{len(negatives)}/{len(negatives_q)} negatives and "
            f"{len(positives)}/{len(positives_q)} positives."
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
