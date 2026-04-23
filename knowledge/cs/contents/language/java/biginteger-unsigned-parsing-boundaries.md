# `BigInteger`, Unsigned Parsing, and Numeric Boundary Semantics

> 한 줄 요약: `long`을 넘는 정수나 unsigned 값을 다룰 때 `BigInteger`와 `parseUnsigned*`는 단순한 대체 API가 아니다. 표현 범위, signed/unsigned 해석, 직렬화 문자열 계약, DB/API 경계가 함께 바뀐다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Integer Overflow, Exact Arithmetic, and Unit Conversion Pitfalls](./integer-overflow-exact-arithmetic-unit-conversion-pitfalls.md)
> - [`BigInteger` Parser Radix, Leading Zero, and Sign Policies](./biginteger-radix-leading-zero-sign-policies.md)
> - [Parser Overflow Boundaries: `parseInt`, `parseLong`, and `toIntExact`](./parser-overflow-boundaries-parseint-parselong-tointexact.md)
> - [Autoboxing, `IntegerCache`, `==`, and Null Unboxing Pitfalls](./autoboxing-integercache-null-unboxing-pitfalls.md)
> - [Java IO, NIO, Serialization, JSON Mapping](./io-nio-serialization.md)
> - [Value Object Invariants, Canonicalization, and Boundary Design](./value-object-invariants-canonicalization-boundary-design.md)

> retrieval-anchor-keywords: BigInteger, unsigned parsing, parseUnsignedInt, parseUnsignedLong, unsigned value, numeric boundary, bigint payload, decimal string contract, large identifier, numeric range validation, signed vs unsigned, radix policy, leading zero

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

숫자가 크다고 해서 무조건 `BigInteger`를 쓰면 끝나는 것은 아니다.

질문은 보통 세 가지다.

- 표현 범위를 넘는가
- signed인지 unsigned인지
- 문자열/JSON/DB 경계에서 어떤 형식으로 계약할 것인가

즉 타입 선택은 수학적 크기뿐 아니라 해석 규칙의 선택이다.

## 깊이 들어가기

### 1. unsigned는 타입이 아니라 해석 방식이다

Java primitive 정수는 기본적으로 signed다.  
그래서 unsigned 값을 다룰 땐:

- `parseUnsignedInt`
- `parseUnsignedLong`
- 비교/출력 시 unsigned helper

같은 별도 해석이 필요하다.

즉 값 저장 방식과 값 해석 방식이 분리된다.

### 2. `BigInteger`는 overflow를 없애지만 계약은 더 무거워진다

장점:

- 범위 걱정이 줄어든다
- exact integer semantics를 유지한다

비용:

- allocation 증가
- 문자열/바이너리 직렬화 정책 필요
- DB/API consumer가 같은 범위를 받아줄지 검토 필요

즉 overflow 해결과 boundary interoperability는 별개다.

### 3. large numeric identifier는 숫자인지 문자열인지 먼저 정해야 한다

아주 큰 ID를 JSON number로 내보내면:

- JavaScript consumer precision 손실
- 언어별 파서 차이
- 서명/해시 표현 차이

가 생길 수 있다.

그래서 큰 정수는 종종 "숫자처럼 보이지만 문자열 계약"으로 다루는 편이 더 안전하다.

### 4. `BigInteger`와 unsigned helper를 섞을 때도 canonicalization이 필요하다

예:

- leading zero 허용 여부
- radix 고정 여부
- 음수 부호 금지 여부

같은 정책이 없다면 숫자는 같아도 payload가 달라진다.

### 5. DB와 API가 허용하는 최대 범위는 따로 봐야 한다

애플리케이션 안에서 `BigInteger`가 안전해도:

- DB bigint
- message schema
- external REST/OpenAPI

가 더 작은 범위를 강제할 수 있다.

즉 domain max와 transport max를 분리해야 한다.

## 실전 시나리오

### 시나리오 1: snowflake-like ID를 JavaScript client에 number로 준다

서버에선 `long`이 맞아도 브라우저에선 안전 정수 범위를 넘을 수 있다.  
이 경우는 JSON number보다 문자열 계약이 더 안전하다.

### 시나리오 2: unsigned hex 값을 signed long으로 읽는다

표현은 같아 보여도 해석이 달라진다.  
경계에서 signed/unsigned 규칙을 안 맞추면 비교 결과가 뒤틀린다.

### 시나리오 3: `BigInteger`로 바꿨는데 DB 저장은 여전히 `BIGINT`다

애플리케이션만 넓은 범위를 받아도 persistence boundary에서 다시 깨질 수 있다.

## 코드로 보기

### 1. unsigned long parsing 감각

```java
long value = Long.parseUnsignedLong("18446744073709551615");
```

이 값은 signed `long` 연산 감각과 다르게 읽어야 한다.

### 2. 큰 정수는 문자열 계약을 검토

```java
String orderId = new java.math.BigInteger("123456789012345678901234567890").toString();
```

### 3. 범위 검증

```java
java.math.BigInteger max = new java.math.BigInteger("999999999999999999");
if (input.compareTo(max) > 0) {
    throw new IllegalArgumentException("too large");
}
```

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| signed primitive | 빠르고 단순하다 | 범위와 unsigned 해석에 약하다 |
| unsigned helper API | 기존 primitive 위에서 unsigned semantics를 표현할 수 있다 | 타입 시스템이 직접 막아주진 않는다 |
| `BigInteger` | 매우 큰 정확한 정수를 다룰 수 있다 | allocation과 boundary 계약이 무거워진다 |
| 문자열 계약 | 상호운용성이 높다 | 숫자 검증과 parsing 책임이 커진다 |

핵심은 "더 큰 숫자"보다 "이 값을 어떤 규칙으로 해석하고 운반할 것인가"를 먼저 정하는 것이다.

## 꼬리질문

> Q: Java에 unsigned 타입이 없으면 어떻게 다루나요?
> 핵심: unsigned helper API와 비교/출력 규칙을 따로 써서 해석 모델을 맞춘다.

> Q: `BigInteger`면 항상 안전한가요?
> 핵심: 앱 내부 범위는 넓어지지만 DB/API/consumer 경계가 같은 범위를 보장하는지는 별도 문제다.

> Q: 큰 ID를 왜 문자열로 주기도 하나요?
> 핵심: 언어별 숫자 정밀도와 JSON number 해석 차이 때문에 문자열이 더 안전할 때가 많다.

## 한 줄 정리

`BigInteger`와 unsigned parsing은 overflow 해결 도구이면서 동시에 boundary interpretation 선택이므로, signed/unsigned와 문자열 계약을 함께 설계해야 한다.
