---
schema_version: 2
title: "Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB"
concept_id: "network/request-timing-decomposition"
difficulty: advanced
doc_role: deep_dive
level: advanced
aliases:
  - request timing decomposition
  - TTFB
  - TTLB
  - DNS time
  - connect time
  - TLS handshake
  - latency breakdown
expected_queries:
  - TTFB랑 TTLB는 뭐가 달라?
  - 요청 latency를 DNS connect TLS로 어떻게 나눠?
  - latency breakdown은 어떻게 봐?
  - time_starttransfer는 뭐야?
---

# Request Timing Decomposition: DNS, Connect, TLS, TTFB, TTLB

> 한 줄 요약: "요청이 2초 걸렸다"는 말만으로는 원인을 못 찾는다. DNS, connect, TLS, queue wait, TTFB, TTLB를 분리해 봐야 어느 계층이 실제로 시간을 태웠는지 보인다.
>
> 문서 역할: 이 문서는 network 운영 cluster 안에서 **latency breakdown 관측과 원인 분해**를 맡는 deep dive다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Browser DevTools Waterfall Primer: DNS, Connect, SSL, Waiting 읽기](./browser-devtools-waterfall-primer.md)
> - [Timeout 타입: connect, read, write](./timeout-types-connect-read-write.md)
> - [Upstream Queueing, Connection Pool Wait, Tail Latency](./upstream-queueing-connection-pool-wait-tail-latency.md)
> - [TLS Session Resumption, 0-RTT, Replay Risk](./tls-session-resumption-0rtt-replay-risk.md)
> - [Packet Loss, Jitter, Reordering Diagnostics](./packet-loss-jitter-reordering-diagnostics.md)
> - [Happy Eyeballs, Dual-Stack Racing](./happy-eyeballs-dual-stack-racing.md)
> - [Queue Saturation Attribution, Metrics, Runbook](./queue-saturation-attribution-metrics-runbook.md)
> - [Network, Spring Request Lifecycle, Timeout, Disconnect Bridge](./network-spring-request-lifecycle-timeout-disconnect-bridge.md)
> - [Spring MVC 요청 생명주기](../spring/spring-mvc-request-lifecycle.md)
> - [Spring RestClient vs WebClient Lifecycle Boundaries](../spring/spring-restclient-vs-webclient-lifecycle-boundaries.md)

retrieval-anchor-keywords: request timing decomposition, DNS time, connect time, TLS handshake time, TTFB, TTLB, queue wait, time_namelookup, time_connect, time_appconnect, time_starttransfer, latency breakdown

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

## 이 문서 다음에 보면 좋은 문서

- DevTools `dns`/`connect`/`ssl`/`waiting` 라벨을 먼저 읽고 싶다면 [Browser DevTools Waterfall Primer: DNS, Connect, SSL, Waiting 읽기](./browser-devtools-waterfall-primer.md)부터 본다.
- 전체 예산 설계는 [Timeout Budget Propagation Across Proxy, Gateway, Service Hops](./timeout-budget-propagation-proxy-gateway-service-hop-chain.md)로 이어진다.
- 재시도 / 타임아웃 정책 자체는 [Timeout, Retry, Backoff 실전](./timeout-retry-backoff-practical.md)과 같이 보는 편이 좋다.
- queue wait가 병목으로 보이면 [Upstream Queueing, Connection Pool Wait, Tail Latency](./upstream-queueing-connection-pool-wait-tail-latency.md)를 이어서 본다.

## 핵심 개념

전체 latency는 하나의 시간이 아니라 여러 구간의 합이다.

- DNS resolution
- TCP connect
- TLS handshake
- local queue wait
- request write
- TTFB(time to first byte)
- TTLB(time to last byte)

중요한 점은 일부 대시보드가 이 중 몇 개만 보여 준다는 점이다.  
그래서 실제 병목은 queue wait인데 connect가 느리다고 오해하거나, TLS는 빠른데 TTFB만 보고 네트워크 탓을 하기도 쉽다.

### Retrieval Anchors

- `request timing decomposition`
- `DNS time`
- `connect time`
- `TLS handshake time`
- `TTFB`
- `TTLB`
- `queue wait`
- `latency breakdown`

## 깊이 들어가기

### 1. phase timing은 누적값이라는 점을 먼저 이해해야 한다

예를 들어 curl 계열 지표는 보통 이런 감각이다.

- `time_namelookup`: DNS까지 누적
- `time_connect`: TCP connect까지 누적
- `time_appconnect`: TLS까지 누적
- `time_starttransfer`: first byte까지 누적
- `time_total`: 전체 완료까지 누적

즉 각 값을 바로 비교하기보다 **구간 차이**를 봐야 한다.

- DNS 구간 = `time_namelookup`
- connect 구간 = `time_connect - time_namelookup`
- TLS 구간 = `time_appconnect - time_connect`
- server think + upstream wait + first byte 지연 = `time_starttransfer - time_appconnect`
- body transfer 구간 = `time_total - time_starttransfer`

### 2. TTFB는 서버 코드 시간과 같은 말이 아니다

