---
schema_version: 3
title: Map 순서 이상 증상 라우터 카드
concept_id: data-structure/map-order-symptom-router-card
canonical: false
category: data-structure
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 80
mission_ids: []
review_feedback_tags:
- map-iteration-order-contract
- linkedhashmap-access-order
- treemap-sorted-order-assumption
aliases:
- map order changed unexpectedly
- hashmap order not guaranteed
- linkedhashmap access order changed
- treemap sorted iteration order
- map 출력 순서가 바뀜
- 해시맵 순서가 이상함
- 조회만 했는데 뒤로 감
- linkedhashmap accessOrder
symptoms:
- 실행할 때마다 Map 출력 순서가 기대와 다르게 나온다
- 조회만 했는데 LinkedHashMap 항목이 뒤로 밀린다
- 넣은 순서로 보여야 하는데 key 정렬처럼 보인다
- HashMap이 우연히 일정해 보여서 순서 보장으로 착각한다
intents:
- symptom
- troubleshooting
prerequisites:
- data-structure/map-vs-set-requirement-bridge
- data-structure/hashmap-treemap-linkedhashmap-beginner-selection-primer
next_docs:
- data-structure/linkedhashmap-access-order-mini-primer
- data-structure/treemap-vs-hashmap-vs-linkedhashmap
linked_paths:
- contents/data-structure/hashmap-treemap-linkedhashmap-beginner-selection-primer.md
- contents/data-structure/linkedhashmap-access-order-mini-primer.md
- contents/data-structure/treemap-vs-hashmap-vs-linkedhashmap.md
- contents/language/java/hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md
- contents/language/java/navigablemap-navigableset-mental-model.md
confusable_with:
- data-structure/hashmap-treemap-linkedhashmap-beginner-selection-primer
- data-structure/treemap-vs-hashmap-vs-linkedhashmap
- data-structure/linkedhashmap-access-order-mini-primer
forbidden_neighbors:
expected_queries:
- HashMap인데 왜 실행할 때마다 출력 순서가 달라지는지 먼저 진단하고 싶어
- 조회만 했는데 LinkedHashMap 마지막으로 밀리는 현상을 어디서부터 봐야 해?
- 넣은 순서로 보여야 하는데 abc 순으로 나오는 Map 문제를 빠르게 분기해줘
- 순서 계약이 없는 Map과 access-order Map을 증상 기준으로 구분하고 싶어
- 해시맵이 가끔은 순서가 맞아 보여서 더 헷갈릴 때 어떤 문서를 먼저 봐야 해?
- TreeMap 정렬 순서와 LinkedHashMap 삽입 순서를 증상 관점에서 나눠 설명해줘
contextual_chunk_prefix: |
  이 문서는 Map 순회 결과가 흔들려서 순서 버그처럼 보일 때 어떤
  구현체의 계약을 잘못 기대했는지 먼저 가르게 돕는 symptom_router다.
  실행마다 줄 순서가 달라짐, 조회 뒤 맨 끝으로 밀림, 넣은 순서가
  아니라 정렬처럼 보임, 우연한 HashMap 순서를 믿음, access-order가
  섞여 보임, 출력 순서 규칙을 어디서부터 확인하나 같은 자연어
  paraphrase가 본 문서의 원인 분기에 매핑된다.
---
# Map order symptom router card

> 한 줄 요약: `왜 출력 순서가 바뀌지?`라는 증상은 먼저 `순서를 아예 보장하지 않는 HashMap`, `삽입 순서를 기억하는 LinkedHashMap`, `key 정렬 순서로 읽는 TreeMap` 셋 중 무엇을 쓰는지부터 자르면 대부분 빨리 풀린다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md)
- [LinkedHashMap access-order 미니 프라이머](./linkedhashmap-access-order-mini-primer.md)
- [TreeMap, HashMap, LinkedHashMap 비교](./treemap-vs-hashmap-vs-linkedhashmap.md)
- [Map 구현체별 반복 순서 치트시트](../language/java/hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md)
- [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)

