#!/usr/bin/env python3
"""Search archived PR data from the SQLite database."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


DEFAULT_DB_PATH = Path("catalog/pr-datasets/github-prs.sqlite3")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search archived PR data.")
    parser.add_argument("--query", required=True, help="FTS query text")
    parser.add_argument(
        "--scope",
        choices=("comments", "patches", "bodies"),
        default="comments",
        help="Search target",
    )
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with sqlite3.connect(args.db_path) as connection:
        connection.row_factory = sqlite3.Row
        rows = search(connection, args.scope, args.query, args.limit)
        for row in rows:
            print_row(args.scope, row)


def search(connection: sqlite3.Connection, scope: str, query: str, limit: int) -> list[sqlite3.Row]:
    if scope == "comments":
        return connection.execute(
            """
            SELECT
                pr.number,
                pr.title,
                c.path,
                c.line,
                c.user_login,
                c.body
            FROM review_comment_fts fts
            JOIN pull_request_review_comments_current c
              ON c.id = fts.review_comment_id
            JOIN pull_requests_current pr
              ON pr.id = c.pull_request_id
            WHERE review_comment_fts MATCH ?
            ORDER BY pr.number DESC
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()

    if scope == "patches":
        return connection.execute(
            """
            SELECT
                pr.number,
                pr.title,
                f.path,
                f.patch_text
            FROM patch_fts fts
            JOIN pull_request_files_current f
              ON f.id = fts.pull_request_file_id
            JOIN pull_requests_current pr
              ON pr.id = f.pull_request_id
            WHERE patch_fts MATCH ?
            ORDER BY pr.number DESC
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()

    return connection.execute(
        """
        SELECT
            pr.number,
            pr.title,
            pr.body
        FROM pr_body_fts fts
        JOIN pull_requests_current pr
          ON pr.id = fts.pull_request_id
        WHERE pr_body_fts MATCH ?
        ORDER BY pr.number DESC
        LIMIT ?
        """,
        (query, limit),
    ).fetchall()


def print_row(scope: str, row: sqlite3.Row) -> None:
    if scope == "comments":
        print(f"PR #{row['number']} | {row['title']}")
        print(f"  file: {row['path']}:{row['line']} | user: {row['user_login']}")
        print(f"  body: {row['body']}")
        print()
        return

    if scope == "patches":
        print(f"PR #{row['number']} | {row['title']}")
        print(f"  file: {row['path']}")
        print("  patch:")
        print(row["patch_text"] or "")
        print()
        return

    print(f"PR #{row['number']} | {row['title']}")
    print("  body:")
    print(row["body"] or "")
    print()


if __name__ == "__main__":
    main()
