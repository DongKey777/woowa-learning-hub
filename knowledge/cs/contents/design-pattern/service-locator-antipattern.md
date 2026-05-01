---
schema_version: 2
title: "Service Locator Antipattern"
concept_id: "design-pattern/service-locator-antipattern"
difficulty: intermediate
doc_role: comparison
level: intermediate
aliases:
  - Service Locator
  - service locator antipattern
  - hidden dependency
  - 숨은 의존성
expected_queries:
  - Service Locator가 왜 안 좋아?
  - Service Locator랑 DI는 뭐가 달라?
  - 숨은 의존성이 왜 문제야?
  - 컨테이너에서 직접 꺼내 쓰면 왜 위험해?
acceptable_neighbors:
  - contents/spring/spring-ioc-di-basics.md
  - contents/software-engineering/dependency-injection-basics.md
---

# Service Locator Antipattern: 숨은 의존성을 만드는 조회 중심 설계

> 한 줄 요약: Service Locator는 필요한 객체를 전역 조회하게 만들어 의존성을 숨기고 테스트와 추적을 어렵게 하는 안티 패턴이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Injected Registry vs Service Locator Checklist: 명시적 주입과 숨은 조회 구분하기](./injected-registry-vs-service-locator-checklist.md)
- [Registry Primer: lookup table, resolver, router, service locator를 처음 구분하기](./registry-primer-lookup-table-resolver-router-service-locator.md)
- [Bean Name vs Domain Key Lookup: Spring handler map을 domain registry로 감싸기](./bean-name-vs-domain-key-lookup.md)
- [Hexagonal Ports: 유스케이스를 둘러싼 입출력 경계](./hexagonal-ports-pattern-language.md)
- [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](../spring/spring-bean-di-basics.md)

retrieval-anchor-keywords: service locator antipattern, applicationcontext.getbean service locator, beanfactory.getbean service locator, objectprovider.getifavailable misuse, objectprovider.getobject runtime lookup, getbean 안티패턴, 스프링 getbean 직접 호출, 처음 배우는데 getbean, hidden dependency, global lookup, service locator vs dependency injection, registry vs service locator beginner, 언제 objectprovider 쓰는지, bean name 문자열 lookup, constructor injection basics

---

## 핵심 개념

Service Locator는 객체가 필요한 의존성을 생성자 주입이 아니라 **중앙 조회소에서 직접 찾아 쓰는 방식**이다.
겉으로는 편리하지만 실제로는 숨은 결합을 만든다.

- 어떤 의존성이 필요한지 시그니처에 안 보인다
- 테스트에서 전역 상태를 조작해야 한다
- 런타임 오류가 늦게 난다

## 처음 배우는데: 20초 분기

처음에는 용어보다 질문 하나로 자르면 된다.

**"이 클래스가 필요한 협력자를 생성자만 보고 말할 수 있는가?"**

- 예: DI/좁은 registry 쪽일 가능성이 크다.
- 아니오 + 본문에 `ApplicationContext.getBean(...)`이 보임: service locator 안티 패턴 신호다.

| 검색어가 이렇게 들어오면 | 먼저 볼 문서 | 이유 |
|---|---|---|
| `hidden dependency`, `global lookup` | 이 문서 | 숨은 의존성/전역 조회 문제를 먼저 자른다 |
| `ApplicationContext.getBean` | 이 문서 | Spring 컨테이너 직접 조회가 왜 냄새인지 바로 확인한다 |
| `BeanFactory.getBean`, `ObjectProvider.getIfAvailable` | 이 문서 | 메서드 본문 조회인지, optional 주입인지 먼저 구분한다 |
| `registry vs service locator` | [Injected Registry vs Service Locator Checklist: 명시적 주입과 숨은 조회 구분하기](./injected-registry-vs-service-locator-checklist.md) | 코드 리뷰 기준으로 빠르게 판별한다 |
| `lookup table resolver router` | [Registry Primer: lookup table, resolver, router, service locator를 처음 구분하기](./registry-primer-lookup-table-resolver-router-service-locator.md) | 용어 큰 그림을 먼저 정리한다 |

### Retrieval Anchors

- `service locator antipattern`
- `applicationcontext.getbean service locator`
- `beanfactory.getbean service locator`
- `objectprovider.getifavailable misuse`
- `objectprovider.getobject runtime lookup`
- `getbean 안티패턴`
- `스프링 getbean 직접 호출`
- `처음 배우는데 getbean`
- `hidden dependency`
- `global lookup`
- `service locator vs dependency injection`
- `registry vs service locator beginner`

---

## 깊이 들어가기

### 1. 편리함이 함정이다

직접 주입받으면 클래스 시그니처에서 의존성이 보인다.
Service Locator는 그걸 숨겨버린다.

### 2. Registry와 같은 것이 아니다

Registry는 보통 명시적 lookup table이고, Service Locator는 객체가 필요할 때마다 전역적으로 의존성을 찾는 방식이다.

여기서 초보자가 자주 헷갈리는 변형이 있다.

- `BeanFactory.getBean(...)`: 컨테이너를 직접 조회하면 locator 쪽 냄새가 강하다.
- `ObjectProvider.getIfAvailable()`: 생성자에서 optional 협력자를 늦게 확인하는 용도면 괜찮을 수 있다.
- 하지만 서비스 본문에서 `provider.getObject()`나 `getIfAvailable()`로 매 요청마다 구현체를 찾기 시작하면, 이름만 다를 뿐 같은 lookup 중심 설계가 된다.

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
