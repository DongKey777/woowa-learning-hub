---
schema_version: 3
title: Session Store / Claim-Version Cutover 설계
concept_id: system-design/session-store-claim-version-cutover-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- session store migration
- claim version cutover
- claim schema rollout
- auth claim migration
aliases:
- session store migration
- claim version cutover
- claim schema rollout
- auth claim migration
- session authority transfer
- claim translation bridge
- token validator overlap
- revocation propagation
- revoke before epoch
- refresh family revoke
- logout tail
- regional revoke lag recovery
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/session-store-design-at-scale.md
- contents/system-design/database-security-identity-bridge-cutover-design.md
- contents/system-design/traffic-shadowing-progressive-cutover-design.md
- contents/system-design/dual-read-comparison-verification-platform-design.md
- contents/system-design/edge-verifier-claim-skew-fallback-design.md
- contents/system-design/verifier-overlap-hard-reject-retirement-gates-design.md
- contents/system-design/refresh-family-rotation-cutover-design.md
- contents/system-design/canonical-revocation-plane-across-token-generations-design.md
- contents/system-design/refresh-reauth-escalation-matrix-design.md
- contents/system-design/revocation-bus-regional-lag-recovery-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Session Store / Claim-Version Cutover 설계 설계 핵심을 설명해줘
- session store migration가 왜 필요한지 알려줘
- Session Store / Claim-Version Cutover 설계 실무 트레이드오프는 뭐야?
- session store migration 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Session Store / Claim-Version Cutover 설계를 다루는 deep_dive 문서다. session store migration과 claim schema/version rollout 설계는 세션 authority 이전, claim semantic 전환, revoke propagation, cleanup 시계를 하나의 cutover matrix로 묶어 old store는 내려갔는데 old claim이 남거나 new claim은 발급됐는데 revoke tail이 따라오지 않는 반쪽 전환을 막는 운영 설계다. 검색 질의가 session store migration, claim version cutover, claim schema rollout, auth claim migration처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Session Store / Claim-Version Cutover 설계

> 한 줄 요약: session store migration과 claim schema/version rollout 설계는 세션 authority 이전, claim semantic 전환, revoke propagation, cleanup 시계를 하나의 cutover matrix로 묶어 old store는 내려갔는데 old claim이 남거나 new claim은 발급됐는데 revoke tail이 따라오지 않는 반쪽 전환을 막는 운영 설계다.

> 문서 역할: 이 문서는 [Session Store Design at Scale](./session-store-design-at-scale.md)의 세션 일관성 문제와 [Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md)의 authority transfer 문제 사이를 메우는 focused deep dive다.

retrieval-anchor-keywords: session store migration, claim version cutover, claim schema rollout, auth claim migration, session authority transfer, claim translation bridge, token validator overlap, revocation propagation, revoke before epoch, refresh family revoke, logout tail, regional revoke lag recovery, revoke redrive, cache invalidation replay, deprecated claim last seen, cleanup timing, translator retirement, translator cleanup example, deprecated claim soak window, revoke tail soak complete, legacy claim dark retirement, session translator decommission, rollback window, session cutover matrix, identity cutover, tenant scope version, refresh family migration, forced refresh reissue, mixed-version auth rollout, replay containment during rotation, edge verifier claim skew, unknown claim fallback, origin introspection fallback, verifier overlap end threshold, legacy parser hard reject threshold, unknown claim silence window, parser dark observe, unexpected legacy claim, overlap exit floor, cleanup evidence, retirement evidence, scim reconciliation close, decision log join key, audit hold evidence, deprovision proof, session auth gate path, verification ladder, read parity gate, revoke propagation parity, auth shadow exit criteria, shared promotion path, shadow route verification, session auth promotion path, read parity auth parity shared cohort, canonical revocation plane, token generation coexistence, alias projection

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Session Store Design at Scale](./session-store-design-at-scale.md)
> - [Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md)
> - [Dual-Read Comparison / Verification Platform 설계](./dual-read-comparison-verification-platform-design.md)
> - [Edge Verifier Claim-Skew Fallback 설계](./edge-verifier-claim-skew-fallback-design.md)
> - [Verifier Overlap Hard-Reject Retirement Gates 설계](./verifier-overlap-hard-reject-retirement-gates-design.md)
> - [Refresh-Family Rotation Cutover 설계](./refresh-family-rotation-cutover-design.md)
> - [Canonical Revocation Plane Across Token Generations 설계](./canonical-revocation-plane-across-token-generations-design.md)
> - [Refresh Reauth Escalation Matrix 설계](./refresh-reauth-escalation-matrix-design.md)
> - [Revocation Bus Regional Lag Recovery 설계](./revocation-bus-regional-lag-recovery-design.md)
> - [Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md)
> - [Capability Negotiation / Feature Gating 설계](./capability-negotiation-feature-gating-design.md)
> - [Capability Sunset Gate Matrix 설계](./capability-sunset-gate-matrix-design.md)
> - [Cleanup Point-of-No-Return 설계](./cleanup-point-of-no-return-design.md)
> - [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md)
> - [Adapter Retirement / Compatibility Bridge Decommission 설계](./adapter-retirement-compatibility-bridge-decommission-design.md)
> - [Write-Freeze Rollback Window 설계](./write-freeze-rollback-window-design.md)
> - [Protocol Version Skew / Compatibility 설계](./protocol-version-skew-compatibility-design.md)
> - [Security: Session Revocation at Scale](../security/session-revocation-at-scale.md)
> - [Security: Revocation Propagation Lag / Debugging](../security/revocation-propagation-lag-debugging.md)
> - [Security: SCIM Drift / Reconciliation](../security/scim-drift-reconciliation.md)
> - [Security: JWT / JWKS Outage Recovery / Failover Drills](../security/jwt-jwks-outage-recovery-failover-drills.md)
> - [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)
> - [Security: AuthZ Decision Logging Design](../security/authz-decision-logging-design.md)
> - [Security: Audit Logging for Auth / AuthZ Traceability](../security/audit-logging-auth-authz-traceability.md)
> - [Signed Cookies / Server Sessions / JWT Tradeoffs](../security/signed-cookies-server-sessions-jwt-tradeoffs.md)

