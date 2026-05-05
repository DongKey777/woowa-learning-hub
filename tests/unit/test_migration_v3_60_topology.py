"""Topology invariants for the migration_v3_60 worker fleet.

The 60-worker variant is shaped to attack the cohort_eval weak spots
measured 2026-05-05 (mission_bridge 83.3%, confusable_pairs 90%,
symptom_to_cause 93.3%). This module pins the contract — fleet size,
Wave A/B/C distribution, write-scope uniqueness, FLEET_PROFILES
registration. A drift between intended cohort attack and the actual
fleet topology fails here first.
"""

from __future__ import annotations

import unittest
from collections import Counter

from scripts.workbench.core import orchestrator_workers as OW
from scripts.workbench.core import orchestrator_migration_workers as MW


class FleetCompositionTest(unittest.TestCase):
    def test_fleet_size_is_60(self):
        self.assertEqual(len(MW.MIGRATION_V3_60_FLEET), MW.MIGRATION_V3_60_FLEET_SIZE)
        self.assertEqual(MW.MIGRATION_V3_60_FLEET_SIZE, 60)

    def test_role_split(self):
        roles = Counter(w["role"] for w in MW.MIGRATION_V3_60_FLEET)
        self.assertEqual(
            dict(roles),
            {"curriculum": 2, "migration": 34, "qa": 12, "rag": 8, "ops": 4},
        )

    def test_four_waves_with_revisit_loop_closer(self):
        modes = Counter(w["mode"] for w in MW.MIGRATION_V3_60_FLEET)
        self.assertEqual(modes["migrate_v0_to_v3"], 11)
        self.assertEqual(modes["migrate_prefix"], 11)
        self.assertEqual(modes["migrate_new_doc"], 11)
        self.assertEqual(modes["migrate_revisit"], 1)


class WaveCCohortAttackTest(unittest.TestCase):
    """Wave C is the direct attack on cohort_eval weak spots.

    Bigger weakness gets more workers (mission_bridge has the largest
    gap and gets 5 dedicated writers; chooser and symptom_router get 3
    each because confusable_pairs and symptom_to_cause have smaller
    fail counts)."""

    def test_five_mission_bridge_writers(self):
        names = {w["name"] for w in MW.MIGRATION_V3_60_FLEET
                 if "mission-bridge" in w["name"]}
        self.assertEqual(len(names), 5)
        for mission in MW.MIGRATION_V3_60_WAVE_C_MISSIONS:
            self.assertIn(
                f"migration-v3-60-new-mission-bridge-{mission}",
                names,
            )

    def test_three_chooser_writers(self):
        names = [w["name"] for w in MW.MIGRATION_V3_60_FLEET
                 if "new-chooser-" in w["name"]]
        self.assertEqual(len(names), 3)
        for category in MW.MIGRATION_V3_60_WAVE_C_CHOOSER_CATEGORIES:
            self.assertIn(
                f"migration-v3-60-new-chooser-{category}",
                names,
            )

    def test_three_symptom_router_writers(self):
        names = [w["name"] for w in MW.MIGRATION_V3_60_FLEET
                 if "new-symptom-router-" in w["name"]]
        self.assertEqual(len(names), 3)


class WaveABCategoryCoverageTest(unittest.TestCase):
    def test_wave_a_covers_all_eleven_categories(self):
        names = {w["name"] for w in MW.MIGRATION_V3_60_FLEET
                 if w["mode"] == "migrate_v0_to_v3"}
        for category in MW.MIGRATION_V3_CATEGORIES:
            self.assertIn(f"migration-v3-60-frontmatter-{category}", names)

    def test_wave_b_covers_all_eleven_categories(self):
        names = {w["name"] for w in MW.MIGRATION_V3_60_FLEET
                 if w["mode"] == "migrate_prefix"}
        for category in MW.MIGRATION_V3_CATEGORIES:
            self.assertIn(f"migration-v3-60-prefix-{category}", names)

    def test_language_java_path_nested(self):
        spring = next(w for w in MW.MIGRATION_V3_60_FLEET
                      if w["name"] == "migration-v3-60-frontmatter-spring")
        java = next(w for w in MW.MIGRATION_V3_60_FLEET
                    if w["name"] == "migration-v3-60-frontmatter-language-java")
        self.assertEqual(spring["target_paths"],
                         ["knowledge/cs/contents/spring/**"])
        self.assertEqual(java["target_paths"],
                         ["knowledge/cs/contents/language/java/**"])


class WriteScopeIsolationTest(unittest.TestCase):
    def test_no_write_scope_conflicts(self):
        scope_to_workers: dict[str, list[str]] = {}
        for w in MW.MIGRATION_V3_60_FLEET:
            for scope in w["write_scopes"]:
                scope_to_workers.setdefault(scope, []).append(w["name"])
        for scope, owners in scope_to_workers.items():
            self.assertEqual(len(owners), 1,
                             f"write_scope {scope!r} owned by {owners}")

    def test_singletons_are_singletons(self):
        scopes = {s for w in MW.MIGRATION_V3_60_FLEET for s in w["write_scopes"]}
        for must_be_singleton in (
            "migration_v3_60:rag:cohort-eval",
            "migration_v3_60:rag:golden",
            "migration_v3_60:rag:signal-rules",
        ):
            self.assertIn(must_be_singleton, scopes)

    def test_pending_cap_doubled_vs_v3_30(self):
        self.assertGreater(
            MW.MIGRATION_V3_60_WORKER_PENDING_CAP,
            MW.MIGRATION_V3_WORKER_PENDING_CAP,
        )
        self.assertEqual(MW.MIGRATION_V3_60_WORKER_PENDING_CAP, 28)


class FleetProfilesRegistrationTest(unittest.TestCase):
    def test_migration_v3_60_registered(self):
        self.assertIn("migration_v3_60", OW.FLEET_PROFILES)
        self.assertIs(OW.FLEET_PROFILES["migration_v3_60"], MW.MIGRATION_V3_60_FLEET)

    def test_normalize_accepts_migration_v3_60(self):
        self.assertEqual(
            OW._normalize_fleet_profile("migration_v3_60"),
            "migration_v3_60",
        )

    def test_v3_30_and_v3_60_coexist(self):
        """Both profiles are independent — switching one doesn't affect
        the other's worker definitions."""
        self.assertIs(OW.FLEET_PROFILES["migration_v3"], MW.MIGRATION_V3_FLEET)
        self.assertIs(OW.FLEET_PROFILES["migration_v3_60"], MW.MIGRATION_V3_60_FLEET)
        self.assertIsNot(MW.MIGRATION_V3_FLEET, MW.MIGRATION_V3_60_FLEET)


class PilotLockGateAppliesToBothFleetsTest(unittest.TestCase):
    """The Pilot lock check is profile-agnostic — it triggers for any
    worker whose name starts with 'migration-v3-' (covers both fleets)."""

    def test_v3_30_worker_caught_by_lock(self):
        self.assertTrue(OW._is_migration_v3_worker("migration-v3-spring-frontmatter"))

    def test_v3_60_worker_caught_by_lock(self):
        self.assertTrue(
            OW._is_migration_v3_worker("migration-v3-60-frontmatter-spring")
        )
        self.assertTrue(
            OW._is_migration_v3_worker("migration-v3-60-new-mission-bridge-roomescape")
        )

    def test_non_migration_worker_not_caught(self):
        self.assertFalse(OW._is_migration_v3_worker("expansion60-spring-di-bean"))


if __name__ == "__main__":
    unittest.main()
