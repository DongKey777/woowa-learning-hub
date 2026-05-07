---
schema_version: 3
title: "SSE/WebFlux Streaming Cancel After First Byte"
concept_id: network/sse-webflux-streaming-cancel-after-first-byte
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 88
mission_ids: []
review_feedback_tags:
- sse
- webflux-cancel
- streaming-disconnect
aliases:
- SSE disconnect after first byte
- WebFlux first byte commit
- partial flush failure
- cancellation lag
- text/event-stream broken pipe
- Last-Event-ID gap
- Reactor Netty cancel lag
symptoms:
- SSE first byte가 commit되면 스트림 전체가 성공했다고 판단한다
- downstream disconnect, partial flush failure, producer stop 시각을 하나로 본다
- partial event write 시도 id와 client가 정상 처리한 Last-Event-ID를 구분하지 않는다
- WebFlux cancel이 boundedElastic이나 prefetch 작업까지 즉시 멈춘다고 생각한다
intents:
- troubleshooting
- deep_dive
- comparison
prerequisites:
- network/sse-websocket-polling
- network/network-spring-request-lifecycle-timeout-disconnect-bridge
next_docs:
- network/sse-last-event-id-replay-window
- network/webflux-cancel-lag-tuning
- network/sse-failure-attribution-http1-http2
- spring/reactive-blocking-bridge-boundedelastic-block-traps
linked_paths:
- contents/network/sse-websocket-polling.md
- contents/network/sse-last-event-id-replay-window.md
- contents/network/webflux-cancel-lag-tuning.md
- contents/network/client-disconnect-499-broken-pipe-cancellation-proxy-chain.md
- contents/network/sse-failure-attribution-http1-http2.md
- contents/network/network-spring-request-lifecycle-timeout-disconnect-bridge.md
- contents/network/servlet-container-abort-surface-map-tomcat-jetty-undertow.md
- contents/network/http-response-compression-buffering-streaming-tradeoffs.md
- contents/network/tls-record-sizing-flush-streaming-latency.md
- contents/network/http2-rst-stream-goaway-streaming-failure-semantics.md
- contents/spring/spring-reactive-blocking-bridge-boundedelastic-block-traps.md
- contents/spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md
confusable_with:
- network/sse-last-event-id-replay-window
- network/webflux-cancel-lag-tuning
- network/client-disconnect-499-broken-pipe-cancellation-proxy-chain
- network/http2-rst-stream-goaway-streaming-failure-semantics
forbidden_neighbors: []
expected_queries:
- "SSE first byte commit 후 client가 끊기면 어떤 시계를 따로 봐야 해?"
- "WebFlux streaming cancel lag 때문에 producer가 계속 도는 이유는?"
- "partial flush failure와 Last-Event-ID gap을 어떻게 해석해?"
- "text/event-stream에서 첫 이벤트 일부만 쓰고 broken pipe가 나면 client는 어디까지 받았어?"
- "SSE disconnect 후 duplicate suppression과 replay window를 어떻게 설계해?"
contextual_chunk_prefix: |
  이 문서는 SSE/WebFlux streaming에서 first byte commit 이후 downstream
  disconnect, partial flush failure, reactive cancellation lag, producer stop,
  Last-Event-ID replay window를 다루는 advanced playbook이다.
---
# SSE/WebFlux Streaming Cancel After First Byte

