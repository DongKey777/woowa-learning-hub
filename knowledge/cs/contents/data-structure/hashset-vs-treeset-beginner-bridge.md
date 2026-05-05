---
schema_version: 3
title: HashSet vs TreeSet Beginner Bridge
concept_id: data-structure/hashset-vs-treeset-beginner-bridge
canonical: false
category: data-structure
difficulty: beginner
doc_role: bridge
level: beginner
language: ko
source_priority: 85
mission_ids: []
review_feedback_tags:
- set-membership-vs-order
- treeset-neighbor-query
- lower-floor-boundary
aliases:
- hashset vs treeset beginner
- hashset treeset 차이
- set 처음 배우는데 뭐 써요
- hashset 언제 쓰는지
- treeset 언제 쓰는지
- 왜 treeset 써요
- sorted set 뭐예요
- 중복 제거만 필요할 때
- 정렬된 set 필요할 때
- floor ceiling set 뭐예요
- set range query beginner
- dedupe only vs sorted set
- 처음 배우는데 hashset treeset 큰 그림
- 해시셋 트리셋 차이
- 왜 lower랑 floor가 달라요 set
symptoms:
- Set을 써야 하는 건 알겠는데 중복 체크만 하면 되는지 정렬까지 필요한지 판단이 안 돼
- HashSet으로 충분한지 TreeSet으로 넘어가야 하는지 기준이 모호해
- lower floor ceiling 같은 이웃 값 API가 왜 Set 선택 문제로 이어지는지 헷갈려
intents:
- comparison
prerequisites:
- data-structure/basic
- data-structure/map-vs-set-requirement-bridge
next_docs:
- data-structure/treeset-exact-match-drill
- data-structure/treemap-interval-entry-primer
- language/hashset-vs-treeset-duplicate-semantics
linked_paths:
- contents/data-structure/map-vs-set-requirement-bridge.md
- contents/data-structure/treeset-exact-match-drill.md
- contents/data-structure/hashmap-treemap-linkedhashmap-beginner-selection-primer.md
- contents/data-structure/treemap-interval-entry-primer.md
- contents/language/java/hashset-vs-treeset-duplicate-semantics.md
- contents/algorithm/dfs-bfs-intro.md
confusable_with:
- data-structure/map-vs-set-requirement-bridge
- data-structure/treemap-interval-entry-primer
- language/hashset-vs-treeset-duplicate-semantics
forbidden_neighbors: []
expected_queries:
- set을 처음 배우는데 hashset이랑 treeset 중 뭐부터 골라야 해?
- 중복 제거만 하면 되는데 treeset까지 써야 하나요?
- treeset은 언제 쓰고 hashset은 언제 쓰는지 beginner 기준으로 설명해줘
- floor, ceiling 같은 이웃 값 조회가 필요하면 왜 treeset이 맞아요?
- 정렬된 set이 필요한지 그냥 membership만 필요한지 어떻게 구분해?
contextual_chunk_prefix: |
  이 문서는 Set을 처음 고르는 학습자가 중복 제거만 필요한지, 정렬된 순서와
  가장 가까운 값·범위 조회까지 필요한지 기준으로 HashSet과 TreeSet을 연결해
  선택하게 돕는 bridge다. 값 존재 확인, 정렬된 집합 필요, 바로 앞뒤 값 찾기,
  범위 안 값 보기, lower floor 차이 같은 자연어 paraphrase가 본 문서의 선택
  기준에 매핑된다.
---
# HashSet vs TreeSet Beginner Bridge

> 한 줄 요약: `Set`을 고를 때는 "중복만 막으면 되나"와 "정렬된 순서, 이웃 값, 범위까지 필요하나"를 먼저 나누면 `HashSet`과 `TreeSet` 선택이 훨씬 쉬워진다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [Map vs Set Requirement Bridge](./map-vs-set-requirement-bridge.md)
- [TreeSet Exact-Match Drill](./treeset-exact-match-drill.md)
- [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md)
- [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md)
- [HashSet vs TreeSet Duplicate Semantics](../language/java/hashset-vs-treeset-duplicate-semantics.md)
- [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)

retrieval-anchor-keywords: hashset vs treeset beginner, hashset treeset 차이, set 처음 배우는데 뭐 써요, hashset 언제 쓰는지, treeset 언제 쓰는지, 왜 treeset 써요, sorted set 뭐예요, 중복 제거만 필요할 때, 정렬된 set 필요할 때, floor ceiling set 뭐예요, set range query beginner, dedupe only vs sorted set, 처음 배우는데 hashset treeset 큰 그림, 해시셋 트리셋 차이, 왜 lower랑 floor가 달라요 set

## 핵심 개념

`HashSet`과 `TreeSet`은 둘 다 "`중복 없는 값 모음`"을 만들지만, 먼저 지키는 약속이 다르다.

- `HashSet`: "이 값이 있나?"를 빠르게 확인하는 기본 set
- `TreeSet`: 중복도 막고 값을 정렬된 상태로 유지하는 set

