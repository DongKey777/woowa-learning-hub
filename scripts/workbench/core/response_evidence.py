"""Evidence formatting and quoting helpers extracted from response.py."""

from __future__ import annotations

from .response_memory import _learning_memory_profile


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
