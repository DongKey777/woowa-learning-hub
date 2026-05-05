---
schema_version: 3
title: Value Object Invariants, Canonicalization, and Boundary Design
concept_id: language/value-object-invariants-canonicalization-boundary-design
canonical: true
category: language
difficulty: advanced
doc_role: primer
level: advanced
language: mixed
source_priority: 90
mission_ids:
- missions/roomescape
- missions/lotto
- missions/shopping-cart
review_feedback_tags:
- value-object-invariant-leak
- canonicalization-missing
- serialization-boundary-invariant
aliases:
- value object invariant boundary
- canonicalization equality boundary
- value object normalization design
- domain primitive invariant design
- value object serialization invariant
- 값객체 불변식 경계 설계
- canonicalization 왜 필요한가
- 값 의미 equality 경계
- 직렬화 이후 값객체 규칙
- advanced value object design
symptoms:
- 값 객체로 감쌌는데도 trim이나 scale 규칙이 호출자마다 달라져서 의미가 흔들려
- 같은 값처럼 보여도 equals나 캐시 키 결과가 달라져서 canonicalization이 왜 필요한지 모르겠어
- 역직렬화 뒤에 invalid value object가 생기는데 경계를 어디서 잠가야 할지 막혀
intents:
- definition
prerequisites:
- language/money-value-object-basics
- language/record-value-object-equality-basics
- language/immutable-objects-and-defensive-copying
next_docs:
- language/bigdecimal-money-equality-rounding-serialization-pitfalls
- language/locale-root-case-mapping-unicode-normalization
- language/record-serialization-evolution
linked_paths:
- contents/language/java/immutable-objects-and-defensive-copying.md
- contents/language/java/money-value-object-basics.md
- contents/language/java/record-value-object-equality-basics.md
- contents/language/java/bigdecimal-money-equality-rounding-serialization-pitfalls.md
- contents/language/java/locale-root-case-mapping-unicode-normalization.md
- contents/language/java/record-serialization-evolution.md
- contents/language/java/java-immutable-object-basics.md
confusable_with:
- language/money-value-object-basics
- language/record-value-object-equality-basics
- language/immutable-objects-and-defensive-copying
forbidden_neighbors:
- contents/language/java/immutable-objects-and-defensive-copying.md
expected_queries:
- 값 객체를 만들었는데도 비교 기준과 직렬화 경계가 흔들릴 때 무엇을 점검해야 해
- canonicalization이 equals hashCode 계약의 일부라는 말을 자바 예제로 이해하고 싶어
- trim lower-case scale 정책을 생성 시점에 잠그는 고급 value object 설계 문서를 찾고 있어
- invalid state가 역직렬화로 다시 들어오는 문제를 value object 관점에서 설명해줘
- 캐시 키와 중복 제거가 깨질 때 값 객체 경계를 어떻게 다시 잡아야 하는지 알고 싶어
- 불변 객체와 진짜 value object의 차이를 invariant 관점으로 정리한 글이 필요해
contextual_chunk_prefix: 이 문서는 Java 학습자가 value object를 단순 불변 DTO가 아니라
  생성 시점 불변식과 canonicalization을 잠그는 도메인 경계로 이해하도록 돕는 advanced
  primer다. 비교 기준, 캐시 키, 중복 제거, 직렬화 이후에도 같은 의미를 유지하는 설계와
  raw String이나 BigDecimal을 언제 값 객체로 올릴지 같은 질문이 이 문서의 핵심 개념에
  매핑된다.
---
# Value Object Invariants, Canonicalization, and Boundary Design

> 한 줄 요약: 좋은 value object는 "immutable DTO"보다 더 많다. 생성 시점에 invariant를 잠그고, 비교 기준을 canonicalize하고, 직렬화/역직렬화 경계에서도 같은 의미를 유지해야 캐시 키, 중복 제거, 금액/시간/식별자 모델이 흔들리지 않는다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)
> - [Money Value Object Basics](./money-value-object-basics.md)
> - [Java `equals`, `hashCode`, `Comparable` 계약](../java-equals-hashcode-comparable-contracts.md)
> - [`BigDecimal` Money Equality, Rounding, and Serialization Pitfalls](./bigdecimal-money-equality-rounding-serialization-pitfalls.md)
> - [`Locale.ROOT`, Case Mapping, and Unicode Normalization Pitfalls](./locale-root-case-mapping-unicode-normalization.md)
> - [Record Serialization Evolution](./record-serialization-evolution.md)

> retrieval-anchor-keywords: value object, domain primitive, invariant, canonicalization, normalization, equality boundary, immutability, factory method, validation, record value object, serialization invariant, domain model, boundary design

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

value object의 핵심은 세 가지다.

- identity보다 값 의미가 중요하다
- 생성 이후 invariant가 깨지지 않는다
- 같은 값을 같은 방식으로 표현한다

즉 value object는 필드 몇 개 묶은 클래스가 아니라,
"이 타입을 통과하면 그 이후엔 믿을 수 있다"는 경계다.

그래서 설계 질문도 바뀐다.

- 어떤 값이 유효한가
- 어떤 표현을 canonical form으로 삼을 것인가
- 비교와 직렬화에서 무엇을 같은 값으로 볼 것인가

## 깊이 들어가기

### 1. immutable과 valid는 다른 문제다

객체가 불변이어도 invalid state일 수 있다.

- 음수 금액
- trim되지 않은 식별자
- zone 없는 절대 시각
- scale이 섞인 금액 표현

즉 `final field`만으로는 부족하다.
생성 시점 validation과 canonicalization이 value object의 본질이다.

### 2. canonicalization은 equality contract의 일부다

겉보기엔 같은 값을 서로 다른 표현으로 허용하면 다음이 흔들린다.

