---
schema_version: 3
title: Consistent Hashing / Hot Key 전략
concept_id: system-design/consistent-hashing-hot-key-strategies
canonical: false
category: system-design
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- consistent hashing
- hot key
- virtual node
- ring
aliases:
- consistent hashing
- hot key
- virtual node
- ring
- rebalancing
- shard split
- cache hotspot
- partition movement
- key remap
- hot shard
- Consistent Hashing / Hot Key 전략
- consistent hashing hot key strategies
symptoms: []
intents:
- deep_dive
- design
prerequisites: []
next_docs: []
linked_paths:
- contents/system-design/system-design-framework.md
- contents/system-design/back-of-envelope-estimation.md
- contents/system-design/distributed-cache-design.md
- contents/system-design/rate-limiter-design.md
- contents/system-design/shard-rebalancing-partition-relocation-design.md
- contents/database/mvcc-replication-sharding.md
- contents/database/bptree-vs-lsm-tree.md
confusable_with: []
forbidden_neighbors: []
expected_queries:
- Consistent Hashing / Hot Key 전략 설계 핵심을 설명해줘
- consistent hashing가 왜 필요한지 알려줘
- Consistent Hashing / Hot Key 전략 실무 트레이드오프는 뭐야?
- consistent hashing 설계에서 흔한 실수는 무엇이야?
contextual_chunk_prefix: 이 문서는 system-design 카테고리에서 Consistent Hashing / Hot Key 전략를 다루는 deep_dive 문서다. consistent hashing은 key 이동을 줄이는 분산 배치 기법이고, hot key 전략은 그 배치가 깨질 때를 버티는 운영 설계다. 검색 질의가 consistent hashing, hot key, virtual node, ring처럼 들어오면 확장성, 일관성, 장애 격리, 운영 검증 관점으로 연결한다.
---
# Consistent Hashing / Hot Key 전략

> 한 줄 요약: consistent hashing은 key 이동을 줄이는 분산 배치 기법이고, hot key 전략은 그 배치가 깨질 때를 버티는 운영 설계다.

retrieval-anchor-keywords: consistent hashing, hot key, virtual node, ring, rebalancing, shard split, cache hotspot, partition movement, key remap, hot shard

**난이도: 🔴 Advanced**

> 관련 문서:
> - [시스템 설계 면접 프레임워크](./system-design-framework.md)
> - [Back-of-Envelope 추정법](./back-of-envelope-estimation.md)
> - [분산 캐시 설계](./distributed-cache-design.md)
> - [Rate Limiter 설계](./rate-limiter-design.md)
> - [Shard Rebalancing / Partition Relocation 설계](./shard-rebalancing-partition-relocation-design.md)
> - [MVCC, Replication, Sharding](../database/mvcc-replication-sharding.md)
> - [B+Tree vs LSM-Tree](../database/bptree-vs-lsm-tree.md)

---

## 핵심 개념

consistent hashing은 노드 수가 바뀌어도 key 재배치를 최소화하기 위해 쓰는 기법이다.  
hot key 전략은 특정 key에 트래픽이 몰릴 때 한 노드가 죽지 않게 하는 운영 기법이다.

두 개는 따로가 아니다.

- consistent hashing은 평균적인 분산을 돕는다.
- hot key 전략은 분산이 깨지는 예외 상황을 다룬다.

---

## 깊이 들어가기

### 1. 왜 필요한가

단순 modulo 분배는 노드가 바뀌면 대부분의 key가 재배치된다.

```text
node = hash(key) % N
```

N이 바뀌면 캐시 미스가 폭발하고, DB로 쏠리고, 서비스가 흔들린다.  
consistent hashing은 이 이동 범위를 줄이기 위해 ring 구조를 쓴다.

### 2. 가상 노드

실제 노드 수가 적으면 분포가 불균형해진다.  
가상 노드는 이 문제를 줄인다.

장점:

- 분포가 더 고르게 된다
- 노드 추가/삭제의 영향이 줄어든다

단점:

- 관리 포인트가 늘어난다
- 해시 계산과 metadata가 복잡해진다

