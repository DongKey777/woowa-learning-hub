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

GOLDEN_FIXTURE_PATH = Path(__file__).resolve().parents[1] / "fixtures" / "cs_rag_golden_queries.json"


def _load_golden_fixture_payload() -> dict:
    with GOLDEN_FIXTURE_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def _load_golden_fixture_query(query_id: str) -> dict:
    payload = _load_golden_fixture_payload()
    for query in payload.get("queries", []):
        if query.get("id") == query_id:
            return query
    raise KeyError(f"unknown CS RAG golden query fixture: {query_id}")


def _load_stable_full_mode_fixture_contract() -> dict[str, object]:
    payload = _load_golden_fixture_payload()
    return payload.get("_meta", {}).get("stable_full_mode_fixture_queries", {})


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
        "c1",
        "contents/database/read-committed-vs-repeatable-read-anomalies.md",
        "Read Committed와 Repeatable Read의 이상 현상 비교",
        "database",
        "Beginner anomaly overview",
        (
            "read committed, repeatable read, phantom read, non-repeatable read 같은 이상 현상을 "
            "입문자 큰 그림으로 먼저 비교하고 optimistic lock 전에 anomaly vocabulary 를 맞춘다."
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
        "e1",
        "contents/network/keepalive-connection-reuse-basics.md",
        "Keep-Alive and Connection Reuse Basics",
        "network",
        "HTTP connection reuse beginner primer",
        (
            "keep-alive connection reuse basics 문서는 persistent connection, idle timeout, "
            "TCP 연결 재사용, keep-alive 큰 그림을 입문자 관점으로 설명한다."
        ),
    ),
    _chunk(
        "e2",
        "contents/network/http2-http3-connection-reuse-coalescing.md",
        "HTTP/2, HTTP/3 Connection Reuse and Coalescing",
        "network",
        "Cross-origin reuse deep dive",
        (
            "http2 http3 connection reuse coalescing 문서는 authority coalescing, origin frame, "
            "alt-svc, 421 retry, connection pooling policy 같은 운영 심화 주제를 다룬다."
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
        "f4",
        "contents/database/connection-pool-basics.md",
        "Connection Pool Basics",
        "database",
        "Why connection pools exist",
        (
            "connection pool basics 는 db connection reuse, hikari cp, connection timeout, "
            "pool exhaustion 을 처음 배우는 백엔드 학습자 기준으로 설명한다."
        ),
    ),
    _chunk(
        "f5",
        "contents/database/transaction-locking-connection-pool-primer.md",
        "Transaction Locking and Connection Pool Primer",
        "database",
        "Operational lock/pool interplay",
        (
            "transaction locking connection pool primer 는 long transaction, lock wait timeout, "
            "pool starvation, retry storm, connection leak triage 같은 운영 문제를 다룬다."
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
        "g1",
        "contents/security/authentication-authorization-session-foundations.md",
        "Authentication, Authorization, and Session Foundations",
        "security",
        "Authentication and authorization foundations",
        (
            "authentication authorization session foundations 문서는 로그인 흐름, "
            "authentication, authorization, session vs jwt, stateful session 과 "
            "stateless token 차이를 백엔드 입문자 기준으로 설명한다."
        ),
    ),
    _chunk(
        "g1a",
        "contents/security/session-cookie-jwt-basics.md",
        "세션·쿠키·JWT 기초",
        "security",
        "Session cookie JWT basics",
        (
            "session cookie jwt basics 문서는 cookie session jwt browser flow, http "
            "stateless login state, jsessionid, server session vs jwt, login state "
            "persistence, why login stays, stay signed in, browser remembers my login, "
            "keep me signed in, and token based authentication 를 입문자 기준으로 "
            "설명한다."
        ),
    ),
    _chunk(
        "g1b",
        "contents/network/http-state-session-cache.md",
        "HTTP State Session Cache",
        "network",
        "HTTP stateless basics",
        (
            "http state session cache 문서는 http stateless request response, cookie, "
            "session, cache, browser cache, server cache, and why http itself does not "
            "remember prior requests 를 설명한다."
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
        "i1",
        "contents/spring/spring-transactional-basics.md",
        "Spring Transactional Basics",
        "spring",
        "Transactional beginner primer",
        (
            "spring transactional basics 문서는 transactional annotation basics, spring proxy "
            "transaction, rollback 기본 규칙을 입문자 큰 그림으로 설명한다."
        ),
    ),
    _chunk(
        "i2",
        "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md",
        "Spring Request Pipeline and Bean Container Foundations",
        "spring",
        "DispatcherServlet beginner primer",
        (
            "dispatcher servlet beginner primer 는 요청 흐름, bean container foundation, "
            "controller service repository roles 를 처음 배우는 학습자 관점으로 설명한다."
        ),
    ),
    _chunk(
        "i2a",
        "contents/spring/spring-mvc-controller-basics.md",
        "Spring MVC Controller Basics",
        "spring",
        "Controller mapping deep dive",
        (
            "spring mvc controller basics 는 handler mapping, argument resolver, response body, "
            "exception resolver, view resolver 를 중심으로 controller 계층을 자세히 설명한다."
        ),
    ),
    _chunk(
        "i3",
        "contents/spring/spring-ioc-di-basics.md",
        "Spring IoC and DI Basics",
        "spring",
        "IoC/DI beginner comparison",
        (
            "spring ioc di basics 문서는 inversion of control, dependency injection, 객체 생성 "
            "책임 위임을 비교하며 DI vs IoC 차이를 입문자 기준으로 정리한다."
        ),
    ),
    _chunk(
        "i4",
        "contents/spring/spring-transaction-propagation-deep-dive.md",
        "Spring Transaction Propagation Deep Dive",
        "spring",
        "Propagation and nested boundary",
        (
            "transaction propagation deep dive 문서는 required requires_new nested propagation, "
            "self invocation trap, remote call boundary 를 운영 관점으로 분석한다."
        ),
    ),
    _chunk(
        "i5",
        "contents/spring/spring-bean-definition-overriding-semantics.md",
        "Spring Bean Definition Overriding Semantics",
        "spring",
        "Bean resolution deep dive",
        (
            "bean definition overriding semantics 문서는 bean override collision, @Primary, "
            "@Qualifier, conditional bean activation 충돌 사례를 심화로 다룬다."
        ),
    ),
    _chunk(
        "i6",
        "contents/spring/spring-rollbackonly-vs-checked-exception-commit-surprise-card.md",
        "Spring RollbackOnly vs Checked Exception Commit Surprise Card",
        "spring",
        "Operational incident primer",
        (
            "rollback incident primer operational triage card 는 rollbackOnly, "
            "unexpectedRollbackException, checked exception commit surprise, transaction "
            "rollback, isolation, commit failure 를 한 카드에 묶어 운영 사고처럼 소개한다."
        ),
    ),
    _chunk(
        "i7",
        "contents/spring/spring-unexpectedrollbackexception-mini-debugging-card.md",
        "Spring UnexpectedRollbackException Mini Debugging Card",
        "spring",
        "Rollback debugging card",
        (
            "unexpectedRollbackException mini debugging card 는 rollback incident, debugging, "
            "triage, operational card, rollback-only 표시, transaction rollback, isolation, "
            "commit failure 를 빠르게 훑는 Spring 운영 문서다."
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
            "한 줄 모델: write model 은 먼저 성공하고 read model 은 projection lag 만큼 "
            "뒤따라온다. 그래서 저장 직후 조회에서는 방금 쓴 값 대신 예전 데이터나 예전 목록이 "
            "잠깐 보일 수 있다.\n\n"
            "CQRS read model staleness, read model freshness, projection lag, read-your-writes, "
            "freshness budget, eventual consistency UX 계약을 다루는 입문 primer 다.\n\n"
            "입문 체크포인트: 저장 직후 목록 최신화가 안 됨, 저장했는데 목록이 그대로, 수정했는데 "
            "화면엔 예전 목록이 보여, 저장한 뒤 화면 반영이 늦음, 저장 직후 조회하면 예전 데이터가 "
            "보임, 저장은 됐는데 조회가 달라, 수정했는데 목록은 그대로야.\n\n"
            "자주 헷갈리는 비교: rollback window 와 transaction rollback 차이, rollback "
            "window vs transaction rollback 구분, 롤백 윈도우와 트랜잭션 롤백 헷갈림.\n\n"
            "관련 문서: Read Model Cutover Guardrails, Projection Freshness SLO Pattern\n\n"
            "retrieval-anchor-keywords: 읽기 모델 최신성, 읽기 모델 지연, 읽기 모델 반영 지연, "
            "read model freshness, 방금 저장했는데 안 보여, 저장 직후 조회, 저장 직후 목록 "
            "최신화가 안 됨, 저장했는데 목록이 그대로, 수정했는데 화면엔 예전 목록이 보여, "
            "저장한 뒤 화면 반영이 늦음, 저장했는데 옛값이 보임, 예전 값이 보임, 예전 데이터가 "
            "보임, 저장은 됐는데 조회가 달라, 수정했는데 목록은 그대로야, rollback window, "
            "transaction rollback, 롤백 윈도우, 트랜잭션 롤백, "
            "차이, 구분, 헷갈림, 쓴 직후 읽기 보장, 방금 쓴 값 읽기, 오래된 값 조회"
        ),
    ),
    _chunk(
        "l1",
        "contents/design-pattern/session-pinning-vs-version-gated-strict-reads.md",
        "Session Pinning vs Version-Gated Strict Reads",
        "design-pattern",
        "Strict-read routing mental model",
        (
            "session pinning vs version gated strict reads primer 는 session pinning strict read "
            "와 expected version strict read, watermark gated strict read 차이가 뭐야 같은 "
            "입문 질문에 답한다. actor scoped pinning, cross screen read your writes, strict "
            "screen routing window 를 큰 그림으로 먼저 비교하고 cutover guardrails 나 "
            "fallback contract 같은 운영 playbook 전에 읽는 bridge 문서다."
        ),
    ),
    _chunk(
        "l2",
        "contents/design-pattern/strict-read-fallback-contracts.md",
        "Strict Read Fallback Contracts",
        "design-pattern",
        "Fallback ownership and routing",
        (
            "strict read fallback contracts 문서는 strict screen fallback, fallback ownership, "
            "fallback routing, fallback rate contract, watermark gated fallback, version gated "
            "fallback, write model fallback, cutover fallback 같은 운영 playbook 주제를 다룬다."
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
            "read cutover, cutover guardrail 을 연결한다. beginner cqrs survey routing 에서만 "
            "read model freshness 와 projection overview 를 짧게 연결한다."
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

    def test_beginner_transaction_anomaly_primer_query_prefers_anomaly_doc_over_locking_primer(
        self,
    ) -> None:
        hits = self._search(
            "트랜잭션 격리 수준이랑 locking 을 처음 배우는데 optimistic/pessimistic lock 전에 "
            "read committed, repeatable read, phantom read 같은 이상 현상 큰 그림부터 설명해줘",
            top_k=4,
        )

        anomaly_doc = "contents/database/read-committed-vs-repeatable-read-anomalies.md"
        locking_primer = "contents/database/transaction-isolation-locking.md"
        self.assert_path_rank_at_most(hits, anomaly_doc, 1)
        self.assert_ranks_ahead(hits, anomaly_doc, locking_primer)
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

    def test_database_focused_transaction_rollback_query_prefers_transaction_primer_over_projection_primer(
        self,
    ) -> None:
        hits = self._search(
            "트랜잭션 롤백이 왜 필요한지와 isolation level 에서 dirty read, phantom read 를 어떻게 막는지 설명해줘",
            top_k=5,
        )

        tx_doc = "contents/database/transaction-isolation-locking.md"
        projection_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"

        self.assert_path_rank_at_most(hits, tx_doc, 1)
        if projection_doc in [hit["path"] for hit in hits]:
            self.assert_ranks_ahead(hits, tx_doc, projection_doc)
        else:
            self.assertNotIn(projection_doc, [hit["path"] for hit in hits[:3]])

    def test_transaction_rollback_incident_primer_query_stays_in_database_family(self) -> None:
        hits = self._search(
            "transaction rollback incident primer 를 beginner 관점에서 설명해줘",
            learning_points=["transaction_consistency"],
            top_k=5,
        )

        tx_doc = "contents/database/transaction-isolation-locking.md"

        self.assert_path_rank_at_most(hits, tx_doc, 1)
        self.assertTrue(all(hit["category"] == "database" for hit in hits[:3]), hits[:3])

    def test_empty_learning_points_matches_none_for_beginner_transaction_primer_query(self) -> None:
        prompt = (
            "트랜잭션 격리 수준이랑 locking 을 처음 배우는데 optimistic pessimistic lock 전에 "
            "read committed repeatable read phantom read 큰 그림부터 설명해줘"
        )

        none_hits = self._search(prompt, learning_points=None, top_k=5)
        empty_hits = self._search(prompt, learning_points=[], top_k=5)

        anomaly_doc = "contents/database/read-committed-vs-repeatable-read-anomalies.md"
        tx_doc = "contents/database/transaction-isolation-locking.md"

        self.assertEqual(
            [hit["path"] for hit in empty_hits[:3]],
            [hit["path"] for hit in none_hits[:3]],
        )
        self.assertEqual(
            [hit["category"] for hit in empty_hits[:3]],
            [hit["category"] for hit in none_hits[:3]],
        )
        self.assert_path_rank_at_most(empty_hits, anomaly_doc, 1)
        self.assert_path_rank_at_most(empty_hits, tx_doc, 2)
        self.assertTrue(all(hit["category"] == "database" for hit in empty_hits[:3]), empty_hits[:3])

    def test_commit_failure_rollback_incident_primer_keeps_spring_operational_cards_out_of_top3(
        self,
    ) -> None:
        hits = self._search(
            "commit failure rollback incident primer 를 beginner 관점에서 설명해줘",
            learning_points=["transaction_consistency"],
            top_k=5,
        )

        tx_doc = "contents/database/transaction-isolation-locking.md"
        spring_doc = (
            "contents/spring/spring-rollbackonly-vs-checked-exception-commit-surprise-card.md"
        )

        self.assert_path_rank_at_most(hits, tx_doc, 1)
        self.assertNotIn(spring_doc, [hit["path"] for hit in hits[:3]])
        self.assertTrue(all(hit["category"] == "database" for hit in hits[:4]), hits[:4])

    def test_transaction_anomaly_incident_primer_query_keeps_spring_operational_cards_out_of_top3(
        self,
    ) -> None:
        hits = self._search(
            "dirty read phantom read rollback incident primer 를 beginner 큰 그림으로 설명해줘",
            learning_points=["transaction_consistency"],
            top_k=5,
        )

        anomaly_doc = "contents/database/read-committed-vs-repeatable-read-anomalies.md"
        tx_doc = "contents/database/transaction-isolation-locking.md"
        deadlock_doc = "contents/database/deadlock-case-study.md"

        self.assert_path_rank_at_most(hits, anomaly_doc, 2)
        self.assert_path_rank_at_most(hits, tx_doc, 2)
        self.assertNotIn(deadlock_doc, [hit["path"] for hit in hits[:3]])
        self.assertTrue(all(hit["category"] == "database" for hit in hits[:3]), hits[:3])

    def test_dirty_read_incident_primer_query_stays_on_database_anomaly_primers(
        self,
    ) -> None:
        hits = self._search(
            "dirty read incident primer 를 beginner 관점에서 설명해줘",
            learning_points=["transaction_consistency"],
            top_k=5,
        )

        anomaly_doc = "contents/database/read-committed-vs-repeatable-read-anomalies.md"
        spring_doc = "contents/spring/spring-transactional-basics.md"

        self.assert_path_rank_at_most(hits, anomaly_doc, 2)
        spring_ranked_paths = [hit["path"] for hit in hits]
        if spring_doc in spring_ranked_paths:
            self.assert_ranks_ahead(hits, anomaly_doc, spring_doc)
        self.assertTrue(all(hit["category"] == "database" for hit in hits[:4]), hits[:4])

    def test_phantom_read_isolation_incident_primer_query_keeps_database_family_ahead_of_spring(
        self,
    ) -> None:
        hits = self._search(
            "phantom read isolation incident primer 를 beginner 관점에서 설명해줘",
            learning_points=["transaction_consistency"],
            top_k=5,
        )

        tx_doc = "contents/database/transaction-isolation-locking.md"
        anomaly_doc = "contents/database/read-committed-vs-repeatable-read-anomalies.md"
        spring_doc = "contents/spring/spring-transactional-basics.md"

        self.assert_path_rank_at_most(hits, tx_doc, 1)
        self.assert_path_rank_at_most(hits, anomaly_doc, 2)
        self.assertNotIn(spring_doc, [hit["path"] for hit in hits[:3]])
        self.assertTrue(all(hit["category"] == "database" for hit in hits[:3]), hits[:3])

    def test_mixed_rollback_window_and_korean_transaction_rollback_without_primer_cue_keeps_db_docs_ahead_of_projection_primer(
        self,
    ) -> None:
        hits = self._search(
            "rollback window 랑 트랜잭션 롤백 차이가 뭐야",
            top_k=5,
        )

        tx_doc = "contents/database/transaction-isolation-locking.md"
        decision_doc = "contents/database/transaction-boundary-isolation-locking-decision-framework.md"
        projection_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"

        self.assert_path_rank_at_most(hits, tx_doc, 2)
        self.assert_path_rank_at_most(hits, decision_doc, 2)
        self.assert_ranks_ahead(hits, tx_doc, projection_doc)
        self.assert_ranks_ahead(hits, decision_doc, projection_doc)

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

    def test_dispatcherservlet_shortform_query_prefers_beginner_request_pipeline_primer(self) -> None:
        hits = self._search(
            "DispatcherServlet 이 뭐야?",
            top_k=4,
        )

        primer_doc = "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md"
        deep_dive_doc = "contents/spring/spring-mvc-controller-basics.md"
        self.assert_path_rank_at_most(hits, primer_doc, 1)
        self.assert_ranks_ahead(hits, primer_doc, deep_dive_doc)

    def test_dispatcher_servlet_spacing_variant_prefers_beginner_request_pipeline_primer(self) -> None:
        hits = self._search(
            "Dispatcher Servlet 이 뭐야?",
            top_k=4,
        )

        primer_doc = "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md"
        deep_dive_doc = "contents/spring/spring-mvc-controller-basics.md"
        self.assert_path_rank_at_most(hits, primer_doc, 1)
        self.assert_ranks_ahead(hits, primer_doc, deep_dive_doc)

    def test_dispatcher_servlet_lowercase_variant_prefers_beginner_request_pipeline_primer(
        self,
    ) -> None:
        hits = self._search(
            "dispatcher servlet 이 뭐야?",
            top_k=4,
        )

        primer_doc = "contents/spring/spring-request-pipeline-bean-container-foundations-primer.md"
        deep_dive_doc = "contents/spring/spring-mvc-controller-basics.md"
        self.assert_path_rank_at_most(hits, primer_doc, 1)
        self.assert_ranks_ahead(hits, primer_doc, deep_dive_doc)

    def test_keepalive_shortform_query_prefers_connection_reuse_primer_over_coalescing_deep_dive(
        self,
    ) -> None:
        hits = self._search(
            "HTTP keep-alive 뭐야?",
            top_k=4,
        )

        primer_doc = "contents/network/keepalive-connection-reuse-basics.md"
        deep_dive_doc = "contents/network/http2-http3-connection-reuse-coalescing.md"
        self.assert_path_rank_at_most(hits, primer_doc, 1)
        self.assert_ranks_ahead(hits, primer_doc, deep_dive_doc)

    def test_keep_alive_spacing_shortform_query_prefers_connection_reuse_primer_over_coalescing_deep_dive(
        self,
    ) -> None:
        hits = self._search(
            "HTTP keep alive 뭐야?",
            top_k=4,
        )

        primer_doc = "contents/network/keepalive-connection-reuse-basics.md"
        deep_dive_doc = "contents/network/http2-http3-connection-reuse-coalescing.md"
        self.assert_path_rank_at_most(hits, primer_doc, 1)
        self.assert_ranks_ahead(hits, primer_doc, deep_dive_doc)

    def test_connection_pool_shortform_query_prefers_pool_basics_over_locking_operational_doc(
        self,
    ) -> None:
        hits = self._search(
            "connection pool 이 뭐야?",
            top_k=4,
        )

        primer_doc = "contents/database/connection-pool-basics.md"
        deep_dive_doc = "contents/database/transaction-locking-connection-pool-primer.md"
        self.assert_path_rank_at_most(hits, primer_doc, 1)
        self.assert_ranks_ahead(hits, primer_doc, deep_dive_doc)

    def test_connection_pooling_shortform_query_prefers_pool_basics_over_locking_operational_doc(
        self,
    ) -> None:
        hits = self._search(
            "connection pooling 이 뭐야?",
            top_k=4,
        )

        primer_doc = "contents/database/connection-pool-basics.md"
        deep_dive_doc = "contents/database/transaction-locking-connection-pool-primer.md"
        self.assert_path_rank_at_most(hits, primer_doc, 1)
        self.assert_ranks_ahead(hits, primer_doc, deep_dive_doc)

    def test_transactional_shortform_query_prefers_transactional_basics_over_propagation_deep_dive(
        self,
    ) -> None:
        hits = self._search(
            "@Transactional 이 뭐야?",
            top_k=4,
        )

        primer_doc = "contents/spring/spring-transactional-basics.md"
        deep_dive_doc = "contents/spring/spring-transaction-propagation-deep-dive.md"
        self.assert_path_rank_at_most(hits, primer_doc, 1)
        self.assert_ranks_ahead(hits, primer_doc, deep_dive_doc)

    def test_transactional_english_shortform_query_prefers_transactional_basics_over_propagation_deep_dive(
        self,
    ) -> None:
        hits = self._search(
            "What is @Transactional?",
            top_k=4,
        )

        primer_doc = "contents/spring/spring-transactional-basics.md"
        deep_dive_doc = "contents/spring/spring-transaction-propagation-deep-dive.md"
        self.assert_path_rank_at_most(hits, primer_doc, 1)
        self.assert_ranks_ahead(hits, primer_doc, deep_dive_doc)

    def test_transactional_english_plain_alias_query_prefers_transactional_basics_over_propagation_deep_dive(
        self,
    ) -> None:
        hits = self._search(
            "What is transactional in Spring?",
            top_k=4,
        )

        primer_doc = "contents/spring/spring-transactional-basics.md"
        deep_dive_doc = "contents/spring/spring-transaction-propagation-deep-dive.md"
        self.assert_path_rank_at_most(hits, primer_doc, 1)
        self.assert_ranks_ahead(hits, primer_doc, deep_dive_doc)

    def test_transactional_english_plain_alias_meaning_query_prefers_transactional_basics_over_propagation_deep_dive(
        self,
    ) -> None:
        hits = self._search(
            "What does transactional mean in Spring?",
            top_k=4,
        )

        primer_doc = "contents/spring/spring-transactional-basics.md"
        deep_dive_doc = "contents/spring/spring-transaction-propagation-deep-dive.md"
        self.assert_path_rank_at_most(hits, primer_doc, 1)
        self.assert_ranks_ahead(hits, primer_doc, deep_dive_doc)

    def test_transactional_english_short_alias_without_question_words_prefers_transactional_basics_over_propagation_deep_dive(
        self,
    ) -> None:
        hits = self._search(
            "transactional in spring",
            top_k=4,
        )

        primer_doc = "contents/spring/spring-transactional-basics.md"
        deep_dive_doc = "contents/spring/spring-transaction-propagation-deep-dive.md"
        self.assert_path_rank_at_most(hits, primer_doc, 1)
        self.assert_ranks_ahead(hits, primer_doc, deep_dive_doc)

    def test_transactional_english_token_pair_alias_prefers_transactional_basics_over_propagation_deep_dive(
        self,
    ) -> None:
        hits = self._search(
            "spring transactional",
            top_k=4,
        )

        primer_doc = "contents/spring/spring-transactional-basics.md"
        deep_dive_doc = "contents/spring/spring-transaction-propagation-deep-dive.md"
        self.assert_path_rank_at_most(hits, primer_doc, 1)
        self.assert_ranks_ahead(hits, primer_doc, deep_dive_doc)

    def test_transactional_english_why_use_query_prefers_transactional_basics_over_propagation_deep_dive(
        self,
    ) -> None:
        hits = self._search(
            "Why use @Transactional?",
            top_k=4,
        )

        primer_doc = "contents/spring/spring-transactional-basics.md"
        deep_dive_doc = "contents/spring/spring-transaction-propagation-deep-dive.md"
        self.assert_path_rank_at_most(hits, primer_doc, 1)
        self.assert_ranks_ahead(hits, primer_doc, deep_dive_doc)

    def test_transactional_english_propagation_query_prefers_propagation_deep_dive_over_primer(
        self,
    ) -> None:
        hits = self._search(
            "What does propagation mean in @Transactional?",
            top_k=4,
        )

        deep_dive_doc = "contents/spring/spring-transaction-propagation-deep-dive.md"
        primer_doc = "contents/spring/spring-transactional-basics.md"
        self.assert_path_rank_at_most(hits, deep_dive_doc, 1)
        self.assert_ranks_ahead(hits, deep_dive_doc, primer_doc)

    def test_di_vs_ioc_shortform_query_prefers_ioc_di_basics_over_bean_override_semantics(
        self,
    ) -> None:
        hits = self._search(
            "DI vs IoC 차이가 뭐야?",
            top_k=4,
        )

        primer_doc = "contents/spring/spring-ioc-di-basics.md"
        deep_dive_doc = "contents/spring/spring-bean-definition-overriding-semantics.md"
        self.assert_path_rank_at_most(hits, primer_doc, 1)
        self.assert_ranks_ahead(hits, primer_doc, deep_dive_doc)

    def test_di_and_ioc_shortform_query_prefers_ioc_di_basics_over_bean_override_semantics(
        self,
    ) -> None:
        hits = self._search(
            "DI와 IoC 차이가 뭐야?",
            top_k=4,
        )

        primer_doc = "contents/spring/spring-ioc-di-basics.md"
        deep_dive_doc = "contents/spring/spring-bean-definition-overriding-semantics.md"
        self.assert_path_rank_at_most(hits, primer_doc, 1)
        self.assert_ranks_ahead(hits, primer_doc, deep_dive_doc)

    def test_session_vs_jwt_shortform_query_prefers_session_cookie_jwt_primer_over_auth_foundation_and_jwt_deep_dive(
        self,
    ) -> None:
        hits = self._search(
            "세션이랑 JWT 차이가 뭐야?",
            top_k=4,
        )

        primer_doc = "contents/security/session-cookie-jwt-basics.md"
        auth_foundation_doc = "contents/security/authentication-authorization-session-foundations.md"
        deep_dive_doc = "contents/security/jwt-deep-dive.md"
        self.assert_path_rank_at_most(hits, primer_doc, 1)
        self.assert_ranks_ahead(hits, primer_doc, auth_foundation_doc)
        self.assert_ranks_ahead(hits, primer_doc, deep_dive_doc)
        http_state_doc = "contents/network/http-state-session-cache.md"
        if http_state_doc in [hit["path"] for hit in hits]:
            self.assert_ranks_ahead(hits, primer_doc, http_state_doc)

    def test_session_vs_jwt_english_shortform_query_prefers_session_cookie_jwt_primer_over_auth_foundation_and_jwt_deep_dive(
        self,
    ) -> None:
        hits = self._search(
            "session vs JWT what is the difference?",
            top_k=4,
        )

        primer_doc = "contents/security/session-cookie-jwt-basics.md"
        auth_foundation_doc = "contents/security/authentication-authorization-session-foundations.md"
        deep_dive_doc = "contents/security/jwt-deep-dive.md"
        self.assert_path_rank_at_most(hits, primer_doc, 1)
        self.assert_ranks_ahead(hits, primer_doc, auth_foundation_doc)
        self.assert_ranks_ahead(hits, primer_doc, deep_dive_doc)
        http_state_doc = "contents/network/http-state-session-cache.md"
        if http_state_doc in [hit["path"] for hit in hits]:
            self.assert_ranks_ahead(hits, primer_doc, http_state_doc)

    def test_cookie_login_state_colloquial_queries_prefer_session_cookie_jwt_primer_over_auth_foundation_and_jwt_deep_dive(
        self,
    ) -> None:
        prompts = (
            "JWT랑 쿠키 둘 다 로그인 유지에 쓰는 거야?",
            "왜 쿠키 있으면 로그인 안 풀려?",
            "Why do cookies keep me signed in?",
            "브라우저가 로그인 기억하는 건 세션이야 JWT야?",
            "Why am I still logged in when the browser remembers my cookie?",
        )

        primer_doc = "contents/security/session-cookie-jwt-basics.md"
        auth_foundation_doc = "contents/security/authentication-authorization-session-foundations.md"
        deep_dive_doc = "contents/security/jwt-deep-dive.md"
        http_state_doc = "contents/network/http-state-session-cache.md"

        for prompt in prompts:
            with self.subTest(prompt=prompt):
                hits = self._search(
                    prompt,
                    top_k=4,
                )

                self.assert_path_rank_at_most(hits, primer_doc, 1)
                self.assert_ranks_ahead(hits, primer_doc, auth_foundation_doc)
                self.assert_ranks_ahead(hits, primer_doc, deep_dive_doc)
                if http_state_doc in [hit["path"] for hit in hits]:
                    self.assert_ranks_ahead(hits, primer_doc, http_state_doc)

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

    def test_additional_korean_read_model_symptom_queries_use_primer_doc_anchors_without_signal_expansion(
        self,
    ) -> None:
        prompts = {
            "query_old_data": "저장 직후 조회하면 예전 데이터가 보임",
            "list_not_refreshing": "저장 직후 목록 최신화가 안 됨",
            "list_still_same": "저장했는데 목록이 그대로",
            "screen_shows_old_list": "수정했는데 화면엔 예전 목록이 보여",
            "update_visible_late": "저장한 뒤 화면 반영이 늦음",
            "write_read_mismatch": "저장은 됐는데 조회가 달라",
            "updated_but_list_stale": "수정했는데 목록은 그대로야",
        }

        with mock.patch.object(
            signal_rules,
            "expand_query",
            side_effect=lambda prompt, topic_hints=None: searcher._fallback_tokens(prompt),
        ):
            for cue, prompt in prompts.items():
                with self.subTest(cue=cue):
                    hits = self._search(prompt, top_k=3)
                    self.assert_path_rank_at_most(
                        hits,
                        "contents/design-pattern/read-model-staleness-read-your-writes.md",
                        1,
                    )

    def test_generic_korean_crud_list_update_prompt_avoids_projection_staleness_primer(
        self,
    ) -> None:
        query = _load_golden_fixture_query("generic_crud_korean_list_read_but_update_fails")
        hits = self._search(query["prompt"], top_k=5)

        primer_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        candidate_paths = [query["expected_path"], *query.get("acceptable_paths", [])]
        top_paths = [hit["path"] for hit in hits[:3]]

        self.assertTrue(any(path in top_paths for path in candidate_paths), hits)
        self.assertNotIn(primer_doc, top_paths)

    def test_generic_korean_crud_api_difference_prompt_prefers_beginner_layering_docs(self) -> None:
        query = _load_golden_fixture_query("generic_crud_korean_update_vs_read_api_difference")
        hits = self._search(query["prompt"], top_k=5)

        primer_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        candidate_paths = [query["expected_path"], *query.get("acceptable_paths", [])]
        top_paths = [hit["path"] for hit in hits[:3]]

        self.assertTrue(any(path in top_paths for path in candidate_paths), hits)
        self.assertNotIn(primer_doc, top_paths)

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
            top_k=7,
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

    def test_projection_beginner_navigator_bridge_query_surfaces_neighbor_docs_before_cqrs_survey(
        self,
    ) -> None:
        hits = self._search(
            "읽기 모델 projection 을 처음 배우는데 예전 값이 왜 보이는지 개요 문서랑 주변 형제 문서를 같이 보고 싶어. CQRS 전체 survey 말고 projection 큰 그림부터 보고 싶어",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        guardrail_doc = "contents/design-pattern/read-model-cutover-guardrails.md"
        lag_budget_doc = "contents/design-pattern/projection-lag-budgeting-pattern.md"
        cqrs_survey_doc = "contents/database/schema-migration-partitioning-cdc-cqrs.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assert_path_rank_at_most(hits, guardrail_doc, 3)
        self.assert_path_rank_at_most(hits, lag_budget_doc, 4)
        top_paths = [hit["path"] for hit in hits]
        if cqrs_survey_doc in top_paths:
            self.assert_ranks_ahead(hits, guardrail_doc, cqrs_survey_doc)
            self.assert_ranks_ahead(hits, lag_budget_doc, cqrs_survey_doc)
        else:
            self.assertNotIn(cqrs_survey_doc, top_paths)

    def test_projection_beginner_staleness_overview_query_surfaces_neighbor_docs_before_cqrs_survey(
        self,
    ) -> None:
        hits = self._search(
            "읽기 모델 projection 을 처음 배우는데 stale read 때문에 예전 값이 왜 보이는지 "
            "staleness overview doc 이랑 nearby docs 를 같이 보고 싶어. CQRS 전체 "
            "overview 말고 projection 큰 그림부터 보고 싶어",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        guardrail_doc = "contents/design-pattern/read-model-cutover-guardrails.md"
        lag_budget_doc = "contents/design-pattern/projection-lag-budgeting-pattern.md"
        cqrs_survey_doc = "contents/database/schema-migration-partitioning-cdc-cqrs.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assert_path_rank_at_most(hits, guardrail_doc, 3)
        self.assert_path_rank_at_most(hits, lag_budget_doc, 4)
        top_paths = [hit["path"] for hit in hits]
        if cqrs_survey_doc in top_paths:
            self.assert_ranks_ahead(hits, guardrail_doc, cqrs_survey_doc)
            self.assert_ranks_ahead(hits, lag_budget_doc, cqrs_survey_doc)
        else:
            self.assertNotIn(cqrs_survey_doc, top_paths)

    def test_projection_beginner_overview_docs_sibling_docs_query_surfaces_neighbor_docs_before_cqrs_survey(
        self,
    ) -> None:
        hits = self._search(
            "읽기 모델 projection 을 처음 배우는데 예전 값이 왜 보이는지 overview docs 랑 "
            "nearby sibling docs 를 같이 보고 싶어. broad CQRS survey routes "
            "말고 projection 큰 그림부터 보고 싶어",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        guardrail_doc = "contents/design-pattern/read-model-cutover-guardrails.md"
        lag_budget_doc = "contents/design-pattern/projection-lag-budgeting-pattern.md"
        cqrs_survey_doc = "contents/database/schema-migration-partitioning-cdc-cqrs.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assert_path_rank_at_most(hits, guardrail_doc, 3)
        self.assert_path_rank_at_most(hits, lag_budget_doc, 4)
        top_paths = [hit["path"] for hit in hits]
        if cqrs_survey_doc in top_paths:
            self.assert_ranks_ahead(hits, guardrail_doc, cqrs_survey_doc)
            self.assert_ranks_ahead(hits, lag_budget_doc, cqrs_survey_doc)
        else:
            self.assertNotIn(cqrs_survey_doc, top_paths)

    def test_projection_beginner_entrypoint_bridge_query_surfaces_neighbor_docs_before_cqrs_survey(
        self,
    ) -> None:
        hits = self._search(
            "읽기 모델 projection 을 처음 배우는데 예전 값이 왜 보이는지 entrypoint primer "
            "랑 bridge docs, linked sibling docs 를 같이 보고 싶어. broad CQRS "
            "survey routes 말고 projection 큰 그림부터 보고 싶어",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        guardrail_doc = "contents/design-pattern/read-model-cutover-guardrails.md"
        lag_budget_doc = "contents/design-pattern/projection-lag-budgeting-pattern.md"
        cqrs_survey_doc = "contents/database/schema-migration-partitioning-cdc-cqrs.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assert_path_rank_at_most(hits, guardrail_doc, 3)
        self.assert_path_rank_at_most(hits, lag_budget_doc, 4)
        top_paths = [hit["path"] for hit in hits]
        if cqrs_survey_doc in top_paths:
            self.assert_ranks_ahead(hits, guardrail_doc, cqrs_survey_doc)
            self.assert_ranks_ahead(hits, lag_budget_doc, cqrs_survey_doc)
        else:
            self.assertNotIn(cqrs_survey_doc, top_paths)

    def test_introductory_session_pinning_vs_expected_version_query_keeps_strict_read_primer_first(
        self,
    ) -> None:
        query = _load_golden_fixture_query(
            "strict_read_intro_session_pinning_vs_expected_version"
        )
        hits = self._search(query["prompt"], top_k=5)

        primer_doc = query["expected_path"]
        fallback_doc = "contents/design-pattern/strict-read-fallback-contracts.md"
        guardrail_doc = "contents/design-pattern/read-model-cutover-guardrails.md"
        paths = [hit["path"] for hit in hits]

        self.assert_path_rank_at_most(hits, primer_doc, int(query.get("max_rank", 1)))
        self.assert_ranks_ahead(hits, primer_doc, fallback_doc)
        if guardrail_doc in paths:
            self.assert_ranks_ahead(hits, primer_doc, guardrail_doc)
        self.assertTrue(all(hit["category"] == "design-pattern" for hit in hits[:3]), hits[:3])

    def test_introductory_session_pinning_vs_watermark_gate_query_keeps_strict_read_primer_first(
        self,
    ) -> None:
        query = _load_golden_fixture_query(
            "strict_read_intro_session_pinning_vs_watermark_gate"
        )
        hits = self._search(query["prompt"], top_k=5)

        primer_doc = query["expected_path"]
        fallback_doc = "contents/design-pattern/strict-read-fallback-contracts.md"
        guardrail_doc = "contents/design-pattern/read-model-cutover-guardrails.md"
        paths = [hit["path"] for hit in hits]

        self.assert_path_rank_at_most(hits, primer_doc, int(query.get("max_rank", 1)))
        self.assert_ranks_ahead(hits, primer_doc, fallback_doc)
        if guardrail_doc in paths:
            self.assert_ranks_ahead(hits, primer_doc, guardrail_doc)
        self.assertEqual(hits[0]["category"], "design-pattern")

    def test_introductory_session_pinning_vs_version_gated_queries_keep_strict_read_primer_ahead_of_playbooks_and_auth_noise(
        self,
    ) -> None:
        fallback_doc = "contents/design-pattern/strict-read-fallback-contracts.md"
        guardrail_doc = "contents/design-pattern/read-model-cutover-guardrails.md"
        auth_doc = "contents/security/authentication-authorization-session-foundations.md"
        session_cookie_doc = "contents/security/session-cookie-jwt-basics.md"

        for query_id in (
            "strict_read_intro_session_pinning_vs_version_gated_playbook_contrast",
            "strict_read_intro_session_pinning_vs_version_gated_shortform",
        ):
            with self.subTest(query_id=query_id):
                query = _load_golden_fixture_query(query_id)
                hits = self._search(query["prompt"], top_k=5)
                paths = [hit["path"] for hit in hits]
                primer_doc = query["expected_path"]

                self.assert_path_rank_at_most(hits, primer_doc, int(query.get("max_rank", 1)))
                self.assert_ranks_ahead(hits, primer_doc, fallback_doc)
                if guardrail_doc in paths:
                    self.assert_ranks_ahead(hits, primer_doc, guardrail_doc)
                if auth_doc in paths:
                    self.assert_ranks_ahead(hits, primer_doc, auth_doc)
                if session_cookie_doc in paths:
                    self.assert_ranks_ahead(hits, primer_doc, session_cookie_doc)
                self.assertEqual(hits[0]["category"], "design-pattern")

    def test_introductory_projection_primer_vs_guardrail_compare_query_keeps_primer_first(
        self,
    ) -> None:
        hits = self._search(
            "read model freshness 를 처음 배우는데 stale read 랑 read-your-writes primer, read model cutover guardrails 를 같이 비교해서 보고 싶어. 입문자는 guardrail 전에 뭐부터 이해해야 해?",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        guardrail_doc = "contents/design-pattern/read-model-cutover-guardrails.md"
        visibility_doc = "contents/database/failover-visibility-window-topology-cache-playbook.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assert_path_rank_at_most(hits, guardrail_doc, 3)
        self.assert_ranks_ahead(hits, overview_doc, guardrail_doc)
        if visibility_doc in [hit["path"] for hit in hits]:
            self.assert_ranks_ahead(hits, guardrail_doc, visibility_doc)

    def test_introductory_projection_primer_vs_rebuild_playbook_compare_query_keeps_primer_first(
        self,
    ) -> None:
        hits = self._search(
            "read model freshness 를 처음 배우는데 stale read 랑 read-your-writes primer, projection rebuild backfill cutover playbook 를 같이 비교해서 보고 싶어. 입문자는 운영 playbook 전에 뭐부터 이해해야 해?",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        rebuild_doc = "contents/design-pattern/projection-rebuild-backfill-cutover-pattern.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        if rebuild_doc in [hit["path"] for hit in hits]:
            self.assert_ranks_ahead(hits, overview_doc, rebuild_doc)
        self.assertEqual(hits[0]["category"], "design-pattern")

    def test_introductory_projection_fully_korean_primer_vs_guardrail_compare_query_keeps_primer_first(
        self,
    ) -> None:
        hits = self._search(
            "읽기 모델 최신성을 처음 배우는데 예전 값이 보여서 헷갈려. 방금 쓴 값 읽기 보장 설명이랑 전환 안전 구간 안내를 같이 비교해서 보고 싶어. 입문자는 운영 안전 규칙 전에 어떤 기초 설명부터 봐야 해?",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        guardrail_doc = "contents/design-pattern/read-model-cutover-guardrails.md"
        visibility_doc = "contents/database/failover-visibility-window-topology-cache-playbook.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assert_path_rank_at_most(hits, guardrail_doc, 3)
        self.assert_ranks_ahead(hits, overview_doc, guardrail_doc)
        if visibility_doc in [hit["path"] for hit in hits]:
            self.assert_ranks_ahead(hits, guardrail_doc, visibility_doc)

    def test_introductory_projection_fully_korean_primer_vs_rebuild_compare_query_keeps_primer_first(
        self,
    ) -> None:
        hits = self._search(
            "읽기 모델 최신성을 처음 배우는데 저장했는데도 예전 값이 보여서 헷갈려. 방금 쓴 값 읽기 보장 설명이랑 프로젝션 재빌드 백필 컷오버 안내를 같이 비교해서 보고 싶어. 입문자는 운영 복구 문서 전에 어떤 기초 설명부터 봐야 해?",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        rebuild_doc = "contents/design-pattern/projection-rebuild-backfill-cutover-pattern.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        if rebuild_doc in [hit["path"] for hit in hits]:
            self.assert_ranks_ahead(hits, overview_doc, rebuild_doc)
        self.assertEqual(hits[0]["category"], "design-pattern")

    def test_introductory_projection_primer_vs_guardrail_and_rebuild_triad_query_keeps_primer_first(
        self,
    ) -> None:
        hits = self._search(
            "read model freshness 를 처음 배우는데 stale read 랑 read-your-writes primer, read model cutover guardrails, projection rebuild backfill cutover playbook 를 같이 비교해서 보고 싶어. 입문자는 운영 문서 전에 뭐부터 이해해야 해?",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        guardrail_doc = "contents/design-pattern/read-model-cutover-guardrails.md"
        rebuild_doc = "contents/design-pattern/projection-rebuild-backfill-cutover-pattern.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        if guardrail_doc in [hit["path"] for hit in hits]:
            self.assert_ranks_ahead(hits, overview_doc, guardrail_doc)
        if rebuild_doc in [hit["path"] for hit in hits]:
            self.assert_ranks_ahead(hits, overview_doc, rebuild_doc)
        self.assertEqual(hits[0]["category"], "design-pattern")

    def test_introductory_projection_korean_only_primer_vs_guardrail_compare_query_keeps_primer_first(
        self,
    ) -> None:
        hits = self._search(
            "읽기 모델을 처음 배우는데 예전 값이 보여서 헷갈려. 쓴 직후 읽기 보장과 전환 안전 구간 문서를 같이 비교해서 보고 싶어. 입문자는 운영 안전 규칙 전에 뭐부터 이해해야 해?",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        guardrail_doc = "contents/design-pattern/read-model-cutover-guardrails.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assert_path_rank_at_most(hits, guardrail_doc, 3)
        self.assert_ranks_ahead(hits, overview_doc, guardrail_doc)
        self.assertTrue(all(hit["category"] == "design-pattern" for hit in hits[:3]), hits[:3])

    def test_introductory_projection_korean_phrase_only_primer_vs_guardrail_compare_query_keeps_primer_first(
        self,
    ) -> None:
        hits = self._search(
            "읽기 모델을 처음 배우는데 방금 저장했는데도 예전 값이 보여서 헷갈려. 쓴 직후 읽기 보장 설명이랑 전환 안전 구간 안내를 같이 비교해서 보고 싶어. 입문자는 운영 문서 전에 어떤 기초 설명부터 봐야 해?",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        guardrail_doc = "contents/design-pattern/read-model-cutover-guardrails.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assert_path_rank_at_most(hits, guardrail_doc, 3)
        self.assert_ranks_ahead(hits, overview_doc, guardrail_doc)
        self.assertTrue(all(hit["category"] == "design-pattern" for hit in hits[:3]), hits[:3])

    def test_introductory_projection_korean_only_primer_vs_rebuild_backfill_compare_query_keeps_primer_first(
        self,
    ) -> None:
        hits = self._search(
            "읽기 모델을 처음 배우는데 저장했는데도 예전 값이 보여서 헷갈려. 쓴 직후 읽기 보장 설명이랑 프로젝션 재빌드 백필 컷오버 안내를 같이 비교해서 보고 싶어. 입문자는 운영 복구 문서 전에 어떤 기초 설명부터 봐야 해?",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        rebuild_doc = "contents/design-pattern/projection-rebuild-backfill-cutover-pattern.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        if rebuild_doc in [hit["path"] for hit in hits]:
            self.assert_ranks_ahead(hits, overview_doc, rebuild_doc)
        self.assertEqual(hits[0]["category"], "design-pattern")

    def test_introductory_projection_primer_vs_slo_lag_budget_compare_query_keeps_primer_first(
        self,
    ) -> None:
        hits = self._search(
            "read model freshness 를 처음 배우는데 stale read 랑 read-your-writes primer를 먼저 보고, projection freshness SLO 문서랑 projection lag budget 문서를 같이 비교하고 싶어. 입문자는 SLO 전에 뭐부터 이해해야 해?",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        slo_doc = "contents/design-pattern/projection-freshness-slo-pattern.md"
        lag_budget_doc = "contents/design-pattern/projection-lag-budgeting-pattern.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assert_path_rank_at_most(hits, slo_doc, 3)
        self.assert_path_rank_at_most(hits, lag_budget_doc, 3)
        self.assert_ranks_ahead(hits, overview_doc, slo_doc)
        self.assert_ranks_ahead(hits, overview_doc, lag_budget_doc)
        self.assertTrue(all(hit["category"] == "design-pattern" for hit in hits[:3]), hits[:3])

    def test_introductory_projection_fully_korean_primer_vs_slo_lag_budget_compare_query_keeps_primer_first(
        self,
    ) -> None:
        hits = self._search(
            "읽기 모델을 처음 배우는데 예전 값이 보여서 헷갈려. 예전 값이 보이는 기초 설명이랑 최신성 서비스 수준 목표, 반영 지연 허용 범위 문서를 같이 비교해서 보고 싶어. 입문자는 운영 목표 전에 뭐부터 이해해야 해?",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        slo_doc = "contents/design-pattern/projection-freshness-slo-pattern.md"
        lag_budget_doc = "contents/design-pattern/projection-lag-budgeting-pattern.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assert_path_rank_at_most(hits, slo_doc, 3)
        self.assert_path_rank_at_most(hits, lag_budget_doc, 3)
        self.assert_ranks_ahead(hits, overview_doc, slo_doc)
        self.assert_ranks_ahead(hits, overview_doc, lag_budget_doc)
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

    def test_introductory_projection_korean_rollback_window_vs_korean_transaction_rollback_query_keeps_primer_first(
        self,
    ) -> None:
        hits = self._search(
            "read model freshness 를 처음 배우는데 롤백 윈도우 랑 트랜잭션 롤백 차이를 같이 비교해서 보고 싶어. stale read 랑 read-your-writes 큰 그림부터 설명해줘",
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

    def test_introductory_projection_korean_rollback_contrast_synonym_queries_keep_primer_first(
        self,
    ) -> None:
        prompts = {
            "비교": (
                "read model freshness 를 처음 배우는데 롤백 윈도우 랑 트랜잭션 롤백 을 "
                "같이 비교해서 보고 싶어. stale read 랑 read-your-writes 큰 그림부터 설명해줘"
            ),
            "구분": (
                "read model freshness 를 처음 배우는데 롤백 윈도우 랑 트랜잭션 롤백 을 "
                "어떻게 구분해야 해? stale read 랑 read-your-writes 큰 그림부터 설명해줘"
            ),
            "헷갈림": (
                "read model freshness 를 처음 배우는데 롤백 윈도우 랑 트랜잭션 롤백 "
                "헷갈림이 있어. stale read 랑 read-your-writes 큰 그림부터 설명해줘"
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

    def test_introductory_projection_full_korean_rollback_contrast_query_keeps_primer_first(
        self,
    ) -> None:
        hits = self._search(
            "읽기 모델 최신성을 처음 배우는데 롤백 윈도우랑 트랜잭션 롤백 차이를 같이 비교해서 보고 싶어. 왜 예전 값이 보이고 방금 쓴 값 읽기가 흔들리는지 큰 그림부터 설명해줘",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        tx_doc = "contents/database/transaction-isolation-locking.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assert_path_rank_at_most(hits, tx_doc, 5)
        self.assert_ranks_ahead(hits, overview_doc, tx_doc)

    def test_introductory_projection_full_korean_rollback_distinguish_query_keeps_primer_first(
        self,
    ) -> None:
        hits = self._search(
            "읽기 모델 최신성을 처음 배우는데 롤백 윈도우랑 트랜잭션 롤백을 어떻게 구분해야 해? 왜 예전 값이 보이고 방금 쓴 값 읽기 보장이 흔들리는지 큰 그림부터 설명해줘",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        tx_doc = "contents/database/transaction-isolation-locking.md"

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

    def test_korean_projection_freshness_beginner_synonym_query_ranks_primer_ahead_of_schema_survey(
        self,
    ) -> None:
        hits = self._search(
            "CQRS 읽기 모델을 처음 배우는데 롤백 윈도우 때문에 예전 값이 보임. "
            "쓴 직후 읽기 보장이 왜 깨지는지 큰 그림부터 설명해줘",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        survey_doc = "contents/database/schema-migration-partitioning-cdc-cqrs.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assertIn(survey_doc, [hit["path"] for hit in hits])
        self.assert_ranks_ahead(hits, overview_doc, survey_doc)

    def test_symptom_only_projection_refresh_lag_queries_keep_primer_first(self) -> None:
        prompts = {
            "korean_only": (
                "저장했는데 목록 새로고침이 느리고 이전 화면 상태가 한동안 남아 있어. "
                "처음 배우는 사람 기준으로 큰 그림부터 설명해줘"
            ),
            "mixed_terms": (
                "저장 직후 list refresh lag 때문에 old screen state 가 남아 보여. "
                "운영 문서 전에 왜 이런지 기초부터 알고 싶어"
            ),
            "app_screen_delay_variant": (
                "앱에서 수정했는데 화면이 늦게 바뀌고 예전 목록이 남아 있어. 왜 이래?"
            ),
            "screen_update_delay_symptom_only": (
                "모바일에서 화면 업데이트가 늦고 목록이 한참 뒤에 바뀌어. 왜 이런 거야?"
            ),
            "screen_update_delay_jiyeon_variant": (
                "모바일에서 저장했는데 화면 업데이트 지연 때문에 예전 목록이 남아 있어. 왜 이래?"
            ),
            "pull_to_refresh_variant": (
                "앱에서 pull to refresh 해야 바뀐 값이 보여. 리스트 갱신이 늦어."
            ),
            "swipe_refresh_once_variant": (
                "앱에서 당겨서 새로고침 한 번 해야 최신 화면으로 바뀌어. 왜 이렇게 늦어?"
            ),
            "swipe_refresh_shortform_variant": (
                "앱에서 스와이프 새로고침해야 목록이 갱신돼. 왜 바로 안 보여?"
            ),
            "swipe_refresh_transliterated_variant": (
                "모바일에서 스와이프 리프레시 해야 화면이 따라와. 왜 바로 반영 안 돼?"
            ),
            "swipe_refresh_after_gesture_variant": (
                "앱에서 스와이프 새로고침하고 나서야 바뀐 값이 보여. 왜 바로 안 보여?"
            ),
            "swipe_refresh_pull_down_variant": (
                "앱에서 새로고침 쓸어내리고 나서야 새 값이 떠. 왜 바로 반영 안 돼?"
            ),
        }

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        tx_doc = "contents/database/transaction-isolation-locking.md"
        guardrail_doc = "contents/design-pattern/read-model-cutover-guardrails.md"

        for cue, prompt in prompts.items():
            with self.subTest(cue=cue):
                hits = self._search(prompt, top_k=5)

                self.assert_path_rank_at_most(hits, overview_doc, 1)
                self.assertNotIn(tx_doc, [hit["path"] for hit in hits[:3]])
                self.assert_path_rank_at_most(hits, guardrail_doc, 5)
                self.assert_ranks_ahead(hits, overview_doc, guardrail_doc)
                self.assertTrue(
                    all(hit["category"] == "design-pattern" for hit in hits[:3]),
                    hits[:3],
                )

    def test_beginner_stale_list_queries_prefer_lag_budget_companion_over_repository_boundary_doc(
        self,
    ) -> None:
        prompts = {
            "refresh_lag": (
                "읽기 모델을 처음 배우는데 저장했는데 목록 새로고침이 느리고 이전 화면 상태가 "
                "한동안 남아 있어. 왜 이런지 큰 그림부터 설명해줘"
            ),
            "detail_list_split": (
                "상세는 바뀌었는데 목록은 예전 값이야. 처음 배우는 사람 기준으로 왜 이런지 "
                "큰 그림부터 설명해줘"
            ),
        }

        primer_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        lag_budget_doc = "contents/design-pattern/projection-lag-budgeting-pattern.md"
        repository_doc = "contents/design-pattern/repository-boundary-aggregate-vs-read-model.md"

        for cue, prompt in prompts.items():
            with self.subTest(cue=cue):
                hits = self._search(prompt, top_k=5)

                self.assert_path_rank_at_most(hits, primer_doc, 1)
                self.assert_path_rank_at_most(hits, lag_budget_doc, 3)
                self.assert_ranks_ahead(hits, lag_budget_doc, repository_doc)

    def test_projection_cached_screen_after_save_golden_query_keeps_primer_first_without_http_cache_noise(
        self,
    ) -> None:
        http_cache_doc = "contents/network/http-state-session-cache.md"
        tx_doc = "contents/database/transaction-isolation-locking.md"
        query_ids = (
            "projection_freshness_intro_korean_cached_screen_after_save",
            "projection_freshness_symptom_only_mobile_screen_delay",
            "projection_freshness_symptom_only_mobile_screen_update_delay_variant",
            "projection_freshness_symptom_only_mobile_screen_update_delay_jiyeon_variant",
            "projection_freshness_symptom_only_mobile_swipe_refresh_lag",
            "projection_freshness_symptom_only_mobile_swipe_refresh_once_variant",
            "projection_freshness_symptom_only_mobile_swipe_refresh_shortform_variant",
            "projection_freshness_symptom_only_mobile_swipe_refresh_transliterated_variant",
            "projection_freshness_symptom_only_mobile_swipe_refresh_after_gesture_variant",
            "projection_freshness_symptom_only_mobile_swipe_refresh_pull_down_variant",
            "projection_freshness_symptom_only_mobile_app_screen_delay_variant",
            "projection_freshness_symptom_only_mobile_pull_to_refresh_variant",
            "projection_freshness_symptom_only_no_jargon_cached_screen",
            "projection_freshness_symptom_only_no_jargon_cached_screen_after_save_confusion",
            "projection_freshness_symptom_only_no_jargon_cached_screen_compact",
        )

        for query_id in query_ids:
            with self.subTest(query_id=query_id):
                query = _load_golden_fixture_query(query_id)
                hits = self._search(query["prompt"], top_k=5)

                overview_doc = query["expected_path"]
                self.assert_path_rank_at_most(hits, overview_doc, int(query.get("max_rank", 1)))
                self.assertNotIn(http_cache_doc, [hit["path"] for hit in hits[:3]])
                self.assertNotIn(tx_doc, [hit["path"] for hit in hits[:3]])

    def test_introductory_projection_vs_failover_queries_keep_primer_first_and_failover_signal_visible(
        self,
    ) -> None:
        prompts = {
            "compare": (
                "read model freshness 를 처음 배우는데 projection freshness 랑 "
                "failover 차이를 같이 비교해서 보고 싶어. stale read 랑 "
                "read-your-writes 큰 그림부터 설명해줘"
            ),
            "different": (
                "read model freshness 를 처음 배우는데 projection freshness 랑 "
                "failover 가 어떻게 다른지 같이 보고 싶어. stale read 랑 "
                "read-your-writes 큰 그림부터 설명해줘"
            ),
        }

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        failover_doc = "contents/system-design/global-traffic-failover-control-plane-design.md"

        for cue, prompt in prompts.items():
            with self.subTest(cue=cue):
                hits = self._search(prompt, top_k=5)

                self.assert_path_rank_at_most(hits, overview_doc, 1)
                self.assert_path_rank_at_most(hits, failover_doc, 3)
                self.assert_ranks_ahead(hits, overview_doc, failover_doc)

    def test_introductory_projection_vs_failover_visibility_query_keeps_primer_first_with_visibility_companion(
        self,
    ) -> None:
        hits = self._search(
            "read model freshness 를 처음 배우는데 projection freshness 랑 failover visibility window 차이를 같이 보고 싶어. stale read 랑 read-your-writes 큰 그림부터 설명해줘",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        visibility_doc = "contents/database/failover-visibility-window-topology-cache-playbook.md"
        global_failover_doc = "contents/system-design/global-traffic-failover-control-plane-design.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assert_path_rank_at_most(hits, visibility_doc, 3)
        self.assert_ranks_ahead(hits, overview_doc, visibility_doc)
        self.assertNotIn(global_failover_doc, [hit["path"] for hit in hits[:3]])

    def test_introductory_projection_vs_failover_visibility_alias_query_keeps_primer_first_with_visibility_companion(
        self,
    ) -> None:
        hits = self._search(
            "읽기 모델을 처음 배우는데 projection freshness 랑 failover visibility 차이를 같이 보고 싶어. stale read 랑 read-your-writes 큰 그림부터 설명해줘",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        visibility_doc = "contents/database/failover-visibility-window-topology-cache-playbook.md"
        global_failover_doc = "contents/system-design/global-traffic-failover-control-plane-design.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assert_path_rank_at_most(hits, visibility_doc, 3)
        self.assert_ranks_ahead(hits, overview_doc, visibility_doc)
        self.assertNotIn(global_failover_doc, [hit["path"] for hit in hits[:3]])

    def test_introductory_projection_vs_stateful_failover_placement_query_keeps_primer_first_with_stateful_companion(
        self,
    ) -> None:
        hits = self._search(
            "read model freshness 를 처음 배우는데 projection freshness 랑 stateful failover placement 차이를 같이 보고 싶어. stale read 랑 read-your-writes 큰 그림부터 설명해줘",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        stateful_doc = (
            "contents/system-design/stateful-workload-placement-failover-control-plane-design.md"
        )
        global_failover_doc = "contents/system-design/global-traffic-failover-control-plane-design.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assert_path_rank_at_most(hits, stateful_doc, 3)
        self.assert_ranks_ahead(hits, overview_doc, stateful_doc)
        self.assert_ranks_ahead(hits, stateful_doc, global_failover_doc)

    def test_korean_only_projection_vs_stateful_failover_placement_queries_keep_primer_first(
        self,
    ) -> None:
        prompts = (
            "읽기 모델 최신성을 처음 배우는데 투영 최신성이랑 상태 저장 워크로드 장애 전환 배치가 어떻게 다른지 같이 알고 싶어. 왜 저장 직후엔 예전 값이 남고 상태 저장 서비스는 장애 때 어느 복제본을 올릴지 따로 고민하는지 큰 그림부터 설명해줘",
            "입문자 기준으로 읽기 모델 최신성이랑 상태 저장 서비스 리더 배치, 배치 예산 판단이 뭐가 다른지 비교해줘. 저장 직후 예전 값이 보이는 문제와 장애 전환 때 리더를 어디에 둘지 고민하는 문제를 큰 그림부터 알고 싶어",
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        stateful_doc = (
            "contents/system-design/stateful-workload-placement-failover-control-plane-design.md"
        )
        global_failover_doc = "contents/system-design/global-traffic-failover-control-plane-design.md"

        for prompt in prompts:
            with self.subTest(prompt=prompt):
                hits = self._search(prompt, top_k=5)
                self.assert_path_rank_at_most(hits, overview_doc, 1)
                self.assert_path_rank_at_most(hits, stateful_doc, 3)
                self.assert_ranks_ahead(hits, overview_doc, stateful_doc)
                self.assert_ranks_ahead(hits, stateful_doc, global_failover_doc)

    def test_introductory_projection_vs_failover_verification_query_keeps_primer_first_without_jwt_playbook_noise(
        self,
    ) -> None:
        hits = self._search(
            "read model freshness 를 처음 배우는데 projection freshness 랑 failover verification 차이를 같이 보고 싶어. stale read 랑 read-your-writes 큰 그림부터 설명해줘",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        failover_doc = "contents/database/commit-horizon-after-failover-verification.md"
        jwt_doc = "contents/security/jwt-signature-verification-failure-playbook.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assert_path_rank_at_most(hits, failover_doc, 3)
        self.assert_ranks_ahead(hits, overview_doc, failover_doc)
        self.assertNotIn(jwt_doc, [hit["path"] for hit in hits[:3]])

    def test_introductory_projection_failover_visibility_vs_write_loss_verification_query_keeps_beginner_primer_first(
        self,
    ) -> None:
        hits = self._search(
            "read model freshness 를 처음 배우는데 failover visibility window 에서 stale read 가 보일 수 있다는 말이랑 write loss audit 로 verify 해야 한다는 말을 같이 들었어. 뭐가 다른지 큰 그림부터 설명해줘",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        visibility_doc = "contents/database/failover-visibility-window-topology-cache-playbook.md"
        verification_doc = "contents/database/commit-horizon-after-failover-verification.md"
        jwt_doc = "contents/security/jwt-signature-verification-failure-playbook.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assert_path_rank_at_most(hits, visibility_doc, 4)
        self.assert_path_rank_at_most(hits, verification_doc, 4)
        self.assert_ranks_ahead(hits, overview_doc, visibility_doc)
        self.assert_ranks_ahead(hits, overview_doc, verification_doc)
        self.assertNotIn(jwt_doc, [hit["path"] for hit in hits[:4]])

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

    def test_introductory_projection_cutover_safety_vs_failover_visibility_queries_keep_primer_first(
        self,
    ) -> None:
        prompts = {
            "compare": (
                "read model freshness 를 처음 배우는데 cutover safety window 랑 failover "
                "visibility window 차이를 같이 비교해서 보고 싶어. stale read 랑 "
                "read-your-writes 큰 그림부터 설명해줘"
            ),
            "different": (
                "read model freshness 를 처음 배우는데 cutover safety window 랑 failover "
                "visibility window 가 어떻게 다른지 같이 보고 싶어. stale read 랑 "
                "read-your-writes 큰 그림부터 설명해줘"
            ),
            "distinguish": (
                "read model freshness 를 처음 배우는데 cutover safety window 랑 failover "
                "visibility window 를 구별해서 보고 싶어. stale read 랑 "
                "read-your-writes 큰 그림부터 설명해줘"
            ),
        }

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        visibility_doc = "contents/database/failover-visibility-window-topology-cache-playbook.md"
        global_failover_doc = "contents/system-design/global-traffic-failover-control-plane-design.md"

        for cue, prompt in prompts.items():
            with self.subTest(cue=cue):
                hits = self._search(prompt, top_k=5)

                self.assert_path_rank_at_most(hits, overview_doc, 1)
                self.assert_path_rank_at_most(hits, visibility_doc, 3)
                self.assertNotIn(global_failover_doc, [hit["path"] for hit in hits[:3]])
                self.assert_ranks_ahead(hits, overview_doc, visibility_doc)

    def test_mixed_language_projection_cutover_safety_vs_failover_visibility_query_keeps_primer_first(
        self,
    ) -> None:
        hits = self._search(
            "읽기 모델을 처음 배우는데 cutover safety window vs failover visibility window 를 같이 비교해서 보고 싶어. stale read 랑 read-your-writes 큰 그림부터 설명해줘",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        visibility_doc = "contents/database/failover-visibility-window-topology-cache-playbook.md"
        global_failover_doc = "contents/system-design/global-traffic-failover-control-plane-design.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assert_path_rank_at_most(hits, visibility_doc, 3)
        self.assertNotIn(global_failover_doc, [hit["path"] for hit in hits[:3]])
        self.assert_ranks_ahead(hits, overview_doc, visibility_doc)

    def test_full_korean_projection_cutover_safety_vs_failover_visibility_query_keeps_primer_first(
        self,
    ) -> None:
        hits = self._search(
            "읽기 모델 최신성을 처음 배우는데 전환 안전 윈도우 랑 failover visibility window 차이를 같이 보고 싶어. 왜 예전 값이 보이고 방금 쓴 값 읽기 보장이 흔들리는지 큰 그림부터 설명해줘",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        visibility_doc = "contents/database/failover-visibility-window-topology-cache-playbook.md"
        global_failover_doc = "contents/system-design/global-traffic-failover-control-plane-design.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assert_path_rank_at_most(hits, visibility_doc, 3)
        self.assertNotIn(global_failover_doc, [hit["path"] for hit in hits[:3]])
        self.assert_ranks_ahead(hits, overview_doc, visibility_doc)

    def test_korean_projection_cutover_safety_window_keeps_failover_noise_out_of_top3(
        self,
    ) -> None:
        hits = self._search(
            "읽기 모델을 처음 배우는데 전환 안전 구간 동안 예전 값이 보이고 쓴 직후 읽기 보장이 왜 깨지는지 알고 싶어. failover rollback 같은 운영 얘기 전에 큰 그림부터 설명해줘",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        failover_doc = "contents/system-design/global-traffic-failover-control-plane-design.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assertNotIn(failover_doc, [hit["path"] for hit in hits[:3]])

    def test_full_korean_projection_cutover_safety_vs_failover_rollback_compare_keeps_primer_first(
        self,
    ) -> None:
        hits = self._search(
            "읽기 모델 최신성을 처음 배우는데 전환 안전 구간이랑 장애 전환 되돌리기 차이를 같이 비교해서 보고 싶어. 왜 예전 값이 보이고 방금 쓴 값 읽기 보장이 흔들리는지 큰 그림부터 설명해줘",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        failover_doc = "contents/system-design/global-traffic-failover-control-plane-design.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assertNotIn(failover_doc, [hit["path"] for hit in hits[:3]])

    def test_transliterated_projection_cutover_safety_zone_keeps_failover_noise_out_of_top3(
        self,
    ) -> None:
        hits = self._search(
            "읽기 모델을 처음 배우는데 컷오버 안전 구간 동안 예전 값이 보이고 쓴 직후 읽기 보장이 왜 깨지는지 알고 싶어. failover rollback 같은 운영 얘기 전에 큰 그림부터 설명해줘",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        failover_doc = "contents/system-design/global-traffic-failover-control-plane-design.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assertNotIn(failover_doc, [hit["path"] for hit in hits[:3]])
        self.assertTrue(all(hit["category"] == "design-pattern" for hit in hits[:3]), hits[:3])

    def test_projection_cutover_safety_shortform_question_keeps_primer_first(self) -> None:
        hits = self._search(
            "컷오버 안전 구간 뭐야",
            top_k=5,
        )

        overview_doc = "contents/design-pattern/read-model-staleness-read-your-writes.md"
        failover_doc = "contents/system-design/global-traffic-failover-control-plane-design.md"
        guardrail_doc = "contents/design-pattern/read-model-cutover-guardrails.md"

        self.assert_path_rank_at_most(hits, overview_doc, 1)
        self.assertNotIn(failover_doc, [hit["path"] for hit in hits[:3]])
        if guardrail_doc in [hit["path"] for hit in hits]:
            self.assert_ranks_ahead(hits, overview_doc, guardrail_doc)
        self.assertTrue(all(hit["category"] == "design-pattern" for hit in hits[:3]), hits[:3])

    def test_mixed_korean_english_projection_cutover_safety_window_keeps_failover_noise_out_of_top3(
        self,
    ) -> None:
        hits = self._search(
            "읽기 모델을 처음 배우는데 cutover safety window 동안 stale reads 가 보이고 쓴 직후 읽기 보장이 왜 깨지는지 큰 그림부터 알고 싶어. failover rollback 같은 운영 얘기는 잠깐 빼고",
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

    def test_spaced_transliterated_projection_cutover_safety_window_keeps_key_rotation_noise_out_of_top3(
        self,
    ) -> None:
        hits = self._search(
            "읽기 모델을 처음 배우는데 컷 오버 안전 윈도우 동안 예전 값이 보이고 쓴 직후 읽기 보장이 왜 흔들리는지 알고 싶어. key rotation rollback 같은 운영 얘기는 잠깐 빼고 큰 그림부터 설명해줘",
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

    def test_full_korean_projection_cutover_safety_vs_key_rotation_rollback_compare_keeps_primer_first(
        self,
    ) -> None:
        hits = self._search(
            "읽기 모델 최신성을 처음 배우는데 전환 안전 구간이랑 키 교체 되돌리기 차이를 같이 비교해서 보고 싶어. 왜 예전 값이 보이고 방금 쓴 값 읽기 보장이 흔들리는지 큰 그림부터 설명해줘",
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

    def test_korean_projection_cutover_safety_window_keeps_key_rotation_noise_out_of_top3(
        self,
    ) -> None:
        hits = self._search(
            "읽기 모델을 처음 배우는데 전환 안전 윈도우 동안 예전 값이 보이고 쓴 직후 읽기 보장이 왜 흔들리는지 알고 싶어. key rotation rollback 같은 운영 얘기는 잠깐 빼고 큰 그림부터 설명해줘",
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

    def test_failover_visibility_alias_query_keeps_visibility_doc_within_top3(self) -> None:
        hits = self._search(
            "failover visibility 때문에 stale primary 랑 topology cache divergence 가 왜 생기는지 알고 싶어",
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

    def test_failover_divergence_beginner_alias_queries_keep_divergence_doc_ahead_of_visibility_playbook(
        self,
    ) -> None:
        visibility_doc = "contents/database/failover-visibility-window-topology-cache-playbook.md"
        divergence_doc = "contents/database/failover-promotion-read-divergence.md"
        global_failover_doc = "contents/system-design/global-traffic-failover-control-plane-design.md"

        for query_id in (
            "failover_stale_primary_beginner_alias",
            "failover_old_primary_read_beginner_alias",
            "failover_promotion_read_divergence_beginner_alias",
        ):
            with self.subTest(query_id=query_id):
                query = _load_golden_fixture_query(query_id)
                hits = self._search(query["prompt"], top_k=5)

                self.assert_path_rank_at_most(
                    hits,
                    divergence_doc,
                    int(query.get("max_rank", 1)),
                )
                self.assert_path_rank_at_most(
                    hits,
                    visibility_doc,
                    int(query.get("companion_max_rank", 4)),
                )
                self.assert_ranks_ahead(hits, divergence_doc, visibility_doc)
                self.assertNotIn(global_failover_doc, [hit["path"] for hit in hits[:3]])

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


class CsRagFullModeFixturePathTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmpdir = tempfile.TemporaryDirectory()
        cls.tmp = Path(cls._tmpdir.name)
        CsRagSearchTest._build_fixture_index(cls.tmp)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmpdir.cleanup()

    def _row_id_for_path(self, path: str) -> int:
        conn = indexer.open_readonly(self.tmp)
        try:
            cur = conn.execute("SELECT id FROM chunks WHERE path = ?", (path,))
            row = cur.fetchone()
        finally:
            conn.close()
        self.assertIsNotNone(row, f"fixture path missing from local index: {path}")
        return int(row[0])

    def _dense_hits_for_paths(self, paths: list[str]) -> list[tuple[int, float]]:
        # Keep the primer path in the dense pool alongside its nearby companion
        # docs so this remains a deterministic full-mode fixture smoke rather
        # than a live-index-dependent ranking test.
        return [
            (self._row_id_for_path(path), 1.0 - (rank * 0.01))
            for rank, path in enumerate(paths)
        ]

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
        self.assertLess(
            paths.index(winner),
            paths.index(loser),
            f"expected {winner} ahead of {loser}, got {paths}",
        )

    def test_stable_full_mode_fixture_queries_keep_primer_ahead_of_companion_docs(
        self,
    ) -> None:
        contract = _load_stable_full_mode_fixture_contract()
        query_contracts = contract.get("queries", {})
        self.assertTrue(query_contracts)

        for query_id, query_contract in query_contracts.items():
            with self.subTest(query_id=query_id):
                query = _load_golden_fixture_query(query_id)
                companion_paths = list(query_contract.get("companion_paths", []))
                dense_paths = [query["expected_path"], *companion_paths]
                with mock.patch.object(
                    searcher,
                    "_dense_search",
                    return_value=self._dense_hits_for_paths(dense_paths),
                ) as dense_search:
                    hits = searcher.search(
                        query["prompt"],
                        learning_points=query.get("learning_points") or None,
                        mode="full",
                        index_root=self.tmp,
                        top_k=max(
                            5,
                            int(query_contract.get("companion_max_rank", 5)),
                        ),
                        use_reranker=False,
                        experience_level=query.get("experience_level"),
                    )

                dense_search.assert_called_once()
                self.assertTrue(hits, f"expected fixture hits for {query_id}")
                self.assert_path_rank_at_most(
                    hits,
                    query["expected_path"],
                    int(query.get("max_rank", 1)),
                )
                for companion_path in companion_paths:
                    self.assert_path_rank_at_most(
                        hits,
                        companion_path,
                        int(query_contract.get("companion_max_rank", 5)),
                    )
                    self.assert_ranks_ahead(
                        hits,
                        query["expected_path"],
                        companion_path,
                    )


if __name__ == "__main__":
    unittest.main()
