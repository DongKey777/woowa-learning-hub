"""Teaching-section builders extracted from response.py."""

from __future__ import annotations

from .response_memory import _infer_question_focus
from .response_evidence import (
    _clip_text,
    _mentor_comment_samples,
    _mentor_review_samples,
    _unique_lines,
)


def _dominant_learning_point_ids(profile: dict) -> set[str]:
    return {
        item.get("learning_point")
        for item in profile.get("dominant_learning_points", [])
        if item.get("learning_point") and item.get("confidence") in {"medium", "high"}
    }


def _deepen_and_broaden_lines(interpretation_payload: dict, profile: dict, limit: int = 3) -> tuple[list[str], list[str]]:
    dominant = _dominant_learning_point_ids(profile)
    deepen = []
    broaden = []
    for item in interpretation_payload.get("learning_point_recommendations", []):
        primary = item.get("primary_candidate") or {}
        line = f"{item.get('label')}: PR #{primary.get('pr_number')}{_cohort_suffix(primary)} - {primary.get('title')}"
        if primary.get("best_evidence"):
            line += f" | {primary.get('best_evidence')}"
        if item.get("learning_point") in dominant:
            deepen.append(line)
        else:
            broaden.append(line)
    return deepen[:limit], broaden[:limit]


def _topic_boundary(topic: str | None) -> str:
    boundaries = {
        "Repository": "도메인 입장에서 필요한 저장/복원 책임과 DB 접근 세부 구현을 어디까지 분리할지의 경계",
        "DAO": "SQL 실행 단위와 aggregate 복원 책임을 어디서 나눌지의 경계",
        "Transaction": "하나의 유스케이스를 원자적으로 저장해야 하는 범위를 어디까지 볼지의 경계",
        "Service": "유스케이스 조합 책임과 도메인 규칙 책임을 어디서 끊을지의 경계",
        "Palace": "보드 공간 규칙과 기물 이동 규칙을 어느 객체가 들고 있을지의 경계",
        "Getter": "도메인 노출을 최소화하면서 외부 계층에 필요한 정보를 어떤 질의 메서드로 전달할지의 경계",
        "DTO": "도메인 객체와 저장/전달 전용 데이터를 어디서 변환할지의 경계",
        "Test": "행동 검증에 필요한 최소 시나리오와 저장 구조 세부 구현을 어디까지 드러낼지의 경계",
    }
    return boundaries.get(topic or "", "현재 변경의 책임 경계를 어디서 자를지의 문제")


def _display_topic(context: dict) -> str | None:
    return context.get("primary_topic") or context.get("topic_query")


def _learning_point_recommendations(packets: dict) -> list[dict]:
    return (packets.get("candidate_interpretation") or {}).get("learning_point_recommendations", [])


def _primary_recommendation(packets: dict) -> dict | None:
    recommendations = _learning_point_recommendations(packets)
    if not recommendations:
        return None
    return recommendations[0]


def _primary_candidate(recommendation: dict | None) -> dict:
    if not recommendation:
        return {}
    return recommendation.get("primary_candidate") or {}


def _primary_quote(recommendation: dict | None) -> dict | None:
    candidate = _primary_candidate(recommendation)
    threads = candidate.get("thread_samples") or []
    for thread in threads:
        participants = thread.get("participants") or []
        mentor_turns = [
            p for p in participants
            if (p.get("role") or "").startswith("mentor")
        ]
        if len(participants) >= 2 and mentor_turns:
            last_mentor = mentor_turns[-1]
            return {
                "source": "thread",
                "pr_number": candidate.get("pr_number"),
                "path": thread.get("path"),
                "line": thread.get("line"),
                "author": last_mentor.get("author"),
                "excerpt": last_mentor.get("body_excerpt"),
                "role_sequence": thread.get("role_sequence"),
            }
    quotes = candidate.get("evidence_quotes") or []
    if not quotes:
        return None
    return quotes[0]


def _quote_location(quote: dict | None) -> str | None:
    if not quote:
        return None
    path = quote.get("path")
    line = quote.get("line")
    if path and line:
        return f"{path}:{line}"
    return path


def _cohort_suffix(candidate: dict | None) -> str:
    """Append " (YYYY년 자료)" when the peer PR is from a prior cohort.

    The peer-cohort plan requires this caveat to surface in every line
    where the learner reads a PR reference, not just in evidence
    sections — a 2024 PR mentioned without context can be read as if it
    came from the same mission as the learner.
    """
    if not isinstance(candidate, dict):
        return ""
    if not candidate.get("cohort_caveat"):
        return ""
    year = candidate.get("created_year")
    if not year:
        return ""
    return f" ({year}년 자료)"


