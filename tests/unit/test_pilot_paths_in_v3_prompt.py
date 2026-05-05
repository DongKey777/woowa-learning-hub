"""The v3 migration worker prompt must inject the Pilot lock path
list filtered by the worker's lane globs.

Pre-fix the prompt only said *"read the file"*. LLM workers ignored
that pointer and freely modified Pilot 69 docs whenever a queue item
landed inside the lane glob, so the completion gate caught 11 Pilot
violations on the v3 migration cycle 2026-05-05. The fix is to bake
the actual filtered AVOID list into the prompt header so the model
has the exact paths in working memory.

These tests pin:

  * the helper filters Pilot paths down to lane-relevant ones
  * the v3 prompt header surfaces the AVOID block whenever the lane
    overlaps Pilot territory
  * lanes outside Pilot territory (qa-only, rag-only) get no block —
    so the prompt size doesn't bloat for workers that can never hit
    the issue
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from scripts.workbench.core import orchestrator_workers as OW


_FAKE_PILOT_PATHS = [
    "knowledge/cs/contents/network/latency-bandwidth-throughput-basics.md",
    "knowledge/cs/contents/network/request-timing-decomposition-dns.md",
    "knowledge/cs/contents/spring/spring-bean-di-basics.md",
    "knowledge/cs/contents/spring/spring-transaction-basics.md",
    "knowledge/cs/contents/database/connection-pool-basics.md",
]


class PilotPathsForLaneFilterTest(unittest.TestCase):
    def _patch_locked(self, paths):
        return mock.patch.object(OW, "_load_pilot_lock_paths", return_value=set(paths))

    def test_returns_empty_when_lock_missing(self) -> None:
        with self._patch_locked([]):
            self.assertEqual(
                OW._pilot_paths_for_lane(["knowledge/cs/contents/network/**"]),
                [],
            )

    def test_returns_empty_when_target_paths_empty(self) -> None:
        with self._patch_locked(_FAKE_PILOT_PATHS):
            self.assertEqual(OW._pilot_paths_for_lane([]), [])

    def test_filters_to_lane_glob(self) -> None:
        with self._patch_locked(_FAKE_PILOT_PATHS):
            result = OW._pilot_paths_for_lane(
                ["knowledge/cs/contents/network/**"],
            )
        self.assertEqual(
            result,
            [
                "knowledge/cs/contents/network/latency-bandwidth-throughput-basics.md",
                "knowledge/cs/contents/network/request-timing-decomposition-dns.md",
            ],
        )

    def test_no_match_for_unrelated_lane_glob(self) -> None:
        with self._patch_locked(_FAKE_PILOT_PATHS):
            self.assertEqual(
                OW._pilot_paths_for_lane(["state/orchestrator/reports/**"]),
                [],
            )

    def test_multi_glob_lane_unions_matches(self) -> None:
        with self._patch_locked(_FAKE_PILOT_PATHS):
            result = OW._pilot_paths_for_lane([
                "knowledge/cs/contents/spring/**",
                "knowledge/cs/contents/database/**",
            ])
        self.assertEqual(
            result,
            [
                "knowledge/cs/contents/database/connection-pool-basics.md",
                "knowledge/cs/contents/spring/spring-bean-di-basics.md",
                "knowledge/cs/contents/spring/spring-transaction-basics.md",
            ],
        )

    def test_recursive_glob_covers_nested_dirs(self) -> None:
        nested = [
            "knowledge/cs/contents/language/java/java-foo.md",
            "knowledge/cs/contents/spring/spring-foo.md",
        ]
        with self._patch_locked(nested):
            result = OW._pilot_paths_for_lane(["knowledge/cs/contents/**/*.md"])
        self.assertEqual(sorted(result), sorted(nested))


class V3PromptPilotInjectionTest(unittest.TestCase):
    """Render the v3 worker prompt and assert the AVOID block appears
    with the lane-filtered Pilot path list."""

    def _render(self, worker: str, lane: str) -> str:
        return OW._worker_prompt(
            worker, lane,
            {"item_id": "test-001", "title": "t", "goal": "g", "tags": []},
            fleet_profile="migration_v3_60",
        )

    def test_network_lane_lists_only_network_pilot_paths(self) -> None:
        with mock.patch.object(
            OW, "_load_pilot_lock_paths", return_value=set(_FAKE_PILOT_PATHS)
        ):
            prompt = self._render(
                "migration-v3-60-prefix-network",
                "migration-content-network",
            )
        self.assertIn("PILOT LOCK PATHS IN YOUR LANE — NEVER MODIFY", prompt)
        self.assertIn(
            "knowledge/cs/contents/network/latency-bandwidth-throughput-basics.md",
            prompt,
        )
        self.assertIn(
            "knowledge/cs/contents/network/request-timing-decomposition-dns.md",
            prompt,
        )
        # Spring / database paths must NOT leak into a network worker's prompt.
        self.assertNotIn(
            "knowledge/cs/contents/spring/spring-bean-di-basics.md",
            prompt,
        )
        self.assertNotIn(
            "knowledge/cs/contents/database/connection-pool-basics.md",
            prompt,
        )

    def test_no_avoid_block_when_no_pilot_in_lane(self) -> None:
        # rag-only lane has no overlap with knowledge/cs/contents.
        with mock.patch.object(
            OW, "_load_pilot_lock_paths", return_value=set(_FAKE_PILOT_PATHS)
        ):
            prompt = self._render(
                "migration-v3-60-rag-cohort-eval-gate",
                "migration-rag",
            )
        # Header still cites the file for transparency, but the
        # explicit AVOID list is omitted (lane has no overlap).
        self.assertNotIn("PILOT LOCK PATHS IN YOUR LANE", prompt)

    def test_no_avoid_block_when_lock_file_missing(self) -> None:
        with mock.patch.object(OW, "_load_pilot_lock_paths", return_value=set()):
            prompt = self._render(
                "migration-v3-60-prefix-network",
                "migration-content-network",
            )
        self.assertNotIn("PILOT LOCK PATHS IN YOUR LANE", prompt)

    def test_avoid_block_size_matches_filtered_count(self) -> None:
        with mock.patch.object(
            OW, "_load_pilot_lock_paths", return_value=set(_FAKE_PILOT_PATHS)
        ):
            prompt = self._render(
                "migration-v3-60-frontmatter-spring",
                "migration-content-spring",
            )
        # Spring lane has 2 fake pilot paths.
        self.assertIn("The following 2 doc(s) are inside your", prompt)
        self.assertIn("knowledge/cs/contents/spring/spring-bean-di-basics.md", prompt)
        self.assertIn("knowledge/cs/contents/spring/spring-transaction-basics.md", prompt)


class V3PromptPilotInjectionWithRealLockTest(unittest.TestCase):
    """Sanity check against the real lock file shipped in the repo —
    confirms that as of the test author's knowledge there are
    Pilot paths in network / spring / database lanes."""

    def test_real_lock_has_paths_in_network_spring_database(self) -> None:
        # If this test fails, the lock file's path roster has
        # changed shape. That's a design signal — review the
        # AVOID-block contract before silencing.
        for category in ("network", "spring", "database"):
            paths = OW._pilot_paths_for_lane(
                [f"knowledge/cs/contents/{category}/**"]
            )
            self.assertGreater(
                len(paths), 0,
                f"expected at least one Pilot path in {category} lane",
            )


if __name__ == "__main__":
    unittest.main()
