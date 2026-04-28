from __future__ import annotations

from pathlib import PurePosixPath

TOPIC_RULES = [
    {
        "topic": "Repository",
        "query": "Repository",
        "prompt_keywords": ["repository", "레포지토리", "저장소", "jdbcgamerepository", "boardrepository"],
        "path_keywords": ["repository", "jdbc", "infra"],
    },
    {
        "topic": "DAO",
        "query": "DAO",
        "prompt_keywords": ["dao", "gamedao", "piecedao"],
        "path_keywords": ["dao", "data"],
    },
    {
        "topic": "Transaction",
        "query": "Transaction",
        "prompt_keywords": ["transaction", "rollback", "commit", "connectionfactory", "트랜잭션"],
        "path_keywords": ["transaction", "connection", "database"],
    },
    {
        "topic": "Service",
        "query": "Service",
        "prompt_keywords": ["service", "application", "서비스"],
        "path_keywords": ["service", "application", "usecase"],
    },
    {
        "topic": "Palace",
        "query": "Palace",
        "prompt_keywords": ["palace", "궁성", "cannonpiece", "guardpiece", "generalpiece"],
        "path_keywords": ["palace", "castle", "cannon", "guard", "general"],
    },
    {
        "topic": "Getter",
        "query": "getter",
        "prompt_keywords": ["getter", "getboard", "getname", "getteam"],
        "path_keywords": ["getter"],
    },
    {
        "topic": "DTO",
        "query": "DTO",
        "prompt_keywords": ["dto", "data", "entity"],
        "path_keywords": ["dto", "data", "entity"],
    },
    {
        "topic": "Test",
        "query": "test",
        "prompt_keywords": ["test", "테스트"],
        "path_keywords": ["test"],
    },
    {
        "topic": "Domain",
        "query": "Domain",
        "prompt_keywords": [
            # Korean single-word
            "도메인", "모델", "모델링", "엔티티", "값객체", "객체",
            # Korean multi-word — explicit modeling intent gets Domain priority
            # over single-word ties (especially for entity collision with DTO).
            "도메인 설계", "도메인 객체", "도메인 모델",
            "엔티티 설계", "엔티티 모델링",
            # English single-word
            "domain", "model", "entity", "aggregate",
            # English multi-word — `entity modeling` prompts win Domain (6) over DTO (3).
            "entity modeling", "entity design", "domain modeling", "domain design", "domain object",
        ],
        "path_keywords": ["domain", "model", "entity", "aggregate"],
    },
    {
        "topic": "Controller",
        "query": "Controller",
        "prompt_keywords": [
            "컨트롤러", "엔드포인트", "라우팅", "핸들러",
            "controller", "endpoint", "handler", "routing", "rest",
        ],
        "path_keywords": ["controller", "handler", "endpoint"],
    },
]

INTENT_RULES = [
    {"intent": "review_triage", "keywords": ["리뷰", "다음 액션", "먼저", "우선", "priority", "what next"], "weight": 1},
    {"intent": "concept_explanation", "keywords": ["왜", "무슨 뜻", "설명", "개념", "차이", "difference"], "weight": 2},
    {"intent": "peer_comparison", "keywords": ["다른 크루", "비교", "패턴", "어떻게 했", "compare"], "weight": 2},
    {"intent": "reviewer_lens", "keywords": ["리뷰어", "관점", "reviewer"], "weight": 2},
    {"intent": "implementation_planning", "keywords": ["수정", "반영", "리팩터링", "구조", "설계", "how to change"], "weight": 2},
    {"intent": "testing_strategy", "keywords": ["테스트", "검증", "시나리오", "케이스", "test"], "weight": 3},
    {"intent": "pr_response", "keywords": ["pr 본문", "리뷰 답변", "코멘트 답변", "답변", "reply", "response", "어떻게 답"], "weight": 4},
]


def _path_tokens(diff_files: list[str]) -> tuple[set[str], str]:
    tokens: set[str] = set()
    normalized_paths: list[str] = []
    for path in diff_files:
        normalized = path.lower()
        normalized_paths.append(normalized)
        pieces = (
            normalized.replace("/", " ")
            .replace("-", " ")
            .replace("_", " ")
            .replace(".", " ")
            .split()
        )
        tokens.update(piece for piece in pieces if piece)
        pure_path = PurePosixPath(normalized)
        tokens.update(part for part in pure_path.parts if part)
        stem = pure_path.stem
        if stem:
            tokens.add(stem)
    return tokens, " ".join(normalized_paths)


def _has_test_path(diff_files: list[str]) -> bool:
    for path in diff_files:
        normalized = path.lower()
        if normalized.startswith("src/test/") or normalized.endswith("test.java"):
            return True
    return False


