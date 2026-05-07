---
schema_version: 3
title: Java Timer vs ScheduledExecutorService vs DelayQueue Router
concept_id: data-structure/java-timer-vs-scheduledexecutorservice-vs-delayqueue-router
canonical: false
category: data-structure
difficulty: beginner
doc_role: symptom_router
level: beginner
language: mixed
source_priority: 80
mission_ids: []
review_feedback_tags:
- scheduler-default-vs-queue-material
- timer-legacy-default-misread
- delayqueue-direct-use-overreach
aliases:
- java timer vs scheduledexecutorservice vs delayqueue
- 자바에서 몇 초 뒤 실행 뭐 써요
- timer vs scheduledexecutorservice 차이
- scheduledexecutorservice 기본값
- delayqueue는 언제 직접 써요
- java scheduler 큰 그림
- delayed task beginner java
- timertask 레거시 뭐예요
- 직접 scheduler 구현 vs executor
- why not timer for new code
- 처음 배우는 자바 스케줄러 선택
symptoms:
- 몇 초 뒤 실행만 하면 되는데 DelayQueue까지 직접 구현해야 할 것 같아 헷갈린다
- 새 코드 기본값을 골라야 하는데 Timer 예제가 먼저 보여서 선택이 흔들린다
- scheduleAtFixedRate 같은 API를 봤는데 executor와 queue를 같은 층위로 이해하고 있다
- 지연 실행 도구와 스케줄러 재료를 한 번에 배우려다 기준이 안 선다
intents:
- symptom
- troubleshooting
- comparison
prerequisites:
- data-structure/queue-vs-deque-vs-priority-queue-primer
next_docs:
- data-structure/scheduledexecutorservice-vs-delayqueue-bridge
- data-structure/fixed-rate-vs-fixed-delay-overrun-primer
- data-structure/delayqueue-delayed-contract-primer
linked_paths:
- contents/data-structure/scheduledexecutorservice-vs-delayqueue-bridge.md
- contents/data-structure/fixed-rate-vs-fixed-delay-overrun-primer.md
- contents/data-structure/timer-priority-policy-split.md
- contents/data-structure/java-timer-clock-choice-primer.md
- contents/data-structure/delayqueue-delayed-contract-primer.md
- contents/data-structure/priorityblockingqueue-timer-misuse-primer.md
- contents/data-structure/delayqueue-repeating-task-primer.md
- contents/data-structure/scheduledfuture-cancel-stale-entries.md
- contents/data-structure/timer-cancellation-reschedule-stale-entry-primer.md
- contents/data-structure/timing-wheel-vs-delay-queue.md
confusable_with:
- data-structure/scheduledexecutorservice-vs-delayqueue-bridge
- data-structure/delayqueue-delayed-contract-primer
- data-structure/priorityblockingqueue-timer-misuse-primer
forbidden_neighbors: []
expected_queries:
- 자바에서 몇 초 뒤 작업 실행할 때 Timer, ScheduledExecutorService, DelayQueue를 어디서부터 갈라야 해?
- 새 코드 기본값으로 ScheduledExecutorService를 먼저 보는 이유를 증상 기준으로 설명해줘
- DelayQueue를 직접 써야 하는 문제와 그냥 scheduler API를 쓰면 되는 문제를 빠르게 분기하고 싶어
- Timer 예제를 봤는데 레거시 읽기와 새 설계 기본값을 어떻게 분리해야 해?
- scheduleAtFixedRate가 보일 때 executor 선택 문제인지 queue 구현 문제인지 먼저 잘라줘
- 지연 실행, 주기 실행, 직접 scheduler 구현을 한 장에서 라우팅해줘
- Java delayed task를 처음 배울 때 왜 Timer보다 ScheduledExecutorService가 기본인지 궁금해
- DelayQueue를 쓰는 순간 애플리케이션 API가 아니라 구현 재료로 내려간다는 말을 이해하고 싶어
contextual_chunk_prefix: |
  이 문서는 Java 지연 실행과 주기 실행을 처음 배우는 학습자가 Timer,
  ScheduledExecutorService, DelayQueue를 증상에서 요구사항으로 먼저
  라우팅하게 돕는 symptom_router다. 몇 초 뒤 실행, 주기 실행, 레거시
  Timer, scheduler 기본값, DelayQueue 직접 구현, queue와 executor 층위
  혼동 같은 자연어 paraphrase가 본 문서의 분기 기준에 매핑된다.
