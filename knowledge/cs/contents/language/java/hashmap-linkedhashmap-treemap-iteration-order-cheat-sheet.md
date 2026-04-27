# Map 구현체별 반복 순서 치트시트

> 한 줄 요약: `HashMap`은 반복 순서를 믿으면 안 되고, `LinkedHashMap`은 기본이 삽입 순서지만 `access-order=true`면 최근 접근 순서로 바뀌며, `TreeMap`은 정렬 순서로 읽으면 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [Map 구현체 선택 미니 드릴](./map-implementation-selection-mini-drill.md)
- [HashMap vs LinkedHashMap vs TreeMap Key Contract Bridge](./hashmap-vs-linkedhashmap-vs-treemap-key-contract-bridge.md)
- [Map Iteration Patterns Cheat Sheet](./map-iteration-patterns-cheat-sheet.md)
- [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)
- [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md)

retrieval-anchor-keywords: hashmap linkedhashmap treemap iteration order, java map order cheat sheet, hashmap iteration order not guaranteed, linkedhashmap insertion order, linkedhashmap access order, linkedhashmap lru example, treemap sorted order, map 구현체별 순서 차이, hashmap linkedhashmap treemap 차이, 자바 map 순서 보장, 자바 hashmap 순서 왜 바뀌지, linkedhashmap accessorder 뭐예요, linkedhashmap 최근 접근 순서, map 출력 순서 오해, beginner map order primer

## 먼저 잡는 멘탈 모델

`Map`에서 "반복 순서"는 `Map` 공통 규칙이 아니라 **구현체별 규칙**이다.

- `HashMap`: 순서 없음
- `LinkedHashMap`: 기본은 넣은 순서, 옵션을 바꾸면 최근 접근 순서
- `TreeMap`: 정렬 순서 있음

그래서 "출력 순서가 중요하다"는 요구가 생기면 `Map`만 고르면 안 되고, 어떤 구현체인지까지 같이 골라야 한다.

## 10초 비교표

| 구현체 | 반복 순서 | 보장 여부 | 이런 때 고른다 |
|---|---|---|---|
| `HashMap` | 예측하지 않는다 | 순서 미보장 | 순서보다 일반 조회/갱신이 중요할 때 |
| `LinkedHashMap` | 기본은 삽입 순서 | 보장 | 화면/로그에서 넣은 순서대로 보여 주고 싶을 때 |
| `TreeMap` | key 정렬 순서 | 보장 | key를 오름차순/정렬 기준대로 보고 싶을 때 |

초보자용 기억 문장은 이것만으로 충분하다.

- "순서 기대 안 함" -> `HashMap`
- "넣은 순서 유지" -> 기본 `LinkedHashMap`
- "최근에 본 것이 뒤로 가야 함" -> `LinkedHashMap(access-order=true)`
- "정렬해서 봄" -> `TreeMap`

## 같은 데이터로 바로 비교

```java
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.TreeMap;

Map<String, Integer> hashMap = new HashMap<>();
Map<String, Integer> linkedHashMap = new LinkedHashMap<>();
Map<String, Integer> treeMap = new TreeMap<>();

hashMap.put("banana", 2);
hashMap.put("apple", 1);
hashMap.put("carrot", 3);

linkedHashMap.put("banana", 2);
linkedHashMap.put("apple", 1);
linkedHashMap.put("carrot", 3);

treeMap.put("banana", 2);
treeMap.put("apple", 1);
treeMap.put("carrot", 3);

System.out.println(linkedHashMap.keySet()); // [banana, apple, carrot]
System.out.println(treeMap.keySet());       // [apple, banana, carrot]
System.out.println(hashMap.keySet());       // 순서를 기대하면 안 됨
```

읽는 포인트는 두 가지다.

- `LinkedHashMap`은 넣은 순서를 그대로 보여 준다.
- `TreeMap`은 `key` 기준으로 정렬해서 보여 준다.

`HashMap`은 어떤 실행에서 우연히 일정해 보일 수 있어도, 그 결과를 로직 규칙처럼 믿으면 안 된다.

## `LinkedHashMap`의 삽입 순서 vs 접근 순서

`LinkedHashMap`은 여기서 한 번 더 갈린다.