def _focus_core_lesson(question_focus: str) -> str:
    lessons = {
        "lesson": "이 질문은 정의를 외우는 문제가 아니라, 현재 코드에서 어떤 책임이 섞였는지 찾는 문제다.",
        "example": "비교의 목적은 정답 PR을 찾는 것이 아니라, 같은 기능을 어디서 끊었는지 보는 것이다.",
        "reviewer": "리뷰를 읽을 때는 표현보다 리뷰어가 문제로 본 책임 경계를 먼저 잡아야 한다.",
        "application": "적용은 새 추상화를 추가하기보다, 지금 경계가 가장 먼저 흔들리는 파일 하나를 고르는 데서 시작한다.",
        "response": "리뷰 답변은 방어문을 만드는 일이 아니라, 무엇을 바꾸고 무엇을 유지할지 경계 기준으로 분리하는 일이다.",
    }
    return lessons.get(question_focus, "현재 질문의 핵심은 코드의 책임 경계를 근거와 함께 해석하는 것이다.")


def _topic_focus_lesson(topic: str | None, question_focus: str) -> str:
    if topic == "Repository":
        lessons = {
            "lesson": "Repository를 단순 DB 접근 래퍼로 보면 부족하다. 도메인에 어떤 저장/복원을 약속하는지가 먼저다.",
            "example": "Repository 비교에서는 클래스 이름보다 aggregate 복원을 어디서 끝내는지 보는 편이 정확하다.",
            "reviewer": "Repository 관련 리뷰는 보통 SQL 문법보다 연결, 변환, 복원 책임이 한곳에 섞였는지를 먼저 본다.",
            "application": "Repository를 바꿀 때는 save/find 시그니처보다 내부에서 도메인 복원과 저장 기술 세부가 같이 있는지부터 확인한다.",
            "response": "Repository 관련 답변에서는 왜 필요하냐보다, 현재 코드에서 DAO나 저장 기술 세부와 어떻게 나눴는지를 설명해야 한다.",
        }
        return lessons.get(question_focus, lessons["lesson"])

    if topic == "DAO":
        lessons = {
            "lesson": "DAO는 데이터를 읽고 쓰는 기술 경계를 다루는 쪽이지, 유스케이스 의미까지 들고 가는 쪽은 아니다.",
            "example": "DAO 비교에서는 SQL 개수보다 row/document 수준 처리까지만 멈추는지를 보는 편이 낫다.",
            "reviewer": "DAO 관련 리뷰는 보통 연결 생성, 설정값, CRUD가 한 클래스에 섞이는 순간을 민감하게 본다.",
            "application": "DAO를 손볼 때는 도메인 복원 로직이 밀려 들어와 있는지부터 확인한다.",
            "response": "DAO 답변에서는 기술 세부를 감추는 이유와, 그 때문에 Repository가 무엇을 더 맡는지 같이 설명해야 한다.",
        }
        return lessons.get(question_focus, lessons["lesson"])

    if topic == "Transaction":
        lessons = {
            "lesson": "트랜잭션은 DB 기능 이름이 아니라, 유스케이스가 중간 상태 없이 끝나야 하는 경계다.",
            "example": "트랜잭션 사례 비교에서는 어노테이션 유무보다 어디까지를 한 번에 저장하려 했는지를 봐야 한다.",
            "reviewer": "트랜잭션 관련 리뷰는 save가 여러 번 호출되는 사실보다, 중간 실패 시 어떤 상태가 남는지를 본다.",
            "application": "적용할 때는 한 유스케이스 안에서 여러 저장소 호출이 묶이는 지점부터 찾으면 된다.",
            "response": "트랜잭션 답변에서는 성능보다 정합성을 위해 어디를 원자적으로 묶었는지 설명하는 편이 맞다.",
        }
        return lessons.get(question_focus, lessons["lesson"])

    if topic == "Service":
        lessons = {
            "lesson": "Service는 규칙을 대신 갖는 객체라기보다, 유스케이스 흐름을 조합하는 객체에 가깝다.",
            "example": "Service 비교에서는 메서드 수보다 도메인 규칙과 저장 흐름을 어디서 조합하는지 보는 편이 좋다.",
            "reviewer": "Service 관련 리뷰는 보통 도메인 규칙이 서비스로 새어 나왔는지, 반대로 저장 흐름이 도메인으로 들어갔는지를 본다.",
            "application": "적용은 Service가 지금 과하게 알고 있는지, 아니면 오히려 유스케이스 조합을 못 하고 있는지부터 확인하면 된다.",
            "response": "Service 답변에서는 서비스가 왜 존재하는지보다, 현재 어디까지를 유스케이스 조합 책임으로 봤는지 설명해야 한다.",
        }
        return lessons.get(question_focus, lessons["lesson"])

    if topic:
        return f"{topic}를 볼 때도 결국 핵심은 {_topic_boundary(topic)}."
    return "현재 질문의 핵심은 책임 경계를 어디서 자를지 코드와 리뷰 근거로 설명하는 것이다."


