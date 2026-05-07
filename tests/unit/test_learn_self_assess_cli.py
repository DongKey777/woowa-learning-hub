"""learn-self-assess CLI regression tests."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
WORKBENCH_DIR = ROOT / "scripts" / "workbench"
if str(WORKBENCH_DIR) not in sys.path:
    sys.path.insert(0, str(WORKBENCH_DIR))

import cli as workbench_cli  # noqa: E402
from core import cognitive_trigger, learner_memory  # noqa: E402


class _SelfAssessmentIsolated(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tmp_root = Path(self.tmp.name)
        self.learner_dir = tmp_root / "learner"
        self.learner_dir.mkdir(parents=True, exist_ok=True)
        self.history_path = self.learner_dir / "history.jsonl"
        self.profile_path = self.learner_dir / "profile.json"
        self.summary_path = self.learner_dir / "summary.json"
        self.identity_path = self.learner_dir / "identity.json"
        self.pending_triggers_path = self.learner_dir / "pending_triggers.json"

        prev_env = os.environ.get("WOOWA_LEARNER_ID")
        os.environ["WOOWA_LEARNER_ID"] = "self-assess-tester"

        def _restore_env() -> None:
            if prev_env is None:
                os.environ.pop("WOOWA_LEARNER_ID", None)
            else:
                os.environ["WOOWA_LEARNER_ID"] = prev_env
        self.addCleanup(_restore_env)

        for p in [
            patch.object(learner_memory, "LEARNER_DIR", self.learner_dir),
            patch.object(learner_memory, "ensure_learner_layout", lambda: self.learner_dir),
            patch.object(learner_memory, "learner_history_path", lambda: self.history_path),
            patch.object(learner_memory, "learner_profile_path", lambda: self.profile_path),
            patch.object(learner_memory, "learner_summary_path", lambda: self.summary_path),
            patch.object(learner_memory, "learner_identity_path", lambda: self.identity_path),
            patch.object(
                cognitive_trigger,
                "_pending_triggers_path",
                lambda: self.pending_triggers_path,
            ),
        ]:
            p.start()
            self.addCleanup(p.stop)

    def _events(self) -> list[dict]:
        if not self.history_path.exists():
            return []
        return [
            json.loads(line)
            for line in self.history_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def _write_pending(self, trigger_session_id: str = "sa-1") -> None:
        self.pending_triggers_path.write_text(
            json.dumps(
                {
                    "self_assessment": {
                        "trigger_session_id": trigger_session_id,
                        "payload": {"concept_ids": ["concept:spring/transactional"]},
                    }
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )


class LearnSelfAssessCliTest(_SelfAssessmentIsolated):
    def test_self_assessment_event_appended_and_pending_trigger_cleared(self) -> None:
        self._write_pending("sa-1")
        ns = argparse.Namespace(
            response="8점이고 막힌 데는 트랜잭션 경계야",
            trigger_session_id="sa-1",
            silent=True,
        )

        rc = workbench_cli.cmd_learn_self_assess(ns)

        self.assertEqual(rc, 0)
        events = self._events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "self_assessment")
        self.assertEqual(events[0]["score"], 8)
        self.assertEqual(events[0]["trigger_session_id"], "sa-1")
        self.assertEqual(events[0]["concept_ids"], ["concept:spring/transactional"])

        pending = json.loads(self.pending_triggers_path.read_text(encoding="utf-8"))
        self.assertNotIn("self_assessment", pending)

    def test_self_assessment_rejected_without_pending_trigger(self) -> None:
        ns = argparse.Namespace(
            response="8점이야",
            trigger_session_id="sa-missing",
            silent=True,
        )

        rc = workbench_cli.cmd_learn_self_assess(ns)

        self.assertEqual(rc, 2)
        self.assertEqual(self._events(), [])
        self.assertFalse(self.pending_triggers_path.exists())


if __name__ == "__main__":
    unittest.main()
