"""Idempotency + correctness tests for `migrate_from_repos`.

Legacy per-repo `state/repos/<repo>/memory/history.jsonl` entries are
mapped to v3 `coach_run` events. Re-running the migration must NOT
duplicate events, even when called multiple times.
"""

from __future__ import annotations

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

from core import concept_catalog, learner_memory  # noqa: E402


LEGACY_ENTRY_TEMPLATE = {
    "entry_type": "learning_memory_entry",
    "repo": "spring-roomescape-admin",
    "mode": "coach",
    "created_at": "2026-04-20T10:00:00+00:00",
    "prompt": "트랜잭션 어떻게?",
    "question_fingerprint": "트랜잭션 어떻게",
    "diff_fingerprint": None,
    "primary_intent": "deepen",
    "primary_topic": "transaction",
    "primary_learning_points": ["transaction_consistency"],
    "learning_point_recommendations": [
        {
            "learning_point": "transaction_consistency",
            "label": "트랜잭션/정합성",
            "primary_candidate": {"pr_number": 42, "title": "Add tx"},
        }
    ],
    "reviewer": "mentor-x",
    "current_pr": {"number": 7},
    "summary": ["트랜잭션 경계가 흩어져 있다"],
    "answer": ["서비스 단에서 트랜잭션을 잡는 게 좋다"],
    "follow_up_question": "어떤 단위로 잡을까?",
    "next_action_titles": [],
    "evidence_highlights": [],
}


class MigrationIdempotencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        tmp_root = Path(self.tmp.name)
        self.learner_dir = tmp_root / "learner"
        self.learner_dir.mkdir(parents=True, exist_ok=True)
        self.repos_root = tmp_root / "repos"

        history = self.learner_dir / "history.jsonl"
        profile = self.learner_dir / "profile.json"
        summary = self.learner_dir / "summary.json"
        identity = self.learner_dir / "identity.json"
        self.history_path = history

        prev_env = os.environ.get("WOOWA_LEARNER_ID")
        os.environ["WOOWA_LEARNER_ID"] = "migrate-tester"

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

    def _seed_legacy_history(self, repo: str, entries: list[dict]) -> Path:
        repo_dir = self.repos_root / repo / "memory"
        repo_dir.mkdir(parents=True, exist_ok=True)
        history = repo_dir / "history.jsonl"
        with history.open("w", encoding="utf-8") as fh:
            for entry in entries:
                fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return history

    def _entries(self) -> list[dict]:
        if not self.history_path.exists():
            return []
        return [
            json.loads(line)
            for line in self.history_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def test_migration_imports_legacy_entry(self) -> None:
        self._seed_legacy_history("spring-roomescape-admin", [LEGACY_ENTRY_TEMPLATE])
        result = learner_memory.migrate_from_repos(self.repos_root)
        self.assertEqual(result["migrated"], 1)
        self.assertEqual(result["skipped_duplicates"], 0)
        events = self._entries()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["event_type"], "coach_run")
        self.assertEqual(events[0]["ts"], LEGACY_ENTRY_TEMPLATE["created_at"])
        self.assertEqual(events[0]["pr_number"], 7)
        self.assertEqual(events[0]["repo_context"], "spring-roomescape-admin")
        # learning_point → concept_id cross-mapping
        self.assertIn("concept:spring/transactional", events[0]["concept_ids"])
        # Audit metadata preserved
        self.assertIn("source_path", events[0])
        self.assertEqual(events[0]["source_line"], 1)

    def test_migration_is_idempotent_on_second_run(self) -> None:
        self._seed_legacy_history("spring-roomescape-admin", [LEGACY_ENTRY_TEMPLATE])
        first = learner_memory.migrate_from_repos(self.repos_root)
        second = learner_memory.migrate_from_repos(self.repos_root)
        self.assertEqual(first["migrated"], 1)
        self.assertEqual(second["migrated"], 0)
        self.assertEqual(second["skipped_duplicates"], 1)
        self.assertEqual(len(self._entries()), 1)

    def test_migration_preserves_chronological_order(self) -> None:
        e1 = dict(LEGACY_ENTRY_TEMPLATE, created_at="2026-04-21T09:00:00+00:00", prompt="early")
        e2 = dict(LEGACY_ENTRY_TEMPLATE, created_at="2026-04-22T09:00:00+00:00", prompt="middle")
        e3 = dict(LEGACY_ENTRY_TEMPLATE, created_at="2026-04-23T09:00:00+00:00", prompt="late")
        # Stored out of order intentionally to test sort.
        self._seed_legacy_history("spring-roomescape-admin", [e3, e1, e2])
        learner_memory.migrate_from_repos(self.repos_root)
        events = self._entries()
        self.assertEqual([e["prompt"] for e in events], ["early", "middle", "late"])

    def test_migration_handles_multiple_repos(self) -> None:
        self._seed_legacy_history(
            "spring-roomescape-admin",
            [dict(LEGACY_ENTRY_TEMPLATE, created_at="2026-04-21T08:00:00+00:00", prompt="A")],
        )
        self._seed_legacy_history(
            "spring-roomescape",
            [dict(LEGACY_ENTRY_TEMPLATE, repo="spring-roomescape", created_at="2026-04-22T08:00:00+00:00", prompt="B")],
        )
        result = learner_memory.migrate_from_repos(self.repos_root)
        self.assertEqual(result["repos_visited"], 2)
        self.assertEqual(result["migrated"], 2)
        events = self._entries()
        repos = {e["repo_context"] for e in events}
        self.assertEqual(repos, {"spring-roomescape-admin", "spring-roomescape"})

    def test_migration_dedupes_when_some_already_present(self) -> None:
        self._seed_legacy_history("spring-roomescape-admin", [LEGACY_ENTRY_TEMPLATE])
        learner_memory.migrate_from_repos(self.repos_root)
        # Add a NEW entry to the legacy history.
        new_entry = dict(LEGACY_ENTRY_TEMPLATE, created_at="2026-04-24T10:00:00+00:00", prompt="새 질문")
        self._seed_legacy_history("spring-roomescape-admin", [LEGACY_ENTRY_TEMPLATE, new_entry])
        second = learner_memory.migrate_from_repos(self.repos_root)
        self.assertEqual(second["migrated"], 1)  # only the new one
        self.assertEqual(second["skipped_duplicates"], 1)
        self.assertEqual(len(self._entries()), 2)

    def test_missing_state_repos_returns_zero_counts(self) -> None:
        result = learner_memory.migrate_from_repos(self.repos_root)
        self.assertEqual(result, {"migrated": 0, "skipped_duplicates": 0, "repos_visited": 0})


if __name__ == "__main__":
    unittest.main()
