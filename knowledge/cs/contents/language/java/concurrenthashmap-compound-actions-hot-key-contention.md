---
schema_version: 3
title: ConcurrentHashMap Compound Actions and Hot-Key Contention
concept_id: language/concurrenthashmap-compound-actions-hot-key-contention
canonical: true
category: language
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- concurrenthashmap-compound-action
- computeifabsent-hot-key-contention
- weakly-consistent-iteration
aliases:
- ConcurrentHashMap compound actions
- ConcurrentHashMap hot key contention
- computeIfAbsent pitfall
- check then act race
- weakly consistent iterator
- LongAdder counter
- single flight cache
- Java concurrent map race
symptoms:
- ConcurrentHashMap을 쓰면 get 후 put 같은 복합 동작도 자동으로 원자적이라고 생각하고 있어
- computeIfAbsent 안에서 느린 DB나 HTTP 호출을 해서 hot key 요청이 직렬화되는 문제를 놓치고 있어
- map은 thread-safe인데 value 객체나 iteration snapshot도 안전하다고 오해하고 있어
intents:
- deep_dive
- troubleshooting
prerequisites:
- language/java-concurrency-utilities
- language/java-collections-basics
- data-structure/hash-table-basics
next_docs:
- language/collections-performance
- language/copyonwritearraylist-snapshot-iteration-write-amplification
- language/completablefuture-execution-model-common-pool-pitfalls
- system-design/cache-invalidation-patterns-primer
linked_paths:
- contents/language/java/java-concurrency-utilities.md
- contents/language/java/collections-performance.md
- contents/language/java/copyonwritearraylist-snapshot-iteration-write-amplification.md
- contents/language/java/executor-sizing-queue-rejection-policy.md
- contents/language/java/completablefuture-execution-model-common-pool-pitfalls.md
- contents/language/java/oom-heap-dump-playbook.md
- contents/system-design/cache-invalidation-patterns-primer.md
confusable_with:
- language/collections-performance
- language/copyonwritearraylist-snapshot-iteration-write-amplification
- system-design/cache-invalidation-patterns-primer
forbidden_neighbors: []
expected_queries:
- ConcurrentHashMap에서 get 후 put check-then-act race가 왜 생겨?
- computeIfAbsent 안에 느린 외부 호출을 넣으면 hot key에서 어떤 병목이 생겨?
- ConcurrentHashMap value가 ArrayList면 map만 thread-safe여도 안전하지 않은 이유는 뭐야?
- weakly consistent iterator는 정확한 snapshot과 무엇이 달라?
- high contention counter에서 AtomicLong 대신 LongAdder를 쓰는 이유는 뭐야?
contextual_chunk_prefix: |
  이 문서는 ConcurrentHashMap advanced deep dive로, individual operation safety와 compound action atomicity, computeIfAbsent mapping function, hot-key contention, mutable value safety, weakly consistent iteration, LongAdder counter를 분리한다.
  ConcurrentHashMap race, check then act, computeIfAbsent hot key, cache stampede, weakly consistent iterator 같은 자연어 질문이 본 문서에 매핑된다.
---
# `ConcurrentHashMap` Compound Actions and Hot-Key Contention

> 한 줄 요약: `ConcurrentHashMap`은 개별 연산을 thread-safe하게 만들어주지만, check-then-act race, 긴 `computeIfAbsent()` 로더, hot-key contention, weakly consistent iteration까지 자동으로 해결해주지는 않는다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Java 동시성 유틸리티](./java-concurrency-utilities.md)
> - [Java Collections 성능 감각](./collections-performance.md)
> - [`CopyOnWriteArrayList` Snapshot Iteration and Write Amplification](./copyonwritearraylist-snapshot-iteration-write-amplification.md)
> - [Executor Sizing, Queue, Rejection Policy](./executor-sizing-queue-rejection-policy.md)
> - [CompletableFuture Execution Model and Common Pool Pitfalls](./completablefuture-execution-model-common-pool-pitfalls.md)
> - [OOM Heap Dump Playbook](./oom-heap-dump-playbook.md)

