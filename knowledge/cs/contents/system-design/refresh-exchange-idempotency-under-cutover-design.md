---
schema_version: 3
title: Refresh Exchange Idempotency Under Cutover 설계
concept_id: system-design/refresh-exchange-idempotency-under-cutover-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- refresh exchange idempotency
- refresh cutover duplicate handling
- refresh exchange lease
- refresh replay cache
aliases:
- refresh exchange idempotency
- refresh cutover duplicate handling
- refresh exchange lease
- refresh replay cache
- duplicate response replay
- same-context duplicate
- cross-context duplicate
- benign retry vs compromise
- forced reissue retry
- already migrated receipt
- refresh successor replay handle
- refresh exchange decision id
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/refresh-family-rotation-cutover-design.md
- contents/system-design/refresh-reauth-escalation-matrix-design.md
- contents/system-design/canonical-revocation-plane-across-token-generations-design.md
- contents/system-design/session-store-claim-version-cutover-design.md
- contents/system-design/idempotency-key-store-dedup-window-replay-safe-retry-design.md
- contents/system-design/session-store-design-at-scale.md
- contents/security/refresh-token-rotation-reuse-detection.md
- contents/security/refresh-token-family-invalidation-at-scale.md
- contents/security/token-misuse-detection-replay-containment.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Refresh Exchange Idempotency Under Cutover 설계 설계 핵심을 설명해줘
- refresh exchange idempotency가 왜 필요한지 알려줘
- Refresh Exchange Idempotency Under Cutover 설계 실무 트레이드오프는 뭐야?
- refresh exchange idempotency 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Refresh Exchange Idempotency Under Cutover 설계를 다루는 deep_dive 문서다. refresh exchange idempotency under cutover 설계는 forced reissue와 mixed-version overlap 동안 같은 refresh artifact가 다시 들어와도 successor를 한 번만 발급하고, lease·replay cache·duplicate-response contract로 benign retry와 실제 compromise 신호를 분리하는 운영 설계다. 검색 질의가 refresh exchange idempotency, refresh cutover duplicate handling, refresh exchange lease, refresh replay cache처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Refresh Exchange Idempotency Under Cutover 설계

> 한 줄 요약: refresh exchange idempotency under cutover 설계는 forced reissue와 mixed-version overlap 동안 같은 refresh artifact가 다시 들어와도 successor를 한 번만 발급하고, lease·replay cache·duplicate-response contract로 benign retry와 실제 compromise 신호를 분리하는 운영 설계다.
>
> 문서 역할: 이 문서는 [Refresh-Family Rotation Cutover 설계](./refresh-family-rotation-cutover-design.md)의 "idempotent exchange" 문장을 더 깊게 풀어, cutover 시점의 refresh endpoint가 왜 단순 rotate API가 아니라 duplicate classification state machine이어야 하는지 설명하는 focused deep dive다.

retrieval-anchor-keywords: refresh exchange idempotency, refresh cutover duplicate handling, refresh exchange lease, refresh replay cache, duplicate response replay, same-context duplicate, cross-context duplicate, benign retry vs compromise, forced reissue retry, already migrated receipt, refresh successor replay handle, refresh exchange decision id, refresh token duplicate classification, refresh exchange grace window, refresh family cutover idempotency, refresh retry context binding, migration replay cache miss, cutover duplicate containment, response replay under refresh rotation

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Refresh-Family Rotation Cutover 설계](./refresh-family-rotation-cutover-design.md)
> - [Refresh Reauth Escalation Matrix 설계](./refresh-reauth-escalation-matrix-design.md)
> - [Canonical Revocation Plane Across Token Generations 설계](./canonical-revocation-plane-across-token-generations-design.md)
> - [Session Store / Claim-Version Cutover 설계](./session-store-claim-version-cutover-design.md)
> - [Idempotency Key Store / Dedup Window / Replay-Safe Retry 설계](./idempotency-key-store-dedup-window-replay-safe-retry-design.md)
> - [Session Store Design at Scale](./session-store-design-at-scale.md)
> - [Security: Refresh Token Rotation / Reuse Detection](../security/refresh-token-rotation-reuse-detection.md)
> - [Security: Refresh Token Family Invalidation at Scale](../security/refresh-token-family-invalidation-at-scale.md)
> - [Security: Token Misuse Detection / Replay Containment](../security/token-misuse-detection-replay-containment.md)

