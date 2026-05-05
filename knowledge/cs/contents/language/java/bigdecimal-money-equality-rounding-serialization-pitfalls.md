---
schema_version: 3
title: '`BigDecimal` Money Equality, Rounding, and Serialization Pitfalls'
concept_id: language/bigdecimal-money-equality-rounding-serialization-pitfalls
canonical: true
category: language
difficulty: advanced
doc_role: primer
level: advanced
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- bigdecimal-equals-vs-compareto
- money-value-object-boundary
- rounding-boundary-policy
- serialization-canonicalization
aliases:
- bigdecimal money
- monetary amount policy
- 금액 scale 정책
- money rounding contract
- bigdecimal serialization money
- compareto equals money amount
symptoms:
- 결제 금액은 같은데 Set이나 캐시 키 결과가 다르게 나와
- 1.0과 1.00 때문에 중복 결제 방지 키가 자꾸 어긋나
- JSON이나 DB를 한번 거치면 금액 비교가 이상해져
intents:
- definition
prerequisites:
- language/bigdecimal-construction-policy-beginner-bridge
- language/money-value-object-basics
next_docs:
- language/bigdecimal-mathcontext-striptrailingzeros-canonicalization-traps
- language/serialization-compatibility-serial-version-uid
linked_paths:
- contents/language/java/bigdecimal-construction-policy-beginner-bridge.md
- contents/language/java/money-value-object-basics.md
- contents/language/java/bigdecimal-sorted-collection-bridge.md
- contents/language/java/bigdecimal-mathcontext-striptrailingzeros-canonicalization-traps.md
- contents/language/java/io-nio-serialization.md
- contents/language/java/serialization-compatibility-serial-version-uid.md
- contents/language/java/record-serialization-evolution.md
- contents/language/java-equals-hashcode-comparable-contracts.md
confusable_with:
- language/bigdecimal-sorted-collection-bridge
- language/money-value-object-basics
forbidden_neighbors: []
expected_queries:
- 결제 금액을 BigDecimal로 다룰 때 equals와 compareTo를 어떻게 나눠 써야 해?
- 금액 반올림은 계산 중간에 해야 해 마지막에 해야 해?
- 1.0과 1.00 때문에 idempotency key가 달라지는 문제를 정리해줘
- BigDecimal 금액을 JSON 문자열로 보내는 게 왜 더 안전할 수 있어?
- DB 저장 후 scale이 바뀌면 어떤 버그가 생기는지 알고 싶어
contextual_chunk_prefix: |
  이 문서는 Java 학습자가 금액 값을 BigDecimal로 다룰 때 숫자
  동일성과 표현 동일성, 반올림 경계, 직렬화 계약을 함께 처음부터
  정확히 잡는 primer다. 결제 금액은 같은데 캐시 키가 달라짐, 1.0과
  1.00 중복 방지 키 어긋남, 계산 중간 반올림 시점, JSON이나 DB를 거친
  뒤 값 표기가 달라짐 같은 자연어 paraphrase가 본 문서의 money 계약
  함정에 매핑된다.
---
# `BigDecimal` Money Equality, Rounding, and Serialization Pitfalls

> 한 줄 요약: 금액은 숫자 하나가 아니라 통화, scale, 반올림 규칙, 직렬화 계약까지 포함한 도메인 값이다. `BigDecimal`의 `equals()`/`compareTo()` 차이와 경계별 반올림 정책을 분리하지 않으면 결제, 정산, 캐시, 메시징에서 조용히 불일치가 쌓인다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [BigDecimal 생성 정책 입문 브리지](./bigdecimal-construction-policy-beginner-bridge.md)
> - [Money Value Object Basics](./money-value-object-basics.md)
> - [Java `equals`, `hashCode`, `Comparable` 계약](../java-equals-hashcode-comparable-contracts.md)
> - [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md)
> - [BigDecimal `MathContext`, `stripTrailingZeros()`, and Canonicalization Traps](./bigdecimal-mathcontext-striptrailingzeros-canonicalization-traps.md)
> - [Java IO, NIO, Serialization, JSON Mapping](./io-nio-serialization.md)
> - [Serialization Compatibility and `serialVersionUID`](./serialization-compatibility-serial-version-uid.md)
> - [Record Serialization Evolution](./record-serialization-evolution.md)

> retrieval-anchor-keywords: BigDecimal money, monetary amount, scale, precision, `equals`, `compareTo`, `hashCode`, `setScale`, `RoundingMode`, divide, currency, JSON serialization, Jackson BigDecimal, scientific notation, minor unit, payment, settlement, idempotency, MathContext, stripTrailingZeros

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

금액 도메인에서 `BigDecimal`은 "정밀한 숫자"라서 쓰는 것이지,
"돈 문제를 자동으로 안전하게 처리해주는 타입"이라서 쓰는 것은 아니다.

