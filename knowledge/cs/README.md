# Basic Knowledge of Computer Science

> Since 2020.09.04

<p align="center">
  <img src="https://user-images.githubusercontent.com/22045163/111120575-d9370f00-85ae-11eb-8fa3-54f47ed3caa3.png" alt="coding" width="150px" />
</p>

> retrieval-anchor-keywords: cs root readme, meta navigator, readme router, roadmap, survey, study order, big picture, category readme, category navigator, category navigator snapshot, category readme snapshot, primer, basics, intro, catalog snapshot, navigator, index guide, what to read next, deep dive, troubleshooting, incident badge vocabulary, playbook label, runbook label, drill label, incident matrix label, master note, synthesis, question bank, interview questions, senior questions, rag routing, navigation taxonomy, security bridge cluster, auth session bridge, auth session troubleshooting bridge, authority bridge, replay session defense bundle, service delegation boundary bundle, hardware trust recovery bundle, incident recovery trust, session boundary replay, identity delegation lifecycle, auth outage, auth-outage, login loop, cookie drop, session store outage, saved request loop, savedrequest, sid mapping, post-login session persistence, logout token session miss, replay store down, nonce store down, replay-safe retry, duplicate request after retry, backfill replay, revoke lag, logout still works, logout tail, revocation tail, allowed after revoke, stale authz cache, stale deny, tenant-specific 403, cached 404 after grant, missing audit trail, missing-audit-trail, audit trail missing, auth signal gap, auth-signal-gap, auth telemetry gap, decision log missing, no decision log, observability blind spot, acting on behalf of, break glass, delegated admin, support access notification, authority transfer, SCIM deprovision, SCIM disable but still access, auth shadow divergence, trust bundle recovery, trust bundle rollback, hardware attestation failure, database category navigator, database category survey, database routing summary, database primer, database deep dive catalog, network category survey, network routing summary, network category primer, network deep dive catalog, network legacy primer, network modern topic catalog, minimum spanning tree, MST, mst router, prim vs kruskal, connect all nodes minimum cost, connect all cities minimum cost, connect all points minimum cost, minimum spanning forest, shortest path vs mst, 모든 정점을 최소 비용으로 연결, 최소 신장 트리, 프림, 크루스칼, stale read, stale-read, read-after-write, replica lag, transaction beginner side path, REQUIRES_NEW beginner route, rollback-only beginner route, readOnly beginner route, routing datasource confusion, inner readOnly writer pool, partial commit beginner, client disconnect, client-disconnect, 499, broken pipe, cancellation propagation, 502, 504, bad gateway, gateway timeout, local reply, upstream reset, timeout mismatch, async timeout mismatch, idle timeout mismatch, deadline budget mismatch, jwks outage, JWKS outage, auth verification outage, invalid signature, kid miss, unable to find JWK, stale jwks cache, browser session troubleshooting path, 302 login loop, hidden session mismatch

## Table of Contents

