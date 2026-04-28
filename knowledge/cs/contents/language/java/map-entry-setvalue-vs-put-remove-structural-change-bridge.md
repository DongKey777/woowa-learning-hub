# Map 값 변환 프라이머: `replaceAll()` vs `entrySet()` 수정 vs 새 맵 만들기

> 한 줄 요약: `Map`을 돌며 value를 바꿔야 할 때 초보자 기본값은 `replaceAll()`이고, 조건 분기가 더 필요하면 `entrySet()` 수정, 원본 보존이 더 중요하면 새 맵 만들기로 나누면 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Map Iteration Patterns Cheat Sheet](./map-iteration-patterns-cheat-sheet.md)
- [Map 수정 중 순회 안전 가이드](./map-remove-during-iteration-safety-primer.md)
- [Collection Update Strategy Primer](./collection-update-strategy-primer.md)
- [Java 스트림과 람다 입문](./java-stream-lambda-basics.md)

retrieval-anchor-keywords: map value transform primer, java map replaceall beginner, map entryset setvalue beginner, new map copy transform java, map 순회 중 값 변환, replaceall vs entryset vs new map, hashmap value update pattern, map in place mutation beginner, map copy and replace beginner, map readability safety choice, map for each put smell, map structural change beginner, map replaceall condition update, entryset setvalue vs replaceall, 새 맵 만들기 map 변환

## 먼저 잡는 멘탈 모델

`Map` value 변환은 "같은 사물함을 고치나, 새 사물함을 다시 만드나"로 보면 쉽다.

- 모든 value를 같은 규칙으로 바꾼다 -> `replaceAll()`
- 순회하면서 일부 entry만 보고 바꾼다 -> `entrySet()` + `setValue(...)`
- 원본을 건드리면 불안하다 -> 새 맵 만들기

초보자 기준 첫 질문은 이것 하나면 충분하다.

> "원본 맵을 바로 고쳐도 되나?"

## 10초 선택표

| 지금 하려는 일 | 먼저 떠올릴 선택 | 안전성/가독성 기준 |
|---|---|---|
| 모든 value를 같은 규칙으로 바꾼다 | `replaceAll()` | 가장 짧고 의도가 바로 보임 |
| key와 현재 value를 같이 보며 일부만 바꾼다 | `entrySet()` + `setValue(...)` | 조건 분기를 직접 읽기 쉬움 |
| 원본 유지, 단계 분리, 결과 교체가 중요하다 | 새 맵 만들기 | side effect 범위가 가장 분명함 |

짧게 외우면 된다.

- 전체 일괄 변환이면 `replaceAll()`
- 조건부 수정이면 `entrySet()`
- 원본 보호면 새 맵

## 같은 예제로 세 패턴 보기

쿠폰 할인율을 5%p 올리되, 50%는 넘기지 않는다고 하자.

```java
Map<String, Integer> discountByGrade = new HashMap<>();
```

### 1. `replaceAll()`이 기본값인 경우

```java
discountByGrade.replaceAll((grade, discount) -> Math.min(discount + 5, 50));
```

이 코드는 "모든 entry를 같은 규칙으로 바꾼다"가 한 줄로 보인다.
초보자 기본값으로 가장 좋은 이유는 순회 코드보다 **변환 의도**가 먼저 읽히기 때문이다.

### 2. `entrySet()` 수정이 더 읽기 쉬운 경우

```java
for (Map.Entry<String, Integer> entry : discountByGrade.entrySet()) {
    if (entry.getKey().startsWith("VIP")) {
        entry.setValue(Math.min(entry.getValue() + 5, 50));
    }
}
```

이 패턴은 "VIP만 올린다"처럼 조건이 분명할 때 좋다.
핵심은 `put(...)` 대신 `entry.setValue(...)`로 **지금 보고 있는 칸의 value만 바꾼다**는 점을 드러내는 것이다.

### 3. 새 맵 만들기가 더 안전한 경우

```java
Map<String, Integer> updated = new HashMap<>();

for (Map.Entry<String, Integer> entry : discountByGrade.entrySet()) {
    updated.put(entry.getKey(), Math.min(entry.getValue() + 5, 50));
}

discountByGrade = updated;
```

이 패턴은 "원본을 끝까지 유지하고, 마지막에만 바꿔 끼운다"는 흐름이 중요할 때 좋다.
테스트 중간 확인, 실패 복구, 불변 스타일에 더 잘 맞는다.

## 초보자용 Do / Don't

| Do | 이유 | Don't | 왜 헷갈리나 |
|---|---|---|---|
| `replaceAll(...)` | 전체 변환 의도가 바로 보임 | `for-each` 안에서 `map.put(...)` 반복 | 기존 key 덮어쓰기인지 새 key 추가인지 한 번 더 생각해야 함 |
| `entry.setValue(...)` | 현재 entry value만 수정한다고 드러남 | `for-each` 안에서 `map.remove(...)`/`put(newKey, ...)` | 값 변환이 아니라 구조 변경까지 섞임 |
| 새 맵에 `put(...)` | 원본 보존 범위가 분명함 | 원본/복사본 기준 없이 섞어 수정 | side effect 범위를 놓치기 쉬움 |

증상 문장으로도 연결해 두면 좋다.

- "순회 중 값만 바꾸고 싶어요" -> `replaceAll()` 또는 `entrySet().setValue(...)`
- "조건이 복잡해서 한 줄이 안 읽혀요" -> `entrySet()` 루프
- "원본이 중간에 바뀌면 불안해요" -> 새 맵 만들기

## 자주 하는 오해

- "`replaceAll()`이니까 구조도 바꾸나요?"
  아니다. 기존 key는 그대로 두고 각 value를 다시 계산한다.
- "`entrySet()`에서 `put(existingKey, ...)` 해도 되지 않나요?"
  동작할 수는 있어도 초보자 코드에서는 `setValue(...)`가 의도를 더 직접적으로 보여 준다.
- "새 맵 만들기는 무조건 과한가요?"
  아니다. 원본 보존이 요구사항이면 가장 읽기 쉬운 선택일 수 있다.
- "그럼 `map.remove(...)`도 같이 섞어도 되나요?"
  값 변환 프라이머에서는 섞지 않는 쪽이 안전하다. 삭제/추가는 [Map 수정 중 순회 안전 가이드](./map-remove-during-iteration-safety-primer.md)로 분리해서 본다.

## 한 줄 정리

전체 value를 한 규칙으로 바꾸면 `replaceAll()`, 조건부로 현재 entry만 고치면 `entrySet()` + `setValue(...)`, 원본 보존이 더 중요하면 새 맵 만들기로 고르면 `Map` 값 변환 코드를 초보자도 더 안전하고 읽기 쉽게 가져갈 수 있다.