---
# Java Timer vs ScheduledExecutorService vs DelayQueue Router

> 한 줄 요약: 초보자 기준 기본값은 거의 항상 `ScheduledExecutorService`이고, `Timer`는 레거시 호환 맥락에서만, `DelayQueue`는 직접 scheduler 규칙을 만들 때만 고른다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../algorithm/backend-algorithm-starter-pack.md)


retrieval-anchor-keywords: java timer vs scheduledexecutorservice vs delayqueue, 자바 스케줄러 처음 배우는데, 자바에서 몇 초 뒤 실행 뭐 써요, timer vs scheduledexecutorservice 차이, scheduledexecutorservice 기본값, delayqueue는 언제 직접 써요, java scheduler 큰 그림, delayed task beginner java, scheduleatfixedrate 어디서 써요, timertask 레거시 뭐예요, 직접 scheduler 구현 vs executor, what is scheduledexecutorservice, what is delayqueue in java, why not timer for new code, 처음 배우는 자바 스케줄러 선택
> 관련 문서:
> - [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)
> - [Fixed Rate vs Fixed Delay Overrun Primer](./fixed-rate-vs-fixed-delay-overrun-primer.md)
> - [Timer Priority Policy Split](./timer-priority-policy-split.md)
> - [Java Timer Clock Choice Primer](./java-timer-clock-choice-primer.md)
> - [DelayQueue Delayed Contract Primer](./delayqueue-delayed-contract-primer.md)
> - [PriorityBlockingQueue Timer Misuse Primer](./priorityblockingqueue-timer-misuse-primer.md)
> - [DelayQueue Repeating Task Primer](./delayqueue-repeating-task-primer.md)
> - [ScheduledFuture Cancellation Bridge](./scheduledfuture-cancel-stale-entries.md)
> - [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md)
> - [Timing Wheel vs Delay Queue](./timing-wheel-vs-delay-queue.md)
>
> retrieval-anchor-keywords: java timer vs scheduledexecutorservice, java timer vs scheduled executor service, timer vs scheduledexecutorservice vs delayqueue, java scheduler router, java timer router, scheduled executor router, delayqueue router, legacy timer vs scheduledthreadpoolexecutor, timer task vs scheduled future, direct delayqueue use case, when to use delayqueue, when to use scheduledexecutorservice, when to use java timer, java delayed task beginner, java scheduler selection table, timer scheduled executor beginner primer, timer legacy api, delayed work queue mental model, 자바 Timer vs ScheduledExecutorService, 자바 스케줄러 선택, 자바 타이머 라우터, DelayQueue 언제 쓰나, 레거시 Timer vs ScheduledExecutorService, 스케줄드 executor 기본값, 직접 DelayQueue 구현

## 먼저 10초 결정

먼저 "무엇을 만들고 싶은가"부터 나누면 쉽다.

- 그냥 "몇 초 뒤 실행"과 "주기 실행"이 필요하다면 `ScheduledExecutorService`
- 옛날 `Timer` 코드와 만나고 있거나 아주 단순한 레거시 설명을 읽는 중이라면 `Timer`
- delayed queue 위에 **직접** consumer loop, cancellation 정책, 재등록 규칙을 얹고 싶다면 `DelayQueue`

핵심 문장:

> `Timer`는 오래된 단일 타이머 API,
> `ScheduledExecutorService`는 보통의 애플리케이션 기본값,
> `DelayQueue`는 scheduler를 만드는 재료에 가깝다.

