from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str | None) -> dict | None:
    if not path:
        return None
    json_path = Path(path)
    if not json_path.exists():
        return None
    try:
        return json.loads(json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _packet_payloads(context: dict) -> dict:
    packets = {}
    for key in ["pr_report", "reviewer_packet", "topic_packet", "focus_ranking", "candidate_interpretation"]:
        payload = _load_json(context.get(f"{key}_json_path"))
        if payload is None and context.get(f"{key}_evidence") is not None:
            payload = {"evidence": context.get(f"{key}_evidence")}
        if payload is None and context.get(key) is not None:
            payload = context.get(key)
        packets[key] = payload or {}
    return packets


def _learning_memory_profile(context: dict) -> dict:
    return context.get("learning_memory_profile") or {}


def _learning_memory_summary(context: dict) -> dict:
    return context.get("learning_memory_summary") or {}


def _infer_question_focus(context: dict) -> dict:
    prompt = (context.get("prompt") or "").lower()
    intent = context.get("primary_intent") or ""

    focus_rules = [
        ("response", ["답변", "reply", "response", "뭐라고", "어떻게 답"]),
        ("application", ["내 코드", "어디", "어떻게 적용", "어떻게 바꿔", "어디부터", "수정", "반영"]),
        ("reviewer", ["리뷰어", "리뷰", "코멘트", "왜 달렸", "관점"]),
        ("example", ["다른 크루", "사례", "예시", "비교", "패턴", "어떻게 했"]),
        ("lesson", ["왜", "무슨 뜻", "설명", "개념", "차이", "원리", "관점"]),
    ]

    for focus, keywords in focus_rules:
        if any(keyword in prompt for keyword in keywords):
            return {"focus": focus, "reason": f"prompt:{focus}"}

    fallback = {
        "concept_explanation": "lesson",
        "peer_comparison": "example",
        "reviewer_lens": "reviewer",
        "implementation_planning": "application",
        "testing_strategy": "application",
        "review_triage": "reviewer",
        "pr_response": "response",
    }
    return {"focus": fallback.get(intent, "lesson"), "reason": f"intent:{intent}"}


def _memory_policy(context: dict, packets: dict) -> dict:
    profile = _learning_memory_profile(context)
    confidence = profile.get("confidence", "low")
    if confidence == "low":
        return {
            "mode": "neutral",
            "reason": "memory confidence is low, so current question and current evidence should dominate",
        }

    streak = profile.get("recent_learning_streak") or {}
    if (streak.get("count") or 0) >= 3:
        return {
            "mode": "broaden",
            "reason": f"recent learning streak on {streak.get('learning_point')} suggests broadening into a less explored point",
        }

    dormant_points = {
        item.get("learning_point")
        for item in profile.get("dominant_learning_points", [])
        if item.get("recency_status") == "dormant" and item.get("confidence") in {"medium", "high"}
    }
    if dormant_points:
        return {
            "mode": "broaden",
            "reason": f"dominant points {', '.join(sorted(dormant_points))} are dormant — broadening to refresh or explore new areas",
        }

    active_repeated = {
        item.get("learning_point")
        for item in profile.get("repeated_learning_points", [])
        if item.get("confidence") in {"medium", "high"} and item.get("recency_status") in {"active", "cooling"}
    }
    interpretation = packets.get("candidate_interpretation", {})
    if any(item.get("learning_point") in active_repeated for item in interpretation.get("learning_point_recommendations", [])):
        return {
            "mode": "deepen",
            "reason": "current recommendations overlap with actively repeated learning points",
        }

    return {
        "mode": "neutral",
        "reason": "no strong memory signal suggests explicit deepen or broaden policy",
    }


def _join_states(states: dict) -> str:
    if not states:
        return "state 없음"
    ordered = sorted(states.items(), key=lambda item: item[0])
    return ", ".join(f"{name}={count}" for name, count in ordered)


def _path_lines(items: list[dict], count_key: str, limit: int = 3) -> list[str]:
    lines = []
    for item in items[:limit]:
        path = item.get("path")
        count = item.get(count_key)
        if not path:
            continue
        if count is None:
            lines.append(path)
            continue
        lines.append(f"{path} ({count})")
    return lines


def _mentor_comment_samples(pr_evidence: dict) -> list[dict]:
    mentor = pr_evidence.get("mentor_comment_samples")
    if mentor:
        return mentor
    return pr_evidence.get("comment_samples", [])


def _mentor_review_samples(pr_evidence: dict) -> list[dict]:
    samples = pr_evidence.get("review_samples", [])
    mentors = [s for s in samples if (s.get("reviewer_role") or "mentor") == "mentor"]
    return mentors or samples


def _comment_lines(items: list[dict], limit: int = 3) -> list[str]:
    lines = []
    for item in items[:limit]:
        path = item.get("path") or "path 없음"
        line = item.get("line")
        excerpt = item.get("body_excerpt") or "본문 없음"
        if line:
            lines.append(f"{path}:{line} - {excerpt}")
            continue
        lines.append(f"{path} - {excerpt}")
    return lines


def _review_lines(items: list[dict], limit: int = 3) -> list[str]:
    lines = []
    for item in items[:limit]:
        reviewer = item.get("reviewer_login") or "reviewer 없음"
        state = item.get("state") or "state 없음"
        excerpt = item.get("body_excerpt") or "본문 없음"
        lines.append(f"{reviewer} [{state}] - {excerpt}")
    return lines


def _pr_lines(items: list[dict], limit: int = 3) -> list[str]:
    lines = []
    for item in items[:limit]:
        number = item.get("number")
        title = item.get("title") or "title 없음"
        if number is None:
            continue
        tail = []
        if item.get("hit_count") is not None:
            tail.append(f"hit={item['hit_count']}")
        if item.get("comment_count") is not None:
            tail.append(f"comments={item['comment_count']}")
        suffix = f" ({', '.join(tail)})" if tail else ""
        lines.append(f"PR #{number} - {title}{suffix}")
    return lines


def _focus_pr_lines(focus_payload: dict, limit: int = 3) -> list[str]:
    lines = []
    for item in focus_payload.get("candidates", [])[:limit]:
        number = item.get("pr_number")
        title = item.get("title") or "title 없음"
        score = item.get("score")
        author = item.get("author_login")
        matched_paths = item.get("matched_paths", [])
        suffix = []
        if score is not None:
            suffix.append(f"score={score}")
        if author:
            suffix.append(f"author={author}")
        if matched_paths:
            suffix.append(f"path={matched_paths[0]}")
        tail = f" ({', '.join(suffix)})" if suffix else ""
        lines.append(f"PR #{number} - {title}{tail}")
    return lines


def _interpretation_lines(interpretation_payload: dict, limit: int = 3) -> list[str]:
    lines = []
    for item in interpretation_payload.get("learning_point_recommendations", [])[:limit]:
        primary = item.get("primary_candidate") or {}
        pr_number = primary.get("pr_number")
        title = primary.get("title") or "title 없음"
        label = item.get("label")
        quotes = primary.get("evidence_quotes") or []
        if quotes:
            quote = quotes[0]
            source = quote.get("source")
            path = quote.get("path")
            line = quote.get("line")
            excerpt = quote.get("excerpt")
            location = ""
            if path and line:
                location = f"{path}:{line}"
            elif path:
                location = path
            if location:
                lines.append(f"{label}: PR #{pr_number} - {title} | {source} {location} | {excerpt}")
                continue
            lines.append(f"{label}: PR #{pr_number} - {title} | {source} | {excerpt}")
            continue
        lines.append(f"{label}: PR #{pr_number} - {title}")
    return lines


def _candidate_profile_lines(interpretation_payload: dict, limit: int = 3) -> list[str]:
    lines = []
    for item in interpretation_payload.get("candidate_profiles", [])[:limit]:
        labels = [point.get("label") for point in item.get("learning_points", [])[:3] if point.get("label")]
        label_text = ", ".join(labels)
        if label_text:
            lines.append(f"PR #{item['pr_number']} - {label_text}")
            continue
        lines.append(f"PR #{item['pr_number']} - {item.get('title')}")
    return lines


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
        line = f"{item.get('label')}: PR #{primary.get('pr_number')} - {primary.get('title')}"
        if primary.get("best_evidence"):
            line += f" | {primary.get('best_evidence')}"
        if item.get("learning_point") in dominant:
            deepen.append(line)
        else:
            broaden.append(line)
    return deepen[:limit], broaden[:limit]


def _focus_excerpt_lines(focus_payload: dict, limit: int = 3) -> list[str]:
    lines = []
    for item in focus_payload.get("candidates", [])[:limit]:
        number = item.get("pr_number")
        matched_comment_samples = item.get("matched_comment_samples", [])
        matched_review_samples = item.get("matched_review_samples", [])
        matched_issue_comment_samples = item.get("matched_issue_comment_samples", [])
        matched_paths = item.get("matched_paths", [])
        matched_terms = item.get("matched_terms", [])
        excerpt = item.get("focus_excerpt")
        if matched_comment_samples:
            sample = matched_comment_samples[0]
            path = sample.get("path") or "path 없음"
            line = sample.get("line")
            prefix = f"{path}:{line}" if line else path
            lines.append(f"PR #{number} - review comment {prefix} | {sample.get('body_excerpt')}")
            continue
        if matched_review_samples:
            sample = matched_review_samples[0]
            reviewer = sample.get("reviewer_login") or "reviewer 없음"
            state = sample.get("state") or "state 없음"
            lines.append(f"PR #{number} - review body {reviewer}[{state}] | {sample.get('body_excerpt')}")
            continue
        if matched_issue_comment_samples:
            sample = matched_issue_comment_samples[0]
            user = sample.get("user_login") or "user 없음"
            lines.append(f"PR #{number} - issue comment {user} | {sample.get('body_excerpt')}")
            continue
        if matched_paths or matched_terms:
            parts = []
            if matched_paths:
                parts.append(f"path={matched_paths[0]}")
            if matched_terms:
                parts.append(f"terms={', '.join(matched_terms[:3])}")
            lines.append(f"PR #{number} - {' | '.join(parts)}")
            continue
        if not excerpt:
            continue
        lines.append(f"PR #{number} - {excerpt}")
    return lines


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


def _clip_text(text: str | None, limit: int = 110) -> str | None:
    if not text:
        return None
    collapsed = " ".join(str(text).split())
    if len(collapsed) <= limit:
        return collapsed
    return collapsed[: limit - 3].rstrip() + "..."


def _unique_lines(items: list[str], limit: int | None = None) -> list[str]:
    lines = []
    seen = set()
    for item in items:
        if not item:
            continue
        normalized = " ".join(item.split())
        if normalized in seen:
            continue
        seen.add(normalized)
        lines.append(normalized)
        if limit is not None and len(lines) >= limit:
            break
    return lines


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

    if location and excerpt:
        return f"{label}는 PR #{pr_number}에서 {author}가 {location} {source}로 '{excerpt}'라고 짚은 지점에서 실제로 드러난다."
    if excerpt:
        return f"{label}는 PR #{pr_number}에서 {author}가 '{excerpt}'라고 짚은 지점에서 실제로 드러난다."
    return f"{label}는 PR #{pr_number}의 실제 리뷰 근거와 연결해 봐야 한다."


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
        quotes = primary.get("evidence_quotes") or []
        if quotes:
            quote = quotes[0]
            author = quote.get("author")
            location = _quote_location(quote)
            excerpt = _clip_text(quote.get("excerpt"), limit=95)
            if location and excerpt:
                subject = f"{author}가" if author else "리뷰어가"
                items.append(
                    f"PR #{pr_number} ({title})에서는 {item.get('label')}를 {location}에서 다뤘다. {subject} '{excerpt}'라고 짚었다."
                )
                continue
            if excerpt:
                subject = f"{author}가" if author else "리뷰어가"
                items.append(f"PR #{pr_number} ({title})에서는 {item.get('label')}를 다뤘고, {subject} '{excerpt}'라고 짚었다.")
                continue
            continue
        items.append(f"{item.get('label')} 사례로는 PR #{pr_number} ({title})를 볼 수 있다.")
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


def _response_evidence(context: dict, packets: dict) -> list[dict]:
    evidence = []

    pr_packet = packets.get("pr_report", {})
    pr_evidence = pr_packet.get("evidence", {})
    if pr_evidence:
        review_summary = pr_evidence.get("review_summary", {})
        overview = pr_evidence.get("overview", {})
        evidence.append({
            "type": "pr_report",
            "json_path": context.get("pr_report_json_path"),
            "markdown_path": context.get("pr_report_path"),
            "summary": [
                f"PR #{overview.get('pr_number')} changed_files={overview.get('changed_files')}",
                f"reviews={review_summary.get('review_count', 0)}, comments={review_summary.get('review_comment_count', 0)}",
            ],
            "highlights": _path_lines(pr_evidence.get("hotspot_paths", []), "comment_count", limit=3),
        })

    reviewer_packet = packets.get("reviewer_packet", {})
    reviewer_evidence = reviewer_packet.get("evidence", {})
    if reviewer_evidence:
        reviewer_summary = reviewer_evidence.get("summary") or {}
        evidence.append({
            "type": "reviewer_packet",
            "json_path": context.get("reviewer_packet_json_path"),
            "markdown_path": context.get("reviewer_packet_path"),
            "summary": [
                f"reviews={reviewer_summary.get('review_count', 0)}",
                f"changes_requested={reviewer_summary.get('changes_requested_count', 0)}",
            ],
            "highlights": _path_lines(reviewer_evidence.get("ranked_paths", []), "comment_count", limit=3),
        })

    topic_packet = packets.get("topic_packet", {})
    topic_evidence = topic_packet.get("evidence", {})
    if topic_evidence:
        topic_summary = topic_evidence.get("summary", {})
        evidence.append({
            "type": "topic_packet",
            "json_path": context.get("topic_packet_json_path"),
            "markdown_path": context.get("topic_packet_path"),
            "summary": [
                f"query={topic_summary.get('query')}",
                f"related_prs={topic_summary.get('related_pr_count', 0)}",
            ],
            "highlights": _path_lines(topic_evidence.get("ranked_paths", []), "hit_count", limit=3),
        })

    focus_payload = packets.get("focus_ranking", {})
    if focus_payload:
        evidence.append({
            "type": "focus_ranking",
            "json_path": context.get("focus_ranking_path"),
            "markdown_path": None,
            "summary": [
                f"candidate_count={focus_payload.get('candidate_count', 0)}",
                f"path_source={(focus_payload.get('local_path_signature') or {}).get('source')}",
            ],
            "highlights": _focus_pr_lines(focus_payload, limit=3),
        })

    interpretation_payload = packets.get("candidate_interpretation", {})
    if interpretation_payload:
        evidence.append({
            "type": "candidate_interpretation",
            "json_path": context.get("candidate_interpretation_path"),
            "markdown_path": None,
            "summary": [
                f"learning_points={len(interpretation_payload.get('learning_point_recommendations', []))}",
                f"candidate_profiles={len(interpretation_payload.get('candidate_profiles', []))}",
            ],
            "highlights": _interpretation_lines(interpretation_payload, limit=3),
        })

    profile = _learning_memory_profile(context)
    if profile:
        evidence.append({
            "type": "learning_memory_profile",
            "json_path": context.get("learning_memory_profile_path"),
            "markdown_path": None,
            "summary": [
                f"dominant_learning_points={len(profile.get('dominant_learning_points', []))}",
                f"repeated_question_patterns={len(profile.get('repeated_question_patterns', []))}",
            ],
            "highlights": [
                f"{item.get('label')}: {item.get('count')}회"
                for item in profile.get("dominant_learning_points", [])[:3]
                if item.get("label")
            ],
        })

    return evidence


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
