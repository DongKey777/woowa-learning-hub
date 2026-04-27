# Cancelled Task Cleanup: `purge()` vs `removeOnCancelPolicy`

> 한 줄 요약: `cancel()`은 "이 작업을 더 이상 실행하지 말라"는 상태 변경이고, 취소된 task를 queue에서 언제 치울지는 `removeOnCancelPolicy(true)` 같은 즉시 정리 정책이나 `purge()` 같은 나중 정리 호출로 따로 결정된다.

**난이도: 🟢 Beginner**

관련 문서:

- [ScheduledFuture Cancellation Bridge](./scheduledfuture-cancel-stale-entries.md)
- [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)
- [DelayQueue Remove Cost Primer](./delayqueue-remove-cost-primer.md)
- [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md)
- [Timing Wheel vs Delay Queue](./timing-wheel-vs-delay-queue.md)

retrieval-anchor-keywords: purge vs removeOnCancelPolicy, scheduledthreadpoolexecutor purge, scheduledthreadpoolexecutor removeoncancelpolicy, cancelled task cleanup, cancelled task retention, cancelled scheduled task queue cleanup, scheduledfuture cancel queue size, cancel true queue size unchanged, purge removes cancelled tasks, removeOnCancelPolicy immediate cleanup, scheduled executor cancelled task memory retention, stale scheduled task cleanup, delayed work queue cancelled entry, batch cleanup vs immediate cleanup, threadpoolexecutor purge, scheduled executor purge when to use, removeOnCancelPolicy when to use, beginner scheduled task cleanup, 취소된 task 정리, purge removeOnCancelPolicy 차이, cancel 성공인데 queue 안 줄어듦

## 먼저 그림부터

예약 task를 "알람표"라고 생각하면 쉽다.

1. `schedule(...)`를 호출하면 queue에 알람표가 들어간다.
2. `cancel(...)`를 호출하면 그 알람표는 더 이상 실행하면 안 되는 상태가 된다.
3. 하지만 알람표 종이가 queue 상자 안에서 바로 사라지는지는 별도 문제다.

즉 초보자용 핵심은 이것이다.

```text
cancel() = 실행 금지
cleanup  = queue에서 언제 치울지
```

여기서 cleanup을 하는 대표 방법이 두 가지다.

| 방법 | 감각 | 언제 비용을 내나 |
|---|---|---|
| `setRemoveOnCancelPolicy(true)` | 취소하는 순간 바로 치운다 | `cancel()` hot path |
| `purge()` | 취소된 것들을 나중에 한 번 훑어서 치운다 | `purge()` 호출 시점 |

## 둘의 차이를 한 번에 보기

| 질문 | `removeOnCancelPolicy(true)` | `purge()` |
|---|---|---|
| 언제 동작하나 | 각 `cancel()` 직후 | 내가 `purge()`를 호출할 때 |
| 정리 방식 | 즉시 제거 쪽에 가깝다 | batch cleanup에 가깝다 |
| 보통 쓰는 이유 | 취소된 task가 오래 남는 것을 줄이고 싶다 | 이미 쌓인 cancelled entry를 한 번 비우고 싶다 |
| trade-off | cancel 경로 비용과 lock 경쟁이 올라올 수 있다 | purge 호출 자체가 queue scan 비용을 가진다 |
| beginner 메모 | "매 취소 때 청소" | "가끔 대청소" |

짧게 외우면 이렇게 잡으면 된다.

```text
removeOnCancelPolicy = 취소할 때 바로 청소
purge()              = 나중에 모아서 청소
```

## 언제 explicit cleanup이 필요해지나

취소된 task는 실행만 안 되면 correctness는 맞을 수 있다.
문제는 retention이다.

아래 상황이 겹치면 queue cleanup을 신경 써야 한다.

