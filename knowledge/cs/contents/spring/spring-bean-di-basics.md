# Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기

> 한 줄 요약: Spring Bean은 "내가 `new`로 직접 만든 객체"가 아니라, 컨테이너가 등록하고 조립하고 필요하면 프록시로 감싸서 꺼내 주는 객체다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 Bean 등록, component scan, configuration, proxy 감각을 한 번에 묶는 **beginner primer**를 담당한다. "왜 DI가 필요한가" 자체는 `spring-ioc-di-basics.md`가 먼저 담당한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring 요청 파이프라인과 Bean Container 기초: `DispatcherServlet`, 레이어 역할, Bean 등록, DI, 설정 읽기](./spring-request-pipeline-bean-container-foundations-primer.md)
- [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)
- [IoC 컨테이너와 DI](./ioc-di-container.md)
- [Bean 생명주기와 스코프 함정](./spring-bean-lifecycle-scope-traps.md)
- [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)
- [Spring Boot 자동 구성 (Auto-configuration)](./spring-boot-autoconfiguration.md)
- [Spring Bean Definition Overriding Semantics](./spring-bean-definition-overriding-semantics.md)
- [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드](./spring-primary-qualifier-collection-injection-decision-guide.md)
- [Spring DI 예외 빠른 판별](./spring-di-exception-quick-triage.md)
- [의존성 주입 기초](../software-engineering/dependency-injection-basics.md)
- [팩토리 패턴 기초](../design-pattern/factory-basics.md)

retrieval-anchor-keywords: spring bean basics, spring bean 뭐예요, component scan basics, spring proxy intuition, spring configuration basics, spring bean 언제 만들어져요, component scan vs di difference, configuration vs bean registration, 왜 transactional 안 먹어요, springbootapplication basics, 스프링 빈 처음, beginner spring bean, 빈 등록과 주입 차이, bean registration basics, component scan what is

---

## 핵심 개념

`IoC와 DI 기초`를 읽고 난 뒤에는 "왜"보다 "Spring이 실제로 어디서 객체를 올리고 연결하는가"가 다음 질문이 된다. 이 문서는 그 경계를 정리한다.

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

처음 배우는 단계에서는 이 다섯 단어를 아래처럼 대응시키면 덜 헷갈린다.

| 지금 들리는 말 | 실제로 Spring이 하는 일 | 먼저 붙잡을 질문 |
|---|---|---|
| "bean 등록" | 컨테이너가 객체 설계도와 생성 규칙을 올린다 | 이 객체는 scan으로 찾았나, `@Bean`으로 만들었나 |
| "DI" | 등록된 후보 중 맞는 의존성을 연결한다 | 누구를 누구에게 넣었나 |
| "초기화" | 주입이 끝난 뒤 준비 작업을 한다 | 연결 확인이나 캐시 예열이 필요한가 |
| "프록시" | 메서드 호출 앞에서 부가기능을 가로챈다 | 트랜잭션/캐시/보안이 왜 붙었나 |
| "사용" | 컨트롤러, 서비스, 스케줄러가 Bean을 호출한다 | 지금 문제는 요청 길찾기인가, 객체 조립인가 |

---

## 한 요청 예시로 붙여 보기

처음엔 용어를 따로 외우기보다, 한 요청에서 각 개념이 어디에 끼는지만 붙여 보면 덜 헷갈린다.

```text
POST /orders
-> DispatcherServlet 이 OrderController 로 보냄
-> OrderController 는 이미 주입된 OrderService 를 사용
-> OrderService 가 OrderRepository 를 호출
-> @Transactional 이 붙은 service 라면 프록시가 경계에서 begin/commit/rollback 처리
```

