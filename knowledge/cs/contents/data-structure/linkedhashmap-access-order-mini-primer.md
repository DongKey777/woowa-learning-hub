---
schema_version: 3
title: LinkedHashMap access-order 미니 프라이머
concept_id: data-structure/linkedhashmap-access-order-mini-primer
canonical: false
category: data-structure
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 87
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- linkedhashmap-access-order
- map-iteration-order
- lru-beginner
aliases:
- LinkedHashMap access order
- insertion order vs access order
- accessOrder true
- LinkedHashMap LRU mini example
- get changes order LinkedHashMap
- same key reinsert order
- 최근 접근 순서 map
symptoms:
- LinkedHashMap이 항상 insertion order만 유지한다고 생각해 accessOrder=true에서 get이나 existing put이 순서를 바꾸는 동작을 놓친다
- LRU 예제에서 오래 안 쓴 항목이 앞에 오고 최근 접근 항목이 뒤로 가는 access-order 모델을 이해하지 못한다
- HashMap LinkedHashMap TreeMap의 iteration order 차이와 cache eviction 예제를 섞어 본다
intents:
- definition
- comparison
prerequisites:
- data-structure/hashmap-treemap-linkedhashmap-beginner-selection-primer
next_docs:
- data-structure/lru-cache-basics
- data-structure/lru-cache-design
- language/hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet
linked_paths:
- contents/data-structure/hashmap-treemap-linkedhashmap-beginner-selection-primer.md
- contents/data-structure/lru-cache-basics.md
- contents/data-structure/lru-cache-design.md
- contents/language/java/hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md
confusable_with:
- data-structure/hashmap-treemap-linkedhashmap-beginner-selection-primer
- data-structure/lru-cache-basics
- data-structure/lru-cache-design
- language/hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet
forbidden_neighbors: []
expected_queries:
- LinkedHashMap은 insertion order와 access order가 어떻게 달라?
- accessOrder=true를 켜면 get이나 기존 key put이 순서를 바꾸는 이유는?
- LinkedHashMap으로 작은 LRU cache 예제를 읽을 때 무엇을 봐야 해?
- 읽기만 했는데 map iteration order가 바뀌면 어떤 모드야?
- HashMap LinkedHashMap TreeMap 반복 순서 차이를 beginner 기준으로 알려줘
contextual_chunk_prefix: |
  이 문서는 LinkedHashMap의 기본 insertion-order 모드와 accessOrder=true의
  access-order 모드를 구분하는 beginner primer다. get, existing put, same key
  update가 순서를 바꾸는지와 LRU cache 예제에서 오래 안 쓴 항목을 찾는
  감각을 설명한다.
---
# LinkedHashMap access-order 미니 프라이머

> 한 줄 요약: `LinkedHashMap`은 기본이 삽입 순서 map이지만, `accessOrder=true`를 켜면 "최근에 만진 항목이 뒤로 가는" 접근 순서 map으로 바뀌고 이 차이가 아주 작은 LRU 예제를 읽는 핵심이다.

**난이도: 🟢 Beginner**

관련 문서:

- [자료구조 카테고리 인덱스](./README.md)
- [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md)
- [LRU 캐시 설계 입문 (LRU Cache Basics)](./lru-cache-basics.md)
- [LRU Cache Design](./lru-cache-design.md)
- [Map 구현체별 반복 순서 치트시트](../language/java/hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md)

retrieval-anchor-keywords: linkedhashmap access order primer, linkedhashmap insertion order vs access order, linkedhashmap accessorder true beginner, linkedhashmap lru mini example, linkedhashmap get changes order, linkedhashmap put existing key order, linkedhashmap same key reinsert order, linkedhashmap update existing key access order, linkedhashmap 최근 접근 순서, linkedhashmap 삽입 순서 접근 순서 차이, linkedhashmap 같은 키 다시 put, access order map intro, lru 예제 처음, map 순서 헷갈림

## 핵심 개념

`LinkedHashMap`을 처음 배울 때 가장 많이 섞이는 두 문장은 이것이다.

- "넣은 순서를 유지한다"
- "최근에 접근한 것이 뒤로 간다"

둘 다 `LinkedHashMap` 이야기일 수 있지만, **같은 모드가 아니다**.

