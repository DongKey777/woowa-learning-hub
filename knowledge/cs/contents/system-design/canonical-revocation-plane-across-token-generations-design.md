# Canonical Revocation Plane Across Token Generations 설계

> 한 줄 요약: canonical revocation plane across token generations 설계는 legacy/new access token, refresh token, verifier, cache tier가 함께 살아 있는 overlap window 동안 세대별 ID를 canonical subject/session/family scope로 접어 넣고, revoke fan-out과 family quarantine를 한 state machine으로 운영해 zombie allow와 lineage fork를 동시에 막는 운영 설계다.
>
> 문서 역할: 이 문서는 [Session Store / Claim-Version Cutover 설계](./session-store-claim-version-cutover-design.md)의 canonical revoke truth, [Refresh-Family Rotation Cutover 설계](./refresh-family-rotation-cutover-design.md)의 canonical family graph, [Revocation Bus Regional Lag Recovery 설계](./revocation-bus-regional-lag-recovery-design.md)의 regional repair를 하나의 revocation plane으로 묶어 설명하는 focused deep dive다.

retrieval-anchor-keywords: canonical revocation plane across token generations, mixed-version token revocation, legacy new token coexistence, canonical revoke ledger, alias mapping, alias projection, token generation coexistence, generation-aware revoke fan-out, canonical family quarantine, family quarantine release gate, legacy verifier alias miss, multi-generation revoke propagation, canonical session subject device family scope, projection backlog, stale allow after quarantine, mixed-generation auth rollout, overlap window revocation design, family fork containment

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Session Store / Claim-Version Cutover 설계](./session-store-claim-version-cutover-design.md)
> - [Refresh-Family Rotation Cutover 설계](./refresh-family-rotation-cutover-design.md)
> - [Revocation Bus Regional Lag Recovery 설계](./revocation-bus-regional-lag-recovery-design.md)
> - [Refresh Reauth Escalation Matrix 설계](./refresh-reauth-escalation-matrix-design.md)
> - [Edge Verifier Claim-Skew Fallback 설계](./edge-verifier-claim-skew-fallback-design.md)
> - [Session Store Design at Scale](./session-store-design-at-scale.md)
> - [Protocol Version Skew / Compatibility 설계](./protocol-version-skew-compatibility-design.md)
> - [Security: Session Revocation at Scale](../security/session-revocation-at-scale.md)
> - [Security: Refresh Token Family Invalidation at Scale](../security/refresh-token-family-invalidation-at-scale.md)
> - [Security: Token Misuse Detection / Replay Containment](../security/token-misuse-detection-replay-containment.md)
> - [Security: Revocation Propagation Lag / Debugging](../security/revocation-propagation-lag-debugging.md)
> - [Security: Device / Session Graph Revocation Design](../security/device-session-graph-revocation-design.md)

## 핵심 개념

token generation overlap window에서 가장 위험한 사고는 "legacy token이 아직 남아 있다"는 사실 자체가 아니라,
같은 보안 의도가 세대별로 다르게 해석되는 상태다.

- 새 verifier는 `canonical_family_id` 기준으로 family quarantine를 걸었는데 legacy refresh path는 아직 `legacy_family_id`만 본다
- password reset이나 SCIM deprovision이 canonical subject epoch를 올렸는데 old access cache는 예전 namespace verdict를 계속 들고 있다
- refresh forced reissue는 new generation으로만 승격했는데 revoke fan-out은 old/new projection을 따로 쏴 lineage fork와 stale allow를 동시에 만든다

즉 overlap window의 핵심은 "토큰이 둘이다"가 아니라 **진실원이 둘이 되지 않게 막는 것**이다.
권장 원칙은 아래 한 줄로 요약된다.

- `dual-accept, single-issue, single-revoke, single-quarantine`

읽기 호환은 둘일 수 있지만, revoke truth와 containment truth는 하나여야 한다.

## 깊이 들어가기

### 1. 세대가 여러 개여도 single truth로 남겨야 하는 것은 네 가지다

| truth | canonical 질문 | 분리되면 생기는 문제 | 유지해야 할 불변식 |
|---|---|---|---|
| issue truth | successor token을 누가 발급하는가 | lineage fork, legacy successor 재발급 | overlap 동안에도 target generation만 발급 |
| alias truth | presented token이 어느 canonical scope에 속하는가 | alias miss, revoke miss, audit 분기 | generation-local ID는 모두 canonical subject/session/family로 접힘 |
| revoke truth | 어떤 epoch/state가 최종 무효화인가 | stale allow, region별 의미 차이 | revoke는 canonical scope와 epoch에만 기록 |
| quarantine truth | 어떤 family/session을 containment 상태로 볼 것인가 | 한쪽은 막히고 다른 쪽은 계속 refresh | quarantine는 canonical family/session 상태 전이로만 기록 |

