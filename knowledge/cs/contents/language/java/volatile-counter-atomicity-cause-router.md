---
schema_version: 3
title: Java volatile counter atomicity cause router
concept_id: language/java-volatile-counter-atomicity-cause-router
canonical: false
category: language
difficulty: intermediate
doc_role: symptom_router
level: intermediate
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- volatile-visibility-not-atomicity
- counter-lost-update-router
- atomic-synchronized-longadder-choice
aliases:
- volatile counter atomicity router
- volatile count++ bug
- Java counter lost update
- volatile atomicinteger synchronized longadder
- count++ lost update cause
- volatile인데 값이 누락돼요
- atomicity visibility ordering counter
- LongAdder 언제 쓰나요
- AtomicInteger vs synchronized counter
- JCStress lost update test
symptoms:
- volatile int에 count++를 했는데 최종 값이 기대보다 작아
- 최신값은 보이는 것 같은데 증가 연산이 누락되는 이유를 모르겠어
- AtomicInteger와 synchronized와 LongAdder 중 무엇을 써야 할지 헷갈려
intents:
- symptom
- troubleshooting
prerequisites:
- language/java-memory-model-happens-before-volatile-final
- language/java-thread-basics
next_docs:
- language/volatile-long-double-atomicity-memory-visibility
- language/varhandle-unsafe-atomics
- language/concurrenthashmap-compound-actions-hot-key-contention
- language/jcstress-concurrency-testing
- operating-system/context-switching-deadlock-lockfree
linked_paths:
- contents/language/java-memory-model-happens-before-volatile-final.md
- contents/language/java/java-thread-basics.md
- contents/language/java/volatile-long-double-atomicity-memory-visibility.md
- contents/language/java/varhandle-unsafe-atomics.md
- contents/language/java/concurrenthashmap-compound-actions-hot-key-contention.md
- contents/language/java/jcstress-concurrency-testing.md
- contents/operating-system/context-switching-deadlock-lockfree.md
- contents/operating-system/cpu-cache-coherence-memory-barrier.md
confusable_with:
- language/java-memory-model-happens-before-volatile-final
- language/volatile-long-double-atomicity-memory-visibility
- language/varhandle-unsafe-atomics
- operating-system/context-switching-deadlock-lockfree
forbidden_neighbors: []
expected_queries:
- volatile int count++를 여러 스레드에서 했는데 값이 왜 누락돼?
- volatile은 최신값을 보장한다는데 원자성은 왜 안 되는 거야?
- counter에는 AtomicInteger, synchronized, LongAdder 중 무엇을 써야 해?
- LongAdder는 빠르다는데 정확한 순간값이 필요할 때도 써도 돼?
- lost update가 진짜 나는지 JCStress로 어떻게 확인해?
contextual_chunk_prefix: |
  이 문서는 Java에서 volatile counter에 count++를 적용했는데 lost update가 발생하는 증상을 atomicity, visibility, ordering 관점으로 분기하는 symptom router다.
  volatile은 visibility와 ordering에는 도움을 주지만 read-modify-write 원자성을 만들지 못한다는 점, AtomicInteger와 synchronized와 LongAdder 선택, JCStress로 재현하는 방법 같은 자연어 질문이 본 문서에 매핑된다.
---
# Java volatile counter atomicity cause router

> 한 줄 요약: `volatile`은 다른 스레드가 값을 보게 돕지만 `count++`의 읽기-수정-쓰기 전체를 하나로 묶지 않으므로, 카운터 누락 증상은 `AtomicInteger`, `synchronized`, `LongAdder` 중 요구 semantics에 맞춰 분기해야 한다.

retrieval-anchor-keywords: volatile counter atomicity router, volatile count++ bug, Java counter lost update, volatile atomicinteger synchronized longadder, count++ lost update cause, volatile인데 값이 누락돼요, atomicity visibility ordering counter, LongAdder 언제 쓰나요, AtomicInteger vs synchronized counter, JCStress lost update test

**난이도: 🟡 Intermediate**

관련 문서:

- [Java Memory Model, Happens-Before, volatile, final](../java-memory-model-happens-before-volatile-final.md)
- [Java Thread Basics](./java-thread-basics.md)
- [volatile long/double atomicity and memory visibility](./volatile-long-double-atomicity-memory-visibility.md)
- [VarHandle, Unsafe, Atomics](./varhandle-unsafe-atomics.md)
- [ConcurrentHashMap compound actions and hot-key contention](./concurrenthashmap-compound-actions-hot-key-contention.md)
- [JCStress Concurrency Testing](./jcstress-concurrency-testing.md)
- [컨텍스트 스위칭, 데드락, lock-free](../../operating-system/context-switching-deadlock-lockfree.md)

---

## 먼저 보는 증상

가장 흔한 코드는 아래처럼 생겼다.

```java
class Counter {
    private volatile int value;

    void increment() {
        value++;
    }

    int value() {
        return value;
    }
}
```

여러 스레드가 동시에 `increment()`를 호출하면 최종 값이 기대보다 작을 수 있다.
이때 문제는 `volatile`이 동작하지 않은 것이 아니라, `volatile`이 보장하는 것과 `count++`에 필요한 것이 다르다는 데 있다.

