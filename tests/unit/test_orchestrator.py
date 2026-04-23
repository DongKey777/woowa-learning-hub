"""Persistent orchestrator queue/lease lifecycle."""

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.workbench.core.orchestrator import Orchestrator
from scripts.workbench.core.orchestrator_workers import WORKER_FLEET


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
    def test_worker_fleet_has_16_distinct_workers(self) -> None:
        self.assertEqual(len(WORKER_FLEET), 16)
        names = {entry["name"] for entry in WORKER_FLEET}
        lanes = {entry["lane"] for entry in WORKER_FLEET}
        self.assertEqual(len(names), 16)
        self.assertEqual(len(lanes), 16)


if __name__ == "__main__":
    unittest.main()
