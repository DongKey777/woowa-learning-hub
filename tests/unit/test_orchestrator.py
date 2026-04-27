"""Persistent orchestrator queue/lease lifecycle."""

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

from scripts.workbench.core import orchestrator_workers as ow
from scripts.workbench.core.orchestrator import Orchestrator
from scripts.workbench.core.orchestrator_workers import WORKER_FLEET, _fleet_can_enqueue


class OrchestratorTest(unittest.TestCase):
    def _make_orchestrator(self) -> Orchestrator:
        tmpdir = Path(tempfile.mkdtemp())
        return Orchestrator(tmpdir / "state" / "orchestrator")

    def test_run_once_seeds_queue_and_wave(self) -> None:
        orchestrator = self._make_orchestrator()
        payload = orchestrator.run_once(low_water_mark=1, wave_size=5)
        queue = orchestrator.load_queue()
        self.assertGreaterEqual(len(queue), 5)
        self.assertEqual(len(payload["current_wave"]["items"]), 5)
        self.assertEqual(payload["status"]["queue_summary"]["pending"], len(queue))

    def test_run_once_can_refresh_without_building_expansion_wave(self) -> None:
        orchestrator = self._make_orchestrator()
        payload = orchestrator.run_once(low_water_mark=0, wave_size=0, refresh_backlog=False)
        self.assertEqual(orchestrator.load_queue(), [])
        self.assertEqual(payload["current_wave"]["items"], [])

    def test_claim_and_complete_cycle(self) -> None:
        orchestrator = self._make_orchestrator()
        orchestrator.run_once(low_water_mark=1, wave_size=3)
        claimed = orchestrator.claim("worker-a", limit=2)
        self.assertEqual(len(claimed["claimed"]), 2)
        item_id = claimed["claimed"][0]["item_id"]
        complete = orchestrator.complete(item_id, "worker-a", "completed one wave")
        self.assertEqual(complete["status"], "completed")
        item = next(entry for entry in orchestrator.load_queue() if entry["item_id"] == item_id)
        self.assertEqual(item["status"], "completed")
        self.assertEqual(item["completion_summary"], "completed one wave")

    def test_claim_can_skip_backlog_refresh_for_quality_workers(self) -> None:
        orchestrator = self._make_orchestrator()
        orchestrator.run_once(low_water_mark=1, wave_size=3)
        queue_len = len(orchestrator.load_queue())
        claimed = orchestrator.claim("worker-a", lanes=["not-a-real-lane"], refresh_backlog=False)
        self.assertEqual(claimed["claimed"], [])
        self.assertEqual(len(orchestrator.load_queue()), queue_len)
        self.assertEqual(orchestrator.status()["current_wave"]["items"], [])

    def test_expired_lease_returns_to_pending(self) -> None:
        orchestrator = self._make_orchestrator()
        start = datetime(2026, 4, 14, 0, 0, tzinfo=timezone.utc)
        orchestrator.run_once(low_water_mark=1, wave_size=2, now=start)
        claimed = orchestrator.claim("worker-a", limit=1, lease_seconds=1, now=start)
        item_id = claimed["claimed"][0]["item_id"]
        orchestrator.run_once(now=start + timedelta(seconds=2))
        item = next(entry for entry in orchestrator.load_queue() if entry["item_id"] == item_id)
        self.assertEqual(item["status"], "pending")
        self.assertIsNone(item["lease_owner"])

    def test_status_reports_current_wave(self) -> None:
        orchestrator = self._make_orchestrator()
        orchestrator.run_once(low_water_mark=1, wave_size=4)
        status = orchestrator.status()
        self.assertIn("current_wave", status)
        self.assertEqual(len(status["current_wave"]["items"]), 4)

    def test_requeue_returns_leased_item_to_pending(self) -> None:
        orchestrator = self._make_orchestrator()
        now = datetime(2026, 4, 14, 0, 0, tzinfo=timezone.utc)
        orchestrator.run_once(low_water_mark=1, wave_size=2, now=now)
        claimed = orchestrator.claim("worker-a", limit=1, now=now)
        item_id = claimed["claimed"][0]["item_id"]
        payload = orchestrator.requeue(item_id, "worker-a", "backend failed", now=now)
        self.assertEqual(payload["status"], "pending")
        item = next(entry for entry in orchestrator.load_queue() if entry["item_id"] == item_id)
        self.assertEqual(item["status"], "pending")
        self.assertIsNone(item["lease_owner"])

    def test_release_worker_leases_requeues_owned_items(self) -> None:
        orchestrator = self._make_orchestrator()
        now = datetime(2026, 4, 14, 0, 0, tzinfo=timezone.utc)
        orchestrator.run_once(low_water_mark=1, wave_size=2, now=now)
        claimed = orchestrator.claim("worker-a", limit=1, now=now)
        item_id = claimed["claimed"][0]["item_id"]
        released = orchestrator.release_worker_leases("worker-a", "restart", now=now)
        self.assertEqual(released, [item_id])
        item = next(entry for entry in orchestrator.load_queue() if entry["item_id"] == item_id)
        self.assertEqual(item["status"], "pending")

    def test_write_scope_lock_blocks_conflicting_worker(self) -> None:
        orchestrator = self._make_orchestrator()
        now = datetime(2026, 4, 14, 0, 0, tzinfo=timezone.utc)
        orchestrator.run_once(low_water_mark=1, wave_size=2, now=now)
        first = orchestrator.claim(
            "worker-a",
            limit=1,
            write_scopes=["content:spring:core-mvc"],
            now=now,
        )
        self.assertEqual(len(first["claimed"]), 1)

        blocked = orchestrator.claim(
            "worker-b",
            limit=1,
            write_scopes=["content:spring:core-mvc"],
            now=now,
        )
        self.assertEqual(blocked["claimed"], [])

    def test_claim_tags_filter_candidate_selection(self) -> None:
        orchestrator = self._make_orchestrator()
        now = datetime(2026, 4, 14, 0, 0, tzinfo=timezone.utc)
        orchestrator.enqueue_candidates(
            "language-java",
            [
                {"title": "Java collections first route", "goal": "Explain List and Map basics", "tags": ["collections"]},
                {"title": "Java object memory model", "goal": "Explain object references", "tags": ["zz-object-filter"]},
            ],
            source="test",
            now=now,
        )
        claimed = orchestrator.claim(
            "worker-a",
            lanes=["language-java"],
            limit=1,
            claim_tags=["zz-object-filter"],
            now=now,
        )
        self.assertEqual(claimed["claimed"][0]["title"], "Java object memory model")

    def test_seed_woowa_backend_curriculum_backlog_adds_foundation_pack(self) -> None:
        orchestrator = self._make_orchestrator()
        created = orchestrator.seed_woowa_backend_curriculum_backlog()
        self.assertIn("language-java", created)
        self.assertIn("spring", created)
        queue = orchestrator.load_queue()
        java_item = next(
            entry
            for entry in queue
            if entry.get("base_title") == "Java execution model and object mental model"
        )
        self.assertEqual(java_item["source"], "curriculum-foundation")
        self.assertIn("curriculum-foundation", java_item["tags"])
        self.assertGreaterEqual(int(java_item["priority"]), 100)


