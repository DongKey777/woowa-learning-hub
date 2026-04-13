from __future__ import annotations

import json
from datetime import datetime, timezone

from .paths import repo_profile_dir

REVIEWER_LENS_RULES = [
    {"lens": "responsibility_boundary", "keywords": ["Repository", "DAO", "Service", "boundary", "책임"]},
    {"lens": "consistency_transaction", "keywords": ["transaction", "rollback", "commit", "정합성", "원자성"]},
    {"lens": "testing_quality", "keywords": ["test", "테스트", "시나리오", "케이스"]},
    {"lens": "naming_convention", "keywords": ["getter", "네이밍", "컨벤션", "이름", "변수"]},
    {"lens": "readability", "keywords": ["읽기", "가독성", "한 눈", "readability"]},
]


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _score_lenses(packet: dict) -> list[str]:
    text_parts = []
    for comment in packet.get("representative_comments", []):
        body = comment.get("body")
        if body:
            text_parts.append(body.lower())
    for path_info in packet.get("hotspot_paths", []):
        path = path_info.get("path")
        if path:
            text_parts.append(path.lower())
    text = "\n".join(text_parts)

    scored = []
    for rule in REVIEWER_LENS_RULES:
        score = 0
        for keyword in rule["keywords"]:
            if keyword.lower() in text:
                score += 1
        if score > 0:
            scored.append((score, rule["lens"]))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [lens for _, lens in scored[:3]]


def profile_path(repo_name: str, reviewer: str):
    return repo_profile_dir(repo_name) / f"reviewer-{reviewer}.json"


def build_reviewer_profile(repo_name: str, reviewer_packet: dict) -> dict:
    reviewer = reviewer_packet["reviewer"]
    payload = {
        "repo": repo_name,
        "reviewer": reviewer,
        "generated_at": _timestamp(),
        "summary": reviewer_packet.get("summary"),
        "lenses": _score_lenses(reviewer_packet),
        "hotspot_paths": reviewer_packet.get("hotspot_paths", []),
    }
    path = profile_path(repo_name, reviewer)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payload["json_path"] = str(path)
    return payload