처음엔 이렇게 기억하면 충분하다.

- `HashSet`은 출입 명단
- `TreeSet`은 출입 명단 + 정렬된 번호표

초급자가 먼저 물어야 할 질문은 이것이다.

> 나는 정말 `있다/없다`만 알면 되나, 아니면 `가장 가까운 값`, `정렬된 순서`, `범위`까지 필요하나?

이 문서는 `"Set 처음 배우는데 HashSet이랑 TreeSet 중 뭐부터 골라요?"` 같은 첫 질문에서 바로 걸리도록 만든 entrypoint primer다.

이 질문으로 자르면 `HashSet`과 `TreeSet`을 이름이 아니라 요구사항으로 고르게 된다.

## 한눈에 보기

| 지금 필요한 것 | 먼저 볼 구조 | 왜 이 구조가 맞나 |
|---|---|---|
| 중복 제거, membership 확인 | `HashSet` | 질문이 `"이미 봤나?"`에서 끝난다 |
| 항상 정렬된 순서로 순회 | `TreeSet` | 넣을 때부터 정렬 상태를 유지한다 |
| 기준값 바로 앞/뒤 찾기 | `TreeSet` | `floor`, `ceiling`, `lower`, `higher`가 자연스럽다 |
| 범위 안의 값만 보기 | `TreeSet` | sorted set의 range view가 맞다 |

같은 `Set`이라도 실제 질문 문장을 붙이면 차이가 더 또렷하다.

| 질문 문장 | `HashSet` 신호 | `TreeSet` 신호 |
|---|---|---|
| `이미 처리한 ID인가?` | 강함 | 약함 |
| `가장 가까운 다음 예약 시각은?` | 약함 | 강함 |
| `사전순으로 태그를 보여 줘야 하나?` | 약함 | 강함 |
| `중복만 막으면 끝인가?` | 강함 | 약함 |

README에서 beginner가 자주 멈추는 `lower/floor/ceiling/higher`는 `TreeSet`에서도 아래처럼 바로 번역하면 된다.

| 헷갈리는 말 | `TreeSet`에서 바로 읽는 법 | 짧은 치트키 |
|---|---|---|
| `왜 lower랑 floor가 달라요?` | 같은 값이 있으면 `lower`는 건너뛰고 `floor`는 멈춘다 | `lower` = `바로 이전`, `floor` = `같거나 이전` |
| `왜 higher랑 ceiling이 달라요?` | 같은 값이 있으면 `higher`는 건너뛰고 `ceiling`은 멈춘다 | `higher` = `바로 다음`, `ceiling` = `같거나 다음` |
| `exact match 포함 여부가 헷갈려요` | `floor/ceiling`만 같은 값을 포함한다 | inclusive pair |
| `같은 값이 있으면 제외하나요?` | `lower/higher`는 같은 값을 제외한다 | strict pair |

이 네 줄은 `TreeSet`을 처음 볼 때 방향보다 포함 여부를 먼저 고정하는 용도다.

## 먼저 자르는 질문

처음엔 아래 세 질문만 순서대로 보면 된다.

1. 답이 `있다/없다`면 충분한가?
2. 항상 정렬된 순서로 보여 주거나 꺼내야 하는가?
3. 기준값 주변(`바로 이전`, `바로 다음`)이나 범위(`10~20`)를 자주 묻는가?

분기 기준은 단순하다.

- 1번만 `예`면 `HashSet`
- 2번이나 3번이 `예`면 `TreeSet`

입문자가 자주 놓치는 포인트는 "`정렬된 출력 한 번`"과 "`정렬된 구조를 계속 유지`"가 다르다는 점이다.
마지막에 한 번만 정렬해서 보여 주면 `HashSet`으로 충분할 수 있지만, 매번 이웃 값과 범위를 묻는다면 `TreeSet` 쪽이 더 직접적이다.

증상 문장을 API 이름으로 바로 바꾸면 더 빨리 분기된다.

| 문제 문장 | 실제 질문 | 구조 |
|---|---|---|
| `이 값이 이미 있나?` | membership only | `HashSet` |
| `30 바로 이전 값은?` | `lower(30)` | `TreeSet` |
| `30이 있으면 그 값도 포함한 다음 값은?` | `ceiling(30)` | `TreeSet` |
| `왜 lower랑 floor가 달라요?` | strict vs inclusive neighbor query | `TreeSet` |

## 같은 도메인도 요구가 달라지면 갈린다

주문/예약 서비스에서도 문장에 따라 선택이 달라진다.

| 같은 서비스 장면 | 먼저 고를 구조 | 이유 |
|---|---|---|
| `이 주문번호를 이미 처리했나?` | `HashSet<String>` | membership만 확인한다 |
| `활성 쿠폰 코드를 사전순으로 보여 주기` | `TreeSet<String>` | 정렬된 순회가 기능 요구다 |
| `12:00 이후 첫 예약 시각 찾기` | `TreeSet<LocalTime>` | 이웃 탐색이 필요하다 |
| `이번 배치에서 이미 본 회원 ID 막기` | `HashSet<Long>` | 중복 방지가 핵심이다 |

