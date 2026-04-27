# Timer Cancellation and Reschedule Stale Entry Primer

> 한 줄 요약: `DelayQueue`를 골라도 "시간이 될 때까지 기다리기"만 해결될 뿐, 이미 queue 안에 들어간 timer를 취소하거나 다시 예약할 때는 `generation` 같은 최신성 표식과 lazy stale skip 정책을 따로 정해야 한다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../algorithm/backend-algorithm-starter-pack.md)


retrieval-anchor-keywords: timer cancellation reschedule stale entry primer basics, timer cancellation reschedule stale entry primer beginner, timer cancellation reschedule stale entry primer intro, data structure basics, beginner data structure, 처음 배우는데 timer cancellation reschedule stale entry primer, timer cancellation reschedule stale entry primer 입문, timer cancellation reschedule stale entry primer 기초, what is timer cancellation reschedule stale entry primer, how to timer cancellation reschedule stale entry primer
> 관련 문서:
> - [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)
> - [DelayQueue Repeating Task Primer](./delayqueue-repeating-task-primer.md)
> - [ScheduledFuture Cancellation Bridge](./scheduledfuture-cancel-stale-entries.md)
> - [DelayQueue Remove Cost Primer](./delayqueue-remove-cost-primer.md)
> - [DelayQueue Delayed Contract Primer](./delayqueue-delayed-contract-primer.md)
> - [DelayQueue vs PriorityQueue Timer Pitfalls](./delayqueue-vs-priorityqueue-timer-pitfalls.md)
> - [Java PriorityQueue Pitfalls](./java-priorityqueue-pitfalls.md)
> - [Mutable Priority Stale Ticket Pattern](./mutable-priority-stale-ticket-pattern.md)
> - [Timing Wheel vs Delay Queue](./timing-wheel-vs-delay-queue.md)
>
> retrieval-anchor-keywords: timer cancellation stale entry, timer reschedule stale entry, delayqueue cancellation, delayqueue reschedule, delayqueue stale entry, java delayqueue cancellation, java delayqueue reschedule, delayed task cancellation, delayed task reschedule, scheduledfuture cancel stale entry, scheduledthreadpoolexecutor removeoncancelpolicy, removeOnCancelPolicy, stale timer ticket, cancelled timer ticket, lazy cancellation timer, immediate remove timer, remove vs lazy cancellation, generation token scheduler, latest generation timer, cancelled flag delayqueue, generation flag delayqueue, version token timer, latest wins timer, lazy stale skip, stale skip worker loop, heap stale entry timer, mutable deadline delayqueue, deadline reschedule heap, self rescheduling job cancel, repeating task stale ticket, periodic reschedule stale ticket, scheduledexecutorservice cancellation mental model, beginner timer cancellation, delayqueue remove cost, heap arbitrary remove timer, 타이머 취소 stale entry, delayqueue 취소, delayqueue 재예약, timer stale ticket, lazy cancellation 타이머, generation 플래그, 최신 예약만 실행

## 먼저 그림부터

timer를 "알람 ticket 상자"로 생각하면 쉽다.

1. `10초 뒤 실행`이라는 ticket을 하나 만든다.
2. `DelayQueue`는 가장 빠른 ticket을 앞에 두고, 시간이 될 때까지 worker를 기다리게 한다.
3. 시간이 되면 worker가 ticket을 꺼내 실행한다.

여기까지는 `DelayQueue`가 잘 도와준다.

하지만 아래 질문은 다른 문제다.

- 그 알람이 필요 없어졌다면, 상자 안의 ticket을 어떻게 없앨까?
- 같은 작업을 `10초 뒤`에서 `30초 뒤`로 바꾸려면, 이미 들어간 ticket을 어떻게 바꿀까?
- worker가 오래된 ticket을 꺼냈을 때 "이건 최신 예약이 아니다"를 어떻게 알아볼까?

`DelayQueue`는 **deadline까지 기다리는 계약**을 준다.
하지만 **상자 중간에 들어 있는 특정 ticket을 싸게 찾아 고치거나 지우는 계약**까지 주지는 않는다.

