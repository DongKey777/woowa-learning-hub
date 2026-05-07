---
schema_version: 3
title: "Proxy Header Normalization Chain, Trust Boundary"
concept_id: network/proxy-header-normalization-chain-trust-boundary
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- proxy-headers
- trust-boundary
- header-normalization
aliases:
- proxy header normalization
- proxy chain trust boundary
- X-Forwarded-For normalization
- Forwarded header rewriting
- header sanitization
- ingress chain canonicalization
- X-Forwarded-Proto secure cookie
symptoms:
- 외부 client가 넣은 X-Forwarded-For를 trusted proxy 값처럼 읽는다
- proxy hop마다 header append/rewrite 규칙이 달라 client IP와 proto가 흔들린다
- X-Forwarded-Proto가 틀려 secure cookie나 redirect URL이 깨진다
- CDN WAF LB proxy app chain에서 어디서 신뢰 경계를 초기화해야 하는지 모른다
intents:
- troubleshooting
- deep_dive
- design
prerequisites:
- network/forwarded-x-forwarded-for-x-real-ip-trust-boundary
- network/api-gateway-reverse-proxy-operational-points
next_docs:
- network/proxy-protocol-client-ip-trust-boundary
- network/tls-loadbalancing-proxy
- network/alb-elb-retry-amplification-proxy-chain
- network/http-proxy-auth-407-explicit-proxy
linked_paths:
- contents/network/forwarded-x-forwarded-for-x-real-ip-trust-boundary.md
- contents/network/api-gateway-reverse-proxy-operational-points.md
- contents/network/tls-loadbalancing-proxy.md
- contents/network/proxy-protocol-client-ip-trust-boundary.md
- contents/network/alb-elb-retry-amplification-proxy-chain.md
confusable_with:
- network/forwarded-x-forwarded-for-x-real-ip-trust-boundary
- network/proxy-protocol-client-ip-trust-boundary
- network/tls-loadbalancing-proxy
- network/api-gateway-reverse-proxy-operational-points
forbidden_neighbors: []
expected_queries:
- "proxy chain에서 X-Forwarded-For를 어떻게 normalize해야 안전해?"
- "trust boundary 밖에서 들어온 Forwarded header를 왜 제거하거나 재작성해야 해?"
- "X-Forwarded-Proto가 틀려 secure cookie가 깨지는 원인을 설명해줘"
- "CDN WAF LB proxy app에서 client IP header 신뢰 경계를 어떻게 잡아?"
- "Forwarded와 X-Forwarded-*를 함께 쓸 때 canonical form이 필요한 이유는?"
contextual_chunk_prefix: |
  이 문서는 proxy chain에서 Forwarded, X-Forwarded-For, X-Forwarded-Proto,
  X-Real-IP header normalization, sanitization, canonicalization, trust boundary를
  다루는 advanced playbook이다.
---
# Proxy Header Normalization Chain, Trust Boundary

> 한 줄 요약: 프록시 헤더는 누적만 해서는 안 되고, 각 홉에서 정규화와 재작성 규칙을 지켜야 신뢰 경계가 흐트러지지 않는다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Forwarded, X-Forwarded-For, X-Real-IP와 Trust Boundary](./forwarded-x-forwarded-for-x-real-ip-trust-boundary.md)
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)
> - [TLS, 로드밸런싱, 프록시](./tls-loadbalancing-proxy.md)
> - [Proxy Protocol, Client IP, Trust Boundary](./proxy-protocol-client-ip-trust-boundary.md)
> - [ALB, ELB Retry Amplification, Proxy Chain](./alb-elb-retry-amplification-proxy-chain.md)

retrieval-anchor-keywords: header normalization, proxy chain, trust boundary, X-Forwarded-For, Forwarded, header rewriting, sanitization, canonicalization, ingress chain

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

proxy 헤더는 단순히 "전달"하는 게 아니라 **정규화(normalization)** 해야 한다.

- 외부에서 들어온 값은 제거하거나 재작성한다
- trusted proxy가 붙인 값만 누적한다
- hop마다 동일한 정책으로 canonical form을 유지한다

