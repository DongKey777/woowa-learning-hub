# Timer Priority Policy Split

> 한 줄 요약: timer queue에서는 "시간이 됐는가"와 "시간이 된 작업 중 무엇을 먼저 할 것인가"를 같은 `Delayed.compareTo()`에 억지로 넣지 말고, due-time gate와 business-priority ready queue로 나누면 버그가 줄어든다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../algorithm/backend-algorithm-starter-pack.md)


retrieval-anchor-keywords: timer priority policy split basics, timer priority policy split beginner, timer priority policy split intro, data structure basics, beginner data structure, 처음 배우는데 timer priority policy split, timer priority policy split 입문, timer priority policy split 기초, what is timer priority policy split, how to timer priority policy split
> 관련 문서:
> - [ScheduledExecutorService vs DelayQueue Bridge](./scheduledexecutorservice-vs-delayqueue-bridge.md)
> - [DelayQueue Delayed Contract Primer](./delayqueue-delayed-contract-primer.md)
> - [DelayQueue vs PriorityQueue Timer Pitfalls](./delayqueue-vs-priorityqueue-timer-pitfalls.md)
> - [PriorityBlockingQueue Timer Misuse Primer](./priorityblockingqueue-timer-misuse-primer.md)
> - [Ready Queue Starvation Primer](./ready-queue-starvation-primer.md)
> - [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md)
> - [Java PriorityQueue Pitfalls](./java-priorityqueue-pitfalls.md)
>
> retrieval-anchor-keywords: timer priority policy split, delayqueue business priority, due time gate, due-time gating, deadline gate vs business priority, delayed compareto priority misuse, delayed compareTo business priority, delayqueue priority comparator, expired task hidden by priority, scheduler priority after due, ready queue priority, java delayqueue priority scheduling, two stage scheduler, deadline then priority, delay-aware gating, business priority ordering timer, due tasks priority queue, high priority future task blocks expired task

## 먼저 그림부터

timer scheduler를 문 앞 대기실로 생각하면 쉽다.

- 첫 번째 문은 **시간 문**이다. 아직 예약 시간이 안 된 작업은 들어오면 안 된다.
- 두 번째 대기실은 **업무 우선순위 줄**이다. 이미 시간이 된 작업들끼리만 중요도를 비교한다.

`DelayQueue`의 `Delayed.compareTo()`를 업무 우선순위 줄처럼 쓰고 싶어지는 순간이 있다.
하지만 `DelayQueue`에서 queue head는 "가장 중요한 작업"이 아니라 **가장 먼저 시간이 되어야 하는 작업**이어야 한다.

짧게 말하면:

> due-time은 gate이고, business priority는 gate를 통과한 뒤의 ordering이다.

## 1. 왜 `compareTo()`에 priority를 먼저 넣으면 위험한가

아래 요구를 생각해 보자.

> 시간이 된 작업 중에서는 높은 priority를 먼저 실행하고 싶다.

이 말을 잘못 줄이면 "`Delayed.compareTo()`를 priority 기준으로 만들자"가 된다.

```java
// 잘못된 예: queue head를 business priority로 정한다.
@Override
public int compareTo(Delayed other) {
    TimerJob that = (TimerJob) other;
    return Integer.compare(that.priority, this.priority);
}
```

이제 이런 상황이 생길 수 있다.

| 작업 | due time | business priority | 지금 실행 가능? | priority 기준 위치 |
|---|---:|---:|---|---|
| A | 지금 | 1 | 예 | 뒤 |
| B | 10초 뒤 | 100 | 아니오 | 앞 |

사람 눈에는 A가 지금 실행돼야 한다.
하지만 queue head는 B가 된다.

`DelayQueue.take()`는 head인 B를 보고 "아직 10초 남았다"고 기다릴 수 있다.
그 사이 A는 이미 시간이 됐는데도 queue 안에서 숨어 버린다.