특히 백엔드 시스템에서는 다음 네 가지를 같이 설계해야 한다.

- 값의 의미: 숫자만 같은가, 표현까지 같은가
- 반올림 시점: 계산 중간마다 반올림할지, 마지막에만 반올림할지
- 직렬화 계약: JSON, DB, 캐시, 메시지에서 같은 값으로 보장되는가
- 도메인 모델: 통화와 scale을 값 객체가 강제하는가

핵심 오해는 보통 여기서 나온다.

- `new BigDecimal("1.0")`과 `new BigDecimal("1.00")`는 숫자적으로는 같아 보인다
- 하지만 `equals()`는 `false`이고 `compareTo()`는 `0`이다
- 즉 "금액이 같다"는 정의를 정하지 않으면 컬렉션, 캐시 키, 중복 제거, 서명 검증이 각각 다르게 동작할 수 있다

## 깊이 들어가기

### 1. `BigDecimal`은 값과 표현을 함께 들고 있다

`BigDecimal`은 unscaled value와 scale을 함께 가진다.
그래서 `1.0`과 `1.00`은 같은 수학적 값이어도 같은 표현은 아니다.

이 차이는 다음으로 이어진다.

- `compareTo()`는 수학적 크기를 본다
- `equals()`와 `hashCode()`는 scale까지 포함한 표현을 본다

즉 "금액 비교"와 "금액을 key로 다루는 일"은 같은 문제가 아니다.

결제 승인 금액 비교에는 `compareTo()`가 맞을 수 있다.
반면 캐시 키, 중복 결제 방지 키, 서명 대상 문자열에는 canonical representation이 필요하다.

### 2. 돈은 `BigDecimal` 하나로 끝나지 않는다

실무 금액은 보통 다음 요소를 함께 가져야 한다.

- 금액
- 통화
- 허용 scale
- 반올림 정책
- 입출력 포맷

예를 들어 KRW는 소수점이 없는 경우가 많고,
USD는 보통 소수 둘째 자리까지 표현한다.
세금, 수수료, 환율 계산은 내부 계산 scale을 더 크게 잡고 마지막에 표시 scale로 내리는 경우가 많다.

즉 `BigDecimal`만 노출하면 도메인 규칙이 호출자에게 흩어진다.
팀마다 `setScale(2)`를 제각각 넣기 시작하면 같은 계산도 결과가 달라진다.

### 3. 반올림은 "어느 모드인가"보다 "어디서 한 번 하는가"가 더 중요하다

`RoundingMode.HALF_UP`이냐 `HALF_EVEN`이냐도 중요하지만,
그보다 먼저 반올림 시점을 통제해야 한다.

중간 단계마다 반올림하면 오차가 누적된다.

- 항목별 세금을 먼저 반올림한 뒤 합산
- 합산 후 한 번만 반올림

이 둘은 결과가 다를 수 있다.

정산 시스템에서는 보통 다음을 분리한다.

- 계산용 scale: 내부 계산에서 충분히 크게 유지
- 저장/표시용 scale: 외부에 노출할 때만 축소
- 분배 규칙: 1원, 1센트의 remainder를 어떤 순서로 나눌지 명시

즉 반올림 규칙은 유틸 메서드가 아니라 회계 정책에 가깝다.

### 4. `divide()`는 "정확히 나눠 떨어질 것"을 가정하지 않는다

`BigDecimal.divide()`는 무한소수 결과가 나오면 예외를 던질 수 있다.
이 점을 모르고 수수료율, 환율, 할부 금액을 계산하면 운영 중에만 터진다.

예를 들어 `1 / 3`, `100 / 7` 같은 값은 scale과 `RoundingMode`를 같이 줘야 한다.

문제는 여기서도 "아무 scale이나 넣는다"가 위험하다는 점이다.
표시용 scale 2자리와 내부 계산용 scale 8자리는 목적이 다르다.

### 5. 직렬화 경계에서는 숫자 타입보다 계약이 더 중요하다

서비스 내부에서 `BigDecimal`을 잘 썼더라도, 경계를 넘는 순간 문제가 다시 생긴다.

대표적인 실패 패턴은 이렇다.

- JSON 숫자로 보내면서 consumer가 `double`로 파싱한다
- `"1.00"`과 `"1.0"`이 서로 다른 서명/해시 입력이 된다
- DB `DECIMAL(19, 2)`에 저장되며 scale이 강제로 맞춰진다
- 캐시 key 생성 시 `toString()`과 `toPlainString()`이 섞인다

즉 직렬화는 단순 포맷 변환이 아니라 canonicalization 문제다.

