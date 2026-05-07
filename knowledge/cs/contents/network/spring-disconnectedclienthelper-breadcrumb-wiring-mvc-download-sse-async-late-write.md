---
schema_version: 3
title: "Spring DisconnectedClientHelper Breadcrumb Wiring"
concept_id: network/spring-disconnectedclienthelper-breadcrumb-wiring-mvc-download-sse-async-late-write
canonical: true
category: network
difficulty: advanced
doc_role: bridge
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- spring-disconnect
- breadcrumb-logging
- late-write
aliases:
- DisconnectedClientHelper breadcrumb
- app.http.disconnect
- StreamingResponseBody disconnect helper
- SSE disconnect breadcrumb
- AsyncRequestNotUsableException breadcrumb
- client abort breadcrumb
- broken pipe one-line logging
symptoms:
- DisconnectedClientHelper를 root logger suppression 도구로 오해한다
- expected disconnect와 app regression을 모두 같은 log level로 숨긴다
- StreamingResponseBody, SseEmitter, async late write의 app-owned write boundary에 helper를 붙이지 않는다
- committed response 뒤 ProblemDetail이나 JSON error envelope를 다시 쓰려 한다
intents:
- troubleshooting
- deep_dive
- design
prerequisites:
- network/container-specific-disconnect-logging-recipes-spring-boot
- network/network-spring-request-lifecycle-timeout-disconnect-bridge
next_docs:
- spring/streamingresponsebody-responsebodyemitter-sse-commit-lifecycle
- spring/servlet-container-disconnect-exception-mapping
- spring/async-mvc-streaming-observability-playbook
- network/sse-failure-attribution-http1-http2
linked_paths:
- contents/network/container-specific-disconnect-logging-recipes-spring-boot.md
- contents/network/spring-mvc-async-onerror-asyncrequestnotusableexception-crosswalk.md
- contents/network/network-spring-request-lifecycle-timeout-disconnect-bridge.md
- contents/network/sse-failure-attribution-http1-http2.md
- contents/network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md
- contents/spring/spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md
- contents/spring/spring-servlet-container-disconnect-exception-mapping.md
- contents/spring/spring-async-mvc-streaming-observability-playbook.md
confusable_with:
- network/container-specific-disconnect-logging-recipes-spring-boot
- network/network-spring-request-lifecycle-timeout-disconnect-bridge
- spring/servlet-container-disconnect-exception-mapping
- spring/async-mvc-streaming-observability-playbook
forbidden_neighbors: []
expected_queries:
- "Spring DisconnectedClientHelper를 어디에 wiring해야 해?"
- "StreamingResponseBody download에서 broken pipe를 app.http.disconnect breadcrumb로 남기는 법은?"
- "SseEmitter send heartbeat에서 expected disconnect와 진짜 오류를 어떻게 나눠?"
- "AsyncRequestNotUsableException late write를 왜 ProblemDetail로 다시 쓰면 안 돼?"
- "DisconnectedClientHelper는 root logger suppression 도구가 아닌 이유는?"
contextual_chunk_prefix: |
  이 문서는 Spring DisconnectedClientHelper를 MVC download, SseEmitter,
  async late write boundary에 붙여 expected disconnect를 app.http.disconnect
  breadcrumb로 정규화하는 advanced bridge다.
---
# Spring `DisconnectedClientHelper` Breadcrumb Wiring: MVC Download, SSE, Async Late Write

