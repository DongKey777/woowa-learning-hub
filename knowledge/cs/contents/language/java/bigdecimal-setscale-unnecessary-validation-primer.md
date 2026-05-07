---
schema_version: 3
title: BigDecimal setScale UNNECESSARY Validation Primer
concept_id: language/bigdecimal-setscale-unnecessary-validation-primer
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
- bigdecimal-scale-policy
- input-validation
- rounding-boundary
aliases:
- BigDecimal setScale UNNECESSARY
- BigDecimal scale validation
- RoundingMode.UNNECESSARY validation
- BigDecimal reject extra decimals
- 자바 BigDecimal 소수 자릿수 검증
- BigDecimal setScale 검증
symptoms:
- setScale을 반올림 도구로만 보고 RoundingMode.UNNECESSARY가 입력 자릿수 계약 검증이라는 점을 놓쳐
- 소수 둘째 자리까지만 허용해야 하는 API에서 조용히 HALF_UP으로 보정해 계약 위반을 숨길 수 있어
- stripTrailingZeros 정규화와 setScale 자릿수 검증을 같은 문제로 섞어 판단해
intents:
- definition
- troubleshooting
- comparison
prerequisites:
- language/bigdecimal-construction-policy-beginner-bridge
next_docs:
- language/bigdecimal-striptrailingzeros-input-boundary-bridge
- language/bigdecimal-tostring-vs-toplainstring-output-policy-mini-bridge
- language/bigdecimal-money-equality-rounding-serialization-pitfalls
linked_paths:
- contents/language/java/bigdecimal-construction-policy-beginner-bridge.md
- contents/language/java/bigdecimal-striptrailingzeros-input-boundary-bridge.md
- contents/language/java/bigdecimal-key-policy-30-second-checklist.md
- contents/language/java/bigdecimal-tostring-vs-toplainstring-output-policy-mini-bridge.md
- contents/language/java/bigdecimal-mathcontext-striptrailingzeros-canonicalization-traps.md
- contents/language/java/bigdecimal-money-equality-rounding-serialization-pitfalls.md
confusable_with:
- language/bigdecimal-striptrailingzeros-input-boundary-bridge
- language/bigdecimal-construction-policy-beginner-bridge
- language/bigdecimal-tostring-vs-toplainstring-output-policy-mini-bridge
forbidden_neighbors: []
expected_queries:
- BigDecimal setScale 2 UNNECESSARY는 반올림이 아니라 입력 검증이라는 뜻이야?
- 소수 둘째 자리까지만 허용할 때 RoundingMode.UNNECESSARY를 어떻게 써야 해?
- BigDecimal setScale과 stripTrailingZeros는 각각 언제 쓰는지 비교해줘
- 12.345를 조용히 반올림하지 않고 거부하려면 BigDecimal에서 무엇을 써야 해?
- BigDecimal scale contract와 rounding policy를 초보자 기준으로 정리해줘
contextual_chunk_prefix: |
  이 문서는 BigDecimal setScale(..., RoundingMode.UNNECESSARY)를 반올림 없는 scale contract validation으로 설명하는 beginner primer다.
  BigDecimal scale validation, reject extra decimals, setScale vs stripTrailingZeros, HALF_UP vs UNNECESSARY 질문이 본 문서에 매핑된다.
---
# BigDecimal `setScale()` 검증 입문: `RoundingMode.UNNECESSARY`를 입력 정책으로 보기

> 한 줄 요약: `setScale(..., RoundingMode.UNNECESSARY)`는 "예쁘게 반올림하는 트릭"보다 먼저 "이 입력은 반올림 없이 우리 자릿수 계약으로 표현 가능해야 한다"를 코드로 선언하는 검증 도구다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README](../README.md)
- [BigDecimal 생성 정책 입문 브리지](./bigdecimal-construction-policy-beginner-bridge.md)
- [BigDecimal `stripTrailingZeros()` 입력 경계 브리지](./bigdecimal-striptrailingzeros-input-boundary-bridge.md)
- [BigDecimal Key 정책 30초 체크리스트](./bigdecimal-key-policy-30-second-checklist.md)
- [BigDecimal 출력 정책 미니 브리지: `toString()` vs `toPlainString()`](./bigdecimal-tostring-vs-toplainstring-output-policy-mini-bridge.md)
- [BigDecimal `MathContext`, `stripTrailingZeros()`, and Canonicalization Traps](./bigdecimal-mathcontext-striptrailingzeros-canonicalization-traps.md)
- [BigDecimal Money Equality, Rounding, and Serialization Pitfalls](./bigdecimal-money-equality-rounding-serialization-pitfalls.md)

