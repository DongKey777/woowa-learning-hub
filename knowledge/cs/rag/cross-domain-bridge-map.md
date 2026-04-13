# Cross-Domain Bridge Map

> 한 줄 요약: 질문이 한 영역만 건드리지 않을 때, 어떤 카테고리를 먼저 읽고 어떤 문서를 같이 묶어야 하는지 정리한 교차 연결 지도다.

## 목적

`CS-study`의 질문은 자주 한 분야에만 머물지 않는다.
예를 들어 `Spring` 질문처럼 보여도 실제로는 `Java`, `OS`, `Network`, `Security`까지 함께 봐야 답이 안정적이다.

이 문서는 그런 교차 질문을 빠르게 분해하기 위한 지도다.

## 브리지 규칙

1. 질문의 **주 도메인**을 먼저 정한다.
2. 그 다음 **보조 도메인**을 1~2개 붙인다.
3. 정의는 주 도메인 문서에서, 원리는 보조 도메인 문서에서 찾는다.
4. 운영/장애 질문이면 `SENIOR-QUESTIONS.md`를 같이 붙인다.

## 자주 쓰는 연결

| 주 도메인 | 같이 볼 도메인 | 우선 문서 |
|---|---|---|
| `spring` | `language/java`, `operating-system` | `spring/README.md`, `aop-proxy-mechanism.md`, `virtual-threads-project-loom.md` |
| `security` | `network`, `spring` | `security/README.md`, `http-state-session-cache.md`, `spring-security-architecture.md` |
| `database` | `network`, `software-engineering` | `database/README.md`, `slow-query-analysis-playbook.md`, `distributed-cache-design.md` |
| `system-design` | `database`, `network`, `security` | `system-design/README.md`, `distributed-cache-design.md`, `grpc-vs-rest.md`, `jwt-deep-dive.md` |
| `operating-system` | `language/java` | `operating-system/README.md`, `context-switching-deadlock-lockfree.md`, `virtual-threads-project-loom.md` |
| `network` | `operating-system`, `spring` | `network/README.md`, `nat-conntrack-ephemeral-port-exhaustion.md`, `timeout-retry-backoff-practical.md`, `spring-resilience4j-retry-circuit-breaker-bulkhead.md` |
| `network` | `security` | `forwarded-x-forwarded-for-x-real-ip-trust-boundary.md`, `api-key-hmac-signature-replay-protection.md`, `tls-loadbalancing-proxy.md` |
| `language/java` | `operating-system`, `network` | `language/README.md`, `direct-buffer-offheap-memory-troubleshooting.md`, `oom-killer-cgroup-memory-pressure.md`, `nat-conntrack-ephemeral-port-exhaustion.md` |
| `language/java` | `data-structure` | `java-equals-hashcode-comparable-contracts.md`, `collections-performance.md`, `treemap-vs-hashmap-vs-linkedhashmap.md` |
| `design-pattern` | `spring`, `software-engineering` | `design-pattern/README.md`, `strategy-pattern.md`, `decorator-vs-proxy.md` |
| `software-engineering` | `database`, `system-design` | `software-engineering/README.md`, `strangler-fig-migration-contract-cutover.md`, `cdc-debezium-outbox-binlog.md`, `workflow-orchestration-saga-design.md` |
| `software-engineering` | `spring`, `database` | `branch-by-abstraction-vs-feature-flag-vs-strangler.md`, `spring-eventlistener-transaction-phase-outbox.md`, `outbox-inbox-domain-events.md` |
| `data-structure` | `algorithm`, `database` | `data-structure/README.md`, `hashmap-internals.md`, `lru-cache-design.md` |
| `system-design` | `database`, `security` | `payment-system-ledger-idempotency-reconciliation-design.md`, `idempotency-key-and-deduplication.md`, `service-to-service-auth-mtls-jwt-spiffe.md` |
| `algorithm` | `data-structure`, `system-design` | `algorithm/README.md`, `sliding-window-patterns.md`, `topological-sort-patterns.md` |

## 브리지 예시

### Spring + Java + OS

질문 예시:

`Virtual Threads를 쓰면 Spring MVC가 왜 더 단순해지나요?`

읽는 순서:

1. [Spring MVC vs WebFlux](../contents/spring/spring-webflux-vs-mvc.md)
2. [Virtual Threads(Project Loom)](../contents/language/java/virtual-threads-project-loom.md)
3. [I/O 모델과 이벤트 루프](../contents/operating-system/io-models-and-event-loop.md)

### Security + Network

질문 예시:

`JWT는 왜 stateless인데도 로그아웃이 어려운가요?`

읽는 순서:

1. [JWT 깊이 파기](../contents/security/jwt-deep-dive.md)
2. [HTTP의 무상태성과 쿠키, 세션, 캐시](../contents/network/http-state-session-cache.md)
3. [Spring Security 아키텍처](../contents/spring/spring-security-architecture.md)

### Security + Network + Spring

질문 예시:

`서비스 간 인증에서 mTLS와 JWT를 어떻게 같이 쓰나요?`

읽는 순서:

1. [Service-to-Service Auth: mTLS, JWT, SPIFFE](../contents/security/service-to-service-auth-mtls-jwt-spiffe.md)
2. [Service Mesh, Sidecar Proxy](../contents/network/service-mesh-sidecar-proxy.md)
3. [Spring Security 아키텍처](../contents/spring/spring-security-architecture.md)

### Network + Security

질문 예시:

`X-Forwarded-For를 어디까지 믿어야 하나요?`

읽는 순서:

1. [Forwarded / X-Forwarded-For / X-Real-IP 신뢰 경계](../contents/network/forwarded-x-forwarded-for-x-real-ip-trust-boundary.md)
2. [TLS, 로드밸런싱, 프록시](../contents/network/tls-loadbalancing-proxy.md)
3. [API Key / HMAC Signature / Replay Protection](../contents/security/api-key-hmac-signature-replay-protection.md)

### Spring + Database + Software Engineering

질문 예시:

`@TransactionalEventListener와 Outbox는 언제 다르게 쓰나요?`

읽는 순서:

1. [Spring EventListener, TransactionalEventListener, Outbox](../contents/spring/spring-eventlistener-transaction-phase-outbox.md)
2. [Domain Events, Outbox, Inbox](../contents/software-engineering/outbox-inbox-domain-events.md)
3. [Outbox, Saga, Eventual Consistency](../contents/database/outbox-saga-eventual-consistency.md)

### System Design + Database + Security

질문 예시:

`결제 시스템에서 ledger와 reconciliation을 왜 따로 보나요?`

읽는 순서:

1. [Payment System, Ledger, Idempotency, Reconciliation](../contents/system-design/payment-system-ledger-idempotency-reconciliation-design.md)
2. [멱등성 키와 중복 방지](../contents/database/idempotency-key-and-deduplication.md)
3. [Service-to-Service Auth: mTLS, JWT, SPIFFE](../contents/security/service-to-service-auth-mtls-jwt-spiffe.md)

### Database + System Design

질문 예시:

`분산 캐시를 넣으면 DB 부하는 줄어드는데, 왜 정합성 문제가 먼저 나오나요?`

읽는 순서:

1. [인덱스와 실행 계획](../contents/database/index-and-explain.md)
2. [분산 캐시 설계](../contents/system-design/distributed-cache-design.md)
3. [Back-of-Envelope 추정법](../contents/system-design/back-of-envelope-estimation.md)

### Java + OS

질문 예시:

`heap은 괜찮은데 RSS만 올라가요`

읽는 순서:

1. [Direct Buffer, Off-Heap, Native Memory Troubleshooting](../contents/language/java/direct-buffer-offheap-memory-troubleshooting.md)
2. [OOM Killer, cgroup Memory Pressure](../contents/operating-system/oom-killer-cgroup-memory-pressure.md)
3. [mmap, sendfile, splice, zero-copy](../contents/operating-system/mmap-sendfile-splice-zero-copy.md)

### Software Engineering + Database + System Design

질문 예시:

`레거시를 점진적으로 옮길 때 dual write와 cutover를 어떻게 설계하나요?`

읽는 순서:

1. [Strangler Fig Migration, Contract, Cutover](../contents/software-engineering/strangler-fig-migration-contract-cutover.md)
2. [CDC, Debezium, Outbox, Binlog](../contents/database/cdc-debezium-outbox-binlog.md)
3. [Workflow Orchestration / Saga](../contents/system-design/workflow-orchestration-saga-design.md)

## 체크 포인트

- 문서 하나로 끝나는 질문인지, 연결이 필요한 질문인지 먼저 구분한다.
- 주 도메인은 `README`에서, 원리는 deep dive에서 찾는다.
- 보조 도메인은 2개를 넘기기 전에 질문을 다시 잘게 쪼갠다.

## 한 줄 정리

질문이 여러 축을 건드리면, 주 도메인 1개와 보조 도메인 1~2개를 묶어 읽어야 RAG가 덜 흔들린다.