이것이 `Delayed.compareTo()`를 business priority로 오버로딩하면 깨지는 핵심이다.

## 2. `compareTo()` 안에서 priority를 써도 되는 경우

priority를 무조건 버리라는 뜻은 아니다.
다만 **deadline이 먼저**이고, priority는 tie-breaker여야 한다.

| 요구 | 안전한 `compareTo()` 축 |
|---|---|
| 가장 이른 deadline부터 실행 | `deadline -> sequence` |
| 같은 deadline끼리는 high priority 먼저 | `deadline -> priority -> sequence` |
| 시간이 된 작업 전체 중 high priority 먼저 | `DelayQueue(deadline)` + `ready PriorityQueue(priority)` |
| future high priority가 due low priority보다 먼저 head에 오게 함 | 잘못된 설계 |

`deadline -> priority`는 "같은 시각에 도착한 작업끼리"의 tie-breaker다.
"이미 시간이 된 작업들 전체에서 priority로 다시 고르기"와는 다르다.

## 3. 분리해야 하는 신호

아래 말이 나오면 `Delayed.compareTo()` 하나로 해결하려고 하지 말고 정책을 나눌 가능성이 높다.

| 요구 문장 | 분리해야 하는 이유 |
|---|---|
| "시간이 된 것들 중 VIP 먼저" | due 여부와 VIP ordering은 다른 질문이다 |
| "미래의 high priority가 현재 due 작업을 막으면 안 됨" | head는 business priority가 아니라 가장 이른 due time이어야 한다 |
| "priority가 대기 중에도 바뀔 수 있음" | heap 안 key mutation은 위험하므로 ready 단계에서 최신 priority를 읽는 편이 낫다 |
| "같은 tick에 만료된 작업을 모아 중요도 순으로 처리" | 먼저 expired 작업을 모은 뒤 별도 heap에서 정렬해야 한다 |

핵심 질문은 이것이다.

> priority가 "같은 deadline의 동점 처리"인가, 아니면 "이미 실행 가능한 작업들 사이의 업무 정책"인가?

후자라면 policy split이 더 안전하다.

## 4. 두 단계 구조로 생각하기

입문 단계에서는 아래 구조만 기억해도 충분하다.

```text
DelayQueue<TimerTicket>
  - 역할: 시간이 된 ticket만 밖으로 내보낸다
  - 정렬: runAtNanos -> sequence

PriorityQueue<ReadyJob>
  - 역할: 이미 시간이 된 job 중 무엇을 먼저 실행할지 고른다
  - 정렬: businessPriority -> sequence
```

흐름은 이렇게 된다.

1. `DelayQueue.take()`로 첫 expired ticket을 하나 꺼낸다.
2. 바로 이어서 `DelayQueue.poll()`로 지금 이미 expired인 ticket들을 더 모은다.
3. 모은 ticket을 `readyQueue`에 넣는다.
4. `readyQueue.poll()`로 business priority 순서대로 실행한다.

이 구조에서는 future high priority ticket이 `DelayQueue` head를 차지하지 못한다.
`DelayQueue`는 due-time gate만 맡고, 업무 priority는 gate를 통과한 뒤에만 적용된다.

## 5. 아주 작은 Java 모양

아래 코드는 전체 scheduler 구현이 아니라 역할 분리를 보여 주는 축소 예시다.