class FleetSpecTest(unittest.TestCase):
    def test_worker_fleet_has_30_quality_repair_workers(self) -> None:
        self.assertEqual(len(WORKER_FLEET), 30)
        names = {entry["name"] for entry in WORKER_FLEET}
        self.assertEqual(len(names), 30)
        roles = {entry["role"] for entry in WORKER_FLEET}
        self.assertEqual(roles, {"qa", "rag", "ops"})
        self.assertFalse(any(entry["role"] == "content" for entry in WORKER_FLEET))
        self.assertGreaterEqual(sum(1 for entry in WORKER_FLEET if entry["role"] == "qa"), 20)
        self.assertTrue(all("mode" in entry for entry in WORKER_FLEET))
        self.assertTrue(all("write_scopes" in entry for entry in WORKER_FLEET))
        self.assertTrue(all("claim_tags" in entry for entry in WORKER_FLEET))
        self.assertTrue(all(not entry.get("can_enqueue", True) for entry in WORKER_FLEET))
        self.assertFalse(_fleet_can_enqueue())


class CompletionGateTest(unittest.TestCase):
    def test_authoring_lint_targets_only_content_articles(self) -> None:
        targets = ow._authoring_lint_targets(
            [
                "knowledge/cs/contents/database/transaction-basics.md",
                "knowledge/cs/contents/database/README.md",
                "knowledge/cs/rag/README.md",
                "docs/orchestrator.md",
            ]
        )
        self.assertEqual(targets, ["knowledge/cs/contents/database/transaction-basics.md"])

    def test_rag_projection_worker_runs_projection_search_slice(self) -> None:
        tests = ow._rag_pytest_args("runtime-rag-ranking-projection", "qa-retrieval", [])
        self.assertEqual(tests, [["tests/unit/test_cs_rag_search.py", "-k", "projection"]])

    def test_rag_signal_rule_change_runs_signal_rule_tests(self) -> None:
        tests = ow._rag_pytest_args(
            "runtime-rag-signal-rules",
            "qa-retrieval",
            ["scripts/learning/rag/signal_rules.py"],
        )
        self.assertEqual(tests, [["tests/unit/test_cs_rag_signal_rules.py"]])

    def test_completion_gates_run_lint_for_changed_content_doc(self) -> None:
        commands: list[list[str]] = []

        def fake_run(command: list[str], *, timeout_seconds: int) -> dict:
            commands.append(command)
            return {"command": " ".join(command), "returncode": 0, "ok": True, "output": ""}

        with (
            mock.patch.object(ow, "_project_python", return_value="python"),
            mock.patch.object(ow, "_run_completion_gate_command", side_effect=fake_run),
        ):
            result = ow._run_completion_gates(
                "runtime-qa-content-database",
                "qa-content-database",
                {
                    "changed_files": [
                        "knowledge/cs/contents/database/transaction-basics.md",
                        "knowledge/cs/contents/database/README.md",
                        "knowledge/cs/rag/README.md",
                    ]
                },
            )

        self.assertTrue(result["ok"])
        self.assertEqual(
            commands,
            [
                [
                    "python",
                    "scripts/lint_cs_authoring.py",
                    "--quiet",
                    "knowledge/cs/contents/database/transaction-basics.md",
                ]
            ],
        )

    def test_completion_gates_fail_on_lint_failure(self) -> None:
        def fake_run(command: list[str], *, timeout_seconds: int) -> dict:
            return {
                "command": " ".join(command),
                "returncode": 1,
                "ok": False,
                "output": "[FAIL] bad.md",
            }

        with (
            mock.patch.object(ow, "_project_python", return_value="python"),
            mock.patch.object(ow, "_run_completion_gate_command", side_effect=fake_run),
        ):
            result = ow._run_completion_gates(
                "runtime-qa-content-database",
                "qa-content-database",
                {"changed_files": ["knowledge/cs/contents/database/bad.md"]},
            )

        self.assertFalse(result["ok"])
        self.assertIn("completion gate failed", result["summary"])

    def test_completion_gates_reject_unsafe_changed_file_path(self) -> None:
        result = ow._run_completion_gates(
            "runtime-qa-content-database",
            "qa-content-database",
            {"changed_files": ["../outside.md"]},
        )
        self.assertFalse(result["ok"])
        self.assertIn("invalid changed file path", result["summary"])


if __name__ == "__main__":
    unittest.main()
