"""Operational triage CLI for BLOCKED queue items.

Two CLI surfaces are pinned here:

* ``Orchestrator.unblock_items()`` — restores BLOCKED → PENDING so a
  worker can re-claim. Used when the gate flagged a transient issue
  (lint failure, prompt drift) and the next attempt has a real chance.
* ``Orchestrator.drop_blocked_items()`` — deletes BLOCKED rows that
  cannot usefully be retried (Pilot lock violations etc.). Re-running
  the same item would just hit the same fail-fast gate again.

Both methods share the ``--item-id`` / ``--reason-contains`` /
``--profile`` matcher contract and a safe-default empty-match guard
so that an accidental no-arg call cannot mass-mutate the queue.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.workbench.core.orchestrator import Orchestrator


def _read_history(orchestrator: Orchestrator) -> list[dict]:
    if not orchestrator.history_path.exists():
        return []
    return [
        json.loads(line)
        for line in orchestrator.history_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class _TmpOrchestrator(unittest.TestCase):
    def setUp(self) -> None:
        tmpdir = Path(tempfile.mkdtemp())
        self.orchestrator = Orchestrator(tmpdir / "state" / "orchestrator")
        self.addCleanup(lambda: None)

    def _seed(self, items: list[dict]) -> None:
        self.orchestrator.save_queue(items)

    def _blocked_item(
        self,
        item_id: str,
        *,
        lane: str = "migration-content-network",
        summary: str = "pilot lock violation: 2 file(s) — first: foo.md",
        fleet_profile: str = "migration_v3_60",
    ) -> dict:
        return {
            "item_id": item_id,
            "lane": lane,
            "title": f"title-{item_id}",
            "goal": f"goal-{item_id}",
            "tags": [],
            "status": "blocked",
            "fleet_profile": fleet_profile,
            "completion_summary": summary,
            "lease_owner": None,
            "lease_expires_at": None,
            "lease_write_scopes": [],
            "source": "migration-template",
            "priority": 5,
            "updated_at": "2026-05-05T00:00:00Z",
            "created_at": "2026-05-05T00:00:00Z",
        }


class UnblockItemsTest(_TmpOrchestrator):
    def test_no_matcher_is_safe_no_op(self) -> None:
        self._seed([self._blocked_item("a"), self._blocked_item("b")])
        result = self.orchestrator.unblock_items()
        self.assertEqual(result, {"matched": 0, "unblocked": 0, "items": []})
        # Both items still blocked.
        statuses = [it["status"] for it in self.orchestrator.load_queue()]
        self.assertEqual(statuses, ["blocked", "blocked"])

    def test_unblock_by_item_id_restores_to_pending(self) -> None:
        self._seed([self._blocked_item("a"), self._blocked_item("b")])
        result = self.orchestrator.unblock_items(item_ids=["a"])
        self.assertEqual(result["unblocked"], 1)
        self.assertEqual(result["items"][0]["item_id"], "a")
        statuses = {
            it["item_id"]: it["status"]
            for it in self.orchestrator.load_queue()
        }
        self.assertEqual(statuses, {"a": "pending", "b": "blocked"})

    def test_unblock_by_reason_substring(self) -> None:
        self._seed([
            self._blocked_item("a", summary="strict-v3 lint fail: missing field"),
            self._blocked_item("b", summary="pilot lock violation: 1 file"),
        ])
        result = self.orchestrator.unblock_items(reason_contains="strict-v3")
        self.assertEqual(result["unblocked"], 1)
        self.assertEqual(result["items"][0]["item_id"], "a")
        statuses = {
            it["item_id"]: it["status"]
            for it in self.orchestrator.load_queue()
        }
        self.assertEqual(statuses, {"a": "pending", "b": "blocked"})

    def test_unblock_clears_lease_fields(self) -> None:
        item = self._blocked_item("a")
        item["lease_owner"] = "stale-worker"
        item["lease_expires_at"] = "2026-05-04T00:00:00Z"
        item["lease_write_scopes"] = ["scope:x"]
        self._seed([item])
        self.orchestrator.unblock_items(item_ids=["a"])
        loaded = self.orchestrator.load_queue()[0]
        self.assertEqual(loaded["status"], "pending")
        self.assertIsNone(loaded["lease_owner"])
        self.assertIsNone(loaded["lease_expires_at"])
        self.assertEqual(loaded["lease_write_scopes"], [])

    def test_unblock_writes_audit_event(self) -> None:
        self._seed([self._blocked_item("a")])
        self.orchestrator.unblock_items(item_ids=["a"])
        events = _read_history(self.orchestrator)
        unblocked_events = [
            e for e in events if e.get("type") == "queue.unblocked"
        ]
        self.assertEqual(len(unblocked_events), 1)
        self.assertEqual(unblocked_events[0]["item_id"], "a")

    def test_profile_filter_narrows_match(self) -> None:
        self._seed([
            self._blocked_item("a", fleet_profile="migration_v3_60"),
            self._blocked_item("b", fleet_profile="expansion60"),
        ])
        result = self.orchestrator.unblock_items(
            item_ids=["a", "b"], fleet_profile="migration_v3_60",
        )
        self.assertEqual(result["unblocked"], 1)
        self.assertEqual(result["items"][0]["item_id"], "a")


class DropBlockedItemsTest(_TmpOrchestrator):
    def test_no_matcher_is_safe_no_op(self) -> None:
        self._seed([self._blocked_item("a"), self._blocked_item("b")])
        result = self.orchestrator.drop_blocked_items()
        self.assertEqual(result, {"matched": 0, "dropped": 0, "items": []})
        self.assertEqual(len(self.orchestrator.load_queue()), 2)

    def test_drop_by_reason_removes_rows(self) -> None:
        self._seed([
            self._blocked_item("a", summary="pilot lock violation: 2 file(s)"),
            self._blocked_item("b", summary="strict-v3 lint fail"),
            self._blocked_item("c", summary="pilot lock violation: 1 file"),
        ])
        result = self.orchestrator.drop_blocked_items(
            reason_contains="pilot lock violation",
        )
        self.assertEqual(result["dropped"], 2)
        remaining = [it["item_id"] for it in self.orchestrator.load_queue()]
        self.assertEqual(remaining, ["b"])

    def test_drop_does_not_touch_non_blocked(self) -> None:
        pending = self._blocked_item("p")
        pending["status"] = "pending"
        self._seed([pending, self._blocked_item("a")])
        self.orchestrator.drop_blocked_items(item_ids=["p", "a"])
        remaining = {it["item_id"] for it in self.orchestrator.load_queue()}
        # 'p' was pending — drop_blocked_items must not touch it.
        self.assertEqual(remaining, {"p"})

    def test_drop_writes_audit_event(self) -> None:
        self._seed([self._blocked_item("a")])
        self.orchestrator.drop_blocked_items(item_ids=["a"])
        events = _read_history(self.orchestrator)
        dropped_events = [
            e for e in events if e.get("type") == "queue.dropped"
        ]
        self.assertEqual(len(dropped_events), 1)
        self.assertEqual(dropped_events[0]["item_id"], "a")

    def test_no_match_keeps_queue_unchanged(self) -> None:
        self._seed([self._blocked_item("a", summary="something else")])
        before = self.orchestrator.load_queue()
        self.orchestrator.drop_blocked_items(reason_contains="pilot lock")
        after = self.orchestrator.load_queue()
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
