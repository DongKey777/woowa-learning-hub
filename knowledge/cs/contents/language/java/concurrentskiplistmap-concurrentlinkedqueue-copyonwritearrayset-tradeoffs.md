---
schema_version: 3
title: ConcurrentSkipListMap, ConcurrentLinkedQueue, and CopyOnWriteArraySet Trade-offs
concept_id: language/concurrentskiplistmap-concurrentlinkedqueue-copyonwritearrayset-tradeoffs
canonical: true
category: language
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- java-concurrent-collections
- workload-fit
- iteration-semantics
aliases:
- ConcurrentSkipListMap ConcurrentLinkedQueue CopyOnWriteArraySet tradeoffs
- Java concurrent collection tradeoffs
- ConcurrentLinkedQueue unbounded growth
- CopyOnWriteArraySet snapshot iteration
- ConcurrentSkipListMap range query
- weakly consistent iteration
symptoms:
- concurrent collection이면 모두 thread-safe 대체재라고 보고 sorted range lookup, unbounded FIFO, copy-on-write membership 요구를 구분하지 못해
- ConcurrentLinkedQueue에 bounded backpressure가 없어서 consumer 지연을 memory growth와 latency debt로 숨기는 문제를 놓쳐
- CopyOnWriteArraySet을 write-heavy membership set에 써서 write amplification과 snapshot staleness를 만든다
intents:
- deep_dive
- comparison
- troubleshooting
prerequisites:
- language/java-concurrency-utilities
- language/collections-performance
next_docs:
- language/blockingqueue-transferqueue-concurrentskiplistset-semantics
- language/copyonwritearraylist-snapshot-iteration-write-amplification
- language/concurrenthashmap-compound-actions-hot-key-contention
linked_paths:
- contents/language/java/collections-performance.md
- contents/language/java/blockingqueue-transferqueue-concurrentskiplistset-semantics.md
- contents/language/java/copyonwritearraylist-snapshot-iteration-write-amplification.md
- contents/language/java/concurrenthashmap-compound-actions-hot-key-contention.md
confusable_with:
- language/blockingqueue-transferqueue-concurrentskiplistset-semantics
- language/copyonwritearraylist-snapshot-iteration-write-amplification
- language/concurrenthashmap-compound-actions-hot-key-contention
forbidden_neighbors: []
expected_queries:
- ConcurrentSkipListMap ConcurrentLinkedQueue CopyOnWriteArraySet을 workload 기준으로 비교해줘
- ConcurrentLinkedQueue가 thread-safe해도 bounded backpressure가 없어서 위험한 이유가 뭐야?
- CopyOnWriteArraySet은 listener registry에는 맞지만 churn이 큰 membership set에는 왜 부적합해?
- ConcurrentSkipListMap은 ConcurrentHashMap에 정렬을 더한 대체재인지 range lookup 전용인지 알려줘
- weakly consistent iteration과 snapshot iteration, current-state exactness를 구분해줘
contextual_chunk_prefix: |
  이 문서는 ConcurrentSkipListMap, ConcurrentLinkedQueue, CopyOnWriteArraySet을 sorted range lookup, unbounded FIFO, snapshot/read-mostly membership, weakly consistent iteration 관점으로 비교하는 advanced deep dive다.
  Java concurrent collection tradeoff, ConcurrentLinkedQueue backpressure, CopyOnWriteArraySet, ConcurrentSkipListMap range query 질문이 본 문서에 매핑된다.
---
# `ConcurrentSkipListMap`, `ConcurrentLinkedQueue`, and `CopyOnWriteArraySet` Trade-offs

> 한 줄 요약: concurrent collection이라고 해서 용도가 비슷한 것은 아니다. 정렬된 concurrent map, lock-free FIFO queue, read-mostly snapshot set는 각자 전혀 다른 비용 모델을 가지며, 이를 혼동하면 stale iteration, ordering 오해, unbounded growth가 생긴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Java Collections 성능 감각](./collections-performance.md)
> - [`ConcurrentHashMap` Compound Actions and Hot-Key Contention](./concurrenthashmap-compound-actions-hot-key-contention.md)
> - [`CopyOnWriteArrayList` Snapshot Iteration and Write Amplification](./copyonwritearraylist-snapshot-iteration-write-amplification.md)
> - [Java 동시성 유틸리티](./java-concurrency-utilities.md)

> retrieval-anchor-keywords: ConcurrentSkipListMap, ConcurrentLinkedQueue, CopyOnWriteArraySet, concurrent collection tradeoff, sorted concurrent map, lock-free queue, snapshot set, weakly consistent iteration, concurrent ordering, unbounded queue growth, read mostly set

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

세 컬렉션은 각기 다른 질문에 답한다.

- `ConcurrentSkipListMap`: 정렬된 key space가 필요한가
- `ConcurrentLinkedQueue`: lock-free FIFO handoff가 필요한가
- `CopyOnWriteArraySet`: 읽기가 압도적으로 많고 snapshot-style set이 필요한가

즉 "멀티스레드 컬렉션"이라는 공통점만 보고 바꾸면 안 된다.

