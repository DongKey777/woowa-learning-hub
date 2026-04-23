"""candidate_interpretation: learning_profile boost behavior."""

import unittest

from scripts.workbench.core.candidate_interpretation import (
    _profile_boost,
    _score_learning_points,
)


def _candidate(pr_number: int, title: str, excerpt: str) -> dict:
    return {
        "pr_number": pr_number,
        "title": title,
        "author_login": "crew",
        "score": 10,
        "focus_excerpt": excerpt,
        "matched_paths": ["src/main/java/board/Repository.java"],
        "matched_comment_samples": [
            {"body_excerpt": "repository 경계를 다시 봐야 합니다", "user_login": "mentor"}
        ],
        "matched_review_samples": [],
        "matched_issue_comment_samples": [],
        "path_examples": [],
    }


class ProfileBoostTest(unittest.TestCase):
    def test_no_profile_returns_zero(self) -> None:
        self.assertEqual(_profile_boost("repository_boundary", None), (0, []))

    def test_repeated_active_stacks(self) -> None:
        profile = {
            "repeated_learning_points": [
                {"learning_point": "repository_boundary", "recency_status": "active"}
            ]
        }
        boost, reasons = _profile_boost("repository_boundary", profile)
        self.assertEqual(boost, 5)
        self.assertIn("profile:repeated", reasons)
        self.assertIn("profile:active", reasons)

    def test_dominant_only(self) -> None:
        profile = {
            "dominant_learning_points": [
                {"learning_point": "db_modeling", "recency_status": "cooling"}
            ]
        }
        boost, reasons = _profile_boost("db_modeling", profile)
        self.assertEqual(boost, 2)
        self.assertEqual(reasons, ["profile:dominant"])

    def test_underexplored_gentle(self) -> None:
        profile = {
            "underexplored_learning_points": [{"learning_point": "testing_strategy"}]
        }
        boost, reasons = _profile_boost("testing_strategy", profile)
        self.assertEqual(boost, 1)
        self.assertEqual(reasons, ["profile:underexplored"])

    def test_repeated_wins_over_dominant(self) -> None:
        profile = {
            "repeated_learning_points": [
                {"learning_point": "repository_boundary", "recency_status": "dormant"}
            ],
            "dominant_learning_points": [
                {"learning_point": "repository_boundary", "recency_status": "active"}
            ],
        }
        boost, reasons = _profile_boost("repository_boundary", profile)
        # repeated branch taken, dormant → no active bonus
        self.assertEqual(boost, 3)
        self.assertEqual(reasons, ["profile:repeated"])


class ScoreLearningPointsTest(unittest.TestCase):
    def test_profile_boost_does_not_fabricate(self) -> None:
        # candidate has no repository_boundary signals at all
        empty_candidate = {
            "pr_number": 1,
            "title": "docs: readme tweak",
            "focus_excerpt": "just fixing typos",
            "matched_paths": [],
            "matched_comment_samples": [],
            "matched_review_samples": [],
            "matched_issue_comment_samples": [],
        }
        profile = {
            "repeated_learning_points": [
                {"learning_point": "repository_boundary", "recency_status": "active"}
            ]
        }
        scores = _score_learning_points(empty_candidate, learning_profile=profile)
        # no content match → boost cannot fabricate a learning point
        self.assertEqual(scores, [])

    def test_profile_boost_amplifies_existing_match(self) -> None:
        candidate = _candidate(10, "repository 경계 정리", "repository 책임 분리")
        plain = _score_learning_points(candidate)
        boosted = _score_learning_points(
            candidate,
            learning_profile={
                "repeated_learning_points": [
                    {"learning_point": "repository_boundary", "recency_status": "active"}
                ]
            },
        )
        plain_score = next(s["score"] for s in plain if s["id"] == "repository_boundary")
        boosted_score = next(
            s["score"] for s in boosted if s["id"] == "repository_boundary"
        )
        self.assertEqual(boosted_score - plain_score, 5)
        boosted_reasons = next(
            s["reasons"] for s in boosted if s["id"] == "repository_boundary"
        )
        self.assertIn("profile:repeated", boosted_reasons)
        self.assertIn("profile:active", boosted_reasons)


if __name__ == "__main__":
    unittest.main()
