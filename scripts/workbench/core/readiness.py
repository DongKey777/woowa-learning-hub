from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from .archive import write_archive_status
from .mission_map import write_mission_map
from .paths import MISSIONS_DIR, REGISTRY_PATH, ensure_global_layout
from .repo_intake import resolve_repo_input
from .registry import list_repos
from .shell import run_capture


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def environment_status() -> dict:
    ensure_global_layout()
    gh_installed = shutil.which("gh") is not None
    gh_auth = None
    if gh_installed:
        result = run_capture(["gh", "auth", "status"])
        gh_auth = result.returncode == 0
    return {
        "python3": shutil.which("python3") is not None,
        "gh": gh_installed,
        "gh_auth": gh_auth,
        "missions_dir_exists": MISSIONS_DIR.exists(),
        "registry_exists": REGISTRY_PATH.exists(),
    }


def _under_missions(path: Path) -> bool:
    try:
        path.relative_to(MISSIONS_DIR)
        return True
    except ValueError:
        return False


def _repo_issues(repo: dict) -> list[str]:
    issues = []
    repo_path = Path(repo["path"])
    if not repo_path.exists():
        issues.append("repo path does not exist")
        return issues
    if not (repo_path / ".git").exists():
        issues.append("repo path is not a git repository")
    if not repo.get("upstream"):
        issues.append("upstream is missing")
    if not repo.get("track"):
        issues.append("track is missing")
    if not repo.get("mission"):
        issues.append("mission is missing")
    if not _under_missions(repo_path):
        issues.append("repo is outside missions/ convention")
    return issues


def _readiness_summary(environment: dict, repo: dict, archive_status: dict, issues: list[str]) -> dict:
    if not environment.get("python3"):
        return {
            "stage": "environment_blocked",
            "coaching_available": False,
            "message": "python3가 없어 workbench를 실행할 수 없습니다.",
        }
    if not environment.get("gh"):
        return {
            "stage": "environment_blocked",
            "coaching_available": False,
            "message": "gh가 없어 PR 수집을 진행할 수 없습니다.",
        }
    if environment.get("gh_auth") is False:
        return {
            "stage": "environment_blocked",
            "coaching_available": False,
            "message": "gh 인증이 되어 있지 않아 PR 수집을 진행할 수 없습니다.",
        }
    if any(issue in {"repo path does not exist", "repo path is not a git repository"} for issue in issues):
        return {
            "stage": "repo_blocked",
            "coaching_available": False,
            "message": "미션 repo 경로가 유효하지 않아 코칭 세션을 시작할 수 없습니다.",
        }

    bootstrap_state = archive_status.get("bootstrap_state")
    if bootstrap_state == "ready":
        return {
            "stage": "ready",
            "coaching_available": True,
            "message": "이 repo는 바로 코칭 세션을 진행할 준비가 되어 있습니다.",
        }
    if bootstrap_state == "bootstrapping":
        return {
            "stage": "bootstrapping",
            "coaching_available": True,
            "message": "partial 자료로 코칭은 가능하지만, 더 풍부한 근거를 위해 bootstrap을 이어가는 편이 좋습니다.",
        }
    return {
        "stage": "needs_bootstrap",
        "coaching_available": False,
        "message": "아직 이 repo의 PR 학습 자료가 없어 첫 bootstrap이 필요합니다.",
    }


