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
            "query service",
        },
        "expand": [
            "repository",
            "repository pattern",
            "dao pattern",
            "persistence",
            "aggregate root",
            "read model",
            "query service",
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
            "isolation level",
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
            "anomaly overview",
            "isolation level",
            "mvcc",
            "dirty read",
            "non-repeatable read",
            "phantom read",
            "read committed",
            "repeatable read",
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
            "aop",
            "spring aop",
            "dispatcher servlet",
            "dispatcherservlet",
            "@transactional",
            "transactional",
            "@controller",
            "@restcontroller",
            "@service",
            "@component",
            "@componentscan",
            "ioc",
            "di",
            "dependency injection",
            "의존성 주입",
            "inversion of control",
            "제어 역전",
            "제어의 역전",
            "bean",
            "beanfactory",
            "bean factory",
            "빈",
            "스프링",
            "스프링 부트",
            "스프링 부트 actuator",
            "jpa",
            "hibernate",
            "entitymanager",
            "applicationcontext",
            "application context",
            "component scan",
            "componentscan",
            "컴포넌트 스캔",
            "컴포넌트스캔",
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
        "tag": "java_oop_basics",
        "triggers": {
            "oop",
            "object oriented",
            "object-oriented",
            "object oriented programming",
            "object-oriented programming",
            "객체지향",
            "객체 지향",
            "캡슐화",
            "상속",
            "다형성",
            "추상화",
            "정보 은닉",
            "클래스",
            "객체",
            "인스턴스",
        },
        "expand": [
            "object oriented core principles",
            "encapsulation",
            "inheritance",
            "polymorphism",
            "abstraction",
            "class object instance",
        ],
        "category": "language",
    },
    {
        "tag": "java_completablefuture_cancellation",
        "triggers": {
            "cancel",
            "cancellation",
            "cancellation semantics",
            "cancellationexception",
            "cancel(true)",
            "cancel(false)",
            "cancel false",
            "mayinterruptifrunning",
            "may interrupt if running",
            "interrupt",
            "interruptedexception",
            "cooperative cancellation",
            "propagation",
            "exceptional completion",
            "dependent stage",
        },
        "expand": [
            "completablefuture cancellation",
            "cancellationexception",
            "cooperative cancellation",
            "interrupt",
            "exceptional completion",
        ],
        "category": "language",
    },
    {
        "tag": "java_completablefuture_fan_in_timeout",
        "triggers": {
            "allof",
            "all of",
            "anyof",
            "any of",
            "join",
            "join vs get",
            "completionexception",
            "executionexception",
            "ortimeout",
            "or timeout",
            "completeontimeout",
            "complete on timeout",
            "exceptionally",
            "whencomplete",
            "partial failure",
            "partial success",
            "fan-in",
            "fan in",
            "fan-out",
            "fan out",
        },
        "expand": [
            "completablefuture allof",
            "join vs get",
            "completionexception",
            "ortimeout",
            "exceptionally",
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
        "tag": "java_structured_concurrency",
        "triggers": {
            "structured concurrency",
            "structured-concurrency",
            "structuredtaskscope",
            "structured task scope",
            "structured cancellation",
            "scope-bound context",
            "scope bound context",
            "scope lifetime",
            "structured lifetime",
            "task group lifetime",
            "fail-fast task group",
        },
        "expand": [
            "structured concurrency",
            "structuredtaskscope",
            "cancellation propagation",
            "scope lifetime",
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
        "tag": "network_keepalive_basics",
        "triggers": {
            "keep-alive",
            "keep alive",
            "keepalive",
            "connection reuse",
            "persistent connection",
            "http keep alive",
            "http/1.1 persistent connection",
            "tcp 연결 재사용",
            "커넥션 재사용",
        },
        "expand": [
            "keepalive connection reuse basics",
            "http keep-alive",
            "persistent connection",
            "connection reuse",
            "idle timeout",
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
            "session",
            "세션",
            "cookie",
            "cookies",
            "쿠키",
            "cookie login",
            "cookie keeps me signed in",
            "browser remembers my login",
            "login state",
            "logged in",
            "signed in",
            "still logged in",
            "stay logged in",
            "remember me",
            "로그인 상태",
            "로그인 유지",
            "로그인 계속",
            "로그인 안 풀",
            "로그인 풀림",
            "로그인 기억",
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
            "key-rotation",
            "kid rollover",
            "kid-rollover",
            "rollover",
            "cache invalidation",
            "cache-invalidation",
            "jwks ttl",
            "stale key",
            "stale-key",
            "known-good key",
            "known-good-key",
            "refresh storm",
            "refresh-storm",
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
            "key-rotation runbook",
            "key rotation rollback",
            "key-rotation rollback",
            "dual validation",
            "dual-validation",
            "grace window",
            "grace-window",
            "revoke old key",
            "revoke-old-key",
            "rollback decision",
            "rollback-decision",
            "rollback plan",
            "rollback-plan",
            "recovery path",
            "recovery-path",
            "audit trail",
            "rotation incident",
            "rotation-incident",
        },
        "expand": [
            "key rotation",
            "rotation runbook",
            "key rotation rollback",
            "rollback plan",
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
            "kid-miss storm",
            "fail-open",
            "stale-if-error",
            "fail-closed",
            "recovery ladder",
            "outage drill",
            "verifier cache skew",
            "verifier-cache-skew",
            "old key removal failure",
            "old-key removal failure",
            "signer cutover rollback",
            "signer-cutover rollback",
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
            "stale read",
            "stale reads",
            "read model cutover",
            "read model freshness",
            "read model staleness",
            "projection lag",
            "projection freshness",
            "읽기 모델 최신성",
            "읽기 모델 지연",
            "읽기 모델 반영 지연",
            "롤백 윈도우",
            "예전 값이 보임",
            "예전 값이 보여",
            "예전 값이 왜 보이는지",
            "예전 값이 왜 보여",
            "옛값이 보임",
            "옛값이 보여",
            "옛값이 왜 보이는지",
            "옛값이 왜 보여",
            "옛값만 보여",
            "옛 값이 보임",
            "옛 값이 보여",
            "쓴 직후 읽기",
            "방금 저장했는데 안 보여",
            "방금 저장했는데 안 보임",
            "저장했는데 안 보여",
            "저장했는데 안 보임",
            "저장했는데 옛값이 보인다",
            "저장 직후 조회",
            "저장 직후 조회하면 예전 데이터가 보임",
            "저장 직후 예전 값이 보이",
            "저장 직후 예전 값이 왜 보이",
            "저장 직후 목록 최신화가 안 됨",
            "저장했는데 목록이 그대로",
            "수정했는데 화면엔 예전 목록이 보여",
            "저장한 뒤 화면 반영이 늦음",
            "저장했는데 화면이 캐시된 것처럼 안 바뀌어",
            "저장했는데 화면이 캐시된 것 같아",
            "저장 후 화면이 캐시된 것 같아",
            "저장 후 화면이 캐시된 것처럼 보여",
            "저장하고 나서 화면이 캐시된 것처럼 보여",
            "목록이 바로 안 바뀌고",
            "예전 화면이 잠깐 보여",
            "새로고침 전까지 이전 상태가 보이고",
            "화면 반영이 한참 늦어",
            "목록 새로고침이 느림",
            "목록 새로고침이 느리고",
            "리스트가 늦게 갱신",
            "리스트가 늦게 갱신되고",
            "이전 화면 상태가 남아",
            "예전 상태가 남아 보여",
            "old screen state",
            "list refresh lag",
            "refresh lag",
            "old value",
            "old values",
            "저장했는데 옛값이 보임",
            "예전 데이터가 보임",
            "저장한 값이 안 보여",
            "저장한 값이 안 보임",
            "방금 쓴 값이 안 보임",
            "저장은 됐는데 조회가 달라",
            "수정했는데 목록은 그대로야",
            "목록이 안 바뀜",
            "방금 쓴 값 읽기",
            "오래된 값 조회",
            "삭제는 성공했는데 목록에 계속 남아 보여",
            "삭제했는데 목록에 남아",
            "삭제했는데 목록에 계속 보여",
            "삭제는 성공했는데 검색 결과에 아직 남아 있어",
            "삭제했는데 검색 결과에 남아",
            "삭제했는데 검색 결과에 아직 남아 있어",
            "삭제했는데 검색 결과나 목록에 아직 남아 있어",
            "삭제했는데 검색에 계속 보여",
            "지웠는데 목록에 남아",
            "지웠는데 검색 결과에 남아",
            "delete succeeded but still appears in list",
            "delete succeeded but still appears in search",
            "deleted item still appears in list",
            "deleted item still appears in search",
            "freshness budget",
            "lag budget",
            "freshness slo",
            "freshness sli",
            "최신성 slo",
            "지연 예산",
            "반영 지연 예산",
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
            "cutover safety window",
            "cutover safety windows",
            "컷 오버 안전 윈도우",
            "컷 오버 안전 구간",
            "컷오버 안전 윈도우",
            "컷오버 안전 구간",
            "전환 안전 윈도우",
            "전환 안전 구간",
        },
        "expand": [
            "read model staleness",
            "read your writes",
            "old data after write",
            "saved but still old data",
            "list refresh lag after write",
            "old screen state after save",
            "eventual consistency ux",
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
            "stateful failover placement",
            "stateful placement failover",
            "stateful workload",
            "stateful workload placement",
            "상태 있는 워크로드 배치 장애 전환",
            "상태 저장 워크로드",
            "상태 저장 워크로드 배치",
            "상태 저장 워크로드 장애 전환 배치",
            "상태 저장 서비스 리더 배치",
            "리더 배치",
            "어느 복제본을 올릴지",
            "상태 있는 서비스 장애 때 어느 노드를 리더로 둘지",
            "어느 노드를 리더로 둘지",
            "배치 예산",
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
        "tag": "failover_read_divergence",
        "triggers": {
            "promotion read divergence",
            "read divergence",
            "stale primary",
            "old primary read",
            "old primary still serving reads",
            "promotion stale read split",
            "post promotion read split",
        },
        "expand": [
            "failover promotion",
            "read divergence",
            "stale primary",
            "old primary still serving reads",
            "read split after promotion",
        ],
        "category": "database",
    },
    {
        "tag": "failover_visibility",
        "triggers": {
            "failover visibility",
            "visibility window",
            "stale primary",
            "topology cache",
            "freshness fence",
            "post promotion stale reads",
            "promotion visibility",
            "stale endpoint read",
            "failover 가시성",
            "페일오버 visibility",
            "장애 전환 뒤 읽기 보임",
            "장애 전환 뒤 읽기 보임 구간",
            "읽기 보임 구간",
            "옛 주 서버",
            "주 서버를 읽",
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
            "promotion validation",
            "failover verification",
            "failover validation",
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
            "strangler validation",
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
        "tag": "connection_pool_basics",
        "triggers": {
            "connection pool",
            "connection pooling",
            "커넥션 풀",
            "db connection pool",
            "hikari",
            "hikari cp",
            "datasource pool",
            "pool exhaustion",
            "pool size",
            "maximum pool size",
            "connection timeout",
        },
        "expand": [
            "connection pool basics",
            "db connection reuse",
            "hikari cp",
            "pool exhaustion",
            "connection timeout",
        ],
        "category": "database",
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
    "connection_pool_basics": {
        "resource_lifecycle",
    },
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
    "java_completablefuture_cancellation": {
        "java_concurrency_utilities",
    },
    "java_completablefuture_fan_in_timeout": {
        "java_concurrency_utilities",
        "network_and_reliability",
    },
    "java_structured_concurrency": {
        "concurrency",
    },
    "java_oop_basics": {
        "java_language_runtime",
    },
    "network_keepalive_basics": {
        "network_and_reliability",
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

_JAVA_COMPLETABLEFUTURE_CANCELLATION_TRIGGERS = {
    "cancel",
    "cancellation",
    "cancellation semantics",
    "cancellationexception",
    "cancel(true)",
    "cancel(false)",
    "mayinterruptifrunning",
    "may interrupt if running",
    "interrupt",
    "interruptedexception",
    "cooperative cancellation",
    "propagation",
    "exceptional completion",
    "dependent stage",
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

_JAVA_STRUCTURED_CONCURRENCY_HTTPCLIENT_CUES = {
    "httpclient",
    "http client",
    "fan-out",
    "fan out",
    "deadline",
    "retry",
    "bulkhead",
    "remote concurrency",
}

_JAVA_STRUCTURED_CONCURRENCY_CONTEXT_CUES = {
    "scopedvalue",
    "scoped value",
    "threadlocal",
    "inheritablethreadlocal",
    "inheritable threadlocal",
    "context propagation",
    "mdc",
}

_SPRING_FRAMEWORK_DISPATCHER_TRIGGERS = {
    "dispatcher servlet",
    "dispatcherservlet",
    "spring mvc",
    "springmvc",
    "__dispatcher_servlet_compound__",
    "__spring_mvc_compound__",
    "__mvc_beginner_shortform__",
}

_SPRING_FRAMEWORK_TRANSACTIONAL_TRIGGERS = {
    "@transactional",
    "transactional",
    "__transaction_propagation_beginner_shortform__",
    "__spring_transaction_beginner_shortform__",
}

_SPRING_FRAMEWORK_IOC_DI_TRIGGERS = {
    "ioc",
    "di",
    "di vs ioc",
    "di ioc",
    "dependency injection",
    "의존성 주입",
    "inversion of control",
    "제어 역전",
    "제어의 역전",
}

_SPRING_FRAMEWORK_COMPONENT_SCAN_TRIGGERS = {
    "component scan",
    "componentscan",
    "@componentscan",
    "컴포넌트 스캔",
    "컴포넌트스캔",
}

_SPRING_FRAMEWORK_AOP_TRIGGERS = {
    "aop",
    "spring aop",
    "관점 지향 프로그래밍",
    "횡단 관심사",
}

_SPRING_FRAMEWORK_JPA_TRIGGERS = {
    "spring data jpa",
    "jpa",
    "hibernate",
    "entitymanager",
}

_SPRING_FRAMEWORK_SECURITY_TRIGGERS = {
    "spring security",
    "filter chain",
}

_SPRING_FOUNDATION_FLOW_TOPIC_CUES = {
    "bean",
    "빈",
    "applicationcontext",
    "application context",
    "beanfactory",
    "bean factory",
}

_SPRING_FOUNDATION_FLOW_CUES = {
    "flow",
    "흐름",
    "registration",
    "등록",
    "registration flow",
    "등록 흐름",
    "bean registration",
}

_SPRING_FOUNDATION_ROLE_CUES = {
    "뭐 하는 거야",
    "뭐하는 거야",
    "무슨 역할",
}

_SPRING_FOUNDATION_ADVANCED_CUES = {
    "override",
    "overriding",
    "semantics",
    "collision",
    "conflict",
    "precedence",
    "merge",
}

_SPRING_BEGINNER_ENGLISH_MEANING_TOPIC_CUES = {
    "spring bean",
    "beanfactory",
    "bean factory",
    "applicationcontext",
    "application context",
    "component scan",
    "componentscan",
    "@componentscan",
}

_BEGINNER_INTENT_PHRASES = {
    "처음 배우",
    "처음 보",
    "입문자",
    "입문용",
    "입문 관점",
    "감이 안 와",
    "감이 안와",
    "감이 안 온",
    "기초",
    "기초부터",
    "기본부터",
    "기본 개념",
    "큰 그림",
    "basics",
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

_BEGINNER_CONFUSION_CUES = {
    "모르겠",
    "헷갈",
}

_BEGINNER_SHORTFORM_QUESTION_CUES = {
    "뭐야",
    "뭔데",
    "뭔데요",
    "뭐예요",
    "뭐 하는 거야",
    "뭐하는 거야",
    "무슨 역할",
    "어디에 써",
    "무엇",
    "무슨 뜻이야",
    "무슨 뜻이에요",
    "what is",
    "what's",
    "why use",
    "why do we use",
    "why should i use",
    "차이가 뭐야",
    "차이가 뭐예요",
    "뭐가 달라",
    "뭐가 다른데",
}

_BEGINNER_WHY_USE_SHORTFORM_CUES = {
    "왜 써",
    "왜 사용",
    "왜 있어",
    "왜 필요해",
    "왜 필요하지",
    "왜 쓰는",
    "왜 쓰죠",
}

_KOREAN_DEFINITION_SHORTFORM_RE = re.compile(
    r"(?:^|[\s(])[\w@./+-]+(?:이란|란)(?:\?|$|[\s)])"
)

_TRANSACTIONAL_BEGINNER_WHY_USE_CUES = {
    "why use @transactional",
    "why use transactional",
    "why should i use @transactional",
    "why should i use transactional",
    "why do we use @transactional",
    "why do we use transactional",
}

_TRANSACTIONAL_BEGINNER_PLAIN_ALIAS_CUES = {
    "what is transactional",
    "what's transactional",
    "what does transactional mean",
}

_TRANSACTIONAL_BEGINNER_MECHANICS_CUES = {
    "how does @transactional work",
    "how does transactional work",
    "how @transactional works",
    "how transactional works",
}

_AUTH_BEGINNER_MEANING_CUES = {
    "what does jwt mean",
    "what does session mean",
    "what does cookie mean",
}

_AUTH_LOGIN_MEMORY_CUES = {
    "로그인 기억",
    "브라우저가 로그인",
    "브라우저가 기억",
    "왜 기억해",
    "왜 기억하지",
    "왜 기억돼",
    "왜 기억되",
    "기억돼",
    "기억되",
    "remember my login",
    "browser remembers my login",
    "still logged in",
    "stay logged in",
    "keep me signed in",
}

_AUTH_HTTP_STATELESS_CUES = {
    "http",
    "stateless",
    "상태 없",
    "상태가 없",
    "상태를 안",
}

_JWT_VALIDATION_ORDER_CUES = {
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
}

_WOOWA_BACKEND_FOUNDATION_TOPIC_CUES = {
    "dispatcherservlet",
    "dispatcher servlet",
    "mvc",
    "spring bean",
    "bean",
    "beanfactory",
    "bean factory",
    "applicationcontext",
    "application context",
    "빈",
    "컴포넌트 스캔",
    "컴포넌트스캔",
    "keep-alive",
    "keep alive",
    "keepalive",
    "persistent connection",
    "connection reuse",
    "connection pool",
    "connection pooling",
    "@transactional",
    "transactional",
    "di vs ioc",
    "di ioc",
    "di와 ioc",
    "ioc",
    "dependency injection",
    "inversion of control",
    "의존성 주입",
    "제어의 역전",
    "aop",
    "spring aop",
    "횡단 관심사",
    "session vs jwt",
    "session",
    "jwt",
    "cookie",
    "cookies",
    "쿠키",
    "세션",
}

_DATABASE_MODELING_BEGINNER_TOPIC_CUES = {
    "normalization",
    "정규화",
    "index",
    "인덱스",
    "database normalization",
    "database index",
    "db index",
}

_TRANSACTIONAL_ADVANCED_CUES = {
    "propagation",
    "isolation",
    "rollbackfor",
    "self invocation",
    "self-invocation",
    "remote call",
}

_TRANSACTION_PRIMER_SHORTFORM_TOPIC_CUES = {
    "mvcc",
    "격리 수준",
    "격리수준",
    "isolation level",
    "optimistic lock",
    "pessimistic lock",
    "낙관적 락",
    "비관적 락",
}

_TRANSACTION_PRIMER_SHORTFORM_ADVANCED_CUES = {
    "read view",
    "undo chain",
    "undo log",
    "history list",
    "version chain",
    "gap lock",
    "next-key lock",
    "next key lock",
    "deadlock",
    "데드락",
    "lock ordering",
}

_JAVA_CONCURRENCY_BEGINNER_SHORTFORM_TOPIC_CUES = {
    "callable",
    "executorservice",
    "future",
    "completablefuture",
    "countdownlatch",
    "cyclicbarrier",
    "phaser",
    "stampedlock",
}

_TRANSACTION_PRIMER_CONCEPT_EXPLANATION_CUES = {
    "개념 설명",
    "개념만 설명",
    "개념부터 설명",
    "기초 개념",
}

_PROJECTION_FRESHNESS_PRIMER_CUES = {
    "read model freshness",
    "read model staleness",
    "projection freshness",
    "읽기 모델 최신성",
    "읽기 모델 최신성을",
    "read-your-writes",
    "read your writes",
    "stale read",
    "stale reads",
    "old value",
    "old values",
    "old data after write",
    "saved but still old data",
    "saved but old data",
    "예전 값이 보임",
    "예전 값이 보여",
    "예전 값이 왜 보이는지",
    "예전 값이 왜 보여",
    "옛값이 보임",
    "옛값이 보여",
    "옛값이 왜 보이는지",
    "옛값이 왜 보여",
    "옛값만 보여",
    "옛 값이 보임",
    "옛 값이 보여",
    "쓴 직후 읽기",
    "방금 저장했는데 안 보여",
    "방금 저장했는데 안 보임",
    "저장했는데 안 보여",
    "저장했는데 안 보임",
    "저장했는데 옛값이 보인다",
    "저장 직후 조회",
    "저장 직후 조회하면 예전 데이터가 보임",
    "저장 직후 예전 값이 보이",
    "저장 직후 예전 값이 왜 보이",
    "저장 직후 목록 최신화가 안 됨",
    "저장했는데 목록이 그대로",
    "수정했는데 화면엔 예전 목록이 보여",
    "저장한 뒤 화면 반영이 늦음",
    "저장했는데 화면이 캐시된 것처럼 안 바뀌어",
    "저장했는데 화면이 캐시된 것 같아",
    "저장 후 화면이 캐시된 것 같아",
    "저장 후 화면이 캐시된 것처럼 보여",
    "저장하고 나서 화면이 캐시된 것처럼 보여",
    "목록이 바로 안 바뀌고",
    "예전 화면이 잠깐 보여",
    "새로고침 전까지 이전 상태가 보이고",
    "화면 반영이 한참 늦어",
    "목록 새로고침이 느림",
    "목록 새로고침이 느리고",
    "리스트가 늦게 갱신",
    "리스트가 늦게 갱신되고",
    "이전 화면 상태가 남아",
    "예전 상태가 남아 보여",
    "old screen state",
    "list refresh lag",
    "refresh lag",
    "저장했는데 옛값이 보임",
    "예전 데이터가 보임",
    "저장한 값이 안 보여",
    "저장한 값이 안 보임",
    "방금 쓴 값이 안 보임",
    "저장은 됐는데 조회가 달라",
    "저장했는데 화면이 캐시된 것처럼 안 바뀌어",
    "저장했는데 화면이 캐시된 것 같아",
    "저장 후 화면이 캐시된 것 같아",
    "저장 후 화면이 캐시된 것처럼 보여",
    "저장하고 나서 화면이 캐시된 것처럼 보여",
    "수정했는데 목록은 그대로야",
    "목록이 안 바뀜",
    "방금 쓴 값 읽기",
    "오래된 값 조회",
    "삭제는 성공했는데 목록에 계속 남아 보여",
    "삭제했는데 목록에 남아",
    "삭제했는데 목록에 계속 보여",
    "삭제는 성공했는데 검색 결과에 아직 남아 있어",
    "삭제했는데 검색 결과에 남아",
    "삭제했는데 검색 결과에 아직 남아 있어",
    "삭제했는데 검색 결과나 목록에 아직 남아 있어",
    "삭제했는데 검색에 계속 보여",
    "지웠는데 목록에 남아",
    "지웠는데 검색 결과에 남아",
    "delete succeeded but still appears in list",
    "delete succeeded but still appears in search",
    "deleted item still appears in list",
    "deleted item still appears in search",
    "컷 오버 안전 윈도우",
    "컷 오버 안전 구간",
    "컷오버 안전 윈도우",
    "컷오버 안전 구간",
    "전환 안전 윈도우",
    "전환 안전 구간",
}

_PROJECTION_MINIMAL_STALE_AFTER_SAVE_CUES = {
    "stale read",
    "stale reads",
    "old value",
    "old values",
    "saved but old data",
    "방금 저장했는데 안 보여",
    "방금 저장했는데 안 보임",
    "저장했는데 안 보여",
    "저장했는데 안 보임",
    "저장했는데 옛값이 보인다",
    "저장했는데 옛값이 보임",
    "저장했는데 안 보이고",
    "옛값이 보여",
    "옛값만 보여",
    "이전 화면 상태가 남아 있어",
    "저장한 값이 안 보여",
    "저장한 값이 안 보임",
    "방금 쓴 값이 안 보임",
    "저장은 됐는데 조회가 달라",
    "수정했는데 목록은 그대로야",
    "목록이 안 바뀜",
    "삭제는 성공했는데 목록에 계속 남아 보여",
    "삭제했는데 목록에 남아",
    "삭제했는데 목록에 계속 보여",
    "삭제는 성공했는데 검색 결과에 아직 남아 있어",
    "삭제했는데 검색 결과에 남아",
    "삭제했는데 검색 결과에 아직 남아 있어",
    "삭제했는데 검색 결과나 목록에 아직 남아 있어",
    "삭제했는데 검색에 계속 보여",
    "지웠는데 목록에 남아",
    "지웠는데 검색 결과에 남아",
    "delete succeeded but still appears in list",
    "delete succeeded but still appears in search",
    "deleted item still appears in list",
    "deleted item still appears in search",
}

_PROJECTION_DETAIL_LIST_SPLIT_DETAIL_CUES = {
    "상세는 바뀌었는데",
    "상세 화면은 바뀌었는데",
    "상세 화면은 바뀌었는데도",
    "디테일은 바뀌었는데",
    "detail은 바뀌었는데",
    "detail view updated",
    "detail page updated",
}

_PROJECTION_DETAIL_LIST_SPLIT_LIST_CUES = {
    "목록은 예전 값",
    "목록은 이전 값",
    "리스트는 예전 값",
    "리스트는 이전 값",
    "목록 카드만 예전 값",
    "목록 카드만 이전 값",
    "리스트 카드만 예전 값",
    "리스트 카드만 이전 값",
    "목록은 옛값",
    "리스트는 옛값",
    "목록 카드만 옛값",
    "리스트 카드만 옛값",
    "list still old value",
    "list card still old value",
    "list card stale",
}

_PROJECTION_ROLLBACK_WINDOW_CUES = {
    "rollback window",
    "rollback windows",
    "롤백 윈도우",
}

_PROJECTION_CUTOVER_SAFETY_WINDOW_CUES = {
    "cutover safety window",
    "cutover safety windows",
    "safety window",
    "safety windows",
    "컷 오버 안전 윈도우",
    "컷 오버 안전 구간",
    "컷오버 안전 윈도우",
    "컷오버 안전 구간",
    "전환 안전 윈도우",
    "전환 안전 구간",
}

_PROJECTION_STRICT_READ_ROUTE_CUES = {
    "session pinning",
    "세션 피닝",
    "세션 고정",
    "strict read",
    "strict reads",
    "strict screen",
    "strict screens",
    "strict window",
    "cross screen",
    "cross-screen",
    "actor scoped",
    "actor-scoped",
}

_PROJECTION_STRICT_READ_GATE_CUES = {
    "expectedversion",
    "expected version",
    "version gate",
    "version gated",
    "version-gated",
    "projection version gate",
    "watermark gate",
    "watermark gated",
    "watermark-gated",
}

_PROJECTION_TRANSACTION_ROLLBACK_CUES = {
    "transaction rollback",
    "트랜잭션 rollback",
    "트랜잭션 롤백",
}

_PROJECTION_TX_CONTRAST_CUES = {
    "차이",
    "비교",
    "구분",
    "헷갈",
    "vs",
    "versus",
    "compare",
    "contrast",
}

_PROJECTION_OPERATIONAL_COMPARISON_CUES = {
    "차이",
    "비교",
    "구분",
    "구별",
    "헷갈",
    "vs",
    "versus",
    "compare",
    "contrast",
    "difference",
    "different",
    "다른지",
    "뭐가 다른지",
    "어떻게 다른지",
}

_PROJECTION_SLO_CUES = {
    "projection freshness slo",
    "freshness slo",
    "최신성 slo",
    "최신성 서비스 수준 목표",
    "서비스 수준 목표",
}

_PROJECTION_LAG_BUDGET_CUES = {
    "projection lag budget",
    "lag budget",
    "지연 예산",
    "반영 지연 예산",
    "반영 지연 허용 범위",
    "지연 허용 범위",
    "허용 지연 범위",
}

_PROJECTION_ADVANCED_SLO_TUNING_CUES = {
    "freshness sli",
    "lag breach",
    "breach policy",
    "error budget",
    "consumer backlog budget",
    "projection watermark",
    "watermark gap",
    "slo tuning",
}

_PROJECTION_REBUILD_PLAYBOOK_CUES = {
    "projection rebuild",
    "rebuild",
    "backfill",
    "프로젝션 재빌드",
    "프로젝션 백필",
    "재빌드",
    "백필",
    "재구축",
    "projection rebuild backfill cutover playbook",
    "rebuild backfill playbook",
    "rebuild playbook",
    "backfill playbook",
    "프로젝션 재빌드 백필 컷오버 문서",
    "프로젝션 재빌드 백필 컷오버 안내",
    "프로젝션 재빌드 백필 컷오버 플레이북",
}

_PROJECTION_CACHE_CONFUSION_CUES = {
    "캐시인지",
    "캐시 때문",
    "캐시 탓",
    "캐시 문제",
    "캐시된 것처럼",
    "캐시된 것 같",
    "cache 때문",
    "cache 탓",
    "cache issue",
    "is it cache",
}

_PROJECTION_CACHED_SCREEN_SAVE_CUES = {
    "저장",
    "수정",
    "업데이트",
    "saved",
    "save",
    "updated",
    "update",
    "write",
}

_PROJECTION_CACHED_SCREEN_VIEW_CUES = {
    "화면",
    "screen",
}

_PROJECTION_CACHED_SCREEN_STALE_CUES = {
    "안 바뀌",
    "그대로",
    "예전",
    "이전",
    "옛값",
    "old",
    "남아",
    "보여",
}

_PROJECTION_MOBILE_APP_CUES = {
    "앱",
    "어플",
    "모바일",
    "mobile",
    "app",
}

_PROJECTION_MOBILE_REFRESH_GESTURE_CUES = {
    "당겨서 새로고침 한 번 해야",
    "당겨서 새로고침",
    "당겨 새로고침",
    "당겨 내려야",
    "내려서 새로고침",
    "새로고침 쓸어내리고",
    "새로고침 끌어내리고",
    "스와이프 새로고침",
    "스와이프해서 새로고침",
    "스와이프해 새로고침",
    "스와이프 새로고침하고 나서야",
    "스와이프해서 새로고침하고 나서야",
    "스와이프 리프레시",
    "쓸어내려 새로고침",
    "쓸어내리고 나서야",
    "끌어내려 새로고침",
    "끌어내리고 나서야",
    "pull down refresh",
    "swipe refresh",
    "swipe-refresh",
    "swipe to refresh",
    "swipe-to-refresh",
    "pull to refresh",
    "pull-to-refresh",
}

_PROJECTION_MOBILE_DELAY_VIEW_CUES = {
    "화면",
    "screen",
    "목록",
    "리스트",
    "list",
    "카드",
    "card",
}

_PROJECTION_MOBILE_DELAY_STALE_CUES = {
    "안 바뀌",
    "안 보여",
    "안 보임",
    "바로 안 보여",
    "바로 안 보임",
    "바로 반영 안",
    "반영 안 돼",
    "반영이 안",
    "반영 지연",
    "늦어",
    "늦게",
    "느려",
    "한참",
    "지연",
    "lag",
    "delay",
    "밀려",
    "남아",
    "그대로",
    "갱신돼",
    "갱신이 안",
    "갱신이 느려",
    "최신 값이 보여",
    "최신 화면으로 바뀌어",
    "새 값이 보여",
    "바뀐 값이 보여",
    "화면이 따라와",
}

_PROJECTION_MOBILE_REFRESH_VALUE_CUES = {
    "최신 값",
    "최신 화면",
    "새 값",
    "바뀐 값",
    "갱신",
    "갱신돼",
    "업데이트",
    "반영",
    "new value",
    "updated value",
}

_PROJECTION_REPLICA_DISAMBIGUATION_CUES = {
    "replica",
    "replica lag",
    "read replica",
    "리플리카",
}

_PROJECTION_DISAMBIGUATION_CONFUSION_CUES = {
    "모르겠",
    "헷갈",
    "구분",
    "차이",
    "vs",
}

_PROJECTION_APPLICATION_CACHE_CONTEXT_CUES = {
    "application",
    "app",
    "real",
    "actual",
    "redis",
    "caffeine",
    "local cache",
    "service cache",
    "cache eviction",
    "cache evict",
}

_GENERIC_CRUD_KOREAN_READ_CUES = {
    "조회",
    "read",
    "list",
    "목록",
}

_GENERIC_CRUD_KOREAN_WRITE_CUES = {
    "수정",
    "update",
    "삭제",
    "delete",
}

_GENERIC_CRUD_KOREAN_SCOPE_CUES = {
    "crud",
    "api",
    "rest",
    "회원",
    "soft delete",
    "hard delete",
    "service",
    "controller",
}

_GENERIC_CRUD_KOREAN_FRESHNESS_EXCLUSION_CUES = {
    "예전",
    "옛값",
    "old value",
    "stale",
    "lag",
    "새로고침",
    "반영",
    "read-your-writes",
    "read your writes",
    "projection",
    "읽기 모델",
}

_PROJECTION_CACHE_COMPARE_ENTRYPOINT_CUES = {
    "projection lag",
    "read model",
}

_PROJECTION_FILTER_SORT_STATE_CUES = {
    "filter",
    "filter state",
    "filtering",
    "sort",
    "sort state",
    "sorting",
    "검색 조건",
    "로컬 상태",
    "브라우저 필터",
    "브라우저 정렬",
    "정렬",
    "정렬 기준",
    "클라이언트 필터",
    "클라이언트 정렬",
    "탭 상태",
    "필터",
    "필터 상태",
}

_QUERY_MODEL_BEGINNER_FILTER_SORT_SCOPE_CUES = {
    "list",
    "목록",
    "query",
    "query model",
    "search",
    "검색",
    "조건",
}

_QUERY_MODEL_BEGINNER_MEANING_TOPIC_CUES = {
    "query model",
    "query service",
}

_QUERY_MODEL_BEGINNER_MEANING_ADVANCED_CUES = {
    "aggregate",
    "aggregate persistence",
    "join dto",
    "remote lookup",
    "anti-pattern",
    "anti pattern",
    "cqrs",
    "projection",
    "eventual consistency",
}

_PROJECTION_BACKEND_FRESHNESS_ANCHOR_CUES = {
    "cqrs",
    "eventual consistency",
    "projection",
    "projection lag",
    "read model",
    "read your writes",
    "read-your-writes",
    "replica",
    "replica lag",
    "쓴 직후 읽기",
    "읽기 모델",
    "프로젝션",
}

_PROJECTION_TX_NOISE_TRIGGERS = {
    "rollback",
    "transaction",
    "트랜잭션",
    "commit",
}

_PROJECTION_BEGINNER_OPERATIONAL_NOISE_TAGS = {
    "migration_repair_cutover",
    "global_failover_control_plane",
    "stateful_failover_placement",
    "failover_visibility",
    "failover_verification",
    "security_key_rotation_rollover",
    "security_key_rotation_runbook",
    "security_jwks_recovery",
}

_PROJECTION_BEGINNER_OPERATIONAL_CONTRAST_EXPANSION_TAGS = {
    "global_failover_control_plane",
    "stateful_failover_placement",
    "failover_visibility",
    "failover_verification",
}

_PROJECTION_BEGINNER_FAILOVER_CONTRAST_EXPAND_OVERRIDES: dict[str, list[str]] = {
    "global_failover_control_plane": [
        "global traffic failover",
        "control plane",
    ],
    "stateful_failover_placement": [
        "stateful workload placement",
        "failover control plane",
        "placement budget",
    ],
    "failover_visibility": [],
    "failover_verification": [
        "commit horizon after failover",
    ],
}

_FAILOVER_VISIBILITY_OPERATIONAL_CUES = {
    "visibility window",
    "topology cache",
    "cache invalidation",
    "topology invalidation",
    "freshness fence",
    "stale endpoint",
    "dns ttl",
    "cache bust",
    "pinning",
}

_PROJECTION_BEGINNER_ROLLBACK_CONTRAST_EXPAND_OVERRIDES: dict[str, list[str]] = {
    "global_failover_control_plane": [
        "failover rollback",
        "failover",
    ],
    "security_key_rotation_runbook": [
        "key rotation rollback",
        "key rotation",
    ],
}

_PROJECTION_BEGINNER_NOISE_PROTECTED_TOKENS = {
    "cutover",
    "freshness",
    "model",
    "old",
    "projection",
    "read",
    "reads",
    "rollback",
    "safe",
    "safety",
    "stale",
    "window",
    "windows",
}

_TRANSACTION_BEGINNER_INCIDENT_NOISE_TOKENS = {
    "commit",
    "incident",
    "failure",
    "primer",
    "operational",
    "triage",
    "debugging",
    "debug",
    "card",
}

_TRANSACTION_BEGINNER_INCIDENT_SPRING_PROTECTED_CUES = {
    "spring",
    "@transactional",
    "transactional",
    "rollbackonly",
    "rollback-only",
    "unexpectedrollbackexception",
    "requires_new",
    "requires new",
    "jpa",
    "hibernate",
}

_BEGINNER_PRIMER_OVERRIDES: dict[str, dict[str, object]] = {
    "spring_framework": {
        "score_bonus": 2,
        "suppress": {"api_boundary"},
    },
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
    "java_completablefuture_cancellation": {
        "expand": [
            "completablefuture cancellation basics",
            "cancel does not stop work",
            "cancel vs timeout basics",
            "interrupt vs cancellation",
        ],
        "score_bonus": 2,
    },
    "java_completablefuture_fan_in_timeout": {
        "expand": [
            "completablefuture allof join basics",
            "allof does not collect results",
            "join wraps exceptions",
            "timeout exceptional completion basics",
        ],
        "score_bonus": 3,
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
    "java_structured_concurrency": {
        "expand": [
            "structured concurrency basics",
            "structured task scope",
            "scope bound context",
            "fail-fast task group",
        ],
        "score_bonus": 3,
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
    "network_keepalive_basics": {
        "expand": [
            "keep-alive basics",
            "http connection reuse",
        ],
        "score_bonus": 2,
    },
    "connection_pool_basics": {
        "expand": [
            "db connection pool beginner",
            "hikari cp beginner",
            "pool size basics",
        ],
        "score_bonus": 2,
        "suppress": {"resource_lifecycle"},
    },
    "db_modeling": {
        "expand": [
            "database fundamentals for beginners",
        ],
        "score_bonus": 2,
        "suppress": {"java_value_canonicalization"},
    },
    "transaction_isolation": {
        "expand": [
            "transaction isolation basics",
            "transaction isolation beginner primer",
            "transaction isolation simple mental model",
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
            "anomaly overview",
            "isolation level",
            "transaction isolation basics",
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
            "list refresh lag after write",
            "old screen state after save",
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


def _is_transaction_isolation_beginner_meaning_prompt(
    haystack: str,
    tokens: set[str],
) -> bool:
    if not (_has_beginner_intent(haystack, tokens) or _has_beginner_confusion_intent(haystack)):
        return False
    if not any(cue in haystack for cue in _TRANSACTION_PRIMER_SHORTFORM_TOPIC_CUES):
        return False
    if any(cue in haystack for cue in _TRANSACTION_PRIMER_SHORTFORM_ADVANCED_CUES):
        return False
    if any(
        cue in haystack
        for cue in {
            "optimistic lock",
            "pessimistic lock",
            "낙관적 락",
            "비관적 락",
            "select for update",
            "for update",
            "locking strategy",
        }
    ):
        return False
    return (
        any(cue in haystack for cue in _BEGINNER_SHORTFORM_QUESTION_CUES)
        or _has_korean_definition_shortform(haystack)
        or any(cue in haystack for cue in _TRANSACTION_PRIMER_CONCEPT_EXPLANATION_CUES)
        or _has_beginner_confusion_intent(haystack)
        or "큰 그림" in haystack
    )


def _transaction_isolation_expand(
    haystack: str,
    tokens: set[str],
    matched_triggers: set[str],
    *,
    beginner_intent: bool = False,
) -> list[str]:
    expand = [
        "transaction",
        "isolation level",
        "locking strategy",
        "optimistic lock",
        "pessimistic lock",
        "rollback",
    ]

    if beginner_intent:
        expand.extend(
            [
                "transaction isolation basics",
                "mvcc",
                "dirty read",
                "non-repeatable read",
                "phantom read",
                "read committed",
                "repeatable read",
            ]
        )

    if _is_mvcc_beginner_why_use_prompt(haystack):
        return [
            "transaction isolation basics",
            "transaction isolation beginner primer",
            "transaction isolation simple mental model",
            "mvcc",
            "mvcc basics",
            "mvcc beginner",
            "mvcc concept overview",
            "why use mvcc",
            "concurrent read write visibility basics",
        ]

    if _is_transaction_isolation_beginner_meaning_prompt(haystack, tokens):
        expand = [
            "transaction isolation basics",
            "transaction isolation beginner primer",
            "transaction isolation simple mental model",
            "transaction isolation level basics",
            "isolation level beginner",
            "read committed beginner",
            "repeatable read beginner",
            "serializable beginner",
            "dirty read beginner",
            "트랜잭션 격리 수준 처음 배우는데",
            "격리 수준이 뭐예요",
            "동시에 실행될 때 무엇이 보이는지",
            "mvcc",
        ]
        if "mvcc" in haystack:
            expand.extend(
                [
                    "mvcc 개념 설명",
                    "mvcc 처음 배우는데",
                    "mvcc beginner",
                    "read committed",
                    "repeatable read",
                    "phantom read",
                ]
            )

    if matched_triggers & {
        "locking",
        "optimistic",
        "pessimistic",
        "for update",
        "serializable",
    }:
        expand.extend(
            [
                "locking strategy",
                "optimistic lock",
                "pessimistic lock",
            ]
        )

    return expand


def _db_modeling_expand(
    haystack: str,
    tokens: set[str],
    matched_triggers: set[str],
    *,
    beginner_intent: bool = False,
) -> list[str]:
    del haystack, tokens
    expand = ["schema design", "normalization", "index", "primary key"]

    if not beginner_intent:
        return expand

    beginner_expand = ["database schema basics", "db modeling beginner", "큰 그림"]
    if matched_triggers & {"정규화", "normalization"}:
        beginner_expand.extend(
            [
                "database normalization basics",
                "normal form basics",
                "1nf 2nf 3nf",
                "정규화 기초",
                "정규화 큰 그림",
            ]
        )
    if matched_triggers & {"index", "인덱스"}:
        beginner_expand.extend(
            [
                "database index basics",
                "b-tree basics",
                "index lookup beginner",
                "인덱스 기초",
                "인덱스 큰 그림",
            ]
        )
    return beginner_expand + expand


def _connection_pool_expand(
    haystack: str,
    matched_triggers: set[str],
    *,
    beginner_intent: bool = False,
) -> list[str]:
    beginner_hikari_shortform = bool(
        matched_triggers & {"hikari", "hikari cp"}
        and (
            any(cue in haystack for cue in _BEGINNER_SHORTFORM_QUESTION_CUES)
            or any(cue in haystack for cue in _BEGINNER_WHY_USE_SHORTFORM_CUES)
            or _has_beginner_confusion_intent(haystack)
        )
    )
    expand = [
        "connection pool basics",
        "db connection reuse",
        "hikari cp",
        "pool exhaustion",
        "connection timeout",
    ]

    if beginner_intent or beginner_hikari_shortform:
        expand.extend(
            [
                "db connection pool beginner",
                "hikari cp beginner",
                "pool size basics",
            ]
        )

    if matched_triggers & {"hikari", "hikari cp"} and (beginner_intent or beginner_hikari_shortform):
        expand.extend(
            [
                "hikaricp basics",
                "hikaricp connection pool overview",
            ]
        )

    return expand


def _has_spring_foundation_english_role_intent(
    haystack: str,
    matched_triggers: set[str],
) -> bool:
    if not (
        matched_triggers
        & {"beanfactory", "bean factory", "applicationcontext", "application context", "bean"}
    ):
        return False
    return bool(
        re.search(
            r"\bwhat\s+does\s+(?:a\s+)?(?:spring\s+)?"
            r"(?:beanfactory|bean\s+factory|applicationcontext|application\s+context|bean)\s+do\b",
            haystack,
        )
    )


def _spring_framework_expand(
    haystack: str,
    matched_triggers: set[str],
    *,
    beginner_intent: bool = False,
) -> list[str]:
    expand = [
        "spring",
        "spring boot",
        "bean lifecycle",
    ]

    if matched_triggers & _SPRING_FRAMEWORK_DISPATCHER_TRIGGERS:
        expand.extend(
            [
                "dispatcher servlet",
                "spring request pipeline beginner",
                "dispatcher servlet beginner",
                "bean container foundation",
                "controller service repository roles",
            ]
        )
        if beginner_intent:
            expand.extend(
                [
                    "spring request pipeline bean container foundations primer",
                    "dispatcher servlet bean container big picture",
                    "spring mvc beginner mental model",
                    "요청 처리 흐름",
                    "객체 준비 흐름",
                    "bean 컨테이너 큰 그림",
                ]
            )
            if (
                matched_triggers
                & {"dispatcher servlet", "dispatcherservlet", "__dispatcher_servlet_compound__"}
            ) and (
                matched_triggers
                & {"spring mvc", "springmvc", "__spring_mvc_compound__", "__mvc_beginner_shortform__"}
            ):
                expand.extend(
                    [
                        "dispatcher servlet vs spring mvc",
                        "front controller vs mvc mental model",
                        "dispatcher servlet handles request routing",
                        "spring mvc is the web stack big picture",
                    ]
                )

    if matched_triggers & _SPRING_FRAMEWORK_TRANSACTIONAL_TRIGGERS:
        if beginner_intent:
            expand.extend(
                [
                    "spring transactional basics",
                    "@transactional",
                    "transactional annotation how it works",
                    "transactional annotation basics",
                    "transactional method beginner",
                    "spring proxy transaction",
                    "unchecked exception rollback",
                    "checked exception rollback",
                    "rollbackfor",
                    "self invocation transactional",
                ]
            )
            if "propagation" in haystack or "전파" in haystack:
                expand.extend(
                    [
                        "transaction propagation basics",
                        "propagation behavior basics",
                    ]
                )
        else:
            expand.extend(
                [
                    "spring transaction",
                    "transactional deep dive",
                    "transaction propagation",
                    "service layer transaction boundary patterns",
                    "remote call transaction boundary",
                ]
            )
            if "propagation" in haystack:
                expand.extend(
                    [
                        "propagation behavior",
                        "required",
                        "requires new",
                        "requires_new",
                        "nested transaction",
                    ]
                )

    if matched_triggers & _SPRING_FRAMEWORK_IOC_DI_TRIGGERS:
        expand.extend(
            [
                "spring ioc di basics",
                "dependency injection",
                "inversion of control",
            ]
        )
        if beginner_intent:
            expand.extend(
                [
                    "spring ioc di beginner primer",
                    "ioc 제어 역전 입문",
                    "dependency injection 입문",
                    "의존성 주입이 뭐예요",
                    "spring 객체 조립 컨테이너",
                    "테스트하기 좋은 코드 di",
                ]
            )

    if matched_triggers & _SPRING_FRAMEWORK_COMPONENT_SCAN_TRIGGERS:
        expand.extend(
            [
                "component scan basics",
                "spring component scan basics",
            ]
        )
        if (
            beginner_intent
            or any(cue in haystack for cue in _BEGINNER_SHORTFORM_QUESTION_CUES)
            or any(cue in haystack for cue in _BEGINNER_WHY_USE_SHORTFORM_CUES)
        ):
            expand.extend(
                [
                    "spring bean di basics",
                    "component scan beginner mental model",
                    "springbootapplication basics",
                    "bean registration vs component scan",
                    "component scan candidate discovery",
                ]
            )

    if matched_triggers & _SPRING_FRAMEWORK_AOP_TRIGGERS:
        if beginner_intent:
            expand.extend(
                [
                    "spring aop basics",
                    "aop basics",
                    "why use spring aop",
                    "spring aop beginner overview",
                    "aspect oriented programming basics",
                    "proxy aop beginner",
                    "cross-cutting concern",
                    "why use aop",
                    "self invocation internal call",
                ]
            )
        else:
            expand.extend(
                [
                    "aop proxy mechanism",
                    "advisor pointcut advice",
                    "self invocation proxy bypass",
                ]
            )

    if beginner_intent and matched_triggers & {
        "bean",
        "빈",
        "beanfactory",
        "bean factory",
        "applicationcontext",
        "application context",
    }:
        expand.extend(
            [
                "spring bean basics",
                "bean container foundation",
                "applicationcontext basics",
                "beanfactory basics",
                "bean definition",
                "bean registration basics",
                "beanfactory vs applicationcontext",
                "applicationcontext extends beanfactory",
                "applicationcontext beginner mental model",
                "spring request pipeline bean container foundations primer",
                "요청 처리 흐름",
                "객체 준비 흐름",
                "bean 컨테이너 큰 그림",
            ]
        )
        if any(cue in haystack for cue in _SPRING_FOUNDATION_ROLE_CUES) or (
            _has_spring_foundation_english_role_intent(haystack, matched_triggers)
        ):
            expand.extend(
                [
                    "spring bean role basics",
                    "applicationcontext role basics",
                    "beanfactory role basics",
                    "spring bean what it does",
                    "applicationcontext what it does",
                    "빈이 하는 일",
                    "beanfactory 역할",
                    "applicationcontext 역할",
                ]
            )

    if matched_triggers & _SPRING_FRAMEWORK_JPA_TRIGGERS:
        expand.extend(
            [
                "spring data jpa",
                "hibernate",
                "jpa",
            ]
        )

    if matched_triggers & _SPRING_FRAMEWORK_SECURITY_TRIGGERS:
        expand.extend(
            [
                "spring security filter chain",
            ]
        )

    if beginner_intent and len(expand) <= 3:
        expand.append("spring fundamentals for beginners")

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

    if beginner_intent and matched_triggers & {
        "executorservice",
        "future",
        "callable",
        "completablefuture",
        "countdownlatch",
    }:
        expand.extend(
            [
                "java concurrency utilities overview",
                "executorservice callable future overview",
                "future vs completablefuture basics",
                "countdownlatch coordination basics",
            ]
        )

    return expand


def _java_completablefuture_cancellation_expand(
    matched_triggers: set[str],
    *,
    beginner_intent: bool = False,
) -> list[str]:
    expand = [
        "completablefuture cancellation",
        "cancellationexception",
        "cooperative cancellation",
        "interrupt",
        "exceptional completion",
    ]

    if beginner_intent:
        expand.extend(
            [
                "completablefuture cancellation basics",
                "cancel does not stop work",
                "cancel vs timeout basics",
                "interrupt vs cancellation",
            ]
        )
    else:
        expand.extend(
            [
                "mayinterruptifrunning",
                "dependent stage cancellation propagation",
                "timeout semantics",
            ]
        )

    if matched_triggers & {"propagation", "dependent stage"}:
        expand.extend(
            [
                "dependent stage",
                "cancellation propagation",
            ]
        )

    if matched_triggers & {"interrupt", "interruptedexception", "mayinterruptifrunning"}:
        expand.extend(
            [
                "mayinterruptifrunning",
                "interruptedexception",
            ]
        )

    return expand


def _java_completablefuture_fan_in_timeout_expand(
    matched_triggers: set[str],
    *,
    beginner_intent: bool = False,
) -> list[str]:
    expand = [
        "completablefuture allof",
        "join vs get",
        "completionexception",
        "ortimeout",
        "exceptionally",
    ]

    if beginner_intent:
        expand.extend(
            [
                "completablefuture allof join basics",
                "allof does not collect results",
                "join wraps exceptions",
                "timeout exceptional completion basics",
            ]
        )
    else:
        expand.extend(
            [
                "completeontimeout",
                "whencomplete",
                "partial failure",
                "fan-out fan-in",
                "background task leak",
            ]
        )

    if matched_triggers & {"allof", "all of", "anyof", "any of"}:
        expand.extend(
            [
                "allof fan-in",
                "result aggregation",
            ]
        )

    if matched_triggers & {"join", "join vs get", "completionexception", "executionexception"}:
        expand.extend(
            [
                "join exception wrapper",
                "executionexception",
            ]
        )

    if matched_triggers & {
        "ortimeout",
        "or timeout",
        "completeontimeout",
        "complete on timeout",
    }:
        expand.extend(
            [
                "timeout semantics",
                "future completion vs task cancellation",
            ]
        )

    if matched_triggers & {"exceptionally", "whencomplete", "partial failure", "partial success"}:
        expand.extend(
            [
                "failure recovery boundary",
                "partial success fan-in",
            ]
        )

    return expand


def _security_authentication_expand(
    haystack: str,
    matched_triggers: set[str],
    *,
    beginner_intent: bool = False,
) -> list[str]:
    expand = [
        "authentication",
        "authorization",
        "jwt",
        "session",
    ]

    has_session_jwt_basics_intent = (
        "jwt" in matched_triggers
        and bool(matched_triggers & {"session", "세션"})
    ) or (
        "jwt" in haystack and ("session" in haystack or "세션" in haystack)
    )
    has_cookie_login_state_intent = any(
        cue in haystack
        for cue in {
            "cookie",
            "cookies",
            "쿠키",
            "로그인 상태",
            "로그인 유지",
            "왜 유지돼",
            "왜 유지되",
            "로그인 계속",
            "로그인 안 풀",
            "로그인 풀림",
            "로그인 기억",
            "브라우저가 로그인",
            "브라우저가 기억",
            "login state",
            "still logged in",
            "stay logged in",
            "logged in",
            "signed in",
            "keep me signed in",
            "browser remembers my login",
            "remember my login",
            "remember me",
        }
    )
    has_http_login_state_intent = "__http_login_state__" in matched_triggers
    has_login_state_memory_intent = "__login_state_memory__" in matched_triggers
    has_jwt_structure_intent = any(
        cue in haystack
        for cue in {
            "payload structure",
            "token payload structure",
            "claims",
            " exp ",
        }
    ) or _is_jwt_validation_order_prompt(haystack)
    has_auth_beginner_meaning_intent = (
        not has_jwt_structure_intent
        and any(cue in haystack for cue in _AUTH_BEGINNER_MEANING_CUES)
        and bool(matched_triggers & {"jwt", "session", "세션", "cookie", "cookies", "쿠키"})
    )
    has_beginner_jwt_mental_model_intent = (
        (beginner_intent or has_auth_beginner_meaning_intent)
        and not has_jwt_structure_intent
        and "jwt" in matched_triggers
    )
    has_beginner_cookie_mental_model_intent = (
        (beginner_intent or has_auth_beginner_meaning_intent)
        and not has_jwt_structure_intent
        and bool(matched_triggers & {"cookie", "cookies", "쿠키"})
    )
    has_beginner_session_mental_model_intent = (
        (beginner_intent or has_auth_beginner_meaning_intent)
        and not has_jwt_structure_intent
        and bool(matched_triggers & {"session", "세션"})
    )

    if (
        has_http_login_state_intent
        or has_login_state_memory_intent
        or
        has_cookie_login_state_intent
        or has_beginner_cookie_mental_model_intent
        or has_beginner_session_mental_model_intent
        or (has_session_jwt_basics_intent and not has_jwt_structure_intent)
    ):
        expand.extend(
            [
                "session vs jwt",
                "session cookie jwt basics",
                "cookie session jwt browser flow",
                "http stateless login state",
                "jsessionid",
                "server session vs jwt",
                "login state persistence",
                "why login stays",
            ]
        )

    if has_beginner_jwt_mental_model_intent:
        expand.extend(
            [
                "session cookie jwt basics",
                "session vs jwt",
                "http stateless login state",
                "token based authentication",
            ]
        )

    return expand


def _transaction_deadlock_expand(
    haystack: str,
    tokens: set[str],
    matched_triggers: set[str],
    *,
    beginner_intent: bool = False,
) -> list[str]:
    expand = [
        "deadlock",
        "deadlock case study",
        "lock ordering",
        "deadlock retry",
        "lock wait",
        "wait graph",
        "transaction deadlock",
        "circular wait",
        "innodb deadlock log",
    ]

    if matched_triggers & {"lock ordering", "deadlock log", "innodb deadlock log"}:
        expand.extend(
            [
                "row lock acquisition order",
                "consistent lock ordering",
                "deadlock victim retry",
            ]
        )

    if _is_deadlock_timeout_beginner_primer_prompt(
        haystack,
        tokens,
        beginner_intent=beginner_intent,
    ):
        expand.extend(
            [
                "deadlock vs lock wait timeout",
                "circular wait vs long wait",
                "deadlock victim vs timeout retry",
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


def _projection_freshness_expand(
    haystack: str,
    *,
    beginner_intent: bool = False,
) -> list[str]:
    tokens = set(_tokenize(haystack))
    cutover_shortform_prompt = _is_projection_cutover_safety_shortform_prompt(haystack)
    minimal_stale_after_save_prompt = _is_projection_minimal_stale_after_save_prompt(haystack)
    cache_vs_replica_prompt = _is_projection_cache_vs_replica_disambiguation_prompt(haystack)
    detail_list_split_prompt = _has_projection_detail_list_split_symptom(haystack)
    slo_lag_compare_prompt = _is_projection_beginner_slo_lag_compare_prompt(haystack, tokens)
    navigator_bridge_prompt = _is_projection_beginner_navigator_bridge_prompt(haystack, tokens)
    if _is_projection_rollback_window_transaction_rollback_db_prompt(
        haystack,
        beginner_intent=beginner_intent,
    ):
        return ["rollback window"]

    if not beginner_intent and any(cue in haystack for cue in _PROJECTION_SLO_CUES) and any(
        cue in haystack for cue in _PROJECTION_ADVANCED_SLO_TUNING_CUES
    ):
        return [
            "projection freshness slo",
            "projection lag budget",
            "freshness budget",
            "lag breach policy",
            "consumer backlog budget",
            "projection watermark",
            "watermark gap",
            "read your writes",
            "read model cutover guardrails",
        ]

    expand = [
        "read model staleness",
        "read your writes",
        "old data after write",
        "saved but still old data",
        "list refresh lag after write",
        "old screen state after save",
        "eventual consistency ux",
    ]

    if beginner_intent and _is_projection_strict_read_beginner_intro_prompt(haystack, tokens):
        expand.extend(
            [
                "session pinning strict read",
                "session pinning vs version gated",
                "session pinning vs version-gated strict reads",
                "expected version strict read",
                "watermark gated strict read",
                "actor scoped pinning",
                "cross screen read your writes",
            ]
        )
        return expand

    if (
        beginner_intent and _is_projection_freshness_primer_prompt(haystack)
    ) or minimal_stale_after_save_prompt:
        beginner_compare_prompt = any(
            cue in haystack for cue in _PROJECTION_OPERATIONAL_COMPARISON_CUES
        )
        if (
            beginner_intent
            and not beginner_compare_prompt
            and not cache_vs_replica_prompt
            and not any(cue in haystack for cue in _PROJECTION_CUTOVER_SAFETY_WINDOW_CUES)
            and not navigator_bridge_prompt
            and not _has_projection_cqrs_survey_rejection(haystack)
        ):
            expand.extend(
                [
                    "cqrs survey routing",
                    "schema migration partitioning cdc cqrs",
                ]
            )
        expand.extend(
            [
                "saved-but-not-visible",
                "old-screen-state",
                "쓴 직후 읽기 보장",
                "저장 직후 예전 값이 보임",
                "저장한 값이 바로 안 보임",
                "query sees old value after save",
                "read after write mismatch",
                "deleted item still visible after delete",
                "deleted item still appears in search results",
                "deleted item still appears in list results",
            ]
        )
        if detail_list_split_prompt:
            expand.extend(
                [
                    "detail view updated but list stale",
                    "detail page changed but list card stale",
                    "상세는 바뀌었는데 목록 카드만 예전 값",
                ]
            )
        if navigator_bridge_prompt:
            expand.extend(
                [
                    "read model staleness overview",
                    "read model staleness and read-your-writes",
                    "read model cutover guardrails",
                    "read model cutover guardrail sibling",
                    "projection primer sibling docs",
                    "projection lag budgeting pattern sibling",
                    "projection lag budgeting pattern",
                    "projection lag budget",
                    "freshness neighbor docs",
                    "nearby sibling docs",
                ]
            )
        if _is_projection_mobile_refresh_lag_prompt(haystack):
            expand.extend(
                [
                    "mobile screen update delay after save",
                    "swipe refresh needed to see new value",
                ]
            )
        if minimal_stale_after_save_prompt and not slo_lag_compare_prompt:
            expand.extend(
                [
                    "read-after-write",
                    "replica lag",
                    "read replica delay",
                    "primary fallback",
                ]
            )
        if cache_vs_replica_prompt:
            expand.extend(
                [
                    "cache vs replica lag",
                    "cache or replica after write",
                    "application cache vs read replica",
                    "read-after-write strategies",
                    "read-after-write diagnosis",
                ]
            )
        if beginner_compare_prompt and any(
            cue in haystack for cue in _PROJECTION_ROLLBACK_WINDOW_CUES
        ) and any(cue in haystack for cue in _PROJECTION_CUTOVER_SAFETY_WINDOW_CUES):
            expand.extend(
                [
                    "rollback window",
                    "cutover safety window",
                    "롤백 윈도우",
                    "전환 안전 구간",
                    "freshness guardrail",
                    "dual read parity",
                ]
            )
        if any(cue in haystack for cue in _PROJECTION_CUTOVER_SAFETY_WINDOW_CUES):
            expand.extend(
                [
                    "cutover safety window",
                    "projection freshness slo",
                    "projection lag budget",
                ]
            )
        if (
            (
                any(cue in haystack for cue in _PROJECTION_CUTOVER_SAFETY_WINDOW_CUES)
                or "read model cutover guardrails" in haystack
                or "cutover guardrails" in haystack
                or "guardrail" in haystack
            )
            and not cutover_shortform_prompt
        ):
            expand.extend(
                [
                    "read model cutover guardrails",
                    "freshness guardrail",
                    "dual read parity",
                    "cutover assumption checklist",
                    "pagination cutover",
                    "canary promotion threshold",
                ]
            )
        if any(cue in haystack for cue in _PROJECTION_SLO_CUES):
            expand.extend(
                [
                    "read model staleness and read-your-writes",
                    "projection freshness slo pattern",
                    "projection freshness slo",
                    "freshness slo",
                    "최신성 slo",
                    "최신성 서비스 수준 목표",
                    "freshness SLO는 운영 계약",
                    "freshness budget burn",
                ]
            )
        if any(cue in haystack for cue in _PROJECTION_LAG_BUDGET_CUES):
            expand.extend(
                [
                    "projection lag budgeting pattern",
                    "projection lag budget",
                    "lag budget",
                    "지연 예산",
                    "반영 지연 허용 범위",
                    "lag budget이 설계 trade-off",
                    "freshness budget",
                ]
            )
        if slo_lag_compare_prompt:
            expand.extend(
                [
                    "projection freshness slo pattern",
                    "projection lag budgeting pattern",
                    "projection freshness slo",
                    "projection lag budget",
                ]
            )
    else:
        expand.extend(
            [
                "projection lag budget",
                "projection freshness slo",
                "freshness budget",
                "read model cutover guardrails",
            ]
        )

    if beginner_intent and _is_projection_cache_invalidation_contrast_prompt(haystack):
        expand.extend(
            [
                "cache invalidation",
                "application cache invalidation",
                "cache eviction after write",
                "projection lag vs cache invalidation",
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


def _security_authentication_compound_matches(haystack: str, tokens: set[str]) -> set[str]:
    matched: set[str] = set()
    has_http_stateless_cue = "http" in tokens or any(
        cue in haystack for cue in _AUTH_HTTP_STATELESS_CUES
    )
    has_login_memory_cue = any(cue in haystack for cue in _AUTH_LOGIN_MEMORY_CUES)
    has_login_state_topic_cue = (
        "로그인" in haystack
        or "login" in tokens
        or "logged" in tokens
        or "signed" in tokens
    )
    if has_http_stateless_cue and has_login_memory_cue:
        matched.add("__http_login_state__")
    if has_login_state_topic_cue and has_login_memory_cue:
        matched.add("__login_state_memory__")
    return matched


def _is_projection_strict_read_beginner_intro_prompt(haystack: str, tokens: set[str]) -> bool:
    if not _has_beginner_intent(haystack, tokens):
        return False
    has_route_cue = any(cue in haystack for cue in _PROJECTION_STRICT_READ_ROUTE_CUES)
    has_gate_cue = any(cue in haystack for cue in _PROJECTION_STRICT_READ_GATE_CUES)
    if not (has_route_cue and has_gate_cue):
        return False
    return (
        _is_projection_freshness_primer_prompt(haystack)
        or "큰 그림" in haystack
        or "before" in haystack
        or "먼저" in haystack
    )


def _projection_freshness_compound_matches(haystack: str, tokens: set[str]) -> set[str]:
    matched: set[str] = set()
    if (
        any(cue in haystack for cue in _PROJECTION_CUTOVER_SAFETY_WINDOW_CUES)
        and "저장 직후" in haystack
        and "예전 값이" in haystack
        and "보이" in haystack
    ):
        matched.add("__projection_cutover_old_value__")
    if _has_projection_detail_list_split_symptom(haystack):
        matched.add("__projection_detail_list_split__")
    if _is_projection_cached_screen_after_save_prompt(haystack):
        matched.add("__projection_cached_screen_after_save__")
    if _is_projection_mobile_refresh_lag_prompt(haystack):
        matched.add("__projection_mobile_refresh_lag__")
    if _is_projection_cache_vs_replica_disambiguation_prompt(haystack):
        matched.add("__projection_cache_vs_replica__")
    if _is_projection_strict_read_beginner_intro_prompt(haystack, tokens):
        matched.add("__projection_strict_read_intro__")
    return matched


def _mvcc_beginner_primer_matches(haystack: str, tokens: set[str]) -> set[str]:
    if "mvcc" not in haystack:
        return set()
    if not (_has_beginner_intent(haystack, tokens) or _has_beginner_confusion_intent(haystack)):
        return set()
    return {"__mvcc_beginner_primer__"}


def _is_mvcc_beginner_why_use_prompt(haystack: str) -> bool:
    if "mvcc" not in haystack:
        return False
    if any(cue in haystack for cue in _TRANSACTION_PRIMER_SHORTFORM_ADVANCED_CUES):
        return False
    return any(
        cue in haystack
        for cue in {
            "why use",
            "why do we use",
            "why should i use",
            "왜 써",
            "왜 사용",
            "왜 있어",
            "왜 필요해",
            "왜 필요하지",
            "왜 쓰는",
            "왜 쓰죠",
        }
    )


def _spring_framework_compound_matches(haystack: str, tokens: set[str]) -> set[str]:
    matched: set[str] = set()
    has_propagation_cue = "propagation" in haystack or "전파" in haystack
    if {"dispatcher", "servlet"} <= tokens:
        matched.add("__dispatcher_servlet_compound__")
    if ({"spring", "mvc"} <= tokens) or ({"스프링", "mvc"} <= tokens):
        matched.add("__spring_mvc_compound__")
    if (
        ({"spring", "m", "v", "c"} <= tokens)
        or ({"스프링", "m", "v", "c"} <= tokens)
    ):
        matched.add("__spring_mvc_compound__")
    if _has_beginner_intent(haystack, tokens) and (
        "mvc" in tokens or {"m", "v", "c"} <= tokens
    ):
        matched.add("__mvc_beginner_shortform__")
    if "spring" in tokens and has_propagation_cue and (
        "transaction" in tokens or "transactional" in haystack
    ):
        matched.add("__spring_transaction_propagation_compound__")
    if (
        _has_beginner_intent(haystack, tokens)
        and has_propagation_cue
        and ("transaction" in tokens or "트랜잭션" in haystack)
        and (
            any(cue in haystack for cue in _BEGINNER_SHORTFORM_QUESTION_CUES)
            or any(cue in haystack for cue in _BEGINNER_WHY_USE_SHORTFORM_CUES)
        )
        and "spring" not in tokens
        and "@transactional" not in haystack
        and "transactional" not in haystack
    ):
        matched.add("__transaction_propagation_beginner_shortform__")
    if _is_spring_transaction_beginner_shortform_prompt(haystack, tokens):
        matched.add("__spring_transaction_beginner_shortform__")
    return matched


def _is_spring_transaction_propagation_prompt(haystack: str, tokens: set[str]) -> bool:
    has_spring_transactional_context = (
        "spring" in tokens or "@transactional" in haystack or "transactional" in haystack
    )
    has_transaction_family_cue = (
        "transaction" in tokens or "@transactional" in haystack or "transactional" in haystack
    )
    return "propagation" in haystack and has_spring_transactional_context and has_transaction_family_cue


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


def _should_suppress_network_http_login_state_noise(haystack: str, hits: list[dict]) -> bool:
    present_tags = {hit["tag"] for hit in hits}
    if "security_authentication" not in present_tags:
        return False

    network_hit = next((hit for hit in hits if hit["tag"] == "network_and_reliability"), None)
    if not network_hit:
        return False

    matched_triggers = network_hit.get("_matched_triggers", set())
    if not matched_triggers or matched_triggers - {"http"}:
        return False

    auth_compound_matches = _security_authentication_compound_matches(
        haystack,
        set(_tokenize(haystack)),
    )
    return "__http_login_state__" in auth_compound_matches


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


def _spring_transactional_beginner_suppressions(
    haystack: str,
    tokens: set[str],
    hits: list[dict],
) -> set[str]:
    if not _has_beginner_intent(haystack, tokens):
        return set()

    spring_compound_matches = _spring_framework_compound_matches(haystack, tokens)
    if not (
        any(trigger in haystack for trigger in _SPRING_FRAMEWORK_TRANSACTIONAL_TRIGGERS)
        or "__transaction_propagation_beginner_shortform__" in spring_compound_matches
        or "__spring_transaction_beginner_shortform__" in spring_compound_matches
    ):
        return set()

    present_tags = {hit["tag"] for hit in hits}
    if "spring_framework" not in present_tags or "transaction_isolation" not in present_tags:
        return set()

    return {"transaction_isolation"}


def _should_suppress_java_cf_propagation_noise(
    haystack: str,
    tokens: set[str],
    hits: list[dict],
) -> bool:
    if not _is_spring_transaction_propagation_prompt(haystack, tokens):
        return False

    java_cf_hit = next(
        (hit for hit in hits if hit["tag"] == "java_completablefuture_cancellation"),
        None,
    )
    if not java_cf_hit:
        return False

    matched_triggers = java_cf_hit.get("_matched_triggers", set())
    return bool(matched_triggers) and matched_triggers <= {"propagation"}


def _should_suppress_transaction_isolation_for_spring_propagation(
    haystack: str,
    tokens: set[str],
    hits: list[dict],
) -> bool:
    if not _is_spring_transaction_propagation_prompt(haystack, tokens):
        return False

    present_tags = {hit["tag"] for hit in hits}
    return "spring_framework" in present_tags and "transaction_isolation" in present_tags


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


def _is_deadlock_timeout_beginner_primer_prompt(
    haystack: str,
    tokens: set[str],
    *,
    beginner_intent: bool,
) -> bool:
    if not beginner_intent:
        return False
    if "lock wait timeout" not in haystack:
        return False
    if not ({"deadlock", "데드락"} & tokens or "mysql deadlock" in haystack or "mysql 데드락" in haystack):
        return False
    return any(cue in haystack for cue in _PROJECTION_OPERATIONAL_COMPARISON_CUES)


def _should_suppress_deadlock_timeout_primer_anomaly_overlap(
    haystack: str,
    tokens: set[str],
    hits: list[dict],
) -> bool:
    if not _is_deadlock_timeout_beginner_primer_prompt(
        haystack,
        tokens,
        beginner_intent=_has_beginner_intent(haystack, tokens),
    ):
        return False

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
        "lock wait timeout",
    }


def _should_suppress_deadlock_timeout_primer_gap_lock_noise(
    haystack: str,
    tokens: set[str],
    hits: list[dict],
) -> bool:
    if not _is_deadlock_timeout_beginner_primer_prompt(
        haystack,
        tokens,
        beginner_intent=_has_beginner_intent(haystack, tokens),
    ):
        return False

    present_tags = {hit["tag"] for hit in hits}
    if "transaction_deadlock_case_study" not in present_tags:
        return False

    gap_lock_hit = next((hit for hit in hits if hit["tag"] == "mysql_gap_locking"), None)
    if not gap_lock_hit:
        return False

    matched_triggers = gap_lock_hit.get("_matched_triggers", set())
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


def _should_suppress_projection_cache_rotation_noise(
    haystack: str,
    tokens: set[str],
    hits: list[dict],
) -> bool:
    if not _is_projection_beginner_cache_invalidation_contrast_prompt(haystack, tokens):
        return False

    present_tags = {hit["tag"] for hit in hits}
    if "projection_freshness" not in present_tags:
        return False

    rollover_hit = next(
        (hit for hit in hits if hit["tag"] == "security_key_rotation_rollover"),
        None,
    )
    if not rollover_hit:
        return False

    matched_triggers = rollover_hit.get("_matched_triggers", set())
    return bool(matched_triggers) and matched_triggers <= {"cache invalidation"}


def _should_suppress_generic_key_rotation_rollover_when_runbook_is_more_specific(
    hits: list[dict],
) -> bool:
    present_tags = {hit["tag"] for hit in hits}
    if "security_key_rotation_runbook" not in present_tags:
        return False

    rollover_hit = next(
        (hit for hit in hits if hit["tag"] == "security_key_rotation_rollover"),
        None,
    )
    if not rollover_hit:
        return False

    matched_triggers = rollover_hit.get("_matched_triggers", set())
    return bool(matched_triggers) and matched_triggers <= {"key rotation", "key-rotation"}


def _should_suppress_projection_filter_sort_state_noise(
    haystack: str,
    tokens: set[str],
    hits: list[dict],
) -> bool:
    if not _has_beginner_intent(haystack, tokens):
        return False
    if not _is_projection_freshness_primer_prompt(haystack):
        return False
    if not any(cue in haystack for cue in _PROJECTION_FILTER_SORT_STATE_CUES):
        return False
    if any(cue in haystack for cue in _PROJECTION_BACKEND_FRESHNESS_ANCHOR_CUES):
        return False

    present_tags = {hit["tag"] for hit in hits}
    return "projection_freshness" in present_tags


def _is_beginner_query_model_filter_sort_prompt(haystack: str, tokens: set[str]) -> bool:
    if not _has_beginner_intent(haystack, tokens):
        return False
    if not any(cue in haystack for cue in _PROJECTION_FILTER_SORT_STATE_CUES):
        return False
    if not any(cue in haystack for cue in _QUERY_MODEL_BEGINNER_FILTER_SORT_SCOPE_CUES):
        return False
    if any(cue in haystack for cue in _PROJECTION_BACKEND_FRESHNESS_ANCHOR_CUES):
        return False
    return True


def _is_beginner_query_model_meaning_prompt(haystack: str, tokens: set[str]) -> bool:
    has_beginner_cue = (
        _has_beginner_intent(haystack, tokens)
        or _has_beginner_confusion_intent(haystack)
        or any(cue in haystack for cue in _BEGINNER_SHORTFORM_QUESTION_CUES)
        or any(cue in haystack for cue in _BEGINNER_WHY_USE_SHORTFORM_CUES)
        or _has_korean_definition_shortform(haystack)
    )
    if not has_beginner_cue:
        return False
    if not any(cue in haystack for cue in _QUERY_MODEL_BEGINNER_MEANING_TOPIC_CUES):
        return False
    if any(cue in haystack for cue in _QUERY_MODEL_BEGINNER_MEANING_ADVANCED_CUES):
        return False
    return True


def _should_suppress_global_failover_when_visibility_is_more_specific(
    hits: list[dict],
) -> bool:
    present_tags = {hit["tag"] for hit in hits}
    if not present_tags & {"failover_visibility", "failover_read_divergence"}:
        return False

    global_failover_hit = next(
        (hit for hit in hits if hit["tag"] == "global_failover_control_plane"),
        None,
    )
    if not global_failover_hit:
        return False

    matched_triggers = global_failover_hit.get("_matched_triggers", set())
    return bool(matched_triggers) and matched_triggers <= {"failover", "promotion"}


def _should_suppress_failover_visibility_when_read_divergence_is_more_specific(
    haystack: str,
    hits: list[dict],
) -> bool:
    present_tags = {hit["tag"] for hit in hits}
    if "failover_read_divergence" not in present_tags or "failover_visibility" not in present_tags:
        return False
    if any(cue in haystack for cue in _FAILOVER_VISIBILITY_OPERATIONAL_CUES):
        return False

    visibility_hit = next((hit for hit in hits if hit["tag"] == "failover_visibility"), None)
    if not visibility_hit:
        return False

    matched_triggers = visibility_hit.get("_matched_triggers", set())
    return bool(matched_triggers) and matched_triggers <= {"stale primary", "promotion visibility"}


def _should_suppress_security_token_validation_for_projection_failover_contrast(
    haystack: str,
    tokens: set[str],
    hits: list[dict],
) -> bool:
    if not _has_beginner_intent(haystack, tokens):
        return False
    if not _is_projection_freshness_primer_prompt(haystack):
        return False

    present_tags = {hit["tag"] for hit in hits}
    required_tags = {
        "projection_freshness",
        "failover_visibility",
        "failover_verification",
        "security_token_validation",
    }
    if not required_tags <= present_tags:
        return False

    auth_cues = {"jwt", "jwks", "kid", "issuer", "audience", "signature", "token"}
    if any(cue in haystack for cue in auth_cues):
        return False

    visibility_cues = {
        "stale read",
        "stale reads",
        "예전 값",
        "old value",
        "old data",
    }
    verification_cues = {
        "write loss",
        "write-loss",
        "loss boundary",
        "write loss audit",
        "commit horizon",
        "verify",
        "validation",
        "failover validation",
    }
    return any(cue in haystack for cue in visibility_cues) and any(
        cue in haystack for cue in verification_cues
    )


def _should_suppress_projection_rollback_transaction_noise(
    haystack: str,
    tokens: set[str],
    hits: list[dict],
) -> bool:
    if not _has_beginner_intent(haystack, tokens):
        return False
    if not _is_projection_freshness_primer_prompt(haystack):
        return False
    has_projection_rollback_window = any(cue in haystack for cue in _PROJECTION_ROLLBACK_WINDOW_CUES)
    has_cutover_safety = any(cue in haystack for cue in _PROJECTION_CUTOVER_SAFETY_WINDOW_CUES)
    if not has_projection_rollback_window and not has_cutover_safety:
        return False
    if (
        any(cue in haystack for cue in _PROJECTION_TRANSACTION_ROLLBACK_CUES)
        and any(cue in haystack for cue in _PROJECTION_TX_CONTRAST_CUES)
    ):
        return False

    present_tags = {hit["tag"] for hit in hits}
    if "projection_freshness" not in present_tags or "transaction_isolation" not in present_tags:
        return False

    transaction_hit = next((hit for hit in hits if hit["tag"] == "transaction_isolation"), None)
    if not transaction_hit:
        return False

    matched_triggers = transaction_hit.get("_matched_triggers", set())
    if (
        has_cutover_safety
        and any(cue in haystack for cue in _PROJECTION_OPERATIONAL_COMPARISON_CUES)
        and (
            {
                "global_failover_control_plane",
                "security_key_rotation_rollover",
                "security_key_rotation_runbook",
            }
            & present_tags
        )
    ):
        return bool(matched_triggers) and matched_triggers <= {"rollback"}
    return bool(matched_triggers) and matched_triggers <= _PROJECTION_TX_NOISE_TRIGGERS


def _projection_beginner_operational_noise_tags(
    haystack: str,
    tokens: set[str],
    hits: list[dict],
) -> set[str]:
    if not (
        _is_projection_beginner_cutover_safety_primer(haystack, tokens)
        or _is_projection_beginner_rebuild_compare_prompt(haystack, tokens)
    ):
        return set()

    present_tags = {hit["tag"] for hit in hits}
    if "projection_freshness" not in present_tags:
        return set()

    return {
        hit["tag"]
        for hit in hits
        if hit["tag"] in _PROJECTION_BEGINNER_OPERATIONAL_NOISE_TAGS
        and hit.get("_matched_triggers")
    }


def _projection_beginner_operational_contrast_expand_tags(
    haystack: str,
    tokens: set[str],
    hits: list[dict],
) -> set[str]:
    if not _is_projection_beginner_cutover_safety_contrast_prompt(haystack, tokens):
        return set()
    if "rollback" in tokens:
        return set()

    present_tags = {hit["tag"] for hit in hits}
    if "projection_freshness" not in present_tags:
        return set()

    return present_tags & _PROJECTION_BEGINNER_OPERATIONAL_CONTRAST_EXPANSION_TAGS


def _projection_beginner_failover_contrast_expand_overrides(
    haystack: str,
    tokens: set[str],
    hits: list[dict],
) -> dict[str, list[str]]:
    if not _has_beginner_intent(haystack, tokens):
        return {}
    if not _is_projection_freshness_primer_prompt(haystack):
        return {}
    if any(cue in haystack for cue in _PROJECTION_CUTOVER_SAFETY_WINDOW_CUES):
        return {}
    if not any(cue in haystack for cue in _PROJECTION_OPERATIONAL_COMPARISON_CUES):
        return {}

    present_tags = {hit["tag"] for hit in hits}
    if "projection_freshness" not in present_tags:
        return {}
    if not (
        present_tags & _PROJECTION_BEGINNER_FAILOVER_CONTRAST_EXPAND_OVERRIDES.keys()
    ):
        return {}

    overrides = {
        tag: list(_PROJECTION_BEGINNER_FAILOVER_CONTRAST_EXPAND_OVERRIDES[tag])
        for tag in present_tags & _PROJECTION_BEGINNER_FAILOVER_CONTRAST_EXPAND_OVERRIDES.keys()
    }
    if (
        "failover_visibility" in overrides
        and (
            "failover_verification" in overrides
            or (
                "visibility window" not in haystack
                and "failover visibility window" not in haystack
            )
        )
    ):
        overrides["failover_visibility"] = ["failover visibility window"]
    return overrides


def _projection_beginner_rollback_contrast_expand_overrides(
    haystack: str,
    tokens: set[str],
    hits: list[dict],
) -> dict[str, list[str]]:
    if not _is_projection_beginner_cutover_safety_contrast_prompt(haystack, tokens):
        return {}
    if "rollback" not in tokens:
        return {}

    present_tags = {hit["tag"] for hit in hits}
    if "projection_freshness" not in present_tags:
        return {}

    return {
        tag: list(_PROJECTION_BEGINNER_ROLLBACK_CONTRAST_EXPAND_OVERRIDES[tag])
        for tag in present_tags & _PROJECTION_BEGINNER_ROLLBACK_CONTRAST_EXPAND_OVERRIDES.keys()
    }


def _projection_beginner_visibility_contrast_expand_overrides(
    haystack: str,
    tokens: set[str],
    hits: list[dict],
) -> dict[str, list[str]]:
    if not _is_projection_beginner_cutover_safety_contrast_prompt(haystack, tokens):
        return {}
    if "failover" not in tokens:
        return {}
    if "visibility" not in tokens and "visibility window" not in haystack:
        return {}

    present_tags = {hit["tag"] for hit in hits}
    if "projection_freshness" not in present_tags or "failover_visibility" not in present_tags:
        return {}

    return {"failover_visibility": ["failover visibility window"]}


def _projection_beginner_operational_noise_tokens(
    haystack: str,
    tokens: set[str],
) -> set[str]:
    rebuild_compare_prompt = _is_projection_beginner_rebuild_compare_prompt(haystack, tokens)
    cutover_primer_prompt = _is_projection_beginner_cutover_safety_primer(haystack, tokens)
    if not (cutover_primer_prompt or rebuild_compare_prompt):
        return set()

    allowed_noise_tags = _PROJECTION_BEGINNER_OPERATIONAL_NOISE_TAGS
    if rebuild_compare_prompt and not cutover_primer_prompt:
        # In primer-vs-playbook compare prompts, keep companion-doc anchors
        # visible in the base query and only strip the rebuild-playbook noise.
        allowed_noise_tags = {"migration_repair_cutover"}

    stripped_tokens: set[str] = set()
    for rule in _RULES:
        if rule["tag"] not in allowed_noise_tags:
            continue
        for trigger in _matched_triggers(haystack, tokens, rule["triggers"]):
            stripped_tokens.update(
                token
                for token in _tokenize(trigger)
                if token not in _PROJECTION_BEGINNER_NOISE_PROTECTED_TOKENS
            )
    if cutover_primer_prompt and not any(
        cue in haystack for cue in _PROJECTION_OPERATIONAL_COMPARISON_CUES
    ):
        stripped_tokens.update({"cutover", "컷오버", "전환"})
    if rebuild_compare_prompt:
        stripped_tokens.update({"rebuild", "backfill"})
    return stripped_tokens


def _projection_beginner_failover_verification_noise_tokens(
    haystack: str,
    tokens: set[str],
) -> set[str]:
    if not _has_beginner_intent(haystack, tokens):
        return set()
    if not _is_projection_freshness_primer_prompt(haystack):
        return set()
    if _is_projection_beginner_rebuild_compare_prompt(haystack, tokens):
        return set()
    has_verification_cue = (
        "verification" in tokens
        or "verify" in tokens
        or "validation" in tokens
        or ("write" in tokens and "loss" in tokens)
        or "commit horizon" in haystack
        or "failover validation" in haystack
    )
    if "failover" not in tokens or not has_verification_cue:
        return set()
    if not any(cue in haystack for cue in _PROJECTION_OPERATIONAL_COMPARISON_CUES):
        return set()
    stripped_tokens = {"verification"}
    if "verify" in tokens:
        stripped_tokens.add("verify")
    if "validation" in tokens:
        stripped_tokens.add("validation")
    return stripped_tokens


def _projection_strict_read_intro_noise_tokens(
    haystack: str,
    tokens: set[str],
) -> set[str]:
    if not _is_projection_strict_read_beginner_intro_prompt(haystack, tokens):
        return set()
    return {
        "cutover",
        "guardrails",
        "fallback",
        "contract",
        "playbook",
        "playbooks",
        "운영",
        "문서",
    }


def _transaction_beginner_incident_noise_tokens(
    haystack: str,
    tokens: set[str],
) -> set[str]:
    if not _has_beginner_intent(haystack, tokens):
        return set()
    if not (
        "incident" in tokens
        or "triage" in tokens
        or "debugging" in tokens
        or "debug" in tokens
        or "card" in tokens
    ):
        return set()
    if any(cue in haystack for cue in _TRANSACTION_BEGINNER_INCIDENT_SPRING_PROTECTED_CUES):
        return set()

    has_anomaly_vocabulary = (
        "dirty read" in haystack
        or "phantom read" in haystack
        or "non-repeatable read" in haystack
        or "non repeatable read" in haystack
        or "read committed" in haystack
        or "repeatable read" in haystack
    )
    has_database_transaction_primer_intent = (
        "rollback" in tokens
        or "deadlock" in tokens
        or "데드락" in tokens
        or has_anomaly_vocabulary
        or "lock wait timeout" in haystack
        or "gap lock" in haystack
        or "next-key lock" in haystack
        or "next key lock" in haystack
        or "isolation level" in haystack
        or "트랜잭션" in tokens
        or "격리" in tokens
    )
    if not has_database_transaction_primer_intent:
        return set()

    stripped_tokens = {
        token for token in _TRANSACTION_BEGINNER_INCIDENT_NOISE_TOKENS if token in tokens
    }
    if has_anomaly_vocabulary and "deadlock" not in tokens and "데드락" not in tokens:
        stripped_tokens.add("rollback")
        if "beginner" in tokens:
            stripped_tokens.add("beginner")
    return stripped_tokens


def _projection_beginner_cache_confusion_noise_tokens(
    haystack: str,
    tokens: set[str],
) -> set[str]:
    if not _is_projection_beginner_cache_confusion_prompt(haystack, tokens):
        return set()
    return {"cache", "캐시"}


def _projection_beginner_slo_lag_compare_noise_tokens(
    haystack: str,
    tokens: set[str],
) -> set[str]:
    if not _is_projection_beginner_slo_lag_compare_prompt(haystack, tokens):
        return set()

    stripped_tokens: set[str] = set()
    for cue in _PROJECTION_SLO_CUES | _PROJECTION_LAG_BUDGET_CUES:
        if cue in haystack:
            stripped_tokens.update(_tokenize(cue))
    return stripped_tokens


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


def _java_family_generic_noise_suppressions(
    haystack: str,
    tokens: set[str],
    hits: list[dict],
) -> set[str]:
    present_tags = {hit["tag"] for hit in hits}
    java_family_tags = {
        "java_language_runtime",
        "java_concurrency_utilities",
        "java_virtual_threads_loom",
    }
    if not (present_tags & java_family_tags):
        return set()

    suppressed_tags: set[str] = set()
    beginner_intent = _has_beginner_intent(haystack, tokens)

    runtime_hit = next((hit for hit in hits if hit["tag"] == "java_language_runtime"), None)
    runtime_specific = False
    if runtime_hit:
        runtime_triggers = runtime_hit.get("_matched_triggers", set())
        runtime_specific = bool(runtime_triggers - {"java", "자바"})

    concurrency_hit = next((hit for hit in hits if hit["tag"] == "concurrency"), None)
    if concurrency_hit:
        matched_triggers = concurrency_hit.get("_matched_triggers", set())
        if matched_triggers and matched_triggers <= {"thread"}:
            suppressed_tags.add("concurrency")

    network_hit = next((hit for hit in hits if hit["tag"] == "network_and_reliability"), None)
    if network_hit:
        matched_triggers = network_hit.get("_matched_triggers", set())
        if matched_triggers and matched_triggers <= {"network", "네트워크", "timeout"}:
            if beginner_intent or runtime_specific:
                suppressed_tags.add("network_and_reliability")

    resource_hit = next((hit for hit in hits if hit["tag"] == "resource_lifecycle"), None)
    if resource_hit:
        matched_triggers = resource_hit.get("_matched_triggers", set())
        if matched_triggers and matched_triggers <= {"close"}:
            if beginner_intent or runtime_specific:
                suppressed_tags.add("resource_lifecycle")

    return suppressed_tags


def _has_beginner_intent(haystack: str, tokens: set[str]) -> bool:
    if any(phrase in haystack for phrase in _BEGINNER_INTENT_PHRASES):
        return True
    if any(group <= tokens for group in _BEGINNER_INTENT_TOKEN_GROUPS):
        return True
    if _has_korean_definition_shortform(haystack):
        return True
    return (
        _is_woowa_backend_foundation_shortform_prompt(haystack)
        or _is_database_modeling_beginner_shortform_prompt(haystack)
        or _is_transaction_primer_shortform_prompt(haystack)
        or _is_projection_cutover_safety_shortform_prompt(haystack)
        or _is_java_concurrency_beginner_shortform_prompt(haystack)
        or _is_java_virtual_threads_beginner_shortform_prompt(haystack)
        or _is_transactional_beginner_why_use_prompt(haystack)
        or _is_transactional_beginner_plain_alias_prompt(haystack)
        or _is_transactional_beginner_mechanics_prompt(haystack)
        or _is_transactional_beginner_spring_shortform_prompt(haystack, tokens)
        or _is_spring_transaction_beginner_shortform_prompt(haystack, tokens)
        or _is_transaction_propagation_beginner_shortform_prompt(haystack, tokens)
        or _is_spring_beginner_english_meaning_prompt(haystack)
        or _is_spring_foundation_english_role_prompt(haystack)
        or _is_spring_ioc_di_beginner_shortform_prompt(haystack)
        or _is_spring_foundation_flow_prompt(haystack)
    )


def _has_beginner_confusion_intent(haystack: str) -> bool:
    return any(cue in haystack for cue in _BEGINNER_CONFUSION_CUES)


def _has_korean_definition_shortform(haystack: str) -> bool:
    return bool(_KOREAN_DEFINITION_SHORTFORM_RE.search(haystack))


def _is_jwt_validation_order_prompt(haystack: str) -> bool:
    return any(cue in haystack for cue in _JWT_VALIDATION_ORDER_CUES)


def _is_woowa_backend_foundation_shortform_prompt(haystack: str) -> bool:
    if not (
        any(cue in haystack for cue in _BEGINNER_SHORTFORM_QUESTION_CUES)
        or any(cue in haystack for cue in _BEGINNER_WHY_USE_SHORTFORM_CUES)
        or _has_korean_definition_shortform(haystack)
    ):
        return False
    if not any(cue in haystack for cue in _WOOWA_BACKEND_FOUNDATION_TOPIC_CUES):
        return False
    if "@transactional" in haystack and any(cue in haystack for cue in _TRANSACTIONAL_ADVANCED_CUES):
        return False
    return True


def _is_database_modeling_beginner_shortform_prompt(haystack: str) -> bool:
    if not (
        any(cue in haystack for cue in _BEGINNER_SHORTFORM_QUESTION_CUES)
        or any(cue in haystack for cue in _BEGINNER_WHY_USE_SHORTFORM_CUES)
        or _has_korean_definition_shortform(haystack)
    ):
        return False
    return any(cue in haystack for cue in _DATABASE_MODELING_BEGINNER_TOPIC_CUES)


def _is_transaction_primer_shortform_prompt(haystack: str) -> bool:
    if not (
        any(cue in haystack for cue in _BEGINNER_SHORTFORM_QUESTION_CUES)
        or any(cue in haystack for cue in _BEGINNER_WHY_USE_SHORTFORM_CUES)
        or _has_korean_definition_shortform(haystack)
        or any(cue in haystack for cue in _TRANSACTION_PRIMER_CONCEPT_EXPLANATION_CUES)
    ):
        return False
    if not any(cue in haystack for cue in _TRANSACTION_PRIMER_SHORTFORM_TOPIC_CUES):
        return False
    if any(cue in haystack for cue in _TRANSACTION_PRIMER_SHORTFORM_ADVANCED_CUES):
        return False
    return True


def _is_transaction_propagation_beginner_shortform_prompt(
    haystack: str,
    tokens: set[str],
) -> bool:
    if not (
        any(cue in haystack for cue in _BEGINNER_SHORTFORM_QUESTION_CUES)
        or any(cue in haystack for cue in _BEGINNER_WHY_USE_SHORTFORM_CUES)
    ):
        return False
    if "transaction" not in tokens and "트랜잭션" not in haystack:
        return False
    if "propagation" not in haystack and "전파" not in haystack:
        return False
    return "@transactional" not in haystack


def _is_java_concurrency_beginner_shortform_prompt(haystack: str) -> bool:
    if not (
        any(cue in haystack for cue in _BEGINNER_SHORTFORM_QUESTION_CUES)
        or _has_korean_definition_shortform(haystack)
    ):
        return False
    return any(cue in haystack for cue in _JAVA_CONCURRENCY_BEGINNER_SHORTFORM_TOPIC_CUES)


def _is_java_virtual_threads_beginner_shortform_prompt(haystack: str) -> bool:
    if not (
        any(cue in haystack for cue in _BEGINNER_SHORTFORM_QUESTION_CUES)
        or _has_korean_definition_shortform(haystack)
    ):
        return False
    if not any(cue in haystack for cue in _JAVA_VIRTUAL_THREADS_CORE_TRIGGERS):
        return False
    if any(cue in haystack for cue in _JAVA_VIRTUAL_THREADS_MIGRATION_CUES):
        return False
    if any(cue in haystack for cue in _JAVA_VIRTUAL_THREADS_BUDGET_CUES):
        return False
    return True


def _is_transactional_beginner_why_use_prompt(haystack: str) -> bool:
    if not any(cue in haystack for cue in _TRANSACTIONAL_BEGINNER_WHY_USE_CUES):
        return False
    return not any(cue in haystack for cue in _TRANSACTIONAL_ADVANCED_CUES)


def _is_transactional_beginner_plain_alias_prompt(haystack: str) -> bool:
    if "@transactional" in haystack:
        return False
    if not any(cue in haystack for cue in _TRANSACTIONAL_BEGINNER_PLAIN_ALIAS_CUES):
        return False
    if "spring" not in haystack:
        return False
    return not any(cue in haystack for cue in _TRANSACTIONAL_ADVANCED_CUES)


def _is_transactional_beginner_spring_shortform_prompt(
    haystack: str,
    tokens: set[str],
) -> bool:
    if "@transactional" in haystack:
        return False
    if "transactional" not in haystack or "spring" not in haystack:
        return False
    if any(cue in haystack for cue in _TRANSACTIONAL_ADVANCED_CUES):
        return False
    return len(tokens) <= 4


def _is_spring_transaction_beginner_shortform_prompt(
    haystack: str,
    tokens: set[str],
) -> bool:
    if "@transactional" in haystack or "transactional" in haystack:
        return False
    if not (
        any(cue in haystack for cue in _BEGINNER_SHORTFORM_QUESTION_CUES)
        or any(cue in haystack for cue in _BEGINNER_WHY_USE_SHORTFORM_CUES)
        or _has_korean_definition_shortform(haystack)
    ):
        return False
    if not ({"spring", "transaction"} <= tokens or ("스프링" in haystack and "트랜잭션" in haystack)):
        return False
    return not any(cue in haystack for cue in _TRANSACTIONAL_ADVANCED_CUES)


def _is_transactional_beginner_mechanics_prompt(haystack: str) -> bool:
    if not any(cue in haystack for cue in _TRANSACTIONAL_BEGINNER_MECHANICS_CUES):
        return False
    if "@transactional" not in haystack and "spring" not in haystack:
        return False
    return not any(cue in haystack for cue in _TRANSACTIONAL_ADVANCED_CUES)


def _is_spring_foundation_flow_prompt(haystack: str) -> bool:
    if not any(cue in haystack for cue in _SPRING_FOUNDATION_FLOW_CUES):
        return False
    if not any(cue in haystack for cue in _SPRING_FOUNDATION_FLOW_TOPIC_CUES):
        return False
    return not any(cue in haystack for cue in _SPRING_FOUNDATION_ADVANCED_CUES)


def _is_spring_beginner_english_meaning_prompt(haystack: str) -> bool:
    if "what does" not in haystack or "mean" not in haystack:
        return False
    if not any(cue in haystack for cue in _SPRING_BEGINNER_ENGLISH_MEANING_TOPIC_CUES):
        return False
    return not any(cue in haystack for cue in _SPRING_FOUNDATION_ADVANCED_CUES)


def _is_spring_foundation_english_role_prompt(haystack: str) -> bool:
    if "what does" not in haystack or " do" not in haystack:
        return False
    return _has_spring_foundation_english_role_intent(
        haystack,
        {
            "beanfactory",
            "bean factory",
            "applicationcontext",
            "application context",
            "bean",
        },
    ) and not any(cue in haystack for cue in _SPRING_FOUNDATION_ADVANCED_CUES)


def _is_spring_ioc_di_beginner_shortform_prompt(haystack: str) -> bool:
    return any(cue in haystack for cue in _BEGINNER_SHORTFORM_QUESTION_CUES) and any(
        cue in haystack for cue in _SPRING_FRAMEWORK_IOC_DI_TRIGGERS
    )


def _is_projection_freshness_primer_prompt(haystack: str) -> bool:
    return (
        any(cue in haystack for cue in _PROJECTION_FRESHNESS_PRIMER_CUES)
        or _is_projection_cached_screen_after_save_prompt(haystack)
        or _is_projection_mobile_refresh_lag_prompt(haystack)
        or _is_projection_cutover_safety_shortform_prompt(haystack)
        or _has_projection_detail_list_split_symptom(haystack)
        or _is_projection_cache_vs_replica_disambiguation_prompt(haystack)
    )


def _is_projection_minimal_stale_after_save_prompt(haystack: str) -> bool:
    return (
        any(cue in haystack for cue in _PROJECTION_MINIMAL_STALE_AFTER_SAVE_CUES)
        or _is_projection_cached_screen_after_save_prompt(haystack)
        or _is_projection_mobile_refresh_lag_prompt(haystack)
        or _has_projection_detail_list_split_symptom(haystack)
        or _is_projection_cache_vs_replica_disambiguation_prompt(haystack)
    )


def _has_projection_detail_list_split_symptom(haystack: str) -> bool:
    return any(cue in haystack for cue in _PROJECTION_DETAIL_LIST_SPLIT_DETAIL_CUES) and any(
        cue in haystack for cue in _PROJECTION_DETAIL_LIST_SPLIT_LIST_CUES
    )


def _is_projection_cutover_safety_shortform_prompt(haystack: str) -> bool:
    return any(cue in haystack for cue in _BEGINNER_SHORTFORM_QUESTION_CUES) and any(
        cue in haystack for cue in _PROJECTION_CUTOVER_SAFETY_WINDOW_CUES
    )


def _is_projection_beginner_cutover_safety_primer(haystack: str, tokens: set[str]) -> bool:
    if not _has_beginner_intent(haystack, tokens):
        return False
    if not _is_projection_freshness_primer_prompt(haystack):
        return False
    if not any(cue in haystack for cue in _PROJECTION_CUTOVER_SAFETY_WINDOW_CUES):
        return False
    return not any(cue in haystack for cue in _PROJECTION_OPERATIONAL_COMPARISON_CUES)


def _is_projection_beginner_cutover_safety_contrast_prompt(
    haystack: str,
    tokens: set[str],
) -> bool:
    if not _has_beginner_intent(haystack, tokens):
        return False
    if not _is_projection_freshness_primer_prompt(haystack):
        return False
    if not any(cue in haystack for cue in _PROJECTION_CUTOVER_SAFETY_WINDOW_CUES):
        return False
    return any(cue in haystack for cue in _PROJECTION_OPERATIONAL_COMPARISON_CUES)


def _is_projection_beginner_rebuild_compare_prompt(haystack: str, tokens: set[str]) -> bool:
    if not _has_beginner_intent(haystack, tokens):
        return False
    if not _is_projection_freshness_primer_prompt(haystack):
        return False
    if not any(cue in haystack for cue in _PROJECTION_REBUILD_PLAYBOOK_CUES):
        return False
    return any(cue in haystack for cue in _PROJECTION_OPERATIONAL_COMPARISON_CUES)


def _is_projection_beginner_cache_confusion_prompt(haystack: str, tokens: set[str]) -> bool:
    if not _has_beginner_intent(haystack, tokens):
        return False
    if not _is_projection_freshness_primer_prompt(haystack):
        return False
    if _is_projection_cache_vs_replica_disambiguation_prompt(haystack):
        return False
    if any(cue in haystack for cue in _PROJECTION_OPERATIONAL_COMPARISON_CUES):
        return False
    return any(cue in haystack for cue in _PROJECTION_CACHE_CONFUSION_CUES) or (
        _is_projection_cached_screen_after_save_prompt(haystack)
    )


def _is_projection_beginner_slo_lag_compare_prompt(
    haystack: str,
    tokens: set[str],
) -> bool:
    if not _has_beginner_intent(haystack, tokens):
        return False
    if not _is_projection_freshness_primer_prompt(haystack):
        return False
    if not any(cue in haystack for cue in _PROJECTION_OPERATIONAL_COMPARISON_CUES):
        return False
    return any(cue in haystack for cue in _PROJECTION_SLO_CUES) and any(
        cue in haystack for cue in _PROJECTION_LAG_BUDGET_CUES
    )


def _is_projection_beginner_navigator_bridge_prompt(haystack: str, tokens: set[str]) -> bool:
    if not _has_beginner_intent(haystack, tokens):
        return False
    has_overview_cue = any(
        cue in haystack
        for cue in {
            "overview",
            "overview doc",
            "overview docs",
            "staleness overview",
            "freshness overview",
            "primer",
            "primer doc",
            "primer docs",
            "entrypoint",
            "entrypoint doc",
            "entrypoint docs",
            "bridge",
            "bridge doc",
            "bridge docs",
            "start here",
            "starter",
            "개요",
            "개요 문서",
            "개요 docs",
            "입문 개요",
            "입문 문서",
            "시작 문서",
            "브리지",
        }
    )
    has_neighbor_cue = any(
        cue in haystack
        for cue in {
            "sibling",
            "sibling doc",
            "sibling docs",
            "neighbor",
            "neighbors",
            "neighbor docs",
            "nearby docs",
            "형제 문서",
            "주변 형제 문서",
            "주변 문서",
            "옆 문서",
            "옆 형제 문서",
            "nearby sibling docs",
            "nearby sibling",
            "linked docs",
            "linked sibling docs",
            "follow-up docs",
            "next docs",
            "연결 문서",
            "이어 볼 문서",
        }
    )
    if not has_overview_cue:
        return False
    if not has_neighbor_cue and not _has_projection_cqrs_survey_rejection(haystack):
        return False
    if not any(cue in haystack for cue in _PROJECTION_BACKEND_FRESHNESS_ANCHOR_CUES):
        return False
    return _is_projection_freshness_primer_prompt(haystack)


def _has_projection_cqrs_survey_rejection(haystack: str) -> bool:
    if "cqrs" not in haystack:
        return False
    if not any(
        cue in haystack
        for cue in {
            "survey",
            "surveys",
            "survey route",
            "survey routes",
            "survey routing",
            "route",
            "routes",
            "routing",
            "sweep",
            "설문",
            "overview",
            "개요",
            "큰 그림",
            "big picture",
        }
    ):
        return False
    return "말고" in haystack or "instead of" in haystack or "rather than" in haystack


def _is_projection_cached_screen_after_save_prompt(haystack: str) -> bool:
    if not any(cue in haystack for cue in _PROJECTION_CACHE_CONFUSION_CUES):
        return False
    if not any(cue in haystack for cue in _PROJECTION_CACHED_SCREEN_SAVE_CUES):
        return False
    if not any(cue in haystack for cue in _PROJECTION_CACHED_SCREEN_VIEW_CUES):
        return False
    return any(cue in haystack for cue in _PROJECTION_CACHED_SCREEN_STALE_CUES)


def _is_projection_mobile_refresh_lag_prompt(haystack: str) -> bool:
    has_view_target = any(cue in haystack for cue in _PROJECTION_MOBILE_DELAY_VIEW_CUES)
    has_mobile_surface = any(cue in haystack for cue in _PROJECTION_MOBILE_APP_CUES) and has_view_target
    has_refresh_gesture = any(
        cue in haystack for cue in _PROJECTION_MOBILE_REFRESH_GESTURE_CUES
    )
    if not has_mobile_surface and not has_refresh_gesture:
        return False
    has_write_or_new_value = any(cue in haystack for cue in _PROJECTION_CACHED_SCREEN_SAVE_CUES)
    if has_refresh_gesture and any(
        cue in haystack for cue in _PROJECTION_MOBILE_REFRESH_VALUE_CUES
    ):
        has_write_or_new_value = True
    if not has_write_or_new_value:
        return False
    if not any(cue in haystack for cue in _PROJECTION_MOBILE_DELAY_STALE_CUES):
        return False
    if has_refresh_gesture:
        return True
    return has_view_target


def _is_projection_cache_vs_replica_disambiguation_prompt(haystack: str) -> bool:
    if not any(cue in haystack for cue in _PROJECTION_CACHE_CONFUSION_CUES):
        return False
    if not any(cue in haystack for cue in _PROJECTION_REPLICA_DISAMBIGUATION_CUES):
        return False
    if not any(cue in haystack for cue in _PROJECTION_DISAMBIGUATION_CONFUSION_CUES):
        return False
    return "저장" in haystack or "saved" in haystack or "write" in haystack


def _has_projection_application_cache_contrast(haystack: str) -> bool:
    if "cache invalidation" not in haystack:
        return False
    return any(cue in haystack for cue in _PROJECTION_APPLICATION_CACHE_CONTEXT_CUES)


def _is_generic_crud_korean_prompt(haystack: str) -> bool:
    if any(cue in haystack for cue in _GENERIC_CRUD_KOREAN_FRESHNESS_EXCLUSION_CUES):
        return False
    if any(cue in haystack for cue in _PROJECTION_FRESHNESS_PRIMER_CUES):
        return False
    if not any(cue in haystack for cue in _GENERIC_CRUD_KOREAN_READ_CUES):
        return False
    if not any(cue in haystack for cue in _GENERIC_CRUD_KOREAN_WRITE_CUES):
        return False
    return any(cue in haystack for cue in _GENERIC_CRUD_KOREAN_SCOPE_CUES) or (
        "목록" in haystack and "조회" in haystack
    )


def _generic_crud_korean_expand(haystack: str) -> list[str]:
    expand = [
        "controller service repository roles",
        "spring request pipeline beginner",
    ]
    if "api" in haystack or "rest" in haystack:
        expand.extend(
            [
                "rest api",
                "request validation",
            ]
        )
    if any(cue in haystack for cue in {"수정", "update", "삭제", "delete", "안 돼"}):
        expand.extend(
            [
                "service layer transaction boundary patterns",
                "transactional annotation basics",
            ]
        )
    if "soft delete" in haystack or "hard delete" in haystack:
        expand.append("soft delete")
    return expand


def _is_projection_cache_invalidation_contrast_prompt(haystack: str) -> bool:
    if not any(cue in haystack for cue in _PROJECTION_OPERATIONAL_COMPARISON_CUES):
        return False
    if not _has_projection_application_cache_contrast(haystack):
        return False
    return any(cue in haystack for cue in _PROJECTION_CACHE_COMPARE_ENTRYPOINT_CUES) or any(
        cue in haystack for cue in _PROJECTION_FRESHNESS_PRIMER_CUES
    )


def _is_projection_beginner_cache_invalidation_contrast_prompt(
    haystack: str,
    tokens: set[str],
) -> bool:
    if not _has_beginner_intent(haystack, tokens):
        return False
    return _is_projection_cache_invalidation_contrast_prompt(haystack)


def _is_projection_rollback_window_transaction_rollback_db_prompt(
    haystack: str,
    *,
    beginner_intent: bool,
) -> bool:
    if beginner_intent:
        return False
    if _is_projection_freshness_primer_prompt(haystack):
        return False
    if not any(cue in haystack for cue in _PROJECTION_ROLLBACK_WINDOW_CUES):
        return False
    return any(cue in haystack for cue in _PROJECTION_TRANSACTION_ROLLBACK_CUES)


def _apply_beginner_primer_bias(haystack: str, tokens: set[str], hits: list[dict]) -> set[str]:
    if not _has_beginner_intent(haystack, tokens):
        if not _is_beginner_query_model_meaning_prompt(haystack, tokens):
            return set()

    hits_by_tag = {hit["tag"]: hit for hit in hits}
    present_tags = set(hits_by_tag)
    suppressed_tags: set[str] = set()
    if _is_beginner_query_model_meaning_prompt(haystack, tokens) and "persistence_boundary" in present_tags:
        primer_hit = hits_by_tag["persistence_boundary"]
        primer_hit["score"] += 3
        primer_hit["expand"].extend(
            [
                "query model separation",
                "query model separation read heavy apis",
                "query service vs repository",
                "read-heavy api beginner primer",
                "list search filter sort beginner guide",
            ]
        )
        suppressed_tags.update(present_tags & {"api_boundary", "layer_responsibility"})
    for primer_tag, config in _BEGINNER_PRIMER_OVERRIDES.items():
        if primer_tag not in present_tags:
            continue
        if primer_tag == "security_authentication" and _is_jwt_validation_order_prompt(haystack):
            continue
        if primer_tag == "projection_freshness" and not (
            _is_projection_freshness_primer_prompt(haystack)
            or _is_projection_strict_read_beginner_intro_prompt(haystack, tokens)
        ):
            continue
        required_tags = set(config.get("requires_any", set()))
        if required_tags and not (present_tags & required_tags):
            continue

        primer_hit = hits_by_tag[primer_tag]
        primer_hit["score"] += int(config.get("score_bonus", 0))
        if primer_tag == "transaction_isolation" and _is_mvcc_beginner_why_use_prompt(haystack):
            primer_hit["expand"].extend(
                [
                    "transaction isolation beginner primer",
                    "transaction isolation simple mental model",
                    "mvcc basics",
                    "mvcc concept overview",
                    "why use mvcc",
                    "concurrent read write visibility basics",
                ]
            )
        else:
            primer_hit["expand"].extend(config.get("expand", []))
        if primer_tag == "projection_freshness" and _is_projection_strict_read_beginner_intro_prompt(
            haystack, tokens
        ):
            primer_hit["expand"].extend(
                [
                    "session pinning strict read",
                    "session pinning vs version gated",
                    "expected version strict read",
                    "watermark gated strict read",
                    "actor scoped pinning",
                    "cross screen read your writes",
                ]
            )
            suppressed_tags.add("security_authentication")
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
        if rule["tag"] == "security_authentication":
            matched_triggers.update(_security_authentication_compound_matches(haystack, tokens))
        if rule["tag"] == "spring_framework":
            matched_triggers.update(_spring_framework_compound_matches(haystack, tokens))
        if rule["tag"] == "mysql_gap_locking":
            matched_triggers.update(_gap_lock_compound_matches(haystack))
        if rule["tag"] == "projection_freshness":
            matched_triggers.update(_projection_freshness_compound_matches(haystack, tokens))
        score = len(matched_triggers)
        if score == 0:
            continue
        expand = list(rule["expand"])
        if rule["tag"] == "storage_contract_evolution":
            expand = _storage_contract_expand(matched_triggers)
        elif rule["tag"] == "transaction_isolation":
            expand = _transaction_isolation_expand(
                haystack,
                tokens,
                matched_triggers,
                beginner_intent=_has_beginner_intent(haystack, tokens),
            )
        elif rule["tag"] == "db_modeling":
            expand = _db_modeling_expand(
                haystack,
                tokens,
                matched_triggers,
                beginner_intent=_has_beginner_intent(haystack, tokens),
            )
        elif rule["tag"] == "security_authentication":
            expand = _security_authentication_expand(
                haystack,
                matched_triggers,
                beginner_intent=_has_beginner_intent(haystack, tokens),
            )
        elif rule["tag"] == "connection_pool_basics":
            expand = _connection_pool_expand(
                haystack,
                matched_triggers,
                beginner_intent=_has_beginner_intent(haystack, tokens),
            )
        elif rule["tag"] == "java_language_runtime":
            expand = _java_runtime_expand(matched_triggers)
        elif rule["tag"] == "spring_framework":
            expand = _spring_framework_expand(
                haystack,
                matched_triggers,
                beginner_intent=_has_beginner_intent(haystack, tokens),
            )
        elif rule["tag"] == "java_concurrency_utilities":
            expand = _java_concurrency_expand(
                matched_triggers,
                beginner_intent=_has_beginner_intent(haystack, tokens),
            )
        elif rule["tag"] == "java_completablefuture_cancellation":
            expand = _java_completablefuture_cancellation_expand(
                matched_triggers,
                beginner_intent=_has_beginner_intent(haystack, tokens),
            )
        elif rule["tag"] == "java_completablefuture_fan_in_timeout":
            expand = _java_completablefuture_fan_in_timeout_expand(
                matched_triggers,
                beginner_intent=_has_beginner_intent(haystack, tokens),
            )
        elif rule["tag"] == "java_virtual_threads_loom":
            expand = _java_virtual_threads_expand(
                haystack,
                matched_triggers,
                beginner_intent=_has_beginner_intent(haystack, tokens),
            )
        elif rule["tag"] == "projection_freshness":
            expand = _projection_freshness_expand(
                haystack,
                beginner_intent=_has_beginner_intent(haystack, tokens),
            )
        elif rule["tag"] == "transaction_deadlock_case_study":
            expand = _transaction_deadlock_expand(
                haystack,
                tokens,
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
        if _should_suppress_java_cf_propagation_noise(haystack, tokens, hits):
            suppressed_tags.add("java_completablefuture_cancellation")
        if _should_suppress_gap_lock_deadlock_noise(haystack, hits):
            suppressed_tags.add("transaction_anomaly_patterns")
        if _should_suppress_deadlock_timeout_primer_anomaly_overlap(haystack, tokens, hits):
            suppressed_tags.add("transaction_anomaly_patterns")
        if _should_suppress_deadlock_timeout_primer_gap_lock_noise(haystack, tokens, hits):
            suppressed_tags.add("mysql_gap_locking")
        if _should_suppress_jwks_fail_closed_resource_noise(hits):
            suppressed_tags.add("resource_lifecycle")
        if _should_suppress_os_locking_concurrency_noise(hits):
            suppressed_tags.add("concurrency")
        if _should_suppress_failover_rotation_cache_noise(hits):
            suppressed_tags.add("security_key_rotation_rollover")
        if _should_suppress_projection_cache_rotation_noise(haystack, tokens, hits):
            suppressed_tags.add("security_key_rotation_rollover")
        if _should_suppress_generic_key_rotation_rollover_when_runbook_is_more_specific(hits):
            suppressed_tags.add("security_key_rotation_rollover")
        if _should_suppress_projection_filter_sort_state_noise(haystack, tokens, hits):
            suppressed_tags.add("projection_freshness")
        if _should_suppress_global_failover_when_visibility_is_more_specific(hits):
            suppressed_tags.add("global_failover_control_plane")
        if _should_suppress_failover_visibility_when_read_divergence_is_more_specific(
            haystack, hits
        ):
            suppressed_tags.add("failover_visibility")
        if _should_suppress_security_token_validation_for_projection_failover_contrast(
            haystack, tokens, hits
        ):
            suppressed_tags.add("security_token_validation")
        if _should_suppress_transaction_isolation_for_spring_propagation(
            haystack, tokens, hits
        ):
            suppressed_tags.add("transaction_isolation")
        if _should_suppress_projection_rollback_transaction_noise(haystack, tokens, hits):
            suppressed_tags.add("transaction_isolation")
        suppressed_tags.update(_spring_transactional_beginner_suppressions(haystack, tokens, hits))
        suppressed_tags.update(
            _projection_beginner_operational_noise_tags(haystack, tokens, hits)
        )
        suppressed_tags.update(_java_concurrency_false_positive_suppressions(hits))
        suppressed_tags.update(_java_runtime_false_positive_suppressions(hits))
        suppressed_tags.update(_java_virtual_threads_false_positive_suppressions(hits))
        suppressed_tags.update(_java_family_generic_noise_suppressions(haystack, tokens, hits))
        if _should_suppress_network_http_login_state_noise(haystack, hits):
            suppressed_tags.add("network_and_reliability")
        if suppressed_tags:
            hits = [hit for hit in hits if hit["tag"] not in suppressed_tags]
    hits.sort(key=lambda h: (-h["score"], h["tag"]))
    for hit in hits:
        hit.pop("_matched_triggers", None)
    return hits


def expand_query(prompt: str, topic_hints: list[str] | None = None) -> list[str]:
    """Produce augmented query tokens (original + rule expansions)."""
    haystack = _haystack(prompt, topic_hints)
    tokens = set(_tokenize(haystack))
    base = _tokenize(prompt)
    if _is_generic_crud_korean_prompt(haystack):
        base.extend(_generic_crud_korean_expand(haystack))
    for hint in topic_hints or []:
        base.extend(_tokenize(hint))
    stripped_tokens = _projection_beginner_operational_noise_tokens(haystack, tokens)
    stripped_tokens.update(
        _projection_beginner_failover_verification_noise_tokens(haystack, tokens)
    )
    stripped_tokens.update(_transaction_beginner_incident_noise_tokens(haystack, tokens))
    stripped_tokens.update(_projection_beginner_cache_confusion_noise_tokens(haystack, tokens))
    stripped_tokens.update(_projection_strict_read_intro_noise_tokens(haystack, tokens))
    stripped_tokens.update(_projection_beginner_slo_lag_compare_noise_tokens(haystack, tokens))
    if stripped_tokens:
        base = [tok for tok in base if tok.lower() not in stripped_tokens]
    signals = detect_signals(prompt, topic_hints)
    suppressed_expand_tags = _projection_beginner_operational_contrast_expand_tags(
        haystack,
        tokens,
        signals,
    )
    contrast_expand_overrides = _projection_beginner_failover_contrast_expand_overrides(
        haystack,
        tokens,
        signals,
    )
    contrast_expand_overrides.update(
        _projection_beginner_rollback_contrast_expand_overrides(
            haystack,
            tokens,
            signals,
        )
    )
    contrast_expand_overrides.update(
        _projection_beginner_visibility_contrast_expand_overrides(
            haystack,
            tokens,
            signals,
        )
    )
    for signal in signals:
        if signal["tag"] in contrast_expand_overrides:
            base.extend(contrast_expand_overrides[signal["tag"]])
            continue
        if signal["tag"] in suppressed_expand_tags:
            continue
        base.extend(signal["expand"])
    if _is_beginner_query_model_filter_sort_prompt(haystack, tokens):
        base.extend(
            [
                "query model separation",
                "query model separation read heavy apis",
                "list search filter sort beginner guide",
                "browser filter state",
                "local sort state",
            ]
        )
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
