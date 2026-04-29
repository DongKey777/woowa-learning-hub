# LinkedHashMap `get()` vs 기존 key `put()` access-order 미니 드릴

> 한 줄 요약: 기본 `LinkedHashMap`과 `LinkedHashMap(access-order=true)`를 헷갈릴 때는 `get()`과 "기존 key에 다시 `put()`" 두 장면만 따로 떼어 보면 된다. 기본 모드는 자리 유지, access-order 모드는 최근에 다시 만진 항목이 뒤로 간다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README: Java primer](../README.md#java-primer)
- [LinkedHashMap access-order vs TreeMap navigable API 미니 드릴](./linkedhashmap-access-order-vs-treemap-navigable-mini-drill.md)
- [Map 구현체별 반복 순서 치트시트](./hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md)
- [LinkedHashMap access-order와 캐시 동작 브리지](./linkedhashmap-access-order-cache-behavior-bridge.md)
- [LinkedHashMap access-order 미니 프라이머](../../data-structure/linkedhashmap-access-order-mini-primer.md)

retrieval-anchor-keywords: linkedhashmap get put existing key access order, linkedhashmap get changes order drill, linkedhashmap existing key put order, linkedhashmap insertion order vs access order exact match, linkedhashmap accessorder true beginner, 조회만 했는데 순서가 바뀐다, 기존 key put 하면 왜 뒤로 가요, linkedhashmap 같은 키 다시 put, map 순서 헷갈림 basics, what is linkedhashmap access order, beginner linkedhashmap micro drill, 처음 배우는 linkedhashmap order

## 먼저 고정할 한 문장

이번 드릴은 `LinkedHashMap`의 모든 기능을 다루지 않는다.
딱 아래 두 문장만 손에 붙이면 된다.

- 기본 `LinkedHashMap`: `get()`도, 기존 key `put()`도 순서를 바꾸지 않는다
- `LinkedHashMap(access-order=true)`: `get()`과 기존 key `put()`이 둘 다 "최근에 다시 만짐"으로 기록될 수 있다

짧게 외우면 이렇다.

> 기본 모드는 "처음 들어온 자리"를 기억하고, access-order 모드는 "마지막에 다시 만진 순서"를 기억한다.

여기서 말하는 `put()`은 **새 key 추가가 아니라 이미 있는 key에 다시 넣는 경우**만 뜻한다.
새 key를 넣으면 두 모드 모두 맨 뒤에 붙는다.

## 10초 비교표

시작 순서가 `[A, B, C]`일 때만 보자.

| 장면 | 기본 `LinkedHashMap` | `LinkedHashMap(access-order=true)` |
|---|---|---|
| `get(B)` | `[A, B, C]` | `[A, C, B]` |
| 기존 key에 `put(B, 20)` | `[A, B, C]` | `[A, C, B]` |
| 새 key에 `put(D, 4)` | `[A, B, C, D]` | `[A, B, C, D]` |

이 표에서 beginner가 먼저 볼 포인트는 하나다.

- "`B`가 뒤로 갔다"면 access-order 쪽 신호다
- "`B` 자리가 그대로다"면 기본 삽입 순서 쪽 신호다

즉 `get()`과 기존 key `put()`은 access-order를 판별하는 exact-match 장면이다.

## 드릴 1: `get()`만 했을 때

```java
import java.util.LinkedHashMap;
import java.util.Map;

Map<String, Integer> insertionOrder = new LinkedHashMap<>();
insertionOrder.put("A", 1);
insertionOrder.put("B", 2);
insertionOrder.put("C", 3);
insertionOrder.get("B");

Map<String, Integer> accessOrder = new LinkedHashMap<>(16, 0.75f, true);
accessOrder.put("A", 1);
accessOrder.put("B", 2);
accessOrder.put("C", 3);
accessOrder.get("B");
```

실행 전에 먼저 적어 보자.

| map | 내 답 |
|---|---|
| `insertionOrder.keySet()` |  |
| `accessOrder.keySet()` |  |

정답:

- `insertionOrder.keySet() -> [A, B, C]`
- `accessOrder.keySet() -> [A, C, B]`

읽는 법은 짧다.

- 기본 모드의 `get(B)`는 조회만 했으므로 자리 유지
- access-order의 `get(B)`는 최근 접근으로 기록되므로 `B`가 맨 뒤

그래서 "`get()`만 했는데 순서가 바뀐다"는 로그를 보면, 기본 `LinkedHashMap`보다 `accessOrder=true` 여부를 먼저 확인하는 편이 빠르다.

## 드릴 2: 기존 key에 다시 `put()`했을 때

이번에는 새 key가 아니라 **이미 있는 `B`의 value만 갱신**한다.

```java
import java.util.LinkedHashMap;
import java.util.Map;

Map<String, Integer> insertionOrder = new LinkedHashMap<>();
insertionOrder.put("A", 1);
insertionOrder.put("B", 2);
insertionOrder.put("C", 3);
insertionOrder.put("B", 20);

Map<String, Integer> accessOrder = new LinkedHashMap<>(16, 0.75f, true);
accessOrder.put("A", 1);
accessOrder.put("B", 2);
accessOrder.put("C", 3);
accessOrder.put("B", 20);
```

| map | 결과 | 읽는 법 |
|---|---|---|
| 기본 `LinkedHashMap` | `[A, B, C]` | 기존 key 값만 바뀌고 자리는 유지 |
| `LinkedHashMap(access-order=true)` | `[A, C, B]` | 기존 key를 다시 만졌다고 보고 `B`를 뒤로 이동 |

여기서 많이 나오는 오해는 "`put()`이면 삽입이니까 항상 맨 뒤 아닌가요?"다.
하지만 beginner용으로는 이렇게 자르는 편이 안전하다.

- 새 key `put()`이면 둘 다 맨 뒤에 붙는다
- 기존 key `put()`이면 기본 모드는 자리 유지, access-order 모드는 최근 접근처럼 뒤로 갈 수 있다

즉 "같은 key에 새 value를 넣었다"와 "새로 삽입했다"는 같은 말이 아니다.

## 자주 헷갈리는 순간

- "`get()`은 읽기니까 순서를 바꾸면 안 되는 것 아닌가요?"  
  기본 모드에서는 그렇지만, access-order 모드에서는 읽기 자체가 접근 기록이다.
- "`put()`은 무조건 삽입이니까 기존 key도 맨 뒤로 가겠죠?"  
  새 key 추가와 기존 key 갱신을 나눠서 봐야 한다.
- "`기본 LinkedHashMap`도 순서가 있으니 access-order와 거의 같지 않나요?"  
  아니다. "조회 후 이동"과 "기존 key 갱신 후 이동"이 갈라지는 순간 두 모드는 바로 구분된다.
- "이 규칙만 알면 LRU 캐시 전체를 이해한 건가요?"  
  아니다. 여기서는 순서 규칙만 고정한다. eviction 정책과 동시성은 다음 문서에서 따로 본다.

안전한 판별 순서는 아래처럼 잡으면 된다.

1. 새 key 추가인지, 기존 key 갱신인지 먼저 본다.
2. `get()`이나 기존 key `put()` 뒤에 순서가 바뀌었는지 본다.
3. 바뀌었다면 `accessOrder=true`를 먼저 의심한다.

## 다음 읽기

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| "`get()`이 왜 eviction 결과까지 바꾸지?" | [LinkedHashMap access-order와 캐시 동작 브리지](./linkedhashmap-access-order-cache-behavior-bridge.md) |
| "`TreeMap` range query랑 access-order를 자꾸 같은 ordered map으로 읽는다" | [LinkedHashMap access-order vs TreeMap navigable API 미니 드릴](./linkedhashmap-access-order-vs-treemap-navigable-mini-drill.md) |
| "삽입 순서 map, access-order map, 정렬 map을 한 장으로 다시 보고 싶다" | [Map 구현체별 반복 순서 치트시트](./hashmap-linkedhashmap-treemap-iteration-order-cheat-sheet.md) |
| "기본 개념부터 아주 짧게 다시 보고 싶다" | [LinkedHashMap access-order 미니 프라이머](../../data-structure/linkedhashmap-access-order-mini-primer.md) |

## 한 줄 정리

`LinkedHashMap`에서 `get()`과 기존 key `put()` 뒤 순서가 그대로면 기본 삽입 순서 모드, 그 key가 뒤로 가면 `accessOrder=true` 쪽이라고 읽으면 default 모드와 access-order 모드를 가장 빨리 구분할 수 있다.
