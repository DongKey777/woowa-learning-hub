---
schema_version: 3
title: ScheduledFuture Cancellation Bridge
concept_id: data-structure/scheduledfuture-cancel-stale-entries
canonical: false
category: data-structure
difficulty: beginner
doc_role: bridge
level: beginner
language: ko
source_priority: 89
mission_ids: []
review_feedback_tags:
- scheduledfuture-cancel
- stale-timer-entry
- remove-on-cancel-policy
aliases:
- ScheduledFuture cancel stale entry
- ScheduledFuture cancellation bridge
- scheduled executor cancelled task retention
- removeOnCancelPolicy
- cancel true queue size same
- stale timeout ticket
- DelayQueue invalidation
symptoms:
- ScheduledFuture.cancel true를 queue entry가 즉시 물리 제거됐다는 뜻으로 오해한다
- cancelled delayed task가 stale entry로 남아 queue.size가 바로 줄지 않는 현상을 취소 실패로 해석한다
- removeOnCancelPolicy true false 차이를 correctness가 아니라 cleanup 시점과 hot-path 비용 차이로 보지 못한다
intents:
- definition
- troubleshooting
prerequisites:
- data-structure/scheduledexecutorservice-vs-delayqueue-bridge
- data-structure/delayqueue-delayed-contract-primer
next_docs:
- data-structure/cancelled-task-cleanup-purge-vs-removeoncancelpolicy
- data-structure/delayqueue-remove-cost-primer
- data-structure/timer-cancellation-reschedule-stale-entry-primer
linked_paths:
- contents/data-structure/queue-vs-deque-vs-priority-queue-primer.md
- contents/data-structure/scheduledexecutorservice-vs-delayqueue-bridge.md
- contents/data-structure/periodic-task-cancellation-bridge.md
- contents/data-structure/delayqueue-remove-cost-primer.md
- contents/data-structure/cancelled-task-cleanup-purge-vs-removeoncancelpolicy-primer.md
- contents/data-structure/timer-cancellation-reschedule-stale-entry-primer.md
- contents/data-structure/delayqueue-vs-priorityqueue-timer-pitfalls.md
- contents/data-structure/priorityblockingqueue-timer-misuse-primer.md
- contents/data-structure/timing-wheel-vs-delay-queue.md
- contents/algorithm/amortized-analysis-pitfalls.md
confusable_with:
- data-structure/delayqueue-handle-vs-equality-cancel-guide
- data-structure/cancelled-task-cleanup-purge-vs-removeoncancelpolicy
- data-structure/timer-cancellation-reschedule-stale-entry-primer
- data-structure/delayqueue-remove-cost-primer
forbidden_neighbors: []
expected_queries:
- ScheduledFuture cancel true인데 ScheduledThreadPoolExecutor queue size가 그대로인 이유는?
- ScheduledFuture.cancel은 DelayQueue stale ticket 관점에서 어떻게 이해해야 해?
- removeOnCancelPolicy true를 켜면 cancelled task cleanup 시점과 비용이 어떻게 달라져?
- scheduled executor에서 cancel 성공과 queue entry 물리 제거는 왜 다른 사건이야?
- timeout 예약을 취소했는데 stale entry가 남는 문제를 초보자에게 설명해줘
contextual_chunk_prefix: |
  이 문서는 ScheduledFuture.cancel을 실행 금지 상태 전환과 queue cleanup 시점으로
  분리해 설명한다. cancelled delayed task retention, stale ticket, removeOnCancelPolicy,
  DelayQueue-style invalidation을 beginner bridge로 연결한다.
---
# ScheduledFuture Cancellation Bridge

