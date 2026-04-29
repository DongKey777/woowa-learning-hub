# Null Object Pattern: null 대신 아무 일도 하지 않는 객체를 넣기

> 한 줄 요약: Null Object 패턴은 null 체크를 흩뿌리는 대신, 기본 동작을 가진 빈 구현체를 넣어 호출부를 단순화한다.

**난이도: 🟡 Intermediate**


관련 문서:

- [디자인 패턴 카테고리 인덱스](./README.md)
- [상속보다 조합 기초](./composition-over-inheritance-basics.md)
- [전략 패턴](./strategy-pattern.md)
- [실전 패턴 선택 가이드](./pattern-selection.md)
- [Java Optional 입문](../language/java/java-optional-basics.md)
- [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](../language/java/optional-collections-domain-null-handling-bridge.md)
- [연결 입문 문서](../software-engineering/oop-design-basics.md)


retrieval-anchor-keywords: null object pattern, null object 뭐예요, null 대신 객체 넣는 패턴, null 체크 없애는 패턴, 처음 배우는데 null object, 왜 null check가 많아져요, optional vs null object, null object vs optional, null object 언제 쓰는지, noop object, no-op notifier, 기본 동작 객체 패턴, 없는 대신 아무 일도 안 하는 객체, collaborator default object, if null check 줄이기
> 관련 문서:
> - [전략 패턴](./strategy-pattern.md)
> - [상속보다 조합 기초](./composition-over-inheritance-basics.md)
> - [실전 패턴 선택 가이드](./pattern-selection.md)
> - [Java Optional 입문](../language/java/java-optional-basics.md)
> - [`Optional`에서 끝낼까, 컬렉션/도메인 타입으로 옮길까 beginner bridge](../language/java/optional-collections-domain-null-handling-bridge.md)

---

## 핵심 개념

이 문서는 `null object pattern 뭐예요`, `null 대신 객체를 넣어도 돼요?`, `optional이랑 뭐가 달라요?` 같은 첫 질문을 먼저 받는 primer다.

Null Object 패턴은 **null을 특별 취급하지 않도록 "아무 일도 하지 않는 객체"를 제공**하는 패턴이다.
핵심은 호출부가 `if (x != null)`에 매번 신경 쓰지 않게 만드는 것이다.

backend에서는 다음과 같이 자주 쓰인다.

- 알림이 없어도 되는 경우
- 로깅이나 메트릭이 선택적인 경우
- 할인/쿠폰/추천이 없어도 흐름이 이어져야 하는 경우

### Retrieval Anchors

- `null object pattern`
- `noop implementation`
- `default behavior`
- `sentinel object`
- `avoid null checks`

---

## 깊이 들어가기

### 1. null과 빈 객체는 다르다

null은 "없음"이고, Null Object는 "존재하지만 아무 일도 하지 않음"이다.

이 차이는 호출부에서 중요하다.

- null이면 분기문이 늘어난다
- 빈 객체면 동일한 인터페이스로 계속 호출할 수 있다

### 2. 기본 구현이 필요한 이유

기본 구현이 있으면 다음 문제가 줄어든다.

- NPE 방지
- 조건문 중복 제거
- 테스트에서 stub 생성 단순화

### 3. 하지만 의미를 숨길 수도 있다

Null Object는 편하지만, 무조건 좋은 건 아니다.

- 중요한 누락이 가려질 수 있다
- 데이터가 정말 없는지, 기본값인지 구분이 어려울 수 있다
- "없음"이 도메인적으로 중요한 경우엔 위험하다

---

## 실전 시나리오

### 시나리오 1: 알림 수신자 없음

사용자가 알림을 끄면 `NoOpNotifier`를 넣어 호출부를 단순하게 유지할 수 있다.

### 시나리오 2: 할인 정책 없음

쿠폰이 없을 때도 `NoDiscountPolicy`를 넣으면 계산 흐름이 깔끔해진다.

### 시나리오 3: 감사 로그 선택적 비활성화

운영 환경에 따라 로깅 구현을 바꾸되, 호출부는 그대로 유지할 수 있다.

---

## 코드로 보기

### Before: null 체크가 흩어진다

```java
public class OrderService {
    private final Notifier notifier;

    public OrderService(Notifier notifier) {
        this.notifier = notifier;
    }

    public void completeOrder(Order order) {
        order.complete();
        if (notifier != null) {
            notifier.notify(order);
        }
    }
}
```

### After: Null Object

```java
public interface Notifier {
    void notify(Order order);
}

public class EmailNotifier implements Notifier {
    @Override
    public void notify(Order order) {
        // 이메일 발송
    }
}

public class NoOpNotifier implements Notifier {
    @Override
    public void notify(Order order) {
        // 아무 일도 하지 않음
    }
}

public class OrderService {
    private final Notifier notifier;

    public OrderService(Notifier notifier) {
        this.notifier = notifier;
    }

    public void completeOrder(Order order) {
        order.complete();
        notifier.notify(order);
    }
}
```

### Optional 대신 사용할 때

```java
public interface DiscountPolicy {
    int apply(int amount);
}

public class NoDiscountPolicy implements DiscountPolicy {
    @Override
    public int apply(int amount) {
        return amount;
    }
}
```

호출부는 "할인 정책이 있나?"를 묻지 않고, 그냥 적용한다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| null 체크 | 가장 직접적이다 | 중복이 쌓인다 | 한 번만 확인하면 될 때 |
| Optional | 의도가 명확하다 | 도메인 객체로 쓰기엔 무겁다 | 반환값 처리 |
| Null Object | 호출부가 단순해진다 | 누락을 숨길 수 있다 | 기본 동작이 자연스러울 때 |

판단 기준은 다음과 같다.

- "없음"이 자연스러운 기본값이면 Null Object
- "없음"이 중요한 상태면 명시적으로 다뤄야 한다
- 반환값은 Optional, 협력 객체는 Null Object가 자주 맞는다

---

## 꼬리질문

> Q: Null Object와 Optional은 어떻게 다르나요?
> 의도: 반환값과 협력 객체의 차이를 아는지 확인한다.
> 핵심: Optional은 값의 부재를 표현하고, Null Object는 행동을 가진 기본 구현이다.

> Q: Null Object가 위험한 경우는 언제인가요?
> 의도: 누락을 숨기는 부작용을 아는지 확인한다.
> 핵심: "정말로 없어야 하는데 기본값으로 넘어가는" 상황이다.

> Q: if문 제거만이 목적이면 Null Object를 써도 되나요?
> 의도: 패턴 과사용을 경계하는지 확인한다.
> 핵심: 아니다. 도메인 의미가 유지될 때만 써야 한다.

## 한 줄 정리

Null Object 패턴은 null 체크를 줄이기 위해 기본 동작을 가진 빈 구현체를 넣는 패턴이다.