- 기본값 `accessOrder=false`: 삽입 순서 유지
- 옵션 `accessOrder=true`: 접근 순서 유지

즉 `LinkedHashMap`은 "항상 넣은 순서 map"이 아니라, 생성자 옵션에 따라 **삽입 순서 map** 또는 **접근 순서 map**이 된다.

## 한눈에 보기

| 구분 | 삽입 순서 모드 | 접근 순서 모드 |
|---|---|---|
| 생성 방식 | `new LinkedHashMap<>()` | `new LinkedHashMap<>(16, 0.75f, true)` |
| 순서가 바뀌는 기준 | 새 key를 넣을 때 | `get()` 또는 기존 key를 다시 만질 때 |
| 이런 요구에 맞다 | "등록한 순서 그대로 보여 줘" | "최근에 본 항목이 맨 뒤로 가야 해" |
| 자주 붙는 예시 | 화면 표시 순서 | 아주 작은 LRU 스타일 캐시 |

같은 데이터 `A, B, C`를 넣었다고 하자.

| 연산 | 삽입 순서 모드 | 접근 순서 모드 |
|---|---|---|
| 시작 | `[A, B, C]` | `[A, B, C]` |
| `get(A)` | `[A, B, C]` | `[B, C, A]` |
| `put(B, ...)` | `[A, B, C]` | `[C, A, B]` |

입문자용으로 한 줄만 외우면 이렇다.

- "읽기만 했는데 순서가 바뀌면" 접근 순서 모드다.
- "읽어도 그대로면" 삽입 순서 모드다.
- "기존 key를 다시 `put()`했을 때 뒤로 가면" 접근 순서 모드다.

## 상세 분해

### 1. 삽입 순서는 "처음 들어온 순서"를 기억한다

기본 `LinkedHashMap`은 새 key가 들어온 순서를 유지한다.
그래서 "관리자가 등록한 순서", "사용자가 담은 순서"처럼 **입력 순서 자체가 기능 요구**일 때 잘 맞는다.

중요한 점은 `get()`만으로는 순서가 바뀌지 않는다는 것이다.
즉 조회는 조회일 뿐이고, 화면 순서 계약은 그대로 남는다.

### 2. 접근 순서는 "최근에 만진 순서"를 기억한다

`accessOrder=true`를 켜면 순서 기준이 바뀐다.
이때는 오래전에 넣었어도 방금 `get()` 했다면 최신 항목 쪽으로 이동한다.

이 모드는 "최근에 본 항목을 뒤로 보내기", "오래 안 쓴 항목을 앞에 두기" 같은 요구를 표현할 때 쓴다.
그래서 LRU 예제를 볼 때 핵심은 "누가 먼저 들어왔나"가 아니라 "누가 마지막에 다시 만져졌나"다.

## 같은 key 갱신

기존 key 재삽입처럼 보이는 장면은 access-order를 배울 때 가장 자주 헷갈리는 지점이다.

### 3. 같은 key를 다시 넣을 때도 두 모드가 다르게 보인다

입문자가 특히 헷갈리는 장면은 이것이다.

> "`put()`이면 어차피 삽입 아닌가요? 기존 key를 다시 넣으면 맨 뒤로 가나요?"

짧게 답하면 아래처럼 보면 된다.

| 연산 | 삽입 순서 모드 | 접근 순서 모드 |
|---|---|---|
| 시작 | `[A, B, C]` | `[A, B, C]` |
| `put(B, "new")` | `[A, B, C]` | `[A, C, B]` |

초급 mental model에서는 이렇게 기억하면 충분하다.

- 새 key 추가: 두 모드 모두 맨 뒤에 붙는다
- 기존 key 값 갱신: 삽입 순서 모드는 자리 유지, 접근 순서 모드는 "다시 만졌다"고 보고 뒤로 이동할 수 있다

즉 "같은 key에 새 value를 넣었다"는 사실만으로 기존 항목이 새로 삽입된 것은 아니다.
삽입 순서 모드에서는 **처음 들어온 위치**를 계속 기억하고, 접근 순서 모드만 **최근에 다시 만진 항목**으로 취급한다.