retrieval-anchor-keywords: map order symptom router, why did map order change, why output order changed hashmap, hashmap order not guaranteed beginner, linkedhashmap insertion order beginner, linkedhashmap access order symptom, treemap sorted key order beginner, map 출력 순서 왜 바뀌지, 해시맵 순서 이상함, 링크드해시맵 조회만 했는데 순서 변경, 트리맵 정렬 순서, put 했는데 왜 뒤로 가요

## 먼저 잡는 한 문장

이 증상은 복잡하게 보이지만, 입문자는 먼저 이렇게만 잘라 보면 된다.

- `HashMap`이면: 원래 순서를 믿으면 안 된다
- `LinkedHashMap`이면: 기본은 삽입 순서지만 `accessOrder=true`면 조회 후에도 순서가 바뀔 수 있다
- `TreeMap`이면: 이상한 것이 아니라 key 정렬 순서로 읽히는 중일 수 있다

즉 "왜 바뀌었지?"보다 먼저 "지금 이 map이 어떤 순서 규칙을 약속하나?"를 묻는 편이 빠르다.

## 10초 증상 라우터

| 지금 보이는 장면 | 먼저 의심할 구현체/원인 | 첫 확인 |
|---|---|---|
| 실행할 때마다 출력 순서가 기대와 다르다 | `HashMap` | 순서 보장 요구인데 `HashMap`을 쓴 것은 아닌지 |
| 넣은 순서로 보여야 하는데 조회 후 뒤로 밀린다 | `LinkedHashMap(accessOrder=true)` | 생성자 세 번째 인자가 `true`인지 |
| `a, b, c`가 아니라 key 오름차순으로 나온다 | `TreeMap` | key 정렬이 요구인지, 단순 삽입 순서를 원한 것은 아닌지 |
| 기존 key 값만 바꿨는데 순회 순서가 달라진다 | `LinkedHashMap(accessOrder=true)` | 기존 key `put()`도 재접근처럼 취급되는지 |

짧게 외우면 아래 한 줄이면 된다.

- `순서 계약 없음` -> `HashMap`
- `넣은 순서 유지` -> 기본 `LinkedHashMap`
- `조회 후 최근 접근 순서로 이동` -> `LinkedHashMap(accessOrder=true)`
- `정렬 순서` -> `TreeMap`

## 같은 데이터로 보면 더 쉽다

같은 key `banana`, `apple`, `carrot`를 넣어도 읽는 규칙이 다르다.

| 구현체 | 보이는 순서 | beginner 해석 |
|---|---|---|
| `HashMap` | 예측하지 않음 | 우연히 일정해 보여도 규칙으로 믿지 않는다 |
| `LinkedHashMap` | `banana, apple, carrot` | 넣은 순서 그대로 읽는다 |
| `TreeMap` | `apple, banana, carrot` | key 기준 정렬 순서로 읽는다 |

여기서 많이 생기는 오해는 "지금 출력된 모습"을 곧바로 비즈니스 규칙으로 받아들이는 것이다.
하지만 `HashMap`은 순서 자체가 계약이 아니고, `TreeMap`은 삽입 순서가 아니라 정렬 규칙을 보여 준다.

## 가장 자주 틀리는 두 장면

### 1. `HashMap`인데도 순서가 그럴듯해 보이는 장면

초보자는 `HashMap`이 몇 번 실행해도 비슷하게 찍히면 "이 순서가 유지되나 보다"라고 생각하기 쉽다.
하지만 그건 구현 세부가 우연히 그렇게 보이는 것뿐이다.

그래서 요구사항이 `출력 순서도 기능`이라면 `HashMap`에 기대지 말고 의도를 드러내야 한다.

- 등록한 순서가 중요하다 -> `LinkedHashMap`
- key 정렬이 중요하다 -> `TreeMap`

### 2. `LinkedHashMap`인데 조회만 했더니 뒤로 가는 장면

이 장면은 거의 항상 `accessOrder=true`와 연결된다.
기본 `LinkedHashMap`은 조회만으로 순서를 바꾸지 않지만, 접근 순서 모드는 `get()`이나 기존 key `put()`도 "최근에 만졌다"고 본다.

그래서 "화면은 등록 순서 그대로여야 하는데 최근에 본 항목이 자꾸 뒤로 간다"면 기능 요구와 구현체 모드가 어긋난 경우가 많다.

