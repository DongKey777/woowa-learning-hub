# Advanced Backend CS Roadmap

> 기본 개념을 한 번 돌린 뒤, 시니어 질문까지 버틸 수 있는 수준으로 올리기 위한 심화 학습 가이드

## 이 문서의 목표

이 문서는 “신입 백엔드 로드맵”을 한 바퀴 돌린 뒤,

- 개념을 더 깊게 파고
- 트레이드오프를 설명하고
- 장애 시나리오를 말하고
- 시스템 설계 질문에도 답할 수 있게

만드는 것을 목표로 한다.

즉 **암기형 CS -> 설명 가능한 CS -> 판단 가능한 CS**로 올라가기 위한 문서다.

## 1단계. 데이터베이스를 운영 관점으로 확장

추천 순서:

1. [트랜잭션 격리수준과 락](./contents/database/transaction-isolation-locking.md)
2. [트랜잭션 실전 시나리오](./contents/database/transaction-case-studies.md)
3. [인덱스와 실행 계획](./contents/database/index-and-explain.md)
4. [SQL 조인과 쿼리 실행 순서](./contents/database/sql-joins-and-query-order.md)
5. [MVCC, Replication, Sharding](./contents/database/mvcc-replication-sharding.md)
6. [Schema Migration, Partitioning, CDC, CQRS](./contents/database/schema-migration-partitioning-cdc-cqrs.md)
7. [JDBC 실전 코드 패턴](./contents/database/jdbc-code-patterns.md)
8. [멱등성 키와 중복 방지](./contents/database/idempotency-key-and-deduplication.md)
9. [쿼리 튜닝 체크리스트](./contents/database/query-tuning-checklist.md)
10. [Outbox, Saga, Eventual Consistency](./contents/database/outbox-saga-eventual-consistency.md)
11. [Deadlock Case Study](./contents/database/deadlock-case-study.md)
12. [Connection Pool, Transaction Propagation, Bulk Write](./contents/database/connection-pool-transaction-propagation-bulk-write.md)
13. [B+Tree vs LSM-Tree](./contents/database/bptree-vs-lsm-tree.md)
14. [Online Schema Change 전략](./contents/database/online-schema-change-strategies.md)
15. [Slow Query Analysis Playbook](./contents/database/slow-query-analysis-playbook.md)
16. [MySQL Optimizer Hint와 Index Merge](./contents/database/mysql-optimizer-hints-index-merge.md)
17. [Hikari Connection Pool 튜닝](./contents/database/hikari-connection-pool-tuning.md)
18. [정규화 vs 반정규화 Trade-off](./contents/database/normalization-denormalization-tradeoffs.md)
19. [Replica Lag와 Read-after-Write 전략](./contents/database/replica-lag-read-after-write-strategies.md)
20. [CDC, Debezium, Outbox, Binlog](./contents/database/cdc-debezium-outbox-binlog.md)
21. [Offset vs Seek Pagination](./contents/database/pagination-offset-vs-seek.md)
22. [Write Skew와 Phantom Read 사례](./contents/database/write-skew-phantom-read-case-studies.md)
23. [Redo Log, Undo Log, Checkpoint, Crash Recovery](./contents/database/redo-log-undo-log-checkpoint-crash-recovery.md)
24. [Index Condition Pushdown, Filesort, Temporary Table](./contents/database/index-condition-pushdown-filesort-temporary-table.md)
이 단계에서 목표:

- 정합성 문제를 구체 사례로 설명할 수 있다.
- 인덱스/실행 계획을 보고 병목을 추론할 수 있다.
- replication, sharding, migration의 목적과 비용을 설명할 수 있다.
- JDBC 저장 계층 구조를 읽고 비판할 수 있다.
- outbox / saga / eventual consistency가 왜 필요한지 설명할 수 있다.
- idempotency key가 트랜잭션만으로 해결되지 않는 문제를 어떻게 메우는지 설명할 수 있다.
- connection pool과 bulk write 전략의 trade-off를 설명할 수 있다.
- B+Tree와 LSM-Tree가 읽기/쓰기 워크로드에 따라 어떤 차이를 만드는지 설명할 수 있다.
- 대용량 스키마 변경과 슬로우 쿼리 대응을 운영 절차 관점으로 설명할 수 있다.
- optimizer hint, replica lag, CDC, pagination, write skew 같은 실전 이슈를 저장/트랜잭션 모델과 연결해 설명할 수 있다.
- Optimizer 힌트, 커넥션 풀, 정규화 판단이 실제 운영 성능과 모델링에 어떤 차이를 만드는지 설명할 수 있다.
- redo/undo, checkpoint, crash recovery를 commit latency, fsync, 복구 시간과 연결해 설명할 수 있다.
- `Using index condition`, `Using filesort`, `Using temporary`를 실행 계획의 냄새로 읽고 어떤 튜닝이 필요한지 설명할 수 있다.

