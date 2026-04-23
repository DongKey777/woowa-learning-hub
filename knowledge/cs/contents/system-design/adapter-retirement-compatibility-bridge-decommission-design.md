# Adapter Retirement / Compatibility Bridge Decommission 설계

> 한 줄 요약: adapter retirement와 compatibility bridge decommission 설계는 migration과 skew 대응을 위해 잠시 도입한 변환 계층을 negotiated capability, compatibility envelope, retained replay horizon, rollback boundary를 기준으로 언제 제거할지 정해 기술 부채를 줄이면서도 안전한 decommission을 만드는 운영 설계다.
>
> 문서 역할: 이 문서는 [Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md)의 joint cutover gate를 통과한 뒤, translator와 compatibility bridge를 어떤 증거로 retire할지 설명하는 decommission deep dive다.

retrieval-anchor-keywords: adapter retirement, compatibility bridge decommission, protocol adapter cleanup, bridge removal gate, deprecation traffic, adapter observability, compatibility bridge sunset, retirement soak window, adapter dependency map, decommission safety, compatibility envelope exit, capability sunset, bridge dark retirement, protocol skew cleanup, verification evidence handoff, shadow exit signal, parity exit signal, database security bridge, cutover matrix, joint bridge retirement, deprecated capability last seen, auth shadow divergence, session revoke tail, identity capability cleanup

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md)
> - [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md)
> - [Session Store / Claim-Version Cutover 설계](./session-store-claim-version-cutover-design.md)
> - [Cleanup Point-of-No-Return 설계](./cleanup-point-of-no-return-design.md)
> - [Protocol Version Skew / Compatibility 설계](./protocol-version-skew-compatibility-design.md)
> - [Capability Negotiation / Feature Gating 설계](./capability-negotiation-feature-gating-design.md)
> - [Dual-Write Avoidance / Migration Bridge 설계](./dual-write-avoidance-migration-bridge-design.md)
> - [Deploy Rollback Safety / Compatibility Envelope 설계](./deploy-rollback-safety-compatibility-envelope-design.md)
> - [Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md)
> - [Dual-Read Comparison / Verification Platform 설계](./dual-read-comparison-verification-platform-design.md)
> - [Feature Flag Control Plane 설계](./feature-flag-control-plane-design.md)

## 이 문서 다음에 보면 좋은 설계

- database authority 이동과 identity capability rollout이 함께 묶인 bridge라면 [Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md)로 돌아가 joint cutover gate의 `bridge retirement` 행을 같이 닫아야 한다.
- 실제 bridge removal change request를 쓸 때는 [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md)의 `shadow_exit_signal`, `parity_exit_signal`을 함께 인용해야 runtime disable과 code deletion이 같은 근거를 공유한다.
- claim/session translator 은퇴라면 [Session Store / Claim-Version Cutover 설계](./session-store-claim-version-cutover-design.md)까지 이어서 보면 revoke tail과 cleanup clock을 더 정확히 잡을 수 있다.
- 실제 irreversible cleanup 경계는 [Cleanup Point-of-No-Return 설계](./cleanup-point-of-no-return-design.md)로 이어진다.

## 핵심 개념

adapter와 compatibility bridge는 문제를 해결하지만 오래 두면 또 다른 문제를 만든다.

- old/new path가 계속 공존한다
- 운영자가 어느 경로가 진실인지 헷갈린다
- latent skew path가 영구화된다
- adapter 유지 비용이 커진다

하지만 너무 빨리 지우면 rollback이나 legacy compatibility가 깨진다.
즉, 핵심은 "언제 제거할 수 있는가"다.

## 깊이 들어가기

### 1. 왜 adapter가 남는가

대표 예:

- old API route를 위한 translation adapter
- old event consumer를 위한 schema bridge
- legacy DB read model을 위한 projection adapter
- old config shape를 위한 compatibility translator

이들은 처음엔 유용하지만, 시간이 지나면 invisible dependency가 된다.

### 2. Capacity Estimation

예:

- adapter를 거치는 traffic 5%
- replay/archive consumer는 여전히 old format 사용
- adapter path latency overhead 15%
- decommission 관찰 창 7일

이때 봐야 할 숫자:

- residual traffic
- adapter-only caller count
- fallback invocation rate
- bridge maintenance cost
- decommission rollback window

adapter 은퇴는 코드 삭제보다 dependency 발견이 더 어렵다.

### 3. Retirement gate

보통 다음을 만족해야 한다.

- live traffic 충분히 감소
- background batch / replay / archive 경로 확인
- old capability advertised 비율 하락
- replacement path SLO 안정
- rollback window 종료 판단

즉, "아무도 안 쓰는 것 같다"로는 부족하다.
특히 bridge가 database authority transfer와 identity capability rollout을 함께 메우는 경우에는 residual traffic만으로 retire를 열면 안 된다.
[Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md)의 joint cutover gate로 되돌아가 아래 두 축을 같이 닫아야 한다.

- database plane: backfill/drift/repair backlog가 정리됐는가
- security plane: deprecated capability last-seen, auth shadow divergence, session revoke tail이 가라앉았는가

### 4. bridge removal gate는 explicit verification exit signal을 인용해야 한다

residual traffic가 거의 0이고 deprecated capability last-seen이 오래됐더라도,
bridge removal change request에 explicit verification handoff가 없으면 adapter는 아직 retire-ready가 아니다.
가장 안전한 최소 묶음은 아래 세 줄이다.

| handoff 항목 | adapter retirement에서 확인하는 질문 | 빠지면 생기는 오판 |
|---|---|---|
| `shadow_exit_signal` | 같은 cohort에서 mirrored/live-equivalent request mix와 auth shadow decision이 이미 닫혔는가 | route/plugin wiring은 아직 흔들리는데 deprecation traffic만 낮다고 보고 hard disable을 연다 |
| `parity_exit_signal` | 같은 cohort에서 read parity와 revoke/decision parity가 닫혀 old adapter 없이도 같은 state/decision을 재현하는가 | translator를 지운 뒤 state parity나 revoke tail이 다시 열려도 원인을 설명하지 못한다 |
| `same_cohort_joined` | last-seen caller, dual-read diff, shadow divergence가 같은 join key로 이어지는가 | 서로 다른 표본을 섞어 "대충 다 green"이라고 오판한다 |

즉 adapter 문서는 [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md)에 이미 적힌
verification exit block을 받아 `runtime disable`, `hard disable`, `code removal` 순서를 여는 문서여야 한다.
둘 중 하나라도 `hold`나 `fail`이면 bridge removal은 연기하고 packet부터 다시 닫는다.

### 5. Compatibility envelope exit criteria

bridge는 단순히 "사용량이 적다"가 아니라 "호환성 계약에서 빠져도 된다"가 확인돼야 은퇴할 수 있다.

- required capability 집합에서 old capability가 제거됐는가
- optional capability miss가 더 이상 bridge를 필요로 하지 않는가
- rollback envelope가 아직 old semantic을 요구하지 않는가
- support / deprecation policy 상 skew window가 종료됐는가

즉, bridge retirement는 traffic cleanup이 아니라 compatibility envelope contract 축소다.

### 6. Dependency map

좋은 운영은 adapter 의존성을 명시한다.

- 어떤 caller가 adapter를 쓰는가
- 어떤 tenant/region이 남아 있는가
- 어떤 replay job이 old format을 쓸 수 있는가
- 어떤 config가 adapter path를 여는가

이 지도 없이 삭제하면 hidden path가 터진다.

### 7. Shadow retirement

adapter 제거는 바로 삭제보다 보통 다음 단계를 거친다.

1. new path preferred
2. adapter path dark mode
3. adapter request 관찰 및 alert
4. hard disable
5. code removal

즉, runtime disable과 code deletion은 분리하는 편이 안전하다.

### 8. Bridge decommission runbook

decommission은 보통 다음 순서로 진행한다.

1. capability / protocol deprecation 공지
2. bridge-open reason과 last-seen caller를 고정된 대시보드로 추적
3. allowlist 외 caller에 대해 dark deny를 걸고 unexpected hit를 관찰
4. replay / archive / emergency tooling을 별도 경로로 격리
5. runtime block 후 soak window를 둔다
6. [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md)의 `shadow_exit_signal`, `parity_exit_signal`, `same_cohort_joined`를 packet ref와 함께 다시 확인한다
7. [Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md)의 `bridge retirement` row를 다시 확인한다
8. point-of-no-return 승인 뒤 code와 config를 제거한다