retrieval-anchor-keywords: bigdecimal setscale beginner, bigdecimal unnecessary validation, bigdecimal input validation scale policy, bigdecimal setscale unnecessary primer, java bigdecimal scale validation beginner, java bigdecimal roundingmode unnecessary, 자바 bigdecimal setscale 검증, 자바 bigdecimal unnecessary 검증, 자바 bigdecimal 소수 자릿수 검증, 자바 bigdecimal 반올림 말고 검증, bigdecimal scale contract, bigdecimal reject extra decimals, bigdecimal payload decimal places validation, bigdecimal setscale unnecessary validation primer basics, bigdecimal setscale unnecessary validation primer beginner

## 먼저 잡을 멘탈 모델

초급자 기준으로는 이 한 줄이 제일 중요하다.

> `setScale(2, UNNECESSARY)`는 "2자리로 반올림해 줘"가 아니라 "반올림 없이 2자리로 맞출 수 있어야 해"에 가깝다.

- 값 보정이 아니라 계약 검증이다.
- 통과하면 "입력이 이미 정책 안에 있다"는 뜻이다.
- 실패하면 "몰래 반올림하지 말고 바로 거부하자"는 뜻이다.

## 먼저 결론

| 하고 싶은 일 | 초급자용 첫 선택 | 이유 |
|---|---|---|
| 소수 둘째 자리까지만 허용하고 싶다 | `setScale(2, UNNECESSARY)` | 셋째 자리 이후가 있으면 조용히 고치지 않고 바로 드러낸다 |
| `12.345`도 받아서 `12.35`로 맞추고 싶다 | `setScale(2, HALF_UP)` 같은 명시적 반올림 | 입력 보정보다 사용자 편의가 우선일 때 |
| `1.0`, `1.00`, `1`을 같은 표현으로 맞추고 싶다 | `stripTrailingZeros()` 정책 검토 | 자릿수 검증이 아니라 정규화 문제다 |

핵심은 `setScale`을 하나의 기능으로 보지 않는 것이다.

- `UNNECESSARY`: 검증
- 다른 `RoundingMode`: 보정

## 30초 예제: 검증과 보정은 다르다

```java
import java.math.BigDecimal;
import java.math.RoundingMode;

BigDecimal ok = new BigDecimal("12.30")
        .setScale(2, RoundingMode.UNNECESSARY);

BigDecimal alsoOk = new BigDecimal("12.3")
        .setScale(2, RoundingMode.UNNECESSARY);

BigDecimal fixed = new BigDecimal("12.345")
        .setScale(2, RoundingMode.HALF_UP);

System.out.println(ok);    // 12.30
System.out.println(alsoOk); // 12.30
System.out.println(fixed); // 12.35
```

여기서 중요한 차이는 결과 숫자보다 의도다.

- `UNNECESSARY`는 "반올림 없이 정책 안으로 들어와야 한다"
- `HALF_UP`은 "안 맞아도 내가 고쳐서 쓸게"

같은 `setScale` 호출이어도 정책은 완전히 다르다.

## 왜 beginner가 자주 헷갈리나

`setScale`이라는 이름만 보면 보통 이렇게 생각하기 쉽다.

- "소수 둘째 자리로 바꾸는 함수겠지"
- "안 맞으면 알아서 반올림하겠지"
- "검증도 되고 보정도 되니 아무거나 써도 되겠지"

하지만 초급 단계에서는 아래처럼 나누어 기억하는 편이 안전하다.

| 질문 | 먼저 떠올릴 것 |
|---|---|
| 입력이 정책을 이미 만족해야 하나 | `UNNECESSARY` 검증 |
| 입력을 받아서 서비스가 보정해도 되나 | 반올림 mode 선택 |
| 같은 값을 같은 표현으로만 맞추고 싶나 | 정규화(`stripTrailingZeros`) |

## 언제 `UNNECESSARY`가 잘 맞나

아래처럼 "초과 자릿수는 데이터 오류"인 경우에 특히 잘 맞는다.

| 상황 | 왜 `UNNECESSARY`가 맞나 |
|---|---|
| KRW 금액은 정수만 허용 | `100.5`를 101로 몰래 바꾸면 안 된다 |
| 소수 둘째 자리까지만 받는 결제 payload | `19.999`를 서버가 임의로 바꾸면 계약이 흐려진다 |
| 이미 외부에서 반올림된 값만 받아야 하는 정산 단계 | 누가 언제 반올림했는지 경계를 분명히 할 수 있다 |

예를 들면 이렇다.