특히 메시지, 캐시, 로그 재처리, idempotency key 같은 곳에서는
"동일 금액"의 정의를 문자열 수준에서 고정해야 한다.

### 6. 외부 계약에서는 숫자 문자열이 더 안전할 때가 많다

JSON number 자체가 항상 문제라는 뜻은 아니다.
문제는 소비자가 어떤 언어, 어떤 파서, 어떤 storage를 쓰는지 통제되지 않는다는 점이다.

다음 상황이면 문자열 계약이 더 안전할 수 있다.

- JavaScript 클라이언트가 중간에 낀다
- 여러 언어 서비스가 같은 이벤트를 소비한다
- 서명/검증 대상으로 원문이 중요하다
- scale 보존 자체가 비즈니스 의미다

예를 들어 `"amount": "1234.50"`처럼 보내면
숫자 값과 표현을 모두 보존할 수 있다.

물론 그 대신 consumer validation과 schema 문서화 책임이 커진다.

## 실전 시나리오

### 시나리오 1: `HashSet`과 `TreeSet`이 서로 다른 중복 제거 결과를 낸다

```java
import java.math.BigDecimal;
import java.util.HashSet;
import java.util.Set;
import java.util.TreeSet;

Set<BigDecimal> hashSet = new HashSet<>();
hashSet.add(new BigDecimal("1.0"));
hashSet.add(new BigDecimal("1.00"));

Set<BigDecimal> treeSet = new TreeSet<>();
treeSet.add(new BigDecimal("1.0"));
treeSet.add(new BigDecimal("1.00"));

System.out.println(hashSet.size()); // 2
System.out.println(treeSet.size()); // 1
```

이 버그는 컬렉션 API 문제가 아니라,
"도메인 동등성"과 "`BigDecimal` 표현 동등성"을 구분하지 않은 결과다.

### 시나리오 2: 항목별 반올림과 총액 반올림이 달라 정산 차액이 생긴다

주문 3건 각각에 세금을 계산하고 바로 `setScale(0, HALF_UP)` 해버리면,
합산 후 한 번만 반올림했을 때와 1원 차이가 날 수 있다.

정산, 쿠폰 배분, 포인트 소진은 이 1원 차이가 결국 장애나 CS 이슈로 이어진다.

대응은 기술보다 정책의 문제다.

- 어느 단계에서 반올림할지
- remainder를 누구에게 줄지
- 화면 표시와 장부 계산을 어떻게 분리할지

이 셋을 코드에 녹여야 한다.

### 시나리오 3: JSON 직렬화 후 idempotency key가 달라진다

한 서비스는 `"amount": 1.0`으로 쓰고,
다른 서비스는 `"amount": 1.00` 또는 `"amount": "1.00"`으로 쓴다.

둘 다 사람이 보기엔 같지만 다음은 달라질 수 있다.

- 메시지 본문 해시
- 서명 검증 결과
- 캐시 키
- 중복 결제 방지 키

즉 "값만 같으면 된다"는 가정이 깨지는 지점이다.

### 시나리오 4: DB에서 읽고 나니 `equals()`가 달라진다

애플리케이션 안에서는 `1.0`으로 만들었는데,
DB 컬럼이 `DECIMAL(19, 2)`라 저장 후 읽으면 `1.00`이 된다.

그러면 다음이 흔들린다.

- 엔티티 변경 감지
- 테스트 fixture 비교
- 캐시 hit 여부
- 메시지 재생산 결과

이때 "DB가 값을 망쳤다"보다 먼저,
도메인 내부 canonical scale을 정했는지부터 봐야 한다.

## 코드로 보기

### 1. `double` 생성자를 피하고 입력 경계를 정규화한다

```java
import java.math.BigDecimal;

BigDecimal a = new BigDecimal("19.99");
BigDecimal b = BigDecimal.valueOf(19.99d);

// new BigDecimal(19.99d)는 binary floating-point 흔적을 가져오므로 피하는 편이 안전하다.
```

문자열 입력 또는 `BigDecimal.valueOf(double)`를 쓰고,
그 다음 도메인 허용 scale로 검증하는 흐름이 보통 더 안전하다.

### 2. 금액 값 객체에서 scale과 통화를 강제한다