| 같은 장면에서 보이는 것 | 실제 질문 | 담당 개념 |
|---|---|---|
| `OrderController`가 어떻게 `OrderService`를 갖고 있나 | 누가 객체를 연결했나 | DI |
| `OrderService`, `OrderRepository`는 언제 올라왔나 | 어떤 객체를 Bean으로 등록했나 | component scan / `@Bean` |
| `@Transactional`이 왜 메서드 앞뒤에서 동작하나 | 누가 호출을 가로챘나 | proxy |
| `/orders`가 왜 이 컨트롤러로 오나 | 누가 URL을 연결했나 | MVC |

이 표에서 중요한 포인트는 "`/orders` 요청을 받는 일"과 "`OrderService`를 주입해 두는 일"이 같은 단계가 아니라는 점이다.

---

## 1. DI는 여기서 "등록된 Bean을 어떻게 연결하느냐"의 문제다

왜 DI가 필요한지는 [IoC와 DI 기초](./spring-ioc-di-basics.md)에서 먼저 다뤘다. 여기서는 그 다음 단계로, Spring이 **이미 등록한 Bean 후보를 어떻게 연결하는지**만 본다.

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

핵심은 `OrderService`가 `MemoryOrderRepository`를 직접 `new`하지 않는다는 점이다. 다만 이 문서의 중심은 "왜 그렇게 하느냐"보다 "그 객체가 Bean 후보로 어떻게 올라왔느냐"다.

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

앞 문서가 "DI가 필요한 이유"를 설명했다면, 여기서는 "컨테이너가 주입하려면 먼저 후보를 등록해야 한다"는 흐름을 붙인다.

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

## 2-1. 등록 방식은 이렇게 고른다

| 지금 만들려는 객체 | 먼저 떠올릴 등록 방식 | 이유 |
|---|---|---|
| `OrderService`, `OrderRepository`처럼 우리 레이어 객체 | component scan | 역할이 클래스에 이미 드러난다 |
| `Clock`, `ObjectMapper`, 외부 SDK client | `@Configuration` + `@Bean` | 내가 소유하지 않은 타입이라 stereotype을 붙일 수 없다 |
| starter가 자동으로 만들어 주는 공용 기본값 | auto-configuration | 내가 직접 만들기보다 Boot 기본 계약을 먼저 탄다 |

짧게 외우면 이렇다.

- 우리 코드 역할 객체면 scan
- 외부 객체 조립이면 `@Bean`
- Boot가 제공하는 기본값이면 auto-configuration

다음 질문이 "`그래서 언제 `@Bean`을 쓰고 Boot 자동 구성은 언제 믿죠?`"라면 [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)으로 이어진다.

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

여기서 많이 섞이는 오해를 한 번 더 잘라 두면 좋다.

| 증상 | 먼저 볼 축 | 이유 |
|---|---|---|
| `OrderService` 자체가 안 뜬다 | component scan | 후보 등록이 안 됐을 가능성이 크다 |
| `PaymentClient` 구현체가 둘이라 주입이 모호하다 | DI 후보 선택 | scan보다 `@Primary`, `@Qualifier` 문제일 수 있다 |
| `@Transactional`이 기대대로 안 먹는다 | proxy 경계 | Bean은 있어도 프록시를 우회했을 수 있다 |

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

## 4-2. Collection 주입까지만 먼저 익힌다

입문 단계에서는 `@Primary`와 `@Qualifier` 다음으로 `List<PaymentClient>`, `Map<String, PaymentClient>`만 먼저 익혀도 충분하다. 이 둘은 "후보를 하나 고르는 것"이 아니라 "후보를 전부 받는 것"이다.

초보자용 한 장 요약:

| 내가 원하는 것 | 먼저 떠올릴 도구 |
|---|---|
| 기본값 하나면 된다 | `@Primary` |
| 이번 주입에서 특정 구현체 | `@Qualifier` |
| 후보 전부 받기 | `List<T>`, `Map<String, T>` |

