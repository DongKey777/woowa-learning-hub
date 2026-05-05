# Request Dispatch Naming: `Router`, `Dispatcher`, `HandlerMapping`이 `Selector`나 `Factory`보다 맞을 때

> 한 줄 요약: request dispatch 코드는 "요청을 어디로 보낼까, 어떤 handler가 맞을까, 그 handoff 전체를 누가 조율할까"를 드러내는 이름이 먼저다. 그래서 보통 `Router`, `HandlerMapping`, `Dispatcher`가 맞고, handler 안쪽의 정책 선택이나 새 객체 생성에만 `Selector`, `Factory`를 쓴다.

**난이도: 🟢 Beginner**


관련 문서:

- [카테고리 README](./README.md)
- [우아코스 백엔드 CS 로드맵](../../JUNIOR-BACKEND-ROADMAP.md)
- [연결 입문 문서](../software-engineering/oop-design-basics.md)

> 관련 문서:
> - [Map-backed 클래스 네이밍 체크리스트: `Selector`, `Resolver`, `Registry`, `Factory`](./map-backed-selector-resolver-registry-factory-naming-checklist.md)
> - [Registry Primer: lookup table, resolver, router, service locator를 처음 구분하기](./registry-primer-lookup-table-resolver-router-service-locator.md)
> - [Bean Name vs Domain Key Lookup: Spring handler map을 domain registry로 감싸기](./bean-name-vs-domain-key-lookup.md)
> - [책임 연쇄 패턴: 필터와 인터셉터로 요청 파이프라인 만들기](./chain-of-responsibility-filters-interceptors.md)
> - [Spring `Filter`, `HandlerInterceptor`, `OncePerRequestFilter`: 템플릿 메소드 vs 책임 연쇄](./template-method-vs-filter-interceptor-chain.md)
> - [디자인 패턴 카테고리 인덱스](./README.md)

retrieval-anchor-keywords: request dispatch naming, router vs selector naming, dispatcher vs selector naming, handler mapping vs selector, handler mapping vs factory, router dispatcher handlermapping beginner, request router naming beginner, request dispatcher naming beginner, spring dispatcher servlet handler mapping naming, dispatcherservlet handlermapping routerfunction naming, handler selector factory smell, request routing vs strategy selector, handler lookup not factory, request dispatch not factory, controller dispatch naming

---

## 먼저 머릿속 그림

request dispatch 코드는 보통 아래 세 질문으로 나누면 쉽다.

- **Router**: "이 요청을 어느 길, 어느 영역으로 보낼까?"
- **HandlerMapping**: "이 요청 조건에 맞는 구체 handler는 무엇일까?"
- **Dispatcher**: "찾고, 넘기고, 실행하고, 응답까지 전체 handoff를 누가 조율할까?"

그리고 이 셋 바깥에 다른 질문이 있다.

- **Selector**: "이미 들어온 handler 안에서 어떤 정책/전략을 고를까?"
- **Factory**: "지금 새 command, client, session 같은 객체를 만들까?"

짧게 외우면 된다.

**길을 정하면 `Router`, 매칭표를 찾으면 `HandlerMapping`, 전체 전달을 조율하면 `Dispatcher`다.
정책을 고르면 `Selector`, 새로 만들면 `Factory`다.**

---

## 30초 이름 선택표

| 코드가 실제로 답하는 질문 | 더 자연스러운 이름 | `Selector`/`Factory`가 덜 맞는 이유 |
|---|---|---|
| 이 요청을 어느 path group, controller family, queue로 보낼까 | `Router` | 정책 선택보다 request flow 분기가 중심이다 |
| method/path/header 조건에 맞는 handler metadata는 무엇일까 | `HandlerMapping` | 새 객체 생성이 아니라 request-to-handler matching이다 |
| mapping 조회, handler 호출, 예외 처리, 응답 작성을 누가 묶을까 | `Dispatcher` | "고른다"보다 handoff orchestration이 중심이다 |
| 이미 선택된 handler 안에서 할인/검증/결제 정책을 무엇으로 할까 | `Selector` | 이제 request route는 정해졌고 business policy만 남았다 |
| 요청별 command, adapter, client를 새로 조립할까 | `Factory` | 이때는 실제 생성 책임이 public API에 드러난다 |

핵심 기준은 자료구조가 아니다.
`Map<RequestPattern, Handler>`를 써도 바깥 질문이 "어느 handler가 맞나?"면 `HandlerMapping`이 더 정확하다.

---

## 같은 "고른다"처럼 보여도 층이 다르다

아래처럼 한 요청 안에서도 이름이 층마다 달라진다.

```text
HTTP request
  -> ApiRouter.route(request)
  -> OrderHandlerMapping.getHandler(request)
  -> RequestDispatcher.dispatch(request)
  -> DiscountPolicySelector.select(order)
  -> PaymentCommandFactory.create(request)
```

