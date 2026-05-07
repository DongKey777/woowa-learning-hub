---
schema_version: 3
title: Streaming Response Abort Surfaces Servlet Virtual Threads
concept_id: language/streaming-response-abort-surfaces-servlet-virtual-threads
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
- streaming
- servlet-async
- cancellation
aliases:
- Streaming Response Abort Surfaces Servlet Virtual Threads
- StreamingResponseBody disconnect broken pipe
- SseEmitter disconnect abort surface
- AsyncRequestNotUsableException streaming
- virtual thread streaming cancellation gap
- streaming orphan work cleanup
symptoms:
- StreamingResponseBody나 SseEmitter에서 client disconnect가 controller return 시점에 즉시 보인다고 생각해 다음 write flush send 전까지 producer가 계속 도는 gap을 놓쳐
- virtual thread를 쓰면 streaming writer와 downstream I/O가 자동으로 cancel될 것이라고 기대해 JDBC cursor, remote download, scheduler cleanup을 연결하지 않아
- response committed 이후 broken pipe를 application error response로 재작성하려고 하거나 late write failure를 새 장애로 반복 로깅해
intents:
- troubleshooting
- deep_dive
- design
prerequisites:
- language/servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads
- language/mvc-async-executor-boundaries
- language/servlet-asynclistener-cleanup-patterns
next_docs:
- language/streamingresponsebody-sseemitter-terminal-cleanup-matrix
- language/jdbc-cursor-cleanup-download-abort
- spring/streamingresponsebody-responsebodyemitter-sse-commit-lifecycle
linked_paths:
- contents/language/java/servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads.md
- contents/language/java/virtual-thread-mvc-async-executor-boundaries.md
- contents/language/java/servlet-asynclistener-cleanup-patterns.md
- contents/language/java/streamingresponsebody-sseemitter-terminal-cleanup-matrix.md
- contents/language/java/virtual-thread-spring-jdbc-httpclient-framework-integration.md
- contents/language/java/virtual-thread-jdbc-cancel-semantics.md
- contents/language/java/jdbc-cursor-cleanup-download-abort.md
- contents/language/java/thread-interruption-cooperative-cancellation-playbook.md
- contents/language/java/completablefuture-cancellation-semantics.md
- contents/spring/spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md
- contents/spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md
- contents/spring/spring-servlet-container-disconnect-exception-mapping.md
- contents/spring/spring-sse-proxy-idle-timeout-matrix.md
- contents/network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md
confusable_with:
- language/streamingresponsebody-sseemitter-terminal-cleanup-matrix
- language/servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads
- language/servlet-asynclistener-cleanup-patterns
forbidden_neighbors: []
expected_queries:
- StreamingResponseBody와 SseEmitter에서 client disconnect는 어떤 abort surface에서 처음 보이나?
- streaming response broken pipe는 다음 write flush send에서 늦게 보일 수 있다는 뜻을 설명해줘
- virtual thread streaming writer를 써도 producer와 JDBC cursor downstream I/O가 자동 취소되지 않는 이유가 뭐야?
- response committed 이후에는 상태 코드나 JSON error를 재작성하지 못하고 cleanup과 late write suppression이 핵심이야?
- StreamingResponseBody disconnect와 SseEmitter disconnect cleanup ownership을 비교해줘
contextual_chunk_prefix: |
  이 문서는 StreamingResponseBody와 SseEmitter의 disconnect/abort surface를 next write/flush/send, async callback, container exception, virtual-thread cancellation gap 관점에서 진단하는 advanced playbook이다.
  streaming response abort, StreamingResponseBody, SseEmitter, broken pipe, AsyncRequestNotUsableException 질문이 본 문서에 매핑된다.
---
# Streaming Response Abort Surfaces: `StreamingResponseBody`, SSE, and Virtual-Thread Cancellation Gaps

