---
schema_version: 3
title: "HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block"
concept_id: network/http2-http3-downgrade-attribution-alt-svc-udp-block
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 87
mission_ids: []
review_feedback_tags:
- http3-downgrade
- udp-block
- alt-svc
aliases:
- HTTP/3 downgrade
- H3 fallback
- H2 fallback
- Alt-Svc downgrade attribution
- UDP block
- browser alt-svc cache
- ALPN fallback
symptoms:
- HTTP/3가 안 붙는데 요청은 성공해서 protocol downgrade를 놓친다
- Alt-Svc 광고, browser cache, UDP block, CDN policy 중 원인 주체를 가르지 못한다
- synthetic test는 H3 성공인데 실제 사용자망에서는 H2로 조용히 fallback된다
- Protocol=h2 결과만 보고 QUIC version negotiation 문제로 단정한다
intents:
- troubleshooting
- deep_dive
- comparison
prerequisites:
- network/browser-http-version-selection-alpn-alt-svc-fallback
- network/h3-fallback-trace-bridge
next_docs:
- network/http3-quic-practical-tradeoffs
- network/quic-version-negotiation-fallback
- network/alpn-negotiation-failure-routing-mismatch
- network/http2-http3-connection-reuse-coalescing
linked_paths:
- contents/network/browser-http-version-selection-alpn-alt-svc-fallback.md
- contents/network/h3-fallback-trace-bridge.md
- contents/network/http3-quic-practical-tradeoffs.md
- contents/network/quic-version-negotiation-fallback.md
- contents/network/alpn-negotiation-failure-routing-mismatch.md
- contents/network/http2-http3-connection-reuse-coalescing.md
- contents/network/proxy-local-reply-vs-upstream-error-attribution.md
confusable_with:
- network/h3-fallback-trace-bridge
- network/quic-version-negotiation-fallback
- network/alpn-negotiation-failure-routing-mismatch
- network/http3-quic-practical-tradeoffs
forbidden_neighbors: []
expected_queries:
- "HTTP/3가 조용히 H2로 downgrade되는 원인을 어떻게 attribution해?"
- "Alt-Svc는 있는데 특정 회사망에서만 H3가 안 붙으면 UDP block을 어떻게 확인해?"
- "browser Alt-Svc cache와 CDN H3 policy가 downgrade에 미치는 영향은?"
- "Protocol=h2 결과만으로 HTTP/3 fallback 원인을 단정하면 안 되는 이유는?"
- "H3 attempted ratio와 success ratio를 어떤 지표로 봐야 해?"
contextual_chunk_prefix: |
  이 문서는 HTTP/3 to HTTP/2 downgrade attribution, Alt-Svc cache,
  UDP/QUIC block, ALPN fallback, CDN/proxy/browser policy를 다루는 advanced
  playbook이다.
---
# HTTP/2, HTTP/3 Downgrade Attribution, Alt-Svc, UDP Block

> 한 줄 요약: 사용자가 "HTTP/3가 안 붙고 느리다"고 느낄 때 원인은 QUIC 버전 협상 하나가 아니다. `Alt-Svc` 광고, UDP 차단, ALPN, proxy/CDN policy, browser cache가 겹치며 조용한 downgrade가 일어난다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [브라우저의 HTTP 버전 선택: ALPN, Alt-Svc, Fallback 입문](./browser-http-version-selection-alpn-alt-svc-fallback.md)
> - [H3 Fallback Trace Bridge: Discovery Evidence에서 UDP Block과 H2 Fallback 읽기](./h3-fallback-trace-bridge.md)
> - [HTTP/3, QUIC Practical Trade-offs](./http3-quic-practical-tradeoffs.md)
> - [QUIC Version Negotiation, Fallback Behavior](./quic-version-negotiation-fallback.md)
> - [ALPN Negotiation Failure, Routing Mismatch](./alpn-negotiation-failure-routing-mismatch.md)
> - [HTTP/2, HTTP/3 Connection Reuse, Coalescing](./http2-http3-connection-reuse-coalescing.md)
> - [Proxy Local Reply vs Upstream Error Attribution](./proxy-local-reply-vs-upstream-error-attribution.md)

retrieval-anchor-keywords: HTTP/3 downgrade, Alt-Svc, UDP block, H3 fallback, H2 fallback, downgrade attribution, browser alt-svc cache, ALPN fallback, QUIC disabled path, protocol downgrade

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

HTTP/3 도입 뒤 실제 사용자 경로는 종종 다음처럼 움직인다.

- 먼저 H3 시도
- 실패 또는 정책상 회피
- H2 또는 H1로 조용히 downgrade

문제는 이 downgrade가 대개 사용자에게는 "조금 느린 것"으로만 보인다는 점이다.

초급 triage에서 discovery evidence와 UDP block attribution 사이를 먼저 짧게 연결해야 하면 [H3 Fallback Trace Bridge: Discovery Evidence에서 UDP Block과 H2 Fallback 읽기](./h3-fallback-trace-bridge.md)를 먼저 본 뒤 이 문서로 돌아오면 된다.

### Retrieval Anchors

- `HTTP/3 downgrade`
- `Alt-Svc`
- `UDP block`
- `H3 fallback`
- `H2 fallback`
- `downgrade attribution`
- `browser alt-svc cache`
- `ALPN fallback`

