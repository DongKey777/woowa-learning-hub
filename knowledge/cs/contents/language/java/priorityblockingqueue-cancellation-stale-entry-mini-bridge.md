# `PriorityBlockingQueue` Cancellation/Update Mini Bridge

> 한 줄 요약: `PriorityBlockingQueue`에서 cancel이나 priority update가 들어오면, 초보자 기본값은 **queue 안 entry를 직접 고치기보다 새 entry를 넣고 예전 entry는 stale로 버리는 것**이다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: priorityblockingqueue cancellation stale entry mini bridge basics, priorityblockingqueue cancellation stale entry mini bridge beginner, priorityblockingqueue cancellation stale entry mini bridge intro, java basics, beginner java, 처음 배우는데 priorityblockingqueue cancellation stale entry mini bridge, priorityblockingqueue cancellation stale entry mini bridge 입문, priorityblockingqueue cancellation stale entry mini bridge 기초, what is priorityblockingqueue cancellation stale entry mini bridge, how to priorityblockingqueue cancellation stale entry mini bridge
> 관련 문서:
> - [Priority Update Patterns](./priority-update-patterns-treeset-treemap-priorityqueue-bridge.md)
> - [Thread Interruption and Cooperative Cancellation Playbook](./thread-interruption-cooperative-cancellation-playbook.md)
> - [PriorityBlockingQueue Timer Misuse Primer](../data-structure/priorityblockingqueue-timer-misuse-primer.md)
> - [Mutable Priority Stale Ticket Pattern](../data-structure/mutable-priority-stale-ticket-pattern.md)
> - [Java PriorityQueue Pitfalls](../data-structure/java-priorityqueue-pitfalls.md)
>
> retrieval-anchor-keywords: language-java-00124, PriorityBlockingQueue cancellation update, priorityblockingqueue duplicate entries, priorityblockingqueue stale entry, priorityblockingqueue cancel pattern, priorityblockingqueue reprioritize, priorityblockingqueue lazy deletion, priorityblockingqueue versioned entry, priorityblockingqueue remove linear cost, priorityblockingqueue cancelled task stale skip, java priorityblockingqueue update priority safely, java priorityblockingqueue duplicate ticket normal, priorityblockingqueue beginner bridge, 자바 PriorityBlockingQueue 취소, 자바 PriorityBlockingQueue 중복 엔트리, 자바 PriorityBlockingQueue stale entry, 자바 PriorityBlockingQueue 우선순위 변경

## 먼저 잡을 멘탈 모델

`PriorityBlockingQueue`를 "여러 스레드가 함께 쓰는 우선순위 inbox"로 보면 쉽다.

- inbox 안에 이미 들어간 편지를 직접 고쳐서 재정렬한다고 기대하지 않는다
- cancel이나 priority update는 "새 상태를 담은 새 편지"를 넣는 쪽에 가깝다
- 나중에 꺼낸 편지가 최신이 아니면 stale로 버린다

즉 초보자 기본값은 이것이다.

> `PriorityBlockingQueue`에서는 **중복 entry가 생길 수 있고, 그 자체가 곧 버그는 아니다.**
> 중요한 것은 `poll()`/`take()` 뒤에 "이 entry가 아직 최신인가?"를 한 번 더 확인하는 것이다.

## 한 장 비교표

| 상황 | 바로 떠올릴 기본 패턴 | 왜 이렇게 하나 |
|---|---|---|
| priority를 바꾸고 싶다 | 새 entry `offer` + 예전 entry stale 처리 | queue 안 원소 제자리 수정은 자동 재정렬을 기대하기 어렵다 |
| task를 취소하고 싶다 | shared state에서 inactive 처리 + worker가 stale skip | queue 중간의 exact entry를 항상 싸게 지우는 구조가 아니다 |
| queue 안에 같은 task가 두 번 보인다 | 중복 자체보다 "최신 판별"을 먼저 본다 | lazy update/cancel 패턴에서는 자연스럽다 |
| "취소했는데 왜 아직 남아 있지?" | queue 안 잔류와 실제 실행 여부를 분리해서 본다 | 남아 있어도 worker가 stale로 버리면 실행은 막을 수 있다 |

## cancel, duplicate, stale entry를 같이 보면 덜 헷갈린다

예를 들어 작업 `A`가 있다고 하자.

1. `A(priority=5, version=1)`을 넣는다.
2. 나중에 더 급해져서 `A(priority=1, version=2)`를 다시 넣는다.
3. 그 뒤 아예 취소해서 현재 상태를 `inactive`로 바꾼다.

