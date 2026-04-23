# Service Locator Antipattern: 숨은 의존성을 만드는 조회 중심 설계

> 한 줄 요약: Service Locator는 필요한 객체를 전역 조회하게 만들어 의존성을 숨기고 테스트와 추적을 어렵게 하는 안티 패턴이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Registry Primer: lookup table, resolver, router, service locator를 처음 구분하기](./registry-primer-lookup-table-resolver-router-service-locator.md)
> - [Registry Pattern](./registry-pattern.md)
> - [Injected Registry vs Service Locator Checklist: 명시적 주입과 숨은 조회 구분하기](./injected-registry-vs-service-locator-checklist.md)
> - [Strategy Registry vs Service Locator Drift Note](./strategy-registry-vs-service-locator-drift.md)
> - [Bean Name vs Domain Key Lookup: Spring handler map을 domain registry로 감싸기](./bean-name-vs-domain-key-lookup.md)
> - [Hexagonal Ports: 유스케이스를 둘러싼 입출력 경계](./hexagonal-ports-pattern-language.md)
> - [Plugin Architecture: 기능을 꽂아 넣는 패턴 언어](./plugin-architecture-pattern-language.md)
> - [안티 패턴](./anti-pattern.md)

---

## 핵심 개념

Service Locator는 객체가 필요한 의존성을 생성자 주입이 아니라 **중앙 조회소에서 직접 찾아 쓰는 방식**이다.  
겉으로는 편리하지만 실제로는 숨은 결합을 만든다.

- 어떤 의존성이 필요한지 시그니처에 안 보인다
- 테스트에서 전역 상태를 조작해야 한다
- 런타임 오류가 늦게 난다

### Retrieval Anchors

- `service locator antipattern`
- `service locator beginner`
- `service locator 처음 배우는데`
- `service locator 큰 그림`
- `service locator 기초`
- `hidden dependency`
- `hidden dependency lookup beginner`
- `global lookup`
- `global lookup antipattern`
- `전역 조회소 안티패턴`
- `testability issue`
- `service locator vs dependency injection`
- `service locator vs registry`
- `registry vs service locator beginner`
- `lookup table vs service locator`
- `resolver router registry service locator`
- `ApplicationContext getBean service locator`
- `injected registry vs service locator checklist`
- `strategy registry vs service locator drift`
- `strategy lookup helper smell`
- `ApplicationContext getBean handler smell`
- `explicit constructor injection registry`

---

## 깊이 들어가기

### 1. 편리함이 함정이다

직접 주입받으면 클래스 시그니처에서 의존성이 보인다.  
Service Locator는 그걸 숨겨버린다.

### 2. Registry와 같은 것이 아니다

Registry는 보통 명시적 lookup table이고, Service Locator는 객체가 필요할 때마다 전역적으로 의존성을 찾는 방식이다.

### 3. 테스트가 어려워진다

전역 locator에 등록된 객체를 바꿔야 하므로 테스트 격리가 깨지기 쉽다.

---

## 실전 시나리오

### 시나리오 1: 오래된 코드베이스

기존에 locator가 많다면 줄여나가는 방향이 낫다.

### 시나리오 2: 플러그인 시스템

플러그인 조회를 locator처럼 쓰기 쉬우나, 명시적 registry와 구분해야 한다.

### 시나리오 3: 테스트

의존성 주입이 더 단순하고 안전하다.

---

## 코드로 보기

### Bad

```java
public class OrderService {
    public void place() {
        PaymentPort paymentPort = ServiceLocator.get(PaymentPort.class);
        paymentPort.pay(new PaymentRequest());
    }
}
```

### Better

```java
public class OrderService {
    private final PaymentPort paymentPort;

    public OrderService(PaymentPort paymentPort) {
        this.paymentPort = paymentPort;
    }
}
```

### Why it matters

```java
// 의존성이 생성자에 나타나야 테스트와 리뷰가 쉬워진다.
```

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| Service Locator | 호출이 짧다 | 숨은 의존성이 생긴다 | 거의 없음 |
| Constructor Injection | 의존성이 보인다 | 생성자가 길어질 수 있다 | 일반적인 backend |
| Registry | lookup이 명시적이다 | 오남용 시 locator가 된다 | 핸들러/전략 조회 |

판단 기준은 다음과 같다.

- 의존성이 시그니처에 보여야 한다
- 전역 조회를 기본값으로 두지 않는다
- registry를 locator처럼 쓰지 않는다

---

## 꼬리질문

> Q: Service Locator가 왜 안티 패턴인가요?
> 의도: 숨은 의존성과 테스트 문제를 아는지 확인한다.
> 핵심: 객체가 무엇을 필요로 하는지 보이지 않기 때문이다.

> Q: Registry와 Service Locator는 어떻게 다르죠?
> 의도: lookup table과 전역 의존성 해소를 구분하는지 확인한다.
> 핵심: Registry는 명시적 조회, Locator는 숨은 조회다.

> Q: locator를 완전히 못 쓰는 건가요?
> 의도: 절대 규칙으로 오해하지 않는지 확인한다.
> 핵심: 가능은 하지만 기본 설계로는 피하는 편이 좋다.

## 한 줄 정리

Service Locator는 의존성을 숨겨 테스트와 추적을 어렵게 만드는 대표적인 안티 패턴이다.
