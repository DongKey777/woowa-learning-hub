# Bean Name vs Domain Key Lookup: Spring handler map을 domain registry로 감싸기

> 한 줄 요약: Spring이 주입한 `Map<String, Handler>`의 key는 보통 bean name이다. 주문 상태, 결제 수단, 이벤트 타입처럼 애플리케이션이 이해하는 key로 분기한다면 bean name map을 그대로 쓰지 말고 domain-key registry로 한 번 감싸자.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../software-engineering/oop-design-basics.md)

> 관련 문서:
> - [주입된 Handler Map에서 Registry vs Factory: lookup과 creation을 분리하기](./registry-vs-factory-injected-handler-maps.md)
> - [Handler Registry Test Shape: `supports()` 기반 registry를 Spring 없이 단위 테스트하기](./handler-registry-test-shape-supports-without-spring.md)
> - [Injected Registry vs Service Locator Checklist: 명시적 주입과 숨은 조회 구분하기](./injected-registry-vs-service-locator-checklist.md)
> - [Strategy Map vs Registry Primer](./strategy-map-vs-registry-primer.md)
> - [Registry Pattern: 객체를 찾는 이름표와 저장소](./registry-pattern.md)
> - [Factory와 DI 컨테이너 Wiring: 프레임워크가 대신하는 생성, 남겨야 하는 생성](./factory-vs-di-container-wiring.md)
> - [Service Locator Antipattern: 숨은 의존성을 만드는 조회 중심 설계](./service-locator-antipattern.md)

retrieval-anchor-keywords: bean name vs domain key lookup, spring bean name handler map, map<string handler> bean name, autowired map bean names, spring injected map domain key registry, domain key registry, handler supports domain key, bean name leak, container naming leak, @component name lookup smell, applicationcontext getbean handler smell, injected registry vs service locator checklist, qualifier vs domain key, beginner channel handler map, 처음 배우는데 채널 분기 큰 그림

---

## 처음 배우는데 먼저 보는 큰 그림

Spring이 `Map<String, PaymentHandler>`를 주입해 주면 처음에는 편해 보인다.

```text
Spring bean name -> handler bean
```

하지만 주문 코드가 실제로 묻는 질문은 보통 이것이다.

```text
PaymentMethod.CARD -> card handler
```

두 key는 비슷해 보여도 역할이 다르다.

- **bean name**: 컨테이너가 bean을 구분하기 위한 기술적 이름
- **domain key**: 결제 수단, 주문 상태, 이벤트 타입처럼 애플리케이션 규칙이 이해하는 이름

짧게 외우면 된다.

**"컨테이너 이름으로 받은 map은 시작 지점에서만 쓰고, 서비스 코드는 domain key로 registry를 조회한다."**

---

## `channel -> bean name` 혼동 1분 교정

처음 배우는데 가장 자주 섞이는 문장은 아래 두 개다.

- `"channel이 SMS니까 smsHandler bean을 찾으면 되죠?"`
- `"그냥 bean 이름을 채널 이름 규칙으로 맞추면 되는 거 아닌가요?"`

여기서 핵심은 "channel은 도메인 입력값"이고 "bean name은 컨테이너 내부 식별자"라는 점이다.

```text
channel(EMAIL/SMS/KAKAO) -> domain key registry lookup -> handler 실행
bean name -> Spring 내부 wiring 식별
```

즉 channel 분기를 언제 쓰는지 질문이 나오면, 답은 bean name 문자열 규칙이 아니라 domain key registry다.

---

## 30초 판단표

