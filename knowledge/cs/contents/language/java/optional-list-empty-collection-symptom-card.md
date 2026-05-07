---
schema_version: 3
title: Optional List Empty Collection Symptom Card
concept_id: language/optional-list-empty-collection-symptom-card
canonical: true
category: language
difficulty: beginner
doc_role: symptom_router
level: beginner
language: ko
source_priority: 92
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- optional
- collection
- null-handling
aliases:
- Optional List Empty Collection Symptom Card
- Optional<List<T>> vs empty collection
- Optional list beginner
- Optional collection absence
- empty list vs Optional list
- Optional<List> 빈 컬렉션 차이
symptoms:
- 여러 건 결과가 0개일 수 있다는 이유로 Optional<List<T>>를 반환해 바깥 Optional과 안쪽 List empty를 모두 확인하게 만들어
- Optional은 한 건의 없음이고 List Set Map은 0개 이상을 표현한다는 shape 차이를 구분하지 못해
- 목록 자체가 로드되지 않음과 로드됐지만 비어 있음의 차이가 정말 필요한데 상태 타입 대신 Optional<List<T>>에 의미를 숨겨
- 빈 컬렉션을 null과 비슷한 실패 상태로 오해해 정상적인 0개 결과를 예외 흐름으로 처리해
intents:
- troubleshooting
- comparison
- design
prerequisites:
- language/java-optional-basics
- language/java-collections-basics
- language/optional-collections-domain-null-handling-bridge
next_docs:
- language/optional-field-parameter-antipattern-card
- language/optional-boolean-double-absence-follow-up-card
- software-engineering/dto-vo-entity-basics
linked_paths:
- contents/language/java/java-optional-basics.md
- contents/language/java/optional-collections-domain-null-handling-bridge.md
- contents/language/java/java-collections-basics.md
- contents/language/java/optional-field-parameter-antipattern-card.md
- contents/software-engineering/dto-vo-entity-basics.md
confusable_with:
- language/optional-collections-domain-null-handling-bridge
- language/optional-field-parameter-antipattern-card
- language/optional-boolean-double-absence-follow-up-card
forbidden_neighbors: []
expected_queries:
- Optional<List<T>>보다 빈 List를 반환하는 게 더 좋은 경우를 beginner 기준으로 설명해줘
- Optional은 한 건의 없음이고 컬렉션은 0개 이상이라는 shape 차이를 알려줘
- Optional<List<T>>를 쓰면 바깥 Optional empty와 안쪽 List empty를 왜 둘 다 봐야 해서 헷갈려?
- 목록이 아직 로드 안 됨과 로드됐지만 비어 있음이 다르면 어떤 상태 타입을 고려해야 해?
- empty collection은 null이 아니라 정상적인 0개 결과라는 점을 예제로 보여줘
contextual_chunk_prefix: |
  이 문서는 Optional<List<T>>와 empty collection 혼동을 여러 건 결과의 0개와 한 건의 absence로 분리하는 beginner symptom router다.
  Optional List, empty collection, Optional collection, 0개 결과, absence shape 질문이 본 문서에 매핑된다.
---
# `Optional<List<T>>` vs 빈 컬렉션 증상 카드

