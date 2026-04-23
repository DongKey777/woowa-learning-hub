"""memory._confidence_level + _build_profile drill-score integration."""

import unittest

from scripts.workbench.core.memory import (
    _build_profile,
    _confidence_level,
    _shift_level,
)


class ConfidenceLevelTest(unittest.TestCase):
    def test_count_only(self) -> None:
        self.assertEqual(_confidence_level(4, 0.0), "high")
        self.assertEqual(_confidence_level(2, 0.0), "medium")
        self.assertEqual(_confidence_level(1, 0.0), "low")

    def test_strong_drill_score_promotes(self) -> None:
        self.assertEqual(_confidence_level(1, 0.0, avg_drill_score=8.5), "medium")
        self.assertEqual(_confidence_level(2, 0.0, avg_drill_score=8.5), "high")
        # already at top, stays high
        self.assertEqual(_confidence_level(5, 4.0, avg_drill_score=9.5), "high")

    def test_weak_drill_score_demotes(self) -> None:
        self.assertEqual(_confidence_level(4, 3.0, avg_drill_score=3.0), "medium")
        self.assertEqual(_confidence_level(2, 1.5, avg_drill_score=3.0), "low")
        # already at bottom, stays low
        self.assertEqual(_confidence_level(1, 0.0, avg_drill_score=2.0), "low")

    def test_mid_drill_score_no_shift(self) -> None:
        self.assertEqual(_confidence_level(2, 1.5, avg_drill_score=6.0), "medium")

    def test_shift_level_clamps(self) -> None:
        self.assertEqual(_shift_level("low", -1), "low")
        self.assertEqual(_shift_level("high", +1), "high")
        self.assertEqual(_shift_level("medium", +1), "high")
        self.assertEqual(_shift_level("medium", -1), "low")


class BuildProfileDrillScoreTest(unittest.TestCase):
    def _summary_with_medium_confidence(self) -> dict:
        return {
            "total_sessions": 3,
            "top_topics": [],
            "top_intents": [],
            "top_learning_points": [
                {
                    "learning_point": "repository_boundary",
                    "count": 2,
                    "weighted_count": 1.5,
                    "confidence": "medium",
                }
            ],
            "repeated_learning_points": [
                {
                    "learning_point": "repository_boundary",
                    "count": 2,
                    "weighted_count": 1.5,
                    "confidence": "medium",
                }
            ],
            "learning_point_confidence": [
                {
                    "learning_point": "repository_boundary",
                    "count": 2,
                    "weighted_count": 1.5,
                    "confidence": "medium",
                }
            ],
            "weighted_learning_points": [],
            "repeated_question_patterns": [],
        }

    def test_strong_drill_promotes_global_confidence(self) -> None:
        profile = _build_profile(
            "repo-x",
            self._summary_with_medium_confidence(),
            entries=[],
            avg_drill_score=8.0,
        )
        self.assertEqual(profile["confidence"], "high")

    def test_weak_drill_demotes_global_confidence(self) -> None:
        profile = _build_profile(
            "repo-x",
            self._summary_with_medium_confidence(),
            entries=[],
            avg_drill_score=4.0,
        )
        self.assertEqual(profile["confidence"], "low")

    def test_no_drill_score_leaves_confidence_alone(self) -> None:
        profile = _build_profile(
            "repo-x", self._summary_with_medium_confidence(), entries=[]
        )
        self.assertEqual(profile["confidence"], "medium")


if __name__ == "__main__":
    unittest.main()
