---
schema_version: 3
title: Shard Rebalancing / Partition Relocation 설계
concept_id: system-design/shard-rebalancing-partition-relocation-design
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- shard rebalancing
- partition relocation
- hot shard
- partition migration
aliases:
- shard rebalancing
- partition relocation
- hot shard
- partition migration
- ownership transfer
- copy catchup cutover
- shard split
- rebalance planner
- drain warmup
- placement control plane
- failover policy
- tenant reassignment
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/consistent-hashing-hot-key-strategies.md
- contents/system-design/distributed-cache-design.md
- contents/system-design/session-store-design-at-scale.md
- contents/system-design/service-discovery-health-routing-design.md
- contents/system-design/zero-downtime-schema-migration-platform-design.md
- contents/system-design/multi-region-active-active-design.md
- contents/system-design/stateful-workload-placement-failover-control-plane-design.md
- contents/system-design/consensus-membership-reconfiguration-design.md
- contents/system-design/tenant-partition-strategy-reassignment-design.md
- contents/system-design/receiver-warmup-cache-prefill-write-freeze-cutover-design.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Shard Rebalancing / Partition Relocation 설계 설계 핵심을 설명해줘
- shard rebalancing가 왜 필요한지 알려줘
- Shard Rebalancing / Partition Relocation 설계 실무 트레이드오프는 뭐야?
- shard rebalancing 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Shard Rebalancing / Partition Relocation 설계를 다루는 deep_dive 문서다. shard rebalancing과 partition relocation은 상태를 가진 파티션을 노드 사이에서 점진적으로 옮겨, hot shard 완화와 노드 증설·축소를 서비스 중단 없이 처리하는 stateful platform 운영 기술이다. 검색 질의가 shard rebalancing, partition relocation, hot shard, partition migration처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Shard Rebalancing / Partition Relocation 설계

> 한 줄 요약: shard rebalancing과 partition relocation은 상태를 가진 파티션을 노드 사이에서 점진적으로 옮겨, hot shard 완화와 노드 증설·축소를 서비스 중단 없이 처리하는 stateful platform 운영 기술이다.

retrieval-anchor-keywords: shard rebalancing, partition relocation, hot shard, partition migration, ownership transfer, copy catchup cutover, shard split, rebalance planner, drain warmup, placement control plane, failover policy, tenant reassignment, receiver warmup, write freeze

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Consistent Hashing / Hot Key 전략](./consistent-hashing-hot-key-strategies.md)
> - [Distributed Cache 설계](./distributed-cache-design.md)
> - [Session Store 설계 at Scale](./session-store-design-at-scale.md)
> - [Service Discovery / Health Routing 설계](./service-discovery-health-routing-design.md)
> - [Zero-Downtime Schema Migration Platform 설계](./zero-downtime-schema-migration-platform-design.md)
> - [Multi-Region Active-Active 설계](./multi-region-active-active-design.md)
> - [Stateful Workload Placement / Failover Control Plane 설계](./stateful-workload-placement-failover-control-plane-design.md)
> - [Consensus Membership Reconfiguration 설계](./consensus-membership-reconfiguration-design.md)
> - [Tenant Partition Strategy / Reassignment 설계](./tenant-partition-strategy-reassignment-design.md)
> - [Receiver Warmup / Cache Prefill / Write Freeze Cutover 설계](./receiver-warmup-cache-prefill-write-freeze-cutover-design.md)

## 핵심 개념

stateful 시스템은 노드를 늘리는 것만으로 자동 확장되지 않는다.
데이터와 ownership도 같이 옮겨야 한다.

실전에서 relocation은 다음 문제를 동시에 가진다.

- 현재 트래픽을 받는 shard를 끊지 않고 옮겨야 한다
- 복사 중에도 새 write가 계속 들어온다
- routing metadata가 늦게 퍼지면 dual owner가 생길 수 있다
- hot shard는 단순 이동만으로는 해결되지 않을 수 있다

즉, shard relocation은 단순 copy 작업이 아니라 **copy, catch-up, fencing, cutover를 포함한 상태 이전 절차**다.

## 깊이 들어가기

### 1. 왜 rebalance가 필요한가

대표적인 트리거:

- 노드 추가/제거
- 용량 불균형
- 특정 tenant 또는 key의 hot shard
- 리전 evacuation
- 하드웨어 교체

평균 분산이 좋아 보여도, 실제 운영에서는 상위 몇 개 shard가 대부분의 문제를 만든다.

### 2. Capacity Estimation

예:

- shard 총 2만 개
- shard당 평균 30 GB
- hot shard는 평시 write QPS의 8배
- relocation 동시 실행 50개

이때 봐야 할 숫자:

- bytes to move
- catch-up lag
- ownership handoff latency
- donor / receiver saturation
- rebalance completion time

재배치는 background 작업이지만, 잘못하면 사용자 경로의 p99를 직접 흔든다.

### 3. Placement control plane

좋은 시스템은 placement를 명시적으로 관리한다.

- shard -> node mapping
- desired state
- current state
- move plan
- fencing token
- drain / warm-up state

이 정보가 없으면 운영자는 "이 shard가 지금 누구 것인지"조차 확신하기 어렵다.

### 4. Copy, catch-up, cutover

가장 흔한 이전 절차:

1. receiver에 snapshot copy
2. donor의 새 write를 log tailing으로 따라잡기
3. lag가 충분히 줄어들면 short freeze 또는 fenced handoff
4. routing metadata cutover
5. donor drain 및 cleanup

즉, 장시간 전체 중단 대신 짧은 최종 handoff 구간만 만드는 것이 목표다.

### 5. Fencing과 dual owner 방지

가장 위험한 상태는 donor와 receiver가 동시에 owner라고 믿는 것이다.

대응:

- monotonically increasing fencing token
- lease expiration
- routing version
- write freeze window

특히 client-side routing이나 local cache가 있으면 stale metadata가 오래 남을 수 있어 더 조심해야 한다.

### 6. Hot shard는 split이 필요할 수 있다

hot shard를 다른 노드로 옮겨도, 여전히 한 shard 자체가 뜨거우면 문제는 남는다.

그래서 선택지가 나뉜다.

- relocate only
- logical split
- key remap
- read replica / follower offload

즉, rebalance는 placement 문제와 key design 문제를 구분해서 봐야 한다.
특히 multi-tenant 시스템에서는 shard 이동이 곧 tenant reassignment로 이어질 수 있으므로, tenant directory와 placement class를 같이 관리하는 편이 좋다.

### 7. Warm-up과 관측성

새 receiver는 데이터만 있다고 바로 준비되는 것이 아니다.

- cache warm-up
- connection pool 안정화
- compaction / index build
- query latency soak period

운영자는 다음을 봐야 한다.

- relocation lag
- handoff retry count
- per-shard latency
- stale route miss
- donor/receiver CPU and IO

## 실전 시나리오

### 시나리오 1: 캐시 cluster 증설

문제:

- 새 노드를 추가했더니 key 이동이 많아 cache miss가 폭증한다

해결:

- virtual node를 점진적으로 추가한다
- hot shard부터 우선 이전한다
- receiver warm-up 동안 traffic weight를 제한한다

### 시나리오 2: session store 노드 장애 전 drain

문제:

- 특정 노드를 내리기 전에 세션 shard를 옮겨야 한다

해결:

- node를 donor-only 상태로 둔다
- shard snapshot과 delta catch-up을 수행한다
- cutover 후 donor를 read-only drain으로 유지한다

### 시나리오 3: multi-region evacuation

문제:

- 한 region의 상태 shard를 다른 region으로 옮겨야 한다

해결:

- routing version과 fencing token을 region 단위로 관리한다
- replication lag와 write locality 정책을 함께 본다
- cross-region copy는 hot path보다 낮은 우선순위로 제한한다

## 코드로 보기

```pseudo
function relocate(shard, donor, receiver):
  snapshot = donor.snapshot(shard)
  receiver.restore(snapshot)
  while lag(shard, donor, receiver) > threshold:
    delta = donor.readChanges(shard)
    receiver.apply(delta)
  token = placement.issueFence(shard)
  donor.freezeWrites(shard, token)
  receiver.promote(shard, token)
  placement.updateOwner(shard, receiver, token)
```

```java
public void moveShard(ShardId shardId, NodeId target) {
    RelocationPlan plan = planner.plan(shardId, target);
    relocationExecutor.execute(plan);
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Stop-the-world move | 단순하다 | downtime이 크다 | 내부 배치, 작은 상태 |
| Copy + catch-up + cutover | 무중단에 가깝다 | 운영 복잡도 증가 | 대부분의 stateful 플랫폼 |
| Consistent hashing only | 자동성이 좋다 | hot shard와 drain 제어가 약하다 | 단순 캐시 |
| Manual placement | 제어력이 높다 | 운영 부담이 크다 | 고가치 shard, special tenant |
| Logical shard split | 근본 해결이 된다 | 애플리케이션 영향이 크다 | hot shard가 구조적일 때 |

핵심은 shard rebalancing이 노드 운영이 아니라 **상태 ownership을 안전하게 이전하는 stateful platform 절차**라는 점이다.

## 꼬리질문

> Q: consistent hashing이 있으면 rebalancing 문제는 끝나지 않나요?
> 의도: 평균 분산과 state move 차이 이해 확인
> 핵심: 아니다. 실제 state copy, catch-up, warm-up, fencing은 별도 운영 문제가 된다.

> Q: 왜 routing metadata version이 중요한가요?
> 의도: stale route와 dual owner 이해 확인
> 핵심: 일부 클라이언트가 늦게 갱신되더라도 누가 최신 owner인지 판별해야 하기 때문이다.

> Q: hot shard를 옮기기만 하면 되나요?
> 의도: hot shard의 구조적 원인 이해 확인
> 핵심: key 자체가 뜨거우면 split이나 read offload가 필요할 수 있다.

> Q: donor를 바로 지우지 않고 drain 기간을 두는 이유는?
> 의도: cutover 안전장치 이해 확인
> 핵심: stale route, 늦은 ack, rollback 가능성을 흡수하기 위해서다.

## 한 줄 정리

Shard rebalancing과 partition relocation은 상태를 가진 파티션의 ownership을 copy, catch-up, fencing, cutover 절차로 안전하게 옮겨 stateful 플랫폼의 증설과 장애 대응을 가능하게 하는 운영 기술이다.
