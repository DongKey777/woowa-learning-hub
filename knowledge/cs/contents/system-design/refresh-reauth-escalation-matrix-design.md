---
schema_version: 3
title: Refresh Reauth Escalation Matrix 설계
concept_id: system-design/refresh-reauth-escalation-matrix-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- refresh reauth escalation matrix
- mixed-version refresh migration
- silent refresh migration
- refresh step-up
aliases:
- refresh reauth escalation matrix
- mixed-version refresh migration
- silent refresh migration
- refresh step-up
- full reauthentication
- risk-gated reissue
- refresh assurance portability
- auth assurance carry-over
- auth_time migration
- acr amr migration
- refresh binding portability
- device-bound refresh migration
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/refresh-family-rotation-cutover-design.md
- contents/security/step-up-session-coherence-auth-assurance.md
- contents/system-design/refresh-exchange-idempotency-under-cutover-design.md
- contents/system-design/session-store-claim-version-cutover-design.md
- contents/system-design/edge-verifier-claim-skew-fallback-design.md
- contents/system-design/capability-sunset-gate-matrix-design.md
- contents/system-design/protocol-version-skew-compatibility-design.md
- contents/security/mfa-step-up-auth-design.md
- contents/security/refresh-token-rotation-reuse-detection.md
- contents/security/token-misuse-detection-replay-containment.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Refresh Reauth Escalation Matrix 설계 설계 핵심을 설명해줘
- refresh reauth escalation matrix가 왜 필요한지 알려줘
- Refresh Reauth Escalation Matrix 설계 실무 트레이드오프는 뭐야?
- refresh reauth escalation matrix 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Refresh Reauth Escalation Matrix 설계를 다루는 deep_dive 문서다. refresh reauth escalation matrix 설계는 mixed-version refresh migration 동안 "형식만 옮기면 되는지", "현재 세션이 더 강한 증거를 한 번 더 제출하면 되는지", "현재 세션 자체를 더는 믿으면 안 되는지"를 구분해 silent migration, step-up, full reauthentication을 서로 다른 증거 강도로 결정하는 운영 설계다. 검색 질의가 refresh reauth escalation matrix, mixed-version refresh migration, silent refresh migration, refresh step-up처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Refresh Reauth Escalation Matrix 설계

> 한 줄 요약: refresh reauth escalation matrix 설계는 mixed-version refresh migration 동안 "형식만 옮기면 되는지", "현재 세션이 더 강한 증거를 한 번 더 제출하면 되는지", "현재 세션 자체를 더는 믿으면 안 되는지"를 구분해 silent migration, step-up, full reauthentication을 서로 다른 증거 강도로 결정하는 운영 설계다.
>
> 문서 역할: 이 문서는 [Refresh-Family Rotation Cutover 설계](./refresh-family-rotation-cutover-design.md)의 forced reissue state machine과 [Security: Step-Up Session Coherence / Auth Assurance](../security/step-up-session-coherence-auth-assurance.md)의 assurance coherence를 연결해, mixed-version refresh migration에서 escalation을 언제 어느 단계로 올려야 하는지 정리하는 focused deep dive다.

