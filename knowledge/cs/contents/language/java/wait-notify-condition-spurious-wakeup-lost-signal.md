---
schema_version: 3
title: wait/notify, Condition, Spurious Wakeup, and Lost Signal
concept_id: language/wait-notify-condition-spurious-wakeup-lost-signal
canonical: true
category: language
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- guarded-block
- lost-signal-debugging
- condition-variable-protocol
aliases:
- wait notify Condition
- spurious wakeup
- lost signal
- lost notification
- guarded block
- Condition await signal
- monitor wait
- notifyAll
- producer consumer
- WAITING thread
- 조건 대기 프로토콜
- 스퓨리어스 웨이크업
symptoms:
- wait나 await에서 깨어나면 조건이 참이라고 믿고 if로 감싸서 rare race와 spurious wakeup 버그를 만든다
- 조건 변경과 notify가 같은 lock discipline 아래 있지 않아 lost signal로 worker가 영원히 기다린다
- notify와 notifyAll, Condition queue, Semaphore, CountDownLatch를 모두 이벤트 전송 API처럼 섞어 쓴다
intents:
- troubleshooting
- deep_dive
prerequisites:
- language/java-concurrency-utilities
- language/thread-interruption-cooperative-cancellation-playbook
next_docs:
- language/locksupport-park-unpark-permit-semantics
- language/semaphore-countdownlatch-cyclicbarrier-phaser-coordination-semantics
- language/thread-dump-state-interpretation
- language/java-memory-model-happens-before-volatile-final
linked_paths:
- contents/language/java/thread-interruption-cooperative-cancellation-playbook.md
- contents/language/java/thread-dump-state-interpretation.md
- contents/language/java-memory-model-happens-before-volatile-final.md
- contents/language/java/locksupport-park-unpark-permit-semantics.md
- contents/language/java/semaphore-countdownlatch-cyclicbarrier-phaser-coordination-semantics.md
- contents/language/java/executor-sizing-queue-rejection-policy.md
- contents/language/java/java-concurrency-utilities.md
confusable_with:
- language/locksupport-park-unpark-permit-semantics
- language/semaphore-countdownlatch-cyclicbarrier-phaser-coordination-semantics
- language/thread-dump-state-interpretation
forbidden_neighbors: []
expected_queries:
- wait notify에서 왜 if가 아니라 while로 predicate를 다시 확인해야 하는지 spurious wakeup 기준으로 설명해줘
- lost signal은 조건 상태 변경과 notify가 같은 lock 아래 있지 않을 때 어떻게 생겨?
- notify와 notifyAll은 언제 각각 위험하고 Condition을 쓰면 무엇이 더 명시적으로 나뉘어?
- thread dump에 WAITING on object monitor가 쌓일 때 wait notify protocol에서 무엇을 확인해야 해?
- producer consumer 문제에서 raw wait notify보다 BlockingQueue나 Semaphore를 쓰는 게 나은 경우를 비교해줘
contextual_chunk_prefix: |
  이 문서는 wait/notify와 Condition을 이벤트 전송이 아니라 condition predicate protocol로 다루는 playbook이다.
  guarded block, while predicate loop, spurious wakeup, lost signal, notify vs notifyAll, Condition.await/signal, WAITING thread dump, LockSupport, Semaphore, CountDownLatch와의 경계를 다룬다.
---
# `wait`/`notify`, `Condition`, Spurious Wakeup, and Lost Signal

> 한 줄 요약: `wait()`/`notify()`와 `Condition.await()`/`signal()`은 이벤트 전송 API가 아니라 조건 대기 프로토콜이다. 조건(predicate), 락, 신호 순서를 잘못 잡으면 spurious wakeup, lost signal, 영원한 `WAITING`이 생긴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Thread Interruption and Cooperative Cancellation Playbook](./thread-interruption-cooperative-cancellation-playbook.md)
> - [Thread Dump State Interpretation](./thread-dump-state-interpretation.md)
> - [Java Memory Model, Happens-Before, `volatile`, `final`](../java-memory-model-happens-before-volatile-final.md)
> - [`LockSupport.park`/`unpark` Permit Semantics and Coordination Pitfalls](./locksupport-park-unpark-permit-semantics.md)
> - [`Semaphore`, `CountDownLatch`, `CyclicBarrier`, and `Phaser` Coordination Semantics](./semaphore-countdownlatch-cyclicbarrier-phaser-coordination-semantics.md)
> - [Executor Sizing, Queue, Rejection Policy](./executor-sizing-queue-rejection-policy.md)

