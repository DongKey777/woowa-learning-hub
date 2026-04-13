from __future__ import annotations

import json
from pathlib import Path

from .shell import run_capture


def read_git_context(repo_path: Path) -> dict:
    branch_result = run_capture(["git", "branch", "--show-current"], cwd=repo_path)
    status_result = run_capture(["git", "status", "--short"], cwd=repo_path)
    diff_result = run_capture(["git", "diff", "--name-only"], cwd=repo_path)

    return {
        "branch": branch_result.stdout.strip() if branch_result.returncode == 0 else None,
        "status_lines": [line for line in status_result.stdout.splitlines() if line.strip()],
        "diff_files": [line for line in diff_result.stdout.splitlines() if line.strip()],
    }


def read_current_pr(repo_path: Path) -> dict | None:
    result = run_capture(["gh", "pr", "view", "--json", "number,url,title"], cwd=repo_path)
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None
