# List 순회 중 삭제와 인덱스 밀림 프라이머

> 한 줄 요약: `List`를 돌면서 지울 때는 `for-each` 안의 `list.remove(...)`를 피하고, 상황에 따라 `Iterator.remove()`, 역순 인덱스 삭제, `removeIf(...)` 중 하나를 고르면 인덱스 밀림과 순회 예외를 함께 줄일 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [Collection Update Strategy Primer](./collection-update-strategy-primer.md)
- [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md)
- [Set 수정 중 순회 안전 가이드](./set-remove-during-iteration-safety-primer.md)
- [Map 수정 중 순회 안전 가이드](./map-remove-during-iteration-safety-primer.md)

retrieval-anchor-keywords: list remove during iteration, java list index shift, iterator remove list beginner, reverse index removal list, removeif list beginner, arraylist remove while iterating, for each list remove bug, concurrentmodificationexception list beginner, list 순회 중 삭제, 리스트 인덱스 밀림, 자바 list removeif 기초, 자바 iterator remove list, list remove during iteration index shift primer basics, list remove during iteration index shift primer beginner, list remove during iteration index shift primer intro

## 먼저 잡는 멘탈 모델

`List` 삭제는 "줄에서 사람을 빼면 뒤 사람이 한 칸씩 앞으로 당겨진다"로 이해하면 쉽다.

- `for-each` 순회 중 바깥 `list.remove(...)`를 호출하면 순회가 보던 목록이 중간에 바뀐다
- 앞에서부터 인덱스로 지우면 뒤 원소가 앞으로 당겨져서 다음 칸을 건너뛸 수 있다

초보자용 기본 규칙은 이 세 줄이면 충분하다.

- `for-each` 안에서 직접 `list.remove(...)` 하지 않는다
- 조건 삭제만 하면 `removeIf(...)`를 먼저 본다
- 인덱스로 직접 지워야 하면 뒤에서 앞으로 지운다

## 가장 흔한 실수 두 가지

| 실수 | 왜 문제인가 | 바로 바꿀 것 |
|---|---|---|
| `for-each` 안에서 `list.remove(...)` | 순회와 삭제 통로가 달라져 `ConcurrentModificationException`이 날 수 있다 | `Iterator.remove()` 또는 `removeIf(...)` |
| `for (int i = 0; i < list.size(); i++)`에서 앞에서부터 삭제 | 삭제 직후 뒤 원소가 앞으로 당겨져 다음 검사 대상을 건너뛸 수 있다 | 역순 인덱스 삭제 |

여기서 `Concurrent`는 꼭 멀티스레드 뜻이 아니다. 같은 스레드에서도 순회 중 구조를 바꾸면 충분히 깨질 수 있다.

## 왜 인덱스가 밀릴까

```java
List<String> names = new ArrayList<>(List.of("a", "x", "x", "b"));

for (int i = 0; i < names.size(); i++) {
    if (names.get(i).equals("x")) {
        names.remove(i); // 앞에서부터 삭제
    }
}
```

첫 번째 `"x"`를 지우면 뒤 `"x"`가 앞으로 당겨진다.
그런데 `for` 루프는 바로 `i++`를 해 버려서, 당겨진 원소를 검사하지 못하고 지나칠 수 있다.

즉 `List`에서는 "삭제"와 "다음 인덱스 이동"이 서로 영향을 준다.
그래서 초보자는 "앞에서 지우면 밀린다, 뒤에서 지우면 덜 꼬인다"를 먼저 기억하면 된다.

## 세 가지 안전한 선택지

| 상황 | 추천 | 이유 |
|---|---|---|
| 한 칸씩 보면서 지울지 말지 결정 | `Iterator.remove()` | 순회와 삭제를 같은 통로로 맞춘다 |
| 인덱스 자체가 필요한 삭제 | 역순 인덱스 삭제 | 뒤에서 지우면 앞 인덱스가 안 밀린다 |
| 조건에 맞는 원소를 한 번에 제거 | `removeIf(...)` | 의도가 가장 짧게 보인다 |

초보자 기본값은 `removeIf(...)`다.
인덱스가 꼭 필요할 때만 역순 루프를, while 흐름이 이미 필요할 때만 `Iterator.remove()`를 고르면 된다.

