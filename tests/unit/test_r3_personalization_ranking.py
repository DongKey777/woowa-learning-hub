"""Phase 9.2 — personalization-aware ranking in R3 (default off).

Pre-9.2: r3.search.search() received learner_context but only set
`debug["learner_context_present"]` — zero ranking impact.

Phase 9.2 introduces a fusion-stage score adjustment driven by the
learner profile:

  * mastered_concepts → demote candidates whose concept_id matches
    (learner already knows this; surface the next thing instead)
  * weak_dimensions / underexplored_in_current_stage → boost
    candidates in those areas

The feature is gated on ``WOOWA_RAG_PERSONALIZATION_ENABLED=1`` and
defaults off because Phase 8 corpus migration must populate v3
``concept_id`` on ≥30% of docs before adjustments become meaningful
(currently 69 / 2,286 = 3%).

The ``concept:`` prefix used by ``learner_memory.build_learner_context``
(``concept:spring/bean``) is stripped before matching the v3 corpus
``concept_id`` (``spring/bean``).
"""

from __future__ import annotations

import unittest

from scripts.learning.rag.r3 import personalization
from scripts.learning.rag.r3.candidate import Candidate


def _candidate(
    path: str, *, concept_id: str | None = None, score: float = 0.5,
    rank: int = 1,
) -> Candidate:
    metadata: dict = {}
    if concept_id is not None:
        metadata["concept_id"] = concept_id
    return Candidate(
        path=path, retriever="test", rank=rank, score=score,
        chunk_id=f"{path}#0", metadata=metadata,
    )


def _candidate_with_document_concept(
    path: str,
    *,
    concept_id: str,
    score: float = 0.5,
    rank: int = 1,
) -> Candidate:
    return Candidate(
        path=path,
        retriever="test",
        rank=rank,
        score=score,
        chunk_id=f"{path}#0",
        metadata={"document": {"concept_id": concept_id}},
    )


# ---------------------------------------------------------------------------
# Disabled-by-default contract (Phase 8 dependency)
# ---------------------------------------------------------------------------

class DisabledByDefaultTest(unittest.TestCase):
    def test_compute_returns_empty_when_disabled(self):
        adjustments = personalization.compute_score_adjustments(
            candidates=[_candidate("knowledge/cs/contents/spring/x.md",
                                   concept_id="spring/di")],
            learner_context={"mastered_concepts": [{"id": "concept:spring/di"}]},
            enabled=False,
        )
        self.assertEqual(adjustments, {})

    def test_apply_is_noop_when_disabled(self):
        cands = [_candidate("knowledge/cs/contents/spring/x.md",
                            concept_id="spring/di", score=0.85)]
        out = personalization.apply_score_adjustments(
            cands,
            learner_context={"mastered_concepts": [{"id": "concept:spring/di"}]},
            enabled=False,
        )
        # Same list (or list-equal), scores unchanged
        self.assertEqual([(c.path, c.score) for c in out], [(c.path, c.score) for c in cands])


class NullContextTest(unittest.TestCase):
    def test_no_adjustments_when_learner_context_missing(self):
        adjustments = personalization.compute_score_adjustments(
            candidates=[_candidate("k/c/spring/x.md", concept_id="spring/di")],
            learner_context=None,
            enabled=True,
        )
        self.assertEqual(adjustments, {})

    def test_no_adjustments_when_no_mastered_no_weak(self):
        adjustments = personalization.compute_score_adjustments(
            candidates=[_candidate("k/c/spring/x.md", concept_id="spring/di")],
            learner_context={"mastered_concepts": [], "uncertain_concepts": []},
            enabled=True,
        )
        self.assertEqual(adjustments, {})


# ---------------------------------------------------------------------------
# Mastered demote
# ---------------------------------------------------------------------------

