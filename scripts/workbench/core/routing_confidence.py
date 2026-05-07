"""Heuristic confidence scoring for the Tier classifier (plan §P4.4).

The Tier classifier (``interactive_rag_router.classify``) returns a
deterministic decision but no confidence. This module computes a
*post-hoc* confidence score from the decision + the matched-token
snapshot that the routing logger already collects. The AI session
reads the score and decides whether to round-trip through
``bin/rag-route-fallback`` (when confidence < threshold AND AI is
in-turn) or trust the heuristic.

Pure function — no I/O, no state. Designed to be cheap so the AI
session can call it once per turn without measurable latency.

## Score in [0.0, 1.0]

Higher = more confident. The score is the sum of evidence weights,
clamped to ``[0, 1]``, with category-specific tuning:

- **Override matched** → 1.0 (override always wins, no ambiguity).
- **Tier 3 with coach_request token AND PR open** → 0.95 (coach
  request is multi-word and unambiguous).
- **Tier 3 blocked** → 0.6 (we recognise the intent but can't fulfil;
  AI can't fix the gap, just confirm).
- **Tier 2 with depth signal AND domain match** → 0.85 (both
  conditions together is strong).
- **Tier 1 with definition/study intent signal AND domain match** → 0.75
  for definition, 0.72 for broad study intent (clear but slightly weaker
  than depth).
- **Tier 1 promoted by profile** → 0.7 (profile evidence layered
  over a Tier 1 → Tier 2 promotion is a soft call).
- **Tier 0 with tool token but no domain** → 0.85 (tool-only
  prompts are crisp).
- **Tier 0 with no signals at all** → 0.6 (off-topic chatter; no
  retrieval helps, but AI rephrasing might).
- **Mixed / weak** signal counts adjust the base score downward by
  ``0.1 × (ambiguous_buckets)``.

The thresholds in the docstring are the defaults — ``threshold``
parameter is exposed so callers can tune the AI fallback trigger
empirically.

Tested in ``tests/unit/test_routing_confidence.py``.
"""

from __future__ import annotations

from dataclasses import dataclass


# Heuristic threshold below which the AI session should consider
# falling back to the AI router classifier. Tuned for "ambiguous
# 10%" target per plan §P4.4.
DEFAULT_FALLBACK_THRESHOLD = 0.55


@dataclass(frozen=True)
class ConfidenceResult:
    score: float            # [0.0, 1.0]
    rationale: str          # one-line human-readable explanation
    should_fallback: bool   # True when score < threshold


def _sum_lengths(matched: dict, *keys: str) -> int:
    total = 0
    for k in keys:
        v = matched.get(k)
        if isinstance(v, list):
            total += len(v)
    return total


def score_decision(
    *,
    decision: dict,
    matched_tokens: dict,
    threshold: float = DEFAULT_FALLBACK_THRESHOLD,
) -> ConfidenceResult:
    """Score the heuristic decision.

    ``decision`` is a dict with at least: tier, mode, override_active,
    blocked, promoted_by_profile (RouterDecision.asdict() shape).
    ``matched_tokens`` is the snapshot from
    ``routing_log.collect_matched_tokens(prompt)``.
    """
    if not (0.0 <= threshold <= 1.0):
        raise ValueError("threshold must be in [0, 1]")

    tier = decision.get("tier")
    blocked = bool(decision.get("blocked", False))
    override_active = bool(decision.get("override_active", False))
    promoted = bool(decision.get("promoted_by_profile", False))

    if override_active:
        return _result(1.0, "override matched — bypass classifier", threshold)

    n_definition = _sum_lengths(matched_tokens, "definition")
    n_depth = _sum_lengths(matched_tokens, "depth")
    n_study = _sum_lengths(matched_tokens, "study_intent")
    n_domain = _sum_lengths(matched_tokens, "cs_domain", "learning_concept", "corpus_signal")
    n_coach = _sum_lengths(matched_tokens, "coach_request")
    n_tool = _sum_lengths(matched_tokens, "tool")

    # Tier 3
    if tier == 3:
        if blocked:
            return _result(0.6, "tier3 intent recognised but preconditions missing", threshold)
        if n_coach >= 1:
            return _result(0.95, "tier3 coach_request matched + PR ready", threshold)
        return _result(0.5, "tier3 selected without coach_request token", threshold)

    # Tier 2
    if tier == 2:
        if promoted:
            return _result(0.7, "tier2 promoted by profile (soft call)", threshold)
        if n_depth >= 1 and n_domain >= 1:
            base = 0.85
            # Penalty fires only when *unrelated* buckets also matched
            # (definition / coach_request / tool) — cs_domain and
            # learning_concept both count as "domain" for the classifier
            # so they're never an ambiguity source on their own.
            if _ambiguity_penalty(
                matched_tokens, expected={"depth", "cs_domain", "learning_concept", "corpus_signal"},
            ) > 0:
                base -= 0.05
            return _result(base, "tier2 depth + domain", threshold)
        return _result(0.55, "tier2 selected with weak signals", threshold)

    # Tier 1
    if tier == 1:
        if n_definition >= 1 and n_domain >= 1:
            return _result(0.75, "tier1 definition + domain", threshold)
        if n_study >= 1 and n_domain >= 1:
            return _result(0.72, "tier1 study intent + domain", threshold)
        if promoted:
            return _result(0.7, "tier1 promoted by profile", threshold)
        return _result(0.5, "tier1 selected with weak signals", threshold)

    # Tier 0
    if tier == 0:
        if n_tool >= 1 and n_domain == 0 and n_definition == 0 and n_depth == 0 and n_study == 0:
            return _result(0.85, "tier0 tool/build question, no domain", threshold)
        if n_domain == 0 and n_definition == 0 and n_depth == 0 and n_study == 0 and n_coach == 0:
            return _result(0.6, "tier0 off-topic — no retrieval signal", threshold)
        # Tier 0 *despite* some signal count is the suspicious case.
        # E.g. domain matched but classifier punted because tool also
        # matched — the AI fallback could probably help.
        return _result(0.4, "tier0 but signal tokens matched — possible miss", threshold)

    return _result(0.3, f"unknown tier={tier}", threshold)


def _ambiguity_penalty(matched_tokens: dict, *, expected: set[str]) -> int:
    """Count buckets that fired *outside* the ones the decision relies
    on. A high count indicates the prompt straddles intents (e.g.
    domain + tool + definition all matched) and is more likely to
    benefit from AI re-classification."""
    extra = {"definition", "depth", "study_intent", "cs_domain", "learning_concept",
             "corpus_signal", "coach_request", "tool"} - expected - {"override"}
    score = 0
    for k in extra:
        if _sum_lengths(matched_tokens, k) > 0:
            score += 1
    return score


def _result(score: float, rationale: str, threshold: float) -> ConfidenceResult:
    clamped = max(0.0, min(1.0, score))
    return ConfidenceResult(
        score=clamped,
        rationale=rationale,
        should_fallback=clamped < threshold,
    )
