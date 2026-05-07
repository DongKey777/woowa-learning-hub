---
schema_version: 3
title: 'Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름'
concept_id: spring/mvc-controller-basics
canonical: true
category: spring
difficulty: beginner
doc_role: primer
level: beginner
language: mixed
source_priority: 90
mission_ids:
- missions/roomescape
- missions/shopping-cart
review_feedback_tags:
- mvc-controller
- mvc
- controller
- restcontroller
aliases:
- Spring MVC
- Controller
- RestController
- DispatcherServlet
intents:
- definition
linked_paths:
- contents/spring/spring-mvc-request-lifecycle-basics.md
- contents/spring/spring-request-pipeline-bean-container-foundations-primer.md
- contents/spring/spring-controller-entity-return-vs-dto-return-primer.md
- contents/spring/spring-dispatcherservlet-handlerinterceptor-beginner-bridge.md
expected_queries:
- Spring MVC가 뭐야?
- Controller는 요청을 어떻게 받아?
- DispatcherServlet이 뭐야?
- Controller랑 RestController 차이가 뭐야?
contextual_chunk_prefix: |
  이 문서는 학습자가 URL과 메서드를 묶어 요청을 받아 응답을 돌려주는
  Spring 클래스를 어떻게 만드는지, DispatcherServlet에서 컨트롤러까지의
  요청 흐름을 처음 잡는 primer다. URL과 메서드 묶기, 요청 받아 응답 돌려주기,
  컨트롤러 만드는 법, URL과 메서드를 묶어 요청을 받아서 응답을 돌려주는
  클래스, RestController vs Controller, @RequestMapping 자연어 paraphrase가
  본 문서의 큰 그림에 매핑된다.
---
# Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름

> 한 줄 요약: 처음 배우는데 Spring MVC 큰 그림이 헷갈리면, HTTP 요청을 `DispatcherServlet`이 받아 컨트롤러를 찾고 실행해 응답으로 돌려주는 흐름만 먼저 잡으면 된다.

## 미션 진입 증상

| 학습자 발화 | 미션 장면 | 이 문서에서 먼저 잡을 것 |
|---|---|---|
| "Controller가 요청을 어떻게 받아요?" | roomescape 예약 생성 API에서 URL, HTTP method, request body를 method에 묶는 첫 구현 | DispatcherServlet이 handler method를 찾아 실행하는 흐름을 잡는다 |
| "`@Controller`랑 `@RestController` 차이가 뭐예요?" | shopping-cart API가 HTML view가 아니라 JSON response를 돌려줘야 하는 상황 | view rendering과 response body 직렬화 경계를 나눈다 |
| "컨트롤러가 service를 어디까지 불러야 해요?" | endpoint method 안에서 validation, use case 호출, response mapping이 섞이는 코드 | controller는 웹 입구이고 business 흐름은 service로 넘기는 구조를 본다 |

**난이도: 🟢 Beginner**

관련 문서:

