from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .paths import repo_action_dir


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _open_artifact_action(artifact: str, json_path: str | None, markdown_path: str | None) -> dict:
    return {
        "kind": "open_artifact",
        "artifact": artifact,
        "json_path": json_path,
        "markdown_path": markdown_path,
    }


def _choose_reviewer_action(candidates: list[str], candidate_details: list[dict]) -> dict:
    return {
        "kind": "choose_reviewer",
        "candidates": candidates,
        "candidate_details": candidate_details,
    }


def _inspect_paths_action(paths: list[str], source: str) -> dict:
    return {
        "kind": "inspect_paths",
        "source": source,
        "paths": paths,
    }


def _review_topics_action(suggested_topics: list[str], topic_candidates: list[dict]) -> dict:
    return {
        "kind": "review_topics",
        "topics": suggested_topics,
        "topic_candidates": topic_candidates,
    }


def _open_focus_action(json_path: str | None, candidates: list[dict]) -> dict:
    return {
        "kind": "open_artifact",
        "artifact": "focus_ranking",
        "json_path": json_path,
        "markdown_path": None,
        "candidate_preview": candidates[:3],
    }


def _open_candidate_interpretation_action(json_path: str | None, recommendations: list[dict]) -> dict:
    return {
        "kind": "open_artifact",
        "artifact": "candidate_interpretation",
        "json_path": json_path,
        "markdown_path": None,
        "recommendation_preview": recommendations[:3],
    }


def _bootstrap_collection_action(repo: str) -> dict:
    return {
        "kind": "run_workbench",
        "command": "bootstrap-repo",
        "args": {
            "repo": repo,
        },
    }


def _bootstrap_action(repo: str) -> dict:
    return {
        "kind": "run_workbench",
        "command": "coach",
        "args": {
            "repo": repo,
            "prompt": "이 PR 기준으로 다음 액션 뭐야?",
        },
        "fallback_commands": [
            {
                "command": "my-pr",
                "args": {
                    "repo": repo,
                },
            }
        ],
    }


