---
schema_version: 3
title: "h2c, Cleartext Upgrade, Prior Knowledge, Routing"
concept_id: network/h2c-cleartext-upgrade-prior-knowledge-routing
canonical: true
category: network
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- h2c-cleartext-http2
- prior-knowledge-upgrade
- grpc-proxy-routing
aliases:
- h2c
- cleartext HTTP/2
- Upgrade h2c
- prior knowledge HTTP2
- grpc cleartext
- protocol preface routing
symptoms:
- HTTP/2 지원이라고 보고 h2와 h2c 진입 방식을 구분하지 않는다
- public TLS h2는 되는데 internal cleartext gRPC만 깨지는 이유를 놓친다
- Upgrade h2c와 prior knowledge를 proxy chain이 같은 방식으로 처리한다고 생각한다
intents:
- deep_dive
- troubleshooting
- comparison
prerequisites:
- network/http1-http2-http3-beginner-comparison
- network/alpn-negotiation-failure-routing-mismatch
next_docs:
- network/h2c-operational-traps-proxy-chain-dev-prod
- network/grpc-vs-rest
- network/http2-rst-stream-goaway-streaming-failure-semantics
- network/api-gateway-reverse-proxy-operational-points
linked_paths:
- contents/network/alpn-negotiation-failure-routing-mismatch.md
- contents/network/grpc-vs-rest.md
- contents/network/http2-multiplexing-hol-blocking.md
- contents/network/api-gateway-reverse-proxy-operational-points.md
- contents/network/http2-rst-stream-goaway-streaming-failure-semantics.md
- contents/network/h2c-operational-traps-proxy-chain-dev-prod.md
confusable_with:
- network/h2c-operational-traps-proxy-chain-dev-prod
- network/alpn-negotiation-failure-routing-mismatch
- network/grpc-vs-rest
- network/http2-rst-stream-goaway-streaming-failure-semantics
forbidden_neighbors: []
expected_queries:
- "h2와 h2c는 같은 HTTP/2인데 진입 방식이 어떻게 달라?"
- "Upgrade h2c와 prior knowledge가 proxy routing에서 다르게 깨지는 이유를 설명해줘"
- "public HTTPS h2는 되는데 internal cleartext gRPC만 안 되면 무엇을 의심해?"
- "HTTP/2 protocol preface를 모르는 proxy가 있으면 어떤 오류가 나?"
- "h2c를 운영에서 deliberate choice로 봐야 하는 이유가 뭐야?"
contextual_chunk_prefix: |
  이 문서는 HTTP/2 over TLS h2와 cleartext h2c를 구분하고, Upgrade: h2c,
  prior knowledge, protocol preface, internal mesh/gRPC/proxy routing mismatch를
  설명하는 advanced HTTP/2 deep dive다.
---
# h2c, Cleartext Upgrade, Prior Knowledge, Routing

> 한 줄 요약: HTTP/2는 TLS 위의 `h2`만 있는 것이 아니다. cleartext 환경에서는 `Upgrade: h2c`와 prior knowledge가 섞이는데, proxy와 routing이 이를 기대하지 않으면 "왜 h2만 안 되지?" 같은 미묘한 장애가 생긴다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [ALPN Negotiation Failure, Routing Mismatch](./alpn-negotiation-failure-routing-mismatch.md)
> - [gRPC vs REST](./grpc-vs-rest.md)
> - [HTTP/2 멀티플렉싱과 HOL blocking](./http2-multiplexing-hol-blocking.md)
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
> - [HTTP/2 RST_STREAM, GOAWAY, Streaming Failure Semantics](./http2-rst-stream-goaway-streaming-failure-semantics.md)
> - [h2c Operational Traps: Proxy Chain, Dev/Prod Drift](./h2c-operational-traps-proxy-chain-dev-prod.md)

retrieval-anchor-keywords: h2c, cleartext HTTP/2, Upgrade h2c, prior knowledge, HTTP/2 over cleartext, proxy routing mismatch, gRPC cleartext, h2c upgrade, protocol preface, internal mesh traffic

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

HTTP/2 진입 방식은 둘로 나뉜다.

- TLS 위 ALPN `h2`
- cleartext 환경의 `h2c`

`h2c`에서도 다시 두 방식이 있다.

- `Upgrade: h2c`
- prior knowledge(처음부터 HTTP/2 preface 전송)

즉 "HTTP/2 지원"이라고 해도 **어떤 진입 방식까지 지원하는가**를 명확히 해야 한다.

### Retrieval Anchors

- `h2c`
- `cleartext HTTP/2`
- `Upgrade h2c`
- `prior knowledge`
- `HTTP/2 over cleartext`
- `proxy routing mismatch`
- `gRPC cleartext`
- `protocol preface`

## 깊이 들어가기

### 1. `h2`와 `h2c`는 같은 HTTP/2지만 진입 방식이 다르다

TLS 환경에선 ALPN으로 `h2`를 협상한다.  
cleartext 환경에선 그런 협상이 없으므로 별도 방식이 필요하다.

- HTTP/1.1로 시작 후 `Upgrade: h2c`
- 또는 prior knowledge로 바로 HTTP/2 preface

