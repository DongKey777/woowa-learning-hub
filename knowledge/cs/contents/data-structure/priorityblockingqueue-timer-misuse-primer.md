# PriorityBlockingQueue Timer Misuse Primer

> 한 줄 요약: `PriorityBlockingQueue`는 여러 스레드가 안전하게 공유하는 priority queue일 뿐이고, deadline이 오기 전 작업을 막아 두는 timer 계약은 따로 제공하지 않는다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
> - [Java PriorityQueue Pitfalls](./java-priorityqueue-pitfalls.md)
> - [DelayQueue vs PriorityQueue Timer Pitfalls](./delayqueue-vs-priorityqueue-timer-pitfalls.md)
> - [Timing Wheel vs Delay Queue](./timing-wheel-vs-delay-queue.md)
> - [응용 자료 구조 개요](./applied-data-structures-overview.md)
>
> retrieval-anchor-keywords: priorityblockingqueue timer misuse, priorityblockingqueue timer queue, priorityblockingqueue vs delayqueue, priorityblockingqueue delay semantics, thread safe priority queue timer java, java priorityblockingqueue timer pitfalls, delay aware blocking, timer semantics, delayed task queue java, blocking queue not timer queue, future task popped too early, java timer queue beginner, scheduled executor queue semantics, priorityblockingqueue primer, 자바 PriorityBlockingQueue 타이머, thread safety와 timer semantics 차이

## 먼저 그림부터

`PriorityBlockingQueue`를 timer queue로 착각하는 가장 흔한 이유는 이름 때문이다.

- `Priority`: deadline 순으로 잘 정렬될 것 같다
- `Blocking`: 시간이 될 때까지 알아서 기다려 줄 것 같다

하지만 실제 `Blocking`의 뜻은 보통 **"queue가 비어 있으면 기다린다"**에 가깝다.  
timer queue에 필요한 것은 **"head가 아직 미래 시각이면 기다린다"**는 계약이다.

이 차이를 먼저 분리하면 거의 끝난다.

| 질문 | `PriorityBlockingQueue` | timer queue / `DelayQueue` |
|---|---|---|
| 여러 스레드가 동시에 넣고 빼도 안전한가 | 예 | 예 |
| head가 가장 이른 deadline인가 | 예 | 예 |
| queue에 원소가 있으면 `take()`가 바로 반환되는가 | 예 | 아니오 |
| head deadline 전에는 consumer가 못 가져가야 하는가 | 보장 안 함 | 보장함 |

짧게 말하면:

- `PriorityBlockingQueue`는 **thread-safe 정렬 상자**
- timer queue는 **시간이 되기 전에는 잠겨 있는 정렬 상자**

## 1. 왜 바로 꺼내지면 timer가 아닌가

timer worker가 진짜 원하는 동작은 보통 이렇다.

1. 가장 이른 deadline 작업을 본다
2. 아직 시간이 안 됐으면 기다린다
3. 시간이 되면 그때 꺼내서 실행한다

그런데 `PriorityBlockingQueue`는 2번을 해주지 않는다.

```java
record TimerTask(long deadlineNanos, Runnable job) {}

PriorityBlockingQueue<TimerTask> queue =
    new PriorityBlockingQueue<>(11, Comparator.comparingLong(TimerTask::deadlineNanos));

queue.put(new TimerTask(System.nanoTime() + 10_000_000_000L, () -> {
    System.out.println("run");
}));

TimerTask task = queue.take(); // 10초 뒤가 아니라 "지금" 반환된다.
```

이 코드는 deadline이 10초 뒤여도, queue가 비어 있지 않으므로 `take()`가 즉시 반환된다.

즉 `PriorityBlockingQueue`가 막아 주는 것은:

- empty queue에서의 경쟁
- concurrent `offer` / `poll` 충돌

막아 주지 않는 것은:

- 아직 만료되지 않은 작업의 조기 반환
- 다음 deadline까지의 정확한 sleep
- 더 이른 deadline이 새로 들어왔을 때 wait 재계산

## 2. timer queue에는 "정렬" 말고 한 가지가 더 필요하다

초보자 기준으로 timer queue는 두 층으로 보면 쉽다.

