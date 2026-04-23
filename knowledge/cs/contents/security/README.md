# Security (보안)

**난이도: 🔴 Advanced**

> 인증, 인가, 세션, OAuth/OIDC, browser/BFF 경계, replay/misuse, JWT/JWKS 운영 장애, auth observability를 함께 보는 카테고리

> retrieval-anchor-keywords: security readme, security navigator, security category navigator, category navigator, auth navigator, security primer, security survey, security catalog, security deep dive, deep dive route, security deep dive route, security playbook, security runbook, security drill, incident catalog, incident matrix, incident ladder, recovery label, recovery guide, incident-oriented recovery doc, mixed incident catalog, incident deep dive cue, deep dive label, outage recovery catalog, security routing, security routing summary, security index guide, security entrypoint, bridge entrypoint, security bridge entrypoint, cross-category bridge, security cross-category bridge, auth basics intro, auth troubleshooting, auth learning path, principal basics, principal vs session, permission model basics, role vs permission, role vs scope vs ownership, role check vs scope check vs ownership check, scope is not ownership, ownership check primer, resource ownership primer, object ownership primer, claim vs authority vs permission, claims vs roles vs authorities mapping, jwt claims vs authorities, spring grantedauthority, granted authority, spring authority mapping pitfalls, spring security authority mapping, spring security valid jwt but 403, valid token empty authorities, JwtAuthenticationConverter 403, JwtGrantedAuthoritiesConverter 403, hasrole vs hasauthority, role prefix mismatch, scope prefix mismatch, authorityPrefix drift, jwt role claim, scope claim vs permission, oauth scope vs audience vs permission, api audience vs scope vs permission, audience is not scope, scope is not permission, aud claim vs scope claim, api audience primer, application permission source of truth, subject resource action, spring + security route, auth incident bridge, session coherence bridge, observability bridge, incident bundle, session bundle, observability bundle, identity bundle, hardware trust recovery bundle, replay session defense bundle, service delegation boundary bundle, incident recovery bridge, session boundary bridge, identity lifecycle bridge, identity / authority transfer bridge, authority transfer / security bridge, database / security authority bridge, verification / shadowing / authority bridge, authority route parity, security + system design route, database + security + system design route, system design handoff, control-plane handoff, cutover handoff, session coherence, browser session coherence, browser session troubleshooting path, browser hardening survey, login hardening path, redirect hardening path, session fixation, clickjacking, csp, open redirect, post-login redirect, frame ancestors, session inventory ux, revocation scope design, operator tooling safety rails, revocation impact preview, revoke preview payload, preview join keys, graph snapshot id, preview drift response contract, preview expired, forced re-confirmation, stale preview response, revocation propagation status, revocation status payload, requested in progress fully blocked confirmed, fully blocked confirmed meaning, operator revoke progress, aobo revocation audit event schema, break glass revocation audit schema, preview confirm timeline join key, revocation request id access group id grant id, acting on behalf of, break glass, incident close gate, break glass closure blocker, incident close blocked active override, break glass ended but access still works, cleanup confirmed when, cleanup_confirmed blocked, support access notification, support access audience matrix, support access delivery surface, support access email vs inbox vs timeline, support access alternate verified channel, compromised mailbox support access alert, primary email suppression policy, tenant admin notification, security contact notification, emergency access notification, security timeline retention, security timeline event schema, support access event schema, access group id, case ref, retention class, emergency grant cleanup, leftover aobo grant, leftover break glass grant, expired grant sweeper, incident cleanup SLA, post incident grant review, tenant policy schema, privileged support alert policy, managed identity escalation, security contact opt in, compliance-sensitive support event, policy snapshot id, jwt jwks outage, JWKS outage, auth verification outage, stale JWKS cache, invalid signature, signature verify failed, kid miss, unable to find jwk, unable to find JWK, browser bff boundary, login loop, 302 login loop, 401 redirect loop, 401 302 bounce, saved request loop, hidden session mismatch, replay defense, replay store down, nonce store down, authz caching, authorization graph cache, authorization graph caching, authz graph cache, authz graph, graph snapshot, graph snapshot cache, graph snapshot version, relationship cache, relationship edge cache, path cache, edge cache, graph invalidation, tenant-scoped graph invalidation, delegated scope revoke, 403 cache stale, stale deny, grant but still denied, tenant-specific 403, only one tenant 403, inconsistent 401 404, 401 404 flip, concealment drift, authz cache debug, logout but still works, logout tail, revoke lag, revocation tail, oauth oidc, oauth device code flow, device authorization, cross-device login, PAR, JAR, pushed authorization request, signed request object, workload identity, auth observability, auth observability gap, auth telemetry gap, auth signal gap, auth-signal-gap, auth blind spot, observability blind spot, missing audit trail, missing-audit-trail, audit trail missing, no audit evidence, decision log missing, no decision log, allow deny reason missing, 401 403 spike no reason code, sender-constrained token, mTLS client auth, certificate-bound token, auth failover, session store, service discovery, global traffic failover, security system design bridge, attestation recovery, hardware attestation recovery, key compromise recovery, trust bundle recovery, control plane auth incident, blast radius recovery, recovery drill, response ladder, database security bridge, authority transfer, decision parity, auth shadow divergence, delegated admin, scim deprovision tail, scim disable but still access, scim disable still login, deprovisioned user still logged in, deprovision finished but access remains, auth shadow evaluation, backfill is green but access tail remains, backfill verification, cleanup evidence, retirement evidence, decision log join key, audit evidence bundle, claim version retirement, oauth branch point, oauth device code branch, oauth par jar branch, browserless oauth path, request hardening branch, delegated session tail cleanup, session-tail cleanup, aobo cleanup tail, break glass cleanup tail, false closure, delegated refresh family cleanup, stale cache convergence, oauth callback hardening, callback login completion hardening, pkce verifier mismatch, state vs csrf token, social login first post 403, first post 403 after login, http stateless bridge, cookie session jwt bridge, beginner auth bridge, session basics to spring security, why login state is kept, hidden jsessionid route, spring security beginner route, security symptom shortcut, 401 403 404 beginner guide, login required vs forbidden vs not found, auth failure primer route, role change session freshness, permission change while logged in, role revoked but still works, admin removed still access, granted role but still 403, stale authority claim, stale authorities, authz freshness primer, grant path freshness, permission granted still 403, newly granted permission still forbidden, new role still 403, 403 until claim refresh, 403 until cache invalidation, claim refresh after grant, permission grant propagation, grant path cache invalidation, stale deny after grant, fresh grant stale deny, grant convergence

<details>
<summary>Table of Contents</summary>

