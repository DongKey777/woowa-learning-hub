"""Direct test of the coach_run.py learner-event hook.

We don't drive the full coach-run pipeline here (that's covered by
`test_coach_run_pipeline.py`). Instead, we replicate the success-path
hook in isolation: given a session_payload, exercise
`build_coach_run_event` + `append_learner_event` and confirm one event
lands with the expected concept_ids and pr_number.

Drill engine hook (`drill.append_history`) is exercised the same way.
"""

from __future__ import annotations

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

from core import concept_catalog, learner_memory  # noqa: E402

# `drill.append_history` imports `scripts.workbench.core.learner_memory`
# (the absolute-path form). When this test runs `from core import
# learner_memory`, sys.path makes that the same file but Python
# considers it a *different* module instance — so our `patch.object`
# calls below would only stamp one of the two. Force both names to
# point at the same module instance so a single round of patches
# covers the drill hook too.
import importlib  # noqa: E402
sys.modules.setdefault("scripts.workbench.core.learner_memory", learner_memory)


class _IsolatedDir(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tmp_root = Path(self.tmp.name)
        self.learner_dir = tmp_root / "learner"
        self.learner_dir.mkdir(parents=True, exist_ok=True)

        history = self.learner_dir / "history.jsonl"
        profile = self.learner_dir / "profile.json"
        summary = self.learner_dir / "summary.json"
        identity = self.learner_dir / "identity.json"
        self.history_path = history

        prev_env = os.environ.get("WOOWA_LEARNER_ID")
        os.environ["WOOWA_LEARNER_ID"] = "hook-tester"

        def _restore_env() -> None:
            if prev_env is None:
                os.environ.pop("WOOWA_LEARNER_ID", None)
            else:
                os.environ["WOOWA_LEARNER_ID"] = prev_env
        self.addCleanup(_restore_env)

        for p in [
            patch.object(learner_memory, "LEARNER_DIR", self.learner_dir),
            patch.object(learner_memory, "ensure_learner_layout", lambda: self.learner_dir),
            patch.object(learner_memory, "learner_history_path", lambda: history),
            patch.object(learner_memory, "learner_profile_path", lambda: profile),
            patch.object(learner_memory, "learner_summary_path", lambda: summary),
            patch.object(learner_memory, "learner_identity_path", lambda: identity),
        ]:
            p.start()
            self.addCleanup(p.stop)
        concept_catalog.reset_cache()

    def _events(self) -> list[dict]:
        if not self.history_path.exists():
            return []
        return [
            json.loads(line)
            for line in self.history_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


class CoachRunHookTests(_IsolatedDir):
    def test_coach_run_event_records_with_concept_ids(self) -> None:
        # The hook in coach_run.py reads exactly these fields from
        # session_payload and produces a coach_run event.
        from core.concept_catalog import load_catalog
        catalog = load_catalog()
        session_payload = {
            "repo": "spring-roomescape-admin",
            "current_pr": {"number": 14},
            "primary_learning_points": ["transaction_consistency"],
            "learning_point_recommendations": [
                {
                    "learning_point": "transaction_consistency",
                    "label": "트랜잭션",
                    "primary_candidate": {"pr_number": 100},
                }
            ],
            "review_state": "approved",
            "response": {
                "summary": ["요약"],
                "answer": ["본문"],
                "follow_up_question": "질문",
            },
        }
        event = learner_memory.build_coach_run_event(
            session_payload=session_payload,
            learner_id="hook-tester",
            catalog=catalog,
        )
        learner_memory.append_learner_event(event)
        events = self._events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "coach_run")
        self.assertEqual(events[0]["pr_number"], 14)
        self.assertIn("concept:spring/transactional", events[0]["concept_ids"])
        self.assertFalse(events[0]["had_negative_feedback"])

    def test_coach_run_event_negative_feedback_signal(self) -> None:
        from core.concept_catalog import load_catalog
        catalog = load_catalog()
        session_payload = {
            "repo": "x",
            "current_pr": {"number": 1},
            "primary_learning_points": ["transaction_consistency"],
            "review_state": "request_changes",
            "mentor_comment_samples": [{"body": "여기 트랜잭션 다시 봐주세요"}],
        }
        event = learner_memory.build_coach_run_event(
            session_payload=session_payload,
            learner_id="hook-tester",
            catalog=catalog,
        )
        learner_memory.append_learner_event(event)
        self.assertTrue(self._events()[0]["had_negative_feedback"])

    def test_module_context_inferred_from_profile_when_last_active_fresh(self) -> None:
        # Seed a recent rag_ask in spring-core-1, recompute profile, then
        # build a coach_run event that has no explicit module — expect it
        # to inherit spring-core-1 from profile.activity.current_module.
        from core.concept_catalog import load_catalog
        from datetime import datetime, timezone
        catalog = load_catalog()
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self.history_path.open("w", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "event_type": "rag_ask",
                "event_id": "r1",
                "ts": ts,
                "learner_id": "hook-tester",
                "repo_context": None,
                "module_context": "spring-core-1",
                "concept_ids": ["concept:spring/bean"],
                "prompt": "Bean이 뭐야",
                "tier": 1,
                "rag_mode": "cheap",
                "blocked": False,
            }) + "\n")
        learner_memory.recompute_learner_profile()
        event = learner_memory.build_coach_run_event(
            session_payload={
                "repo": "spring-core-1",
                "primary_learning_points": ["transaction_consistency"],
            },
            learner_id="hook-tester",
            catalog=catalog,
        )
        self.assertEqual(event["module_context"], "spring-core-1")

    def test_module_context_skipped_when_profile_last_active_stale(self) -> None:
        # Profile says current_module=spring-core-1 but last_active is 5 days
        # ago — _detect_current_module must NOT use it. With no other recent
        # event either, module_context falls through to None.
        from core.concept_catalog import load_catalog
        from datetime import datetime, timedelta, timezone
        catalog = load_catalog()
        old_ts = (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(timespec="seconds")
        with self.history_path.open("w", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "event_type": "rag_ask",
                "event_id": "r-old",
                "ts": old_ts,
                "learner_id": "hook-tester",
                "repo_context": None,
                "module_context": "spring-core-1",
                "concept_ids": ["concept:spring/bean"],
                "prompt": "Bean이 뭐야",
                "tier": 1,
                "rag_mode": "cheap",
                "blocked": False,
            }) + "\n")
        learner_memory.recompute_learner_profile()
        event = learner_memory.build_coach_run_event(
            session_payload={
                "repo": "spring-core-1",
                "primary_learning_points": ["transaction_consistency"],
            },
            learner_id="hook-tester",
            catalog=catalog,
        )
        self.assertIsNone(event["module_context"])

    def test_module_context_explicit_payload_field_wins(self) -> None:
        # When the caller explicitly passes a module, that overrides
        # profile/history inference.
        from core.concept_catalog import load_catalog
        catalog = load_catalog()
        event = learner_memory.build_coach_run_event(
            session_payload={
                "repo": "spring-core-1",
                "module": "spring-jdbc-2",
                "primary_learning_points": ["transaction_consistency"],
            },
            learner_id="hook-tester",
            catalog=catalog,
        )
        self.assertEqual(event["module_context"], "spring-jdbc-2")

    def test_module_context_none_when_history_empty(self) -> None:
        from core.concept_catalog import load_catalog
        catalog = load_catalog()
        event = learner_memory.build_coach_run_event(
            session_payload={
                "repo": "spring-core-1",
                "primary_learning_points": ["transaction_consistency"],
            },
            learner_id="hook-tester",
            catalog=catalog,
        )
        self.assertIsNone(event["module_context"])


class DrillHookTests(_IsolatedDir):
    def test_drill_append_history_records_learner_event(self) -> None:
        # Use a stubbed `_history_path` so drill.append_history writes
        # only to a temp dir; the *learner* hook should still fire.
        from scripts.learning import drill as drill_module
        with tempfile.TemporaryDirectory() as repo_state:
            repo_state_path = Path(repo_state)
            with patch.object(
                drill_module, "_history_path",
                lambda repo_name: repo_state_path / f"{repo_name}-drill-history.jsonl",
            ):
                drill_module.append_history(
                    "spring-roomescape-admin",
                    {
                        "drill_session_id": "d-1",
                        "scored_at": "2026-04-27T15:00:00+00:00",
                        "linked_learning_point": "transaction_consistency",
                        "question": "?",
                        "answer": "...",
                        "total_score": 8,
                        "level": "L4",
                        "dimensions": {"accuracy": 8},
                        "weak_tags": [],
                        "improvement_notes": [],
                        "source_doc": None,
                    },
                )
        events = self._events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "drill_answer")
        self.assertEqual(events[0]["total_score"], 8)
        self.assertIn("concept:spring/transactional", events[0]["concept_ids"])


if __name__ == "__main__":
    unittest.main()