| 층 | 질문 | `PriorityBlockingQueue` |
|---|---|---|
| 정렬 층 | 가장 이른 deadline이 head인가 | 해결 |
| 시간 층 | 아직 미래면 꺼내지 말고 기다리는가 | 미해결 |

그래서 `PriorityBlockingQueue`는 **timer queue의 재료**는 될 수 있어도,  
그 자체로는 **완성된 timer semantics**가 아니다.

여기서 오해가 자주 생긴다.

> "thread-safe priority queue면 thread-safe timer queue 아닌가요?"

아니다. timer queue는 단순 공유 자료구조가 아니라 **clock-aware scheduler 계약**까지 필요하다.

## 3. 실수 구현이 왜 금방 복잡해지나

`PriorityBlockingQueue` 위에 timer를 직접 얹으면 보통 이런 보정 코드가 따라온다.

- `take()`로 future task를 꺼낸 뒤 남은 시간을 계산하고 다시 잔다
- 자는 동안 더 이른 deadline이 들어오면 깨워야 한다
- 너무 일찍 꺼낸 task를 다시 넣을지, 손에 들고 있을지 정해야 한다

즉 "`PriorityBlockingQueue` 하나면 끝"이라고 생각하고 시작해도,  
결국은 `lock + condition + earlier-deadline wakeup`을 다시 구현하게 된다.

이 지점이 바로 `DelayQueue`류 구조가 필요한 이유다.

## 4. 그럼 `PriorityBlockingQueue`는 언제 맞나

`PriorityBlockingQueue`가 틀린 구조라는 뜻은 아니다.  
다만 **timer semantics를 바깥 runtime이 이미 책임질 때** 더 자연스럽다.

예를 들면:

- 별도 scheduler thread가 주기적으로 깨어나 `peek()`로 만료 여부만 확인한다
- event loop가 자체 clock tick으로 expired task를 가져간다
- 여러 스레드가 안전하게 "deadline 순 목록"만 공유하면 된다

이 경우 `PriorityBlockingQueue`의 역할은 **thread-safe ordered container**다.  
timer 역할은 queue 바깥의 poll loop나 scheduler가 맡는다.

## 5. 무엇을 고르면 되나

| 지금 필요한 것 | 더 자연스러운 기본값 | 이유 |
|---|---|---|
| 여러 스레드가 안전하게 priority order만 공유 | `PriorityBlockingQueue` | thread safety + head ordering이면 충분하다 |
| deadline 전에는 consumer가 가져가면 안 됨 | `DelayQueue` 또는 `ScheduledExecutorService` 계열 | delay-aware blocking이 필요하다 |
| timeout 등록/취소 churn이 매우 큼 | timing wheel 계열 | heap timer보다 churn 비용을 더 잘 누를 수 있다 |

핵심 판단 문장은 이것 하나면 된다.

> "나는 thread-safe priority queue가 필요한가, 아니면 delay-aware timer queue가 필요한가?"

## 자주 하는 오해

1. `BlockingQueue`의 `blocking`이 "시간이 될 때까지 대기"라고 생각한다.
2. deadline 정렬만 있으면 timer semantics도 따라온다고 생각한다.
3. `PriorityBlockingQueue.take()`가 `DelayQueue.take()`와 비슷하게 동작할 것이라고 기대한다.
4. `PriorityBlockingQueue` 위에 조금만 코드를 얹으면 간단한 timer executor가 된다고 생각한다.

## 다음 문서로 이어가기

- Java timer loop에서 `PriorityQueue`, `PriorityBlockingQueue`, `DelayQueue` 차이를 더 보려면 [DelayQueue vs PriorityQueue Timer Pitfalls](./delayqueue-vs-priorityqueue-timer-pitfalls.md)
- heap 자체의 comparator, stale entry, mutable key 함정을 먼저 정리하려면 [Java PriorityQueue Pitfalls](./java-priorityqueue-pitfalls.md)
- timer 구조를 workload 기준으로 더 넓게 비교하려면 [Timing Wheel vs Delay Queue](./timing-wheel-vs-delay-queue.md)

## 한 줄 정리

`PriorityBlockingQueue`는 **안전한 priority queue**이고,  
timer queue는 거기에 더해 **아직 미래인 head를 숨기는 시간 계약**이 필요하다.