초보자에게 가장 안전한 mental model은 이것이다.

- queue 안 ticket은 "지금 예약 상태의 스냅샷"이다.
- cancel/reschedule은 그 스냅샷을 직접 고치기보다, "이 스냅샷은 더 이상 최신이 아님"을 바깥 상태로 표시하는 쪽에 가깝다.
- worker는 ticket을 꺼낸 뒤 마지막으로 "이 스냅샷이 아직 최신인가?"를 검사해야 한다.

## 1. `DelayQueue`를 골라도 남는 문제

| 필요한 동작 | `DelayQueue`가 직접 해결하나 | 이유 |
|---|---|---|
| 가장 이른 deadline을 head에 둔다 | 예 | `Delayed.compareTo()` 기준으로 정렬한다 |
| head 시간이 아직 미래면 기다린다 | 예 | `take()`가 expired head만 반환한다 |
| queue 중간의 특정 timer를 싸게 삭제한다 | 아니다 | heap은 arbitrary remove가 주 관심사가 아니다 |
| queue 안 ticket의 deadline을 제자리에서 바꾼다 | 아니다 | heap 순서가 자동으로 다시 잡히지 않는다 |
| 오래된 예약인지 최신 예약인지 판단한다 | 아니다 | `cancelled`, `generation` 같은 상태를 직접 설계해야 한다 |

초보자용 핵심은 이것이다.

> `DelayQueue`는 "언제 꺼낼까"를 도와주지만, "이 ticket이 아직 유효한가"는 애플리케이션이 판단해야 한다.

## 2. 취소는 즉시 제거와 lazy skip 사이의 선택이다

예를 들어 RPC 요청 timeout을 등록했다고 하자.

```text
t=0s   요청 A 전송, timeout ticket을 10초 뒤로 등록
t=2s   응답 도착, timeout은 이제 필요 없음
t=10s  오래된 timeout ticket이 head로 올라옴
```

응답이 이미 왔으니 timeout 작업은 실행되면 안 된다.
이때 보통 두 선택지가 있다.

| 방식 | 어떻게 처리하나 | 장점 | 단점 |
|---|---|---|---|
| 즉시 제거 | 취소 시점에 queue에서 ticket을 찾아 `remove`한다 | queue 안 쓰레기가 줄어든다 | 탐색 비용과 lock 경쟁이 취소 경로로 온다 |
| lazy cancellation | ticket에 `cancelled = true`만 표시하고, 나중에 worker가 꺼낼 때 버린다 | 취소 경로가 단순하고 빠르다 | cancelled ticket이 만료 시각까지 queue 안에 남을 수 있다 |

같은 논리 task를 다시 살리지 않는 **순수 cancel만** 있다면, ticket-local `cancelled` 플래그만으로도 충분할 때가 있다.

여기서 즉시 제거가 왜 "heap root 하나 빼기"와 다른 비용 모양인지 짧게 잡고 싶다면 [DelayQueue Remove Cost Primer](./delayqueue-remove-cost-primer.md)를 먼저 보고 돌아오면 된다.
timer queue의 `remove(ticket)`는 exact handle을 들고 있더라도, 보통 head removal과는 다른 탐색/동등성 고민이 붙는다.

lazy cancellation을 쓰면 worker는 이런 순서로 생각한다.

```java
while (true) {
    TimerTicket ticket = queue.take();
    if (ticket.isCancelled()) {
        continue; // stale entry
    }
    ticket.run();
}
```

여기서 stale entry는 "queue에는 남아 있지만 이제 실행하면 안 되는 오래된 ticket"이다.

## 3. 그런데 재예약이 들어오면 `cancelled` 하나로는 부족할 수 있다

초급자가 가장 많이 헷갈리는 지점이 여기다.

```text
t=0s   작업 A를 10초 뒤로 예약한다
t=2s   A를 취소한다
t=3s   A를 다시 30초 뒤로 예약한다
t=10s  예전 10초 ticket이 queue head로 올라온다
```

