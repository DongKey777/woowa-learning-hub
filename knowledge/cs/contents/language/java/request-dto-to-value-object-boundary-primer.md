# Request DTO에서 raw string을 값 객체로 올리는 경계 입문

> 한 줄 요약: request DTO는 바깥에서 들어온 문자열 상자이고, 값 객체는 안쪽에서 믿고 쓰는 타입이므로, `trim`/정규화/불변식이 중요한 입력은 service 로직 전에 작은 value object로 올려 두는 편이 초보자에게 더 덜 헷갈린다.

**난이도: 🟢 Beginner**

관련 문서:

- [language 카테고리 인덱스](../README.md)
- [Record and Value Object Equality](./record-value-object-equality-basics.md)
- [Domain-State Type Primer: `boolean`/`null` 대신 `enum`, `record`, 값 객체를 언제 쓸까](./domain-state-type-primer-enum-record-value-object.md)
- [Money Value Object Basics](./money-value-object-basics.md)
- [DTO, VO, Entity 기초](../../software-engineering/dto-vo-entity-basics.md)
- [Validation Boundary Mini Bridge](../../software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge.md)

retrieval-anchor-keywords: language-java-00277, request dto value object boundary, dto raw string vs value object, request dto to value object primer, dto에서 값객체 언제, service 전에 값객체로 바꾸기, raw string domain beginner, email value object boundary, validated input before service logic, dto string 그대로 넘겨도 되나요, 처음 dto 값객체 헷갈려, what is request dto boundary, value object basics, equals hashcode set key beginner

## 핵심 개념

처음에는 이렇게 나눠 기억하면 된다.

- request DTO는 "밖에서 들어온 원본 입력"이다
- value object는 "안쪽에서 믿고 쓰는 도메인 값"이다

즉 DTO에 `String email`이 있다고 해서 service도 끝까지 `String`을 붙잡고 있어야 하는 것은 아니다.

오히려 아래 신호가 보이면 service 로직 전에 작은 값 객체로 올리는 편이 안전하다.

- 비어 있으면 안 된다
- `trim`, 소문자화, 단위 통일 같은 정규화가 필요하다
- 같은 값 판단이 중요하다
- `Set`, `Map` key, 중복 체크에 자주 쓰인다

짧게 외우면 이렇다.

> DTO는 "들어온 값", value object는 "검증되어 의미가 고정된 값"이다.

## 한눈에 보기

| 단계 | 손에 든 값 | 여기서 하는 일 | 안쪽으로 넘길 때 기대하는 것 |
|---|---|---|---|
| request DTO | `String email`, `String nickname` | JSON/HTTP 입력을 읽는다 | 아직 raw input일 수 있다 |
| boundary 변환 | `new EmailAddress(request.email())` | 검증, 정규화, 의미 부여 | invalid면 여기서 빠르게 실패 |
| service 로직 | `EmailAddress`, `Nickname` | 비즈니스 규칙 판단 | "이 타입이면 이미 믿을 수 있다" |

초보자 기본값은 아래 한 줄이면 충분하다.

- "웹에서 들어온 문자열"과 "도메인에서 믿고 쓰는 값"을 같은 타입으로 오래 끌고 가지 않는다.

## 왜 raw string을 service까지 오래 들고 가면 헷갈릴까

`String` 자체는 나쁜 타입이 아니다. 문제는 **의미가 너무 넓다**는 데 있다.

예를 들어 service가 아래처럼 raw string을 받기 시작하면, 호출자마다 규칙을 외워야 한다.

```java
void signUp(String email, String nickname) {
    // null, blank, trim, lower-case, 길이 제한을 여기저기서 반복
}
```

이 구조에서 흔히 생기는 혼란은 이렇다.

- 어떤 호출자는 `trim()`을 하고, 어떤 호출자는 안 한다
- `" Foo@Bar.com "`과 `"foo@bar.com"`을 같은 값으로 볼지 매번 달라진다
- `Set<String>` 중복 체크가 입력 표현 차이에 흔들린다

반대로 value object로 올리면 규칙을 타입이 붙잡는다.

```java
new EmailAddress(" Foo@Bar.com ").equals(new EmailAddress("foo@bar.com"))
```

이 식이 `true`가 되도록 만들 수 있으면, 그다음 service와 컬렉션은 "이메일의 같은 값 기준"을 다시 고민하지 않아도 된다.

즉 beginner 관점에서는 value object가 추상적인 DDD 장식이 아니라,
**문자열 규칙을 한곳에 모아 두는 안전한 경계**다.

## Request DTO -> value object로 올리는 1분 예시

회원가입 요청을 아주 작게 보면 이런 흐름이다.

```java
public record SignUpRequest(String email, String nickname) {}
```

