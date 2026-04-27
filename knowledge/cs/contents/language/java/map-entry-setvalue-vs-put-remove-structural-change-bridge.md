# Map `entry.setValue(...)` vs `put/remove(...)`: 값 수정과 구조 변경 미니 브리지

> 한 줄 요약: `entry.setValue(...)`는 지금 보고 있는 entry의 value만 바꾸는 쪽에 가깝고, `put(...)`/`remove(...)`는 key-value 자리 자체를 늘리거나 줄일 수 있는 구조 변경이라서 순회 중에는 같은 감각으로 섞어 보면 안 된다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Map 수정 중 순회 안전 가이드](./map-remove-during-iteration-safety-primer.md)
- [Map Iteration Patterns Cheat Sheet](./map-iteration-patterns-cheat-sheet.md)
- [Iterable vs Collection vs Map 브리지 입문](./iterable-collection-map-iteration-bridge.md)
- [Collection Update Strategy Primer](./collection-update-strategy-primer.md)

retrieval-anchor-keywords: map entry setvalue vs put remove, java structural modification map beginner, entry.setvalue iteration safe, map put remove during iteration, java map 값 수정 구조 변경, hashmap structural change beginner, map entry value overwrite, java map 순회 중 값 수정, entryset setvalue vs put, map remove concurrentmodificationexception, beginner map update distinction, java map overwrite vs insert, map entry setvalue vs put remove structural change bridge basics, map entry setvalue vs put remove structural change bridge beginner, map entry setvalue vs put remove structural change bridge intro

## 먼저 잡는 멘탈 모델

`Map`을 사물함으로 보면 쉽다.

- `entry.setValue(...)`: 이미 있는 사물함 칸은 그대로 두고, 그 안의 내용물만 바꾼다
- `put(...)`: 사물함 칸이 없으면 새 칸을 만들 수도 있고, 있으면 안의 내용물을 덮어쓸 수도 있다
- `remove(...)`: 사물함 칸 자체를 없앤다

초보자 기준 핵심은 "값 수정"과 "구조 변경"을 분리해서 읽는 것이다.

- 값 수정: 기존 key 자리는 유지하고 value만 바뀜
- 구조 변경: entry 개수나 key 배치가 달라질 수 있음

## 10초 비교표

| 코드 | 보통 무슨 일을 하나 | 구조 변경 가능성 | 순회 중 초보자 기본 선택 |
|---|---|---|---|
| `entry.setValue(newValue)` | 현재 entry의 value만 교체 | 보통 없음 | 값만 바꿀 때 가장 먼저 고려 |
| `map.put(existingKey, newValue)` | 기존 key의 value 덮어쓰기 | 보통 없음 | 가능해도 `entry.setValue(...)`가 의도 표현이 더 직접적 |
| `map.put(newKey, value)` | 새 entry 추가 | 있음 | 순회 중 직접 호출 피하기 |
| `map.remove(key)` | entry 삭제 | 있음 | 순회 중 직접 호출 피하기 |

여기서 beginner용 한 줄 규칙은 이것이다.

> 순회 중 value만 바꿀 일이면 `entry.setValue(...)`를 먼저 떠올리고, entry를 추가하거나 지우는 일은 구조 변경으로 따로 생각한다.

## 가장 헷갈리는 예제 하나

```java
for (Map.Entry<String, Integer> entry : scores.entrySet()) {
    if (entry.getValue() < 60) {
        entry.setValue(60); // 값만 보정
    }
}
```

이 코드는 "기존 key는 그대로 두고 점수 value만 바꾼다"는 의도가 바로 보인다.

반대로 아래는 구조가 흔들릴 수 있다.

```java
for (Map.Entry<String, Integer> entry : scores.entrySet()) {
    if (entry.getValue() < 60) {
        scores.remove(entry.getKey()); // entry 삭제
    }
}
```

이 코드는 순회 도중 entry 개수를 줄인다.
그래서 `ConcurrentModificationException` 같은 fail-fast 상황으로 이어지기 쉽다.

핵심 차이는 메서드 이름보다 "map의 칸 수나 key 배치가 바뀌는가"다.

## `put(...)`은 왜 더 조심해서 읽나

`put(...)`은 두 얼굴이 있다.

- 기존 key에 덮어쓰기: value 수정에 가까움
- 새 key 추가: 구조 변경

그래서 순회 중에 `put(...)`을 보면 초보자는 먼저 "이게 정말 기존 key 덮어쓰기만 하나?"를 확인해야 한다.
그 보장이 없다면 `entry.setValue(...)`가 더 안전한 사고방식이다.

```java
for (Map.Entry<String, Integer> entry : scores.entrySet()) {
    if (entry.getKey().equals("mina")) {
        entry.setValue(95);
    }
}
```

위 코드는 "지금 보고 있는 key의 value만 바꾼다"는 범위가 분명하다.
반면 `scores.put(someKey, 95)`는 `someKey`가 새 key인지 기존 key인지까지 같이 신경 써야 한다.

## 자주 하는 오해

- "`put(...)`은 그냥 값 바꾸기 아닌가요?"
  기존 key면 그럴 수 있지만, 새 key를 넣는 순간 구조 변경이다.
- "`entry.setValue(...)`도 map을 수정하니 위험한 것 아닌가요?"
  수정은 맞지만, 보통은 value 교체라서 삭제/추가와 같은 구조 변경과는 결이 다르다.
- "`remove(...)`만 조심하면 되나요?"
  아니다. 새 key를 넣는 `put(...)`도 구조를 바꾼다.
- "`put(existingKey, value)`면 항상 안전한가요?"
  구조 변경은 아닐 수 있어도, 순회 중 의도를 가장 분명하게 드러내는 코드는 보통 `entry.setValue(...)`다.

## 바로 쓰는 선택 규칙

- 지금 보고 있는 entry의 value만 고친다 -> `entry.setValue(...)`
- 조건에 맞는 entry를 지운다 -> `Iterator.remove()` 또는 `entrySet().removeIf(...)`
- 새 key를 넣어야 한다 -> 순회 밖에서 하거나 별도 로직으로 분리
- `put(...)`을 쓰고 싶다 -> 새 key 추가 가능성이 있는지 먼저 확인

## 한 줄 정리

`entry.setValue(...)`는 "기존 칸의 내용물만 교체", `put/remove(...)`는 "칸 자체를 늘리거나 줄일 수 있는 연산"으로 구분해 두면 `Map` 순회 중 수정 규칙을 훨씬 덜 헷갈린다.
