from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from scripts.workbench.core import cognitive_trigger


class CognitiveTriggerTest(unittest.TestCase):
    def test_selector_is_pure_no_side_effect(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pending_path = Path(tmp) / "pending_triggers.json"
            with patch.object(cognitive_trigger, "_pending_triggers_path", return_value=pending_path):
                trigger = cognitive_trigger.select_cognitive_trigger(
                    profile={
                        "open_follow_up_queue": [
                            {"question": "DI를 다시 볼까?", "learning_points": ["dependency_injection"]}
                        ]
                    }
                )
            self.assertEqual(trigger["trigger_type"], "follow_up")
            self.assertFalse(pending_path.exists())

    def test_pending_drill_blocks_all_other_triggers(self) -> None:
        trigger = cognitive_trigger.select_cognitive_trigger(
            profile={"open_follow_up_queue": [{"question": "남은 질문"}]},
            drill_pending={"drill_session_id": "pending"},
        )
        self.assertEqual(trigger["trigger_type"], "none")
        self.assertIsNone(trigger["markdown"])

    def test_only_follow_up_active_in_commit_1(self) -> None:
        trigger = cognitive_trigger.select_cognitive_trigger(
            history=[{"event_type": "code_attempt"}],
            profile={"open_follow_up_queue": [{"question": "트랜잭션 경계 다시 볼까?"}]},
            drill_history=[{"total_score": 4}],
        )
        self.assertEqual(trigger["trigger_type"], "follow_up")
        self.assertIn("트랜잭션", trigger["markdown"])
        self.assertIn("follow_up", trigger["competed_against"])
        self.assertNotIn("self_assessment_due", trigger["competed_against"])
        self.assertNotIn("review_due", trigger["competed_against"])

    def test_no_trigger_when_follow_up_queue_empty(self) -> None:
        trigger = cognitive_trigger.select_cognitive_trigger(
            history=[{"event_type": "code_attempt"}],
            profile={"open_follow_up_queue": []},
            drill_history=[{"total_score": 4}],
        )
        self.assertEqual(trigger["trigger_type"], "none")

    def test_pending_trigger_atomic_write_and_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            pending_path = Path(tmp) / "pending_triggers.json"
            with patch.object(cognitive_trigger, "_pending_triggers_path", return_value=pending_path):
                cognitive_trigger.write_pending_triggers_atomic(
                    {"self_assessment": {"trigger_session_id": "abc"}}
                )
                pending = cognitive_trigger.load_pending_triggers()
        self.assertEqual(pending["self_assessment"]["trigger_session_id"], "abc")
        self.assertEqual(
            cognitive_trigger.match_pending_trigger(
                pending,
                "self_assessment",
                {"trigger_session_id": "abc"},
            ),
            "abc",
        )
        self.assertIsNone(
            cognitive_trigger.match_pending_trigger(
                pending,
                "self_assessment",
                {"trigger_session_id": "other"},
            )
        )

    def test_expire_stale_triggers_after_24h(self) -> None:
        now = datetime(2026, 5, 7, tzinfo=timezone.utc)
        pending = {
            "self_assessment": {
                "trigger_session_id": "old",
                "issued_at": (now - timedelta(hours=25)).isoformat(),
            },
            "follow_up": {
                "trigger_session_id": "fresh",
                "issued_at": (now - timedelta(hours=1)).isoformat(),
            },
        }
        out = cognitive_trigger.expire_stale_triggers(pending, now)
        self.assertNotIn("self_assessment", out)
        self.assertIn("follow_up", out)


if __name__ == "__main__":
    unittest.main()

