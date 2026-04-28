from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .paths import repo_context_dir
from .schema_validation import validate_payload
from .thread_builder import build_threads_for_packet

LEARNING_POINT_RULES = [
    {
        "id": "repository_boundary",
        "label": "Repository/DAO 경계",
        "description": "Repository와 DAO의 책임을 어디서 나누고 aggregate 복원을 어디서 맡길지 보는 관점",
        "keywords": ["repository", "dao", "aggregate", "레포지토리", "aggregate root", "table", "boardrepository", "piecerepository"],
        "path_keywords": ["repository", "dao"],
    },
    {
        "id": "responsibility_boundary",
        "label": "계층 책임 분리",
        "description": "controller, service, repository, infra 사이 책임 경계를 어떻게 잡는지 보는 관점",
        "keywords": ["책임", "경계", "관심사", "service", "controller", "infra", "layer", "분리", "협력"],
        "path_keywords": ["controller", "service", "application", "infra"],
    },
    {
        "id": "transaction_consistency",
        "label": "트랜잭션/정합성",
        "description": "하나의 유스케이스를 원자적으로 저장하고 복구해야 하는 범위를 보는 관점",
        "keywords": ["transaction", "rollback", "commit", "정합", "원자", "트랜잭션", "consistency", "connection"],
        "path_keywords": ["transaction", "connection", "factory"],
    },
    {
        "id": "db_modeling",
        "label": "DB 모델링",
        "description": "테이블, 문서, 스키마, 정규화 같은 저장 구조 설계를 보는 관점",
        "keywords": ["schema", "table", "document", "rdb", "mongodb", "db", "sql", "정규화", "컬렉션", "스키마"],
        "path_keywords": ["schema", "dao", "repository", "document", "entity", "data"],
    },
    {
        "id": "reconstruction_mapping",
        "label": "도메인 복원/매핑",
        "description": "DB 데이터에서 도메인 객체를 복원할 때 factory, mapper, dto를 어디에 둘지 보는 관점",
        "keywords": ["restore", "복원", "mapper", "mapping", "factory", "dto", "entity", "document", "rebuild"],
        "path_keywords": ["factory", "mapper", "dto", "entity", "data"],
    },
    {
        "id": "testing_strategy",
        "label": "테스트 전략",
        "description": "DB 연동과 구조 변경을 어떤 테스트 시나리오로 검증할지 보는 관점",
        "keywords": ["test", "테스트", "시나리오", "검증", "fixture", "integration", "jdbc test"],
        "path_keywords": ["test"],
    },
    {
        "id": "resource_lifecycle",
        "label": "리소스/연결 수명주기",
        "description": "Connection, Client, Pool 같은 인프라 자원의 생성과 종료 책임을 보는 관점",
        "keywords": ["close", "resource", "pool", "lifecycle", "connection pool", "config", "설정", "client", "resource leak"],
        "path_keywords": ["connection", "config", "factory", "client"],
    },
    {
        "id": "review_response",
        "label": "리뷰 대응 방식",
        "description": "설명으로 답할지 코드로 바꿀지, 리뷰를 어떻게 구조화해 대응할지 보는 관점",
        "keywords": ["리뷰", "답변", "response", "reply", "설명", "의도", "코멘트", "changes requested"],
        "path_keywords": ["readme"],
    },
]


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_text(text: str | None) -> str:
    if not text:
        return ""
    lowered = text.lower()
    collapsed = re.sub(r"[^0-9a-z가-힣]+", " ", lowered)
    return " ".join(collapsed.split())


def _clip(text: str | None, limit: int = 180) -> str:
    if not text:
        return ""
    flattened = " ".join(text.split())
    if len(flattened) <= limit:
        return flattened
    return flattened[: limit - 3].rstrip() + "..."


def _candidate_text(candidate: dict) -> str:
    parts = [candidate.get("title"), candidate.get("focus_excerpt")]
    for sample in candidate.get("matched_review_samples", []):
        parts.append(sample.get("body_excerpt"))
    for sample in candidate.get("matched_comment_samples", []):
        parts.append(sample.get("body_excerpt"))
    for sample in candidate.get("matched_issue_comment_samples", []):
        parts.append(sample.get("body_excerpt"))
    return _normalize_text(" ".join(part for part in parts if part))


def _candidate_path_text(candidate: dict) -> str:
    parts = []
    parts.extend(candidate.get("matched_paths", []))
    parts.extend(candidate.get("path_examples", []))
    return _normalize_text(" ".join(parts))


def _best_evidence(candidate: dict) -> str:
    for sample in candidate.get("matched_comment_samples", []):
        excerpt = sample.get("body_excerpt")
        if excerpt:
            return f"review comment: {_clip(excerpt)}"
    for sample in candidate.get("matched_review_samples", []):
        excerpt = sample.get("body_excerpt")
        if excerpt:
            return f"review body: {_clip(excerpt)}"
    for sample in candidate.get("matched_issue_comment_samples", []):
        excerpt = sample.get("body_excerpt")
        if excerpt:
            return f"issue comment: {_clip(excerpt)}"
    if candidate.get("focus_excerpt"):
        return f"pr body: {_clip(candidate.get('focus_excerpt'))}"
    return ""


