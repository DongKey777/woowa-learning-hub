# Handler Registry Test Shape: `supports()` 기반 registry를 Spring 없이 단위 테스트하기

> 한 줄 요약: `supports()` 기반 handler registry 테스트의 핵심은 "Spring이 handler 목록을 모아 주는 일"과 "registry가 그 목록을 domain key로 검증/조회하는 일"을 분리해서 보는 것이다. registry 쪽은 보통 생성자 호출만으로 충분히 단위 테스트할 수 있다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../software-engineering/oop-design-basics.md)

> 관련 문서:
> - [주입된 Handler Map에서 Registry vs Factory: lookup과 creation을 분리하기](./registry-vs-factory-injected-handler-maps.md)
> - [Bean Name vs Domain Key Lookup: Spring handler map을 domain registry로 감싸기](./bean-name-vs-domain-key-lookup.md)
> - [Injected Registry vs Service Locator Checklist: 명시적 주입과 숨은 조회 구분하기](./injected-registry-vs-service-locator-checklist.md)
> - [Service Locator Antipattern: 숨은 의존성을 만드는 조회 중심 설계](./service-locator-antipattern.md)
> - [Factory와 DI 컨테이너 Wiring: 프레임워크가 대신하는 생성, 남겨야 하는 생성](./factory-vs-di-container-wiring.md)
> - [Registry Pattern: 객체를 찾는 이름표와 저장소](./registry-pattern.md)
> - [Strategy Map vs Registry Primer](./strategy-map-vs-registry-primer.md)

retrieval-anchor-keywords: handler registry test shape, supports registry test, supports based registry test, handler registry unit test without spring, spring handler registry unit test, no spring container registry test, no application context registry test, supports() registry test, supports method registry, registry bootstrap test, duplicate supports key test, missing handler key test, fail fast registry bootstrap test, handler registry test shape supports without spring basics, handler registry test shape supports without spring beginner

---

## 이 문서는 언제 읽으면 좋은가

- `List<Handler>`를 Spring이 주입하는 구조인데, 테스트도 꼭 `@SpringBootTest`로 해야 하는지 헷갈릴 때
- registry가 `supports()`로 key를 모으는데 duplicate/missing 검증을 어디서 테스트해야 할지 막막할 때
- "bean wiring 테스트"와 "registry 규칙 테스트"를 한 파일에서 섞다가 테스트가 무거워질 때

---

## 먼저 머릿속 그림

`supports()` 기반 registry는 보통 두 단계로 나뉜다.

1. Spring이 handler bean 목록을 모은다
2. registry가 그 목록을 domain key map으로 바꾸고 검증한다

테스트도 같은 둘로 자르면 쉽다.

| 확인하려는 것 | 테스트 질문 | Spring 컨테이너 필요? |
|---|---|---|
| `supports()` key가 겹치면 빨리 실패하는가 | duplicate bootstrap 검증 | 보통 불필요 |
| 필수 key가 빠지면 빨리 실패하는가 | missing bootstrap 검증 | 보통 불필요 |
| `get(CARD)`가 올바른 handler를 돌려주는가 | lookup 검증 | 보통 불필요 |
| `@Component`, profile, conditional bean wiring이 맞는가 | 컨테이너 wiring 검증 | 필요할 수 있음 |

짧게 외우면 된다.

**"registry 테스트의 기본값은 생성자 단위 테스트, Spring 테스트는 wiring 확인이 진짜 목적일 때만."**

---

## 왜 Spring 없이도 테스트가 되나

registry가 실제로 받는 것은 대개 이것이다.

```java
public PaymentHandlerRegistry(List<PaymentHandler> handlers) { ... }
```

운영 환경에서는 Spring이 `List<PaymentHandler>`를 만들어 준다.
하지만 테스트에서는 그 목록을 우리가 직접 만들 수 있다.

즉 registry의 관점에서는

- "이 목록이 어디서 왔는가"보다
- "이 목록 안의 handler들이 어떤 `supports()` 값을 말하는가"

