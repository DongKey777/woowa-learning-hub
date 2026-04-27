# Record component로 `BigDecimal`을 써도 되나요?

> 한 줄 요약: 써도 되지만 `record`가 `BigDecimal`의 scale 차이까지 그대로 equality에 넣으므로, `1.0` vs `1.00`을 같은 값으로 볼지 먼저 정하고 생성 시 한 번만 canonicalization해야 컬렉션 동작이 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README](../README.md)
- [Record and Value Object Equality](./record-value-object-equality-basics.md)
- [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md)
- [BigDecimal `stripTrailingZeros()` 입력 경계 브리지](./bigdecimal-striptrailingzeros-input-boundary-bridge.md)
- [BigDecimal 미니 드릴: `1.0` vs `1.00` in `HashSet`/`TreeSet`/`TreeMap`](./bigdecimal-1-0-vs-1-00-collections-mini-drill.md)
- [Money Value Object Basics](./money-value-object-basics.md)

retrieval-anchor-keywords: record bigdecimal faq, record component bigdecimal, record bigdecimal equals, record bigdecimal hashset, record bigdecimal treeset, record bigdecimal canonicalization, record bigdecimal 1.0 1.00, bigdecimal value object record, java record money faq, java record bigdecimal beginner, bigdecimal scale equality record, striptrailingzeros record money

## 먼저 잡을 멘탈 모델

초급자 기준으로는 이 한 줄이 가장 중요하다.

> `record`는 component를 그대로 비교하고, `BigDecimal`은 숫자와 scale을 함께 들고 있다.

그래서 아래 두 값은 숫자로는 같아 보여도 record 안에서는 다른 값이 될 수 있다.

```java
new BigDecimal("1.0").equals(new BigDecimal("1.00")); // false
new BigDecimal("1.0").compareTo(new BigDecimal("1.00")) == 0; // true
```

즉 "`record`니까 값 객체로 안전하겠지"보다 먼저 "`1.0`과 `1.00`을 같은 돈으로 볼까?"를 정해야 한다.

## 왜 record component에 `BigDecimal`을 넣으면 자주 헷갈리나요?

`record`는 선언한 component의 `equals()`와 `hashCode()`를 그대로 쓴다.

```java
import java.math.BigDecimal;

record Price(BigDecimal amount) {}

System.out.println(
    new Price(new BigDecimal("1.0"))
        .equals(new Price(new BigDecimal("1.00")))
); // false
```

이 결과는 record 버그가 아니다.

- `record`는 `amount.equals(...)`를 따른다
- `BigDecimal.equals(...)`는 scale 차이도 본다
- 그래서 `1.0`과 `1.00`이 다른 component로 남는다

한 줄로 줄이면 "`record`가 값을 망친다"가 아니라 "`BigDecimal`의 기존 equality 규칙이 record 안으로 그대로 들어온다"이다.

## 컬렉션에서는 무엇이 달라지나요?

초급자가 많이 막히는 부분은 set/map 결과가 서로 갈리는 장면이다.

| 위치 | 기준 | `new Price("1.0")` vs `new Price("1.00")` |
|---|---|---|
| `HashSet<Price>` | record의 `equals()`/`hashCode()` | 둘 다 남을 수 있다 |
| `TreeSet<Price>` + `Comparator.comparing(Price::amount)` | `compare(...) == 0` | 하나로 합쳐질 수 있다 |
| `TreeMap<Price, V>` + 같은 comparator | `compare(...) == 0` | 같은 key 자리로 보고 덮어쓸 수 있다 |

짧은 재현 예시는 아래처럼 읽으면 된다.

```java
import java.math.BigDecimal;
import java.util.Comparator;
import java.util.HashSet;
import java.util.Set;
import java.util.TreeSet;

record Price(BigDecimal amount) {}

Set<Price> hash = new HashSet<>();
hash.add(new Price(new BigDecimal("1.0")));
hash.add(new Price(new BigDecimal("1.00")));

Set<Price> tree = new TreeSet<>(Comparator.comparing(Price::amount));
tree.add(new Price(new BigDecimal("1.0")));
tree.add(new Price(new BigDecimal("1.00")));
```

- `hash.size()`는 `2`가 될 수 있다
- `tree.size()`는 `1`이 될 수 있다

즉 record와 컬렉션이 충돌한 것이 아니라, hash 기준과 sorted 기준이 다른 것이다.

## 그럼 canonicalization은 어디서 하나요?

초급 단계에서는 "생성 시 한 번"이 가장 덜 헷갈린다.

```java
import java.math.BigDecimal;

public record MoneyAmount(BigDecimal amount) {
    public MoneyAmount {
        if (amount == null) {
            throw new IllegalArgumentException("amount is required");
        }
        amount = amount.stripTrailingZeros();
    }
}
```

이렇게 하면 `1.0`, `1.00`, `1`이 같은 canonical component로 모인다.

| 입력 | canonical component |
|---|---|
| `"1.0"` | `1` |
| `"1.00"` | `1` |
| `"1"` | `1` |

다만 이 정책이 항상 정답은 아니다.

- scale 자체가 의미면 raw 표현을 보존해야 한다
- 외부 표시 형식이 중요하면 출력 정책을 따로 둬야 한다
- 돈 의미까지 묶고 싶으면 `BigDecimal` 하나보다 `Money(currency, amount)` 쪽이 더 읽기 쉽다

핵심은 "정규화할까?"보다 "우리 팀은 `1.0`과 `1.00`을 같은 값으로 볼까?"를 먼저 적는 것이다.

## 언제 record + `BigDecimal`이 괜찮고, 언제 money 타입이 더 낫나요?

| 상황 | 첫 선택 |
|---|---|
| 숫자 값 하나를 작은 value object로 감싸고 싶다 | record + 생성 시 검증/정규화 |
| 통화, 자릿수, 반올림 정책이 같이 움직인다 | `Money` 같은 전용 value object |
| scale 차이 자체가 도메인 의미다 | raw `BigDecimal` 보존 정책 명시 |

초급자 기준으로는 아래처럼 기억하면 충분하다.

- "숫자 하나를 감싼 값 객체"면 record도 괜찮다
- "돈 규칙 전체"가 필요하면 `BigDecimal` component 하나로는 설명력이 부족하다

## 자주 헷갈리는 포인트

- `record`를 쓰면 `compareTo()` 기준까지 자동 통일된다고 생각하기 쉽다.
- `stripTrailingZeros()`를 아무 데서나 호출해도 된다고 생각하기 쉽다. 보통은 입력 경계 한 곳이 더 안전하다.
- `1.0`과 `1.00`을 같은 값으로 만들었으면 출력도 항상 같은 문자열일 거라고 생각하기 쉽다. 출력 정책은 별개다.
- 돈 도메인인데 통화 없이 `BigDecimal`만 두고 value object가 완성됐다고 생각하기 쉽다.

## 한 줄 정리

record component에 `BigDecimal`을 넣는 것은 가능하지만, 초급자에게 중요한 포인트는 문법보다 "`1.0`과 `1.00`을 같은 값으로 볼지"를 먼저 정하고 그 정책을 생성 시 canonicalization 한 곳에 묶는 것이다.
