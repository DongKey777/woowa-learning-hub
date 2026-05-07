---
schema_version: 3
title: Consistent Hashing Rebalancing Cost Model
concept_id: data-structure/consistent-hashing-rebalancing-cost-model
canonical: false
category: data-structure
difficulty: advanced
doc_role: playbook
level: advanced
language: ko
source_priority: 82
mission_ids: []
review_feedback_tags:
- consistent-hashing-rebalance
- vnode-distribution
- shard-migration-cost
aliases:
- consistent hashing rebalancing cost
- vnode distribution
- key movement model
- shard migration cost
- cluster expansion rebalance
- partition movement
- load skew consistent hashing
symptoms:
- consistent hashing을 쓰면 rebalancing cost가 거의 0이라고 생각해 key movement와 replica movement를 모델링하지 않는다
- vnode 개수가 load skew를 줄이지만 metadata와 운영 오버헤드를 키운다는 trade-off를 놓친다
- 노드 증감 시 이동 key 수만 보고 cache miss, metadata update, replica rebuild가 만든 운영 흔들림을 계산하지 않는다
intents:
- design
- troubleshooting
prerequisites:
- data-structure/consistent-hashing-ring
next_docs:
- data-structure/consistent-hashing-ring
- data-structure/hashmap-internals
- algorithm/top-k-streaming-heavy-hitters
linked_paths:
- contents/data-structure/consistent-hashing-ring.md
- contents/data-structure/hashmap-internals.md
- contents/algorithm/top-k-streaming-heavy-hitters.md
confusable_with:
- data-structure/consistent-hashing-ring
- data-structure/hashmap-internals
- algorithm/top-k-streaming-heavy-hitters
forbidden_neighbors: []
expected_queries:
- Consistent Hashing에서 노드 추가 삭제 시 실제로 얼마나 많은 key가 움직여?
- vnode 수가 rebalancing cost와 load skew에 어떤 영향을 줘?
- consistent hashing을 써도 shard migration 비용을 모델링해야 하는 이유는?
- 캐시 클러스터 확장 때 key movement와 cache miss를 어떻게 계산해?
- consistent hashing rebalancing에서 replica 정책까지 같이 봐야 하는 이유는?
contextual_chunk_prefix: |
  이 문서는 consistent hashing의 rebalancing cost를 노드 증감, vnode 분포,
  key movement, replica movement, cache miss, metadata update 비용으로
  모델링하는 playbook이다. consistent hashing이 전체 재해시는 줄여도 운영
  이동 비용을 0으로 만들지는 않는다는 점을 강조한다.
---
# Consistent Hashing Rebalancing Cost Model

> 한 줄 요약: Consistent Hashing의 재배치 비용은 노드 증감으로 영향을 받는 키 구간의 크기와 vnode 분포 품질로 거의 결정된다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Consistent Hashing Ring](./consistent-hashing-ring.md)
> - [HashMap 내부 구조](./hashmap-internals.md)
> - [Top-k Streaming and Heavy Hitters](../algorithm/top-k-streaming-heavy-hitters.md)

> retrieval-anchor-keywords: consistent hashing rebalancing cost, vnode distribution, key movement, shard migration, rehash cost, partition movement, load skew, cluster expansion, rebalance model

## 핵심 개념

Consistent hashing을 쓴다고 재배치 비용이 0이 되는 건 아니다.  
중요한 건 "얼마나 많이 옮겨야 하느냐"를 모델링하는 것이다.

재배치 비용은 대략 다음에 좌우된다.

- 추가/삭제된 노드 수
- vnode 수
- 키 분포의 편차
- replica 정책

## 깊이 들어가기

### 1. 왜 전체가 아니라 일부만 움직이나

링에서 노드가 바뀌면 그 노드의 구간만 주로 영향받는다.

즉 전체 키를 다 옮기지 않고 국소적인 key range만 이동한다.

### 2. vnode 개수의 영향

vnode가 많을수록 분포가 좋아지고, 단일 물리 노드가 먹는 편차가 줄어든다.

하지만 vnode가 너무 많으면 관리 오버헤드가 커진다.

### 3. 비용 모델링 감각

실무에서는 다음을 같이 본다.

- 이동해야 하는 key 수
- 이동 중 캐시 미스 비용
- metadata 업데이트 비용
- replica 재배치 비용

즉 "몇 개 옮겼나"만이 아니라 "옮기는 동안 시스템이 얼마나 흔들리나"도 중요하다.

### 4. backend 운영에서의 의미

클러스터 확장이나 장애 조치에서 rebalancing은 흔하다.

- 새 노드 투입
- 장애 노드 제거
- 테넌트 재배치

정책이 없으면 consistent hashing도 운영이 어려워진다.

## 실전 시나리오

### 시나리오 1: 캐시 클러스터 확장

새 노드를 추가할 때 전체 캐시를 비우지 않아도 된다.

### 시나리오 2: 장애 복구

특정 샤드가 사라져도 주변 노드가 그 구간만 흡수하면 된다.

### 시나리오 3: 오판

재배치 비용이 작다고 무조건 좋진 않다.  
운영 메타데이터와 key skew가 심하면 여전히 병목이 된다.

## 코드로 보기

```java
public class RebalancingCostModel {
    public long estimatedMovedKeys(long totalKeys, int changedNodes, int vnodeCount) {
        if (vnodeCount <= 0) return totalKeys;
        long perVNodeShare = totalKeys / vnodeCount;
        return perVNodeShare * changedNodes;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Consistent Hashing | 일부 키만 옮긴다 | vnode/운영 정책이 필요하다 | 노드 변동이 잦을 때 |
| Full Rehash | 단순하다 | 모든 키가 이동한다 | 작은 시스템 |
| Central Repartition | 제어가 쉽다 | 중앙 제어점이 생긴다 | 명시적 운영이 중요할 때 |

## 꼬리질문

> Q: 왜 vnode가 재배치 비용에 영향을 주나?
> 의도: 분포와 이동 단위를 이해하는지 확인
> 핵심: 더 잘게 나눌수록 이동이 고르게 분산되기 때문이다.

> Q: rebalancing cost는 무엇으로 구성되나?
> 의도: 운영 비용을 단순 key move 이상으로 보는지 확인
> 핵심: key 이동, metadata, cache miss, replica 비용이다.

> Q: consistent hashing이 있다고 운영이 끝나는가?
> 의도: 설계와 운영을 구분하는지 확인
> 핵심: 아니다. 정책과 관측이 필요하다.

## 한 줄 정리

Consistent hashing의 재배치 비용은 이동되는 키 구간 크기와 vnode 분포, replica 정책을 함께 봐야 현실적으로 판단할 수 있다.
