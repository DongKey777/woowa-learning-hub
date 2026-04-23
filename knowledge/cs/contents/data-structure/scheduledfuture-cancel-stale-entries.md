# ScheduledFuture Cancellation Stale Entries

> 한 줄 요약: `ScheduledFuture.cancel()`은 작업을 "실행하지 말라"고 표시하는 API이고, `ScheduledThreadPoolExecutor`의 queue entry를 바로 뺄지 나중에 버릴지는 `removeOnCancelPolicy`로 고르는 비용 trade-off다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)
> - [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md)
> - [DelayQueue vs PriorityQueue Timer Pitfalls](./delayqueue-vs-priorityqueue-timer-pitfalls.md)
> - [PriorityBlockingQueue Timer Misuse Primer](./priorityblockingqueue-timer-misuse-primer.md)
> - [Timing Wheel vs Delay Queue](./timing-wheel-vs-delay-queue.md)
>
> retrieval-anchor-keywords: scheduledfuture cancel stale entry, scheduledfuture cancellation, scheduledfuture cancel false, scheduledfuture cancel true, scheduledthreadpoolexecutor removeoncancelpolicy, setremoveoncancelpolicy, getremoveoncancelpolicy, remove on cancel policy, scheduled executor cancelled task retention, cancelled delayed task queue, cancelled scheduled task remains in queue, scheduled executor queue size cancelled tasks, lazy cancellation scheduled executor, lazy stale entry scheduled task, delayed work queue cancellation, mayInterruptIfRunning scheduled future, scheduled task cancellation queue cost, java scheduledexecutorservice cancellation beginner, java scheduledthreadpoolexecutor cancellation, timeout scheduledfuture cancel memory, 스케줄드퓨처 취소, scheduledfuture cancel 큐, removeOnCancelPolicy, 취소된 예약 작업 큐 잔류, 스케줄러 stale entry

## 먼저 그림부터

`ScheduledExecutorService`에서 10분 뒤 timeout을 예약했다고 하자.

```java
ScheduledFuture<?> timeout = scheduler.schedule(
    () -> closeConnection(id),
    10,
    TimeUnit.MINUTES
);
```

자료구조 관점에서는 queue 안에 이런 ticket이 들어간 셈이다.

```text
[10분 뒤 실행할 closeConnection ticket]
```

그런데 2초 뒤 응답이 도착하면 timeout은 필요 없어질 수 있다.

```java
timeout.cancel(false);
```

초보자가 여기서 가장 자주 헷갈리는 지점은 이것이다.

> `cancel()`은 "작업을 실행하지 말라"는 상태 변경이지, 항상 "queue 안 ticket을 즉시 물리적으로 제거한다"는 뜻은 아니다.

즉 머릿속 그림은 이렇게 잡는 편이 안전하다.

```text
cancel 전: [10분 뒤 실행할 ticket]
cancel 후: [취소 표시가 붙은 ticket]  // queue에 잠시 남을 수 있음
```

이 취소된 ticket이 바로 없어지지 않고 queue 안에 남아 있는 상태를 이 문서에서는 **stale entry**라고 부른다.

## API와 queue 동작은 층이 다르다

`ScheduledFuture.cancel()`을 호출하면 Java API 관점에서는 future 상태가 바뀐다.

| 상황 | `cancel(...)`의 의미 |
|---|---|
| 아직 실행 전 | 실행되지 않도록 취소를 시도한다 |
| 이미 완료됨 | 보통 취소에 실패한다 |
| 이미 실행 중 | `mayInterruptIfRunning` 값에 따라 interrupt 시도 여부가 갈린다 |
| 반복 작업 | 이후 반복 실행이 더 진행되지 않도록 취소한다 |

하지만 내부 queue 관점에서는 질문이 하나 더 남는다.

> 취소된 delayed task entry를 queue에서 지금 바로 뺄까, 아니면 나중에 head로 올라왔을 때 버릴까?

이것은 correctness보다 **queue 비용 배치**에 가까운 문제다.  
취소된 작업이 실제로 실행되지 않도록 하는 것과, 취소된 entry를 queue 메모리에서 언제 제거하는 것은 같은 말이 아니다.

## 기본 mental model: lazy stale entry

`ScheduledThreadPoolExecutor`는 취소된 delayed task를 queue에 잠시 남겨 둘 수 있다.  
이때 worker가 나중에 그 entry를 만나면 "이미 취소됐네"라고 확인하고 실행하지 않는다.

