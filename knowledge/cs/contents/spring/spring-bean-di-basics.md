# Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기

> 한 줄 요약: Spring Bean은 "내가 `new`로 직접 만든 객체"가 아니라, 컨테이너가 등록하고 조립하고 필요하면 프록시로 감싸서 꺼내 주는 객체다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 Bean, DI, component scan, configuration, proxy 감각을 한 번에 잡는 **beginner primer**를 담당한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring 요청 파이프라인과 Bean Container 기초: `DispatcherServlet`, 레이어 역할, Bean 등록, DI, 설정 읽기](./spring-request-pipeline-bean-container-foundations-primer.md)
- [IoC 컨테이너와 DI](./ioc-di-container.md)
- [Bean 생명주기와 스코프 함정](./spring-bean-lifecycle-scope-traps.md)
- [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)
- [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)
- [Spring Bean Definition Overriding Semantics](./spring-bean-definition-overriding-semantics.md)
- [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드](./spring-primary-qualifier-collection-injection-decision-guide.md)
- [Spring DI 예외 빠른 판별](./spring-di-exception-quick-triage.md)
- [의존성 주입 기초](../software-engineering/dependency-injection-basics.md)
- [팩토리 패턴 기초](../design-pattern/factory-basics.md)

retrieval-anchor-keywords: spring bean basics, spring bean 뭐예요, dependency injection basics, component scan basics, spring proxy intuition, constructor injection, qualifier annotation basics, primary annotation basics, collection injection, objectprovider basics, springbootapplication basics, 스프링 빈 처음, beginner spring bean, intro spring di

---

## 핵심 개념

Spring 입문 초반에는 아래 다섯 개만 먼저 구분하면 된다.

- Bean: Spring 컨테이너가 관리하는 객체
- DI: Bean이 필요로 하는 다른 객체를 컨테이너가 넣어 주는 방식
- Component Scan: `@Component`, `@Service`, `@Repository`, `@Controller` 같은 후보를 자동으로 찾는 과정
- Configuration: `@Configuration`, `@Bean`으로 "이 객체는 이렇게 만들라"고 명시하는 방식
- Proxy: 진짜 객체 앞에 한 겹 더 두어 호출을 가로채는 래퍼

초보자가 자주 헷갈리는 이유는 이 다섯 개가 한 번에 섞여 보이기 때문이다.

- "빈이 등록된다"는 말과
- "의존성이 주입된다"는 말과
- "트랜잭션이 적용된다"는 말은

모두 같은 시점의 얘기가 아니다.

---

## 큰 흐름 한 번에 보기

애플리케이션 시작부터 Bean 사용까지를 아주 단순화하면 이 순서다.

```text
@SpringBootApplication 시작
-> component scan + configuration + auto-configuration으로 BeanDefinition 등록
-> 컨테이너가 의존성 후보를 찾음
-> Bean 생성자 호출
-> 의존성 주입
-> 초기화 콜백 실행
-> 필요한 Bean은 프록시로 감쌈
-> 애플리케이션이 Bean 사용
```

처음에는 아래 순서만 머리에 남겨 두면 충분하다.

**등록 -> 주입 -> 초기화 -> 프록시 -> 사용**

---

## 1. DI는 "객체를 누가 조립하느냐"의 문제다

Spring을 쓰기 전에는 보통 내가 직접 의존 객체를 만든다.

```java
OrderRepository orderRepository = new MemoryOrderRepository();
OrderService orderService = new OrderService(orderRepository);
```

Spring에서는 객체 그래프 조립을 컨테이너가 맡는다.

```java
@Repository
public class MemoryOrderRepository implements OrderRepository {
}

@Service
public class OrderService {
    private final OrderRepository orderRepository;

    public OrderService(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }
}
```

핵심은 `OrderService`가 `MemoryOrderRepository`를 직접 `new`하지 않는다는 점이다.

