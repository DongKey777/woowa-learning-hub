# Topic Map

> 한 줄 요약: `CS-study`를 RAG로 쓸 때 어떤 질문이 어떤 문서 축으로 가야 하는지 정리한 topic routing map이다.
>
> 관련 문서:
> - [Query Playbook](./query-playbook.md)
> - [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)
> - [Retrieval Anchor Keywords](./retrieval-anchor-keywords.md)
> - [Algorithm README](../contents/algorithm/README.md)

> retrieval-anchor-keywords: topic map, topic routing, category cluster, symptom cluster, stale read cluster, stale-read route, read-after-write cluster, projection lag route, old data after write route, transaction isolation cluster, transaction-isolation route, @Transactional route, transactional not applied route, rollback not working route, self invocation route, checked exception commit route, rollback-only route, UnexpectedRollbackException route, readOnly isolation confusion route, database spring transaction bridge, database + spring route, transaction isolation to @Transactional route, freshness routing, client disconnect cluster, client-disconnect route, client closed request route, 499 route, broken pipe route, connection reset route, cancelled request route, zombie work route, proxy timeout vs spring bug route, 502 route, 504 route, bad gateway route, gateway timeout route, local reply route, local reply vs app error route, timeout mismatch route, async timeout mismatch route, idle timeout mismatch route, deadline budget mismatch route, auth outage cluster, auth-outage route, login loop route, 302 login loop route, hidden session mismatch route, savedrequest route, saved request loop route, sid mapping route, post-login session persistence route, logout token session miss route, cookie drop route, session store outage route, logout tail route, JWKS outage cluster, kid miss route, unable to find jwk route, auth verification outage, revoke lag cluster, revocation tail route, logout but still works route, stale authz cache route, stale deny route, 403 after revoke route, revoked admin still has access route, authority transfer cluster, SCIM deprovision route, SCIM disable but still access route, decision parity route, access tail remains route, auth shadow divergence route, deprovision tail route, cleanup evidence route, retirement evidence route, decision log join key route, audit evidence bundle route, database security system design bridge, spring security bridge, java runtime catalog, java concurrency catalog, java serialization catalog, java payload contract route, java boundary design catalog, thread dump route, jcmd route, async-profiler route, flamegraph route, safepoint route, jcstress route, lis route, subsequence vs subarray, sliding window route, binary search adjacency, lower_bound route, contiguous vs skip allowed, meeting rooms ii route, minimum meeting rooms route, railway platform route, hotel booking possible route, calendar booking route, sweep line route, interval greedy route, cross-category router, master note route, incident recovery trust route, browser session troubleshooting path route, session boundary replay route, identity delegation lifecycle route, authz tenant response contracts route, system design handoff cue, control plane handoff cue, cutover handoff cue

## 목적

이 문서는 단순 목차가 아니다.
RAG가 질문을 받았을 때 다음을 빠르게 판단하기 위한 라우팅 표다.

- 어떤 카테고리를 먼저 찾을지
- 어떤 문서를 우선 인용할지
- 같은 주제라도 정의, 실전, 운영, 트레이드오프 중 무엇을 먼저 가져올지

문서 역할 구분이 애매하면 [Navigation Taxonomy](./navigation-taxonomy.md)를 먼저 본다.

## 문서 역할 우선순위

| 질문 형태 | 먼저 볼 역할 | 예시 문서 |
|---|---|---|
| "어디부터 읽지?" | `survey` | `JUNIOR-BACKEND-ROADMAP.md`, `ADVANCED-BACKEND-ROADMAP.md` |
| "기초 개념부터 다시 잡고 싶다" | `primer` | `contents/system-design/system-design-framework.md`, `contents/data-structure/applied-data-structures-overview.md` |
| "이 카테고리에서 뭘 읽어야 하지?" | `catalog/navigator` | 루트 `README.md`, `contents/*/README.md` |
| "왜 이런 장애/트레이드오프가 생기지?" | `deep dive` 또는 `playbook` | `contents/database/slow-query-analysis-playbook.md`, `contents/network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md` |
| "여러 도메인을 같이 설명해야 한다" | `master note` / `synthesis` | `master-notes/latency-debugging-master-note.md`, `master-notes/consistency-boundary-master-note.md` |
| "면접 질문으로 빈틈을 점검하고 싶다" | `question bank` | `SENIOR-QUESTIONS.md` |

