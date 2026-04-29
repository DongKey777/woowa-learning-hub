# Record and Value Object Equality

> 한 줄 요약: `record`는 "이 필드들이 곧 값이다"를 선언할 때 잘 맞고, 시간에 따라 상태가 바뀌는 entity에는 기본 선택이 아니다. sorted collection, comparator, `BigDecimal` 정책은 첫 읽기 뒤 follow-up으로 넘긴다.

**난이도: 🟢 Beginner**

관련 문서:

- [Language README](../README.md)
- [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md)
- [Java Array Equality Basics](./java-array-equality-basics.md)
- [불변 객체와 방어적 복사](./immutable-objects-and-defensive-copying.md)
- [Comparator Consistency With `equals()` Bridge](./comparator-consistency-with-equals-bridge.md)

retrieval-anchor-keywords: java record equality, java record equals hashcode, record value object basics, record vs entity beginner, record 언제 쓰나요, record 왜 equals 자동, record equality 헷갈, record mutable field bug, record array equality, record list copyof, java value object equality, 처음 배우는 record equality

## 먼저 잡을 멘탈 모델

처음엔 `record`를 "코드 줄이는 문법"보다 "값 경계를 적는 문법"으로 보는 편이 안전하다.

| 질문 | `yes`면 보통 | `no`면 보통 |
|---|---|---|
| 현재 필드 값이 곧 의미인가 | `record` / value object | entity-style class |
| 생성 후 거의 안 바꾸는가 | `record`가 잘 맞음 | mutable class 검토 |
| `Set` 원소나 `Map` key로 쓸 수 있어야 하나 | 불변 value가 유리 | 비교 기준 설계부터 다시 봄 |

짧게 외우면 이렇다.

- `record`: 같은 값이면 같은 것으로 봐도 되는 타입
- entity: 시간이 지나도 같은 대상을 추적해야 하는 타입

## 처음엔 여기까지만 잡으면 된다

`record` beginner 문서에서 가장 흔한 scope creep은 "`record`도 배웠으니 comparator, `TreeMap`, `BigDecimal`, serialization까지 한 번에 봐야 하나요?"로 번지는 것이다.

이 문서에서는 아래 두 질문만 먼저 붙이면 충분하다.

1. 이 타입이 "현재 필드 값이 곧 의미"인 value object인가?
2. component가 배열이나 가변 컬렉션처럼 equality를 흔들 수 있는가?

정렬 기준 충돌, 금액 canonicalization, 직렬화 진화는 모두 다음 한 칸 주제다.

## `record`의 `equals()`/`hashCode()`는 무엇을 보나

`record`는 header에 적은 component 전체를 기준으로 `equals()`와 `hashCode()`를 만든다.

```java
public record Money(String currency, long amount) {}
```

위 타입은 `currency`와 `amount`가 모두 같아야 같은 값이다.

```java
Money a = new Money("KRW", 1000L);
Money b = new Money("KRW", 1000L);

System.out.println(a.equals(b)); // true
```

초보자용 첫 규칙은 한 줄이면 충분하다.

- component에 적은 필드가 곧 value 의미다

그래서 `record`를 고를 때는 "필드가 많으니 줄이자"보다 "이 필드 전부를 같은 값 기준으로 써도 되나"를 먼저 묻는다.

## 언제 `record`가 잘 맞나

아래처럼 "현재 값 자체"가 중요한 타입은 `record`와 잘 맞는다.

| 타입 예시 | 왜 잘 맞나 |
|---|---|
| `EmailAddress` | 정규화된 문자열 값이 곧 의미다 |
| `Money` | 통화 + 금액 값이 같으면 같은 값이다 |
| `Coordinate` | x, y 값 조합이 곧 의미다 |

```java
public record EmailAddress(String value) {}
```

이런 타입은 `HashSet` 원소나 `Map` key로도 비교적 안전하다. 단, component가 실제로도 불변에 가깝다는 전제가 있어야 한다.

## 언제 `record`가 위험해지나

아래처럼 "상태가 바뀌어도 같은 대상"이어야 하는 타입은 `record` 기본 동작이 어긋날 수 있다.

| 타입 예시 | 왜 조심하나 |
|---|---|
| `Order` | 상태와 주소가 바뀌어도 같은 주문이다 |
| `MemberAccount` | 비밀번호, 상태가 바뀌어도 같은 계정이다 |
| `Reservation` | 시간 변경이 곧 다른 대상은 아니다 |