## 2단계. 네트워크를 시스템 관점으로 확장

추천 순서:

1. [HTTP 메서드, REST, 멱등성](./contents/network/http-methods-rest-idempotency.md)
2. [HTTP의 무상태성과 쿠키, 세션, 캐시](./contents/network/http-state-session-cache.md)
3. [TLS, 로드밸런싱, 프록시](./contents/network/tls-loadbalancing-proxy.md)
4. [DNS, CDN, WebSocket, HTTP/2, HTTP/3](./contents/network/dns-cdn-websocket-http2-http3.md)
5. [SSE, WebSocket, Polling](./contents/network/sse-websocket-polling.md)
6. [Timeout, Retry, Backoff 실전](./contents/network/timeout-retry-backoff-practical.md)
7. [Cache-Control 실전](./contents/network/cache-control-practical.md)
8. [API Gateway, Reverse Proxy 운영 포인트](./contents/network/api-gateway-reverse-proxy-operational-points.md)
9. [Connection Keep-Alive, Load Balancing, Circuit Breaker](./contents/network/connection-keepalive-loadbalancing-circuit-breaker.md)
10. [gRPC vs REST](./contents/network/grpc-vs-rest.md)
11. [TCP Congestion Control](./contents/network/tcp-congestion-control.md)
12. [Service Mesh와 Sidecar Proxy](./contents/network/service-mesh-sidecar-proxy.md)
13. [HTTP/2 Multiplexing과 HOL Blocking](./contents/network/http2-multiplexing-hol-blocking.md)
14. [Connect / Read / Write Timeout](./contents/network/timeout-types-connect-read-write.md)
15. [Load Balancer Healthcheck Failure Patterns](./contents/network/load-balancer-healthcheck-failure-patterns.md)
16. [HTTP/3와 QUIC 실전 트레이드오프](./contents/network/http3-quic-practical-tradeoffs.md)
17. [CDN 캐시 키와 무효화 전략](./contents/network/cdn-cache-key-invalidation.md)
18. [WebSocket heartbeat, backpressure, reconnect](./contents/network/websocket-heartbeat-backpressure-reconnect.md)
19. [DNS TTL과 캐시 실패 패턴](./contents/network/dns-ttl-cache-failure-patterns.md)
20. [NAT, Conntrack, Ephemeral Port Exhaustion](./contents/network/nat-conntrack-ephemeral-port-exhaustion.md)
21. [Forwarded, X-Forwarded-For, X-Real-IP 신뢰 경계](./contents/network/forwarded-x-forwarded-for-x-real-ip-trust-boundary.md)
이 단계에서 목표:

- 왜 어떤 요청은 재시도해도 되고 어떤 요청은 위험한지 설명할 수 있다.
- 세션/JWT/캐시를 각각 언제 선택할지 설명할 수 있다.
- reverse proxy, load balancer, CDN이 시스템에서 어떤 위치를 차지하는지 말할 수 있다.
- SSE / WebSocket / Polling 중 어떤 실시간 전송 모델을 고를지 비교할 수 있다.
- timeout / retry / backoff 전략의 실전 trade-off를 설명할 수 있다.
- API gateway, circuit breaker, keep-alive를 운영 관점으로 설명할 수 있다.
- REST와 gRPC를 브라우저, 모바일, 백엔드 간 통신 맥락에서 비교할 수 있다.
- 혼잡 제어와 서비스 메시가 지연 시간, 운영 복잡도에 어떤 영향을 주는지 설명할 수 있다.
- QUIC, timeout 종류, CDN 캐시 키, WebSocket heartbeat, DNS TTL이 실제 장애와 지연에 어떤 영향을 주는지 설명할 수 있다.
- HTTP/2 HOL blocking, timeout 종류, healthcheck 실패가 실제 장애 패턴으로 어떻게 이어지는지 설명할 수 있다.
- NAT, conntrack, ephemeral port exhaustion이 외부 API 호출 폭증과 retry storm에서 어떻게 드러나는지 설명할 수 있다.
- reverse proxy 체인에서 forwarded header를 어디까지 신뢰해야 하는지와 spoofing 위험을 설명할 수 있다.

