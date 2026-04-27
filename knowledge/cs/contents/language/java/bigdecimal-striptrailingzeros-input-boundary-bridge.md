# BigDecimal `stripTrailingZeros()` 입력 경계 브리지

> 한 줄 요약: `stripTrailingZeros()`는 "숫자 값 보정" 도구가 아니라 "입력 경계에서 같은 값을 같은 표현으로 맞출지"를 선택할 때 쓰는 정규화 도구다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README](../README.md)
- [BigDecimal 생성 정책 입문 브리지](./bigdecimal-construction-policy-beginner-bridge.md)
- [BigDecimal `setScale()` 검증 입문: `RoundingMode.UNNECESSARY`를 입력 정책으로 보기](./bigdecimal-setscale-unnecessary-validation-primer.md)
- [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md)
- [BigDecimal Key 정책 30초 체크리스트](./bigdecimal-key-policy-30-second-checklist.md)
- [BigDecimal 미니 드릴: `1.0` vs `1.00` in `HashSet`/`TreeSet`/`TreeMap`](./bigdecimal-1-0-vs-1-00-collections-mini-drill.md)
- [BigDecimal 조회 전용 미니 드릴: `contains`/`get` in `HashMap` vs `TreeMap`](./bigdecimal-hashmap-treemap-lookup-mini-drill.md)
- [Value Object Invariants, Canonicalization, and Boundary Design](./value-object-invariants-canonicalization-boundary-design.md)
- [BigDecimal `MathContext`, `stripTrailingZeros()`, and Canonicalization Traps](./bigdecimal-mathcontext-striptrailingzeros-canonicalization-traps.md)

retrieval-anchor-keywords: bigdecimal striptrailingzeros beginner, java bigdecimal normalization beginner, bigdecimal input boundary policy, bigdecimal canonicalization entrypoint, bigdecimal 1.0 1.00 normalization, striptrailingzeros toplainstring policy, bigdecimal beginner bridge, bigdecimal boundary contract, bigdecimal normalize at input, bigdecimal scale meaning beginner, bigdecimal input normalization checklist, bigdecimal key policy checklist, bigdecimal boundary policy example, bigdecimal normalize once at input, bigdecimal setscale vs striptrailingzeros beginner

## 먼저 잡을 멘탈 모델

초급자 기준으로는 이 한 줄이 제일 안전하다.

> `stripTrailingZeros()`는 "값을 고치는 함수"가 아니라 "입구에서 표현을 맞춰 둘지"를 결정할 때 쓰는 함수다.

- 값 자체(`compareTo`)를 바꾸는 게 아니다.
- 표현(`equals`/문자열 출력)이 달라질 수 있다.
- 그래서 계산 중간이 아니라 입력 경계에서 정책으로 쓰는 편이 덜 헷갈린다.

## 가장 먼저 고를 정책

초급자라면 구현보다 이 질문 두 개를 먼저 고정하면 된다.

| 먼저 정할 것 | `Yes`라면 | `No`라면 |
|---|---|---|
| `1.0`, `1.00`, `1`을 같은 입력으로 볼까? | 입력 직후 한 번 정규화 | 원본 scale을 보존한다 |
| 비교/저장 기준을 팀 전체에서 통일할까? | 생성 함수나 팩토리 한 곳에서 처리 | 호출자마다 raw 값을 그대로 다룬다 |

핵심은 "`stripTrailingZeros()`를 쓸까?"보다 "정규화를 어디서 한 번만 할까?"다.

## 언제 쓰고, 언제 안 쓰나

| 상황 | 초급자용 첫 선택 | 이유 |
|---|---|---|
| `1.0`, `1.00`, `1`을 같은 금액으로 보고 싶다 | 입력 직후 한 번 정규화 | hash/sorted 컬렉션 결과 차이를 줄이기 쉽다 |
| 소수 자릿수 자체가 의미다 (예: UI 표시 계약) | 원본 표현 보존, 정규화는 별도 값으로만 | `1.0`과 `1.00` 의미를 잃지 않는다 |
| 계산 단계마다 정규화하고 싶다 | 기본은 피한다 | 중간 표현 변경이 디버깅/직렬화 혼동을 키울 수 있다 |

