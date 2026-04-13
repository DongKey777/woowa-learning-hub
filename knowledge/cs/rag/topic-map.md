# Topic Map

> 한 줄 요약: `CS-study`를 RAG로 쓸 때 어떤 질문이 어떤 문서 축으로 가야 하는지 정리한 topic routing map이다.

## 목적

이 문서는 단순 목차가 아니다.
RAG가 질문을 받았을 때 다음을 빠르게 판단하기 위한 라우팅 표다.

- 어떤 카테고리를 먼저 찾을지
- 어떤 문서를 우선 인용할지
- 같은 주제라도 정의, 실전, 운영, 트레이드오프 중 무엇을 먼저 가져올지

## Top-Level 라우팅

| 질문 의도 | 먼저 볼 카테고리 | 우선 문서 |
|---|---|---|
| 넓은 교차 질문, 증상 기반 디버깅, 큰 그림 설명 | `master-notes/` | `latency-debugging-master-note.md`, `consistency-boundary-master-note.md`, `auth-session-token-master-note.md`, `database-to-spring-transaction-master-note.md`, `retry-timeout-idempotency-master-note.md`, `migration-cutover-master-note.md` |
| 저장/트랜잭션/쿼리 문제 | `contents/database/` | `README.md`, `index-and-explain.md`, `slow-query-analysis-playbook.md`, `redo-log-undo-log-checkpoint-crash-recovery.md`, `index-condition-pushdown-filesort-temporary-table.md` |
| HTTP, TLS, 실시간 통신 | `contents/network/` | `README.md`, `grpc-vs-rest.md`, `http3-quic-practical-tradeoffs.md`, `tcp-congestion-control.md`, `service-mesh-sidecar-proxy.md`, `nat-conntrack-ephemeral-port-exhaustion.md`, `forwarded-x-forwarded-for-x-real-ip-trust-boundary.md` |
| OS, 스레드, I/O, 컨테이너 | `contents/operating-system/` | `README.md`, `epoll-kqueue-io-uring.md`, `container-cgroup-namespace.md`, `false-sharing-cache-line.md`, `run-queue-load-average-cpu-saturation.md`, `ebpf-perf-strace-production-tracing.md`, `monotonic-clock-wall-clock-timeout-deadline.md` |
| Spring 내부 동작 | `contents/spring/` | `README.md`, `spring-security-architecture.md`, `spring-webflux-vs-mvc.md`, `spring-transaction-debugging-playbook.md`, `spring-observability-micrometer-tracing.md`, `spring-resilience4j-retry-circuit-breaker-bulkhead.md`, `spring-eventlistener-transaction-phase-outbox.md` |
| Java 런타임/GC/리플렉션 | `contents/language/` | `README.md`, `g1-vs-zgc.md`, `reflection-cost-and-alternatives.md`, `virtual-threads-project-loom.md`, `jfr-jmc-performance-playbook.md`, `classloader-memory-leak-playbook.md`, `direct-buffer-offheap-memory-troubleshooting.md`, `java-memory-model-happens-before-volatile-final.md`, `java-equals-hashcode-comparable-contracts.md` |
| 설계/아키텍처/경계 | `contents/software-engineering/` | `README.md`, `solid-failure-patterns.md`, `ddd-bounded-context-failure-patterns.md`, `monolith-to-msa-failure-patterns.md`, `strangler-fig-migration-contract-cutover.md` |
| 시스템 설계 면접 | `contents/system-design/` | `README.md`, `system-design-framework.md`, `back-of-envelope-estimation.md`, `distributed-cache-design.md`, `chat-system-design.md`, `newsfeed-system-design.md`, `notification-system-design.md`, `multi-tenant-saas-isolation-design.md`, `payment-system-ledger-idempotency-reconciliation-design.md` |
| 디자인 패턴 | `contents/design-pattern/` | `README.md`, `strategy-pattern.md`, `decorator-vs-proxy.md`, `builder-pattern.md`, `facade-vs-adapter-vs-proxy.md` |
| 자료구조/알고리즘 | `contents/data-structure/`, `contents/algorithm/` | `README.md`, `hashmap-internals.md`, `treemap-vs-hashmap-vs-linkedhashmap.md`, `sliding-window-patterns.md`, `bloom-filter.md`, `network-flow-intuition.md`, `trie-prefix-search-autocomplete.md` |
| 인증/인가/보안 | `contents/security/` | `README.md`, `authentication-vs-authorization.md`, `jwt-deep-dive.md`, `oauth2-authorization-code-grant.md`, `oidc-id-token-userinfo-boundaries.md`, `cors-samesite-preflight.md`, `service-to-service-auth-mtls-jwt-spiffe.md`, `api-key-hmac-signature-replay-protection.md` |

## Cross-Domain Bridges

질문 하나가 여러 축을 건드리면, 아래 연결을 우선한다.

