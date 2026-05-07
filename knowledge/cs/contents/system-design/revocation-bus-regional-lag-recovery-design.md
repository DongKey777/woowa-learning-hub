---
schema_version: 3
title: Revocation Bus Regional Lag Recovery 설계
concept_id: system-design/revocation-bus-regional-lag-recovery-design
canonical: false
category: system-design
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 84
mission_ids: []
review_feedback_tags:
- revocation bus regional lag
- revoke propagation recovery
- revocation redrive
- revocation re-drive
aliases:
- revocation bus regional lag
- revoke propagation recovery
- revocation redrive
- revocation re-drive
- revoke dedupe
- cache invalidation replay
- stale allow recovery
- regional revoke backlog
- lagging cache tier
- revoke epoch watermark
- forced logout probe
- revocation observability
symptoms:
- Revocation Bus Regional Lag Recovery 설계 관련 장애나 마이그레이션 리스크가 발생해 단계별 대응이 필요하다
intents:
- troubleshooting
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/session-store-claim-version-cutover-design.md
- contents/system-design/multi-region-active-active-design.md
- contents/system-design/session-store-design-at-scale.md
- contents/system-design/canonical-revocation-plane-across-token-generations-design.md
- contents/system-design/distributed-cache-design.md
- contents/system-design/consistency-repair-anti-entropy-platform-design.md
- contents/system-design/replay-repair-orchestration-control-plane-design.md
- contents/system-design/global-traffic-failover-control-plane-design.md
- contents/system-design/refresh-family-rotation-cutover-design.md
- contents/security/session-revocation-at-scale.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Revocation Bus Regional Lag Recovery 설계 장애 대응 순서를 알려줘
- revocation bus regional lag 복구 설계 체크리스트가 뭐야?
- Revocation Bus Regional Lag Recovery 설계에서 blast radius를 어떻게 제한해?
- revocation bus regional lag 운영 리스크를 줄이는 방법은?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Revocation Bus Regional Lag Recovery 설계를 다루는 playbook 문서다. revocation bus regional lag recovery 설계는 특정 region이나 cache tier가 revoke fan-out에서 뒤처졌을 때 durable replay log, idempotent dedupe, lag-aware traffic degrade, synthetic verification을 함께 써서 stale allow long tail을 수습하는 운영 설계다. 검색 질의가 revocation bus regional lag, revoke propagation recovery, revocation redrive, revocation re-drive처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Revocation Bus Regional Lag Recovery 설계

> 한 줄 요약: revocation bus regional lag recovery 설계는 특정 region이나 cache tier가 revoke fan-out에서 뒤처졌을 때 durable replay log, idempotent dedupe, lag-aware traffic degrade, synthetic verification을 함께 써서 stale allow long tail을 수습하는 운영 설계다.
>
> 문서 역할: 이 문서는 [Session Store / Claim-Version Cutover 설계](./session-store-claim-version-cutover-design.md)의 revocation clock과 [Multi-Region Active-Active 설계](./multi-region-active-active-design.md)의 regional failure behavior 사이를 메우는 focused deep dive다.

retrieval-anchor-keywords: revocation bus regional lag, revoke propagation recovery, revocation redrive, revocation re-drive, revoke dedupe, cache invalidation replay, stale allow recovery, regional revoke backlog, lagging cache tier, revoke epoch watermark, forced logout probe, revocation observability, invalidate storm prevention, session revoke multi-region, replay safe invalidation, generation-aware revocation, alias projection lag, family quarantine fan-out

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Session Store Design at Scale](./session-store-design-at-scale.md)
> - [Session Store / Claim-Version Cutover 설계](./session-store-claim-version-cutover-design.md)
> - [Canonical Revocation Plane Across Token Generations 설계](./canonical-revocation-plane-across-token-generations-design.md)
> - [Multi-Region Active-Active 설계](./multi-region-active-active-design.md)
> - [Distributed Cache 설계](./distributed-cache-design.md)
> - [Consistency Repair / Anti-Entropy Platform 설계](./consistency-repair-anti-entropy-platform-design.md)
> - [Replay / Repair Orchestration Control Plane 설계](./replay-repair-orchestration-control-plane-design.md)
> - [Global Traffic Failover Control Plane 설계](./global-traffic-failover-control-plane-design.md)
> - [Refresh-Family Rotation Cutover 설계](./refresh-family-rotation-cutover-design.md)
> - [Security: Session Revocation at Scale](../security/session-revocation-at-scale.md)
> - [Security: Revocation Propagation Lag / Debugging](../security/revocation-propagation-lag-debugging.md)
> - [Security: JWT / JWKS Outage Recovery / Failover Drills](../security/jwt-jwks-outage-recovery-failover-drills.md)