def build_next_actions(context: dict) -> dict:
    actions: list[dict] = []
    git_context = context.get("git_context", {})
    diff_files = git_context.get("diff_files", [])
    current_pr = context.get("current_pr")
    topic_query = context.get("topic_query")
    suggested_topics = context.get("suggested_topics") or []
    reviewer = context.get("reviewer")
    reviewer_candidates = context.get("reviewer_candidates") or []
    reviewer_candidate_details = context.get("reviewer_candidate_details") or []
    reviewer_profile = context.get("reviewer_profile")
    primary_intent = context.get("primary_intent")
    topic_candidates = context.get("topic_candidates") or []
    focus_ranking = context.get("focus_ranking") or {}
    candidate_interpretation = context.get("candidate_interpretation") or {}
    archive_status = context.get("archive_status") or {}
    learner_profile = context.get("learner_profile", {})
    experience_level = learner_profile.get("experience_level", "intermediate")
    mission_map_path = context.get("mission_map_path")
    mission_map_summary = context.get("mission_map_summary") or []

    if archive_status.get("bootstrap_state") in {"uninitialized", "bootstrapping"}:
        total_prs = (archive_status.get("signals") or {}).get("total_prs", 0)
        actions.append({
            "priority": 0,
            "category": "bootstrap",
            "title": "초기 자료 수집하기",
            "why": f"지금은 학습 자료가 충분하지 않습니다. 현재 수집된 PR은 {total_prs}개뿐이라 다른 크루 사례와 리뷰 근거가 제한적입니다.",
            "action": _bootstrap_collection_action(context["repo"]),
        })

    if mission_map_path:
        why = "로컬 미션 repo 자체의 구조와 likely review topic을 먼저 읽으면 이후 PR 추천을 더 정확하게 해석할 수 있습니다."
        if mission_map_summary:
            why = f"{mission_map_summary[0]}. {why}"
        actions.append({
            "priority": 1,
            "category": "analysis",
            "title": "Read mission map",
            "why": why,
            "action": _open_artifact_action(
                "mission_map",
                mission_map_path,
                None,
            ),
        })

    if current_pr:
        actions.append({
            "priority": 1,
            "category": "review",
            "title": "Open current PR report",
            "why": "Start from the PR-specific report before comparing with other crews.",
            "action": _open_artifact_action(
                "pr_report",
                context.get("pr_report_json_path"),
                context.get("pr_report_path"),
            ),
        })

    if reviewer and context.get("reviewer_packet_generated"):
        actions.append({
            "priority": 2,
            "category": "reviewer",
            "title": "Read reviewer packet",
            "why": "Use the reviewer packet to understand this reviewer's repeated criteria.",
            "action": _open_artifact_action(
                "reviewer_packet",
                context.get("reviewer_packet_json_path"),
                context.get("reviewer_packet_path"),
            ),
        })
        if reviewer_profile:
            actions.append({
                "priority": 3,
                "category": "reviewer",
                "title": "Check reviewer lens profile",
                "why": "Use the inferred reviewer lenses to interpret the comments consistently.",
                "action": _open_artifact_action(
                    "reviewer_profile",
                    reviewer_profile.get("json_path"),
                    None,
                ),
            })
    elif reviewer_candidates:
        actions.append({
            "priority": 2,
            "category": "reviewer",
            "title": "Choose a reviewer lens",
            "why": "No reviewer was fixed, so pick one of the likely reviewers before deeper interpretation.",
            "action": _choose_reviewer_action(reviewer_candidates, reviewer_candidate_details),
        })

    if context.get("topic_packet_generated"):
        actions.append({
            "priority": 4,
            "category": "topic",
            "title": f"Read topic packet for {topic_query}",
            "why": "Topic packet gives cross-PR evidence for the main design keyword.",
            "action": _open_artifact_action(
                "topic_packet",
                context.get("topic_packet_json_path"),
                context.get("topic_packet_path"),
            ),
        })

    if focus_ranking.get("candidates"):
        actions.append({
            "priority": 4 if primary_intent in {"peer_comparison", "concept_explanation"} else 4,
            "category": "peer",
            "title": "Inspect closest peer PRs",
            "why": "This ranking uses current prompt and local path signature to find the closest peer PRs in the same mission stage.",
            "action": _open_focus_action(
                context.get("focus_ranking_path"),
                focus_ranking.get("candidates", []),
            ),
        })

    if candidate_interpretation.get("learning_point_recommendations"):
        actions.append({
            "priority": 3 if primary_intent in {"peer_comparison", "concept_explanation", "implementation_planning"} else 4,
            "category": "learning",
            "title": "Read learning-point recommendations",
            "why": "This packet reorganizes candidate PRs by what they are good for learning, not only by raw similarity score.",
            "action": _open_candidate_interpretation_action(
                context.get("candidate_interpretation_path"),
                candidate_interpretation.get("learning_point_recommendations", []),
            ),
        })

    if primary_intent == "testing_strategy":
        actions.append({
            "priority": 4,
            "category": "testing",
            "title": "Inspect changed tests and missing scenarios",
            "why": "The current learning intent is testing-focused, so test gaps should be checked early.",
            "action": _inspect_paths_action(diff_files, "git_diff") if diff_files else _open_artifact_action(
                "pr_report",
                context.get("pr_report_json_path"),
                context.get("pr_report_path"),
            ),
        })

    if diff_files:
        actions.append({
            "priority": 4 if primary_intent != "testing_strategy" else 5,
            "category": "diff",
            "title": "Compare packet evidence with local diff files",
            "why": "The current repo has modified files that should be mapped back to the review evidence.",
            "action": _inspect_paths_action(diff_files, "git_diff"),
        })

    if suggested_topics:
        actions.append({
            "priority": 5,
            "category": "topic",
            "title": "Check alternative topics if needed",
            "why": "Suggested topics help widen analysis if the primary packet is not enough.",
            "action": _review_topics_action(suggested_topics, topic_candidates),
        })

    if not actions:
        actions.append({
            "priority": 1,
            "category": "bootstrap",
            "title": "Generate coach context first",
            "why": "No session context was available to infer next actions.",
            "action": _bootstrap_action(context["repo"]),
        })

    actions.sort(key=lambda item: (item["priority"], item["title"]))

    if experience_level == "beginner":
        actions = actions[:3]

    return {
        "repo": context["repo"],
        "context": context.get("context_type", "coach"),
        "generated_at": _timestamp(),
        "experience_level": experience_level,
        "next_actions": actions,
    }


def write_next_actions(repo_name: str, context_name: str, payload: dict) -> Path:
    action_dir = repo_action_dir(repo_name)
    path = action_dir / f"{context_name}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path