- 서비스는 "무엇이 필요하다"만 말한다
- 컨테이너는 "그걸 누구로 채울지"를 결정한다

이 분리가 있어야 테스트, 교체, 확장이 쉬워진다.

### 생성자 주입을 기본으로 보는 이유

| 방식 | 느낌 | beginner 기준 |
|---|---|---|
| 생성자 주입 | 생성 시점에 필요한 의존성이 고정된다 | 기본 선택 |
| setter 주입 | 선택 의존성이나 재설정이 가능하다 | 정말 선택일 때만 |
| 필드 주입 | 짧게 쓰기 쉽다 | 학습용 예제 외에는 피하는 편이 낫다 |

생성자 주입을 기본으로 두면 아래가 자연스럽다.

- 필수 의존성이 빠진 객체를 만들기 어렵다
- 테스트에서 직접 생성하기 쉽다
- 객체가 불변에 가까워진다

---

## 2. Component Scan과 `@Bean` 등록은 역할이 다르다

Spring은 Bean을 두 가지 큰 경로로 많이 등록한다.

### Component Scan

애플리케이션 코드 안의 "역할 객체"를 자동 발견한다.

```java
@Controller
public class OrderController {
}

@Service
public class OrderService {
}

@Repository
public class JpaOrderRepository {
}
```

보통 아래처럼 생각하면 된다.

- `@Controller`: 웹 요청 진입점
- `@Service`: 도메인 로직
- `@Repository`: 영속성 접근
- `@Component`: 위 셋 말고도 컨테이너에 올릴 일반 컴포넌트

### `@Configuration` + `@Bean`

"자동 발견"보다 "명시적 조립"이 중요할 때 쓴다.

```java
@Configuration
public class AppConfig {

    @Bean
    public Clock systemClock() {
        return Clock.systemUTC();
    }

    @Bean
    public ObjectMapper objectMapper() {
        return new ObjectMapper();
    }
}
```

이 방식이 특히 자연스러운 경우는 아래다.

- 내가 소유하지 않은 라이브러리 클래스를 Bean으로 올릴 때
- 생성 로직이 길거나 분기될 때
- 같은 타입을 여러 개 등록하면서 이름과 역할을 분명히 하고 싶을 때

### 둘을 같이 놓고 보기

| 등록 방식 | 잘 맞는 대상 | 한 줄 감각 |
|---|---|---|
| component scan | 우리 코드의 service/repository/controller | "찾아서 올린다" |
| `@Bean` | 외부 라이브러리 객체, 명시적 조립 | "직접 만들어 올린다" |
| auto-configuration | 프레임워크 기본값 | "조건이 맞으면 대신 올려 준다" |

---

## 3. `@SpringBootApplication`은 scan 시작점도 정한다

Spring Boot 초보자가 자주 놓치는 포인트다.

`@SpringBootApplication`은 아래를 묶는다.

- `@Configuration`
- `@EnableAutoConfiguration`
- `@ComponentScan`

즉, 애플리케이션 메인 클래스의 패키지 위치가 component scan 범위를 사실상 결정한다.

예를 들어 메인 클래스가 `com.example.app`에 있으면, 보통 그 하위 패키지가 스캔 대상이다.

```text
com.example.app
  ├── Application
  ├── order
  │   └── OrderService
  └── member
      └── MemberRepository
```

이 구조면 자연스럽다. 반대로 메인 클래스를 너무 깊거나 엉뚱한 패키지에 두면 이런 문제가 난다.

- `NoSuchBeanDefinitionException`
- 컨트롤러가 안 잡힘
- 서비스가 주입되지 않음

초보자 기준으로는 "Bean 등록이 안 된다면, 먼저 scan 범위와 어노테이션부터 본다"가 가장 실용적이다.

---

## 4. 같은 타입 빈이 여러 개면 후보 선택 문제가 된다