가 더 중요하다.

그래서 registry 테스트에서는 Spring container보다 **작은 fake handler 목록**이 더 직접적인 입력이 된다.

---

## 가장 작은 테스트 모양

먼저 registry가 정말 검사하는 것이 무엇인지 코드로 작게 본다.

```java
public interface PaymentHandler {
    PaymentMethod supports();
    void handle(Order order);
}

public final class PaymentHandlerRegistry {
    private final Map<PaymentMethod, PaymentHandler> handlers;

    public PaymentHandlerRegistry(List<PaymentHandler> handlers) {
        Map<PaymentMethod, PaymentHandler> indexed = new EnumMap<>(PaymentMethod.class);

        for (PaymentHandler handler : handlers) {
            PaymentMethod key = handler.supports();
            PaymentHandler previous = indexed.putIfAbsent(key, handler);
            if (previous != null) {
                throw new IllegalStateException("duplicate handler: " + key);
            }
        }

        EnumSet<PaymentMethod> missing = EnumSet.allOf(PaymentMethod.class);
        missing.removeAll(indexed.keySet());
        if (!missing.isEmpty()) {
            throw new IllegalStateException("missing handlers: " + missing);
        }

        this.handlers = Map.copyOf(indexed);
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

이 클래스가 직접 하는 일은 셋뿐이다.

- `supports()`를 읽어 key를 만든다
- duplicate/missing을 검증한다
- `get(key)`로 handler를 돌려준다

셋 다 생성자 호출과 일반 메서드 호출만 있으면 확인된다.

---

## fake handler로 테스트를 시작한다

입문자에게는 mock보다 작은 fake/stub가 더 읽기 쉽다.

```java
final class StubPaymentHandler implements PaymentHandler {
    private final PaymentMethod method;

    StubPaymentHandler(PaymentMethod method) {
        this.method = method;
    }

    @Override
    public PaymentMethod supports() {
        return method;
    }

    @Override
    public void handle(Order order) {
    }
}
```

이제 테스트 입력은 아주 단순해진다.

```java
List<PaymentHandler> handlers = List.of(
    new StubPaymentHandler(PaymentMethod.CARD),
    new StubPaymentHandler(PaymentMethod.POINT)
);
```

중요한 점은 fake가 "결제를 잘 처리하는가"를 증명할 필요가 없다는 것이다.
여기서는 오직 **registry가 `supports()`를 어떻게 읽는가**만 보면 된다.

---

## 어떤 테스트 입력을 고르면 되나

registry 질문에 따라 입력도 다르게 고르면 된다.

| 입력 | 여기서 확인하는 질문 | beginner 기본값 |
|---|---|---|
| 작은 fake/stub handler 객체 | `supports()` key 매핑과 duplicate/missing 검증 | 가장 추천 |
| mock handler | 특정 호출 여부나 예외 전파까지 같이 보고 싶을 때 | 필요할 때만 |
| Spring container로 띄운 bean 그래프 | profile, conditional, component scan wiring | registry 규칙 테스트에는 보통 과하다 |

처음에는 이렇게 잡으면 된다.

- `supports()` 반환값만 중요하면 fake/stub로 시작한다
- interaction verification이 정말 필요할 때만 mock으로 올린다
- bean wiring이 질문일 때만 Spring 테스트를 쓴다

---

## 복사해서 시작하는 테스트 틀

테스트 본문에서 보고 싶은 것은 "어떤 key 조합으로 registry를 만들었는가"다.
그래서 helper를 하나 두고 테스트를 짧게 유지하면 읽기가 쉬워진다.

```java
class PaymentHandlerRegistryTest {

    @Test
    void duplicate_supports_key_fails_fast() {
        assertThrows(
            IllegalStateException.class,
            () -> new PaymentHandlerRegistry(handlers(
                PaymentMethod.CARD,
                PaymentMethod.CARD,
                PaymentMethod.POINT
            ))
        );
    }

