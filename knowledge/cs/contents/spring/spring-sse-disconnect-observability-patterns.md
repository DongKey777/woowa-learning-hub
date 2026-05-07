---
schema_version: 3
title: Spring SSE Disconnect Observability Patterns
concept_id: spring/sse-disconnect-observability-patterns
canonical: true
category: spring
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 87
review_feedback_tags:
- sse-disconnect-observability
- eventsource-reconnect-pressure
- last-successful-flush
- interval
aliases:
- SSE disconnect observability
- EventSource reconnect pressure
- last successful flush interval
- SseEmitter broken pipe
- proxy idle close
- streaming disconnect alerting
intents:
- troubleshooting
- deep_dive
linked_paths:
- contents/spring/spring-async-mvc-streaming-observability-playbook.md
- contents/spring/spring-sse-proxy-idle-timeout-matrix.md
- contents/spring/spring-mvc-sseemitter-vs-webflux-sse-timeout-behavior.md
- contents/spring/spring-sse-buffering-compression-checklist.md
- contents/spring/spring-sse-replay-buffer-last-event-id-recovery-patterns.md
- contents/network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md
symptoms:
- SSE disconnect count만 alert로 걸었더니 정상 reconnect까지 noisy하게 잡힌다.
- proxy idle close와 애플리케이션 성능 문제를 구분하기 어렵다.
- broken pipe 예외 shape가 container마다 달라 같은 원인을 놓친다.
expected_queries:
- Spring SSE disconnect alerting은 disconnect count만 보면 왜 noisy해?
- heartbeat cadence, last flush interval, reconnect pressure를 같이 봐야 하는 이유는?
- proxy idle close와 실제 서버 지연을 SSE 관측 지표로 어떻게 나눠?
- SseEmitter broken pipe 예외는 어떤 타임라인에서 해석해야 해?
contextual_chunk_prefix: |
  이 문서는 SSE endpoint 관측을 disconnect count 하나로 보지 않고 heartbeat cadence,
  last successful flush interval, reconnect pressure, container exception shape를 같은
  타임라인에서 읽어 proxy idle close와 실제 latency 문제를 분리하는 playbook이다.
---
# Spring SSE Disconnect Observability Patterns

> 한 줄 요약: SSE endpoint alerting은 disconnect count 하나로 걸면 거의 반드시 noisy해지므로, heartbeat cadence, 마지막 성공 flush 간격, reconnect pressure, container 예외 shape를 같은 타임라인에서 읽어야 proxy idle close와 실제 성능 문제를 분리할 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Spring Async MVC Streaming Observability Playbook](./spring-async-mvc-streaming-observability-playbook.md)
> - [Spring SSE Proxy Idle-Timeout Matrix](./spring-sse-proxy-idle-timeout-matrix.md)
> - [Spring MVC `SseEmitter` vs WebFlux SSE Timeout Behavior](./spring-mvc-sseemitter-vs-webflux-sse-timeout-behavior.md)
> - [Spring SSE Buffering / Compression Checklist](./spring-sse-buffering-compression-checklist.md)
> - [Spring SSE Replay Buffer and `Last-Event-ID` Recovery Patterns](./spring-sse-replay-buffer-last-event-id-recovery-patterns.md)
> - [Spring Servlet Container Disconnect Exception Mapping](./spring-servlet-container-disconnect-exception-mapping.md)
> - [Spring HTTP/2 Reset Attribution in Spring MVC](./spring-http2-reset-attribution-spring-mvc.md)
> - [Spring Partial-Response Access Log Interpretation](./spring-partial-response-access-log-interpretation.md)
> - [Spring `StreamingResponseBody` / `ResponseBodyEmitter` / `SseEmitter` Commit Lifecycle](./spring-streamingresponsebody-responsebodyemitter-sse-commit-lifecycle.md)
> - [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](./spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](../network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)

retrieval-anchor-keywords: spring SSE disconnect observability, SSE alerting, SseEmitter alerting, heartbeat cadence, heartbeat gap, reconnect noise, reconnect pressure, reconnect storm, disconnect ratio, last flush age, last successful flush, proxy idle suspected, EventSource retry jitter, Last-Event-ID replay, SSE replay buffer, replay window miss, stale cursor, replay gap events, high water mark fence, multi-instance SSE recovery, proxy buffering drift, SSE gzip drift, EventSource burst delivery, client-visible flush gap, ClientAbortException, EofException, ClosedChannelException, AsyncRequestNotUsableException, Tomcat SSE disconnect, Jetty SSE reset, Undertow SSE closed channel, ALB idle timeout, nginx proxy_read_timeout, CDN streaming timeout, HTTP/2 stream reset, RST_STREAM, GOAWAY, WebFlux SSE disconnect, doOnCancel, reactive SSE cancellation, SignalType.CANCEL

