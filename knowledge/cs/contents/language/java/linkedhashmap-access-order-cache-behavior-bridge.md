---
schema_version: 3
title: LinkedHashMap Access-Order Cache Behavior Bridge
concept_id: language/linkedhashmap-access-order-cache-behavior-bridge
canonical: true
category: language
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 93
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- linkedhashmap
- lru-cache
- map-order
aliases:
- LinkedHashMap access-order cache bridge
- LinkedHashMap LRU eviction beginner
- accessOrder true removeEldestEntry
- get changes eviction order LinkedHashMap
- 조회만 했는데 캐시 순서가 바뀜
- 왜 캐시에서 B가 지워지지
symptoms:
- LinkedHashMap accessOrder=true에서 get 호출이 최근 접근으로 기록되어 eviction 후보를 바꾼다는 점을 놓쳐
- removeEldestEntry만 override하면 LRU가 된다고 생각하고 accessOrder=true 설정을 확인하지 않아 insertion-order eviction을 만든다
- 캐시에서 제거된 key를 보고 순서 버그라고 판단하지만 실제로는 get 이후 eldest가 바뀐 LRU 동작임을 설명하지 못해
intents:
- definition
- troubleshooting
- drill
prerequisites:
- data-structure/linkedhashmap-access-order-mini-primer
- data-structure/lru-cache-basics
- language/hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet
next_docs:
- language/linkedhashmap-get-put-existing-key-access-order-mini-drill
- language/linkedhashmap-access-order-vs-treemap-navigable-mini-drill
- data-structure/lru-cache-basics
linked_paths:
- contents/data-structure/linkedhashmap-access-order-mini-primer.md
- contents/data-structure/lru-cache-basics.md
- contents/language/java/hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md
- contents/language/java/map-implementation-selection-mini-drill.md
- contents/language/java/hashmap-vs-linkedhashmap-vs-treemap-key-contract-bridge.md
- contents/language/java/linkedhashmap-get-put-existing-key-access-order-mini-drill.md
- contents/language/java/linkedhashmap-access-order-vs-treemap-navigable-mini-drill.md
confusable_with:
- data-structure/linkedhashmap-access-order-mini-primer
- data-structure/lru-cache-basics
- language/hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet
forbidden_neighbors: []
expected_queries:
- LinkedHashMap accessOrder=true에서 get을 했는데 왜 eviction 대상이 바뀌어?
- removeEldestEntry와 accessOrder=true를 같이 써야 LRU처럼 동작하는 이유를 설명해줘
- LinkedHashMap으로 용량 2 LRU 캐시를 만들 때 A를 get하면 왜 B가 지워져?
- insertion-order와 access-order는 캐시 제거 후보를 어떻게 다르게 정해?
- LinkedHashMap 캐시에서 조회만 했는데 순서가 바뀌는 현상을 beginner 예제로 보여줘
contextual_chunk_prefix: |
  이 문서는 LinkedHashMap accessOrder=true가 get/put을 최근 접근으로 기록하고 removeEldestEntry eviction 후보를 LRU처럼 바꾸는 흐름을 설명하는 beginner bridge다.
  LinkedHashMap access-order, LRU cache, removeEldestEntry, get changes order, eviction target 질문이 본 문서에 매핑된다.
---
# LinkedHashMap access-order에서 cache/LRU로 넘어가는 브리지

> 한 줄 요약: `LinkedHashMap`의 access-order 자체는 자료구조 프라이머에서 먼저 잡고, 이 문서는 그 다음 단계인 "`get()` 한 번 했는데 왜 캐시에서 `B`가 지워지지?" 같은 eviction 증상을 LRU 관점으로 번역하는 데 집중한다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [LinkedHashMap access-order 미니 프라이머](../../data-structure/linkedhashmap-access-order-mini-primer.md)
- [LRU 캐시 설계 입문 (LRU Cache Basics)](../../data-structure/lru-cache-basics.md)
- [Map 구현체별 반복 순서 치트시트](./hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md)
- [Map 구현체 선택 미니 드릴](./map-implementation-selection-mini-drill.md)
- [HashMap vs LinkedHashMap vs TreeMap Key Contract Bridge](./hashmap-vs-linkedhashmap-vs-treemap-key-contract-bridge.md)

retrieval-anchor-keywords: linkedhashmap cache bridge, linkedhashmap lru eviction beginner, linkedhashmap get changes eviction order, linkedhashmap removeeldestentry beginner, linkedhashmap accessorder true cache symptom, linkedhashmap 조회만 했는데 순서가 바뀐다, 왜 캐시에서 b가 지워지지, linkedhashmap eviction target changed after get, linkedhashmap tiny lru example, linkedhashmap cache 뭐예요, linkedhashmap why access order changes cache, linkedhashmap removeeldestentry accessorder true, linkedhashmap cache eviction symptom, linkedhashmap lru bridge, linkedhashmap beginner cache

## 핵심 개념

이 문서는 `LinkedHashMap` 자체를 처음 소개하는 프라이머가 아니다.
이미 "기본은 삽입 순서, `accessOrder=true`면 접근 순서"까지는 본 상태라고 가정하고, 그다음에 자주 나오는 cache/LRU 증상을 풀어 주는 브리지다.