- [Controller Entity Return vs DTO Return Primer](./spring-controller-entity-return-vs-dto-return-primer.md)
- [Spring MVC 요청 생명주기 기초: `DispatcherServlet`, 필터, 인터셉터, 바인딩, 예외 처리 한 장으로 잡기](./spring-mvc-request-lifecycle-basics.md)
- [Spring `DispatcherServlet` / `HandlerInterceptor` 입문 브리지: 큰 그림부터 잡기](./spring-dispatcherservlet-handlerinterceptor-beginner-bridge.md)
- [Spring 요청 파이프라인과 Bean Container 기초: `DispatcherServlet`, 레이어 역할, Bean 등록, DI, 설정 읽기](./spring-request-pipeline-bean-container-foundations-primer.md)
- [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
- [IoC 컨테이너와 DI](./ioc-di-container.md)
- [IoC와 DI 기초: 제어 역전과 의존성 주입이 왜 필요한가](./spring-ioc-di-basics.md)
- [HTTP 메서드와 REST 멱등성 입문](../network/http-methods-rest-idempotency-basics.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring mvc 처음 배우는데, spring mvc 큰 그림, spring mvc 기초, spring mvc는 언제 쓰는지, dispatcherservlet 뭐예요, handlermapping이 뭐예요, handleradapter가 뭐예요, 요청은 누가 찾고 누가 실행하나요, 컨트롤러는 요청을 어떻게 받나요, spring mvc가 controller 메서드를 어떻게 실행해요, spring mvc에서 값은 누가 넣어줘요, pathvariable requestparam은 누가 해석해요, @controller @restcontroller 차이, @requestmapping 기초, @pathvariable @requestparam 차이, URL과 메서드를 묶어 요청을 받아서 응답을 돌려주는 클래스, 요청 받아서 응답 돌려주는 클래스를 어떻게 만들어

## 핵심 개념

Spring MVC는 웹 요청을 처리하는 프레임워크이고, 중심에는 `DispatcherServlet`이 있다. 모든 HTTP 요청이 이 서블릿 하나로 들어오고, 그 안에서 적절한 컨트롤러를 찾아 실행하고 응답을 만든다.

입문자가 자주 헷갈리는 이유는 `@Controller`와 `@RestController`의 차이, 그리고 요청이 어떤 순서로 처리되는지 보이지 않기 때문이다.

처음 배우는 기준에서는 용어를 다 외우기보다 아래 3문장만 먼저 잡으면 충분하다.

- MVC는 "웹 요청을 어느 컨트롤러 메서드로 보낼지"를 다루는 층이다.
- `DispatcherServlet`은 요청을 받아 길을 정하는 관문이다.
- 컨트롤러는 요청을 서비스로 넘기고 응답을 돌려주는 입구다.

## 한눈에 보기

```text
HTTP 요청
  -> DispatcherServlet
  -> HandlerMapping (어떤 컨트롤러?)
  -> HandlerAdapter (메서드 실행)
  -> @Controller 메서드 실행
  -> ViewResolver 또는 @ResponseBody
  -> HTTP 응답
```

| 어노테이션 | 역할 | 차이 |
|---|---|---|
| `@Controller` | 뷰 이름을 반환, 템플릿 엔진과 연결 | 기본 MVC 방식 |
| `@RestController` | `@Controller` + `@ResponseBody` | JSON 반환이 기본 |

## `handlermapping` vs `handleradapter` 먼저 구분하기

처음 배우는데 이 둘이 같이 나오면 이름이 비슷해서 둘 다 "컨트롤러를 찾는 것"처럼 느껴지기 쉽다. 큰 그림은 간단하다. `handlermapping`은 "누가 처리할지 찾는 단계"이고, `handleradapter`는 "찾아낸 대상을 실제로 실행하는 단계"다.

| 용어 | 지금 단계에서 이렇게 기억하면 된다 | 한 줄 비유 |
|---|---|---|
| `HandlerMapping` | URL, HTTP 메서드를 보고 맞는 handler를 고른다 | "담당자 찾기" |
| `HandlerAdapter` | 찾은 handler를 Spring MVC 방식에 맞게 호출한다 | "업무 방식 맞춰 실행하기" |

예를 들어 `GET /orders/10`이 들어오면 `handlermapping`이 `OrderController#getOrder`를 찾고, `handleradapter`가 `@PathVariable`, `@RequestBody` 같은 규칙까지 맞춰 메서드를 실제 호출한다.

자주 하는 혼동도 여기서 끊어 두면 좋다.

- `handlermapping`이 메서드를 직접 실행하는 것은 아니다. 어디로 보낼지만 정한다.
- `handleradapter`가 새 컨트롤러를 만드는 것도 아니다. 이미 찾은 handler를 "Spring이 아는 호출 방식"으로 실행한다.
- 처음에는 구현체 이름보다 "`찾기` 다음 `실행`" 순서만 잡아도 충분하다.

## 상세 분해

- **`DispatcherServlet`**: Spring MVC의 진입점. 모든 요청을 받아 다음 단계로 위임한다.
- **`HandlerMapping`**: 요청 URL과 메서드를 보고 어떤 컨트롤러의 어떤 메서드가 처리할지 결정한다.
- **`HandlerAdapter`**: `HandlerMapping`이 찾은 대상을 실제로 호출한다. 메서드 파라미터 바인딩, 반환값 처리 시작점도 여기와 연결된다.
- **`@RequestMapping`과 파생 어노테이션**: 경로와 HTTP 메서드를 컨트롤러 메서드에 매핑한다. `@GetMapping`, `@PostMapping` 등은 `@RequestMapping`의 단축 표기다.
- **`@PathVariable`**: URL 경로의 일부를 파라미터로 받는다. 예: `/orders/{id}`에서 `{id}` 부분.
- **`@RequestParam`**: 쿼리스트링 파라미터를 받는다. 예: `/orders?status=open`에서 `status`.
- **`@RequestBody`**: 요청 본문(주로 JSON)을 Java 객체로 변환해 받는다.

## 흔한 오해와 함정

**오해 1: `@Controller`와 `@RestController`는 기능이 같다**
`@RestController`는 모든 메서드에 `@ResponseBody`가 붙은 것과 같다. 메서드가 반환한 객체가 JSON으로 직렬화되어 응답 본문에 들어간다. `@Controller`는 기본적으로 뷰 이름을 반환한다.

**오해 2: `@PathVariable`과 `@RequestParam`은 같다**
`@PathVariable`은 URL 경로 안 `{변수}`에서, `@RequestParam`은 URL 뒤 `?key=value`에서 값을 꺼낸다.

**오해 3: 컨트롤러 메서드가 직접 DB를 건드려도 된다**
컨트롤러는 요청을 받고 응답을 반환하는 역할이다. 비즈니스 로직은 서비스 레이어, DB 접근은 리포지토리 레이어에 두는 것이 관례다.

**오해 4: `@RestController`면 엔티티를 그대로 반환해도 괜찮다**
JSON 직렬화 단계에서 lazy loading이 터질 수 있으므로, 초급자 기본값은 service가 DTO를 만들어 controller가 DTO를 반환하는 흐름이다. 자세한 이유는 [Controller Entity Return vs DTO Return Primer](./spring-controller-entity-return-vs-dto-return-primer.md)를 보면 된다.

## 실무에서 쓰는 모습

REST API 컨트롤러의 가장 기본 형태다.

```java
@RestController
@RequestMapping("/orders")
public class OrderController {

    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @GetMapping("/{id}")
    public OrderResponse getOrder(@PathVariable Long id) {
        return orderService.findOrder(id);
    }

    @PostMapping
    public OrderResponse createOrder(@RequestBody OrderRequest request) {
        return orderService.placeOrder(request);
    }
}

@Service
public class OrderService {

    public OrderResponse findOrder(Long id) {
        return new OrderResponse(id, "PAID");
    }

    public OrderResponse placeOrder(OrderRequest request) {
        return new OrderResponse(1L, "CREATED");
    }
}
```

`OrderService`를 생성자 주입받아 사용하는 것이 Spring 관례다. 컨트롤러는 요청 파라미터를 꺼내고 서비스를 호출하고 응답을 반환하는 역할만 한다.

## 5분 요청 walkthrough

처음 읽을 때는 "`GET`은 조회", "`POST`는 생성", "컨트롤러는 서비스에 전달"만 붙여도 충분하다.

| 요청 | HTTP 메서드 의도 | 컨트롤러 매핑 | 서비스 호출 |
|---|---|---|---|
| `GET /orders/10` | 기존 주문 10번을 읽고 싶다 | `@GetMapping("/{id}")` + `@PathVariable Long id` | `orderService.findOrder(10L)` |
| `POST /orders` + JSON body | 새 주문을 만들고 싶다 | `@PostMapping` + `@RequestBody OrderRequest` | `orderService.placeOrder(request)` |

한 요청만 따라가 보면 흐름은 같다.

1. 브라우저나 클라이언트가 `GET /orders/10` 또는 `POST /orders`를 보낸다.
2. `DispatcherServlet`이 HTTP 메서드와 경로를 보고 맞는 컨트롤러 메서드를 찾는다.
3. `GET`이면 경로의 `10`을 `id`에 넣고, `POST`면 JSON 본문을 `OrderRequest`로 바꿔 넣는다.
4. 컨트롤러는 직접 `new OrderService()`를 하지 않고, 이미 주입된 `orderService`를 호출한다.
5. 서비스가 결과를 돌려주면 `@RestController`가 그 객체를 JSON 응답으로 보낸다.

자주 하는 혼동도 여기서 같이 정리하면 안전하다.

- `GET /orders/10`과 `POST /orders`는 경로만이 아니라 HTTP 메서드까지 같이 봐야 다른 메서드로 매핑된다.
- `orderService`는 요청마다 새로 만드는 객체가 아니라, Spring이 시작할 때 Bean으로 준비해 둔 의존성이다.
- 컨트롤러의 역할은 "HTTP를 서비스가 이해할 형태로 바꾸는 입구"이지, 비즈니스 규칙을 길게 담는 곳이 아니다.

## 첫 읽기 연결 포인트 (HTTP -> MVC -> DI)

처음에는 아래 3문장을 같이 묶어 기억하면 된다.

| 층위 | 한 줄 질문 | 이 문서에서 보는 것 |
|---|---|---|
| HTTP | "이 요청은 무슨 의도인가?" | `GET /orders/{id}`, `POST /orders` |
| MVC | "누가 이 요청을 받는가?" | `@GetMapping`, `@PostMapping`, `DispatcherServlet` |
| DI | "컨트롤러 안 `OrderService`는 누가 넣었는가?" | 생성자 주입, Bean 컨테이너 |

즉 컨트롤러 기초는 "HTTP 메서드 의미"와 "DI wiring" 사이를 연결하는 중간 다리다.

## 더 깊이 가려면

- `HandlerMapping`, `HandlerAdapter`, 예외 처리 흐름 전체는 [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)에서 더 자세히 다룬다.
- 컨트롤러가 Bean으로 등록되는 원리는 [IoC 컨테이너와 DI](./ioc-di-container.md)와 연결된다.
- HTTP 메서드(GET/POST/PUT/DELETE)와 REST 설계 원칙은 [HTTP 메서드, REST, 멱등성](../network/http-methods-rest-idempotency.md)에서 먼저 잡으면 좋다.
- HTTP 메서드 감각을 먼저 잡고 싶다면 [HTTP 메서드와 REST 멱등성 입문](../network/http-methods-rest-idempotency-basics.md)부터 읽는다.
- 컨트롤러의 `service` 주입이 왜 필요한지 바로 붙이려면 [IoC와 DI 기초: 제어 역전과 의존성 주입이 왜 필요한가](./spring-ioc-di-basics.md)로 이어 읽는다.
- 요청 흐름과 객체 준비를 한 번에 묶으려면 [Spring 요청 파이프라인과 Bean Container 기초: `DispatcherServlet`, 레이어 역할, Bean 등록, DI, 설정 읽기](./spring-request-pipeline-bean-container-foundations-primer.md)로 돌아온다.
- `DispatcherServlet`과 `HandlerInterceptor`가 같이 나와서 처음부터 용어가 무겁게 느껴지면 [Spring `DispatcherServlet` / `HandlerInterceptor` 입문 브리지: 큰 그림부터 잡기](./spring-dispatcherservlet-handlerinterceptor-beginner-bridge.md)로 먼저 우회한다.
- 필터, 인터셉터, 바인딩, 예외 처리까지 한 장으로 연결해서 보고 싶다면 [Spring MVC 요청 생명주기 기초: `DispatcherServlet`, 필터, 인터셉터, 바인딩, 예외 처리 한 장으로 잡기](./spring-mvc-request-lifecycle-basics.md)로 이어간다.

## 면접/시니어 질문 미리보기

> Q: `@Controller`와 `@RestController`의 차이는 무엇인가?
> 의도: 어노테이션 의미 이해 확인
> 핵심: `@RestController`는 `@ResponseBody`가 기본 포함되어 반환 객체가 JSON으로 직렬화된다.

> Q: `DispatcherServlet`은 어떤 역할을 하는가?
> 의도: MVC 요청 흐름 이해 확인
> 핵심: 모든 요청의 진입점으로 HandlerMapping, HandlerAdapter, ViewResolver를 조율한다.

> Q: `@PathVariable`과 `@RequestParam`을 어떻게 구분해서 쓰는가?
> 의도: URL 파라미터 구분 확인
> 핵심: 경로 변수(`/orders/{id}`)는 PathVariable, 쿼리 파라미터(`?status=open`)는 RequestParam.

## 한 줄 정리

Spring MVC 컨트롤러는 `DispatcherServlet`이 찾아 실행하는 요청 처리 진입점이고, `@RestController`는 반환 객체를 JSON으로 바로 응답한다.
