---
schema_version: 3
title: Java Timer Clock Choice Primer
concept_id: data-structure/java-timer-clock-choice-primer
canonical: false
category: data-structure
difficulty: beginner
doc_role: chooser
level: beginner
language: ko
source_priority: 88
mission_ids:
- missions/roomescape
review_feedback_tags:
- java-timer-clock-choice
- nanotime-vs-currenttimemillis
- delayqueue-deadline-nanos
aliases:
- java timer clock choice
- nanoTime vs currentTimeMillis
- DelayQueue deadline nanos
- wall clock vs monotonic clock Java
- relative delay Java
- timer code unit mismatch
- 자바 nanotime currenttimemillis 차이
symptoms:
- 5초 뒤 실행 같은 상대 지연을 currentTimeMillis 기반으로만 계산해 wall clock 변경이나 보정에 흔들리는 모델을 만든다
- queue 내부 deadline은 nanoTime 기준이고 사용자/로그/API dueAt은 epoch wall clock이라는 경계를 구분하지 못한다
- Duration, TimeUnit, millis, nanos 변환을 섞어 timer delay 단위 버그를 만든다
intents:
- comparison
- troubleshooting
prerequisites:
- data-structure/timer-vocabulary-delay-timeout-deadline-dueat-bridge
next_docs:
- data-structure/delayqueue-delayed-contract-primer
- operating-system/monotonic-clock-wall-clock-timeout-deadline
- language/java-time-instant-localdatetime-boundaries
linked_paths:
- contents/data-structure/timer-vocabulary-delay-timeout-deadline-dueat-bridge.md
- contents/data-structure/delayqueue-delayed-contract-primer.md
- contents/operating-system/monotonic-clock-wall-clock-timeout-deadline.md
- contents/language/java/java-time-instant-localdatetime-boundaries.md
confusable_with:
- data-structure/timer-vocabulary-delay-timeout-deadline-dueat-bridge
- data-structure/delayqueue-delayed-contract-primer
- operating-system/monotonic-clock-wall-clock-timeout-deadline
- language/java-time-instant-localdatetime-boundaries
forbidden_neighbors: []
expected_queries:
- Java timer에서 System.nanoTime과 currentTimeMillis는 언제 각각 써야 해?
- DelayQueue 내부 deadline은 왜 nanoTime 기반이 더 안전해?
- 상대 delay와 사용자에게 보여줄 dueAt timestamp는 어떤 시계로 나눠야 해?
- TimeUnit millis nanos 변환 실수로 timer가 늦거나 빠르게 도는 버그를 어떻게 피해?
- wall clock과 monotonic clock 차이를 Java timer queue 기준으로 알려줘
contextual_chunk_prefix: |
  이 문서는 Java timer queue에서 상대 delay/deadline 계산은 System.nanoTime
  스톱워치 기준으로, 사용자/로그/저장소의 절대 시각은 currentTimeMillis나
  Instant 같은 wall clock 기준으로 나누는 beginner chooser다.
---
# Java Timer Clock Choice Primer

> 한 줄 요약: Java에서 "`5초 뒤 실행`" 같은 **상대 지연**을 다루는 queue 내부 시계는 보통 `System.nanoTime()`이 더 안전하고, `System.currentTimeMillis()`는 사용자/로그/저장소와 이야기할 때의 **벽시계 시간**에 더 가깝다.

**난이도: 🟢 Beginner**

관련 문서:

- [카테고리 README](./README.md)
- [Timer Vocabulary Bridge: delay vs timeout vs deadline vs dueAt](./timer-vocabulary-delay-timeout-deadline-dueat-bridge.md)
- [DelayQueue Delayed Contract Primer](./delayqueue-delayed-contract-primer.md)
- [Monotonic Clock, Wall Clock, Timeout, Deadline](../operating-system/monotonic-clock-wall-clock-timeout-deadline.md)
- [`Instant`, `LocalDateTime`, `OffsetDateTime`, `ZonedDateTime` Boundary Design](../language/java/java-time-instant-localdatetime-boundaries.md)

