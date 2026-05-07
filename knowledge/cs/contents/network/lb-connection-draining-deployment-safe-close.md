---
schema_version: 3
title: "LB Connection Draining, Deployment Safe Close"
concept_id: network/lb-connection-draining-deployment-safe-close
canonical: true
category: network
difficulty: advanced
doc_role: playbook
level: advanced
language: mixed
source_priority: 86
mission_ids: []
review_feedback_tags:
- connection-draining
- graceful-shutdown
- deployment-reset
aliases:
- connection draining
- deployment safe close
- graceful shutdown drain
- deregistration delay
- scale-in preStop
- load balancer draining
symptoms:
- 배포 직후 502나 connection reset이 늘어난다
- scale-in 때 기존 keep-alive나 streaming 요청이 중간에 끊긴다
- readiness false 이후에도 기존 연결 정리 순서를 모른다
- drain timeout을 짧게 잡아 WebSocket이나 long request가 깨진다
intents:
- troubleshooting
- deep_dive
- design
prerequisites:
- network/load-balancer-healthcheck-failure-patterns
- network/connection-keepalive-loadbalancing-circuit-breaker
next_docs:
- network/idle-timeout-mismatch-lb-proxy-app
- network/fin-rst-half-close-eof-semantics
- network/api-gateway-reverse-proxy-operational-points
- network/http-keepalive-timeout-mismatch-deeper-cases
linked_paths:
- contents/network/load-balancer-healthcheck-failure-patterns.md
- contents/network/idle-timeout-mismatch-lb-proxy-app.md
- contents/network/connection-keepalive-loadbalancing-circuit-breaker.md
- contents/network/fin-rst-half-close-eof-semantics.md
- contents/network/api-gateway-reverse-proxy-operational-points.md
- contents/network/http-keepalive-timeout-mismatch-deeper-cases.md
confusable_with:
- network/load-balancer-healthcheck-failure-patterns
- network/idle-timeout-mismatch-lb-proxy-app
- network/connection-draining-vs-fin-rst-graceful-close
- network/fin-rst-half-close-eof-semantics
forbidden_neighbors: []
expected_queries:
- "배포 직후 502와 reset이 늘면 connection draining을 어떻게 확인해?"
- "LB deregistration delay와 Kubernetes preStop 순서를 어떻게 맞춰?"
- "scale-in 중 기존 keep-alive 요청을 안전하게 마무리하는 방법은?"
- "graceful shutdown과 readiness false만으로 충분하지 않은 이유는?"
- "WebSocket이나 streaming 서비스 배포 때 drain timeout을 어떻게 잡아?"
contextual_chunk_prefix: |
  이 문서는 load balancer connection draining, graceful shutdown,
  deregistration delay, Kubernetes preStop, 배포/scale-in 중 기존 연결
  safe close를 다루는 advanced playbook이다.
---
# LB Connection Draining, Deployment Safe Close

> 한 줄 요약: connection draining은 배포나 scale-in 중에 기존 연결을 갑자기 자르지 않고 마무리하게 만들어, 불필요한 502와 reset을 줄인다.

**난이도: 🔴 Advanced**

> 관련 문서:
> - [Load Balancer 헬스체크 실패 패턴](./load-balancer-healthcheck-failure-patterns.md)
> - [Idle Timeout 불일치: LB, Proxy, App](./idle-timeout-mismatch-lb-proxy-app.md)
> - [Connection Keep-Alive, Load Balancing, Circuit Breaker](./connection-keepalive-loadbalancing-circuit-breaker.md)
> - [FIN, RST, Half-Close, EOF](./fin-rst-half-close-eof-semantics.md)
> - [API Gateway, Reverse Proxy 운영 포인트](./api-gateway-reverse-proxy-operational-points.md)

retrieval-anchor-keywords: connection draining, deployment safe close, graceful shutdown, deregistration delay, scale-in, preStop, load balancer, connection reuse, drain timeout

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

connection draining은 LB가 기존 연결을 즉시 끊지 않고, 새 연결만 다른 곳으로 보내며 **기존 연결을 천천히 마무리**하게 하는 운영 방식이다.

