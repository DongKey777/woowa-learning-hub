# Injected Registry vs Service Locator Checklist: 명시적 주입과 숨은 조회 구분하기

> 한 줄 요약: 생성자에 좁은 registry가 보이면 의존성이 드러난 설계이고, 메서드 안에서 컨테이너나 전역 조회소를 직접 뒤지면 service locator로 미끄러진 설계다.

**난이도: 🟢 Beginner**

> 관련 문서:
> - [주입된 Handler Map에서 Registry vs Factory: lookup과 creation을 분리하기](./registry-vs-factory-injected-handler-maps.md)
> - [Bean Name vs Domain Key Lookup: Spring handler map을 domain registry로 감싸기](./bean-name-vs-domain-key-lookup.md)
> - [Strategy Registry vs Service Locator Drift Note](./strategy-registry-vs-service-locator-drift.md)
> - [Registry Pattern: 객체를 찾는 이름표와 저장소](./registry-pattern.md)
> - [Service Locator Antipattern: 숨은 의존성을 만드는 조회 중심 설계](./service-locator-antipattern.md)
> - [Factory와 DI 컨테이너 Wiring: 프레임워크가 대신하는 생성, 남겨야 하는 생성](./factory-vs-di-container-wiring.md)

retrieval-anchor-keywords: injected registry vs service locator checklist, explicit constructor injection registry, hidden dependency lookup checklist, service locator drift, strategy registry service locator drift, strategy lookup helper smell, strategy selector service locator smell, handler registry service locator smell, ApplicationContext getBean handler smell, BeanFactory getBean handler registry, narrow typed registry, global lookup smell, registry constructor injection, dependency injection registry checklist, service locator vs dependency injection beginner, service locator hidden dependency, Map<String Object> service locator, registry vs service locator 처음 배우는데, 주입된 registry service locator, 생성자 주입 registry, 숨은 의존성 lookup, handler registry 체크리스트, ApplicationContext getBean smell, 서비스 로케이터 드리프트, 레지스트리 DI 체크리스트

---

## 먼저 머릿속 그림

두 코드는 겉으로 모두 "무언가를 찾아서 쓴다"처럼 보인다.
차이는 **찾는 통로가 설계에 드러나는가**다.

- **Injected registry**: 생성자에 `PaymentHandlerRegistry`처럼 좁은 조회 도구가 보인다.
- **Service locator**: 메서드 안에서 `ApplicationContext`, `BeanFactory`, `ServiceLocator` 같은 넓은 조회소를 직접 부른다.

짧게 외우면 된다.

**"의존성이 생성자에 보이면 DI 쪽, 본문에서 몰래 찾으면 locator 쪽."**

---

## 30초 비교표

| 질문 | Injected registry | Service locator drift |
|---|---|---|
| 의존성이 어디에 보이나 | 생성자와 필드 타입에 보인다 | 메서드 본문 조회 코드에 숨어 있다 |
| 조회 범위가 얼마나 넓나 | `PaymentHandler` 같은 한 종류로 좁다 | 컨테이너 안의 거의 모든 bean으로 넓다 |
| key가 무엇인가 | `PaymentMethod`, `OrderStatus` 같은 domain key | bean name 문자열, class 이름, 임의 문자열 |
| 테스트는 어떻게 하나 | fake registry나 fake handler를 생성자에 넣는다 | 전역 registry나 Spring context를 준비해야 한다 |
| 실패는 언제 드러나나 | registry 생성/검증 시점에 빠르게 드러난다 | 특정 요청 경로에서 늦게 터지기 쉽다 |

---

## 체크리스트: 아직 injected registry다

아래 항목이 대부분 맞으면 service locator가 아니라 명시적 주입을 잘 유지하고 있는 쪽이다.

- 클래스 생성자에 `PaymentHandlerRegistry`, `Map<PaymentMethod, PaymentHandler>`, `List<PaymentHandler>`처럼 필요한 후보가 보인다.
- registry가 다루는 값이 한 역할로 좁다. 예를 들어 결제 handler registry는 결제 handler만 안다.
- 서비스 코드는 `registry.get(order.paymentMethod())`처럼 domain key로 묻는다.
- registry는 시작 시점에 만들어지고, 요청 처리 중에는 읽기 전용에 가깝다.
- 누락 key, 중복 key 검증이 registry 한 곳에 모여 있다.
- 단위 테스트에서 Spring context 없이 fake registry나 fake handler를 넣을 수 있다.
- handler를 하나 추가해도 기존 서비스가 컨테이너 이름이나 class 이름을 새로 알 필요가 없다.

---

## 체크리스트: service locator로 미끄러지는 중이다

아래 신호가 보이면 registry라는 이름을 달고 있어도 숨은 의존성 lookup이 되었는지 의심한다.

