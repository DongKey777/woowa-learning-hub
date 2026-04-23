# Consensus Membership Reconfiguration 설계

> 한 줄 요약: consensus membership reconfiguration은 quorum 시스템의 노드 추가·제거·교체를 split brain 없이 안전하게 수행하기 위해, joint consensus와 learner 단계, 승격 조건을 관리하는 상태 변경 절차다.

retrieval-anchor-keywords: consensus membership reconfiguration, quorum, joint consensus, raft membership change, learner replica, majority, leader transfer, split brain avoidance, cluster reconfig, voter promotion

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Stateful Workload Placement / Failover Control Plane 설계](./stateful-workload-placement-failover-control-plane-design.md)
> - [Shard Rebalancing / Partition Relocation 설계](./shard-rebalancing-partition-relocation-design.md)
> - [Distributed Lock 설계](./distributed-lock-design.md)
> - [Multi-Region Active-Active 설계](./multi-region-active-active-design.md)
> - [Backup, Restore, Disaster Recovery Drill 설계](./backup-restore-disaster-recovery-drill-design.md)
> - [Control Plane / Data Plane Separation 설계](./control-plane-data-plane-separation-design.md)

## 핵심 개념

quorum 기반 시스템에서 가장 위험한 작업 중 하나는 membership 변경이다.

- 새 노드를 추가하고 싶다
- 오래된 노드를 제거하고 싶다
- 리전이나 zone을 교체하고 싶다
- leader를 옮기고 싶다

겉으로는 단순해 보여도 잘못하면 quorum 계산이 바뀌면서 split brain이나 availability loss가 생긴다.

즉, membership reconfiguration은 "서버 교체"가 아니라 **합의 집합 자체를 안전하게 바꾸는 상태 전이**다.

## 깊이 들어가기

### 1. 왜 위험한가

quorum 시스템은 누가 투표권(voter)을 가지는지에 따라 안전성이 결정된다.

단순히 old config를 지우고 new config를 넣으면 다음 문제가 생길 수 있다.

- 과거 leader가 여전히 자신이 합법적이라고 믿음
- old/new 다수 집합이 서로 겹치지 않음
- 노드 제거 중 failure가 나서 quorum 상실

그래서 membership 변경은 보통 두 단계 이상으로 한다.

### 2. Capacity Estimation

예:

- 5-node quorum cluster
- 하루 membership change 수십 회
- node bootstrap에 수십 GB log catch-up 필요
- promotion 허용 lag 수 초 이하

이때 봐야 할 숫자:

- learner catch-up lag
- leader transfer time
- reconfiguration completion time
- unavailability window
- log replication backlog

membership 변경은 빈도는 낮지만, 한 번 실패하면 blast radius가 매우 크다.

### 3. Joint consensus 또는 overlapping quorum

안전한 접근의 핵심은 old와 new config가 일정 기간 겹치도록 만드는 것이다.

대표 아이디어:

- old config와 new config가 동시에 유효한 transition state
- 과반수 판단이 두 집합을 모두 만족하도록 함
- transition이 끝난 뒤에만 old config 제거

이렇게 해야 old/new world가 완전히 분리되는 시점을 피할 수 있다.

### 4. Learner / non-voting replica

새 노드를 바로 voter로 넣으면 위험하다.
보통은 다음 단계를 둔다.

1. learner로 추가
2. log catch-up
3. health / lag / snapshot 검증
4. voter로 승격

즉, "복제 준비가 된 노드"와 "투표권이 있는 노드"는 다르다.

### 5. Leader transfer와 write disruption

membership 변경 중 leader가 가장 바쁜 역할을 할 수 있다.
따라서 다음을 고려한다.

- low-latency follower로 leader transfer
- catch-up이 늦은 follower는 승격 금지
- write-heavy 시점엔 reconfiguration 연기

실전에서는 membership change가 가능하더라도 트래픽 상황상 "지금은 하면 안 되는" 경우가 많다.

### 6. Removal sequencing

노드 제거 순서도 중요하다.

- dead node를 먼저 뺄지
- lagging replica를 먼저 교체할지
- zone diversity를 유지할지
- maintenance drain과 묶을지

