---
schema_version: 3
title: Capability Sunset Gate Matrix 설계
concept_id: system-design/capability-sunset-gate-matrix-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- capability sunset gate matrix
- capability sunset
- overlap signal
- soak signal
aliases:
- capability sunset gate matrix
- capability sunset
- overlap signal
- soak signal
- cleanup signal
- downgrade decision
- dark deny
- hard reject
- deprecated capability last seen
- sunset silence window
- capability deprecation matrix
- bridge sunset decision
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/capability-negotiation-feature-gating-design.md
- contents/system-design/adapter-retirement-compatibility-bridge-decommission-design.md
- contents/system-design/cleanup-point-of-no-return-design.md
- contents/system-design/protocol-version-skew-compatibility-design.md
- contents/system-design/edge-verifier-claim-skew-fallback-design.md
- contents/system-design/verifier-overlap-hard-reject-retirement-gates-design.md
- contents/system-design/database-security-identity-bridge-cutover-design.md
- contents/system-design/bridge-retirement-evidence-packet-design.md
- contents/system-design/deploy-rollback-safety-compatibility-envelope-design.md
- contents/system-design/session-store-claim-version-cutover-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Capability Sunset Gate Matrix 설계 설계 핵심을 설명해줘
- capability sunset gate matrix가 왜 필요한지 알려줘
- Capability Sunset Gate Matrix 설계 실무 트레이드오프는 뭐야?
- capability sunset gate matrix 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Capability Sunset Gate Matrix 설계를 다루는 deep_dive 문서다. capability sunset gate matrix 설계는 deprecated capability를 제거할 때 overlap, soak, cleanup 신호를 서로 다른 강도의 증거로 읽어 `downgrade`, `dark-deny`, `hard-reject`를 순서대로 허용하는 운영 설계다. 검색 질의가 capability sunset gate matrix, capability sunset, overlap signal, soak signal처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Capability Sunset Gate Matrix 설계

> 한 줄 요약: capability sunset gate matrix 설계는 deprecated capability를 제거할 때 overlap, soak, cleanup 신호를 서로 다른 강도의 증거로 읽어 `downgrade`, `dark-deny`, `hard-reject`를 순서대로 허용하는 운영 설계다.
>
> 문서 역할: 이 문서는 [Capability Negotiation / Feature Gating 설계](./capability-negotiation-feature-gating-design.md)의 sunset 단계, [Adapter Retirement / Compatibility Bridge Decommission 설계](./adapter-retirement-compatibility-bridge-decommission-design.md)의 runtime disable 단계, [Cleanup Point-of-No-Return 설계](./cleanup-point-of-no-return-design.md)의 irreversible cleanup 단계를 하나의 gate matrix로 묶는 focused deep dive다.

retrieval-anchor-keywords: capability sunset gate matrix, capability sunset, overlap signal, soak signal, cleanup signal, downgrade decision, dark deny, hard reject, deprecated capability last seen, sunset silence window, capability deprecation matrix, bridge sunset decision, compatibility envelope exit, shadow exit signal, parity exit signal, runtime block gate, cleanup hold, legacy caller allowlist, verifier overlap, rollout soak, legacy capability cleanup

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Capability Negotiation / Feature Gating 설계](./capability-negotiation-feature-gating-design.md)
> - [Protocol Version Skew / Compatibility 설계](./protocol-version-skew-compatibility-design.md)
> - [Edge Verifier Claim-Skew Fallback 설계](./edge-verifier-claim-skew-fallback-design.md)
> - [Verifier Overlap Hard-Reject Retirement Gates 설계](./verifier-overlap-hard-reject-retirement-gates-design.md)
> - [Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md)
> - [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md)
> - [Adapter Retirement / Compatibility Bridge Decommission 설계](./adapter-retirement-compatibility-bridge-decommission-design.md)
> - [Cleanup Point-of-No-Return 설계](./cleanup-point-of-no-return-design.md)
> - [Deploy Rollback Safety / Compatibility Envelope 설계](./deploy-rollback-safety-compatibility-envelope-design.md)
> - [Session Store / Claim-Version Cutover 설계](./session-store-claim-version-cutover-design.md)
> - [Security: Authorization Runtime Signals / Shadow Evaluation](../security/authorization-runtime-signals-shadow-evaluation.md)

## 이 문서 다음에 보면 좋은 설계