    @Test
    void missing_required_key_fails_fast() {
        assertThrows(
            IllegalStateException.class,
            () -> new PaymentHandlerRegistry(handlers(PaymentMethod.CARD))
        );
    }

    @Test
    void returns_registered_handler_for_domain_key() {
        PaymentHandler card = new StubPaymentHandler(PaymentMethod.CARD);
        PaymentHandler point = new StubPaymentHandler(PaymentMethod.POINT);

        PaymentHandlerRegistry registry =
            new PaymentHandlerRegistry(List.of(card, point));

        assertSame(card, registry.get(PaymentMethod.CARD));
        assertSame(point, registry.get(PaymentMethod.POINT));
    }

    private static List<PaymentHandler> handlers(PaymentMethod... methods) {
        return Arrays.stream(methods)
            .map(StubPaymentHandler::new)
            .toList();
    }
}
```

이 틀의 장점은 테스트 본문이 "지원 key 출석부"처럼 읽힌다는 점이다.
입문자는 helper까지 포함한 이 shape를 먼저 고정해 두면 `@SpringBootTest` 없이도 registry 테스트를 빠르게 늘릴 수 있다.

---

## 먼저 써야 하는 3가지 테스트

### 1. duplicate key fail-fast

```java
@Test
void duplicate_supports_key_fails_fast() {
    IllegalStateException error = assertThrows(
        IllegalStateException.class,
        () -> new PaymentHandlerRegistry(List.of(
            new StubPaymentHandler(PaymentMethod.CARD),
            new StubPaymentHandler(PaymentMethod.CARD),
            new StubPaymentHandler(PaymentMethod.POINT)
        ))
    );

    assertTrue(error.getMessage().contains("duplicate handler"));
}
```

이 테스트가 답하는 질문은 "첫 요청 전부터 registry 등록표가 깨졌다는 사실을 알 수 있는가"다.

### 2. missing key fail-fast

```java
@Test
void missing_required_key_fails_fast() {
    IllegalStateException error = assertThrows(
        IllegalStateException.class,
        () -> new PaymentHandlerRegistry(List.of(
            new StubPaymentHandler(PaymentMethod.CARD)
        ))
    );

    assertTrue(error.getMessage().contains("missing handlers"));
}
```

이 테스트는 닫힌 enum 집합일 때 특히 중요하다.
나중 요청에서 늦게 터질 오류를 startup shape에서 바로 잡아낸다.

### 3. lookup returns the registered handler

```java
@Test
void returns_registered_handler_for_domain_key() {
    PaymentHandler card = new StubPaymentHandler(PaymentMethod.CARD);
    PaymentHandler point = new StubPaymentHandler(PaymentMethod.POINT);

    PaymentHandlerRegistry registry = new PaymentHandlerRegistry(List.of(card, point));

    assertSame(card, registry.get(PaymentMethod.CARD));
    assertSame(point, registry.get(PaymentMethod.POINT));
}
```

이 테스트는 registry의 public 약속을 가장 직접적으로 보여 준다.

## 먼저 써야 하는 3가지 테스트 (계속 2)

- domain key로 찾는다
- 같은 handler 인스턴스를 돌려준다
- Spring bean name이나 `ApplicationContext`는 보이지 않는다

---

## Spring 테스트와 역할을 섞지 말자

같은 registry라도 테스트 책임은 두 층으로 나뉜다.

| 테스트 종류 | 주로 확인하는 것 | 무게 |
|---|---|---|
| plain unit test | `supports()` key 매핑, duplicate/missing, `get()` 동작 | 가볍다 |
| Spring integration test | component scan, conditional bean, profile, qualifier wiring | 무겁다 |

초보자가 자주 꼬이는 지점은 plain unit test에서 확인할 일을 전부 `@SpringBootTest`로 가져가는 것이다.
그러면 실패 원인이 흐려진다.

- registry 규칙이 틀린 건지
- component scan이 빠진 건지
- test configuration이 잘못된 건지

한 번에 섞여 버린다.

그래서 beginner 기본값은 다음처럼 두면 된다.

1. registry 규칙은 plain unit test로 먼저 고정한다
2. 정말 필요한 wiring만 얇은 Spring 테스트로 따로 둔다

---

## 작은 비교: fake registry 단위 테스트 vs Spring context locator 테스트

둘 다 "결제 수단에 맞는 handler를 고른다"는 시나리오를 다룬다.
하지만 무엇을 질문하는지는 꽤 다르다.

| 비교 기준 | fake registry 단위 테스트 | Spring context locator 테스트 |
|---|---|---|
| 서비스가 의존하는 것 | 좁은 registry/lookup 포트 | `ApplicationContext`, bean name 규칙 |
| 테스트 입력 | domain key와 fake registry | Spring context, bean 등록, mock bean |
| 실패가 말해 주는 것 | lookup 계약이나 분기 규칙이 틀렸다 | wiring, bean 이름, context 구성, lookup 규칙이 섞여 있다 |
| 속도와 읽기 난이도 | 가볍고 읽기 쉽다 | 상대적으로 무겁고 원인 분리가 어렵다 |
| beginner 기본값 | 먼저 여기서 시작 | wiring 질문이 진짜일 때만 |

짧게 외우면 된다.

**"registry seam이 보이면 fake로 자르고, `ApplicationContext.getBean(...)`이 보이면 locator smell도 함께 의심한다."**

### 1. fake registry 단위 테스트 모양

서비스 테스트로 올라가면 registry consumer 쪽은 작은 fake registry로도 충분히 읽을 수 있다.
아래는 registry를 좁은 lookup 포트로 받는다는 가정의 가장 작은 예시다.

## 작은 비교: fake registry 단위 테스트 vs Spring context locator 테스트 (계속 2)

```java
interface PaymentHandlerLookup {
    PaymentHandler get(PaymentMethod method);
}