> 한 줄 요약: `ScheduledFuture.cancel()`의 사용자-facing 의미는 "이 예약은 더 이상 실행하지 말라"이고, 내부 자료구조 mental model로는 "ticket을 stale로 만들고 나중에 버리거나, `removeOnCancelPolicy`로 즉시 치울 수 있다"로 이어서 보면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
- [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)
- [Periodic Task Cancellation Bridge](./periodic-task-cancellation-bridge.md)
- [DelayQueue Remove Cost Primer](./delayqueue-remove-cost-primer.md)
- [Cancelled Task Cleanup: `purge()` vs `removeOnCancelPolicy`](./cancelled-task-cleanup-purge-vs-removeoncancelpolicy-primer.md)
- [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md)
- [DelayQueue vs PriorityQueue Timer Pitfalls](./delayqueue-vs-priorityqueue-timer-pitfalls.md)
- [PriorityBlockingQueue Timer Misuse Primer](./priorityblockingqueue-timer-misuse-primer.md)
- [Timing Wheel vs Delay Queue](./timing-wheel-vs-delay-queue.md)
- [Amortized Analysis Pitfalls](../algorithm/amortized-analysis-pitfalls.md)

retrieval-anchor-keywords: scheduledfuture cancellation bridge, scheduledfuture cancel stale entry, scheduledfuture stale ticket, scheduledfuture cancellation semantics, scheduledfuture cancel true, scheduledfuture cancel return value, cancel true queue still contains task, cancel true but queue size same, remove on cancel policy, removeoncancelpolicy timeline, removeoncancelpolicy false vs true, scheduled executor queue retention timeline, scheduled executor queue size cancelled tasks, what is scheduledfuture cancel, beginner scheduled executor cancellation

## 먼저 그림부터

`ScheduledExecutorService`에서 10분 뒤 timeout을 예약했다고 하자.

```java
ScheduledFuture<?> timeout = scheduler.schedule(
    () -> closeConnection(id),
    10,
    TimeUnit.MINUTES
);
```

자료구조 관점에서는 queue 안에 이런 ticket이 들어간 셈이다.

```text
[10분 뒤 실행할 closeConnection ticket]
```

그런데 2초 뒤 응답이 도착하면 timeout은 필요 없어질 수 있다.

```java
timeout.cancel(false);
```

초보자가 여기서 가장 자주 헷갈리는 지점은 이것이다.

> `cancel()`은 "작업을 실행하지 말라"는 상태 변경이지, 항상 "queue 안 ticket을 즉시 물리적으로 제거한다"는 뜻은 아니다.

즉 머릿속 그림은 이렇게 잡는 편이 안전하다.

```text
cancel 전: [10분 뒤 실행할 ticket]
cancel 후: [취소 표시가 붙은 ticket]  // queue에 잠시 남을 수 있음
```

이 취소된 ticket이 바로 없어지지 않고 queue 안에 남아 있는 상태를 이 문서에서는 **stale entry**라고 부른다.

## 초보자용 bridge 먼저

이 문서는 아래 세 문장을 한 그림으로 붙이는 데 집중한다.

| 초보자가 실제로 하는 말 | 바로 붙여야 하는 해석 | 내부 queue 그림 |
|---|---|---|
| "`cancel()`을 눌렀다" | 이 예약을 앞으로 실행하지 말라는 요청이다 | ticket이 stale로 표시될 수 있다 |
| "`cancel()`이 `true`였다" | future 상태 전환은 성공했다 | stale ticket이 queue에 잠시 남아 있을 수 있다 |
| "`queue.size()`가 안 줄었다" | 취소 실패라는 뜻은 아니다 | 물리적 cleanup이 아직 안 된 것일 수 있다 |
| "`removeOnCancelPolicy(true)`를 켰다" | 취소 시 정리까지 더 당겨오겠다는 뜻이다 | stale ticket을 cancel path에서 바로 빼는 쪽에 가깝다 |

짧게 외우면 이렇다.

```text
cancel 성공 = "논리적으로는 무효"
queue 잔류     = "물리적으로는 아직 남을 수 있음"
removeOnCancelPolicy = "그 물리 정리를 지금 할지 결정"
```

