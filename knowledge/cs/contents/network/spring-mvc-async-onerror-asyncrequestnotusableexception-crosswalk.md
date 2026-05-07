---
schema_version: 3
title: "Spring MVC Async onError to AsyncRequestNotUsableException Crosswalk"
concept_id: network/spring-mvc-async-onerror-asyncrequestnotusableexception-crosswalk
canonical: true
category: network
difficulty: advanced
doc_role: bridge
level: advanced
language: mixed
source_priority: 89
mission_ids: []
review_feedback_tags:
- spring-async
- async-disconnect
- late-write
aliases:
- async onError timeline
- AsyncRequestNotUsableException timeline
- Spring MVC async onError
- response not usable after response errors
- committed response race
- late write Spring MVC
- emitter onError AsyncRequestNotUsableException
symptoms:
- AsyncRequestNotUsableException을 항상 1차 원인으로 읽고 raw write/flush failure를 놓친다
- AsyncListener.onError, Spring ERROR state, producer late write를 서로 다른 incident로 중복 집계한다
- response가 이미 commit된 뒤 JSON error envelope를 쓰려고 한다
- onCompletion 이후에도 scheduler/producer가 멈추지 않아 tail exception이 반복된다
intents:
- troubleshooting
- deep_dive
- comparison
prerequisites:
- network/network-spring-request-lifecycle-timeout-disconnect-bridge
- network/spring-disconnectedclienthelper-breadcrumb-wiring-mvc-download-sse-async-late-write
next_docs:
- spring/mvc-async-deferredresult-callable-dispatch
- spring/streamingresponsebody-responsebodyemitter-sse-commit-lifecycle
- spring/servlet-container-disconnect-exception-mapping
- network/container-specific-disconnect-logging-recipes-spring-boot
linked_paths:
- contents/network/network-spring-request-lifecycle-timeout-disconnect-bridge.md
- contents/network/container-specific-disconnect-logging-recipes-spring-boot.md
- contents/network/spring-disconnectedclienthelper-breadcrumb-wiring-mvc-download-sse-async-late-write.md
- contents/network/servlet-container-abort-surface-map-tomcat-jetty-undertow.md
- contents/network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md
- contents/network/sse-webflux-streaming-cancel-after-first-byte.md
- contents/spring/spring-mvc-async-deferredresult-callable-dispatch.md
- contents/spring/spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md
- contents/spring/spring-problemdetail-before-after-commit-matrix.md
- contents/spring/spring-servlet-container-disconnect-exception-mapping.md
confusable_with:
- network/spring-disconnectedclienthelper-breadcrumb-wiring-mvc-download-sse-async-late-write
- network/servlet-container-abort-surface-map-tomcat-jetty-undertow
- network/sse-webflux-streaming-cancel-after-first-byte
- spring/streamingresponsebody-responsebodyemitter-sse-commit-lifecycle
forbidden_neighbors: []
expected_queries:
- "Spring MVC async onError와 AsyncRequestNotUsableException은 같은 disconnect의 다른 시계야?"
- "AsyncRequestNotUsableException이 1차 원인이 아니라 late write guard일 수 있는 이유는?"
- "committed response race에서 raw ClientAbortException과 Spring ERROR state를 어떻게 읽어?"
- "Response not usable after response errors 메시지는 무엇을 의미해?"
- "SseEmitter나 DeferredResult producer가 onCompletion 뒤에도 쓰면 어떤 문제가 생겨?"
contextual_chunk_prefix: |
  이 문서는 Spring MVC async에서 AsyncListener.onError, raw container write
  failure, Spring ERROR state, AsyncRequestNotUsableException, late producer write를
  하나의 timeline으로 연결하는 advanced bridge다.
---
# Spring MVC Async `onError` -> `AsyncRequestNotUsableException` Crosswalk

