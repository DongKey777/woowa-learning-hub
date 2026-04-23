# Global Traffic Failover Control Plane 설계

> 한 줄 요약: global traffic failover control plane은 리전 간 트래픽 분산, 우선순위, failover, evacuation을 중앙에서 결정해 인터넷 진입 트래픽이 장애와 유지보수 중에도 안전한 경로로 흐르도록 만드는 제어 시스템이다.

retrieval-anchor-keywords: global traffic failover, gslb, dns failover, geo routing, regional evacuation, failover policy, weighted region routing, health signal aggregation, edge steering, traffic control plane

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Multi-Region Active-Active 설계](./multi-region-active-active-design.md)
> - [Service Discovery / Health Routing 설계](./service-discovery-health-routing-design.md)
> - [Stateful Workload Placement / Failover Control Plane 설계](./stateful-workload-placement-failover-control-plane-design.md)
> - [Backup, Restore, Disaster Recovery Drill 설계](./backup-restore-disaster-recovery-drill-design.md)
> - [Failure Injection / Resilience Validation Platform 설계](./failure-injection-resilience-validation-platform-design.md)
> - [Traffic Shadowing / Progressive Cutover 설계](./traffic-shadowing-progressive-cutover-design.md)

## 핵심 개념

여러 리전에 서비스를 운영할 때 "어디로 보낼지"는 단순 DNS 문제로 끝나지 않는다.
실전에서는 다음을 같이 결정해야 한다.

- 평소에는 어느 리전이 얼마나 받는가
- 리전 또는 zone 건강 상태를 어떻게 판단하는가
- partial outage일 때 완전 failover를 할지 일부만 줄일지
- evacuation과 maintenance 때 어떤 순서로 비울지
- stateful backend가 준비되기 전까지 얼마나 천천히 보낼지

즉, global traffic failover는 DNS 레코드 변경이 아니라 **건강 신호, capacity, 정책을 묶어 리전 간 진입 트래픽을 제어하는 control plane**이다.

## 깊이 들어가기

### 1. 왜 local discovery와 다른가

service discovery는 보통 이미 선택된 region 안에서 healthy endpoint를 고르는 문제다.
global traffic failover는 그보다 한 단계 위에서 다음을 다룬다.

- 어떤 region으로 갈지
- 어떤 percentage를 보낼지
- 어떤 region은 읽기만 허용할지
- 어떤 region은 evacuation 중인지

즉, locality의 범위가 다르다.

### 2. Capacity Estimation

예:

- APAC 50%, US 30%, EU 20% 정상 분산
- 한 region 손실 시 나머지 region이 1.7x까지 흡수 가능
- DNS TTL 30초
- health aggregation 지연 5초

이때 봐야 할 숫자:

- regional headroom
- traffic shift convergence time
- stale routing window
- failover completion time
- cold region warm-up duration

글로벌 트래픽 제어는 라우팅 알고리즘보다 "얼마나 빨리, 얼마나 안전하게 옮길 수 있는가"가 중요하다.

### 3. Health aggregation

리전 health는 단일 비트가 아니다.
보통 다음을 종합한다.

- ingress error rate
- p95/p99 latency
- saturation
- dependency reachability
- stateful backend readiness
- operator override

특히 stateful 시스템은 프런트만 살아 있어도 backend가 따라오지 않으면 failover하면 안 된다.

### 4. Routing policy

대표 정책:

- geo-local routing
- weighted regional split
- priority failover
- region pinning
- evacuation mode
- degraded read-only mode

중요한 것은 정책이 한 줄로 끝나지 않는다는 점이다.
예를 들어 "US 장애면 EU로"가 아니라, "EU가 stateful capacity를 얼마나 준비했는가"까지 봐야 한다.

### 5. Drain, warm-up, and re-entry

region failover는 옮기는 순간보다 옮긴 뒤가 더 어렵다.

- 갑자기 0%에서 50%로 올리면 cache cold start가 난다
- background queue와 replay job이 같이 몰릴 수 있다
- 복구된 region을 다시 넣을 때도 조심해야 한다

그래서 보통은 다음 단계를 둔다.

1. warm-up traffic
2. partial traffic
3. full cutover
4. controlled re-entry

### 6. Manual override와 automation 균형

