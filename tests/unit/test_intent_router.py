"""pre_decide + finalize branch coverage."""

import unittest

from scripts.workbench.core import intent_router


class PreDecideTest(unittest.TestCase):
    def test_mission_only_skips_cs_search(self) -> None:
        result = intent_router.pre_decide("내 PR #346 리뷰 스레드 어떻게 답해?")
        self.assertEqual(result["pre_intent"], intent_router.MISSION_ONLY)
        self.assertEqual(result["cs_search_mode"], "skip")

    def test_cs_only_runs_full_search(self) -> None:
        result = intent_router.pre_decide("트랜잭션 격리 수준이 뭐야? 개념 설명해줘")
        self.assertEqual(result["pre_intent"], intent_router.CS_ONLY)
        self.assertEqual(result["cs_search_mode"], "full")

    def test_mixed_runs_full_search(self) -> None:
        result = intent_router.pre_decide(
            "내 PR에서 트랜잭션 경계 왜 리뷰에서 지적받았지? 개념도 설명해줘"
        )
        self.assertEqual(result["pre_intent"], intent_router.MIXED)
        self.assertEqual(result["cs_search_mode"], "full")

    def test_unknown_without_signals(self) -> None:
        result = intent_router.pre_decide("음...")
        self.assertEqual(result["pre_intent"], intent_router.UNKNOWN)

    def test_unresolved_threads_nudge_mission_only(self) -> None:
        learner_state = {
            "target_pr_detail": {
                "threads": [
                    {"classification": "still-applies"},
                    {"classification": "ambiguous"},
                ]
            }
        }
        result = intent_router.pre_decide("그건 어떻게 되는 거지", learner_state=learner_state)
        # "어떻게" is a question keyword so would normally be UNKNOWN;
        # unresolved threads nudge mission.
        self.assertEqual(result["pre_intent"], intent_router.MISSION_ONLY)
        self.assertEqual(result["cs_search_mode"], "skip")

    def test_drill_answer_when_pending_and_conditions_met(self) -> None:
        pending = {
            "question": "트랜잭션 격리 수준에서 phantom read 가 왜 발생해?",
        }
        prompt = "phantom read 는 트랜잭션 격리 수준이 낮아 같은 쿼리 결과가 달라질 때 발생해"
        result = intent_router.pre_decide(prompt, pending_drill=pending)
        self.assertIn(
            result["pre_intent"],
            {intent_router.DRILL_ANSWER, intent_router.MIXED_WITH_DRILL_ANSWER},
        )
        self.assertEqual(result["cs_search_mode"], "cheap")


class FinalizeTest(unittest.TestCase):
    def test_mission_only_plan(self) -> None:
        pre = {"pre_intent": intent_router.MISSION_ONLY, "cs_search_mode": "skip", "signals": {}}
        decision = intent_router.finalize(pre, verification_required_count=2)
        plan = decision["block_plan"]
        self.assertEqual(plan["snapshot_block"], "primary")
        self.assertEqual(plan["cs_block"], "omit")
        self.assertEqual(plan["verification"], "primary")

    def test_cs_only_primary_when_hits_exist(self) -> None:
        pre = {"pre_intent": intent_router.CS_ONLY, "cs_search_mode": "full", "signals": {}}
        augment = {"by_learning_point": {"repository_boundary": [{"path": "x"}]}}
        decision = intent_router.finalize(pre, augment_result=augment)
        self.assertEqual(decision["block_plan"]["cs_block"], "primary")
        self.assertEqual(decision["block_plan"]["snapshot_block"], "omit")

    def test_cs_only_degrades_to_mission_when_no_hits(self) -> None:
        pre = {"pre_intent": intent_router.CS_ONLY, "cs_search_mode": "full", "signals": {}}
        decision = intent_router.finalize(pre, augment_result=None)
        self.assertEqual(decision["block_plan"]["cs_block"], "omit")
        self.assertEqual(decision["block_plan"]["snapshot_block"], "supporting")


if __name__ == "__main__":
    unittest.main()
