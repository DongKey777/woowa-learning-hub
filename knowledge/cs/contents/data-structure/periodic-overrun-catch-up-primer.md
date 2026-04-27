# Periodic Overrun Catch-Up Primer

> 한 줄 요약: 반복 작업이 주기보다 오래 걸리면 scheduler는 보통 네 가지 중 하나를 택한다. **원래 박자를 따라잡으려 하거나(catch-up), 점점 늦어지거나(drift), 늦은 회차를 건너뛰거나(skip), 여러 번 밀린 일을 한 번으로 합치기도(coalesce)** 한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Fixed Rate vs Fixed Delay Overrun Primer](./fixed-rate-vs-fixed-delay-overrun-primer.md)
> - [Periodic Scheduling Drift vs Backlog Primer](./periodic-scheduling-drift-vs-backlog-primer.md)
> - [Slow Periodic Task Primer](./slow-periodic-task-primer.md)
> - [DelayQueue Repeating Task Primer](./delayqueue-repeating-task-primer.md)
> - [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)
> - [Bounded Queue Policy Primer](./bounded-queue-policy-primer.md)
>
> retrieval-anchor-keywords: periodic overrun catch up primer, periodic overrun beginner, fixed rate catch up primer, repeating task catch up policy, scheduler catch up drift skip coalesce, periodic task runtime longer than period, scheduled task overrun policy, delayqueue repeating task catch up, scheduleatfixedrate catch up, schedulewithfixeddelay drift, skip missed ticks, coalesce missed periods, timer overrun policy table, java repeating task overrun beginner, periodic backlog drift skip coalesce, 주기 작업 오버런, catch-up drift skip coalesce, 밀린 주기 작업 처리, 늦은 틱 건너뛰기, 주기 작업 드리프트

## 먼저 감각부터

초보자에게는 반복 작업을 이렇게 보면 쉽다.

> scheduler queue에는 "이 작업의 다음 실행 ticket 한 장"이 들어 있다.

작업이 `period = 5초`인데 실제 실행이 `8초` 걸리면,
다음 ticket이 나와야 할 시각보다 항상 늦게 끝난다. 이 상태를 여기서는 **overrun**이라고 부른다.

그러면 scheduler는 "늦은 작업을 어떻게 처리할지" 정책을 골라야 한다.

## 한눈에 보는 네 가지 반응

가정:

- 원래 주기: `5초`
- 실제 실행 시간: `8초`
- worker: 1개

| 정책 감각 | 초보자용 한 줄 | 보이는 결과 |
|---|---|---|
| catch-up | 놓친 박자를 따라잡으려 함 | 끝나자마자 다시 실행될 수 있음 |
| drift | 이번 실행이 끝난 시각에서 다시 출발 | 전체 스케줄이 점점 뒤로 밀림 |
| skip | 늦은 회차를 일부 버리고 최신 박자로 점프 | 실행 횟수는 줄지만 원래 cadence를 다시 맞추기 쉬움 |
| coalesce | 여러 번 밀린 일을 한 번 처리로 합침 | 중복 일은 줄이지만 "몇 회차를 합쳤는지" 의미를 설계해야 함 |

이 문서에서는 이 네 단어를 먼저 분리하는 것이 목표다.

## 1. catch-up: "밀린 박자 따라잡기"

가장 흔한 예는 `scheduleAtFixedRate` 같은 fixed-rate 쪽이다.

> 다음 ticket을 "이전 예정 시각 + period"로 계산한다.

그래서 실행이 늦으면 다음 ticket deadline이 이미 과거가 될 수 있다.

| 시각 | 무슨 일이 보이나 |
|---|---|
| `t=0` | 1회차 시작 |
| `t=8` | 1회차 종료 |
| `t=8` | 원래 2회차는 `t=5`였으므로 이미 늦음 |
| `t=8` | worker가 거의 바로 2회차를 시작할 수 있음 |
| `t=16` | 2회차 종료. 원래 3회차는 `t=10`, 4회차는 `t=15`였음 |

```text
planned tick:  0 --- 5 --- 10 --- 15 --- 20
actual start:  0 ------- 8 ------- 16 -------
```

초보자 감각으로는 이렇다.

- "실행 후 5초 쉰다"가 아니다.
- 이미 늦은 tick이 있으면 바로 다음 실행으로 이어질 수 있다.
- 원래 벽시계 박자를 중요하게 볼 때 이런 정책이 쓰인다.

## 2. drift: "이번 실행 기준으로 다시 시작"

대표 예는 `scheduleWithFixedDelay` 같은 fixed-delay 쪽이다.

> 다음 ticket을 "이번 실행 종료 시각 + delay"로 계산한다.

이 방식은 놓친 회차를 따라잡으려 하지 않는다.

| 시각 | 무슨 일이 보이나 |
|---|---|
| `t=0` | 1회차 시작 |
| `t=8` | 1회차 종료 |
| `t=13` | 5초 쉬고 2회차 시작 |
| `t=21` | 2회차 종료 |
| `t=26` | 다시 5초 쉬고 3회차 시작 |

```text
ideal beat:    0 --- 5 --- 10 --- 15 --- 20
actual start:  0 ------- 13 ------- 26 -------
```

여기서는 catch-up 대신 **drift**가 커진다.

- 작업 사이 쉬는 간격은 읽기 쉽다.
- 하지만 "매 5초 정각" 같은 원래 cadence는 점점 멀어진다.

## 3. skip: "놓친 회차를 버리고 최신 박자로 점프"

어떤 작업은 모든 회차를 꼭 다 실행할 필요가 없다.

예:

- "현재 캐시 상태를 5초마다 다시 계산"
- "최신 메트릭을 주기적으로 집계"

