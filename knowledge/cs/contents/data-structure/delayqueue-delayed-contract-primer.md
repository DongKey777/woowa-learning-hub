---
schema_version: 3
title: DelayQueue Delayed Contract Primer
concept_id: data-structure/delayqueue-delayed-contract-primer
canonical: false
category: data-structure
difficulty: beginner
doc_role: playbook
level: beginner
language: ko
source_priority: 87
mission_ids:
- missions/roomescape
review_feedback_tags:
- delayed-contract
- compareto-getdelay-alignment
- timer-deadline-ordering
aliases:
- DelayQueue Delayed contract
- Delayed compareTo getDelay
- compareTo getDelay mismatch
- expired head DelayQueue
- deadlineNanos Delayed
- timer priority policy split
- getDelay negative but not head
symptoms:
- compareTo는 business priority를 보고 getDelay는 deadline을 봐서 가장 먼저 만료된 task가 head에 오지 않는다
- getDelay가 음수인 task가 있는데 head가 아니어서 DelayQueue가 계속 기다리는 이상 현상을 만든다
- mutable deadline, currentTimeMillis clock, same deadline tie-breaker를 Delayed contract와 함께 설계하지 않는다
intents:
- troubleshooting
- definition
prerequisites:
- data-structure/queue-vs-deque-vs-priority-queue-primer
- data-structure/java-priorityqueue-pitfalls
next_docs:
- data-structure/delayqueue-vs-priorityqueue-timer-pitfalls
- data-structure/timer-vocabulary-delay-timeout-deadline-dueat-bridge
- data-structure/java-timer-clock-choice-primer
- data-structure/timer-priority-policy-split
linked_paths:
- contents/data-structure/queue-vs-deque-vs-priority-queue-primer.md
- contents/data-structure/java-priorityqueue-pitfalls.md
- contents/data-structure/priorityblockingqueue-timer-misuse-primer.md
- contents/data-structure/timer-vocabulary-delay-timeout-deadline-dueat-bridge.md
- contents/data-structure/java-timer-clock-choice-primer.md
- contents/data-structure/delayqueue-vs-priorityqueue-timer-pitfalls.md
- contents/data-structure/timer-priority-policy-split.md
- contents/data-structure/timer-cancellation-reschedule-stale-entry-primer.md
- contents/data-structure/timing-wheel-vs-delay-queue.md
confusable_with:
- data-structure/java-priorityqueue-pitfalls
- data-structure/delayqueue-vs-priorityqueue-timer-pitfalls
- data-structure/timer-priority-policy-split
- data-structure/java-timer-clock-choice-primer
forbidden_neighbors: []
expected_queries:
- DelayQueue에서 compareTo와 getDelay는 왜 같은 deadline 기준을 봐야 해?
- getDelay가 만료됐는데 task가 head가 아니라서 실행되지 않는 버그는 어떻게 생겨?
- Delayed 구현에서 business priority와 deadline ordering을 섞으면 왜 위험해?
- deadlineNanos와 sequence tie-breaker로 DelayQueue task ordering을 구현하는 법을 알려줘
- DelayQueue Delayed contract를 beginner 기준으로 설명해줘
contextual_chunk_prefix: |
  이 문서는 Java DelayQueue의 Delayed contract에서 compareTo는 queue head
  ordering을, getDelay는 head expiry gate를 맡기 때문에 두 판단이 같은
  deadlineNanos 기준으로 정렬되어야 한다는 primer다. business priority,
  clock choice, tie-breaker, mutable deadline 함정을 다룬다.
---
# DelayQueue Delayed Contract Primer

> 한 줄 요약: `DelayQueue`에서 `compareTo()`는 "누가 줄 맨 앞인가"를 정하고, `getDelay()`는 "맨 앞 사람이 지금 나가도 되는가"를 정하므로 두 판단은 같은 deadline을 기준으로 맞아야 한다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../algorithm/backend-algorithm-starter-pack.md)


