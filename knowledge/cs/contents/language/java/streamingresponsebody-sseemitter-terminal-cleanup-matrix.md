---
schema_version: 3
title: StreamingResponseBody SseEmitter Terminal Cleanup Matrix
concept_id: language/streamingresponsebody-sseemitter-terminal-cleanup-matrix
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
- cleanup
- sse
aliases:
- StreamingResponseBody and SseEmitter Terminal Cleanup Matrix
- streaming terminal cleanup matrix
- post commit streaming error cleanup
- producer cancellation after broken pipe
- late write suppression
- SseEmitter onCompletion cleanup
symptoms:
- 첫 바이트 이후 StreamingResponseBody나 SseEmitter 실패를 아직 error response로 바꿀 수 있는 application failure로 취급해 response rewrite를 시도해
- timeout disconnect normal complete late write failure별 cleanup 코드를 따로 두어 producer stop, resource release, closed flag suppression이 중복되거나 누락돼
- writer IOException이나 emitter onCompletion이 DB query, HTTP download, scheduler, subscription cancel까지 자동으로 처리한다고 추정해
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- language/streaming-response-abort-surfaces-servlet-virtual-threads
- language/servlet-asynclistener-cleanup-patterns
- language/servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads
next_docs:
- language/sse-last-event-id-replay-reconnect-ownership
- spring/servlet-container-disconnect-exception-mapping
- network/client-disconnect-499-broken-pipe-cancellation-proxy-chain
linked_paths:
- contents/language/java/streaming-response-abort-surfaces-servlet-virtual-threads.md
- contents/language/java/servlet-asynclistener-cleanup-patterns.md
- contents/language/java/servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads.md
- contents/language/java/virtual-thread-jdbc-cancel-semantics.md
- contents/language/java/thread-interruption-cooperative-cancellation-playbook.md
- contents/spring/spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md
- contents/spring/spring-servlet-container-disconnect-exception-mapping.md
- contents/spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md
- contents/network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md
confusable_with:
- language/streaming-response-abort-surfaces-servlet-virtual-threads
- language/sse-last-event-id-replay-reconnect-ownership
- language/servlet-asynclistener-cleanup-patterns
forbidden_neighbors: []
expected_queries:
- StreamingResponseBody와 SseEmitter terminal cleanup은 stop producer release resources suppress late write 순서로 왜 묶어야 해?
- 첫 바이트 이후 broken pipe가 나면 response rewrite가 아니라 transport phase terminal signal로 봐야 하는 이유가 뭐야?
- StreamingResponseBody는 write flush IOException이고 SseEmitter는 send heartbeat onCompletion이 주요 abort surface라는 차이를 알려줘
- late write failure를 새 장애로 보지 않고 closed flag로 suppression하는 패턴을 설명해줘
- streaming response cleanup matrix에서 timeout disconnect normal complete를 같은 idempotent cleanup contract로 묶는 방법이 뭐야?
contextual_chunk_prefix: |
  이 문서는 StreamingResponseBody와 SseEmitter post-commit terminal signal을 stop producer, release resources, suppress late write cleanup contract로 묶는 advanced playbook이다.
  StreamingResponseBody cleanup, SseEmitter cleanup, broken pipe, late write suppression, terminal cleanup matrix 질문이 본 문서에 매핑된다.
---
# `StreamingResponseBody` and `SseEmitter` Terminal Cleanup Matrix