def _mission_map_topic_candidates(mission_map: dict | None) -> list[dict]:
    if not mission_map:
        return []
    analysis = mission_map.get("analysis") or {}
    candidates = []
    for item in analysis.get("likely_review_topics", []):
        topic = item.get("topic")
        query = item.get("query")
        if not topic or not query:
            continue
        candidates.append({
            "topic": topic,
            "query": query,
            "score": int(item.get("score", 0)),
            "reasons": [f"mission-map:{reason}" for reason in item.get("reasons", [])[:5]] or ["mission-map:fallback"],
        })
    return candidates


def infer_topics(prompt: str, diff_files: list[str], mission_map: dict | None = None) -> dict:
    prompt_text = prompt.lower()
    diff_tokens, diff_text = _path_tokens(diff_files)
    scored: list[dict] = []

    for rule in TOPIC_RULES:
        score = 0
        reasons: list[str] = []
        for keyword in rule.get("prompt_keywords", []):
            if keyword in prompt_text:
                score += 3
                reasons.append(f"prompt:{keyword}")
        for keyword in rule.get("path_keywords", []):
            if keyword in diff_tokens:
                score += 4
                reasons.append(f"path-token:{keyword}")
            elif keyword in diff_text:
                score += 2
                reasons.append(f"path-fragment:{keyword}")
        if rule["topic"] == "Test" and _has_test_path(diff_files):
            score += 5
            reasons.append("path:test-signal")
        if score > 0:
            scored.append({
                "topic": rule["topic"],
                "query": rule["query"],
                "score": score,
                "reasons": reasons,
            })

    mission_candidates = _mission_map_topic_candidates(mission_map)
    if mission_candidates:
        if scored:
            existing_topics = {item["topic"] for item in scored}
            for candidate in mission_candidates:
                if candidate["topic"] in existing_topics:
                    continue
                scored.append({
                    **candidate,
                    "score": 1,
                    "reasons": ["mission-map:fallback"] + candidate.get("reasons", [])[:3],
                })
        else:
            # Prompt-silent: cap mission-map fallback so a single weak signal
            # cannot outscore a real prompt-side match (3 per keyword).
            for candidate in mission_candidates:
                capped = min(int(candidate.get("score", 0)), 2)
                scored.append({
                    **candidate,
                    "score": capped,
                    "reasons": ["mission-map:weak-fallback"] + candidate.get("reasons", [])[:3],
                })

    if not scored:
        return {
            "primary_topic": "Repository",
            "primary_query": "Repository",
            "suggested_topics": ["Repository"],
            "inference_reasons": ["default: no prompt/diff match"],
            "topic_candidates": [
                {
                    "topic": "Repository",
                    "query": "Repository",
                    "score": 0,
                    "reasons": ["default: no prompt/diff match"],
                }
            ],
            "confidence": "low",
        }

    scored.sort(key=lambda item: (-item["score"], item["topic"]))
    top_score = scored[0]["score"]
    if top_score >= 6:
        confidence = "high"
    elif top_score >= 3:
        confidence = "medium"
    else:
        confidence = "low"
    return {
        "primary_topic": scored[0]["topic"],
        "primary_query": scored[0]["query"],
        "suggested_topics": [item["topic"] for item in scored[:3]],
        "inference_reasons": scored[0]["reasons"],
        "topic_candidates": scored[:5],
        "confidence": confidence,
    }


def infer_intent(prompt: str, reviewer: str | None = None) -> dict:
    prompt_text = prompt.lower()
    scored: list[dict] = []

    for rule in INTENT_RULES:
        score = 0
        reasons: list[str] = []
        for keyword in rule["keywords"]:
            if keyword in prompt_text:
                score += rule.get("weight", 1)
                reasons.append(f"prompt:{keyword}")
        if reviewer and rule["intent"] == "reviewer_lens":
            score += 2
            reasons.append("input:reviewer")
        if score > 0:
            scored.append({
                "intent": rule["intent"],
                "score": score,
                "reasons": reasons,
            })

    if not scored:
        return {
            "primary_intent": "review_triage",
            "suggested_intents": ["review_triage"],
            "intent_reasons": ["default: no prompt match"],
            "intent_candidates": [
                {
                    "intent": "review_triage",
                    "score": 0,
                    "reasons": ["default: no prompt match"],
                }
            ],
        }

    scored.sort(key=lambda item: (-item["score"], item["intent"]))
    return {
        "primary_intent": scored[0]["intent"],
        "suggested_intents": [item["intent"] for item in scored[:3]],
        "intent_reasons": scored[0]["reasons"],
        "intent_candidates": scored[:5],
    }
