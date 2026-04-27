# Periodic Scheduling Drift vs Backlog Primer

> 한 줄 요약: `scheduleAtFixedRate`는 원래 박자를 지키려다 실행이 밀리면 **overdue deadline debt**가 쌓여 끝나자마자 다시 돌기 쉽고, `scheduleWithFixedDelay`는 매번 종료 시각에서 다시 출발해서 **drift**가 커지지만 숨 고를 간격은 유지한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Slow Periodic Task Primer](./slow-periodic-task-primer.md)
- [Fixed Rate vs Fixed Delay Overrun Primer](./fixed-rate-vs-fixed-delay-overrun-primer.md)
- [Periodic Overrun Catch-Up Primer](./periodic-overrun-catch-up-primer.md)
- [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)
- [DelayQueue Repeating Task Primer](./delayqueue-repeating-task-primer.md)
- [Ready Queue Starvation Primer](./ready-queue-starvation-primer.md)
- [Spring `TaskExecutor` / `TaskScheduler` Overload, Queue, and Rejection Semantics](../spring/spring-taskexecutor-taskscheduler-overload-rejection-semantics.md)

retrieval-anchor-keywords: periodic scheduling drift vs backlog, scheduleatfixedrate vs schedulewithfixeddelay, fixed rate vs fixed delay beginner, periodic task overrun primer, scheduledexecutorservice overrun, fixed rate backlog mental model, fixed delay drift mental model, periodic rescheduling queue, overdue deadline debt, periodic catch up execution, what is scheduler drift, why fixed rate runs immediately, why fixed delay drifts, periodic task queue beginner, fixed rate vs fixed delay overrun primer

## 먼저 감각부터

초보자는 반복 작업을 "계속 살아 있는 하나의 스레드"로 상상해서 헷갈린다.
이 문서에서는 더 단순하게 이렇게 본다.

> scheduler queue에는 "이 작업의 다음 실행 ticket 한 장"이 들어 있다.

작업이 끝날 때마다 scheduler는 새 ticket을 다시 만든다.
차이는 그 ticket의 시간을 어디 기준으로 찍느냐뿐이다.

- `scheduleAtFixedRate`: 원래 박자표를 기준으로 다음 ticket을 찍는다.
- `scheduleWithFixedDelay`: 방금 끝난 시각을 기준으로 다음 ticket을 찍는다.

그래서 overrun이 생기면 결과가 갈린다.

- 원래 박자를 계속 따라가려 하면 backlog처럼 **놓친 박자 debt**가 보인다.
- 매번 종료 시각에서 다시 시작하면 실제 시작 시각이 점점 뒤로 밀리며 drift가 보인다.

## 한눈에 보기

가정:

- 간격은 `5초`
- 실제 실행 시간은 `8초`
- worker는 1개

| 질문 | `scheduleAtFixedRate` | `scheduleWithFixedDelay` |
|---|---|---|
| 다음 ticket 기준 | 이전 예정 시각 + 5초 | 이번 실행 종료 시각 + 5초 |
| overrun 때 보이는 핵심 현상 | overdue deadline debt, catch-up 압박 | schedule drift, breathing room 유지 |
| 끝나자마자 다시 실행될 수 있나 | 자주 그렇다 | 아니다. delay만큼 쉰다 |
| "원래 0,5,10,15..." 박자를 유지하려 하나 | 예 | 아니오 |
| 초보자용 한 줄 | 메트로놈을 놓쳐도 원래 박자를 보려는 방식 | 매번 숨 돌리고 다시 출발하는 방식 |

## drift와 backlog를 같은 그림에서 보기

같은 느린 작업도 두 방식에서 전혀 다르게 보인다.

```text
period = 5s, runtime = 8s

fixed-rate planned: 0 --- 5 --- 10 --- 15 --- 20
fixed-rate actual:  0 ------- 8 ------- 16 -------

fixed-delay actual: 0 ------- 8 ----- 13 ------- 21 ----- 26
```

여기서 초보자가 먼저 분리해야 할 단어는 두 개다.

| 단어 | 이 문서에서 뜻하는 것 | 주로 어디서 더 잘 보이나 |
|---|---|---|
| drift | 실제 시작 시각이 원래 박자에서 점점 뒤로 밀리는 현상 | `fixed-delay` |
| backlog | 다음 deadline이 이미 과거라 worker가 overdue ticket을 바로 다시 집는 압박 | `fixed-rate` |

엄밀히 말하면 backlog라는 말이 "queue에 같은 작업 복사본이 여러 장 쌓인다"는 뜻은 아니다.
입문자에게는 **원래 시작했어야 할 시각들이 이미 지나가 버린 상태**라고 잡는 편이 정확하다.

## `scheduleAtFixedRate`: backlog처럼 보이는 이유

`fixed-rate`는 다음 ticket을 "원래 예정 시각 + period"로 계산한다.

| 시각 | queue / worker에서 보이는 일 |
|---|---|
| `t=0` | 1회차 시작 |
| `t=8` | 1회차 종료. 원래 다음 deadline은 `t=5`였다 |
| `t=8` | queue head가 이미 overdue라서 worker는 거의 바로 다음 실행을 잡을 수 있다 |
| `t=16` | 2회차 종료. 원래 다음 deadline은 `t=10`, 그다음은 `t=15`였다 |

초보자용 비유:

> 5분 간격 버스가 와야 했는데 차가 늦어서, 정류장에 도착하자마자 이미 다음 출발 시각도 지나 있는 상태다.

그래서 `fixed-rate`는 작업이 느릴수록 이런 감각이 강해진다.

- "끝나고 5초 쉬는 작업"처럼 보이지 않는다.
- worker 입장에서는 overdue ticket이 계속 head에 걸린다.
- 원래 리듬을 따라잡으려는 압박이 생긴다.