짧은 코드로 보면 차이가 더 잘 보인다.

```java
Set<String> processedOrderIds = new HashSet<>();
NavigableSet<Integer> activeScores = new TreeSet<>();
```

첫 줄은 `"봤나?"`를 답하는 용도다.
둘째 줄은 `"정렬된 상태에서 가장 가까운 점수는?"` 같은 질문까지 답할 수 있다.

## 흔한 오해와 함정

- "`TreeSet`이 더 많은 기능이 있으니 항상 더 좋은가요?"
  아니다. 중복만 막으면 되는 문제에 `TreeSet`을 쓰면 의도보다 구조가 무거워질 수 있다.
- "`HashSet`도 나중에 정렬하면 되니 `TreeSet`은 필요 없나요?"
  마지막 한 번 정렬은 가능하지만, 매 조회마다 `floor/ceiling/range`를 묻는 상황은 `TreeSet`이 더 자연스럽다.
- "`TreeSet`은 value를 저장하는 map 비슷한 구조인가요?"
  아니다. 여전히 `Set`이다. 값 하나만 저장하고, 그 값의 정렬 규칙이 중요할 뿐이다.
- "`visited`는 항상 `HashSet`인가요?"
  방문 여부만 체크하면 보통 `HashSet`이다. 하지만 거리나 부모 정보까지 저장하면 [Map vs Set Requirement Bridge](./map-vs-set-requirement-bridge.md)로 넘어가 `Map`을 보는 편이 맞다.
- "`TreeSet`을 고르면 자동으로 삽입 순서도 유지되나요?"
  아니다. 삽입 순서가 아니라 정렬 순서다. 삽입 순서가 필요하면 set보다 map/linked 계열 요구를 다시 봐야 한다.

## 실무에서 쓰는 모습

`HashSet`은 중복 요청 차단, 이미 본 ID 기록, 배치 중복 제거처럼 "`있는가`만 답하면 끝"인 장면에 잘 맞는다.

`TreeSet`은 예약 시각 집합, 정책 구간 경계, 정렬된 태그 목록처럼 "`정렬된 채로 다뤄야 하는가`"가 중요한 장면에 잘 맞는다.

특히 아래처럼 요구가 바뀌는 순간을 주의하면 좋다.

- `중복만 막기` -> `HashSet`
- `중복도 막고 항상 정렬된 목록 보여 주기` -> `TreeSet`
- `중복도 막고 다음 값/이전 값 찾기` -> `TreeSet`

## 더 깊이 가려면

- `Set`과 `Map` 자체가 아직 헷갈리면 [Map vs Set Requirement Bridge](./map-vs-set-requirement-bridge.md)
- `TreeSet`과 `TreeMap`의 정렬/이웃 탐색 감각을 같이 잡고 싶으면 [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md)
- `TreeSet`과 `PriorityQueue`를 `next smallest` 문장 기준으로 먼저 분리하고 싶다면 [TreeSet vs PriorityQueue Neighbor-Choice Card](./treeset-vs-priorityqueue-neighbor-choice-card.md)
- `TreeSet`의 `floor/ceiling` 감각을 예약 예제로 보고 싶으면 [TreeMap Interval Entry Primer](./treemap-interval-entry-primer.md)
- 값만 있는 `TreeSet`에서 `lower/floor/ceiling/higher` exact match를 먼저 손으로 맞히고 싶다면 [TreeSet Exact-Match Drill](./treeset-exact-match-drill.md)
- Java에서 `HashSet`과 `TreeSet`의 실제 중복 판정 차이를 보려면 [HashSet vs TreeSet Duplicate Semantics](../language/java/hashset-vs-treeset-duplicate-semantics.md)
- `visited set`이 BFS에서 어떻게 쓰이는지 복습하려면 [DFS와 BFS 입문](../algorithm/dfs-bfs-intro.md)

## 면접/시니어 질문 미리보기

1. 왜 `HashSet` 대신 항상 `TreeSet`을 쓰지 않나요?
   정렬, 이웃 값, 범위 조회가 필요 없으면 `HashSet`이 더 직접적이기 때문이다.
2. `HashSet`에서 마지막에 정렬하는 것과 `TreeSet`을 쓰는 것은 언제 갈리나요?
   한 번 보여 주기용 정렬이면 전자, 조회 중 계속 정렬된 탐색이 필요하면 후자다.
3. `TreeSet`을 보면 `TreeMap`도 같이 떠올려야 하나요?
   그렇다. 둘 다 정렬과 이웃 탐색이 핵심이어서 beginner 분기에서는 함께 이해하면 편하다.

## 한 줄 정리

`있나?`에서 끝나면 `HashSet`, `정렬된 순서나 주변 값까지 필요하면 TreeSet`이라고 먼저 자르면 beginner의 set 선택 실수가 크게 줄어든다.