- capability set 협상과 compatibility envelope 자체를 먼저 다시 잡으려면 [Capability Negotiation / Feature Gating 설계](./capability-negotiation-feature-gating-design.md)부터 읽는 편이 좋다.
- verifier overlap, shadow/parity, security tail을 database repair와 같은 cohort로 묶으려면 [Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md)와 [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md)을 함께 보면 된다.
- bounded fallback을 언제 내리고 hard reject로 올릴지 edge/runtime 관점의 문턱만 따로 보고 싶다면 [Verifier Overlap Hard-Reject Retirement Gates 설계](./verifier-overlap-hard-reject-retirement-gates-design.md)로 이어서 보면 된다.
- runtime block 이후 bridge 은퇴 절차를 실제 runbook으로 내리려면 [Adapter Retirement / Compatibility Bridge Decommission 설계](./adapter-retirement-compatibility-bridge-decommission-design.md)로 이어서 보면 된다.
- hard reject 뒤 code/config/schema cleanup까지 닫으려면 [Cleanup Point-of-No-Return 설계](./cleanup-point-of-no-return-design.md)와 [Deploy Rollback Safety / Compatibility Envelope 설계](./deploy-rollback-safety-compatibility-envelope-design.md)를 같이 보는 편이 안전하다.

## 핵심 개념

capability sunset에서 가장 흔한 오판은 세 가지 결정을 같은 세기로 취급하는 것이다.

- `downgrade`는 overlap 기간의 가용성 보호 수단이다.
- `dark-deny`는 hidden caller를 드러내는 soak 수단이다.
- `hard-reject`는 cleanup-ready contract를 강제하는 종료 수단이다.

즉 결정 강도는 증거 강도를 넘으면 안 된다.
overlap 신호만 있는데 `hard-reject`를 열면 false outage가 나고,
cleanup 신호 없이 `code removal`까지 가면 rollback 근거를 태워 버린다.

## 깊이 들어가기

### 1. 왜 sunset에도 별도 gate matrix가 필요한가

capability rollout 문서에서는 보통 "언제 advertise하고 언제 retire하나"를 다루지만,
실전 운영은 그 사이의 decision ladder가 더 중요하다.

- mixed-version caller가 아직 남아 있으면 availability를 위해 낮춰 받아야 한다.
- expected caller는 다 닫혔지만 hidden long-tail이 의심되면 deny probe를 걸어야 한다.
- repair/security/access tail이 모두 닫혔고 rollback closure가 명시됐을 때만 최종 reject를 열 수 있다.

즉 sunset 판단은 트래픽 감소 그래프 하나가 아니라, overlap clock, soak clock, cleanup clock을 따로 읽는 문제다.

### 2. Compact gate table

| 결정 | overlap 신호 | soak 신호 | cleanup 신호 | 이 결정을 쓰는 이유 |
|---|---|---|---|---|
| `downgrade` | verifier/JWKS/parser overlap이 열려 있고 mixed-version caller가 의도적으로 남아 있다 | 아직 불충분하거나 시작 전이다 | 아직 없음 | 새 contract를 강제하지 않고 availability를 지키기 위해 |
| `dark-deny` | critical divergence는 0이고 expected caller migration은 끝났다 | `shadow_exit_signal=pass`, `parity_exit_signal=pass`, unexpected hit alarm이 준비됐고 residual caller가 allowlist long-tail로 좁혀졌다 | rollback handle과 cleanup hold는 아직 살아 있다 | hidden caller를 드러내되 irreversible cleanup은 미루기 위해 |
| `hard-reject` | overlap advertise/accept가 완전히 닫혔다 | dark-deny soak 동안 unexpected hit가 0이고 required silence window를 채웠다 | `deprecated_capability_last_seen_at`이 cohort 기준으로 닫혔고 repair/revoke/access tail이 SLO 안이며 bridge retirement packet이 approve-candidate다 | 최종 contract를 강제하고 adapter/code cleanup을 열기 위해 |

핵심은 `dark-deny`가 `hard-reject`의 약한 표현이 아니라,
서로 다른 질문에 답하는 별도 gate라는 점이다.

### 3. overlap 신호는 "아직 낮춰서라도 받아야 하는가"를 묻는다

`downgrade`를 유지해야 하는 대표 조건은 아래와 같다.

- verifier overlap이 열려 있어 old/new claim 또는 capability를 둘 다 읽는다
- mobile, edge, batch, replay처럼 long-tail caller가 아직 support window 안에 있다
- fallback hit ratio가 예상 envelope 안에 있고 critical divergence는 0이다
- emergency rollback envelope가 아직 old semantic을 요구한다

