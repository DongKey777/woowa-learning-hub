---
schema_version: 3
title: HTTP/2 MAX_CONCURRENT_STREAMS, Pending Queue, Saturation
concept_id: network/http2-max-concurrent-streams-pending-queue-saturation
canonical: true
category: network
difficulty: advanced
doc_role: primer
level: advanced
language: mixed
source_priority: 90
mission_ids: []
review_feedback_tags:
- stream-slot-vs-flow-control
- grpc-channel-saturation
- connection-sharding-threshold
aliases:
- settings_max_concurrent_streams
- pending streams
- http/2 stream queue
- stream saturation
- h2 concurrency
- grpc channel saturation
- queued stream
- connection sharding
- unary vs streaming
- head of line in scheduler
symptoms:
- 연결은 살아 있는데 요청이 바로 안 나가요
- gRPC 호출이 느린데 socket보다 stream slot이 부족한 것 같아요
- HTTP/2에서 요청이 시작도 못 한 채 내부 대기열에 쌓여요
intents:
- definition
prerequisites:
- network/latency-bandwidth-throughput-basics
- network/http1-http2-http3-beginner-comparison
next_docs:
- network/queue-saturation-attribution-metrics-runbook
- network/http2-flow-control-window-update-stalls
- network/http2-http3-connection-reuse-coalescing
linked_paths:
- contents/network/http2-hol-blocking-vs-flow-control-stall-quick-decision-table.md
- contents/network/http2-multiplexing-hol-blocking.md
- contents/network/http2-flow-control-window-update-stalls.md
- contents/network/upstream-queueing-connection-pool-wait-tail-latency.md
- contents/network/http2-http3-connection-reuse-coalescing.md
- contents/network/grpc-keepalive-goaway-max-connection-age.md
confusable_with:
- network/queue-saturation-attribution-metrics-runbook
- network/request-timing-decomposition
forbidden_neighbors:
- contents/network/http2-flow-control-window-update-stalls.md
expected_queries:
- H2는 연결이 살아 있는데 왜 요청이 시작도 못 하고 밀려?
- SETTINGS_MAX_CONCURRENT_STREAMS에 걸리면 어디서 대기해?
- gRPC 호출이 느린데 stream slot 부족부터 봐야 하나?
- HTTP/2에서 pending stream queue가 생기는 상황을 설명해줘
- connection sharding이 필요한 H2 포화 징후가 뭐야?
- flow control stall 말고 stream 개수 한도 문제를 구분하고 싶어
- unary 요청이 장수 stream 때문에 같이 밀릴 수 있어?
- MAX_CONCURRENT_STREAMS 포화가 upstream 지연처럼 보일 수 있어?
contextual_chunk_prefix: |
  이 문서는 HTTP/2를 이미 다루는 학습자가 multiplexing이 무한 병렬이
  아니라는 점과 SETTINGS_MAX_CONCURRENT_STREAMS 한도 때문에 요청이
  stream 시작 전 내부 대기열에서 밀리는 상황을 처음 잡는 primer다. 연결은
  살아 있는데 요청이 바로 안 나감, gRPC가 socket보다 stream slot이 먼저
  부족함, unary 요청이 streaming 뒤에서 기다림, pending stream queue,
  connection sharding 필요성 같은 자연어 paraphrase가 본 문서의 핵심
  병목 개념에 매핑된다.
---
# HTTP/2 MAX_CONCURRENT_STREAMS, Pending Queue, Saturation

> 한 줄 요약: HTTP/2 multiplexing은 무한 병렬이 아니다. `SETTINGS_MAX_CONCURRENT_STREAMS` 한계에 걸리면 새 stream은 보이지 않는 대기열에 서고, 운영자는 이를 upstream 지연이나 네트워크 문제로 오해하기 쉽다.

