from __future__ import annotations

import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .comment_classifier import _has_column
from .paths import PR_ARCHIVE_DIR, repo_packet_dir
from .schema_validation import validate_payload
from .shell import run_capture
from .thread_builder import build_threads_for_packet


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_markdown(path: Path, content: str) -> None:
    path.write_text(content + "\n", encoding="utf-8")


def _slug(value: str) -> str:
    return value.lower().replace("/", "-").replace(" ", "-")


def _clip(value: str | None, limit: int = 220) -> str:
    if not value:
        return ""
    flattened = " ".join(value.split())
    if len(flattened) <= limit:
        return flattened
    return flattened[: limit - 3].rstrip() + "..."


def _run_markdown(script_name: str, args: list[str]) -> tuple[bool, str, str]:
    result = run_capture(["python3", str(PR_ARCHIVE_DIR / script_name), *args])
    return result.returncode == 0, result.stdout.strip(), result.stderr.strip()


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in row.keys()}


def _connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def _comment_sample(row: dict) -> dict:
    sample = {
        "pr_number": row.get("number"),
        "title": row.get("title"),
        "path": row.get("path"),
        "line": row.get("line"),
        "author": row.get("user_login"),
        "body_excerpt": _clip(row.get("body")),
        "diff_hunk_excerpt": _clip(row.get("diff_hunk"), limit=180),
    }
    if row.get("comment_role"):
        sample["comment_role"] = row.get("comment_role")
    return sample


def _patch_sample(row: dict) -> dict:
    return {
        "pr_number": row.get("number"),
        "title": row.get("title"),
        "path": row.get("path"),
        "patch_excerpt": _clip(row.get("patch_text"), limit=220),
    }


def _topic_evidence(payload: dict) -> dict:
    evidence = {
        "summary": {
            "query": payload["query"],
            "related_pr_count": len(payload["related_prs"]),
            "reviewer_count": len(payload["top_reviewers"]),
            "hotspot_path_count": len(payload["hotspot_paths"]),
            "comment_sample_count": len(payload["representative_comments"]),
            "patch_sample_count": len(payload["representative_patches"]),
        },
        "ranked_prs": payload["related_prs"][:5],
        "ranked_reviewers": payload["top_reviewers"][:5],
        "ranked_paths": payload["hotspot_paths"][:5],
        "comment_samples": [_comment_sample(row) for row in payload["representative_comments"][:5]],
        "patch_samples": [_patch_sample(row) for row in payload["representative_patches"][:5]],
    }
    if "mentor_comments" in payload:
        evidence["mentor_comment_samples"] = [_comment_sample(row) for row in payload["mentor_comments"][:5]]
        evidence["crew_response_samples"] = [_comment_sample(row) for row in payload["crew_responses"][:3]]
    return evidence


def _reviewer_evidence(payload: dict) -> dict:
    evidence = {
        "summary": payload["summary"],
        "counts": {
            "related_pr_count": len(payload["related_prs"]),
            "hotspot_path_count": len(payload["hotspot_paths"]),
            "comment_sample_count": len(payload["representative_comments"]),
        },
        "ranked_prs": payload["related_prs"][:5],
        "ranked_paths": payload["hotspot_paths"][:5],
        "comment_samples": [_comment_sample(row) for row in payload["representative_comments"][:5]],
    }
    if "mentor_comments" in payload:
        evidence["mentor_comment_samples"] = [_comment_sample(row) for row in payload["mentor_comments"][:5]]
        evidence["crew_response_samples"] = [_comment_sample(row) for row in payload["crew_responses"][:3]]
    return evidence


