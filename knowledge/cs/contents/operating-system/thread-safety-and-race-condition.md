---
schema_version: 3
title: Thread Safety and Race Condition Primer
concept_id: operating-system/thread-safety-and-race-condition
canonical: true
category: operating-system
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 84
mission_ids:
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- thread-safety
- race-condition
- shared-state
- concurrency
aliases:
- thread safety
- race condition
- data race
- shared mutable state
- 스레드 안전
- 경쟁 상태
- 공유 상태 동시성
symptoms:
- 여러 스레드가 같은 값을 수정할 때 결과가 가끔 틀어진다
- 테스트를 반복 실행하면 한 번씩만 실패하는 동시성 문제가 보인다
- synchronized, lock, Atomic 중 무엇으로 막아야 하는지 모르겠다
intents:
- definition
- troubleshooting
- comparison
prerequisites:
- operating-system/process-thread-basics
- operating-system/sync-async-blocking-nonblocking-basics
next_docs:
- operating-system/mutex-deadlock-basics
- operating-system/futex-mutex-semaphore-spinlock
- operating-system/atomic-vs-lock
linked_paths:
- contents/operating-system/process-thread-basics.md
- contents/operating-system/sync-async-blocking-nonblocking-basics.md
- contents/operating-system/mutex-deadlock-basics.md
- contents/operating-system/futex-mutex-semaphore-spinlock.md
- contents/operating-system/context-switching-deadlock-lockfree.md
- contents/operating-system/lock-contention-futex-offcpu-debugging.md
confusable_with:
- operating-system/process-thread-basics
- operating-system/mutex-deadlock-basics
- operating-system/futex-mutex-semaphore-spinlock
forbidden_neighbors: []
expected_queries:
- race condition이 뭐고 thread safety와 어떻게 연결돼?
- 공유 mutable state를 여러 스레드가 만질 때 왜 결과가 가끔 틀어져?
- synchronized나 lock 없이 counter를 올리면 왜 손실 업데이트가 생겨?
- thread safe하게 만들려면 상태를 없애는 것과 lock을 거는 것 중 무엇을 먼저 봐야 해?
- 동시성 테스트가 가끔만 실패할 때 race condition을 어떻게 의심해?
contextual_chunk_prefix: |
  이 문서는 thread safety와 race condition을 처음 연결하는 operating-system
  primer다. 여러 스레드가 같은 mutable state를 수정할 때 결과가 가끔
  틀어지는 증상, lost update, synchronized, lock, atomic, shared state
  같은 자연어 질문을 race condition의 읽기/쓰기 interleaving 문제로
  매핑하고 다음 lock/atomic 문서로 이어 준다.
---
# Thread Safety and Race Condition Primer

> 한 줄 요약: race condition은 "여러 실행 흐름의 순서가 결과를 바꾸는 상태"이고, thread safety는 그 순서가 달라도 의미 있는 결과가 유지되게 만드는 성질이다.

**난이도: Beginner**

## 먼저 나누기

| 질문 | 먼저 보는 것 |
|---|---|
| 여러 thread가 같은 값을 읽고 쓴다 | shared mutable state가 있는가 |
| 가끔만 실패한다 | 실행 순서에 따라 결과가 달라지는가 |
| counter가 덜 올라간다 | read-modify-write가 쪼개져 있는가 |
| lock을 걸어도 느리다 | critical section이 너무 넓은가 |

`count++`도 한 동작처럼 보이지만 보통은 읽기, 더하기, 쓰기로 나뉜다.
두 thread가 동시에 같은 이전 값을 읽으면 한 번의 증가가 사라질 수 있다.

## thread safe하게 만드는 순서

1. 공유 상태를 없앨 수 있는지 본다.
2. 상태를 객체 안으로 가두고 외부 변경 경로를 줄인다.
3. 꼭 공유해야 하면 lock, atomic, actor/queue 같은 직렬화 경계를 고른다.
4. 성능 문제가 생기면 lock 범위와 경합 지점을 따로 본다.

초심자에게 가장 안전한 기준은 "lock부터 붙이기"가 아니라 "무엇이 공유되고 무엇이 변경되는가"를 먼저 적는 것이다.

## 흔한 오해

| 오해 | 교정 |
|---|---|
| thread가 여러 개면 항상 race condition이다 | 공유 변경 상태가 없으면 문제가 아닐 수 있다 |
| 테스트가 대부분 통과하면 안전하다 | race는 timing 문제라 반복 실행에서만 드러날 수 있다 |
| atomic이면 모든 불변식이 자동으로 안전하다 | 단일 값 연산과 여러 필드 불변식은 다르다 |
| lock을 크게 잡으면 항상 좋다 | 안전해질 수는 있지만 경합과 deadlock 위험이 커진다 |

## 다음 문서

- lock의 기본 형태는 [뮤텍스와 교착상태 기초](./mutex-deadlock-basics.md)로 본다.
- atomic과 lock 선택은 [Atomic vs Lock](./atomic-vs-lock.md)로 이어진다.
- futex, semaphore, spinlock 차이는 [Futex Mutex Semaphore Spinlock](./futex-mutex-semaphore-spinlock.md)에서 비교한다.