처음 읽는다면 [HTTP/2 HOL Blocking vs Flow-Control Stall Quick Decision Table](./http2-hol-blocking-vs-flow-control-stall-quick-decision-table.md)에서 `slot 부족`과 `credit 부족` 차이부터 잡고 들어오는 편이 빠르다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [HTTP/2 HOL Blocking vs Flow-Control Stall Quick Decision Table](./http2-hol-blocking-vs-flow-control-stall-quick-decision-table.md)
> - [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md)
> - [HTTP/2 Flow Control, WINDOW_UPDATE, Stall](./http2-flow-control-window-update-stalls.md)
> - [Upstream Queueing, Connection Pool Wait, Tail Latency](./upstream-queueing-connection-pool-wait-tail-latency.md)
> - [HTTP/2, HTTP/3 Connection Reuse, Coalescing](./http2-http3-connection-reuse-coalescing.md)
> - [gRPC Keepalive, GOAWAY, Max Connection Age](./grpc-keepalive-goaway-max-connection-age.md)

retrieval-anchor-keywords: SETTINGS_MAX_CONCURRENT_STREAMS, pending streams, HTTP/2 stream queue, stream saturation, H2 concurrency, gRPC channel saturation, queued stream, connection sharding, unary vs streaming, head of line in scheduler

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

HTTP/2는 하나의 connection에서 많은 stream을 동시에 다룰 수 있지만, "많다"는 "무한하다"가 아니다.

- peer는 `SETTINGS_MAX_CONCURRENT_STREAMS`로 동시 stream 수를 제한할 수 있다
- client/proxy 라이브러리는 한도를 넘는 새 요청을 pending queue에 넣을 수 있다
- 이 대기 시간은 connect time이나 upstream service time에 잘 안 잡히기도 한다

즉, stream이 아직 열리지도 못한 채 **H2 내부 스케줄러 앞에서 대기**할 수 있다.

### Retrieval Anchors

- `SETTINGS_MAX_CONCURRENT_STREAMS`
- `pending streams`
- `HTTP/2 stream queue`
- `stream saturation`
- `H2 concurrency`
- `gRPC channel saturation`
- `queued stream`
- `connection sharding`

## 깊이 들어가기

### 1. 이것은 flow control과 다른 병목이다

자주 헷갈리는 구분:

- flow control: 열린 stream에서 얼마나 더 보낼 수 있는가
- max concurrent streams: 몇 개 stream을 동시에 열 수 있는가

둘 다 체감상 "느리다"로 보이지만, 병목 지점이 다르다.

- flow control stall은 stream이 열려 있는데 데이터가 안 흐른다
- concurrency saturation은 stream 자체가 아직 시작되지 못한다

### 2. pending queue는 connection pool 밖에 숨어 있을 수 있다

운영자는 보통 다음만 본다.

- active TCP connections
- connect latency
- request count

하지만 H2에서는 한 connection 안에서 또 다른 queue가 생긴다.

- channel은 살아 있다
- socket도 있다
- 다만 stream slot이 없다

그래서 "연결은 충분한데 왜 응답이 늦지?" 같은 혼란이 생긴다.

### 3. long-lived stream이 slot을 오래 점유하면 unary RPC가 같이 밀린다

같은 H2 connection에 다음이 섞이면 위험하다.

- server streaming
- bidi streaming
- 큰 upload / download stream
- 짧은 unary request

slot 수가 적거나 peer 정책이 보수적이면, 짧은 요청도 시작 전에 줄을 선다.

### 4. 하나의 gRPC channel에 과도하게 몰아넣는 설계가 흔하다

gRPC는 channel 재사용이 좋지만, 단일 channel이 항상 최선은 아니다.

- hot upstream 하나에 unary와 streaming을 같이 몰아넣는다
- channel 하나가 peer의 stream cap에 걸린다
- pending queue가 길어지며 p99가 튄다

이때 문제는 "gRPC가 느리다"가 아니라 **channel concurrency 설계가 안 맞는다**는 것일 수 있다.

