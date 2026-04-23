# Spring MVC Async Dispatch with `Callable` / `DeferredResult`

> 한 줄 요약: Spring MVC async는 WebFlux가 아니라 Servlet async + redispatch 모델이므로, 스레드 전환과 두 번째 dispatch를 이해해야 timeout, filter, security 문제가 풀린다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring MVC 요청 생명주기](./spring-mvc-request-lifecycle.md)
> - [Spring Async Timeout vs Disconnect Decision Tree](./spring-async-timeout-disconnect-decision-tree.md)
> - [Spring WebFlux vs MVC](./spring-webflux-vs-mvc.md)
> - [Spring Request Scope Proxy Pitfalls](./spring-request-scope-proxy-pitfalls.md)
> - [Spring `OncePerRequestFilter` Async / Error Dispatch Traps](./spring-onceperrequestfilter-async-error-dispatch-traps.md)
> - [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
> - [Spring SecurityContext Propagation across Async / Reactive Boundaries](./spring-securitycontext-propagation-async-reactive-boundaries.md)
> - [Spring MVC Filter, Interceptor, and ControllerAdvice Boundaries](./spring-mvc-filter-interceptor-controlleradvice-boundaries.md)
> - [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](../network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md)
> - [Timeout, Retry, Backoff 실전](../network/timeout-retry-backoff-practical.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](../network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)

retrieval-anchor-keywords: spring mvc async, callable, deferredresult, webasynctask, async dispatch, async redispatch, servlet async, async timeout, AsyncRequestTimeoutException, AsyncRequestNotUsableException, disconnected client, onceperrequestfilter async dispatch, webasyncmanager

## 핵심 개념

Spring MVC에서 async 처리라고 해서 곧바로 reactive가 되는 것은 아니다.

핵심은 다음이다.

- 첫 번째 요청 스레드가 컨트롤러까지 진입한다
- 컨트롤러가 `Callable`, `DeferredResult`, `WebAsyncTask` 같은 async 타입을 반환한다
- Servlet 컨테이너가 요청을 async 모드로 전환하고 원래 요청 스레드를 반환한다
- 결과가 준비되면 컨테이너가 같은 요청을 다시 dispatch한다

즉, MVC async의 본질은 "논블로킹 프레임워크"가 아니라 **서블릿 요청을 잠시 보류했다가 다시 dispatch하는 모델**이다.

이걸 놓치면 다음이 흔들린다.

- 왜 interceptor가 두 번 보이는가
- 왜 filter 로그가 기대만큼 안 찍히는가
- 왜 request scope / `SecurityContext`가 스레드 전환에서 깨지는가
- 왜 timeout 응답이 `@ControllerAdvice`와 다르게 느껴지는가

## 깊이 들어가기

### 1. MVC async는 WebFlux와 다른 모델이다

둘 다 "오래 걸리는 작업 때문에 요청 스레드를 덜 묶는다"는 점은 비슷해 보인다.

하지만 내부 모델은 다르다.

- MVC async: Servlet stack 위에서 async dispatch를 사용한다
- WebFlux: event-loop와 reactive publisher 계약 위에서 흘러간다

즉 MVC async는 **기존 MVC 생명주기를 유지한 채, 중간에 스레드를 반납하는 확장**이다.

그래서 blocking I/O를 다른 executor로 옮길 수는 있지만, 시스템 전체가 reactive backpressure를 갖게 되는 것은 아니다.

### 2. 반환 타입마다 책임이 다르다

대표 타입은 아래처럼 구분하면 된다.

- `Callable<T>`: Spring이 작업을 executor에 제출하고, 완료되면 결과를 받아 redispatch한다
- `WebAsyncTask<T>`: `Callable`에 timeout, executor, callback 정책을 덧붙인 형태다
- `DeferredResult<T>`: 결과를 만드는 주체가 controller 밖에 있고, 나중에 누군가 완료시킨다
- `ResponseBodyEmitter` / `SseEmitter`: 응답을 여러 조각으로 오래 스트리밍할 때 쓴다

즉 질문은 "비동기인가?"가 아니라, **결과를 누가 언제 완성하느냐**다.

### 3. async 처리의 핵심은 redispatch다

흐름을 단순화하면 아래와 같다.

```text
client request
-> DispatcherServlet
-> controller returns Callable/DeferredResult
-> request enters async mode
-> original servlet thread returns to pool
-> async result completes on another thread or callback
-> container redispatches same request
-> DispatcherServlet resumes and writes response
```

여기서 중요한 점은 "응답 쓰기"가 최초 스레드에서 바로 끝나지 않을 수 있다는 것이다.

따라서 필터와 인터셉터를 볼 때도 dispatch type을 같이 봐야 한다.

- 첫 번째 request dispatch
- 나중의 async redispatch

이 구분이 없으면 "왜 같은 요청이 두 번 보이지?"라는 혼란이 생긴다.

### 4. filter와 interceptor는 async 경계에서 체감이 달라진다

MVC interceptor는 async 시작 시점에 일반 완료 콜백 대신 `afterConcurrentHandlingStarted`가 호출될 수 있다.

이후 결과가 준비되어 redispatch되면 다시 completion 단계가 이어진다.

필터는 더 헷갈리기 쉽다.

특히 `OncePerRequestFilter`는 기본적으로 async dispatch를 다시 필터링하지 않도록 설계된 경우가 많다.
그래서 "요청은 재개됐는데 필터 로그는 왜 한 번만 찍히지?" 같은 현상이 나온다.

핵심은 filter/interceptor를 볼 때 `REQUEST`, `ASYNC`, `ERROR` dispatch를 함께 추적하는 것이다.

### 5. 스레드 로컬과 request scope는 공짜로 안전하지 않다

async MVC에서 가장 많이 깨지는 가정은 "같은 요청이니 같은 스레드겠지"다.

그렇지 않다.

- MDC 같은 로깅 컨텍스트
- 직접 다루는 `ThreadLocal`
- `TransactionSynchronizationManager`
- request scope 접근 타이밍

이런 요소는 스레드 전환에서 쉽게 어긋난다.

Security는 조금 더 미묘하다.

- `Callable` 기반 async에는 Spring Security가 `WebAsyncManagerIntegrationFilter`를 통해 `SecurityContext`를 이어 주는 편이다
- 하지만 `DeferredResult`를 채우는 외부 스레드에서 임의의 보안 작업을 하면, 그 스레드의 컨텍스트 전파는 별도로 설계해야 한다

즉 "MVC async에서 보안 컨텍스트가 된다/안 된다"가 아니라, **어떤 async 타입과 어떤 스레드 모델을 쓰는지**가 중요하다.

### 6. timeout과 executor는 운영 계약이다

MVC async는 servlet thread를 아끼게 해 주지만, 작업 스레드와 timeout이 사라지는 것은 아니다.

오히려 다음을 명시해야 운영이 안정된다.

- async executor 크기
- queue 크기
- per-request timeout
- timeout 시 HTTP 응답 계약
- 취소/정리 콜백

설정을 안 하면 개발 환경에서는 되는데 운영에서 p99가 흔들리기 쉽다.

```java
@Configuration
public class WebMvcAsyncConfig implements WebMvcConfigurer {

    @Override
    public void configureAsyncSupport(AsyncSupportConfigurer configurer) {
        configurer.setDefaultTimeout(3_000);
        configurer.setTaskExecutor(mvcTaskExecutor());
    }

    @Bean
    public AsyncTaskExecutor mvcTaskExecutor() {
        ThreadPoolTaskExecutor executor = new ThreadPoolTaskExecutor();
        executor.setCorePoolSize(16);
        executor.setMaxPoolSize(64);
        executor.setQueueCapacity(200);
        executor.setThreadNamePrefix("mvc-async-");
        executor.initialize();
        return executor;
    }
}
```

## 실전 시나리오

### 시나리오 1: 외부 API가 느려서 servlet thread가 고갈된다

동기 MVC에서 controller 안에서 오래 block하면 request thread가 그대로 묶인다.

`Callable`로 넘기면 servlet thread는 빨리 반납할 수 있다.

하지만 착각하면 안 된다.

- blocking call이 worker thread로 옮겨갔을 뿐이다
- worker pool과 timeout을 제한하지 않으면 병목 위치만 바뀐다

### 시나리오 2: `DeferredResult`를 만들었는데 timeout이 자주 난다

대개 결과를 채우는 주체가 너무 늦거나, 완료/실패/취소 콜백이 비어 있다.

이 경우는 단순 코드 버그가 아니라 **미완료 요청이 메모리에 오래 남는 운영 문제**로 이어질 수 있다.

### 시나리오 3: 요청 로깅 필터가 completion 로그를 안 남긴다

초기 request dispatch만 로그를 남기고 async redispatch는 필터링하지 않았을 수 있다.

dispatch type과 `OncePerRequestFilter` 정책을 같이 봐야 한다.

### 시나리오 4: request-scoped bean이나 custom `ThreadLocal`이 worker thread에서 깨진다

controller는 같은 요청이라고 생각하지만, async 작업은 다른 스레드에서 실행될 수 있다.

그래서 request/thread affinity를 전제로 한 코드는 async 경계에서 쉽게 무너진다.

## 코드로 보기

### `Callable` 기반 async controller

```java
@GetMapping("/orders/{id}")
public Callable<ResponseEntity<OrderResponse>> getOrder(@PathVariable Long id) {
    return () -> ResponseEntity.ok(orderService.find(id));
}
```

### `DeferredResult` 기반 외부 완료

```java
@GetMapping("/reports/{id}")
public DeferredResult<ResponseEntity<ReportResponse>> report(@PathVariable Long id) {
    DeferredResult<ResponseEntity<ReportResponse>> result = new DeferredResult<>(5_000L);

    reportFacade.generateAsync(id)
        .whenComplete((report, throwable) -> {
            if (throwable != null) {
                result.setErrorResult(ResponseEntity.internalServerError().build());
                return;
            }
            result.setResult(ResponseEntity.ok(report));
        });

    result.onTimeout(() ->
        result.setErrorResult(ResponseEntity.status(HttpStatus.GATEWAY_TIMEOUT).build())
    );

    return result;
}
```

### `WebAsyncTask`로 timeout과 executor 분리

```java
@GetMapping("/inventory/{sku}")
public WebAsyncTask<ResponseEntity<InventoryResponse>> inventory(@PathVariable String sku) {
    Callable<ResponseEntity<InventoryResponse>> task =
        () -> ResponseEntity.ok(inventoryService.read(sku));

    WebAsyncTask<ResponseEntity<InventoryResponse>> webAsyncTask =
        new WebAsyncTask<>(2_000L, task);

    webAsyncTask.onTimeout(() -> ResponseEntity.status(HttpStatus.GATEWAY_TIMEOUT).build());
    return webAsyncTask;
}
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 동기 MVC | 단순하다 | 느린 I/O가 request thread를 묶는다 | 빠른 내부 처리 |
| `Callable` | servlet thread를 빨리 반환한다 | 별도 worker pool 관리가 필요하다 | 오래 걸리는 blocking 작업 |
| `DeferredResult` | 외부 이벤트/콜백과 잘 맞는다 | 완료 누락, timeout 디버깅이 어렵다 | 결과 생성 주체가 controller 밖에 있을 때 |
| WebFlux | end-to-end reactive 모델이 가능하다 | 학습/전환 비용이 높다 | I/O 경계 전체를 reactive로 설계할 때 |

핵심은 async 타입을 "성능 옵션"으로만 보지 않고, **스레드 전환과 응답 완료 책임의 모델**로 보는 것이다.

## 꼬리질문

> Q: Spring MVC async와 WebFlux의 가장 큰 차이는 무엇인가?
> 의도: servlet async와 reactive 모델 구분 확인
> 핵심: 전자는 redispatch 기반 MVC 확장이고, 후자는 reactive execution model이다.

> Q: `Callable`과 `DeferredResult`의 차이는 무엇인가?
> 의도: async 책임 주체 구분 확인
> 핵심: 전자는 Spring이 작업을 실행하고, 후자는 외부 주체가 나중에 결과를 완성한다.

> Q: async MVC에서 filter 로그가 한 번만 보이는 이유는 무엇인가?
> 의도: dispatch type 인식 확인
> 핵심: async redispatch를 필터가 다시 처리하지 않도록 설정됐을 수 있다.

> Q: servlet thread를 반납하면 왜 여전히 장애가 날 수 있는가?
> 의도: 병목 이동 이해 확인
> 핵심: worker pool, timeout, callback 누락이 새 병목이 된다.

## 한 줄 정리

Spring MVC async는 "요청을 다른 스레드에서 끝내는 것"이 아니라, Servlet async와 redispatch를 이용해 응답 완료 시점을 뒤로 미루는 모델이다.
