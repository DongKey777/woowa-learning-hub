"""Signal rules — prompt/topic → query expansion tokens.

Each rule: trigger token set → expansion tokens + canonical signal tag
(used as the fallback-bucket key when no peer learning-point matches).

Signal tags are stable identifiers the rest of the pipeline can switch on.
The 11 rules cover the recurring Woowa mission review axes.
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Rule table
# ---------------------------------------------------------------------------

Rule = dict  # {"tag": str, "triggers": set[str], "expand": list[str], "category": str}

_RULES: list[Rule] = [
    {
        "tag": "persistence_boundary",
        "triggers": {"repository", "dao", "aggregate", "레포지토리", "영속성", "persistence"},
        "expand": [
            "repository",
            "repository pattern",
            "dao pattern",
            "persistence",
            "aggregate root",
        ],
        "category": "database",
    },
    {
        "tag": "transaction_isolation",
        "triggers": {"transaction", "트랜잭션", "rollback", "commit", "isolation", "격리"},
        "expand": ["transaction", "isolation level", "lock", "rollback"],
        "category": "database",
    },
    {
        "tag": "db_modeling",
        "triggers": {"schema", "스키마", "정규화", "normalization", "table", "index", "인덱스"},
        "expand": ["schema design", "normalization", "index", "primary key"],
        "category": "database",
    },
    {
        "tag": "layer_responsibility",
        "triggers": {"책임", "경계", "계층", "controller", "service", "layer", "관심사"},
        "expand": ["layered architecture", "separation of concerns", "service layer"],
        "category": "design-pattern",
    },
    {
        "tag": "api_boundary",
        "triggers": {"api", "rest", "endpoint", "controller", "dto", "요청", "응답"},
        "expand": ["rest api", "dto", "controller", "request validation"],
        "category": "network",
    },
    {
        "tag": "collections_and_domain",
        "triggers": {"list", "map", "collection", "컬렉션", "iterator", "stream", "도메인"},
        "expand": ["collection", "domain model", "value object"],
        "category": "design-pattern",
    },
    {
        "tag": "network_and_reliability",
        "triggers": {"timeout", "retry", "circuit", "network", "네트워크", "http", "latency"},
        "expand": ["timeout", "retry", "circuit breaker", "reliability"],
        "category": "network",
    },
    {
        "tag": "security_authentication",
        "triggers": {"jwt", "token", "auth", "인증", "oauth", "password", "csrf", "xss"},
        "expand": ["authentication", "authorization", "jwt", "session"],
        "category": "security",
    },
    {
        "tag": "testing_strategy",
        "triggers": {"test", "테스트", "fixture", "mock", "integration", "unit test"},
        "expand": ["unit test", "integration test", "fixture", "test double"],
        "category": "software-engineering",
    },
    {
        "tag": "resource_lifecycle",
        "triggers": {"connection pool", "close", "resource", "pool", "leak", "lifecycle"},
        "expand": ["connection pool", "resource lifecycle", "leak", "close"],
        "category": "operating-system",
    },
    {
        "tag": "concurrency",
        "triggers": {"thread", "동시성", "concurrency", "lock", "race", "atomic", "synchronized"},
        "expand": ["concurrency", "lock", "race condition", "atomic"],
        "category": "operating-system",
    },
]

_TOKEN_RE = re.compile(r"[0-9a-zA-Z가-힣]+")
# Strip a trailing Korean-particle run from ASCII-prefixed tokens like
# "boundary와" / "repository가" so the FTS side queries the bare stem the
# index actually stores. Pure-Hangul tokens are left untouched (stripping
# particles from them risks mangling legitimate stems).
_MIXED_TAIL_RE = re.compile(r"^([0-9A-Za-z]+)[가-힣]+$")


def _tokenize(text: str) -> list[str]:
    if not text:
        return []
    out: list[str] = []
    for tok in _TOKEN_RE.findall(text):
        if not tok:
            continue
        m = _MIXED_TAIL_RE.match(tok)
        if m:
            tok = m.group(1)
        out.append(tok.lower())
    return out


def _haystack(prompt: str, topic_hints: list[str] | None) -> str:
    parts = [prompt or ""]
    parts.extend(topic_hints or [])
    return " ".join(parts).lower()


def _count_trigger_hits(haystack: str, triggers: set[str]) -> int:
    """Count how many triggers appear in the haystack as substrings.

    Substring match handles Korean-particle-attached English words
    (`Repository가` still contains `repository`) and multi-word triggers
    like `connection pool`.
    """
    return sum(1 for trig in triggers if trig in haystack)


def detect_signals(prompt: str, topic_hints: list[str] | None = None) -> list[dict]:
    """Return matched rules with expansion tokens, ranked by trigger overlap.

    Output item shape: {"tag", "category", "expand", "score"}.
    """
    haystack = _haystack(prompt, topic_hints)
    hits: list[dict] = []
    for rule in _RULES:
        score = _count_trigger_hits(haystack, rule["triggers"])
        if score == 0:
            continue
        hits.append(
            {
                "tag": rule["tag"],
                "category": rule["category"],
                "expand": list(rule["expand"]),
                "score": score,
            }
        )
    hits.sort(key=lambda h: (-h["score"], h["tag"]))
    return hits


def expand_query(prompt: str, topic_hints: list[str] | None = None) -> list[str]:
    """Produce augmented query tokens (original + rule expansions)."""
    base = _tokenize(prompt)
    for hint in topic_hints or []:
        base.extend(_tokenize(hint))
    for signal in detect_signals(prompt, topic_hints):
        base.extend(signal["expand"])
    # de-dupe while preserving order
    seen: set[str] = set()
    out: list[str] = []
    for tok in base:
        key = tok.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(tok)
    return out


def top_signal_tag(prompt: str, topic_hints: list[str] | None = None) -> str | None:
    """Return the highest-scoring signal tag, or None."""
    signals = detect_signals(prompt, topic_hints)
    return signals[0]["tag"] if signals else None