## Top-Level 라우팅

| 질문 의도 | 먼저 볼 카테고리 | 우선 문서 |
|---|---|---|
| 넓은 교차 질문, 증상 기반 디버깅, 큰 그림 설명 (`stale read`, `client disconnect`, `JWKS outage`, `authority transfer`) | `master-notes/` | `latency-debugging-master-note.md`, `consistency-boundary-master-note.md`, `auth-session-token-master-note.md`, `database-to-spring-transaction-master-note.md`, `retry-timeout-idempotency-master-note.md`, `migration-cutover-master-note.md` |
| transaction isolation / rollback / proxy boundary (`transaction isolation`, `transaction-isolation`, `@Transactional`, `self invocation`, `rollback-only`, `UnexpectedRollbackException`, `readOnly isolation`) | `master-notes/`, `contents/database/`, `contents/spring/` | `database-to-spring-transaction-master-note.md`, `transaction-isolation-locking.md`, `transactional-deep-dive.md`, `spring-service-layer-transaction-boundary-patterns.md`, `spring-transaction-debugging-playbook.md`, `spring-transaction-isolation-readonly-pitfalls.md`, `spring-unexpectedrollback-rollbackonly-marker-traps.md`, `spring-self-invocation-proxy-annotation-matrix.md` |
| 저장/트랜잭션/쿼리/신선도 문제 (`stale read`, `read-after-write`, `projection lag`) | `contents/database/` | `README.md`, `index-and-explain.md`, `slow-query-analysis-playbook.md`, `redo-log-undo-log-checkpoint-crash-recovery.md`, `index-condition-pushdown-filesort-temporary-table.md` |
| HTTP, TLS, 실시간 통신 / 종료 지점 문제 (`client disconnect`, `499`, `broken pipe`) | `contents/network/` | `README.md`, `grpc-vs-rest.md`, `http3-quic-practical-tradeoffs.md`, `tcp-congestion-control.md`, `service-mesh-sidecar-proxy.md`, `nat-conntrack-ephemeral-port-exhaustion.md`, `forwarded-x-forwarded-for-x-real-ip-trust-boundary.md` |
| OS, 스레드, I/O, 컨테이너 | `contents/operating-system/` | `README.md`, `epoll-kqueue-io-uring.md`, `container-cgroup-namespace.md`, `false-sharing-cache-line.md`, `run-queue-load-average-cpu-saturation.md`, `ebpf-perf-strace-production-tracing.md`, `monotonic-clock-wall-clock-timeout-deadline.md` |
| Spring 내부 동작 / request lifecycle (`async timeout`, `cancellation`, `client disconnect`) | `contents/spring/` | `README.md`, `spring-security-architecture.md`, `spring-webflux-vs-mvc.md`, `spring-transaction-debugging-playbook.md`, `spring-observability-micrometer-tracing.md`, `spring-resilience4j-retry-circuit-breaker-bulkhead.md`, `spring-eventlistener-transaction-phase-outbox.md` |
| 브라우저 세션 / login redirect / federated logout (`auth-outage`, `login loop`, `hidden session mismatch`, `logout token은 오는데 spring 앱 세션을 못 찾는다`) | `master-notes/`, `contents/security/` (`Browser / Session Troubleshooting Path`, `Session / Boundary / Replay`), `contents/spring/`, `contents/system-design/` | `auth-session-token-master-note.md`, `browser-auth-frontend-backend-master-note.md`, `contents/security/README.md#browser--session-troubleshooting-path`, `contents/security/README.md#session--boundary--replay`, `spring-security-requestcache-savedrequest-boundaries.md`, `spring-securitycontextrepository-sessioncreationpolicy-boundaries.md`, `browser-bff-token-boundary-session-translation.md`, `oidc-backchannel-logout-session-coherence.md`, `session-store-design-at-scale.md` |
| Java 런타임/동시성/직렬화/경계 설계 (`GC`, `thread dump`, `async-profiler`, `jcstress`, `payload contract`) | `contents/language/` | `contents/language/README.md#java-runtime-and-diagnostics`, `contents/language/README.md#java-concurrency-and-async`, `contents/language/README.md#java-serialization-and-payload-contracts`, `contents/language/README.md#java-language-and-boundary-design`, `contents/language/java/thread-dump-state-interpretation.md`, `contents/language/java/async-profiler-vs-jfr-comparison.md`, `contents/language/java/jcstress-concurrency-testing.md` |
| 설계/아키텍처/경계 | `contents/software-engineering/` | `README.md`, `solid-failure-patterns.md`, `ddd-bounded-context-failure-patterns.md`, `monolith-to-msa-failure-patterns.md`, `strangler-fig-migration-contract-cutover.md` |
| 시스템 설계 면접 | `contents/system-design/` | `README.md`, `system-design-framework.md`, `back-of-envelope-estimation.md`, `distributed-cache-design.md`, `chat-system-design.md`, `newsfeed-system-design.md`, `notification-system-design.md`, `multi-tenant-saas-isolation-design.md`, `payment-system-ledger-idempotency-reconciliation-design.md` |
| revoke lag / stale authz cache (`logout but still works`, `allowed after revoke`, `stale deny`, `grant but still denied`, `403 after revoke`) | `master-notes/`, `contents/security/` (`Session / Boundary / Replay`, `AuthZ / Tenant / Response Contracts`), `contents/system-design/` | `authz-and-permission-master-note.md`, `contents/security/README.md#session--boundary--replay`, `contents/security/README.md#authz--tenant--response-contracts-deep-dive-catalog`, `revocation-propagation-lag-debugging.md`, `authorization-caching-staleness.md`, `authz-cache-inconsistency-runtime-debugging.md`, `session-store-claim-version-cutover-design.md`, `revocation-bus-regional-lag-recovery-design.md` |
| authority transfer / SCIM deprovision / decision parity (`SCIM disable but still access`, `backfill is green but access tail remains`, `shadow read green but auth decision diverges`) | `master-notes/`, `contents/security/` (`Identity / Delegation / Lifecycle`), `contents/database/`, `contents/system-design/` | `migration-cutover-master-note.md`, `contents/security/README.md#identity--delegation--lifecycle`, `contents/database/online-backfill-verification-cutover-gates.md`, `contents/security/scim-deprovisioning-session-authz-consistency.md`, `contents/security/authorization-runtime-signals-shadow-evaluation.md`, `contents/system-design/README.md#system-design-database-security-authority-bridge`, `contents/system-design/README.md#system-design-verification-shadowing-authority-bridge`, `contents/system-design/database-security-identity-bridge-cutover-design.md` |
| 디자인 패턴 | `contents/design-pattern/` | `README.md`, `strategy-pattern.md`, `decorator-vs-proxy.md`, `builder-pattern.md`, `facade-vs-adapter-vs-proxy.md` |
| 자료구조/알고리즘 | `contents/data-structure/`, `contents/algorithm/` | `contents/algorithm/README.md`, `contents/data-structure/README.md`, `longest-increasing-subsequence-patterns.md`, `sliding-window-patterns.md`, `binary-search-patterns.md`, `two-pointer.md`, `interval-greedy-patterns.md`, `sweep-line-overlap-counting.md`, `hashmap-internals.md`, `trie-prefix-search-autocomplete.md` |
| 인증/인가/보안 / incident, trust recovery (`JWKS outage`, `kid miss`, `unable to find jwk`, `signing key compromise`, `trust bundle rollback`, `hardware attestation failure`) | `contents/security/` (`Incident / Recovery / Trust`, `Hardware Trust / Recovery`) | `contents/security/README.md#incident--recovery--trust`, `contents/security/README.md#hardware-trust--recovery-deep-dive-catalog`, `jwt-signature-verification-failure-playbook.md`, `jwt-jwks-outage-recovery-failover-drills.md`, `signing-key-compromise-recovery-playbook.md`, `hardware-attestation-policy-failure-recovery.md` |