이때 queue 안에는 예전 `A` entry들이 남아 있을 수 있다.
초보자는 여기서 "중복이니까 잘못됐다"고 느끼기 쉽지만, 실제 판단 기준은 더 단순하다.

- queue 안에 남아 있는가?
- 지금 꺼낸 entry가 **최신 version**인가?
- 그 task가 **현재 active 상태**인가?

마지막 두 질문에 `아니오`가 나오면 stale로 버리면 된다.

즉 cancel의 핵심은 "queue에서 흔적을 0으로 만드는 것"이 아니라,
"worker가 더 이상 실행하지 못하게 만드는 것"이다.

## 초보자 기본 예시

```java
import java.util.Comparator;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.PriorityBlockingQueue;

record TaskState(long version, boolean active) {}
record QueueEntry(String taskId, int priority, long version, Runnable job) {}

public final class TaskInbox {
    private final PriorityBlockingQueue<QueueEntry> queue =
            new PriorityBlockingQueue<>(11,
                    Comparator.<QueueEntry>comparingInt(QueueEntry::priority)
                            .thenComparingLong(QueueEntry::version));

    private final ConcurrentHashMap<String, TaskState> stateByTask =
            new ConcurrentHashMap<>();

    public void upsert(String taskId, int priority, Runnable job) {
        TaskState next = stateByTask.compute(taskId, (id, oldState) -> {
            long nextVersion = oldState == null ? 1L : oldState.version() + 1L;
            return new TaskState(nextVersion, true);
        });

        queue.offer(new QueueEntry(taskId, priority, next.version(), job));
    }

    public void cancel(String taskId) {
        stateByTask.computeIfPresent(taskId, (id, oldState) ->
                new TaskState(oldState.version() + 1L, false));
    }

    public QueueEntry takeLive() throws InterruptedException {
        while (true) {
            QueueEntry entry = queue.take();
            TaskState state = stateByTask.get(entry.taskId());

            if (state == null) {
                continue; // 이미 사라진 task
            }

## 초보자 기본 예시 (계속 2)

if (!state.active()) {
                continue; // 취소된 뒤 남아 있던 stale entry
            }
            if (state.version() != entry.version()) {
                continue; // update 전에 넣어 둔 오래된 entry
            }

            return entry;
        }
    }
}
```

이 코드에서 beginner가 꼭 가져갈 포인트는 세 가지다.

- `update`는 기존 entry 수정이 아니라 `version` 증가 + 새 entry 추가다
- `cancel`은 지금 유효한 버전을 한 번 더 넘기고 `active=false`로 만든다
- worker는 `take()` 직후 `active`와 `version`을 같이 검사한다

## `remove()`로 바로 지우면 안 되나요?

가능은 하다.
하지만 beginner 기본값으로는 바로 그 방향을 추천하지 않는 편이 안전하다.

| 질문 | beginner 기본 답 |
|---|---|
| `PriorityBlockingQueue.remove(entry)`가 있지 않나 | 있다 |
| 그걸 cancel/update 기본 패턴으로 써도 되나 | 보통은 아니다 |
| 이유는 | exact entry를 찾는 비용, 동등성 기준, concurrent update 타이밍까지 함께 신경 써야 하기 때문이다 |

즉 처음에는 이렇게 구분하면 충분하다.

- "지금 당장 queue에서 없애는 것"과
- "실제로 실행되지 못하게 막는 것"

`PriorityBlockingQueue`에서는 두 번째가 더 중요한 경우가 많다.

## 자주 하는 오해

- `PriorityBlockingQueue`가 thread-safe니까 priority update도 자동 안전하다고 생각한다.
- queue 안 중복 entry를 보면 무조건 데이터 버그라고 생각한다.
- cancel 후에도 queue 크기가 바로 안 줄면 취소가 실패했다고 생각한다.
- `take()`로 꺼냈으면 바로 실행해도 된다고 생각한다.
- deadline 기반 대기까지 기대한다. 이건 [PriorityBlockingQueue Timer Misuse Primer](../data-structure/priorityblockingqueue-timer-misuse-primer.md) 쪽 질문이다.

## 한 줄 정리

`PriorityBlockingQueue`에서 cancel/update의 초보자 기본값은 **새 entry 추가, old entry stale 처리, worker의 최신성 검사** 세 줄로 기억하면 된다.