만약 worker가 shared `cancelled` 플래그만 보면, `t=3s`의 재예약이 `cancelled = false`를 다시 만들 수 있다.
그러면 `t=10s`에 나온 예전 ticket도 "지금은 cancelled가 아니네?"라고 잘못 판단할 수 있다.

| 체크 방식 | 순수 cancel만 있나 | cancel 뒤 reschedule도 있나 | 부족해지는 지점 |
|---|---|---|---|
| ticket 하나에만 `cancelled` 저장 | 대체로 된다 | 자주 위험하다 | 예전 ticket과 새 ticket을 구분할 버전 정보가 없다 |
| `taskId -> latest generation` 저장 | 된다 | 된다 | worker가 "최신 예약인가"를 숫자로 비교할 수 있다 |

핵심은 이것이다.

> `cancelled`는 "실행하면 안 됨"을 말하기 쉽지만, `generation`은 "이 ticket이 최신 예약인가"를 구분해 준다.

같은 logical task를 "항상 최신 예약 하나만 유효"하게 만들고 싶다면, boolean보다 `generation`이나 version token이 더 안전하다.
반복 작업이 실행 후 스스로 다음 ticket을 다시 넣는 구조라면, 이 generation 검사가 stale self-rescheduling 버그를 막는 마지막 안전장치가 된다. 이 흐름만 따로 붙여 보고 싶으면 [DelayQueue Repeating Task Primer](./delayqueue-repeating-task-primer.md)를 먼저 보고 돌아와도 된다.

## 4. 재예약은 새 ticket을 넣고 예전 ticket을 stale로 만든다

reschedule에서 가장 위험한 실수는 queue 안 ticket의 deadline 필드를 직접 바꾸는 것이다.

```text
나쁜 직관: 기존 ticket.runAt = now + 30초로 바꾸면 되겠지?
```

heap은 이미 들어간 원소의 key가 바뀌었다고 해서 스스로 다시 정렬되지 않는다.
그래서 보통은 이렇게 한다.

1. 새 deadline으로 새 ticket을 만든다.
2. 작업 id의 최신 `generation`을 증가시킨다.
3. 취소만 할 때도 예전 ticket을 무효화하려면 `generation`을 한 번 올린다.
4. worker가 ticket을 꺼냈을 때 generation이 최신인지 확인한다.
5. 최신이 아니면 stale entry로 버린다.

흐름은 아래처럼 볼 수 있다.

| 시점 | 작업 id | ticket | 최신 generation | worker 판단 |
|---|---|---|---:|---|
| 처음 등록 | `A` | `A#g1`, 10초 뒤 | 1 | 아직 모름 |
| 취소 | `A` | queue 안에는 여전히 `A#g1` | 2 | `g1`은 이제 stale |
| 재예약 | `A` | `A#g3`, 30초 뒤 추가 | 3 | `g1`을 포함한 이전 ticket은 모두 오래됨 |
| 10초 도달 | `A` | `A#g1` 꺼냄 | 3 | `1 != 3`, 버림 |
| 30초 도달 | `A` | `A#g3` 꺼냄 | 3 | 실행 가능 |

Java에서 많이 쓰는 최소 안전 패턴은 "queue에는 immutable ticket, 바깥에는 latest generation map" 조합이다.

## 4. 재예약은 새 ticket을 넣고 예전 ticket을 stale로 만든다 (계속 2)