즉 `ScheduledFuture.cancel()`을 API 의미로 읽으면 "무효화",
자료구조 의미로 읽으면 "stale ticket 처리 방식 선택"까지 같이 떠올리면 된다.

## `cancel()`을 DelayQueue-style invalidation으로 번역하면

직접 `DelayQueue` 기반 timer를 만들었다고 상상하면 `ScheduledFuture.cancel()`은 더 단순하게 읽힌다.

> "이미 queue에 들어간 deadline ticket을 무효화하고, worker가 나중에 stale entry로 건너뛰게 만든다. 필요하면 cancel 시점에 queue에서 바로 제거할 수도 있다."

즉 executor API의 `cancel()`은, `DelayQueue` 사고방식으로 번역하면 **invalidation request**에 가깝다.

| executor API에서 보이는 것 | `DelayQueue`로 번역한 mental model | 초보자가 붙여야 할 결론 |
|---|---|---|
| `schedule(...)` | `deadline ticket`을 queue에 `offer` | 나중에 실행할 표 하나가 들어갔다 |
| `ScheduledFuture<?>`를 받음 | 그 ticket을 가리키는 handle을 받음 | 나중에 취소/상태 확인할 손잡이가 생겼다 |
| `future.cancel(false)` | ticket에 `cancelled` 표시를 하거나 최신 generation 밖으로 밀어냄 | 이 ticket은 이제 stale 취급될 수 있다 |
| `cancel() == true` | invalidation이 성공했다 | 실행 금지는 확정, 즉시 제거는 별도 |
| `removeOnCancelPolicy(false)` | stale ticket을 queue 안에 둔 채 head에서 버림 | lazy invalidation |
| `removeOnCancelPolicy(true)` | cancel path에서 queue `remove`까지 시도 | eager cleanup |
| worker가 나중에 그 ticket을 만남 | `cancelled`/generation 검사 후 `continue` | stale entry skip |

한 줄로 압축하면 이렇게 생각하면 된다.

```text
ScheduledFuture.cancel()
  = "executor API로 감싼 DelayQueue-style invalidate"
  = "실행 금지" + "queue 청소 시점은 정책에 따라 분리"
```

JDK 내부 구현이 문자 그대로 위 표의 pseudo-code와 동일하다는 뜻은 아니다.
초보자에게 필요한 연결은 "API 이름은 cancel이지만, 자료구조 그림에서는 stale ticket invalidation으로 읽는 편이 맞다"는 점이다.

## API와 queue 동작은 층이 다르다

`ScheduledFuture.cancel()`을 호출하면 Java API 관점에서는 future 상태가 바뀐다.

| 상황 | `cancel(...)`의 의미 |
|---|---|
| 아직 실행 전 | 실행되지 않도록 취소를 시도한다 |
| 이미 완료됨 | 보통 취소에 실패한다 |
| 이미 실행 중 | `mayInterruptIfRunning` 값에 따라 interrupt 시도 여부가 갈린다 |
| 반복 작업 | 이후 반복 실행이 더 진행되지 않도록 취소한다 |

하지만 내부 queue 관점에서는 질문이 하나 더 남는다.

> 취소된 delayed task entry를 queue에서 지금 바로 뺄까, 아니면 나중에 head로 올라왔을 때 버릴까?

이것은 correctness보다 **queue 비용 배치**에 가까운 문제다.
취소된 작업이 실제로 실행되지 않도록 하는 것과, 취소된 entry를 queue 메모리에서 언제 제거하는 것은 같은 말이 아니다.

그래서 초보자는 아래 세 축을 따로 보는 편이 안전하다.

| 보는 축 | 질문 | 바로 연결되는 값 |
|---|---|---|
| future 상태 | "이 작업은 취소됐나?" | `cancel()` 반환값, `isCancelled()` |
| 실행 여부 | "이 작업이 실제로 실행될까?" | worker가 cancelled 상태를 보고 건너뛴다 |
| queue 정리 시점 | "취소된 흔적이 queue에서 언제 사라지나?" | lazy 유지 vs `removeOnCancelPolicy(true)` |