retrieval-anchor-keywords: refresh reauth escalation matrix, mixed-version refresh migration, silent refresh migration, refresh step-up, full reauthentication, risk-gated reissue, refresh assurance portability, auth assurance carry-over, auth_time migration, acr amr migration, refresh binding portability, device-bound refresh migration, refresh lineage alias miss, refresh family quarantine, replay-triggered reauth, session continuity proof, refresh migration prompt budget, silent vs step-up vs reauth, refresh migration escalation policy, refresh exchange idempotency, duplicate response replay, same-context duplicate

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Refresh-Family Rotation Cutover 설계](./refresh-family-rotation-cutover-design.md)
> - [Refresh Exchange Idempotency Under Cutover 설계](./refresh-exchange-idempotency-under-cutover-design.md)
> - [Session Store / Claim-Version Cutover 설계](./session-store-claim-version-cutover-design.md)
> - [Edge Verifier Claim-Skew Fallback 설계](./edge-verifier-claim-skew-fallback-design.md)
> - [Capability Sunset Gate Matrix 설계](./capability-sunset-gate-matrix-design.md)
> - [Protocol Version Skew / Compatibility 설계](./protocol-version-skew-compatibility-design.md)
> - [Security: MFA / Step-Up Auth Design](../security/mfa-step-up-auth-design.md)
> - [Security: Step-Up Session Coherence / Auth Assurance](../security/step-up-session-coherence-auth-assurance.md)
> - [Security: Refresh Token Rotation / Reuse Detection](../security/refresh-token-rotation-reuse-detection.md)
> - [Security: Token Misuse Detection / Replay Containment](../security/token-misuse-detection-replay-containment.md)
> - [Security: Session Revocation at Scale](../security/session-revocation-at-scale.md)

## 이 문서 다음에 보면 좋은 설계

- refresh family alias, forced reissue, replay containment의 canonical lineage를 먼저 다시 잡으려면 [Refresh-Family Rotation Cutover 설계](./refresh-family-rotation-cutover-design.md)부터 이어서 보면 된다.
- benign retry와 실제 replay를 exchange contract로 어떻게 가르는지는 [Refresh Exchange Idempotency Under Cutover 설계](./refresh-exchange-idempotency-under-cutover-design.md)로 좁혀 보면 된다.
- step-up 결과를 base session과 어떻게 분리해 들고 가는지는 [Security: Step-Up Session Coherence / Auth Assurance](../security/step-up-session-coherence-auth-assurance.md)로 내려가면 된다.
- verifier overlap이나 unknown claim fallback이 refresh escalation과 어떻게 섞이는지는 [Edge Verifier Claim-Skew Fallback 설계](./edge-verifier-claim-skew-fallback-design.md)와 함께 보는 편이 안전하다.
- overlap 종료 이후 hard reject와 cleanup까지 넘기려면 [Capability Sunset Gate Matrix 설계](./capability-sunset-gate-matrix-design.md)를 같이 봐야 한다.

## 핵심 개념

refresh migration에서 "추가 인증이 필요하다"는 말은 하나가 아니다.

- `silent migration`: lineage, binding, assurance를 모두 새 세대로 결정론적으로 옮길 수 있다.
- `step-up`: lineage와 base session은 믿을 수 있지만, 새 정책이 요구하는 assurance나 freshness가 부족하다.
- `full reauthentication`: lineage sponsor 자체를 믿을 수 없거나 compromise signal이 있어 현재 세션을 더 연장하면 안 된다.

경계는 간단하다.
**현재 세션이 같은 사용자와 같은 디바이스를 대신해 더 강한 증거를 제출할 자격이 있으면 step-up이고, 그 자격 자체가 깨졌으면 full reauth**다.

즉 이 주제의 핵심은 refresh migration을 "토큰 재발급 성공/실패"가 아니라 **신뢰 연속성(continuity)과 보증 수준(assurance)을 함께 판정하는 escalation matrix**로 보는 것이다.

## 깊이 들어가기

### 1. 왜 refresh migration에 별도 escalation matrix가 필요한가

refresh-family cutover만 보면 old token을 새 family로 옮기면 끝날 것처럼 보인다.
하지만 mixed-version rollout에서는 같은 refresh 요청도 서로 다른 의미를 가진다.

- 어떤 요청은 단순 format upgrade라 silent하게 넘겨도 된다.
- 어떤 요청은 lineage는 안전하지만 `auth_time`, `amr`, device possession이 새 route floor를 못 맞춰 step-up이 맞다.
- 어떤 요청은 lineage alias miss, family quarantine, cross-device replay처럼 현재 세션을 더 이상 sponsor로 삼을 수 없어 full reauth가 맞다.

이 셋을 구분하지 않으면 두 가지 오판이 반복된다.