- 서비스 메서드 안에서 `ApplicationContext.getBean(...)`, `BeanFactory.getBean(...)`, `ServiceLocator.get(...)`을 직접 호출한다.
- 생성자에는 실제 필요한 handler가 보이지 않고, 넓은 `Context`, `Container`, `Registry`, `Map<String, Object>`만 보인다.
- 요청 값으로 bean name 문자열을 조합한다. 예: `"cardPaymentHandler"`.
- 여러 서비스가 같은 전역 registry에서 각자 필요한 객체를 꺼낸다.
- registry가 `get(Class<T>)`, `get(String)`, `getAnything(...)`처럼 모든 의존성 조회를 받아 준다.
- 테스트가 static/global registry를 먼저 등록하거나 지워야만 통과한다.
- bean 이름 변경, `@Component` 이름 변경, package 이동 같은 리팩터링이 비즈니스 분기를 깨뜨린다.

초보자용 빠른 판단은 이것이다.

**"이 클래스가 무엇을 필요로 하는지 생성자만 보고 말할 수 없으면 locator smell이다."**

---

## 좋은 예: 좁은 registry를 생성자로 받는다

```java
@Service
public class CheckoutService {
    private final PaymentHandlerRegistry handlers;

    public CheckoutService(PaymentHandlerRegistry handlers) {
        this.handlers = handlers;
    }

    public void pay(Order order) {
        PaymentHandler handler = handlers.get(order.paymentMethod());
        handler.pay(order);
    }
}
```

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

이 코드는 lookup을 한다.
하지만 service locator는 아니다.

- `CheckoutService`가 필요한 협력자가 생성자에 보인다.
- registry는 `PaymentHandler`만 다루는 좁은 타입이다.
- key는 bean name이 아니라 `PaymentMethod`다.
- 테스트는 `PaymentHandlerRegistry`나 `PaymentHandler` fake로 시작할 수 있다.

---

## 나쁜 예: 컨테이너를 런타임 조회소로 쓴다

```java
@Service
public class CheckoutService {
    private final ApplicationContext context;

    public CheckoutService(ApplicationContext context) {
        this.context = context;
    }

    public void pay(Order order) {
        String beanName = order.paymentMethod().name().toLowerCase() + "PaymentHandler";
        PaymentHandler handler = context.getBean(beanName, PaymentHandler.class);
        handler.pay(order);
    }
}
```

이 코드는 처음에는 유연해 보이지만, 의존성을 숨긴다.

- `CheckoutService` 생성자만 보면 어떤 handler가 필요한지 알기 어렵다.
- 결제 수단과 Spring bean name 규칙이 묶인다.
- 단위 테스트가 Spring context나 mock context에 의존한다.
- handler 이름 변경이 런타임 결제 오류로 이어질 수 있다.

이런 경우는 [Bean Name vs Domain Key Lookup](./bean-name-vs-domain-key-lookup.md)처럼 시작 시점에 domain-key registry로 감싸는 편이 낫다.

---

## 애매한 경우 정리

| 코드 모양 | 판단 |
|---|---|
| registry 생성자에서만 `Map<String, Handler>`를 받고 values를 domain-key map으로 바꾼다 | 괜찮다. Spring bean name map을 bootstrap 입력으로만 쓴다 |
| 서비스가 `Map<PaymentMethod, PaymentHandler>`를 직접 생성자로 받는다 | 작은 코드에서는 괜찮다. 검증/오류 처리가 늘면 registry 클래스로 감싼다 |
| 서비스가 `ApplicationContext`를 받아 요청마다 `getBean`한다 | service locator smell이다 |
| plugin loader가 plugin registry를 주입받아 plugin id로 찾는다 | registry일 수 있다. 단, 범위를 plugin으로 좁히고 전역 의존성 조회로 키우지 않는다 |
| factory가 내부에서 creator registry를 쓴다 | 괜찮다. 바깥 public 책임이 `create(...)`라면 factory + 내부 registry다 |

---

## 코드 리뷰에서 바로 묻는 질문

1. 이 클래스가 필요한 협력자를 생성자만 보고 말할 수 있는가?
2. registry가 한 종류의 handler/strategy만 다루는가?
3. key가 domain value인가, 컨테이너 bean name인가?
4. 테스트가 Spring context 없이 fake를 넣고 시작할 수 있는가?
5. `getBean`, static locator, `Map<String, Object>`가 요청 처리 경로에 있는가?

다섯 질문 중 1, 4가 "아니오"이고 5가 "예"라면 service locator drift를 먼저 의심한다.

## 한 줄 정리

Registry lookup 자체가 나쁜 것은 아니다. 문제는 lookup 대상과 경로가 넓어져서 **생성자 주입으로 보여야 할 의존성이 메서드 안의 숨은 조회로 사라지는 순간**이다.