final class FakePaymentHandlerRegistry implements PaymentHandlerLookup {
    private final Map<PaymentMethod, PaymentHandler> handlers = new EnumMap<>(PaymentMethod.class);

    FakePaymentHandlerRegistry register(PaymentMethod method, PaymentHandler handler) {
        handlers.put(method, handler);
        return this;
    }

    @Override
    public PaymentHandler get(PaymentMethod method) {
        PaymentHandler handler = handlers.get(method);
        if (handler == null) {
            throw new IllegalArgumentException("unsupported method: " + method);
        }
        return handler;
    }
}

@Test
void checkout_service_uses_card_handler_from_fake_registry() {
    RecordingPaymentHandler card = new RecordingPaymentHandler(PaymentMethod.CARD);
    PaymentHandlerLookup lookup = new FakePaymentHandlerRegistry()
        .register(PaymentMethod.CARD, card);

    CheckoutService service = new CheckoutService(lookup);

    service.pay(new Order(PaymentMethod.CARD));

    assertTrue(card.wasCalled());
}
```

여기서 `RecordingPaymentHandler`는 `handle()` 호출 여부만 기록하는 작은 fake/spy면 충분하다.

이 테스트가 묻는 질문은 좁다.

- 서비스가 domain key로 registry를 올바르게 조회하는가
- 선택된 handler가 실제로 호출되는가
- Spring bean 이름이나 context 부팅이 없어도 흐름을 설명할 수 있는가

### 2. Spring context locator 테스트 모양

반대로 서비스가 직접 `ApplicationContext.getBean(...)`을 쓰면 테스트 shape도 달라진다.

## 작은 비교: fake registry 단위 테스트 vs Spring context locator 테스트 (계속 3)

```java
@SpringBootTest
class CheckoutServiceLocatorTest {

    @Autowired
    CheckoutService service;

    @MockBean(name = "cardPaymentHandler")
    PaymentHandler cardHandler;

