---
schema_version: 3
title: Parser Overflow Boundaries parseInt parseLong toIntExact
concept_id: language/parser-overflow-boundaries-parseint-parselong-tointexact
canonical: true
category: language
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids:
- missions/lotto
- missions/payment
review_feedback_tags:
- numeric-boundary
- parsing
- overflow
aliases:
- Parser Overflow Boundaries parseInt parseLong toIntExact
- Java parseInt parseLong toIntExact boundary
- NumberFormatException numeric payload validation
- parser overflow vs arithmetic overflow
- narrowing conversion Math.toIntExact
- 자바 숫자 파싱 오버플로 경계
symptoms:
- parseInt overflow를 arithmetic overflow처럼 silent wraparound된다고 생각해 NumberFormatException fail-fast boundary를 놓쳐
- long으로 parse한 뒤 int로 줄이는 narrowing conversion에서 Math.toIntExact 같은 별도 경계를 두지 않아 값이 잘리거나 예외 의미가 흐려져
- whitespace sign radix leading zero 허용 여부를 parser contract로 문서화하지 않아 API boundary마다 숫자 payload 해석이 달라져
intents:
- troubleshooting
- deep_dive
- design
prerequisites:
- language/integer-overflow-exact-arithmetic-unit-conversion-pitfalls
- language/biginteger-unsigned-parsing-boundaries
- language/primitive-vs-wrapper-fields-json-payload-semantics
next_docs:
- language/biginteger-radix-leading-zero-sign-policies
- language/saturating-arithmetic-clamping-domain-contracts
- software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge
linked_paths:
- contents/language/java/integer-overflow-exact-arithmetic-unit-conversion-pitfalls.md
- contents/language/java/biginteger-unsigned-parsing-boundaries.md
- contents/language/java/biginteger-radix-leading-zero-sign-policies.md
- contents/language/java/primitive-vs-wrapper-fields-json-payload-semantics.md
confusable_with:
- language/integer-overflow-exact-arithmetic-unit-conversion-pitfalls
- language/biginteger-unsigned-parsing-boundaries
- language/saturating-arithmetic-clamping-domain-contracts
forbidden_neighbors: []
expected_queries:
- parseInt와 parseLong overflow는 arithmetic overflow와 어떻게 다르게 실패해?
- long으로 parse한 값을 int로 줄일 때 Math.toIntExact를 쓰는 이유가 뭐야?
- NumberFormatException을 API validation error로 번역할 때 어떤 boundary를 정해야 해?
- 숫자 payload에서 whitespace sign radix leading zero 허용 정책을 parser contract로 정해야 하는 이유가 뭐야?
- missing invalid number overflow narrowing failure를 primitive binding 전에 어떻게 구분해?
contextual_chunk_prefix: |
  이 문서는 parseInt, parseLong, Math.toIntExact를 중심으로 parser overflow, narrowing conversion, numeric payload validation boundary를 점검하는 advanced playbook이다.
  parser overflow, parseInt, parseLong, toIntExact, NumberFormatException, numeric boundary 질문이 본 문서에 매핑된다.
---
# Parser Overflow Boundaries: `parseInt`, `parseLong`, and `toIntExact`

> 한 줄 요약: parser overflow는 연산 overflow와 다른 층의 문제다. 입력 문자열이 아예 타입 범위를 넘는지, parse 후 축소 변환에서 깨지는지, whitespace/sign/radix를 어디까지 허용할지 정하지 않으면 숫자 payload 경계가 구현마다 달라진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Integer Overflow, Exact Arithmetic, and Unit Conversion Pitfalls](./integer-overflow-exact-arithmetic-unit-conversion-pitfalls.md)
> - [`BigInteger`, Unsigned Parsing, and Numeric Boundary Semantics](./biginteger-unsigned-parsing-boundaries.md)
> - [`BigInteger` Parser Radix, Leading Zero, and Sign Policies](./biginteger-radix-leading-zero-sign-policies.md)
> - [Primitive vs Wrapper Fields in JSON Payload Semantics](./primitive-vs-wrapper-fields-json-payload-semantics.md)

> retrieval-anchor-keywords: parser overflow, parseInt boundary, parseLong boundary, toIntExact, NumberFormatException, numeric payload validation, parse boundary, input range validation, narrowing conversion, string to int contract

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

숫자 payload boundary에는 보통 세 단계가 있다.