## 핵심 개념

revoke plane에서 가장 위험한 장애는 "이벤트가 완전히 사라진 경우"보다
"한 region 또는 한 cache tier만 뒤처져 stale allow가 길게 남는 경우"다.

- origin/session authority는 이미 revoke를 알고 있다
- 일부 region-local consumer나 edge cache만 old verdict를 계속 들고 있다
- 로그인/조회는 대부분 정상이라 사고가 늦게 발견된다
- cleanup이나 failback을 서두르면 zombie session tail이 더 길어진다

그래서 좋은 설계는 pub/sub health check 하나로 끝나지 않는다.
핵심은 아래 네 가지를 같이 갖추는 것이다.

- replay 가능한 durable revoke ledger
- scope/epoch 기반 idempotent apply
- lagging region을 좁혀서 redrive하는 repair path
- "정말 tail이 닫혔는가"를 보는 synthetic observability

즉 이 주제는 메세지 재전송이 아니라 **revocation drift를 탐지하고 안전하게 수리하는 운영 설계**다.

## 깊이 들어가기

### 1. 먼저 무엇이 뒤처졌는지 층별로 분리한다

같은 "logout tail"이라도 뒤처진 층이 다르면 복구 전략도 달라진다.

| lagging layer | 보이는 증상 | 잘못된 대응 | 권장 대응 |
|---|---|---|---|
| region revoke consumer | 특정 region만 `logout all devices` tail이 길다 | 전체 글로벌 failover | 해당 region cursor catch-up + bounded degrade |
| edge decision cache | origin은 deny인데 일부 PoP가 allow를 계속 낸다 | TTL만 무작정 축소 | cache namespace epoch bump + synthetic probe |
| session/refresh cache tier | refresh는 막혔는데 access allow cache가 남아 있다 | access token 재발급만 반복 | family/subject scope invalidate와 old verdict drain |
| mobile/device fan-out worker | UI에는 logout로 보이는데 실제 push/device disconnect가 늦다 | bus 중복 resend만 늘림 | delivery ledger와 device ack gap repair |

중요한 점은 region lag와 cache lag를 같은 메트릭으로 뭉개지 않는 것이다.
버스 backlog가 0이어도 cache tier가 오래된 allow verdict를 들고 있으면 revocation incident는 끝난 것이 아니다.
특히 legacy/new token generation이 함께 살아 있는 기간에는 canonical ledger lag와 별도로 generation projection lag가 남을 수 있으므로, alias projection과 family quarantine fan-out을 포함한 설계는 [Canonical Revocation Plane Across Token Generations 설계](./canonical-revocation-plane-across-token-generations-design.md)로 이어서 보면 좋다.

### 2. redrive 전에 event 모델을 replay-safe로 만들어야 한다

re-drive가 안전하려면 revoke event 자체가 "한 번 더 적용해도 상태가 망가지지 않는" 형태여야 한다.

권장 envelope:

- `event_id`: 생산자 재시도 중복 제거용 유일 ID
- `scope_type`: `session`, `device`, `subject`, `refresh_family`
- `scope_id`
- `authz_epoch` 또는 `revoke_before`
- `authority_version`
- `source_region`
- `stream_offset`
- `occurred_at`
- `repair_reason` (`live`, `cursor_redrive`, `snapshot_delta`, `cache_sweep`)

여기서 핵심은 `event_id` 하나만으로 dedupe하지 않는 것이다.
운영 중에는 같은 revoke 의미가 다른 event ID로 재발행될 수 있기 때문이다.

실제 apply 기준은 대개 아래 둘의 조합이다.

- semantic key: `scope_type + scope_id + authz_epoch`
- transport key: `event_id` 또는 `stream_offset`

