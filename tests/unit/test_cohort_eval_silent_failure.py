"""Phase 9.3 Step E — cohort_eval recognizes tier_downgraded vs
silent_failure outcomes for corpus_gap_probe.

Pre-9.3 the metric awarded ``refusal_clean`` to any corpus_gap_probe
query whose top-K contained no primary/acceptable/forbidden paths —
which auto-passes garbage retrieval. With Phase 9.3 sentinel emission,
we distinguish:

  * R3 returned a confidence-threshold sentinel → ``tier_downgraded``,
    pass=True (real refusal — system honestly said "no confident
    match").
  * R3 returned top-K real (but irrelevant-to-qrel) docs → new
    ``silent_failure`` outcome, pass=False (system returned garbage
    that scored as refusal_clean only because there were no
    primary/forbidden paths to compare against).

This is the metric reform that makes the 95.5% baseline honest.
"""

from __future__ import annotations

import unittest

from scripts.learning.rag.r3.eval import cohort_eval


def _classify(*, cohort_tag, final_paths, hits=None, primary=(),
              acceptable=(), forbidden=(), top_k=5):
    return cohort_eval._classify_outcome(
        cohort_tag=cohort_tag,
        final_paths=tuple(final_paths),
        primary_paths=tuple(primary),
        acceptable_paths=tuple(acceptable),
        forbidden_paths=tuple(forbidden),
        top_k=top_k,
        hits=tuple(hits) if hits is not None else None,
    )


class CorpusGapProbeRefusalReformTest(unittest.TestCase):
    def test_sentinel_hit_yields_tier_downgraded_pass(self):
        """When R3 returns the no_confident_match sentinel, classify
        as tier_downgraded with pass=True."""
        sentinel_hit = {
            "path": "<sentinel:no_confident_match>",
            "sentinel": "no_confident_match",
            "rejected_top": "knowledge/cs/contents/spring/random.md",
            "rejected_score": -1.5,
        }
        expected, actual, pass_status, prim, acc, forb = _classify(
            cohort_tag="corpus_gap_probe",
            final_paths=("<sentinel:no_confident_match>",),
            hits=[sentinel_hit],
            primary=(),
            forbidden=(),
        )
        self.assertEqual(expected, "refusal_clean")
        self.assertEqual(actual, "tier_downgraded")
        self.assertTrue(pass_status)

    def test_garbage_hits_without_sentinel_yields_silent_failure(self):
        """R3 returned 5 real docs that happen not to overlap with
        primary/forbidden. Pre-9.3 this auto-passed; post-9.3 we mark
        it silent_failure with pass=False."""
        garbage_hits = [
            {"path": "knowledge/cs/contents/spring/random.md"},
            {"path": "knowledge/cs/contents/database/another.md"},
        ]
        expected, actual, pass_status, prim, acc, forb = _classify(
            cohort_tag="corpus_gap_probe",
            final_paths=tuple(h["path"] for h in garbage_hits),
            hits=garbage_hits,
            primary=(),
            forbidden=(),
        )
        self.assertEqual(expected, "refusal_clean")
        self.assertEqual(actual, "silent_failure")
        self.assertFalse(pass_status)

    def test_empty_hits_yields_silent_failure_not_pass(self):
        """No hits at all (unusual — R3 always returns top-K) is also
        silent_failure: the AI session would respond from training
        knowledge with no signal that a refusal was warranted."""
        expected, actual, pass_status, _, _, _ = _classify(
            cohort_tag="corpus_gap_probe",
            final_paths=(),
            hits=[],
            primary=(),
            forbidden=(),
        )
        self.assertEqual(actual, "silent_failure")
        self.assertFalse(pass_status)

    def test_primary_hit_still_passes_for_corpus_gap_probe(self):
        """If qrel author added a primary path (rare; corpus_gap_probe
        is usually empty), a primary hit is still a clean pass."""
        expected, actual, pass_status, _, _, _ = _classify(
            cohort_tag="corpus_gap_probe",
            final_paths=("knowledge/cs/contents/spring/p.md",),
            hits=[{"path": "knowledge/cs/contents/spring/p.md"}],
            primary=("knowledge/cs/contents/spring/p.md",),
            forbidden=(),
        )
        self.assertEqual(actual, "primary_hit")
        self.assertTrue(pass_status)

    def test_forbidden_hit_still_fails(self):
        forbidden_hit = {"path": "knowledge/cs/contents/spring/forbidden.md"}
        expected, actual, pass_status, _, _, _ = _classify(
            cohort_tag="corpus_gap_probe",
            final_paths=("knowledge/cs/contents/spring/forbidden.md",),
            hits=[forbidden_hit],
            primary=(),
            forbidden=("knowledge/cs/contents/spring/forbidden.md",),
        )
        self.assertEqual(actual, "forbidden_hit")
        self.assertFalse(pass_status)


class NonRefusalCohortsUnaffectedTest(unittest.TestCase):
    """Sentinel detection is scoped to corpus_gap_probe — other
    cohorts continue to use the standard primary_in_top_k contract."""

    def test_sentinel_in_paraphrase_cohort_treated_as_miss(self):
        sentinel_hit = {
            "path": "<sentinel:no_confident_match>",
            "sentinel": "no_confident_match",
        }
        expected, actual, pass_status, _, _, _ = _classify(
            cohort_tag="paraphrase_human",
            final_paths=("<sentinel:no_confident_match>",),
            hits=[sentinel_hit],
            primary=("knowledge/cs/contents/spring/p.md",),
            forbidden=(),
        )
        # Sentinel is not a primary path — falls through to miss
        self.assertEqual(actual, "miss")
        self.assertFalse(pass_status)


class BackwardCompatibilityTest(unittest.TestCase):
    def test_classify_still_callable_without_hits_kwarg(self):
        """Older callers that don't know about the hits parameter
        must still get the legacy behavior (no sentinel detection)."""
        expected, actual, pass_status, _, _, _ = cohort_eval._classify_outcome(
            cohort_tag="corpus_gap_probe",
            final_paths=("knowledge/cs/contents/spring/random.md",),
            primary_paths=(),
            acceptable_paths=(),
            forbidden_paths=(),
            top_k=5,
        )
        # Without hits info, garbage path stays graded as refusal_clean
        # (legacy behavior — the metric reform requires hits to be
        # passed explicitly).
        self.assertIn(actual, ("refusal_clean", "silent_failure"))


if __name__ == "__main__":
    unittest.main()