```java
import java.math.BigDecimal;
import java.math.RoundingMode;

static BigDecimal validateUsdAmount(String raw) {
    return new BigDecimal(raw).setScale(2, RoundingMode.UNNECESSARY);
}

validateUsdAmount("19.99");  // 통과
validateUsdAmount("19.9");   // 통과 -> 19.90
validateUsdAmount("19.999"); // 예외
```

이 코드는 "무조건 2자리 문자열만 받는다"가 아니라 "셋째 자리에서 반올림이 필요하면 입력 자체를 거부한다"를 드러낸다.

## `UNNECESSARY`가 아닌 편이 맞는 경우

반대로 아래 상황은 검증보다 보정 정책이 먼저일 수 있다.

| 상황 | 더 자연스러운 방향 |
|---|---|
| UI 입력에서 편의상 `12.345`를 받아 `12.35`로 보여 줘도 된다 | 명시적 반올림 |
| 내부 계산 결과를 마지막 저장 단계에서 2자리로 내려야 한다 | 저장/표시 경계에서 반올림 |
| 할인/세금 계산 후 remainder 분배 규칙이 따로 있다 | 도메인 반올림 정책 문서화 |

즉 `UNNECESSARY`는 "항상 더 엄격해서 좋은 것"이 아니라, 입력 계약이 엄격할 때 좋은 선택이다.

## `stripTrailingZeros()`와 무엇이 다른가

이 둘은 초급자가 특히 자주 섞는다.

| 메서드 | 먼저 보는 문제 | 예시 질문 |
|---|---|---|
| `setScale(2, UNNECESSARY)` | 허용 자릿수 검증 | `12.345`를 거부해야 하나 |
| `setScale(2, HALF_UP)` | 자릿수 보정 | `12.345`를 `12.35`로 바꿔도 되나 |
| `stripTrailingZeros()` | 표현 정규화 | `1.0`과 `1.00`을 같은 표현으로 볼까 |

짧게 말하면:

- `setScale`은 자릿수 정책
- `stripTrailingZeros()`는 표현 정책

## 초보자 혼동 포인트

- `UNNECESSARY`도 결국 반올림 mode니까 반올림 도구라고만 읽기 쉽다.
- `setScale(2)`가 항상 "소수 둘째 자리로 예쁘게 맞추기"라고 생각하기 쉽다.
- 입력 검증과 출력 포맷팅을 같은 단계에서 처리하려고 하기 쉽다.
- `19.9`처럼 자리가 모자란 값도 거부된다고 오해하기 쉽다. `setScale(2, UNNECESSARY)`는 zero를 붙이는 것만으로 충분하면 통과시킨다.
- `19.90`처럼 trailing zero가 있는 값은 나쁜 입력이라고 오해하기 쉽다. `setScale(2, UNNECESSARY)`는 이런 값도 통과시킨다.
- `1.0`과 `1.00`을 같은 표현으로 맞추는 문제를 `UNNECESSARY`로 해결하려 하기 쉽다. 그건 정규화 쪽 문제다.

## 초급자용 구현 순서

1. 생성 정책부터 고정한다: 문자열이면 문자열 생성자, 이미 `double`이면 `BigDecimal.valueOf(...)`.
2. 도메인이 허용하는 소수 자릿수를 한 문장으로 적는다.
3. 입력은 거부할지, 서버가 보정할지 먼저 정한다.
4. 거부가 맞으면 `setScale(..., UNNECESSARY)`를 입력 경계에 둔다.
5. 표현 통일까지 필요하면 `stripTrailingZeros()`나 출력 정책을 별도로 본다.

## 다음 문서로 연결

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| 입력 생성부터 흔들리지 않게 하고 싶다 | [BigDecimal 생성 정책 입문 브리지](./bigdecimal-construction-policy-beginner-bridge.md) |
| `1.0`과 `1.00`을 같은 표현으로 볼지 고민된다 | [BigDecimal `stripTrailingZeros()` 입력 경계 브리지](./bigdecimal-striptrailingzeros-input-boundary-bridge.md) |
| map key 동등성 정책까지 같이 점검하고 싶다 | [BigDecimal Key 정책 30초 체크리스트](./bigdecimal-key-policy-30-second-checklist.md) |
| `MathContext`, precision, canonicalization까지 깊게 보고 싶다 | [BigDecimal `MathContext`, `stripTrailingZeros()`, and Canonicalization Traps](./bigdecimal-mathcontext-striptrailingzeros-canonicalization-traps.md) |

## 한 줄 정리

`setScale(..., RoundingMode.UNNECESSARY)`는 반올림 편의 함수보다 먼저 "이 입력은 반올림 없이 우리 자릿수 계약으로 표현 가능해야 한다"를 선언하는 beginner-friendly 검증 도구다.
