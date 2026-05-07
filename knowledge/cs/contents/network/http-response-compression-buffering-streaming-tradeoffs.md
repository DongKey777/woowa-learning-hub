---
schema_version: 3
title: "HTTP Response Compression, Buffering, Streaming Trade-offs"
concept_id: network/http-response-compression-buffering-streaming-tradeoffs
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 85
mission_ids: []
review_feedback_tags:
- response-compression
- streaming-latency
- proxy-buffering
aliases:
- HTTP response compression
- gzip streaming
- brotli streaming
- compression flush
- response buffering
- chunk latency
- proxy gzip
- content-encoding latency
symptoms:
- gzip이나 brotli를 켠 뒤 streaming 이벤트가 몇 개씩 묶여 늦게 도착한다
- TTFB와 chunk cadence 악화를 네트워크 지연으로만 본다
- app, proxy, CDN 중 어디서 압축하거나 buffering하는지 분리하지 못한다
- content-encoding과 cache Vary 정책을 보지 않고 압축 정책만 바꾼다
intents:
- troubleshooting
- deep_dive
- design
prerequisites:
- network/request-timing-decomposition
- network/websocket-proxy-buffering-streaming-latency
next_docs:
- network/tls-record-sizing-flush-streaming-latency
- network/compression-cache-vary-accept-encoding-personalization
- network/cache-vary-accept-encoding-edge-case
- network/api-gateway-reverse-proxy-operational-points
linked_paths:
- contents/network/websocket-proxy-buffering-streaming-latency.md
- contents/network/tls-record-sizing-flush-streaming-latency.md
- contents/network/request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md
- contents/network/api-gateway-reverse-proxy-operational-points.md
- contents/network/mtu-fragmentation-mss-blackhole.md
- contents/network/compression-cache-vary-accept-encoding-personalization.md
- contents/network/cache-vary-accept-encoding-edge-case-playbook.md
confusable_with:
- network/websocket-proxy-buffering-streaming-latency
- network/tls-record-sizing-flush-streaming-latency
- network/compression-cache-vary-accept-encoding-personalization
- network/cache-vary-accept-encoding-edge-case
forbidden_neighbors: []
expected_queries:
- "HTTP 응답 압축이 streaming latency를 악화시키는 이유는?"
- "gzip brotli compression flush 때문에 SSE chunk가 늦게 오는 패턴을 설명해줘"
- "proxy response buffering과 compression buffering을 어떻게 구분해?"
- "content-encoding과 Vary Accept-Encoding을 같이 봐야 하는 이유는?"
- "TTFB는 괜찮은데 chunk cadence가 몰아서 오는 원인을 어떻게 추적해?"
contextual_chunk_prefix: |
  이 문서는 HTTP gzip/brotli response compression, compression flush,
  proxy/CDN response buffering, streaming chunk latency, content-encoding과
  cache Vary 상호작용을 다루는 advanced playbook이다.
---
# HTTP Response Compression, Buffering, Streaming Trade-offs

> 한 줄 요약: gzip이나 brotli는 대역폭을 줄이는 좋은 도구지만, streaming 경로에서는 압축 단위와 flush 타이밍이 늦어져 first byte와 chunk cadence를 망칠 수 있다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [WebSocket Proxy Buffering, Streaming Latency](./websocket-proxy-buffering-streaming-latency.md)
> - [TLS Record Sizing, Flush, Streaming Latency](./tls-record-sizing-flush-streaming-latency.md)
> - [Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB](./request-timing-decomposition-dns-connect-tls-ttfb-ttlb.md)
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
> - [MTU, Fragmentation, MSS, Blackhole](./mtu-fragmentation-mss-blackhole.md)
> - [Compression, Cache, Vary, Accept-Encoding, Personalization](./compression-cache-vary-accept-encoding-personalization.md)
> - [Cache, Vary, Accept-Encoding Edge Case Playbook](./cache-vary-accept-encoding-edge-case-playbook.md)

retrieval-anchor-keywords: HTTP compression, gzip streaming, brotli streaming, response buffering, compression flush, chunk latency, content-encoding, first byte delay, streaming compression, proxy gzip

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

HTTP 응답 압축은 대개 네트워크 비용을 줄이고 다운로드를 빠르게 만든다.

- payload bytes 감소
- 느린 회선에서 체감 개선
- CDN와 proxy 비용 절감

하지만 streaming이나 interactive response에서는 다음 부작용이 있다.

- 압축기가 더 많은 바이트를 모으려 한다
- flush가 늦어진다
- 작은 chunk가 묶여서 나간다

즉 압축은 throughput 최적화이면서 동시에 **latency shaping** 장치다.

### Retrieval Anchors

- `HTTP compression`
- `gzip streaming`
- `brotli streaming`
- `response buffering`
- `compression flush`
- `chunk latency`
- `content-encoding`
- `first byte delay`

## 깊이 들어가기

### 1. 압축은 바이트를 줄이는 대신 시간을 조금 더 쓴다

압축의 본질은 CPU와 지연 일부를 써서 네트워크 전송량을 줄이는 것이다.

- bulk download에는 이득이 크다
- 텍스트 응답에는 잘 맞는다
- 작은 응답이나 즉시성이 중요한 응답에는 애매할 수 있다