def _compare_evidence(payload: dict) -> dict:
    comment_groups = []
    for group in payload["representative_comments"][:5]:
        comment_groups.append({
            "pr_number": group.get("pr_number"),
            "comments": [
                {
                    "path": comment.get("path"),
                    "line": comment.get("line"),
                    "author": comment.get("user_login"),
                    "body_excerpt": _clip(comment.get("body")),
                }
                for comment in group.get("comments", [])[:3]
            ],
        })
    return {
        "summary": {
            "pr_count": len(payload["pr_summary"]),
            "review_density_count": len(payload["review_density"]),
            "path_hotspot_group_count": len(payload["path_hotspots"]),
            "comment_group_count": len(payload["representative_comments"]),
        },
        "prs": payload["pr_summary"][:5],
        "review_density": payload["review_density"][:5],
        "path_overlap": payload["path_hotspots"][:5],
        "comment_groups": comment_groups,
    }


def _review_state_counts(reviews: list[dict]) -> dict:
    states = Counter((review.get("state") or "").lower() for review in reviews if review.get("state"))
    return {
        "approved_count": states.get("approved", 0),
        "changes_requested_count": states.get("changes_requested", 0),
        "commented_count": states.get("commented", 0),
    }


def _reviewer_summary(reviews: list[dict]) -> list[dict]:
    buckets: dict[str, dict] = {}
    for review in reviews:
        reviewer = review.get("reviewer_login")
        if not reviewer:
            continue
        if reviewer not in buckets:
            buckets[reviewer] = {
                "reviewer_login": reviewer,
                "count": 0,
                "states": Counter(),
            }
        buckets[reviewer]["count"] += 1
        state = (review.get("state") or "").lower()
        if state:
            buckets[reviewer]["states"][state] += 1

    summary = []
    for item in buckets.values():
        summary.append({
            "reviewer_login": item["reviewer_login"],
            "count": item["count"],
            "states": dict(item["states"]),
        })
    summary.sort(key=lambda item: (-item["count"], item["reviewer_login"]))
    return summary


def _hotspot_paths(review_comments: list[dict], limit: int = 8) -> list[dict]:
    counts = Counter(comment.get("path") for comment in review_comments if comment.get("path"))
    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [
        {"path": path, "comment_count": count}
        for path, count in ranked[:limit]
    ]


def _review_samples(reviews: list[dict], limit: int = 5) -> list[dict]:
    mentor_first = sorted(
        reviews,
        key=lambda r: 0 if (r.get("reviewer_role") == "mentor") else 1,
    )
    samples = []
    for review in mentor_first:
        excerpt = _clip(review.get("body"))
        if not excerpt:
            continue
        samples.append({
            "reviewer_login": review.get("reviewer_login"),
            "state": review.get("state"),
            "submitted_at": review.get("submitted_at"),
            "body_excerpt": excerpt,
            "reviewer_role": review.get("reviewer_role"),
        })
        if len(samples) >= limit:
            break
    return samples


_MENTOR_ROLES = {"mentor_original", "mentor_followup"}
_CREW_REPLY_ROLES = {"crew_self_reply"}
_CREW_ORIGINAL_ROLES = {"crew_self_original"}