그래서 proxy가 "HTTP/2는 지원"한다고 해도 h2c까지 된다는 뜻은 아니다.

### 2. internal traffic에서만 문제처럼 보이기 쉽다

대외 HTTPS는 `h2`로 잘 되는데 내부망만 이상한 이유:

- 내부 ingress/service mesh는 cleartext hop이 있다
- gRPC cleartext를 쓰는 개발/테스트 환경이 있다
- local dev proxy가 TLS termination 없이 HTTP/2를 기대한다

즉 h2c 문제는 종종 **내부 통신에서만 재현**된다.

### 3. prior knowledge와 upgrade는 proxy 기대치가 다르다

`Upgrade: h2c`:

- 처음엔 HTTP/1.1처럼 보인다
- 중간 홉이 upgrade header를 이해해야 한다

prior knowledge:

- 처음부터 HTTP/2 preface를 보낸다
- 중간 홉이 cleartext H2를 바로 이해해야 한다

그래서 proxy나 LB가 어느 쪽을 기대하는지 맞지 않으면 protocol error, fallback, reset이 생긴다.

### 4. gRPC는 특히 h2c mismatch에 민감하다

gRPC는 HTTP/2 전제를 강하게 깐다.

- cleartext 환경에서 gRPC client는 h2c를 기대할 수 있다
- proxy는 HTTP/1.1로만 처리하려 할 수 있다
- 결과는 vague한 `UNAVAILABLE`, protocol error, or reset

그래서 "gRPC only broken" 상황을 만들기 쉽다.

### 5. observability는 protocol entry mode를 보여 줘야 한다

중요한 구분:

- TLS + ALPN h2
- cleartext upgrade
- cleartext prior knowledge
- downgraded to HTTP/1.1

이걸 안 남기면 "HTTP/2가 느리다/안 된다" 정도로만 보이게 된다.

### 6. 운영에서 h2c는 deliberate choice여야 한다

h2c는 그냥 "TLS 없는 h2" 정도로 켜면 안 된다.

- internal trusted network인가
- proxy chain이 모두 지원하는가
- cleartext gRPC가 정말 필요한가
- fallback과 observability가 있는가

를 먼저 봐야 한다.

## 실전 시나리오

### 시나리오 1: public HTTPS는 잘 되는데 internal gRPC만 깨진다

h2c entry mode mismatch를 의심할 만하다.

### 시나리오 2: dev 환경에선 되는데 ingress 뒤에서는 안 된다

local proxy는 prior knowledge를 이해하지만 ingress는 HTTP/1.1 upgrade만 기대하는 패턴일 수 있다.

### 시나리오 3: cleartext 내부 호출이 간헐적으로 HTTP/1.1로 떨어진다

중간 홉이 upgrade를 무시하거나 protocol preface를 정상 전달하지 못한 것일 수 있다.

### 시나리오 4: gRPC client는 `UNAVAILABLE`만 보이고 서버는 조용하다

entry mode mismatch가 proxy에서 protocol level failure로 끝났을 수 있다.

## 코드로 보기

### 관찰 포인트

```text
- ALPN h2인가, h2c upgrade인가, prior knowledge인가
- proxy가 cleartext H2 preface를 이해하는가
- upgrade header가 중간 홉에서 보존되는가
- failure surface가 HTTP/1.1 fallback인지 reset인지 protocol error인지
```

### 현장 질문

```text
- 이 hop은 TLS termination 뒤 cleartext로 바뀌는가
- gRPC client가 h2c를 기대하는가
- proxy/LB는 upgrade와 prior knowledge 중 무엇을 지원하는가
- downgrade / reset을 계측하고 있는가
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| TLS + ALPN h2 | 표준적이고 관측이 비교적 명확하다 | TLS 비용과 인증서 운영이 있다 | 일반 운영 |
| h2c upgrade | cleartext 환경과 일부 legacy 프록시에 맞출 수 있다 | 중간 홉 지원 차이가 크다 | 내부/제한 환경 |
| h2c prior knowledge | 단순한 cleartext H2 진입이 가능하다 | proxy mismatch에 더 민감하다 | 통제된 내부망 |
| HTTP/1.1 fallback | 호환성이 좋다 | gRPC/H2 기능이 사라진다 | 임시 대응 |

핵심은 HTTP/2 지원 여부보다 **어떤 진입 방식(h2, h2c upgrade, prior knowledge)을 경로 전체가 이해하는가**를 확인하는 것이다.

## 꼬리질문

> Q: `h2`와 `h2c`의 차이는 무엇인가요?
> 핵심: `h2`는 보통 TLS+ALPN, `h2c`는 cleartext HTTP/2 진입 방식이다.

> Q: prior knowledge는 무엇인가요?
> 핵심: 처음부터 HTTP/2 preface를 보내 cleartext H2로 바로 시작하는 방식이다.

> Q: 왜 internal gRPC에서만 이런 문제가 잘 보이나요?
> 핵심: 내부 cleartext hop과 h2c 기대치가 섞이기 쉽기 때문이다.

## 한 줄 정리

h2c 문제는 "HTTP/2 지원 여부"보다 cleartext 경로에서 upgrade와 prior knowledge를 proxy chain이 실제로 어떻게 이해하는가의 문제다.
