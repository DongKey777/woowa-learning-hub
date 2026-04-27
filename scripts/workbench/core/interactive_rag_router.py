"""Tier-based RAG router for interactive learning sessions.

Classifies a learner prompt into one of 4 tiers (0/1/2/3) so the AI session
can route the turn to the right RAG entry point:

- Tier 0: skip RAG (tooling/build/IDE/git/OS questions)
- Tier 1: cheap augment (FTS only, ~50-200ms) — definition lookups
- Tier 2: full augment (FTS + dense + rerank, ~500ms-2s warm) — comparison/depth
- Tier 3: bin/coach-run (full pipeline) — PR coaching with onboarded repo

Replaces the prior "AI remembers to use RAG every turn" runtime convention
that proved unreliable. Codifies the routing as a pure function with tests.

Token matching:
- ASCII tokens use ASCII-only lookaround word boundary (Python's `\\b` is
  Unicode word boundary, which fails for tokens immediately followed by
  Hangul, e.g. `\\bdi\\b` does NOT match "DI가").
- Korean (or mixed Korean+ASCII) tokens use casefold() substring match.

False-positive guard: Tier 1/2 require BOTH a domain match (CS_DOMAIN_TOKENS
or LEARNING_CONCEPT_TOKENS) AND a signal match (DEFINITION_SIGNALS or
DEPTH_SIGNALS). Signal-only prompts like "오늘 점심 왜 없어?" stay Tier 0.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RouterDecision:
    """Output of `classify()`. Consumed by `bin/rag-ask` (or any caller)
    to decide whether to invoke augment(), coach-run, or nothing."""

    tier: int                           # 0, 1, 2, 3
    mode: str | None                    # None | "cheap" | "full" | "coach-run"
    reason: str                         # one-line explanation for header
    experience_level: str | None        # "beginner" | None
    override_active: bool               # True if a user override matched
    blocked: bool = False               # True when tier=3 but preconditions unmet
    promoted_by_profile: bool = False   # v3: tier was raised because the
                                        # learner has asked about this concept
                                        # before (closed-loop signal)


# === 1. Definition signals (Tier 1 trigger — ANDed with domain) ===
DEFINITION_SIGNALS = frozenset([
    # Korean (≥2 chars; "란" 1-char excluded to avoid "이란" / "한란" noise)
    "뭐야", "뭐예요", "알려줘", "설명해", "정의가", "정의는", "이란", "이라고",
    # English (word boundary applied)
    "what is", "what's", "define", "definition of", "explain briefly",
])

# === 2. Depth/comparison signals (Tier 2 trigger — ANDed with domain) ===
DEPTH_SIGNALS = frozenset([
    # Korean
    "vs", "차이", "비교", "왜 필요", "왜 써", "왜 사용", "왜 쓰",
    "어떻게 동작", "어떻게 작동", "어떻게 돼", "어떻게 처리",
    "방법", "해결 방법", "원리", "내부 구조", "트레이드오프",
    # English
    "vs.", "difference between", "why use", "why does", "how does",
    "trade-off", "tradeoff", "under the hood",
])

# === 3. CS domain tokens (concrete concept terms — ≥2 Korean chars) ===
CS_DOMAIN_TOKENS = frozenset([
    # Korean (1-char "락" excluded — collides with "연락"/"호락호락")
    "트랜잭션", "격리수준", "정규화", "인덱스", "캐시", "동기화", "비동기",
    "재시도", "타임아웃", "아키텍처", "데드락", "교착", "쓰레드",
    "스레드", "병행성", "동시성", "락(", "잠금",
    "큐", "스택", "트리", "그래프", "해시", "힙", "연결리스트",
    "예외", "예외처리",
    # English
    "transaction", "isolation", "normalization", "index", "cache",
    "deadlock", "thread", "concurrency", "synchronization",
    "throttle", "timeout", "architecture",
    "queue", "stack", "tree", "graph", "hash", "heap", "linked list",
    "exception", "exception handling",
])

# === 4. Learning concept tokens (Spring/JPA + Java basics + DS — woowa context) ===
LEARNING_CONCEPT_TOKENS = frozenset([
    # Spring core/web
    "spring", "bean", "di", "ioc", "autowired", "component", "applicationcontext",
    "controller", "service", "repository", "restcontroller", "dispatcherservlet",
    "filter", "interceptor",
    # Persistence
    "jpa", "hibernate", "jdbc", "jdbctemplate", "entity", "dto", "vo",
    "transactional", "savepoint", "mvcc",
    # Java basics (covers woowa level-2 learning tests)
    "java", "interface", "abstract", "static", "final", "generic",
    "collection", "stream", "lambda", "optional", "enum",
    "record", "sealed",
    # Java collection concrete classes (HashMap, ArrayList etc — common questions)
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

# === 5. Coaching request tokens (Tier 3 — multi-word strong patterns) ===
COACH_REQUEST_TOKENS = frozenset([
    # Korean (multi-word; bare "리뷰"/"PR"/"리뷰어가" too broad)
    "내 pr", "내 PR", "내 코드 리뷰", "내 미션", "내 풀리퀘",
    "pr 리뷰", "PR 리뷰", "pr 코칭", "PR 코칭",
    "리뷰어 코멘트", "리뷰어가 남긴", "리뷰어 피드백",
    "리뷰 응답", "리뷰 답변", "스레드 해결", "unresolved 리뷰",
    # English
    "my pr", "my pull request", "review my", "reviewer comment",
    "unresolved review", "review thread",
])

# === 6. Tool tokens (Tier 0) ===
TOOL_TOKENS = frozenset([
    "gradle", "maven", "sbt", "build.gradle", "settings.gradle", "pom.xml",
    "intellij", "vscode", "eclipse", "ide",
    "git", "rebase", "merge conflict", "git commit", "git branch",
    "npm", "yarn", "pip", "conda", "brew",
    "terminal", "shell", "bash", "zsh", "path 설정",
])


# === Override tokens (highest priority — short-circuits classification) ===
# Order: stronger intent first. First match wins.
OVERRIDE_TOKENS: dict[str, list[str]] = {
    "force_coach": ["코치 모드", "coach mode"],                          # → Tier 3 attempt
    "force_full":  ["RAG로 깊게", "심도 있게", "depth", "full RAG"],     # → Tier 2
    "force_min1":  ["RAG로 답해", "근거 보여줘", "with RAG"],            # → at least Tier 1
    "force_skip":  ["그냥 답해", "RAG 빼고", "skip RAG"],                # → Tier 0
}


# === Experience level inference ===
BEGINNER_HINTS = frozenset([
    "처음 배우는데", "처음 보는데", "왜 필요해요", "기초", "입문",
    "뭐야", "뭐예요", "어떻게 시작",
    "beginner", "intro", "first time",
])
ADVANCED_HINTS = frozenset([
    "edge case", "trade-off", "internals", "under the hood",
    "MVCC", "WAL", "CAS", "두 번째 단계", "심화",
])


def _match_token(prompt: str, token: str) -> bool:
    """Return True iff `token` matches `prompt`.

    ASCII tokens: ASCII-only lookaround word boundary + escape + IGNORECASE.
        Python's `\\b` is unicode word boundary, which fails for `\\bdi\\b`
        against "DI가" (Hangul is a word character in unicode). The lookaround
        forces the boundary to be a non-ASCII-alnum/underscore character or
        start/end of string.

    Non-ASCII tokens: casefold() substring match. Korean tokens are multi-char
        and distinctive enough that substring is safe (1-char Korean tokens
        like "락" are excluded from the vocabularies above).
    """
    is_ascii = all(ord(c) < 128 for c in token)
    if is_ascii:
        pattern = rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])"
        return bool(re.search(pattern, prompt, re.IGNORECASE))
    return token.casefold() in prompt.casefold()


def _any_match(prompt: str, tokens) -> bool:
    return any(_match_token(prompt, t) for t in tokens)


def infer_experience_level(prompt: str) -> str | None:
    """Infer learner level from prompt phrasing.

    Returns "beginner" if any BEGINNER_HINT matches.
    Returns None for advanced/unclear prompts (no boost — advanced corpus
    dominates retrieval anyway).
    """
    if _any_match(prompt, BEGINNER_HINTS):
        return "beginner"
    return None


def _check_override(prompt: str) -> str | None:
    """Return override key if any OVERRIDE_TOKENS match, else None."""
    for key, tokens in OVERRIDE_TOKENS.items():
        if _any_match(prompt, tokens):
            return key
    return None


def _missing_tier3_preconditions(repo_context: dict | None) -> list[str]:
    """Return list of missing preconditions for Tier 3."""
    missing: list[str] = []
    if not repo_context:
        return ["repo_context"]
    if not repo_context.get("repo_name"):
        missing.append("repo_name")
    if not repo_context.get("archive_ready"):
        missing.append("archive_ready")
    if not repo_context.get("has_open_pr"):
        missing.append("has_open_pr")
    return missing


def classify(
    prompt: str,
    *,
    repo_context: dict | None = None,
    learner_profile: dict | None = None,
) -> RouterDecision:
    """Classify a learning-session prompt into Tier 0~3.

    repo_context shape (all optional fields):
        {"repo_name": str, "archive_ready": bool, "has_open_pr": bool}

    `learner_profile` (v3) is the persisted learner profile loaded by
    `bin/rag-ask`. When passed, three closed-loop rules apply (in order):

      1. Rolling experience_level (`high` confidence) overrides the
         prompt-only `BEGINNER_HINTS` lookup — a learner who has been
         flagged beginner across 20 turns shouldn't lose that just because
         this single prompt sounds advanced.
      2. Repeated uncertain concept (≥3 asks in 7d) promotes a Tier 1
         "domain + definition" hit to Tier 2 with `promoted_by_profile=True`.
         Stops the "the learner asked Bean five times and we keep giving
         the same shallow answer" failure mode.
      3. Cold start: when profile is None or has < 3 events, the router
         falls back to the v2.2 prompt-only behavior.

    Router still does NOT do disk/network I/O itself — `learner_profile`
    must be loaded by the caller.
    """
    profile_level = _profile_experience_level(learner_profile)
    inferred_level = infer_experience_level(prompt)
    level = profile_level or inferred_level

    # --- Stage 1: override short-circuit ---
    override = _check_override(prompt)
    if override == "force_skip":
        return RouterDecision(
            tier=0, mode=None, reason="user override: skip RAG",
            experience_level=level, override_active=True,
        )
    if override == "force_coach":
        missing = _missing_tier3_preconditions(repo_context)
        if missing:
            return RouterDecision(
                tier=3, mode=None,
                reason=f"user override coach mode but tier3_blocked: missing={missing}",
                experience_level=level, override_active=True, blocked=True,
            )
        return RouterDecision(
            tier=3, mode="coach-run", reason="user override: coach mode",
            experience_level=level, override_active=True,
        )
    if override == "force_full":
        return RouterDecision(
            tier=2, mode="full", reason="user override: full RAG",
            experience_level=level, override_active=True,
        )
    if override == "force_min1":
        # Promote to Tier 2 if depth signal present, else Tier 1
        domain = _any_match(prompt, CS_DOMAIN_TOKENS) or _any_match(prompt, LEARNING_CONCEPT_TOKENS)
        if domain and _any_match(prompt, DEPTH_SIGNALS):
            return RouterDecision(
                tier=2, mode="full", reason="user override: with RAG (depth signal)",
                experience_level=level, override_active=True,
            )
        return RouterDecision(
            tier=1, mode="cheap", reason="user override: with RAG",
            experience_level=level, override_active=True,
        )

    # --- Stage 2: detect signals/domains ---
    has_coach_req = _any_match(prompt, COACH_REQUEST_TOKENS)
    has_tool = _any_match(prompt, TOOL_TOKENS)
    has_cs_domain = _any_match(prompt, CS_DOMAIN_TOKENS)
    has_learning = _any_match(prompt, LEARNING_CONCEPT_TOKENS)
    has_domain = has_cs_domain or has_learning
    has_definition = _any_match(prompt, DEFINITION_SIGNALS)
    has_depth = _any_match(prompt, DEPTH_SIGNALS)

    # --- Stage 3: Tier 3 (PR coaching) ---
    if has_coach_req:
        missing = _missing_tier3_preconditions(repo_context)
        if missing:
            return RouterDecision(
                tier=3, mode=None,
                reason=f"tier3_blocked: missing={missing}",
                experience_level=level, override_active=False, blocked=True,
            )
        return RouterDecision(
            tier=3, mode="coach-run",
            reason="coach request matched, repo+PR ready",
            experience_level=level, override_active=False,
        )

    # --- Stage 4: Tier 0 (tool questions without CS domain) ---
    if has_tool and not has_domain:
        return RouterDecision(
            tier=0, mode=None, reason="tool/build question, no CS domain",
            experience_level=level, override_active=False,
        )

    # --- Stage 5: Tier 2 (depth + domain) ---
    if has_domain and has_depth:
        return RouterDecision(
            tier=2, mode="full", reason="domain + depth signal",
            experience_level=level, override_active=False,
        )

    # --- Stage 6: Tier 1 (definition + domain) ---
    if has_domain and has_definition:
        # v3 closed-loop: if the learner has been asking about a concept
        # mentioned here ≥3 times in the last 7 days (uncertain), promote
        # to Tier 2 so the answer goes deeper.
        if _profile_concept_repeated(learner_profile, prompt):
            return RouterDecision(
                tier=2, mode="full",
                reason="domain + definition signal · profile uncertain (repeated 7d)",
                experience_level=level, override_active=False,
                promoted_by_profile=True,
            )
        return RouterDecision(
            tier=1, mode="cheap", reason="domain + definition signal",
            experience_level=level, override_active=False,
        )

    # --- Stage 7: default = Tier 0 (no learning-domain signal) ---
    return RouterDecision(
        tier=0, mode=None, reason="no learning-domain signal",
        experience_level=level, override_active=False,
    )


# === v3 profile helpers (cold-start safe) ================================
def _profile_experience_level(profile: dict | None) -> str | None:
    """Return the rolling experience level if confidence is high enough."""
    if not profile:
        return None
    exp = profile.get("experience_level") or {}
    if exp.get("confidence") in ("high", "medium") and exp.get("current") == "beginner":
        return "beginner"
    return None


def _profile_concept_repeated(profile: dict | None, prompt: str) -> bool:
    """True iff ANY uncertain concept_id matches this prompt and the
    profile has enough events to trust the signal (cold-start: <3 events
    falls through to v2.2 behavior)."""
    if not profile:
        return False
    if (profile.get("total_events") or 0) < 3:
        return False
    uncertain = (profile.get("concepts") or {}).get("uncertain") or []
    if not uncertain:
        return False
    try:
        from .concept_catalog import (  # local import to avoid bootstrap cycles
            extract_concept_ids,
            load_catalog,
        )
        catalog = load_catalog()
    except Exception:  # noqa: BLE001 — router stays usable without catalog
        return False
    prompt_concepts = set(extract_concept_ids(prompt, catalog))
    if not prompt_concepts:
        return False
    uncertain_ids = {entry.get("concept_id") for entry in uncertain}
    return bool(prompt_concepts & uncertain_ids)
