# Master Notes Index

> 증상, 의사결정, 교차 관점 중심으로 여러 CS 문서를 묶어 읽기 위한 상위 노트 인덱스

> retrieval-anchor-keywords: master notes index, synthesis navigator, cross-domain guide, symptom-first reading, broad question routing, latency cluster, transaction cluster, master note catalog, stale read, stale-read, read-after-write, replica lag, 499, client disconnect, broken pipe, cancellation propagation, auth outage, auth-outage, login loop, 401 storm, 403 storm, session store outage, replay session defense bundle, service delegation boundary bundle, hardware trust recovery bundle, replay store down, nonce store down, acting on behalf of, break glass, hardware attestation recovery, trust bundle recovery

## 이 디렉토리의 역할

이 디렉토리는 `contents/`의 카테고리 문서를 대체하지 않는다.  
대신 다음 역할을 담당한다.

- 여러 카테고리를 하나의 실전 질문으로 묶기
- 미션 중 필요한 큰 그림을 빠르게 제공하기
- RAG가 광범위한 질문을 놓치지 않도록 상위 요약 레이어 만들기
- 회고와 시니어 질문 대비용 상위 설명 노트 제공하기

문서 역할 이름이 헷갈리면 [Navigation Taxonomy](../rag/navigation-taxonomy.md)를 먼저 보고, 저장소 전체 진입점은 [CS Root README](../README.md)에서 다시 잡는다.

## 추천 진입 방식

- `latency`, `timeout`, `retry`, `backpressure`
- `transaction`, `consistency`, `idempotency`, `outbox`
- `auth`, `session`, `token`, `trust boundary`
- `replay`, `replay store`, `nonce store`, `dedupe window`, `replay-safe retry`
- `migration`, `rollout`, `cutover`, `rollback`
- `delegation`, `acting on behalf of`, `break glass`, `support access`, `trust bundle`, `attestation`
- `cache`, `hot key`, `invalidation`, `stampede`
- `stale read`, `stale-read`, `read-after-write`, `replica lag`, `freshness budget`
- `499`, `client disconnect`, `broken pipe`, `cancel propagation`
- `auth outage`, `auth-outage`, `login loop`, `401`, `403`, `session store`
- `JVM`, `native memory`, `RSS`, `page cache`, `cgroup`

## Symptom Shortcuts

- `stale-read`, `stale read`, `read-after-write failure`, `방금 쓴 데이터가 안 보임`, `replica lag`부터 떠오르면 [Replica Freshness Master Note](./replica-freshness-master-note.md)로 먼저 들어가고, 일관성 경계 자체를 넓게 잡아야 하면 [Eventual Consistency Master Note](./eventual-consistency-master-note.md), [Cache Consistency Master Note](./cache-consistency-master-note.md)로 이어진다.
- `dirty read`, `lost update`, `write skew`, `phantom`, `@Transactional`, `왜 안 롤백되지`, `self invocation`, `checked exception commit`이 같이 나오면 [Database to Spring Transaction Master Note](./database-to-spring-transaction-master-note.md)를 대표 진입점으로 잡고, invariant scope가 더 먼저면 [Transaction Boundary Master Note](./transaction-boundary-master-note.md), lock/deadlock 감각이 먼저면 [Transaction Locking Master Note](./transaction-locking-master-note.md)를 함께 본다.
- `499`, `client disconnect`, `broken pipe`, `cancelled request`, `zombie work`가 섞이면 [Network Failure Handling Master Note](./network-failure-handling-master-note.md)와 [Edge Request Lifecycle Master Note](./edge-request-lifecycle-master-note.md)를 먼저 보고, timeout/retry budget까지 엮이면 [Retry, Timeout, Idempotency Master Note](./retry-timeout-idempotency-master-note.md)로 확장한다.
- `auth-outage`, `auth outage`, `login loop`, `cookie drop`, `401/403 storm`, `session store outage`라면 [Auth, Session, Token Master Note](./auth-session-token-master-note.md)를 대표 진입점으로 잡고, 브라우저/BFF 경계면 [Browser Auth Frontend Backend Master Note](./browser-auth-frontend-backend-master-note.md), 브라우저 callback이 없으면 [OAuth Device Code Flow / Security Model](../contents/security/oauth-device-code-flow-security.md), authorization request hardening이 먼저면 [OAuth PAR / JAR Basics](../contents/security/oauth-par-jar-basics.md), service identity나 policy deny면 [Trust and Identity Master Note](./trust-and-identity-master-note.md), [Authz and Permission Master Note](./authz-and-permission-master-note.md)로 이어진다.
- `replay store down`, `nonce store down`, `duplicate request after retry`, `replay-safe retry`, `backfill replay`가 섞이면 [Retry, Timeout, Idempotency Master Note](./retry-timeout-idempotency-master-note.md)를 먼저 보고, 저장소 replay/backfill/repair 축이 더 크면 [Data Pipeline Replay Master Note](./data-pipeline-replay-master-note.md), [Eventual Consistency Master Note](./eventual-consistency-master-note.md)로 이어진다.
- `acting on behalf of`, `break glass`, `delegated admin`, `support access notification`, `trust bundle rollback`, `hardware attestation failure`라면 [Trust and Identity Master Note](./trust-and-identity-master-note.md)를 대표 진입점으로 잡고, session fallout까지 붙으면 [Auth, Session, Token Master Note](./auth-session-token-master-note.md), rollout/cutover 문맥이 크면 [Migration Cutover Master Note](./migration-cutover-master-note.md)로 이어진다.

## Start Here

아래 노트는 겹치는 주제를 통합적으로 보는 **대표 진입점**이다.

