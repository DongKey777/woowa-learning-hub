---
schema_version: 3
title: Servlet Async Redispatch Filter Interceptor Ordering
concept_id: language/servlet-async-redispatch-filter-interceptor-ordering
canonical: true
category: language
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids:
- missions/spring-roomescape
- missions/payment
review_feedback_tags:
- servlet-async
- spring-mvc
- threadlocal
aliases:
- Servlet REQUEST ASYNC ERROR Redispatch Ordering for Filters and Interceptors
- servlet async redispatch interceptor ordering
- AsyncHandlerInterceptor afterConcurrentHandlingStarted
- request lifetime vs thread lifetime
- OncePerRequestFilter async error dispatch
- servlet async MDC cleanup
symptoms:
- async MVC에서 request-lifetime state와 thread-bound ThreadLocal MDC view를 섞어 원래 REQUEST thread에 context가 새거나 async redispatch에서 context가 빠져
- async가 시작됐는데 filter finally에서 request wrapper나 cleanup handle을 너무 일찍 닫아 ASYNC redispatch가 쓰는 state를 잃어
- afterCompletion만 믿고 cleanup을 두어 REQUEST dispatch에서 async 시작 시 afterConcurrentHandlingStarted만 호출되는 경로를 놓쳐
intents:
- troubleshooting
- deep_dive
- design
prerequisites:
- language/servlet-asynclistener-cleanup-patterns
- language/servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads
- language/threadlocal-leaks-context-propagation
next_docs:
- language/servlet-async-timeout-downstream-deadline-propagation
- language/streamingresponsebody-sseemitter-terminal-cleanup-matrix
- spring/onceperrequestfilter-async-error-dispatch-traps
linked_paths:
- contents/language/java/servlet-asynclistener-cleanup-patterns.md
- contents/language/java/servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads.md
- contents/language/java/streamingresponsebody-sseemitter-terminal-cleanup-matrix.md
- contents/language/java/threadlocal-leaks-context-propagation.md
- contents/spring/spring-mvc-async-deferredresult-callable-dispatch.md
- contents/spring/spring-onceperrequestfilter-async-error-dispatch-traps.md
- contents/spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md
- contents/spring/spring-mvc-filter-interceptor-controlleradvice-boundaries.md
confusable_with:
- language/servlet-asynclistener-cleanup-patterns
- language/threadlocal-leaks-context-propagation
- spring/onceperrequestfilter-async-error-dispatch-traps
forbidden_neighbors: []
expected_queries:
- Servlet async에서 REQUEST ASYNC ERROR redispatch 순서와 filter interceptor callback ordering을 설명해줘
- AsyncHandlerInterceptor afterConcurrentHandlingStarted는 왜 original REQUEST thread state를 비우는 데 중요해?
- request attribute로 살아야 하는 state와 ThreadLocal MDC처럼 dispatch thread에만 붙는 view를 어떻게 나눠?
- async가 시작된 REQUEST dispatch에서 afterCompletion이 바로 호출되지 않을 수 있는 이유가 뭐야?
- OncePerRequestFilter async error dispatch와 ThreadLocal cleanup traps를 Spring MVC 기준으로 알려줘
contextual_chunk_prefix: |
  이 문서는 Servlet async REQUEST/ASYNC/ERROR redispatch에서 filter, interceptor, AsyncHandlerInterceptor, ThreadLocal/MDC cleanup ordering을 진단하는 advanced playbook이다.
  servlet async redispatch, filter ordering, interceptor afterConcurrentHandlingStarted, ThreadLocal cleanup, MDC 질문이 본 문서에 매핑된다.
---
# Servlet `REQUEST` / `ASYNC` / `ERROR` Redispatch Ordering for Filters and Interceptors

