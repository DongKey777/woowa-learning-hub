---
schema_version: 3
title: StampedLock Optimistic Read and Conversion Pitfalls
concept_id: language/stampedlock-optimistic-read-conversion-pitfalls
canonical: true
category: language
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 85
mission_ids:
- missions/racingcar
- missions/payment
review_feedback_tags:
- concurrency
- stampedlock
- optimistic-read
aliases:
- StampedLock Optimistic Read and Conversion Pitfalls
- StampedLock optimistic read validate
- tryConvertToWriteLock failure
- StampedLock non-reentrant
- optimistic read mutable object graph
- 자바 StampedLock optimistic read
symptoms:
- StampedLock optimistic read를 lock-free snapshot처럼 이해해 validate 전 값으로 부작용을 일으키거나 검증 실패 fallback을 빠뜨려
- StampedLock이 non-reentrant라는 점을 모르고 lock을 잡은 채 같은 lock 경로로 재진입하는 메서드나 callback을 호출해
- tryConvertToWriteLock이 항상 성공한다고 가정해 read 후 조건 확인과 write upgrade 실패 경로를 안전하게 설계하지 않아
intents:
- troubleshooting
- deep_dive
- design
prerequisites:
- language/java-concurrency-utilities
- language/thread-dump-state-interpretation
- language/java-memory-model-happens-before-volatile-final
next_docs:
- language/varhandle-unsafe-atomics
- language/locksupport-park-unpark-permit-semantics
- language/thread-interruption-cooperative-cancellation-playbook
linked_paths:
- contents/language/java/java-concurrency-utilities.md
- contents/language/java/thread-dump-state-interpretation.md
- contents/language/java/varhandle-unsafe-atomics.md
- contents/language/java-memory-model-happens-before-volatile-final.md
confusable_with:
- language/java-concurrency-utilities
- language/varhandle-unsafe-atomics
- language/thread-dump-state-interpretation
forbidden_neighbors: []
expected_queries:
- StampedLock optimistic read는 lock-free snapshot이 아니라 validate하는 추측이라는 뜻이 뭐야?
- StampedLock optimistic read에서 validate 실패 시 read lock fallback을 어떻게 설계해야 해?
- mutable object graph를 optimistic read로 읽으면 서로 다른 시점 값이 섞일 수 있는 이유가 뭐야?
- StampedLock은 non-reentrant라서 ReentrantReadWriteLock과 어떤 사고방식이 달라?
- tryConvertToWriteLock이 실패할 수 있는 fast path라면 update flow를 어떻게 짜야 해?
contextual_chunk_prefix: |
  이 문서는 StampedLock optimistic read, validate, read fallback, non-reentrant behavior, tryConvertToWriteLock failure, mutable object graph pitfalls를 점검하는 advanced playbook이다.
  StampedLock, optimistic read, validate, lock conversion, non-reentrant 질문이 본 문서에 매핑된다.
---
# `StampedLock` Optimistic Read and Conversion Pitfalls

> 한 줄 요약: `StampedLock`의 optimistic read는 lock-free snapshot이 아니라 "읽고 나서 validate하는 추측"이다. non-reentrant 특성, lock conversion 실패, 긴 읽기 구간, mutable object graph를 함께 이해하지 않으면 오히려 더 위험한 동시성 코드를 만들 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Java 동시성 유틸리티](./java-concurrency-utilities.md)
> - [Thread Dump State Interpretation](./thread-dump-state-interpretation.md)
> - [VarHandle, Unsafe, Atomics](./varhandle-unsafe-atomics.md)
> - [Java Memory Model, Happens-Before, `volatile`, `final`](../java-memory-model-happens-before-volatile-final.md)

> retrieval-anchor-keywords: StampedLock, optimistic read, validate, lock conversion, tryConvertToWriteLock, non-reentrant lock, read mostly workload, mutable object graph, write starvation, optimistic snapshot, backend contention

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

`StampedLock`은 세 가지 모드를 제공한다.

- write lock
- read lock
- optimistic read

여기서 optimistic read는 "안 잠그고 읽어도 괜찮을 것이라 가정하고, 나중에 검증하는 방식"이다.

즉 의미가 다르다.

- read lock: 실제로 읽기 락을 잡는다
- optimistic read: 잠그지 않고 stamp만 받아 later validation 한다

그래서 optimistic read는 snapshot 보장 자체가 아니라 **검증 가능한 추측**이다.

## 깊이 들어가기

### 1. optimistic read는 읽은 뒤 validate해야 한다

전형적인 패턴은 이렇다.

- optimistic stamp 획득
- 필요한 필드를 지역 변수로 읽음
- `validate(stamp)` 호출
- 실패하면 read lock으로 다시 읽음

즉 먼저 읽고 나중에 검증한다.  
검증 전 값에 기반해 부작용을 일으키면 안 된다.

### 2. mutable object graph에서는 더 조심해야 한다

primitive 두 개 읽는 정도는 비교적 안전하게 설명하기 쉽다.  
하지만 reference graph를 따라가면 문제가 커진다.

- 객체 참조는 읽었는데 내부 필드가 바뀐다
- 컬렉션 크기와 실제 요소 상태가 엇갈린다
- 읽은 여러 필드가 서로 다른 시점 값을 섞는다

즉 optimistic read는 짧고 단순한 state snapshot에 더 잘 맞는다.

