# Timer Vocabulary Bridge: delay vs timeout vs deadline vs dueAt

> 한 줄 요약: timer/scheduler 문맥에서는 `delay`를 "지금부터 얼마나 뒤", `deadline`을 "내부 queue가 비교하는 실행 가능 시각", `dueAt`을 "바깥 세계와 공유하는 절대 시각", `timeout`을 "그 시각까지 안 끝나면 실패로 취급하는 규칙"으로 나누면 초반 혼선이 크게 줄어든다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)
> - [DelayQueue Delayed Contract Primer](./delayqueue-delayed-contract-primer.md)
> - [Java Timer Clock Choice Primer](./java-timer-clock-choice-primer.md)
> - [DelayQueue Repeating Task Primer](./delayqueue-repeating-task-primer.md)
> - [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md)
> - [DelayQueue vs PriorityQueue Timer Pitfalls](./delayqueue-vs-priorityqueue-timer-pitfalls.md)
> - [PriorityBlockingQueue Timer Misuse Primer](./priorityblockingqueue-timer-misuse-primer.md)
>
> retrieval-anchor-keywords: delay vs timeout vs deadline vs dueAt, timeout deadline dueAt vocabulary, timer terminology bridge, scheduler terminology beginner, delay deadline timeout difference, dueAt vs deadline java, schedule delay vs dueAt, timeout task deadline queue, dueAtEpochMillis deadlineNanos, queue timer words beginner, delayed task vocabulary, absolute time vs relative delay timer, timeout means what scheduler, 자바 타이머 용어 정리, delay timeout deadline dueAt 차이, dueAt deadline 차이, 스케줄러 용어 브리지, 지연 타이머 용어, deadlineNanos dueAtEpochMillis

## 먼저 한 장으로 잡기

초보자 기준으로는 이 한 문장부터 잡으면 된다.

- `delay`: 지금부터 얼마나 뒤인가
- `deadline`: queue 안에서 "언제 실행 가능해지는가"를 비교하는 시각
- `dueAt`: 로그, DB, API payload에 적기 좋은 절대 시각
- `timeout`: 그 시각까지 일이 안 끝나면 실패 처리하겠다는 규칙

같은 타이머를 두고도 이름이 여러 개 나오는 이유는
"사람이 읽는 말", "외부 계약", "queue 내부 계산", "실패 정책"이 서로 다른 층이기 때문이다.

## 빠른 선택표

| 지금 말하고 싶은 것 | 가장 자연스러운 단어 | 초보자용 감각 |
|---|---|---|
| `3초 뒤 실행`처럼 지금 기준 간격 | `delay` | 아직 시각이 아니라 길이다 |
| heap/queue가 비교하는 내부 실행 시각 | `deadline` | `DelayQueue` head를 정하는 기준점이다 |
| API/DB에 `"2026-04-27T12:00:05Z"`처럼 남길 시각 | `dueAt` | 바깥 세계와 공유하는 약속된 절대 시간이다 |
| "그때까지 응답이 없으면 실패" 규칙 | `timeout` | 타이머가 울리면 실패 branch로 간다 |

핵심은 `timeout`만 정책 이름이고,
`delay`/`deadline`/`dueAt`은 대체로 **시각을 만드는 표현**이라는 점이다.

## 1. 하나의 작업을 네 단어로 번역해 보기

예를 들어 "응답이 5초 안에 안 오면 timeout 처리"를 만든다고 하자.

```text
now = 12:00:00.000
delay = 5초
dueAt = 12:00:05.000 (epoch millis로도 표현 가능)
deadline = queue 내부에서 비교할 runAtNanos
timeout = 12:00:05.000까지 응답이 없으면 fail
```

표로 보면 더 단순하다.

| 단어 | 이 예시에서 하는 일 | 어디에서 자주 보이나 |
|---|---|---|
| `delay` | `5초`라는 상대 간격 | `schedule(job, 5, SECONDS)` |
| `dueAt` | `12:00:05`라는 절대 시각 | API payload, DB 컬럼, 로그 |
| `deadline` | queue 내부 `deadlineNanos` | `Delayed.compareTo()`, heap head |
| `timeout` | 그 시각까지 완료 안 되면 실패 | request guard, cancellation branch |

즉 보통 흐름은 이렇게 읽으면 된다.

1. 입력은 `delay`나 `dueAt`으로 들어온다.
2. scheduler는 그것을 내부 `deadline`으로 바꿔 queue에 넣는다.
3. 그 timer가 "실패 처리용"이라면 이름은 `timeout`이 된다.

## 2. `delay`는 길이이고, `deadline`은 점이다

이 둘이 가장 자주 섞인다.

| 단어 | 질문 형태 | 예시 |
|---|---|---|
| `delay` | "얼마나 뒤?" | `3초 뒤`, `250ms 뒤` |
| `deadline` | "정확히 언제 실행 가능?" | `deadlineNanos = nowNanos + 3초` |

`schedule(job, 3, SECONDS)`는 API 표면에서는 `delay`를 받는다.
하지만 queue 안으로 들어갈 때는 거의 항상 `deadline`으로 바뀐다.

```java
long delayNanos = unit.toNanos(delay);
long deadlineNanos = System.nanoTime() + delayNanos;
```

그래서 자료구조 문서에서 `deadline`이 많이 보이는 것은 자연스럽다.

- heap은 보통 "점"을 비교해야 정렬이 쉽다
- `getDelay()`는 그 점까지 남은 시간을 다시 계산한다

즉 `delay`는 입력 표현이고, `deadline`은 내부 표현이라고 보면 된다.

