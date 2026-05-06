"""Pilot lock guard tests for the migration_v3 completion gate.

The lock list (config/migration_v3/locked_pilot_paths.json)
is the contract that holds the OVERALL 95.5% baseline. If a migration
worker tries to write to any path in that list, the completion gate
must fail fast (no subprocess invocations) and the task must be
returned to the queue.

These tests stub the lock loader so they don't depend on the
production lock file.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from scripts.workbench.core import orchestrator_workers as OW


class PilotLockDetectionTest(unittest.TestCase):
    def test_is_migration_v3_worker_recognizes_prefix(self):
        self.assertTrue(OW._is_migration_v3_worker("migration-v3-spring-frontmatter"))
        self.assertTrue(OW._is_migration_v3_worker("migration-v3-rag-cohort-eval-gate"))
        self.assertFalse(OW._is_migration_v3_worker("expansion60-spring-di-bean"))
        self.assertFalse(OW._is_migration_v3_worker("runtime-java-basics"))
        self.assertFalse(OW._is_migration_v3_worker(""))


class PilotLockLoaderTest(unittest.TestCase):
    def test_returns_empty_set_when_lock_file_missing(self):
        with mock.patch.object(OW, "ROOT", Path("/tmp/does-not-exist-xyz")):
            self.assertEqual(OW._load_pilot_lock_paths(), set())

    def test_returns_empty_set_on_invalid_json(self):
        with TemporaryDirectory() as td:
            tmp = Path(td)
            (tmp / "config" / "migration_v3").mkdir(parents=True)
            (tmp / OW.PILOT_LOCK_PATH_REL).write_text("not-json", encoding="utf-8")
            with mock.patch.object(OW, "ROOT", tmp):
                self.assertEqual(OW._load_pilot_lock_paths(), set())

    def test_loads_paths_from_lock_file(self):
        with TemporaryDirectory() as td:
            tmp = Path(td)
            (tmp / "config" / "migration_v3").mkdir(parents=True)
            payload = {
                "locked_paths": [
                    "knowledge/cs/contents/database/lock-basics.md",
                    "knowledge/cs/contents/spring/spring-bean-di-basics.md",
                ],
            }
            (tmp / OW.PILOT_LOCK_PATH_REL).write_text(
                json.dumps(payload), encoding="utf-8")
            with mock.patch.object(OW, "ROOT", tmp):
                self.assertEqual(
                    OW._load_pilot_lock_paths(),
                    {"knowledge/cs/contents/database/lock-basics.md",
                     "knowledge/cs/contents/spring/spring-bean-di-basics.md"},
                )


class PilotLockViolationTest(unittest.TestCase):
    def _patched_load(self, locked: set[str]):
        return mock.patch.object(OW, "_load_pilot_lock_paths",
                                 return_value=locked)

    def test_no_violations_when_lock_empty(self):
        with self._patched_load(set()):
            self.assertEqual(
                OW._pilot_lock_violations(["knowledge/cs/contents/foo.md"]),
                [],
            )

    def test_no_violations_when_changed_outside_lock(self):
        locked = {"knowledge/cs/contents/database/lock-basics.md"}
        with self._patched_load(locked):
            self.assertEqual(
                OW._pilot_lock_violations(
                    ["knowledge/cs/contents/algorithm/new.md"]),
                [],
            )

    def test_returns_intersection_sorted(self):
        locked = {
            "knowledge/cs/contents/database/lock-basics.md",
            "knowledge/cs/contents/spring/spring-bean-di-basics.md",
        }
        changed = [
            "knowledge/cs/contents/spring/spring-bean-di-basics.md",
            "knowledge/cs/contents/database/lock-basics.md",
            "knowledge/cs/contents/algorithm/new.md",  # not locked
        ]
        with self._patched_load(locked):
            violations = OW._pilot_lock_violations(changed)
        self.assertEqual(
            violations,
            [
                "knowledge/cs/contents/database/lock-basics.md",
                "knowledge/cs/contents/spring/spring-bean-di-basics.md",
            ],
        )


class CompletionGateBehaviorTest(unittest.TestCase):
    """End-to-end gate behavior: pilot lock blocks migration workers
    without spawning any subprocess."""

    def test_gate_fails_fast_on_pilot_violation_no_subprocess(self):
        locked = {"knowledge/cs/contents/database/lock-basics.md"}
        task = {
            "changed_files": [
                "knowledge/cs/contents/database/lock-basics.md",
            ],
        }
        with mock.patch.object(OW, "_load_pilot_lock_paths", return_value=locked), \
             mock.patch.object(OW, "_run_completion_gate_command") as gate_cmd:
            result = OW._run_completion_gates(
                "migration-v3-database-frontmatter",
                "migration-content-database",
                task,
            )
        self.assertFalse(result["ok"])
        self.assertTrue(result["blocked"])
        self.assertIn("pilot lock violation", result["summary"])
        self.assertEqual(result["commands"], [])
        gate_cmd.assert_not_called()

    def test_gate_proceeds_when_changed_files_outside_lock(self):
        locked = {"knowledge/cs/contents/database/lock-basics.md"}
        task = {
            "changed_files": [
                "knowledge/cs/contents/algorithm/new-doc.md",
            ],
        }
        ok_command = {
            "command": "stub", "returncode": 0, "ok": True, "output": "",
        }
        with mock.patch.object(OW, "_load_pilot_lock_paths", return_value=locked), \
             mock.patch.object(OW, "_run_completion_gate_command",
                               return_value=ok_command) as gate_cmd:
            result = OW._run_completion_gates(
                "migration-v3-algorithm-frontmatter",
                "migration-content-algorithm",
                task,
            )
        self.assertTrue(result["ok"])
        # corpus_lint v3 was scheduled for the migration worker
        called_commands = [call.args[0] for call in gate_cmd.mock_calls]
        joined = " ".join(" ".join(c) for c in called_commands)
        self.assertIn("scripts.learning.rag.corpus_lint", joined)
        self.assertIn("--strict-v3", joined)

    def test_legacy_worker_unaffected_by_pilot_lock(self):
        """Non-migration worker is allowed to touch any file (lock list
        is migration_v3-scoped)."""
        locked = {"knowledge/cs/contents/database/lock-basics.md"}
        task = {
            "changed_files": [
                "knowledge/cs/contents/database/lock-basics.md",
            ],
        }
        ok_command = {
            "command": "stub", "returncode": 0, "ok": True, "output": "",
        }
        with mock.patch.object(OW, "_load_pilot_lock_paths", return_value=locked), \
             mock.patch.object(OW, "_run_completion_gate_command",
                               return_value=ok_command) as gate_cmd:
            result = OW._run_completion_gates(
                "expansion60-database-jdbc",
                "database",
                task,
            )
        self.assertTrue(result["ok"])
        # Legacy lint, not corpus_lint
        called_commands = [call.args[0] for call in gate_cmd.mock_calls]
        joined = " ".join(" ".join(c) for c in called_commands)
        self.assertIn("scripts/lint_cs_authoring.py", joined)
        self.assertNotIn("--strict-v3", joined)


if __name__ == "__main__":
    unittest.main()
