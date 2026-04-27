# Stream `groupingBy` Result Shape Primer

> 한 줄 요약: `Collectors.groupingBy(...)`는 stream 요소를 key별로 "버킷에 모으는" collector라서, 가장 기본형 결과를 `Map<K, List<V>>`로 읽는 감각을 먼저 잡으면 이후 `counting()`이나 `mapping()` 변형도 훨씬 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java 스트림과 람다 입문](./java-stream-lambda-basics.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [Map Value-Shape Drill](./map-value-shape-drill.md)
- [`Collectors.toMap(...)` Duplicate Key Primer](./collectors-tomap-duplicate-key-primer.md)
- [Map Iteration Patterns Cheat Sheet](./map-iteration-patterns-cheat-sheet.md)

retrieval-anchor-keywords: language-java-00100, java groupingby beginner, stream groupingby result shape, collectors.groupingby map list primer, java group by list map, groupingby output how to read, java stream group bucket mental model, groupingby counting mapping beginner, java grouped pipeline result transform, stream groupingby vs tomap beginner, 자바 groupingby 기초, 자바 stream groupingby 결과 모양, 자바 groupingby map list, 자바 그룹핑 결과 읽기, 자바 groupingby counting mapping

## 먼저 잡는 멘탈 모델

`groupingBy(...)`는 "같은 key끼리 한 칸에 모아 담기"다.

- key를 정한다
- 같은 key가 나온 요소들을 같은 칸에 넣는다
- 그래서 기본형 결과는 보통 `Map<K, List<T>>`처럼 읽힌다

초보자 기준으로는 이렇게 읽으면 충분하다.

> `groupingBy`는 "하나의 key에 속한 요소 여러 개"를 `List`로 모아 주는 collector다.

## 가장 기본 결과 모양

주문 목록을 상태별로 묶는다고 하자.

```java
record Order(long id, String status, String customerName, int amount) {}

List<Order> orders = List.of(
        new Order(1L, "PAID", "Kim", 12000),
        new Order(2L, "READY", "Lee", 8000),
        new Order(3L, "PAID", "Park", 15000)
);
```

```java
Map<String, List<Order>> ordersByStatus = orders.stream()
        .collect(Collectors.groupingBy(Order::status));
```

이 결과는 이렇게 읽는다.

- `"PAID"` key 아래에 `Order` 두 개가 들어 있다
- `"READY"` key 아래에 `Order` 한 개가 들어 있다

즉 결과 모양은 대략 이런 느낌이다.

```text
{
    "PAID": [Order(1, ...), Order(3, ...)],
    "READY": [Order(2, ...)]
}
```

핵심은 `Map<String, List<Order>>`를 보고 "`status -> 그 상태에 속한 주문들`"이라고 문장으로 읽는 것이다.

## 왜 `List`가 붙는가

`toMap(...)`은 보통 "key 하나에 value 하나"를 만든다.
반면 `groupingBy(...)`는 "같은 key의 요소를 여러 개 유지"하는 쪽이 목적이다.

| collector | 기본으로 만드는 모양 | 어울리는 질문 |
|---|---|---|
| `toMap(...)` | `Map<K, V>` | "최종 값 하나만 두고 싶다" |
| `groupingBy(...)` | `Map<K, List<T>>` | "같은 key의 요소들을 전부 묶어 보고 싶다" |

예를 들어 `"PAID"` 주문이 여러 개일 수 있는데 하나만 남기면 정보가 사라진다.
이럴 때는 `toMap(...)`보다 `groupingBy(...)`가 구조적으로 더 맞다.

## 초보자가 결과를 읽는 순서

`Map<String, List<Order>>`를 보면 한 번에 다 해석하려 하지 말고 순서를 고정하면 쉽다.

1. `Map<...>` 이므로 "key로 찾는 구조"라고 본다.
2. key 타입 `String`을 보고 "무엇을 기준으로 묶었나"를 본다.
3. value 타입 `List<Order>`를 보고 "한 key 아래 주문 여러 개가 들어가는구나"를 본다.

즉

```java
Map<String, List<Order>>
```

는

- `String`: 묶는 기준
- `List<Order>`: 그 기준에 속한 원본 요소 묶음

으로 읽으면 된다.

## 가장 흔한 변형 1: "묶은 다음 개수만 보고 싶다"

처음에는 `Map<K, List<T>>`를 만든 뒤 `list.size()`를 떠올리기 쉽다.
그런데 collector 단계에서 바로 개수로 만들 수도 있다.

```java
Map<String, Long> countByStatus = orders.stream()
        .collect(Collectors.groupingBy(
                Order::status,
                Collectors.counting()
        ));
```

이제 결과 모양은 `Map<String, Long>`이다.

- `"PAID" -> 2`
- `"READY" -> 1`

즉 `groupingBy`가 항상 `Map<K, List<T>>`만 만드는 것은 아니고,
**기본형은 리스트 묶음이고 downstream collector를 붙이면 value 모양이 바뀐다.**

## 가장 흔한 변형 2: "원본 전체 말고 필요한 값만 모으고 싶다"

상태별로 주문 전체가 아니라 고객 이름만 묶고 싶다면 `mapping(...)`을 같이 쓴다.

```java
Map<String, List<String>> customerNamesByStatus = orders.stream()
        .collect(Collectors.groupingBy(
                Order::status,
                Collectors.mapping(Order::customerName, Collectors.toList())
        ));
```

이 결과는 이렇게 읽는다.

- `"PAID" -> ["Kim", "Park"]`
- `"READY" -> ["Lee"]`

즉

- 묶는 기준은 여전히 `status`
- 각 칸에 넣는 값은 `Order` 전체가 아니라 `customerName`

이다.

## 기본형과 변형을 한 표로 보기

| 코드 의도 | 결과 타입 | 읽는 문장 |
|---|---|---|
| `groupingBy(Order::status)` | `Map<String, List<Order>>` | 상태별 주문 목록 |
| `groupingBy(Order::status, Collectors.counting())` | `Map<String, Long>` | 상태별 주문 개수 |
| `groupingBy(Order::status, Collectors.mapping(Order::customerName, Collectors.toList()))` | `Map<String, List<String>>` | 상태별 고객 이름 목록 |

초보자에게 중요한 포인트는 "결과 타입이 collector 의도를 그대로 말해 준다"는 점이다.

## grouped 결과를 파이프라인 밖에서 다루는 법

묶은 뒤에는 보통 `entrySet()`으로 읽는다.

```java
for (Map.Entry<String, List<Order>> entry : ordersByStatus.entrySet()) {
    String status = entry.getKey();
    List<Order> groupedOrders = entry.getValue();

    System.out.println(status + " -> " + groupedOrders.size());
}
```

여기서 읽는 순서는 단순하다.

- `getKey()`는 그룹 이름
- `getValue()`는 그 그룹에 속한 요소들

초보자는 `List<Order>`를 다시 한 번 별도 리스트처럼 다룬다고 생각하면 된다.

## 자주 하는 오해

- `groupingBy(...)` 결과가 항상 `Map<K, T>`라고 착각한다
- key 하나에 요소가 하나만 들어갈 거라고 넘겨짚고 `List`를 잊는다
- 사실은 "개수"만 필요했는데 먼저 `Map<K, List<T>>`를 만든 뒤 복잡하게 다시 센다
- 사실은 "이름 목록"만 필요했는데 원본 객체 전체를 계속 들고 있는 구조를 만든다
- `toMap(...)` 예외를 피하려고 `groupingBy(...)`를 쓰면서도, 정작 결과를 `List`로 읽지 못해 다시 막힌다

## 헷갈릴 때 빠른 판단표

| 지금 필요한 것 | 먼저 떠올릴 표현 |
|---|---|
| 같은 key의 원본 요소 전체 묶음 | `groupingBy(key)` |
| 같은 key의 개수 | `groupingBy(key, Collectors.counting())` |
| 같은 key의 특정 필드 목록 | `groupingBy(key, Collectors.mapping(valueMapper, Collectors.toList()))` |
| 같은 key의 최종 값 하나 | `toMap(...)` 또는 집계 규칙 검토 |

## `groupingBy`를 볼 때 스스로에게 던질 질문

- key는 무엇인가
- value는 원본 요소 전체인가, 특정 필드인가
- 한 key 아래 여러 개를 유지하는 것이 맞는가
- 내가 정말 필요한 결과는 `List`, `개수`, `합계`, `이름 목록` 중 무엇인가

이 네 가지만 확인해도 grouped pipeline 읽기가 많이 쉬워진다.

## 다음 단계

- `stream` 파이프라인 자체가 아직 낯설면 [Java 스트림과 람다 입문](./java-stream-lambda-basics.md)
- `groupingBy`와 `toMap` 차이가 계속 섞이면 [`Collectors.toMap(...)` Duplicate Key Primer](./collectors-tomap-duplicate-key-primer.md)
- `Map<K, List<V>>` 같은 value 모양 해석이 약하면 [Map Value-Shape Drill](./map-value-shape-drill.md)
- grouped 결과를 순회하며 후처리하는 패턴은 [Map Iteration Patterns Cheat Sheet](./map-iteration-patterns-cheat-sheet.md)

## 한 줄 정리

`groupingBy(...)`는 기본적으로 "key별 원본 요소 리스트"를 만드는 collector이고, 그 기본 모양을 `Map<K, List<T>>`로 읽을 수 있어야 `counting()`이나 `mapping()`으로 바뀐 결과 타입도 자연스럽게 따라갈 수 있다.
