#!/usr/bin/env python3
"""Generate a reviewer-based learning packet from archived PR data."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


DEFAULT_DB_PATH = Path("catalog/pr-datasets/github-prs.sqlite3")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a reviewer packet from archived PR data.")
    parser.add_argument("--reviewer", required=True, help="Reviewer login")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--comment-limit", type=int, default=12)
    parser.add_argument("--path-limit", type=int, default=10)
    parser.add_argument("--pr-limit", type=int, default=8)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with sqlite3.connect(args.db_path) as connection:
        connection.row_factory = sqlite3.Row

        summary = find_reviewer_summary(connection, args.reviewer)
        prs = find_related_pull_requests(connection, args.reviewer, args.pr_limit)
        paths = find_hotspot_paths(connection, args.reviewer, args.path_limit)
        comments = find_representative_comments(connection, args.reviewer, args.comment_limit)

        print(render_packet(
            reviewer=args.reviewer,
            summary=summary,
            prs=prs,
            paths=paths,
            comments=comments,
        ))


def find_reviewer_summary(connection: sqlite3.Connection, reviewer: str) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT
            reviewer_login,
            COUNT(*) AS review_count,
            SUM(CASE WHEN state = 'APPROVED' THEN 1 ELSE 0 END) AS approved_count,
            SUM(CASE WHEN state = 'CHANGES_REQUESTED' THEN 1 ELSE 0 END) AS changes_requested_count,
            SUM(CASE WHEN state = 'COMMENTED' THEN 1 ELSE 0 END) AS commented_count
        FROM pull_request_reviews_current
        WHERE reviewer_login = ?
        GROUP BY reviewer_login
        """,
        (reviewer,),
    ).fetchone()


def find_related_pull_requests(connection: sqlite3.Connection, reviewer: str, limit: int) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            pr.number,
            pr.title,
            pr.state,
            COUNT(c.id) AS comment_count
        FROM pull_request_review_comments_current c
        JOIN pull_requests_current pr
          ON pr.id = c.pull_request_id
        WHERE c.user_login = ?
        GROUP BY pr.id, pr.number, pr.title, pr.state
        ORDER BY comment_count DESC, pr.number DESC
        LIMIT ?
        """,
        (reviewer, limit),
    ).fetchall()


def find_hotspot_paths(connection: sqlite3.Connection, reviewer: str, limit: int) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            path,
            COUNT(*) AS comment_count
        FROM pull_request_review_comments_current
        WHERE user_login = ?
          AND path IS NOT NULL
        GROUP BY path
        ORDER BY comment_count DESC, path
        LIMIT ?
        """,
        (reviewer, limit),
    ).fetchall()


def find_representative_comments(connection: sqlite3.Connection, reviewer: str, limit: int) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            pr.number,
            pr.title,
            c.path,
            c.line,
            c.body,
            c.diff_hunk
        FROM pull_request_review_comments_current c
        JOIN pull_requests_current pr
          ON pr.id = c.pull_request_id
        WHERE c.user_login = ?
        ORDER BY pr.number DESC, c.created_at DESC
        LIMIT ?
        """,
        (reviewer, limit),
    ).fetchall()


def render_packet(
        reviewer: str,
        summary: sqlite3.Row | None,
        prs: list[sqlite3.Row],
        paths: list[sqlite3.Row],
        comments: list[sqlite3.Row],
) -> str:
    lines: list[str] = []
    lines.append(f"# Reviewer Packet: {reviewer}")
    lines.append("")

    lines.append("## Summary")
    if summary is None:
        lines.append("- 없음")
    else:
        lines.append(f"- reviews: {summary['review_count']}")
        lines.append(f"- approved: {summary['approved_count']}")
        lines.append(f"- changes_requested: {summary['changes_requested_count']}")
        lines.append(f"- commented: {summary['commented_count']}")
    lines.append("")

    lines.append("## Related PRs")
    if not prs:
        lines.append("- 없음")
    else:
        for row in prs:
            lines.append(
                f"- PR #{row['number']} | {row['title']} | state={row['state']} | comment_count={row['comment_count']}"
            )
    lines.append("")

    lines.append("## Hotspot Paths")
    if not paths:
        lines.append("- 없음")
    else:
        for row in paths:
            lines.append(f"- `{row['path']}`: {row['comment_count']}")
    lines.append("")

    lines.append("## Representative Comments")
    if not comments:
        lines.append("- 없음")
    else:
        for row in comments:
            lines.append(f"### PR #{row['number']} | `{row['path']}`:{row['line']}")
            lines.append(f"- comment: {row['body']}")
            if row["diff_hunk"]:
                lines.append("")
                lines.append("```diff")
                lines.append(trim_block(row["diff_hunk"], 12))
                lines.append("```")
            lines.append("")

    return "\n".join(lines).strip() + "\n"


def trim_block(text: str, max_lines: int) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[:max_lines] + ["..."])


if __name__ == "__main__":
    main()
