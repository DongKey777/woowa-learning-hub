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

    def test_drill_answer_mixed_when_mission_tokens_present(self) -> None:
        pending = {"question": "트랜잭션 격리 수준에서 phantom read 가 왜 발생해?"}
        # answer-shaped body that *also* mentions a PR → mixed_with_drill_answer
        prompt = (
            "phantom read 는 트랜잭션 격리 수준이 낮아 같은 쿼리 결과가 달라질 때 발생해. "
            "내 PR 리뷰에서도 그 맥락이 나와"
        )
        result = intent_router.pre_decide(prompt, pending_drill=pending)
        self.assertEqual(result["pre_intent"], intent_router.MIXED_WITH_DRILL_ANSWER)
        self.assertEqual(result["cs_search_mode"], "cheap")

    def test_drill_pending_but_question_shaped_falls_through(self) -> None:
        # pending exists but prompt is a short question → not a drill answer,
        # normal classification kicks in (CS tokens → CS_ONLY).
        pending = {"question": "repository boundary 가 왜 중요해?"}
        result = intent_router.pre_decide(
            "트랜잭션 격리가 뭐야?", pending_drill=pending
        )
        self.assertEqual(result["pre_intent"], intent_router.CS_ONLY)
        self.assertEqual(result["cs_search_mode"], "full")

    def test_empty_prompt_without_state_is_unknown(self) -> None:
        result = intent_router.pre_decide("")
        self.assertEqual(result["pre_intent"], intent_router.UNKNOWN)
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

    def test_mixed_plan_with_cs_hits_and_verification(self) -> None:
        pre = {"pre_intent": intent_router.MIXED, "cs_search_mode": "full", "signals": {}}
        augment = {"by_fallback_key": {"database:hikari": [{"path": "x"}]}}
        decision = intent_router.finalize(
            pre, augment_result=augment, verification_required_count=1
        )
        plan = decision["block_plan"]
        self.assertEqual(plan["snapshot_block"], "primary")
        self.assertEqual(plan["cs_block"], "supporting")
        self.assertEqual(plan["verification"], "supporting")

    def test_unknown_mirrors_mixed_plan(self) -> None:
        pre = {"pre_intent": intent_router.UNKNOWN, "cs_search_mode": "cheap", "signals": {}}
        decision = intent_router.finalize(pre)
        plan = decision["block_plan"]
        self.assertEqual(plan["snapshot_block"], "primary")
        self.assertEqual(plan["cs_block"], "omit")
        self.assertEqual(plan["verification"], "omit")

    def test_drill_answer_plan_prioritizes_drill_block(self) -> None:
        pre = {
            "pre_intent": intent_router.DRILL_ANSWER,
            "cs_search_mode": "cheap",
            "signals": {},
        }
        augment = {"by_learning_point": {"repository_boundary": [{"path": "x"}]}}
        decision = intent_router.finalize(
            pre,
            augment_result=augment,
            drill_result={"total_score": 7},
            verification_required_count=2,
        )
        plan = decision["block_plan"]
        self.assertEqual(plan["drill_block"], "primary")
        self.assertEqual(plan["snapshot_block"], "supporting")
        self.assertEqual(plan["cs_block"], "supporting")
        self.assertEqual(plan["verification"], "supporting")
        self.assertTrue(decision["drill_in_turn"]["has_result"])
        self.assertFalse(decision["drill_in_turn"]["has_offer"])

    def test_mixed_with_drill_answer_keeps_snapshot_primary(self) -> None:
        pre = {
            "pre_intent": intent_router.MIXED_WITH_DRILL_ANSWER,
            "cs_search_mode": "cheap",
            "signals": {},
        }
        decision = intent_router.finalize(pre)
        plan = decision["block_plan"]
        self.assertEqual(plan["snapshot_block"], "primary")
        self.assertEqual(plan["drill_block"], "supporting")

    def test_drill_offer_elevates_drill_block_on_mission_only(self) -> None:
        pre = {"pre_intent": intent_router.MISSION_ONLY, "cs_search_mode": "skip", "signals": {}}
        offer = {"drill_session_id": "d-new", "question": "?"}
        decision = intent_router.finalize(pre, drill_offer=offer)
        plan = decision["block_plan"]
        # base plan for mission_only leaves drill_block=omit; offer elevates.
        self.assertEqual(plan["drill_block"], "supporting")
        self.assertTrue(decision["drill_in_turn"]["has_offer"])

    def test_finalize_preserves_pre_signals_and_mode(self) -> None:
        pre = {
            "pre_intent": intent_router.MISSION_ONLY,
            "cs_search_mode": "skip",
            "signals": {"mission_score": 3, "cs_score": 0},
        }
        decision = intent_router.finalize(pre)
        self.assertEqual(decision["cs_search_mode"], "skip")
        self.assertEqual(decision["signals"]["mission_score"], 3)
        self.assertEqual(decision["detected_intent"], intent_router.MISSION_ONLY)


if __name__ == "__main__":
    unittest.main()
