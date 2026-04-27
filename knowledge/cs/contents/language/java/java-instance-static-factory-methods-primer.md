# Java 인스턴스 메서드, `static` 유틸리티, 팩터리 메서드 입문

> 한 줄 요약: Java 입문자가 "이 동작을 객체에 붙일지, `static` helper로 둘지, 생성용 `static factory`로 만들지"를 `this` 의존성, 생성 책임, 호출 문장 모양으로 구분하도록 돕는 practice primer다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](../README.md)
- [우아코스 백엔드 CS 로드맵](../../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../../data-structure/backend-data-structure-starter-pack.md)


retrieval-anchor-keywords: java instance static factory methods primer basics, java instance static factory methods primer beginner, java instance static factory methods primer intro, java basics, beginner java, 처음 배우는데 java instance static factory methods primer, java instance static factory methods primer 입문, java instance static factory methods primer 기초, what is java instance static factory methods primer, how to java instance static factory methods primer
> 관련 문서:
> - [Language README](../README.md)
> - [Java 메서드와 생성자 실전 입문](./java-methods-constructors-practice-primer.md)
> - [Java 접근 제한자와 멤버 모델 입문](./java-access-modifiers-member-model-basics.md)
> - [Java 생성자와 초기화 순서 입문](./java-constructors-initialization-order-basics.md)
> - [객체지향 핵심 원리](./object-oriented-core-principles.md)
> - [Value Object Invariants, Canonicalization, and Boundary Design](./value-object-invariants-canonicalization-boundary-design.md)
> - [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)

> retrieval-anchor-keywords: java static vs instance methods, java instance method basics, java static utility method basics, java static factory method basics, java simple factory method basics, when to use instance method java, when to use static method java, java utility class beginner, java factory method beginner, java of from valueOf basics, java named constructor basics, java this dependent behavior, java object creation entrypoint, java method design beginner

<details>
<summary>Table of Contents</summary>