| workload 신호 | 왜 보나 | 먼저 떠올릴 선택 |
|---|---|---|
| delay가 길다 | 취소된 entry가 오래 남을 수 있다 | `removeOnCancelPolicy(true)` 검토 |
| 등록은 많고 대부분 빨리 취소된다 | stale entry가 유효 task보다 더 많아질 수 있다 | 즉시 제거 또는 주기적 `purge()` 검토 |
| `getQueue().size()`가 계속 큰데 실제 실행은 적다 | cancelled entry가 섞였을 수 있다 | retention 의심 |
| 메모리 압박이 보인다 | long-delay cancelled task가 쌓일 수 있다 | cleanup 정책 확인 |
| cancel hot path latency가 민감하다 | 즉시 제거 비용이 부담일 수 있다 | lazy + 주기적 `purge()`도 후보 |

핵심은 이것이다.

> 취소 correctness와 취소 흔적 cleanup은 다른 문제다.

## `purge()`는 무엇을 하는가

`purge()`는 "지금 queue 안에 남아 있는 cancelled task들을 한 번 훑어서 제거하자"에 가깝다.

초보자용 그림은 이렇다.

```text
취소 직후:
[live][cancelled][live][cancelled][live]

purge() 호출 후:
[live][live][live]
```

즉 `purge()`는 취소 API가 아니라 cleanup API다.

| 자주 하는 착각 | 더 정확한 해석 |
|---|---|
| `purge()`가 취소를 대신한다 | 아니다. 이미 취소된 task를 정리할 뿐이다 |
| `purge()`가 자동으로 항상 돈다 | 아니다. 직접 호출해야 한다 |
| `purge()`를 한 번 부르면 앞으로도 즉시 제거된다 | 아니다. 그 시점의 cancelled entry를 치우는 batch cleanup에 가깝다 |

## `removeOnCancelPolicy(true)`는 무엇을 바꾸나

`ScheduledThreadPoolExecutor`에서 이 정책을 켜면, cancel path에서 queue 제거를 더 적극적으로 하게 된다.

```java
ScheduledThreadPoolExecutor scheduler =
    new ScheduledThreadPoolExecutor(4);

scheduler.setRemoveOnCancelPolicy(true);
```

이 설정은 초보자 기준으로 이렇게 읽으면 충분하다.

- `cancel()` 성공만으로 끝내지 않고
- 취소된 delayed entry를 queue에서 바로 빼려고 한다

그래서 long-delay timeout을 많이 만들었다가 대부분 곧 취소하는 workload에서 retention을 줄이는 데 유용할 수 있다.

## 둘을 timeline으로 보면

같은 timeout workload를 두 방식으로 보면 차이가 더 잘 보인다.

### 1. 기본 lazy cleanup에 가깝게 둘 때

```text
t=0s   1시간 뒤 timeout 예약
t=2s   응답 도착, cancel(false)
t=2s   task는 논리적으로 취소됨
t=2s   queue에는 cancelled entry가 남아 있을 수 있음
t=10m  purge()를 안 부르면 여전히 retention이 보일 수 있음
```

### 2. `removeOnCancelPolicy(true)`를 켠 경우

```text
t=0s   1시간 뒤 timeout 예약
t=2s   응답 도착, cancel(false)
t=2s   task는 논리적으로 취소됨
t=2s   cancel 경로에서 queue 제거까지 더 시도
t=2s   queue 잔류 시간이 더 짧아질 수 있음
```

### 3. lazy로 두되 가끔 `purge()`를 부르는 경우

```text
t=0s   여러 long-delay timeout 예약
t=2s   다수 cancel
t=30s  cancelled entry가 queue에 남아 있음
t=60s  purge() 호출
t=60s  그 시점의 cancelled entry를 batch cleanup
```

## 어떤 쪽을 먼저 고를까

| 상황 | 더 자연스러운 시작점 |
|---|---|
| 취소가 많고 retention이 바로 문제다 | `removeOnCancelPolicy(true)` 먼저 검토 |
| cancel 호출이 매우 뜨거워서 매번 제거 비용이 부담이다 | lazy 유지 + 필요 시 `purge()` 검토 |
| 이미 운영 중이고 cancelled entry가 쌓인 것이 보인다 | 우선 `purge()`로 정리 관찰 |
| queue 크기 해석이 필요하다 | cancelled entry 포함 여부를 먼저 분리 |
| timeout churn이 매우 크다 | heap scheduler 자체가 맞는지까지 재검토 |

초보자용 판단 기준은 복잡하게 잡지 않아도 된다.

