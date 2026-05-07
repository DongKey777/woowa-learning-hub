---
schema_version: 3
title: Consistent Hashing Ring
concept_id: data-structure/consistent-hashing-ring
canonical: false
category: data-structure
difficulty: advanced
doc_role: primer
level: advanced
language: ko
source_priority: 83
mission_ids: []
review_feedback_tags:
- consistent-hashing-ring
- distributed-cache-sharding
- virtual-node
aliases:
- consistent hashing
- hash ring
- virtual node
- vnode
- shard assignment ring
- cache cluster sharding
- first clockwise node
symptoms:
- hash(key) % n modulo sharding을 써서 노드 수가 바뀔 때 대부분의 key가 재배치되는 문제를 겪는다
- consistent hashing ring에서 key가 시계 방향 첫 노드로 배치되는 규칙과 vnode 필요성을 헷갈린다
- 분산 캐시나 세션 저장소에서 shard skew, failover, replica 정책을 hash ring과 함께 보지 않는다
intents:
- definition
- design
prerequisites:
- data-structure/hashmap-internals
next_docs:
- data-structure/consistent-hashing-rebalancing-cost-model
- data-structure/hashmap-internals
- data-structure/lru-cache-design
linked_paths:
- contents/data-structure/hashmap-internals.md
- contents/data-structure/lru-cache-design.md
- contents/data-structure/treemap-vs-hashmap-vs-linkedhashmap.md
confusable_with:
- data-structure/consistent-hashing-rebalancing-cost-model
- data-structure/hashmap-internals
- data-structure/lru-cache-design
forbidden_neighbors: []
expected_queries:
- Consistent Hashing Ring은 modulo sharding과 무엇이 달라?
- hash ring에서 key는 왜 시계 방향 첫 노드에 배치돼?
- virtual node가 consistent hashing의 부하 분산에 필요한 이유는?
- 분산 캐시 클러스터에서 노드 추가 삭제 시 key 재배치를 줄이는 방법은?
- consistent hashing을 쓸 때 shard skew와 failover policy를 어떻게 봐야 해?
contextual_chunk_prefix: |
  이 문서는 Consistent Hashing Ring을 hash(key) modulo n 대신 key와 node를
  같은 해시 공간에 올리고 시계 방향 첫 node에 배치하는 distributed
  sharding primer로 설명한다. vnode, cache cluster, shard assignment,
  failover, replica policy를 함께 다룬다.
---
# Consistent Hashing Ring

> 한 줄 요약: Consistent Hashing Ring은 노드 수가 바뀌어도 키 재배치 범위를 최소화하는 분산 배치 방식이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [HashMap 내부 구조](./hashmap-internals.md)
> - [LRU Cache Design](./lru-cache-design.md)
> - [TreeMap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md)

> retrieval-anchor-keywords: consistent hashing, hash ring, virtual node, vnode, shard assignment, cache cluster, rebalancing, hotspot, failover, distributed partition

## 핵심 개념

Consistent hashing은 키를 `hash(key) % n`으로 바로 나누는 대신, **해시 공간 전체를 원형 링으로 보고 키와 노드를 같은 공간에 올려서 매핑**하는 방식이다.

핵심 장점은 서버가 늘거나 줄어도 **대부분의 키를 다시 옮기지 않아도 된다**는 점이다.

- 노드 추가 시: 새 노드 주변의 일부 키만 이동
- 노드 제거 시: 그 노드가 담당하던 일부 키만 이동

실무에서는 다음과 같은 곳에 자주 나온다.

- 분산 캐시 샤딩
- 세션 저장소 배치
- 멀티 리전 라우팅
- 리더 선출 이전의 partition ownership

## 깊이 들어가기

### 1. 왜 modulo sharding이 깨지나

단순히 `hash(key) % n`을 쓰면 노드 수가 바뀔 때 모든 키의 배치가 흔들린다.

예를 들어 노드가 10개에서 11개로 바뀌면 대부분의 키가 새 위치로 재분배된다.  
이건 캐시나 세션 저장소에서 매우 비싼 작업이다.

### 2. ring과 first clockwise node

해시 결과를 0부터 2^32-1 같은 원형 공간에 놓고, 각 노드도 같은 공간의 점으로 본다.

키는 해시 위치에서 **시계 방향으로 처음 만나는 노드**에 배치한다.

- 키와 노드가 같은 해시 공간을 공유한다.
- 노드 수가 바뀌어도 국소적인 영역만 영향받는다.

### 3. virtual node가 필요한 이유

실제로는 노드 하나를 링 위에 한 점만 두면 분포가 불균형해질 수 있다.

