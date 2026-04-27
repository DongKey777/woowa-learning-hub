# Mutable Priority Stale Ticket Pattern

> 한 줄 요약: heap 안에 들어간 항목의 priority를 제자리에서 바꾸지 말고, 새 priority로 새 ticket을 넣은 뒤 예전 ticket은 `stale`로 버리는 쪽이 Java `PriorityQueue`에서 가장 안전한 기본 패턴이다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../algorithm/backend-algorithm-starter-pack.md)


retrieval-anchor-keywords: mutable priority stale ticket pattern basics, mutable priority stale ticket pattern beginner, mutable priority stale ticket pattern intro, data structure basics, beginner data structure, 처음 배우는데 mutable priority stale ticket pattern, mutable priority stale ticket pattern 입문, mutable priority stale ticket pattern 기초, what is mutable priority stale ticket pattern, how to mutable priority stale ticket pattern
> 관련 문서:
> - [Java PriorityQueue Pitfalls](./java-priorityqueue-pitfalls.md)
> - [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md)
> - [DelayQueue vs PriorityQueue Timer Pitfalls](./delayqueue-vs-priorityqueue-timer-pitfalls.md)
> - [PriorityBlockingQueue Timer Misuse Primer](./priorityblockingqueue-timer-misuse-primer.md)
> - [Heap vs Priority Queue vs Ordered Map Beginner Bridge](./heap-vs-priority-queue-vs-ordered-map-beginner-bridge.md)
>
> retrieval-anchor-keywords: mutable priority stale ticket pattern, priority change after enqueue, priorityqueue stale ticket, mutable heap key java, java priorityqueue priority update, java priorityqueue reschedule, java priorityqueue stale entry, scheduler stale ticket, duplicate push stale skip, versioned ticket heap, immutable ticket priority queue, priorityqueue change priority safely, priorityqueue remove and reinsert, heap key mutation bug, latest version map heap, task reprioritization queue, reprioritize without decrease key, beginner priority queue update, 우선순위 변경 stale ticket, 힙 키 변경 금지, priorityqueue 재우선순위화, 오래된 티켓 버리기

## 먼저 그림부터

우선순위 큐를 "가장 급한 ticket이 맨 위에 오는 상자"라고 생각하면 쉽다.

1. 작업 A를 priority `5`로 넣는다.
2. 나중에 A의 priority를 `1`로 바꾸고 싶어진다.
3. 초보자는 종종 "그럼 queue 안 객체의 필드만 `1`로 바꾸면 되지 않나?"라고 생각한다.

여기서 핵심 오해가 생긴다.

> heap은 "들어갈 때의 정렬 기준"으로 자리를 잡는다.
> 안에 들어간 뒤 key가 바뀌어도 스스로 다시 줄을 서지 않는다.

즉 priority가 바뀐 작업을 다룰 때 가장 안전한 기본 mental model은 이것이다.

- queue 안 ticket은 "그 시점 우선순위의 스냅샷"이다
- priority가 바뀌면 기존 ticket을 직접 고치지 않는다
- 새 priority를 담은 새 ticket을 하나 더 넣는다
- 나중에 예전 ticket이 나오면 `stale`인지 확인하고 버린다

## 빠른 선택표

| 지금 상황 | 먼저 고를 기본 패턴 | 이유 |
|---|---|---|
| priority가 거의 안 바뀌고 항목 수도 작다 | `remove` 후 `offer` 재삽입 | 단순하고 이해하기 쉽다 |
| priority 변경이 자주 일어나고 exact handle 제거가 비싸다 | 새 ticket 추가 + stale skip | Java `PriorityQueue`에서 흔한 안전 기본값이다 |
| "항상 최신 priority만 유효"한 scheduler/task queue다 | `taskId -> latest version` 맵 + immutable ticket | worker가 오래된 ticket을 숫자로 판정할 수 있다 |
| priority 변경보다 `floor/ceiling/range` 조회가 더 중요하다 | `TreeMap` 같은 ordered map 재검토 | 질문 자체가 heap보다 map에 더 가깝다 |

초급자 기준으로는 이렇게 외우면 충분하다.

```text
queue 안 값을 고치지 말고
새 표를 넣고
오래된 표는 나중에 버린다
```

## 1. 왜 제자리 수정이 위험한가

아래 코드는 겉보기에 그럴듯하지만 위험하다.

```java
Task task = new Task("A", 5);
PriorityQueue<Task> pq =
    new PriorityQueue<>(Comparator.comparingInt(Task::priority));

pq.offer(task);
task.setPriority(1); // 이미 heap 안에 들어간 뒤 필드 변경
```

문제는 `setPriority(1)`이 heap 재정렬을 자동으로 일으키지 않는다는 점이다.

| 초보자 기대 | 실제 동작 |
|---|---|
| priority가 작아졌으니 곧바로 head로 올라갈 것이다 | 내부 배열은 그대로일 수 있다 |
| `peek()`가 바로 새 priority 기준 최솟값을 보여 줄 것이다 | 예전 위치 때문에 틀린 head가 남을 수 있다 |
| 객체 하나만 바꿨으니 안전하다 | heap 불변식이 깨진 채로 동작할 수 있다 |

그래서 Java `PriorityQueue`에서는 "mutable key를 제자리에서 바꾸기"를 피하는 쪽이 기본이다.

## 2. 가장 안전한 입문 패턴: immutable ticket + 최신 버전 표식