> 한 줄 요약: `StreamingResponseBody`와 SSE는 abort가 controller return 시점이 아니라 다음 `write`/`flush`, emitter callback, container-specific disconnect 예외에서 늦게 surface되며, virtual thread를 써도 그 신호가 producer나 downstream I/O 취소로 자동 번역되지는 않는다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Servlet Container Timeout and Cancellation Boundaries: Spring MVC and Virtual Threads](./servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads.md)
> - [Virtual-Thread MVC Async Executor Boundaries](./virtual-thread-mvc-async-executor-boundaries.md)
> - [Servlet `AsyncListener` Cleanup Patterns for `Callable`, `WebAsyncTask`, and `DeferredResult`](./servlet-asynclistener-cleanup-patterns.md)
> - [`StreamingResponseBody` and `SseEmitter` Terminal Cleanup Matrix](./streamingresponsebody-sseemitter-terminal-cleanup-matrix.md)
> - [Virtual Thread Framework Integration: Spring, JDBC, and `HttpClient`](./virtual-thread-spring-jdbc-httpclient-framework-integration.md)
> - [Virtual-Thread JDBC Cancel Semantics](./virtual-thread-jdbc-cancel-semantics.md)
> - [JDBC Cursor Cleanup on Download Abort](./jdbc-cursor-cleanup-download-abort.md)
> - [Thread Interruption and Cooperative Cancellation Playbook](./thread-interruption-cooperative-cancellation-playbook.md)
> - [CompletableFuture Cancellation Semantics](./completablefuture-cancellation-semantics.md)
> - [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](../../spring/spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
> - [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](../../spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
> - [Spring Servlet Container Disconnect Exception Mapping](../../spring/spring-servlet-container-disconnect-exception-mapping.md)
> - [Spring SSE Proxy Idle-Timeout Matrix](../../spring/spring-sse-proxy-idle-timeout-matrix.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](../../network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)

> retrieval-anchor-keywords: streaming response abort, StreamingResponseBody disconnect, StreamingResponseBody broken pipe, SSE disconnect, SseEmitter disconnect, late write failure, response streaming cancellation gap, servlet container disconnect, async streaming abort surface, AsyncRequestNotUsableException, ClientAbortException, EofException, ClosedChannelException, response committed broken pipe, streaming terminal cleanup matrix, producer cancel vs writer failure, late write suppression, virtual thread streaming executor, spring.threads.virtual.enabled, request lifetime vs stream lifetime, heartbeat disconnect detection, streaming orphan work, after commit write failure, servlet async streaming cancel, download abort JDBC cursor cleanup, streaming export broken pipe query cancel

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [Abort Surface 지도](#abort-surface-지도)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [관측 포인트](#관측-포인트)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

스트리밍 응답 abort를 읽을 때는 "요청이 끝났다"를 하나로 보면 거의 항상 해석이 틀어진다.

실제로는 최소 네 수명이 따로 돈다.

- client, proxy, browser가 기다리는 **response lifetime**
- servlet container가 `AsyncContext`와 connection을 붙들고 있는 **request lifetime**
- `StreamingResponseBody` callback, SSE scheduler, `CompletableFuture`, broker subscription 같은 **producer lifetime**
- JDBC, outbound HTTP, 파일 읽기 같은 **downstream I/O lifetime**

abort는 이 수명 중 하나가 끝났다고 해서 즉시 모두에게 알려지지 않는다.

- client가 탭을 닫아도 서버는 다음 바이트를 쓸 때까지 모를 수 있다
- servlet async timeout이 나도 producer task는 계속 돌 수 있다
- virtual thread가 cheap해져도 DB query, remote call, scheduler는 자동으로 멈추지 않는다

핵심 질문은 "disconnect가 났는가?"가 아니라 **"disconnect 신호가 어느 surface에서 처음 보이고, 그 다음 lifetime들을 누가 실제로 닫는가?"**다.

## Abort Surface 지도

| 경로 | abort가 처음 잘 보이는 자리 | 흔한 실행 주체 | 자동으로 일어나지 않는 것 |
|---|---|---|---|
| `StreamingResponseBody` | `OutputStream.write()` / `flush()` / `close()`의 `IOException`, 이후 `AsyncRequestNotUsableException` | MVC async executor의 writer thread | row producer, DB cursor/query, remote download 자동 중단 |
| `SseEmitter` | 다음 `send(...)` 또는 heartbeat, `onError`, `onCompletion` | emitter에 쓰는 producer thread + container callback thread | heartbeat scheduler, broker subscription, detached future 정리 |
| first-byte 이후 late write failure | Tomcat `ClientAbortException`, Jetty `EofException`, Undertow `ClosedChannelException`/`IOException`, Spring wrapper | container write path / Spring wrapper | 상태 코드/JSON error 재작성 |
| proxy/client가 먼저 포기했지만 서버가 아직 모름 | access log `499`/`504`, 다음 write에서 broken pipe | proxy, gateway, 다음 chunk writer | 현재 handler 또는 writer thread interrupt 보장 |
| servlet async timeout | `onTimeout`, timeout redispatch, 경우에 따라 `AsyncRequestTimeoutException` | container thread | producer, JDBC, outbound HTTP, retry loop 취소 |

표의 핵심은 단순하다.  
스트리밍 abort는 보통 **"다음 바이트를 쓰려는 순간"**이나 **"async lifecycle callback"**에서 surface되고, 그 전까지는 내부 작업이 조용히 남아 있을 수 있다.

## 깊이 들어가기

### 1. `StreamingResponseBody`는 request thread보다 writer thread 경계가 더 중요하다

`StreamingResponseBody`는 controller가 return한 뒤 Spring MVC async 경로에서 body writer callback이 실행된다.  
즉 request 진입 thread와 실제 stream writer는 종종 같은 실행 경계가 아니다.

여기서 흔한 오해가 두 가지다.

- `spring.threads.virtual.enabled`를 켰으니 streaming writer도 무조건 같은 request virtual thread에서 돈다
- client disconnect가 나면 writer thread가 바로 interrupt된다

둘 다 portable하게 기대하면 안 된다.

- MVC async 처리에는 별도의 executor 선택이 개입한다
- Spring Boot 기본 구성에서는 auto-configured async executor를 따라가는 경우가 많지만, `AsyncSupportConfigurer`나 custom `applicationTaskExecutor`를 두면 그 선택이 우선한다
- client disconnect는 대개 writer가 다음 `write`/`flush`를 시도할 때 `IOException` 계열로 보이지, "현재 writer를 즉시 interrupt"하는 계약으로 보장되지 않는다

즉 `StreamingResponseBody`에서 virtual thread를 쓴다는 것은 "writer를 어떤 executor에 올릴지"의 문제일 뿐, **abort detection과 cancellation ownership**을 해결하는 문제는 아니다.

### 2. `StreamingResponseBody`는 `flush()` 간격이 곧 abort detection 간격이다

`StreamingResponseBody`는 애플리케이션이 `OutputStream`에 직접 쓴다.  
그래서 abort를 언제 관측하는지도 flush cadence에 크게 좌우된다.

- `write()`만 오래 하고 `flush()`를 늦게 하면 peer 종료를 늦게 본다
- 적절한 batch마다 `flush()`하면 disconnect를 더 빨리 surface할 수 있다
- 너무 자주 `flush()`하면 syscall/TLS/proxy overhead가 커질 수 있다

즉 `flush()`는 단지 UX를 위해 first byte를 빨리 보내는 knob가 아니다.  
운영 관점에서는 **"abort를 얼마나 빨리 알 것인가"**와도 연결된다.

### 3. SSE는 다음 event나 heartbeat가 와야 disconnect를 알기 쉽다

SSE는 특히 "연결은 이미 죽었는데 서버는 아직 모른다"는 현상이 잘 보이는 경로다.

- 브라우저 탭 종료
- mobile network 전환
- proxy idle timeout
- LB/CDN buffering 뒤 선종료

이런 경우도 서버는 다음 SSE event 또는 heartbeat를 보내기 전까지 정상 연결처럼 착각할 수 있다.

그래서 SSE에서는 heartbeat가 두 역할을 한다.

- idle timeout을 넘기지 않게 하는 keepalive
- disconnect를 더 빨리 surface하는 probe

반대로 heartbeat가 없으면, abort는 business event가 다시 생길 때까지 늦게 드러날 수 있다.

### 4. `SseEmitter`의 진짜 정리 지점은 `onCompletion`이다

`SseEmitter`는 `onTimeout`, `onError`, `onCompletion`을 제공한다.  
실전에서 가장 중요한 것은 `onCompletion`을 "정상 종료 후처리"가 아니라 **request lifetime 종료 backstop**으로 보는 것이다.

이유는 간단하다.

- timeout이어도 `onCompletion`이 온다
- disconnect여도 `onCompletion`이 온다
- 정상 종료여도 `onCompletion`이 온다

따라서 다음 리소스는 `onCompletion`에서 반드시 끊는 편이 안전하다.

- heartbeat scheduler
- broker subscription
- polling task
- detached future graph

`onTimeout`과 `onError`는 이유별 추가 정책을 얹는 곳이고, **"무조건 정리"는 `onCompletion`**에 두는 쪽이 더 휴대성이 높다.

### 5. late write failure는 "응답 생성 실패"보다 "commit 이후 전송 실패"에 가깝다

첫 chunk, 첫 SSE event, 첫 `flush()`가 나간 뒤에는 응답 메타데이터 ownership이 거의 닫힌다.

그 다음 실패는 보통 이런 shape로 보인다.

- Tomcat: `ClientAbortException`
- Jetty: `EofException`
- Undertow: `ClosedChannelException` 또는 일반 `IOException`
- Spring async wrapper: `AsyncRequestNotUsableException`

이 지점에서 중요한 해석은 "에러 envelope를 어떻게 예쁘게 만들까?"가 아니다.

- 상태 코드는 이미 나갔을 수 있다
- JSON `ProblemDetail`로 갈아엎기 어렵다
- access log는 `200`/`206`인데 body 전송은 중간에 끊겼을 수 있다

즉 late write failure는 애플리케이션 계약보다 **transport-phase 관측 이벤트**에 가깝다.

### 6. virtual thread는 cancellation gap을 감추기 더 쉬운 환경을 만든다

virtual thread 이후엔 "끊기지 않은 작업"이 thread starvation으로 바로 티 나지 않을 수 있다.

- request writer가 cheap한 virtual thread 위에서 계속 대기한다
- detached `CompletableFuture`가 별도 executor에서 계속 fan-out한다
- JDBC query가 statement timeout 전까지 계속 실행된다
- SSE heartbeat scheduler가 subscriber가 사라진 뒤에도 계속 돈다

즉 orphan work가 덜 아픈 것이 아니라, **겉으로 덜 시끄러워질 뿐**이다.

그래서 streaming abort 처리에서는 보통 신호를 세 겹으로 묶는다.

- request lifetime 종료 표면: `onCompletion`, `IOException`, `AsyncListener`
- task 종료 표면: `Future.cancel(true)`, stop token, subscription dispose
- downstream 종료 표면: JDBC statement timeout/cancel, outbound HTTP timeout/cancel, file handle close

virtual thread는 이 wiring을 대체하지 않는다.

### 7. "writer가 실패했다"와 "producer가 멈췄다"를 따로 기록해야 gap이 보인다

운영에서 가장 흔한 blind spot은 여기다.

- app log에는 `ClientAbortException`이 남았다
- 하지만 DB query cancel 기록은 없다
- SSE `onCompletion`은 왔지만 scheduler cancel metric은 없다

이 경우 시스템은 "abort를 관측"했지만 "실제 cleanup"은 못 했을 가능성이 높다.

즉 스트리밍 endpoint는 예외 건수만으로 보지 말고, 최소한 다음 둘을 분리해 기록해야 한다.

- `response_aborted`
- `producer_cancelled`

두 지표가 항상 같이 오르지 않으면 cancellation gap이 숨어 있을 수 있다.

## 실전 시나리오

### 시나리오 1: `StreamingResponseBody` 다운로드를 중간 취소했는데 export query는 몇 초 더 돈다

흔한 타임라인은 이렇다.

```text
client cancels download
-> servlet container/socket is effectively closed
-> app is still mapping or fetching next rows
-> next write/flush surfaces broken pipe
-> query keeps running until statement timeout or explicit cancel
```

문제는 `StreamingResponseBody` 자체가 아니라 **late write failure와 query cancel을 연결하지 않은 것**이다.

### 시나리오 2: SSE는 잘 붙는데 브라우저 탭을 닫은 뒤에도 scheduler가 계속 돈다

heartbeat나 다음 event 전까지 disconnect를 늦게 알 수 있다.  
거기에 `onCompletion`에서 scheduler/subscription cleanup을 하지 않았다면 task leak가 남는다.

즉 "SSE reconnect가 많다"와 "SSE cleanup이 안전하다"는 전혀 다른 문제다.

### 시나리오 3: virtual thread를 켠 뒤 `AsyncRequestNotUsableException`이 더 눈에 띈다

이건 보통 Loom bug가 아니라 다음 둘 중 하나다.

- write 이후 response가 이미 unusable/completed가 됐는데 producer가 계속 쓴다
- disconnect를 빨리 못 본 상태에서 detached work가 늦게 write를 시도한다

즉 virtual thread 전환이 실패를 만든 게 아니라, **기존 cancellation gap을 더 많이 노출**했을 가능성이 크다.

### 시나리오 4: gateway는 504인데 backend SSE producer는 정상처럼 계속 event를 만든다

gateway deadline이나 proxy idle timeout이 app의 async timeout보다 먼저 끝났을 수 있다.  
app이 다음 send/heartbeat 전까지 disconnect를 못 보면 producer는 계속 돈다.

이 경우 필요한 것은 더 빠른 thread가 아니라:

- heartbeat 간격 재설계
- app async timeout 정렬
- producer cancel wiring

이다.

## 코드로 보기

### `StreamingResponseBody`: late write failure를 stop signal로 연결하기

```java
@GetMapping(value = "/exports/orders", produces = MediaType.APPLICATION_NDJSON_VALUE)
public ResponseEntity<StreamingResponseBody> exportOrders() {
    AtomicBoolean stop = new AtomicBoolean();

    StreamingResponseBody body = outputStream -> {
        try (BufferedWriter writer =
                 new BufferedWriter(new OutputStreamWriter(outputStream, StandardCharsets.UTF_8))) {
            int count = 0;
            for (OrderRow row : exportService.streamRows(stop)) {
                if (stop.get() || Thread.currentThread().isInterrupted()) {
                    return;
                }

                writer.write(toNdjson(row));
                writer.newLine();

                if (++count % 100 == 0) {
                    writer.flush(); // disconnect가 가장 자주 surface되는 지점
                }
            }
            writer.flush();
        } catch (IOException ex) {
            stop.set(true); // 별도 producer/query cancel wiring의 입력 신호
            throw ex;
        }
    };

    return ResponseEntity.ok(body);
}
```

이 코드의 핵심은 `IOException`을 "응답 쓰기 실패"로만 보지 않고 **producer 중단 신호의 시작점**으로 쓰는 데 있다.  
실제 서비스에서는 여기에 request-level `AsyncListener`, in-flight statement registry, remote client cancel을 추가로 연결해야 orphan work가 줄어든다.

### `SseEmitter`: heartbeat와 cleanup을 같은 handle로 묶기

```java
@GetMapping("/events/orders")
public SseEmitter orderEvents() {
    SseEmitter emitter = new SseEmitter(60_000L);
    AtomicBoolean closed = new AtomicBoolean();

    BrokerSubscription subscription = broker.subscribe(event -> {
        if (closed.get()) {
            return;
        }
        try {
            emitter.send(SseEmitter.event()
                .name("order-updated")
                .data(event));
        } catch (IOException ex) {
            emitter.completeWithError(ex);
        }
    });

    ScheduledFuture<?> heartbeat = scheduler.scheduleAtFixedRate(() -> {
        if (closed.get()) {
            return;
        }
        try {
            emitter.send(SseEmitter.event().comment("keepalive"));
        } catch (IOException ex) {
            emitter.completeWithError(ex);
        }
    }, 15, 15, TimeUnit.SECONDS);

    Runnable closeOnce = () -> {
        if (closed.compareAndSet(false, true)) {
            heartbeat.cancel(true);
            subscription.dispose();
        }
    };

    emitter.onTimeout(closeOnce);
    emitter.onError(ex -> closeOnce.run());
    emitter.onCompletion(closeOnce);

    return emitter;
}
```

포인트는 세 가지다.

- heartbeat가 있어야 disconnect를 너무 늦게 알지 않는다
- `onCompletion`이 cleanup backstop이다
- `completeWithError(...)`는 JSON error 복구가 아니라 async lifecycle 종료 신호에 가깝다

## 관측 포인트

스트리밍 abort는 raw 예외 개수보다 phase tagging이 더 중요하다.

| 태그 | 왜 필요한가 |
|---|---|
| `stream_type=streaming_response_body|sse` | 어느 surface에서 abort가 보였는지 구분 |
| `container=tomcat|jetty|undertow` | root exception shape 해석 분리 |
| `phase=response_write|response_flush|completion_callback` | disconnect가 어디서 surface됐는지 구분 |
| `commit_state=before_commit|after_commit` | 에러 계약 재작성 가능성 구분 |
| `writer_thread=platform|virtual|unknown` | virtual-thread 전환 후 실행 경계 확인 |
| `producer_cancelled=true|false` | abort 후 orphan work 유무 확인 |
| `bytes_sent` 또는 `events_sent` | first-byte 이전 종료인지, 중간 전송 실패인지 구분 |

추가로 보면 좋은 질문은 이렇다.

- abort 직후 `producer_cancelled` metric이 같이 찍히는가
- `ClientAbortException`/`EofException` 증가와 gateway `499`/`504`가 같이 움직이는가
- SSE disconnect 증가 시 heartbeat 간격과 proxy idle timeout이 맞는가
- virtual thread 전환 뒤 thread dump보다 downstream cancel 지표가 더 나빠지진 않았는가

## 트레이드오프

| 선택 | 장점 | 비용 | 적합한 경우 |
|---|---|---|---|
| 작은 batch마다 자주 `flush()` | first byte와 disconnect 감지가 빨라진다 | write overhead가 커진다 | 사용자 체감 응답과 조기 abort 감지가 중요할 때 |
| 큰 batch 후 드물게 `flush()` | throughput이 좋아질 수 있다 | disconnect를 늦게 안다 | 대용량 export, sequential download |
| heartbeat가 있는 SSE | idle timeout과 disconnect detection을 함께 제어한다 | event noise와 scheduler 비용이 늘어난다 | 장기 연결, proxy hop이 많은 SSE |
| writer만 virtual thread로 전환 | thread 비용을 낮춘다 | cancellation gap은 그대로 남는다 | blocking writer가 많지만 cleanup wiring은 이미 있는 경우 |
| `onCompletion`/`IOException`에 producer cancel 연결 | orphan work를 줄인다 | registry/token plumbing이 늘어난다 | DB/HTTP fan-out, subscription 기반 스트림 |

핵심은 "어느 thread를 쓰느냐"보다 **"abort surface에서 다음 lifetime을 누가 닫느냐"**다.

## 꼬리질문

> Q: `spring.threads.virtual.enabled`를 켜면 `StreamingResponseBody` abort도 자동으로 더 잘 처리되나요?
> 의도: virtual thread와 cancellation semantics 분리 확인
> 핵심: 아니다. async writer executor가 virtual-thread 기반이 될 수는 있지만, disconnect를 producer/downstream cancel로 자동 번역하지는 않는다.

> Q: SSE disconnect가 왜 탭을 닫는 순간 바로 안 보이나요?
> 의도: late observation 이해 확인
> 핵심: 서버는 대개 다음 event나 heartbeat를 쓰려 할 때 peer 종료를 관측하기 때문이다.

> Q: late write failure를 `@ExceptionHandler`로 일반 JSON 에러처럼 바꾸기 어려운 이유는 무엇인가요?
> 의도: commit 이후 경계 이해 확인
> 핵심: 첫 chunk/event 이후엔 상태 코드와 헤더가 이미 나갔을 수 있어 HTTP 계약을 다시 쓰기 어렵기 때문이다.

> Q: abort가 보였는데도 DB query나 subscription이 계속 돌 수 있는 이유는 무엇인가요?
> 의도: cancellation gap 이해 확인
> 핵심: response lifetime 종료와 producer/downstream lifetime 종료가 자동으로 연결되지 않기 때문이다.

## 한 줄 정리

스트리밍 응답의 abort는 보통 다음 `write`/`flush`나 completion callback에서 늦게 surface되고, virtual thread를 써도 그 신호를 producer와 downstream cancel로 직접 이어 주지 않으면 orphan work가 남는다.
