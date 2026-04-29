# Trie Prefix Search vs TreeMap Ordered Map Beginner Card

> 한 줄 요약: 문자열 key를 다룬다고 `Trie`와 `TreeMap`이 같은 자리를 차지하는 것은 아니다. `"이 prefix로 시작하는 후보 묶음"`이 핵심이면 `Trie`, `"사전순 다음/이전 key"`나 `"정렬된 범위"`가 핵심이면 `TreeMap`으로 먼저 자르면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [Trie vs HashMap: exact lookup이냐 prefix search냐](./trie-vs-hashmap-exact-lookup-beginner-card.md)
- [TreeMap 문자열 Prefix vs 사전순 Range Mini Drill](./treemap-string-prefix-range-mini-drill.md)
- [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md)
- [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md)
- [Trie Prefix Search / Autocomplete](./trie-prefix-search-autocomplete.md)
- [`subMap()` / `headMap()` / `tailMap()` Live View Primer](../language/java/treemap-range-view-live-window-primer.md)
- [Search 시스템 설계](../system-design/search-system-design.md)

retrieval-anchor-keywords: trie vs treemap beginner, prefix search vs ordered map, string key trie or treemap, trie prefix beginner, treemap string range beginner, prefix search 처음, 문자열 key trie treemap 헷갈림, 왜 trie 말고 treemap, startswith vs next key, neighbor lookup vs autocomplete, next string lookup, next string vs prefix search, 문자열 다음 key 찾기, 사전순 다음 문자열, string range lookup

## 핵심 개념

입문자가 가장 자주 섞는 질문은 보통 이 둘이다.

- `"ann"`으로 시작하는 모든 사용자 id 후보를 보여 줄까?
- `"anna"` 다음 사전순 사용자 id 하나를 찾을까?

둘 다 문자열 key를 다루지만 질문의 축이 다르다.

- `Trie`: prefix 자체를 따라 내려가며 `"ann"` 아래 후보 묶음을 찾는 구조
- `TreeMap`: 문자열 key를 정렬해 `"바로 다음 key"`, `"바로 이전 key"`, `"이 구간"`을 찾는 구조

짧게 외우면 이렇다.

> `prefix 묶음 찾기`면 `Trie`, `정렬된 이웃/범위`면 `TreeMap`

이 카드는 특히 `prefix search는 알겠는데 다음 문자열은 뭐로 찾지?`, `startsWith랑 사전순 range lookup이 왜 다른가요?` 같은 follow-up 질문을 받았을 때 바로 이어서 읽도록 만든 bridge다.

## 한눈에 보기

| 지금 필요한 답 | 먼저 떠올릴 구조 | 왜 이쪽이 맞나 |
|---|---|---|
| `"ann"`으로 시작하는 후보 목록 | `Trie` | prefix 경로를 바로 따라간다 |
| `"anna"` 다음 사전순 id 하나 | `TreeMap` | 정렬된 key의 오른쪽 이웃을 찾는다 |
| `"ann"` 접두사 후보를 자동완성 5개로 보여 주기 | `Trie` | prefix가 중심인 질의다 |
| `"anna"` 이상 `"annz"` 미만 key 범위 보기 | `TreeMap` | 사전순 범위 view가 중심이다 |
| `"ann"`이라는 exact key가 있나 | 보통 `HashMap` 또는 `TreeMap` | prefix보다 exact lookup이 더 직접적이다 |

이 문서의 첫 분기는 "문자열이냐"가 아니라 "질문이 prefix냐, ordered range/neighbor냐"다.
손으로 더 짧게 구분해 보고 싶다면 [TreeMap 문자열 Prefix vs 사전순 Range Mini Drill](./treemap-string-prefix-range-mini-drill.md)에서 `startsWith("app")`와 `subMap("app", "apq")`를 같은 key 줄 위에서 바로 비교해 보면 된다.

## 같은 문자열도 질문이 바뀌면 구조가 바뀐다

같은 사용자 id 목록 `anna`, `anne`, `annie`, `bob`이 있다고 하자.

