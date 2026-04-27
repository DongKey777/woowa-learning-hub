# DelayQueue Remove Cost Primer

> 한 줄 요약: heap-backed timer queue에서 head를 꺼내는 일과 queue 중간의 timer를 `remove`하는 일은 같은 비용 모양이 아니며, 정확한 취소를 하려면 `handle`과 `equals()` 기준을 따로 생각해야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [힙 기초](./heap-basics.md)
- [Java PriorityQueue Pitfalls](./java-priorityqueue-pitfalls.md)
- [ScheduledFuture Cancellation Bridge](./scheduledfuture-cancel-stale-entries.md)
- [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md)
- [DelayQueue vs PriorityQueue Timer Pitfalls](./delayqueue-vs-priorityqueue-timer-pitfalls.md)

retrieval-anchor-keywords: delayqueue remove cost, delayqueue remove o(n), heap arbitrary remove, heap head removal vs arbitrary remove, timer queue cancel remove cost, timer queue remove handle, timer queue equality caveat, scheduledfuture removeoncancelpolicy cost, removeOnCancelPolicy linear remove, delayqueue cancel by handle, delayqueue cancel by equals, heap middle delete timer, delayed task remove cost, stale entry vs remove timer, heap timer queue beginner primer, arbitrary remove not like poll heap, handle vs equality timer queue, generation equality timer queue

## 먼저 그림부터

놀이공원 줄을 떠올리면 쉽다.

- head removal은 **맨 앞 사람 한 명 빼기**다.
- arbitrary `remove`는 **줄 중간의 특정 사람 찾은 뒤 빼기**다.

힙(heap)은 "맨 앞 사람이 누구인가"만 빠르게 알려 준다.
줄 중간의 누구를 지우고 싶을 때는, 보통 먼저 그 사람을 **찾아야** 한다.

그래서 beginner용 핵심 문장은 이것이다.

> `poll()`/`take()`가 빠르다고 해서 `remove(ticket)`도 같은 모양으로 빠르다고 생각하면 안 된다.

## 한눈에 비교

| 하고 싶은 일 | heap이 바로 아는 것 | 보통 드는 비용 감각 |
|---|---|---|
| head 보기 (`peek`) | 루트 | `O(1)` |
| head 꺼내기 (`poll`, `take`) | 루트 | `O(log n)` |
| 특정 timer 지우기 (`remove(x)`) | 모름, 먼저 찾아야 함 | 보통 `O(n)` 탐색 + heap 복구 |
| 취소만 표시하고 나중에 버리기 | queue 밖 최신성 상태 | cancel 경로는 가볍고 cleanup은 나중으로 밀림 |

여기서 세 번째 줄이 포인트다.

- heap은 루트 접근에는 강하다
- 하지만 "이 timer가 지금 몇 번째 칸에 있지?"는 기본적으로 모른다
- 그래서 arbitrary remove는 head removal과 다른 비용 모양을 가진다

Java의 `DelayQueue`/`PriorityQueue` 계열을 beginner 감각으로 읽으면 보통 이렇게 이해하면 충분하다.

- head removal: root를 빼고 sift down/up 하면 된다
- arbitrary remove: 대상 entry를 선형 탐색으로 찾고, 찾은 뒤에야 sift down/up을 한다

## 왜 이런 차이가 생기나

힙은 **전체 정렬 구조**가 아니라 **루트만 빠른 부분 정렬 구조**다.

예를 들어 min-heap은 아래만 보장한다.

- 부모는 자식보다 작거나 같다
- 그래서 가장 작은 값은 루트에 있다

하지만 힙은 아래를 보장하지 않는다.

- 값 `x`가 배열 몇 번 칸에 있는지
- 같은 `taskId`를 가진 timer가 몇 개 있는지
- "중간의 그 ticket"으로 바로 점프하는 방법

그래서 특정 timer를 없애려면 보통 두 단계가 필요하다.

1. 원하는 entry를 찾는다
2. 그 자리를 메운 뒤 heap 성질을 다시 맞춘다

초보자에게 중요한 건 1번이 루트 제거에는 없지만, arbitrary remove에는 있다는 점이다.

## `handle`이 있으면 왜 얘기가 달라지나

여기서 `handle`은 "그때 넣은 바로 그 ticket을 가리키는 손잡이"라고 생각하면 된다.

| 내가 손에 쥔 것 | 무엇을 지우려는 뜻이 되나 | 남는 caveat |
|---|---|---|
| exact ticket reference | "그때 넣은 그 entry" | 그래도 queue가 index를 따로 안 들고 있으면 내부 탐색이 남을 수 있다 |
| `ScheduledFuture` 같은 취소 핸들 | "그 예약 하나" | 구현에 따라 즉시 제거가 아니라 cancelled 상태만 바꿀 수도 있다 |
| 새로 만든 equal-looking 객체 | "`equals()`가 같다고 보는 아무 entry 하나" | duplicate/generation이 있으면 잘못된 entry를 건드릴 수 있다 |
| logical task id만 | "작업 A 관련 timer" 정도 | reschedule된 여러 ticket 중 어떤 것을 지울지 모호하다 |

