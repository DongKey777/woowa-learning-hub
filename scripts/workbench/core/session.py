from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .contexts import build_coach_context, build_my_pr_context, write_next_actions_from_context
from .memory import load_learning_memory
from .paths import repo_action_dir, repo_archive_db
from .response import build_response, render_response_markdown
from .schema_validation import validate_payload


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _action_name(mode: str) -> str:
    return "coach" if mode == "coach" else "my-pr"


def _context_name(mode: str) -> str:
    return "coach-context" if mode == "coach" else "my-pr-context"


def write_response_artifacts(repo_name: str, mode: str, response: dict) -> tuple[Path, Path]:
    action_dir = repo_action_dir(repo_name)
    action_name = _action_name(mode)
    json_path = action_dir / f"{action_name}-response.json"
    md_path = action_dir / f"{action_name}-response.md"
    json_path.write_text(json.dumps(response, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_response_markdown(response), encoding="utf-8")
    return json_path, md_path


def start_session(
    repo: dict,
    mode: str,
    prompt: str | None = None,
    pr_number: int | None = None,
    reviewer: str | None = None,
    memory_context: dict | None = None,
    archive_status: dict | None = None,
) -> dict:
    repo_name = repo["name"]
    db_path = repo_archive_db(repo_name)
    resolved_memory = memory_context or load_learning_memory(repo_name)

    if mode == "coach":
        resolved_prompt = prompt or "이 PR 기준으로 지금 뭘 먼저 봐야 해?"
        context = build_coach_context(repo, db_path, resolved_prompt, pr_number, reviewer)
    else:
        context = build_my_pr_context(repo, db_path, pr_number)

    context["learning_memory_summary"] = resolved_memory.get("summary", {})
    context["learning_memory_profile"] = resolved_memory.get("profile", {})
    context["learning_memory_summary_path"] = resolved_memory.get("summary_path")
    context["learning_memory_profile_path"] = resolved_memory.get("profile_path")
    context["archive_status"] = archive_status
    next_actions = write_next_actions_from_context(context)
    response = build_response(context, next_actions)
    validate_payload("coach-response", response)
    response_json_path, response_markdown_path = write_response_artifacts(repo_name, mode, response)

    session_payload = {
        "session_type": "session_start",
        "repo": repo_name,
        "mode": mode,
        "generated_at": _timestamp(),
        "prompt": context.get("prompt"),
        "context_path": context.get("json_path"),
        "action_path": next_actions.get("json_path"),
        "response_json_path": str(response_json_path),
        "response_markdown_path": str(response_markdown_path),
        "mission_map_path": context.get("mission_map_path"),
        "mission_map_summary": context.get("mission_map_summary", []),
        "context_type": context.get("context_type"),
        "primary_intent": context.get("primary_intent"),
        "primary_topic": context.get("primary_topic") or context.get("topic_query") or (context.get("suggested_topics") or [None])[0],
        "reviewer": context.get("reviewer"),
        "current_pr": context.get("current_pr"),
        "focus_ranking_path": context.get("focus_ranking_path"),
        "focus_candidates": (context.get("focus_ranking") or {}).get("candidates", [])[:5],
        "focus_local_path_signature": (context.get("focus_ranking") or {}).get("local_path_signature"),
        "candidate_interpretation_path": context.get("candidate_interpretation_path"),
        "learning_point_recommendations": (context.get("candidate_interpretation") or {}).get("learning_point_recommendations", [])[:5],
        "learning_memory_summary": resolved_memory.get("summary", {}),
        "learning_memory_profile": resolved_memory.get("profile", {}),
        "recommended_next_actions": context.get("recommended_next_actions", []),
        "response": response,
    }
    validate_payload("session-result", session_payload)

    action_dir = repo_action_dir(repo_name)
    session_path = action_dir / f"{_action_name(mode)}-session.json"
    session_path.write_text(json.dumps(session_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    session_payload["json_path"] = str(session_path)
    return session_payload
