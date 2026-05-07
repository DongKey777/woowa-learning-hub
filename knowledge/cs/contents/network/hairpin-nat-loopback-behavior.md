---
schema_version: 3
title: "Hairpin NAT, Loopback Behavior"
concept_id: network/hairpin-nat-loopback-behavior
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 80
mission_ids: []
review_feedback_tags:
- hairpin-nat-loopback
- internal-public-ip-path
- nat-conntrack-observability
aliases:
- hairpin NAT
- loopback NAT
- NAT reflection
- internal to public IP
- LAN loopback
- conntrack hairpin
symptoms:
- 내부 클라이언트가 public hostname을 호출해 NAT를 돌아 내부 서버로 다시 들어오는 경로를 놓친다
- 내부 테스트가 외부보다 느린데 hairpin NAT와 conntrack 증가를 의심하지 않는다
- split-horizon DNS가 없어서 내부 트래픽이 public IP 경로로 우회하는 장면을 못 본다
intents:
- troubleshooting
- design
- deep_dive
prerequisites:
- network/nat-conntrack-ephemeral-port-exhaustion
- network/dns-split-horizon-behavior
next_docs:
- network/nat-keepalive-tuning-connection-lifetime
- network/forwarded-x-forwarded-for-x-real-ip-trust-boundary
- network/connection-reuse-vs-service-discovery-churn
linked_paths:
- contents/network/nat-conntrack-ephemeral-port-exhaustion.md
- contents/network/nat-keepalive-tuning-connection-lifetime.md
- contents/network/dns-split-horizon-behavior.md
- contents/network/forwarded-x-forwarded-for-x-real-ip-trust-boundary.md
- contents/network/connection-reuse-vs-service-discovery-churn.md
confusable_with:
- network/nat-conntrack-ephemeral-port-exhaustion
- network/dns-split-horizon-behavior
- network/forwarded-x-forwarded-for-x-real-ip-trust-boundary
- network/connection-reuse-vs-service-discovery-churn
forbidden_neighbors: []
expected_queries:
- "Hairpin NAT는 내부 클라이언트가 public IP로 나갔다 다시 내부 서버로 들어오는 구조야?"
- "내부에서 같은 hostname이 외부보다 느리면 NAT loopback을 어떻게 의심해?"
- "Split-horizon DNS가 hairpin NAT를 피하는 데 어떤 역할을 해?"
- "NAT reflection 때문에 conntrack entry가 늘고 client IP 로그가 애매해지는 흐름을 설명해줘"
- "내부 서비스 호출이 public IP를 쓰는지 dig ip route ss로 확인하는 순서를 알려줘"
contextual_chunk_prefix: |
  이 문서는 hairpin NAT, loopback NAT, NAT reflection이 내부 클라이언트의
  public hostname 호출을 NAT/conntrack을 거쳐 내부 서버로 되돌리는 경로와
  split-horizon DNS 대안을 설명하는 advanced playbook이다.
---
# Hairpin NAT, Loopback Behavior

> 한 줄 요약: hairpin NAT는 내부 클라이언트가 공인 주소로 다시 내부 서버를 호출하게 만드는 우회 경로라서, 라우팅과 관측이 생각보다 복잡해진다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [NAT, Conntrack, Ephemeral Port Exhaustion](./nat-conntrack-ephemeral-port-exhaustion.md)
> - [NAT Keepalive Tuning, Connection Lifetime](./nat-keepalive-tuning-connection-lifetime.md)
> - [DNS Split-Horizon Behavior](./dns-split-horizon-behavior.md)
> - [Forwarded, X-Forwarded-For, X-Real-IP와 Trust Boundary](./forwarded-x-forwarded-for-x-real-ip-trust-boundary.md)
> - [Connection Reuse vs Service Discovery Churn](./connection-reuse-vs-service-discovery-churn.md)

retrieval-anchor-keywords: hairpin NAT, loopback NAT, NAT reflection, internal to public IP, conntrack, source NAT, destination NAT, LAN loopback