핵심은 live path, background path, emergency rollback path를 같은 날 함께 지우지 않는 것이다.
특히 database/security bridge라면 repair backlog와 auth drift tail이 둘 다 0이고,
`shadow_exit_signal=pass`, `parity_exit_signal=pass`가 같은 cohort에서 확인되기 전에는 8단계로 넘어가면 안 된다.

### 9. Rollback과 retirement의 충돌

adapter는 rollback safety의 일부일 때가 많다.
그래서 다음을 같이 봐야 한다.

- cleanup point-of-no-return 도달 여부
- old/new mixed-version window 종료 여부
- protocol skew 잔존 여부
- correction / replay 시 old path가 필요한지 여부

adapter를 지우는 순간 일부 rollback 옵션도 함께 사라질 수 있다.

### 10. Replay / archive horizon 분리

live traffic는 0이어도 retained data horizon이 남아 있으면 bridge가 아직 필요할 수 있다.

- event retention 기간
- archive restore path
- batch reprocessing cadence
- legal / audit replay requirement

그래서 실무에서는 live bridge를 먼저 닫고, replay-only adapter를 더 작은 격리 경로로 남긴 뒤 나중에 제거하기도 한다.
이 분리가 없으면 live path 은퇴가 replay 의존성 때문에 끝없이 미뤄진다.

### 11. Retirement evidence packet

bridge를 지우기 전에 보통 다음 증거 묶음을 남긴다.

- residual traffic 추이와 last-use provenance
- explicit `shadow_exit_signal`, `parity_exit_signal`, `same_cohort_joined`
- negotiated capability 분포와 deprecated capability last-seen
- rollback envelope 평가 결과
- replay horizon 만료 또는 대체 경로 존재 증명
- joint cutover matrix의 `bridge retirement` row 재검증 결과
- dark deny 기간의 unexpected hit 알람 결과

이 패킷이 있어야 은퇴 판단이 사람 기억이 아니라 반복 가능한 운영 절차가 된다.
database repair closure와 security tail closure를 같은 approval packet으로 적는 구체적 형식은 [Bridge Retirement Evidence Packet](./bridge-retirement-evidence-packet-design.md)에서 template으로 바로 이어진다.

### 12. Observability

운영자는 다음을 봐야 한다.

- adapter hit count
- 어떤 capability mismatch가 adapter를 열었는가
- 어떤 compatibility envelope가 아직 bridge를 허용하는가
- last use timestamp
- hidden background use 여부
- removal 후 unexpected request 발생 여부
- hard deny 이후 bridge miss가 어디서 재발하는가

숫자 하나보다 provenance가 중요하다.

## 실전 시나리오

### 시나리오 1: old API translation adapter 제거

문제:

- 새 route로 모두 옮겼다고 생각하지만 일부 batch tool이 old route를 사용한다

해결:

- route-level shadow retirement를 수행한다
- adapter hit가 남는 caller를 식별한다
- disable 후 일정 기간 unexpected hit 알람을 둔다
- public API envelope에서 old capability를 optional에서 removed로 승격하기 전에 support window 종료를 확인한다

### 시나리오 2: old event consumer bridge 제거

문제:

- live consumer는 모두 새 format이지만 archive replay는 아직 old bridge를 통과한다

해결:

- replay path dependency를 먼저 분리한다
- retained event horizon을 넘긴 뒤 retirement한다
- 필요하면 replay 전용 adapter를 별도 격리한다

### 시나리오 3: config compatibility adapter 제거

문제:

- old flat config를 nested config로 번역하는 bridge를 지우고 싶다

해결:

- old binary traffic가 0인지 확인한다
- config rollback path에 adapter가 필요한지 확인한다
- remove 전에 point-of-no-return과 함께 승인한다

### 시나리오 4: mesh metadata bridge sunset

문제:

- 일부 downstream만 old trace propagation metadata를 필요로 해서 sidecar bridge가 헤더를 변환하고 있다

해결:

- 서비스별 negotiated capability 분포를 모아 old metadata 광고가 남은 서비스를 찾는다
- bridge를 dark deny로 전환해 unexpected miss를 관찰한다
- emergency rollback envelope가 새 metadata만으로도 성립하면 sidecar translation을 제거한다

## 코드로 보기

```pseudo
function retireAdapter(adapter):
  if residualTraffic(adapter) > threshold:
    reject()
  if capabilityLastSeen(adapter.legacyCapability) < deprecationGrace:
    reject()
  if !bridgeCutoverMatrixHealthy(adapter):
    reject()
  if !shadowExitSignalClosed(adapter):
    reject()
  if !parityExitSignalClosed(adapter):
    reject()
  if rollbackEnvelopeStillNeeds(adapter):
    reject()
  if replayDependencyExists(adapter):
    reject()
  disableRuntimePath(adapter)
  startRetirementObservation(adapter)
  if noUnexpectedHits(adapter):
    removeCode(adapter)

function handleRequest(req):
  if adapterDisabled(req.route):
    return newPath(req)
  return adapter.translate(req)
```

```java
public RetirementDecision decide(AdapterId adapterId) {
    AdapterUsageReport report = adapterUsageService.report(adapterId);
    CompatibilityEnvelopeReport envelope = envelopeService.report(adapterId);
    BridgeCutoverMatrix matrix = bridgeCutoverMatrixService.report(adapterId);
    BridgeRetirementPacket packet = bridgeRetirementPacketService.report(adapterId);
    return retirementGate.evaluate(report, envelope, matrix, packet);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Keep adapter indefinitely | 안전해 보인다 | 부채와 ambiguity가 늘어난다 | 임시 emergency only |
| Runtime disable then code delete | 안전하다 | 단계가 늘어난다 | 대부분의 실서비스 |
| Live bridge 제거 + replay-only 격리 | decommission을 앞당길 수 있다 | 별도 경로 관리가 필요하다 | retention이 길고 live skew는 끝난 경우 |
| Immediate removal | 단순하다 | hidden dependency에 취약하다 | 아주 작은 시스템 |
| Replay-only isolated adapter | retirement를 쉽게 한다 | 추가 경로가 생긴다 | retained event가 긴 경우 |

핵심은 adapter retirement가 cleanup의 부가 단계가 아니라 **compatibility envelope 축소, rollback safety, hidden dependency, retained replay horizon을 함께 확인하며 compatibility bridge를 종료하는 운영 설계**라는 점이다.

## 꼬리질문

> Q: live traffic가 0이면 바로 adapter를 지워도 되나요?
> 의도: hidden dependency와 retained path 고려 확인
> 핵심: 아니다. batch, replay, archive, emergency fallback이 남아 있을 수 있다.

> Q: runtime disable과 code delete를 왜 분리하나요?
> 의도: decommission safety 이해 확인
> 핵심: 먼저 disable 후 unexpected hit를 관찰해야 hidden path를 더 안전하게 찾을 수 있기 때문이다.

> Q: adapter가 남아 있으면 더 안전한 것 아닌가요?
> 의도: compatibility debt 이해 확인
> 핵심: 단기적으론 안전할 수 있지만, 장기적으로는 ambiguity와 maintenance cost, latent bug 경로를 키운다.

> Q: retirement gate에서 가장 중요한 지표는 무엇인가요?
> 의도: observability 감각 확인
> 핵심: residual live traffic뿐 아니라 deprecated capability last-seen, replay/archive dependency, rollback envelope 상태, last-use provenance를 함께 보는 것이다.

> Q: bridge를 먼저 막고 코드는 나중에 지우는 이유가 뭔가요?
> 의도: dark retirement 이해 확인
> 핵심: unexpected caller를 먼저 드러내야 hidden dependency를 찾을 수 있고, 그 결과가 code deletion 승인 근거가 되기 때문이다.

## 한 줄 정리

Adapter retirement / compatibility bridge decommission 설계는 migration과 skew 대응용 변환 계층을 residual traffic, negotiated capability, replay horizon, rollback boundary를 함께 확인하며 compatibility envelope 밖으로 안전하게 밀어내는 운영 설계다.
