# Virtual-Thread MVC Async Executor Boundaries

> 한 줄 요약: `spring.threads.virtual.enabled`는 Spring Boot의 기본 request-entry thread와 `applicationTaskExecutor`를 virtual-thread 쪽으로 기울일 수 있지만, MVC async 경계는 여전히 따로 존재한다. `Callable`과 `StreamingResponseBody`는 MVC async executor를 타고, 직접 만든 `ResponseBodyEmitter`/`SseEmitter` workload는 `send()`를 호출한 producer thread를 탄다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Virtual Threads(Project Loom)](./virtual-threads-project-loom.md)
> - [Virtual Thread Framework Integration: Spring, JDBC, and `HttpClient`](./virtual-thread-spring-jdbc-httpclient-framework-integration.md)
> - [Servlet Container Timeout and Cancellation Boundaries: Spring MVC and Virtual Threads](./servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads.md)
> - [Streaming Response Abort Surfaces: `StreamingResponseBody`, SSE, and Virtual-Thread Cancellation Gaps](./streaming-response-abort-surfaces-servlet-virtual-threads.md)
> - [`StreamingResponseBody` and `SseEmitter` Terminal Cleanup Matrix](./streamingresponsebody-sseemitter-terminal-cleanup-matrix.md)
> - [Servlet `AsyncListener` Cleanup Patterns for `Callable`, `WebAsyncTask`, and `DeferredResult`](./servlet-asynclistener-cleanup-patterns.md)
> - [Servlet Async Timeout to Downstream HTTP and JDBC Deadline Propagation](./servlet-async-timeout-downstream-deadline-propagation.md)
> - [Thread Interruption and Cooperative Cancellation Playbook](./thread-interruption-cooperative-cancellation-playbook.md)
> - [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](../../spring/spring-mvc-async-deferredresult-callable-dispatch.md)
> - [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](../../spring/spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
> - [Spring `TaskExecutor` / `TaskScheduler` Overload, Queue, and Rejection Semantics](../../spring/spring-taskexecutor-taskscheduler-overload-rejection-semantics.md)

> retrieval-anchor-keywords: virtual thread MVC async executor, spring.threads.virtual.enabled MVC, AsyncSupportConfigurer task executor, applicationTaskExecutor MVC async, Spring Boot virtual thread MVC, Callable executor Spring MVC, StreamingResponseBody executor, StreamingResponseBody Callable boundary, ResponseBodyEmitter executor, SseEmitter executor, emitter send thread, reactive emitter blocking writes, RequestMappingHandlerAdapter taskExecutor, WebMvcAutoConfiguration applicationTaskExecutor, MVC async timeout default, emitter timeout override, virtual thread request thread vs async thread, servlet async executor boundary, MVC async virtual thread mismatch, custom AsyncSupportConfigurer virtual threads

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [Executor Boundary Matrix](#executor-boundary-matrix)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [관측 포인트](#관측-포인트)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

이 주제에서 먼저 분리해야 하는 thread 경계는 세 가지다.

- servlet container가 controller 진입을 실행하는 **request-entry thread**
- Spring MVC가 async return type을 위해 쓰는 **MVC async executor**
- `SseEmitter.send(...)`, scheduler, broker listener, `CompletableFuture` callback이 실제로 돌아가는 **producer thread**

`spring.threads.virtual.enabled`를 켰다고 해서 이 셋이 자동으로 하나가 되지는 않는다.

- Spring Boot는 이 속성으로 embedded servlet container request handling과 `applicationTaskExecutor` 기본값을 virtual-thread 쪽으로 바꿀 수 있다
- 하지만 `Callable`/`StreamingResponseBody`는 여전히 controller return 이후 MVC async executor로 hop한다
- 직접 만든 `ResponseBodyEmitter`/`SseEmitter`는 MVC async executor가 아니라 `send()`를 호출한 producer 쪽 executor/scheduler를 따른다

즉 질문은 "virtual thread를 켰나?"보다 **"어느 workload가 request-entry thread를 끝까지 쓰고, 어느 workload가 MVC async executor나 detached producer executor로 갈라지나?"**다.

## Executor Boundary Matrix

| workload | async를 시작하는 방식 | 실제 body/result work를 수행하는 쪽 | `spring.threads.virtual.enabled` 영향 | `AsyncSupportConfigurer#setTaskExecutor(...)` 영향 | 흔한 오해 |
|---|---|---|---|---|---|
| `Callable` / `WebAsyncTask` | controller가 `Callable`을 반환 | MVC async executor | Boot 기본 `applicationTaskExecutor`가 virtual-thread 쪽으로 바뀔 수 있음 | **직접 영향 있음** | request-entry thread가 계속 이어진다고 착각 |
| `StreamingResponseBody` | handler가 내부적으로 `Callable`로 감싸 `startCallableProcessing(...)` | MVC async executor 위 writer task | Boot 기본 executor를 쓸 때만 간접 영향 | **직접 영향 있음** | streaming이면 emitter처럼 producer thread가 따로라고 착각 |
| 직접 반환한 `ResponseBodyEmitter` / `SseEmitter` | handler가 `DeferredResult` async lifecycle만 시작 | `emitter.send(...)`를 호출한 thread | producer가 Boot 기본 executor를 따로 쓰지 않는 한 영향 없음 | send thread에는 **직접 영향 없음** | emitter도 MVC async executor가 대신 써 준다고 착각 |
| reactive type이 emitter로 적응되는 경우 (`Flux<ServerSentEvent<?>>`, NDJSON 등) | `ReactiveTypeHandler`가 emitter를 만들고 subscriber를 연결 | blocking write를 스케줄링하는 MVC async executor | Boot 기본 executor를 쓸 때 영향 있음 | **직접 영향 있음** | direct emitter와 reactive streaming을 같은 경계로 취급 |
| emitter timeout | `DeferredResult` async lifecycle | thread 실행이 아니라 request timeout budget | 직접 영향 없음 | **default timeout에 영향 있음** | timeout 설정이 producer executor까지 자동 취소한다고 착각 |

표를 읽는 핵심은 단순하다.

- `Callable`과 `StreamingResponseBody`는 executor 경계상 같은 축이다
- direct emitter는 timeout/lifecycle은 MVC async에 걸치지만, write 실행 주체는 애플리케이션 producer 쪽이다
- "emitter workload"라고 해도 direct emitter와 reactive-to-emitter는 executor ownership이 다르다

## 깊이 들어가기

### 1. `spring.threads.virtual.enabled`는 Spring Boot 기본값을 두 군데에서 바꾼다

Spring Framework 자체는 `spring.threads.virtual.enabled`를 모른다.  
이 속성은 Spring Boot가 해석하는 기본값 스위치다.

실제로는 보통 두 군데가 갈라진다.

- Tomcat/Jetty 같은 supported embedded servlet container의 request handling executor
- `applicationTaskExecutor` 기본 bean

그래서 이 속성이 켜져 있으면 "controller 진입 thread도 virtual", "MVC async 기본 executor도 virtual"이 동시에 될 수 있다.  
하지만 이 둘은 **같은 thread**가 아니라 **서로 다른 경계**다.

즉 controller가 virtual thread에서 시작해도, `Callable`이나 `StreamingResponseBody`는 그 뒤 다른 virtual thread로 hop할 수 있다.

### 2. `AsyncSupportConfigurer#setTaskExecutor(...)`는 MVC async 경계를 다시 그린다

Spring MVC는 최종적으로 `RequestMappingHandlerAdapter`의 `taskExecutor`를 보고 async 작업을 실행한다.  
Spring Boot는 `applicationTaskExecutor`가 있으면 `configureAsyncSupport(...)`에서 그 executor를 넣어 주지만, 여기서 끝이 아니다.

애플리케이션이 `WebMvcConfigurer#configureAsyncSupport(...)`에서 `setTaskExecutor(...)`를 호출하면 MVC async 경계는 그 executor 기준으로 다시 잡힌다.

중요한 점은 범위다.

- `Callable`
- `WebAsyncTask`
- `StreamingResponseBody`
- reactive type streaming의 blocking write

여기까지는 MVC async executor 경계 안이다.

반대로 다음은 아니다.

- direct `SseEmitter`를 보내는 scheduler
- controller 밖의 message listener
- app이 직접 만든 `CompletableFuture` callback executor

즉 `setTaskExecutor(...)`는 **MVC가 소유하는 async hop**을 바꾸는 설정이지, app 안의 모든 async producer를 몰수하는 설정이 아니다.

### 3. `StreamingResponseBody`는 문서상보다 더 강하게 `Callable` 축에 붙어 있다

Spring MVC reference는 `AsyncTaskExecutor`를 주로 `Callable`과 reactive blocking writes에 대해 설명한다.  
하지만 구현을 보면 `StreamingResponseBodyReturnValueHandler`는 `StreamingResponseBody`를 내부 `Callable`로 감싸서 `WebAsyncManager.startCallableProcessing(...)`로 넘긴다.

이 말은 곧 다음을 뜻한다.

- `StreamingResponseBody` writer는 MVC async executor를 탄다
- global async timeout과 `CallableProcessingInterceptor` 축을 공유한다
- custom `AsyncSupportConfigurer#setTaskExecutor(...)`가 있으면 그 executor를 따른다

따라서 `spring.threads.virtual.enabled=true`여도 custom MVC async executor를 platform `ThreadPoolTaskExecutor`로 두면, request-entry는 virtual thread인데 download writer는 platform pool에서 도는 조합이 나올 수 있다.

### 4. direct `ResponseBodyEmitter` / `SseEmitter`는 lifecycle과 send thread를 분리해서 봐야 한다

`ResponseBodyEmitterReturnValueHandler`는 direct emitter를 받을 때 `startDeferredResultProcessing(...)`로 async request lifecycle을 연다.  
하지만 실제 `send(...)`는 `DefaultSseEmitterHandler`가 **그 메서드를 호출한 thread**에서 converter write와 `flush()`를 수행한다.

즉 direct emitter에서 MVC async 쪽이 맡는 것은 주로 이쪽이다.

- request를 async mode로 열어 두는 것
- default timeout 적용
- error/completion redispatch lifecycle

반대로 애플리케이션이 직접 소유하는 것은 이쪽이다.

- 어떤 scheduler/executor가 heartbeat를 보내는가
- 어떤 broker listener가 event를 읽는가
- 어떤 thread가 `emitter.send(...)`를 호출하는가

그래서 `spring.threads.virtual.enabled`를 켰는데도 direct SSE send path가 platform thread에서 도는 것은 이상한 일이 아니다.  
scheduler나 producer executor를 따로 그렇게 만들었기 때문이다.

### 5. reactive type이 emitter로 적응될 때는 direct emitter와 해석이 달라진다

`Flux<ServerSentEvent<?>>`, `Flux<String>`, NDJSON streaming 같은 reactive multi-value return은 `ReactiveTypeHandler`가 emitter로 적응한다.  
이 경로에서는 subscriber가 next signal을 바로 쓰지 않고, blocking write를 `TaskExecutor`에 스케줄한다.

즉 reactive streaming은 겉보기엔 emitter 계열이지만 executor ownership은 direct emitter보다 `Callable` 쪽에 더 가깝다.

- `spring.threads.virtual.enabled`로 Boot 기본 MVC executor가 virtual이면 write task도 virtual thread에서 실행될 수 있다
- custom `AsyncSupportConfigurer#setTaskExecutor(...)`가 있으면 그 executor를 따른다
- upstream reactive publisher thread와 response write thread는 분리될 수 있다

그래서 "SSE니까 direct emitter와 같겠지"라고 보면 trace와 cancellation reasoning이 자주 꼬인다.

### 6. timeout은 executor 선택과 별도 축이다

`AsyncSupportConfigurer#setDefaultTimeout(...)`은 MVC async request의 기본 timeout budget을 정한다.  
하지만 return type별로 덮어쓰는 지점이 다르다.

- `Callable`: global default 또는 `WebAsyncTask` per-request timeout
- `StreamingResponseBody`: global async timeout
- `ResponseBodyEmitter` / `SseEmitter`: 생성자 timeout이 있으면 그 값이 우선, 없으면 global async timeout

여기서 중요한 오해는 "timeout을 맞췄으니 producer도 자동 중단된다"는 기대다.

- direct emitter timeout은 scheduler cancel을 자동 보장하지 않는다
- `StreamingResponseBody` timeout은 JDBC/file read를 자동 cancel하지 않는다
- executor를 virtual thread로 바꿔도 cancel ownership은 그대로 설계해야 한다

## 실전 시나리오

### 시나리오 1: 속성만 켰는데 `Callable`과 SSE heartbeat thread 이름이 다르다

Boot 기본값만 쓰면 `Callable`은 `applicationTaskExecutor` 쪽 virtual thread를 탈 수 있다.  
하지만 SSE heartbeat를 `ScheduledExecutorService`나 별도 scheduler에서 보내면, direct emitter send path는 그 scheduler thread 이름을 보게 된다.

이건 설정 누락이 아니라 executor ownership 차이다.

### 시나리오 2: `spring.threads.virtual.enabled=true`인데 `StreamingResponseBody`는 platform pool에서 돈다

`configureAsyncSupport(...)`에서 custom `ThreadPoolTaskExecutor`를 넣었다면 정상이다.

- request-entry: container virtual thread
- `StreamingResponseBody.writeTo(...)`: custom MVC async pool

즉 property보다 explicit MVC config가 더 가까운 경계에서 우선한다.

### 시나리오 3: direct `SseEmitter`에 virtual thread를 기대했는데 producer가 그대로 남는다

controller가 `SseEmitter`를 return한 뒤 event 발행이 broker listener나 polling scheduler에서 계속 일어나면, 그 sender가 실제 write thread다.  
MVC async executor는 request lifecycle만 열어 둘 뿐 producer를 대신 실행하지 않는다.

그래서 여기서는 `AsyncSupportConfigurer`보다 scheduler/broker/subscription ownership을 먼저 봐야 한다.

### 시나리오 4: `Flux<ServerSentEvent<?>>`와 `SseEmitter`를 같은 observability로 본다

둘 다 브라우저에는 SSE처럼 보이지만 thread timeline은 다를 수 있다.

- `Flux<ServerSentEvent<?>>`: MVC async executor가 blocking writes를 담당
- direct `SseEmitter`: producer가 호출한 thread가 직접 write

같은 metric 이름으로 뭉개면 queue saturation과 late send 원인을 잘못 해석하기 쉽다.

## 코드로 보기

### 1. MVC async executor를 명시적으로 고정하기

```java
@Configuration
class MvcAsyncConfig implements WebMvcConfigurer {

    private final AsyncTaskExecutor mvcAsyncExecutor;

    MvcAsyncConfig(@Qualifier("mvcAsyncExecutor") AsyncTaskExecutor mvcAsyncExecutor) {
        this.mvcAsyncExecutor = mvcAsyncExecutor;
    }

    @Override
    public void configureAsyncSupport(AsyncSupportConfigurer configurer) {
        configurer.setTaskExecutor(this.mvcAsyncExecutor);
        configurer.setDefaultTimeout(30_000L);
    }
}
```

이렇게 두면 Boot가 `spring.threads.virtual.enabled`로 만든 기본 `applicationTaskExecutor`가 있더라도, MVC async 경계는 여기서 지정한 executor를 따른다.

### 2. 같은 controller 안에서도 workload별 thread ownership이 달라진다

```java
@RestController
class AsyncDemoController {

    private final ScheduledExecutorService sseScheduler =
            Executors.newSingleThreadScheduledExecutor();

    @GetMapping("/callable")
    Callable<String> callable() {
        return () -> "callable on " + Thread.currentThread();
    }

    @GetMapping("/download")
    StreamingResponseBody download() {
        return outputStream -> {
            outputStream.write(("stream on " + Thread.currentThread()).getBytes(StandardCharsets.UTF_8));
            outputStream.flush();
        };
    }

    @GetMapping(path = "/events", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    SseEmitter events() {
        SseEmitter emitter = new SseEmitter(30_000L);
        this.sseScheduler.scheduleAtFixedRate(() -> {
            try {
                emitter.send(SseEmitter.event().data("send on " + Thread.currentThread()));
            }
            catch (IOException ex) {
                // disconnect나 timeout 이후 producer cleanup은 여기서 멈춘다.
            }
        }, 0, 5, TimeUnit.SECONDS);
        return emitter;
    }
}
```

이 예제에서 thread ownership은 보통 이렇게 읽는다.

- `/callable`: MVC async executor
- `/download`: MVC async executor
- `/events`: `sseScheduler` thread

즉 `SseEmitter`는 direct producer를 밖에서 어떻게 붙였는지가 핵심이다.

### 3. reactive emitter adaptation은 다시 MVC async executor 쪽으로 돌아온다

```java
@GetMapping(path = "/flux-events", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
Flux<ServerSentEvent<String>> fluxEvents() {
    return Flux.interval(Duration.ofSeconds(1))
            .map(seq -> ServerSentEvent.builder("seq=" + seq).build());
}
```

이 경우 publisher signal과 response write는 같은 thread일 필요가 없다.  
Spring MVC는 blocking response write를 MVC async executor에 올릴 수 있기 때문이다.

## 관측 포인트

- controller entry, `Callable.call()`, `StreamingResponseBody.writeTo()`, `emitter.send()`에 각각 thread name을 남겨 executor 경계를 분리한다
- direct emitter라면 MVC async executor metric보다 producer scheduler/subscription metric이 더 중요하다
- `AsyncRequestTimeoutException`, `onTimeout`, `onCompletion`은 request lifetime signal이지 producer stop 보장이 아님을 분리 기록한다
- `streamingResponseBody`와 direct `SseEmitter`는 둘 다 streaming이어도 다른 executor tag를 붙여야 late write와 backlog를 구분하기 쉽다

## 트레이드오프

- `spring.threads.virtual.enabled`는 기본 구성을 단순하게 하지만, "모든 async가 virtual thread"라는 착시를 만들기 쉽다
- custom `AsyncSupportConfigurer`는 `Callable`/`StreamingResponseBody` backpressure를 제어하기 좋지만, direct emitter producer까지 정리해 주지는 않는다
- direct emitter는 producer ownership이 명확한 대신 scheduler leak와 timeout-cleanup gap을 스스로 관리해야 한다
- reactive emitter adaptation은 backpressure 해석이 쉬운 대신 direct emitter보다 thread hop이 덜 직관적일 수 있다

## 꼬리질문

- 지금 보고 있는 endpoint는 direct `SseEmitter`인가, reactive type이 emitter로 적응된 경우인가?
- `spring.threads.virtual.enabled`가 바꾼 것은 request-entry thread인가, `applicationTaskExecutor`인가, 둘 다인가?
- `configureAsyncSupport(...)`에서 custom executor를 넣었다면 그 executor가 실제로 `Callable`/`StreamingResponseBody` 경계를 먹고 있는가?
- timeout이 났을 때 끊고 싶은 대상은 request lifetime인가, producer scheduler인가, JDBC/HTTP downstream인가?

## 한 줄 정리

`spring.threads.virtual.enabled`는 Boot 기본 request-entry thread와 `applicationTaskExecutor`를 virtual-thread 쪽으로 바꿀 수 있지만, MVC async 경계는 그대로 남는다. 그래서 `Callable`과 `StreamingResponseBody`는 MVC async executor를 따르고, direct `ResponseBodyEmitter`/`SseEmitter`는 `send()`를 호출한 producer thread를 따른다.
