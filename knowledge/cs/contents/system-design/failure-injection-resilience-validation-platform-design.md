# Failure Injection / Resilience Validation Platform 설계

> 한 줄 요약: failure injection과 resilience validation 플랫폼은 timeout, partial outage, dependency slowness, zone loss 같은 장애 조건을 통제된 방식으로 주입하고, 시스템의 복원력과 runbook의 실제 유효성을 검증하는 운영 검증 시스템이다.

retrieval-anchor-keywords: failure injection, resilience validation, chaos engineering platform, fault injection, dependency latency, zonal outage simulation, steady state hypothesis, blast radius budget, resilience experiment, recovery validation, global failover drill

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Backup, Restore, Disaster Recovery Drill 설계](./backup-restore-disaster-recovery-drill-design.md)
> - [Automated Canary Analysis / Rollback Platform 설계](./automated-canary-analysis-rollback-platform-design.md)
> - [Backpressure and Load Shedding 설계](./backpressure-and-load-shedding-design.md)
> - [Service Discovery / Health Routing 설계](./service-discovery-health-routing-design.md)
> - [Distributed Tracing Pipeline 설계](./distributed-tracing-pipeline-design.md)
> - [Stateful Workload Placement / Failover Control Plane 설계](./stateful-workload-placement-failover-control-plane-design.md)
> - [Global Traffic Failover Control Plane 설계](./global-traffic-failover-control-plane-design.md)

## 핵심 개념

장애 복원력은 설계 문서만으로 증명되지 않는다.
실제로 다음이 통제된 환경에서 검증되어야 한다.

- timeout budget이 맞는가
- failover가 실제로 동작하는가
- queue backlog와 shedding 정책이 견디는가
- runbook을 운영자가 따라 할 수 있는가
- observability가 원인을 충분히 보여 주는가

failure injection 플랫폼은 시스템을 일부러 망가뜨리는 도구가 아니라 **복원력 가설을 안전하게 검증하는 실험 제어 시스템**이다.

## 깊이 들어가기

### 1. 왜 필요한가

실전 장애는 보통 완전한 다운보다 애매한 부분 장애다.

- dependency p99만 급증
- 한 zone만 packet loss 발생
- 특정 shard만 lag 증가
- control plane push 지연
- retry amplification

이런 실패는 테스트 환경에서 잘 재현되지 않기 때문에, 운영에 가까운 조건에서 주입해 봐야 한다.

### 2. Capacity Estimation

예:

- 동시에 활성화 가능한 experiment 수 10개 이하
- 각 experiment는 1개 서비스 또는 1개 zone만 영향
- steady-state metric 100개 추적
- auto abort window 수 초~수 분

이때 봐야 할 숫자:

- experiment scope size
- blast radius budget
- abort reaction time
- metric convergence time
- false alarm rate

실험 플랫폼은 production에서 동작할 수 있어야 하지만, 그 자체가 production 위험이 되면 안 된다.

### 3. Experiment control plane

보통 구조는 다음과 같다.

```text
Experiment Authoring
  -> Policy / Approval
  -> Target Selector
  -> Fault Injector
  -> Metric / Trace Guardrail
  -> Auto Abort / Report Generator
```

이 control plane이 관리하는 것은 단순 "fault on/off"가 아니다.

- steady-state hypothesis
- allowed scope
- inject duration
- guardrail metric
- abort condition
- required approvals

### 4. Fault model library

대표 주입 유형:

- latency injection
- error injection
- packet loss / connection reset
- CPU / memory pressure
- zone or node cordon
- stale config / delayed propagation

모든 실패를 다 지원할 필요는 없지만, 가장 자주 겪는 failure mode를 먼저 모델링해야 한다.

### 5. Steady-state와 guardrail

좋은 실험은 "무엇이 정상인지"를 먼저 정의한다.

예:

- API success rate 99.9% 이상
- queue lag 30초 미만
- checkout conversion drop 1% 이내
- failover completion 60초 이내

steady-state가 없으면 실험이 "재밌는 파괴 활동"으로 끝나 버린다.

### 6. Auto abort와 human override

실험은 실패를 유도하지만, 무제한으로 두면 안 된다.

필요한 장치:

- hard blast radius limit
- metric-based auto abort
- time-based auto stop
- break-glass manual abort
- post-abort cooldown