## 3단계. 자바를 런타임과 동시성 관점으로 확장

추천 순서:

1. [JVM, GC, JMM](./contents/language/java/4.md)
2. [Java 동시성 유틸리티](./contents/language/java/5.md)
3. [Virtual Threads(Project Loom)](./contents/language/java/virtual-threads-project-loom.md)
4. [ClassLoader, Exception 설계, equals/hashCode/compareTo](./contents/language/java/6.md)
5. [Reflection, Generics, Annotations](./contents/language/java/reflection-generics-annotations.md)
6. [Annotation Processing](./contents/language/java/annotation-processing.md)
7. [Collections 성능 감각](./contents/language/java/collections-performance.md)
8. [IO/NIO + Serialization/JSON Mapping](./contents/language/java/io-nio-serialization.md)
9. [Optional / Stream / 불변 컬렉션 / 메모리 누수 패턴](./contents/language/java/7.md)
10. [G1 GC vs ZGC](./contents/language/java/g1-vs-zgc.md)
11. [Reflection 비용과 대안](./contents/language/java/reflection-cost-and-alternatives.md)
12. [제네릭 타입 소거와 우회 패턴](./contents/language/java/generic-type-erasure-workarounds.md)
13. [JIT Warmup과 Deoptimization](./contents/language/java/jit-warmup-deoptimization.md)
14. [OOM Heap Dump Playbook](./contents/language/java/oom-heap-dump-playbook.md)
15. [ClassLoader Memory Leak Playbook](./contents/language/java/classloader-memory-leak-playbook.md)
16. [JFR, JMC Performance Playbook](./contents/language/java/jfr-jmc-performance-playbook.md)
17. [Records, Sealed Classes, Pattern Matching](./contents/language/java/records-sealed-pattern-matching.md)
18. [VarHandle, Unsafe, Atomics](./contents/language/java/varhandle-unsafe-atomics.md)
19. [Direct Buffer, Off-Heap, Native Memory Troubleshooting](./contents/language/java/direct-buffer-offheap-memory-troubleshooting.md)
20. [Java Memory Model, happens-before, volatile, final](./contents/language/java-memory-model-happens-before-volatile-final.md)
21. [equals, hashCode, Comparable 계약](./contents/language/java-equals-hashcode-comparable-contracts.md)
이 단계에서 목표:

- 메모리/가시성/스레드 문제를 코드 수준에서 설명할 수 있다.
- `ExecutorService`, `Future`, `CompletableFuture` 선택 기준을 말할 수 있다.
- Virtual Threads가 기존 thread-per-request 모델을 어디까지 단순화하고 어디서 핀닝/디버깅 문제가 생기는지 설명할 수 있다.
- 자바 언어 요소가 프레임워크와 어떻게 연결되는지 이해한다.
- 컬렉션 선택이 성능과 복잡도에 어떤 차이를 만드는지 설명할 수 있다.
- 직렬화, JSON 매핑, NIO/IO 선택 감각을 말할 수 있다.
- Optional/Stream을 코드 가독성과 오버헤드 관점에서 비판적으로 설명할 수 있다.
- GC 선택과 reflection 대안이 지연 시간과 프레임워크 비용에 어떤 차이를 만드는지 설명할 수 있다.
- JIT, ClassLoader leak, OOM dump, VarHandle 같은 JVM 실전 문제를 성능/장애 대응 관점에서 설명할 수 있다.
- 타입 소거, JIT, 힙 덤프 분석 같은 JVM 내부 이슈를 장애 대응과 연결해 설명할 수 있다.
- direct buffer, mmap, off-heap native memory 문제를 heap/RSS/cgroup 관점으로 구분해서 설명할 수 있다.
- happens-before, `volatile`, `final` publication을 실전 concurrency 버그와 연결해 설명할 수 있다.
- `equals`/`hashCode`/`Comparable` 계약이 컬렉션과 정렬, 중복 제거에 어떤 버그를 만드는지 설명할 수 있다.

## 4단계. 운영체제를 서버 모델과 연결

추천 순서:

1. [리눅스 프로세스 상태 머신, Zombie, Orphan](./contents/operating-system/linux-process-state-zombie-orphan.md)
2. [컨텍스트 스위칭, 데드락, lock-free](./contents/operating-system/context-switching-deadlock-lockfree.md)
3. [I/O 모델과 이벤트 루프](./contents/operating-system/io-models-and-event-loop.md)
4. [CPU 캐시, 코히어런시, 메모리 배리어](./contents/operating-system/cpu-cache-coherence-memory-barrier.md)
5. [스케줄러 공정성, page cache, 파일 시스템 기초](./contents/operating-system/scheduler-fairness-page-cache.md)
6. [시스템 콜과 User-Kernel Boundary](./contents/operating-system/syscall-user-kernel-boundary.md)
7. [NUMA, page replacement, thrashing](./contents/operating-system/memory-management-numa-page-replacement-thrashing.md)
8. [file descriptor, socket, syscall cost](./contents/operating-system/file-descriptor-socket-syscall-cost-server-impact.md)
9. [epoll, kqueue, io_uring](./contents/operating-system/epoll-kqueue-io-uring.md)
10. [컨테이너의 cgroup과 namespace](./contents/operating-system/container-cgroup-namespace.md)
11. [False Sharing과 Cache Line](./contents/operating-system/false-sharing-cache-line.md)
12. [Futex, Mutex, Semaphore, Spinlock](./contents/operating-system/futex-mutex-semaphore-spinlock.md)
13. [Page Replacement: Clock vs LRU](./contents/operating-system/page-replacement-clock-vs-lru.md)
14. [Run Queue, Load Average, CPU Saturation](./contents/operating-system/run-queue-load-average-cpu-saturation.md)
15. [Page Cache, Dirty Writeback, fsync](./contents/operating-system/page-cache-dirty-writeback-fsync.md)
16. [NUMA Production Debugging](./contents/operating-system/numa-production-debugging.md)
17. [Signals, Process Supervision](./contents/operating-system/signals-process-supervision.md)
18. [eBPF, perf, strace, and Production Tracing](./contents/operating-system/ebpf-perf-strace-production-tracing.md)
19. [Monotonic Clock, Wall Clock, Timeout and Deadline](./contents/operating-system/monotonic-clock-wall-clock-timeout-deadline.md)

이 단계에서 목표:

- 스레드 수가 많아지면 왜 무조건 좋은 게 아닌지 설명할 수 있다.
- zombie/orphan 프로세스와 container의 PID 1 문제가 운영 이슈로 어떻게 이어지는지 설명할 수 있다.
- blocking I/O와 event loop 모델의 차이를 시스템 관점으로 말할 수 있다.
- CPU cache coherence와 memory barrier가 왜 JMM 이야기와 연결되는지 설명할 수 있다.
- user space / kernel space 경계에서 비용이 왜 생기는지 설명할 수 있다.
- NUMA와 page cache, file descriptor 한계가 서버 성능에 어떤 영향을 주는지 설명할 수 있다.
- io_uring 같은 최신 I/O 모델과 container 격리 메커니즘을 서버 운영 현실과 연결해 설명할 수 있다.
- false sharing, futex 계열 락, 페이지 교체 정책이 실제 지연 시간과 CPU 사용률에 어떤 영향을 주는지 설명할 수 있다.
- run queue, dirty writeback, signal supervision 같은 운영 지표를 애플리케이션 지연과 연결해 설명할 수 있다.
- strace, perf, eBPF를 각각 언제 써야 하는지와 off-CPU 문제를 어떻게 추적하는지 설명할 수 있다.
- monotonic clock과 wall clock을 timeout, deadline, retry scheduler, deadline propagation 관점으로 설명할 수 있다.

## 5단계. Spring을 내부 동작 관점으로 확장

추천 순서:

1. [Spring Framework](./contents/spring/README.md)
2. [IoC 컨테이너와 DI](./contents/spring/ioc-di-container.md)
3. [AOP와 프록시 메커니즘](./contents/spring/aop-proxy-mechanism.md)
4. [@Transactional 깊이 파기](./contents/spring/transactional-deep-dive.md)
5. [Spring MVC 요청 생명주기](./contents/spring/spring-mvc-request-lifecycle.md)
6. [Spring Boot 자동 구성](./contents/spring/spring-boot-autoconfiguration.md)
7. [Spring Security 아키텍처](./contents/spring/spring-security-architecture.md)
8. [Spring MVC vs WebFlux](./contents/spring/spring-webflux-vs-mvc.md)
9. [Bean 생명주기와 스코프 함정](./contents/spring/spring-bean-lifecycle-scope-traps.md)
10. [Spring OAuth2 + JWT 통합](./contents/spring/spring-oauth2-jwt-integration.md)
11. [Spring Test Slice와 Context Caching](./contents/spring/spring-test-slices-context-caching.md)
12. [Spring Cache Abstraction 함정](./contents/spring/spring-cache-abstraction-traps.md)
13. [Spring Transaction Debugging Playbook](./contents/spring/spring-transaction-debugging-playbook.md)
14. [Spring Scheduler와 Async 경계](./contents/spring/spring-scheduler-async-boundaries.md)
15. [Spring Batch chunk, retry, skip](./contents/spring/spring-batch-chunk-retry-skip.md)
16. [Spring Observability, Micrometer, Tracing](./contents/spring/spring-observability-micrometer-tracing.md)
17. [Spring WebClient vs RestTemplate](./contents/spring/spring-webclient-vs-resttemplate.md)
18. [Spring Resilience4j: Retry, CircuitBreaker, Bulkhead](./contents/spring/spring-resilience4j-retry-circuit-breaker-bulkhead.md)
19. [Spring EventListener, TransactionalEventListener, Outbox](./contents/spring/spring-eventlistener-transaction-phase-outbox.md)

