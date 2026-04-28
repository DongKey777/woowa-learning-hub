# LinkedHashMap access-order와 캐시 동작 브리지

> 한 줄 요약: `LinkedHashMap`의 `accessOrder=true`는 "순서를 예쁘게 바꾸는 옵션"이 아니라, 조회할 때도 항목을 뒤로 보내서 다음 제거 대상까지 바꾸는 옵션이라서 캐시 동작이 달라진다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Map 구현체별 반복 순서 치트시트](./hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md)
- [Map 구현체 선택 미니 드릴](./map-implementation-selection-mini-drill.md)
- [HashMap vs LinkedHashMap vs TreeMap Key Contract Bridge](./hashmap-vs-linkedhashmap-vs-treemap-key-contract-bridge.md)
- [LinkedHashMap access-order 미니 프라이머](../../data-structure/linkedhashmap-access-order-mini-primer.md)
- [LRU 캐시 설계 입문 (LRU Cache Basics)](../../data-structure/lru-cache-basics.md)

retrieval-anchor-keywords: linkedhashmap access order cache behavior, linkedhashmap accessorder true 왜 캐시가 바뀌지, linkedhashmap insertion order vs access order cache, linkedhashmap get changes eviction order, linkedhashmap removeeldestentry beginner, linkedhashmap lru basics java, linkedhashmap 최근 접근 순서 왜, linkedhashmap 처음 accessorder 헷갈림, linkedhashmap cache 뭐예요, linkedhashmap why access order changes cache, java linkedhashmap basics, linkedhashmap get 하면 순서 바뀜

## 핵심 개념

이미 "`LinkedHashMap`은 넣은 순서를 기억한다"까지는 이해했는데 캐시 예제로 넘어가면 갑자기 막히는 이유는, `accessOrder=true`가 **읽기(`get`)를 순서 변경 이벤트로 바꾸기 때문**이다.

- 기본 모드: "누가 먼저 들어왔나"를 기억한다
- `accessOrder=true`: "누가 가장 최근에 다시 만져졌나"를 기억한다

캐시는 보통 맨 앞의 오래된 항목을 지우므로, 조회가 순서를 바꾸는 순간 **다음에 쫓겨날 후보도 바뀐다**. 이게 beginner가 놓치기 쉬운 핵심이다.

## 한눈에 보기

| 질문 | 삽입 순서 모드 | `accessOrder=true` |
|---|---|---|
| `get("A")`를 하면? | 순서 그대로 | `A`가 뒤로 이동 |
| "가장 오래된 항목" 의미 | 가장 먼저 넣은 항목 | 가장 오래 안 만진 항목 |
| 캐시 제거 대상 | 오래전에 넣은 것 | 오래전에 접근한 것 |
| 어울리는 상황 | 등록 순서 유지 | 작은 LRU 스타일 캐시 |

용량 2짜리 예제를 머릿속에서만 따라가 보자.

| 단계 | 삽입 순서 모드 | `accessOrder=true` |
|---|---|---|
| `put(A), put(B)` | `[A, B]` | `[A, B]` |
| `get(A)` | `[A, B]` | `[B, A]` |
| `put(C)` 후 eldest 제거 | `A` 제거 -> `[B, C]` | `B` 제거 -> `[A, C]` |

같은 `get(A)` 한 번이 제거 대상을 `A`에서 `B`로 바꿨다. 캐시 동작이 달라졌다고 읽는 이유가 여기 있다.

## 왜 캐시 동작이 바뀌나

초보자용으로는 `LinkedHashMap`을 "줄 서 있는 카드"처럼 보면 된다.

- 앞쪽: 가장 오래된 후보
- 뒤쪽: 가장 최근에 만진 후보

삽입 순서 모드에서는 `get()`이 카드를 움직이지 않는다. 그래서 앞에 있는 카드가 계속 제거 후보다.

반대로 `accessOrder=true`에서는 `get()`이 카드를 맨 뒤로 보낸다. 그러면 방금 읽은 항목은 보호되고, 그 대신 더 오래 안 만진 항목이 앞쪽에 남는다.

즉 `removeEldestEntry()`는 똑같이 "맨 앞 카드"를 제거하지만, **누가 맨 앞에 남는지**가 달라지므로 캐시 정책도 달라진다.

## 흔한 오해와 함정

- "`accessOrder=true`는 출력 순서만 예쁘게 바꾸는 옵션 아닌가요?"
  아니다. 캐시라면 출력보다 제거 후보가 바뀌는 쪽이 더 중요하다.
- "`get()`은 읽기인데 왜 부작용처럼 보이죠?"
  접근 순서 모드에서는 "읽었다" 자체가 최신 사용 기록이다.
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

이 코드는 "조회한 `A`를 살리고, 더 오래 안 만진 `B`를 내보낸다"로 읽으면 된다.

만약 세 번째 인자를 빼면 같은 코드도 "먼저 들어온 `A`를 내보낸다" 쪽으로 읽혀서 캐시 의미가 깨진다. 그래서 tiny LRU 예제를 읽을 때는 `removeEldestEntry()`보다 먼저 `true` 인자를 확인하는 습관이 안전하다.

## 더 깊이 가려면

- `LinkedHashMap`의 삽입 순서와 접근 순서 차이를 더 넓게 보려면 [LinkedHashMap access-order 미니 프라이머](../../data-structure/linkedhashmap-access-order-mini-primer.md)
- `HashMap`/`LinkedHashMap`/`TreeMap` 순서 차이를 한 장으로 다시 보려면 [Map 구현체별 반복 순서 치트시트](./hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md)
- 아주 작은 LRU에서 왜 `hash map + linked list` 조합이 나오는지 보려면 [LRU 캐시 설계 입문 (LRU Cache Basics)](../../data-structure/lru-cache-basics.md)
- key 조회 규칙까지 같이 정리하려면 [HashMap vs LinkedHashMap vs TreeMap Key Contract Bridge](./hashmap-vs-linkedhashmap-vs-treemap-key-contract-bridge.md)

## 한 줄 정리

`LinkedHashMap`의 `accessOrder=true`는 "읽은 항목을 뒤로 보내는 규칙"이라서, 캐시에서 다음 제거 대상 자체를 바꾸는 옵션으로 이해해야 한다.
