"""Signal rules — prompt/topic → query expansion tokens.

Each rule: trigger token set → expansion tokens + canonical signal tag
(used as the fallback-bucket key when no peer learning-point matches).

Signal tags are stable identifiers the rest of the pipeline can switch on.
The rules cover the recurring Woowa mission review axes plus a few
high-value CS corpus entrypoints.
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
        "triggers": {
            "repository",
            "dao",
            "aggregate",
            "레포지토리",
            "영속성",
            "persistence",
            "read model",
            "query model",
        },
        "expand": [
            "repository",
            "repository pattern",
            "dao pattern",
            "persistence",
            "aggregate root",
            "read model",
        ],
        "category": "database",
    },
    {
        "tag": "transaction_isolation",
        "triggers": {
            "transaction",
            "트랜잭션",
            "rollback",
            "commit",
            "isolation",
            "격리",
            "locking",
            "optimistic",
            "pessimistic",
            "for update",
            "serializable",
        },
        "expand": [
            "transaction",
            "isolation level",
            "locking strategy",
            "optimistic lock",
            "pessimistic lock",
            "rollback",
        ],
        "category": "database",
    },
    {
        "tag": "mysql_gap_locking",
        "triggers": {
            "mysql gap lock",
            "gap lock",
            "next-key lock",
            "next key lock",
            "record lock",
            "insert intention",
            "insert intention wait",
            "range lock",
            "repeatable read locking",
            "innodb gap locking",
            "phantom read prevention",
            "select for update insert blocked",
            "mysql overlap locking",
            "overlap enforcement fallback",
            "engine fallback overlap enforcement",
            "engine fallbacks overlap enforcement",
            "lock wait timeout",
        },
        "expand": [
            "gap lock",
            "next-key lock",
            "record lock",
            "insert intention wait",
            "range lock",
            "innodb gap locking",
            "overlap enforcement fallback",
            "engine fallback overlap enforcement",
        ],
        "category": "database",
    },
    {
        "tag": "transaction_anomaly_patterns",
        "triggers": {
            "이상 현상",
            "anomaly",
            "dirty read",
            "non-repeatable read",
            "non repeatable read",
            "phantom read",
            "read committed",
            "repeatable read",
            "write skew",
            "deadlock",
            "데드락",
            "lock wait timeout",
            "mysql deadlock",
        },
        "expand": [
            "transaction anomaly",
            "dirty read",
            "non-repeatable read",
            "phantom read",
            "read committed",
            "repeatable read",
            "deadlock",
            "mysql deadlock",
        ],
        "category": "database",
    },
    {
        "tag": "transaction_deadlock_case_study",
        "triggers": {
            "mysql 데드락",
            "mysql deadlock",
            "deadlock",
            "데드락",
            "wait graph",
            "circular wait",
            "lock ordering",
            "deadlock log",
            "innodb deadlock log",
        },
        "expand": [
            "deadlock",
            "deadlock case study",
            "lock ordering",
            "deadlock retry",
            "lock wait",
            "wait graph",
            "transaction deadlock",
            "circular wait",
            "innodb deadlock log",
        ],
        "category": "database",
    },
    {
        "tag": "db_modeling",
        "triggers": {"schema", "스키마", "정규화", "normalization", "table", "index", "인덱스"},
        "expand": ["schema design", "normalization", "index", "primary key"],
        "category": "database",
    },
    {
        "tag": "storage_contract_evolution",
        "triggers": {
            "cdc schema evolution",
            "cross-service schema evolution",
            "cross service schema evolution",
            "expand-contract",
            "expand contract",
            "contract phase",
            "contract/remove phase",
            "contract remove phase",
            "remove phase",
            "contract-safe rollout",
            "debezium schema change",
            "versioned payload",
            "forward compatible consumer",
            "backward compatible payload",
            "consumer tolerance",
            "backward compatible event",
            "column retirement",
            "field retirement",
            "destructive schema cleanup",
            "destructive cleanup",
            "schema cleanup",
            "drop column safety",
            "field removal runbook",
            "old field shadow read",
            "shadow read removal",
            "shadow read 제거",
            "retention replay window",
            "retention/replay window",
            "read-off",
            "write-off",
            "old consumer",
            "new connector",
            "하위 호환",
            "상위 호환",
        },
        "expand": [
            "cdc schema evolution",
            "cross-service schema evolution",
            "expand contract migration",
            "backward compatible payload",
            "forward compatible consumer",
            "consumer tolerance",
            "versioned payload",
            "debezium schema change",
            "contract-safe rollout",
            "column retirement",
        ],
        "category": "database",
    },
    {
        "tag": "event_upcaster_compatibility",
        "triggers": {
            "upcaster",
            "upcast",
            "event schema",
            "event schema evolution",
            "event compatibility",
            "legacy event",
            "legacy event replay",
            "semantic versioned event",
            "upcast chain",
            "tolerant reader",
            "event contract",
            "replay compatibility",
        },
        "expand": [
            "event upcaster",
            "event compatibility layer",
            "legacy event replay",
            "event schema evolution",
            "semantic versioned event",
            "upcast chain",
            "tolerant reader",
        ],
        "category": "design-pattern",
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
        "triggers": {"list", "map", "collection", "컬렉션", "iterator", "stream api", "도메인"},
        "expand": ["collection", "domain model", "value object"],
        "category": "design-pattern",
    },
    {
        "tag": "spring_framework",
        "triggers": {
            "spring",
            "spring boot",
            "spring data jpa",
            "spring mvc",
            "springmvc",
            "dispatcher servlet",
            "dispatcherservlet",
            "@transactional",
            "@controller",
            "@restcontroller",
            "@service",
            "@component",
            "bean",
            "빈",
            "스프링",
            "스프링 부트",
            "스프링 부트 actuator",
            "jpa",
            "hibernate",
            "entitymanager",
            "applicationcontext",
            "filter chain",
            "spring security",
        },
        "expand": [
            "spring",
            "spring boot",
            "spring data jpa",
            "hibernate",
            "jpa",
            "bean lifecycle",
            "dispatcher servlet",
            "spring transaction",
            "spring security filter chain",
        ],
        "category": "spring",
    },
    {
        "tag": "language_runtime_general",
        "triggers": {
            "python",
            "파이썬",
            "go",
            "golang",
            "rust",
            "kotlin",
            "코틀린",
            "typescript",
            "javascript",
            "자바스크립트",
            "node.js",
            "nodejs",
            "async/await",
            "coroutine",
            "코루틴",
            "goroutine",
            "ownership",
            "borrow checker",
            "generic type",
            "제네릭",
        },
        "expand": [
            "language runtime",
            "coroutine",
            "async await",
            "goroutine",
            "ownership",
            "generics",
            "type system",
        ],
        "category": "language",
    },
    {
        "tag": "java_language_runtime",
        "triggers": {
            "java",
            "자바",
            "bytecode",
            "바이트코드",
            "jvm",
            "gc",
            "jmm",
            "happens-before",
            "classloader",
            "class loader",
            "thread context class loader",
            "metaspace",
            "metaspace leak",
            "static cache pinning",
            "hot redeploy",
            "jit warmup",
            "tiered compilation",
            "inlining",
            "code cache",
            "profile pollution",
            "deopt",
            "deopt trigger",
            "deoptimization",
        },
        "expand": [
            "java",
            "java language",
            "bytecode",
            "jvm",
            "gc",
            "jmm",
            "happens-before",
        ],
        "category": "language",
    },
    {
        "tag": "java_concurrency_utilities",
        "triggers": {
            "executorservice",
            "executor",
            "executor sizing",
            "future",
            "callable",
            "completablefuture",
            "concurrenthashmap",
            "countdownlatch",
            "cyclicbarrier",
            "phaser",
            "stampedlock",
            "자바 동시성",
            "thread pool",
            "thread pool tuning",
            "queue capacity",
            "rejection policy",
            "worker saturation",
            "common pool",
            "common-pool",
            "commonpool",
            "default executor",
            "async stage",
            "blocking stage",
            "thread hopping",
            "forkjoinpool",
        },
        "expand": [
            "java concurrency utilities",
            "executorservice",
            "future",
            "completablefuture",
            "concurrenthashmap",
            "countdownlatch",
        ],
        "category": "language",
    },
    {
        "tag": "java_virtual_threads_loom",
        "triggers": {
            "virtual thread",
            "virtual threads",
            "virtual-thread",
            "virtual-threads",
            "project loom",
            "loom",
            "carrier thread",
            "mount unmount",
            "mount/unmount",
            "thread per request",
            "thread-per-request",
            "가상 스레드",
            "버추얼 스레드",
        },
        "expand": [
            "virtual threads",
            "project loom",
            "carrier thread",
        ],
        "category": "language",
    },
    {
        "tag": "java_numeric_value_semantics",
        "triggers": {
            "bigdecimal",
            "money",
            "equals",
            "compareto",
            "equality",
            "rounding",
            "canonicalization",
            "scale",
            "mathcontext",
            "striptrailingzeros",
            "serialization",
            "직렬화",
        },
        "expand": [
            "bigdecimal",
            "equals",
            "compareto",
            "roundingmode",
            "canonicalization",
            "json serialization",
        ],
        "category": "language",
    },
    {
        "tag": "java_value_canonicalization",
        "triggers": {
            "value object",
            "canonicalization",
            "normalization",
            "scale normalization",
            "striptrailingzeros",
            "mathcontext",
            "toplainstring",
            "scientific notation",
            "invariant",
        },
        "expand": [
            "value object",
            "canonicalization",
            "normalization",
            "scale normalization",
            "striptrailingzeros",
        ],
        "category": "language",
    },
    {
        "tag": "applied_data_structures",
        "triggers": {
            "자료구조",
            "자료 구조",
            "data structure",
            "deque",
            "ring buffer",
            "lock-free queue",
            "timing wheel",
            "bloom filter",
            "count-min sketch",
            "hyperloglog",
            "roaring bitmap",
            "trie",
            "radix tree",
            "finite state transducer",
            "cache eviction",
        },
        "expand": [
            "applied data structures",
            "data structure overview",
            "자료 구조 개요",
        ],
        "category": "data-structure",
    },
    {
        "tag": "network_error_attribution",
        "triggers": {
            "attribution",
            "local reply",
            "upstream error",
            "upstream reset",
            "generated response",
            "dns",
            "connect time",
            "tls handshake",
            "ttfb",
            "ttlb",
            "latency breakdown",
        },
        "expand": [
            "proxy local reply",
            "upstream error attribution",
            "request timing decomposition",
            "ttfb",
            "ttlb",
        ],
        "category": "network",
    },
    {
        "tag": "network_edge_failover",
        "triggers": {
            "anycast",
            "edge failover",
            "bgp",
            "route convergence",
            "path asymmetry",
            "nearest edge",
            "pop",
        },
        "expand": [
            "anycast",
            "edge failover",
            "route convergence",
            "path asymmetry",
            "global load balancing",
        ],
        "category": "network",
    },
    {
        "tag": "network_and_reliability",
        "triggers": {
            "timeout",
            "retry",
            "circuit",
            "network",
            "네트워크",
            "http",
            "latency",
            "backpressure",
            "backoff",
            "bulkhead",
            "overload",
            "load shedding",
            "deadline",
            "jitter",
        },
        "expand": [
            "timeout",
            "retry",
            "backoff",
            "retry budget",
            "backpressure",
            "load shedding",
            "circuit breaker",
            "reliability",
        ],
        "category": "network",
    },
    {
        "tag": "idempotency_dedup_family",
        "triggers": {
            "idempotency",
            "idempotency key",
            "중복 방지",
            "중복 요청",
            "중복 결제",
            "double charge",
            "payment ledger",
            "key store",
            "dedup",
            "dedup window",
            "deduplication",
            "processing lease",
            "payload hash",
            "replay safe retry",
            "replay-safe retry",
        },
        "expand": [
            "idempotency key",
            "request deduplication",
            "payment ledger",
            "double charge prevention",
            "reconciliation",
            "dedup window",
            "processing lease",
            "payload hash",
            "replay safe retry",
        ],
        "category": "system-design",
    },
    {
        "tag": "security_authentication",
        "triggers": {
            "jwt",
            "token",
            "auth",
            "인증",
            "oauth",
            "password",
            "csrf",
            "xss",
        },
        "expand": [
            "authentication",
            "authorization",
            "jwt",
            "session",
        ],
        "category": "security",
    },
    {
        "tag": "security_token_validation",
        "triggers": {
            "jwks",
            "jwk",
            "kid",
            "issuer",
            "audience",
            "signature",
            "서명",
            "verify",
            "verification",
            "claim validation",
        },
        "expand": [
            "jwt",
            "jwks",
            "token validation",
            "issuer",
            "audience",
            "signature verification",
        ],
        "category": "security",
    },
    {
        "tag": "security_key_rotation_rollover",
        "triggers": {
            "key rotation",
            "kid rollover",
            "rollover",
            "cache invalidation",
            "jwks ttl",
            "stale key",
            "known-good key",
            "refresh storm",
        },
        "expand": [
            "jwks",
            "key rotation",
            "kid rollover",
            "cache invalidation",
            "stale key",
        ],
        "category": "security",
    },
    {
        "tag": "security_key_rotation_runbook",
        "triggers": {
            "runbook",
            "dual validation",
            "grace window",
            "revoke old key",
            "rollback decision",
            "audit trail",
            "rotation incident",
        },
        "expand": [
            "key rotation",
            "rotation runbook",
            "dual validation",
            "grace window",
            "revoke old key",
        ],
        "category": "security",
    },
    {
        "tag": "security_jwks_recovery",
        "triggers": {
            "kid miss storm",
            "fail-open",
            "stale-if-error",
            "fail-closed",
            "recovery ladder",
            "outage drill",
            "verifier cache skew",
            "old key removal failure",
            "signer cutover rollback",
        },
        "expand": [
            "jwks outage recovery",
            "kid miss storm",
            "fail-open",
            "stale-if-error",
            "fail-closed",
            "recovery ladder",
            "jwks recovery",
        ],
        "category": "security",
    },
    {
        "tag": "migration_repair_cutover",
        "triggers": {
            "migration",
            "migrate",
            "마이그레이션",
            "backfill",
            "백필",
            "replay",
            "리플레이",
            "repair",
            "리페어",
            "reconciliation",
            "정합성",
            "dual write",
            "cutover",
            "컷오버",
            "rehearsal",
            "리허설",
            "receiver warmup",
            "cache prefill",
            "write freeze",
            "cutover soak",
        },
        "expand": [
            "migration",
            "backfill",
            "replay",
            "repair",
            "reconciliation",
            "cutover",
            "dual write",
            "receiver warmup",
        ],
        "category": "system-design",
    },
    {
        "tag": "projection_freshness",
        "triggers": {
            "read-your-writes",
            "read your writes",
            "read model cutover",
            "projection lag",
            "projection freshness",
            "freshness budget",
            "lag budget",
            "freshness slo",
            "freshness sli",
            "watermark gap",
            "projection watermark",
            "projection rebuild",
            "dual projection run",
            "lag breach",
            "guardrails",
            "cutover guardrails",
            "rollback policy",
            "read model cutover guardrails",
            "freshness guardrail",
            "rollback window",
            "rollback windows",
            "cutover fallback",
            "dual read parity",
        },
        "expand": [
            "read model staleness",
            "read your writes",
            "projection lag budget",
            "projection freshness slo",
            "freshness budget",
            "read model cutover guardrails",
        ],
        "category": "design-pattern",
    },
    {
        "tag": "global_failover_control_plane",
        "triggers": {
            "failover",
            "promotion",
            "regional evacuation",
            "evacuation",
            "gslb",
            "dns failover",
            "weighted region routing",
            "health signal aggregation",
            "edge steering",
        },
        "expand": [
            "global traffic failover",
            "regional evacuation",
            "weighted region routing",
            "health signal aggregation",
            "control plane",
        ],
        "category": "system-design",
    },
    {
        "tag": "stateful_failover_placement",
        "triggers": {
            "stateful workload",
            "stateful workload placement",
            "leader placement",
            "replica promotion",
            "maintenance drain",
            "quorum-aware",
            "standby assignment",
            "placement decision",
            "shard owner",
            "placement budget",
        },
        "expand": [
            "stateful workload placement",
            "failover control plane",
            "leader placement",
            "replica promotion",
            "maintenance drain",
        ],
        "category": "system-design",
    },
    {
        "tag": "failover_visibility",
        "triggers": {
            "visibility window",
            "stale primary",
            "topology cache",
            "freshness fence",
            "post promotion stale reads",
            "promotion visibility",
            "stale endpoint read",
        },
        "expand": [
            "failover visibility window",
            "post-promotion stale reads",
            "topology cache invalidation",
            "stale primary",
            "freshness fence",
        ],
        "category": "database",
    },
    {
        "tag": "failover_verification",
        "triggers": {
            "commit horizon",
            "loss boundary",
            "last applied position",
            "write loss audit",
            "promotion verification",
            "failover verification",
            "backend db recovery",
        },
        "expand": [
            "commit horizon after failover",
            "loss boundary",
            "promotion verification",
            "write loss audit",
        ],
        "category": "database",
    },
    {
        "tag": "progressive_cutover_control_plane",
        "triggers": {
            "shadowing",
            "traffic shadowing",
            "shadow traffic",
            "mirrored requests",
            "progressive cutover",
            "route guardrail",
            "abort switch",
            "dual read verification",
            "dark launch",
            "shadow traffic metrics",
            "response diff",
            "semantic equivalence",
            "diffing",
            "strangler verification",
        },
        "expand": [
            "progressive cutover",
            "traffic shadowing",
            "shadow traffic",
            "mirrored requests",
            "route guardrail",
            "response diff",
        ],
        "category": "system-design",
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
    {
        "tag": "os_locking_debugging",
        "triggers": {
            "futex",
            "mutex",
            "semaphore",
            "spinlock",
            "off-cpu",
            "perf lock",
            "lock contention",
            "mutex convoy",
        },
        "expand": [
            "futex",
            "lock contention",
            "off-cpu",
            "perf lock",
        ],
        "category": "operating-system",
    },
    {
        "tag": "os_async_io_overview",
        "triggers": {
            "io_uring",
            "epoll",
            "kqueue",
            "readiness model",
            "async i/o",
            "edge triggered",
            "completion queue",
        },
        "expand": [
            "epoll",
            "kqueue",
            "io_uring",
            "readiness model",
            "async i/o",
        ],
        "category": "operating-system",
    },
    {
        "tag": "os_io_uring_queues",
        "triggers": {
            "sq",
            "cq",
            "sqe",
            "cqe",
            "submission queue",
            "completion queue",
            "registered buffers",
            "fixed files",
        },
        "expand": [
            "io_uring",
            "submission queue",
            "completion queue",
            "sqe",
            "cqe",
        ],
        "category": "operating-system",
    },
    {
        "tag": "os_io_uring_operational_hazards",
        "triggers": {
            "registered buffers",
            "fixed files",
            "sqpoll",
            "operational hazards",
            "pointer lifetime",
            "cq overflow",
            "provided buffers",
            "iowq",
            "memlock",
        },
        "expand": [
            "io_uring operational hazards",
            "registered buffers",
            "fixed files",
            "sqpoll",
            "cq overflow",
        ],
        "category": "operating-system",
    },
]

_TOKEN_RE = re.compile(r"[0-9a-zA-Z가-힣]+")
# Strip a trailing Korean-particle run from ASCII-prefixed tokens like
# "boundary와" / "repository가" so the FTS side queries the bare stem the
# index actually stores. Pure-Hangul tokens are left untouched (stripping
# particles from them risks mangling legitimate stems).
_MIXED_TAIL_RE = re.compile(r"^([0-9A-Za-z]+)[가-힣]+$")

# When a specific signal family matches, drop broader generic buckets that
# would otherwise add noisy fallback vocabulary to the expanded query.
_SUPPRESSED_WHEN_PRESENT: dict[str, set[str]] = {
    "event_upcaster_compatibility": {
        "db_modeling",
        "layer_responsibility",
        "migration_repair_cutover",
        "storage_contract_evolution",
    },
    "idempotency_dedup_family": {
        "migration_repair_cutover",
        "network_and_reliability",
    },
    "java_concurrency_utilities": {
        "concurrency",
    },
    "mysql_gap_locking": {
        "concurrency",
    },
    "projection_freshness": {
        "persistence_boundary",
    },
    "storage_contract_evolution": {
        "db_modeling",
        "layer_responsibility",
        "migration_repair_cutover",
    },
}

_LOCK_WAIT_TIMEOUT_DATABASE_TAGS = {
    "mysql_gap_locking",
    "transaction_anomaly_patterns",
    "transaction_deadlock_case_study",
    "transaction_isolation",
}

_STORAGE_CONTRACT_CDC_TRIGGERS = {
    "cdc schema evolution",
    "debezium schema change",
    "backward compatible event",
    "old consumer",
    "new connector",
}

_STORAGE_CONTRACT_CROSS_SERVICE_TRIGGERS = {
    "cross-service schema evolution",
    "cross service schema evolution",
    "backward compatible payload",
    "consumer tolerance",
}

_STORAGE_CONTRACT_RETIREMENT_TRIGGERS = {
    "contract phase",
    "contract/remove phase",
    "contract remove phase",
    "remove phase",
    "column retirement",
    "field retirement",
    "destructive schema cleanup",
    "destructive cleanup",
    "schema cleanup",
    "drop column safety",
    "field removal runbook",
    "old field shadow read",
    "shadow read removal",
    "shadow read 제거",
    "retention replay window",
    "retention/replay window",
    "read-off",
    "write-off",
}

_JAVA_RUNTIME_CLASSLOADER_TRIGGERS = {
    "classloader",
    "class loader",
    "thread context class loader",
    "metaspace",
    "metaspace leak",
    "static cache pinning",
    "hot redeploy",
}

_JAVA_RUNTIME_JIT_TRIGGERS = {
    "jit warmup",
    "tiered compilation",
    "inlining",
    "code cache",
    "profile pollution",
    "deopt",
    "deopt trigger",
    "deoptimization",
}

_JAVA_RUNTIME_DEEP_DIVE_TRIGGERS = (
    _JAVA_RUNTIME_CLASSLOADER_TRIGGERS | _JAVA_RUNTIME_JIT_TRIGGERS
)

_JAVA_CONCURRENCY_TUNING_TRIGGERS = {
    "executor",
    "executor sizing",
    "thread pool",
    "thread pool tuning",
    "queue capacity",
    "rejection policy",
    "worker saturation",
}

_JAVA_CONCURRENCY_COMMON_POOL_TRIGGERS = {
    "common pool",
    "common-pool",
    "commonpool",
    "default executor",
    "async stage",
    "blocking stage",
    "thread hopping",
    "forkjoinpool",
}

_JAVA_CONCURRENCY_OVERVIEW_TRIGGERS = {
    "executorservice",
    "future",
    "callable",
    "completablefuture",
    "concurrenthashmap",
    "countdownlatch",
    "cyclicbarrier",
    "phaser",
    "stampedlock",
    "자바 동시성",
}

_JAVA_VIRTUAL_THREADS_CORE_TRIGGERS = {
    "virtual thread",
    "virtual threads",
    "virtual-thread",
    "virtual-threads",
    "project loom",
    "loom",
    "가상 스레드",
    "버추얼 스레드",
}

_JAVA_VIRTUAL_THREADS_MECHANICS_TRIGGERS = {
    "carrier thread",
    "mount unmount",
    "mount/unmount",
    "thread per request",
    "thread-per-request",
}

_JAVA_VIRTUAL_THREADS_MIGRATION_CUES = {
    "migration",
    "threadlocal",
    "pool boundary",
    "context propagation",
    "scopedvalue",
    "scoped value",
    "mdc",
}

_JAVA_VIRTUAL_THREADS_BUDGET_CUES = {
    "datasource",
    "pool sizing",
    "safe concurrency",
    "bulkhead",
    "request admission",
    "capacity planning",
}

_JAVA_VIRTUAL_THREADS_INCIDENT_CUES = {
    "jfr",
    "incident",
    "threadpark",
    "thread park",
    "virtualthreadpinned",
    "virtual thread pinned",
    "socketread",
    "socket read",
    "javamonitorenter",
    "java monitor enter",
}

_BEGINNER_INTENT_PHRASES = {
    "처음 배우",
    "처음 보",
    "입문자",
    "입문용",
    "입문 관점",
    "기초부터",
    "기본부터",
    "기본 개념",
    "큰 그림",
    "first principles",
    "big picture",
    "beginner",
    "intro",
    "overview",
    "primer",
}

_BEGINNER_INTENT_TOKEN_GROUPS = (
    frozenset({"처음", "배우는데"}),
    frozenset({"처음", "보는데"}),
    frozenset({"처음", "설명"}),
    frozenset({"입문", "설명"}),
    frozenset({"먼저", "설명해줘"}),
)

_PROJECTION_FRESHNESS_PRIMER_CUES = {
    "read model freshness",
    "read model staleness",
    "projection freshness",
    "read-your-writes",
    "read your writes",
    "stale read",
    "old data after write",
    "saved but still old data",
}

_PROJECTION_ROLLBACK_WINDOW_CUES = {
    "rollback window",
    "rollback windows",
}

_PROJECTION_TX_NOISE_TRIGGERS = {
    "rollback",
    "transaction",
    "트랜잭션",
    "commit",
}

_BEGINNER_PRIMER_OVERRIDES: dict[str, dict[str, object]] = {
    "java_language_runtime": {
        "expand": [
            "java runtime overview",
            "bytecode execution flow",
            "heap stack metaspace",
            "runtime basics",
        ],
        "score_bonus": 1,
    },
    "java_concurrency_utilities": {
        "expand": [
            "java concurrency overview",
            "thread pool basics",
            "future composition basics",
            "coordination primitives",
            "executor basics",
        ],
        "score_bonus": 2,
    },
    "java_virtual_threads_loom": {
        "expand": [
            "loom overview",
            "virtual threads basics",
            "blocking i/o with virtual threads",
            "thread per request with loom",
            "mount unmount",
        ],
        "score_bonus": 3,
        "suppress": {
            "concurrency",
            "java_language_runtime",
            "resource_lifecycle",
        },
    },
    "security_authentication": {
        "requires_any": {"security_token_validation"},
        "expand": [
            "token payload structure",
            "claims",
            "exp",
            "jwt basics",
        ],
        "score_bonus": 2,
        "suppress": {"security_token_validation"},
    },
    "transaction_isolation": {
        "expand": [
            "mvcc",
            "dirty read",
            "non-repeatable read",
            "phantom read",
            "read committed",
            "repeatable read",
        ],
        "score_bonus": 1,
    },
    "transaction_anomaly_patterns": {
        "requires_any": {"transaction_isolation"},
        "expand": [
            "mvcc",
            "dirty read",
            "non-repeatable read",
            "phantom read",
            "read committed",
            "repeatable read",
        ],
        "score_bonus": 3,
        "suppress": {"transaction_isolation"},
    },
    "os_async_io_overview": {
        "requires_any": {"os_io_uring_queues", "os_io_uring_operational_hazards"},
        "expand": [
            "epoll kqueue io_uring overview",
            "edge triggered",
            "overview",
        ],
        "score_bonus": 2,
        "suppress": {
            "os_io_uring_queues",
            "os_io_uring_operational_hazards",
        },
    },
    "projection_freshness": {
        "expand": [
            "read model staleness",
            "stale read",
            "old data after write",
            "eventual consistency ux",
            "saved but still old data",
        ],
        "score_bonus": 2,
        "suppress": {"migration_repair_cutover"},
    },
}


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


def _is_short_ascii_trigger(trigger: str) -> bool:
    return len(trigger) <= 2 and trigger.isascii() and trigger.isalnum()


def _matched_triggers(haystack: str, tokens: set[str], triggers: set[str]) -> set[str]:
    matched: set[str] = set()
    for trig in triggers:
        if _is_short_ascii_trigger(trig):
            if trig in tokens:
                matched.add(trig)
            continue
        if trig in haystack:
            matched.add(trig)
    return matched


def _storage_contract_expand(matched_triggers: set[str]) -> list[str]:
    expand = [
        "expand contract migration",
        "forward compatible consumer",
        "versioned payload",
        "contract-safe rollout",
        "column retirement",
    ]

    has_cross_service = bool(matched_triggers & _STORAGE_CONTRACT_CROSS_SERVICE_TRIGGERS)
    has_cdc = bool(matched_triggers & _STORAGE_CONTRACT_CDC_TRIGGERS)
    has_retirement = bool(matched_triggers & _STORAGE_CONTRACT_RETIREMENT_TRIGGERS)

    if has_retirement:
        expand.extend(
            [
                "contract phase",
                "destructive schema cleanup",
                "schema cleanup",
                "drop column safety",
                "field removal runbook",
            ]
        )

    if has_cross_service:
        expand.extend(
            [
                "cross-service schema evolution",
                "backward compatible payload",
                "consumer tolerance",
            ]
        )

    if has_cdc:
        expand.extend(
            [
                "cdc schema evolution",
                "debezium schema change",
                "backward compatible event",
                "old consumer",
                "new connector",
            ]
        )

    if not (has_cross_service or has_cdc or has_retirement):
        expand.extend(
            [
                "backward compatible payload",
                "consumer tolerance",
            ]
        )

    return expand


def _java_runtime_expand(matched_triggers: set[str]) -> list[str]:
    expand = [
        "java",
        "java language",
        "bytecode",
        "jvm",
        "gc",
        "jmm",
        "happens-before",
    ]

    if matched_triggers & _JAVA_RUNTIME_CLASSLOADER_TRIGGERS:
        expand.extend(
            [
                "classloader",
                "metaspace leak",
                "thread context class loader",
                "static cache pinning",
                "hot redeploy leak triage",
            ]
        )

    if matched_triggers & _JAVA_RUNTIME_JIT_TRIGGERS:
        expand.extend(
            [
                "jit warmup",
                "tiered compilation",
                "code cache",
                "profile pollution",
                "deoptimization",
            ]
        )

    return expand


def _java_concurrency_expand(
    matched_triggers: set[str],
    *,
    beginner_intent: bool = False,
) -> list[str]:
    expand = [
        "java concurrency utilities",
        "executorservice",
        "future",
        "completablefuture",
        "concurrenthashmap",
        "countdownlatch",
    ]

    has_tuning_intent = bool(matched_triggers & _JAVA_CONCURRENCY_TUNING_TRIGGERS)
    has_overview_intent = bool(matched_triggers & _JAVA_CONCURRENCY_OVERVIEW_TRIGGERS)
    has_common_pool_intent = bool(matched_triggers & _JAVA_CONCURRENCY_COMMON_POOL_TRIGGERS)
    if has_tuning_intent and not has_overview_intent:
        expand.extend(
            [
                "executor sizing",
                "queue capacity",
                "rejection policy",
                "worker saturation",
                "thread pool tuning",
            ]
        )

    if has_common_pool_intent and not beginner_intent:
        expand.extend(
            [
                "common pool",
                "default executor",
                "forkjoinpool",
                "async stage",
                "blocking stage",
                "thread hopping",
            ]
        )

    return expand


def _java_virtual_threads_expand(
    haystack: str,
    matched_triggers: set[str],
    *,
    beginner_intent: bool = False,
) -> list[str]:
    expand = [
        "virtual threads",
    ]

    if beginner_intent or matched_triggers & _JAVA_VIRTUAL_THREADS_MECHANICS_TRIGGERS:
        expand.extend(
            [
                "carrier thread",
                "thread per request with loom",
                "mount unmount",
                "blocking i/o with virtual threads",
            ]
        )

    if beginner_intent:
        expand.extend(
            [
                "project loom",
                "loom overview",
                "virtual threads basics",
                "pinning basics",
            ]
        )

    if not beginner_intent and any(cue in haystack for cue in _JAVA_VIRTUAL_THREADS_MIGRATION_CUES):
        expand.extend(
            [
                "virtual thread migration",
                "threadlocal migration",
                "pool boundary strategy",
            ]
        )

    if not beginner_intent and any(cue in haystack for cue in _JAVA_VIRTUAL_THREADS_BUDGET_CUES):
        expand.extend(
            [
                "connection budget alignment after loom",
                "datasource pool sizing after virtual threads",
                "outbound http bulkhead budget",
            ]
        )

    if not beginner_intent and any(cue in haystack for cue in _JAVA_VIRTUAL_THREADS_INCIDENT_CUES):
        expand.extend(
            [
                "jfr loom incident map",
                "threadpark",
                "virtualthreadpinned",
                "socketread",
                "javamonitorenter",
            ]
        )

    return expand


def _gap_lock_compound_matches(haystack: str) -> set[str]:
    matched: set[str] = set()
    if "select for update" in haystack and "insert blocked" in haystack:
        matched.add("__select_for_update_insert_blocked__")
    if "select for update" in haystack and (
        "예약 겹침" in haystack or "겹침 검사" in haystack or "overlap" in haystack
    ):
        matched.add("__overlap_enforcement_locking__")
    return matched


def _mvcc_beginner_primer_matches(haystack: str, tokens: set[str]) -> set[str]:
    if "mvcc" not in haystack:
        return set()
    if not _has_beginner_intent(haystack, tokens):
        return set()
    return {"__mvcc_beginner_primer__"}


def _should_suppress_network_timeout_noise(haystack: str, hits: list[dict]) -> bool:
    if "lock wait timeout" not in haystack:
        return False

    present_tags = {hit["tag"] for hit in hits}
    if not (present_tags & _LOCK_WAIT_TIMEOUT_DATABASE_TAGS):
        return False

    network_hit = next((hit for hit in hits if hit["tag"] == "network_and_reliability"), None)
    if not network_hit:
        return False

    matched_triggers = network_hit.get("_matched_triggers", set())
    return bool(matched_triggers) and matched_triggers <= {"timeout"}


def _should_suppress_deadlock_anomaly_overlap(hits: list[dict]) -> bool:
    present_tags = {hit["tag"] for hit in hits}
    if "transaction_deadlock_case_study" not in present_tags:
        return False

    anomaly_hit = next((hit for hit in hits if hit["tag"] == "transaction_anomaly_patterns"), None)
    if not anomaly_hit:
        return False

    matched_triggers = anomaly_hit.get("_matched_triggers", set())
    return bool(matched_triggers) and matched_triggers <= {
        "deadlock",
        "데드락",
        "mysql deadlock",
    }


def _should_suppress_deadlock_concurrency_noise(hits: list[dict]) -> bool:
    present_tags = {hit["tag"] for hit in hits}
    if "transaction_deadlock_case_study" not in present_tags:
        return False

    concurrency_hit = next((hit for hit in hits if hit["tag"] == "concurrency"), None)
    if not concurrency_hit:
        return False

    matched_triggers = concurrency_hit.get("_matched_triggers", set())
    return bool(matched_triggers) and matched_triggers <= {"lock"}


def _should_suppress_transaction_locking_concurrency_noise(hits: list[dict]) -> bool:
    present_tags = {hit["tag"] for hit in hits}
    if "transaction_isolation" not in present_tags:
        return False

    concurrency_hit = next((hit for hit in hits if hit["tag"] == "concurrency"), None)
    if not concurrency_hit:
        return False

    matched_triggers = concurrency_hit.get("_matched_triggers", set())
    return bool(matched_triggers) and matched_triggers <= {"lock"}


def _should_suppress_gap_lock_deadlock_noise(haystack: str, hits: list[dict]) -> bool:
    if "lock wait timeout" not in haystack:
        return False

    present_tags = {hit["tag"] for hit in hits}
    if "mysql_gap_locking" not in present_tags:
        return False

    anomaly_hit = next((hit for hit in hits if hit["tag"] == "transaction_anomaly_patterns"), None)
    if not anomaly_hit:
        return False

    matched_triggers = anomaly_hit.get("_matched_triggers", set())
    return bool(matched_triggers) and matched_triggers <= {"lock wait timeout"}


def _should_suppress_jwks_fail_closed_resource_noise(hits: list[dict]) -> bool:
    present_tags = {hit["tag"] for hit in hits}
    if "security_jwks_recovery" not in present_tags:
        return False

    resource_hit = next((hit for hit in hits if hit["tag"] == "resource_lifecycle"), None)
    if not resource_hit:
        return False

    matched_triggers = resource_hit.get("_matched_triggers", set())
    return bool(matched_triggers) and matched_triggers <= {"close"}


def _should_suppress_os_locking_concurrency_noise(hits: list[dict]) -> bool:
    present_tags = {hit["tag"] for hit in hits}
    if "os_locking_debugging" not in present_tags:
        return False

    concurrency_hit = next((hit for hit in hits if hit["tag"] == "concurrency"), None)
    if not concurrency_hit:
        return False

    matched_triggers = concurrency_hit.get("_matched_triggers", set())
    return bool(matched_triggers) and matched_triggers <= {"lock"}


def _should_suppress_failover_rotation_cache_noise(hits: list[dict]) -> bool:
    present_tags = {hit["tag"] for hit in hits}
    if "failover_visibility" not in present_tags:
        return False

    rollover_hit = next(
        (hit for hit in hits if hit["tag"] == "security_key_rotation_rollover"),
        None,
    )
    if not rollover_hit:
        return False

    matched_triggers = rollover_hit.get("_matched_triggers", set())
    return bool(matched_triggers) and matched_triggers <= {"cache invalidation"}


def _should_suppress_projection_rollback_transaction_noise(
    haystack: str,
    tokens: set[str],
    hits: list[dict],
) -> bool:
    if not _has_beginner_intent(haystack, tokens):
        return False
    if not _is_projection_freshness_primer_prompt(haystack):
        return False
    if not any(cue in haystack for cue in _PROJECTION_ROLLBACK_WINDOW_CUES):
        return False

    present_tags = {hit["tag"] for hit in hits}
    if "projection_freshness" not in present_tags or "transaction_isolation" not in present_tags:
        return False

    transaction_hit = next((hit for hit in hits if hit["tag"] == "transaction_isolation"), None)
    if not transaction_hit:
        return False

    matched_triggers = transaction_hit.get("_matched_triggers", set())
    return bool(matched_triggers) and matched_triggers <= _PROJECTION_TX_NOISE_TRIGGERS


def _java_concurrency_false_positive_suppressions(hits: list[dict]) -> set[str]:
    present_tags = {hit["tag"] for hit in hits}
    if "java_concurrency_utilities" not in present_tags:
        return set()

    suppressed_tags: set[str] = set()

    runtime_hit = next((hit for hit in hits if hit["tag"] == "java_language_runtime"), None)
    if runtime_hit:
        matched_triggers = runtime_hit.get("_matched_triggers", set())
        if matched_triggers and matched_triggers <= {"java", "자바"}:
            suppressed_tags.add("java_language_runtime")

    layer_hit = next((hit for hit in hits if hit["tag"] == "layer_responsibility"), None)
    if layer_hit:
        matched_triggers = layer_hit.get("_matched_triggers", set())
        if matched_triggers and matched_triggers <= {"service"}:
            suppressed_tags.add("layer_responsibility")

    modeling_hit = next((hit for hit in hits if hit["tag"] == "db_modeling"), None)
    if modeling_hit:
        matched_triggers = modeling_hit.get("_matched_triggers", set())
        if matched_triggers and matched_triggers <= {"table"}:
            suppressed_tags.add("db_modeling")

    resource_hit = next((hit for hit in hits if hit["tag"] == "resource_lifecycle"), None)
    if resource_hit:
        matched_triggers = resource_hit.get("_matched_triggers", set())
        if matched_triggers and matched_triggers <= {"pool"}:
            suppressed_tags.add("resource_lifecycle")

    transaction_hit = next((hit for hit in hits if hit["tag"] == "transaction_isolation"), None)
    if transaction_hit:
        matched_triggers = transaction_hit.get("_matched_triggers", set())
        if matched_triggers and matched_triggers <= {"locking"}:
            suppressed_tags.add("transaction_isolation")

    return suppressed_tags


def _java_runtime_false_positive_suppressions(hits: list[dict]) -> set[str]:
    present_tags = {hit["tag"] for hit in hits}
    if "java_language_runtime" not in present_tags:
        return set()

    runtime_hit = next((hit for hit in hits if hit["tag"] == "java_language_runtime"), None)
    if not runtime_hit:
        return set()

    runtime_triggers = runtime_hit.get("_matched_triggers", set())
    if not (runtime_triggers & _JAVA_RUNTIME_DEEP_DIVE_TRIGGERS):
        return set()

    suppressed_tags: set[str] = set()

    concurrency_hit = next((hit for hit in hits if hit["tag"] == "concurrency"), None)
    if concurrency_hit:
        matched_triggers = concurrency_hit.get("_matched_triggers", set())
        if matched_triggers and matched_triggers <= {"thread"}:
            suppressed_tags.add("concurrency")

    resource_hit = next((hit for hit in hits if hit["tag"] == "resource_lifecycle"), None)
    if resource_hit:
        matched_triggers = resource_hit.get("_matched_triggers", set())
        if matched_triggers and matched_triggers <= {"leak"}:
            suppressed_tags.add("resource_lifecycle")

    return suppressed_tags


def _java_virtual_threads_false_positive_suppressions(hits: list[dict]) -> set[str]:
    present_tags = {hit["tag"] for hit in hits}
    if "java_virtual_threads_loom" not in present_tags:
        return set()

    suppressed_tags: set[str] = set()

    concurrency_hit = next((hit for hit in hits if hit["tag"] == "concurrency"), None)
    if concurrency_hit:
        matched_triggers = concurrency_hit.get("_matched_triggers", set())
        if matched_triggers and matched_triggers <= {
            "thread",
            "lock",
            "concurrency",
            "동시성",
        }:
            suppressed_tags.add("concurrency")

    runtime_hit = next((hit for hit in hits if hit["tag"] == "java_language_runtime"), None)
    if runtime_hit:
        matched_triggers = runtime_hit.get("_matched_triggers", set())
        if matched_triggers and matched_triggers <= {"java", "자바"}:
            suppressed_tags.add("java_language_runtime")

    transaction_hit = next((hit for hit in hits if hit["tag"] == "transaction_isolation"), None)
    if transaction_hit:
        matched_triggers = transaction_hit.get("_matched_triggers", set())
        if matched_triggers and matched_triggers <= {"locking"}:
            suppressed_tags.add("transaction_isolation")

    return suppressed_tags


def _has_beginner_intent(haystack: str, tokens: set[str]) -> bool:
    if any(phrase in haystack for phrase in _BEGINNER_INTENT_PHRASES):
        return True
    return any(group <= tokens for group in _BEGINNER_INTENT_TOKEN_GROUPS)


def _is_projection_freshness_primer_prompt(haystack: str) -> bool:
    return any(cue in haystack for cue in _PROJECTION_FRESHNESS_PRIMER_CUES)


def _apply_beginner_primer_bias(haystack: str, tokens: set[str], hits: list[dict]) -> set[str]:
    if not _has_beginner_intent(haystack, tokens):
        return set()

    hits_by_tag = {hit["tag"]: hit for hit in hits}
    present_tags = set(hits_by_tag)
    suppressed_tags: set[str] = set()
    for primer_tag, config in _BEGINNER_PRIMER_OVERRIDES.items():
        if primer_tag not in present_tags:
            continue
        if primer_tag == "projection_freshness" and not _is_projection_freshness_primer_prompt(
            haystack
        ):
            continue
        required_tags = set(config.get("requires_any", set()))
        if required_tags and not (present_tags & required_tags):
            continue

        primer_hit = hits_by_tag[primer_tag]
        primer_hit["score"] += int(config.get("score_bonus", 0))
        primer_hit["expand"].extend(config.get("expand", []))
        suppressed_tags.update(present_tags & set(config.get("suppress", set())))
    return suppressed_tags


def detect_signals(prompt: str, topic_hints: list[str] | None = None) -> list[dict]:
    """Return matched rules with expansion tokens, ranked by trigger overlap.

    Output item shape: {"tag", "category", "expand", "score"}.
    """
    haystack = _haystack(prompt, topic_hints)
    tokens = set(_tokenize(haystack))
    hits: list[dict] = []
    for rule in _RULES:
        matched_triggers = _matched_triggers(haystack, tokens, rule["triggers"])
        if rule["tag"] == "transaction_isolation" and not matched_triggers:
            matched_triggers.update(_mvcc_beginner_primer_matches(haystack, tokens))
        if rule["tag"] == "mysql_gap_locking":
            matched_triggers.update(_gap_lock_compound_matches(haystack))
        score = len(matched_triggers)
        if score == 0:
            continue
        expand = list(rule["expand"])
        if rule["tag"] == "storage_contract_evolution":
            expand = _storage_contract_expand(matched_triggers)
        elif rule["tag"] == "java_language_runtime":
            expand = _java_runtime_expand(matched_triggers)
        elif rule["tag"] == "java_concurrency_utilities":
            expand = _java_concurrency_expand(
                matched_triggers,
                beginner_intent=_has_beginner_intent(haystack, tokens),
            )
        elif rule["tag"] == "java_virtual_threads_loom":
            expand = _java_virtual_threads_expand(
                haystack,
                matched_triggers,
                beginner_intent=_has_beginner_intent(haystack, tokens),
            )
        hits.append(
            {
                "tag": rule["tag"],
                "category": rule["category"],
                "expand": expand,
                "score": score,
                "_matched_triggers": matched_triggers,
            }
        )
    if hits:
        present_tags = {hit["tag"] for hit in hits}
        suppressed_tags = {
            suppressed_tag
            for tag, suppressed in _SUPPRESSED_WHEN_PRESENT.items()
            if tag in present_tags
            for suppressed_tag in suppressed
        }
        suppressed_tags.update(_apply_beginner_primer_bias(haystack, tokens, hits))
        if _should_suppress_network_timeout_noise(haystack, hits):
            suppressed_tags.add("network_and_reliability")
        if _should_suppress_deadlock_anomaly_overlap(hits):
            suppressed_tags.add("transaction_anomaly_patterns")
        if _should_suppress_deadlock_concurrency_noise(hits):
            suppressed_tags.add("concurrency")
        if _should_suppress_transaction_locking_concurrency_noise(hits):
            suppressed_tags.add("concurrency")
        if _should_suppress_gap_lock_deadlock_noise(haystack, hits):
            suppressed_tags.add("transaction_anomaly_patterns")
        if _should_suppress_jwks_fail_closed_resource_noise(hits):
            suppressed_tags.add("resource_lifecycle")
        if _should_suppress_os_locking_concurrency_noise(hits):
            suppressed_tags.add("concurrency")
        if _should_suppress_failover_rotation_cache_noise(hits):
            suppressed_tags.add("security_key_rotation_rollover")
        if _should_suppress_projection_rollback_transaction_noise(haystack, tokens, hits):
            suppressed_tags.add("transaction_isolation")
        suppressed_tags.update(_java_concurrency_false_positive_suppressions(hits))
        suppressed_tags.update(_java_runtime_false_positive_suppressions(hits))
        suppressed_tags.update(_java_virtual_threads_false_positive_suppressions(hits))
        if suppressed_tags:
            hits = [hit for hit in hits if hit["tag"] not in suppressed_tags]
    hits.sort(key=lambda h: (-h["score"], h["tag"]))
    for hit in hits:
        hit.pop("_matched_triggers", None)
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