## 핵심 개념

session store migration과 claim version rollout은 별도 프로젝트처럼 보이지만,
실제로는 같은 인증 상태를 두 개의 다른 층에서 옮기는 작업이다.

- session store는 "이 세션이 아직 유효한가"를 저장한다
- claim schema/version은 "이 토큰을 verifier가 어떻게 해석하는가"를 결정한다
- revocation propagation은 "무효화가 언제 어디까지 도달했는가"를 결정한다
- cleanup timing은 "언제부터 rollback 대신 correction만 가능한가"를 결정한다

이 네 시계가 따로 돌면 다음 같은 반쪽 cutover가 생긴다.

- 새 store는 authoritative인데 edge verifier는 old claim semantic으로 allow를 낸다
- 새 claim은 발급되는데 old session cache가 revoke를 늦게 받아 access tail이 남는다
- shadow compare는 green인데 old refresh family가 아직 살아 있어 cleanup 이후에만 문제가 드러난다

즉 이 주제의 핵심은 **session authority, claim meaning, revoke fan-out, cleanup boundary를 하나의 cutover unit으로 묶는 것**이다.

## 깊이 들어가기

### 1. 실제로 맞춰야 하는 것은 네 개의 시계다

| 시계 | 질문 | 늦으면 생기는 문제 | 빨라도 생기는 문제 |
|---|---|---|---|
| session authority clock | 어느 store가 session truth인가 | dual truth, stale lookup, inconsistent refresh | new store만 남고 old verifier가 session miss |
| claim semantic clock | verifier가 어떤 claim meaning을 이해하는가 | old/new semantic divergence, tenant scope bug | old client/verifier reject 급증 |
| revocation clock | revoke signal이 edge/cache/device까지 언제 닿는가 | logout tail, deprovision tail, zombie refresh | 과도한 deny, fallback storm |
| cleanup clock | old parser/store/bridge를 언제 지울 수 있는가 | bridge cost와 운영 복잡도 장기화 | rollback 불가, hidden long tail 폭발 |

실전에서는 cutover 완료 시각보다 각 시계의 종료 조건이 더 중요하다.
"새 store로 로그인 성공"은 첫 번째 시계만 닫은 것일 수 있다.

### 2. canonical truth를 한 군데로 모아야 한다

가장 위험한 설계는 old/new store가 각각 revoke counter와 refresh truth를 들고 있는 상태다.
이 경우 claim version rollout과 store migration이 겹치면 무엇이 authoritative인지 설명하기 어려워진다.

권장 원칙은 다음과 같다.

- 세션 조회 경로는 여러 개여도 revoke epoch와 refresh family truth는 하나만 둔다
- claim translator는 syntax만 바꾸고 security semantic은 바꾸지 않는다
- 새 claim이 추가하는 필드도 결국 canonical internal model로 역직렬화돼야 한다
- refresh token 재발급 시점부터는 가능한 한 새 store/new claim으로 수렴시킨다

대표 필드는 아래처럼 생각할 수 있다.

- `session_id`
- `subject_id`
- `store_generation`
- `claim_schema_version`
- `authz_epoch`
- `revoke_before`
- `refresh_family_id`
- `tenant_scope_version`

핵심은 토큰 안의 버전 필드보다, verifier가 최종적으로 비교하는 **canonical revocation state**가 더 중요하다는 점이다.

### 3. 안전한 전환은 dual-accept이되 single-issue, single-revoke여야 한다