`event_id`는 전송 중복을 줄이고, `scope + epoch`는 의미 중복을 막는다.
둘 중 하나만 쓰면 replay 후 stale overwrite나 duplicate invalidate storm가 생기기 쉽다.

### 3. redrive는 offset catch-up, snapshot+delta, cache sweep을 분리한다

한 종류의 복구만 준비하면 retention gap이나 cache-only lag에서 막힌다.

| 패턴 | 언제 쓰는가 | 장점 | 주의점 |
|---|---|---|---|
| offset catch-up | region consumer가 멈췄지만 log retention 안에 있다 | 가장 싸고 causality를 보존한다 | backlog drain 중 live traffic 보호 필요 |
| snapshot + delta repair | consumer cursor가 retention 밖으로 밀렸거나 state store가 유실됐다 | 장기 lag를 회복할 수 있다 | snapshot 시점 이후 delta를 반드시 다시 붙여야 한다 |
| cache sweep / namespace epoch bump | event는 받았지만 cache tier만 invalidate를 놓쳤다 | 빠르게 stale verdict를 끊는다 | hit ratio 급락과 cold start를 감수해야 한다 |
| route-scoped degrade | high-risk route만 즉시 stronger check가 필요하다 | 전체 서비스 blast radius를 줄인다 | origin introspection capacity를 미리 예약해야 한다 |

권장 runbook은 보통 아래 흐름이다.

1. lagging region/tier를 식별한다.
2. high-risk route를 `direct introspection` 또는 shorter TTL로 일시 승격한다.
3. retention이 남아 있으면 cursor redrive를 수행한다.
4. retention이 끊겼으면 snapshot+delta repair로 전환한다.
5. cache tier가 따로 뒤처졌으면 namespace epoch bump나 scoped sweep을 건다.
6. synthetic revoke probe가 회복될 때까지 cleanup과 rollback window 종료를 보류한다.

즉 redrive는 메시지를 더 많이 보내는 행위가 아니라,
**어느 층을 어떤 repair primitive로 복구할지 선택하는 절차**여야 한다.

### 4. dedupe는 event 중복보다 "오래된 revoke가 새 상태를 덮지 못하게" 하는 데 초점을 둔다

복구 중 가장 흔한 사고는 duplicate deny보다 stale allow 재오염이다.

예를 들어:

- region A는 `subject_epoch=18`을 이미 적용했다
- 늦게 따라온 cache sweep이 `subject_epoch=17` 기준 verdict를 다시 쓴다
- 결과적으로 redrive 뒤에 오히려 allow tail이 부활한다

이를 막으려면 consumer/state tier가 다음 규칙을 공유해야 한다.

1. apply는 항상 `max(epoch)` 기반이다.
2. cache key에는 `authz_epoch` 또는 `revoke_before`를 포함한다.
3. invalidate receipt에도 `scope + epoch`를 남겨 older sweep이 newer state를 덮지 못하게 한다.
4. redrive worker는 subject/device/family 단위로 coalesce해 invalidate storm를 줄인다.

```pseudo
function applyRevoke(event):
  key = (event.scopeType, event.scopeId)
  state = revokeLedger.get(key)

  if state.maxEpoch > event.authzEpoch:
    return drop("older_than_applied_state")
  if state.maxEpoch == event.authzEpoch and state.lastEventId == event.eventId:
    return drop("duplicate_transport_event")

  invalidateCaches(key, minEpoch=event.authzEpoch)
  revokeLedger.put(
    key=key,
    maxEpoch=max(state.maxEpoch, event.authzEpoch),
    lastEventId=event.eventId,
    lastOffset=max(state.lastOffset, event.streamOffset)
  )
  return applied()
```

핵심은 dedupe store가 "이 이벤트를 봤는가"만 기억하는 것이 아니라,
**이 scope에 대해 어디까지의 revoke truth를 이미 적용했는가**를 기억해야 한다는 점이다.

### 5. observability는 backlog보다 stale allow를 직접 보여줘야 한다

revoke incident는 broker lag만 보면 과소평가되기 쉽다.
실제로 필요한 것은 "사용자 관점에서 revoke가 아직 안 닫힌 곳이 어디인가"를 보여주는 관측이다.

권장 지표:

- `revoke_bus_consumer_lag_seconds{region,tier}`
- `revoke_apply_backlog{region,tier}`
- `revoke_redrive_inflight{region,repair_type}`
- `revoke_duplicate_drop_total{region,tier,reason}`
- `decision_divergence_total{edge_region,origin_region,reason}`
- `stale_allow_shadow_ratio{region,route_class}`
- `forced_logout_probe_p95_seconds{region,tier}`
- `cache_namespace_epoch_skew{region,cache_tier}`
- `revoke_tail_over_slo_total{region,scope_type}`

특히 synthetic probe가 중요하다.
예를 들어 region마다 아래 시나리오를 주기적으로 강제로 발생시킨다.

- test subject 생성
- access token 발급
- `logout all devices` 실행
- edge, origin, refresh path, cache tier별로 deny 전환 시점 측정

이 probe가 없으면 "consumer lag는 회복됐는데 특정 edge tier만 오래된 allow를 낸다"를 놓치기 쉽다.

### 6. recovery gate를 traffic policy와 함께 둔다

복구 중에는 관측만으로는 부족하고, route별 완화 정책을 같이 걸어야 한다.

| 상태 | traffic policy | recovery action | release gate |
|---|---|---|---|
| `suspected_lag` | high-risk route를 shorter TTL 또는 origin confirm으로 승격 | lagging tier 식별 | probe와 divergence 원인 확정 |
| `active_redrive` | lagging region만 bounded degrade | cursor replay 또는 snapshot+delta 수행 | backlog 감소, duplicate storm 없음 |
| `cache_sweep` | cache miss budget 확대, rate limit 보호 | namespace epoch bump 또는 scoped invalidate | stale allow shadow 감소 |
| `verification_soak` | 일부 direct check 유지 | synthetic logout/deprovision 반복 | probe p95/p99가 SLO 안 |
| `recovered` | 임시 degrade 해제 | cleanup clock 재개 | resend queue 0, tail alert 0 |

복구가 끝났다고 판단하는 기준은 `consumer lag == 0`이 아니다.
적어도 다음 세 가지가 동시에 닫혀야 한다.

- backlog drain 완료
- stale allow shadow ratio 정상화
- synthetic revoke tail 정상화

### 7. region isolation이 retention 밖으로 넘어가면 snapshot authority가 필요하다

어떤 region은 장시간 고립되어 durable log retention을 넘길 수 있다.
이때 단순 redrive는 불가능하고 snapshot authority가 필요하다.

권장 방식:

- canonical revoke state를 authoritative store에서 scope별 snapshot으로 뽑는다
- lagging region은 local ledger를 snapshot 기준으로 fast-forward한다
- snapshot 시점 이후 이벤트는 delta replay로 붙인다
- snapshot 완료 전에는 high-risk route를 local cache verdict만으로 allow하지 않는다

여기서 중요한 것은 snapshot이 "세션 전체 dump"가 아니라
**revocation 판단에 필요한 최소 state**여야 한다는 점이다.

예:

- `subject_epoch`
- `device_epoch`
- `refresh_family_revoked_at`
- `session_tombstone_until`
- `snapshot_version`

그래야 region recovery가 빠르고, dedupe 기준도 단순해진다.

## 실전 시나리오

### 시나리오 1: APAC revoke consumer가 deploy 중 25분 멈췄다

문제:

- APAC edge만 `logout all devices` tail이 길고, origin introspection은 이미 deny다

해결:

- APAC high-risk route만 direct introspection fallback을 켠다
- APAC consumer cursor를 offset catch-up으로 redrive한다
- `stale_allow_shadow_ratio{region=\"apac\"}`와 forced logout synthetic probe로 회복을 확인한다

### 시나리오 2: 글로벌 bus는 정상인데 edge L2 cache만 invalidate를 놓쳤다

문제:

- consumer lag는 0인데 특정 PoP만 allow verdict를 오래 유지한다

해결:

- event replay보다 cache namespace epoch bump를 우선 적용한다
- scope가 좁다면 subject/device/family targeted sweep으로 cold start를 줄인다
- `cache_namespace_epoch_skew`와 `decision_divergence_total`로 효과를 본다

### 시나리오 3: 한 region이 장시간 분리돼 retention을 넘겼다

