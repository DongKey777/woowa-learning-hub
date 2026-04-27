# DelayQueue Repeating Task Primer

> 한 줄 요약: `DelayQueue`의 반복 작업은 "영원히 도는 하나의 queue 원소"가 아니라 **실행이 끝날 때마다 다음 deadline ticket을 다시 넣는 흐름**이고, `fixed rate`는 이전 예정 시각 기준, `fixed delay`는 실행 종료 시각 기준으로 다음 ticket을 잡는다. 그래서 cancel/reschedule이 끼면 오래된 ticket을 stale로 버리는 최신성 검사가 필요하다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../algorithm/backend-algorithm-starter-pack.md)


retrieval-anchor-keywords: delayqueue repeating task primer basics, delayqueue repeating task primer beginner, delayqueue repeating task primer intro, data structure basics, beginner data structure, 처음 배우는데 delayqueue repeating task primer, delayqueue repeating task primer 입문, delayqueue repeating task primer 기초, what is delayqueue repeating task primer, how to delayqueue repeating task primer
> 관련 문서:
> - [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)
> - [Java Timer Clock Choice Primer](./java-timer-clock-choice-primer.md)
> - [DelayQueue Delayed Contract Primer](./delayqueue-delayed-contract-primer.md)
> - [ScheduledFuture Cancellation Bridge](./scheduledfuture-cancel-stale-entries.md)
> - [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md)
> - [DelayQueue vs PriorityQueue Timer Pitfalls](./delayqueue-vs-priorityqueue-timer-pitfalls.md)
>
> retrieval-anchor-keywords: delayqueue repeating task, delayqueue periodic task, delayqueue repeating job, delayqueue self rescheduling job, self-rescheduling delayqueue, self rescheduling timer job, fixed rate vs fixed delay delayqueue, delayqueue fixed rate, delayqueue fixed delay, scheduleAtFixedRate scheduleWithFixedDelay delayqueue mental model, periodic re-enqueue delayqueue, repeating timer ticket, repeating scheduler ticket, stale ticket bug, stale periodic ticket, reschedule stale ticket, latest generation repeating job, generation check repeating timer, delayqueue beginner repeating primer, periodic scheduler beginner, repeating task requeue, job state vs queue ticket, fixed rate timeline, fixed delay timeline, stale self reschedule bug, 반복 작업 delayqueue, fixed rate fixed delay 차이, stale ticket 버그, 재등록 타이머

## 먼저 그림부터

`DelayQueue`의 반복 작업은 "queue 안에 같은 작업이 계속 살아 있다"보다
"worker가 ticket 하나를 꺼내 실행한 뒤, **다음 차례 ticket을 새로 넣는다**"로 이해하는 편이 쉽다.

| 눈에 보이는 것 | 실제로 queue에 들어 있는 것 |
|---|---|
| "5초마다 실행되는 작업 A" | 지금 시점에서 **다음 한 번** 실행할 ticket |
| worker가 한 번 실행함 | 그 ticket 하나를 소비함 |
| 반복 실행 계속됨 | 다음 deadline의 새 ticket을 다시 `offer()`함 |

핵심은 이것이다.

> `DelayQueue`는 "논리 작업 A"를 보관하지 않고, "A의 다음 실행 시각 스냅샷"인 ticket을 보관한다.

이 문장 하나를 잡고 가면 fixed-rate / fixed-delay 차이와 stale-ticket 버그가 같이 보인다.

## 1. fixed-rate와 fixed-delay는 "다음 ticket을 어느 시각으로 찍나"의 차이다

둘 다 worker가 실행을 끝낸 뒤 다음 ticket을 다시 넣는다.
차이는 **다음 deadline 계산 기준**이다.

| 방식 | 다음 deadline 기준 | 초보자용 감각 |
|---|---|---|
| `fixed rate` | 이전 예정 시각 + period | 원래 박자표를 유지하려고 함 |
| `fixed delay` | 이번 실행 종료 시각 + delay | 이번 실행 뒤 쉬는 간격을 유지하려고 함 |

같은 반복 작업이라도 "다음 ticket을 언제로 찍느냐"가 다르다고 보면 된다.

