"""Phase 8 long-running balance — 편향 방지 가드 회귀.

migration_v3_60 fleet이 무한 운영 모드에서도 코퍼스 분포 균형을
유지하도록 만든 4가지 메커니즘을 검증:

  1. ``_v3_balance_snapshot`` — 동적 코퍼스 분포 (5분 캐시)
  2. ``_recent_cohort_eval_feedback`` — 최근 약점 cohort 추출
  3. ``_v3_saturation_ceilings_block`` — 카테고리당 doc_role 캡
  4. ``_anti_drift_next_candidates`` — migration mode에도 적용
  5. ``migrate_revisit`` mode — Wave D 품질 보강 loop closer
  6. balance-monitor 워커 — 정기 imbalance alarm
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from scripts.workbench.core import orchestrator_workers as OW


class V3BalanceSnapshotTest(unittest.TestCase):
    def test_snapshot_block_has_required_sections(self):
        block = OW._v3_balance_snapshot()
        for marker in (
            "v3 balance snapshot",
            "corpus total:",
            "v3 frontmatter coverage:",
            "contextual_chunk_prefix coverage:",
            "underweight cells",
            "saturated cells",
        ):
            self.assertIn(marker, block, f"missing marker: {marker!r}")

    def test_snapshot_cached_within_ttl(self):
        # First call populates cache, second returns same string
        # without re-walking the corpus tree.
        OW._V3_SNAPSHOT_CACHE.clear()
        first = OW._v3_balance_snapshot()
        # Even if files change between calls, within TTL the cache wins
        second = OW._v3_balance_snapshot()
        self.assertIs(first, second)


class CohortEvalFeedbackTest(unittest.TestCase):
    def test_feedback_block_extracts_weak_cohorts(self):
        # The repo has post_phase_9_3_active.json from the calibration
        # cycle; the feedback block must reference at least one of
        # the cohort tags from that JSON.
        block = OW._recent_cohort_eval_feedback()
        # Either feedback was loaded (cohort tags appear) OR no recent
        # eval was found and the block says so.
        if "no recent JSON found" in block:
            self.skipTest("no cohort_eval JSON in repo")
        self.assertIn("OVERALL:", block)
        self.assertIn("Weak cohorts", block)

    def test_missing_eval_file_returns_explanation(self):
        with mock.patch.object(
            OW, "ROOT", Path("/tmp/woowa-no-such-path-test"),
        ):
            block = OW._recent_cohort_eval_feedback()
        self.assertIn("no recent JSON found", block)


class SaturationCeilingsTest(unittest.TestCase):
    def test_block_lists_all_doc_roles(self):
        block = OW._v3_saturation_ceilings_block()
        for role in ("primer", "deep_dive", "playbook", "chooser",
                      "bridge", "drill", "symptom_router", "mission_bridge"):
            self.assertIn(role, block)

    def test_block_states_share_ceiling(self):
        block = OW._v3_saturation_ceilings_block()
        self.assertIn("60%", block)
        self.assertIn("saturated", block)


class MigrationPromptIncludesGuardTest(unittest.TestCase):
    """Each migration prompt mode must carry the long-running guard
    so codex sees live balance / cohort / saturation context per call."""

    def _prompt_for(self, worker, mode_dummy_lane="migration-content-spring"):
        return OW._worker_prompt(
            worker, mode_dummy_lane,
            {"item_id": "t", "title": "x", "goal": "y", "tags": []},
            fleet_profile="migration_v3_60",
        )

    def test_v0_to_v3_carries_guard(self):
        p = self._prompt_for("migration-v3-60-frontmatter-spring")
        self.assertIn("LONG-RUNNING BALANCE GUARD", p)
        self.assertIn("v3 balance snapshot", p)
        self.assertIn("Weak cohorts", p)
        self.assertIn("Saturation ceiling rules", p)

    def test_prefix_carries_guard(self):
        p = self._prompt_for("migration-v3-60-prefix-spring")
        self.assertIn("LONG-RUNNING BALANCE GUARD", p)

    def test_new_doc_carries_guard(self):
        p = self._prompt_for(
            "migration-v3-60-new-mission-bridge-roomescape",
            "migration-content-mission-bridge",
        )
        self.assertIn("LONG-RUNNING BALANCE GUARD", p)

    def test_revisit_mode_prompt_exists(self):
        p = self._prompt_for(
            "migration-v3-60-revisit-quality-deepen",
            "migration-content-revisit",
        )
        self.assertIn("WAVE D — existing-doc quality revisit", p)
        self.assertIn("aliases length", p)
        self.assertIn("forbidden_neighbors", p)


class AntiDriftV3CoverageTest(unittest.TestCase):
    """The anti-drift filter must trigger for all four migrate_* modes,
    not just legacy expansion mode."""

    def _profile(self, mode):
        return {"role": "migration", "mode": mode}

    def _candidate(self, *tags, title="next"):
        return {"title": title, "tags": list(tags)}

    def test_migrate_v0_to_v3_filter_active(self):
        item = {"tags": ["spring", "frontmatter", "v3"]}
        cands = [
            self._candidate("spring", "v3-prefix", "cohort-weak", title="ok-pivot"),
            self._candidate("spring", "frontmatter", "v3", title="same-cell"),
        ]
        out = OW._anti_drift_next_candidates(item, cands, self._profile("migrate_v0_to_v3"))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["title"], "ok-pivot")

    def test_migrate_prefix_filter_active(self):
        item = {"tags": ["database", "prefix", "wave-b"]}
        cands = [
            self._candidate("database", "v3-revisit", "balance-gap", title="ok"),
            self._candidate("database", "prefix", "wave-b", title="repeat"),
        ]
        out = OW._anti_drift_next_candidates(item, cands, self._profile("migrate_prefix"))
        self.assertEqual(len(out), 1)

    def test_migrate_new_doc_filter_active(self):
        item = {"tags": ["roomescape", "mission-bridge", "wave-c"]}
        cands = [
            self._candidate("baseball", "mission-bridge", "cohort-weak", title="next-mission"),
            self._candidate("roomescape", "mission-bridge", title="same-mission"),
        ]
        out = OW._anti_drift_next_candidates(item, cands, self._profile("migrate_new_doc"))
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["title"], "next-mission")

    def test_migrate_revisit_filter_active(self):
        item = {"tags": ["spring", "revisit", "wave-d"]}
        cands = [
            self._candidate("database", "revisit", "v3-revisit", title="next-cat"),
            self._candidate("spring", "revisit", "wave-d", title="same"),
        ]
        out = OW._anti_drift_next_candidates(item, cands, self._profile("migrate_revisit"))
        self.assertEqual(len(out), 1)

    def test_qa_mode_filter_inactive(self):
        """QA / RAG / Ops worker next_candidates are not anti-drift
        filtered (their job is repeated lint/rag invariants)."""
        item = {"tags": ["lint"]}
        cands = [
            self._candidate("lint", title="repeat"),
            self._candidate("lint", title="repeat-2"),
        ]
        qa_profile = {"role": "qa", "mode": "fix"}
        out = OW._anti_drift_next_candidates(item, cands, qa_profile)
        self.assertEqual(len(out), len(cands))


class V3DriftTagsRegisteredTest(unittest.TestCase):
    """Migration tags must be in the anti-drift accept list so a
    well-formed next_candidate isn't rejected for missing the tag
    signal."""

    def test_v3_tags_registered(self):
        for tag in ("v3-frontmatter", "v3-prefix", "v3-new-doc",
                    "v3-revisit", "cohort-weak", "mission-bridge",
                    "chooser", "symptom-router"):
            self.assertIn(tag, OW.ANTI_DRIFT_NEXT_CANDIDATE_TAGS)


class BalanceMonitorWorkerRegisteredTest(unittest.TestCase):
    from scripts.workbench.core import orchestrator_migration_workers as MW

    def test_balance_monitor_in_v3_60_fleet(self):
        from scripts.workbench.core import orchestrator_migration_workers as MW
        names = {w["name"] for w in MW.MIGRATION_V3_60_FLEET}
        self.assertIn("migration-v3-60-rag-balance-monitor", names)

    def test_revisit_worker_in_v3_60_fleet(self):
        from scripts.workbench.core import orchestrator_migration_workers as MW
        names = {w["name"] for w in MW.MIGRATION_V3_60_FLEET}
        self.assertIn("migration-v3-60-revisit-quality-deepen", names)

    def test_revisit_worker_uses_migrate_revisit_mode(self):
        from scripts.workbench.core import orchestrator_migration_workers as MW
        revisit = next(w for w in MW.MIGRATION_V3_60_FLEET
                       if w["name"] == "migration-v3-60-revisit-quality-deepen")
        self.assertEqual(revisit["mode"], "migrate_revisit")


if __name__ == "__main__":
    unittest.main()
