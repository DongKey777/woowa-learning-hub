# Enum equality quick bridge

> 한 줄 요약: Java `enum` 상수는 각 값이 하나뿐인 singleton처럼 만들어지기 때문에 `==`와 `equals()`가 둘 다 맞고, 초급 코드에서는 null-safe 비교 의도까지 잘 드러나는 `==`를 관용적으로 쓴다.

**난이도: 🟢 Beginner**

관련 문서:

- [Java enum 기초](./java-enum-basics.md)
- [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- [Enum에서 상태 전이 모델로 넘어가는 첫 브리지](./enum-to-state-transition-beginner-bridge.md)
- [Java Optional 입문](./java-optional-basics.md)
- [객체지향 설계 기초](../../software-engineering/oop-design-basics.md)
- [language 카테고리 인덱스](../README.md)

retrieval-anchor-keywords: enum equality bridge, java enum == vs equals, enum equals 왜 돼요, enum == 왜 돼요, java enum singleton basics, enum 비교는 뭘 써야 하나, enum identity equality beginner, java enum compare with ==, enum null safe comparison, 처음 배우는데 enum equals, enum equals null, enum comparison idiom

## 핵심 개념

`enum`은 "값이 몇 개 안 되는 특수한 클래스"처럼 보이지만, 실제 사용 감각은 더 단순하다. `OrderStatus.PAID`라는 값은 실행 중에 새로 계속 만들어지는 객체가 아니라, 그 상수 하나를 대표하는 인스턴스 하나다.

그래서 같은 enum 상수를 비교할 때는 다음 둘이 모두 맞게 동작한다.

- `status == OrderStatus.PAID`
- `status.equals(OrderStatus.PAID)`

초급자가 헷갈리는 지점은 "참조형이면 원래 `equals()`를 써야 하는 것 아닌가?"라는 감각이다. enum은 참조형이지만, 각 상수가 singleton처럼 고정되어 있어서 `==`가 곧 "같은 enum 상수인가"라는 질문과 정확히 맞아떨어진다.

## 한눈에 보기

| 비교식 | 왜 동작하나 | 초급 코드 기본 선택 |
|---|---|---|
| `status == OrderStatus.PAID` | enum 상수는 각 값당 인스턴스가 하나라서 같은 상수면 같은 참조다 | 가장 권장 |
| `status.equals(OrderStatus.PAID)` | `Enum.equals()`도 결국 같은 상수인지 본다 | 가능하지만 덜 관용적 |
| `status == null` | null 여부를 바로 본다 | null 체크에 적합 |
| `status.equals(null)` | 항상 `false`지만 `status`가 null이면 NPE 가능 | 피하는 편이 안전 |

핵심 문장은 이것 하나면 충분하다.

> enum은 "값 비교를 위해 새 규칙을 만든 객체"라기보다, "상수 하나당 객체 하나가 고정된 타입"이라서 `==`가 자연스럽다.

## 왜 `==`와 `equals()`가 둘 다 맞을까

예를 들어 enum을 이렇게 선언했다고 하자.

```java
enum OrderStatus {
    READY, PAID, CANCELLED
}
```

이때 `OrderStatus.PAID`는 필요할 때마다 새 객체를 만드는 값이 아니다. JVM 안에서 그 상수 인스턴스 하나를 재사용한다. 그래서 아래 비교는 둘 다 `true`다.

```java
OrderStatus left = OrderStatus.PAID;
OrderStatus right = OrderStatus.PAID;

System.out.println(left == right);      // true
System.out.println(left.equals(right)); // true
```

초급자 mental model은 이렇게 잡으면 충분하다.

1. enum 상수마다 대표 객체가 하나 있다.
2. 같은 상수 이름을 가리키면 같은 객체를 본다.
3. 그래서 `==`와 `equals()` 결과가 같게 나온다.

즉 여기서는 `String`처럼 "내용은 같지만 다른 객체일 수 있음"을 걱정할 필요가 없다.

## 관용적으로 왜 `==`를 쓸까

실무와 학습 코드에서는 보통 `==`를 먼저 쓴다. 이유는 거창하지 않고, 읽기와 안전성 측면에서 더 직접적이기 때문이다.

| 이유 | `==`가 주는 장점 |
|---|---|
| 의도가 바로 보인다 | "이 enum 상수인가?"를 한눈에 읽는다 |
| null에 안전하다 | `status == OrderStatus.PAID`는 `status`가 null이어도 NPE가 없다 |
| enum의 성질과 맞다 | singleton 상수 비교이므로 identity 비교가 곧 값 비교다 |

특히 null 가능성이 있을 때 차이가 더 잘 보인다.

```java
if (status == OrderStatus.PAID) {
    ship();
}
```

위 코드는 `status`가 null이어도 그냥 `false`다. 반면 아래 코드는 `status`가 null이면 예외가 난다.

```java
if (status.equals(OrderStatus.PAID)) {
    ship();
}
```

그래서 enum 비교에서는 "`String`은 `equals()`, enum은 `==`"라는 초급 규칙을 먼저 잡아 두면 실수가 줄어든다.

## 흔한 오해와 함정

### 1. "참조형이면 무조건 `equals()`다"

참조형 전부가 같은 규칙을 쓰는 것은 아니다.

- `String`은 내용 비교가 중요해서 `equals()`
- enum은 상수 인스턴스가 고정되어 있어서 `==`

즉 "참조형"보다 "그 타입이 같은 값을 어떻게 표현하나"를 봐야 한다.

### 2. "enum에서 `equals()`를 쓰면 더 객체지향적이다"

그렇게 볼 이유는 거의 없다. enum에서는 `==`가 더 짧고, 더 읽기 쉽고, null-safe하다.

### 3. "외부 문자열과도 `==`처럼 비교하면 되나"

안 된다. `"PAID"` 같은 문자열 입력은 먼저 enum으로 변환한 뒤 비교해야 한다.

```java
OrderStatus status = OrderStatus.valueOf("PAID");
if (status == OrderStatus.PAID) {
    ship();
}
```

문자열 자체를 enum 상수와 직접 비교하는 감각으로 넘어가면 안 된다.

## 실무에서 쓰는 모습

미션 코드에서 가장 흔한 형태는 상태 분기다.

```java
if (reservationStatus == ReservationStatus.CONFIRMED) {
    // 입장 가능
}
```

또는 switch로 바로 이어진다.

```java
switch (reservationStatus) {
    case REQUESTED -> ...
    case CONFIRMED -> ...
    case CANCELLED -> ...
}
```

여기서 중요한 연결은 두 가지다.

- enum 비교는 `==`로 간단히 둔다
- 상태 전이 규칙 자체는 `confirm()`, `cancel()` 같은 도메인 메서드로 모은다

즉 enum 비교는 "지금 어떤 상태인가"를 읽는 입구이고, 그다음 설계는 [Enum에서 상태 전이 모델로 넘어가는 첫 브리지](./enum-to-state-transition-beginner-bridge.md)로 이어진다.

## 더 깊이 가려면

- enum 문법, `name()`, `ordinal()` 큰 그림부터 다시 보면 [Java enum 기초](./java-enum-basics.md)
- `String`, 사용자 정의 객체, `hashCode()`까지 비교 규칙을 한 번에 잇고 싶다면 [Java Equality and Identity Basics](./java-equality-identity-basics.md)
- enum을 상태 전이 규칙까지 확장하는 다음 단계는 [Enum에서 상태 전이 모델로 넘어가는 첫 브리지](./enum-to-state-transition-beginner-bridge.md)

## 한 줄 정리

enum은 상수마다 인스턴스가 하나로 고정된 타입이라 `==`와 `equals()`가 둘 다 맞지만, 의도 표현과 null 안전성 때문에 관용적으로 `==`를 쓴다.