priority가 바뀌면 새 ticket을 넣고, 바깥에서 "이 작업의 최신 버전"만 따로 추적한다.

| 구성 요소 | 역할 |
|---|---|
| `Ticket(taskId, version, priority)` | enqueue 시점 스냅샷 |
| `latestVersionByTask` | 각 task의 최신 우선순위 버전 |
| `pq.offer(new Ticket(...))` | priority 변경 시 새 스냅샷 추가 |
| `poll()` 후 version 비교 | 오래된 ticket을 stale로 폐기 |

예를 들어 scheduler가 "숫자가 작을수록 더 급함"이라고 하자.

```text
t=0  A를 priority 5로 넣음        -> A#1(p=5)
t=1  A를 priority 1로 올림       -> A#2(p=1) 추가
t=2  worker가 A#1을 꺼냄         -> latest는 version 2, 그래서 stale
t=3  worker가 A#2를 꺼냄         -> 최신 ticket이므로 실행
```

핵심은 `A#1`을 고쳐 쓰지 않았다는 점이다.
예전 표는 남아 있어도 "최신 표가 아님"으로 처리하면 된다.

## 3. Java 예시

```java
import java.util.Comparator;
import java.util.HashMap;
import java.util.Map;
import java.util.PriorityQueue;

record Ticket(String taskId, long version, int priority, Runnable job) {}

public final class MutablePriorityScheduler {
    private final PriorityQueue<Ticket> pq = new PriorityQueue<>(
        Comparator.<Ticket>comparingInt(Ticket::priority)
            .thenComparingLong(Ticket::version)
    );
    private final Map<String, Long> latestVersionByTask = new HashMap<>();

    public void upsert(String taskId, int priority, Runnable job) {
        long nextVersion = latestVersionByTask.getOrDefault(taskId, 0L) + 1L;
        latestVersionByTask.put(taskId, nextVersion);
        pq.offer(new Ticket(taskId, nextVersion, priority, job));
    }

    public void runNext() {
        while (!pq.isEmpty()) {
            Ticket ticket = pq.poll();
            long latestVersion = latestVersionByTask.getOrDefault(ticket.taskId(), -1L);

            if (ticket.version() != latestVersion) {
                continue; // stale ticket
            }

            latestVersionByTask.remove(ticket.taskId(), ticket.version());
            ticket.job().run();
            return;
        }
    }
}
```

이 코드에서 초보자가 꼭 붙여야 할 감각은 아래다.

- `Ticket`은 immutable 스냅샷이다
- priority가 바뀌어도 기존 `Ticket`을 수정하지 않는다
- 새 version을 하나 더 넣는다
- worker는 `poll()` 뒤에 "이게 최신 표인가?"만 확인한다

## 4. `remove + 재삽입`과 무엇이 다른가

priority 변경을 처리하는 방법은 꼭 하나만 있는 것은 아니다.

| 방식 | 언제 괜찮나 | 주의점 |
|---|---|---|
| 기존 항목 `remove` 후 새 priority로 `offer` | 항목 수가 작고 변경 횟수가 적을 때 | Java `PriorityQueue.remove(Object)`는 대상 탐색 비용이 든다 |
| 객체 필드만 직접 수정 | 거의 권장되지 않음 | heap 순서가 자동으로 복구되지 않는다 |
| 새 ticket 추가 후 stale skip | 변경이 잦거나 scheduler 루프가 분명할 때 | queue 안에 오래된 ticket이 잠시 남는다 |

입문자에게는 보통 세 번째가 더 안정적인 기본값이다.

이유는 간단하다.

- key mutation 버그를 피하기 쉽다
- `decrease-key` 같은 전용 연산이 없어도 된다
- Dijkstra, timer reschedule, retry scheduler처럼 이미 널리 쓰는 사고방식과 맞는다

## 5. 자주 헷갈리는 지점

- "객체 참조를 잡고 있으니 필드만 바꾸면 heap도 알겠지" -> 아니다. heap은 스스로 다시 정렬하지 않는다.
- "예전 ticket이 queue에 남아 있으면 무조건 버그 아닌가" -> 아니다. stale skip을 전제로 한 설계일 수 있다.
- "stale entry가 생기면 correctness가 깨진다" -> 최신성 검사만 있으면 correctness와 cleanup 시점을 분리할 수 있다.
- "priority queue면 항상 하나의 task는 하나의 node만 있어야 한다" -> Java에서는 같은 logical task의 여러 snapshot이 함께 있을 수 있다.

## 6. 언제 이 패턴을 떠올리면 좋은가

아래 문장을 보면 stale ticket 패턴을 먼저 떠올리면 된다.

- "큐에 넣은 뒤 우선순위가 바뀔 수 있어요"
- "같은 작업을 더 급하게 다시 넣어야 해요"
- "retry 시간을 앞당기거나 늦춰야 해요"
- "scheduler에서 기존 예약을 직접 고치지 않고 최신 예약만 유효하게 만들고 싶어요"

특히 Java `PriorityQueue`에서 `decrease-key` 같은 연산을 찾고 있다면, 많은 경우 실제 답은 "그 연산 대신 duplicate push + stale skip"이다.

## 한 줄 정리

priority가 바뀌는 작업을 heap 안에서 직접 수정하려 하지 말고, **새 priority의 immutable ticket을 다시 넣고 예전 ticket은 stale로 버리는 것**이 Java `PriorityQueue` 입문자에게 가장 안전한 기본 패턴이다.