    @Test
    void pays_with_card_handler_through_context_lookup() {
        service.pay(new Order(PaymentMethod.CARD));

        verify(cardHandler).handle(any(Order.class));
    }
}
```

이 예시는 서비스 내부가 `ApplicationContext.getBean(...)`으로 handler를 찾는다고 가정한다.

이 테스트는 유용할 수 있다.
하지만 동시에 너무 많은 질문을 안고 들어온다.

- bean name 조합 규칙이 맞는가
- Spring context가 그 bean을 실제로 올렸는가
- test configuration과 `@MockBean` 치환이 맞는가
- 서비스의 domain 분기가 맞는가

즉 이 테스트가 실패하면 "registry lookup 규칙이 틀린 것"인지 "Spring wiring이 틀린 것"인지 바로 잘리지 않는다.
그래서 beginner 기준에서는 이 모양을 registry test의 기본값으로 두지 않는 편이 낫다.

이 지점이 더 궁금하면 [Injected Registry vs Service Locator Checklist](./injected-registry-vs-service-locator-checklist.md)와 [Service Locator Antipattern](./service-locator-antipattern.md)을 같이 보면 이어진다.

---

## 언제 Spring 컨테이너 테스트가 필요한가

아예 안 쓰라는 뜻은 아니다.
아래 질문이 진짜라면 Spring 테스트가 맞다.

- `@Profile`, `@ConditionalOnProperty` 때문에 특정 handler가 빠지지 않는지 확인해야 한다
- `@Qualifier`나 bean overriding 때문에 실제 운영 wiring이 달라질 수 있다
- component scan 범위나 auto-configuration 연결이 registry 입력을 바꾼다

즉 **registry 자체의 규칙**이 아니라 **운영 wiring의 결과**가 질문일 때만 Spring container가 필요하다.

---

## 이 문서에서 일부러 안 보는 것

아래 항목은 중요하지만, registry primer의 첫 파동에서는 분리해서 보는 편이 좋다.

- 각 handler의 비즈니스 로직이 맞는가
- `@Component`, `@Qualifier`, `@Profile` 조합이 실제 운영 bean graph를 제대로 만드는가
- AOP proxy, 트랜잭션, 보안 어노테이션처럼 handler 바깥 래핑이 붙는가

이 셋을 registry 테스트와 섞으면 "key 등록표가 깨진 것"과 "Spring wiring이 깨진 것"을 구분하기 어려워진다.
그래서 이 문서의 기본 스코프는 끝까지 좁다.

- registry는 constructor + `get()` 단위 테스트로 본다
- handler 동작은 각 handler 테스트로 본다
- wiring은 정말 필요한 얇은 Spring 테스트로 따로 본다

---

## 흔한 오해

- **"운영에서 Spring이 `List<Handler>`를 넣어 주니까 테스트도 Spring이 필요하지 않나요?"**
  아니다. registry는 `List<Handler>`만 받으면 되므로 테스트에서는 그 목록을 직접 만들면 된다.
- **"mock으로 `supports()`를 stub하면 충분하지 않나요?"**
  가능은 하다. 하지만 입문 단계에서는 작은 fake handler가 더 읽기 쉽고, registry의 입력 모양도 더 잘 드러낸다.
- **"lookup 테스트보다 handler 동작 테스트가 더 중요하지 않나요?"**
  handler 동작 테스트도 필요하다. 다만 그것은 각 handler 단위 테스트의 책임이고, registry 테스트는 key 매핑과 bootstrap 검증의 책임이다.
- **"`@SpringBootTest` 하나로 다 검증하면 더 안전하지 않나요?"**
  넓게 보면 그렇지 않다. 실패 원인이 뭉쳐서 registry 규칙 버그를 찾기 어려워진다. 기본 규칙은 작은 단위 테스트로 먼저 고정하는 편이 안전하다.

---

## 한 줄 정리

`supports()` 기반 handler registry 테스트의 기본 모양은 **fake handler 목록을 직접 만들고, 생성자에서 bootstrap 검증과 `get()` lookup을 확인하는 단위 테스트**다. Spring container 테스트는 그 위의 wiring 결과를 확인할 때만 별도로 둔다.
