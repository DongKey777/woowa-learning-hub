# Cleanup Point-of-No-Return 설계

> 한 줄 요약: cleanup point-of-no-return 설계는 migration이나 cutover 이후 old path, old schema, old protocol, old infra를 언제 제거하면 rollback이 사실상 불가능해지는지 명확히 정의해, cleanup 작업을 운영적으로 안전하게 분리하는 설계다.
>
> 문서 역할: 이 문서는 [Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md) 이후 cleanup이 database authority rollback 근거와 identity rollback 근거를 언제 동시에 닫는지 설명하는 cleanup deep dive다.

retrieval-anchor-keywords: cleanup point of no return, contract phase, irreversible cleanup, rollback boundary, destructive cleanup, decommission safety, cleanup freeze, post cutover cleanup, removal gate, irreversible migration, adapter retirement, verification evidence handoff, shadow exit signal, parity exit signal, write freeze rollback window, database security bridge, cutover matrix, auth drift cleanup, deprecated capability retirement, session revoke tail cleanup, bridge cleanup gate, dedicated cell retirement, shared cell exit proof, rollback closure after tenant split out

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md)
> - [Session Store / Claim-Version Cutover 설계](./session-store-claim-version-cutover-design.md)
> - [Deploy Rollback Safety / Compatibility Envelope 설계](./deploy-rollback-safety-compatibility-envelope-design.md)
> - [Zero-Downtime Schema Migration Platform 설계](./zero-downtime-schema-migration-platform-design.md)
> - [Dual-Write Avoidance / Migration Bridge 설계](./dual-write-avoidance-migration-bridge-design.md)
> - [Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md)
> - [Protocol Version Skew / Compatibility 설계](./protocol-version-skew-compatibility-design.md)
> - [Config Rollback Safety 설계](./config-rollback-safety-design.md)
> - [Bridge Retirement Evidence Packet 설계](./bridge-retirement-evidence-packet-design.md)
> - [Adapter Retirement / Compatibility Bridge Decommission 설계](./adapter-retirement-compatibility-bridge-decommission-design.md)
> - [Dedicated Cell Drain and Retirement 설계](./dedicated-cell-drain-retirement-design.md)
> - [Write-Freeze Rollback Window 설계](./write-freeze-rollback-window-design.md)

## 이 문서 다음에 보면 좋은 설계

- database/security authority transfer 뒤 cleanup gate를 다시 점검하려면 [Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md)의 `post-cutover soak`와 `bridge retirement` 행을 먼저 같이 본다.
- bridge removal approval packet을 cleanup change request로 넘길 때는 [Bridge Retirement Evidence Packet 설계](./bridge-retirement-evidence-packet-design.md)의 `shadow_exit_signal`, `parity_exit_signal`, `same_cohort_joined`를 먼저 붙인 뒤 내려온다.
- bridge를 실제로 retire하는 절차는 [Adapter Retirement / Compatibility Bridge Decommission 설계](./adapter-retirement-compatibility-bridge-decommission-design.md)로 이어진다.
- claim/session translator cleanup은 [Session Store / Claim-Version Cutover 설계](./session-store-claim-version-cutover-design.md)에서 revoke tail과 cleanup clock을 함께 봐야 한다.
- tenant split-out 이후 shared cell drain, legacy principal retirement, rollback closure를 묶어 보려면 [Dedicated Cell Drain and Retirement 설계](./dedicated-cell-drain-retirement-design.md)를 같이 보면 좋다.

## 핵심 개념

대부분의 전환 작업은 cutover보다 cleanup에서 진짜 되돌릴 수 없게 된다.

- old column 삭제
- old route 제거
- old config key 제거
- compatibility adapter 삭제
- donor state 폐기

이 순간이 바로 point of no return이다.
즉, cleanup은 단순 정리 작업이 아니라 **rollback 가능성을 닫는 최종 상태 전이**다.

## 깊이 들어가기

### 1. 왜 cleanup이 위험한가

전환 직후는 오히려 안전할 수 있다.

- old path가 아직 남아 있음
- adapter가 살아 있음
- old schema를 읽을 수 있음
- donor가 drain 상태로 남아 있음

