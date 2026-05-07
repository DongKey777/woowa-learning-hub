---
schema_version: 3
title: ScheduledThreadPoolExecutor Queue Observability Primer
concept_id: data-structure/scheduledthreadpoolexecutor-queue-observability-primer
canonical: false
category: data-structure
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 89
mission_ids: []
review_feedback_tags:
- scheduled-executor-observability
- queue-size-not-backlog
- cancelled-task-retention
aliases:
- ScheduledThreadPoolExecutor queue observability
- scheduled executor queue size
- getQueue size active count completed task count
- queue size not backlog
- cancelled task retention metrics
- scheduled executor metrics beginner
symptoms:
- getQueue.size를 runnable backlog와 동일시해 future deadline task, cancelled retained entry, active worker를 구분하지 못한다
- getActiveCount와 getCompletedTaskCount를 queue cleanup metric으로 잘못 읽어 실행 중 work와 완료된 execution count를 섞는다
- cancel이 많은 timeout workload에서 queue size는 큰데 completed count가 평평한 상황을 CPU backlog로 오진한다
intents:
- symptom
- troubleshooting
prerequisites:
- data-structure/scheduledexecutorservice-vs-delayqueue-bridge
- data-structure/scheduledfuture-cancel-stale-entries
next_docs:
- data-structure/delayqueue-queue-size-vs-live-timers-primer
- data-structure/cancelled-task-cleanup-purge-vs-removeoncancelpolicy
- data-structure/periodic-scheduling-drift-vs-backlog-primer
linked_paths:
- contents/data-structure/scheduledexecutorservice-vs-delayqueue-bridge.md
- contents/data-structure/scheduledfuture-cancel-stale-entries.md
- contents/data-structure/delayqueue-queue-size-vs-live-timers-primer.md
- contents/data-structure/cancelled-task-cleanup-purge-vs-removeoncancelpolicy-primer.md
- contents/data-structure/periodic-task-cancellation-bridge.md
- contents/data-structure/delayqueue-remove-cost-primer.md
- contents/spring/spring-taskexecutor-taskscheduler-overload-rejection-semantics.md
confusable_with:
- data-structure/delayqueue-queue-size-vs-live-timers-primer
- data-structure/scheduledfuture-cancel-stale-entries
- data-structure/periodic-scheduling-drift-vs-backlog-primer
- spring/taskexecutor-taskscheduler-overload-rejection-semantics
forbidden_neighbors: []
expected_queries:
- ScheduledThreadPoolExecutor getQueue size가 큰데 실제 backlog인지 cancelled retention인지 어떻게 구분해?
- getQueue size activeCount completedTaskCount를 각각 어떻게 해석해야 해?
- cancel된 scheduled task가 많을 때 queue size와 completed count가 왜 같이 움직이지 않아?
- scheduled executor metrics에서 queue entries와 live runnable work를 구분하는 방법은?
- ScheduledThreadPoolExecutor 관측성에서 queue size만 보면 안 되는 이유를 알려줘
contextual_chunk_prefix: |
  이 문서는 ScheduledThreadPoolExecutor 관측 지표를 queue entries, active workers,
  completed executions, live scheduled work로 분리한다. cancelled delayed task retention과
  future deadline entry 때문에 queue size가 runnable backlog와 다를 수 있음을 설명한다.
---
# ScheduledThreadPoolExecutor Queue Observability Primer

> 한 줄 요약: cancelled delayed task가 stale entry로 남을 수 있는 `ScheduledThreadPoolExecutor`에서는 `getQueue().size()`, `getActiveCount()`, `getCompletedTaskCount()`가 각각 "상자 안 흔적", "지금 손에 든 일", "끝난 실행 횟수"를 뜻하므로 한 숫자로 backlog를 단정하면 안 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)
- [ScheduledFuture Cancellation Bridge](./scheduledfuture-cancel-stale-entries.md)
- [DelayQueue Queue Size vs Live Timers Primer](./delayqueue-queue-size-vs-live-timers-primer.md)
- [Cancelled Task Cleanup: `purge()` vs `removeOnCancelPolicy`](./cancelled-task-cleanup-purge-vs-removeoncancelpolicy-primer.md)
- [Periodic Task Cancellation Bridge](./periodic-task-cancellation-bridge.md)
- [DelayQueue Remove Cost Primer](./delayqueue-remove-cost-primer.md)
- [Spring TaskExecutor / TaskScheduler Overload & Rejection Semantics](../spring/spring-taskexecutor-taskscheduler-overload-rejection-semantics.md)