### 3. hot key가 생기는 이유

hot key는 보통 다음 원인으로 생긴다.

- 특정 게시물/상품이 바이럴됨
- 하나의 세션/토큰에 트래픽 집중
- 캐시 키 설계가 지나치게 단순함
- 배치 작업이 한 key만 자주 만짐

hot key는 성능 문제이면서 장애 문제다.  
한 노드에 CPU, 메모리, 네트워크가 같이 몰린다.

### 4. 대응 전략

대표 전략:

- key splitting
- local cache 추가
- request coalescing
- TTL jitter
- read replica 분산
- pre-warming
- rate limit

예를 들어 특정 게시물 조회가 많으면:

```text
post:123 -> post:123:meta
post:123:view_count -> sharded counter
```

### 5. consistent hashing의 한계

좋은 분배는 평균에 강하다.  
하지만 hot key는 평균을 무시한다.

즉, consistent hashing만 믿으면 안 된다.

- key 하나가 뜨거우면 ring 상 한 노드에 계속 몰린다.
- virtual node를 늘려도 한 key의 집중은 못 막는다.
- 결국 key 자체를 쪼개거나 읽기 경로를 분리해야 한다.

### 6. 운영 메트릭

다음 지표를 봐야 한다.

- per-key QPS
- node별 CPU
- cache hit ratio
- eviction rate
- key cardinality
- rebalancing time

---

## 실전 시나리오

### 시나리오 1: 단일 인기 게시물

한 게시물이 SNS에 퍼지면 조회가 한 key로 몰린다.

대응:

- local cache
- CDN/edge cache
- hot key 분리
- 읽기용 복제본

### 시나리오 2: 세션 키 폭주

특정 login flow나 이벤트로 세션 키가 몰리면 하나의 shard가 터진다.

대응:

- key prefix 분산
- shard key 재설계
- rate limit

### 시나리오 3: 노드 증설

노드를 추가할 때 리밸런싱이 일어나면 DB가 흔들릴 수 있다.

대응:

- 점진적 rebalancing
- warm-up
- read throttle

실제로 상태를 많이 가진 shard라면 hash ring 변경만으로 끝나지 않고, snapshot copy와 ownership handoff까지 포함한 relocation 절차가 필요하다.

---

## 코드로 보기

```pseudo
function getNode(key):
    h = hash(key)
    vnode = ring.ceiling(h)
    if vnode == null:
        vnode = ring.first()
    return vnode.node
```

```java
public Node locate(String key) {
    long hash = hashFunction.hash(key);
    Map.Entry<Long, Node> entry = ring.ceilingEntry(hash);
    if (entry == null) {
        entry = ring.firstEntry();
    }
    return entry.getValue();
}
```

### hot key 분할 예시

```java
public String shardHotKey(String key, int bucketCount) {
    int bucket = Math.abs(key.hashCode()) % bucketCount;
    return key + ":" + bucket;
}
```

이 방식은 조회 시 재조합 비용이 생기므로, 읽기 패턴에 맞게만 써야 한다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|-------------|
| modulo 분배 | 단순하다 | 노드 변경에 약하다 | 매우 작은 시스템 |
| consistent hashing | key 이동이 적다 | hot key는 못 막는다 | 일반적인 분산 캐시 |
| virtual node 증가 | 분포가 좋아진다 | 운영 복잡도 증가 | 노드 수가 적을 때 |
| key splitting | hot key 완화 | 조회/정합성 복잡도 증가 | 특정 key 집중이 심할 때 |

## 꼬리질문

> Q: consistent hashing만 쓰면 hot key 문제도 해결되나요?
> 의도: 평균 분산과 최악 상황을 구분하는지 확인
> 핵심: 아니다. hot key는 별도 대응이 필요하다

> Q: key를 쪼개면 왜 항상 좋은 것이 아니죠?
> 의도: 설계 복잡도와 조회 비용을 보는지 확인
> 핵심: 읽기 시 재조합과 정합성 비용이 생긴다

## 한 줄 정리

consistent hashing은 배치 문제를, hot key 전략은 배치가 깨질 때의 운영 문제를 푼다.
