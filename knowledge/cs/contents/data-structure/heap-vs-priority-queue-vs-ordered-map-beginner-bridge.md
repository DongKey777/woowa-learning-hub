# Heap vs Priority Queue vs Ordered Map Beginner Bridge

> 한 줄 요약: `priority queue`는 "지금 가장 중요한 것 1개"를 뽑는 규칙이고, `heap`은 그 규칙을 빠르게 구현하는 대표 구조이며, `TreeMap` 같은 ordered map은 `floor/ceiling/range`처럼 기준값 주변을 찾는 데 맞다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../algorithm/backend-algorithm-starter-pack.md)


retrieval-anchor-keywords: heap vs priority queue vs ordered map beginner bridge basics, heap vs priority queue vs ordered map beginner bridge beginner, heap vs priority queue vs ordered map beginner bridge intro, data structure basics, beginner data structure, 처음 배우는데 heap vs priority queue vs ordered map beginner bridge, heap vs priority queue vs ordered map beginner bridge 입문, heap vs priority queue vs ordered map beginner bridge 기초, what is heap vs priority queue vs ordered map beginner bridge, how to heap vs priority queue vs ordered map beginner bridge
> 관련 문서:
> - [힙 기초](./heap-basics.md)
> - [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
> - [TreeMap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md)
> - [Balanced BST vs Unbalanced BST Primer](./balanced-bst-vs-unbalanced-bst-primer.md)
> - [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)
>
> retrieval-anchor-keywords: heap vs priority queue vs ordered map, heap vs treemap, priority queue vs treemap, ordered map beginner, ordered map vs heap, top 1 vs range query, top1 vs neighbor query, floor ceiling vs heap, ceilingKey floorKey example, TreeMap range query beginner, priority queue is usually heap, heap is implementation priority queue is behavior, sorted map vs priority queue, 힙 우선순위 큐 트리맵 차이, top 1 자료구조, 범위 질의 자료구조, 이웃 질의 자료구조, floor ceiling 입문, TreeMap vs heap

## 먼저 10초 결정

문제를 읽자마자 이 질문부터 한다.

> 내가 빨리 답해야 하는 건 "지금 top 1 하나"인가, 아니면 "`x` 근처 값들"인가?

- `가장 작은 것 하나`, `가장 이른 작업 하나`, `현재 최고 우선순위 하나`를 계속 꺼내면 `priority queue`
- 그 `priority queue`를 보통 `heap`으로 구현한다
- `10:15 바로 다음 예약`, `10:15 바로 이전 값`, `10:15~11:00 범위 전체`가 필요하면 `TreeMap` 같은 ordered map

즉 `heap`과 `priority queue`는 보통 한 팀이고, `ordered map`은 질문 자체가 다르다.

## 빠른 선택표

| 문제에서 실제로 필요한 답 | 먼저 떠올릴 것 | 이유 | 예시 |
|---|---|---|---|
| 지금 가장 작은 값 하나 | `priority queue` (`heap`) | top 1 `peek/poll`가 핵심 | 가장 이른 deadline 작업 실행 |
| top 1을 계속 꺼내며 새 값도 넣기 | `priority queue` (`heap`) | insert + extract-top 반복 | 작업 스케줄러, top-k 유지 |
| 기준값 바로 이전/다음 값 | `TreeMap` 같은 ordered map | `floor/ceiling/lower/higher`가 핵심 | `10:15` 다음 예약 찾기 |
| 어떤 구간 안의 값들 전체 | `TreeMap` 같은 ordered map | range view / ordered iteration이 핵심 | `10:15~11:00` 예약 전부 보기 |

## 같은 데이터로 보면 더 잘 분리된다

예약 시각 `10:00`, `10:30`, `11:00`이 있다고 하자.

### 1. "다음 예약 하나만 계속 꺼내면 된다"

이 질문은 `priority queue` 쪽이다.

```text
min-heap / priority queue
peek()  -> 10:00
poll()  -> 10:00
peek()  -> 10:30
```

핵심은 항상 **맨 앞 한 개**만 빠르게 알면 된다는 점이다.
이럴 때는 `heap`이 자연스럽다.

### 2. "`10:15` 기준으로 앞뒤를 찾고 싶다"

이 질문은 ordered map 쪽이다.

```text
TreeMap / ordered map
floorKey(10:15)   -> 10:00
ceilingKey(10:15) -> 10:30
```

여기서는 "전체 중 최소 하나"보다 **기준값 주변 이웃**이 중요하다.
이런 질문은 heap이 잘 못 한다.

### 3. "`10:15~11:00` 사이 예약을 전부 보고 싶다"

이것도 ordered map 쪽이다.

```text
subMap(10:15, true, 11:00, true)
-> 10:30, 11:00
```

이 질문은 top 1이 아니라 **정렬된 range**를 요구한다.
그래서 `TreeMap` 같은 ordered map이 맞다.

## 연산 감각을 한 장으로 보기

| 하고 싶은 일 | `priority queue` (`heap`) | `TreeMap` 같은 ordered map |
|---|---|---|
| 가장 작은/큰 값 하나 보기 | 아주 자연스럽다 | 가능은 하지만 주특기는 아니다 |
| top 1을 반복해서 꺼내기 | 아주 자연스럽다 | 가능은 하지만 range/neighbor 쿼리 쪽이 더 본업이다 |
| `x` 바로 이전/다음 값 찾기 | 보통 부자연스럽다 | `floor/ceiling/lower/higher`가 자연스럽다 |
| `[a, b]` 범위 순회 | 보통 부자연스럽다 | `subMap/headMap/tailMap`이 자연스럽다 |
| 전체를 정렬된 순서로 훑기 | 힙만으로는 불편하다 | 자연스럽다 |

초보자 입장에서는 이렇게 외우면 충분하다.

- `heap`은 루트 한 칸이 강하다
- ordered map은 정렬된 줄 전체를 다루는 데 강하다

## 자주 헷갈리는 말

### 1. `priority queue`와 `heap`은 같은 말인가

완전히 같은 말은 아니다.

- `priority queue`: "우선순위가 가장 높은 원소가 먼저 나온다"는 **동작 규칙**
- `heap`: 그 규칙을 빠르게 만들기 위한 **대표 구현체**

실무와 면접에서는 거의 붙어서 나오지만, 같은 층위의 단어는 아니다.

### 2. 힙도 정렬되어 있으니 `ceiling` 같은 걸 할 수 있지 않나

보통 아니다.

힙은 루트만 강하게 보장한다.
`10:15` 다음 예약처럼 **중간 기준값 주변 이웃**을 찾는 질문은 힙의 강점이 아니다.

### 3. `PriorityQueue`는 넣은 순서도 자동으로 기억해 주나

아니다.

- `PriorityQueue`는 **우선순위가 높은 원소가 먼저 나오도록** 도와준다
- 같은 우선순위끼리 **삽입 순서까지 자동 보존한다고 기대하면 안 된다**

예를 들어 우선순위가 모두 `5`인 작업 `A`, `B`, `C`를 이 순서로 넣어도, 꺼낼 때 항상 `A -> B -> C`를 보장한다고 보면 안 된다.

즉 `PriorityQueue`는 `queue`라는 이름이 있어도, 초급자가 떠올리는 FIFO queue와는 다르다.
같은 우선순위에서 "먼저 들어온 것을 먼저 꺼내야 한다"면 `(priority, sequence)`처럼 **우선순위 + 삽입 번호**를 함께 관리해야 한다.

### 4. `TreeMap`도 `firstKey()`가 있으니 heap 대신 쓰면 되는 것 아닌가

가능은 하지만 질문이 다르다.

- 핵심 루프가 `peek/poll top 1`이면 `priority queue`가 더 직접적이다
- 핵심 루프가 `floor/ceiling/subMap`이면 ordered map이 더 직접적이다

둘 다 "최솟값 하나"는 보여 줄 수 있어도, **편하게 풀리는 질문**이 다르다.

### 5. 둘 다 필요하면 하나로 통일하면 안 되나

초급 단계에서는 먼저 이렇게 판단하면 된다.

- top 1 반복 추출이 본체면 `priority queue`
- neighbor/range 질의가 본체면 ordered map

둘 다 정말 중요하면 두 구조를 함께 두거나 문제 설계를 다시 봐야 한다.
"한 구조가 모든 질문을 다 싸게 처리하겠지"라고 기대하면 초반에 자주 꼬인다.

## 다음에 어디로 가면 좋은가

- `heap`과 `priority queue` 자체가 아직 헷갈리면 [힙 기초](./heap-basics.md)
- `queue / deque / priority queue`의 1차 분기가 먼저 필요하면 [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
- `TreeMap`의 `floorKey`, `ceilingKey`, `subMap`이 왜 자연스러운지 보고 싶으면 [TreeMap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md)
- Java `NavigableMap`의 `lower/floor/ceiling/higher` 이름이 헷갈리면 [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)

## 한 줄 정리

`heap`은 보통 `priority queue`의 엔진이고, `TreeMap` 같은 ordered map은 `x` 근처 이웃과 range를 찾는 도구다.
입문자는 먼저 "`top 1`이냐, `neighbor/range`냐"만 구분해도 꽤 많은 혼선을 줄일 수 있다.