즉, 안전한 혼란만 허용해야 한다.

### 7. Observability-rich reporting

실험이 끝난 뒤 중요한 것은 기록이다.

- 어떤 fault를 어디에 주입했는가
- 어떤 metric / trace가 변했는가
- guardrail이 언제 발동했는가
- runbook은 실제로 유효했는가
- 기대와 다른 결과는 무엇이었는가

좋은 플랫폼은 실험 결과를 postmortem과 runbook 개선 입력으로 남긴다.

## 실전 시나리오

### 시나리오 1: dependency latency spike 검증

문제:

- 외부 결제 provider가 느려질 때 timeout과 retry 정책이 맞는지 불확실하다

해결:

- latency injection을 특정 dependency 호출에만 적용한다
- retry amplification과 queue backlog를 같이 본다
- guardrail 위반 시 즉시 abort한다

### 시나리오 2: zone evacuation rehearsal

문제:

- 한 zone이 사라졌을 때 routing과 placement가 버틸지 확인하고 싶다

해결:

- zone 대상 experiment를 계획한다
- service discovery, stateful placement, load shedding metric을 함께 관찰한다
- failover completion time을 steady-state 가설로 둔다

### 시나리오 3: control plane staleness 실험

문제:

- config propagation이 늦어질 때 data plane이 버티는지 확인이 안 된다

해결:

- control push 지연 fault를 주입한다
- last-known-good snapshot으로 처리 지속 여부를 검증한다
- stale window를 넘는 경우만 경고하도록 조정한다

## 코드로 보기

```pseudo
function runExperiment(spec):
  ensureApproved(spec)
  guard = guardrail.start(spec)
  injector.apply(spec.target, spec.fault)
  while spec.active:
    if guard.violated() or timeoutExceeded():
      injector.abort(spec.target)
      break
  report.store(collector.collect(spec))

function violated():
  return metric("error_rate") > threshold ||
         metric("queue_lag") > threshold ||
         metric("conversion_drop") > threshold
```

```java
public ExperimentResult execute(ExperimentSpec spec) {
    approvalService.ensureApproved(spec);
    faultInjector.apply(spec);
    return monitorService.observeUntilComplete(spec);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Ad-hoc chaos test | 시작이 빠르다 | 재현성과 안전장치가 약하다 | 초기 학습 |
| Guardrail-based experiment platform | 안전성과 학습 효과가 높다 | 구축 비용이 든다 | mature 운영 조직 |
| Staging-only validation | 안전하다 | 실제 failure mode를 놓치기 쉽다 | 초기 검증 |
| Limited production experiments | 현실성이 높다 | 운영 리스크 관리가 필요하다 | 중요한 복원력 검증 |

핵심은 failure injection 플랫폼이 파괴 도구가 아니라 **복원력 가설, guardrail, abort, 실험 기록을 함께 가진 운영 검증 시스템**이라는 점이다.

## 꼬리질문

> Q: staging에서 충분히 테스트하면 production fault injection은 불필요하지 않나요?
> 의도: 환경 차이와 현실적 failure mode 이해 확인
> 핵심: 실제 traffic mix, dependency behavior, capacity pressure는 staging과 다르기 때문에 production과 유사한 환경 검증이 여전히 필요하다.

> Q: chaos engineering과 DR drill은 같은 건가요?
> 의도: 실험 범위 차이 이해 확인
> 핵심: 겹치지만 chaos는 fault hypothesis 검증, DR drill은 복구 절차 검증 성격이 더 강하다.

> Q: auto abort가 꼭 필요한가요?
> 의도: 실험 안전장치 이해 확인
> 핵심: production 실험에서 blast radius를 강하게 제한하려면 필수에 가깝다.

> Q: 좋은 resilience experiment의 시작점은 무엇인가요?
> 의도: steady-state 사고방식 확인
> 핵심: 어떤 정상 상태를 유지해야 하는지와, 어떤 조건에서 중단해야 하는지부터 명확히 정의하는 것이다.

## 한 줄 정리

Failure injection / resilience validation 플랫폼은 통제된 fault 주입과 guardrail 기반 관찰로 시스템의 복원력과 runbook 유효성을 실제로 검증하는 운영 실험 시스템이다.