> 한 줄 요약: `StreamingResponseBody`와 `SseEmitter`는 첫 바이트 이후 failure를 "응답 생성 실패"가 아니라 transport-phase terminal signal로 다뤄야 하며, portable한 설계는 signal 관측 지점보다 `stop producer -> release resources -> suppress late write` 순서를 같은 cleanup contract로 묶는 데 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Streaming Response Abort Surfaces: `StreamingResponseBody`, SSE, and Virtual-Thread Cancellation Gaps](./streaming-response-abort-surfaces-servlet-virtual-threads.md)
> - [Servlet `AsyncListener` Cleanup Patterns for `Callable`, `WebAsyncTask`, and `DeferredResult`](./servlet-asynclistener-cleanup-patterns.md)
> - [Servlet Container Timeout and Cancellation Boundaries: Spring MVC and Virtual Threads](./servlet-container-timeout-cancellation-boundaries-spring-mvc-virtual-threads.md)
> - [Virtual-Thread JDBC Cancel Semantics](./virtual-thread-jdbc-cancel-semantics.md)
> - [Thread Interruption and Cooperative Cancellation Playbook](./thread-interruption-cooperative-cancellation-playbook.md)
> - [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](../../spring/spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
> - [Spring Servlet Container Disconnect Exception Mapping](../../spring/spring-servlet-container-disconnect-exception-mapping.md)
> - [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](../../spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](../../network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)

> retrieval-anchor-keywords: StreamingResponseBody cleanup matrix, SseEmitter cleanup matrix, terminal cleanup matrix, post-commit streaming error, late write handling, response committed error handling, response committed broken pipe, streaming async cleanup, stream disconnect cleanup, SseEmitter onCompletion cleanup, StreamingResponseBody IOException cleanup, AsyncRequestNotUsableException cleanup, ClientAbortException cleanup, EofException cleanup, ClosedChannelException cleanup, heartbeat disconnect probe, producer cancellation after commit, late completion suppression, portable streaming cleanup, transport phase failure, response rewrite impossible after commit

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [Terminal Cleanup Matrix](#terminal-cleanup-matrix)
- [휴대성 있는 설계 규칙](#휴대성-있는-설계-규칙)
- [타입별 해석 차이](#타입별-해석-차이)
- [코드로 보기](#코드로-보기)
- [관측 포인트](#관측-포인트)
- [실전 시나리오](#실전-시나리오)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄-정리)

</details>

## 핵심 개념

`StreamingResponseBody`와 `SseEmitter`를 같이 읽을 때 제일 먼저 버려야 하는 직관은 "마지막에 예외가 났으니 아직 응답을 실패로 바꿀 수 있겠지"라는 기대다.

첫 바이트가 나간 뒤에는 보통 이미 다음 경계가 닫혀 있다.

- status / header를 다시 고치는 **response rewrite**
- `ProblemDetail` 같은 body contract를 새로 쓰는 **application error rendering**
- producer가 계속 일해도 된다고 착각하는 **lifetime ownership**

남는 것은 대체로 세 가지뿐이다.

- 더 이상 쓸 수 없다는 **terminal signal 관측**
- 아직 남아 있는 producer와 downstream I/O를 멈추는 **stop**
- 이미 끝난 request에 다시 쓰려는 late completion을 무해화하는 **suppression**

portable cleanup contract는 framework callback 이름이 아니라 이 세 책임으로 정리해야 읽기가 쉽다.

## Terminal Cleanup Matrix

| 상황 | `StreamingResponseBody`에서 먼저 보이는 표면 | `SseEmitter`에서 먼저 보이는 표면 | portable하게 반드시 해야 하는 일 | 하지 말아야 할 기대 |
|---|---|---|---|---|
| 첫 바이트 이전 producer 실패 | callback 안 예외, `IOException`, MVC async error path | 첫 `send(...)` 전 예외, `completeWithError(...)` 가능 | commit 전이면 실패 응답 선택 + stop + release | 이미 일부 body가 나간 것처럼 가정 |
| 첫 바이트 이후 peer disconnect | 다음 `write()` / `flush()` / `close()`의 `IOException`, container-specific abort, 이후 `AsyncRequestNotUsableException` | 다음 `send(...)` 또는 heartbeat의 예외, 이어서 `onError` / `onCompletion` | stop token flip, detached task cancel, DB/HTTP/file handle 정리, late send 억제 | 즉시 thread interrupt 보장, 상태 코드 재작성 |
| async timeout이 먼저 옴 | container timeout, 경우에 따라 async error/complete, writer는 나중에 unusable response를 만날 수 있음 | `onTimeout`, 뒤이어 `onCompletion` | timeout fallback이 있다면 commit 전만 사용, commit 후에는 stop + release를 우선 | timeout이 producer와 downstream I/O를 자동 종료 |
| 애플리케이션이 정상 종료를 선택 | callback return 후 stream close/flush | `emitter.complete()` 후 `onCompletion` | completion path에서도 같은 release backstop 실행 | 정상 종료면 cleanup 코드가 필요 없다고 가정 |
| terminal signal 뒤 늦게 producer가 다시 씀 | 추가 `write()`에서 `AsyncRequestNotUsableException` 또는 같은 abort 예외 재노출 | late `send(...)`가 실패하거나 무의미해짐 | `closed`/`stop` flag로 late write suppress, noisy log sampling | late write를 새 장애로 해석 |
| transport abort 뒤 query / remote call이 남음 | writer 실패와 별개로 DB/HTTP task가 계속 돈다 | `onCompletion` 뒤에도 scheduler/future/subscription이 남을 수 있음 | response signal과 실제 producer cancel을 분리 기록 | writer 예외가 query cancel까지 했다고 추정 |

표를 읽는 핵심은 단순하다.

- `StreamingResponseBody`의 1차 표면은 대개 **다음 write/flush**
- `SseEmitter`의 1차 표면은 대개 **다음 send/heartbeat + completion callback**
- 둘 다 cleanup contract의 핵심은 **response 재작성**이 아니라 **producer와 resource ownership 종료**

## 휴대성 있는 설계 규칙

### 1. cleanup은 "이유별 callback"이 아니라 "한 번만 닫히는 contract"로 만든다

`timeout`, `disconnect`, `normal complete`, `late write failure`를 각각 따로 정리하면 중복과 누락이 같이 생긴다.

휴대성 있는 구조는 보통 다음 셋을 같은 coordinator로 묶는다.

- `stop(reason)`: producer에게 더 진행하지 말라고 알림
- `release()`: scheduler, subscription, registry, file handle을 정리
- `markClosed()`: 이후 late write를 suppression path로 보냄

이렇게 하면 `IOException`, `onTimeout`, `onCompletion`이 어느 순서로 오더라도 idempotent하게 수습할 수 있다.

### 2. `StreamingResponseBody`는 `flush` cadence가 곧 disconnect probe다

`StreamingResponseBody`에는 emitter callback이 없으므로 disconnect를 빨리 알 방법이 결국 다음 `write`/`flush`뿐인 경우가 많다.

따라서 flush 정책은 UX knob이면서 cleanup latency knob이기도 하다.

- 너무 드문 flush: disconnect를 늦게 알아 producer가 더 오래 돈다
- 너무 잦은 flush: throughput과 syscall/TLS overhead가 커진다

즉 batch 경계는 전송 효율뿐 아니라 **cleanup signal budget**으로도 잡아야 한다.

### 3. `SseEmitter`는 heartbeat가 keepalive이자 cleanup probe다

SSE는 business event가 없으면 disconnect가 오래 숨어 있을 수 있다.

그래서 heartbeat는 두 역할을 동시에 가진다.

- proxy idle timeout을 넘기지 않게 하는 keepalive
- 끊긴 연결을 다음 `send(...)`보다 빨리 발견하는 disconnect probe

이때 scheduler cancel을 `onCompletion`에 두지 않으면, heartbeat가 오히려 leak source가 된다.

### 4. commit 이후엔 `completeWithError`보다 stop/release가 우선이다

이미 first byte가 나간 뒤라면 `completeWithError(...)`는 대개 "응답을 예쁘게 바꾸는 API"가 아니다.

실제 우선순위는 보통 이렇다.

1. producer가 더 이상 새 데이터를 만들지 못하게 한다
2. query, remote call, subscription, scheduler를 정리한다
3. late write를 noisy error가 아니라 closed-path metric으로 보낸다

즉 post-commit error의 중심은 error payload가 아니라 **terminal cleanup ordering**이다.

### 5. writer 실패와 producer 종료는 다른 metric으로 남긴다

실무에서 자주 놓치는 것은 "`ClientAbortException`이 있었으니 cleanup도 됐겠지"라는 추정이다.

최소한 아래 둘은 분리해 두는 편이 안전하다.

- `response_terminal_signal_total`
- `producer_cancelled_total`

둘이 같이 안 오르면 late-write suppression이나 downstream cancel wiring에 구멍이 있다는 뜻일 수 있다.

## 타입별 해석 차이

### `StreamingResponseBody`

`StreamingResponseBody`는 callback 자체가 writer다. 그래서 cleanup reasoning이 보통 "예외를 catch한 지점"에 많이 모인다.

주의할 점은 두 가지다.

- writer thread와 row producer / DB query / remote stream이 같은 생명주기라는 보장이 없다
- callback이 끝났다고 해서 upstream producer가 자동 종료되는 것도 아니다

따라서 catch block에서는 보통 다음 정도만 신뢰한다.

- 지금 response는 더 못 쓴다
- stop token을 올리고 cancellation ladder를 시작해야 한다
- late write 시도는 closed path로 버려야 한다

### `SseEmitter`

`SseEmitter`는 send surface와 completion surface가 분리돼 있다.

그래서 reasoning도 분리해야 한다.

- `send(...)` 실패: transport가 더 못 간다는 신호
- `onTimeout`: timeout-specific 정책 결정
- `onCompletion`: 이유와 무관한 최종 cleanup backstop

특히 SSE는 producer가 controller 밖 scheduler, broker listener, polling task에 붙는 경우가 많아서 `onCompletion`이 사실상 ownership 종료 지점이다.

### 공통점

두 타입 모두 commit 이후에는 다음 판단이 공통이다.

- transport failure는 application error body보다 cleanup 우선
- stop signal은 request lifetime에서 producer lifetime으로 번역돼야 함
- late write는 새 응답이 아니라 suppress 대상

## 코드로 보기

### terminal cleanup coordinator

```java
public final class StreamTerminalCleanup {
    private final AtomicBoolean stopOnce = new AtomicBoolean();
    private final AtomicBoolean releaseOnce = new AtomicBoolean();
    private final AtomicBoolean closed = new AtomicBoolean();
    private final Consumer<String> stopProducer;
    private final Runnable releaseResources;

    public StreamTerminalCleanup(
        Consumer<String> stopProducer,
        Runnable releaseResources
    ) {
        this.stopProducer = stopProducer;
        this.releaseResources = releaseResources;
    }

    public void terminal(String reason) {
        closed.set(true);
        if (stopOnce.compareAndSet(false, true)) {
            stopProducer.accept(reason);
        }
        if (releaseOnce.compareAndSet(false, true)) {
            releaseResources.run();
        }
    }

    public boolean isClosed() {
        return closed.get();
    }
}
```

핵심은 callback별로 다른 cleanup을 만들지 않고, terminal signal이 오면 같은 contract를 닫는다는 점이다.

### `StreamingResponseBody`: late write failure를 cleanup contract에 연결

```java
@GetMapping(value = "/exports/orders", produces = MediaType.APPLICATION_NDJSON_VALUE)
public ResponseEntity<StreamingResponseBody> exportOrders() {
    StreamTerminalCleanup cleanup = new StreamTerminalCleanup(
        reason -> exportService.cancel(reason),
        () -> exportService.release()
    );

    StreamingResponseBody body = outputStream -> {
        try (BufferedWriter writer =
                 new BufferedWriter(new OutputStreamWriter(outputStream, StandardCharsets.UTF_8))) {
            int count = 0;
            for (OrderRow row : exportService.streamRows()) {
                if (cleanup.isClosed() || Thread.currentThread().isInterrupted()) {
                    return;
                }

                writer.write(toNdjson(row));
                writer.newLine();

                if (++count % 100 == 0) {
                    writer.flush();
                }
            }

            writer.flush();
        } catch (IOException ex) {
            cleanup.terminal("response-write-failed");
        } finally {
            cleanup.terminal("stream-finished");
        }
    };

    return ResponseEntity.ok(body);
}
```

이 패턴에서 중요한 점은 `IOException`을 "실패 응답 생성"으로 보내지 않는 것이다. 이미 commit 이후일 수 있으므로 cleanup contract를 닫는 쪽이 더 portable하다.

### `SseEmitter`: send surface와 completion surface를 같은 cleanup으로 묶기

```java
@GetMapping(path = "/events/orders", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public SseEmitter orderEvents() {
    SseEmitter emitter = new SseEmitter(60_000L);
    StreamTerminalCleanup cleanup = new StreamTerminalCleanup(
        reason -> subscriptionRegistry.cancel("orders", reason),
        () -> heartbeatRegistry.stop("orders")
    );

    emitter.onTimeout(() -> cleanup.terminal("timeout"));
    emitter.onError(ex -> cleanup.terminal("send-error"));
    emitter.onCompletion(() -> cleanup.terminal("completion"));

    heartbeatRegistry.start("orders", () -> {
        if (cleanup.isClosed()) {
            return;
        }

        try {
            emitter.send(SseEmitter.event().comment("keepalive"));
        } catch (IOException ex) {
            cleanup.terminal("heartbeat-write-failed");
        }
    });

    return emitter;
}
```

여기서는 `onCompletion`이 가장 중요한 backstop이다. `timeout`, `disconnect`, `normal complete`가 섞여도 최종 정리는 한 번만 실행된다.

## 관측 포인트

| 질문 | 최소 관측값 | 이유 |
|---|---|---|
| transport가 먼저 끊겼는가 | root exception family, phase=`write|flush|send|completion` | `ClientAbortException`류와 late `AsyncRequestNotUsableException`를 같은 bucket으로 묶기 위해 |
| cleanup이 실제로 됐는가 | `producer_cancelled_total`, `resource_release_total` | writer 실패만 보고 cleanup 성공으로 오해하지 않기 위해 |
| late write가 남는가 | `late_write_suppressed_total` | terminal 이후 producer가 계속 밀어넣는지 보기 위해 |
| disconnect를 얼마나 늦게 보는가 | last-successful-write 시각, next-failed-write 시각, heartbeat interval | flush/heartbeat cadence가 cleanup latency를 만들기 때문에 |

특히 SSE와 download endpoint는 access log 성공 여부와 transport completion 여부를 분리해서 보는 편이 안전하다.

## 실전 시나리오

### 시나리오 1: 다운로드는 broken pipe로 끝났는데 export query는 계속 돈다

이 경우 해석은 보통 "writer failure는 봤지만 producer cancellation ladder를 연결하지 않았다"에 가깝다.

- `StreamingResponseBody` catch block은 있었다
- 하지만 query cancel registry나 stop token flip이 없었다
- 그래서 next write failure 이후에도 row fetch가 계속 이어졌다

### 시나리오 2: SSE 탭을 닫았는데 heartbeat scheduler가 계속 돈다

대개 `onCompletion`을 cleanup backstop으로 쓰지 않았거나, scheduler cancel이 `onTimeout`에만 묶여 있는 경우다.

이때 필요한 것은 더 화려한 예외 변환이 아니라:

- `onCompletion` 기반 release
- late heartbeat suppression
- heartbeat interval과 proxy idle timeout 정렬

### 시나리오 3: `AsyncRequestNotUsableException`만 많이 보여 원인이 헷갈린다

이건 새 failure family라기보다 이미 terminal 상태가 된 response에 late write가 들어간 후행 신호일 수 있다.

그래서 해석은 보통 이렇게 한다.

- 최초 signal: `ClientAbortException` / `IOException` / timeout / completion
- 후행 signal: late write가 만든 `AsyncRequestNotUsableException`

즉 alerting은 후행 예외 count보다 **최초 terminal signal과 cleanup 누락 비율**을 중심으로 잡는 편이 낫다.

## 꼬리질문

> Q: 왜 post-commit error에서 `ProblemDetail`보다 cleanup ordering을 먼저 봐야 하나?
> 의도: commit 이후 failure의 본질 확인
> 핵심: 첫 바이트 이후에는 응답 메타데이터 ownership이 닫혀 있어 transport failure를 애플리케이션 오류 응답으로 다시 포장하기 어렵기 때문이다.

> Q: `StreamingResponseBody`는 emitter callback이 없는데 어떻게 portable하게 cleanup을 묶나?
> 의도: writer-only surface의 대응 확인
> 핵심: `IOException`/`flush` failure를 terminal signal로 보고, stop token과 downstream cancel ladder를 idempotent coordinator에 연결하면 된다.

> Q: `SseEmitter`에서 왜 `onTimeout`보다 `onCompletion`이 더 중요한가?
> 의도: terminal callback 역할 확인
> 핵심: timeout, disconnect, 정상 종료를 모두 포함하는 최종 ownership 종료 지점이기 때문이다.

## 한 줄 정리

`StreamingResponseBody`와 `SseEmitter`의 차이는 terminal signal이 surface되는 자리이고, portable cleanup의 핵심은 둘 다 **post-commit failure를 stop/release/late-write suppression contract로 닫는 것**이다.