> "매 취소 때 바로 치울지"와 "나중에 한 번에 치울지"의 선택이라고 보면 된다.

## 작은 예시

```java
class RequestTimeouts {
    private final ScheduledThreadPoolExecutor scheduler =
        new ScheduledThreadPoolExecutor(2);

    RequestTimeouts() {
        scheduler.setRemoveOnCancelPolicy(true);
    }

    ScheduledFuture<?> register(String requestId) {
        return scheduler.schedule(
            () -> failRequest(requestId),
            30,
            TimeUnit.SECONDS
        );
    }

    void onResponse(ScheduledFuture<?> timeout) {
        timeout.cancel(false);
    }

    void cleanupIfNeeded() {
        scheduler.purge();
    }

    private void failRequest(String requestId) {
        // timeout 처리
    }
}
```

이 코드에서 역할은 이렇게 나뉜다.

| 코드 | 역할 |
|---|---|
| `timeout.cancel(false)` | 그 timeout을 실행하지 않도록 상태 전환 |
| `setRemoveOnCancelPolicy(true)` | 취소 시 queue에서도 바로 정리하려는 정책 |
| `scheduler.purge()` | 이미 남아 있는 cancelled task를 batch cleanup |

여기서 중요한 점은 `purge()`와 `removeOnCancelPolicy(true)`가 서로 완전히 같은 기능이 아니라는 점이다.

- 하나는 cancel path의 즉시 정리 정책이다.
- 다른 하나는 나중에 실행하는 청소 작업이다.

## `purge()`가 더 필요한 순간

아래처럼 생각하면 된다.

| 질문 | `purge()`가 특히 떠오르는 상황 |
|---|---|
| 이미 취소된 task가 많이 쌓였나 | 예 |
| 지금 정책을 당장 바꾸기 어렵나 | 예 |
| 항상 즉시 제거할 필요는 없나 | 예 |
| 가끔 maintenance 성격의 cleanup이면 충분한가 | 예 |

반대로 아래라면 `removeOnCancelPolicy(true)` 쪽이 더 직접적이다.

| 질문 | `removeOnCancelPolicy(true)`가 더 자연스러운 상황 |
|---|---|
| 취소될 때마다 곧바로 queue를 가볍게 유지하고 싶은가 | 예 |
| 요청 timeout처럼 cancel 직후 retention을 줄이고 싶은가 | 예 |
| `ScheduledThreadPoolExecutor`를 직접 제어할 수 있는가 | 예 |

## 자주 하는 오해

1. `cancel()`이 성공하면 queue에서도 즉시 사라진다고 생각한다.
2. `purge()`가 취소를 대신한다고 생각한다.
3. `removeOnCancelPolicy(true)`가 공짜 cleanup이라고 생각한다.
4. `purge()`를 한 번 부르면 그 뒤부터는 항상 즉시 제거된다고 생각한다.
5. `queue.size()`를 곧바로 "앞으로 실행될 유효 task 수"로 읽는다.

특히 3번과 5번이 중요하다.

- 즉시 제거는 cancel path 비용을 당겨온다.
- queue size에는 cancelled entry가 섞여 있을 수 있다.

## 다음 문서로 이어가기

- `cancel()` 성공과 queue 잔류를 먼저 분리해서 보고 싶으면 [ScheduledFuture Cancellation Bridge](./scheduledfuture-cancel-stale-entries.md)
- delayed queue에서 stale entry가 왜 생기는지 보고 싶으면 [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md)
- 왜 즉시 제거 비용이 head pop과 다르게 느껴지는지 보고 싶으면 [DelayQueue Remove Cost Primer](./delayqueue-remove-cost-primer.md)
- timer 구조 선택까지 넓히고 싶으면 [Timing Wheel vs Delay Queue](./timing-wheel-vs-delay-queue.md)

## 한 줄 정리

`removeOnCancelPolicy(true)`는 "취소할 때 바로 치우기"이고, `purge()`는 "이미 취소된 것들을 나중에 한 번에 치우기"다.
cancelled-task retention이 보일 때는 correctness와 cleanup 시점을 분리해서 읽어야 한다.
