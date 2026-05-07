---
schema_version: 3
title: Timeout Churn Structure Selection Bridge
concept_id: data-structure/timeout-churn-structure-selection-bridge
canonical: false
category: data-structure
difficulty: beginner
doc_role: chooser
level: beginner
language: ko
source_priority: 90
mission_ids: []
review_feedback_tags:
- timeout-churn
- timer-structure-selection
- delayqueue-vs-timing-wheel
aliases:
- timeout churn structure selection
- ScheduledThreadPoolExecutor vs DelayQueue vs timing wheel
- many long delay timeouts cancelled
- cancellation heavy timer queue
- heap timer queue vs timing wheel
- long delay cancelled task retention
- timeout scheduler chooser
symptoms:
- long-delay timeout이 많고 대부분 cancel되는 workload를 단순 API 선택 문제로만 보고 cancellation churn 비용을 분리하지 않는다
- DelayQueue로 내려오면 heap cancel/remove와 stale entry 문제가 자동 해결된다고 오해한다
- timing wheel의 bucket 근사와 churn 최적화 tradeoff를 exact earliest ordering 요구와 비교하지 않는다
intents:
- comparison
- design
prerequisites:
- data-structure/scheduledexecutorservice-vs-delayqueue-bridge
- data-structure/scheduledfuture-cancel-stale-entries
next_docs:
- data-structure/timing-wheel-vs-delay-queue
- data-structure/hierarchical-timing-wheel
- data-structure/timer-cancellation-reschedule-stale-entry-primer
linked_paths:
- contents/data-structure/scheduledexecutorservice-vs-delayqueue-bridge.md
- contents/data-structure/scheduledfuture-cancel-stale-entries.md
- contents/data-structure/delayqueue-remove-cost-primer.md
- contents/data-structure/timer-cancellation-reschedule-stale-entry-primer.md
- contents/data-structure/cancelled-task-cleanup-purge-vs-removeoncancelpolicy-primer.md
- contents/data-structure/timing-wheel-vs-delay-queue.md
- contents/data-structure/hierarchical-timing-wheel.md
confusable_with:
- data-structure/timing-wheel-vs-delay-queue
- data-structure/scheduledexecutorservice-vs-delayqueue-bridge
- data-structure/delayqueue-remove-cost-primer
- data-structure/cancelled-task-cleanup-purge-vs-removeoncancelpolicy
forbidden_neighbors: []
expected_queries:
- long delay timeout이 많고 대부분 cancel되면 ScheduledThreadPoolExecutor DelayQueue timing wheel 중 뭘 골라?
- timeout cancellation churn이 큰 workload에서 heap timer queue와 timing wheel은 어떻게 달라?
- DelayQueue를 쓰면 long-delay cancelled task retention 문제가 자동으로 해결돼?
- removeOnCancelPolicy와 timing wheel은 timeout churn을 어떤 다른 방식으로 다뤄?
- 정확한 deadline ordering보다 bucket 근사 expiry를 허용하면 어떤 timer 구조가 유리해?
contextual_chunk_prefix: |
  이 문서는 long-delay timeout이 많고 대부분 만료 전에 취소되는 workload에서
  ScheduledThreadPoolExecutor, DelayQueue, timing wheel을 고르는 chooser다.
  heap stale entry, remove cost, bucket precision tradeoff를 beginner bridge로 연결한다.
---
# Timeout Churn Structure Selection Bridge

> 한 줄 요약: "오래 기다리는 timeout을 엄청 많이 걸어 두지만, 대부분은 중간에 취소된다"면 `ScheduledThreadPoolExecutor`와 `DelayQueue`는 heap 계열 기본값이고, timing wheel은 그 cancellation churn을 더 싸게 처리하려고 쓰는 구조다.

**난이도: 🟢 Beginner**

관련 문서:

- [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)
- [ScheduledFuture Cancellation Bridge](./scheduledfuture-cancel-stale-entries.md)
- [DelayQueue Remove Cost Primer](./delayqueue-remove-cost-primer.md)
- [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md)
- [Cancelled Task Cleanup: `purge()` vs `removeOnCancelPolicy`](./cancelled-task-cleanup-purge-vs-removeoncancelpolicy-primer.md)
- [Timing Wheel vs Delay Queue](./timing-wheel-vs-delay-queue.md)
- [Hierarchical Timing Wheel](./hierarchical-timing-wheel.md)

- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)

retrieval-anchor-keywords: scheduledthreadpoolexecutor vs delayqueue vs timing wheel, timeout churn structure selection, many long-delay timeouts cancelled, cancellation heavy timer queue, long delay timeout cancellation, scheduledthreadpoolexecutor long delay cancel, delayqueue long delay cancel, timing wheel long delay cancel, timer churn beginner, java timeout structure choice, heap timer queue vs timing wheel, delayed timeout cancellation retention, removeoncancelpolicy timeout churn, long delay cancelled task retention, beginner timer structure bridge

## 먼저 그림부터

세 구조를 모두 "알람 보관함"으로 생각하면 쉽다.

- `ScheduledThreadPoolExecutor`: 알람 보관함 + worker thread + `Future`까지 같이 주는 완제품
- `DelayQueue`: 알람 보관함만 직접 다루는 부품
- timing wheel: 알람 시각을 촘촘히 정렬하기보다 비슷한 시각끼리 칸(bucket)에 모아 두는 대량 처리형 보관함

여기서 질문은 보통 이것이다.

> "10분 뒤, 30분 뒤 같은 long-delay timeout을 많이 등록하는데, 대부분은 응답이 먼저 와서 곧 취소된다. 뭘 골라야 하지?"

초보자용 핵심은 한 문장으로 정리된다.

> 적당한 규모면 heap 계열 기본값부터 시작하고, long-delay cancellation churn이 정말 커졌을 때 timing wheel을 검토한다.

## 왜 long-delay + frequent cancel이 까다로운가

예를 들어 요청마다 30초 timeout을 건다고 하자.

```text
t=0s   timeout 100만 개 예약
t=50ms 대부분 응답 도착
t=50ms timeout 95만 개 취소
```

이 workload의 문제는 "언제 실행되나"보다 "대부분 실행되기 전에 취소된다"에 있다.

| 보이는 현상 | 왜 부담이 생기나 |
|---|---|
| timeout 수가 많다 | queue 안 entry 자체가 많아진다 |
| delay가 길다 | 취소된 entry가 오래 남아 있을 수 있다 |
| cancel이 많다 | 즉시 제거면 cancel path가 무거워지고, lazy 제거면 stale entry가 쌓인다 |
| 정확한 1ms 순서가 꼭 필요하지 않을 수 있다 | bucket 구조가 더 유리해질 여지가 생긴다 |

즉 이 문제는 "타이머 API 하나 고르기"가 아니라
**정확한 deadline ordering이 중요한지, cancellation churn을 얼마나 싸게 처리해야 하는지**를 고르는 일이다.

## 세 후보를 한 번에 보기

| 구조 | 초보자용 역할 | 이 상황에서의 기본 인상 |
|---|---|---|
| `ScheduledThreadPoolExecutor` | 바로 쓰는 Java 스케줄러 | 기본값으로 가장 안전하다 |
| `DelayQueue` | 직접 scheduler를 조립할 때 쓰는 delay-aware queue | 커스텀 제어는 쉽지만 heap 취소 고민은 그대로 남는다 |
| timing wheel | 대량 timeout churn용 bucket scheduler | long-delay 대량 취소에 강하지만 정밀도와 구현 단순성을 양보한다 |

중요한 점:

- `ScheduledThreadPoolExecutor`와 `DelayQueue`는 층이 다르다.
- 하지만 **long-delay + frequent cancel** 문제에서는 둘 다 대체로 heap 계열 고민을 공유한다.
- timing wheel은 그 고민을 "정밀 정렬" 대신 "bucket 처리"로 바꾸려는 선택이다.

## 가장 빠른 선택표