- 모든 mismatch를 full reauth로 몰아 UX와 rollout 안정성을 동시에 망친다.
- 반대로 모든 mismatch를 silent forced reissue로 넘겨 hidden assurance gap과 compromise tail을 길게 남긴다.

따라서 refresh migration은 availability guardrail과 security guardrail을 동시에 잡는 **3단 escalation 문제**로 다뤄야 한다.

### 2. 결정은 네 개의 축을 같이 읽어야 한다

| 축 | 묻는 질문 | silent 가능 조건 | step-up 조건 | full reauth 조건 |
|---|---|---|---|---|
| lineage portability | legacy refresh를 canonical family에 결정론적으로 매핑할 수 있는가 | alias hit, single-issue, single-contain 유지 | alias는 맞지만 승격 전 추가 증거가 필요 | alias miss, family fork, revoke truth 불명 |
| binding continuity | 같은 device/session continuity를 새 generation에 이어 붙일 수 있는가 | 기존 binding을 그대로 carry-over 가능 | 같은 session이 fresh possession proof를 다시 낼 수 있음 | binding이 끊겼거나 다른 device로 보임 |
| assurance portability | 새 policy가 요구하는 `auth_time`, `acr`, `amr`, risk floor를 만족하는가 | 현재 base assurance로 충분 | continuity는 있으나 assurance/freshness가 낮음 | sponsor session 자체가 assurance artifact를 신뢰할 수 없음 |
| threat posture | benign retry인지, 실제 탈취/replay인지 구분되는가 | same-context duplicate만 보임 | risk signal이 경계선이지만 current session은 여전히 신뢰 가능 | family quarantine, suspicious replay, subject epoch advance |

핵심은 이 네 축이 순서대로 닫힌다는 점이다.

1. lineage가 불명확하면 step-up 이전에 full reauth 또는 deny가 먼저다.
2. lineage가 명확해도 binding continuity가 없다면 current session은 challenge를 sponsor할 수 없다.
3. continuity가 살아 있으면 그제야 assurance gap을 step-up으로 메운다.
4. threat posture가 compromise 쪽으로 기울면 silent/step-up보다 containment와 full reauth가 우선이다.

### 3. Compact escalation matrix

| 관찰 상태 | 해석 | 권장 응답 | 남겨야 할 증거 |
|---|---|---|---|
| legacy refresh alias hit, same device/session, low-risk route, target claim이 deterministic translation 가능 | 단순 representation upgrade | silent migrate + target generation reissue | `decision=silent`, `reason=portable_upgrade`, prior response replay handle |
| alias hit, same device/session, 새 route가 더 강한 `auth_time`/`amr`를 요구 | continuity는 살아 있으나 assurance gap 존재 | step-up challenge 후 migrated successor 발급 | `decision=step-up`, `reason=assurance_gap`, challenge TTL, completion outcome |
| alias hit, device-bound refresh로 올릴 예정인데 현재 device가 fresh possession proof를 다시 제출 가능 | binding 재확인이 필요 | step-up challenge 또는 lease rebind 후 승격 | `decision=step-up`, `reason=binding_rebind_required`, new binding hash |
| alias miss, canonical family state 조회 실패, subject epoch advance, password reset/deprovision 반영됨 | current session sponsor 불가 | full reauth required | `decision=full-reauth`, precise reason code, revoke/cache clear evidence |
| successor 발급 후 old token이 다른 ASN/device에서 재등장하거나 family가 `QUARANTINED` 상태 | compromise 가능성 높음 | family containment + full reauth required | quarantine event, replay evidence, downstream revoke fan-out |

이 표에서 중요한 것은 `step-up`이 `full reauth`의 완화판이 아니라는 점이다.
step-up은 "지금 세션이 challenge를 sponsor해도 된다"는 판단이 있을 때만 열 수 있다.

### 4. silent migration은 "프롬프트 없음"이지 "무조건 더 넓게 허용"이 아니다