## 1. `Iterator.remove()`: 순회와 삭제를 같은 통로로 맞춘다

```java
Iterator<String> iterator = names.iterator();

while (iterator.hasNext()) {
    String name = iterator.next();

    if (name.equals("x")) {
        iterator.remove();
    }
}
```

읽는 포인트는 두 개다.

- 현재 원소는 `next()`로 받는다
- 삭제는 `list.remove(name)`가 아니라 `iterator.remove()`로 한다

`for-each`를 직접 깨지 않고, "지금 순회 중인 도구가 허용한 삭제"만 쓰는 방식이다.

## 2. 역순 인덱스 삭제: 인덱스가 필요하면 뒤에서 앞으로

```java
for (int i = names.size() - 1; i >= 0; i--) {
    if (names.get(i).equals("x")) {
        names.remove(i);
    }
}
```

이 패턴은 `List`에서만 특히 중요하다.

- 뒤 원소를 지워도 앞쪽 인덱스는 그대로다
- 그래서 아직 검사하지 않은 칸 번호가 흔들리지 않는다

초보자가 "삭제 대상의 위치를 같이 써야 한다", "인덱스 기반 로직을 이미 돌고 있다" 같은 상황이면 역순 루프가 가장 단순할 때가 많다.

## 3. `removeIf(...)`: 조건 삭제면 가장 먼저 떠올릴 기본값

```java
names.removeIf(name -> name.equals("x"));
```

조건 삭제가 목적이면 이 한 줄이 제일 읽기 쉽다.

- `"x"`면 제거
- 아니면 유지

직접 인덱스를 관리하지 않아도 되고, `Iterator` 문법도 감출 수 있어서 초보자 실수를 가장 빠르게 줄여 준다.

## 같은 요구를 세 방식으로 비교

`"temp"`로 시작하는 문자열을 삭제한다고 하자.

```java
// 1) while 흐름이 필요할 때
Iterator<String> iterator = names.iterator();
while (iterator.hasNext()) {
    if (iterator.next().startsWith("temp")) {
        iterator.remove();
    }
}

// 2) 인덱스가 필요할 때
for (int i = names.size() - 1; i >= 0; i--) {
    if (names.get(i).startsWith("temp")) {
        names.remove(i);
    }
}

// 3) 조건 삭제만 하면 될 때
names.removeIf(name -> name.startsWith("temp"));
```

가장 짧게 고르는 법은 이렇다.

- 조건만 보이면 `removeIf(...)`
- 인덱스가 중요하면 역순 삭제
- 순회 중 다른 로직도 많으면 `Iterator.remove()`

## 초보자 혼동 포인트

- "`for-each` 안에서 하나만 지우면 괜찮지 않나요?"
  아니다. 하나만 지워도 바깥 `list.remove(...)`면 같은 문제다.
- "`ConcurrentModificationException`이면 멀티스레드 버그인가요?"
  꼭 아니다. 같은 스레드에서도 순회 중 구조를 바꾸면 날 수 있다.
- "`removeIf(...)`도 결국 원본을 바꾸나요?"
  그렇다. 새 리스트를 만드는 것이 아니라 원본 `List`에서 삭제한다.
- "`ArrayList`만 이런가요?"
  아니다. `LinkedList`라도 `for-each` 중 바깥 삭제는 같은 결의 실수다. 다만 인덱스 밀림 설명은 `List` 전반에 공통으로 이해해 두면 된다.
- "앞에서부터 삭제하되 `i--` 하면 되나요?"
  가능은 하지만 초보자에게는 역순 루프가 더 읽기 쉽고 덜 헷갈린다.

## 빠른 선택 규칙

1. 그냥 조건으로 몇 개 지우는 일인가?
   `removeIf(...)`부터 본다.
2. 삭제 대상의 인덱스가 중요한가?
   역순 인덱스 삭제를 쓴다.
3. 순회 흐름 안에서 중간 판단과 삭제가 함께 필요한가?
   `Iterator.remove()`를 쓴다.

## 한 줄 정리

`List` 삭제는 `for-each` 안의 직접 `remove(...)`를 피하고, 조건 삭제는 `removeIf(...)`, 인덱스 삭제는 역순 루프, 순회 중 한 칸씩 판단은 `Iterator.remove()`로 고르면 초보자 실수를 크게 줄일 수 있다.