이 단계에서 목표:

- Spring이 내부적으로 프록시, 빈 생명주기, 조건부 자동 구성으로 동작한다는 점을 설명할 수 있다.
- `@Transactional`, `@Async`, `@Cacheable` 같은 어노테이션이 어디까지 프레임워크 마법이고 어디부터 제약인지 설명할 수 있다.
- MVC 요청 흐름과 Security 필터 체인을 디버깅 포인트까지 포함해 설명할 수 있다.
- Boot 자동 구성과 커스텀 설정의 경계를 판단할 수 있다.
- thread-per-request 모델과 reactive/event-loop 모델을 각각 언제 선택할지 설명할 수 있다.
- Bean scope/proxy 타이밍과 OAuth2 로그인 후 JWT 발급 경계를 코드 수준에서 설명할 수 있다.
- 테스트 컨텍스트, 캐시 추상화, 트랜잭션 디버깅까지 포함해 Spring 문제를 운영 관점으로 추적할 수 있다.
- scheduler, batch, observability, client 선택까지 포함해 Spring 생태계를 운영 관점으로 설명할 수 있다.
- retry storm, circuit breaker, bulkhead, fallback를 Spring Boot 코드와 관측성 관점으로 조합해 설명할 수 있다.
- `@EventListener`, `@TransactionalEventListener`, Outbox를 트랜잭션 phase와 정합성 경계 기준으로 구분할 수 있다.

## 6단계. 보안과 인증을 운영 관점으로 확장

추천 순서:

1. [Security](./contents/security/README.md)
2. [인증과 인가의 차이](./contents/security/authentication-vs-authorization.md)
3. [JWT 깊이 파기](./contents/security/jwt-deep-dive.md)
4. [OAuth2 Authorization Code Grant](./contents/security/oauth2-authorization-code-grant.md)
5. [Spring Security 아키텍처](./contents/spring/spring-security-architecture.md)
6. [Spring OAuth2 + JWT 통합](./contents/spring/spring-oauth2-jwt-integration.md)
7. [HTTP의 무상태성과 쿠키, 세션, 캐시](./contents/network/http-state-session-cache.md)
8. [TLS, 로드밸런싱, 프록시](./contents/network/tls-loadbalancing-proxy.md)
9. [비밀번호 저장: bcrypt / scrypt / argon2](./contents/security/password-storage-bcrypt-scrypt-argon2.md)
10. [SQL Injection beyond PreparedStatement](./contents/security/sql-injection-beyond-preparedstatement.md)
11. [XSS / CSRF / Spring Security](./contents/security/xss-csrf-spring-security.md)
12. [HTTPS / HSTS / MITM](./contents/security/https-hsts-mitm.md)
13. [CORS / SameSite / Preflight](./contents/security/cors-samesite-preflight.md)
14. [OIDC, ID Token, UserInfo 경계](./contents/security/oidc-id-token-userinfo-boundaries.md)
15. [Secret Rotation / Leak Patterns](./contents/security/secret-management-rotation-leak-patterns.md)
16. [Session Fixation / Clickjacking / CSP](./contents/security/session-fixation-clickjacking-csp.md)
17. [Service-to-Service Auth: mTLS, JWT, SPIFFE](./contents/security/service-to-service-auth-mtls-jwt-spiffe.md)
18. [API Key, HMAC Signature, Replay Protection](./contents/security/api-key-hmac-signature-replay-protection.md)

이 단계에서 목표:

- 인증(Authentication)과 인가(Authorization)를 분리해서 설명할 수 있다.
- 세션, JWT, OAuth2가 각각 어떤 책임을 가지는지 설명할 수 있다.
- stateless 인증이 실제 운영에서 왜 완전히 stateless가 되기 어려운지 설명할 수 있다.
- 보안 기능을 애플리케이션 코드만의 문제가 아니라 네트워크, 프록시, 필터 체인과 연결해서 볼 수 있다.
- Refresh Token, PKCE, 토큰 탈취 대응 같은 세부 운영 포인트를 설명할 수 있다.
- 인증/인가 외에도 비밀번호 저장, 인젝션, XSS/CSRF, HTTPS 위생이 왜 별도 축으로 중요한지 설명할 수 있다.
- OIDC, CORS/SameSite, secret rotation, session fixation 같은 브라우저/운영 경계 이슈를 별도 축으로 설명할 수 있다.
- 서비스 간 인증에서 mTLS, JWT, SPIFFE/SPIRE를 각각 어떤 책임으로 나눠야 하는지 설명할 수 있다.
- API key와 HMAC signed request를 nonce/timestamp/replay protection 관점으로 비교할 수 있다.

## 7단계. 설계를 아키텍처와 운영 관점으로 확장

추천 순서:

1. [SOLID Failure Patterns](./contents/software-engineering/solid-failure-patterns.md)
2. [DDD Bounded Context Failure Patterns](./contents/software-engineering/ddd-bounded-context-failure-patterns.md)
3. [Monolith → MSA Failure Patterns](./contents/software-engineering/monolith-to-msa-failure-patterns.md)
4. [Repository, DAO, Entity](./contents/software-engineering/repository-dao-entity.md)
5. [API 설계와 예외 처리](./contents/software-engineering/api-design-error-handling.md)
6. [테스트 전략과 테스트 더블](./contents/software-engineering/testing-strategy-and-test-doubles.md)
7. [캐시, 메시징, 관측성](./contents/software-engineering/cache-message-observability.md)
8. [DDD, Hexagonal Architecture, Consistency Boundary](./contents/software-engineering/ddd-hexagonal-consistency.md)
9. [Domain Event, Outbox, Inbox](./contents/software-engineering/outbox-inbox-domain-events.md)
10. [Clean Architecture, Layered, Modular Monolith](./contents/software-engineering/clean-architecture-layered-modular-monolith.md)
11. [Feature Flags, Rollout, Dependency Management](./contents/software-engineering/feature-flags-rollout-dependency-management.md)
12. [Deployment, Rollout, Rollback, Canary, Blue-Green](./contents/software-engineering/deployment-rollout-rollback-canary-blue-green.md)
13. [API Versioning, Contract Testing, Anti-Corruption Layer](./contents/software-engineering/api-versioning-contract-testing-anti-corruption-layer.md)
14. [Event Sourcing와 CQRS 도입 기준](./contents/software-engineering/event-sourcing-cqrs-adoption-criteria.md)
15. [기술 부채와 리팩토링 타이밍](./contents/software-engineering/technical-debt-refactoring-timing.md)
16. [Anti-Corruption Layer 통합 패턴](./contents/software-engineering/anti-corruption-layer-integration-patterns.md)
17. [API Contract Testing, Consumer-Driven](./contents/software-engineering/api-contract-testing-consumer-driven.md)
18. [Modular Monolith Boundary Enforcement](./contents/software-engineering/modular-monolith-boundary-enforcement.md)
19. [Feature Flag Cleanup and Expiration](./contents/software-engineering/feature-flag-cleanup-expiration.md)
20. [Idempotency, Retry, Consistency Boundaries](./contents/software-engineering/idempotency-retry-consistency-boundaries.md)
21. [Strangler Fig Migration, Contract, Cutover](./contents/software-engineering/strangler-fig-migration-contract-cutover.md)
22. [Branch by Abstraction, Feature Flag, Strangler Fig](./contents/software-engineering/branch-by-abstraction-vs-feature-flag-vs-strangler.md)

이 단계에서 목표:

- 계층 분리가 왜 필요한지 설명할 수 있다.
- 예외, 테스트, 캐시, 메시징을 설계 관점으로 설명할 수 있다.
- SOLID를 “좋은 원칙”이 아니라 깨졌을 때 어떤 냄새와 장애로 이어지는지 설명할 수 있다.
- 바운디드 컨텍스트 분리 실패와 무리한 MSA 전환이 어떤 운영 문제를 만드는지 설명할 수 있다.
- 아키텍처를 위한 아키텍처가 되는 순간을 구분할 수 있다.
- 이벤트 기반 확장과 eventually consistent 설계를 설명할 수 있다.
- clean architecture, layered, modular monolith의 차이와 선택 기준을 설명할 수 있다.
- API versioning, contract testing, rollout 전략을 운영 관점으로 설명할 수 있다.
- CQRS/Event Sourcing, 기술 부채, ACL 같은 확장 전략을 언제 쓰고 언제 참아야 하는지 판단할 수 있다.
- contract testing, modular monolith, feature flag cleanup, idempotency boundary를 구조적 설계 문제로 설명할 수 있다.
- strangler fig migration, shadow traffic, dual write, rollback 경로를 점진 전환 전략으로 설명할 수 있다.
- branch by abstraction, feature flag, strangler fig를 코드/기능/시스템 레벨의 전환 도구로 구분할 수 있다.

## 8단계. 시스템 설계로 확장

추천 순서:

1. [System Design](./contents/system-design/README.md)
2. [시스템 설계 면접 프레임워크](./contents/system-design/system-design-framework.md)
3. [Back-of-Envelope 추정법](./contents/system-design/back-of-envelope-estimation.md)
4. [URL 단축기 설계](./contents/system-design/url-shortener-design.md)
5. [Rate Limiter 설계](./contents/system-design/rate-limiter-design.md)
6. [분산 캐시 설계](./contents/system-design/distributed-cache-design.md)
7. [채팅 시스템 설계](./contents/system-design/chat-system-design.md)
8. [뉴스피드 시스템 설계](./contents/system-design/newsfeed-system-design.md)
9. [알림 시스템 설계](./contents/system-design/notification-system-design.md)
10. [Consistent Hashing과 Hot Key 전략](./contents/system-design/consistent-hashing-hot-key-strategies.md)
11. [Distributed Lock 설계](./contents/system-design/distributed-lock-design.md)
12. [Search 시스템 설계](./contents/system-design/search-system-design.md)
13. [File Storage / Presigned URL / CDN](./contents/system-design/file-storage-presigned-url-cdn-design.md)
14. [Workflow Orchestration / Saga](./contents/system-design/workflow-orchestration-saga-design.md)
15. [멀티 테넌트 SaaS 격리 설계](./contents/system-design/multi-tenant-saas-isolation-design.md)
16. [Payment System, Ledger, Idempotency, Reconciliation](./contents/system-design/payment-system-ledger-idempotency-reconciliation-design.md)

이 단계에서 목표:

- 요구사항을 기능 목록이 아니라 QPS, 저장 용량, 지연 시간, 일관성 요구로 번역할 수 있다.
- 고수준 설계를 그리고 나서 병목과 단일 장애점을 스스로 검토할 수 있다.
- 추정값과 trade-off를 근거로 설계 선택을 설명할 수 있다.
- Edge와 애플리케이션 레벨의 Rate Limiting을 어떤 기준으로 배치할지 설명할 수 있다.
- 캐시 무효화와 메시지 순서/오프라인 전달 같은 분산 시스템 난제를 설계 관점으로 설명할 수 있다.
- feed, notification, hot key 분산 같은 대규모 시스템 설계 패턴을 실제 서비스 문맥으로 설명할 수 있다.
- distributed lock, search, file storage, workflow orchestration을 별도 시스템 설계 문제로 설명할 수 있다.
- 멀티 테넌트 격리를 앱, DB, 캐시, 큐, authz 계층으로 나눠 설계할 수 있다.
- payment auth/capture/refund와 ledger/reconciliation/idempotency를 정합성 설계 관점으로 설명할 수 있다.

## 9단계. 디자인 패턴을 비판적으로 보기

추천 순서:

1. [Strategy](./contents/design-pattern/strategy-pattern.md)
2. [Decorator vs Proxy](./contents/design-pattern/decorator-vs-proxy.md)
3. [Builder](./contents/design-pattern/builder-pattern.md)
4. [Factory](./contents/design-pattern/factory.md)
5. [Template Method](./contents/design-pattern/template-method.md)
6. [Pattern Selection Guide](./contents/design-pattern/pattern-selection.md)
7. [안티 패턴](./contents/design-pattern/anti-pattern.md)
8. [Observer / Pub-Sub / Application Event](./contents/design-pattern/observer-pubsub-application-events.md)
9. [Template Method vs Strategy](./contents/design-pattern/template-method-vs-strategy.md)
10. [God Object / Spaghetti / Golden Hammer](./contents/design-pattern/god-object-spaghetti-golden-hammer.md)
11. [Facade vs Adapter vs Proxy](./contents/design-pattern/facade-vs-adapter-vs-proxy.md)
12. [Factory vs Abstract Factory vs Builder](./contents/design-pattern/factory-vs-abstract-factory-vs-builder.md)
13. [Composition over Inheritance](./contents/design-pattern/composition-over-inheritance-practical.md)
14. [Command Pattern, Undo, Queue](./contents/design-pattern/command-pattern-undo-queue.md)

