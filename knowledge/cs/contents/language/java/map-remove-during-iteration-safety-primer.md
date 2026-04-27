# Map 수정 중 순회 안전 가이드

> 한 줄 요약: `Map`을 돌면서 지워야 할 때는 `for-each` 안에서 `map.remove(...)`를 바로 부르지 말고, `Iterator.remove()` 또는 `entrySet().removeIf(...)`처럼 "순회가 허용한 삭제 통로"를 써야 한다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [Iterable vs Collection vs Map 브리지 입문](./iterable-collection-map-iteration-bridge.md)
- [Map Iteration Patterns Cheat Sheet](./map-iteration-patterns-cheat-sheet.md)
- [Map `entry.setValue(...)` vs `put/remove(...)`: 값 수정과 구조 변경 미니 브리지](./map-entry-setvalue-vs-put-remove-structural-change-bridge.md)
- [`ConcurrentHashMap` Compound Actions and Hot-Key Contention](./concurrenthashmap-compound-actions-hot-key-contention.md)

retrieval-anchor-keywords: java map remove during iteration, java concurrentmodificationexception beginner, iterator.remove map example, map entryset removeif example, for each map.remove bug, map 순회 중 삭제, concurrentmodificationexception 원인, iterator remove 사용법, removeif map entryset, map 수정 중 순회 안전, 자바 map 순회 삭제 do dont, map entryset iterator remove beginner, map remove while iterating java, map.remove in for each don't

## 먼저 잡는 멘탈 모델

`Map` 순회는 "지금 보고 있는 목록" 위를 걷는 일이다.
그런데 걷는 도중에 바깥에서 목록 구조를 갑자기 바꾸면, 순회는 "내가 보고 있던 목록이 바뀌었네?"라고 판단하고 깨질 수 있다.

초보자용 규칙은 이 한 줄이면 충분하다.

- 순회 중 삭제가 필요하면, 순회 도구가 제공한 삭제 방법만 쓴다

즉 보통 아래 둘만 기억하면 된다.

- 한 칸씩 보며 지울 때: `Iterator.remove()`
- 조건으로 한 번에 지울 때: `removeIf(...)`

## 가장 흔한 실수 한 장 표

| 상황 | Do | Don't |
|---|---|---|
| `for-each`로 `entrySet()` 순회 중 삭제 | `Iterator.remove()` 사용 | `map.remove(key)` 직접 호출 |
| 조건에 맞는 항목 여러 개 삭제 | `entrySet().removeIf(...)` 사용 | 순회 안에서 직접 `map.remove(...)` 반복 |
| "`Map`에 `removeIf` 있나?" | `entrySet()`/`keySet()`/`values()` 뷰에서 호출 | `map.removeIf(...)` 찾기 |

## 왜 `ConcurrentModificationException`이 나올까

이 예시는 초보자가 가장 자주 만드는 패턴이다.

```java
for (Map.Entry<String, Integer> entry : scores.entrySet()) {
    if (entry.getValue() < 60) {
        scores.remove(entry.getKey()); // Don't
    }
}
```

문제는 "순회는 `entrySet()`이 관리하는데, 삭제는 바깥의 `scores.remove(...)`로 해 버렸다"는 점이다.

이때 자주 보는 예외가 `ConcurrentModificationException`이다.
여기서 `Concurrent`는 꼭 멀티스레드라는 뜻이 아니다. 같은 스레드에서도 "순회 도중 구조 변경"이면 충분히 터질 수 있다.

## Do 1: 한 칸씩 보며 지울 때는 `Iterator.remove()`

```java
Iterator<Map.Entry<String, Integer>> iterator = scores.entrySet().iterator();

while (iterator.hasNext()) {
    Map.Entry<String, Integer> entry = iterator.next();

    if (entry.getValue() < 60) {
        iterator.remove(); // Do
    }
}
```

이 코드는 순회와 삭제가 같은 통로를 쓰므로 안전하다.

읽는 포인트는 2개다.

- `next()`로 현재 항목을 받는다
- 지울 땐 `map.remove(...)`가 아니라 `iterator.remove()`를 호출한다

## Do 2: 조건 삭제면 `removeIf(...)`가 더 읽기 쉽다

```java
scores.entrySet().removeIf(entry -> entry.getValue() < 60);
```

초보자 입장에서는 이 한 줄이 가장 읽기 쉽다.