| 필요한 것 | `volatile`이 주는가 | 설명 |
|---|---:|---|
| 다른 스레드가 쓴 값을 볼 가능성 | 예 | visibility에 관여한다 |
| 읽기/쓰기 재정렬 제한 | 예 | ordering에 관여한다 |
| `읽기 -> +1 -> 쓰기` 전체 원자성 | 아니오 | read-modify-write는 여전히 쪼개진다 |

핵심 문장:

- `volatile`은 관찰을 돕는다.
- `volatile`은 복합 갱신을 하나의 임계영역으로 만들지 않는다.

## 30초 분기표

| 지금 원하는 semantics | 먼저 고를 도구 | 왜 |
|---|---|---|
| 단일 숫자를 정확히 원자적으로 증가 | `AtomicInteger` / `AtomicLong` | CAS 기반 원자 증가를 제공한다 |
| 여러 필드를 한 번에 일관되게 바꿈 | `synchronized` 또는 lock | 한 임계영역 안에 복합 상태를 묶는다 |
| metrics처럼 쓰기가 많고 순간 정확성이 덜 엄격 | `LongAdder` | 경합을 분산해 throughput을 높인다 |
| 저수준 메모리 오더나 필드 접근 제어 | `VarHandle` | 일반 서비스 코드보다 라이브러리/런타임 쪽에 가깝다 |
| 정말 재현되는지 증명 | `JCStress` | JMM outcome을 반복 실험으로 확인한다 |

## 왜 `count++`는 깨지나

`count++`는 한 명령처럼 보여도 보통 아래 세 단계다.

```text
1. value 읽기
2. 읽은 값에 1 더하기
3. value에 다시 쓰기
```

두 스레드가 동시에 `0`을 읽으면 둘 다 `1`을 계산하고 둘 다 `1`을 쓴다.
호출은 두 번이었지만 최종 값은 `2`가 아니라 `1`이 된다.
이것이 lost update다.

`volatile`은 마지막 쓰기가 보이게 도와도, 두 스레드가 같은 old value를 읽는 일을 막지 못한다.

## 선택 예시

### 단일 counter면 `AtomicInteger`

```java
import java.util.concurrent.atomic.AtomicInteger;

class Counter {
    private final AtomicInteger value = new AtomicInteger();

    int increment() {
        return value.incrementAndGet();
    }

    int value() {
        return value.get();
    }
}
```

단일 값 증가라면 이 선택이 가장 단순하다.

### 복합 상태면 `synchronized`

```java
class Inventory {
    private int stock;
    private int reserved;

    synchronized boolean reserve() {
        if (stock <= reserved) {
            return false;
        }
        reserved++;
        return true;
    }
}
```

`stock`과 `reserved`처럼 여러 필드를 함께 봐야 하면 `AtomicInteger` 하나로 문제를 가리기 어렵다.
이때는 상태 불변식을 임계영역으로 묶는 편이 더 읽기 쉽다.

### 고경합 metrics면 `LongAdder`

```java
import java.util.concurrent.atomic.LongAdder;

class Metrics {
    private final LongAdder requests = new LongAdder();

    void recordRequest() {
        requests.increment();
    }

    long snapshot() {
        return requests.sum();
    }
}
```

`LongAdder`는 쓰기 경합을 줄이는 데 유리하다.
대신 아주 엄격한 순간값 semantics가 필요한 도메인 판정에는 먼저 맞는지 검토해야 한다.

## 흔한 오해

- `volatile`이면 최신값이니까 증가도 안전하다고 생각하기 쉽다. 최신성/가시성과 복합 연산 원자성은 다르다.
- `AtomicInteger`면 모든 동시성 문제가 끝난다고 생각하기 쉽다. 여러 필드의 불변식은 별도 설계가 필요하다.
- `LongAdder`가 항상 `AtomicLong`보다 낫다고 생각하기 쉽다. 고경합 counter에는 유리하지만 strict snapshot이 필요한 곳에는 semantics를 확인해야 한다.
- 테스트가 한 번 통과하면 안전하다고 생각하기 쉽다. lost update는 타이밍 문제라 반복과 outcome 기반 검증이 필요하다.

## 다음으로 어디를 볼까

- `volatile` 자체의 visibility/order를 더 보려면 [Java Memory Model, Happens-Before, volatile, final](../java-memory-model-happens-before-volatile-final.md)
- `volatile long/double`의 읽기/쓰기 원자성과 복합 연산 차이를 보려면 [volatile long/double atomicity and memory visibility](./volatile-long-double-atomicity-memory-visibility.md)
- CAS와 VarHandle까지 내려가려면 [VarHandle, Unsafe, Atomics](./varhandle-unsafe-atomics.md)
- `ConcurrentHashMap<String, LongAdder>` 같은 hot-key counter가 궁금하면 [ConcurrentHashMap compound actions and hot-key contention](./concurrenthashmap-compound-actions-hot-key-contention.md)
- 실제로 lost update outcome을 검증하려면 [JCStress Concurrency Testing](./jcstress-concurrency-testing.md)

## 한 줄 정리

`volatile` counter가 깨지는 원인은 visibility 부족이 아니라 `count++`의 read-modify-write 원자성 부족이며, 단일 counter는 `AtomicInteger`, 복합 불변식은 lock, 고경합 metrics는 `LongAdder`, 검증은 `JCStress`로 분기하는 편이 안전하다.