## 깊이 들어가기

### 1. downgrade는 실패와 성공 사이의 회색 지대다

완전 장애가 아니면 운영자가 놓치기 쉽다.

- 요청은 결국 성공한다
- 다만 기대한 protocol이 아니다
- latency, CPU, connection behavior만 달라진다

그래서 "서비스는 정상이지만 체감은 나빠진" 상태가 생긴다.

### 2. `Alt-Svc`가 H3 진입의 시작점이자 함정일 수 있다

브라우저는 종종 먼저 H2/H1로 연결한 뒤, `Alt-Svc`를 보고 다음부터 H3를 시도한다.

문제 패턴:

- 오래된 `Alt-Svc` cache
- edge는 H3 광고하지만 일부 path는 UDP 차단
- 광고 포트/endpoint와 실제 QUIC listener mismatch

이 경우 first request와 subsequent request의 동작이 달라진다.

### 3. downgrade 원인은 transport, policy, routing 세 층에 있을 수 있다

transport:

- UDP blocked
- QUIC path MTU 문제
- version negotiation failure

policy:

- browser가 해당 path를 일시적으로 회피
- enterprise proxy가 UDP를 금지
- CDN/provider가 특정 region에서 H3 비활성화

routing:

- ALPN mismatch
- `Alt-Svc`가 가리키는 endpoint와 실제 edge가 다름
- 일부 PoP만 H3 준비가 덜 됨

### 4. same URL이라도 first request와 warmed path가 다를 수 있다

H3는 cache와 advertisement 영향을 많이 받는다.

- 첫 요청: H2
- 이후 요청: H3 시도
- 일부 실패 후 다시 H2 고정

그래서 synthetic test와 real browser telemetry가 다른 이유가 생긴다.

### 5. downgrade attribution은 "누가 H3를 막았는가"를 좁히는 문제다

가능한 책임 주체:

- client network
- browser policy/cache
- corporate proxy / firewall
- CDN edge
- origin/front proxy configuration

같은 "H3 안 씀"이라도 조치가 완전히 다르다.

### 6. observability는 success rate보다 protocol selection 분포를 봐야 한다

중요한 지표:

- H3 attempted ratio
- H3 success ratio
- downgrade to H2 ratio
- downgrade reason bucket
- region / ASN / browser별 편차

성공률만 보면 downgrade는 거의 다 숨어 버린다.

## 실전 시나리오

### 시나리오 1: synthetic test는 H3가 잘 붙는데 실제 사용자는 체감이 없다

브라우저 alt-svc cache, enterprise firewall, mobile carrier path 차이가 원인일 수 있다.

### 시나리오 2: 특정 회사망에서만 H3가 거의 안 붙는다

UDP 443 차단 또는 explicit proxy 경유 정책을 의심할 수 있다.

### 시나리오 3: CDN 설정 바꾼 뒤 일부 지역만 느려졌다

일부 PoP의 H3 광고/listener mismatch 또는 region별 provider policy 차이일 수 있다.

### 시나리오 4: app 팀은 변화가 없다고 하는데 edge 팀만 protocol 분포 변화를 본다

downgrade는 app success rate와 분리된 edge-layer 현상일 수 있다.

## 코드로 보기

### 확인 감각

```bash
curl --http3 -I https://example.com
curl --http2 -I https://example.com
```

### 관찰 포인트

```text
- Alt-Svc advertised?
- H3 attempted but downgraded?
- UDP path blocked or flaky?
- region / browser / ASN별 downgrade 비율은 어떤가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| aggressive H3 advertising | 더 많은 사용자에게 H3 이득을 준다 | 준비 안 된 path에서 downgrade noise가 커진다 | edge 최적화 단계 |
| conservative rollout | attribution이 쉽다 | H3 이득이 늦게 퍼진다 | 초기 도입 |
| graceful downgrade | 성공률이 높다 | downgrade가 관측에서 숨기 쉬워진다 | 일반 서비스 |
| strict H3 expectation | 문제를 빨리 드러낸다 | 사용자 체감 실패가 커질 수 있다 | 실험/검증 환경 |

핵심은 H3/H2 전환을 단순 fallback이 아니라 **protocol selection과 downgrade attribution 문제**로 보는 것이다.

## 꼬리질문

> Q: H3 downgrade는 왜 운영에서 놓치기 쉬운가요?
> 핵심: 요청은 결국 성공하므로 성공률 대시보드에는 잘 드러나지 않고, 체감 latency만 바뀔 수 있기 때문이다.

> Q: `Alt-Svc`는 왜 중요한가요?
> 핵심: 브라우저가 이후 H3를 시도할지 말지를 결정하는 힌트이자 cache mismatch 원인이 되기 때문이다.

> Q: H3가 안 붙으면 항상 QUIC 버전 협상 문제인가요?
> 핵심: 아니다. UDP 차단, ALPN, proxy policy, browser cache 등 여러 층이 원인일 수 있다.

## 한 줄 정리

HTTP/3 downgrade를 제대로 보려면 QUIC 실패만이 아니라 `Alt-Svc`, UDP path, ALPN, edge policy가 어떻게 H2/H1로 조용히 내려가게 만드는지까지 함께 추적해야 한다.