- [About](#about)
  - [Repository Rule](#repository-rule)
  - [Collaborator](#collaborator)
  - [Reference](#reference)
- [Quick Routes](#quick-routes)
  - [Symptom-First Quick Routes](#symptom-first-quick-routes)
- [Junior Backend Roadmap](#junior-backend-roadmap)
- [Advanced Backend Roadmap](#advanced-backend-roadmap)
- [Master Notes](#master-notes)
- [Senior-Level Questions](#senior-level-questions)
- [RAG Ready](#rag-ready)
- [Category Catalog Snapshots](#category-catalog-snapshots)
- [Data Structure (자료구조)](#data-structure-자료구조)
- [Algorithm (알고리즘)](#algorithm-알고리즘)
- [Operating System (운영체제)](#operating-system-운영체제)
- [Database (데이터베이스)](#database-데이터베이스)
- [Network (네트워크)](#network-네트워크)
- [Design Pattern (디자인 패턴)](#design-pattern-디자인-패턴)
- [Software Engineering (소프트웨어 공학)](#software-engineering-소프트웨어-공학)
- [Spring Framework (스프링 프레임워크)](#spring-framework-스프링-프레임워크)
- [System Design (시스템 설계)](#system-design-시스템-설계)
- [Security (보안)](#security-보안)
- [Language](#language)

## About

알고리즘과 CS 기초 지식의 이론부터 구현까지, 컴퓨터공학 전공자 및 예비 개발자로서 알아야 할 필수 전공 지식들을 공부하고 기록한 저장소입니다. 매주 스터디한 흔적인 **발표 자료**들이 업로드되어 있으며, 더 나아가 **글**로, **질의응답** 형태로 문서화하는 것을 목표로 합니다.

### Repository Rule

> [CS-study Repo 가이드](https://www.notion.so/CS-study-Repo-3428a7e4213345ffa08362c7abea8528)

- **주제별 정리** : 이론정리, 구현, 자료업로드, 질의응답
- **Commit convention rule** : [대주제] 소주제 분류(이론정리/구현/...) _ex) [DataStructure] Stack 자료정리_
- **Branch naming convention** : 대주제/닉네임 _ex) DataStructure/Nickname_

### Collaborator

<p>
<a href="https://github.com/KimKwon">
  <img src="https://github.com/KimKwon.png" width="100">
</a>
<a href="https://github.com/Seogeurim">
  <img src="https://github.com/Seogeurim.png" width="100">
</a>
<a href="https://github.com/yoongoing">
  <img src="https://github.com/yoongoing.png" width="100">
</a>
<a href="https://github.com/3people">
  <img src="https://github.com/3people.png" width="100">
</a>
<a href="https://github.com/JuseobJang">
  <img src="https://github.com/JuseobJang.png" width="100">
</a>
<a href="https://github.com/Hee-Jae">
  <img src="https://github.com/Hee-Jae.png" width="100">
</a>
<a href="https://github.com/ggjae">
  <img src="https://github.com/ggjae.png" width="100">
</a>
</p>

### Reference

- [JaeYeopHan/Interview_Question_for_Beginner](https://github.com/JaeYeopHan/Interview_Question_for_Beginner)
- [gyoogle/tech-interview-for-developer](https://github.com/gyoogle/tech-interview-for-developer)
- [WeareSoft/tech-interview](https://github.com/WeareSoft/tech-interview)
- [jobhope/TechnicalNote](https://github.com/jobhope/TechnicalNote)

## Quick Routes

이 루트 `README`는 저장소 전체의 **meta navigator**다.
여기서 설명을 끝내기보다, 필요한 역할 문서로 한 단계 더 내려 보내는 것이 목적이다.

`README.md`라는 파일명만으로 역할을 판단하지 않는다.
루트 `README`는 `meta navigator`, 카테고리 `README`는 `catalog / navigator`, `rag/*.md`는 `routing helper`에 가깝다.

| 지금 필요한 것 | 문서 역할 | 먼저 볼 문서 | 아직 기대하지 말 것 |
|---|---|---|---|
| 저장소 전체에서 어디로 들어갈지 정하기 | `meta navigator` | 이 루트 `README` | `primer`나 `deep dive` 본문 |
| 학습 순서를 잡는 큰 그림 | `survey` | roadmap 문서들 | 세부 장애 대응이나 trade-off 결론 |
| 카테고리 안에서 다음 문서를 고르기 | `catalog / navigator` | 각 카테고리 `README` | 본문 설명 전체 |
| 특정 주제의 개념 축을 세우기 | `primer` | 카테고리 `README`의 primer 구간 | cross-domain synthesis |
| 특정 경계나 failure mode를 깊게 파기 | `deep dive` | 개별 `contents/**` 문서 | 넓은 학습 순서 안내 |
| incident badge를 구분해서 고르기 | `playbook` / `runbook` / `drill` / `incident matrix` | `rag/navigation-taxonomy.md#incident-badge-vocabulary`, incident-heavy 카테고리 `README` | badge 이름이 다 비슷하다고 보고 아무 데나 같은 의미로 붙이기 |
| 여러 카테고리를 엮어 정리하기 | `master note` / `synthesis` | `master-notes/README.md` | 카테고리 전체 catalog |
| README나 navigator 역할이 헷갈리기 | `taxonomy` / `routing helper` | `rag/navigation-taxonomy.md`, `rag/README.md` | 개념 설명 본문 |

- 학습 순서용 `survey`부터 보고 싶다면:
  - [Junior Backend Roadmap](./JUNIOR-BACKEND-ROADMAP.md)
  - [Advanced Backend Roadmap](./ADVANCED-BACKEND-ROADMAP.md)
- 카테고리별 `catalog / navigator`로 바로 들어가려면:
  - 각 카테고리 `contents/*/README.md`
- 교차 도메인 `synthesis / master note`로 바로 들어가려면:
  - [Master Notes](./master-notes/README.md)
- 면접형 `question bank`로 점검하려면:
  - [Senior-Level Questions](./SENIOR-QUESTIONS.md)
- README / navigator 역할이 헷갈리면:
  - [Navigation Taxonomy](./rag/navigation-taxonomy.md)
  - [RAG Design](./rag/README.md)
- incident 대응 badge 기준이 헷갈리면:
  - [Incident Badge Vocabulary](./rag/navigation-taxonomy.md#incident-badge-vocabulary)
- 검색어가 역할 이름과 섞이면:
  - [Retrieval Anchor Keywords](./rag/retrieval-anchor-keywords.md)
- 문서 역할 구분이나 retrieval 라우팅 규칙이 더 필요하면:
  - [Topic Map](./rag/topic-map.md)
  - [Query Playbook](./rag/query-playbook.md)

### Symptom-First Quick Routes

루트 진입점에서도 자주 들어오는 증상 질의를 바로 route할 수 있게, 아래 route 묶음들은 [Master Notes](./master-notes/README.md), [Query Playbook](./rag/query-playbook.md), [Cross-Domain Bridge Map](./rag/cross-domain-bridge-map.md), category bridge `README` 기준을 한 번에 붙여 둔다.

- `stale read`, `stale-read`, `read-after-write`, `방금 썼는데 조회가 옛값`, `replica lag`부터 떠오르면 [Replica Freshness Master Note](./master-notes/replica-freshness-master-note.md), [Consistency Boundary Master Note](./master-notes/consistency-boundary-master-note.md)로 freshness budget을 먼저 잡고, bridge route는 [Read Model Staleness and Read-Your-Writes](./contents/design-pattern/read-model-staleness-read-your-writes.md) -> [Incremental Summary Table Refresh and Watermark Discipline](./contents/database/incremental-summary-table-refresh-watermark.md) -> [Dual-Read Comparison / Verification Platform 설계](./contents/system-design/dual-read-comparison-verification-platform-design.md) 순으로 내려간다.
- `dirty read`, `lost update`, `write skew`, `phantom`, `@Transactional`, `왜 안 롤백되지`, `self invocation`, `checked exception commit`, `lock wait`, `deadlock`, `UnexpectedRollbackException`이 같이 나오면 [Database to Spring Transaction Master Note](./master-notes/database-to-spring-transaction-master-note.md)로 DB/Spring 경계를 먼저 묶고, beginner split은 [DB Lock Wait / Deadlock vs Spring Proxy / Rollback 빠른 분기표](./contents/spring/spring-db-lock-deadlock-vs-proxy-rollback-decision-matrix.md)로 branch를 먼저 고른다. core ladder는 [트랜잭션 격리수준과 락](./contents/database/transaction-isolation-locking.md) -> [@Transactional 깊이 파기](./contents/spring/transactional-deep-dive.md) -> [Spring Service-Layer Transaction Boundary Patterns](./contents/spring/spring-service-layer-transaction-boundary-patterns.md) 순으로 먼저 맞춘다.
  - core ladder 뒤 follow-up beginner branch는 증상별로 나눈다.
  - `audit는 남고 본 작업은 롤백`, `REQUIRES_NEW`, `partial commit`이면 [Spring Transaction Propagation: NESTED / REQUIRES_NEW Case Studies](./contents/spring/spring-transaction-propagation-nested-requires-new-case-studies.md) -> [Spring `TransactionSynchronization` Ordering, Suspend / Resume, and Resource Binding](./contents/spring/spring-transactionsynchronization-ordering-suspend-resume-resource-binding.md)
  - `UnexpectedRollbackException`, `transaction marked rollback-only`, `catch 했는데 마지막에 터짐`이면 [Spring `UnexpectedRollbackException` and Rollback-Only Marker Traps](./contents/spring/spring-unexpectedrollback-rollbackonly-marker-traps.md) -> [Spring Transaction Debugging Playbook](./contents/spring/spring-transaction-debugging-playbook.md)
  - `readOnly면 안전한가`, `dirty checking`, `flush mode`가 헷갈리면 [Spring Transaction Isolation / ReadOnly Pitfalls](./contents/spring/spring-transaction-isolation-readonly-pitfalls.md)
  - `inner readOnly인데 writer pool`, `reader route가 안 탄다`, `read/write split`이면 [Spring Routing DataSource Read/Write Transaction Boundaries](./contents/spring/spring-routing-datasource-read-write-transaction-boundaries.md)
- `499`, `client disconnect`, `client-disconnect`, `broken pipe`, `cancelled request`, `zombie work`가 섞이면 [Network Failure Handling Master Note](./master-notes/network-failure-handling-master-note.md), [Retry, Timeout, Idempotency Master Note](./master-notes/retry-timeout-idempotency-master-note.md)로 hop별 종료 지점과 retry 증폭 여부를 먼저 보고, bridge route는 [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./contents/spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md) -> [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./contents/network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md) -> [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](./contents/network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md) 순으로 붙인다.
- `502`, `504`, `bad gateway`, `gateway timeout`, `local reply`, `upstream reset`이 먼저 보이면 [Edge Request Lifecycle Master Note](./master-notes/edge-request-lifecycle-master-note.md), [Network Failure Handling Master Note](./master-notes/network-failure-handling-master-note.md)로 edge/app 관측 ownership을 먼저 고정하고, bridge route는 [Proxy Local Reply vs Upstream Error Attribution](./contents/network/proxy-local-reply-vs-upstream-error-attribution.md) -> [Vendor-Specific Proxy Symptom Translation: Nginx, Envoy, ALB](./contents/network/vendor-specific-proxy-symptom-translation-nginx-envoy-alb.md) -> [Service Mesh Local Reply, Timeout, Reset Attribution](./contents/network/service-mesh-local-reply-timeout-reset-attribution.md) 순으로 붙인다.
- `timeout mismatch`, `async timeout mismatch`, `idle timeout mismatch`, `deadline budget mismatch`, `gateway는 504인데 app은 200`이 보이면 [Retry, Timeout, Idempotency Master Note](./master-notes/retry-timeout-idempotency-master-note.md), [Edge Request Lifecycle Master Note](./master-notes/edge-request-lifecycle-master-note.md)로 hop budget과 종료 순서를 먼저 잡고, bridge route는 [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./contents/spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md) -> [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](./contents/network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md) -> [Idle Timeout Mismatch: LB / Proxy / App](./contents/network/idle-timeout-mismatch-lb-proxy-app.md) -> [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./contents/network/network-spring-request-lifecycle-timeout-disconnect-bridge.md) 순으로 붙인다.
- `auth verification outage`, `JWKS outage`, `invalid signature`, `kid miss`, `unable to find JWK`, `stale JWKS cache`가 먼저 보이면 [Auth, Session, Token Master Note](./master-notes/auth-session-token-master-note.md), [Trust and Identity Master Note](./master-notes/trust-and-identity-master-note.md)로 auth state와 trust 경계를 먼저 잡고, security route label은 `[cross-category bridge]` [Incident / Recovery / Trust](./contents/security/README.md#incident--recovery--trust)로 맞춘다. bridge route는 `[playbook]` [JWT Signature Verification Failure Playbook](./contents/security/jwt-signature-verification-failure-playbook.md) -> `[drill]` [JWT / JWKS Outage Recovery / Failover Drills](./contents/security/jwt-jwks-outage-recovery-failover-drills.md) -> `[incident matrix]` [Auth Incident Triage / Blast-Radius Recovery Matrix](./contents/security/auth-incident-triage-blast-radius-recovery-matrix.md) -> `[system design]` [Security / System-Design Incident Bridge](./contents/system-design/README.md#system-design-security-incident-bridge) -> `[system design]` [Service Discovery / Health Routing 설계](./contents/system-design/service-discovery-health-routing-design.md) 순으로 붙인다.
- `auth-outage`, `auth outage`, `login loop`, `302 login loop`, `hidden session mismatch`, `SavedRequest 때문에 login loop가 난다`, `sid mapping`, `post-login session persistence`, `logout token은 오는데 spring 앱 세션을 못 찾는다`, `cookie drop`, `session store outage`가 먼저 보이면 [Auth, Session, Token Master Note](./master-notes/auth-session-token-master-note.md), [Browser Auth Frontend Backend Master Note](./master-notes/browser-auth-frontend-backend-master-note.md)로 browser/BFF/session state를 먼저 잡고, security route label은 `[catalog]` [Browser / Session Troubleshooting Path](./contents/security/README.md#browser--session-troubleshooting-path) -> `[cross-category bridge]` [Session / Boundary / Replay](./contents/security/README.md#session--boundary--replay) 순으로 읽는다. bridge route는 `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./contents/security/browser-401-vs-302-login-redirect-guide.md) -> `[deep dive]` [Spring Security `RequestCache` / `SavedRequest` Boundaries](./contents/spring/spring-security-requestcache-savedrequest-boundaries.md) -> `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) -> `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./contents/security/browser-bff-token-boundary-session-translation.md) -> `[system design]` [Auth Session Troubleshooting Bridge](./contents/system-design/README.md#system-design-auth-session-troubleshooting-bridge) -> `[system design]` [Session Store Design at Scale](./contents/system-design/session-store-design-at-scale.md) 순으로 붙인다.
- `revoke lag`, `logout still works`, `logout tail`, `allowed after revoke`, `revoked admin still has access`, `revocation tail`이 먼저 보이면 [Auth, Session, Token Master Note](./master-notes/auth-session-token-master-note.md), [Authz and Permission Master Note](./master-notes/authz-and-permission-master-note.md)로 session freshness와 permission fallout을 먼저 묶고, security route label은 `[catalog]` [Browser / Session Troubleshooting Path](./contents/security/README.md#browser--session-troubleshooting-path) -> `[cross-category bridge]` [Session / Boundary / Replay](./contents/security/README.md#session--boundary--replay)다. bridge route는 `[deep dive]` [Revocation Propagation Lag / Debugging](./contents/security/revocation-propagation-lag-debugging.md) -> `[deep dive]` [Session Revocation at Scale](./contents/security/session-revocation-at-scale.md) -> `[deep dive]` [Revocation Propagation Status Contract](./contents/security/revocation-propagation-status-contract.md) -> `[system design]` [Session Store / Claim-Version Cutover 설계](./contents/system-design/session-store-claim-version-cutover-design.md) -> `[system design]` [Revocation Bus Regional Lag Recovery](./contents/system-design/revocation-bus-regional-lag-recovery-design.md) 순으로 붙인다.
- `stale authz cache`, `stale deny`, `grant but still denied`, `tenant-specific 403`, `403 after revoke`, `cached 404 after grant`이 먼저 보이면 [Authz and Permission Master Note](./master-notes/authz-and-permission-master-note.md)로 authz cache와 concealment 경계를 먼저 잡고, security route label은 `[catalog]` [AuthZ / Tenant / Response Contracts deep dive catalog](./contents/security/README.md#authz--tenant--response-contracts-deep-dive-catalog)다. bridge route는 `[deep dive]` [Authorization Caching / Staleness](./contents/security/authorization-caching-staleness.md) -> `[deep dive]` [AuthZ Cache Inconsistency / Runtime Debugging](./contents/security/authz-cache-inconsistency-runtime-debugging.md) -> `[primer]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./contents/security/auth-failure-response-401-403-404.md) -> `[system design]` [Session Store / Claim-Version Cutover 설계](./contents/system-design/session-store-claim-version-cutover-design.md) 순으로 붙인다.
- `missing-audit-trail`, `audit trail이 없다`, `누가 허용/거부했는지 안 남는다`, `decision log missing`, `auth-signal-gap`, `allow/deny reason code가 안 보인다`, `401/403 spike인데 reason bucket이 없다`가 먼저 보이면 [Auth, Session, Token Master Note](./master-notes/auth-session-token-master-note.md), [Trust and Identity Master Note](./master-notes/trust-and-identity-master-note.md)로 auth evidence/telemetry 경계를 먼저 잡고, security route label은 `[catalog]` [운영 / Incident catalog](./contents/security/README.md#운영--incident-catalog) -> `[catalog]` [AuthZ / Tenant / Response Contracts deep dive catalog](./contents/security/README.md#authz--tenant--response-contracts-deep-dive-catalog)다. bridge route는 `[deep dive]` [Auth Observability: SLI / SLO / Alerting](./contents/security/auth-observability-sli-slo-alerting.md) -> `[deep dive]` [AuthZ Decision Logging Design](./contents/security/authz-decision-logging-design.md) -> `[deep dive]` [Audit Logging for Auth / AuthZ Traceability](./contents/security/audit-logging-auth-authz-traceability.md) -> `[deep dive]` [Authorization Runtime Signals / Shadow Evaluation](./contents/security/authorization-runtime-signals-shadow-evaluation.md) 순으로 붙인다.
- `replay store down`, `nonce store down`, `duplicate request after retry`, `replay-safe retry`, `backfill replay`가 섞이면 [Retry, Timeout, Idempotency Master Note](./master-notes/retry-timeout-idempotency-master-note.md)를 먼저 보고, 저장소 replay/backfill/repair 축이 더 크면 [Data Pipeline Replay Master Note](./master-notes/data-pipeline-replay-master-note.md), [Eventual Consistency Master Note](./master-notes/eventual-consistency-master-note.md)로 이어진다. security route label은 `[cross-category bridge]` [Session / Boundary / Replay](./contents/security/README.md#session--boundary--replay)로 맞추고, bridge route는 `[recovery]` [Replay Store Outage / Degradation Recovery](./contents/security/replay-store-outage-degradation-recovery.md) -> `[system design]` [Idempotency Key Store / Dedup Window / Replay-Safe Retry 설계](./contents/system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md) -> `[system design]` [Replay / Repair Orchestration Control Plane 설계](./contents/system-design/replay-repair-orchestration-control-plane-design.md) 순으로 붙인다.
- `authority transfer`, `SCIM deprovision`, `SCIM disable but still access`, `backfill is green but access tail remains`, `decision parity`, `auth shadow divergence`, `deprovision tail`, `cleanup evidence`, `retirement evidence`, `decision log join key`, `audit evidence bundle`가 보이면 [Migration Cutover Master Note](./master-notes/migration-cutover-master-note.md), [Trust and Identity Master Note](./master-notes/trust-and-identity-master-note.md)로 cutover와 authority 경계를 먼저 잡고, security route label은 `[cross-category bridge]` [Identity / Delegation / Lifecycle](./contents/security/README.md#identity--delegation--lifecycle)이다. bridge route는 `[deep dive]` [SCIM Deprovisioning / Session / AuthZ Consistency](./contents/security/scim-deprovisioning-session-authz-consistency.md) -> `[deep dive]` [Authorization Runtime Signals / Shadow Evaluation](./contents/security/authorization-runtime-signals-shadow-evaluation.md) -> `[system design]` [Database / Security Authority Bridge](./contents/system-design/README.md#system-design-database-security-authority-bridge) -> `[system design]` [Verification / Shadowing / Authority Bridge](./contents/system-design/README.md#system-design-verification-shadowing-authority-bridge) -> `[system design]` [Database / Security Identity Bridge Cutover 설계](./contents/system-design/database-security-identity-bridge-cutover-design.md) 순으로 붙인다.
- `acting on behalf of`, `break glass`, `delegated admin`, `support access notification`이 보이면 [Trust and Identity Master Note](./master-notes/trust-and-identity-master-note.md)를 대표 진입점으로 잡고, security route label은 `[cross-category bridge]` [Identity / Delegation / Lifecycle](./contents/security/README.md#identity--delegation--lifecycle)이다. bridge route는 `[deep dive]` [Support Operator / Acting-on-Behalf-Of Controls](./contents/security/support-operator-acting-on-behalf-of-controls.md) -> `[deep dive]` [Customer-Facing Support Access Notifications](./contents/security/customer-facing-support-access-notifications.md) -> `[deep dive]` [Audience Matrix for Support Access Events](./contents/security/audience-matrix-for-support-access-events.md) -> `[deep dive]` [Incident-Close Break-Glass Gate](./contents/security/incident-close-break-glass-gate.md) 순으로 붙인다.
- `trust bundle rollback`, `hardware attestation failure`, `trust bundle recovery`가 보이면 [Trust and Identity Master Note](./master-notes/trust-and-identity-master-note.md)를 대표 진입점으로 잡고, rollout/cutover 문맥이 크면 [Migration Cutover Master Note](./master-notes/migration-cutover-master-note.md)를 같이 본다. security route label은 `[cross-category bridge]` [Incident / Recovery / Trust](./contents/security/README.md#incident--recovery--trust) -> `[catalog]` [Hardware Trust / Recovery deep dive catalog](./contents/security/README.md#hardware-trust--recovery-deep-dive-catalog)다. bridge route는 `[deep dive]` [mTLS Certificate Rotation / Trust Bundle Rollout](./contents/security/mtls-certificate-rotation-trust-bundle-rollout.md) -> `[recovery]` [Hardware Attestation Policy / Failure Recovery](./contents/security/hardware-attestation-policy-failure-recovery.md) -> `[system design]` [Trust-Bundle Rollback During Cell Cutover 설계](./contents/system-design/trust-bundle-rollback-during-cell-cutover-design.md) 순으로 붙인다.

## Junior Backend Roadmap

- [신입 백엔드 CS 학습 순서 가이드](./JUNIOR-BACKEND-ROADMAP.md)

## Advanced Backend Roadmap

- [백엔드 심화 학습 순서 가이드](./ADVANCED-BACKEND-ROADMAP.md)

## Master Notes

- [마스터노트 인덱스](./master-notes/README.md)
- [Master Notes 안내](./MASTER-NOTES.md)

추천 진입:

- `latency / timeout / retry / backpressure`
- `transaction / consistency / idempotency / outbox`
- `auth / session / token / trust boundary`
- `migration / cutover / rollback / shadow traffic`
- `JVM / OS / native memory / page cache`

대표 노트:

- [Latency Debugging Master Note](./master-notes/latency-debugging-master-note.md)
- [Consistency Boundary Master Note](./master-notes/consistency-boundary-master-note.md)
- [Auth, Session, Token Master Note](./master-notes/auth-session-token-master-note.md)
- [Database to Spring Transaction Master Note](./master-notes/database-to-spring-transaction-master-note.md)
- [Retry, Timeout, Idempotency Master Note](./master-notes/retry-timeout-idempotency-master-note.md)
- [Migration Cutover Master Note](./master-notes/migration-cutover-master-note.md)

## Senior-Level Questions

- [시니어 레벨 질문 모음](./SENIOR-QUESTIONS.md)

## RAG Ready

- [RAG Ready Checklist](./RAG-READY.md)
- [RAG Design](./rag/README.md)
- [Topic Map](./rag/topic-map.md)
- [Query Playbook](./rag/query-playbook.md)
- [Retrieval Anchor Keywords](./rag/retrieval-anchor-keywords.md)
- [Cross-Domain Bridge Map](./rag/cross-domain-bridge-map.md)
- [Learning Paths for Retrieval](./rag/learning-paths-for-retrieval.md)

### RAG Navigation

| 목적 | 먼저 볼 문서 |
|---|---|
| 학습 순서 잡기 | `JUNIOR-BACKEND-ROADMAP.md`, `ADVANCED-BACKEND-ROADMAP.md` |
| 문서 역할 판별 | `rag/navigation-taxonomy.md` |
| `playbook` / `runbook` / `drill` / `incident matrix` badge 구분 | `rag/navigation-taxonomy.md#incident-badge-vocabulary`, incident-heavy 카테고리 `README.md` |
| 역할이 헷갈리면서 범위도 넓다 | `rag/navigation-taxonomy.md`, `rag/query-playbook.md`, `master-notes/README.md` |
| 카테고리 진입점 찾기 | 루트 `README.md`, 각 카테고리 `README.md` |
| 교차 도메인 맥락 잡기 | `master-notes/README.md`, 대표 master note 문서 |
| 질문 bank로 점검하기 | `SENIOR-QUESTIONS.md` |
| 증상 기반 키워드 확장 | `rag/retrieval-anchor-keywords.md`, `rag/query-playbook.md` |
| 검색 라우팅 잡기 | `rag/topic-map.md`, `rag/query-playbook.md`, `rag/cross-domain-bridge-map.md` |

## Category Catalog Snapshots

아래 대분류 섹션들은 루트 `README`에 남겨 둔 **catalog snapshot**이다.

- 학습 순서를 고르려면 roadmap 같은 `survey`로 돌아간다.
- 설명 본문이 필요하면 각 카테고리 `README`의 `primer` 또는 개별 `deep dive` 문서로 내려간다.
- 교차 도메인 묶음이 필요하면 `master note`, self-check가 목적이면 `question bank`로 이동한다.
- 루트 snapshot heading도 generic `정리노트`보다 `카테고리 README` / `category navigator` 같은 역할명이 바로 보이게 유지한다.
- 링크를 연 다음에도 상단 역할 라벨(`primer`, `catalog`, `deep dive`, `question bank`)을 다시 확인한다.
- 역할 이름이 헷갈리면 [Navigation Taxonomy](./rag/navigation-taxonomy.md)에서 `survey / primer / catalog / deep dive` 경계를 다시 확인하고, incident 라벨이 섞이면 [Incident Badge Vocabulary](./rag/navigation-taxonomy.md#incident-badge-vocabulary)를 본다.

## Data Structure (자료구조)

### [📖 자료구조 README](./contents/data-structure/README.md) (`category navigator` snapshot)

#### 기본 자료 구조

- Array
- Linked List
- Stack
- Queue
- Tree
- Binary Tree
- Graph

#### 응용 자료 구조

- Deque
- Heap & Priority Queue
- Indexed Tree (Segment Tree)
- Trie
- Bloom Filter
- LRU Cache Design
- HashMap 내부 구조
- TreeMap / HashMap / LinkedHashMap 선택 기준
- Monotonic Queue / Stack
- Segment Tree Lazy Propagation
- Union-Find Deep Dive

[🔝 목차로 돌아가기](#table-of-contents)

## Algorithm (알고리즘)

### [📖 알고리즘 README](./contents/algorithm/README.md) (`category navigator` snapshot)

- `MST`, `minimum spanning tree`, `connect all nodes minimum cost`, `connect all cities minimum cost`, `모든 정점을 최소 비용으로 연결`, `Prim vs Kruskal`처럼 전체 연결 비용 질문이면 [Minimum Spanning Tree: Prim vs Kruskal](./contents/algorithm/minimum-spanning-tree-prim-vs-kruskal.md)로 먼저 들어간다.

#### 알고리즘 기본

- 시간복잡도와 공간복잡도
- 상각 분석과 복잡도 함정
- 완전 탐색 알고리즘 (Brute Force)
  - DFS와 BFS
  - 순열, 조합, 부분집합
- 백트래킹 (Backtracking)
- 분할 정복법 (Divide and Conquer)
- 탐욕 알고리즘 (Greedy)
- 동적 계획법 (Dynamic Programming)

#### 알고리즘 응용

- 정렬 알고리즘
- 그래프
  - 최단 경로 알고리즘
  - [Minimum Spanning Tree: Prim vs Kruskal](./contents/algorithm/minimum-spanning-tree-prim-vs-kruskal.md)
  - Union Find & Kruskal
  - 위상 정렬 패턴
- 두 포인터 (two-pointer)
- Sliding Window 패턴
- Binary Search 패턴
- Interval Greedy 패턴
- Shortest Path 알고리즘 비교
- Network Flow 기초 직관
- 문자열 처리 알고리즘
  - KMP 알고리즘

[🔝 목차로 돌아가기](#table-of-contents)

## Operating System (운영체제)

### [📖 운영체제 README](./contents/operating-system/README.md) (`category navigator` snapshot)

- `primer`: 프로세스와 스레드 / 멀티 프로세스와 멀티 스레드 / 프로세스 스케줄링 / CPU 스케줄링 / 프로세스 동기화 / 가상 메모리
- `runtime catalog`: 컨텍스트 스위칭 / futex / off-CPU / run queue / scheduler latency / epoll / io_uring
- `memory / durability`: false sharing / cache line / page cache / dirty writeback / fsync / mmap coherency / direct I/O
- `container / pressure`: cgroup / namespace / container 격리 / overlayfs / tmpfs / OOM / pressure stall
- `diagnostics`: NUMA 운영 디버깅 / eBPF / perf / strace / deleted-but-open files / signals / supervision

[🔝 목차로 돌아가기](#table-of-contents)

## Database (데이터베이스)

### [📖 데이터베이스 README](./contents/database/README.md) (`category navigator` snapshot)

- `survey`: [추천 학습 흐름 (category-local survey)](./contents/database/README.md#추천-학습-흐름-category-local-survey)에서 `Transaction / Locking / Invariant`, `Query Plan / Index / Write Path`, `Schema Migration / CDC / Replay`, `Replica / Failover / Freshness`, `Lifecycle / Cleanup / Drift` 순으로 큰 흐름을 잡는다.
- `navigator entrypoint`: [빠른 탐색](./contents/database/README.md#빠른-탐색), [역할별 라우팅 요약](./contents/database/README.md#역할별-라우팅-요약)에서 `survey / primer / catalog / playbook-runbook / taxonomy` 중 어디로 바로 들어갈지 고른다.
- `primer`: [트랜잭션 격리수준과 락](./contents/database/transaction-isolation-locking.md), [인덱스와 실행 계획](./contents/database/index-and-explain.md), [MVCC, Replication, Sharding](./contents/database/mvcc-replication-sharding.md)
- `deep dive catalog`: [현대 catalog](./contents/database/README.md#현대-catalog), [트랜잭션 격리수준과 락](./contents/database/README.md#트랜잭션-격리수준과-락), [Schema Migration, Partitioning, CDC, CQRS](./contents/database/README.md#schema-migration-partitioning-cdc-cqrs), [Authority Transfer / Security Bridge](./contents/database/README.md#authority-transfer--security-bridge), [Replica Lag와 Read-after-Write](./contents/database/README.md#replica-lag와-read-after-write), [Vacuum / Purge Debt](./contents/database/README.md#vacuum--purge-debt)
- `playbook / runbook`: [Lock Wait, Deadlock, and Latch Contention Triage Playbook](./contents/database/lock-wait-deadlock-latch-triage-playbook.md), [느린 쿼리 분석 플레이북](./contents/database/slow-query-analysis-playbook.md), [Expired-Unreleased Drift Runbook](./contents/database/expired-unreleased-drift-runbook.md), [CDC Replay Verification, Idempotency, and Acceptance Runbook](./contents/database/cdc-replay-verification-idempotency-runbook.md)

[🔝 목차로 돌아가기](#table-of-contents)

## Network (네트워크)

### [📖 네트워크 README](./contents/network/README.md) (`category navigator` snapshot)

- `survey`: [추천 학습 흐름 (category-local survey)](./contents/network/README.md#추천-학습-흐름-category-local-survey)에서 `TCP / HTTP Version Progression`, `Proxy / Mesh / Trust Boundary`, `Timeout / Queueing / Overload`, `Streaming / Disconnect / Cancellation`, `Cache / DNS / Edge Variation` 순으로 큰 흐름을 잡는다.
- `routing summary`: [역할별 라우팅 요약](./contents/network/README.md#역할별-라우팅-요약)에서 `survey / primer / catalog / playbook-runbook / taxonomy` 중 어디로 바로 들어갈지 고른다.
- `primer`: [레거시 primer](./contents/network/README.md#레거시-primer), [보조 primer](./contents/network/README.md#보조-primer)에서 `OSI`, `TCP handshake`, `TCP vs UDP`, `웹 통신의 흐름` 같은 입문 축을 먼저 잡고 primer 내부 anchor로 더 내려간다.
- `deep dive catalog`: [현대 topic catalog](./contents/network/README.md#현대-topic-catalog)에서 `HTTP/2 / gRPC`, `TLS / Proxy / Mesh`, `Timeout / Queueing / Overload`, `Streaming / Disconnect / Cancellation`, `Cache / DNS / Edge Variation` bucket 중 필요한 축을 고른다.
- `playbook / runbook`: [Cache, Vary, Accept-Encoding Edge Case Playbook](./contents/network/cache-vary-accept-encoding-edge-case-playbook.md), [Queue Saturation Attribution, Metrics, Runbook](./contents/network/queue-saturation-attribution-metrics-runbook.md), [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./contents/network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md), [SSE Failure Attribution Across HTTP/1.1 and HTTP/2](./contents/network/sse-failure-attribution-http1-http2.md)

[🔝 목차로 돌아가기](#table-of-contents)

## Design Pattern (디자인 패턴)

### [📖 디자인 패턴 README](./contents/design-pattern/README.md) (`category navigator` snapshot)

- 디자인 패턴의 개념과 종류
- Strategy 패턴
- Decorator vs Proxy
- Observer / Pub-Sub / Application Event
- Singleton 패턴
- Factory 패턴
- Builder 패턴
- Template Method vs Strategy
- God Object / Spaghetti / Golden Hammer
- Facade / Adapter / Proxy 비교
- Factory / Abstract Factory / Builder 비교
- Composition over Inheritance
- Command Pattern / Undo / Queue
- MVC 패턴

[🔝 목차로 돌아가기](#table-of-contents)

## Software Engineering (소프트웨어 공학)

### [📖 소프트웨어 공학 README](./contents/software-engineering/README.md) (`category navigator` snapshot)

- 프로그래밍 패러다임
  - 명령형 프로그래밍 vs 선언형 프로그래밍
  - 함수형 프로그래밍
  - 객체지향 프로그래밍
- DDD 바운디드 컨텍스트 실패 패턴
- Monolith → MSA 실패 패턴
- Event Sourcing / CQRS 도입 기준
- 기술 부채 / 리팩토링 타이밍
- Anti-Corruption Layer 통합 패턴
- Contract Testing / Modular Monolith / Feature Flag Cleanup / Idempotency Boundary
- Strangler Fig / Contract / Cutover
- Branch by Abstraction / Feature Flag / Strangler 선택 기준
- Repository / DAO / Entity / Mapper
- SOLID failure patterns
- 애자일 개발 프로세스

[🔝 목차로 돌아가기](#table-of-contents)

## Spring Framework (스프링 프레임워크)

### [📖 스프링 README](./contents/spring/README.md) (`category navigator` snapshot)

- IoC 컨테이너와 DI
- AOP 프록시 메커니즘
- `@Transactional` 동작 원리와 함정
- Spring MVC 요청 생명주기
- Spring Boot 자동 구성
- Spring Security 아키텍처
- Spring MVC vs WebFlux
- Async Servlet Dispatch / `Callable` / `DeferredResult`
- Bean 생명주기 / Scope 함정
- OAuth2 + JWT 통합
- Security 401/403 번역 / `SessionCreationPolicy` / `SecurityContextRepository`
- Test Slice / Context Caching
- Cache Abstraction 함정 / Transaction Debugging
- Startup Hook / Readiness Warmup / Routing DataSource / JDBC Exception Translation
- Scheduler / Async / Batch / Observability / WebClient
- Resilience4j / Retry / CircuitBreaker / Bulkhead

[🔝 목차로 돌아가기](#table-of-contents)

## System Design (시스템 설계)

### [📖 시스템 설계 README](./contents/system-design/README.md) (`category navigator` snapshot)

- 시스템 설계 면접 프레임워크
- Back-of-the-envelope 추정
- URL 단축기 설계
- Rate Limiter 설계
- 분산 캐시 설계
- 채팅 시스템 설계
- 뉴스피드 시스템 설계
- 알림 시스템 설계
- Consistent Hashing / Hot Key 전략
- Multi-tenant SaaS isolation
- Payment System / Ledger / Idempotency / Reconciliation
- Distributed Lock / Search / File Storage / Workflow
- 요구사항을 숫자와 병목으로 바꾸는 사고법
- 검색 / 분산 합의 / 워크플로우 / 멀티테넌시 주제로 확장
- `bridge cluster`: [Security / System-Design Incident Bridge](./contents/system-design/README.md#system-design-security-incident-bridge), [Auth Session Troubleshooting Bridge](./contents/system-design/README.md#system-design-auth-session-troubleshooting-bridge), [Database / Security Authority Bridge](./contents/system-design/README.md#system-design-database-security-authority-bridge), [Capability Rollout Deepening](./contents/system-design/README.md#system-design-capability-rollout-deepening), [Verification / Shadowing / Authority Bridge](./contents/system-design/README.md#system-design-verification-shadowing-authority-bridge)

[🔝 목차로 돌아가기](#table-of-contents)

## Security (보안)

### [📖 보안 README](./contents/security/README.md) (`category navigator` snapshot)

- `survey`: [추천 학습 흐름 (category-local survey)](./contents/security/README.md#추천-학습-흐름-category-local-survey)에서 `JWT / Session / Recovery`, `OAuth / Browser / BFF` mainline과 `OAuth PAR / JAR` / `OAuth Device Code` branch point, `Service Trust / Delegation`, `AuthZ / Tenant / Detection`, `Abuse / Replay / PoP`, `SCIM / Lifecycle / Drift` 순으로 큰 흐름을 잡는다.
- `primer`: [인증과 인가의 차이](./contents/security/authentication-vs-authorization.md), [Signed Cookies / Server Sessions / JWT Trade-offs](./contents/security/signed-cookies-server-sessions-jwt-tradeoffs.md), [OAuth2 Authorization Code Grant](./contents/security/oauth2-authorization-code-grant.md)
- `catalog / navigator`: [운영 / Incident catalog](./contents/security/README.md#운영--incident-catalog), [Hardware Trust / Recovery deep dive catalog](./contents/security/README.md#hardware-trust--recovery-deep-dive-catalog), [Session Coherence / Assurance deep dive catalog](./contents/security/README.md#session-coherence--assurance-deep-dive-catalog), [Browser / Session Coherence](./contents/security/README.md#browser--session-coherence), [Browser / Session Troubleshooting Path](./contents/security/README.md#browser--session-troubleshooting-path), [Browser / Server Boundary deep dive catalog](./contents/security/README.md#browser--server-boundary-deep-dive-catalog), [Replay / Token Misuse / Session Defense deep dive catalog](./contents/security/README.md#replay--token-misuse--session-defense-deep-dive-catalog), [Identity Lifecycle / Provisioning deep dive catalog](./contents/security/README.md#identity-lifecycle--provisioning-deep-dive-catalog), [Service / Delegation Boundaries deep dive catalog](./contents/security/README.md#service--delegation-boundaries-deep-dive-catalog), [AuthZ / Tenant / Response Contracts deep dive catalog](./contents/security/README.md#authz--tenant--response-contracts-deep-dive-catalog)
- `route label`: `[cross-category bridge]` [Incident / Recovery / Trust](./contents/security/README.md#incident--recovery--trust), `[catalog]` [Browser / Session Troubleshooting Path](./contents/security/README.md#browser--session-troubleshooting-path), `[cross-category bridge]` [Session / Boundary / Replay](./contents/security/README.md#session--boundary--replay), `[cross-category bridge]` [Identity / Delegation / Lifecycle](./contents/security/README.md#identity--delegation--lifecycle), `[catalog]` [AuthZ / Tenant / Response Contracts deep dive catalog](./contents/security/README.md#authz--tenant--response-contracts-deep-dive-catalog)이 topic map의 security symptom cluster label과 같은 이름으로 맞춰진 root entrypoint다.
- `incident badge snapshot`: security category README와 같은 기준으로 `[playbook]` / `[runbook]` / `[drill]` / `[incident matrix]` / `[recovery]` badge를 읽는다. follow-up에서도 `[deep dive]` / `[cross-category bridge]` / `[system design]` cue를 다시 붙여 다음 handoff를 고른다.
- `[playbook]` [JWT Signature Verification Failure Playbook](./contents/security/jwt-signature-verification-failure-playbook.md), `[runbook]` [Key Rotation Runbook](./contents/security/key-rotation-runbook.md), `[playbook]` [Signing Key Compromise Recovery Playbook](./contents/security/signing-key-compromise-recovery-playbook.md), `[drill]` [JWT / JWKS Outage Recovery / Failover Drills](./contents/security/jwt-jwks-outage-recovery-failover-drills.md), `[incident matrix]` [Auth Incident Triage / Blast-Radius Recovery Matrix](./contents/security/auth-incident-triage-blast-radius-recovery-matrix.md)
- `[recovery]` [JWKS Rotation Cutover Failure / Recovery](./contents/security/jwks-rotation-cutover-failure-recovery.md), [BFF Session Store Outage / Degradation Recovery](./contents/security/bff-session-store-outage-degradation-recovery.md), [Replay Store Outage / Degradation Recovery](./contents/security/replay-store-outage-degradation-recovery.md), [Hardware Attestation Policy / Failure Recovery](./contents/security/hardware-attestation-policy-failure-recovery.md)
- `follow-up role cue`: `[deep dive]` [JWK Rotation / Cache Invalidation / `kid` Rollover](./contents/security/jwk-rotation-cache-invalidation-kid-rollover.md), `[deep dive]` [Revocation Propagation Lag / Debugging](./contents/security/revocation-propagation-lag-debugging.md), `[catalog]` [Browser / Session Troubleshooting Path](./contents/security/README.md#browser--session-troubleshooting-path), `[cross-category bridge]` [Incident / Recovery / Trust](./contents/security/README.md#incident--recovery--trust), `[cross-category bridge]` [Session / Boundary / Replay](./contents/security/README.md#session--boundary--replay), `[cross-category bridge]` [Identity / Delegation / Lifecycle](./contents/security/README.md#identity--delegation--lifecycle), `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](./contents/spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md), `[system design]` [System Design: Auth Session Troubleshooting Bridge](./contents/system-design/README.md#system-design-auth-session-troubleshooting-bridge), `[system design]` [System Design: Control Plane / Data Plane Separation](./contents/system-design/control-plane-data-plane-separation-design.md), `[system design]` [System Design: Database / Security Identity Bridge Cutover 설계](./contents/system-design/database-security-identity-bridge-cutover-design.md)

[🔝 목차로 돌아가기](#table-of-contents)

## Language

### [📖 언어 README](./contents/language/README.md) (`category navigator` snapshot)

- Java
  - Runtime / diagnostics: JVM / GC / JMM, G1 vs ZGC, JIT, JFR-JMC / event interpretation, thread dump / jcmd, async-profiler vs JFR, safepoint, OOM, off-heap, classloader leak
  - Concurrency / async: 동시성 유틸리티, Java Memory Model, jcstress / happens-before 검증, executor sizing / queue / rejection, common pool / CompletableFuture, structured concurrency / virtual threads
  - Concurrency quick links: [executor / common pool](./contents/language/README.md#java-concurrency-executor--common-pool-cluster), [cancellation / context propagation](./contents/language/README.md#java-concurrency-cancellation--context-propagation-cluster), [Loom / structured concurrency](./contents/language/README.md#java-concurrency-loom--structured-concurrency-cluster)
  - Serialization / payload contracts: IO-NIO, native serialization evolution, JSON null-missing-unknown field, enum / record evolution
  - Language / boundary design: 불변 객체, equals-hashCode-compareTo, parsing / numeric boundaries, reflection / generics / records / sealed
- C++

[🔝 목차로 돌아가기](#table-of-contents)