```java
Map<String, Integer> insertionOrder = new LinkedHashMap<>();
insertionOrder.put("A", 1);
insertionOrder.put("B", 2);
insertionOrder.put("C", 3);
insertionOrder.put("B", 20);
// 순서: A, B, C

Map<String, Integer> accessOrder = new LinkedHashMap<>(16, 0.75f, true);
accessOrder.put("A", 1);
accessOrder.put("B", 2);
accessOrder.put("C", 3);
accessOrder.put("B", 20);
// 순서: A, C, B
```

그래서 "값만 갱신했는데 순회 순서가 바뀌었다"면 먼저 `accessOrder=true`인지 확인하는 편이 빠르다.

## tiny LRU 연결

### 4. tiny LRU 예제는 이 차이만 읽으면 된다

아주 작은 용량 2짜리 예제를 보자.

```java
Map<String, String> lru = new LinkedHashMap<>(16, 0.75f, true) {
    @Override
    protected boolean removeEldestEntry(Map.Entry<String, String> eldest) {
        return size() > 2;
    }
};

lru.put("A", "apple");   // [A]
lru.put("B", "banana");  // [A, B]
lru.get("A");            // [B, A]
lru.put("C", "carrot");  // [A, C]  B 제거
```

이 예제에서 읽어야 할 건 두 줄뿐이다.

- `get("A")` 뒤에 순서가 `[B, A]`로 바뀐다
- 다음 삽입에서 가장 앞의 `B`가 제거된다

즉 tiny LRU는 "가장 오래전에 넣은 것 제거"가 아니라 **가장 오래 접근되지 않은 것 제거**다.

## 흔한 오해와 함정

- "`LinkedHashMap`은 원래 항상 삽입 순서 아닌가요?"
  기본은 그렇지만, `accessOrder=true`면 다르다.
- "`get()`은 읽기니까 순서에 영향이 없지 않나요?"
  접근 순서 모드에서는 `get()`도 순서를 바꾼다.
- "기존 key에 `put()`하면 삽입 순서 모드에서도 맨 뒤로 가나요?"
  아니다. 삽입 순서 모드는 자리를 유지하고, 접근 순서 모드에서만 최근 접근처럼 뒤로 갈 수 있다.
- "이걸 보면 LRU 캐시 전체 설계를 안다고 봐도 되나요?"
  아니다. 여기서는 `LinkedHashMap`의 순서 규칙만 잡는다. 동시성, TTL, 분산 캐시 같은 범위는 다음 문서로 넘기는 편이 맞다.

## 실무에서 쓰는 모습

"사용자가 최근에 본 항목 2개만 로컬에서 잠깐 기억하자" 같은 아주 작은 기능이면 `LinkedHashMap(accessOrder=true)` 예제가 잘 읽힌다.
여기서 중요한 건 거대한 캐시 시스템이 아니라, **접근하면 뒤로 이동하고 가장 오래 안 만진 항목이 밀려난다**는 동작이다.

반대로 "등록한 순서를 그대로 보여 줘" 같은 요구라면 access-order가 아니라 기본 `LinkedHashMap`을 써야 한다.
둘을 섞으면 "조회만 했는데 화면 순서가 바뀌는" 버그를 만나기 쉽다.

## 더 깊이 가려면

- `HashMap` / `LinkedHashMap` / `TreeMap` 첫 선택을 다시 묶어 보려면 [HashMap, TreeMap, LinkedHashMap Beginner Selection Primer](./hashmap-treemap-linkedhashmap-beginner-selection-primer.md)
- 반복 순서 차이를 한 장으로 복습하려면 [Map 구현체별 반복 순서 치트시트](../language/java/hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md)
- LRU 자체의 목적과 `hash map + doubly linked list` 조합을 보려면 [LRU 캐시 설계 입문 (LRU Cache Basics)](./lru-cache-basics.md)
- `removeEldestEntry()`와 직접 구현 trade-off까지 보려면 [LRU Cache Design](./lru-cache-design.md)

## 한 줄 정리

`LinkedHashMap`은 기본이 삽입 순서지만 `accessOrder=true`를 켜면 접근 순서 map으로 바뀌고, tiny LRU 예제는 이 차이를 읽을 줄 알면 거의 다 이해된다.
