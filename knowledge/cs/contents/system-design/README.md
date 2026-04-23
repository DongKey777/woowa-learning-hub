# System Design

**난이도: 🔴 Advanced**

> 대규모 시스템 설계 면접 핵심 주제 모음

> retrieval-anchor-keywords: system design catalog, system design interview, system design foundations, request path failure modes, request deadline and timeout budget primer, timeout budget primer, client timeout budget, app timeout budget, cache timeout fallback, db timeout budget, partial failure retry storm, deadline ladder, cache outage primer, queue outage primer, app instance failure primer, database outage primer, failure absorption order, read-only mode, graceful degradation patterns, stale-if-error, partial feature disablement, brownout pattern, database incident read-only, cache incident stale read, stateless sessions primer, sticky session, external session store, token-based auth, load balancer drain and affinity primer, load balancer health check basics, connection draining, deregistration delay, sticky affinity deploy tail, sticky affinity failover, session revocation basics, logout basics, logout propagation basics, short-lived access token basics, token lifecycle state, database scaling primer, caching vs read replica, cache vs replica, cache invalidation basics, stale read basics, read-after-write consistency basics, read-after-write routing primer, mixed cache replica read path, mixed cache+replica read path pitfalls, dual stale source, cache miss stale replica, stale refill from replica, source selection rules, freshness routing observability, read your writes basics, primary replica basics, primary fallback, session stickiness, session pinning primer, monotonic reads primer, strong read consistency, read write split, indexing basics, partitioning vs sharding, shard key selection basics, partition key basics, hot partition detection, tenant key sharding pitfall, user key sharding pitfall, load balancer basics, horizontal scaling intuition, stateless app, cache database queue basics, learning tracks, migration cutover, replay repair, control plane, stateful platform, consistency, reliability, observability, dual read verification, cdc outbox, auth failover, session store, security bridge, security + system design route, spring + security route, database security bridge, identity / delegation / lifecycle route, identity / authority transfer bridge, authority transfer / security bridge, database / security authority bridge, verification / shadowing / authority bridge, authority route parity, database + system design route, database + security + system design route, design pattern / read model + database + system design route, identity capability rollout, auth shadow evaluation, backfill verification, analytics correction, dashboard restatement ux, alert reevaluation after backfill, projection freshness slo, read model cutover guardrail, session revocation, claim version cutover, session store migration, revocation cleanup timing, revocation bus regional lag, revoke redrive, cache invalidation replay, canonical revocation plane, token generation coexistence, generation-aware revoke fan-out, alias projection backlog, family quarantine release gate, tenant split out, dedicated cell migration, dedicated cell promotion verification ladder, mirrored traffic dual read auth drift, workload identity allowlist, SPIFFE allowlist, SPIFFE trust bundle overlap, SPIRE bundle propagation, trust bundle rollback, mesh trust root rotation, auth drift soak, verification cluster, traffic shadowing bridge, decision parity, shadow evaluation path, shadow exit signal, parity exit signal, verification evidence chain, jwks overlap reading order, verifier overlap, verifier overlap end threshold, legacy parser hard reject threshold, parser dark observe, unexpected legacy claim, workload identity rollout, hard reject timing, capability sunset gate matrix, capability overlap soak cleanup, dark deny probe, sunset silence window, bridge sunset ladder, verifier overlap hard reject retirement gates, bounded fallback retirement, overlap drained cutoff, scoped reject canary, emergency re-enable handle, cleanup handoff before code deletion, spring security session boundary, request cache login loop, 302 login loop, browser bff session troubleshooting, browser session troubleshooting path, logout tail, revocation tail, refresh family rotation cutover, refresh exchange idempotency, refresh exchange lease, duplicate response replay, same-context duplicate, cross-context duplicate, refresh reauth escalation matrix, silent refresh migration, refresh step-up, full reauthentication during migration, forced refresh reissue, mixed-version auth rollout, replay containment during migration, edge verifier claim skew fallback, unknown claim handling, origin introspection fallback, fallback storm, overlap window latency budget, tenant move background path hygiene, tenant caller class rollout matrix, foreground background caller checklist, principal issuance checklist, caller class allowlist checklist, caller class drift soak, stale route cache drain, legacy principal drain, replay worker route cache, support tooling route hygiene, search indexer cutover hygiene, webhook sender principal rollover, dedicated cell drain, shared cell retirement, rollback closure after tenant split out, bridge cluster toc, security incident bundle toc, auth session bridge toc, authority bridge toc, verification shadowing auth bridge toc, decommission retirement cluster, bridge sunset quick navigation, irreversible cleanup path, compatibility bridge sunset, retirement rollback closure, destructive cleanup gate, donor drain retirement bundle, hardware trust recovery bundle, replay session defense bundle, service delegation boundary bundle, hardware attestation recovery, trust bundle recovery, replay store down, nonce store down, acting on behalf of, delegated admin, support access notification, break glass, cleanup evidence, retirement evidence, scim reconciliation close, decision log join key, audit hold evidence, bridge retirement evidence packet, database repair signals, security tail signals, retirement approval packet, repair before cleanup, session auth gate path, verification ladder, read parity gate, revoke propagation parity, auth shadow exit criteria, system design drill label, system design incident matrix label, system design recovery label, mixed incident catalog, mixed incident bridge, inline badge normalization

<details>
<summary>Table of Contents</summary>

