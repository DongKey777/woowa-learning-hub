"""Phase 9.2 — personalization-aware fusion-stage score adjustments.

Pre-9.2: ``r3.search.search()`` accepted ``learner_context`` and set
``debug["learner_context_present"]`` — zero ranking impact.

Phase 9.2 adds two adjustment signals at the fusion stage (after
``fuse_candidates`` and before ``rerank``):

  * **mastered demote** — candidates whose ``concept_id`` matches a
    ``mastered_concepts[*].id`` in the learner profile get score
    minus ``mastered_demote`` (default 0.15). The learner already
    knows this concept; surfacing it again is wasted attention.

  * **uncertain / underexplored boost** — candidates matching
    ``uncertain_concepts[*].id`` or
    ``underexplored_in_current_stage[*].id`` get score plus
    ``weak_boost`` (default 0.10). These are the areas the learner
    is actively working through.

The ``concept:`` prefix used by
``learner_memory.build_learner_context`` (``concept:spring/bean``) is
stripped before matching the v3 corpus ``concept_id`` (``spring/bean``).

Default-off contract — gated on
``WOOWA_RAG_PERSONALIZATION_ENABLED=1`` in ``R3Config.from_env``.
The Phase 8 corpus migration must populate v3 ``concept_id`` on
≥30% of docs before adjustments become statistically meaningful
(currently 69 / 2,286 = 3%); flipping the env on with sparse
metadata yields tiny noisy effects.
"""

from __future__ import annotations

from typing import Any, Iterable, Sequence

from scripts.learning.rag.r3.candidate import Candidate


CONCEPT_PREFIX = "concept:"


def _normalize_concept_id(raw: Any) -> str | None:
    """Strip the ``concept:`` prefix learner_memory uses.

    learner_memory.build_learner_context emits ``concept:spring/bean``;
    the v3 corpus ``concept_id`` field is ``spring/bean`` (no prefix).
    Tolerate either form on input.
    """
    if not raw:
        return None
    cid = str(raw).strip()
    if not cid:
        return None
    if cid.startswith(CONCEPT_PREFIX):
        cid = cid[len(CONCEPT_PREFIX):]
    return cid or None


def _concept_set(items: Iterable[dict] | None) -> set[str]:
    """Build a set of normalized concept_ids from a list of dicts.

    Accepts the shapes used by build_learner_context — items with
    either ``id`` or ``concept_id`` key.
    """
    out: set[str] = set()
    if not items:
        return out
    for entry in items:
        if not isinstance(entry, dict):
            continue
        raw = entry.get("id") or entry.get("concept_id")
        cid = _normalize_concept_id(raw)
        if cid:
            out.add(cid)
    return out


def _candidate_concept_id(candidate: Candidate) -> str | None:
    cid = _normalize_concept_id(candidate.metadata.get("concept_id"))
    if cid:
        return cid
    document = candidate.metadata.get("document")
    if isinstance(document, dict):
        return _normalize_concept_id(document.get("concept_id"))
    return None


def _same_concept_family(profile_concept_id: str, candidate_concept_id: str) -> bool:
    profile_cid = _normalize_concept_id(profile_concept_id)
    candidate_cid = _normalize_concept_id(candidate_concept_id)
    if not profile_cid or not candidate_cid:
        return False
    if profile_cid == candidate_cid:
        return True
    if "/" not in profile_cid or "/" not in candidate_cid:
        return False
    profile_category, profile_slug = profile_cid.split("/", 1)
    candidate_category, candidate_slug = candidate_cid.split("/", 1)
    if profile_category != candidate_category:
        return False
    return (
        candidate_slug.startswith(f"{profile_slug}-")
        or profile_slug.startswith(f"{candidate_slug}-")
    )


def compute_score_adjustments(
    *,
    candidates: Sequence[Candidate],
    learner_context: Any,
    enabled: bool,
    mastered_demote: float = 0.15,
    weak_boost: float = 0.10,
) -> dict[int, float]:
    """Return a {position_index: adjustment_delta} dict.

    Adjustments are applied to the *position* in the input candidates
    list rather than candidate identity so the caller can feed the
    same list back into a sort. Position keys are the indices of
    ``candidates`` (0-based).
    """
    if not enabled:
        return {}
    if not isinstance(learner_context, dict):
        return {}

    profile = learner_context
    # learner_context shape (from learner_memory.build_learner_context):
    # ``{mastered_concepts: [{id, evidence}, ...], uncertain_concepts:
    # [{id, ask_count_7d, ...}, ...], underexplored_in_current_stage:
    # [{id, reason}, ...]}``.
    mastered = _concept_set(profile.get("mastered_concepts"))
    weak = _concept_set(profile.get("uncertain_concepts")) | _concept_set(
        profile.get("underexplored_in_current_stage")
    )

    adjustments: dict[int, float] = {}
    for idx, cand in enumerate(candidates):
        cid = _candidate_concept_id(cand)
        if cid is None:
            continue
        if any(_same_concept_family(mastered_id, cid) for mastered_id in mastered):
            adjustments[idx] = -float(mastered_demote)
        elif any(_same_concept_family(weak_id, cid) for weak_id in weak):
            adjustments[idx] = +float(weak_boost)
    return adjustments


def apply_score_adjustments(
    candidates: Sequence[Candidate],
    *,
    learner_context: Any,
    enabled: bool,
    mastered_demote: float = 0.15,
    weak_boost: float = 0.10,
) -> list[Candidate]:
    """Apply per-candidate adjustments and return a re-sorted list.

    No-op when ``enabled`` is False (Phase 8 dependency). Otherwise
    returns a new list with adjusted scores, sorted by the new score
    descending. Candidate identity (path / chunk_id / metadata) is
    preserved; only the ``score`` field changes.
    """
    if not enabled:
        return list(candidates)

    adjustments = compute_score_adjustments(
        candidates=candidates,
        learner_context=learner_context,
        enabled=enabled,
        mastered_demote=mastered_demote,
        weak_boost=weak_boost,
    )
    if not adjustments:
        return list(candidates)

    rebuilt: list[Candidate] = []
    for idx, cand in enumerate(candidates):
        delta = adjustments.get(idx)
        if delta is None:
            rebuilt.append(cand)
            continue
        rebuilt.append(
            Candidate(
                path=cand.path,
                retriever=cand.retriever,
                rank=cand.rank,
                score=float(cand.score) + delta,
                chunk_id=cand.chunk_id,
                title=cand.title,
                section_title=cand.section_title,
                metadata={
                    **cand.metadata,
                    "personalization_adjustment": float(delta),
                    "pre_personalization_score": float(cand.score),
                },
            )
        )
    rebuilt.sort(key=lambda c: (-c.score, c.path))
    return rebuilt