하지만 cleanup을 해 버리면:

- old binary가 더 이상 new state를 못 읽음
- old route로 즉시 돌아갈 수 없음
- replay / correction이 필요해짐

즉, 위험한 순간은 "잘 됐으니 지우자"는 판단 직후다.

### 2. Capacity Estimation

예:

- 배포 후 관찰 창 24시간
- cleanup job 일일 1회
- old path 데이터 수 TB 단위
- rollback 목표 10분, forward-fix 목표 6시간

이때 봐야 할 숫자:

- post-cutover observation time
- old path residual traffic
- cleanup duration
- irreversible change count
- rollback readiness score

cleanup safety는 기술 비용보다 타이밍과 의사결정 경계가 더 중요하다.

### 3. Cleanup 종류

대표적으로 나뉜다.

- schema cleanup
- config key cleanup
- route / policy cleanup
- protocol adapter cleanup
- donor state cleanup
- background replay/bridge cleanup

이 각각은 point-of-no-return의 의미가 다르다.

### 4. Removal gate

좋은 시스템은 cleanup 전에 다음을 확인한다.

- old traffic가 충분히 0에 가까운가
- dual-read / canary가 충분히 안정적이었는가
- rollback boundary 밖으로 나가도 괜찮은가
- repair / correction plan이 준비되었는가
- approval이 필요한가

즉, cleanup은 cron이 아니라 gate 통과 후 실행되는 change management 작업이다.
cleanup 대상이 database route, claim translator, session authority bridge처럼 data plane과 identity plane을 함께 건드리면 gate도 양쪽 증거를 같이 본다.
[Database / Security Identity Bridge Cutover 설계](./database-security-identity-bridge-cutover-design.md)의 joint cutover gate 표에서 `post-cutover soak`와 `bridge retirement` 행을 다시 확인해 아래가 동시에 닫혔는지 봐야 한다.

- database plane: repair backlog, drift bucket, replay tail
- security plane: deprecated capability hit, auth shadow divergence, session revoke/access tail

### 5. point-of-no-return은 explicit exit signal handoff를 소비한다

destructive cleanup은 "traffic가 거의 없다" 같은 분위기 신호로 열면 안 된다.
point-of-no-return change request에는 bridge retirement packet에서 내려온 explicit handoff가 같이 붙어야 한다.

| handoff 항목 | cleanup에서 확인하는 질문 | 빠지면 생기는 위험 |
|---|---|---|
| `shadow_exit_signal` | 같은 cohort에서 shadow route, plugin, auth decision이 이미 닫혔는가 | hidden caller나 latent allow drift가 남은 채 route/config/schema를 지워 버린다 |
| `parity_exit_signal` | 같은 cohort에서 read parity와 revoke/decision parity가 닫혔는가 | cleanup 후 correction-only 상태에서 state mismatch와 auth tail을 다시 설명하지 못한다 |
| `same_cohort_joined` + packet ref | retirement packet과 cleanup change set이 같은 join key를 공유하는가 | 다른 표본을 섞은 승인이라 incident 발생 시 forensic 재구성이 불가능하다 |

즉 cleanup gate는 `bridge retirement packet이 approve-candidate였다`는 말만 받지 말고,
어떤 `shadow_exit_signal`, 어떤 `parity_exit_signal`이 닫혔는지까지 그대로 인용해야 한다.
둘 중 하나라도 `hold`면 cleanup은 아직 irreversible boundary를 넘으면 안 된다.

### 6. Freeze와 delayed cleanup

실무에서는 cleanup을 늦게 하는 편이 안전하다.

대표 전략:

- fixed soak window
- cleanup freeze during incident-prone hours
- manual approval for destructive contract
- scoped cleanup by tenant/region/cell

이렇게 하면 불필요하게 빠른 irreversible change를 줄일 수 있다.

### 7. Soft delete mindset

완전 제거 대신 다음 단계를 둘 수 있다.

- hidden but restorable
- disabled but recoverable
- tombstoned with grace period
- finally purged

즉, cleanup도 여러 단계로 나누면 point-of-no-return을 늦출 수 있다.

### 8. Observability

운영자는 다음을 알아야 한다.