### Retrieval Anchors

- `header normalization`
- `proxy chain`
- `trust boundary`
- `X-Forwarded-For`
- `Forwarded`
- `header rewriting`
- `sanitization`
- `canonicalization`
- `ingress chain`

## 깊이 들어가기

### 1. 왜 normalization이 필요한가

헤더는 문자열이다.

- 공격자가 임의로 넣을 수 있다
- 중간 프록시가 여러 번 붙으면 값이 길어질 수 있다
- 서로 다른 형식이 섞일 수 있다

그래서 "읽기"보다 "정리"가 먼저다.

### 2. chain에서 어떤 일이 일어나나

예를 들어 체인이 다음과 같다면:

```text
Client -> CDN -> WAF -> LB -> Proxy -> App
```

각 홉은 다음 역할을 한다.

- CDN/WAF: 외부 입력을 제거하고 신뢰 가능한 정보를 남긴다
- LB: 원본 IP와 proto를 정리한다
- Proxy: 다시 canonical header를 만든다
- App: 마지막으로 trusted chain만 읽는다

### 3. 잘못된 normalization이 만드는 문제

- 헤더가 중복된다
- IP 순서가 뒤집힌다
- proto/host가 일치하지 않는다
- trust boundary 밖의 값이 남는다

### 4. 왜 canonical form이 중요한가

운영과 로그 분석은 한 가지 형태를 기대한다.

- `Forwarded`만 쓰거나
- `X-Forwarded-*`만 쓰거나
- 둘을 함께 쓰더라도 우선순위를 정해야 한다

형식이 일정하지 않으면 tracing이 꼬인다.

### 5. 어디서 끊어야 하나

외부 경계에서 들어온 값은 한 번 초기화하는 편이 안전하다.

- 익명 client header는 버린다
- trusted proxy가 재작성한다
- app은 마지막 chain만 읽는다

## 실전 시나리오

### 시나리오 1: 로그마다 client IP가 다르게 나온다

정규화 규칙이 홉마다 달라졌을 수 있다.

### 시나리오 2: proto가 http로 찍혀 secure cookie가 깨진다

proxy chain 중간에서 `X-Forwarded-Proto`가 재작성되지 않았을 수 있다.

### 시나리오 3: CDN 뒤에서만 rate limit이 이상하다

trust boundary 밖의 헤더가 chain에 섞였을 가능성이 있다.

## 코드로 보기

### Nginx 정규화 감각

```nginx
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto $scheme;
proxy_set_header X-Forwarded-Host $host;
```

### HAProxy 감각

```haproxy
http-request del-header X-Forwarded-For
http-request set-header X-Forwarded-For %[src]
```

### 체크 포인트

```text
- external headers are stripped
- trusted proxy headers are rewritten
- app sees canonical chain only
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| append only | 구현이 쉽다 | 공격자 값이 남을 수 있다 | 내부 통제 낮음 |
| rewrite at boundary | 신뢰성이 높다 | 설정이 늘어난다 | 일반 운영 |
| strict canonicalization | 분석이 쉽다 | 호환성 조정이 필요하다 | 대규모 체인 |

핵심은 "헤더를 전달했다"가 아니라 **신뢰 가능한 형태로 정리했다**다.

## 꼬리질문

> Q: proxy header normalization이 왜 필요한가요?
> 핵심: 여러 홉을 거치며 들어온 값을 신뢰 가능한 형태로 정리해야 하기 때문이다.

> Q: append만 하면 안 되나요?
> 핵심: 외부 입력이 섞인 채 남아 trust boundary가 흐려질 수 있다.

> Q: app은 무엇을 믿어야 하나요?
> 핵심: canonicalized chain과 trusted proxy가 다시 쓴 값만 믿어야 한다.

## 한 줄 정리

proxy 헤더는 단순 전달이 아니라 각 홉에서 정규화해야 하며, canonical chain만 남겨야 trust boundary가 유지된다.