## 핵심 개념

SSE disconnect 관측에서 가장 먼저 버려야 하는 가정은 "`disconnect`는 한 종류"라는 생각이다.

실제로는 최소한 다음 세 질문이 섞여 있다.

- heartbeat cadence가 proxy/edge idle timeout보다 충분히 짧은가
- reconnect가 정상 복구 noise인가, lock-step storm인가
- container가 본 예외가 user cancel인지, proxy idle close인지, HTTP/2 stream reset인지

따라서 `disconnect_total` 하나로 alert를 걸면 다음이 한 bucket에 섞인다.

- 사용자가 탭을 닫아 생긴 정상 `ClientAbortException` / `EofException`
- ALB, Nginx, CDN idle timeout 뒤 다음 heartbeat에서 surface된 write failure
- HTTP/2 `RST_STREAM` / `GOAWAY`가 만든 single-stream cancel
- producer가 `onCompletion` 이후에도 계속 `send()`해서 생긴 후행 noise

운영 기준은 "disconnect 예외가 몇 건이냐"가 아니라, **heartbeat budget, reconnect pressure, commit 이후 phase, container family**를 같이 보는 것이다.

## 먼저 숫자 세 개를 분리한다

SSE triage를 빠르게 하려면 아래 세 숫자를 먼저 계산하는 편이 좋다.

| 지표 | 의미 | 왜 필요한가 |
|---|---|---|
| `Tmin` | chain에서 가장 짧은 유효 idle timeout | heartbeat가 실제로 지켜야 하는 상한을 정한다 |
| `heartbeat_gap` | 마지막 성공 flush 이후 다음 성공 flush까지의 간격 | proxy idle close 위험을 직접 드러낸다 |
| `reconnect_pressure` | 일정 구간 reconnect 수 / 평균 active connection 수 | reconnect spike가 실제 incident인지 noise인지 가른다 |

여기서 `Tmin`은 "설정 파일에서 제일 작은 숫자"가 아니라, **실제로 client-visible byte를 못 본 hop의 timeout**이다.

- Nginx가 upstream heartbeat를 읽어도 buffering 때문에 브라우저가 못 보면 client-visible `Tmin`은 더 짧아질 수 있다
- CDN이 `text/event-stream`을 coalesce하면 origin 관점 heartbeat와 browser 관점 heartbeat가 달라진다
- HTTP/2에서는 socket close가 아니라 `RST_STREAM`이 먼저 와서 idle close와 다른 패턴으로 보일 수 있다

즉 origin `heartbeat_gap`만 건강하고 browser 수신 cadence가 무너지면, timeout tuning보다 먼저 [Spring SSE Buffering / Compression Checklist](./spring-sse-buffering-compression-checklist.md) 쪽의 buffering/compression/transform 경로를 확인해야 한다.

## Heartbeat Cadence를 alert budget으로 바꾼다

heartbeat interval `H`는 keepalive 설정이면서 동시에 alert budget의 기준점이다.

실무 시작점은 보통 다음 정도가 안전하다.

- 내부 hop만 있고 buffering이 없으면 `H <= Tmin / 2`
- ALB, Nginx, CDN, mobile network, GC pause를 함께 고려하면 `H <= Tmin / 3`
- `H`를 `Tmin` 직전으로 붙이면 scheduler drift, flush 지연, packet loss 때문에 lock-step disconnect가 쉬워진다

운영 대시보드에선 `heartbeat_gap_p95 / Tmin`을 따로 보는 편이 좋다.

| 신호 | 시작 heuristics | 해석 |
|---|---|---|
| `heartbeat_gap_p95 / Tmin <= 0.5` | 정상 범위 | heartbeat slack이 충분하다 |
| `heartbeat_gap_p95 / Tmin > 0.7` | warning 후보 | 일부 hop에서 idle budget이 빠듯해졌다 |
| `heartbeat_gap_p99 / Tmin > 0.9` 그리고 disconnect/reconnect 동반 | critical 후보 | proxy idle close가 실제 user-visible incident로 번지는 중일 수 있다 |

이 값들은 절대 규칙이 아니라 **baseline이 없는 팀이 처음 잡는 시작선**이다.
중요한 건 threshold 하나보다 다음 조합이다.

```text
heartbeat_gap_budget 상승
AND after-first-byte disconnect ratio 상승
AND reconnect pressure 동반
```

이 세 개가 같이 움직이지 않으면 page보다 sampled log나 warning으로 끝나는 경우가 많다.

## 꼭 남겨야 하는 SSE 전용 신호

async streaming 공통 메트릭 위에 SSE는 아래 필드가 더 있어야 triage가 쉬워진다.