### 3. `StampedLock`은 reentrant가 아니다

같은 thread가 다시 같은 lock을 잡는다고 안전하지 않다.  
콜백, 로깅, 다른 메서드 재진입이 섞이면 예상보다 쉽게 꼬인다.

그래서 다음 패턴은 위험하다.

- lock 잡은 채 다른 메서드 호출
- 그 메서드가 다시 같은 lock 경로를 탐
- 재귀 구조와 함께 사용

이건 `ReentrantReadWriteLock`과 사고방식이 다르다.

### 4. lock conversion도 항상 성공하는 게 아니다

`tryConvertToWriteLock()` 같은 API는 유용해 보이지만,  
항상 upgrade가 되는 것은 아니다.

즉 read 후 조건 확인, 그다음 write로 승격하는 흐름은  
"실패할 수 있는 fast path"로 설계해야 한다.

성공만 가정하면 fallback 경로가 빠지고 correctness가 흔들린다.

### 5. 성능 이득은 workload가 맞을 때만 나온다

`StampedLock`은 read-mostly, short critical section, simple state일 때 이득이 있을 수 있다.  
하지만 write가 자주 오거나 읽기 구간이 길면 복잡도만 늘어난다.

즉 "고급 lock이니 더 빠르다"가 아니라,  
workload가 lock model과 맞는지부터 봐야 한다.

## 실전 시나리오

### 시나리오 1: 캐시 메타데이터를 자주 읽고 드물게 갱신한다

size, version, lastUpdated 같은 짧은 필드 집합이면 optimistic read 후보가 될 수 있다.  
하지만 읽은 값으로 바로 외부 부작용을 일으키면 fallback이 어려워진다.

### 시나리오 2: 객체 그래프를 optimistic read로 순회한다

참조를 따라가며 많은 값을 읽는 순간 validate 성공 의미가 약해진다.  
짧은 scalar snapshot이 아니면 이득보다 위험이 커질 수 있다.

### 시나리오 3: 같은 서비스 메서드에서 lock 재진입이 생긴다

코드 구조가 예쁘게 분리되어 보여도,  
내부적으로 같은 `StampedLock`을 다시 타면 자기 자신과 충돌할 수 있다.

### 시나리오 4: thread dump에 lock 경합이 보이는데 `StampedLock`으로 바꾸고 싶다

원인이 긴 critical section이나 mutable graph라면 lock 타입 변경만으로는 해결되지 않는다.  
immutable snapshot, copy-on-write, state partition이 더 맞을 수 있다.

## 코드로 보기

### 1. 전형적인 optimistic read 패턴

```java
import java.util.concurrent.locks.StampedLock;

public final class Point {
    private final StampedLock lock = new StampedLock();
    private double x;
    private double y;

    public double distanceFromOrigin() {
        long stamp = lock.tryOptimisticRead();
        double currentX = x;
        double currentY = y;

        if (!lock.validate(stamp)) {
            stamp = lock.readLock();
            try {
                currentX = x;
                currentY = y;
            } finally {
                lock.unlockRead(stamp);
            }
        }

        return Math.hypot(currentX, currentY);
    }
}
```

### 2. conversion은 fallback을 전제로 한다

```java
long stamp = lock.readLock();
try {
    if (needsWrite()) {
        long writeStamp = lock.tryConvertToWriteLock(stamp);
        if (writeStamp == 0L) {
            lock.unlockRead(stamp);
            stamp = lock.writeLock();
        } else {
            stamp = writeStamp;
        }
        mutate();
    }
} finally {
    lock.unlock(stamp);
}
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| `StampedLock` optimistic read | read-mostly workload에서 이득이 있을 수 있다 | validate/fallback, non-reentrant 제약, 코드 복잡도가 크다 |
| `ReentrantReadWriteLock` | 모델이 더 익숙하고 reentrant다 | optimistic path는 없다 |
| immutable snapshot/copy-on-write | correctness reasoning이 쉽다 | 쓰기 비용과 메모리 비용이 늘 수 있다 |
| plain `synchronized` | 가장 단순하다 | 고경합 read-heavy workload엔 비효율적일 수 있다 |

핵심은 `StampedLock`을 속도 도구가 아니라 **reasoning 비용이 비싼 특수 lock**으로 보는 것이다.

## 꼬리질문

> Q: optimistic read는 lock을 잡는 건가요?
> 핵심: 아니다. 값을 읽은 뒤 stamp validation으로 충돌이 없었는지 확인하는 방식이다.

> Q: 왜 validate 전에 읽은 값으로 부작용을 내면 안 되나요?
> 핵심: 그 값이 일관된 snapshot이 아닐 수 있어서 fallback으로 복구할 수 없기 때문이다.

> Q: `StampedLock`은 왜 조심해야 하나요?
> 핵심: non-reentrant이고 mutable graph에서 reasoning이 어려워 correctness bug를 만들기 쉽기 때문이다.

> Q: 언제 고려할 만한가요?
> 핵심: 읽기가 압도적으로 많고 짧은 scalar state를 읽는 경우에 한해 신중히 고려할 만하다.

## 한 줄 정리

`StampedLock`의 optimistic read는 "싸게 읽는다"가 아니라 "검증 가능한 추측을 한다"는 모델이므로, 짧은 state snapshot이 아닌 곳에 무리하게 쓰면 위험하다.