```java
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Currency;
import java.util.Objects;

public final class Money {
    private final Currency currency;
    private final BigDecimal amount;

    private Money(Currency currency, BigDecimal amount) {
        this.currency = Objects.requireNonNull(currency);
        this.amount = normalize(currency, amount);
    }

    public static Money of(Currency currency, String amount) {
        return new Money(currency, new BigDecimal(amount));
    }

    public Money add(Money other) {
        assertSameCurrency(other);
        return new Money(currency, amount.add(other.amount));
    }

    public Money multiply(BigDecimal factor, RoundingMode roundingMode) {
        int scale = currency.getDefaultFractionDigits();
        BigDecimal calculated = amount
            .multiply(factor)
            .setScale(scale, roundingMode);
        return new Money(currency, calculated);
    }

    public BigDecimal amount() {
        return amount;
    }

    public Currency currency() {
        return currency;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof Money money)) return false;
        return currency.equals(money.currency) && amount.equals(money.amount);
    }

    @Override
    public int hashCode() {
        return Objects.hash(currency, amount);
    }

    private void assertSameCurrency(Money other) {
        if (!currency.equals(other.currency)) {
            throw new IllegalArgumentException("currency mismatch");
        }
    }

    private static BigDecimal normalize(Currency currency, BigDecimal raw) {
        int scale = currency.getDefaultFractionDigits();
        if (scale < 0) {
            throw new IllegalArgumentException("unsupported currency");
        }
        return raw.setScale(scale, RoundingMode.UNNECESSARY);
    }
}
```

핵심은 `BigDecimal` 자체를 전역적으로 흩뿌리지 않고,
도메인 진입 시점에 scale과 currency를 고정하는 것이다.

내부 고정밀 계산이 길게 이어진다면,
계산용 서비스와 저장용 `Money`를 분리하는 편이 더 깔끔하다.

### 3. 나눗셈은 계산 scale과 표시 scale을 분리한다

```java
import java.math.BigDecimal;
import java.math.RoundingMode;

BigDecimal total = new BigDecimal("100.00");
BigDecimal ratio = new BigDecimal("3");

BigDecimal calculated = total.divide(ratio, 8, RoundingMode.HALF_EVEN);
BigDecimal display = calculated.setScale(2, RoundingMode.HALF_EVEN);
```

계산 단계에서는 충분한 scale을 유지하고,
표시 또는 저장 경계에서만 최종 scale로 내리는 편이 더 예측 가능하다.

### 4. 외부 직렬화는 canonical string을 명시한다

```java
public record MoneyPayload(
    String currency,
    String amount
) {
    public static MoneyPayload from(Money money) {
        return new MoneyPayload(
            money.currency().getCurrencyCode(),
            money.amount().toPlainString()
        );
    }
}
```

숫자 필드를 문자열로 보내면 scale 보존과 cross-language 계약이 쉬워진다.
대신 consumer는 숫자 검증과 범위 검증을 직접 해야 한다.

## 트레이드오프

| 선택 | 장점 | 비용 |
|---|---|---|
| `BigDecimal` 직접 노출 | 구현이 빠르다 | scale, currency, rounding 정책이 흩어진다 |
| `Money` 값 객체 | 규칙을 한곳에 모은다 | 코드와 변환 계층이 늘어난다 |
| JSON number로 직렬화 | 일반적인 API 관례와 맞다 | scale 보존과 cross-language precision 이슈가 생길 수 있다 |
| 문자열 금액 계약 | 표현과 scale을 보존하기 쉽다 | validation, schema 문서화 책임이 커진다 |
| minor unit `long` 사용 | key/비교/합산이 단순하다 | 소수 자릿수 다른 통화와 환율 계산은 별도 모델이 필요하다 |

핵심은 "`BigDecimal`을 쓴다"가 목표가 아니라,
금액의 canonical form과 경계 계약을 먼저 정하는 것이다.

## 꼬리질문

> Q: 금액 비교는 `equals()`와 `compareTo()` 중 무엇을 써야 하나요?
> 핵심: 수학적 동등성 비교는 `compareTo() == 0`, 표현까지 같은 canonical value 비교는 `equals()`다. 둘을 혼용하지 말고 용도를 분리해야 한다.

> Q: `stripTrailingZeros()`로 다 정리하면 되나요?
> 핵심: 일부 경우 canonicalization에 도움이 되지만, scale 자체가 비즈니스 의미일 수 있고 `0E-?` 같은 표현 변화도 생길 수 있어 무조건적인 해결책은 아니다.

> Q: 돈은 `BigDecimal`보다 `long` cents가 더 좋은가요?
> 핵심: 단일 통화, 고정 소수 자릿수, 단순 합산이면 `long` minor unit이 단순하다. 하지만 환율, 가변 scale, 계산 중간 정밀도까지 다루면 별도 모델링이 더 필요하다.

> Q: 외부 API에서는 숫자로 보내야 하나요, 문자열로 보내야 하나요?
> 핵심: 단일 Java 백엔드 내부라면 숫자도 가능하지만, 다중 언어 소비자나 서명/재처리 요구가 있으면 문자열 계약이 더 안전할 수 있다.

## 한 줄 정리

금액 모델링의 핵심은 `BigDecimal` 선택 자체가 아니라, 동등성 기준, 반올림 시점, canonical serialization을 팀 규칙으로 고정하는 것이다.