retrieval-anchor-keywords: java timer clock choice, java nanotime vs currenttimemillis, timeunit milliseconds to nanoseconds, duration to millis vs to nanos, timer code unit mismatch, java schedule after 5 seconds, delayqueue deadline nanos, dueat epoch millis to nanotime, relative delay java beginner, wall clock vs monotonic clock java, 자바 nanotime currenttimemillis 차이, 자바 timeunit duration 변환, 밀리초 나노초 변환 실수, timeout 단위 헷갈림 beginner

## 먼저 그림부터

초보자 기준으로는 시계를 두 종류로 나누면 거의 끝난다.

- `System.currentTimeMillis()`는 **벽시계**에 가깝다.
  지금이 몇 시 몇 분인지, 로그 timestamp가 무엇인지 말할 때 쓴다.
- `System.nanoTime()`은 **스톱워치**에 가깝다.
  지금부터 5초가 지났는지, 남은 시간이 얼마인지 계산할 때 쓴다.

timer queue가 묻는 질문은 대개 "지금 몇 시인가?"보다
"이 task까지 **얼마나 남았나**?"에 더 가깝다.

그래서 기본 선택표는 아주 단순하다.

| 지금 풀려는 질문 | 더 자연스러운 시계 | 이유 |
|---|---|---|
| 지금 실제 벽시계 시간이 몇 시인가 | `currentTimeMillis()` | 사람/로그/DB timestamp와 맞닿아 있다 |
| 작업이 5초 지연됐는가, 200ms 남았는가 | `nanoTime()` | 경과 시간과 남은 시간을 재는 데 더 자연스럽다 |
| `DelayQueue` head가 언제 만료되는가 | `nanoTime()` 기반 deadline | 상대 지연 비교가 흔들리지 않게 잡기 쉽다 |
| API payload에 `dueAt` timestamp를 실어 보내야 하는가 | `currentTimeMillis()` 또는 epoch timestamp | 다른 시스템과 공유 가능한 절대 시간이다 |

핵심 문장:

> queue 내부의 **상대 delay/deadline**은 `nanoTime()`,
> 사용자와 주고받는 **절대 시각**은 `currentTimeMillis()`.

여기서 `delay`, `deadline`, `dueAt`, `timeout`이라는 말 자체가 먼저 섞인다면 [Timer Vocabulary Bridge: delay vs timeout vs deadline vs dueAt](./timer-vocabulary-delay-timeout-deadline-dueat-bridge.md)에서 단어 층을 먼저 나누고 돌아오면 더 덜 헷갈린다.

## 1. 왜 timer queue는 스톱워치 쪽 감각이 더 맞나

`DelayQueue`나 delayed work queue에서 필요한 계산은 보통 이렇다.

1. 지금부터 `delay`만큼 뒤의 deadline을 만든다.
2. 현재 시각과 deadline을 비교해 남은 시간을 구한다.
3. 남은 시간이 0 이하가 되면 task를 꺼낸다.

이 흐름은 "캘린더 시각"보다 "얼마나 흘렀나"가 핵심이다.

```java
long delayNanos = unit.toNanos(delay);
long deadlineNanos = System.nanoTime() + delayNanos;

long remainingNanos = deadlineNanos - System.nanoTime();
```

이 코드는 "언제 실행 가능한가"를 **같은 기준의 스톱워치 값**으로 계산한다.

반대로 아래처럼 wall-clock 기준으로만 생각하면,
"벽시계가 바뀌면 남은 시간도 같이 흔들린다"는 그림을 놓치기 쉽다.

```java
long deadlineMillis = System.currentTimeMillis() + delayMillis;
long remainingMillis = deadlineMillis - System.currentTimeMillis();
```

이 패턴이 항상 즉시 틀리는 것은 아니다.
다만 timer queue 입문에서는 **벽시계 보정이나 변경의 영향을 덜 받는 방향**으로 mental model을 잡는 편이 안전하다.

## 2. `currentTimeMillis()`가 헷갈리게 만드는 장면

