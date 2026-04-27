# Money Value Object Basics

> 한 줄 요약: `BigDecimal`은 "정확한 숫자"를 다루는 데는 좋지만, 돈의 의미까지 자동으로 담아 주지는 않는다. 금액이 통화, 허용 소수 자릿수, 반올림 규칙과 함께 움직이기 시작하면 `Money` 같은 전용 value object가 더 안전하다.

**난이도: 🟢 Beginner**

관련 문서:

- [BigDecimal 생성 정책 입문 브리지](./bigdecimal-construction-policy-beginner-bridge.md)
- [BigDecimal 미니 드릴: `1.0` vs `1.00` in `HashSet`/`TreeSet`/`TreeMap`](./bigdecimal-1-0-vs-1-00-collections-mini-drill.md)
- [Money Equality Policy Mini Drill](./money-equality-policy-mini-drill.md)
- [BigDecimal Money Equality, Rounding, and Serialization Pitfalls](./bigdecimal-money-equality-rounding-serialization-pitfalls.md)
- [Record and Value Object Equality](./record-value-object-equality-basics.md)
- [Value Object Invariants, Canonicalization, and Boundary Design](./value-object-invariants-canonicalization-boundary-design.md)
- [불변 객체와 방어적 복사 입문](./java-immutable-object-basics.md)

retrieval-anchor-keywords: money value object basics, java money type beginner, bigdecimal not enough money, currency plus amount value object, money scale policy beginner, java monetary amount primer, raw bigdecimal vs money, java value object money example, money currency rounding beginner, 자바 money value object, 자바 bigdecimal 돈 타입, 통화 금액 값 객체, 금액 스케일 정책 입문

## 먼저 잡을 멘탈 모델

처음에는 이렇게 구분하면 된다.

- `BigDecimal`은 "소수 오차를 줄인 숫자 타입"이다.
- `Money`는 "돈으로서의 규칙을 묶은 도메인 타입"이다.

즉 `BigDecimal`은 재료이고, `Money`는 그 재료에 도메인 규칙을 입힌 완성품에 가깝다.

## 언제 raw `BigDecimal`만으로도 괜찮나

아래처럼 아직 "숫자 계산 연습" 수준이면 `BigDecimal`만으로도 충분할 수 있다.

| 상황 | raw `BigDecimal`로도 괜찮은 이유 |
|---|---|
| 할인율, 세율 계산 예제를 연습 중 | 아직 통화와 저장 정책이 없다 |
| 한 메서드 안에서 잠깐 계산하고 바로 끝난다 | 값 의미가 넓게 퍼지지 않는다 |
| 통화가 하나로 고정되고 화면 출력도 단순하다 | 규칙이 거의 늘어나지 않는다 |

하지만 이 상태가 오래가면 보통 규칙이 호출자 쪽으로 새기 시작한다.

## `BigDecimal`만으로 부족해지는 순간

다음 중 두세 가지가 같이 나오면 전용 `Money` 타입을 고민할 시점이다.

| 신호 | 왜 위험한가 |
|---|---|
| 메서드마다 `setScale(...)`가 반복된다 | 자릿수 정책이 흩어진다 |
| `KRW`, `USD`를 문자열이나 주석으로만 구분한다 | 통화가 값에서 빠진다 |
| `"1.0"`과 `"1.00"`을 같은 돈으로 볼지 헷갈린다 | equality 기준이 흔들린다 |
| 저장/응답/로그마다 포맷이 조금씩 다르다 | 직렬화 계약이 퍼진다 |
| `BigDecimal amount` 파라미터가 너무 많다 | "이 숫자가 돈인지 비율인지" 코드만 보고 모호하다 |

핵심은 한 줄이다.

> 숫자 자체보다 "이 숫자를 어떤 돈으로 해석할까"가 중요해지는 순간, `BigDecimal` 하나로는 설명력이 부족해진다.

## 왜 통화와 scale 정책을 타입 안에 두려 하나

돈은 보통 숫자 하나로 끝나지 않는다.

- 어떤 통화인가
- 소수 몇 자리까지 허용할 것인가
- 입력이 그 자릿수를 넘으면 거절할지, 반올림할지
- 비교할 때 표현 차이까지 볼지, 값만 볼지

이 규칙이 타입 밖으로 나가면 이런 코드가 생긴다.

```java
BigDecimal price = new BigDecimal("12.30");
BigDecimal tax = price.multiply(new BigDecimal("0.10")).setScale(2, RoundingMode.HALF_UP);
BigDecimal total = price.add(tax).setScale(2, RoundingMode.HALF_UP);
```

겉으로는 동작하지만, 다음 질문의 답이 코드에 없다.

- 이 값은 KRW인가 USD인가
- 왜 2자리인가
- 입력이 `12.345`면 예외여야 하나, 반올림이어야 하나

이런 질문을 타입이 대신 답하게 만드는 것이 money value object의 역할이다.

## 비교 예시: raw 숫자 vs money 타입

### raw `BigDecimal`만 쓰는 코드

