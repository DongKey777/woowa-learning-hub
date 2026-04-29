"""Hybrid CS RAG searcher.

Pipeline
--------
1. Expand query via signal_rules.expand_query (original + rule expansions).
2. FTS5 MATCH to get top-N candidates (score = bm25, lower is better).
3. Dense cosine similarity top-N (skipped in ``cheap`` mode).
4. Reciprocal Rank Fusion (RRF, k=60) to merge the two rankings.
5. Category boost for learning-point ↔ CS category pairs.
6. Signal boost and signal-routed path injection — when the router identifies
   a precise concept family, keep its canonical/companion docs in the candidate
   pool even if corpus growth pushed them just below the raw FTS+dense cut.
7. Category filter — when learning_points are set, restrict the pool to the
   mapped categories so the reranker never sees off-topic noise (e.g. an
   auth doc winning a persistence query on surface-token overlap). If the
   filter would leave fewer than top_k items, fall back to unfiltered.
8. Optional cross-encoder rerank (skipped in ``cheap`` mode, env-disabled
   in tests via WOOWA_RAG_NO_RERANK=1).
9. Document-level dedupe — keep the best-scoring chunk per source path so
   a single document's sibling sections cannot monopolize top-K.
10. Return top-K dicts ready for cs_block rendering.

Modes
-----
- ``cheap``: FTS only + category boost. No ML deps loaded. Used by
  intent_router when pre_intent == "drill_answer" or for tests.
- ``full``: FTS + dense + RRF + (optional) rerank.

Contracts
---------
- ``search()`` returns a list of dicts with deterministic ordering.
- Lazy-imports numpy / sentence-transformers only when needed.
- Never raises on empty corpus — returns [].
"""

from __future__ import annotations

import math
import os
import re
import sqlite3
from pathlib import Path
from typing import Iterable

from . import category_mapping, indexer, signal_rules

RRF_K = 60
DEFAULT_TOP_K = 5
FTS_POOL_SIZE = 80
DENSE_POOL_SIZE = 80
CATEGORY_BOOST = 0.15  # added to final score when category matches a learning point
SIGNAL_CATEGORY_BOOST = 0.0015
POST_RERANK_SIGNAL_BOOST_MULTIPLIER = 1000.0

# Difficulty boost ladder — applied as a tie-breaker inside the top pool only,
# so it never promotes an unrelated doc into the candidate set. Experience
# levels other than beginner/intermediate keep the legacy zero-boost behavior
# to guarantee zero diff against existing golden fixtures.
#
# Magnitudes are intentionally an order of magnitude smaller than CATEGORY_BOOST
# (0.15) so a clearly-more-relevant advanced doc still beats a marginally
# relevant beginner doc, while ties are broken in favor of the learner level.
DIFFICULTY_BOOST_LADDER: dict[str | None, dict[str | None, float]] = {
    "beginner": {
        "beginner": 0.04,
        "intermediate": 0.02,
        "advanced": 0.0,
        "expert": -0.01,
        None: 0.0,
    },
    "intermediate": {
        "beginner": 0.01,
        "intermediate": 0.03,
        "advanced": 0.01,
        "expert": 0.0,
        None: 0.0,
    },
}

# Small, deterministic boosts for signal families whose beginner primer should
# survive cheap-mode FTS ties. Values stay far below CATEGORY_BOOST so explicit
# learner-state category mappings remain dominant.
SIGNAL_CATEGORY_BOOST_TAGS = {
    "java_oop_basics",
    "transaction_anomaly_patterns",
}

SIGNAL_PATH_BOOSTS: dict[str, dict[str, float]] = {
    "java_oop_basics": {
        "contents/language/java/object-oriented-core-principles.md": 0.004,
    },
    "transaction_anomaly_patterns": {
        "contents/database/read-committed-vs-repeatable-read-anomalies.md": 0.008,
        "contents/database/transaction-isolation-locking.md": 0.003,
    },
    "java_completablefuture_fan_in_timeout": {
        "contents/language/java/completablefuture-allof-join-timeout-exception-handling-hazards.md": 0.014,
        "contents/language/java/completablefuture-execution-model-common-pool-pitfalls.md": 0.003,
        "contents/language/java/completablefuture-cancellation-semantics.md": 0.003,
    },
    "storage_contract_evolution": {
        "contents/database/cdc-schema-evolution-compatibility-playbook.md": 0.014,
        "contents/database/destructive-schema-cleanup-column-retirement.md": 0.008,
        "contents/database/schema-migration-partitioning-cdc-cqrs.md": 0.006,
    },
}


# ---------------------------------------------------------------------------
# FTS query sanitization
# ---------------------------------------------------------------------------

_FTS_TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣]+")


def _to_fts_query(tokens: Iterable[str]) -> str:
    """Build a defensive FTS5 MATCH string from free tokens.

    Each token is quoted so punctuation cannot break the parser, and the
    tokens are OR-joined.
    """
    quoted: list[str] = []
    seen: set[str] = set()
    for tok in tokens:
        # extract only matchable segments; drop stray chars
        for piece in _FTS_TOKEN_RE.findall(tok):
            key = piece.lower()
            if len(key) < 2 or key in seen:
                continue
            seen.add(key)
            quoted.append(f'"{piece}"')
    return " OR ".join(quoted)


# ---------------------------------------------------------------------------
# FTS search
# ---------------------------------------------------------------------------

def _fts_search(
    conn: sqlite3.Connection,
    fts_query: str,
    limit: int,
) -> list[tuple[int, float]]:
    """Return ``[(row_id, bm25_score)]``. Lower score = better match."""
    if not fts_query:
        return []
    try:
        cur = conn.execute(
            """
            SELECT chunks_fts.rowid, bm25(chunks_fts)
            FROM chunks_fts
            WHERE chunks_fts MATCH ?
            ORDER BY bm25(chunks_fts)
            LIMIT ?
            """,
            (fts_query, limit),
        )
    except sqlite3.OperationalError:
        return []
    return [(row[0], row[1]) for row in cur.fetchall()]