| 상황 | 그대로 `Map<String, Handler>`를 써도 되나 | 이유 |
|---|---|---|
| 설정/부트스트랩 코드에서 bean 목록을 읽는다 | 가능 | 컨테이너 wiring을 다루는 코드라 bean name이 자연스럽다 |
| 요청의 `channel` 값(`EMAIL`, `SMS`, `KAKAO`)으로 handler를 고른다 | 감싸야 한다 | channel은 도메인 key다. bean name 문자열 조합 대신 domain-key registry를 조회해야 한다 |
| 서비스가 `order.paymentMethod()`로 handler를 고른다 | 감싸야 한다 | 서비스의 분기 기준은 bean name이 아니라 domain key다 |
| bean 이름을 `cardPaymentHandler`에서 `creditCardPaymentHandler`로 바꿨더니 결제가 깨진다 | 이미 누수다 | 리팩터링 이름 변경이 도메인 동작을 바꾸면 경계가 섞였다 |
| `ApplicationContext.getBean(name)`을 여러 서비스에서 호출한다 | 피한다 | 명시적 주입이 사라지고 service locator smell로 간다 |

핵심 기준은 단순하다.

**요청 데이터나 도메인 값으로 찾는 순간, bean name map을 public 설계로 노출하지 않는다.**

---

## 나쁜 예: domain key를 bean name 규칙에 맞춘다

아래 코드는 Spring이 주입한 bean name map을 결제 분기에 직접 사용한다.

```java
@Service
public class CheckoutService {
    private final Map<String, PaymentHandler> handlers;

    public CheckoutService(Map<String, PaymentHandler> handlers) {
        this.handlers = handlers;
    }

    public void pay(Order order) {
        String beanName = order.paymentMethod().name().toLowerCase() + "PaymentHandler";
        PaymentHandler handler = handlers.get(beanName);
        if (handler == null) {
            throw new IllegalArgumentException("unsupported method: " + order.paymentMethod());
        }
        handler.pay(order);
    }
}
```

겉으로는 map lookup일 뿐이지만, 실제로는 세 가지가 섞였다.

- `PaymentMethod.CARD`라는 도메인 값
- `cardPaymentHandler`라는 Spring bean 이름 규칙
- 결제 서비스의 런타임 분기

그래서 handler 클래스 이름이나 `@Component` 이름을 바꾸는 리팩터링이 결제 동작을 깨뜨릴 수 있다.
초보자가 보기에도 위험 신호는 이것이다.

**"도메인 코드가 문자열 조합으로 bean 이름을 만들고 있다."**

---

## 좋은 예: handler가 자기 domain key를 말하게 한다

서비스가 알아야 하는 것은 bean name이 아니라 "이 handler가 어떤 결제 수단을 지원하는가"다.

```java
public interface PaymentHandler {
    PaymentMethod supports();
    void pay(Order order);
}

@Component
public class CardPaymentHandler implements PaymentHandler {
    @Override
    public PaymentMethod supports() {
        return PaymentMethod.CARD;
    }

    @Override
    public void pay(Order order) {
        // ...
    }
}
```

registry는 Spring이 준비한 handler bean들을 받아 domain key map으로 바꾼다.

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

서비스는 이제 domain key로만 말한다.

```java
@Service
public class CheckoutService {
    private final PaymentHandlerRegistry handlers;

    public CheckoutService(PaymentHandlerRegistry handlers) {
        this.handlers = handlers;
    }

    public void pay(Order order) {
        handlers.get(order.paymentMethod()).pay(order);
    }
}
```

이 구조에서 Spring bean 이름은 바깥으로 새지 않는다.

## 좋은 예: handler가 자기 domain key를 말하게 한다 (계속 2)

- `CardPaymentHandler` bean 이름은 바뀌어도 된다
- 결제 분기 key는 `PaymentMethod.CARD`로 고정된다
- 지원하지 않는 결제 수단은 registry 한 곳에서 실패한다

---

## Spring이 꼭 `Map<String, Handler>`를 준다면

프레임워크 map을 받는 것 자체가 문제는 아니다.
문제는 그 key를 서비스 코드가 도메인 key처럼 쓰는 것이다.

```java
@Component
public class PaymentHandlerRegistry {
    private final Map<PaymentMethod, PaymentHandler> handlers;

    public PaymentHandlerRegistry(Map<String, PaymentHandler> beanHandlers) {
        this.handlers = beanHandlers.values().stream()
            .collect(Collectors.toUnmodifiableMap(
                PaymentHandler::supports,
                handler -> handler
            ));
    }
}
```

