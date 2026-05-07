---
schema_version: 3
title: CopyOnWriteArrayList Snapshot Iteration and Write Amplification
concept_id: language/copyonwritearraylist-snapshot-iteration-write-amplification
canonical: true
category: language
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- concurrent-collection
- copy-on-write
- write-amplification
aliases:
- CopyOnWriteArrayList snapshot iteration
- CopyOnWriteArrayList write amplification
- read mostly collection
- listener registry collection
- stale snapshot iterator
- copy on write array list
symptoms:
- CopyOnWriteArrayList를 thread-safe ArrayList로만 보고 write마다 전체 배열 복사가 발생하는 비용 모델을 놓쳐
- iterator가 생성 시점 snapshot을 보므로 최신 current-state 판정에는 맞지 않는다는 점을 모른다
- listener registry처럼 read-mostly에는 맞지만 request마다 갱신되는 write-heavy path에서는 allocation burst와 GC pressure를 만든다
intents:
- deep_dive
- comparison
- troubleshooting
prerequisites:
- language/collections-performance
next_docs:
- language/concurrentskiplistmap-concurrentlinkedqueue-copyonwritearrayset-tradeoffs
- language/concurrenthashmap-compound-actions-hot-key-contention
- language/oom-heap-dump-playbook
linked_paths:
- contents/language/java/collections-performance.md
- contents/language/java/concurrenthashmap-compound-actions-hot-key-contention.md
- contents/language/java/java-concurrency-utilities.md
- contents/language/java/oom-heap-dump-playbook.md
confusable_with:
- language/concurrentskiplistmap-concurrentlinkedqueue-copyonwritearrayset-tradeoffs
- language/concurrenthashmap-compound-actions-hot-key-contention
- language/collections-performance
forbidden_neighbors: []
expected_queries:
- CopyOnWriteArrayList는 thread-safe ArrayList가 아니라 snapshot iteration과 write amplification 구조라는 뜻이야?
- CopyOnWriteArrayList iterator가 최신 상태가 아니라 생성 시점 snapshot을 보는 이유를 설명해줘
- listener registry에는 CopyOnWriteArrayList가 맞고 write-heavy queue에는 왜 부적합해?
- CopyOnWriteArrayList add remove가 큰 리스트에서 allocation과 GC pressure를 만드는 이유가 뭐야?
- stale snapshot을 business decision에 쓰면 어떤 버그가 생길 수 있어?
contextual_chunk_prefix: |
  이 문서는 CopyOnWriteArrayList를 snapshot iteration, copy-on-write array replacement, read-mostly listener registry, write amplification, stale snapshot 관점으로 설명하는 advanced deep dive다.
  CopyOnWriteArrayList, snapshot iterator, write amplification, listener registry, stale snapshot 질문이 본 문서에 매핑된다.
---
# `CopyOnWriteArrayList` Snapshot Iteration and Write Amplification

> 한 줄 요약: `CopyOnWriteArrayList`는 thread-safe `ArrayList`가 아니라 "읽을 때 snapshot을 보고, 쓸 때 전체 배열을 복사하는" 컬렉션이다. listener registry나 read-mostly 설정 목록에는 잘 맞지만, write-heavy 경로에 넣으면 allocation과 stale snapshot 버그를 만든다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Java Collections 성능 감각](./collections-performance.md)
> - [`ConcurrentHashMap` Compound Actions and Hot-Key Contention](./concurrenthashmap-compound-actions-hot-key-contention.md)
> - [Java 동시성 유틸리티](./java-concurrency-utilities.md)
> - [OOM Heap Dump Playbook](./oom-heap-dump-playbook.md)

> retrieval-anchor-keywords: CopyOnWriteArrayList, snapshot iteration, write amplification, listener registry, read mostly collection, stale snapshot, copy on write, thread-safe iteration, concurrent collection, allocation burst

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

`CopyOnWriteArrayList`의 읽기와 쓰기 비용 모델은 비대칭이다.

- 읽기: lock-free에 가깝게 현재 snapshot을 본다
- 쓰기: 내부 배열 전체를 새로 복사한다

즉 장점은:

- iteration이 안전하고 단순하다
- 읽는 쪽이 lock 경쟁에 덜 민감하다

하지만 비용은:

- write마다 배열 복사
- 큰 리스트일수록 allocation 증가
- iterator가 최신 값이 아니라 생성 시점 snapshot을 본다

이다.

## 깊이 들어가기

### 1. iterator는 live view가 아니다

`CopyOnWriteArrayList` iterator는 생성 시점 배열 snapshot을 본다.  
즉 순회 도중 다른 thread가 add/remove해도 iterator는 그 변화를 보지 않는다.

이건 장점이면서 함정이다.

