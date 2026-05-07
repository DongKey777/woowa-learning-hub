---
schema_version: 3
title: BigInteger Parser Radix, Leading Zero, Sign, and Boundary Contracts
concept_id: language/biginteger-radix-leading-zero-sign-policies
canonical: true
category: language
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 83
mission_ids: []
review_feedback_tags:
- numeric-boundary
- parser-contract
- canonicalization
aliases:
- BigInteger parser contract
- BigInteger radix policy
- BigInteger leading zero sign policy
- BigInteger String radix
- decimal string contract
- numeric canonicalization
- BigInteger 파싱 계약
symptoms:
- BigInteger가 큰 수를 읽어 주면 radix prefix sign leading zero 정책도 자동으로 정해진다고 오해해
- 원문 문자열과 canonical string이 달라지는 상황을 signature, cache key, audit log 경계에서 분리하지 못해
- primitive overflow를 BigInteger로 피했지만 domain max, transport max, exact conversion 경계 검증을 놓쳐
intents:
- deep_dive
- troubleshooting
- design
prerequisites:
- language/biginteger-unsigned-parsing-boundaries
- language/parser-overflow-boundaries-parseint-parselong-tointexact
next_docs:
- language/biginteger-unsigned-parsing-boundaries
- language/integer-overflow-exact-arithmetic-unit-conversion-pitfalls
- language/value-object-invariants-canonicalization-boundary-design
linked_paths:
- contents/language/java/biginteger-unsigned-parsing-boundaries.md
- contents/language/java/parser-overflow-boundaries-parseint-parselong-tointexact.md
- contents/language/java/integer-overflow-exact-arithmetic-unit-conversion-pitfalls.md
- contents/language/java/primitive-vs-wrapper-fields-json-payload-semantics.md
- contents/language/java/empty-string-blank-null-missing-payload-semantics.md
- contents/language/java/value-object-invariants-canonicalization-boundary-design.md
- contents/language/java/locale-root-case-mapping-unicode-normalization.md
confusable_with:
- language/biginteger-unsigned-parsing-boundaries
- language/parser-overflow-boundaries-parseint-parselong-tointexact
- language/integer-overflow-exact-arithmetic-unit-conversion-pitfalls
forbidden_neighbors: []
expected_queries:
- BigInteger parser에서 radix prefix leading zero sign 정책을 어떻게 계약으로 잠가야 해?
- new BigInteger raw radix가 0x prefix를 자동 처리하지 않는 이유를 설명해줘
- BigInteger로 primitive overflow를 피해도 domain max와 transport boundary를 다시 검증해야 하는 이유가 뭐야?
- BigInteger 입력에서 +000 -0 leading zero를 canonical string으로 어떻게 처리해야 해?
- 큰 정수 payload를 signature cache key audit log에 쓸 때 raw input과 canonical value를 어떻게 나눠?
contextual_chunk_prefix: |
  이 문서는 BigInteger parser contract를 radix, prefix, sign, leading zero, digit alphabet, canonical string, domain max, exact conversion boundary로 설명하는 advanced deep dive다.
  BigInteger radix policy, 0x prefix, leading zero, minus zero, numeric canonicalization, parser boundary 질문이 본 문서에 매핑된다.
---
# `BigInteger` Parser Radix, Leading Zero, Sign, and Boundary Contracts

> 한 줄 요약: `BigInteger`는 parse 시점의 primitive overflow ceiling은 없애 주지만, radix/prefix, sign, leading zero, digit alphabet, domain max를 대신 정해 주지 않는다. parser contract를 안 잠그면 같은 값이 다른 문자열로 들어오고, exact conversion과 transport boundary에서 다시 깨진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [`BigInteger`, Unsigned Parsing, and Numeric Boundary Semantics](./biginteger-unsigned-parsing-boundaries.md)
> - [Parser Overflow Boundaries: `parseInt`, `parseLong`, and `toIntExact`](./parser-overflow-boundaries-parseint-parselong-tointexact.md)
> - [Integer Overflow, Exact Arithmetic, and Unit Conversion Pitfalls](./integer-overflow-exact-arithmetic-unit-conversion-pitfalls.md)
> - [Primitive vs Wrapper Fields in JSON Payload Semantics](./primitive-vs-wrapper-fields-json-payload-semantics.md)
> - [Empty String, Blank, `null`, and Missing Payload Semantics](./empty-string-blank-null-missing-payload-semantics.md)
> - [Value Object Invariants, Canonicalization, and Boundary Design](./value-object-invariants-canonicalization-boundary-design.md)
> - [`Locale.ROOT`, Case Mapping, and Unicode Normalization Pitfalls](./locale-root-case-mapping-unicode-normalization.md)