즉 `cancel()`이 성공했다는 사실과, queue가 즉시 비워졌다는 사실은 동일한 문장이 아니다.

## 한 요청을 세 층으로 같이 읽기

아래는 초보자가 가장 많이 만나는 timeout 취소 상황을 세 층으로 나눈 표다.

| 시점 | 사용자 코드에서 보이는 일 | future / executor 의미 | 내부 stale-ticket mental model |
|---|---|---|---|
| `t=0s` | `schedule(...)` 호출 | 나중에 실행할 future를 받는다 | deadline이 붙은 ticket이 queue에 들어간다 |
| `t=2s` | `cancel(false)` 호출 | 이 예약을 실행하지 않도록 취소를 시도한다 | ticket을 stale로 취급하거나 즉시 제거를 시도한다 |
| 직후 | `cancel(...) == true` | future는 cancelled 상태가 된다 | correctness는 끝났지만 cleanup 정책은 아직 별도다 |
| 그 뒤 | `getQueue().size()` 확인 | 숫자가 바로 안 줄 수도 있다 | stale ticket이 lazy cleanup을 기다릴 수 있다 |
| 만료 시점 | worker가 head를 본다 | cancelled task는 실행되지 않아야 한다 | stale ticket이면 skip 후 버린다 |

이 표를 머릿속에 넣어 두면 아래 문장이 동시에 참이라는 점이 덜 이상해진다.

- `cancel(false)`는 성공했다.
- 그 task는 실행되지 않는다.
- queue에는 취소된 ticket 흔적이 잠시 남아 있을 수 있다.

## `cancel()` 반환값을 어떻게 읽나

`cancel()`은 "state 전환 시도" API다.
반환값도 먼저 그 축에서 읽어야 한다.

| 표현 | 초보자용 해석 | 여기서 바로 알 수 없는 것 |
|---|---|---|
| `cancel(...) == true` | future가 cancelled 상태로 바뀌었다 | queue entry가 즉시 제거됐는지 |
| `cancel(...) == false` | 이미 끝났거나, 지금 시점에 취소하지 못했다 | queue에 무엇이 남았는지 |
| `future.isCancelled() == true` | future는 취소 상태다 | `getQueue().size()`가 줄었는지 |
| `future.isDone() == true` | 이제 더 기다릴 필요는 없다 | 성공 완료인지, 예외인지, 취소인지 |

특히 아래 오해가 흔하다.

```java
boolean cancelled = timeout.cancel(false);
System.out.println(cancelled); // true
```

이 `true`는 "이제 실행하지 말라"가 성공했다는 뜻이지,
"queue 안에서 그 자리의 node를 즉시 지웠다"는 뜻이 아니다.

## 기본 mental model: lazy stale entry

`ScheduledThreadPoolExecutor`는 취소된 delayed task를 queue에 잠시 남겨 둘 수 있다.
이때 worker가 나중에 그 entry를 만나면 "이미 취소됐네"라고 확인하고 실행하지 않는다.

```text
t=0s      10분 뒤 timeout 예약
t=2s      응답 도착, timeout.cancel(false)
t=10m     취소된 timeout entry가 head 근처로 올라옴
worker    cancelled 상태 확인 후 실행하지 않고 버림
```

이 방식은 lazy cancellation이다.

| 관점 | lazy 방식의 효과 |
|---|---|
| correctness | 취소 상태를 확인하므로 작업은 실행되지 않는다 |
| cancel 호출 비용 | queue 중간에서 찾아 빼지 않아도 되어 싸질 수 있다 |
| queue 크기 | 취소된 entry가 delay가 끝날 때까지 남을 수 있다 |
| 메모리 | 장기 timer가 많이 취소되면 retention이 보일 수 있다 |
| 모니터링 | `queue.size()`가 실제 유효 작업 수보다 크게 느껴질 수 있다 |