```java
record TimerTicket(
    long runAtNanos,
    long sequence,
    int priority,
    Runnable job
) implements Delayed {
    @Override
    public long getDelay(TimeUnit unit) {
        return unit.convert(runAtNanos - System.nanoTime(), TimeUnit.NANOSECONDS);
    }

    @Override
    public int compareTo(Delayed other) {
        TimerTicket that = (TimerTicket) other;
        int byDueTime = Long.compare(this.runAtNanos, that.runAtNanos);
        if (byDueTime != 0) {
            return byDueTime;
        }
        return Long.compare(this.sequence, that.sequence);
    }
}

PriorityQueue<TimerTicket> readyQueue =
    new PriorityQueue<>(
        Comparator.<TimerTicket>comparingInt(TimerTicket::priority).reversed()
            .thenComparingLong(TimerTicket::sequence)
    );

void workerLoop(DelayQueue<TimerTicket> delayQueue) throws InterruptedException {
    while (true) {
        TimerTicket firstDue = delayQueue.take();
        readyQueue.offer(firstDue);

        TimerTicket alsoDue;
        while ((alsoDue = delayQueue.poll()) != null) {
            readyQueue.offer(alsoDue);
        }

        while (!readyQueue.isEmpty()) {
            readyQueue.poll().job().run();
        }
    }
}
```

여기서 `TimerTicket.compareTo()`는 priority를 보지 않는다.
priority는 이미 시간이 된 ticket이 `readyQueue`에 들어간 뒤에만 쓰인다.

이 예시의 요점은 "항상 이렇게 구현하라"가 아니다.
**due-time gating과 business-priority ordering을 코드에서 다른 단계로 보이게 만들라**는 것이다.

## 6. 빠른 선택표

| 상황 | 추천 구조 | 이유 |
|---|---|---|
| 같은 deadline에서만 priority 차이가 의미 있음 | `DelayQueue`의 `compareTo(): deadline -> priority -> sequence` | priority가 tie-breaker라 계약이 깨지지 않는다 |
| due 작업들을 모아 priority 순으로 처리 | `DelayQueue(deadline)` + `ready PriorityQueue(priority)` | due gate와 업무 ordering이 분리된다 |
| thread pool, cancellation, 반복 실행까지 필요 | `ScheduledExecutorService` | 애플리케이션 레벨 기본값이다 |
| 취소/재예약이 매우 많아 stale entry가 쌓임 | timing wheel 검토 | priority split보다 timer churn 구조 문제가 더 크다 |

## 자주 하는 오해

1. `DelayQueue`의 priority는 business priority라고 생각한다.
2. `getDelay()`만 정확하면 `compareTo()`는 어떤 기준이어도 된다고 생각한다.
3. "high priority"가 "아직 시간이 안 됐어도 먼저 head에 있어야 함"이라고 착각한다.
4. `deadline -> priority`와 "due tasks 전체를 priority로 재정렬"을 같은 말로 본다.
5. priority가 자주 바뀌는데 queue 안 객체 필드를 직접 바꿔도 heap이 알아서 정렬될 것이라고 기대한다.

## 다음 문서로 이어가기

- `Delayed.compareTo()`와 `getDelay()`의 기본 계약이 먼저 흔들리면 [DelayQueue Delayed Contract Primer](./delayqueue-delayed-contract-primer.md)
- `PriorityBlockingQueue.take()`가 왜 timer 대기가 아닌지 헷갈리면 [PriorityBlockingQueue Timer Misuse Primer](./priorityblockingqueue-timer-misuse-primer.md)
- `PriorityQueue`, `PriorityBlockingQueue`, `DelayQueue`의 timer 선택 차이를 더 보려면 [DelayQueue vs PriorityQueue Timer Pitfalls](./delayqueue-vs-priorityqueue-timer-pitfalls.md)
- due task를 ready queue로 넘긴 뒤 공정성 문제가 왜 따로 남는지 보려면 [Ready Queue Starvation Primer](./ready-queue-starvation-primer.md)
- cancel/reschedule 때문에 오래된 ticket이 남는 흐름은 [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md)
- heap comparator와 stale entry 전반은 [Java PriorityQueue Pitfalls](./java-priorityqueue-pitfalls.md)

## 한 줄 정리

`DelayQueue`의 `compareTo()`는 "누가 먼저 시간이 되는가"를 지키게 두고, "시간이 된 작업 중 무엇이 더 중요한가"는 별도 ready queue나 scheduler 정책으로 옮기는 편이 안전하다.