def _first_chunk_ids_for_paths(conn: sqlite3.Connection, paths: Iterable[str]) -> list[int]:
    """Return one stable representative chunk per path.

    Signal routing is path-level. The golden contract cares whether the right
    document is visible, not which internal chunk won. Pulling one chunk per
    boosted path keeps companion docs eligible after corpus expansion without
    letting a single routed document flood the rerank pool.
    """
    path_list = sorted({path for path in paths if path})
    if not path_list:
        return []

    placeholders = ",".join("?" for _ in path_list)
    rows = conn.execute(
        f"""
        SELECT id, path
        FROM chunks
        WHERE path IN ({placeholders})
        ORDER BY path, id
        """,
        path_list,
    ).fetchall()

    seen: set[str] = set()
    row_ids: list[int] = []
    for row_id, path in rows:
        if path in seen:
            continue
        seen.add(path)
        row_ids.append(int(row_id))
    return row_ids


# ---------------------------------------------------------------------------
# Dense search (lazy)
# ---------------------------------------------------------------------------

_QUERY_EMBEDDER = None  # module-level cache to avoid reloading per query


def _get_query_embedder():
    global _QUERY_EMBEDDER
    if _QUERY_EMBEDDER is not None:
        return _QUERY_EMBEDDER
    from sentence_transformers import SentenceTransformer  # type: ignore

    _QUERY_EMBEDDER = SentenceTransformer(indexer.EMBED_MODEL)
    return _QUERY_EMBEDDER


def _load_query_vector(prompt: str, topic_hints: list[str] | None):
    import numpy as np  # type: ignore

    model = _get_query_embedder()
    text = prompt
    if topic_hints:
        text = f"{prompt}\n\n" + "\n".join(topic_hints)
    vec = model.encode(
        [text],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )
    return np.asarray(vec[0], dtype="float32")


def _dense_search(
    index_root: Path | str,
    prompt: str,
    topic_hints: list[str] | None,
    limit: int,
) -> list[tuple[int, float]]:
    """Return ``[(row_id, similarity)]`` where similarity is in [-1, 1]."""
    try:
        import numpy as np  # type: ignore
    except ImportError:
        return []
    try:
        embeddings, row_ids = indexer.load_dense(index_root)
    except (FileNotFoundError, OSError):
        return []
    try:
        qvec = _load_query_vector(prompt, topic_hints)
    except Exception:
        return []
    if embeddings.shape[0] == 0:
        return []
    sims = embeddings @ qvec  # (N,)
    top = np.argsort(-sims)[:limit]
    return [(int(row_ids[i]), float(sims[i])) for i in top]


# ---------------------------------------------------------------------------
# Reciprocal Rank Fusion
# ---------------------------------------------------------------------------

def _rrf_merge(
    rankings: list[list[tuple[int, float]]],
    k: int = RRF_K,
) -> list[tuple[int, float]]:
    """Merge multiple (row_id, score) rankings into a single fused ranking.

    RRF formula: score_rrf(d) = Σ 1 / (k + rank(d in list_i))
    """
    fused: dict[int, float] = {}
    for ranking in rankings:
        for rank, (row_id, _) in enumerate(ranking, start=1):
            fused[row_id] = fused.get(row_id, 0.0) + 1.0 / (k + rank)
    return sorted(fused.items(), key=lambda t: (-t[1], t[0]))


# ---------------------------------------------------------------------------
# Category boost
# ---------------------------------------------------------------------------

def _apply_category_boost(
    scored: list[tuple[int, float]],
    chunks: dict[int, dict],
    allowed_categories: set[str],
) -> list[tuple[int, float]]:
    if not allowed_categories:
        return scored
    boosted: list[tuple[int, float]] = []
    for row_id, score in scored:
        chunk = chunks.get(row_id)
        if chunk and chunk["category"] in allowed_categories:
            score = score + CATEGORY_BOOST
        boosted.append((row_id, score))
    boosted.sort(key=lambda t: (-t[1], t[0]))
    return boosted


def _apply_difficulty_boost(
    scored: list[tuple[int, float]],
    chunks: dict[int, dict],
    experience_level: str | None,
) -> list[tuple[int, float]]:
    """Re-rank the existing pool toward the learner's level.

    No-op when ``experience_level`` is None or not in the ladder (advanced /
    expert learners keep legacy ranking exactly). Applied after category
    boost so the discovery set is unchanged — purely a tie-breaker on the
    candidates that already passed FTS+dense+category filtering.
    """
    if not experience_level:
        return scored
    ladder = DIFFICULTY_BOOST_LADDER.get(experience_level)
    if ladder is None:
        return scored
    boosted: list[tuple[int, float]] = []
    for row_id, score in scored:
        chunk = chunks.get(row_id)
        delta = ladder.get((chunk or {}).get("difficulty"), 0.0) if chunk else 0.0
        boosted.append((row_id, score + delta))
    boosted.sort(key=lambda t: (-t[1], t[0]))
    return boosted


def _contains_any(haystack: str, cues: set[str]) -> bool:
    return any(cue in haystack for cue in cues)


