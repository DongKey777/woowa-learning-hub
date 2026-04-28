"""Tests for `bin/reclassify-history` (cli.cmd_reclassify_history).

The CLI backfills two fields:

  * ``rag_ask.tier`` — re-running the current router with
    ``learner_profile=None`` (deliberately prompt-only so we don't apply
    today's profile to past prompts).
  * ``test_result.concept_match_mode`` — running ``infer_concepts_from_test``
    again to fill in strict/fallback/none on events that pre-date the field.

Guards: ``--dry-run`` leaves the file untouched, the rewrite creates a
``.bak`` backup, and the rewrite is idempotent (running twice produces
no further changes).
"""

from __future__ import annotations

import importlib
import json
import os
import sys
import tempfile
import unittest
from argparse import Namespace
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
WORKBENCH_DIR = ROOT / "scripts" / "workbench"
if str(WORKBENCH_DIR) not in sys.path:
    sys.path.insert(0, str(WORKBENCH_DIR))

from core import concept_catalog, learner_memory  # noqa: E402


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class _IsolatedDir(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.learner_dir = Path(self.tmp.name) / "learner"
        self.learner_dir.mkdir(parents=True, exist_ok=True)

        self.history_path = self.learner_dir / "history.jsonl"
        profile = self.learner_dir / "profile.json"
        summary = self.learner_dir / "summary.json"
        identity = self.learner_dir / "identity.json"

        prev_env = os.environ.get("WOOWA_LEARNER_ID")
        os.environ["WOOWA_LEARNER_ID"] = "rc-tester"

        def _restore_env() -> None:
            if prev_env is None:
                os.environ.pop("WOOWA_LEARNER_ID", None)
            else:
                os.environ["WOOWA_LEARNER_ID"] = prev_env

        self.addCleanup(_restore_env)

        for p in [
            patch.object(learner_memory, "LEARNER_DIR", self.learner_dir),
            patch.object(learner_memory, "ensure_learner_layout", lambda: self.learner_dir),
            patch.object(
                learner_memory, "learner_history_path", lambda: self.history_path
            ),
            patch.object(learner_memory, "learner_profile_path", lambda: profile),
            patch.object(learner_memory, "learner_summary_path", lambda: summary),
            patch.object(learner_memory, "learner_identity_path", lambda: identity),
        ]:
            p.start()
            self.addCleanup(p.stop)
        concept_catalog.reset_cache()

    def _seed(self, events: list[dict]) -> None:
        with self.history_path.open("w", encoding="utf-8") as fh:
            for ev in events:
                fh.write(json.dumps(ev, ensure_ascii=False) + "\n")

    def _read_events(self) -> list[dict]:
        return [
            json.loads(line)
            for line in self.history_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


class ReclassifyTests(_IsolatedDir):
    def _cmd(self):
        cli_mod = importlib.import_module("cli")
        return cli_mod.cmd_reclassify_history

    def test_dry_run_does_not_modify_file(self) -> None:
        # Old rag_ask events with stale tier=0; current router classifies them
        # higher (these prompts hit known concept aliases).
        events = [
            {
                "event_type": "rag_ask",
                "event_id": "r1",
                "ts": _now(),
                "learner_id": "rc-tester",
                "module_context": "spring-core-1",
                "concept_ids": ["concept:spring/bean"],
                "prompt": "Spring Bean이 뭐야",
                "tier": 0,
                "rag_mode": None,
                "blocked": False,
            },
        ]
        self._seed(events)
        before = self.history_path.read_text(encoding="utf-8")
        rc = self._cmd()(Namespace(dry_run=True))
        self.assertEqual(rc, 0)
        after = self.history_path.read_text(encoding="utf-8")
        self.assertEqual(before, after)
        self.assertFalse(self.history_path.with_suffix(".jsonl.bak").exists())

    def test_rewrite_updates_rag_ask_tier_and_creates_backup(self) -> None:
        events = [
            {
                "event_type": "rag_ask",
                "event_id": "r1",
                "ts": _now(),
                "learner_id": "rc-tester",
                "module_context": "spring-core-1",
                "concept_ids": ["concept:spring/bean"],
                "prompt": "Spring Bean이 뭐야",
                "tier": 0,  # stale
                "rag_mode": None,
                "blocked": False,
            },
        ]
        self._seed(events)
        rc = self._cmd()(Namespace(dry_run=False))
        self.assertEqual(rc, 0)
        backup = self.history_path.with_suffix(".jsonl.bak")
        self.assertTrue(backup.exists())
        rewritten = self._read_events()
        self.assertNotEqual(rewritten[0]["tier"], 0)

    def test_test_result_backfills_concept_match_mode(self) -> None:
        # Pre-existing test_result event without concept_match_mode field.
        events = [
            {
                "event_type": "test_result",
                "event_id": "t1",
                "ts": _now(),
                "learner_id": "rc-tester",
                "module_context": "spring-core-1",
                "concept_ids": ["concept:spring/bean"],
                "module": "spring-core-1",
                "test_class": "cholog.Bean",  # word-boundary match → strict
                "test_method": "register",
                "pass": True,
            },
        ]
        self._seed(events)
        rc = self._cmd()(Namespace(dry_run=False))
        self.assertEqual(rc, 0)
        rewritten = self._read_events()
        self.assertEqual(rewritten[0]["concept_match_mode"], "strict")

    def test_non_rag_ask_events_preserved(self) -> None:
        events = [
            {
                "event_type": "drill_answer",
                "event_id": "d1",
                "ts": _now(),
                "learner_id": "rc-tester",
                "concept_ids": ["concept:spring/bean"],
                "drill_session_id": "s1",
                "linked_learning_point": "x",
                "total_score": 8,
                "dimensions": {},
                "weak_tags": [],
            },
        ]
        self._seed(events)
        rc = self._cmd()(Namespace(dry_run=False))
        self.assertEqual(rc, 0)
        rewritten = self._read_events()
        # Drill event should be unchanged.
        self.assertEqual(rewritten[0]["event_type"], "drill_answer")
        self.assertEqual(rewritten[0]["total_score"], 8)

    def test_idempotent_second_run_makes_no_changes(self) -> None:
        events = [
            {
                "event_type": "rag_ask",
                "event_id": "r1",
                "ts": _now(),
                "learner_id": "rc-tester",
                "module_context": "spring-core-1",
                "concept_ids": ["concept:spring/bean"],
                "prompt": "Spring Bean이 뭐야",
                "tier": 0,
                "rag_mode": None,
                "blocked": False,
            },
        ]
        self._seed(events)
        cmd = self._cmd()
        cmd(Namespace(dry_run=False))
        first_pass = self.history_path.read_text(encoding="utf-8")
        cmd(Namespace(dry_run=False))
        second_pass = self.history_path.read_text(encoding="utf-8")
        # Second run reaches the steady-state — bytes match.
        self.assertEqual(first_pass, second_pass)

    def test_empty_history_returns_no_op(self) -> None:
        # No file at all
        rc = self._cmd()(Namespace(dry_run=False))
        self.assertEqual(rc, 0)
        # Now an empty file
        self.history_path.write_text("", encoding="utf-8")
        rc = self._cmd()(Namespace(dry_run=False))
        self.assertEqual(rc, 0)


if __name__ == "__main__":
    unittest.main()
