# Spring Async Timeout vs Disconnect Decision Tree

> 한 줄 요약: `AsyncRequestTimeoutException`은 기본 async timeout 신호이고, `AsyncRequestNotUsableException`은 이미 죽은 response에 다시 쓰려 할 때 드러나는 unusable 신호이며, raw disconnected-client 예외는 transport 계층 신호이므로, 네 가지 반환 타입은 "어떤 async primitive 위에 올라탔는가"와 "첫 바이트가 이미 나갔는가" 두 축으로 읽어야 헷갈리지 않는다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](./spring-mvc-async-deferredresult-callable-dispatch.md)
> - [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
> - [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
> - [Spring `ProblemDetail` Before-After Commit Matrix](./spring-problemdetail-before-after-commit-matrix.md)
> - [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)
> - [Spring Async MVC Streaming Observability Playbook](./spring-async-mvc-streaming-observability-playbook.md)
> - [Spring MVC Exception Resolver Chain Contract](./spring-mvc-exception-resolver-chain-contract.md)
> - [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)

retrieval-anchor-keywords: AsyncRequestTimeoutException, AsyncRequestNotUsableException, disconnected client signal, DeferredResult, ResponseBodyEmitter, SseEmitter, StreamingResponseBody, Callable, WebAsyncManager, TimeoutDeferredResultProcessingInterceptor, TimeoutCallableProcessingInterceptor, ResponseEntityExceptionHandler, DefaultHandlerExceptionResolver, DisconnectedClientHelper, broken pipe, ClientAbortException, EofException, ClosedChannelException, response committed, ProblemDetail, exception resolver, async timeout vs disconnect, decision tree, onTimeout, onError, onCompletion

## 핵심 개념

같은 "async endpoint가 실패했다"라도 Spring은 항상 같은 예외를 던지지 않는다.

먼저 네 타입을 두 가족으로 접어야 한다.

- `DeferredResult`: `DeferredResult` 자체가 async result holder다
- `ResponseBodyEmitter`, `SseEmitter`: 반환 타입은 streaming처럼 보이지만 내부적으로는 `DeferredResult` 기반 async lifecycle 위에 올라탄다
- `StreamingResponseBody`: `Callable` 기반 async execution으로 처리된다

그다음 예외 이름보다 먼저 물어야 할 질문은 둘이다.

1. servlet async timeout이 먼저 왔는가, 아니면 client/proxy disconnect나 write failure가 먼저 왔는가?
2. 첫 바이트가 이미 나가서 response가 commit되었는가, 아니면 아직 오류 응답으로 갈아엎을 수 있는가?

이 두 질문이 갈리면 해석도 갈린다.

- 첫 바이트 전 timeout: `AsyncRequestTimeoutException`은 아직 503 `ProblemDetail` 후보가 될 수 있다
- 첫 바이트 후 write failure: `AsyncRequestNotUsableException`이나 disconnected-client 신호는 transport 종료로 읽어야 한다
- completion 이후 late write: 이름은 `AsyncRequestNotUsableException`이어도 client disconnect가 아니라 post-completion write race일 수 있다

## 먼저 밑바닥을 맞춘다

| 반환 타입 | 실제 async primitive | Spring 기본 timeout 신호 | disconnect/unusable 신호가 붙는 자리 | cleanup 주체 |
|---|---|---|---|---|
| `DeferredResult<T>` | `WebAsyncManager.startDeferredResultProcessing(...)` | `TimeoutDeferredResultProcessingInterceptor`가 `AsyncRequestTimeoutException`를 error result로 넣는다 | container `onError`, final body write, completion 뒤 late write | `onTimeout`, `onError`, `onCompletion` |
| `ResponseBodyEmitter` | 내부적으로 `DeferredResult` + emitter handler | emitter timeout이 결국 `DeferredResult` timeout 경로로 들어간다 | `send(...)` 중 `IOException`, container `onError`, completion 뒤 추가 `send(...)` | `onTimeout`, `onError`, `onCompletion` |
| `SseEmitter` | 내부적으로 `DeferredResult` + SSE emitter handler | `ResponseBodyEmitter`와 동일 | 다음 event 또는 heartbeat `send(...)` 시점, container `onError` | `onTimeout`, `onError`, `onCompletion` |
| `StreamingResponseBody` | `WebAsyncManager.startCallableProcessing(...)` | `TimeoutCallableProcessingInterceptor`가 `AsyncRequestTimeoutException`를 concurrent result로 넣는다 | `write` / `flush` / `close`, container `onError`, completion 뒤 late write | 애플리케이션 `try/finally` |

핵심은 `ResponseBodyEmitter`와 `SseEmitter`를 "별도 timeout 시스템"으로 보면 안 된다는 점이다.

- 반환 타입 표면은 streaming이지만
- async timeout과 redispatch ownership은 `DeferredResult` 가족을 따른다

반대로 `StreamingResponseBody`는 emitter callback이 없고, `Callable` family의 timeout/interceptor 규칙을 따른다.

## 최상위 decision tree

```text
async endpoint에서 timeout/disconnect 같은 실패가 보임
-> 1. first successful send/flush 이전인가?
   -> yes
      -> 2. servlet async timeout notification이 먼저 왔는가?
         -> yes
            -> 기본 결과는 AsyncRequestTimeoutException
            -> resolver chain이 503으로 번역할 여지가 남아 있다
         -> no
            -> raw disconnected-client 신호 또는 AsyncRequestNotUsableException
            -> transport 문제로 읽는다
   -> no, 이미 첫 바이트가 나갔다
      -> 2. 다음 send/write/flush에서 실패했는가?
         -> yes
            -> raw disconnected-client 신호 또는 AsyncRequestNotUsableException
            -> response committed, 오류 body 재작성 불가
      -> 3. timeout callback이 뒤늦게 왔는가?
         -> yes
            -> timeout 신호 자체는 맞지만 이미 열린 stream 종료로 읽어야 한다
-> 4. completion callback 이후 late send/write였는가?
   -> yes
      -> AsyncRequestNotUsableException이라도 disconnect보다 post-completion write race 가능성이 높다
```

이 tree에서 가장 중요한 경계는 "첫 바이트"다.

- 첫 바이트 전: exception resolver와 `ProblemDetail` 계약이 아직 의미가 있다
- 첫 바이트 후: resolver보다 transport lifecycle과 cleanup이 더 중요하다

## 타입별 해석

### 1. `DeferredResult`는 "최종 한 번의 write" 직전까지 timeout 응답 후보가 남아 있다

`DeferredResult`는 스트리밍이 아니라 마지막 결과를 한 번 써서 끝내는 모델이다.

따라서 가장 전형적인 흐름은 이렇다.

```text
controller returns DeferredResult
-> request enters async mode
-> 외부 스레드/콜백이 result를 채움
-> redispatch
-> 최종 body write
```

이 타입에서 읽는 법은 단순하다.

- timeout이 결과 세팅보다 먼저 오고 첫 바이트도 아직 안 나갔다
  - 기본 결과는 `AsyncRequestTimeoutException`
  - `ResponseEntityExceptionHandler`나 default resolver가 503 경로를 태울 수 있다
- client/proxy가 final body write 전에 끊기거나 write 중 끊긴다
  - raw container 예외 또는 `AsyncRequestNotUsableException`로 기운다
  - 이 시점엔 timeout보다 disconnect가 원인 축이다
- timeout/completion 뒤에 외부 스레드가 늦게 `setResult(...)`를 시도한다
  - response를 되살리는 것이 아니라 late completion race를 만든다

즉 `DeferredResult`에선 "`AsyncRequestTimeoutException`인가?"보다 "`최종 body write 전에 timeout이 먼저 왔는가?"가 더 중요하다.

### 2. `ResponseBodyEmitter`는 첫 `send(...)` 전과 후가 완전히 다르다

`ResponseBodyEmitter`는 내부적으로 `DeferredResult`를 쓰지만, 첫 `send(...)`가 나가는 순간부터는 streaming response다.

- 첫 `send(...)` 전 timeout
  - 아직 `DeferredResult` family처럼 읽는다
  - `AsyncRequestTimeoutException`은 503 후보가 될 수 있다
- 첫 `send(...)` 후 timeout
  - timeout 신호는 맞더라도 response는 이미 commit됐다
  - 오류 body 재작성보다 stream 종료와 cleanup이 남는다
- `send(...)` 중 `IOException`
  - raw disconnect 또는 그 뒤 `AsyncRequestNotUsableException` 연쇄를 의심한다
- `onCompletion` 후 또 `send(...)`
  - client disconnect가 아니라 producer cancellation 누락일 수 있다

특히 `completeWithError(...)`를 recovery 버튼처럼 쓰면 틀리기 쉽다.

- commit 전에는 error dispatch로 이어질 수 있다
- commit 후에는 이미 열린 stream을 끝내는 신호에 가깝다

### 3. `SseEmitter`는 `ResponseBodyEmitter` 규칙에 heartbeat가 추가된 형태다

`SseEmitter`는 timeout/disconnect 해석 자체는 `ResponseBodyEmitter`와 같다.

다만 disconnected-client signal이 surface되는 타이밍이 더 늦어질 수 있다.

- business event가 뜸하면 끊김을 즉시 모른다
- 다음 event나 heartbeat를 보낼 때 비로소 disconnect가 드러난다
- 그래서 heartbeat 부재는 "disconnect를 늦게 surface하는 운영 문제"로 읽어야 한다

정리하면:

- 첫 event 전 timeout -> `AsyncRequestTimeoutException` 503 후보
- 첫 event 후 timeout -> 이미 열린 SSE 종료
- 다음 event/heartbeat write 실패 -> disconnected-client signal 또는 `AsyncRequestNotUsableException`

즉 `SseEmitter`에서 timeout vs disconnect를 가르는 가장 실무적인 질문은 "heartbeat가 있었는가?"다.

### 4. `StreamingResponseBody`는 `Callable` family라 callback보다 write loop가 중심이다

`StreamingResponseBody`는 `Callable` 기반 async 실행이므로 emitter callback이 없다.

흐름은 대략 이렇다.

```text
controller returns StreamingResponseBody
-> Spring starts Callable processing
-> worker thread executes writeTo(outputStream)
-> callback 종료 시 Spring이 outputMessage.flush() 한 번 더 수행
```

이 타입에서의 해석 기준은 다음과 같다.

- 첫 `flush()` 전 timeout
  - 기본 결과는 `AsyncRequestTimeoutException`
  - 미commit이면 503 경로가 가능하다
- 첫 `flush()` 후 timeout
  - 이름은 timeout이어도 이미 열린 download/stream 종료다
  - resolver보다 write loop cleanup이 중요하다
- `write` / `flush` / `close` 중 `IOException`
  - raw disconnect family 또는 `AsyncRequestNotUsableException`
  - 특히 container `onError` 이후 late flush가 겹치면 wrapper가 붙기 쉽다

즉 `StreamingResponseBody`는 "콜백이 무엇을 줬는가"보다 **어느 flush가 마지막 성공 flush였는가**를 로그로 남겨야 정확히 읽힌다.

## exception resolver는 무엇을 해 주고, 어디서 멈추는가

| 신호 | `ResponseEntityExceptionHandler` 기본 해석 | `DefaultHandlerExceptionResolver` 기본 해석 | 실무 해석 |
|---|---|---|---|
| `AsyncRequestTimeoutException` | `handleExceptionInternal(...)`로 위임한다. 단, response가 이미 commit되면 `null`을 반환한다 | `handleAsyncRequestTimeoutException(...)`는 `null`을 반환하고, 결국 uncommitted response라면 503 `sendError(...)`로 이어질 수 있다 | pre-commit timeout이면 HTTP 503 후보, post-commit timeout이면 더 이상 오류 계약을 재작성할 수 없다 |
| `AsyncRequestNotUsableException` | 기본 구현은 `null`을 반환한다 | 빈 `ModelAndView`를 반환하며 아무 것도 쓰지 않는다 | response unusable 신호다. API 오류 envelope가 아니라 transport/cancellation cleanup 대상으로 읽는다 |
| raw disconnected-client signal | custom advice가 잡아도 response가 usable하지 않으면 의미가 없다 | `DisconnectedClientHelper` 기준으로 empty `ModelAndView`로 처리한다 | `ClientAbortException`, `EofException`, `broken pipe`, `connection reset by peer`는 disconnect bucket으로 묶는다 |

즉 resolver 관점에서 요약하면 이렇다.

- `AsyncRequestTimeoutException`: "아직 응답을 쓸 수 있으면" 503로 번역 가능
- `AsyncRequestNotUsableException`: "더 이상 응답을 쓸 수 없으니" 번역 중단
- disconnected-client raw signal: "peer가 사라졌으니" 번역보다 suppression/정규화가 우선

## `AsyncRequestNotUsableException`는 항상 client disconnect가 아니다

이 예외는 `IOException` 하위 타입이지만, 의미는 "Spring bug"도 "항상 client abort"도 아니다.

보통 셋 중 하나다.

| 패턴 | 해석 | 먼저 볼 것 |
|---|---|---|
| cause 체인에 `ClientAbortException`, `EofException`, `ClosedChannelException`, `broken pipe`, `connection reset by peer`가 있다 | wrapped disconnect | container raw cause, access log, last successful flush |
| `onCompletion` 또는 timeout/error callback 뒤에 추가 `send`/`write`가 있다 | post-completion write race | producer cancel, scheduler 정리, subscription cleanup |
| timeout이 먼저 오고 그 뒤 response unusable이 된다 | timeout after unusable | timeout budget, worker cancellation, first-byte 여부 |

그래서 `AsyncRequestNotUsableException`를 볼 때는 예외 이름만 세지 말고 최소한 아래 셋을 같이 남겨야 한다.

- `commit_state=before_first_byte|after_first_byte`
- `phase=send|write|flush|completion_callback`
- `root_disconnect_family` 또는 `attribution`

## 빠른 판별 규칙

- `DeferredResult`에서 503 `ProblemDetail`을 기대한다면 final body write 전 timeout이어야 한다.
- `ResponseBodyEmitter`와 `SseEmitter`에서 첫 `send(...)` 후엔 timeout도 disconnect도 "이미 열린 stream을 어떻게 정리할 것인가" 문제다.
- `SseEmitter`에서 disconnect surface가 늦다면 먼저 heartbeat 부재를 의심한다.
- `StreamingResponseBody`에서 resolver보다 중요한 것은 마지막 성공 `flush()`와 `IOException` 위치다.
- `AsyncRequestNotUsableException`는 root cause라기보다 "지금 response에 더 못 쓴다"는 후행 신호일 때가 많다.

## 꼬리질문

> Q: `ResponseBodyEmitter`와 `SseEmitter`도 결국 `AsyncRequestTimeoutException`를 볼 수 있는데, 왜 stream 중간 timeout은 503처럼 안 보이는가?
> 의도: timeout signal과 commit 경계 분리 확인
> 핵심: timeout 신호 자체는 같아도 첫 send 뒤엔 response가 이미 commit되어 status/body를 다시 바꾸기 어렵기 때문이다.

> Q: `StreamingResponseBody`는 왜 emitter처럼 `onTimeout`/`onCompletion` 콜백이 없는데도 같은 timeout 예외를 볼 수 있는가?
> 의도: async primitive 차이 확인
> 핵심: 이 타입은 emitter family가 아니라 `Callable` family라서, timeout 인터셉터가 concurrent result로 `AsyncRequestTimeoutException`를 만든다.

> Q: `AsyncRequestNotUsableException`가 보이면 무조건 disconnected client인가?
> 의도: unusable와 disconnect 구분 확인
> 핵심: 아니다. raw disconnect wrapper일 수도 있지만, completion 뒤 late write race나 timeout 뒤 unusable 상태일 수도 있다.

## 한 줄 정리

`AsyncRequestTimeoutException`은 "아직 응답을 바꿀 수 있는 timeout"일 때 의미가 크고, `AsyncRequestNotUsableException`와 disconnected-client 신호는 대개 "이미 열린 응답 채널이 죽었다"는 뜻이므로, 네 반환 타입은 async primitive와 first-byte 경계로 먼저 분해해서 읽어야 한다.