> 한 줄 요약: 여러 건 결과에서 "0개"는 보통 빈 컬렉션이 이미 표현하므로, `Optional<List<T>>`는 "목록 자체가 없음"과 "목록이 비어 있음"을 한 번 더 감싸서 초보자 질문만 늘리기 쉽다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Java Optional 입문](./java-optional-basics.md)
- [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](./optional-collections-domain-null-handling-bridge.md)
- [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- [`Optional` 필드/파라미터 anti-pattern 30초 카드](./optional-field-parameter-antipattern-card.md)
- [DTO, VO, Entity 기초](../../software-engineering/dto-vo-entity-basics.md)

retrieval-anchor-keywords: optional list vs empty collection, optional list beginner, optional list 왜 안 쓰나, optional list empty list difference, empty collection java beginner, 빈 리스트 optional 차이, optional collection absence symptom, optional list 헷갈려요, optional set map list 언제 비우나, why optional list feels wrong, what is optional list vs empty list, beginner optional collection design, optional list 0개 데이터, optional list empty collection card

## 핵심 증상

초보자가 자주 하는 말은 비슷하다.

- "`없을 수도 있으면` `Optional<List<T>>`가 더 안전한 것 아닌가요?"
- "빈 리스트면 `null`이랑 뭐가 다른가요?"
- "`Optional`도 보고 `isEmpty()`도 봐야 해서 더 헷갈려요"

이때 먼저 잘라야 할 질문은 하나다.

- 지금 표현하려는 것이 `한 건의 없음`인가
- 아니면 `여러 건 결과가 0개`인가

여러 건 결과라면, 컬렉션은 이미 "0개"를 자기 타입 안에서 표현한다. 그래서 beginner 단계에서는 `Optional<List<T>>`보다 `List<T>`와 빈 리스트가 보통 더 직접적이다.

## 먼저 잡는 멘탈 모델

초보자용으로는 아래 두 줄이면 충분하다.

- `Optional<T>`는 한 칸짜리 상자다. 값이 0개 또는 1개다.
- `List<T>`, `Set<T>`, `Map<K, V>`는 여러 칸짜리 상자다. 원소가 0개 이상이다.

즉 `List<T>`가 비어 있다는 것은 "상자가 있는데 안에 0개가 들어 있다"는 뜻이다. 이것만으로 충분한 상황이 대부분이다.

반면 `Optional<List<T>>`는 질문을 두 번 만들기 쉽다.

- 바깥 `Optional`이 비어 있나
- 안쪽 `List`가 비어 있나

그래서 한 줄로 외우면 이렇다.

> 여러 건의 `0개`는 빈 컬렉션, "목록 자체가 왜 없나"까지 따져야 하면 별도 상태 타입이다.

## 한눈에 보기

| 지금 코드가 말하려는 것 | 첫 선택 | 왜 이쪽이 더 읽기 쉬운가 |
|---|---|---|
| 회원 한 명을 찾았는데 없을 수도 있다 | `Optional<Member>` | 단건 결과의 있음/없음만 말하면 된다 |
| 주문 항목이 하나도 없을 수 있다 | `List<OrderLine>` + 빈 리스트 | 여러 건의 `0개`는 컬렉션이 이미 표현한다 |
| 태그 집합이 비어 있을 수 있다 | `Set<String>` + 빈 집합 | 중복 없는 여러 건 결과다 |
| 설정 테이블이 아직 로드 안 됨 / 로드했지만 비어 있음이 다르다 | 상태 타입 | "왜 비어 있는지"를 이름으로 드러내야 한다 |

짧게 번역하면 이렇다.

- `Optional`은 한 건의 없음
- 빈 컬렉션은 여러 건의 0개
- 상태 타입은 없음의 이유

## 왜 `Optional<List<T>>`가 오히려 질문을 늘리나

`Optional<List<T>>`를 받으면 호출자는 보통 두 단계를 모두 확인하게 된다.

```java
Optional<List<Coupon>> coupons = findCoupons(memberId);

if (coupons.isPresent() && !coupons.get().isEmpty()) {
    ...
}
```

이 코드는 "쿠폰 목록이 있는가?"와 "쿠폰이 0개인가?"를 한 번에 섞는다.

그런데 대부분의 조회에서는 아래 질문 하나면 충분하다.

- 쿠폰이 몇 개인가

그래서 보통은 이렇게 줄이는 편이 낫다.

```java
List<Coupon> coupons = findCoupons(memberId);

if (coupons.isEmpty()) {
    ...
}
```

이쪽이 더 읽기 쉬운 이유는 단순하다.

- `isPresent()`와 `isEmpty()`를 둘 다 보지 않아도 된다
- for-each, stream, `size()`를 바로 쓸 수 있다
- "여러 건 결과"라는 의도가 타입 이름에서 바로 보인다

## 같은 예제로 비교하기

회원의 장바구니 상품을 읽는다고 하자.

```java
List<CartItem> items = cartService.findItems(memberId);

if (items.isEmpty()) {
    System.out.println("장바구니 비어 있음");
}
```

이 코드는 자연스럽다. 장바구니는 원래 상품이 0개일 수 있기 때문이다.

반면 아래처럼 감싸면 absence 해석이 한 번 더 생긴다.

```java
Optional<List<CartItem>> items = cartService.findItems(memberId);
```

그러면 초보자 머릿속에 이런 질문이 따라온다.

- `empty`는 장바구니를 아직 안 만든 것인가
- 빈 리스트는 장바구니는 있는데 상품이 없는 것인가
- 이 둘을 정말 분리해야 하나

만약 이 차이가 진짜 업무 의미라면 `Optional<List<T>>`보다 상태 타입이 더 낫다.

```java
enum CartState {
    NOT_CREATED,
    READY
}

record CartItemsView(CartState state, List<CartItem> items) {
}
```

이렇게 두면 "목록이 없다"가 아니라 "왜 그런 상태인지"를 이름으로 보여 줄 수 있다.

## 흔한 오해와 첫 선택 순서

- "`Optional<List<T>>`가 더 안전하다"
  더 안전하다기보다 체크 포인트가 하나 더 생긴다.
- "빈 리스트는 `null`을 숨기는 임시방편이다"
  아니다. 여러 건 결과에서 빈 리스트는 정상 상태다.
- "비어 있는 이유를 나중에 설명하면 된다"
  이유가 중요하면 처음부터 상태 타입으로 올리는 편이 더 읽기 쉽다.

처음 고를 때는 아래 순서가 안전하다.

1. 결과가 한 건인지 여러 건인지 먼저 본다.
2. 여러 건이면 `List`/`Set`/`Map`이 스스로 `0개`를 표현하는지 본다.
3. "아직 로드 안 됨", "권한 없어 숨김"처럼 이유가 중요하면 `Optional<List<T>>` 대신 상태 타입을 검토한다.

## 더 깊이 가려면

- `Optional`의 큰 그림부터 다시 보고 싶으면 [Java Optional 입문](./java-optional-basics.md)
- 단건/다건/상태 타입 분기 전체를 보고 싶으면 [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](./optional-collections-domain-null-handling-bridge.md)
- `List`/`Set`/`Map` 기본 성격이 먼저 약하면 [Java 컬렉션 프레임워크 입문](./java-collections-basics.md)
- `Optional`을 API 여기저기 감싸는 습관 자체를 짧게 정리하면 [`Optional` 필드/파라미터 anti-pattern 30초 카드](./optional-field-parameter-antipattern-card.md)
- API 경계에서 "필드 미전달"과 "빈 목록"을 어떻게 나눌지 보려면 [DTO, VO, Entity 기초](../../software-engineering/dto-vo-entity-basics.md)

## 한 줄 정리

`Optional<List<T>>`보다 먼저 "여러 건의 0개는 빈 컬렉션"을 떠올리고, 목록 자체의 상태 의미가 중요할 때만 `Optional`이 아니라 별도 상태 타입을 검토하면 된다.