여기서 많이 놓치는 부분이 alias truth다.
alias mapping을 단순 lookup 편의 기능으로 보면 revoke plane이 필연적으로 깨진다.
overlap window에서 alias mapping은 곧 **revocation index**다.

### 2. alias mapping은 "나중에 붙이는 번역기"가 아니라 revoke 인덱스다

legacy/new token이 공존할 때 presented artifact는 제각각 다르다.

- legacy access token은 old `jti`나 old `session_key`를 들고 올 수 있다
- new access token은 new claim pointer나 session handle을 들고 올 수 있다
- legacy refresh는 old lineage row나 `legacy_family_id`를 기준으로 들어올 수 있다
- new refresh는 `canonical_family_id` 또는 migrated successor chain을 기준으로 들어올 수 있다

이들을 revoke plane이 이해하는 canonical scope로 접으려면 alias record가 발급 시점부터 존재해야 한다.
권장 record는 대략 아래 정도 정보를 가진다.

```yaml
alias_record:
  presented_artifact_hash: "tok_h:ab12"
  artifact_type: refresh_token
  generation: legacy
  canonical_subject_id: "subj_42"
  canonical_session_id: "sess_9"
  canonical_family_id: "fam_c_7"
  canonical_epoch_ref:
    subject: 18
    device: 5
    family: 33
  mapped_by: forced_reissue
  successor_artifact_hash: "tok_h:cd34"
  alias_state: ACTIVE
  projection_version: 8842
```

설계 원칙:

- alias record는 issue/refresh/forced reissue 시점에 생성한다. first-revoke 시점에 lazy create하면 이미 늦다.
- alias record는 append-only에 가깝게 다룬다. old alias를 다른 canonical family로 in-place 덮어쓰지 않는다.
- reverse lookup이 가능해야 한다. `canonical_family_id -> all active generations`가 나와야 fan-out과 audit가 닫힌다.
- `alias_miss`는 safe allow 이유가 아니라 incident signal이다. post-issue path에서 alias miss가 나면 bounded fallback 또는 deny가 먼저다.
- cleanup 시 alias를 지울 때도 last legacy expiry만 보지 말고 quarantine/audit horizon까지 같이 본다.

중요한 점은 alias record가 "세대 간 번역"만 하는 것이 아니라,
**어느 presented token이 어떤 canonical revoke state를 봐야 하는지 결정하는 권한 경로**라는 점이다.

### 3. revoke fan-out은 canonical event가 먼저고 generation projection은 그 다음이다

좋은 revoke plane은 old/new token마다 독립 revoke event를 따로 만들지 않는다.
먼저 canonical state를 쓰고, 그 다음 generation-aware projection을 파생한다.

권장 flow:

1. canonical ledger에 `subject/session/device/family` scope와 epoch/state를 기록한다.
2. revoke event를 canonical envelope로 publish한다.
3. projector가 consumer/generation별 invalidate target을 계산한다.
4. edge cache, refresh path, session cache, support tooling이 같은 canonical state를 서로 다른 projection으로 적용한다.

예를 들어 password reset 또는 suspicious replay는 아래처럼 표현할 수 있다.

```yaml
canonical_revocation_event:
  scope:
    canonical_subject_id: "subj_42"
    canonical_session_id: "sess_9"
    canonical_family_id: "fam_c_7"
  epoch:
    subject_epoch: 18
    family_epoch: 33
  state:
    revoke_before: "2026-04-14T09:20:00Z"
    family_state: QUARANTINED
  projections:
    generations: [legacy, v2]
    cache_namespaces:
      - edge_access_legacy
      - edge_access_v2
      - refresh_lineage_legacy
      - refresh_lineage_v2
    projection_version: 8842
```

이 구조의 장점:

- revoke intent를 한 번만 기록하므로 lineage fork와 double-revoke race가 줄어든다
- consumer는 `scope + epoch` 기준으로 apply해 replay-safe하게 복구할 수 있다
- generation projection lag와 canonical ledger lag를 분리 관측할 수 있다

반대로 나쁜 설계는 아래 둘 중 하나다.

- legacy/new 시스템에 각각 revoke를 쓰고 "대충 비슷하게" 맞춘다
- every token invalidate를 실시간으로 다 쏘려다 projection backlog와 invalidate storm를 만든다

