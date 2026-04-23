# Stateful Workload Placement / Failover Control Plane 설계

> 한 줄 요약: stateful workload placement와 failover control plane은 leader, shard owner, replica, standby의 배치와 승격 규칙을 관리해 장애와 유지보수 중에도 상태를 가진 서비스를 예측 가능하게 운영하는 제어 시스템이다.

retrieval-anchor-keywords: stateful workload placement, failover control plane, leader placement, replica promotion, maintenance drain, quorum-aware scheduling, standby assignment, evacuation plan, failover policy, placement decision, membership reconfiguration

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Shard Rebalancing / Partition Relocation 설계](./shard-rebalancing-partition-relocation-design.md)
> - [Service Discovery / Health Routing 설계](./service-discovery-health-routing-design.md)
> - [Multi-Region Active-Active 설계](./multi-region-active-active-design.md)
> - [Distributed Lock 설계](./distributed-lock-design.md)
> - [Session Store Design at Scale](./session-store-design-at-scale.md)
> - [Backup, Restore, Disaster Recovery Drill 설계](./backup-restore-disaster-recovery-drill-design.md)
> - [Consensus Membership Reconfiguration 설계](./consensus-membership-reconfiguration-design.md)
> - [Control Plane / Data Plane Separation 설계](./control-plane-data-plane-separation-design.md)
> - [Cell-Based Architecture / Blast Radius Isolation 설계](./cell-based-architecture-blast-radius-isolation-design.md)
> - [Global Traffic Failover Control Plane 설계](./global-traffic-failover-control-plane-design.md)

## 핵심 개념

stateless 서비스는 새 인스턴스를 띄우고 라우팅만 바꾸면 비교적 단순하다.
하지만 stateful workload는 다음을 같이 결정해야 한다.

- 누가 leader인가
- replica는 어디에 둘 것인가
- 장애 시 누구를 promote할 것인가
- maintenance drain은 어떤 순서로 할 것인가
- region / zone / rack failure domain을 어떻게 나눌 것인가

즉, placement control plane은 "어디에 배치할까"보다 **어떤 상태 역할을 어떤 실패 모델 아래 유지할까**를 다루는 시스템이다.

## 깊이 들어가기

### 1. 왜 stateless scheduler와 다른가

stateful workload는 placement가 곧 정합성과 가용성에 영향을 준다.

- leader와 follower가 같은 failure domain에 있으면 의미가 없다
- hot shard owner가 같은 rack에 몰리면 장애 시 쏠림이 심하다
- maintenance 중 drain 순서를 잘못 잡으면 quorum이 깨진다

그래서 CPU/메모리 bin packing만으로는 부족하다.

### 2. Capacity Estimation

예:

- shard leader 5천 개
- replica factor 3
- zone 3개
- maintenance로 한 zone capacity 20% 감소

이때 봐야 할 숫자:

- leader distribution skew
- quorum-safe spare capacity
- promotion time
- evacuation duration
- hot standby utilization

stateful control plane은 평균 리소스보다 failure domain별 잔여 용량이 더 중요하다.

### 3. Desired state와 actual state

control plane은 다음을 분리해야 한다.

- desired placement
- actual placement
- planned moves
- blocked moves
- degraded assignments

이 모델이 있어야 "원래 이렇게 있어야 하는데 지금은 왜 다르게 동작하는가"를 설명할 수 있다.

### 4. Failover policy

장애가 나면 아무 replica나 승격하면 안 된다.
승격 후보는 보통 다음으로 평가한다.

- replication lag
- zone / region locality
- health score
- warm cache 여부
- fencing / lease validity

즉, failover는 단순 heartbeat 기반이 아니라 **promotion eligibility policy**가 필요하다.

### 5. Maintenance drain과 evacuation

실전에서는 장애보다 planned maintenance가 더 자주 일어난다.

필요한 기능:

- node cordon
- no-new-leader assignment
- staged demotion
- shard handoff sequencing
- evacuation progress visibility

특히 quorum 기반 시스템은 "한 번에 얼마나 뺄 수 있는가"를 엄격히 계산해야 한다.

### 6. Placement constraints

대표 제약:

- zone anti-affinity
- rack diversity
- tenant isolation
- hot shard spreading
- storage class match
- data residency

