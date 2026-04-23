# 주입된 Handler Map에서 Registry vs Factory: lookup과 creation을 분리하기

> 한 줄 요약: 프레임워크가 `List<Handler>`나 `Map<Key, Handler>`를 주입해 줬다면 대개 네 손에 들어온 것은 factory가 아니라 registry다. factory는 그 lookup 뒤에 "새로 만든다"가 붙을 때 등장한다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [Factory와 DI 컨테이너 Wiring: 프레임워크가 대신하는 생성, 남겨야 하는 생성](./factory-vs-di-container-wiring.md)
> - [Registry Pattern: 객체를 찾는 이름표와 저장소](./registry-pattern.md)
> - [팩토리 패턴 기초](./factory-basics.md)
> - [Factory Switch Registry Smell](./factory-switch-registry-smell.md)
> - [Service Locator Antipattern: 숨은 의존성을 만드는 조회 중심 설계](./service-locator-antipattern.md)

retrieval-anchor-keywords: registry vs factory injected handler map, spring handler map injection, list of handlers registry, bean collection injection registry, bean map injection factory, payment handler map not factory, registry lookup vs factory creation, injected handlers beginner, strategy map vs factory, service locator vs injected registry

---

## 핵심 개념

먼저 용어보다 그림으로 자르면 쉽다.

- 프레임워크가 `Handler`들을 미리 모아 준다
- 네 코드는 그중 맞는 하나를 **찾아 쓴다**
- 정말 새 객체가 필요하면, 찾은 creator/factory에게 **만들어 달라고 한다**

즉 질문은 두 개다.

- **Registry 질문**: "이미 있는 것 중 어떤 걸 꺼낼까?"
- **Factory 질문**: "지금 새로 무엇을 만들까?"

프레임워크가 컬렉션을 주입했다고 해서 자동으로 factory가 되는 것은 아니다.
그건 보통 **준비된 후보들을 모아 둔 registry**에 더 가깝다.

---

## 30초 구분표

| 코드 모양 | 보통 뭐라고 부르나 | 이유 |
|---|---|---|
| `Map<PaymentMethod, PaymentHandler>`에서 꺼내 바로 `handle()` 호출 | Registry | 이미 만들어진 handler를 lookup한다 |
| `List<PaymentHandler>`를 받아 시작 시점에 map으로 묶음 | DI + Registry bootstrap | 컨테이너가 wiring했고, 코드는 lookup table만 만든다 |
| `Map<PaymentMethod, PaymentSessionCreator>`를 찾은 뒤 `create(order)` 호출 | Factory + 내부 Registry | creator를 lookup한 다음 새 객체를 만든다 |
| `ApplicationContext.getBean(name)`을 서비스 여기저기서 호출 | Service Locator smell | 명시적 주입 대신 전역 조회로 흘러간다 |

짧게 외우면 이렇다.

**"기존 bean을 꺼내 쓰면 registry, 새 객체를 만들면 factory."**

---

## 예시 1: injected handler map은 대개 registry다

아래 코드는 Spring이 여러 `PaymentHandler` bean을 모아 주고, 애플리케이션이 그중 하나를 찾는 구조다.

```java
@Component
public class PaymentHandlerRegistry {
    private final Map<PaymentMethod, PaymentHandler> handlers;

    public PaymentHandlerRegistry(List<PaymentHandler> handlers) {
        this.handlers = handlers.stream()
            .collect(Collectors.toUnmodifiableMap(
                PaymentHandler::supports,
                handler -> handler
            ));
    }

    public PaymentHandler get(PaymentMethod method) {
        PaymentHandler handler = handlers.get(method);
        if (handler == null) {
            throw new IllegalArgumentException("unsupported method: " + method);
        }
        return handler;
    }
}
```

```java
PaymentHandler handler = registry.get(order.getPaymentMethod());
handler.handle(order);
```

여기서 일어난 일은 둘뿐이다.

- 컨테이너가 handler bean들을 준비했다
- `registry.get(...)`가 그중 하나를 골랐다