| 신호 | 권장 태그/필드 | 목적 |
|---|---|---|
| `sse.active_connections` | `route`, `container_family`, `http_protocol`, `edge_hop` | reconnect pressure의 분모 |
| `sse.heartbeat_gap` | `route`, `edge_hop` | proxy idle risk 조기 탐지 |
| `sse.disconnect_total` | `route`, `container_family`, `disconnect_family`, `phase`, `commit_state` | servlet/container shape 정규화 |
| `sse.reconnect_total` | `route`, `client_family`, `edge_hop` | reconnect burst 감지 |
| `sse.replay_gap_events` 또는 `Last-Event-ID` gap | `route` | reconnect가 단순 복구인지 실제 손실 회복인지 구분 |
| completion log 1줄 | `last_flush_age_ms`, `heartbeat_gap_ms`, `retry_hint_ms`, `root_exception` | alert 해석에 필요한 의미 필드 확보 |

특히 `reconnect_total`만 보면 noise가 커진다.
가능하면 "재접속은 했지만 replay gap은 0"과 "재접속 + 누락 이벤트 replay 발생"을 분리하는 편이 좋다.
이때 replay window sizing, stale cursor 분기, ordering fence가 불안정하면 `replay_gap_events` 해석도 흔들리므로 [Spring SSE Replay Buffer and `Last-Event-ID` Recovery Patterns](./spring-sse-replay-buffer-last-event-id-recovery-patterns.md)와 같이 보는 편이 좋다.

## Proxy x Container 증거 매트릭스

같은 SSE disconnect라도 proxy 힌트와 container 예외 shape를 합쳐야 alert 품질이 올라간다.

| 패턴 | proxy / edge 힌트 | Tomcat | Jetty | Undertow | 기본 알림 정책 |
|---|---|---|---|---|---|
| 조용한 구간 뒤 idle close | `proxy_read_timeout`, ALB idle timeout, CDN idle cap 근처에서 끊김 | `ClientAbortException` 또는 wrapper | `EofException("Closed")` 또는 quiet EOF | `ClosedChannelException` 또는 일반 `IOException` | count는 집계하되, `heartbeat_gap_budget` 상승이 같이 있을 때만 warn/page |
| 브라우저 refresh / 탭 종료 / 짧은 reconnect | proxy timeout 힌트 없음, `last_flush_age` 짧음 | `ClientAbortException` | `EofException` | `ClosedChannelException` | sampled debug만. page 금지 |
| HTTP/2 stream reset | `RST_STREAM`, `GOAWAY`, edge drain, h2 only | `CloseNowException` / `StreamException` / `ClientAbortException` 혼재 | `EofException("reset")`, `EofException("Output shutdown")` | `ClosedChannelException` + h2 trace | socket disconnect와 분리해서 집계. before-first-byte 증가 시에만 더 강하게 본다 |
| completion 이후 후행 write | proxy 힌트 없음, 직전에 completion callback 존재 | `AsyncRequestNotUsableException` | `AsyncRequestNotUsableException` | `AsyncRequestNotUsableException` | 성능 page보다 cleanup bug 경고로 본다 |

핵심은 "Tomcat은 `ClientAbortException`", "Jetty는 `EofException`", "Undertow는 `ClosedChannelException`" 같은 class 매칭을 넘어서:

- `phase=before_first_byte|mid_stream|after_completion`
- `http_protocol=http1|http2`
- `edge_hop=alb|nginx|cdn|direct`

를 같이 남기는 것이다.

## Reconnect Noise와 Incident를 가르는 기준

reconnect 자체는 SSE의 정상 동작 일부다.
문제는 reconnect가 **동기화된 집단 행동**으로 바뀌는 순간이다.

| 관측 패턴 | 해석 | 권장 정책 |
|---|---|---|
| reconnect 증가, disconnect 증가도 있으나 `heartbeat_gap_budget` 안정적이고 replay gap 거의 없음 | deploy, tab churn, mobile handoff, 정상 재접속 noise 가능성 | page 금지, 1시간 baseline 비교만 |
| reconnect가 같은 주기로 몰리고 `last_flush_age`가 `Tmin` 근처에 군집 | heartbeat가 proxy idle timeout을 못 이김 | warning 이상. hop별 idle/buffering 우선 조사 |
| reconnect pressure가 갑자기 커졌지만 active connection은 줄고 first-byte latency도 함께 상승 | app이 첫 event를 늦게 보내거나 auth/filter 병목 | page 후보. transport noise보다 app 성능 문제 가능성 |
| reconnect는 많은데 before-first-byte disconnect는 적고 after-first-byte만 증가 | client/proxy close가 많다 | proxy/config 문제 우선, application exception page는 억제 |

여기서 유용한 시작식은 다음과 같다.

```text
reconnect_pressure = reconnects_per_minute / max(avg_active_connections, 1)
disconnect_ratio = after_first_byte_disconnects / stream_completions
```