`ObjectProvider<T>`처럼 "지금 말고 나중에 꺼내기", scope 지연 조회 같은 주제는 초반 큰 그림을 잡은 뒤에 봐도 된다. 처음에는 "하나 고르기"와 "전부 받기"만 분리해도 DI 오류를 훨씬 빨리 읽을 수 있다. 더 필요하면 [Spring `@Primary` vs `@Qualifier` vs 컬렉션 주입 결정 가이드](./spring-primary-qualifier-collection-injection-decision-guide.md)로 내려가면 된다.

---

## 5. Bean 생명주기는 이 정도만 먼저 잡는다

입문자는 생명주기를 모두 외우기보다 "등록과 주입 뒤에도 초기화와 프록시 단계가 남아 있다"는 감각만 먼저 잡으면 된다.

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

같은 "초기화 작업"에는 잘 맞는다. 반대로 트랜잭션, 캐시, 보안처럼 프록시를 타는 동작 원리까지 여기서 한꺼번에 파고들 필요는 없다. 그런 부분은 [Bean 생명주기와 스코프 함정](./spring-bean-lifecycle-scope-traps.md), [AOP와 프록시 메커니즘](./aop-proxy-mechanism.md)에서 따로 보면 된다.

특히 beginner가 자주 묻는 질문을 한 줄로 정리하면 이렇다.

- "`@PostConstruct`는 준비 작업"에 가깝다
- "`@Transactional`은 메서드 호출을 프록시가 감싼다"에 가깝다

즉 둘은 비슷한 "어노테이션"처럼 보여도 개입 시점이 다르다.

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

## 6. Proxy는 "앞에서 한 번 더 받는 문지기" 정도로 잡는다

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

여기까지 이해하면 beginner 문서 목표는 충분하다. `@Configuration`의 `proxyBeanMethods`, BeanPostProcessor 체인, `BeanDefinition` 같은 컨테이너 내부는 이미 다음 단계다. 그런 심화는 [IoC 컨테이너와 DI](./ioc-di-container.md), [Spring `@Configuration`, `proxyBeanMethods`, and BeanPostProcessor Chain](./spring-configuration-proxybeanmethods-beanpostprocessor-chain.md)으로 넘겨 두는 편이 첫 이해에 안전하다.

### 6-1. 설정 클래스 프록시는 왜 또 따로 말할까

service의 `@Transactional` 프록시와 `@Configuration` 프록시는 목적이 다르다.

| 프록시가 붙는 자리 | 초보자용 목적 | 지금 기억할 한 줄 |
|---|---|---|
| service 메서드 앞 | 트랜잭션, 캐시, 보안 같은 부가기능 | "호출을 가로챈다" |
| `@Configuration` 클래스 | `@Bean` 메서드 사이 singleton 의미를 지킨다 | "같은 bean을 중복 생성하지 않게 돕는다" |

즉 proxy라는 단어는 같아도 "부가기능 프록시"와 "설정 조립 프록시"를 같은 이유로 붙는다고 보면 오해가 커진다.

---

## 자주 하는 혼동 4개

- "component scan이 DI를 한다"로 외우기 쉽지만, 더 정확히는 component scan은 **후보를 등록**하고 DI는 **등록된 후보를 연결**한다.
- controller가 요청마다 service를 `new`한다고 느끼기 쉽지만, 보통 service/repository는 애플리케이션 시작 때 singleton Bean으로 이미 준비된다.
- `@Transactional`을 "DB 저장 어노테이션"으로 보면 좁다. 실제로는 **Spring Bean 호출 경계에 프록시를 세우는 방식**이 핵심이다.
- 직접 `new OrderService()`를 만들고 "`@Transactional`이 안 먹는다"고 놀라기 쉽지만, 컨테이너 밖 객체는 Bean 프록시 혜택을 받지 못한다.

짧게 외우면 아래 한 줄이다.

**등록은 scan/`@Bean`, 연결은 DI, 부가기능은 proxy, 요청 길찾기는 MVC다.**

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

Bean 문서는 "Spring이 객체를 어디서 등록하고 어떻게 연결하고 왜 프록시로 감싸는가"를 한 장면으로 묶어 주는 primer라고 보면 된다.
