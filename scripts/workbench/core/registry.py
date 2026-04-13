from __future__ import annotations

import json
from pathlib import Path

from .paths import REGISTRY_PATH, ensure_global_layout


def load_registry() -> dict:
    ensure_global_layout()
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def save_registry(data: dict) -> None:
    REGISTRY_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def list_repos() -> list[dict]:
    return load_registry().get("repos", [])


def find_repo(name: str) -> dict:
    for repo in list_repos():
        if repo.get("name") == name:
            return repo
    raise SystemExit(f"repo not found in registry: {name}")


def find_repo_by_path(path: Path) -> dict | None:
    resolved = str(path.resolve())
    for repo in list_repos():
        if repo.get("path") == resolved:
            return repo
    return None


def upsert_repo(
    *,
    name: str,
    path: Path,
    upstream: str | None,
    track: str | None,
    mission: str | None,
    title_contains: str | None,
    extra_fields: dict | None = None,
) -> dict:
    registry = load_registry()
    repos = registry.setdefault("repos", [])
    filtered = [repo for repo in repos if repo.get("name") != name and repo.get("path") != str(path)]
    repo_info = {
        "name": name,
        "path": str(path),
        "upstream": upstream,
        "track": track,
        "mission": mission,
        "title_contains": title_contains,
    }
    if extra_fields:
        repo_info.update(extra_fields)
    filtered.append(repo_info)
    registry["repos"] = sorted(filtered, key=lambda item: item["name"])
    save_registry(registry)
    return repo_info