## 빠른 선택표

| 지금 필요한 것 | 먼저 고를 것 | 이유 |
|---|---|---|
| 애플리케이션에서 작업을 몇 초 뒤 실행하거나 주기 실행 | `ScheduledExecutorService` | 표준 executor API, `Future`/cancel/thread-pool 모델이 자연스럽다 |
| 기존 레거시 코드가 이미 `Timer`/`TimerTask`로 묶여 있고 큰 리팩터링 없이 이해만 해야 함 | `Timer` | "왜 옛 코드가 이렇게 생겼나"를 읽는 데는 필요하지만 새 기본값은 아니다 |
| `Delayed` 원소, head blocking, stale ticket skip 같은 내부 규칙을 직접 설계 | `DelayQueue` | 실행 서비스가 아니라 delay-aware queue 계약 자체를 다룬다 |

## 세 가지를 층으로 나누기

| 이름 | 초보자용 정체 | 직접 실행까지 해 주나 | 보통 누가 쓰나 |
|---|---|---|---|
| `Timer` | 오래된 Java 타이머 클래스 | 예 | 레거시 코드 |
| `ScheduledExecutorService` | 지연 실행/주기 실행용 executor 서비스 | 예 | 일반 애플리케이션 코드 |
| `DelayQueue` | 시간이 된 원소만 꺼내는 queue | 아니오 | scheduler/infra 구현 코드 |

여기서 가장 흔한 오해는 `ScheduledExecutorService`와 `DelayQueue`를 같은 층으로 보는 것이다.

- `ScheduledExecutorService`는 "실행 API"다.
- `DelayQueue`는 "대기 규칙을 가진 자료구조"다.

즉 보통은 둘 중 하나를 경쟁적으로 고르는 게 아니라:

- 앱 코드는 `ScheduledExecutorService`
- scheduler 내부 mental model은 `DelayQueue` 쪽

으로 나뉜다.

## 1. 기본값이 왜 `ScheduledExecutorService`인가

초보자에게는 이 질문이 제일 중요하다.

> "나는 queue를 공부하는 중인가, 아니면 일을 나중에 실행시키고 싶은가?"

대부분의 서비스 코드는 두 번째다.

```java
ScheduledExecutorService scheduler =
    Executors.newScheduledThreadPool(2);

scheduler.schedule(job, 3, TimeUnit.SECONDS);
scheduler.scheduleAtFixedRate(heartbeat, 1, 10, TimeUnit.SECONDS);
```

이 경우 관심사는 보통 아래다.

- 몇 초 뒤 실행
- 주기 실행
- 취소 가능 여부
- worker thread 개수

이 질문들은 `ScheduledExecutorService`가 바로 답한다.
내부 queue 규칙까지 직접 만들 필요가 없다.

## 2. `Timer`는 언제 떠올리면 되나

`Timer`는 "새로 고를 기본값"이라기보다 "레거시를 읽을 때 알아야 할 이름"에 가깝다.

| 장면 | 해석 |
|---|---|
| 오래된 블로그나 예제에서 `Timer` / `TimerTask`가 보인다 | 예전 Java 타이머 스타일이라고 보면 된다 |
| 기존 코드가 이미 `Timer` 중심으로 돌아간다 | 당장 읽고 이해하는 데는 필요하다 |
| 새 코드에서 어떤 scheduler API를 고를지 묻는다 | 보통 `ScheduledExecutorService` 쪽으로 간다 |

초보자용으로는 이렇게만 기억해도 충분하다.

- `Timer`를 봤다고 해서 개념이 완전히 다른 것은 아니다.
- 둘 다 "나중에 실행"을 다루지만, 새 코드 기본값은 보통 `ScheduledExecutorService`다.
- 레거시 문맥을 읽는 용도와 새 설계의 기본값을 분리해야 덜 헷갈린다.

## 3. `DelayQueue`는 언제 직접 쓰나