여기서 `beanHandlers`의 `String` key는 버린다.
registry를 만드는 bootstrap 입력으로만 쓴다.

도메인 key를 얻는 방법은 보통 셋 중 하나다.

| 방법 | 예 | beginner 기본값 |
|---|---|---|
| handler 메서드 | `handler.supports()` | 가장 단순하고 테스트하기 쉽다 |
| domain annotation | `@HandlesPayment(CARD)` | 프레임워크 반사가 필요할 때만 쓴다 |
| 설정 파일 | `payment.handlers.card=...` | 운영 설정으로 매핑을 바꿔야 할 때만 쓴다 |

입문 단계에서는 먼저 `supports()` 메서드를 추천한다.
도메인 key가 Java 타입으로 보이고, IDE 리팩터링과 테스트가 쉽기 때문이다.
`supports()` 기반 registry를 실제로 어떻게 Spring 없이 단위 테스트할지는 [Handler Registry Test Shape](./handler-registry-test-shape-supports-without-spring.md)에서 이어서 보면 된다.

---

## 흔한 오해

- **"`Map<String, Handler>`를 주입받으면 Spring이 registry를 만들어 준 것 아닌가요?"**
  모양은 registry-like lookup이 맞다. 하지만 key가 bean name이면 아직 domain registry는 아니다.
- **"bean name을 도메인 이름과 똑같이 맞추면 괜찮지 않나요?"**
  작은 예제에서는 된다. 하지만 이름 변경, `@Component("...")`, profile별 bean 교체가 들어오면 도메인 규칙이 컨테이너 naming에 묶인다.
- **"`@Qualifier`도 문자열인데 이것도 전부 나쁜가요?"**
  아니다. wiring을 고정하려는 설정 코드에서는 자연스럽다. 문제는 요청마다 바뀌는 domain key를 `@Qualifier`나 bean name 문자열로 흉내 내는 것이다.
- **"그럼 registry가 factory인가요?"**
  아니다. 위 예시는 이미 만들어진 handler를 찾으므로 registry다. 새 객체를 만드는 책임이 붙으면 [Registry vs Factory](./registry-vs-factory-injected-handler-maps.md)에서 이어서 구분하면 된다.

---

## 코드 리뷰에서 보는 신호

아래가 보이면 domain-key registry로 감싸는 리팩터링을 고려한다.

- service/controller가 bean name 문자열을 조합한다
- `PaymentMethod`, `OrderStatus`, `EventType` 같은 도메인 값과 bean name이 1:1로 맞아야만 동작한다
- handler 이름 변경이 비즈니스 테스트 실패로 이어진다
- 여러 서비스가 같은 `Map<String, Handler>`에서 직접 `get(...)` 한다
- 지원 key 누락 검증이 각 호출부에 흩어져 있다

반대로 괜찮은 경우도 있다.

- `@Configuration`이나 registry 생성자 안에서만 bean name map을 다룬다
- bean name이 로그, 진단, actuator 표시용일 뿐 도메인 분기 key가 아니다
- 서비스는 `PaymentMethod`, `OrderStatus`, `EventType` 같은 domain key만 본다

---

## 다음에 이어서 보면 좋은 문서

- `Map<String, Handler>`가 factory인지 registry인지 헷갈리면 [주입된 Handler Map에서 Registry vs Factory](./registry-vs-factory-injected-handler-maps.md)를 본다.
- 같은 `Map<Key, ...>`라도 strategy collection인지 plain registry인지 헷갈리면 [Strategy Map vs Registry Primer](./strategy-map-vs-registry-primer.md)를 본다.
- registry가 전역 조회소처럼 퍼지기 시작하면 [Service Locator Antipattern](./service-locator-antipattern.md)을 본다.

## 한 줄 정리

Spring이 준 `Map<String, Handler>`의 bean name은 컨테이너 내부 이름이다. 도메인 코드가 결제 수단, 상태, 이벤트 타입으로 handler를 고른다면 시작 시점에 `Map<DomainKey, Handler>` registry로 바꿔서 사용하자.