class MasteredDemoteTest(unittest.TestCase):
    def test_strips_concept_prefix_when_matching(self):
        adjustments = personalization.compute_score_adjustments(
            candidates=[_candidate("k/c/spring/di.md", concept_id="spring/di")],
            learner_context={
                "mastered_concepts": [{"id": "concept:spring/di"}],
            },
            enabled=True,
        )
        self.assertEqual(len(adjustments), 1)
        # Demote = negative adjustment
        self.assertLess(list(adjustments.values())[0], 0)

    def test_no_match_when_concept_id_missing_on_candidate(self):
        adjustments = personalization.compute_score_adjustments(
            candidates=[_candidate("k/c/spring/di.md")],  # no concept_id
            learner_context={
                "mastered_concepts": [{"id": "concept:spring/di"}],
            },
            enabled=True,
        )
        self.assertEqual(adjustments, {})

    def test_matches_nested_document_concept_id(self):
        adjustments = personalization.compute_score_adjustments(
            candidates=[
                _candidate_with_document_concept(
                    "k/c/spring/bean-di-basics.md",
                    concept_id="spring/bean-di-basics",
                )
            ],
            learner_context={
                "mastered_concepts": [{"id": "concept:spring/bean"}],
            },
            enabled=True,
        )

        self.assertEqual(len(adjustments), 1)
        self.assertLess(list(adjustments.values())[0], 0)

    def test_slug_family_match_does_not_match_partial_prefix_words(self):
        adjustments = personalization.compute_score_adjustments(
            candidates=[
                _candidate_with_document_concept(
                    "k/c/spring/dispatcher-servlet.md",
                    concept_id="spring/dispatcher-servlet",
                )
            ],
            learner_context={
                "mastered_concepts": [{"id": "concept:spring/di"}],
            },
            enabled=True,
        )

        self.assertEqual(adjustments, {})

    def test_apply_demotes_score(self):
        cands = [
            _candidate("k/c/spring/x.md", concept_id="spring/di", score=0.85),
            _candidate("k/c/spring/y.md", concept_id="spring/ioc", score=0.78),
        ]
        out = personalization.apply_score_adjustments(
            cands,
            learner_context={"mastered_concepts": [{"id": "concept:spring/di"}]},
            enabled=True,
            mastered_demote=0.20,
        )
        # Top-1 should now be ioc (0.78 unchanged) ahead of di (0.85 - 0.20 = 0.65)
        scores = {c.path: c.score for c in out}
        self.assertAlmostEqual(scores["k/c/spring/x.md"], 0.65, places=6)
        self.assertAlmostEqual(scores["k/c/spring/y.md"], 0.78, places=6)
        self.assertEqual(out[0].path, "k/c/spring/y.md")


# ---------------------------------------------------------------------------
# Uncertain / underexplored boost
# ---------------------------------------------------------------------------

class UncertainBoostTest(unittest.TestCase):
    def test_uncertain_concept_boosted(self):
        adjustments = personalization.compute_score_adjustments(
            candidates=[
                _candidate("k/c/spring/x.md", concept_id="spring/transaction",
                           score=0.5),
            ],
            learner_context={
                "uncertain_concepts": [
                    {"id": "concept:spring/transaction", "ask_count_7d": 5},
                ],
            },
            enabled=True,
        )
        # Boost = positive adjustment
        self.assertGreater(list(adjustments.values())[0], 0)

    def test_underexplored_concept_boosted(self):
        adjustments = personalization.compute_score_adjustments(
            candidates=[
                _candidate("k/c/spring/x.md", concept_id="spring/aop"),
            ],
            learner_context={
                "underexplored_in_current_stage": [
                    {"id": "concept:spring/aop", "reason": "no recent visits"},
                ],
            },
            enabled=True,
        )
        self.assertGreater(list(adjustments.values())[0], 0)


# ---------------------------------------------------------------------------
# R3Config flag
# ---------------------------------------------------------------------------

class R3ConfigPersonalizationFlagTest(unittest.TestCase):
    def test_default_off(self):
        from scripts.learning.rag.r3.config import R3Config
        import os
        from unittest import mock
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("WOOWA_RAG_PERSONALIZATION_ENABLED", None)
            self.assertFalse(R3Config.from_env().personalization_enabled)

    def test_env_on(self):
        from scripts.learning.rag.r3.config import R3Config
        import os
        from unittest import mock
        with mock.patch.dict(os.environ, {"WOOWA_RAG_PERSONALIZATION_ENABLED": "1"}):
            self.assertTrue(R3Config.from_env().personalization_enabled)


# ---------------------------------------------------------------------------
# Hit threading — _hit_from_candidate exposes concept_id
# ---------------------------------------------------------------------------

class HitConceptIdExposureTest(unittest.TestCase):
    def test_hit_includes_concept_id_when_metadata_has_it(self):
        from scripts.learning.rag.r3 import search as r3_search
        cand = _candidate("k/c/spring/x.md", concept_id="spring/di")
        hit = r3_search._hit_from_candidate(cand)
        self.assertEqual(hit.get("concept_id"), "spring/di")

    def test_hit_concept_id_none_when_metadata_missing(self):
        from scripts.learning.rag.r3 import search as r3_search
        cand = _candidate("k/c/spring/x.md")  # no concept_id
        hit = r3_search._hit_from_candidate(cand)
        self.assertIsNone(hit.get("concept_id"))

    def test_hit_uses_nested_document_concept_id(self):
        from scripts.learning.rag.r3 import search as r3_search
        cand = _candidate_with_document_concept(
            "k/c/spring/bean-di-basics.md",
            concept_id="spring/bean-di-basics",
        )
        hit = r3_search._hit_from_candidate(cand)
        self.assertEqual(hit.get("concept_id"), "spring/bean-di-basics")


if __name__ == "__main__":
    unittest.main()
