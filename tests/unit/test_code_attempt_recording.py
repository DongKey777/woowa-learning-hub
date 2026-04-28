"""Tests for the AI auto-invocation contract on code review.

The Code Attempt Recording rule lives in AGENTS.md / CLAUDE.md / GEMINI.md
and is paired with `bin/learn-record-code` + the CLI handler. These tests
guard:

* The `--silent` flag suppresses stdout but still records the event.
* The three AI files contain the operational rule with all required keywords
  (so a learner running on any of the three has the same auto-recording).
* A recorded code_attempt with a `linked_test` is recognized by the
  `_code_attempt_with_passing_test` mastery signal in `learner_memory.py`
  when there's a corresponding test_result.pass=True.

The "render path" is end-to-end here: AGENTS rule → `bin` wrapper →
CLI handler → history.jsonl → recompute_learner_profile() → mastered.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
WORKBENCH_DIR = ROOT / "scripts" / "workbench"
if str(WORKBENCH_DIR) not in sys.path:
    sys.path.insert(0, str(WORKBENCH_DIR))

from core import concept_catalog, learner_memory  # noqa: E402


REQUIRED_AI_FILE_KEYWORDS = [
    "Code Attempt Recording",
    "bin/learn-record-code --silent",
    "Write/Edit tool",
    "명시적으로 파일 경로",
    "linked-test",
    "학습자가 외울 명령 = 0",
]


class AIFileContractTests(unittest.TestCase):
    """The operational rule must appear in all three AI start-of-session files
    and carry the same trigger conditions.
    """

    def _read(self, name: str) -> str:
        return (ROOT / name).read_text(encoding="utf-8")

    def test_agents_md_has_code_attempt_section(self) -> None:
        text = self._read("AGENTS.md")
        for keyword in REQUIRED_AI_FILE_KEYWORDS:
            self.assertIn(keyword, text, f"AGENTS.md missing keyword: {keyword!r}")

    def test_claude_md_has_code_attempt_section(self) -> None:
        text = self._read("CLAUDE.md")
        for keyword in REQUIRED_AI_FILE_KEYWORDS:
            self.assertIn(keyword, text, f"CLAUDE.md missing keyword: {keyword!r}")

    def test_gemini_md_has_code_attempt_section(self) -> None:
        text = self._read("GEMINI.md")
        for keyword in REQUIRED_AI_FILE_KEYWORDS:
            self.assertIn(keyword, text, f"GEMINI.md missing keyword: {keyword!r}")


class _IsolatedDir(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.learner_dir = Path(self.tmp.name) / "learner"
        self.learner_dir.mkdir(parents=True, exist_ok=True)

        history = self.learner_dir / "history.jsonl"
        profile = self.learner_dir / "profile.json"
        summary = self.learner_dir / "summary.json"
        identity = self.learner_dir / "identity.json"
        self.history_path = history

        prev_env = os.environ.get("WOOWA_LEARNER_ID")
        os.environ["WOOWA_LEARNER_ID"] = "ca-tester"

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


class SilentFlagTests(_IsolatedDir):
    """Exercise `cmd_learn_record_code` directly so disk patches apply.

    A subprocess test would bypass the in-process patches that redirect
    LEARNER_DIR to the tempdir.
    """

    def _make_args(self, **overrides):
        from argparse import Namespace
        defaults = dict(
            file_path="missions/spring-learning-test/spring-core-1/initial/Bean.java",
            summary="Bean 등록 로직 추가",
            lines_added=12,
            lines_removed=3,
            linked_test=None,
            module=None,
            silent=False,
        )
        defaults.update(overrides)
        return Namespace(**defaults)

    def test_silent_suppresses_stdout_but_records_event(self) -> None:
        import importlib
        cli_mod = importlib.import_module("cli")
        cmd_learn_record_code = cli_mod.cmd_learn_record_code
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cmd_learn_record_code(self._make_args(silent=True))
        self.assertEqual(rc, 0)
        self.assertEqual(buf.getvalue().strip(), "")
        events = [
            json.loads(line)
            for line in self.history_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "code_attempt")
        self.assertIn("concept:spring/bean", events[0]["concept_ids"])

    def test_default_prints_event_id(self) -> None:
        import importlib
        cli_mod = importlib.import_module("cli")
        cmd_learn_record_code = cli_mod.cmd_learn_record_code
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = cmd_learn_record_code(self._make_args(silent=False))
        self.assertEqual(rc, 0)
        self.assertIn("recorded", buf.getvalue())


class MasterySignalIntegrationTests(_IsolatedDir):
    """code_attempt with linked_test must be recognized by the
    `_code_attempt_with_passing_test` signal in mastery scoring."""

    def _ts(self, days_ago: float) -> str:
        return (
            datetime.now(timezone.utc) - timedelta(days=days_ago)
        ).isoformat(timespec="seconds")

    def test_code_attempt_with_passing_test_contributes_to_mastery(self) -> None:
        # 2 high-score drills (+2) + code_attempt linked to passing test (+1)
        # = 3 ≥ threshold → mastered. Without the code_attempt the score would
        # be 2 and not reach the threshold (since this test_result is fallback,
        # which alone needs 2 passes).
        events = [
            {
                "event_type": "drill_answer",
                "event_id": "d1",
                "ts": self._ts(1),
                "learner_id": "ca-tester",
                "concept_ids": ["concept:spring/bean"],
                "drill_session_id": "s1",
                "linked_learning_point": "x",
                "total_score": 9,
                "dimensions": {},
                "weak_tags": [],
            },
            {
                "event_type": "drill_answer",
                "event_id": "d2",
                "ts": self._ts(0.5),
                "learner_id": "ca-tester",
                "concept_ids": ["concept:spring/bean"],
                "drill_session_id": "s2",
                "linked_learning_point": "x",
                "total_score": 8,
                "dimensions": {},
                "weak_tags": [],
            },
            # Fallback test pass — alone gives 0 (needs 2).
            {
                "event_type": "test_result",
                "event_id": "t-pass",
                "ts": self._ts(0.2),
                "learner_id": "ca-tester",
                "module_context": "spring-core-1",
                "concept_ids": ["concept:spring/bean"],
                "concept_match_mode": "fallback",
                "module": "spring-core-1",
                "test_class": "BeanTest",
                "test_method": "register",
                "pass": True,
            },
            # code_attempt with linked_test pointing at the above test pass.
            {
                "event_type": "code_attempt",
                "event_id": "ca1",
                "ts": self._ts(0.1),
                "learner_id": "ca-tester",
                "module_context": "spring-core-1",
                "concept_ids": ["concept:spring/bean"],
                "file_path": "missions/spring-learning-test/spring-core-1/initial/Bean.java",
                "diff_summary": "register 추가",
                "lines_added": 5,
                "lines_removed": 0,
                "linked_test": "BeanTest.register",
            },
        ]
        with self.history_path.open("w", encoding="utf-8") as fh:
            for ev in events:
                fh.write(json.dumps(ev, ensure_ascii=False) + "\n")
        profile = learner_memory.recompute_learner_profile()
        mastered = {c["concept_id"] for c in profile["concepts"]["mastered"]}
        self.assertIn("concept:spring/bean", mastered)


if __name__ == "__main__":
    unittest.main()