## `stripTrailingZeros()`가 아닌 것

초급 단계에서는 아래 셋을 먼저 분리해서 기억하면 덜 헷갈린다.

| 내가 하려는 일 | 먼저 떠올릴 것 | 왜 다른가 |
|---|---|---|
| 같은 입력을 같은 표현으로 맞추기 | `stripTrailingZeros()` | 정규화다 |
| 소수 자릿수를 강제로 맞추기 | `setScale(...)` | 반올림/검증 정책이다 |
| 화면이나 로그에 보기 좋게 찍기 | `toPlainString()` 같은 출력 정책 | 표시 정책이다 |

즉 `stripTrailingZeros()`는 "보기 좋게 만들기"보다 "입구에서 같은 표현으로 모을지"에 더 가깝다.

## 10초 비교: 입력을 그대로 둘 때 vs 입구에서 맞출 때

| 입력 | 그대로 보관 | 입력 경계에서 `stripTrailingZeros()` |
|---|---|---|
| `"1.0"` | `1.0` | `1` |
| `"1.00"` | `1.00` | `1` |
| `"10.500"` | `10.500` | `10.5` |

이 표에서 봐야 할 것은 "숫자가 바뀌었다"가 아니라 "표현이 한쪽으로 모였다"는 점이다.

## 컬렉션 key나 API 경계 직전에 무엇이 도움이 되나

초급자라면 아래처럼 먼저 나누면 된다.

| 지금 하려는 일 | 먼저 보는 메서드 | 왜 이쪽이 맞나 |
|---|---|---|
| `HashMap` key에서 `1`, `1.0`, `1.00`을 같은 값으로 모으고 싶다 | `stripTrailingZeros()` | trailing zero를 걷어 표현을 한쪽으로 모으는 정규화 문제다 |
| API payload가 "소수 둘째 자리까지만 허용"이어야 한다 | `setScale(2, UNNECESSARY)` | 같은 값 묶기가 아니라 허용 자릿수 검증 문제다 |
| API 바깥으로 항상 `12.30`처럼 2자리로 내보내야 한다 | `setScale(2, ...)` + 출력 정책 | canonical key보다 직렬화/표시 계약이 중요하다 |

한 줄로 줄이면 이렇다.

- `stripTrailingZeros()`는 "`1.0`과 `1`을 같은 key로 볼까?"에 가깝다.
- `setScale(...)`는 "이 값은 소수 몇 자리까지 허용할까?"에 가깝다.

즉 collection key와 API boundary를 한 번에 생각할 때도,
"같은 값으로 묶기"와 "허용 자릿수 고정"은 다른 문제로 보는 편이 안전하다.

## 30초 follow-up: key와 API boundary를 같이 잡는 예시

예를 들어 API가 USD 금액을 받고, 내부 캐시 key도 같은 기준으로 쓰고 싶다고 하자.

```java
import java.math.BigDecimal;
import java.math.RoundingMode;

static BigDecimal normalizeUsdAmount(String raw) {
    BigDecimal validated = new BigDecimal(raw)
            .setScale(2, RoundingMode.UNNECESSARY);
    return validated.stripTrailingZeros();
}
```

이 코드는 두 단계를 분리해서 읽어야 한다.

1. `setScale(2, UNNECESSARY)`:
API 경계에서 "소수 둘째 자리까지만 허용"을 검증한다.

2. `stripTrailingZeros()`:
검증을 통과한 값들 중 `1.20`과 `1.2`처럼 같은 수를 같은 key 표현으로 모은다.

초급자 관점에서 중요한 점은 "둘 중 하나만 만능으로 쓰지 않는다"는 것이다.

- 자릿수 계약이 먼저면 `setScale(...)`
- key canonicalization이 먼저면 `stripTrailingZeros()`
- 둘 다 필요하면 순서를 나눠서 읽히게 둔다

## 언제 특히 도움이 되나

