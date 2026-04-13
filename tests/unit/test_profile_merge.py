"""profile_merge.unify() + compute_cs_view() regression."""

import unittest

from scripts.learning import profile_merge


class ComputeCsViewTest(unittest.TestCase):
    def test_empty_history_returns_none(self) -> None:
        self.assertIsNone(profile_merge.compute_cs_view(None))
        self.assertIsNone(profile_merge.compute_cs_view([]))

    def test_weak_dimensions_and_categories(self) -> None:
        history = [
            {
                "total_score": 4,
                "dimensions": {"accuracy": 2, "depth": 1, "practicality": 0, "completeness": 1},
                "weak_tags": ["깊이", "실전성"],
                "source_doc": {"category": "database"},
            },
            {
                "total_score": 5,
                "dimensions": {"accuracy": 3, "depth": 1, "practicality": 0, "completeness": 1},
                "weak_tags": ["깊이"],
                "source_doc": {"category": "database"},
            },
        ]
        view = profile_merge.compute_cs_view(history)
        self.assertEqual(view["avg_score"], 4.5)
        self.assertEqual(view["level"], "L2")
        self.assertIn("depth", view["weak_dimensions"])
        self.assertIn("practicality", view["weak_dimensions"])
        self.assertIn("깊이", view["weak_tags"])
        self.assertEqual(view["low_categories"], ["database"])

    def test_high_scoring_history_has_no_weak_dims(self) -> None:
        history = [
            {
                "total_score": 10,
                "dimensions": {"accuracy": 4, "depth": 3, "practicality": 2, "completeness": 1},
                "source_doc": {"category": "database"},
            },
        ]
        view = profile_merge.compute_cs_view(history)
        self.assertEqual(view["weak_dimensions"], [])
        self.assertEqual(view["low_categories"], [])
        self.assertEqual(view["level"], "L5")


class UnifyTest(unittest.TestCase):
    def test_unify_without_drills_yields_cs_view_none(self) -> None:
        coach_profile = {
            "confidence": "medium",
            "dominant_learning_points": [{"label": "repository_boundary"}],
            "repeated_learning_points": [{"label": "repository_boundary"}],
            "underexplored_learning_points": [{"label": "testing_strategy"}],
        }
        unified = profile_merge.unify(coach_profile, drill_history=[])
        self.assertIsNone(unified["cs_view"])
        self.assertEqual(unified["coach_view"]["confidence"], "medium")
        self.assertIn("repository_boundary", unified["coach_view"]["repeated_points"])
        self.assertIn("repository_boundary", unified["reconciled"]["priority_focus"])

    def test_unify_with_drills_populates_cs_view(self) -> None:
        coach_profile = {
            "confidence": "low",
            "dominant_learning_points": ["api_boundary"],
            "repeated_learning_points": ["api_boundary"],
        }
        history = [
            {
                "total_score": 4,
                "dimensions": {"accuracy": 2, "depth": 1, "practicality": 0, "completeness": 1},
                "weak_tags": ["깊이"],
                "source_doc": {"category": "network"},
            }
        ]
        unified = profile_merge.unify(coach_profile, drill_history=history)
        self.assertIsNotNone(unified["cs_view"])
        self.assertIn("깊이", unified["cs_view"]["weak_tags"])
        self.assertIn("network", unified["cs_view"]["low_categories"])

    def test_unify_none_coach_profile(self) -> None:
        unified = profile_merge.unify(None, drill_history=[])
        self.assertEqual(unified["coach_view"]["dominant_points"], [])
        self.assertIsNone(unified["cs_view"])


if __name__ == "__main__":
    unittest.main()