def _learning_point_lesson(recommendation: dict | None) -> str | None:
    if not recommendation:
        return None

    lessons = {
        "repository_boundary": "핵심은 Repository 이름이 아니라 aggregate 복원 책임과 저장 기술 세부가 어디서 갈리는지다.",
        "responsibility_boundary": "계층을 나누는 목적은 클래스를 늘리는 것이 아니라, 바뀌는 이유가 다른 코드를 분리하는 데 있다.",
        "transaction_consistency": "트랜잭션 경계는 메서드 호출 수가 아니라, 중간 상태가 남으면 안 되는 유스케이스를 기준으로 잡아야 한다.",
        "db_modeling": "DB 모델링에서는 테이블 수보다 도메인 상태를 안정적으로 저장하고 다시 복원할 수 있는지가 더 중요하다.",
        "reconstruction_mapping": "복원 로직은 데이터를 읽는 코드와 도메인을 만드는 코드를 뒤섞지 않는 쪽이 유지보수에 유리하다.",
        "testing_strategy": "테스트는 저장 구조 전부를 증명하려 하기보다, 이번 변경으로 깨질 행동 하나를 가장 싸게 잡는 데서 시작한다.",
        "resource_lifecycle": "연결과 클라이언트 수명주기에서는 누가 생성했는가보다 누가 닫을 책임을 가지는지가 더 중요하다.",
        "review_response": "리뷰 대응은 맞고 틀림을 변론하는 일이 아니라, 수정/유지/보류 판단을 근거와 함께 나누는 작업이다.",
    }
    learning_point = recommendation.get("learning_point")
    if learning_point in lessons:
        return lessons[learning_point]

    label = recommendation.get("label")
    description = recommendation.get("description")
    if label and description:
        return f"{label}에서는 {description}."
    return None


def _grounded_lesson(recommendation: dict | None) -> str | None:
    if not recommendation:
        return None

    candidate = _primary_candidate(recommendation)
    quote = _primary_quote(recommendation)
    if not quote:
        return None

    pr_number = candidate.get("pr_number")
    label = recommendation.get("label") or "이 포인트"
    location = _quote_location(quote)
    excerpt = _clip_text(quote.get("excerpt"))
    author = quote.get("author") or "리뷰어"
    source = {
        "review_comment": "리뷰 코멘트",
        "review_body": "리뷰 본문",
        "issue_comment": "코멘트",
        "pr_body": "PR 본문",
    }.get(quote.get("source"), "근거")

    cohort_suffix = _cohort_suffix(candidate)
    if location and excerpt:
        return f"{label}는 PR #{pr_number}{cohort_suffix}에서 {author}가 {location} {source}로 '{excerpt}'라고 짚은 지점에서 실제로 드러난다."
    if excerpt:
        return f"{label}는 PR #{pr_number}{cohort_suffix}에서 {author}가 '{excerpt}'라고 짚은 지점에서 실제로 드러난다."
    return f"{label}는 PR #{pr_number}{cohort_suffix}의 실제 리뷰 근거와 연결해 봐야 한다."


def _memory_lesson(memory_policy: dict) -> str | None:
    mode = memory_policy.get("mode")
    if mode == "broaden":
        return "이번 질문에서는 반복해서 보던 포인트만 깊게 파기보다, 덜 본 포인트를 같이 확장해 보는 편이 좋다."
    if mode == "deepen":
        return "이번 질문은 이미 반복해서 보던 핵심 경계를 더 깊게 다지는 쪽이 효과적이다."
    return None


def _data_confidence_lesson(context: dict) -> str | None:
    archive_status = context.get("archive_status") or {}
    data_confidence = archive_status.get("data_confidence")
    total_prs = (archive_status.get("signals") or {}).get("total_prs", 0)
    if data_confidence == "partial" and total_prs:
        return f"지금은 수집된 PR이 {total_prs}개뿐이라 사례를 정답처럼 일반화하기보다, 반복해서 보이는 기준 위주로 받아들이는 편이 안전하다."
    return None