def _projection_path_boosts(haystack: str, signal_tags: set[str]) -> dict[str, float]:
    if "projection_freshness" not in signal_tags:
        return {}
    if _contains_any(haystack, {"캐시인지", "리플리카", "cache vs replica", "replica lag"}):
        return {
            "contents/database/replica-lag-read-after-write-strategies.md": 0.014,
            "contents/database/read-your-writes-session-pinning.md": 0.006,
            "contents/database/cache-replica-split-read-inconsistency.md": 0.004,
        }
    if not _contains_any(
        haystack,
        {
            "처음",
            "입문",
            "beginner",
            "read model",
            "읽기 모델",
            "projection",
            "투영",
            "stale read",
            "read-your-writes",
            "strict read",
            "session pinning",
            "expected version",
            "watermark",
            "cutover",
            "guardrail",
            "전환 안전",
            "컷오버",
            "컷 오버",
            "왜",
            "이전 화면",
            "예전 화면",
            "화면",
            "목록",
            "리스트",
            "새로고침",
            "업데이트 지연",
            "안 바뀜",
            "옛값만",
            "방금 쓴 값",
            "안 보임",
        },
    ):
        return {
            "contents/database/replica-lag-read-after-write-strategies.md": 0.014,
            "contents/database/read-your-writes-session-pinning.md": 0.004,
        }
    if _contains_any(
        haystack,
        {
            "failover",
            "visibility",
            "verification",
            "write loss",
            "stateful",
            "replica",
            "리플리카",
            "캐시인지",
            "cache invalidation",
            "application cache",
        },
    ) and not _contains_any(
        haystack,
        {
            "처음",
            "입문",
            "beginner",
            "read model",
            "읽기 모델",
            "projection",
            "투영",
            "stale read",
            "read-your-writes",
            "저장 직후",
            "예전 값",
            "옛값",
            "cutover",
            "guardrail",
            "전환 안전",
            "컷오버",
            "컷 오버",
        },
    ):
        return {}
    if _contains_any(haystack, {"transaction rollback", "트랜잭션 롤백"}) and not _contains_any(
        haystack,
        {
            "read model",
            "읽기 모델",
            "stale read",
            "read-your-writes",
            "저장",
            "예전 값",
            "옛값",
        },
    ):
        return {}
    if _contains_any(haystack, {"projection rebuild", "backfill", "watermark"}) and not _contains_any(
        haystack,
        {
            "처음",
            "입문",
            "먼저",
            "stale read",
            "read-your-writes",
            "예전 값",
            "옛값",
            "strict read",
            "session pinning",
            "watermark gated",
        },
    ):
        return {}

    if _contains_any(
        haystack,
        {"slo tuning", "freshness sli", "lag breach policy", "consumer backlog", "exception budget"},
    ):
        return {
            "contents/design-pattern/projection-freshness-slo-pattern.md": 0.020,
            "contents/design-pattern/projection-lag-budgeting-pattern.md": 0.014,
            "contents/design-pattern/read-model-staleness-read-your-writes.md": 0.002,
        }

    boosts = {
        "contents/design-pattern/read-model-staleness-read-your-writes.md": 0.025,
    }
    if _contains_any(
        haystack,
        {
            "strict read",
            "session pinning",
            "세션 피닝",
            "세션 고정",
            "expected version",
            "watermark gated",
            "watermark gate",
            "version gated",
        },
    ):
        boosts.update(
            {
                "contents/design-pattern/session-pinning-vs-version-gated-strict-reads.md": 0.040,
                "contents/design-pattern/strict-read-fallback-contracts.md": 0.020,
            }
        )
    if _contains_any(haystack, {"cqrs", "survey", "설문"}) and not _contains_any(
        haystack,
        {
            "말고",
            "not",
            "rejection",
            "broad cqrs",
            "전체 survey",
            "전체 개요",
        },
    ):
        boosts["contents/database/schema-migration-partitioning-cdc-cqrs.md"] = 0.0015
    if _contains_any(
        haystack,
        {
            "브라우저 필터",
            "정렬 상태",
            "query condition",
            "filter state",
            "sort state",
        },
    ):
        return {}
    if _contains_any(
        haystack,
        {
            "목록 새로고침",
            "이전 화면 상태",
            "목록은 그대로",
            "목록이 바로 안 바뀌",
            "상세는 바뀌었는데",
            "list refresh lag",
            "old screen state",
            "detail view updated",
            "list stale",
        },
    ):
        boosts["contents/design-pattern/projection-lag-budgeting-pattern.md"] = 0.014
        boosts["contents/design-pattern/repository-boundary-aggregate-vs-read-model.md"] = 0.006
    if _contains_any(
        haystack,
        {
            "slo",
            "lag budget",
            "freshness budget",
            "서비스 수준",
            "허용 범위",
            "반영 지연",
        },
    ):
        boosts.update(
            {
                "contents/design-pattern/projection-freshness-slo-pattern.md": 0.008,
                "contents/design-pattern/projection-lag-budgeting-pattern.md": 0.008,
            }
        )
        return boosts

    boosts["contents/design-pattern/read-model-cutover-guardrails.md"] = max(
        boosts.get("contents/design-pattern/read-model-cutover-guardrails.md", 0.0),
        0.007,
    )
    boosts["contents/design-pattern/projection-lag-budgeting-pattern.md"] = max(
        boosts.get("contents/design-pattern/projection-lag-budgeting-pattern.md", 0.0),
        0.005,
    )
    if "rebuild" in haystack or "backfill" in haystack:
        boosts["contents/design-pattern/projection-rebuild-backfill-cutover-pattern.md"] = 0.005
    return boosts


def _stateful_failover_path_boosts(haystack: str, signal_tags: set[str]) -> dict[str, float]:
    if "stateful_failover_placement" not in signal_tags and not _contains_any(
        haystack,
        {
            "stateful failover placement",
            "stateful workload",
            "leader placement",
            "상태 있는 서비스",
            "어느 노드를 리더",
            "어느 노드를 리더로 둘지",
        },
    ):
        return {}
    if not _contains_any(
        haystack,
        {
            "상태 저장",
            "리더 배치",
            "배치 예산",
            "복제본을 올릴지",
            "stateful workload placement",
            "stateful failover placement",
            "leader placement",
            "어느 노드를 리더로 둘지",
            "placement budget",
        },
    ):
        return {}
    return {
        "contents/system-design/stateful-workload-placement-failover-control-plane-design.md": 0.020,
        "contents/system-design/global-traffic-failover-control-plane-design.md": 0.002,
    }


def _query_model_filter_sort_path_boosts(haystack: str) -> dict[str, float]:
    if not _contains_any(
        haystack,
        {
            "브라우저 필터",
            "정렬 상태",
            "query condition",
            "filter state",
            "sort state",
        },
    ):
        return {}
    return {
        "contents/software-engineering/query-model-separation-read-heavy-apis.md": 0.024,
        "contents/design-pattern/read-model-staleness-read-your-writes.md": 0.002,
    }