## 이 문서 다음에 보면 좋은 설계

- lineage authority, forced reissue, canonical family graph를 먼저 넓게 보려면 [Refresh-Family Rotation Cutover 설계](./refresh-family-rotation-cutover-design.md)부터 이어서 보면 된다.
- duplicate가 실제 containment나 revoke fan-out으로 어떻게 닫히는지는 [Canonical Revocation Plane Across Token Generations 설계](./canonical-revocation-plane-across-token-generations-design.md)로 내려가면 된다.
- duplicate를 benign retry로 재생할지, step-up으로 올릴지, full reauth로 닫을지는 [Refresh Reauth Escalation Matrix 설계](./refresh-reauth-escalation-matrix-design.md)와 함께 보는 편이 안전하다.
- generic lease / dedup / replay 저장소 관점은 [Idempotency Key Store / Dedup Window / Replay-Safe Retry 설계](./idempotency-key-store-dedup-window-replay-safe-retry-design.md)에서 다시 정리할 수 있다.

## 핵심 개념

refresh cutover에서 가장 위험한 질문은 "같은 refresh token이 또 왔다"가 아니다.
진짜 질문은 아래 둘 중 무엇인가다.

- 사용자는 이미 successor를 받았지만 응답을 못 받아 재시도하고 있는가
- 공격자는 old refresh artifact를 들고 cutover 창을 이용해 lineage를 다시 열려 하는가

이 둘을 구분하지 못하면 두 가지가 동시에 깨진다.

- benign duplicate를 compromise로 오판해 family quarantine false positive가 늘어난다
- 실제 compromise를 단순 retry로 오판해 successor 이후 old artifact reuse를 흘려보낸다

따라서 refresh endpoint는 단순 `rotate(token)`이 아니라 아래 불변식을 지키는 exchange state machine이어야 한다.

- `single-issue`: presented refresh 한 개당 cutover decision은 한 번만 successor issuance로 닫힌다
- `replayable-success`: 성공 응답을 잃어버린 재시도는 같은 decision을 다시 받을 수 있다
- `context-scored-duplicate`: duplicate는 "몇 번 왔나"가 아니라 "같은 trust context에서 왔나"로 분류한다
- `single-contain`: compromise 의심 duplicate는 generation별로 따로 막지 않고 canonical family/session 축으로 containment 한다

## 깊이 들어가기

### 1. cutover는 duplicate를 더 많이 만들고, 그 duplicate는 더 해석하기 어려워진다

단순 refresh rotation만 있을 때도 duplicate는 생긴다.
cutover가 붙으면 duplicate의 의미가 훨씬 복잡해진다.

- old app build는 legacy refresh를 재전송한다
- new server는 forced reissue로 successor를 이미 발급했을 수 있다
- response path는 네트워크 유실로 끊길 수 있다
- 웹 다중 탭이나 mobile foreground/background race가 같은 artifact를 거의 동시에 보낸다
- 공격자는 "successor가 이미 발급된 old artifact"를 재사용해 lineage를 다시 열 수 있는지 탐색한다

즉 cutover duplicate는 retry 문제이면서 동시에 containment 문제다.
그래서 설계 질문도 두 개를 같이 묻는다.

| 질문 | 잘못 답하면 생기는 문제 |
|---|---|
| 같은 artifact로 successor를 두 번 발급하지 않으려면? | family fork, successor race |
| 같은 artifact 재등장을 benign retry와 compromise로 어떻게 가를까? | false quarantine 또는 hidden replay |