DI 오류는 "주입 기능이 고장 났다"보다 "후보가 둘 이상이라 못 고른다"인 경우가 많다.

```java
public interface PaymentClient {
    void pay();
}

@Component
public class TossPaymentClient implements PaymentClient {
}

@Component
public class KakaoPaymentClient implements PaymentClient {
}
```

이 상태에서 그냥 `PaymentClient`를 주입하면 Spring은 어느 구현체를 넣어야 할지 모른다.

이때 자주 쓰는 도구는 네 가지다.

- `@Primary`: 기본 후보를 정한다
- `@Qualifier`: 특정 이름이나 qualifier를 지정한다
- `List<PaymentClient>`, `Map<String, PaymentClient>`: 여러 후보를 한 번에 받는다
- `ObjectProvider<PaymentClient>`: 지금 당장 하나를 확정하지 않고 나중에 조회한다

즉, DI는 단순 연결이 아니라 **후보 해석 규칙**까지 포함한 메커니즘이다.

### 4-1. `@Primary`와 `@Qualifier` — 기본값과 명시적 선택

`@Primary`는 같은 타입 후보가 여러 개일 때 기본 선택지를 정한다.

```java
@Component
@Primary
public class TossPaymentClient implements PaymentClient {
}
```

`CheckoutService`처럼 `PaymentClient`를 그냥 주입하면 `TossPaymentClient`를 받는다.

`@Qualifier`는 주입 지점에서 특정 후보를 정확히 찍을 때 쓴다.

```java
public RefundService(@Qualifier("kakaoPaymentClient") PaymentClient paymentClient) { ... }
```

초보자 기준:

| 상황 | 실제 선택 |
|---|---|
| 단일 주입 + `@Primary` 있음 | `@Primary` bean |
| 단일 주입 + `@Qualifier` 있음 | qualifier가 가리킨 bean |
| 둘 다 있음 | `@Qualifier`가 더 구체적이다 |

---

## 4-2. Collection 주입과 ObjectProvider — 후보 수집과 지연 조회

`List<PaymentClient>`, `Map<String, PaymentClient>`는 후보를 전부 받는다. `@Primary`가 있어도 collection에는 둘 다 들어간다.

`ObjectProvider<PaymentClient>`는 즉시 확정하지 않고 나중에 꺼낸다.

- optional bean: `getIfAvailable()`
- request scope 객체: 매번 새로 꺼내야 할 때
- 실행 시점에 조회해야 할 때

초보자용 한 장 요약:

| 내가 원하는 것 | 먼저 떠올릴 도구 |
|---|---|
| 기본값 하나면 된다 | `@Primary` |
| 이번 주입에서 특정 구현체 | `@Qualifier` |
| 후보 전부 받기 | `List<T>`, `Map<String, T>` |
| 나중에, 또는 없을 수도 있는 bean | `ObjectProvider<T>` |

---

## 5. Bean 생명주기는 생성 직후 끝나지 않는다

Bean은 "생성"만으로 끝나지 않는다.

```text
정의 등록
-> 생성자 호출
-> 의존성 주입
-> 초기화 콜백(@PostConstruct)
-> 필요하면 프록시 적용
-> 사용
-> 소멸(@PreDestroy)
```

입문 단계에서 특히 중요한 포인트는 두 가지다.

### 1. `@PostConstruct`는 초기화 훅이다

- 연결 확인
- 캐시 예열
- 간단한 검증

같은 "초기화 작업"에는 잘 맞는다.

하지만 "프록시를 반드시 타야 하는 호출"은 여기서 기대하지 않는 편이 안전하다.

### 2. 기본 scope는 singleton이다

대부분의 Bean은 기본적으로 singleton이다. 즉, 컨테이너 안에 한 개가 만들어져 공유된다.

그래서 아래 같은 코드는 위험하다.

```java
@Service
public class CouponService {
    private String currentUserId;
}
```