```java
import java.math.BigDecimal;

public record LineItem(String name, BigDecimal price) {
}
```

이 상태에서는 호출자가 스스로 기억해야 한다.

- price 통화는 무엇인지
- 소수 자릿수는 몇 자리인지
- `1.0`과 `1.00`을 같은 가격으로 볼지

### 간단한 `Money` value object로 감싼 코드

```java
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Currency;

public record Money(Currency currency, BigDecimal amount) {
    public Money {
        if (currency == null || amount == null) {
            throw new IllegalArgumentException("currency and amount are required");
        }

        int scale = currency.getDefaultFractionDigits();
        amount = amount.setScale(scale, RoundingMode.UNNECESSARY);
    }

    public static Money of(String currencyCode, String amountText) {
        return new Money(
            Currency.getInstance(currencyCode),
            new BigDecimal(amountText)
        );
    }
}
```

이 예시는 초급자 기준으로 두 가지를 한 번에 보여 준다.

- 통화와 금액이 항상 같이 다닌다
- 허용 자릿수를 생성 시점에 바로 검사한다

`RoundingMode.UNNECESSARY`는 "몰래 반올림하지 말고, 잘못된 자릿수면 바로 알려 달라"는 입력 정책으로 읽으면 된다.

## 초급자가 바로 체감하는 장점

| 장점 | 실제로 줄어드는 혼동 |
|---|---|
| 파라미터 의미가 또렷해진다 | `BigDecimal`이 돈인지 비율인지 덜 헷갈린다 |
| 생성 시 검증을 한곳에 모은다 | 여기저기서 `setScale(2)`를 반복하지 않는다 |
| equality 경계가 선명해진다 | 금액 비교 기준을 타입 설계로 고정할 수 있다 |
| 테스트 읽기가 쉬워진다 | `"KRW 12000"` 같은 도메인 의미가 드러난다 |

## 자주 나오는 질문

### Q. 통화가 항상 KRW 하나면 `Money`가 과한가요?

초기엔 그럴 수 있다.
하지만 아래 중 하나가 생기면 다시 볼 가치가 있다.

- 금액 validation이 여러 곳에 퍼진다
- 같은 금액 타입이 API, DB, 계산 로직 사이를 자주 오간다
- 자릿수 정책이나 반올림 정책이 반복된다

즉 통화가 하나여도 "돈 규칙"이 커지면 value object가 도움이 된다.

### Q. `Money` 안에서 무조건 반올림하면 되나요?

보통은 신중해야 한다.
입력 검증과 계산 반올림은 다른 문제라서, 초급 단계에서는 먼저 "입력 자릿수를 강제하는 생성자"부터 두는 편이 안전하다.

- 생성 시 검증: 잘못된 입력을 빨리 막는다
- 계산 시 반올림: 비즈니스 정책에 따라 별도 메서드나 서비스에서 결정한다

### Q. `Money`면 `BigDecimal` 문제를 전부 해결하나요?

아니다.
계산은 여전히 `BigDecimal`로 한다. 다만 통화, equality, 자릿수 정책을 "호출자 기억"이 아니라 "타입 규칙"으로 옮겨 준다.

## 한 장 체크리스트

- `BigDecimal amount`가 여러 계층을 돌아다닌다
- 통화가 값과 분리돼 따로 전달된다
- `setScale(...)`가 여러 메서드에 반복된다
- 금액 비교 기준을 설명하기가 어렵다

위 항목이 보이면 raw `BigDecimal`에서 `Money` value object로 한 단계 올릴 시점일 가능성이 크다.

## 다음 읽기

| 지금 궁금한 질문 | 다음 문서 |
|---|---|
| `BigDecimal` 입력을 처음부터 어떻게 받는 게 안전한가 | [BigDecimal 생성 정책 입문 브리지](./bigdecimal-construction-policy-beginner-bridge.md) |
| `1.0`과 `1.00`이 컬렉션에서 왜 다르게 보이나 | [BigDecimal 미니 드릴: `1.0` vs `1.00` in `HashSet`/`TreeSet`/`TreeMap`](./bigdecimal-1-0-vs-1-00-collections-mini-drill.md) |
| `Money`가 raw `BigDecimal`보다 set/map key로 왜 안전한가 | [Money Equality Policy Mini Drill](./money-equality-policy-mini-drill.md) |
| value object의 invariant와 canonicalization은 어디까지 들어가나 | [Value Object Invariants, Canonicalization, and Boundary Design](./value-object-invariants-canonicalization-boundary-design.md) |
| 돈 계산의 더 까다로운 함정까지 같이 보고 싶다 | [BigDecimal Money Equality, Rounding, and Serialization Pitfalls](./bigdecimal-money-equality-rounding-serialization-pitfalls.md) |

## 한 줄 정리

`BigDecimal`은 돈 계산의 좋은 재료지만, 통화와 자릿수 정책이 중요해지는 순간부터는 `Money` 같은 value object가 도메인 규칙을 더 안전하게 묶어 준다.