핵심은 이것이다.

> exact handle은 **의도**를 분명하게 해 주지만, 비용까지 자동으로 `poll()` 수준으로 낮춰 주는 것은 아니다.

`O(log n)`에 가까운 arbitrary remove를 하려면 보통 추가 구조가 더 필요하다.

- entry가 자신의 heap index를 안다
- 외부 map이 `taskId -> heap index`를 들고 있다
- handle이 node 위치와 함께 관리된다

즉 "정확히 무엇을 지울지"와 "얼마나 싸게 지울지"는 다른 문제다.

## `equals()`로 찾을 때 왜 timer queue가 더 헷갈리나

timer queue는 같은 logical task가 여러 ticket으로 존재하기 쉽다.

- cancel 전에 오래된 ticket이 남아 있을 수 있다
- reschedule하면서 새 deadline의 ticket을 다시 넣을 수 있다
- latest-wins 정책이면 예전 generation ticket이 stale entry가 된다

예를 들어 이런 상황을 보자.

| ticket | taskId | generation | deadline |
|---|---|---:|---:|
| old | `A` | 1 | 10초 |
| new | `A` | 2 | 30초 |

그런데 `equals()`가 `taskId`만 본다면 둘 다 "같은 A"다.

이 상태에서

```java
queue.remove(new TimerTicket("A"));
```

처럼 생각하면 초보자가 흔히 빠지는 함정이 생긴다.

- old ticket을 지운다고 믿었지만 new ticket이 지워질 수 있다
- new ticket을 지운다고 믿었지만 old stale ticket만 사라질 수 있다
- `equals()` 기준이 deadline/generation과 안 맞으면 아예 못 찾을 수도 있다

즉 timer queue에서는 "`같은 작업`"과 "`같은 scheduled entry`"를 구분해야 한다.

## beginner용 안전한 기준

취소/재예약이 섞이는 timer queue에서는 아래 기준이 안전하다.

| 상황 | 더 안전한 기본값 |
|---|---|
| 정확히 그 예약 하나를 취소하고 싶다 | schedule 시 돌려받은 handle/reference를 잡고 간다 |
| reschedule이 잦다 | 기존 entry를 broad equality로 찾기보다 새 ticket + stale skip을 먼저 검토한다 |
| 같은 task의 여러 generation이 공존할 수 있다 | `taskId`만으로 `equals()`를 잡지 않는다 |
| cancel hot path가 매우 뜨겁다 | 즉시 `remove` 비용이 cancel 경로로 들어오는지 먼저 본다 |

실무에서 lazy stale skip이 자주 나오는 이유도 여기 있다.

- `remove`를 매번 정확히 찾는 비용을 취소 시점에 내지 않는다
- 대신 worker가 head로 올라온 오래된 ticket을 버린다
- 메모리 retention과 stale cleanup 비용은 뒤로 밀린다

즉시 제거가 틀렸다는 뜻은 아니다.
다만 **head pop과 같은 비용 감각으로 생각하면 설계가 어긋나기 쉽다**는 뜻이다.

## 자주 하는 오해

1. heap은 정렬돼 있으니 특정 원소도 빨리 찾을 수 있다고 생각한다.
2. exact handle이 있으면 `remove` 비용도 자동으로 `O(log n)`일 것이라고 생각한다.
3. `equals()`가 같은 객체면 어느 ticket을 지워도 괜찮다고 생각한다.
4. `taskId` 하나만 같으면 reschedule 전후 ticket도 같은 entry라고 생각한다.
5. `removeOnCancelPolicy(true)`는 공짜로 queue를 깨끗하게 만든다고 생각한다.

특히 5번은 주의해야 한다.
queue를 빨리 깨끗하게 만드는 대신, 그 cleanup 비용을 `cancel()` 쪽으로 당겨올 수 있다.

## 다음 문서로 이어가기

- `ScheduledFuture.cancel()`과 `removeOnCancelPolicy` trade-off를 API 쪽에서 보고 싶으면 [ScheduledFuture Cancellation Bridge](./scheduledfuture-cancel-stale-entries.md)
- `DelayQueue`에서 cancel/reschedule과 stale skip 정책을 같이 보고 싶으면 [Timer Cancellation and Reschedule Stale Entry Primer](./timer-cancellation-reschedule-stale-entry-primer.md)
- heap에서 `remove(Object)`가 왜 stale-entry 패턴과 연결되는지 더 넓게 보려면 [Java PriorityQueue Pitfalls](./java-priorityqueue-pitfalls.md)
- timer queue 구조 선택까지 넓히려면 [DelayQueue vs PriorityQueue Timer Pitfalls](./delayqueue-vs-priorityqueue-timer-pitfalls.md)

## 한 줄 정리

heap-backed timer queue에서 head removal은 "루트 하나 빼기"지만, arbitrary `remove`는 보통 "원하는 ticket 찾기 + heap 복구"다.
그래서 cancellation 설계에서는 `handle`, `equals()`, stale-entry 정책을 같이 봐야 한다.
