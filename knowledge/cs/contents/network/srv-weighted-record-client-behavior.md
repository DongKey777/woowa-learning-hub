# SRV, Weighted Record Client Behavior

> 한 줄 요약: SRV와 가중치 기반 레코드는 클라이언트가 얼마나 똑똑하게 해석하느냐에 따라 분산이 달라지므로, 서버보다 클라이언트 행동을 먼저 봐야 한다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [DNS, CDN, HTTP/2, HTTP/3](./dns-cdn-websocket-http2-http3.md)
> - [DNS TTL Cache Failure Patterns](./dns-ttl-cache-failure-patterns.md)
> - [Connection Reuse vs Service Discovery Churn](./connection-reuse-vs-service-discovery-churn.md)
> - [Load Balancer 헬스체크 실패 패턴](./load-balancer-healthcheck-failure-patterns.md)
> - [Happy Eyeballs, Dual-Stack Racing](./happy-eyeballs-dual-stack-racing.md)

retrieval-anchor-keywords: SRV record, weighted record, priority, weight, client-side load balancing, service discovery, DNS RR, endpoint selection

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

SRV 레코드는 서비스가 어느 host와 port로 제공되는지 알려준다.  
가중치 기반 레코드는 여러 후보 중 어떤 쪽으로 더 자주 보내고 싶은지를 표현한다.

- priority: 먼저 시도할 순서
- weight: 같은 priority 내에서 분산 비율
- client behavior: 실제로 이를 어떻게 해석하느냐

### Retrieval Anchors

- `SRV record`
- `weighted record`
- `priority`
- `weight`
- `client-side load balancing`
- `service discovery`
- `DNS RR`
- `endpoint selection`

## 깊이 들어가기

### 1. 왜 클라이언트 행동이 중요한가

DNS가 여러 레코드를 줘도, 클라이언트가 그것을 어떻게 쓰는지는 다양하다.

- 일부는 SRV를 적극 지원한다
- 일부는 무시한다
- 일부는 첫 항목만 고정적으로 쓴다
- 일부는 캐시와 조합해 이상한 분포를 만든다

### 2. priority와 weight의 감각

- priority가 낮은 쪽이 먼저다
- 같은 priority 내에서 weight가 높은 쪽이 더 자주 선택된다
- 하지만 클라이언트가 이 규칙을 제대로 따라야 의미가 있다

### 3. 왜 분산이 기대와 달라지나

- connection reuse 때문에 선택은 적게 일어난다
- resolver cache가 오래 남을 수 있다
- 일부 client는 weighted sampling을 단순화한다

### 4. 운영에서 자주 놓치는 점

- SRV를 지원하지 않는 library가 많다
- HTTP 클라이언트는 보통 A/AAAA 위주다
- 서비스 디스커버리와 DNS가 서로 다른 추상화일 수 있다

### 5. 언제 쓰면 좋은가

- 비HTTP 서비스
- 내부 서비스 디스커버리
- port가 이름으로 표현되어야 할 때

## 실전 시나리오

### 시나리오 1: 가중치를 줬는데도 한 서버에만 몰린다

클라이언트가 weight를 무시하거나 cache가 지나치게 길 수 있다.

### 시나리오 2: failover가 느리다

priority가 높은 노드가 죽어도 client가 이전 선택을 계속 사용할 수 있다.

### 시나리오 3: 일부 라이브러리만 다른 backend를 친다

SRV 지원 여부와 DNS resolver 구현 차이를 의심한다.

## 코드로 보기

### SRV 조회 감각

```bash
dig _service._tcp.example.com SRV
```

### 관찰 포인트

```text
- client honors priority?
- client honors weight?
- cache lifetime aligned with discovery?
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| SRV/weighted record | DNS로 분산 의도를 표현한다 | 클라이언트 지원이 들쭉날쭉하다 | 서비스 디스커버리 |
| LB 기반 분산 | 클라이언트 단순화 | DNS 레벨 유연성이 낮다 | HTTP 서비스 |
| client-side balancing | 제어가 세밀하다 | 구현이 복잡하다 | 내부 RPC |

핵심은 레코드보다 **클라이언트가 그 의미를 얼마나 잘 지키는가**다.

## 꼬리질문

> Q: SRV 레코드는 무엇을 표현하나요?
> 핵심: 서비스의 host/port와 우선순위, 가중치를 표현한다.

> Q: 왜 분산이 기대와 다를 수 있나요?
> 핵심: 클라이언트 구현과 캐시가 weight를 다르게 다룰 수 있기 때문이다.

> Q: 언제 유용한가요?
> 핵심: 비HTTP 서비스나 내부 discovery에서 유용하다.

## 한 줄 정리

SRV와 weighted record는 서비스 위치와 분산 의도를 표현하지만, 실제 분포는 클라이언트의 해석과 캐시 정책에 크게 좌우된다.
