"""response_contract.build_follow_up_block + coach_run surface."""

import unittest

from scripts.workbench.core.response_contract import (
    build_follow_up_block,
    build_response_contract,
)


class FollowUpBlockTest(unittest.TestCase):
    def test_no_profile_empty(self) -> None:
        block = build_follow_up_block(None)
        self.assertIsNone(block["markdown"])
        self.assertEqual(block["items"], [])
        self.assertEqual(block["reason"], "none")

    def test_empty_queue(self) -> None:
        block = build_follow_up_block({"open_follow_up_queue": []})
        self.assertEqual(block["reason"], "none")

    def test_renders_questions_with_date_and_points(self) -> None:
        profile = {
            "open_follow_up_queue": [
                {
                    "question": "JPA 영속성 컨텍스트가 왜 필요해?",
                    "created_at": "2026-04-10T12:00:00+00:00",
                    "prompt": "지금 JPA 도입하면 어디까지 바꿔야 할까?",
                    "learning_points": ["db_modeling", "reconstruction_mapping"],
                },
                {
                    "question": "트랜잭션 경계는 어디까지 service가 잡아야 해?",
                    "created_at": "2026-04-08T09:00:00+00:00",
                    "learning_points": ["transaction_consistency"],
                },
            ]
        }
        block = build_follow_up_block(profile)
        self.assertEqual(block["reason"], "ready")
        self.assertEqual(len(block["items"]), 2)
        md = block["markdown"]
        self.assertIn("## 지난 턴 후속 질문", md)
        self.assertIn("JPA 영속성 컨텍스트가 왜 필요해?", md)
        self.assertIn("from 2026-04-10", md)
        self.assertIn("db_modeling, reconstruction_mapping", md)
        self.assertIn("트랜잭션 경계는 어디까지", md)

    def test_skips_blank_questions(self) -> None:
        profile = {
            "open_follow_up_queue": [
                {"question": "   ", "created_at": "2026-04-10"},
                {"question": "진짜 질문", "created_at": "2026-04-10"},
            ]
        }
        block = build_follow_up_block(profile)
        self.assertEqual(len(block["items"]), 1)

    def test_response_contract_includes_follow_up_block(self) -> None:
        contract = build_response_contract(
            None,
            "ready",
            learning_profile={
                "open_follow_up_queue": [
                    {"question": "왜 Hikari 풀 크기가 중요해?", "created_at": "2026-04-11"}
                ]
            },
        )
        self.assertIn("follow_up_block", contract)
        self.assertEqual(contract["follow_up_block"]["reason"], "ready")
        self.assertIn("Hikari", contract["follow_up_block"]["markdown"])

    def test_response_contract_empty_when_no_profile(self) -> None:
        contract = build_response_contract(None, "ready")
        self.assertEqual(contract["follow_up_block"]["reason"], "none")
        self.assertIsNone(contract["follow_up_block"]["markdown"])


if __name__ == "__main__":
    unittest.main()
