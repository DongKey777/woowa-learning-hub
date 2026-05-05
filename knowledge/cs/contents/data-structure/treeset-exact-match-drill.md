---
schema_version: 3
title: TreeSet exact-match 이웃 조회 드릴
concept_id: data-structure/treeset-exact-match-drill
canonical: false
category: data-structure
difficulty: beginner
doc_role: drill
level: beginner
language: ko
source_priority: 75
mission_ids: []
review_feedback_tags:
- strict-vs-inclusive-boundary
- treeset-neighbor-query
- treeset-to-treemap-transfer
aliases:
- treeset exact match drill
- treeset lower floor ceiling higher
- navigableset neighbor practice
- sorted set exact neighbor
- treeset 바로 이전 같거나 이전
- treeset 같거나 다음 바로 다음
- treeset lower higher 헷갈림
symptoms:
- lower floor ceiling higher가 exact match에서 자꾸 섞인다
- TreeSet에서 익힌 감각을 TreeMap으로 옮길 때 이름만 바뀌어도 흔들린다
intents:
- drill
prerequisites:
- data-structure/hashset-vs-treeset-beginner-bridge
- data-structure/treeset-treemap-null-boundary-quick-reference
next_docs:
- data-structure/treemap-neighbor-query-micro-drill
- data-structure/treemap-interval-entry-primer
linked_paths:
- contents/data-structure/treeset-treemap-null-boundary-quick-reference.md
- contents/data-structure/hashset-vs-treeset-beginner-bridge.md
- contents/data-structure/treeset-range-view-mini-drill.md
- contents/data-structure/treemap-neighbor-query-micro-drill.md
- contents/data-structure/treemap-interval-entry-primer.md
- contents/language/java/navigablemap-navigableset-mental-model.md
confusable_with:
- data-structure/treeset-range-view-mini-drill
- data-structure/treemap-neighbor-query-micro-drill
- data-structure/treeset-treemap-null-boundary-quick-reference
forbidden_neighbors:
- contents/data-structure/treeset-range-view-mini-drill.md
- contents/data-structure/treemap-neighbor-query-micro-drill.md
expected_queries:
- TreeSet에서 lower floor ceiling higher를 손으로 바로 맞히는 연습 문제를 풀고 싶어
- exact match가 있을 때 strict와 inclusive 이웃 조회를 어떻게 구분하는지 드릴로 확인하고 싶어
- 30이 있을 때 lower와 floor가 왜 달라지는지 숫자 줄 예제로 연습하고 싶어
- TreeSet 감각을 TreeMap lowerKey floorKey로 옮기기 전에 짧게 손추적하고 싶어
- null boundary까지 포함해서 TreeSet 이웃 메서드를 초급 드릴로 복습하고 싶어
- 정렬된 set에서 바로 이전 값과 같거나 이전 값을 헷갈리지 않게 훈련하고 싶어
contextual_chunk_prefix: |
  이 문서는 TreeSet 이웃 조회에서 exact match 포함과 제외를 자꾸
  섞는 학습자가 숫자 줄 기준으로 이전 칸, 그 자리에 머무르기, 다음 칸을
  확인 질문으로 굳히는 drill이다. strict vs inclusive 경계, 값이 있으면
  어디서 멈추는지, 정렬된 값 줄 손추적, null 경계, TreeMap 이름으로
  바꿔도 같은 규칙인지 같은 자연어 paraphrase가 본 문서의 핵심 감각에
  매핑된다.
---
# TreeSet Exact-Match Drill

> 한 줄 요약: `TreeSet`의 `lower/floor/ceiling/higher`는 beginner 기준으로 `바로 이전 / 같거나 이전 / 같거나 다음 / 바로 다음` 네 칸으로 읽으면 손으로 바로 맞힐 수 있고, 그 감각은 `TreeMap`의 `lowerKey/floorKey/ceilingKey/higherKey`로 거의 그대로 넘어간다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [TreeSet, TreeMap Null-Boundary Quick Reference](./treeset-treemap-null-boundary-quick-reference.md)
- [HashSet vs TreeSet Beginner Bridge](./hashset-vs-treeset-beginner-bridge.md)
- [TreeSet Range View Mini Drill](./treeset-range-view-mini-drill.md)
- [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md)
- [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md)
- [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)

retrieval-anchor-keywords: treeset exact match drill, treeset lower floor ceiling higher, navigableset beginner drill, treeset exact match beginner, treeset floor ceiling 처음, lower higher 헷갈림 set, sorted set basics, treeset 뭐예요, treeset neighbor query, treeset exact value practice, treeset 바로 이전 같거나 이전, treeset 같거나 다음 바로 다음, what is treeset lower floor, treeset to treemap bridge, set only intuition treemap