```text
t=0s      10분 뒤 timeout 예약
t=2s      응답 도착, timeout.cancel(false)
t=10m     취소된 timeout entry가 head 근처로 올라옴
worker    cancelled 상태 확인 후 실행하지 않고 버림
```

이 방식은 lazy cancellation이다.

| 관점 | lazy 방식의 효과 |
|---|---|
| correctness | 취소 상태를 확인하므로 작업은 실행되지 않는다 |
| cancel 호출 비용 | queue 중간에서 찾아 빼지 않아도 되어 싸질 수 있다 |
| queue 크기 | 취소된 entry가 delay가 끝날 때까지 남을 수 있다 |
| 메모리 | 장기 timer가 많이 취소되면 retention이 보일 수 있다 |
| 모니터링 | `queue.size()`가 실제 유효 작업 수보다 크게 느껴질 수 있다 |

핵심은 "lazy라서 작업이 실행된다"가 아니다.  
**lazy라서 실행은 막되, queue 정리는 뒤로 미룬다**가 더 정확하다.

## `removeOnCancelPolicy`는 무엇을 바꾸나

`ScheduledThreadPoolExecutor`를 직접 쓰면 취소 시 제거 정책을 켤 수 있다.

```java
ScheduledThreadPoolExecutor scheduler =
    new ScheduledThreadPoolExecutor(4);

scheduler.setRemoveOnCancelPolicy(true);
```

이 정책을 켜면 `cancel()`된 delayed task를 work queue에서 즉시 제거하는 쪽으로 동작한다.  
초보자용으로 말하면 "취소 표시만 해 두고 나중에 버리기" 대신 "취소할 때 queue에서도 빼기"에 가깝다.

| 정책 | queue 처리 감각 | 장점 | 비용 |
|---|---|---|---|
| `removeOnCancelPolicy = false` | 취소된 entry가 delay 만료 전까지 남을 수 있다 | cancel hot path가 단순하다 | stale entry, 메모리 retention, `queue.size()` 착시가 생길 수 있다 |
| `removeOnCancelPolicy = true` | 취소 시 queue에서도 제거한다 | queue가 유효 작업 수에 더 가까워진다 | cancel 시점에 queue 제거 비용과 lock 경쟁이 올 수 있다 |

그래서 이 옵션은 "무조건 켜야 하는 정답"이라기보다 workload 선택이다.

| workload 신호 | 먼저 생각할 방향 |
|---|---|
| 예약은 많지만 취소가 거의 없다 | 기본 lazy 정책도 충분할 수 있다 |
| 긴 delay 작업을 많이 예약하고 대부분 곧 취소한다 | `removeOnCancelPolicy(true)` 검토 |
| timeout을 요청마다 만들고 성공 응답 때 취소한다 | 취소된 장기 timeout retention을 관찰해야 한다 |
| 취소 호출이 매우 뜨거운 hot path다 | 즉시 제거 비용이 latency에 들어오는지 확인 |
| 수십만 timeout churn이 계속된다 | heap 기반 scheduler보다 [Timing Wheel vs Delay Queue](./timing-wheel-vs-delay-queue.md)까지 비교 |

## `mayInterruptIfRunning`과 헷갈리지 말기

`cancel(true)`와 `cancel(false)`의 boolean은 queue 제거 정책이 아니다.

```java
future.cancel(false); // 이미 실행 중이면 interrupt하지 않음
future.cancel(true);  // 이미 실행 중이면 interrupt를 시도할 수 있음
```

이 값은 **실행 중인 작업을 interrupt할지**에 관한 신호다.  
취소된 scheduled entry를 queue에서 즉시 제거할지 말지는 `ScheduledThreadPoolExecutor`의 `removeOnCancelPolicy` 쪽 관심사다.

| 헷갈리는 질문 | 보는 축 |
|---|---|
| 이미 실행 중인 task를 interrupt할까? | `cancel(true/false)`의 `mayInterruptIfRunning` |
| 아직 실행 전인 delayed task가 실행되지 않게 할까? | `ScheduledFuture`의 cancelled state |
| 취소된 delayed task entry를 queue에서 즉시 뺄까? | `removeOnCancelPolicy` |

## 작은 예시로 비용 보기

아래 코드는 요청 timeout을 예약했다가 응답이 오면 취소하는 흔한 형태다.