retrieval-anchor-keywords: scheduledthreadpoolexecutor queue observability, scheduled executor queue size vs active count, queue size vs completed task count, getqueue size cancelled task retention, completed task count meaning, active count vs completed task count, scheduled executor queue size not backlog, cancel true queue size same completed count flat, scheduled executor observability basics, getqueue 해석, queue size와 실제 작업 수 차이, completed task count 해석, 취소된 task retention, 스케줄드스레드풀익스큐터 관측성, 처음 배우는 scheduled executor metrics

## 먼저 멘탈모델 하나만

`ScheduledThreadPoolExecutor`를 "알람표를 보관하는 상자 + 시간이 되면 꺼내 실행하는 직원들"로 생각하면 쉽다.

- `getQueue()`는 상자 안 종이들을 보여 준다.
- worker thread는 이미 손에 들고 실행 중인 일을 처리한다.
- `getCompletedTaskCount()`는 이미 끝내고 내려놓은 일의 누적 횟수에 가깝다.
- 취소된 종이가 상자 안에 잠시 남아 있을 수도 있다.

그래서 아래 네 숫자는 서로 다를 수 있다.

```text
queue entries != live runnable work != active workers != completed executions
```

초보자용 핵심 문장은 이것이다.

> `getQueue().size()`는 "상자 안에 남아 있는 scheduled entry 수"이고, `getActiveCount()`는 "지금 실행 중인 수", `getCompletedTaskCount()`는 "이미 끝난 실행 수"다.

## `getQueue()`를 보면 정확히 무엇을 보나

`ScheduledThreadPoolExecutor`의 `getQueue()`는 내부 delayed work queue를 `BlockingQueue<Runnable>` 모습으로 보여 준다.

초보자에게 중요한 해석은 구현 클래스 이름보다 아래 두 가지다.

1. queue 원소는 보통 **원래 넣은 `Runnable` 자체**가 아니라 scheduled wrapper다.
2. 이 queue는 **아직 worker가 꺼내지 않은 task entry들**을 담는다.

즉 `getQueue()`로 바로 알기 쉬운 것은 "대기 중인 흔적이 얼마나 남았나"이고,
바로 알기 어려운 것은 "지금 실제로 몇 개가 유효하게 실행될 예정인가"다.

## 가장 먼저 분리할 다섯 숫자

| 보고 싶은 값 | 초보자용 의미 | `getQueue().size()`와 같은가 |
|---|---|---|
| queue entries | queue 안에 물리적으로 남아 있는 entry 수 | 예 |
| active workers | 지금 실제로 thread가 잡고 실행 중인 task 수 | 아니다 |
| completed executions | 이미 끝난 task 실행 횟수 누적치 | 아니다 |
| live scheduled work | 아직 유효하고 앞으로 실행될 예정인 task 수 | 아니다 |
| ready-to-run delayed tasks | delay가 끝나 worker만 기다리는 task 수 | 아니다 |

이 표를 먼저 머리에 넣으면 `size()`를 과하게 해석하는 실수를 줄일 수 있다.

특히 `completed executions`는 **"queue에서 사라진 흔적 수"**가 아니다.

- 정상 실행을 마친 task는 completed count를 올린다.
- 실행 전에 `cancel()`된 delayed task는 completed count를 올리지 않을 수 있다.
- 그래서 cancelled stale entry가 남아 있으면 `queue.size()`는 큰데 `completedTaskCount`는 거의 안 오르는 장면이 가능하다.

## 왜 queue size가 live runnable work와 어긋나나

| 원인 | 무슨 일이 생기나 | 관측상 보이는 현상 |
|---|---|---|
| 아직 미래 deadline | task는 queue 안에 있지만 아직 runnable이 아니다 | `size()`는 큰데 실제 실행은 적다 |
| cancelled-task retention | `cancel()` 뒤에도 entry가 잠시 남을 수 있다 | `size()`가 바로 안 줄 수 있다 |
| periodic/re-enqueue 흐름 | 반복 task의 다음 차례가 다시 queue에 들어간다 | queue에는 미래 실행 한 장이 보일 수 있다 |
| active execution은 queue 밖 | worker가 이미 꺼낸 task는 queue에 없다 | 바쁜데도 `size()`는 0일 수 있다 |
| remove 정책 차이 | eager cleanup vs lazy cleanup이 다르다 | 같은 workload도 size 곡선이 달라진다 |

