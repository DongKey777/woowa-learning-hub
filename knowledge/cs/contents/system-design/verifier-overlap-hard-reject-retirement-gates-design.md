# Verifier Overlap Hard-Reject Retirement Gates 설계

> 한 줄 요약: verifier overlap hard-reject retirement gates 설계는 bounded fallback으로 overlap을 버틴 뒤, `dark-observe`, scoped canary, hard reject, cleanup handoff를 분리해 unknown claim fallback을 종료하면서도 rollback 손잡이는 마지막까지 보존하는 은퇴 운영 설계다.
>
> 문서 역할: 이 문서는 [Edge Verifier Claim-Skew Fallback 설계](./edge-verifier-claim-skew-fallback-design.md)의 bounded fallback 종료 지점, [Capability Sunset Gate Matrix 설계](./capability-sunset-gate-matrix-design.md)의 `dark-deny -> hard-reject` ladder, [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md)의 approval packet 사이를 메우는 focused deep dive다.

retrieval-anchor-keywords: verifier overlap hard reject retirement gates, verifier overlap drain, bounded fallback retirement, parser dark observe, legacy parser hard reject, overlap drained cutoff, fallback disable sequencing, rollback safe reject rollout, identity edge retirement, origin introspection fallback retirement, deprecated claim hard reject, verifier class region route gate, dark observe silence window, emergency re-enable handle, bridge retirement packet handoff, cleanup before code deletion, background caller cadence gate, revocation tail before hard reject

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Edge Verifier Claim-Skew Fallback 설계](./edge-verifier-claim-skew-fallback-design.md)
> - [Session Store / Claim-Version Cutover 설계](./session-store-claim-version-cutover-design.md)
> - [Capability Sunset Gate Matrix 설계](./capability-sunset-gate-matrix-design.md)
> - [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md)
> - [Adapter Retirement / Compatibility Bridge Decommission 설계](./adapter-retirement-compatibility-bridge-decommission-design.md)
> - [Cleanup Point-of-No-Return 설계](./cleanup-point-of-no-return-design.md)
> - [Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md)
> - [Refresh Reauth Escalation Matrix 설계](./refresh-reauth-escalation-matrix-design.md)
> - [Trust-Bundle Rollback During Cell Cutover 설계](./trust-bundle-rollback-during-cell-cutover-design.md)
> - [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)

## 이 문서 다음에 보면 좋은 설계

- overlap 동안 fallback을 어떻게 흡수하는지부터 다시 잡으려면 [Edge Verifier Claim-Skew Fallback 설계](./edge-verifier-claim-skew-fallback-design.md)를 먼저 읽는 편이 좋다.
- sunset ladder 전체를 broader capability 관점으로 보고 싶다면 [Capability Sunset Gate Matrix 설계](./capability-sunset-gate-matrix-design.md)로 이어서 보면 된다.
- hard reject를 retirement approval packet과 같은 cohort로 닫으려면 [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md)과 [Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md)를 같이 본다.
- hard reject 뒤 parser/code/config 삭제까지 넘기려면 [Adapter Retirement / Compatibility Bridge Decommission 설계](./adapter-retirement-compatibility-bridge-decommission-design.md)와 [Cleanup Point-of-No-Return 설계](./cleanup-point-of-no-return-design.md)로 이어서 내려가면 된다.

## 핵심 개념

verifier overlap이 drain됐다고 해서 곧바로 hard reject로 올리면 안 된다.
여기서 자주 생기는 오판은 두 가지다.

- fallback traffic이 거의 0이니 legacy parser를 바로 reject해도 된다고 보는 것
- hard reject를 열었으니 parser code/config도 같은 wave에서 지워도 된다고 보는 것

둘 다 위험하다.
첫 번째는 hidden background caller, revoke tail, long-tail PoP를 outage로 찾게 만든다.
두 번째는 rollback 손잡이를 hard reject 검증 전에 태워 버린다.

그래서 안전한 ladder는 아래처럼 분리된다.

1. `bounded fallback`으로 overlap을 흡수한다.
2. overlap drain이 확인되면 fallback을 normal path에서 내리고 `dark-observe`로 바꾼다.
3. scoped canary로 reject를 실전 traffic에 좁게 걸어 hidden caller를 확인한다.
4. hard reject를 연다.
5. 별도 point-of-no-return 승인 뒤 code/config 삭제를 연다.