silent path를 열 수 있는 최소 조건은 아래와 같다.

- legacy refresh가 canonical family와 deterministic alias로 연결된다.
- same device/session continuity가 유지되고 cross-context anomaly가 없다.
- target generation의 mandatory claim이 translator로 채워지거나 안전하게 유도 가능하다.
- 새 토큰이 요구하는 assurance floor가 base session 수준과 같다.
- high-risk scope를 이번 refresh에서 몰래 넓히지 않는다.

여기서 자주 하는 실수는 silent migration을 "새 policy 전체를 프롬프트 없이 통과시킨다"로 해석하는 것이다.
안전한 설계는 반대다.

- silent path는 **base assurance를 보존하는 범위까지만** 승격한다.
- admin write, payout change, delegated support action처럼 높은 assurance가 필요한 기능은 나중 route에서 step-up을 요구해도 된다.
- refresh 응답에는 `migration_decision=silent`와 reason code를 남겨 나중 incident 때 UX-friendly path와 security exception path를 구분할 수 있어야 한다.

즉 silent migration의 목표는 friction 제거가 아니라 **representation skew만 조용히 제거하는 것**이다.

### 5. step-up은 continuity가 살아 있을 때만 허용한다

step-up이 맞는 대표 상황은 아래와 같다.

- old session의 `auth_time`이 새 정책 freshness floor보다 오래됐다.
- old version에는 `amr`나 device possession evidence가 약하지만, 현재 same-device challenge는 가능하다.
- payout, admin, tenant move 같은 high-risk route가 새 generation에서 더 강한 assurance를 요구한다.
- refresh token을 device-bound 형태로 올리려는데 현재 session이 같은 device key를 다시 prove할 수 있다.

권장 패턴:

- current family는 `QUARANTINED`가 아니라 `PENDING_ASSURANCE_UPGRADE` 같은 상태로 둔다.
- challenge handle은 `canonical_family_id + session_id + device_key_hash + target_assurance`에 바인딩한다.
- TTL은 짧게 두고 one-time consume으로 처리한다.
- step-up 성공 후에만 elevated refresh/access generation을 발급한다.
- 실패나 timeout은 "migration 실패"와 "공격 의심"을 분리해 기록한다.

중요한 점은 step-up pending 동안 old refresh를 unrestricted하게 다시 돌려서는 안 된다는 것이다.

- base assurance 범위의 narrow token만 허용하거나
- prior challenge result를 재사용하거나
- 아예 challenge complete 전까지 privileged successor issuance를 막는 편이 안전하다.

즉 step-up path의 본질은 더 강한 증거를 요구하는 것이지, 기존 lineage를 무한히 연장하는 것이 아니다.

### 6. full reauth는 sponsor session이 깨졌을 때 열린다

full reauth가 필요한 대표 조건:

- canonical family alias miss나 lineage fork 때문에 current refresh의 정체를 설명할 수 없다.
- family state가 이미 `QUARANTINED` 또는 `REVOKED`다.
- password reset, deprovision, subject epoch advance처럼 기존 session 자체를 무효화하는 사건이 발생했다.
- successor 발급 후 old refresh가 다른 device, ASN, geo, binding에서 다시 나타난다.
- step-up에 필요한 device possession이나 session coherence artifact를 current session이 제시할 수 없다.

여기서 중요한 운영 원칙은 "step-up으로 신뢰를 복구하려 하지 말라"는 것이다.
이미 sponsor session이 의심스러우면, 그 세션이 올린 challenge 결과도 설득력이 약하다.

full reauth path에서는 보통 아래가 같이 일어난다.

- canonical family containment 또는 revoke
- session/access cache clear
- outstanding challenge handle 폐기
- `full_reauth_required` reason code 반환
- incident ladder에 맞춘 telemetry와 operator surface 갱신

즉 full reauth는 단순히 로그인 화면으로 보내는 UX 결정이 아니라 **현재 lineage를 더는 승격 대상이 아니라 containment 대상으로 바꾸는 상태 전이**다.

