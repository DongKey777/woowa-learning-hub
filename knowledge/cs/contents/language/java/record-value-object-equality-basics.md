# Record and Value Object Equality

> 한 줄 요약: Java record는 선언한 component 전체를 기준으로 `equals()`/`hashCode()`를 자동 생성하므로 immutable value object에는 잘 맞지만, identity와 lifecycle이 중요한 mutable entity-style class에는 그대로 가져오면 오히려 위험할 수 있다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Language README](../README.md)
> - [Java Equality and Identity Basics](./java-equality-identity-basics.md)
> - [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)
> - [Records, Sealed Classes, Pattern Matching](./records-sealed-pattern-matching.md)
> - [Java Array Equality Basics](./java-array-equality-basics.md)
> - [Value Object Invariants, Canonicalization, and Boundary Design](./value-object-invariants-canonicalization-boundary-design.md)
> - [Record Serialization Evolution](./record-serialization-evolution.md)

> retrieval-anchor-keywords: java record equality, java record equals hashCode, record component equality, record generated equals, record generated hashCode, record shallow immutability, java value object equality, immutable value object, entity vs value object, mutable entity equality hazard, hashset mutable key bug, record canonical constructor normalization, array component equality

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [record의 `equals()`와 `hashCode()`는 어떻게 만들어지나](#record의-equals와-hashcode는-어떻게-만들어지나)
- [record equality에서 자주 놓치는 함정](#record-equality에서-자주-놓치는-함정)
- [immutable value object가 더 안전한 경우](#immutable-value-object가-더-안전한-경우)
- [mutable entity-style class가 맞는 경우](#mutable-entity-style-class가-맞는-경우)
- [코드로 비교하기](#코드로-비교하기)
- [빠른 체크리스트](#빠른-체크리스트)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

`record`를 처음 배우면 "보일러플레이트를 줄여 주는 문법"으로만 기억하기 쉽다.

하지만 실제로 더 중요한 점은 이 문법이 **값의 정의**를 코드에 박아 넣는다는 것이다.

- 어떤 필드가 같은 값 판단에 들어가는가
- 해시 컬렉션에서 안정적으로 동작하는가
- 상태가 바뀌면 같은 객체로 봐야 하는가, 다른 값으로 봐야 하는가

이 질문에 답하려면 `record`의 자동 생성 메서드와 value object / entity 차이를 같이 봐야 한다.

## record의 `equals()`와 `hashCode()`는 어떻게 만들어지나

다음 record를 보자.

```java
public record Money(String currency, long amount) {}
```

컴파일러는 header에 적은 component를 기준으로 record의 기본 동작을 만든다.

| 규칙 | 의미 |
|---|---|
| component 전체가 equality 경계다 | `currency`, `amount` 둘 다 같아야 같은 값이다 |
| 같은 record 타입이어야 한다 | 다른 클래스와는 값이 같아 보여도 `equals()`가 성립하지 않는다 |
| `hashCode()`도 같은 component를 사용한다 | `equals()`가 `true`면 `hashCode()`도 같아진다 |
| 생성 시 정규화한 값이 최종 비교값이 된다 | compact constructor에서 trim/lowercase를 하면 그 결과가 equality 기준이 된다 |

즉 record는 "이 필드들이 곧 이 타입의 값 의미다"라고 선언하는 문법이다.

```java
Money a = new Money("KRW", 1_000L);
Money b = new Money("KRW", 1_000L);

System.out.println(a.equals(b)); // true
System.out.println(a.hashCode() == b.hashCode()); // true
```

이런 타입은 직접 `equals()`/`hashCode()`를 쓰지 않아도 된다.  
component가 곧 값 정의이기 때문이다.

## record equality에서 자주 놓치는 함정

### 1. component 타입이 곧 equality 품질을 결정한다

record가 자동으로 비교를 만들어 줘도, 각 component가 어떤 equality를 가지는지는 타입마다 다르다.

- `String`, `Integer`, 다른 immutable value object는 보통 기대한 대로 동작한다
- `List`는 내용 기반 `equals()`가 있지만, 리스트 자체가 mutable이면 값 의미가 흔들릴 수 있다
- 배열은 내용 비교가 아니라 참조 비교이므로 초보자가 특히 자주 실수한다

```java
public record Tags(String[] values) {}

Tags left = new Tags(new String[] {"java"});
Tags right = new Tags(new String[] {"java"});

System.out.println(left.equals(right)); // false
```

배열은 `Object.equals()`를 그대로 쓰기 때문에, "내용은 같아 보이는데 record는 안 같다"는 상황이 생긴다.  
배열 비교 자체는 [Java Array Equality Basics](./java-array-equality-basics.md)에서 따로 이어서 보면 된다.

### 2. record는 깊은 불변이 아니라 얕은 불변이다

record의 field는 바꿀 수 없지만, field가 가리키는 객체까지 자동으로 불변이 되는 것은 아니다.

```java
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

public record AccountRoles(List<String> roles) {}

List<String> roles = new ArrayList<>(List.of("USER"));
AccountRoles key = new AccountRoles(roles);

Set<AccountRoles> seen = new HashSet<>();
seen.add(key);

roles.add("ADMIN");

System.out.println(seen.contains(key)); // false 가능
```

리스트 내용이 바뀌면 record가 보는 값도 사실상 바뀐다.  
이런 타입을 `HashSet` key처럼 쓰면 버그가 생기기 쉽다.

### 3. compact constructor의 정규화가 equality를 결정한다

record는 compact constructor에서 validation과 canonicalization을 넣을 수 있다.

```java
import java.util.Locale;

public record EmailAddress(String value) {
    public EmailAddress {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("blank email");
        }
        value = value.trim().toLowerCase(Locale.ROOT);
    }
}
```

이렇게 하면 다음 두 값은 같은 값으로 수렴한다.

```java
new EmailAddress(" Foo@Bar.com ").equals(new EmailAddress("foo@bar.com"));
```

즉 record equality는 "원본 입력"이 아니라 "생성 후 저장된 canonical 값"을 본다.

## immutable value object가 더 안전한 경우

다음 조건이 맞으면 record나 불변 클래스 형태의 value object가 훨씬 안전하다.

| 상황 | 왜 value object가 안전한가 |
|---|---|
| `HashMap` key, `HashSet` 원소, 캐시 키로 쓴다 | 생성 후 값이 안 바뀌어 `hashCode()`가 안정적이다 |
| 여러 스레드나 계층에 공유한다 | 외부 변경 때문에 의미가 흔들리지 않는다 |
| validation/canonicalization이 필요하다 | 생성 시점에 규칙을 한 번만 통과시키면 된다 |
| identity보다 값 의미가 중요하다 | `Money`, `EmailAddress`, `RetryLimit`처럼 "무엇을 나타내는가"가 곧 타입이다 |

핵심은 이렇다.

- 같은 값이면 같은 객체처럼 취급해도 된다
- 생성 이후 상태를 바꾸지 않는 편이 도메인 의미와 잘 맞는다
- 컬렉션 key로 써도 값 의미가 흔들리지 않는다

이럴 때는 immutable value object가 mutable entity-style class보다 훨씬 덜 위험하다.

## mutable entity-style class가 맞는 경우

반대로 다음과 같은 모델은 entity 성격이 강하다.

- 고유한 identity가 있다
- 시간에 따라 상태가 변한다
- "현재 필드 값"이 바뀌어도 같은 대상이어야 한다

예를 들어 `Order`는 배송지나 상태가 바뀌어도 같은 주문이다.

```java
public final class Order {
    private final Long id;
    private OrderStatus status;
    private String shippingAddress;

    // ...
}
```

이 타입에서 "모든 필드가 같아야 같은 객체"라고 보면 곤란하다.

- `status`가 바뀌었다고 다른 주문이 되는 것은 아니다
- `shippingAddress`가 바뀌었다고 identity가 바뀌는 것도 아니다
- 아직 저장 전이라 stable id가 없는 시점까지 고려해야 할 수도 있다

그래서 entity-style class는 record의 기본 equality보다 더 신중한 설계가 필요하다.  
오히려 "상태가 바뀌는 객체인데 `equals()`/`hashCode()`가 상태 전체를 본다"가 가장 위험한 조합이다.

## 코드로 비교하기

### 1. record value object는 값 의미를 고정하기 쉽다

```java
import java.util.Locale;

public record EmailAddress(String value) {
    public EmailAddress {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("blank email");
        }
        value = value.trim().toLowerCase(Locale.ROOT);
    }
}

EmailAddress a = new EmailAddress(" Foo@Bar.com ");
EmailAddress b = new EmailAddress("foo@bar.com");

System.out.println(a.equals(b)); // true
```

생성 시 정규화가 끝나므로, 그 뒤에는 어디서 비교해도 같은 의미를 유지하기 쉽다.

### 2. mutable entity-style 객체는 해시 컬렉션에서 특히 조심해야 한다

```java
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;

public final class OrderLine {
    private final String sku;
    private int quantity;

    public OrderLine(String sku, int quantity) {
        this.sku = sku;
        this.quantity = quantity;
    }

    public void changeQuantity(int quantity) {
        this.quantity = quantity;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (!(o instanceof OrderLine other)) return false;
        return quantity == other.quantity && Objects.equals(sku, other.sku);
    }

    @Override
    public int hashCode() {
        return Objects.hash(sku, quantity);
    }
}

Set<OrderLine> lines = new HashSet<>();
OrderLine line = new OrderLine("A-100", 1);

lines.add(line);
line.changeQuantity(2);

System.out.println(lines.contains(line)); // false 가능
```

이 버그는 "mutable state를 equality/hashCode에 넣었다"는 점에서 생긴다.  
이럴 때는 record가 아니라 entity equality 정책을 따로 설계해야 한다.

## 빠른 체크리스트

- record는 선언한 component 전체로 `equals()`/`hashCode()`를 만든다
- 같은 값 비교가 중요하면 record나 immutable value object가 잘 맞는다
- 배열, mutable collection, mutable 객체를 component로 넣으면 value semantics가 쉽게 흐려진다
- `HashMap` key나 `HashSet` 원소로 쓸 타입은 mutable state를 equality에 넣지 않는 편이 안전하다
- identity와 lifecycle이 중요하면 entity-style class로 모델링하고 equality 규칙을 따로 정한다

## 꼬리질문

> Q: record면 자동으로 좋은 value object인가요?
> 핵심: 아니다. component가 mutable이거나 배열이면 value semantics가 쉽게 흔들린다.

> Q: entity도 `equals()`/`hashCode()`를 만들 수 있나요?
> 핵심: 가능하지만 "현재 상태 전체"를 기준으로 만들면 위험하다. stable identity와 lifecycle을 먼저 봐야 한다.

> Q: record에서 `equals()`/`hashCode()`를 직접 고쳐도 되나요?
> 핵심: 기술적으로는 가능하지만, 예외 규칙이 많아질수록 record보다 일반 클래스가 더 맞는 신호일 때가 많다.

## 한 줄 정리

record의 자동 `equals()`/`hashCode()`는 immutable value semantics를 선언하는 도구이고, 상태가 변하는 entity에는 그 자동성보다 명시적 equality 설계가 더 중요하다.