`DelayQueue`를 직접 쓰는 쪽은 애플리케이션 사용법보다 한 단계 아래다.

```java
DelayQueue<TaskTicket> queue = new DelayQueue<>();
TaskTicket task = queue.take(); // 시간이 된 head만 꺼냄
task.run();
```

이 흐름은 "3초 뒤 실행 API"를 편하게 쓰는 것보다 아래 레벨의 관심사다.

| 이런 질문이 보이면 | `DelayQueue` 쪽 신호 |
|---|---|
| `Delayed.compareTo()`와 `getDelay()`를 어떻게 맞추지? | queue 계약 자체를 구현 중 |
| cancel/reschedule 시 stale ticket을 어떻게 건너뛰지? | scheduler 내부 정책을 설계 중 |
| worker가 다음 deadline까지 어떻게 block하지? | delay-aware consumer loop가 핵심 |

즉 `DelayQueue`는 "앱에서 작업 예약하기"보다
"작은 scheduler/runtime를 직접 만들기"에 더 가깝다.

## 자주 하는 오진

1. `Timer`, `ScheduledExecutorService`, `DelayQueue`를 모두 같은 층의 대안으로 본다.
2. `DelayQueue`가 더 저수준이니 초보자에게도 더 정석이라고 생각한다.
3. `Timer`가 단순해 보이니 새 코드 기본값이라고 생각한다.
4. `ScheduledExecutorService`를 쓰면 내부 queue 감각은 전혀 몰라도 된다고 생각한다.

더 안전한 정리는 이렇다.

- 새 앱 코드 기본값은 `ScheduledExecutorService`
- 레거시 읽기 키워드는 `Timer`
- queue/scheduler 내부 구현 주제는 `DelayQueue`

## 짧은 라우팅 예시

| 상황 | 먼저 갈 문서/도구 |
|---|---|
| "알림을 5초 뒤 보내고 싶다" | `ScheduledExecutorService` |
| "옛 코드에 `TimerTask`가 있는데 뭐지?" | `Timer` 레거시 해석 관점 |
| "직접 delayed worker queue를 만들고 싶다" | `DelayQueue` + `Delayed` 계약 문서 |
| "fixed-rate와 fixed-delay 차이가 뭐지?" | [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md), [DelayQueue Repeating Task Primer](./delayqueue-repeating-task-primer.md) |
| "취소 후 queue 안에 오래된 ticket이 남는 이유가 뭐지?" | [ScheduledFuture Cancellation Bridge](./scheduledfuture-cancel-stale-entries.md), [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md) |

## 다음 문서로 이어가기

- `ScheduledExecutorService` 아래에서 delayed work queue가 어떻게 보이는지부터 잡으려면 [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)
- 주기 작업이 밀릴 때 `fixed-rate`와 `fixed-delay`를 먼저 가르려면 [Fixed Rate vs Fixed Delay Overrun Primer](./fixed-rate-vs-fixed-delay-overrun-primer.md)
- due-time gate와 business priority ready queue를 왜 나누는지 보려면 [Timer Priority Policy Split](./timer-priority-policy-split.md)
- queue 내부 deadline 시계를 왜 `nanoTime()` 쪽으로 생각하는지 보려면 [Java Timer Clock Choice Primer](./java-timer-clock-choice-primer.md)
- `DelayQueue`를 직접 구현 레벨에서 이해하려면 [DelayQueue Delayed Contract Primer](./delayqueue-delayed-contract-primer.md)
- repeating task 재등록 규칙은 [DelayQueue Repeating Task Primer](./delayqueue-repeating-task-primer.md)
- cancellation/reschedule stale entry 패턴은 [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md)

## 한 줄 정리

새 코드에서 "나중에 실행"이 필요하면 먼저 `ScheduledExecutorService`를 잡고,
`Timer`는 레거시 해석용으로, `DelayQueue`는 scheduler 내부 구현용으로 분리해서 보면 초반 혼선이 크게 줄어든다.