> 한 줄 요약: SSE/WebFlux 스트리밍은 first byte commit이 성공해도 끝난 요청이 아니다. 그 뒤에는 downstream disconnect 감지 시각, partial flush failure 발생 지점, reactive cancellation 전파, 실제 producer 중단 시점이 서로 어긋날 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [SSE, WebSocket, Polling](./sse-websocket-polling.md)
> - [SSE Last-Event-ID Replay Window](./sse-last-event-id-replay-window.md)
> - [WebFlux Cancel-Lag Tuning](./webflux-cancel-lag-tuning.md)
> - [Client Disconnect, 499, Broken Pipe, Cancellation in Proxy Chains](./client-disconnect-499-broken-pipe-cancellation-proxy-chain.md)
> - [SSE Failure Attribution Across HTTP/1.1 and HTTP/2](./sse-failure-attribution-http1-http2.md)
> - [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
> - [Servlet Container Abort Surface Map: Tomcat, Jetty, Undertow](./servlet-container-abort-surface-map-tomcat-jetty-undertow.md)
> - [HTTP Response Compression, Buffering, Streaming Trade-offs](./http-response-compression-buffering-streaming-tradeoffs.md)
> - [TLS Record Sizing, Flush, Streaming Latency](./tls-record-sizing-flush-streaming-latency.md)
> - [HTTP/2 RST_STREAM, GOAWAY, Streaming Failure Semantics](./http2-rst-stream-goaway-streaming-failure-semantics.md)
> - [Spring Reactive Blocking Bridge and `boundedElastic` Traps](../spring/spring-reactive-blocking-bridge-boundedelastic-block-traps.md)
> - [Spring Request Lifecycle Timeout / Disconnect / Cancellation Bridges](../spring/spring-request-lifecycle-timeout-disconnect-cancellation-bridges.md)

retrieval-anchor-keywords: streaming cancel after first byte, SSE disconnect after first event, WebFlux first byte commit, partial flush failure, cancellation lag, text/event-stream broken pipe, response committed streaming, reactor netty cancel lag, webflux prefetch cancel lag, boundedElastic cancel lag, last-event-id gap, SSE replay window, duplicate suppression, SSE downstream disconnect, 499, RST_STREAM, EOF, HTTP/1.1 chunked flush failure

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

SSE/WebFlux 스트리밍에서 "first byte가 나갔다"는 말은 보통 아래 넷 중 첫 번째만 의미한다.

- origin response가 commit됐다
- downstream hop가 disconnect를 관찰했다
- 다음 chunk flush가 partial failure로 터졌다
- cancel이 producer까지 전파돼 실제 작업이 멈췄다

이 네 시계는 자주 어긋난다.  
그래서 `200` 또는 첫 이벤트 전송 성공만 보고 "스트림 성공"이라고 말하면 안 된다.

특히 SSE는 **완전한 이벤트 frame**이 도착해야 브라우저가 처리하기 때문에, 바이트 일부가 나갔어도 마지막 정상 이벤트 `id`는 더 앞일 수 있다.

### Retrieval Anchors

- `streaming cancel after first byte`
- `SSE disconnect after first event`
- `WebFlux first byte commit`
- `partial flush failure`
- `cancellation lag`
- `text/event-stream broken pipe`
- `reactor netty cancel lag`
- `webflux prefetch cancel lag`
- `boundedElastic cancel lag`
- `last-event-id gap`

## 깊이 들어가기

### 1. first byte commit은 전달 보장이 아니라 상태 경계다

first byte commit이 되면 대개 다음이 고정된다.

- HTTP status와 header
- `text/event-stream` 응답 시작 여부
- Spring의 committed response 상태

하지만 아직 확정되지 않은 것도 많다.

- 브라우저가 첫 이벤트를 실제로 파싱했는가
- 중간 proxy가 disconnect를 언제 감지하는가
- origin의 다음 write가 성공하는가
- producer가 cancel 이후 얼마나 더 도는가

즉 first byte commit은 "성공 전달"이 아니라 **이제 status를 바꾸기 어려운 구간으로 들어갔다**는 뜻에 가깝다.

### 2. SSE/WebFlux 경로에서는 네 개의 시계를 따로 찍어야 한다

| 시계 | 대표 신호 | 의미 | 섞어 말하면 생기는 오해 |
|------|-----------|------|--------------------------|
| commit 시각 | response committed, first write success | header/status가 확정됐다 | "commit됐다 = 클라이언트가 받았다" |
| disconnect 시각 | edge `499`, H2 `RST_STREAM`, FIN/RST | downstream이 더 이상 안 받는다 | "연결이 끊겼으니 app도 즉시 멈췄다" |
| partial flush failure 시각 | `broken pipe`, `EPIPE`, `IOException` on flush | commit 뒤 특정 chunk가 완전히 전달되지 못했다 | "첫 이벤트도 못 나갔다" |
| producer stop 시각 | `doOnCancel`, dispose, worker stop | 실질적인 작업이 멈췄다 | "cancel log가 떴으니 낭비 작업은 없다" |

실무 장애는 대개 `disconnect 시각 < flush failure 시각 < producer stop 시각` 순서로 벌어진다.

### 3. partial flush failure는 "이벤트 일부가 날아갔다"는 뜻일 수 있다

SSE는 줄 단위 텍스트를 `\n\n`로 끝내야 한 이벤트가 완성된다.

- `id: 41\n`
- `event: progress\n`
- `data: 73\n\n`

여기서 flush 실패가 중간에 나면:

- 일부 바이트는 wire에 올라갔을 수 있다
- 하지만 브라우저는 완전한 frame이 아니라서 무시할 수 있다
- 서버는 "41번 이벤트 write 시도"를 남겼지만 클라이언트의 마지막 정상 `Last-Event-ID`는 `40`일 수 있다

그래서 partial flush failure를 다룰 때는 **마지막 write 시도 id**보다 **마지막 정상적으로 완료된 이벤트 id**가 중요하다.

### 4. WebFlux cancel은 빨리 보이지만 producer stop은 늦을 수 있다

WebFlux/Reactor Netty는 downstream close를 비교적 명시적으로 cancel로 바꿔 준다.

- subscriber cancel
- channel dispose
- operator chain termination

그런데 아래가 끼면 lag가 커진다.

- `publishOn`/`flatMap` prefetch로 이미 당겨온 요소
- `onBackpressureBuffer` 같은 버퍼
- `Mono.fromCallable`과 blocking bridge
- `boundedElastic`에 이미 올라간 작업
- 외부 async callback이 cancel-aware하지 않은 경우

이 경우 edge는 이미 `499`나 reset을 남겼는데, producer는 수백 ms에서 수초 더 돌 수 있다.

### 5. SSE에서는 `Last-Event-ID`가 partial failure 이후의 진실을 복원한다

SSE reconnect는 "끊겼다" 자체보다 **어디까지 정상 반영됐는가**가 중요하다.

- first heartbeat comment만 성공했을 수 있다
- 어떤 progress 이벤트는 write 시도만 되고 브라우저는 못 받았을 수 있다
- reconnect 후 중복 또는 gap이 생길 수 있다

그래서 long-lived SSE는:

- stable event `id`
- replay 가능한 window
- reconnect 시 `Last-Event-ID` 기준 재전송

이 셋이 없으면 partial flush failure 이후 상태 복원이 매우 어렵다.

### 6. proxy/TLS/compression 층이 "보냈다"의 의미를 더 흐린다

origin에서 first byte commit이 됐어도 중간 hop은 아직 다를 수 있다.

- TLS record coalescing이 첫 chunk를 늦출 수 있다
- compression이 flush cadence를 바꿀 수 있다
- proxy buffering이 이벤트를 모아둘 수 있다

따라서 "첫 이벤트까지는 분명 갔다"를 주장하려면 origin commit 로그만으로는 부족하고, edge write/flush 또는 client-side last received event까지 봐야 한다.

### 7. 관측은 마지막 정상 이벤트와 cancel lag를 함께 남겨야 한다

유용한 marker:

- response commit 시각
- first SSE comment/event flush 성공 시각
- 마지막 정상 완료 이벤트 `id`
- 다음 flush 실패 시각과 예외 종류
- edge disconnect 관찰 시각
- cancel signal 수신 시각
- producer 실제 중단 시각

이 중 마지막 두 개의 차이가 **cancellation lag**다.  
streaming 경로에서는 이 값이 zombie work 크기를 가장 잘 보여 준다.

## 실전 시나리오

### 시나리오 1: 첫 heartbeat는 나갔는데 사용자가 탭을 닫았다

흔한 순서:

- SSE stream open
- comment heartbeat 또는 첫 progress event flush 성공
- 브라우저 탭 종료
- edge는 `499` 또는 H2 stream reset 기록
- origin은 다음 flush에서 `broken pipe`
- Reactor cancel은 들어왔지만 producer는 조금 더 작업

이 경우 "첫 바이트는 성공"과 "스트림이 정상 종료"는 완전히 다른 말이다.

### 시나리오 2: 진행률 이벤트 41번을 보냈다고 믿었는데 재접속 후 40번부터 다시 와야 한다

41번 이벤트의 일부 바이트만 나가고 frame 종료 전 flush가 실패했을 수 있다.  
브라우저는 완성되지 않은 SSE event를 처리하지 않기 때문에 `Last-Event-ID` 기준으로는 40번이 마지막 정상 이벤트다.

### 시나리오 3: WebFlux cancel 로그는 바로 찍히는데 CPU와 DB 부하는 계속 오른다

reactive chain 안에 blocking poller, prefetch buffer, 외부 callback이 섞여 cancel 이후에도 작업이 계속된 패턴일 수 있다.  
이때 봐야 하는 것은 exception 개수보다 `disconnect -> producer stop` 지연이다.

### 시나리오 4: gateway 뒤 H2 SSE에서 어떤 요청은 499, 어떤 요청은 stream reset으로 보인다

브라우저, edge, gateway, origin이 서로 다른 층에서 종료를 본 패턴일 수 있다.

- edge access log는 `499`
- gateway는 `RST_STREAM`
- origin은 commit 후 flush `IOException`

셋 다 맞는 말일 수 있으니 하나로 뭉개면 안 된다.

## 코드로 보기

### 타임라인 체크리스트

```text
t1 response committed
t2 SSE event id=40 flush success
t3 client disconnect observed at edge
t4 SSE event id=41 flush attempted
t5 flush failed with EPIPE / broken pipe
t6 reactive cancel observed
t7 producer actually stopped

cancellation lag = t7 - t3
last safe replay point = event id 40
```

### 운영 질문

```text
- first byte commit은 어느 hop에서 확인된 사실인가
- 마지막 정상 완료 SSE event id는 무엇인가
- 실패한 chunk는 write 시도만 됐는가, complete frame까지 갔는가
- disconnect는 edge가 먼저 봤는가 origin이 먼저 봤는가
- cancel signal 이후 producer가 얼마나 더 일했는가
```

### 분류 감각

| 보이는 증상 | 우선 의심할 것 | 첫 확인 포인트 |
|------------|----------------|----------------|
| app은 첫 이벤트 전송 성공, edge는 `499` | commit 뒤 downstream abort | disconnect와 flush failure의 선후 |
| 재접속 후 duplicate/gap | partial SSE frame 손실 | 마지막 정상 `Last-Event-ID` |
| WebFlux cancel 후 CPU 유지 | cancel lag | blocking bridge, prefetch, external callback |
| status는 `200`, 운영은 broken pipe만 봄 | committed streaming late failure | status 변경 불가 구간인지 |

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| SSE event마다 stable `id` 부여 | partial flush 뒤 replay 기준이 선명해진다 | 저장/replay 비용이 든다 | 재접속 허용 stream |
| 작은 prefetch와 제한된 buffer | cancel lag를 줄인다 | throughput이 줄 수 있다 | disconnect 비용이 큰 stream |
| cancel-aware blocking bridge | zombie work를 줄인다 | 구현 복잡도가 오른다 | WebFlux + 외부 blocking 자원 |
| first byte만 성공 로그로 기록 | 구현이 단순하다 | partial failure와 낭비 작업을 숨긴다 | 권장되지 않음 |

핵심은 스트리밍 성공 기준을 "response committed" 하나로 두지 않고 **마지막 정상 이벤트와 producer stop까지 포함해 정의하는 것**이다.

## 꼬리질문

> Q: first byte commit이면 클라이언트가 첫 SSE 이벤트를 본 것 아닌가요?
> 핵심: 아니다. origin commit은 status/header 경계일 뿐이고, 중간 buffering이나 incomplete frame 때문에 브라우저는 아직 못 봤을 수 있다.

> Q: commit 후 `broken pipe`가 났으면 status를 5xx로 바꿔야 하나요?
> 핵심: 대개 어렵다. 이미 committed 상태라 late streaming failure로 따로 관측해야 한다.

> Q: WebFlux는 cancel이 자동 전파되는데 왜 작업이 남나요?
> 핵심: prefetch, buffer, blocking bridge, 외부 callback이 cancel보다 앞서 예약된 일을 계속 수행할 수 있기 때문이다.

> Q: SSE에서 `Last-Event-ID`가 왜 그렇게 중요한가요?
> 핵심: partial flush failure 뒤 어떤 이벤트까지 정상 반영됐는지 복구하는 기준이기 때문이다.

## 한 줄 정리

SSE/WebFlux 스트리밍은 first byte commit 이후에도 disconnect 감지, partial flush failure, cancel 전파, 실제 작업 중단이 따로 움직이므로, 마지막 정상 이벤트와 cancellation lag를 같이 기록해야 제대로 진단된다.