핵심은 "lazy라서 작업이 실행된다"가 아니다.
**lazy라서 실행은 막되, queue 정리는 뒤로 미룬다**가 더 정확하다.

## `removeOnCancelPolicy`는 무엇을 바꾸나

`ScheduledThreadPoolExecutor`를 직접 쓰면 취소 시 제거 정책을 켤 수 있다.

```java
ScheduledThreadPoolExecutor scheduler =
    new ScheduledThreadPoolExecutor(4);

scheduler.setRemoveOnCancelPolicy(true);
```

이 정책을 켜면 `cancel()`된 delayed task를 work queue에서 즉시 제거하는 쪽으로 동작한다.
초보자용으로 말하면 "취소 표시만 해 두고 나중에 버리기" 대신 "취소할 때 queue에서도 빼기"에 가깝다.

| 정책 | queue 처리 감각 | 장점 | 비용 |
|---|---|---|---|
| `removeOnCancelPolicy = false` | 취소된 entry가 delay 만료 전까지 남을 수 있다 | cancel hot path가 단순하다 | stale entry, 메모리 retention, `queue.size()` 착시가 생길 수 있다 |
| `removeOnCancelPolicy = true` | 취소 시 queue에서도 제거한다 | queue가 유효 작업 수에 더 가까워진다 | cancel 시점에 queue 제거 비용과 lock 경쟁이 올 수 있다 |

그래서 이 옵션은 "무조건 켜야 하는 정답"이라기보다 workload 선택이다.

여기서 "제거 비용" 감각이 잘 안 잡히면 [DelayQueue Remove Cost Primer](./delayqueue-remove-cost-primer.md)를 같이 보면 된다.
heap 계열 queue에서 head를 꺼내는 일과 queue 중간의 취소 대상을 찾아 `remove`하는 일은 같은 비용 모양이 아니기 때문이다.

`removeOnCancelPolicy(true)`와 `purge()`를 둘 다 "취소된 task cleanup"으로 보되, 하나는 cancel 시점의 즉시 정리 정책이고 다른 하나는 나중 batch cleanup이라는 차이만 따로 떼어 보고 싶다면 [Cancelled Task Cleanup: `purge()` vs `removeOnCancelPolicy`](./cancelled-task-cleanup-purge-vs-removeoncancelpolicy-primer.md)를 이어서 보면 된다.

이 차이는 상각 관점으로도 읽을 수 있다.
lazy 정책은 cleanup 비용을 나중 dequeue 시점으로 미루고, 즉시 제거 정책은 그 비용을 `cancel()` hot path로 당겨온다.
이런 "언제 비용을 낼지" 감각이 더 필요하면 [Amortized Analysis Pitfalls](../algorithm/amortized-analysis-pitfalls.md)를 같이 보면 연결이 잘 된다.

## `removeOnCancelPolicy`는 무엇을 바꾸나 (계속 2)

| workload 신호 | 먼저 생각할 방향 |
|---|---|
| 예약은 많지만 취소가 거의 없다 | 기본 lazy 정책도 충분할 수 있다 |
| 긴 delay 작업을 많이 예약하고 대부분 곧 취소한다 | `removeOnCancelPolicy(true)` 검토 |
| timeout을 요청마다 만들고 성공 응답 때 취소한다 | 취소된 장기 timeout retention을 관찰해야 한다 |
| 취소 호출이 매우 뜨거운 hot path다 | 즉시 제거 비용이 latency에 들어오는지 확인 |
| 수십만 timeout churn이 계속된다 | heap 기반 scheduler보다 [Timing Wheel vs Delay Queue](./timing-wheel-vs-delay-queue.md)까지 비교 |

## `removeOnCancelPolicy` 타임라인으로 보면

초보자에게는 "같은 `cancel(false)`인데 왜 `queue.size()` 체감이 달라지지?"를 시간축으로 보는 편이 가장 쉽다.