- `equals`/`hashCode`
- 캐시 키
- 중복 제거
- idempotency 판단

예:

- 이메일의 display value와 비교 키
- 돈의 currency + scale
- 사용자명이 composed/decomposed Unicode로 들어오는 경우

canonicalization은 편의 로직이 아니라 value semantics를 고정하는 과정이다.

### 3. primitive obsession을 줄이면 경계가 선명해진다

`String`, `long`, `BigDecimal`을 그대로 노출하면 호출자가 규칙을 외워야 한다.
value object로 감싸면 규칙을 타입이 가진다.

예:

- `EmailAddress`
- `Money`
- `UserId`
- `Percent`
- `RetryLimit`

이렇게 되면 파라미터 순서 실수, 단위 착각, 비교 기준 누락이 줄어든다.

### 4. 원본 표현과 canonical 표현을 분리할 때가 있다

모든 값을 정규화해서 하나만 남기는 것이 항상 정답은 아니다.

- 사용자에게 보여줄 원본 문자열
- 비교와 인덱싱에 쓸 canonical key
- 외부 계약에 쓸 직렬화 형식

이 셋이 다를 수 있다.

예를 들어 사용자명은 display value를 보존하되,
canonical key는 `Locale.ROOT` + NFC로 따로 둘 수 있다.

### 5. 역직렬화 경계도 생성자 규칙을 통과해야 한다

value object의 invariant를 생성자에서 강제했는데,
역직렬화나 ORM이 이를 우회하면 결국 같은 문제가 돌아온다.

즉 다음을 같이 봐야 한다.

- JSON binding이 어떤 생성 경로를 타는가
- record canonical constructor가 정규화를 하는가
- native serialization 복원 후 invariant가 다시 보장되는가

value object는 코드 안에서만 예쁜 타입이 아니라, boundary-aware 타입이어야 한다.

## 실전 시나리오

### 시나리오 1: 같은 이메일이 서로 다른 키로 저장된다

한쪽은 trim/lower-case/NFC를 거치고, 다른 쪽은 raw string을 그대로 쓴다.
이러면 unique check, cache, login lookup이 서로 다른 기준으로 움직인다.

### 시나리오 2: 돈 객체가 `BigDecimal`만 감싼 thin wrapper다

통화, scale, rounding policy 없이 `amount`만 있으면
호출자들이 제각각 `setScale()`을 붙이게 되고 value object가 경계를 못 만든다.

### 시나리오 3: value object를 `Map` key로 쓰는데 canonicalization이 없다

표현이 다른 동등 값이 따로 저장되면서 cache miss와 dedup 실패가 생긴다.

### 시나리오 4: JSON 역직렬화 뒤 invalid value object가 생긴다

생성 경로가 여러 개인데 일부만 검증을 수행하면,
서비스 내부에 "타입은 맞지만 의미는 틀린 값"이 들어온다.

## 코드로 보기

### 1. invariant와 canonical key를 함께 가진 식별자

```java
import java.text.Normalizer;
import java.util.Locale;

public record Username(String displayValue, String canonicalKey) {
    public Username {
        if (displayValue == null || displayValue.isBlank()) {
            throw new IllegalArgumentException("username is blank");
        }
        canonicalKey = Normalizer.normalize(displayValue, Normalizer.Form.NFC)
            .toLowerCase(Locale.ROOT);
    }

    public static Username from(String raw) {
        return new Username(raw, null);
    }
}
```

### 2. 도메인 primitive로 단위 고정

```java
public record RetryLimit(int value) {
    public RetryLimit {
        if (value < 0 || value > 10) {
            throw new IllegalArgumentException("retry limit out of range");
        }
    }
}
```

### 3. thin wrapper보다 richer value object

```java
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Currency;

public record Money(Currency currency, BigDecimal amount) {
    public Money {
        int scale = currency.getDefaultFractionDigits();
        amount = amount.setScale(scale, RoundingMode.HALF_UP);
    }
}
```

정책을 타입 안으로 넣지 않으면 호출자가 규칙을 나눠 가지게 된다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| primitive 그대로 사용 | 빠르게 코드를 쓸 수 있다 | 규칙이 호출자에 흩어진다 |
| value object + 생성 시 검증 | invariant를 타입이 보장한다 | 타입 수와 변환 코드가 늘어난다 |
| aggressive canonicalization | 비교와 중복 제거가 안정적이다 | 원본 표현 보존 전략이 필요할 수 있다 |
| 원본/정규화 값 분리 | 표시와 비교 요구를 함께 만족한다 | 모델과 저장 구조가 복잡해진다 |

핵심은 value object를 "래퍼 클래스"가 아니라 도메인 의미를 잠그는 boundary object로 보는 것이다.

## 꼬리질문

> Q: immutable 객체면 value object라고 볼 수 있나요?
> 핵심: 아니다. 불변성은 필요조건에 가깝고, invariant와 의미 있는 equality가 함께 있어야 한다.

> Q: canonicalization은 왜 value object 안에 들어가야 하나요?
> 핵심: equality와 키 semantics를 호출자마다 다르게 해석하지 않게 하기 위해서다.

> Q: value object가 너무 많아지지 않나요?
> 핵심: 늘어날 수 있지만, 단위 혼동과 boundary bug를 줄이는 비용으로 보는 편이 낫다.

> Q: 원본 문자열과 canonical key를 둘 다 가져도 되나요?
> 핵심: 된다. 표시용 표현과 비교용 표현이 다른 도메인에서는 오히려 더 안전하다.

## 한 줄 정리

좋은 value object는 immutable wrapper가 아니라 invariant, canonicalization, equality, serialization boundary를 함께 잠그는 타입이다.
