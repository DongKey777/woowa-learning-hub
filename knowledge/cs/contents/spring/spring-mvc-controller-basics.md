# Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름

> 한 줄 요약: HTTP 요청은 `DispatcherServlet`이 받아 `HandlerMapping`으로 컨트롤러를 찾고, `HandlerAdapter`로 메서드를 실행한 뒤 응답을 돌려주는 흐름이다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
- [IoC 컨테이너와 DI](./ioc-di-container.md)
- [HTTP 메서드, REST, 멱등성](../network/http-methods-rest-idempotency.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: spring mvc controller basics, dispatcherservlet 흐름, spring mvc 요청 흐름 beginner, @controller @restcontroller 차이, @requestmapping 기초, @getmapping @postmapping 입문, spring 컨트롤러가 뭐예요, spring mvc request flow beginner, @requestbody @responsebody 기초, @pathvariable @requestparam 차이, spring rest controller beginner, mvc request dispatch

## 핵심 개념

Spring MVC는 웹 요청을 처리하는 프레임워크이고, 중심에는 `DispatcherServlet`이 있다. 모든 HTTP 요청이 이 서블릿 하나로 들어오고, 그 안에서 적절한 컨트롤러를 찾아 실행하고 응답을 만든다.

입문자가 자주 헷갈리는 이유는 `@Controller`와 `@RestController`의 차이, 그리고 요청이 어떤 순서로 처리되는지 보이지 않기 때문이다.

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

## 상세 분해

- **`DispatcherServlet`**: Spring MVC의 진입점. 모든 요청을 받아 다음 단계로 위임한다.
- **`HandlerMapping`**: 요청 URL과 메서드를 보고 어떤 컨트롤러의 어떤 메서드가 처리할지 결정한다.
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
```

`OrderService`를 생성자 주입받아 사용하는 것이 Spring 관례다. 컨트롤러는 요청 파라미터를 꺼내고 서비스를 호출하고 응답을 반환하는 역할만 한다.

## 더 깊이 가려면

- `HandlerMapping`, `HandlerAdapter`, 예외 처리 흐름 전체는 [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)에서 더 자세히 다룬다.
- 컨트롤러가 Bean으로 등록되는 원리는 [IoC 컨테이너와 DI](./ioc-di-container.md)와 연결된다.
- HTTP 메서드(GET/POST/PUT/DELETE)와 REST 설계 원칙은 [HTTP 메서드, REST, 멱등성](../network/http-methods-rest-idempotency.md)에서 먼저 잡으면 좋다.

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
