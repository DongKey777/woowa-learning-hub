---
schema_version: 3
title: Spring Async MVC Streaming Observability Playbook
concept_id: spring/async-mvc-streaming-observability-playbook
canonical: true
category: spring
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 84
review_feedback_tags:
- async-mvc-streaming
- observability
- streamingresponsebody-metrics
- responsebodyemitter-metrics
aliases:
- async MVC streaming observability
- StreamingResponseBody metrics
- ResponseBodyEmitter metrics
- SseEmitter metrics
- first byte latency
- last successful flush
- AsyncRequestNotUsableException attribution
- client abort ratio
intents:
- troubleshooting
- design
symptoms:
- streaming endpoint에서 http.server.requests만 보고 timeout, disconnect, app error가 섞여 보인다.
- first byte 이후 실패라서 ProblemDetail 응답으로 바뀌지 않고 partial response나 broken pipe로 남는다.
- SSE reconnect noise와 실제 proxy idle timeout 또는 flush cadence 문제를 구분하기 어렵다.
linked_paths:
- contents/spring/spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md
- contents/spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md
- contents/spring/spring-servlet-container-disconnect-exception-mapping.md
- contents/spring/spring-partial-response-access-log-interpretation.md
- contents/spring/spring-observability-micrometer-tracing.md
- contents/spring/spring-problemdetail-before-after-commit-matrix.md
- contents/spring/spring-sse-proxy-idle-timeout-matrix.md
- contents/spring/spring-sse-disconnect-observability-patterns.md
- contents/network/request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md
- contents/network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md
expected_queries:
- Spring MVC streaming endpoint는 어떤 메트릭을 남겨야 해?
- SseEmitter disconnect와 timeout을 observability에서 어떻게 구분해?
- AsyncRequestNotUsableException이 root cause인지 후행 신호인지 어떻게 판단해?
- first byte latency와 last successful flush를 따로 봐야 하는 이유가 뭐야?
contextual_chunk_prefix: |
  이 문서는 Spring Async MVC streaming endpoint의 관측 playbook이다.
  StreamingResponseBody, ResponseBodyEmitter, SseEmitter, first successful flush,
  last_successful_flush, completion_cause, AsyncRequestNotUsableException,
  broken pipe, client abort, proxy idle timeout, Micrometer low-cardinality tag를
  분리해 alert noise와 실제 성능 문제를 구분한다.
---
# Spring Async MVC Streaming Observability Playbook

