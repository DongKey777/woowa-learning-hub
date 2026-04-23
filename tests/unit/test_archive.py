"""Direct unit coverage for ``scripts.workbench.core.archive``.

Patches the disk-mapping seams (``repo_archive_db``, ``ensure_repo_layout``,
``write_mission_map``, ``classify_all``, ``run_capture``) in the ``archive``
module namespace so each test runs against a tmp-path SQLite DB seeded
inline with the actual schema column names from the production code.

Schema reference: archive.py:67-99 reads ``pull_requests_current``,
``pull_request_reviews_current``, ``pull_request_review_comments_current``;
archive.py:322-365 reads ``collection_runs`` and ``collection_run_failures``.

data_confidence enum: ``ready`` / ``partial`` / ``bootstrap`` only
(archive.py:148).
"""

from __future__ import annotations

import sqlite3
import subprocess
import unittest
from contextlib import ExitStack
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import mock

from scripts.workbench.core import archive as ar


# ---------------------------------------------------------------------------
# DB seeding helpers — minimal CREATE TABLE statements covering only the
# columns the archive module actually queries.
# ---------------------------------------------------------------------------

_SCHEMA_DDL = """
CREATE TABLE pull_requests_current (
    id INTEGER PRIMARY KEY,
    is_missing INTEGER NOT NULL DEFAULT 0,
    created_at TEXT
);

CREATE TABLE pull_request_reviews_current (
    id INTEGER PRIMARY KEY,
    pull_request_id INTEGER
);

CREATE TABLE pull_request_review_comments_current (
    id INTEGER PRIMARY KEY,
    pull_request_id INTEGER
);

CREATE TABLE collection_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mode TEXT,
    started_at TEXT,
    finished_at TEXT,
    success INTEGER,
    pr_count INTEGER,
    notes TEXT
);

CREATE TABLE collection_run_failures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    collection_run_id INTEGER,
    github_pr_number INTEGER,
    stage TEXT,
    error_message TEXT,
    created_at TEXT
);
"""


def _init_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.executescript(_SCHEMA_DDL)
        conn.commit()
    finally:
        conn.close()


def _seed_db(
    path: Path,
    *,
    prs: int = 0,
    pr_review_coverage: int = 0,
    runs: list[dict] | None = None,
    failures: list[dict] | None = None,
) -> None:
    """Populate the seeded DB.

    ``pr_review_coverage`` controls how many of the ``prs`` rows get a
    matching review row (covers the ``prs_with_review_activity`` count).
    """
    _init_db(path)
    conn = sqlite3.connect(path)
    try:
        for i in range(1, prs + 1):
            conn.execute(
                "INSERT INTO pull_requests_current (id, is_missing, created_at) "
                "VALUES (?, 0, ?)",
                (i, "2026-01-01T00:00:00+00:00"),
            )
        for i in range(1, pr_review_coverage + 1):
            conn.execute(
                "INSERT INTO pull_request_reviews_current (id, pull_request_id) "
                "VALUES (?, ?)",
                (i, i),
            )
        for run in runs or []:
            conn.execute(
                "INSERT INTO collection_runs "
                "(id, mode, started_at, finished_at, success, pr_count, notes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    run["id"], run.get("mode", "incremental"),
                    run.get("started_at"), run.get("finished_at"),
                    1 if run.get("success") else 0,
                    run.get("pr_count", 0),
                    run.get("notes"),
                ),
            )
        for fail in failures or []:
            conn.execute(
                "INSERT INTO collection_run_failures "
                "(id, collection_run_id, github_pr_number, stage, "
                "error_message, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    fail["id"], fail.get("collection_run_id"),
                    fail.get("github_pr_number"), fail.get("stage"),
                    fail.get("error_message"), fail.get("created_at"),
                ),
            )
        conn.commit()
    finally:
        conn.close()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

class ArchiveTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.tmp = Path(self._tmp.name)
        self.db_path = self.tmp / "prs.sqlite3"
        self.repo_layout = self.tmp / "layout"
        (self.repo_layout / "archive").mkdir(parents=True, exist_ok=True)

    def _patch_paths(self, stack: ExitStack) -> None:
        stack.enter_context(
            mock.patch.object(ar, "repo_archive_db", return_value=self.db_path)
        )
        stack.enter_context(
            mock.patch.object(ar, "ensure_repo_layout", return_value=self.repo_layout)
        )

    # ---- compute_archive_status: ready / bootstrapping / uninitialized ----

    def test_compute_status_ready(self) -> None:
        _seed_db(
            self.db_path,
            prs=ar.MIN_PRS_FOR_READY + 5,
            pr_review_coverage=ar.MIN_PRS_FOR_READY,  # 100% coverage
            runs=[{"id": 1, "mode": "full", "finished_at": _now_iso(),
                   "success": True, "pr_count": ar.MIN_PRS_FOR_READY + 5}],
        )
        with ExitStack() as stack:
            self._patch_paths(stack)
            status = ar.compute_archive_status("demo-repo")

        self.assertEqual(status["bootstrap_state"], "ready")
        self.assertEqual(status["data_confidence"], "ready")

    def test_compute_status_bootstrapping_when_below_pr_threshold(self) -> None:
        _seed_db(
            self.db_path,
            prs=5,
            pr_review_coverage=5,
            runs=[{"id": 1, "mode": "full", "finished_at": _now_iso(),
                   "success": True, "pr_count": 5}],
        )
        with ExitStack() as stack:
            self._patch_paths(stack)
            status = ar.compute_archive_status("demo-repo")

        self.assertEqual(status["bootstrap_state"], "bootstrapping")
        self.assertEqual(status["data_confidence"], "partial")

    def test_compute_status_uninitialized_when_db_missing(self) -> None:
        # Note: no DB created at self.db_path
        with ExitStack() as stack:
            self._patch_paths(stack)
            status = ar.compute_archive_status("demo-repo")

        self.assertEqual(status["bootstrap_state"], "uninitialized")
        self.assertEqual(status["data_confidence"], "bootstrap")

    def test_compute_status_bootstrapping_when_low_review_coverage(self) -> None:
        _seed_db(
            self.db_path,
            prs=ar.MIN_PRS_FOR_READY + 10,
            pr_review_coverage=2,  # ratio = 2/30 << 0.4 threshold
            runs=[{"id": 1, "mode": "full", "finished_at": _now_iso(),
                   "success": True, "pr_count": ar.MIN_PRS_FOR_READY + 10}],
        )
        with ExitStack() as stack:
            self._patch_paths(stack)
            status = ar.compute_archive_status("demo-repo")

        self.assertEqual(status["bootstrap_state"], "bootstrapping")
        self.assertEqual(status["data_confidence"], "partial")

    # ---- latest_collection_run / latest_collection_failure ----

    def test_latest_collection_run_empty_db(self) -> None:
        # Missing DB → None
        self.assertIsNone(ar.latest_collection_run(self.db_path))

    def test_latest_collection_run_with_failures(self) -> None:
        _seed_db(
            self.db_path,
            prs=3, pr_review_coverage=0,
            runs=[
                {"id": 1, "mode": "full", "finished_at": _now_iso(),
                 "success": True, "pr_count": 3},
                {"id": 2, "mode": "incremental", "finished_at": _now_iso(),
                 "success": True, "pr_count": 4},
            ],
            failures=[
                {"id": 1, "collection_run_id": 2, "github_pr_number": 42,
                 "stage": "fetch", "error_message": "boom",
                 "created_at": _now_iso()},
            ],
        )
        latest = ar.latest_collection_run(self.db_path)
        self.assertIsNotNone(latest)
        # Latest run is id=2 (DESC) — failure attached to id=2.
        self.assertEqual(latest["failure_count"], 1)
        self.assertIsNotNone(latest["latest_failure"])
        self.assertEqual(latest["latest_failure"]["github_pr_number"], 42)
        self.assertEqual(latest["current_pr_count"], 3)

    def test_latest_collection_failure_filters_by_run_id(self) -> None:
        _seed_db(
            self.db_path,
            failures=[
                {"id": 1, "collection_run_id": 1, "github_pr_number": 10,
                 "stage": "fetch", "error_message": "old",
                 "created_at": _now_iso()},
                {"id": 2, "collection_run_id": 2, "github_pr_number": 20,
                 "stage": "fetch", "error_message": "new",
                 "created_at": _now_iso()},
            ],
        )
        # Without filter → returns most recent overall (id=2).
        latest = ar.latest_collection_failure(self.db_path)
        self.assertEqual(latest["github_pr_number"], 20)
        # Filtered to run 1 → returns the older one.
        scoped = ar.latest_collection_failure(self.db_path, collection_run_id=1)
        self.assertEqual(scoped["github_pr_number"], 10)

    def test_latest_collection_failure_missing_db(self) -> None:
        self.assertIsNone(ar.latest_collection_failure(self.db_path))

    # ---- sync_repo_archive: ArchiveSyncError on subprocess failure ----

    def test_sync_repo_archive_raises_on_subprocess_failure(self) -> None:
        _init_db(self.db_path)
        fake_completed = subprocess.CompletedProcess(
            args=["python3"], returncode=1,
            stdout="", stderr="explode",
        )
        with ExitStack() as stack:
            self._patch_paths(stack)
            stack.enter_context(
                mock.patch.object(ar, "run_capture", return_value=fake_completed)
            )
            stack.enter_context(
                mock.patch.object(
                    ar, "write_mission_map",
                    return_value={"json_path": str(self.tmp / "mm.json"),
                                  "analysis": {"retrieval_terms": ["a", "b"]}},
                )
            )
            stack.enter_context(
                mock.patch.object(ar, "classify_all", return_value={})
            )

            with self.assertRaises(ar.ArchiveSyncError) as ctx:
                ar.sync_repo_archive(
                    repo={"name": "demo-repo", "upstream": "owner/repo"},
                )

        err = ctx.exception
        self.assertEqual(err.stderr, "explode")
        self.assertIn("collect_prs.py", " ".join(err.command))
        d = err.to_dict()
        self.assertEqual(d["stderr"], "explode")

    def test_sync_repo_archive_success_path(self) -> None:
        _seed_db(
            self.db_path,
            prs=2, pr_review_coverage=2,
            runs=[{"id": 1, "mode": "full", "finished_at": _now_iso(),
                   "success": True, "pr_count": 2}],
        )
        ok_completed = subprocess.CompletedProcess(
            args=["python3"], returncode=0, stdout="ok\n", stderr="",
        )
        with ExitStack() as stack:
            self._patch_paths(stack)
            stack.enter_context(
                mock.patch.object(ar, "run_capture", return_value=ok_completed)
            )
            stack.enter_context(
                mock.patch.object(
                    ar, "write_mission_map",
                    return_value={"json_path": str(self.tmp / "mm.json"),
                                  "analysis": {"retrieval_terms": []}},
                )
            )
            stack.enter_context(
                mock.patch.object(ar, "classify_all", return_value={"ok": True})
            )

            result = ar.sync_repo_archive(
                repo={"name": "demo-repo", "upstream": "owner/repo"},
            )

        self.assertEqual(result["repo"], "demo-repo")
        self.assertEqual(result["classify_result"], {"ok": True})
        self.assertEqual(result["stdout"], "ok")

    # ---- ensure_repo_archive: allow_full=False, force=True ----

    def test_ensure_repo_archive_blocks_full_when_disallowed(self) -> None:
        # No DB → archive_sync_status reports recommended_mode="full".
        with ExitStack() as stack:
            self._patch_paths(stack)
            stack.enter_context(
                mock.patch.object(ar, "write_archive_status", return_value={})
            )
            sync_mock = stack.enter_context(
                mock.patch.object(ar, "sync_repo_archive")
            )

            result = ar.ensure_repo_archive(
                repo={"name": "demo-repo", "upstream": "owner/repo"},
                allow_full=False,
            )

        self.assertTrue(result["skipped"])
        self.assertTrue(result["full_sync_blocked"])
        sync_mock.assert_not_called()

    def test_ensure_repo_archive_skip_when_fresh(self) -> None:
        # Fresh archive → needs_sync False → ensure returns skipped without
        # calling sync_repo_archive.
        _seed_db(
            self.db_path,
            prs=1, pr_review_coverage=1,
            runs=[{"id": 1, "mode": "incremental", "finished_at": _now_iso(),
                   "success": True, "pr_count": 1}],
        )
        with ExitStack() as stack:
            self._patch_paths(stack)
            stack.enter_context(
                mock.patch.object(ar, "write_archive_status", return_value={})
            )
            sync_mock = stack.enter_context(
                mock.patch.object(ar, "sync_repo_archive")
            )

            result = ar.ensure_repo_archive(
                repo={"name": "demo-repo", "upstream": "owner/repo"},
            )

        self.assertTrue(result["skipped"])
        self.assertNotIn("full_sync_blocked", result)
        sync_mock.assert_not_called()

    def test_ensure_repo_archive_force_invokes_sync(self) -> None:
        _seed_db(
            self.db_path,
            prs=1, pr_review_coverage=1,
            runs=[{"id": 1, "mode": "incremental", "finished_at": _now_iso(),
                   "success": True, "pr_count": 1}],
        )
        with ExitStack() as stack:
            self._patch_paths(stack)
            stack.enter_context(
                mock.patch.object(ar, "write_archive_status", return_value={})
            )
            sync_mock = stack.enter_context(
                mock.patch.object(
                    ar, "sync_repo_archive",
                    return_value={"repo": "demo-repo", "classify_result": {}},
                )
            )

            result = ar.ensure_repo_archive(
                repo={"name": "demo-repo", "upstream": "owner/repo"},
                force=True,
            )

        sync_mock.assert_called_once()
        self.assertFalse(result["skipped"])


if __name__ == "__main__":
    unittest.main()
