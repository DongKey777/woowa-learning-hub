"""Topology invariants for the migration_v3 worker fleet.

Phase 8 fleet is registered but intentionally unstarted. This module
guards the *shape* — fleet size, role split, mode split, write-scope
uniqueness, FLEET_PROFILES registration, and Pilot lock list shape.

If a migration design change reaches the fleet, this test is the
first place to update — and the first place to fail when the change
is unintended.
"""

from __future__ import annotations

import json
import unittest
from collections import Counter
from pathlib import Path

from scripts.workbench.core import orchestrator_workers as OW
from scripts.workbench.core import orchestrator_migration_workers as MW


REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LOCK_PATH = REPO_ROOT / OW.PILOT_LOCK_PATH_REL


class FleetCompositionTest(unittest.TestCase):
    def test_fleet_size_matches_constant(self):
        self.assertEqual(len(MW.MIGRATION_V3_FLEET), MW.MIGRATION_V3_FLEET_SIZE)
        self.assertEqual(MW.MIGRATION_V3_FLEET_SIZE, 30)

    def test_role_split_is_2_22_3_2_1(self):
        roles = Counter(w["role"] for w in MW.MIGRATION_V3_FLEET)
        self.assertEqual(
            dict(roles),
            {"curriculum": 2, "migration": 22, "qa": 3, "rag": 2, "ops": 1},
        )

    def test_eleven_categories_have_two_workers_each(self):
        # 11 categories x {frontmatter, prefix} = 22 migration workers
        categories = MW.MIGRATION_V3_CATEGORIES
        self.assertEqual(len(categories), 11)
        for category in categories:
            frontmatter_name = f"migration-v3-{category}-frontmatter"
            prefix_name = f"migration-v3-{category}-prefix"
            names = {w["name"] for w in MW.MIGRATION_V3_FLEET}
            self.assertIn(frontmatter_name, names,
                          f"missing worker {frontmatter_name}")
            self.assertIn(prefix_name, names,
                          f"missing worker {prefix_name}")

    def test_modes_balanced(self):
        modes = Counter(w["mode"] for w in MW.MIGRATION_V3_FLEET)
        # 11 frontmatter + 11 prefix workers
        self.assertEqual(modes["migrate_v0_to_v3"], 11)
        self.assertEqual(modes["migrate_prefix"], 11)
        # 2 curriculum reports
        self.assertEqual(modes["report"], 2)


class WriteScopeContentionTest(unittest.TestCase):
    def test_write_scopes_have_no_unintended_collisions(self):
        scope_to_workers: dict[str, list[str]] = {}
        for w in MW.MIGRATION_V3_FLEET:
            for scope in w["write_scopes"]:
                scope_to_workers.setdefault(scope, []).append(w["name"])
        # At most one worker per scope (no broad locks).
        for scope, owners in scope_to_workers.items():
            self.assertEqual(
                len(owners), 1,
                f"write_scope {scope!r} owned by multiple workers: {owners}",
            )

    def test_singleton_singletons_are_singletons(self):
        # rag golden + cohort-eval should each have a single owner
        # (matching expansion60 singleton pattern).
        scopes = {scope for w in MW.MIGRATION_V3_FLEET for scope in w["write_scopes"]}
        self.assertIn("migration_v3:rag:golden", scopes)
        self.assertIn("migration_v3:rag:cohort-eval", scopes)


class PendingCapTest(unittest.TestCase):
    def test_pending_cap_tighter_than_expansion60(self):
        # Migration is more conservative — fewer items in flight per
        # worker because cohort_eval gate latency dominates.
        self.assertLess(
            MW.MIGRATION_V3_WORKER_PENDING_CAP,
            OW.EXPANSION60_WORKER_PENDING_CAP,
        )
        self.assertEqual(MW.MIGRATION_V3_WORKER_PENDING_CAP, 12)

    def test_every_worker_carries_pending_cap_field(self):
        for w in MW.MIGRATION_V3_FLEET:
            self.assertEqual(w["pending_cap"], MW.MIGRATION_V3_WORKER_PENDING_CAP)


class FleetProfilesRegistrationTest(unittest.TestCase):
    def test_migration_v3_registered_in_FLEET_PROFILES(self):
        self.assertIn("migration_v3", OW.FLEET_PROFILES)
        self.assertIs(OW.FLEET_PROFILES["migration_v3"], MW.MIGRATION_V3_FLEET)

    def test_normalize_accepts_migration_v3(self):
        self.assertEqual(OW._normalize_fleet_profile("migration_v3"), "migration_v3")
        self.assertEqual(OW._normalize_fleet_profile(" Migration_V3 "), "migration_v3")


class PilotLockListTest(unittest.TestCase):
    """The lock list shape is part of the gate contract."""

    def test_lock_file_exists_and_is_valid_json(self):
        self.assertTrue(LOCK_PATH.exists(),
                        f"lock list missing at {LOCK_PATH}")
        payload = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        self.assertEqual(payload["schema_version"], 1)
        self.assertIn("locked_paths", payload)
        self.assertIsInstance(payload["locked_paths"], list)

    def test_lock_count_matches_corpus_v3_count(self):
        payload = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        # 69 v3 docs in the corpus as of 2026-05-05. If this drifts,
        # update the lock list explicitly via a curriculum-pilot-lock
        # worker invocation, not silently.
        self.assertEqual(payload["locked_count"], len(payload["locked_paths"]))

    def test_lock_paths_all_repo_relative(self):
        payload = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        for p in payload["locked_paths"]:
            self.assertFalse(Path(p).is_absolute(),
                             f"lock path {p!r} is absolute")
            self.assertTrue(p.startswith("knowledge/cs/contents/"),
                            f"lock path {p!r} not under content tree")


if __name__ == "__main__":
    unittest.main()
