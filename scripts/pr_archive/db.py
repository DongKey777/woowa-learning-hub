#!/usr/bin/env python3
"""SQLite helpers for PR archive collection."""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from typing import Any


class ArchiveDatabase:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path

    def connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def initialize_schema(self, schema_path: Path) -> None:
        with self.connect() as connection:
            connection.executescript(schema_path.read_text())

    def upsert_repository(
            self,
            owner: str,
            name: str,
            full_name: str,
            track: str | None,
            mission_name: str | None,
            source_type: str = "github-pr",
    ) -> int:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO repositories(owner, name, full_name, track, mission_name, source_type)
                VALUES(?, ?, ?, ?, ?, ?)
                ON CONFLICT(full_name) DO UPDATE SET
                    track = excluded.track,
                    mission_name = excluded.mission_name,
                    source_type = excluded.source_type,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (owner, name, full_name, track, mission_name, source_type),
            )
            row = connection.execute(
                "SELECT id FROM repositories WHERE full_name = ?",
                (full_name,),
            ).fetchone()
            return row["id"]

    def start_collection_run(self, repository_id: int, mode: str, started_at: str) -> int:
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO collection_runs(repository_id, mode, started_at)
                VALUES(?, ?, ?)
                """,
                (repository_id, mode, started_at),
            )
            return cursor.lastrowid

    def finish_collection_run(
            self,
            collection_run_id: int,
            finished_at: str,
            success: bool,
            pr_count: int,
            notes: str = "",
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                UPDATE collection_runs
                SET finished_at = ?, success = ?, pr_count = ?, notes = ?
                WHERE id = ?
                """,
                (finished_at, int(success), pr_count, notes, collection_run_id),
            )

    def record_failure(
            self,
            collection_run_id: int,
            github_pr_number: int,
            stage: str,
            error_message: str,
    ) -> None:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO collection_run_failures(collection_run_id, github_pr_number, stage, error_message)
                VALUES(?, ?, ?, ?)
                """,
                (collection_run_id, github_pr_number, stage, error_message),
            )

    def mark_pull_requests_missing(self, repository_id: int) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE pull_requests_current SET is_missing = 1 WHERE repository_id = ?",
                (repository_id,),
            )

    def mark_pr_children_missing(self, pull_request_id: int) -> None:
        with self.connect() as connection:
            connection.execute(
                "UPDATE pull_request_files_current SET is_missing = 1 WHERE pull_request_id = ?",
                (pull_request_id,),
            )
            connection.execute(
                "UPDATE pull_request_reviews_current SET is_missing = 1 WHERE pull_request_id = ?",
                (pull_request_id,),
            )
            connection.execute(
                "UPDATE pull_request_review_comments_current SET is_missing = 1 WHERE pull_request_id = ?",
                (pull_request_id,),
            )
            connection.execute(
                "UPDATE pull_request_issue_comments_current SET is_missing = 1 WHERE pull_request_id = ?",
                (pull_request_id,),
            )

    def upsert_pull_request(
            self,
            repository_id: int,
            pr: dict[str, Any],
            collected_at: str,
    ) -> int:
        body = pr.get("body") or ""
        body_hash = self._hash_text(body)

        with self.connect() as connection:
            existing = connection.execute(
                "SELECT id, body, head_sha, state, mergeable, mergeable_state FROM pull_requests_current WHERE github_pr_id = ?",
                (pr["id"],),
            ).fetchone()

            connection.execute(
                """
                INSERT INTO pull_requests_current(
                    repository_id, github_pr_id, number, title, body, state, author_login,
                    base_ref_name, head_ref_name, head_sha, mergeable, mergeable_state,
                    changed_files, commits_count, additions, deletions,
                    issue_comments_count, review_comments_count,
                    created_at, updated_at, closed_at, merged_at, html_url,
                    last_collected_at, last_seen_at, is_missing
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(github_pr_id) DO UPDATE SET
                    repository_id = excluded.repository_id,
                    number = excluded.number,
                    title = excluded.title,
                    body = excluded.body,
                    state = excluded.state,
                    author_login = excluded.author_login,
                    base_ref_name = excluded.base_ref_name,
                    head_ref_name = excluded.head_ref_name,
                    head_sha = excluded.head_sha,
                    mergeable = excluded.mergeable,
                    mergeable_state = excluded.mergeable_state,
                    changed_files = excluded.changed_files,
                    commits_count = excluded.commits_count,
                    additions = excluded.additions,
                    deletions = excluded.deletions,
                    issue_comments_count = excluded.issue_comments_count,
                    review_comments_count = excluded.review_comments_count,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at,
                    closed_at = excluded.closed_at,
                    merged_at = excluded.merged_at,
                    html_url = excluded.html_url,
                    last_collected_at = excluded.last_collected_at,
                    last_seen_at = excluded.last_seen_at,
                    is_missing = 0
                """,
                (
                    repository_id,
                    pr["id"],
                    pr["number"],
                    pr["title"],
                    body,
                    pr["state"],
                    pr["user"]["login"],
                    pr.get("base", {}).get("ref"),
                    pr.get("head", {}).get("ref"),
                    pr.get("head", {}).get("sha"),
                    None if pr.get("mergeable") is None else int(pr["mergeable"]),
                    pr.get("mergeable_state"),
                    pr.get("changed_files"),
                    pr.get("commits"),
                    pr.get("additions"),
                    pr.get("deletions"),
                    pr.get("comments"),
                    pr.get("review_comments"),
                    pr.get("created_at"),
                    pr.get("updated_at"),
                    pr.get("closed_at"),
                    pr.get("merged_at"),
                    pr.get("html_url"),
                    collected_at,
                    collected_at,
                ),
            )

            current = connection.execute(
                "SELECT id, body, head_sha, state, mergeable, mergeable_state FROM pull_requests_current WHERE github_pr_id = ?",
                (pr["id"],),
            ).fetchone()
            pull_request_id = current["id"]

            if existing is None or self._hash_text(existing["body"] or "") != body_hash:
                connection.execute(
                    """
                    INSERT INTO pull_request_body_history(pull_request_id, body, body_hash, captured_at)
                    VALUES(?, ?, ?, ?)
                    """,
                    (pull_request_id, body, body_hash, collected_at),
                )

            if existing is None or existing["head_sha"] != pr.get("head", {}).get("sha"):
                connection.execute(
                    """
                    INSERT INTO pull_request_head_history(pull_request_id, head_sha, captured_at)
                    VALUES(?, ?, ?)
                    """,
                    (pull_request_id, pr.get("head", {}).get("sha"), collected_at),
                )

            if (
                existing is None
                or existing["state"] != pr["state"]
                or existing["mergeable"] != (None if pr.get("mergeable") is None else int(pr["mergeable"]))
                or existing["mergeable_state"] != pr.get("mergeable_state")
            ):
                connection.execute(
                    """
                    INSERT INTO pull_request_state_history(pull_request_id, state, mergeable, mergeable_state, captured_at)
                    VALUES(?, ?, ?, ?, ?)
                    """,
                    (
                        pull_request_id,
                        pr["state"],
                        None if pr.get("mergeable") is None else int(pr["mergeable"]),
                        pr.get("mergeable_state"),
                        collected_at,
                    ),
                )

            connection.execute(
                "INSERT OR REPLACE INTO pr_body_fts(rowid, pull_request_id, title, body) VALUES(?, ?, ?, ?)",
                (pull_request_id, pull_request_id, pr["title"], body),
            )
            return pull_request_id

    def upsert_pull_request_file(
            self,
            pull_request_id: int,
            file_data: dict[str, Any],
            collected_at: str,
    ) -> int:
        patch_text = file_data.get("patch")
        patch_hash = self._hash_text(patch_text or "")
        is_binary = 1 if patch_text is None else 0

        with self.connect() as connection:
            existing = connection.execute(
                "SELECT id, patch_hash FROM pull_request_files_current WHERE pull_request_id = ? AND path = ?",
                (pull_request_id, file_data["filename"]),
            ).fetchone()

            connection.execute(
                """
                INSERT INTO pull_request_files_current(
                    pull_request_id, path, previous_filename, status, additions, deletions, changes_count,
                    patch_text, patch_hash, is_binary, last_collected_at, last_seen_at, is_missing
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(pull_request_id, path) DO UPDATE SET
                    previous_filename = excluded.previous_filename,
                    status = excluded.status,
                    additions = excluded.additions,
                    deletions = excluded.deletions,
                    changes_count = excluded.changes_count,
                    patch_text = excluded.patch_text,
                    patch_hash = excluded.patch_hash,
                    is_binary = excluded.is_binary,
                    last_collected_at = excluded.last_collected_at,
                    last_seen_at = excluded.last_seen_at,
                    is_missing = 0
                """,
                (
                    pull_request_id,
                    file_data["filename"],
                    file_data.get("previous_filename"),
                    file_data.get("status"),
                    file_data.get("additions"),
                    file_data.get("deletions"),
                    file_data.get("changes"),
                    patch_text,
                    patch_hash,
                    is_binary,
                    collected_at,
                    collected_at,
                ),
            )

            current = connection.execute(
                "SELECT id, patch_hash FROM pull_request_files_current WHERE pull_request_id = ? AND path = ?",
                (pull_request_id, file_data["filename"]),
            ).fetchone()
            pull_request_file_id = current["id"]

            if patch_text and (existing is None or existing["patch_hash"] != patch_hash):
                connection.execute(
                    """
                    INSERT INTO pull_request_file_patch_history(
                        pull_request_file_current_id, patch_text, patch_hash, captured_at
                    )
                    VALUES(?, ?, ?, ?)
                    """,
                    (pull_request_file_id, patch_text, patch_hash, collected_at),
                )

            if patch_text:
                connection.execute(
                    "INSERT OR REPLACE INTO patch_fts(rowid, pull_request_file_id, path, patch_text) VALUES(?, ?, ?, ?)",
                    (pull_request_file_id, pull_request_file_id, file_data["filename"], patch_text),
                )
            return pull_request_file_id

    def upsert_review(
            self,
            pull_request_id: int,
            review: dict[str, Any],
            collected_at: str,
    ) -> int:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO pull_request_reviews_current(
                    pull_request_id, github_review_id, reviewer_login, state, body, submitted_at,
                    commit_id, last_collected_at, last_seen_at, is_missing
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(github_review_id) DO UPDATE SET
                    pull_request_id = excluded.pull_request_id,
                    reviewer_login = excluded.reviewer_login,
                    state = excluded.state,
                    body = excluded.body,
                    submitted_at = excluded.submitted_at,
                    commit_id = excluded.commit_id,
                    last_collected_at = excluded.last_collected_at,
                    last_seen_at = excluded.last_seen_at,
                    is_missing = 0
                """,
                (
                    pull_request_id,
                    review["id"],
                    review["user"]["login"],
                    review["state"],
                    review.get("body"),
                    review.get("submitted_at"),
                    review.get("commit_id"),
                    collected_at,
                    collected_at,
                ),
            )
            row = connection.execute(
                "SELECT id FROM pull_request_reviews_current WHERE github_review_id = ?",
                (review["id"],),
            ).fetchone()
            return row["id"]

    def upsert_review_comment(
            self,
            pull_request_id: int,
            comment: dict[str, Any],
            collected_at: str,
    ) -> int:
        body = comment.get("body") or ""
        body_hash = self._hash_text(body)

        with self.connect() as connection:
            existing = connection.execute(
                "SELECT id, body FROM pull_request_review_comments_current WHERE github_comment_id = ?",
                (comment["id"],),
            ).fetchone()

            connection.execute(
                """
                INSERT INTO pull_request_review_comments_current(
                    pull_request_id, github_review_id, github_comment_id, user_login, path, position,
                    original_position, line, original_line, start_line, side, start_side, commit_id,
                    original_commit_id, in_reply_to_github_comment_id, diff_hunk, body, created_at, updated_at,
                    html_url, last_collected_at, last_seen_at, is_missing
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(github_comment_id) DO UPDATE SET
                    pull_request_id = excluded.pull_request_id,
                    github_review_id = excluded.github_review_id,
                    user_login = excluded.user_login,
                    path = excluded.path,
                    position = excluded.position,
                    original_position = excluded.original_position,
                    line = excluded.line,
                    original_line = excluded.original_line,
                    start_line = excluded.start_line,
                    side = excluded.side,
                    start_side = excluded.start_side,
                    commit_id = excluded.commit_id,
                    original_commit_id = excluded.original_commit_id,
                    in_reply_to_github_comment_id = excluded.in_reply_to_github_comment_id,
                    diff_hunk = excluded.diff_hunk,
                    body = excluded.body,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at,
                    html_url = excluded.html_url,
                    last_collected_at = excluded.last_collected_at,
                    last_seen_at = excluded.last_seen_at,
                    is_missing = 0
                """,
                (
                    pull_request_id,
                    comment.get("pull_request_review_id"),
                    comment["id"],
                    comment["user"]["login"],
                    comment.get("path"),
                    comment.get("position"),
                    comment.get("original_position"),
                    comment.get("line"),
                    comment.get("original_line"),
                    comment.get("start_line"),
                    comment.get("side"),
                    comment.get("start_side"),
                    comment.get("commit_id"),
                    comment.get("original_commit_id"),
                    comment.get("in_reply_to_id"),
                    comment.get("diff_hunk"),
                    body,
                    comment.get("created_at"),
                    comment.get("updated_at"),
                    comment.get("html_url"),
                    collected_at,
                    collected_at,
                ),
            )

            current = connection.execute(
                "SELECT id, body FROM pull_request_review_comments_current WHERE github_comment_id = ?",
                (comment["id"],),
            ).fetchone()
            review_comment_id = current["id"]

            if existing is None or self._hash_text(existing["body"] or "") != body_hash:
                connection.execute(
                    """
                    INSERT INTO pull_request_review_comment_body_history(
                        review_comment_current_id, body, body_hash, captured_at
                    )
                    VALUES(?, ?, ?, ?)
                    """,
                    (review_comment_id, body, body_hash, collected_at),
                )

            connection.execute(
                "INSERT OR REPLACE INTO review_comment_fts(rowid, review_comment_id, path, body, diff_hunk) VALUES(?, ?, ?, ?, ?)",
                (review_comment_id, review_comment_id, comment.get("path"), body, comment.get("diff_hunk")),
            )
            return review_comment_id

    def upsert_issue_comment(
            self,
            pull_request_id: int,
            comment: dict[str, Any],
            collected_at: str,
    ) -> int:
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO pull_request_issue_comments_current(
                    pull_request_id, github_comment_id, user_login, body, created_at,
                    updated_at, html_url, last_collected_at, last_seen_at, is_missing
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                ON CONFLICT(github_comment_id) DO UPDATE SET
                    pull_request_id = excluded.pull_request_id,
                    user_login = excluded.user_login,
                    body = excluded.body,
                    created_at = excluded.created_at,
                    updated_at = excluded.updated_at,
                    html_url = excluded.html_url,
                    last_collected_at = excluded.last_collected_at,
                    last_seen_at = excluded.last_seen_at,
                    is_missing = 0
                """,
                (
                    pull_request_id,
                    comment["id"],
                    comment["user"]["login"],
                    comment.get("body"),
                    comment.get("created_at"),
                    comment.get("updated_at"),
                    comment.get("html_url"),
                    collected_at,
                    collected_at,
                ),
            )
            row = connection.execute(
                "SELECT id FROM pull_request_issue_comments_current WHERE github_comment_id = ?",
                (comment["id"],),
            ).fetchone()
            return row["id"]

    def _hash_text(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
