# Backend Data-Structure Starter Pack

> 한 줄 요약: 백엔드에서 자료구조는 "무엇을 저장하나"보다 "무슨 질문을 반복하나"로 고른다. `lookup`은 `map`, `dedupe`는 `set`, `FIFO handoff`는 `queue`, `top-k/earliest-first`는 `priority queue`, `prefix search`는 `trie`가 기본 출발점이다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [자료구조 정리](./README.md)
> - [기본 자료 구조](./basic.md)
> - [배열 vs 연결 리스트](./array-vs-linked-list.md)
> - [해시 테이블 기초](./hash-table-basics.md)
> - [TreeMap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md)
> - [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
> - [Heap vs Priority Queue vs Ordered Map Beginner Bridge](./heap-vs-priority-queue-vs-ordered-map-beginner-bridge.md)
> - [Top-K Heap Direction Patterns](./top-k-heap-direction-patterns.md)
> - [Trie Prefix Search / Autocomplete](./trie-prefix-search-autocomplete.md)
> - [Top-k Streaming and Heavy Hitters](../algorithm/top-k-streaming-heavy-hitters.md)
>
> retrieval-anchor-keywords: backend data structure starter pack, backend data-structure starter pack, array list map set queue priority queue trie, lookup dedupe ordering fifo handoff top-k selection, array vs list backend, list vs set backend, map vs set backend, queue vs priority queue backend, trie prefix search backend, top-k priority queue backend, id lookup data structure, duplicate check data structure, prefix autocomplete structure, 백엔드 자료구조 입문, 백엔드 자료구조 선택, 배열 리스트 맵 셋 큐 우선순위 큐 트라이, 조회 중복제거 순서 fifo top-k 자료구조

## 먼저 잡는 mental model

백엔드에서 자료구조는 "데이터를 어디에 담지?"보다 **"같은 질문을 무엇으로 가장 자주 물을까?"**로 고르는 편이 훨씬 실용적이다.

- `userId`로 바로 값을 찾고 싶다 -> `map`
- 이미 처리한 요청인지 확인하고 싶다 -> `set`
- 순서를 유지한 채 응답이나 배치를 만들고 싶다 -> `array/list`
- 먼저 들어온 작업부터 넘기고 싶다 -> `queue`
- 가장 급한 작업이나 상위 `k`개만 빨리 보고 싶다 -> `priority queue`
- `"spr"`처럼 접두사로 찾고 싶다 -> `trie`

처음에는 아래 표만 몸에 익혀도 실무 선택이 많이 정리된다.

| 반복해서 던지는 질문 | 먼저 떠올릴 구조 | 왜 이 구조가 맞나 | 흔한 오진 |
|---|---|---|---|
| `index 3`, `7번째`, `순서대로 응답 만들기` | `array/list` | 순서와 위치가 핵심이다 | `map`으로 순서를 대신 관리 |
| `id 42의 값은?` | `map` | key -> value lookup이 중심이다 | `list`를 끝까지 순회 |
| `이 값 이미 봤나?` | `set` | 존재 여부만 알면 된다 | `map`에 dummy value 저장 |
| `먼저 들어온 작업부터 처리` | `queue` | arrival order가 규칙이다 | `priority queue`를 습관적으로 사용 |
| `가장 이른 마감/가장 큰 점수/top-k는?` | `priority queue` | 경계값 하나를 계속 꺼내거나 유지한다 | 매번 전체 정렬 |
| `"app"`로 시작하는 후보는? | `trie` | prefix를 구조에 녹여 둔다 | `map` 전체를 `startsWith`로 스캔 |

## 같은 도메인도 질문이 달라지면 구조가 달라진다

주문 도메인 하나만 봐도 자료구조는 질문마다 바뀐다.

```java
List<OrderLine> orderLines = new ArrayList<>();
Map<Long, Order> ordersById = new HashMap<>();
Set<String> processedRequestIds = new HashSet<>();
Queue<EmailJob> emailJobs = new ArrayDeque<>();
PriorityQueue<RetryTask> retryTasks =
    new PriorityQueue<>(Comparator.comparingLong(RetryTask::nextAttemptAt));
```

- 주문 라인을 응답에 그대로 보여 주려면 `List<OrderLine>`
- 주문 번호로 바로 찾으려면 `Map<Long, Order>`
- 같은 요청을 두 번 처리하지 않으려면 `Set<String>`
- 메일 작업을 받은 순서대로 넘기려면 `Queue<EmailJob>`
- 다음 재시도 시각이 가장 이른 작업부터 꺼내려면 `PriorityQueue<RetryTask>`

즉 "주문 데이터를 저장한다"는 한 문장만으로는 자료구조를 못 고른다.
**어떤 연산이 반복되는지**가 먼저다.

## 1. Array / List: 순서와 위치가 핵심일 때

`array`와 `list`는 둘 다 **순서 있는 묶음**이지만, 실무에서 쓰는 감각은 조금 다르다.

- `array`: 크기가 고정되어 있고 인덱스 접근이 아주 직접적일 때
- `list`: 개수가 유동적이고 append + iteration이 자연스러울 때

백엔드에서 먼저 떠올리기 좋은 예시는 이렇다.

| 상황 | 보통 선택 | 이유 |
|---|---|---|
| JSON 응답에 상품 목록을 순서대로 담기 | `List<Product>` | 개수가 유동적이고 순회가 많다 |
| 7일 요일 카운터, 24시간 bucket | `int[]` 같은 array | 크기가 고정이고 index가 곧 의미다 |
| 배치 처리할 ID 목록 | `List<Long>` | append 후 순서대로 소비하기 쉽다 |

입문자에게 특히 중요한 점:

- Java에서 `List`를 쓴다고 해서 곧바로 linked list를 뜻하지는 않는다.
- 대부분의 기본 선택은 `ArrayList`다.
- `LinkedList`는 이름보다 자주 쓰이지 않는다.

즉 `순서 있는 데이터`가 필요하면 먼저 `List`,
`고정 크기 + index hot path`면 `array`를 떠올리면 충분하다.

## 2. Map: exact lookup이 중심일 때

`map`은 **key로 value를 바로 찾는 문제**에 가장 잘 맞는다.

| 백엔드 질문 | 왜 `map`인가 |
|---|---|
| `userId`로 유저를 바로 찾고 싶다 | key -> value 조회가 핵심이다 |
| `couponCode`로 쿠폰 정보를 꺼내고 싶다 | 전체 순회보다 direct lookup이 낫다 |
| `productId`별 집계를 모으고 싶다 | key별로 값을 축적하기 쉽다 |

이 신호가 보이면 `map`을 먼저 의심하면 된다.

- 리스트에서 같은 `id`를 여러 번 찾아야 한다
- "이 key의 현재 상태"를 자주 갱신한다
- 값을 꺼낼 때 순서보다 식별자가 더 중요하다

추가로 한 번만 기억하면 좋은 분기:

- exact lookup만 중요하면 보통 `HashMap`
- key 정렬, `floor/ceiling`, 범위 탐색이 중요하면 ordered map 축으로 간다
  자세한 분기는 [TreeMap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md)로 이어서 보면 된다.

## 3. Set: dedupe와 membership가 핵심일 때

`set`은 **값이 있는지 없는지**만 중요할 때 쓴다.

| 백엔드 질문 | 왜 `set`인가 |
|---|---|
| 이 `requestId`를 이미 처리했나? | 중복 여부만 보면 된다 |
| 이 이메일 주소를 이미 초대했나? | 존재 확인이 핵심이다 |
| 방문한 노드/사용자 ID를 다시 막고 싶다 | unique membership가 목적이다 |

`set`은 `map`보다 생각이 단순하다.

- value payload가 필요 없다
- 중복이 들어오면 하나로 취급한다
- 질문이 `"있나?"`에서 끝난다

실무에서는 이런 식으로 감각을 잡으면 된다.

- 존재 여부만 필요하면 `set`
- 존재 여부뿐 아니라 count, timestamp, 상태도 붙여야 하면 `map`

즉 `set`은 "value가 없는 `map`처럼" 생각하면 입문 단계에서는 충분하다.

## 4. Queue: FIFO handoff가 핵심일 때

`queue`는 **먼저 들어온 것이 먼저 나가는 흐름**을 만들 때 쓴다.

| 백엔드 질문 | 왜 `queue`인가 |
|---|---|
| 받은 순서대로 메일 작업을 worker에게 넘기고 싶다 | FIFO handoff 자체가 정책이다 |
| 요청을 버퍼에 넣고 순서대로 소비하고 싶다 | arrival order를 보존해야 한다 |
| 단순 retry 대상을 먼저 쌓인 순서대로 재처리한다 | 우선순위보다 도착 순서가 먼저다 |

`queue`가 맞는지 확인하는 가장 쉬운 질문은 이것이다.

> "새로 들어온 더 중요한 작업이 기존 맨 앞 작업을 추월해도 되나?"

- 안 된다 -> `queue`
- 된다 -> `priority queue`나 다른 정책을 봐야 한다

양쪽 끝 제어나 `deque` 패턴이 궁금해지면
[Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)로 내려가면 된다.

## 5. Priority Queue: earliest-first와 top-k가 핵심일 때

`priority queue`는 **도착 순서가 아니라 우선순위 키가 다음 원소를 결정**할 때 쓴다.

| 백엔드 질문 | 왜 `priority queue`인가 |
|---|---|
| 다음 재시도 시각이 가장 이른 작업을 꺼내고 싶다 | earliest-first 추출이 핵심이다 |
| 점수가 높은 상위 `k`개 상품만 유지하고 싶다 | 경계값을 힙 루트에 둘 수 있다 |
| SLA가 가장 급한 작업을 먼저 보고 싶다 | priority key가 순서를 바꾼다 |

입문자가 가장 자주 하는 실수는 두 가지다.

- 전체를 매번 정렬해야 한다고 생각한다
- `queue`처럼 도착 순서도 어느 정도 유지될 거라고 기대한다

하지만 `priority queue`의 핵심은 **루트 한 개가 가장 중요하다**는 점이다.

- top-1 추출
- earliest deadline 추출
- streaming top-k 유지

이 세 가지에 특히 잘 맞는다.

`top-k largest`에서 왜 max-heap이 아니라 min-heap을 쓰는지 헷갈리면
[Top-K Heap Direction Patterns](./top-k-heap-direction-patterns.md)로 바로 이어서 보면 된다.

정렬된 이웃 탐색이나 `range query`가 필요하면 `priority queue`보다 ordered map 쪽이 맞을 수 있으니,
그 분기는 [Heap vs Priority Queue vs Ordered Map Beginner Bridge](./heap-vs-priority-queue-vs-ordered-map-beginner-bridge.md)에서 이어서 확인하면 된다.

## 6. Trie: prefix lookup이 핵심일 때

`trie`는 **문자열 전체 일치**보다 **접두사(prefix) 질의**가 많을 때 빛난다.

| 백엔드 질문 | 왜 `trie`인가 |
|---|---|
| `"spr"`로 시작하는 검색어 후보를 보여 주고 싶다 | 공통 prefix를 공유하며 내려갈 수 있다 |
| 명령어/사전 후보를 prefix로 빠르게 찾고 싶다 | exact key보다 startsWith가 중심이다 |
| 자동완성 후보를 prefix 기준으로 묶고 싶다 | prefix 자체가 index다 |

반대로 이런 경우는 `trie`가 아니라 `map`이 더 단순하다.

- 문자열 전체가 정확히 일치하는지만 확인한다
- prefix 후보를 모을 필요가 없다
- key 수가 작고 `startsWith`가 거의 없다

즉 문자열 key라고 해서 항상 `trie`가 아니라,
**질문이 exact lookup이면 `map`, prefix lookup이면 `trie`**다.

## 자주 헷갈리는 분기

- `array/list` vs `set`
  - 순서와 중복 보존이 필요하면 `array/list`
  - 중복 제거와 존재 확인이 핵심이면 `set`
- `map` vs `set`
  - value가 필요하면 `map`
  - key 존재 여부만 필요하면 `set`
- `list` vs `queue`
  - 저장 순서를 유지하며 여러 번 순회하면 `list`
  - 가장 오래된 항목을 앞에서 반복 소비하면 `queue`
- `queue` vs `priority queue`
  - 먼저 온 작업부터 처리하면 `queue`
  - 더 급한 작업이 새치기해야 하면 `priority queue`
- `map` vs `trie`
  - exact key lookup이면 `map`
  - `"이 prefix로 시작하는 것"`이면 `trie`
- `list` vs `priority queue`
  - 정렬된 결과를 한 번 보여 주는 것과 top-1/top-k를 계속 유지하는 것은 다르다
  - 후자는 `priority queue` 쪽이 더 자연스럽다

## 30초 선택 체크리스트

1. 순서 있는 묶음이 필요하고 index/iteration이 중심인가? -> `array/list`
2. key로 값을 바로 찾는가? -> `map`
3. 중복만 막거나 membership만 확인하는가? -> `set`
4. 먼저 들어온 작업부터 넘기는가? -> `queue`
5. 가장 급한 것 하나나 상위 `k`개를 계속 뽑는가? -> `priority queue`
6. prefix로 후보를 찾는가? -> `trie`

이 여섯 갈래로 먼저 나누면, 초급 백엔드 문제의 첫 선택은 대부분 틀리지 않는다.

## 다음 읽기

- 순서 있는 자료의 기본 trade-off를 더 보고 싶다면: [배열 vs 연결 리스트](./array-vs-linked-list.md)
- exact lookup과 hash 감각을 먼저 잡고 싶다면: [해시 테이블 기초](./hash-table-basics.md)
- map의 ordered 변형까지 보고 싶다면: [TreeMap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md)
- queue, deque, priority queue 분기를 더 또렷하게 보고 싶다면: [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
- top-k와 heap 방향이 헷갈리면: [Top-K Heap Direction Patterns](./top-k-heap-direction-patterns.md)
- prefix search와 autocomplete를 더 보고 싶다면: [Trie Prefix Search / Autocomplete](./trie-prefix-search-autocomplete.md)

## 한 줄 정리

입문 단계에서는 "반복 질문"만 먼저 구분하면 된다.
`순서`는 `array/list`, `lookup`은 `map`, `dedupe`는 `set`, `FIFO handoff`는 `queue`, `earliest-first/top-k`는 `priority queue`, `prefix search`는 `trie`가 기본 선택이다.
