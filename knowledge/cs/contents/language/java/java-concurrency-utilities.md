# Java 동시성 유틸리티

**난이도: 🔴 Advanced**

> 신입 백엔드 개발자가 스레드와 비동기 처리 코드를 읽기 위해 필요한 실전 정리

> 관련 문서:
> - [Language README](../README.md)
> - [JVM, GC, JMM](./jvm-gc-jmm-overview.md)
> - [Thread Interruption and Cooperative Cancellation Playbook](./thread-interruption-cooperative-cancellation-playbook.md)
> - [CompletableFuture Execution Model and Common Pool Pitfalls](./completablefuture-execution-model-common-pool-pitfalls.md)
> - [CompletableFuture Cancellation Semantics](./completablefuture-cancellation-semantics.md)
> - [`InheritableThreadLocal` vs `ScopedValue` Context Propagation Boundaries](./inheritablethreadlocal-vs-scopedvalue-context-propagation.md)
> - [`ConcurrentHashMap` Compound Actions and Hot-Key Contention](./concurrenthashmap-compound-actions-hot-key-contention.md)
> - [`ConcurrentSkipListMap`, `ConcurrentLinkedQueue`, and `CopyOnWriteArraySet` Trade-offs](./concurrentskiplistmap-concurrentlinkedqueue-copyonwritearrayset-tradeoffs.md)
> - [`BlockingQueue`, `TransferQueue`, and `ConcurrentSkipListSet` Semantics](./blockingqueue-transferqueue-concurrentskiplistset-semantics.md)
> - [`Semaphore`, `CountDownLatch`, `CyclicBarrier`, and `Phaser` Coordination Semantics](./semaphore-countdownlatch-cyclicbarrier-phaser-coordination-semantics.md)
> - [`wait`/`notify`, `Condition`, Spurious Wakeup, and Lost Signal](./wait-notify-condition-spurious-wakeup-lost-signal.md)
> - [`StampedLock` Optimistic Read and Conversion Pitfalls](./stampedlock-optimistic-read-conversion-pitfalls.md)
> - [Executor Sizing, Queue, Rejection Policy](./executor-sizing-queue-rejection-policy.md)
> - [Virtual Threads(Project Loom)](./virtual-threads-project-loom.md)
> - [Virtual Thread Migration: Pinning, `ThreadLocal`, and Pool Boundary Strategy](./virtual-thread-migration-pinning-threadlocal-pool-boundaries.md)

> retrieval-anchor-keywords: Java concurrency utilities, ExecutorService, thread pool, Callable, Future, CompletableFuture, ConcurrentHashMap, ConcurrentSkipListMap, ConcurrentLinkedQueue, CopyOnWriteArraySet, BlockingQueue, TransferQueue, ConcurrentSkipListSet, interrupt, cancellation, wait notify, Condition, Semaphore, CountDownLatch, CyclicBarrier, Phaser, StampedLock, worker shutdown, shared state, async composition

<details>
<summary>Table of Contents</summary>

