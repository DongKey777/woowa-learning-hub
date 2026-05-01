"""Single source of truth for router/intent token vocabularies (plan §P5.1).

Pre-consolidation, the token sets lived in three places:

- ``interactive_rag_router.py`` — DEFINITION_SIGNALS, DEPTH_SIGNALS,
  CS_DOMAIN_TOKENS, LEARNING_CONCEPT_TOKENS, COACH_REQUEST_TOKENS,
  TOOL_TOKENS, OVERRIDE_TOKENS, BEGINNER_HINTS, ADVANCED_HINTS
- ``intent_tokens.py`` — MISSION_TOKENS, CS_TOKENS,
  DRILL_ANSWER_NEGATIVE_KEYWORDS

Adding one Korean word forced editing both files (sometimes 3, with
``signal_rules.py``). This module is now the **only** place to add a
token. The router modules ``import`` from here and re-export under
their existing names for backwards compatibility.

## Match strategy

Each set is paired with a documented match strategy. Two helpers are
exposed here:

``match_word_boundary(prompt, tokens)``
    For sets where a token like ``"di"`` must not match ``"di가"``
    embedded in Korean text. ASCII-only word boundary via lookaround
    (Python's ``\\b`` is unicode and treats Hangul as a word
    character — wrong for our purposes). Non-ASCII tokens fall back
    to ``casefold`` substring (Korean tokens are vetted to be ≥ 2
    chars and distinctive).

``match_substring(prompt, tokens)``
    For sets where the haystack is already lowercased and tokens are
    multi-character Korean phrases or distinctive English n-grams.
    Used by ``intent_router`` two-stage classification.

Sets are tagged with a ``match_strategy`` constant so a future
linter can enforce that consumers pick the right helper. The tag is
informational — the data is just frozensets.

## Versioning

Frozensets, not regular sets — read-only and the immutability makes
accidental mutation impossible.
"""

from __future__ import annotations

import re
from typing import Iterable

# ---------------------------------------------------------------------------
# Match strategy tags (informational — see module docstring)
# ---------------------------------------------------------------------------

WORD_BOUNDARY = "word_boundary"   # use match_word_boundary()
SUBSTRING = "substring"           # use match_substring()


# ---------------------------------------------------------------------------
# Override tokens — highest priority (short-circuits classification)
# Match strategy: word_boundary
# ---------------------------------------------------------------------------

OVERRIDE_TOKENS: dict[str, list[str]] = {
    "force_coach": ["코치 모드", "coach mode"],                          # → Tier 3 attempt
    "force_full":  ["RAG로 깊게", "심도 있게", "depth", "full RAG"],     # → Tier 2
    "force_min1":  ["RAG로 답해", "근거 보여줘", "with RAG"],            # → at least Tier 1
    "force_skip":  ["그냥 답해", "RAG 빼고", "skip RAG"],                # → Tier 0
}


# ---------------------------------------------------------------------------
# Tier 1 — definition signals (learner asking what something is)
# Match strategy: word_boundary
# ---------------------------------------------------------------------------

DEFINITION_SIGNALS: frozenset[str] = frozenset([
    # Korean (≥2 chars; "란" 1-char excluded to avoid "이란" / "한란" noise)
    "뭐야", "뭐예요", "뭐임", "뭐냐", "머야", "머냐",
    "알려줘", "설명해", "정의가", "정의는", "이란", "이라고",
    # "어떤" / "무슨" + 명사 — definitional intent
    "어떤거야", "어떤 거야", "어떤 건가",
    "어떤 의미", "무슨 의미",
    "어떤 역할", "무슨 역할",
    "어떤 개념", "무슨 개념",
    # English (word boundary applied)
    "what is", "what's", "define", "definition of", "explain briefly",
])


# ---------------------------------------------------------------------------
# Tier 2 — depth/comparison signals
# Match strategy: word_boundary
# ---------------------------------------------------------------------------

DEPTH_SIGNALS: frozenset[str] = frozenset([
    # Korean
    "vs", "차이", "비교", "왜 필요", "왜 써", "왜 사용", "왜 쓰",
    "어떻게 동작", "어떻게 작동", "어떻게 돼", "어떻게 처리",
    "방법", "해결 방법", "원리", "내부 구조", "트레이드오프",
    # 비교 표현
    "뭐가 다른", "뭐가 달라", "어떻게 달라",
    # 사용 시점 묻기
    "언제 쓰는", "언제 써", "언제 붙이는", "언제 사용",
    # English
    "vs.", "difference between", "why use", "why does", "how does",
    "trade-off", "tradeoff", "under the hood",
])