예를 들어 주문 상태가 바뀌었다고 주문 자체가 다른 값이 되면 entity 추적이 꼬일 수 있다.

- value object 질문: "지금 값이 같은가?"
- entity 질문: "시간이 지나도 같은 대상인가?"

`record`는 첫 질문에 강하고, 둘째 질문이 중심이면 일반 class에서 equality 정책을 따로 정하는 편이 안전하다.

## 초보자가 자주 놓치는 함정 3개

| 함정 | 왜 문제인가 | 먼저 할 일 |
|---|---|---|
| 배열 component | 배열은 값보다 참조 비교처럼 보이기 쉽다 | [Java Array Equality Basics](./java-array-equality-basics.md)로 분기 |
| 가변 `List` component | record는 얕은 불변만 준다 | 생성 시 복사 또는 불변 컬렉션 검토 |
| mutable field를 key처럼 사용 | `Set`/`Map` 조회가 흔들릴 수 있다 | [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md)로 분기 |

짧은 예시는 아래와 같다.

```java
public record Tags(String[] values) {}

System.out.println(
        new Tags(new String[] {"java"}).equals(new Tags(new String[] {"java"}))
); // false
```

배열은 내용이 같아 보여도 바로 값 비교가 되지 않을 수 있다. "왜 `record`인데 false지?"가 보이면 `record` 자체보다 component 타입의 equality를 먼저 본다.

## 증상별로 다음 문서 고르기

| 지금 보이는 증상 | 이 문서에서 먼저 결론낼 것 | 다음 문서 |
|---|---|---|
| "`record`인데 왜 `equals()`가 false지?" | component 타입이 배열/가변 값인지 확인 | [Java Array Equality Basics](./java-array-equality-basics.md) |
| "`HashSet`/`HashMap`에 넣었더니 조회가 흔들린다" | component 또는 key가 mutable한지 확인 | [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md) |
| "`TreeSet`/`TreeMap`에서 결과가 다르다" | 이 문서는 해시 기준까지만 본다고 선 긋기 | [Comparator Consistency With `equals()` Bridge](./comparator-consistency-with-equals-bridge.md) |
| "`BigDecimal` component도 그냥 같다고 보면 되나요?" | 금액 동등성 정책은 별도라고 분리 | [Record component로 `BigDecimal`을 써도 되나요?](./record-bigdecimal-component-faq.md) |

## `record` 안에서 안전하게 시작하는 방법

처음엔 아래 세 가지를 기본값으로 두면 실수가 줄어든다.

1. component는 가능하면 immutable 타입으로 고른다.
2. `List`를 받으면 `List.copyOf(...)` 같은 방어적 복사를 먼저 검토한다.
3. `Set`/`Map` key로 쓸 타입이면 생성 후 값이 안 바뀌게 둔다.

```java
import java.util.List;

public record Roles(List<String> values) {
    public Roles {
        values = List.copyOf(values);
    }
}
```

이 코드는 "record도 깊은 불변은 아니다"라는 함정을 beginner 단계에서 먼저 막아 준다.

## 흔한 헷갈림

- "`record`면 무조건 value object인가요?"
  - 아니다. 문법은 같아도 도메인 의미가 entity면 기본 선택이 아닐 수 있다.
- "`record`면 컬렉션에서 항상 안전한가요?"
  - 아니다. component가 배열이거나 가변 컬렉션이면 바로 흔들릴 수 있다.
- "`record`면 `TreeSet`도 `equals()`만 보면 되나요?"
  - 아니다. sorted collection은 comparator/ordering follow-up 주제다.

처음엔 여기까지만 잡고, 정렬 기준 충돌이나 `BigDecimal` 정책은 관련 follow-up 문서로 넘기는 편이 낫다.

## 다음 한 칸

- "`==`와 `equals()`가 아직도 섞인다"면 [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- "`HashSet` 중복이나 `HashMap` 조회가 왜 깨지지?"면 [Collections, Equality, and Mutable-State Foundations](./collections-equality-mutable-state-foundations.md)
- "배열 component가 왜 false지?"면 [Java Array Equality Basics](./java-array-equality-basics.md)
- "`TreeSet`/`TreeMap`까지 같이 헷갈린다"면 [Comparator Consistency With `equals()` Bridge](./comparator-consistency-with-equals-bridge.md)

## 한 줄 정리

`record`는 "이 필드 전체가 같은 값 기준이다"가 맞을 때 쓰고, 상태가 바뀌어도 같은 대상을 추적해야 하면 entity 규칙을 먼저 세우는 편이 안전하다.
