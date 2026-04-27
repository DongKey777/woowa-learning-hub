# System Design

> 한 줄 요약: system design 카테고리의 primer, bridge, deep dive를 읽기 순서 중심으로 묶어 주는 탐색용 인덱스다.

**난이도: 🔴 Advanced**

관련 문서:

- [System Design Foundations](./system-design-foundations.md)
- [Consistency, Idempotency, and Async Workflow Foundations](./consistency-idempotency-async-workflow-foundations.md)
- [Cross-Primer Glossary Anchors](./cross-primer-glossary-anchors.md)
- [database 카테고리 인덱스](../database/README.md)

retrieval-anchor-keywords: system design catalog, system design reading route, beginner consistency route, notification watermark route, system design bridge index, 처음 배우는데 system design 뭐부터 읽어요, basics route, 알림 숫자 해석 뭐예요, consistency route primer

> retrieval-anchor-keywords: system design catalog, system design interview, system design foundations, stateless backend cache database queue starter pack, stateless backend architecture primer, backend box mental model, request path failure modes, request deadline and timeout budget primer, timeout budget primer, client timeout budget, app timeout budget, cache timeout fallback, db timeout budget, partial failure retry storm, deadline ladder, cache outage primer, queue outage primer, app instance failure primer, database outage primer, failure absorption order, read-only mode, graceful degradation patterns, stale-if-error, partial feature disablement, brownout pattern, database incident read-only, cache incident stale read, stateless sessions primer, sticky session, external session store, token-based auth, load balancer drain and affinity primer, load balancer health check basics, connection draining, deregistration delay, sticky affinity deploy tail, sticky affinity failover, session revocation basics, logout basics, logout propagation basics, oidc back-channel logout handoff, oidc logout primer bridge, short-lived access token basics, token lifecycle state, database scaling primer, caching vs read replica, cache vs replica, cache invalidation basics, stale read basics, read-after-write consistency basics, read-after-write routing primer, monotonic reads and session guarantees primer, monotonic writes ordering primer, per-session write ordering primer, session write sequence primer, session guarantees primer, session guarantees decision matrix, session policy implementation sketches, gateway app database hint propagation, session hint envelope, recent-write min-version write-sequence propagation, list detail monotonicity bridge, list detail search min-version floor, value regression across pages, session guarantee policy bundle, writes-follow-reads beginner, monotonic writes beginner, idempotency key vs sequence number, simple queue fence ordering, product flow consistency matrix, beginner consistency self-check worksheet, estimation invalidation monotonic guard dashboard check, causal consistency primer, notification causal token walkthrough, notification click watermark check, cache acceptance rules for causal reads, causal read cache hit check, causal token cache hit miss refill, required watermark cache acceptance, causal cache refill guard, notification badge vs source freshness, unread badge count read model, badge count stale independently, notification count projection lag, badge count vs causal consistency, read-after-write vs monotonic reads, mixed cache replica read path, mixed cache+replica read path pitfalls, mixed cache replica freshness bridge, cache hit miss refill consistency, rejected hit observability primer, rejected cache hit logging, cache hit reject reason, replica fallback reason, refill no-fill reason, recent write min version causal token, dual stale source, cache miss stale replica, stale refill from replica, source selection rules, freshness routing observability, read your writes basics, primary replica basics, primary fallback, session stickiness, session pinning primer, monotonic reads primer, strong read consistency, read write split, indexing basics, partitioning vs sharding, shard key selection basics, partition key basics, hot partition detection, tenant key sharding pitfall, user key sharding pitfall, load balancer basics, horizontal scaling intuition, stateless app, cache database queue basics, learning tracks, migration cutover, replay repair, control plane, stateful platform, consistency, reliability, observability, dual read verification, cdc outbox, auth failover, session store, security bridge, security + system design route, spring + security route, database security bridge, identity / delegation / lifecycle route, identity / authority transfer bridge, authority transfer / security bridge, database / security authority bridge, verification / shadowing / authority bridge, authority route parity, round-trip handoff parity, security-side role badge parity, beginner handoff ladder, bridge sequence parity, incident ladder parity, catalog to system design handoff, auth session handoff ladder, database + system design route, database + security + system design route, design pattern / read model + database + system design route, identity capability rollout, auth shadow evaluation, backfill verification, analytics correction, dashboard restatement ux, alert reevaluation after backfill, projection freshness slo, read model cutover guardrail, session revocation, claim version cutover, session store migration, revocation cleanup timing, revocation bus regional lag, revoke redrive, cache invalidation replay, canonical revocation plane, token generation coexistence, generation-aware revoke fan-out, alias projection backlog, family quarantine release gate, tenant split out, dedicated cell migration, dedicated cell promotion verification ladder, mirrored traffic dual read auth drift, workload identity allowlist, SPIFFE allowlist, SPIFFE trust bundle overlap, SPIRE bundle propagation, trust bundle rollback, mesh trust root rotation, auth drift soak, verification cluster, traffic shadowing bridge, decision parity, shadow evaluation path, shadow exit signal, parity exit signal, verification evidence chain, jwks overlap reading order, verifier overlap, verifier overlap end threshold, legacy parser hard reject threshold, parser dark observe, unexpected legacy claim, workload identity rollout, hard reject timing, capability sunset gate matrix, capability overlap soak cleanup, dark deny probe, sunset silence window, bridge sunset ladder, verifier overlap hard reject retirement gates, bounded fallback retirement, overlap drained cutoff, scoped reject canary, emergency re-enable handle, cleanup handoff before code deletion, spring security session boundary, request cache login loop, 302 login loop, savedrequest loop vs cookie not sent, savedrequest loop vs server mapping missing, cookie-not-sent login loop, server-mapping-missing login loop, browser bff session troubleshooting, browser session troubleshooting path, logout tail, revocation tail, refresh family rotation cutover, refresh exchange idempotency, refresh exchange lease, duplicate response replay, same-context duplicate, cross-context duplicate, refresh reauth escalation matrix, silent refresh migration, refresh step-up, full reauthentication during migration, forced refresh reissue, mixed-version auth rollout, replay containment during migration, edge verifier claim skew fallback, unknown claim handling, origin introspection fallback, fallback storm, overlap window latency budget, tenant move background path hygiene, tenant caller class rollout matrix, foreground background caller checklist, principal issuance checklist, caller class allowlist checklist, caller class drift soak, stale route cache drain, legacy principal drain, replay worker route cache, support tooling route hygiene, search indexer cutover hygiene, webhook sender principal rollover, dedicated cell drain, shared cell retirement, rollback closure after tenant split out, bridge cluster toc, security incident bundle toc, auth session bridge toc, authority bridge toc, verification shadowing auth bridge toc, decommission retirement cluster, bridge sunset quick navigation, irreversible cleanup path, compatibility bridge sunset, retirement rollback closure, destructive cleanup gate, donor drain retirement bundle, hardware trust recovery bundle, replay session defense bundle, service delegation boundary bundle, hardware attestation recovery, trust bundle recovery, replay store down, nonce store down, acting on behalf of, delegated admin, support access notification, break glass, cleanup evidence, retirement evidence, scim reconciliation close, decision log join key, audit hold evidence, bridge retirement evidence packet, database repair signals, security tail signals, retirement approval packet, repair before cleanup, session auth gate path, verification ladder, read parity gate, revoke propagation parity, auth shadow exit criteria, system design drill label, system design incident matrix label, system design recovery label, mixed incident catalog, mixed incident bridge, inline badge normalization, SavedRequest cookie-missing server-anonymous, savedrequest cookie missing server anonymous beginner split, server anonymous after cookie
> retrieval-anchor-keywords: incident / recovery / trust route, incident bridge role order, playbook drill incident matrix system design recovery ladder, session / boundary / replay route, browser / session troubleshooting route, auth session troubleshooting bridge parity, catalog primer primer bridge deep dive recovery system design ladder, identity / delegation / lifecycle route, authority bridge role order, cross-category bridge to system design handoff, verification shadowing authority evidence ladder, security readme badge parity, beginner bridge role map, consistency idempotency async workflow foundations, cache basics beginner, message queue basics beginner, beginner first session route
> retrieval-anchor-keywords: SavedRequest cookie-missing server-anonymous beginner ladder, savedrequest cookie-missing server-anonymous safe next step, 기억 전송 복원 사다리, login loop 기억 전송 복원 사다리, browser session memory transport restore ladder, login loop memory transport restore, redirect memory cookie transport session restore, cookie-missing beginner route, server-anonymous beginner route, hidden session mismatch beginner split, auth session minimum evidence checklist, auth session mini checklist, DevTools 1개 로그 1개, 분기별 최소 증거, beginner troubleshooting evidence, session troubleshooting evidence ladder
> retrieval-anchor-keywords: authority transfer beginner route, beginner authority transfer route, authority transfer first-step primer, identity lifecycle primer route, decision parity beginner route, auth shadow divergence beginner route, SCIM deprovision, SCIM disable but still access, deprovision tail, access tail beginner route, verification shadowing authority route, authority cleanup evidence ladder
> retrieval-anchor-keywords: beginner consistency quick start, glossary to mixed freshness route, glossary mixed freshness rejected hit dashboard, mixed freshness observability dashboard order, search hit overlay pattern, stale search hit overlay, search result hydration pattern, top k hydrate overlay, search result older than detail, search ranking keep but fields refresh

<details>
<summary>Table of Contents</summary>

