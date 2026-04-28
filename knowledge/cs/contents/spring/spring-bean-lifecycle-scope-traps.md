# Bean 생명주기와 스코프 함정

> 한 줄 요약: Spring Bean은 생성만 되는 객체가 아니라, 생명주기와 스코프, 프록시 시점까지 같이 이해해야 안전하게 쓸 수 있다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../database/transaction-basics.md)


retrieval-anchor-keywords: spring bean lifecycle scope traps, singleton mutable state bug, prototype bean singleton injection trap, request scope async trap, scoped proxy objectprovider difference, @postconstruct transactional trap, bean scope deep dive, 스프링 빈 스코프 함정, request scope 비동기 문제, prototype singleton 주입 문제, scoped proxy objectprovider 차이, 왜 singleton 상태가 섞여요, request scope 왜 async 에서 깨져요, scoped proxy 왜 헷갈려요
> 관련 문서:
> - [Spring Bean 생명주기 기초: 생성부터 소멸까지](./spring-bean-lifecycle-basics.md)
> - [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
> - [IoC 컨테이너와 DI](./ioc-di-container.md)
> - [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)
> - [Spring Request Scope Proxy Pitfalls](./spring-request-scope-proxy-pitfalls.md)
> - [@Transactional 깊이 파기](./transactional-deep-dive.md)
> - [Spring Security 아키텍처](./spring-security-architecture.md)

---

> retrieval-anchor-keywords:
> - Spring bean lifecycle
> - bean scope traps
> - singleton scope
> - prototype scope
> - request scope
> - session scope
> - scoped proxy
> - ObjectProvider
> - provider vs proxy
> - prototype lookup timing
> - request lookup timing
> - @PostConstruct
> - @PreDestroy
> - bean 생명주기
> - 스코프 함정

## 핵심 개념

처음 배우는 단계에서 "빈은 언제 만들어져요?", "singleton이랑 prototype 뭐가 달라요?"를 묻는다면 이 문서보다 [Spring Bean 생명주기 기초: 생성부터 소멸까지](./spring-bean-lifecycle-basics.md)를 먼저 보는 편이 안전하다. 이 문서는 그 다음 단계에서 **왜 상태 공유 버그가 생기고, 왜 scope와 프록시가 같이 꼬이는지**를 파고드는 심화 카드다.

Spring Bean은 컨테이너가 만드는 객체다.
중요한 건 “객체를 만든다”가 아니라, **언제 만들고, 어디까지 공유하고, 어떤 시점에 프록시로 바뀌는가**다.

핵심 축은 세 가지다.

1. 생명주기: 생성, 의존성 주입, 초기화, 소멸
2. 스코프: singleton, prototype, request, session, application
3. 프록시: 실제 객체가 아니라 래퍼를 통해 호출이 가로채질 수 있음

이 문서를 봐야 하는 이유는 단순하다.
Spring에서 가장 자주 나는 버그는 “Bean이 이상하다”가 아니라, **상태를 잘못 공유했거나 프록시가 안 타는 구조**이기 때문이다.

---

## 깊이 들어가기

### 1. 생명주기에서 중요한 시점

Spring Bean의 일반적인 흐름은 이렇다.

```text
BeanDefinition 등록
-> 인스턴스 생성
-> 의존성 주입
-> BeanPostProcessor before
-> 초기화 콜백
-> BeanPostProcessor after
-> 사용
-> 소멸 콜백
```

실무에서 중요한 포인트는 두 가지다.

- `@PostConstruct`는 아직 프록시가 아닐 수 있다
- `BeanPostProcessor#postProcessAfterInitialization` 이후에 AOP 프록시가 적용될 수 있다

즉, 초기화 시점에 트랜잭션/캐시/AOP를 기대하면 어긋날 수 있다.

### 2. scope는 공유 범위를 정한다

| Scope | 의미 | 함정 |
|---|---|---|
| `singleton` | 컨테이너당 1개 | 상태 필드를 두면 전 요청이 공유한다 |
| `prototype` | 조회할 때마다 새 인스턴스 | singleton에 직접 주입하면 1번만 생성된다 |
| `request` | HTTP 요청당 1개 | 비동기 작업으로 넘기면 사라질 수 있다 |
| `session` | HTTP 세션당 1개 | 세션 저장소, 스티키 세션 문제와 연결된다 |
| `application` | ServletContext당 1개 | 전역 캐시처럼 쓰다 메모리 누수가 난다 |

### 3. 프록시는 scope와 생명주기를 더 헷갈리게 만든다

`@Transactional`, `@Cacheable`, `@Async` 같은 기능은 프록시 기반이다.
즉, Bean이 있어도 **호출 경로가 프록시를 지나지 않으면 적용되지 않는다.**

대표적인 함정:

- `this.method()` 내부 호출
- `@PostConstruct` 안에서 트랜잭션 기대
- `prototype` 빈을 singleton에 필드로 고정
- request/session scope를 async thread에 그대로 기대

---

## 실전 시나리오

### 시나리오 1: singleton 서비스에 상태를 넣었다

```java
@Service
public class DiscountService {
    private int discountRate;

    public void setDiscountRate(int discountRate) {
        this.discountRate = discountRate;
    }

    public int priceOf(int basePrice) {
        return basePrice * (100 - discountRate) / 100;
    }
}
```

이 코드는 테스트에서는 그럴듯하지만 운영에서 깨진다.

- 요청 A가 10을 넣고
- 요청 B가 30을 넣고
- 요청 A가 30을 읽을 수 있다

해결은 상태를 메서드 로컬로 내리거나, 아예 불변으로 만드는 것이다.

### 시나리오 2: prototype 빈을 singleton에 주입했다

```java
@Component
@Scope("prototype")
public class ShoppingCart {
}

@Service
public class OrderService {
    private final ShoppingCart cart;

    public OrderService(ShoppingCart cart) {
        this.cart = cart;
    }
}
```

이 경우 `OrderService`가 만들어질 때 한 번만 주입된다.
원하는 건 “호출마다 새 인스턴스”인데 실제로는 “주입 시점 1회”다.

해결은 `ObjectProvider`나 scoped proxy다.
둘 다 짧은 수명의 bean을 singleton에 직접 고정하지 않는다는 점은 같지만, **실제 대상을 조회하는 시점**은 다르다.

### 시나리오 3: request scope를 비동기 작업에 넘겼다

request scope는 요청 스레드와 강하게 묶인다.
비동기 큐로 넘긴 뒤 나중에 쓰려고 하면 값이 이미 사라져 있을 수 있다.

이 문제는 [Spring Security 아키텍처](./spring-security-architecture.md)의 `SecurityContext` 스레드 로컬 모델과도 비슷하다.

---

## 코드로 보기

### 안전한 provider 사용

```java
@Service
public class OrderService {
    private final ObjectProvider<ShoppingCart> shoppingCartProvider;

    public OrderService(ObjectProvider<ShoppingCart> shoppingCartProvider) {
        this.shoppingCartProvider = shoppingCartProvider;
    }

    public void order() {
        ShoppingCart cart = shoppingCartProvider.getObject();
        // 매 호출마다 새 instance
    }
}
```

### scoped proxy

```java
@Component
@Scope(value = WebApplicationContext.SCOPE_REQUEST, proxyMode = ScopedProxyMode.TARGET_CLASS)
public class RequestUserContext {
}
```

프록시가 실제 request scope 객체를 대신한다.
이 방식은 편하지만, 원인을 숨길 수 있어서 남용하면 추적이 어려워진다.

### `ObjectProvider`와 scoped proxy는 조회 시점이 다르다

둘 다 "지금은 긴 수명의 singleton 안에 있지만, 실제 짧은 수명 bean은 나중에 찾는다"는 점은 같다.
차이는 **언제 그 lookup이 일어나는지 코드에서 드러나는가**다.

| 비교 축 | `ObjectProvider` | scoped proxy |
|---|---|---|
| singleton에 주입되는 것 | provider 핸들 | proxy 객체 |
| 실제 target 조회 시점 | `getObject()`를 호출하는 순간 | proxy 메서드를 호출하는 순간 |
| 조회 시점 가시성 | 높다. 호출 코드가 직접 드러낸다 | 낮다. 호출자는 평범한 bean처럼 보인다 |
| `prototype`에서의 감각 | "이번 작업에서 한 번 꺼내 로컬 변수로 재사용"이 쉽다 | 같은 필드처럼 보여도 메서드 호출마다 새 target이 풀릴 수 있다 |
| `request`에서의 감각 | request가 살아 있을 때만 명시적으로 꺼낸다 | 요청마다 다른 target을 프록시 뒤에서 자동으로 연결한다 |

#### prototype bean: provider는 조회 횟수, proxy는 호출 횟수가 기준이 된다

## 코드로 보기 (계속 2)

```java
@Component
@Scope(ConfigurableBeanFactory.SCOPE_PROTOTYPE)
public class PrototypeTrace {
    private final UUID id = UUID.randomUUID();

    public UUID id() {
        return id;
    }
}

@Service
public class CheckoutService {
    private final ObjectProvider<PrototypeTrace> traceProvider;

    public CheckoutService(ObjectProvider<PrototypeTrace> traceProvider) {
        this.traceProvider = traceProvider;
    }

    public void checkout() {
        PrototypeTrace trace = traceProvider.getObject();
        log.info("first={}", trace.id());
        log.info("second={}", trace.id());
    }
}
```

여기서는 `getObject()`를 한 번만 불렀으므로 `trace`는 같은 인스턴스다.
즉, 한 작업 단위 안에서 prototype을 한 번 꺼내 재사용하고 싶다면 provider 쪽이 더 직관적이다.

```java
@Component
@Scope(value = ConfigurableBeanFactory.SCOPE_PROTOTYPE, proxyMode = ScopedProxyMode.TARGET_CLASS)
public class PrototypeTrace {
    private final UUID id = UUID.randomUUID();

    public UUID id() {
        return id;
    }
}

@Service
public class CheckoutService {
    private final PrototypeTrace trace;

    public CheckoutService(PrototypeTrace trace) {
        this.trace = trace;
    }

    public void checkout() {
        log.info("first={}", trace.id());
        log.info("second={}", trace.id());
    }
}
```

이 경우 `trace` 필드는 하나처럼 보이지만, shared proxy 뒤에서 method invocation마다 prototype target이 다시 풀린다.
그래서 prototype에서는 "한 번 조회해서 같은 인스턴스를 계속 쓴다"는 의도를 provider가 더 분명하게 드러낸다.

#### request bean: 둘 다 현재 요청 target을 보지만, lookup을 숨기는 정도가 다르다

## 코드로 보기 (계속 3)

```java
@Component
@RequestScope
public class RequestUserContext {
    private final UUID requestId = UUID.randomUUID();

    public UUID requestId() {
        return requestId;
    }
}

@Service
public class AuditService {
    private final ObjectProvider<RequestUserContext> contextProvider;
    private final RequestUserContext requestUserContext;

    public AuditService(
            ObjectProvider<RequestUserContext> contextProvider,
            RequestUserContext requestUserContext
    ) {
        this.contextProvider = contextProvider;
        this.requestUserContext = requestUserContext;
    }

    public UUID providerStyle() {
        return contextProvider.getObject().requestId();
    }

    public UUID proxyStyle() {
        return requestUserContext.requestId();
    }
}
```

`@RequestScope`는 기본적으로 scoped proxy를 만든다.
그래서 `requestUserContext` 필드에는 실제 request bean이 아니라 proxy가 들어가고, 메서드를 호출하는 순간 현재 요청의 target을 찾는다.

반면 provider는 `getObject()` 호출 시점이 코드에 남는다.
같은 request 안에서는 둘 다 같은 request target을 보지만, request 밖에서 접근하면 둘 다 실패할 수 있다.

정리하면 이렇다.

- `ObjectProvider`: "지금 이 줄에서 lookup한다"는 의도를 드러낸다
- scoped proxy: "평범한 의존성처럼 보이게 하되 lookup을 프록시 뒤로 숨긴다"
- prototype에서는 provider가 작업 단위별 인스턴스 경계를 더 잘 보여 준다
- request에서는 scoped proxy가 주입 코드를 단순하게 만들지만, 실제 조회 시점은 메서드 호출 순간이다

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| singleton + 무상태 | 단순하고 빠르다 | 상태가 들어가면 위험하다 | 대부분의 서비스 |
| prototype | 인스턴스 분리가 쉽다 | lifecycle 관리가 어렵다 | 생성 시점마다 별도 객체가 필요할 때 |
| request/session scope | 웹 요청과 자연스럽다 | 비동기/배치에 취약하다 | 웹 요청 상태 보관 |
| scoped proxy | 주입이 편하다 | 디버깅이 어렵다 | scope 객체를 singleton에 연결해야 할 때 |
| provider 조회 | 의도가 명확하다 | 코드가 약간 장황하다 | scope 객체를 명시적으로 가져오고 싶을 때 |

핵심 기준은 하나다.
**공유해도 되는 상태인지, 요청마다 분리해야 하는 상태인지 먼저 구분해야 한다.**

---

## 꼬리질문

> Q: singleton bean에 mutable field를 두면 왜 위험한가?
> 의도: 스레드 공유와 상태 오염 이해 여부 확인
> 핵심: 컨테이너 스코프와 동시성은 분리해서 봐야 한다

> Q: `@PostConstruct`에서 `@Transactional`을 호출하면 왜 기대와 다를 수 있는가?
> 의도: 프록시 생성 시점 이해 확인
> 핵심: 초기화 시점은 아직 프록시 이후가 아닐 수 있다

> Q: prototype bean을 singleton에 넣으면 왜 매번 새 객체가 아니라고 보는가?
> 의도: 주입 시점과 조회 시점 구분
> 핵심: scope는 주입이 아니라 조회 방식과 함께 봐야 한다

> Q: `ObjectProvider`와 scoped proxy를 둘 다 "지연 조회"라고만 보면 왜 부족한가?
> 의도: 조회 시점 차이 이해 확인
> 핵심: provider는 `getObject()` 시점, proxy는 메서드 호출 시점에 target을 푼다

> Q: request scope를 async 작업에 넘길 때 왜 조심해야 하는가?
> 의도: 요청 생명주기와 thread boundary 이해
> 핵심: request context는 thread-local과 함께 사라질 수 있다

---

## 한 줄 정리

Bean은 만들 수만 있으면 끝이 아니다. 생명주기, scope, 프록시 시점을 같이 봐야 운영에서 안 터진다.