def _query_model_beginner_entrypoint_path_boosts(haystack: str) -> dict[str, float]:
    if not _contains_any(haystack, {"query model", "query service", "쿼리 모델", "쿼리 서비스"}):
        return {}
    if not _contains_any(
        haystack,
        {
            "처음",
            "입문",
            "큰 그림",
            "뭐야",
            "뭐예요",
            "왜",
            "무슨 역할",
            "what is",
            "meaning",
            "role",
            "beginner",
            "basics",
        },
    ):
        return {}
    return {
        "contents/software-engineering/dao-vs-query-model-entrypoint-primer.md": 0.035,
    }


def _transaction_path_boosts(haystack: str, signal_tags: set[str]) -> dict[str, float]:
    if "projection_freshness" in signal_tags:
        return {}
    if "transaction_isolation" not in signal_tags and "transaction_anomaly_patterns" not in signal_tags:
        return {}
    if _contains_any(
        haystack,
        {
            "@transactional",
            "service layer",
            "self invocation",
            "remote call",
            "controller/repository",
        },
    ):
        return {}
    if _contains_any(
        haystack,
        {
            "locking strategy",
            "optimistic pessimistic",
            "for update",
            "어떻게 같이 정해",
            "strategy",
        },
    ):
        return {}
    if not _contains_any(
        haystack,
        {
            "mvcc",
            "phantom read",
            "dirty read",
            "non-repeatable read",
            "왜 생기",
            "처음",
            "입문",
            "primer",
            "큰 그림",
        },
    ):
        return {}
    if _contains_any(
        haystack,
        {
            "뭐야",
            "뭐예요",
            "뭔데",
            "what is",
            "basics",
            "기초",
            "개념",
        },
    ) and not _contains_any(haystack, {"phantom read", "dirty read", "non-repeatable read"}):
        return {
            "contents/database/transaction-isolation-basics.md": 0.012,
            "contents/database/transaction-isolation-locking.md": 0.003,
            "contents/database/read-committed-vs-repeatable-read-anomalies.md": 0.004,
        }
    if _contains_any(haystack, {"이상 현상", "anomaly"}) and "incident" not in haystack:
        return {
            "contents/database/read-committed-vs-repeatable-read-anomalies.md": 0.020,
            "contents/database/transaction-isolation-locking.md": 0.006,
            "contents/database/transaction-isolation-basics.md": 0.004,
        }
    return {
        "contents/database/transaction-isolation-locking.md": 0.060,
        "contents/database/read-committed-vs-repeatable-read-anomalies.md": 0.004,
        "contents/database/transaction-isolation-basics.md": 0.004,
    }


def _spring_framework_path_boosts(haystack: str, signal_tags: set[str]) -> dict[str, float]:
    if "spring_framework" not in signal_tags:
        return {}
    if _contains_any(haystack, {"dispatcher servlet", "dispatcherservlet"}):
        return {
            "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md": 0.030,
            "contents/spring/spring-mvc-request-lifecycle-basics.md": 0.006,
            "contents/spring/spring-dispatcherservlet-handlerinterceptor-beginner-bridge.md": 0.006,
        }
    if _contains_any(haystack, {"spring mvc", "spring m v c", "스프링 mvc", "스프링 m v c"}):
        return {
            "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md": 0.012,
            "contents/spring/spring-mvc-request-lifecycle-basics.md": 0.006,
            "contents/spring/spring-dispatcherservlet-handlerinterceptor-beginner-bridge.md": 0.004,
        }
    if _contains_any(haystack, {"component scan", "component scanning", "@componentscan", "컴포넌트 스캔"}):
        return {
            "contents/spring/spring-bean-di-basics.md": 0.012,
            "contents/spring/spring-component-scan-failure-patterns.md": 0.005,
            "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md": 0.004,
        }
    if _contains_any(
        haystack,
        {
            "spring bean",
            "beanfactory",
            "bean factory",
            "applicationcontext",
            "application context",
            "빈이",
            "빈은",
        },
    ):
        return {
            "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md": 0.012,
            "contents/spring/spring-bean-di-basics.md": 0.006,
            "contents/spring/spring-bean-definition-overriding-semantics.md": 0.004,
        }
    if _contains_any(
        haystack,
        {"service layer", "controller/repository", "self invocation", "remote call"},
    ):
        return {
            "contents/spring/spring-service-layer-transaction-boundary-patterns.md": 0.020,
            "contents/spring/spring-transactional-basics.md": 0.004,
            "contents/spring/spring-transaction-propagation-deep-dive.md": 0.004,
        }
    if "propagation" in haystack:
        return {
            "contents/spring/spring-transaction-propagation-deep-dive.md": 0.018,
            "contents/spring/spring-transactional-basics.md": 0.004,
        }
    if _contains_any(haystack, {"스프링 트랜잭션이 뭐야", "spring transaction meaning"}):
        return {
            "contents/spring/spring-transactional-basics.md": 0.030,
            "contents/spring/spring-transaction-propagation-deep-dive.md": 0.004,
        }
    if _contains_any(haystack, {"@transactional", "transactional"}):
        return {
            "contents/spring/spring-transactional-basics.md": 0.014,
            "contents/spring/spring-transaction-propagation-deep-dive.md": 0.006,
            "contents/spring/spring-transactional-self-invocation-test-bridge-primer.md": 0.002,
        }
    if _contains_any(
        haystack,
        {
            "di vs ioc",
            "di와 ioc",
            "dependency injection",
            "의존성 주입",
            "inversion of control",
            "제어 역전",
            "제어의 역전",
            "ioc",
        },
    ):
        return {
            "contents/spring/spring-ioc-di-basics.md": 0.014,
            "contents/software-engineering/dependency-injection-basics.md": 0.006,
            "contents/spring/ioc-di-container.md": 0.004,
        }
    if _contains_any(haystack, {"aop", "관점 지향", "횡단 관심사"}) and _contains_any(
        haystack,
        {
            "뭐야",
            "뭐예요",
            "뭔데",
            "what is",
            "why use",
            "왜 써",
            "왜 사용",
            "basics",
            "기초",
            "입문",
            "처음",
        },
    ):
        return {
            "contents/spring/spring-aop-basics.md": 0.008,
            "contents/spring/aop-proxy-mechanism.md": 0.004,
        }
    return {}