상황은 동일하게 두고 비교해 보자.

- `t=0s`: 30초 뒤 timeout 예약
- `t=2s`: 실제 응답이 와서 `cancel(false)` 호출
- 비교 포인트: 취소 직후와 원래 만료 시각에 queue 안에 무엇이 남는가

| 시점 | `removeOnCancelPolicy(false)` | `removeOnCancelPolicy(true)` |
|---|---|---|
| `t=0s` 예약 직후 | live ticket 1개가 queue에 들어간다 | live ticket 1개가 queue에 들어간다 |
| `t=2s` `cancel(false)` 직후 | future는 cancelled, queue에는 stale ticket이 남을 수 있다 | future는 cancelled, cancel 경로에서 queue 제거를 시도한다 |
| `t=2s` 직후 `getQueue().size()` | 아직 `1`처럼 보일 수 있다 | `0`에 더 가까운 결과를 기대할 수 있다 |
| `t=30s` 원래 만료 시각 | worker가 stale ticket을 만나 skip 후 버린다 | 이미 제거됐다면 worker가 만날 ticket이 없다 |
| 비용이 실리는 곳 | 나중 dequeue 시점으로 cleanup이 밀린다 | `cancel()` 시점으로 cleanup 비용이 당겨진다 |

ASCII 그림으로 붙이면 더 직관적이다.

```text
removeOnCancelPolicy(false)
t=0s   [live timeout]
t=2s   cancel(false)
       [cancelled timeout]   <- queue에 남을 수 있음
t=30s  worker가 꺼내서 skip
       []
```

```text
removeOnCancelPolicy(true)
t=0s   [live timeout]
t=2s   cancel(false)
       []                    <- cancel 경로에서 제거 시도
t=30s  worker가 만날 stale ticket이 없음
       []
```

중요한 포인트는 이것이다.

> 두 경우 모두 task 실행은 막힌다. 달라지는 것은 "취소 흔적이 queue에 얼마나 오래 남느냐"다.

즉 이 옵션은 correctness 스위치보다 **queue retention timeline 스위치**로 기억하는 편이 덜 헷갈린다.

## 어떤 설명을 먼저 붙이면 덜 헷갈리나

| 학습자가 먼저 본 현상 | 바로 붙여 줄 설명 | 이어서 볼 문서 |
|---|---|---|
| `cancel()`은 `true`인데 `queue.size()`가 그대로다 | lazy cleanup이면 stale entry가 남을 수 있다 | [Cancelled Task Cleanup: `purge()` vs `removeOnCancelPolicy`](./cancelled-task-cleanup-purge-vs-removeoncancelpolicy-primer.md) |
| `removeOnCancelPolicy(true)`를 켰더니 queue가 빨리 줄었다 | 실행 의미가 바뀐 것이 아니라 retention timeline이 짧아진 것이다 | [DelayQueue Remove Cost Primer](./delayqueue-remove-cost-primer.md) |
| timeout churn이 많아 메모리가 걱정된다 | long-delay cancelled entry retention을 먼저 의심한다 | [Timing Wheel vs Delay Queue](./timing-wheel-vs-delay-queue.md) |
| 직접 timer queue를 구현 중이다 | cancel은 stale invalidation, worker는 stale skip을 떠올린다 | [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md) |

## `mayInterruptIfRunning`과 헷갈리지 말기

`cancel(true)`와 `cancel(false)`의 boolean은 queue 제거 정책이 아니다.

```java
future.cancel(false); // 이미 실행 중이면 interrupt하지 않음
future.cancel(true);  // 이미 실행 중이면 interrupt를 시도할 수 있음
```

이 값은 **실행 중인 작업을 interrupt할지**에 관한 신호다.
취소된 scheduled entry를 queue에서 즉시 제거할지 말지는 `ScheduledThreadPoolExecutor`의 `removeOnCancelPolicy` 쪽 관심사다.