fan-out은 historical token 개수만큼 확장하는 것이 아니라,
**canonical scope와 generation namespace 조합으로 압축**하는 편이 안전하다.

### 4. consumer는 canonical state를 공유하되 projection은 계층별로 다르게 적용한다

같은 revoke라도 consumer마다 apply 방식은 다르다.

| consumer | 정상 apply 방식 | projection lag 때의 안전한 대응 |
|---|---|---|
| edge access verifier | token hash -> alias lookup -> canonical epoch compare | alias miss나 projection skew면 origin confirm 또는 route-scoped deny |
| refresh endpoint | presented refresh -> canonical family state 조회 | `QUARANTINED`/`REVOKED`면 successor issuance 금지, reauth/incident path로 승격 |
| session cache | `session_id`/`subject_id` namespace epoch bump | older namespace가 newer epoch를 덮지 못하게 `max(epoch)` apply |
| device/session inventory | canonical session/device graph 갱신 | UI는 local cache보다 canonical graph를 우선 표시 |
| support/audit tooling | legacy/new ID를 둘 다 포함한 event chain 저장 | generation별 projection 누락을 별도 fault bucket으로 표시 |

핵심은 "같은 canonical state를 봐야 한다"이지 "모든 계층이 같은 저장 방식이어야 한다"가 아니다.
projection은 consumer 최적화일 뿐이고, authority는 canonical ledger 하나만 가진다.

### 5. family quarantine는 refresh-side flag가 아니라 canonical containment 상태여야 한다

mixed-version 환경에서 family quarantine를 refresh path 로컬 상태로 두면 바로 구멍이 생긴다.

- new refresh endpoint는 `QUARANTINED`를 보고 막지만 legacy refresh endpoint는 alias를 몰라 통과시킨다
- refresh는 막혔는데 old access cache는 여전히 warm verdict를 들고 있어 고위험 route를 통과시킨다
- support tooling은 "quarantine됨"이라고 보는데 edge에는 아직 projection이 안 내려가 investigation이 꼬인다

권장 상태 전이는 아래처럼 잡는 편이 안전하다.

| state | refresh 동작 | access 동작 | release 조건 |
|---|---|---|---|
| `ACTIVE` | dual-accept 가능, target generation만 발급 | local allow/cache 정상 | 없음 |
| `MIGRATING` | legacy accept + forced reissue, single-issue 유지 | canonical epoch 비교 유지 | overlap 관측 충족 |
| `QUARANTINED` | 모든 generation에서 successor issuance 금지 | local allow-only cache 금지, high-risk route는 deny/step-up, 나머지는 bounded origin confirm | replay 증거 해소, projection lag 0, stale allow 0 |
| `REVOKED` | 모든 generation hard deny | access/session/device cache도 hard revoke | 새로운 로그인/reauth만 허용 |

여기서 `QUARANTINED`의 의미는 "조사 중이니 잠깐 refresh만 멈춤"이 아니다.
의미는 **현재 lineage를 더는 cache-only allow path로 신뢰하지 않는다**는 것이다.

즉 quarantine entry 시 즉시 일어나야 하는 일:

- canonical family state를 `QUARANTINED`로 전이
- legacy/new refresh successor issuance 전면 중단
- high-risk route의 local allow receipt 무효화
- access/session/device 관련 cache namespace 또는 epoch를 같이 올림
- reauth/step-up policy를 route risk별로 승격

### 6. quarantine release는 "이제 조용해 보인다"가 아니라 generation별 증거가 닫혀야 한다

mixed-version 환경에서 가장 위험한 오판은 quarantine clear를 너무 빨리 여는 것이다.
권장 release gate는 최소 아래를 함께 본다.

| evidence | 왜 필요한가 | 예시 지표 |
|---|---|---|
| alias health | release 직후 legacy path가 다시 miss 나지 않는가 | `alias_miss_total`, `alias_projection_backlog` |
| fan-out closure | old/new projection이 모두 같은 state를 봤는가 | `canonical_revoke_apply_p99{generation}`, `projection_epoch_skew` |
| stale allow closure | quarantine 중 local allow tail이 남지 않았는가 | `stale_allow_after_quarantine_total`, `forced_logout_probe_p99` |
| replay posture | benign duplicate와 실제 공격이 정리됐는가 | `family_quarantine_reopen_total`, `replay_after_quarantine_clear_total` |

release gate 예시는 아래처럼 잡을 수 있다.

