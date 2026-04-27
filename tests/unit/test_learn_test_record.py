"""Coverage for `bin/learn-test` and `bin/learn-record-code`.

Both subcommands write events into `state/learner/history.jsonl`. We
build a fake JUnit results dir with a passing case + a failing case,
run `cmd_learn_test`, then confirm both events were recorded with the
expected pass/fail flags and concept_ids.
"""

from __future__ import annotations

import argparse
import io
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
from core import concept_catalog, learner_memory  # noqa: E402


JUNIT_XML_PASS = """<?xml version="1.0" encoding="UTF-8"?>
<testsuite name="cholog.BeanTest" tests="2" failures="1" errors="0" skipped="0" time="0.245">
  <testcase name="registerBean" classname="cholog.BeanTest" time="0.123"/>
  <testcase name="failBean" classname="cholog.BeanTest" time="0.122">
    <failure message="expected 1 but was 0">java.lang.AssertionError: expected 1 but was 0
    at cholog.BeanTest.failBean(BeanTest.java:42)</failure>
  </testcase>
</testsuite>
"""


class _DiskIsolated(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tmp_root = Path(self.tmp.name)
        self.learner_dir = tmp_root / "learner"
        self.learner_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir = tmp_root / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

        history = self.learner_dir / "history.jsonl"
        profile = self.learner_dir / "profile.json"
        summary = self.learner_dir / "summary.json"
        identity = self.learner_dir / "identity.json"
        self.history_path = history

        prev_env = os.environ.get("WOOWA_LEARNER_ID")
        os.environ["WOOWA_LEARNER_ID"] = "junit-tester"

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
        self._stdout = io.StringIO()
        self._stdout_patch = patch.object(sys, "stdout", self._stdout)
        self._stdout_patch.start()
        self.addCleanup(self._stdout_patch.stop)

    def _events(self) -> list[dict]:
        if not self.history_path.exists():
            return []
        return [
            json.loads(line)
            for line in self.history_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]


class LearnTestCommandTests(_DiskIsolated):
    def setUp(self) -> None:
        super().setUp()
        (self.results_dir / "TEST-cholog.BeanTest.xml").write_text(
            JUNIT_XML_PASS, encoding="utf-8"
        )

    def test_records_pass_and_fail_events(self) -> None:
        ns = argparse.Namespace(
            module="spring-core-1",
            path=str(self.results_dir),
            no_record=False,
        )
        rc = workbench_cli.cmd_learn_test(ns)
        self.assertEqual(rc, 0)
        events = self._events()
        self.assertEqual(len(events), 2)
        passed = [e for e in events if e["pass"]]
        failed = [e for e in events if not e["pass"]]
        self.assertEqual(len(passed), 1)
        self.assertEqual(len(failed), 1)
        self.assertIsNone(passed[0]["failure_message"])
        self.assertIn("expected 1", failed[0]["failure_message"])
        self.assertIn("concept:spring/bean", failed[0]["concept_ids"])

    def test_no_record_flag_only_summarizes(self) -> None:
        ns = argparse.Namespace(
            module="spring-core-1",
            path=str(self.results_dir),
            no_record=True,
        )
        rc = workbench_cli.cmd_learn_test(ns)
        self.assertEqual(rc, 0)
        self.assertEqual(self._events(), [])
        out = json.loads(self._stdout.getvalue().strip().splitlines()[-1])
        self.assertEqual(out["scanned"], 2)
        self.assertEqual(out["recorded"], 0)
        self.assertEqual(out["passed"], 1)
        self.assertEqual(out["failed"], 1)


class LearnRecordCodeTests(_DiskIsolated):
    def test_appends_code_attempt(self) -> None:
        ns = argparse.Namespace(
            file_path="missions/spring-learning-test/spring-core-1/initial/Bean.java",
            summary="added @Component to BeanRegistry",
            lines_added=3,
            lines_removed=1,
            linked_test="cholog.BeanTest.registerBean",
            module="spring-core-1",
        )
        rc = workbench_cli.cmd_learn_record_code(ns)
        self.assertEqual(rc, 0)
        events = self._events()
        self.assertEqual(len(events), 1)
        ev = events[0]
        self.assertEqual(ev["event_type"], "code_attempt")
        self.assertEqual(ev["lines_added"], 3)
        self.assertEqual(ev["lines_removed"], 1)
        self.assertEqual(ev["linked_test"], "cholog.BeanTest.registerBean")


if __name__ == "__main__":
    unittest.main()