이 단계에서 목표:

- “패턴을 썼다”와 “문제를 해결했다”를 구분할 수 있다.
- 전략/템플릿 메소드/컴포지션 선택 기준을 설명할 수 있다.
- 데코레이터, 프록시, 퍼사드의 차이를 실전적으로 비교할 수 있다.
- Builder와 정적 팩토리, Lombok 같은 도구성 추상화를 구분해서 설명할 수 있다.
- 패턴 과사용이 어떤 문제를 만드는지 설명할 수 있다.
- 이벤트 패턴과 안티패턴을 함께 보고, 구조적 냄새를 패턴 언어로 설명할 수 있다.
- facade/adapter/proxy, abstract factory/builder, command/composition 관점까지 비교할 수 있다.

## 10단계. 시니어 질문으로 검증

마지막에는 반드시 아래 문서로 검증한다.

- [Senior-Level CS Questions](./SENIOR-QUESTIONS.md)
- [System Design](./contents/system-design/README.md)
- [RAG Ready Checklist](./RAG-READY.md)

## 교차 관점 디버깅 경로

- `JWT / OIDC 문제` : [Security](./contents/security/README.md) → [Spring](./contents/spring/README.md) → [Network](./contents/network/README.md)
- `지연 시간 / p99 문제` : [Network](./contents/network/README.md) → [Operating System](./contents/operating-system/README.md) → [Database](./contents/database/README.md)
- `캐시 정합성 문제` : [System Design](./contents/system-design/README.md) → [Software Engineering](./contents/software-engineering/README.md) → [Database](./contents/database/README.md)
- `OOM / JVM 이상` : [Language](./contents/language/README.md) → [Spring](./contents/spring/README.md) → [Operating System](./contents/operating-system/README.md)
- `외부 API timeout / NAT 문제` : [Network](./contents/network/README.md) → [Operating System](./contents/operating-system/README.md) → [Spring](./contents/spring/README.md)
- `Native memory / RSS 문제` : [Language](./contents/language/README.md) → [Operating System](./contents/operating-system/README.md) → [Network](./contents/network/README.md)
- `서비스 간 인증 / zero-trust 문제` : [Security](./contents/security/README.md) → [Network](./contents/network/README.md) → [Spring](./contents/spring/README.md)
- `점진 전환 / cutover 문제` : [Software Engineering](./contents/software-engineering/README.md) → [Database](./contents/database/README.md) → [System Design](./contents/system-design/README.md)
- `결제 / 정산 / reconciliation 문제` : [System Design](./contents/system-design/README.md) → [Database](./contents/database/README.md) → [Security](./contents/security/README.md)

기준:

- 정의만 답하면 실패
- 실제 사례가 있어야 함
- 대안 비교가 있어야 함
- 트레이드오프를 말할 수 있어야 함
- 숫자와 운영 포인트가 있어야 함

## 추천 공부 방식

### 방식 A. 문서 중심

1. 문서 읽기
2. 핵심 요약 5줄 작성
3. 실전 예시 1개 붙이기
4. 시니어 질문 2개 답해보기
5. [RAG Query Playbook](./rag/query-playbook.md) 기준으로 검색 질문 2개 만들어보기
6. [Cross-Domain Bridge Map](./rag/cross-domain-bridge-map.md)으로 보조 도메인 1개 붙여보기

### 방식 B. 코드 중심

1. 실제 코드/프로젝트 보기
2. “여기서 필요한 CS가 뭐지?” 질문하기
3. 문서에서 해당 개념 찾기
4. 다시 코드로 돌아와 설명하기
5. [Topic Map](./rag/topic-map.md)으로 연관 카테고리까지 추적하기
6. [Question Decomposition Examples](./rag/question-decomposition-examples.md)로 질문을 더 잘게 쪼개보기

## 마지막 기준

이 문서를 다 돌고 나면 최소한 아래 질문에는 답할 수 있어야 한다.

- 왜 이 기술을 선택했는가?
- 어떤 대안이 있었는가?
- 장애가 났을 때 어디부터 볼 것인가?
- 이 설계는 언제까지 유효한가?

이 수준까지 가야 시니어 질문에도 버틸 수 있다.
