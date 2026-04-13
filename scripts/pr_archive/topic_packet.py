#!/usr/bin/env python3
"""Generate a topic-based learning packet from archived PR data."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


DEFAULT_DB_PATH = Path("catalog/pr-datasets/github-prs.sqlite3")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a topic packet from archived PR data.")
    parser.add_argument("--topic", required=True, help="Topic name shown in the packet")
    parser.add_argument("--query", required=True, help="FTS query used to collect evidence")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--comment-limit", type=int, default=10)
    parser.add_argument("--patch-limit", type=int, default=5)
    parser.add_argument("--pr-limit", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with sqlite3.connect(args.db_path) as connection:
        connection.row_factory = sqlite3.Row

        comments = find_comment_evidence(connection, args.query, args.comment_limit)
        patches = find_patch_evidence(connection, args.query, args.patch_limit)
        prs = find_related_pull_requests(connection, args.query, args.pr_limit)
        hotspots = find_hotspots(connection, args.query, args.pr_limit)
        reviewers = find_top_reviewers(connection, args.query, args.pr_limit)

        print(render_packet(
            topic=args.topic,
            query=args.query,
            comments=comments,
            patches=patches,
            prs=prs,
            hotspots=hotspots,
            reviewers=reviewers,
        ))


def find_comment_evidence(connection: sqlite3.Connection, query: str, limit: int) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            pr.number,
            pr.title,
            c.path,
            c.line,
            c.user_login,
            c.body,
            c.diff_hunk
        FROM review_comment_fts fts
        JOIN pull_request_review_comments_current c
          ON c.id = fts.review_comment_id
        JOIN pull_requests_current pr
          ON pr.id = c.pull_request_id
        WHERE review_comment_fts MATCH ?
        ORDER BY pr.number DESC, c.created_at DESC
        LIMIT ?
        """,
        (query, limit),
    ).fetchall()


def find_patch_evidence(connection: sqlite3.Connection, query: str, limit: int) -> list[sqlite3.Row]:
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


def find_related_pull_requests(connection: sqlite3.Connection, query: str, limit: int) -> list[sqlite3.Row]:
    return connection.execute(
        """
        WITH comment_hits AS (
            SELECT c.pull_request_id AS pull_request_id, COUNT(*) AS hit_count
            FROM review_comment_fts fts
            JOIN pull_request_review_comments_current c
              ON c.id = fts.review_comment_id
            WHERE review_comment_fts MATCH ?
            GROUP BY c.pull_request_id
        )
        SELECT
            pr.number,
            pr.title,
            pr.author_login,
            pr.state,
            comment_hits.hit_count
        FROM comment_hits
        JOIN pull_requests_current pr
          ON pr.id = comment_hits.pull_request_id
        ORDER BY comment_hits.hit_count DESC, pr.number DESC
        LIMIT ?
        """,
        (query, limit),
    ).fetchall()


def find_hotspots(connection: sqlite3.Connection, query: str, limit: int) -> list[sqlite3.Row]:
    return connection.execute(
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


def find_top_reviewers(connection: sqlite3.Connection, query: str, limit: int) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            c.user_login,
            COUNT(*) AS hit_count
        FROM review_comment_fts fts
        JOIN pull_request_review_comments_current c
          ON c.id = fts.review_comment_id
        WHERE review_comment_fts MATCH ?
        GROUP BY c.user_login
        ORDER BY hit_count DESC, c.user_login
        LIMIT ?
        """,
        (query, limit),
    ).fetchall()


def render_packet(
        topic: str,
        query: str,
        comments: list[sqlite3.Row],
        patches: list[sqlite3.Row],
        prs: list[sqlite3.Row],
        hotspots: list[sqlite3.Row],
        reviewers: list[sqlite3.Row],
) -> str:
    lines: list[str] = []
    lines.append(f"# Topic Packet: {topic}")
    lines.append("")
    lines.append("## Query")
    lines.append(f"- `{query}`")
    lines.append("")

    lines.append("## Related PRs")
    if not prs:
        lines.append("- 없음")
    else:
        for row in prs:
            lines.append(
                f"- PR #{row['number']} | {row['title']} | author={row['author_login']} | "
                f"state={row['state']} | comment_hits={row['hit_count']}"
            )
    lines.append("")

    lines.append("## Top Reviewers")
    if not reviewers:
        lines.append("- 없음")
    else:
        for row in reviewers:
            lines.append(f"- {row['user_login']}: {row['hit_count']}")
    lines.append("")

    lines.append("## Hotspot Paths")
    if not hotspots:
        lines.append("- 없음")
    else:
        for row in hotspots:
            lines.append(f"- `{row['path']}`: {row['hit_count']}")
    lines.append("")

    lines.append("## Representative Review Comments")
    if not comments:
        lines.append("- 없음")
    else:
        for row in comments:
            lines.append(f"### PR #{row['number']} | `{row['path']}`:{row['line']}")
            lines.append(f"- reviewer: `{row['user_login']}`")
            lines.append(f"- comment: {row['body']}")
            if row["diff_hunk"]:
                lines.append("")
                lines.append("```diff")
                lines.append(trim_block(row["diff_hunk"], 12))
                lines.append("```")
            lines.append("")

    lines.append("## Representative Patch Context")
    if not patches:
        lines.append("- 없음")
    else:
        for row in patches:
            lines.append(f"### PR #{row['number']} | `{row['path']}`")
            lines.append("```diff")
            lines.append(trim_block(row["patch_text"] or "", 20))
            lines.append("```")
            lines.append("")

    lines.append("## Suggested Reading Order")
    if prs:
        for row in prs:
            lines.append(f"1. PR #{row['number']} - {row['title']}")
    else:
        lines.append("1. 관련 PR 없음")

    return "\n".join(lines).strip() + "\n"


def trim_block(text: str, max_lines: int) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join(lines[:max_lines] + ["..."])


if __name__ == "__main__":
    main()