```text
quarantine_release_eligible =
  alias_projection_backlog == 0
  and projection_epoch_skew == 0
  and stale_allow_after_quarantine_total == 0 for 2x access_ttl
  and forced_logout_probe_p99 < revoke_slo
  and no_cross_context_replay_for >= observation_window
```

즉 `QUARANTINED -> ACTIVE`는 cache 침묵만으로 열지 않는다.
**alias, projection, stale allow, replay evidence가 동시에 닫혀야 한다.**

### 7. generation coexistence에서는 regional lag recovery도 projection-aware해야 한다

revocation bus recovery를 canonical ledger backlog만으로 끝냈다고 판단하면 mixed-version 환경에서 사고가 남는다.

대표 실패 모드:

| failure mode | 보이는 증상 | 안전한 대응 |
|---|---|---|
| canonical ledger는 최신인데 legacy projection만 지연 | new verifier는 deny, legacy PoP는 allow | legacy generation namespace sweep + bounded degrade |
| alias projector가 retention gap으로 밀림 | bus lag 0인데 `alias_miss` 급증 | canonical snapshot으로 alias/projection version fast-forward |
| family fork가 감지됨 | legacy path와 new path가 서로 다른 successor를 봄 | canonical family 즉시 quarantine, successor issuance 중단 |
| refresh revoke는 닫혔는데 access cache만 남음 | refresh는 막히지만 기존 access가 high-risk route를 통과 | access cache namespace epoch bump + synthetic probe |

장시간 고립된 region을 복구할 때 필요한 snapshot도 세션 전체가 아니라
**canonical revoke truth와 generation projection watermark**여야 한다.

예:

- `subject_epoch`
- `device_epoch`
- `family_state`
- `revoke_before`
- `projection_version_by_generation`
- `last_alias_projection_at`

이렇게 해야 region이 reconnect된 뒤 old projection이 new state를 덮는 일을 막을 수 있다.

### 8. cleanup은 마지막 legacy expiry보다 revoke horizon이 더 길다

overlap window cleanup을 "last legacy token TTL 지남"으로 잡으면 보통 너무 이르다.
alias mapping과 generation projection은 revoke/audit horizon이 닫힐 때까지 남겨야 한다.

```text
cleanup_eligible_at =
  max(
    rollback_window_end,
    last_legacy_generation_seen + observation_window,
    last_alias_projection_lag_recovered_at + safety_buffer,
    last_family_quarantine_cleared_at + observation_window,
    last_generation_specific_cache_sweep_recovered_at + safety_buffer,
    audit_hold_end
  )
```

각 항목이 필요한 이유:

- `last_legacy_generation_seen + observation_window`: long-tail client가 정말 사라졌는지 보기 위해
- `last_alias_projection_lag_recovered_at + safety_buffer`: projector fault가 다시 열리지 않는지 보기 위해
- `last_family_quarantine_cleared_at + observation_window`: false clear 이후 replay 재발견을 막기 위해
- `last_generation_specific_cache_sweep_recovered_at + safety_buffer`: 한 generation cache만 뒤처진 tail을 닫기 위해

즉 cleanup은 storage 회수 타이밍이 아니라
**canonical revoke truth를 세대별로 다시 풀어 설명할 필요가 완전히 끝났는가**의 문제다.

## 실전 시나리오

### 시나리오 1: password reset이 legacy access와 new refresh가 섞인 세션에 들어왔다

문제:

- 모바일은 legacy access cache를 아직 쓰고, 웹은 new refresh lineage로 이미 승격돼 있다

해결:

- canonical subject/session/family epoch를 한 번 올린다
- projector가 legacy/new access namespace와 refresh path를 함께 invalidate한다
- any generation alias hit는 모두 같은 canonical epoch와 비교한다

핵심은 세대별 revoke를 두 번 발행하는 것이 아니라,
하나의 canonical revoke가 generation projection 둘을 닫게 만드는 것이다.

### 시나리오 2: forced reissue 후 old legacy refresh가 다른 device에서 다시 나타났다

문제:

- new generation child는 이미 발급됐고, old token이 cross-device context로 재등장했다

해결:

- `canonical_family_id` 기준으로 즉시 `QUARANTINED` 처리한다
- legacy/new refresh successor issuance를 동시에 중단한다
- high-risk access는 deny 또는 full reauth로, 일반 access는 bounded origin confirm 또는 step-up으로 올린다
- same-context benign duplicate인지가 확인되기 전까지 cache-only allow를 열지 않는다

