# 빌더 패턴

> 한 줄 요약: 복잡한 객체 생성을 생성자 폭발 없이 단계적으로 조립하는 패턴이다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [객체지향 디자인 패턴 기초: 전략, 템플릿 메소드, 팩토리, 빌더, 옵저버](./object-oriented-design-pattern-basics.md)
> - [빌더 패턴 기초 (Builder Pattern Basics)](./builder-pattern-basics.md)
> - [팩토리 (Factory)](./factory.md)
> - [Factory vs Abstract Factory vs Builder](./factory-vs-abstract-factory-vs-builder.md)
> - [요청 모델에서 record로 끝낼까, 정적 팩토리/빌더로 올릴까](./record-vs-builder-request-model-chooser.md)
> - [전략 (Strategy)](./strategy-pattern.md)
> - [템플릿 메소드 (Template Method)](./template-method.md)
> - [안티 패턴](./anti-pattern.md)

retrieval-anchor-keywords: builder pattern, step by step object construction, builder vs constructor, builder vs factory, builder vs setter, immutable object builder, build method validation, when to use builder, beginner builder pattern, fluent builder mutation smell, lombok builder confusion, builder pattern mental model, builder 선택 기준, builder decision checklist, build 검증 예시, builder required field validation, constructor parameter order confusion

---

## 먼저 멘탈 모델

처음에는 "초안 작성 -> 최종 제출"로 보면 된다.

```text
new Order(...)                 -> 값을 한 번에 넣는다
Order.builder() ... .build()   -> 초안에 값을 채우고 마지막에 완성한다
```

빌더의 본질은 객체를 여러 번 만들거나 똑똑한 로직을 넣는 게 아니라, **"어떤 값을 왜 넣는지 호출부에서 읽히게 만드는 것"**이다.

| 지금 고민 | 먼저 보는 선택지 | 이유 |
|---|---|---|
| 필드가 2~3개고 필수값만 있다 | 생성자 / 정적 팩토리 | 더 짧고 단순하다 |
| 필수/선택값이 섞여 있고 인자가 많다 | 빌더 | 이름 있는 단계 조립이 읽기 쉽다 |
| 요청마다 다른 구현 타입을 고른다 | 팩토리 / 전략 | 이건 "조립"보다 "선택" 문제다 |

## 15초 선택 루틴

아래 질문에 `예`가 2개 이상이면 빌더를 우선 후보로 둔다.

1. `new Foo(a, b, c, d...)` 호출이 길어져 값 의미를 자주 헷갈리는가?
2. 필수값과 선택값이 섞여 누락/순서 실수가 반복되는가?
3. `build()` 시점에 필수값 검증을 한곳으로 모으고 싶은가?

`아니오`가 대부분이면 생성자나 정적 팩토리가 더 단순하다.

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

### 3. `build()`에서 검증을 모은다

빌더가 필수값 검증을 자동으로 해주지는 않는다. 초보자가 가장 자주 놓치는 지점이라 `build()`를 "최종 검문소"로 두는 습관이 중요하다.

```java
public Order build() {
    if (userId == null || userId.isBlank()) {
        throw new IllegalStateException("userId is required");
    }
    if (quantity <= 0) {
        throw new IllegalStateException("quantity must be positive");
    }
    return new Order(userId, itemId, quantity, couponCode, giftWrap, memo);
}
```

이렇게 하면 "체이닝은 자유롭게, 도메인 유효성은 마지막에 한 번"이라는 경계를 유지할 수 있다.

### 4. Lombok `@Builder`

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

### 5. JDK와의 연결

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

## 자주 헷갈리는 포인트

- **"체이닝이면 다 빌더인가요?"**: 아니다. `this`를 계속 반환한다고 빌더는 아니다. `build()`로 완성 객체를 만드는지 본다.
- **"빌더를 쓰면 검증이 자동인가요?"**: 아니다. 필수값 검증은 `build()`에 직접 넣어야 한다.
- **"Lombok `@Builder`면 패턴 이해가 끝났나요?"**: 아니다. Lombok은 코드 생성 도구다. 설계 판단은 개발자가 해야 한다.
- **"빌더를 DI 대신 써도 되나요?"**: 아니다. 빌더는 요청/DTO/값 객체 조립에 가깝고, 서비스 의존성 관리는 DI 영역이다.

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

## 다음 학습 경로 (상황별)

- "빌더를 처음 배우는 중"이면: [빌더 패턴 기초](./builder-pattern-basics.md)
- "팩토리/빌더를 계속 헷갈림"이면: [Factory vs Abstract Factory vs Builder](./factory-vs-abstract-factory-vs-builder.md)
- "요청 모델에 빌더가 과한지 판단이 필요"하면: [요청 모델에서 record로 끝낼까, 정적 팩토리/빌더로 올릴까](./record-vs-builder-request-model-chooser.md)
- "체이닝 코드가 빌더인지 mutation helper인지 애매"하면: [Builder vs Fluent Mutation Smell](./builder-vs-fluent-mutation-smell.md)

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
