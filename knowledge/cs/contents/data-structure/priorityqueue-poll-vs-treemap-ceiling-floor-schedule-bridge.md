---
schema_version: 3
title: PriorityQueue.poll() vs TreeMap ceiling/floor Schedule Bridge
concept_id: data-structure/priorityqueue-poll-vs-treemap-ceiling-floor-schedule-bridge
canonical: false
category: data-structure
difficulty: intermediate
doc_role: mission_bridge
level: intermediate
language: mixed
source_priority: 78
mission_ids:
- missions/roomescape
review_feedback_tags:
- priorityqueue-vs-ordered-map-schedule-query
- poll-vs-ceiling-floor-boundary
- reservation-neighbor-query-value-read
aliases:
- priorityqueue poll vs treemap ceiling floor
- schedule neighbor query bridge
- treemap ceilingkey floorkey reservation
- priorityqueue poll schedule 왜 틀려요
- ceiling floor 있는데 poll을 왜 쓰죠
- ordered map vs priority queue schedule
- key value schedule nearest neighbor
- exact neighbor query treemap
- reservation next previous lookup
- poll removes global min
- what is ceiling floor schedule
- 처음 schedule neighbor query
- floorentry ceilingentry value read
symptoms:
- "roomescape 예약표에서 다음 예약을 찾는데 `poll()`이 먼저 떠올라 조회 로직이 꼬인다"
- 기준 시각 주변 이웃 조회와 전체 최소값 꺼내기를 같은 질문처럼 읽는다
- "`TreeMap<start, reservation>`에서 value까지 읽어야 하는데 PriorityQueue로 풀려다 막힌다"
intents:
- mission_bridge
- comparison
- troubleshooting
prerequisites:
- data-structure/heap-vs-priority-queue-vs-ordered-map-beginner-bridge
- data-structure/treemap-neighbor-query-micro-drill
next_docs:
- data-structure/treemap-floorentry-ceilingentry-value-read-micro-drill
- data-structure/treemap-interval-entry-primer
- language/navigablemap-navigableset-mental-model
linked_paths:
- contents/data-structure/heap-vs-priority-queue-vs-ordered-map-beginner-bridge.md
- contents/data-structure/treemap-neighbor-query-micro-drill.md
- contents/data-structure/treemap-floorentry-ceilingentry-value-read-micro-drill.md
- contents/data-structure/treemap-interval-entry-primer.md
- contents/language/java/navigablemap-navigableset-mental-model.md
- contents/language/java/java-collections-basics.md
confusable_with:
- data-structure/heap-vs-priority-queue-vs-ordered-map-beginner-bridge
- data-structure/treemap-interval-entry-primer
- data-structure/treemap-floorentry-ceilingentry-value-read-micro-drill
forbidden_neighbors:
- contents/data-structure/queue-vs-deque-vs-priority-queue-primer.md
- contents/data-structure/queue-basics.md
expected_queries:
- "roomescape 예약표에서 `다음 예약`을 찾을 때 왜 PriorityQueue가 아니라 TreeMap을 먼저 봐야 해?"
- "기준 시각 `10:15` 이후 첫 예약을 찾는 질문과 `poll()`이 다른 이유를 미션 예제로 설명해줘"
- "예약 schedule 조회인데 `ceilingKey` 대신 `poll()`을 쓰면 왜 어색한지 알고 싶어"
- "`TreeMap<start, reservation>`에서 다음 예약 정보까지 읽으려면 어떤 API 조합이 맞아?"
- 전체에서 가장 이른 예약 처리와 특정 시각 이후 첫 예약 조회를 자료구조로 구분해줘
- roomescape에서 예약 조회 로직과 처리 순서 로직을 같은 구조로 보면 안 되는 이유가 궁금해
contextual_chunk_prefix: |
  이 문서는 예약표 조회 질문에서 PriorityQueue.poll과 TreeMap
  ceiling/floor를 어떻게 갈라 읽는지 헷갈리는 학습자에게 전체 최소값
  꺼내기와 기준 시각 주변 이웃 찾기를 Woowa 미션과 연결해 잇는
  mission_bridge다. 가장 이른 예약 처리, 10시 15분 이후 첫 예약, poll이
  왜 조회가 아냐, 기준 시각 주변 찾기, key와 value 같이 읽기 같은
  자연어 paraphrase가 본 문서의 스케줄 조회 선택에 매핑된다.