### 2. refresh exchange는 "토큰 1개"가 아니라 "결정 1개"를 멱등하게 만들어야 한다

cutover에서 멱등해야 하는 것은 raw request 자체보다 **exchange decision**이다.
실전 계약은 보통 아래처럼 잡는 편이 안전하다.

```text
same presented refresh
+ same canonical family lineage
+ same target generation policy
= at most one exchange decision
```

이 decision은 단순 성공/실패만이 아니다.
최소한 아래 outcome bucket을 분리해야 한다.

- `SUCCESS_REISSUED`: silent migrate 또는 normal rotate로 successor 발급
- `PENDING`: lease는 잡았지만 결과 durable commit 전
- `ALREADY_MIGRATED`: successor는 이미 존재하지만 replay cache가 비었거나 caller가 늦게 재진입
- `CONTAINED`: suspicious duplicate라 family/session containment로 올림
- `REAUTH_REQUIRED`: compromise 또는 sponsor 불신으로 더는 replay 대상이 아님

핵심은 duplicate가 들어와도 새 판단을 즉석에서 다시 만드는 것이 아니라,
**이미 존재하는 decision을 재현하거나 그 decision을 containment로 승격하는 것**이다.

### 3. lease는 successor 중복 발급을 막고 duplicate 해석의 기준점을 만든다

lease가 없다면 웹 탭 경쟁이나 timeout retry만으로도 두 개의 successor가 만들어질 수 있다.
권장 lease key는 보통 아래 둘 중 하나다.

- `presented_token_hash + target_generation`
- `canonical_family_id + presented_token_hash + migration_policy_version`

record는 대략 이런 필드를 가진다.

```yaml
refresh_exchange_record:
  exchange_key: "fam_c_7:tok_h_ab12:v2"
  canonical_family_id: "fam_c_7"
  presented_token_hash: "tok_h_ab12"
  target_generation: v2
  decision_state: LEASED
  lease_owner: "req_91"
  lease_until: "2026-04-14T12:00:05Z"
  first_context_hash: "ctx_h_33"
  first_seen_at: "2026-04-14T12:00:00Z"
  replay_until: null
  successor_ref: null
  containment_reason: null
```

lease가 하는 일은 세 가지다.

- **중복 발급 방지**: 아직 같은 artifact의 exchange가 진행 중이면 두 번째 caller는 join/replay/pending으로 보내고 새 issuance를 금지한다
- **first-observer anchor**: 첫 요청이 어떤 context에서 왔는지 저장해 이후 duplicate를 same-context / cross-context로 비교한다
- **recover-first 분기**: lease가 만료됐는데 결과가 불명확하면 곧바로 새 successor를 발급하지 않고 canonical lineage를 조회해 이미 발급된 흔적을 먼저 찾는다

중요한 점은 lease TTL이 짧더라도, lease expiry가 issuance 허용 신호는 아니라는 것이다.
expiry 뒤에는 `recover or contain`, not `blind reissue`가 기본이다.

### 4. replay cache는 "같은 성공"을 다시 보여 주기 위한 증거 저장소다

lease가 duplicate 발급을 막는다면 replay cache는 benign retry를 정상 흐름으로 돌려놓는다.
저장 대상은 raw token 전체보다 **재현 가능한 성공 결과**다.

권장 형태는 세 가지다.

| 패턴 | 저장 내용 | 언제 쓰는가 | 장점 | 주의점 |
|---|---|---|---|---|
| full response replay | 암호화된 successor envelope, response metadata | BFF나 trusted mobile channel | 최초 성공과 가장 비슷한 UX | 보관 시간과 secret handling이 까다롭다 |
| response handle replay | `decision_id`, redeemable handle, successor ref | public API, 다중 edge 경유 | raw token 보관을 줄인다 | handle redeem path가 추가된다 |
| current-session pointer | `session_id`, `family_id`, `reissue_epoch` | replay cache evict 후 degraded path | duplicate 재발급을 막는다 | caller가 한 번 더 fetch해야 할 수 있다 |