권장 phase는 보통 다음과 같다.

#### Phase A. compatibility window

- old/new verifier 모두 old claim과 new claim을 읽을 수 있게 둔다
- claim translator는 old claim을 canonical model로 바꿔 준다
- revoke source는 단일 epoch service 또는 단일 session authority에서만 올린다
- old/new store를 동시에 write하지 말고, refresh 또는 migration worker를 통해 점진 수렴시킨다

중요한 점은 "둘 다 읽을 수 있음"과 "둘 다 진실원임"이 전혀 다르다는 것이다.

#### Phase B. shadow validation

- old parser + old store decision과 new parser + new store decision을 나란히 비교한다
- `missing_claim_field`, `tenant_scope_mismatch`, `session_not_found_delta`, `revoke_state_delta`를 수집한다
- 새 claim을 아직 강제하지 말고, divergence 원인부터 줄인다

이 구간에서 보는 핵심 숫자:

- claim parser fallback ratio
- validator decision divergence
- old/new session lookup mismatch
- revoke propagation p95 / p99
- refresh reissue conversion ratio

#### Phase C. fenced issuance cutover

- 새 로그인과 새 refresh는 new store + new claim만 발급한다
- old session은 validate는 허용하되 가능한 빨리 refresh를 통해 새 세대로 옮긴다
- old store는 read-only drain 또는 tombstoned-but-restorable 상태로 남긴다
- rollback window 동안 old parser와 translator는 유지한다

이때부터 "새 발급은 하나"가 되어야 관측이 단순해진다.

#### Phase D. revocation soak

- forced logout, password reset, SCIM deprovision, device revoke를 일부러 발생시켜 tail을 측정한다
- edge cache invalidation, token validator cache eviction, refresh family revoke가 모두 같은 epoch를 보게 만든다
- `deprecated_claim_last_seen`, `legacy_store_hit`, `revocation_tail_gt_slo`가 감소 추세인지 본다

이 구간을 건너뛰면 login path는 성공해도 logout path가 늦게 무너진다.

#### Phase E. cleanup

- old claim parser hit가 0에 수렴하고
- old refresh family horizon이 지나고
- revoke propagation lag가 안정적으로 SLO 안이며
- rollback window가 닫힌 뒤에만
- old translator, old store read path, legacy cache key를 제거한다

cleanup은 "트래픽이 적어 보인다"가 아니라 **long-tail revoke와 refresh expiry가 모두 닫혔다**는 증거가 필요하다.

### 4. revocation propagation을 claim rollout과 따로 보면 사고가 난다

claim version이 바뀌면 verifier의 local cache key, edge enforcement path, refresh reissue 조건도 같이 바뀌기 쉽다.
그래서 revoke propagation을 단순 pub/sub fan-out 문제로만 보면 놓치는 것이 많다.

특히 함께 봐야 하는 경계는 아래와 같다.

| 경계 | 질문 | 잘못 설계했을 때 |
|---|---|---|
| session record vs token claim | 토큰 안 버전과 store 안 epoch가 어떻게 만나는가 | old claim이 새 revoke를 모름 |
| access token vs refresh family | access는 짧아도 refresh가 old semantic을 계속 재생산하는가 | old claim이 며칠씩 재발급됨 |
| region-local cache vs global revoke bus | 어느 시점에 local allow를 뒤집는가 | 특정 region만 logout tail이 길어짐 |
| edge verifier vs origin introspection | unknown claim version을 어디서 판정하는가 | edge reject 폭증 또는 origin fallback storm |

권장 패턴은 다음과 같다.

1. revoke는 `session_id` 단위뿐 아니라 `subject/device/family` 축을 함께 가진다.
2. verifier는 claim version이 달라도 canonical epoch 비교만큼은 동일하게 수행한다.
3. unknown new claim은 바로 hard reject하지 말고 overlap window 동안 origin introspection으로 보내 수습한다.
4. old claim을 받았더라도 `revoke_before`나 `authz_epoch` 비교는 same-code path로 태운다.

즉, revocation plane은 parser 바깥의 별도 경로가 아니라 **claim skew를 흡수하는 마지막 안전망**이어야 한다.
특히 한 region이나 cache tier만 뒤처졌을 때 revoke redrive, dedupe, synthetic probe를 어떻게 설계할지는 [Revocation Bus Regional Lag Recovery 설계](./revocation-bus-regional-lag-recovery-design.md)로 이어서 보면 좋다.

refresh family migration, forced reissue retry, mixed-version rollout 중 replay containment decision tree를 더 좁혀 보면 [Refresh-Family Rotation Cutover 설계](./refresh-family-rotation-cutover-design.md)로 바로 이어진다.
legacy/new token generation이 함께 남는 overlap window에서 canonical revoke truth, alias mapping, family quarantine fan-out을 어떻게 같은 plane으로 묶을지는 [Canonical Revocation Plane Across Token Generations 설계](./canonical-revocation-plane-across-token-generations-design.md)로 이어서 보면 된다.