운영 시작점으로는 다음 정도가 무난하다.

- `reconnect_pressure > 0.2`가 2개 이상 윈도우 연속 지속되면 storm 후보
- `disconnect_ratio > max(3 x baseline, 0.05)`면 noise를 넘는 변화 후보
- 둘이 함께 오르고 `heartbeat_gap_budget`도 상승하면 page 검토

절대값보다 **baseline 대비 배수와 동시성**이 중요하다.

## Alert Threshold Patterns

SSE alert는 단일 counter보다 조합 경보가 더 낫다.

### 1. Page를 피해야 하는 noise bucket

다음은 기본적으로 sampled log 또는 dashboard 경고에 가깝다.

- 단발성 `ClientAbortException`, `EofException`, `ClosedChannelException`
- `protocol=h2`에서 single-stream `RST_STREAM` 계열 reset
- reconnect는 늘었지만 `Last-Event-ID` replay gap이 거의 0인 경우
- deploy 직후 짧은 reconnect burst

### 2. Warning bucket

다음 조합이면 hop-level timeout drift 가능성이 높다.

```text
heartbeat_gap_p95 / Tmin > 0.7
AND disconnect_ratio(route, 5m) > baseline
AND completion_cause=disconnect가 after_first_byte에서 증가
```

이 경우 우선순위는:

1. heartbeat cadence 확인
2. Nginx/CDN buffering 여부 확인
3. ALB/CDN idle timeout과 `retry:` lock-step 여부 확인

### 3. Critical / page bucket

다음은 실제 user-visible degradation 가능성이 높다.

```text
heartbeat_gap_p99 / Tmin > 0.9
AND reconnect_pressure > 0.2
AND disconnect_ratio > max(3 x baseline, 0.05)
AND upstream 499/504 또는 first_byte_p95 상승 동반
```

핵심은 page 조건에 **latency 또는 upstream signal**을 반드시 섞는 것이다.
그렇지 않으면 정상 reconnect noise가 pager를 흔든다.

## 실전 시나리오

### 시나리오 1: Nginx 앞 Tomcat SSE에서 정확히 60초 근처 disconnect가 반복된다

관측:

- `heartbeat_gap_p95`가 50초 후반
- Nginx `proxy_read_timeout=60s`
- Tomcat 쪽은 `ClientAbortException`
- reconnect가 같은 주기로 몰림

해석은 "Tomcat 예외가 많다"가 아니라 heartbeat budget 부족 + lock-step reconnect다.

### 시나리오 2: ALB 뒤 Jetty h2 SSE에서 `EofException("reset")`가 늘었지만 user report는 거의 없다

관측:

- `protocol=h2`
- deploy 직후 `GOAWAY`/drain 흔적 존재
- `last_flush_age`는 짧고 `heartbeat_gap_budget` 안정적

이 경우는 broken pipe alert보다 connection drain / stream reset noise 억제가 더 중요하다.

### 시나리오 3: CDN 앞 Undertow SSE에서 `ClosedChannelException`과 reconnect burst가 같이 보인다

관측:

- origin heartbeat는 20초인데 browser 체감 reconnect는 60초 근처
- CDN이 `text/event-stream`을 coalesce하거나 buffering
- Undertow는 generic `ClosedChannelException`

이 패턴은 container class 이름보다 "누가 마지막 바이트를 실제로 봤는가"를 먼저 확인해야 한다.

## 꼬리질문

> Q: 왜 SSE alert를 `disconnect_total` 하나로 걸면 noisy한가?
> 의도: reconnect noise와 incident 구분 확인
> 핵심: user cancel, proxy idle close, HTTP/2 reset, post-completion write가 모두 같은 counter에 섞이기 때문이다.

> Q: 왜 `heartbeat_gap_p95 / Tmin` 같은 budget 비율이 필요한가?
> 의도: heartbeat cadence와 idle timeout의 관계 확인
> 핵심: 절대 milliseconds보다 "가장 짧은 유효 idle timeout에 얼마나 근접했는가"가 proxy idle risk를 더 잘 드러내기 때문이다.

> Q: Jetty `EofException`과 Undertow `ClosedChannelException`은 왜 무조건 page 대상이 아닌가?
> 의도: container-specific noise 해석 확인
> 핵심: SSE reconnect, browser cancel, HTTP/2 stream reset에서도 흔히 보이는 shape이어서 phase와 reconnect pressure를 같이 봐야 하기 때문이다.

## 한 줄 정리

SSE disconnect alerting의 핵심은 예외 count를 줄이는 것이 아니라, **heartbeat budget, reconnect pressure, proxy hop, container exception family**를 한 묶음으로 읽어 정상 재연결 noise와 실제 성능 저하를 분리하는 것이다.