특히 대역폭이 충분하고 latency가 더 중요한 경로에서는 압축이 오히려 손해가 될 수 있다.

### 2. streaming 응답에서는 "언제 flush되는가"가 더 중요하다

SSE, progress update, chunked streaming은:

- 빨리 첫 바이트가 나가야 하고
- 작은 이벤트가 규칙적으로 보여야 한다

그런데 압축기가 내부 버퍼를 모으려 하면:

- 이벤트가 여러 개 모여 한 번에 나간다
- TTFB가 늦어진다
- 사용자 입장에서는 "멈춘 뒤 몰아서 옴"처럼 보인다

### 3. proxy와 app이 둘 다 압축하면 원인 파악이 더 어렵다

가능한 패턴:

- app이 이미 gzip
- proxy도 content-encoding 정책을 적용
- CDN이 또 다른 압축 정책을 씀

이 경우:

- 압축 위치가 어디인지 헷갈린다
- chunk cadence를 누가 바꿨는지 파악하기 어렵다
- CPU는 app가 먹고, latency는 proxy가 늘리는 식의 혼선이 생긴다

### 4. 압축 단위와 TLS record/response buffering이 서로 겹친다

실제 wire 경로에는 여러 층이 있다.

- app serialization
- compression buffer
- TLS record coalescing
- proxy response buffering

그래서 streaming latency는 한 지점만 최적화해도 해결되지 않는다.  
압축을 꺼도 TLS record와 proxy buffering이 남아 있을 수 있고, buffering을 꺼도 compression flush가 늦을 수 있다.

### 5. 모든 응답을 압축하는 정책은 흔히 과하다

다음 응답은 상대적으로 압축 이득이 크다.

- 큰 JSON
- 텍스트 문서
- 정적 자산

반대로 다음은 신중해야 한다.

- 짧은 응답
- low-latency streaming
- 이미 작거나 binary compressed payload
- 실시간 progress / heartbeat 경로

### 6. observability는 `content-encoding`과 chunk cadence를 함께 봐야 한다

다음 항목이 같이 있어야 원인 분해가 쉽다.

- 압축 여부
- compression ratio
- TTFB 변화
- chunk 간격 변화
- CPU 사용량

압축을 켠 뒤 bandwidth는 줄었는데 p99가 올랐다면, streaming/flush를 의심해야 한다.

## 실전 시나리오

### 시나리오 1: 다운로드 API는 빨라졌는데 진행률 스트림은 나빠졌다

bulk 최적화 압축 정책이 interactive stream에도 그대로 적용된 패턴일 수 있다.

### 시나리오 2: SSE 이벤트가 몇 초씩 묶여서 온다

proxy buffering뿐 아니라 compression buffer flush도 의심할 수 있다.

### 시나리오 3: CPU는 오르고 네트워크 사용량은 줄었는데 사용자 체감은 비슷하다

응답 크기는 줄었지만 latency-sensitive 경로에서는 압축 이득이 작았을 수 있다.

### 시나리오 4: 특정 경로만 p99가 늘었다

content-encoding, response size 분포, streaming 여부가 다른 endpoint일 수 있다.

## 코드로 보기

### 관찰 포인트

```text
- content-encoding: gzip / br / none
- response size before/after compression
- TTFB delta after enabling compression
- chunk cadence under streaming
- CPU cost on proxy/app
```

### 현장 질문

```text
- 이 endpoint는 throughput보다 first byte가 중요한가
- app, proxy, CDN 중 누가 압축하는가
- streaming response에 같은 압축 정책을 쓰고 있는가
- compression flush와 proxy buffering이 겹치는가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| aggressive compression | bandwidth와 egress 비용을 줄인다 | CPU와 latency가 늘 수 있다 | 큰 텍스트 응답 |
| selective compression | endpoint 특성에 맞춘 최적화가 가능하다 | 정책 관리가 복잡하다 | mixed workload |
| streaming 경로 무압축 | first byte와 chunk cadence가 좋아진다 | payload bytes가 늘어난다 | SSE, progress stream |
| proxy-level 중앙 압축 | 운영이 단순하다 | app 특성별 세밀 제어가 어렵다 | 공통 텍스트 응답 |

핵심은 압축을 단순 성능 기능으로 보지 않고 **대역폭 절감과 streaming latency 사이의 교환**으로 보는 것이다.

## 꼬리질문

> Q: 압축을 켜면 항상 빨라지나요?
> 핵심: 아니다. bulk transfer엔 유리해도 streaming이나 작은 응답에선 latency가 나빠질 수 있다.

> Q: SSE가 묶여서 오면 proxy buffering만 보면 되나요?
> 핵심: 아니다. compression flush와 TLS record coalescing도 같이 봐야 한다.

> Q: 왜 모든 endpoint에 같은 압축 정책을 쓰면 안 좋나요?
> 핵심: throughput이 중요한 경로와 first byte가 중요한 경로의 최적점이 다르기 때문이다.

## 한 줄 정리

HTTP 응답 압축은 bytes를 줄이는 대신 flush와 chunk cadence를 바꿔 streaming latency를 건드릴 수 있으므로, bulk endpoint와 interactive endpoint를 같은 정책으로 다루면 안 된다.