### 7. observability는 outcome bucket을 섞지 않아야 한다

refresh migration이 흔들릴 때는 "reauth 비율이 올랐다"보다 어떤 bucket이 올랐는지가 중요하다.

| metric | 왜 중요한가 |
|---|---|
| `refresh_migration_decision_total{decision,reason,version_pair,route_risk}` | silent, step-up, full reauth가 어디서 갈리는지 본다 |
| `silent_migration_replay_after_issue_total` | silent path가 benign retry와 실제 replay를 제대로 분리하는지 본다 |
| `step_up_required_total{reason}` / `step_up_complete_ratio` | assurance gap인지 UX dead-end인지 구분한다 |
| `full_reauth_required_total{reason}` | lineage untrusted인지 policy bug인지 reason bucket을 나눈다 |
| `challenge_unbindable_total` | step-up으로 열 수 있어야 할 경로가 실제로는 full reauth로 새고 있는지 본다 |
| `alias_miss_total`, `family_fork_detected_total` | migration data/control plane 오류를 빨리 잡는다 |

gate 판단도 세 outcome을 같이 읽어야 한다.

- silent ramp를 열 때는 `full_reauth`가 아니라 `silent -> replay` tail이 안정적인지 먼저 본다.
- step-up 비율이 늘었다고 바로 incident라고 단정하면 안 된다. high-risk route exposure 증가일 수도 있다.
- full reauth 비율이 올라가면 policy 강화를 먼저 의심하지 말고 alias miss, revoke lag, lineage fork를 같이 확인해야 한다.

### 8. cleanup은 "prompt가 안 보인다"가 아니라 decision 근거가 닫힌 뒤에 한다

mixed-version refresh migration이 끝났다고 해도, escalation matrix를 바로 지우면 안 된다.
cleanup은 아래가 모두 닫힐 때 여는 편이 안전하다.

- `legacy_refresh_last_seen`이 silence window를 충족한다.
- `step_up_pending` backlog가 0이다.
- `full_reauth_required_total{reason=alias_miss}`가 rollout bug가 아니라 expected residual만 남는다.
- replay containment, revoke propagation, challenge cleanup tail이 observation window 안에서 안정적이다.

즉 escalation matrix cleanup은 prompt 노출이 줄었다는 이유로 닫는 것이 아니라,
**silent/step-up/full reauth를 갈랐던 근거 자체가 더는 mixed-version skew를 설명하지 않을 때** 닫는 것이다.

## 실전 시나리오

### 시나리오 1: 모바일 구버전 앱 refresh를 조용히 새 family로 옮긴다

문제:

- 구버전 앱은 legacy refresh를 보내지만 같은 device/session이고 low-risk base route만 사용한다.

해결:

- canonical family alias hit를 확인한다.
- same-device continuity와 benign retry window를 확인한 뒤 silent migrated successor를 발급한다.
- 새 토큰은 base assurance만 담고, 이후 high-risk route는 별도 step-up 정책으로 다룬다.

### 시나리오 2: payout 관리 화면 진입 전에 assurance를 한 번 더 올려야 한다

문제:

- legacy refresh로 base session은 연장 가능하지만 `auth_time`이 오래됐고 새 payout route는 stronger `amr`를 요구한다.

해결:

- current family는 유지하되 `PENDING_ASSURANCE_UPGRADE`로 표시한다.
- same-device step-up challenge를 요구한다.
- 성공 시에만 elevated refresh/access generation을 발급하고, 실패 시 privileged route 접근만 막는다.

### 시나리오 3: forced reissue 뒤 old refresh가 다른 device에서 다시 나타난다

문제:

- 이미 successor가 발급된 canonical family의 old token이 다른 ASN/device/binding에서 재등장했다.

해결:

- same-context retry로 보지 않는다.
- canonical family를 quarantine 또는 revoke하고 full reauth를 강제한다.
- reason code를 `replay_after_successor_issue`처럼 분리해 migration retry와 실제 탈취를 섞지 않는다.

