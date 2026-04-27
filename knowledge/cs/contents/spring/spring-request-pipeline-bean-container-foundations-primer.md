# Spring 요청 파이프라인과 Bean Container 기초: `DispatcherServlet`, 레이어 역할, Bean 등록, DI, 설정 읽기

> 한 줄 요약: Spring 초반에는 "요청은 `DispatcherServlet`이 받고, 일은 controller -> service -> repository로 흘러가고, 그 객체들은 Bean 컨테이너가 미리 등록하고 주입해 둔다"는 한 장의 그림을 먼저 잡는 게 가장 중요하다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 `DispatcherServlet`, controller/service/repository 역할, Bean 등록, DI, component scan, `application.yml` 설정 읽기를 한 흐름으로 묶는 **beginner bridge primer**를 담당한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring README: 요청 파이프라인 엔트리](./README.md#spring-요청-파이프라인과-bean-container-기초)
- [Junior Backend Roadmap: 5단계 Spring 기본기 연결](../../JUNIOR-BACKEND-ROADMAP.md#5단계-spring-기본기-연결)
- [Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름](./spring-mvc-controller-basics.md)
- [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
- [Spring `404`/`405` vs Bean Wiring Error Confusion Card: 요청 매핑 실패와 DI 예외를 먼저 분리하기](./spring-404-405-vs-bean-wiring-confusion-card.md)
- [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)
- [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)
- [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property](./spring-property-source-precedence-quick-guide.md)
- [Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정](./spring-component-scan-failure-patterns.md)
- [Spring Service-Layer Transaction Boundary Patterns](./spring-service-layer-transaction-boundary-patterns.md)
- [IoC 컨테이너와 DI](./ioc-di-container.md)
- [HTTP 요청-응답 기본 흐름](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)
- [SQL 읽기와 관계형 모델링 기초](../database/sql-reading-relational-modeling-primer.md)

retrieval-anchor-keywords: spring request pipeline beginner, spring bean container foundation, dispatcherservlet beginner, controller service repository roles, controller service repository 차이, spring mission structure, woowacourse backend spring structure, 우테코 백엔드 스프링 구조, spring bean registration vs di, component scan beginner, @SpringBootApplication scan beginner, configuration reading spring, application yml spring beginner, @ConfigurationProperties beginner, @Value beginner, spring request flow and bean container, spring 입문 한 장 그림, dispatcher servlet bean container relationship, spring primer return path, spring readme request pipeline entrypoint, spring to network http bridge, spring to database sql primer bridge, beginner backend lane handoff, spring request flow entry route, http mvc ioc di beginner bridge

## 첫 읽기 엔트리 루트 (HTTP -> MVC -> IoC/DI)

처음 읽을 때는 문서를 깊이 파기보다, 아래 3단계로 "요청 의도 -> 요청 진입 -> 객체 연결" 순서만 먼저 고정하면 된다.

| 단계 | 먼저 답할 질문 | 먼저 읽을 문서 | 여기로 돌아오는 이유 |
|---|---|---|---|
| 1 | 이 요청은 조회/생성/수정/삭제 중 무엇인가 | [HTTP 메서드와 REST 멱등성 입문](../network/http-methods-rest-idempotency-basics.md) | `GET/POST` 의도를 잡아야 컨트롤러 매핑이 덜 헷갈린다 |
| 2 | 이 URL 요청은 어떤 컨트롤러 메서드로 들어오는가 | [Spring MVC 컨트롤러 기초](./spring-mvc-controller-basics.md) | `DispatcherServlet -> @GetMapping/@PostMapping` 연결을 먼저 본다 |
| 3 | 컨트롤러가 호출한 service/repository는 누가 연결했는가 | [IoC와 DI 기초](./spring-ioc-di-basics.md) | `new` 대신 컨테이너 주입으로 wiring되는 이유를 붙인다 |

이 문서는 위 3단계를 한 장으로 다시 묶어 "요청 처리 흐름"과 "객체 준비 흐름"이 어디서 만나는지 설명한다.

## 이 문서 다음에 보면 좋은 문서

- 학습 흐름으로 돌아가려면 [Spring README: 요청 파이프라인 엔트리](./README.md#spring-요청-파이프라인과-bean-container-기초), [Junior Backend Roadmap: 5단계 Spring 기본기 연결](../../JUNIOR-BACKEND-ROADMAP.md#5단계-spring-기본기-연결)을 먼저 본다.
- 컨트롤러 진입 지점을 먼저 얕게 보고 싶다면 [Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름](./spring-mvc-controller-basics.md)로 이어진다.
- MVC 내부 전략 객체까지 보고 싶다면 [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)로 이어진다.
- `404`/`405`와 bean wiring 예외를 자꾸 한 문제로 섞는다면 [Spring `404`/`405` vs Bean Wiring Error Confusion Card: 요청 매핑 실패와 DI 예외를 먼저 분리하기](./spring-404-405-vs-bean-wiring-confusion-card.md)에서 "요청 길찾기 vs 객체 조립"부터 다시 자른다.
- Bean 후보 선택, `@Primary`, `@Qualifier`까지 가려면 [Spring Bean과 DI 기초: Component Scan, Configuration, Proxy 감각 잡기](./spring-bean-di-basics.md)를 같이 본다.
- `@Configuration`, `@Bean`, Boot 기본 설정이 어떻게 이어지는지 보려면 [Spring Configuration vs Auto-configuration 입문: `@Configuration`, `@Bean`, `proxyBeanMethods`](./spring-configuration-vs-autoconfiguration-primer.md)로 이어진다.
- `application.yml` 값이 왜 기대와 다르게 들어오는지 먼저 가르려면 [Spring Property Source 우선순위 빠른 판별: `application.yml`, profile, env var, command-line, test property](./spring-property-source-precedence-quick-guide.md)로 넘어간다.
- 단일 설정값 주입과 설정 객체 바인딩을 언제 나눌지 헷갈리면 [Spring `@Value` vs `@ConfigurationProperties` Env Guide](./spring-value-vs-configurationproperties-env-guide.md)로 이어진다.
- Bean이 아예 안 뜬다면 [Spring Component Scan 실패 패턴: `@SpringBootApplication`, 패키지 경계, Multi-Module 함정](./spring-component-scan-failure-patterns.md)에서 scan 경계부터 본다.
- HTTP 요청 자체가 아직 흐리면 [HTTP 요청-응답 기본 흐름](../network/http-request-response-basics-url-dns-tcp-tls-keepalive.md)으로 한 번 내려가 네트워크 단계부터 다시 맞춘다.
- Repository/JPA 전에 SQL 관계 모델부터 안전하게 정리하려면 [SQL 읽기와 관계형 모델링 기초](../database/sql-reading-relational-modeling-primer.md)로 이어진다.

---

## 핵심 개념

Spring 입문 초반에는 사실 두 흐름만 먼저 구분하면 된다.

1. **요청 처리 흐름**
   브라우저나 테스트가 보낸 HTTP 요청이 `DispatcherServlet`을 지나 controller -> service -> repository로 흘러가는 과정
2. **객체 준비 흐름**
   애플리케이션 시작 시점에 Spring 컨테이너가 Bean을 등록하고, 의존성을 주입하고, 필요하면 설정값까지 묶어 두는 과정

초보자가 자주 헷갈리는 이유는 이 둘이 한 장면처럼 보이기 때문이다.

- 요청이 들어올 때마다 Spring이 controller를 새로 만드는 것 같고
- `@Service`, `@Repository`가 요청 중간에 갑자기 나타나는 것 같고
- `application.yml` 값도 요청을 받을 때마다 읽는 것처럼 느껴진다

하지만 보통은 반대다.

- Bean은 **대부분 애플리케이션 시작 때** 준비된다
- 요청이 오면 `DispatcherServlet`이 **이미 준비된 Bean**을 꺼내서 흐름을 연결한다
- 설정값도 대개 **시작 시점에 읽혀 Bean에 바인딩**된다

즉 초반 mental model은 이 한 줄이면 충분하다.

**컨테이너가 미리 조립해 두고, 요청이 들어오면 MVC가 그 조립된 객체를 사용한다.**

---

## 큰 그림 한 번에 보기

```text
애플리케이션 시작
  -> @SpringBootApplication 기준으로 component scan
  -> @Configuration / @Bean / auto-configuration으로 Bean 등록
  -> 생성자 주입으로 controller/service/repository 연결
  -> application.yml 값을 필요한 Bean에 바인딩

HTTP 요청 도착
  -> DispatcherServlet
  -> Controller Bean 호출
  -> Service Bean 호출
  -> Repository Bean 호출
  -> 응답 반환
```

여기서 초보자가 먼저 끊어 읽어야 할 포인트는 아래다.

| 구간 | 질문 | 담당 |
|---|---|---|
| 애플리케이션 시작 | 어떤 객체를 Spring이 관리할까 | Bean 컨테이너 |
| 애플리케이션 시작 | 객체끼리 누구를 주입할까 | DI |
| 요청 처리 | 이 URL을 누가 처리할까 | `DispatcherServlet` + MVC |
| 요청 처리 | 실제 비즈니스 로직과 DB 접근은 누가 할까 | service / repository |
| 애플리케이션 시작 | 설정 파일 값은 어디에 담길까 | property binding |

---

## 1. `DispatcherServlet`과 Bean 컨테이너는 다른 역할이다

둘을 같은 것으로 보면 거의 모든 입문 혼동이 시작된다.

| 개념 | 하는 일 | 언제 주로 보나 |
|---|---|---|
| Bean 컨테이너 | Bean 등록, 생성, 의존성 주입 | 애플리케이션 시작 |
| `DispatcherServlet` | 들어온 HTTP 요청을 적절한 컨트롤러로 보냄 | 요청 처리 시점 |

`DispatcherServlet`은 controller를 "생성"하는 객체가 아니라, **이미 컨테이너에 등록된 controller Bean을 찾아 실행 흐름에 태우는 관문**에 가깝다.

이 차이를 짧게 요약하면 아래와 같다.

- Bean 컨테이너: "이 앱에 어떤 객체가 필요하고 어떻게 연결할까?"
- `DispatcherServlet`: "이번 요청은 어느 controller 메서드로 보낼까?"

그래서 미션에서 `NoSuchBeanDefinitionException`이 났다면 MVC보다 **Bean 등록/scan/DI** 쪽을 먼저 봐야 하고,
404나 매핑 문제라면 Bean 생성이 아니라 **MVC 요청 매핑** 쪽을 먼저 봐야 한다.

---

## 2. controller / service / repository는 역할을 나누기 위한 레이어다

우테코 백엔드 미션에서 가장 자주 보는 구조를 아주 단순화하면 이 표다.

| 레이어 | 주된 책임 | 보통 하지 않는 일 |
|---|---|---|
| controller | HTTP 요청/응답 다루기, 입력 받기, 서비스 호출 | SQL 직접 실행, 긴 비즈니스 규칙 누적 |
| service | 유스케이스 흐름 조합, 비즈니스 규칙 적용 | HTTP 세부사항 처리, 화면/JSON 포맷 책임 |
| repository | DB/저장소 접근 | 요청 파라미터 해석, 화면/응답 결정 |

예를 들면 주문 조회는 보통 이렇게 읽는다.

```text
GET /orders/1
-> OrderController 가 path variable을 받음
-> OrderService 가 "주문 조회"라는 유스케이스를 수행
-> OrderRepository 가 DB에서 주문을 읽음
-> Service 가 응답용 데이터를 정리
-> Controller 가 HTTP 응답으로 돌려줌
```

### 왜 굳이 나누는가

- controller는 웹 기술이 바뀌면 영향을 받기 쉽다
- repository는 저장소 기술이 바뀌면 영향을 받기 쉽다
- service는 그 사이에서 "우리 도메인 규칙"을 지키는 중심이 된다

즉 레이어 분리는 멋으로 하는 게 아니라, **변화 이유를 분리하기 위한 장치**다.

---

## 3. Bean은 어떻게 등록되는가: component scan과 `@Bean`

Spring 입문에서 Bean 등록 경로는 일단 두 가지로 보면 충분하다.

| 등록 방식 | 언제 자연스러운가 | 예시 |
|---|---|---|
| component scan | 우리 애플리케이션의 controller/service/repository | `@Controller`, `@Service`, `@Repository` |
| `@Configuration` + `@Bean` | 외부 라이브러리 객체, 명시적 설정 객체 | `Clock`, `ObjectMapper`, custom client |

### component scan 예시

```java
@RestController
@RequestMapping("/orders")
public class OrderController {
    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }
}

@Service
public class OrderService {
    private final OrderRepository orderRepository;

    public OrderService(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }
}

@Repository
public class OrderRepository {
}
```

`@SpringBootApplication`이 있는 패키지와 그 하위 패키지 안에 있으면, Spring이 이런 stereotype annotation을 보고 Bean 후보로 등록한다.

### `@Bean` 등록 예시

```java
@Configuration
public class AppConfig {

    @Bean
    public Clock systemClock() {
        return Clock.systemUTC();
    }
}
```

여기서 beginner 기준으로 기억할 규칙은 간단하다.

- 우리 코드의 기본 레이어는 보통 scan으로 등록한다
- 외부 객체나 설정 객체는 보통 `@Bean`으로 명시 등록한다

---

## 4. DI는 "누가 누구를 만든 뒤 연결하느냐"의 문제다

Spring을 쓰지 않으면 보통 내가 직접 `new`를 이어 붙인다.

```java
OrderRepository orderRepository = new OrderRepository();
OrderService orderService = new OrderService(orderRepository);
OrderController orderController = new OrderController(orderService);
```

Spring에서는 그 연결을 컨테이너가 맡는다.

```java
@RestController
public class OrderController {
    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }
}
```

이 코드의 핵심은 controller가 service를 직접 만들지 않는다는 점이다.

- controller는 "OrderService가 필요하다"만 선언한다
- Spring은 등록된 Bean 중에서 `OrderService`를 찾아 넣는다

그래서 생성자 주입이 beginner 기준 기본 선택이 된다.

| 방식 | beginner 기준 해석 |
|---|---|
| 생성자 주입 | 필수 의존성을 명확히 드러내서 가장 읽기 쉽다 |
| setter 주입 | 선택 의존성일 때만 제한적으로 고려한다 |
| 필드 주입 | 짧아 보이지만 테스트와 구조 파악이 어렵다 |

---

## 5. 설정 파일은 어떻게 읽혀 Bean으로 연결되는가

미션에서 `application.yml`을 볼 때도 같은 그림으로 읽으면 된다.

```yaml
app:
  payment-timeout-ms: 1500
```

이 값이 곧바로 service 코드 안으로 순간이동하는 것은 아니다.
보통은 아래처럼 한 번 Bean에 묶인 뒤 다른 Bean이 주입받는다.

```java
@ConfigurationProperties(prefix = "app")
public record AppProperties(long paymentTimeoutMs) {
}
```

이 예시는 `@ConfigurationPropertiesScan` 또는 `@EnableConfigurationProperties(AppProperties.class)`로 이 타입이 Bean으로 등록됐다고 가정한다.

```java
@Service
public class PaymentService {
    private final AppProperties appProperties;

    public PaymentService(AppProperties appProperties) {
        this.appProperties = appProperties;
    }

    public long timeoutMs() {
        return appProperties.paymentTimeoutMs();
    }
}
```

이 흐름을 한 줄로 줄이면 이렇다.

```text
application.yml
-> property source 로딩
-> @ConfigurationProperties / @Value 바인딩
-> Bean 생성
-> service 등이 그 Bean을 주입받아 사용
```

### `@Value`와 `@ConfigurationProperties`를 어떻게 구분할까

| 방식 | 언제 쓰기 쉬운가 | beginner 기준 |
|---|---|---|
| `@Value("${app.payment-timeout-ms}")` | 값 한두 개를 빠르게 읽을 때 | 작은 예제에서는 가능 |
| `@ConfigurationProperties` | 관련 설정 여러 개를 묶을 때 | 미션 코드가 커지면 이쪽이 더 읽기 쉽다 |

중요한 점은 둘 다 결국 **설정값을 Bean 세계로 끌어오는 방법**이라는 것이다.

단일 env var와 설정 묶음을 언제 가를지 더 직접적인 판단 기준은 [Spring `@Value` vs `@ConfigurationProperties` Env Guide](./spring-value-vs-configurationproperties-env-guide.md)에 따로 정리되어 있다.

---

## 6. 미션 코드에서 한 번에 읽는 예시

아래처럼 보면 request pipeline과 Bean container를 한 번에 연결하기 쉽다.

```java
@RestController
@RequestMapping("/orders")
public class OrderController {
    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @PostMapping
    public OrderResponse create(@RequestBody OrderRequest request) {
        return orderService.create(request);
    }
}

@Service
public class OrderService {
    private final OrderRepository orderRepository;
    private final AppProperties appProperties;

    public OrderService(OrderRepository orderRepository, AppProperties appProperties) {
        this.orderRepository = orderRepository;
        this.appProperties = appProperties;
    }

    public OrderResponse create(OrderRequest request) {
        Order order = new Order(request.productId(), appProperties.paymentTimeoutMs());
        Order saved = orderRepository.save(order);
        return OrderResponse.from(saved);
    }
}

@Repository
public class OrderRepository {
    public Order save(Order order) {
        return order;
    }
}
```

이 예시를 눈으로 읽는 순서는 아래가 가장 실용적이다.

1. `DispatcherServlet`이 `/orders` 요청을 `OrderController`로 보낸다
2. controller는 HTTP 입력을 자바 객체로 받고 service를 호출한다
3. service는 비즈니스 규칙과 설정값을 함께 사용한다
4. repository는 저장 책임을 맡는다
5. 이 셋은 모두 Spring Bean이라서 컨테이너가 생성자 주입으로 연결한다

---

## 7. 초보자가 자주 헷갈리는 지점

### 오해 1. 요청이 올 때마다 controller/service/repository가 새로 만들어진다

보통은 아니다. 기본 scope인 singleton이면 애플리케이션 시작 시점에 한 번 만들어 두고 재사용한다.

### 오해 2. `DispatcherServlet`이 service나 repository도 직접 호출한다

직접 아는 것은 보통 controller까지다.
service와 repository 연결은 MVC가 아니라 **Bean 주입 구조** 안에서 이뤄진다.

### 오해 3. controller가 repository를 바로 호출해도 항상 같은 수준으로 괜찮다

기술적으로는 가능해도, 미션이 커질수록 비즈니스 규칙과 HTTP 처리 코드가 섞여 읽기 어려워진다.
기본값은 controller -> service -> repository 구조로 두는 편이 안전하다.

### 오해 4. `application.yml`은 필요할 때마다 파일을 다시 읽는다

보통은 시작 시점에 환경과 함께 읽혀 바인딩되고, 실행 중에는 그 결과 Bean이나 값이 사용된다.

### 오해 5. Bean 주입 오류가 나면 무조건 `@Qualifier`부터 붙이면 된다

초반에는 먼저 아래 둘을 나눠야 한다.

- Bean이 **아예 없나**: package, stereotype annotation, scan boundary를 확인
- Bean이 **여러 개라 못 고르나**: `@Primary`, `@Qualifier`를 확인

### 오해 6. HTTP 메서드 개념과 DI 개념이 같은 층위다

둘은 서로 다른 질문에 답한다.

| 구분 | 질문 | 예시 |
|---|---|---|
| HTTP 메서드 | "클라이언트가 서버에 무엇을 하려는가?" | `POST /orders` |
| MVC 매핑 | "이 요청을 어느 컨트롤러 메서드가 받는가?" | `@PostMapping("/orders")` |
| DI | "컨트롤러 안의 `orderService`는 누가 넣어주는가?" | 생성자 주입 |

`POST`를 `PUT`으로 바꿔도 DI 구조는 그대로이고, `@Qualifier`를 바꿔도 HTTP 메서드 의미는 그대로다.
문제가 생겼을 때 이 세 층위를 분리하면 디버깅이 빨라진다.

---

## 한 줄 정리

Spring 초반의 핵심은 "`DispatcherServlet`이 요청을 controller로 보내고, controller/service/repository는 컨테이너가 미리 등록하고 DI로 연결하며, 설정값도 그 Bean 세계 안으로 읽혀 들어온다"는 전체 그림을 먼저 머리에 고정하는 것이다.
