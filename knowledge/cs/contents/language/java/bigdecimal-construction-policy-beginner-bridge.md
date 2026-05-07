---
schema_version: 3
title: BigDecimal 생성 정책 입문 브리지
concept_id: language/bigdecimal-construction-policy-beginner-bridge
canonical: true
category: language
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 88
mission_ids:
- missions/baseball
- missions/lotto
review_feedback_tags:
- bigdecimal-input-boundary
- floating-point-precision
- value-object-policy
aliases:
- BigDecimal construction policy
- new BigDecimal double pitfall
- BigDecimal valueOf vs string constructor
- BigDecimal input boundary
- 자바 BigDecimal 생성 정책
- BigDecimal double 생성자 피하기
symptoms:
- new BigDecimal(double)을 기본 선택지로 골라 화면에 보인 십진수와 다른 긴 근사값을 만들 수 있어
- BigDecimal 생성 정책, setScale 자릿수 정책, stripTrailingZeros 정규화 정책을 한꺼번에 섞어 판단해
- 문자열 입력과 이미 double로 들어온 값의 안전한 처리 경계를 구분하지 못해
intents:
- definition
- troubleshooting
- comparison
prerequisites:
- language/floating-point-precision-nan-infinity-serialization-pitfalls
next_docs:
- language/bigdecimal-setscale-unnecessary-validation-primer
- language/bigdecimal-striptrailingzeros-input-boundary-bridge
- language/bigdecimal-sorted-collection-bridge
linked_paths:
- contents/language/java/bigdecimal-setscale-unnecessary-validation-primer.md
- contents/language/java/bigdecimal-striptrailingzeros-input-boundary-bridge.md
- contents/language/java/bigdecimal-sorted-collection-bridge.md
- contents/language/java/floating-point-precision-nan-infinity-serialization-pitfalls.md
- contents/language/java/value-object-invariants-canonicalization-boundary-design.md
confusable_with:
- language/floating-point-precision-nan-infinity-serialization-pitfalls
- language/bigdecimal-setscale-unnecessary-validation-primer
- language/bigdecimal-striptrailingzeros-input-boundary-bridge
forbidden_neighbors: []
expected_queries:
- Java BigDecimal은 왜 new BigDecimal double 생성자를 피하고 문자열이나 valueOf를 쓰라고 해?
- BigDecimal.valueOf와 new BigDecimal(\"19.99\")를 입력 경계 관점으로 비교해줘
- BigDecimal 생성 정책과 setScale 반올림 정책은 어떻게 달라?
- 문자열 금액 입력을 BigDecimal로 만들 때 초보자가 지킬 규칙을 알려줘
- 이미 double 값만 있을 때 BigDecimal.valueOf가 new BigDecimal(double)보다 덜 놀라운 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 Java BigDecimal 생성 정책을 string constructor, BigDecimal.valueOf(double), new BigDecimal(double) pitfall, input boundary 관점으로 설명하는 beginner primer다.
  BigDecimal double 생성자, valueOf vs string, floating point precision, setScale, stripTrailingZeros 질문이 본 문서에 매핑된다.
---
# BigDecimal 생성 정책 입문 브리지

> 한 줄 요약: 초급자 기준으로는 "`new BigDecimal(double)`은 기본 선택지에서 빼고, 문자열 입력이면 문자열 생성자, 이미 `double`이면 `BigDecimal.valueOf(double)`"만 먼저 고정해도 입력 흔들림을 크게 줄일 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README](../README.md)
- [BigDecimal `setScale()` 검증 입문: `RoundingMode.UNNECESSARY`를 입력 정책으로 보기](./bigdecimal-setscale-unnecessary-validation-primer.md)
- [BigDecimal `stripTrailingZeros()` 입력 경계 브리지](./bigdecimal-striptrailingzeros-input-boundary-bridge.md)
- [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md)
- [Floating-Point Precision, `NaN`, `Infinity`, and Serialization Pitfalls](./floating-point-precision-nan-infinity-serialization-pitfalls.md)

retrieval-anchor-keywords: bigdecimal construction policy beginner, new bigdecimal double pitfall, bigdecimal valueof vs string, java bigdecimal 생성 정책, 자바 bigdecimal double 생성자 피하기, 처음 배우는데 bigdecimal, bigdecimal 왜 double 생성자 피하나요, bigdecimal 헷갈리는 생성 규칙, bigdecimal input boundary, bigdecimal beginner bridge, bigdecimal string constructor, bigdecimal valueof beginner

## 먼저 잡을 mental model

`BigDecimal` 생성은 계산 규칙보다 먼저 입력 규칙을 고르는 문제다.