### 5. cleanup 시계는 max TTL이 아니라 max residual horizon으로 계산한다

cleanup을 "새 버전 배포 후 24시간"처럼 정하면 거의 항상 너무 이르다.
실전에서는 아래 항목의 최댓값을 보는 편이 안전하다.

```text
cleanup_eligible_at =
  max(
    rollback_window_end,
    last_old_claim_seen + observation_window,
    last_old_refresh_family_expiry,
    revocation_lag_recovered_at + safety_buffer,
    audit_or_forensics_hold_end
  )
```

각 항목의 의미:

- `rollback_window_end`: donor store와 old parser를 유지해야 하는 최소 시점
- `last_old_claim_seen + observation_window`: long-tail caller를 다시 한 번 확인하는 구간
- `last_old_refresh_family_expiry`: old semantic이 재생산될 수 있는 마지막 시점
- `revocation_lag_recovered_at + safety_buffer`: logout/deprovision tail이 실제로 닫혔는지 확인하는 버퍼
- `audit_or_forensics_hold_end`: 장애 조사나 규제 보존 때문에 old evidence를 남겨야 하는 시점

즉 cleanup timing은 max TTL보다 보수적이어야 하며, 특히 refresh family와 revoke tail이 둘 다 닫히기 전에는 old bridge를 지우면 안 된다.

### 6. joint cutover gate를 표로 두면 운영 판단이 빨라진다

| gate | session/store evidence | claim/version evidence | revoke evidence | cleanup decision |
|---|---|---|---|---|
| pre-cutover readiness | new store hydration 완료, lookup mismatch 낮음 | translator/validator 배포 완료 | revoke bus healthy | cleanup disabled |
| shadow safety | old/new lookup divergence 0 근접 | parser fallback 낮음, semantic divergence 0 근접 | forced logout shadow pass | cleanup disabled |
| issuance cutover | new issue path only | new claim issue coverage 충분 | cache invalidation fan-out healthy | old parser/store retained |
| revocation soak | legacy store hit 감소 | deprecated claim last-seen 감소 | revoke lag SLO 안, tail 감소 | cleanup hold |
| retirement | old refresh horizon 종료 | legacy claim last-seen 0 | revoke lag stable, resend queue 0 | translator/store cleanup allowed |

이 표를 두면 "로그인은 다 된다" 같은 모호한 문장을 gate로 착각하지 않게 된다.

### 7. session/auth 승격은 같은 verification ladder를 따라야 한다

앞의 gate 표는 상태를 압축한 것이고, 실제 운영에서는 이를 계단처럼 읽어야 한다.
session store / claim-version cutover는 세션 문서처럼 보여도 read cutover와 auth bridge가 쓰는 검증 사다리를 그대로 공유한다.
즉 `read parity -> revoke parity -> auth shadow exit`는 따로 승인받는 세 개의 체크리스트가 아니라,
같은 cohort를 위로 올리는 하나의 promotion path다.

| ladder rung | 무엇을 증명하나 | 대표 signal | exit 기준 | 같이 볼 문서 |
|---|---|---|---|---|
| traffic shadow capture | 같은 route, gateway, auth plugin, session lookup 압력을 새 경로가 버티는가 | `shadow_path_error`, `session_lookup_shadow_timeout`, `legacy_claim_fallback_ratio` | shadow path saturation과 fallback storm 없이 실제 request mix를 재현 | [Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md) |
| read parity | old/new store와 translator가 같은 session/claim snapshot을 읽는가 | `session_not_found_delta`, `tenant_scope_mismatch`, `store_generation_read_skew`, `claim_translation_delta` | critical parity mismatch가 0이고 나머지 mismatch가 allowlisted skew로만 설명됨 | [Dual-Read Comparison / Verification Platform 설계](./dual-read-comparison-verification-platform-design.md) |
| revoke propagation parity | 같은 revoke epoch가 edge/cache/refresh path까지 같은 시간 예산 안에 도달하는가 | `revoke_visibility_delta_sec`, `revocation_tail_gt_slo`, `last_access_after_deprovision_sec_p99`, `revocation_resend_queue` | forced logout, password reset, SCIM deprovision probe가 모두 SLO 안에 수렴 | [Revocation Bus Regional Lag Recovery 설계](./revocation-bus-regional-lag-recovery-design.md) |
| auth shadow exit | 같은 request context에서 old/new policy와 verifier가 같은 allow/deny를 내는가 | `old_deny_new_allow`, `old_allow_new_deny`, `legacy_parser_reason_code`, `unknown_claim_origin_fallback` | high-risk divergence가 0이고 reason-code drift가 허용 범위 안 | [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md) |
| fenced issuance / soak | single-issue, revoke soak, cleanup hold가 같은 cohort에서 유지되는가 | `new_store_only_issue_coverage`, `deprecated_claim_last_seen`, `legacy_refresh_family_open`, `cleanup_enabled=false` | 위 네 rung가 모두 green인 동일 cohort만 single-issue로 승격 | [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md) |

