---
schema_version: 3
title: TreeMap 문자열 prefix와 사전순 range 미니 드릴
concept_id: data-structure/treemap-string-prefix-range-mini-drill
canonical: false
category: data-structure
difficulty: beginner
doc_role: drill
level: beginner
language: ko
source_priority: 74
mission_ids: []
review_feedback_tags:
- prefix-vs-range-intent
- string-key-ordered-map
- neighbor-vs-prefix-confusion
aliases:
- treemap string prefix range mini drill
- startswith vs submap beginner
- treemap 문자열 prefix range
- 사전순 range와 prefix 차이
- string key ordered map beginner
- prefix query vs neighbor query
symptoms:
- startsWith와 subMap이 비슷해 보여서 TreeMap이 prefix 검색 구조라고 착각한다
- 문자열 key에서 prefix 질문인지 ordered neighbor/range 질문인지 분기가 안 된다
- subMap 결과가 우연히 같아서 의도를 잘못 읽는다
intents:
- comparison
- drill
prerequisites:
- data-structure/trie-prefix-search-vs-treemap-ordered-map-beginner-card
- data-structure/treemap-neighbor-query-micro-drill
next_docs:
- data-structure/trie-prefix-search-autocomplete
- data-structure/treemap-submap-schedule-window-mini-drill
linked_paths:
- contents/data-structure/trie-prefix-search-vs-treemap-ordered-map-beginner-card.md
- contents/data-structure/treemap-neighbor-query-micro-drill.md
- contents/data-structure/treemap-submap-schedule-window-mini-drill.md
- contents/data-structure/trie-prefix-search-autocomplete.md
- contents/language/java/submap-boundaries-primer.md
- contents/system-design/search-system-design.md
confusable_with:
- data-structure/trie-prefix-search-vs-treemap-ordered-map-beginner-card
- data-structure/treemap-neighbor-query-micro-drill
- data-structure/treemap-submap-schedule-window-mini-drill
forbidden_neighbors:
- contents/data-structure/trie-prefix-search-vs-treemap-ordered-map-beginner-card.md
- contents/data-structure/treemap-neighbor-query-micro-drill.md
expected_queries:
- startsWith와 TreeMap subMap이 왜 같은 질문이 아닌지 문자열 예제로 보고 싶어
- TreeMap이 prefix 검색 구조인지 ordered map 구조인지 처음부터 구분하고 싶어
- app prefix 후보 찾기와 app 다음 문자열 찾기를 서로 다른 의도로 분리해줘
- 문자열 key에서 neighbor query와 range query가 어떻게 다른지 초급 드릴로 확인하고 싶어
- subMap 결과가 prefix 검색처럼 보여서 헷갈릴 때 볼 문서가 필요해
- ordered map string range basics를 한국어 예제로 다시 보고 싶어
contextual_chunk_prefix: |
  이 문서는 문자열 key를 다루는 입문자가 startsWith 같은 접두사
  질문과 TreeMap subMap, higherKey 같은 사전순 범위 질문을 확인
  질문으로 굳히는 drill이다. app으로 시작하는 후보 모으기, app 다음
  문자열 하나 찾기, 문자열 구간을 창처럼 자르기, prefix 자동완성과
  ordered map 범위 조회 구분, 결과가 비슷해도 의도가 다른 이유,
  사전순 경계를 먼저 세우기 같은 자연어 paraphrase가 본 문서의 분기
  감각에 매핑된다.
---
# TreeMap 문자열 Prefix vs 사전순 Range Mini Drill

> 한 줄 요약: 문자열 key에서 `startsWith` 질문과 `TreeMap.subMap(...)` 질문은 비슷해 보여도, 전자는 "접두사 일치"를 묻고 후자는 "사전순 경계 사이"를 묻는다는 점을 concrete key로 먼저 분리해 두면 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [Trie Prefix Search vs TreeMap Ordered Map Beginner Card](./trie-prefix-search-vs-treemap-ordered-map-beginner-card.md)
- [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md)
- [TreeMap `subMap` Schedule-Window Mini Drill](./treemap-submap-schedule-window-mini-drill.md)
- [Trie Prefix Search / Autocomplete](./trie-prefix-search-autocomplete.md)
- [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](../language/java/submap-boundaries-primer.md)
- [Search 시스템 설계](../system-design/search-system-design.md)

retrieval-anchor-keywords: treemap string prefix range, startswith vs submap, lexicographic submap beginner, treemap string key range, startswith intent beginner, 문자열 prefix range 헷갈림, treemap submap 뭐예요, startswith와 submap 차이, what is lexicographic range, prefix query 처음, ordered map string range basics

## 핵심 개념

문자열 key를 보면 beginner가 가장 자주 섞는 두 문장은 이렇다.

- `"app"`으로 시작하는 key를 모아 줘
- `"app"` 이상 `"apq"` 미만 key를 보여 줘

겉으로는 비슷해 보여도 질문의 중심이 다르다.

- `startsWith("app")`: 각 문자열이 `app`으로 시작하는지 묻는다
- `subMap("app", true, "apq", false)`: 정렬된 key가 `[app, apq)` 범위 안에 드는지 묻는다

즉 결과가 우연히 비슷할 수는 있어도, `TreeMap`이 prefix 의미를 아는 것은 아니다.

질문이 `"app" 다음 key 하나가 뭐예요?`처럼 이웃 조회라면 이 문서보다 [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md)로 바로 가는 편이 정확하다. 여기서는 prefix와 range가 헷갈리는 장면만 푼다.

> `startsWith`는 문자열 규칙이고, `subMap`은 사전순 경계 규칙이다.