| 질문 | 우선 선택 | 이유 |
|---|---|---|
| 그냥 Java에서 timeout 실행과 취소를 안전하게 쓰고 싶나 | `ScheduledThreadPoolExecutor` | API, thread pool, `Future`를 한 번에 준다 |
| worker loop, 최신성 검사, cancel 정책을 직접 설계해야 하나 | `DelayQueue` | 구조를 노출해서 커스텀 scheduler를 만들기 쉽다 |
| timeout 수가 매우 많고 대부분 만료 전에 취소되나 | timing wheel 검토 | bucket 기반이라 cancellation churn 부담을 줄이기 쉽다 |
| 정확한 earliest deadline ordering이 중요하나 | heap 계열 (`ScheduledThreadPoolExecutor` / `DelayQueue`) | 가장 이른 deadline 하나를 정확히 뽑기 쉽다 |
| 몇 ms 정도의 tick 오차를 받아들일 수 있나 | timing wheel 쪽 | exact ordering보다 대량 처리에 유리하다 |

## 1. `ScheduledThreadPoolExecutor`: 먼저 잡는 기본값

이 구조는 "자료구조 선택"보다 "운영 가능한 완제품 선택"에 가깝다.

```java
ScheduledThreadPoolExecutor scheduler = new ScheduledThreadPoolExecutor(4);
```

초보자에게는 아래 장점이 크다.

- 바로 `schedule(...)`, `cancel(...)`, periodic API를 쓸 수 있다
- 직접 worker loop를 만들지 않아도 된다
- 기본 mental model이 비교적 단순하다

하지만 long-delay timeout을 엄청 많이 걸고 자주 취소하면 이런 고민이 생긴다.

| 질문 | beginner용 해석 |
|---|---|
| 취소된 task가 queue에 남아 보이나 | lazy cleanup일 수 있다 |
| cancel이 너무 잦은가 | 즉시 제거 정책은 cancel path 비용을 올릴 수 있다 |
| timeout 수가 매우 큰가 | heap 계열 자체가 churn에 불리할 수 있다 |

그래서 보통은 이렇게 시작한다.

1. 먼저 `ScheduledThreadPoolExecutor`를 쓴다.
2. 취소된 task retention이 문제면 `removeOnCancelPolicy` 같은 cleanup 정책을 점검한다.
3. 그래도 long-delay cancellation churn이 너무 크면 timing wheel까지 비교한다.

즉 초보자용 결론은:

> "일단 이걸로 시작하되, 대량 취소 때문에 queue retention과 cancel 비용이 눈에 띄면 다음 단계로 넘어간다."

## 2. `DelayQueue`: 직접 만들 자유, 대신 책임도 직접 짐

`DelayQueue`는 "만료된 head만 꺼낼 수 있는 queue"다.

```text
offer(ticket with deadline)
take() when deadline expires
```

이 구조가 맞는 순간은 보통 이럴 때다.

- timeout이 아니라 custom scheduler semantics를 만들고 싶다
- generation, stale skip, ready queue 분리 같은 정책을 직접 설계해야 한다
- executor 완제품보다 queue 부품이 더 잘 맞는다

하지만 이 문제에서 중요한 함정은 이것이다.

> `DelayQueue`로 내려와도 long-delay cancellation churn이 자동으로 해결되지는 않는다.

왜냐하면:

- 여전히 heap 스타일의 deadline ordering을 다룬다
- queue 중간의 특정 timer 제거는 별도 비용이 붙는다
- reschedule/cancel은 stale entry 정책을 직접 정해야 한다

그래서 `DelayQueue`는 이런 답에 가깝다.

| 원하는 것 | `DelayQueue`가 주는 것 | 직접 해야 하는 것 |
|---|---|---|
| 만료 시각까지 기다리기 | 준다 | 없음 |
| 취소 handle API | 안 준다 | 직접 설계 |
| stale entry skip | 패턴만 가능 | 직접 구현 |
| long-delay cancel churn 최적화 | 자동으로 안 됨 | 직접 정책화 |

즉 "직접 만들고 싶다"가 이유라면 `DelayQueue`가 맞을 수 있다.
하지만 "heap 취소 비용이 싫다"만 이유라면 timing wheel 쪽 질문을 먼저 해야 한다.

## 3. timing wheel: 정밀 순서보다 churn을 먼저 본다

timing wheel은 deadline을 전부 촘촘히 정렬하기보다,
비슷한 시각의 timeout을 같은 bucket에 넣는다.

```text
tick 0 | tick 1 | tick 2 | tick 3 | ...
   A,B      C        -      D,E
```