이 제약이 많아질수록 단순 greedy placement로는 충분하지 않고, 정책 우선순위와 예외 모델이 필요해진다.

### 7. Observability-rich operations

좋은 control plane은 상태 이동 자체보다 설명력이 중요하다.

- 왜 이 leader가 이 node에 있는가
- 왜 이 replica는 promote 불가인가
- 어떤 move가 blocked 되었는가
- evacuation ETA는 얼마인가
- failover 후 어떤 SLA가 degraded 되었는가

운영자가 설명 가능한 시스템이어야 사고 때 빠르게 판단할 수 있다.

## 실전 시나리오

### 시나리오 1: session store zone maintenance

문제:

- 한 zone을 비워야 하지만 세션 leader가 몰려 있다

해결:

- 해당 zone을 no-new-leader 상태로 둔다
- follower lag를 줄인 뒤 순차 promote한다
- service discovery는 drain된 endpoint를 점진 제거한다

### 시나리오 2: storage node sudden failure

문제:

- shard owner가 죽었고 replica 중 일부도 lag가 크다

해결:

- promotion policy로 가장 안전한 replica를 고른다
- stale replica는 read-only 또는 catch-up 대기 상태로 둔다
- placement plane은 degraded 상태를 명시적으로 노출한다

### 시나리오 3: region evacuation rehearsal

문제:

- 특정 region을 비우는 rehearsal을 하고 싶다

해결:

- desired state를 evacuation mode로 바꾼다
- promote candidate와 failover budgets를 계산한다
- traffic router와 placement plan을 함께 관찰한다

## 코드로 보기

```pseudo
function reconcilePlacement():
  desired = planner.computeDesired(clusterState, policy)
  actual = inventory.currentAssignments()
  moves = diff(desired, actual)
  for move in prioritize(moves):
    if policy.safeToExecute(move):
      executor.start(move)

function choosePromotion(shard):
  candidates = replicas(shard).filter(healthy && fenceValid)
  return maxBy(candidates, lagScore + localityScore + warmupScore)
```

```java
public PlacementDecision decide(Shard shard, ClusterState state) {
    return placementPolicy.evaluate(shard, state, maintenanceWindow.current());
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Manual leader placement | 단순하다 | 운영 피로가 크다 | 작은 클러스터 |
| Basic automatic failover | 빠르다 | 잘못 승격할 위험이 있다 | 낮은 위험도 상태 |
| Policy-rich control plane | 예측 가능성이 높다 | 정책과 디버깅이 복잡하다 | 중요한 stateful 플랫폼 |
| Hot standby reserve | failover가 빠르다 | 비용이 든다 | 짧은 RTO 필요 |
| Aggressive evacuation | maintenance가 빠르다 | quorum risk가 커진다 | 여유 capacity가 클 때 |

핵심은 stateful workload placement / failover control plane이 스케줄러 기능이 아니라 **상태 역할, failure domain, 승격 정책을 함께 관리하는 운영 제어 시스템**이라는 점이다.

## 꼬리질문

> Q: stateful workload도 그냥 오토스케일러에 맡기면 안 되나요?
> 의도: stateless vs stateful 배치 차이 이해 확인
> 핵심: leader/follower 역할, quorum, lag, ownership handoff 같은 제약이 있어 단순 autoscaling만으로는 부족하다.

> Q: failover 후보는 왜 가장 가까운 replica만 고르면 안 되나요?
> 의도: promotion policy 이해 확인
> 핵심: lag, warm-up, fencing, zone diversity를 같이 봐야 안전하기 때문이다.

> Q: maintenance drain이 장애 대응보다 어려울 수 있는 이유는?
> 의도: planned operations의 복잡도 이해 확인
> 핵심: 여러 move를 동시에 계획해야 하고, quorum-safe capacity와 sequencing을 계산해야 하기 때문이다.

> Q: placement control plane의 observability에서 가장 중요한 질문은?
> 의도: 설명 가능성 감각 확인
> 핵심: "왜 지금 이 배치가 선택되었는가"를 운영자가 설명할 수 있어야 한다는 점이다.

## 한 줄 정리

Stateful workload placement와 failover control plane은 leader, replica, standby의 배치와 승격 규칙을 failure domain과 lag, maintenance 제약 아래 관리해 상태를 가진 서비스를 예측 가능하게 운영하는 제어 시스템이다.
