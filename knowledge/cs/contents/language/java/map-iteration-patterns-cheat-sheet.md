# Map Iteration Patterns Cheat Sheet

> 한 줄 요약: `Map` 반복의 기본값은 `entrySet()`이다. key/value가 둘 다 필요하면 한 번에 꺼내고, 필요한 쪽만 볼 때만 `keySet()` 또는 `values()`를 고른다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [Iterable vs Collection vs Map 브리지 입문](./iterable-collection-map-iteration-bridge.md)
- [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md)
- [Java 스트림과 람다 입문](./java-stream-lambda-basics.md)
- [Spring 런타임 전략 선택과 `@Qualifier` 경계 분리: `Map<String, Bean>` Router vs Injection-time 선택](../../spring/spring-runtime-strategy-router-vs-qualifier-boundaries.md)

retrieval-anchor-keywords: java map iteration cheat sheet, map entryset keyset values 차이, entryset vs keyset performance, java map for each beginner, map 반복문 기초, entryset do dont 예시, keyset values 언제 쓰나, map key value iteration beginner, 처음 배우는데 map 순회, hashmap 반복 패턴, map 왜 entryset 기본인가요, map get in loop smell, keyset get null confusion, containskey getordefault iteration bridge

## 먼저 잡는 멘탈 모델

`Map<K, V>`는 `K -> V` 쌍의 모음이다.
반복할 때는 "쌍을 볼 건지", "key만 볼 건지", "value만 볼 건지"를 먼저 정한다.

- key와 value 둘 다 필요함: `entrySet()`
- key만 필요함: `keySet()`
- value만 필요함: `values()`

초보자 기본값은 `entrySet()`이다.

## 10초 선택표

| 지금 필요한 것 | 선택 API | 이유 |
|---|---|---|
| key와 value 둘 다 | `entrySet()` | 한 번 순회로 둘 다 가져옴 |
| key만 | `keySet()` | key 집합만 직접 순회 |
| value만 | `values()` | value 컬렉션만 직접 순회 |

## Do / Don't 핵심 예시

### 1) key와 value 둘 다 쓸 때

```java
// Do: entrySet() 한 번 순회
for (Map.Entry<String, Integer> entry : scores.entrySet()) {
    String user = entry.getKey();
    Integer score = entry.getValue();
    System.out.println(user + ": " + score);
}

// Don't: keySet() 순회 + map.get(key) 재조회
for (String user : scores.keySet()) {
    Integer score = scores.get(user); // 매번 재조회
    System.out.println(user + ": " + score);
}
```

`Don't` 코드가 항상 틀린 건 아니지만, key/value를 둘 다 쓰는 상황에서는 `entrySet()`이 더 직접적이고 의도가 선명하다.

### 2) key만 필요할 때

```java
// Do: keySet() 사용
for (String user : scores.keySet()) {
    System.out.println(user);
}

// Don't: value까지 꺼내고 버리기
for (Map.Entry<String, Integer> entry : scores.entrySet()) {
    System.out.println(entry.getKey());
    // value는 안 씀
}
```

### 3) value만 필요할 때

```java
// Do: values() 사용
for (Integer score : scores.values()) {
    System.out.println(score);
}

// Don't: key까지 꺼내고 버리기
for (Map.Entry<String, Integer> entry : scores.entrySet()) {
    System.out.println(entry.getValue());
    // key는 안 씀
}
```

## `forEach` 버전도 같은 규칙

```java
// key + value
scores.forEach((user, score) -> System.out.println(user + ": " + score));

// key only
scores.keySet().forEach(System.out::println);

// value only
scores.values().forEach(System.out::println);
```

문법이 달라도 선택 기준은 동일하다.

## 흔한 혼동 4가지

- "`Map`도 for-each 바로 되나요?"
  `Map` 자체는 `Iterable`이 아니다. `entrySet()`/`keySet()`/`values()` 중 하나를 꺼내서 순회해야 한다.
- "`keySet()` + `get()`이 무조건 나쁜가요?"
  무조건 나쁜 건 아니다. 다만 key/value를 둘 다 쓸 때는 `entrySet()`이 보통 더 읽기 쉽고 실수 여지가 적다.
- "`values()`로 돌 때 key도 알 수 있나요?"
  직접은 못 얻는다. key가 필요하면 `entrySet()`으로 바꿔야 한다.
- "처음엔 뭘 기본으로 잡죠?"
  고민되면 `entrySet()`부터 시작하고, key-only/value-only가 명확할 때 좁혀 가면 된다.

헷갈리면 이 한 문장으로 다시 돌아오면 된다.

- 둘 다 쓰면 `entrySet()`
- 하나만 쓰면 그 뷰만 꺼낸다

## 빠른 기억 문장

- key+value: `entrySet()`
- key only: `keySet()`
- value only: `values()`

"둘 다 쓰면 `entrySet()`"만 확실히 기억하면 첫 시도 실패를 크게 줄일 수 있다.

## 다음에 어디로 이어서 읽을까

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| "`Map` 자체가 왜 for-each가 안 되죠?" | [Iterable vs Collection vs Map 브리지 입문](./iterable-collection-map-iteration-bridge.md) |
| "`get()`이 `null`일 때 반복 중 판단을 어떻게 하죠?" | [Map `get()` null 의미와 `containsKey()`/`getOrDefault()` 선택 프라이머](./map-get-null-containskey-getordefault-primer.md) |
| "람다 `forEach`와 일반 반복문은 언제 바꾸죠?" | [Java 스트림과 람다 입문](./java-stream-lambda-basics.md) |
| "Spring의 `Map<String, Bean>` 반복은 이 규칙과 어떻게 이어지죠?" | [Spring 런타임 전략 선택과 `@Qualifier` 경계 분리: `Map<String, Bean>` Router vs Injection-time 선택](../../spring/spring-runtime-strategy-router-vs-qualifier-boundaries.md) |

## 한 줄 정리

`Map` 반복의 기본값은 `entrySet()`이다. key/value가 둘 다 필요하면 한 번에 꺼내고, 필요한 쪽만 볼 때만 `keySet()` 또는 `values()`를 고른다.
