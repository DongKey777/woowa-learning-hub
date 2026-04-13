"""4-dimension answer scoring for drill / CS responses.

Dimensions (max raw points):
- accuracy     : 0..4  — 핵심 용어/사실/인과관계의 정확성
- depth        : 0..3  — 개념 간 연결, trade-off, 내부 동작 설명
- practicality : 0..2  — 실제 코드·운영·경계 상황에 대한 적용
- completeness : 0..1  — 질문에 대한 응답의 결락 없는 커버리지

Total: 0..10 → level L1..L5.

Pure stdlib. Korean + English markers mixed in the same tables so
answers in either language map to the same dimension score.

Use via ``score_answer(question, answer, *, category=None,
expected_terms=None)``. ``expected_terms`` is optional additional
accuracy vocabulary derived from the source CS document when the drill
engine knows what the correct answer should contain.
"""

from __future__ import annotations

import re
from typing import Any

_TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣_]+")


# ---------------------------------------------------------------------------
# Marker tables
# ---------------------------------------------------------------------------

DEPTH_MARKERS: tuple[str, ...] = (
    # Korean
    "왜냐하면", "이유는", "원리", "내부적으로", "반면", "대신",
    "trade-off", "트레이드오프", "비교하면", "차이점", "근본적으로",
    "보장", "불변식", "invariant",
    # English
    "because", "whereas", "internally", "under the hood", "fundamentally",
    "tradeoff", "in contrast",
)

PRACTICAL_MARKERS: tuple[str, ...] = (
    # Korean
    "예를 들면", "실제로", "운영", "장애", "배포", "롤백", "성능",
    "테스트", "검증", "경계 조건", "엣지 케이스", "타임아웃", "재시도",
    "모니터링", "로그",
    # English
    "for example", "in practice", "production", "incident", "rollback",
    "edge case", "timeout", "retry", "monitoring", "benchmark",
)

COMPLETENESS_PENALTIES: tuple[str, ...] = (
    "잘 모르", "모르겠", "패스", "pass", "skip",
)

DIMENSION_LABELS = {
    "accuracy": "정확도",
    "depth": "깊이",
    "practicality": "실전성",
    "completeness": "완결성",
}

IMPROVEMENT_TEMPLATES = {
    "accuracy": "핵심 용어를 한 번 더 확인하고 답에 명시적으로 써보세요.",
    "depth": "왜 그런지/내부 원리를 한 문장 더 풀어서 설명하면 깊이가 올라갑니다.",
    "practicality": "실제 코드나 운영 상황(타임아웃·재시도·롤백 등)에 어떻게 적용되는지 예를 하나 덧붙여 보세요.",
    "completeness": "질문에서 빠뜨린 하위 항목이 없는지 체크하고 남은 축도 마저 답해 보세요.",
}

WEAK_THRESHOLDS = {
    "accuracy": 3,
    "depth": 2,
    "practicality": 1,
    "completeness": 1,
}

LEVEL_TABLE = (
    (9, "L5"),
    (7, "L4"),
    (5, "L3"),
    (3, "L2"),
    (0, "L1"),
)


def _tokenize(text: str) -> list[str]:
    return [m.lower() for m in _TOKEN_RE.findall(text or "")]


def _count_hits(haystack: str, markers: tuple[str, ...]) -> int:
    return sum(1 for m in markers if m in haystack)


def _score_accuracy(answer_tokens: set[str], expected_terms: list[str]) -> int:
    if not expected_terms:
        # No ground-truth vocab — use a soft heuristic: answer with ≥ 8
        # distinct tokens gets 2; ≥ 16 gets 3; question-word answers get 0-1.
        n = len(answer_tokens)
        if n >= 24:
            return 4
        if n >= 16:
            return 3
        if n >= 8:
            return 2
        if n >= 3:
            return 1
        return 0
    hits = sum(1 for t in expected_terms if t.lower() in answer_tokens)
    coverage = hits / max(len(expected_terms), 1)
    if coverage >= 0.8:
        return 4
    if coverage >= 0.6:
        return 3
    if coverage >= 0.4:
        return 2
    if coverage >= 0.2:
        return 1
    return 0


def _score_depth(answer: str) -> int:
    hits = _count_hits(answer, DEPTH_MARKERS)
    if hits >= 3:
        return 3
    if hits == 2:
        return 2
    if hits == 1:
        return 1
    return 0


def _score_practicality(answer: str) -> int:
    hits = _count_hits(answer, PRACTICAL_MARKERS)
    if hits >= 2:
        return 2
    if hits == 1:
        return 1
    return 0


def _score_completeness(answer: str) -> int:
    lower = answer.lower()
    if any(p in lower for p in COMPLETENESS_PENALTIES):
        return 0
    if len(answer.strip()) >= 40:
        return 1
    return 0


def _level_for(total: int) -> str:
    for threshold, label in LEVEL_TABLE:
        if total >= threshold:
            return label
    return "L1"


def _weak_tags(dimensions: dict[str, int]) -> list[str]:
    out: list[str] = []
    for dim, threshold in WEAK_THRESHOLDS.items():
        if dimensions.get(dim, 0) < threshold:
            out.append(DIMENSION_LABELS[dim])
    return out


def _improvement_notes(dimensions: dict[str, int]) -> list[str]:
    notes: list[str] = []
    for dim, threshold in WEAK_THRESHOLDS.items():
        if dimensions.get(dim, 0) < threshold:
            notes.append(IMPROVEMENT_TEMPLATES[dim])
    return notes


def score_answer(
    question: str,
    answer: str,
    *,
    category: str | None = None,
    expected_terms: list[str] | None = None,
) -> dict[str, Any]:
    """Score an answer on 4 dimensions.

    Returns::

        {
            "dimensions": {"accuracy": int, "depth": int, "practicality": int, "completeness": int},
            "total_score": int,            # 0..10
            "level": "L1".."L5",
            "weak_tags": [...],
            "improvement_notes": [...],
            "category": str | None,
        }
    """
    body = answer or ""
    tokens = set(_tokenize(body))
    dimensions = {
        "accuracy": _score_accuracy(tokens, expected_terms or []),
        "depth": _score_depth(body),
        "practicality": _score_practicality(body),
        "completeness": _score_completeness(body),
    }
    total = sum(dimensions.values())
    return {
        "dimensions": dimensions,
        "total_score": total,
        "level": _level_for(total),
        "weak_tags": _weak_tags(dimensions),
        "improvement_notes": _improvement_notes(dimensions),
        "category": category,
    }