| 같은 데이터 | 질문 | 첫 구조 |
|---|---|---|
| `anna`, `anne`, `annie`, `bob` | `"ann"`으로 시작하는 id 후보는? | `Trie` |
| `anna`, `anne`, `annie`, `bob` | `"anna"` 다음 id는? | `TreeMap` |
| `anna`, `anne`, `annie`, `bob` | `"ann"` prefix 후보를 점수순으로 보여 줄까? | `Trie` + 랭킹 로직 |
| `anna`, `anne`, `annie`, `bob` | `"anne"` 이상 `"bob"` 미만 구간을 훑을까? | `TreeMap` |

즉 같은 문자열 key라도 `startsWith`류 질문이면 `Trie`, `next/previous/range`류 질문이면 `TreeMap`이 먼저 떠올라야 한다.

## 흔한 오해와 함정

- `TreeMap도 문자열이 정렬되니 prefix search 구조 아닌가요?`
  아니다. `TreeMap`의 기본 감각은 ordered map이다. prefix 후보 묶음보다 이웃과 범위를 먼저 떠올리는 편이 맞다.
- `Trie면 문자열 검색은 다 해결되나요?`
  아니다. `"다음 단어 하나"`, `"이 key보다 바로 큰 값"` 같은 ordered neighbor 질문은 `TreeMap` 쪽 감각이 더 직접적이다.
- `TreeMap으로도 prefix 범위를 흉내 낼 수 있으면 Trie가 필요 없나요?`
  작은 규모에서는 그럴 수 있다. 하지만 초보자 mental model로는 `TreeMap = ordered range/neighbor`, `Trie = prefix search`로 먼저 분리해야 덜 헷갈린다.
- `자동완성은 TreeMap으로도 되나요?`
  일부는 가능해도, 자동완성의 중심 질문은 보통 prefix 후보 수집이라 `Trie`가 더 자연스러운 출발점이다.

## 실무에서 쓰는 모습

검색창, 명령어 추천, 사전 후보 제안처럼 `"spr"`를 입력할 때마다 앞부분이 같은 문자열들을 모아야 하면 `Trie`가 자연스럽다. 핵심이 `"이 prefix 아래 후보 몇 개"`이기 때문이다.

반대로 사용자 id를 사전순으로 관리하며 `"현재 id 다음 사람"`, `"a로 시작하는 구간만 순서대로 훑기"`, `"이 key 이상 첫 사용자"`를 자주 묻는 화면이나 운영 도구는 `TreeMap` 감각이 잘 맞는다. 이때 핵심은 prefix tree가 아니라 정렬된 key 공간이다.

## 더 깊이 가려면

- exact lookup과 prefix search를 먼저 자르려면 [Trie vs HashMap: exact lookup이냐 prefix search냐](./trie-vs-hashmap-exact-lookup-beginner-card.md)
- ordered map의 `floor/ceiling/lower/higher`를 손에 붙이려면 [TreeMap Neighbor-Query Micro Drill](./treemap-neighbor-query-micro-drill.md)
- `Trie`의 autocomplete와 메모리 trade-off를 더 보려면 [Trie Prefix Search / Autocomplete](./trie-prefix-search-autocomplete.md)
- Java `TreeMap` range view를 코드 기준으로 이어 보려면 [`subMap()` / `headMap()` / `tailMap()` Live View Primer](../language/java/treemap-range-view-live-window-primer.md)

## 면접/시니어 질문 미리보기

1. 왜 문자열 key라고 바로 `Trie`를 고르면 안 되나요?
   문자열이라는 사실보다 반복 질문이 exact lookup, prefix, neighbor, range 중 무엇인지가 더 중요하기 때문이다.
2. `TreeMap`과 `Trie`를 같이 쓰는 경우도 있나요?
   있다. prefix 후보 수집은 `Trie`, 운영용 정렬 조회나 범위 스캔은 `TreeMap`으로 나누기도 한다.
3. `TreeMap`으로 prefix range를 다룰 수 있는데도 `Trie`를 배우는 이유는 무엇인가요?
   자동완성처럼 prefix가 중심인 문제를 구조 자체로 표현하는 감각을 얻기 위해서다.

## 한 줄 정리

문자열 key에서 `Trie`와 `TreeMap`이 헷갈리면 `startsWith 후보 묶음`은 `Trie`, `사전순 다음/이전 key와 범위`는 `TreeMap`이라고 먼저 자르면 된다.