- DB 성능 + 네트워크 지연: `database/` + `network/`
- Spring 동작 + Java 런타임: `spring/` + `language/java/`
- 인증/인가 + HTTP 상태성: `security/` + `network/`
- 캐시/메시징 + 시스템 설계: `software-engineering/` + `system-design/`
- 컨테이너 운영 + OS 지식: `operating-system/` + `system-design/`
- JWT/OAuth2 문제: `security/` + `spring/` + `network/`
- OOM/latency 문제: `language/java/` + `operating-system/` + `spring/`
- 검색/피드/알림 문제: `system-design/` + `database/` + `network/`
- 캐시 무효화/정합성 문제: `system-design/` + `software-engineering/` + `database/`
- NAT/egress 장애: `network/` + `operating-system/` + `spring/`
- 서비스 간 인증: `security/` + `network/` + `spring/`
- native memory/RSS 문제: `language/java/` + `operating-system/` + `network/`
- 점진 전환/cutover 문제: `software-engineering/` + `database/` + `system-design/`
- multi-tenant/noisy neighbor 문제: `system-design/` + `database/` + `security/` + `software-engineering/`
- forwarded trust boundary 문제: `network/` + `security/`
- HMAC signed request / replay 문제: `security/` + `network/`
- transaction phase / outbox 문제: `spring/` + `software-engineering/` + `database/`
- ledger / reconciliation 문제: `system-design/` + `database/` + `security/`
- JMM / happens-before 문제: `language/java/` + `operating-system/`
- equals/hashCode/Comparable 문제: `language/java/` + `data-structure/`

## Topic Priority Rules

1. 먼저 카테고리 `README.md`를 본다.
2. 질문이 넓거나 교차 도메인이면 `master-notes/`를 먼저 본다.
3. 그다음 1차 문서 1개를 고른다.
4. 질문이 운영/장애/트레이드오프를 포함하면 심화 문서를 우선한다.
5. 같은 개념의 정의 문서와 사례 문서를 함께 가져간다.

## Retrieval Hint

RAG 질의는 보통 아래 순서로 분해하면 좋다.

1. 문제 영역을 결정한다.
2. 기본 정의 문서를 찾는다.
3. 실전/장애/트레이드오프 문서를 붙인다.
4. 마지막에 시니어 질문을 붙여 검증한다.

예를 들면:

- `JPA 인덱스가 안 타요` -> `database/index-and-explain.md` + `database/slow-query-analysis-playbook.md`
- `JWT 로그아웃이 안 돼요` -> `security/jwt-deep-dive.md` + `security/authentication-vs-authorization.md`
- `Spring에서 AOP가 왜 안 먹지` -> `spring/aop-proxy-mechanism.md` + `spring/transaction-debugging-playbook.md`
- `Thread가 많아졌는데 지연이 줄지 않아요` -> `operating-system/context-switching-deadlock-lockfree.md` + `language/java/virtual-threads-project-loom.md`
- `ClassLoader leak 같아요` -> `language/java/classloader-memory-leak-playbook.md` + `spring/spring-test-slices-context-caching.md`
- `CDN 캐시가 이상해요` -> `network/cdn-cache-key-invalidation.md` + `system-design/file-storage-presigned-url-cdn-design.md`
- `connect timeout이 늘고 NAT가 의심돼요` -> `network/nat-conntrack-ephemeral-port-exhaustion.md` + `network/timeout-retry-backoff-practical.md`
- `heap은 괜찮은데 RSS만 올라요` -> `language/java/direct-buffer-offheap-memory-troubleshooting.md` + `operating-system/oom-killer-cgroup-memory-pressure.md`
- `서비스 간 인증을 어떻게 설계하죠` -> `security/service-to-service-auth-mtls-jwt-spiffe.md` + `network/service-mesh-sidecar-proxy.md`
- `레거시를 점진적으로 옮기고 싶어요` -> `software-engineering/strangler-fig-migration-contract-cutover.md` + `database/cdc-debezium-outbox-binlog.md`
- `멀티 테넌트 noisy neighbor가 심해요` -> `system-design/multi-tenant-saas-isolation-design.md` + `system-design/rate-limiter-design.md`
- `p99가 튀는데 DB, JVM, 네트워크 중 어디가 문제인지 모르겠어요` -> `master-notes/latency-debugging-master-note.md` + `operating-system/psi-pressure-stall-information-runtime-debugging.md`
- `세션이랑 JWT랑 OIDC를 지금 서비스에 어떻게 섞어야 할지 모르겠어요` -> `master-notes/auth-session-token-master-note.md` + `security/jwt-deep-dive.md`
- `트랜잭션과 outbox와 retry를 같이 설명해줘` -> `master-notes/retry-timeout-idempotency-master-note.md` + `master-notes/database-to-spring-transaction-master-note.md`

## RAG Note

이 repo는 같은 개념이 여러 폴더에 등장한다.
그럴 때는 중복 제거보다 **시각 분리**를 우선한다.

- `database/`는 저장소 관점
- `network/`는 프로토콜/전송 관점
- `operating-system/`는 커널/자원 관점
- `spring/`는 프레임워크 내부 동작 관점
- `software-engineering/`는 설계/경계 관점

질문을 받을 때 "어디서 설명해야 가장 정확한가"를 먼저 고르면 RAG 품질이 올라간다.
