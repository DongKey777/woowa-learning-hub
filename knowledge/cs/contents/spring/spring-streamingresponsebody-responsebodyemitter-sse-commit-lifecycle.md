# Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle

> 한 줄 요약: 셋 다 Spring MVC async 위에서 동작하지만, 첫 바이트가 언제 commit되는지, flush가 어떤 주기로 일어나는지, timeout/disconnect가 어느 콜백과 예외로 드러나는지가 다르므로 같은 "스트리밍 응답"으로 뭉뚱그리면 운영 해석이 쉽게 틀어진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring `ProblemDetail` Before-After Commit Matrix](./spring-problemdetail-before-after-commit-matrix.md)
> - [Spring Async Timeout vs Disconnect Decision Tree](./spring-async-timeout-disconnect-decision-tree.md)
> - [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](./spring-mvc-async-deferredresult-callable-dispatch.md)
> - [Spring `HandlerMethodReturnValueHandler` / `ResponseEntity` / `@ResponseBody` Chain](./spring-handlermethodreturnvaluehandler-chain.md)
> - [Spring `ResponseBodyAdvice` on Streaming Types: `ResponseBodyEmitter`, `SseEmitter`, `StreamingResponseBody`](./spring-responsebodyadvice-streaming-types.md)
> - [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
> - [Spring Partial-Response Access Log Interpretation](./spring-partial-response-access-log-interpretation.md)
> - [Spring Async MVC Streaming Observability Playbook](./spring-async-mvc-streaming-observability-playbook.md)
> - [Spring `ResponseBodyEmitter` Media-Type Boundaries: NDJSON, Plain Text, JSON Array](./spring-responsebodyemitter-media-type-boundaries.md)
> - [Spring MVC `SseEmitter` vs WebFlux SSE Timeout Behavior](./spring-mvc-sseemitter-vs-webflux-sse-timeout-behavior.md)
> - [Spring `SseEmitter` Timeout Callback Race Matrix](./spring-sseemitter-timeout-callback-race-matrix.md)
> - [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)
> - [Spring SSE Buffering / Compression Checklist](./spring-sse-buffering-compression-checklist.md)
> - [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)
> - [Spring `RequestBodyAdvice` and `ResponseBodyAdvice` Pipeline](./spring-requestbody-responsebodyadvice-pipeline.md)
> - [Spring MVC vs WebFlux](./spring-webflux-vs-mvc.md)
> - [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](../network/request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](../network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)

retrieval-anchor-keywords: StreamingResponseBody, ResponseBodyEmitter, SseEmitter, DeferredResult, Callable, text/event-stream, SSE heartbeat, async mvc streaming, first byte commit, response commit, flush cadence, output stream flush, chunked transfer encoding, async timeout, AsyncRequestTimeoutException, AsyncRequestNotUsableException, broken pipe, client abort, disconnect handling, partial response access log, truncated download, bytes sent correlation, completeWithError, onTimeout, onError, onCompletion, response streaming, NDJSON streaming, application/x-ndjson, text/plain streaming, application/json array, document framing, ClientAbortException, EofException, ClosedChannelException, ALB idle timeout, nginx proxy_read_timeout, EventSource retry, Last-Event-ID, proxy buffering, X-Accel-Buffering, Content-Encoding gzip, Cache-Control no-transform, WebFlux SSE, Flux<ServerSentEvent>, reactive SSE cancellation, SseEmitter vs WebFlux SSE, emitter replacement race, scheduler cleanup

## 핵심 개념

이 세 타입은 모두 "긴 응답"을 만든다는 점은 같지만, 실제 책임 경계는 다르다.

- `StreamingResponseBody`: 애플리케이션이 `OutputStream`에 직접 쓴다
- `ResponseBodyEmitter`: Spring이 `HttpMessageConverter`로 각 조각을 써 준다
- `SseEmitter`: `ResponseBodyEmitter` 위에 SSE 포맷(`text/event-stream`)을 얹는다

이 차이 때문에 운영에서 봐야 하는 질문도 달라진다.

- 첫 바이트는 누가 언제 밀어 넣는가?
- flush는 매 조각마다 자동인가, 내가 직접 해야 하는가?
- timeout은 어디서 설정하고 어디서 cleanup하는가?
- client disconnect는 즉시 보이나, 다음 write에서야 보이나?

## 먼저 구분할 것: commit과 wire chunk는 같은 말이 아니다

response commit은 "상태 코드와 헤더가 더 이상 자유롭게 바뀌지 않는 경계"다.

보통 streaming 응답에서 이 경계는 다음 중 하나로 생긴다.

- 첫 body flush
- servlet buffer 초과
- 컨테이너의 최종 flush

하지만 네트워크에 실제로 어떤 chunk나 frame이 나가 보이는지는 별개다.

- HTTP/1.1에선 `Content-Length`가 없으면 흔히 chunked transfer가 된다
- HTTP/2에선 chunked transfer encoding 대신 data frame으로 보인다
- proxy/CDN은 flush를 받아도 잠시 더 버퍼링할 수 있다

즉 buffering, gzip/brotli, edge body transform 때문에 실제 `text/event-stream` cadence가 어떻게 달라지는지는 [Spring SSE Buffering / Compression Checklist](./spring-sse-buffering-compression-checklist.md)에서 따로 점검해야 한다.

즉 "앱이 flush했다"는 것은 **바로 그 시점부터 commit과 downstream write가 가능해졌다**는 뜻이지, 사용자가 즉시 화면에서 본다는 보장은 아니다.

## 비교 표

| 타입 | body 작성 주체 | 첫 바이트 commit 계기 | flush cadence | timeout 제어 | disconnect가 드러나는 자리 |
|---|---|---|---|---|---|
| `StreamingResponseBody` | 애플리케이션이 `OutputStream` 직접 write | 애플리케이션의 첫 `flush()`, buffer overflow, 또는 callback 종료 후 Spring의 최종 flush | Spring은 callback 끝에서 한 번 flush, 중간 cadence는 애플리케이션 책임 | MVC async 기본 timeout / container timeout, 별도 emitter callback 없음 | `write` / `flush` / `close`에서 `IOException` 또는 `AsyncRequestNotUsableException` |
| `ResponseBodyEmitter` | Spring이 `HttpMessageConverter`로 각 item write | 첫 `send(...)`가 write 후 flush할 때 거의 확정 | 기본 `send(...)`는 호출마다 flush, batch `send(Set<...>)`는 끝에서 한 번 flush | 인스턴스 timeout 또는 MVC default, `onTimeout` / `onError` / `onCompletion` 지원 | `send(...)` 예외, container async error, completion callback |
| `SseEmitter` | Spring이 SSE 필드와 payload를 조합해 write | 첫 SSE event flush 시점 | event 1개당 보통 한 번 flush, line마다 자동 flush는 아님 | `ResponseBodyEmitter`와 동일 | 다음 event/heartbeat write 시점의 예외와 completion callback |

핵심은 `StreamingResponseBody`만이 "중간 flush를 내가 직접 설계"하고, emitter 계열은 "Spring이 send 단위로 flush"한다는 점이다.

## 깊이 들어가기

### 1. `StreamingResponseBody`는 write cadence를 애플리케이션이 가진다

Spring MVC는 `StreamingResponseBody`를 async `Callable`로 감싸 실행하고, callback이 끝나면 마지막에 `outputMessage.flush()`를 한 번 더 호출한다.

하지만 callback 내부의 중간 flush는 Spring이 대신 해 주지 않는다.

즉 다음은 완전히 다른 동작이다.

- `write()`만 여러 번 하고 `flush()`를 끝에서 한 번만 한다
- 의미 있는 batch마다 `flush()`를 호출한다
- 아주 작은 조각마다 `flush()`를 호출한다

운영 해석은 이렇게 잡으면 된다.

- 첫 바이트가 빨리 나가야 한다면 초반에 명시적 `flush()`가 필요할 수 있다
- 너무 자주 flush하면 syscalls, TLS record, proxy write가 잘게 쪼개져 throughput이 나빠질 수 있다
- 너무 늦게 flush하면 클라이언트는 "아직 아무것도 안 오는" 응답으로 본다

즉 `StreamingResponseBody`의 chunk cadence는 프레임워크 기능이 아니라 **애플리케이션의 flush 정책**이다.

### 2. `ResponseBodyEmitter`는 `send` 호출이 곧 write + flush 단위다

`ResponseBodyEmitter`는 `send(object)`마다 다음을 한다.

- 적절한 `HttpMessageConverter`를 선택해 body 조각을 쓴다
- 곧바로 response를 flush한다

그래서 첫 `send(...)`가 사실상 first-byte commit 포인트가 된다.

이 타입에서 중요한 함정은 flush 주기가 "내 loop iteration"이 아니라 **`send(...)` 호출 횟수**라는 점이다.

- `send()`를 1,000번 호출하면 1,000번 flush가 붙는다
- Spring 6.0.12+의 `send(Set<DataWithMediaType>)`를 쓰면 여러 item을 한 번에 쓰고 마지막에 한 번만 flush한다

즉 고빈도 NDJSON/텍스트 스트리밍에서 성능이 흔들리면 "converter가 느리다"보다 먼저 **send 호출 granularity가 너무 잘게 쪼개졌는가**를 본다.

다만 `send()` 횟수와 client parsing 단위는 별개다. `application/x-ndjson`, `text/plain`, `application/json`이 각각 어떤 framing 계약을 가지는지는 [Spring `ResponseBodyEmitter` Media-Type Boundaries: NDJSON, Plain Text, JSON Array](./spring-responsebodyemitter-media-type-boundaries.md)에서 따로 정리한다.

또 하나의 의미는, `ResponseEntity<ResponseBodyEmitter>` 조합에서 headers/status는 첫 send 전까지 조정 가능하지만, streaming이 시작된 뒤엔 사실상 응답 메타데이터 ownership이 닫힌다는 점이다.

### 3. `SseEmitter`는 "line마다 flush"가 아니라 "event마다 flush"에 가깝다

`SseEmitter`는 `ResponseBodyEmitter`의 하위 타입이지만, `send(...)` 전에 SSE event를 조립한다.

예를 들어 다음 필드들이 한 event가 될 수 있다.

- `id:`
- `event:`
- `retry:`
- `data:`
- 마지막 빈 줄

Spring은 이 event를 내부적으로 여러 조각으로 모아 쓴 뒤, 마지막에 한 번 flush한다.

즉 보통의 해석은 이렇다.

- `emitter.send(event().name("tick").data(payload))`
- event 전체가 write된다
- flush는 event 끝에서 한 번 일어난다

그래서 `SseEmitter`의 flush cadence는 보통 "메시지 1건 = flush 1번"이다.

이건 SSE heartbeat 설계에도 바로 연결된다.

- Spring이 heartbeat를 자동으로 보내 주지 않는다
- proxy idle timeout보다 긴 공백이 생기면 연결이 끊길 수 있다
- keepalive comment나 작은 event를 스케줄링해야 한다

즉 SSE가 몇 분 뒤 조용히 끊긴다면 "business event가 없었다"와 "heartbeat가 없었다"를 함께 봐야 한다.

### 4. timeout의 시작점은 async 전환 이후다

Servlet async에서 timeout 카운트는 보통 container processing thread가 빠져나간 뒤 시작된다.

세 타입 모두 이 async 경계 위에 올라탄다. 다만 노출 방식은 다르다.

- `StreamingResponseBody`: per-instance callback이 없고 MVC async timeout 설정을 따른다
- `ResponseBodyEmitter` / `SseEmitter`: 생성자 timeout 또는 MVC default를 쓰고 callback을 직접 건다

즉 timeout 모델은 "streaming 전용 magic timeout"이 아니라 **기존 Servlet async timeout 계약의 표면적 차이**다.

### 5. emitter 계열은 timeout/error/completion callback이 cleanup의 중심이다

`ResponseBodyEmitter`와 `SseEmitter`는 container thread에서 다음 callback을 받을 수 있다.

- `onTimeout`
- `onError`
- `onCompletion`

의미는 이렇게 구분하는 편이 정확하다.

- `onTimeout`: async request timeout이 발생했다
- `onError`: async processing 중 container가 error를 통지했다
- `onCompletion`: timeout, network error, 정상 종료를 포함해 더 이상 emitter를 쓸 수 없다

즉 cleanup은 `onCompletion`에 모으고, timeout-specific 정책만 `onTimeout`에 두는 편이 안전하다.

특히 SSE heartbeat scheduler, broker subscription, polling task는 `onCompletion`에서 반드시 정리해야 한다.

### 6. `completeWithError`는 error contract를 되살리는 만능 복구가 아니다

emitter 계열은 `completeWithError(...)`를 제공하지만, 이 시점엔 응답이 이미 commit된 경우가 많다.

즉 다음을 기대하면 안 된다.

- 이미 일부 event/chunk가 나간 뒤
- JSON `ProblemDetail`로 예쁘게 갈아엎기
- 상태 코드를 새로 바꾸기

Spring Javadoc도 send 중 `IOException`이 났다면 애플리케이션이 굳이 `completeWithError(...)`를 다시 호출하지 말라고 본다. 이미 container notification과 async dispatch가 이어질 수 있기 때문이다.

핵심은 `completeWithError`를 "commit 전 예외 번역기"로 보지 말고, **남은 async lifecycle을 끝내는 신호**로 보는 것이다.

### 7. disconnect는 대개 "다음 write"에서야 관측된다

브라우저 탭 종료, mobile network drop, proxy idle timeout은 서버가 즉시 알지 못할 수 있다.

그래서 streaming 응답의 흔한 타임라인은 이렇다.

```text
연결은 이미 peer 쪽에서 끊김
-> 서버는 아직 모름
-> 다음 send/write/flush 시도
-> broken pipe / connection reset / AsyncRequestNotUsableException
-> onError 또는 onCompletion
```

즉 disconnect는 "클라이언트가 끊은 시각"보다 **서버가 다음 바이트를 쓰려 한 시각**에 더 자주 드러난다.

SSE에서 heartbeat가 중요한 이유도 이것이다.

- heartbeat가 없으면 끊김을 늦게 안다
- heartbeat가 있으면 끊김을 더 빨리 surface한다

### 8. first-byte 이후엔 JSON API 오류 계약을 기대하지 말아야 한다

이 세 타입은 first-byte commit을 앞당기기 쉽다.

- `StreamingResponseBody`: 첫 `flush()` 이후
- `ResponseBodyEmitter`: 첫 `send()` 이후
- `SseEmitter`: 첫 event 이후

이 경계를 넘으면 남는 선택지는 대개 다음뿐이다.

- stream 종료
- socket error 기록
- callback을 통한 cleanup
- metrics / tracing / access log 관측

즉 streaming endpoint를 일반 JSON controller와 같은 예외 처리 직관으로 보면 안 된다.

## 실전 시나리오

### 시나리오 1: `StreamingResponseBody` 다운로드가 끝나기 전까지 클라이언트에 아무 바이트도 안 보인다

대개 loop 안에서 `write()`만 하고 중간 `flush()`를 하지 않은 경우다.

문제는 "Spring이 늦게 보낸다"가 아니라, **애플리케이션이 commit cadence를 끝으로 몰았다**는 데 있다.

### 시나리오 2: `ResponseBodyEmitter`로 NDJSON을 보냈더니 CPU는 높지 않은데 throughput이 낮다

send 단위가 너무 작아 매 item마다 flush가 일어나고 있을 수 있다.

이 경우는 serialization보다 **flush granularity**가 병목일 가능성이 높다.

### 시나리오 3: SSE는 잘 붙는데 60초쯤 지나면 조용히 끊긴다

앱 timeout이 아니라 proxy idle timeout일 수 있다.

heartbeat comment/event가 없으면 다음 business event가 오기 전까지 disconnect를 늦게 관측한다.

### 시나리오 4: timeout 후에도 producer가 계속 `send()`를 시도한다

emitter는 이미 unusable 상태인데 worker가 이를 모르고 계속 쓰고 있을 수 있다.

이 경우 `onCompletion`에서 producer 취소를 연결하지 않은 설계가 흔한 원인이다.

## 코드로 보기

### `StreamingResponseBody`: batch 경계에서 명시적 flush

```java
@GetMapping("/exports/orders")
public ResponseEntity<StreamingResponseBody> exportOrders() {
    StreamingResponseBody body = outputStream -> {
        try (BufferedWriter writer =
                     new BufferedWriter(new OutputStreamWriter(outputStream, StandardCharsets.UTF_8))) {
            int count = 0;
            for (OrderRow row : orderExportService.streamRows()) {
                writer.write(toNdjson(row));
                writer.newLine();

                if (++count % 100 == 0) {
                    writer.flush();
                }
            }
            writer.flush();
        }
        catch (AsyncRequestNotUsableException | IOException ex) {
            orderExportService.cancelCurrentExport();
        }
    };

    return ResponseEntity.ok()
            .contentType(MediaType.APPLICATION_NDJSON)
            .body(body);
}
```

핵심은 "100건마다 flush"가 곧 commit/next-chunk cadence라는 점이다.

### `ResponseBodyEmitter`: `send()` 횟수가 flush 횟수다

```java
@GetMapping("/reports/live")
public ResponseBodyEmitter liveReport() {
    ResponseBodyEmitter emitter = new ResponseBodyEmitter(15_000L);
    Runnable stopProducer = reportService::cancelCurrentStream;

    emitter.onTimeout(emitter::complete);
    emitter.onCompletion(stopProducer);
    emitter.onError(ex -> stopProducer.run());

    reportExecutor.execute(() -> {
        try {
            for (ReportChunk chunk : reportService.streamChunks()) {
                emitter.send(chunk, MediaType.APPLICATION_JSON);
            }
            emitter.complete();
        }
        catch (IOException ex) {
            stopProducer.run();
        }
    });

    return emitter;
}
```

여기서는 각 `emitter.send(...)`가 write + flush 1회를 만든다.

### `SseEmitter`: heartbeat를 cleanup과 함께 묶기

```java
@GetMapping(path = "/events/orders", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public SseEmitter orderEvents() {
    SseEmitter emitter = new SseEmitter(30_000L);

    ScheduledFuture<?> heartbeat = scheduler.scheduleAtFixedRate(() -> {
        try {
            emitter.send(SseEmitter.event().comment("keepalive"));
        }
        catch (IOException ex) {
            emitter.complete();
        }
    }, Duration.ofSeconds(15));

    emitter.onTimeout(emitter::complete);
    emitter.onError(ex -> heartbeat.cancel(false));
    emitter.onCompletion(() -> heartbeat.cancel(false));

    return emitter;
}
```

중요한 점은 heartbeat 자체도 다음 disconnect를 surface하는 write라는 점이다.

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| `StreamingResponseBody` | flush, 포맷, batch 경계를 가장 세밀하게 통제한다 | timeout callback과 cleanup 연결을 직접 더 신경 써야 한다 | 대용량 다운로드, custom binary/text stream |
| `ResponseBodyEmitter` | converter 재사용이 쉽고 Spring MVC JSON/text 경로와 잘 붙는다 | `send()`마다 flush라 고빈도 스트림은 비효율적일 수 있다 | NDJSON, 점진적 텍스트/JSON 응답 |
| `SseEmitter` | SSE framing과 `text/event-stream` 설정이 단순하다 | heartbeat, reconnect, idle-timeout 운영을 앱이 설계해야 한다 | 브라우저 push, 이벤트 피드, live status |

핵심은 "streaming이면 다 같다"가 아니라, **flush ownership과 cleanup ownership이 누구에게 있느냐**로 선택하는 것이다.

## 꼬리질문

> Q: `StreamingResponseBody`에서 첫 바이트가 언제 commit되는가?
> 의도: 앱 주도 flush 모델 확인
> 핵심: 대개 첫 명시적 `flush()`나 buffer overflow, 또는 callback 종료 후 최종 flush 시점이다.

> Q: `ResponseBodyEmitter`가 작은 조각을 너무 많이 보낼 때 왜 느려질 수 있는가?
> 의도: send 단위와 flush 단위 연결 확인
> 핵심: 기본 `send()`가 호출마다 write 후 flush하기 때문이다.

> Q: `SseEmitter`는 왜 event 사이 heartbeat가 중요한가?
> 의도: idle timeout과 disconnect surface 이해 확인
> 핵심: Spring이 자동 heartbeat를 보내지 않으므로 proxy idle timeout과 disconnect 관측이 다음 write까지 지연될 수 있기 때문이다.

> Q: timeout이나 네트워크 오류 후 cleanup을 어디에 두는 것이 가장 안전한가?
> 의도: emitter lifecycle callback 이해 확인
> 핵심: 정상 종료, timeout, 네트워크 오류를 모두 덮는 `onCompletion`이 cleanup 중심이 된다.

## 한 줄 정리

`StreamingResponseBody`는 flush를 내가 설계하는 타입이고, `ResponseBodyEmitter`와 `SseEmitter`는 send/event 단위로 Spring이 flush를 붙이는 타입이므로, first-byte commit·timeout·disconnect 해석을 같은 공식으로 보면 안 된다.
