from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .git_context import read_current_pr
from .paths import MISSIONS_DIR
from .registry import find_repo, find_repo_by_path, upsert_repo
from .shell import run_capture


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_repo_path(repo_path: str | Path) -> Path:
    return Path(repo_path).expanduser().resolve()


def _parse_remote_full_name(url: str | None) -> str | None:
    if not url:
        return None
    normalized = url.strip().removesuffix("/")
    https_match = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/]+?)(?:\.git)?$", normalized)
    if https_match:
        return f"{https_match.group('owner')}/{https_match.group('repo')}"
    return None


def _infer_track(repo_path: Path) -> str | None:
    parts = repo_path.parts
    for index, part in enumerate(parts):
        if part == "tracks" and index + 1 < len(parts):
            return parts[index + 1]
    return None


def _extract_title_contains(current_pr_title: str | None, branch: str | None) -> str | None:
    candidates = [current_pr_title or "", branch or ""]
    patterns = [
        r"(사이클\s*\d+)",
        r"(사이클\d+)",
        r"(\d+단계)",
        r"(step\s*\d+)",
        r"(step\d+)",
    ]
    for raw in candidates:
        text = raw.strip()
        if not text:
            continue
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if not match:
                continue
            value = match.group(1).replace(" ", "")
            step_match = re.fullmatch(r"step(\d+)", value, flags=re.IGNORECASE)
            if step_match:
                return f"사이클{step_match.group(1)}"
            return value
    return None


def _git_remote_url(repo_path: Path, remote_name: str) -> str | None:
    result = run_capture(["git", "remote", "get-url", remote_name], cwd=repo_path)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def _gh_repo_metadata(repo_path: Path) -> dict | None:
    result = run_capture(["gh", "repo", "view", "--json", "nameWithOwner,isFork,parent,url"], cwd=repo_path)
    if result.returncode != 0:
        return None
    try:
        raw = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

    parent = raw.get("parent") or {}
    parent_owner = (parent.get("owner") or {}).get("login")
    parent_name = parent.get("name")
    upstream = None
    if raw.get("isFork") and parent_owner and parent_name:
        upstream = f"{parent_owner}/{parent_name}"

    return {
        "origin_full_name": raw.get("nameWithOwner"),
        "upstream": upstream or raw.get("nameWithOwner"),
        "origin_url": raw.get("url"),
        "is_fork": bool(raw.get("isFork")),
    }


def detect_repo_metadata(repo_path: str | Path, repo_name: str | None = None) -> dict:
    resolved_path = _normalize_repo_path(repo_path)
    if not (resolved_path / ".git").exists():
        raise SystemExit(f"not a git repository: {resolved_path}")

    branch_result = run_capture(["git", "branch", "--show-current"], cwd=resolved_path)
    branch = branch_result.stdout.strip() if branch_result.returncode == 0 else None
    current_pr = read_current_pr(resolved_path)
    gh_repo = _gh_repo_metadata(resolved_path) or {}
    origin_url = gh_repo.get("origin_url") or _git_remote_url(resolved_path, "origin")
    origin_full_name = gh_repo.get("origin_full_name") or _parse_remote_full_name(origin_url)

    upstream_remote_url = _git_remote_url(resolved_path, "upstream")
    upstream_full_name = gh_repo.get("upstream") or _parse_remote_full_name(upstream_remote_url) or origin_full_name

    mission = upstream_full_name.split("/", 1)[1] if upstream_full_name and "/" in upstream_full_name else resolved_path.name
    detected_name = repo_name or resolved_path.name
    title_contains = _extract_title_contains((current_pr or {}).get("title"), branch)

    return {
        "name": detected_name,
        "path": str(resolved_path),
        "upstream": upstream_full_name,
        "track": _infer_track(resolved_path),
        "mission": mission,
        "title_contains": title_contains,
        "origin_full_name": origin_full_name,
        "origin_url": origin_url,
        "branch_hint": branch,
        "current_pr_title": (current_pr or {}).get("title"),
        "current_pr": current_pr,
        "auto_detected_at": _timestamp(),
    }


def _refresh_registered_repo(repo: dict) -> dict:
    path = repo.get("path")
    if not path:
        return repo
    resolved_path = _normalize_repo_path(path)
    if not (resolved_path / ".git").exists():
        return repo

    detected = detect_repo_metadata(resolved_path, repo_name=repo.get("name"))
    return upsert_repo(
        name=repo.get("name") or detected["name"],
        path=resolved_path,
        upstream=detected.get("upstream") or repo.get("upstream"),
        track=detected.get("track") or repo.get("track"),
        mission=detected.get("mission") or repo.get("mission"),
        title_contains=detected.get("title_contains") or repo.get("title_contains"),
        extra_fields={
            "origin_full_name": detected.get("origin_full_name") or repo.get("origin_full_name"),
            "origin_url": detected.get("origin_url") or repo.get("origin_url"),
            "branch_hint": detected.get("branch_hint") or repo.get("branch_hint"),
            "current_pr_title": detected.get("current_pr_title") or repo.get("current_pr_title"),
            "auto_detected_at": detected.get("auto_detected_at"),
        },
    )


def resolve_repo_input(repo_name: str | None = None, repo_path: str | None = None, auto_register: bool = True) -> tuple[dict, dict]:
    if repo_name:
        try:
            repo = find_repo(repo_name)
            if auto_register:
                repo = _refresh_registered_repo(repo)
            return repo, {"source": "registry", "repo_name": repo_name, "path": repo.get("path")}
        except SystemExit:
            pass

    candidate_path = _normalize_repo_path(repo_path) if repo_path else None
    if candidate_path is None and repo_name:
        default_path = MISSIONS_DIR / repo_name
        if default_path.exists():
            candidate_path = default_path.resolve()

    if candidate_path is None:
        raise SystemExit("repo could not be resolved; provide --repo or --path")

    existing = find_repo_by_path(candidate_path)
    if existing:
        if auto_register:
            existing = _refresh_registered_repo(existing)
        return existing, {"source": "registry-path", "repo_name": existing.get("name"), "path": existing.get("path")}

    detected = detect_repo_metadata(candidate_path, repo_name=repo_name)
    if not auto_register:
        return detected, {"source": "detected", "repo_name": detected["name"], "path": detected["path"]}

    repo = upsert_repo(
        name=detected["name"],
        path=Path(detected["path"]),
        upstream=detected.get("upstream"),
        track=detected.get("track"),
        mission=detected.get("mission"),
        title_contains=detected.get("title_contains"),
        extra_fields={
            "origin_full_name": detected.get("origin_full_name"),
            "origin_url": detected.get("origin_url"),
            "branch_hint": detected.get("branch_hint"),
            "current_pr_title": detected.get("current_pr_title"),
            "auto_detected_at": detected.get("auto_detected_at"),
        },
    )
    return repo, {"source": "auto-onboarded", "repo_name": repo.get("name"), "path": repo.get("path")}