이 단계에서 중요한 것은 "old capability가 아직 보인다"보다
"그 old capability를 보는 것이 현재 정책상 정상인가"다.
정상 overlap인데 `dark-deny`를 먼저 열면 sunset이 아니라 self-inflicted incident가 된다.

### 4. soak 신호는 "예상 caller는 닫혔고 숨어 있는 caller만 남았는가"를 묻는다

`dark-deny`는 migration이 끝났다고 선언하는 단계가 아니라,
runtime path를 더 강하게 막아 hidden dependency를 찾는 단계다.

대표 soak 조건:

- `shadow_exit_signal=pass`
- `parity_exit_signal=pass`
- `same_cohort_joined=true`
- residual caller provenance가 allowlist나 emergency tooling으로 좁혀짐
- `unexpected_dark_deny_hit_total`을 볼 수 있는 알람/대시보드가 준비됨
- cleanup change는 아직 비활성화돼 있어 deny hit가 나와도 되돌릴 손잡이가 남아 있음

즉 `dark-deny`는 bridge를 지우는 단계가 아니라,
bridge 없이도 실제 운영이 버티는지 probe 하는 단계다.
여기서 hit가 다시 나오면 `downgrade`나 scoped allowlist로 한 단계 내려가면 된다.

### 5. cleanup 신호는 "runtime reject를 irreversible cleanup으로 넘겨도 되는가"를 묻는다

`hard-reject`는 단순 runtime policy change가 아니라 cleanup 직전 contract closure다.
그래서 아래처럼 repair/security/rollback 신호를 함께 읽어야 한다.

- `deprecated_capability_last_seen_at` 또는 `legacy_principal_last_seen_at`이 required silence window를 충족한다
- `replay_backlog=0`, `cdc_gap_backlog=0`, `drift_bucket_critical=0`처럼 data repair tail이 닫혀 있다
- `session_revoke_tail_p99_sec`, `last_access_after_deprovision_sec_p99`, `old_root_last_seen_at`이 SLO 안이다
- [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md)의 `overall_decision=approve-candidate`이고 `shadow_exit_signal`, `parity_exit_signal`, `same_cohort_joined`가 그대로 인용 가능하다
- rollback boundary가 `rollback-closed`로 명시됐지만, point-of-no-return change request는 아직 별도 승인 전이다

중요한 점은 `hard-reject`가 cleanup과 같은 말이 아니라는 점이다.
보통은 `hard-reject`를 먼저 열고 soak을 한 번 더 본 뒤,
마지막에 code/config/schema cleanup을 연다.

### 6. gate precedence는 항상 약한 결정부터 강한 결정 순으로 읽는다

실전 decision precedence는 보통 아래처럼 단순하게 유지하는 편이 안전하다.

1. overlap이 열려 있으면 `downgrade`
2. overlap은 닫혔지만 cleanup 증거가 아직 부족하면 `dark-deny`
3. soak과 cleanup 증거가 모두 닫혔을 때만 `hard-reject`

이를 뒤집어 `hard-reject`를 먼저 열고 문제 없으면 cleanup한다고 생각하면 안 된다.
그 접근은 dark-deny가 제공하는 "hidden caller 발견" 단계를 통째로 건너뛴다.

### 7. 세 신호 묶음은 같은 cohort/join key를 공유해야 한다

sunset gate matrix는 표만 그려 놓으면 끝나는 문서가 아니다.
각 신호가 같은 cohort를 가리키는지 확인해야 한다.

- 같은 tenant/region/route epoch인가
- 같은 claim schema version 또는 capability generation인가
- 같은 decision log key / request cohort인가
- 같은 observation window인가

이 join이 깨지면 `deprecated_capability_last_seen_at`은 tenant A에서 가져오고,
`replay_backlog=0`은 tenant B에서 가져와 "대충 다 green"처럼 오판하게 된다.
그래서 bridge retirement packet의 join key를 sunset gate matrix가 그대로 재사용하는 편이 안전하다.

## 실전 시나리오

### 시나리오 1: public API capability sunset

문제:

- mobile app 일부가 old filter capability를 아직 보내고 있다

해결:

- app store long-tail이 남아 있는 동안은 `downgrade`로 old representation을 유지한다
- support window가 끝난 뒤에는 allowlist 외 caller를 `dark-deny`로 막아 unexpected hit를 찾는다
- stale client silence window가 충족되고 deny hit가 0이면 `hard-reject`로 올린다

### 시나리오 2: service-to-service claim capability sunset

문제:

- workload identity rollout은 끝났지만 일부 support tool이 legacy principal claim을 아직 사용한다

해결:

- verifier overlap과 auth shadow divergence를 보는 동안은 `downgrade` 또는 bridge path를 유지한다
- expected service caller가 모두 새 principal로 옮겨간 뒤 support tool만 allowlist로 남기고 `dark-deny` soak을 건다
- `legacy_principal_last_seen_at`, revoke/access tail, bridge packet approval이 모두 닫히면 `hard-reject`로 전환한다

### 시나리오 3: live path는 닫혔지만 replay horizon이 남는다

문제:

- live request에서는 old capability가 보이지 않지만 archive replay job이 아직 old translator를 통과한다

해결:

- live path에는 `dark-deny`를 걸어 hidden caller를 먼저 없앤다
- replay adapter는 격리된 별도 envelope로 남겨 `hard-reject` 범위를 live path로만 한정한다
- retained horizon이 끝난 뒤 전체 cleanup gate를 다시 열어 final reject와 code removal을 함께 진행한다

## 코드로 보기

```pseudo
function decideSunsetAction(scope):
  if scope.overlap.verifierOverlapOpen or
     scope.overlap.mixedVersionCallerRatio > 0 or
     scope.overlap.rollbackEnvelopeRequiresLegacy:
    return downgrade(scope.defaultFallback)

  if !scope.soak.shadowExitPass or
     !scope.soak.parityExitPass or
     !scope.soak.sameCohortJoined:
    return downgrade(scope.defaultFallback)

  if !scope.cleanup.requiredSilenceWindowMet or
     scope.cleanup.replayBacklog > 0 or
     scope.cleanup.revokeTailGtSlo > 0 or
     !scope.cleanup.bridgePacketApproveCandidate:
    return darkDeny(scope.allowlist)

  return hardReject()
```

```yaml
capability_sunset_gate:
  capability: legacy-claim-v2
  overlap:
    verifier_overlap_open: false
    mixed_version_caller_ratio: 0.0
    rollback_envelope_requires_legacy: false
  soak:
    shadow_exit_signal: pass
    parity_exit_signal: pass
    same_cohort_joined: true
    dark_deny_unexpected_hit_total: 0
  cleanup:
    required_silence_window_minutes: 1440
    required_silence_window_met: true
    deprecated_capability_last_seen_at: 2026-04-13T07:10:00Z
    replay_backlog: 0
    revoke_tail_gt_slo: 0
    bridge_packet_approve_candidate: true
  decision: hard-reject
```

핵심은 `traffic=0`만으로 결정하지 않고,
overlap, soak, cleanup 신호를 차례대로 좁혀 가며 decision 강도를 올리는 것이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `downgrade` 오래 유지 | availability가 좋다 | legacy path 비용이 길게 남는다 | long-tail client/support window가 길 때 |
| `dark-deny` soak | hidden caller를 실전에서 찾을 수 있다 | 알람과 oncall 대응이 필요하다 | bridge retirement 직전 |
| `hard-reject` 빠르게 전환 | cleanup 속도가 빨라진다 | rollback 근거를 빨리 태울 수 있다 | internal caller만 있고 증거가 이미 충분할 때 |
| live/replay gate 분리 | live sunset을 먼저 끝낼 수 있다 | envelope가 하나 더 생긴다 | retained replay horizon이 길 때 |

## 꼬리질문

> Q: deprecated capability last-seen이 0이면 바로 hard reject해도 되나요?
> 의도: silence window와 join key의 필요성 확인
> 핵심: 아니다. same cohort 기준의 silence window, replay/revoke/access tail, bridge packet approval까지 같이 닫혀야 한다.

> Q: dark-deny와 hard-reject의 차이는 결국 allowlist 유무 아닌가요?
> 의도: soak 단계의 의미 확인
> 핵심: allowlist 자체보다 rollback handle과 cleanup hold가 아직 살아 있는지가 더 중요하다. dark-deny는 probe이고 hard-reject는 final contract다.

> Q: cleanup approval을 받았으면 dark-deny는 생략해도 되나요?
> 의도: 단계 생략의 위험 이해 확인
> 핵심: hidden caller를 실제로 드러내는 단계가 사라지므로 위험하다. 매우 짧은 skew의 내부 시스템이 아니면 dark-deny soak을 두는 편이 안전하다.

## 한 줄 정리

Capability sunset gate matrix 설계는 overlap, soak, cleanup 신호를 같은 cohort 기준으로 읽어 `downgrade`에서 `dark-deny`, `hard-reject`까지 decision 강도를 순서대로 올리는 sunset 운영 설계다.