- "점수가 60 미만인 entry를 지운다"가 바로 보인다
- 직접 `Iterator`를 다루지 않아도 된다

조건 삭제가 목적이라면 먼저 `removeIf(...)`를 떠올리면 된다.

## `removeIf(...)`는 어디에 쓰나

`Map` 자체에는 `removeIf(...)`가 없다.
대신 `Map`이 보여 주는 뷰에서 쓴다.

| 지우는 기준 | 추천 코드 | 설명 |
|---|---|---|
| key 기준 | `map.keySet().removeIf(key -> ...)` | key 조건으로 삭제 |
| value 기준 | `map.values().removeIf(value -> ...)` | value 조건으로 삭제 |
| key와 value 둘 다 기준 | `map.entrySet().removeIf(entry -> ...)` | 가장 표현력이 좋음 |

보통은 key와 value를 같이 보는 경우가 많아서 초보자 기본값은 `entrySet().removeIf(...)`다.

## 같은 요구, Do/Don't 비교

### 점수 60 미만 사용자 삭제

```java
// Do
scores.entrySet().removeIf(entry -> entry.getValue() < 60);

// Don't
for (Map.Entry<String, Integer> entry : scores.entrySet()) {
    if (entry.getValue() < 60) {
        scores.remove(entry.getKey());
    }
}
```

### 이름이 `temp`로 시작하는 key 삭제

```java
// Do
scores.keySet().removeIf(key -> key.startsWith("temp"));

// Don't
for (String key : scores.keySet()) {
    if (key.startsWith("temp")) {
        scores.remove(key);
    }
}
```

## 초보자 혼동 포인트

- "`ConcurrentModificationException`이면 멀티스레드 버그인가요?"
  꼭 아니다. 같은 스레드에서도 순회 중 구조를 바꾸면 날 수 있다.
- "`entry.setValue(...)`도 위험한가요?"
  값만 바꾸는 것은 보통 "구조 변경"이 아니라서 삭제/추가와는 결이 다르다. 초보자는 우선 "삭제/추가는 조심, 값 수정은 별개"로 구분하면 된다.
- "`Map`에 왜 `removeIf`가 없죠?"
  `Map` 자체는 `Collection`이 아니기 때문이다. 대신 `entrySet()`/`keySet()`/`values()` 같은 뷰에서 쓴다.
- "`values().removeIf(...)`를 쓰면 value만 지워지나요?"
  아니다. 그 value를 가진 항목(entry) 자체가 `Map`에서 제거된다.
- "그럼 무조건 `Iterator.remove()`만 쓰면 되나요?"
  아니다. 조건 삭제라면 `removeIf(...)`가 더 짧고 읽기 쉽다. `Iterator.remove()`는 while 순회가 이미 필요할 때 고르면 된다.

## 초보자용 선택 규칙

1. 그냥 조건으로 지우는 일인가?
   `entrySet().removeIf(...)`부터 본다.
2. 순회 중에 추가 로직이 많아서 while 루프가 필요한가?
   `Iterator.remove()`를 쓴다.
3. `for-each` 안에서 `map.remove(...)`를 쓰고 싶은가?
   일단 멈추고 위 둘 중 하나로 바꾼다.

## 다음 읽기

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| "`Map`은 왜 `for-each`를 바로 못 돌죠?" | [Iterable vs Collection vs Map 브리지 입문](./iterable-collection-map-iteration-bridge.md) |
| "`entrySet()`/`keySet()`/`values()`는 언제 고르죠?" | [Map Iteration Patterns Cheat Sheet](./map-iteration-patterns-cheat-sheet.md) |
| "`entry.setValue(...)`와 `put/remove(...)`는 어떻게 다르게 읽죠?" | [Map `entry.setValue(...)` vs `put/remove(...)`: 값 수정과 구조 변경 미니 브리지](./map-entry-setvalue-vs-put-remove-structural-change-bridge.md) |
| "동시성 컬렉션에서는 또 다르게 봐야 하나요?" | [`ConcurrentHashMap` Compound Actions and Hot-Key Contention](./concurrenthashmap-compound-actions-hot-key-contention.md) |

## 한 줄 정리

- `for-each` 안에서 `map.remove(...)`는 위험
- 순회 중 삭제는 `Iterator.remove()` 또는 `removeIf(...)`
- `Map` 자체가 아니라 `entrySet()`/`keySet()`/`values()`에서 삭제한다