- `ApiRouter`: 요청을 어느 영역으로 보낼지 정한다
- `OrderHandlerMapping`: 그 영역 안에서 어떤 handler가 맞는지 찾는다
- `RequestDispatcher`: lookup, invoke, response handoff를 묶는다
- `DiscountPolicySelector`: handler 안쪽에서 비즈니스 정책을 고른다
- `PaymentCommandFactory`: 요청별 새 객체를 만든다

즉 "무언가를 고른다"는 공통점만 보고 전부 `Selector`라고 부르면 request flow와 business rule이 섞인다.

---

## 예시: `RequestHandlerSelectorFactory`보다 왜 이름을 쪼개는가

처음에는 아래처럼 이름이 뭉치기 쉽다.

```java
public final class RequestHandlerSelectorFactory {
    private final Map<RequestPattern, HandlerExecution> handlers;

    public HandlerExecution create(HttpRequest request) {
        return handlers.get(RequestPattern.from(request));
    }
}
```

이 클래스는 실제로는 두 약속 모두 어긴다.

- `Factory`인데 새 객체를 만들지 않는다
- `Selector`라고 보기에도 request dispatch boundary 쪽 질문이 더 크다

역할을 나누면 이름이 바로 또렷해진다.

```java
public interface HandlerMapping {
    HandlerExecution getHandler(HttpRequest request);
}

public final class RequestDispatcher {
    private final HandlerMapping handlerMapping;
    private final HandlerAdapter handlerAdapter;

    public HttpResponse dispatch(HttpRequest request) {
        HandlerExecution execution = handlerMapping.getHandler(request);
        return handlerAdapter.handle(request, execution);
    }
}
```

여기서 읽는 사람은 바로 이해할 수 있다.

- `HandlerMapping`: request 조건으로 기존 handler execution을 찾는다
- `RequestDispatcher`: 찾은 결과를 실제 실행 흐름에 태운다

정말 새 객체가 필요하면 그 다음에 별도 factory를 둔다.

```java
PaymentCommand command = paymentCommandFactory.create(request);
```

이제 `Factory`도 생성 책임을 정확히 말한다.

---

## `Router`와 `HandlerMapping`은 어떻게 고르나

둘 다 "어디로 보낼까"처럼 보여도 초점이 다르다.

| 이름 | 초점 | beginner 기본 예시 |
|---|---|---|
| `Router` | 큰 길 분기, 다음 lane 결정 | `/admin/**`는 admin flow, `/payments/**`는 payment flow |
| `HandlerMapping` | 구체 handler match lookup | `GET /orders/{id}`는 `OrderController#show` |

한 문장 규칙으로 자르면 이렇다.

- **큰 길을 갈라 주면 `Router`**
- **매칭 규칙표에서 담당자를 찾으면 `HandlerMapping`**

그래서 Spring MVC처럼 중앙 dispatch가 있는 구조에서는 `DispatcherServlet` + `HandlerMapping` 조합이 자연스럽고, 함수형 route DSL이나 gateway 쪽에서는 `Router`라는 이름이 더 자주 맞는다.

---

## 흔한 혼동

- **"어차피 handler 하나를 고르니까 `Selector` 아닌가요?"**
  - request dispatch는 "비즈니스 정책 선택"보다 "요청을 어느 처리 흐름에 태울까"가 중심이다. route와 policy를 같은 이름으로 부르면 읽는 사람이 경계를 놓친다.
- **"`Map<RequestPattern, Handler>`면 `Registry` 아닌가요?"**
  - 구현 안쪽에서는 registry-like lookup일 수 있다. 하지만 public 책임이 request matching이면 `HandlerMapping`이나 `Router`가 더 설명력이 높다.
- **"`Dispatcher`도 결국 handler를 고르는데 왜 `Selector`가 아니죠?"**
  - `Dispatcher`는 고르기만 하지 않는다. 호출, 예외 처리, 응답 작성, 다음 단계 handoff까지 함께 조율한다.
- **"`Factory`처럼 handler를 돌려주는데 왜 안 맞나요?"**
  - 기존 handler나 metadata를 찾아 반환할 뿐이면 생성 약속이 없다. 새 객체를 조립할 때만 `Factory`가 맞다.
- **"`Router`와 `Dispatcher`가 같이 있으면 중복 아닌가요?"**
  - 아니다. `Router`는 방향을 정하고, `Dispatcher`는 그 방향으로 실제 전달 절차를 실행한다. 하나의 객체가 둘 다 할 수도 있지만, 이름은 public 책임이 더 큰 쪽을 따라간다.

## 한 줄 정리

request dispatch 코드에서 이름은 "무엇을 선택하나"보다 **요청 흐름의 어느 책임을 맡나**를 먼저 보여 줘야 한다. 그래서 길 분기면 `Router`, request-to-handler matching이면 `HandlerMapping`, 전체 handoff 조율이면 `Dispatcher`가 맞고, handler 안쪽 정책 선택과 새 객체 생성에만 `Selector`, `Factory`를 남기는 편이 초보자에게도 읽기 쉽다.