cutover에서는 두 가지 규칙이 특히 중요하다.

- replay cache TTL은 access TTL이 아니라 **response-loss grace window** 기준으로 잡는다
- replay cache miss가 곧 reissue 허용은 아니다. canonical lineage에 `migrated_from_token_id`가 남아 있으면 `ALREADY_MIGRATED`로 응답한다

즉 replay cache의 목적은 편의가 아니라, **성공한 cutover를 다시 성공으로 보이게 만드는 것**이다.

### 5. duplicate-response contract가 있어야 benign retry와 compromise를 분리할 수 있다

같은 duplicate라도 응답 패턴이 하나면 분류가 무너진다.
권장 duplicate-response 패턴은 아래처럼 나눈다.

| duplicate 상황 | 권장 응답 패턴 | 의미 | 무엇을 막는가 |
|---|---|---|---|
| 첫 요청이 아직 lease 안에서 처리 중, 같은 trust context | `PENDING` + decision handle | 아직 결과 확정 전이지만 같은 작업에 합류 | 탭 경쟁으로 인한 second issuance |
| successor가 이미 발급됐고 same-context duplicate | prior-successor replay | benign retry 흡수 | false quarantine, UX 반복 로그인 |
| successor는 이미 존재하지만 replay cache만 비어 있음 | `ALREADY_MIGRATED` + current-session pointer | 새 issuance는 금지, 현재 state를 다시 조회 | cache miss를 이용한 lineage fork |
| successor 이후 cross-context duplicate | `CONTAINED` 또는 `REAUTH_REQUIRED` | compromise 의심, replay 대상 아님 | attacker probing을 benign retry로 오판 |

여기서 HTTP status code는 구현체마다 달라도 된다.
중요한 것은 status number가 아니라 **duplicate가 기존 decision을 재생한 것인지, containment로 승격된 것인지가 호출자와 telemetry에 구분돼야 한다**는 점이다.

### 6. benign retry vs compromise는 transport count가 아니라 context drift로 가른다

cutover duplicate 분류는 "두 번 왔다"보다 "무엇이 얼마나 달라졌나"가 중요하다.
대표 비교 축은 아래와 같다.

| 축 | benign 쪽 신호 | compromise 쪽 신호 |
|---|---|---|
| session continuity | 같은 browser session / app install / device binding | 다른 session, binding proof 불일치 |
| network drift | 같은 ASN/region, 짧은 RTT window | ASN/geo 급변, known bad egress |
| issuance timing | successor 직후 짧은 grace window 재시도 | observation window 밖 늦은 재등장 |
| usage evidence | caller가 새 successor 사용 흔적이 없음 또는 매우 짧음 | 새 successor가 이미 high-risk route에 쓰인 뒤 old artifact 재등장 |
| family state | `ACTIVE`, `DRAINING` | 이미 `QUARANTINED`, `REVOKED`, subject epoch advanced |

실전 분류는 보통 이렇게 다룬다.

- same-context + short window duplicate: replay 또는 pending
- same device지만 continuity evidence 일부 부족: 즉시 quarantine보다 step-up 후보로 보되 새 issuance는 금지
- cross-context duplicate after successor issue: compromise 후보로 승격하고 canonical family/session containment

ASN 하나만 달랐다고 바로 compromise로 닫는 것은 과하고,
반대로 successor 이후 cross-context duplicate를 response replay로 돌리는 것은 더 위험하다.

### 7. replay cache miss와 lease expiry는 가장 위험한 순간이다

실무에서 사고가 가장 많이 나는 지점은 정상 상태가 아니라 degrade 상태다.

#### case A. replay cache miss, lineage hit

