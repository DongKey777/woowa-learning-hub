---
schema_version: 3
title: LockSupport park unpark Permit Semantics and Coordination Pitfalls
concept_id: language/locksupport-park-unpark-permit-semantics
canonical: true
category: language
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 86
mission_ids:
- missions/racingcar
- missions/payment
review_feedback_tags:
- locksupport
- coordination
- thread-dump
aliases:
- LockSupport park unpark permit semantics
- thread per permit park unpark Java
- LockSupport permit consumption
- park unpark spurious return interrupt
- low-level coordination primitive
- 자바 LockSupport park unpark permit
symptoms:
- LockSupport를 sleep이나 wait/notify 대체재로만 이해해 thread당 최대 1개의 permit 모델을 설명하지 못해
- unpark가 park보다 먼저 오면 signal이 사라진다고 생각하거나 여러 번 unpark하면 permit가 누적된다고 오해해
- park를 predicate loop 없이 사용해 spurious return, interrupt, 기존 permit 소비 때문에 예상보다 바로 깨어나는 문제를 만든다
intents:
- deep_dive
- troubleshooting
- design
prerequisites:
- language/wait-notify-condition-spurious-wakeup-lost-signal
- language/thread-dump-state-interpretation
- language/semaphore-countdownlatch-cyclicbarrier-phaser-coordination-semantics
next_docs:
- language/thread-interruption-cooperative-cancellation-playbook
- language/jfr-loom-incident-signal-map
- language/java-concurrency-utilities
linked_paths:
- contents/language/java/wait-notify-condition-spurious-wakeup-lost-signal.md
- contents/language/java/thread-dump-state-interpretation.md
- contents/language/java/semaphore-countdownlatch-cyclicbarrier-phaser-coordination-semantics.md
- contents/language/java/thread-interruption-cooperative-cancellation-playbook.md
- contents/language/java/jfr-loom-incident-signal-map.md
- contents/language/java/java-concurrency-utilities.md
confusable_with:
- language/wait-notify-condition-spurious-wakeup-lost-signal
- language/semaphore-countdownlatch-cyclicbarrier-phaser-coordination-semantics
- language/thread-interruption-cooperative-cancellation-playbook
forbidden_neighbors: []
expected_queries:
- LockSupport park unpark는 thread당 1개의 permit라는 모델을 어떻게 이해해야 해?
- unpark가 park보다 먼저 호출되면 이후 park가 왜 바로 반환될 수 있어?
- unpark를 여러 번 해도 permit가 누적되지 않는 이유와 Semaphore와 차이를 설명해줘
- LockSupport.park를 predicate while loop와 blocker object와 함께 써야 하는 이유가 뭐야?
- thread dump에서 parking to wait for가 보일 때 blocker와 predicate를 어떻게 확인해?
contextual_chunk_prefix: |
  이 문서는 LockSupport.park/unpark를 thread당 1-bit permit semantics, spurious return, interrupt, blocker object 관점에서 설명하는 advanced deep dive다.
  LockSupport, park unpark, permit semantics, spurious return, thread parking 질문이 본 문서에 매핑된다.
---
# `LockSupport.park`/`unpark` Permit Semantics and Coordination Pitfalls

> 한 줄 요약: `LockSupport`는 low-level wait/notify 대체재처럼 보이지만, 실제 모델은 thread당 최대 1개의 permit이다. 이 permit semantics를 이해하지 못하면 lost wakeup이 아니라 "이미 있던 permit을 소비해 예상보다 바로 깨어나는" 종류의 버그가 생긴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [`wait`/`notify`, `Condition`, Spurious Wakeup, and Lost Signal](./wait-notify-condition-spurious-wakeup-lost-signal.md)
> - [Thread Dump State Interpretation](./thread-dump-state-interpretation.md)
> - [`Semaphore`, `CountDownLatch`, `CyclicBarrier`, and `Phaser` Coordination Semantics](./semaphore-countdownlatch-cyclicbarrier-phaser-coordination-semantics.md)
> - [Thread Interruption and Cooperative Cancellation Playbook](./thread-interruption-cooperative-cancellation-playbook.md)

> retrieval-anchor-keywords: LockSupport, park, unpark, permit semantics, parked thread, spurious return, blocker object, low-level coordination, thread parking, permit consumption, interruptible wait, backend hang

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

`LockSupport`의 핵심 모델은 permit이다.

- 각 thread는 최대 1개의 permit를 가진다
- `unpark(thread)`는 permit를 준다
- `park()`는 permit가 있으면 즉시 소비하고 반환한다
- permit가 없으면 block될 수 있다

즉 이 모델은 queue가 아니라 one-bit signal에 가깝다.

## 깊이 들어가기

### 1. `unpark`가 먼저 와도 신호가 사라지지 않을 수 있다