- `ConcurrentModificationException`이 거의 없다
- 하지만 "지금 현재 상태"를 보고 있다고 착각하면 안 된다

즉 monitoring이나 listener broadcast엔 좋을 수 있지만,  
정확한 동시 상태 판정엔 맞지 않을 수 있다.

### 2. write amplification은 생각보다 빠르게 비싸진다

원소 1개 추가도 내부적으로 새 배열을 만든다.  
리스트가 크거나 write 빈도가 높으면:

- allocation burst
- old array churn
- GC pressure

가 생긴다.

즉 synchronized list보다 "항상 빠른 concurrent list"가 아니다.

### 3. listener registry에는 잘 맞는다

대표적인 적합 사례:

- 이벤트 리스너 목록
- 읽기가 압도적으로 많은 설정 목록
- 변경이 드문 subscriber 집합

이 경우는:

- 순회가 많고
- 변경은 드물며
- 순회 중 구조 변경이 터지지 않아야 한다

는 요구를 잘 만족시킨다.

### 4. queue나 hot write list로 쓰면 안 된다

다음에는 보통 부적합하다.

- request log buffer
- 작업 큐
- 자주 변하는 세션 목록
- write-heavy cache value list

이런 곳은 자료구조 특성과 workload가 정면으로 충돌한다.

### 5. stale snapshot을 business decision에 쓰지 않는다

snapshot iterator는 consistency가 아니라 isolation을 준다.  
그래서 "현재 등록자 수", "최신 listener 목록", "삭제 직후 존재 여부" 같은 판단을 그대로 얹으면 오해가 생길 수 있다.

## 실전 시나리오

### 시나리오 1: listener 목록 broadcast가 간단해야 한다

순회 중 add/remove가 있어도 현재 broadcast를 깨고 싶지 않다면 `CopyOnWriteArrayList`가 자연스럽다.

### 시나리오 2: request마다 리스트를 갱신한다

write-heavy workload에 `CopyOnWriteArrayList`를 넣으면 성능이 느려지는 이유가 lock이 아니라 복사 비용일 수 있다.

### 시나리오 3: 순회 결과로 "현재 구독자 없음"을 판정한다

iterator snapshot은 최신 상태가 아닐 수 있으므로,  
정확한 membership 판단엔 별도 동기화나 다른 자료구조가 더 맞을 수 있다.

### 시나리오 4: heap dump에 `Object[]`가 많이 보인다

작은 write가 많았던 `CopyOnWriteArrayList`는 allocation churn을 만들 수 있다.  
이때 문제는 메모리 leak이 아니라 workload와 자료구조 불일치일 수 있다.

## 코드로 보기

### 1. listener registry

```java
import java.util.concurrent.CopyOnWriteArrayList;

CopyOnWriteArrayList<Listener> listeners = new CopyOnWriteArrayList<>();

for (Listener listener : listeners) {
    listener.onEvent(event);
}
```

### 2. write-heavy anti-pattern 감각

```java
events.add(newEvent); // add마다 내부 배열 복사
```

### 3. snapshot iterator 감각

```java
for (String value : list) {
    // 순회 중 다른 thread가 add/remove해도
    // 현재 iterator는 기존 snapshot을 본다.
}
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| `CopyOnWriteArrayList` | snapshot iteration이 단순하고 읽기 경쟁이 적다 | write amplification과 stale snapshot semantics가 있다 |
| synchronized list | 모델이 단순하다 | 읽기/쓰기 모두 lock 경쟁이 생긴다 |
| queue/set/map 기반 대안 | workload에 더 잘 맞을 수 있다 | 사용 목적에 따라 API가 달라진다 |

핵심은 이 컬렉션을 "concurrent list"가 아니라 "read-mostly snapshot list"로 보는 것이다.

## 꼬리질문

> Q: `CopyOnWriteArrayList` iterator는 최신 값을 보나요?
> 핵심: 아니다. iterator 생성 시점 snapshot을 본다.

> Q: 왜 write-heavy workload에 안 맞나요?
> 핵심: 작은 변경도 내부 배열 전체 복사를 유발해 allocation과 GC 비용이 커지기 때문이다.

> Q: 언제 잘 맞나요?
> 핵심: listener registry나 드물게 바뀌는 설정 목록처럼 read-mostly workload에 잘 맞는다.

> Q: `ConcurrentModificationException`이 안 나면 안전한 건가요?
> 핵심: 구조적 예외는 줄지만, 최신 상태를 본다는 뜻은 아니다.

## 한 줄 정리

`CopyOnWriteArrayList`는 읽기 안정성을 위해 쓰기 복사를 감수하는 자료구조이므로, snapshot iteration이 장점인 read-mostly workload에만 쓰는 편이 안전하다.