| 모드 | 순서가 바뀌는 순간 | 이런 때 쓴다 |
|---|---|---|
| 기본값 (`access-order=false`) | 새 key를 `put`할 때 | 입력한 순서를 유지하고 싶을 때 |
| 접근 순서 (`access-order=true`) | `get`, `put`, `putIfAbsent`처럼 entry를 다시 만질 때 | "최근에 사용한 것" 기준으로 보고 싶을 때 |

즉 `LinkedHashMap`은 항상 "삽입 순서 map"이 아니다. 생성자 옵션 하나로 "최근 접근 순서 map"으로도 쓸 수 있다.

## 작은 LRU 느낌 예제

```java
import java.util.LinkedHashMap;
import java.util.Map;

Map<String, String> cache = new LinkedHashMap<>(16, 0.75f, true) {
    @Override
    protected boolean removeEldestEntry(Map.Entry<String, String> eldest) {
        return size() > 2;
    }
};

cache.put("A", "apple");
cache.put("B", "banana");   // [A, B]
cache.get("A");             // [B, A]  최근 접근한 A가 뒤로 감
cache.put("C", "carrot");   // [A, C]  가장 오래된 B 제거
```

이 예제의 읽는 포인트는 두 가지다.

- 세 번째 인자 `true`가 `access-order`를 켠다.
- `removeEldestEntry()`를 같이 쓰면 "가장 오래 안 쓴 것부터 밀어내기" 같은 아주 작은 LRU 스타일 캐시를 만들 수 있다.

## 자주 하는 오해 4가지

- "`HashMap`도 지금은 항상 같은 순서로 찍히는데요?"
  지금 그 환경에서 우연히 그렇게 보이는 것뿐이다. 반복 순서 계약이 아니므로 코드 의미로 기대하면 안 된다.
- "`LinkedHashMap`은 key를 정렬해 주나요?"
  아니다. 정렬이 아니라 **삽입 순서 유지**다.
- "`LinkedHashMap`은 항상 넣은 순서 아닌가요?"
  기본은 그렇지만, `new LinkedHashMap<>(..., true)`로 만들면 최근 접근 순서로 바뀐다.
- "`TreeMap`은 value 기준 정렬인가요?"
  아니다. 기본은 **key 기준 정렬**이다. `Comparator`를 주지 않으면 key의 자연 순서를 쓴다.
- "출력만 예쁘게 하고 싶은데 `HashMap` 써도 되나요?"
  출력 순서가 중요한 순간부터 `HashMap`은 의도가 약하다. `LinkedHashMap`이나 `TreeMap`으로 의도를 드러내는 편이 안전하다.

## 어떤 구현체를 고를지 빠르게 정하기

| 요구사항 한 줄 | 첫 선택 |
|---|---|
| "순서는 상관없고 key로 빨리 찾고 싶다" | `HashMap` |
| "사용자가 입력한 순서대로 보여 주고 싶다" | `LinkedHashMap` |
| "최근에 본 항목이 뒤로 가야 하고 오래된 것을 밀어내고 싶다" | `LinkedHashMap(access-order=true)` |
| "이름순, 날짜순처럼 정렬된 key 순서가 필요하다" | `TreeMap` |

## 다음 읽기

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| "짧은 요구 문장에서 셋 중 하나를 바로 골라야 한다" | [Map 구현체 선택 미니 드릴](./map-implementation-selection-mini-drill.md) |
| "조회 규칙과 immutable key까지 같이 비교하고 싶다" | [HashMap vs LinkedHashMap vs TreeMap Key Contract Bridge](./hashmap-vs-linkedhashmap-vs-treemap-key-contract-bridge.md) |
| "`Map`을 돌 때 `entrySet()`/`keySet()`/`values()` 중 뭘 써야 하지?" | [Map Iteration Patterns Cheat Sheet](./map-iteration-patterns-cheat-sheet.md) |
| "`TreeMap`에서 왜 두 번째 `put`이 덮어써지지?" | [Natural Ordering in TreeSet and TreeMap](./treeset-treemap-natural-ordering-compareto-bridge.md) |
| "`firstKey`, `floorKey` 같은 탐색은 언제 쓰지?" | [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md) |

## 한 줄 정리

반복 순서가 중요하면 `Map`이 아니라 `HashMap`/`LinkedHashMap`/`TreeMap` 중 무엇인지까지 명확히 고르고, `LinkedHashMap`은 삽입 순서인지 접근 순서인지까지 함께 결정해야 오해를 줄일 수 있다.
