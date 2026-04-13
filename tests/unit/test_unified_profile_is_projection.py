"""unified_profile must be rebuildable from profile.json fields.

This pins the source-of-truth rule in the plan (Phase 3.2):
profile.json is persisted truth, unified_profile is a derived projection.
"""

import unittest

from scripts.learning import profile_merge


class UnifiedProfileIsProjectionTest(unittest.TestCase):
    def test_coach_view_is_subset_of_profile(self) -> None:
        profile = {
            "confidence": "high",
            "dominant_learning_points": [
                {"label": "repository_boundary"},
                {"label": "api_boundary"},
            ],
            "repeated_learning_points": [{"label": "repository_boundary"}],
            "underexplored_learning_points": [{"label": "testing_strategy"}],
        }
        unified = profile_merge.unify(profile, drill_history=[])
        coach_view = unified["coach_view"]

        def _labels(points):
            return [p["label"] if isinstance(p, dict) else p for p in points]

        self.assertEqual(
            set(coach_view["dominant_points"]),
            set(_labels(profile["dominant_learning_points"])),
        )
        self.assertEqual(
            set(coach_view["repeated_points"]),
            set(_labels(profile["repeated_learning_points"])),
        )
        self.assertEqual(
            set(coach_view["underexplored_points"]),
            set(_labels(profile["underexplored_learning_points"])),
        )
        self.assertEqual(coach_view["confidence"], profile["confidence"])

    def test_unify_is_deterministic(self) -> None:
        profile = {
            "confidence": "medium",
            "dominant_learning_points": [{"label": "x"}],
            "repeated_learning_points": [{"label": "x"}],
        }
        history = [
            {
                "total_score": 7,
                "dimensions": {"accuracy": 3, "depth": 2, "practicality": 1, "completeness": 1},
                "weak_tags": ["실전성"],
                "source_doc": {"category": "database"},
            }
        ]
        a = profile_merge.unify(profile, drill_history=history)
        b = profile_merge.unify(profile, drill_history=history)
        self.assertEqual(a, b)

    def test_cs_view_is_derivable_from_drill_history(self) -> None:
        history = [
            {
                "total_score": 3,
                "dimensions": {"accuracy": 1, "depth": 1, "practicality": 0, "completeness": 1},
                "weak_tags": ["정확도"],
                "source_doc": {"category": "security"},
            }
        ]
        unified = profile_merge.unify({}, drill_history=history)
        direct = profile_merge.compute_cs_view(history)
        self.assertEqual(unified["cs_view"], direct)


if __name__ == "__main__":
    unittest.main()