```java
import java.util.Locale;

public record EmailAddress(String value) {
    public EmailAddress {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("email is blank");
        }
        value = value.trim().toLowerCase(Locale.ROOT);
    }
}
```

```java
public record Nickname(String value) {
    public Nickname {
        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException("nickname is blank");
        }
        value = value.trim();
    }
}
```

```java
void signUp(SignUpRequest request) {
    memberService.signUp(
        new EmailAddress(request.email()),
        new Nickname(request.nickname())
    );
}
```

이제 service는 raw string 대신 의미가 붙은 타입을 받는다.

```java
void signUp(EmailAddress email, Nickname nickname) {
    // 가입 규칙, 중복 체크, 저장 로직
}
```

여기서 중요한 포인트는 두 가지다.

- DTO는 여전히 외부 계약이므로 `String`이어도 괜찮다
- service에 들어가기 전 한 번만 value object로 올리면 이후 로직이 단순해진다

`equals()`/`hashCode()` 감각도 같이 좋아진다.
이메일을 값 객체로 만들면 `HashSet<EmailAddress>`나 `Map<EmailAddress, Member>`에서 같은 값 기준을 타입이 고정해 줄 수 있기 때문이다.

## 언제 값 객체로 올리고, 언제 문자열로 둬도 될까

모든 `String`을 다 감쌀 필요는 없다.
초보자 기준으로는 아래 표 정도만 기억하면 충분하다.

| 입력 값 | 먼저 떠올릴 선택 | 이유 |
|---|---|---|
| 이메일, 금액, 상품코드처럼 의미와 규칙이 분명한 값 | 값 객체 | 검증, 정규화, equality 기준이 반복된다 |
| 중복 체크나 key로 자주 쓰는 값 | 값 객체 | `equals()`/`hashCode()` 정책을 타입이 잡아 준다 |
| 단순 검색어, 자유 메모, 일회성 표시 문자열 | `String` 유지 가능 | 도메인 규칙보다 전달 자체가 더 중요하다 |
| 아직 규칙이 거의 없는 임시 입력 | `String`으로 시작 가능 | 신호가 쌓이면 나중에 값 객체로 승격해도 된다 |

결정이 헷갈릴 때는 이 질문 하나가 가장 잘 먹힌다.

> "이 문자열 규칙을 호출자 여러 명이 반복해서 외우게 둘 것인가?"

`yes`라면 value object 후보일 가능성이 높다.

## 흔한 오해와 함정

- "`Request DTO`도 record니까 value object 아닌가요?"
  아니다. record 문법과 value object 역할은 다른 질문이다. DTO record는 전달 상자일 수 있고, 값 객체 record는 규칙을 잠근 타입일 수 있다.
- "그럼 DTO 필드를 처음부터 `EmailAddress`로 받으면 되지 않나요?"
  가능은 하지만, beginner 단계에서는 먼저 "외부 계약의 raw input"과 "도메인 안쪽 타입"을 구분해서 보는 편이 더 덜 헷갈린다.
- "Controller 검증이 있으니 value object는 필요 없지 않나요?"
  아니다. controller 검증은 입구 검사이고, value object는 안쪽에서도 계속 유지되는 값 의미다.
- "모든 문자열을 다 값 객체로 감싸야 하나요?"
  아니다. 도메인적으로 중요한 값, 반복 규칙이 있는 값, equality 기준이 중요한 값부터 올리면 된다.
- "service에서 바로 `trim()`하면 더 빠르지 않나요?"
  당장은 빠를 수 있지만, 규칙이 늘어날수록 여러 service와 테스트에 중복이 퍼진다.

## 더 깊이 가려면

- DTO/VO/Entity의 큰 역할 구분은 [DTO, VO, Entity 기초](../../software-engineering/dto-vo-entity-basics.md)
- 입력 검증과 도메인 불변식 경계는 [Validation Boundary Mini Bridge](../../software-engineering/validation-boundary-input-vs-domain-invariant-mini-bridge.md)
- record가 value object와 잘 맞는 이유는 [Record and Value Object Equality](./record-value-object-equality-basics.md)
- 금액처럼 규칙이 더 분명한 예시는 [Money Value Object Basics](./money-value-object-basics.md)
- `enum`, `record`, 값 객체를 언제 갈라 쓰는지 더 넓게 보려면 [Domain-State Type Primer: `boolean`/`null` 대신 `enum`, `record`, 값 객체를 언제 쓸까](./domain-state-type-primer-enum-record-value-object.md)

## 한 줄 정리

request DTO의 raw string은 "밖에서 들어온 값"이고, value object는 "안쪽에서 믿고 쓰는 값"이므로, 규칙과 같은 값 판단이 중요한 입력은 service 전에 작은 값 객체로 올려 두는 편이 더 안전하다.
