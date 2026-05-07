---
schema_version: 3
title: Servlet AsyncListener Cleanup Patterns
concept_id: language/servlet-asynclistener-cleanup-patterns
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
- cleanup
- cancellation
aliases:
- Servlet AsyncListener Cleanup Patterns for Callable WebAsyncTask DeferredResult
- AsyncListener cleanup patterns
- servlet async cleanup coordinator
- Callable WebAsyncTask DeferredResult cleanup
- async timeout producer cancel resource cleanup
- Spring MVC async cleanup
symptoms:
- servlet async 종료를 timeout response 선택, producer 중단, request resource 해제 한 콜백에 뭉개 timeout과 disconnect와 normal completion 경로가 다르게 새어
- onTimeout에서만 취소하고 onError나 onComplete backstop을 놓쳐 client disconnect나 network error 뒤 producer가 계속 실행돼
- AsyncListener가 async cycle 단위로 붙는다는 점을 모르고 onStartAsync에서 listener 재등록을 하지 않아 redispatch 이후 cleanup 이벤트를 놓쳐
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- language/servlet-async-redispatch-filter-interceptor-ordering
- language/servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads
- language/thread-interruption-cooperative-cancellation-playbook
next_docs:
- language/servlet-async-timeout-downstream-deadline-propagation
- language/streaming-response-abort-surfaces-servlet-virtual-threads
- language/streamingresponsebody-sseemitter-terminal-cleanup-matrix
linked_paths:
- contents/language/java/servlet-async-redispatch-filter-interceptor-ordering.md
- contents/language/java/servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads.md
- contents/language/java/servlet-async-timeout-downstream-deadline-propagation.md
- contents/language/java/streaming-response-abort-surfaces-servlet-virtual-threads.md
- contents/language/java/streamingresponsebody-sseemitter-terminal-cleanup-matrix.md
- contents/language/java/thread-interruption-cooperative-cancellation-playbook.md
- contents/language/java/completablefuture-cancellation-semantics.md
- contents/language/java/virtual-thread-spring-jdbc-httpclient-framework-integration.md
- contents/spring/spring-mvc-async-deferredresult-callable-dispatch.md
- contents/spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md
- contents/spring/spring-onceperrequestfilter-async-error-dispatch-traps.md
confusable_with:
- language/servlet-async-redispatch-filter-interceptor-ordering
- language/servlet-async-timeout-downstream-deadline-propagation
- language/streamingresponsebody-sseemitter-terminal-cleanup-matrix
forbidden_neighbors: []
expected_queries:
- AsyncListener onTimeout onError onComplete onStartAsync를 cleanup coordinator에 어떻게 연결해야 해?
- Callable WebAsyncTask DeferredResult에서 timeout response 선택과 producer cancel과 final resource cleanup을 왜 분리해야 해?
- AsyncListener는 async cycle마다 붙기 때문에 onStartAsync에서 재등록해야 한다는 뜻이 뭐야?
- client disconnect error path에서 onTimeout만 믿으면 producer가 계속 도는 이유를 설명해줘
- Spring MVC async callback과 servlet AsyncListener cleanup을 idempotent coordinator로 묶는 패턴을 알려줘
contextual_chunk_prefix: |
  이 문서는 Servlet AsyncListener와 Spring MVC Callable/WebAsyncTask/DeferredResult callback을 idempotent cleanup coordinator로 연결해 timeout, error, complete, redispatch cleanup 누락을 막는 advanced playbook이다.
  AsyncListener, servlet async cleanup, Callable, WebAsyncTask, DeferredResult, cancellation coordinator 질문이 본 문서에 매핑된다.
---
# Servlet `AsyncListener` Cleanup Patterns for `Callable`, `WebAsyncTask`, and `DeferredResult`