그래서 보통 하나의 물리 서버를 여러 개의 virtual node로 쪼개서 링에 분산시킨다.

- 부하 분산이 좋아진다.
- 특정 서버가 해시상 빈 공간을 많이 먹는 문제를 줄인다.
- 장애 시에도 더 부드럽게 재배치된다.

### 4. backend 운영에서 중요한 것

Consistent hashing은 이론보다 운영이 중요하다.

- 해시 함수가 충분히 균등해야 한다.
- vnode 개수를 너무 적게 잡으면 skew가 생긴다.
- 노드 장애 시 failover 대상이 명확해야 한다.
- replica를 어디까지 둘지 정책이 필요하다.

## 실전 시나리오

### 시나리오 1: 분산 캐시 클러스터

Redis 같은 캐시를 여러 샤드로 나눌 때 consistent hashing을 쓰면, 노드가 하나 추가되어도 캐시 전체를 다시 채우지 않아도 된다.

### 시나리오 2: 세션 저장소

로그인 세션을 특정 노드에 저장할 때, 같은 사용자의 요청이 항상 비슷한 샤드로 가면 세션 조회가 단순해진다.

### 시나리오 3: 핫키 완화

특정 키가 지나치게 뜨거우면 vnode 단위 분산이나 replica read 전략을 섞어서 hotspot을 줄일 수 있다.

### 시나리오 4: 장애 복구

서버 한 대가 내려갔을 때 모든 키를 재배치하지 않고, 그 노드 구간만 주변 노드가 흡수하면 복구가 훨씬 가볍다.

## 코드로 보기

```java
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.NavigableMap;
import java.util.TreeMap;

public class ConsistentHashRing<T> {
    private final NavigableMap<Long, T> ring = new TreeMap<>();
    private final Map<String, List<Long>> vnodeIndex = new HashMap<>();
    private final int virtualNodeCount;

    public ConsistentHashRing(int virtualNodeCount) {
        this.virtualNodeCount = virtualNodeCount;
    }

    public void addNode(String nodeId, T node) {
        List<Long> hashes = new ArrayList<>();
        for (int i = 0; i < virtualNodeCount; i++) {
            long h = hash(nodeId + "#" + i);
            ring.put(h, node);
            hashes.add(h);
        }
        vnodeIndex.put(nodeId, hashes);
    }

    public void removeNode(String nodeId) {
        List<Long> hashes = vnodeIndex.remove(nodeId);
        if (hashes == null) {
            return;
        }
        for (Long h : hashes) {
            ring.remove(h);
        }
    }

    public T getNode(String key) {
        if (ring.isEmpty()) {
            return null;
        }
        long h = hash(key);
        Long target = ring.ceilingKey(h);
        if (target == null) {
            target = ring.firstKey();
        }
        return ring.get(target);
    }

    private long hash(String value) {
        byte[] bytes = value.getBytes(StandardCharsets.UTF_8);
        long h = 1125899906842597L;
        for (byte b : bytes) {
            h = 31 * h + (b & 0xff);
        }
        return h & 0x7fffffffffffffffL;
    }
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 단순 modulo sharding | 구현이 매우 쉽다 | 노드 수 변경 시 재배치 폭이 크다 | 노드 수가 고정일 때 |
| Consistent hashing | 재배치 범위를 줄인다 | vnode와 replica 정책이 필요하다 | 노드가 자주 바뀌는 클러스터 |
| 중앙 라우터 기반 배치 | 제어가 쉽다 | 라우터가 병목이 될 수 있다 | 운영 제어가 더 중요할 때 |

Consistent hashing은 "배치 안정성"이 중요한 분산 시스템에 특히 맞는다.

## 꼬리질문

> Q: virtual node는 왜 그냥 하나의 노드보다 낫나?
> 의도: 해시 분산과 부하 편차를 이해하는지 확인
> 핵심: 점을 여러 개로 쪼개야 링 위 분포가 더 균등해진다.

> Q: 장애가 나면 어떤 키가 영향을 받나?
> 의도: 재배치 범위를 이해하는지 확인
> 핵심: 그 노드의 시계 방향 구간에 속한 키들만 주로 재배치된다.

> Q: 분산 캐시에서 왜 많이 쓰나?
> 의도: 운영 맥락과 연결되는지 확인
> 핵심: 캐시 미스를 전체적으로 폭발시키지 않고 국소적으로만 조정할 수 있기 때문이다.

## 한 줄 정리

Consistent Hashing Ring은 노드 증감이 잦은 분산 환경에서 키 재배치를 최소화하기 위한 배치 구조다.