> 한 줄 요약: servlet async에서 오래 살아야 하는 상태는 request/async lifecycle에 붙이고, `MDC`나 custom `ThreadLocal` 같은 thread-bound view는 각 dispatch마다 다시 bind/clear해야 한다. `REQUEST`에서 async가 시작되면 Spring interceptor는 `afterConcurrentHandlingStarted`로 원래 스레드 상태를 비우고, 실제 최종 release는 `AsyncListener`나 Spring async callback이 맡는 편이 안전하다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Servlet `AsyncListener` Cleanup Patterns for `Callable`, `WebAsyncTask`, and `DeferredResult`](./servlet-asynclistener-cleanup-patterns.md)
> - [Servlet Container Timeout and Cancellation Boundaries: Spring MVC and Virtual Threads](./servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads.md)
> - [`StreamingResponseBody` and `SseEmitter` Terminal Cleanup Matrix](./streamingresponsebody-sseemitter-terminal-cleanup-matrix.md)
> - [ThreadLocal Leaks and Context Propagation](./threadlocal-leaks-context-propagation.md)
> - [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](../../spring/spring-mvc-async-deferredresult-callable-dispatch.md)
> - [Spring `OncePerRequestFilter` Async / Error Dispatch Traps](../../spring/spring-onceperrequestfilter-async-error-dispatch-traps.md)
> - [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](../../spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
> - [Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries](../../spring/spring-mvc-filter-interceptor-controlleradvice-boundaries.md)

> retrieval-anchor-keywords: async redispatch interceptor ordering, servlet REQUEST ASYNC ERROR ordering, dispatcher type REQUEST ASYNC ERROR, HandlerInterceptor async redispatch, AsyncHandlerInterceptor afterConcurrentHandlingStarted, OncePerRequestFilter async error dispatch, request scoped state async release, request attribute vs ThreadLocal, servlet async MDC cleanup, async redispatch filter ordering, error dispatch interceptor ordering, request lifetime vs thread lifetime, AsyncListener onComplete, onTimeout, onError, onStartAsync, request wrapper release after async, hasOriginalRequestAndResponse, spring mvc async ordering, request scoped bean async thread, deferredresult redispatch ordering, callable redispatch ordering

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [Dispatch Ordering Map](#dispatch-ordering-map)
- [상태를 어디에 둘 것인가](#상태를-어디에-둘-것인가)
- [Filter / Interceptor별 attach-release 규칙](#filter--interceptor별-attach-release-규칙)
- [코드로 보기](#코드로-보기)
- [실전 시나리오](#실전-시나리오)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

이 주제에서 가장 먼저 분리해야 하는 것은 두 가지 수명이다.

- **request-lifetime state**: correlation id, cleanup coordinator, request wrapper, detached producer cancel handle처럼 요청 전체 생애 동안 살아야 하는 상태
- **thread-bound view**: `MDC`, custom `ThreadLocal`, `LocaleContextHolder`처럼 "현재 dispatch를 수행 중인 thread"에만 묶여야 하는 상태

async MVC에서는 같은 HTTP 요청이 여러 dispatch를 거치지만, 그 dispatch를 처리하는 thread는 달라질 수 있다.

- 최초 진입은 보통 `REQUEST`
- async 결과를 이어서 처리하는 것은 `ASYNC` redispatch
- container error page 경로는 `ERROR` dispatch

따라서 질문은 "필터나 interceptor가 몇 번 도나"가 아니라 아래 둘을 구분했는가다.

- 어떤 상태가 **요청 전체 생애**를 따라가야 하는가
- 어떤 상태가 **현재 dispatch thread**에만 잠깐 붙어야 하는가

이걸 섞으면 흔히 이런 버그가 생긴다.

- 원래 `REQUEST` thread에 남은 `ThreadLocal`이 pool 재사용으로 다른 요청에 새어 나간다
- async가 시작됐는데 filter `finally`에서 wrapper나 cleanup handle을 너무 일찍 닫는다
- `afterCompletion`만 믿고 정리하다가 timeout / disconnect / error path에서 release가 빠진다

## Dispatch Ordering Map

### 1. 가장 흔한 async success 흐름은 `REQUEST -> ASYNC`

```text
REQUEST dispatch
-> filter(REQUEST)
-> interceptor.preHandle
-> controller returns Callable / WebAsyncTask / DeferredResult
-> interceptor.afterConcurrentHandlingStarted
-> filter finally
-> original request thread exits

async result becomes available
-> container ASYNC dispatch
-> filter(ASYNC) if mapped
-> interceptor.preHandle
-> Spring resumes with concurrent result
-> interceptor.postHandle / afterCompletion (normal MVC rules)
-> filter finally
-> AsyncListener.onComplete
```

핵심은 `REQUEST`에서 async가 시작되면 **그 dispatch에서는 `postHandle`과 `afterCompletion`이 호출되지 않고** `afterConcurrentHandlingStarted`가 대신 호출된다는 점이다.  
그 뒤 결과가 준비되면 새로운 `ASYNC` dispatch에서 `preHandle -> postHandle -> afterCompletion`이 다시 돈다.

### 2. timeout이나 async error가 항상 `ERROR` dispatch를 뜻하는 것은 아니다

Spring MVC async timeout은 종종 "concurrent result나 예외를 만들어 `ASYNC` redispatch로 복귀"하는 방식으로 처리된다.  
반대로 servlet container는 `AsyncListener.onTimeout` / `onError` 이후 애플리케이션이 `dispatch()`나 `complete()`를 하지 않으면 `ERROR` dispatch를 만들 수 있다.

즉 timeout/error 해석은 보통 아래 둘 중 하나다.

- **Spring이 직접 concurrent result를 세팅한 경우**: `ASYNC` redispatch로 돌아와 MVC가 응답을 마무리
- **container error page 경로로 넘어간 경우**: `ERROR` dispatch

그래서 "timeout이 났으니 interceptor `afterCompletion`이 반드시 원래 handler 체인에서 호출되겠지"라고 가정하면 위험하다.

### 3. `ERROR` dispatch는 원래 handler chain의 연장이 아니라 별도 error rendering 경로다

`ERROR` dispatch는 filter 관점에서는 같은 request의 후속 dispatch지만, Spring MVC interceptor 관점에서는 **어떤 handler가 error page를 처리하느냐**가 중요하다.

- `DispatcherServlet`이 `/error` 같은 경로를 처리하면 그 error handler용 interceptor chain이 돈다
- container가 자체 error page를 처리하면 원래 MVC interceptor chain이 아예 관여하지 않을 수도 있다

즉 `ERROR` dispatch는 "원래 controller의 마지막 콜백"이 아니라 **error dispatch target의 새 진입**으로 보는 편이 안전하다.

## 상태를 어디에 둘 것인가

| 상태 종류 | 권장 저장 위치 | attach 시점 | release 시점 | 이유 |
|---|---|---|---|---|
| 요청 전체에 걸친 state (`traceId`, cleanup handle, cancel token, span handle) | request attribute 또는 async lifecycle에 묶인 holder | 최초 `REQUEST` filter/interceptor | `AsyncListener.onComplete`, `DeferredResult.onCompletion`, `CallableProcessingInterceptor.afterCompletion` 같은 terminal callback | thread가 바뀌어도 살아 있어야 한다 |
| thread-bound view (`MDC`, custom `ThreadLocal`, `LocaleContextHolder`) | 영구 저장하지 말고 request state에서 재구성 | 각 `REQUEST` / `ASYNC` / 필요한 경우 `ERROR` dispatch 시작점 | 각 dispatch의 `finally`, `afterConcurrentHandlingStarted`, `afterCompletion` | dispatch thread마다 다시 붙여야 한다 |
| request/response wrapper, cached body wrapper | wrapper 자체 + 필요 여부 flag를 request에 보관 | 최초 `REQUEST` filter | async를 안 썼으면 현재 `finally`, async를 썼으면 `AsyncListener.onComplete` | async redispatch 동안 wrapper가 더 살아야 할 수 있다 |
| request-scoped bean의 실제 target 객체 | detached worker에 직접 넘기지 않는다 | dispatch thread 안에서만 resolve | 일반 request lifecycle에 맡김 | request scope는 redispatch thread에는 다시 열릴 수 있어도 detached worker에서는 안전하지 않다 |

여기서 제일 중요한 규칙은 두 가지다.

- request/response 객체 자체는 thread-safe한 공유 객체라고 생각하면 안 된다. async worker에는 필요한 값만 snapshot으로 넘긴다.
- request-scoped bean이나 `HttpServletRequest`를 async producer thread에 오래 붙잡아 두지 말고, 필요한 식별자나 immutable snapshot만 넘긴다.

## Filter / Interceptor별 attach-release 규칙

### 1. `OncePerRequestFilter`: request-lifetime state는 만들고, thread-bound state는 dispatch마다 비운다

filter의 책임이 무엇이냐에 따라 policy가 갈린다.

- **인증/파싱 1회성 작업**: 보통 `REQUEST`에서만 실행하고 `ASYNC`/`ERROR`는 제외한다
- **MDC/tracing rebinding**: `ASYNC`에도 참여해 각 dispatch마다 bind/clear한다
- **wrapper-owning filter**: async 시작 여부를 보고 최종 release를 `AsyncListener`로 미룬다

초기 `REQUEST` dispatch의 `finally`에서 안전한 일은 아래 정도다.

- 현재 thread의 `MDC` / custom `ThreadLocal` 제거
- `request.isAsyncStarted()` 확인
- async가 시작됐다면 cleanup listener 등록

반대로 위험한 일은 아래다.

- async가 이미 시작됐는데 request-lifetime resource를 즉시 닫기
- `ERROR` dispatch에서도 다시 인증이나 body rewrite를 시도하기

wrapper를 붙인 filter라면 servlet spec의 `AsyncContext.hasOriginalRequestAndResponse()`가 "wrapper를 보존해야 하는가"를 판단하는 힌트가 될 수 있다.

### 2. `AsyncHandlerInterceptor`: `afterConcurrentHandlingStarted`는 "최종 release"가 아니라 "현재 thread 정리"다

Spring MVC에서 async가 시작되면 `postHandle` / `afterCompletion` 대신 `afterConcurrentHandlingStarted`가 호출된다.  
이 메서드는 request-lifetime cleanup보다 **원래 request thread에 묶여 있던 상태를 비우는 지점**으로 보는 편이 맞다.

보통 책임 분리는 이렇게 잡는다.

- `preHandle`: request attribute에서 state를 읽어 현재 thread에 bind
- `afterConcurrentHandlingStarted`: 원래 thread에서만 필요한 `ThreadLocal` 정리
- `afterCompletion`: 현재 dispatch thread에서 bind한 상태 정리

즉 interceptor는 **per-dispatch bind/unbind**에 강하고, 최종 terminal release의 단독 owner로 두기에는 약하다.

### 3. `AsyncListener`나 Spring async callback이 최종 release를 맡는다

request-lifetime state의 최종 release는 보통 아래 surface 중 하나가 맡는 편이 안전하다.

- `AsyncListener.onComplete`
- `AsyncListener.onTimeout`
- `AsyncListener.onError`
- `DeferredResult.onCompletion`
- `WebAsyncTask.onCompletion`
- `CallableProcessingInterceptor.afterCompletion`

이 surface가 중요한 이유는 timeout, disconnect, error dispatch 유무와 상관없이 **async lifecycle이 끝났다는 사실**에 더 가깝기 때문이다.

또한 async cycle이 다시 시작될 수 있으므로 `AsyncListener`는 `onStartAsync`에서 자기 자신을 새 `AsyncContext`에 다시 등록하는 패턴이 필요하다.

## 코드로 보기

### 1. interceptor는 request attribute를 기준으로 thread-bound view를 다시 붙인다

```java
public final class RequestStateInterceptor implements AsyncHandlerInterceptor {
    public static final String ATTR = RequestStateInterceptor.class.getName() + ".state";

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        RequestState state = (RequestState) request.getAttribute(ATTR);
        if (state == null) {
            state = RequestState.from(request);
            request.setAttribute(ATTR, state);
        }

        state.bindToCurrentThread();
        return true;
    }

    @Override
    public void afterConcurrentHandlingStarted(
            HttpServletRequest request, HttpServletResponse response, Object handler) {
        RequestState.clearThreadBinding();
    }

    @Override
    public void afterCompletion(
            HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) {
        RequestState.clearThreadBinding();
    }
}
```

핵심은 state를 `ThreadLocal` 그 자체로 들고 가는 것이 아니라, **request attribute에 둔 state를 dispatch마다 bind/unbind**하는 것이다.

### 2. filter는 async가 시작됐을 때 final release를 listener로 넘긴다

```java
public final class TraceContextFilter extends OncePerRequestFilter {

    @Override
    protected boolean shouldNotFilterAsyncDispatch() {
        return false; // ASYNC redispatch에서도 MDC를 다시 붙이고 싶을 때
    }

    @Override
    protected boolean shouldNotFilterErrorDispatch() {
        return true; // error rendering까지 같은 정책이 꼭 필요하지 않다면 보수적으로 제외
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain) throws ServletException, IOException {

        RequestState state = RequestState.getOrCreate(request);
        state.bindToCurrentThread();

        try {
            filterChain.doFilter(request, response);
        } finally {
            RequestState.clearThreadBinding();

            if (request.isAsyncStarted()) {
                AsyncCleanupListener.attachOnce(request.getAsyncContext(), state);
            } else {
                state.releaseOnce();
            }
        }
    }
}
```

이 패턴의 의도는 단순하다.

- 현재 dispatch thread 정리는 filter/interceptor `finally`
- request 전체 생애에 대한 최종 release는 async listener

## 실전 시나리오

### 시나리오 1: async controller에서 로그 `traceId`가 끊긴다

초기 `REQUEST` dispatch에서만 `MDC`를 세팅하고, `ASYNC` redispatch에서 다시 bind하지 않았을 가능성이 크다.  
request attribute에 담아 두고 각 dispatch 시작 시 다시 붙여야 한다.

### 시나리오 2: `DeferredResult` timeout 뒤 wrapper close 예외가 난다

최초 filter `finally`에서 wrapper나 request-lifetime resource를 닫았을 수 있다.  
async가 시작됐으면 최종 release를 `onComplete` 계열로 미뤄야 한다.

### 시나리오 3: `afterCompletion`에 cleanup을 뒀는데 client disconnect에서 leak이 난다

원래 handler chain의 `afterCompletion`만으로는 terminal path를 모두 덮지 못했을 수 있다.  
특히 `ERROR` dispatch가 다른 target으로 가거나 redispatch 자체가 생략되면 최종 release는 async callback이 더 안전하다.

### 시나리오 4: request-scoped bean을 `CompletableFuture`에 넘겼더니 이상하게 깨진다

request scope는 "같은 HTTP 요청"과 "아무 async thread"를 동일시하지 않는다.  
detached worker에는 bean target 대신 필요한 값 snapshot만 넘겨야 한다.

## 꼬리질문

> Q: async가 시작된 `REQUEST` dispatch에서 왜 interceptor `afterCompletion`이 바로 호출되지 않는가?
> 의도: async hand-off 시 Spring interceptor 계약 확인
> 핵심: 그 dispatch는 아직 끝난 것이 아니라 concurrent handling으로 넘어간 것이므로 `afterConcurrentHandlingStarted`가 대신 호출된다.

> Q: request-lifetime state와 `ThreadLocal` state를 왜 따로 봐야 하는가?
> 의도: request 수명과 thread 수명 분리 확인
> 핵심: 같은 HTTP 요청이 여러 dispatch와 여러 thread를 거칠 수 있기 때문이다.

> Q: `ERROR` dispatch에 original interceptor cleanup을 걸어 두면 왜 불안한가?
> 의도: error path ownership 확인
> 핵심: `ERROR` dispatch는 원래 handler chain의 연장이 아니라 error target의 새 진입일 수 있기 때문이다.

> Q: filter `finally`에서 `request.isAsyncStarted()`를 왜 봐야 하는가?
> 의도: async hand-off와 premature release 구분 확인
> 핵심: async가 시작됐으면 request-lifetime resource는 아직 살아 있어야 할 수 있기 때문이다.

## 한 줄 정리

servlet async에서 정답은 "`REQUEST`에서 만들고 `ASYNC`에서 다시 붙이고, 최종 release는 async lifecycle callback에 둔다"다. filter/interceptor는 per-dispatch 정리에 강하고, request 전체 생애의 마지막 cleanup owner는 `AsyncListener`나 Spring async callback이 맡는 편이 안전하다.