def _strict_read_path_boosts(haystack: str) -> dict[str, float]:
    if not _contains_any(haystack, {"strict read", "strict reads"}):
        return {}
    if _contains_any(
        haystack,
        {"session pinning", "expected version", "version gated", "watermark gate", "watermark gated"},
    ):
        return {
            "contents/design-pattern/session-pinning-vs-version-gated-strict-reads.md": 0.018,
            "contents/design-pattern/strict-read-fallback-contracts.md": 0.006,
            "contents/design-pattern/read-model-cutover-guardrails.md": 0.004,
        }
    if _contains_any(haystack, {"fallback contract", "fallback policy", "degraded read"}):
        return {
            "contents/design-pattern/strict-read-fallback-contracts.md": 0.018,
            "contents/design-pattern/session-pinning-vs-version-gated-strict-reads.md": 0.006,
            "contents/design-pattern/read-model-cutover-guardrails.md": 0.004,
        }
    return {}


def _java_concurrency_path_boosts(haystack: str, signal_tags: set[str]) -> dict[str, float]:
    if "java_concurrency_utilities" not in signal_tags:
        return {}
    if "future" not in haystack or "completablefuture" not in haystack:
        return {}
    if _contains_any(
        haystack,
        {
            "allof",
            "anyof",
            "join",
            "ortimeout",
            "completeontimeout",
            "cancellation",
            "cancel",
        },
    ):
        return {}
    if not _contains_any(
        haystack,
        {"처음", "입문", "beginner", "overview", "큰 그림", "짧게", "deep dive 말고"},
    ):
        return {}
    return {
        "contents/language/java/java-concurrency-utilities.md": 0.012,
        "contents/language/java/completablefuture-execution-model-common-pool-pitfalls.md": 0.002,
    }


def _di_ioc_path_boosts(haystack: str) -> dict[str, float]:
    if not _contains_any(
        haystack,
        {
            "di vs ioc",
            "di와 ioc",
            "dependency injection",
            "의존성 주입",
            "inversion of control",
            "제어 역전",
            "제어의 역전",
        },
    ):
        return {}
    return {
        "contents/spring/spring-ioc-di-basics.md": 0.014,
        "contents/software-engineering/dependency-injection-basics.md": 0.006,
        "contents/spring/ioc-di-container.md": 0.004,
    }


def _mvcc_path_boosts(haystack: str) -> dict[str, float]:
    if "mvcc" not in haystack:
        return {}
    if _contains_any(haystack, {"phantom read", "dirty read", "non-repeatable read", "isolation"}):
        return {
            "contents/database/transaction-isolation-locking.md": 0.014,
            "contents/database/read-committed-vs-repeatable-read-anomalies.md": 0.006,
            "contents/database/mvcc-read-view-consistent-read-internals.md": 0.004,
        }
    if not _contains_any(haystack, {"read view", "내부", "internals", "구현"}):
        return {
            "contents/database/transaction-isolation-basics.md": 0.014,
            "contents/database/transaction-isolation-locking.md": 0.006,
            "contents/database/mvcc-read-view-consistent-read-internals.md": 0.004,
        }
    return {
        "contents/database/transaction-isolation-locking.md": 0.014,
        "contents/database/mvcc-read-view-consistent-read-internals.md": 0.006,
        "contents/database/read-committed-vs-repeatable-read-anomalies.md": 0.004,
    }


def _transaction_rollback_contrast_path_boosts(haystack: str) -> dict[str, float]:
    if not _contains_any(haystack, {"rollback window", "롤백 윈도우"}):
        return {}
    if not _contains_any(haystack, {"transaction rollback", "트랜잭션 롤백"}):
        return {}
    if not _contains_any(
        haystack,
        {"read model", "읽기 모델", "projection", "투영", "stale read", "read-your-writes", "예전 값", "방금"},
    ):
        return {
            "contents/database/transaction-isolation-locking.md": 0.020,
            "contents/database/transaction-boundary-isolation-locking-decision-framework.md": 0.010,
        }
    return {
        "contents/database/transaction-isolation-locking.md": 0.003,
        "contents/database/transaction-boundary-isolation-locking-decision-framework.md": 0.001,
    }


def _api_schema_evolution_path_boosts(haystack: str) -> dict[str, float]:
    if _contains_any(haystack, {"event upcaster", "upcaster", "upcast chain"}):
        return {
            "contents/design-pattern/event-upcaster-compatibility-patterns.md": 0.016,
            "contents/software-engineering/event-schema-versioning-compatibility.md": 0.004,
        }
    if _contains_any(haystack, {"cdc", "connector", "storage contract"}):
        return {}
    if "cross-service schema evolution" in haystack:
        return {
            "contents/software-engineering/schema-contract-evolution-cross-service.md": 0.018,
            "contents/software-engineering/api-versioning-contract-testing-anti-corruption-layer.md": 0.004,
            "contents/software-engineering/event-schema-versioning-compatibility.md": 0.002,
        }
    if not _contains_any(
        haystack,
        {
            "api versioning",
            "rest api",
            "api schema evolution",
            "cross-service schema evolution",
            "compatibility layer",
        },
    ):
        return {}
    return {
        "contents/software-engineering/api-versioning-contract-testing-anti-corruption-layer.md": 0.012,
        "contents/software-engineering/schema-contract-evolution-cross-service.md": 0.010,
        "contents/software-engineering/event-schema-versioning-compatibility.md": 0.002,
    }


def _db_modeling_path_boosts(haystack: str, signal_tags: set[str]) -> dict[str, float]:
    if "db_modeling" not in signal_tags:
        return {}
    if _contains_any(haystack, {"value object", "canonicalization", "invariant"}):
        return {}
    if _contains_any(haystack, {"normalization", "정규화"}):
        return {
            "contents/database/normalization-basics.md": 0.012,
            "contents/database/normalization-denormalization-tradeoffs.md": 0.006,
        }
    return {}