---
# PriorityQueue.poll() vs TreeMap `ceiling`/`floor` Schedule Bridge

> 한 줄 요약: 예약표처럼 `key -> value`로 저장된 스케줄에서 `10:15` 주변 이웃을 찾는 질문은 `PriorityQueue.poll()`이 아니라 `TreeMap`의 `floor/ceiling` 계열이 먼저이고, `poll()`은 "현재 전체 최솟값 하나를 꺼내기"라는 다른 질문에 답한다.

**난이도: 🟡 Intermediate**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [Heap vs Priority Queue vs Ordered Map Beginner Bridge](./heap-vs-priority-queue-vs-ordered-map-beginner-bridge.md)
- [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md)
- [TreeMap `floorEntry`/`ceilingEntry` Value-Read Micro Drill](./treemap-floorentry-ceilingentry-value-read-micro-drill.md)
- [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md)
- [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)
- [Java 컬렉션 프레임워크 입문](../language/java/java-collections-basics.md)

retrieval-anchor-keywords: priorityqueue poll vs treemap ceiling floor, schedule neighbor query bridge, treemap ceilingkey floorkey reservation, priorityqueue poll schedule 왜 틀려요, ceiling floor 있는데 poll을 왜 쓰죠, ordered map vs priority queue schedule, key value schedule nearest neighbor, exact neighbor query treemap, reservation next previous lookup, poll removes global min, what is ceiling floor schedule, 처음 schedule neighbor query, 왜 priorityqueue poll이 안 맞아요, floorentry ceilingentry value read

## 핵심 개념

이 문서는 이런 follow-up 질문을 바로 받는 bridge다.

- `ceilingKey()`를 배웠는데도 왜 자꾸 `PriorityQueue.poll()`이 떠오르죠?
- 예약표가 `TreeMap<start, reservation>`인데 `다음 예약`을 찾으려다 `poll()`을 쓰면 왜 이상하죠?
- `가장 이른 예약`과 `10:15 이후 첫 예약`이 왜 다른 질문인가요?

먼저 한 줄로 자르면 된다.

> `poll()`은 "지금 전체에서 가장 이른 것 하나"를 꺼내고, `ceiling/floor`는 "`x` 기준으로 가장 가까운 이웃"을 찾는다.

둘 다 정렬 느낌이 있어서 헷갈리지만, 질문의 기준점이 다르다.

- `PriorityQueue.poll()`의 기준점: 자료구조 전체 head
- `TreeMap.ceilingKey(x)` / `floorKey(x)`의 기준점: 내가 지금 묻는 `x`

예약표처럼 `start -> reservation`을 들고 있을 때는 보통 `x`가 이미 문제 문장 안에 있다.
이때는 `poll()`이 아니라 ordered map neighbor query가 먼저다.

## 한눈에 보기

같은 예약표가 아래처럼 있다고 하자.

```text
09:00 -> 상담
10:30 -> 리뷰
13:00 -> 점검
15:30 -> 배포
```

질문을 두 종류로 나누면 차이가 바로 보인다.

| learner 질문 | 먼저 떠올릴 연산 | 이유 |
|---|---|---|
| `지금 가장 이른 예약 하나를 꺼내 처리하자` | `PriorityQueue.poll()` | 전체 최소값을 반복해서 꺼내는 질문이다 |
| `10:15 이후 첫 예약은?` | `TreeMap.ceilingKey(10:15)` | 기준 시각 오른쪽 이웃을 찾는 질문이다 |
| `10:15 이전 마지막 예약은?` | `TreeMap.floorKey(10:15)` | 기준 시각 왼쪽 이웃을 찾는 질문이다 |
| `10:30 예약이 있으면 그 예약 정보까지 같이 보자` | `TreeMap.ceilingEntry(10:30)` | key와 value를 같이 읽는 질문이다 |

핵심은 `다음`이라는 한국어가 둘로 갈라진다는 점이다.

- `전체에서 다음으로 처리할 것` -> `poll()`
- `10:15 기준 다음 예약` -> `ceiling`

## 왜 `poll()`이 직관적으로 떠오르는데도 틀리나

초보자는 `PriorityQueue`를 보면 "정렬된 예약표"처럼 느끼기 쉽다.
하지만 `poll()`은 예약표를 읽는 API가 아니라 **head를 제거하는 API**다.

예를 들어 `10:15 이후 첫 예약`을 찾고 싶다고 하자.

```text
PriorityQueue poll 순서
poll() -> 09:00
poll() -> 10:30
```

