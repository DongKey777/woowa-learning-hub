# TreeSet vs PriorityQueue Neighbor-Choice Card

> 한 줄 요약: 학습자가 `next smallest`를 물을 때는 "기준값 주변 이웃을 찾는가"와 "최솟값을 계속 꺼내는가"를 먼저 나누면 `TreeSet`과 `PriorityQueue`를 훨씬 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [HashSet vs TreeSet Beginner Bridge](./hashset-vs-treeset-beginner-bridge.md)
- [TreeSet Exact-Match Drill](./treeset-exact-match-drill.md)
- [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
- [Heap vs Priority Queue vs Ordered Map Beginner Bridge](./heap-vs-priority-queue-vs-ordered-map-beginner-bridge.md)
- [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)

retrieval-anchor-keywords: treeset vs priorityqueue neighbor choice, treeset vs priority queue beginner, next smallest confusion, next smallest after x, ordered neighbor query basics, repeated min extraction basics, ceiling vs poll beginner, treeset ceiling higher 언제, priorityqueue poll 언제, 왜 next smallest가 헷갈려요, 처음 배우는 treeset priorityqueue, what is ordered neighbor query, priority queue vs sorted set, selection vs neighbor lookup

## 핵심 개념

`다음으로 작은 것`이라는 말은 초보자에게 두 뜻으로 섞여 들어온다.

- `전체에서 가장 작은 값을 하나 꺼내고, 또 그다음 최소값을 꺼내고 싶다`
- `기준값 x 바로 다음 값을 알고 싶다`

이 둘은 같은 질문이 아니다.

> `PriorityQueue`는 "현재 전체 최소값"을 반복해서 꺼내는 도구이고, `TreeSet`은 "기준값 주변 이웃"을 찾는 도구다.

짧게 외우면 이렇게 자르면 된다.

- `poll()`을 반복하면 된다 -> `PriorityQueue`
- `ceiling(x)`, `higher(x)`, `floor(x)`, `lower(x)`가 필요하다 -> `TreeSet`

## 한눈에 보기

같은 숫자 줄 `[10, 20, 30, 40]`을 놓고 보면 차이가 빨리 보인다.

| learner 질문 | 먼저 떠올릴 구조 | 이유 |
|---|---|---|
| `가장 작은 값부터 계속 꺼내고 싶어요` | `PriorityQueue` | 매번 전체 최소값 하나가 핵심이다 |
| `25 다음 값이 뭐예요?` | `TreeSet` | 기준값 `25` 주변 이웃을 찾는다 |
| `30이 있으면 그 값도 포함해서 오른쪽을 찾고 싶어요` | `TreeSet` | `ceiling(30)` 같은 inclusive neighbor query다 |
| `처리할 때마다 가장 작은 일을 하나씩 가져오고 싶어요` | `PriorityQueue` | 반복 min extraction이 본체다 |

핵심 오진은 보통 여기서 난다.

- `next smallest`를 보고 무조건 `PriorityQueue`로 가는 경우
- `정렬돼 있으니 TreeSet이면 poll도 다 되겠지`라고 생각하는 경우

## 먼저 자를 질문

문제를 읽자마자 아래 두 문장만 먼저 확인하면 된다.

1. 내가 찾는 기준이 `현재 전체 최소값`인가?
2. 아니면 `어떤 x 바로 다음/이전 값`인가?

분기는 단순하다.

| 질문의 실제 모양 | 구조 |
|---|---|
| `min 하나`, `가장 작은 것`, `가장 급한 것`을 계속 꺼낸다 | `PriorityQueue` |
| `x보다 크면서 가장 가까운 값`, `x 바로 다음 값`, `x 근처 값`을 찾는다 | `TreeSet` |

`x`가 문장 안에 명시되면 `TreeSet` 쪽일 가능성이 크고, `전체 중 가장 작은 것`만 반복되면 `PriorityQueue` 쪽일 가능성이 크다.

## 같은 데이터로 보면 더 덜 헷갈린다

데이터가 `[10, 20, 30, 40]`일 때를 계속 보자.

### 1. `PriorityQueue`가 맞는 질문

질문: `가장 작은 값부터 하나씩 모두 처리하고 싶다`

```text
poll() -> 10
poll() -> 20
poll() -> 30
poll() -> 40
```

이 질문은 항상 맨 앞 최소값만 알면 된다.
`25` 같은 기준값은 중요하지 않다.

### 2. `TreeSet`이 맞는 질문

질문: `25 다음 값이 뭐예요?`

```text
ceiling(25) -> 30
higher(25)  -> 30
```

여기서는 `전체 최소값 10`이 답이 아니다.
중요한 건 `25` 기준으로 가장 가까운 오른쪽 값이다.

### 3. exact match가 있으면 더 차이가 난다

질문: `30이 이미 있으면 그 값도 포함해서 다음 값을 보나요?`

```text
ceiling(30) -> 30
higher(30)  -> 40
```

이건 `PriorityQueue`의 `poll()`로는 자연스럽게 표현되지 않는다.
`poll()`은 "30 기준 오른쪽"이 아니라 그냥 현재 최소값을 꺼내기 때문이다.

## 흔한 오해와 함정

- `PriorityQueue`가 정렬 구조니까 `25 다음 값`도 잘 찾을 수 있다고 생각하기 쉽다.
  실제 핵심은 `peek/poll` top 1이지, arbitrary `x` 주변 탐색이 아니다.
- `TreeSet`이 정렬돼 있으니 `PriorityQueue`를 완전히 대체한다고 보면 안 된다.
  핵심 루프가 `반복 poll`이면 `PriorityQueue` 쪽이 질문에 더 직접적이다.
- `next smallest`라는 영어 문장만 보고 고르면 자주 틀린다.
  `next after x`인지, `next global min`인지 먼저 번역해야 한다.
- `ceiling`과 `higher`를 같은 말로 외우면 exact match에서 실수한다.
  같은 값을 포함하면 `ceiling`, strict하게 다음이면 `higher`다.
- 둘 다 정렬을 다룬다고 해서 같은 API를 기대하면 안 된다.
  `TreeSet`은 neighbor query, `PriorityQueue`는 repeated extraction 쪽이 강하다.

## 실무에서 쓰는 모습

두 구조는 서비스 문장에서 신호가 다르게 나온다.

| 장면 | 더 자연스러운 구조 | 이유 |
|---|---|---|
| 스케줄러에서 `가장 이른 작업`을 계속 꺼내 실행 | `PriorityQueue` | 다음 실행 대상은 늘 전체 최소 deadline이다 |
| 예약 시각 모음에서 `10:15 이후 첫 예약` 찾기 | `TreeSet` | 기준 시각 오른쪽 첫 이웃이 필요하다 |
| top-k 후보를 관리하며 가장 작은 후보를 밀어내기 | `PriorityQueue` | 반복 min extraction과 insert가 핵심이다 |
| 점수 cutoff 바로 위 점수 찾기 | `TreeSet` | `higher`/`ceiling`이 직접적이다 |

입문자는 먼저 이렇게 번역하면 안전하다.

- `작업을 하나씩 꺼내 처리` -> `PriorityQueue`
- `값 x 주변을 조회` -> `TreeSet`

## 더 깊이 가려면

- `TreeSet`의 `lower/floor/ceiling/higher` 자체가 아직 헷갈리면 [TreeSet Exact-Match Drill](./treeset-exact-match-drill.md)
- `priority queue`가 FIFO queue와 왜 다른지 먼저 분리하고 싶다면 [Queue vs Deque vs Priority Queue Primer](./queue-vs-deque-vs-priority-queue-primer.md)
- `TreeSet`보다 `TreeMap`이 맞는 순간까지 이어 보고 싶다면 [Heap vs Priority Queue vs Ordered Map Beginner Bridge](./heap-vs-priority-queue-vs-ordered-map-beginner-bridge.md)
- Java 이름표 전체를 `NavigableSet` 기준으로 같이 보고 싶다면 [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)

## 면접/시니어 질문 미리보기

1. `PriorityQueue`로 `x` 바로 다음 값을 찾기 불편한 이유는 무엇인가요?
   주특기가 arbitrary neighbor query가 아니라 현재 top 1 extraction이기 때문이다.
2. `TreeSet`과 `PriorityQueue`가 둘 다 정렬 관련 구조인데 선택 기준은 무엇인가요?
   질문이 `반복 최소 추출`인지 `기준값 주변 탐색`인지로 자른다.
3. exact match가 있을 때 `ceiling`과 `higher`는 왜 다른가요?
   `ceiling`은 inclusive, `higher`는 strict이기 때문이다.

## 한 줄 정리

`next smallest`를 보면 먼저 `x 기준 이웃인가, 전체 최소를 계속 꺼내는가`를 자르고, 전자면 `TreeSet`, 후자면 `PriorityQueue`로 가면 beginner 선택 실수가 크게 줄어든다.