## Symptom Alias Cluster Labels

증상으로 먼저 질문이 들어오면, 아래 alias cluster를 category label처럼 취급하고 첫 라우팅을 잡는다.
아래 cluster들은 질문이 커지기 쉬우므로, 필요하면 `master-notes/`로 먼저 올라간 뒤 category 본문으로 내려간다.
security symptom cluster는 [Security README](../contents/security/README.md)의 `Incident / Recovery / Trust`, `Browser / Session Troubleshooting Path`, `Session / Boundary / Replay`, `Identity / Delegation / Lifecycle`, `AuthZ / Tenant / Response Contracts deep dive catalog` wording을 그대로 따라 `catalog` entrypoint, `deep dive` 본문, `system design` handoff cue가 같은 이름으로 읽히게 맞춘다.

| 증상 alias cluster | 먼저 붙일 카테고리 | 우선 문서 | 함께 볼 bridge |
|---|---|---|---|
| `freshness`, `stale read`, `stale-read`, `read-after-write`, `projection lag`, `old data after write`, `방금 썼는데 조회가 옛값` | `master-notes/` -> `contents/design-pattern/`, `contents/database/`, `contents/system-design/` | `replica-freshness-master-note.md`, `read-model-staleness-read-your-writes.md`, `incremental-summary-table-refresh-watermark.md` | [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)의 `Freshness / Stale Read / Read-After-Write` section (`design-pattern/read-model ↔ database/system-design`) |
| `transaction isolation`, `transaction-isolation`, `@Transactional`, `transactional not applied`, `rollback not working`, `self invocation`, `checked exception commit`, `UnexpectedRollbackException`, `rollback-only`, `readOnly isolation confusion` | `master-notes/` -> `contents/database/`, `contents/spring/` | `database-to-spring-transaction-master-note.md`, `transaction-isolation-locking.md`, `transactional-deep-dive.md`, `spring-transaction-debugging-playbook.md`, `spring-transaction-isolation-readonly-pitfalls.md`, `spring-unexpectedrollback-rollbackonly-marker-traps.md`, `spring-self-invocation-proxy-annotation-matrix.md` | [Cross-Domain Bridge Map](./cross-domain-bridge-map.md#bridge-database-spring-transaction-cluster)의 `Transaction Isolation / @Transactional / Rollback Debugging` section (`database ↔ spring`) |
| `client disconnect`, `client-disconnect`, `client closed request`, `499`, `broken pipe`, `connection reset`, `cancelled request`, `zombie work`, `proxy timeout`, `proxy timeout인지 spring bug인지` | `master-notes/` -> `contents/spring/`, `contents/network/` | `network-failure-handling-master-note.md`, `spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md`, `client-disconnect-499-broken-pipe-cancellation-proxy-chain.md` | [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)의 `Client Disconnect / 499 / Broken Pipe` section (`spring ↔ network`) |
| `502`, `504`, `bad gateway`, `gateway timeout`, `local reply`, `local reply인지 app 에러인지`, `upstream reset` | `master-notes/` -> `contents/network/`, `contents/spring/` | `edge-request-lifecycle-master-note.md`, `proxy-local-reply-vs-upstream-error-attribution.md`, `vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md` | [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)의 `Edge 502 / 504 / Timeout Mismatch` section (`spring ↔ network`) |
| `timeout mismatch`, `async timeout mismatch`, `idle timeout mismatch`, `deadline budget mismatch`, `gateway는 504인데 app은 200` | `master-notes/` -> `contents/spring/`, `contents/network/` | `retry-timeout-idempotency-master-note.md`, `spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md`, `timeout-budget-propagation-proxy-gateway-service-hop-chain.md`, `idle-timeout-mismatch-lb-proxy-app.md` | [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)의 `Edge 502 / 504 / Timeout Mismatch` section (`spring ↔ network`) |
| `auth verification`, `JWKS outage`, `kid miss`, `unable to find jwk`, `stale JWKS cache` | `master-notes/` -> `contents/security/` (`Incident / Recovery / Trust`) -> `contents/system-design/` | `auth-session-token-master-note.md`, `contents/security/README.md#incident--recovery--trust`, `jwt-signature-verification-failure-playbook.md`, `jwt-jwks-outage-recovery-failover-drills.md`, `service-discovery-health-routing-design.md` | [Security README](../contents/security/README.md#incident--recovery--trust)의 `Incident / Recovery / Trust` -> [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)의 `Auth Incident / JWKS Outage / Auth Verification` section (`security ↔ system-design`) |
| `auth-outage`, `auth outage`, `login loop`, `302 login loop`, `hidden session mismatch`, `logout token은 오는데 spring 앱 세션을 못 찾는다`, `SavedRequest 때문에 login loop가 난다`, `sid mapping`, `post-login session persistence`, `cookie drop`, `session store outage`, `logout tail` | `master-notes/` -> `contents/security/` (`Browser / Session Troubleshooting Path`, `Session / Boundary / Replay`) -> `contents/spring/`, `contents/system-design/` | `auth-session-token-master-note.md`, `browser-auth-frontend-backend-master-note.md`, `contents/security/README.md#browser--session-troubleshooting-path`, `contents/security/README.md#session--boundary--replay`, `spring-security-requestcache-savedrequest-boundaries.md`, `spring-securitycontextrepository-sessioncreationpolicy-boundaries.md`, `browser-bff-token-boundary-session-translation.md`, `session-store-design-at-scale.md` | [Security README](../contents/security/README.md#browser--session-troubleshooting-path)의 `Browser / Session Troubleshooting Path` -> `Session / Boundary / Replay` -> [Cross-Domain Bridge Map](./cross-domain-bridge-map.md#spring--security)의 `Spring + Security` section (`spring ↔ security`) |
| `revoke lag`, `logout but still works`, `allowed after revoke`, `revoked admin still has access`, `revocation tail` | `master-notes/` -> `contents/security/` (`Browser / Session Troubleshooting Path`, `Session / Boundary / Replay`) -> `contents/system-design/` | `auth-session-token-master-note.md`, `contents/security/README.md#browser--session-troubleshooting-path`, `contents/security/README.md#session--boundary--replay`, `revocation-propagation-lag-debugging.md`, `session-revocation-at-scale.md`, `session-store-claim-version-cutover-design.md`, `revocation-bus-regional-lag-recovery-design.md` | [Security README](../contents/security/README.md#browser--session-troubleshooting-path)의 `Browser / Session Troubleshooting Path` -> `Session / Boundary / Replay` -> [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)의 `Revoke Lag / Stale AuthZ Cache / 403 After Revoke` section (`security ↔ system-design`) |
| `stale authz cache`, `stale deny`, `grant but still denied`, `tenant-specific 403`, `403 after revoke`, `cached 404 after grant` | `master-notes/` -> `contents/security/` (`AuthZ / Tenant / Response Contracts`) -> `contents/system-design/` | `authz-and-permission-master-note.md`, `contents/security/README.md#authz--tenant--response-contracts-deep-dive-catalog`, `authorization-caching-staleness.md`, `authz-cache-inconsistency-runtime-debugging.md`, `auth-failure-response-401-403-404.md`, `session-store-claim-version-cutover-design.md` | [Security README](../contents/security/README.md#authz--tenant--response-contracts-deep-dive-catalog)의 `AuthZ / Tenant / Response Contracts` -> [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)의 `Revoke Lag / Stale AuthZ Cache / 403 After Revoke` section (`security ↔ system-design`) |
| `authority transfer`, `SCIM deprovision`, `SCIM deprovision 뒤에도 권한이 남는다`, `SCIM disable but still access`, `backfill은 green인데 access tail이 남는다`, `backfill is green but access tail remains`, `shadow read는 green인데 auth decision이 갈린다`, `shadow read green but auth decision diverges`, `decision parity`, `auth shadow divergence`, `deprovision tail`, `cleanup evidence`, `retirement evidence`, `decision log join key`, `audit evidence bundle` | `master-notes/` -> `contents/security/` (`Identity / Delegation / Lifecycle`) -> `contents/database/`, `contents/system-design/` | `migration-cutover-master-note.md`, `contents/security/README.md#identity--delegation--lifecycle`, `online-backfill-verification-cutover-gates.md`, `scim-deprovisioning-session-authz-consistency.md`, `authorization-runtime-signals-shadow-evaluation.md`, `contents/system-design/README.md#system-design-database-security-authority-bridge`, `contents/system-design/README.md#system-design-verification-shadowing-authority-bridge`, `database-security-identity-bridge-cutover-design.md` | [Security README](../contents/security/README.md#identity--delegation--lifecycle)의 `Identity / Delegation / Lifecycle` -> [Cross-Domain Bridge Map](./cross-domain-bridge-map.md)의 `Authority Transfer / SCIM Deprovision / Decision Parity` section (`database ↔ security ↔ system-design`) |

## Algorithm Pattern Alias Cluster Labels

알고리즘 질문은 증상형 인시던트만큼이나 alias가 섞여 들어온다.
특히 `LIS`, `subsequence`, `subarray`, `subwindow`, `binary search`, `lower_bound`는 한 묶음으로 뭉개면 잘못 라우팅되기 쉬우므로, 첫 진입 문서와 바로 붙일 인접 문서를 같이 적어 둔다.

| 알고리즘 alias cluster | 먼저 붙일 카테고리 | 우선 문서 | 바로 붙일 인접 문서 |
|---|---|---|---|
| `LIS`, `longest increasing subsequence`, `subsequence`, `증가 부분 수열`, `skip allowed`, `order preserving` | `contents/algorithm/` | `README.md`, `longest-increasing-subsequence-patterns.md` | `binary-search-patterns.md` (`tails`, `lower_bound` 구현 축), `sliding-window-patterns.md` (`contiguous`와의 경계 확인) |
| `subarray`, `substring`, `window`, `subwindow`, `sliding window`, `contiguous only`, `recent k` | `contents/algorithm/` | `README.md`, `sliding-window-patterns.md` | `two-pointer.md` (포인터 이동 기본기), `binary-search-patterns.md` (길이/용량 feasibility를 바깥에서 탐색할 때) |
| `binary search`, `lower_bound`, `upper_bound`, `first true`, `answer space`, `monotonic predicate` | `contents/algorithm/` | `README.md`, `binary-search-patterns.md` | `longest-increasing-subsequence-patterns.md` (`tails + lower_bound` 하위 루틴), `sliding-window-patterns.md` (연속 구간 feasibility 판정 함수) |
| `meeting rooms II`, `minimum meeting rooms`, `railway platform`, `hotel booking possible`, `calendar overlap count`, `car pooling`, `max concurrency` | `contents/algorithm/` | `README.md`, `sweep-line-overlap-counting.md` | `interval-greedy-patterns.md` (`meeting rooms I`, `erase overlap intervals` 경계), `heap-variants.md` (활성 끝점 상태 유지), `interval-tree.md` (`my calendar`, online insert/query) |

첫 라우팅의 핵심은 세 패턴을 같은 "탐색 최적화" 군집으로 합치지 않는 것이다.
`skip allowed`가 보이면 LIS 쪽이고, `contiguous only`가 보이면 sliding window 쪽이며, `first true`나 `lower_bound`가 보이면 binary search를 중심에 둔 뒤 하위 판정 문서를 붙인다.

## Cross-Domain Bridges

질문 하나가 여러 축을 건드리면, 아래 연결을 우선한다.

- freshness / stale read / read-after-write / projection lag: `design-pattern/` + `database/` + `system-design/`
- transaction isolation / `@Transactional` / rollback-only / self invocation: `database/` + `spring/`
- client disconnect / 499 / broken pipe / connection reset: `spring/` + `network/`
- auth outage / login loop / SavedRequest / sid mapping / federated logout: `spring/` + `security/` + `system-design/`
- JWKS outage / kid miss / auth verification outage: `security/` + `system-design/`
- revoke lag / stale authz cache / 403 after revoke: `security/` + `system-design/`
- authority transfer / SCIM deprovision / decision parity / auth shadow divergence: `database/` + `security/` + `system-design/`
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

1. 먼저 질문의 카테고리와 문서 역할을 같이 정한다.
2. 역할이 애매하면 `navigation-taxonomy.md`를 본다.
3. 그다음 카테고리 `README.md` 또는 `master-notes/`로 진입점을 고른다.
4. 질문이 운영/장애/트레이드오프를 포함하면 `deep dive`나 `playbook`을 우선한다.
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
- `thread dump가 전부 RUNNABLE인데 CPU는 낮아요` -> `language/java/thread-dump-state-interpretation.md` + `language/java/async-profiler-vs-jfr-comparison.md`
- `jcmd로 JVM에서 어디부터 봐야 할지 모르겠어요` -> `language/java/jcmd-diagnostic-command-cheatsheet.md` + `language/java/jfr-event-interpretation.md`
- `ClassLoader leak 같아요` -> `language/java/classloader-memory-leak-playbook.md` + `spring/spring-test-slices-context-caching.md`
- `CDN 캐시가 이상해요` -> `network/cdn-cache-key-invalidation.md` + `system-design/file-storage-presigned-url-cdn-design.md`
- `connect timeout이 늘고 NAT가 의심돼요` -> `network/nat-conntrack-ephemeral-port-exhaustion.md` + `network/timeout-retry-backoff-practical.md`
- `heap은 괜찮은데 RSS만 올라요` -> `language/java/direct-buffer-offheap-memory-troubleshooting.md` + `operating-system/oom-killer-cgroup-memory-pressure.md`
- `jcstress로 volatile/publication을 검증하고 싶어요` -> `language/java/jcstress-concurrency-testing.md` + `language/java-memory-model-happens-before-volatile-final.md`
- `서비스 간 인증을 어떻게 설계하죠` -> `security/service-to-service-auth-mtls-jwt-spiffe.md` + `network/service-mesh-sidecar-proxy.md`
- `레거시를 점진적으로 옮기고 싶어요` -> `software-engineering/strangler-fig-migration-contract-cutover.md` + `database/cdc-debezium-outbox-binlog.md`
- `멀티 테넌트 noisy neighbor가 심해요` -> `system-design/multi-tenant-saas-isolation-design.md` + `system-design/rate-limiter-design.md`
- `p99가 튀는데 DB, JVM, 네트워크 중 어디가 문제인지 모르겠어요` -> `master-notes/latency-debugging-master-note.md` + `operating-system/psi-pressure-stall-information-runtime-debugging.md`
- `세션이랑 JWT랑 OIDC를 지금 서비스에 어떻게 섞어야 할지 모르겠어요` -> `master-notes/auth-session-token-master-note.md` + `security/jwt-deep-dive.md`
- `왜 @Transactional이 안 먹어요` -> `master-notes/database-to-spring-transaction-master-note.md` + `spring/spring-self-invocation-proxy-annotation-matrix.md` + `spring/spring-transaction-debugging-playbook.md`
- `UnexpectedRollbackException이 나요` -> `master-notes/database-to-spring-transaction-master-note.md` + `spring/spring-unexpectedrollback-rollbackonly-marker-traps.md`
- `LIS가 왜 sliding window가 아니에요` -> `algorithm/longest-increasing-subsequence-patterns.md` + `algorithm/sliding-window-patterns.md`
- `lower_bound로 LIS를 푸는 이유가 뭐예요` -> `algorithm/longest-increasing-subsequence-patterns.md` + `algorithm/binary-search-patterns.md`
- `길이 L의 subarray가 가능한지 판정해요` -> `algorithm/binary-search-patterns.md` + `algorithm/sliding-window-patterns.md`
- `meeting rooms II가 왜 interval greedy가 아니에요` -> `algorithm/sweep-line-overlap-counting.md` + `algorithm/interval-greedy-patterns.md`
- `my calendar가 meeting rooms랑 뭐가 달라요` -> `algorithm/sweep-line-overlap-counting.md` + `data-structure/interval-tree.md`
- `stale read가 나요` -> `master-notes/replica-freshness-master-note.md` + `design-pattern/read-model-staleness-read-your-writes.md`
- `499랑 broken pipe가 같이 나요` -> `spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md` + `network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md`
- `SavedRequest 때문에 login loop가 나요` -> `master-notes/browser-auth-frontend-backend-master-note.md` + `spring/spring-security-requestcache-savedrequest-boundaries.md` + `security/oidc-backchannel-logout-session-coherence.md`
- `unable to find jwk가 떠요` -> `master-notes/auth-session-token-master-note.md` + `security/jwt-jwks-outage-recovery-failover-drills.md`
- `403 after revoke가 떠요` -> `master-notes/authz-and-permission-master-note.md` + `security/authorization-caching-staleness.md` + `security/authz-cache-inconsistency-runtime-debugging.md`
- `backfill은 green인데 access tail이 남아요` -> `master-notes/migration-cutover-master-note.md` + `database/online-backfill-verification-cutover-gates.md` + `security/authorization-runtime-signals-shadow-evaluation.md`
- `SCIM disable 했는데 access tail이 남고 decision parity가 안 맞아요` -> `master-notes/migration-cutover-master-note.md` + `security/scim-deprovisioning-session-authz-consistency.md` + `security/authorization-runtime-signals-shadow-evaluation.md` + `system-design/database-security-identity-bridge-cutover-design.md`
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
