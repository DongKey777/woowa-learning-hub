# 전략 패턴 기초 (Strategy Pattern Basics)

> 한 줄 요약: 전략 패턴은 알고리즘(행동)을 별도 객체로 분리해 런타임에 교체할 수 있게 만드는 패턴으로, if-else 분기보다 변경 축을 명확하게 나누고 싶을 때 쓴다.

**난이도: 🟢 Beginner**

관련 문서:

- [전략 (Strategy) — 심화](./strategy-pattern.md)
- [전략 폭발 냄새](./strategy-explosion-smell.md)
- [디자인 패턴 카테고리 인덱스](./README.md)
- [IoC 컨테이너와 DI](../spring/ioc-di-container.md)

retrieval-anchor-keywords: strategy pattern basics, 전략 패턴, strategy pattern beginner, 전략 패턴이 뭔가요, context strategy interface, 알고리즘 교체, if-else 대신 전략, when to use strategy pattern, strategy pattern example, 결제 수단 전략, 할인 정책 전략, runtime 구현 교체, strategy vs if-else

---

## 핵심 개념

전략 패턴은 "무엇을 할지"는 `Context`가 결정하고, "어떻게 할지"는 `Strategy` 구현체가 결정하도록 역할을 나누는 패턴이다. `Context`는 구체 구현 대신 공통 인터페이스(`Strategy`)에만 의존하므로, 구현체를 교체해도 `Context`를 바꿀 필요가 없다.

입문자가 자주 막히는 지점은 "if-else와 결과가 같은데 왜 구조를 키우나?"라는 의문이다. 핵심은 **변경 축의 분리**다. 새 결제 수단이나 새 할인 정책이 추가될 때 기존 코드를 건드리지 않고 새 구현체만 추가하면 된다.

## 한눈에 보기

```
Context (주문 처리)
    └─ Strategy 인터페이스 (pay)
            ├─ CardPayment
            ├─ CashPayment
            └─ VoucherPayment
```

| 역할 | 설명 |
|------|------|
| Context | 전략을 보유하고 실행 흐름을 가짐 |
| Strategy 인터페이스 | 공통 행동을 정의하는 추상화 |
| 구현체 (Concrete Strategy) | 실제 알고리즘/행동을 담은 클래스 |

## 상세 분해

전략 패턴의 세 가지 구성 요소:

- **Strategy 인터페이스** — 교체 가능한 행동의 공통 계약을 정의한다. 예: `PaymentStrategy.pay(int amount)`.
- **Concrete Strategy** — 인터페이스를 구현한 실제 알고리즘 클래스다. 예: `CardPaymentStrategy`, `CashPaymentStrategy`.
- **Context** — Strategy 인터페이스에 의존하며, 구체 구현은 모른다. 주입받거나 설정에서 받아 실행한다.

```java
public interface DiscountStrategy {
    int apply(int price);
}

public class VipDiscount implements DiscountStrategy {
    public int apply(int price) { return (int)(price * 0.8); }
}
```

## 흔한 오해와 함정

- **"if-else를 없애는 게 목적이다"** — 목적은 변경 축을 나누는 것이지 분기를 없애는 것이 아니다. 구현이 2개이고 단순하다면 if-else가 더 읽기 쉬울 수 있다.
- **"구현체 수가 많아야 전략이다"** — 구현체가 1개라도 교체 가능성이 있고 테스트에서 가짜를 넣어야 한다면 전략이 유용하다.
- **"전략 = 행동을 주입하는 모든 것"** — 람다나 함수도 넓게 보면 전략이지만, 이름 있는 역할·협력 객체·독립 테스트가 필요할 때 Strategy 타입으로 분리한다.

## 실무에서 쓰는 모습

**결제 수단 선택**: `OrderService`는 `PaymentStrategy`에만 의존하고, 카드/현금/바우처 구현체는 런타임에 주입된다. 새 결제 수단이 추가돼도 `OrderService`는 그대로다.

**할인 정책 적용**: 회원 등급별로 다른 `DiscountStrategy`를 Map에 등록해두고 등급 키로 꺼내 실행한다. 등급이 늘어도 Map에 구현체만 추가한다.

## 더 깊이 가려면

- [전략 (Strategy) — 심화](./strategy-pattern.md) — hook method, Context 결합 방식, 전략 선택 registry 구조까지
- [Strategy vs Function: lambda로 충분한가](./strategy-vs-function-chooser.md) — 언제 lambda로 끝낼지, 언제 Strategy 타입이 필요한지

## 면접/시니어 질문 미리보기

> Q: 전략 패턴과 단순 if-else의 차이가 무엇인가?
> 의도: 패턴의 목적을 이해하는지 확인한다.
> 핵심: if-else는 조건이 늘어날수록 수정이 집중되지만, 전략은 새 구현체 추가로 끝난다.

> Q: Context가 Strategy를 어떻게 받아야 더 좋은가?
> 의도: 생성자 주입 vs 메서드 주입 차이를 아는지 확인한다.
> 핵심: 생성자 주입이면 Context가 일관된 전략을 유지하고, 메서드 주입이면 호출마다 전략을 바꿀 수 있다.

> Q: 전략 구현체가 10개 이상 늘어나면 어떤 문제가 생기는가?
> 의도: 전략 폭발 냄새를 아는지 확인한다.
> 핵심: 클래스 수가 폭증하면 registry나 lambda 맵으로 단순화하는 방향을 고려한다.

## 한 줄 정리

전략 패턴은 "어떻게 할지"를 인터페이스 뒤로 숨겨 Context를 변경 없이 구현체를 교체할 수 있게 만드는 구조다.
