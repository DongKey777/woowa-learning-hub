---
schema_version: 3
title: Records Sealed Pattern Matching
concept_id: language/records-sealed-pattern-matching
canonical: true
category: language
difficulty: beginner
doc_role: primer
level: beginner
language: ko
source_priority: 93
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- record
- sealed
- pattern-matching
aliases:
- Java record sealed class pattern matching 입문
- records sealed pattern matching
- record sealed class beginner
- pattern matching instanceof switch
- DTO value object sealed hierarchy
- 자바 record sealed pattern matching
symptoms:
- record, sealed, pattern matching을 코드를 짧게 쓰는 문법으로만 외워 값 상자, 허용된 타입 목록, 안전한 분기라는 문제 분리를 놓쳐
- record를 DTO, value object, entity와 같은 층위로 섞어 식별자와 생명주기가 있는 타입에도 무조건 적용하려 해
- sealed hierarchy와 pattern matching switch를 쓰면서 variant 추가와 exhaustive branch가 설계와 호환성에 미치는 영향을 고려하지 않아
intents:
- definition
- comparison
- design
prerequisites:
- language/java-language-basics
- language/object-oriented-core-principles
next_docs:
- language/record-value-object-equality-basics
- language/sealed-interfaces-exhaustive-switch-design
- language/record-sealed-hierarchy-evolution-pattern-matching-compatibility
linked_paths:
- contents/language/java/java-language-basics.md
- contents/language/java/object-oriented-core-principles.md
- contents/language/java/record-value-object-equality-basics.md
- contents/language/java/sealed-interfaces-exhaustive-switch-design.md
- contents/language/java/record-sealed-hierarchy-evolution-pattern-matching-compatibility.md
- contents/software-engineering/dto-vo-entity-basics.md
confusable_with:
- language/record-value-object-equality-basics
- language/sealed-interfaces-exhaustive-switch-design
- language/record-sealed-hierarchy-evolution-pattern-matching-compatibility
forbidden_neighbors: []
expected_queries:
- Java record sealed class pattern matching을 beginner 기준으로 값 상자 허용 타입 목록 안전한 분기로 설명해줘
- record는 DTO나 value object에 언제 잘 맞고 entity와는 왜 구분해야 해?
- sealed class는 가능한 상태가 몇 개로 고정된 결과 타입에서 왜 유용해?
- pattern matching은 instanceof와 casting을 어떻게 줄여 주는지 예제로 알려줘
- record sealed pattern matching 다음에 equality exhaustive switch compatibility를 어떤 순서로 읽으면 좋아?
contextual_chunk_prefix: |
  이 문서는 modern Java의 record, sealed class, pattern matching을 값 상자, 제한된 hierarchy, 안전한 type branch로 소개하는 beginner primer다.
  record, sealed class, pattern matching, DTO, value object, exhaustive switch 질문이 본 문서에 매핑된다.
---
# Java record, sealed class, pattern matching 입문

> 한 줄 요약: `record`, `sealed`, `pattern matching`은 "코드를 짧게 쓰는 문법"이 아니라 `값 상자`, `허용된 타입 목록`, `안전한 분기`를 beginner 관점에서 분리해 주는 입문 묶음이다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)
- [DTO, VO, Entity 기초](../../software-engineering/dto-vo-entity-basics.md)


retrieval-anchor-keywords: java record sealed class pattern matching beginner, java modern syntax primer, record sealed class 뭐예요, record sealed pattern matching 큰 그림, 처음 배우는데 record sealed class, 처음 배우는데 pattern matching, record는 언제 쓰나요, sealed class는 왜 쓰나요, pattern matching 왜 쓰나요, record dto value object beginner, sealed hierarchy beginner, instanceof 캐스팅 줄이기, switch 분기 타입 안전, java record sealed 차이, record sealed pattern matching 헷갈려요
> 관련 문서:
> - [자바 언어의 구조와 기본 문법](./java-language-basics.md)
> - [객체지향 핵심 원리](./object-oriented-core-principles.md)
> - [Record and Value Object Equality](./record-value-object-equality-basics.md)
> - [Sealed Interfaces and Exhaustive Switch Design](./sealed-interfaces-exhaustive-switch-design.md)
> - [Record/Sealed Hierarchy Evolution and Pattern Matching Compatibility](./record-sealed-hierarchy-evolution-pattern-matching-compatibility.md)
> - [DTO, VO, Entity 기초](../../software-engineering/dto-vo-entity-basics.md)

> retrieval-anchor-keywords: record, sealed class, pattern matching, DTO, value object, permits, exhaustive switch, hierarchy evolution, variant compatibility, record equals hashCode, record component equality, record shallow immutability, record dto 차이, sealed class exhaustive switch, pattern matching instanceof switch

## 핵심 개념

`record`, `sealed class`, `pattern matching`은 서로 연결된 현대 Java 기능이다.

왜 중요한가:

- DTO와 값 객체를 덜 장황하게 표현할 수 있다
- 상속 구조를 통제할 수 있다
- 조건 분기 코드를 더 읽기 쉽게 만들 수 있다

이 문서의 target query shape는 아래처럼 "처음 배우는 질문"이다.

- `record가 뭐예요?`
- `sealed class는 왜 써요?`
- `pattern matching은 instanceof랑 뭐가 달라요?`
- `DTO나 value object에 record를 써도 되나요?`

## 30초 멘탈 모델

처음에는 세 기능을 하나의 패키지로 외우기보다, 각자 푸는 문제를 분리해서 보면 된다.

| 기능 | 가장 짧은 기억법 | beginner가 자주 묻는 말 |
|---|---|---|
| `record` | 값을 담는 상자를 짧게 선언 | `DTO 만들 때 getter/equals를 왜 계속 써요?` |
| `sealed` | 자식 타입 목록을 잠그는 문법 | `이 상태는 Success/Failure 둘뿐인데 아무 클래스나 구현해도 되나요?` |
| `pattern matching` | 타입 검사와 꺼내기를 같이 쓰는 문법 | `instanceof 하고 캐스팅 또 해야 하나요?` |

한 줄로 줄이면 이렇다.

- `record`는 "값 상자"
- `sealed`는 "허용된 자식 목록"
- `pattern matching`은 "타입 확인 뒤 바로 꺼내기"

## 깊이 들어가기

### 1. record

record는 데이터 전달용 불변 객체를 짧게 선언하는 방식이다.
특히 beginner가 처음 만나는 `DTO`, `value object` 문맥에서 잘 맞는다.

### 2. sealed class

sealed class는 상속 가능한 타입을 제한한다.
도메인 상태가 제한적일 때 유용하다.

### 3. pattern matching

타입 체크와 캐스팅을 줄여 분기 코드를 단순화한다.

## 어디에 먼저 쓰는지 quick map

| 지금 만들려는 것 | 먼저 떠올릴 기능 | 이유 |
|---|---|---|
| 요청/응답 DTO, 값 객체 | `record` | 필드 묶음과 값 동등성을 짧게 표현하기 쉽다 |
| 성공/실패처럼 가능한 상태가 몇 개로 고정된 결과 타입 | `sealed` | 허용된 하위 타입만 열어 둘 수 있다 |
| `if (x instanceof Foo)` 뒤 캐스팅 반복, 타입별 `switch` 분기 | `pattern matching` | 검사와 사용을 같이 적어 분기를 덜 지저분하게 만든다 |

처음 배우는데 `record`와 `Entity`를 같은 층위로 보면 금방 헷갈린다.
`record`는 값 중심 타입에 더 잘 맞고, 식별자와 생명주기가 중요한 `Entity`는 [DTO, VO, Entity 기초](../../software-engineering/dto-vo-entity-basics.md)로 이어서 구분하는 편이 안전하다.

## 실전 시나리오

### 시나리오 1: 이벤트 타입이 몇 개로 고정돼 있다

sealed class로 타입 폭발을 막을 수 있다.

### 시나리오 2: 단순 DTO가 너무 장황하다

record로 생성자/getter/equals/hashCode를 덜 쓸 수 있다.

## 코드로 보기

```java
public sealed interface PaymentResult permits Success, Failure {}

public record Success(String transactionId) implements PaymentResult {}
public record Failure(String reason) implements PaymentResult {}
```

```java
switch (result) {
    case Success s -> handleSuccess(s.transactionId());
    case Failure f -> handleFailure(f.reason());
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|------|------|------|-------------|
| record | 짧고 명확 | mutable 모델엔 부적합 | 값 객체/DTO |
| sealed | 타입 안전 | 구조 변경 비용 | 상태가 제한적일 때 |
| pattern matching | 가독성 좋음 | 버전/문법 의존 | 분기 로직 단순화 |

## 흔한 헷갈림

- `record = 아무 클래스나 줄여 쓰는 문법`은 아니다.
  값 의미가 분명한 DTO/VO에 먼저 붙이는 편이 안전하다.
- `sealed = 무조건 복잡한 설계`도 아니다.
  `Success/Failure`처럼 가능한 경우가 몇 개 안 될 때 오히려 초보자에게 더 읽기 쉽다.
- `pattern matching = 새 문법 장식`도 아니다.
  `instanceof` 검사 후 캐스팅 반복을 줄여서 분기 의도를 더 빨리 보이게 한다.

## 꼬리질문

> Q: record는 언제 쓰면 안 되는가?
> 의도: 불변성과 도메인 모델 구분 여부 확인
> 핵심: mutable aggregate에는 부적절하다.

> Q: sealed class가 왜 유용한가?
> 의도: 상속 통제의 의미 이해 여부 확인
> 핵심: 허용된 하위 타입만 관리할 수 있다.

## 한 줄 정리

record, sealed, pattern matching은 Java를 더 짧게 쓰게 하는 기능이 아니라, 도메인 타입을 더 안전하게 표현하게 해주는 기능이다.