def _lesson_items(context: dict, packets: dict, question_focus: str) -> list[str]:
    recommendation = _primary_recommendation(packets)
    items = [
        _focus_core_lesson(question_focus),
        _topic_focus_lesson(_display_topic(context), question_focus),
        _learning_point_lesson(recommendation),
        _grounded_lesson(recommendation),
        _memory_lesson(context.get("memory_policy", {})),
        _data_confidence_lesson(context),
    ]

    lesson_items = _unique_lines(items, limit=4)
    if lesson_items:
        return lesson_items
    return ["질문의 핵심은 현재 코드의 책임 경계를 근거와 함께 해석하는 것이다."]


def _example_items(context: dict, packets: dict) -> list[str]:
    items = []
    for item in _learning_point_recommendations(packets)[:3]:
        primary = item.get("primary_candidate") or {}
        pr_number = primary.get("pr_number")
        title = primary.get("title") or "title 없음"
        cohort_suffix = _cohort_suffix(primary)
        quotes = primary.get("evidence_quotes") or []
        if quotes:
            quote = quotes[0]
            author = quote.get("author")
            location = _quote_location(quote)
            excerpt = _clip_text(quote.get("excerpt"), limit=95)
            if location and excerpt:
                subject = f"{author}가" if author else "리뷰어가"
                items.append(
                    f"PR #{pr_number}{cohort_suffix} ({title})에서는 {item.get('label')}를 {location}에서 다뤘다. {subject} '{excerpt}'라고 짚었다."
                )
                continue
            if excerpt:
                subject = f"{author}가" if author else "리뷰어가"
                items.append(f"PR #{pr_number}{cohort_suffix} ({title})에서는 {item.get('label')}를 다뤘고, {subject} '{excerpt}'라고 짚었다.")
                continue
            continue
        items.append(f"{item.get('label')} 사례로는 PR #{pr_number}{cohort_suffix} ({title})를 볼 수 있다.")
    return _unique_lines(items, limit=3)


def _reviewer_view_items(context: dict, packets: dict) -> list[str]:
    items = []
    primary_quote = _primary_quote(_primary_recommendation(packets))
    if primary_quote:
        author = primary_quote.get("author") or "리뷰어"
        location = _quote_location(primary_quote)
        excerpt = _clip_text(primary_quote.get("excerpt"), limit=95)
        if location and excerpt:
            items.append(f"{author}는 {location}에서 '{excerpt}'처럼 구현 세부보다 책임이 섞인 지점을 먼저 봤다.")
        elif excerpt:
            items.append(f"{author}는 '{excerpt}'처럼 설계 기준을 먼저 확인했다.")

    reviewer_profile = context.get("reviewer_profile") or {}
    if reviewer_profile.get("lenses"):
        lenses = ", ".join(reviewer_profile.get("lenses", [])[:3])
        items.append(f"현재 리뷰어는 보통 {lenses} 관점으로 코드를 본다.")

    reviewer_packet = packets.get("reviewer_packet", {})
    reviewer_evidence = reviewer_packet.get("evidence", {})
    ranked_paths = reviewer_evidence.get("ranked_paths", [])
    if ranked_paths:
        top_path = ranked_paths[0]
        items.append(f"이 리뷰어는 {top_path.get('path')} 같은 경로에서 구조적 책임 문제를 자주 짚는다.")

    if not items:
        pr_report = packets.get("pr_report", {})
        pr_evidence = pr_report.get("evidence", {})
        samples = _mentor_review_samples(pr_evidence)
        if samples:
            sample = samples[0]
            items.append(f"현재 리뷰에서는 {sample.get('reviewer_login')}가 '{sample.get('body_excerpt')}'라는 식으로 전체 기준을 먼저 제시한다.")

    if not items:
        items.append("리뷰어 관점이 명확하지 않다면, 현재 PR의 hotspot path에서 반복적으로 나온 지적을 먼저 보는 편이 좋다.")
    return _unique_lines(items, limit=3)