- [왜 중요한가](#왜-중요한가)
- [Thread를 직접 만들기보다 Executor를 쓰는 이유](#thread를-직접-만들기보다-executor를-쓰는-이유)
- [Executor와 ExecutorService](#executor와-executorservice)
- [Thread Pool](#thread-pool)
- [Callable과 Future](#callable과-future)
- [CompletableFuture](#completablefuture)
- [ConcurrentHashMap](#concurrenthashmap)
- [추천 공식 자료](#추천-공식-자료)
- [면접에서 자주 나오는 질문](#면접에서-자주-나오는-질문)

</details>

## 왜 중요한가

백엔드에서는

- 여러 요청을 동시에 처리하고
- 비동기 작업을 분리하고
- 공유 자원을 안전하게 다뤄야 한다.

그래서 자바에서 많이 쓰는 동시성 유틸리티를 알아야 한다.

---

## Thread를 직접 만들기보다 Executor를 쓰는 이유

`new Thread(...)`를 직접 쓰면

- 생성/관리 책임이 흩어지고
- 스레드 수 제어가 어려워지고
- 재사용이 안 된다

그래서 보통은 스레드 생성보다 **작업(task) 제출**에 집중하고,
실제 스레드 관리는 `Executor`가 하게 한다.

---

## Executor와 ExecutorService

### `Executor`

- 작업을 실행하는 최소 인터페이스

```java
executor.execute(runnable);
```

### `ExecutorService`

- `Executor`를 확장한 인터페이스
- 종료, 제출, 결과 받기까지 포함

예:

```java
executorService.submit(callable);
executorService.shutdown();
```

---

## Thread Pool

스레드 풀은 **미리 만들어둔 스레드를 재사용하는 방식**이다.

장점:

- 스레드 생성 비용 감소
- 스레드 수 제어 가능
- 서버 자원 고갈 방지

대표:

- `Executors.newFixedThreadPool(...)`
- `Executors.newCachedThreadPool(...)`
- `Executors.newSingleThreadExecutor()`

---

## Callable과 Future

### `Runnable`

- 반환값 없음

### `Callable`

- 반환값 있음
- 예외를 던질 수 있음

### `Future`

- 비동기 작업의 결과를 나중에 받을 수 있게 해줌

즉

- `Callable` = 값을 돌려주는 작업
- `Future` = 그 결과를 나중에 받는 핸들

---

## CompletableFuture

`CompletableFuture`는 **비동기 작업을 조합하기 쉽게 만든 도구**다.

예:

- 작업 A 실행
- 끝나면 작업 B 실행
- 둘 다 끝나면 결과 합치기

같은 흐름을 체이닝하기 좋다.

즉 `Future`보다 **조합성과 표현력**이 더 좋다.

실전에서는 실행 모델과 취소 semantics까지 같이 봐야 한다.  
관련해서 [CompletableFuture Execution Model and Common Pool Pitfalls](./completablefuture-execution-model-common-pool-pitfalls.md)와 [CompletableFuture Cancellation Semantics](./completablefuture-cancellation-semantics.md), [Thread Interruption and Cooperative Cancellation Playbook](./thread-interruption-cooperative-cancellation-playbook.md)을 함께 보면 좋다.

---

## ConcurrentHashMap

일반 `HashMap`은 멀티스레드 환경에서 안전하지 않다.

`ConcurrentHashMap`은

- 동시 접근을 고려해 설계된 Map
- 읽기/쓰기 경쟁 상황에서 더 안전

즉 공유 자료구조가 필요할 때 기본 후보로 많이 본다.

다만 "개별 연산이 안전하다"와 "복합 동작이 안전하다"는 다른 문제다.  
실무 함정은 [ConcurrentHashMap Compound Actions and Hot-Key Contention](./concurrenthashmap-compound-actions-hot-key-contention.md)에서 더 자세히 다룬다.

---

## 추천 공식 자료

- Oracle Executors tutorial:
  - https://docs.oracle.com/javase/tutorial/essential/concurrency/executors.html
- Java `Executors` API:
  - https://docs.oracle.com/en/java/javase/24/docs/api/java.base/java/util/concurrent/Executors.html
- Java `CompletableFuture` API:
  - https://docs.oracle.com/en/java/javase/24/docs/api/java.base/java/util/concurrent/CompletableFuture.html

---

## 면접에서 자주 나오는 질문

### Q. `new Thread()`보다 `ExecutorService`를 쓰는 이유는 무엇인가요?

- 스레드 생성/관리 책임을 분리하고, 재사용과 개수 제어를 쉽게 하기 위해서다.

### Q. `Runnable`과 `Callable` 차이는 무엇인가요?

- `Runnable`은 반환값이 없고, `Callable`은 반환값이 있으며 예외를 던질 수 있다.

### Q. `Future`와 `CompletableFuture` 차이는 무엇인가요?

- `Future`는 결과를 나중에 받는 데 초점이 있고,
- `CompletableFuture`는 비동기 작업 조합과 후속 처리에 더 강하다.

### Q. `HashMap` 대신 `ConcurrentHashMap`을 쓰는 이유는 무엇인가요?

- 여러 스레드가 동시에 접근하는 상황에서 더 안전하게 동작하기 때문이다.