이 결과는 "10:15 기준 오른쪽 이웃"을 직접 준 것이 아니다.
단지 전체 최소값을 하나씩 버리다가 우연히 `10:30`에 도달한 것이다.

여기서 beginner가 자주 놓치는 문제는 세 가지다.

| `poll()`로 억지로 풀면 생기는 일 | 왜 문제인가 |
|---|---|
| `09:00`부터 차례로 꺼내야 한다 | `10:15` 기준 이웃을 바로 읽는 질문이 아니다 |
| 원본 queue를 쓰면 앞 예약들이 제거된다 | 조회 한 번이 상태 변경이 된다 |
| 복사본 queue를 만들어도 기준값 이웃 질의 자체는 여전히 부자연스럽다 | 질문과 구조가 안 맞는다 |

즉 `PriorityQueue`로 못 푼다는 뜻이 아니라, **문제의 중심 연산이 아니다**는 뜻이다.

## 같은 예약표로 둘을 나란히 보기

예약표가 아래와 같다고 하자.

```text
09:00 -> 상담
10:30 -> 리뷰
13:00 -> 점검
15:30 -> 배포
```

질문: `10:15` 이후 첫 예약은?

| 접근 | 결과 | 읽는 법 |
|---|---|---|
| `PriorityQueue.poll()` 한 번 | `09:00` | 전체 최소 예약을 꺼냈을 뿐이다 |
| `PriorityQueue.poll()` 두 번 | `10:30` | `10:15` 이웃을 직접 찾은 게 아니라 앞 원소를 버리고 도달했다 |
| `TreeMap.ceilingKey(10:15)` | `10:30` | `10:15` 기준 오른쪽 이웃을 바로 읽는다 |
| `TreeMap.floorKey(10:15)` | `09:00` | `10:15` 기준 왼쪽 이웃을 바로 읽는다 |

질문이 `10:30 예약 정보까지 같이 보고 싶다`로 바뀌면 ordered map 쪽 장점이 더 또렷해진다.

| 접근 | 결과 |
|---|---|
| `TreeMap.ceilingEntry(10:30)` | `10:30 -> 리뷰` |
| `TreeMap.floorEntry(10:30)` | `10:30 -> 리뷰` |

즉 key-value schedule에서는 `ceiling/floor`가 단순히 시간을 찾는 데서 끝나지 않고, 그 시간에 연결된 value를 같이 읽는 다음 단계까지 자연스럽게 이어진다.

## exact match가 있으면 더 분리된다

`10:30`이 실제 key로 존재할 때는 `poll()`과 `ceiling`의 질문 차이가 더 분명해진다.

| 질문 | 자연스러운 답 |
|---|---|
| `10:30과 같거나 다음 예약` | `ceilingKey(10:30)` -> `10:30` |
| `10:30보다 strict하게 다음 예약` | `higherKey(10:30)` -> `13:00` |
| `현재 전체에서 가장 이른 예약 하나` | `poll()` -> `09:00` |

여기서 `poll()`은 exact match 포함 여부와 아무 관계가 없다.
`ceiling/higher/floor/lower`는 모두 "`x` 주변에서 어디에 멈추나"를 말하고, `poll()`은 "`x`와 무관하게 head를 꺼내라"를 말한다.

그래서 `exact match 포함 여부가 헷갈려요`라는 질문에 `PriorityQueue`를 들고 오면 층위가 어긋난다.
이 질문은 ordered map strict/inclusive 규칙의 영역이다.

## value까지 읽어야 하면 왜 TreeMap 쪽이 더 직접적인가

스케줄에서는 보통 시간만 찾고 끝나지 않는다.
`10:15 이후 첫 예약의 종료 시각`, `10:15 직전 예약의 이름`, `그 예약이 어느 회의실인가`처럼 value가 바로 따라붙는다.

이때 `TreeMap`은 질문이 그대로 이어진다.

```java
Map.Entry<LocalTime, Reservation> next = schedule.ceilingEntry(requestTime);
Map.Entry<LocalTime, Reservation> prev = schedule.floorEntry(requestTime);
```

여기서 읽는 순서는 단순하다.

1. `requestTime` 기준 이웃을 `ceiling/floor`로 찾는다.
2. `Entry`를 받아 `getKey()`와 `getValue()`를 같이 읽는다.

반대로 `PriorityQueue.poll()`은 "어느 예약을 head에서 제거할 것인가"에 가깝다.
예약표 조회 API가 아니라 처리 순서 API라고 생각하는 편이 안전하다.