## 핵심 개념

`TreeSet`은 "정렬된 값 줄"이라고 보면 된다.
`TreeMap`처럼 value를 붙이지 않고 값 자체만 다루기 때문에, 초보자에게는 `lower/floor/ceiling/higher` 감각을 떼어 연습하기 더 쉽다.

- `lower(x)`: `x`의 `바로 이전` 값
- `floor(x)`: `x`의 `같거나 이전` 값
- `ceiling(x)`: `x`의 `같거나 다음` 값
- `higher(x)`: `x`의 `바로 다음` 값

먼저 외울 문장은 한 줄이면 충분하다.

> `lower/floor/ceiling/higher`를 `바로 이전 / 같거나 이전 / 같거나 다음 / 바로 다음`으로 먼저 읽고, 그다음에 `strict/inclusive`를 붙이면 덜 헷갈린다.

## 한눈에 보기

같은 숫자 줄을 계속 쓴다.

```text
[10, 20, 30, 40]
```

| 질문 | 답을 찾는 메서드 | 초보자용 shortcut |
|---|---|---|
| `30` 바로 이전 값은? | `lower(30)` | exact match는 빼고 한 칸 왼쪽 |
| `30` 같거나 이전 값은? | `floor(30)` | `30`이 있으면 거기서 멈춤 |
| `30` 같거나 다음 값은? | `ceiling(30)` | `30`이 있으면 거기서 멈춤 |
| `30` 바로 다음 값은? | `higher(30)` | exact match는 빼고 한 칸 오른쪽 |

exact match가 있을 때만 `바로`와 `같거나` 차이가 크게 드러난다.
값이 없는 중간 지점에서는 왼쪽 둘, 오른쪽 둘이 각각 같은 답으로 모인다.

## 상세 분해

### 예제 1. exact match가 있는 값

질문: `30`을 넣으면?

| 호출 | 답 |
|---|---|
| `lower(30)` | `20` |
| `floor(30)` | `30` |
| `ceiling(30)` | `30` |
| `higher(30)` | `40` |

해석: `같거나 이전/다음`만 `30`을 붙잡고, `바로 이전/다음`은 exact match를 건너뛴다.

### 예제 2. 값 사이에 있는 수

질문: `25`를 넣으면?

| 호출 | 답 |
|---|---|
| `lower(25)` | `20` |
| `floor(25)` | `20` |
| `ceiling(25)` | `30` |
| `higher(25)` | `30` |

해석: `25`는 set 안에 없으므로 `바로`와 `같거나` 차이가 사라진다.

### 예제 3. 맨 왼쪽보다 더 작은 값

질문: `5`를 넣으면?

| 호출 | 답 |
|---|---|
| `lower(5)` | `null` |
| `floor(5)` | `null` |
| `ceiling(5)` | `10` |
| `higher(5)` | `10` |

해석: 왼쪽에는 값이 없어서 `null`이 나온다. 이건 에러가 아니라 정상 결과다.

### 예제 4. 맨 오른쪽보다 더 큰 값

질문: `45`를 넣으면?

| 호출 | 답 |
|---|---|
| `lower(45)` | `40` |
| `floor(45)` | `40` |
| `ceiling(45)` | `null` |
| `higher(45)` | `null` |

해석: 이번에는 오른쪽 값이 없어서 `ceiling/higher`가 `null`이 된다.

## 흔한 오해와 함정

- `floor`를 "이전 값"으로만 외우면 exact match에서 틀린다. beginner shortcut은 `같거나 이전`이다.
- `ceiling`을 "다음 값"으로만 외우면 exact match에서 틀린다. beginner shortcut은 `같거나 다음`이다.
- `lower`와 `floor`, `higher`와 `ceiling`을 같은 말처럼 쓰면 대부분 exact match 문제에서 실수한다.
- `null`이 나오면 예외라고 느끼기 쉽지만, 단지 그 방향에 이웃 값이 없다는 뜻이다.
- `TreeSet`인데도 `key/value`처럼 생각하면 오히려 헷갈린다. 이 문서는 값 하나짜리 줄로만 보면 된다.
- "`비어 있을 때도 `floor`가 예외를 던지나?`처럼 null boundary 자체가 먼저 흔들리면 [TreeSet, TreeMap Null-Boundary Quick Reference](./treeset-treemap-null-boundary-quick-reference.md)부터 보고 돌아오는 편이 빠르다.

## 실무에서 쓰는 모습