## 2. 짧은 timeline으로 보면 바로 갈린다

가정은 단순하게 두자.

- 첫 실행 ticket은 `t=10`
- 간격은 `10초`
- 매 실행은 `3초` 걸린다
- worker는 1개다

### fixed rate

| 시각 | queue / worker에서 보이는 일 |
|---|---|
| `t=0` | `ticket@10`이 queue에 들어간다 |
| `t=10` | worker가 `ticket@10`을 꺼내 실행한다 |
| `t=13` | 실행이 끝난다. 다음 ticket을 `@20`으로 다시 넣는다 |
| `t=20` | worker가 다음 실행을 시작한다 |

```text
fixed rate
time:    0 -------- 10 --- 13 ------- 20
queue:   ticket@10      ticket@20
worker:            run1
```

### fixed delay

| 시각 | queue / worker에서 보이는 일 |
|---|---|
| `t=0` | `ticket@10`이 queue에 들어간다 |
| `t=10` | worker가 `ticket@10`을 꺼내 실행한다 |
| `t=13` | 실행이 끝난다. 다음 ticket을 `@23`으로 다시 넣는다 |
| `t=23` | worker가 다음 실행을 시작한다 |

```text
fixed delay
time:    0 -------- 10 --- 13 ---------- 23
queue:   ticket@10      ticket@23
worker:            run1
```

같은 작업이라도 fixed-rate는 `10, 20, 30...`처럼 원래 리듬을 기억하고,
fixed-delay는 `10, 23, 36...`처럼 실행 시간만큼 뒤로 밀린다.

## 3. stale-ticket bug는 "같은 논리 작업의 오래된 snapshot"이 남을 때 생긴다

여기서 초보자가 자주 놓치는 점은 `DelayQueue`가 **논리 작업 하나당 ticket 하나만 강제하지 않는다**는 것이다.

즉 같은 작업 A에 대해 아래 둘이 동시에 존재할 수 있다.

- 예전 설정으로 만든 오래된 ticket
- 새 설정으로 만든 최신 ticket

queue 입장에서는 둘 다 그냥 deadline이 붙은 원소일 뿐이다.

## 4. self-rescheduling job에서 버그가 생기는 순간

가장 흔한 사고는 "실행이 끝나면 무조건 다음 ticket을 다시 넣는 코드"가
중간의 cancel/reschedule을 모르고 움직일 때다.

예를 들어 처음에는 fixed-rate 10초 작업이었다고 하자.

| 시각 | 무슨 일이 생기나 |
|---|---|
| `t=0` | 작업 A를 `fixed-rate`, `period=10초`로 등록한다. queue에는 `A#g1@10`이 있다 |
| `t=10` | worker가 `A#g1@10`을 꺼내 실행을 시작한다 |
| `t=12` | 운영자가 설정을 바꿔 `fixed-delay`, `delay=30초`로 다시 등록한다. 새 ticket `A#g2@42`가 들어간다 |
| `t=13` | **오래된 실행 코드가** "나는 fixed-rate 작업이었지"라고 생각하고 `A#g1@20`을 다시 넣는다 |
| `t=20` | queue에는 `A#g1@20`과 `A#g2@42`가 함께 있고, 오래된 `A#g1@20`이 먼저 실행된다 |

이게 stale-ticket bug다.

- 사람 의도: "이제부터는 fixed-delay 30초 정책만 살아 있어야 한다"
- queue 현실: 예전 fixed-rate 정책의 ticket도 남아 있어서 한 번 더 실행된다

즉 버그 위치는 `take()` 자체가 아니라 **실행 후 다시 넣는 순간**이다.

### 같은 류의 버그가 자주 생기는 지점

| 상황 | 오래된 ticket이 남는 이유 |
|---|---|
| 실행 중에 `cancel()`했다 | 실행이 끝난 코드가 취소 사실을 다시 확인하지 않고 재등록한다 |
| 실행 중에 period/delay를 바꿨다 | 기존 실행 흐름이 옛 설정으로 다음 ticket을 다시 만든다 |
| retry/backoff 로직이 따로 다음 ticket을 넣는다 | periodic 재등록과 retry 재등록이 겹쳐 두 장의 ticket이 공존한다 |
| queue 크기만 보고 "활성 작업 수"라고 생각한다 | stale ticket도 size에 포함될 수 있다 |