완전 자동 failover는 매력적이지만 위험하다.

필요한 장치:

- auto failover threshold
- human approval on large shift
- forced evacuation switch
- cooldown before re-entry

즉, 일부는 자동화하고 일부는 운영자 승인 경계를 두는 편이 많다.

### 7. Observability-rich control

좋은 시스템은 다음 질문에 바로 답할 수 있어야 한다.

- 지금 각 region에 몇 %가 가는가
- 왜 이 shift가 일어났는가
- health score는 어떤 신호로 계산되었는가
- operator override가 있는가
- failover 후 어떤 SLO가 degraded 되었는가

트래픽 제어는 보이지 않으면 신뢰하기 어렵다.

## 실전 시나리오

### 시나리오 1: 한 region partial outage

문제:

- APAC error rate만 올라가고 완전 다운은 아니다

해결:

- weighted shift로 APAC 비중을 점진적으로 줄인다
- stateful backend readiness를 보며 US/EU를 늘린다
- 정상화 후 re-entry도 점진적으로 수행한다

### 시나리오 2: maintenance evacuation

문제:

- 특정 region을 계획적으로 비워야 한다

해결:

- evacuation mode를 활성화한다
- 신규 session과 write-heavy traffic부터 다른 region으로 보낸다
- region-local backlog와 cold cache를 고려해 단계적으로 이동한다

### 시나리오 3: DR rehearsal

문제:

- failover runbook이 실제로 동작하는지 검증하고 싶다

해결:

- failure injection과 결합해 region shift 실험을 한다
- convergence time과 SLO 변화를 기록한다
- operator override와 auto policy가 충돌하지 않는지 검증한다

## 코드로 보기

```pseudo
function decideGlobalRouting():
  health = healthAggregator.current()
  capacity = regionalCapacity.current()
  policy = policyStore.current()
  plan = planner.compute(health, capacity, policy)
  publisher.publish(plan)

function compute(health, capacity, policy):
  if policy.evacuationRegion:
    return drainRegion(policy.evacuationRegion, capacity)
  if health.region("apac").severe:
    return weightedShift(from="apac", to=["us","eu"])
  return policy.normalPlan
```

```java
public TrafficPlan reconcile() {
    RegionalState state = regionalStateService.current();
    return failoverPlanner.compute(state, policySnapshot.current());
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| DNS priority failover | 단순하다 | partial outage 대응이 약하다 | 초기 multi-region |
| Weighted global routing | 유연하다 | control plane이 복잡해진다 | 대부분의 대형 서비스 |
| Full auto failover | 반응이 빠르다 | 오탐 시 위험하다 | 신뢰도 높은 health model |
| Human-gated large shifts | 안전하다 | 반응이 느릴 수 있다 | stateful/high-risk backend |

핵심은 global traffic failover control plane이 단순 DNS 운영이 아니라 **health, capacity, state readiness를 바탕으로 리전 간 진입 트래픽을 조정하는 운영 제어 시스템**이라는 점이다.

## 꼬리질문

> Q: service discovery와 global traffic failover는 어떻게 다른가요?
> 의도: global vs regional routing 계층 구분 확인
> 핵심: discovery는 보통 region 내 endpoint 선택, global failover는 region 간 트래픽 분배와 evacuation을 다룬다.

> Q: region health가 나쁘면 무조건 다른 region으로 보내면 되나요?
> 의도: state readiness와 capacity 고려 확인
> 핵심: 아니다. target region의 backend readiness, headroom, cold start 비용을 같이 봐야 한다.

> Q: auto failover가 왜 위험할 수 있나요?
> 의도: false positive와 blast radius 이해 확인
> 핵심: 잘못된 health signal이나 일시적 spike만으로 대규모 traffic shift가 일어나면 오히려 더 큰 장애를 만들 수 있다.

> Q: failback은 왜 별도로 강조하나요?
> 의도: re-entry 운영 감각 확인
> 핵심: 복구된 region을 한 번에 다시 넣으면 cold start와 cache miss, state catch-up 문제로 재장애가 날 수 있다.

## 한 줄 정리

Global traffic failover control plane은 리전 health, capacity, state readiness를 종합해 인터넷 진입 트래픽의 분배와 failover, evacuation, re-entry를 조정하는 운영 제어 시스템이다.
