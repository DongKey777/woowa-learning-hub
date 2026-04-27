# Java Timer vs ScheduledExecutorService vs DelayQueue Router

> 한 줄 요약: 초보자 기준 기본값은 거의 항상 `ScheduledExecutorService`이고, `Timer`는 레거시 호환 맥락에서만, `DelayQueue`는 직접 scheduler 규칙을 만들 때만 고른다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../algorithm/backend-algorithm-starter-pack.md)


retrieval-anchor-keywords: java timer vs scheduledexecutorservice vs delayqueue router basics, java timer vs scheduledexecutorservice vs delayqueue router beginner, java timer vs scheduledexecutorservice vs delayqueue router intro, data structure basics, beginner data structure, 처음 배우는데 java timer vs scheduledexecutorservice vs delayqueue router, java timer vs scheduledexecutorservice vs delayqueue router 입문, java timer vs scheduledexecutorservice vs delayqueue router 기초, what is java timer vs scheduledexecutorservice vs delayqueue router, how to java timer vs scheduledexecutorservice vs delayqueue router
> 관련 문서:
> - [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)
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
- queue 내부 deadline 시계를 왜 `nanoTime()` 쪽으로 생각하는지 보려면 [Java Timer Clock Choice Primer](./java-timer-clock-choice-primer.md)
- `DelayQueue`를 직접 구현 레벨에서 이해하려면 [DelayQueue Delayed Contract Primer](./delayqueue-delayed-contract-primer.md)
- repeating task 재등록 규칙은 [DelayQueue Repeating Task Primer](./delayqueue-repeating-task-primer.md)
- cancellation/reschedule stale entry 패턴은 [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md)

## 한 줄 정리

새 코드에서 "나중에 실행"이 필요하면 먼저 `ScheduledExecutorService`를 잡고,
`Timer`는 레거시 해석용으로, `DelayQueue`는 scheduler 내부 구현용으로 분리해서 보면 초반 혼선이 크게 줄어든다.
