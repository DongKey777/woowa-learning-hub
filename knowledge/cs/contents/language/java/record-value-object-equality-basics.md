# Record and Value Object Equality

> 한 줄 요약: Java record는 선언한 component 전체를 기준으로 `equals()`/`hashCode()`를 자동 생성하므로 immutable value object에는 잘 맞지만, identity와 lifecycle이 중요한 mutable entity-style class에는 그대로 가져오면 오히려 위험할 수 있다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: record value object equality basics basics, record value object equality basics beginner, record value object equality basics intro, java basics, beginner java, 처음 배우는데 record value object equality basics, record value object equality basics 입문, record value object equality basics 기초, what is record value object equality basics, how to record value object equality basics
> 관련 문서:
> - [Language README](../README.md)
> - [Java Equality and Identity Basics](./java-equality-identity-basics.md)
> - [Comparator Consistency With `equals()` Bridge](./comparator-consistency-with-equals-bridge.md)
> - [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
> - [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
> - [Beginner Drill Sheet: Equality vs Ordering](./equality-vs-ordering-beginner-drill-sheet.md)
> - [Record-Comparator 60초 미니 드릴](./record-comparator-60-second-mini-drill.md)
> - [Record component로 `BigDecimal`을 써도 되나요?](./record-bigdecimal-component-faq.md)
> - [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)
> - [`List.copyOf(...)` vs `stream.toList()` 읽기 전용 스냅샷 브리지](./list-copyof-vs-stream-tolist-readonly-snapshot-bridge.md)
> - [Records, Sealed Classes, Pattern Matching](./records-sealed-pattern-matching.md)
> - [Java Array Equality Basics](./java-array-equality-basics.md)
> - [Value Object Invariants, Canonicalization, and Boundary Design](./value-object-invariants-canonicalization-boundary-design.md)
> - [Record Serialization Evolution](./record-serialization-evolution.md)

> retrieval-anchor-keywords: java record equality, java record equals hashCode, record component equality, record generated equals, record generated hashCode, record shallow immutability, java value object equality, immutable value object, entity vs value object, record vs entity decision, record vs class beginner, mutable entity equality hazard, hashset mutable key bug, record canonical constructor normalization, array component equality, record mutable component pitfall, record value object entity example, record hashset contains false, record comparator mismatch, record equals comparator compare zero mismatch, treeset record duplicate surprise, treemap record key overwrite comparator, record equals true but treeset size one, equals ordering inconsistency beginner, record array component faq, record list component faq, record defensive copy, record canonicalization beginner, record array equals false, record mutable collection component, record compact constructor copy normalize, record accessor mutable list, record accessor collection exposure, record list copyof faq, tree set compare zero beginner, record equals tree map overwrite

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [30초 멘탈 모델: value object vs entity](#30초-멘탈-모델-value-object-vs-entity)
- [같은 도메인에서도 역할이 갈린다: 1분 예시](#같은-도메인에서도-역할이-갈린다-1분-예시)
- [record의 `equals()`와 `hashCode()`는 어떻게 만들어지나](#record의-equals와-hashcode는-어떻게-만들어지나)
- [record equality에서 자주 놓치는 함정](#record-equality에서-자주-놓치는-함정)
- [record 자동 `equals()`와 comparator 기준이 충돌하는 지점](#record-자동-equals와-comparator-기준이-충돌하는-지점)
- [초보자 common confusion 한 장 정리](#초보자-common-confusion-한-장-정리)
- [immutable value object가 더 안전한 경우](#immutable-value-object가-더-안전한-경우)
- [mutable entity-style class가 맞는 경우](#mutable-entity-style-class가-맞는-경우)
- [코드로 비교하기](#코드로-비교하기)
- [자주 묻는 질문: 배열, 가변 컬렉션, canonicalization](#자주-묻는-질문-배열-가변-컬렉션-canonicalization)
- [빠른 체크리스트](#빠른-체크리스트)
- [꼬리질문](#꼬리질문)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

`record`를 처음 배우면 "보일러플레이트를 줄여 주는 문법"으로만 기억하기 쉽다.

하지만 실제로 더 중요한 점은 이 문법이 **값의 정의**를 코드에 박아 넣는다는 것이다.

- 어떤 필드가 같은 값 판단에 들어가는가
- 해시 컬렉션에서 안정적으로 동작하는가
- 상태가 바뀌면 같은 객체로 봐야 하는가, 다른 값으로 봐야 하는가

이 질문에 답하려면 `record`의 자동 생성 메서드와 value object / entity 차이를 같이 봐야 한다.

## 30초 멘탈 모델: value object vs entity

초보자가 record를 선택할지 헷갈릴 때는 아래 표부터 보면 된다.

| 질문 | `Yes`에 가깝다면 | `No`에 가깝다면 |
|---|---|---|
| "현재 값"이 곧 의미인가? | value object 쪽 (`record` 잘 맞음) | entity 쪽 (일반 class 설계 검토) |
| 생성 후 상태를 거의 바꾸지 않는가? | 불변 모델에 가깝다 | mutable lifecycle 고려 필요 |
| 컬렉션 key로 안전하게 써야 하는가? | immutable value 설계가 유리 | mutable equality는 버그 위험 증가 |

핵심은 한 줄이다.

- `record`는 "값 의미를 선언"할 때 강하고, "시간에 따라 변하는 대상의 identity"를 다룰 때는 신중해야 한다.

### 같은 도메인에서도 역할이 갈린다: 1분 예시

초보자가 특히 헷갈리는 지점은 "도메인 용어가 비슷하면 같은 모델이어야 한다"고 느끼는 부분이다.

| 타입 | 무엇을 같다고 보는가 | `record` 적합성 |
|---|---|---|
| `EmailAddress` | 정규화된 문자열 값이 같으면 같은 값 | 높음 (value object) |
| `Money` | 통화 + 금액이 같으면 같은 값 | 높음 (value object) |
| `Order` | 주문 id로 동일 대상을 추적 | 낮음 (entity 성격) |
| `MemberAccount` | 시간에 따라 상태가 바뀌어도 같은 대상 | 낮음 (entity 성격) |

즉 "이 타입이 무엇을 표현하는지"보다, **같음을 어디에 둘지**를 먼저 정해야 record 선택이 쉬워진다.

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

## record equality에서 자주 놓치는 함정 (계속 2)

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

### 4. record를 "entity 대체 문법"으로 오해한다

record는 자동 메서드 생성 기능이 아니라, 사실상 **값 경계를 선언하는 문법**에 가깝다.

- 값 중심 타입은 record가 잘 맞는다.
- 상태 변화와 lifecycle이 핵심인 타입은 entity 규칙을 먼저 세워야 한다.
- "필드가 많으니 record로 줄이자"만으로 선택하면 equality 버그를 끌고 오기 쉽다.

처음엔 이렇게 기억하면 안전하다.

- 값의 snapshot을 다루면 `record`
- 시간에 따라 같은 대상을 추적하면 일반 class + 명시적 entity 규칙

## record 자동 `equals()`와 comparator 기준이 충돌하는 지점

`record`를 쓰기 시작한 초급자가 자주 막히는 질문은 이것이다.

- "record가 자동으로 `equals()`를 만들어 주는데, 왜 `TreeSet`에서는 하나로 합쳐지지?"

먼저 한 줄로 보면:

- `record` 자동 `equals()`는 값 동등성 기준이다
- `TreeSet`/`TreeMap`의 중복 기준은 comparator의 `compare(...) == 0`이다

| 상황 | 실제 기준 | 흔한 오해 |
|---|---|---|
| `HashSet` 중복 판단 | `equals()`/`hashCode()` | record면 모든 컬렉션이 같은 기준일 것 |
| `TreeSet` 중복 판단 | `compare(...) == 0` | `equals()`가 `false`면 둘 다 들어갈 것 |
| `TreeMap` key 자리 | `compare(...) == 0` | key 객체가 다르면 덮어쓰기 안 일어날 것 |

간단한 예시:

```java
import java.util.Comparator;
import java.util.Set;
import java.util.TreeSet;

record Student(long id, String name) {}

Set<Student> byName = new TreeSet<>(Comparator.comparing(Student::name));
byName.add(new Student(1L, "Mina"));
byName.add(new Student(2L, "Mina"));

System.out.println(byName.size()); // 1
```

두 `Student`는 record 기준 `equals()`로는 다르지만, comparator는 이름만 봐서 `compare(...) == 0`이 된다.
그래서 sorted collection에서는 하나 자리로 합쳐져 보인다.

지금 이 포인트가 헷갈리면 바로 아래 브리지로 이동하면 된다.

- 30초 비교 정리: [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md)
- `TreeSet`/`TreeMap` tie-breaker까지 한 번에: [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md)
- 실행 전 예측 연습: [Beginner Drill Sheet: Equality vs Ordering](./equality-vs-ordering-beginner-drill-sheet.md)

## 초보자 common confusion 한 장 정리

헷갈릴 때는 "record가 같은 값을 정하는가?"와 "sorted collection이 같은 자리를 정하는가?"를 분리해서 보면 된다.

| 헷갈리는 말 | 실제로 먼저 보는 기준 | 초보자용 한 줄 |
|---|---|---|
| "`record`니까 두 `Student`는 다르다" | `record`의 `equals()` | `HashSet`에서는 맞을 수 있지만 `TreeSet`은 아니다 |
| "`equals()`가 `false`면 `TreeSet`에 둘 다 들어간다" | comparator의 `compare(...) == 0` | sorted collection은 comparator가 같은 자리라고 보면 합쳐질 수 있다 |
| "`TreeMap` key 객체가 다르면 덮어쓰기 안 된다" | comparator의 `compare(...) == 0` | key reference가 달라도 comparator가 같다고 보면 같은 key 자리다 |
| "`thenComparing(...)`은 보기 좋게 정렬하는 옵션이다" | tie-breaker가 distinctness까지 결정 | sorted collection에서는 "끝까지 다른지"를 나누는 규칙이기도 하다 |

자주 나오는 오해를 bullet로 더 줄이면 아래 네 줄이다.

- `record` 자동 `equals()`는 값 비교 규칙이고, `TreeSet`/`TreeMap`의 중복 규칙은 comparator다.
- `HashSet`에서의 "같다"와 `TreeSet`에서의 "같다"는 같은 뜻이 아닐 수 있다.
- `compare(...) == 0`은 sorted collection 안에서는 "정렬상 동점"보다 "같은 슬롯"에 가깝다.
- comparator가 `id`를 안 보면, record에 `id`가 있어도 sorted collection은 그 차이를 잃어버릴 수 있다.

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

## 코드로 비교하기 (계속 2)

이 버그는 "mutable state를 equality/hashCode에 넣었다"는 점에서 생긴다.
이럴 때는 record가 아니라 entity equality 정책을 따로 설계해야 한다.

## 자주 묻는 질문: 배열, 가변 컬렉션, canonicalization

초급자가 record를 고를 때 가장 많이 묻는 세 질문만 먼저 짧게 정리하면 아래와 같다.

| 질문 | 짧은 답 | 먼저 기억할 한 줄 |
|---|---|---|
| record component에 배열을 넣어도 되나요? | 가능은 하지만 초급자에겐 보통 비추천 | 배열은 내용이 아니라 참조로 비교되기 쉽다 |
| `List` 같은 컬렉션을 넣어도 되나요? | 가능하지만 그대로 넣으면 value semantics가 흔들릴 수 있다 | record는 깊은 불변이 아니다 |
| `BigDecimal`을 넣어도 되나요? | 가능하지만 `1.0` vs `1.00` 정책을 먼저 정해야 한다 | record는 `BigDecimal.equals()` 규칙을 그대로 쓴다 |
| compact constructor에서 trim/정렬/복사를 해도 되나요? | 오히려 value object라면 자주 필요한 패턴이다 | "입구에서 한 번 정리"가 핵심이다 |

### Q. record component에 배열을 넣어도 되나요?

가능은 하지만, "내용이 같으면 같은 값"을 기대하는 beginner 문맥에서는 자주 어긋난다.

```java
record Scores(int[] values) {}

System.out.println(
    new Scores(new int[] {1, 2}).equals(new Scores(new int[] {1, 2}))
); // false
```

이유는 단순하다.

- record는 component의 `equals()`를 그대로 따른다
- 배열은 기본적으로 내용 비교가 아니라 참조 비교 쪽에 가깝다

그래서 초급자 기준 첫 선택은 보통 아래 둘 중 하나가 더 안전하다.

- 정말 배열이 필요하면: 생성 시 복사하고, 비교 규칙은 별도 문서 기준으로 명확히 본다
- "값 목록"이 목적이면: `List` 같은 더 읽기 쉬운 값 표현을 먼저 검토한다

배열 비교 자체가 막히면 [Java Array Equality Basics](./java-array-equality-basics.md), 배열 복사까지 함께 막히면 [Java Array Copy and Clone Basics](./java-array-copy-clone-basics.md)로 바로 내려가면 된다.

### Q. record component에 `List` 같은 가변 컬렉션을 넣어도 되나요?

넣을 수는 있지만, "field가 `final`이니 안전하겠지"라고 생각하면 거의 항상 한 번은 헷갈린다.

```java
import java.util.ArrayList;
import java.util.List;

record Tags(List<String> values) {}

List<String> raw = new ArrayList<>(List.of("java"));
Tags tags = new Tags(raw);
raw.add("record");

System.out.println(tags.values()); // [java, record]
```

## 자주 묻는 질문: 배열, 가변 컬렉션, canonicalization (계속 2)

초급자 기준 핵심은 "`values()` accessor가 복사본을 돌려주지 않는다"는 점이다.

- `raw`를 바꾸면 record 안의 값도 같이 바뀐다
- `tags.values()`로 꺼낸 리스트를 직접 바꿀 수도 있다
- 그래서 record accessor는 "안전한 창문"이 아니라 "같은 리스트 손잡이"가 될 수 있다

```java
import java.util.ArrayList;
import java.util.List;

public record SafeTags(List<String> values) {
    public SafeTags {
        values = List.copyOf(values);
    }
}

List<String> raw = new ArrayList<>(List.of("java"));
SafeTags tags = new SafeTags(raw);
raw.add("record");              // tags 안은 안 바뀜
tags.values().add("oops");      // UnsupportedOperationException
```

짧게 비교하면 아래처럼 읽으면 된다.

| 설계 | accessor 결과 | 초급자 관점 |
|---|---|---|
| `record Tags(List<String> values) {}` | 원본과 연결된 같은 리스트일 수 있음 | 밖에서 바뀌는 이유가 헷갈리기 쉽다 |
| `values = List.copyOf(values)` | 읽기 전용 snapshot | "생성 시점 값 묶음"으로 읽기 쉽다 |

체크리스트:

- "이 record는 현재 시점의 값 snapshot인가?"를 먼저 묻는다
- snapshot이면 생성자에서 `List.copyOf(...)`로 연결을 끊는다
- accessor로 받은 컬렉션을 수정 대상으로 쓰지 않는다
- 해시 컬렉션 key로 쓸 타입이면 가변 컬렉션 component를 더 강하게 피한다

컬렉션/복사 관점이 더 헷갈리면 [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)를 먼저 보면 된다.

### Q. record component에 `BigDecimal`을 넣어도 되나요?

넣을 수는 있다. 다만 초급자가 가장 자주 놓치는 부분은 `record`가 `BigDecimal`의 equality 규칙을 그대로 받는다는 점이다.

즉 `new BigDecimal("1.0")`과 `new BigDecimal("1.00")`은 숫자로는 같아 보여도 record 안에서는 다른 component로 남을 수 있다.
이 질문은 컬렉션 동작과 canonicalization까지 함께 묶여서 자주 반복되므로, 별도 FAQ인 [Record component로 `BigDecimal`을 써도 되나요?](./record-bigdecimal-component-faq.md)에서 `HashSet`/`TreeSet` 차이와 생성 시 정규화 위치를 따로 이어서 보면 된다.

## 자주 묻는 질문: 배열, 가변 컬렉션, canonicalization (계속 3)

### Q. compact constructor에서 복사나 정규화(canonicalization)를 해도 되나요?

된다. 오히려 value object라면 가장 흔한 정상 패턴 중 하나다.

핵심 멘탈 모델은 이것이다.

- raw input은 아직 "들어온 값"이다
- constructor를 통과한 뒤 값이 "우리 시스템이 믿는 값"이 된다

예를 들어 이메일은 trim/lowercase를 하고, 목록은 복사해서 고정할 수 있다.

```java
import java.util.List;
import java.util.Locale;

public record SignupForm(String email, List<String> roles) {
    public SignupForm {
        if (email == null || email.isBlank()) {
            throw new IllegalArgumentException("blank email");
        }
        email = email.trim().toLowerCase(Locale.ROOT);
        roles = List.copyOf(roles);
    }
}
```

이 패턴의 장점은 한 번 정리한 규칙을 호출자마다 다시 쓰지 않아도 된다는 점이다.

- `" Foo@Bar.com "`과 `"foo@bar.com"`을 같은 값으로 맞출 수 있다
- 외부 리스트 변경이 record 안으로 새지 않게 막을 수 있다
- 이후 `equals()`/`hashCode()`가 더 예측 가능해진다

정규화 범위를 더 깊게 잡아야 하는 상황은 [Value Object Invariants, Canonicalization, and Boundary Design](./value-object-invariants-canonicalization-boundary-design.md)에서 이어서 보면 된다.

## 빠른 체크리스트

- record는 선언한 component 전체로 `equals()`/`hashCode()`를 만든다
- 같은 값 비교가 중요하면 record나 immutable value object가 잘 맞는다
- 배열, mutable collection, mutable 객체를 component로 넣으면 value semantics가 쉽게 흐려진다
- component를 고를 때는 "이 필드가 바뀌면 같은 값 판단이 깨지는가?"를 먼저 묻는다
- `HashMap` key나 `HashSet` 원소로 쓸 타입은 mutable state를 equality에 넣지 않는 편이 안전하다
- identity와 lifecycle이 중요하면 entity-style class로 모델링하고 equality 규칙을 따로 정한다

## 꼬리질문

> Q: record면 자동으로 좋은 value object인가요?
> 핵심: 아니다. component가 mutable이거나 배열이면 value semantics가 쉽게 흔들린다.

> Q: entity도 `equals()`/`hashCode()`를 만들 수 있나요?
> 핵심: 가능하지만 "현재 상태 전체"를 기준으로 만들면 위험하다. stable identity와 lifecycle을 먼저 봐야 한다.

> Q: record에서 `equals()`/`hashCode()`를 직접 고쳐도 되나요?
> 핵심: 기술적으로는 가능하지만, 예외 규칙이 많아질수록 record보다 일반 클래스가 더 맞는 신호일 때가 많다.

## 어떤 문서를 다음에 읽으면 좋은가

지금 막힌 포인트별로 바로 가려면 아래 표가 빠르다.

| 지금 막힌 질문 | 다음 문서 |
|---|---|
| `==`와 `equals()` 자체가 아직 헷갈린다 | [Java Equality and Identity Basics](./java-equality-identity-basics.md) |
| record component에 배열/중첩 배열이 있을 때 비교가 이상하다 | [Java Array Equality Basics](./java-array-equality-basics.md) |
| record 자동 `equals()`와 `TreeSet`/`TreeMap` comparator 결과가 왜 다른지 헷갈린다 | [Comparator in TreeSet and TreeMap](./treeset-treemap-comparator-tie-breaker-basics.md) |
| `HashSet`은 2개인데 `TreeSet`은 1개가 되는 이유를 먼저 짧게 확인하고 싶다 | [HashSet vs TreeSet Duplicate Semantics](./hashset-vs-treeset-duplicate-semantics.md) |
| `final` 참조인데도 값이 바뀌는 이유가 헷갈린다 | [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md) |
| 금액 value object의 `BigDecimal`이 컬렉션에서 다르게 동작한다 | [BigDecimal compareTo vs equals in HashSet, TreeSet, and TreeMap](./bigdecimal-sorted-collection-bridge.md) |
| record component에 `BigDecimal`을 넣을 때 `1.0` vs `1.00`, canonicalization, 컬렉션 기준이 한 번에 헷갈린다 | [Record component로 `BigDecimal`을 써도 되나요?](./record-bigdecimal-component-faq.md) |
| 생성 시 정규화/검증 규칙을 어디까지 넣을지 고민된다 | [Value Object Invariants, Canonicalization, and Boundary Design](./value-object-invariants-canonicalization-boundary-design.md) |

record 이후 modern Java 타입 설계로 넘어가려면 [Records, Sealed Classes, Pattern Matching](./records-sealed-pattern-matching.md)을 이어서 보면 된다.

## 한 줄 정리

record의 자동 `equals()`/`hashCode()`는 immutable value semantics를 선언하는 도구이고, 상태가 변하는 entity에는 그 자동성보다 명시적 equality 설계가 더 중요하다.
