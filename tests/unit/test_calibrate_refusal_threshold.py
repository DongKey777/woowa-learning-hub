"""Unit tests for the refusal-threshold calibration helpers (Phase 9.3 Step A).

Live R3 calibration runs are end-to-end and require the index +
reranker — those aren't tested here. This module covers the pure
math: percentile summary, F1-at-threshold, F1-optimal sweep, and
the conservative recommendation rounding.
"""

from __future__ import annotations

import unittest

from scripts.learning.rag.r3.eval.calibrate_refusal_threshold import (
    _f1_at_threshold,
    _f1_optimal_threshold,
    _percentile,
    _round_recommendation,
    _summary,
)


class PercentileTest(unittest.TestCase):
    def test_p50_of_sorted_range(self):
        self.assertEqual(_percentile([1, 2, 3, 4, 5], 50), 3.0)

    def test_p0_min_p100_max(self):
        self.assertEqual(_percentile([1, 5, 9], 0), 1.0)
        self.assertEqual(_percentile([1, 5, 9], 100), 9.0)

    def test_unsorted_input(self):
        self.assertEqual(_percentile([5, 1, 3], 50), 3.0)

    def test_empty_returns_zero(self):
        self.assertEqual(_percentile([], 50), 0.0)


class SummaryTest(unittest.TestCase):
    def test_summary_carries_n_and_quantiles(self):
        s = _summary([0.1, 0.2, 0.3, 0.4, 0.5])
        self.assertEqual(s["n"], 5)
        self.assertEqual(s["min"], 0.1)
        self.assertEqual(s["max"], 0.5)
        self.assertAlmostEqual(s["p50"], 0.3, places=5)

    def test_empty_summary(self):
        self.assertEqual(_summary([])["n"], 0)


class F1AtThresholdTest(unittest.TestCase):
    """Negative class = `score < threshold` is the refusal target.

    `tp` = corpus_gap below threshold (correct refusal)
    `fp` = paraphrase below threshold (spurious refusal)
    `fn` = corpus_gap at/above threshold (silent_failure)
    """

    def test_perfect_separation_yields_f1_1(self):
        negatives = [-2.0, -1.5]
        positives = [1.0, 2.0]
        self.assertAlmostEqual(
            _f1_at_threshold(threshold=0.0, negatives=negatives, positives=positives),
            1.0,
        )

    def test_partial_overlap_yields_lower_f1(self):
        negatives = [-1.0, -0.5, 0.5]
        positives = [-0.5, 0.5, 1.0]
        f1 = _f1_at_threshold(threshold=0.0, negatives=negatives, positives=positives)
        # Some negatives below + some positives below → F1 < 1
        self.assertLess(f1, 1.0)
        self.assertGreater(f1, 0.0)

    def test_no_negatives_below_threshold_returns_zero(self):
        # All negatives are above threshold = 0 correct refusals
        negatives = [0.5, 1.0]
        positives = [-1.0, 2.0]
        self.assertEqual(
            _f1_at_threshold(threshold=0.0, negatives=negatives, positives=positives),
            0.0,
        )


class F1OptimalSweepTest(unittest.TestCase):
    def test_clean_separation_picks_a_boundary(self):
        negatives = [-2.0, -1.5, -1.0]
        positives = [1.0, 1.5, 2.0]
        threshold = _f1_optimal_threshold(negatives=negatives, positives=positives)
        # Threshold must lie between max negative and min positive
        self.assertGreater(threshold, -1.0 - 1e-9)
        self.assertLess(threshold, 1.0 + 1e-9)

    def test_overlap_picks_finite_threshold(self):
        negatives = [-1.0, -0.5, 0.0, 0.5]
        positives = [-0.25, 0.25, 1.0, 2.0]
        threshold = _f1_optimal_threshold(negatives=negatives, positives=positives)
        self.assertIsInstance(threshold, float)


class RoundRecommendationTest(unittest.TestCase):
    def test_rounds_down_to_nearest_005(self):
        self.assertEqual(_round_recommendation(0.487), 0.45)
        self.assertEqual(_round_recommendation(0.5), 0.5)
        self.assertEqual(_round_recommendation(0.499), 0.45)

    def test_handles_zero_and_negative(self):
        self.assertEqual(_round_recommendation(0.0), 0.0)
        self.assertEqual(_round_recommendation(-0.3), -0.3)


if __name__ == "__main__":
    unittest.main()
