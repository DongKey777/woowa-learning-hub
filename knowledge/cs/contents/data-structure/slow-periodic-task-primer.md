---
schema_version: 3
title: Slow Periodic Task Primer
concept_id: data-structure/slow-periodic-task-primer
canonical: false
category: data-structure
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 90
mission_ids: []
review_feedback_tags:
- slow-periodic-task
- fixed-rate-vs-fixed-delay
- scheduled-executor-overrun
aliases:
- slow periodic task
- fixed-rate vs fixed-delay overrun
- scheduleAtFixedRate slow task
- scheduleWithFixedDelay slow task
- task runtime longer than period
- overdue deadline
- periodic task catch up
symptoms:
- fixed-rate period를 실행 후 휴식 시간으로 오해해 runtime이 period보다 길 때 끝나자마자 재실행되는 이유를 이해하지 못한다
- fixed-delay가 이번 실행 종료 시각 기준으로 다음 deadline을 잡아 breathing room을 보장한다는 점을 놓친다
- 느린 periodic task가 겹쳐 실행되는지, overdue deadline으로 연속 실행되는지, worker starvation인지 구분하지 못한다
intents:
- definition
- troubleshooting
prerequisites:
- data-structure/timer-vocabulary-delay-timeout-deadline-dueat-bridge
- data-structure/scheduledexecutorservice-vs-delayqueue-bridge
next_docs:
- data-structure/fixed-rate-vs-fixed-delay-overrun-primer
- data-structure/periodic-scheduling-drift-vs-backlog-primer
- data-structure/ready-queue-starvation-primer
linked_paths:
- contents/data-structure/timer-vocabulary-delay-timeout-deadline-dueat-bridge.md
- contents/data-structure/scheduledexecutorservice-vs-delayqueue-bridge.md
- contents/data-structure/fixed-rate-vs-fixed-delay-overrun-primer.md
- contents/data-structure/delayqueue-repeating-task-primer.md
- contents/data-structure/periodic-scheduling-drift-vs-backlog-primer.md
- contents/data-structure/queue-vs-deque-vs-priority-queue-primer.md
- contents/data-structure/timing-wheel-vs-delay-queue.md
- contents/data-structure/ready-queue-starvation-primer.md
confusable_with:
- data-structure/fixed-rate-vs-fixed-delay-overrun-primer
- data-structure/periodic-scheduling-drift-vs-backlog-primer
- data-structure/delayqueue-repeating-task-primer
- data-structure/ready-queue-starvation-primer
forbidden_neighbors: []
expected_queries:
- task runtime이 period보다 길 때 fixed-rate는 왜 끝나자마자 다시 실행돼?
- fixed-delay는 느린 periodic task에서 왜 실행 사이에 숨 고를 시간을 보장해?
- scheduleAtFixedRate와 scheduleWithFixedDelay를 deadline ticket 관점으로 설명해줘
- 느린 scheduled task가 겹쳐 실행되는 건지 overdue deadline을 따라잡는 건지 어떻게 구분해?
- periodic overrun에서 drift backlog worker starvation을 초보자에게 설명해줘
contextual_chunk_prefix: |
  이 문서는 runtime이 period보다 긴 periodic task에서 fixed-rate와 fixed-delay를
  deadline ticket 관점으로 설명한다. overdue deadline, catch-up execution,
  breathing room, worker starvation 가능성을 beginner primer로 분리한다.
---
# Slow Periodic Task Primer

> 한 줄 요약: 주기보다 실행 시간이 더 긴 작업에서는 `fixed-rate`가 "원래 deadline 박자"를 따라잡으려 하면서 **끝나자마자 다시 실행될 수 있고**, `fixed-delay`는 "이번 실행이 끝난 뒤 쉬는 간격"을 지켜서 항상 숨 고를 틈을 만든다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../algorithm/backend-algorithm-starter-pack.md)
- [Timer Vocabulary Bridge](./timer-vocabulary-delay-timeout-deadline-dueat-bridge.md)


