---
schema_version: 3
title: Atomic vs Lock
concept_id: operating-system/atomic-vs-lock
canonical: true
category: operating-system
difficulty: intermediate
doc_role: chooser
level: intermediate
language: mixed
source_priority: 82
mission_ids:
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- atomic-vs-lock
- concurrency-control
- invariant-boundary
- compare-and-set
aliases:
- atomic vs lock
- CAS vs mutex
- lock free vs lock
- 원자 연산과 락
- AtomicInteger vs synchronized
- compare and set
symptoms:
- AtomicInteger를 쓰면 여러 필드 불변식도 안전한지 헷갈린다
- synchronized와 CAS 중 무엇을 써야 하는지 모르겠다
- lock-free라는 말이 항상 빠르다는 뜻으로 들린다
intents:
- comparison
- design
- troubleshooting
prerequisites:
- operating-system/thread-safety-and-race-condition
- operating-system/process-thread-basics
next_docs:
- operating-system/futex-mutex-semaphore-spinlock
- operating-system/context-switching-deadlock-lockfree
- operating-system/lock-contention-futex-offcpu-debugging
linked_paths:
- contents/operating-system/thread-safety-and-race-condition.md
- contents/operating-system/futex-mutex-semaphore-spinlock.md
- contents/operating-system/context-switching-deadlock-lockfree.md
- contents/operating-system/lock-contention-futex-offcpu-debugging.md
- contents/language/java/volatile-counter-atomicity-cause-router.md
- contents/database/lock-basics.md
confusable_with:
- operating-system/thread-safety-and-race-condition
- operating-system/futex-mutex-semaphore-spinlock
- operating-system/context-switching-deadlock-lockfree
forbidden_neighbors: []
expected_queries:
- AtomicInteger와 synchronized는 언제 각각 써?
- atomic 연산이면 lock이 전혀 필요 없는 거야?
- CAS와 mutex의 차이를 불변식 기준으로 설명해줘
- 여러 필드를 같이 바꿔야 하면 atomic 변수만으로 충분해?
- lock-free가 항상 더 빠른지 알려줘
contextual_chunk_prefix: |
  이 문서는 atomic operation과 lock을 invariant boundary 기준으로 고르는
  operating-system chooser다. AtomicInteger, synchronized, CAS, mutex,
  lock-free, 여러 필드 불변식, counter lost update 같은 질문을 단일 값
  원자성인지 복합 상태 보호인지로 나눠 다음 lock 문서로 연결한다.
---
# Atomic vs Lock

> 한 줄 요약: atomic은 작은 단일 연산을 안전하게 바꾸는 도구이고, lock은 여러 읽기/쓰기와 불변식을 하나의 임계구역으로 묶는 도구다.

**난이도: Intermediate**

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "재고 수량만 `AtomicInteger`로 바꾸면 장바구니 동시성은 끝난 건가요?" | shopping-cart에서 stock, reserved, updatedAt 같은 값을 함께 맞춰야 하는 코드 | 단일 값 원자성과 여러 필드 불변식 보호를 분리한다 |
| "예약 가능 여부 확인 후 저장을 CAS로 처리하면 lock 없이 안전할까요?" | roomescape에서 check 후 insert/update가 여러 단계로 나뉘는 흐름 | CAS가 맞는 작은 상태인지, 더 큰 직렬화 경계가 필요한지 확인한다 |
| "lock-free가 항상 더 빠르다는데 synchronized를 쓰면 안 되나요?" | 경합이 있는 counter나 상태 전이를 성능 이름만으로 고르는 설계 | retry 경합 비용과 임계구역 불변식 표현력을 같이 본다 |

## 선택 기준

| 상황 | 먼저 고려 |
|---|---|
| 단일 counter 증가 | atomic |
| 하나의 reference 교체 | atomic/CAS |
| 두 필드를 함께 맞춰야 함 | lock |
| check 후 update가 여러 단계 | lock 또는 더 큰 직렬화 경계 |
| 경합이 심하고 지연이 중요 | lock 범위, sharding, queue, lock-free 구조 검토 |

`AtomicInteger.incrementAndGet()`은 counter 하나에는 잘 맞는다.
하지만 `balance`와 `lastUpdatedAt`을 함께 바꾸거나, `stock > 0` 확인 뒤 차감하는 불변식은 단일 atomic 변수만으로는 부족할 수 있다.

## CAS의 장점과 한계

CAS는 "내가 본 값이 아직 그대로면 새 값으로 바꾼다"는 원자적 비교-교체다.
작은 상태에는 빠르고 blocking을 피할 수 있지만, 실패하면 retry loop가 필요하고 여러 값을 함께 지키기는 어렵다.

| 도구 | 강점 | 조심할 점 |
|---|---|---|
| atomic/CAS | 작은 상태, 짧은 갱신, blocking 회피 | retry 경합, ABA, 복합 불변식 |
| lock/mutex | 여러 연산을 한 경계로 묶음 | deadlock, convoy, 넓은 critical section |

## 흔한 오해

- atomic을 쓰면 class 전체가 thread-safe해지는 것은 아니다.
- lock-free가 항상 빠른 것은 아니다. 경합이 심하면 CAS retry가 비용이 된다.
- lock은 나쁜 것이 아니라 불변식 경계를 표현하는 가장 단순한 도구일 수 있다.
- volatile은 visibility에 가깝고 복합 연산의 atomicity를 대신하지 않는다.

## 다음 문서

- race condition 감각은 [Thread Safety and Race Condition](./thread-safety-and-race-condition.md)에서 먼저 잡는다.
- mutex/semaphore/spinlock 비교는 [Futex Mutex Semaphore Spinlock](./futex-mutex-semaphore-spinlock.md)으로 이어진다.
- Java counter 증상은 [volatile counter atomicity cause router](../language/java/volatile-counter-atomicity-cause-router.md)에서 사례로 본다.
