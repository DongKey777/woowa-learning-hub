# 빌더 패턴

> 한 줄 요약: 복잡한 객체 생성을 생성자 폭발 없이 단계적으로 조립하는 패턴이다.

**난이도: 🟢 Basic**

> 관련 문서:
> - [팩토리 (Factory)](./factory.md)
> - [전략 (Strategy)](./strategy-pattern.md)
> - [템플릿 메소드 (Template Method)](./template-method.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

빌더 패턴은 생성자 파라미터가 많아지거나, 필수값과 선택값이 섞이거나, 객체 생성 과정이 복잡할 때 사용한다.

핵심은 두 가지다.

- 객체의 생성 과정을 분리한다.
- 생성 중간 상태를 명시적으로 표현한다.

Java에서는 `new Foo(...)` 대신 `Foo.builder()...build()` 형태가 대표적이다.  
Lombok `@Builder` 때문에 더 자주 보이지만, 패턴 자체는 Lombok보다 훨씬 오래된 개념이다.

---

## 깊이 들어가기

### 1. 생성자 폭발을 피한다

생성자에 선택값이 계속 붙으면 시그니처가 읽기 어려워진다.

```java
public class Order {
    private final String userId;
    private final String itemId;
    private final int quantity;
    private final String couponCode;
    private final boolean giftWrap;
    private final String memo;

    public Order(String userId, String itemId, int quantity, String couponCode, boolean giftWrap, String memo) {
        this.userId = userId;
        this.itemId = itemId;
        this.quantity = quantity;
        this.couponCode = couponCode;
        this.giftWrap = giftWrap;
        this.memo = memo;
    }
}
```

무엇이 필수이고 무엇이 선택인지 읽기 어렵다.

### 2. 빌더는 의도를 드러낸다

```java
Order order = Order.builder()
    .userId("user-1")
    .itemId("item-9")
    .quantity(2)
    .couponCode("WELCOME")
    .giftWrap(true)
    .memo("leave at door")
    .build();
```

이 구조는 호출부에서 의도를 읽기 쉽다.

### 3. Lombok `@Builder`

Lombok은 보일러플레이트를 줄여준다.

```java
@Builder
public class Order {
    private final String userId;
    private final String itemId;
    private final int quantity;
    private final String couponCode;
}
```

다만 Lombok은 문법이 아니라 도구다.  
빌더 패턴 자체를 이해하지 못하면 `@Builder`만 붙이고도 여전히 잘못된 객체를 만들 수 있다.

### 4. JDK와의 연결

JDK에는 이름에 빌더가 직접 붙지 않아도 같은 사고방식이 많다.

- `StringBuilder`: 여러 단계로 문자열을 조립한다
- `ProcessBuilder`: 프로세스 실행 옵션을 단계적으로 설정한다
- `HttpRequest.Builder`: 요청 구성을 단계적으로 만든다

이런 API는 "객체를 한 번에 완성하지 않고, 조립 과정을 드러낸다"는 점에서 빌더 사고와 가깝다.

---

## 실전 시나리오

### 시나리오 1: 복잡한 요청 DTO

필드가 많고 선택값이 많을수록 빌더는 읽기 쉬워진다.  
특히 API 요청 객체나 테스트 픽스처에서 효과가 크다.

### 시나리오 2: 불변 객체 생성

빌더는 `final` 필드와 잘 맞는다.  
생성 후 변경이 필요 없는 객체를 만들 때 유리하다.

### 시나리오 3: 잘못된 사용

아무 객체에나 빌더를 붙이면 오히려 중복이 늘어난다.  
필드가 2~3개뿐인 단순 객체는 생성자나 정적 팩토리가 더 낫다.

---

## 코드로 보기

### Before

```java
Order order = new Order("user-1", "item-9", 2, "WELCOME", true, "leave at door");
```

파라미터 순서를 기억해야 한다.

### After

```java
Order order = Order.builder()
    .userId("user-1")
    .itemId("item-9")
    .quantity(2)
    .couponCode("WELCOME")
    .giftWrap(true)
    .memo("leave at door")
    .build();
```

의도가 보인다.

### `toBuilder`

```java
Order updated = order.toBuilder()
    .memo("call on arrival")
    .build();
```

기존 객체를 복사하되 일부만 바꿀 때 유용하다.

### `@Singular`

```java
@Builder
public class Notification {
    @Singular
    private final java.util.List<String> recipients;
}
```

컬렉션 필드가 있을 때 반복 추가를 자연스럽게 표현할 수 있다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|------|------|------|----------------|
| 생성자 | 단순하다 | 인자가 많아지면 읽기 어렵다 | 필드가 적을 때 |
| 정적 팩토리 | 이름이 있다 | 옵션이 많으면 복잡해진다 | 경우가 몇 가지로 나뉠 때 |
| 빌더 | 선택값과 조립 과정이 드러난다 | 객체 수가 늘고 코드가 길어진다 | 옵션이 많고 생성이 복잡할 때 |

빌더는 "무조건 좋은 생성 방식"이 아니다.  
객체가 작고 단순하면 생성자나 정적 팩토리가 더 낫다.

### 빌더를 쓰면 안 되는 신호

- 파라미터가 2~3개뿐이다
- 생성 중간 상태가 의미 없다
- 생성자보다 읽기 쉬워지지 않는다

---

## 꼬리질문

> Q: 빌더와 정적 팩토리 중 언제 빌더를 선택하는가?
> 의도: 생성 방식 선택 기준을 아는지 확인
> 핵심: 선택값이 많고 읽기 쉬워야 할 때

> Q: Lombok `@Builder`를 왜 그대로 쓰지 말고 이해해야 하는가?
> 의도: 도구와 패턴을 구분하는지 확인
> 핵심: 패턴 자체를 모르면 오용하기 쉽다

> Q: `toBuilder()`는 언제 유용한가?
> 의도: 불변 객체와 부분 수정의 연결 이해 확인
> 핵심: 기존 객체를 기반으로 일부만 바꿀 때

---

## 한 줄 정리

빌더는 복잡한 객체 생성 과정을 읽기 쉽게 만드는 패턴이다. 단순한 객체에는 과한 추상화가 될 수 있다.
