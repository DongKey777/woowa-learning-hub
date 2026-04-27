# Iterable vs Collection vs Map 브리지 입문

> 한 줄 요약: `Iterable`은 "반복할 수 있다"는 약속이고, `Collection`은 "원소 묶음" 인터페이스이며, `Map`은 key-value 사전이라 `Collection` 계층과 분리되어 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [Java 제네릭 입문](./java-generics-basics.md)
- [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
- [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md)

retrieval-anchor-keywords: iterable collection map 차이, iterable vs collection vs map, java interface hierarchy iterable collection map, map is not collection, for each iterable map iteration, java iterator basics, java entrySet keySet values 차이, collection iteration api beginner, map iteration beginner, collection api size add remove, iterable forEach beginner, 처음 배우는데 Iterable Collection Map 차이, Map은 Collection인가요, 자바 컬렉션 계층 구조, 자바 반복 API 기초

## 먼저 잡는 멘탈 모델

- `Iterable`: "for-each로 순회 가능"이라는 **반복 약속**
- `Collection`: 원소들을 담는 **컨테이너 약속** (`size`, `add`, `remove` 같은 공통 API)
- `Map`: key로 value를 찾는 **사전 약속** (원소 하나가 아니라 `key -> value` 쌍)

핵심만 기억하면 된다.

- `Collection`은 `Iterable`을 상속한다.
- `Map`은 `Collection`을 상속하지 않는다.
- 그래서 `Map`은 순회할 때 `entrySet()`/`keySet()`/`values()` 중 하나를 먼저 꺼내서 돈다.

## 계층 구조를 한 줄 트리로 보기

```text
Iterable<E>
└─ Collection<E>
   ├─ List<E>
   ├─ Set<E>
   └─ Queue<E>

Map<K, V>   // Collection 계층 밖
```

## API 비교표 (초보자용 최소 버전)

| 타입 | 주 목적 | 대표 공통 API | for-each 직접 가능? |
|---|---|---|---|
| `Iterable<E>` | 순회 가능성 표현 | `iterator()`, `forEach(...)` | 가능 |
| `Collection<E>` | 원소 묶음 조작 | `size()`, `isEmpty()`, `add()`, `remove()`, `contains()` | 가능 (`Iterable` 상속) |
| `Map<K,V>` | key-value 조회/갱신 | `put()`, `get()`, `containsKey()`, `remove()` | 불가 (`Map` 자체는 `Iterable` 아님) |

## 같은 데이터, 반복 방식만 비교

```java
import java.util.HashMap;
import java.util.List;
import java.util.Map;

List<String> names = List.of("alice", "bob");

for (String name : names) { // List는 Collection -> Iterable
    System.out.println(name);
}

Map<String, Integer> scoreByUser = new HashMap<>();
scoreByUser.put("alice", 95);
scoreByUser.put("bob", 88);

for (Map.Entry<String, Integer> entry : scoreByUser.entrySet()) {
    System.out.println(entry.getKey() + " -> " + entry.getValue());
}
```

읽는 포인트는 2개다.

- `List`는 바로 `for-each` 가능
- `Map`은 `entrySet()`으로 바꿔서 `for-each` 가능

## Map 반복 API 빠른 선택

| 지금 필요한 것 | API |
|---|---|
| key와 value 둘 다 | `entrySet()` |
| key만 | `keySet()` |
| value만 | `values()` |

초보자 기본값은 `entrySet()`이다. key/value 둘 다 필요한 경우가 가장 흔하고, 의도도 가장 명확하다.

## 흔한 혼동 정리

- "`Map`도 데이터 모음인데 왜 `Collection`이 아니죠?"
  `Collection`은 "원소 하나(`E`)"를 다루는 계층이고, `Map`은 "쌍(`K`,`V`)"을 다루는 별도 계약이라서 분리되어 있다.
- "`for (x : map)`이 왜 안 되죠?"
  `Map`은 `Iterable`이 아니기 때문이다. `map.entrySet()` 같은 뷰를 꺼내 순회해야 한다.
- "`Iterable`만 알면 컬렉션 조작도 되나요?"
  아니다. `Iterable`은 순회 약속만 담는다. 추가/삭제/크기 확인은 `Collection` API다.
- "`Collection`과 `Collections`는 같은 건가요?"
  아니다. `Collection`은 인터페이스, `Collections`는 유틸리티 클래스다.

## 다음 읽기

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| "List/Set/Map 첫 선택을 빠르게 고르고 싶어요" | [Java 컬렉션 프레임워크 입문](./java-collections-basics.md) |
| "`Set` 중복 판단이 왜 이상해 보여요?" | [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md) |
| "`Map`에서 floor/ceiling 같은 탐색은 언제 쓰죠?" | [NavigableMap and NavigableSet Mental Model](./navigablemap-navigableset-mental-model.md) |