def _value_object_path_boosts(haystack: str) -> dict[str, float]:
    if not _contains_any(haystack, {"value object", "canonicalization", "canonical form"}):
        return {}
    if not _contains_any(haystack, {"invariant", "scale normalization", "boundary"}):
        return {}
    return {
        "contents/language/java/value-object-invariants-canonicalization-boundary-design.md": 0.016,
        "contents/language/java/bigdecimal-mathcontext-striptrailingzeros-canonicalization-traps.md": 0.004,
    }


def _security_path_boosts(haystack: str, signal_tags: set[str]) -> dict[str, float]:
    if "security_jwks_recovery" in signal_tags:
        return {
            "contents/security/jwt-jwks-outage-recovery-failover-drills.md": 0.008,
            "contents/security/jwks-rotation-cutover-failure-recovery.md": 0.008,
            "contents/security/jwk-rotation-cache-invalidation-kid-rollover.md": 0.003,
        }
    if "security_key_rotation_rollover" in signal_tags:
        return {
            "contents/security/jwk-rotation-cache-invalidation-kid-rollover.md": 0.008,
            "contents/security/key-rotation-runbook.md": 0.004,
            "contents/security/jwks-rotation-cutover-failure-recovery.md": 0.003,
        }
    if "security_token_validation" not in signal_tags:
        return {}
    if not _contains_any(
        haystack,
        {
            "kid",
            "issuer",
            "audience",
            "signature",
            "signature validation",
            "signature verification",
            "claim validation",
            "token validation",
            "validation 순서",
            "검증 순서",
            "서명 검증",
        },
    ):
        return {}
    if _contains_any(haystack, {"처음", "입문", "먼저", "beginner"}) and "jwks" not in haystack:
        return {
            "contents/security/jwt-deep-dive.md": 0.012,
            "contents/security/jwt-signature-verification-failure-playbook.md": 0.002,
        }
    return {
        "contents/security/jwt-signature-verification-failure-playbook.md": 0.008,
        "contents/security/jwt-deep-dive.md": 0.002,
    }


def _auth_session_path_boosts(haystack: str, signal_tags: set[str]) -> dict[str, float]:
    if "security_authentication" not in signal_tags:
        return {}
    if "security_token_validation" in signal_tags:
        return {}
    if not _contains_any(
        haystack,
        {"session", "세션", "cookie", "cookies", "쿠키", "login", "로그인", "jwt"},
    ):
        return {}
    if _contains_any(haystack, {"jwt payload", "payload structure"}) or (
        "jwt" in haystack and "authentication authorization" in haystack
    ):
        return {
            "contents/security/jwt-deep-dive.md": 0.018,
            "contents/security/session-cookie-jwt-basics.md": 0.006,
            "contents/security/authentication-authorization-session-foundations.md": 0.004,
        }
    if _contains_any(haystack, {"처음", "입문", "로그인 흐름", "authentication basics"}):
        return {
            "contents/security/authentication-authorization-session-foundations.md": 0.014,
            "contents/security/session-cookie-jwt-basics.md": 0.008,
            "contents/network/cookie-session-jwt-browser-flow-primer.md": 0.004,
        }
    if _contains_any(haystack, {"jwt", "session vs jwt", "세션이랑 jwt"}):
        return {
            "contents/security/session-cookie-jwt-basics.md": 0.014,
            "contents/security/authentication-authorization-session-foundations.md": 0.006,
            "contents/network/cookie-session-jwt-browser-flow-primer.md": 0.004,
        }
    return {
        "contents/security/session-cookie-jwt-basics.md": 0.014,
        "contents/security/authentication-authorization-session-foundations.md": 0.006,
        "contents/network/http-state-session-cache.md": 0.002,
    }


def _failover_path_boosts(haystack: str, signal_tags: set[str]) -> dict[str, float]:
    boosts: dict[str, float] = {}
    if "global_failover_control_plane" in signal_tags and not (
        "failover_visibility" in signal_tags
        or "failover_verification" in signal_tags
        or "stateful_failover_placement" in signal_tags
    ):
        boosts["contents/system-design/global-traffic-failover-control-plane-design.md"] = 0.018
    if "failover_visibility" in signal_tags:
        boosts.update(
            {
                "contents/database/failover-visibility-window-topology-cache-playbook.md": 0.012,
                "contents/database/failover-promotion-read-divergence.md": 0.006,
            }
        )
    if "failover_read_divergence" in signal_tags:
        boosts["contents/database/failover-promotion-read-divergence.md"] = max(
            boosts.get("contents/database/failover-promotion-read-divergence.md", 0.0),
            0.012,
        )
        boosts["contents/database/failover-visibility-window-topology-cache-playbook.md"] = max(
            boosts.get("contents/database/failover-visibility-window-topology-cache-playbook.md", 0.0),
            0.004,
        )
    if "failover_verification" in signal_tags:
        boosts["contents/database/commit-horizon-after-failover-verification.md"] = max(
            boosts.get("contents/database/commit-horizon-after-failover-verification.md", 0.0),
            0.020,
        )
    if "failover verification" in haystack or "write loss audit" in haystack:
        boosts["contents/database/commit-horizon-after-failover-verification.md"] = max(
            boosts.get("contents/database/commit-horizon-after-failover-verification.md", 0.0),
            0.020,
        )
    return boosts


def _generic_crud_korean_path_boosts(haystack: str) -> dict[str, float]:
    if not _contains_any(haystack, {"조회", "목록", "read"}):
        return {}
    if not _contains_any(haystack, {"수정", "삭제", "등록", "생성", "update", "delete", "create"}):
        return {}
    if _contains_any(
        haystack,
        {"저장 직후", "예전 값", "옛값", "안 보여", "목록이 그대로", "캐시", "stale"},
    ):
        return {}

    if _contains_any(haystack, {"어디 책임", "책임이", "안 돼", "실패"}):
        return {
            "contents/spring/spring-service-layer-transaction-boundary-patterns.md": 0.012,
            "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md": 0.008,
            "contents/design-pattern/repository-boundary-aggregate-vs-read-model.md": 0.006,
        }
    return {
        "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md": 0.012,
        "contents/spring/spring-mvc-controller-basics.md": 0.006,
        "contents/design-pattern/repository-pattern-vs-antipattern.md": 0.004,
    }