캐시 예제에서 갑자기 막히는 이유는 `accessOrder=true`가 **읽기(`get`)를 순서 변경 이벤트로 바꾸기 때문**이다.

- 기본 모드: "누가 먼저 들어왔나"를 기억한다
- `accessOrder=true`: "누가 가장 최근에 다시 만져졌나"를 기억한다

캐시는 보통 맨 앞의 오래된 항목을 지우므로, 조회가 순서를 바꾸는 순간 **다음에 쫓겨날 후보도 바뀐다**. 이게 beginner가 놓치기 쉬운 핵심이다.

초보자용으로는 아래 한 문장까지 붙이면 거의 끝난다.

> insertion-order는 "먼저 들어온 순서", access-order는 "마지막으로 만진 순서"를 기억한다.

## 이 문서가 맡는 질문

duplicate retrieval을 줄이려면 프라이머와 브리지가 받는 질문이 달라야 한다.
이 문서는 아래 오른쪽 열 질문을 맡는다.

| 지금 학습자가 묻는 것 | 먼저 볼 문서 | 왜 그 문서가 맞나 |
|---|---|---|
| "`LinkedHashMap` 기본 순서가 뭐예요?", "`get()`도 순서를 바꾸나요?" | [LinkedHashMap access-order 미니 프라이머](../../data-structure/linkedhashmap-access-order-mini-primer.md) | access-order 규칙 자체를 먼저 고정해야 한다 |
| "기존 key를 다시 `put()`하면 뒤로 가나요?" | [LinkedHashMap access-order 미니 프라이머](../../data-structure/linkedhashmap-access-order-mini-primer.md) | 캐시보다 순서 규칙 차이를 먼저 이해해야 한다 |
| "`get(A)` 한 번 했는데 왜 캐시에서 `B`가 지워지지?" | 이 문서 | eviction 대상을 LRU 관점으로 읽는 질문이다 |
| "`removeEldestEntry()`를 붙였는데 왜 가장 먼저 넣은 게 아니라 다른 게 지워지지?" | 이 문서 | access-order와 eviction이 같이 작동하는 장면이다 |

즉 프라이머는 "`LinkedHashMap`의 순서 규칙"을 맡고, 이 브리지는 "`그 규칙이 cache eviction으로 어떻게 번역되나`"를 맡는다.

## 한눈에 보기

| 질문 | 삽입 순서 모드 | `accessOrder=true` |
|---|---|---|
| `get("A")`를 하면? | 순서 그대로 | `A`가 뒤로 이동 |
| "가장 오래된 항목" 의미 | 가장 먼저 넣은 항목 | 가장 오래 안 만진 항목 |
| 캐시 제거 대상 | 오래전에 넣은 것 | 오래전에 접근한 것 |
| 이 문서에서 바로 보는 장면 | 단순 순서 복습 | 작은 LRU 스타일 캐시 |

용량 2짜리 예제를 머릿속에서만 따라가 보자.

| 단계 | 삽입 순서 모드 | `accessOrder=true` |
|---|---|---|
| `put(A), put(B)` | `[A, B]` | `[A, B]` |
| `get(A)` | `[A, B]` | `[B, A]` |
| `put(C)` 후 eldest 제거 | `A` 제거 -> `[B, C]` | `B` 제거 -> `[A, C]` |

같은 `get(A)` 한 번이 제거 대상을 `A`에서 `B`로 바꿨다. 캐시 동작이 달라졌다고 읽는 이유가 여기 있다.

## 삽입 순서 이해에서 캐시 이해로 건너가는 3문장

입문자가 자주 멈추는 지점은 "`get()`은 읽기인데 왜 캐시 결과가 바뀌죠?"라는 질문이다. 이때는 아래 3문장으로 연결하면 된다.

1. `removeEldestEntry()`는 여전히 "맨 앞 항목"을 제거한다.
2. 그런데 `accessOrder=true`에서는 `get()`이 방금 읽은 항목을 맨 뒤로 보낸다.
3. 그래서 "맨 앞에 남는 항목"이 달라지고, 결국 제거 대상도 달라진다.

즉 캐시 정책이 새로 생긴 것이 아니라, **eldest를 정하는 기준이 insertion-order에서 last-access-order로 바뀐 것**이다.

## 증상 질문을 그대로 번역하면

입문자 질문 두 개를 나란히 놓으면 연결이 더 직접적으로 보인다.

| 학습자 질문 | 내부에서 벌어진 일 | 바로 떠올릴 체크포인트 |
|---|---|---|
| "조회만 했는데 순서가 바뀐다" | `get("A")`가 `A`를 맨 뒤로 보냈다 | `LinkedHashMap(..., true)`인지 |
| "왜 캐시에서 `B`가 지워지지" | `A`를 읽은 뒤 eldest가 `B`로 바뀌었다 | `removeEldestEntry()` 직전 순서가 `[B, A]`인지 |

