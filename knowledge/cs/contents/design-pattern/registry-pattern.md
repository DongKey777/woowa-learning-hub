# Registry Pattern: 객체를 찾는 이름표와 저장소

> 한 줄 요약: Registry 패턴은 생성된 객체나 핸들러를 키로 등록해두고 필요할 때 조회하는 중앙 저장소다.

**난이도: 🟡 Intermediate**

> 관련 문서:
> - [Registry Primer: lookup table, resolver, router, service locator를 처음 구분하기](./registry-primer-lookup-table-resolver-router-service-locator.md)
> - [팩토리 (Factory)](./factory.md)
> - [Factory Switch Registry Smell](./factory-switch-registry-smell.md)
> - [Injected Registry vs Service Locator Checklist: 명시적 주입과 숨은 조회 구분하기](./injected-registry-vs-service-locator-checklist.md)
> - [Service Locator Antipattern](./service-locator-antipattern.md)
> - [전략 패턴](./strategy-pattern.md)
> - [Ports and Adapters vs GoF 패턴](./ports-and-adapters-vs-classic-patterns.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

Registry는 **이름과 객체를 연결해 조회 가능하게 만드는 저장소**다.  
팩토리가 객체를 만들고, Registry는 만들어진 객체를 찾는다.

backend에서 흔히 이런 형태로 나타난다.

- handler registry
- converter registry
- strategy map
- event type registry

### Retrieval Anchors

- `registry pattern`
- `registry pattern beginner`
- `registry 처음 배우는데`
- `registry 큰 그림`
- `registry 기초`
- `registry 언제 쓰는지`
- `registry backed factory`
- `lookup table`
- `lookup table beginner`
- `lookup table vs registry`
- `lookup table vs resolver`
- `lookup table vs router`
- `keyed lookup primer`
- `named handlers`
- `strategy map`
- `service registry`
- `factory vs registry`
- `resolver vs registry`
- `router vs registry`
- `registry vs service locator`
- `service locator vs registry`
- `lookup table resolver router service locator difference`
- `injected registry vs service locator checklist`
- `explicit constructor injection registry`

---

## 깊이 들어가기

### 1. Registry는 생성과 조회를 분리한다

팩토리는 생성 책임에 가깝고, Registry는 조회 책임에 가깝다.

- 새로운 구현체를 등록한다
- 이름이나 타입으로 찾는다
- 호출부는 구체 클래스를 몰라도 된다

### 2. 전략 맵은 Registry의 흔한 형태다

전략 패턴이 많아지면 `Map<Key, Strategy>`가 되곤 한다.
이건 사실상 Registry다.

### 3. 과하면 서비스 로케이터가 된다

Registry가 모든 의존성을 숨기면 문제가 생긴다.

- 어디서 무엇이 주입되는지 보이지 않는다
- 테스트가 어려워진다
- 전역 상태처럼 변한다

그래서 Registry는 **읽기 전용 룩업**에 가깝게 유지하는 편이 좋다.

### 4. switch-heavy factory를 옮길 때는 Factory를 지우지 않는다

실무에서 Registry를 배우는 계기는 종종 "거대한 switch factory를 줄이고 싶다"는 요구다.  
이때 흔한 오해는 Registry를 도입하면서 Factory를 없애고, 각 서비스가 Registry를 직접 뒤지게 만드는 것이다.

더 안전한 경계는 아래와 같다.

- Factory는 `create(key)` 같은 생성 진입점을 유지한다
- Registry는 `key -> creator` 또는 `key -> handler` lookup만 맡는다
- 어떤 key를 쓸지 고르는 규칙은 selector/policy가 맡는다
- 서비스는 Registry가 아니라 필요한 포트나 Factory를 생성자로 주입받는다

즉 Registry는 **lookup을 데이터화하는 도구**이지,  
애플리케이션 전체 의존성을 꺼내 쓰는 전역 진입점이 아니다.

---

## 실전 시나리오

### 시나리오 1: 결제 수단 핸들러

신용카드, 간편결제, 포인트 결제를 키로 찾아 처리한다.

### 시나리오 2: 메시지 타입 처리기

이벤트 타입별 핸들러를 등록해 라우팅할 때 쓸 수 있다.

### 시나리오 3: 변환기 조회

외부 포맷에 맞는 converter를 고를 때 유용하다.

---

## 코드로 보기

### Registry

```java
public class HandlerRegistry {
    private final Map<String, PaymentHandler> handlers = new HashMap<>();

    public void register(String key, PaymentHandler handler) {
        handlers.put(key, handler);
    }

    public PaymentHandler get(String key) {
        PaymentHandler handler = handlers.get(key);
        if (handler == null) {
            throw new IllegalArgumentException("unknown key: " + key);
        }
        return handler;
    }
}
```

### 사용

```java
PaymentHandler handler = registry.get(request.method());
handler.handle(request);
```

### 전략 맵

```java
Map<String, PricingStrategy> strategies = Map.of(
    "VIP", new VipPricingStrategy(),
    "NORMAL", new NormalPricingStrategy()
);
```

이 구조는 작게 쓰면 편하지만, 전역적으로 퍼지면 의존성 추적이 어려워진다.

### Registry-backed factory

```java
public final class PaymentFactory {
    private final PaymentPortRegistry registry;

    public PaymentFactory(PaymentPortRegistry registry) {
        this.registry = registry;
    }

    public PaymentPort create(PaymentMethod method) {
        return registry.creatorFor(method).get();
    }
}
```

이 구조에서는 Factory가 생성 진입점이고, Registry는 좁은 creator lookup에 머문다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| if/switch | 직접적이다 | 타입이 늘면 길어진다 | 키가 적을 때 |
| Factory | 생성이 명확하다 | 조회 개념은 약하다 | 새 객체를 만들 때 |
| Registry | 조회와 라우팅이 쉽다 | 전역 상태나 locator로 오남용되기 쉽다 | 핸들러/전략 lookup |

판단 기준은 다음과 같다.

- 객체를 "찾는" 것이 핵심이면 Registry
- 객체를 "만드는" 것이 핵심이면 Factory
- Registry를 전역 서비스 로케이터처럼 쓰지 않는다
- switch-heavy factory를 줄일 때도 호출부에 registry 조회를 퍼뜨리지 않는다

---

## 꼬리질문

> Q: Registry와 Factory의 차이는 무엇인가요?
> 의도: 생성과 조회를 분리하는지 확인한다.
> 핵심: Factory는 만들고 Registry는 찾는다.

> Q: Registry가 위험해지는 순간은 언제인가요?
> 의도: 전역 상태와 숨은 의존성을 아는지 확인한다.
> 핵심: 모든 의존성을 여기저기서 꺼내 쓰기 시작할 때다.

> Q: switch factory를 registry로 옮길 때 factory를 없애도 되나요?
> 의도: lookup과 생성 진입점을 분리하는지 확인한다.
> 핵심: 보통은 아니다. Registry는 creator lookup을 맡고, 생성 진입점은 Factory나 명시적 조립 계층에 남기는 편이 안전하다.

> Q: strategy map은 패턴인가요?
> 의도: Registry가 실무에서 어떻게 드러나는지 아는지 확인한다.
> 핵심: 네, Registry의 실전 형태로 볼 수 있다.

## 한 줄 정리

Registry 패턴은 객체를 키로 등록해 조회하게 해주지만, switch-heavy factory를 줄일 때도 전역 service locator로 커지지 않도록 Factory와의 경계를 지켜야 한다.
