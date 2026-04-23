# Spring SSE Proxy Idle-Timeout Matrix

> 한 줄 요약: `SseEmitter` heartbeat는 단순한 "연결 유지용 ping"이 아니라 ALB, Nginx, CDN, 브라우저 reconnect가 서로 다른 타이머를 갖는 체인에서 가장 짧은 유효 idle timeout을 넘기지 않게 만드는 운영 계약이다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
> - [Spring MVC `SseEmitter` vs WebFlux SSE Timeout Behavior](./spring-mvc-sseemitter-vs-webflux-sse-timeout-behavior.md)
> - [Spring `SseEmitter` Timeout Callback Race Matrix](./spring-sseemitter-timeout-callback-race-matrix.md)
> - [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
> - [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)
> - [Spring SSE Disconnect Observability Patterns](./spring-sse-disconnect-observability-patterns.md)
> - [Spring SSE Buffering / Compression Checklist](./spring-sse-buffering-compression-checklist.md)
> - [Spring SSE Replay Buffer and `Last-Event-ID` Recovery Patterns](./spring-sse-replay-buffer-last-event-id-recovery-patterns.md)
> - [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](./spring-mvc-async-deferredresult-callable-dispatch.md)
> - [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](../network/timeout-budget-propagation-proxy-gateway-service-hop-chain.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](../network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
> - [Service Mesh Local Reply, Timeout, Reset Attribution](../network/service-mesh-local-reply-timeout-reset-attribution.md)

retrieval-anchor-keywords: SseEmitter, SSE proxy idle timeout, ALB idle timeout, nginx proxy_read_timeout, CDN streaming timeout, proxy buffering, proxy_buffering off, X-Accel-Buffering, SSE gzip off, SSE brotli off, Content-Encoding gzip, Cache-Control no-transform, CDN body transform, EventSource retry, Last-Event-ID, SSE replay buffer, replay window, recovery fence, high water mark, event ordering fence, multi-instance SSE recovery, sticky session failover, heartbeat interval, keepalive comment, reconnect storm, idle timeout matrix, text/event-stream, server sent events, async timeout, disconnect surface, SSE disconnect observability, heartbeat gap, reconnect pressure, proxy idle suspected, WebFlux SSE heartbeat, Flux timeout SSE, SseEmitter timeout vs proxy idle, SseEmitter onError, SseEmitter onCompletion, SSE callback race, proxy idle next send failure

## 핵심 개념

SSE 운영에서 자주 섞이는 타이머는 사실 서로 다른 질문에 답한다.

- Spring MVC async timeout: 이 request를 애플리케이션이 얼마나 오래 붙잡을 것인가
- proxy idle timeout: 바이트가 안 흐르는 연결을 얼마나 오래 살려둘 것인가
- browser reconnect delay: 연결이 이미 끊긴 뒤 얼마나 기다렸다 다시 붙을 것인가

따라서 heartbeat가 모든 타이머를 동시에 해결한다고 생각하면 설계가 틀어진다.

- heartbeat는 주로 **network idle timeout**을 리셋한다
- heartbeat는 **disconnect를 다음 write에서 빨리 surface**하게 만든다
- heartbeat는 **Servlet async timeout 자체를 자동 연장하지 않는다**

핵심은 "`SseEmitter` timeout", "`proxy_read_timeout`", "`EventSource` retry"를 하나의 숫자로 맞추는 것이 아니라, 각 숫자의 의미를 분리한 뒤 **가장 짧은 유효 idle hop 기준으로 heartbeat를 잡고, reconnect는 별도 정책으로 설계**하는 것이다.

## Idle-Timeout Matrix

| 계층 | 실제로 재는 것 | heartbeat가 리셋하는가 | 흔한 오해 | 운영 기준 |
|---|---|---|---|---|
| Spring MVC async / `SseEmitter` timeout | async request의 전체 수명 | 보통 아니다 | heartbeat를 보내면 Spring request도 영원히 산다 | app 쪽 lifetime을 명시적으로 길게 두거나, 장기 SSE라면 MVC async timeout을 의도적으로 조정한다 |
| Nginx `proxy_read_timeout` | upstream(Spring)에서 다음 바이트를 읽을 때까지의 간격 | 그렇다. 단, Nginx가 실제로 upstream 바이트를 읽어야 한다 | app에서 flush만 하면 브라우저도 바로 heartbeat를 본다 | heartbeat 간격을 `proxy_read_timeout`보다 충분히 짧게 두고, SSE 경로는 buffering 여부를 같이 확인한다 |
| ALB idle timeout | 연결/stream에 바이트가 흐르지 않는 구간 | 그렇다. ALB를 가로질러 바이트가 지나가면 리셋된다 | app과 ALB 사이 heartbeat만 있으면 끝이다 | ALB가 체인에서 가장 짧으면 그 값이 실질 상한이다 |
| CDN / edge proxy | vendor별 downstream idle, origin idle, streaming cap, buffering 정책 | 경우에 따라 다르다 | origin이 heartbeat를 쓰면 브라우저도 동일 cadence로 받는다 | CDN이 SSE를 pass-through 하는지, buffering/transform 없이 전달하는지 먼저 검증한다 |
| Browser `EventSource` reconnect | 연결이 끊긴 뒤 재시도 전 대기 시간 | 해당 없음 | reconnect delay가 keepalive 역할도 한다 | reconnect는 keepalive가 아니라 복구 정책이다. `retry:`와 `Last-Event-ID`를 별도로 설계한다 |

여기서 중요한 문장은 하나다.

> **가장 짧은 timeout이 항상 이기는 것은 아니고, 가장 짧은 "heartbeat를 실제로 보게 되는" timeout이 이긴다.**

즉 Nginx가 upstream heartbeat를 읽어 timeout은 안 내도, buffering 때문에 브라우저나 CDN이 heartbeat를 못 보면 체인 끝에서는 여전히 idle close가 날 수 있다.

## 왜 `SseEmitter` heartbeat만으로 충분하지 않을 때가 있는가

### 1. heartbeat는 app timeout보다 proxy timeout에 더 직접적이다

`SseEmitter`는 Servlet async 위에서 동작한다.

- app timeout은 async lifecycle의 총 길이
- proxy idle timeout은 "다음 바이트를 언제 보느냐"

따라서 20초마다 heartbeat를 보내도 app timeout이 30초라면, request는 30초 부근에서 app 쪽이 먼저 닫을 수 있다.

즉 "heartbeat가 있으니 긴 연결이다"가 아니라:

- `SseEmitter`/MVC async timeout을 명시적으로 맞췄는가?
- heartbeat가 proxy idle보다 짧은가?
- reconnect가 app-close와 proxy-close를 모두 복구할 수 있는가?

를 각각 따져야 한다.

### 2. Nginx buffering은 heartbeat의 의미를 바꾼다

SSE에서 자주 생기는 착시는 이렇다.

```text
Spring emits heartbeat every 15s
-> Nginx reads it, so upstream read timeout is safe
-> Nginx buffers or coalesces bytes
-> browser/CDN does not observe periodic downstream bytes
-> downstream idle timeout still expires
```

즉 heartbeat는 **생성된 것**만으로는 부족하고, **실제로 다음 hop으로 전달된 것**이어야 한다.

그래서 SSE 경로는 보통 다음 질문을 같이 본다.

- `proxy_buffering`이 꺼져 있는가?
- 필요하다면 `X-Accel-Buffering: no` 같은 경로별 우회가 적용되는가?
- 압축/변환이 event stream을 뭉개지 않는가?
- CDN이 long-lived streaming response를 pass-through 하는가?

buffering, gzip/brotli, `no-transform` header, edge body transform을 한 번에 점검하려면 [Spring SSE Buffering / Compression Checklist](./spring-sse-buffering-compression-checklist.md)를 같이 보는 편이 빠르다.

### 3. ALB는 앱 예외를 남기지 않고 조용히 끊김을 만들 수 있다

ALB idle timeout이 먼저 만료되면 애플리케이션은 보통 즉시 알지 못한다.

흔한 타임라인은 다음과 같다.

```text
business event가 한동안 없음
-> ALB idle timeout 만료
-> 서버는 아직 연결 종료를 모름
-> 다음 heartbeat 또는 다음 business event write
-> IOException / AsyncRequestNotUsableException / broken pipe surface
```

즉 ALB timeout은 Spring stacktrace보다 access log, connection reset, 다음 write 실패로 더 잘 보인다.

### 4. CDN은 "idle timeout"만이 아니라 "streaming compatibility" 문제를 만든다

CDN/edge 계층은 제품마다 차이가 커서 같은 SSE라도 다음이 달라질 수 있다.

- origin에서 받은 작은 chunk를 즉시 내보내는가
- 일정 크기까지 모아 버퍼링하는가
- 장시간 open response를 제한하는가
- response transform/compression이 SSE framing을 건드리는가

그래서 CDN이 끼는 구조에서는 "heartbeat를 몇 초마다 보낼까"보다 먼저:

- 이 CDN이 `text/event-stream`을 long-lived pass-through 하는가
- origin keepalive와 client-side keepalive가 같은 hop에서 관측되는가

를 확인해야 한다.

## Heartbeat Interval Sizing

실무에선 다음 순서가 안전하다.

1. app부터 edge까지 모든 타이머를 적는다.
2. 그중 "실제 바이트 전달이 없으면 닫히는" idle timeout만 따로 표시한다.
3. 그중 가장 짧은 유효 idle timeout을 `Tmin`으로 둔다.
4. heartbeat interval `H`는 `Tmin`보다 훨씬 짧게 둔다.

보수적으로는 다음 가이드를 쓰면 된다.

- 안정적인 내부망: `H <= Tmin / 2`
- GC pause, scheduler jitter, mobile network, CDN buffering 가능성 존재: `H <= Tmin / 3`
- heartbeat가 너무 촘촘해 비용이 크면 timeout을 늘리는 쪽을 먼저 검토한다

중요한 건 heartbeat를 timeout 직전으로 바싹 붙이지 않는 것이다.

- scheduler drift
- JVM stop-the-world pause
- proxy flush 지연
- packet loss / retransmission

같은 요인 때문에 "timeout 60초, heartbeat 55초"는 운영 여유가 너무 작다.

## 토폴로지별 해석 매트릭스

| 토폴로지 | 가장 먼저 확인할 것 | 끊김이 보이는 모습 | 설계 포인트 |
|---|---|---|---|
| App -> ALB -> Browser | ALB idle timeout vs heartbeat interval | event가 뜸할 때 일정 주기 후 다음 write에서 예외 | heartbeat를 ALB idle보다 충분히 짧게 두고, disconnect를 다음 write에서 처리한다 |
| App -> Nginx -> Browser | `proxy_read_timeout`, `proxy_buffering` | upstream은 안정적이지만 브라우저 쪽은 조용히 끊김 | SSE 경로는 buffering을 피하고 comment/event가 downstream까지 흘러가게 한다 |
| App -> ALB -> CDN -> Browser | CDN streaming pass-through / client-side idle | ALB는 살아 있지만 브라우저 reconnect가 반복 | 가장 짧은 값만 보지 말고, CDN이 heartbeat를 전달하는지 검증한다 |
| App -> Nginx -> ALB -> CDN -> Browser | hop별 idle + buffering 조합 | 특정 hop 로그와 브라우저 체감이 서로 다름 | "어디서 끊겼는가"보다 "누가 마지막 바이트를 봤는가"로 추적한다 |

## Reconnect Strategy

proxy idle close를 완전히 없애지 못한다면 reconnect는 필수다. 다만 reconnect를 기본값에만 맡기면 timeout 주기와 lock-step이 되기 쉽다.

### 1. `retry:`는 keepalive가 아니라 복구 속도 제어다

SSE의 `retry:`는 브라우저가 다음 reconnect를 언제 시도할지에 대한 힌트다.

- heartbeat interval과 같은 값으로 맞출 필요는 없다
- 오히려 동일 값으로 맞추면 주기적인 reconnect sawtooth를 만들 수 있다

실무 기준은 이렇다.

- 기본 reconnect는 low-seconds 영역에서 시작한다
- client flood를 피하려면 jitter를 섞는다
- 장애가 길어지면 cap이 있는 backoff를 둔다

native `EventSource`만 쓴다면 브라우저 reconnect는 대체로 결정적이므로, 서버가 connection별로 조금 다른 `retry:` 값을 내려 주는 편이 낫다.

### 2. event `id`와 `Last-Event-ID` 없이는 reconnect가 복구가 아니라 손실이 된다

proxy idle timeout으로 끊긴 연결은 "오래된 연결의 종료"일 뿐, 비즈니스 이벤트 손실 여부와는 별개다.

그래서 운영적으로는 다음이 필요하다.

- business event마다 안정적인 `id`를 보낸다
- reconnect 시 `Last-Event-ID`를 읽어 gap을 메울 수 있게 한다
- heartbeat comment에는 보통 `id`를 붙이지 않는다

즉 heartbeat는 liveness용, `id`는 recovery용이다.
replay window 크기, replay/live handoff ordering fence, multi-instance failover trade-off는 [Spring SSE Replay Buffer and `Last-Event-ID` Recovery Patterns](./spring-sse-replay-buffer-last-event-id-recovery-patterns.md)에서 따로 정리한다.

### 3. reconnect storm는 heartbeat 실수와 함께 온다

가장 흔한 안 좋은 조합은 다음이다.

- shortest idle timeout보다 heartbeat가 길다
- 모든 client가 동일한 `retry:`를 쓴다
- timeout이 deterministic하게 발생한다

그러면 수천 연결이 비슷한 시각에 같이 끊기고 같이 다시 붙는다.

완화 기준:

- heartbeat에 충분한 slack 확보
- `retry:`에 connection-level jitter 부여
- 서버는 reconnect 직후 replay 범위를 `Last-Event-ID` 기준으로 좁힌다

## 코드로 보기

### heartbeat와 reconnect 힌트를 분리한 `SseEmitter`

```java
@GetMapping(path = "/events/orders", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public SseEmitter orderEvents(
        @RequestHeader(name = "Last-Event-ID", required = false) String lastEventId
) throws IOException {
    long heartbeatMillis = 20_000L;
    long reconnectMillis = 1_000L + ThreadLocalRandom.current().nextLong(1_000L);

    SseEmitter emitter = new SseEmitter(10 * 60_000L);

    ScheduledFuture<?> heartbeatTask = scheduler.scheduleAtFixedRate(() -> {
        try {
            emitter.send(SseEmitter.event().comment("hb"));
        }
        catch (IOException ex) {
            emitter.complete();
        }
    }, Duration.ofMillis(heartbeatMillis));

    Runnable cleanup = () -> heartbeatTask.cancel(false);
    emitter.onCompletion(cleanup);
    emitter.onTimeout(emitter::complete);
    emitter.onError(ex -> cleanup.run());

    emitter.send(SseEmitter.event()
            .name("ready")
            .reconnectTime(reconnectMillis)
            .data("connected"));

    replayMissedEvents(lastEventId, emitter);
    registry.add(emitter);
    return emitter;
}
```

여기서 분리해야 하는 의도는 명확하다.

- heartbeat comment: proxy idle timeout 방지 + disconnect 조기 감지
- `reconnectTime(...)`: 연결이 끊긴 뒤 브라우저 재접속 속도 제어
- `Last-Event-ID`: 재접속 뒤 손실 구간 복구

## 관측 체크리스트

SSE idle-timeout 이슈를 보면 다음 순서로 좁히는 편이 빠르다.

1. `SseEmitter`/MVC async timeout이 proxy idle보다 더 짧지 않은가?
2. heartbeat가 실제로 `Tmin`보다 충분히 짧은가?
3. Nginx/CDN이 heartbeat를 downstream으로 바로 전달하는가?
4. disconnect는 access log와 다음 write 실패 중 어디에서 먼저 보이는가?
5. reconnect가 `Last-Event-ID` replay와 연결되어 있는가?

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 선택하는가 |
|---|---|---|---|
| 짧은 heartbeat | idle close를 줄이고 disconnect를 빨리 감지한다 | write 비용과 로그 노이즈가 늘어난다 | 짧은 proxy idle, 민감한 실시간 UI |
| 긴 heartbeat | 비용이 적다 | deterministic idle close와 reconnect storm 위험이 커진다 | hop별 timeout이 충분히 길고 event 빈도가 높을 때 |
| comment heartbeat | payload 비용이 작고 UI 의미와 분리된다 | buffering이 있으면 관측이 어려울 수 있다 | pure keepalive 목적 |
| data heartbeat | client가 명시적으로 수신 사실을 볼 수 있다 | UI/도메인 이벤트와 구분이 흐려질 수 있다 | 클라이언트 관측까지 필요한 경우 |

핵심은 heartbeat를 "앱 내부 타이머"가 아니라 **proxy chain과 reconnect strategy를 묶는 네트워크 계약**으로 보는 것이다.

## 꼬리질문

> Q: heartbeat를 보내는데도 `SseEmitter` request가 먼저 끝나는 이유는 무엇인가?
> 의도: app timeout과 proxy idle timeout 구분 확인
> 핵심: heartbeat는 proxy idle은 리셋해도 async request 전체 수명 타이머를 자동 연장하지 않기 때문이다.

> Q: Nginx 앞에서는 heartbeat가 보이는데 브라우저는 몇십 초 뒤 끊기는 이유는 무엇인가?
> 의도: buffering 함정 확인
> 핵심: Nginx가 upstream 바이트는 읽어 timeout을 막아도, buffering 때문에 downstream으로 즉시 흘리지 않을 수 있기 때문이다.

> Q: 왜 reconnect delay를 heartbeat interval과 같은 값으로 맞추면 안 좋은가?
> 의도: reconnect와 keepalive 역할 분리 확인
> 핵심: keepalive 실패 주기와 reconnect 주기가 동기화되면 lock-step reconnect storm를 만들기 쉽기 때문이다.

> Q: `Last-Event-ID`가 없으면 왜 reconnect가 복구 전략이 아니라 손실 전략이 되는가?
> 의도: replay 복구 이해 확인
> 핵심: proxy idle close 직전/직후 사이에 놓친 business event를 재생할 기준점이 없기 때문이다.

## 한 줄 정리

SSE는 "연결이 길다"가 아니라 "여러 hop의 idle timer를 주기적 바이트와 reconnect 정책으로 함께 다루는 프로토콜"로 봐야 하며, `SseEmitter` heartbeat는 그 계약의 일부일 뿐 전부가 아니다.
