"""Unit tests for the refusal-threshold calibration helpers (Phase 9.3 Step A).

Live R3 calibration runs are end-to-end and require the index +
reranker — those aren't tested here. This module covers the pure
math: percentile summary, F1-at-threshold, F1-optimal sweep, and
the conservative recommendation rounding.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest import mock

from scripts.learning.rag.r3.eval.calibrate_refusal_threshold import (
    CALIBRATION_ENV_DEFAULTS,
    NEGATIVE_COHORT,
    POSITIVE_COHORT,
    _env_snapshot,
    _f1_at_threshold,
    _f1_optimal_threshold,
    _format_threshold,
    _percentile,
    _require_full_score_coverage,
    _restore_env,
    _round_recommendation,
    _summary,
    _threshold_outcomes,
    calibrate,
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

    def test_equal_f1_tie_break_prefers_lower_threshold(self):
        negatives = [-1.0, 1.0, 1.5]
        positives = [-0.5, 0.0, 0.5]
        threshold = _f1_optimal_threshold(negatives=negatives, positives=positives)
        self.assertGreater(threshold, 1.5)

    def test_equal_f1_tie_break_still_prefers_lower_boundary(self):
        negatives = [-2.0, 0.0]
        positives = [-1.0, 0.0]
        threshold = _f1_optimal_threshold(negatives=negatives, positives=positives)
        self.assertEqual(threshold, -1.0)


class ThresholdOutcomesTest(unittest.TestCase):
    def test_outcomes_expose_refusal_tradeoff_counts(self):
        outcomes = _threshold_outcomes(
            threshold=0.5,
            negatives=[0.1, 0.6, 0.4],
            positives=[0.2, 0.7],
        )
        self.assertEqual(outcomes["correct_refusals"], 2)
        self.assertEqual(outcomes["silent_failures"], 1)
        self.assertEqual(outcomes["spurious_refusals"], 1)
        self.assertEqual(outcomes["preserved_answers"], 1)
        self.assertAlmostEqual(outcomes["negative_recall"], 2 / 3)
        self.assertAlmostEqual(outcomes["positive_preservation_rate"], 0.5)
        self.assertAlmostEqual(outcomes["negative_silent_failure_rate"], 1 / 3)
        self.assertAlmostEqual(outcomes["precision"], 2 / 3)


class RoundRecommendationTest(unittest.TestCase):
    def test_rounds_down_to_nearest_005(self):
        self.assertEqual(_round_recommendation(0.487), 0.45)
        self.assertEqual(_round_recommendation(0.5), 0.5)
        self.assertEqual(_round_recommendation(0.499), 0.45)

    def test_handles_zero_and_negative(self):
        self.assertEqual(_round_recommendation(0.0), 0.0)
        self.assertEqual(_round_recommendation(-0.3), -0.3)
        self.assertEqual(_round_recommendation(-0.26), -0.3)


class FormatThresholdTest(unittest.TestCase):
    def test_preserves_copy_paste_safe_two_decimal_env_value(self):
        self.assertEqual(_format_threshold(0.1), "0.10")
        self.assertEqual(_format_threshold(0.45), "0.45")
        self.assertEqual(_format_threshold(-0.3), "-0.30")


class EnvHelpersTest(unittest.TestCase):
    def test_restore_env_puts_original_values_back(self):
        with mock.patch.dict(os.environ, {"KEEP": "before"}, clear=True):
            snapshot = _env_snapshot(["KEEP", "DROP"])
            os.environ["KEEP"] = "after"
            os.environ["DROP"] = "temp"
            _restore_env(snapshot)
            self.assertEqual(os.environ["KEEP"], "before")
            self.assertNotIn("DROP", os.environ)

    def test_require_full_score_coverage_rejects_partial_scores(self):
        with self.assertRaisesRegex(RuntimeError, "full cohort coverage"):
            _require_full_score_coverage(
                queries=["q1", "q2"],
                scores=[0.1],
                cohort_name="corpus_gap_probe",
            )


class CalibrateContractTest(unittest.TestCase):
    def test_calibrate_reports_env_and_outcomes(self):
        original_threshold = os.environ.get("WOOWA_RAG_REFUSAL_THRESHOLD")
        query1 = mock.Mock(
            cohort_tag=NEGATIVE_COHORT,
            prompt="neg",
            reformulated_query="neg ref",
        )
        query2 = mock.Mock(
            cohort_tag=POSITIVE_COHORT,
            prompt="pos",
            reformulated_query="pos ref",
        )
        suite = mock.Mock(queries=[query1, query2])

        captured_env: list[dict[str, str | None]] = []

        def fake_search(prompt: str, **kwargs):
            captured_env.append(
                {
                    "threshold": os.environ.get("WOOWA_RAG_REFUSAL_THRESHOLD"),
                    "r3_enabled": os.environ.get("WOOWA_RAG_R3_ENABLED"),
                    "offline": os.environ.get("HF_HUB_OFFLINE"),
                    "reformulated_query": kwargs.get("reformulated_query"),
                }
            )
            if prompt == "neg":
                return [{"cross_encoder_score": 0.2}]
            return [{"cross_encoder_score": 0.8}]

        with (
            mock.patch(
                "scripts.learning.rag.r3.eval.calibrate_refusal_threshold.load_cohort_qrels",
                return_value=suite,
            ),
            mock.patch.dict(os.environ, {"WOOWA_RAG_REFUSAL_THRESHOLD": "0.9"}, clear=True),
        ):
            report = calibrate(
                qrels_path=Path("dummy.json"),
                search_fn=fake_search,
                top_k=5,
                use_reformulated_query=True,
            )

        self.assertEqual(captured_env[0]["threshold"], "off")
        self.assertEqual(
            captured_env[0]["r3_enabled"],
            CALIBRATION_ENV_DEFAULTS["WOOWA_RAG_R3_ENABLED"],
        )
        self.assertEqual(
            captured_env[0]["offline"],
            CALIBRATION_ENV_DEFAULTS["HF_HUB_OFFLINE"],
        )
        self.assertEqual(captured_env[0]["reformulated_query"], "neg ref")
        self.assertEqual(captured_env[1]["reformulated_query"], "pos ref")
        self.assertEqual(report["calibration_env_defaults"], CALIBRATION_ENV_DEFAULTS)
        self.assertEqual(
            report["calibration_env_applied"]["WOOWA_RAG_REFUSAL_THRESHOLD"],
            "off",
        )
        self.assertEqual(
            report["threshold_semantics"],
            "strict_less_than_preserves_equal_scores",
        )
        self.assertEqual(report["negative_query_count"], 1)
        self.assertEqual(report["positive_score_count"], 1)
        self.assertEqual(report["recommended_env_value"], "0.80")
        self.assertEqual(report["recommended_outcomes"]["preserved_answers"], 1)
        self.assertEqual(report["f1_optimal_outcomes"]["correct_refusals"], 1)
        self.assertIn("WOOWA_RAG_REFUSAL_THRESHOLD=0.80", report["report"])
        self.assertIn("0/1 still slip through as silent failures", report["report"])
        self.assertEqual(
            os.environ.get("WOOWA_RAG_REFUSAL_THRESHOLD"),
            original_threshold,
        )


if __name__ == "__main__":
    unittest.main()
