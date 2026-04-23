# 런타임 선택에서 Bridge vs Strategy vs Factory: 행동 축과 생성 축을 헷갈리지 않기

> 한 줄 요약: 런타임에 "이번에는 어떤 정책/행동을 쓸까"를 고르는 일은 보통 Strategy이고, Factory는 그 전략이나 협력 객체를 어떻게 만들지를 숨길 때 등장하며, Bridge는 행동 종류와 구현 제공자처럼 두 변화 축이 함께 늘어날 때 쓴다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Strategy vs Policy Selector Naming: `Factory`보다 의도가 잘 보이는 이름들](./strategy-policy-selector-naming.md)
> - [전략 패턴 기초](./strategy-pattern-basics.md)
> - [팩토리 패턴 기초](./factory-basics.md)
> - [Bridge Pattern: 저장소와 제공자를 분리하는 추상화](./bridge-storage-provider-abstractions.md)
> - [Strategy vs State vs Policy Object](./strategy-vs-state-vs-policy-object.md)
> - [주입된 Handler Map에서 Registry vs Factory: lookup과 creation을 분리하기](./registry-vs-factory-injected-handler-maps.md)
> - [Policy Object Pattern: 도메인 결정을 객체로 만든다](./policy-object-pattern.md)
> - [디자인 패턴 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: bridge vs strategy vs factory, runtime selection strategy factory, behavior axis vs creation axis, policy selection not factory, runtime policy chooser, junior factory confusion, strategy selection beginner, strategy vs policy selector naming, selector resolver registry strategy vs factory, factory creates strategy, factory creates gateway client, bridge two change axes, behavior selection vs object creation, strategy vs factory beginner, bridge strategy factory payment example, payment policy selector not factory, runtime behavior selection pattern, provider axis vs policy axis, strategy registry selector, two axis explosion bridge

---

## 이 문서는 언제 읽으면 좋은가

아래 말이 입에서 나오면 이 문서를 먼저 보면 된다.

- "런타임에 골라 쓰니까 이건 factory 아닌가요?"
- "`CardPolicy`, `PointPolicy`를 고르는데 이름을 `PolicyFactory`로 붙여도 되나요?"
- "행동을 바꾸는 문제인지, 객체를 만드는 문제인지 자꾸 섞입니다"
- "결제 방식과 PG provider가 둘 다 늘어나는데 클래스가 폭발합니다"

핵심은 패턴 이름보다 **무엇이 바뀌는가**다.

---

## 먼저 그림으로 자르기

용어보다 아래 세 질문이 더 중요하다.

- **Strategy 질문**: "이번 요청을 어떤 방식으로 처리할까?"
- **Factory 질문**: "지금 어떤 객체를 만들어 줄까?"
- **Bridge 질문**: "서로 다른 두 변화 축을 어떻게 분리할까?"

짧게 외우면 이렇게 정리된다.

- **방법을 고르면 Strategy**
- **생성을 감추면 Factory**
- **두 축을 찢어 놓으면 Bridge**

런타임에 선택이 일어난다는 사실만으로 factory가 되지는 않는다.
핵심은 **선택의 대상이 행동인지, 새 객체 생성인지**다.

---

## 30초 구분표

| 패턴 | 가장 먼저 던질 질문 | 주로 바뀌는 것 | 런타임에 보이는 모습 | 대표 예시 |
|---|---|---|---|---|
| Strategy | 어떻게 처리할까 | 알고리즘, 정책, 행동 | 이미 준비된 구현 중 하나를 골라 실행 | 할인 정책, 결제 수단, 라우팅 규칙 |
| Factory | 무엇을 만들어 줄까 | 생성 로직, 생성 파라미터, 구현 감춤 | `create()`로 새 객체나 조립 결과를 반환 | client/session 생성, 복잡한 객체 조립 |
| Bridge | 두 축이 독립적으로 바뀌는가 | 추상화 축 + 구현 축 | 한 축 객체가 다른 축 인터페이스에 위임 | 알림 종류 x 전송 채널, 결제 흐름 x PG provider |

한 문장으로 다시 말하면:

- Strategy는 **행동 선택**
- Factory는 **객체 생성**
- Bridge는 **축 분리**

---

## 초보자가 가장 많이 헷갈리는 장면

예를 들어 주문 결제에서 결제 수단마다 처리 로직이 다르다고 하자.

```java
public interface PaymentStrategy {
    PaymentResult pay(Order order);
}

public final class CardPaymentStrategy implements PaymentStrategy {
    @Override
    public PaymentResult pay(Order order) {
        // 카드 결제 흐름
    }
}

public final class PointPaymentStrategy implements PaymentStrategy {
    @Override
    public PaymentResult pay(Order order) {
        // 포인트 결제 흐름
    }
}
```

그리고 서비스가 결제 수단으로 구현을 고른다.

```java
public final class PaymentStrategyRegistry {
    private final Map<PaymentMethod, PaymentStrategy> strategies;

    public PaymentStrategyRegistry(Map<PaymentMethod, PaymentStrategy> strategies) {
        this.strategies = strategies;
    }

    public PaymentStrategy get(PaymentMethod method) {
        return strategies.get(method);
    }
}
```

```java
PaymentStrategy strategy = strategyRegistry.get(order.getPaymentMethod());
return strategy.pay(order);
```

여기서 많은 주니어가 `PaymentFactory`라는 이름을 붙인다.
하지만 이 코드는 대개 factory보다 아래 설명이 더 정확하다.

- **Strategy**: 카드냐 포인트냐, 즉 **행동 방식**을 고른다
- **Registry/Selector**: 이미 준비된 전략 객체 중 맞는 것을 **찾는다**
- **Factory 아님**: 요청마다 새 `PaymentStrategy`를 만드는 장면이 없다

즉 "고른다"와 "만든다"를 섞으면 이름이 흐려진다.

---

## 언제 진짜 Factory인가

같은 결제 도메인에서도 아래는 factory라고 부를 만하다.

```java
public final class PaymentGatewayFactory {
    public PaymentGateway create(Tenant tenant, ProviderType providerType) {
        Credentials credentials = loadCredentials(tenant, providerType);
        HttpClient client = new HttpClient(credentials.apiKey());
        return switch (providerType) {
            case TOSS -> new TossPaymentGateway(client);
            case KSNET -> new KsnetPaymentGateway(client);
        };
    }
}
```

여기서는 실제로 생성 책임이 있다.

- 자격 증명을 읽는다
- client를 조립한다
- 어떤 gateway 구현을 `new` 할지 감춘다

즉 **behavior 선택**이 아니라 **creation 복잡도 은닉**이 중심이다.

실무에서는 둘이 같이 나오기도 한다.

1. Factory가 gateway/client를 만든다
2. Strategy가 그 gateway를 사용해 결제 흐름을 실행한다

이때 "factory를 썼다"는 사실이 전략 문제를 factory 문제로 바꾸지는 않는다.
각자 맡는 질문이 다를 뿐이다.

---

## Bridge는 언제 끼어드나

이제 결제 수단뿐 아니라 PG provider도 함께 늘어난다고 하자.

- 결제 수단 축: 카드, 포인트, 쿠폰
- provider 축: Toss, KSNET, Mock

이걸 클래스 이름으로 곱하기 시작하면 금방 이렇게 된다.

- `TossCardPayment`
- `TossPointPayment`
- `KsnetCardPayment`
- `KsnetPointPayment`

이때 보이는 문제는 "무엇을 생성하나"보다 **두 변화 축이 서로 독립적으로 늘어난다**는 점이다.
이 질문은 factory보다 bridge에 가깝다.

```java
public interface PaymentGateway {
    Approval approve(PaymentRequest request);
}

public final class CardPaymentStrategy implements PaymentStrategy {
    private final PaymentGateway gateway;

    public CardPaymentStrategy(PaymentGateway gateway) {
        this.gateway = gateway;
    }

    @Override
    public PaymentResult pay(Order order) {
        Approval approval = gateway.approve(PaymentRequest.from(order));
        return PaymentResult.from(approval);
    }
}
```

이 구조에서는:

- `CardPaymentStrategy`, `PointPaymentStrategy`가 **행동 축**이다
- `TossPaymentGateway`, `KsnetPaymentGateway`가 **구현/provider 축**이다
- 전략이 gateway 인터페이스에 위임하면서 두 축을 독립적으로 바꾼다

즉 **행동 선택은 Strategy**, **두 축 분리는 Bridge**, **필요하면 gateway 생성은 Factory**가 맡는다.
셋은 경쟁 관계라기보다 질문이 다른 도구다.

---

## 이름 붙일 때 바로 쓰는 체크표

| 코드가 실제로 하는 일 | 더 맞는 이름 |
|---|---|
| 이미 만들어진 정책 객체를 `get()`으로 찾는다 | `StrategyRegistry`, `PolicySelector`, `Resolver` |
| 요청마다 새 client/session/gateway를 조립해 돌려준다 | `Factory` |
| 정책 종류와 provider 종류를 독립적으로 늘린다 | `Bridge` 구조를 의식한 `Strategy + Provider` 조합 |
| "정책을 고른다"와 "생성을 숨긴다"를 둘 다 한다 | `Selector + Factory`를 분리할지 먼저 본다 |

특히 아래 이름은 자주 다시 봐야 한다.

- `PolicyFactory`인데 실제로는 `Map`에서 꺼내기만 한다면 factory보다 registry다
- `PaymentFactory`인데 실제로는 `pay()`를 위임하기만 한다면 strategy 쪽 질문이다
- `GatewayFactory`인데 provider별 client 생성과 설정 조립을 숨긴다면 그때는 factory가 맞다

---

## 흔한 오해 5가지

- **"런타임에 선택하니까 factory다"**
  - 아니다. 런타임 선택은 Strategy, Registry, Bridge에서도 모두 일어난다. factory 여부는 `create/new/조립` 책임으로 본다.
- **"전략 구현을 여러 개 두면 다 bridge다"**
  - 아니다. 변화 축이 하나면 그냥 Strategy로 충분하다. Bridge는 독립적인 두 축이 있어야 의미가 있다.
- **"factory가 strategy를 만들면 결국 strategy도 factory다"**
  - 아니다. factory는 strategy를 **만들 수** 있지만, strategy의 핵심 역할은 여전히 **행동 수행**이다.
- **"policy object를 고르면 무조건 factory라고 부를 수 있다"**
  - 아니다. policy를 평가/실행할 객체를 고르는 일은 보통 selector 또는 strategy selection에 더 가깝다.
- **"이름만 factory로 붙여도 큰 문제는 없다"**
  - 리뷰와 유지보수에서 계속 비용이 난다. 사람들은 `Factory`를 보면 생성 복잡도가 숨어 있다고 기대한다.

---

## 아주 짧은 결정 순서

1. 지금 질문이 "무엇을 만들까"면 Factory부터 본다.
2. 질문이 "어떻게 처리할까"면 Strategy부터 본다.
3. "행동 종류"와 "구현 provider"가 함께 늘어나면 Bridge를 본다.
4. 이미 있는 객체를 `Map`에서 찾기만 하면 Registry/Selector라고 부르는 편이 정확하다.

---

## 다음으로 읽으면 좋은 문서

- Strategy 감각을 먼저 굳히려면 [전략 패턴 기초](./strategy-pattern-basics.md)
- 생성 책임과 이름 붙이기를 더 분명히 하려면 [팩토리 패턴 기초](./factory-basics.md)
- 주입된 `Map<..., Handler>`가 왜 factory보다 registry에 가까운지 보려면 [주입된 Handler Map에서 Registry vs Factory](./registry-vs-factory-injected-handler-maps.md)
- 결제 수단 축과 상태/정책 축을 더 세밀하게 나누려면 [Strategy vs State vs Policy Object](./strategy-vs-state-vs-policy-object.md)
- 독립적인 두 축 분리를 더 깊게 보려면 [Bridge Pattern: 저장소와 제공자를 분리하는 추상화](./bridge-storage-provider-abstractions.md)

## 한 줄 정리

"런타임에 고른다"만으로 factory라고 부르지 말고, **행동을 고르면 Strategy, 새 객체를 만들면 Factory, 두 축을 분리하면 Bridge**라고 먼저 자르는 편이 정확하다.
