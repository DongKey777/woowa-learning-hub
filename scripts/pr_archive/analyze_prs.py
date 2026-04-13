#!/usr/bin/env python3
"""Analyze archived PR data for learning."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


DEFAULT_DB_PATH = Path("catalog/pr-datasets/github-prs.sqlite3")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze archived PR data.")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)

    subparsers = parser.add_subparsers(dest="command", required=True)

    reviewer_summary = subparsers.add_parser("reviewer-summary")
    reviewer_summary.add_argument("--limit", type=int, default=10)

    path_hotspots = subparsers.add_parser("path-hotspots")
    path_hotspots.add_argument("--limit", type=int, default=15)

    keyword_report = subparsers.add_parser("keyword-report")
    keyword_report.add_argument("--query", required=True)
    keyword_report.add_argument("--limit", type=int, default=10)

    pr_report = subparsers.add_parser("pr-report")
    pr_report.add_argument("--number", type=int, required=True)

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with sqlite3.connect(args.db_path) as connection:
        connection.row_factory = sqlite3.Row

        if args.command == "reviewer-summary":
            print_reviewer_summary(connection, args.limit)
            return

        if args.command == "path-hotspots":
            print_path_hotspots(connection, args.limit)
            return

        if args.command == "keyword-report":
            print_keyword_report(connection, args.query, args.limit)
            return

        if args.command == "pr-report":
            print_pr_report(connection, args.number)


def print_reviewer_summary(connection: sqlite3.Connection, limit: int) -> None:
    rows = connection.execute(
        """
        SELECT
            reviewer_login,
            COUNT(*) AS review_count,
            SUM(CASE WHEN state = 'APPROVED' THEN 1 ELSE 0 END) AS approved_count,
            SUM(CASE WHEN state = 'CHANGES_REQUESTED' THEN 1 ELSE 0 END) AS changes_requested_count,
            SUM(CASE WHEN state = 'COMMENTED' THEN 1 ELSE 0 END) AS commented_count
        FROM pull_request_reviews_current
        GROUP BY reviewer_login
        ORDER BY review_count DESC, reviewer_login
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    for row in rows:
        print(
            f"{row['reviewer_login']}: reviews={row['review_count']}, "
            f"approved={row['approved_count']}, "
            f"changes_requested={row['changes_requested_count']}, "
            f"commented={row['commented_count']}"
        )


def print_path_hotspots(connection: sqlite3.Connection, limit: int) -> None:
    rows = connection.execute(
        """
        SELECT
            path,
            COUNT(*) AS comment_count,
            COUNT(DISTINCT pull_request_id) AS pr_count
        FROM pull_request_review_comments_current
        WHERE path IS NOT NULL
        GROUP BY path
        ORDER BY comment_count DESC, pr_count DESC, path
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    for row in rows:
        print(f"{row['path']}: comments={row['comment_count']}, prs={row['pr_count']}")


def print_keyword_report(connection: sqlite3.Connection, query: str, limit: int) -> None:
    comment_rows = connection.execute(
        """
        SELECT
            pr.number,
            pr.title,
            c.path,
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

    print(f"[comments] query={query}")
    for row in comment_rows:
        print(f"PR #{row['number']} | {row['path']} | {row['user_login']}")
        print(f"  {row['body']}")

    print()
    print("[top paths]")
    path_rows = connection.execute(
        """
        SELECT
            c.path,
            COUNT(*) AS hit_count
        FROM review_comment_fts fts
        JOIN pull_request_review_comments_current c
          ON c.id = fts.review_comment_id
        WHERE review_comment_fts MATCH ?
          AND c.path IS NOT NULL
        GROUP BY c.path
        ORDER BY hit_count DESC, c.path
        LIMIT ?
        """,
        (query, limit),
    ).fetchall()
    for row in path_rows:
        print(f"{row['path']}: {row['hit_count']}")


def print_pr_report(connection: sqlite3.Connection, number: int) -> None:
    pr = connection.execute(
        """
        SELECT
            id,
            number,
            title,
            state,
            author_login,
            changed_files,
            additions,
            deletions,
            body
        FROM pull_requests_current
        WHERE number = ?
        """,
        (number,),
    ).fetchone()

    if pr is None:
        print(f"PR #{number} not found")
        return

    print(f"PR #{pr['number']} | {pr['title']}")
    print(f"state={pr['state']} author={pr['author_login']}")
    print(f"changed_files={pr['changed_files']} additions={pr['additions']} deletions={pr['deletions']}")
    print()
    print("[body]")
    print(pr["body"] or "")
    print()

    review_rows = connection.execute(
        """
        SELECT reviewer_login, state, body
        FROM pull_request_reviews_current
        WHERE pull_request_id = ?
        ORDER BY submitted_at
        """,
        (pr["id"],),
    ).fetchall()
    print("[reviews]")
    for row in review_rows:
        print(f"- {row['reviewer_login']} | {row['state']}")
        if row["body"]:
            print(f"  {row['body']}")
    print()

    comment_rows = connection.execute(
        """
        SELECT path, line, user_login, body
        FROM pull_request_review_comments_current
        WHERE pull_request_id = ?
        ORDER BY path, line, id
        """,
        (pr["id"],),
    ).fetchall()
    print("[review comments]")
    for row in comment_rows:
        print(f"- {row['path']}:{row['line']} | {row['user_login']}")
        print(f"  {row['body']}")


if __name__ == "__main__":
    main()