문제:

- reconnect 이후 old cursor로는 gap를 메울 수 없다

해결:

- canonical revoke snapshot을 내려 local ledger를 fast-forward한다
- snapshot 이후 delta만 replay한다
- verification soak 동안은 logout/deprovision probe를 반복하고 cleanup을 미룬다

## 코드로 보기

```pseudo
function recoverLaggingRegion(region):
  if metrics.consumerLag(region) <= sloLag and metrics.staleAllowRatio(region) == 0:
    return healthy()

  trafficPolicy.enableBoundedDegrade(region, highRiskRoutes)

  if log.hasRetentionFor(region.cursor):
    redrive.replayFromOffset(region.cursor)
  else:
    snapshot = authority.exportRevocationSnapshot(region)
    repair.fastForward(region, snapshot)
    redrive.replayFromTime(snapshot.generatedAt)

  if metrics.cacheEpochSkew(region) > 0:
    cache.bumpNamespaceEpoch(region)

  verifier.runSyntheticLogoutProbe(region)
  return waitFor(
    metrics.consumerLag(region) == 0 &&
    metrics.staleAllowRatio(region) == 0 &&
    probes.logoutTail(region) < revokeSlo
  )
```

```yaml
revocation_recovery:
  slo:
    consumer_lag_sec: 15
    forced_logout_tail_sec: 30
  degrade_policy:
    direct_check_routes: [admin_write, payout_approve, password_change]
    fallback_timeout_ms: 40
  repair_modes:
    within_retention: cursor_redrive
    beyond_retention: snapshot_delta
    cache_only_gap: namespace_epoch_bump
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| per-event replay only | 구조가 단순하다 | retention gap와 cache-only lag에 약하다 | 짧은 지연만 다루는 시스템 |
| snapshot + delta repair | 장기 lag도 복구 가능하다 | snapshot authority 관리가 필요하다 | region isolation 가능성이 큰 환경 |
| aggressive global degrade | stale allow를 빨리 줄인다 | origin 비용과 latency가 급증한다 | 보안 민감 route가 많을 때 |
| scoped degrade + synthetic verify | blast radius를 줄인다 | 제어 plane과 probe 설계가 필요하다 | multi-region auth/runtime |
| event-id dedupe only | 구현이 쉽다 | semantic duplicate와 stale overwrite를 못 막는다 | 권장하지 않음 |

핵심은 regional lag recovery가 "누락된 이벤트를 다시 보내기"가 아니라
**single revoke truth를 유지한 채 lagging tier를 repair하고, stale allow tail이 실제로 닫혔는지 검증하는 운영 설계**라는 점이다.

## 꼬리질문

> Q: revoke bus lag가 보이면 TTL을 짧게 줄이면 끝나지 않나요?
> 의도: cache TTL 완화와 repair 차이 이해 확인
> 핵심: TTL 축소는 tail을 줄일 수 있지만 이미 뒤처진 consumer cursor나 cache epoch skew를 복구하지는 못한다.

> Q: redrive dedupe는 event ID 하나면 충분하지 않나요?
> 의도: transport 중복과 semantic 중복 차이 이해 확인
> 핵심: 아니다. 동일 revoke 의미가 다른 event ID로 재발행될 수 있으므로 scope + epoch 기준이 필요하다.

> Q: region lag recovery가 끝났는지는 무엇으로 확인하나요?
> 의도: backlog 지표와 사용자 관점 지표 구분 확인
> 핵심: consumer lag뿐 아니라 stale allow shadow ratio와 synthetic logout tail이 함께 정상화돼야 한다.

> Q: retention을 넘긴 region은 왜 전체 세션을 다시 sync하지 않고 revoke snapshot만 복구하나요?
> 의도: 최소 복구 상태와 복구 속도 trade-off 이해 확인
> 핵심: regional lag incident의 핵심은 revoke truth 복원이지 세션 전체 재구성이 아니기 때문이다.

## 한 줄 정리

Revocation bus regional lag recovery 설계는 lagging region이나 cache tier를 replay-safe revoke ledger, scope/epoch dedupe, lag-aware degrade, synthetic verification으로 복구해 stale allow long tail을 닫는 운영 설계다.