이렇게 보면 장점이 바로 보인다.

- timeout 등록/취소를 bucket 수준으로 다루기 쉽다
- long-delay timeout이 많아도 exact heap ordering 부담을 줄일 수 있다
- "대부분 나중에 취소될 timeout" workload에 잘 맞는다

대신 양보도 있다.

| 양보하는 점 | 왜 생기나 |
|---|---|
| exact earliest ordering | 같은 bucket 안에서는 묶여 처리될 수 있다 |
| 아주 세밀한 deadline precision | tick 단위 근사가 들어간다 |
| 구현 단순성 | wheel, cascade, bucket sweep 개념이 필요하다 |

초보자용 결론은 이렇다.

> "timeout이 엄청 많고 대부분 취소되며, 몇 ms~수십 ms 오차를 받아들일 수 있다면 timing wheel 후보가 강해진다."

## 자주 나오는 실제 선택 흐름

### 시나리오 A: 일반적인 JVM 서비스 timeout

- 요청 수는 많지만 timer가 수십만~수백만 수준까지 가지는 않는다
- Java executor API가 필요하다
- 복잡한 커스텀 scheduler는 원하지 않는다

이때는 `ScheduledThreadPoolExecutor`가 먼저다.

### 시나리오 B: custom retry/lease/timeout scheduler

- 실행보다 queue 정책을 직접 통제해야 한다
- generation, stale skip, ready queue 분리를 구현해야 한다
- 규모는 아직 timing wheel까지 가지 않았다

이때는 `DelayQueue`가 자연스럽다.

### 시나리오 C: connection idle timeout, RPC timeout 같은 대량 churn

- long-delay timeout이 매우 많다
- 대부분 실제 만료 전에 취소된다
- exact 1ms ordering보다 시스템 부담이 더 중요하다

이때는 timing wheel 검토가 자연스럽다.

## 흔한 오해

1. `ScheduledThreadPoolExecutor`와 timing wheel이 그냥 API 취향 차이라고 생각한다.
2. `DelayQueue`로 직접 만들면 heap cancel 비용 문제가 사라진다고 생각한다.
3. long-delay timeout이 많아도 "어차피 실행은 안 되니까" 취소된 entry 비용이 없다고 생각한다.
4. timing wheel을 쓰면 항상 더 정확하고 더 빠르다고 생각한다.
5. exact ordering이 필요한데도 churn만 보고 timing wheel로 바로 간다.

## 지금 질문에 대한 짧은 답

"많은 long-delay timeout이 자주 취소된다"는 조건만 놓고 보면 선택의 기본 방향은 이렇다.

| 목표 | 더 자연스러운 선택 |
|---|---|
| 안전한 Java 기본값 | `ScheduledThreadPoolExecutor` |
| custom scheduler 조립 | `DelayQueue` |
| 대량 cancellation churn 완화 | timing wheel |

한 줄로 압축하면:

> 기본은 `ScheduledThreadPoolExecutor`, 직접 조립이 필요하면 `DelayQueue`, 정말 큰 long-delay cancellation churn이면 timing wheel을 검토한다.

## 다음 문서로 이어가기

- Java 기본 scheduler와 delay-aware queue 연결부터 다시 잡으려면 [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)
- `cancel()`이 왜 "실행 금지"와 "즉시 제거"를 같은 뜻으로 보장하지 않는지 보려면 [ScheduledFuture Cancellation Bridge](./scheduledfuture-cancel-stale-entries.md)
- heap queue에서 중간 removal 비용이 왜 따로 드는지 보려면 [DelayQueue Remove Cost Primer](./delayqueue-remove-cost-primer.md)
- 취소/재예약을 stale entry와 generation으로 이해하려면 [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md)
- timing wheel 쪽 구조 비교를 더 보려면 [Timing Wheel vs Delay Queue](./timing-wheel-vs-delay-queue.md)

## 한 줄 정리

long-delay timeout을 많이 걸어 두고 대부분 곧 취소하는 workload에서는 heap 계열 기본값인 `ScheduledThreadPoolExecutor`와 `DelayQueue`가 먼저이고, cancellation churn과 retention 부담이 충분히 커졌을 때 timing wheel이 강한 후보가 된다.
