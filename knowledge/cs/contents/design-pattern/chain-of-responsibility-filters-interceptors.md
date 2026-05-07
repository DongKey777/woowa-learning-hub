---
schema_version: 3
title: Chain of Responsibility: Filters and Interceptors
concept_id: design-pattern/chain-of-responsibility-filters-interceptors
canonical: true
category: design-pattern
difficulty: advanced
doc_role: deep_dive
level: advanced
language: ko
source_priority: 84
mission_ids: []
review_feedback_tags:
- chain-of-responsibility
- servlet-filter-chain
- handler-interceptor-chain
aliases:
- chain of responsibility filter interceptor
- servlet filter chain
- handlerinterceptor chain
- request short circuit
- authentication authorization logging pipeline
- filter vs interceptor beginner
- spring filter interceptor chain
- onceperrequestfilter chain wrapper
- request pipeline pattern
- 책임 연쇄 패턴
symptoms:
- 인증, 인가, 로깅, 검증을 하나의 service method에 몰아넣어 실패 시 어느 단계에서 막혔는지 추적하기 어렵다
- Servlet Filter와 Spring HandlerInterceptor와 OncePerRequestFilter를 같은 레벨의 체인으로 혼동한다
- 요청을 현재 흐름에서 막아야 하는 책임 연쇄 문제와 이미 일어난 일을 알리는 이벤트 문제를 구분하지 못한다
intents:
- deep_dive
- troubleshooting
- comparison
prerequisites:
- software-engineering/servlet-filter-vs-mvc-interceptor-beginner-bridge
- design-pattern/template-method-vs-filter-interceptor-chain
- design-pattern/pattern-selection
next_docs:
- design-pattern/pipeline-vs-chain-of-responsibility
- design-pattern/middleware-pattern-language
- design-pattern/observer-pubsub-application-events
linked_paths:
- contents/software-engineering/servlet-filter-vs-mvc-interceptor-beginner-bridge.md
- contents/design-pattern/template-method-vs-filter-interceptor-chain.md
- contents/design-pattern/template-method-framework-lifecycle-examples.md
- contents/design-pattern/facade-vs-adapter-vs-proxy.md
- contents/design-pattern/observer-pubsub-application-events.md
- contents/design-pattern/pattern-selection.md
- contents/design-pattern/anti-pattern.md
confusable_with:
- design-pattern/pipeline-vs-chain-of-responsibility
- design-pattern/middleware-pattern-language
- design-pattern/observer-pubsub-application-events
- design-pattern/template-method-vs-filter-interceptor-chain
forbidden_neighbors: []
expected_queries:
- Chain of Responsibility는 request를 여러 handler에 순서대로 넘기며 인증 검증 로깅을 어떻게 분리해?
- Servlet Filter와 HandlerInterceptor는 요청 전역과 controller 전후 시점에서 어떻게 달라?
- OncePerRequestFilter는 별도 체인이 아니라 Filter 구현용 Template Method base class라는 말은 무슨 뜻이야?
- 책임 연쇄와 이벤트는 현재 요청을 막는 흐름 제어와 이미 일어난 일을 알리는 통지 관점에서 어떻게 달라?
- filter chain이 길어질 때 어느 단계에서 short-circuit 되었는지 tracing이 필요한 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 Chain of Responsibility filters/interceptors deep dive로, request를
  인증, 인가, 검증, 로깅 같은 handler chain에 순서대로 통과시키며 각 단계가 next로 넘기거나
  short-circuit할 수 있는 구조를 설명하고, Servlet Filter, Spring HandlerInterceptor,
  OncePerRequestFilter, event notification과의 차이를 다룬다.
---
# 책임 연쇄 패턴: 필터와 인터셉터로 요청 파이프라인 만들기

> 한 줄 요약: 책임 연쇄 패턴은 요청을 여러 처리자에 통과시키며, 인증·로깅·검증·차단 같은 공통 관심사를 파이프라인으로 분리한다.

처음 읽는데 `Filter`와 `HandlerInterceptor`가 한 덩어리로 섞인다면, 이 primer에 바로 들어오기보다 [Servlet Filter vs MVC Interceptor Beginner Bridge](../software-engineering/servlet-filter-vs-mvc-interceptor-beginner-bridge.md)에서 "`request` 입구를 다루는가, `controller` 주변을 다루는가"만 먼저 나누고 돌아오면 덜 헷갈린다.

