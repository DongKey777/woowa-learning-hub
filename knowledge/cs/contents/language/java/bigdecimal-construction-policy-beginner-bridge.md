# BigDecimal 생성 정책 입문 브리지

> 한 줄 요약: 초급자 기준으로는 "`new BigDecimal(double)`은 피하고, 입력이 문자열이면 문자열 생성자, 이미 `double`이라면 `BigDecimal.valueOf(double)`"만 먼저 고정해도 입력 흔들림을 크게 줄일 수 있다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README](../README.md)
- [BigDecimal `setScale()` 검증 입문: `RoundingMode.UNNECESSARY`를 입력 정책으로 보기](./bigdecimal-setscale-unnecessary-validation-primer.md)
- [BigDecimal `stripTrailingZeros()` 입력 경계 브리지](./bigdecimal-striptrailingzeros-input-boundary-bridge.md)
- [BigDecimal Key 정책 30초 체크리스트](./bigdecimal-key-policy-30-second-checklist.md)
- [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md)
- [BigDecimal Money Equality, Rounding, and Serialization Pitfalls](./bigdecimal-money-equality-rounding-serialization-pitfalls.md)
- [Floating-Point Precision, `NaN`, `Infinity`, and Serialization Pitfalls](./floating-point-precision-nan-infinity-serialization-pitfalls.md)

retrieval-anchor-keywords: bigdecimal construction policy beginner, new bigdecimal double vs string vs valueof, bigdecimal input stability beginner, bigdecimal valueof beginner bridge, bigdecimal string constructor beginner, new bigdecimal double pitfall beginner, java bigdecimal 생성 정책, 자바 bigdecimal double 생성자 피하기, 자바 bigdecimal valueof 문자열 차이, 자바 bigdecimal 입력 경계, 자바 bigdecimal 초급 브리지, bigdecimal construction policy beginner bridge basics, bigdecimal construction policy beginner bridge beginner, bigdecimal construction policy beginner bridge intro, java basics

## 먼저 잡을 멘탈 모델

초급자 기준으로는 이 한 줄이 제일 안전하다.

> `BigDecimal` 생성은 "숫자를 어떻게 계산할까?"보다 먼저 "입력을 어떤 모양으로 안전하게 받았나?"를 정하는 문제다.

- 문자열 입력이면 문자열 그대로 받는 편이 가장 읽기 쉽다.
- 이미 `double` 값이 들어왔다면 `valueOf`가 `new BigDecimal(double)`보다 예측 가능하다.
- 계산 전에 생성 정책부터 고정해야 이후 정규화, 비교, 저장 정책도 덜 흔들린다.

## 먼저 결론

| 지금 가진 입력 | 초급자용 첫 선택 | 이유 |
|---|---|---|
| `"19.99"` 같은 문자열 | `new BigDecimal("19.99")` | 사람이 본 십진 표현을 그대로 옮기기 쉽다 |
| `19.99d` 같은 `double` | `BigDecimal.valueOf(19.99d)` | `new BigDecimal(double)`보다 덜 놀랍다 |
| 아직 API를 설계 중 | 가능하면 처음부터 문자열/정수 minor unit로 받기 | 경계에서 뜻이 더 분명해진다 |

초급 단계에서는 아래 한 줄로 기억해도 충분하다.

> 문자열이 있으면 문자열, 이미 `double`이면 `valueOf`, `new BigDecimal(double)`은 기본값으로 고르지 않는다.

## 왜 `new BigDecimal(double)`이 초급자에게 흔들리나

`double`은 많은 십진수를 정확히 저장하지 못한다.
그래서 `new BigDecimal(double)`은 "내가 화면에서 본 숫자"가 아니라 "`double` 안에 들어 있던 근사값"을 그대로 옮길 수 있다.

짧게 보면 이렇다.

```java
import java.math.BigDecimal;

System.out.println(new BigDecimal(0.1d));
System.out.println(BigDecimal.valueOf(0.1d));
System.out.println(new BigDecimal("0.1"));
```

초급자 관점에서 중요한 건 "정확한 내부 규칙"보다 출력 감각이다.

- `new BigDecimal(0.1d)`는 예상보다 긴 값으로 보여 초급자를 놀라게 하기 쉽다.
- `BigDecimal.valueOf(0.1d)`는 보통 사람이 기대한 십진 표현 쪽에 더 가깝다.
- `new BigDecimal("0.1")`은 애초에 문자열 `"0.1"`을 기준으로 시작한다.