# ---------------------------------------------------------------------------
# CS domain tokens — concrete concept terms (≥2 Korean chars)
# Match strategy: word_boundary
# ---------------------------------------------------------------------------

CS_DOMAIN_TOKENS: frozenset[str] = frozenset([
    # Korean (1-char "락" excluded — collides with "연락"/"호락호락")
    "트랜잭션", "격리수준", "정규화", "인덱스", "캐시", "동기화", "비동기",
    "재시도", "타임아웃", "아키텍처", "데드락", "교착", "쓰레드",
    "스레드", "병행성", "동시성", "락(", "잠금",
    "큐", "스택", "트리", "그래프", "해시", "힙", "연결리스트",
    "예외", "예외처리",
    # 인프라 / 서버 (학습자가 "웹서버와 WAS 차이" 같은 질문할 때 자주 등장)
    "웹서버", "웹 서버", "애플리케이션 서버",
    "톰캣", "서블릿", "리버스 프록시",
    "네트워크", "지연", "대역폭", "처리량",
    # English
    "transaction", "isolation", "normalization", "index", "cache",
    "deadlock", "thread", "concurrency", "synchronization",
    "throttle", "timeout", "architecture",
    "queue", "stack", "tree", "graph", "hash", "heap", "linked list",
    "exception", "exception handling",
    # Infrastructure / servers
    "web server", "application server", "was",
    "tomcat", "nginx", "apache", "servlet", "reverse proxy",
    # Network/protocol performance terms frequently asked in mixed Korean.
    "network", "latency", "bandwidth", "throughput", "rtt",
    "ttfb", "ttlb", "dns", "tcp", "tls", "http",
])


# ---------------------------------------------------------------------------
# Learning concept tokens (Tier 1+ trigger)
# Match strategy: word_boundary
# ---------------------------------------------------------------------------

LEARNING_CONCEPT_TOKENS: frozenset[str] = frozenset([
    # Spring core/web
    "spring", "bean", "di", "ioc", "aop", "autowired", "component", "applicationcontext",
    "controller", "service", "repository", "restcontroller", "dispatcherservlet",
    "filter", "interceptor",
    # DI 방식별 phrase
    "constructor injection", "setter injection", "field injection",
    "생성자 주입", "세터 주입", "필드 주입",
    # Spring concept 한글 phrase
    "컴포넌트 스캔", "컴포넌트스캔", "의존성 주입", "어노테이션",
    # Spring core annotations / proxy
    "configuration", "@configuration", "@bean", "프록시", "횡단 관심사",
    "rest controller", "@restcontroller",
    # Persistence
    "jpa", "hibernate", "jdbc", "jdbctemplate", "entity", "dto", "vo",
    "transactional", "savepoint", "mvcc",
    # Java basics (covers woowa level-2 learning tests)
    "java", "interface", "abstract", "static", "final", "generic",
    "collection", "stream", "lambda", "optional", "enum",
    "record", "sealed",
    # Java collection concrete classes
    "list", "set", "map", "hashmap", "linkedhashmap", "treemap",
    "arraylist", "linkedlist", "hashset", "treeset",
    # Patterns
    "service locator", "factory", "singleton", "observer", "strategy",
    "adapter", "decorator", "proxy", "template method",
    # Architecture
    "layered architecture", "hexagonal", "ddd", "cqrs",
    # Network/protocol
    "rest", "graphql", "websocket", "tls",
    # Security
    "oauth", "jwt", "csrf", "xss",
    # Algorithms / DS
    "big-o", "binary search", "dfs", "bfs", "dynamic programming",
])


# ---------------------------------------------------------------------------
# Tier 3 — coaching request tokens (multi-word strong patterns)
# Match strategy: word_boundary
# ---------------------------------------------------------------------------

COACH_REQUEST_TOKENS: frozenset[str] = frozenset([
    # Korean (multi-word; bare "리뷰"/"PR"/"리뷰어가" too broad)
    "내 pr", "내 PR", "내 코드 리뷰", "내 미션", "내 풀리퀘",
    "pr 리뷰", "PR 리뷰", "pr 코칭", "PR 코칭",
    "리뷰어 코멘트", "리뷰어가 남긴", "리뷰어 피드백",
    "리뷰 응답", "리뷰 답변", "스레드 해결", "unresolved 리뷰",
    # English
    "my pr", "my pull request", "review my", "reviewer comment",
    "unresolved review", "review thread",
])