> 한 줄 요약: async MVC streaming 관측은 "요청 하나가 몇 ms 걸렸는가"보다 먼저 first-byte latency, 마지막 성공 flush, completion cause, `AsyncRequestNotUsableException`의 원인 귀속을 분리해야 alert noise와 실제 성능 문제를 구분할 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
> - [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
> - [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)
> - [Spring Partial-Response Access Log Interpretation](./spring-partial-response-access-log-interpretation.md)
> - [Spring Observability with Micrometer Tracing](./spring-observability-micrometer-tracing.md)
> - [Spring `ProblemDetail` Before-After Commit Matrix](./spring-problemdetail-before-after-commit-matrix.md)
> - [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)
> - [Spring SSE Disconnect Observability Patterns](./spring-sse-disconnect-observability-patterns.md)
> - [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](../network/request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](../network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)

retrieval-anchor-keywords: async mvc streaming observability, streaming observability playbook, first-byte latency, time to first byte, TTFB, first flush, last flush, last successful flush, last_flush_age, completion cause, stream completion cause, async streaming metrics, async streaming logs, StreamingResponseBody metrics, ResponseBodyEmitter metrics, SseEmitter metrics, partial response access log, bytes sent interpretation, access log status bytes duration, AsyncRequestNotUsableException attribution, disconnected client attribution, broken pipe attribution, ClientAbortException, EofException, ClosedChannelException, response commit observability, emitter onCompletion, emitter onTimeout, emitter onError, Micrometer Observation, low cardinality tags, client abort ratio, stream duration, bytes sent, flush count, SSE disconnect observability, heartbeat gap, reconnect noise, reconnect pressure, SSE alert thresholds

## 핵심 개념

streaming endpoint에서 운영 해석을 어렵게 만드는 이유는 "비즈니스 작업 완료"와 "응답 전송 완료"가 같은 말이 아니기 때문이다.

- first byte 전: 아직 일반 HTTP 오류 계약과 timeout 해석이 가능하다
- first byte 후: response는 이미 commit됐고, 이후 실패는 transport/write lifecycle로 기운다
- completion 시점: 정상 종료, timeout, disconnect, post-completion write race가 서로 다른 의미를 가진다

따라서 `http.server.requests` 하나만 보면 다음 네 질문이 섞여 버린다.

1. 첫 바이트가 늦었는가?
2. 중간 flush cadence가 끊겼는가?
3. 마지막 성공 flush 뒤 idle 상태로 timeout/disconnect가 났는가?
4. `AsyncRequestNotUsableException`이 root cause인가, 이미 죽은 response에 뒤늦게 쓴 후행 신호인가?

이 플레이북의 목표는 이 네 축을 분리해서 로그와 메트릭을 남기는 것이다.

## 먼저 깔아둘 타임라인

최소한 아래 이벤트를 같은 request/trace에 묶어 남겨야 한다.

| 이벤트 | 의미 | 왜 필요한가 |
|---|---|---|
| `request_start` | servlet request 진입 | 기준 시각이 없으면 first-byte latency를 계산할 수 없다 |
| `async_started` | MVC가 async mode로 전환됨 | sync path와 async path를 분리한다 |
| `first_body_write_attempt` | 첫 `send()` 또는 첫 `write()` 시도 | app이 첫 chunk를 언제 밀기 시작했는지 본다 |
| `first_successful_flush` | 첫 flush 성공 | response commit 및 TTFB 관측의 핵심 경계다 |
| `last_successful_flush` | 가장 마지막으로 성공한 flush | timeout/disconnect 직전까지 실제로 데이터가 흘렀는지 본다 |
| `completion_signal` | `onCompletion`, callback 종료, async complete | stream lifecycle이 종료된 시각이다 |
| `error_signal` | `onError`, `IOException`, `AsyncRequestNotUsableException` | 종료 원인 귀속에 필요하다 |
| `timeout_signal` | `onTimeout`, async timeout | app bug와 timeout을 분리한다 |

여기서 중요한 점은 `last_successful_flush`가 "마지막 write 시도"가 아니라 **실제로 flush가 성공한 마지막 순간**이어야 한다는 것이다.

- 마지막 write 시도 직후 예외가 났다면 last flush는 더 과거일 수 있다
- proxy idle timeout은 "오랫동안 flush가 없었다"는 패턴으로 더 잘 보인다
- client abort는 last flush 직후 곧바로 다음 write에서 터질 수도 있다

## 메트릭 설계

### 1. 최소 메트릭 세트

streaming endpoint에는 아래 네 계열 메트릭이 있으면 운영 해석이 크게 좋아진다.

| 메트릭 | 타입 | 권장 태그 | 목적 |
|---|---|---|---|
| `http.server.streaming.first_byte` | timer | `route`, `stream_type`, `outcome` | request start부터 first successful flush까지의 latency |
| `http.server.streaming.active` | long task timer 또는 gauge | `route`, `stream_type` | 현재 열려 있는 stream 수 |
| `http.server.streaming.flush.count` | counter 또는 distribution summary | `route`, `stream_type` | flush cadence 과소/과다를 본다 |
| `http.server.streaming.last_flush_age` | timer 또는 summary | `route`, `stream_type`, `completion_cause` | completion 시점 기준 "마지막 성공 flush 이후 얼마나 비었나"를 본다 |
| `http.server.streaming.completion` | counter | `route`, `stream_type`, `completion_cause`, `commit_state` | 종료 원인을 비율로 본다 |
| `http.server.streaming.disconnect` | counter | `route`, `stream_type`, `disconnect_family`, `phase` | `AsyncRequestNotUsableException`와 raw container cause를 구분한다 |

`outcome`과 `completion_cause`는 비슷해 보여도 분리하는 편이 좋다.

- `outcome`: 메트릭 조회용 큰 버킷 (`normal`, `timeout`, `disconnect`, `app_error`)
- `completion_cause`: drilldown용 세부 버킷 (`normal_complete`, `async_timeout`, `client_abort`, `proxy_idle_timeout_suspected`, `post_completion_write`, `app_exception`)

### 2. 저카디널리티 태그만 남긴다

권장 태그:

- `route=/exports/{id}`
- `stream_type=streaming_response_body|response_body_emitter|sse_emitter`
- `completion_cause=normal_complete|async_timeout|disconnect|post_completion_write|app_error`
- `disconnect_family=tomcat_client_abort|jetty_eof|undertow_closed_channel|spring_async_not_usable|io_broken_pipe_or_reset|unknown`
- `phase=first_write|mid_stream_write|flush|completion_callback`
- `commit_state=before_first_byte|after_first_byte`

피해야 할 태그:

- 예외 message 전체
- client IP 전체
- user id, order id
- SSE event name 전체
- 파일명/다운로드 객체 key 전체

`AsyncRequestNotUsableException`는 태그 값으로 직접 쓰기보다 `disconnect_family=spring_async_not_usable`와 `attribution=wrapped_disconnect|post_completion_write|unknown`처럼 정규화하는 편이 대시보드 안정성이 높다.

### 3. last flush age를 별도 메트릭으로 둔다

first-byte latency만 보면 "stream이 늦게 시작됐다"까지만 안다.

하지만 운영에서 자주 필요한 질문은 그 다음이다.

- 첫 바이트는 빨랐는데 왜 completion이 timeout인가?
- 이벤트는 잘 나가다가 왜 idle timeout처럼 끝났는가?
- 마지막 flush 직후 끊긴 것인가, 오랫동안 정적이었다가 끊긴 것인가?

`last_flush_age = completion_time - last_successful_flush_time`를 남기면 다음이 갈린다.

- `last_flush_age`가 매우 짧음 + disconnect 증가: user cancel / proxy reset / 네트워크 단절 가능성
- `last_flush_age`가 timeout 값과 비슷함 + SSE: heartbeat 부재 가능성
- `last_flush_age`가 큼 + worker는 계속 일함: producer cancellation 누락 가능성

## 로그 설계

### 1. completion 로그 한 줄을 표준화한다

streaming request마다 마지막에 아래 필드를 가진 구조화 로그 한 줄이 있으면 좋다.

```text
event=stream_completion
trace_id=...
route=/exports/{id}
stream_type=streaming_response_body
first_byte_ms=84
flush_count=17
last_flush_age_ms=1203
bytes_sent=184320
completion_cause=disconnect
disconnect_family=spring_async_not_usable
attribution=wrapped_disconnect
commit_state=after_first_byte
phase=mid_stream_flush
root_exception=ClientAbortException
```

여기서 핵심은 stacktrace보다 **의미 필드**다.

- `first_byte_ms`: app이 늦었는지
- `flush_count`: flush granularity가 과한지
- `last_flush_age_ms`: idle timeout인지
- `completion_cause`: 정상 종료/timeout/disconnect/app error 중 무엇인지
- `disconnect_family`: raw transport shape가 무엇인지
- `attribution`: `AsyncRequestNotUsableException`를 어떤 bucket에 넣었는지

### 2. 중간 로그는 marker 성격으로만 둔다

모든 flush마다 info 로그를 찍으면 noisy하다.

권장 패턴:

- `debug` 또는 샘플링된 `trace`로 `first_successful_flush`
- `warn`은 completion cause가 `app_error` 또는 예상 밖 `post_completion_write`일 때만
- `disconnect`는 단건 full stacktrace보다 counter + sampled log를 우선

즉 운영 기본선은 "중간 이벤트는 메트릭", "종료 시점은 구조화 로그 1줄"이다.

## `AsyncRequestNotUsableException` 귀속 플레이북

이 예외는 대개 root cause가 아니라 **이미 unusable해진 response를 다시 건드렸다는 신호**다.

### 1. 먼저 세 갈래로 나눈다

| 패턴 | 해석 | 운영 조치 |
|---|---|---|
| cause 체인에 `ClientAbortException`, `EofException`, `ClosedChannelException`, `broken pipe`, `connection reset by peer`가 있음 | transport disconnect를 Spring이 wrapping했을 가능성이 높다 | disconnect bucket으로 집계, page 금지 |
| 직전에 `onCompletion`/`onError`/`onTimeout`가 이미 왔고 그 뒤 추가 `send`/`write`에서 발생 | post-completion write race다 | producer cancellation / scheduler 정리 누락 조사 |
| first byte 전이고 timeout 신호가 먼저 있었음 | async timeout 후 unusable 상태일 수 있다 | timeout budget, worker cancel, fallback 응답 경계 확인 |

즉 `AsyncRequestNotUsableException == Spring bug`로 읽지 않는다.

### 2. attribution 필드를 따로 둔다

`disconnect_family=spring_async_not_usable`만 있으면 너무 거칠다.

최소한 아래 3개로 나눠 두는 편이 좋다.

- `attribution=wrapped_disconnect`
- `attribution=post_completion_write`
- `attribution=timeout_after_unusable`

판별 기준은 다음처럼 잡을 수 있다.

```text
1. raw cause에 container disconnect shape가 있는가?
   -> yes: wrapped_disconnect
2. completion callback이 먼저 기록되었는가?
   -> yes: post_completion_write
3. timeout callback/AsyncRequestTimeoutException이 먼저 있었는가?
   -> yes: timeout_after_unusable
4. 아니면
   -> unknown
```

### 3. first-byte 여부와 함께 본다

같은 `AsyncRequestNotUsableException`이어도 해석은 달라진다.

- `before_first_byte`: 아직 일반 timeout/error contract 문제일 여지가 있다
- `after_first_byte`: transport 종료 또는 post-completion write race에 더 가깝다

따라서 completion 로그에는 최소한 `commit_state=before_first_byte|after_first_byte`가 필요하다.

## 타입별 instrumentation 포인트

### 1. `StreamingResponseBody`

이 타입은 애플리케이션이 flush cadence를 직접 가진다.

따라서 계측 포인트도 write loop 안에 둬야 한다.

- 첫 `flush()` 성공 시 `first_byte_ms` 기록
- flush 성공마다 `flush_count`, `last_successful_flush_time` 갱신
- `IOException` 또는 `AsyncRequestNotUsableException`를 catch해서 `completion_cause` 후보 기록
- `finally`에서 completion 로그/메트릭 마감

이 타입에서 흔한 오해는 "write했다"와 "나갔다"를 같은 말로 보는 것이다.

`write()` 호출만 세고 flush 성공을 안 잡으면 last flush 해석이 틀린다.

### 2. `ResponseBodyEmitter`

`send(...)`가 사실상 write + flush 단위다.

관측 포인트:

- 첫 `send(...)` 성공을 first byte로 취급
- `send(...)` 성공마다 `flush_count`와 `last_successful_flush_time` 갱신
- `onCompletion`, `onTimeout`, `onError`를 모두 등록
- `complete()` 또는 `completeWithError(...)` 호출 자체보다 callback이 실제로 언제 왔는지 기록

특히 `send()` 이후 예외가 난 뒤 또 `completeWithError(...)`를 호출하면 `AsyncRequestNotUsableException` 연쇄가 생길 수 있으므로, logging은 "누가 먼저 completion을 선언했는가"를 남겨야 한다.

### 3. `SseEmitter`

SSE는 business event가 없으면 관측도 멈춘다.

따라서 heartbeat가 곧 observability다.

- heartbeat event/comment 성공 시 last flush 갱신
- `last_flush_age`가 proxy idle timeout에 가까워지면 위험 신호로 본다
- reconnect storm가 보이면 `completion_cause=disconnect`만 보지 말고 `first_byte_ms`, heartbeat gap, reconnect interval을 같이 본다

SSE에서 "마지막 business event는 오래전인데 completion은 지금" 같은 패턴은 대부분 heartbeat 설계와 연결된다.

## Micrometer 예시

```java
public final class StreamingObservation {
    private final long requestStartNanos = System.nanoTime();
    private final AtomicBoolean firstByteRecorded = new AtomicBoolean(false);
    private final AtomicLong lastFlushNanos = new AtomicLong(-1L);
    private final AtomicInteger flushCount = new AtomicInteger();

    public void markFlushSuccess(Timer firstByteTimer, Counter flushCounter) {
        long now = System.nanoTime();
        if (firstByteRecorded.compareAndSet(false, true)) {
            firstByteTimer.record(now - requestStartNanos, TimeUnit.NANOSECONDS);
        }
        lastFlushNanos.set(now);
        flushCount.incrementAndGet();
        flushCounter.increment();
    }

    public long lastFlushAgeMillisAt(long completionNanos) {
        long last = lastFlushNanos.get();
        return last < 0 ? -1L : TimeUnit.NANOSECONDS.toMillis(completionNanos - last);
    }
}
```

핵심은 "write 시도"가 아니라 `markFlushSuccess(...)`를 **성공한 flush 직후**에만 호출하는 것이다.

## 대시보드와 알림

### 1. 대시보드 기본 패널

streaming endpoint는 아래 네 패널만 있어도 초기 triage가 빨라진다.

1. `first_byte` p50/p95/p99 by route
2. `completion_cause` ratio by route
3. `last_flush_age` distribution by route and stream type
4. `disconnect_family` stacked count with `attribution`

### 2. 알림은 ratio + latency 조합으로 건다

권장 패턴:

```text
disconnect_ratio(route, 5m) 상승
AND first_byte_p95(route) 상승 또는 last_flush_age_p95(route) 상승
AND upstream 499/504 또는 reconnect storm 동반
```

반대로 아래는 기본 page 대상이 아니다.

- 단발성 `AsyncRequestNotUsableException`
- 단발성 `ClientAbortException`
- SSE reconnect 과정의 짧은 disconnect

## 실전 시나리오

### 시나리오 1: first-byte latency만 급증하고 completion은 대부분 정상이다

문제는 stream 중간이 아니라 첫 send 이전일 가능성이 높다.

- DB/외부 API 선행 작업
- auth/filter 병목
- 첫 chunk 생성 비용

### 시나리오 2: `last_flush_age`가 proxy idle timeout 근처로 몰리고 SSE disconnect가 늘었다

heartbeat gap 문제일 가능성이 높다.

- business event 부재
- heartbeat scheduler 지연
- proxy idle timeout과 heartbeat interval 불일치

### 시나리오 3: `AsyncRequestNotUsableException`는 늘었는데 raw disconnect cause는 거의 없다

post-completion write race를 의심한다.

- `onCompletion` 뒤 producer 중단 안 됨
- scheduler/subscription cleanup 누락
- timeout 후에도 worker가 계속 `send()` 시도

### 시나리오 4: first byte 전에 timeout과 unusable이 함께 증가한다

이 경우는 transport noise보다 timeout budget 문제에 가깝다.

- async timeout이 너무 짧음
- 첫 chunk 생성이 너무 느림
- fallback/error path가 commit 전에 닫히지 못함

## 꼬리질문

> Q: 왜 `http.server.requests`만으로 streaming 장애를 해석하면 부족한가?
> 의도: 단일 latency와 stream lifecycle 분리 확인
> 핵심: first byte, 중간 flush, completion cause, disconnect attribution이 서로 다른 질문이기 때문이다.

> Q: 왜 `last_flush_age`를 별도 메트릭으로 두는가?
> 의도: idle timeout과 즉시 disconnect 구분 확인
> 핵심: 마지막 성공 flush 이후의 공백 길이가 timeout/heartbeat/cancel 패턴을 드러내기 때문이다.

> Q: `AsyncRequestNotUsableException`를 왜 root cause로 바로 취급하면 안 되는가?
> 의도: Spring wrapper 의미 확인
> 핵심: 대개 이미 unusable해진 response에 대한 후행 신호이므로 raw disconnect cause나 post-completion write race를 함께 봐야 한다.

> Q: `StreamingResponseBody`에서 write 수가 아니라 flush 성공 수를 세야 하는 이유는 무엇인가?
> 의도: write와 실제 전송 경계 구분 확인
> 핵심: 관측상 중요한 경계는 successful flush와 first-byte commit이기 때문이다.

## 한 줄 정리

async MVC streaming 관측의 핵심은 first-byte, 마지막 성공 flush, completion cause, `AsyncRequestNotUsableException` attribution을 분리해 "느린 응답", "idle timeout", "client abort", "post-completion write bug"를 각각 다른 bucket으로 읽는 것이다.
