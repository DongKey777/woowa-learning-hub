# Fixed Rate vs Fixed Delay Overrun Primer

> 한 줄 요약: 같은 timer queue mental model로 보면 `scheduleAtFixedRate`는 overrun 뒤에도 원래 박자 deadline을 따라가려 해서 **끝나자마자 다시 실행될 수 있고**, `scheduleWithFixedDelay`는 방금 끝난 시각에서 다시 ticket을 찍어서 **항상 delay만큼 쉰다**.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../algorithm/backend-algorithm-starter-pack.md)


retrieval-anchor-keywords: fixed rate vs fixed delay overrun primer basics, fixed rate vs fixed delay overrun primer beginner, fixed rate vs fixed delay overrun primer intro, data structure basics, beginner data structure, 처음 배우는데 fixed rate vs fixed delay overrun primer, fixed rate vs fixed delay overrun primer 입문, fixed rate vs fixed delay overrun primer 기초, what is fixed rate vs fixed delay overrun primer, how to fixed rate vs fixed delay overrun primer
> 관련 문서:
> - [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)
> - [Periodic Task Cancellation Bridge](./periodic-task-cancellation-bridge.md)
> - [Slow Periodic Task Primer](./slow-periodic-task-primer.md)
> - [Periodic Scheduling Drift vs Backlog Primer](./periodic-scheduling-drift-vs-backlog-primer.md)
> - [Periodic Overrun Catch-Up Primer](./periodic-overrun-catch-up-primer.md)
> - [DelayQueue Repeating Task Primer](./delayqueue-repeating-task-primer.md)
> - [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
>
> retrieval-anchor-keywords: fixed rate vs fixed delay overrun primer, scheduleAtFixedRate vs scheduleWithFixedDelay overrun, fixed rate overrun beginner, fixed delay overrun beginner, periodic task runtime longer than interval, task takes longer than period java, scheduledexecutorservice overrun primer, timer queue mental model fixed rate fixed delay, deadline ticket overrun, overdue deadline debt, fixed rate catch up, fixed delay breathing room, why scheduleAtFixedRate runs immediately, why scheduleWithFixedDelay waits, fixed rate vs fixed delay runtime exceeds interval, periodic overrun catch up, catch-up drift skip coalesce, 주기보다 실행 시간이 긴 작업, fixed-rate vs fixed-delay 오버런, scheduleAtFixedRate scheduleWithFixedDelay 차이, 타이머 큐 멘탈모델, deadline ticket, catch-up 실행, drift backlog beginner

## 먼저 멘탈모델 하나만

초보자에게는 반복 작업을 "계속 살아 있는 스레드"보다 이렇게 보는 편이 쉽다.

> timer queue 안에는 "이 작업의 다음 실행 deadline ticket 한 장"만 들어 있다.

worker가 ticket을 꺼내 실행하고 나면, scheduler가 다음 ticket을 다시 넣는다.
핵심 질문은 하나다.

> 이번 실행이 끝났을 때, 다음 ticket deadline이 이미 과거인가 미래인가?

- 과거면: worker는 거의 바로 다음 실행을 시작할 수 있다.
- 미래면: 그 시각까지 기다린다.

이 질문 하나로 `fixed-rate`와 `fixed-delay`가 갈린다.

## 한눈에 보는 차이

가정:

- interval은 `5초`
- 실제 실행 시간은 `12초`
- worker는 1개

| 방식 | 다음 ticket 기준 | 실행이 interval을 넘겼을 때 보이는 것 |
|---|---|---|
| `scheduleAtFixedRate` | 이전 예정 시각 + 5초 | 다음 deadline이 이미 과거라서 끝나자마자 다시 돌기 쉽다 |
| `scheduleWithFixedDelay` | 이번 실행 종료 시각 + 5초 | 항상 5초 쉬고 다시 돈다 |

초보자용으로는 이렇게만 잡아도 된다.

- `fixed-rate`: 원래 박자를 따라가려는 쪽
- `fixed-delay`: 실행 사이 쉬는 간격을 지키는 쪽

## 같은 작업을 두 timeline으로 보기

### `scheduleAtFixedRate`

첫 실행 예정 시각을 `t=0`으로 두자.

| 시각 | queue / worker에서 보이는 일 |
|---|---|
| `t=0` | 1회차 시작 |
| `t=12` | 1회차 종료 |
| `t=12` | 원래 다음 deadline은 `t=5`, 그다음은 `t=10`이었다 |
| `t=12` | 다음 ticket이 이미 overdue 상태라 거의 바로 2회차가 가능하다 |
| `t=24` | 2회차 종료. 원래 `t=15`, `t=20` 박자도 이미 지나 있다 |

```text
fixed-rate, runtime=12s, interval=5s

planned deadline: 0 --- 5 --- 10 --- 15 --- 20 --- 25
actual start:     0 ----------- 12 ----------- 24
actual finish:         12            24            36
```

queue 관점에서는 "놓친 박자 debt"가 계속 남는다.
그래서 worker는 쉬기보다 **밀린 박자를 따라잡으려는 모습**을 보인다.

### `scheduleWithFixedDelay`

같은 조건에서 `fixed-delay`를 보자.

| 시각 | queue / worker에서 보이는 일 |
|---|---|
| `t=0` | 1회차 시작 |
| `t=12` | 1회차 종료 |
| `t=12` | 다음 ticket을 `t=17`로 새로 찍는다 |
| `t=17` | 2회차 시작 |
| `t=29` | 2회차 종료 |
| `t=29` | 다음 ticket을 `t=34`로 찍는다 |

```text
fixed-delay, runtime=12s, delay=5s

start:   0 ----------- 17 ----------- 34
finish:      12            29            46
rest:        [5s]          [5s]
```

이쪽은 overdue deadline debt를 들고 가지 않는다.
매번 **"지금 끝난 시각 + delay"** 로 새 출발한다.

## 왜 갈리는지, 식 하나로 보기

둘 다 반복 실행 뒤에 다음 ticket을 다시 넣는다.
차이는 timestamp를 어디에 찍느냐뿐이다.

| 방식 | 다음 ticket 계산식 | overrun 때 느낌 |
|---|---|---|
| `fixed-rate` | `next = previousPlannedTime + period` | 이미 늦은 deadline이 남아 catch-up 압박이 생김 |
| `fixed-delay` | `next = finishedAt + delay` | 항상 종료 후 숨 고를 시간 보장 |

즉 "실행이 느릴 때 특별 규칙이 추가된다"가 아니다.
원래 재등록 규칙이 overrun 상황에서 더 또렷하게 보일 뿐이다.

## 선택표

| 질문 | 먼저 떠올릴 쪽 | 이유 |
|---|---|---|
| "매 분 0초처럼 원래 박자가 중요하다" | `scheduleAtFixedRate` | 원래 cadence 기준으로 다음 ticket을 잡는다 |
| "작업 사이 최소 휴식 시간이 중요하다" | `scheduleWithFixedDelay` | 종료 후 delay를 보장한다 |
| "작업이 종종 interval보다 오래 걸린다" | 기본값은 `scheduleWithFixedDelay`부터 검토 | 끝나자마자 재실행되는 압박을 줄인다 |
| "왜 한 작업이 계속 head를 차지하나?" | `fixed-rate` overdue deadline 여부 확인 | 다음 ticket이 이미 과거일 수 있다 |

## 자주 하는 오해

1. `period=5초`면 두 방식 모두 "실행 후 5초 쉰다"고 생각한다.
2. `fixed-rate` overrun이면 같은 periodic task가 여러 개 동시에 겹쳐 폭발한다고 바로 상상한다.
3. `fixed-delay`는 느린 작업을 더 빨리 따라잡는 방식이라고 생각한다.
4. timer queue 안에 같은 논리 작업이 영원히 하나만 살아 있다고 생각한다.

초보자 기준으로는 이렇게 바로잡으면 된다.

- `fixed-rate`: "원래 시작했어야 할 시각"을 기억한다.
- `fixed-delay`: "방금 끝난 뒤 얼마를 쉴지"를 기억한다.

## 다음 문서로 이어가기

- 같은 멘탈모델을 더 짧은 느린 작업 예시로 보고 싶다면 [Slow Periodic Task Primer](./slow-periodic-task-primer.md)
- catch-up, drift, skip, coalesce를 한 표로 고르고 싶다면 [Periodic Overrun Catch-Up Primer](./periodic-overrun-catch-up-primer.md)
- drift와 backlog를 같은 그림에서 비교하고 싶다면 [Periodic Scheduling Drift vs Backlog Primer](./periodic-scheduling-drift-vs-backlog-primer.md)
- scheduled executor 자체를 deadline ticket queue로 이해하고 싶다면 [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)
- 반복 작업이 실제로 "다음 ticket 재등록"으로 구현되는 감각을 보고 싶다면 [DelayQueue Repeating Task Primer](./delayqueue-repeating-task-primer.md)

## 한 줄 정리

overrun 상황에서 `scheduleAtFixedRate`와 `scheduleWithFixedDelay`의 차이는 결국 "다음 deadline ticket을 원래 박자에 찍느냐, 방금 끝난 시각에 찍느냐"다. 그래서 전자는 끝나자마자 다시 돌 수 있고, 후자는 항상 한 번 쉰다.