TTFB가 길다고 해서 무조건 앱 로직이 느린 건 아니다.

TTFB 안에는 여러 요소가 섞일 수 있다.

- upstream connection pool wait
- proxy worker queue
- TLS resumption 실패
- auth / rate limit / routing
- app compute
- DB lock or queueing
- response header가 나가기 전 buffering

그래서 TTFB를 "서버 처리 시간"으로 단순 치환하면 자주 틀린다.

### 3. TTLB는 body streaming과 flush 정책까지 포함한다

first byte가 빨라도 total이 늦을 수 있다.

- large response body
- slow client download
- proxy buffering
- chunk flush 간격
- TLS record coalescing

특히 streaming API는 TTFB보다 **chunk cadence와 TTLB**가 더 의미 있을 수 있다.

### 4. queue wait는 phase timing에서 가장 쉽게 사라진다

로컬 queueing은 네트워크 계층 바깥에서 발생할 수 있다.

- request가 아직 socket도 못 잡았다
- H2 pending stream queue에서 기다린다
- worker queue에서 dispatch 전 대기한다

이 구간은 connect/tls 계측만으로는 사라진다.  
그래서 "connect는 5ms인데 왜 요청은 700ms냐" 같은 현상이 생긴다.

### 5. TLS와 DNS는 캐시 hit 여부에 따라 분포가 갈린다

phase timing이 bimodal하게 보이면 cache hit/miss를 의심할 수 있다.

- DNS cache hit vs miss
- TLS resumption hit vs full handshake
- idle keep-alive reuse vs 새 connection

평균으로만 보면 이런 분포가 묻힌다.

### 6. proxy chain에서는 hop별 timing을 따로 남겨야 한다

edge 하나만 보면 실제 병목을 놓친다.

- edge access log의 request time
- upstream connect time
- upstream first byte time
- application internal queue wait
- downstream write time

이런 구간이 분리되어야 "edge는 2초, app은 80ms" 같은 상황을 설명할 수 있다.

## 실전 시나리오

### 시나리오 1: `time_appconnect`는 빠른데 `time_starttransfer`만 늦다

가능한 원인:

- app compute 또는 DB lock
- proxy auth/routing
- upstream queueing
- H2 pending stream queue

### 시나리오 2: `time_total`만 길고 TTFB는 정상이다

가능한 원인:

- large body 전송
- slow client
- proxy buffering
- flush 간격이 길다

### 시나리오 3: 첫 요청만 느리고 이후는 빠르다

DNS miss, full handshake, warm-up, cold connection을 의심할 수 있다.

### 시나리오 4: 평균은 괜찮은데 p99만 튄다

일부 요청만:

- DNS miss
- connect retransmission
- queue saturation
- slow downstream write

를 만나는 분포일 수 있다.

## 코드로 보기

### curl timing 감각

```bash
curl -w 'dns=%{time_namelookup} connect=%{time_connect} tls=%{time_appconnect} ttfb=%{time_starttransfer} total=%{time_total}\n' \
  -o /dev/null -s https://api.example.com
```

### phase를 차이로 해석하는 감각

```text
dns   = namelookup
tcp   = connect - namelookup
tls   = appconnect - connect
ttfb  = starttransfer - appconnect
body  = total - starttransfer
```

### 관찰 포인트

```text
- queue wait를 phase timing 밖에서 별도 계측하는가
- upstream connect / first byte / total을 hop마다 남기는가
- first request vs reused connection 분포가 분리되는가
- TTFB와 TTLB를 같은 원인으로 뭉개고 있지 않은가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| coarse total latency만 수집 | 단순하다 | 병목 위치를 거의 못 찾는다 | 아주 초기 모니터링 |
| phase timing 수집 | 원인 분해가 빨라진다 | 계측 포인트가 늘어난다 | 운영 서비스 |
| hop별 상세 timing | blame이 쉬워진다 | 로그/메트릭 설계가 복잡하다 | proxy chain, microservices |
| sampled deep tracing | 세밀한 원인 분석이 가능하다 | 지속적 전량 수집은 비싸다 | p99/p999 조사 |

핵심은 latency를 총합 하나로 보지 않고 **구간 차이와 분포**로 보는 것이다.

## 꼬리질문

> Q: TTFB가 길면 항상 서버 코드가 느린 건가요?
> 핵심: 아니다. queue wait, TLS, routing, upstream wait도 first byte 전 구간에 포함될 수 있다.

> Q: TTLB가 길면 무엇을 의심하나요?
> 핵심: 큰 body, slow client, buffering, flush 정책을 먼저 본다.

> Q: 왜 queue wait가 phase timing에서 잘 안 보이나요?
> 핵심: socket을 잡기 전 로컬 대기는 네트워크 timing 지표 밖에 숨어 있을 수 있기 때문이다.

## 한 줄 정리

정확한 네트워크 진단은 "전체 2초"가 아니라 DNS, connect, TLS, queue, TTFB, TTLB를 분해해서 어느 구간이 실제로 꼬리를 만들었는지 보는 것에서 시작한다.