- [빠른 탐색](#빠른-탐색)
- [Security / System-Design Incident Bridge](#system-design-security-incident-bridge)
- [Auth Session Troubleshooting Bridge](#system-design-auth-session-troubleshooting-bridge)
- [Database / Security Authority Bridge](#system-design-database-security-authority-bridge)
- [Capability Rollout Deepening](#system-design-capability-rollout-deepening)
- [Verification / Shadowing / Authority Bridge](#system-design-verification-shadowing-authority-bridge)
- [Decommission / Retirement Cluster](#system-design-decommission-retirement-cluster)
- [카테고리 목차](#카테고리-목차)
- [학습 순서 추천](#학습-순서-추천)
- [심화 트랙 추천](#심화-트랙-추천)
- [참고](#참고)

</details>

## 빠른 탐색

이 `README`는 system design primer와 advanced catalog를 함께 묶는 **navigator 문서**다.
mixed bridge/catalog에서는 `[drill]`, `[incident matrix]`, `[recovery]` badge로 incident-oriented 문서를 구분하고, 라벨이 없는 항목은 system-design `deep dive`로 읽는다.

- survey / primer부터 읽고 싶다면:
  - [System Design Foundations](./system-design-foundations.md)
  - [Request Path Failure Modes Primer](./request-path-failure-modes-primer.md)
  - [Request Deadline and Timeout Budget Primer](./request-deadline-timeout-budget-primer.md)
  - [Retry Amplification and Backpressure Primer](./retry-amplification-and-backpressure-primer.md)
  - [Read-Only and Graceful Degradation Patterns](./read-only-and-graceful-degradation-patterns.md)
  - [Stateless Sessions Primer](./stateless-sessions-primer.md)
  - [Load Balancer Drain and Affinity Primer](./load-balancer-drain-and-affinity-primer.md)
  - [Browser BFF Session Boundary Primer](./browser-bff-session-boundary-primer.md)
  - [Session Revocation Basics](./session-revocation-basics.md)
  - [Database Scaling Primer](./database-scaling-primer.md)
  - [Shard Key Selection Basics](./shard-key-selection-basics.md)
  - [Caching vs Read Replica Primer](./caching-vs-read-replica-primer.md)
  - [Cache Invalidation Patterns Primer](./cache-invalidation-patterns-primer.md)
  - [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md)
  - [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
  - [시스템 설계 면접 프레임워크](./system-design-framework.md)
  - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
- 🟢 Beginner 입문 문서 (새로 추가):
  - [API Gateway 기초](./api-gateway-basics.md)
  - [Rate Limiting 기초](./rate-limiting-basics.md)
  - [CDN 기초](./cdn-basics.md)
  - [가용성과 SLA/SLO/SLI 기초](./availability-and-sla-basics.md)
  - [Circuit Breaker 기초](./circuit-breaker-basics.md)
  - [로드 밸런서 기초](./load-balancer-basics.md)
  - [메시지 큐 기초](./message-queue-basics.md)
  - [캐시 기초](./caching-basics.md)
  - [수평 확장과 수직 확장 기초](./horizontal-vs-vertical-scaling-basics.md)
  - [Stateless vs Stateful 서비스 기초](./stateless-vs-stateful-basics.md)
- 대표 사례형 설계부터 읽고 싶다면:
  - [URL 단축기 설계](./url-shortener-design.md)
  - [Rate Limiter 설계](./rate-limiter-design.md)
  - [분산 캐시 설계](./distributed-cache-design.md)
  - [Payment System / Ledger / Idempotency / Reconciliation](./payment-system-ledger-idempotency-reconciliation-design.md)
- migration / replay / cutover cluster로 바로 들어가려면:
  - [Change Data Capture / Outbox Relay](./change-data-capture-outbox-relay-design.md)
  - [Historical Backfill / Replay Platform](./historical-backfill-replay-platform-design.md)
  - [Dual-Write Avoidance / Migration Bridge](./dual-write-avoidance-migration-bridge-design.md)
  - [Zero-Downtime Schema Migration Platform](./zero-downtime-schema-migration-platform-design.md)
  - [Traffic Shadowing / Progressive Cutover](./traffic-shadowing-progressive-cutover-design.md)
  - [Dual-Read Comparison / Verification Platform](./dual-read-comparison-verification-platform-design.md)
  - [Tenant Split-Out with Service Identity Rollout](./tenant-split-out-service-identity-rollout-design.md)
  - [Dedicated Cell Drain and Retirement](./dedicated-cell-drain-retirement-design.md)
- analytics correction / restatement cluster로 바로 들어가려면:
  - [Historical Backfill / Replay Platform](./historical-backfill-replay-platform-design.md)
  - [Analytics Late Data Reconciliation](./analytics-late-data-reconciliation-design.md)
  - [Dashboard Restatement UX](./dashboard-restatement-ux-design.md)
  - [Alert Re-Evaluation / Correction](./alert-reevaluation-correction-design.md)
- [Security + System Design](../../rag/cross-domain-bridge-map.md#security--system-design) route로 바로 들어가려면:
  - [Security / System-Design Incident Bridge](#system-design-security-incident-bridge)
  - [Security: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path)
  - [Security: Hardware Trust / Recovery deep dive catalog](../security/README.md#hardware-trust--recovery-deep-dive-catalog)
  - [Security: Replay / Token Misuse / Session Defense deep dive catalog](../security/README.md#replay--token-misuse--session-defense-deep-dive-catalog)
- [Spring + Security](../../rag/cross-domain-bridge-map.md#spring--security) route로 바로 들어가려면:
  - [Auth Session Troubleshooting Bridge](#system-design-auth-session-troubleshooting-bridge)
  - [Security: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path)
  - [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
  - [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md)
- decommission / retirement / irreversible cleanup cluster로 바로 들어가려면:
  - [Decommission / Retirement Cluster](#system-design-decommission-retirement-cluster)
  - [Verifier Overlap Hard-Reject Retirement Gates](./verifier-overlap-hard-reject-retirement-gates-design.md)
  - [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md)
  - [Capability Sunset Gate Matrix](./capability-sunset-gate-matrix-design.md)
  - [Adapter Retirement / Compatibility Bridge Decommission](./adapter-retirement-compatibility-bridge-decommission-design.md)
  - [Dedicated Cell Drain and Retirement](./dedicated-cell-drain-retirement-design.md)
  - [Cleanup Point-of-No-Return](./cleanup-point-of-no-return-design.md)
- [Database + Security + System Design](../../rag/cross-domain-bridge-map.md#database--security--system-design) route로 바로 들어가려면:
  - [Database: Identity / Authority Transfer 브리지](../database/README.md#database-bridge-identity-authority)
  - [Security: Identity / Delegation / Lifecycle](../security/README.md#identity--delegation--lifecycle)
  - [Database / Security Authority Bridge](#system-design-database-security-authority-bridge)
  - [Verification / Shadowing / Authority Bridge](#system-design-verification-shadowing-authority-bridge)
- [Database + System Design](../../rag/cross-domain-bridge-map.md#database--system-design) route부터 잡고 싶다면:
  - [Database Scaling Primer](./database-scaling-primer.md)
  - [Shard Key Selection Basics](./shard-key-selection-basics.md)
  - [Caching vs Read Replica Primer](./caching-vs-read-replica-primer.md)
  - [Cache Invalidation Patterns Primer](./cache-invalidation-patterns-primer.md)
  - [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md)
  - [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
  - [Mixed Cache+Replica Read Path Pitfalls](./mixed-cache-replica-read-path-pitfalls.md)
  - [Change Data Capture / Outbox Relay](./change-data-capture-outbox-relay-design.md)
  - [Dual-Read Comparison / Verification Platform](./dual-read-comparison-verification-platform-design.md)
  - [Database: Schema Migration, Partitioning, CDC, CQRS](../database/schema-migration-partitioning-cdc-cqrs.md)
- [Design Pattern / Read Model + Database + System Design](../../rag/cross-domain-bridge-map.md#design-pattern--read-model--database--system-design) route로 확장하려면:
  - [Design Pattern: Read Model Staleness and Read-Your-Writes](../design-pattern/read-model-staleness-read-your-writes.md)
  - [Design Pattern: Read Model Cutover Guardrails](../design-pattern/read-model-cutover-guardrails.md)
  - [Design Pattern: Projection Freshness SLO Pattern](../design-pattern/projection-freshness-slo-pattern.md)
  - [Database: Incremental Summary Table Refresh and Watermark Discipline](../database/incremental-summary-table-refresh-watermark.md)

<a id="system-design-security-incident-bridge"></a>
### Security / System-Design Incident Bridge

보안 incident 대응과 system design 운영 경계를 한 묶음으로 훑을 때 바로 내려오는 subsection이다.

  - `[incident matrix]` [Security: Auth Incident Triage / Blast-Radius Recovery Matrix](../security/auth-incident-triage-blast-radius-recovery-matrix.md)
  - `[drill]` [Security: JWT / JWKS Outage Recovery / Failover Drills](../security/jwt-jwks-outage-recovery-failover-drills.md)
  - [Security: Hardware Trust / Recovery deep dive catalog](../security/README.md#hardware-trust--recovery-deep-dive-catalog)
  - [Security: Replay / Token Misuse / Session Defense deep dive catalog](../security/README.md#replay--token-misuse--session-defense-deep-dive-catalog)
  - [Service Discovery / Health Routing](./service-discovery-health-routing-design.md)
  - [Session Store Design at Scale](./session-store-design-at-scale.md)
  - [Session Store / Claim-Version Cutover](./session-store-claim-version-cutover-design.md)
  - [Canonical Revocation Plane Across Token Generations](./canonical-revocation-plane-across-token-generations-design.md)
  - `[recovery]` [Revocation Bus Regional Lag Recovery](./revocation-bus-regional-lag-recovery-design.md)
  - [Edge Verifier Claim-Skew Fallback](./edge-verifier-claim-skew-fallback-design.md)
  - [Refresh-Family Rotation Cutover](./refresh-family-rotation-cutover-design.md)
  - [Refresh Exchange Idempotency Under Cutover](./refresh-exchange-idempotency-under-cutover-design.md)
  - [Refresh Reauth Escalation Matrix](./refresh-reauth-escalation-matrix-design.md)
  - [Global Traffic Failover Control Plane](./global-traffic-failover-control-plane-design.md)

<a id="system-design-auth-session-troubleshooting-bridge"></a>
### Auth Session Troubleshooting Bridge

security README의 [Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path)에서 browser/session symptom을 먼저 갈라 본 뒤, system-design 원인까지 내려갈 때 쓰는 subsection이다.
여기서는 session-store 문서로 바로 넘기지 말고 `SavedRequest loop`와 `hidden session mismatch`를 먼저 갈라서 읽는다.

1. `SavedRequest loop`
   - 로그인은 성공한 것 같은데 같은 보호 URL로 다시 튀거나 `401 -> 302 -> /login` bounce, login HTML 응답, 숨은 `JSESSIONID`가 redirect 직후에만 보일 때 본다.
   - 순서: [Security: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path) -> [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md) -> [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
   - 이 branch는 redirect 복귀와 hidden session 생성 경계가 핵심이므로, browser cookie는 남아 있는데 서버측 session/token translation이 실제로 사라졌다는 증거가 잡히기 전에는 [Session Store Design at Scale](./session-store-design-at-scale.md)로 바로 내려가지 않는다.

2. `hidden session mismatch`
   - cookie는 살아 있는데 서버가 session/token translation을 못 찾거나, node/region별로 login 상태가 흔들리고, logout은 되는데 일부 BFF/downstream 호출만 계속 통과할 때 본다.
   - 순서: [Security: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path) -> [Security: Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md) -> `[recovery]` [Security: BFF Session Store Outage / Degradation Recovery](../security/bff-session-store-outage-degradation-recovery.md) -> [Browser BFF Session Boundary Primer](./browser-bff-session-boundary-primer.md) -> [Stateless Sessions Primer](./stateless-sessions-primer.md) -> [Session Store Design at Scale](./session-store-design-at-scale.md)
   - claim semantic, authority migration, mixed-version rollout이 같이 묶이면 [Session Store / Claim-Version Cutover](./session-store-claim-version-cutover-design.md)까지 이어 붙인다.

3. `revoke tail`
   - mismatch가 아니라 revoke propagation, logout tail, claim-version cleanup tail로 확인되면 아래 순서로 내려간다.
   - 순서: [Session Revocation Basics](./session-revocation-basics.md) -> [Security: Session Revocation at Scale](../security/session-revocation-at-scale.md) -> [Security: Revocation Propagation Lag / Debugging](../security/revocation-propagation-lag-debugging.md) -> [Canonical Revocation Plane Across Token Generations](./canonical-revocation-plane-across-token-generations-design.md) -> `[recovery]` [Revocation Bus Regional Lag Recovery](./revocation-bus-regional-lag-recovery-design.md)

<a id="system-design-database-security-authority-bridge"></a>
### Database / Security Authority Bridge

database authority 이동과 identity capability rollout이 같이 얽힌 cutover를 추적할 때 쓰는 subsection이다. security README의 `Identity / Delegation / Lifecycle`, database README의 `Identity / Authority Transfer 브리지` / `Authority Transfer / Security Bridge`에서 넘어오는 같은 authority-transfer route를 system-design handoff 이름으로 받는 구간이다.
category README bridge entrypoint를 같이 맞추려면 `[cross-category bridge]` [Database: Identity / Authority Transfer 브리지](../database/README.md#database-bridge-identity-authority), `[cross-category bridge]` [Security: Identity / Delegation / Lifecycle](../security/README.md#identity--delegation--lifecycle)를 먼저 열고, parity/retirement evidence까지 넘길 때는 아래 `[system design]` [Verification / Shadowing / Authority Bridge](#system-design-verification-shadowing-authority-bridge)로 이어 붙인다. paired subsection 사이를 왕복할 때는 system-design 문서에 `[system design]`, security deep dive나 catalog로 되돌아가는 지점에 `[deep dive]` / `[catalog]` cue를 다시 붙여 앞 링크 badge가 뒤 링크로 암묵 상속되지 않게 유지한다.

  - `[system design]` [Database / Security Identity Bridge Cutover](./database-security-identity-bridge-cutover-design.md)
  - `[catalog]` [Security: Service / Delegation Boundaries deep dive catalog](../security/README.md#service--delegation-boundaries-deep-dive-catalog)
  - `[system design]` [Tenant Split-Out with Service Identity Rollout](./tenant-split-out-service-identity-rollout-design.md)
  - `[system design]` [Dedicated Cell Drain and Retirement](./dedicated-cell-drain-retirement-design.md)
  - `[system design]` [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md)
  - `[system design]` [Trust-Bundle Rollback During Cell Cutover](./trust-bundle-rollback-during-cell-cutover-design.md)
  - `[deep dive]` [Security: SCIM Drift / Reconciliation](../security/scim-drift-reconciliation.md)
  - `[system design]` [Session Store / Claim-Version Cutover](./session-store-claim-version-cutover-design.md)
  - `[system design]` [Edge Verifier Claim-Skew Fallback](./edge-verifier-claim-skew-fallback-design.md)
  - `[system design]` [Refresh-Family Rotation Cutover](./refresh-family-rotation-cutover-design.md)
  - `[system design]` [Zero-Downtime Schema Migration Platform](./zero-downtime-schema-migration-platform-design.md)
  - `[system design]` [Capability Negotiation / Feature Gating](./capability-negotiation-feature-gating-design.md)
  - `[deep dive]` [Database: Online Backfill Verification, Drift Checks, and Cutover Gates](../database/online-backfill-verification-cutover-gates.md)
  - `[deep dive]` [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)
  - `[deep dive]` [Security: AuthZ Decision Logging Design](../security/authz-decision-logging-design.md)
  - `[deep dive]` [Security: Audit Logging for Auth / AuthZ Traceability](../security/audit-logging-auth-authz-traceability.md)
  - `[drill]` [Security: JWT / JWKS Outage Recovery / Failover Drills](../security/jwt-jwks-outage-recovery-failover-drills.md)

<a id="system-design-capability-rollout-deepening"></a>
### Capability Rollout Deepening

mixed-version auth rollout, verifier overlap, capability gating 순서를 깊게 따라가고 싶을 때 쓰는 subsection이다.

  - [Capability Negotiation / Feature Gating](./capability-negotiation-feature-gating-design.md)
  - [Edge Verifier Claim-Skew Fallback](./edge-verifier-claim-skew-fallback-design.md)
  - [Refresh-Family Rotation Cutover](./refresh-family-rotation-cutover-design.md)
  - [Refresh Exchange Idempotency Under Cutover](./refresh-exchange-idempotency-under-cutover-design.md)
  - [Canonical Revocation Plane Across Token Generations](./canonical-revocation-plane-across-token-generations-design.md)
  - [Refresh Reauth Escalation Matrix](./refresh-reauth-escalation-matrix-design.md)
  - [Verifier Overlap Hard-Reject Retirement Gates](./verifier-overlap-hard-reject-retirement-gates-design.md)
  - [Security: MFA / Step-Up Auth Design](../security/mfa-step-up-auth-design.md)
  - [Security: Step-Up Session Coherence / Auth Assurance](../security/step-up-session-coherence-auth-assurance.md)
  - `[drill]` [Security: JWT / JWKS Outage Recovery / Failover Drills](../security/jwt-jwks-outage-recovery-failover-drills.md)
  - [Tenant Split-Out with Service Identity Rollout](./tenant-split-out-service-identity-rollout-design.md)
  - [Database / Security Identity Bridge Cutover](./database-security-identity-bridge-cutover-design.md)
  - [Adapter Retirement / Compatibility Bridge Decommission](./adapter-retirement-compatibility-bridge-decommission-design.md)

<a id="system-design-verification-shadowing-authority-bridge"></a>
### Verification / Shadowing / Authority Bridge

read parity, revoke propagation, auth shadow evaluation, authority transfer를 한 흐름으로 묶고 그 근거를 retirement/cleanup gate까지 넘겨 보고 싶을 때 쓰는 subsection이다. 같은 authority-transfer route를 late-stage verification / cleanup 이름으로 다시 부르는 handoff라서, security/database README의 sibling label과 함께 보존해야 retrieval route가 끊기지 않는다.
database/security 쪽 navigator parity를 유지하려면 `[cross-category bridge]` [Database: Identity / Authority Transfer 브리지](../database/README.md#database-bridge-identity-authority), `[cross-category bridge]` [Security: Identity / Delegation / Lifecycle](../security/README.md#identity--delegation--lifecycle), 위 `[system design]` [Database / Security Authority Bridge](#system-design-database-security-authority-bridge)를 함께 본다. 이 paired subsection도 system-design 설계 문서에는 `[system design]`, security deep dive로 hand back하는 지점에는 `[deep dive]` cue를 다시 붙여 reciprocity를 맞춘다.

  - `[system design]` [Traffic Shadowing / Progressive Cutover](./traffic-shadowing-progressive-cutover-design.md)
  - `[system design]` [Dual-Read Comparison / Verification Platform](./dual-read-comparison-verification-platform-design.md)
  - `[system design]` [Session Store / Claim-Version Cutover](./session-store-claim-version-cutover-design.md)
  - `[system design]` [Verifier Overlap Hard-Reject Retirement Gates](./verifier-overlap-hard-reject-retirement-gates-design.md)
  - `[recovery]` [Revocation Bus Regional Lag Recovery](./revocation-bus-regional-lag-recovery-design.md)
  - `[deep dive]` [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)
  - `[system design]` [Database / Security Identity Bridge Cutover](./database-security-identity-bridge-cutover-design.md)
  - `[system design]` [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md)
  - `[system design]` [Adapter Retirement / Compatibility Bridge Decommission](./adapter-retirement-compatibility-bridge-decommission-design.md)
  - `[system design]` [Cleanup Point-of-No-Return](./cleanup-point-of-no-return-design.md)
  - `[system design]` [Tenant Split-Out with Service Identity Rollout](./tenant-split-out-service-identity-rollout-design.md)

<a id="system-design-decommission-retirement-cluster"></a>
### Decommission / Retirement Cluster

bridge sunset, rollback closure, destructive cleanup 같은 종료 단계 문서를 한 번에 찾고 싶고 bridge removal 전에 shadow/parity exit signal chain까지 함께 닫고 싶을 때 쓰는 subsection이다.

  - [Database / Security Identity Bridge Cutover](./database-security-identity-bridge-cutover-design.md)
  - [Session Store / Claim-Version Cutover](./session-store-claim-version-cutover-design.md)
  - [Verifier Overlap Hard-Reject Retirement Gates](./verifier-overlap-hard-reject-retirement-gates-design.md)
  - [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md)
  - [Capability Sunset Gate Matrix](./capability-sunset-gate-matrix-design.md)
  - [Adapter Retirement / Compatibility Bridge Decommission](./adapter-retirement-compatibility-bridge-decommission-design.md)
  - [Dedicated Cell Drain and Retirement](./dedicated-cell-drain-retirement-design.md)
  - [Cleanup Point-of-No-Return](./cleanup-point-of-no-return-design.md)
  - [Deploy Rollback Safety / Compatibility Envelope](./deploy-rollback-safety-compatibility-envelope-design.md)
  - [Write-Freeze Rollback Window](./write-freeze-rollback-window-design.md)
  - [Trust-Bundle Rollback During Cell Cutover](./trust-bundle-rollback-during-cell-cutover-design.md)

## 카테고리 목차

| # | 주제 | 난이도 | 파일 |
|---|------|--------|------|
| 1 | 시스템 설계 면접 프레임워크 | 🟢 Basic | [system-design-framework.md](system-design-framework.md) |
| 2 | Back-of-Envelope 추정법 | 🟢 Basic | [back-of-envelope-estimation.md](back-of-envelope-estimation.md) |
| 3 | URL 단축기 설계 | 🟡 Intermediate | [url-shortener-design.md](url-shortener-design.md) |
| 4 | Rate Limiter 설계 | 🟡 Intermediate | [rate-limiter-design.md](rate-limiter-design.md) |
| 5 | 분산 캐시 설계 | 🔴 Advanced | [distributed-cache-design.md](distributed-cache-design.md) |
| 6 | 채팅 시스템 설계 | 🔴 Advanced | [chat-system-design.md](chat-system-design.md) |
| 7 | Newsfeed 시스템 설계 | 🔴 Advanced | [newsfeed-system-design.md](newsfeed-system-design.md) |
| 8 | Notification 시스템 설계 | 🔴 Advanced | [notification-system-design.md](notification-system-design.md) |
| 9 | Consistent Hashing / Hot Key 전략 | 🔴 Advanced | [consistent-hashing-hot-key-strategies.md](consistent-hashing-hot-key-strategies.md) |
| 10 | Distributed Lock 설계 | 🔴 Advanced | [distributed-lock-design.md](distributed-lock-design.md) |
| 11 | Search 시스템 설계 | 🔴 Advanced | [search-system-design.md](search-system-design.md) |
| 12 | File Storage / Presigned URL / CDN | 🔴 Advanced | [file-storage-presigned-url-cdn-design.md](file-storage-presigned-url-cdn-design.md) |
| 13 | Workflow Orchestration / Saga | 🔴 Advanced | [workflow-orchestration-saga-design.md](workflow-orchestration-saga-design.md) |
| 14 | 멀티 테넌트 SaaS 격리 설계 | 🔴 Advanced | [multi-tenant-saas-isolation-design.md](multi-tenant-saas-isolation-design.md) |
| 15 | Payment System / Ledger / Idempotency / Reconciliation | 🔴 Advanced | [payment-system-ledger-idempotency-reconciliation-design.md](payment-system-ledger-idempotency-reconciliation-design.md) |
| 16 | Idempotency Key Store / Dedup Window / Replay-Safe Retry | 🔴 Advanced | [idempotency-key-store-dedup-window-replay-safe-retry-design.md](idempotency-key-store-dedup-window-replay-safe-retry-design.md) |
| 17 | Change Data Capture / Outbox Relay | 🔴 Advanced | [change-data-capture-outbox-relay-design.md](change-data-capture-outbox-relay-design.md) |
| 18 | Historical Backfill / Replay Platform | 🔴 Advanced | [historical-backfill-replay-platform-design.md](historical-backfill-replay-platform-design.md) |
| 19 | Zero-Downtime Schema Migration Platform | 🔴 Advanced | [zero-downtime-schema-migration-platform-design.md](zero-downtime-schema-migration-platform-design.md) |
| 20 | Service Discovery / Health Routing | 🔴 Advanced | [service-discovery-health-routing-design.md](service-discovery-health-routing-design.md) |
| 21 | Distributed Tracing Pipeline | 🔴 Advanced | [distributed-tracing-pipeline-design.md](distributed-tracing-pipeline-design.md) |
| 22 | `[drill]` Backup, Restore, Disaster Recovery Drill | 🔴 Advanced | [backup-restore-disaster-recovery-drill-design.md](backup-restore-disaster-recovery-drill-design.md) |
| 23 | Traffic Shadowing / Progressive Cutover | 🔴 Advanced | [traffic-shadowing-progressive-cutover-design.md](traffic-shadowing-progressive-cutover-design.md) |
| 24 | Consistency Repair / Anti-Entropy Platform | 🔴 Advanced | [consistency-repair-anti-entropy-platform-design.md](consistency-repair-anti-entropy-platform-design.md) |
| 25 | Shard Rebalancing / Partition Relocation | 🔴 Advanced | [shard-rebalancing-partition-relocation-design.md](shard-rebalancing-partition-relocation-design.md) |
| 26 | Stateful Stream Processor State Store / Checkpoint Recovery | 🔴 Advanced | [stateful-stream-processor-state-store-checkpoint-recovery-design.md](stateful-stream-processor-state-store-checkpoint-recovery-design.md) |
| 27 | Automated Canary Analysis / Rollback Platform | 🔴 Advanced | [automated-canary-analysis-rollback-platform-design.md](automated-canary-analysis-rollback-platform-design.md) |
| 28 | Dual-Read Comparison / Verification Platform | 🔴 Advanced | [dual-read-comparison-verification-platform-design.md](dual-read-comparison-verification-platform-design.md) |
| 29 | Replay / Repair Orchestration Control Plane | 🔴 Advanced | [replay-repair-orchestration-control-plane-design.md](replay-repair-orchestration-control-plane-design.md) |
| 30 | Stateful Workload Placement / Failover Control Plane | 🔴 Advanced | [stateful-workload-placement-failover-control-plane-design.md](stateful-workload-placement-failover-control-plane-design.md) |
| 31 | Control Plane / Data Plane Separation | 🟡 Intermediate | [control-plane-data-plane-separation-design.md](control-plane-data-plane-separation-design.md) |
| 32 | Consensus Membership Reconfiguration | 🔴 Advanced | [consensus-membership-reconfiguration-design.md](consensus-membership-reconfiguration-design.md) |
| 33 | Service Mesh Control Plane | 🔴 Advanced | [service-mesh-control-plane-design.md](service-mesh-control-plane-design.md) |
| 34 | Failure Injection / Resilience Validation Platform | 🔴 Advanced | [failure-injection-resilience-validation-platform-design.md](failure-injection-resilience-validation-platform-design.md) |
| 35 | Global Traffic Failover Control Plane | 🔴 Advanced | [global-traffic-failover-control-plane-design.md](global-traffic-failover-control-plane-design.md) |
| 36 | Cell-Based Architecture / Blast Radius Isolation | 🔴 Advanced | [cell-based-architecture-blast-radius-isolation-design.md](cell-based-architecture-blast-radius-isolation-design.md) |
| 37 | Read / Write Quorum & Staleness Budget | 🔴 Advanced | [read-write-quorum-staleness-budget-design.md](read-write-quorum-staleness-budget-design.md) |
| 38 | Dual-Write Avoidance / Migration Bridge | 🔴 Advanced | [dual-write-avoidance-migration-bridge-design.md](dual-write-avoidance-migration-bridge-design.md) |
| 39 | Reconciliation Window / Cutoff Control | 🔴 Advanced | [reconciliation-window-cutoff-control-design.md](reconciliation-window-cutoff-control-design.md) |
| 40 | Tenant Partition Strategy / Reassignment | 🔴 Advanced | [tenant-partition-strategy-reassignment-design.md](tenant-partition-strategy-reassignment-design.md) |
| 41 | Deploy Rollback Safety / Compatibility Envelope | 🔴 Advanced | [deploy-rollback-safety-compatibility-envelope-design.md](deploy-rollback-safety-compatibility-envelope-design.md) |
| 42 | Receiver Warmup / Cache Prefill / Write Freeze Cutover | 🔴 Advanced | [receiver-warmup-cache-prefill-write-freeze-cutover-design.md](receiver-warmup-cache-prefill-write-freeze-cutover-design.md) |
| 43 | Config Rollback Safety | 🔴 Advanced | [config-rollback-safety-design.md](config-rollback-safety-design.md) |
| 44 | Protocol Version Skew / Compatibility | 🔴 Advanced | [protocol-version-skew-compatibility-design.md](protocol-version-skew-compatibility-design.md) |
| 45 | Cleanup Point-of-No-Return | 🔴 Advanced | [cleanup-point-of-no-return-design.md](cleanup-point-of-no-return-design.md) |
| 46 | Analytics Late Data Reconciliation | 🔴 Advanced | [analytics-late-data-reconciliation-design.md](analytics-late-data-reconciliation-design.md) |
| 47 | Capability Negotiation / Feature Gating | 🔴 Advanced | [capability-negotiation-feature-gating-design.md](capability-negotiation-feature-gating-design.md) |
| 48 | Adapter Retirement / Compatibility Bridge Decommission | 🔴 Advanced | [adapter-retirement-compatibility-bridge-decommission-design.md](adapter-retirement-compatibility-bridge-decommission-design.md) |
| 49 | Dashboard Restatement UX | 🔴 Advanced | [dashboard-restatement-ux-design.md](dashboard-restatement-ux-design.md) |
| 50 | Alert Re-Evaluation / Correction | 🔴 Advanced | [alert-reevaluation-correction-design.md](alert-reevaluation-correction-design.md) |
| 51 | `[recovery]` Tenant-Scoped Config Incident Recovery | 🔴 Advanced | [tenant-scoped-config-incident-recovery-design.md](tenant-scoped-config-incident-recovery-design.md) |
| 52 | Write-Freeze Rollback Window | 🔴 Advanced | [write-freeze-rollback-window-design.md](write-freeze-rollback-window-design.md) |
| 53 | Database / Security Identity Bridge Cutover | 🔴 Advanced | [database-security-identity-bridge-cutover-design.md](database-security-identity-bridge-cutover-design.md) |
| 54 | Session Store / Claim-Version Cutover | 🔴 Advanced | [session-store-claim-version-cutover-design.md](session-store-claim-version-cutover-design.md) |
| 55 | Tenant Split-Out with Service Identity Rollout | 🔴 Advanced | [tenant-split-out-service-identity-rollout-design.md](tenant-split-out-service-identity-rollout-design.md) |
| 56 | Refresh-Family Rotation Cutover | 🔴 Advanced | [refresh-family-rotation-cutover-design.md](refresh-family-rotation-cutover-design.md) |
| 57 | Refresh Exchange Idempotency Under Cutover | 🔴 Advanced | [refresh-exchange-idempotency-under-cutover-design.md](refresh-exchange-idempotency-under-cutover-design.md) |
| 58 | Edge Verifier Claim-Skew Fallback | 🔴 Advanced | [edge-verifier-claim-skew-fallback-design.md](edge-verifier-claim-skew-fallback-design.md) |
| 59 | Verifier Overlap Hard-Reject Retirement Gates | 🔴 Advanced | [verifier-overlap-hard-reject-retirement-gates-design.md](verifier-overlap-hard-reject-retirement-gates-design.md) |
| 60 | `[recovery]` Revocation Bus Regional Lag Recovery | 🔴 Advanced | [revocation-bus-regional-lag-recovery-design.md](revocation-bus-regional-lag-recovery-design.md) |
| 61 | Trust-Bundle Rollback During Cell Cutover | 🔴 Advanced | [trust-bundle-rollback-during-cell-cutover-design.md](trust-bundle-rollback-during-cell-cutover-design.md) |
| 62 | Dedicated Cell Drain and Retirement | 🔴 Advanced | [dedicated-cell-drain-retirement-design.md](dedicated-cell-drain-retirement-design.md) |
| 63 | Bridge Retirement Evidence Packet | 🔴 Advanced | [bridge-retirement-evidence-packet-design.md](bridge-retirement-evidence-packet-design.md) |
| 64 | Capability Sunset Gate Matrix | 🔴 Advanced | [capability-sunset-gate-matrix-design.md](capability-sunset-gate-matrix-design.md) |
| 65 | Refresh Reauth Escalation Matrix | 🔴 Advanced | [refresh-reauth-escalation-matrix-design.md](refresh-reauth-escalation-matrix-design.md) |
| 66 | Canonical Revocation Plane Across Token Generations | 🔴 Advanced | [canonical-revocation-plane-across-token-generations-design.md](canonical-revocation-plane-across-token-generations-design.md) |
| 67 | System Design Foundations | 🟢 Basic | [system-design-foundations.md](system-design-foundations.md) |
| 68 | Database Scaling Primer | 🟢 Basic | [database-scaling-primer.md](database-scaling-primer.md) |
| 69 | Stateless Sessions Primer | 🟢 Basic | [stateless-sessions-primer.md](stateless-sessions-primer.md) |
| 70 | Load Balancer Drain and Affinity Primer | 🟢 Basic | [load-balancer-drain-and-affinity-primer.md](load-balancer-drain-and-affinity-primer.md) |
| 71 | Browser BFF Session Boundary Primer | 🟢 Basic | [browser-bff-session-boundary-primer.md](browser-bff-session-boundary-primer.md) |
| 72 | Request Path Failure Modes Primer | 🟢 Basic | [request-path-failure-modes-primer.md](request-path-failure-modes-primer.md) |
| 73 | Request Deadline and Timeout Budget Primer | 🟢 Basic | [request-deadline-timeout-budget-primer.md](request-deadline-timeout-budget-primer.md) |
| 74 | Caching vs Read Replica Primer | 🟢 Basic | [caching-vs-read-replica-primer.md](caching-vs-read-replica-primer.md) |
| 75 | Cache Invalidation Patterns Primer | 🟢 Basic | [cache-invalidation-patterns-primer.md](cache-invalidation-patterns-primer.md) |
| 76 | Read-After-Write Consistency Basics | 🟢 Basic | [read-after-write-consistency-basics.md](read-after-write-consistency-basics.md) |
| 77 | Read-After-Write Routing Primer | 🟢 Basic | [read-after-write-routing-primer.md](read-after-write-routing-primer.md) |
| 78 | Shard Key Selection Basics | 🟢 Basic | [shard-key-selection-basics.md](shard-key-selection-basics.md) |
| 79 | Session Revocation Basics | 🟢 Basic | [session-revocation-basics.md](session-revocation-basics.md) |
| 80 | Read-Only and Graceful Degradation Patterns | 🟡 Intermediate | [read-only-and-graceful-degradation-patterns.md](read-only-and-graceful-degradation-patterns.md) |
| 81 | Retry Amplification and Backpressure Primer | 🟢 Basic | [retry-amplification-and-backpressure-primer.md](retry-amplification-and-backpressure-primer.md) |
| 82 | Mixed Cache+Replica Read Path Pitfalls | 🟡 Intermediate | [mixed-cache-replica-read-path-pitfalls.md](mixed-cache-replica-read-path-pitfalls.md) |

## 학습 순서 추천

아래 구간은 broad survey에 가깝고, 세부 설계 trade-off는 각 문서로 내려가서 읽는 편이 좋다.

```
System Design Foundations → Request Path Failure Modes Primer → Request Deadline and Timeout Budget Primer → Retry Amplification and Backpressure Primer → Read-Only and Graceful Degradation Patterns → Stateless Sessions Primer → Load Balancer Drain and Affinity Primer → Browser BFF Session Boundary Primer → Session Revocation Basics → Database Scaling Primer → Shard Key Selection Basics → Caching vs Read Replica Primer → Cache Invalidation Patterns Primer → Read-After-Write Consistency Basics → Read-After-Write Routing Primer → Mixed Cache+Replica Read Path Pitfalls → 프레임워크 → 추정법 → URL 단축기 → Rate Limiter → 분산 캐시 → Multi-tenant SaaS 격리 → Payment System / Ledger / Reconciliation → Idempotency Key Store / Replay-Safe Retry → Consistent Hashing → Newsfeed → Notification → 채팅 시스템 → Distributed Lock → Search → File Storage → Workflow
```

## 심화 트랙 추천

- 데이터 이동/동기화: [Change Data Capture / Outbox Relay](./change-data-capture-outbox-relay-design.md) → [Historical Backfill / Replay Platform](./historical-backfill-replay-platform-design.md) → [Search Indexing Pipeline](./search-indexing-pipeline-design.md) → [Event Bus Control Plane](./event-bus-control-plane-design.md)
- 무중단 구조 변경: [Zero-Downtime Schema Migration Platform](./zero-downtime-schema-migration-platform-design.md) → [Historical Backfill / Replay Platform](./historical-backfill-replay-platform-design.md) → [Search Indexing Pipeline](./search-indexing-pipeline-design.md)
- 런타임 네트워크/관측성: [Load Balancer Drain and Affinity Primer](./load-balancer-drain-and-affinity-primer.md) → [Service Discovery / Health Routing](./service-discovery-health-routing-design.md) → [Distributed Tracing Pipeline](./distributed-tracing-pipeline-design.md) → [Metrics Pipeline / TSDB](./metrics-pipeline-tsdb-design.md)
- 장애 복구/글로벌 운영: `[drill]` [Backup, Restore, Disaster Recovery Drill](./backup-restore-disaster-recovery-drill-design.md) → [Multi-Region Active-Active](./multi-region-active-active-design.md) → [Object Metadata Service](./object-metadata-service-design.md)
- 세션/로그아웃 라이프사이클 기초: [Stateless Sessions Primer](./stateless-sessions-primer.md) → [Load Balancer Drain and Affinity Primer](./load-balancer-drain-and-affinity-primer.md) → [Browser BFF Session Boundary Primer](./browser-bff-session-boundary-primer.md) → [Session Revocation Basics](./session-revocation-basics.md) → [Session Store Design at Scale](./session-store-design-at-scale.md)
- 안전한 컷오버/승격: [Traffic Shadowing / Progressive Cutover](./traffic-shadowing-progressive-cutover-design.md) → [API Gateway Control Plane](./api-gateway-control-plane-design.md) → [Feature Flag Control Plane](./feature-flag-control-plane-design.md) → [Service Discovery / Health Routing](./service-discovery-health-routing-design.md)
- 정합성 수리/복구: [Consistency Repair / Anti-Entropy Platform](./consistency-repair-anti-entropy-platform-design.md) → [Historical Backfill / Replay Platform](./historical-backfill-replay-platform-design.md) → [Payment System Ledger, Idempotency, Reconciliation](./payment-system-ledger-idempotency-reconciliation-design.md)
- 상태 운영/재배치: [Shard Rebalancing / Partition Relocation](./shard-rebalancing-partition-relocation-design.md) → [Consistent Hashing / Hot Key 전략](./consistent-hashing-hot-key-strategies.md) → [Stateful Stream Processor State Store / Checkpoint Recovery](./stateful-stream-processor-state-store-checkpoint-recovery-design.md)
- shard key / hot partition 기초: [Database Scaling Primer](./database-scaling-primer.md) → [Shard Key Selection Basics](./shard-key-selection-basics.md) → [Consistent Hashing / Hot Key 전략](./consistent-hashing-hot-key-strategies.md) → [Shard Rebalancing / Partition Relocation](./shard-rebalancing-partition-relocation-design.md)
- 검증 기반 read cutover: [Dual-Read Comparison / Verification Platform](./dual-read-comparison-verification-platform-design.md) → [Zero-Downtime Schema Migration Platform](./zero-downtime-schema-migration-platform-design.md) → [Traffic Shadowing / Progressive Cutover](./traffic-shadowing-progressive-cutover-design.md)
- verification / shadowing / auth bridge: [Traffic Shadowing / Progressive Cutover](./traffic-shadowing-progressive-cutover-design.md) → [Dual-Read Comparison / Verification Platform](./dual-read-comparison-verification-platform-design.md) → [Session Store / Claim-Version Cutover](./session-store-claim-version-cutover-design.md) → [Canonical Revocation Plane Across Token Generations](./canonical-revocation-plane-across-token-generations-design.md) → `[recovery]` [Revocation Bus Regional Lag Recovery](./revocation-bus-regional-lag-recovery-design.md) → [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md) → [Database / Security Identity Bridge Cutover](./database-security-identity-bridge-cutover-design.md) → [Tenant Split-Out with Service Identity Rollout](./tenant-split-out-service-identity-rollout-design.md)
- bridge retirement evidence chain: [Traffic Shadowing / Progressive Cutover](./traffic-shadowing-progressive-cutover-design.md) → [Dual-Read Comparison / Verification Platform](./dual-read-comparison-verification-platform-design.md) → [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md) → [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md) → [Adapter Retirement / Compatibility Bridge Decommission](./adapter-retirement-compatibility-bridge-decommission-design.md) → [Cleanup Point-of-No-Return](./cleanup-point-of-no-return-design.md)
- capability sunset ladder: [Capability Negotiation / Feature Gating](./capability-negotiation-feature-gating-design.md) → [Capability Sunset Gate Matrix](./capability-sunset-gate-matrix-design.md) → [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md) → [Adapter Retirement / Compatibility Bridge Decommission](./adapter-retirement-compatibility-bridge-decommission-design.md) → [Cleanup Point-of-No-Return](./cleanup-point-of-no-return-design.md)
- dedicated-cell 승격 검증 사다리: [Traffic Shadowing / Progressive Cutover](./traffic-shadowing-progressive-cutover-design.md) → [Dual-Read Comparison / Verification Platform](./dual-read-comparison-verification-platform-design.md) → [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md) → [Tenant Split-Out with Service Identity Rollout](./tenant-split-out-service-identity-rollout-design.md) → [Dedicated Cell Drain and Retirement](./dedicated-cell-drain-retirement-design.md)
- canary 운영 자동화: [Automated Canary Analysis / Rollback Platform](./automated-canary-analysis-rollback-platform-design.md) → [Traffic Shadowing / Progressive Cutover](./traffic-shadowing-progressive-cutover-design.md) → [Distributed Tracing Pipeline](./distributed-tracing-pipeline-design.md) → [Metrics Pipeline / TSDB](./metrics-pipeline-tsdb-design.md)
- replay/repair 거버넌스: [Replay / Repair Orchestration Control Plane](./replay-repair-orchestration-control-plane-design.md) → [Historical Backfill / Replay Platform](./historical-backfill-replay-platform-design.md) → [Consistency Repair / Anti-Entropy Platform](./consistency-repair-anti-entropy-platform-design.md)
- retry storm containment: [Request Path Failure Modes Primer](./request-path-failure-modes-primer.md) → [Request Deadline and Timeout Budget Primer](./request-deadline-timeout-budget-primer.md) → [Retry Amplification and Backpressure Primer](./retry-amplification-and-backpressure-primer.md) → [Job Queue 설계](./job-queue-design.md) → [Backpressure and Load Shedding](./backpressure-and-load-shedding-design.md)
- 인증/세션 운영 경계: [Service Discovery / Health Routing](./service-discovery-health-routing-design.md) → [Global Traffic Failover Control Plane](./global-traffic-failover-control-plane-design.md) → `[drill]` [Security: JWT / JWKS Outage Recovery / Failover Drills](../security/jwt-jwks-outage-recovery-failover-drills.md) → `[incident matrix]` [Security: Auth Incident Triage / Blast-Radius Recovery Matrix](../security/auth-incident-triage-blast-radius-recovery-matrix.md)
- stateful control plane: [Stateful Workload Placement / Failover Control Plane](./stateful-workload-placement-failover-control-plane-design.md) → [Shard Rebalancing / Partition Relocation](./shard-rebalancing-partition-relocation-design.md) → [Service Discovery / Health Routing](./service-discovery-health-routing-design.md)
- control/data plane fundamentals: [Control Plane / Data Plane Separation](./control-plane-data-plane-separation-design.md) → [Config Distribution System](./config-distribution-system-design.md) → [API Gateway Control Plane](./api-gateway-control-plane-design.md) → [Event Bus Control Plane](./event-bus-control-plane-design.md)
- quorum/stateful reconfiguration: [Consensus Membership Reconfiguration](./consensus-membership-reconfiguration-design.md) → [Stateful Workload Placement / Failover Control Plane](./stateful-workload-placement-failover-control-plane-design.md) → [Shard Rebalancing / Partition Relocation](./shard-rebalancing-partition-relocation-design.md)
- mesh/routing policy: [Service Mesh Control Plane](./service-mesh-control-plane-design.md) → [Service Discovery / Health Routing](./service-discovery-health-routing-design.md) → [Traffic Shadowing / Progressive Cutover](./traffic-shadowing-progressive-cutover-design.md)
- resilience validation: [Failure Injection / Resilience Validation Platform](./failure-injection-resilience-validation-platform-design.md) → `[drill]` [Backup, Restore, Disaster Recovery Drill](./backup-restore-disaster-recovery-drill-design.md) → [Backpressure and Load Shedding](./backpressure-and-load-shedding-design.md)
- cache/db incident downgrade ladder: [Request Path Failure Modes Primer](./request-path-failure-modes-primer.md) → [Request Deadline and Timeout Budget Primer](./request-deadline-timeout-budget-primer.md) → [Read-Only and Graceful Degradation Patterns](./read-only-and-graceful-degradation-patterns.md) → [Backpressure and Load Shedding](./backpressure-and-load-shedding-design.md) → [Read / Write Quorum & Staleness Budget](./read-write-quorum-staleness-budget-design.md)
- global routing/failover: [Global Traffic Failover Control Plane](./global-traffic-failover-control-plane-design.md) → [Multi-Region Active-Active](./multi-region-active-active-design.md) → [Service Discovery / Health Routing](./service-discovery-health-routing-design.md)
- cell isolation/containment: [Cell-Based Architecture / Blast Radius Isolation](./cell-based-architecture-blast-radius-isolation-design.md) → [Multi-tenant SaaS 격리](./multi-tenant-saas-isolation-design.md) → [Stateful Workload Placement / Failover Control Plane](./stateful-workload-placement-failover-control-plane-design.md)
- consistency budget: [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md) → [Read-After-Write Routing Primer](./read-after-write-routing-primer.md) → [Mixed Cache+Replica Read Path Pitfalls](./mixed-cache-replica-read-path-pitfalls.md) → [Read / Write Quorum & Staleness Budget](./read-write-quorum-staleness-budget-design.md) → [Consistency Repair / Anti-Entropy Platform](./consistency-repair-anti-entropy-platform-design.md) → [Session Store Design at Scale](./session-store-design-at-scale.md)
- browser BFF auth boundary basics: [Stateless Sessions Primer](./stateless-sessions-primer.md) → [Browser BFF Session Boundary Primer](./browser-bff-session-boundary-primer.md) → [Session Store Design at Scale](./session-store-design-at-scale.md) → [Security: Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md)
- session/claim cutover deep dive: [Session Store Design at Scale](./session-store-design-at-scale.md) → [Session Store / Claim-Version Cutover](./session-store-claim-version-cutover-design.md) → [Canonical Revocation Plane Across Token Generations](./canonical-revocation-plane-across-token-generations-design.md) → [Security: SCIM Drift / Reconciliation](../security/scim-drift-reconciliation.md) → [Security: AuthZ Decision Logging Design](../security/authz-decision-logging-design.md) → [Security: Audit Logging for Auth / AuthZ Traceability](../security/audit-logging-auth-authz-traceability.md) → [Cleanup Point-of-No-Return](./cleanup-point-of-no-return-design.md)
- claim overlap exit / hard reject thresholds: [Session Store / Claim-Version Cutover](./session-store-claim-version-cutover-design.md) → [Edge Verifier Claim-Skew Fallback](./edge-verifier-claim-skew-fallback-design.md) → [Verifier Overlap Hard-Reject Retirement Gates](./verifier-overlap-hard-reject-retirement-gates-design.md) → [Capability Sunset Gate Matrix](./capability-sunset-gate-matrix-design.md) → [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md)
- translator retirement / revoke-tail cleanup: [Session Store / Claim-Version Cutover](./session-store-claim-version-cutover-design.md) → [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md) → [Adapter Retirement / Compatibility Bridge Decommission](./adapter-retirement-compatibility-bridge-decommission-design.md) → [Cleanup Point-of-No-Return](./cleanup-point-of-no-return-design.md)
- revocation lag recovery / multi-region invalidate: [Session Store Design at Scale](./session-store-design-at-scale.md) → [Session Store / Claim-Version Cutover](./session-store-claim-version-cutover-design.md) → [Canonical Revocation Plane Across Token Generations](./canonical-revocation-plane-across-token-generations-design.md) → `[recovery]` [Revocation Bus Regional Lag Recovery](./revocation-bus-regional-lag-recovery-design.md) → [Multi-Region Active-Active](./multi-region-active-active-design.md)
- edge verifier / claim-skew fallback: [Edge Authorization Service](./edge-authorization-service-design.md) → [Session Store / Claim-Version Cutover](./session-store-claim-version-cutover-design.md) → [Edge Verifier Claim-Skew Fallback](./edge-verifier-claim-skew-fallback-design.md) → `[drill]` [Security: JWT / JWKS Outage Recovery / Failover Drills](../security/jwt-jwks-outage-recovery-failover-drills.md)
- verifier overlap retirement / hard reject: [Edge Verifier Claim-Skew Fallback](./edge-verifier-claim-skew-fallback-design.md) → [Session Store / Claim-Version Cutover](./session-store-claim-version-cutover-design.md) → [Verifier Overlap Hard-Reject Retirement Gates](./verifier-overlap-hard-reject-retirement-gates-design.md) → [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md) → [Adapter Retirement / Compatibility Bridge Decommission](./adapter-retirement-compatibility-bridge-decommission-design.md)
- refresh-family rotation / replay containment: [Session Store / Claim-Version Cutover](./session-store-claim-version-cutover-design.md) → [Refresh-Family Rotation Cutover](./refresh-family-rotation-cutover-design.md) → [Refresh Exchange Idempotency Under Cutover](./refresh-exchange-idempotency-under-cutover-design.md) → [Canonical Revocation Plane Across Token Generations](./canonical-revocation-plane-across-token-generations-design.md) → [Refresh Reauth Escalation Matrix](./refresh-reauth-escalation-matrix-design.md) → [Security: Refresh Token Rotation / Reuse Detection](../security/refresh-token-rotation-reuse-detection.md) → [Security: Token Misuse Detection / Replay Containment](../security/token-misuse-detection-replay-containment.md)
- refresh migration escalation / auth assurance: [Refresh-Family Rotation Cutover](./refresh-family-rotation-cutover-design.md) → [Refresh Exchange Idempotency Under Cutover](./refresh-exchange-idempotency-under-cutover-design.md) → [Refresh Reauth Escalation Matrix](./refresh-reauth-escalation-matrix-design.md) → [Security: MFA / Step-Up Auth Design](../security/mfa-step-up-auth-design.md) → [Security: Step-Up Session Coherence / Auth Assurance](../security/step-up-session-coherence-auth-assurance.md)
- dual-write avoidance / authority transfer: [Dual-Write Avoidance / Migration Bridge](./dual-write-avoidance-migration-bridge-design.md) → [Zero-Downtime Schema Migration Platform](./zero-downtime-schema-migration-platform-design.md) → [Database / Security Identity Bridge Cutover](./database-security-identity-bridge-cutover-design.md) → [Database: Online Backfill Verification, Drift Checks, and Cutover Gates](../database/online-backfill-verification-cutover-gates.md)
- database/security authority transfer: [Database / Security Identity Bridge Cutover](./database-security-identity-bridge-cutover-design.md) → [Dual-Write Avoidance / Migration Bridge](./dual-write-avoidance-migration-bridge-design.md) → [Capability Negotiation / Feature Gating](./capability-negotiation-feature-gating-design.md) → [Database: Online Backfill Verification, Drift Checks, and Cutover Gates](../database/online-backfill-verification-cutover-gates.md) → [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)
- trust-bundle / verifier overlap rollback: [Tenant Split-Out with Service Identity Rollout](./tenant-split-out-service-identity-rollout-design.md) → [Trust-Bundle Rollback During Cell Cutover](./trust-bundle-rollback-during-cell-cutover-design.md) → [Service Mesh Control Plane](./service-mesh-control-plane-design.md) → [Write-Freeze Rollback Window](./write-freeze-rollback-window-design.md)
- reconciliation close / correction: [Reconciliation Window / Cutoff Control](./reconciliation-window-cutoff-control-design.md) → [Payment System Ledger, Idempotency, Reconciliation](./payment-system-ledger-idempotency-reconciliation-design.md) → [Replay / Repair Orchestration Control Plane](./replay-repair-orchestration-control-plane-design.md)
- tenant partition / mobility: [Tenant Partition Strategy / Reassignment](./tenant-partition-strategy-reassignment-design.md) → [멀티 테넌트 SaaS 격리](./multi-tenant-saas-isolation-design.md) → [Cell-Based Architecture / Blast Radius Isolation](./cell-based-architecture-blast-radius-isolation-design.md)
- rollback safety / compatibility: [Deploy Rollback Safety / Compatibility Envelope](./deploy-rollback-safety-compatibility-envelope-design.md) → [Automated Canary Analysis / Rollback Platform](./automated-canary-analysis-rollback-platform-design.md) → [Zero-Downtime Schema Migration Platform](./zero-downtime-schema-migration-platform-design.md)
- receiver cutover hygiene: [Receiver Warmup / Cache Prefill / Write Freeze Cutover](./receiver-warmup-cache-prefill-write-freeze-cutover-design.md) → [Shard Rebalancing / Partition Relocation](./shard-rebalancing-partition-relocation-design.md) → [Distributed Cache](./distributed-cache-design.md)
- config rollback / skew safety: [Config Rollback Safety](./config-rollback-safety-design.md) → [Deploy Rollback Safety / Compatibility Envelope](./deploy-rollback-safety-compatibility-envelope-design.md) → [Protocol Version Skew / Compatibility](./protocol-version-skew-compatibility-design.md)
- irreversible cleanup management: [Database / Security Identity Bridge Cutover](./database-security-identity-bridge-cutover-design.md) → [Adapter Retirement / Compatibility Bridge Decommission](./adapter-retirement-compatibility-bridge-decommission-design.md) → [Cleanup Point-of-No-Return](./cleanup-point-of-no-return-design.md) → [Deploy Rollback Safety / Compatibility Envelope](./deploy-rollback-safety-compatibility-envelope-design.md)
- analytics late data / correction: [Historical Backfill / Replay Platform](./historical-backfill-replay-platform-design.md) → [Analytics Late Data Reconciliation](./analytics-late-data-reconciliation-design.md) → [Streaming Analytics Pipeline](./streaming-analytics-pipeline-design.md) → [Reconciliation Window / Cutoff Control](./reconciliation-window-cutoff-control-design.md)
- capability negotiation / skew control: [Capability Negotiation / Feature Gating](./capability-negotiation-feature-gating-design.md) → `[drill]` [Security: JWT / JWKS Outage Recovery / Failover Drills](../security/jwt-jwks-outage-recovery-failover-drills.md) → [Tenant Split-Out with Service Identity Rollout](./tenant-split-out-service-identity-rollout-design.md) → [Database / Security Identity Bridge Cutover](./database-security-identity-bridge-cutover-design.md) → [Adapter Retirement / Compatibility Bridge Decommission](./adapter-retirement-compatibility-bridge-decommission-design.md)
- tenant split-out / identity rollout: [Tenant Partition Strategy / Reassignment](./tenant-partition-strategy-reassignment-design.md) → [Tenant Split-Out with Service Identity Rollout](./tenant-split-out-service-identity-rollout-design.md) → [Database / Security Identity Bridge Cutover](./database-security-identity-bridge-cutover-design.md) → [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)
- tenant move background path hygiene: [Tenant Split-Out with Service Identity Rollout](./tenant-split-out-service-identity-rollout-design.md) → [Historical Backfill / Replay Platform](./historical-backfill-replay-platform-design.md) → [Search Indexing Pipeline](./search-indexing-pipeline-design.md) → [Webhook Delivery Platform](./webhook-delivery-platform-design.md)
- tenant caller-class rollout matrix: [Tenant Split-Out with Service Identity Rollout](./tenant-split-out-service-identity-rollout-design.md) → [Edge Verifier Claim-Skew Fallback](./edge-verifier-claim-skew-fallback-design.md) → [Dedicated Cell Drain and Retirement](./dedicated-cell-drain-retirement-design.md) → [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md)
- dedicated cell drain / retirement: [Tenant Split-Out with Service Identity Rollout](./tenant-split-out-service-identity-rollout-design.md) → [Dedicated Cell Drain and Retirement](./dedicated-cell-drain-retirement-design.md) → [Trust-Bundle Rollback During Cell Cutover](./trust-bundle-rollback-during-cell-cutover-design.md) → [Cleanup Point-of-No-Return](./cleanup-point-of-no-return-design.md)
- capability lifecycle / bridge retirement: [Capability Negotiation / Feature Gating](./capability-negotiation-feature-gating-design.md) → [Database / Security Identity Bridge Cutover](./database-security-identity-bridge-cutover-design.md) → [Adapter Retirement / Compatibility Bridge Decommission](./adapter-retirement-compatibility-bridge-decommission-design.md) → [Cleanup Point-of-No-Return](./cleanup-point-of-no-return-design.md)
- adapter retirement / bridge sunset: [Database / Security Identity Bridge Cutover](./database-security-identity-bridge-cutover-design.md) → [Session Store / Claim-Version Cutover](./session-store-claim-version-cutover-design.md) → [Adapter Retirement / Compatibility Bridge Decommission](./adapter-retirement-compatibility-bridge-decommission-design.md) → [Cleanup Point-of-No-Return](./cleanup-point-of-no-return-design.md)
- analytics UX / alert correction: [Historical Backfill / Replay Platform](./historical-backfill-replay-platform-design.md) → [Analytics Late Data Reconciliation](./analytics-late-data-reconciliation-design.md) → [Dashboard Restatement UX](./dashboard-restatement-ux-design.md) → [Alert Re-Evaluation / Correction](./alert-reevaluation-correction-design.md)
- tenant-scoped recovery / reversible config cutover: `[recovery]` [Tenant-Scoped Config Incident Recovery](./tenant-scoped-config-incident-recovery-design.md) → [Config Rollback Safety](./config-rollback-safety-design.md) → [Write-Freeze Rollback Window](./write-freeze-rollback-window-design.md) → [Traffic Shadowing / Progressive Cutover](./traffic-shadowing-progressive-cutover-design.md)
- reversible stateful cutover: [Write-Freeze Rollback Window](./write-freeze-rollback-window-design.md) → [Receiver Warmup / Cache Prefill / Write Freeze Cutover](./receiver-warmup-cache-prefill-write-freeze-cutover-design.md) → [Cleanup Point-of-No-Return](./cleanup-point-of-no-return-design.md)

## 참고

- DB 레벨의 Sharding, Replication, CQRS 등은 [database/](../database/) 카테고리 참조
- 실시간 전송 모델 비교는 [network/](../network/)의 SSE / WebSocket 문서와 함께 보면 좋다
- 멀티 테넌트 격리 문제는 [Security](../security/README.md), [Database](../database/README.md), [Software Engineering](../software-engineering/README.md) 문서와 함께 보면 더 잘 보인다
- 결제/정산/정합성은 [Database](../database/README.md)의 멱등성, redo/undo, reconciliation 관점과 함께 보면 좋다
- 안전한 재시도, dedup window, replay 복구는 [Idempotency Key Store / Dedup Window / Replay-Safe Retry](./idempotency-key-store-dedup-window-replay-safe-retry-design.md)와 [Database](../database/README.md)의 멱등성 관련 문서를 같이 보면 더 촘촘해진다
- replay-safe retry와 dedup 저장소 장애는 `[recovery]` [Security: Replay Store Outage / Degradation Recovery](../security/replay-store-outage-degradation-recovery.md), [Security: Token Misuse Detection / Replay Containment](../security/token-misuse-detection-replay-containment.md)까지 같이 보면 운영 경계가 더 선명해진다
- CDC, outbox, replay, reindex는 [Change Data Capture / Outbox Relay](./change-data-capture-outbox-relay-design.md), [Historical Backfill / Replay Platform](./historical-backfill-replay-platform-design.md), [Search Indexing Pipeline](./search-indexing-pipeline-design.md)을 함께 보면 연결이 빨라진다
- event replay와 schema evolution은 [Design Pattern: Projection Rebuild, Backfill, and Cutover Pattern](../design-pattern/projection-rebuild-backfill-cutover-pattern.md), [Design Pattern: Event Upcaster Compatibility Patterns](../design-pattern/event-upcaster-compatibility-patterns.md), [Language: JSON `null`, Missing Field, Unknown Property, and Schema Evolution](../language/java/json-null-missing-unknown-field-schema-evolution.md)으로 이어 보면 더 촘촘해진다
- zero-downtime migration은 DB DDL만의 문제가 아니므로 [Zero-Downtime Schema Migration Platform](./zero-downtime-schema-migration-platform-design.md), [Dual-Write Avoidance / Migration Bridge](./dual-write-avoidance-migration-bridge-design.md), [Database / Security Identity Bridge Cutover](./database-security-identity-bridge-cutover-design.md)를 같이 보는 편이 좋다
- database authority 이동과 identity capability rollout이 같이 엮이면 [Database / Security Identity Bridge Cutover](./database-security-identity-bridge-cutover-design.md), [Capability Negotiation / Feature Gating](./capability-negotiation-feature-gating-design.md), `[playbook]` [Database: CDC Gap Repair, Reconciliation, and Rebuild Boundaries](../database/cdc-gap-repair-reconciliation-playbook.md), [Security: SCIM Deprovisioning / Session / AuthZ Consistency](../security/scim-deprovisioning-session-authz-consistency.md)를 한 묶음으로 보는 편이 좋다
- 서비스 라우팅과 관측성은 [Service Discovery / Health Routing](./service-discovery-health-routing-design.md), [Distributed Tracing Pipeline](./distributed-tracing-pipeline-design.md), [Metrics Pipeline / TSDB](./metrics-pipeline-tsdb-design.md)를 묶어서 보는 편이 실전 감각에 가깝다
- 재해 복구는 단순 failover와 다르므로 `[drill]` [Backup, Restore, Disaster Recovery Drill](./backup-restore-disaster-recovery-drill-design.md)과 [Multi-Region Active-Active](./multi-region-active-active-design.md)를 구분해서 이해하는 것이 좋다
- 안전한 cutover는 단순 canary 비율 조정보다 넓은 주제라서 [Traffic Shadowing / Progressive Cutover](./traffic-shadowing-progressive-cutover-design.md), [Feature Flag Control Plane](./feature-flag-control-plane-design.md), [Distributed Tracing Pipeline](./distributed-tracing-pipeline-design.md)을 함께 보면 guardrail이 잘 보인다
- replay와 repair는 다르므로 [Historical Backfill / Replay Platform](./historical-backfill-replay-platform-design.md)과 [Consistency Repair / Anti-Entropy Platform](./consistency-repair-anti-entropy-platform-design.md)을 구분해서 보는 편이 좋다
- stateful 플랫폼 운영은 [Shard Rebalancing / Partition Relocation](./shard-rebalancing-partition-relocation-design.md), [Stateful Stream Processor State Store / Checkpoint Recovery](./stateful-stream-processor-state-store-checkpoint-recovery-design.md), [Distributed Cache](./distributed-cache-design.md)를 함께 보면 연결이 빨라진다
- dual-read verification은 migration의 세부 구현이 아니라 별도 운영 패턴이므로 [Dual-Read Comparison / Verification Platform](./dual-read-comparison-verification-platform-design.md)과 [Zero-Downtime Schema Migration Platform](./zero-downtime-schema-migration-platform-design.md)을 같이 보는 편이 좋다
- 자동 canary 분석은 route shifting과 별개로 baseline 선정과 rollback hysteresis가 중요하므로 [Automated Canary Analysis / Rollback Platform](./automated-canary-analysis-rollback-platform-design.md)과 [Traffic Shadowing / Progressive Cutover](./traffic-shadowing-progressive-cutover-design.md)를 같이 보면 좋다
- replay/repair는 엔진만큼 governance가 중요하므로 [Replay / Repair Orchestration Control Plane](./replay-repair-orchestration-control-plane-design.md), [Historical Backfill / Replay Platform](./historical-backfill-replay-platform-design.md), [Consistency Repair / Anti-Entropy Platform](./consistency-repair-anti-entropy-platform-design.md)을 묶어 보면 좋다
- stateful 서비스는 relocation만큼 placement policy가 중요하므로 [Stateful Workload Placement / Failover Control Plane](./stateful-workload-placement-failover-control-plane-design.md)과 [Shard Rebalancing / Partition Relocation](./shard-rebalancing-partition-relocation-design.md)을 함께 보는 편이 좋다
- control plane / data plane separation은 여러 개별 문서에 흩어져 있는 공통 원리라서 [Control Plane / Data Plane Separation](./control-plane-data-plane-separation-design.md)을 먼저 보고 각 control plane 문서를 보면 연결이 더 잘 보인다
- quorum 시스템을 운영한다면 [Consensus Membership Reconfiguration](./consensus-membership-reconfiguration-design.md)과 [Stateful Workload Placement / Failover Control Plane](./stateful-workload-placement-failover-control-plane-design.md)을 같이 보는 편이 좋다
- service mesh는 gateway나 discovery의 대체재가 아니라 내부 통신 정책 제어의 별도 층이므로 [Service Mesh Control Plane](./service-mesh-control-plane-design.md), [Service Discovery / Health Routing](./service-discovery-health-routing-design.md), [API Gateway Control Plane](./api-gateway-control-plane-design.md)을 구분해서 보는 편이 좋다
- resilience validation은 DR drill, canary, backpressure와 이어지므로 [Failure Injection / Resilience Validation Platform](./failure-injection-resilience-validation-platform-design.md), [Automated Canary Analysis / Rollback Platform](./automated-canary-analysis-rollback-platform-design.md), `[drill]` [Backup, Restore, Disaster Recovery Drill](./backup-restore-disaster-recovery-drill-design.md)을 함께 보면 좋다
- global failover는 region 내부 routing과 다른 층이므로 [Global Traffic Failover Control Plane](./global-traffic-failover-control-plane-design.md), [Service Discovery / Health Routing](./service-discovery-health-routing-design.md), [Multi-Region Active-Active](./multi-region-active-active-design.md)를 구분해서 보는 편이 좋다
- JWT/JWKS 같은 인증 계층 장애는 `[drill]` [Security: JWT / JWKS Outage Recovery / Failover Drills](../security/jwt-jwks-outage-recovery-failover-drills.md)와 같이 보면 routing/failover와 trust boundary를 함께 잡기 좋다
- 세션 일관성과 revoke propagation은 [Security: Session Revocation at Scale](../security/session-revocation-at-scale.md), [Security: Revocation Propagation Lag / Debugging](../security/revocation-propagation-lag-debugging.md), [Session Store Design at Scale](./session-store-design-at-scale.md), [Session Store / Claim-Version Cutover](./session-store-claim-version-cutover-design.md), [Canonical Revocation Plane Across Token Generations](./canonical-revocation-plane-across-token-generations-design.md)를 같이 보면 운영 설계까지 이어지고, `302` login loop나 숨은 `JSESSIONID`처럼 framework symptom에서 출발했다면 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md), [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md)부터 보고 내려가면 분류가 빨라진다
- revoke fan-out 문제가 특정 region이나 cache tier에서만 길게 남거나 legacy/new token generation 중 한쪽만 stale allow를 남기는 경우는 pub/sub health만으로 설명되지 않으므로 [Session Store / Claim-Version Cutover](./session-store-claim-version-cutover-design.md), [Canonical Revocation Plane Across Token Generations](./canonical-revocation-plane-across-token-generations-design.md), `[recovery]` [Revocation Bus Regional Lag Recovery](./revocation-bus-regional-lag-recovery-design.md), [Consistency Repair / Anti-Entropy Platform](./consistency-repair-anti-entropy-platform-design.md), [Multi-Region Active-Active](./multi-region-active-active-design.md)를 묶어 보는 편이 좋다
- cell architecture는 단순 샤딩이 아니라 blast radius 관리이므로 [Cell-Based Architecture / Blast Radius Isolation](./cell-based-architecture-blast-radius-isolation-design.md), [Shard Rebalancing / Partition Relocation](./shard-rebalancing-partition-relocation-design.md), [Multi-tenant SaaS 격리](./multi-tenant-saas-isolation-design.md)를 묶어 보면 좋다
- consistency는 eventual이라고만 말하지 말고 [Read / Write Quorum & Staleness Budget](./read-write-quorum-staleness-budget-design.md)처럼 허용 stale 범위를 숫자로 잡아 보는 편이 좋다
- migration에서 dual write는 마지막 수단에 가깝기 때문에 [Dual-Write Avoidance / Migration Bridge](./dual-write-avoidance-migration-bridge-design.md), [Database / Security Identity Bridge Cutover](./database-security-identity-bridge-cutover-design.md), [Change Data Capture / Outbox Relay](./change-data-capture-outbox-relay-design.md)를 함께 보는 편이 좋다
- reconciliation은 diff만의 문제가 아니라 close/correction 경계가 중요하므로 [Reconciliation Window / Cutoff Control](./reconciliation-window-cutoff-control-design.md)과 [Payment System Ledger, Idempotency, Reconciliation](./payment-system-ledger-idempotency-reconciliation-design.md)을 같이 보는 편이 좋다
- tenant partition은 단순 shard key 문제가 아니라 tenant mobility 문제이므로 [Tenant Partition Strategy / Reassignment](./tenant-partition-strategy-reassignment-design.md)과 [Shard Rebalancing / Partition Relocation](./shard-rebalancing-partition-relocation-design.md)를 함께 보면 좋다
- tenant split-out에 dedicated cell migration과 service identity rollout이 같이 붙으면 [Tenant Split-Out with Service Identity Rollout](./tenant-split-out-service-identity-rollout-design.md), [Database / Security Identity Bridge Cutover](./database-security-identity-bridge-cutover-design.md), [Security: Service-to-Service Auth: mTLS, JWT, SPIFFE](../security/service-to-service-auth-mtls-jwt-spiffe.md)를 한 묶음으로 보는 편이 좋다
- dedicated-cell promotion 검증을 순서대로 읽으려면 [Traffic Shadowing / Progressive Cutover](./traffic-shadowing-progressive-cutover-design.md)로 mirrored traffic을 먼저 보고, [Dual-Read Comparison / Verification Platform](./dual-read-comparison-verification-platform-design.md)으로 read parity를 확인한 뒤, [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)과 [Tenant Split-Out with Service Identity Rollout](./tenant-split-out-service-identity-rollout-design.md)으로 auth drift soak을 닫는 편이 좋다
- foreground/background caller를 분리해 principal issuance, allowlist overlap, drift soak checklist를 읽으려면 [Tenant Split-Out with Service Identity Rollout](./tenant-split-out-service-identity-rollout-design.md), [Edge Verifier Claim-Skew Fallback](./edge-verifier-claim-skew-fallback-design.md), [Dedicated Cell Drain and Retirement](./dedicated-cell-drain-retirement-design.md), [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md)을 한 묶음으로 보면 좋다
- tenant가 shared cell을 완전히 빠져나간 뒤 drain, legacy principal retirement, rollback closure까지 묶어 보려면 [Tenant Split-Out with Service Identity Rollout](./tenant-split-out-service-identity-rollout-design.md), [Dedicated Cell Drain and Retirement](./dedicated-cell-drain-retirement-design.md), [Cleanup Point-of-No-Return](./cleanup-point-of-no-return-design.md)을 같이 보는 편이 좋다
- dedicated cell migration에 SPIFFE/SPIRE issuer 또는 mesh trust root 변경까지 붙으면 [Tenant Split-Out with Service Identity Rollout](./tenant-split-out-service-identity-rollout-design.md), [Trust-Bundle Rollback During Cell Cutover](./trust-bundle-rollback-during-cell-cutover-design.md), [Service Mesh Control Plane](./service-mesh-control-plane-design.md)을 함께 봐야 rollback window와 verifier overlap 순서를 놓치지 않는다
- rollback safety는 canary와 별개로 compatibility envelope를 설계해야 하므로 [Deploy Rollback Safety / Compatibility Envelope](./deploy-rollback-safety-compatibility-envelope-design.md), [Automated Canary Analysis / Rollback Platform](./automated-canary-analysis-rollback-platform-design.md), [Zero-Downtime Schema Migration Platform](./zero-downtime-schema-migration-platform-design.md)을 묶어 보는 편이 좋다
- stateful receiver 전환은 copy보다 warmup/prefill/freeze가 더 까다로우므로 [Receiver Warmup / Cache Prefill / Write Freeze Cutover](./receiver-warmup-cache-prefill-write-freeze-cutover-design.md)와 [Shard Rebalancing / Partition Relocation](./shard-rebalancing-partition-relocation-design.md)를 함께 보는 편이 좋다
- config rollback은 단순 last-known-good 이상으로 version skew를 포함하므로 [Config Rollback Safety](./config-rollback-safety-design.md), [Protocol Version Skew / Compatibility](./protocol-version-skew-compatibility-design.md), [Deploy Rollback Safety / Compatibility Envelope](./deploy-rollback-safety-compatibility-envelope-design.md)을 같이 보는 편이 좋다
- cleanup은 부가 정리가 아니라 irreversible boundary라서 [Database / Security Identity Bridge Cutover](./database-security-identity-bridge-cutover-design.md), [Cleanup Point-of-No-Return](./cleanup-point-of-no-return-design.md), [Deploy Rollback Safety / Compatibility Envelope](./deploy-rollback-safety-compatibility-envelope-design.md)를 같이 보면 좋다
- analytics는 watermark만으로 끝나지 않으므로 [Analytics Late Data Reconciliation](./analytics-late-data-reconciliation-design.md)과 [Reconciliation Window / Cutoff Control](./reconciliation-window-cutoff-control-design.md)을 함께 보면 좋다
- version skew가 단순 버전 비교보다 어려운 이유는 capability 차이 때문이므로 [Capability Negotiation / Feature Gating](./capability-negotiation-feature-gating-design.md), [Database / Security Identity Bridge Cutover](./database-security-identity-bridge-cutover-design.md), [Protocol Version Skew / Compatibility](./protocol-version-skew-compatibility-design.md)을 같이 보는 편이 좋다
- session store migration이 claim version rollout과 같이 엮이면 [Session Store / Claim-Version Cutover](./session-store-claim-version-cutover-design.md), [Capability Negotiation / Feature Gating](./capability-negotiation-feature-gating-design.md), [Cleanup Point-of-No-Return](./cleanup-point-of-no-return-design.md)을 묶어서 보는 편이 좋다
- edge validator가 새 claim semantic을 아직 모르는 overlap window와 그 이후 hard reject retirement 문턱은 [Edge Authorization Service](./edge-authorization-service-design.md), [Session Store / Claim-Version Cutover](./session-store-claim-version-cutover-design.md), [Edge Verifier Claim-Skew Fallback](./edge-verifier-claim-skew-fallback-design.md), [Verifier Overlap Hard-Reject Retirement Gates](./verifier-overlap-hard-reject-retirement-gates-design.md), `[drill]` [Security: JWT / JWKS Outage Recovery / Failover Drills](../security/jwt-jwks-outage-recovery-failover-drills.md)를 한 묶음으로 보는 편이 좋다
- refresh family migration은 token rotation만이 아니라 forced reissue, exchange idempotency, canonical family alias, replay containment, generation-aware revoke fan-out을 같이 봐야 하므로 [Refresh-Family Rotation Cutover](./refresh-family-rotation-cutover-design.md), [Refresh Exchange Idempotency Under Cutover](./refresh-exchange-idempotency-under-cutover-design.md), [Canonical Revocation Plane Across Token Generations](./canonical-revocation-plane-across-token-generations-design.md), [Session Store / Claim-Version Cutover](./session-store-claim-version-cutover-design.md), [Security: Refresh Token Family Invalidation at Scale](../security/refresh-token-family-invalidation-at-scale.md), [Security: Token Misuse Detection / Replay Containment](../security/token-misuse-detection-replay-containment.md)을 한 묶음으로 보는 편이 좋다
- capability 협상은 도입 단계로 끝나지 않고 overlap/soak/cleanup signal을 따라 sunset ladder를 닫아야 하므로 [Capability Negotiation / Feature Gating](./capability-negotiation-feature-gating-design.md), [Capability Sunset Gate Matrix](./capability-sunset-gate-matrix-design.md), [Database / Security Identity Bridge Cutover](./database-security-identity-bridge-cutover-design.md), [Adapter Retirement / Compatibility Bridge Decommission](./adapter-retirement-compatibility-bridge-decommission-design.md)을 한 묶음으로 보는 편이 좋다
- adapter 제거는 cleanup의 하위 작업이 아니라 별도 은퇴 절차이므로 [Database / Security Identity Bridge Cutover](./database-security-identity-bridge-cutover-design.md), [Adapter Retirement / Compatibility Bridge Decommission](./adapter-retirement-compatibility-bridge-decommission-design.md), [Cleanup Point-of-No-Return](./cleanup-point-of-no-return-design.md)을 함께 보는 편이 좋다
- analytics correction은 숫자 재계산만이 아니라 backfill 이후 sink 정렬 문제까지 이어지므로 [Historical Backfill / Replay Platform](./historical-backfill-replay-platform-design.md), [Dashboard Restatement UX](./dashboard-restatement-ux-design.md), [Alert Re-Evaluation / Correction](./alert-reevaluation-correction-design.md), [Analytics Late Data Reconciliation](./analytics-late-data-reconciliation-design.md)을 같이 보는 편이 좋다
- tenant override 사고는 rollback 버튼 하나보다 scoped freeze, rollback safety, reversible soak을 함께 봐야 하므로 `[recovery]` [Tenant-Scoped Config Incident Recovery](./tenant-scoped-config-incident-recovery-design.md), [Config Rollback Safety](./config-rollback-safety-design.md), [Write-Freeze Rollback Window](./write-freeze-rollback-window-design.md), [Traffic Shadowing / Progressive Cutover](./traffic-shadowing-progressive-cutover-design.md)를 묶어 보는 편이 좋다
- stateful handoff는 freeze 자체보다 rollback window 관리가 중요하므로 [Write-Freeze Rollback Window](./write-freeze-rollback-window-design.md)와 [Receiver Warmup / Cache Prefill / Write Freeze Cutover](./receiver-warmup-cache-prefill-write-freeze-cutover-design.md)를 같이 보는 편이 좋다
- 이 카테고리는 **면접 관점의 상위 레벨 아키텍처 설계**에 집중한다