**난이도: 🔴 Advanced**

관련 문서:

- [Servlet Filter vs MVC Interceptor Beginner Bridge](../software-engineering/servlet-filter-vs-mvc-interceptor-beginner-bridge.md)
- [Spring `Filter`, `HandlerInterceptor`, `OncePerRequestFilter`: 템플릿 메소드 vs 책임 연쇄](./template-method-vs-filter-interceptor-chain.md)
- [프레임워크 안의 템플릿 메소드: Servlet, Filter, Test Lifecycle](./template-method-framework-lifecycle-examples.md)
- [퍼사드 vs 어댑터 vs 프록시](./facade-vs-adapter-vs-proxy.md)
- [옵저버, Pub/Sub, ApplicationEvent](./observer-pubsub-application-events.md)
- [실전 패턴 선택 가이드](./pattern-selection.md)
- [안티 패턴](./anti-pattern.md)

retrieval-anchor-keywords: chain of responsibility filter interceptor, servlet filter chain, handlerinterceptor chain, request short circuit, authentication authorization logging pipeline, filter vs interceptor beginner, servlet filter vs mvc interceptor, spring filter interceptor chain, onceperrequestfilter chain wrapper, request pipeline pattern, 처음 배우는데 책임 연쇄, 책임 연쇄 패턴 뭐예요

---

## 핵심 개념

책임 연쇄 패턴(Chain of Responsibility)은 **요청을 여러 처리자에게 순서대로 넘기면서 각 처리자가 자신의 책임만 수행하는 구조**다.
핵심은 "하나의 거대한 서비스 메서드"를 여러 단계로 쪼개는 것이다.

backend에서 가장 자주 보이는 형태는 다음과 같다.

- Servlet `Filter`
- Spring MVC `HandlerInterceptor`
- 보안 필터 체인
- 검증 파이프라인
- 감사 로그/트레이싱 단계

### Retrieval Anchors

- `Spring Filter chain`
- `HandlerInterceptor preHandle postHandle`
- `OncePerRequestFilter template method wrapper`
- `filter vs interceptor vs onceperrequestfilter`
- `authentication authorization logging`
- `request pipeline`
- `cross-cutting concern`

---

## 깊이 들어가기

### 1. 각 처리자는 다음 단계로 넘길지 결정한다

책임 연쇄의 핵심은 단순한 "호출 목록"이 아니라 **제어권 이동**이다.

- 처리하고 넘긴다
- 처리하고 중단한다
- 처리만 하고 응답을 끝낸다

이 차이 때문에 인증 실패, rate limit 초과, 파라미터 오류 같은 경우에 잘 맞는다.

### 2. Filter와 Interceptor는 같은 게 아니다

둘 다 요청 파이프라인에 끼지만 시점이 다르다.

| 구분 | Filter | Interceptor |
|---|---|---|
| 위치 | 서블릿 앞단 | 스프링 핸들러 앞뒤 |
| 대상 | HTTP 요청 전반 | 컨트롤러 실행 |
| 사용 예 | 인코딩, 인증, 로깅 | 인증 보강, 권한 확인, 응답 후처리 |
| 제어 | `doFilter` | `preHandle`, `postHandle`, `afterCompletion` |

Filter는 더 바깥쪽, Interceptor는 더 안쪽이라고 보면 된다.

자주 섞이는 이름 하나를 더 분리하면, `OncePerRequestFilter`는 `Filter`와 같은 레벨의 별도 체인이 아니다.
filter chain 안에 들어가는 **필터 구현용 base class**이고, 그 내부 확장 방식은 [템플릿 메소드](./template-method-vs-filter-interceptor-chain.md)에 더 가깝다.

### 3. 실패를 어디서 끊을지가 중요하다

체인에서 중요한 것은 "성공하면 다음으로"가 아니라 **실패 시 어디서 멈출 것인가**다.

- 인증 실패: 앞단에서 즉시 중단
- 입력 검증 실패: 컨트롤러 진입 전에 중단
- 감사 로그: 실패해도 기록은 남김

이 선택이 곧 운영 품질이다.

---

## 실전 시나리오

### 시나리오 1: 인증과 인가

JWT 파싱, 토큰 검증, 사용자 식별, 권한 검사를 각각 분리하면 유지보수가 쉬워진다.