def _source_quote(source_type: str, pr_number: int | None, sample: dict) -> dict:
    return {
        "source": source_type,
        "pr_number": pr_number,
        "path": sample.get("path"),
        "line": sample.get("line"),
        "author": sample.get("user_login") or sample.get("reviewer_login"),
        "excerpt": sample.get("body_excerpt"),
    }


def _extract_point_terms(point: dict) -> set[str]:
    """Extract keyword terms from point.reasons, ignoring profile-boost reasons.

    profile:* reasons (underexplored/repeated/active/dominant) describe how the
    rule was boosted, not what it's about. Including them would let the
    body-scan fallback in _sample_matches_point match comments containing
    those literal words by accident.
    """
    terms: set[str] = set()
    for reason in point.get("reasons", []):
        if not isinstance(reason, str):
            continue
        if reason.startswith("text:") or reason.startswith("path:"):
            kw = reason.split(":", 1)[1]
            normalized = _normalize_text(kw)
            if normalized:
                terms.add(normalized)
    return terms


def _sample_matches_point(sample: dict, point_terms: set[str]) -> bool:
    """Decide whether a comment/review sample is evidence for a learning point.

    Fast path: if retrieval already tagged matching terms, accept.
    Fallback: scan the sample body for any rule keyword. This covers the
    common case where retrieval vocabulary (prompt + topic terms) doesn't
    include learning-point keywords, which would otherwise reject every
    sample that wasn't coincidentally tagged with a rule keyword.

    Preserves prior behavior: empty matched_terms (path-only retrieval
    match) passes through without body scan, mirroring the original guard.
    """
    if not point_terms:
        return True  # no filter
    raw_matched = sample.get("matched_terms", [])
    matched_terms = {_normalize_text(t) for t in raw_matched if t}
    matched_terms.discard("")
    if not matched_terms:
        return True  # path-only or unfiltered match — preserve old behavior
    if matched_terms & point_terms:
        return True  # fast path
    body = _normalize_text(sample.get("body_excerpt", ""))
    if not body:
        return False
    return any(term in body for term in point_terms)


def _evidence_quotes(candidate: dict, point: dict) -> list[dict]:
    pr_number = candidate.get("pr_number")
    quotes: list[dict] = []
    point_terms = _extract_point_terms(point)

    for sample in candidate.get("matched_comment_samples", []):
        if len(quotes) >= 3:
            break
        if not _sample_matches_point(sample, point_terms):
            continue
        quotes.append(_source_quote("review_comment", pr_number, sample))

    for sample in candidate.get("matched_review_samples", []):
        if len(quotes) >= 3:
            break
        if not _sample_matches_point(sample, point_terms):
            continue
        quotes.append(_source_quote("review_body", pr_number, sample))

    for sample in candidate.get("matched_issue_comment_samples", []):
        if len(quotes) >= 3:
            break
        if not _sample_matches_point(sample, point_terms):
            continue
        quotes.append(_source_quote("issue_comment", pr_number, sample))

    if not quotes and candidate.get("focus_excerpt"):
        quotes.append({
            "source": "pr_body",
            "pr_number": pr_number,
            "path": None,
            "line": None,
            "author": candidate.get("author_login"),
            "excerpt": _clip(candidate.get("focus_excerpt")),
        })
    return quotes


def _has_review_grounding(quotes: list[dict]) -> bool:
    return any(quote.get("source") in {"review_comment", "review_body", "issue_comment"} for quote in quotes)


def _why_learning_point(point: dict, candidate: dict) -> str:
    reasons = point.get("reasons", [])
    if reasons:
        rendered = ", ".join(reasons[:3])
        return f"{candidate.get('title')}은 {rendered} 근거로 {point.get('label')} 학습에 적합하다."
    return f"{candidate.get('title')}은 {point.get('label')}을 살펴보는 데 쓸 수 있는 후보다."


def _profile_boost(rule_id: str, learning_profile: dict | None) -> tuple[int, list[str]]:
    """Return (boost, reasons) for a rule based on the learner memory profile.

    The boost only amplifies rules that already have a positive content
    score — we never fabricate a match out of thin air. Semantics:

    - repeated_learning_points match: +3 (+2 more when recency_status == "active")
    - dominant_learning_points match (not repeated): +2 (+1 when active)
    - underexplored_learning_points match: +1 (surface blind spots gently)
    """
    if not learning_profile:
        return 0, []

    repeated = {
        item.get("learning_point"): item
        for item in (learning_profile.get("repeated_learning_points") or [])
    }
    dominant = {
        item.get("learning_point"): item
        for item in (learning_profile.get("dominant_learning_points") or [])
    }
    underexplored = {
        item.get("learning_point")
        for item in (learning_profile.get("underexplored_learning_points") or [])
    }

    boost = 0
    reasons: list[str] = []
    if rule_id in repeated:
        boost += 3
        reasons.append("profile:repeated")
        if repeated[rule_id].get("recency_status") == "active":
            boost += 2
            reasons.append("profile:active")
    elif rule_id in dominant:
        boost += 2
        reasons.append("profile:dominant")
        if dominant[rule_id].get("recency_status") == "active":
            boost += 1
            reasons.append("profile:active")
    elif rule_id in underexplored:
        boost += 1
        reasons.append("profile:underexplored")
    return boost, reasons