이런 일은 `t=5`, `t=10` 회차를 둘 다 따로 실행하기보다,
이미 늦었다면 **가장 최근 박자 하나만 남기고 건너뛰는 정책**이 더 자연스러울 수 있다.

| 질문 | skip 정책의 답 |
|---|---|
| 늦은 회차를 모두 다시 실행하나 | 아니오 |
| 원래 cadence로 복귀하려 하나 | 예, 자주 그렇다 |
| 적합한 일 | "최신 상태만 중요"한 주기 작업 |
| 부적합한 일 | 각 회차가 반드시 한 번씩 실행되어야 하는 작업 |

초보자 체크 문장:

> "빠진 회차 하나하나가 비즈니스적으로 의미가 있나?"

의미가 없다면 skip을 검토할 수 있다.

## 4. coalesce: "밀린 여러 번을 한 번으로 합치기"

skip과 비슷해 보이지만 질문이 조금 다르다.

- skip: 아예 몇 회차를 버린다.
- coalesce: 여러 회차를 **한 번의 실행에서 대표 처리**한다.

예:

- 변경 이벤트가 20번 밀렸지만 "다시 전체 스캔 1번"이면 충분한 작업
- UI 갱신 요청이 여러 번 왔지만 마지막 상태만 그리면 되는 작업

| 상황 | coalesce가 잘 맞는 이유 |
|---|---|
| 최신 상태만 맞으면 된다 | 마지막 상태 1번 반영으로 충분 |
| 중간 변화 하나하나는 중요하지 않다 | 중복 작업을 줄일 수 있다 |
| 비싼 계산이라 반복 catch-up이 더 위험하다 | 한 번 합쳐 처리하는 편이 안전하다 |

하지만 주의할 점도 있다.

- "몇 회차가 밀렸는지"를 버려도 되는지 먼저 확인해야 한다.
- 회차 수 자체가 의미 있는 작업이면 coalesce가 의미를 깨뜨릴 수 있다.

## 5. 네 정책을 같은 표로 고르기

| 질문 | catch-up | drift | skip | coalesce |
|---|---|---|---|---|
| 원래 박자가 중요한가 | 가장 적합 | 덜 적합 | 적합할 수 있음 | 경우에 따라 다름 |
| 작업 사이 휴식이 중요한가 | 약함 | 강함 | 중간 | 중간 |
| 모든 회차를 꼭 실행해야 하나 | 가장 잘 맞음 | 실행 수는 유지되지만 늦어짐 | 맞지 않음 | 맞지 않을 수 있음 |
| 최신 상태만 중요하나 | 과한 경우가 많음 | 가능 | 잘 맞음 | 매우 잘 맞음 |
| 과부하 때 중복 실행을 줄이나 | 아니오 | 일부 | 예 | 예 |

beginner 기준에서는 먼저 이렇게 보면 된다.

1. 모든 회차가 의미 있으면 `catch-up` 또는 `drift` 쪽을 본다.
2. 최신 상태만 중요하면 `skip` 또는 `coalesce`를 본다.
3. 원래 cadence가 더 중요하면 `catch-up/skip`, 휴식과 안정성이 더 중요하면 `drift/coalesce`를 우선 본다.

## 6. Java에서 흔히 만나는 모습

| Java 감각 | 초보자용 해석 |
|---|---|
| `scheduleAtFixedRate` | 기본적으로 catch-up 성향 |
| `scheduleWithFixedDelay` | 기본적으로 drift 성향 |
| 직접 self-rescheduling 구현 | skip / coalesce 같은 커스텀 정책을 넣기 쉬움 |
| `DelayQueue` 기반 scheduler 설계 | 다음 ticket 계산 정책을 코드로 드러내기 좋음 |

즉 Java API 이름보다 더 중요한 질문은 이것이다.

> "다음 ticket을 어떤 시각으로 다시 넣을 것인가, 그리고 늦은 회차를 모두 살릴 것인가?"

## 7. 자주 하는 오해

1. overrun이면 무조건 버그라고 생각한다.
2. catch-up이면 queue 안에 같은 task 복사본이 무한히 쌓인다고 상상한다.
3. drift는 그냥 "느리다" 정도의 말이라고 생각한다.
4. skip과 coalesce를 같은 말로 취급한다.
5. 모든 주기 작업은 회차를 하나도 빼먹으면 안 된다고 생각한다.

특히 4번은 꼭 분리해 두는 편이 좋다.

- skip은 "몇 회차를 그냥 버림"
- coalesce는 "여러 회차의 목적을 한 번으로 합침"

## 다음 문서로 이어가기

- fixed-rate와 fixed-delay의 기본 timeline 차이를 먼저 익히려면 [Fixed Rate vs Fixed Delay Overrun Primer](./fixed-rate-vs-fixed-delay-overrun-primer.md)
- drift와 backlog 느낌을 더 또렷하게 나누려면 [Periodic Scheduling Drift vs Backlog Primer](./periodic-scheduling-drift-vs-backlog-primer.md)
- repeating task를 ticket 재등록 관점으로 보고 싶다면 [DelayQueue Repeating Task Primer](./delayqueue-repeating-task-primer.md)
- scheduled executor를 delay-aware queue mental model로 연결하려면 [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)
- 주기 작업이 아니라 일반 queue overload에서 drop/keep 정책을 비교하고 싶다면 [Bounded Queue Policy Primer](./bounded-queue-policy-primer.md)

## 한 줄 정리

반복 작업이 주기보다 느릴 때 핵심은 "느려졌다" 자체보다 **밀린 회차를 어떻게 해석할지**다. 원래 박자를 따라잡을지, 점점 늦어질지, 늦은 회차를 건너뛸지, 여러 번을 한 번으로 합칠지에 따라 catch-up, drift, skip, coalesce라는 서로 다른 정책이 갈린다.