즉 이 문서의 질문은 "언제 reject할 수 있는가"보다
"**어떤 증거가 쌓일 때 fallback 종료, reject 전환, cleanup handoff를 각각 분리할 것인가**"다.

## 깊이 들어가기

### 1. overlap 종료와 hard reject는 서로 다른 사건이다

`overlap drained`는 dual-accept와 origin fallback을 normal path에서 내릴 수 있느냐를 묻는다.
`hard reject ready`는 legacy semantic을 live path에서 incident bucket으로 올려도 revoke/access/rollback tail이 다시 열리지 않느냐를 묻는다.

둘을 같은 change set으로 묶으면 다음 문제가 생긴다.

- overlap 종료 증거는 있는데 support tool이나 daily batch가 아직 legacy parser를 친다
- foreground read는 green인데 SCIM close나 device revoke tail이 하루 뒤에 다시 열린다
- reject는 안전했더라도 긴급 rollback 때 legacy parser를 다시 켤 수단을 같이 지워 버린다

즉 overlap drain은 `bounded fallback retirement`의 기준이고,
hard reject는 `runtime contract closure`의 기준이다.

### 2. 판단 단위는 global average가 아니라 가장 느린 조합이다

게이트는 전체 평균이 아니라 아래 축의 최악값으로 읽어야 한다.

- verifier class
- region / PoP
- route risk class
- caller class

대표 조합 예:

- `edge-pop / ap-northeast-2 / FALLBACK_BOUNDED / foreground-read`
- `api-gateway / us-east-1 / LOCAL_STRICT / admin-write`
- `background-verifier / eu-west-1 / batch-read / replay-worker`

평균 `unknown_claim_rate`가 0에 가까워도, daily replay worker 한 군데가 legacy claim을 계속 내면 overlap은 닫힌 것이 아니다.
실제 retirement object는 `scope = verifier_class × region × route_risk_class × caller_class`처럼 잡는 편이 안전하다.

### 3. 권장 상태 머신은 다섯 단계다

| 단계 | live path 동작 | legacy parser 상태 | rollback 손잡이 | 다음 단계로 가는 질문 |
|---|---|---|---|---|
| `bounded-fallback` | trusted-but-unknown claim을 origin introspection으로 승격 | normal accept path 일부 | full | overlap을 계속 흡수해야 하는가 |
| `dark-observe` | normal path fallback off, unknown legacy hit는 log/metric만 남김 | observe-only | full | fallback 없이도 traffic가 안정적인가 |
| `scoped-reject-canary` | 일부 scope에만 reject를 실전 적용 | reject on canary scope, observe elsewhere | full | hidden caller가 없는가 |
| `hard-reject` | live path 전체 reject | emergency allowlist/synthetic-only | limited but still present | cleanup 전 soak이 충분한가 |
| `cleanup-handoff` | reject 유지 | code/config deletion 대기 | no fast rollback after PONR | parser/code 삭제를 열어도 되는가 |

핵심은 `dark-observe`와 `scoped-reject-canary`를 생략하지 않는 것이다.
이 두 단계가 있어야 hidden caller를 outage 전에 찾고, reject 성공과 cleanup 가능성을 분리할 수 있다.

### 4. overlap drain gate는 fallback을 normal path에서 내려도 되는지를 증명해야 한다

권장 overlap drain floor는 아래 정도다.

| 신호 | 기본 floor(예시) | 이유 |
|---|---|---|
| `unknown_claim_rate` | 각 scope에서 `<= 0.1%` | fallback이 exceptional path로 내려왔는지 확인 |
| `verifier_divergence_total` | `0` for 30m | parser semantic mismatch가 남아 있지 않아야 함 |
| `fallback_queue_drop_total` | `0` for 30m | capacity incident가 overlap 종료를 가리지 않게 함 |
| `origin_fallback_timeout_total` | `0` for 30m | fallback을 끄기 전에 이미 timeout성 tail이 없어야 함 |
| `organic_legacy_parser_last_seen` | `>= 30m` silence | synthetic/test가 아닌 실제 live hit가 멈췄는지 확인 |
| `rollback_reenable_ready` | `true` | 필요 시 fallback을 수분 내 재활성화할 수 있어야 함 |

