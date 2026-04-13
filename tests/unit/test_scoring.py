"""4-dimension scoring regression."""

import unittest

from scripts.learning import scoring


class ScoreAnswerTest(unittest.TestCase):
    def test_empty_answer_scores_zero(self) -> None:
        result = scoring.score_answer("트랜잭션이 뭐야?", "")
        self.assertEqual(result["total_score"], 0)
        self.assertEqual(result["level"], "L1")
        self.assertIn("정확도", result["weak_tags"])
        self.assertIn("완결성", result["weak_tags"])

    def test_dont_know_hits_completeness_penalty(self) -> None:
        result = scoring.score_answer(
            "Repository가 뭐야?",
            "잘 모르겠어요. 나중에 다시 볼게요.",
        )
        self.assertEqual(result["dimensions"]["completeness"], 0)

    def test_high_quality_answer_reaches_l4_plus(self) -> None:
        answer = (
            "Repository는 영속성 추상화라서 트랜잭션 경계를 몰라야 한다. "
            "왜냐하면 트랜잭션은 application layer의 책임이고, 내부적으로 "
            "aggregate root 단위의 invariant를 보장해야 하기 때문이다. "
            "실제로 운영 환경에서 타임아웃과 재시도 정책을 얹을 때 "
            "트랜잭션 경계와 도메인 경계가 섞여 있으면 롤백 전략이 꼬인다. "
            "예를 들면 결제 서비스에서 보상 트랜잭션을 돌릴 때..."
        )
        expected = [
            "repository", "트랜잭션", "경계", "영속성",
            "aggregate", "application",
        ]
        result = scoring.score_answer(
            "Repository가 트랜잭션을 알면 왜 안 돼?",
            answer,
            expected_terms=expected,
        )
        self.assertGreaterEqual(result["dimensions"]["accuracy"], 3)
        self.assertGreaterEqual(result["dimensions"]["depth"], 2)
        self.assertGreaterEqual(result["dimensions"]["practicality"], 1)
        self.assertEqual(result["dimensions"]["completeness"], 1)
        self.assertGreaterEqual(result["total_score"], 7)
        self.assertIn(result["level"], {"L4", "L5"})

    def test_partial_answer_flags_weak_dimensions(self) -> None:
        result = scoring.score_answer(
            "JWT 서명은 무엇을 보장해?",
            "서명은 무결성을 보장한다.",
        )
        self.assertLessEqual(result["total_score"], 4)
        self.assertIn("깊이", result["weak_tags"])
        self.assertIn("실전성", result["weak_tags"])
        self.assertTrue(result["improvement_notes"])

    def test_level_table_boundaries(self) -> None:
        # 직접 level_for 경로 커버 — total_score 계산이 아닌 함수 자체.
        self.assertEqual(scoring._level_for(10), "L5")
        self.assertEqual(scoring._level_for(9), "L5")
        self.assertEqual(scoring._level_for(7), "L4")
        self.assertEqual(scoring._level_for(5), "L3")
        self.assertEqual(scoring._level_for(3), "L2")
        self.assertEqual(scoring._level_for(0), "L1")


if __name__ == "__main__":
    unittest.main()