## 10초 비교표

| 생성 방식 | 초급자용 해석 | 첫 선택으로 권장? |
|---|---|---|
| `new BigDecimal(double)` | 이미 흔들릴 수 있는 `double` 근사값을 그대로 옮긴다 | 아니오 |
| `BigDecimal.valueOf(double)` | `double`에서 시작하지만 보통 더 예측 가능한 십진 표현으로 간다 | 예, `double`만 있을 때 |
| `new BigDecimal(String)` | 입력 문자열을 기준으로 바로 만든다 | 예, 문자열 입력일 때 |

## 가장 흔한 입력 경계 예시

### 1. 사용자 입력이나 JSON이 문자열일 때

이 경우는 보통 문자열 생성자가 가장 단순하다.

```java
BigDecimal amount = new BigDecimal("19.99");
```

- "사용자가 입력한 십진수"라는 뜻이 코드에 바로 드러난다.
- 이후 정규화가 필요하면 생성 직후 한 번만 이어 붙이면 된다.

```java
BigDecimal amount = new BigDecimal("19.99").stripTrailingZeros();
```

### 2. 이미 계산 결과가 `double`로 들어왔을 때

경계를 당장 못 바꾼다면 `valueOf`가 첫 방어선이다.

```java
BigDecimal amount = BigDecimal.valueOf(19.99d);
```

이건 "근본적으로 `double`이 안전하다"는 뜻이 아니다.

- 이미 `double`이 된 뒤에는 근사값 문제가 앞단에서 시작됐을 수 있다.
- 그래도 `new BigDecimal(double)`로 한 번 더 놀라운 표현을 만드는 일은 줄여 준다.

## 초급자용 선택 순서

1. 입력이 원래 문자열인지 먼저 본다.
2. 문자열이면 문자열 생성자를 쓴다.
3. 이미 `double`밖에 없다면 `valueOf`를 쓴다.
4. 그 다음에야 `stripTrailingZeros()`나 `setScale(...)` 같은 후속 정책을 붙인다.

핵심은 생성 정책과 후속 정책을 섞지 않는 것이다.

- 생성 정책: 어떤 입력을 어떤 값으로 받아들일까
- 정규화 정책: `1.0`과 `1.00`을 같은 표현으로 맞출까
- 자릿수 정책: 몇 자리까지 허용/반올림할까

## 초보자 혼동 포인트

- `valueOf(double)`가 있으니 `double` 자체도 정확하다고 생각하기 쉽다.
- `new BigDecimal("0.10")`과 `BigDecimal.valueOf(0.10d)`가 항상 같은 문자열 표현을 줄 거라고 기대하기 쉽다.
- `stripTrailingZeros()` 문제와 생성 문제를 같은 것으로 섞기 쉽다.
- "어차피 나중에 `setScale(2)` 하면 되지"라고 생각하기 쉽지만, 생성 시점의 입력 흔들림과 반올림 정책은 다른 문제다.

## 다음 문서로 연결

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| `setScale(2, UNNECESSARY)`를 반올림이 아니라 입력 검증으로 이해하고 싶다 | [BigDecimal `setScale()` 검증 입문: `RoundingMode.UNNECESSARY`를 입력 정책으로 보기](./bigdecimal-setscale-unnecessary-validation-primer.md) |
| 입력 뒤에 `1.0`과 `1.00`을 같은 표현으로 맞출지 고민된다 | [BigDecimal `stripTrailingZeros()` 입력 경계 브리지](./bigdecimal-striptrailingzeros-input-boundary-bridge.md) |
| `HashMap`/`TreeMap`에서 왜 같은 숫자가 다르게 보이지? | [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md) |
| 돈 계산, 반올림, 직렬화까지 같이 봐야 한다 | [BigDecimal Money Equality, Rounding, and Serialization Pitfalls](./bigdecimal-money-equality-rounding-serialization-pitfalls.md) |
| 왜 `double` 자체가 흔들리는지부터 보고 싶다 | [Floating-Point Precision, `NaN`, `Infinity`, and Serialization Pitfalls](./floating-point-precision-nan-infinity-serialization-pitfalls.md) |

## 한 줄 정리

초급자에게 가장 안전한 `BigDecimal` 생성 정책은 "문자열이면 문자열 생성자, 이미 `double`이면 `valueOf`, `new BigDecimal(double)`은 기본 선택지에서 제외"다.