즉 `queue.size()`는 "현재 runnable backlog"보다 **보관량 + retention + 미래 예약량**에 더 가깝다.

## `completedTaskCount`는 무엇을 세나

초보자에게는 이 문장 하나가 가장 중요하다.

> `getCompletedTaskCount()`는 "실행이 끝난 횟수"를 세는 쪽이지, "queue에서 흔적이 사라진 횟수"를 세는 것이 아니다.

cancelled delayed task가 stale entry로 queue 안에 남아 있어도, 그 task가 실제로 실행되지 않았다면 completed count는 같이 늘지 않을 수 있다.

| 관측값 | 더 안전한 beginner 해석 |
|---|---|
| `getCompletedTaskCount()`가 오른다 | worker가 실제 실행을 끝낸 task가 있었다 |
| `getCompletedTaskCount()`가 그대로다 | 실행 완료가 거의 없었다. cancelled cleanup과는 별개다 |
| `getQueue().size()`는 큰데 completed count는 평평하다 | 미래 예약이 많거나 cancelled stale entry가 쌓였을 수 있다 |
| completed count는 오르는데 queue size도 계속 크다 | 실행도 계속 있지만 새 예약 유입이나 반복 예약도 계속 있다 |

즉 `completedTaskCount`는 cleanup metric보다는 **실행 throughput 힌트**로 읽는 편이 맞다.

## 가장 흔한 오해 세 가지

### 1. `queue.size()`가 크면 바로 backlog다

아니다. 큰 이유가 셋 중 하나일 수 있다.

- 미래 시각 task가 많다
- 취소된 entry가 남아 있다
- 진짜 ready task가 밀렸다

이 셋은 운영 의미가 다르다.

### 2. `cancel()`이 성공하면 size도 즉시 줄어야 한다

아니다. `cancel()` 성공은 우선 **future 상태 전환 성공**이다.
queue에서 언제 물리적으로 사라질지는 `removeOnCancelPolicy`, `purge()`, 만료 시점 skip 같은 cleanup 흐름에 달려 있다.

### 3. worker가 바쁘면 queue도 항상 커야 한다

아니다. 이미 worker가 꺼내 간 task는 queue 밖에 있다.

```text
pool size = 4
active threads = 4
queue size = 0
```

이 상태는 충분히 가능하다.
"바쁘다"는 active count에 더 가깝고, "쌓였다"는 queue metrics에 더 가깝다.

### 4. completed count가 안 오르면 queue 정리가 안 됐다는 뜻이다

아니다. completed count는 "실행 완료 수"를 보는 값이다.

- 취소된 delayed task는 실행되지 않고 stale entry로 남을 수 있다.
- 이 경우 queue size는 크지만 completed count는 그대로일 수 있다.
- 반대로 completed count가 올라도 미래 예약 유입이 계속되면 queue size는 여전히 클 수 있다.

## 짧은 예시 1: long-delay timeout이 많은 서비스

```java
ScheduledThreadPoolExecutor scheduler =
    new ScheduledThreadPoolExecutor(4);

scheduler.schedule(taskA, 10, TimeUnit.MINUTES);
scheduler.schedule(taskB, 12, TimeUnit.MINUTES);
scheduler.schedule(taskC, 15, TimeUnit.MINUTES);
```

직후에는 이렇다.

| metric | 값 예시 | 해석 |
|---|---:|---|
| `getQueue().size()` | 3 | 대기 entry 3개 |
| active workers | 0 | 아직 실행 중인 worker 일 없음 |
| ready-to-run tasks | 0 | 아직 deadline이 안 됨 |

즉 `size() = 3`이지만 live runnable work는 `0`에 가깝다.

## 짧은 예시 2: cancel이 많은 timeout workload

```text
t=0s   1분 뒤 timeout 100개 예약
t=1s   95개 요청이 성공해서 timeout 95개 cancel
t=1s   removeOnCancelPolicy(false)
```

이때 충분히 이런 숫자가 나올 수 있다.

| metric | 값 예시 | 해석 |
|---|---:|---|
| `getQueue().size()` | 100 | queue 안 흔적은 아직 100장일 수 있다 |
| `getActiveCount()` | 0 | 지금 당장 실행 중인 timeout 작업은 없을 수 있다 |
| `getCompletedTaskCount()` | 0 | 취소돼서 실행 완료된 timeout은 거의 없을 수 있다 |
| live timeouts | 5 | 실제로 아직 필요한 timeout |
| cancelled retained | 95 | 실행되면 안 되지만 남아 있는 entry |