이 필드는 모든 요청이 공유할 수 있다. 초보자에게는 아래 원칙이 가장 중요하다.

**singleton 서비스에는 요청별 가변 상태를 넣지 않는다.**

---

## 6. Proxy는 "앞에서 한 번 더 받는 객체"라고 이해하면 된다

`@Transactional`, `@Cacheable`, `@Async` 같은 기능이 초반에 어렵게 느껴지는 이유는 프록시를 못 잡아서다.

감각은 단순하다.

```text
클라이언트 -> 프록시 -> 실제 객체
```

프록시는 중간에서 이런 일을 한다.

- 트랜잭션 시작/종료
- 캐시 조회
- 보안 검사
- 메서드 실행 전후 로깅

즉, 어노테이션이 마법을 부리는 게 아니라, **프록시가 메서드 호출을 가로채는 것**이다.

### 왜 내부 호출은 자주 기대와 다를까

```java
@Service
public class OrderService {

    public void placeOrder() {
        saveOrder(); // this.saveOrder()와 같은 내부 호출
    }

    @Transactional
    public void saveOrder() {
    }
}
```

외부에서 프록시를 통해 `saveOrder()`를 부르면 트랜잭션이 걸릴 수 있다.
하지만 같은 클래스 안에서 `saveOrder()`를 직접 부르면 프록시를 우회할 수 있다.

초보자 기준 한 줄 감각은 이거다.

**프록시 기능은 "빈 밖에서 빈으로 들어오는 호출"에서 먼저 의심한다.**

### `@Configuration`도 프록시 감각과 연결된다

`@Configuration` 클래스는 경우에 따라 프록시처럼 동작해 `@Bean` 메서드가 같은 singleton을 돌려주도록 보정한다.

입문 단계에서는 아래만 기억해도 충분하다.

- `@Bean` 메서드끼리 직접 호출이 섞이면 단순 자바 메서드 호출이 아닐 수 있다
- 이 영역은 AOP 프록시와는 목적이 다르지만 "중간에서 호출을 보정한다"는 감각은 비슷하다

---

## 7. 초보자가 먼저 점검할 체크리스트

문제가 생기면 아래 순서로 보면 대부분 빠르게 좁혀진다.

1. 이 객체가 정말 Spring Bean인가
2. component scan 범위 안에 있는가
3. 같은 타입 Bean이 둘 이상인가
4. 직접 `new`로 만들어서 컨테이너 밖 객체가 된 건 아닌가
5. `@Transactional` 같은 프록시 기능을 내부 호출에서 기대한 건 아닌가
6. singleton Bean에 요청별 상태를 넣은 건 아닌가

---

## 꼬리질문

> Q: component scan과 `@Bean` 등록의 차이는 무엇인가?
> 의도: 자동 발견과 명시적 조립을 구분하는지 확인
> 핵심: "찾아서 등록"과 "직접 만들어 등록"의 차이

> Q: 같은 타입 Bean이 두 개일 때 왜 DI가 실패할 수 있는가?
> 의도: DI를 후보 선택 문제로 이해하는지 확인
> 핵심: `@Primary`, `@Qualifier` 감각

> Q: `@Transactional`이 어떤 메서드에서는 되고 어떤 메서드에서는 안 되는 이유는 무엇인가?
> 의도: 프록시 경계 이해 확인
> 핵심: 내부 호출은 프록시를 우회할 수 있음

> Q: singleton 서비스에 mutable field를 넣으면 왜 위험한가?
> 의도: Bean scope와 요청 단위 상태를 분리해서 보는지 확인
> 핵심: 컨테이너 singleton은 여러 요청이 공유함

---

## 한 줄 정리

Bean, DI, scan, configuration, proxy를 따로 외우지 말고 "컨테이너가 객체를 등록하고 조립하고 필요하면 감싸서 꺼내 준다"는 한 문장으로 묶어 두면 Spring 입문이 훨씬 덜 헷갈린다.
