from __future__ import annotations

import sqlite3
from pathlib import Path


BOT_USERS = frozenset({
    "coderabbitai",
    "github-actions[bot]",
    "dependabot[bot]",
    "codecov[bot]",
    "sonarcloud[bot]",
})


def _has_column(connection: sqlite3.Connection, table: str, column: str) -> bool:
    return any(
        row[1] == column
        for row in connection.execute(f"PRAGMA table_info({table})")
    )


def _ensure_column(connection: sqlite3.Connection, table: str, column: str, col_type: str = "TEXT") -> bool:
    if _has_column(connection, table, column):
        return False
    connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
    return True


def _pr_author_map(connection: sqlite3.Connection) -> dict[int, str]:
    rows = connection.execute(
        "SELECT id, author_login FROM pull_requests_current WHERE is_missing = 0"
    ).fetchall()
    return {row[0]: row[1] for row in rows}


def classify_review_comments(db_path: str | Path) -> dict:
    db_path = Path(db_path)
    if not db_path.exists():
        return {"classified": 0, "skipped": True, "reason": "db not found"}

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        _ensure_column(connection, "pull_request_review_comments_current", "comment_role")
        connection.commit()

        pr_authors = _pr_author_map(connection)

        comments = connection.execute("""
            SELECT id, pull_request_id, user_login, in_reply_to_github_comment_id, github_comment_id
            FROM pull_request_review_comments_current
            WHERE is_missing = 0
        """).fetchall()

        comment_map: dict[int, dict] = {}
        for c in comments:
            comment_map[c["github_comment_id"]] = {
                "id": c["id"],
                "pull_request_id": c["pull_request_id"],
                "user_login": c["user_login"],
                "in_reply_to": c["in_reply_to_github_comment_id"],
            }

        updates: list[tuple[str, int]] = []
        for c in comments:
            user = (c["user_login"] or "").lower()
            pr_author = (pr_authors.get(c["pull_request_id"]) or "").lower()
            in_reply_to = c["in_reply_to_github_comment_id"]

            if user in BOT_USERS or user.endswith("[bot]"):
                role = "bot"
            elif in_reply_to is None:
                role = "crew_self_original" if user == pr_author else "mentor_original"
            else:
                is_pr_author = user == pr_author
                if is_pr_author:
                    role = "crew_self_reply"
                else:
                    parent = comment_map.get(in_reply_to)
                    parent_is_crew = False
                    if parent:
                        parent_user = (parent["user_login"] or "").lower()
                        parent_pr_author = (pr_authors.get(parent["pull_request_id"]) or "").lower()
                        parent_is_crew = parent_user == parent_pr_author
                    role = "mentor_followup" if parent_is_crew else "mentor_original"

            updates.append((role, c["id"]))

        connection.executemany(
            "UPDATE pull_request_review_comments_current SET comment_role = ? WHERE id = ?",
            updates,
        )
        connection.commit()

        counts: dict[str, int] = {}
        for role, _ in updates:
            counts[role] = counts.get(role, 0) + 1

        return {"classified": len(updates), "counts": counts}
    finally:
        connection.close()


def classify_review_bodies(db_path: str | Path) -> dict:
    db_path = Path(db_path)
    if not db_path.exists():
        return {"classified": 0, "skipped": True, "reason": "db not found"}

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        _ensure_column(connection, "pull_request_reviews_current", "reviewer_role")
        connection.commit()

        pr_authors = _pr_author_map(connection)

        reviews = connection.execute("""
            SELECT id, pull_request_id, reviewer_login
            FROM pull_request_reviews_current
            WHERE is_missing = 0
        """).fetchall()

        updates: list[tuple[str, int]] = []
        for r in reviews:
            user = (r["reviewer_login"] or "").lower()
            pr_author = (pr_authors.get(r["pull_request_id"]) or "").lower()

            if user in BOT_USERS or user.endswith("[bot]"):
                role = "bot"
            elif user == pr_author:
                role = "self"
            else:
                role = "mentor"

            updates.append((role, r["id"]))

        connection.executemany(
            "UPDATE pull_request_reviews_current SET reviewer_role = ? WHERE id = ?",
            updates,
        )
        connection.commit()

        counts: dict[str, int] = {}
        for role, _ in updates:
            counts[role] = counts.get(role, 0) + 1

        return {"classified": len(updates), "counts": counts}
    finally:
        connection.close()


def classify_issue_comments(db_path: str | Path) -> dict:
    db_path = Path(db_path)
    if not db_path.exists():
        return {"classified": 0, "skipped": True, "reason": "db not found"}

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        _ensure_column(connection, "pull_request_issue_comments_current", "comment_role")
        connection.commit()

        pr_authors = _pr_author_map(connection)

        comments = connection.execute("""
            SELECT id, pull_request_id, user_login
            FROM pull_request_issue_comments_current
            WHERE is_missing = 0
        """).fetchall()

        updates: list[tuple[str, int]] = []
        for c in comments:
            user = (c["user_login"] or "").lower()
            pr_author = (pr_authors.get(c["pull_request_id"]) or "").lower()

            if user in BOT_USERS or user.endswith("[bot]"):
                role = "bot"
            elif user == pr_author:
                role = "self"
            else:
                role = "mentor"

            updates.append((role, c["id"]))

        connection.executemany(
            "UPDATE pull_request_issue_comments_current SET comment_role = ? WHERE id = ?",
            updates,
        )
        connection.commit()

        counts: dict[str, int] = {}
        for role, _ in updates:
            counts[role] = counts.get(role, 0) + 1

        return {"classified": len(updates), "counts": counts}
    finally:
        connection.close()


def classify_all(db_path: str | Path) -> dict:
    return {
        "review_comments": classify_review_comments(db_path),
        "review_bodies": classify_review_bodies(db_path),
        "issue_comments": classify_issue_comments(db_path),
    }