## `get()`만 했는데 왜 순서가 바뀌나

이 증상은 말로만 보면 잘 안 잡힌다. 아래처럼 `accessOrder=true`를 켠 `LinkedHashMap`이면 조회만으로도 최근 접근 항목이 뒤로 이동한다.

```java
Map<String, Integer> recentOrder = new LinkedHashMap<>(16, 0.75f, true);
recentOrder.put("apple", 1);
recentOrder.put("banana", 2);
recentOrder.put("carrot", 3);

recentOrder.get("apple");
System.out.println(recentOrder.keySet()); // [banana, carrot, apple]
```

이 장면에서 중요한 해석은 둘뿐이다.

- 등록 순서를 기대했다면 `accessOrder=true`가 요구와 어긋난다.
- 최근 조회 항목이 뒤로 가야 하는 LRU류 요구라면 오히려 의도대로 동작한 것이다.

그래서 "`조회만 했는데 순서가 섞여요`"라는 질문은 버그처럼 보이더라도, 먼저 `LinkedHashMap` 생성자 세 번째 인자가 `true`인지부터 확인하는 편이 가장 빠르다.

## 빠른 선택 규칙

| 내가 진짜 원하는 것 | 첫 선택 |
|---|---|
| key로 값만 찾으면 된다 | `HashMap` |
| 사용자가 넣은 순서 그대로 보여 준다 | 기본 `LinkedHashMap` |
| 최근에 본 항목이 뒤로 가야 한다 | `LinkedHashMap(accessOrder=true)` |
| key 기준 다음 값, 범위, 정렬 순회가 필요하다 | `TreeMap` |

한 번만 정렬해서 출력하면 되는 경우는 `HashMap`에 담고 마지막에 따로 정렬해도 된다.
반대로 조회 중간중간 계속 순서 규칙을 써야 하면 구현체가 그 규칙을 직접 표현하는 편이 안전하다.

## 증상에서 요구로 다시 번역하기

증상 문장을 요구사항으로 바꾸면 구현체 선택이 훨씬 쉬워진다.

| 학습자 질문 | 실제 요구 | 먼저 확인할 것 |
|---|---|---|
| `왜 실행할 때마다 순서가 달라요?` | 안정된 순서 출력 | `HashMap`을 순서 있는 컬렉션처럼 쓰고 있지 않은지 |
| `조회만 했는데 마지막으로 밀려요` | 최근 접근 순서 | `LinkedHashMap(accessOrder=true)`인지 |
| `넣은 순서가 아니라 abc 순으로 나와요` | key 정렬 순회 | `TreeMap` 또는 정렬된 view를 기대한 것인지 |
| `한 번만 정렬해서 보여주면 되는데 뭘 써야 해요?` | 저장과 출력 요구 분리 | 보관은 `HashMap`, 출력 직전에만 정렬해도 되는지 |

핵심은 "현재 보이는 순서"를 그대로 믿지 말고, "내가 진짜 필요한 순서 계약이 무엇인가"를 먼저 말로 고정하는 것이다.

## 다음으로 어디를 읽을까

- `LinkedHashMap`의 삽입 순서와 access-order를 예제로 더 짧게 보고 싶으면 [LinkedHashMap access-order 미니 프라이머](./linkedhashmap-access-order-mini-primer.md)
- 셋 중 무엇을 고를지 처음부터 다시 묶어 보고 싶으면 [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md)
- `TreeMap`에서 `floorKey`, `ceilingKey`, `subMap`이 왜 나오는지까지 이어 가려면 [NavigableMap and NavigableSet Mental Model](../language/java/navigablemap-navigableset-mental-model.md)
- Java 출력 예제로 순서 차이를 한 장에 복습하려면 [Map 구현체별 반복 순서 치트시트](../language/java/hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md)

## 한 줄 정리

`왜 출력 순서가 바뀌지?`라는 증상은 `HashMap이라서 순서 계약이 없나`, `LinkedHashMap access-order가 켜졌나`, `TreeMap이라서 정렬 순서로 읽히나`를 먼저 자르면 대부분 바로 방향이 잡힌다.
