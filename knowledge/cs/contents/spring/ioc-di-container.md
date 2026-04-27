# IoC 컨테이너와 의존성 주입 (IoC Container & Dependency Injection)


> 한 줄 요약: IoC 컨테이너와 의존성 주입 (IoC Container & Dependency Injection)는 입문자가 먼저 잡아야 할 핵심 기준과 실무에서 헷갈리는 경계를 한 문서에서 정리한다.
> Spring의 심장은 IoC 컨테이너다. 객체의 생성, 조립, 생명주기를 프레임워크가 제어하는 구조를 코드 레벨에서 해체한다.

**난이도: 🟡 Intermediate**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../database/transaction-basics.md)

> 관련 문서:
> - [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
> - [Spring ApplicationContext Refresh Phases](./spring-application-context-refresh-phases.md)
> - [Spring BeanFactoryPostProcessor vs BeanPostProcessor Lifecycle](./spring-beanfactorypostprocessor-vs-beanpostprocessor-lifecycle.md)
> - [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)
> - [Spring Boot Condition Evaluation Report Debugging](./spring-boot-condition-evaluation-report-debugging.md)
> - [Spring Startup Bean Graph Debugging Playbook](./spring-startup-bean-graph-debugging-playbook.md)
> - [Spring Bean Definition Overriding Semantics](./spring-bean-definition-overriding-semantics.md)
> - [Spring `FactoryBean` and `SmartInitializingSingleton` Extension Points](./spring-factorybean-smartinitializingsingleton-extension-points.md)
> - [Spring Early Bean References and Circular Proxy Traps](./spring-early-bean-reference-circular-proxy-traps.md)
> - [Spring `@ConfigurationProperties` Binding Internals](./spring-configurationproperties-binding-internals.md)

retrieval-anchor-keywords: beandefinition, beanfactory, applicationcontext, beanfactorypostprocessor, beanpostprocessor, autowire candidate, scope, circular dependency, constructor injection, bean overriding, condition evaluation report, ioc di container basics, ioc di container beginner, ioc di container intro, spring basics

---

## 핵심 개념

**IoC(Inversion of Control)** 란 객체의 생성과 의존 관계 설정의 제어권이 개발자에서 프레임워크로 역전되는 것이다.

**DI(Dependency Injection)** 는 IoC를 구현하는 패턴 중 하나로, 의존 객체를 외부에서 주입받는 방식이다.

Spring IoC 컨테이너의 핵심 인터페이스 계층:

```
BeanFactory (최상위 — 지연 초기화, 기본 DI)
  └── ApplicationContext (즉시 초기화, 이벤트, 국제화, AOP 통합)
        ├── AnnotationConfigApplicationContext (Java Config)
        ├── ClassPathXmlApplicationContext (XML Config)
        └── GenericWebApplicationContext (웹 환경)
```

### Spring 없이 DI를 구현하면?

```java
// 직접 의존성을 조립하는 코드 — "수동 DI"
public class OrderService {
    private final OrderRepository repository;
    private final PaymentGateway gateway;

    public OrderService() {
        // 구체 클래스에 직접 의존 — 교체·테스트가 어려움
        this.repository = new JdbcOrderRepository(new HikariDataSource());
        this.gateway = new TossPaymentGateway(new RestTemplate());
    }
}

// 사용처에서 객체 그래프를 직접 조립
DataSource ds = new HikariDataSource();
OrderRepository repo = new JdbcOrderRepository(ds);
PaymentGateway gw = new TossPaymentGateway(new RestTemplate());
OrderService service = new OrderService(repo, gw); // 생성자 DI 수동 버전
```

Spring을 사용하면 이 조립 코드가 컨테이너 내부로 이동한다.

---

## 깊이 들어가기

### 1. BeanDefinition — 빈의 설계도

Spring은 `@Component`, `@Bean`, XML 등 다양한 소스를 모두 **BeanDefinition**이라는 메타데이터 객체로 통일한다.

```
@Configuration 클래스 → ConfigurationClassBeanDefinitionReader → BeanDefinition
@Component 스캔    → ClassPathBeanDefinitionScanner      → BeanDefinition
XML                → XmlBeanDefinitionReader              → BeanDefinition
```

`BeanDefinition`에 담기는 정보:
- Bean 클래스명, scope, lazy 여부
- 생성자 인자, 프로퍼티 값
- init-method, destroy-method
- depends-on 관계

실무에서는 이 설계도 단계가 매우 중요하다.

- `BeanDefinitionRegistryPostProcessor`는 새 정의를 추가하거나 기존 정의를 바꿀 수 있다.
- `BeanFactoryPostProcessor`는 이미 등록된 정의를 조정한다.
- `@Import`, `@ImportResource`, `ImportBeanDefinitionRegistrar`는 정의 등록을 확장하는 대표 통로다.

즉, 컨테이너 확장은 "인스턴스 생성"보다 먼저 일어나는 경우가 많다.

### 2. Bean 생명주기 (Lifecycle)

```
1. BeanDefinition 등록
2. BeanFactoryPostProcessor 실행 (BeanDefinition 조작 시점)
3. 인스턴스 생성 (Constructor)
4. 의존성 주입 (@Autowired, setter)
5. BeanPostProcessor#postProcessBeforeInitialization
6. @PostConstruct / InitializingBean#afterPropertiesSet / init-method
7. BeanPostProcessor#postProcessAfterInitialization  ← AOP 프록시가 여기서 생성됨
8. 사용
9. @PreDestroy / DisposableBean#destroy / destroy-method
10. GC
```

**핵심 포인트**: AOP 프록시는 7단계에서 만들어진다. 따라서 `@PostConstruct` 시점(6단계)에서는 프록시가 아닌 실제 객체의 메서드가 호출된다. 이 시점에서 `@Transactional` 메서드를 호출하면 트랜잭션이 적용되지 않는다.

여기에 더해, Spring Boot의 자동 구성과 조건부 등록은 이 생명주기 사이에 끼어든다.

## 깊이 들어가기 (계속 2)

- `ConditionEvaluationReport`는 어떤 정의가 왜 들어오고 빠지는지 설명한다.
- `@ConfigurationProperties` 바인딩은 이후 설정 객체를 안정적으로 주입하는 데 쓰인다.
- `ApplicationContext` refresh가 끝나기 전에 일부 Bean은 아직 완성되지 않았을 수 있다.

### 3. Bean Scope

| Scope | 설명 | 인스턴스 수 |
|-------|------|------------|
| `singleton` (기본) | 컨테이너당 1개 | 1 |
| `prototype` | 요청마다 새로 생성 | N |
| `request` | HTTP 요청당 1개 | 요청 수 |
| `session` | HTTP 세션당 1개 | 세션 수 |
| `application` | ServletContext당 1개 | 1 |

### 4. Singleton 빈의 함정

#### 함정 1: 상태를 가진 Singleton

```java
@Service
public class PriceCalculator {
    private int discountRate; // 공유 상태! 위험!

    public void setDiscountRate(int rate) {
        this.discountRate = rate; // Thread A가 10 설정 → Thread B가 20 설정 → Thread A가 20 읽음
    }

    public int calculate(int price) {
        return price * (100 - discountRate) / 100;
    }
}
```

Singleton 빈은 여러 스레드가 공유한다. **변경 가능한 인스턴스 필드를 두면 동시성 버그**가 발생한다. 해결책:
- 상태를 메서드 로컬 변수로 이동
- `ThreadLocal` 사용
- 불변 객체로 설계

#### 함정 2: Singleton 안에 Prototype 주입

```java
@Component @Scope("prototype")
public class ShoppingCart { /* 사용자별 장바구니 */ }

@Service
public class OrderService {
    private final ShoppingCart cart; // Singleton 생성 시 딱 한 번 주입됨!

    public OrderService(ShoppingCart cart) {
        this.cart = cart; // 모든 사용자가 같은 cart 공유 — 버그!
    }
}
```

**해결책 — Provider 패턴:**

## 깊이 들어가기 (계속 3)

```java
@Service
public class OrderService {
    private final ObjectProvider<ShoppingCart> cartProvider;

    public OrderService(ObjectProvider<ShoppingCart> cartProvider) {
        this.cartProvider = cartProvider;
    }

    public void order() {
        ShoppingCart cart = cartProvider.getObject(); // 매번 새 인스턴스
    }
}
```

또는 `@Scope(proxyMode = ScopedProxyMode.TARGET_CLASS)`로 프록시를 통해 매번 새 인스턴스를 위임할 수 있다.

### 5. 의존성 해석은 후보 선택의 문제다

Spring은 같은 타입의 빈이 여러 개일 수 있다는 전제를 가진다.

- `@Primary`는 기본 후보를 정한다.
- `@Qualifier`는 특정 후보를 명시한다.
- `ObjectProvider`는 필요할 때 꺼내도록 한다.
- `Collection`/`Map` 주입은 여러 후보를 한 번에 받는다.

이 구분을 이해하지 못하면 "주입이 안 된다"가 아니라 "어느 후보를 골라야 할지 모른다"가 정확한 문제다.

---

## 실전 시나리오

### 시나리오: 순환 의존 (Circular Dependency)

```java
@Service
public class A {
    private final B b;
    public A(B b) { this.b = b; }
}

@Service
public class B {
    private final A a;
    public B(A a) { this.a = a; }
}
```

Spring Boot 2.6부터 **생성자 주입 순환 의존은 기본적으로 금지**되었다. (`spring.main.allow-circular-references=false`)

내부적으로 Spring은 "3단계 캐시"로 순환 의존을 해결할 수 있다:

```
singletonObjects        (1차 — 완성된 빈)
earlySingletonObjects   (2차 — 아직 의존성 주입 안 된 빈)
singletonFactories      (3차 — 빈을 만들 수 있는 팩토리)
```

생성자 주입은 객체 자체가 아직 만들어지지 않았으므로 3단계 캐시로도 해결 불가능하다. **Setter 주입이나 @Lazy**를 사용하면 우회 가능하지만, 순환 의존 자체가 설계 문제의 신호이므로 의존 방향을 재설계하는 것이 바람직하다.

### 시나리오: 프로퍼티는 바뀌었는데 설정 객체에 반영되지 않음

이 경우는 `@Value`와 `@ConfigurationProperties` 바인딩 시점 차이를 먼저 봐야 한다.

- 설정값은 이미 환경에 들어가 있지만
- 바인딩 대상 객체가 늦게 생성되거나
- prefix나 relaxed binding 규칙이 어긋났을 수 있다

이 문맥은 [Spring `@ConfigurationProperties` Binding Internals](./spring-configurationproperties-binding-internals.md)에서 더 자세히 이어진다.

---

## 코드로 보기

### BeanFactory 수동 구현 (미니 IoC 컨테이너)

Spring 없이 IoC 컨테이너의 핵심 원리를 이해하기 위한 간략한 구현:

```java
public class MiniContainer {
    private final Map<Class<?>, Object> beans = new ConcurrentHashMap<>();
    private final Map<Class<?>, Supplier<?>> factories = new ConcurrentHashMap<>();

    // 빈 팩토리 등록
    public <T> void register(Class<T> type, Supplier<T> factory) {
        factories.put(type, factory);
    }

    // Singleton 방식으로 빈 조회
    @SuppressWarnings("unchecked")
    public <T> T getBean(Class<T> type) {
        return (T) beans.computeIfAbsent(type, k -> {
            Supplier<?> factory = factories.get(k);
            if (factory == null) throw new IllegalArgumentException("No bean: " + k);
            return factory.get();
        });
    }
}

// 사용
MiniContainer container = new MiniContainer();
container.register(OrderRepository.class, () -> new JdbcOrderRepository());
container.register(OrderService.class, () ->
    new OrderService(container.getBean(OrderRepository.class))
);

OrderService service = container.getBean(OrderService.class);
```

이것이 Spring의 `DefaultListableBeanFactory`가 하는 일의 극도로 단순화된 버전이다. 실제 Spring은 여기에 BeanDefinition 파싱, BeanPostProcessor 체인, 스코프 관리, AOP 프록시 생성 등이 추가된다.

### 주입 방식 비교

## 코드로 보기 (계속 2)

```java
// 1. 생성자 주입 (권장)
@Service
public class OrderService {
    private final OrderRepository repository;

    public OrderService(OrderRepository repository) { // 단일 생성자면 @Autowired 생략 가능
        this.repository = repository;
    }
}

// 2. Setter 주입
@Service
public class OrderService {
    private OrderRepository repository;

    @Autowired
    public void setRepository(OrderRepository repository) {
        this.repository = repository;
    }
}

// 3. 필드 주입 (비추천)
@Service
public class OrderService {
    @Autowired
    private OrderRepository repository;
    // 테스트에서 목 주입이 리플렉션 없이는 불가능
    // final 불가 → 불변성 보장 안 됨
}
```

**생성자 주입이 권장되는 이유:**
- `final` 필드로 불변성 보장
- 필수 의존성 누락 시 컴파일 타임에 감지
- 테스트에서 new로 직접 생성 가능 (프레임워크 의존성 없음)
- 순환 의존을 조기에 발견 가능

---

## 트레이드오프

| 관점 | IoC/DI 사용 | 직접 생성 (new) |
|------|-------------|----------------|
| 유연성 | 인터페이스 기반 교체 용이 | 구체 클래스에 강결합 |
| 테스트 | Mock 주입 쉬움 | 의존 객체 교체 어려움 |
| 디버깅 | 빈 생성 흐름 추적 어려움 | 직관적, 스택트레이스 명확 |
| 학습곡선 | 컨테이너 동작 이해 필요 | 없음 |
| 성능 | 초기화 시 리플렉션 비용 | 직접 호출로 빠름 |
| 순환의존 | 컨테이너가 감지 가능 | 런타임 StackOverflow |

---

## 꼬리질문

1. `BeanFactory`와 `ApplicationContext`의 차이는 무엇인가? 어떤 상황에서 `BeanFactory`를 쓰는가?
2. `@Autowired`는 내부적으로 어떤 `BeanPostProcessor`가 처리하는가? (`AutowiredAnnotationBeanPostProcessor`)
3. `@Configuration` 클래스에서 `@Bean` 메서드를 서로 호출하면 매번 새 객체가 생성되는가? (`CGLIB 프록시`로 Singleton 보장)
4. `@Primary`와 `@Qualifier`는 어떤 시점에 어떻게 해석되는가?
5. Prototype 빈에 `@PreDestroy`를 달면 호출되는가? (아니다 — 컨테이너가 Prototype의 소멸을 관리하지 않음)
6. `BeanFactoryPostProcessor`와 `BeanPostProcessor`의 실행 시점과 역할 차이는?
7. `BeanDefinitionRegistryPostProcessor`는 언제 필요한가?
8. `@ConfigurationProperties`는 왜 `@Value`보다 구조적인가?

---

## 한 줄 정리

> Spring IoC 컨테이너는 BeanDefinition을 설계도로 삼아 객체를 생성하고, BeanPostProcessor 체인을 통해 의존성 주입부터 AOP 프록시 생성까지 수행하는 **객체 생명주기 관리 엔진**이다.