- [빠른 시작](#빠른-시작)
- [역할별 라우팅 요약](#역할별-라우팅-요약)
- [증상별 바로 가기](#증상별-바로-가기)
- [기본 primer](#기본-primer)
- [운영 / Incident catalog](#운영--incident-catalog)
- [Hardware Trust / Recovery deep dive catalog](#hardware-trust--recovery-deep-dive-catalog)
- [Session Coherence / Assurance deep dive catalog](#session-coherence--assurance-deep-dive-catalog)
- [Browser / Session Coherence](#browser--session-coherence)
- [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path)
- [Browser / Server Boundary deep dive catalog](#browser--server-boundary-deep-dive-catalog)
- [Replay / Token Misuse / Session Defense deep dive catalog](#replay--token-misuse--session-defense-deep-dive-catalog)
- [Identity Lifecycle / Provisioning deep dive catalog](#identity-lifecycle--provisioning-deep-dive-catalog)
- [Service / Delegation Boundaries deep dive catalog](#service--delegation-boundaries-deep-dive-catalog)
- [AuthZ / Tenant / Response Contracts deep dive catalog](#authz--tenant--response-contracts-deep-dive-catalog)
- [추천 학습 흐름 (category-local survey)](#추천-학습-흐름-category-local-survey)
- [연결해서 보면 좋은 문서 (cross-category bridge)](#연결해서-보면-좋은-문서-cross-category-bridge)
- [Incident / Recovery / Trust](#security-bridge-incident-recovery-trust)
- [Session / Boundary / Replay](#security-bridge-session-boundary-replay)
- [Identity / Delegation / Lifecycle](#security-bridge-identity-delegation-lifecycle)

</details>

## 빠른 시작

이 README는 security category `navigator`다. `기본 primer`는 auth / session / OAuth 기초 축을 맞추는 입문 구간이고, `추천 학습 흐름`은 category-local `survey`, `... deep dive catalog` heading은 theme bucket을 고르는 `catalog`, 링크된 개별 `.md`는 실제 `deep dive`다. 즉시 대응은 `[playbook]` / `[runbook]` / `[drill]` / `[incident matrix]` / `[recovery]` 문서로 내려간다.

- 전체 흐름 `survey`가 먼저 필요하면:
  - 아래 `추천 학습 흐름 (category-local survey)` 구간
  - [루트 README](../../README.md)
- auth / session `primer`부터 읽고 싶다면:
  - [기본 primer](#기본-primer)
  - [인증과 인가의 차이](./authentication-vs-authorization.md)
  - authn / authz뿐 아니라 `principal`, `session`, `permission model` 기본축까지 같이 잡고 싶을 때 가장 먼저 본다.
  - [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md)
  - `role`, OAuth `scope`, `ownership`가 같은 말처럼 보일 때 읽는 primer다. `orders.read`가 모든 주문을 뜻하지 않고, role이 있어도 객체 관계 검사가 따로 필요하다는 점을 먼저 분리한다.
  - [OAuth Scope vs API Audience vs Application Permission](./oauth-scope-vs-api-audience-vs-application-permission.md)
  - OAuth `scope`, token `audience`, app `permission`이 다 같은 "권한"처럼 들릴 때 읽는 primer다. gateway audience, service audience, downscoped token, business permission을 한 번에 분리한다.
  - [JWT Claims vs Roles vs Spring Authorities vs Application Permissions](./jwt-claims-roles-authorities-permissions-mapping.md)
  - `roles`, `scope`, `ROLE_`, `hasRole`, `hasAuthority`, app `permission`이 한 단어처럼 섞일 때 바로 보는 primer다.
  - [Spring Authority Mapping Pitfalls](./spring-authority-mapping-pitfalls.md)
  - JWT는 valid한데 Spring route / method security에서만 `403`이 날 때, `JwtAuthenticationConverter`, `ROLE_`, `SCOPE_`, `hasRole`, `hasAuthority` mismatch를 바로 좁히는 debugging deep dive다.
  - [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md)
  - `권한을 방금 줬는데도 403`이 남을 때 source of truth 변경, claim refresh, deny cache invalidation이 서로 다른 단계라는 점을 먼저 분리하는 primer다.
  - [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md)
  - `401` / `403` / `404` primer와 cookie / session / JWT -> Spring auth handoff는 [Session / Boundary / Replay](#session--boundary--replay) anchor에서 이어 본다.
  - network primer의 `cookie` / `session` / `JWT` 설명에서 바로 올라오거나, `login loop` / `SavedRequest` / `hidden session mismatch`가 보이는데 용어가 아직 흐리면 [Cross-Domain Bridge Map: HTTP Stateless / Cookie / Session / Spring Security](../../rag/cross-domain-bridge-map.md#bridge-http-session-security-cluster) route를 먼저 탄다.
  - 브라우저 없는 기기 login branch point는 [OAuth Device Code Flow / Security Model](./oauth-device-code-flow-security.md)
  - authorization request hardening branch point는 [OAuth PAR / JAR Basics](./oauth-par-jar-basics.md)
  - server-side code exchange나 BFF 이후 client proof / sender-constrained branch는 [Session / Boundary / Replay](#session--boundary--replay) anchor에서 이어 본다.
- session coherence `deep dive` cluster로 바로 들어가려면:
  - [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path)
  - [Session / Boundary / Replay](#session--boundary--replay)
- authz graph / relationship cache cluster로 바로 들어가려면:
  - [AuthZ / Tenant / Response Contracts deep dive catalog](#authz--tenant--response-contracts-deep-dive-catalog)
  - graph invalidation / stale deny / tenant-scoped authz bundle은 [Identity / Delegation / Lifecycle](#identity--delegation--lifecycle) anchor에서 이어 본다.
- auth observability / evidence `deep dive` cluster로 바로 들어가려면:
  - [운영 / Incident catalog](#운영--incident-catalog)
  - [AuthZ / Tenant / Response Contracts deep dive catalog](#authz--tenant--response-contracts-deep-dive-catalog)
  - `missing-audit-trail`, `auth-signal-gap`, `decision log missing`, `allow/deny reason code가 안 보인다`가 먼저 보이면 [Auth Observability: SLI / SLO / Alerting](./auth-observability-sli-slo-alerting.md), [AuthZ Decision Logging Design](./authz-decision-logging-design.md), [deep dive] [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md), [deep dive] [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md) 순으로 붙인다.
- boundary `deep dive`로 바로 들어가려면:
  - [JWT 깊이 파기](./jwt-deep-dive.md)
  - [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md)
  - [Identity / Delegation / Lifecycle](#identity--delegation--lifecycle)
- 운영 `playbook` / `runbook` / `drill` / `incident matrix` / `[recovery]` route로 바로 들어가려면:
  - [운영 / Incident catalog](#운영--incident-catalog)
  - [Incident / Recovery / Trust](#incident--recovery--trust)
  - [Session / Boundary / Replay](#session--boundary--replay)
  - `JWKS outage`, `kid miss`, `unable to find JWK`, `auth verification outage`, `stale JWKS cache`가 먼저 보이면 위 incident bridge에서 시작한다.
- outage/debugging symptom 문장으로 바로 routing하려면:
  - [증상별 바로 가기](#증상별-바로-가기)
- [Spring + Security](../../rag/cross-domain-bridge-map.md#spring--security) route로 바로 들어가려면:
  - [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path)
  - [Session / Boundary / Replay](#session--boundary--replay)
- [Security + System Design](../../rag/cross-domain-bridge-map.md#security--system-design) / [Database + Security + System Design](../../rag/cross-domain-bridge-map.md#database--security--system-design) route로 바로 들어가려면:
  - `[cross-category bridge]` [연결해서 보면 좋은 문서 (cross-category bridge)](#연결해서-보면-좋은-문서-cross-category-bridge)
  - `[cross-category bridge]` [Incident / Recovery / Trust](#incident--recovery--trust)
  - `[cross-category bridge]` [Identity / Delegation / Lifecycle](#identity--delegation--lifecycle)
  - `[system design]` [System Design: Control Plane / Data Plane Separation](../system-design/control-plane-data-plane-separation-design.md)
- 문서 역할이 헷갈리면:
  - [역할별 라우팅 요약](#역할별-라우팅-요약)
  - [연결해서 보면 좋은 문서 (cross-category bridge)](#연결해서-보면-좋은-문서-cross-category-bridge)

## 역할별 라우팅 요약

| 지금 필요한 것 | 문서 역할 | 먼저 갈 곳 |
|---|---|---|
| security 전체 지형과 추천 순서 | `survey` | [추천 학습 흐름 (category-local survey)](#추천-학습-흐름-category-local-survey), [루트 README](../../README.md) |
| auth / session / OAuth 기초 축 | `primer` | [기본 primer](#기본-primer) |
| session / browser / authz / SCIM 중 어느 bucket부터 읽을지 먼저 고르기 | `catalog / navigator` | 아래 각 `deep dive catalog` 섹션 |
| 특정 failure mode, boundary, cache, revocation tail 같은 한 축을 바로 깊게 보기 | `deep dive` | [Session Revocation at Scale](./session-revocation-at-scale.md), [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md), [deep dive] [Permission Model Drift / AuthZ Graph Design](./permission-model-drift-authz-graph-design.md) |
| 장애 대응 순서, rotation 운영, rehearsal, blast-radius 분류가 먼저 필요함 | `playbook` / `runbook` / `drill` / `incident matrix` / `recovery` | [운영 / Incident catalog](#운영--incident-catalog) |
| security 바깥 handoff까지 같이 묶어 읽기 | `cross-category bridge` | [연결해서 보면 좋은 문서 (cross-category bridge)](#연결해서-보면-좋은-문서-cross-category-bridge) |
| 역할 라벨이나 검색 alias가 헷갈림 | `taxonomy` / `routing helper` | [Navigation Taxonomy](../../rag/navigation-taxonomy.md), [Retrieval Anchor Keywords](../../rag/retrieval-anchor-keywords.md) |

## 증상별 바로 가기

증상 문장으로 들어온 질문을 incident badge 문서(`playbook` / `runbook` / `drill` / `incident matrix` / `[recovery]`)나 `deep dive` 본문으로 다시 번역하는 shortcut이다. 첫 진입점과 follow-up 모두에 역할 cue를 명시해서, incident 대응 문서와 개념/원인 `deep dive`, section-level `catalog` / `cross-category bridge`를 같은 row 안에서도 바로 구분할 수 있게 유지한다.

| 지금 보이는 증상 / 질문 문장 | 먼저 갈 곳 | 이어서 볼 문서 |
|---|---|---|
| `JWKS outage`, `invalid signature`, `kid` miss, `unable to find JWK`, `auth verification outage`, `stale JWKS cache`, JWKS fetch/cache mismatch | `[playbook]` [JWT Signature Verification Failure Playbook](./jwt-signature-verification-failure-playbook.md) | `[deep dive]` [JWK Rotation / Cache Invalidation / `kid` Rollover](./jwk-rotation-cache-invalidation-kid-rollover.md), `[drill]` [JWT / JWKS Outage Recovery / Failover Drills](./jwt-jwks-outage-recovery-failover-drills.md) |
| rotation 직후 일부 인스턴스만 검증 실패하거나 old/new signer가 섞여 보임 | `[recovery]` [JWKS Rotation Cutover Failure / Recovery](./jwks-rotation-cutover-failure-recovery.md) | `[runbook]` [Key Rotation Runbook](./key-rotation-runbook.md), `[playbook]` [Signing Key Compromise Recovery Playbook](./signing-key-compromise-recovery-playbook.md) |
| `로그아웃했는데 계속 된다`, `logout still works`, revoke가 늦다, route별 tail이 남고 세션이 곳곳에 남는다 | `[catalog]` [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path) | `[deep dive]` [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md), `[deep dive]` [Session Revocation at Scale](./session-revocation-at-scale.md), `[deep dive]` [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md), `[system design]` [System Design: Auth Session Troubleshooting Bridge](../system-design/README.md#system-design-auth-session-troubleshooting-bridge), `[system design]` [System Design: Session Store / Claim-Version Cutover](../system-design/session-store-claim-version-cutover-design.md), `[system design]` [System Design: Canonical Revocation Plane Across Token Generations](../system-design/canonical-revocation-plane-across-token-generations-design.md), `[recovery]` [System Design: Revocation Bus Regional Lag Recovery](../system-design/revocation-bus-regional-lag-recovery-design.md) |
| operator-triggered revoke 이후 `requested`, `in_progress`, `fully_blocked_confirmed`를 언제 내려야 할지 헷갈림 | `[deep dive]` [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md) | `[deep dive]` [Revocation Impact Preview Data Contract](./revocation-impact-preview-data-contract.md), `[deep dive]` [Revocation Preview Drift Response Contract](./revocation-preview-drift-response-contract.md) |
| AOBO / break-glass revoke에서 `preview_id`, `access_group_id`, `revocation_request_id`를 어떤 event와 timeline row에 실어야 할지 헷갈림 | `[deep dive]` [AOBO Revocation Audit Event Schema](./aobo-revocation-audit-event-schema.md) | `[deep dive]` [Revocation Impact Preview Data Contract](./revocation-impact-preview-data-contract.md), `[deep dive]` [Canonical Security Timeline Event Schema](./canonical-security-timeline-event-schema.md), `[deep dive]` [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md) |
| break-glass는 종료됐는데 access/session tail이 남고 delegated refresh family, stale cache cleanup이 끝났는지 모르겠어 `cleanup_confirmed`를 언제 내려야 할지 헷갈림 | `[deep dive]` [Delegated Session Tail Cleanup](./delegated-session-tail-cleanup.md) | `[deep dive]` [Emergency Grant Cleanup Metrics](./emergency-grant-cleanup-metrics.md), `[deep dive]` [Refresh Token Family Invalidation at Scale](./refresh-token-family-invalidation-at-scale.md), `[deep dive]` [Incident-Close Break-Glass Gate](./incident-close-break-glass-gate.md) |
| delegated support access에서 start/end event id, lifecycle state, inbox/timeline close, `cleanup_confirmed` 경계를 어떻게 맞춰야 할지 헷갈림 | `[deep dive]` [AOBO Start / End Event Contract](./aobo-start-end-event-contract.md) | `[deep dive]` [Canonical Security Timeline Event Schema](./canonical-security-timeline-event-schema.md), `[deep dive]` [Customer-Facing Support Access Notifications](./customer-facing-support-access-notifications.md), `[deep dive]` [Audience Matrix for Support Access Events](./audience-matrix-for-support-access-events.md), `[deep dive]` [Delivery Surface Policy for Support Access Alerts](./delivery-surface-policy-for-support-access-alerts.md) |
| support access alert에서 email, in-app inbox, security timeline, alternate verified channel을 언제 써야 할지, mailbox compromise 때 primary email을 계속 믿어도 되는지 헷갈림 | `[deep dive]` [Delivery Surface Policy for Support Access Alerts](./delivery-surface-policy-for-support-access-alerts.md) | `[deep dive]` [Customer-Facing Support Access Notifications](./customer-facing-support-access-notifications.md), `[deep dive]` [Audience Matrix for Support Access Events](./audience-matrix-for-support-access-events.md), `[deep dive]` [Email Magic-Link Threat Model](./email-magic-link-threat-model.md) |
| tenant마다 privileged support change alert, security-contact opt-in, managed-identity escalation, compliance-sensitive support event retention을 어떤 schema로 저장하고 평가해야 할지 헷갈림 | `[deep dive]` [Tenant Policy Schema for Privileged Support Alerts](./tenant-policy-schema-for-privileged-support-alerts.md) | `[deep dive]` [Audience Matrix for Support Access Events](./audience-matrix-for-support-access-events.md), `[deep dive]` [Canonical Security Timeline Event Schema](./canonical-security-timeline-event-schema.md), `[deep dive]` [Delivery Surface Policy for Support Access Alerts](./delivery-surface-policy-for-support-access-alerts.md) |
| `missing-audit-trail`, `audit trail이 없다`, `누가 허용/거부했는지 안 남는다`, `decision log missing`, `allow/deny reason code가 없다`, `auth-signal-gap`, `auth telemetry gap`, `401/403 spike인데 reason bucket이 안 보임`, `observability blind spot` | `[deep dive]` [Auth Observability: SLI / SLO / Alerting](./auth-observability-sli-slo-alerting.md) | `[deep dive]` [AuthZ Decision Logging Design](./authz-decision-logging-design.md), `[deep dive]` [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md), `[deep dive]` [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md) |
| `302`, login loop, `401 -> 302` bounce, `hidden session mismatch`, 숨은 세션 불일치가 보임 | `[catalog]` [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path) | `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md), `[primer]` [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md), `[deep dive]` [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md), `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md), `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md), `[recovery]` [BFF Session Store Outage / Degradation Recovery](./bff-session-store-outage-degradation-recovery.md), `[system design]` [System Design: Auth Session Troubleshooting Bridge](../system-design/README.md#system-design-auth-session-troubleshooting-bridge), `[system design]` [System Design: Session Store Design at Scale](../system-design/session-store-design-at-scale.md) |
| social login callback은 성공했는데 첫 POST가 `403`이거나, callback 이후 CSRF 경계가 어디서 다시 시작되는지 헷갈림 | `[deep dive]` [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md) | `[deep dive]` [PKCE Failure Modes / Recovery](./pkce-failure-modes-recovery.md), `[primer]` [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md), `[deep dive]` [Session Fixation in Federated Login](./session-fixation-in-federated-login.md) |
| `authorization graph cache`, `graph snapshot`, `relationship cache`, delegated scope revoke 뒤 graph invalidation이 의심됨 | `[catalog]` [AuthZ / Tenant / Response Contracts deep dive catalog](#authz--tenant--response-contracts-deep-dive-catalog) | `[deep dive]` [Authorization Graph Caching](./authorization-graph-caching.md), `[deep dive]` [Authorization Caching / Staleness](./authorization-caching-staleness.md), `[deep dive]` [Permission Model Drift / AuthZ Graph Design](./permission-model-drift-authz-graph-design.md), `[deep dive]` [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md) |
| `role revoked but still works`, stale authority claim, old authorities가 JWT/session/cache/revocation 중 어디에 남는지 먼저 분해하고 싶음 | `[primer bridge]` [Claim Freshness After Permission Changes](./claim-freshness-after-permission-changes.md) | `[primer]` [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md), `[deep dive]` [AuthZ / Session Versioning Patterns](./authz-session-versioning-patterns.md), `[deep dive]` [Session Revocation at Scale](./session-revocation-at-scale.md), `[deep dive]` [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md), `[deep dive]` [Authorization Caching / Staleness](./authorization-caching-staleness.md), `[deep dive]` [Token Introspection vs Self-Contained JWT](./token-introspection-vs-self-contained-jwt.md) |
| `권한을 방금 줬는데 still 403`, `new role granted but forbidden`, `새 tenant membership을 받았는데 403`, re-login/refresh를 언제 요구해야 하는지 헷갈림 | `[primer]` [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md) | `[primer]` [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md), `[deep dive]` [Authorization Caching / Staleness](./authorization-caching-staleness.md), `[deep dive]` [AuthZ Negative Cache Failure Case Study](./authz-negative-cache-failure-case-study.md), `[deep dive]` [Token Introspection vs Self-Contained JWT](./token-introspection-vs-self-contained-jwt.md) |
| `scope`는 있는데 왜 이 API가 token을 안 받지, `aud`/`scope`/app permission이 같은 말인지 헷갈림 | `[primer]` [OAuth Scope vs API Audience vs Application Permission](./oauth-scope-vs-api-audience-vs-application-permission.md) | `[primer]` [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md), `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md), [JWT Claims vs Roles vs Spring Authorities vs Application Permissions](./jwt-claims-roles-authorities-permissions-mapping.md), `[deep dive]` [Token Exchange / Impersonation Risks](./token-exchange-impersonation-risks.md) |
| JWT는 valid한데 Spring Security route / method security에서만 `403`이고, `JwtAuthenticationConverter`, `ROLE_` / `SCOPE_`, `hasRole` / `hasAuthority` mismatch가 의심됨 | `[deep dive]` [Spring Authority Mapping Pitfalls](./spring-authority-mapping-pitfalls.md) | `[primer]` [JWT Claims vs Roles vs Spring Authorities vs Application Permissions](./jwt-claims-roles-authorities-permissions-mapping.md), `[deep dive]` [Spring Security Filter Chain](../spring/spring-security-filter-chain.md), `[primer]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) |
| `role`은 있는데 왜 남의 resource는 못 보지, `scope=orders.read`면 모든 주문인가, role/scope/ownership 차이가 헷갈림 | `[primer]` [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md) | `[deep dive]` [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md), [JWT Claims vs Roles vs Spring Authorities vs Application Permissions](./jwt-claims-roles-authorities-permissions-mapping.md), `[primer]` [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) |
| stale deny가 남거나 특정 tenant에서만 `403`이 반복되고, 같은 실패가 `401`/`404` 사이에서 흔들림 | `[deep dive]` [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md) | `[deep dive]` [Authorization Caching / Staleness](./authorization-caching-staleness.md), `[deep dive]` [Authorization Graph Caching](./authorization-graph-caching.md), `[deep dive]` [AuthZ Negative Cache Failure Case Study](./authz-negative-cache-failure-case-study.md), [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md) |
| nonce/replay store가 죽어서 중복 요청이 막히지 않거나 정상 요청이 과차단됨 | `[recovery]` [Replay Store Outage / Degradation Recovery](./replay-store-outage-degradation-recovery.md) | `[deep dive]` [Token Misuse Detection / Replay Containment](./token-misuse-detection-replay-containment.md), `[deep dive]` [API Key, HMAC Signed Request, Replay Protection](./api-key-hmac-signature-replay-protection.md) |
| key compromise, emergency revoke, blast radius부터 빨리 판단해야 함 | `[playbook]` [Signing Key Compromise Recovery Playbook](./signing-key-compromise-recovery-playbook.md) | `[incident matrix]` [Auth Incident Triage / Blast-Radius Recovery Matrix](./auth-incident-triage-blast-radius-recovery-matrix.md), `[runbook]` [Key Rotation Runbook](./key-rotation-runbook.md) |
| `SCIM disable했는데 still access`, deprovision은 끝났는데 session/authz tail이 남음, `backfill is green but access tail remains`, `decision parity`, `auth shadow divergence` | `[cross-category bridge]` [Identity / Delegation / Lifecycle](#identity--delegation--lifecycle) | `[deep dive]` [SCIM Deprovisioning / Session / AuthZ Consistency](./scim-deprovisioning-session-authz-consistency.md), `[deep dive]` [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md), `[deep dive]` [Database: Online Backfill Verification, Drift Checks, and Cutover Gates](../database/online-backfill-verification-cutover-gates.md), `[system design]` [System Design: Database / Security Authority Bridge](../system-design/README.md#system-design-database-security-authority-bridge), `[system design]` [System Design: Verification / Shadowing / Authority Bridge](../system-design/README.md#system-design-verification-shadowing-authority-bridge), `[system design]` [System Design: Database / Security Identity Bridge Cutover 설계](../system-design/database-security-identity-bridge-cutover-design.md) |
| support AOBO나 break-glass를 누구에게 알려야 할지, email/push/in-app copy를 어떻게 맞출지 헷갈림 | `[deep dive]` [Audience Matrix for Support Access Events](./audience-matrix-for-support-access-events.md) | `[deep dive]` [Customer-Facing Support Access Notifications](./customer-facing-support-access-notifications.md), `[deep dive]` [Support Operator / Acting-on-Behalf-Of Controls](./support-operator-acting-on-behalf-of-controls.md) |

## 기본 primer

아래 문서들은 security 내부의 broad survey가 아니라, 이후 `deep dive catalog`를 읽기 전에 기초 축을 맞추는 `primer`다.

**🟢 Beginner 입문 문서 (security 처음이라면 여기서 시작)**

- [보안 기초: 왜 보안이 필요한가](./security-basics-what-and-why.md): CIA 트라이어드(기밀성·무결성·가용성)와 인증·인가의 최소 개념을 잡는 security 첫 진입 문서다. 백엔드에서 보안이 어디서 등장하는지 흐름을 먼저 본 뒤 다른 primer로 이어가기에 좋다.
- [HTTPS와 TLS 기초](./https-tls-beginner.md): HTTP와 HTTPS의 차이, TLS 핸드셰이크, CA 인증서가 무엇인지를 입문자 관점에서 정리한 primer다. 전송 구간 보안이 왜 필요한지부터 잡고 [HTTPS / HSTS / MITM](./https-hsts-mitm.md) 심화로 이어지기에 좋다.
- [세션·쿠키·JWT 기초](./session-cookie-jwt-basics.md): HTTP 무상태성 때문에 로그인 상태를 유지하는 방법(서버 세션 vs JWT)과 쿠키 보안 속성(HttpOnly·Secure·SameSite)을 초보자 관점에서 정리한 primer다. [JWT 깊이 파기](./jwt-deep-dive.md)와 [네트워크 HTTP 상태·세션·캐시](../network/http-state-session-cache.md) 사이를 잇는 bridge다.
- [비밀번호 저장 기초: 왜 해시를 써야 하나](./password-hashing-basics.md): 평문·가역 암호화·빠른 해시가 왜 부족한지, salt와 bcrypt가 무엇을 다르게 하는지를 입문자 관점에서 설명한다. [비밀번호 저장: bcrypt / scrypt / argon2](./password-storage-bcrypt-scrypt-argon2.md) 심화 전 기초 primer다.
- [XSS와 CSRF 기초](./xss-csrf-basics.md): XSS(스크립트 실행)와 CSRF(인증 상태 도용 요청)의 차이, 각각의 방어 방향(출력 이스케이프 vs CSRF 토큰·SameSite)을 초보자 관점에서 정리한 primer다. [XSS / CSRF / Spring Security](./xss-csrf-spring-security.md) 심화 전에 먼저 읽으면 좋다.
- [SQL 인젝션 기초](./sql-injection-basics.md): 사용자 입력이 SQL 쿼리 구조에 끼어드는 원리와 PreparedStatement / 파라미터 바인딩으로 입력을 값으로만 처리하는 방어 패턴을 입문자 관점에서 정리한 primer다. [SQL 인젝션: PreparedStatement를 넘어서](./sql-injection-beyond-preparedstatement.md) 심화 전에 먼저 읽으면 좋다.
- [CORS 기초](./cors-basics.md): 동일 출처 정책(SOP)과 CORS 에러가 왜 브라우저에서만 발생하는지, `Access-Control-Allow-Origin` 헤더의 역할, Spring Boot에서 CORS를 설정하는 방법을 입문자 관점에서 정리한 primer다. [CORS / SameSite / Preflight 심화](./cors-samesite-preflight.md) 전에 먼저 읽으면 좋다.
- [입력값 검증 기초](./input-validation-basics.md): "서버는 클라이언트를 신뢰하지 않는다"는 원칙과 형식 검증·의미 검증·allowlist 방식, Bean Validation 활용을 입문자 관점에서 정리한 primer다. 프론트엔드 검증만으로 충분하지 않은 이유를 먼저 잡는 데 좋다.
- [대칭키·비대칭키 암호화 기초](./symmetric-asymmetric-encryption-basics.md): AES(대칭)와 RSA(비대칭)의 차이, 키 배포 문제, 디지털 서명, HTTPS가 두 방식을 결합하는 이유를 입문자 관점에서 정리한 primer다. [봉투 암호화와 KMS 기초](./envelope-encryption-kms-basics.md) 심화 전에 먼저 읽으면 좋다.
- [API 키 기초](./api-key-basics.md): API 키의 역할, 코드 하드코딩 금지와 환경 변수 보관, 키 노출 시 대응, API 키와 OAuth 토큰의 차이를 입문자 관점에서 정리한 primer다. [시크릿 관리·로테이션·누출 패턴](./secret-management-rotation-leak-patterns.md) 심화 전에 먼저 읽으면 좋다.

- [인증과 인가의 차이](./authentication-vs-authorization.md): authn / authz 경계가 섞일 때 먼저 잡는 primer다. `principal`, `session`, `permission model`의 최소 단위를 같이 정리해 두면 이후 authz / tenant 계열 deep dive로 내려가기 좋다.
- [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md): `role check`, OAuth `scope`, 객체 `ownership`이 서로 다른 질문이라는 점을 짧게 분리해 주는 beginner primer다. `scope=orders.read`가 모든 주문을 뜻하지 않고, role만으로 object-level allow가 끝나지 않는다는 점을 먼저 정리한 뒤 IDOR / deeper authz로 내려가기에 좋다.
- [OAuth Scope vs API Audience vs Application Permission](./oauth-scope-vs-api-audience-vs-application-permission.md): external token의 `aud`, OAuth `scope`, 서비스 내부 permission이 서로 다른 boundary라는 점을 multi-service 관점에서 정리하는 primer다. gateway audience와 service audience, downscoped token, business permission을 같이 분리하고 싶을 때 읽으면 좋다.
- [JWT Claims vs Roles vs Spring Authorities vs Application Permissions](./jwt-claims-roles-authorities-permissions-mapping.md): JWT claim, role, Spring authority, application permission이 서로 다른 층위라는 점을 초보자 관점에서 정리한 primer다. `roles`, `scope`, `ROLE_`, `hasRole`, `hasAuthority`가 섞일 때 바로 읽으면 좋다.
- [Spring Authority Mapping Pitfalls](./spring-authority-mapping-pitfalls.md): JWT는 valid한데 Spring route / method security에서만 `403`이 나는 상황을 디버깅하는 deep dive다. `JwtAuthenticationConverter`, `ROLE_`, `SCOPE_`, `hasRole`, `hasAuthority` mismatch를 실제 authority 문자열 기준으로 좁힌다.
- [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md): 로그인된 session이 살아 있어도 role, permission, tenant membership이 바뀌면 old claim이 낡을 수 있다는 점을 초보자 관점에서 정리한 primer다. 이후 [AuthZ / Session Versioning Patterns](./authz-session-versioning-patterns.md), session revocation, authz caching, SCIM deprovisioning 문서로 이어지는 bridge 역할을 한다.
- [Claim Freshness After Permission Changes](./claim-freshness-after-permission-changes.md): role/permission change가 source of truth에서 끝난 뒤 JWT claim, server session principal, authz cache, revoke plane으로 각각 어떻게 전파되는지 한 장의 timeline으로 묶어 주는 primer bridge다. `old authority가 왜 아직 남는가`를 층별로 분해한 뒤 [AuthZ / Session Versioning Patterns](./authz-session-versioning-patterns.md), [deep dive] [Authorization Caching / Staleness](./authorization-caching-staleness.md), [Session Revocation at Scale](./session-revocation-at-scale.md)로 이어지기 좋다.
- [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md): source of truth에서는 grant가 끝났는데 request path에서는 old claim이나 stale deny cache 때문에 `403`이 남을 수 있다는 점을 beginner/intermediate 관점에서 정리한 primer다. [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md)와 [deep dive] [Authorization Caching / Staleness](./authorization-caching-staleness.md) 사이를 잇는 bridge 역할을 한다.
- [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md): org/team/tenant 이동이 단순 selector 변경이 아니라 active tenant, membership snapshot, derived scope를 refresh해야 하는 session coherence 문제라는 점을 짧게 정리한 primer다. stale cross-tenant access를 왜 막아야 하는지 role-change primer 바로 다음 단계로 읽기 좋다.
- [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md): 위 primer 다음 단계다. `401` / `403` / `404`를 authn failure, authz deny, concealment `404`로 나눠 초보자 관점에서 바로 구분하게 돕고, safe error body 예시와 `request_id` 중심 내부 log 필드 매핑까지 같이 보여 준다.
- [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md): 브라우저 page redirect와 raw API `401`을 같은 뜻으로 읽지 않도록 돕는 primer bridge다. `SavedRequest`, session cookie, login loop를 처음 분해할 때 바로 붙인다.
- [Signed Cookies / Server Sessions / JWT Trade-offs](./signed-cookies-server-sessions-jwt-tradeoffs.md): browser/server session 모델과 token 보관 전략의 기본 축을 잡는 primer다. 이후 [Browser / Session Coherence](#browser--session-coherence), session coherence, browser / BFF boundary catalog로 이어진다.
- [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md): OAuth/OIDC authorization flow와 token 발급 경로를 복습하는 primer다. 이후 [Browser / Session Coherence](#browser--session-coherence), browser / BFF, service / delegation boundary deep dive로 이어지고, callback/login-completion failure mode는 [PKCE Failure Modes / Recovery](./pkce-failure-modes-recovery.md)와 [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md)로 이어서 보면 된다. 브라우저가 없는 기기는 [OAuth Device Code Flow / Security Model](./oauth-device-code-flow-security.md), front-channel request hardening은 [OAuth PAR / JAR Basics](./oauth-par-jar-basics.md), server-side token endpoint client proof 선택은 [OAuth Client Authentication: `client_secret_basic`, `private_key_jwt`, mTLS](./oauth-client-authentication-private-key-jwt-mtls.md)로 분기해서 보면 된다.

아래 구간은 설명 본문이 아니라 theme별 `deep dive catalog`다. 순서대로 읽는 `survey`가 아니라, 문제 축에 맞는 개별 문서를 고르는 index로 보면 된다. mixed catalog에서 `[playbook]`, `[runbook]`, `[drill]`, `[incident matrix]`는 서로 다른 incident badge다. 각각 live triage, repeatable operation, rehearsal/validation, blast-radius routing을 뜻하고, 기준은 [Navigation Taxonomy의 Incident Badge Vocabulary](../../rag/navigation-taxonomy.md#incident-badge-vocabulary)를 따른다. `[recovery]` 라벨은 outage/degradation incident를 직접 다루지만 full step runbook은 아닌 incident-oriented recovery deep dive라는 뜻이다. mixed incident catalog에서는 incident badge 문서 옆에 놓인 개념 본문도 bare link로 두지 않고 `[deep dive]` cue를 붙인다. badge가 없는 pure deep-dive-only catalog에서는 필요할 때만 bare link를 유지한다.

## 운영 / Incident catalog

이 구간은 incident 대응 순서가 먼저 필요한 `playbook`, repeatable operator 절차인 `runbook`, rehearsal 중심 `drill`, 분류표 역할의 `incident matrix`, 그리고 recovery-oriented `deep dive`를 함께 묶은 incident-first catalog다.

- `[playbook]` [JWT Signature Verification Failure Playbook](./jwt-signature-verification-failure-playbook.md)
- `[drill]` [JWT / JWKS Outage Recovery / Failover Drills](./jwt-jwks-outage-recovery-failover-drills.md)
- `[deep dive]` [JWK Rotation / Cache Invalidation / `kid` Rollover](./jwk-rotation-cache-invalidation-kid-rollover.md)
- `[recovery]` [JWKS Rotation Cutover Failure / Recovery](./jwks-rotation-cutover-failure-recovery.md)
- `[runbook]` [Key Rotation Runbook](./key-rotation-runbook.md)
- `[playbook]` [Signing Key Compromise Recovery Playbook](./signing-key-compromise-recovery-playbook.md)
- `[incident matrix]` [Auth Incident Triage / Blast-Radius Recovery Matrix](./auth-incident-triage-blast-radius-recovery-matrix.md)
- `[deep dive]` [Auth Observability: SLI / SLO / Alerting](./auth-observability-sli-slo-alerting.md)
- `[deep dive]` [deep dive] [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md)
- `[deep dive]` [AuthZ Kill Switch / Break-Glass Governance](./authz-kill-switch-break-glass-governance.md)
- `[deep dive]` [deep dive] [Incident-Close Break-Glass Gate](./incident-close-break-glass-gate.md)
- `[deep dive]` [Token Misuse Detection / Replay Containment](./token-misuse-detection-replay-containment.md)
- `[recovery]` [Replay Store Outage / Degradation Recovery](./replay-store-outage-degradation-recovery.md)
- `[deep dive]` [Session Revocation at Scale](./session-revocation-at-scale.md)
- `[deep dive]` [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md)
- `[deep dive]` [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md)
- `[deep dive]` [OIDC Back-Channel Logout / Session Coherence](./oidc-backchannel-logout-session-coherence.md)

## Hardware Trust / Recovery deep dive catalog

- `[deep dive]` [Hardware-Backed Keys / Attestation](./hardware-backed-keys-attestation.md)
- `[recovery]` [Hardware Attestation Policy / Failure Recovery](./hardware-attestation-policy-failure-recovery.md)
- `[playbook]` [Signing Key Compromise Recovery Playbook](./signing-key-compromise-recovery-playbook.md)
- `[deep dive]` [mTLS Certificate Rotation / Trust Bundle Rollout](./mtls-certificate-rotation-trust-bundle-rollout.md)

## Session Coherence / Assurance deep dive catalog

- [Role Change and Session Freshness Basics](./role-change-session-freshness-basics.md)
- [Claim Freshness After Permission Changes](./claim-freshness-after-permission-changes.md)
- [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md)
- [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md)
- [AuthZ / Session Versioning Patterns](./authz-session-versioning-patterns.md)
- [Session Revocation at Scale](./session-revocation-at-scale.md)
- [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md)
- [OIDC Back-Channel Logout / Session Coherence](./oidc-backchannel-logout-session-coherence.md)
- [MFA / Step-Up Auth Design](./mfa-step-up-auth-design.md)
- [Step-Up Session Coherence / Auth Assurance](./step-up-session-coherence-auth-assurance.md)
- [Session Quarantine / Partial Lockdown Patterns](./session-quarantine-partial-lockdown-patterns.md)
- [Device / Session Graph Revocation Design](./device-session-graph-revocation-design.md)
- [Session Inventory UX / Revocation Scope Design](./session-inventory-ux-revocation-scope-design.md)
- [Revocation Impact Preview Data Contract](./revocation-impact-preview-data-contract.md)
- [deep dive] [Revocation Preview Drift Response Contract](./revocation-preview-drift-response-contract.md)
- [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md)
- [Delegated Session Tail Cleanup](./delegated-session-tail-cleanup.md)
- [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)

## Browser / Session Coherence

브라우저 symptom으로 들어온 auth/session 질문의 canonical entrypoint다.
`302`/login-loop와 revoke tail을 같은 묶음에서 받되, 아래 troubleshooting path에서 먼저 `saved request / hidden session` 문제와 `revocation propagation` 문제를 갈라 본다.
redirect 검증, callback 이후 세션 재발급, frame/script 정책, browser-visible credential 축을 한 번에 잡고 싶으면 아래 browser/server boundary catalog와 `Session / Boundary / Replay` bridge bullet을 같이 보면 된다.

- primer에서 다시 들어오면 [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md) -> [Cookie / Session / JWT 브라우저 흐름 입문](../network/cookie-session-jwt-browser-flow-primer.md) -> [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> [Signed Cookies / Server Sessions / JWT Trade-offs](./signed-cookies-server-sessions-jwt-tradeoffs.md) -> [OAuth2 Authorization Code Grant](./oauth2-authorization-code-grant.md) 순으로 올라오면 cookie/session 상태 저장, redirect 응답의 cookie 저장, 원래 URL 복귀, callback 이후 내부 세션 발급 경계가 한 줄로 이어진다.
- raw `401`과 browser `302 -> /login`이 같은 말처럼 보여 첫 판별이 안 되면 [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)에서 `SavedRequest`, session cookie, API HTML fallback을 먼저 분리한 뒤 아래 troubleshooting path로 내려오면 된다.
- front-channel login completion hardening은 [Open Redirect Hardening](./open-redirect-hardening.md), [PKCE Failure Modes / Recovery](./pkce-failure-modes-recovery.md), [Session Fixation in Federated Login](./session-fixation-in-federated-login.md), [Session Fixation, Clickjacking, CSP](./session-fixation-clickjacking-csp.md)를 먼저 묶어 보면 된다.
- browser/server credential translation은 [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md), [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md), [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)로 이어 읽으면 된다.

### Browser / Session Troubleshooting Path

- `cookie`, `session`, `JWT`는 아는데 `SavedRequest`, `hidden JSESSIONID`, `SecurityContextRepository`가 갑자기 등장해 문장이 안 읽히면 [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md) -> [Cookie / Session / JWT 브라우저 흐름 입문](../network/cookie-session-jwt-browser-flow-primer.md) -> [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> [Signed Cookies / Server Sessions / JWT Trade-offs](./signed-cookies-server-sessions-jwt-tradeoffs.md) -> [Spring Security 아키텍처](../spring/spring-security-architecture.md) -> [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) -> [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md) 순으로 먼저 올라와 cookie 자동 전송, redirect 응답의 저장/복귀, hidden session 생성, Spring persistence, browser/BFF token translation 축을 맞춘다.
- `SavedRequest`, `login loop`, `401 -> 302` bounce, `hidden session mismatch`, 숨은 `JSESSIONID`가 먼저 보이면 [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md)에서 browser-side escalation을 먼저 읽고, [Browser `401` vs `302` Login Redirect Guide](./browser-401-vs-302-login-redirect-guide.md)에서 raw auth failure와 browser redirect를 갈라 본 뒤, [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md)에서 saved-request bounce 여부를 확인하고, 다음 단계로 [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md), [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md) 순서로 좁힌다. cookie는 살아 있는데 서버 세션이나 token translation이 사라진 쪽이면 바로 `[recovery]` [BFF Session Store Outage / Degradation Recovery](./bff-session-store-outage-degradation-recovery.md)로 간다. 여기서 session-store 원인까지 내려가야 하면 `[system design]` [System Design: Auth Session Troubleshooting Bridge](../system-design/README.md#system-design-auth-session-troubleshooting-bridge), `[system design]` [System Design: Session Store Design at Scale](../system-design/session-store-design-at-scale.md)로 handoff한다.
- `로그아웃했는데 계속 된다`, `logout still works`, revoke가 늦다, route/region별 tail이 남으면 [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md)에서 propagation 원인을 먼저 분리하고, [Session Revocation at Scale](./session-revocation-at-scale.md), [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md)로 기대 guarantee와 status vocabulary를 맞춘다. federated logout mapping은 [OIDC Back-Channel Logout / Session Coherence](./oidc-backchannel-logout-session-coherence.md), system-design 쪽 tail은 `[system design]` [System Design: Auth Session Troubleshooting Bridge](../system-design/README.md#system-design-auth-session-troubleshooting-bridge), `[system design]` [System Design: Session Store / Claim-Version Cutover](../system-design/session-store-claim-version-cutover-design.md), `[system design]` [System Design: Canonical Revocation Plane Across Token Generations](../system-design/canonical-revocation-plane-across-token-generations-design.md), `[recovery]` [System Design: Revocation Bus Regional Lag Recovery](../system-design/revocation-bus-regional-lag-recovery-design.md)로 이어 붙인다.
- redirect hardening, PKCE verifier/state, callback 이후 세션 재발급, browser-visible credential 설계 자체를 보고 싶으면 [Open Redirect Hardening](./open-redirect-hardening.md), [PKCE Failure Modes / Recovery](./pkce-failure-modes-recovery.md), [Session Fixation in Federated Login](./session-fixation-in-federated-login.md), [Session Fixation, Clickjacking, CSP](./session-fixation-clickjacking-csp.md), [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md), [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md)를 설계 축으로 본다.

## Browser / Server Boundary deep dive catalog

- [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md)
- [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md)
- [Open Redirect Hardening](./open-redirect-hardening.md)
- [PKCE Failure Modes / Recovery](./pkce-failure-modes-recovery.md)
- [Session Fixation in Federated Login](./session-fixation-in-federated-login.md)
- [Session Fixation, Clickjacking, CSP](./session-fixation-clickjacking-csp.md)
- [OAuth PAR / JAR Basics](./oauth-par-jar-basics.md)
- [OAuth Device Code Flow / Security Model](./oauth-device-code-flow-security.md)
- [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)
- `[recovery]` [BFF Session Store Outage / Degradation Recovery](./bff-session-store-outage-degradation-recovery.md)
- [Gateway Auth Context Headers / Trust Boundary](./gateway-auth-context-header-trust-boundary.md)
- [Trust Boundary Bypass / Detection Signals](./trust-boundary-bypass-detection-signals.md)
- [OAuth Client Authentication: `client_secret_basic`, `private_key_jwt`, mTLS](./oauth-client-authentication-private-key-jwt-mtls.md)

## Replay / Token Misuse / Session Defense deep dive catalog

- [deep dive] [API Key, HMAC Signed Request, Replay Protection](./api-key-hmac-signature-replay-protection.md)
- [Webhook Signature Verification / Replay Defense](./webhook-signature-verification-replay-defense.md)
- [One-Time Token Consumption Race / Burn-After-Read](./one-time-token-consumption-race-burn-after-read.md)
- [DPoP / Token Binding Basics](./dpop-token-binding-basics.md)
- [Proof-of-Possession vs Bearer Token Trade-offs](./proof-of-possession-vs-bearer-token-tradeoffs.md)
- [mTLS Client Auth vs Certificate-Bound Access Token](./mtls-client-auth-vs-certificate-bound-access-token.md)
- [Refresh Token Rotation / Reuse Detection](./refresh-token-rotation-reuse-detection.md)
- [deep dive] [Refresh Token Family Invalidation at Scale](./refresh-token-family-invalidation-at-scale.md)
- [Device Binding Caveats](./device-binding-caveats.md)
- [deep dive] [Email Magic-Link Threat Model](./email-magic-link-threat-model.md)
- [Token Misuse Detection / Replay Containment](./token-misuse-detection-replay-containment.md)
- `[recovery]` [Replay Store Outage / Degradation Recovery](./replay-store-outage-degradation-recovery.md)
- [Abuse Throttling / Runtime Signals](./abuse-throttling-runtime-signals.md)

## Identity Lifecycle / Provisioning deep dive catalog

- [SCIM Provisioning Security](./scim-provisioning-security.md)
- [SCIM Drift / Reconciliation](./scim-drift-reconciliation.md)
- [SCIM Deprovisioning / Session / AuthZ Consistency](./scim-deprovisioning-session-authz-consistency.md)

## Service / Delegation Boundaries deep dive catalog

- [OAuth Scope vs API Audience vs Application Permission](./oauth-scope-vs-api-audience-vs-application-permission.md)
- [Service-to-Service Auth: mTLS, JWT, SPIFFE](./service-to-service-auth-mtls-jwt-spiffe.md)
- [mTLS Client Auth vs Certificate-Bound Access Token](./mtls-client-auth-vs-certificate-bound-access-token.md)
- [Gateway Auth Context Headers / Trust Boundary](./gateway-auth-context-header-trust-boundary.md)
- [Trust Boundary Bypass / Detection Signals](./trust-boundary-bypass-detection-signals.md)
- [Token Exchange / Impersonation Risks](./token-exchange-impersonation-risks.md)
- [Workload Identity / Long-Lived Service Account Keys](./workload-identity-vs-long-lived-service-account-keys.md)
- [Workload Identity / User Context Propagation Boundaries](./workload-identity-user-context-propagation-boundaries.md)
- [deep dive] [Support Operator / Acting-on-Behalf-Of Controls](./support-operator-acting-on-behalf-of-controls.md)
- [deep dive] [Customer-Facing Support Access Notifications](./customer-facing-support-access-notifications.md)
- [deep dive] [Delivery Surface Policy for Support Access Alerts](./delivery-surface-policy-for-support-access-alerts.md)
- [deep dive] [Canonical Security Timeline Event Schema](./canonical-security-timeline-event-schema.md)
- [AOBO Start / End Event Contract](./aobo-start-end-event-contract.md)
- [AOBO Revocation Audit Event Schema](./aobo-revocation-audit-event-schema.md)
- [deep dive] [Audience Matrix for Support Access Events](./audience-matrix-for-support-access-events.md)
- [Tenant Policy Schema for Privileged Support Alerts](./tenant-policy-schema-for-privileged-support-alerts.md)
- [Operator Tooling State Semantics / Safety Rails](./operator-tooling-state-semantics-safety-rails.md)
- [Emergency Grant Cleanup Metrics](./emergency-grant-cleanup-metrics.md)
- [Delegated Session Tail Cleanup](./delegated-session-tail-cleanup.md)
- [deep dive] [Incident-Close Break-Glass Gate](./incident-close-break-glass-gate.md)
- [Session Inventory UX / Revocation Scope Design](./session-inventory-ux-revocation-scope-design.md)
- [Revocation Impact Preview Data Contract](./revocation-impact-preview-data-contract.md)
- [deep dive] [Revocation Preview Drift Response Contract](./revocation-preview-drift-response-contract.md)
- [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md)

## AuthZ / Tenant / Response Contracts deep dive catalog

- [Role vs Scope vs Ownership Primer](./role-vs-scope-vs-ownership-primer.md)
- [OAuth Scope vs API Audience vs Application Permission](./oauth-scope-vs-api-audience-vs-application-permission.md)
- [Tenant Membership Change vs Session Scope Basics](./tenant-membership-change-session-scope-basics.md)
- [IDOR / BOLA Patterns and Fixes](./idor-bola-patterns-and-fixes.md)
- [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md)
- [JWT Claims vs Roles vs Spring Authorities vs Application Permissions](./jwt-claims-roles-authorities-permissions-mapping.md)
- [Spring Authority Mapping Pitfalls](./spring-authority-mapping-pitfalls.md)
- [PDP / PEP Boundaries Design](./pdp-pep-boundaries-design.md)
- [deep dive] [Permission Model Drift / AuthZ Graph Design](./permission-model-drift-authz-graph-design.md)
- [AuthZ / Session Versioning Patterns](./authz-session-versioning-patterns.md)
- [Grant Path Freshness and Stale Deny Basics](./grant-path-freshness-stale-deny-basics.md)
- [deep dive] [Authorization Caching / Staleness](./authorization-caching-staleness.md)
- [deep dive] [Authorization Graph Caching](./authorization-graph-caching.md)
- [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md)
- [deep dive] [AuthZ Negative Cache Failure Case Study](./authz-negative-cache-failure-case-study.md)
- [deep dive] [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md)
- [AuthZ Kill Switch / Break-Glass Governance](./authz-kill-switch-break-glass-governance.md)
- [deep dive] [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md)
- [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md)
- [Background Job Auth Context / Revalidation](./background-job-auth-context-revalidation.md)
- [AuthZ Decision Logging Design](./authz-decision-logging-design.md)
- [deep dive] [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)

## 추천 학습 흐름 (category-local survey)

아래 흐름은 security 내부에서 `primer -> deep dive -> playbook`을 잇는 category-local survey다.

### 1. JWT / Session / Recovery

```text
Signed Cookies / Server Sessions / JWT Trade-offs → Role Change and Session Freshness Basics → Claim Freshness After Permission Changes → AuthZ / Session Versioning Patterns → JWT 깊이 파기 → Refresh Token Rotation / Reuse Detection → JWK Rotation / Cache Invalidation / kid Rollover → `[recovery]` JWKS Rotation Cutover Failure / Recovery → `[drill]` JWT / JWKS Outage Recovery / Failover Drills → `[playbook]` Signing Key Compromise Recovery Playbook → Session Revocation at Scale → Revocation Propagation Lag / Debugging → Revocation Propagation Status Contract
```

### 2. OAuth / Browser / BFF

이 구간의 mainline은 브라우저 redirect/BFF 기준이고, `OAuth PAR / JAR`와 `OAuth Device Code`는 inline exception이 아니라 아래 branch point에서 따로 갈라지는 side branch로 읽는다.

#### 2-A. Mainline: Browser Redirect / BFF

```text
OAuth2 Authorization Code Grant → OAuth Scope vs API Audience vs Application Permission → PKCE Failure Modes / Recovery → Open Redirect Hardening → Session Fixation in Federated Login → Session Fixation, Clickjacking, CSP → Browser Storage Threat Model for Tokens → CSRF in SPA + BFF Architecture → Browser / BFF Token Boundary / Session Translation → OAuth Client Authentication → `[recovery]` BFF Session Store Outage / Degradation Recovery → Step-Up Session Coherence / Auth Assurance → OIDC Back-Channel Logout / Session Coherence
```

#### 2-B. Branch Point: Authorization Request Hardening

```text
OAuth2 Authorization Code Grant → OAuth PAR / JAR Basics → Open Redirect Hardening
```

`PAR / JAR`는 `Open Redirect Hardening` 앞에 잠깐 끼워 넣는 예외가 아니라, authorization request 자체를 hardening해야 할 때 Authorization Code에서 먼저 갈라지는 branch다. 이 branch를 읽고 나면 mainline의 browser hardening 흐름으로 합류하면 된다.

#### 2-C. Branch Point: Browserless / Cross-Device Login

```text
OAuth Device Code Flow / Security Model
```

브라우저 callback이 없는 CLI, TV, 콘솔은 Authorization Code mainline의 예외 처리로 넘기지 말고 여기서 별도 시작한다. sender-constrained token이나 device-bound hardening까지 같이 보려면 [DPoP / Token Binding Basics](./dpop-token-binding-basics.md), [Proof-of-Possession vs Bearer Token Trade-offs](./proof-of-possession-vs-bearer-token-tradeoffs.md), [Device Binding Caveats](./device-binding-caveats.md)를 이어서 보면 된다.

### 3. Service Trust / Delegation

```text
Service-to-Service Auth: mTLS, JWT, SPIFFE → Gateway Auth Context Headers / Trust Boundary → Trust Boundary Bypass / Detection Signals → Token Exchange / Impersonation Risks → Workload Identity / User Context Propagation Boundaries → Support Operator / Acting-on-Behalf-Of Controls → Canonical Security Timeline Event Schema → AOBO Start / End Event Contract → Customer-Facing Support Access Notifications → Audience Matrix for Support Access Events → Tenant Policy Schema for Privileged Support Alerts → Delivery Surface Policy for Support Access Alerts → Operator Tooling State Semantics / Safety Rails → AuthZ Kill Switch / Break-Glass Governance → Emergency Grant Cleanup Metrics → Delegated Session Tail Cleanup → Incident-Close Break-Glass Gate → Revocation Impact Preview Data Contract → Revocation Preview Drift Response Contract → Revocation Propagation Status Contract → AOBO Revocation Audit Event Schema → Session Inventory UX / Revocation Scope Design
```

### 4. AuthZ / Tenant / Detection

```text
인증과 인가의 차이 → Role vs Scope vs Ownership Primer → OAuth Scope vs API Audience vs Application Permission → JWT Claims vs Roles vs Spring Authorities vs Application Permissions → Spring Authority Mapping Pitfalls → IDOR / BOLA Patterns and Fixes → Beginner Guide to Auth Failure Responses: `401` / `403` / `404` → PDP / PEP Boundaries Design → Permission Model Drift / AuthZ Graph Design → AuthZ / Session Versioning Patterns → Grant Path Freshness and Stale Deny Basics → Delegated Admin / Tenant RBAC → Authorization Caching / Staleness → Authorization Graph Caching → AuthZ Cache Inconsistency / Runtime Debugging → Authorization Runtime Signals / Shadow Evaluation → AuthZ Kill Switch / Break-Glass Governance → Tenant Isolation / AuthZ Testing → Token Misuse Detection / Replay Containment → Auth Observability: SLI / SLO / Alerting
```

### 5. Abuse / Replay / PoP

```text
Rate Limiting vs Brute Force Defense → Abuse Throttling / Runtime Signals → DPoP / Token Binding Basics → Proof-of-Possession vs Bearer Token Trade-offs → mTLS Client Auth vs Certificate-Bound Access Token → `[recovery]` Replay Store Outage / Degradation Recovery
```

### 6. SCIM / Lifecycle / Drift

```text
SCIM Provisioning Security → SCIM Drift / Reconciliation → SCIM Deprovisioning / Session / AuthZ Consistency → Authorization Runtime Signals / Shadow Evaluation → AuthZ Decision Logging Design → Audit Logging for Auth / AuthZ Traceability
```

### 7. Security + System Design

```text
`[drill]` JWT / JWKS Outage Recovery / Failover Drills → `[incident matrix]` Auth Incident Triage / Blast-Radius Recovery Matrix → `[system design]` Service Discovery / Health Routing → `[system design]` Global Traffic Failover Control Plane → `[system design]` Session Store Design at Scale
```

### 8. Database + Security + System Design

```text
`[deep dive]` SCIM Drift / Reconciliation → `[deep dive]` Database: Online Backfill Verification, Drift Checks, and Cutover Gates → `[deep dive]` SCIM Deprovisioning / Session / AuthZ Consistency → `[deep dive]` Authorization Runtime Signals / Shadow Evaluation → `[system design]` Database / Security Identity Bridge Cutover 설계 → `[system design]` Session Store / Claim-Version Cutover 설계 → `[deep dive]` AuthZ Decision Logging Design → `[deep dive]` Audit Logging for Auth / AuthZ Traceability
```

## 연결해서 보면 좋은 문서 (cross-category bridge)

겹치던 bridge bullet을 `incident / session / identity` 3축으로 다시 묶었다. 같은 문서를 여러 묶음에 반복하지 않고, 가장 먼저 던지는 질문 기준으로 한 번만 배치했다.
빠른 시작 구간에는 entrypoint만 남기고, 세부 교차 링크는 아래 세 묶음에서만 길게 유지한다.
bridge bullet에서도 역할 cue를 유지한다. `[cross-category bridge]`는 README subsection entrypoint, `[playbook]` / `[drill]` / `[incident matrix]` / `[recovery]`는 incident 대응 문서, `[deep dive]`는 개념·경계 본문, `[system design]`는 control-plane / cutover 설계 handoff를 뜻한다.
같은 bullet 안에서 security/database `deep dive` -> system-design handoff -> security evidence `deep dive`처럼 역할이 다시 바뀌면 첫 링크 한 번만 표기하지 말고 전환 지점마다 badge를 다시 붙여 handoff boundary를 숨기지 않는다.
이 alias 이름은 [Navigation Taxonomy](../../rag/navigation-taxonomy.md)와 [Retrieval Anchor Keywords](../../rag/retrieval-anchor-keywords.md)에서 쓰는 `cross-category bridge` / `deep dive route` / `system design handoff` vocabulary를 그대로 따른다.
bullet 첫머리에는 `Identity / Delegation / Lifecycle` 같은 개념명만 두지 않고, 학습자가 실제로 말할 symptom 문장을 먼저 노출해 retrieval entry phrase를 바로 읽히게 유지한다.

<a id="security-bridge-incident-recovery-trust"></a>
### Incident / Recovery / Trust

- `JWKS outage`, `kid miss`, `unable to find JWK`, `auth verification outage`, `stale JWKS cache` alias cluster의 security-side entrypoint다.
- JWT/JWKS 장애의 response ladder를 빠르게 훑으려면 `[playbook]` [JWT Signature Verification Failure Playbook](./jwt-signature-verification-failure-playbook.md)에서 시작해 `[drill]` [JWT / JWKS Outage Recovery / Failover Drills](./jwt-jwks-outage-recovery-failover-drills.md), `[incident matrix]` [Auth Incident Triage / Blast-Radius Recovery Matrix](./auth-incident-triage-blast-radius-recovery-matrix.md), `[system design]` [System Design: Service Discovery / Health Routing](../system-design/service-discovery-health-routing-design.md), `[system design]` [System Design: Global Traffic Failover Control Plane](../system-design/global-traffic-failover-control-plane-design.md), `[system design]` [System Design: Session Store Design at Scale](../system-design/session-store-design-at-scale.md)를 순서대로 보면 `unable to find JWK` 같은 verify error string과 route-level 복구, state-level 복구가 분리된다.
- rotation cutover 실패나 signer compromise를 trust convergence 문제로 보려면 `[deep dive]` [JWK Rotation / Cache Invalidation / `kid` Rollover](./jwk-rotation-cache-invalidation-kid-rollover.md), `[recovery]` [JWKS Rotation Cutover Failure / Recovery](./jwks-rotation-cutover-failure-recovery.md), `[playbook]` [Signing Key Compromise Recovery Playbook](./signing-key-compromise-recovery-playbook.md), `[deep dive]` [mTLS Certificate Rotation / Trust Bundle Rollout](./mtls-certificate-rotation-trust-bundle-rollout.md)을 함께 보고, hardware root까지 흔들린 상황은 `[deep dive]` [Hardware-Backed Keys / Attestation](./hardware-backed-keys-attestation.md), `[recovery]` [Hardware Attestation Policy / Failure Recovery](./hardware-attestation-policy-failure-recovery.md)로 이어 가면 된다.
- `break-glass는 종료됐는데 access/session tail이 남는다`, `cleanup_confirmed`를 언제 내려야 할지 모르겠다, `incident close가 active override 때문에 막힌다` 같은 incident symptom이면 `[deep dive]` [AuthZ Kill Switch / Break-Glass Governance](./authz-kill-switch-break-glass-governance.md), [Emergency Grant Cleanup Metrics](./emergency-grant-cleanup-metrics.md), [Delegated Session Tail Cleanup](./delegated-session-tail-cleanup.md), [deep dive] [Incident-Close Break-Glass Gate](./incident-close-break-glass-gate.md), [deep dive] [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md), [AuthZ Decision Logging Design](./authz-decision-logging-design.md), [deep dive] [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)를 같이 보면 detection, evidence, leftover privilege cleanup 판단 기준이 이어진다.

<a id="security-bridge-session-boundary-replay"></a>
### Session / Boundary / Replay

- browser/session symptom routing은 [Browser / Session Troubleshooting Path](#browser--session-troubleshooting-path) 하나로 먼저 모은다. 아래 bullet들은 거기서 갈라진 뒤 원인별 deep dive를 확장하는 용도다.
- `cookie`, `session`, `JWT` 개념은 아는데 Spring 문서에서 `SavedRequest`, `hidden JSESSIONID`, `SecurityContextRepository`, `SessionCreationPolicy`가 갑자기 등장하면 [HTTP의 무상태성과 쿠키, 세션, 캐시](../network/http-state-session-cache.md) -> [Cookie / Session / JWT 브라우저 흐름 입문](../network/cookie-session-jwt-browser-flow-primer.md) -> [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> [Signed Cookies / Server Sessions / JWT Tradeoffs](./signed-cookies-server-sessions-jwt-tradeoffs.md) -> `[deep dive]` [Spring Security 아키텍처](../spring/spring-security-architecture.md) -> `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) -> `[deep dive]` [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md) 순으로 먼저 올라오면 cookie 자동 전송, redirect 응답의 저장/복귀, hidden session 생성, Spring persistence, browser/BFF translation 경계가 한 줄로 이어진다.
- login callback hardening을 redirect 검증부터 post-login session/headers까지 한 번에 보려면 `[deep dive]` [Open Redirect Hardening](./open-redirect-hardening.md), [PKCE Failure Modes / Recovery](./pkce-failure-modes-recovery.md), [Session Fixation in Federated Login](./session-fixation-in-federated-login.md), [Session Fixation, Clickjacking, CSP](./session-fixation-clickjacking-csp.md), [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md), [CSRF in SPA + BFF Architecture](./csrf-in-spa-bff-architecture.md), [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md)를 같이 보면 redirect destination, verifier/state consumption, session regeneration, frame/script policy, browser-visible credential, post-login mutation hardening 축이 한 줄로 이어진다.
- 브라우저에 어떤 credential이 보이는지와 BFF가 그 credential을 어떻게 서버측 세션/token cache로 번역하는지는 `[deep dive]` [Browser Storage Threat Model for Tokens](./browser-storage-threat-model-for-tokens.md), [Browser / BFF Token Boundary / Session Translation](./browser-bff-token-boundary-session-translation.md), `[recovery]` [BFF Session Store Outage / Degradation Recovery](./bff-session-store-outage-degradation-recovery.md), `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md), [Spring Security `LogoutHandler` / `LogoutSuccessHandler` Boundaries](../spring/spring-security-logout-handler-success-boundaries.md), [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md)를 같이 보면 세션 pinning, request 복귀, local logout cleanup, store outage 문맥이 한 번에 정리된다.
- 세션 일관성 자체를 보고 싶으면 `[deep dive]` [AuthZ / Session Versioning Patterns](./authz-session-versioning-patterns.md), [Session Revocation at Scale](./session-revocation-at-scale.md), [Revocation Propagation Lag / Debugging](./revocation-propagation-lag-debugging.md), [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md), [OIDC Back-Channel Logout / Session Coherence](./oidc-backchannel-logout-session-coherence.md), [MFA / Step-Up Auth Design](./mfa-step-up-auth-design.md), [Step-Up Session Coherence / Auth Assurance](./step-up-session-coherence-auth-assurance.md)를 먼저 묶으면 된다.
- device/session graph와 operator action surface를 같이 보려면 `[deep dive]` [deep dive] [Refresh Token Family Invalidation at Scale](./refresh-token-family-invalidation-at-scale.md), [Device Binding Caveats](./device-binding-caveats.md), [Device / Session Graph Revocation Design](./device-session-graph-revocation-design.md), [Session Inventory UX / Revocation Scope Design](./session-inventory-ux-revocation-scope-design.md), [Revocation Impact Preview Data Contract](./revocation-impact-preview-data-contract.md), [deep dive] [Revocation Preview Drift Response Contract](./revocation-preview-drift-response-contract.md), [Revocation Propagation Status Contract](./revocation-propagation-status-contract.md), [Delegated Session Tail Cleanup](./delegated-session-tail-cleanup.md), [Operator Tooling State Semantics / Safety Rails](./operator-tooling-state-semantics-safety-rails.md)를 한 번에 보면 revoke scope, preview payload, confirm-time drift contract, propagation status contract, delegated tail cleanup 기준, support tooling semantics가 이어진다.
- sender-constrained token과 replay store failure를 같은 boundary 문제로 보려면 `[deep dive]` [deep dive] [API Key, HMAC Signed Request, Replay Protection](./api-key-hmac-signature-replay-protection.md), [DPoP / Token Binding Basics](./dpop-token-binding-basics.md), [Proof-of-Possession vs Bearer Token Trade-offs](./proof-of-possession-vs-bearer-token-tradeoffs.md), [OAuth Client Authentication: `client_secret_basic`, `private_key_jwt`, mTLS](./oauth-client-authentication-private-key-jwt-mtls.md), [mTLS Client Auth vs Certificate-Bound Access Token](./mtls-client-auth-vs-certificate-bound-access-token.md), `[recovery]` [Replay Store Outage / Degradation Recovery](./replay-store-outage-degradation-recovery.md)를 같이 보면 partial rollout과 fallback regression까지 이어진다.
- replay/dedup과 one-time token race를 애플리케이션 boundary 바깥 저장소 문제로 확장하려면 `[deep dive]` [Database: 멱등성 키와 중복 방지](../database/idempotency-key-and-deduplication.md), `[system design]` [System Design: Idempotency Key Store / Dedup Window / Replay-Safe Retry](../system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md), `[system design]` [System Design: Replay / Repair Orchestration Control Plane](../system-design/replay-repair-orchestration-control-plane-design.md), `[deep dive]` [deep dive] [Email Magic-Link Threat Model](./email-magic-link-threat-model.md), `[deep dive]` [Password Reset Threat Modeling](./password-reset-threat-modeling.md), `[deep dive]` [One-Time Token Consumption Race / Burn-After-Read](./one-time-token-consumption-race-burn-after-read.md)를 묶어 보면 된다.

<a id="security-bridge-identity-delegation-lifecycle"></a>
### Identity / Delegation / Lifecycle

- `SCIM disable했는데 still access`, `deprovision은 끝났는데 session/authz tail이 남는다`, `backfill is green but access tail remains`, `decision parity`, `auth shadow divergence` alias cluster를 security README에서 바로 붙일 때 쓰는 bridge다.
- 같은 authority-transfer route를 database README는 `Identity / Authority Transfer 브리지` / `Authority Transfer / Security Bridge`, system-design README는 `Database / Security Authority Bridge` -> `Verification / Shadowing / Authority Bridge`로 부른다. route-name이 달라도 같은 handoff 묶음이라는 점을 여기서 먼저 고정한다.
- 서비스 간 caller identity와 end-user context propagation을 같이 보려면 `[deep dive]` [Service-to-Service Auth: mTLS, JWT, SPIFFE](./service-to-service-auth-mtls-jwt-spiffe.md), [Token Exchange / Impersonation Risks](./token-exchange-impersonation-risks.md), [Workload Identity / User Context Propagation Boundaries](./workload-identity-user-context-propagation-boundaries.md), [Trust Boundary Bypass / Detection Signals](./trust-boundary-bypass-detection-signals.md)를 같이 보면 trust propagation과 bypass signal이 한 묶음으로 보인다.
- `support AOBO나 break-glass는 끝났는데 customer timeline이 안 닫히고 delegated session tail이 남는다`, `preview_id`/`access_group_id`/`revocation_request_id`를 어떤 event spine으로 묶어야 할지 막힌다면 delegated admin/support operator 축을 `[deep dive]` [deep dive] [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md), [deep dive] [Support Operator / Acting-on-Behalf-Of Controls](./support-operator-acting-on-behalf-of-controls.md), [deep dive] [Canonical Security Timeline Event Schema](./canonical-security-timeline-event-schema.md), [AOBO Start / End Event Contract](./aobo-start-end-event-contract.md), [deep dive] [Customer-Facing Support Access Notifications](./customer-facing-support-access-notifications.md), [deep dive] [Audience Matrix for Support Access Events](./audience-matrix-for-support-access-events.md), [Tenant Policy Schema for Privileged Support Alerts](./tenant-policy-schema-for-privileged-support-alerts.md), [deep dive] [Delivery Surface Policy for Support Access Alerts](./delivery-surface-policy-for-support-access-alerts.md), [AuthZ Kill Switch / Break-Glass Governance](./authz-kill-switch-break-glass-governance.md), [Emergency Grant Cleanup Metrics](./emergency-grant-cleanup-metrics.md), [Delegated Session Tail Cleanup](./delegated-session-tail-cleanup.md), [deep dive] [Incident-Close Break-Glass Gate](./incident-close-break-glass-gate.md) 순으로 먼저 보고, preview/confirm/status/timeline을 잇는 `preview_id`/`access_group_id`/`revocation_request_id` correlation spine은 `[deep dive]` [AOBO Revocation Audit Event Schema](./aobo-revocation-audit-event-schema.md)에서 확인한 뒤 세션 그래프 영향 범위는 바로 위 `Session / Boundary / Replay`의 device/revocation 묶음으로 내려가면 된다.
- authz runtime inconsistency를 정책/캐시 문제로 보려면 `[deep dive]` [AuthZ / Session Versioning Patterns](./authz-session-versioning-patterns.md), [Rate Limiting vs Brute Force Defense](./rate-limiting-vs-brute-force-defense.md), [Abuse Throttling / Runtime Signals](./abuse-throttling-runtime-signals.md), [deep dive] [Authorization Caching / Staleness](./authorization-caching-staleness.md), [AuthZ Cache Inconsistency / Runtime Debugging](./authz-cache-inconsistency-runtime-debugging.md), [deep dive] [AuthZ Negative Cache Failure Case Study](./authz-negative-cache-failure-case-study.md), [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md), [PDP / PEP Boundaries Design](./pdp-pep-boundaries-design.md), [Beginner Guide to Auth Failure Responses: `401` / `403` / `404`](./auth-failure-response-401-403-404.md)를 같이 보면 stale deny, tenant-specific `403`, `401`/`404` flip, runtime guardrail이 한 축으로 이어진다.
- `authorization graph cache`, `graph snapshot`, `relationship cache`, `relationship-based authz인데 delegated scope revoke 뒤 tenant별로 allow/deny가 갈린다`, `tenant ownership move 뒤 graph invalidation이 어디서 끊겼는지 모르겠다` 같은 symptom이면 `[deep dive]` [deep dive] [Permission Model Drift / AuthZ Graph Design](./permission-model-drift-authz-graph-design.md), [deep dive] [Delegated Admin / Tenant RBAC](./delegated-admin-tenant-rbac.md), [PDP / PEP Boundaries Design](./pdp-pep-boundaries-design.md), [deep dive] [Authorization Caching / Staleness](./authorization-caching-staleness.md), [deep dive] [Authorization Graph Caching](./authorization-graph-caching.md), [deep dive] [Authorization Runtime Signals / Shadow Evaluation](./authorization-runtime-signals-shadow-evaluation.md), [Tenant Isolation / AuthZ Testing](./tenant-isolation-authz-testing.md)를 같이 보면 graph source of truth, scope edge, decision/enforcement split, tenant-scoped invalidation, shadow diff, negative regression test가 한 줄로 이어진다.
- `SCIM disable했는데 로그인/권한이 그대로 남는다`, `deprovision은 끝났는데 tenant access tail이 남는다`, `backfill is green but access tail remains` 같은 lifecycle symptom이면 먼저 `[cross-category bridge]` [Database: Identity / Authority Transfer 브리지](../database/README.md#database-bridge-identity-authority), `[system design]` [System Design: Database / Security Authority Bridge](../system-design/README.md#system-design-database-security-authority-bridge), `[system design]` [System Design: Verification / Shadowing / Authority Bridge](../system-design/README.md#system-design-verification-shadowing-authority-bridge)로 route를 맞춘 다음, `[deep dive]` [SCIM Provisioning Security](./scim-provisioning-security.md), `[deep dive]` [SCIM Drift / Reconciliation](./scim-drift-reconciliation.md), `[deep dive]` [SCIM Deprovisioning / Session / AuthZ Consistency](./scim-deprovisioning-session-authz-consistency.md), `[deep dive]` [Database: Online Backfill Verification, Drift Checks, and Cutover Gates](../database/online-backfill-verification-cutover-gates.md), `[system design]` [System Design: Database / Security Identity Bridge Cutover 설계](../system-design/database-security-identity-bridge-cutover-design.md), `[system design]` [System Design: Session Store / Claim-Version Cutover 설계](../system-design/session-store-claim-version-cutover-design.md), `[deep dive]` [AuthZ Decision Logging Design](./authz-decision-logging-design.md), `[deep dive]` [deep dive] [Audit Logging for Auth / AuthZ Traceability](./audit-logging-auth-authz-traceability.md)를 같이 보면 `decision parity`, `auth shadow divergence`, cleanup/retirement evidence를 한 번에 분리해서 볼 수 있다.