```java
ConcurrentHashMap<String, Long> latestGeneration = new ConcurrentHashMap<>();
DelayQueue<TimerTicket> queue = new DelayQueue<>();

long nextGeneration(String taskId) {
    return latestGeneration.compute(taskId, (id, current) ->
        current == null ? 1L : current + 1L
    );
}

void scheduleOrReschedule(String taskId, long delayNanos, Runnable job) {
    long generation = nextGeneration(taskId);
    long deadlineNanos = System.nanoTime() + delayNanos;
    queue.offer(new TimerTicket(taskId, generation, deadlineNanos, job));
}

void cancel(String taskId) {
    latestGeneration.computeIfPresent(taskId, (id, current) -> current + 1L);
}

void workerLoop() throws InterruptedException {
    while (true) {
        TimerTicket ticket = queue.take();
        long latest = latestGeneration.getOrDefault(ticket.taskId(), -1L);

        if (ticket.generation() != latest) {
            continue; // stale: cancelled or rescheduled
        }

        try {
            ticket.job().run();
        } finally {
            latestGeneration.remove(ticket.taskId(), ticket.generation());
        }
    }
}
```

실제 구현에서는 `TimerTicket`이 [DelayQueue Delayed Contract Primer](./delayqueue-delayed-contract-primer.md)의 패턴처럼 `deadlineNanos`로 `getDelay()`와 `compareTo()`를 맞춰야 한다.

이 코드에서 역할은 이렇게 나뉜다.

## 4. 재예약은 새 ticket을 넣고 예전 ticket을 stale로 만든다 (계속 3)

| 구성 요소 | 역할 |
|---|---|
| `TimerTicket(taskId, generation, deadline)` | "그 시점 예약의 스냅샷" |
| `latestGeneration` | 각 task의 최신 예약 번호 |
| `cancel(taskId)` | queue 안 원소를 직접 지우지 않고 예전 ticket을 무효화 |
| worker의 `generation` 비교 | lazy stale skip으로 오래된 ticket 폐기 |

이 패턴의 장점은 취소와 재예약이 같은 규칙으로 합쳐진다는 점이다.

- cancel: 새 ticket 없이 generation만 올려서 예전 ticket을 무효화한다.
- reschedule: generation을 올리고 새 ticket을 넣는다.
- worker: "꺼낸 ticket의 generation이 최신 번호와 같은가?"만 본다.

## 5. stale entry가 왜 비용이 되나

lazy 방식은 취소와 재예약을 단순하게 만든다.
대신 오래된 ticket이 queue 안에 남는다.

| 상황 | 무슨 일이 생기나 |
|---|---|
| 1시간 뒤 timeout을 취소했다 | 그 ticket은 즉시 제거하지 않으면 최대 1시간 동안 queue 크기에 남을 수 있다 |
| 같은 작업을 100번 재예약했다 | 최신 ticket 1개와 오래된 ticket 99개가 함께 있을 수 있다 |
| 오래된 ticket들이 같은 시각에 몰렸다 | worker가 한동안 `take -> stale 확인 -> 버림`을 반복할 수 있다 |
| `queue.size()`를 모니터링한다 | 실제 유효 timer 수보다 크게 보일 수 있다 |

그래서 lazy cancellation은 공짜가 아니다.

- 취소 hot path는 싸진다.
- 대신 heap 메모리와 만료 시점 cleanup 비용이 늘 수 있다.
- stale entry가 너무 많으면 timer 구조 선택을 다시 봐야 한다.

대규모 timeout churn까지 고민해야 하면 [Timing Wheel vs Delay Queue](./timing-wheel-vs-delay-queue.md)로 넘어가면 된다.
이 문서는 그 전 단계인 "`DelayQueue`를 골랐는데 왜 stale entry가 아직 남지?"를 잡기 위한 입문 bridge다.

## 6. 빠른 선택표

| workload 신호 | 먼저 생각할 정책 |
|---|---|
| 취소가 드물고 queue 크기를 작게 유지해야 한다 | 즉시 제거를 검토한다 |
| 취소와 재예약이 자주 일어나고 hot path가 중요하다 | lazy cancellation + stale skip을 검토한다 |
| 같은 task를 최신 예약 하나로만 실행해야 한다 | `taskId -> generation` 또는 latest version token을 둔다 |
| 취소된 장기 timer가 너무 오래 쌓인다 | 주기적 cleanup, 즉시 제거, 다른 timer 구조를 검토한다 |
| 수많은 timeout이 계속 등록/취소된다 | timing wheel 계열까지 비교한다 |