`new`가 없다. 새 객체도 안 만든다.
그래서 핵심 책임은 **creation이 아니라 lookup**이다.

---

## 예시 2: factory는 lookup 뒤에 creation이 붙는다

이번에는 map 안에 handler 자체가 아니라 "만드는 역할"이 들어 있다고 하자.

```java
public interface PaymentSessionCreator {
    PaymentMethod supports();
    PaymentSession create(Order order);
}

@Component
public class PaymentSessionFactory {
    private final Map<PaymentMethod, PaymentSessionCreator> creators;

    public PaymentSessionFactory(List<PaymentSessionCreator> creators) {
        this.creators = creators.stream()
            .collect(Collectors.toUnmodifiableMap(
                PaymentSessionCreator::supports,
                creator -> creator
            ));
    }

    public PaymentSession create(Order order) {
        PaymentSessionCreator creator = creators.get(order.getPaymentMethod());
        if (creator == null) {
            throw new IllegalArgumentException("unsupported method: " + order.getPaymentMethod());
        }
        return creator.create(order);
    }
}
```

여기서는 안쪽에 registry 성격이 있다.
하지만 바깥에서 보는 public 책임은 `create(...)`다.

- `creators` map: 어떤 creator를 쓸지 **lookup**
- `creator.create(order)`: 실제 **creation**

즉 **factory가 내부에서 registry를 사용할 수는 있지만, lookup만 하는 클래스와는 역할이 다르다.**

---

## 이름 붙일 때 자주 헷갈리는 지점

| 클래스가 실제로 하는 일 | 더 맞는 이름 |
|---|---|
| `get(key)`, `find(key)`, `resolve(key)`로 기존 handler 반환 | `Registry`, `Resolver`, `Router` |
| `create(...)`, `newSession(...)`으로 새 객체 반환 | `Factory` |
| `Map<Key, Handler>`를 받아 분기만 함 | 보통 `Registry` |
| `Map<Key, Creator>`를 받아 생성까지 마침 | 보통 `Factory` |

입문자가 많이 만드는 이름 충돌은 이것이다.

- 클래스 이름은 `PaymentHandlerFactory`
- 실제 구현은 `handlers.get(method)`만 함

이 경우는 factory보다 registry라고 부르는 편이 구조를 더 잘 설명한다.

---

## 흔한 오해 4가지

- **"Spring이 map을 주입했으니 factory를 대신해 준 거 아닌가요?"**
  - 아니다. Spring은 주로 bean **wiring**을 대신한다. 런타임 lookup과 생성 책임은 아직 네 코드에 남아 있다.
- **"handler를 고르는 것도 create의 일부 아닌가요?"**
  - 선택은 관련 있지만, 선택만 하고 기존 객체를 돌려주면 registry 쪽에 더 가깝다.
- **"주입된 map을 쓰면 바로 service locator인가요?"**
  - 아니다. 좁은 타입의 map을 생성자로 명시적으로 주입받는 것은 registry로 쓸 수 있다. 문제는 `ApplicationContext`나 전역 map에서 아무 타입이나 꺼내 쓰기 시작할 때다.
- **"그럼 factory와 registry 중 하나만 써야 하나요?"**
  - 아니다. factory가 내부에서 registry를 써도 된다. 중요한 것은 lookup과 creation을 머릿속에서 섞지 않는 것이다.

---

## 언제 이 문서를 바로 떠올리면 좋은가

- `List<Handler>`를 받아 `Map`으로 바꿨는데 이름을 `*Factory`로 붙이려는 순간
- 코드 리뷰에서 "이건 factory보다 registry 같아요"라는 말을 들었을 때
- Spring이 handler collection을 주입해 주는 구조에서 lookup 책임과 생성 책임이 섞일 때
- injected map을 쓰다가 [Service Locator Antipattern](./service-locator-antipattern.md)으로 미끄러지는지 걱정될 때

## 한 줄 정리

프레임워크가 모아 준 handler map은 보통 **registry**이고, 그 map에서 고른 creator로 새 객체를 만들 때 비로소 **factory**가 된다.