| 헷갈리는 질문 | 보는 축 |
|---|---|
| 이미 실행 중인 task를 interrupt할까? | `cancel(true/false)`의 `mayInterruptIfRunning` |
| 아직 실행 전인 delayed task가 실행되지 않게 할까? | `ScheduledFuture`의 cancelled state |
| 취소된 delayed task entry를 queue에서 즉시 뺄까? | `removeOnCancelPolicy` |

## 작은 예시로 비용 보기

아래 코드는 요청 timeout을 예약했다가 응답이 오면 취소하는 흔한 형태다.

```java
class RequestTimeouts {
    private final ScheduledThreadPoolExecutor scheduler =
        new ScheduledThreadPoolExecutor(2);

    RequestTimeouts() {
        scheduler.setRemoveOnCancelPolicy(true);
    }

    ScheduledFuture<?> registerTimeout(String requestId) {
        return scheduler.schedule(
            () -> failRequest(requestId),
            30,
            TimeUnit.SECONDS
        );
    }

    void onResponse(ScheduledFuture<?> timeout) {
        timeout.cancel(false);
    }

    private void failRequest(String requestId) {
        // timeout 처리
    }
}
```

`setRemoveOnCancelPolicy(true)`를 켜지 않아도 `cancel(false)`된 timeout은 실행되지 않아야 한다.
차이는 "30초가 될 때까지 취소된 entry가 queue 안에 남을 수 있느냐"다.

요청이 초당 1개라면 큰 문제가 아닐 수 있다.
하지만 요청이 초당 수천 개이고 대부분 100ms 안에 응답되어 timeout이 취소된다면, 30초짜리 stale timeout entry가 많이 쌓일 수 있다.

이때 trade-off는 이렇게 읽으면 된다.

```text
lazy cancellation:
  cancel은 가볍지만, 취소된 ticket 청소가 나중으로 밀림

removeOnCancelPolicy(true):
  cancel이 queue 제거까지 부담하지만, stale ticket retention을 줄임
```

## `queue.size()`는 왜 쉽게 착시를 주나

`ScheduledThreadPoolExecutor`를 직접 들고 있으면 queue 크기를 볼 수 있다.

```java
ScheduledThreadPoolExecutor scheduler =
    new ScheduledThreadPoolExecutor(1);

ScheduledFuture<?> timeout = scheduler.schedule(
    () -> closeConnection(id),
    1,
    TimeUnit.HOURS
);

timeout.cancel(false);
System.out.println(scheduler.getQueue().size());
```

초보자가 기대하는 그림은 보통 이렇다.

```text
cancel 성공 -> size 0
```

하지만 lazy stale entry 정책이면 실제 관찰은 이렇게 나올 수 있다.

```text
cancel 성공 -> size 1  // 취소된 ticket이 아직 queue에 남아 있음
```

이 수치는 "queue에 남은 entry 수"에 가깝다.
항상 "앞으로 실행될 유효 작업 수"와 같다고 보면 모니터링 해석이 틀어진다.

| 관찰값 | 바로 결론 내리면 위험한 해석 | 더 안전한 해석 |
|---|---|---|
| `cancel()`이 `true`다 | queue에서도 즉시 사라졌다 | 실행 취소는 성공, cleanup 시점은 별도 |
| `getQueue().size()`가 크다 | 유효 예약 작업이 전부 많다 | stale entry가 섞였을 수 있다 |
| `isCancelled()`가 `true`다 | 메모리 retention 문제도 끝났다 | 실행은 막혔지만 queue 잔류는 남을 수 있다 |

## 자주 하는 오해

