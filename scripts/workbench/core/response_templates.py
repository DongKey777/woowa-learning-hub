"""Per-intent template renderers extracted from response.py."""

from __future__ import annotations

from .response_memory import _learning_memory_profile
from .response_evidence import (
    _candidate_profile_lines,
    _comment_lines,
    _focus_excerpt_lines,
    _focus_pr_lines,
    _interpretation_lines,
    _mentor_comment_samples,
    _mentor_review_samples,
    _path_lines,
    _pr_lines,
    _review_lines,
)
from .response_teaching import (
    _deepen_and_broaden_lines,
    _display_topic,
    _topic_boundary,
)


def _base_summary(context: dict, packets: dict) -> list[str]:
    summary = []
    pr_packet = packets.get("pr_report", {})
    pr_evidence = pr_packet.get("evidence", {})
    topic = _display_topic(context)
    reviewer = context.get("reviewer")
    mission_map_summary = context.get("mission_map_summary") or []

    pr_number = (context.get("current_pr") or {}).get("number")
    if mission_map_summary:
        summary.append(f"미션 구조 요약은 {mission_map_summary[0]} 이다.")
    if pr_number:
        summary.append(f"현재 기준 PR은 #{pr_number} 이다.")
    if reviewer:
        summary.append(f"리뷰어 관점은 {reviewer} 이다.")
    if topic:
        summary.append(f"핵심 주제는 {topic} 이다.")

    review_summary = pr_evidence.get("review_summary", {})
    if review_summary:
        summary.append(
            "리뷰 데이터는 "
            f"review {review_summary.get('review_count', 0)}건, "
            f"inline comment {review_summary.get('review_comment_count', 0)}건 기준이다."
        )

    hotspot_paths = pr_evidence.get("hotspot_paths", [])
    if hotspot_paths:
        top_path = hotspot_paths[0]
        summary.append(f"현재 PR에서 가장 먼저 볼 경로는 {top_path['path']} 이다.")

    focus_payload = packets.get("focus_ranking", {})
    if focus_payload.get("candidates"):
        top_peer = focus_payload["candidates"][0]
        summary.append(f"현재 질문과 가장 가까운 peer PR은 #{top_peer['pr_number']} 이다.")

    profile = _learning_memory_profile(context)
    dominant_learning_points = profile.get("dominant_learning_points", [])
    if dominant_learning_points:
        top_point = dominant_learning_points[0]
        if top_point.get("confidence") in {"medium", "high"}:
            summary.append(f"누적 학습 성향상 가장 자주 다룬 포인트는 {top_point.get('label')} 이다.")

    if not summary:
        summary.append("현재 컨텍스트를 기준으로 다음 학습 액션을 정리한다.")
    return summary


def _generic_sections(context: dict, next_actions: dict) -> list[dict]:
    action_items = next_actions.get("next_actions", [])
    return [
        {
            "title": "지금 바로 할 일",
            "items": [
                f"[{item['priority']}] {item['title']}"
                for item in action_items[:3]
            ] or ["먼저 context와 packet을 다시 생성한다."],
        }
    ]


def _review_triage_template(context: dict, packets: dict, next_actions: dict) -> tuple[list[str], list[dict], list[str], str]:
    pr_evidence = packets.get("pr_report", {}).get("evidence", {})
    reviewer_profile = context.get("reviewer_profile") or {}
    review_summary = pr_evidence.get("review_summary", {})
    changes_requested = review_summary.get("changes_requested_count", 0)
    hotspot_items = _path_lines(pr_evidence.get("hotspot_paths", []), "comment_count")
    mentor_comments = pr_evidence.get("mentor_comment_samples") or pr_evidence.get("comment_samples", [])
    crew_responses = pr_evidence.get("crew_response_samples", [])
    comment_items = _comment_lines(mentor_comments)
    mentor_reviews = [
        r for r in pr_evidence.get("review_samples", [])
        if (r.get("reviewer_role") or "mentor") == "mentor"
    ] or pr_evidence.get("review_samples", [])
    review_items = _review_lines(mentor_reviews, limit=2)
    crew_response_items = _comment_lines(crew_responses, limit=2) if crew_responses else []
    lenses = reviewer_profile.get("lenses", [])

    answer = [
        "우선 현재 PR 자체에서 댓글이 몰린 경로와 변경 요청 상태를 먼저 정리해야 한다.",
        f"지금 데이터상 changes requested는 {changes_requested}건이다." if changes_requested else "현재 리뷰 상태는 설명형 코멘트와 경로별 지적을 같이 봐야 한다.",
        f"리뷰어는 {', '.join(lenses[:2])} 기준을 반복해서 보는 편이다." if lenses else "리뷰어 lens가 없으면 현재 PR의 hotspot path부터 본다.",
    ]
    sections = [
        {
            "title": "먼저 볼 것",
            "items": hotspot_items or ["hotspot path 데이터가 없으면 현재 diff 파일부터 본다."],
        },
        {
            "title": "멘토 지적 (코드 수정 우선 후보)",
            "items": comment_items or ["path/line이 잡힌 inline comment부터 우선 처리한다."],
        },
        {
            "title": "설명으로 먼저 정리할 후보",
            "items": review_items or ["전체 리뷰 body에서 의도/설계 질문 코멘트를 따로 분리한다."],
        },
    ]
    if crew_response_items:
        sections.append({
            "title": "참고: 학습자가 이전에 남긴 응답",
            "items": crew_response_items,
        })
    postpone = [
        "핵심 리뷰와 직접 연결되지 않은 큰 구조 변경은 뒤로 미룬다.",
        "hotspot 경로와 무관한 리팩터링은 지금 우선순위가 아니다.",
    ]
    return answer, sections, postpone, "이 중에서 지금 바로 코드로 반영할 코멘트는 무엇인가?"