- 배포 중 연결이 갑자기 reset되지 않는다
- scale-in 시 사용자 요청이 덜 깨진다
- 오래된 keep-alive 연결을 부드럽게 종료한다

### Retrieval Anchors

- `connection draining`
- `deployment safe close`
- `graceful shutdown`
- `deregistration delay`
- `scale-in`
- `preStop`
- `load balancer`
- `connection reuse`
- `drain timeout`

## 깊이 들어가기

### 1. 왜 필요한가

서버를 그냥 종료하면 연결이 갑자기 끊긴다.

- 요청 처리 중 응답이 날아간다
- proxy와 client에 reset이 보인다
- 배포가 사용자 장애처럼 보인다

draining은 이 상황을 줄이기 위한 완충 장치다.

### 2. 어떤 계층이 draining을 하나

- LB: 새 연결을 막고 기존 연결은 유지한다
- proxy: upstream 연결을 서서히 정리한다
- app: shutdown hook으로 더 이상 새 작업을 받지 않는다

각 층이 자기 역할을 해야 한다.

### 3. 왜 health check만으로는 부족한가

health check가 false를 반환한다고 해서 기존 연결이 즉시 안전하게 닫히는 건 아니다.

- 이미 붙어 있는 keep-alive는 남는다
- streaming 요청은 더 오래 유지될 수 있다
- backend는 종료 전에 요청을 마무리해야 한다

### 4. drain timeout을 어떻게 보나

drain timeout은 너무 짧으면 reset이 늘고, 너무 길면 배포가 느려진다.

- 트래픽 패턴
- 평균 요청 시간
- 스트리밍 여부
- keep-alive 길이

이 네 가지를 같이 봐야 한다.

### 5. safe close의 핵심

진짜 중요한 것은 "빨리 내리는 것"이 아니라 **새 요청을 안 받으면서 기존 요청을 끝내는 것**이다.

## 실전 시나리오

### 시나리오 1: 배포 직후 502가 늘어난다

draining 없이 인스턴스를 내렸을 수 있다.

### 시나리오 2: scale-in 때만 간헐적 reset이 난다

기존 연결이 살아 있는데 backend를 먼저 종료했을 가능성이 있다.

### 시나리오 3: WebSocket/streaming 서비스가 배포 때 깨진다

drain window가 스트리밍 수명보다 짧을 수 있다.

## 코드로 보기

### Kubernetes preStop 감각

```yaml
lifecycle:
  preStop:
    exec:
      command: ["sh", "-c", "sleep 10"]
```

### 앱 종료 흐름 감각

```text
1. readiness false
2. 새 트래픽 중단
3. 기존 요청 마무리
4. 종료
```

### 운영 명령

```bash
kubectl get endpoints
kubectl describe pod my-app
```

## 트레이드오프

| 선택지 | 장점 | 단점 | 언제 쓰는가 |
|--------|------|------|-------------|
| 즉시 종료 | 빠르다 | reset과 에러가 늘 수 있다 | 비정상 종료 |
| draining 사용 | 요청 손실이 줄어든다 | 배포/종료가 느려진다 | 일반 배포 |
| 긴 drain window | 스트리밍에 유리하다 | 자원 회수가 늦다 | long-lived connection |

핵심은 종료를 "꺼버리는 것"이 아니라 **새로 안 받고 기존을 끝내는 것**이다.

## 꼬리질문

> Q: connection draining은 왜 필요한가요?
> 핵심: 배포나 scale-in 때 기존 요청이 갑자기 끊기지 않게 하려고 쓴다.

> Q: health check만으로 충분하지 않나요?
> 핵심: 아니다. 이미 붙은 연결은 별도의 종료 절차가 필요하다.

> Q: drain timeout은 어떻게 생각하나요?
> 핵심: 평균 요청 시간과 long-lived connection 수명보다 여유 있게 잡는다.

## 한 줄 정리

connection draining은 배포와 축소 과정에서 기존 연결을 부드럽게 끝내는 장치라서, reset과 502를 줄이려면 readiness와 함께 써야 한다.