> retrieval-anchor-keywords: wait notify, Condition await signal, spurious wakeup, lost notification, guarded block, monitor wait, notifyAll, signalAll, condition variable, happens-before, producer consumer, WAITING thread, Semaphore, CountDownLatch, LockSupport, park, unpark

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

대기는 "신호를 받으면 진행한다"가 아니라  
"공유 상태가 원하는 조건이 될 때까지 락을 잡은 채 확인하고, 아니면 잠든다"로 이해해야 한다.

즉 핵심은 signal 자체가 아니라 predicate다.

- 조건은 공유 상태에 저장된다
- 대기와 조건 확인은 같은 lock 아래서 이뤄진다
- 깨어나도 조건을 다시 확인한다

이 규칙을 놓치면 lost signal이 생긴다.

## 깊이 들어가기

### 1. `if`가 아니라 `while`로 조건을 감싼다

`wait()`와 `await()`는 깨어났다고 해서 조건이 참이 되었다는 뜻이 아니다.

- spurious wakeup이 있을 수 있다
- 다른 스레드가 먼저 조건을 소비했을 수 있다
- `notifyAll()`로 여러 스레드가 함께 깰 수 있다

그래서 표준 패턴은 guarded block이다.

```java
while (!ready) {
    lock.wait();
}
```

여기서 중요한 것은 `while`이지 `wait()` 자체가 아니다.

### 2. 조건과 신호는 같은 락 아래에서 움직여야 한다

다음 순서가 깨지면 lost signal이 난다.

- 스레드 A가 조건을 확인
- 아직 false라고 보고 잠들 준비
- 스레드 B가 조건을 true로 만들고 notify
- A는 그 notify를 놓치고 영원히 대기

이런 문제를 막으려면 조건 상태 변경과 signal이 같은 lock discipline 안에 있어야 한다.

### 3. `notify()`와 `notifyAll()`은 선택 비용이 다르다

`notify()`는 한 스레드만 깨운다.  
효율적일 수 있지만, 서로 다른 조건을 기다리는 스레드가 섞여 있으면 잘못된 스레드를 깨울 수 있다.

`notifyAll()`은 더 안전할 수 있지만, 깨어난 많은 스레드가 다시 잠들며 thundering herd를 만들 수 있다.

`Condition`을 쓰면 조건 큐를 분리할 수 있어 의도를 더 명확히 표현하기 좋다.

다만 문제 자체가 condition protocol이 아니라 bulkhead, one-shot gate, phase synchronization이라면 raw wait/notify보다 [Semaphore, CountDownLatch, CyclicBarrier, and Phaser Coordination Semantics](./semaphore-countdownlatch-cyclicbarrier-phaser-coordination-semantics.md) 쪽이 더 맞을 수 있다.

### 4. `Condition`은 더 명시적이지만 규칙은 같다

`ReentrantLock`의 `Condition`은 monitor wait/notify보다 표현력이 좋다.

- 조건 큐를 여러 개 둘 수 있다
- interruptible/timed wait를 명시할 수 있다
- lock API와 같이 읽기 쉽다

하지만 역시 predicate loop는 그대로 필요하다.  
`await()`가 자동으로 조건을 보장해주지는 않는다.

### 5. interruption과 timeout도 같이 설계해야 한다

대기 코드는 정상 경로만 있으면 안 된다.

- interrupt 시 어떻게 빠질지
- timeout 후 어떤 상태를 반환할지
- 깨어났지만 조건이 아직 false면 어떻게 재대기할지

즉 wait/notify는 동시성 API이면서 취소 API이기도 하다.

## 실전 시나리오

### 시나리오 1: producer-consumer가 가끔 멈춘다

`if (!ready) wait()` 패턴을 썼다면,  
spurious wakeup이나 경쟁 소비 때문에 빈 큐를 읽으려다 꼬일 수 있다.

### 시나리오 2: 서비스 시작 시 한 번만 notify했는데 worker가 못 깨어난다