- 문자열이 문법상 숫자인가
- 그 숫자가 목표 타입 범위 안인가
- parse 후 다른 더 작은 타입으로 줄여도 되는가

즉 parser는 단순 문자열 변환이 아니라 범위 검증기다.

## 깊이 들어가기

### 1. parser overflow는 계산 overflow와 다르다

`Integer.parseInt("999999999999")`는 계산 결과가 wrap되지 않는다.  
보통 `NumberFormatException`으로 경계를 넘었다는 사실을 바로 드러낸다.

즉 parse boundary는 fail-fast이고,  
계산 overflow는 silent wraparound일 수 있다.

### 2. narrowing conversion도 별도 boundary다

`long`으로는 읽히지만 `int`로는 안 되는 값이 있다.

예:

- DB bigint 읽기
- external ID parsing
- pagination size parsing 후 API 내부 int 사용

이 경우는 parse 성공 후에도 `Math.toIntExact()` 같은 축소 변환 boundary가 필요하다.

### 3. trim/sign/radix 정책이 parser contract 일부다

이 경계에서 흔한 질문:

- 앞뒤 공백 허용 여부
- `+42` 허용 여부
- leading zero 허용 여부
- radix 10 고정 여부

이걸 문서화하지 않으면 같은 API라도 구현마다 behavior가 달라진다.

### 4. parser 에러를 domain 에러로 번역하는 계층이 필요할 수 있다

`NumberFormatException` 자체는 low-level 예외다.  
API boundary에서는 다음을 같이 정해야 한다.

- 400 validation error로 바꿀지
- field-level error로 묶을지
- raw input을 로그/메트릭에 어떻게 남길지

즉 parser boundary는 exception mapping boundary이기도 하다.

### 5. 너무 이른 primitive parse는 intent를 잃을 수 있다

JSON binding 단계에서 바로 primitive로 떨어뜨리면:

- missing
- invalid number
- overflow
- narrowing failure

를 더 정교하게 구분하기 어려울 수 있다.

## 실전 시나리오

### 시나리오 1: 외부 payload는 `long`인데 내부 API는 `int`다

parse는 성공하지만 캐스팅 순간 잘리거나 예외가 난다.  
boundary를 하나로 착각한 전형적인 사례다.

### 시나리오 2: `" 42 "` 입력이 어떤 경로에선 되고 어떤 경로에선 안 된다

trim policy가 일관되지 않다.  
API contract가 구현 detail에 묻힌 상태다.

### 시나리오 3: 너무 큰 page size가 validation 없이 내려온다

문자열 -> long parse는 성공하고, 내부에서 int cast가 조용히 이뤄지면 runtime correctness가 흔들린다.

## 코드로 보기

### 1. parse boundary

```java
int page = Integer.parseInt(rawPage);
```

### 2. narrowing boundary

```java
long rawLimit = Long.parseLong(raw);
int limit = Math.toIntExact(rawLimit);
```

### 3. domain validation과 분리

```java
if (limit <= 0) {
    throw new IllegalArgumentException("limit must be positive");
}
```

parse 성공과 domain validity는 다른 문제다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| 바로 primitive parse | 구현이 단순하다 | policy와 에러 의미가 숨기 쉽다 |
| `long` 후 `toIntExact` | boundary를 더 명확히 나눌 수 있다 | 코드가 조금 길어진다 |
| `BigInteger`로 먼저 읽기 | 범위를 더 넓게 다룰 수 있다 | 일반 API엔 과할 수 있다 |

핵심은 parser를 문자열 변환이 아니라 범위/정책/에러 번역 경계로 보는 것이다.

## 꼬리질문

> Q: parser overflow와 계산 overflow 차이는 무엇인가요?
> 핵심: parser overflow는 보통 즉시 예외로 드러나고, 계산 overflow는 wraparound로 숨어들 수 있다.

> Q: 왜 `toIntExact`가 중요한가요?
> 핵심: parse 성공 이후의 narrowing conversion boundary를 명시적으로 드러내기 때문이다.

> Q: parser 정책을 왜 문서화하나요?
> 핵심: 공백, 부호, radix, leading zero 허용 여부가 API behavior를 바꾸기 때문이다.

## 한 줄 정리

숫자 parser boundary는 문자열 문법, 범위 검증, narrowing conversion, 에러 번역을 함께 다루는 계약이므로 `parseInt()` 한 줄로 끝나지 않는다.