## 5. 최소 안전 패턴은 "job 상태"와 "queue ticket"을 분리하는 것이다

초보자에게 가장 안전한 패턴은 아래 둘을 분리하는 것이다.

| 구성 요소 | 역할 |
|---|---|
| `queue ticket` | 지금 시점의 다음 실행 snapshot |
| `job state` | 이 논리 작업의 최신 generation, mode, interval, active 여부 |

worker는 실행 전과 실행 후에 둘 다 확인해야 한다.

1. 꺼낸 ticket이 아직 최신 generation인지 본다.
2. 실행한다.
3. 실행 도중 cancel/reschedule이 들어왔는지 다시 본다.
4. 여전히 최신이면 그때만 다음 ticket을 다시 넣는다.

```java
while (true) {
    RepeatTicket ticket = queue.take();
    JobState beforeRun = states.get(ticket.jobId());

    if (beforeRun == null || ticket.generation() != beforeRun.generation()) {
        continue; // stale ticket
    }

    ticket.job().run();
    long finishedAt = System.nanoTime();

    JobState afterRun = states.get(ticket.jobId());
    if (afterRun == null || !afterRun.active()
            || ticket.generation() != afterRun.generation()) {
        continue; // cancelled or rescheduled while running
    }

    long nextDeadline = switch (afterRun.mode()) {
        case FIXED_RATE -> ticket.deadlineNanos() + afterRun.intervalNanos();
        case FIXED_DELAY -> finishedAt + afterRun.intervalNanos();
    };

    queue.offer(ticket.next(nextDeadline));
}
```

여기서 중요한 점은 두 가지다.

- fixed-rate / fixed-delay 차이는 `nextDeadline` 계산식에서 난다.
- stale-ticket 방지는 `generation` 재확인에서 난다.

즉 **리듬 계산**과 **최신성 검사**는 다른 문제다.

## 6. 자주 하는 오해

1. 반복 작업이면 queue 안에 같은 원소 하나가 계속 남아 있다고 생각한다.
2. fixed-rate도 "실행이 끝난 뒤 period만큼 쉰다"라고 생각한다.
3. fixed-delay도 "원래 박자표를 유지한다"라고 생각한다.
4. 실행 중 cancel/reschedule이 들어오면 실행 후 재등록도 자동으로 막힌다고 생각한다.
5. `queue.size()`가 곧 현재 살아 있는 논리 작업 수라고 생각한다.

특히 4번이 중요하다.
실행이 끝난 뒤 재등록하기 직전에 최신 상태를 다시 보지 않으면, **오래된 실행이 미래 ticket을 한 장 더 만드는 버그**가 바로 생긴다.

## 다음 문서로 이어가기

- `ScheduledExecutorService` API와 fixed-rate / fixed-delay timeline을 먼저 잡으려면 [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)
- `Delayed.compareTo()`와 `getDelay()`가 왜 같은 deadline을 봐야 하는지 보려면 [DelayQueue Delayed Contract Primer](./delayqueue-delayed-contract-primer.md)
- cancel/reschedule에서 `generation`과 lazy stale skip을 더 넓게 보려면 [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md)
- Java `ScheduledFuture.cancel()`과 `removeOnCancelPolicy`의 API 쪽 의미를 보려면 [ScheduledFuture Cancellation Bridge](./scheduledfuture-cancel-stale-entries.md)
- timer 구조 선택까지 비교하려면 [DelayQueue vs PriorityQueue Timer Pitfalls](./delayqueue-vs-priorityqueue-timer-pitfalls.md)

## 한 줄 정리

`DelayQueue` 반복 작업의 핵심은 "실행 후 다음 ticket을 어떻게 다시 찍느냐"다. `fixed-rate`는 이전 예정 시각 기준, `fixed-delay`는 실행 종료 시각 기준이고, cancel/reschedule이 끼는 순간에는 **오래된 ticket을 stale로 버리는 최신성 검사**가 없으면 self-rescheduling 버그가 난다.