def _contextual_signal_path_boosts(prompt: str, signals: list[dict]) -> dict[str, float]:
    haystack = prompt.lower()
    signal_tags = {str(signal.get("tag")) for signal in signals}
    boosts: dict[str, float] = {}
    for path_boosts in (
        _projection_path_boosts(haystack, signal_tags),
        _stateful_failover_path_boosts(haystack, signal_tags),
        _query_model_beginner_entrypoint_path_boosts(haystack),
        _query_model_filter_sort_path_boosts(haystack),
        _transaction_path_boosts(haystack, signal_tags),
        _spring_framework_path_boosts(haystack, signal_tags),
        _strict_read_path_boosts(haystack),
        _java_concurrency_path_boosts(haystack, signal_tags),
        _di_ioc_path_boosts(haystack),
        _mvcc_path_boosts(haystack),
        _transaction_rollback_contrast_path_boosts(haystack),
        _api_schema_evolution_path_boosts(haystack),
        _db_modeling_path_boosts(haystack, signal_tags),
        _value_object_path_boosts(haystack),
        _security_path_boosts(haystack, signal_tags),
        _auth_session_path_boosts(haystack, signal_tags),
        _failover_path_boosts(haystack, signal_tags),
        _generic_crud_korean_path_boosts(haystack),
    ):
        for path, boost in path_boosts.items():
            boosts[path] = max(boosts.get(path, 0.0), boost)
    return boosts


def _contextual_signal_category_boosts(prompt: str, signals: list[dict]) -> set[str]:
    haystack = prompt.lower()
    categories = {
        signal.get("category")
        for signal in signals
        if signal.get("tag") in SIGNAL_CATEGORY_BOOST_TAGS
    }
    if _projection_path_boosts(haystack, {str(signal.get("tag")) for signal in signals}):
        categories.add("design-pattern")
    if _generic_crud_korean_path_boosts(haystack):
        categories.update({"spring", "design-pattern"})
    return {str(category) for category in categories if category}


def _apply_signal_boost(
    scored: list[tuple[int, float]],
    chunks: dict[int, dict],
    prompt: str,
    signals: list[dict],
    *,
    multiplier: float = 1.0,
) -> list[tuple[int, float]]:
    category_boosts = _contextual_signal_category_boosts(prompt, signals)
    path_boosts: dict[str, float] = {}
    for signal in signals:
        for path, boost in SIGNAL_PATH_BOOSTS.get(str(signal.get("tag")), {}).items():
            path_boosts[path] = max(path_boosts.get(path, 0.0), boost)
    path_boosts.update(_contextual_signal_path_boosts(prompt, signals))

    if not category_boosts and not path_boosts:
        return scored

    boosted: list[tuple[int, float]] = []
    for row_id, score in scored:
        chunk = chunks.get(row_id)
        if chunk is None:
            boosted.append((row_id, score))
            continue
        if chunk["category"] in category_boosts:
            score += SIGNAL_CATEGORY_BOOST * multiplier
        score += path_boosts.get(chunk["path"], 0.0) * multiplier
        boosted.append((row_id, score))
    boosted.sort(key=lambda t: (-t[1], t[0]))
    return boosted


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def search(
    prompt: str,
    *,
    learning_points: list[str] | None = None,
    topic_hints: list[str] | None = None,
    top_k: int = DEFAULT_TOP_K,
    mode: str = "full",
    index_root: Path | str = indexer.DEFAULT_INDEX_ROOT,
    use_reranker: bool | None = None,
    experience_level: str | None = None,
    debug: dict | None = None,
) -> list[dict]:
    """Run a hybrid CS RAG search and return top-K chunk dicts.

    Each output item::

        {
            "row_id", "doc_id", "chunk_id", "path", "title",
            "category", "section_title", "section_path",
            "score", "snippet_preview", "anchors"
        }
    """
    if mode not in ("cheap", "full"):
        raise ValueError(f"unknown mode: {mode}")

    try:
        conn = indexer.open_readonly(index_root)
    except FileNotFoundError:
        return []

    try:
        # 1. Query expansion
        tokens = signal_rules.expand_query(prompt, topic_hints)
        signals = signal_rules.detect_signals(prompt, topic_hints)
        fts_query = _to_fts_query(tokens or _fallback_tokens(prompt))

        # 2. FTS ranking
        fts_hits = _fts_search(conn, fts_query, FTS_POOL_SIZE)

        rankings: list[list[tuple[int, float]]] = []
        if fts_hits:
            rankings.append(fts_hits)

        # 3. Dense ranking (full mode only)
        if mode == "full":
            dense_hits = _dense_search(index_root, prompt, topic_hints, DENSE_POOL_SIZE)
            if dense_hits:
                rankings.append(dense_hits)

        if not rankings:
            return []

        # 4. RRF fusion
        fused = _rrf_merge(rankings)

        # Resolve the full FTS+dense fusion pool for boost + output. Corpus
        # growth can push the right primer below the old top-20 pre-boost
        # slice even when the signal family still identified it correctly.
        signal_path_boosts = _contextual_signal_path_boosts(prompt, signals)
        signal_routed_ids = _first_chunk_ids_for_paths(conn, signal_path_boosts)
        top_pool_ids = [*signal_routed_ids, *[rid for rid, _ in fused]]
        chunks = indexer.fetch_chunks_by_rowid(conn, top_pool_ids)

        # 5. Category boost
        allowed_categories = _collect_categories(learning_points)
        seeded_scores = {
            row_id: 0.0
            for row_id in signal_routed_ids
            if row_id in chunks
        }
        for row_id, score in fused:
            if row_id in chunks:
                seeded_scores[row_id] = max(seeded_scores.get(row_id, score), score)
        boosted = _apply_category_boost(
            list(seeded_scores.items()),
            chunks,
            allowed_categories,
        )

        # 5b. Difficulty boost — re-rank the existing top pool toward the
        #     learner's experience level. No-op for advanced/expert learners
        #     and when experience_level is None, so legacy goldens are
        #     untouched. Applied to the same `boosted` pool so the discovery
        #     set is never widened by difficulty alone.
        boosted = _apply_difficulty_boost(boosted, chunks, experience_level)

        # 5c. Signal boost — cheap mode has no cross-encoder, so near-ties can
        #     let broad survey or deep-dive docs outrank the intended beginner
        #     primer. Use the already-detected signal family as a small,
        #     deterministic tie-breaker without widening the candidate pool.
        boosted = _apply_signal_boost(boosted, chunks, prompt, signals)

        # 6. Category filter — keep only chunks whose category matches the
        #    learning points, if any. Falls back to unfiltered when the
        #    filter would leave fewer than top_k candidates.
        filtered, filter_fallback_used = _filter_allowed_categories(
            boosted, chunks, allowed_categories, top_k
        )
        if debug is not None:
            debug["category_filter_fallback"] = filter_fallback_used
            debug["allowed_categories"] = sorted(allowed_categories)

        # 7. Optional rerank (full mode only). Decorate the prompt with
        #    learning-point anchor phrases so the reranker sees canonical
        #    domain terms (fixes e.g. "책임 분리" collapsing onto
        #    "Chain of Responsibility" on raw token overlap).
        if mode == "full" and _rerank_enabled(use_reranker):
            anchor = category_mapping.anchor_phrase_for(learning_points)
            rerank_prompt = f"{anchor}\n\n{prompt}" if anchor else prompt
            filtered = _rerank(rerank_prompt, filtered, chunks, top_n=top_k * 2)
            # Cross-encoder scores are not calibrated against our route
            # contract. Re-apply signal boosts after rerank so explicit
            # beginner/family routing survives final polishing.
            filtered = _apply_signal_boost(
                filtered,
                chunks,
                prompt,
                signals,
                multiplier=POST_RERANK_SIGNAL_BOOST_MULTIPLIER,
            )

        # 8. Document-level dedupe — one chunk per source path
        deduped = _dedupe_by_path(filtered, chunks)

        # 9. Compose output
        return [_format_hit(chunks[rid], score) for rid, score in deduped[:top_k]]
    finally:
        conn.close()