예를 들어 `5초 뒤 실행` 작업을 등록했다고 하자.

| 시점 | 벽시계 기준으로 보이는 일 | 사람이 기대하는 남은 시간 |
|---|---|---|
| 등록 직후 | `deadline = 현재 시각 + 5초` | 5초 |
| 2초 뒤 | 아직 3초 남아야 함 | 3초 |

그런데 그 사이 시스템 벽시계가 뒤로 밀리거나 앞으로 당겨지면,
`currentTimeMillis()`로 계산한 남은 시간이 갑자기 달라질 수 있다.

| 벽시계 변화 | `currentTimeMillis()` 기반 남은 시간 감각 | 초보자 입장에서 보이는 문제 |
|---|---|---|
| 시계가 뒤로 밀림 | 남은 시간이 갑자기 길어진다 | task가 늦게 실행되는 것처럼 보인다 |
| 시계가 앞으로 당겨짐 | 남은 시간이 갑자기 짧아진다 | task가 너무 빨리 만료된 것처럼 보인다 |

여기서 중요한 건 운영체제 deep dive가 아니다.
입문 단계에서는 아래 한 줄만 기억하면 충분하다.

> 상대 delay는 "벽시계 날짜"보다 "경과 시간" 감각으로 잡아야 덜 헷갈린다.

## 3. `nanoTime()`은 "현재 날짜"를 말해 주는 값이 아니다

`nanoTime()`을 처음 보면 이름 때문에 오해가 생긴다.

| 오해 | 더 안전한 이해 |
|---|---|
| nanosecond precision이 꼭 필요해서 `nanoTime()`을 쓴다 | 핵심은 정밀도보다 **elapsed-time 기준**이라는 점이다 |
| `nanoTime()` 값 자체를 DB나 API에 저장해도 된다 | 보통은 같은 JVM 안 상대 비교용으로만 본다 |
| `nanoTime()`으로 지금 몇 시인지 알 수 있다 | 아니다. wall-clock timestamp 용도가 아니다 |
| `currentTimeMillis()`도 숫자니까 섞어 계산해도 된다 | 두 값은 **기준점이 다르다**고 생각하는 편이 안전하다 |

특히 아래처럼 두 시계를 섞으면 안 된다.

```java
long deadlineNanos = System.nanoTime() + TimeUnit.SECONDS.toNanos(5);
long remaining = deadlineNanos - System.currentTimeMillis(); // 잘못된 혼합
```

이 코드는 단위도 다르고, "무슨 시계를 기준으로 한 숫자인가"도 다르다.

## 4. queue 내부는 `nanoTime()`, 바깥 세계는 epoch time으로 나누면 편하다

실무에서도 이 둘 중 하나만 쓰는 경우보다,
**경계에서 역할을 나눠 쓰는 경우**가 많다.

예를 들어 API나 DB에는 "언제 실행해야 하는지"를 epoch millis로 들고 있고,
JVM 안 queue에는 "남은 지연"을 `nanoTime()` deadline으로 바꿔 넣는 식이다.

```java
long dueAtEpochMillis = command.dueAtEpochMillis();

long delayMillis =
    Math.max(0L, dueAtEpochMillis - System.currentTimeMillis());

long deadlineNanos =
    System.nanoTime() + TimeUnit.MILLISECONDS.toNanos(delayMillis);
```

이 흐름을 표로 보면 더 단순하다.

| 단계 | 쓰는 시계 | 이유 |
|---|---|---|
| API/DB에서 `dueAt` 읽기 | epoch millis / `currentTimeMillis()` 계열 | 외부 시스템과 절대 시각을 공유해야 한다 |
| queue에 넣기 직전 delay 계산 | `currentTimeMillis()`로 차이 계산 | 외부 절대 시각을 현재 벽시계와 비교한다 |
| queue 내부 deadline 저장 | `nanoTime()` | 상대 지연 비교를 안정적으로 가져간다 |
| 로그/UI에 언제 예정이었는지 보여 주기 | epoch millis | 사람이 읽는 시간 표현이 필요하다 |