<details>
<summary>Table of Contents</summary>

- [핵심 개념](#핵심-개념)
- [깊이 들어가기](#깊이-들어가기)
- [실전 시나리오](#실전-시나리오)
- [코드로 보기](#코드로-보기)
- [트레이드오프](#트레이드오프)
- [꼬리질문](#꼬리질문)
- [한 줄 정리](#한-줄 정리)

</details>

## 핵심 개념

hairpin NAT는 내부 클라이언트가 같은 NAT 장비를 돌아 공인 IP로 나갔다가 다시 내부 서버로 돌아오는 구조다.

- NAT reflection이라고도 부른다
- 내부 DNS가 public IP를 주면 자주 발생한다
- conntrack과 NAT 정책이 필요하다

### Retrieval Anchors

- `hairpin NAT`
- `loopback NAT`
- `NAT reflection`
- `internal to public IP`
- `conntrack`
- `source NAT`
- `destination NAT`
- `LAN loopback`

## 깊이 들어가기

### 1. 왜 이런 경로가 생기나

내부 사용자가 서비스의 public hostname을 그대로 호출할 수 있다.

- DNS가 public IP를 준다
- 내부에서 그 IP로 나가면 NAT를 한번 타야 한다
- 다시 내부 서버로 돌아오는 loop가 생긴다

### 2. 왜 문제인가

- 경로가 불필요하게 길어진다
- NAT/conntrack 자원을 쓴다
- 내부와 외부에서 관측 경로가 달라진다

### 3. 왜 split-horizon과 연결되나

내부 DNS가 private IP를 주면 hairpin을 피할 수 있다.

- public IP로 되돌아가는 우회 경로를 줄인다
- 하지만 DNS 정책이 복잡해진다

### 4. 어떤 증상이 보이나

- 외부보다 내부에서 더 느리다
- NAT/conntrack이 불필요하게 증가한다
- 같은 서비스인데 client IP 로그가 애매하다

### 5. 어디서 특히 흔한가

- 사내망에서 공용 도메인을 쓰는 서비스
- 홈 라우터의 LAN loopback
- 클라우드 VPC 내 self-call

## 실전 시나리오

### 시나리오 1: 내부 테스트가 외부보다 느리다

hairpin NAT와 loopback을 의심한다.

### 시나리오 2: 같은 hostname이 내부에서만 이상하다

split-horizon DNS가 없어서 공인 IP로 되돌아가고 있을 수 있다.

### 시나리오 3: conntrack이 예상보다 빨리 찬다

loopback 경로가 불필요한 상태 엔트리를 늘릴 수 있다.

## 코드로 보기

### 경로 확인

```bash
dig api.example.com
ip route get 203.0.113.10
ss -tan state established
```

### 관찰 포인트

```text
- internal client uses public IP?
- conntrack entries increase?
- split-horizon would avoid hairpin?
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| hairpin NAT 허용 | 단일 hostname 유지 | 경로가 비효율적이다 | 간편함 우선 |
| split-horizon DNS | 내부 경로가 짧다 | DNS 정책이 복잡해진다 | 운영 최적화 |
| 별도 내부 hostname | 명확하다 | 이름이 늘어난다 | 경계 분리 우선 |

핵심은 내부 클라이언트가 public IP를 다시 도는 경로를 의도한 것인지 확인하는 것이다.

## 꼬리질문

> Q: hairpin NAT는 무엇인가요?
> 핵심: 내부 클라이언트가 NAT를 돌아 공인 IP로 갔다가 다시 내부로 오는 경로다.

> Q: 왜 느려질 수 있나요?
> 핵심: 불필요한 NAT/conntrack와 우회 경로가 생기기 때문이다.

> Q: 어떻게 줄이나요?
> 핵심: split-horizon DNS나 내부 전용 hostname을 쓴다.

## 한 줄 정리

hairpin NAT는 내부에서 공인 주소를 다시 호출하는 루프라서, split-horizon DNS나 내부 hostname으로 줄이는 편이 낫다.