> retrieval-anchor-keywords: ConcurrentHashMap, compound action, check-then-act, computeIfAbsent, compute, merge, LongAdder, hot key contention, cache stampede, per-key lock, weakly consistent iterator, recursive update, mapping function, concurrent counter, CopyOnWriteArrayList

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

`ConcurrentHashMap`을 쓴다고 해서 모든 동시성 문제가 끝나는 것은 아니다.

이 맵이 잘해주는 것은 주로 다음이다.

- 개별 `get`/`put`/`remove`의 thread-safe execution
- 다중 스레드에서의 높은 read concurrency
- coarse-grained global lock보다 나은 확장성

하지만 다음은 직접 설계해야 한다.

- check-then-act workflow의 원자성
- 한 key에 작업이 몰릴 때의 hot-key contention
- map 안에 담긴 mutable value의 thread safety
- iteration 시점의 snapshot 일관성

즉 `ConcurrentHashMap`은 concurrent container이지 concurrent business transaction이 아니다.

## 깊이 들어가기

### 1. 개별 연산 안전성과 복합 동작 안전성은 다르다

다음 코드는 여전히 경쟁 상태를 만들 수 있다.

```java
Value value = map.get(key);
if (value == null) {
    value = load(key);
    map.put(key, value);
}
```

각 줄은 안전할 수 있어도, 전체 workflow는 원자적이지 않다.  
여러 스레드가 동시에 `null`을 보고 중복 load를 수행할 수 있다.

그래서 compound action에는 `computeIfAbsent`, `compute`, `merge` 같은 API를 고려해야 한다.

### 2. `computeIfAbsent()`는 loader를 감싸는 만능 캐시가 아니다

`computeIfAbsent()`는 per-key race를 줄이는 데 유용하지만, mapping function이 길거나 blocking이면 그 key는 사실상 직렬화된다.

주의점:

- mapping function은 짧고 부작용이 적어야 한다
- 같은 map을 다시 건드리면 recursive update 문제가 생길 수 있다
- DB/HTTP 호출을 그 안에서 바로 하면 hot key에서 병목이 커진다

특히 "한 key에 대한 중복 load 방지"와 "느린 외부 호출 실행"을 한 함수에 같이 넣으면 생각보다 쉽게 막힌다.

### 3. hot key는 map 선택보다 access pattern 문제다

`ConcurrentHashMap`은 많은 key가 퍼져 있을 때 잘 확장된다.  
하지만 모두가 같은 key를 두드리면 자료구조보다 그 key가 병목이다.

대표 패턴:

- 인기 상품 하나의 cache key
- tenant 하나에 요청 집중
- 전역 설정 하나를 모든 요청이 매번 reload

이때는 `ConcurrentHashMap`보다 상위 전략이 필요하다.

- stale-while-revalidate
- single-flight future
- batching
- read-through cache 계층

### 4. counter는 `LongAdder`가 더 잘 맞을 때가 많다

높은 contention에서 `AtomicLong` 하나는 한 지점에 CAS 경쟁을 집중시킨다.  
빈도 집계나 metrics counter처럼 읽기보다 쓰기가 많으면 `LongAdder`가 유리할 수 있다.

그래서 흔한 패턴이 이렇다.

```java
counts.computeIfAbsent(key, ignored -> new LongAdder()).increment();
```

단, `LongAdder`도 정확한 snapshot 타이밍이 아주 엄격한 곳에는 맞지 않을 수 있다.

### 5. iteration은 snapshot이 아니다

`ConcurrentHashMap`의 iterator와 aggregate method는 weakly consistent하다.

- concurrent update 중에도 `ConcurrentModificationException` 없이 돌 수 있다
- 하지만 "정확히 이 순간의 전체 상태"를 보장하지 않는다

즉 monitoring, best-effort sweep에는 잘 맞지만,  
정확한 승인/정산/배치 판정에 그대로 쓰면 위험하다.

## 실전 시나리오

### 시나리오 1: 캐시 miss에서 DB가 두 번씩 호출된다

`get` 후 `put` 패턴을 쓰면 race window가 열린다.  
같은 key를 동시에 본 스레드가 각자 DB를 때린다.

이때 문제는 DB가 아니라 compound action 설계다.