`wait`/`notify`와 달리 `unpark`는 `park`보다 먼저 호출되어도 permit가 남아 있을 수 있다.  
그래서 이후 `park()`는 바로 돌아올 수 있다.

이 점은 lost wakeup을 줄여주기도 하지만,  
반대로 "왜 안 멈추지?" 같은 오해도 만든다.

### 2. permit는 누적되지 않는다

thread당 permit는 최대 1개다.  
`unpark()`를 여러 번 호출해도 permit가 여러 장 쌓이지 않는다.

즉 `LockSupport`는 counting semaphore가 아니다.

### 3. `park()`는 signal만으로 안전하지 않다

`park()`도 predicate loop와 함께 써야 한다.

- spuriously return할 수 있다
- interrupt로 돌아올 수 있다
- 이미 permit가 남아 있어 즉시 반환할 수 있다

즉 `park()`를 "조건 없이 멈추는 명령"으로 쓰면 안 된다.

### 4. blocker object는 진단에 중요하다

`LockSupport.park(blocker)` 형태는 thread dump와 tooling에서  
"무엇 때문에 park 중인가"를 더 읽기 쉽게 해준다.

custom coordination primitive를 만들 때는 blocker 정보가 운영 디버깅에 도움이 된다.

### 5. custom primitive를 만들기 전 고수준 유틸리티를 먼저 본다

`LockSupport`는 AQS 기반 유틸리티의 토대다.  
서비스 코드에서 직접 쓸 때는 reasoning 비용이 높다.

문제가 정말 low-level permit coordination인지, 아니면

- one-shot gate
- bounded handoff
- producer-consumer
- bulkhead

같은 higher-level 문제인지 먼저 봐야 한다.

## 실전 시나리오

### 시나리오 1: worker가 예상보다 바로 깨어난다

이전 라운드에서 남은 permit가 있었다.  
새 `park()`는 block되지 않고 즉시 반환한다.

### 시나리오 2: `unpark()`를 여러 번 했는데 한 번만 효과가 있다

permit가 누적되지 않기 때문이다.  
counting semantics를 원했다면 `Semaphore` 같은 도구가 더 맞다.

### 시나리오 3: thread dump에 `parking to wait for`가 보인다

이때 중요한 것은 park 자체보다 blocker object와 predicate 상태다.  
왜 park 중인지 모르면 stuck thread 원인을 좁히기 어렵다.

### 시나리오 4: interrupt와 park가 섞여 동작이 헷갈린다

`park()`는 interrupt로도 반환할 수 있다.  
그래서 취소와 coordination signal을 구분해서 읽어야 한다.

## 코드로 보기

### 1. predicate loop와 함께 쓰기

```java
while (!ready) {
    java.util.concurrent.locks.LockSupport.park(this);
}
```

### 2. 다른 thread가 permit를 준다

```java
ready = true;
java.util.concurrent.locks.LockSupport.unpark(workerThread);
```

### 3. counting primitive가 아님

```java
LockSupport.unpark(thread);
LockSupport.unpark(thread);
// permit 두 개가 쌓이지는 않는다.
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| `LockSupport` | low-level permit coordination을 직접 표현할 수 있다 | predicate, interrupt, permit semantics를 직접 reasoning해야 한다 |
| `Condition`/monitor wait | 더 익숙한 조건 대기 모델이다 | lock discipline을 잘못 잡으면 lost signal이 생기기 쉽다 |
| `Semaphore`/latch/barrier | 의도가 더 높고 읽기 쉽다 | low-level custom primitive 구성엔 덜 직접적이다 |

핵심은 `park`/`unpark`를 sleep 대체재가 아니라 "thread당 1비트 permit 프로토콜"로 읽는 것이다.

## 꼬리질문

> Q: `unpark()`가 `park()`보다 먼저 와도 괜찮나요?
> 핵심: 가능하다. permit가 남아 있으면 이후 `park()`는 즉시 반환할 수 있다.

> Q: `unpark()`를 두 번 하면 permit 두 개가 쌓이나요?
> 핵심: 아니다. thread당 permit는 최대 1개다.

> Q: `park()`는 왜 while loop가 필요한가요?
> 핵심: spuriously return, interrupt, 기존 permit 소비 때문에 조건을 다시 확인해야 하기 때문이다.

> Q: 언제 직접 `LockSupport`를 써야 하나요?
> 핵심: 정말 low-level custom coordination이 필요할 때만 신중히 쓰고, 대부분은 더 높은 수준 유틸리티가 낫다.

## 한 줄 정리

`LockSupport`의 본질은 permit 1개짜리 저수준 coordination이므로, counting이나 강한 condition wait로 오해하면 subtle한 wakeup bug가 생기기 쉽다.
