"""Top-level coach-run.json size ladder test.

The ladder order mirrors the plan §Artifact Size Budget. Each step must
shrink only its own slice and must never touch load-bearing fields
(cs_block.markdown, snapshot_block.markdown, drill_block.markdown,
intent_decision, cs_readiness, execution_status).
"""

import unittest

from scripts.workbench.core import artifact_budget


def _base_payload() -> dict:
    return {
        "execution_status": "ready",
        "cs_readiness": {"state": "ready"},
        "intent_decision": {"detected_intent": "mixed"},
        "response_contract": {
            "snapshot_block": {"markdown": "## 상태 요약 (snapshot, computed_at=...)"},
            "cs_block": {"markdown": "## 이번 질문의 CS 근거\n- [database] path"},
            "drill_block": {"markdown": "## 확인 질문"},
        },
        "cs_augmentation": {
            "by_learning_point": {
                "repository_boundary": [
                    {"path": "x", "snippet_preview": "A" * 500},
                ],
            },
            "by_fallback_key": {
                "database:tx": [
                    {"path": f"doc-{i}", "snippet_preview": "B" * 500}
                    for i in range(6)
                ],
            },
        },
        "memory": {
            "profile": {
                "drill_history": [
                    {"total_score": i, "level": "L2", "weak_tags": ["깊이"], "junk": "Z" * 1000}
                    for i in range(10)
                ],
            },
        },
        "unified_profile": {
            "reconciled": {
                "priority_focus": [f"focus-{i}" for i in range(10)],
                "empirical_only_gaps": [f"e-{i}" for i in range(8)],
                "theoretical_only_gaps": [f"t-{i}" for i in range(9)],
            },
        },
    }


class EnforceBudgetTest(unittest.TestCase):
    def test_noop_when_under_budget(self) -> None:
        payload = {"execution_status": "ready"}
        out = artifact_budget.enforce_budget(payload, max_bytes=1_000_000)
        self.assertEqual(out, payload)

    def test_ladder_truncates_in_order(self) -> None:
        payload = _base_payload()
        # tight cap to force every step
        out = artifact_budget.enforce_budget(payload, max_bytes=1_500)

        # step 1: snippet previews truncated to 150
        lp_hit = out["cs_augmentation"]["by_learning_point"]["repository_boundary"][0]
        self.assertLessEqual(len(lp_hit["snippet_preview"]), 150)
        for hit in out["cs_augmentation"]["by_fallback_key"]["database:tx"]:
            self.assertLessEqual(len(hit["snippet_preview"]), 150)

        # step 2: drill_history trimmed to last 3, junk field gone
        history = out["memory"]["profile"]["drill_history"]
        self.assertEqual(len(history), 3)
        for entry in history:
            self.assertNotIn("junk", entry)

        # step 3: by_fallback_key top-K shrunk to 3
        self.assertEqual(len(out["cs_augmentation"]["by_fallback_key"]["database:tx"]), 3)

        # step 4: reconciled lists trimmed to 5
        reconciled = out["unified_profile"]["reconciled"]
        self.assertEqual(len(reconciled["priority_focus"]), 5)
        self.assertEqual(len(reconciled["empirical_only_gaps"]), 5)
        self.assertEqual(len(reconciled["theoretical_only_gaps"]), 5)

    def test_load_bearing_fields_never_shrunk(self) -> None:
        payload = _base_payload()
        out = artifact_budget.enforce_budget(payload, max_bytes=1_500)
        self.assertEqual(out["execution_status"], "ready")
        self.assertEqual(out["cs_readiness"], {"state": "ready"})
        self.assertEqual(out["intent_decision"], {"detected_intent": "mixed"})
        rc = out["response_contract"]
        self.assertTrue(rc["snapshot_block"]["markdown"].startswith("## 상태 요약"))
        self.assertTrue(rc["cs_block"]["markdown"].startswith("## 이번 질문의 CS 근거"))
        self.assertEqual(rc["drill_block"]["markdown"], "## 확인 질문")

    def test_original_payload_not_mutated(self) -> None:
        payload = _base_payload()
        before = payload["cs_augmentation"]["by_learning_point"]["repository_boundary"][0]["snippet_preview"]
        artifact_budget.enforce_budget(payload, max_bytes=1_500)
        after = payload["cs_augmentation"]["by_learning_point"]["repository_boundary"][0]["snippet_preview"]
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
