---
schema_version: 3
title: "DNS Split-Horizon Behavior"
concept_id: network/dns-split-horizon-behavior
canonical: true
category: network
difficulty: advanced
doc_role: deep_dive
level: advanced
language: mixed
source_priority: 82
mission_ids: []
review_feedback_tags:
- split-horizon-dns
- resolver-policy-debugging
- internal-external-view
aliases:
- split-horizon DNS
- internal DNS external DNS
- view-based resolution
- private zone public zone
- resolver policy
- DNS inconsistency
symptoms:
- 같은 도메인이 사내/VPN/외부에서 다른 IP를 주는 것을 DNS 전파 오류로만 본다
- 내부 노트북이 외부 resolver나 DoH를 써서 split-horizon view를 벗어난다
- view별 TTL과 resolver cache 차이로 일부 사용자만 옛 경로를 보는 문제를 놓친다
intents:
- deep_dive
- troubleshooting
- comparison
prerequisites:
- network/dns-basics
- network/dns-over-https-operational-tradeoffs
next_docs:
- network/dns-ttl-cache-failure-patterns
- network/connection-reuse-vs-service-discovery-churn
- network/forwarded-x-forwarded-for-x-real-ip-trust-boundary
- network/happy-eyeballs-dual-stack-racing
linked_paths:
- contents/network/dns-ttl-cache-failure-patterns.md
- contents/network/dns-over-https-operational-tradeoffs.md
- contents/network/connection-reuse-vs-service-discovery-churn.md
- contents/network/forwarded-x-forwarded-for-x-real-ip-trust-boundary.md
- contents/network/happy-eyeballs-dual-stack-racing.md
confusable_with:
- network/dns-over-https-operational-tradeoffs
- network/dns-ttl-cache-failure-patterns
- network/dns-negative-caching-nxdomain-behavior
- network/connection-reuse-vs-service-discovery-churn
forbidden_neighbors: []
expected_queries:
- "Split-horizon DNS는 같은 이름이 내부와 외부에서 왜 다른 IP를 줘?"
- "VPN 접속 여부나 resolver 위치에 따라 DNS 답이 다른 장면을 어떻게 디버깅해?"
- "DoH를 쓰면 split-horizon DNS가 왜 깨질 수 있어?"
- "internal private zone과 public zone의 TTL cache가 다르면 어떤 장애가 생겨?"
- "같은 도메인이 사내에서는 되고 집에서는 안 될 때 DNS view를 어떻게 확인해?"
contextual_chunk_prefix: |
  이 문서는 split-horizon DNS, internal/external resolver view, private/public
  zone, VPN/DoH resolver drift, view별 TTL cache가 같은 이름의 다른 답을
  만드는 운영 특성을 설명하는 advanced DNS deep dive다.
---
# DNS Split-Horizon Behavior

> 한 줄 요약: split-horizon DNS는 같은 이름이 내부와 외부에서 다른 주소를 돌려주게 만들어, 편리하지만 정책과 디버깅을 동시에 어렵게 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [DNS TTL Cache Failure Patterns](./dns-ttl-cache-failure-patterns.md)
> - [DNS over HTTPS Operational Trade-offs](./dns-over-https-operational-tradeoffs.md)
> - [Connection Reuse vs Service Discovery Churn](./connection-reuse-vs-service-discovery-churn.md)
> - [Forwarded, X-Forwarded-For, X-Real-IP와 Trust Boundary](./forwarded-x-forwarded-for-x-real-ip-trust-boundary.md)
> - [Happy Eyeballs, Dual-Stack Racing](./happy-eyeballs-dual-stack-racing.md)

retrieval-anchor-keywords: split-horizon DNS, internal DNS, external DNS, view-based resolution, private zone, public zone, resolver policy, DNS inconsistency

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

split-horizon DNS는 같은 도메인 이름에 대해 조회 위치에 따라 다른 답을 주는 방식이다.