## 3. `dueAt`은 외부 계약용 absolute time이다

`dueAt`은 보통 queue 안에서 바로 비교하기보다
바깥 세계와 약속을 맞추기 위해 쓴다.

| 장면 | `dueAt`이 잘 맞는 이유 |
|---|---|
| API가 "언제 보내야 하는지"를 넘겨준다 | 다른 서비스와 같은 절대 시각을 공유해야 한다 |
| DB에 예약 시각을 저장한다 | 재시작 후에도 같은 시각을 복원해야 한다 |
| 로그에서 "원래 몇 시 예정이었나"를 보여 준다 | 사람이 읽는 시간이 필요하다 |

다만 queue 내부에 그대로 들고 가면 머리가 복잡해질 수 있다.
보통은 경계에서 한 번 변환한다.

```java
long dueAtEpochMillis = command.dueAtEpochMillis();
long delayMillis = Math.max(0L, dueAtEpochMillis - System.currentTimeMillis());
long deadlineNanos = System.nanoTime() + TimeUnit.MILLISECONDS.toNanos(delayMillis);
```

초보자용 감각은 이것이다.

- `dueAt`: 밖에서 약속한 시각
- `deadline`: 안에서 비교할 시각

둘 다 "언제"를 말하지만, **시계를 쓰는 목적이 다르다.**

## 4. `timeout`은 시각 그 자체보다 실패 규칙에 가깝다

`timeout`은 `delay`처럼 길이로도 보이고, `deadline`처럼 시각과 연결되기도 해서 더 헷갈린다.

가장 안전한 정리는 아래다.

| 표현 | 초보자용 해석 |
|---|---|
| `timeout = 5초` | 실패 조건을 만들기 위한 설정값 |
| `timeout task` | 그 시간이 지나면 실행될 실패 처리 ticket |
| `request timed out` | deadline 전에 완료 신호가 오지 않았다는 결과 |

예를 들어 요청 timeout은 이렇게 읽으면 된다.

1. `timeout = 5초` 설정을 받는다.
2. scheduler는 `5초 delay`로 timeout ticket을 등록한다.
3. 내부 queue에는 그 ticket의 `deadline`이 저장된다.
4. 응답이 먼저 오면 timeout ticket을 cancel한다.
5. 응답이 안 오면 timeout ticket이 실행된다.

즉 `timeout`은 대개 "무슨 종류의 timer인가?"를 설명하는 이름이다.
그 timer를 queue에 올릴 때 실제로 비교되는 값은 `deadline`이다.

## 5. 문서마다 이름이 달라 보여도 역할은 비슷하다

같은 개념이 문서마다 아래처럼 표현될 수 있다.

| 문서/코드에서 보이는 이름 | 이 문서의 기본 번역 |
|---|---|
| `delay`, `initialDelay` | 지금부터의 간격 |
| `runAt`, `readyAt`, `fireAt` | 내부 또는 외부 실행 시각 |
| `deadlineNanos`, `runAtNanos` | queue 내부 deadline |
| `dueAt`, `dueAtEpochMillis` | 외부 계약용 absolute time |
| `timeout`, `ttl`, `lease expiry` | 그 시각이 지나면 상태가 바뀌는 정책 이름 |

그래서 변수 이름을 읽을 때는 먼저 이 질문을 던지면 된다.

1. 이 값은 "간격"인가, "시각"인가?
2. 이 값은 바깥 세계와 공유하나, queue 안에서만 쓰나?
3. 이 timer는 성공 작업인가, timeout 같은 실패 guard인가?

## 6. 초보자가 많이 섞는 조합

1. `delay`를 business priority처럼 읽는다.
   `delay`는 "먼저 처리할 중요도"가 아니라 "언제 실행 가능해지는가"다.
2. `dueAt`과 `deadline`이 항상 같은 저장값이어야 한다고 생각한다.
   외부 absolute time을 내부 monotonic deadline으로 바꿔도 된다.
3. `timeout`을 "단순 숫자"로만 본다.
   실제로는 cancel/reschedule이 붙는 하나의 timer policy다.
4. `deadline`을 사람에게 보여 줄 로그 시각으로 바로 쓴다.
   `deadlineNanos` 같은 내부 값은 보통 로그용 absolute time과 분리하는 편이 낫다.

## 7. 문서 간 mental model 연결

| 이 문서를 읽고 다음에 막히는 질문 | 이어서 볼 문서 |
|---|---|
| `deadline`을 왜 `nanoTime()`으로 잡지? | [Java Timer Clock Choice Primer](./java-timer-clock-choice-primer.md) |
| `Delayed.compareTo()`와 `getDelay()`는 왜 같은 deadline을 봐야 하지? | [DelayQueue Delayed Contract Primer](./delayqueue-delayed-contract-primer.md) |
| `schedule(delay)`가 queue 입장에서는 어떻게 보이지? | [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md) |
| timeout ticket을 취소하거나 다시 예약하면 왜 stale entry가 남지? | [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md) |
| queue 선택 자체가 헷갈린다 | [DelayQueue vs PriorityQueue Timer Pitfalls](./delayqueue-vs-priorityqueue-timer-pitfalls.md) |

## 한 줄 정리

`delay`는 "얼마나 뒤", `deadline`은 "queue 내부 실행 시각", `dueAt`은 "밖과 공유하는 절대 시각", `timeout`은 "그때까지 안 끝나면 실패"라고 잡으면 scheduler와 queue 문서를 같은 머리로 읽기 쉬워진다.