retrieval-anchor-keywords: delayqueue delayed contract primer basics, delayqueue delayed contract primer beginner, delayqueue delayed contract primer intro, data structure basics, beginner data structure, 처음 배우는데 delayqueue delayed contract primer, delayqueue delayed contract primer 입문, delayqueue delayed contract primer 기초, what is delayqueue delayed contract primer, how to delayqueue delayed contract primer
> 관련 문서:
> - [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
> - [Java PriorityQueue Pitfalls](./java-priorityqueue-pitfalls.md)
> - [PriorityBlockingQueue Timer Misuse Primer](./priorityblockingqueue-timer-misuse-primer.md)
> - [Timer Vocabulary Bridge: delay vs timeout vs deadline vs dueAt](./timer-vocabulary-delay-timeout-deadline-dueat-bridge.md)
> - [Java Timer Clock Choice Primer](./java-timer-clock-choice-primer.md)
> - [DelayQueue vs PriorityQueue Timer Pitfalls](./delayqueue-vs-priorityqueue-timer-pitfalls.md)
> - [Timer Priority Policy Split](./timer-priority-policy-split.md)
> - [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md)
> - [Timing Wheel vs Delay Queue](./timing-wheel-vs-delay-queue.md)
>
> retrieval-anchor-keywords: delayqueue delayed contract, delayed compareto getdelay, delayed compareTo getDelay mismatch, java delayed interface, java delayqueue delayed implementation, delayqueue expired head, delayqueue stuck waiting, delayqueue poll null but expired task exists, delayqueue task runs late, compareTo deadline getDelay deadline, delayed task ordering contract, getDelay negative but not head, business priority in delayqueue, timer priority policy split, delayed compareTo business priority, due time gate, mutable deadline delayqueue, delayqueue reschedule stale entry, delayed beginner primer, delayqueue nanotime, currentTimeMillis vs nanoTime delayqueue, timer clock choice, relative deadline clock, deadlineNanos, equal deadline sequence tie breaker, same deadline fifo delayqueue, delayqueue stable order, delayed sequence business priority separate

## 먼저 그림부터

`DelayQueue`를 놀이공원 입장 줄처럼 생각하면 쉽다.

- `compareTo()`는 **줄 순서**를 정한다.
- `getDelay()`는 **줄 맨 앞 사람이 입장 시간이 됐는지**를 말한다.

문제는 `DelayQueue`가 매번 줄 전체를 뒤져서 "입장 가능한 사람"을 찾지 않는다는 점이다.
보통 **맨 앞 원소의 delay만 보고** 꺼낼지, 더 기다릴지를 정한다.

그래서 두 메서드가 같은 기준을 봐야 한다.

| 메서드 | 초보자용 의미 | 같은 기준이어야 하는 이유 |
|---|---|---|
| `compareTo(other)` | 어떤 task가 queue head에 더 가까운가 | 가장 먼저 만료될 task가 head로 와야 한다 |
| `getDelay(unit)` | 이 task가 지금 실행 가능한가 | head의 delay가 0 이하일 때만 consumer가 꺼낼 수 있다 |

핵심 문장:

> `compareTo()`가 정한 head와 `getDelay()`가 말하는 "가장 먼저 만료됨"이 같은 task여야 한다.

## 1. 정답 패턴은 같은 deadline 필드를 쓰는 것이다

가장 안전한 구현은 **절대 deadline** 하나를 저장하고, 두 메서드가 모두 그 값을 기준으로 판단하게 만드는 방식이다.
여기서 `delay`가 입력 표현이고 `deadline`이 queue 내부 표현이라는 단어 구분부터 먼저 잡고 싶다면 [Timer Vocabulary Bridge: delay vs timeout vs deadline vs dueAt](./timer-vocabulary-delay-timeout-deadline-dueat-bridge.md)를 먼저 보고 와도 좋다.
왜 이 값을 보통 `deadlineMillis`보다 `deadlineNanos`로 두는지부터 헷갈리면 [Java Timer Clock Choice Primer](./java-timer-clock-choice-primer.md)에서 벽시계와 상대 지연 시계를 먼저 나누고 돌아오면 이해가 훨씬 쉽다.

```java
final class ScheduledJob implements Delayed {
    private final long deadlineNanos;
    private final long sequence;
    private final Runnable job;

    ScheduledJob(long delayNanos, long sequence, Runnable job) {
        this.deadlineNanos = System.nanoTime() + delayNanos;
        this.sequence = sequence;
        this.job = job;
    }

    @Override
    public long getDelay(TimeUnit unit) {
        long remaining = deadlineNanos - System.nanoTime();
        return unit.convert(remaining, TimeUnit.NANOSECONDS);
    }

    @Override
    public int compareTo(Delayed other) {
        ScheduledJob that = (ScheduledJob) other;

        int byDeadline = Long.compare(this.deadlineNanos, that.deadlineNanos);
        if (byDeadline != 0) {
            return byDeadline;
        }
        return Long.compare(this.sequence, that.sequence);
    }
}
```

여기서 기준은 단순하다.

## 1. 정답 패턴은 같은 deadline 필드를 쓰는 것이다 (계속 2)

- `deadlineNanos`가 더 작다 = 더 빨리 실행돼야 한다
- `compareTo()`도 `deadlineNanos` 작은 task를 앞에 둔다
- `getDelay()`도 `deadlineNanos - now`로 남은 시간을 계산한다
- `sequence`는 deadline이 같을 때만 쓰는 tie-breaker다

즉 `compareTo()`와 `getDelay()`가 서로 다른 답을 내는 것이 아니라,
같은 deadline을 서로 다른 용도로 읽고 있을 뿐이다.

## 2. 어긋난 구현은 "만료된 작업이 숨어 있는 queue"를 만든다

초보자가 자주 하는 실수는 `compareTo()`에 business priority를 넣는 것이다.

```java
// 잘못된 예: delay는 deadline으로 계산하지만, queue 순서는 priority로 정한다.
@Override
public long getDelay(TimeUnit unit) {
    return unit.convert(deadlineNanos - System.nanoTime(), TimeUnit.NANOSECONDS);
}

@Override
public int compareTo(Delayed other) {
    ScheduledJob that = (ScheduledJob) other;
    return Integer.compare(that.priority, this.priority); // 높은 priority를 먼저 둠
}
```

이제 이런 상황을 보자.

| task | deadline | priority | 실제로 실행 가능? | `compareTo()` 기준 위치 |
|---|---:|---:|---|---|
| A | 지금 | 1 | 예 | 뒤 |
| B | 10초 뒤 | 100 | 아니오 | 앞 |

사람 눈에는 A가 지금 실행돼야 한다.
하지만 queue head는 B가 된다.

`DelayQueue.take()`는 head인 B를 보고 "아직 10초 남았네"라고 판단할 수 있다.
그 결과 A는 이미 만료됐는데도 B 뒤에 숨어서 늦게 실행된다.

### 초보자용 visual trace: 두 메서드가 같은 deadline을 볼 때와 아닐 때

같은 시각 `now = 100`에서 queue 안에 작업 두 개가 있다고 하자.

| task | 저장된 deadline | `getDelay()` 계산 | `compareTo()`가 써야 하는 값 |
|---|---:|---:|---|
| A | 100 | `100 - 100 = 0` | 100 |
| B | 110 | `110 - 100 = 10` | 110 |

이때 올바른 흐름은 아래처럼 한 줄로 이어진다.

```text
same deadline field
A.deadline=100, B.deadline=110, now=100

compareTo(A, B) -> A가 더 이른 deadline이라 head
getDelay(A)     -> 0, 지금 꺼내도 됨

결론: head=A, expired=A
```

즉 `compareTo()`가 "A를 맨 앞에 둔다"고 말한 순간,
`getDelay()`도 같은 deadline을 읽어서 "맞다, A는 지금 만료됐다"고 이어져야 한다.

반대로 `compareTo()`가 deadline 대신 business priority를 보면 흐름이 끊긴다.

## 2. 어긋난 구현은 "만료된 작업이 숨어 있는 queue"를 만든다 (계속 2)

```text
mismatched fields
A.deadline=100, priority=1
B.deadline=110, priority=100
now=100

compareTo(A, B) -> priority 때문에 B가 head
getDelay(B)     -> 10, 아직 아님
getDelay(A)     -> 0, 이미 만료됐지만 head가 아니라 숨음

결론: head=B, expired=A
```

초보자 기준 체크 문장은 이것 하나면 충분하다.

> `compareTo()`가 고른 head와 `getDelay()`가 0 이하라고 말하는 task가 같아야 한다.

## 3. 실제로 깨지는 것

`compareTo()`와 `getDelay()`가 어긋나면 아래 문제가 생긴다.

| 증상 | 왜 생기나 |
|---|---|
| `take()`가 기다리는데 이미 만료된 task가 있다 | 만료된 task가 head가 아니어서 확인되지 않는다 |
| `poll()`이 `null`을 반환하는데 queue 안에 expired task가 있다 | head의 delay는 아직 양수이기 때문이다 |
| task 실행 순서가 deadline과 다르다 | heap 순서가 deadline이 아닌 다른 값으로 정해졌다 |
| 테스트는 가끔 통과하지만 운영에서 늦게 실행된다 | priority, sequence, mutable field가 deadline보다 앞서 비교될 때 입력 순서에 따라 숨어 버린다 |

`DelayQueue`는 "queue 전체에서 delay가 0 이하인 아무 원소나 찾아서 꺼내는 구조"가 아니다.
**head가 만료됐는지**를 보는 구조라고 기억하면 이 버그가 바로 보인다.

## 4. business priority는 어디에 넣어야 하나

business priority가 필요하다고 해서 항상 잘못은 아니다.
다만 primary key가 deadline이어야 한다.

| 요구 | 안전한 방향 |
|---|---|
| 같은 deadline끼리 먼저 들어온 순서대로 처리 | `deadline -> sequence` |
| 같은 deadline끼리 높은 priority 먼저 처리 | `deadline -> priority -> sequence` |
| deadline보다 business priority가 더 중요 | `DelayQueue` 하나로 섞지 말고 scheduler 정책을 분리한다 |

즉 "10초 뒤 high priority"가 "지금 만료된 low priority"보다 head에 오면 안 된다.
그 순간 `DelayQueue`의 delay-aware blocking 계약이 깨진다.
이 분리 기준이 헷갈리면 [Timer Priority Policy Split](./timer-priority-policy-split.md)에서 due-time gate와 ready priority queue를 먼저 나눠 보면 된다.

### 4.5 같은 deadline에서도 sequence tie-breaker를 두는 이유

여기서 초보자가 한 번 더 헷갈리는 지점이 있다.

> "deadline이 같다면 priority를 tie-breaker로 쓰면 되지, sequence까지 왜 필요하지?"

먼저 `sequence`의 역할부터 아주 작게 나누면 쉽다.

| 값 | 답하려는 질문 |
|---|---|
| `deadline` | 언제 실행 가능해지는가 |
| `sequence` | 같은 deadline 묶음 안에서 어떤 순서로 꺼낼 것인가 |
| `business priority` | 이미 실행 가능한 작업들 중 무엇이 더 중요한가 |

즉 `sequence`는 **시간 동점 처리용 안정장치**이고,
`business priority`는 **업무 정책**이다. 둘은 같은 질문에 답하지 않는다.

예를 들어 A와 B가 둘 다 `deadline = 100`이라면 둘 다 같은 시각에 만료된다.
이때 `sequence`가 없으면 "동점일 때 어떤 순서로 나오나"가 구현 세부에 기대는 모양이 되기 쉽다.

| task | deadline | sequence | business priority |
|---|---:|---:|---:|
| A | 100 | 10 | 1 |
| B | 100 | 11 | 100 |

이 표에서 `sequence`가 말하는 것은 단 하나다.

- 둘 다 같은 시각에 due라면 먼저 들어온 A를 먼저 꺼낼지
- 아니면 같은 deadline 묶음 안에서 다른 안정 규칙을 둘지

반면 `business priority`는 "둘 다 ready가 된 뒤 누구를 먼저 처리할까"에 가깝다.
그래서 둘을 한 칸으로 합쳐 생각하면 아래 두 요구가 섞인다.

1. 같은 deadline에서 결과가 흔들리지 않게 하자
2. 중요한 일부터 처리하자

## 4. business priority는 어디에 넣어야 하나 (계속 2)

1번은 comparator stability 문제고, 2번은 scheduler policy 문제다.
같은 deadline 동점 처리를 안정적으로 만들고 싶다면 보통 `deadline -> sequence`를 먼저 둔다.
"같은 deadline에서는 high priority 먼저"가 진짜 요구라면 그때만 `deadline -> priority -> sequence`처럼 넣는다.

핵심은 이것이다.

> `sequence`는 equal deadline을 안정적으로 풀기 위한 tie-breaker이고, business priority는 그 위에 얹을지 말지 따로 결정하는 정책이다.

## 5. 자주 하는 오해

1. `getDelay()`가 정확하면 `compareTo()`는 아무 기준이어도 된다고 생각한다.
2. `DelayQueue`가 queue 전체를 스캔해서 만료된 task를 찾아준다고 생각한다.
3. `compareTo()`를 business priority 정렬용으로 먼저 쓰고, deadline은 `getDelay()`에만 넣는다.
4. `compareTo()`에서 남은 delay를 매번 새로 계산하면 더 정확하다고 생각한다.
5. queue에 넣은 뒤 deadline이나 priority 필드를 바꿔도 heap 순서가 자동으로 다시 잡힌다고 생각한다.

`compareTo()`에서는 보통 현재 시각을 다시 계산하기보다, 저장해 둔 `deadlineNanos` 같은 안정적인 값을 비교하는 편이 안전하다.
남은 시간은 계속 변하지만, "누가 더 이른 deadline인가"는 같은 두 task 사이에서 흔들리면 안 되기 때문이다.

## 다음 문서로 이어가기

- `deadlineNanos`를 왜 `System.nanoTime()`으로 잡는지부터 분리하려면 [Java Timer Clock Choice Primer](./java-timer-clock-choice-primer.md)
- `DelayQueue`와 plain `PriorityQueue`의 timer loop 차이를 더 보려면 [DelayQueue vs PriorityQueue Timer Pitfalls](./delayqueue-vs-priorityqueue-timer-pitfalls.md)
- `PriorityBlockingQueue.take()`가 왜 deadline까지 기다려 주지 않는지 먼저 잡으려면 [PriorityBlockingQueue Timer Misuse Primer](./priorityblockingqueue-timer-misuse-primer.md)
- business priority를 `Delayed.compareTo()`에 넣어도 되는지 헷갈리면 [Timer Priority Policy Split](./timer-priority-policy-split.md)
- heap comparator와 mutable key 함정을 더 넓게 보려면 [Java PriorityQueue Pitfalls](./java-priorityqueue-pitfalls.md)
- 취소와 재예약 때문에 오래된 ticket이 남는 흐름을 보려면 [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md)
- timer 수와 cancellation churn이 커졌을 때 구조 선택을 보려면 [Timing Wheel vs Delay Queue](./timing-wheel-vs-delay-queue.md)

## 한 줄 정리

`Delayed` 구현에서는 `compareTo()`가 **가장 이른 deadline을 head로 보내고**, `getDelay()`가 **그 같은 deadline까지 남은 시간**을 말해야 한다.
둘이 어긋나면 `DelayQueue`는 만료된 task를 queue 안에 두고도 기다리는 이상한 scheduler가 된다.