def _fallback_tokens(prompt: str) -> list[str]:
    """When signal_rules.expand_query returns empty (short prompt)."""
    return [tok for tok in _FTS_TOKEN_RE.findall(prompt) if len(tok) >= 2]


def _collect_categories(learning_points: list[str] | None) -> set[str]:
    if not learning_points:
        return set()
    allowed: set[str] = set()
    for lp in learning_points:
        allowed.update(category_mapping.categories_for(lp))
    return allowed


def _rerank_enabled(use_reranker: bool | None) -> bool:
    if use_reranker is False:
        return False
    if os.environ.get("WOOWA_RAG_NO_RERANK") == "1":
        return False
    return use_reranker is True or use_reranker is None  # default on


def _filter_allowed_categories(
    scored: list[tuple[int, float]],
    chunks: dict[int, dict],
    allowed_categories: set[str],
    min_keep: int,
) -> tuple[list[tuple[int, float]], bool]:
    """Filter the pool to chunks whose category is in ``allowed_categories``.

    When ``allowed_categories`` is empty (no learning points supplied) the
    pool is returned untouched. If strict filtering would leave fewer than
    ``min_keep`` items (too narrow — e.g. a learning point mapped to a
    single category with thin coverage), the original unfiltered pool is
    returned so retrieval still produces an answer.

    Returns ``(pool, fallback_used)``. ``fallback_used`` is True when the
    strict filter would have starved the pool and the unfiltered result
    was returned instead — callers surface this as observability so AI
    sessions can footnote "results from outside the expected category".
    """
    if not allowed_categories:
        return scored, False
    kept: list[tuple[int, float]] = []
    for row_id, score in scored:
        chunk = chunks.get(row_id)
        if chunk is None:
            continue
        if chunk["category"] in allowed_categories:
            kept.append((row_id, score))
    if len(kept) < min_keep:
        return scored, True
    return kept, False


def _dedupe_by_path(
    scored: list[tuple[int, float]],
    chunks: dict[int, dict],
) -> list[tuple[int, float]]:
    """Keep only the first (highest-ranked) chunk per source path.

    Preserves input order, so whatever upstream ranking determined the
    winner wins. Chunks whose row_id is missing from the chunk map are
    dropped silently.
    """
    seen: set[str] = set()
    out: list[tuple[int, float]] = []
    for row_id, score in scored:
        chunk = chunks.get(row_id)
        if chunk is None:
            continue
        path = chunk["path"]
        if path in seen:
            continue
        seen.add(path)
        out.append((row_id, score))
    return out


def _rerank(
    prompt: str,
    scored: list[tuple[int, float]],
    chunks: dict[int, dict],
    top_n: int,
) -> list[tuple[int, float]]:
    try:
        from .reranker import rerank  # type: ignore
    except ImportError:
        return scored
    pool = scored[:top_n]
    try:
        reranked = rerank(prompt, [(rid, chunks[rid]) for rid, _ in pool if rid in chunks])
    except Exception:
        return scored
    reranked_ids = {rid for rid, _ in reranked}
    tail = [item for item in scored if item[0] not in reranked_ids]
    return reranked + tail


def _format_hit(chunk: dict, score: float) -> dict:
    body = chunk["body"]
    snippet = body[:250].replace("\n", " ").strip()
    if len(body) > 250:
        snippet += "…"
    return {
        "row_id": chunk["row_id"],
        "doc_id": chunk["doc_id"],
        "chunk_id": chunk["chunk_id"],
        "path": chunk["path"],
        "title": chunk["title"],
        "category": chunk["category"],
        "section_title": chunk["section_title"],
        "section_path": chunk["section_path"],
        "score": round(score, 6),
        "snippet_preview": snippet,
        "anchors": chunk["anchors"],
    }