## 한눈에 보기

같은 key 줄을 계속 쓴다.

```text
ape, app, apple, apply, apron, banana
```

| 질문 | 먼저 읽는 방식 | 손으로 읽는 답 |
|---|---|---|
| `startsWith("app")`인 key는? | 접두사 일치 검사 | `app`, `apple`, `apply` |
| `subMap("app", true, "apq", false)`는? | 사전순 범위 `[app, apq)` | `app`, `apple`, `apply` |
| `"app"` 다음 사전순 key는? | `higherKey("app")` | `apple` |
| `subMap("apple", true, "banana", false)`는? | 사전순 범위 `[apple, banana)` | `apple`, `apply`, `apron` |

첫 두 줄이 핵심이다. 결과가 같아 보여도 읽는 기준이 다르다.

- `startsWith("app")`는 문자열 앞부분이 `app`인지 본다
- `subMap("app", ..., "apq", ...)`는 `app` 이상 `apq` 미만이라는 줄 위치를 본다

## 미니 드릴

아래 key들이 `TreeMap<String, Integer>`에 정렬돼 있다고 하자.

```text
ape, app, apple, apply, apron, banana
```

### 1. prefix 질문

질문:

```text
startsWith("app")인 key는?
```

답:

- `app`
- `apple`
- `apply`

해석: 각 단어의 맨 앞이 `app`인지 본다. `apron`은 `ap`로 시작하지만 `app`로 시작하지 않으니 빠진다.

### 2. 사전순 range 질문

질문:

```java
scores.subMap("app", true, "apq", false)
```

답:

- `app`
- `apple`
- `apply`

해석: 이번에는 prefix를 검사한 것이 아니라, 사전순으로 `app <= key < apq`인 key를 모았다. 이 예시에서는 결과가 prefix 질문과 같게 나왔을 뿐이다.

### 3. 왜 intent가 다르다고 말하나

질문:

```java
scores.subMap("apple", true, "banana", false)
```

답:

- `apple`
- `apply`
- `apron`

해석: 여기서는 `apple`로 시작하지 않는 `apron`도 들어온다. 이유는 prefix가 아니라 사전순 범위를 잘랐기 때문이다. `apron`은 `apple`보다 뒤이고 `banana`보다 앞이라 창 안에 들어온다.

### 4. 다음 key 하나를 찾는 질문

질문:

```java
scores.higherKey("app")
```

답:

- `apple`

해석: 이건 prefix 묶음도 아니고 range 창도 아니다. 정렬된 줄에서 `"app"` 바로 오른쪽 한 칸을 찾는 ordered neighbor 질문이다.

## 흔한 오해와 함정

- `subMap("app", "apq")` 결과가 `startsWith("app")`와 같았으니 `TreeMap`이 prefix 검색 구조라고 생각하기 쉽다. 아니다. 지금은 사전순 경계를 prefix처럼 잡아 둔 것뿐이다.
- `startsWith("app")`는 true/false 판단을 각 문자열에 한다. 반면 `subMap(...)`은 정렬된 key 창을 한 번에 자른다.
- `"app"` 다음 key를 찾고 싶을 때 `startsWith`로 접근하면 질문을 잘못 읽은 셈이다. 이 경우 핵심은 prefix가 아니라 `higherKey` 같은 이웃 조회다.
- `subMap("apple", "banana")`를 보면 "`apple` 계열만 나오겠네"라고 착각하기 쉽다. 실제로는 그 사이에 있는 `apron`도 들어온다.

## 실무에서 쓰는 모습

검색창 자동완성처럼 `"app"`를 입력할 때마다 같은 prefix 후보를 모으는 문제는 `startsWith` 의도에 가깝다. 구조 선택까지 가면 `Trie`나 prefix index 쪽 감각이 먼저 붙는다.

반대로 운영 도구에서 `"apple"` 이상 `"banana"` 미만 사용자 id만 훑기, `"app"` 다음 key 하나 찾기, `"m"` 구간만 순서대로 보기 같은 요구는 ordered map 질문이다. 이때는 `TreeMap`의 `subMap`, `higherKey`, `ceilingKey`가 더 직접적이다.

초급자는 먼저 이렇게 자르면 안전하다.

- `"어떤 prefix로 시작하나"` -> prefix 의도
- `"어느 경계 사이에 있나"` -> range 의도
- `"바로 다음/이전이 뭔가"` -> neighbor 의도

## 더 깊이 가려면

- 문자열 key에서 `Trie`와 `TreeMap`의 역할을 먼저 자르려면 [Trie Prefix Search vs TreeMap Ordered Map Beginner Card](./trie-prefix-search-vs-treemap-ordered-map-beginner-card.md)
- `TreeMap` range 창을 시간표 예제로 더 연습하려면 [TreeMap `subMap` Schedule-Window Mini Drill](./treemap-submap-schedule-window-mini-drill.md)
- Java range API의 inclusive/exclusive 경계를 더 고정하려면 [`subSet`/`headSet`/`tailSet`, `subMap`/`headMap`/`tailMap` Boundary Primer](../language/java/submap-boundaries-primer.md)
- prefix 검색 구조 자체를 더 보고 싶다면 [Trie Prefix Search / Autocomplete](./trie-prefix-search-autocomplete.md)

## 한 줄 정리

문자열 key에서 `startsWith`와 `TreeMap.subMap(...)`이 비슷해 보여도, 전자는 "접두사 일치", 후자는 "사전순 경계 사이"를 묻는다는 점을 concrete key로 먼저 분리하면 실전에서 덜 헷갈린다.