> 한 줄 요약: `DisconnectedClientHelper`는 root logger suppression 도구가 아니라, app-owned write boundary에서 expected disconnect를 `app.http.disconnect` 한 줄 breadcrumb로 정규화하는 도구다. `StreamingResponseBody` download, `SseEmitter` send/heartbeat, `AsyncRequestNotUsableException` late-write advice처럼 "다음 write에서 끊김이 드러나는 지점"에 붙여야 noise만 줄이고 guardrail은 살릴 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Container-Specific Disconnect Logging Recipes for Spring Boot](./container-specific-disconnect-logging-recipes-spring-boot.md)
> - [Spring MVC Async `onError` -> `AsyncRequestNotUsableException` Crosswalk](./spring-mvc-async-onerror-asyncrequestnotusableexception-crosswalk.md)
> - [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
> - [SSE Failure Attribution Across HTTP/1.1 and HTTP/2](./sse-failure-attribution-http1-http2.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
> - [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](../spring/spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
> - [Spring Servlet Container Disconnect Exception Mapping](../spring/spring-servlet-container-disconnect-exception-mapping.md)
> - [Spring Async MVC Streaming Observability Playbook](../spring/spring-async-mvc-streaming-observability-playbook.md)

retrieval-anchor-keywords: DisconnectedClientHelper breadcrumb, disconnect breadcrumb code example, app.http.disconnect, mvc download disconnect breadcrumb, StreamingResponseBody disconnect helper, StreamingResponseBody broken pipe breadcrumb, SSE disconnect breadcrumb, SseEmitter heartbeat breadcrumb, async late write breadcrumb, AsyncRequestNotUsableException breadcrumb, spring disconnect logging wiring, client abort breadcrumb, broken pipe one-line logging

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

`DisconnectedClientHelper`는 "예외를 없애는" 도구가 아니라 **expected disconnect만 전용 category로 낮게 옮기는** 도구다.

- `checkAndLogClientDisconnectedException(ex)`가 `true`를 반환하면:
  helper가 `app.http.disconnect` 같은 category에 한 줄 breadcrumb를 남겼다는 뜻이다
- 이 경우 앱 코드는:
  producer cleanup, scheduler 중단, subscription dispose 같은 정리만 하고 더 이상 response 재작성을 시도하지 않는 편이 안전하다
- `false`면:
  실제 app/server-side 회귀일 수 있으므로 그대로 재던지거나 기존 error path로 넘긴다

Spring 6.1+ 기준 helper는 대체로 아래 shape를 disconnect bucket으로 본다.

- 예외 이름: `AbortedException`, `ClientAbortException`, `EOFException`, `EofException`, `AsyncRequestNotUsableException`
- 메시지 구문: `broken pipe`, `connection reset by peer`

핵심은 helper를 **가장 마지막 app-owned write boundary**에 붙이는 것이다.

| 경로 | helper를 붙일 위치 | cleanup owner | helper 뒤에 하면 안 되는 것 |
|---|---|---|---|
| MVC download (`StreamingResponseBody`) | `write()` / `flush()` catch | export job, cursor, file handle | `ProblemDetail` 재작성, root logger suppression |
| SSE (`SseEmitter`) | `send(...)` / heartbeat catch, 필요하면 `onError` fallback | heartbeat, broker subscription, producer stop | `completeWithError(...)`를 disconnect에도 무조건 호출 |
| async late write | `AsyncRequestNotUsableException`용 좁은 `@ControllerAdvice` | 추가 write 중단, empty `ModelAndView` | committed response 뒤 JSON 오류 envelope 시도 |

### Retrieval Anchors

- `DisconnectedClientHelper breadcrumb`
- `disconnect breadcrumb code example`
- `app.http.disconnect`
- `mvc download disconnect breadcrumb`
- `SSE disconnect breadcrumb`
- `async late write breadcrumb`
- `AsyncRequestNotUsableException breadcrumb`

## 깊이 들어가기

### 1. baseline은 "전용 category + 얇은 wrapper"면 충분하다

helper는 이미 DEBUG 한 줄 / TRACE full stacktrace 정책을 갖고 있으므로, 보통은 별도 log formatting layer를 두껍게 만들 필요가 없다.

```yaml
logging:
  level:
    app.http.disconnect: DEBUG
    org.springframework.web.context.request.async: INFO
```

```java
@Component
public final class DisconnectBreadcrumbs {

    private final DisconnectedClientHelper helper =
            new DisconnectedClientHelper("app.http.disconnect");

    public boolean logIfClientGone(Throwable ex) {
        return helper.checkAndLogClientDisconnectedException(ex);
    }
}
```

이 wrapper는 intentionally thin 해야 한다.

- 공통 category를 한곳에 고정한다
- 예제 코드에서 중복되는 helper 생성 코드를 줄인다
- non-disconnect는 그대로 상위 error path로 보낼 수 있게 한다

### 2. MVC download는 `flush()` cadence가 곧 breadcrumb probe다

download path는 controller return 시점이 아니라 `StreamingResponseBody` writer callback 안에서 disconnect가 보이는 경우가 많다.  
즉 helper는 바깥 controller가 아니라 **stream body 내부의 `write`/`flush` catch**에 있어야 한다.

```java
@RestController
public class ExportController {

    private final ExportService exportService;
    private final DisconnectBreadcrumbs disconnects;

    public ExportController(ExportService exportService, DisconnectBreadcrumbs disconnects) {
        this.exportService = exportService;
        this.disconnects = disconnects;
    }

    @GetMapping("/exports/orders.csv")
    public ResponseEntity<StreamingResponseBody> exportOrders() {
        ExportHandle handle = exportService.open();

        StreamingResponseBody body = outputStream -> {
            try (BufferedWriter writer = new BufferedWriter(
                    new OutputStreamWriter(outputStream, StandardCharsets.UTF_8))) {

                int batch = 0;
                for (OrderRow row : handle.rows()) {
                    writer.write(toCsv(row));
                    writer.newLine();

                    if (++batch % 200 == 0) {
                        writer.flush(); // 다음 disconnect surface 후보
                    }
                }

                writer.flush();
            }
            catch (IOException ex) {
                handle.cancel();
                if (!disconnects.logIfClientGone(ex)) {
                    throw ex;
                }
            }
            finally {
                handle.close();
            }
        };

        return ResponseEntity.ok()
                .contentType(MediaType.parseMediaType("text/csv"))
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=orders.csv")
                .body(body);
    }
}
```

포인트는 세 가지다.

- `handle.cancel()`을 helper보다 먼저 호출해 orphan work를 줄인다
- helper가 `true`면 disconnect breadcrumb는 이미 남았으니 더 큰 stacktrace를 추가하지 않는다
- `flush()` 간격이 길수록 disconnect를 늦게 본다

### 3. SSE는 payload send와 heartbeat 둘 다 breadcrumb 지점이다

SSE에서는 disconnect가 payload가 아니라 다음 heartbeat에서 처음 드러나는 경우가 흔하다.  
따라서 helper는 `onCompletion`만으로는 부족하고, **`send(...)`와 heartbeat write path**에 같이 있어야 한다.

```java
@RestController
public class OrderEventsController {

    private final OrderEventBroker broker;
    private final TaskScheduler scheduler;
    private final DisconnectBreadcrumbs disconnects;

    public OrderEventsController(
            OrderEventBroker broker,
            TaskScheduler scheduler,
            DisconnectBreadcrumbs disconnects
    ) {
        this.broker = broker;
        this.scheduler = scheduler;
        this.disconnects = disconnects;
    }

    @GetMapping(path = "/events/orders", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public SseEmitter orderEvents() {
        SseEmitter emitter = new SseEmitter(Duration.ofMinutes(10).toMillis());
        AtomicBoolean closed = new AtomicBoolean();

        Subscription subscription = broker.subscribe(event ->
                sendEvent(emitter, closed, event));

        ScheduledFuture<?> heartbeat = scheduler.scheduleAtFixedRate(
                () -> sendHeartbeat(emitter, closed),
                Duration.ofSeconds(15));

        Runnable closeOnce = () -> {
            if (closed.compareAndSet(false, true)) {
                heartbeat.cancel(false);
                subscription.cancel();
            }
        };

        emitter.onTimeout(() -> {
            closeOnce.run();
            emitter.complete();
        });
        emitter.onError(ex -> {
            if (closed.compareAndSet(false, true)) {
                disconnects.logIfClientGone((Throwable) ex);
                heartbeat.cancel(false);
                subscription.cancel();
            }
        });
        emitter.onCompletion(closeOnce);

        return emitter;
    }

    private void sendEvent(SseEmitter emitter, AtomicBoolean closed, OrderEvent event) {
        if (closed.get()) {
            return;
        }

        try {
            emitter.send(SseEmitter.event()
                    .id(event.id())
                    .name("order-updated")
                    .data(event.payload()));
        }
        catch (IOException ex) {
            if (disconnects.logIfClientGone(ex)) {
                closed.set(true);
                emitter.complete();
                return;
            }
            emitter.completeWithError(ex);
        }
    }

    private void sendHeartbeat(SseEmitter emitter, AtomicBoolean closed) {
        if (closed.get()) {
            return;
        }

        try {
            emitter.send(SseEmitter.event().comment("keepalive"));
        }
        catch (IOException ex) {
            if (disconnects.logIfClientGone(ex)) {
                closed.set(true);
                emitter.complete();
                return;
            }
            emitter.completeWithError(ex);
        }
    }
}
```

여기서 중요한 건 disconnect를 정상 reconnect/noise bucket으로 읽을 때와, 실제 app error를 올려야 할 때를 나누는 것이다.

- helper가 `true`
  `complete()` + cleanup으로 끝낸다
- helper가 `false`
  `completeWithError(ex)`로 올린다

즉 helper는 `SseEmitter`를 조용히 만드는 게 아니라 **disconnect와 non-disconnect를 갈라주는 분기점**이다.

### 4. async late write는 좁은 advice로 tail noise를 모은다

`AsyncRequestNotUsableException`은 대개 "이미 죽은 response에 늦게 다시 썼다"는 signal이다.  
이 path에서 중요한 건 error envelope 복구가 아니라 **tail noise를 `app.http.disconnect`로 모으고, non-disconnect는 그대로 흘려보내는 것**이다.

```java
@ControllerAdvice(assignableTypes = {
        ExportController.class,
        OrderEventsController.class
})
public final class AsyncDisconnectBreadcrumbAdvice {

    private final DisconnectBreadcrumbs disconnects;

    public AsyncDisconnectBreadcrumbAdvice(DisconnectBreadcrumbs disconnects) {
        this.disconnects = disconnects;
    }

    @ExceptionHandler({AsyncRequestNotUsableException.class, IOException.class})
    public ModelAndView handleTransportTail(Exception ex) throws Exception {
        if (disconnects.logIfClientGone(ex)) {
            return new ModelAndView();
        }
        throw ex;
    }
}
```

이 advice를 좁게 두는 이유는 분명하다.

- download/SSE/async controller의 late write tail만 모은다
- 일반 MVC controller의 정상적인 `IOException`까지 blanket suppress하지 않는다
- committed response 뒤 `ProblemDetail`을 다시 만들려는 잘못된 시도를 피한다

## 실전 시나리오

### 시나리오 1: 다운로드 취소 때마다 Tomcat `ClientAbortException` stacktrace가 길게 남는다

download callback 안에서 helper를 호출하지 않으면, container 예외가 application logger까지 그대로 올라와 noise가 커진다.  
이 경우 helper는 `flush()` catch에 붙이는 게 맞고, `@GetMapping` 바깥 controller body에 두는 것은 너무 이르다.

### 시나리오 2: SSE는 payload 전송보다 heartbeat에서 disconnect가 더 많이 잡힌다

이건 이상한 현상이 아니라 흔한 운영 패턴이다.  
브라우저는 이미 떠났는데 app은 다음 heartbeat에서야 `IOException`을 보기 때문이다.  
그래서 heartbeat path에도 helper가 있어야 per-request breadcrumb가 균일해진다.

### 시나리오 3: `AsyncRequestNotUsableException`가 `onError` 뒤 연속으로 보인다

첫 transport failure 뒤 producer가 한 번 더 깨어난 late-write tail일 수 있다.  
이 경우 helper + 좁은 advice로 tail noise를 `app.http.disconnect`에 모으고, cleanup bug 자체는 별도 메트릭이나 `org.springframework.web.context.request.async` guardrail로 본다.

## 코드로 보기

### quick checklist

```text
1. helper category는 app.http.disconnect 같은 전용 logger 하나만 쓴다
2. download는 StreamingResponseBody write/flush catch에 helper를 둔다
3. SSE는 payload send와 heartbeat 둘 다 helper 분기를 둔다
4. helper가 true면 cleanup 후 조용히 종료하고, false면 기존 error path로 보낸다
5. late-write tail은 좁은 @ControllerAdvice로만 모은다
```

### wiring anti-pattern

```text
- root logger level을 낮춰 container noise를 통째로 숨긴다
- helper 호출 뒤에도 같은 예외를 WARN/ERROR로 다시 남긴다
- committed response 뒤 ProblemDetail/JSON 오류 envelope를 다시 쓰려 한다
- SSE에서 onCompletion만 믿고 send/heartbeat catch에는 helper를 두지 않는다
- AsyncRequestNotUsableException를 전역 Exception advice에서 모두 삼킨다
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| 각 write boundary에 helper를 직접 둔다 | disconnect probe 위치가 선명하다 | 코드가 조금 흩어진다 | download, SSE, NDJSON처럼 write ownership이 분명한 endpoint |
| 얇은 wrapper bean으로 helper를 감싼다 | category와 호출 규칙을 통일하기 쉽다 | wrapper가 과해지면 중복 로깅 위험이 있다 | 여러 streaming endpoint가 같은 breadcrumb 정책을 공유할 때 |
| late-write advice를 좁게 건다 | `AsyncRequestNotUsableException` tail을 잘 모은다 | controller 범위 지정이 필요하다 | MVC async/streaming controller만 별도 운영할 때 |
| 전역 blanket suppression | 당장은 조용하다 | 실제 회귀까지 가린다 | 권장하지 않음 |

핵심은 helper를 "전역 noise killer"가 아니라 **disconnect-aware branch point**로 다루는 것이다.

## 꼬리질문

> Q: helper를 controller method 전체에 한 번만 두면 안 되나요?
> 핵심: 보통 안 된다. disconnect는 controller return 시점보다 뒤의 `write()` / `flush()` / `send()`에서 보이기 쉽기 때문이다.

> Q: helper가 `true`면 항상 예외를 삼켜도 되나요?
> 핵심: cleanup을 먼저 했고, 이미 commit 뒤 unusable response라면 보통 그렇다. 대신 non-disconnect가 아닌지 `false` 분기를 꼭 살려야 한다.

> Q: `AsyncRequestNotUsableException`도 helper bucket으로 보내도 되나요?
> 핵심: late-write tail을 정리하는 좁은 advice 안에서는 유용하다. 다만 전역 blanket handler로 두면 실제 회귀를 숨길 수 있으니 범위를 제한해야 한다.

## 한 줄 정리

`DisconnectedClientHelper`의 가장 안전한 wiring은 **download는 `flush()` catch, SSE는 `send()`/heartbeat catch, async late write는 좁은 advice**에 붙여서 `app.http.disconnect` breadcrumb만 남기고 non-disconnect는 그대로 올려 보내는 것이다.