운영자가 `size() = 100`만 보고 "실행 backlog 100"이라고 읽으면 틀릴 수 있다.
실제로는 **cancelled-task retention 95 + live 5**일 수 있다.
이때 `activeCount`와 `completedTaskCount`가 낮다면, "지금 CPU가 바쁘다"보다 "취소된 흔적이 상자에 남아 있다" 쪽이 더 맞는 해석이다.

## 짧은 예시 3: queue size는 0인데 시스템은 바쁠 수 있다

가정:

- core pool size는 2
- delay가 끝난 task 2개를 worker가 막 꺼내 갔다
- 추가로 기다리는 task는 없다

그러면 아래처럼 보일 수 있다.

| metric | 값 예시 |
|---|---:|
| `getQueue().size()` | 0 |
| `getActiveCount()` | 2 |
| `getCompletedTaskCount()` | 직전까지 꾸준히 증가 중일 수 있음 |
| CPU 사용률 | 높음 |

즉 "queue가 비었다"는 "한가하다"와 같은 문장이 아니다.

## 세 숫자를 같이 읽는 빠른 표

| `getQueue().size()` | `getActiveCount()` | `getCompletedTaskCount()` | 먼저 붙일 해석 |
|---:|---:|---:|---|
| 높음 | 낮음 | 평평함 | 미래 예약이 많거나 cancelled stale entry retention 가능성 |
| 낮음 | 높음 | 증가 중 | queue는 길지 않지만 worker는 지금 바쁘다 |
| 높음 | 높음 | 증가 중 | 유입도 많고 실행도 많다. 진짜 압박 가능성 |
| 높음 | 낮음 | 증가 중 | 반복 예약 또는 장기 예약이 많아 보관량이 큰 상태일 수 있다 |
| 낮음 | 낮음 | 평평함 | 거의 idle이거나 아직 deadline이 멀다 |

이 표는 "어느 숫자가 backlog의 정답인가?"를 묻기보다,
"세 숫자가 서로 다른 층을 보고 있다"는 감각을 고정하는 용도다.

## 초보자용 선택표: 무엇을 알고 싶은가

| 내가 알고 싶은 질문 | 먼저 볼 값 | `getQueue()`만으로 부족한 이유 |
|---|---|---|
| 지금 thread들이 바쁜가 | `getActiveCount()` | active work는 queue 밖에 있다 |
| 실제 실행이 끝나고 있나 | `getCompletedTaskCount()` 추이 | cleanup과 실행 완료는 다른 사건이다 |
| 미래 예약이 많이 쌓였나 | `getQueue().size()` | 이 질문에는 오히려 유용하다 |
| 실제 runnable backlog가 있나 | ready count, lag, execution delay | 미래 예약과 cancelled entry를 빼야 한다 |
| cancel retention이 큰가 | cancelled/stale 추정치, cleanup 정책 | size 하나로는 원인 분리가 안 된다 |
| 설정 변경 효과가 있었나 | `size()` 추이 + cancel rate + lag | size만 보면 착시가 남는다 |

짧게 외우면 이렇게 정리된다.

```text
queue.size()     -> 상자 안 종이 수
activeCount      -> 지금 손에 들고 일하는 worker 수
completedCount   -> 이미 끝낸 실행 횟수
live/ready count -> 실제 유효 예정 작업 또는 즉시 실행 대기량
```

## `removeOnCancelPolicy`가 그래프를 어떻게 바꾸나

| 설정 | 취소 직후 queue에 남는 감각 | 대시보드에서 흔한 체감 |
|---|---|---|
| `false` | cancelled entry가 한동안 남을 수 있다 | queue size가 천천히 내려간다 |
| `true` | cancel path에서 제거를 더 적극적으로 시도한다 | queue size가 live 수에 더 가까워진다 |

그래서 `removeOnCancelPolicy(true)`를 켠 뒤 queue size가 내려갔다면,
반드시 "트래픽이 줄었다"가 아니라 **retention 해석이 달라졌다**일 수도 있다.

## beginner용 관측 순서