이 문턱을 넘으면 하는 일은 "바로 reject"가 아니다.
액션은 아래 두 개뿐이다.

- normal path의 bounded fallback을 끈다
- legacy parser를 `dark-observe` 또는 synthetic probe 전용으로 내린다

즉 overlap drain은 fallback shutdown gate이지, legacy contract removal gate가 아니다.

### 5. hard reject gate는 security tail과 retirement packet을 같이 닫아야 한다

hard reject는 아래 신호가 모두 같은 cohort로 모일 때만 연다.

| 축 | 요구 신호 | 이유 |
|---|---|---|
| overlap closure | overlap drain floor 유지 | fallback을 내린 뒤에도 다시 열리지 않는지 확인 |
| dark observe silence | `unexpected_legacy_claim_total = 0` for 24h | foreground long-tail caller를 한 주기 이상 본다 |
| live silence | `deprecated_claim_last_seen_at` silence `>= 72h` | stale client, support tool, low-frequency caller를 잡는다 |
| revoke/access tail | `revocation_tail_gt_slo = 0` and `last_access_after_deprovision_gt_slo = 0` for 48h | revoke/SCIM tail이 다시 열리지 않아야 한다 |
| background cadence | `legacy_background_hit = 0` for `1 full job cadence` | 하루 한 번 도는 worker를 놓치지 않기 위해 |
| retirement approval | bridge retirement packet `overall_decision = approve-candidate` | repair plane, security plane, verification exit가 같은 packet으로 닫혀야 함 |
| rollback boundary | fast re-enable path still available, code deletion not started | reject 검증 중 rollback 손잡이를 보존해야 함 |

중요한 점은 `deprecated_claim_last_seen_at = null` 하나만으로 hard reject를 열지 않는 것이다.
그 값은 live foreground silence만 보여 줄 수 있고, revoke tail이나 batch cadence는 별도 시계다.

### 6. 시간을 고정한 계산식이 있어야 운영자가 감으로 밀지 않는다

실전에서는 아래처럼 시각을 명시적으로 계산해 두는 편이 좋다.

```text
overlap_drained_at =
  max(
    last_unknown_claim_rate_above_floor_at + 30m,
    last_verifier_divergence_at + 30m,
    last_fallback_queue_drop_at + 30m,
    last_origin_fallback_timeout_at + 30m,
    last_organic_legacy_parser_hit_at + 30m
  )
```

```text
hard_reject_ready_at =
  max(
    overlap_drained_at + 24h,
    last_unexpected_legacy_claim_at + 24h,
    last_deprecated_claim_seen_at + 72h,
    last_revocation_tail_gt_slo_at + 48h,
    last_access_after_deprovision_gt_slo_at + 48h,
    last_background_legacy_hit_at + 1 full job cadence,
    bridge_packet_approve_candidate_at,
    rollback_window_still_open_at
  )
```

여기서 각 시간이 답하는 질문은 아래와 같다.

- `30m`: parser/JWKS/config fan-out이 실제로 가라앉았는가
- `24h`: 피크/비피크 foreground traffic가 한 번씩 지났는가
- `72h`: 저빈도 human caller와 support tooling까지 quiet한가
- `48h`: revoke, password reset, device logout, SCIM close 같은 security tail이 다시 안 열리는가
- `1 full job cadence`: background/replay/support path가 최소 한 번은 돌았는가

즉 hard reject는 단일 silence window가 아니라 여러 잔존 시계의 최대값으로 열린다.

### 7. rollback-safe sequencing은 runtime flag와 cleanup wave를 분리해야 한다

가장 안전한 순서는 아래와 같다.

1. `bounded fallback` 유지
2. overlap drain floor 충족
3. config/flag로 fallback off, parser는 `dark-observe`
4. scoped canary에서 reject 적용
5. hard reject global rollout
6. reject soak 완료
7. point-of-no-return 승인
8. parser code/config/trust bundle 삭제

여기서 절대 같이 묶지 말아야 하는 change는 다음이다.

- fallback disable + parser binary deletion
- hard reject enable + trust bundle root removal
- hard reject enable + emergency allowlist disable

이들을 분리해야 하는 이유:

