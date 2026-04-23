"""Top-level response composition extracted from response.py."""

from __future__ import annotations

from .response_memory import (
    _infer_question_focus,
    _memory_policy,
    _packet_payloads,
    _timestamp,
)
from .response_evidence import _response_evidence, _unique_lines
from .response_teaching import _build_teaching_sections
from .response_templates import _base_summary, _intent_template


def _compose_answer(question_focus: str, sections: list[dict], fallback: list[str]) -> list[str]:
    priorities = {
        "lesson": ["lesson", "example", "application"],
        "example": ["lesson", "example", "reviewer"],
        "reviewer": ["lesson", "reviewer", "application"],
        "application": ["lesson", "application", "example"],
        "response": ["lesson", "reviewer", "reply"],
    }
    section_items = {
        section.get("kind"): section.get("items", [])
        for section in sections
        if section.get("kind")
    }

    items = []
    for key in priorities.get(question_focus, ["lesson", "example", "application"]):
        for item in section_items.get(key, []):
            items.append(item)
            break

    items.extend(fallback)
    return _unique_lines(items, limit=3)


def _action_preview(action: dict) -> str:
    kind = action.get("kind")
    if kind == "open_artifact":
        return f"open {action.get('artifact')}"
    if kind == "choose_reviewer":
        return "choose reviewer lens"
    if kind == "inspect_paths":
        return f"inspect paths from {action.get('source')}"
    if kind == "review_topics":
        return "review alternative topics"
    if kind == "run_workbench":
        return f"run workbench:{action.get('command')}"
    return kind or "action"


def _level_adjustments(level: str, actions: list[dict]) -> tuple[list[dict], list[str]]:
    if level == "beginner":
        return actions[:3], [
            "용어를 최소화하고 파일/리뷰 위치를 먼저 보여준다.",
            "다음 액션은 최대 3개까지만 제안한다.",
        ]
    if level == "advanced":
        return actions[:5], [
            "trade-off와 보류 기준까지 같이 제시한다.",
            "다음 액션은 최대 5개까지 제안한다.",
        ]
    return actions[:4], [
        "비교와 우선순위를 같이 제시한다.",
        "다음 액션은 최대 4개까지 제안한다.",
    ]


def build_response(context: dict, next_actions: dict) -> dict:
    intent = context.get("primary_intent")
    profile = context.get("learner_profile", {})
    level = profile.get("experience_level", "intermediate")
    packets = _packet_payloads(context)
    memory_policy = _memory_policy(context, packets)
    local_context = dict(context)
    local_context["memory_policy"] = memory_policy
    action_items = next_actions.get("next_actions", [])
    action_items, level_notes = _level_adjustments(level, action_items)
    summary = _base_summary(local_context, packets)
    template_answer, _, postpone, follow_up = _intent_template(intent, local_context, packets, next_actions)
    teaching_points, sections = _build_teaching_sections(local_context, packets)
    evidence = _response_evidence(local_context, packets)
    question_focus = _infer_question_focus(local_context)
    answer = _compose_answer(question_focus["focus"], sections, template_answer)

    return {
        "response_type": "coach_response",
        "response_role": "reference",
        "repo": context["repo"],
        "generated_at": _timestamp(),
        "intent": intent,
        "question_focus": question_focus["focus"],
        "memory_policy": memory_policy,
        "experience_level": level,
        "level_notes": level_notes,
        "usage_guidance": [
            "Use this artifact as a reference frame, not as a final answer to copy verbatim.",
            "Re-synthesize the learner-facing answer from the current question, current repo state, grounded evidence, and memory confidence.",
        ],
        "summary": summary,
        "answer": answer,
        "teaching_points": teaching_points,
        "sections": sections,
        "evidence": evidence,
        "next_actions": action_items,
        "postpone": postpone,
        "follow_up_question": follow_up,
    }


def render_response_markdown(response: dict) -> str:
    lines = [f"# Coach Response: {response['repo']}", ""]
    lines.append("## Intent")
    lines.append(f"- {response['intent']}")
    lines.append(f"- response_role: {response['response_role']}")
    lines.append(f"- question_focus: {response['question_focus']}")
    lines.append(f"- memory_policy: {response['memory_policy']['mode']}")
    lines.append(f"- level: {response['experience_level']}")
    for note in response.get("level_notes", []):
        lines.append(f"- note: {note}")
    for note in response.get("usage_guidance", []):
        lines.append(f"- usage: {note}")
    lines.append("")
    lines.append("## Summary")
    for item in response["summary"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Teaching Points")
    for item in response.get("teaching_points", []):
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Answer")
    for item in response.get("answer", []):
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Sections")
    for section in response.get("sections", []):
        lines.append(f"### {section['title']}")
        for item in section.get("items", []):
            lines.append(f"- {item}")
        lines.append("")
    lines.append("## Evidence")
    for item in response["evidence"]:
        lines.append(f"- {item['type']}")
        if item.get("json_path"):
            lines.append(f"  json: `{item['json_path']}`")
        if item.get("markdown_path"):
            lines.append(f"  markdown: `{item['markdown_path']}`")
        for summary in item.get("summary", []):
            lines.append(f"  summary: {summary}")
        for highlight in item.get("highlights", []):
            lines.append(f"  highlight: {highlight}")
    lines.append("")
    lines.append("## Next Actions")
    for item in response["next_actions"]:
        lines.append(f"- [{item['priority']}] {item['title']}")
        lines.append(f"  why: {item['why']}")
        lines.append(f"  action: {_action_preview(item['action'])}")
    lines.append("")
    lines.append("## Postpone")
    for item in response["postpone"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Follow-up")
    lines.append(f"- {response['follow_up_question']}")
    return "\n".join(lines).strip() + "\n"