즉 "외부 계약은 absolute time, 내부 scheduler는 relative time"으로 나누면 머리가 훨씬 덜 복잡해진다.

## 5. `TimeUnit`과 `Duration` 변환도 결국 내부 기준 하나로 모은다

timer code에서 자주 나는 실수는 시계 혼합만이 아니다.
`ms`, `s`, `ns`, `Duration`이 한 메서드 안에 같이 보일 때
"지금 이 값이 **입력 표현**인지, **내부 비교 기준**인지"를 놓치면 버그가 생긴다.

가장 안전한 mental model은 이것이다.

| 값 | 초보자용 질문 | 흔한 표현 |
|---|---|---|
| 입력 delay | "호출자가 몇 초/밀리초 뒤라고 말했나?" | `5`, `500`, `Duration.ofSeconds(5)` |
| 내부 deadline | "queue는 어떤 기준으로 비교하나?" | `deadlineNanos` |
| 출력/로그 값 | "사람이나 다른 API에 무엇을 보여 주나?" | `remainingMillis`, `dueAtEpochMillis` |

즉 `TimeUnit`과 `Duration`은 보통 **표현을 바꾸는 도구**이고,
queue가 실제로 붙잡고 있어야 하는 값은 여전히 `deadlineNanos` 같은 내부 기준이다.

### 빠른 비교표

| 하고 싶은 일 | 더 안전한 첫 선택 | 이유 |
|---|---|---|
| `(delay, unit)` 입력을 내부 deadline으로 바꾸기 | `unit.toNanos(delay)` | 호출자가 준 단위를 직접 받는다 |
| `Duration`을 내부 deadline으로 바꾸기 | `duration.toNanos()` | 타입에 단위 정보가 이미 들어 있다 |
| 남은 시간을 로그나 메트릭으로 보여 주기 | `Duration.ofNanos(remaining)` 또는 `TimeUnit.NANOSECONDS.toMillis(...)` | 내부 기준에서 바깥 표현으로 한 번만 바꾼다 |
| `Duration`을 다시 `currentTimeMillis()`와 섞어 계산하기 | 피한다 | 단위 변환과 시계 변환이 한 줄에 섞인다 |

예를 들어 아래 두 코드는 같은 뜻이다.

```java
long delayNanos = unit.toNanos(delay);
long deadlineNanos = System.nanoTime() + delayNanos;
```

```java
long deadlineNanos = System.nanoTime() + duration.toNanos();
```

핵심은 `TimeUnit`이든 `Duration`이든 "마지막에는 내부 비교 단위 하나로 모은다"는 점이다.

## 6. millis/nanos 변환 실수는 변수 이름과 최종 단위를 같이 본다

아래는 timer code에서 초보자가 특히 자주 하는 단위 실수다.

| 실수 | 왜 헷갈리나 | 더 안전한 모양 |
|---|---|---|
| `delayMillis`인데 `TimeUnit.SECONDS.toNanos(delayMillis)`를 쓴다 | 변수 이름과 변환 단위가 다르다 | 변수 이름과 변환 단위를 맞춘다 |
| `duration.toMillis()` 후 다시 `MILLISECONDS.toNanos(...)` | 중간 표현을 괜히 거친다 | 가능하면 `duration.toNanos()`로 바로 간다 |
| `deadlineNanos`를 로그에 바로 출력한다 | 내부 기준값을 벽시계처럼 읽는다 | 로그는 `remainingMillis`나 `dueAtEpochMillis`로 따로 만든다 |
| `Duration.ofMillis(500)`과 `schedule(..., 500, SECONDS)`를 같은 감각으로 읽는다 | 숫자는 같아도 단위가 다르다 | 숫자보다 단위를 먼저 읽는다 |

timer code 리뷰에서는 아래 질문 3개만 먼저 던져도 실수가 많이 줄어든다.