```java
class RequestTimeouts {
    private final ScheduledThreadPoolExecutor scheduler =
        new ScheduledThreadPoolExecutor(2);

    RequestTimeouts() {
        scheduler.setRemoveOnCancelPolicy(true);
    }

    ScheduledFuture<?> registerTimeout(String requestId) {
        return scheduler.schedule(
            () -> failRequest(requestId),
            30,
            TimeUnit.SECONDS
        );
    }

    void onResponse(ScheduledFuture<?> timeout) {
        timeout.cancel(false);
    }

    private void failRequest(String requestId) {
        // timeout 처리
    }
}
```

`setRemoveOnCancelPolicy(true)`를 켜지 않아도 `cancel(false)`된 timeout은 실행되지 않아야 한다.  
차이는 "30초가 될 때까지 취소된 entry가 queue 안에 남을 수 있느냐"다.

요청이 초당 1개라면 큰 문제가 아닐 수 있다.  
하지만 요청이 초당 수천 개이고 대부분 100ms 안에 응답되어 timeout이 취소된다면, 30초짜리 stale timeout entry가 많이 쌓일 수 있다.

이때 trade-off는 이렇게 읽으면 된다.

```text
lazy cancellation:
  cancel은 가볍지만, 취소된 ticket 청소가 나중으로 밀림

removeOnCancelPolicy(true):
  cancel이 queue 제거까지 부담하지만, stale ticket retention을 줄임
```

## 자주 하는 오해

1. `ScheduledFuture.cancel(false)`가 내부 queue entry를 항상 즉시 제거한다고 생각한다.
2. `cancel(true)`를 호출하면 stale entry 문제도 함께 사라진다고 생각한다.
3. `isCancelled()`가 `true`면 queue 메모리에서도 이미 사라졌다고 생각한다.
4. `queue.size()`를 "실제로 실행될 task 수"로 그대로 해석한다.
5. `removeOnCancelPolicy(true)`가 모든 scheduler 구현에 있는 공통 `ScheduledExecutorService` 기능이라고 생각한다.
6. lazy stale entry를 correctness 버그로만 보고, hot path 비용을 뒤로 미루는 선택이라는 점을 놓친다.

특히 5번이 중요하다.  
`removeOnCancelPolicy`는 `ScheduledThreadPoolExecutor`의 정책이다.  
변수 타입을 `ScheduledExecutorService`로만 들고 있다면 이 설정 API가 보이지 않는다.

## 다음 문서로 이어가기

- `ScheduledExecutorService`와 `DelayQueue` mental model 연결이 먼저 필요하면 [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)
- 직접 `DelayQueue` timer를 만들 때 `generation`으로 오래된 ticket을 거르는 흐름은 [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md)
- `PriorityQueue`, `PriorityBlockingQueue`, `DelayQueue` 중 무엇을 써야 할지 헷갈리면 [DelayQueue vs PriorityQueue Timer Pitfalls](./delayqueue-vs-priorityqueue-timer-pitfalls.md)
- 취소 churn이 커져 heap 자체가 부담되면 [Timing Wheel vs Delay Queue](./timing-wheel-vs-delay-queue.md)

## 꼬리질문

> Q: `ScheduledFuture.cancel(false)`를 호출하면 작업은 어떻게 되나요?
> 의도: Future 상태와 실행 여부를 먼저 분리하는지 확인
> 핵심: 아직 실행 전이면 실행되지 않도록 취소된다. 다만 내부 delayed queue entry가 즉시 제거되는지는 별도 정책이다.

> Q: `removeOnCancelPolicy(true)`는 무엇을 위해 켜나요?
> 의도: correctness 옵션이 아니라 queue 정리 비용 배치 옵션임을 이해하는지 확인
> 핵심: 취소된 delayed task를 queue에 오래 남기지 않고 cancel 시점에 제거해 stale entry retention을 줄이기 위해 켠다.

> Q: `cancel(true)`와 `removeOnCancelPolicy(true)`의 관심사는 어떻게 다른가요?
> 의도: interrupt와 queue cleanup을 구분하는지 확인
> 핵심: `cancel(true)`의 boolean은 실행 중 task interrupt 시도 여부이고, `removeOnCancelPolicy`는 취소된 scheduled entry를 queue에서 즉시 제거할지에 관한 정책이다.

## 한 줄 정리

`ScheduledFuture.cancel()`은 "이 예약 작업을 실행하지 말라"는 상태 변경이고, 취소된 delayed queue entry를 바로 치울지 lazy하게 나중에 버릴지는 `ScheduledThreadPoolExecutor`의 `removeOnCancelPolicy`로 조절하는 queue-cost trade-off다.
