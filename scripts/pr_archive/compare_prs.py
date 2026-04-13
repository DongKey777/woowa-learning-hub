#!/usr/bin/env python3
"""Generate a comparison packet for multiple PRs."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


DEFAULT_DB_PATH = Path("catalog/pr-datasets/github-prs.sqlite3")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate a comparison packet for multiple PRs.")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--prs", nargs="+", type=int, required=True, help="PR numbers to compare")
    parser.add_argument("--comment-limit", type=int, default=5)
    parser.add_argument("--path-limit", type=int, default=5)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    with sqlite3.connect(args.db_path) as connection:
        connection.row_factory = sqlite3.Row

        pull_requests = [find_pull_request(connection, number) for number in args.prs]
        pull_requests = [pull_request for pull_request in pull_requests if pull_request is not None]

        review_summaries = {pr["number"]: find_review_summary(connection, pr["id"]) for pr in pull_requests}
        hotspots = {pr["number"]: find_path_hotspots(connection, pr["id"], args.path_limit) for pr in pull_requests}
        comments = {
            pr["number"]: find_representative_comments(connection, pr["id"], args.comment_limit)
            for pr in pull_requests
        }

        print(render_packet(
            pull_requests=pull_requests,
            review_summaries=review_summaries,
            hotspots=hotspots,
            comments=comments,
        ))


def find_pull_request(connection: sqlite3.Connection, number: int) -> sqlite3.Row | None:
    return connection.execute(
        """
        SELECT id, number, title, state, author_login, changed_files, additions, deletions
        FROM pull_requests_current
        WHERE number = ?
        """,
        (number,),
    ).fetchone()


def find_review_summary(connection: sqlite3.Connection, pull_request_id: int) -> sqlite3.Row:
    return connection.execute(
        """
        SELECT
            COUNT(*) AS review_count,
            SUM(CASE WHEN state = 'APPROVED' THEN 1 ELSE 0 END) AS approved_count,
            SUM(CASE WHEN state = 'CHANGES_REQUESTED' THEN 1 ELSE 0 END) AS changes_requested_count,
            SUM(CASE WHEN state = 'COMMENTED' THEN 1 ELSE 0 END) AS commented_count
        FROM pull_request_reviews_current
        WHERE pull_request_id = ?
        """,
        (pull_request_id,),
    ).fetchone()


def find_path_hotspots(connection: sqlite3.Connection, pull_request_id: int, limit: int) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            path,
            COUNT(*) AS comment_count
        FROM pull_request_review_comments_current
        WHERE pull_request_id = ?
          AND path IS NOT NULL
        GROUP BY path
        ORDER BY comment_count DESC, path
        LIMIT ?
        """,
        (pull_request_id, limit),
    ).fetchall()


def find_representative_comments(connection: sqlite3.Connection, pull_request_id: int, limit: int) -> list[sqlite3.Row]:
    return connection.execute(
        """
        SELECT
            path,
            line,
            user_login,
            body
        FROM pull_request_review_comments_current
        WHERE pull_request_id = ?
        ORDER BY created_at DESC, id DESC
        LIMIT ?
        """,
        (pull_request_id, limit),
    ).fetchall()


def render_packet(
        pull_requests: list[sqlite3.Row],
        review_summaries: dict[int, sqlite3.Row],
        hotspots: dict[int, list[sqlite3.Row]],
        comments: dict[int, list[sqlite3.Row]],
) -> str:
    lines: list[str] = []
    pr_numbers = ", ".join(f"#{pull_request['number']}" for pull_request in pull_requests)
    lines.append(f"# PR Comparison Packet: {pr_numbers}")
    lines.append("")

    lines.append("## PR Summary")
    for pull_request in pull_requests:
        summary = review_summaries[pull_request["number"]]
        lines.append(
            f"- PR #{pull_request['number']} | {pull_request['title']} | "
            f"author={pull_request['author_login']} | state={pull_request['state']} | "
            f"files={pull_request['changed_files']} | additions={pull_request['additions']} | "
            f"deletions={pull_request['deletions']} | reviews={summary['review_count']} | "
            f"changes_requested={summary['changes_requested_count']}"
        )
    lines.append("")

    lines.append("## Review Density")
    for pull_request in pull_requests:
        summary = review_summaries[pull_request["number"]]
        lines.append(
            f"- PR #{pull_request['number']}: approved={summary['approved_count']}, "
            f"changes_requested={summary['changes_requested_count']}, commented={summary['commented_count']}"
        )
    lines.append("")

    lines.append("## Path Hotspots")
    for pull_request in pull_requests:
        lines.append(f"### PR #{pull_request['number']}")
        path_rows = hotspots[pull_request["number"]]
        if not path_rows:
            lines.append("- 없음")
        else:
            for row in path_rows:
                lines.append(f"- `{row['path']}`: {row['comment_count']}")
        lines.append("")

    lines.append("## Representative Comments")
    for pull_request in pull_requests:
        lines.append(f"### PR #{pull_request['number']}")
        comment_rows = comments[pull_request["number"]]
        if not comment_rows:
            lines.append("- 없음")
        else:
            for row in comment_rows:
                lines.append(f"- `{row['path']}`:{row['line']} | {row['user_login']}")
                lines.append(f"  {row['body']}")
        lines.append("")

    lines.append("## Suggested Comparison Questions")
    lines.append("1. 어떤 PR이 Repository / DAO / Service를 어디까지 나눴는가?")
    lines.append("2. 어떤 PR이 가장 많은 changes requested를 받았고, 그 이유는 무엇인가?")
    lines.append("3. 리뷰가 많이 몰린 파일은 어떤 계층에 속하는가?")
    lines.append("4. 내 코드와 가장 가까운 구조는 무엇이고, 가장 다른 구조는 무엇인가?")

    return "\n".join(lines).strip() + "\n"


if __name__ == "__main__":
    main()