- 이전 exchange는 성공했고 successor도 존재한다
- 하지만 short-lived replay cache가 날아갔다
- duplicate가 다시 들어온다

이때 안전한 기본값은 새 successor 재발급이 아니라 `ALREADY_MIGRATED`다.
caller는 current session/status fetch로 이동하고, backend는 `migrated_from_token_id`와 `successor_token_id`를 근거로 같은 lineage를 가리킨다.

#### case B. lease expired, result unknown

- worker가 successor issuance 직후 죽었는지, 이전에 죽었는지 애매하다
- second caller가 lease expiry 뒤 도착한다

이때도 blind reissue를 열면 안 된다.
먼저 canonical family graph, audit trail, session store에서 아래를 복구 조회한다.

- `migrated_from_token_id`
- `reissue_decision_id`
- `successor_token_id`
- `family_state`

결과가 보이면 replay/`ALREADY_MIGRATED`,
cross-context anomaly가 보이면 containment,
정말 아무 흔적도 없을 때만 fenced retry를 연다.

### 8. state machine은 issue path와 containment path를 같은 record에서 닫아야 한다

권장 상태 전이는 대략 아래와 같다.

```text
OPEN
  -> LEASED
  -> SUCCESS_RECORDED
  -> REPLAYABLE
  -> ALREADY_MIGRATED
  -> CONTAINED
  -> REAUTH_REQUIRED
```

중요한 점은 `REPLAYABLE`과 `CONTAINED`가 서로 다른 시스템의 상태가 아니라,
**같은 exchange record가 duplicate evidence에 따라 어디로 해석됐는지의 결과**라는 것이다.

```pseudo
function exchangeRefresh(presentedToken, context):
  lineage = canonicalFamily.lookup(presentedToken)
  if lineage == null:
    return deny("unknown_refresh")

  result = exchangeStore.claimOrReplay(
    key = buildExchangeKey(lineage, targetGeneration()),
    context = fingerprint(context)
  )

  if result.kind == "REPLAYABLE":
    return duplicateResponse.replay(result)

  if result.kind == "PENDING":
    if sameTrustContext(result.firstContext, context):
      return duplicateResponse.pending(result.decisionHandle)
    containment.quarantine(lineage.canonicalFamilyId, reason="cross_context_duplicate_during_pending")
    return duplicateResponse.containedReauth(result.decisionHandle)

  if lineage.familyState in ["QUARANTINED", "REVOKED"] or suspiciousDrift(lineage, context):
    containment.quarantine(lineage.canonicalFamilyId, reason="duplicate_after_successor_issue")
    exchangeStore.recordContainment(lineage, context)
    return duplicateResponse.containedReauth(null)

  successor = issueSingleSuccessor(lineage, context)
  exchangeStore.completeSuccess(lineage, successor, context)
  return duplicateResponse.success(successor)
```

### 9. observability는 duplicate 수보다 duplicate 분류 품질을 봐야 한다

cutover에서는 duplicate 자체가 늘 수 있다.
문제는 개수가 아니라 **잘못 분류하는 비율**이다.

권장 지표:

- `refresh_exchange_lease_contention_total{same_context,cross_context}`
- `refresh_exchange_replay_total{result=replayed|pending|already_migrated|contained}`
- `refresh_exchange_cache_miss_total{lineage_found}`
- `refresh_duplicate_context_drift_total{dimension}`
- `refresh_compromise_suspected_after_successor_total`
- `refresh_false_quarantine_review_total`
- `refresh_exchange_recover_first_total{outcome}`

gate도 아래처럼 읽는 편이 안전하다.

| gate | 봐야 할 것 |
|---|---|
| ramp open | `same_context_replay`가 안정적이고 `cross_context_duplicate`가 baseline 안 |
| mixed-version soak | `already_migrated_without_reissue`가 늘어도 lineage fork는 0 |
| cleanup 준비 | `legacy_duplicate_last_seen` 감소, replay cache miss 재발급 0, suspicious duplicate residual만 남음 |

