# Spring `DispatcherServlet` / `HandlerInterceptor` 입문 브리지: 큰 그림부터 잡기

> 한 줄 요약: 처음 배우는데 `DispatcherServlet`, `HandlerInterceptor`가 같이 나오면 "요청을 받는 관문"과 "컨트롤러 전후에 끼어드는 도우미"만 먼저 구분하고, MVC 생명주기 deep dive는 나중에 봐도 된다.
>
> 문서 역할: 이 문서는 spring 카테고리 안에서 `DispatcherServlet`/`HandlerInterceptor` intro 질문을 **MVC 기초로 되돌리는 beginner bridge primer**를 담당한다.

**난이도: 🟢 Beginner**

관련 문서:

- [Spring MVC 컨트롤러 기초: 요청이 컨트롤러까지 오는 흐름](./spring-mvc-controller-basics.md)
- [Spring 요청 파이프라인과 Bean Container 기초: `DispatcherServlet`, 레이어 역할, Bean 등록, DI, 설정 읽기](./spring-request-pipeline-bean-container-foundations-primer.md)
- [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
- [Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries](./spring-mvc-filter-interceptor-controlleradvice-boundaries.md)
- [Spring Security Filter Chain Ordering](./spring-security-filter-chain-ordering.md)
- [HTTP 메서드와 REST 멱등성 입문](../network/http-methods-rest-idempotency-basics.md)
- [spring 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: dispatcherservlet 처음 배우는데, handlerinterceptor 처음 배우는데, spring mvc 처음 배우는데, spring mvc 큰 그림, spring mvc 기초, spring mvc 생명주기 전에 볼 문서, handlermapping handleradapter 차이, mvc basics before lifecycle, 인터셉터 뭐예요, dispatcherservlet 뭐예요, mvc primer before deep dive, beginner first-hit mvc primer, dispatcherservlet 언제 쓰는지, handlerinterceptor 언제 쓰는지

## 먼저 큰 그림

처음에는 이렇게만 잡으면 된다.

- `DispatcherServlet`: 들어온 HTTP 요청을 받아 "어느 컨트롤러로 보낼지" 정하는 MVC의 관문
- `HandlerInterceptor`: 컨트롤러를 실행하기 전후에 공통 작업을 넣는 도우미
- `HandlerMapping` / `HandlerAdapter`: 관문 안에서 각각 "누구를 찾는지"와 "어떻게 실행하는지"를 나누는 내부 단계

즉 둘은 경쟁 관계가 아니라 **같은 요청 흐름 안에서 위치가 다른 구성요소**다.

```text
HTTP 요청
  -> DispatcherServlet
  -> HandlerMapping
  -> HandlerInterceptor preHandle
  -> Controller
  -> HandlerInterceptor postHandle / afterCompletion
  -> HTTP 응답
```

여기서 초급자 기준 핵심은 하나다.

**`DispatcherServlet`은 길을 정하고, `HandlerInterceptor`는 그 길 위에서 공통 작업을 덧붙인다.**

처음 질문이 "Spring MVC가 뭐예요?" 수준이라면 이 문서만 오래 붙잡기보다 [Spring MVC 컨트롤러 기초](./spring-mvc-controller-basics.md)로 먼저 가서 controller 중심 흐름을 보고 돌아오는 편이 더 안전하다.

## 용어를 이렇게 나눠 기억하면 덜 헷갈린다

| 용어 | 지금 단계에서 기억할 역할 | 처음부터 깊게 보지 않아도 되는 것 |
|---|---|---|
| `DispatcherServlet` | 모든 웹 요청의 진입점 | 내부 전략 객체 전체 이름 |
| `HandlerInterceptor` | 컨트롤러 전후 공통 처리 | async redispatch, 예외 후처리 세부 순서 |
| `Controller` | 실제 요청을 처리하는 메서드 | resolver chain 세부 구현 |

## 이런 질문이 나오면 어디로 먼저 가면 되는가

| 지금 든 질문 | 먼저 볼 문서 | 이유 |
|---|---|---|
| "`DispatcherServlet`이 뭐예요?" | [Spring MVC 컨트롤러 기초](./spring-mvc-controller-basics.md) | 요청이 컨트롤러까지 가는 기본 흐름을 가장 짧게 잡는다 |
| "`HandlerMapping`이랑 `HandlerAdapter`가 왜 둘 다 필요한가요?" | [Spring MVC 컨트롤러 기초](./spring-mvc-controller-basics.md) | beginner 기준으로 "찾기"와 "실행"을 먼저 분리해 준다 |
| "Spring이 요청을 어떻게 받는지 큰 그림이 필요해요" | [Spring 요청 파이프라인과 Bean Container 기초](./spring-request-pipeline-bean-container-foundations-primer.md) | MVC와 DI를 한 장으로 묶어 준다 |
| "`HandlerInterceptor`는 언제 쓰는지 모르겠어요" | [Spring MVC 컨트롤러 기초](./spring-mvc-controller-basics.md) 먼저, 그다음 [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md) | 먼저 컨트롤러 흐름을 알아야 인터셉터 위치가 보인다 |
| "필터랑 인터셉터 차이는요?" | [Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries](./spring-mvc-filter-interceptor-controlleradvice-boundaries.md) | 책임 경계 비교가 핵심인 질문이다 |

## 가장 흔한 오해 3개

- `DispatcherServlet`이 컨트롤러 객체를 매번 새로 만든다고 생각하기 쉽다.
  실제로는 보통 컨테이너가 미리 만든 Bean을 찾아 연결한다.
- `HandlerInterceptor`가 보안의 중심이라고 생각하기 쉽다.
  인증/인가는 대개 Security filter chain이 먼저 처리하고, 인터셉터는 MVC 전후 공통 작업에 더 가깝다.
- `DispatcherServlet`과 `HandlerInterceptor`를 이해하려면 처음부터 lifecycle deep dive를 끝까지 읽어야 한다고 느끼기 쉽다.
  초반에는 "진입점"과 "전후 훅"만 구분해도 충분하다.

## 아주 짧은 예시

```java
@RestController
@RequestMapping("/orders")
public class OrderController {

    @GetMapping("/{id}")
    public OrderResponse find(@PathVariable Long id) {
        return new OrderResponse(id);
    }
}
```

```java
public class LoggingInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        request.setAttribute("startedAt", System.currentTimeMillis());
        return true;
    }
}
```

이 예시에서:

- `DispatcherServlet`은 `/orders/1` 요청을 `OrderController`로 보낸다.
- `LoggingInterceptor`는 그 직전/직후에 로깅 같은 공통 작업을 넣는다.
- 비즈니스 로직 자체는 여전히 컨트롤러와 서비스가 맡는다.

## 다음 단계

- 큰 그림이 아직 흐리면 [Spring MVC 컨트롤러 기초](./spring-mvc-controller-basics.md)로 먼저 간다.
- MVC와 DI를 한 번에 묶고 싶으면 [Spring 요청 파이프라인과 Bean Container 기초](./spring-request-pipeline-bean-container-foundations-primer.md)로 이어간다.
- lifecycle, resolver, 예외 처리까지 보고 싶을 때만 [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)로 내려간다.
- 필터/인터셉터/예외 advice 경계가 궁금할 때만 [Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries](./spring-mvc-filter-interceptor-controlleradvice-boundaries.md)로 확장한다.

## 한 줄 정리

`DispatcherServlet`은 요청 진입 관문이고 `HandlerInterceptor`는 컨트롤러 전후 공통 처리 훅이므로, 처음에는 MVC 기초 문서에서 위치를 먼저 잡고 그다음 lifecycle deep dive로 내려가면 된다.
