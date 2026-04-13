from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .comment_classifier import classify_all
from .mission_map import write_mission_map
from .paths import DEFAULT_SCHEMA_PATH, PR_ARCHIVE_DIR, ensure_repo_layout, repo_archive_db
from .shell import run_capture


MIN_PRS_FOR_READY = 20
MIN_REVIEW_COVERAGE_RATIO = 0.4


class ArchiveSyncError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        command: list[str] | None = None,
        stdout: str | None = None,
        stderr: str | None = None,
    ) -> None:
        super().__init__(message)
        self.command = command or []
        self.stdout = stdout or ""
        self.stderr = stderr or ""

    def to_dict(self) -> dict:
        return {
            "message": str(self),
            "command": self.command,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def archive_status_path(repo_name: str) -> Path:
    return ensure_repo_layout(repo_name) / "archive" / "status.json"


def _count_archive_signals(db_path: Path) -> dict:
    if not db_path.exists() or db_path.stat().st_size == 0:
        return {
            "total_prs": 0,
            "total_reviews": 0,
            "total_review_comments": 0,
            "prs_with_review_activity": 0,
            "earliest_pr_created_at": None,
            "latest_pr_created_at": None,
        }
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        pr_row = connection.execute(
            """
            SELECT COUNT(*) AS total_prs,
                   MIN(created_at) AS earliest,
                   MAX(created_at) AS latest
            FROM pull_requests_current
            WHERE is_missing = 0
            """
        ).fetchone()
        total_prs = pr_row["total_prs"] if pr_row else 0
        earliest = pr_row["earliest"] if pr_row else None
        latest = pr_row["latest"] if pr_row else None

        review_row = connection.execute(
            "SELECT COUNT(*) AS total_reviews FROM pull_request_reviews_current"
        ).fetchone()
        total_reviews = review_row["total_reviews"] if review_row else 0

        comment_row = connection.execute(
            "SELECT COUNT(*) AS total_comments FROM pull_request_review_comments_current"
        ).fetchone()
        total_review_comments = comment_row["total_comments"] if comment_row else 0

        coverage_row = connection.execute(
            """
            SELECT COUNT(DISTINCT pr_id) AS covered FROM (
                SELECT pull_request_id AS pr_id FROM pull_request_reviews_current
                UNION
                SELECT pull_request_id AS pr_id FROM pull_request_review_comments_current
            )
            """
        ).fetchone()
        prs_with_review_activity = coverage_row["covered"] if coverage_row else 0

        return {
            "total_prs": total_prs,
            "total_reviews": total_reviews,
            "total_review_comments": total_review_comments,
            "prs_with_review_activity": prs_with_review_activity,
            "earliest_pr_created_at": earliest,
            "latest_pr_created_at": latest,
        }
    finally:
        connection.close()


def _derive_bootstrap_state(signals: dict, latest_run: dict | None) -> tuple[str, list[str]]:
    reasons: list[str] = []
    total_prs = signals.get("total_prs", 0)
    covered = signals.get("prs_with_review_activity", 0)

    if total_prs == 0:
        reasons.append("no collection run recorded yet")
        return "uninitialized", reasons

    if latest_run is None:
        reasons.append("archive has PR data but no collection run metadata")
        return "bootstrapping", reasons

    review_ratio = (covered / total_prs) if total_prs else 0.0

    if total_prs < MIN_PRS_FOR_READY:
        reasons.append(f"only {total_prs} PRs collected (threshold {MIN_PRS_FOR_READY})")
        return "bootstrapping", reasons

    if review_ratio < MIN_REVIEW_COVERAGE_RATIO:
        reasons.append(
            f"review/comment coverage {review_ratio:.2f} below threshold {MIN_REVIEW_COVERAGE_RATIO}"
        )
        return "bootstrapping", reasons

    if not latest_run.get("success"):
        reasons.append("latest collection run failed")
        return "bootstrapping", reasons

    reasons.append(
        f"{total_prs} PRs, {covered} with review activity (ratio {review_ratio:.2f})"
    )
    return "ready", reasons


def _derive_data_confidence(bootstrap_state: str) -> str:
    if bootstrap_state == "ready":
        return "ready"
    if bootstrap_state == "bootstrapping":
        return "partial"
    return "bootstrap"


def _bootstrap_commands(repo_name: str) -> dict:
    prefix = "python3 -m scripts.workbench"
    return {
        "archive_status": f"{prefix} archive-status --repo {repo_name}",
        "bootstrap": f"{prefix} bootstrap-repo --repo {repo_name}",
        "retry_bootstrap": f"{prefix} bootstrap-repo --repo {repo_name}",
        "coach_run": f"{prefix} coach-run --repo {repo_name} --prompt \"이 리뷰 기준 다음 액션 뭐야?\"",
    }


def _bootstrap_guidance(repo_name: str, bootstrap_state: str, signals: dict, latest_run: dict | None) -> dict:
    commands = _bootstrap_commands(repo_name)
    total_prs = signals.get("total_prs", 0)
    last_failure = (latest_run or {}).get("latest_failure")

    if bootstrap_state == "ready":
        return {
            "action": "none",
            "message": "초기 자료 수집이 완료되어 바로 코칭 세션을 진행할 수 있습니다.",
            "last_failure": last_failure,
            "next_steps": [
                {
                    "title": "Start coaching",
                    "why": "학습 자료가 충분하므로 현재 질문으로 바로 세션을 시작하면 됩니다.",
                    "command": commands["coach_run"],
                }
            ],
            "commands": commands,
        }

    if latest_run and not latest_run.get("success"):
        return {
            "action": "retry_bootstrap",
            "message": "가장 최근 자료 수집이 실패했습니다. 오류 원인을 확인한 뒤 bootstrap을 다시 실행해야 합니다.",
            "last_failure": last_failure,
            "next_steps": [
                {
                    "title": "Check archive status",
                    "why": "마지막 실패 원인과 남아 있는 데이터 양을 먼저 확인합니다.",
                    "command": commands["archive_status"],
                },
                {
                    "title": "Retry bootstrap",
                    "why": "초기 수집이 실패한 상태라 다시 full bootstrap이 필요합니다.",
                    "command": commands["retry_bootstrap"],
                },
            ],
            "commands": commands,
        }

    if total_prs == 0:
        return {
            "action": "bootstrap_required",
            "message": "아직 이 미션의 PR 학습 자료가 없습니다. 첫 bootstrap이 먼저 필요합니다.",
            "last_failure": last_failure,
            "next_steps": [
                {
                    "title": "Run initial bootstrap",
                    "why": "다른 크루 PR과 리뷰를 학습 근거로 쓰려면 한 번 full 수집을 해야 합니다.",
                    "command": commands["bootstrap"],
                }
            ],
            "commands": commands,
        }

    return {
        "action": "resume_bootstrap",
        "message": f"초기 자료 수집이 아직 덜 끝났습니다. 현재 {total_prs}개 PR만 수집되어 있어 추가 bootstrap이 필요합니다.",
        "last_failure": last_failure,
        "next_steps": [
            {
                "title": "Check archive status",
                "why": "현재 수집량과 ready 기준까지 얼마나 부족한지 먼저 확인합니다.",
                "command": commands["archive_status"],
            },
            {
                "title": "Resume bootstrap",
                "why": "partial 상태라 PR와 리뷰 근거를 더 모아야 추천 품질이 안정됩니다.",
                "command": commands["bootstrap"],
            },
            {
                "title": "Continue limited coaching if needed",
                "why": "지금도 partial 근거로 학습은 가능하지만, 답변 범위는 제한적입니다.",
                "command": commands["coach_run"],
            },
        ],
        "commands": commands,
    }


def compute_archive_status(repo_name: str, freshness_hours: int = 6) -> dict:
    db_path = repo_archive_db(repo_name)
    signals = _count_archive_signals(db_path)
    latest_run = latest_collection_run(db_path)
    sync_status = archive_sync_status(db_path, freshness_hours=freshness_hours)
    bootstrap_state, reasons = _derive_bootstrap_state(signals, latest_run)
    data_confidence = _derive_data_confidence(bootstrap_state)
    bootstrap_guidance = _bootstrap_guidance(repo_name, bootstrap_state, signals, latest_run)

    return {
        "repo": repo_name,
        "db_path": str(db_path),
        "bootstrap_state": bootstrap_state,
        "data_confidence": data_confidence,
        "reasons": reasons,
        "thresholds": {
            "min_prs": MIN_PRS_FOR_READY,
            "min_review_coverage_ratio": MIN_REVIEW_COVERAGE_RATIO,
        },
        "signals": signals,
        "latest_run": latest_run,
        "sync_status": sync_status,
        "bootstrap_guidance": bootstrap_guidance,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }


def write_archive_status(repo_name: str, freshness_hours: int = 6) -> dict:
    status = compute_archive_status(repo_name, freshness_hours=freshness_hours)
    path = archive_status_path(repo_name)
    path.write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    status["status_path"] = str(path)
    return status


def latest_collection_failure(db_path: Path, collection_run_id: int | None = None) -> dict | None:
    if not db_path.exists() or db_path.stat().st_size == 0:
        return None

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        if collection_run_id is None:
            row = connection.execute(
                """
                SELECT collection_run_id, github_pr_number, stage, error_message, created_at
                FROM collection_run_failures
                ORDER BY id DESC
                LIMIT 1
                """
            ).fetchone()
        else:
            row = connection.execute(
                """
                SELECT collection_run_id, github_pr_number, stage, error_message, created_at
                FROM collection_run_failures
                WHERE collection_run_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (collection_run_id,),
            ).fetchone()
        if row is None:
            return None
        return {key: row[key] for key in row.keys()}
    finally:
        connection.close()


def latest_collection_run(db_path: Path) -> dict | None:
    if not db_path.exists() or db_path.stat().st_size == 0:
        return None

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        row = connection.execute(
            """
            SELECT mode, started_at, finished_at, success, pr_count, notes
            FROM collection_runs
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
        if row is None:
            return None

        pr_row = connection.execute(
            """
            SELECT COUNT(*) AS current_pr_count
            FROM pull_requests_current
            WHERE is_missing = 0
            """
        ).fetchone()
        payload = {key: row[key] for key in row.keys()}
        try:
            payload["notes_json"] = json.loads(payload.get("notes") or "")
        except json.JSONDecodeError:
            payload["notes_json"] = None
        payload["current_pr_count"] = pr_row["current_pr_count"] if pr_row else 0
        latest_run_id = connection.execute(
            """
            SELECT id
            FROM collection_runs
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
        run_id = latest_run_id["id"] if latest_run_id else None
        failure_row = connection.execute(
            """
            SELECT COUNT(*) AS failure_count
            FROM collection_run_failures
            WHERE collection_run_id = ?
            """,
            (run_id,),
        ).fetchone() if run_id is not None else None
        payload["failure_count"] = failure_row["failure_count"] if failure_row else 0
        payload["latest_failure"] = latest_collection_failure(db_path, run_id)
        return payload
    finally:
        connection.close()


def archive_sync_status(db_path: Path, freshness_hours: int = 6) -> dict:
    latest = latest_collection_run(db_path)
    if latest is None:
        return {
            "needs_sync": True,
            "reason": "archive missing",
            "latest_run": None,
            "recommended_mode": "full",
        }

    if not latest.get("success"):
        return {
            "needs_sync": True,
            "reason": "latest run failed",
            "latest_run": latest,
            "recommended_mode": "incremental",
        }

    finished_at = _parse_iso(latest.get("finished_at"))
    if finished_at is None:
        return {
            "needs_sync": True,
            "reason": "latest run has no finished_at",
            "latest_run": latest,
            "recommended_mode": "incremental",
        }

    age = datetime.now(timezone.utc) - finished_at.astimezone(timezone.utc)
    if age > timedelta(hours=freshness_hours):
        return {
            "needs_sync": True,
            "reason": f"archive older than {freshness_hours}h",
            "latest_run": latest,
            "recommended_mode": "incremental",
        }

    return {
        "needs_sync": False,
        "reason": "archive fresh",
        "latest_run": latest,
        "recommended_mode": "incremental",
    }


def sync_repo_archive(
    repo: dict,
    mode: str | None = None,
    since: str | None = None,
    limit: int | None = None,
    force: bool = False,
) -> dict:
    upstream = repo.get("upstream")
    if not upstream or "/" not in upstream:
        raise SystemExit(f"invalid upstream for repo {repo.get('name')}: {upstream}")

    owner, repo_name = upstream.split("/", 1)
    db_path = repo_archive_db(repo["name"])
    status_before = archive_sync_status(db_path)
    mission_map = write_mission_map(repo)
    mission_keywords = ((mission_map.get("analysis") or {}).get("retrieval_terms") or [])[:12]

    resolved_mode = mode or status_before["recommended_mode"]
    if force and resolved_mode != "full":
        resolved_mode = "incremental"
    if status_before["latest_run"] is None:
        resolved_mode = "full"

    resolved_since = since
    if resolved_mode == "incremental" and resolved_since is None and status_before["latest_run"]:
        resolved_since = status_before["latest_run"].get("finished_at")

    cmd = [
        "python3", str(PR_ARCHIVE_DIR / "collect_prs.py"),
        "--owner", owner,
        "--repo", repo_name,
        "--mode", resolved_mode,
        "--db-path", str(db_path),
        "--schema-path", str(DEFAULT_SCHEMA_PATH),
    ]
    if repo.get("track"):
        cmd.extend(["--track", repo["track"]])
    if repo.get("mission") or repo.get("name"):
        cmd.extend(["--mission", repo.get("mission") or repo["name"]])
    if repo.get("title_contains"):
        cmd.extend(["--title-contains", repo["title_contains"]])
    if repo.get("branch_hint"):
        cmd.extend(["--branch-hint", repo["branch_hint"]])
    if repo.get("current_pr_title"):
        cmd.extend(["--current-pr-title", repo["current_pr_title"]])
    for keyword in mission_keywords:
        cmd.extend(["--mission-keyword", keyword])
    if resolved_since:
        cmd.extend(["--since", resolved_since])
    if limit is not None:
        cmd.extend(["--limit", str(limit)])

    result = run_capture(cmd)
    if result.returncode != 0:
        raise ArchiveSyncError(
            result.stderr.strip() or "archive sync failed",
            command=cmd,
            stdout=result.stdout.strip(),
            stderr=result.stderr.strip(),
        )

    classify_result = classify_all(db_path)

    latest = latest_collection_run(db_path)
    return {
        "repo": repo["name"],
        "db_path": str(db_path),
        "requested_mode": mode,
        "mode": resolved_mode,
        "since": resolved_since,
        "forced": force,
        "title_contains": repo.get("title_contains"),
        "mission_map_path": mission_map.get("json_path"),
        "mission_keywords": mission_keywords,
        "status_before": status_before,
        "status_after": archive_sync_status(db_path),
        "latest_run": latest,
        "classify_result": classify_result,
        "stdout": result.stdout.strip(),
    }


def ensure_repo_archive(
    repo: dict,
    freshness_hours: int = 6,
    force: bool = False,
    limit: int | None = None,
    allow_full: bool = True,
) -> dict:
    db_path = repo_archive_db(repo["name"])
    status = archive_sync_status(db_path, freshness_hours=freshness_hours)

    if status["recommended_mode"] == "full" and not allow_full:
        write_archive_status(repo["name"], freshness_hours=freshness_hours)
        return {
            "repo": repo["name"],
            "db_path": str(db_path),
            "skipped": True,
            "reason": "full sync required but not allowed in this context",
            "latest_run": status["latest_run"],
            "status_after": status,
            "full_sync_blocked": True,
        }

    if not force and not status["needs_sync"]:
        write_archive_status(repo["name"], freshness_hours=freshness_hours)
        return {
            "repo": repo["name"],
            "db_path": str(db_path),
            "skipped": True,
            "reason": status["reason"],
            "latest_run": status["latest_run"],
            "status_after": status,
        }

    result = sync_repo_archive(
        repo,
        mode=status["recommended_mode"],
        limit=limit,
        force=force,
    )
    result["skipped"] = False
    write_archive_status(repo["name"], freshness_hours=freshness_hours)
    return result


def bootstrap_repo_archive(
    repo: dict,
    limit: int | None = None,
    freshness_hours: int = 6,
) -> dict:
    result = sync_repo_archive(repo, mode="full", limit=limit, force=False)
    result["skipped"] = False
    result["bootstrap"] = True
    archive_status = write_archive_status(repo["name"], freshness_hours=freshness_hours)
    result["archive_status"] = archive_status
    return result