1. 지금 보는 값은 `delay`, `deadline`, `dueAt` 중 무엇인가?
2. 이 줄은 단위 변환인가, 시계 변환인가?
3. 내부 비교 기준이 마지막에 `deadlineNanos` 하나로 모였는가?

## 7. DelayQueue식 구현에서는 이런 모양이 기본값이다

`Delayed` 구현에서는 보통 `deadlineNanos`를 저장하고,
`getDelay()`와 `compareTo()`가 모두 그 값을 기준으로 움직이게 만든다.

```java
final class TimerTicket implements Delayed {
    private final long deadlineNanos;
    private final long sequence;

    TimerTicket(long delay, TimeUnit unit, long sequence) {
        this.deadlineNanos = System.nanoTime() + unit.toNanos(delay);
        this.sequence = sequence;
    }

    @Override
    public long getDelay(TimeUnit unit) {
        return unit.convert(
            deadlineNanos - System.nanoTime(),
            TimeUnit.NANOSECONDS
        );
    }

    @Override
    public int compareTo(Delayed other) {
        TimerTicket that = (TimerTicket) other;
        int byDeadline = Long.compare(this.deadlineNanos, that.deadlineNanos);
        if (byDeadline != 0) {
            return byDeadline;
        }
        return Long.compare(this.sequence, that.sequence);
    }
}
```

여기서 중요한 것은 "나노초까지 정말 정확한가"가 아니라:

- queue head가 가장 이른 deadline인가
- 남은 시간 계산과 head ordering이 같은 기준인가
- 벽시계 변화와 내부 상대 delay를 섞지 않았는가

이 세 가지다.

## 8. 자주 하는 오해

1. `currentTimeMillis()`가 더 익숙하니 timer queue에도 그대로 쓰면 된다고 생각한다.
2. `nanoTime()`은 너무 고급스럽고 과한 선택이라고 느낀다.
3. `nanoTime()`을 쓰면 "현재 시각"도 같이 알 수 있다고 생각한다.
4. `dueAtEpochMillis`와 queue 내부 `deadlineNanos`를 같은 값으로 저장해야 한다고 생각한다.
5. `nanoTime()`을 쓴다는 말이 곧 nanosecond-level accuracy를 약속한다는 뜻으로 읽는다.
6. `Duration`을 쓴다고 해서 clock 선택 문제와 단위 변환 문제가 자동으로 사라진다고 생각한다.
7. 숫자가 같으면 단위도 같은 뜻이라고 읽는다. `500ms`와 `500ns`는 완전히 다른 지연이다.

입문 단계에서는 이렇게만 정리하면 충분하다.

- "몇 시냐?"는 벽시계 질문이다.
- "얼마 남았냐?"는 스톱워치 질문이다.
- delay/deadline queue는 보통 두 번째 질문을 더 자주 한다.
- `TimeUnit`과 `Duration`은 숫자에 단위를 붙여 주는 표현이고, queue 내부 비교 기준은 따로 고정해야 한다.

## 다음 문서로 이어가기

- `ScheduledExecutorService`의 delayed work queue 감각을 먼저 잡으려면 [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)
- `Delayed.compareTo()`와 `getDelay()`가 같은 deadline을 봐야 하는 이유는 [DelayQueue Delayed Contract Primer](./delayqueue-delayed-contract-primer.md)
- `PriorityBlockingQueue`가 왜 timer queue가 아닌지는 [PriorityBlockingQueue Timer Misuse Primer](./priorityblockingqueue-timer-misuse-primer.md)
- cancel/reschedule 후 stale ticket이 남는 흐름은 [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md)
- plain `PriorityQueue`와 `DelayQueue` 선택을 더 넓게 보려면 [DelayQueue vs PriorityQueue Timer Pitfalls](./delayqueue-vs-priorityqueue-timer-pitfalls.md)

## 한 줄 정리

Java timer queue에서 `currentTimeMillis()`는 "몇 시에 실행 예정이었나"를 설명할 때 더 어울리고,
`nanoTime()`은 "지금 얼마나 남았나"를 계산하는 queue 내부 deadline clock으로 더 잘 맞는다.
