# Strategy vs Policy Selector Naming: `Factory`보다 의도가 잘 보이는 이름들

> 한 줄 요약: `Factory`는 "새로 만든다"가 중심일 때 쓰고, 이미 있는 후보를 고르거나 해석하거나 찾아 실행하는 일은 `Selector`, `Resolver`, `Registry`, `Strategy` 같은 이름이 더 정확하다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [팩토리 패턴 기초](./factory-basics.md)
> - [전략 패턴 기초](./strategy-pattern-basics.md)
> - [Strategy Map vs Registry Primer](./strategy-map-vs-registry-primer.md)
> - [주입된 Handler Map에서 Registry vs Factory: lookup과 creation을 분리하기](./registry-vs-factory-injected-handler-maps.md)
> - [런타임 선택에서 Bridge vs Strategy vs Factory](./bridge-strategy-vs-factory-runtime-selection.md)
> - [Policy Object Pattern: 도메인 결정을 객체로 만든다](./policy-object-pattern.md)
> - [디자인 패턴 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: strategy vs policy selector naming, selector resolver registry strategy vs factory, policy selector vs factory, strategy selector naming, resolver vs factory beginner, registry vs factory naming, factory naming smell, factory when not creating, runtime policy selection not factory, chooses not creates, resolves not creates, lookup not creation, PaymentPolicyFactory smell, PaymentPolicySelector, PaymentStrategyResolver, PaymentHandlerRegistry, beginner naming factory selector resolver registry strategy, factory 이름 오해, factory 보다 selector, factory 보다 resolver, factory 보다 registry, factory 보다 strategy, 정책 선택기 이름, 전략 선택 이름, 생성이 아니면 factory 아님, 선택 조회 해석 실행 이름 구분

---

## 먼저 머릿속 그림

초보자가 `Factory`를 많이 붙이는 이유는 "뭔가 하나를 골라 준다"는 느낌 때문이다.
하지만 설계 이름은 보통 **고른다**보다 **무엇을 책임지는가**를 말해야 한다.

- **Factory**: "지금 새 객체나 조립 결과를 만들어 줄까?"
- **Selector**: "요청을 보고 어떤 후보를 쓸지 골라 줄까?"
- **Resolver**: "애매한 입력을 규칙으로 해석해서 하나로 풀어 줄까?"
- **Registry**: "이미 등록된 후보를 key로 찾아 줄까?"
- **Strategy**: "선택된 방식으로 실제 행동을 수행할까?"

짧게 외우면 이렇다.

**만들면 Factory, 고르면 Selector, 해석하면 Resolver, 찾으면 Registry, 실행 방식이면 Strategy다.**

---

## 30초 이름 선택표

| 클래스가 실제로 하는 일 | 더 잘 보이는 이름 | `Factory`가 흐려지는 이유 |
|---|---|---|
| 요청 값에서 정책 key를 결정한다 | `PaymentPolicySelector` | 새 객체를 만들지 않고 선택 기준을 표현한다 |
| 문자열, URL, 코드값을 도메인 객체나 handler로 해석한다 | `ViewResolver`, `PaymentMethodResolver` | 입력 해석 규칙이 중심이다 |
| `Map<Key, Handler>`에서 이미 있는 bean을 꺼낸다 | `PaymentHandlerRegistry` | 생성이 아니라 lookup이다 |
| 선택된 할인/결제/배송 알고리즘을 실행한다 | `DiscountStrategy`, `ShippingStrategy` | 이름이 행동 방식 자체를 말한다 |
| provider별 client를 credentials, timeout과 함께 조립한다 | `PaymentGatewayFactory` | 이때는 생성과 조립이 중심이라 factory가 맞다 |

이 표에서 중요한 기준은 메서드 이름이 아니라 책임이다.
`get()`이 있어도 전략을 고르는 selector일 수 있고, `create()`가 있어도 실제로는 기존 객체를 반환하기만 한다면 이름을 다시 봐야 한다.

---

## 예시: `PaymentPolicyFactory`가 이상한 경우

아래 코드는 이름은 factory지만 실제로는 이미 준비된 정책 중 하나를 고른다.

```java
public final class PaymentPolicyFactory {
    private final Map<PaymentMethod, PaymentPolicy> policies;

    public PaymentPolicy getPolicy(PaymentMethod method) {
        PaymentPolicy policy = policies.get(method);
        if (policy == null) {
            throw new IllegalArgumentException("unsupported method: " + method);
        }
        return policy;
    }
}
```

이 클래스가 하는 일은 `new PaymentPolicy(...)`가 아니다.

- `PaymentPolicy` 후보들은 이미 준비되어 있다
- key로 맞는 후보를 찾는다
- 호출부는 그 정책을 실행한다

그래서 아래 이름이 더 정확하다.

```java
public final class PaymentPolicySelector {
    private final PaymentPolicyRegistry registry;

    public PaymentPolicy select(PaymentMethod method) {
        return registry.get(method);
    }
}
```

```java
PaymentPolicy policy = policySelector.select(order.getPaymentMethod());
return policy.apply(order);
```

여기서는 역할이 더 잘 보인다.

- `PaymentPolicyRegistry`: key로 이미 있는 정책을 찾는다
- `PaymentPolicySelector`: 요청에서 어떤 정책을 쓸지 고른다
- `PaymentPolicy`: 선택된 정책의 행동을 실행한다

---

## `Resolver`는 언제 더 자연스러운가

`Selector`와 `Resolver`도 자주 섞인다.

- `Selector`는 보통 **후보 중 하나를 고르는 느낌**이 강하다
- `Resolver`는 보통 **입력을 해석해서 의미 있는 결과로 풀어내는 느낌**이 강하다

예를 들어 Spring의 `ViewResolver`는 논리 뷰 이름을 실제 view로 해석한다.

```java
View view = viewResolver.resolveViewName("orders/detail");
```

이름을 `ViewFactory`로 붙이면 "새 view 객체를 복잡하게 만든다"는 기대가 생긴다.
하지만 핵심이 view name 해석 규칙이라면 `Resolver`가 더 선명하다.

도메인 코드에서도 비슷하다.

```java
PaymentMethod method = paymentMethodResolver.resolve(request.getMethodCode());
PaymentPolicy policy = policySelector.select(method);
```

- `methodCode`를 도메인 enum으로 풀어내는 일은 `Resolver`
- 도메인 enum으로 정책 후보를 고르는 일은 `Selector`

둘을 분리하면 "입력 해석"과 "정책 선택"이 한 클래스에 뭉치지 않는다.

---

## 흔한 혼동

- **"런타임에 고르니까 Factory 아닌가요?"**
  - 아니다. 런타임 선택은 selector, resolver, registry에서도 일어난다. factory 여부는 생성 책임으로 본다.
- **"`Map`에서 꺼내니까 Strategy가 아니라 Registry 아닌가요?"**
  - map은 lookup 도구다. 꺼낸 값이 같은 행동 계약을 실행하면 전체 흐름은 strategy selection일 수 있다.
- **"`Resolver`와 `Selector` 중 무엇을 골라야 하나요?"**
  - 입력을 의미 있는 값으로 풀면 resolver, 후보 중 하나를 고르면 selector가 더 자연스럽다.
- **"`Factory` 이름이 틀리면 큰 문제인가요?"**
  - 컴파일은 되지만 읽는 사람이 생성 복잡도를 기대한다. 이름이 기대와 다르면 리뷰와 변경에서 비용이 난다.

---

## 빠른 체크리스트

클래스 이름에 `Factory`를 붙이기 전에 아래 질문을 먼저 한다.

- 요청마다 새 객체를 만들거나 조립하는가
- credentials, 설정, 의존성 연결 같은 생성 복잡도를 숨기는가
- 아니면 이미 준비된 객체를 key로 찾기만 하는가
- 입력을 도메인 의미로 해석하는 규칙이 중심인가
- 선택된 객체가 실제 행동 방식인가

판단은 이렇게 끝낸다.

- `new`, `create`, 조립 책임이 중심이면 `Factory`
- 후보 선택 기준이 중심이면 `Selector`
- 입력 해석 규칙이 중심이면 `Resolver`
- key 기반 저장/조회가 중심이면 `Registry`
- 교체 가능한 행동 방식 자체면 `Strategy`

## 한 줄 정리

`Factory`는 "새로 만들어 준다"는 약속이다. 이미 있는 정책을 **고르고**, 입력을 **해석하고**, key로 **찾고**, 선택된 방식으로 **실행하는** 책임은 각각 `Selector`, `Resolver`, `Registry`, `Strategy`라는 이름이 더 잘 드러낸다.