즉 첫 질문은 "순서 버그"가 아니라 eviction 원인을 설명하는 첫 단서다. `get()` 이후 순서를 먼저 말로 적어 보면 제거 대상도 같이 풀린다.

## 왜 캐시 동작이 바뀌나

초보자용으로는 `LinkedHashMap`을 "줄 서 있는 카드"처럼 보면 된다.

- 앞쪽: 가장 오래된 후보
- 뒤쪽: 가장 최근에 만진 후보

삽입 순서 모드에서는 `get()`이 카드를 움직이지 않는다. 그래서 앞에 있는 카드가 계속 제거 후보다.

반대로 `accessOrder=true`에서는 `get()`이 카드를 맨 뒤로 보낸다. 그러면 방금 읽은 항목은 보호되고, 그 대신 더 오래 안 만진 항목이 앞쪽에 남는다.

즉 `removeEldestEntry()`는 똑같이 "맨 앞 카드"를 제거하지만, **누가 맨 앞에 남는지**가 달라지므로 캐시 정책도 달라진다.

이 시점부터는 "`removeEldestEntry()`가 특별한 캐시 마법을 한다"보다 "`accessOrder=true`가 줄 세우는 기준을 바꾼다"에 초점을 두는 편이 안전하다.

## 흔한 오해와 함정

- "`accessOrder=true`는 출력 순서만 예쁘게 바꾸는 옵션 아닌가요?"
  아니다. 캐시라면 출력보다 제거 후보가 바뀌는 쪽이 더 중요하다.
- "`get()`은 읽기인데 왜 부작용처럼 보이죠?"
  접근 순서 모드에서는 "읽었다" 자체가 최신 사용 기록이다.
- "`removeEldestEntry()`만 override하면 LRU가 되나요?"
  `accessOrder=true`가 빠지면 "최근에 사용한 것"이 아니라 "먼저 들어온 것"이 제거된다. 둘은 다르다.
- "기존 key에 `put()`만 했는데 왜 eviction 결과가 달라지죠?"
  접근 순서 모드에서는 갱신도 최근 접근으로 취급될 수 있어서 제거 후보가 밀린다.
- "그럼 `LinkedHashMap`만으로 캐시가 끝나나요?"
  아니다. 여기서는 순서 규칙만 잡는다. 동시성, TTL, 용량 정책은 다음 문서 범위다.

## 실무에서 쓰는 모습

```java
Map<String, String> cache = new LinkedHashMap<>(16, 0.75f, true) {
    @Override
    protected boolean removeEldestEntry(Map.Entry<String, String> eldest) {
        return size() > 2;
    }
};

cache.put("A", "apple");
cache.put("B", "banana");
cache.get("A");            // [B, A]
cache.put("C", "carrot");  // B 제거
```

이 코드는 아래 순서로 읽으면 된다.

- `put(A), put(B)`까지는 단순 삽입 순서다.
- `get(A)`에서 `A`가 뒤로 가므로 이제 eldest는 `B`다.
- `put(C)`로 크기가 3이 되는 순간 맨 앞의 `B`가 제거된다.

즉 "조회한 `A`를 살리고, 더 오래 안 만진 `B`를 내보낸다"로 읽으면 된다.

질문을 바꾸면 더 명확해진다.

- "왜 `B`가 지워지지?" -> `B`가 가장 오래 안 만진 항목이어서
- "왜 가장 오래 안 만진 항목이 `B`지?" -> 방금 `get(A)`를 해서 `A`를 보호했기 때문에
- "왜 `get(A)`가 보호로 취급되지?" -> `accessOrder=true`가 읽기를 최근 접근으로 기록하기 때문에

만약 세 번째 인자를 빼면 같은 코드도 "먼저 들어온 `A`를 내보낸다" 쪽으로 읽혀서 캐시 의미가 깨진다. 그래서 tiny LRU 예제를 읽을 때는 `removeEldestEntry()`보다 먼저 `true` 인자를 확인하는 습관이 안전하다.

## 더 깊이 가려면

- `LinkedHashMap`의 삽입 순서와 접근 순서 차이를 처음부터 다시 잡으려면 [LinkedHashMap access-order 미니 프라이머](../../data-structure/linkedhashmap-access-order-mini-primer.md)
- `HashMap`/`LinkedHashMap`/`TreeMap` 순서 차이를 한 장으로 다시 보려면 [Map 구현체별 반복 순서 치트시트](./hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md)
- 아주 작은 LRU에서 왜 `hash map + linked list` 조합이 나오는지 보려면 [LRU 캐시 설계 입문 (LRU Cache Basics)](../../data-structure/lru-cache-basics.md)
- key 조회 규칙까지 같이 정리하려면 [HashMap vs LinkedHashMap vs TreeMap Key Contract Bridge](./hashmap-vs-linkedhashmap-vs-treemap-key-contract-bridge.md)

## 한 줄 정리

`LinkedHashMap` access-order의 의미 자체는 프라이머에서 먼저 잡고, 이 문서에서는 그 규칙이 cache/LRU에서 "다음에 누가 지워지나"로 번역된다고 이해하면 된다.