## 코드로 보기

```pseudo
function decideRefreshEscalation(lineage, context, targetPolicy):
  if lineage == null or lineage.familyState in ["QUARANTINED", "REVOKED"]:
    return fullReauth("lineage_untrusted")

  if subjectEpochAdvanced(lineage.subjectId) or suspiciousReplay(lineage, context):
    containment.quarantine(lineage.canonicalFamilyId)
    return fullReauth("compromise_or_subject_epoch_advanced")

  if !bindingContinuityPortable(lineage, context):
    return fullReauth("binding_not_portable")

  if needsFreshAssurance(lineage, context, targetPolicy):
    if canCurrentSessionSponsorStepUp(lineage, context, targetPolicy):
      return stepUp("assurance_or_binding_rebind_required")
    return fullReauth("challenge_unbindable")

  return silent("portable_upgrade")
```

```yaml
refresh_reauth_escalation:
  version_pair: legacy-v1-to-v2
  silent:
    require_alias_hit: true
    require_same_device_binding: true
    max_route_risk_class: base
  step_up:
    reasons:
      - auth_time_stale
      - amr_floor_gap
      - possession_rebind_required
    challenge_ttl_seconds: 300
    bind_to:
      - canonical_family_id
      - session_id
      - device_key_hash
  full_reauth:
    reasons:
      - alias_miss
      - family_quarantined
      - subject_epoch_advanced
      - replay_after_successor_issue
      - challenge_unbindable
```

핵심은 parser/translator 여부보다도, **현재 session이 새 assurance를 sponsor할 자격이 있는지**를 먼저 묻는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| silent 범위를 넓게 잡기 | UX가 가장 부드럽다 | assurance gap을 숨기기 쉽다 | low-risk base route가 대부분일 때 |
| step-up을 적극 사용 | current session continuity를 살리며 policy 강화 가능 | prompt와 challenge 상태 관리가 복잡해진다 | same-device continuity는 강하지만 freshness 요구가 자주 바뀔 때 |
| full reauth를 빨리 여는 전략 | semantic이 단순하고 incident triage가 빠르다 | 정상 사용자 churn과 rollout friction이 크다 | lineage sponsor를 믿기 어려운 위협 모델일 때 |
| route-level step-up, refresh-level silent 분리 | refresh UX를 지킬 수 있다 | operator가 두 단계 결정을 함께 이해해야 한다 | base session과 elevated session을 분리 운영할 때 |

## 꼬리질문

> Q: `auth_time`이 오래됐다는 이유만으로 full reauth가 맞나요?
> 의도: assurance gap과 lineage compromise를 구분하는지 확인
> 핵심: 보통은 아니다. same-device/session continuity가 살아 있으면 step-up이 먼저다.

> Q: silent migration이면 이후 high-risk route도 계속 조용히 허용해야 하나요?
> 의도: silent path의 범위를 정확히 이해하는지 확인
> 핵심: 아니다. silent는 representation skew를 조용히 닫는다는 뜻이지 elevated assurance까지 프롬프트 없이 올린다는 뜻이 아니다.

> Q: alias miss가 일시적 cache lag일 수도 있는데도 full reauth가 맞나요?
> 의도: fallback과 fail-closed 경계를 이해하는지 확인
> 핵심: authoritative origin이 같은 budget 안에서 lineage를 확인할 수 있으면 bounded fallback을 쓸 수 있다. 그 확인조차 안 되면 sponsor session을 믿을 수 없으므로 full reauth가 맞다.

## 한 줄 정리

Refresh reauth escalation matrix 설계는 mixed-version refresh migration에서 current session이 단순 승격 대상인지, 추가 증거를 한 번 더 낼 수 있는 sponsor인지, 아니면 더는 믿어선 안 되는 lineage인지 구분해 silent migration, step-up, full reauthentication을 각기 다른 증거 강도로 여는 운영 설계다.
