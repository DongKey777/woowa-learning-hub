# Cross-Domain Bridge Map

> 한 줄 요약: 질문이 한 영역만 건드리지 않을 때, 어떤 카테고리를 먼저 읽고 어떤 문서를 같이 묶어야 하는지 정리한 교차 연결 지도다.

> 관련 문서:
> - [Query Playbook](./query-playbook.md)
> - [Master Notes Index](../master-notes/README.md)
> - [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)

> retrieval-anchor-keywords: cross domain bridge map, category bridge, freshness cluster, stale read cluster, read-after-write cluster, projection lag cluster, database system design bridge, database + system design route, database spring transaction bridge, database + spring route, transaction isolation to @Transactional route, rollback not working route, REQUIRES_NEW beginner route, rollback-only beginner route, readOnly beginner route, routing datasource confusion, inner readOnly writer pool, partial commit beginner, transactional not applied route, self invocation route, checked exception commit route, database + system design route, design pattern read model bridge, design pattern / read model + database + system design route, client disconnect cluster, disconnect cluster, spring network bridge, spring + network route, 499 cluster, broken pipe cluster, 502 route, 504 route, bad gateway route, gateway timeout route, local reply route, timeout mismatch route, async timeout mismatch route, idle timeout mismatch route, deadline budget mismatch route, spring security route, spring + security route, oidc back-channel spring route, oauth2 login session mapping route, saved request route, post-login session persistence route, auth incident cluster, jwks outage cluster, auth verification cluster, revoke lag cluster, revocation tail route, logout but still works route, stale authz cache cluster, stale deny route, 403 after revoke route, revoked admin still has access route, security system design bridge, security + system design route, database security identity bridge, database security system design route, database + security + system design route, authority transfer route, scim deprovision route, scim disable but still access route, decision parity route, migration replay cutover, timeout disconnect bridge, auth failover routing, related docs navigator, stale read route, read-after-write bridge, projection lag route, old data after write route, 499 route, broken pipe route, client disconnect route, client closed request route, jwks outage route, kid miss route, unable to find JWK route, auth verification outage, auth shadow evaluation route, backfill verification route, access tail remains route, backfill green route, shadow read green auth decision diverges, cleanup evidence route, retirement evidence route, decision log join key route, audit evidence bundle route, http stateless route, cookie session jwt bridge, beginner auth bridge, browser auth primer route, session basics to spring security, why login state is kept, hidden jsessionid route, session creation policy basics, cookie session spring security route, login loop beginner bridge, savedrequest beginner route, hidden session troubleshooting starter, incident recovery trust handoff, browser session troubleshooting path handoff, session boundary replay handoff, identity delegation lifecycle handoff, security / system-design incident bridge, auth session troubleshooting bridge, database / security authority bridge, verification / shadowing / authority bridge, system design handoff cue, control plane handoff cue, cutover handoff cue, canonical revocation plane route, cookie 있는데 다시 로그인

## 목적

`CS-study`의 질문은 자주 한 분야에만 머물지 않는다.
예를 들어 `Spring` 질문처럼 보여도 실제로는 `Java`, `OS`, `Network`, `Security`까지 함께 봐야 답이 안정적이다.

이 문서는 그런 교차 질문을 빠르게 분해하기 위한 지도다.

## 브리지 규칙

1. 질문의 **주 도메인**을 먼저 정한다.
2. 그 다음 **보조 도메인**을 1~2개 붙인다.
3. 정의는 주 도메인 문서에서, 원리는 보조 도메인 문서에서 찾는다.
4. 운영/장애 질문이면 `SENIOR-QUESTIONS.md`를 같이 붙인다.

## 증상형 바로가기