> 한 줄 요약: Spring MVC async에서 `AsyncListener.onError`와 `AsyncRequestNotUsableException`은 같은 disconnect incident의 서로 다른 시계일 때가 많다. container가 먼저 본 1차 write/flush 실패, Spring이 `ERROR` 상태로 바꾼 시점, 그 뒤 늦게 깨어난 producer의 2차 late write를 한 타임라인으로 맞춰 읽어야 committed-response race를 오해하지 않는다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
> - [Container-Specific Disconnect Logging Recipes for Spring Boot](./container-specific-disconnect-logging-recipes-spring-boot.md)
> - [Spring `DisconnectedClientHelper` Breadcrumb Wiring: MVC Download, SSE, Async Late Write](./spring-disconnectedclienthelper-breadcrumb-wiring-mvc-download-sse-async-late-write.md)
> - [Servlet Container Abort Surface Map: Tomcat, Jetty, Undertow](./servlet-container-abort-surface-map-tomcat-jetty-undertow.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
> - [SSE/WebFlux Streaming Cancel After First Byte](./sse-webflux-streaming-cancel-after-first-byte.md)
> - [Spring MVC Async Dispatch with `Callable` / `DeferredResult`](../spring/spring-mvc-async-deferredresult-callable-dispatch.md)
> - [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](../spring/spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
> - [Spring `ProblemDetail` Before-After Commit Matrix](../spring/spring-problemdetail-before-after-commit-matrix.md)
> - [Spring Servlet Container Disconnect Exception Mapping](../spring/spring-servlet-container-disconnect-exception-mapping.md)

retrieval-anchor-keywords: async onerror timeline, asyncrequestnotusableexception timeline, spring mvc async onerror, async listener onerror, response not usable after response errors, response not usable after async request completion, committed response race, late write spring mvc, response commit disconnect race, disconnectedclienthelper late write breadcrumb, async late write breadcrumb, emitter onerror asyncrequestnotusableexception, tomcat clientabortexception onerror, jetty eofexception onerror, undertow UT010029 onerror, broken pipe after commit spring async

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

`onError`와 `AsyncRequestNotUsableException`은 보통 "같은 장애의 다른 순간"이다.

- transport 시계: peer close, proxy timeout, TCP reset, half-close
- container 시계: write/flush 실패 또는 async error 감지, `AsyncListener.onError` 통지
- Spring 시계: `StandardServletAsyncWebRequest`가 state를 `ERROR`로 바꾸고, 이후 response 접근을 `AsyncRequestNotUsableException`으로 막음

핵심은 `AsyncRequestNotUsableException`을 1차 원인으로 읽지 않는 것이다.

- 1차 원인 후보: Tomcat `ClientAbortException`, Jetty `EofException`, Undertow `IOException`/`ClosedChannelException`
- 2차 wrapper 후보: `AsyncRequestNotUsableException`
- 3차 꼬리 신호: `onCompletion` 뒤 `"Response not usable after async request completion."`

즉 진단 순서는 "Spring wrapper가 보였다"가 아니라 **어느 write/flush가 처음 실패했는가 -> response가 이미 commit됐는가 -> 그 뒤 producer가 몇 번 더 썼는가**다.

### Retrieval Anchors

- `async onerror timeline`
- `asyncrequestnotusableexception timeline`
- `spring mvc async onerror`
- `response not usable after response errors`
- `response not usable after async request completion`
- `committed response race`
- `late write spring mvc`
- `emitter onerror asyncrequestnotusableexception`

## 깊이 들어가기

### 1. 먼저 한 incident 안의 시계를 분리해야 한다

| 시점 | container에서 흔한 1차 표면 | Spring async state | 애플리케이션에서 보이는 것 | 해석 |
|---|---|---|---|---|
| peer는 이미 떠났지만 서버는 아직 모름 | 없음 | `ASYNC` | producer 계속 일함 | disconnect는 다음 write 전까지 잠복할 수 있다 |
| 다음 write/flush가 처음 실패 | Tomcat `ClientAbortException`, Jetty `EofException`, Undertow `IOException`/`ClosedChannelException` | `ASYNC -> ERROR` 또는 곧 `ERROR` | `send()`/`write()`/`flush()`에서 예외 | 이 순간이 대개 1차 transport signal이다 |
| container가 async error를 통지 | `AsyncListener.onError` | `ERROR` | `ResponseBodyEmitter.onError`, Spring exception handler, cleanup callback | container 시계가 Spring 시계에 반영된 순간이다 |
| producer가 늦게 다시 씀 | 새 raw container cause가 없을 수도 있음 | 이미 `ERROR` | `AsyncRequestNotUsableException("Response not usable after response errors.")` | 2차 late write guard다 |
| async lifecycle 종료 | `onComplete` | `COMPLETED` | `onCompletion` | cleanup 마지막 경계다 |
| 종료 뒤 또 씀 | 보통 새 I/O 없음 | `COMPLETED` | `AsyncRequestNotUsableException("Response not usable after async request completion.")` | 원인을 더 늦게 본 꼬리 신호다 |

같은 incident에서 `onError`, `AsyncRequestNotUsableException`, `onCompletion`이 모두 보일 수 있다.  
이 셋을 서로 다른 failure로 세면 noise가 급증하고, 하나로만 뭉개면 phase를 잃는다.

### 2. Spring은 state machine으로 2차 write를 막는다

Spring MVC async response wrapper는 실무적으로 아래 상태로 읽으면 된다.

```text
NEW
-> ASYNC
-> ERROR
-> COMPLETED
```

핵심 동작은 두 갈래다.

- raw write/flush가 직접 `IOException`으로 깨지면 Spring은 바로 state를 `ERROR`로 바꾸고, cause를 보존한 `AsyncRequestNotUsableException`을 던진다
- container `onError`가 먼저 오면 Spring은 state만 `ERROR`로 바꾸고, 그 뒤 늦은 response 접근에서 `"Response not usable after response errors."`를 던진다

즉 `AsyncRequestNotUsableException`에는 두 타입이 섞인다.

| top-level shape | 의미 | 보통 무엇을 먼저 확인하나 |
|---|---|---|
| `AsyncRequestNotUsableException(..., cause=ClientAbortException/EofException/IOException)` | 지금 막 write/flush가 실제로 실패했다 | nested cause, first failing write, response commit 여부 |
| `AsyncRequestNotUsableException("Response not usable after response errors.")` | `onError` 이후 2차 접근을 Spring이 막았다 | 직전 `onError`, 직전 raw container error, late producer 여부 |
| `AsyncRequestNotUsableException("Response not usable after async request completion.")` | `onCompletion` 뒤 또 썼다 | cleanup 누락, scheduler/producer 정지 누락 |

이 구분이 없으면 direct write failure와 secondary guard exception을 같은 심각도로 해석하게 된다.
실제로 Spring은 async state가 `ASYNC`일 때만 lock을 기다리고, `onError`가 state를 `ERROR`로 뒤집으면 더 기다리지 않고 late writer를 `AsyncRequestNotUsableException`으로 빠르게 돌려보낸다.  
그래서 이 예외는 deadlock 방지와 response 재사용 방지를 겸한 guardrail로 읽는 편이 정확하다.

### 3. committed-response race는 "누가 먼저 ERROR를 찍었는가"의 경쟁이다

response가 이미 commit된 뒤엔 status/code를 되돌리기 어렵다.  
그래서 문제는 business error보다 **wire delivery race**가 된다.

#### Race A: write failure가 먼저 surface

```text
first byte already committed
-> producer writes next chunk
-> container write/flush fails
-> Spring wraps raw IOException as AsyncRequestNotUsableException(cause=...)
-> container onError follows
-> producer writes again
-> "Response not usable after response errors."
```

이 패턴에선 첫 `AsyncRequestNotUsableException`이 1차 signal이고, 뒤의 동일 예외들은 꼬리 noise다.

#### Race B: `onError`가 먼저 state를 뒤집음

```text
peer closed or proxy timeout
-> container notices async error first
-> onError => state=ERROR
-> producer wakes up later and calls send()
-> "Response not usable after response errors."
```

이 패턴에선 raw container cause가 app log에 약하거나 quiet logger에만 남을 수 있다.  
그래서 `AsyncRequestNotUsableException`만 보면 "갑자기 unusable"처럼 보이지만, 실제 1차 signal은 조금 앞서 있었다.

#### Race C: `onCompletion`이 더 빨리 닫아 버림

```text
onError
-> cleanup / complete
-> onCompletion => state=COMPLETED
-> late scheduler tick or retry callback
-> "Response not usable after async request completion."
```

여기서는 `response errors`보다 `async request completion` 문구가 보이더라도, 최초 root cause는 직전 disconnect인 경우가 많다.

### 4. container별 1차 trigger와 2차 wrapper는 다르게 읽어야 한다

| container | committed-response에서 흔한 1차 trigger | `onError`와 wrapper의 실제 체감 순서 | 흔한 2차/후속 표면 | triage 포인트 |
|---|---|---|---|---|
| Tomcat | `ClientAbortException`, cause에 `Broken pipe`/`Connection reset by peer` | 대개 output buffer write/flush 실패 직후 `onError`, 그 뒤 late write guard | `AsyncRequestNotUsableException`, access log `200`/`206` with short bytes | Tomcat은 1차 cause 이름이 선명하다. 먼저 `ClientAbortException` timestamp를 잡는다 |
| Jetty | `EofException("Closed")` 또는 quiet EOF | quiet logger 때문에 raw cause가 짧게 남고, app 쪽에선 `onError` 또는 wrapper가 먼저 눈에 띄기 쉽다 | 반복 heartbeat/send에서 `AsyncRequestNotUsableException` | `org.eclipse.jetty.io`와 `org.eclipse.jetty.server`를 분리해 봐야 1차 cause를 놓치지 않는다 |
| Undertow | plain `IOException`, `ClosedChannelException`; 이미 닫힌 stream에 대한 `UT010029` | raw I/O failure와 `onError`, closed-stream secondary signal이 더 뒤섞여 보이기 쉽다 | `UT010029: Stream is closed`, `AsyncRequestNotUsableException` | Undertow는 `UT010029`를 primary disconnect로 단정하지 말고 선행 raw `IOException`이 있었는지 먼저 본다 |

중요한 건 vendor-neutral 해석이다.

- Tomcat은 **1차 cause 식별이 쉽다**
- Jetty는 **quiet EOF라서 1차 cause가 짧다**
- Undertow는 **primary raw I/O와 secondary closed-stream surface가 잘 섞인다**

즉 "`AsyncRequestNotUsableException`이 보였다"는 사실보다 **그 앞에 어떤 container dialect가 있었는가**가 더 중요하다.

### 5. emitter callback과 late write guard는 역할이 다르다

`ResponseBodyEmitter` / `SseEmitter`에서 흔한 오해는 `onError`와 `AsyncRequestNotUsableException`이 같은 책임을 가진다고 보는 것이다.

- `onError`: async lifecycle이 error 상태로 들어갔다는 통지다
- `onCompletion`: 더 이상 emitter를 쓸 수 없다는 최종 경계다
- `AsyncRequestNotUsableException`: 그 경계를 넘고도 response를 다시 쓰려는 코드를 막는 guard다

그래서 cleanup은 보통 `onCompletion` 중심이 맞다.

- `onError`에서 producer stop을 시작할 수는 있다
- 그래도 scheduler, retry callback, downstream bridge가 완전히 멈추는 최종 정리는 `onCompletion`에서 보장하는 편이 안전하다
- commit 후 `completeWithError(...)`는 JSON 오류 계약 복구가 아니라 async lifecycle 종료 신호에 가깝다

### 6. before-commit과 after-commit은 같은 `onError`라도 해석이 달라진다

| 경계 | 무엇이 아직 가능한가 | `onError` / wrapper 해석 |
|---|---|---|
| first byte 전 | status/body/error dispatch 재선택 여지 | app-level timeout/error와 transport failure가 아직 섞일 수 있다 |
| first byte 후 | status와 body 재작성 거의 불가 | `onError`와 wrapper는 거의 transport/delivery failure로 읽는다 |

따라서 committed-response race를 볼 때는 항상 아래 두 질문을 같이 둬야 한다.

- first byte가 이미 나갔는가
- access log bytes가 기대보다 짧은가

이 둘이 모두 맞으면 `AsyncRequestNotUsableException`은 보통 business exception이 아니라 **partial delivery signal**이다.

## 실전 시나리오

### 시나리오 1: SSE heartbeat에서 `onError` 뒤 `AsyncRequestNotUsableException`이 연속으로 찍힌다

브라우저는 이미 떠났고, heartbeat scheduler가 한 번 더 돌면서 2차 late write를 만든 패턴일 수 있다.

- 첫 신호: quiet EOF 또는 raw write failure
- 두 번째 신호: `onError`
- 세 번째 신호: 다음 heartbeat의 `AsyncRequestNotUsableException`

핵심 수정 포인트는 예외 suppress가 아니라 `onCompletion`에서 scheduler를 끊는 것이다.

### 시나리오 2: access log는 `200`, app log는 Tomcat `ClientAbortException`, 그 뒤 Spring wrapper가 보인다

response는 이미 commit됐고 일부 bytes도 나갔지만 caller는 중간에 떠난 패턴일 수 있다.  
business success와 wire delivery success를 분리해서 읽어야 한다.

### 시나리오 3: Jetty에선 짧은 `EofException: Closed` 한 줄 뒤에만 Spring wrapper가 두드러진다

Jetty quiet logging 때문에 1차 cause가 약하게 남고, 늦게 깨어난 producer가 더 눈에 띄는 패턴일 수 있다.  
이때 wrapper 건수만 세면 root cause보다 cleanup 누락 쪽만 과대평가하게 된다.

### 시나리오 4: Undertow에서 `UT010029`만 보고 primary abort로 분류한다

실제론 선행 plain `IOException` 또는 `ClosedChannelException`이 1차 disconnect였고, `UT010029`는 이미 닫힌 stream에 대한 2차 write일 수 있다.  
Undertow는 특히 "첫 raw I/O 실패"와 "그 뒤 닫힌 stream 재접근"을 분리해야 한다.

## 코드로 보기

### incident crosswalk를 로그 순서로 읽는 법

```text
1. first byte committed?
2. first raw container exception = ClientAbortException / EofException / IOException ?
3. AsyncListener.onError or emitter.onError timestamp
4. first AsyncRequestNotUsableException message:
   - "... failed to write/flush ..." + cause => direct write failure
   - "Response not usable after response errors." => onError 이후 2차 접근
   - "Response not usable after async request completion." => completion 이후 3차 접근
5. onCompletion timestamp
6. scheduler / producer stop timestamp
```

### 실전 triage 체크리스트

```text
- top-level AsyncRequestNotUsableException만 보지 말고 nested cause 유무를 먼저 본다
- access log status와 bytes_sent를 같이 본다
- emitter onError와 onCompletion 사이에 send/write가 더 있었는지 본다
- Tomcat은 ClientAbortException, Jetty는 EofException, Undertow는 raw IOException/UT010029를 각각 1차 후보로 잡는다
- cleanup 기준은 onError보다 onCompletion이 더 안전하다
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|---|---|---|---|
| `AsyncRequestNotUsableException`를 전부 한 bucket으로 묶기 | 대시보드가 단순하다 | direct write failure와 secondary late write를 섞는다 | high-level noise budget만 볼 때 |
| first container cause + Spring wrapper를 분리 집계 | root cause와 cleanup 누락을 따로 본다 | 로그/메트릭 설계가 더 복잡하다 | SSE, download, long-polling, async bridge |
| `onError`에서 즉시 producer stop | useless work를 빨리 줄인다 | 일부 cleanup path가 누락될 수 있다 | 고비용 stream producer |
| `onCompletion`을 cleanup 최종 경계로 유지 | timeout, error, 정상 종료를 모두 덮는다 | stop 시점이 한 박자 늦을 수 있다 | 일반적인 emitter/scheduler cleanup |

핵심은 `AsyncRequestNotUsableException` 자체를 제거하는 것이 아니라 **1차 cause와 2차 late write를 분리해서 읽는 것**이다.

## 꼬리질문

> Q: 왜 같은 incident에서 `onError`와 `AsyncRequestNotUsableException`이 둘 다 보이나요?
> 의도: callback과 guard의 역할 분리 확인
> 핵심: `onError`는 error 상태 진입 통지이고, `AsyncRequestNotUsableException`은 그 뒤 response 재사용을 막는 guard이기 때문이다.

> Q: access log가 `200`인데 `AsyncRequestNotUsableException`이 보일 수 있나요?
> 의도: commit 이후 delivery failure 이해 확인
> 핵심: 가능하다. first byte 이후 caller가 떠나면 business success와 wire delivery success가 갈라진다.

> Q: Undertow의 `UT010029`는 항상 1차 disconnect인가요?
> 의도: primary vs secondary signal 구분 확인
> 핵심: 아니다. 이미 닫힌 stream에 대한 2차 late write인 경우가 흔하다.

> Q: cleanup은 `onError`에 두는 게 맞나요, `onCompletion`에 두는 게 맞나요?
> 의도: emitter lifecycle 정리 전략 확인
> 핵심: stop 시작은 `onError`에 둘 수 있지만, 최종 cleanup 경계는 `onCompletion`이 더 안전하다.

## 한 줄 정리

Spring MVC async에서 `onError`는 error 상태 진입 통지이고 `AsyncRequestNotUsableException`은 그 뒤 늦은 response 접근을 막는 guard이므로, committed-response race는 항상 **첫 container cause -> `onError` -> late write wrapper -> `onCompletion`** 순서로 교차 확인해야 한다.