중요한 점은 이 ladder의 join key를 처음부터 같게 두는 것이다.
`request_id`, `route_id`, `tenant_id`, `session_id`, `claim_schema_version`, `store_generation`, `subject_epoch`, `reconciliation_run_id`가 같은 축으로 남아야
"read parity는 green인데 revoke tail만 남았다"를 같은 승격 표본 안에서 설명할 수 있다.

이렇게 묶지 않으면 아래 같은 잘못된 승격이 생긴다.

- dual-read diff 0을 보고 issue cutover를 열었는데 forced logout probe는 아직 특정 region에서 stale allow를 낸다
- revoke lag SLO는 맞는데 shadow auth에서 `old_deny -> new_allow`가 tenant 경계 route에 남는다
- auth shadow는 green인데 shadow route에서만 origin fallback storm이 나서 실제 cutover 시 latency가 깨진다

따라서 session/auth gate의 exit 문장은 항상 하나여야 한다.
"같은 cohort에서 route shadow가 안정적이고, read parity가 맞고, revoke probe가 닫히고, auth shadow critical divergence가 0이므로 single-issue로 올리되 cleanup은 아직 hold한다."
이 문장으로 설명되지 않으면 아직 승격 ladder를 끝까지 오른 것이 아니다.

#### overlap 종료와 legacy parser hard-reject를 여는 기본 문턱

중요한 것은 `verifier overlap end`와 `legacy parser hard-reject`를 같은 사건으로 취급하지 않는 것이다.
전자는 dual-accept와 origin fallback을 normal path에서 내리는 문턱이고,
후자는 legacy claim을 live path에서 incident bucket으로 올리는 문턱이다.
둘을 같은 change set으로 묶으면 overlap을 닫자마자 hidden caller를 강제 outage로 찾게 된다.

| 단계 | 기본 floor(예시) | 이 floor가 답하는 질문 | 통과 뒤 액션 |
|---|---|---|---|
| verifier overlap end | verifier class × region × route-risk-class 기준 `unknown_claim_rate < 0.1%`, `verifier_divergence_total = 0`, `fallback_queue_drop_total = 0`, organic `legacy_parser_last_seen_silence >= 30m` | dual-accept와 origin fallback을 normal path에서 내려도 되는가 | live request는 new parser를 primary로 쓰고 old parser는 `dark-observe`/synthetic-only로 내린다 |
| legacy parser hard-reject | overlap-end floor 유지 + `unexpected_legacy_claim = 0` for `24h`, organic `deprecated_claim_last_seen` silence `>= 72h`, `legacy_refresh_family_open = false`, `revocation_tail_gt_slo = 0` for `48h`, bridge retirement packet `overall_decision = approve-candidate` | legacy claim을 바로 reject해도 revoke/refresh/access tail이 다시 열리지 않는가 | live path hard-reject, allowlist는 emergency/synthetic-only로 축소, code deletion은 별도 wave로 분리한다 |

이 문턱은 global average가 아니라 **가장 느린 verifier class × region × route-risk-class 조합**으로 읽어야 한다.
한 PoP나 background caller만 legacy parser를 계속 쓰고 있으면 overlap은 끝난 것이 아니다.

실전에서는 아래 두 시각을 별도 계산해 두는 편이 안전하다.

```text
verifier_overlap_end_at =
  max(
    last_unknown_claim_rate_above_0_1pct_at + 30m,
    last_verifier_divergence_at + 30m,
    last_fallback_queue_drop_at + 30m,
    last_organic_legacy_parser_hit_at + 30m
  )
```

```text
legacy_parser_hard_reject_at =
  max(
    verifier_overlap_end_at + 24h,
    last_deprecated_claim_seen_at + 72h,
    last_revocation_tail_gt_slo_at + 48h,
    last_access_after_deprovision_slo_breach_at + 48h,
    rollback_window_end,
    last_background_legacy_hit_at + 1 full job cadence
  )
```

이 값이 중요한 이유는 다음과 같다.

- `30m`은 edge/parser/JWKS fan-out이 수렴한 뒤 overlap normal path를 내릴 수 있는 최소 floor다.
- `24h dark-observe`는 peak/off-peak가 한 번씩 지나가며 hidden foreground caller를 드러내는 최소 주기다.
- `72h deprecated-claim silence`는 access token TTL이 아니라 stale client, support tooling, low-frequency caller를 잡기 위한 live-traffic floor다.
- `48h revoke/deprovision stability`는 logout만이 아니라 password reset, SCIM close, device revoke tail까지 다시 열리지 않는지 보는 soak이다.
- background/replay/support path는 `1 full job cadence`를 별도 항으로 둬야 한다. 하루에 한 번만 도는 job이면 `24h`가 아니라 그 cadence가 hard-reject 문턱을 결정한다.