- 아직 cleanup 전인가 후인가
- 어떤 old path가 살아 있는가
- 어떤 cleanup job이 pending인가
- 어느 작업이 irreversible인가
- rollback 대신 correction만 가능한 상태인가

이 정보가 없으면 cleanup이 지나치게 빨라지거나 끝없이 미뤄진다.

## 실전 시나리오

### 시나리오 1: old schema column 제거

문제:

- 새 코드가 안정화되자 old column을 지우고 싶다

해결:

- old binary traffic와 batch consumer가 완전히 사라졌는지 확인한다
- cleanup gate 통과 후 remove한다
- 제거 직후 일정 기간 recovery runbook을 유지한다

### 시나리오 2: old route / adapter 삭제

문제:

- cutover 후 old API route와 adapter가 남아 있다

해결:

- residual traffic가 0인지 본다
- bridge retirement packet의 `shadow_exit_signal=pass`, `parity_exit_signal=pass`를 확인한다
- incident 기간에는 freeze한다
- rollback이 아니라 forward-fix only 상태임을 명시한 뒤 삭제한다

### 시나리오 3: donor shard state 삭제

문제:

- receiver soak는 끝났지만 donor state를 지워도 되는지 불확실하다

해결:

- rollback window 종료를 명시한다
- stale route miss가 충분히 0에 가까운지 본다
- soft tombstone 기간 후 purge한다

## 코드로 보기

```pseudo
function canCleanup(change):
  return observationWindowPassed(change) &&
         residualTraffic(change.oldPath) < threshold &&
         jointBridgeMatrixHealthy(change) &&
         shadowExitSignal(change.bridgeRetirementPacket) == "pass" &&
         parityExitSignal(change.bridgeRetirementPacket) == "pass" &&
         joinableEvidence(change.bridgeRetirementPacket.join_keys) &&
         noActiveRollbackHold(change) &&
         approvalsSatisfied(change)

function executeCleanup(change):
  if !canCleanup(change):
    reject()
  markPointOfNoReturn(change)
  cleanupExecutor.run(change)
```

```java
public CleanupDecision decide(CleanupCandidate candidate) {
    return cleanupGate.evaluate(
        candidate,
        rollbackReadiness.current(),
        bridgeCutoverMatrix.current()
    );
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Immediate cleanup | 복잡도가 빨리 줄어든다 | rollback safety가 급감한다 | 아주 작은 시스템 |
| Delayed cleanup | 안전하다 | old path 비용이 남는다 | 대부분의 실서비스 |
| Multi-stage cleanup | 유연하다 | 운영 상태가 늘어난다 | 중요한 migration |
| Manual gated cleanup | 안전성이 높다 | 느리다 | 금융, 권한, core state |

핵심은 cleanup point-of-no-return 설계가 "지울까 말까"가 아니라 **언제부터 rollback 대신 correction만 가능한 상태가 되는지 명확히 정의하는 운영 설계**라는 점이다.

## 꼬리질문

> Q: cutover가 끝났으면 cleanup을 바로 해도 되나요?
> 의도: cutover와 cleanup 분리 이해 확인
> 핵심: 보통은 아니다. soak window와 rollback readiness를 먼저 확인해야 한다.

> Q: cleanup을 늦추면 왜 항상 좋은 건 아닌가요?
> 의도: safety vs complexity 균형 확인
> 핵심: old path 유지 비용, 운영 복잡도, accidental dual maintenance 부담이 계속 남기 때문이다.

> Q: point-of-no-return은 누가 정하나요?
> 의도: governance boundary 이해 확인
> 핵심: 기술팀만이 아니라 도메인 owner와 운영 정책이 함께 정하는 경우가 많다.

> Q: donor state를 soft tombstone으로 두는 이유는?
> 의도: reversible cleanup 감각 확인
> 핵심: purge 전에 짧은 복구 기회를 남겨 final rollback window를 조금 더 확보하기 위해서다.

## 한 줄 정리

Cleanup point-of-no-return 설계는 migration과 cutover 이후 어떤 제거 작업이 rollback 가능성을 닫는지 명시해, cleanup을 운영적으로 안전한 마지막 상태 전이로 다루는 설계다.
