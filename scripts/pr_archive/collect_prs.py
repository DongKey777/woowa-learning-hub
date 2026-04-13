#!/usr/bin/env python3
"""Collect GitHub PR data into the PR archive database."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from scripts.pr_archive.db import ArchiveDatabase
from scripts.pr_archive.github_client import GitHubCLIClient, GitHubCLIError
from scripts.pr_archive.mission_relevance import build_mission_signals, filter_relevant_pull_requests


DEFAULT_DB_PATH = Path("catalog/pr-datasets/github-prs.sqlite3")
DEFAULT_SCHEMA_PATH = Path("scripts/pr_archive/schema.sql")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect PR metadata for learning.")
    parser.add_argument("--owner", required=True)
    parser.add_argument("--repo", required=True)
    parser.add_argument("--track")
    parser.add_argument("--mission")
    parser.add_argument("--mode", choices=("full", "incremental"), default="full")
    parser.add_argument("--since", help="ISO-8601 lower bound for incremental sync")
    parser.add_argument("--limit", type=int)
    parser.add_argument("--title-contains", help="Collect only PRs whose title contains this text")
    parser.add_argument("--branch-hint", help="Current local branch hint such as step2")
    parser.add_argument("--current-pr-title", help="Current learner PR title when available")
    parser.add_argument("--mission-keyword", action="append", dest="mission_keywords", default=[])
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH)
    parser.add_argument("--schema-path", type=Path, default=DEFAULT_SCHEMA_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    collected_at = now_iso()
    client = GitHubCLIClient(args.owner, args.repo)
    database = ArchiveDatabase(args.db_path)
    database.initialize_schema(args.schema_path)
    client.fetch_authenticated_user()

    repository_id = database.upsert_repository(
        owner=args.owner,
        name=args.repo,
        full_name=f"{args.owner}/{args.repo}",
        track=args.track,
        mission_name=args.mission,
    )
    collection_run_id = database.start_collection_run(repository_id, args.mode, collected_at)

    processed_count = 0
    try:
        pull_requests = client.fetch_pull_requests()
        targets = filter_pull_requests(
            pull_requests=pull_requests,
            repo_name=args.repo,
            mission=args.mission,
            mode=args.mode,
            since=args.since,
            limit=args.limit,
            title_contains=args.title_contains,
            branch_hint=args.branch_hint,
            current_pr_title=args.current_pr_title,
            mission_keywords=args.mission_keywords,
        )
        if args.mode == "full":
            database.mark_pull_requests_missing(repository_id)

        for pull_request_summary in targets["pull_requests"]:
            collect_pull_request(
                client=client,
                database=database,
                collection_run_id=collection_run_id,
                repository_id=repository_id,
                pull_request_number=pull_request_summary["number"],
                collected_at=collected_at,
            )
            processed_count += 1

        database.finish_collection_run(
            collection_run_id=collection_run_id,
            finished_at=now_iso(),
            success=True,
            pr_count=processed_count,
            notes=targets["summary_json"],
        )
    except Exception as e:
        database.finish_collection_run(
            collection_run_id=collection_run_id,
            finished_at=now_iso(),
            success=False,
            pr_count=processed_count,
            notes=str(e),
        )
        raise


def collect_pull_request(
        client: GitHubCLIClient,
        database: ArchiveDatabase,
        collection_run_id: int,
        repository_id: int,
        pull_request_number: int,
        collected_at: str,
) -> None:
    try:
        detail = client.fetch_pull_request_detail(pull_request_number)
        pull_request_id = database.upsert_pull_request(repository_id, detail, collected_at)
        database.mark_pr_children_missing(pull_request_id)

        for file_data in client.fetch_pull_request_files(pull_request_number):
            database.upsert_pull_request_file(pull_request_id, file_data, collected_at)

        for review in client.fetch_pull_request_reviews(pull_request_number):
            database.upsert_review(pull_request_id, review, collected_at)

        for comment in client.fetch_pull_request_review_comments(pull_request_number):
            database.upsert_review_comment(pull_request_id, comment, collected_at)

        for comment in client.fetch_pull_request_issue_comments(pull_request_number):
            database.upsert_issue_comment(pull_request_id, comment, collected_at)
    except GitHubCLIError as e:
        database.record_failure(collection_run_id, pull_request_number, "github_api", str(e))
        raise
    except Exception as e:
        database.record_failure(collection_run_id, pull_request_number, "persist", str(e))
        raise


def filter_pull_requests(
        pull_requests: list[dict[str, Any]],
        repo_name: str,
        mission: str | None,
        mode: str,
        since: str | None,
        limit: int | None,
        title_contains: str | None,
        branch_hint: str | None,
        current_pr_title: str | None,
        mission_keywords: list[str] | None,
) -> dict[str, Any]:
    targets = pull_requests
    if mode == "incremental" and since:
        targets = [pull_request for pull_request in pull_requests if pull_request["updated_at"] >= since]
    signals = build_mission_signals(
        repo_name=repo_name,
        mission_name=mission,
        title_hint=title_contains,
        branch_hint=branch_hint,
        current_pr_title=current_pr_title,
        mission_keywords=mission_keywords,
    )
    selected, summary = filter_relevant_pull_requests(targets, signals, limit=limit)
    return {
        "pull_requests": selected,
        "summary": summary,
        "summary_json": json.dumps({
            "status": "completed",
            "relevance": summary,
            "title_contains": title_contains,
            "branch_hint": branch_hint,
            "current_pr_title": current_pr_title,
            "mission_keywords": mission_keywords or [],
        }, ensure_ascii=False),
    }


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    main()
