# Set 수정 중 순회 안전 가이드

> 한 줄 요약: `Set`을 돌면서 지워야 할 때는 `for-each` 안에서 `set.remove(...)`를 바로 부르지 말고, `Iterator.remove()` 또는 `removeIf(...)`처럼 순회가 허용한 삭제 통로를 써야 안전하다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [Collection Update Strategy Primer](./collection-update-strategy-primer.md)
- [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md)
- [Map 수정 중 순회 안전 가이드](./map-remove-during-iteration-safety-primer.md)
- [Mutable Element Pitfalls in List and Set](./mutable-element-pitfalls-list-set-primer.md)

retrieval-anchor-keywords: set remove during iteration, set iterator remove, set removeif beginner, set foreach remove bug, concurrentmodificationexception set beginner, hashset remove while iterating, treeset remove while iterating, java set 순회 중 삭제, 자바 set removeif 기초, 자바 set iterator remove, 자바 foreach set remove 실수, set 수정 중 순회 안전, set remove during iteration safety primer basics, set remove during iteration safety primer beginner, set remove during iteration safety primer intro

## 먼저 잡는 멘탈 모델

`Set` 순회는 "지금 보고 있는 집합 목록" 위를 걷는 일이다.
그런데 걷는 도중에 바깥에서 `set.remove(...)`로 구조를 바꾸면, 순회는 "내가 보던 목록이 중간에 바뀌었다"고 보고 깨질 수 있다.

초보자용 규칙은 한 줄이면 충분하다.

- 순회 중 삭제가 필요하면, 순회 도구가 준 삭제 통로만 쓴다

보통 아래 둘만 기억하면 된다.

- 한 칸씩 보며 지울 때: `Iterator.remove()`
- 조건으로 한 번에 지울 때: `removeIf(...)`

## 가장 흔한 실수 한 장 표

| 상황 | Do | Don't |
|---|---|---|
| `for-each`로 `Set` 순회 중 삭제 | `Iterator.remove()` | `set.remove(...)` 직접 호출 |
| 조건에 맞는 원소 여러 개 삭제 | `set.removeIf(...)` | `for-each` 안에서 `set.remove(...)` 반복 |
| "지우는 조건만 중요" | `removeIf(...)` 먼저 검토 | 굳이 `Iterator`부터 직접 작성 |

## 왜 `for-each` 안의 `set.remove(...)`가 위험할까

```java
for (String tag : tags) {
    if (tag.startsWith("temp")) {
        tags.remove(tag); // Don't
    }
}
```

문제는 순회는 `for-each`가 내부 `Iterator`로 진행하는데, 삭제는 바깥의 `tags.remove(...)`로 해 버렸다는 점이다.

이때 자주 보는 예외가 `ConcurrentModificationException`이다.
여기서 `Concurrent`는 꼭 멀티스레드라는 뜻이 아니다. 같은 스레드에서도 순회 도중 구조를 바꾸면 충분히 터질 수 있다.

## Do 1: 한 칸씩 보며 지울 때는 `Iterator.remove()`

```java
Iterator<String> iterator = tags.iterator();

while (iterator.hasNext()) {
    String tag = iterator.next();

    if (tag.startsWith("temp")) {
        iterator.remove();
    }
}
```

읽는 포인트는 두 개다.

- 현재 원소는 `next()`로 받는다
- 지울 때는 `set.remove(tag)`가 아니라 `iterator.remove()`를 호출한다

즉 순회와 삭제를 같은 통로로 맞추는 것이 핵심이다.

## Do 2: 조건 삭제면 `removeIf(...)`가 가장 짧다

```java
tags.removeIf(tag -> tag.startsWith("temp"));
```

초보자 입장에서는 이 한 줄이 가장 읽기 쉽다.

- temp로 시작하면 제거
- 아니면 남김

조건 삭제가 목적이라면 먼저 `removeIf(...)`를 떠올리면 된다.

## `Set`에서는 언제 무엇을 고르면 쉬울까

| 지금 필요한 것 | 추천 | 이유 |
|---|---|---|
| 삭제 말고도 중간 로직이 있다 | `Iterator.remove()` | while 흐름 안에서 한 칸씩 판단 가능 |
| 조건에 맞는 원소를 한 번에 지운다 | `removeIf(...)` | 의도가 가장 짧게 드러남 |
| `for-each` 안에서 이미 `set.remove(...)`를 쓰고 있다 | 위 둘 중 하나로 교체 | 실수 지점을 바로 없앰 |

`HashSet`, `LinkedHashSet`, `TreeSet`처럼 구현체가 달라도 이 기본 원칙은 같다.
순회 중 구조 삭제는 "컬렉션 바깥 remove"가 아니라 "순회가 허용한 remove"로 처리한다.

## 초보자 혼동 포인트

- "`ConcurrentModificationException`이면 멀티스레드 버그인가요?"
  꼭 아니다. 같은 스레드에서도 순회 중 구조를 바꾸면 날 수 있다.
- "`removeIf(...)`는 `Set`에도 되나요?"
  된다. `Set`은 `Collection` 계열이라 `removeIf(...)`를 바로 쓸 수 있다.
- "`for-each` 안에서 하나만 지우면 괜찮지 않나요?"
  아니다. 하나만 지워도 바깥 `set.remove(...)`면 같은 실수다.
- "`Iterator.remove()`가 항상 더 좋은가요?"
  아니다. 조건 삭제만 하면 될 때는 `removeIf(...)`가 더 짧고 읽기 쉽다.

## 한 줄 정리

`Set` 순회 중 삭제는 `for-each` 안의 `set.remove(...)` 대신 `Iterator.remove()` 또는 `removeIf(...)`로 처리한다고 기억하면 초보자 실수를 가장 빨리 줄일 수 있다.