## 자주 하는 오해

1. `DelayQueue`를 쓰면 cancellation도 자동으로 싸진다고 생각한다.
2. `remove(ticket)`이 항상 heap root 제거처럼 싸다고 생각한다.
3. queue 안 객체의 deadline 필드를 바꾸면 순서가 자동으로 갱신된다고 생각한다.
4. `cancelled` 표시만 했으니 queue 크기도 바로 줄어들 것이라고 생각한다.
5. worker가 stale 확인을 하지 않아도 취소된 task가 실행되지 않을 것이라고 생각한다.
6. `generation`을 단순 실행 횟수 카운터로만 보고, "최신 예약 판별용 버전"이라는 뜻을 놓친다.

특히 5번이 중요하다.
lazy cancellation을 골랐다면 **실행 직전 stale check**가 scheduler correctness의 일부다.

## 다음 문서로 이어가기

- fixed-rate / fixed-delay self-rescheduling 코드에서 stale ticket이 어디서 생기는지 보려면 [DelayQueue Repeating Task Primer](./delayqueue-repeating-task-primer.md)
- Java `ScheduledFuture.cancel()`과 `removeOnCancelPolicy`의 queue retention trade-off가 궁금하면 [ScheduledFuture Cancellation Bridge](./scheduledfuture-cancel-stale-entries.md)
- `Delayed.compareTo()`와 `getDelay()` 구현 계약이 헷갈리면 [DelayQueue Delayed Contract Primer](./delayqueue-delayed-contract-primer.md)
- `PriorityQueue`, `PriorityBlockingQueue`, `DelayQueue`의 timer 차이를 한 번에 비교하려면 [DelayQueue vs PriorityQueue Timer Pitfalls](./delayqueue-vs-priorityqueue-timer-pitfalls.md)
- Java heap에서 stale entry 사고방식을 더 넓게 보려면 [Java PriorityQueue Pitfalls](./java-priorityqueue-pitfalls.md)
- 취소 churn이 구조 선택까지 흔드는 규모라면 [Timing Wheel vs Delay Queue](./timing-wheel-vs-delay-queue.md)

## 꼬리질문

> Q: `DelayQueue`를 쓰면 cancellation 문제가 끝나나요?
> 의도: delay-aware blocking과 stale-entry 정책을 구분하는지 확인
> 핵심: 아니다. `DelayQueue`는 기다림을 처리하지만, 취소된 ticket을 즉시 제거할지 나중에 버릴지는 별도 정책이다.

> Q: reschedule할 때 queue 안 ticket의 deadline을 직접 바꾸면 왜 위험한가요?
> 의도: heap key mutation 함정을 이해하는지 확인
> 핵심: heap은 내부 원소의 key 변경을 자동으로 재정렬하지 않으므로, 새 ticket을 넣고 예전 ticket은 stale로 버리는 패턴이 안전하다.

> Q: generation token은 무엇을 막아 주나요?
> 의도: 오래된 예약과 최신 예약을 구분하는 기준을 설명할 수 있는지 확인
> 핵심: 같은 task의 예전 ticket이 나중에 head로 올라와도 최신 generation과 다르면 실행하지 않게 해 준다.

> Q: 왜 `cancelled` 플래그만 보고는 재예약을 안전하게 처리하기 어려울 수 있나요?
> 의도: boolean과 version token의 역할 차이를 구분하는지 확인
> 핵심: 재예약이 `cancelled = false`를 다시 만들면 예전 ticket도 살아난 것처럼 보일 수 있으므로, "최신 예약 번호" 같은 별도 기준이 필요하다.

## 한 줄 정리

`DelayQueue`는 timer worker가 "언제 깨어날지"를 단순하게 해 주지만, 취소와 재예약이 섞이면 오래된 ticket을 즉시 제거할지, 아니면 `generation`을 올리고 worker가 lazy stale skip으로 버릴지 선택해야 한다. 이 선택이 바로 stale-entry trade-off다.