| 상황 | 왜 도움 되나 |
|---|---|
| `HashMap<BigDecimal, ...>`에서 `"1.0"`로 저장하고 `"1"`로 조회하는 혼동을 줄이고 싶다 | `stripTrailingZeros()`를 입력 경계 한 곳에 두면 lookup 기준이 단순해진다 |
| 외부 API에 `12.345` 같은 값을 조용히 반올림하지 말고 거부하고 싶다 | `setScale(..., UNNECESSARY)`가 계약 위반을 바로 드러낸다 |
| 내부에선 같은 key로 묶고, 외부엔 고정 자릿수 문자열을 보내야 한다 | 내부 canonical value와 외부 출력 정책을 분리할 수 있다 |

## 30초 예제: 입력 경계에서만 정규화하기

```java
import java.math.BigDecimal;
import java.util.HashSet;
import java.util.Set;

static BigDecimal normalizeAtInput(String raw) {
    return new BigDecimal(raw).stripTrailingZeros();
}

Set<BigDecimal> amounts = new HashSet<>();
amounts.add(normalizeAtInput("1.0"));
amounts.add(normalizeAtInput("1.00"));

System.out.println(amounts.size()); // 1
```

핵심은 "어디서 호출하느냐"다.

- 입력 경계에서 한 번: 정책이 읽기 쉽다.
- 서비스 곳곳에서 임의 호출: 팀마다 결과 해석이 달라진다.

## 초급자용 체크리스트

- `BigDecimal` 생성 정책부터 먼저 고정한다: 문자열 또는 `BigDecimal.valueOf(...)`.
- "같은 값" 기준이 scale 무시인지 보존인지 먼저 적는다.
- 정규화가 필요하면 입력 함수 한 곳에서만 호출한다.
- 표시 문자열이 중요하면 원본 문자열 또는 별도 출력 정책을 함께 둔다.

## 자주 헷갈리는 포인트

- `stripTrailingZeros()`를 쓰면 `equals()`가 자동으로 안전해진다고 생각하기 쉽다.
- `setScale(2)`만 하면 key 문제까지 같이 해결된다고 생각하기 쉽다. 자릿수 고정과 key canonicalization은 별개다.
- 정규화 후 문자열 표현은 기대와 다를 수 있어, 문자열 계약은 `toPlainString()` 같은 출력 정책과 함께 정해야 한다.
- `stripTrailingZeros()`와 `setScale(...)`를 같은 종류의 함수로 생각하기 쉽다. 전자는 정규화, 후자는 자릿수 정책이다.
- "정규화 = 무조건 정답"이 아니다. 도메인이 scale 의미를 보존해야 하면 오히려 원본 유지가 정답이다.
- `new BigDecimal(double)` 입력 흔들림은 별개 문제다. 생성 정책(문자열/`valueOf`)을 먼저 고정해야 한다.

## 다음 문서로 연결

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| `new BigDecimal(double)` vs 문자열 vs `valueOf`부터 먼저 고르고 싶다 | [BigDecimal 생성 정책 입문 브리지](./bigdecimal-construction-policy-beginner-bridge.md) |
| `setScale(2, UNNECESSARY)`를 반올림이 아니라 입력 검증으로 이해하고 싶다 | [BigDecimal `setScale()` 검증 입문: `RoundingMode.UNNECESSARY`를 입력 정책으로 보기](./bigdecimal-setscale-unnecessary-validation-primer.md) |
| PR 전에 `1.0` vs `1` key 정책과 테스트 항목만 빠르게 점검하고 싶다 | [BigDecimal Key 정책 30초 체크리스트](./bigdecimal-key-policy-30-second-checklist.md) |
| 왜 `HashSet`/`TreeSet`/`TreeMap` 결과가 다르지? | [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md) |
| 조회(`contains`/`get`) 결과만 빠르게 손예측하고 싶다 | [BigDecimal 조회 전용 미니 드릴: `contains`/`get` in `HashMap` vs `TreeMap`](./bigdecimal-hashmap-treemap-lookup-mini-drill.md) |
| `stripTrailingZeros()`의 고급 함정(MathContext, 표기, 계약)을 보고 싶다 | [BigDecimal `MathContext`, `stripTrailingZeros()`, and Canonicalization Traps](./bigdecimal-mathcontext-striptrailingzeros-canonicalization-traps.md) |

## 한 줄 정리

`stripTrailingZeros()`는 "고급 트릭"보다 먼저 "입력 경계 정책"으로 이해하면 초급 단계 혼동을 크게 줄일 수 있다.