def _concept_explanation_template(context: dict, packets: dict, next_actions: dict) -> tuple[list[str], list[dict], list[str], str]:
    topic = _display_topic(context)
    topic_evidence = packets.get("topic_packet", {}).get("evidence", {})
    pr_evidence = packets.get("pr_report", {}).get("evidence", {})
    focus_payload = packets.get("focus_ranking", {})
    interpretation_payload = packets.get("candidate_interpretation", {})
    profile = _learning_memory_profile(context)
    deepen_lines, broaden_lines = _deepen_and_broaden_lines(interpretation_payload, profile, limit=2)
    diff_files = (context.get("git_context") or {}).get("diff_files", [])

    answer = [
        f"지금 질문은 {topic}를 현재 코드 경계에 맞춰 설명하는 문제다." if topic else "지금 질문은 현재 변경의 책임 경계를 설명하는 문제다.",
        _topic_boundary(topic),
        "설명은 추상적인 정의보다 현재 PR의 파일 경로와 다른 PR 패턴에 연결해서 해야 한다.",
    ]
    sections = [
        {
            "title": "개념 경계",
            "items": [
                _topic_boundary(topic),
                f"현재 topic inference 근거: {', '.join(context.get('topic_inference_reasons', [])[:3]) or '없음'}",
            ],
        },
        {
            "title": "현재 코드에서 볼 위치",
            "items": diff_files[:3] or _path_lines(pr_evidence.get("hotspot_paths", []), "comment_count") or ["현재 diff가 없으면 PR hotspot path를 기준으로 본다."],
        },
        {
            "title": "비교 근거",
            "items": deepen_lines or broaden_lines or _interpretation_lines(interpretation_payload) or _focus_pr_lines(focus_payload) or _pr_lines(topic_evidence.get("ranked_prs", [])) or ["같은 topic packet의 related PR를 더 수집해서 본다."],
        },
    ]
    postpone = [
        "개념 설명 단계에서는 바로 구조를 뒤엎는 설계 변경으로 넘어가지 않는다.",
    ]
    return answer, sections, postpone, "이 개념이 현재 코드에서는 어느 객체 경계에서 드러나야 하는가?"