핵심은 "old token replay니까 legacy path만 막자"가 아니라,
같은 canonical family에 속한 모든 generation을 containment 대상으로 본다는 점이다.

### 시나리오 3: APAC에서는 legacy edge projection만 늦고 new projection은 정상이다

문제:

- APAC old PoP만 stale allow를 계속 내고, origin과 new verifier는 이미 deny다

해결:

- APAC legacy namespace만 targeted sweep한다
- high-risk route는 APAC에서만 direct confirm으로 승격한다
- `canonical_revoke_apply_p99{generation="legacy",region="apac"}`와 synthetic revoke probe로 회복을 확인한다

핵심은 global failover보다 generation-scoped repair가 먼저라는 점이다.

## 코드로 보기

```pseudo
function evaluatePresentedArtifact(presentedArtifact, context):
  alias = aliasIndex.lookup(hash(presentedArtifact))
  if alias == null:
    return routePolicy.onAliasMiss(context)

  canonicalState = revokePlane.read(
    subjectId = alias.canonicalSubjectId,
    sessionId = alias.canonicalSessionId,
    familyId = alias.canonicalFamilyId
  )

  if canonicalState.familyState == "REVOKED":
    return deny("family_revoked")

  if canonicalState.familyState == "QUARANTINED":
    return routePolicy.requireOriginCheckOrReauth(context)

  if canonicalState.revokeBefore >= presentedArtifact.issuedAt:
    return deny("revoked_by_epoch")

  projector.ensureVersion(
    generation = alias.generation,
    minProjectionVersion = canonicalState.projectionVersion
  )
  return allow()
```

핵심은 consumer가 presented token 자체를 trust root로 삼지 않고,
항상 alias를 거쳐 canonical revoke state를 읽는다는 점이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| generation별 revoke table 독립 운영 | 구현이 쉬워 보인다 | lineage fork, quarantine gap, audit 분기 | 권장하지 않음 |
| canonical ledger + generation projection | correctness가 높다 | projector와 alias index 운영 비용이 든다 | mixed-version overlap가 길거나 multi-device auth가 복잡할 때 |
| quarantine를 refresh path에만 적용 | 사용자 영향이 작아 보인다 | access stale allow가 남는다 | 권장하지 않음 |
| alias miss를 origin lookup으로 항상 흡수 | correctness를 높이기 쉽다 | fallback storm와 latency 비용이 크다 | 짧은 overlap window의 low-QPS 시스템 |
| projection namespace epoch로 fan-out 압축 | invalidate storm를 줄인다 | epoch/skew 관측이 필수다 | multi-region cache tier가 있는 시스템 |

핵심은 mixed-version revoke plane의 복잡도가 토큰 형식 때문이 아니라,
**같은 canonical containment truth를 세대별 projection으로 안전하게 재현해야 하기 때문**이라는 점이다.

## 꼬리질문

> Q: alias miss가 일시적인 projection lag일 수도 있는데 allow로 보내도 되나요?
> 의도: alias miss를 단순 cache miss로 착각하지 않는지 확인
> 핵심: 아니다. overlap window의 alias miss는 revoke miss일 수 있으므로 bounded fallback 또는 deny가 먼저다.

> Q: family quarantine면 refresh만 막고 access는 access TTL 끝날 때까지 놔둬도 되나요?
> 의도: quarantine를 refresh-side flag로만 보지 않는지 확인
> 핵심: 아니다. quarantine는 cache-only allow path를 닫는 containment 상태여야 하고, 최소한 high-risk route는 즉시 막아야 한다.

> Q: revocation bus backlog가 0이면 multi-generation revoke도 회복됐다고 봐도 되나요?
> 의도: canonical ledger lag와 generation projection lag를 구분하는지 확인
> 핵심: 아니다. generation별 projection skew, stale allow probe, alias backlog까지 닫혀야 한다.

> Q: cleanup은 마지막 legacy refresh expiry만 지나면 alias mapping을 지워도 되나요?
> 의도: revoke/audit horizon을 cleanup 계산에 넣는지 확인
> 핵심: 아니다. quarantine release, projection lag recovery, audit hold까지 닫혀야 alias를 지워도 안전하다.

## 한 줄 정리

Canonical revocation plane across token generations 설계는 overlap window 동안 세대별 token ID와 cache namespace를 canonical subject/session/family truth로 접어 넣고, revoke fan-out과 family quarantine를 같은 상태 기계로 운영해 mixed-version auth rollout의 stale allow와 lineage fork를 동시에 막는 설계다.