> 한 줄 요약: servlet async cleanup은 "timeout 응답 만들기", "실제 producer 중단시키기", "요청에 묶인 리소스 정리"를 한 콜백에 뭉개지 말고, `AsyncListener`와 Spring async callback을 같은 idempotent coordinator로 연결할 때 가장 휴대성이 좋다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Servlet `REQUEST` / `ASYNC` / `ERROR` Redispatch Ordering for Filters and Interceptors](./servlet-async-redispatch-filter-interceptor-ordering.md)
> - [Servlet Container Timeout and Cancellation Boundaries: Spring MVC and Virtual Threads](./servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads.md)
> - [Servlet Async Timeout to Downstream HTTP and JDBC Deadline Propagation](./servlet-async-timeout-downstream-deadline-propagation.md)
> - [Streaming Response Abort Surfaces: `StreamingResponseBody`, SSE, and Virtual-Thread Cancellation Gaps](./streaming-response-abort-surfaces-servlet-virtual-threads.md)
> - [`StreamingResponseBody` and `SseEmitter` Terminal Cleanup Matrix](./streamingresponsebody-sseemitter-terminal-cleanup-matrix.md)
> - [Thread Interruption and Cooperative Cancellation Playbook](./thread-interruption-cooperative-cancellation-playbook.md)
> - [CompletableFuture Cancellation Semantics](./completablefuture-cancellation-semantics.md)
> - [Virtual Thread Framework Integration: Spring, JDBC, and `HttpClient`](./virtual-thread-spring-jdbc-httpclient-framework-integration.md)
> - [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](../../spring/spring-mvc-async-deferredresult-callable-dispatch.md)
> - [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](../../spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
> - [Spring `OncePerRequestFilter` Async / Error Dispatch Traps](../../spring/spring-onceperrequestfilter-async-error-dispatch-traps.md)

> retrieval-anchor-keywords: AsyncListener, AsyncContext, onStartAsync, onTimeout, onError, onComplete, onCompletion, servlet async cleanup, async redispatch cleanup, redispatch listener re-register, Callable cleanup, WebAsyncTask cleanup, DeferredResult cleanup, CallableProcessingInterceptor, DeferredResultProcessingInterceptor, AsyncHandlerInterceptor, request expired, late completion, setResult false, cancel token, idempotent cleanup, client disconnect, network error, async timeout wiring, spring mvc async cleanup, async timeout downstream cancel, async timeout statement cancel, async timeout outbound http cancel, request deadline cleanup coordinator, streaming terminal cleanup matrix, post-commit cleanup, late write suppression

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [경계 지도](#경계-지도)
- [휴대성 있는 설계 규칙](#휴대성-있는-설계-규칙)
- [타입별 cleanup 패턴](#타입별-cleanup-패턴)
- [코드로 보기](#코드로-보기)
- [실전 시나리오](#실전-시나리오)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

`Callable`, `WebAsyncTask`, `DeferredResult`를 섞어 쓰다 보면 cleanup이 자주 꼬이는 이유는 "종료"를 한 가지로 생각하기 때문이다.

실제로는 종료 책임이 셋으로 갈라진다.

- **timeout/error response 선택**: 503, 504, fallback body, `AsyncRequestTimeoutException` 같은 HTTP 표면
- **producer 중단 신호**: `Future.cancel(true)`, cancel token flip, subscription 해제, 외부 client cancel
- **최종 리소스 해제**: registry 제거, heartbeat/scheduler 중단, span 종료, request-scoped 정리

이 셋을 구분하지 않으면 흔히 이런 코드가 나온다.

- `onTimeout`에서만 취소하고 client disconnect/error는 놓친다
- `onCompletion`에서만 정리해서 timeout 직후 producer가 계속 돈다
- redispatch 성공 경로에만 cleanup을 두고 timeout/network error에서 누락된다

따라서 portable한 패턴의 핵심은 **모든 terminal signal을 하나의 idempotent cleanup coordinator로 모으고, response 선택은 타입별 callback에서 따로 한다**는 점이다.

## 경계 지도

| signal | servlet 표면 | Spring 표면 | 추천 책임 |
|---|---|---|---|
| async timeout before result | `AsyncListener.onTimeout` | `WebAsyncTask.onTimeout`, `DeferredResult.onTimeout`, `CallableProcessingInterceptor.handleTimeout` | fallback result 선택 + producer stop 신호 |
| async error / disconnect before result | `AsyncListener.onError` | `WebAsyncTask.onError`, `DeferredResult.onError`, `CallableProcessingInterceptor.handleError` | producer stop 신호 + late result unusable 표시 |
| request finished for any reason | `AsyncListener.onComplete` | `WebAsyncTask.onCompletion`, `DeferredResult.onCompletion`, `CallableProcessingInterceptor.afterCompletion` | 최종 리소스 해제, 남은 producer stop backstop |
| new async cycle started | `AsyncListener.onStartAsync` | redispatch 뒤 내부적으로 다시 async 시작될 수 있음 | listener 재등록 |

핵심은 `onComplete`와 `onCompletion`이 "정상 성공 전용"이 아니라 **timeout, network error를 포함한 최종 종료 신호**라는 점이다.

## 휴대성 있는 설계 규칙

### 1. `AsyncListener`는 async cycle 단위로 붙는다

Servlet `AsyncContext.addListener(...)`는 **가장 최근에 시작된 async cycle**에 연결된다.
그래서 redispatch 이후 다시 `startAsync()`가 일어나면, 기존 listener는 새 cycle 이벤트를 자동으로 계속 받는다고 가정하면 안 된다.

portable한 패턴은 `onStartAsync`에서 자기 자신을 새 `AsyncContext`에 다시 붙이는 것이다.

```java
@Override
public void onStartAsync(AsyncEvent event) {
    event.getAsyncContext().addListener(this);
}
```

이 규칙을 놓치면 첫 timeout은 잡는데 다음 redispatch cycle의 disconnect/complete는 놓치는 식의 vendor-dependent 버그가 생긴다.

### 2. redispatch는 성공 경로 중심으로 생각하고, cleanup은 async callback에 둔다

정상 완료에서는 대개 worker가 결과를 만들고 container가 redispatch해서 Spring MVC가 응답을 쓴다.
하지만 timeout이나 network error에서는 application redispatch가 생략될 수 있다.

그래서 다음 가정은 위험하다.

- `HandlerInterceptor.afterCompletion`이 항상 마지막 cleanup 지점일 것
- controller return 이후 한 번 더 dispatcher를 반드시 탈 것
- late write failure도 controller advice/error page에서 통일 처리될 것

`AsyncHandlerInterceptor`가 따로 존재하는 이유도 여기에 가깝다.
즉 **필수 cleanup은 redispatch 결과가 아니라 async lifecycle callback에서 처리**해야 한다.

### 3. container thread callback은 짧고 idempotent해야 한다

`WebAsyncTask.onTimeout`, `WebAsyncTask.onError`, `DeferredResult.onTimeout`, `DeferredResult.onError`, `onCompletion` 계열 callback은 container thread에서 실행된다.

여기서 안전한 일은 보통 아래 정도다.

- cancel token flip
- `Future.cancel(true)`
- timeout fallback 값 결정
- registry remove

여기서 위험한 일은 보통 아래다.

- 오래 걸리는 cleanup I/O
- lock 경쟁이 큰 정리 작업
- 또 다른 blocking remote call

콜백은 "정리 작업 전체를 수행"하기보다 **정리 작업이 더 진행되지 않도록 신호를 닫는 역할**에 가깝게 두는 편이 안전하다.

### 4. late completion은 정상적인 경쟁 상태다

`DeferredResult.setResult(...)`가 `false`를 돌려주거나 `isSetOrExpired()`가 `true`면 이미 request lifetime이 끝난 것이다.
이건 대개 버그라기보다 timeout/error/completion과 producer 완료가 경합한 결과다.

마찬가지로 `Callable`이나 `WebAsyncTask`의 실제 worker body도 timeout 후 조금 늦게 끝날 수 있다.

portable한 패턴은 late completion을 이렇게 다룬다.

- 응답 재시도는 하지 않는다
- observability만 남긴다
- producer/cleanup은 idempotent handle이 한 번만 실행하게 한다

## 타입별 cleanup 패턴

### `Callable`: cleanup reasoning이 필요하면 plain return보다 interceptor나 `WebAsyncTask`

plain `Callable`은 controller 코드 안에서 timeout/error/completion 훅이 바로 보이지 않는다.
그래서 cleanup reasoning이 필요하면 선택지는 둘이다.

- controller-local 정책이면 plain `Callable` 대신 `WebAsyncTask`
- 전역 정책이면 `CallableProcessingInterceptor` 등록

즉 plain `Callable`은 "worker body만 보이는 형태"이고, cleanup을 읽기 쉽게 만들려면 **callback surface를 드러내는 래퍼가 필요하다**.

### `WebAsyncTask`: `Callable`에 cleanup surface를 노출하는 가장 읽기 쉬운 형태

`WebAsyncTask`는 `Callable`을 그대로 쓰면서도 다음을 한 곳에 모은다.

- timeout fallback
- error fallback
- completion cleanup
- executor / timeout override

그래서 controller 단위에서 reasoning해야 하는 경우 `Callable`보다 읽기 쉽다.
핵심 패턴은 단순하다.

- `onTimeout`에서 fallback response + `cancelOnce("timeout")`
- `onError`에서 `cancelOnce("error")`
- `onCompletion`에서 `cancelOnce("completion")` + `releaseOnce()`

### `DeferredResult`: producer가 controller 밖에 있을 때 stop 신호를 가장 명시적으로 붙인다

`DeferredResult`는 결과 생산자가 외부 executor, message callback, broker subscription일 때 잘 맞는다.
대신 request lifetime과 producer lifetime이 가장 쉽게 벌어진다.

따라서 보통 아래 셋을 같이 둔다.

- `onTimeout`: timeout fallback + producer cancel
- `onError`: producer cancel
- `onCompletion`: subscription/scheduler detach + cancel backstop

그리고 producer 쪽에서는 반드시 아래 둘 중 하나를 쓴다.

- `if (!result.isSetOrExpired()) { ... }`
- `boolean accepted = result.setResult(...)`

즉 `DeferredResult`의 핵심은 "나중에 완료한다"가 아니라 **늦게 도착한 결과를 버릴 계약을 먼저 만든다**는 데 있다.

## 코드로 보기

### 1. request-level cleanup을 한 번만 실행하게 만드는 handle

```java
public final class AsyncCleanup {
    private final AtomicBoolean stopOnce = new AtomicBoolean();
    private final AtomicBoolean releaseOnce = new AtomicBoolean();
    private final Consumer<String> stopProducer;
    private final Runnable releaseResources;

    public AsyncCleanup(Consumer<String> stopProducer, Runnable releaseResources) {
        this.stopProducer = stopProducer;
        this.releaseResources = releaseResources;
    }

    public void stop(String reason) {
        if (stopOnce.compareAndSet(false, true)) {
            stopProducer.accept(reason);
        }
    }

    public void release() {
        if (releaseOnce.compareAndSet(false, true)) {
            releaseResources.run();
        }
    }
}
```

### 2. redispatch/restart를 버텨야 하는 `AsyncListener`

```java
public final class ReattachingAsyncCleanupListener implements AsyncListener {
    private final AsyncCleanup cleanup;

    public ReattachingAsyncCleanupListener(AsyncCleanup cleanup) {
        this.cleanup = cleanup;
    }

    @Override
    public void onTimeout(AsyncEvent event) {
        cleanup.stop("timeout");
    }

    @Override
    public void onError(AsyncEvent event) {
        cleanup.stop("error");
    }

    @Override
    public void onComplete(AsyncEvent event) {
        cleanup.stop("complete");
        cleanup.release();
    }

    @Override
    public void onStartAsync(AsyncEvent event) {
        event.getAsyncContext().addListener(this);
    }
}
```

이 listener는 response fallback을 직접 정하지 않는다.
그 역할은 Spring 쪽 callback에 맡기고, 여기서는 **terminal signal을 놓치지 않는 것**만 담당한다.

Spring MVC에서는 보통 `AsyncHandlerInterceptor.afterConcurrentHandlingStarted(...)`나 async를 시작한 filter에서 `request.getAsyncContext().addListener(...)`로 이 listener를 붙인다.
즉 `AsyncListener`는 request-level backstop이고, `WebAsyncTask`/`DeferredResult` callback은 HTTP 결과 선택 surface라고 나눠 보면 읽기가 쉬워진다.

### 3. `Callable` 전역 cleanup은 interceptor에서 붙인다

```java
@Configuration
public class WebMvcAsyncConfig implements WebMvcConfigurer {

    @Override
    public void configureAsyncSupport(AsyncSupportConfigurer configurer) {
        configurer.registerCallableInterceptors(new CallableProcessingInterceptor() {
            @Override
            public <T> Object handleTimeout(NativeWebRequest request, Callable<T> task) {
                cleanupFrom(request).stop("timeout");
                return CallableProcessingInterceptor.RESULT_NONE;
            }

            @Override
            public <T> Object handleError(
                NativeWebRequest request,
                Callable<T> task,
                Throwable t
            ) {
                cleanupFrom(request).stop("error");
                return CallableProcessingInterceptor.RESULT_NONE;
            }

            @Override
            public <T> void afterCompletion(NativeWebRequest request, Callable<T> task) {
                AsyncCleanup cleanup = cleanupFrom(request);
                cleanup.stop("completion");
                cleanup.release();
            }
        });
    }
}
```

plain `Callable`은 이런 interceptor가 없으면 timeout/error/completion cleanup이 controller 코드 바깥으로 숨어 버린다.

### 4. controller-local reasoning이 필요하면 `WebAsyncTask`

```java
@GetMapping("/inventory/{sku}")
public WebAsyncTask<ResponseEntity<InventoryResponse>> inventory(@PathVariable String sku) {
    AsyncCleanup cleanup = new AsyncCleanup(
        reason -> inventoryJobRegistry.cancel(sku, reason),
        () -> inventoryJobRegistry.detach(sku)
    );

    WebAsyncTask<ResponseEntity<InventoryResponse>> task =
        new WebAsyncTask<>(1_800L, asyncExecutor, () ->
            ResponseEntity.ok(inventoryService.read(sku))
        );

    task.onTimeout(() -> {
        cleanup.stop("timeout");
        return ResponseEntity.status(HttpStatus.GATEWAY_TIMEOUT).build();
    });
    task.onError(() -> {
        cleanup.stop("error");
        return ResponseEntity.status(HttpStatus.BAD_GATEWAY).build();
    });
    task.onCompletion(() -> {
        cleanup.stop("completion");
        cleanup.release();
    });

    return task;
}
```

핵심은 timeout/error/completion 세 갈래가 **같은 cleanup handle**로 들어간다는 점이다.

### 5. `DeferredResult`는 late completion을 먼저 받아들인다

```java
@GetMapping("/reports/{id}")
public DeferredResult<ResponseEntity<ReportResponse>> report(@PathVariable long id) {
    DeferredResult<ResponseEntity<ReportResponse>> result = new DeferredResult<>(1_800L);

    Future<?> producer = reportExecutor.submit(() -> {
        try {
            ReportResponse response = reportService.generate(id);
            result.setResult(ResponseEntity.ok(response)); // false면 late completion
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        } catch (Exception e) {
            result.setErrorResult(ResponseEntity.internalServerError().build());
        }
    });

    AsyncCleanup cleanup = new AsyncCleanup(
        reason -> producer.cancel(true),
        () -> reportRegistry.detach(id)
    );

    result.onTimeout(() -> {
        cleanup.stop("timeout");
        if (!result.isSetOrExpired()) {
            result.setErrorResult(ResponseEntity.status(HttpStatus.GATEWAY_TIMEOUT).build());
        }
    });
    result.onError(ex -> cleanup.stop("error"));
    result.onCompletion(() -> {
        cleanup.stop("completion");
        cleanup.release();
    });

    return result;
}
```

여기서 중요한 건 `timeout 응답 작성`과 `producer 취소`를 동시에 두되, 둘 다 여러 번 들어와도 결과가 뒤틀리지 않게 만드는 것이다.

## 실전 시나리오

### 시나리오 1: timeout은 504로 잘 나가는데 외부 polling task가 계속 돈다

대개 `onTimeout`에는 fallback response만 있고 `onCompletion`이나 request-level `AsyncListener`에는 producer 정리가 비어 있다.

### 시나리오 2: `HandlerInterceptor.afterCompletion`에 cleanup을 뒀는데 disconnect에서 leak가 난다

async timeout이나 network error에서 redispatch가 생략되면 interceptor completion만 믿는 설계가 흔히 비어 버린다.

### 시나리오 3: `DeferredResult`에서 `setResult`가 가끔 실패한다

대개 버그라기보다 request가 먼저 timeout/error/completion으로 끝난 것이다.
여기서는 재시도보다 "late completion count"를 남기는 편이 유용하다.

### 시나리오 4: plain `Callable` controller는 읽기 어려운데 `WebAsyncTask`는 이유가 바로 보인다

`Callable`은 cleanup surface가 숨겨져 있고, `WebAsyncTask`는 timeout/error/completion을 controller에서 바로 읽을 수 있기 때문이다.

## 꼬리질문

> Q: `AsyncListener.onComplete`만 있으면 `onTimeout`/`onError`는 필요 없지 않나요?
> 핵심: 최종 해제는 `onComplete`에 모을 수 있지만, timeout/error 시점의 빠른 producer stop과 fallback response 결정은 더 이른 callback이 필요하다.

> Q: `onStartAsync` 재등록은 꼭 필요한가요?
> 핵심: portable하게 보려면 필요하다. listener는 새 async cycle 이벤트를 자동으로 계속 받는다고 가정하면 안 된다.

> Q: plain `Callable` 대신 `WebAsyncTask`를 쓰라는 뜻인가요?
> 핵심: controller-local cleanup reasoning이 필요하면 그렇다. 전역 정책이면 `CallableProcessingInterceptor`도 충분하다.

> Q: `DeferredResult.onCompletion`만 두면 되지 않나요?
> 핵심: backstop으로는 좋지만, timeout 시점의 빠른 fallback/producer stop을 늦추므로 `onTimeout`과 분리하는 편이 낫다.

## 한 줄 정리

servlet async cleanup을 portable하게 만들려면 redispatch 성공 경로만 믿지 말고, `AsyncListener` 재등록 규칙과 Spring async callback을 같은 idempotent cleanup handle로 묶어 timeout, error, completion을 따로 읽히게 설계해야 한다.