즉 안전한 순서는 항상 다음과 같다.

1. overlap-end floor 충족
2. old parser를 `dark-observe`로 전환
3. hard-reject floor 충족
4. live path hard-reject
5. point-of-no-return 승인 뒤 parser code/config 삭제

이 순서를 지키면 verifier overlap 종료와 parser retirement를 같은 날 억지로 끝내지 않아도 되고,
legacy claim이 다시 나타났을 때도 cleanup boundary를 태우지 않은 채 원인을 되짚을 수 있다.

### 8. cleanup / retirement evidence는 SCIM close와 decision evidence를 같이 닫아야 한다

`deprecated_claim_last_seen = 0`만으로는 bridge retirement를 시작하기 부족하다.
session/claim cutover는 token parser와 session store를 지우는 작업이므로,
SCIM reconciliation이 정말 닫혔는지, runtime allow/deny가 새 semantic으로 수렴했는지,
그리고 그 사실을 나중에도 입증할 수 있는지까지 같이 남겨야 한다.

| 증거 축 | 무엇을 확인하나 | 빠지면 생기는 오판 | 같이 볼 문서 |
|---|---|---|---|
| lifecycle reconciliation | `reconciliation_run_id`가 닫혔고 orphan membership/support grant가 정리됐는가, `last_access_after_deprovision`이 SLO 안으로 내려왔는가 | row diff는 0인데 old refresh/session tail이 남은 상태를 cleanup-safe로 오판 | [SCIM Drift / Reconciliation](../security/scim-drift-reconciliation.md), [SCIM Deprovisioning / Session / AuthZ Consistency](../security/scim-deprovisioning-session-authz-consistency.md) |
| decision parity evidence | `shadow_decision_divergence`, `old_deny_new_allow`, `legacy_parser_reason_code`가 0 또는 허용 범위 안으로 수렴했는가 | DB/backfill은 green인데 authz semantic만 계속 흔들리는 반쪽 cutover를 놓침 | [Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md), [AuthZ Decision Logging Design](../security/authz-decision-logging-design.md) |
| forensic / audit hold | `request_id`, `session_id`, `claim_schema_version`, `store_generation`, `directory_event_id`, `reconciliation_run_id`로 lifecycle event와 decision/audit event를 다시 조인할 수 있는가 | cleanup 후 tail 원인이 stale session인지 stale policy인지 incomplete revoke인지 증명 불가 | [Audit Logging for Auth / AuthZ Traceability](../security/audit-logging-auth-authz-traceability.md), [AuthZ Decision Logging Design](../security/authz-decision-logging-design.md) |

즉 retirement gate는 단순 "old claim이 안 보인다"가 아니라 아래 세 문장을 동시에 만족해야 닫힌다.

- SCIM drift repair가 종료돼 더 이상 old membership/session을 재생산하지 않는다.
- runtime decision이 새 claim semantic과 revoke truth에 수렴했다.
- 남아 있는 incident tail을 audit/decision evidence로 다시 설명할 수 있다.

이때 decision log는 "왜 allow/deny가 났는가"를 설명하는 증거고,
audit log는 "누가 어느 session/claim으로 어떤 자원에 닿았는가"를 설명하는 증거다.
둘 중 하나라도 join key 없이 남기면 translator/store cleanup 뒤에는 tail 원인을 재구성하기 어려워진다.

### 9. worked example: revoke-tail / deprecated-claim soak이 끝난 뒤 translator를 retire하는 순서

가장 자주 생기는 실수는 `deprecated_claim_last_seen = 0`과 revoke tail 안정화가 확인된 직후
translator 코드를 바로 지우는 것이다.
soak complete는 "이제 cleanup wave를 시작해도 된다"는 뜻이지,
runtime disable과 code deletion을 같은 change window에 합쳐도 된다는 뜻이 아니다.

예를 들어 `claim_schema_version=v1 -> v2`, `store_generation=3` 전환이 끝난 상태를 보자.