특히 quorum 크기를 줄이는 작업은 capacity와 안전성을 함께 떨어뜨릴 수 있으므로, replacement를 먼저 붙이고 removal을 나중에 하는 편이 많다.

### 7. Observability와 runbook

membership 변경 중 꼭 봐야 할 것:

- current voters / learners
- replication lag
- commit latency
- leader stability
- joint-config duration
- pending snapshot transfer

운영자는 "지금 누가 합의 집합에 들어가 있는가"를 즉시 답할 수 있어야 한다.

## 실전 시나리오

### 시나리오 1: 오래된 storage node 교체

문제:

- 노드를 빼고 새 노드를 넣어야 한다

해결:

- 새 노드를 learner로 붙인다
- snapshot과 log를 따라잡게 한다
- health 검증 후 joint consensus로 voter 승격한다
- old node는 마지막에 제거한다

### 시나리오 2: zone maintenance

문제:

- 특정 zone의 voter가 일시적으로 내려갈 예정이다

해결:

- 다른 zone에 replacement voter를 먼저 확보한다
- leader가 maintenance zone에 있으면 먼저 transfer한다
- quorum-safe 상태가 확인된 뒤 drain을 시작한다

### 시나리오 3: 리전 evacuation rehearsal

문제:

- 한 리전을 비우되 합의 안정성은 유지해야 한다

해결:

- learner를 타 리전에 먼저 준비한다
- reconfiguration을 shard/cluster 단위로 점진 실행한다
- joint config 상태를 길게 끌지 않도록 batch sizing을 조절한다

## 코드로 보기

```pseudo
function replaceNode(oldNode, newNode):
  addLearner(newNode)
  waitUntil(catchupLag(newNode) < threshold)
  enterJointConfig(oldVoters + newNode)
  promoteToVoter(newNode)
  removeVoter(oldNode)

function safeToPromote(node):
  return node.healthy &&
         node.catchupLag < promoteLagThreshold &&
         snapshotApplied(node)
```

```java
public void reconfigure(ReconfigPlan plan) {
    membershipService.addLearner(plan.newNode());
    membershipService.awaitCatchup(plan.newNode());
    membershipService.enterJointConsensus(plan);
    membershipService.finalizeConfig(plan);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Direct replace | 빠르다 | split brain / quorum risk가 크다 | 거의 권장되지 않음 |
| Learner then promote | 안전하다 | 시간이 더 걸린다 | 대부분의 quorum 시스템 |
| Joint consensus | 수학적으로 안전하다 | 구현 복잡도가 높다 | 성숙한 consensus cluster |
| Maintenance freeze during reconfig | 단순하다 | 운영 유연성이 떨어진다 | 작은 클러스터 |

핵심은 membership reconfiguration이 인프라 교체 작업이 아니라 **합의 집합의 안전성을 유지한 채 quorum 경계를 바꾸는 상태 머신**이라는 점이다.

## 꼬리질문

> Q: 새 노드를 바로 voter로 넣으면 왜 위험한가요?
> 의도: learner 단계 필요성 이해 확인
> 핵심: 아직 log를 충분히 따라오지 못한 노드가 quorum 판단에 들어오면 commit과 failover가 흔들릴 수 있다.

> Q: joint consensus의 핵심 아이디어는 무엇인가요?
> 의도: overlapping quorum 이해 확인
> 핵심: old와 new config가 잠시 동시에 유효해, 어느 쪽도 고립된 다수를 만들지 못하게 하는 것이다.

> Q: membership 변경 중 leader transfer는 왜 중요하나요?
> 의도: 운영 중단 최소화 이해 확인
> 핵심: 바쁜 leader가 reconfiguration과 heavy writes를 동시에 처리하면 latency와 안정성이 모두 악화될 수 있다.

> Q: dead node를 먼저 빼는 게 항상 맞나요?
> 의도: removal sequencing 감각 확인
> 핵심: 상황에 따라 replacement voter를 먼저 준비하는 편이 availability와 diversity 면에서 더 안전하다.

## 한 줄 정리

Consensus membership reconfiguration은 learner 준비, joint consensus, 안전한 removal sequencing을 통해 quorum 시스템의 노드 구성을 split brain 없이 바꾸는 상태 전이 설계다.
