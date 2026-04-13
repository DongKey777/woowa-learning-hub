from __future__ import annotations

import sqlite3
from pathlib import Path

from .comment_classifier import _has_column


def _clip(value: str | None, limit: int = 220) -> str:
    if not value:
        return ""
    flattened = " ".join(value.split())
    if len(flattened) <= limit:
        return flattened
    return flattened[: limit - 3].rstrip() + "..."


def _role_sequence(participants: list[dict]) -> str:
    labels = []
    for p in participants:
        role = p.get("role", "")
        if role.startswith("mentor"):
            labels.append("mentor")
        elif role.startswith("crew"):
            labels.append("crew")
        else:
            labels.append("other")
    return "→".join(labels)


def build_threads(db_path: str | Path, pr_number: int) -> list[dict]:
    db_path = Path(db_path)
    if not db_path.exists():
        return []

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        has_role = _has_column(connection, "pull_request_review_comments_current", "comment_role")
        role_col = ", c.comment_role" if has_role else ""
        bot_filter = " AND c.comment_role != 'bot'" if has_role else ""

        rows = connection.execute(
            f"""
            SELECT c.github_comment_id, c.in_reply_to_github_comment_id,
                   c.user_login, c.path, c.line, c.body, c.created_at,
                   c.diff_hunk{role_col}
            FROM pull_request_review_comments_current c
            JOIN pull_requests_current pr ON pr.id = c.pull_request_id
            WHERE pr.number = ? AND c.is_missing = 0{bot_filter}
            ORDER BY c.created_at
            """,
            (pr_number,),
        ).fetchall()

        comment_map: dict[int, dict] = {}
        for row in rows:
            comment_map[row["github_comment_id"]] = dict(row)

        roots: list[dict] = []
        children: dict[int, list[dict]] = {}
        for row in rows:
            d = dict(row)
            parent_id = d["in_reply_to_github_comment_id"]
            if parent_id is None:
                roots.append(d)
            else:
                children.setdefault(parent_id, []).append(d)

        threads: list[dict] = []
        for root in roots:
            root_id = root["github_comment_id"]
            replies = children.get(root_id, [])
            if not replies:
                continue

            participants = [_participant(root, has_role, 220)]
            for reply in replies[:2]:
                participants.append(_participant(reply, has_role, 150))

            threads.append({
                "thread_id": root_id,
                "path": root.get("path"),
                "line": root.get("line"),
                "role_sequence": _role_sequence(participants),
                "depth": len(participants),
                "participants": participants,
            })

        threads.sort(key=lambda t: (-t["depth"], t["thread_id"]))
        return threads
    finally:
        connection.close()


def _participant(row: dict, has_role: bool, excerpt_limit: int) -> dict:
    result = {
        "author": row.get("user_login"),
        "body_excerpt": _clip(row.get("body"), limit=excerpt_limit),
    }
    if has_role:
        result["role"] = row.get("comment_role", "")
    return result


def build_threads_for_packet(db_path: str | Path, pr_number: int, limit: int = 5) -> list[dict]:
    threads = build_threads(db_path, pr_number)
    return threads[:limit]