- [Latency Debugging Master Note](./latency-debugging-master-note.md)
- [Consistency Boundary Master Note](./consistency-boundary-master-note.md)
- [Auth, Session, Token Master Note](./auth-session-token-master-note.md)
- [Retry, Timeout, Idempotency Master Note](./retry-timeout-idempotency-master-note.md)
- [Database to Spring Transaction Master Note](./database-to-spring-transaction-master-note.md)
- [Migration Cutover Master Note](./migration-cutover-master-note.md)
- [Resource Exhaustion Master Note](./resource-exhaustion-master-note.md)
- [Observability Debugging Master Note](./observability-debugging-master-note.md)

## Reading Rule

- `대표 노트`는 큰 그림과 의사결정 경계를 먼저 잡을 때 읽는다.
- `보조 노트`는 같은 군집 안에서 특정 하위 문제를 더 깊게 볼 때 읽는다.
- broad query에서는 대표 노트가 먼저 회수되고, 보조 노트는 보완용으로 따라오는 구조를 지향한다.

## Consistency / Transaction / Storage

- [Consistency Boundary Master Note](./consistency-boundary-master-note.md)
- [Database to Spring Transaction Master Note](./database-to-spring-transaction-master-note.md)
- [Transaction Boundary Master Note](./transaction-boundary-master-note.md)
- [Transaction Locking Master Note](./transaction-locking-master-note.md)
- [Eventual Consistency Master Note](./eventual-consistency-master-note.md)
- [Replica Freshness Master Note](./replica-freshness-master-note.md)
- [Storage Query Performance Master Note](./storage-query-performance-master-note.md)
- [Storage Engine Behavior Master Note](./storage-engine-behavior-master-note.md)
- [Durability Recovery Master Note](./durability-recovery-master-note.md)
- [Rollback and Recovery Master Note](./rollback-and-recovery-master-note.md)
- [Data Migration Consistency Master Note](./data-migration-consistency-master-note.md)

## Auth / Identity / Trust

- [Auth Session Token Master Note](./auth-session-token-master-note.md)
- [Authz and Permission Master Note](./authz-and-permission-master-note.md)
- [Browser Auth Frontend Backend Master Note](./browser-auth-frontend-backend-master-note.md)
- [Browser Session Security Master Note](./browser-session-security-master-note.md)
- [Trust and Identity Master Note](./trust-and-identity-master-note.md)
- [Trust Boundary Proxy Master Note](./trust-boundary-proxy-master-note.md)
- [Identity Propagation Master Note](./identity-propagation-master-note.md)

## Delivery / Failure / Reliability

- [Retry Timeout Idempotency Master Note](./retry-timeout-idempotency-master-note.md)
- [Failure Amplification Master Note](./failure-amplification-master-note.md)
- [Network Failure Handling Master Note](./network-failure-handling-master-note.md)
- [Queue Worker Reliability Master Note](./queue-worker-reliability-master-note.md)
- [Queue Backpressure Master Note](./queue-backpressure-master-note.md)
- [Event-Driven Delivery Master Note](./event-driven-delivery-master-note.md)
- [Realtime Delivery Master Note](./realtime-delivery-master-note.md)
- [Async Context Propagation Master Note](./async-context-propagation-master-note.md)
- [Observability to Incident Master Note](./observability-to-incident-master-note.md)
- [Rollout Safety Master Note](./rollout-safety-master-note.md)

## Capacity / Performance / Runtime

- [Latency Debugging Master Note](./latency-debugging-master-note.md)
- [Resource Exhaustion Master Note](./resource-exhaustion-master-note.md)
- [JVM to OS Performance Master Note](./jvm-to-os-performance-master-note.md)
- [Cost and Capacity Master Note](./cost-and-capacity-master-note.md)
- [Capacity Estimation Master Note](./capacity-estimation-master-note.md)
- [Service Discovery Connection Lifecycle Master Note](./service-discovery-connection-lifecycle-master-note.md)
- [Edge Request Lifecycle Master Note](./edge-request-lifecycle-master-note.md)
- [Scheduler Deadline Time Master Note](./scheduler-deadline-time-master-note.md)

## Cache / Search / Tenancy / Platform

- [Caching Invalidation Master Note](./caching-invalidation-master-note.md)
- [Cache Consistency Master Note](./cache-consistency-master-note.md)
- [Search Ranking Freshness Master Note](./search-ranking-freshness-master-note.md)
- [Tenancy Isolation Master Note](./tenancy-isolation-master-note.md)
- [Multi-Tenant Noisy Neighbor Master Note](./multi-tenant-noisy-neighbor-master-note.md)
- [Quota Rate Limit Fairness Master Note](./quota-rate-limit-fairness-master-note.md)
- [Batch Processing Master Note](./batch-processing-master-note.md)
- [Data Pipeline Replay Master Note](./data-pipeline-replay-master-note.md)

## Governance / Ownership / Lifecycle

- [Schema Evolution Master Note](./schema-evolution-master-note.md)
- [Data Contract Governance Master Note](./data-contract-governance-master-note.md)
- [Service Ownership Master Note](./service-ownership-master-note.md)
- [Artifact Supply Chain Master Note](./artifact-supply-chain-master-note.md)
- [Migration Cutover Master Note](./migration-cutover-master-note.md)
- [Pricing Billing Master Note](./pricing-billing-master-note.md)

## 관련 문서

- [CS Root README](../README.md)
- [Security README](../contents/security/README.md)
- [System Design README](../contents/system-design/README.md)
- [Master Notes Guide](../MASTER-NOTES.md)
- [Navigation Taxonomy](../rag/navigation-taxonomy.md)
- [Topic Map](../rag/topic-map.md)
- [Query Playbook](../rag/query-playbook.md)
- [Cross-Domain Bridge Map](../rag/cross-domain-bridge-map.md)