### 5. pending queue가 길어지면 timeout budget이 stream open 전부터 탄다

새 stream이 실제로 시작되기 전에도 시간은 흐른다.

- caller deadline은 계속 줄어든다
- queue에서 기다리다 남은 budget이 작아진다
- 시작하자마자 deadline exceeded처럼 보일 수 있다

그래서 H2 pending queue는 upstream service time과 분리해 기록해야 한다.

### 6. 해결은 무조건 cap을 올리는 것이 아니다

가능한 대응은 여러 가지다.

- long-lived streaming과 unary 트래픽 분리
- connection sharding 또는 channel 수 분산
- peer의 max concurrent streams와 client 정책 재조정
- 애초에 queue를 작게 두고 fail-fast

cap만 올리면:

- memory와 scheduler pressure가 커질 수 있다
- 한 connection 장애 반경이 커질 수 있다

## 실전 시나리오

### 시나리오 1: gRPC unary는 짧은데 p99가 갑자기 튄다

실제 원인:

- 같은 channel의 streaming RPC가 slot을 오래 잡고 있다
- unary 요청은 H2 pending queue에서 기다린다

### 시나리오 2: connection pool은 한가한데 timeout이 난다

TCP connection 수는 충분해도 per-connection stream limit에 막혀 있을 수 있다.

### 시나리오 3: `SETTINGS_MAX_CONCURRENT_STREAMS`를 높였는데 오히려 불안정해졌다

queue는 줄었지만:

- 한 connection에 더 많은 work가 몰렸다
- loss나 drain 이벤트의 blast radius가 커졌다
- scheduler fairness가 나빠졌을 수 있다

### 시나리오 4: deploy나 `GOAWAY` 이후 잠깐씩 latency spike가 난다

기존 connection이 drain되며 새 connection으로 slot이 재분배되는 구간에서 pending stream queue가 튈 수 있다.

## 코드로 보기

### 관찰 포인트

```text
- active streams per connection
- queued streams waiting for stream slot
- queue wait before stream open
- unary vs streaming traffic mix on same channel
- deadline exceeded before first response byte
```

### 설계 감각

```text
separate channels for long-lived streams
bounded pending stream queue
observe stream-open latency separately
scale connections, not just streams, when blast radius matters
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 높은 stream cap | connection 수를 줄일 수 있다 | 한 connection failure domain이 커진다 | 짧은 unary 위주 |
| 낮은 cap + 더 많은 connections | 격리가 좋아진다 | handshake와 pool 관리 비용이 늘어난다 | mixed workload |
| shared channel | 단순하고 재사용 효율이 좋다 | streaming이 unary를 가로막을 수 있다 | 트래픽 특성이 비슷할 때 |
| channel 분리 | tail latency 격리가 좋다 | 운영 복잡도가 늘어난다 | unary + long-lived stream 혼합 |

핵심은 H2 병렬성을 socket 수가 아닌 **stream slot이라는 별도 자원**으로 보는 것이다.

## 꼬리질문

> Q: `SETTINGS_MAX_CONCURRENT_STREAMS`와 flow control은 어떻게 다른가요?
> 핵심: 하나는 동시에 열 수 있는 stream 수, 다른 하나는 열린 stream에서 보낼 수 있는 양이다.

> Q: TCP connection이 충분한데 왜 H2 요청이 대기하나요?
> 핵심: 같은 connection 안에서 stream slot이 부족해 pending queue가 생길 수 있기 때문이다.

> Q: stream cap을 크게 올리면 항상 좋은가요?
> 핵심: 아니다. queue는 줄어도 scheduler pressure와 failure blast radius가 커질 수 있다.

## 한 줄 정리

HTTP/2 latency를 정확히 보려면 connect/pool 지표만으로는 부족하고, `MAX_CONCURRENT_STREAMS` 앞에서 stream이 얼마나 기다렸는지도 별도 queue로 봐야 한다.