- 사내에서는 internal IP를 준다
- 외부에서는 public IP를 준다
- 장애 전환과 보안 정책에 유용하다

하지만 잘못 운영하면 "어느 경로가 진짜인가"가 흐려진다.

### Retrieval Anchors

- `split-horizon DNS`
- `internal DNS`
- `external DNS`
- `view-based resolution`
- `private zone`
- `public zone`
- `resolver policy`
- `DNS inconsistency`

## 깊이 들어가기

### 1. 왜 쓰는가

같은 서비스라도 내부와 외부의 목적이 다를 수 있다.

- 내부에서는 private IP로 붙는 게 빠르다
- 외부에서는 public IP가 필요하다
- 이름은 같아도 연결 경로는 달라야 한다

### 2. 왜 문제가 생기나

클라이언트나 resolver가 어디에 붙느냐에 따라 답이 달라진다.

- 내부 노트북이 외부 resolver를 쓰면 잘못된 답을 받을 수 있다
- split-horizon 규칙이 앱/운영 도구와 어긋날 수 있다
- 캐시가 서로 다른 view를 오래 들고 있을 수 있다

### 3. 디버깅이 어려운 이유

같은 이름이라도 환경별로 답이 다르기 때문이다.

- 실내망에서만 재현된다
- VPN 접속 여부에 따라 다르다
- 특정 resolver를 쓰면 다르게 보인다

### 4. 보안과의 관계

split-horizon은 내부 주소를 숨기는 데 도움이 되지만,

- 정책이 너무 많아지면 운영 실수가 늘고
- 외부와 내부의 차이가 너무 커지면 클라이언트가 혼란스러워진다

### 5. 어떤 경우에 특히 유용한가

- 내부 API와 외부 API를 같은 이름 아래 둘 때
- 사내 전용 서비스가 있을 때
- multi-region failover와 함께 쓸 때

## 실전 시나리오

### 시나리오 1: 사내에서는 되는데 집에서는 안 된다

내부 zone이 외부 resolver에 노출되지 않거나, 반대로 내부 resolver가 외부 view를 보지 못할 수 있다.

### 시나리오 2: 같은 이름인데 IP가 다르게 나온다

의도된 split-horizon일 수 있지만, 캐시/뷰 혼선일 수도 있다.

### 시나리오 3: DNS 변경 후 일부 사용자만 계속 옛 경로를 본다

뷰별 TTL과 resolver cache가 다르게 작동할 수 있다.

## 코드로 보기

### 뷰별 조회 감각

```bash
dig @internal-resolver api.example.com
dig @public-resolver api.example.com
```

### 체크 포인트

```text
- where is the resolver?
- which view is active?
- are internal and external answers intentionally different?
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| split-horizon | 내부/외부 정책 분리가 쉽다 | 디버깅이 복잡해진다 | 기업/하이브리드 환경 |
| 단일 public DNS | 단순하다 | 내부 최적화가 어렵다 | 공개 서비스 |
| 단일 internal DNS | 통제하기 쉽다 | 외부 접근 설계가 별도 필요하다 | 내부망 중심 |

핵심은 같은 이름이 다른 답을 주는 사실을 숨기지 말고 **운영 문서로 명시하는 것**이다.

## 꼬리질문

> Q: split-horizon DNS는 무엇인가요?
> 핵심: 조회 위치에 따라 같은 이름이 다른 IP를 반환하는 방식이다.

> Q: 왜 디버깅이 어려운가요?
> 핵심: resolver와 네트워크 위치에 따라 답이 달라지기 때문이다.

> Q: DoH와 충돌할 수 있나요?
> 핵심: 외부 resolver를 쓰면 내부 view를 못 볼 수 있다.

## 한 줄 정리

split-horizon DNS는 내부와 외부 정책을 분리하는 유용한 도구지만, resolver 위치와 캐시를 함께 관리하지 않으면 혼선이 생긴다.