- `stale read`, `read-after-write`, `old data after write`, `방금 썼는데 조회가 옛값`, `projection lag`처럼 freshness symptom으로 시작하면 [Replica Freshness Master Note](../master-notes/replica-freshness-master-note.md)로 예산을 먼저 잡고, [Freshness / Stale Read / Read-After-Write](#bridge-freshness-cluster) route로 내려간다.
- `dirty read`, `lost update`, `write skew`, `phantom`, `@Transactional`, `왜 안 롤백되지`, `왜 private method에서는 안 먹지`, `self invocation`, `checked exception commit`, `REQUIRES_NEW`, `rollback-only`, `readOnly`, `read/write split`처럼 DB anomaly와 Spring 경계가 섞이면 [Database to Spring Transaction Master Note](../master-notes/database-to-spring-transaction-master-note.md)와 [Transaction Isolation / @Transactional / Rollback Debugging](#bridge-database-spring-transaction-cluster) route를 같이 본다.
- `499`, `broken pipe`, `client disconnect`, `client closed request`, `connection reset`, `proxy timeout인지 spring bug인지`처럼 종료 지점이 모호하면 [Network Failure Handling Master Note](../master-notes/network-failure-handling-master-note.md)와 [Client Disconnect / 499 / Broken Pipe](#bridge-disconnect-cluster) route를 같이 본다.
- `502`, `504`, `bad gateway`, `gateway timeout`, `local reply인지 app 에러인지`처럼 edge status owner가 먼저 헷갈리면 [Edge Request Lifecycle Master Note](../master-notes/edge-request-lifecycle-master-note.md)와 [Edge 502 / 504 / Timeout Mismatch](#bridge-edge-timeout-cluster) route를 같이 본다.
- `timeout mismatch`, `async timeout mismatch`, `idle timeout mismatch`, `deadline budget mismatch`, `gateway는 504인데 app은 200`처럼 종료 순서가 흔들리면 [Retry, Timeout, Idempotency Master Note](../master-notes/retry-timeout-idempotency-master-note.md)와 [Edge 502 / 504 / Timeout Mismatch](#bridge-edge-timeout-cluster) route를 같이 본다.
- `HTTP stateless`, `cookie`, `session`, `JWT`, `왜 로그인 상태가 유지되나`, `Spring Security는 어디서 세션을 쓰나`, `hidden JSESSIONID`처럼 기초 개념에서 Spring 경계로 올라가려면 [HTTP Stateless / Cookie / Session / Spring Security](#bridge-http-session-security-cluster) route를 먼저 탄다.
- `SavedRequest`, `saved request bounce`, `browser 401 -> 302 /login bounce`, `hidden session`, `hidden JSESSIONID`, `cookie exists but session missing`, `cookie 있는데 다시 로그인`이 먼저 보이지만 아직 `cookie`와 `session` 차이부터 다시 잡아야 한다면 위 beginner auth bridge를 먼저 탄 뒤 [Spring + Security](#spring--security) route로 넘어간다.
- `JWKS outage`, `kid miss`, `unable to find jwk`, `unable to find JWK`, `auth verification outage`처럼 인증 장애 문장으로 들어오면 [Auth, Session, Token Master Note](../master-notes/auth-session-token-master-note.md)로 auth state를 먼저 잡고, [Auth Incident / JWKS Outage / Auth Verification](#bridge-auth-incident-cluster) route로 failover 레버를 붙인다.
- `logout but still works`, `allowed after revoke`, `revoked admin still has access`, `revocation tail`, `revoke lag`처럼 revoke propagation tail이 먼저 보이면 [Authz and Permission Master Note](../master-notes/authz-and-permission-master-note.md)로 revoke 의미를 먼저 고정하고, [Revoke Lag / Stale AuthZ Cache / 403 After Revoke](#bridge-revoke-authz-cluster) route로 내려간다.
- `stale authz cache`, `stale deny`, `grant but still denied`, `tenant-specific 403`, `403 after revoke`, `cached 404 after grant`처럼 deny/cache drift가 먼저 보이면 역시 [Authz and Permission Master Note](../master-notes/authz-and-permission-master-note.md)를 대표 진입점으로 잡고, 필요하면 [Auth Failure Response Contracts: `401` / `403` / `404`](../contents/security/auth-failure-response-401-403-404.md)를 붙인 뒤 [Revoke Lag / Stale AuthZ Cache / 403 After Revoke](#bridge-revoke-authz-cluster) route로 내려간다.
- `logout token은 오는데 spring 앱 세션을 못 찾는다`, `SavedRequest 때문에 login loop가 난다`, `oauth2Login 이후 어떤 상태를 저장했는지 헷갈린다`, `sid mapping`, `post-login session persistence`처럼 login redirect와 federated logout이 섞이면 [Spring + Security](#spring--security) route를 같이 본다.
- `backfill은 green인데 access tail이 남는다`, `backfill is green but access tail remains`, `SCIM deprovision 뒤에도 권한이 남는다`, `SCIM disable but still access`, `shadow read는 green인데 auth decision이 갈린다`, `decision parity`, `auth shadow divergence`, `authority transfer`처럼 data parity와 decision parity가 섞이면 [Migration Cutover Master Note](../master-notes/migration-cutover-master-note.md)로 승격 단계를 먼저 잡고, [Authority Transfer / SCIM Deprovision / Decision Parity](#bridge-authority-transfer-cluster) route로 내려간다.

## 이번 wave에서 먼저 붙여 볼 브리지

아래 subsection title은 [Topic Map](./topic-map.md)의 symptom alias cluster 이름을 그대로 드러내서, 표 라벨과 bridge example이 같은 어휘로 만나게 맞춘다.

- `database ↔ system-design`: source-of-truth 변화와 운영 cutover를 함께 봐야 한다. `schema-migration-partitioning-cdc-cqrs.md`에서 출발해 `change-data-capture-outbox-relay-design.md`, `historical-backfill-replay-platform-design.md`, `dual-read-comparison-verification-platform-design.md` 순으로 읽으면 relay, replay, verification이 한 줄로 잡힌다.
- `transaction isolation / @Transactional / rollback debugging` (`database ↔ spring`): DB anomaly vocabulary와 Spring transaction surface를 같은 ladder로 봐야 한다. `transaction-isolation-locking.md` → `isolation-anomaly-cheat-sheet.md` → `database-to-spring-transaction-master-note.md` → `transactional-deep-dive.md` → `spring-service-layer-transaction-boundary-patterns.md` → `spring-transaction-debugging-playbook.md` 순으로 읽으면 anomaly, boundary placement, proxy/rollback debugging이 한 줄로 잡힌다.
- `authority transfer / SCIM deprovision / decision parity` (`database ↔ security ↔ system-design`): security README의 `Identity / Delegation / Lifecycle`에서 시작해 system-design handoff를 `Database / Security Authority Bridge` → `Verification / Shadowing / Authority Bridge`로 넘기는 authority transfer 질문이다. `scim-provisioning-security.md` → `scim-drift-reconciliation.md` → `online-backfill-verification-cutover-gates.md` → `authorization-runtime-signals-shadow-evaluation.md` → `database-security-identity-bridge-cutover-design.md` → `session-store-claim-version-cutover-design.md` → `authz-decision-logging-design.md` → `audit-logging-auth-authz-traceability.md` 순으로 읽으면 data parity, auth shadow, session/claim cleanup, retirement evidence가 한 줄로 잡히고, `backfill is green but access tail remains`, `cleanup evidence`, `retirement evidence`를 같은 ladder에서 분해할 수 있다.
- `freshness / stale read / read-after-write` (`design-pattern/read-model ↔ database/system-design`): read-model staleness를 패턴 언어로 이해한 뒤 DB watermark와 verification으로 내려가야 한다. `read-model-staleness-read-your-writes.md` → `projection-freshness-slo-pattern.md` → `incremental-summary-table-refresh-watermark.md` → `read-model-cutover-guardrails.md` → `dual-read-comparison-verification-platform-design.md` 순서가 가장 덜 흔들린다.
- `http stateless / cookie / session / spring security` (`network ↔ security ↔ spring`): browser가 무엇을 자동 전송하고, 서버가 무엇을 session으로 들고 있고, Spring이 어디서 인증 상태를 저장하는지 분리해서 올라가야 한다. `http-state-session-cache.md` → `signed-cookies-server-sessions-jwt-tradeoffs.md` → `spring-security-architecture.md` → `spring-securitycontextrepository-sessioncreationpolicy-boundaries.md` → `browser-bff-token-boundary-session-translation.md` 순서가 가장 안전하다.
- `client disconnect / 499 / broken pipe` (`spring ↔ network`): 같은 timeout/499 문제를 Spring surface와 proxy/network surface에서 번갈아 봐야 한다. `spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md` → `network-spring-request-lifecycle-timeout-disconnect-bridge.md` → `spring-webclient-connection-pool-timeout-tuning.md` → `timeout-budget-propagation-proxy-gateway-service-hop-chain.md` → `service-mesh-local-reply-timeout-reset-attribution.md`를 묶어 본다.
- `edge 502 / 504 / timeout mismatch` (`spring ↔ network`): 같은 edge 오류여도 local reply, upstream reset, hop budget mismatch를 분리해서 봐야 한다. `proxy-local-reply-vs-upstream-error-attribution.md` → `vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md` → `spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md` → `timeout-budget-propagation-proxy-gateway-service-hop-chain.md` → `idle-timeout-mismatch-lb-proxy-app.md` → `network-spring-request-lifecycle-timeout-disconnect-bridge.md`를 묶어 본다.
- `spring ↔ security`: `SavedRequest`는 login bounce UX, `SecurityContextRepository`는 post-login persistence, OIDC back-channel logout은 future revoke lookup이라는 점을 분리해야 하는 질문이다. `spring-security-requestcache-savedrequest-boundaries.md` → `spring-securitycontextrepository-sessioncreationpolicy-boundaries.md` → `spring-oauth2-jwt-integration.md` → `oidc-backchannel-logout-session-coherence.md` 순으로 읽으면 redirect, persisted auth, `sid` mapping, federated revoke가 한 줄로 잡힌다.
- `auth incident / JWKS outage / auth verification` (`security ↔ system-design`): security README의 `Incident / Recovery / Trust`에서 `[playbook]` → `[drill]` → `[incident matrix]` ladder를 먼저 맞춘 뒤 system-design handoff를 `Security / System-Design Incident Bridge`로 넘겨야 한다. `jwt-signature-verification-failure-playbook.md` → `jwt-jwks-outage-recovery-failover-drills.md` → `auth-incident-triage-blast-radius-recovery-matrix.md` → `service-discovery-health-routing-design.md` → `global-traffic-failover-control-plane-design.md` → `session-store-design-at-scale.md`로 이어 읽으면 verify error string, route-level 복구, state-level 복구가 같이 잡힌다.
- `revoke lag / stale authz cache / 403 after revoke` (`security ↔ system-design`): security README의 `Browser / Session Troubleshooting Path` → `Session / Boundary / Replay` → `AuthZ / Tenant / Response Contracts` handoff를 그대로 따라야 allow tail과 deny tail이 섞여도 덜 흔들린다. `session-revocation-at-scale.md` → `revocation-propagation-lag-debugging.md` → `authorization-caching-staleness.md` → `authz-cache-inconsistency-runtime-debugging.md` → `auth-failure-response-401-403-404.md` → `session-store-claim-version-cutover-design.md` → `canonical-revocation-plane-across-token-generations-design.md` → `revocation-bus-regional-lag-recovery-design.md` 순으로 읽으면 revoke propagation, response contract, claim-version cleanup, regional lag recovery가 한 줄로 잡힌다.

## 자주 쓰는 연결

| 주 도메인 | 같이 볼 도메인 | 우선 문서 |
|---|---|---|
| `spring` | `language/java`, `operating-system` | `spring/README.md`, `aop-proxy-mechanism.md`, `virtual-threads-project-loom.md` |
| `spring` | `security` | `spring/README.md`, `spring-security-requestcache-savedrequest-boundaries.md`, `spring-securitycontextrepository-sessioncreationpolicy-boundaries.md`, `spring-oauth2-jwt-integration.md`, `oidc-backchannel-logout-session-coherence.md` |
| `network` | `security`, `spring` | `network/http-state-session-cache.md`, `signed-cookies-server-sessions-jwt-tradeoffs.md`, `spring-security-architecture.md`, `spring-securitycontextrepository-sessioncreationpolicy-boundaries.md` |
| `security` | `network`, `spring` | `security/README.md`, `http-state-session-cache.md`, `spring-security-architecture.md` |
| `security` | `database`, `system-design` | `security/README.md`, `scim-provisioning-security.md`, `scim-drift-reconciliation.md`, `scim-deprovisioning-session-authz-consistency.md`, `authorization-runtime-signals-shadow-evaluation.md`, `database-security-identity-bridge-cutover-design.md`, `session-store-claim-version-cutover-design.md`, `authz-decision-logging-design.md`, `audit-logging-auth-authz-traceability.md`, `online-backfill-verification-cutover-gates.md` |
| `database` | `spring` | `database/README.md`, `database-to-spring-transaction-master-note.md`, `transaction-isolation-locking.md`, `transactional-deep-dive.md`, `spring-service-layer-transaction-boundary-patterns.md`, `spring-transaction-debugging-playbook.md` |
| `database` | `system-design` | `database/README.md`, `schema-migration-partitioning-cdc-cqrs.md`, `change-data-capture-outbox-relay-design.md`, `dual-read-comparison-verification-platform-design.md` |
| `database` | `security`, `system-design` | `database/README.md`, `online-backfill-verification-cutover-gates.md`, `scim-drift-reconciliation.md`, `authorization-runtime-signals-shadow-evaluation.md`, `scim-deprovisioning-session-authz-consistency.md`, `database-security-identity-bridge-cutover-design.md`, `session-store-claim-version-cutover-design.md`, `authz-decision-logging-design.md`, `audit-logging-auth-authz-traceability.md` |
| `database` | `network`, `software-engineering` | `database/README.md`, `slow-query-analysis-playbook.md`, `distributed-cache-design.md` |
| `system-design` | `database`, `network`, `security` | `system-design/README.md`, `distributed-cache-design.md`, `grpc-vs-rest.md`, `jwt-deep-dive.md` |
| `operating-system` | `language/java` | `operating-system/README.md`, `context-switching-deadlock-lockfree.md`, `virtual-threads-project-loom.md` |
| `network` | `operating-system`, `spring` | `network/README.md`, `nat-conntrack-ephemeral-port-exhaustion.md`, `timeout-retry-backoff-practical.md`, `spring-resilience4j-retry-circuit-breaker-bulkhead.md` |
| `network` | `security` | `forwarded-x-forwarded-for-x-real-ip-trust-boundary.md`, `api-key-hmac-signature-replay-protection.md`, `tls-loadbalancing-proxy.md` |
| `language/java` | `operating-system`, `network` | `language/README.md`, `direct-buffer-offheap-memory-troubleshooting.md`, `oom-killer-cgroup-memory-pressure.md`, `nat-conntrack-ephemeral-port-exhaustion.md` |
| `language/java` | `data-structure` | `java-equals-hashcode-comparable-contracts.md`, `collections-performance.md`, `treemap-vs-hashmap-vs-linkedhashmap.md` |
| `design-pattern` | `spring`, `software-engineering` | `design-pattern/README.md`, `strategy-pattern.md`, `decorator-vs-proxy.md` |
| `design-pattern/read-model` | `database`, `system-design` | `design-pattern/README.md`, `read-model-staleness-read-your-writes.md`, `incremental-summary-table-refresh-watermark.md`, `dual-read-comparison-verification-platform-design.md` |
| `spring` | `network` | `spring/README.md`, `spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md`, `network-spring-request-lifecycle-timeout-disconnect-bridge.md`, `spring-webclient-connection-pool-timeout-tuning.md` |
| `security` | `system-design` | `security/README.md`, `jwt-signature-verification-failure-playbook.md`, `jwt-jwks-outage-recovery-failover-drills.md`, `auth-incident-triage-blast-radius-recovery-matrix.md`, `service-discovery-health-routing-design.md`, `global-traffic-failover-control-plane-design.md`, `session-store-design-at-scale.md` |
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

카테고리 entrypoint: [Database README 빠른 탐색](../contents/database/README.md#빠른-탐색), [System Design README 빠른 탐색](../contents/system-design/README.md#빠른-탐색)

질문 예시:

`CDC로 read model을 옮길 때 cutover 검증은 DB 문서로 봐야 하나요, 시스템 설계로 봐야 하나요?`

읽는 순서:

1. [Schema Migration, Partitioning, CDC, CQRS](../contents/database/schema-migration-partitioning-cdc-cqrs.md)
2. [Change Data Capture / Outbox Relay 설계](../contents/system-design/change-data-capture-outbox-relay-design.md)
3. [Dual-Read Comparison / Verification Platform 설계](../contents/system-design/dual-read-comparison-verification-platform-design.md)

<a id="bridge-database-spring-transaction-cluster"></a>
<a id="database--spring"></a>
### Transaction Isolation / `@Transactional` / Rollback Debugging (`database ↔ spring`)

대표 symptom alias: `dirty read`, `lost update`, `write skew`, `phantom`, `@Transactional`, `transactional not applied`, `self invocation`, `checked exception commit`, `rollback-only`, `REQUIRES_NEW`, `readOnly`, `routing datasource`, `read/write split`

대표 synthesis entry: [Database to Spring Transaction Master Note](../master-notes/database-to-spring-transaction-master-note.md). invariant scope가 먼저 흔들리면 [Transaction Boundary Master Note](../master-notes/transaction-boundary-master-note.md)를 보조로 붙인다.

카테고리 entrypoint: [Database README: 트랜잭션 경계 / 애플리케이션 브리지](../contents/database/README.md#database-bridge-transaction-app), [Spring README 빠른 탐색](../contents/spring/README.md#빠른-탐색)

빠른 분기:

- 처음부터 `REQUIRES_NEW`, rollback-only, readOnly, routing-datasource까지 다 열지 말고 core ladder를 먼저 맞춘다: [트랜잭션 격리수준과 락](../contents/database/transaction-isolation-locking.md), [Isolation Anomaly Cheat Sheet](../contents/database/isolation-anomaly-cheat-sheet.md), [Database to Spring Transaction Master Note](../master-notes/database-to-spring-transaction-master-note.md), [@Transactional 깊이 파기](../contents/spring/transactional-deep-dive.md), [Spring Service-Layer Transaction Boundary Patterns](../contents/spring/spring-service-layer-transaction-boundary-patterns.md).
- core ladder 뒤 follow-up beginner branch는 증상별로 고른다.
- `audit는 남고 본 작업은 롤백`, `REQUIRES_NEW`, `partial commit`이면 [Spring Transaction Propagation: NESTED / REQUIRES_NEW Case Studies](../contents/spring/spring-transaction-propagation-nested-requires-new-case-studies.md), [Spring `TransactionSynchronization` Ordering, Suspend / Resume, and Resource Binding](../contents/spring/spring-transactionsynchronization-ordering-suspend-resume-resource-binding.md)로 branch를 탄다.
- `UnexpectedRollbackException`, `transaction marked rollback-only`, `catch 했는데 마지막에 터짐`이면 [Spring `UnexpectedRollbackException` and Rollback-Only Marker Traps](../contents/spring/spring-unexpectedrollback-rollbackonly-marker-traps.md), [Spring Transaction Debugging Playbook](../contents/spring/spring-transaction-debugging-playbook.md)로 branch를 탄다.
- `readOnly면 안전한가`, `isolation 설정이 read replica routing과 왜 엇나가지`, `inner readOnly인데 writer pool`이 핵심이면 [Spring Transaction Isolation / ReadOnly Pitfalls](../contents/spring/spring-transaction-isolation-readonly-pitfalls.md), [Spring Routing DataSource Read/Write Transaction Boundaries](../contents/spring/spring-routing-datasource-read-write-transaction-boundaries.md)로 branch를 탄다.
- lock wait, deadlock, pool starvation이 더 크면 [Deadlock Case Study](../contents/database/deadlock-case-study.md), [Connection Pool / Transaction Propagation / Bulk Write](../contents/database/connection-pool-transaction-propagation-bulk-write.md), [Slow Query Analysis Playbook](../contents/database/slow-query-analysis-playbook.md)로 DB/infra branch를 먼저 본다.

질문 예시:

`write skew나 phantom 같은 건 DB 문서에서 보라고 하는데, 실무에서는 결국 Spring service에 @Transactional을 어디에 붙여야 하고 왜 rollback이 안 되는지도 같이 봐야 하지 않나요?`

읽는 순서:

1. [트랜잭션 격리수준과 락](../contents/database/transaction-isolation-locking.md)
2. [Isolation Anomaly Cheat Sheet](../contents/database/isolation-anomaly-cheat-sheet.md)
3. [Database to Spring Transaction Master Note](../master-notes/database-to-spring-transaction-master-note.md)
4. [@Transactional 깊이 파기](../contents/spring/transactional-deep-dive.md)
5. [Spring Service-Layer Transaction Boundary Patterns](../contents/spring/spring-service-layer-transaction-boundary-patterns.md)

core ladder 뒤 follow-up beginner branch:

- `REQUIRES_NEW`, `partial commit`, `audit만 남고 본 작업은 롤백`이면 [Spring Transaction Propagation: NESTED / REQUIRES_NEW Case Studies](../contents/spring/spring-transaction-propagation-nested-requires-new-case-studies.md) -> [Spring `TransactionSynchronization` Ordering, Suspend / Resume, and Resource Binding](../contents/spring/spring-transactionsynchronization-ordering-suspend-resume-resource-binding.md)
- `UnexpectedRollbackException`, `transaction marked rollback-only`, `catch 했는데 마지막에 터짐`이면 [Spring `UnexpectedRollbackException` and Rollback-Only Marker Traps](../contents/spring/spring-unexpectedrollback-rollbackonly-marker-traps.md) -> [Spring Transaction Debugging Playbook](../contents/spring/spring-transaction-debugging-playbook.md)
- `readOnly면 안전한가`, `read/write split`, `reader route가 안 탄다`이면 [Spring Transaction Isolation / ReadOnly Pitfalls](../contents/spring/spring-transaction-isolation-readonly-pitfalls.md) -> [Spring Routing DataSource Read/Write Transaction Boundaries](../contents/spring/spring-routing-datasource-read-write-transaction-boundaries.md)

<a id="bridge-revoke-authz-cluster"></a>
### Revoke Lag / Stale AuthZ Cache / 403 After Revoke (`security ↔ system-design`)

대표 symptom alias: `revoke lag`, `logout but still works`, `allowed after revoke`, `revocation tail`, `stale authz cache`, `stale deny`, `grant but still denied`, `tenant-specific 403`, `403 after revoke`

대표 synthesis entry: [Authz and Permission Master Note](../master-notes/authz-and-permission-master-note.md). browser-local logout semantics가 더 크면 [Auth, Session, Token Master Note](../master-notes/auth-session-token-master-note.md)를 보조로 붙인다.

카테고리 entrypoint: [Security README: Browser / Session Troubleshooting Path](../contents/security/README.md#browser--session-troubleshooting-path), [Security README: Session / Boundary / Replay](../contents/security/README.md#session--boundary--replay), [Security README: AuthZ / Tenant / Response Contracts deep dive catalog](../contents/security/README.md#authz--tenant--response-contracts-deep-dive-catalog), [System Design README: Auth Session Troubleshooting Bridge](../contents/system-design/README.md#system-design-auth-session-troubleshooting-bridge)

system-design handoff cue: [Security README: Browser / Session Troubleshooting Path](../contents/security/README.md#browser--session-troubleshooting-path) -> [Security README: Session / Boundary / Replay](../contents/security/README.md#session--boundary--replay) -> [System Design README: Auth Session Troubleshooting Bridge](../contents/system-design/README.md#system-design-auth-session-troubleshooting-bridge)

빠른 분기:

- `allowed after revoke`, `logout but still works`, `revoked admin still has access`처럼 allow tail이면 [Session Revocation at Scale](../contents/security/session-revocation-at-scale.md), [Revocation Propagation Lag / Debugging](../contents/security/revocation-propagation-lag-debugging.md)로 revoke tail을 먼저 확인하고, 이어서 `[system design]` [System Design: Session Store / Claim-Version Cutover 설계](../contents/system-design/session-store-claim-version-cutover-design.md), `[system design]` [System Design: Canonical Revocation Plane Across Token Generations](../contents/system-design/canonical-revocation-plane-across-token-generations-design.md), `[recovery]` [System Design: Revocation Bus Regional Lag Recovery](../contents/system-design/revocation-bus-regional-lag-recovery-design.md)로 session/claim plane cleanup을 본다.
- `stale deny`, `grant but still denied`, `tenant-specific 403`, `403 after revoke`처럼 deny tail이면 [Authorization Caching / Staleness](../contents/security/authorization-caching-staleness.md), [AuthZ Cache Inconsistency / Runtime Debugging](../contents/security/authz-cache-inconsistency-runtime-debugging.md), [Auth Failure Response Contracts: `401` / `403` / `404`](../contents/security/auth-failure-response-401-403-404.md) 순으로 cache key, negative cache, concealment drift를 먼저 본다.

질문 예시:

`권한 revoke 직후 어떤 route는 계속 허용되고, 어떤 route는 이미 403으로 바뀌어요. revoke propagation lag인지 stale authz cache인지 어디서 갈라 봐야 하나요?`

읽는 순서:

1. [Security README: Browser / Session Troubleshooting Path](../contents/security/README.md#browser--session-troubleshooting-path)
2. [Session Revocation at Scale](../contents/security/session-revocation-at-scale.md)
3. [Revocation Propagation Lag / Debugging](../contents/security/revocation-propagation-lag-debugging.md)
4. [Authorization Caching / Staleness](../contents/security/authorization-caching-staleness.md)
5. [AuthZ Cache Inconsistency / Runtime Debugging](../contents/security/authz-cache-inconsistency-runtime-debugging.md)
6. [Auth Failure Response Contracts: `401` / `403` / `404`](../contents/security/auth-failure-response-401-403-404.md)
7. `[system design]` [System Design: Session Store / Claim-Version Cutover 설계](../contents/system-design/session-store-claim-version-cutover-design.md)
8. `[system design]` [System Design: Canonical Revocation Plane Across Token Generations](../contents/system-design/canonical-revocation-plane-across-token-generations-design.md)
9. `[recovery]` [System Design: Revocation Bus Regional Lag Recovery](../contents/system-design/revocation-bus-regional-lag-recovery-design.md)

<a id="bridge-authority-transfer-cluster"></a>
<a id="database--security--system-design"></a>
### Authority Transfer / SCIM Deprovision / Decision Parity (`database ↔ security ↔ system-design`)

대표 symptom alias: `authority transfer`, `SCIM deprovision`, `decision parity`, `auth shadow divergence`, `backfill is green but access tail remains`, `cleanup evidence`, `retirement evidence`, `decision log join key`, `audit evidence bundle`

카테고리 entrypoint: [Database README: Identity / Authority Transfer 브리지](../contents/database/README.md#database-bridge-identity-authority), [Security README: Identity / Delegation / Lifecycle](../contents/security/README.md#identity--delegation--lifecycle), [System Design README: Database / Security Authority Bridge](../contents/system-design/README.md#system-design-database-security-authority-bridge), [System Design README: Verification / Shadowing / Authority Bridge](../contents/system-design/README.md#system-design-verification-shadowing-authority-bridge)

system-design handoff cue: [Security README: Identity / Delegation / Lifecycle](../contents/security/README.md#identity--delegation--lifecycle) -> [System Design README: Database / Security Authority Bridge](../contents/system-design/README.md#system-design-database-security-authority-bridge) -> [System Design README: Verification / Shadowing / Authority Bridge](../contents/system-design/README.md#system-design-verification-shadowing-authority-bridge)

질문 예시:

`backfill은 green인데 SCIM deprovision 뒤 access tail이 남고 auth shadow divergence도 보여요. cleanup-ready한지 보려면 decision log와 audit evidence까지 같이 봐야 하나요?`

읽는 순서:

1. [SCIM Provisioning Security](../contents/security/scim-provisioning-security.md)
2. [SCIM Drift / Reconciliation](../contents/security/scim-drift-reconciliation.md)
3. [Online Backfill Verification, Drift Checks, and Cutover Gates](../contents/database/online-backfill-verification-cutover-gates.md)
4. [SCIM Deprovisioning / Session / AuthZ Consistency](../contents/security/scim-deprovisioning-session-authz-consistency.md)
5. [Authorization Runtime Signals / Shadow Evaluation](../contents/security/authorization-runtime-signals-shadow-evaluation.md)
6. `[system design]` [System Design: Database / Security Identity Bridge Cutover 설계](../contents/system-design/database-security-identity-bridge-cutover-design.md)
7. `[system design]` [System Design: Session Store / Claim-Version Cutover 설계](../contents/system-design/session-store-claim-version-cutover-design.md)
8. [AuthZ Decision Logging Design](../contents/security/authz-decision-logging-design.md)
9. [Audit Logging for Auth / AuthZ Traceability](../contents/security/audit-logging-auth-authz-traceability.md)

<a id="bridge-freshness-cluster"></a>
<a id="design-pattern--read-model--database--system-design"></a>
### Freshness / Stale Read / Read-After-Write (`design-pattern/read-model ↔ database/system-design`)

대표 symptom alias: `stale read`, `read-after-write`, `projection lag`, `old data after write`

카테고리 entrypoint: [Design Pattern README 빠른 탐색](../contents/design-pattern/README.md#빠른-탐색), [Database README: CDC / Outbox / Read Model Cutover 브리지](../contents/database/README.md#database-bridge-cdc-cutover), [System Design README 빠른 탐색](../contents/system-design/README.md#빠른-탐색)

질문 예시:

`stale read`, `read-after-write`, `projection lag`, `old data after write`가 같이 보이는데 replica lag인지, read-your-writes 설계가 빠진 건지, verification guardrail이 없는 건지 어떻게 구분하나요?`

읽는 순서:

1. [Read Model Staleness and Read-Your-Writes](../contents/design-pattern/read-model-staleness-read-your-writes.md)
2. [Projection Freshness SLO Pattern](../contents/design-pattern/projection-freshness-slo-pattern.md)
3. [Incremental Summary Table Refresh and Watermark Discipline](../contents/database/incremental-summary-table-refresh-watermark.md)
4. [Dual-Read Comparison / Verification Platform 설계](../contents/system-design/dual-read-comparison-verification-platform-design.md)

<a id="bridge-disconnect-cluster"></a>
<a id="spring--network"></a>
### Client Disconnect / 499 / Broken Pipe (`spring ↔ network`)

대표 symptom alias: `499`, `broken pipe`, `client disconnect`, `connection reset`, `proxy timeout`

카테고리 entrypoint: [Spring README: Spring Request Lifecycle Timeout / Disconnect Bridge](../contents/spring/README.md#spring-request-lifecycle-timeout--disconnect-bridge), [Network README: 연결해서 보면 좋은 문서 (cross-category bridge)](../contents/network/README.md#연결해서-보면-좋은-문서-cross-category-bridge)

질문 예시:

`499`, `broken pipe`, `client disconnect`, `connection reset`, `proxy timeout`이 같이 보이는데 Spring 버그인지 proxy timeout인지 어떻게 구분하나요?`

읽는 순서:

1. [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](../contents/spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
2. [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](../contents/network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
3. [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](../contents/network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md)
4. [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](../contents/network/network-spring-request-lifecycle-timeout-disconnect-bridge.md)

<a id="bridge-edge-timeout-cluster"></a>
### Edge 502 / 504 / Timeout Mismatch (`spring ↔ network`)

대표 symptom alias: `502`, `504`, `bad gateway`, `gateway timeout`, `local reply`, `timeout mismatch`, `async timeout mismatch`, `idle timeout mismatch`, `deadline budget mismatch`

카테고리 entrypoint: [Spring README: 빠른 탐색](../contents/spring/README.md#빠른-탐색), [Network README: 연결해서 보면 좋은 문서 (cross-category bridge)](../contents/network/README.md#연결해서-보면-좋은-문서-cross-category-bridge)

질문 예시:

`edge는 504인데 app은 200`, `bad gateway`, `local reply`, `async timeout mismatch`, `idle timeout mismatch`가 같이 보일 때 어느 hop이 먼저 끝났는지 어떻게 구분하나요?`

읽는 순서:

1. [Proxy Local Reply vs Upstream Error Attribution](../contents/network/proxy-local-reply-vs-upstream-error-attribution.md)
2. [Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB](../contents/network/vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md)
3. [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](../contents/spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
4. [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](../contents/network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md)
5. [Idle Timeout Mismatch: LB / Proxy / App](../contents/network/idle-timeout-mismatch-lb-proxy-app.md)
6. [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](../contents/network/network-spring-request-lifecycle-timeout-disconnect-bridge.md)

<a id="bridge-http-session-security-cluster"></a>
### HTTP Stateless / Cookie / Session / Spring Security (`network ↔ security ↔ spring`)

대표 concept alias: `HTTP stateless`, `cookie`, `session`, `JWT`, `왜 로그인 상태가 유지되나`, `Spring Security는 어디서 세션을 쓰나`, `hidden JSESSIONID`

카테고리 entrypoint: [Network README: 레거시 primer](../contents/network/README.md#레거시-primer), [Security README: 기본 primer](../contents/security/README.md#기본-primer), [Spring README: Spring Security 아키텍처](../contents/spring/README.md#spring-security-아키텍처)

먼저 beginner alias를 한 번 맞춘다.

| 자주 하는 말 | 먼저 이렇게 읽는다 | 안전한 다음 문서 |
|---|---|---|
| `hidden session`, `hidden JSESSIONID`, `cookie exists but session missing`, `cookie 있는데 다시 로그인`, `next request anonymous after login` | browser에는 cookie/session reference가 보이지만 서버는 아직 또는 더 이상 auth/session 상태를 복원하지 못하는 축일 수 있다 | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md) |
| `browser 401 -> 302 /login bounce`, `API가 login HTML을 받음` | raw `401` auth failure가 browser redirect UX로 감싸져 보이는 축일 수 있다 | [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md) |
| `SavedRequest`, `saved request bounce`, `원래 URL 복귀` | 로그인 상태가 아니라 로그인 전 원래 URL을 기억하는 navigation memory 축이다 | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md) |

질문 예시:

`쿠키`, `세션`, `JWT` 차이는 대충 아는데 Spring Security 문서로 올라가면 왜 갑자기 `SecurityContextRepository`, `SessionCreationPolicy`, `SavedRequest`, `hidden JSESSIONID`가 나오는지 모르겠어요. login loop 전까지 어떤 순서로 읽어야 안전한가요?`

읽는 순서:

1. [HTTP의 무상태성과 쿠키, 세션, 캐시](../contents/network/http-state-session-cache.md)
2. [Signed Cookies / Server Sessions / JWT Tradeoffs](../contents/security/signed-cookies-server-sessions-jwt-tradeoffs.md)
3. [Spring Security 아키텍처](../contents/spring/spring-security-architecture.md)
4. [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
5. [Browser / BFF Token Boundary / Session Translation](../contents/security/browser-bff-token-boundary-session-translation.md)

증상으로 갈라지면:

- `browser 401 -> 302 /login bounce`, `SavedRequest`, `saved request bounce`, `로그인 후 다시 /login으로 튄다`: [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md) -> [Spring Security `RequestCache` / `SavedRequest` Boundaries](../contents/spring/spring-security-requestcache-savedrequest-boundaries.md)
- `hidden session`, `hidden JSESSIONID`, `cookie exists but session missing`, `cookie 있는데 다시 로그인`, `next request anonymous after login`: [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../contents/network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> [Browser `401` vs `302` Login Redirect Guide](../contents/security/browser-401-vs-302-login-redirect-guide.md) -> [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
- `브라우저는 로그인돼 보이는데 API만 돈다`, `cookie는 있는데 session missing`이 outage/translation 쪽으로 기울면: [BFF Session Store Outage / Degradation Recovery](../contents/security/bff-session-store-outage-degradation-recovery.md)

### Spring + Security

기초 용어가 아직 흔들리면 바로 위 `HTTP Stateless / Cookie / Session / Spring Security` route를 먼저 타고 내려온다.

카테고리 entrypoint: [Spring README 빠른 탐색](../contents/spring/README.md#빠른-탐색), [Security README 빠른 시작](../contents/security/README.md#빠른-시작)

질문 예시:

`OIDC back-channel logout은 붙였는데 Spring login redirect, SavedRequest, session persistence 중 어디가 꼬였는지 모르겠어요`

읽는 순서:

1. [Spring Security `RequestCache` / `SavedRequest` Boundaries](../contents/spring/spring-security-requestcache-savedrequest-boundaries.md)
2. [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
3. [Spring OAuth2 + JWT 통합](../contents/spring/spring-oauth2-jwt-integration.md)
4. [OIDC Back-Channel Logout / Session Coherence](../contents/security/oidc-backchannel-logout-session-coherence.md)

<a id="bridge-auth-incident-cluster"></a>
<a id="security--system-design"></a>
### Auth Incident / JWKS Outage / Auth Verification (`security ↔ system-design`)

대표 symptom alias: `JWKS outage`, `kid miss`, `unable to find jwk`, `auth verification outage`, `stale JWKS cache`

카테고리 entrypoint: [Security README: Incident / Recovery / Trust](../contents/security/README.md#incident--recovery--trust), [System Design README: Security / System-Design Incident Bridge](../contents/system-design/README.md#system-design-security-incident-bridge)

system-design handoff cue: [Security README: Incident / Recovery / Trust](../contents/security/README.md#incident--recovery--trust) -> [System Design README: Security / System-Design Incident Bridge](../contents/system-design/README.md#system-design-security-incident-bridge)

질문 예시:

`JWKS outage`, `kid miss`, `unable to find jwk`, `auth verification outage`, `stale JWKS cache`가 같이 보이는데 인증 문서만 봐도 되는지, 아니면 failover 문서까지 같이 봐야 하는지 어떻게 판단하나요?`

읽는 순서:

1. `[playbook]` [JWT Signature Verification Failure Playbook](../contents/security/jwt-signature-verification-failure-playbook.md)
2. `[drill]` [JWT / JWKS Outage Recovery / Failover Drills](../contents/security/jwt-jwks-outage-recovery-failover-drills.md)
3. `[incident matrix]` [Auth Incident Triage / Blast-Radius Recovery Matrix](../contents/security/auth-incident-triage-blast-radius-recovery-matrix.md)
4. `[system design]` [System Design: Service Discovery / Health Routing 설계](../contents/system-design/service-discovery-health-routing-design.md)
5. `[system design]` [System Design: Global Traffic Failover Control Plane 설계](../contents/system-design/global-traffic-failover-control-plane-design.md)
6. `[system design]` [System Design: Session Store Design at Scale](../contents/system-design/session-store-design-at-scale.md)

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