조건과 notify 순서가 다른 lock 아래에 있으면 lost signal이 생길 수 있다.  
이건 재현이 어려워 운영에서 더 아프다.

### 시나리오 3: thread dump에 `WAITING (on object monitor)`가 쌓인다

문제는 단순히 wait를 썼다는 사실이 아니라,

- 조건을 누가 true로 만드는지
- 그 신호가 같은 monitor에서 나는지
- 깨어난 뒤 누가 다시 false로 소비하는지

를 보지 않았기 때문이다.

### 시나리오 4: `notify()`를 써서 드물게 교착 비슷한 정지가 난다

여러 종류의 대기 스레드가 같은 monitor를 기다리면,  
잘못된 스레드 하나만 깨워 전체 진행이 멈춘 것처럼 보일 수 있다.

## 코드로 보기

### 1. monitor guarded block

```java
synchronized (lock) {
    while (!ready) {
        lock.wait();
    }
    consume();
}
```

### 2. 상태 변경 후 signal

```java
synchronized (lock) {
    ready = true;
    lock.notifyAll();
}
```

### 3. `Condition` 기반 producer-consumer

```java
import java.util.ArrayDeque;
import java.util.Queue;
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.ReentrantLock;

public final class BoundedBuffer<T> {
    private final Queue<T> queue = new ArrayDeque<>();
    private final int capacity;
    private final ReentrantLock lock = new ReentrantLock();
    private final Condition notEmpty = lock.newCondition();
    private final Condition notFull = lock.newCondition();

    public BoundedBuffer(int capacity) {
        this.capacity = capacity;
    }

    public void put(T value) throws InterruptedException {
        lock.lockInterruptibly();
        try {
            while (queue.size() == capacity) {
                notFull.await();
            }
            queue.add(value);
            notEmpty.signal();
        } finally {
            lock.unlock();
        }
    }

    public T take() throws InterruptedException {
        lock.lockInterruptibly();
        try {
            while (queue.isEmpty()) {
                notEmpty.await();
            }
            T value = queue.remove();
            notFull.signal();
            return value;
        } finally {
            lock.unlock();
        }
    }
}
```

### 4. 피해야 할 `if` 패턴

```java
synchronized (lock) {
    if (!ready) {
        lock.wait();
    }
    consume();
}
```

이 코드는 깨어난 뒤에도 조건이 여전히 참인지 보장하지 못한다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| raw `wait`/`notify` | JDK 기본 도구라 의존성이 적다 | 규칙을 조금만 놓쳐도 버그가 난다 |
| `Condition` | 조건 큐를 분리해 의도를 더 잘 표현한다 | lock 관리 코드가 늘어난다 |
| `BlockingQueue` 같은 고수준 유틸리티 | 구현 실수를 크게 줄인다 | 세밀한 프로토콜을 직접 통제하기 어렵다 |
| `notifyAll()` 우선 | 안전성이 높다 | 깨어나는 스레드가 많아져 비용이 늘 수 있다 |

핵심은 signal API보다 predicate와 lock discipline을 먼저 설계하는 것이다.

## 꼬리질문

> Q: 왜 `if` 대신 `while`을 써야 하나요?
> 핵심: spurious wakeup과 경쟁 소비 때문에 깨어난 뒤에도 조건을 다시 확인해야 하기 때문이다.

> Q: lost signal은 왜 생기나요?
> 핵심: 조건 상태 변경과 대기/신호가 같은 락 규칙 아래에서 움직이지 않으면 신호를 놓칠 수 있다.

> Q: `notify()`보다 `notifyAll()`이 항상 좋은가요?
> 핵심: 안전성은 높지만 비용이 커질 수 있어 조건 큐 구조를 함께 봐야 한다.

> Q: raw wait/notify를 직접 구현해야 하나요?
> 핵심: 대부분은 `BlockingQueue`, `Semaphore`, `CountDownLatch` 같은 고수준 유틸리티가 더 안전하다.

## 한 줄 정리

`wait`/`notify`와 `Condition`은 신호 전달이 아니라 조건 대기 프로토콜이므로, predicate loop와 같은-lock discipline 없이 쓰면 lost signal과 영구 대기가 생기기 쉽다.