def _next_steps(environment: dict, repo: dict, archive_status: dict, issues: list[str]) -> list[dict]:
    steps = []
    if not environment.get("gh"):
        steps.append({
            "title": "Install GitHub CLI",
            "why": "PR 수집 기능은 gh에 의존합니다.",
            "command": "gh --version",
        })
        return steps
    if environment.get("gh_auth") is False:
        steps.append({
            "title": "Authenticate GitHub CLI",
            "why": "수집 전에 gh 인증이 필요합니다.",
            "command": "gh auth login -h github.com -p https -w",
        })

    guidance = archive_status.get("bootstrap_guidance") or {}
    steps.extend(guidance.get("next_steps", []))

    if "repo is outside missions/ convention" in issues:
        steps.append({
            "title": "Keep the repo under missions/ if possible",
            "why": "공유된 구조에서는 missions/ 아래 repo가 가장 자연스럽지만, 현재 경로에서도 동작은 가능합니다.",
            "command": f"mv \"{repo['path']}\" \"{MISSIONS_DIR / Path(repo['path']).name}\"",
        })
    return steps[:4]


def build_repo_readiness(
    *,
    repo_name: str | None = None,
    repo_path: str | None = None,
    freshness_hours: int = 6,
) -> dict:
    environment = environment_status()
    repo, resolution = resolve_repo_input(repo_name=repo_name, repo_path=repo_path, auto_register=True)
    mission_map = write_mission_map(repo)
    archive_status = write_archive_status(repo["name"], freshness_hours=freshness_hours)
    issues = _repo_issues(repo)
    readiness = _readiness_summary(environment, repo, archive_status, issues)

    return {
        "report_type": "repo_readiness",
        "generated_at": _timestamp(),
        "repo_resolution": resolution,
        "environment": environment,
        "mission_map_path": mission_map.get("json_path"),
        "mission_map_summary": mission_map.get("summary", []),
        "repo": {
            "name": repo.get("name"),
            "path": repo.get("path"),
            "under_missions_dir": _under_missions(Path(repo["path"])),
            "upstream": repo.get("upstream"),
            "track": repo.get("track"),
            "mission": repo.get("mission"),
            "title_contains": repo.get("title_contains"),
            "origin_full_name": repo.get("origin_full_name"),
            "branch_hint": repo.get("branch_hint"),
            "current_pr_title": repo.get("current_pr_title"),
        },
        "readiness": {
            **readiness,
            "issues": issues,
        },
        "archive_status": archive_status,
        "next_steps": _next_steps(environment, repo, archive_status, issues),
    }


def build_registry_audit(*, freshness_hours: int = 6) -> dict:
    environment = environment_status()
    repos_output = []
    summary = {
        "ready": 0,
        "bootstrapping": 0,
        "needs_bootstrap": 0,
        "blocked": 0,
    }

    for repo in list_repos():
        issues = _repo_issues(repo)
        mission_map = write_mission_map(repo) if Path(repo["path"]).exists() else None
        archive_status = write_archive_status(repo["name"], freshness_hours=freshness_hours)
        readiness = _readiness_summary(environment, repo, archive_status, issues)
        stage = readiness["stage"]
        if stage == "ready":
            summary["ready"] += 1
        elif stage == "bootstrapping":
            summary["bootstrapping"] += 1
        elif stage == "needs_bootstrap":
            summary["needs_bootstrap"] += 1
        else:
            summary["blocked"] += 1

        repos_output.append({
            "name": repo.get("name"),
            "path": repo.get("path"),
            "track": repo.get("track"),
            "mission": repo.get("mission"),
            "upstream": repo.get("upstream"),
            "title_contains": repo.get("title_contains"),
            "readiness_stage": stage,
            "coaching_available": readiness["coaching_available"],
            "issues": issues,
            "bootstrap_action": (archive_status.get("bootstrap_guidance") or {}).get("action"),
            "bootstrap_message": (archive_status.get("bootstrap_guidance") or {}).get("message"),
            "mission_kind": ((mission_map or {}).get("analysis") or {}).get("mission_kind"),
            "mission_summary": (mission_map or {}).get("summary", [])[:2] if mission_map else [],
            "archive_status_path": archive_status.get("status_path"),
        })

    return {
        "report_type": "registry_audit",
        "generated_at": _timestamp(),
        "environment": environment,
        "repo_count": len(repos_output),
        "summary": summary,
        "repos": repos_output,
    }