retrieval-anchor-keywords: fixed-rate vs fixed-delay basics, 주기보다 실행 시간이 길어요, fixed-rate 끝나자마자 다시 실행, fixed-delay 왜 쉬고 실행, scheduleatfixedrate vs schedulewithfixeddelay, periodic task overrun beginner, 처음 periodic task 헷갈려요, 느린 스케줄 작업 큰 그림, fixed-rate catch up, fixed-delay breathing room, period보다 task가 오래 걸리면, timer queue overdue deadline
> 관련 문서:
> - [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)
> - [Fixed Rate vs Fixed Delay Overrun Primer](./fixed-rate-vs-fixed-delay-overrun-primer.md)
> - [DelayQueue Repeating Task Primer](./delayqueue-repeating-task-primer.md)
> - [Periodic Scheduling Drift vs Backlog Primer](./periodic-scheduling-drift-vs-backlog-primer.md)
> - [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
> - [Timing Wheel vs Delay Queue](./timing-wheel-vs-delay-queue.md)
> - [Ready Queue Starvation Primer](./ready-queue-starvation-primer.md)
>
> retrieval-anchor-keywords: slow periodic task primer, slow scheduled task, task runtime longer than period, fixed rate longer than period, fixed delay longer than period, scheduleAtFixedRate slow task, scheduleWithFixedDelay slow task, fixed rate catch up, fixed delay breathing room, periodic task deadline intuition, overdue deadline queue, delayed work queue periodic backlog, java periodic task slow job, scheduledexecutorservice fixed rate fixed delay slow, scheduler deadline ticket intuition, queue deadline intuition, periodic task overrun beginner, fixed rate vs fixed delay overrun primer, 주기보다 긴 작업, fixed-rate 느린 작업, fixed-delay 느린 작업, 실행 시간이 period보다 김, overdue deadline, catch-up 실행, periodic overrun java

## 먼저 감각부터

반복 작업 하나를 queue 안의 "영원한 작업"으로 보면 헷갈린다.
초보자에게는 이렇게 보는 편이 쉽다.

> queue에는 "이 작업의 다음 실행 deadline ticket 한 장"만 들어 있다.

그래서 느린 주기 작업을 이해하는 질문도 결국 하나다.

> 이번 실행이 끝났을 때, 다음 ticket deadline이 이미 과거인가 미래인가?

- 이미 과거면: worker는 거의 바로 다음 실행을 잡는다.
- 아직 미래면: worker는 그 시각까지 기다린다.

이 한 문장으로 `fixed-rate`와 `fixed-delay`가 갈린다.

## 1. 느린 작업에서 진짜 차이

가정:

- period 또는 delay는 `5초`
- 실제 실행 시간은 `12초`
- worker는 1개

| 방식 | 다음 ticket 계산 기준 | 실행이 12초 걸렸을 때 보이는 현상 |
|---|---|---|
| `fixed-rate` | 이전 예정 시각 + 5초 | 다음 deadline이 이미 지나 있어서 끝나자마자 다시 실행되기 쉽다 |
| `fixed-delay` | 이번 실행 종료 시각 + 5초 | 끝난 뒤 5초 쉬고 다시 실행된다 |

핵심은 "느린 작업이라서 특별한 예외 규칙이 생긴다"가 아니다.
**다음 deadline을 어디에 찍느냐**가 그대로 드러나는 것이다.

## 2. fixed-rate: 늦었어도 원래 박자를 보려 한다

첫 실행 예정 시각을 `t=0`이라고 두자.

| 시각 | 무슨 일이 보이나 |
|---|---|
| `t=0` | 1회차 시작 |
| `t=12` | 1회차 종료. 원래 다음 deadline은 `t=5`였고 그다음은 `t=10`이었다 |
| `t=12` | 이미 `t=5`, `t=10` 박자를 놓쳤으므로 다음 실행은 곧바로 가능하다 |
| `t=12` | 2회차가 바로 시작될 수 있다 |
| `t=24` | 2회차 종료. 원래 다음 deadline은 `t=15`, `t=20`이었으므로 역시 뒤처져 있다 |

```text
fixed-rate, runtime=12s, period=5s

planned deadline: 0 --- 5 --- 10 --- 15 --- 20 --- 25
actual start:     0 ----------- 12 ----------- 24
actual finish:         12            24            36
```

여기서 초보자가 자주 오해하는 부분:

- "period가 5초니까 실행 후 5초 쉬겠지"가 아니다.
- `fixed-rate`는 실행 후 휴식 시간을 보장하지 않는다.
- 대신 "원래는 5초 간격으로 시작했어야 한다"는 박자를 기준으로 다음 deadline을 계산한다.

그래서 작업이 계속 period보다 느리면 queue 관점에서 다음 ticket deadline이 계속 과거에 머문다.
worker는 쉴 틈 없이 **지각한 버스를 연달아 보내는 느낌**으로 실행한다.

## 3. fixed-delay: 이번 실행이 끝난 뒤부터 쉰다

같은 조건에서 `fixed-delay`를 보자.

| 시각 | 무슨 일이 보이나 |
|---|---|
| `t=0` | 1회차 시작 |
| `t=12` | 1회차 종료 |
| `t=12` | 다음 deadline을 `t=17`로 새로 잡는다 |
| `t=17` | 2회차 시작 |
| `t=29` | 2회차 종료 |
| `t=29` | 다음 deadline을 `t=34`로 잡는다 |

```text
fixed-delay, runtime=12s, delay=5s

start:   0 ----------- 17 ----------- 34
finish:      12            29            46
rest:        [5s]          [5s]
```

`fixed-delay`는 "작업이 느려도 괜찮다"는 뜻은 아니다.
다만 queue에 넣는 다음 ticket이 항상 **종료 시점 이후의 미래**가 되므로, 매 실행 사이에 최소 delay만큼은 비워 둔다.

## 4. queue deadline 직관으로 다시 묶기

같은 현상을 queue head 관점으로 보면 더 단순하다.

| 질문 | `fixed-rate` | `fixed-delay` |
|---|---|---|
| 실행이 끝났을 때 다음 ticket deadline은? | 과거일 수 있음 | 항상 미래 |
| worker가 바로 다시 잡을 수 있나? | 자주 그렇다 | 아니다. 미래까지 기다린다 |
| "밀린 박자 따라잡기" 느낌이 있나? | 있다 | 없다 |
| 실행 사이 숨 고를 시간 보장? | 보장 안 함 | delay만큼 보장 |

즉 `fixed-rate`는 **deadline debt**가 쌓일 수 있고,
`fixed-delay`는 debt를 쌓기보다 "이번 실행을 기준으로 새 출발"한다.

## 5. "그럼 fixed-rate는 실행이 겹치나?"라는 질문

초보자가 많이 묻는 질문이 이것이다.

> period보다 느리면 2회차, 3회차가 동시에 겹쳐서 여러 개 실행되나?

Java `ScheduledExecutorService`의 같은 periodic task 하나에 대해서는 보통 이렇게 이해하면 된다.

- 다음 실행이 늦게 시작될 수는 있다.
- 하지만 같은 periodic task의 연속 실행이 동시에 겹쳐서 돌아가지는 않는다.
- 대신 이전 실행이 끝나자마자 다음 실행이 바로 이어질 수 있다.

즉 위험 포인트는 "동시 폭발"보다도
**queue head가 계속 overdue라서 worker가 거의 그 작업만 붙잡는 상황**에 가깝다.

## 6. 빠른 선택표

| 상황 | 더 먼저 떠올릴 선택 | 이유 |
|---|---|---|
| "매 정시, 매 분처럼 원래 박자에 의미가 크다" | `fixed-rate` | 기준 시각을 유지하려고 한다 |
| "작업 사이에 최소 휴식 간격이 꼭 필요하다" | `fixed-delay` | 종료 후 delay를 보장한다 |
| "작업이 종종 period보다 오래 걸린다" | 기본값은 `fixed-delay` 쪽을 먼저 검토 | 끝나자마자 재실행되는 압박을 줄인다 |
| "느린 periodic task가 다른 일도 막는지 걱정된다" | queue/worker 분리와 thread pool 크기 점검 | 정책보다 실행 자원 병목이 먼저일 수 있다 |

초보자 기준에서는 먼저 이렇게 잡으면 된다.

- 절대 시각 박자가 중요하면 `fixed-rate`
- 작업 사이 breathing room이 중요하면 `fixed-delay`
- 잘 모르겠고 작업 시간이 들쭉날쭉하면 `fixed-delay`를 더 안전한 출발점으로 보는 편이 많다

## 7. 자주 하는 오해

1. period가 5초면 무조건 "실행 후 5초 대기"라고 생각한다.
2. `fixed-rate`의 느린 작업은 실행이 겹친다고 바로 상상한다.
3. `fixed-delay`가 느린 작업을 더 빠르게 따라잡아 준다고 생각한다.
4. queue에는 같은 논리 작업이 추상적으로 하나만 있다고 생각한다.
5. 느린 periodic task 문제를 전부 자료구조 문제로만 보고, worker 수나 실행 시간 자체는 안 본다.

특히 1번과 2번을 같이 바로잡아 두면 좋다.

- `fixed-rate`: "period마다 시작했어야 했던 시각"을 기억
- `fixed-delay`: "이번 실행이 끝난 뒤 delay만큼 쉼"

## 다음 문서로 이어가기

- `fixed-rate`와 `fixed-delay`의 기본 재등록 공식을 먼저 보고 싶다면 [DelayQueue Repeating Task Primer](./delayqueue-repeating-task-primer.md)
- drift와 backlog를 한 그림에서 비교하고 싶다면 [Periodic Scheduling Drift vs Backlog Primer](./periodic-scheduling-drift-vs-backlog-primer.md)
- scheduled executor가 왜 "deadline ticket queue"처럼 보이는지부터 잡고 싶다면 [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)
- timer queue와 ready queue를 왜 분리해서 생각해야 하는지 이어서 보려면 [Ready Queue Starvation Primer](./ready-queue-starvation-primer.md)
- 주기 작업이 너무 많아져 자료구조 선택 자체가 고민되면 [Timing Wheel vs Delay Queue](./timing-wheel-vs-delay-queue.md)

## 한 줄 정리

주기보다 실행 시간이 더 긴 작업에서 `fixed-rate`는 "이미 늦은 deadline" 때문에 끝나자마자 다시 실행될 수 있고, `fixed-delay`는 "종료 후 새 deadline"이라 항상 한 번 숨을 고른다. queue 감각으로 보면 차이는 결국 **다음 ticket deadline이 과거인가 미래인가**다.