## 언제 `PriorityQueue`가 다시 맞아지나

`TreeMap`이 맞는 문장을 보다가도 질문이 바뀌면 다시 `PriorityQueue`가 자연스러워질 수 있다.

| 질문이 이렇게 바뀌면 | 더 자연스러운 구조 | 이유 |
|---|---|---|
| `가장 이른 예약부터 하나씩 처리하자` | `PriorityQueue` | 반복 head extraction이 본체다 |
| `현재 진행 중인 작업 중 가장 빨리 끝나는 것만 계속 뽑자` | `PriorityQueue` | global minimum을 반복해서 갱신한다 |
| `10:15 이후 첫 예약`, `10:15 직전 예약`, `10:15~11:00 범위 예약` | `TreeMap` | 기준값 주변 이웃/범위 질의다 |
| `예약 시작 시각으로 찾고, 예약 정보도 같이 읽자` | `TreeMap` | key-value schedule lookup과 value read가 자연스럽다 |

짧게 외우면 된다.

- `처리 순서`를 고르면 `PriorityQueue`
- `조회 기준 시각`을 고르면 `TreeMap`

둘 다 필요하면 한 구조로 우겨 넣기보다, 조회와 처리의 중심 연산이 무엇인지 먼저 다시 확인해야 한다.
경우에 따라 두 구조를 함께 유지할 수는 있지만, 그 판단은 "두 연산이 모두 자주 필요한가"를 본 뒤에 해야 한다.

## 흔한 오해와 함정

- `PriorityQueue`가 정렬돼 있으니 `ceiling` 같은 것도 비슷하게 할 수 있다고 느끼기 쉽다.
  하지만 heap은 보통 head 한 칸만 강하게 보장한다. arbitrary `x` 기준 이웃 조회가 본업은 아니다.
- `TreeMap.firstKey()`도 최소값을 주니 `poll()`과 같다고 생각하면 안 된다.
  `firstKey()`는 조회고, `poll()`은 제거다. 질문이 read인지 consume인지 먼저 갈라야 한다.
- `ceilingKey(10:15)`와 `poll()`이 우연히 같은 값을 줄 때가 있어도 같은 연산은 아니다.
  schedule 상태와 query 시각이 달라지면 바로 갈라진다.
- `TreeMap`이 항상 `PriorityQueue`보다 낫다는 뜻은 아니다.
  이 문서는 `key-value schedule exact-neighbor query` 기준으로만 비교한다.

## 더 깊이 가려면

- `lower/floor/ceiling/higher` 이름 자체가 아직 헷갈리면 [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md)
- key에서 entry로 넘어가 value를 읽는 감각이 약하면 [TreeMap `floorEntry`/`ceilingEntry` Value-Read Micro Drill](./treemap-floorentry-ceilingentry-value-read-micro-drill.md)
- 예약 충돌 검사까지 이어 보고 싶다면 [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md)
- `heap`, `priority queue`, `ordered map`을 더 넓게 한 장에서 다시 자르고 싶다면 [Heap vs Priority Queue vs Ordered Map Beginner Bridge](./heap-vs-priority-queue-vs-ordered-map-beginner-bridge.md)
- Java 이름표 전체를 `NavigableMap` 관점으로 다시 묶고 싶다면 [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)

## 면접/시니어 질문 미리보기

1. 왜 `PriorityQueue`로 `10:15 이후 첫 예약`을 직접 표현하기 어려운가요?
   head extraction은 잘하지만 arbitrary 기준 시각 이웃 질의가 중심 연산이 아니기 때문이다.
2. 왜 schedule을 `TreeMap<start, reservation>`으로 두면 follow-up query가 쉬워지나요?
   `ceiling/floor/entry/subMap`으로 key 기준 이웃과 value read가 같은 축으로 이어지기 때문이다.
3. 언제 두 구조를 함께 둘 수 있나요?
   조회와 처리 순서가 모두 hot path일 때다. 다만 이 문서 범위에서는 "어느 질문이 본체인지"를 먼저 가르는 것이 우선이다.

## 한 줄 정리

예약표에서 `ceiling/floor`를 묻는 순간 질문의 기준점은 `x`이고, `PriorityQueue.poll()`은 그 기준점이 아니라 전체 head를 소비하므로 `key-value schedule neighbor query`의 첫 선택은 `TreeMap` 쪽이다.