def _peer_comparison_template(context: dict, packets: dict, next_actions: dict) -> tuple[list[str], list[dict], list[str], str]:
    topic_evidence = packets.get("topic_packet", {}).get("evidence", {})
    focus_payload = packets.get("focus_ranking", {})
    interpretation_payload = packets.get("candidate_interpretation", {})
    reviewer_profile = context.get("reviewer_profile") or {}
    memory_profile = _learning_memory_profile(context)
    memory_policy = context.get("memory_policy") or {"mode": "neutral"}
    deepen_lines, broaden_lines = _deepen_and_broaden_lines(interpretation_payload, memory_profile, limit=3)

    answer = [
        "비교는 같은 주제에서 반복되는 설계 패턴과 현재 코드의 차이를 같이 봐야 한다.",
        "우열을 먼저 정하기보다 어떤 책임을 어느 객체에 두는지부터 비교하는 편이 맞다.",
        f"현재 비교 기준 topic은 {_display_topic(context)} 이다." if _display_topic(context) else "현재 비교 기준 topic을 먼저 고정해야 한다.",
    ]
    if memory_profile.get("confidence") == "low":
        answer.append("장기 memory 신호는 아직 약하므로, 이번 세션에서는 현재 질문과 근거를 더 우선한다.")
    if memory_policy.get("mode") == "broaden":
        primary_section = {
            "title": "이번에 넓힐 포인트",
            "items": broaden_lines or _interpretation_lines(interpretation_payload) or ["넓힐 포인트 추천이 아직 약하다."],
        }
        secondary_section = {
            "title": "반복 학습 심화 추천",
            "items": deepen_lines or ["반복 학습 포인트와 직접 연결된 추천이 충분하지 않다."],
        }
    else:
        primary_section = {
            "title": "반복 학습 심화 추천",
            "items": deepen_lines or ["아직 반복 학습 포인트와 직접 연결된 추천이 충분하지 않다."],
        }
        secondary_section = {
            "title": "이번에 넓힐 포인트",
            "items": broaden_lines or _interpretation_lines(interpretation_payload) or _focus_pr_lines(focus_payload) or _pr_lines(topic_evidence.get("ranked_prs", [])) or ["topic packet related PR가 더 필요하다."],
        }

    sections = [
        primary_section,
        secondary_section,
        {
            "title": "후보 PR 성격",
            "items": _candidate_profile_lines(interpretation_payload) or _focus_pr_lines(focus_payload) or ["후보 PR의 성격을 해석할 데이터가 더 필요하다."],
        },
        {
            "title": "질문과 가까운 근거",
            "items": _focus_excerpt_lines(focus_payload) or _path_lines(topic_evidence.get("ranked_paths", []), "hit_count") or ["반복 path가 없으면 직접 compare packet을 생성한다."],
        },
        {
            "title": "선택 기준",
            "items": [
                f"memory policy: {memory_policy.get('mode')} - {memory_policy.get('reason')}",
                f"리뷰어 lens: {', '.join(reviewer_profile.get('lenses', [])[:3])}"
                if reviewer_profile.get("lenses")
                else "지금 구조가 책임 분리를 더 명확하게 만드는지 본다.",
                "추가 계층이 늘어날 때 복잡도 증가를 감수할 가치가 있는지 본다.",
                "현재 미션 단계에서 필요한 확장성인지, 과한 추상화인지 같이 본다.",
            ],
        },
    ]
    postpone = [
        "비교만으로 바로 구조를 바꾸지 말고, 내 코드와 가장 가까운 패턴부터 좁힌다.",
    ]
    return answer, sections, postpone, "내 현재 코드와 가장 가까운 패턴 하나만 고르면 무엇인가?"


def _pr_response_template(context: dict, packets: dict, next_actions: dict) -> tuple[list[str], list[dict], list[str], str]:
    pr_evidence = packets.get("pr_report", {}).get("evidence", {})
    code_change_items = _comment_lines(_mentor_comment_samples(pr_evidence))
    explanation_items = _review_lines(_mentor_review_samples(pr_evidence), limit=3)

    answer = [
        "리뷰 답변은 코드 수정과 설명 답변을 한 덩어리로 쓰면 안 된다.",
        "path/line이 붙은 inline comment는 코드 반영 후보로, 전체 리뷰 body는 설명 답변 후보로 먼저 분리하는 편이 낫다.",
        "답변 문장은 수정 사실, 의도 유지 이유, 추가 확인 필요 항목을 분리해서 쓰면 된다.",
    ]
    sections = [
        {
            "title": "코드로 반영할 코멘트",
            "items": code_change_items or ["inline comment가 없으면 파일 단위 코멘트부터 다시 분류한다."],
        },
        {
            "title": "설명으로 답할 코멘트",
            "items": explanation_items or ["review body에서 설계 의도 질문을 먼저 추린다."],
        },
        {
            "title": "답변 문장 뼈대",
            "items": [
                "수정한 경우: 해당 부분은 지적하신 기준에 맞춰 수정했습니다.",
                "유지한 경우: 이 부분은 현재 단계에서는 책임 경계를 이렇게 두는 편이 낫다고 판단했습니다.",
                "추가 확인이 필요한 경우: 우선 이 방향으로 정리했고, 남은 trade-off는 다음 단계에서 더 보겠습니다.",
            ],
        },
    ]
    postpone = [
        "모든 코멘트를 코드 수정으로 과잉 대응하지 않는다.",
    ]
    return answer, sections, postpone, "각 코멘트를 코드 수정과 설명 답변으로 어떻게 나눌 것인가?"