- [빠른 탐색](#빠른-탐색)
- [초심자 1회차 라우트](#초심자-1회차-라우트)
- [Security / System-Design Incident Bridge](#system-design-security-incident-bridge)
- [Auth Session Troubleshooting Bridge](#system-design-auth-session-troubleshooting-bridge)
- [Database / Security Authority Bridge](#system-design-database-security-authority-bridge)
- [Capability Rollout Deepening](#system-design-capability-rollout-deepening)
- [Verification / Shadowing / Authority Bridge](#system-design-verification-shadowing-authority-bridge)
- [Decommission / Retirement Cluster](#system-design-decommission-retirement-cluster)
- [카테고리 목차](#카테고리-목차)
- [학습 순서 추천](#학습-순서-추천)
- [심화 트랙 추천](#심화-트랙-추천)
- [한 줄 정리](#한-줄-정리)

</details>

## 빠른 탐색

이 `README`는 system design primer와 advanced catalog를 함께 묶는 **navigator 문서**다.
mixed bridge/catalog에서는 `[catalog]`는 README subsection entrypoint, `[playbook]` / `[drill]` / `[incident matrix]` / `[recovery]`는 incident-oriented 문서, `[system design]`는 control-plane / cutover handoff를 뜻한다. pure system-design catalog에서만 bare link를 남기고, security README와 왕복하는 bridge sequence는 역할 cue를 다시 붙인다.
beginner troubleshooting route는 `[catalog] -> [primer] -> [primer bridge] -> [deep dive] -> [recovery] / [system design]` 사다리를 먼저 지켜서 security README와 round-trip handoff parity를 맞춘다.

| 헷갈리는 역할 | 이 README에서 뜻하는 것 | 초보자용 첫 진입점 |
|---|---|---|
| `survey` | 넓게 훑으며 다음 문서를 고르는 route overview | 아래 `survey / primer부터 읽고 싶다면` 묶음 |
| `primer` | system-design 용어와 mental model을 먼저 여는 문서 | [System Design Foundations](./system-design-foundations.md), [Stateless Sessions Primer](./stateless-sessions-primer.md) |
| `deep dive` | primer bridge 다음에 security/database/spring 쪽 원인과 경계를 실제로 파는 단계 | bridge section 안의 `[deep dive]` 링크들 |
| `playbook` / `drill` / `incident matrix` | live response, rehearsal, blast-radius triage를 먼저 보는 incident ladder | [Security / System-Design Incident Bridge](#system-design-security-incident-bridge) |
| `recovery` | outage/degradation tail을 다루는 incident-oriented recovery deep dive | [Security / System-Design Incident Bridge](#system-design-security-incident-bridge), [Auth Session Troubleshooting Bridge](#system-design-auth-session-troubleshooting-bridge) |

## 초심자 1회차 라우트

처음 30~60분은 용어를 다 외우기보다 "박스 역할 -> cache/queue 경계 -> consistency 경계" 순서로 보는 편이 빠르다.

| 단계 | 먼저 읽을 문서 | 한 줄 목표 |
|---|---|---|
| 1 | [System Design Foundations](./system-design-foundations.md) | 박스가 왜 나뉘는지 큰 그림을 잡는다 |
| 2 | [Stateless 백엔드, 캐시, 데이터베이스, 큐 스타터 팩](./stateless-backend-cache-database-queue-starter-pack.md) | app/cache/db/queue 역할을 요청 흐름으로 묶는다 |
| 3 | [캐시 기초](./caching-basics.md) + [메시지 큐 기초](./message-queue-basics.md) | "반복 읽기 최적화"와 "후처리 분리"를 분리해서 이해한다 |
| 4 | [Consistency, Idempotency, and Async Workflow Foundations](./consistency-idempotency-async-workflow-foundations.md) | sync/async 경계와 duplicate 흡수 원리를 고정한다 |

## Primer Route

survey / primer부터 읽고 싶다면:
  - [System Design Foundations](./system-design-foundations.md)
  - [Stateless 백엔드, 캐시, 데이터베이스, 큐 스타터 팩](./stateless-backend-cache-database-queue-starter-pack.md)
  - [캐시 기초](./caching-basics.md)
  - [메시지 큐 기초](./message-queue-basics.md)
  - [Consistency, Idempotency, and Async Workflow Foundations](./consistency-idempotency-async-workflow-foundations.md)
  - [Request Path Failure Modes Primer](./request-path-failure-modes-primer.md)
  - [Request Deadline and Timeout Budget Primer](./request-deadline-timeout-budget-primer.md)
  - [Retry Amplification and Backpressure Primer](./retry-amplification-and-backpressure-primer.md)
  - [Read-Only and Graceful Degradation Patterns](./read-only-and-graceful-degradation-patterns.md)
  - [Stateless Sessions Primer](./stateless-sessions-primer.md)
  - [Load Balancer Drain and Affinity Primer](./load-balancer-drain-and-affinity-primer.md)
  - [Browser BFF Session Boundary Primer](./browser-bff-session-boundary-primer.md)
  - [Session Revocation Basics](./session-revocation-basics.md)
## Consistency Primer Route

  - [Database Scaling Primer](./database-scaling-primer.md)
  - [Shard Key Selection Basics](./shard-key-selection-basics.md)
  - [Caching vs Read Replica Primer](./caching-vs-read-replica-primer.md)
  - [Cache Invalidation Patterns Primer](./cache-invalidation-patterns-primer.md)
  - [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md)
  - [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
  - [Monotonic Reads and Session Guarantees Primer](./monotonic-reads-and-session-guarantees-primer.md)
  - [Writes-Follow-Reads Primer](./writes-follow-reads-primer.md)
  - [Monotonic Writes Ordering Primer](./monotonic-writes-ordering-primer.md)
  - [Session Guarantees Decision Matrix](./session-guarantees-decision-matrix.md)
  - [Session Policy Implementation Sketches](./session-policy-implementation-sketches.md)
  - [List-Detail Monotonicity Bridge](./list-detail-monotonicity-bridge.md)
  - [Search Hit Overlay Pattern](./search-hit-overlay-pattern.md)
## Notification Consistency Route

  - [Causal Consistency Notification Primer](./causal-consistency-notification-primer.md)
  - [Notification Causal Token Walkthrough](./notification-causal-token-walkthrough.md)
  - [Cache Acceptance Rules for Causal Reads](./cache-acceptance-rules-for-causal-reads.md)
  - [Outbox Watermark Token Primer](./outbox-watermark-token-primer.md)
  - [Notification Badge vs Source Freshness Primer](./notification-badge-vs-source-freshness-primer.md)
  - [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
  - [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)
## Interview Primer Route

  - [시스템 설계 면접 프레임워크](./system-design-framework.md)
  - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
## Consistency Vocabulary Route

consistency guarantee 용어를 먼저 구분하고 싶다면:
  - [Cross-Primer Glossary Anchors](./cross-primer-glossary-anchors.md)
  - 첫 회독 분리표: Cross-Primer 상단의 `먼저 세 용어를 갈라 읽기` 3행 표는 `read-after-write`(보장) / `recent-write`(write 직후 힌트) / `min-version floor`(역행 방지)를 한 번에 나눈다.
  - 검색 앵커 보강: Cross-Primer의 `오답 문장 앵커`는 `cache hit이면 통과`, `cache hit이면 최신이다`, `cache miss면 fresh다` 같은 틀린 문장을 문장째로 받아서 바로잡는다.
  - 직접 점프: [recent-write](./cross-primer-glossary-anchors.md#term-recent-write) / [min-version floor](./cross-primer-glossary-anchors.md#term-min-version-floor) / [stale window](./cross-primer-glossary-anchors.md#term-stale-window) / [headroom](./cross-primer-glossary-anchors.md#term-headroom)
  - 초보자 혼동 방지: Cross-Primer의 `Confusion Guardrail Box`에서 `방금 저장했는데 안 보임` vs `아까 본 값보다 뒤로 감`을 증상 기준 2행 표로 먼저 가른다.
  - 빠른 triage 치트카드: `recent_write_until` / `min_version` / `stale_rate` / `headroom_ratio` 1:1 매핑 표와 바로 붙여 보는 로그/메트릭 쿼리 4개는 Cross-Primer의 `용어 -> 신호 치트 카드 (triage용)` 아래 `바로 조회하는 로그/메트릭 쿼리 예시` 섹션부터 읽는다.
  - 첫 회독 확인: Cross-Primer 끝의 `빠른 혼동 점검 퀴즈` 5문항은 각 정답 아래에 한 줄 설명이 붙어 있어, 초보자도 deeper doc 없이 바로 셀프 교정할 수 있다.
## Session Guarantee Route

  - [Consistency, Idempotency, and Async Workflow Foundations](./consistency-idempotency-async-workflow-foundations.md)
  - [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md)
  - [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
  - 빠른 비교: [Read-After-Write Routing Primer](./read-after-write-routing-primer.md) 상단 `10초 구분표`는 `read-after-write` 목표, `recent-write` 힌트, `min-version floor` 역행 방지를 같은 주문 예시로 한 번에 묶는다.
  - [Monotonic Reads and Session Guarantees Primer](./monotonic-reads-and-session-guarantees-primer.md)
  - [Writes-Follow-Reads Primer](./writes-follow-reads-primer.md)
  - [Monotonic Writes Ordering Primer](./monotonic-writes-ordering-primer.md)
  - [Session Guarantees Decision Matrix](./session-guarantees-decision-matrix.md)
  - [Session Policy Implementation Sketches](./session-policy-implementation-sketches.md)
  - [List-Detail Monotonicity Bridge](./list-detail-monotonicity-bridge.md)
  - [Search Hit Overlay Pattern](./search-hit-overlay-pattern.md)
## Notification Vocabulary Route

  - [Causal Consistency Notification Primer](./causal-consistency-notification-primer.md)
  - [Notification Causal Token Walkthrough](./notification-causal-token-walkthrough.md)
  - [Cache Acceptance Rules for Causal Reads](./cache-acceptance-rules-for-causal-reads.md)
  - [Notification Badge vs Source Freshness Primer](./notification-badge-vs-source-freshness-primer.md)
  - 빠른 숫자 연결: Notification Badge primer에도 [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md) / [Read-After-Write Routing Primer](./read-after-write-routing-primer.md) / [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)의 공통 stale/headroom 카드 링크를 붙여 두어 `badge stale`과 `click fallback 여유`를 같은 숫자 언어로 이어 읽을 수 있다.
  - [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
  - [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)
## Consistency Check Route

초심자 consistency 품질 점검 루틴(멘탈모델 -> 무효화 -> 화면 일관성 -> 운영 대시보드):
  - [Beginner Consistency Self-Check Worksheet](./beginner-consistency-self-check-worksheet.md)
  - 빠른 포인트: 문서 상단에 `방금 저장한 값이 안 보인다 / 목록이 상세보다 예전 값이다 / 알림을 눌렀는데 원인 데이터가 안 보인다 / 고친 뒤 숫자로 확인하고 싶다` 증상별 시작 링크를 고정했고, 이어서 `숫자 -> 선택 -> 가드 -> 확인` 작성 순서 4칸 카드 + 주문 결제 플로우 샘플 정답 1세트 + `주문 결제 ↔ 알림 읽음 ↔ 프로필 저장(display_name)` Flow 변형 미니 비교표 + `프로필 / 설정 / 헤더` 3칸 projection 체크리스트 + `알림 읽음` 5분 채점 예시 + `read-after-write / monotonic / causal` 첫 회독 3행 용어 대응표 + `미흡 / 충분 / 우수` 3단계 미니 루브릭 포함.
  - [Cross-Primer Glossary Anchors](./cross-primer-glossary-anchors.md)
  - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
  - [Cache Invalidation Patterns Primer](./cache-invalidation-patterns-primer.md)
  - [List-Detail Monotonicity Bridge](./list-detail-monotonicity-bridge.md)
  - [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md)
## Dashboard Number Route

  - 빠른 첫 판정: [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md)에 `stale rate / source distribution / fallback headroom` 정상·주의·drilldown 시작 범위를 한 표로 붙여 두었다.
  - headroom 계산 완충 카드: [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md)에 `remaining_safe_qps / fallback_qps`를 `240 / 60 = 4.0x = Green`으로 다시 푼 `headroom 계산 미니 카드`를 추가해 첫 회독에서 분자/분모를 덜 헷갈리게 했다.
  - Yellow 중간 카드: [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md)에 `stale 5.8% / headroom 2.0x / replica 25% / primary 18%` shared 예시를 넣어, routing fix는 계속하되 fallback 확대를 더 가까이 모니터링해야 하는 구간을 Green과 Red 사이에 끼워 읽게 했다.
## Dashboard Examples Route

  - 설정 저장 미니 카드: [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md)에 `display_name stale rate 3.2% vs baseline 0.4%`와 `fallback headroom 3.6x`를 한 카드로 붙여, 운영 확인 단계 첫 읽기에서 "capacity보다 routing 누락 먼저"를 바로 읽게 했다.
  - 화면 역행 연결 카드: [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md)에 `상세에서 PAID 확인 -> 목록에서 다시 PENDING` 예시와 `stale 3.9% / replica 35% / headroom 3.4x`를 붙여, 운영 패널 마지막 단계에서 "DB 전체 문제"보다 `recent-write 전달 누락`과 `min-version floor`를 먼저 떠올리게 했다.
  - source mix 미니 사례: [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md)에 `replica 비중 증가`, `primary 비중 증가`, `cache 급락과 동반된 동시 상승`을 초보자 첫 행동과 바로 연결한 3개 짧은 사례를 추가했다.
  - 공통 숫자 카드: stale/headroom를 같은 값으로 비교하려면 [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md) -> [Read-After-Write Routing Primer](./read-after-write-routing-primer.md) -> [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md) 순서로 `공통 미니 예시 카드`, `headroom 2.0x (Yellow) 중간 카드`, `headroom 1.4x (Red) 반례 카드`를 붙여 읽는다.
## Beginner Quality Route

  - 용어 검색 보강: [Cross-Primer Glossary Anchors](./cross-primer-glossary-anchors.md)와 [List-Detail Monotonicity Bridge](./list-detail-monotonicity-bridge.md) 본문에서 `min-version floor = monotonic guard = 역행 방지 하한선` 별칭을 같이 잡아 두었다.
  - 혼동 방지 한 줄: [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md)는 "내가 방금 쓴 값이 바로 보이게" 하는 보장이고, monotonic guard는 [List-Detail Monotonicity Bridge](./list-detail-monotonicity-bridge.md)처럼 "한번 본 값보다 뒤로 후퇴하지 않게" 막는 하한선이다.
  - 가장 짧은 beginner route: [Cross-Primer Glossary Anchors](./cross-primer-glossary-anchors.md) → [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md) → [Trace Attribute Freshness / Read-Source Bridge](./trace-attribute-freshness-read-source-bridge.md) → [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md) → [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md)
  - glossary 퀴즈에서 2개 이상 헷갈렸다면: [Cross-Primer Glossary Anchors](./cross-primer-glossary-anchors.md) → [Beginner Consistency Self-Check Worksheet](./beginner-consistency-self-check-worksheet.md) 순서가 가장 짧다.
## Beginner Usage Route

  - 읽는 기준: 용어를 먼저 고정하고, 그 용어가 hit/miss/refill 전체에 어떻게 이어지는지 본 뒤, `rejected_hit_reason` / `fallback_reason` / `no_fill_reason`를 익히고, 마지막에 `stale rate` / `source mix` / `fallback headroom`을 한 화면에서 같이 본다.
  - 증상 -> 추천 primer 빠른 매핑: `방금 쓴 값 미반영`이면 [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md), `화면 역행`이면 [Monotonic Reads and Session Guarantees Primer](./monotonic-reads-and-session-guarantees-primer.md)부터 읽고, list/detail 이동에서 특히 뒤로 가면 [List-Detail Monotonicity Bridge](./list-detail-monotonicity-bridge.md)로 이어간다.
  - 빠른 사용법: `워크시트 1회 작성 -> 숫자 병목 후보 -> 무효화 선택 -> 화면 역행 방지 -> 운영 패널` 순서로 읽고, 각 문서의 `흔한 혼동`과 `다음으로 이어 읽기` 표로 다음 문서를 고른다.
  - 보강 포인트: 첫 회독에서는 각 문서의 `첫 회독 5분 루트`, `증상 기반 첫 대응 매트릭스`, `floor 미달 후보 처리`, `오답 예시 2개`, `초보자 시작 템플릿` 섹션부터 먼저 훑으면 용어 암기 없이도 대응 순서를 잡기 쉽다.
## Beginner Entrypoints

🟢 Beginner 입문 문서 (새로 추가):
  - [Stateless 백엔드, 캐시, 데이터베이스, 큐 스타터 팩](./stateless-backend-cache-database-queue-starter-pack.md)
  - [Consistency, Idempotency, and Async Workflow Foundations](./consistency-idempotency-async-workflow-foundations.md)
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
## Case Study Entrypoints

대표 사례형 설계부터 읽고 싶다면:
  - [URL 단축기 설계](./url-shortener-design.md)
  - [Rate Limiter 설계](./rate-limiter-design.md)
  - [분산 캐시 설계](./distributed-cache-design.md)
  - [Payment System / Ledger / Idempotency / Reconciliation](./payment-system-ledger-idempotency-reconciliation-design.md)
## Replay and Cutover Entrypoints

migration / replay / cutover cluster로 바로 들어가려면:
  - [Outbox Watermark Token Primer](./outbox-watermark-token-primer.md)
  - [Change Data Capture / Outbox Relay](./change-data-capture-outbox-relay-design.md)
  - [Historical Backfill / Replay Platform](./historical-backfill-replay-platform-design.md)
  - [Dual-Write Avoidance / Migration Bridge](./dual-write-avoidance-migration-bridge-design.md)
  - [Zero-Downtime Schema Migration Platform](./zero-downtime-schema-migration-platform-design.md)
  - [Traffic Shadowing / Progressive Cutover](./traffic-shadowing-progressive-cutover-design.md)
  - [Dual-Read Comparison / Verification Platform](./dual-read-comparison-verification-platform-design.md)
  - [Tenant Split-Out with Service Identity Rollout](./tenant-split-out-service-identity-rollout-design.md)
  - [Dedicated Cell Drain and Retirement](./dedicated-cell-drain-retirement-design.md)
## Analytics Correction Entrypoints

analytics correction / restatement cluster로 바로 들어가려면:
  - [Historical Backfill / Replay Platform](./historical-backfill-replay-platform-design.md)
  - [Analytics Late Data Reconciliation](./analytics-late-data-reconciliation-design.md)
  - [Dashboard Restatement UX](./dashboard-restatement-ux-design.md)
  - [Alert Re-Evaluation / Correction](./alert-reevaluation-correction-design.md)
## Stale Triage Entrypoints

first-response stale triage를 먼저 익히려면:
  - [Trace Attribute Freshness / Read-Source Bridge](./trace-attribute-freshness-read-source-bridge.md)
  - [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)
  - [First 15-Minute Triage Flow Card](./first-15-minute-triage-flow-card.md)
  - [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md)
## Security + System Design Route

`[cross-category bridge]` [Security + System Design](../../rag/cross-domain-bridge-map.md#security--system-design) route로 바로 들어가려면:
  - `[system design]` [Security / System-Design Incident Bridge](#system-design-security-incident-bridge)
  - `[catalog]` [Security: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path)
  - `[catalog]` [Security: Hardware Trust / Recovery deep dive catalog](../security/README.md#hardware-trust--recovery-deep-dive-catalog)
  - `[catalog]` [Security: Replay / Token Misuse / Session Defense deep dive catalog](../security/README.md#replay--token-misuse--session-defense-deep-dive-catalog)
## Spring + Security Route

`[cross-category bridge]` [Spring + Security](../../rag/cross-domain-bridge-map.md#spring--security) route로 바로 들어가려면:
  - `[system design]` [Auth Session Troubleshooting Bridge](#system-design-auth-session-troubleshooting-bridge)
  - `[catalog]` [Security: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path)
  - `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
  - `[deep dive]` [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md)
## Retirement Route

decommission / retirement / irreversible cleanup cluster로 바로 들어가려면:
  - [Decommission / Retirement Cluster](#system-design-decommission-retirement-cluster)
  - [Verifier Overlap Hard-Reject Retirement Gates](./verifier-overlap-hard-reject-retirement-gates-design.md)
  - [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md)
  - [Capability Sunset Gate Matrix](./capability-sunset-gate-matrix-design.md)
  - [Adapter Retirement / Compatibility Bridge Decommission](./adapter-retirement-compatibility-bridge-decommission-design.md)
  - [Dedicated Cell Drain and Retirement](./dedicated-cell-drain-retirement-design.md)
  - [Cleanup Point-of-No-Return](./cleanup-point-of-no-return-design.md)
## Database + Security + System Design Route

`[cross-category bridge]` [Database + Security + System Design](../../rag/cross-domain-bridge-map.md#database--security--system-design) route로 바로 들어가려면:
  - `[cross-category bridge]` [Database: Identity / Authority Transfer 브리지](../database/README.md#database-bridge-identity-authority)
  - `[cross-category bridge]` [Security: Identity / Delegation / Lifecycle](../security/README.md#identity--delegation--lifecycle)
  - `[system design]` [Database / Security Authority Bridge](#system-design-database-security-authority-bridge)
  - `[system design]` [Verification / Shadowing / Authority Bridge](#system-design-verification-shadowing-authority-bridge)
## Database + System Design Route

[Database + System Design](../../rag/cross-domain-bridge-map.md#database--system-design) route부터 잡고 싶다면:
  - [Database Scaling Primer](./database-scaling-primer.md)
  - [Shard Key Selection Basics](./shard-key-selection-basics.md)
  - [Caching vs Read Replica Primer](./caching-vs-read-replica-primer.md)
  - [Cache Invalidation Patterns Primer](./cache-invalidation-patterns-primer.md)
  - [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md)
  - [Read-After-Write Routing Primer](./read-after-write-routing-primer.md)
  - [Monotonic Reads and Session Guarantees Primer](./monotonic-reads-and-session-guarantees-primer.md)
  - [Writes-Follow-Reads Primer](./writes-follow-reads-primer.md)
  - [Session Guarantees Decision Matrix](./session-guarantees-decision-matrix.md)
  - [List-Detail Monotonicity Bridge](./list-detail-monotonicity-bridge.md)
  - [Search Hit Overlay Pattern](./search-hit-overlay-pattern.md)
## Database + Notification Consistency Route

  - [Causal Consistency Notification Primer](./causal-consistency-notification-primer.md)
  - [Notification Causal Token Walkthrough](./notification-causal-token-walkthrough.md)
  - [Cache Acceptance Rules for Causal Reads](./cache-acceptance-rules-for-causal-reads.md)
  - [Notification Badge vs Source Freshness Primer](./notification-badge-vs-source-freshness-primer.md)
  - [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md)
  - [Trace Attribute Freshness / Read-Source Bridge](./trace-attribute-freshness-read-source-bridge.md)
  - [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)
  - [Mixed Cache+Replica Read Path Pitfalls](./mixed-cache-replica-read-path-pitfalls.md)
## Database + Read Model Expansion Route

  - [Change Data Capture / Outbox Relay](./change-data-capture-outbox-relay-design.md)
  - [Dual-Read Comparison / Verification Platform](./dual-read-comparison-verification-platform-design.md)
  - [Database: Schema Migration, Partitioning, CDC, CQRS](../database/schema-migration-partitioning-cdc-cqrs.md)
## Read Model Cross-Category Route

[Design Pattern / Read Model + Database + System Design](../../rag/cross-domain-bridge-map.md#design-pattern--read-model--database--system-design) route로 확장하려면:
  - [Design Pattern: Read Model Staleness and Read-Your-Writes](../design-pattern/read-model-staleness-read-your-writes.md)
  - [Design Pattern: Read Model Cutover Guardrails](../design-pattern/read-model-cutover-guardrails.md)
  - [Design Pattern: Projection Freshness SLO Pattern](../design-pattern/projection-freshness-slo-pattern.md)
  - [Database: Incremental Summary Table Refresh and Watermark Discipline](../database/incremental-summary-table-refresh-watermark.md)

<a id="system-design-security-incident-bridge"></a>
## Security / System-Design Incident Bridge

보안 incident 대응과 system design 운영 경계를 한 묶음으로 훑을 때 바로 내려오는 subsection이다.
초보자용 mental model은 verify error string과 first response는 `[playbook]` / `[drill]` / `[incident matrix]`에서, route failover와 control plane은 `[system design]`에서, state convergence tail은 `[recovery]`에서 보는 것이다. security README와 왕복해도 같은 badge를 유지한다.

| security-side badge | 여기서 이어지는 질문 | 이 subsection이 유지하는 다음 role |
|---|---|---|
| `[playbook]` / `[drill]` / `[incident matrix]` | 지금 난 장애를 어떤 ladder로 분류하고 첫 대응할까 | verify error, rehearsal, blast-radius triage를 같은 badge로 먼저 둔다 |
| `[system design]` | 어느 control plane이 reroute와 cutover를 맡나 | [Service Discovery / Health Routing](./service-discovery-health-routing-design.md), [Global Traffic Failover Control Plane](./global-traffic-failover-control-plane-design.md) |
| `[recovery]` | route는 돌았는데 revoke/session tail이 아직 안 닫히나 | [Revocation Bus Regional Lag Recovery](./revocation-bus-regional-lag-recovery-design.md) |

  - `[playbook]` [Security: JWT Signature Verification Failure Playbook](../security/jwt-signature-verification-failure-playbook.md)
  - `[drill]` [Security: JWT / JWKS Outage Recovery / Failover Drills](../security/jwt-jwks-outage-recovery-failover-drills.md)
  - `[incident matrix]` [Security: Auth Incident Triage / Blast-Radius Recovery Matrix](../security/auth-incident-triage-blast-radius-recovery-matrix.md)
  - `[catalog]` [Security: Hardware Trust / Recovery deep dive catalog](../security/README.md#hardware-trust--recovery-deep-dive-catalog)
  - `[catalog]` [Security: Replay / Token Misuse / Session Defense deep dive catalog](../security/README.md#replay--token-misuse--session-defense-deep-dive-catalog)
  - `[system design]` [Service Discovery / Health Routing](./service-discovery-health-routing-design.md)
  - `[system design]` [Global Traffic Failover Control Plane](./global-traffic-failover-control-plane-design.md)
  - `[system design]` [Session Store Design at Scale](./session-store-design-at-scale.md)
  - `[system design]` [Session Store / Claim-Version Cutover](./session-store-claim-version-cutover-design.md)
  - `[system design]` [Canonical Revocation Plane Across Token Generations](./canonical-revocation-plane-across-token-generations-design.md)
  - `[recovery]` [Revocation Bus Regional Lag Recovery](./revocation-bus-regional-lag-recovery-design.md)
  - `[system design]` [Edge Verifier Claim-Skew Fallback](./edge-verifier-claim-skew-fallback-design.md)
  - `[system design]` [Refresh-Family Rotation Cutover](./refresh-family-rotation-cutover-design.md)
  - `[system design]` [Refresh Exchange Idempotency Under Cutover](./refresh-exchange-idempotency-under-cutover-design.md)
  - `[system design]` [Refresh Reauth Escalation Matrix](./refresh-reauth-escalation-matrix-design.md)

<a id="system-design-auth-session-troubleshooting-bridge"></a>
## Auth Session Troubleshooting Bridge

security README의 [Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path)에서 browser/session symptom을 먼저 갈라 본 뒤, system-design 원인까지 내려갈 때 쓰는 subsection이다. 이 section에서도 `safe next step = primer bridge` vocabulary를 그대로 유지한다.
beginner handoff wording drift를 줄이기 위해 browser/session bridge 문서 둘은 같은 `20초 트리아지 결정표`를 공유한다. `302 + /login`은 `기억 / redirect`, `Application`에는 있는데 request `Cookie` header가 비면 `전송 / cookie-not-sent`, request `Cookie` header가 붙었는데도 계속 anonymous면 `조회 / server-anonymous`로 읽고, 표 원문은 [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md#20초-트리아지-결정표)와 [Browser BFF Session Boundary Primer](./browser-bff-session-boundary-primer.md#20초-트리아지-결정표)에서 같은 wording으로 본다.
여기서는 session-store 문서로 바로 넘기지 말고 초보자 표기 `SavedRequest`, `cookie-missing`, `server-anonymous`, `tenant-membership freshness`, `OIDC logout tail`을 먼저 갈라서 읽는다. 기존 `cookie-not-sent`, `server-mapping-missing`은 retrieval 별칭으로만 남긴다.
`hidden session mismatch`는 초보자가 "cookie는 보이는데 왜 다시 로그인하지?"를 뭉뚱그려 말할 때 쓰는 넓은 별칭이고, 실제 첫 분기는 보통 `전송` 실패인지 `복원` 실패인지다.

초보자용 mental model은 `기억`, `전송`, `복원`을 분리하는 것이다. `SavedRequest`는 "로그인 뒤 어디로 돌아갈지"를 기억하는 장치이고, cookie는 browser가 실제 요청에 붙여 보내야 하는 값이며, `server-anonymous`는 cookie가 왔는데도 서버가 session/token state를 복원하지 못한 장면을 뜻한다.
security README와 round-trip parity를 맞추려면 이 section의 안전한 사다리는 `[catalog] -> [primer] -> [primer bridge] -> [deep dive] -> [recovery] / [system design]`로 읽는다. 여기서 `[primer]`는 mental model을 고정하는 첫 문서, `[primer bridge]`는 security/system-design handoff를 붙이는 문서, `[deep dive]`는 framework/runtime 원인을 좁히는 문서, `[recovery]`는 지금 벌어진 degradation tail을 닫는 문서, `[system design]`은 session-store/cutover/control-plane 설계로 올라갈 때 붙는 badge다.

| security-side role badge | 여기서 뜻하는 것 | system-design 쪽으로 넘길 때 유지할 다음 role |
|---|---|---|
| `[catalog]` | symptom entrypoint를 다시 고르는 단계 | [Security: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path) |
| `[primer]` | storage/transport/session-memory mental model을 먼저 고정하는 단계 | [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md), [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md), [Stateless Sessions Primer](./stateless-sessions-primer.md) |
| `[primer bridge]` | security symptom을 system-design handoff 이름으로 안전하게 바꾸는 단계 | [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md), [Browser BFF Session Boundary Primer](./browser-bff-session-boundary-primer.md), [Security: OAuth2 vs OIDC Social Login Primer](../security/oauth2-oidc-social-login-primer.md) |
| `[deep dive]` | spring/security 원인을 실제로 좁히는 단계 | [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md), [Security: Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md) |
| `[recovery]` | store degradation tail, revoke propagation lag, partial outage를 닫는 단계 | [Security: BFF Session Store Outage / Degradation Recovery](../security/bff-session-store-outage-degradation-recovery.md), [Revocation Bus Regional Lag Recovery](./revocation-bus-regional-lag-recovery-design.md) |
| `[system design]` | session-store, revocation plane, cutover/control-plane 설계로 올라가는 단계 | [Session Store Design at Scale](./session-store-design-at-scale.md), [Canonical Revocation Plane Across Token Generations](./canonical-revocation-plane-across-token-generations-design.md) |

| 헷갈리는 이름 | mental model 한 줄 | DevTools/로그에서 볼 첫 증거 | beginner-safe starter order |
|---|---|---|---|
| `SavedRequest` (`기억`) | 원래 URL 기억은 남았지만, 복귀 요청에서 인증이 다시 성립하지 않는다 | `POST /login -> 302 original URL -> 302 /login` 반복 | `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md) |
| `cookie-missing` (`전송`, 기존 `cookie-not-sent`) | cookie가 저장돼 보여도, 실제 다음 요청 운반 단계에서 빠진다 | `Application > Cookies`에는 보이는데 Network request `Cookie` header가 비어 있음 | `[primer]` [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md) -> `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md) |
| `cookie-missing` subdomain 예시 | `auth.example.com`에 저장된 cookie가 `app.example.com` 요청에 자동 전송되는 것은 아니다 | 저장 host는 `auth.example.com`, 실패 요청은 `app.example.com/api/me`, request `Cookie` header는 비어 있음 | `[primer]` [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md)에서 `Domain`/host-only를 먼저 확인 -> `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md) -> 그 뒤에만 `server-anonymous` 갈래로 이동 |
| `server-anonymous` (`복원`, 기존 `server-mapping-missing`) | cookie는 왔지만 서버 복원 단계에서 session/BFF token mapping을 못 찾아 anonymous로 본다 | request `Cookie` header는 있는데 app log는 anonymous/session-not-found/token-mapping-miss | `[primer]` [Stateless Sessions Primer](./stateless-sessions-primer.md) -> `[primer bridge]` [Browser BFF Session Boundary Primer](./browser-bff-session-boundary-primer.md) -> `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md) -> `[deep dive]` [Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md) -> runtime tail이면 `[recovery]` [Security: BFF Session Store Outage / Degradation Recovery](../security/bff-session-store-outage-degradation-recovery.md), 설계 handoff면 `[system design]` [Session Store Design at Scale](./session-store-design-at-scale.md) |
| `revoke tail` | 저장은 끝났는데 revoke/grant freshness가 node, region, cache tier마다 늦게 닫힌다 | logout/revoke 성공 이벤트는 있는데 old session, stale allow, stale deny가 일부 경로에 남음 | `[primer]` [Session Revocation Basics](./session-revocation-basics.md) -> `[primer bridge]` [Security: Claim Freshness After Permission Changes](../security/claim-freshness-after-permission-changes.md) -> `[primer bridge]` [Security: Grant Path Freshness and Stale Deny Basics](../security/grant-path-freshness-stale-deny-basics.md) -> `[deep dive]` [Security: Session Revocation at Scale](../security/session-revocation-at-scale.md) -> runtime tail이면 `[recovery]` [Revocation Bus Regional Lag Recovery](./revocation-bus-regional-lag-recovery-design.md), plane redesign이면 `[system design]` [Canonical Revocation Plane Across Token Generations](./canonical-revocation-plane-across-token-generations-design.md) |
| `tenant-membership freshness` | membership 변경은 끝났는데 active tenant, workspace scope, tenant-scoped cache/session snapshot이 old context를 계속 쓴다 | tenant add/move/remove 이벤트는 성공했는데 old workspace가 남거나 새 tenant에서만 `403`이 반복됨 | `[primer]` [Security: Role Change and Session Freshness Basics](../security/role-change-session-freshness-basics.md) -> `[primer bridge]` [Security: Tenant Membership Change vs Session Scope Basics](../security/tenant-membership-change-session-scope-basics.md) -> `[deep dive]` [Security: Authorization Caching / Staleness](../security/authorization-caching-staleness.md) -> `[deep dive]` [Security: Tenant Isolation / AuthZ Testing](../security/tenant-isolation-authz-testing.md) -> runtime tail이면 `[recovery]` [Revocation Bus Regional Lag Recovery](./revocation-bus-regional-lag-recovery-design.md), tenant/session plane handoff면 `[system design]` [Session Store / Claim-Version Cutover](./session-store-claim-version-cutover-design.md) -> `[system design]` [Multi-tenant SaaS 격리](./multi-tenant-saas-isolation-design.md) |
| `OIDC logout tail` (`연동 로그아웃`) | 앱 logout은 끝났는데 IdP/back-channel 정리 순서가 어긋나 일부 세션만 남는다 | app logout 성공 로그는 있는데 IdP session/already-authenticated 상태가 재로그인처럼 보임 | `[primer]` [Role Change and Session Freshness Basics](../security/role-change-session-freshness-basics.md) -> `[primer bridge]` [Security: OAuth2 vs OIDC Social Login Primer](../security/oauth2-oidc-social-login-primer.md) -> `[deep dive]` [Security: OIDC Back-Channel Logout / Session Coherence](../security/oidc-backchannel-logout-session-coherence.md) -> propagation tail이면 `[recovery]` [Revocation Bus Regional Lag Recovery](./revocation-bus-regional-lag-recovery-design.md), federation/session-plane redesign이면 `[system design]` [Canonical Revocation Plane Across Token Generations](./canonical-revocation-plane-across-token-generations-design.md) |

공통 혼동: `SavedRequest`가 loop를 만든 것처럼 보여도, 실제로는 원래 URL로 돌아간 다음 단계에서 cookie가 빠졌거나 서버가 anonymous로 해석한 경우가 많다. 그래서 첫 분기는 "cookie가 요청에 실렸나?"이고, 그다음이 "서버가 그 값을 복원했나?"다.

짧게 다시 외우면:

- `SavedRequest`는 `기억`이지, 인증 유지 성공 자체가 아니다.
- `Application > Cookies`에 값이 보인다고 `Cookie` header까지 자동 보장되지는 않는다.
- request `Cookie` header가 보인다고 서버 session/BFF mapping 복원 성공까지 자동 보장되지는 않는다.

짧은 최소 증거 체크리스트:

| branch | DevTools에서 1개만 먼저 캡처 | 로그에서 1개만 먼저 찾기 | safe next step |
|---|---|---|---|
| `SavedRequest` | 로그인 직후 `POST /login -> 302 original URL -> 302 /login` 같은 redirect chain 1개 | same request window에서 `SavedRequest` restore / redirect target / entry point log 1개 | `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) |
| `cookie-missing` | 실패한 요청 1개에서 request `Cookie` header가 비어 있는지, 또는 `Application > Cookies`엔 있는데 전송이 안 되는지 1개 | `Set-Cookie` 발급 또는 cookie scope mismatch를 보여 주는 access/proxy/app log 1개 | `[primer]` [Cookie Scope Mismatch Guide](../security/cookie-scope-mismatch-guide.md) |
| `server-anonymous` | 실패한 요청 1개에서 request `Cookie` header가 실제로 붙어 있는지 1개 | 같은 요청에서 `anonymous`, `session-not-found`, `token-mapping-miss` 같은 app log 1개 | `[primer]` [Browser BFF Session Boundary Primer](./browser-bff-session-boundary-primer.md) |
| `revoke tail` / `OIDC logout tail` | logout/revoke 뒤에도 통과한 요청 1개, 또는 재로그인처럼 보인 redirect/network trace 1개 | revoke/logout success event와 늦게 닫힌 allow/deny/session cleanup log 중 1개 | `[primer]` [Session Revocation Basics](./session-revocation-basics.md) |
| `tenant-membership freshness` | tenant 이동/추가/제거 뒤 old workspace가 남는 요청 1개, 또는 새 tenant에서만 `403`이 남는 요청 1개 | tenant membership change event와 stale workspace/tenant context를 보여 주는 app log 1개 | `[primer]` [Security: Role Change and Session Freshness Basics](../security/role-change-session-freshness-basics.md) |

초보자 기준으로는 branch마다 증거를 많이 모으는 것보다 `DevTools 1개 + 로그 1개`를 같은 요청 창으로 맞추는 편이 더 안전하다. 먼저 한 쌍을 맞춘 뒤에만 아래 branch ladder로 내려간다.

1. `SavedRequest` (`SavedRequest loop`)
   - 로그인은 성공한 것 같은데 같은 보호 URL로 다시 튀거나 `401 -> 302 -> /login` bounce, login HTML 응답, 숨은 `JSESSIONID`가 redirect 직후에만 보일 때 본다.
   - 순서: `[catalog]` [Security: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path) -> `[primer]` [Login Redirect, Hidden `JSESSIONID`, `SavedRequest` 입문](../network/login-redirect-hidden-jsessionid-savedrequest-primer.md) -> `[primer bridge]` [Browser `401` vs `302` Login Redirect Guide](../security/browser-401-vs-302-login-redirect-guide.md) -> `[deep dive]` [Spring Security `RequestCache` / `SavedRequest` Boundaries](../spring/spring-security-requestcache-savedrequest-boundaries.md) -> `[deep dive]` [Spring `SecurityContextRepository` and `SessionCreationPolicy` Boundaries](../spring/spring-securitycontextrepository-sessioncreationpolicy-boundaries.md)
   - 이 branch는 redirect 복귀와 hidden session 생성 경계가 핵심이므로, browser cookie는 남아 있는데 서버측 session/token translation이 실제로 사라졌다는 증거가 잡히기 전에는 `[system design]` [Session Store Design at Scale](./session-store-design-at-scale.md)로 바로 내려가지 않는다.

2. `server-anonymous` (`hidden session mismatch`, 기존 `server-mapping-missing`)
   - cookie는 살아 있는데 서버가 session/token translation을 못 찾거나, node/region별로 login 상태가 흔들리고, logout은 되는데 일부 BFF/downstream 호출만 계속 통과할 때 본다.
   - 순서: `[catalog]` [Security: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path) -> `[primer]` [Stateless Sessions Primer](./stateless-sessions-primer.md) -> `[primer bridge]` [Browser BFF Session Boundary Primer](./browser-bff-session-boundary-primer.md) -> `[deep dive]` [Security: Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md) -> runtime 장애를 닫는다면 `[recovery]` [Security: BFF Session Store Outage / Degradation Recovery](../security/bff-session-store-outage-degradation-recovery.md), 구조 자체를 바꿔야 하면 `[system design]` [Session Store Design at Scale](./session-store-design-at-scale.md)
   - claim semantic, authority migration, mixed-version rollout이 같이 묶이면 `[system design]` [Session Store / Claim-Version Cutover](./session-store-claim-version-cutover-design.md)까지 이어 붙인다.

3. `revoke tail`
   - mismatch가 아니라 revoke propagation, logout tail, claim-version cleanup tail로 확인되면 아래 순서로 내려간다.
   - 순서: `[catalog]` [Security: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path) -> `[primer]` [Session Revocation Basics](./session-revocation-basics.md) -> `[primer bridge]` [Security: Claim Freshness After Permission Changes](../security/claim-freshness-after-permission-changes.md) -> `[primer bridge]` [Security: Grant Path Freshness and Stale Deny Basics](../security/grant-path-freshness-stale-deny-basics.md) -> `[deep dive]` [Security: Session Revocation at Scale](../security/session-revocation-at-scale.md) -> `[deep dive]` [Security: Revocation Propagation Lag / Debugging](../security/revocation-propagation-lag-debugging.md) -> 지금 남은 lag를 닫는다면 `[recovery]` [Revocation Bus Regional Lag Recovery](./revocation-bus-regional-lag-recovery-design.md), revoke plane 자체를 다시 설계한다면 `[system design]` [Canonical Revocation Plane Across Token Generations](./canonical-revocation-plane-across-token-generations-design.md)

4. `tenant-membership freshness`
   - tenant add/move/remove 뒤 old workspace가 계속 보이거나 새 tenant에서만 `403`이 남으면 allow/deny tail과 섞지 말고 tenant context freshness branch로 먼저 고정한다.
   - 순서: `[catalog]` [Security: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path) -> `[primer]` [Security: Role Change and Session Freshness Basics](../security/role-change-session-freshness-basics.md) -> `[primer bridge]` [Security: Tenant Membership Change vs Session Scope Basics](../security/tenant-membership-change-session-scope-basics.md) -> `[deep dive]` [Security: Authorization Caching / Staleness](../security/authorization-caching-staleness.md) -> `[deep dive]` [Security: Tenant Isolation / AuthZ Testing](../security/tenant-isolation-authz-testing.md) -> runtime tail을 닫는다면 `[recovery]` [Revocation Bus Regional Lag Recovery](./revocation-bus-regional-lag-recovery-design.md), tenant/session plane 설계로 올리면 `[system design]` [Session Store / Claim-Version Cutover](./session-store-claim-version-cutover-design.md) -> `[system design]` [Multi-tenant SaaS 격리](./multi-tenant-saas-isolation-design.md)

5. `OIDC logout tail` (`federated logout`)
   - app logout 성공 이후에도 IdP session 또는 back-channel 정리 지연 때문에 재로그인/부분 통과처럼 보이면 이 갈래로 본다.
   - 순서: `[catalog]` [Security: Browser / Session Troubleshooting Path](../security/README.md#browser--session-troubleshooting-path) -> `[primer]` [Security: Role Change and Session Freshness Basics](../security/role-change-session-freshness-basics.md) -> `[primer bridge]` [Security: OAuth2 vs OIDC Social Login Primer](../security/oauth2-oidc-social-login-primer.md) -> `[deep dive]` [Security: OIDC Back-Channel Logout / Session Coherence](../security/oidc-backchannel-logout-session-coherence.md) -> propagation tail을 먼저 닫는다면 `[recovery]` [Revocation Bus Regional Lag Recovery](./revocation-bus-regional-lag-recovery-design.md), federation/session-plane 재설계가 필요하면 `[system design]` [Canonical Revocation Plane Across Token Generations](./canonical-revocation-plane-across-token-generations-design.md)

<a id="system-design-database-security-authority-bridge"></a>
## Database / Security Authority Bridge

database authority 이동과 identity capability rollout이 같이 얽힌 cutover를 추적할 때 쓰는 subsection이다. security README의 `Identity / Delegation / Lifecycle`, database README의 `Identity / Authority Transfer 브리지` / `Authority Transfer / Security Bridge`에서 넘어오는 같은 authority-transfer route를 system-design handoff 이름으로 받는 구간이다.
beginner-path alias wording으로는 `deprovision tail -> access tail -> decision parity -> cleanup evidence` 중 이 subsection이 `decision parity`를 맡고, 아래 `Verification / Shadowing / Authority Bridge`가 `cleanup evidence`를 맡는다.
초보자용 mental model: 여기서는 "권한 이름이 무엇인가"보다 "새 authority path를 켜도 모든 요청 경로가 같은 결정을 내리고, old path cleanup으로 되돌릴 수 없는 실수를 하지 않는가"를 본다. `Database / Security Authority Bridge`는 cutover 설계 입구이고, `Verification / Shadowing / Authority Bridge`는 그 증거로 cleanup gate를 닫는 후반 입구다.
- SCIM/deprovision symptom으로 들어왔으면 이 subsection을 첫 문서로 보지 않는다. 먼저 같은 primer-first 순서를 고정한다: `[primer]` [Security: Identity Lifecycle / Provisioning Primer](../security/identity-lifecycle-provisioning-primer.md) -> `[primer]` [Security: Role Change and Session Freshness Basics](../security/role-change-session-freshness-basics.md) -> `[primer bridge]` [Security: Claim Freshness After Permission Changes](../security/claim-freshness-after-permission-changes.md) -> `[cross-category bridge]` [Database: Identity / Authority Transfer 브리지](../database/README.md#database-bridge-identity-authority) -> 그다음에야 이 `[system design]` bridge와 아래 cutover docs로 내려간다.
category README bridge entrypoint를 같이 맞추려면 `[cross-category bridge]` [Database: Identity / Authority Transfer 브리지](../database/README.md#database-bridge-identity-authority), `[cross-category bridge]` [Security: Identity / Delegation / Lifecycle](../security/README.md#identity--delegation--lifecycle)를 먼저 열고, parity/retirement evidence까지 넘길 때는 아래 `[system design]` [Verification / Shadowing / Authority Bridge](#system-design-verification-shadowing-authority-bridge)로 이어 붙인다. paired subsection 사이를 왕복할 때는 system-design 문서에 `[system design]`, security deep dive나 catalog로 되돌아가는 지점에 `[deep dive]` / `[catalog]` cue를 다시 붙여 앞 링크 badge가 뒤 링크로 암묵 상속되지 않게 유지한다.
안전한 round-trip ladder는 `[cross-category bridge]` security/database entrypoint -> `[system design]` Database / Security Authority Bridge -> `[system design]` Verification / Shadowing / Authority Bridge -> `[deep dive]` security evidence docs다.

| handoff stage | 유지할 role badge | 이 stage의 job |
|---|---|---|
| database/security symptom entrypoint | `[cross-category bridge]` | authority-transfer 질문을 sibling README label로 먼저 받는다 |
| cutover 설계 입구 | `[system design]` | new path rollout, claim/session/store cutover, retirement guard를 설계한다 |
| verification / cleanup gate | `[system design]` | shadow/parity evidence와 reversible cleanup 조건을 설계한다 |
| security evidence hand-back | `[deep dive]` | runtime signal, decision log, audit evidence로 cleanup 근거를 닫는다 |

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
## Capability Rollout Deepening

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
  - `[system design]` [Tenant Split-Out with Service Identity Rollout](./tenant-split-out-service-identity-rollout-design.md)
  - `[system design]` [Database / Security Identity Bridge Cutover](./database-security-identity-bridge-cutover-design.md)
  - `[system design]` [Adapter Retirement / Compatibility Bridge Decommission](./adapter-retirement-compatibility-bridge-decommission-design.md)

<a id="system-design-verification-shadowing-authority-bridge"></a>
## Verification / Shadowing / Authority Bridge

read parity, revoke propagation, auth shadow evaluation, authority transfer를 한 흐름으로 묶고 그 근거를 retirement/cleanup gate까지 넘겨 보고 싶을 때 쓰는 subsection이다. 같은 authority-transfer route를 late-stage verification / cleanup 이름으로 다시 부르는 handoff라서, security/database README의 sibling label과 함께 보존해야 retrieval route가 끊기지 않는다.
visible beginner label로는 `cleanup evidence` 단계다. 앞 bridge의 `decision parity`가 맞는지 shadow/diff/audit evidence로 닫는 곳이라고 먼저 읽으면 database/security README의 alias wording과 같은 순서로 이어진다.
초보자 기준으로는 이 section을 새 주제의 시작으로 보지 말고, 앞 bridge에서 세운 "새 authority path가 같은 결정을 내리는가" 질문의 증거 수집 단계로 읽는다. `traffic shadowing`, `dual-read`, `decision log`, `audit evidence`는 모두 cleanup/retirement 결정을 뒷받침하는 확인 수단이다.
- beginner-safe 재진입 순서도 앞 subsection과 동일하다: `[primer]` [Security: Identity Lifecycle / Provisioning Primer](../security/identity-lifecycle-provisioning-primer.md) -> `[primer]` [Security: Role Change and Session Freshness Basics](../security/role-change-session-freshness-basics.md) -> `[primer bridge]` [Security: Claim Freshness After Permission Changes](../security/claim-freshness-after-permission-changes.md) -> `[cross-category bridge]` [Database: Identity / Authority Transfer 브리지](../database/README.md#database-bridge-identity-authority) -> `[system design]` [Database / Security Authority Bridge](#system-design-database-security-authority-bridge). `traffic shadowing`과 cleanup gate 문서는 이 primer-first SCIM order 뒤에만 붙인다.
database/security 쪽 navigator parity를 유지하려면 `[cross-category bridge]` [Database: Identity / Authority Transfer 브리지](../database/README.md#database-bridge-identity-authority), `[cross-category bridge]` [Security: Identity / Delegation / Lifecycle](../security/README.md#identity--delegation--lifecycle), 위 `[system design]` [Database / Security Authority Bridge](#system-design-database-security-authority-bridge)를 함께 본다. 이 paired subsection도 system-design 설계 문서에는 `[system design]`, security deep dive로 hand back하는 지점에는 `[deep dive]` cue를 다시 붙여 reciprocity를 맞춘다.
짧게 외우면 `[cross-category bridge]`에서 질문을 받고, `[system design]`에서 parity/cleanup gate를 설계한 뒤, 마지막 근거 확인은 `[deep dive]` security evidence docs로 되돌아간다.

  - `[system design]` [Traffic Shadowing / Progressive Cutover](./traffic-shadowing-progressive-cutover-design.md)
  - `[system design]` [Dual-Read Comparison / Verification Platform](./dual-read-comparison-verification-platform-design.md)
  - `[system design]` [Session Store / Claim-Version Cutover](./session-store-claim-version-cutover-design.md)
  - `[system design]` [Verifier Overlap Hard-Reject Retirement Gates](./verifier-overlap-hard-reject-retirement-gates-design.md)
  - `[recovery]` [Revocation Bus Regional Lag Recovery](./revocation-bus-regional-lag-recovery-design.md)
  - `[deep dive]` [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)
  - `[deep dive]` [Security: AuthZ Decision Logging Design](../security/authz-decision-logging-design.md)
  - `[deep dive]` [Security: Audit Logging for Auth / AuthZ Traceability](../security/audit-logging-auth-authz-traceability.md)
  - `[system design]` [Database / Security Identity Bridge Cutover](./database-security-identity-bridge-cutover-design.md)
  - `[system design]` [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md)
  - `[system design]` [Adapter Retirement / Compatibility Bridge Decommission](./adapter-retirement-compatibility-bridge-decommission-design.md)
  - `[system design]` [Cleanup Point-of-No-Return](./cleanup-point-of-no-return-design.md)
  - `[system design]` [Tenant Split-Out with Service Identity Rollout](./tenant-split-out-service-identity-rollout-design.md)

<a id="system-design-decommission-retirement-cluster"></a>
## Decommission / Retirement Cluster

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
| 78 | Monotonic Reads and Session Guarantees Primer (beginner용 `read-after-write` vs `monotonic guard` 한 줄 비교표 + monotonic vs causal 1문장 오답 카드) | 🟢 Basic | [monotonic-reads-and-session-guarantees-primer.md](monotonic-reads-and-session-guarantees-primer.md) |
| 79 | Writes-Follow-Reads Primer | 🟢 Basic | [writes-follow-reads-primer.md](writes-follow-reads-primer.md) |
| 80 | Monotonic Writes Ordering Primer | 🟢 Basic | [monotonic-writes-ordering-primer.md](monotonic-writes-ordering-primer.md) |
| 81 | Session Guarantees Decision Matrix | 🟢 Basic | [session-guarantees-decision-matrix.md](session-guarantees-decision-matrix.md) |
| 82 | Session Policy Implementation Sketches | 🟢 Basic | [session-policy-implementation-sketches.md](session-policy-implementation-sketches.md) |
| 83 | List-Detail Monotonicity Bridge (beginner confusion note + glossary anchor jumps for `recent-write` / `min-version floor` / `monotonic guard`) | 🟢 Basic | [list-detail-monotonicity-bridge.md](list-detail-monotonicity-bridge.md) |
| 84 | Causal Consistency Notification Primer | 🟢 Basic | [causal-consistency-notification-primer.md](causal-consistency-notification-primer.md) |
| 85 | Notification Causal Token Walkthrough | 🟢 Basic | [notification-causal-token-walkthrough.md](notification-causal-token-walkthrough.md) |
| 86 | Cache Acceptance Rules for Causal Reads | 🟢 Basic | [cache-acceptance-rules-for-causal-reads.md](cache-acceptance-rules-for-causal-reads.md) |
| 87 | Notification Badge vs Source Freshness Primer | 🟢 Basic | [notification-badge-vs-source-freshness-primer.md](notification-badge-vs-source-freshness-primer.md) |
| 88 | Mixed Cache+Replica Freshness Bridge (beginner taxonomy map for `recent-write` -> `recent_write`) | 🟢 Basic | [mixed-cache-replica-freshness-bridge.md](mixed-cache-replica-freshness-bridge.md) |
| 89 | Outbox Watermark Token Primer | 🟢 Basic | [outbox-watermark-token-primer.md](outbox-watermark-token-primer.md) |
| 90 | Shard Key Selection Basics | 🟢 Basic | [shard-key-selection-basics.md](shard-key-selection-basics.md) |
| 91 | Session Revocation Basics | 🟢 Basic | [session-revocation-basics.md](session-revocation-basics.md) |
| 92 | Read-Only and Graceful Degradation Patterns | 🟡 Intermediate | [read-only-and-graceful-degradation-patterns.md](read-only-and-graceful-degradation-patterns.md) |
| 93 | Retry Amplification and Backpressure Primer | 🟢 Basic | [retry-amplification-and-backpressure-primer.md](retry-amplification-and-backpressure-primer.md) |
| 94 | Rejected-Hit Observability Primer (Reason-to-Action + aligned `fallback_reason` checklist) | 🟢 Basic | [rejected-hit-observability-primer.md](rejected-hit-observability-primer.md) |
| 95 | Mixed Cache+Replica Read Path Pitfalls | 🟡 Intermediate | [mixed-cache-replica-read-path-pitfalls.md](mixed-cache-replica-read-path-pitfalls.md) |
| 96 | Post-Write Stale Dashboard Primer (signal field mini-appendix + glossary jumps + source mix 급변 미니 사례 + stale baseline 함정 표 + 화면 역행 지표 연결 카드) | 🟢 Basic | [post-write-stale-dashboard-primer.md](post-write-stale-dashboard-primer.md) |
| 97 | Stateless 백엔드, 캐시, 데이터베이스, 큐 스타터 팩 | 🟢 Basic | [stateless-backend-cache-database-queue-starter-pack.md](stateless-backend-cache-database-queue-starter-pack.md) |
| 98 | 캐시 기초 (Caching Basics) | 🟢 Basic | [caching-basics.md](caching-basics.md) |
| 99 | 메시지 큐 기초 (Message Queue Basics) | 🟢 Basic | [message-queue-basics.md](message-queue-basics.md) |
| 100 | Consistency, Idempotency, and Async Workflow Foundations | 🟢 Basic | [consistency-idempotency-async-workflow-foundations.md](consistency-idempotency-async-workflow-foundations.md) |
| 101 | Beginner Consistency Self-Check Worksheet (문서 상단 `증상별 시작 링크` 고정: `방금 저장한 값 미반영 / 목록-상세 역행 / 알림 원인 미도착 / 숫자 재확인` -> 워크시트 칸 바로 이동 + glossary 퀴즈 2개 이상 혼동 시 `Read This Next If You Missed 2+` bridge + 작성 순서 4칸 카드 + 용어 대응표 3행 + `무효화 선택 vs floor 처리` 1문장 비교표 + `프로필 / 설정 / 헤더` 3칸 projection 체크리스트 + `알림 읽음` 5분 채점 예시 + `display_name` Yes/No + `충분/우수` 합본 미니 예시 + `display_name` vs `avatar_url` 비교표 + `candidate < floor` 오답 체크 1문항 + causal Yes/No 기준선/primary fallback 분기 + 3단계 미니 루브릭 + 항목별 `미흡 -> primer` 한 줄 매핑표 + Yes/No 통과 기준) | 🟢 Basic | [beginner-consistency-self-check-worksheet.md](beginner-consistency-self-check-worksheet.md) |
| 102 | First 15-Minute Triage Flow Card (starter-matrix action -> first dashboard panel bridge) | 🟢 Basic | [first-15-minute-triage-flow-card.md](first-15-minute-triage-flow-card.md) |
| 103 | Cross-Primer Glossary Anchors (Confusion Guardrail Box + 대표 오답 미니 카드 `TTL만 선택` / `floor 미달인데 그대로 노출` / `cache miss면 무조건 fresh` + `오답 문장 앵커`의 `cache hit이면 통과` / `cache hit이면 최신이다` 검색 교정 + glossary quiz answer-explanation lines + 2개 이상 혼동 시 30초 worksheet handoff bridge) | 🟢 Basic | [cross-primer-glossary-anchors.md](cross-primer-glossary-anchors.md) |
| 104 | Search Hit Overlay Pattern | 🟢 Basic | [search-hit-overlay-pattern.md](search-hit-overlay-pattern.md) |

## 학습 순서 추천

아래 구간은 broad survey에 가깝고, 세부 설계 trade-off는 각 문서로 내려가서 읽는 편이 좋다.

```
System Design Foundations → Stateless 백엔드, 캐시, 데이터베이스, 큐 스타터 팩 → 캐시 기초 → 메시지 큐 기초 → Consistency, Idempotency, and Async Workflow Foundations → Request Path Failure Modes Primer → Request Deadline and Timeout Budget Primer → Retry Amplification and Backpressure Primer → Read-Only and Graceful Degradation Patterns → Stateless Sessions Primer → Load Balancer Drain and Affinity Primer → Browser BFF Session Boundary Primer → Session Revocation Basics → Database Scaling Primer → Shard Key Selection Basics → Caching vs Read Replica Primer → Cache Invalidation Patterns Primer → Read-After-Write Consistency Basics → Read-After-Write Routing Primer → Monotonic Reads and Session Guarantees Primer → Writes-Follow-Reads Primer → Monotonic Writes Ordering Primer → Session Guarantees Decision Matrix → Session Policy Implementation Sketches → List-Detail Monotonicity Bridge → Search Hit Overlay Pattern → Causal Consistency Notification Primer → Notification Causal Token Walkthrough → Cache Acceptance Rules for Causal Reads → Notification Badge vs Source Freshness Primer → Mixed Cache+Replica Freshness Bridge → Outbox Watermark Token Primer → Rejected-Hit Observability Primer → First 15-Minute Triage Flow Card → Post-Write Stale Dashboard Primer → Cross-Primer Glossary Anchors → Beginner Consistency Self-Check Worksheet → Mixed Cache+Replica Read Path Pitfalls → 프레임워크 → 추정법 → URL 단축기 → Rate Limiter → 분산 캐시 → Multi-tenant SaaS 격리 → Payment System / Ledger / Reconciliation → Idempotency Key Store / Replay-Safe Retry → Consistent Hashing → Newsfeed → Notification → 채팅 시스템 → Distributed Lock → Search → File Storage → Workflow
```

## 심화 트랙 추천

- 데이터 이동/동기화: [Outbox Watermark Token Primer](./outbox-watermark-token-primer.md) → [Change Data Capture / Outbox Relay](./change-data-capture-outbox-relay-design.md) → [Historical Backfill / Replay Platform](./historical-backfill-replay-platform-design.md) → [Search Indexing Pipeline](./search-indexing-pipeline-design.md) → [Event Bus Control Plane](./event-bus-control-plane-design.md)
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
- consistency budget: [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md) → [Read-After-Write Routing Primer](./read-after-write-routing-primer.md) → [Monotonic Reads and Session Guarantees Primer](./monotonic-reads-and-session-guarantees-primer.md) → [Writes-Follow-Reads Primer](./writes-follow-reads-primer.md) → [Monotonic Writes Ordering Primer](./monotonic-writes-ordering-primer.md) → [Session Guarantees Decision Matrix](./session-guarantees-decision-matrix.md) → [Session Policy Implementation Sketches](./session-policy-implementation-sketches.md) → [List-Detail Monotonicity Bridge](./list-detail-monotonicity-bridge.md) → [Causal Consistency Notification Primer](./causal-consistency-notification-primer.md) → [Notification Causal Token Walkthrough](./notification-causal-token-walkthrough.md) → [Cache Acceptance Rules for Causal Reads](./cache-acceptance-rules-for-causal-reads.md) → [Notification Badge vs Source Freshness Primer](./notification-badge-vs-source-freshness-primer.md) → [Mixed Cache+Replica Freshness Bridge](./mixed-cache-replica-freshness-bridge.md) → [Trace Attribute Freshness / Read-Source Bridge](./trace-attribute-freshness-read-source-bridge.md) → [Outbox Watermark Token Primer](./outbox-watermark-token-primer.md) → [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md) → [First 15-Minute Triage Flow Card](./first-15-minute-triage-flow-card.md) → [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md) → [Beginner Consistency Self-Check Worksheet](./beginner-consistency-self-check-worksheet.md) → [Mixed Cache+Replica Read Path Pitfalls](./mixed-cache-replica-read-path-pitfalls.md) → [Read / Write Quorum & Staleness Budget](./read-write-quorum-staleness-budget-design.md) → [Consistency Repair / Anti-Entropy Platform](./consistency-repair-anti-entropy-platform-design.md) → [Session Store Design at Scale](./session-store-design-at-scale.md)
  - 초보자용 한 줄 구분: `방금 쓴 값`이면 read-after-write, `내가 이미 본 값보다 뒤로 가면` monotonic, `결과를 먼저 봤다면 원인도 이어서 보여야 하면` causal로 먼저 읽으면 된다.
  - notification 숫자 해석 분기점: `badge`, `unread_count`, `projection_watermark`가 보이면 요약 projection 숫자인지부터 보고 [Notification Badge vs Source Freshness Primer](./notification-badge-vs-source-freshness-primer.md)로 간다. `required_watermark`, `entity_version`, `min_version floor`가 보이면 클릭 뒤 source 입장 기준선이므로 [Notification Causal Token Walkthrough](./notification-causal-token-walkthrough.md) → [Cache Acceptance Rules for Causal Reads](./cache-acceptance-rules-for-causal-reads.md) 순서로 읽는다. `stale peak multiplier`, `fallback headroom ratio`, `rejected_hit_reason=watermark`가 보이면 causal fallback을 얼마나 더 밀 수 있는지 보는 운영 숫자이므로 [Rejected-Hit Observability Primer](./rejected-hit-observability-primer.md)와 [Post-Write Stale Dashboard Primer](./post-write-stale-dashboard-primer.md)로 넘긴다.
  - 빠른 기억법: notification route에서 `count 숫자`는 "요약판이 얼마나 따라왔나", `watermark/version 숫자`는 "클릭한 원본을 보여 줘도 되나", `headroom 숫자`는 "그 fallback을 계속 써도 primary가 버티나"를 뜻한다.
  - 빠른 구분표:

| 증상 | 먼저 필요한 보장 | 추천 문서 |
|---|---|---|
| 저장 직후 상세/프로필에 예전 값이 다시 보임 | read-after-write | [Read-After-Write Consistency Basics](./read-after-write-consistency-basics.md) |
| 상세에서는 `PAID`였는데 목록으로 가니 `PENDING`처럼 뒤로 감 | monotonic reads | [Monotonic Reads and Session Guarantees Primer](./monotonic-reads-and-session-guarantees-primer.md) |
| 알림/배지에서 완료를 봤는데 들어가 보니 원문·주문·댓글이 아직 안 보임 | causal consistency | [Causal Consistency Notification Primer](./causal-consistency-notification-primer.md) |
- stale write / version precondition starter: [Writes-Follow-Reads Primer](./writes-follow-reads-primer.md) → [Session Guarantees Decision Matrix](./session-guarantees-decision-matrix.md) → [Database: Compare-and-Set와 Version Columns](../database/compare-and-set-version-columns.md) → [Database: Version Column Retry Walkthrough](../database/version-column-retry-walkthrough.md) → [Network: Strong vs Weak ETag: validator 정밀도와 cache correctness](../network/strong-vs-weak-etag-validator-precision-cache-correctness.md)
- per-session write ordering starter: [Monotonic Writes Ordering Primer](./monotonic-writes-ordering-primer.md) → [Session Guarantees Decision Matrix](./session-guarantees-decision-matrix.md) → [Session Policy Implementation Sketches](./session-policy-implementation-sketches.md) → [Idempotency Key Store / Dedup Window / Replay-Safe Retry](./idempotency-key-store-dedup-window-replay-safe-retry-design.md) → [Distributed Lock 설계](./distributed-lock-design.md)
- browser BFF auth boundary basics: [Stateless Sessions Primer](./stateless-sessions-primer.md) → [Browser BFF Session Boundary Primer](./browser-bff-session-boundary-primer.md) → `[primer bridge]` [Auth Session Troubleshooting Bridge](#system-design-auth-session-troubleshooting-bridge) (`SavedRequest` / `cookie-missing` / `server-anonymous`, 기존 `cookie-not-sent` / `server-mapping-missing`) → [Session Store Design at Scale](./session-store-design-at-scale.md) → [Security: Browser / BFF Token Boundary / Session Translation](../security/browser-bff-token-boundary-session-translation.md)
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

## 한 줄 정리

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