- fallback disable은 reversible runtime change다
- hard reject는 reversible이지만 incident 대응이 필요한 contract change다
- code/config 삭제는 fast rollback을 잃는 irreversible change다

즉 reject까지는 control plane 조작으로 되돌릴 수 있어야 하고,
cleanup은 그 다음 wave에서만 열어야 한다.

### 8. scoped canary는 route risk가 아니라 rollback blast radius 순으로 여는 편이 안전하다

권장 rollout 순서는 보통 아래와 같다.

1. synthetic / shadow-only scope
2. internal low-blast-radius foreground read
3. external low-risk authenticated read
4. background worker / replay path
5. admin, support, high-value tenant scope

이 순서를 쓰는 이유는 "보안상 중요하니 admin write부터 reject"가 아니라,
incident가 났을 때 가장 빨리 되돌릴 수 있는 순서로 gate를 연다는 데 있다.
이미 `LOCAL_STRICT`여서 fallback이 없던 고위험 route는 별도지만,
`FALLBACK_BOUNDED`였던 경로의 retirement는 blast radius 기준으로 여는 편이 운영상 더 안전하다.

### 9. hard reject 뒤에도 emergency lane은 별도 TTL로 살아 있어야 한다

hard reject는 "누구도 legacy를 못 쓴다"가 아니라,
"정상 live path에서는 legacy를 더 이상 지원하지 않는다"는 뜻에 가깝다.
그래서 보통 아래 예외는 별도 TTL을 둔다.

- synthetic probe
- break-glass support session
- isolated replay repair worker
- rollback validation canary

단, 이 예외는 product traffic allowlist가 아니라 **incident lane**이어야 한다.
요구 조건:

- ticket / approval reference 필수
- 짧은 TTL
- scope 고정
- hit count와 provenance 별도 로깅

그렇지 않으면 emergency lane이 곧 hidden dependency shelter가 된다.

### 10. approval packet에는 reject-ready를 별도 필드로 남겨야 downstream이 재계산하지 않는다

retirement packet이나 change request에는 아래 필드를 명시하는 편이 좋다.

```yaml
verifier_retirement_gate:
  scope: edge-pop/ap-northeast-2/FALLBACK_BOUNDED/foreground-read
  overlap_drained_at: 2026-04-14T01:30:00Z
  fallback_mode: dark-observe
  unexpected_legacy_claim_total_24h: 0
  deprecated_claim_silence_hours: 79
  revocation_tail_gt_slo_48h: 0
  access_after_deprovision_gt_slo_48h: 0
  background_job_cadence_satisfied: true
  emergency_reenable_ready: true
  bridge_packet_ref: brp-tenant42-2026-04-14
  bridge_packet_decision: approve-candidate
  hard_reject_ready: true
  code_deletion_ready: false
```

이렇게 두면 downstream 문서가 raw dashboard를 다시 조합하지 않아도 된다.
중요한 점은 `hard_reject_ready=true`와 `code_deletion_ready=false`가 동시에 가능하다는 것이다.
바로 이 분리가 rollback-safe sequencing의 핵심이다.

## 실전 시나리오

### 시나리오 1: foreground는 quiet하지만 nightly replay가 legacy parser를 친다

문제:

- 낮 시간 traffic에서는 legacy claim hit가 보이지 않는다
- 하지만 nightly replay job이 하루에 한 번 old parser를 통해 archive token을 읽는다

해결:

- overlap drain은 통과할 수 있어도 hard reject는 `1 full job cadence`를 다시 채워야 한다
- live path는 `dark-observe`로 내리고 replay worker는 isolated canary로 먼저 reject를 테스트한다
- replay adapter 대체 또는 별도 envelope 분리 전에는 global hard reject를 열지 않는다

### 시나리오 2: fallback은 사라졌는데 revoke tail이 이틀 뒤 다시 튄다

문제:

- unknown claim fallback은 0이 됐지만 password reset 뒤 특정 region에서 stale allow가 다시 나온다

해결:

- overlap drain은 유지하되 hard reject gate는 닫아 둔다
- `revocation_tail_gt_slo = 0 for 48h`를 다시 채운 뒤에만 reject를 재시도한다
- incident 동안에는 parser 문제가 아니라 revoke fan-out path가 문제임을 명시해 remediation scope를 분리한다