def _split_review_comments_by_role(comments: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    mentors: list[dict] = []
    crew_replies: list[dict] = []
    crew_originals: list[dict] = []
    for row in comments:
        role = row.get("comment_role") or ""
        if role in _MENTOR_ROLES:
            mentors.append(row)
        elif role in _CREW_REPLY_ROLES:
            crew_replies.append(row)
        elif role in _CREW_ORIGINAL_ROLES:
            crew_originals.append(row)
        else:
            mentors.append(row)
    return mentors, crew_replies, crew_originals


def _pr_report_evidence(payload: dict) -> dict:
    review_state_counts = _review_state_counts(payload["reviews"])
    mentors, crew_replies, crew_originals = _split_review_comments_by_role(payload["review_comments"])
    flattened = (mentors + crew_replies + crew_originals)[:8]
    evidence = {
        "overview": {
            "pr_number": payload["pr_number"],
            "state": payload["state"],
            "author": payload["author"],
            "changed_files": payload["changed_files"],
            "additions": payload["additions"],
            "deletions": payload["deletions"],
        },
        "review_summary": {
            "review_count": len(payload["reviews"]),
            "review_comment_count": len(payload["review_comments"]),
            **review_state_counts,
        },
        "reviewers": _reviewer_summary(payload["reviews"])[:5],
        "hotspot_paths": _hotspot_paths(payload["review_comments"]),
        "review_samples": _review_samples(payload["reviews"]),
        "comment_samples": [_comment_sample(row) for row in flattened],
        "mentor_comment_samples": [_comment_sample(row) for row in mentors[:5]],
        "crew_response_samples": [_comment_sample(row) for row in crew_replies[:3]],
    }
    if "thread_samples" in payload:
        evidence["thread_samples"] = payload["thread_samples"]
    return evidence


def _role_filter(connection: sqlite3.Connection, table: str = "pull_request_review_comments_current", column: str = "comment_role") -> str:
    if _has_column(connection, table, column):
        return f" AND {table[0]}.{column} != 'bot' AND ({table[0]}.{column} IS NOT NULL OR 1=1)"
    return ""


def _mentor_order(connection: sqlite3.Connection, table_alias: str = "c") -> str:
    if _has_column(connection, "pull_request_review_comments_current", "comment_role"):
        return f"CASE WHEN {table_alias}.comment_role IN ('mentor_original','mentor_followup') THEN 0 ELSE 1 END, "
    return ""


def _split_comment_buckets(comments: list[dict]) -> dict:
    mentor = []
    crew_responses = []
    crew_originals = []
    for c in comments:
        role = c.get("comment_role") or c.get("role") or ""
        if role in ("mentor_original", "mentor_followup"):
            mentor.append(c)
        elif role == "crew_self_reply":
            crew_responses.append(c)
        elif role == "crew_self_original":
            crew_originals.append(c)
        else:
            mentor.append(c)
    return {
        "mentor_comments": mentor,
        "crew_responses": crew_responses,
        "crew_originals": crew_originals,
    }


def _topic_data(connection: sqlite3.Connection, query: str, comment_limit: int = 10, patch_limit: int = 5, pr_limit: int = 5) -> dict:
    has_role = _has_column(connection, "pull_request_review_comments_current", "comment_role")
    bot_filter = " AND c.comment_role != 'bot'" if has_role else ""
    null_guard = " AND (c.comment_role IS NOT NULL OR 1=1)" if has_role else ""
    role_filter = bot_filter + null_guard
    mentor_order = "CASE WHEN c.comment_role IN ('mentor_original','mentor_followup') THEN 0 ELSE 1 END, " if has_role else ""
    role_select = ", c.comment_role" if has_role else ""

    related_prs = connection.execute(
        f"""
        WITH comment_hits AS (
            SELECT c.pull_request_id AS pull_request_id, COUNT(*) AS hit_count
            FROM review_comment_fts fts
            JOIN pull_request_review_comments_current c
              ON c.id = fts.review_comment_id
            WHERE review_comment_fts MATCH ?
              {role_filter}
            GROUP BY c.pull_request_id
        )
        SELECT pr.number, pr.title, pr.author_login, pr.state, comment_hits.hit_count
        FROM comment_hits
        JOIN pull_requests_current pr
          ON pr.id = comment_hits.pull_request_id
        ORDER BY comment_hits.hit_count DESC, pr.number DESC
        LIMIT ?
        """,
        (query, pr_limit),
    ).fetchall()

    top_reviewers = connection.execute(
        f"""
        SELECT c.user_login, COUNT(*) AS hit_count
        FROM review_comment_fts fts
        JOIN pull_request_review_comments_current c
          ON c.id = fts.review_comment_id
        WHERE review_comment_fts MATCH ?
          {role_filter}
        GROUP BY c.user_login
        ORDER BY hit_count DESC, c.user_login
        LIMIT ?
        """,
        (query, pr_limit),
    ).fetchall()

    hotspot_paths = connection.execute(
        f"""
        SELECT c.path, COUNT(*) AS hit_count
        FROM review_comment_fts fts
        JOIN pull_request_review_comments_current c
          ON c.id = fts.review_comment_id
        WHERE review_comment_fts MATCH ?
          AND c.path IS NOT NULL
          {role_filter}
        GROUP BY c.path
        ORDER BY hit_count DESC, c.path
        LIMIT ?
        """,
        (query, pr_limit),
    ).fetchall()

    representative_comments = connection.execute(
        f"""
        SELECT pr.number, pr.title, c.path, c.line, c.user_login, c.body, c.diff_hunk{role_select}
        FROM review_comment_fts fts
        JOIN pull_request_review_comments_current c
          ON c.id = fts.review_comment_id
        JOIN pull_requests_current pr
          ON pr.id = c.pull_request_id
        WHERE review_comment_fts MATCH ?
          {role_filter}
        ORDER BY {mentor_order}pr.number DESC, c.created_at DESC
        LIMIT ?
        """,
        (query, comment_limit),
    ).fetchall()

    representative_patches = connection.execute(
        """
        SELECT pr.number, pr.title, f.path, f.patch_text
        FROM patch_fts fts
        JOIN pull_request_files_current f
          ON f.id = fts.pull_request_file_id
        JOIN pull_requests_current pr
          ON pr.id = f.pull_request_id
        WHERE patch_fts MATCH ?
        ORDER BY pr.number DESC
        LIMIT ?
        """,
        (query, patch_limit),
    ).fetchall()

    comment_dicts = [_row_to_dict(row) for row in representative_comments]
    result = {
        "related_prs": [_row_to_dict(row) for row in related_prs],
        "top_reviewers": [_row_to_dict(row) for row in top_reviewers],
        "hotspot_paths": [_row_to_dict(row) for row in hotspot_paths],
        "representative_comments": comment_dicts,
        "representative_patches": [_row_to_dict(row) for row in representative_patches],
    }
    if has_role:
        result.update(_split_comment_buckets(comment_dicts))
    return result


def generate_topic_packet(repo_name: str, db_path: Path, topic_name: str, topic_query: str) -> dict:
    ok, markdown, error = _run_markdown(
        "topic_packet.py",
        ["--db-path", str(db_path), "--topic", topic_name, "--query", topic_query],
    )
    packet_dir = repo_packet_dir(repo_name)
    md_path = packet_dir / f"topic-{_slug(topic_name)}.md"
    json_path = packet_dir / f"topic-{_slug(topic_name)}.json"
    if ok:
        _write_markdown(md_path, markdown)

    payload = {
        "packet_type": "topic",
        "repo": repo_name,
        "topic": topic_name,
        "query": topic_query,
        "source_db_path": str(db_path),
        "generated_at": _timestamp(),
        "generated": ok,
        "markdown_path": str(md_path) if ok else None,
        "markdown_preview": markdown.splitlines()[:20] if ok else [],
        "error": None if ok else error,
        "related_prs": [],
        "top_reviewers": [],
        "hotspot_paths": [],
        "representative_comments": [],
        "representative_patches": [],
        "evidence": {
            "summary": {
                "query": topic_query,
                "related_pr_count": 0,
                "reviewer_count": 0,
                "hotspot_path_count": 0,
                "comment_sample_count": 0,
                "patch_sample_count": 0,
            },
            "ranked_prs": [],
            "ranked_reviewers": [],
            "ranked_paths": [],
            "comment_samples": [],
            "patch_samples": [],
        },
    }
    if ok:
        with _connect(db_path) as connection:
            payload.update(_topic_data(connection, topic_query))
        payload["evidence"] = _topic_evidence(payload)

    validate_payload("topic-packet", payload)
    _write_json(json_path, payload)
    payload["json_path"] = str(json_path)
    return payload


def _reviewer_data(connection: sqlite3.Connection, reviewer: str, comment_limit: int = 12, path_limit: int = 10, pr_limit: int = 8) -> dict:
    has_role = _has_column(connection, "pull_request_review_comments_current", "comment_role")
    bot_filter = " AND c.comment_role != 'bot'" if has_role else ""
    role_select = ", c.comment_role" if has_role else ""

    summary = connection.execute(
        """
        SELECT reviewer_login, COUNT(*) AS review_count,
               SUM(CASE WHEN state = 'APPROVED' THEN 1 ELSE 0 END) AS approved_count,
               SUM(CASE WHEN state = 'CHANGES_REQUESTED' THEN 1 ELSE 0 END) AS changes_requested_count,
               SUM(CASE WHEN state = 'COMMENTED' THEN 1 ELSE 0 END) AS commented_count
        FROM pull_request_reviews_current
        WHERE reviewer_login = ?
        GROUP BY reviewer_login
        """,
        (reviewer,),
    ).fetchone()

    related_prs = connection.execute(
        f"""
        SELECT pr.number, pr.title, pr.state, COUNT(c.id) AS comment_count
        FROM pull_request_review_comments_current c
        JOIN pull_requests_current pr ON pr.id = c.pull_request_id
        WHERE c.user_login = ?
          {bot_filter}
        GROUP BY pr.id, pr.number, pr.title, pr.state
        ORDER BY comment_count DESC, pr.number DESC
        LIMIT ?
        """,
        (reviewer, pr_limit),
    ).fetchall()

    hotspot_paths = connection.execute(
        f"""
        SELECT c.path, COUNT(*) AS comment_count
        FROM pull_request_review_comments_current c
        WHERE c.user_login = ?
          AND c.path IS NOT NULL
          {bot_filter}
        GROUP BY c.path
        ORDER BY comment_count DESC, c.path
        LIMIT ?
        """,
        (reviewer, path_limit),
    ).fetchall()

    representative_comments = connection.execute(
        f"""
        SELECT pr.number, pr.title, c.path, c.line, c.body, c.diff_hunk{role_select}
        FROM pull_request_review_comments_current c
        JOIN pull_requests_current pr ON pr.id = c.pull_request_id
        WHERE c.user_login = ?
          {bot_filter}
        ORDER BY pr.number DESC, c.created_at DESC
        LIMIT ?
        """,
        (reviewer, comment_limit),
    ).fetchall()

    comment_dicts = [_row_to_dict(row) for row in representative_comments]
    result = {
        "summary": _row_to_dict(summary) if summary else None,
        "related_prs": [_row_to_dict(row) for row in related_prs],
        "hotspot_paths": [_row_to_dict(row) for row in hotspot_paths],
        "representative_comments": comment_dicts,
    }
    if has_role:
        result.update(_split_comment_buckets(comment_dicts))
    return result


def generate_reviewer_packet(repo_name: str, db_path: Path, reviewer: str) -> dict:
    ok, markdown, error = _run_markdown(
        "reviewer_packet.py",
        ["--db-path", str(db_path), "--reviewer", reviewer],
    )
    packet_dir = repo_packet_dir(repo_name)
    md_path = packet_dir / f"reviewer-{_slug(reviewer)}.md"
    json_path = packet_dir / f"reviewer-{_slug(reviewer)}.json"
    if ok:
        _write_markdown(md_path, markdown)

    payload = {
        "packet_type": "reviewer",
        "repo": repo_name,
        "reviewer": reviewer,
        "source_db_path": str(db_path),
        "generated_at": _timestamp(),
        "generated": ok,
        "markdown_path": str(md_path) if ok else None,
        "markdown_preview": markdown.splitlines()[:20] if ok else [],
        "error": None if ok else error,
        "summary": None,
        "related_prs": [],
        "hotspot_paths": [],
        "representative_comments": [],
        "evidence": {
            "summary": None,
            "counts": {
                "related_pr_count": 0,
                "hotspot_path_count": 0,
                "comment_sample_count": 0,
            },
            "ranked_prs": [],
            "ranked_paths": [],
            "comment_samples": [],
        },
    }
    if ok:
        with _connect(db_path) as connection:
            payload.update(_reviewer_data(connection, reviewer))
        payload["evidence"] = _reviewer_evidence(payload)

    validate_payload("reviewer-packet", payload)
    _write_json(json_path, payload)
    payload["json_path"] = str(json_path)
    return payload


def _compare_data(connection: sqlite3.Connection, prs: list[int], path_limit: int = 5, comment_limit: int = 5) -> dict:
    pr_summary: list[dict] = []
    review_density: list[dict] = []
    path_hotspots: list[dict] = []
    representative_comments: list[dict] = []

    for number in prs:
        pr = connection.execute(
            """
            SELECT id, number, title, state, author_login, changed_files, additions, deletions
            FROM pull_requests_current
            WHERE number = ?
            """,
            (number,),
        ).fetchone()
        if pr is None:
            continue
        pr_summary.append(_row_to_dict(pr))

        density = connection.execute(
            """
            SELECT COUNT(*) AS review_count,
                   SUM(CASE WHEN state = 'APPROVED' THEN 1 ELSE 0 END) AS approved_count,
                   SUM(CASE WHEN state = 'CHANGES_REQUESTED' THEN 1 ELSE 0 END) AS changes_requested_count,
                   SUM(CASE WHEN state = 'COMMENTED' THEN 1 ELSE 0 END) AS commented_count
            FROM pull_request_reviews_current
            WHERE pull_request_id = ?
            """,
            (pr["id"],),
        ).fetchone()
        review_density.append({"pr_number": number, **_row_to_dict(density)})

        hotspots = connection.execute(
            """
            SELECT path, COUNT(*) AS comment_count
            FROM pull_request_review_comments_current
            WHERE pull_request_id = ?
              AND path IS NOT NULL
            GROUP BY path
            ORDER BY comment_count DESC, path
            LIMIT ?
            """,
            (pr["id"], path_limit),
        ).fetchall()
        path_hotspots.append({
            "pr_number": number,
            "paths": [_row_to_dict(row) for row in hotspots],
        })

        comments = connection.execute(
            """
            SELECT path, line, user_login, body
            FROM pull_request_review_comments_current
            WHERE pull_request_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (pr["id"], comment_limit),
        ).fetchall()
        representative_comments.append({
            "pr_number": number,
            "comments": [_row_to_dict(row) for row in comments],
        })

    return {
        "pr_summary": pr_summary,
        "review_density": review_density,
        "path_hotspots": path_hotspots,
        "representative_comments": representative_comments,
    }


def generate_compare_packet(repo_name: str, db_path: Path, prs: list[int]) -> dict:
    pr_args = [str(pr) for pr in prs]
    ok, markdown, error = _run_markdown(
        "compare_prs.py",
        ["--db-path", str(db_path), "--prs", *pr_args],
    )
    packet_dir = repo_packet_dir(repo_name)
    suffix = "-".join(pr_args)
    md_path = packet_dir / f"compare-{suffix}.md"
    json_path = packet_dir / f"compare-{suffix}.json"
    if ok:
        _write_markdown(md_path, markdown)

    payload = {
        "packet_type": "compare",
        "repo": repo_name,
        "prs": prs,
        "source_db_path": str(db_path),
        "generated_at": _timestamp(),
        "generated": ok,
        "markdown_path": str(md_path) if ok else None,
        "markdown_preview": markdown.splitlines()[:20] if ok else [],
        "error": None if ok else error,
        "pr_summary": [],
        "review_density": [],
        "path_hotspots": [],
        "representative_comments": [],
        "evidence": {
            "summary": {
                "pr_count": 0,
                "review_density_count": 0,
                "path_hotspot_group_count": 0,
                "comment_group_count": 0,
            },
            "prs": [],
            "review_density": [],
            "path_overlap": [],
            "comment_groups": [],
        },
    }
    if ok:
        with _connect(db_path) as connection:
            payload.update(_compare_data(connection, prs))
        payload["evidence"] = _compare_evidence(payload)

    validate_payload("compare-packet", payload)
    _write_json(json_path, payload)
    payload["json_path"] = str(json_path)
    return payload


def _pr_report_data(connection: sqlite3.Connection, pr_number: int) -> dict | None:
    pr = connection.execute(
        """
        SELECT id, number, title, state, author_login, changed_files, additions, deletions, body
        FROM pull_requests_current
        WHERE number = ?
        """,
        (pr_number,),
    ).fetchone()
    if pr is None:
        return None

    has_review_role = _has_column(connection, "pull_request_reviews_current", "reviewer_role")
    review_role_select = ", reviewer_role" if has_review_role else ""
    review_role_filter = " AND reviewer_role != 'bot'" if has_review_role else ""
    reviews = connection.execute(
        f"""
        SELECT reviewer_login, state, body, submitted_at{review_role_select}
        FROM pull_request_reviews_current
        WHERE pull_request_id = ?{review_role_filter}
        ORDER BY submitted_at
        """,
        (pr["id"],),
    ).fetchall()

    has_comment_role = _has_column(connection, "pull_request_review_comments_current", "comment_role")
    comment_role_select = ", comment_role" if has_comment_role else ""
    comment_role_filter = " AND comment_role != 'bot'" if has_comment_role else ""
    review_comments = connection.execute(
        f"""
        SELECT path, line, user_login, body, diff_hunk{comment_role_select}
        FROM pull_request_review_comments_current
        WHERE pull_request_id = ?{comment_role_filter}
        ORDER BY path, line, id
        """,
        (pr["id"],),
    ).fetchall()

    payload = _row_to_dict(pr)
    payload["author"] = payload.pop("author_login")
    payload["reviews"] = [_row_to_dict(row) for row in reviews]
    payload["review_comments"] = [_row_to_dict(row) for row in review_comments]
    return payload


def generate_pr_report(repo_name: str, db_path: Path, pr_number: int) -> dict:
    ok, markdown, error = _run_markdown(
        "analyze_prs.py",
        ["--db-path", str(db_path), "pr-report", "--number", str(pr_number)],
    )
    packet_dir = repo_packet_dir(repo_name)
    md_path = packet_dir / f"pr-{pr_number}-report.md"
    json_path = packet_dir / f"pr-{pr_number}-report.json"
    if ok:
        _write_markdown(md_path, markdown)

    payload = {
        "packet_type": "pr_report",
        "repo": repo_name,
        "pr_number": pr_number,
        "source_db_path": str(db_path),
        "generated_at": _timestamp(),
        "generated": ok,
        "markdown_path": str(md_path) if ok else None,
        "markdown_preview": markdown.splitlines()[:20] if ok else [],
        "error": None if ok else error,
        "state": None,
        "author": None,
        "changed_files": None,
        "additions": None,
        "deletions": None,
        "body": "",
        "reviews": [],
        "review_comments": [],
        "evidence": {
            "overview": {
                "pr_number": pr_number,
                "state": None,
                "author": None,
                "changed_files": None,
                "additions": None,
                "deletions": None,
            },
            "review_summary": {
                "review_count": 0,
                "review_comment_count": 0,
                "approved_count": 0,
                "changes_requested_count": 0,
                "commented_count": 0,
            },
            "reviewers": [],
            "hotspot_paths": [],
            "review_samples": [],
            "comment_samples": [],
        },
    }
    if ok:
        with _connect(db_path) as connection:
            data = _pr_report_data(connection, pr_number)
            if data is not None:
                payload.update(data)
                payload["thread_samples"] = build_threads_for_packet(db_path, pr_number, limit=5)
                payload["evidence"] = _pr_report_evidence(payload)

    validate_payload("pr-report", payload)
    _write_json(json_path, payload)
    payload["json_path"] = str(json_path)
    return payload