def _score_learning_points(
    candidate: dict,
    learning_profile: dict | None = None,
) -> list[dict]:
    text = _candidate_text(candidate)
    path_text = _candidate_path_text(candidate)
    scores = []
    for rule in LEARNING_POINT_RULES:
        score = 0
        reasons: list[str] = []
        for keyword in rule["keywords"]:
            normalized = _normalize_text(keyword)
            if normalized and normalized in text:
                score += 4
                reasons.append(f"text:{keyword}")
        for keyword in rule["path_keywords"]:
            normalized = _normalize_text(keyword)
            if normalized and normalized in path_text:
                score += 2
                reasons.append(f"path:{keyword}")
        if score <= 0:
            continue
        # Amplify rules that match the learner's accumulated profile so
        # repeated/underexplored points float to the top when content is
        # otherwise tied. This is the single write→read hook for
        # memory/profile.json in candidate interpretation.
        profile_boost, profile_reasons = _profile_boost(rule["id"], learning_profile)
        score += profile_boost
        reasons.extend(profile_reasons)
        scores.append({
            "id": rule["id"],
            "label": rule["label"],
            "description": rule["description"],
            "score": score,
            "reasons": reasons[:8],
        })
    scores.sort(key=lambda item: (-item["score"], item["id"]))
    return scores


def build_candidate_interpretation(
    repo_name: str,
    mode: str,
    focus_payload: dict,
    db_path: str | None = None,
    *,
    learning_profile: dict | None = None,
) -> dict:
    candidate_profiles = []
    for candidate in focus_payload.get("candidates", []):
        learning_points = _score_learning_points(candidate, learning_profile=learning_profile)
        if not learning_points:
            continue
        profile = {
            "pr_number": candidate.get("pr_number"),
            "title": candidate.get("title"),
            "author_login": candidate.get("author_login"),
            "focus_score": candidate.get("score", 0),
            "learning_points": learning_points[:5],
            "richness_score": candidate.get("score", 0) + sum(point["score"] for point in learning_points[:3]),
            "best_evidence": _best_evidence(candidate),
            "matched_paths": candidate.get("matched_paths", [])[:5],
        }
        candidate_profiles.append(profile)

    candidate_profiles.sort(key=lambda item: (-item["richness_score"], -item["focus_score"], item["pr_number"]))

    recommendations = []
    for rule in LEARNING_POINT_RULES:
        matching = []
        for profile in candidate_profiles:
            point = next((item for item in profile["learning_points"] if item["id"] == rule["id"]), None)
            if point is None:
                continue
            candidate = next(
                (item for item in focus_payload.get("candidates", []) if item.get("pr_number") == profile["pr_number"]),
                None,
            )
            if candidate is None:
                continue
            evidence_quotes = _evidence_quotes(candidate, point)
            matching.append({
                "pr_number": profile["pr_number"],
                "title": profile["title"],
                "author_login": profile["author_login"],
                "learning_point_score": point["score"],
                "focus_score": profile["focus_score"],
                "best_evidence": profile["best_evidence"],
                "matched_paths": profile.get("matched_paths", []),
                "reasons": point["reasons"],
                "evidence_quotes": evidence_quotes,
                "why_this_learning_point": _why_learning_point(point, candidate),
                "created_year": candidate.get("created_year"),
                "cohort_caveat": candidate.get("cohort_caveat", False),
                "freshness_note": candidate.get("freshness_note"),
            })
        matching = [item for item in matching if item.get("evidence_quotes")]
        if not matching:
            continue
        matching.sort(key=lambda item: (-item["learning_point_score"], -item["focus_score"], item["pr_number"]))
        grounded = [item for item in matching if _has_review_grounding(item.get("evidence_quotes", []))]
        if not grounded:
            continue
        primary = grounded[0]
        if db_path and primary.get("pr_number"):
            primary["thread_samples"] = build_threads_for_packet(db_path, primary["pr_number"], limit=3)
        alternatives = [item for item in matching if item["pr_number"] != primary["pr_number"]][:3]
        recommendations.append({
            "learning_point": rule["id"],
            "label": rule["label"],
            "description": rule["description"],
            "primary_candidate": primary,
            "alternative_candidates": alternatives,
        })

    payload = {
        "interpretation_type": "candidate_interpretation",
        "repo": repo_name,
        "mode": mode,
        "generated_at": _timestamp(),
        "source_focus_path": focus_payload.get("json_path"),
        "candidate_count": focus_payload.get("candidate_count", 0),
        "shortlist_count": len(focus_payload.get("candidates", [])),
        "candidate_profiles": candidate_profiles[:10],
        "learning_point_recommendations": recommendations[:8],
    }
    validate_payload("candidate-interpretation", payload)
    path = repo_context_dir(repo_name) / f"{mode}-candidate-interpretation.json"
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    payload["json_path"] = str(path)
    return payload