1. `getQueue().size()`를 보고 "대기 entry 보관량"이라고 먼저 말한다.
2. `getActiveCount()`로 현재 실행 중인 worker 수를 분리한다.
3. `getCompletedTaskCount()` 추이로 실제 실행 완료가 일어나고 있는지 본다.
4. cancel 비율이 높다면 cancelled retention 가능성을 먼저 의심한다.
5. task 실행 지연이나 만료 후 lag를 같이 봐서 진짜 backlog인지 확인한다.

이 순서를 지키면 `size()` 하나로 과잉 진단하는 실수를 줄이기 쉽다.

## 모니터링 예시

| metric 이름 예시 | 왜 보나 |
|---|---|
| `scheduled_queue_entries` | queue에 남은 전체 entry 수 |
| `scheduled_active_workers` | 지금 실행 중인 worker 수 |
| `scheduled_completed_total` | 실제 실행 완료 throughput 추이 |
| `scheduled_cancel_total` | 취소 churn 규모 |
| `scheduled_cancelled_retained_estimate` | queue에 남은 stale/cancelled 규모 추정 |
| `scheduled_ready_lag_ms` | 시간이 된 task가 얼마나 늦게 실행되는지 |

이 조합이면 아래 구분이 쉬워진다.

- `entries`만 크고 `active`와 `completed` 증가율, `lag`는 낮다: 미래 예약 또는 retention 가능성
- `entries`는 낮은데 `active`는 높고 `completed`도 오른다: 지금 worker는 바쁘지만 backlog는 길지 않을 수 있음
- `entries`와 `lag`가 함께 높고 `completed` 증가율은 낮다: 실제 ready backlog 가능성
- `cancel_total`이 높고 `entries`가 잘 안 내려간다: lazy cancellation 영향 가능성

## `getQueue()`를 직접 순회할 때 조심할 점

초보자는 `getQueue()`가 "내가 넣은 business task 목록"이라고 생각하기 쉽다.
하지만 실제로는 scheduled wrapper, future state, delay 상태가 섞여 있다.

그래서 아래처럼 보는 편이 안전하다.

| 하고 싶은 일 | beginner용 권장 해석 |
|---|---|
| queue size 확인 | 가능 |
| 단순 샘플 관찰 | 가능하지만 wrapper 중심으로 보게 된다 |
| "이게 진짜 몇 개 실행될 예정인가" 계산 | 그대로 믿기 어렵다 |
| cancelled retention 판단 | state/cleanup 정책과 같이 읽어야 한다 |

즉 `getQueue()`는 디버깅 힌트로는 좋지만,
그 자체가 "실행 예정 진실의 원장"은 아니다.

## 자주 쓰는 한 줄 판단

| 관측된 현상 | 먼저 붙일 문장 |
|---|---|
| `queue.size()`만 높다 | "상자 안 종이가 많다" |
| `activeCount`만 높다 | "지금 worker가 바쁘다" |
| `completedTaskCount`만 오른다 | "실행은 끝나고 있다" |
| `queue.size()` 높고 cancel churn 높다 | "retention일 수 있다" |
| `queue.size()` 높고 `completedTaskCount`는 평평하다 | "취소 잔류나 미래 예약을 먼저 의심한다" |
| `queue.size()` 높고 lag도 높다 | "진짜 backlog일 수 있다" |
| `queue.size()` 0인데 CPU 높다 | "이미 worker가 task를 꺼내 실행 중일 수 있다" |

## 다음 문서로 이어가기

- `cancel()` 성공과 queue 잔류가 왜 동시에 가능하나부터 보려면 [ScheduledFuture Cancellation Bridge](./scheduledfuture-cancel-stale-entries.md)
- `queue.size()`가 live timer 수와 왜 어긋나는지 더 자료구조 쪽으로 보려면 [DelayQueue Queue Size vs Live Timers Primer](./delayqueue-queue-size-vs-live-timers-primer.md)
- `removeOnCancelPolicy(true)`와 `purge()`의 차이를 보려면 [Cancelled Task Cleanup: `purge()` vs `removeOnCancelPolicy`](./cancelled-task-cleanup-purge-vs-removeoncancelpolicy-primer.md)
- scheduled executor 아래의 delay-aware queue 멘탈모델부터 다시 잡으려면 [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)

## 한 줄 정리

`ScheduledThreadPoolExecutor`에서 cancelled delayed task가 stale entry로 남을 수 있으면, `getQueue().size()`는 보관 흔적, `getActiveCount()`는 현재 실행, `getCompletedTaskCount()`는 끝난 실행을 뜻하므로 세 값을 함께 읽어야 실제 backlog와 retention을 구분할 수 있다.