### 10. 실전 시나리오

#### 시나리오 1: 모바일 앱이 successor 응답을 못 받고 같은 legacy refresh를 다시 보낸다

문제:

- 서버는 forced reissue를 이미 끝냈다
- 앱은 응답을 받지 못해 같은 refresh를 재전송한다

해결:

- exchange lease가 same-context duplicate를 같은 decision에 묶는다
- replay cache에서 prior successor 또는 handle을 재생한다
- 새 successor 추가 발급은 금지한다

#### 시나리오 2: 웹 다중 탭이 동시에 refresh를 때린다

문제:

- 탭 A와 탭 B가 같은 browser session에서 거의 동시에 refresh를 호출한다

해결:

- 탭 A만 lease owner가 된다
- 탭 B는 `PENDING` 또는 prior-successor replay를 받는다
- 같은 session continuity가 유지되므로 quarantine로 올리지 않는다

#### 시나리오 3: successor 발급 후 old refresh가 다른 device에서 재등장한다

문제:

- new generation access가 이미 사용되고 있는데 old artifact가 다른 ASN/device에서 다시 보인다

해결:

- replay cache를 사용하지 않는다
- canonical family/session을 containment 대상으로 승격한다
- `REAUTH_REQUIRED` 또는 `CONTAINED`로 응답하고 revoke fan-out을 시작한다

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| full successor replay | UX가 가장 좋다 | secret handling이 까다롭다 | trusted first-party client |
| response handle replay | 보안/운영 균형이 좋다 | redeem path가 필요하다 | public/mobile mixed edge |
| cache miss 시 blind reissue | 구현이 단순해 보인다 | lineage fork와 compromise 은폐를 만든다 | 권장하지 않음 |
| duplicate를 전부 quarantine | 공격 억제는 강해 보인다 | rollout false positive가 급증한다 | 극고위험 admin surface만 제한적 |
| same-context duplicate만 replay 허용 | benign retry를 흡수한다 | context fingerprint 설계가 필요하다 | 일반 consumer refresh cutover |

핵심은 refresh exchange idempotency under cutover가 단순 retry 완화가 아니라,
**single successor issuance를 유지하면서 duplicate를 증거 기반으로 분류하는 auth migration 운영 설계**라는 점이다.

## 꼬리질문

> Q: replay cache가 비었으면 같은 refresh로 successor를 다시 발급해도 되나요?
> 의도: cache miss와 issuance truth를 분리하는지 확인
> 핵심: 아니다. cache miss는 lineage 조회와 `ALREADY_MIGRATED` degraded path를 먼저 열어야지, blind reissue 신호가 아니다.

> Q: same IP면 benign retry, 다른 IP면 compromise로 보면 되나요?
> 의도: context drift를 단일 축으로 단순화하지 않는지 확인
> 핵심: 아니다. session continuity, binding proof, timing, family state, successor 사용 흔적을 같이 봐야 한다.

> Q: lease가 만료됐으면 다음 요청이 새 issuance를 잡아도 되나요?
> 의도: recover-first 규칙을 아는지 확인
> 핵심: 아니다. lease expiry 뒤에는 canonical lineage와 audit 흔적부터 복구 조회해야 한다.

> Q: duplicate-response pattern은 HTTP status만 잘 나누면 끝인가요?
> 의도: transport 표면과 canonical decision record를 구분하는지 확인
> 핵심: 아니다. status code보다 중요한 것은 duplicate가 같은 decision replay인지 containment 승격인지 backend state와 telemetry에 남는 것이다.

## 한 줄 정리

Refresh exchange idempotency under cutover 설계는 같은 refresh artifact 재등장을 lease와 replay cache로 한 번의 exchange decision에 묶고, context drift가 생길 때만 canonical containment로 승격해 benign retry와 compromise를 구분하는 설계다.