### 시나리오 3: hard reject는 안전했지만 code deletion을 같은 날 하려 한다

문제:

- hard reject canary와 global rollout이 모두 조용해서 parser package와 trust bundle root를 같은 maintenance window에서 삭제하려 한다

해결:

- reject soak과 point-of-no-return 승인을 분리한다
- binary/config 삭제는 다음 wave에서 수행한다
- 삭제 전까지는 fast re-enable flag, emergency allowlist, legacy metrics를 유지한다

## 코드로 보기

```pseudo
function decideVerifierRetirement(scope):
  if !scope.overlapDrainFloorMet:
    return keepBoundedFallback()

  if scope.mode == "bounded-fallback":
    return disableFallbackKeepDarkObserve()

  if !scope.darkObserveSilence24h:
    return keepDarkObserve()

  if !scope.revocationTailStable48h or
     !scope.deprecatedClaimSilence72h or
     !scope.backgroundCadenceSatisfied or
     !scope.bridgePacketApproveCandidate:
    return scopedRejectCanary(scope.lowBlastRadiusSubset)

  if !scope.emergencyReenableReady or scope.codeDeletionStarted:
    return hold("rollback handle missing")

  return hardReject()
```

```yaml
verifier_retirement:
  scope: edge/global/FALLBACK_BOUNDED
  overlap:
    unknown_claim_rate_floor_met: true
    verifier_divergence_total_30m: 0
    fallback_queue_drop_total_30m: 0
    organic_legacy_parser_silence_minutes: 47
  dark_observe:
    unexpected_legacy_claim_total_24h: 0
    canary_reject_hit_total: 0
  tails:
    deprecated_claim_silence_hours: 80
    revocation_tail_gt_slo_48h: 0
    access_after_deprovision_gt_slo_48h: 0
    background_cadence_satisfied: true
  rollback:
    emergency_reenable_ready: true
    code_deletion_started: false
    point_of_no_return_ready: false
  retirement_packet:
    ref: brp-tenant42-2026-04-14
    decision: approve-candidate
  action: hard-reject
```

핵심은 hard reject를 "기능 제거"가 아니라 `rollback handle을 남긴 runtime contract closure`로 다루는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| overlap drain 직후 hard reject | 복잡도를 빨리 줄인다 | hidden caller와 revoke tail을 outage로 찾기 쉽다 | verifier surface가 매우 작고 background path가 없을 때만 |
| `dark-observe` 유지 | rollback이 쉽다 | legacy parser 운영 비용이 더 남는다 | mixed caller inventory가 완전하지 않을 때 |
| scoped reject canary | hidden caller를 좁은 범위에서 찾을 수 있다 | 운영 단계가 하나 더 생긴다 | edge/identity/runtime가 여러 팀에 걸쳐 있을 때 |
| hard reject와 code deletion 분리 | fast rollback 보존 | cleanup이 느려진다 | 대부분의 production retirement |

## 꼬리질문

> Q: `unknown_claim_rate = 0`이면 hard reject로 바로 올려도 되나요?
> 의도: overlap drain과 hard reject 차이 확인
> 핵심: 아니다. revoke/access tail, background cadence, retirement packet approval, rollback handle 보존까지 같이 닫혀야 한다.

> Q: hard reject를 열었으면 parser code도 같은 날 지워도 되나요?
> 의도: runtime reject와 irreversible cleanup 구분 확인
> 핵심: 아니다. hard reject는 reversible runtime gate이고, code deletion은 point-of-no-return 이후 별도 wave다.

> Q: emergency allowlist가 남아 있으면 hard reject가 아니지 않나요?
> 의도: incident lane와 product fallback 차이 확인
> 핵심: product traffic을 위한 bounded fallback은 종료돼야 하지만, ticketed emergency lane은 별도 TTL로 남길 수 있다. 다만 정상 caller shelter가 되면 안 된다.

## 한 줄 정리

Verifier overlap hard-reject retirement gates 설계는 overlap drain, dark-observe silence, revoke/access tail closure, retirement packet approval, cleanup handoff를 분리해 bounded fallback 종료와 hard reject 전환을 같은 날의 무리한 cleanup으로 엮지 않는 identity edge 은퇴 운영 설계다.