- [왜 이 문서가 필요한가](#왜-이-문서가-필요한가)
- [먼저 결론: 세 가지를 어떻게 고르나](#먼저-결론-세-가지를-어떻게-고르나)
- [인스턴스 메서드는 언제 자연스러운가](#인스턴스-메서드는-언제-자연스러운가)
- [`static` 유틸리티 메서드는 언제 자연스러운가](#static-유틸리티-메서드는-언제-자연스러운가)
- [simple factory method는 언제 자연스러운가](#simple-factory-method는-언제-자연스러운가)
- [한 번에 비교하는 코드](#한-번에-비교하는-코드)
- [손으로 분류해 보는 연습](#손으로-분류해-보는-연습)
- [초보자가 자주 틀리는 포인트](#초보자가-자주-틀리는-포인트)
- [어떤 문서를 다음에 읽으면 좋은가](#어떤-문서를-다음에-읽으면-좋은가)
- [한 줄 정리](#한-줄-정리)

</details>

## 왜 이 문서가 필요한가

Java 입문자는 `static`을 배우기 시작하면 비슷한 질문을 자주 만난다.

- "그냥 `static`으로 만들면 더 편한 것 아닌가?"
- "객체를 만드는 메서드도 `static`인데, 유틸리티 메서드와 뭐가 다르지?"
- "생성자가 있는데 왜 `of()`나 `from()` 같은 메서드를 또 만들지?"

핵심은 문법보다 **책임**이다.

- 이미 존재하는 객체의 상태와 규칙을 다루면 인스턴스 메서드가 자연스럽다.
- 객체 상태와 무관한 계산/검사라면 `static` 유틸리티 메서드가 자연스럽다.
- 객체를 어떻게 만들지, 어떤 이름으로 만들지, 생성 전에 어떤 정리를 할지가 중요하면 `static factory method`가 자연스럽다.

이 문서는 위 세 가지를 한 번에 비교해서 "왜 여기에는 `this`가 필요하고, 왜 저기에는 `new` 대신 `of()`가 자연스러운가"를 감각적으로 잡게 하는 데 목적이 있다.

## 먼저 결론: 세 가지를 어떻게 고르나

| 선택 | 이 질문에 `yes`면 우선 고려 | 전형적인 호출 모양 | 핵심 책임 |
|---|---|---|---|
| 인스턴스 메서드 | "이 동작이 현재 객체의 필드/불변식에 기대는가?" | `address.sameDomain(other)` | 이미 존재하는 객체의 상태와 규칙을 다룸 |
| `static` 유틸리티 메서드 | "객체 없이 입력만으로 설명 가능한가?" | `EmailRules.looksLikeEmail(raw)` | 계산, 검사, 포맷팅 같은 보조 동작 |
| simple factory method | "핵심이 생성 경로와 이름 붙이기인가?" | `EmailAddress.of(raw)` | 객체 생성, 검증, 정규화, 기본값 부여 |

짧게 줄이면 다음처럼 기억하면 된다.

- **`this`가 필요하면** 인스턴스 메서드 쪽으로 기운다.
- **`this`가 필요 없고 입력만 보면 되면** `static` 유틸리티를 검토한다.
- **반환값이 새 객체이고 생성 의미를 이름으로 드러내고 싶다면** `static factory`를 검토한다.

여기서 중요한 점 하나가 있다.

- 모든 factory method는 `static`일 수 있다.
- 하지만 모든 `static` 메서드가 utility는 아니다.

즉 "`static`인가 아닌가"보다 **무슨 책임을 가지는가**가 먼저다.

## 인스턴스 메서드는 언제 자연스러운가

인스턴스 메서드는 **이미 만들어진 객체가 자기 상태를 기준으로 일하는 경우**에 자연스럽다.

예를 들어 `EmailAddress` 객체가 있다고 해 보자.

```java
public final class EmailAddress {
    private final String localPart;
    private final String domain;

    private EmailAddress(String localPart, String domain) {
        this.localPart = localPart;
        this.domain = domain;
    }

    public String value() {
        return localPart + "@" + domain;
    }

    public boolean sameDomain(EmailAddress other) {
        return domain.equals(other.domain);
    }

    public boolean isCompanyAddress() {
        return domain.equals("woowa.com");
    }
}
```

위 메서드가 인스턴스 메서드인 이유는 분명하다.

- `value()`는 현재 객체의 `localPart`, `domain`을 읽는다.
- `sameDomain()`은 현재 객체의 `domain`과 다른 객체의 `domain`을 비교한다.
- `isCompanyAddress()`는 현재 객체가 가진 상태를 기준으로 판단한다.

즉 이 메서드는 `EmailAddress`라는 객체가 이미 있어야만 의미가 생긴다.

### 인스턴스 메서드를 고르는 간단한 기준

- 메서드가 `this`를 자연스럽게 떠올리게 한다.
- 필드 접근이나 불변식 확인이 들어간다.
- "이 객체에게 메시지를 보낸다"는 문장으로 읽힌다.

예를 들면 아래는 모두 인스턴스 메서드 쪽이 자연스럽다.

- `cart.totalPrice()`
- `account.withdraw(1000)`
- `order.isPaid()`
- `emailAddress.sameDomain(other)`

이런 동작을 억지로 utility로 빼면 오히려 코드가 어색해진다.

```java
EmailRules.sameDomain(address1, address2)
```

이 코드가 항상 틀린 것은 아니지만, 비교 규칙이 `EmailAddress`의 핵심 의미라면 객체 쪽에 두는 편이 더 읽기 쉽다.

## `static` 유틸리티 메서드는 언제 자연스러운가

`static` 유틸리티 메서드는 **특정 객체의 숨은 상태가 필요 없고, 입력만 보면 설명이 끝나는 동작**에 잘 맞는다.

```java
public final class EmailRules {
    private EmailRules() {
    }

    public static boolean looksLikeEmail(String raw) {
        return raw != null
                && raw.contains("@")
                && raw.indexOf('@') == raw.lastIndexOf('@');
    }

    public static String normalizeDomain(String domain) {
        return domain.trim().toLowerCase();
    }
}
```

위 메서드는 `EmailRules` 객체를 만들 필요가 없다.

- `looksLikeEmail(raw)`는 문자열만 보면 된다.
- `normalizeDomain(domain)`도 인자로 받은 문자열만 바꾼다.

이런 메서드는 보통 다음 성격을 가진다.

- 계산
- 포맷팅
- 파싱 보조
- 간단한 검증
- 상태 없는 변환

### 유틸리티 메서드를 고르는 간단한 기준

- 현재 객체의 필드를 전혀 읽지 않는다.
- 같은 입력이면 같은 결과를 돌려주는 경우가 많다.
- 특정 객체의 생명주기보다 범용 규칙에 가깝다.

예를 들면 아래는 utility 쪽이 자연스럽다.

- `Math.max(a, b)`
- `Integer.parseInt(text)`
- `DateFormats.isIsoDate(raw)`
- `PriceFormatter.formatWon(amount)`

### 이런 냄새가 나면 utility가 아닐 수 있다

다음처럼 utility 메서드가 늘 같은 타입의 객체를 첫 인자로 받기 시작하면, 사실 인스턴스 메서드가 더 자연스러울 수 있다.

```java
public static boolean sameDomain(EmailAddress left, EmailAddress right)
```

이 경우 질문을 다시 해 보면 된다.

- "이 로직이 `EmailAddress` 자체의 의미인가?"
- "호출을 `left.sameDomain(right)`로 읽는 편이 더 자연스러운가?"

둘 다 `yes`라면 객체 쪽으로 붙이는 편이 좋다.

## simple factory method는 언제 자연스러운가

여기서 말하는 simple factory method는 복잡한 GoF 패턴이 아니라, **객체를 만들기 위한 `static` 생성 메서드**를 뜻한다.

- `of(...)`
- `from(...)`
- `valueOf(...)`
- `zero()`
- `guest()`

같은 이름이 대표적이다.

```java
public final class EmailAddress {
    private final String localPart;
    private final String domain;

    private EmailAddress(String localPart, String domain) {
        this.localPart = localPart;
        this.domain = domain;
    }

    public static EmailAddress of(String raw) {
        if (!EmailRules.looksLikeEmail(raw)) {
            throw new IllegalArgumentException("invalid email: " + raw);
        }

        String[] parts = raw.trim().split("@", 2);
        String normalizedLocalPart = parts[0].trim().toLowerCase();
        String normalizedDomain = EmailRules.normalizeDomain(parts[1]);
        return new EmailAddress(normalizedLocalPart, normalizedDomain);
    }

    public static EmailAddress companyAccount(String localPart) {
        String normalizedLocalPart = localPart.trim().toLowerCase();
        return new EmailAddress(normalizedLocalPart, "woowa.com");
    }
}
```

위 메서드가 factory인 이유는 "도와주는 계산"이 아니라 **생성 경로를 제공**하기 때문이다.

- `of(raw)`는 문자열을 파싱하고 검증해서 객체를 만든다.
- `companyAccount(localPart)`는 특정 기본값을 가진 객체를 만든다.

### factory method를 고르는 간단한 기준

- 메서드의 핵심 결과가 "새 객체 반환"이다.
- constructor에 이름을 붙이고 싶다.
- 생성 전에 검증/정규화/기본값 주입이 필요하다.
- `new ClassName(...)`보다 `ClassName.of(...)`가 의미를 더 잘 드러낸다.

예를 들면 아래는 factory 쪽이 자연스럽다.

## simple factory method는 언제 자연스러운가 (계속 2)

- `Money.won(1000)`
- `User.guest()`
- `OrderId.from(raw)`
- `Duration.ofSeconds(30)`

### constructor와 factory는 언제 갈리나

public constructor가 항상 나쁜 것은 아니다.
다만 아래 상황에서는 factory가 더 읽기 쉽다.

- 같은 타입을 여러 방식으로 만들 수 있을 때
- 인자만 봐서는 의미가 모호할 때
- 생성 전에 검증/정규화가 꼭 필요할 때
- 내부 표현을 나중에 바꾸고 싶을 때

즉 factory는 "객체 생성도 메서드 이름으로 설명하고 싶다"는 요구를 해결한다.

## 한 번에 비교하는 코드

아래 코드는 인스턴스 메서드, utility 메서드, factory 메서드가 한 문맥에서 어떻게 다른지 보여 준다.

```java
public final class EmailAddress {
    private final String localPart;
    private final String domain;

    private EmailAddress(String localPart, String domain) {
        this.localPart = localPart;
        this.domain = domain;
    }

    public static EmailAddress of(String raw) {
        if (!EmailRules.looksLikeEmail(raw)) {
            throw new IllegalArgumentException("invalid email: " + raw);
        }

        String[] parts = raw.trim().split("@", 2);
        return new EmailAddress(
                parts[0].trim().toLowerCase(),
                EmailRules.normalizeDomain(parts[1])
        );
    }

    public static EmailAddress companyAccount(String localPart) {
        return new EmailAddress(localPart.trim().toLowerCase(), "woowa.com");
    }

    public boolean sameDomain(EmailAddress other) {
        return domain.equals(other.domain);
    }

    public String value() {
        return localPart + "@" + domain;
    }
}

public final class EmailRules {
    private EmailRules() {
    }

    public static boolean looksLikeEmail(String raw) {
        return raw != null
                && raw.contains("@")
                && raw.indexOf('@') == raw.lastIndexOf('@');
    }

    public static String normalizeDomain(String domain) {
        return domain.trim().toLowerCase();
    }
}
```

## 한 번에 비교하는 코드 (계속 2)

| 메서드 | 분류 | 이유 |
|---|---|---|
| `EmailAddress.of(raw)` | simple factory method | 문자열을 받아 `EmailAddress` 객체를 만든다 |
| `EmailAddress.companyAccount(localPart)` | simple factory method | 기본값이 있는 생성 경로를 이름으로 드러낸다 |
| `sameDomain(other)` | 인스턴스 메서드 | 현재 객체의 `domain`을 사용한다 |
| `value()` | 인스턴스 메서드 | 현재 객체 상태를 문자열로 표현한다 |
| `EmailRules.looksLikeEmail(raw)` | `static` 유틸리티 메서드 | 문자열 검사 자체가 목적이고 객체 생성이 아니다 |
| `EmailRules.normalizeDomain(domain)` | `static` 유틸리티 메서드 | 입력 문자열을 정규화하는 보조 동작이다 |

같은 `static`이라도 factory와 utility는 역할이 다르다는 점이 여기서 분명해진다.

- factory: **만든다**
- utility: **도와준다**

## 손으로 분류해 보는 연습

다음 요구사항을 보고 어떤 형태가 자연스러운지 먼저 적어 보자.

1. 이미 만들어진 `Cart`가 무료배송 기준을 넘는지 확인한다.
2. 문자열이 UUID 모양인지 검사한다.
3. 섭씨 값을 받아 `Temperature` 객체를 만든다.
4. 기본 권한이 `GUEST`인 `User` 객체를 만든다.
5. 이미 만들어진 `Order`가 취소 가능한 상태인지 확인한다.

한 가지 자연스러운 답은 아래와 같다.

1. 인스턴스 메서드
   `cart.isFreeShippingEligible()`
2. `static` 유틸리티 메서드
   `UuidRules.looksLikeUuid(raw)`
3. simple factory method
   `Temperature.ofCelsius(value)`
4. simple factory method
   `User.guest()`
5. 인스턴스 메서드
   `order.canCancel()`

이 연습의 핵심은 다음이다.

- 이미 있는 객체의 상태를 읽으면 인스턴스 메서드 쪽이다.
- 범용 검사/계산이면 utility 쪽이다.
- 새 객체를 만들면 factory 쪽이다.

## 초보자가 자주 틀리는 포인트

### `static`이면 더 간단하니 전부 `static`으로 만들고 싶어진다

처음에는 그렇게 느껴지기 쉽다.
하지만 객체 상태와 규칙을 계속 바깥으로 밀어내면, 결국 데이터를 들고 있는 타입은 비어 있고 로직은 utility class에 흩어진다.

그 결과는 보통 다음처럼 나온다.

- 객체는 단순 보관함처럼 변한다
- 불변식이 타입 바깥으로 새어 나간다
- 메서드 호출 문장이 덜 자연스러워진다

### factory method와 utility method를 같은 것으로 느낀다

둘 다 `static`일 수 있지만 목적이 다르다.

- utility는 생성 자체가 목적이 아니다
- factory는 생성 경로를 여는 것이 목적이다

`parse`, `of`, `from`, `valueOf`, `guest`, `zero`처럼 **"무엇을 만들어 돌려주는가"** 가 앞에 나오면 factory일 가능성이 높다.

### public constructor와 public factory를 아무 이유 없이 둘 다 연다

둘 다 열 수는 있지만, 생성 규칙이 두 군데로 갈라지면 초보자는 어느 쪽이 진짜 entrypoint인지 헷갈리기 쉽다.
검증/정규화가 중요하다면 constructor를 감추고 factory를 주 진입점으로 두는 편이 더 명확할 수 있다.

### utility class가 특정 도메인 타입을 계속 넘겨받는데 그대로 둔다

`PriceRules.total(cart)`, `PriceRules.isEmpty(cart)`처럼 같은 타입을 계속 넘겨받는다면 `Cart` 인스턴스 메서드가 더 자연스러운지 다시 봐야 한다.

## 어떤 문서를 다음에 읽으면 좋은가

- method 시그니처, return type, state change를 먼저 손에 익히고 싶다면 [Java 메서드와 생성자 실전 입문](./java-methods-constructors-practice-primer.md)
- `private`, 인스턴스 멤버, `static`, `final`의 기본 모델을 먼저 정리하고 싶다면 [Java 접근 제한자와 멤버 모델 입문](./java-access-modifiers-member-model-basics.md)
- 생성자 chaining과 `static`/instance 초기화 순서까지 이어서 보고 싶다면 [Java 생성자와 초기화 순서 입문](./java-constructors-initialization-order-basics.md)
- 메시지 전달과 캡슐화 관점에서 "왜 객체에 메서드를 붙이는가"를 더 길게 읽고 싶다면 [객체지향 핵심 원리](./object-oriented-core-principles.md)
- 생성 시 검증, 정규화, 값 객체 경계를 더 엄밀하게 보고 싶다면 [Value Object Invariants, Canonicalization, and Boundary Design](./value-object-invariants-canonicalization-boundary-design.md)
- 상태를 쉽게 바꾸지 않는 설계까지 함께 보고 싶다면 [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)

## 한 줄 정리

인스턴스 메서드는 **이미 있는 객체의 상태와 규칙**을 다루고, `static` 유틸리티 메서드는 **상태 없는 보조 계산/검사**를 맡으며, simple factory method는 **객체 생성 경로를 이름 있게 여는 `static` 메서드**다.
