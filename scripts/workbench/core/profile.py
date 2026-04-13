from __future__ import annotations

import json

from .paths import repo_profile_dir


def profile_path(repo_name: str):
    return repo_profile_dir(repo_name) / "learner.json"


def default_profile() -> dict:
    return {
        "experience_level": "intermediate",
        "preferred_depth": "medium",
        "focus": [],
        "recent_weaknesses": [],
    }


def load_profile(repo_name: str) -> dict:
    path = profile_path(repo_name)
    if not path.exists():
        return default_profile()
    return json.loads(path.read_text(encoding="utf-8"))


def save_profile(repo_name: str, profile: dict) -> dict:
    path = profile_path(repo_name)
    path.write_text(json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return profile