| 체크 항목 | 예시 값 | 왜 중요하나 | 하나라도 어긋나면 |
|---|---|---|---|
| `deprecated_claim_last_seen` | `2026-04-14T09:10:00Z` | legacy claim이 마지막으로 관측된 시각 | silence window를 다시 계산한다 |
| `required_claim_silence_window` | `72h` 충족 (`now=2026-04-17T10:00:00Z`) | hidden caller가 더 없는지 본다 | cleanup hold 유지 |
| `session_revoke_tail_p99_sec` | `9` | revoke tail이 access/session plane에서 안정적인지 본다 | revoke path 먼저 복구 |
| `revocation_tail_gt_slo` | 지난 `48h` 동안 `0` | 장꼬리가 실제로 사라졌는지 본다 | resend/redrive를 다시 점검 |
| `legacy_refresh_family_open` | `false` | old semantic이 다시 재생산되지 않는지 본다 | refresh horizon 종료까지 대기 |
| `legacy_store_hit` | 지난 `48h` 동안 `0` | old store read path가 정말 비었는지 본다 | translator보다 read path drain이 먼저 |
| `last_access_after_deprovision_sec_p99` | `6` | revoke tail뿐 아니라 deprovision tail도 닫혔는지 본다 | SCIM/session close를 다시 본다 |

이 상태라면 cleanup을 아래처럼 세 wave로 나누는 편이 안전하다.

#### Wave 1. approval packet 고정, 하지만 cleanup은 아직 열지 않는다

- [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md) 형식으로 observation window와 join key를 먼저 고정한다.
- `cleanup_enabled=false`, `point_of_no_return_ready=false`로 둔 채 `translator_retirement_candidate=true`만 올린다.
- old claim을 다시 발급할 수 있는 issuer flag, emergency reissue flag, legacy refresh allowlist를 모두 닫는다.

```yaml
translator_retirement_packet:
  scope:
    claim_schema_version: v2
    store_generation: 3
  observation_window:
    started_at: 2026-04-14T10:00:00Z
    ended_at: 2026-04-17T10:00:00Z
    required_claim_silence_window: 72h
    required_revoke_stability_window: 48h
  security_tail:
    deprecated_claim_last_seen_at: 2026-04-14T09:10:00Z
    session_revoke_tail_p99_sec: 9
    revocation_tail_gt_slo: 0
    legacy_refresh_family_open: false
    legacy_store_hit: 0
    last_access_after_deprovision_sec_p99: 6
  approval:
    translator_retirement_candidate: true
    cleanup_enabled: false
    point_of_no_return_ready: false
```

핵심은 "조건이 좋아 보인다"를 바로 cleanup enable로 번역하지 않는 것이다.
승인 패킷은 ready여도 irreversible cleanup 권한은 아직 잠가 둔다.

#### Wave 2. translator를 live path에서 내리고 dark observe를 둔다

- old claim translator를 `accept path`에서 제거하고, 예상치 못한 `v1` claim은 자동 복구 대신 `unexpected_legacy_claim`으로 계측한다.
- origin introspection fallback은 전체 트래픽에 열어 두지 말고 synthetic probe나 emergency rollback handle에만 남긴다.
- [Adapter Retirement / Compatibility Bridge Decommission 설계](./adapter-retirement-compatibility-bridge-decommission-design.md)처럼 runtime disable과 code deletion을 분리한다.

이 wave의 목표는 "정말 아무도 translator를 안 쓰는가"를 확인하는 것이다.
예상 기준은 아래와 같다.

- `translator_invocation = 0`
- `unexpected_legacy_claim = 0`
- `origin_fallback_due_to_legacy_claim = 0`
- `revocation_resend_queue = 0`

여기서 하나라도 튀면 cleanup clock을 다시 연다.
특히 organic traffic에서 old claim이 한 번이라도 보이면 `deprecated_claim_last_seen`을 그 시각으로 리셋하고,
왜 issuer가 다시 old semantic을 만들었는지부터 추적해야 한다.

#### Wave 3. dark observe까지 0이면 그때 code/config를 지운다

dark observe window까지 unexpected hit가 0이면 그제야 다음을 제거한다.

- `translator_v1_to_canonical` 구현
- legacy claim parser와 validator allowlist
- legacy cache key namespace와 old store read fallback
- old claim을 위한 synthetic-only route가 아닌 일반 fallback config

이 시점에만 [Cleanup Point-of-No-Return 설계](./cleanup-point-of-no-return-design.md)의 관점에서
`point_of_no_return_ready=true`를 올리고 destructive cleanup change를 연다.
즉 순서는 항상 다음과 같다.

1. soak complete
2. approval packet 고정
3. runtime disable + dark observe
4. unexpected hit 0 확인
5. code/config deletion

이 순서를 지키면 "deprecated claim은 안 보였는데 hidden support tooling이 translator를 계속 썼다" 같은 사고를
code deletion 전에 잡을 수 있다.

## 실전 시나리오

### 시나리오 1: `tenant_scope_version` claim 추가와 session store 이전이 동시에 진행

문제:

- 새 verifier는 `tenant_scope_version`이 있어야 정확한 authz를 할 수 있는데 old refresh token은 이 필드 없이 계속 재발급된다

해결:

- old refresh family도 재발급 시 new claim으로 강제 승격한다
- old claim parser는 overlap window 동안만 유지한다
- `tenant_scope_version_missing`과 `legacy_refresh_reissue`를 동시에 줄이는 것을 gate로 둔다

### 시나리오 2: 비밀번호 변경 후 모든 기기 로그아웃 tail이 길다

문제:

- new store는 즉시 revoke됐지만 일부 edge cache가 old claim verdict를 오래 들고 있다

해결:

- `subject_epoch`와 `device_epoch`를 canonical source에서 올린다
- edge cache TTL을 access token TTL보다 짧게 잡는다
- forced logout synthetic traffic으로 region별 tail을 측정한다

### 시나리오 3: new claim issuance는 시작했지만 rollback이 필요하다

문제:

- new claim v2를 발급하기 시작한 뒤 verifier divergence가 발견됐다

해결:

- rollback window 동안 old parser와 read-only donor store를 유지한다
- 새 발급을 일시 중지하고 origin introspection fallback을 늘린다
- cleanup clock은 리셋하고 `last_old_claim_seen`을 다시 측정한다

## 코드로 보기

```pseudo
function validate(token, now):
  claim = translator.toCanonical(token)
  session = authority.lookup(claim.sessionId)

  if claim.version not in allowedVersions(now):
    return fallbackOrReject(claim)
  if claim.authzEpoch < revokeState.subjectEpoch(claim.subjectId):
    return deny("subject_revoked")
  if session.storeGeneration < currentStoreGeneration() and !session.readOnlyDrain:
    return deny("stale_session_authority")
  if session.refreshFamilyRevoked:
    return deny("refresh_family_revoked")
  return allow()
```

```yaml
session_claim_cutover:
  issuance:
    new_store_only: true
    accepted_claim_versions: [v1, v2]
  guardrails:
    validator_divergence: 0
    revoke_p99_ms: 30000
    deprecated_claim_last_seen_zero_for: 24h
    legacy_refresh_family_open: false
  cleanup:
    enabled: false
    reason: "revocation tail still observed"
```

핵심은 parser 호환성보다 **canonical revoke comparison과 cleanup hold 조건**이 더 중요하다는 점이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| old/new claim을 둘 다 즉시 hard reject/허용 없이 끊음 | 단순하다 | mixed fleet와 long-tail refresh에 취약하다 | 내부 caller만 있고 skew가 작을 때 |
| dual-accept + single-issue | 수렴 경로가 명확하다 | overlap 관리가 필요하다 | 대부분의 session/identity cutover |
| revoke를 store마다 별도 유지 | 구현이 쉬울 수 있다 | dual truth와 tail debugging이 어려워진다 | 권장하지 않음 |
| origin introspection fallback 적극 사용 | unknown claim version에 안전하다 | latency와 auth dependency가 커진다 | overlap window, incident fallback |
| cleanup을 max TTL보다 늦춤 | revoke tail을 흡수한다 | legacy bridge 비용이 남는다 | logout/deprovision 영향이 큰 시스템 |

핵심은 session store / claim-version cutover가 토큰 포맷 전환이나 cache 교체 문제가 아니라, **authority transfer와 revocation cleanup을 함께 닫는 운영 설계**라는 점이다.

## 꼬리질문

> Q: claim version rollout과 session store migration을 굳이 같이 보아야 하나요?
> 의도: parser 문제와 state authority 문제를 분리하지 않고 설명할 수 있는지 확인
> 핵심: verifier가 이해하는 semantic과 session truth가 어긋나면 로그인은 성공해도 revoke나 authz에서 늦게 장애가 나기 때문이다.

> Q: dual-accept 전략이면 왜 충분하지 않나요?
> 의도: compatibility와 authority를 구분하는지 확인
> 핵심: 읽기 호환만으로는 revoke truth와 refresh reissue truth가 하나로 수렴되지 않으면 long tail이 남는다.

> Q: cleanup은 access token TTL만 지나면 시작해도 되나요?
> 의도: cleanup timing 계산이 단순 TTL이 아님을 이해하는지 확인
> 핵심: 아니다. old refresh family, revoke lag, rollback window, audit hold가 모두 닫혀야 안전하다.

> Q: revocation propagation에서 가장 중요한 지표 하나만 고르라면 무엇인가요?
> 의도: 단일 metric fetish를 경계하는지 확인
> 핵심: 하나만 고르기보다 `decision divergence + revoke tail + deprecated claim last-seen`을 함께 봐야 한다. 어느 하나만 green이어도 반쪽 성공일 수 있다.

## 한 줄 정리

Session store / claim-version cutover 설계는 세션 저장소 이전, claim semantic rollout, revoke fan-out, cleanup boundary를 하나의 승격 절차로 묶어 인증 상태 전환의 long tail을 안전하게 닫는 운영 설계다.