1. `ScheduledFuture.cancel(false)`가 내부 queue entry를 항상 즉시 제거한다고 생각한다.
2. `cancel(true)`를 호출하면 stale entry 문제도 함께 사라진다고 생각한다.
3. `isCancelled()`가 `true`면 queue 메모리에서도 이미 사라졌다고 생각한다.
4. `queue.size()`를 "실제로 실행될 task 수"로 그대로 해석한다.
5. `removeOnCancelPolicy(true)`가 모든 scheduler 구현에 있는 공통 `ScheduledExecutorService` 기능이라고 생각한다.
6. lazy stale entry를 correctness 버그로만 보고, hot path 비용을 뒤로 미루는 선택이라는 점을 놓친다.
7. `cancel()`이 `true`면 "취소 성공"과 "queue 즉시 제거 성공"을 한 문장으로 묶어 생각한다.

특히 5번이 중요하다.
`removeOnCancelPolicy`는 `ScheduledThreadPoolExecutor`의 정책이다.
변수 타입을 `ScheduledExecutorService`로만 들고 있다면 이 설정 API가 보이지 않는다.

## 다음 문서로 이어가기

- `ScheduledExecutorService`와 `DelayQueue` mental model 연결이 먼저 필요하면 [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)
- `purge()`와 `removeOnCancelPolicy(true)`를 cleanup 시점 비교로 따로 보고 싶으면 [Cancelled Task Cleanup: `purge()` vs `removeOnCancelPolicy`](./cancelled-task-cleanup-purge-vs-removeoncancelpolicy-primer.md)
- 직접 `DelayQueue` timer를 만들 때 `generation`으로 오래된 ticket을 거르는 흐름은 [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md)
- `PriorityQueue`, `PriorityBlockingQueue`, `DelayQueue` 중 무엇을 써야 할지 헷갈리면 [DelayQueue vs PriorityQueue Timer Pitfalls](./delayqueue-vs-priorityqueue-timer-pitfalls.md)
- 비용을 "지금 낼지 나중에 낼지"라는 상각 감각으로 더 읽고 싶으면 [Amortized Analysis Pitfalls](../algorithm/amortized-analysis-pitfalls.md)
- 취소 churn이 커져 heap 자체가 부담되면 [Timing Wheel vs Delay Queue](./timing-wheel-vs-delay-queue.md)

## 꼬리질문

> Q: `ScheduledFuture.cancel(false)`를 호출하면 작업은 어떻게 되나요?
> 의도: Future 상태와 실행 여부를 먼저 분리하는지 확인
> 핵심: 아직 실행 전이면 실행되지 않도록 취소된다. 다만 내부 delayed queue entry가 즉시 제거되는지는 별도 정책이다.

> Q: `removeOnCancelPolicy(true)`는 무엇을 위해 켜나요?
> 의도: correctness 옵션이 아니라 queue 정리 비용 배치 옵션임을 이해하는지 확인
> 핵심: 취소된 delayed task를 queue에 오래 남기지 않고 cancel 시점에 제거해 stale entry retention을 줄이기 위해 켠다.

> Q: `cancel(true)`와 `removeOnCancelPolicy(true)`의 관심사는 어떻게 다른가요?
> 의도: interrupt와 queue cleanup을 구분하는지 확인
> 핵심: `cancel(true)`의 boolean은 실행 중 task interrupt 시도 여부이고, `removeOnCancelPolicy`는 취소된 scheduled entry를 queue에서 즉시 제거할지에 관한 정책이다.

> Q: `cancel(false)`가 `true`인데 `getQueue().size()`가 왜 그대로일 수 있나요?
> 의도: future 상태와 queue 물리적 정리를 분리하는지 확인
> 핵심: cancel 성공은 실행 취소 상태 전환을 뜻할 뿐이다. lazy 정책이면 취소된 ticket은 나중에 head로 올라올 때까지 queue 안에 남아 있을 수 있다.

## 한 줄 정리

`ScheduledFuture.cancel()`은 "이 예약 작업을 실행하지 말라"는 상태 변경이고, 취소된 delayed queue entry를 바로 치울지 lazy하게 나중에 버릴지는 `ScheduledThreadPoolExecutor`의 `removeOnCancelPolicy`로 조절하는 queue-cost trade-off다.
