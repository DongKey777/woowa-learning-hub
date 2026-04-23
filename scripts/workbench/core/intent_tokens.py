"""Single-source token vocabularies for intent routing.

Pre-PR#4, these constants lived inside ``intent_router.py`` and a parallel
copy of ``DRILL_ANSWER_NEGATIVE_KEYWORDS`` lived inside ``scripts/learning/
drill.py``. This module owns the live constants so future updates land in
exactly one place.

Frozensets, not regular sets — these are read-only and the immutability
makes accidental mutation impossible.
"""

from __future__ import annotations

MISSION_TOKENS: frozenset[str] = frozenset({
    # Korean
    "pr", "리뷰", "리뷰어", "스레드", "코멘트", "브랜치", "커밋", "해결",
    "답변", "답글", "내 pr", "내꺼", "내 코드", "내 미션", "미션",
    # English
    "pull request", "review", "reviewer", "thread", "unresolved",
    "branch", "commit", "feedback", "comment",
})

CS_TOKENS: frozenset[str] = frozenset({
    # Korean
    "개념", "이론", "원리", "차이", "왜", "무엇", "정의", "설명해",
    "알려줘", "격리", "트랜잭션", "정규화", "인덱스", "캐시", "락",
    "쓰레드", "동기화", "재시도", "타임아웃", "아키텍처", "패턴",
    # English
    "concept", "theory", "definition", "difference between", "explain",
    "what is", "why does", "how does",
    # Code identifiers — learners often paste a mixed Korean + code snippet
    # question. Keeping the list to language-agnostic keywords that clearly
    # signal a concept question.
    "synchronized", "volatile", "override", "interface", "abstract",
    "extends", "implements", "final", "static", "generic",
})

# 11-keyword canonical set (was 7 in drill.py, 11 in intent_router pre-PR#4).
# The intent_router copy was dead, so this consolidates onto the longer set
# and adopts which/when/where so English question phrasings route correctly.
DRILL_ANSWER_NEGATIVE_KEYWORDS: frozenset[str] = frozenset({
    # Korean — presence of these → prompt is asking, not answering
    "뭐야", "어떻게", "왜", "알려줘", "설명해", "차이", "무엇",
    # English
    "what", "why", "how", "explain", "which", "when", "where",
})