- 문자열 입력이면 사람이 본 십진 표현을 그대로 옮기기 쉽다.
- 이미 `double`이 들어왔다면 `valueOf`가 `new BigDecimal(double)`보다 덜 놀랍다.
- 생성 정책을 먼저 고정해야 이후 `setScale`, `stripTrailingZeros`, 비교 정책도 덜 흔들린다.

짧게 외우면 이 순서다.

> 문자열이 있으면 문자열, `double`만 있으면 `valueOf`, `new BigDecimal(double)`은 기본값으로 고르지 않는다.

## 한눈에 보는 선택표

| 지금 가진 입력 | 첫 선택 | 이유 |
|---|---|---|
| `"19.99"` 같은 문자열 | `new BigDecimal("19.99")` | 입력 의도가 그대로 드러난다 |
| `19.99d` 같은 `double` | `BigDecimal.valueOf(19.99d)` | `double` 근사값을 덜 놀랍게 옮긴다 |
| 아직 API 설계 전 | 문자열 또는 정수 minor unit | 경계 의미를 더 명확히 잡기 쉽다 |

초급 단계에서는 위 표만 기억해도 대부분의 첫 실수를 줄일 수 있다.

## 왜 `new BigDecimal(double)`이 흔들리나

`double`은 많은 십진수를 정확히 저장하지 못한다.
그래서 `new BigDecimal(double)`은 "화면에 보인 값"보다 "`double` 내부 근사값"을 그대로 옮기기 쉽다.

```java
System.out.println(new BigDecimal(0.1d));
System.out.println(BigDecimal.valueOf(0.1d));
System.out.println(new BigDecimal("0.1"));
```

초급자 관점에서 중요한 관찰은 세 가지다.

- `new BigDecimal(0.1d)`는 예상보다 긴 값으로 보여 당황하기 쉽다.
- `BigDecimal.valueOf(0.1d)`는 보통 사람이 기대한 십진 표현에 더 가깝다.
- `new BigDecimal("0.1")`은 애초에 문자열 `"0.1"`을 기준으로 시작한다.

## 가장 흔한 입력 장면 두 가지

### 1. 사용자 입력이나 JSON이 문자열일 때

```java
BigDecimal amount = new BigDecimal("19.99");
```

이 방식이 쉬운 이유는 단순하다.

- "입력이 문자열이다"라는 사실이 코드에 그대로 보인다.
- 이후 정규화가 필요하면 생성 직후 한 번만 붙이면 된다.

```java
BigDecimal normalized = new BigDecimal("19.99").stripTrailingZeros();
```

### 2. 이미 `double` 계산 결과만 남았을 때

```java
BigDecimal amount = BigDecimal.valueOf(19.99d);
```

이 선택은 `double`이 완전히 안전하다는 뜻이 아니다.

- 근사값 문제는 이미 앞단에서 시작됐을 수 있다.
- 그래도 `new BigDecimal(double)`로 한 번 더 놀라운 표현을 만드는 일은 줄여 준다.

## 초보자 공통 혼동

- `valueOf(double)`가 있으니 `double` 자체도 정확하다고 생각하기 쉽다.
- 생성 문제와 `stripTrailingZeros()` 같은 정규화 문제를 같은 것으로 섞기 쉽다.
- "나중에 `setScale(2)` 하면 되지"라고 생각하기 쉽지만, 입력 흔들림과 반올림 정책은 다른 문제다.

처음 막힐 때는 질문을 둘로만 자르면 된다.

- 지금 문제는 "어떻게 만들까?"인가
- 아니면 만든 뒤 "자릿수나 표현을 어떻게 맞출까?"인가

안전한 읽기 순서는 이렇다.

1. 입력이 문자열인지 `double`인지 먼저 본다.
2. 생성 정책을 정한다.
3. 그다음에 정규화 정책이나 자릿수 정책을 붙인다.

## 다음에 어디로 이어서 읽을까

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| 생성 뒤 자릿수 검증은 어디서 하지? | [BigDecimal `setScale()` 검증 입문: `RoundingMode.UNNECESSARY`를 입력 정책으로 보기](./bigdecimal-setscale-unnecessary-validation-primer.md) |
| `1.0`과 `1.00`을 같은 표현으로 맞출까? | [BigDecimal `stripTrailingZeros()` 입력 경계 브리지](./bigdecimal-striptrailingzeros-input-boundary-bridge.md) |
| hash/sorted 컬렉션에서 기준이 왜 달라지지? | [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md) |

## 한 줄 정리

초급자에게 가장 안전한 `BigDecimal` 생성 정책은 "문자열이면 문자열 생성자, 이미 `double`이면 `valueOf`, `new BigDecimal(double)`은 기본 선택지에서 제외"다.