`TreeSet<Integer>`나 `TreeSet<LocalTime>`은 "값 자체만 정렬된 상태로 유지"하면 되는 장면에서 가볍게 쓴다.
예를 들어 예약 시작 시각 목록만 관리한다면 `10:00 이후 첫 시각`, `현재보다 바로 이전 시각` 같은 질문을 `ceiling`과 `lower`로 바로 읽을 수 있다.

```java
NavigableSet<Integer> slots = new TreeSet<>(List.of(10, 20, 30, 40));

Integer previous = slots.floor(25);   // 20
Integer next = slots.ceiling(25);     // 30
Integer exactOrNext = slots.ceiling(30); // 30
```

값만 있으면 `TreeSet`, 값에 설명이나 종료 시각까지 붙여야 하면 `TreeMap`으로 넘어가면 된다.

## TreeMap으로 넘길 때 번역표

`TreeSet` drill을 풀 수 있는데 `TreeMap` 이름이 붙는 순간 갑자기 낯설어지는 초보자는 보통 `map`이라는 단어 때문에 새 규칙이 생겼다고 느낀다.
하지만 exact-match 규칙은 그대로고, 바뀌는 것은 "`값만 읽나`"에서 "`key로 줄을 찾고 value도 들고 가나`"뿐이다.

| `TreeSet`에서 이미 아는 질문 | `TreeSet` 호출 | `TreeMap`으로 옮긴 호출 | 그대로 유지되는 규칙 |
|---|---|---|---|
| 바로 이전 값 | `lower(30)` | `lowerKey(30)` | exact match 제외 |
| 같거나 바로 이전 값 | `floor(30)` | `floorKey(30)` | exact match 포함 |
| 같거나 바로 다음 값 | `ceiling(30)` | `ceilingKey(30)` | exact match 포함 |
| 바로 다음 값 | `higher(30)` | `higherKey(30)` | exact match 제외 |

초보자용으로 더 짧게 줄이면 아래 두 줄이다.

- `TreeSet`에서 맞히던 `바로 이전 / 같거나 이전 / 같거나 다음 / 바로 다음` 감각은 `TreeMap`에서도 이름만 `lowerKey/floorKey/ceilingKey/higherKey`로 바뀐다.
- `TreeMap`이 추가하는 새 질문은 "`그 시간에 어떤 value가 붙어 있지?`"이지, exact-match 규칙 자체가 아니다.

예를 들어 `[10, 20, 30, 40]`을 `TreeSet`으로 보던 감각은 아래 예약표로 거의 그대로 옮겨진다.

```text
10 -> A
20 -> B
30 -> C
40 -> D
```

`floor(30) == 30`을 이미 이해했다면 `floorKey(30) == 30`도 같은 이유로 읽는다.
이 다음 단계에서 value까지 함께 읽고 싶을 때만 [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md)과 [TreeMap Key/Entry Strictness Bridge](./treemap-key-entry-strictness-bridge.md)로 넘어가면 된다.

## 더 깊이 가려면

- `Set` 선택 자체가 아직 흐리면 [HashSet vs TreeSet Beginner Bridge](./hashset-vs-treeset-beginner-bridge.md)
- 같은 이웃 조회를 예약표 `key -> value` 기준으로 옮겨 보고 싶다면 [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md)
- `TreeSet`에서 `subSet/headSet/tailSet`으로 단순 range slicing까지 한 칸 더 가고 싶다면 [TreeSet Range View Mini Drill](./treeset-range-view-mini-drill.md)
- `subMap`, 충돌 검사, gap check처럼 `TreeMap` range 감각까지 넓히고 싶다면 [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md)
- Java 이름표 전체를 `NavigableSet`/`NavigableMap` 기준으로 같이 보고 싶다면 [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)

## 면접/시니어 질문 미리보기

1. `TreeSet`과 `HashSet`의 선택 기준은 무엇인가요?
   정렬, 이웃 값, 범위 조회가 필요하면 `TreeSet`, membership만 필요하면 `HashSet`이다.
2. exact match가 있을 때 `floor`와 `lower`는 왜 다른가요?
   `floor`는 inclusive, `lower`는 strict이기 때문이다.
3. `TreeSet`으로 충분한데 `TreeMap`으로 가는 순간은 언제인가요?
   값 자체만이 아니라 `시작 시각 -> 예약 정보`처럼 value를 함께 읽어야 할 때다.

## 한 줄 정리

`TreeSet`의 `lower/floor/ceiling/higher`는 `바로 이전 / 같거나 이전 / 같거나 다음 / 바로 다음` 네 칸으로 먼저 번역하면 초급 손추적이 훨씬 쉬워진다.