def _reviewer_lens_template(context: dict, packets: dict, next_actions: dict) -> tuple[list[str], list[dict], list[str], str]:
    reviewer_profile = context.get("reviewer_profile") or {}
    reviewer_evidence = packets.get("reviewer_packet", {}).get("evidence", {})
    answer = [
        "리뷰어가 반복해서 보는 기준을 먼저 잡아야 현재 코멘트를 일관되게 해석할 수 있다.",
        f"현재 추정 lens는 {', '.join(reviewer_profile.get('lenses', [])[:3]) or '없음'} 이다.",
    ]
    sections = [
        {
            "title": "반복 기준",
            "items": reviewer_profile.get("lenses", []) or ["reviewer profile lens를 더 수집한다."],
        },
        {
            "title": "자주 지적한 경로",
            "items": _path_lines(reviewer_evidence.get("ranked_paths", []), "comment_count") or ["reviewer hotspot path가 더 필요하다."],
        },
        {
            "title": "대표 코멘트",
            "items": _comment_lines(
                reviewer_evidence.get("mentor_comment_samples")
                or reviewer_evidence.get("comment_samples", [])
            ) or ["대표 코멘트를 더 수집한다."],
        },
    ]
    postpone = ["리뷰어 기준 파악 전에는 구조 변경 우선순위를 확정하지 않는다."]
    return answer, sections, postpone, "이 리뷰어 기준을 현재 코드에 적용하면 어떤 파일이 먼저 걸리는가?"


def _implementation_template(context: dict, packets: dict, next_actions: dict) -> tuple[list[str], list[dict], list[str], str]:
    diff_files = (context.get("git_context") or {}).get("diff_files", [])
    action_titles = [f"[{item['priority']}] {item['title']}" for item in next_actions.get("next_actions", [])[:3]]
    answer = [
        "구현 계획은 영향 범위를 줄이는 순서로 쪼개는 것이 우선이다.",
        "현재 수정 대상과 packet evidence가 겹치는 파일부터 자르는 편이 안전하다.",
    ]
    sections = [
        {
            "title": "수정 시작점",
            "items": diff_files[:3] or ["현재 diff 파일이 없으면 PR hotspot path부터 본다."],
        },
        {
            "title": "작업 순서",
            "items": action_titles or ["next-action을 먼저 생성한다."],
        },
    ]
    postpone = ["큰 구조 변경은 작은 리팩터링 단계로 나눠서 진행한다."]
    return answer, sections, postpone, "이 변경을 가장 작은 단계로 자르면 첫 단계는 무엇인가?"


def _testing_template(context: dict, packets: dict, next_actions: dict) -> tuple[list[str], list[dict], list[str], str]:
    pr_evidence = packets.get("pr_report", {}).get("evidence", {})
    diff_files = (context.get("git_context") or {}).get("diff_files", [])
    answer = [
        "테스트는 현재 변경을 가장 싸게 검증하는 시나리오부터 잡아야 한다.",
        "저장 구조나 계층을 전부 검증하려 하기보다, 이번 변경으로 깨질 행동을 먼저 고른다.",
    ]
    sections = [
        {
            "title": "우선 검증할 경로",
            "items": diff_files[:3] or _path_lines(pr_evidence.get("hotspot_paths", []), "comment_count") or ["변경 파일 기준으로 테스트 대상을 좁힌다."],
        },
        {
            "title": "검증 후보 시나리오",
            "items": _comment_lines(_mentor_comment_samples(pr_evidence)) or ["가장 많이 지적된 경로의 대표 동작 하나를 테스트한다."],
        },
    ]
    postpone = ["테스트 전략 단계에서는 모든 조합을 다 커버하려 하지 않는다."]
    return answer, sections, postpone, "이 변경을 가장 싸게 검증하는 테스트 하나는 무엇인가?"


def _intent_template(intent: str, context: dict, packets: dict, next_actions: dict) -> tuple[list[str], list[dict], list[str], str | None]:
    mapping = {
        "review_triage": _review_triage_template,
        "concept_explanation": _concept_explanation_template,
        "peer_comparison": _peer_comparison_template,
        "pr_response": _pr_response_template,
        "reviewer_lens": _reviewer_lens_template,
        "implementation_planning": _implementation_template,
        "testing_strategy": _testing_template,
    }
    builder = mapping.get(intent)
    if builder is None:
        return (
            ["현재 컨텍스트를 기준으로 다음 학습 액션을 정리한다."],
            _generic_sections(context, next_actions),
            ["현재 핵심 주제와 직접 관련 없는 구조 변경은 뒤로 미룬다."],
            "이 해석을 현재 코드의 어떤 파일부터 확인해야 하는가?",
        )
    return builder(context, packets, next_actions)