# ---------------------------------------------------------------------------
# Tool tokens (Tier 0)
# Match strategy: word_boundary
# ---------------------------------------------------------------------------

TOOL_TOKENS: frozenset[str] = frozenset([
    "gradle", "maven", "sbt", "build.gradle", "settings.gradle", "pom.xml",
    "intellij", "vscode", "eclipse", "ide",
    "git", "rebase", "merge conflict", "git commit", "git branch",
    "npm", "yarn", "pip", "conda", "brew",
    "terminal", "shell", "bash", "zsh", "path 설정",
])


# ---------------------------------------------------------------------------
# Experience level inference
# Match strategy: word_boundary
# ---------------------------------------------------------------------------

BEGINNER_HINTS: frozenset[str] = frozenset([
    "처음 배우는데", "처음 보는데", "왜 필요해요", "기초", "입문",
    "뭐야", "뭐예요", "어떻게 시작",
    "beginner", "intro", "first time",
])

ADVANCED_HINTS: frozenset[str] = frozenset([
    "edge case", "trade-off", "internals", "under the hood",
    "MVCC", "WAL", "CAS", "두 번째 단계", "심화",
])


# ---------------------------------------------------------------------------
# Two-stage intent routing tokens (substring match on lowercased haystack)
# Match strategy: substring
# ---------------------------------------------------------------------------

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
    # Code identifiers
    "synchronized", "volatile", "override", "interface", "abstract",
    "extends", "implements", "final", "static", "generic",
})

DRILL_ANSWER_NEGATIVE_KEYWORDS: frozenset[str] = frozenset({
    # Korean — presence of these → prompt is asking, not answering
    "뭐야", "어떻게", "왜", "알려줘", "설명해", "차이", "무엇",
    # English
    "what", "why", "how", "explain", "which", "when", "where",
})


# ---------------------------------------------------------------------------
# Match helpers — both strategies in one place so consumers don't have
# to copy ASCII-vs-Korean reasoning.
# ---------------------------------------------------------------------------

def _is_ascii(token: str) -> bool:
    return all(ord(c) < 128 for c in token)


def match_word_boundary_one(prompt: str, token: str) -> bool:
    """True iff ``token`` matches ``prompt`` with the word-boundary
    contract: ASCII tokens use a non-Hangul-aware lookaround, Korean
    tokens use casefold substring (token vocabularies are vetted to
    avoid 1-char Korean tokens that would false-positive)."""
    if _is_ascii(token):
        pattern = rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])"
        return bool(re.search(pattern, prompt, re.IGNORECASE))
    return token.casefold() in prompt.casefold()


def match_word_boundary(prompt: str, tokens: Iterable[str]) -> bool:
    """Return True if any token in ``tokens`` matches ``prompt``
    under the word-boundary contract."""
    return any(match_word_boundary_one(prompt, t) for t in tokens)


def match_substring(prompt: str, tokens: Iterable[str]) -> bool:
    """Return True if any token in ``tokens`` matches ``prompt`` as a
    plain substring on the lowercased haystack."""
    haystack = (prompt or "").lower()
    return any(t in haystack for t in tokens)


def count_substring_hits(prompt: str, tokens: Iterable[str]) -> int:
    """Substring strategy hit count. Used by intent_router two-stage
    classification (mission vs CS scoring)."""
    haystack = (prompt or "").lower()
    return sum(1 for t in tokens if t in haystack)


# ---------------------------------------------------------------------------
# __all__ — explicit public surface (so a `from .lexicon import *`
# in a future consolidator pulls a known list)
# ---------------------------------------------------------------------------

__all__ = [
    # Match strategy tags
    "WORD_BOUNDARY", "SUBSTRING",
    # Token sets — word boundary
    "OVERRIDE_TOKENS",
    "DEFINITION_SIGNALS", "DEPTH_SIGNALS",
    "CS_DOMAIN_TOKENS", "LEARNING_CONCEPT_TOKENS",
    "COACH_REQUEST_TOKENS", "TOOL_TOKENS",
    "BEGINNER_HINTS", "ADVANCED_HINTS",
    # Token sets — substring
    "MISSION_TOKENS", "CS_TOKENS", "DRILL_ANSWER_NEGATIVE_KEYWORDS",
    # Helpers
    "match_word_boundary_one", "match_word_boundary",
    "match_substring", "count_substring_hits",
]