## `scheduleWithFixedDelay`: drift가 커지는 이유

`fixed-delay`는 다음 ticket을 "이번 실행 종료 시각 + delay"로 계산한다.

| 시각 | queue / worker에서 보이는 일 |
|---|---|
| `t=0` | 1회차 시작 |
| `t=8` | 1회차 종료 |
| `t=13` | 5초 쉬고 2회차 시작 |
| `t=21` | 2회차 종료 |
| `t=26` | 다시 5초 쉬고 3회차 시작 |

이 방식은 원래의 `0, 5, 10, 15...` 박자를 포기한다.
대신 실행 사이 간격은 읽기 쉽다.

- 작업이 8초 걸리면 실제 시작은 `0, 13, 26...`처럼 밀린다.
- 하지만 매번 종료 후 5초는 비워 둔다.
- backlog를 따라잡기보다 "지금 상태에서 다시 일정 잡기"에 가깝다.

즉 `fixed-delay`의 핵심 문제는 "밀린 박자를 처리하느라 바쁨"보다
**전체 스케줄이 점점 늦어지는 drift**다.

## rescheduling queue 관점으로 다시 묶기

반복 작업을 queue로 보면 아래 표 하나로 정리된다.

| 질문 | `fixed-rate` | `fixed-delay` |
|---|---|---|
| 새 ticket을 언제 만들까 | 실행 후 | 실행 후 |
| 새 ticket 시간을 어디 기준으로 찍나 | 이전 예정 시각 | 이번 종료 시각 |
| 새 ticket이 만들어질 때 이미 overdue일 수 있나 | 예 | 거의 아니다 |
| head가 계속 같은 작업으로 채워질 수 있나 | 그렇다 | 덜하다 |
| beginner mental model | rescheduling queue가 과거 deadline debt를 들고 감 | rescheduling queue가 매번 현재 시각에서 새로 출발 |

이 표에서 중요한 점은 하나다.

> 둘 다 "반복 전용 마법"이 아니라, 실행 후 ticket을 다시 넣는 rescheduling queue다.

차이는 ticket timestamp 정책이다.

## 흔한 오해와 함정

1. `fixed-rate`면 같은 task 인스턴스가 여러 개 겹쳐 동시에 폭발한다고 바로 상상한다.
2. backlog를 "queue 안에 복사본이 수십 개 쌓이는 것"으로만 이해한다.
3. `fixed-delay`를 쓰면 느린 작업 문제가 해결된다고 생각한다.
4. drift와 backlog를 둘 다 그냥 "조금 늦음"으로 뭉뚱그린다.
5. scheduler 정책 문제와 worker/thread pool 부족 문제를 구분하지 않는다.

특히 2번이 중요하다.

- 이 문서의 backlog는 **missed schedule debt**에 가깝다.
- 한 periodic task를 볼 때는 "다음 ticket이 이미 늦었는가"가 핵심이다.

## 실무에서 쓰는 모습

| 상황 | 먼저 떠올릴 선택 | 이유 |
|---|---|---|
| "매 정시, 매 분처럼 벽시계 박자가 중요하다" | `scheduleAtFixedRate` | 원래 cadence를 유지하려고 한다 |
| "작업 사이 최소 휴식 시간이 필요하다" | `scheduleWithFixedDelay` | 종료 후 delay를 보장한다 |
| "실행 시간이 들쭉날쭉하고 종종 주기를 넘긴다" | 기본값은 `fixed-delay`부터 검토 | backlog catch-up 압박을 줄인다 |
| "느린 periodic task가 다른 due task까지 잡아먹는지 걱정된다" | queue 정책보다 worker 수와 분리부터 점검 | 병목은 실행 자원일 수 있다 |

초보자 체크 문장:

- 원래 박자 유지가 더 중요한가?
- 아니면 실행 사이 숨 고르기가 더 중요한가?

## 더 깊이 가려면

- 느린 periodic task의 timeline을 더 짧게 보고 싶다면 [Slow Periodic Task Primer](./slow-periodic-task-primer.md)
- catch-up, drift, skip, coalesce 정책 차이를 먼저 정리하고 싶다면 [Periodic Overrun Catch-Up Primer](./periodic-overrun-catch-up-primer.md)
- repeating task를 "다음 ticket 재등록"으로 더 직접 보고 싶다면 [DelayQueue Repeating Task Primer](./delayqueue-repeating-task-primer.md)
- scheduled executor를 deadline queue mental model로 먼저 잡고 싶다면 [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)
- due task가 ready queue에서 굶는 문제까지 이어서 보려면 [Ready Queue Starvation Primer](./ready-queue-starvation-primer.md)
- 스프링 운영 관점의 scheduler overload와 drift 해석이 필요하면 [Spring `TaskExecutor` / `TaskScheduler` Overload, Queue, and Rejection Semantics](../spring/spring-taskexecutor-taskscheduler-overload-rejection-semantics.md)

## 면접/시니어 질문 미리보기

1. `fixed-rate` overrun에서 "backlog"는 queue 복사본이 많다는 뜻인가, overdue deadline debt라는 뜻인가?
2. `fixed-delay`가 drift를 만드는 대신 어떤 운영상 안전성을 주는가?
3. 느린 periodic task 문제를 scheduler policy와 worker pool 병목으로 어떻게 분리해서 볼 것인가?

## 한 줄 정리

`scheduleAtFixedRate`는 원래 박자를 지키려다 overrun 시 overdue deadline debt가 보여 backlog처럼 느껴지고, `scheduleWithFixedDelay`는 종료 시각 기준으로 다시 예약해서 숨 고를 간격은 유지하지만 실제 시작 시각 drift는 커진다.
