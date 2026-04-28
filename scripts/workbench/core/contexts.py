from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from pathlib import PurePosixPath

from .actions import build_next_actions
from .candidate_interpretation import build_candidate_interpretation
from .git_context import read_current_pr, read_git_context
from .intent import infer_intent, infer_topics
from .mission_map import write_mission_map
from .packets import (
    generate_pr_report,
    generate_reviewer_packet,
    generate_topic_packet,
)
from .paths import repo_context_dir, repo_state_dir
from .profile import load_profile
from .reviewer_profile import build_reviewer_profile
from .schema_validation import validate_payload
from .session_focus import build_session_focus


def _write_context(repo_name: str, name: str, payload: dict) -> Path:
    context_dir = repo_context_dir(repo_name)
    path = context_dir / f"{name}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def _workbench_action(command: str, args: dict, why: str) -> dict:
    return {
        "kind": "run_workbench",
        "command": command,
        "args": args,
        "why": why,
    }


def _top_peer_pr_number(focus_payload: dict | None) -> int | str:
    if not focus_payload:
        return "<crew-pr>"
    candidates = focus_payload.get("candidates", [])
    if not candidates:
        return "<crew-pr>"
    return candidates[0].get("pr_number") or "<crew-pr>"


def _connect(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def _add_candidate(candidate_map: dict[str, dict], reviewer: str | None, score: int, reason: str) -> None:
    if not reviewer:
        return
    current = candidate_map.setdefault(reviewer, {"reviewer": reviewer, "score": 0, "reasons": []})
    current["score"] += score
    if reason not in current["reasons"]:
        current["reasons"].append(reason)


def _add_candidate_reasons(candidate_map: dict[str, dict], reviewer: str | None, score: int, reasons: list[str]) -> None:
    if not reviewer:
        return
    current = candidate_map.setdefault(reviewer, {"reviewer": reviewer, "score": 0, "reasons": []})
    current["score"] += score
    for reason in reasons:
        if reason not in current["reasons"]:
            current["reasons"].append(reason)


def _diff_reviewer_candidates(db_path: Path, diff_files: list[str]) -> list[dict]:
    if not diff_files:
        return []

    candidate_map: dict[str, dict] = {}
    with _connect(db_path) as connection:
        for diff_file in diff_files:
            exact_rows = connection.execute(
                """
                SELECT user_login, COUNT(*) AS comment_count
                FROM pull_request_review_comments_current
                WHERE path = ?
                GROUP BY user_login
                ORDER BY comment_count DESC, user_login
                LIMIT 10
                """,
                (diff_file,),
            ).fetchall()
            for row in exact_rows:
                _add_candidate(candidate_map, row["user_login"], 8 + int(row["comment_count"]) * 3, f"exact-path:{diff_file}")

            parent = str(PurePosixPath(diff_file).parent)
            if parent and parent != ".":
                directory_rows = connection.execute(
                    """
                    SELECT user_login, COUNT(*) AS comment_count
                    FROM pull_request_review_comments_current
                    WHERE path LIKE ?
                    GROUP BY user_login
                    ORDER BY comment_count DESC, user_login
                    LIMIT 10
                    """,
                    (f"{parent}/%",),
                ).fetchall()
                for row in directory_rows:
                    _add_candidate(candidate_map, row["user_login"], 3 + int(row["comment_count"]), f"same-dir:{parent}")

    ranked = sorted(candidate_map.values(), key=lambda item: (-item["score"], item["reviewer"]))
    return ranked[:5]


def _suggest_reviewer_candidates(
    db_path: Path,
    diff_files: list[str],
    pr_report_payload: dict | None,
    topic_packet_payload: dict | None,
) -> tuple[list[str], list[dict]]:
    candidate_map: dict[str, dict] = {}

    if pr_report_payload:
        review_counts: dict[str, int] = {}
        for review in pr_report_payload.get("reviews", []):
            reviewer = review.get("reviewer_login")
            if not reviewer:
                continue
            review_counts[reviewer] = review_counts.get(reviewer, 0) + 1
        for reviewer, count in review_counts.items():
            _add_candidate(candidate_map, reviewer, 8 + count, f"current-pr-review:{count}")
    if topic_packet_payload:
        for reviewer in topic_packet_payload.get("top_reviewers", []):
            login = reviewer.get("user_login")
            hit_count = int(reviewer.get("hit_count", 0))
            _add_candidate(candidate_map, login, 2 + hit_count, f"topic-hit:{topic_packet_payload.get('topic')}")
    for candidate in _diff_reviewer_candidates(db_path, diff_files):
        _add_candidate_reasons(
            candidate_map,
            candidate.get("reviewer"),
            int(candidate.get("score", 0)),
            list(candidate.get("reasons", [])),
        )

    ranked = sorted(candidate_map.values(), key=lambda item: (-item["score"], item["reviewer"]))
    return [item["reviewer"] for item in ranked[:3]], ranked[:5]


def build_my_pr_context(
    repo: dict,
    db_path: Path,
    pr_number: int | None = None,
    *,
    learning_profile: dict | None = None,
) -> dict:
    repo_name = repo["name"]
    repo_path = Path(repo["path"])
    git_context = read_git_context(repo_path)
    mission_map = write_mission_map(repo)
    topic_info = infer_topics("", git_context["diff_files"], mission_map)
    intent_info = infer_intent("내 pr 기준 다음 액션", None)
    current_pr = {"number": pr_number} if pr_number else read_current_pr(repo_path)
    if not current_pr or current_pr.get("number") is None:
        raise SystemExit("current PR could not be resolved; pass --pr explicitly")

    report_info = generate_pr_report(repo_name, db_path, int(current_pr["number"]))
    focus_info = build_session_focus(
        repo_name=repo_name,
        db_path=db_path,
        mode="my-pr",
        prompt="내 pr 기준 다음 액션",
        current_pr_number=int(current_pr["number"]),
        git_diff_files=git_context["diff_files"],
        title_hint=repo.get("title_contains"),
        branch_hint=repo.get("branch_hint"),
        current_pr_title=repo.get("current_pr_title"),
        topic_terms=topic_info["suggested_topics"],
        retrieval_path_hints=mission_map.get("retrieval_path_hints"),
    )
    interpretation_info = build_candidate_interpretation(
        repo_name,
        "my-pr",
        focus_info,
        db_path=str(db_path),
        learning_profile=learning_profile,
    )
    payload = {
        "context_type": "my-pr",
        "repo": repo_name,
        "repo_path": str(repo_path),
        "repo_state_dir": str(repo_state_dir(repo_name)),
        "learner_profile": load_profile(repo_name),
        "mission_map_path": mission_map.get("json_path"),
        "mission_map_summary": mission_map.get("summary", []),
        "mission_map": mission_map,
        "upstream": repo.get("upstream"),
        "db_path": str(db_path),
        "current_pr": current_pr,
        "git_context": git_context,
        "primary_topic": topic_info["primary_topic"],
        "suggested_topics": topic_info["suggested_topics"],
        "topic_inference_reasons": topic_info["inference_reasons"],
        "topic_candidates": topic_info["topic_candidates"],
        "topic_confidence": topic_info.get("confidence", "low"),
        "primary_intent": intent_info["primary_intent"],
        "suggested_intents": intent_info["suggested_intents"],
        "intent_reasons": intent_info["intent_reasons"],
        "intent_candidates": intent_info["intent_candidates"],
        "pr_report_generated": report_info["generated"],
        "pr_report_path": report_info.get("markdown_path"),
        "pr_report_json_path": report_info.get("json_path"),
        "pr_report_evidence": report_info.get("evidence"),
        "pr_report_preview": report_info.get("markdown_preview", []),
        "pr_report_error": report_info.get("error"),
        "focus_ranking_path": focus_info.get("json_path"),
        "focus_ranking": focus_info,
        "candidate_interpretation_path": interpretation_info.get("json_path"),
        "candidate_interpretation": interpretation_info,
        "recommended_next_actions": [
            _workbench_action(
                "mission-map",
                {
                    "repo": repo_name,
                },
                "현재 미션 자체의 구조와 retrieval hint를 먼저 읽는다.",
            ),
            _workbench_action(
                "topic",
                {
                    "repo": repo_name,
                    "topic": topic_info["primary_topic"],
                    "query": topic_info["primary_query"],
                },
                "현재 diff와 가장 가까운 주제로 cross-PR evidence를 확장한다.",
            ),
            _workbench_action(
                "reviewer",
                {
                    "repo": repo_name,
                    "reviewer": "<reviewer-login>",
                },
                "실제 리뷰어 기준을 별도 packet으로 읽는다.",
            ),
            _workbench_action(
                "compare",
                {
                    "repo": repo_name,
                    "prs": [current_pr["number"], _top_peer_pr_number(focus_info)],
                },
                "내 PR과 다른 크루 PR을 직접 비교한다.",
            ),
            _workbench_action(
                "coach",
                {
                    "repo": repo_name,
                    "pr": current_pr["number"],
                    "prompt": "이 PR 기준으로 다음 액션 뭐야?",
                },
                "질문 기반 코치 컨텍스트를 다시 생성한다.",
            ),
        ],
        "agent_notes": [
            "Read the PR report evidence object first, then open the full packet if needed.",
            "Use git_context.diff_files to connect review comments back to the local repo state.",
            "Prefer explaining unresolved review intent before changing code.",
        ],
    }
    reviewer_candidates, reviewer_candidate_details = _suggest_reviewer_candidates(
        db_path,
        git_context["diff_files"],
        report_info,
        None,
    )
    payload["reviewer_candidates"] = reviewer_candidates
    payload["reviewer_candidate_details"] = reviewer_candidate_details
    validate_payload("my-pr-context", payload)
    path = _write_context(repo_name, "my-pr-context", payload)
    payload["json_path"] = str(path)
    return payload


def build_coach_context(
    repo: dict,
    db_path: Path,
    prompt: str,
    pr_number: int | None = None,
    reviewer: str | None = None,
    *,
    learning_profile: dict | None = None,
) -> dict:
    repo_name = repo["name"]
    repo_path = Path(repo["path"])
    git_context = read_git_context(repo_path)
    mission_map = write_mission_map(repo)
    inferred_topics = infer_topics(prompt, git_context["diff_files"], mission_map)
    intent_info = infer_intent(prompt, reviewer)
    current_pr = {"number": pr_number} if pr_number else read_current_pr(repo_path)

    topic_info = generate_topic_packet(repo_name, db_path, inferred_topics["primary_topic"], inferred_topics["primary_query"])
    reviewer_info = generate_reviewer_packet(repo_name, db_path, reviewer) if reviewer else None
    reviewer_profile = build_reviewer_profile(repo_name, reviewer_info) if reviewer_info and reviewer_info.get("generated") else None
    pr_info = generate_pr_report(repo_name, db_path, int(current_pr["number"])) if current_pr and current_pr.get("number") is not None else None
    focus_info = build_session_focus(
        repo_name=repo_name,
        db_path=db_path,
        mode="coach",
        prompt=prompt,
        current_pr_number=int(current_pr["number"]) if current_pr and current_pr.get("number") is not None else None,
        git_diff_files=git_context["diff_files"],
        title_hint=repo.get("title_contains"),
        branch_hint=repo.get("branch_hint"),
        current_pr_title=repo.get("current_pr_title"),
        topic_terms=inferred_topics["suggested_topics"],
        retrieval_path_hints=mission_map.get("retrieval_path_hints"),
    )
    interpretation_info = build_candidate_interpretation(
        repo_name,
        "coach",
        focus_info,
        db_path=str(db_path),
        learning_profile=learning_profile,
    )
    reviewer_candidates, reviewer_candidate_details = _suggest_reviewer_candidates(
        db_path,
        git_context["diff_files"],
        pr_info,
        topic_info,
    )

    payload = {
        "context_type": "coach",
        "repo": repo_name,
        "repo_path": str(repo_path),
        "repo_state_dir": str(repo_state_dir(repo_name)),
        "learner_profile": load_profile(repo_name),
        "mission_map_path": mission_map.get("json_path"),
        "mission_map_summary": mission_map.get("summary", []),
        "mission_map": mission_map,
        "upstream": repo.get("upstream"),
        "db_path": str(db_path),
        "prompt": prompt,
        "current_pr": current_pr,
        "reviewer": reviewer,
        "git_context": git_context,
        "suggested_topics": inferred_topics["suggested_topics"],
        "topic_inference_reasons": inferred_topics["inference_reasons"],
        "topic_candidates": inferred_topics["topic_candidates"],
        "topic_confidence": inferred_topics.get("confidence", "low"),
        "primary_intent": intent_info["primary_intent"],
        "suggested_intents": intent_info["suggested_intents"],
        "intent_reasons": intent_info["intent_reasons"],
        "intent_candidates": intent_info["intent_candidates"],
        "reviewer_candidates": reviewer_candidates,
        "reviewer_candidate_details": reviewer_candidate_details,
        "primary_topic": inferred_topics["primary_topic"],
        "topic_query": inferred_topics["primary_query"],
        "topic_packet_generated": topic_info["generated"],
        "topic_packet_path": topic_info.get("markdown_path"),
        "topic_packet_json_path": topic_info.get("json_path"),
        "topic_packet_evidence": topic_info.get("evidence"),
        "topic_packet_preview": topic_info.get("markdown_preview", []),
        "topic_packet_error": topic_info.get("error"),
        "reviewer_packet_generated": reviewer_info["generated"] if reviewer_info else False,
        "reviewer_packet_path": reviewer_info.get("markdown_path") if reviewer_info else None,
        "reviewer_packet_json_path": reviewer_info.get("json_path") if reviewer_info else None,
        "reviewer_packet_evidence": reviewer_info.get("evidence") if reviewer_info else None,
        "reviewer_packet_preview": reviewer_info.get("markdown_preview", []) if reviewer_info else [],
        "reviewer_packet_error": reviewer_info.get("error") if reviewer_info else None,
        "reviewer_profile": reviewer_profile,
        "pr_report_generated": pr_info["generated"] if pr_info else False,
        "pr_report_path": pr_info.get("markdown_path") if pr_info else None,
        "pr_report_json_path": pr_info.get("json_path") if pr_info else None,
        "pr_report_evidence": pr_info.get("evidence") if pr_info else None,
        "pr_report_preview": pr_info.get("markdown_preview", []) if pr_info else [],
        "pr_report_error": pr_info.get("error") if pr_info else None,
        "focus_ranking_path": focus_info.get("json_path"),
        "focus_ranking": focus_info,
        "candidate_interpretation_path": interpretation_info.get("json_path"),
        "candidate_interpretation": interpretation_info,
        "recommended_next_actions": [
            _workbench_action(
                "mission-map",
                {
                    "repo": repo_name,
                },
                "현재 미션 구조와 likely review topic을 먼저 읽는다.",
            ),
            _workbench_action(
                "topic",
                {
                    "repo": repo_name,
                    "topic": inferred_topics["primary_topic"],
                    "query": inferred_topics["primary_query"],
                },
                "현재 질문과 diff 기준으로 topic evidence를 확장한다.",
            ),
            _workbench_action(
                "reviewer",
                {
                    "repo": repo_name,
                    "reviewer": "<reviewer-login>",
                },
                "리뷰어 기준을 별도 packet으로 읽는다.",
            ),
            _workbench_action(
                "compare",
                {
                    "repo": repo_name,
                    "prs": [current_pr["number"] if current_pr and current_pr.get("number") is not None else "<my-pr>", _top_peer_pr_number(focus_info)],
                },
                "다른 크루 PR과 직접 비교 packet을 만든다.",
            ),
            _workbench_action(
                "next-action",
                {
                    "repo": repo_name,
                    "context": "coach",
                },
                "현재 context 기준 우선순위 액션을 다시 계산한다.",
            ),
        ],
        "agent_notes": [
            "Start with the packet evidence objects and open the full packet files only if more detail is needed.",
            "If reviewer is provided, read the reviewer packet before interpreting feedback patterns.",
            "If current_pr is present, read the PR report before proposing review responses.",
            "Check git_context.diff_files before proposing code changes.",
            "Connect packet evidence back to the current mission repo code.",
            "Separate code changes from explanation-only review responses.",
        ],
    }
    validate_payload("coach-context", payload)
    path = _write_context(repo_name, "coach-context", payload)
    payload["json_path"] = str(path)
    return payload


def write_next_actions_from_context(context: dict) -> dict:
    payload = build_next_actions(context)
    validate_payload("next-actions", payload)
    path = repo_context_dir(context["repo"]).parent / "actions" / f"{context['context_type']}.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payload["json_path"] = str(path)
    return payload
