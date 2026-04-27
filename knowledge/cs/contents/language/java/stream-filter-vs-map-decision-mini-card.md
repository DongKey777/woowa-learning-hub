# `filter` vs `map` 결정 미니 카드

> 한 줄 요약: `filter`는 "남길지 버릴지"를 고르고, `map`은 "남긴 값을 무엇으로 바꿀지"를 정한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Java 스트림과 람다 입문](./java-stream-lambda-basics.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [`Stream.toList()` vs `Collectors.toList()` Result Mutability Bridge](./stream-tolist-vs-collectors-tolist-mutability-bridge.md)
- [Spring MVC 컨트롤러 기초](../../spring/spring-mvc-controller-basics.md)
- [language 카테고리 인덱스](../README.md)

retrieval-anchor-keywords: filter vs map basics, java filter map difference, stream filter map beginner, filter map 언제 쓰는지, filter map 뭐가 다른가요, stream 조건 변환 차이, beginner stream decision card, for문 stream 변환 basics, filter 는 남기기, map 은 바꾸기, stream 처음 배우는데 filter map, what is filter vs map

## 핵심 개념

초보자는 둘 다 "스트림에서 뭔가 처리하는 메서드"처럼 보여서 자주 섞는다. 하지만 질문이 다르다.

- `filter`: 이 요소를 결과에 남길까?
- `map`: 남긴 요소를 어떤 값으로 바꿀까?

먼저 `남길지`를 고르고, 그다음 `무엇으로 바꿀지`를 적는다고 보면 된다.

## 한눈에 보기

| 메서드 | 내가 답하는 질문 | 람다 반환값 | 결과 개수 감각 |
| --- | --- | --- | --- |
| `filter(...)` | "이 요소를 남길까?" | `boolean` | 줄어들거나 그대로 |
| `map(...)` | "이 요소를 무엇으로 바꿀까?" | 새로운 값 | 보통 입력 개수와 같다 |

짧게 외우면 이렇다.

- `filter` = 통과 검사
- `map` = 값 변환

## 10초 결정 순서

문장을 먼저 읽고 동사를 찾으면 빠르다.

| 문제 문장에 이런 말이 있으면 | 먼저 떠올릴 것 |
| --- | --- |
| "조건에 맞는 것만", "OO만 골라서" | `filter` |
| "이름만 뽑아서", "DTO로 바꿔서", "대문자로 바꿔서" | `map` |
| "조건에 맞는 것만 골라서 이름으로 바꿔라" | `filter` 다음 `map` |

즉 "골라라"는 `filter`, "바꿔라"는 `map`이다.

## 같은 예제로 비교하기

문제: 주문 목록에서 `PAID` 상태만 골라서 고객 이름만 대문자로 뽑는다.

```java
List<String> names = orders.stream()
    .filter(order -> order.getStatus() == OrderStatus.PAID)
    .map(order -> order.getCustomerName().toUpperCase())
    .toList();
```

한 줄씩 읽으면:

- `filter(...)`: 결제 완료 주문만 남긴다
- `map(...)`: 남은 주문을 고객 이름 문자열로 바꾼다

여기서 `filter`를 빼면 취소 주문도 들어오고, `map`을 빼면 결과가 `String` 목록이 아니라 `Order` 목록으로 남는다.

## 흔한 혼동

- `filter` 안에서 값을 바꾸려고 하지 않는다. `filter`는 `true/false`를 돌려주는 자리다.
- `map`은 조건 검사 자리가 아니다. `map`에서 `boolean`을 만들면 `List<Boolean>`이 생길 뿐이다.
- `map`이 항상 타입을 바꿔야 하는 것은 아니다. `String -> String` 대문자 변환도 `map`이다.
- 초보자에게 가장 흔한 모양은 `filter -> map -> toList()`다. 순서가 뒤집히면 읽기도 어려워지고 중간 타입도 바뀐다.

## 더 읽을 것

- 스트림 파이프라인 전체를 `for` 루프와 연결해서 보고 싶다면 [Java 스트림과 람다 입문](./java-stream-lambda-basics.md)
- `List`/`Set`/`Map`과 함께 "무엇을 모으는지"부터 다시 잡고 싶다면 [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- 스트림 결과를 받은 뒤 수정 가능한 리스트가 필요한지까지 이어서 보려면 [`Stream.toList()` vs `Collectors.toList()` Result Mutability Bridge](./stream-tolist-vs-collectors-tolist-mutability-bridge.md)
- 컨트롤러에서 조회 결과를 DTO나 응답 값으로 바꾸는 감각을 Spring 쪽에서 이어서 보려면 [Spring MVC 컨트롤러 기초](../../spring/spring-mvc-controller-basics.md)

## 한 줄 정리

`filter`는 조건으로 남길 요소를 고르고, `map`은 남긴 요소를 원하는 값으로 바꾼다.