## 깊이 들어가기

### 1. `ConcurrentSkipListMap`은 concurrent + sorted map이다

정렬과 범위 검색이 필요한 concurrent workload에 맞는다.

- `ceilingKey`, `floorEntry`
- range query
- 자연 순서 기반 iteration

하지만 hash map보다 보통 느리고, comparator/ordering semantics가 더 중요하다.

즉 "ConcurrentHashMap + 정렬" 대체재가 아니라,  
정렬된 key space가 본질일 때만 쓴다.

### 2. `ConcurrentLinkedQueue`는 non-blocking FIFO다

장점:

- lock-free queue semantics
- producer/consumer 경합에서 단순하다

주의점:

- bounded backpressure가 없다
- queue size 판단이 비싸거나 애매할 수 있다
- unbounded growth가 쉽게 생긴다

즉 queue가 있다는 사실보다 "얼마나 쌓일 수 있나"가 더 중요하다.

### 3. `CopyOnWriteArraySet`은 write 비용을 읽기 안정성으로 바꾼다

이 set은 내부적으로 copy-on-write 특성을 공유한다.

- iteration이 단순하다
- 읽는 쪽 snapshot 안정성이 좋다
- 쓰기가 드물 때 잘 맞는다

하지만 add/remove가 잦으면 set이라도 write amplification이 그대로 문제다.

즉 listener/subscriber registry에는 좋고, churn이 큰 membership set엔 부적합할 수 있다.

### 4. weakly consistent vs snapshot vs current-state를 구분해야 한다

concurrent collection에서 iteration 의미가 중요하다.

- weakly consistent iteration
- snapshot iteration
- current-state exactness

이 셋은 다르다.

정확한 "지금 현재" 판정을 business logic에 얹고 싶다면,  
컬렉션 종류만 바꿔선 해결되지 않는다.

### 5. boundedness는 별도 설계다

특히 `ConcurrentLinkedQueue` 같은 lock-free queue는 쉽게 "잘 돌아간다"고 느껴진다.  
하지만 bounded backpressure가 없으면 latency debt와 memory growth를 숨길 수 있다.

즉 concurrent collection 선택은 thread safety보다 workload control과 함께 봐야 한다.

## 실전 시나리오

### 시나리오 1: 시각 순 정렬된 작업 예약 맵이 필요하다

key ordering과 range lookup이 핵심이면 `ConcurrentSkipListMap`이 자연스럽다.  
단순 동시 접근만 필요하다면 `ConcurrentHashMap`이 더 싸다.

### 시나리오 2: 이벤트 큐를 간단히 붙였는데 메모리가 늘어난다

`ConcurrentLinkedQueue` 자체는 안전해 보여도,  
consumer가 늦으면 unbounded queue가 된다.

### 시나리오 3: subscriber set을 자주 순회한다

변경은 드물고 broadcast가 많다면 `CopyOnWriteArraySet`이 잘 맞을 수 있다.  
반대로 connect/disconnect churn이 크면 비용이 커진다.

## 코드로 보기

### 1. 정렬된 concurrent map

```java
java.util.concurrent.ConcurrentSkipListMap<Long, Job> jobsByDeadline =
    new java.util.concurrent.ConcurrentSkipListMap<>();
```

### 2. lock-free queue

```java
java.util.concurrent.ConcurrentLinkedQueue<Event> queue =
    new java.util.concurrent.ConcurrentLinkedQueue<>();
```

### 3. read-mostly set

```java
java.util.concurrent.CopyOnWriteArraySet<Listener> listeners =
    new java.util.concurrent.CopyOnWriteArraySet<>();
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| `ConcurrentSkipListMap` | 정렬과 범위 검색이 가능하다 | 해시 기반보다 무겁고 ordering contract가 중요하다 |
| `ConcurrentLinkedQueue` | lock-free FIFO가 단순하다 | bounded backpressure가 없어 unbounded growth 위험이 있다 |
| `CopyOnWriteArraySet` | read-mostly iteration이 단순하다 | write amplification이 크다 |

핵심은 concurrent collection을 thread-safe container가 아니라 **ordering, boundedness, iteration semantics를 가진 contract**로 보는 것이다.

## 꼬리질문

> Q: `ConcurrentSkipListMap`은 언제 쓰나요?
> 핵심: 정렬된 key와 범위 검색이 동시성보다 본질일 때 쓴다.

> Q: `ConcurrentLinkedQueue`면 큐 문제가 해결되나요?
> 핵심: thread safety는 얻지만 backpressure와 boundedness는 별도 설계가 필요하다.

> Q: `CopyOnWriteArraySet`은 어디에 잘 맞나요?
> 핵심: read-mostly subscriber/listener set처럼 순회가 많고 변경이 드문 경우다.

## 한 줄 정리

`ConcurrentSkipListMap`, `ConcurrentLinkedQueue`, `CopyOnWriteArraySet`은 서로 다른 ordering·queueing·snapshot contract를 가진 도구라서, thread safety보다 workload 의미를 먼저 맞춰야 한다.
