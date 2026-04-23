"""Ranking-focused regression tests for the CS RAG search path in cheap mode.

Builds a fixture index using ``indexer._insert_chunks`` directly
(bypassing sentence-transformers) and asserts that representative
queries rank the most specific document first. Covers:

- category boost/filter via ``LEARNING_POINT_TO_CS_CATEGORY``
- query expansion from ``signal_rules`` in cheap mode
- ranking guardrails for the growing repository/security/reliability
  and migration corpus slices
- newly added design-pattern docs around read models, projection
  rebuilds, and event compatibility
- renamed Java overview docs and the applied-data-structures router
- cheap mode degrade path (no ML deps required)

This suite intentionally never touches numpy / sentence-transformers so
it stays green in First-Run Protocol environments.
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from unittest import mock
from pathlib import Path

from scripts.learning.rag import corpus_loader, indexer, searcher, signal_rules


def _chunk(
    doc_id: str,
    path: str,
    title: str,
    category: str,
    section_title: str,
    body: str,
) -> corpus_loader.CorpusChunk:
    return corpus_loader.CorpusChunk(
        doc_id=doc_id,
        chunk_id=f"{doc_id}#0",
        path=path,
        title=title,
        category=category,
        section_title=section_title,
        section_path=[title, section_title],
        body=body,
        char_len=len(body),
    )


FIXTURES = [
    _chunk(
        "a",
        "contents/design-pattern/repository-pattern-vs-antipattern.md",
        "Repository Pattern vs Anti-Pattern",
        "design-pattern",
        "Repository query leakage",
        (
            "repository pattern 은 aggregate root 를 저장하는 persistence abstraction 이지만 "
            "DAO 처럼 query leakage 와 화면용 join DTO 생성을 모두 맡기면 anti-pattern 이 된다."
        ),
    ),
    _chunk(
        "b",
        "contents/design-pattern/repository-boundary-aggregate-vs-read-model.md",
        "Repository Boundary: Aggregate Persistence vs Read Model",
        "design-pattern",
        "Aggregate persistence vs read model",
        (
            "repository boundary 는 aggregate persistence 에 맞추고 read model, query service, "
            "read model boundary, join DTO, remote lookup 은 밖으로 분리한다. aggregate "
            "persistence 와 read model query service 경계를 선명하게 나누는 설계다."
        ),
    ),
    _chunk(
        "c",
        "contents/database/transaction-isolation-locking.md",
        "트랜잭션 격리수준과 락",
        "database",
        "Isolation anomalies",
        (
            "transaction isolation level 과 MVCC, phantom read, non-repeatable read, deadlock 을 "
            "설명하는 기초 문서다."
        ),
    ),
    _chunk(
        "d",
        "contents/database/transaction-boundary-isolation-locking-decision-framework.md",
        "Transaction Boundary, Isolation, and Locking Decision Framework",
        "database",
        "Choosing boundary and locking strategy",
        (
            "transaction boundary, isolation, locking strategy 를 함께 고른다. optimistic lock, "
            "pessimistic lock, select for update, retry, invariant protection 을 비교한다."
        ),
    ),
    _chunk(
        "d1",
        "contents/database/gap-lock-next-key-lock.md",
        "Gap Lock과 Next-Key Lock",
        "database",
        "Range locking in InnoDB",
        (
            "gap lock, next-key lock, record lock, insert intention wait, range lock, "
            "repeatable read locking, InnoDB gap locking 을 설명한다."
        ),
    ),
    _chunk(
        "d2",
        "contents/database/deadlock-case-study.md",
        "MySQL Deadlock Case Study",
        "database",
        "Deadlock graph and lock ordering",
        (
            "mysql deadlock case study 는 wait graph, circular wait, lock ordering, deadlock retry, "
            "innodb deadlock log, error 1213, transaction deadlock 복구를 설명한다."
        ),
    ),
    _chunk(
        "d3",
        "contents/database/mvcc-read-view-consistent-read-internals.md",
        "MVCC Read View and Consistent Read Internals",
        "database",
        "Read view visibility rules",
        (
            "mvcc read view, consistent read, m_low_limit_id, m_up_limit_id, undo chain, "
            "trx visibility, snapshot read 를 다루는 심화 문서다."
        ),
    ),
    _chunk(
        "d4",
        "contents/database/undo-record-version-chain-traversal.md",
        "Undo Record Version Chain Traversal",
        "database",
        "Undo chain walk",
        (
            "undo record, version chain traversal, read view, consistent read, purge lag, "
            "old row version reconstruction 을 설명하는 mvcc 심화 문서다."
        ),
    ),
    _chunk(
        "e",
        "contents/network/timeout-retry-backoff-practical.md",
        "Timeout, Retry, Backoff 실전",
        "network",
        "Retry budget",
        (
            "timeout budget, retry budget, exponential backoff, jitter, fail-fast 를 함께 설계하는 "
            "network reliability 실전 문서다."
        ),
    ),
    _chunk(
        "f",
        "contents/system-design/backpressure-and-load-shedding-design.md",
        "Backpressure and Load Shedding 설계",
        "system-design",
        "Queue depth and overload",
        (
            "backpressure, load shedding, queue depth, admission control, overload protection, "
            "queueing, retry amplification 을 다루는 생존성 설계 문서다."
        ),
    ),
    _chunk(
        "f1",
        "contents/database/idempotency-key-and-deduplication.md",
        "Idempotency Key and Deduplication",
        "database",
        "Idempotency key basics",
        (
            "idempotency key 와 request deduplication 은 POST 중복 요청 방지, request fingerprint, "
            "dedup store, TTL, duplicate suppression 을 함께 설명하는 기초 문서다."
        ),
    ),
    _chunk(
        "f2",
        "contents/system-design/payment-system-ledger-idempotency-reconciliation-design.md",
        "Payment System Ledger, Idempotency, Reconciliation",
        "system-design",
        "Double charge prevention",
        (
            "payment ledger 는 double charge prevention, settlement reconciliation, idempotency key, "
            "ledger append, duplicate payment recovery 를 같이 다룬다."
        ),
    ),
    _chunk(
        "f3",
        "contents/system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md",
        "Idempotency Key Store, Dedup Window, Replay-Safe Retry Design",
        "system-design",
        "Key store replay-safe retry window",
        (
            "idempotency key store 설계는 dedup window, replay-safe retry, request log retention, "
            "key TTL, processing lease, payload hash, duplicate suppression window, safe retry "
            "contract 를 함께 다룬다."
        ),
    ),
    _chunk(
        "g",
        "contents/security/jwt-deep-dive.md",
        "JWT 깊이 파기",
        "security",
        "Claims and sessions",
        (
            "jwt token 의 payload structure, claims, exp, session 과의 차이, authentication 과 "
            "authorization 의 구분을 설명한다."
        ),
    ),
    _chunk(
        "h",
        "contents/security/jwt-signature-verification-failure-playbook.md",
        "JWT Signature Verification Failure Playbook",
        "security",
        "JWKS kid validation ladder",
        (
            "jwt signature verification 은 JWKS fetch, kid selection, issuer binding, audience "
            "validation, claim validation 순서로 점검해야 한다."
        ),
    ),
    _chunk(
        "i",
        "contents/spring/spring-service-layer-transaction-boundary-patterns.md",
        "Spring Service-Layer Transaction Boundary Patterns",
        "spring",
        "Transactional placement",
        (
            "@Transactional 은 controller 나 repository 가 아니라 application service layer "
            "boundary 에 두고 self invocation 을 피하며 remote call 은 가능하면 transaction "
            "밖으로 빼야 한다."
        ),
    ),
    _chunk(
        "j",
        "contents/software-engineering/data-migration-rehearsal-reconciliation-cutover.md",
        "Data Migration Rehearsal, Reconciliation, Cutover",
        "software-engineering",
        "Migration rehearsal",
        (
            "data migration 은 dual write 이후 rehearsal, reconciliation, migration validation, "
            "cutover readiness 를 단계적으로 준비해야 한다."
        ),
    ),
    _chunk(
        "k",
        "contents/system-design/replay-repair-orchestration-control-plane-design.md",
        "Replay / Repair Orchestration Control Plane 설계",
        "system-design",
        "Approval and guardrails",
        (
            "replay, repair, dry run, approval, blast radius budget, execution guardrail 을 관리하는 "
            "control plane 설계 문서다."
        ),
    ),
    _chunk(
        "l",
        "contents/design-pattern/read-model-staleness-read-your-writes.md",
        "Read Model Staleness and Read-Your-Writes",
        "design-pattern",
        "Projection lag and freshness budget",
        (
            "CQRS read model staleness, projection lag, read-your-writes, freshness budget, eventual "
            "consistency UX 계약을 다룬다.\n\n"
            "retrieval-anchor-keywords: 읽기 모델 최신성, 읽기 모델 지연, "
            "방금 저장했는데 안 보여, 저장했는데 옛값이 보임, 예전 값이 보임, "
            "쓴 직후 읽기 보장, 방금 쓴 값 읽기, 오래된 값 조회"
        ),
    ),
    _chunk(
        "m",
        "contents/design-pattern/event-upcaster-compatibility-patterns.md",
        "Event Upcaster Compatibility Patterns",
        "design-pattern",
        "Legacy event replay",
        (
            "event upcaster 는 legacy event replay 와 event schema evolution 에서 compatibility "
            "layer, upcast chain, tolerant reader 를 제공한다."
        ),
    ),
    _chunk(
        "m1",
        "contents/design-pattern/tolerant-reader-event-contract-pattern.md",
        "Tolerant Reader for Event Contracts",
        "design-pattern",
        "Forward-compatible consumer",
        (
            "tolerant reader 는 forward compatible consumer, unknown enum handling, optional field "
            "parsing, event consumer compatibility, contract looseness, live consumer robustness 를 "
            "다룬다."
        ),
    ),
    _chunk(
        "m2",
        "contents/design-pattern/snapshot-versioning-compatibility-pattern.md",
        "Snapshot Versioning and Compatibility Pattern",
        "design-pattern",
        "Restore format version",
        (
            "snapshot versioning 은 snapshot compatibility, snapshot invalidation, restore format "
            "version, snapshot upcast, checkpoint schema drift, partial restore replay tail 을 "
            "다룬다."
        ),
    ),
    _chunk(
        "m3",
        "contents/software-engineering/api-versioning-contract-testing-anti-corruption-layer.md",
        "API Versioning, Contract Testing, Anti-Corruption Layer",
        "software-engineering",
        "Compatibility policy",
        (
            "api versioning 은 schema evolution, compatibility layer, backward compatible additive "
            "field rollout, contract testing, anti-corruption layer, endpoint versioning 을 함께 "
            "다루는 계약 진화 문서다."
        ),
    ),
    _chunk(
        "m4",
        "contents/software-engineering/schema-contract-evolution-cross-service.md",
        "Schema Contract Evolution Across Services",
        "software-engineering",
        "Backward and forward compatibility",
        (
            "cross-service schema evolution 은 api compatibility layer, contract compatibility, "
            "backward compatible payload, forward compatible consumer, consumer tolerance, expand "
            "and contract, additive field rollout 을 함께 다룬다."
        ),
    ),
    _chunk(
        "m5",
        "contents/database/cdc-schema-evolution-compatibility-playbook.md",
        "CDC Schema Evolution, Event Compatibility, and Expand-Contract Playbook",
        "database",
        "Expand-contract rollout",
        (
            "cdc schema evolution playbook 은 old producer, new connector, old consumer 가 함께 "
            "살아도 event compatibility 가 깨지지 않게 expand contract migration, versioned "
            "payload, backward compatible event, forward compatible consumer, debezium schema "
            "change, contract-safe rollout 순서를 운영한다."
        ),
    ),
    _chunk(
        "m6",
        "contents/database/schema-migration-partitioning-cdc-cqrs.md",
        "Schema Migration, Partitioning, CDC, CQRS",
        "database",
        "Survey routing",
        (
            "schema migration, partitioning, cdc, cqrs 를 한 번에 훑는 survey 문서다. broad "
            "survey routing 으로 schema evolution compatibility, cdc outbox, projection rebuild, "
            "read cutover, cutover guardrail 을 연결한다."
        ),
    ),
    _chunk(
        "m7",
        "contents/system-design/zero-downtime-schema-migration-platform-design.md",
        "Zero-Downtime Schema Migration Platform 설계",
        "system-design",
        "Migration control plane",
        (
            "zero downtime schema migration 플랫폼은 expand and contract, compatibility window, "
            "backfill, cutover, migration control plane, deploy rollback safety 를 함께 다루는 "
            "generic migration deep dive 다."
        ),
    ),
    _chunk(
        "n",
        "contents/design-pattern/projection-rebuild-backfill-cutover-pattern.md",
        "Projection Rebuild, Backfill, and Cutover Pattern",
        "design-pattern",
        "Dual run and watermark",
        (
            "projection rebuild, backfill, cutover, dual projection run, projection watermark, replay "
            "safe projector 를 운영 절차와 함께 다룬다."
        ),
    ),
    _chunk(
        "o",
        "contents/language/java/java-language-basics.md",
        "자바 언어의 구조와 기본 문법",
        "language",
        "Java program structure",
        (
            "java language basics 는 기본 문법, 데이터 타입, 변수, 배열, 제어문, bytecode, JVM 실행 "
            "흐름과 플랫폼 구조를 함께 설명한다."
        ),
    ),
    _chunk(
        "p",
        "contents/language/java/jvm-gc-jmm-overview.md",
        "JVM, GC, JMM",
        "language",
        "Runtime overview",
        (
            "JVM, GC, JMM overview 는 heap, stack, metaspace, classloader, bytecode execution "
            "flow, safepoint, happens-before, visibility, ordering 을 runtime overview 관점에서 "
            "큰 그림으로 설명한다."
        ),
    ),
    _chunk(
        "p1",
        "contents/language/java/classloader-memory-leak-playbook.md",
        "Classloader Memory Leak Playbook",
        "language",
        "Metaspace leak triage",
        (
            "classloader memory leak playbook 는 metaspace leak, thread context class loader, "
            "static cache pinning, hot redeploy leak triage 처럼 classloader deep dive 에 "
            "집중하는 문서다."
        ),
    ),
    _chunk(
        "p2",
        "contents/language/java/jit-warmup-deoptimization.md",
        "JIT Warmup and Deoptimization",
        "language",
        "Compiler profiling deep dive",
        (
            "jit warmup deoptimization 문서는 tiered compilation, inlining, code cache, profile "
            "pollution, deopt trigger 같은 JVM performance deep dive 를 다룬다."
        ),
    ),
    _chunk(
        "q",
        "contents/language/java/java-concurrency-utilities.md",
        "Java 동시성 유틸리티",
        "language",
        "ExecutorService and Future",
        (
            "Java concurrency utilities 문서는 ExecutorService, thread pool, Callable, Future, "
            "CompletableFuture, ConcurrentHashMap, CountDownLatch, Phaser 를 입문 overview 와 "
            "coordination primitives 기준으로 폭넓게 다룬다."
        ),
    ),
    _chunk(
        "q1",
        "contents/language/java/completablefuture-execution-model-common-pool-pitfalls.md",
        "CompletableFuture Execution Model and Common Pool Pitfalls",
        "language",
        "Common pool and blocking stage hazards",
        (
            "completablefuture execution model common pool pitfalls 문서는 default executor, "
            "common pool, async stage, blocking stage, thread hopping, forkjoinpool starvation "
            "같은 실행 경계 위험을 설명한다."
        ),
    ),
    _chunk(
        "q2",
        "contents/language/java/forkjoinpool-work-stealing.md",
        "ForkJoinPool Work-Stealing",
        "language",
        "CommonPool work-stealing tradeoffs",
        (
            "forkjoinpool work-stealing 문서는 commonPool, deque, work-stealing, managed blocker, "
            "blocking I/O, starvation tradeoff 를 설명하는 sibling deep dive 다."
        ),
    ),
    _chunk(
        "r",
        "contents/language/java/executor-sizing-queue-rejection-policy.md",
        "Executor Sizing, Queue, Rejection Policy",
        "language",
        "Thread pool tuning",
        (
            "executor sizing, queue capacity, rejection policy, worker saturation 처럼 thread pool "
            "튜닝에 집중하는 심화 문서다."
        ),
    ),
    _chunk(
        "r1",
        "contents/language/java/virtual-threads-project-loom.md",
        "Virtual Threads(Project Loom)",
        "language",
        "Virtual thread primer",
        (
            "virtual threads project loom primer 는 thread-per-request, blocking I/O, carrier "
            "thread, mount unmount, pinning basics 를 큰 그림으로 설명하는 입문 문서다."
        ),
    ),
    _chunk(
        "r2",
        "contents/language/java/virtual-thread-migration-pinning-threadlocal-pool-boundaries.md",
        "Virtual Thread Migration: Pinning, ThreadLocal, and Pool Boundary Strategy",
        "language",
        "Migration boundary audit",
        (
            "virtual thread migration 문서는 pinning, ThreadLocal migration, MDC propagation, "
            "pool boundary strategy, synchronized I/O, Spring JDBC HttpClient 경계 점검을 다룬다."
        ),
    ),
    _chunk(
        "r3",
        "contents/language/java/connection-budget-alignment-after-loom.md",
        "Connection Budget Alignment After Loom",
        "language",
        "Datasource and bulkhead budget",
        (
            "connection budget alignment after loom 문서는 datasource pool sizing, DB safe "
            "concurrency, outbound HTTP bulkhead budget, request admission, capacity planning 을 "
            "정리한다."
        ),
    ),
    _chunk(
        "r4",
        "contents/language/java/jfr-loom-incident-signal-map.md",
        "JFR Loom Incident Signal Map",
        "language",
        "ThreadPark and VirtualThreadPinned incident map",
        (
            "jfr loom incident signal map 은 ThreadPark, VirtualThreadPinned, SocketRead, "
            "JavaMonitorEnter, loom observability, incident fingerprint 를 묶어 읽는 playbook 이다."
        ),
    ),
    _chunk(
        "s",
        "contents/data-structure/applied-data-structures-overview.md",
        "응용 자료 구조 개요",
        "data-structure",
        "Problem-pattern routing",
        (
            "applied data structures overview 는 deque, ring buffer, lock-free queue, timing wheel, "
            "heap, bloom filter, count-min sketch, hyperloglog, roaring bitmap, trie, radix tree, "
            "finite state transducer, cache eviction 을 문제 패턴 기준으로 라우팅한다."
        ),
    ),
    _chunk(
        "t",
        "contents/data-structure/ring-buffer.md",
        "Ring Buffer",
        "data-structure",
        "Bounded producer-consumer buffer",
        (
            "ring buffer 는 bounded queue, producer consumer, fixed-size circular buffer, cache "
            "friendly queue 구현에 특화된 자료 구조다."
        ),
    ),
    _chunk(
        "u",
        "contents/language/java/object-oriented-core-principles.md",
        "객체지향 핵심 원리",
        "language",
        "Encapsulation and polymorphism",
        (
            "객체지향 핵심 원리는 클래스, 객체, 인스턴스, 캡슐화, 상속, 다형성, 추상화, 정보 은닉을 "
            "자바 기준으로 설명한다."
        ),
    ),
    _chunk(
        "v",
        "contents/security/jwk-rotation-cache-invalidation-kid-rollover.md",
        "JWK Rotation / Cache Invalidation / `kid` Rollover",
        "security",
        "Rotation window and stale key",
        (
            "JWK rotation 은 JWKS cache invalidation, kid rollover, stale key, JWKS TTL, "
            "refresh storm, known-good key 운영이 핵심이다."
        ),
    ),
    _chunk(
        "w",
        "contents/security/key-rotation-runbook.md",
        "Key Rotation Runbook",
        "security",
        "Dual validation and revoke old key",
        (
            "key rotation runbook 은 dual validation, grace window, revoke old key, rollback "
            "decision, audit trail 절차를 정리한다."
        ),
    ),
    _chunk(
        "x",
        "contents/network/proxy-local-reply-vs-upstream-error-attribution.md",
        "Proxy Local Reply vs Upstream Error Attribution",
        "network",
        "502 503 504 attribution",
        (
            "proxy local reply 와 upstream error attribution 을 구분하고 502 503 504 generated "
            "response 의 error source 를 나눈다."
        ),
    ),
    _chunk(
        "y",
        "contents/network/request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md",
        "Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB",
        "network",
        "Latency breakdown",
        (
            "request timing decomposition 은 DNS time, connect time, TLS handshake, queue wait, "
            "TTFB, TTLB, latency breakdown 을 분리해 본다."
        ),
    ),
    _chunk(
        "z",
        "contents/operating-system/futex-mutex-semaphore-spinlock.md",
        "Futex, Mutex, Semaphore, Spinlock",
        "operating-system",
        "Waiting semantics",
        (
            "futex, mutex, semaphore, spinlock 의 waiting semantics 와 futex_wait, futex_wake, "
            "critical section 감각을 설명한다."
        ),
    ),
    _chunk(
        "aa",
        "contents/operating-system/lock-contention-futex-offcpu-debugging.md",
        "Lock Contention, Futex Wait, Off-CPU Debugging",
        "operating-system",
        "perf lock and off-CPU",
        (
            "lock contention debugging 은 futex wait, off-CPU, perf lock, mutex convoy, blocked "
            "threads, lock handoff 를 같이 본다."
        ),
    ),
    _chunk(
        "ab",
        "contents/operating-system/epoll-kqueue-io-uring.md",
        "epoll, kqueue, io_uring",
        "operating-system",
        "Readiness model overview",
        (
            "epoll, kqueue, io_uring overview 는 readiness model, edge triggered, completion "
            "queue, async I/O 를 비교한다."
        ),
    ),
    _chunk(
        "ac",
        "contents/operating-system/io-uring-sq-cq-basics.md",
        "io_uring SQ, CQ Basics",
        "operating-system",
        "Submission and completion queue",
        (
            "io_uring SQ, CQ basics 는 submission queue, completion queue, SQE, CQE, batching, "
            "registered buffers 를 설명한다."
        ),
    ),
    _chunk(
        "ad",
        "contents/language/java/bigdecimal-money-equality-rounding-serialization-pitfalls.md",
        "`BigDecimal` Money Equality, Rounding, and Serialization Pitfalls",
        "language",
        "equals compareTo rounding",
        (
            "BigDecimal money pitfalls 는 equals, compareTo, hashCode, scale, RoundingMode, "
            "JSON serialization, settlement, idempotency 를 함께 다룬다."
        ),
    ),
    _chunk(
        "ae",
        "contents/language/java-equals-hashcode-comparable-contracts.md",
        "equals, hashCode, Comparable 계약",
        "language",
        "Generic object contracts",
        (
            "equals, hashCode, Comparable contract 는 generic equality semantics, collection key, "
            "ordering consistency 를 설명하는 일반 문서다."
        ),
    ),
    _chunk(
        "ai",
        "contents/language/java/bigdecimal-mathcontext-striptrailingzeros-canonicalization-traps.md",
        "`BigDecimal` `MathContext`, `stripTrailingZeros()`, and Canonicalization Traps",
        "language",
        "Canonicalization and representation",
        (
            "BigDecimal canonicalization traps 는 MathContext, stripTrailingZeros, scientific "
            "notation, toPlainString, precision vs scale, decimal contract 를 다룬다."
        ),
    ),
    _chunk(
        "aj",
        "contents/language/java/value-object-invariants-canonicalization-boundary-design.md",
        "Value Object Invariants, Canonicalization, and Boundary Design",
        "language",
        "Invariant and canonical form",
        (
            "value object canonicalization 은 invariant, canonical form, normalization, boundary "
            "design, scale normalization, equality boundary 를 함께 설계한다."
        ),
    ),
    _chunk(
        "af",
        "contents/system-design/global-traffic-failover-control-plane-design.md",
        "Global Traffic Failover Control Plane 설계",
        "system-design",
        "Regional evacuation and steering",
        (
            "global traffic failover control plane 은 regional evacuation, weighted region routing, "
            "health signal aggregation, edge steering 을 중앙에서 결정한다."
        ),
    ),
    _chunk(
        "ag",
        "contents/system-design/traffic-shadowing-progressive-cutover-design.md",
        "Traffic Shadowing / Progressive Cutover 설계",
        "system-design",
        "Shadow traffic and weighted routing",
        (
            "traffic shadowing 과 progressive cutover 는 shadow traffic, mirrored requests, route "
            "guardrail, weighted routing, abort switch 를 다룬다."
        ),
    ),
    _chunk(
        "ah",
        "contents/database/failover-promotion-read-divergence.md",
        "Failover Promotion과 Read Divergence",
        "database",
        "Promotion and stale primary",
        (
            "failover promotion 과 read divergence 는 stale primary, topology cache, write "
            "fencing, promotion 이후 read split 문제를 다룬다."
        ),
    ),
    _chunk(
        "ak",
        "contents/design-pattern/projection-freshness-slo-pattern.md",
        "Projection Freshness SLO Pattern",
        "design-pattern",
        "Freshness SLI and breach policy",
        (
            "projection freshness slo 는 freshness SLI, freshness SLO, error budget, lag breach "
            "policy, degrade rollback 를 운영 계약으로 다룬다."
        ),
    ),
    _chunk(
        "al",
        "contents/design-pattern/projection-lag-budgeting-pattern.md",
        "Projection Lag Budgeting Pattern",
        "design-pattern",
        "Lag budget and backlog budget",
        (
            "projection lag budgeting 은 freshness budget, lag budget, consumer backlog budget, "
            "staleness tier, lag degrade policy 를 함께 설계한다."
        ),
    ),
    _chunk(
        "am",
        "contents/security/jwks-rotation-cutover-failure-recovery.md",
        "JWKS Rotation Cutover Failure / Recovery",
        "security",
        "Verifier cache skew and old key removal",
        (
            "JWKS rotation cutover failure 는 kid miss after rotation, old key removal failure, "
            "signer cutover rollback, verifier cache skew, dual-publish window 를 다룬다."
        ),
    ),
    _chunk(
        "an",
        "contents/database/failover-visibility-window-topology-cache-playbook.md",
        "Failover Visibility Window, Topology Cache, and Freshness Playbook",
        "database",
        "Visibility window and freshness fence",
        (
            "failover visibility window 은 topology cache invalidation, stale endpoint read, "
            "promotion visibility, freshness fence, post promotion stale reads 를 다룬다."
        ),
    ),
    _chunk(
        "ao",
        "contents/operating-system/io-uring-operational-hazards-registered-resources-sqpoll.md",
        "io_uring Operational Hazards, Registered Resources, SQPOLL",
        "operating-system",
        "Pointer lifetime and SQPOLL",
        (
            "io_uring operational hazards 는 registered buffers, fixed files, SQPOLL, pointer "
            "lifetime, memlock, CQ draining discipline 을 다룬다."
        ),
    ),
    _chunk(
        "ap",
        "contents/operating-system/io-uring-cq-overflow-provided-buffers-iowq-placement.md",
        "io_uring CQ Overflow, Provided Buffers, IOWQ Worker Placement",
        "operating-system",
        "CQ overflow and provided buffers",
        (
            "io_uring CQ overflow 는 provided buffer ring, IOWQ worker placement, completion "
            "backlog, buffer ownership, multishot completion pressure 를 설명한다."
        ),
    ),
    _chunk(
        "aq",
        "contents/design-pattern/read-model-cutover-guardrails.md",
        "Read Model Cutover Guardrails",
        "design-pattern",
        "Freshness guardrail and rollback window",
        (
            "read model cutover guardrails 는 dual read parity, rollback window, cutover fallback, "
            "freshness guardrail, projection canary 를 운영 절차로 다룬다."
        ),
    ),
    _chunk(
        "ar",
        "contents/system-design/receiver-warmup-cache-prefill-write-freeze-cutover-design.md",
        "Receiver Warmup / Cache Prefill / Write Freeze Cutover 설계",
        "system-design",
        "Warmup and freeze cutover",
        (
            "receiver warmup, cache prefill, write freeze cutover 는 cold start mitigation, "
            "prewarm cache, staged traffic enable, rollback window 을 다룬다."
        ),
    ),
    _chunk(
        "as",
        "contents/database/commit-horizon-after-failover-verification.md",
        "Commit Horizon After Failover, Loss Boundaries, and Verification",
        "database",
        "Commit horizon and loss boundary",
        (
            "commit horizon after failover verification 은 loss boundary, last applied position, "
            "write loss audit, promotion verification 을 다룬다."
        ),
    ),
    _chunk(
        "at",
        "contents/software-engineering/strangler-verification-shadow-traffic-metrics.md",
        "Strangler Verification, Shadow Traffic Metrics",
        "software-engineering",
        "Shadow traffic diffing",
        (
            "strangler verification 은 shadow traffic metrics, response diff, semantic equivalence, "
            "cutover metrics, replay safety 를 통해 전환 전 검증을 다룬다."
        ),
    ),
    _chunk(
        "au",
        "contents/system-design/stateful-workload-placement-failover-control-plane-design.md",
        "Stateful Workload Placement / Failover Control Plane 설계",
        "system-design",
        "Leader placement and promotion policy",
        (
            "stateful workload placement failover control plane 은 leader placement, replica "
            "promotion, maintenance drain, standby assignment, quorum-aware scheduling 을 다룬다."
        ),
    ),
    _chunk(
        "av",
        "contents/network/anycast-routing-tradeoffs-edge-failover.md",
        "Anycast Routing Trade-offs, Edge Failover",
        "network",
        "BGP and route convergence",
        (
            "anycast edge failover 는 BGP, route convergence, path asymmetry, nearest edge, PoP, "
            "global load balancing tradeoff 를 다룬다."
        ),
    ),
]


class CsRagSearchTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmpdir = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmpdir.name)
        cls._build_fixture_index(cls.tmp)
        os.environ["WOOWA_RAG_NO_RERANK"] = "1"

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmpdir.cleanup()
        os.environ.pop("WOOWA_RAG_NO_RERANK", None)

    @staticmethod
    def _build_fixture_index(tmp: Path) -> None:
        sqlite_path, dense_path, manifest_path = indexer._paths(tmp)
        conn = indexer._open_sqlite(sqlite_path)
        try:
            indexer._insert_chunks(conn, FIXTURES)
        finally:
            conn.close()
        manifest_path.write_text(
            json.dumps(
                {
                    "index_version": indexer.INDEX_VERSION,
                    "embed_model": "fixture",
                    "embed_dim": 0,
                    "row_count": len(FIXTURES),
                    "corpus_hash": "fixture",
                    "corpus_root": "fixture",
                }
            ),
            encoding="utf-8",
        )
        dense_path.touch()

    def _search(
        self,
        prompt: str,
        *,
        learning_points: list[str] | None = None,
        top_k: int = 4,
    ) -> list[dict]:
        return searcher.search(
            prompt,
            learning_points=learning_points,
            mode="cheap",
            index_root=self.tmp,
            top_k=top_k,
        )

    def assert_path_rank_at_most(
        self,
        hits: list[dict],
        path: str,
        max_rank: int,
    ) -> None:
        paths = [hit["path"] for hit in hits]
        self.assertIn(path, paths, f"expected {path} in hits {paths}")
        rank = paths.index(path) + 1
        self.assertLessEqual(
            rank,
            max_rank,
            f"expected {path} within top-{max_rank}, got rank #{rank} in {paths}",
        )

    def assert_ranks_ahead(
        self,
        hits: list[dict],
        winner: str,
        loser: str,
    ) -> None:
        paths = [hit["path"] for hit in hits]
        self.assertIn(winner, paths, f"missing winner {winner} in {paths}")
        self.assertIn(loser, paths, f"missing loser {loser} in {paths}")
        self.assertLess(paths.index(winner), paths.index(loser), paths)

    def assert_any_path_in_top_k(
        self,
        hits: list[dict],
        candidates: set[str],
        top_k: int,
    ) -> None:
        paths = {hit["path"] for hit in hits[:top_k]}
        self.assertTrue(
            paths & candidates,
            f"expected one of {sorted(candidates)} in top-{top_k}, got {sorted(paths)}",
        )

    def test_repository_boundary_query_prefers_read_model_boundary_doc(self) -> None:
        hits = self._search(
            "aggregate persistence 와 read model query service remote lookup 경계를 어떻게 나눠?",
            learning_points=["repository_boundary"],
            top_k=4,
        )

        self.assertTrue(hits, "expected non-empty result")
        self.assert_path_rank_at_most(
            hits,
            "contents/design-pattern/repository-boundary-aggregate-vs-read-model.md",
            1,
        )
        allowed = {"database", "design-pattern", "spring"}
        self.assertTrue(all(hit["category"] in allowed for hit in hits), hits)

    def test_transaction_decision_query_prefers_locking_framework_doc(self) -> None:
        hits = self._search(
            "transaction boundary isolation locking strategy 와 optimistic pessimistic lock, FOR UPDATE 를 어떻게 같이 정해?",
            learning_points=["transaction_consistency"],
            top_k=3,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/database/transaction-boundary-isolation-locking-decision-framework.md",
            1,
        )
        allowed = {"database", "spring"}
        self.assertTrue(all(hit["category"] in allowed for hit in hits), hits)

    def test_introductory_transaction_query_prefers_primer_doc_over_decision_framework(self) -> None:
        hits = self._search(
            "트랜잭션 격리 수준과 락을 처음 배우는데 큰 그림부터 설명해줘",
            top_k=4,
        )

        primer_doc = "contents/database/transaction-isolation-locking.md"
        decision_doc = "contents/database/transaction-boundary-isolation-locking-decision-framework.md"
        self.assert_path_rank_at_most(hits, primer_doc, 1)
        self.assert_ranks_ahead(hits, primer_doc, decision_doc)
        self.assertTrue(all(hit["category"] == "database" for hit in hits[:3]), hits[:3])

    def test_lock_only_intro_query_prefers_primer_doc_over_decision_framework(self) -> None:
        hits = self._search(
            "optimistic/pessimistic lock 을 처음 배우는데 언제 쓰는지 말고 큰 그림부터 설명해줘",
            top_k=4,
        )

        primer_doc = "contents/database/transaction-isolation-locking.md"
        decision_doc = "contents/database/transaction-boundary-isolation-locking-decision-framework.md"
        self.assert_path_rank_at_most(hits, primer_doc, 1)
        self.assert_ranks_ahead(hits, primer_doc, decision_doc)
        self.assertTrue(all(hit["category"] == "database" for hit in hits[:3]), hits[:3])

    def test_introductory_mvcc_query_prefers_transaction_primer_over_read_view_deep_dives(self) -> None:
        hits = self._search(
            "MVCC 를 처음 배우는데 read view, undo chain 같은 내부 용어 전에 큰 그림부터 설명해줘",
            top_k=5,
        )

        primer_doc = "contents/database/transaction-isolation-locking.md"
        read_view_doc = "contents/database/mvcc-read-view-consistent-read-internals.md"
        undo_doc = "contents/database/undo-record-version-chain-traversal.md"
        self.assert_path_rank_at_most(hits, primer_doc, 1)
        self.assert_ranks_ahead(hits, primer_doc, read_view_doc)
        self.assert_ranks_ahead(hits, primer_doc, undo_doc)
        self.assertTrue(all(hit["category"] == "database" for hit in hits[:3]), hits[:3])

    def test_gap_lock_query_prefers_database_locking_doc(self) -> None:
        hits = self._search(
            "MySQL gap lock next-key lock 어떻게 동작해",
            top_k=4,
        )

        gap_lock_doc = "contents/database/gap-lock-next-key-lock.md"
        deadlock_doc = "contents/database/deadlock-case-study.md"
        self.assert_path_rank_at_most(
            hits,
            gap_lock_doc,
            1,
        )
        self.assertTrue(all(hit["category"] == "database" for hit in hits[:2]), hits)
        self.assert_ranks_ahead(hits, gap_lock_doc, deadlock_doc)
        paths = [hit["path"] for hit in hits]
        os_lock_doc = "contents/operating-system/lock-contention-futex-offcpu-debugging.md"
        if os_lock_doc in paths:
            self.assertLess(
                paths.index(gap_lock_doc),
                paths.index(os_lock_doc),
                paths,
            )

    def test_lock_wait_timeout_query_prefers_database_doc_ahead_of_timeout_doc(self) -> None:
        hits = self._search(
            "InnoDB lock wait timeout 과 next-key lock 은 왜 같이 보나?",
            top_k=4,
        )

        gap_lock_doc = "contents/database/gap-lock-next-key-lock.md"
        deadlock_doc = "contents/database/deadlock-case-study.md"
        self.assert_path_rank_at_most(
            hits,
            gap_lock_doc,
            1,
        )
        self.assert_ranks_ahead(hits, gap_lock_doc, deadlock_doc)
        timeout_doc = "contents/network/timeout-retry-backoff-practical.md"
        paths = [hit["path"] for hit in hits]
        if timeout_doc in paths:
            self.assertLess(
                paths.index(gap_lock_doc),
                paths.index(timeout_doc),
                paths,
            )

    def test_mysql_deadlock_query_prefers_deadlock_doc_over_gap_lock_sibling(self) -> None:
        hits = self._search(
            "MySQL deadlock log 보고 lock ordering 을 어떻게 고쳐?",
            top_k=4,
        )

        deadlock_doc = "contents/database/deadlock-case-study.md"
        gap_lock_doc = "contents/database/gap-lock-next-key-lock.md"
        self.assert_path_rank_at_most(hits, deadlock_doc, 1)
        self.assert_ranks_ahead(hits, deadlock_doc, gap_lock_doc)

    def test_cs_only_jwt_basics_query_prefers_jwt_deep_dive(self) -> None:
        hits = self._search(
            "JWT payload structure 랑 authentication authorization, session 차이가 뭐야?",
            top_k=3,
        )

        self.assertTrue(hits, "cs_only query must still yield results")
        self.assert_path_rank_at_most(hits, "contents/security/jwt-deep-dive.md", 1)

    def test_jwks_validation_query_prefers_failure_playbook(self) -> None:
        hits = self._search(
            "JWKS kid issuer audience signature validation 순서를 어떻게 점검해?",
            top_k=3,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/security/jwt-signature-verification-failure-playbook.md",
            1,
        )

    def test_introductory_jwt_validation_query_prefers_jwt_primer_over_playbook(self) -> None:
        hits = self._search(
            "JWT 를 처음 배우는데 kid issuer audience signature validation 순서를 입문자 기준으로 먼저 설명해줘",
            top_k=4,
        )

        primer_doc = "contents/security/jwt-deep-dive.md"
        playbook_doc = "contents/security/jwt-signature-verification-failure-playbook.md"
        self.assert_path_rank_at_most(hits, primer_doc, 1)
        self.assert_ranks_ahead(hits, primer_doc, playbook_doc)

    def test_timeout_query_prefers_retry_budget_doc(self) -> None:
        hits = self._search(
            "timeout budget retry budget exponential backoff jitter",
            top_k=3,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/network/timeout-retry-backoff-practical.md",
            1,
        )

    def test_backpressure_query_prefers_overload_doc_ahead_of_timeout_doc(self) -> None:
        hits = self._search(
            "backpressure load shedding queueing retry amplification",
            top_k=4,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/system-design/backpressure-and-load-shedding-design.md",
            1,
        )
        self.assert_ranks_ahead(
            hits,
            "contents/system-design/backpressure-and-load-shedding-design.md",
            "contents/network/timeout-retry-backoff-practical.md",
        )

    def test_key_store_replay_safe_retry_query_prefers_key_store_doc(self) -> None:
        hits = self._search(
            "idempotency key store 에서 dedup-window 와 replay-safe-retry 를 어떻게 같이 설계해?",
            top_k=5,
        )

        key_store_doc = (
            "contents/system-design/"
            "idempotency-key-store-dedup-window-replay-safe-retry-design.md"
        )
        ledger_doc = (
            "contents/system-design/"
            "payment-system-ledger-idempotency-reconciliation-design.md"
        )
        database_doc = "contents/database/idempotency-key-and-deduplication.md"
        self.assert_path_rank_at_most(
            hits,
            key_store_doc,
            1,
        )
        self.assert_ranks_ahead(hits, key_store_doc, ledger_doc)
        self.assert_ranks_ahead(hits, key_store_doc, database_doc)

    def test_key_store_dedup_window_lease_query_prefers_key_store_doc_over_ledger_doc(self) -> None:
        hits = self._search(
            "idempotency key store 에서 dedup-window TTL 이랑 processing lease 를 어떻게 같이 설계해?",
            top_k=5,
        )

        key_store_doc = (
            "contents/system-design/"
            "idempotency-key-store-dedup-window-replay-safe-retry-design.md"
        )
        ledger_doc = (
            "contents/system-design/"
            "payment-system-ledger-idempotency-reconciliation-design.md"
        )
        database_doc = "contents/database/idempotency-key-and-deduplication.md"

        self.assert_path_rank_at_most(hits, key_store_doc, 1)
        self.assert_ranks_ahead(hits, key_store_doc, ledger_doc)
        self.assert_ranks_ahead(hits, key_store_doc, database_doc)

    def test_key_store_request_log_retention_ttl_query_prefers_key_store_doc_over_base_doc(self) -> None:
        hits = self._search(
            "idempotency key store 에서 request-log retention TTL 이랑 key TTL 을 어떻게 같이 잡아야 해?",
            top_k=5,
        )

        key_store_doc = (
            "contents/system-design/"
            "idempotency-key-store-dedup-window-replay-safe-retry-design.md"
        )
        ledger_doc = (
            "contents/system-design/"
            "payment-system-ledger-idempotency-reconciliation-design.md"
        )
        database_doc = "contents/database/idempotency-key-and-deduplication.md"

        self.assert_path_rank_at_most(hits, key_store_doc, 1)
        self.assert_ranks_ahead(hits, key_store_doc, ledger_doc)
        self.assert_ranks_ahead(hits, key_store_doc, database_doc)

    def test_spring_service_boundary_query_prefers_service_layer_doc(self) -> None:
        hits = self._search(
            "@Transactional 을 controller/repository 가 아닌 application service layer 에 두고 self invocation 과 remote call 을 어떻게 피하지?",
            learning_points=["transaction_consistency"],
            top_k=3,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/spring/spring-service-layer-transaction-boundary-patterns.md",
            1,
        )

    def test_data_migration_query_prefers_rehearsal_cutover_doc(self) -> None:
        hits = self._search(
            "dual write rehearsal reconciliation cutover migration validation",
            top_k=3,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/software-engineering/data-migration-rehearsal-reconciliation-cutover.md",
            1,
        )

    def test_replay_repair_query_prefers_control_plane_doc(self) -> None:
        hits = self._search(
            "replay repair approval blast radius guardrail dry run",
            top_k=3,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/system-design/replay-repair-orchestration-control-plane-design.md",
            1,
        )

    def test_read_model_query_keeps_read_your_writes_doc_within_top3(self) -> None:
        hits = self._search(
            "CQRS read model staleness 와 read-your-writes projection lag",
            top_k=5,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
            3,
        )
        self.assert_any_path_in_top_k(
            hits,
            {
                "contents/design-pattern/projection-freshness-slo-pattern.md",
                "contents/design-pattern/projection-lag-budgeting-pattern.md",
            },
            5,
        )

    def test_korean_read_model_symptom_query_uses_primer_fixture_anchors_without_signal_expansion(
        self,
    ) -> None:
        with mock.patch.object(
            signal_rules,
            "expand_query",
            side_effect=lambda prompt, topic_hints=None: searcher._fallback_tokens(prompt),
        ):
            hits = self._search("방금 저장했는데 안 보여", top_k=3)

        self.assert_path_rank_at_most(
            hits,
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
            1,
        )

    def test_event_upcaster_query_prefers_compatibility_doc(self) -> None:
        hits = self._search(
            "legacy event replay 를 위한 event upcaster compatibility layer 와 schema evolution",
            top_k=3,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/design-pattern/event-upcaster-compatibility-patterns.md",
            1,
        )

    def test_upcaster_fixture_replay_query_beats_tolerant_reader_sibling(self) -> None:
        hits = self._search(
            "event upcaster 로 legacy fixture replay 와 semantic versioned event upcast chain 을 어떻게 테스트해?",
            top_k=5,
        )

        upcaster_doc = "contents/design-pattern/event-upcaster-compatibility-patterns.md"
        tolerant_reader_doc = "contents/design-pattern/tolerant-reader-event-contract-pattern.md"
        self.assert_path_rank_at_most(hits, upcaster_doc, 1)
        self.assert_ranks_ahead(hits, upcaster_doc, tolerant_reader_doc)

    def test_upcaster_snapshot_mixed_replay_query_beats_snapshot_sibling(self) -> None:
        hits = self._search(
            "snapshot 이전/이후 혼합 replay 에서 event upcaster compatibility policy 로 legacy event 를 current model 로 끌어올리는 기준이 궁금해",
            top_k=5,
        )

        upcaster_doc = "contents/design-pattern/event-upcaster-compatibility-patterns.md"
        snapshot_doc = "contents/design-pattern/snapshot-versioning-compatibility-pattern.md"
        self.assert_path_rank_at_most(hits, upcaster_doc, 1)
        self.assert_ranks_ahead(hits, upcaster_doc, snapshot_doc)

    def test_api_schema_evolution_query_prefers_api_contract_doc_over_upcaster_family(
        self,
    ) -> None:
        hits = self._search(
            "REST API versioning 과 schema evolution 에서 compatibility layer 를 어디까지 둬야 해?",
            top_k=5,
        )

        api_doc = "contents/software-engineering/api-versioning-contract-testing-anti-corruption-layer.md"
        upcaster_doc = "contents/design-pattern/event-upcaster-compatibility-patterns.md"
        paths = [hit["path"] for hit in hits]
        self.assert_path_rank_at_most(hits, api_doc, 1)
        self.assertNotIn(upcaster_doc, paths[:2], paths)

    def test_cross_service_schema_evolution_query_prefers_contract_doc_over_upcaster_family(
        self,
    ) -> None:
        hits = self._search(
            "cross-service schema evolution 에서 backward compatible payload 와 consumer tolerance 를 어떻게 설계해?",
            top_k=5,
        )

        schema_doc = "contents/software-engineering/schema-contract-evolution-cross-service.md"
        upcaster_doc = "contents/design-pattern/event-upcaster-compatibility-patterns.md"
        paths = [hit["path"] for hit in hits]
        self.assert_path_rank_at_most(hits, schema_doc, 1)
        self.assertNotIn(upcaster_doc, paths[:2], paths)

    def test_cdc_schema_evolution_query_prefers_dedicated_playbook_over_generic_migration_docs(
        self,
    ) -> None:
        hits = self._search(
            "CDC schema evolution 에서 expand-contract migration, versioned payload, forward compatible consumer 순서를 어떻게 잡아?",
            top_k=10,
        )

        cdc_doc = "contents/database/cdc-schema-evolution-compatibility-playbook.md"
        cross_service_doc = "contents/software-engineering/schema-contract-evolution-cross-service.md"
        survey_doc = "contents/database/schema-migration-partitioning-cdc-cqrs.md"
        migration_doc = "contents/system-design/zero-downtime-schema-migration-platform-design.md"

        self.assert_path_rank_at_most(hits, cdc_doc, 1)
        self.assert_ranks_ahead(hits, cdc_doc, cross_service_doc)
        self.assert_ranks_ahead(hits, cdc_doc, survey_doc)
        self.assert_ranks_ahead(hits, cdc_doc, migration_doc)

    def test_projection_rebuild_query_prefers_cutover_doc(self) -> None:
        hits = self._search(
            "projection rebuild backfill cutover dual run watermark replay safe projector",
            top_k=3,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/design-pattern/projection-rebuild-backfill-cutover-pattern.md",
            1,
        )

    def test_projection_watermark_query_keeps_projection_family_stable(self) -> None:
        hits = self._search(
            "read model cutover 에서 dual projection run 이랑 projection watermark 를 어떻게 써?",
            top_k=5,
        )

        self.assert_any_path_in_top_k(
            hits,
            {
                "contents/design-pattern/projection-rebuild-backfill-cutover-pattern.md",
                "contents/design-pattern/read-model-cutover-guardrails.md",
            },
            3,
        )
        self.assertIn(
            "contents/design-pattern/projection-rebuild-backfill-cutover-pattern.md",
            [hit["path"] for hit in hits[:5]],
        )
        self.assert_any_path_in_top_k(
            hits,
            {
                "contents/design-pattern/read-model-staleness-read-your-writes.md",
                "contents/design-pattern/projection-freshness-slo-pattern.md",
            },
            5,
        )

    def test_java_basics_query_prefers_java_language_basics_doc(self) -> None:
        hits = self._search(
            "자바 기본 문법 데이터 타입 바이트코드 JVM 실행 흐름을 한 번에 정리해줘",
            top_k=3,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/language/java/java-language-basics.md",
            1,
        )
        self.assertIn("language", {hit["category"] for hit in hits})

    def test_jvm_overview_query_prefers_runtime_overview_doc(self) -> None:
        hits = self._search(
            "JVM GC JMM 차이랑 happens-before 를 한 번에 개념 잡고 싶어",
            top_k=3,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/language/java/jvm-gc-jmm-overview.md",
            1,
        )
        self.assert_ranks_ahead(
            hits,
            "contents/language/java/jvm-gc-jmm-overview.md",
            "contents/language/java/java-language-basics.md",
        )

    def test_introductory_java_runtime_query_prefers_overview_doc_over_deep_dive_siblings(self) -> None:
        hits = self._search(
            "자바 런타임을 처음 배우는데 classloader JIT GC JMM 차이를 큰 그림으로 먼저 설명해줘",
            top_k=6,
        )

        primer_doc = "contents/language/java/jvm-gc-jmm-overview.md"
        classloader_doc = "contents/language/java/classloader-memory-leak-playbook.md"
        jit_doc = "contents/language/java/jit-warmup-deoptimization.md"
        self.assert_path_rank_at_most(hits, primer_doc, 1)
        self.assert_ranks_ahead(hits, primer_doc, classloader_doc)
        self.assert_ranks_ahead(hits, primer_doc, jit_doc)

    def test_classloader_deep_dive_query_prefers_classloader_doc_over_runtime_overview(self) -> None:
        hits = self._search(
            "metaspace leak thread context class loader static cache pinning hot redeploy leak triage 를 어떻게 해?",
            top_k=8,
        )

        classloader_doc = "contents/language/java/classloader-memory-leak-playbook.md"
        overview_doc = "contents/language/java/jvm-gc-jmm-overview.md"
        self.assert_path_rank_at_most(hits, classloader_doc, 1)
        self.assert_ranks_ahead(hits, classloader_doc, overview_doc)

    def test_jit_warmup_query_prefers_jit_doc_over_runtime_overview(self) -> None:
        hits = self._search(
            "tiered compilation inlining code cache profile pollution deopt trigger 를 JIT warmup 관점에서 설명해줘",
            top_k=5,
        )

        jit_doc = "contents/language/java/jit-warmup-deoptimization.md"
        overview_doc = "contents/language/java/jvm-gc-jmm-overview.md"
        self.assert_path_rank_at_most(hits, jit_doc, 1)
        self.assert_ranks_ahead(hits, jit_doc, overview_doc)

    def test_java_concurrency_query_prefers_overview_doc(self) -> None:
        hits = self._search(
            "Java 에서 ExecutorService Future CompletableFuture CountDownLatch 와 queue rejection policy 까지 포함해 동시성 유틸을 전체적으로 훑고 싶어",
            top_k=5,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/language/java/java-concurrency-utilities.md",
            1,
        )
        self.assert_ranks_ahead(
            hits,
            "contents/language/java/java-concurrency-utilities.md",
            "contents/language/java/executor-sizing-queue-rejection-policy.md",
        )

    def test_introductory_java_concurrency_query_prefers_overview_doc_over_executor_tuning(self) -> None:
        hits = self._search(
            "Java 동시성을 처음 배우는데 queue rejection policy 같은 튜닝보다 ExecutorService "
            "Future CompletableFuture CountDownLatch 를 큰 그림부터 설명해줘",
            top_k=5,
        )

        primer_doc = "contents/language/java/java-concurrency-utilities.md"
        tuning_doc = "contents/language/java/executor-sizing-queue-rejection-policy.md"
        self.assert_path_rank_at_most(hits, primer_doc, 1)
        self.assert_ranks_ahead(hits, primer_doc, tuning_doc)
        paths = [hit["path"] for hit in hits]
        runtime_doc = "contents/language/java/jvm-gc-jmm-overview.md"
        if runtime_doc in paths:
            self.assertLess(paths.index(primer_doc), paths.index(runtime_doc), paths)

    def test_beginner_future_completablefuture_query_prefers_overview_doc_over_common_pool_pitfalls(
        self,
    ) -> None:
        hits = self._search(
            "Future CompletableFuture 를 처음 배우는데 ExecutorService Callable CountDownLatch "
            "큰 그림부터 정리해줘",
            top_k=5,
        )

        overview_doc = "contents/language/java/java-concurrency-utilities.md"
        common_pool_doc = (
            "contents/language/java/completablefuture-execution-model-common-pool-pitfalls.md"
        )
        forkjoin_doc = "contents/language/java/forkjoinpool-work-stealing.md"
        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assert_ranks_ahead(hits, overview_doc, common_pool_doc)
        paths = [hit["path"] for hit in hits]
        if forkjoin_doc in paths:
            self.assertLess(paths.index(overview_doc), paths.index(forkjoin_doc), paths)

    def test_common_pool_completablefuture_query_prefers_pitfall_doc_over_overview(self) -> None:
        hits = self._search(
            "CompletableFuture common pool default executor blocking stage thread hopping "
            "starvation 을 어떻게 이해해야 해?",
            top_k=5,
        )

        common_pool_doc = (
            "contents/language/java/completablefuture-execution-model-common-pool-pitfalls.md"
        )
        overview_doc = "contents/language/java/java-concurrency-utilities.md"
        forkjoin_doc = "contents/language/java/forkjoinpool-work-stealing.md"
        self.assert_path_rank_at_most(hits, common_pool_doc, 1)
        self.assert_ranks_ahead(hits, common_pool_doc, overview_doc)
        paths = [hit["path"] for hit in hits]
        if forkjoin_doc in paths:
            self.assertLess(paths.index(common_pool_doc), paths.index(forkjoin_doc), paths)

    def test_executor_tuning_query_prefers_executor_doc_over_concurrency_overview(self) -> None:
        hits = self._search(
            "executor sizing queue capacity rejection policy worker saturation thread pool tuning 을 어떻게 잡아?",
            top_k=5,
        )

        tuning_doc = "contents/language/java/executor-sizing-queue-rejection-policy.md"
        overview_doc = "contents/language/java/java-concurrency-utilities.md"
        self.assert_path_rank_at_most(hits, tuning_doc, 1)
        self.assert_ranks_ahead(hits, tuning_doc, overview_doc)

    def test_introductory_virtual_thread_query_prefers_loom_primer_over_operational_siblings(self) -> None:
        hits = self._search(
            "Project Loom virtual threads 를 처음 배우는데 blocking I/O, carrier thread, "
            "pinning 큰 그림부터 설명해줘",
            top_k=6,
        )

        primer_doc = "contents/language/java/virtual-threads-project-loom.md"
        migration_doc = (
            "contents/language/java/virtual-thread-migration-pinning-threadlocal-pool-boundaries.md"
        )
        budget_doc = "contents/language/java/connection-budget-alignment-after-loom.md"
        incident_doc = "contents/language/java/jfr-loom-incident-signal-map.md"
        self.assert_path_rank_at_most(hits, primer_doc, 1)
        self.assert_ranks_ahead(hits, primer_doc, migration_doc)
        self.assert_ranks_ahead(hits, primer_doc, budget_doc)
        paths = [hit["path"] for hit in hits]
        if incident_doc in paths:
            self.assertLess(paths.index(primer_doc), paths.index(incident_doc), paths)
        tx_doc = "contents/database/transaction-isolation-locking.md"
        if tx_doc in paths:
            self.assertLess(paths.index(primer_doc), paths.index(tx_doc), paths)

    def test_virtual_thread_migration_query_prefers_migration_doc_over_primer(self) -> None:
        hits = self._search(
            "virtual thread migration 에서 pinning ThreadLocal pool boundary 를 어떻게 점검해?",
            top_k=5,
        )

        migration_doc = (
            "contents/language/java/virtual-thread-migration-pinning-threadlocal-pool-boundaries.md"
        )
        primer_doc = "contents/language/java/virtual-threads-project-loom.md"
        self.assert_path_rank_at_most(hits, migration_doc, 1)
        self.assert_ranks_ahead(hits, migration_doc, primer_doc)

    def test_virtual_thread_budget_query_prefers_connection_budget_doc_over_primer(self) -> None:
        hits = self._search(
            "Loom 이후 datasource pool sizing, DB safe concurrency, outbound HTTP bulkhead "
            "예산을 어떻게 맞춰?",
            top_k=5,
        )

        budget_doc = "contents/language/java/connection-budget-alignment-after-loom.md"
        primer_doc = "contents/language/java/virtual-threads-project-loom.md"
        self.assert_path_rank_at_most(hits, budget_doc, 1)
        self.assert_ranks_ahead(hits, budget_doc, primer_doc)

    def test_jfr_loom_incident_query_prefers_incident_map_over_primer(self) -> None:
        hits = self._search(
            "JFR Loom incident 에서 ThreadPark VirtualThreadPinned SocketRead "
            "JavaMonitorEnter 를 어떻게 묶어 읽어?",
            top_k=5,
        )

        incident_doc = "contents/language/java/jfr-loom-incident-signal-map.md"
        primer_doc = "contents/language/java/virtual-threads-project-loom.md"
        self.assert_path_rank_at_most(hits, incident_doc, 1)
        self.assert_ranks_ahead(hits, incident_doc, primer_doc)

    def test_applied_data_structures_query_prefers_overview_router_doc(self) -> None:
        hits = self._search(
            "ring buffer bloom filter hyperloglog trie 같은 응용 자료 구조를 문제 패턴별로 어디서부터 읽어야 해?",
            top_k=4,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/data-structure/applied-data-structures-overview.md",
            1,
        )
        self.assert_ranks_ahead(
            hits,
            "contents/data-structure/applied-data-structures-overview.md",
            "contents/data-structure/ring-buffer.md",
        )

    def test_java_oop_query_prefers_object_oriented_overview_doc(self) -> None:
        hits = self._search(
            "객체지향 캡슐화 상속 다형성 추상화를 자바 기준으로 정리해줘",
            top_k=3,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/language/java/object-oriented-core-principles.md",
            1,
        )

    def test_jwks_rotation_query_keeps_rollover_doc_within_top3(self) -> None:
        hits = self._search(
            "JWKS key rotation 때 kid rollover 와 cache invalidation 을 어떻게 안전하게 운영해?",
            top_k=4,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/security/jwk-rotation-cache-invalidation-kid-rollover.md",
            3,
        )
        self.assertIn(
            "contents/security/key-rotation-runbook.md",
            [hit["path"] for hit in hits[:4]],
        )

    def test_jwks_recovery_query_keeps_recovery_docs_within_top3(self) -> None:
        hits = self._search(
            "kid miss storm, stale-if-error, fail-closed 로 JWKS recovery ladder 를 어떻게 운영해?",
            top_k=5,
        )

        self.assert_any_path_in_top_k(
            hits,
            {
                "contents/security/jwt-jwks-outage-recovery-failover-drills.md",
                "contents/security/jwks-rotation-cutover-failure-recovery.md",
            },
            3,
        )
        self.assertIn(
            "contents/security/jwk-rotation-cache-invalidation-kid-rollover.md",
            [hit["path"] for hit in hits[:5]],
        )

    def test_jwks_rotation_failure_query_keeps_failure_doc_within_top3(self) -> None:
        hits = self._search(
            "old key removal failure 와 signer cutover rollback 이 동시에 나면 어디부터 복구해?",
            top_k=5,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/security/jwks-rotation-cutover-failure-recovery.md",
            3,
        )
        self.assert_any_path_in_top_k(
            hits,
            {
                "contents/security/jwk-rotation-cache-invalidation-kid-rollover.md",
                "contents/security/jwt-signature-verification-failure-playbook.md",
                "contents/security/jwt-jwks-outage-recovery-failover-drills.md",
            },
            5,
        )

    def test_key_rotation_runbook_query_keeps_runbook_doc_within_top3(self) -> None:
        hits = self._search(
            "key rotation runbook 에서 dual validation grace window revoke old key 순서를 어떻게 잡아?",
            top_k=4,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/security/key-rotation-runbook.md",
            3,
        )
        self.assertIn(
            "contents/security/jwk-rotation-cache-invalidation-kid-rollover.md",
            [hit["path"] for hit in hits[:4]],
        )

    def test_timeout_attribution_query_prefers_proxy_error_source_doc(self) -> None:
        hits = self._search(
            "timeout attribution 을 할 때 local reply 랑 upstream error source 를 어떻게 구분해?",
            top_k=4,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/network/proxy-local-reply-vs-upstream-error-attribution.md",
            1,
        )
        self.assert_ranks_ahead(
            hits,
            "contents/network/proxy-local-reply-vs-upstream-error-attribution.md",
            "contents/network/request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md",
        )

    def test_request_timing_query_prefers_latency_breakdown_doc(self) -> None:
        hits = self._search(
            "DNS connect TLS handshake TTFB TTLB queue wait latency breakdown 을 보고 싶어",
            top_k=4,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/network/request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md",
            1,
        )

    def test_anycast_failover_query_keeps_anycast_doc_within_top3(self) -> None:
        hits = self._search(
            "anycast edge failover tradeoff 랑 route convergence 차이를 알고 싶어",
            top_k=5,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/network/anycast-routing-tradeoffs-edge-failover.md",
            3,
        )
        self.assertIn(
            "contents/system-design/global-traffic-failover-control-plane-design.md",
            [hit["path"] for hit in hits[:5]],
        )

    def test_futex_debugging_query_prefers_offcpu_doc(self) -> None:
        hits = self._search(
            "futex wait 때문에 off-CPU lock contention 이 생길 때 perf lock 으로 어디부터 봐야 해?",
            top_k=4,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/operating-system/lock-contention-futex-offcpu-debugging.md",
            1,
        )
        self.assert_ranks_ahead(
            hits,
            "contents/operating-system/lock-contention-futex-offcpu-debugging.md",
            "contents/operating-system/futex-mutex-semaphore-spinlock.md",
        )

    def test_io_uring_overview_query_keeps_overview_doc_within_top3(self) -> None:
        hits = self._search(
            "epoll kqueue io_uring 차이와 readiness model 을 개념적으로 보고 싶어",
            top_k=4,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/operating-system/epoll-kqueue-io-uring.md",
            3,
        )
        self.assertIn(
            "contents/operating-system/io-uring-sq-cq-basics.md",
            [hit["path"] for hit in hits[:4]],
        )

    def test_introductory_io_uring_queue_query_prefers_overview_doc_over_sq_cq_doc(self) -> None:
        hits = self._search(
            "io_uring 을 처음 배우는데 SQ CQ 보다 epoll kqueue 랑 차이를 먼저 개념적으로 알고 싶어",
            top_k=4,
        )

        overview_doc = "contents/operating-system/epoll-kqueue-io-uring.md"
        basics_doc = "contents/operating-system/io-uring-sq-cq-basics.md"
        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assert_ranks_ahead(hits, overview_doc, basics_doc)

    def test_io_uring_queue_query_keeps_sq_cq_doc_within_top3(self) -> None:
        hits = self._search(
            "epoll kqueue 보다 io_uring 의 SQ CQ submission queue completion queue 가 어떻게 도는지 알고 싶어",
            top_k=4,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/operating-system/io-uring-sq-cq-basics.md",
            3,
        )
        self.assertIn(
            "contents/operating-system/epoll-kqueue-io-uring.md",
            [hit["path"] for hit in hits[:4]],
        )

    def test_io_uring_hazards_query_keeps_operational_doc_within_top3(self) -> None:
        hits = self._search(
            "io_uring registered buffers, fixed files, SQPOLL 같은 operational hazards 는 어디서 봐야 해?",
            top_k=5,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/operating-system/io-uring-operational-hazards-registered-resources-sqpoll.md",
            3,
        )
        self.assert_any_path_in_top_k(
            hits,
            {
                "contents/operating-system/io-uring-sq-cq-basics.md",
                "contents/operating-system/io-uring-cq-overflow-provided-buffers-iowq-placement.md",
            },
            5,
        )

    def test_io_uring_cq_overflow_query_keeps_cq_doc_within_top3(self) -> None:
        hits = self._search(
            "CQ overflow, provided buffer ring, IOWQ worker placement 은 어디서 봐야 해?",
            top_k=5,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/operating-system/io-uring-cq-overflow-provided-buffers-iowq-placement.md",
            3,
        )
        self.assert_any_path_in_top_k(
            hits,
            {
                "contents/operating-system/io-uring-operational-hazards-registered-resources-sqpoll.md",
                "contents/operating-system/io-uring-sq-cq-basics.md",
            },
            5,
        )

    def test_bigdecimal_query_keeps_money_pitfalls_doc_within_top3(self) -> None:
        hits = self._search(
            "BigDecimal equals compareTo rounding 직렬화 함정이 뭐야?",
            top_k=4,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/language/java/bigdecimal-money-equality-rounding-serialization-pitfalls.md",
            3,
        )
        self.assert_any_path_in_top_k(
            hits,
            {
                "contents/language/java/bigdecimal-mathcontext-striptrailingzeros-canonicalization-traps.md",
                "contents/language/java/value-object-invariants-canonicalization-boundary-design.md",
            },
            4,
        )

    def test_bigdecimal_canonicalization_query_keeps_canonicalization_doc_within_top3(self) -> None:
        hits = self._search(
            "BigDecimal canonicalization, MathContext, stripTrailingZeros, toPlainString 함정이 뭐야?",
            top_k=5,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/language/java/bigdecimal-mathcontext-striptrailingzeros-canonicalization-traps.md",
            3,
        )
        self.assert_any_path_in_top_k(
            hits,
            {
                "contents/language/java/bigdecimal-money-equality-rounding-serialization-pitfalls.md",
                "contents/language/java/value-object-invariants-canonicalization-boundary-design.md",
            },
            5,
        )

    def test_value_object_canonicalization_query_keeps_value_object_doc_within_top3(self) -> None:
        hits = self._search(
            "value object canonicalization 으로 scale normalization invariant 를 강제해야 하나?",
            top_k=5,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/language/java/value-object-invariants-canonicalization-boundary-design.md",
            3,
        )
        self.assert_any_path_in_top_k(
            hits,
            {
                "contents/language/java/bigdecimal-mathcontext-striptrailingzeros-canonicalization-traps.md",
                "contents/language/java/bigdecimal-money-equality-rounding-serialization-pitfalls.md",
            },
            5,
        )

    def test_projection_freshness_query_keeps_staleness_doc_within_top3(self) -> None:
        hits = self._search(
            "projection freshness budget 이랑 read-your-writes 는 어떻게 설명해?",
            top_k=5,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/design-pattern/read-model-staleness-read-your-writes.md",
            3,
        )
        self.assert_any_path_in_top_k(
            hits,
            {
                "contents/design-pattern/projection-freshness-slo-pattern.md",
                "contents/design-pattern/projection-lag-budgeting-pattern.md",
            },
            5,
        )

    def test_introductory_projection_freshness_query_prefers_staleness_doc_over_cutover_playbooks(
        self,
    ) -> None:
        hits = self._search(
            "read model freshness 를 처음 배우는데 read model cutover guardrails 나 projection rebuild backfill cutover playbook 전에 stale read 랑 read-your-writes 큰 그림부터 알고 싶어",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        guardrail_doc = "contents/design-pattern/read-model-cutover-guardrails.md"
        rebuild_doc = "contents/design-pattern/projection-rebuild-backfill-cutover-pattern.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assert_ranks_ahead(hits, overview_doc, guardrail_doc)
        self.assert_ranks_ahead(hits, overview_doc, rebuild_doc)
        self.assertTrue(all(hit["category"] == "design-pattern" for hit in hits[:3]), hits[:3])

    def test_introductory_projection_primer_vs_guardrail_compare_query_keeps_primer_first(
        self,
    ) -> None:
        hits = self._search(
            "read model freshness 를 처음 배우는데 stale read 랑 read-your-writes primer, read model cutover guardrails 를 같이 비교해서 보고 싶어. 입문자는 guardrail 전에 뭐부터 이해해야 해?",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        guardrail_doc = "contents/design-pattern/read-model-cutover-guardrails.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assert_path_rank_at_most(hits, guardrail_doc, 3)
        self.assert_ranks_ahead(hits, overview_doc, guardrail_doc)
        self.assertTrue(all(hit["category"] == "design-pattern" for hit in hits[:3]), hits[:3])

    def test_introductory_projection_rollback_window_query_keeps_transaction_isolation_noise_out_of_top3(
        self,
    ) -> None:
        hits = self._search(
            "read model freshness 를 처음 배우는데 rollback window 때문에 stale read 랑 read-your-writes 큰 그림이 더 헷갈려",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        guardrail_doc = "contents/design-pattern/read-model-cutover-guardrails.md"
        tx_doc = "contents/database/transaction-isolation-locking.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assert_path_rank_at_most(hits, guardrail_doc, 3)
        self.assertNotIn(tx_doc, [hit["path"] for hit in hits[:3]])
        self.assertTrue(all(hit["category"] == "design-pattern" for hit in hits[:3]), hits[:3])

    def test_introductory_projection_rollback_window_vs_transaction_rollback_query_keeps_primer_first(
        self,
    ) -> None:
        hits = self._search(
            "read model freshness 를 처음 배우는데 rollback window 랑 transaction rollback 차이를 같이 비교해서 보고 싶어. stale read 랑 read-your-writes 큰 그림부터 설명해줘",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        tx_doc = "contents/database/transaction-isolation-locking.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assert_path_rank_at_most(hits, tx_doc, 5)
        self.assert_ranks_ahead(hits, overview_doc, tx_doc)

    def test_introductory_projection_rollback_window_vs_korean_transaction_rollback_query_keeps_primer_first(
        self,
    ) -> None:
        hits = self._search(
            "read model freshness 를 처음 배우는데 rollback window 랑 트랜잭션 롤백 차이를 같이 비교해서 보고 싶어. stale read 랑 read-your-writes 큰 그림부터 설명해줘",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        tx_doc = "contents/database/transaction-isolation-locking.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assert_path_rank_at_most(hits, tx_doc, 5)
        self.assert_ranks_ahead(hits, overview_doc, tx_doc)

    def test_introductory_projection_rollback_contrast_synonym_queries_keep_primer_first(
        self,
    ) -> None:
        prompts = {
            "구분": (
                "read model freshness 를 처음 배우는데 rollback window 랑 transaction rollback 을 "
                "어떻게 구분해야 해? stale read 랑 read-your-writes 큰 그림부터 설명해줘"
            ),
            "헷갈림": (
                "read model freshness 를 처음 배우는데 rollback window 랑 transaction rollback "
                "헷갈림이 있어. stale read 랑 read-your-writes 큰 그림부터 설명해줘"
            ),
            "vs": (
                "read model freshness 를 처음 배우는데 rollback window vs transaction rollback 이 "
                "뭐가 다른지 모르겠어. stale read 랑 read-your-writes 큰 그림부터 설명해줘"
            ),
        }

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        tx_doc = "contents/database/transaction-isolation-locking.md"

        for cue, prompt in prompts.items():
            with self.subTest(cue=cue):
                hits = self._search(prompt, top_k=5)

                self.assert_path_rank_at_most(hits, overview_doc, 1)
                self.assert_path_rank_at_most(hits, tx_doc, 5)
                self.assert_ranks_ahead(hits, overview_doc, tx_doc)

    def test_korean_projection_freshness_synonym_query_keeps_primer_first(self) -> None:
        prompts = {
            "old_value_visible": (
                "CQRS 읽기 모델을 처음 배우는데 롤백 윈도우 때문에 예전 값이 보임. "
                "쓴 직후 읽기 보장이 왜 깨지는지 큰 그림부터 설명해줘"
            ),
            "saved_not_visible": (
                "읽기 모델을 처음 배우는데 방금 저장했는데 안 보여. "
                "왜 옛값이 보여? 큰 그림부터 설명해줘"
            ),
            "saved_value_not_visible": (
                "CQRS를 처음 배우는데 저장한 값이 안 보이고 옛값이 보여. "
                "쓴 직후 읽기 보장이 왜 깨지는지 큰 그림부터 설명해줘"
            ),
            "minimal_saved_not_visible": "방금 저장했는데 안 보여",
            "minimal_old_value_visible": "옛값이 보여",
        }

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        tx_doc = "contents/database/transaction-isolation-locking.md"

        for cue, prompt in prompts.items():
            with self.subTest(cue=cue):
                hits = self._search(prompt, top_k=5)

                self.assert_path_rank_at_most(hits, overview_doc, 1)
                self.assertNotIn(tx_doc, [hit["path"] for hit in hits[:3]])
                self.assertTrue(
                    all(hit["category"] == "design-pattern" for hit in hits[:3]),
                    hits[:3],
                )

    def test_introductory_projection_cutover_safety_window_keeps_failover_noise_out_of_top3(
        self,
    ) -> None:
        hits = self._search(
            "read model freshness 를 처음 배우는데 cutover safety window 동안 stale read 랑 read-your-writes 를 어떻게 이해해야 해? failover rollback 같은 운영 얘기 전에 큰 그림부터 알고 싶어",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        failover_doc = "contents/system-design/global-traffic-failover-control-plane-design.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assertNotIn(failover_doc, [hit["path"] for hit in hits[:3]])
        self.assertTrue(all(hit["category"] == "design-pattern" for hit in hits[:3]), hits[:3])

    def test_introductory_projection_cutover_safety_window_keeps_key_rotation_noise_out_of_top3(
        self,
    ) -> None:
        hits = self._search(
            "read model freshness 를 처음 배우는데 cutover safety window 와 rollback window 때문에 stale read 가 왜 생기는지 알고 싶어. key rotation rollback 같은 운영 얘기는 잠깐 빼고",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        security_docs = {
            "contents/security/jwk-rotation-cache-invalidation-kid-rollover.md",
            "contents/security/key-rotation-runbook.md",
            "contents/security/jwks-rotation-cutover-failure-recovery.md",
        }

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assertFalse(security_docs & {hit["path"] for hit in hits[:3]}, hits[:3])
        self.assertTrue(all(hit["category"] == "design-pattern" for hit in hits[:3]), hits[:3])

    def test_projection_freshness_slo_query_keeps_slo_doc_within_top3(self) -> None:
        hits = self._search(
            "projection freshness SLO, freshness SLI, lag breach policy 를 어떻게 잡아?",
            top_k=5,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/design-pattern/projection-freshness-slo-pattern.md",
            3,
        )
        self.assert_any_path_in_top_k(
            hits,
            {
                "contents/design-pattern/read-model-staleness-read-your-writes.md",
                "contents/design-pattern/projection-lag-budgeting-pattern.md",
            },
            5,
        )

    def test_projection_lag_budget_query_keeps_budget_doc_within_top3(self) -> None:
        hits = self._search(
            "projection lag budget, consumer backlog budget, freshness budget 을 어떻게 나눠?",
            top_k=5,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/design-pattern/projection-lag-budgeting-pattern.md",
            3,
        )
        self.assert_any_path_in_top_k(
            hits,
            {
                "contents/design-pattern/read-model-staleness-read-your-writes.md",
                "contents/design-pattern/projection-freshness-slo-pattern.md",
            },
            5,
        )

    def test_projection_cutover_guardrail_query_keeps_guardrail_doc_within_top3(self) -> None:
        hits = self._search(
            "read model cutover guardrails, dual read parity, rollback window, freshness guardrail 을 같이 보고 싶어",
            top_k=5,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/design-pattern/read-model-cutover-guardrails.md",
            3,
        )
        self.assert_any_path_in_top_k(
            hits,
            {
                "contents/design-pattern/projection-freshness-slo-pattern.md",
                "contents/design-pattern/projection-rebuild-backfill-cutover-pattern.md",
            },
            5,
        )

    def test_projection_canary_query_keeps_guardrail_doc_within_top3(self) -> None:
        hits = self._search(
            "projection canary, dual read parity, rollback window 를 같이 보고 싶어",
            top_k=5,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/design-pattern/read-model-cutover-guardrails.md",
            3,
        )
        self.assert_any_path_in_top_k(
            hits,
            {
                "contents/design-pattern/projection-freshness-slo-pattern.md",
                "contents/design-pattern/projection-rebuild-backfill-cutover-pattern.md",
            },
            5,
        )

    def test_global_failover_query_keeps_failover_doc_within_top3(self) -> None:
        hits = self._search(
            "regional evacuation 이랑 weighted region routing 을 하는 global traffic failover control plane 을 어떻게 설계해?",
            top_k=5,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/system-design/global-traffic-failover-control-plane-design.md",
            3,
        )
        self.assertIn(
            "contents/system-design/traffic-shadowing-progressive-cutover-design.md",
            [hit["path"] for hit in hits[:5]],
        )

    def test_stateful_failover_query_keeps_stateful_doc_within_top3(self) -> None:
        hits = self._search(
            "stateful workload placement failover control plane 에서 evacuation 과 placement budget 을 어떻게 잡아?",
            top_k=5,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/system-design/stateful-workload-placement-failover-control-plane-design.md",
            3,
        )
        self.assertIn(
            "contents/system-design/global-traffic-failover-control-plane-design.md",
            [hit["path"] for hit in hits[:5]],
        )

    def test_failover_visibility_query_keeps_visibility_doc_within_top3(self) -> None:
        hits = self._search(
            "failover visibility window 동안 stale primary 와 topology cache divergence 를 어떻게 줄이지?",
            top_k=5,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/database/failover-visibility-window-topology-cache-playbook.md",
            3,
        )
        self.assertIn(
            "contents/database/failover-promotion-read-divergence.md",
            [hit["path"] for hit in hits[:5]],
        )

    def test_failover_visibility_post_promotion_query_keeps_visibility_doc_within_top3(self) -> None:
        hits = self._search(
            "post-promotion stale reads 와 topology cache invalidation visibility window 를 알고 싶어",
            top_k=5,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/database/failover-visibility-window-topology-cache-playbook.md",
            3,
        )
        self.assertIn(
            "contents/database/failover-promotion-read-divergence.md",
            [hit["path"] for hit in hits[:5]],
        )

    def test_failover_commit_horizon_query_keeps_verification_doc_within_top3(self) -> None:
        hits = self._search(
            "commit horizon after failover verification 을 어떻게 해야 하지?",
            top_k=5,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/database/commit-horizon-after-failover-verification.md",
            3,
        )
        self.assert_any_path_in_top_k(
            hits,
            {
                "contents/database/failover-visibility-window-topology-cache-playbook.md",
                "contents/database/failover-promotion-read-divergence.md",
                "contents/system-design/global-traffic-failover-control-plane-design.md",
            },
            5,
        )

    def test_progressive_cutover_query_keeps_shadowing_doc_within_top3(self) -> None:
        hits = self._search(
            "shadow traffic mirrored requests route guardrail 로 progressive cutover 를 운영하고 싶어",
            top_k=5,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/system-design/traffic-shadowing-progressive-cutover-design.md",
            3,
        )
        self.assert_any_path_in_top_k(
            hits,
            {
                "contents/system-design/global-traffic-failover-control-plane-design.md",
                "contents/software-engineering/data-migration-rehearsal-reconciliation-cutover.md",
                "contents/design-pattern/read-model-cutover-guardrails.md",
            },
            5,
        )

    def test_strangler_verification_query_keeps_shadow_metrics_doc_within_top3(self) -> None:
        hits = self._search(
            "strangler verification, shadow traffic metrics, diffing 으로 cutover 전 검증하고 싶어",
            top_k=5,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/software-engineering/strangler-verification-shadow-traffic-metrics.md",
            3,
        )
        self.assert_any_path_in_top_k(
            hits,
            {
                "contents/system-design/traffic-shadowing-progressive-cutover-design.md",
                "contents/design-pattern/read-model-cutover-guardrails.md",
            },
            5,
        )

    def test_receiver_warmup_cutover_query_keeps_warmup_doc_within_top3(self) -> None:
        hits = self._search(
            "receiver warmup, cache prefill, write freeze 로 cutover blast radius 를 줄이고 싶어",
            top_k=5,
        )

        self.assert_path_rank_at_most(
            hits,
            "contents/system-design/receiver-warmup-cache-prefill-write-freeze-cutover-design.md",
            3,
        )
        self.assert_any_path_in_top_k(
            hits,
            {
                "contents/system-design/traffic-shadowing-progressive-cutover-design.md",
                "contents/software-engineering/data-migration-rehearsal-reconciliation-cutover.md",
            },
            5,
        )

    def test_snippet_preview_is_bounded(self) -> None:
        hits = self._search("Repository aggregate persistence", top_k=2)

        for hit in hits:
            self.assertLessEqual(len(hit["snippet_preview"]), 251)  # 250 + …
            self.assertIn("snippet_preview", hit)
            self.assertIn("category", hit)
            self.assertIn("section_title", hit)
            self.assertIn("score", hit)

    def test_cheap_mode_does_not_touch_dense_or_rerank(self) -> None:
        hits = self._search("phantom read 와 MVCC 는 왜 생기지?", top_k=2)

        self.assertTrue(hits)
        self.assert_path_rank_at_most(
            hits,
            "contents/database/transaction-isolation-locking.md",
            1,
        )

    def test_is_ready_reports_missing_for_empty_dir(self) -> None:
        with tempfile.TemporaryDirectory() as empty:
            report = indexer.is_ready(empty, self.tmp)  # corpus_root irrelevant here
            self.assertEqual(report.state, "missing")
            self.assertEqual(report.next_command, "bin/cs-index-build")

    def test_category_filter_fallback_flag_false_when_matches(self) -> None:
        # repository_boundary maps to design-pattern/database/spring, and
        # the fixture has plenty of design-pattern + database chunks — the
        # strict filter keeps enough rows so no fallback fires.
        debug: dict = {}
        hits = searcher.search(
            "repository boundary 와 aggregate persistence 경계",
            learning_points=["repository_boundary"],
            mode="cheap",
            index_root=self.tmp,
            top_k=3,
            debug=debug,
        )
        self.assertTrue(hits)
        self.assertIn("category_filter_fallback", debug)
        self.assertFalse(debug["category_filter_fallback"])

    def test_category_filter_fallback_flag_true_when_no_matches(self) -> None:
        # Force the strict filter to starve by pretending an allowed
        # category set the fixture has zero docs in. We patch
        # category_mapping.categories_for to return a made-up bucket.
        from scripts.learning.rag import category_mapping

        original = category_mapping.categories_for
        category_mapping.categories_for = lambda lp: ["nonexistent-category"]
        try:
            debug: dict = {}
            hits = searcher.search(
                "repository boundary 와 aggregate persistence 경계",
                learning_points=["__forced_fallback__"],
                mode="cheap",
                index_root=self.tmp,
                top_k=3,
                debug=debug,
            )
        finally:
            category_mapping.categories_for = original
        self.assertTrue(hits, "fallback pool should still produce hits")
        self.assertTrue(debug.get("category_filter_fallback"))
        self.assertEqual(debug.get("allowed_categories"), ["nonexistent-category"])


if __name__ == "__main__":
    unittest.main()