def _application_items(context: dict, packets: dict) -> list[str]:
    items = []
    git_context = context.get("git_context") or {}
    diff_files = git_context.get("diff_files", [])
    recommendation = _primary_recommendation(packets)
    if diff_files and recommendation:
        items.append(f"지금은 {diff_files[0]}에서 {recommendation.get('label')}가 실제로 흔들리는지부터 확인하면 된다.")
    if diff_files:
        items.append(f"네 코드에서는 {diff_files[0]}부터 보면 된다.")
    else:
        pr_report = packets.get("pr_report", {})
        pr_evidence = pr_report.get("evidence", {})
        hotspot_paths = pr_evidence.get("hotspot_paths", [])
        if hotspot_paths:
            items.append(f"네 코드에서는 {hotspot_paths[0].get('path')}부터 보는 게 가장 효율적이다.")

    recommendations = _learning_point_recommendations(packets)
    if recommendations:
        items.append(f"지금 코드를 볼 때는 특히 {recommendations[0].get('label')} 관점으로 경계를 다시 보면 좋다.")

    pr_report = packets.get("pr_report", {})
    pr_evidence = pr_report.get("evidence", {})
    comment_samples = _mentor_comment_samples(pr_evidence)
    if comment_samples:
        sample = comment_samples[0]
        path = sample.get("path") or "현재 PR 경로"
        line = sample.get("line")
        location = f"{path}:{line}" if line else path
        items.append(f"현재 PR에서도 {location} 코멘트가 바로 적용 지점이다.")

    if not items:
        items.append("현재 코드를 볼 때는 질문과 직접 연결된 경로 하나를 먼저 정하고 거기서부터 해석을 시작하는 편이 좋다.")
    return _unique_lines(items, limit=3)


def _reply_items(context: dict, packets: dict) -> list[str]:
    items = []
    recommendation = _primary_recommendation(packets)
    if recommendation:
        items.append(f"답변 첫 문장에서는 {recommendation.get('label')} 관점에서 무엇을 바꾸고 무엇을 유지했는지 먼저 나누는 편이 좋다.")

    primary_quote = _primary_quote(recommendation)
    if primary_quote:
        excerpt = _clip_text(primary_quote.get("excerpt"), limit=95)
        if excerpt:
            items.append(f"리뷰 문장을 그대로 반복하기보다, '{excerpt}'가 말하는 문제를 어떻게 해석했고 어떻게 대응했는지 적으면 된다.")

    pr_report = packets.get("pr_report", {})
    pr_evidence = pr_report.get("evidence", {})
    comment_samples = _mentor_comment_samples(pr_evidence)
    review_samples = _mentor_review_samples(pr_evidence)
    if comment_samples:
        sample = comment_samples[0]
        path = sample.get("path") or "path 없음"
        line = sample.get("line")
        location = f"{path}:{line}" if line else path
        items.append(f"코드로 바로 반영할 후보는 {location} 코멘트처럼 path/line이 붙은 지적이다.")
    if review_samples:
        sample = review_samples[0]
        items.append(f"설명으로 먼저 정리할 후보는 {sample.get('reviewer_login')}의 전체 리뷰 본문처럼 의도와 기준을 묻는 코멘트다.")
    items.append("답변은 수정 사실, 유지 이유, 남은 trade-off를 분리해서 쓰는 편이 좋다.")
    return _unique_lines(items, limit=3)


def _teaching_section_order(intent: str, question_focus: str) -> list[str]:
    if question_focus == "application":
        return ["lesson", "application", "example", "reviewer"]
    if question_focus == "reviewer":
        return ["lesson", "reviewer", "example", "application"]
    if question_focus == "response":
        return ["lesson", "reviewer", "application", "reply"]
    if intent == "peer_comparison":
        return ["lesson", "example", "reviewer", "application"]
    return ["lesson", "example", "reviewer", "application"]


def _build_teaching_sections(context: dict, packets: dict) -> tuple[list[str], list[dict]]:
    focus_info = _infer_question_focus(context)
    question_focus = focus_info["focus"]
    lesson_items = _lesson_items(context, packets, question_focus)

    section_builders = {
        "lesson": ("이번 질문의 핵심 교훈", lesson_items),
        "example": ("비슷한 사례에서는 이렇게 했다", _example_items(context, packets)),
        "reviewer": ("리뷰어는 이런 점을 봤다", _reviewer_view_items(context, packets)),
        "application": ("네 코드에선 여기부터 보면 된다", _application_items(context, packets)),
        "reply": ("답변은 이렇게 구성하면 된다", _reply_items(context, packets)),
    }

    ordered_sections = []
    for key in _teaching_section_order(context.get("primary_intent") or "", question_focus):
        title, items = section_builders[key]
        if items:
            ordered_sections.append({"kind": key, "title": title, "items": items})

    teaching_points = lesson_items[:3]
    return teaching_points, ordered_sections