> retrieval-anchor-keywords: BigInteger parser contract, BigInteger radix policy, BigInteger(String radix), leading zero policy, sign policy, plus sign, minus zero, prefix parsing, 0x prefix, decimal string contract, hex parsing, numeric canonicalization, longValueExact, intValueExact, unsigned64 range, digit alphabet, ASCII digits only, NumberFormatException, bigint payload normalization

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [입력 행렬](#입력-행렬)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

`BigInteger` parser boundary에는 최소 네 축이 있다.

- 어떤 문자열 문법을 숫자로 볼 것인가
- parse된 값을 어떤 canonical string으로 볼 것인가
- 그 값이 도메인/전송 boundary의 최대 범위 안에 있는가
- parser 예외를 어떤 domain error로 번역할 것인가

즉 `BigInteger`는 "큰 수를 읽는 API"이기도 하지만,  
실무에선 더 자주 **문자열 숫자 계약을 잠그는 경계**다.

## 깊이 들어가기

### 1. radix는 편의 기능이 아니라 문법 계약이다

`new BigInteger(raw, radix)`는 radix 2..36만 받는다.  
이 범위를 벗어나면 입력 내용과 상관없이 `NumberFormatException`이 난다.

핵심은 radix를 열어두는 순간 허용 문자 집합과 같은 원문 해석이 함께 열린다는 점이다.

- `"42"`는 radix 10에선 `42`
- 같은 `"42"`도 radix 16에선 `66`
- 같은 `"10"`도 radix 2, 10, 16, 36에서 모두 다른 값

그래서 external payload는 보통 radix를 고정하고,  
운영자용 도구나 migration 입력에서만 다중 radix를 여는 편이 안전하다.

### 2. prefix는 자동 해석되지 않는다

`BigInteger`는 `0x`, `0b`, `0o` prefix를 특별 취급하지 않는다.

- `new BigInteger("0x10", 16)`은 실패한다
- `new BigInteger("0x10", 36)`은 실패가 아니라 다른 수로 parse된다

즉 "prefix가 붙은 hex 문자열"을 받으려면:

1. prefix를 boundary에서 명시적으로 판별하고
2. prefix를 제거한 뒤
3. 그에 맞는 radix로 parse해야 한다

auto-detect를 느슨하게 만들면 `"10"`과 `"0x10"`이 같은 정책 표면에 섞여 들어와 contract가 흐려진다.

### 3. sign과 leading zero는 값 문제가 아니라 표현 정책이다

`BigInteger`는 다음을 자연스럽게 받아들인다.

- `+42`
- `-42`
- `000123`
- `+000`
- `-0`

이 값들은 parse 후 각각 `42`, `-42`, `123`, `0`, `0`으로 정규화된다.

즉 raw input과 canonical string이 자동으로 달라질 수 있다.  
이게 중요한 이유는 다음과 같다.

- signature 대상 문자열
- 캐시 키
- audit log
- idempotency key
- 사람이 보는 원문 회수 여부

특히 `-0`이 `0`으로 collapse되면 "부호 있는 원문을 받았는지" 정보는 `BigInteger` 값만으로 복원되지 않는다.

### 4. digit alphabet도 생각보다 넓다

`BigInteger(String, radix)`는 ASCII 숫자/문자만 읽는다고 생각하기 쉽지만,  
실제 digit 판별은 더 넓게 동작할 수 있다.

예를 들어 full-width digit가 섞인 `"０42"`도 decimal로 읽히면 `42`가 된다.

즉 contract가 "ASCII decimal string만 허용"이라면 `BigInteger`에 바로 넘기지 말고:

- ASCII 문자 검증
- 허용 sign/prefix 검증
- leading zero 검증

를 먼저 해야 한다.

### 5. `BigInteger` parse는 primitive parse overflow만 없앤다

`Integer.parseInt()`나 `Long.parseLong()`은 타입 범위를 넘는 순간 parse 자체가 실패한다.  
반면 `BigInteger`는 매우 큰 정수도 읽는다.

하지만 boundary 문제는 사라지지 않는다. 단지 **다음 단계로 이동**할 뿐이다.

- 도메인 최대값 비교 (`compareTo`)
- transport/schema 최대값 검증
- DB 컬럼 범위 검증
- `longValueExact()` / `intValueExact()` 같은 exact narrowing boundary

예를 들어:

- `9223372036854775807`은 `longValueExact()` 가능
- `9223372036854775808`은 parse는 되지만 `longValueExact()`에서 실패
- `18446744073709551615`도 parse는 되지만 signed `long` exact conversion은 실패

즉 "`BigInteger`라서 overflow가 없다"가 아니라,  
"constructor overflow는 없고 downstream exact boundary는 별도로 있다"가 정확하다.

### 6. unsigned contract도 따로 잠가야 한다

`BigInteger`는 음수도 읽고, unsigned 상한도 자동으로 강제하지 않는다.

예를 들어 unsigned 64-bit decimal 계약이라면 parser는 최소 다음을 함께 강제해야 한다.

- 음수 금지
- radix 10 고정
- optional `+` 허용 여부
- leading zero 허용 여부
- `0 <= value <= 18446744073709551615`

그렇지 않으면 `-1`, `+42`, `00042`, `18446744073709551616`이 모두 다른 의미로 흘러들어온다.

### 7. parser contract는 단계별로 쪼개야 선명하다

실무에서 제일 안전한 구조는 다음이다.

1. lexical policy: trim 여부, ASCII-only 여부, prefix/sign 허용 여부
2. parse policy: radix 고정 후 `BigInteger` 생성
3. numeric range policy: unsigned인지, domain max/min은 무엇인지
4. canonicalization policy: `toString()`으로 저장할지 raw도 같이 보관할지
5. error mapping policy: `NumberFormatException`과 range error를 어떤 validation error로 번역할지

이 다섯 단계를 한 util 함수에 감추면 boundary reasoning이 약해진다.  
value object나 boundary adapter 안에 잠그는 편이 낫다.

## 입력 행렬

| Raw input | `BigInteger` 동작 | 계약 질문 |
|---|---|---|
| `+42` | 허용되고 `42`가 된다 | explicit plus를 허용할 것인가 |
| `000123` | 허용되고 `123`이 된다 | leading zero를 거부할지, canonicalize할지 |
| `-0` | 허용되고 `0`이 된다 | negative zero를 원문 기준으로 금지할지 |
| `0x10` with radix 16 | 실패한다 | prefix를 strip한 뒤 parse할 것인가 |
| `0x10` with radix 36 | 실패가 아니라 다른 수가 된다 | multi-radix auto-detect를 금지할 것인가 |
| ` 42 ` | 실패한다 | trim을 boundary 바깥에서 할지 안 할지 |
| `1_000` | 실패한다 | 사람이 읽기 쉬운 separator를 허용할 것인가 |
| `０42` | 허용되고 `42`가 된다 | ASCII-only 숫자 계약이 필요한가 |
| radix `1` or `37` | 입력과 무관하게 실패한다 | parser 설정값 검증을 어디서 할 것인가 |

핵심은 `BigInteger`가 "값을 읽어 준다"는 사실과  
"우리가 받아야 하는 문자열 계약"이 같지 않다는 점이다.

## 실전 시나리오

### 시나리오 1: unsigned 64-bit ID를 `BigInteger`로 먼저 읽는다

외부 payload가 decimal string이고 JS consumer도 있다면 `BigInteger` parse 후:

- 음수 금지
- `2^64 - 1` 상한 검증
- canonical decimal string 저장

을 같이 해야 한다.

이때 parse 성공은 곧 unsigned64 계약 성공이 아니다.

### 시나리오 2: 운영 도구는 hex를 받고 public API는 decimal만 받는다

운영 도구에서 `0xFF` 같은 입력이 편하다는 이유로 public API에도 같은 parser를 쓰면  
도메인 boundary와 operator tooling boundary가 섞인다.

외부 API는 decimal-only, 내부 tool은 prefix-dispatch + radix parse처럼  
계약 표면을 분리하는 편이 안전하다.

### 시나리오 3: 캐시 키와 서명이 raw string에 묶여 있다

`+00042`와 `42`는 값은 같아도 raw string은 다르다.  
boundary에서 canonicalization 없이 흘려 보내면:

- cache duplication
- signature mismatch
- audit log 비교 혼선

이 생긴다.

## 코드로 보기

### 1. strict decimal unsigned64 parser 예시

```java
import java.math.BigInteger;
import java.util.Objects;
import java.util.regex.Pattern;

public final class Unsigned64Decimal {
    private static final Pattern ASCII_DECIMAL = Pattern.compile("0|[1-9][0-9]*");
    private static final BigInteger MAX =
            new BigInteger("18446744073709551615");

    private final BigInteger value;
    private final String canonical;

    private Unsigned64Decimal(BigInteger value) {
        this.value = value;
        this.canonical = value.toString();
    }

    public static Unsigned64Decimal parse(String raw) {
        Objects.requireNonNull(raw, "raw");

        if (!ASCII_DECIMAL.matcher(raw).matches()) {
            throw new IllegalArgumentException("expected canonical ASCII decimal");
        }

        BigInteger parsed = new BigInteger(raw, 10);
        if (parsed.compareTo(MAX) > 0) {
            throw new IllegalArgumentException("unsigned64 overflow");
        }

        return new Unsigned64Decimal(parsed);
    }

    public BigInteger value() {
        return value;
    }

    public String canonical() {
        return canonical;
    }
}
```

이 예시는 일부러 다음을 동시에 강제한다.

- radix 10 고정
- `+` 금지
- leading zero 금지 (`0`만 예외)
- ASCII digit만 허용
- unsigned64 상한 검증
- canonical decimal string 보관

### 2. prefix-dispatch가 필요하면 parse 전 단계에서 분리

```java
static BigInteger parseToolNumber(String raw) {
    if (raw.startsWith("0x") || raw.startsWith("0X")) {
        return new BigInteger(raw.substring(2), 16);
    }
    if (raw.startsWith("0b") || raw.startsWith("0B")) {
        return new BigInteger(raw.substring(2), 2);
    }
    return new BigInteger(raw, 10);
}
```

이 함수는 운영 도구엔 유용할 수 있지만,  
public API contract에 그대로 노출하면 표현 공간이 과하게 넓어진다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| raw string을 바로 `BigInteger`에 넘긴다 | 구현이 가장 단순하다 | sign, leading zero, digit alphabet, prefix 정책이 숨는다 |
| parse 전 lexical validation을 둔다 | 문자열 계약이 선명해진다 | 코드와 테스트가 늘어난다 |
| multi-radix + prefix tool parser | 운영/마이그레이션 입력이 편하다 | external contract drift 위험이 크다 |
| canonical string만 저장한다 | cache/signature/비교가 안정된다 | 원문 표시가 필요하면 별도 보관이 필요하다 |
| `BigInteger` 후 `longValueExact()`로 줄인다 | downstream boundary가 드러난다 | exact conversion 단계를 빼먹기 쉽다 |

핵심은 `BigInteger` parser를 숫자 변환기보다 **경계 계약 집행기**로 보는 것이다.

## 꼬리질문

> Q: `BigInteger` parsing도 overflow가 있나요?
> 핵심: constructor parse는 매우 큰 수를 읽지만, domain max와 `longValueExact()` 같은 downstream exact boundary는 여전히 남아 있다.

> Q: `0x10`을 radix 16으로 주면 왜 바로 안 되나요?
> 핵심: `BigInteger`는 `0x`를 prefix 토큰으로 보지 않으므로 boundary에서 직접 strip해야 한다.

> Q: leading zero나 `+` 부호를 왜 따로 막아야 하나요?
> 핵심: 값은 같아도 raw string 계약, cache key, signature, audit semantics가 달라질 수 있기 때문이다.

> Q: 왜 ASCII-only 검증까지 이야기하나요?
> 핵심: `BigInteger`가 받아들이는 digit alphabet이 생각보다 넓을 수 있어서, 외부 계약이 ASCII decimal string이라면 별도 lexical gate가 필요하다.

## 한 줄 정리

`BigInteger` parsing의 핵심은 "큰 수를 읽는다"가 아니라 radix, prefix, sign, leading zero, digit alphabet, downstream range를 명시적으로 잠가 문자열 숫자 계약을 안정화하는 것이다.