### 시나리오 2: API 보호 계층

rate limit, IP 차단, 헤더 정규화, trace id 주입은 체인으로 넣기 좋다.

### 시나리오 3: 요청 관측성

로깅과 메트릭 수집은 요청 전후에 반복되므로 체인 구조가 잘 맞는다.

---

## 직접 구현 예시

체인을 직접 만들면 "다음 단계로 넘길지 말지"가 어디서 결정되는지 바로 보인다.

```java
public interface RequestHandler {
    void setNext(RequestHandler next);
    void handle(RequestContext context);
}

public abstract class AbstractRequestHandler implements RequestHandler {
    private RequestHandler next;

    @Override
    public void setNext(RequestHandler next) {
        this.next = next;
    }

    protected void next(RequestContext context) {
        if (next != null) {
            next.handle(context);
        }
    }
}

public class AuthenticationHandler extends AbstractRequestHandler {
    @Override
    public void handle(RequestContext context) {
        if (!context.hasValidToken()) {
            throw new UnauthorizedException();
        }
        next(context);
    }
}

public class LoggingHandler extends AbstractRequestHandler {
    @Override
    public void handle(RequestContext context) {
        context.logRequest();
        next(context);
    }
}
```

## Spring Filter 예시

Servlet `Filter`는 요청을 더 바깥에서 보고, 필요하면 다음 단계로 넘기지 않고 바로 끊을 수 있다.

```java
@Component
public class TraceIdFilter extends OncePerRequestFilter {
    @Override
    protected void doFilterInternal(
        HttpServletRequest request,
        HttpServletResponse response,
        FilterChain filterChain
    ) throws ServletException, IOException {
        request.setAttribute("traceId", UUID.randomUUID().toString());
        filterChain.doFilter(request, response);
    }
}
```

## Spring Interceptor 예시

`HandlerInterceptor`는 컨트롤러 실행 전후를 다루고, `preHandle()` 반환값으로 계속/중단을 정한다.

```java
@Component
public class AuthInterceptor implements HandlerInterceptor {
    @Override
    public boolean preHandle(
        HttpServletRequest request,
        HttpServletResponse response,
        Object handler
    ) throws Exception {
        if (!isAuthorized(request)) {
            response.sendError(HttpStatus.UNAUTHORIZED.value());
            return false;
        }
        return true;
    }
}
```

Filter는 요청 전체를, Interceptor는 컨트롤러 실행 전후를 다루기 좋다.

---

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 한 메서드에 몰기 | 읽기는 짧다 | 공통 관심사가 섞인다 | 규칙이 매우 적을 때 |
| 책임 연쇄 | 단계별 책임이 분리된다 | 흐름 추적이 어려워질 수 있다 | 인증, 로깅, 검증이 반복될 때 |
| 이벤트 발행 | 결합도가 낮다 | 순서와 실패 처리가 복잡하다 | 후속 작업이 비핵심일 때 |

판단 기준은 다음과 같다.

- 요청을 **막아야** 하면 책임 연쇄가 맞다
- 요청 이후의 **부가 작업**이면 이벤트가 맞다
- 흐름 자체를 **숨기고 싶다**면 퍼사드를 먼저 본다

---

## 꼬리질문

> Q: 책임 연쇄 패턴과 이벤트는 어떻게 다른가요?
> 의도: 흐름 제어와 느슨한 통지를 구분하는지 확인한다.
> 핵심: 책임 연쇄는 현재 요청을 처리하는 흐름이고, 이벤트는 이미 일어난 일을 알리는 흐름이다.

> Q: Filter와 Interceptor를 섞어 써도 되나요?
> 의도: 각 계층의 책임 경계를 아는지 확인한다.
> 핵심: 가능하지만, 서블릿 전역 정책은 Filter, MVC 전후 처리는 Interceptor가 보통 더 적합하다.

> Q: 체인이 길어지면 무엇이 문제인가요?
> 의도: 구조가 길수록 추적성과 디버깅이 어려워진다는 점을 보는지 확인한다.
> 핵심: 어떤 단계에서 중단됐는지 추적하는 장치가 필요하다.

## 한 줄 정리

책임 연쇄 패턴은 요청을 여러 처리자에게 순서대로 넘겨 인증, 검증, 로깅 같은 공통 관심사를 단계별로 분리하는 패턴이다.