### 시나리오 2: `computeIfAbsent()` 안에서 외부 API를 호출한다

특정 key가 인기면 같은 key의 요청들이 그 mapping function 뒤에 줄선다.  
latency spike가 생기고 executor queue까지 밀릴 수 있다.

### 시나리오 3: value 객체 자체가 안전하지 않다

맵은 thread-safe여도, 안에 든 `ArrayList`나 mutable DTO는 별개다.  
`map.get(key).add(...)`는 map이 보호해주지 않는다.

### 시나리오 4: iteration 결과로 business decision을 내린다

배치 스레드가 map을 순회하며 "남은 작업이 0개"라고 판단했는데,  
동시에 다른 스레드가 task를 추가했다면 그 결론은 믿기 어렵다.

## 코드로 보기

### 1. check-then-act anti-pattern

```java
public Value getOrLoad(String key) {
    Value cached = cache.get(key);
    if (cached != null) {
        return cached;
    }

    Value loaded = loadFromDatabase(key);
    cache.put(key, loaded);
    return loaded;
}
```

### 2. 짧은 mapping function만 두고 실제 load는 future로 분리

```java
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;

public final class SingleFlightCache {
    private final ConcurrentHashMap<String, CompletableFuture<Value>> inflight = new ConcurrentHashMap<>();

    public CompletableFuture<Value> load(String key) {
        return inflight.computeIfAbsent(key, ignored ->
            CompletableFuture.supplyAsync(() -> loadFromDatabase(key))
                .whenComplete((result, error) -> inflight.remove(key))
        );
    }

    private Value loadFromDatabase(String key) {
        return new Value(key);
    }

    private record Value(String key) {}
}
```

핵심은 mapping function 안에서 오래 blocking하지 않고, duplicate collapse만 맡기는 것이다.

### 3. 고경합 카운터

```java
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.LongAdder;

ConcurrentHashMap<String, LongAdder> counts = new ConcurrentHashMap<>();
counts.computeIfAbsent("tenant-a", ignored -> new LongAdder()).increment();
```

### 4. value thread safety는 별도 고려

```java
cache.computeIfAbsent(key, ignored -> new java.util.concurrent.CopyOnWriteArrayList<>())
    .add(event);
```

어떤 value 타입을 담는지가 map만큼 중요하다.
이 예시의 snapshot iteration 비용과 write amplification은 [CopyOnWriteArrayList Snapshot Iteration and Write Amplification](./copyonwritearraylist-snapshot-iteration-write-amplification.md)에서 이어서 볼 수 있다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| `ConcurrentHashMap` 기본 연산 | 사용이 쉽고 read-heavy workload에 강하다 | compound action correctness는 직접 챙겨야 한다 |
| `computeIfAbsent()` | per-key race를 줄인다 | 긴 mapping function은 hot key 병목을 만든다 |
| `LongAdder` | 고경합 카운터에 유리하다 | 정확한 순간값 semantics가 더 느슨하다 |
| 외부 캐시/loader 계층 | stampede 제어와 eviction을 체계화할 수 있다 | 운영 복잡도와 의존성이 늘어난다 |

핵심은 자료구조 선택보다 "어떤 key에 어떤 동작을 얼마나 오래 묶는가"다.

## 꼬리질문

> Q: `ConcurrentHashMap`이면 `get` 후 `put`도 안전한가요?
> 핵심: 개별 연산은 안전해도 전체 workflow는 race를 만들 수 있다.

> Q: `computeIfAbsent()` 안에서 DB 호출해도 되나요?
> 핵심: 가능은 하지만 hot key에서 병목과 tail latency를 크게 만들 수 있어 매우 신중해야 한다.

> Q: 왜 `LongAdder`를 쓰나요?
> 핵심: 높은 contention에서 단일 CAS 지점을 줄여 counter update 확장성을 높이기 위해서다.

> Q: map이 thread-safe면 value도 안전한가요?
> 핵심: 아니다. container의 안전성과 value object의 안전성은 별개다.

## 한 줄 정리

`ConcurrentHashMap`은 좋은 concurrent container지만, compound action 원자성, hot-key collapse, value thread safety는 여전히 애플리케이션이 설계해야 한다.
